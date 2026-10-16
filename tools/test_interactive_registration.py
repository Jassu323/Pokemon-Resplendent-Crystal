"""Linked fixed-species registration context and ownership contracts."""
import argparse
import json
from pathlib import Path
import re
import struct
import unittest

from dex_timing.assets import Repository, offset
from dex_timing.cpu import CounterCPU

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'build/interactive-registration-fixed-full-20261016/candidate'
BASELINE = ROOT / 'build/interactive-registration-fixed-full-20261016/baseline-source'
FIELDS = '''hMapAnims hSCX hSCY hWX hWY hVBlank hOAMUpdate hBGMapMode
    hLCDCPointer hInMenu hMapObjectIndex hObjectStructIndex wPokedexStatus
    wJumptableIndex wDexArrowCursorPosIndex wDexArrowCursorDelayCounter
    wDexArrowCursorBlinkCounter wCurPartySpecies wCurSpecies wTempSpecies
    wUnownLetter wOptions wStateFlags wVolume wLastVolume wScriptVar
    wMenuCursorY rVBK wPayDayMoney wPayDayMoneyByte1 wPayDayMoneyByte2'''.split()
CONTEXT_SIZE = 32 + len(FIELDS) + 4


class RegistrationContracts(unittest.TestCase):
    number_row_costs = []
    number_glyph_comparisons = 0
    stats_cpu_budget_t = None
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(SOURCE, SOURCE / 'pokecrystal.gbc', SOURCE / 'pokecrystal.sym')
        cls.repo.symbols['rVBK'] = 0, 0xff4f
        bank, address = cls.repo.symbols['wPayDayMoney']
        cls.repo.symbols['wPayDayMoneyByte1'] = bank, address + 1
        cls.repo.symbols['wPayDayMoneyByte2'] = bank, address + 2

    def cpu(self):
        cpu = CounterCPU(self.repo.rom, self.repo.symbols)
        cpu.field('hROMBank', self.repo.symbols['NewPokedexEntry'][0])
        return cpu

    def get(self, cpu, name, size=1):
        bank, address = self.repo.symbols[name]
        if 0xd000 <= address < 0xe000:
            data = cpu.wram[bank][address-0xd000:address-0xd000+size]
        else:
            data = cpu.ram[address:address+size]
        return int.from_bytes(data, 'little')

    def test_field_table_is_independently_enumerated(self):
        start = offset(self.repo.symbols['NewDexRegistration_Fields'])
        end = offset(self.repo.symbols['NewDexRegistration_Fields.end'])
        self.assertEqual(struct.unpack('<31H', self.repo.rom[start:end]),
                         tuple(self.repo.symbols[n][1] for n in FIELDS))

    def test_direct_transfers_stay_in_the_current_or_home_bank(self):
        source = (SOURCE / 'engine/pokedex/new_pokedex_entry.asm').read_text()
        bank = self.repo.symbols['NewPokedexEntry'][0]
        targets = re.findall(r'^\s*(?:call|jp)\s+(?:(?:nz|z|nc|c),\s*)?'
                             r'([A-Za-z_]\w*)\s*(?:;[^\n]*)?$', source, re.M)
        self.assertGreater(len(targets), 25)
        for target in targets:
            self.assertIn(self.repo.symbols[target][0], (0, bank), target)

    def test_context_roundtrip_and_dead_graphics_invalidation(self):
        for seed in (0, 1, 37, 127, 255):
            with self.subTest(seed=seed):
                cpu = self.cpu()
                expected = {}
                for n, name in enumerate(FIELDS):
                    value = (seed + n*17) & 255
                    if name == 'rVBK':
                        value &= 1
                    cpu.field(name, value)
                    expected[name] = value
                prefix = bytes((seed+n*13) & 255 for n in range(32))
                at = self.repo.symbols['wBattleMenuGFXFlags'][1]
                cpu.ram[at:at+32] = prefix
                cpu.field('wPrevDexEntry', 373, 2)
                temp = self.repo.symbols['wTempTilemap'][1] & 4095
                cpu.wram[2][temp:temp+96] = b'\xa6' * 96
                cpu.run('NewDexRegistration_SaveContext')
                self.assertEqual(cpu.ram[0xff70], 1)
                self.assertEqual(cpu.wram[2][temp:temp+CONTEXT_SIZE],
                                 prefix + bytes(expected[n] for n in FIELDS) + b'\x75\x01\x00\x00')
                self.assertEqual(cpu.wram[2][temp+CONTEXT_SIZE:temp+96], b'\xa6'*(96-CONTEXT_SIZE))
                cpu.ram[at:at+32] = b'\xff'*32
                for name in FIELDS:
                    cpu.field(name, 0)
                cpu.field('wPrevDexEntry', 0, 2)
                cpu.run('NewDexRegistration_RestoreContext')
                for name, value in expected.items():
                    self.assertEqual(self.get(cpu, name), value, name)
                self.assertEqual(self.get(cpu, 'wPrevDexEntry', 2), 373)
                restored = bytearray(prefix)
                restored[0] &= ~1
                for name in ('wBattleFrontpicProducerState', 'wBattleFrontpicProducerStagedTiles',
                             'wBattleFrontpicProducerStageOffset'):
                    restored[self.repo.symbols[name][1]-at] = 0
                self.assertEqual(cpu.ram[at:at+32], restored)
                self.assertEqual(cpu.ram[0xff70], 1)
                self.assertEqual(cpu.wram[2][temp+CONTEXT_SIZE:temp+96], b'\xa6'*(96-CONTEXT_SIZE))

    def test_legitimate_payday_totals_survive_scratch_overwrite(self):
        address = self.repo.symbols['wPayDayMoney'][1]
        for value in (0, 1, 12, 65535, 65536, 999999, 0xffffff):
            with self.subTest(value=value):
                cpu = self.cpu()
                cpu.ram[address:address+3] = value.to_bytes(3, 'big')
                cpu.run('NewDexRegistration_SaveContext')
                cpu.ram[address:address+3] = b'\x01\x00\x00'
                cpu.run('NewDexRegistration_RestoreContext')
                self.assertEqual(int.from_bytes(cpu.ram[address:address+3], 'big'), value)
                self.assertEqual(cpu.ram[0xff70], 1)
                self.assertEqual(cpu.sp, 0xc0f0)

    def test_allocated_ram_and_shared_dispatch_addresses_do_not_move(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        for name, original in baseline.symbols.items():
            if original[1] >= 0xa000 and name in self.repo.symbols:
                self.assertEqual(self.repo.symbols[name], original, name)
        for name in ('VBlank', 'LCD', 'SampledCryTimer', 'DelayFrame'):
            # These addresses are not permission to add any per-frame work.
            self.assertEqual(self.repo.symbols[name], baseline.symbols[name], name)

    def test_shared_interrupt_and_delay_bodies_remain_byte_identical(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        for begin, end in (('VBlank', 'BattleMenuGraphic_ClearForText_Home'),
                           ('SampledCryTimer', None)):
            start = baseline.symbols[begin][1]
            stop = baseline.symbols[end][1] if end else 0x4000
            self.assertEqual(self.repo.rom[start:stop], baseline.rom[start:stop], begin)
        bank = baseline.symbols['Pokedex_VBlankDispatch'][0]
        self.assertEqual(self.repo.rom[bank*0x4000:(bank+1)*0x4000],
                         baseline.rom[bank*0x4000:(bank+1)*0x4000])

    def test_previous_lock_is_recovered_after_transient_id_reuse(self):
        cpu = self.cpu()
        bank, entries = self.repo.symbols['wPokemonIndexTableEntries']
        locked = self.repo.symbols['wPokemonIndexTableLockedEntries'][1]
        # Slot eight is DEX_SELECTED in the existing eight map-lock layout.
        slot = 8
        cpu.wram[bank][entries-0xd000+12:entries-0xd000+14] = (373).to_bytes(2, 'little')
        cpu.wram[bank][locked-0xd000+slot] = 7
        cpu.run('NewDexRegistration_SaveContext')
        temp = self.repo.symbols['wTempTilemap'][1] & 4095
        self.assertEqual(cpu.wram[2][temp+CONTEXT_SIZE-2:temp+CONTEXT_SIZE], (373).to_bytes(2, 'little'))
        cpu.wram[bank][entries-0xd000+12:entries-0xd000+14] = (1).to_bytes(2, 'little')
        cpu.wram[bank][entries-0xd000+14:entries-0xd000+16] = (373).to_bytes(2, 'little')
        cpu.wram[bank][locked-0xd000+slot] = 9
        cpu.run('NewDexRegistration_RestoreContext')
        self.assertEqual(cpu.wram[bank][locked-0xd000+slot], 8)
        self.assertEqual(cpu.ram[0xff70], 1)

    def test_prepared_start_retains_the_shared_waiting_state_guard(self):
        for state in (0, 2, 3, 255):
            with self.subTest(state=state):
                cpu = self.cpu()
                cpu.field('wPokedexAnimPlaybackState', state)
                cpu.run('Pokedex_BeginPreparedDescriptionAnimation', max_steps=8)
                self.assertEqual(self.get(cpu, 'wPokedexAnimPlaybackState'), state)
                self.assertEqual(self.get(cpu, 'hSampledCryTimer'), 0)

    def test_relocated_number_table_retains_all_1024_glyphs(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        table_bank = self.repo.symbols['PokedexInfoNumbers'][0]
        self.assertEqual(table_bank, self.repo.symbols['PokedexInfoTileGFX'][0])
        self.assertNotEqual(table_bank, self.repo.symbols['PokedexInfoSpecies'][0])
        for number in range(256):
            for cell in range(4):
                pictures = []
                for repo in (baseline, self.repo):
                    start = offset(repo.symbols['PokedexInfoNumbers']) + number*8 + cell*2
                    pointer = int.from_bytes(repo.rom[start:start+2], 'little')
                    bank = repo.symbols['PokedexInfoTileGFX'][0]
                    at = offset((bank, pointer))
                    pictures.append(repo.rom[at:at+16])
                type(self).number_glyph_comparisons += 1
                self.assertEqual(pictures[0], pictures[1], (number, cell))

    def test_number_row_fetch_has_fixed_bounded_cpu_cost(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        deltas = set()
        for row in range(6):
            for value in (0, 1, 45, 100, 255):
                costs = []
                for repo in (baseline, self.repo):
                    cpu = CounterCPU(repo.rom, repo.symbols)
                    cpu.field('wPokedexInfoRow', row)
                    cpu.field('wPokedexInfoTileCount', 15)
                    cpu.field('wPokedexInfoStats', int.from_bytes(bytes([value])*6, 'little'), 6)
                    cpu.ram[0xff70] = 3
                    costs.append(cpu.run('PokedexInfo_PlanStats'))
                deltas.add(costs[1]-costs[0])
                self.number_row_costs.append(dict(row=row, value=value,
                    production_cpu_t=costs[0], candidate_cpu_t=costs[1],
                    added_cpu_t=costs[1]-costs[0]))
        self.assertEqual(len(deltas), 1)
        self.assertGreater(next(iter(deltas)), 0)
        self.assertLessEqual(next(iter(deltas)), 1000)
        gate = offset(self.repo.symbols['PokedexPerf_InfoLatestLY']) + 2
        latest = self.repo.rom[gate]
        budget = (144-latest)*456 - 2048 - 8182
        type(self).stats_cpu_budget_t = budget
        self.assertLessEqual(max(r['candidate_cpu_t'] for r in self.number_row_costs), budget)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=SOURCE)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    parser.add_argument('--report', type=Path)
    args, rest = parser.parse_known_args()
    BASELINE = args.baseline.resolve()
    SOURCE = args.root.resolve()
    program = unittest.main(argv=[__file__, *rest], exit=False)
    if args.report:
        path = args.report.resolve()
        if not path.is_relative_to(ROOT / 'build'):
            raise ValueError('Generated evidence belongs under build/')
        path.parent.mkdir(parents=True, exist_ok=True)
        result = program.result
        path.write_text(json.dumps(dict(source=str(SOURCE),
            **RegistrationContracts.repo.hashes, cases=result.testsRun,
            failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped),
            numeric_glyph_comparisons=RegistrationContracts.number_glyph_comparisons,
            stats_cpu_budget_t=RegistrationContracts.stats_cpu_budget_t,
            number_row_costs=RegistrationContracts.number_row_costs,
            timing_scope='CPU-only path counter, not display/audio timing'), indent=2)+'\n')
    raise SystemExit(not program.result.wasSuccessful())
