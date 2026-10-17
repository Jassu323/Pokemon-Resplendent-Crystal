"""Linked fixed-species registration context and ownership contracts."""
import argparse
import json
from itertools import product
from pathlib import Path
import re
import struct
from types import SimpleNamespace
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


def normalize_mainline_farcall_relocations(repo, reference):
    bank = reference.symbols['Pokedex_VBlankDispatch'][0]
    if repo.symbols['Pokedex_VBlankDispatch'] != reference.symbols['Pokedex_VBlankDispatch']:
        raise ValueError('Shared dispatch moved')
    start = bank * 0x4000
    original = reference.rom[start:start+0x4000]
    normalized = bytearray(repo.rom[start:start+0x4000])
    # These mainline calls precede interrupt dispatch. Only their linked
    # callee operands may relocate; no opcode, handler or other bank byte may.
    callers = (
        ('Pokedex_CopyBackingToBG', 'Pokedex_CopyBackingToMap',
         ('Pokedex_IsDescriptionLayout', 'Pokedex_CopyDescriptionRightEdge')),
        ('Pokedex_RestoreListingAfterSelectedMon', 'Pokedex_ReloadNormalFootprint',
         ('PokedexSelectedMon_NormalizeLinearReturn',)),
        ('Pokedex_StageOwnerTransitionMaps', 'Pokedex_PublishOrStageDescriptionBacking',
         ('Pokedex_IsDescriptionLayout', 'Pokedex_StageDescriptionRightEdge')),
        ('Pokedex_PublishOrStageDescriptionBacking.description_badge',
         'Pokedex_PublishOrStageDescriptionBacking.lower_ready',
         ('PokedexBadge_Prepare',)))
    def encoded_call(source, label):
        target_bank, address = source.symbols[label]
        return bytes((0x3e, target_bank, 0x21, address & 255, address >> 8, 0xcf))
    for begin, end, targets in callers:
        if any(repo.symbols[name] != reference.symbols[name] for name in (begin, end)):
            raise ValueError('Mainline relocation window moved')
        lo, hi = reference.symbols[begin][1]-0x4000, reference.symbols[end][1]-0x4000
        if reference.symbols[begin][0] != bank or hi > reference.symbols['Pokedex_VBlankDispatch'][1]-0x4000:
            raise ValueError('Relocation window overlaps interrupt dispatch')
        for label in targets:
            old, new = encoded_call(reference, label), encoded_call(repo, label)
            if original[lo:hi].count(old) != 1:
                raise ValueError('Expected one mainline farcall: ' + label)
            at = original.index(old, lo, hi)
            if normalized[at:at+6] != new:
                raise ValueError('Unexpected mainline farcall bytes: ' + label)
            normalized[at:at+6] = old
    return bytes(normalized), original


class RegistrationContracts(unittest.TestCase):
    number_row_costs = []
    number_glyph_comparisons = 0
    ready_staging_costs = []
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
        actual, original = normalize_mainline_farcall_relocations(self.repo, baseline)
        self.assertEqual(actual, original)

    def test_interrupt_bank_guard_rejects_handler_opcode_change(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        data = bytearray(self.repo.rom)
        data[offset(self.repo.symbols['Pokedex_VBlankDispatch'])] ^= 1
        changed = SimpleNamespace(rom=data, symbols=self.repo.symbols)
        actual, original = normalize_mainline_farcall_relocations(changed, baseline)
        self.assertNotEqual(actual, original)

    def test_interrupt_bank_guard_rejects_wrong_mainline_target(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        data = bytearray(self.repo.rom)
        lo = offset(self.repo.symbols['Pokedex_CopyBackingToBG'])
        hi = offset(self.repo.symbols['Pokedex_CopyBackingToMap'])
        # The first farcall follows the native CALL in this small mainline body.
        at = data.index(0x3e, lo, hi)
        data[at+3] ^= 1
        with self.assertRaises(ValueError):
            normalize_mainline_farcall_relocations(SimpleNamespace(rom=data, symbols=self.repo.symbols), baseline)

    def test_interrupt_bank_guard_rejects_wrong_badge_target(self):
        baseline = Repository(BASELINE, BASELINE / 'pokecrystal.gbc', BASELINE / 'pokecrystal.sym')
        data = bytearray(self.repo.rom)
        lo = offset(self.repo.symbols['Pokedex_PublishOrStageDescriptionBacking.description_badge'])
        hi = offset(self.repo.symbols['Pokedex_PublishOrStageDescriptionBacking.lower_ready'])
        bank, address = self.repo.symbols['PokedexBadge_Prepare']
        encoded = bytes((0x3e, bank, 0x21, address & 255, address >> 8, 0xcf))
        at = data.index(encoded, lo, hi)
        data[at+3] ^= 1
        with self.assertRaises(ValueError):
            normalize_mainline_farcall_relocations(SimpleNamespace(rom=data, symbols=self.repo.symbols), baseline)

    def test_info_ready_staging_fits_its_declared_budget(self):
        cutoff = self.repo.rom[offset(self.repo.symbols['PokedexPerf_InfoLatestLY']) + 5]
        self.assertIn(cutoff, (84, 108))
        budget = (144-cutoff)*456 - 2048 - 8182
        for page, miniatures, cache, bank in product((0, 1), (0, 2), (0, 5, 6), (1, 3, 5)):
            with self.subTest(page=page, cutoff=cutoff, miniatures=miniatures, cache=cache, bank=bank):
                cpu = self.cpu()
                cpu.allowed_io.add(0xff44)
                cpu.ram[0xff44] = cutoff - 1
                cpu.ram[0xff70] = bank
                for name, value in dict(hCGB=1, wPokedexSelectedView=1,
                    wPokedexAnimPlaybackState=2, wPokedexInfoState=5,
                    wPokedexInfoPage=page, wPokedexInfoActiveMiniCount=miniatures,
                    hSampledCryTimer=int(bool(cache)), hSampledCryBlocks=8,
                    wSampledCryCacheCount=cache).items():
                    cpu.field(name, value)
                elapsed = cpu.run('PokedexInfo_Service')
                type(self).ready_staging_costs.append(dict(page=page, miniatures=miniatures,
                    cache=cache, caller_bank=bank, cutoff=cutoff, cpu_t=elapsed, budget_t=budget))
                self.assertEqual(self.get(cpu, 'wPokedexOwnerTransition'), 5)
                self.assertLessEqual(elapsed, budget)
                self.assertEqual(cpu.ram[0xff70], bank)
                self.assertEqual(cpu.sp, 0xc0f0)

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
            ready_staging_costs=RegistrationContracts.ready_staging_costs,
            timing_scope='CPU-only path counter, not display/audio timing'), indent=2)+'\n')
    raise SystemExit(not program.result.wasSuccessful())
