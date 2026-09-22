"""Current-link registration contracts; no emulator or save-file writes."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import unittest

from dex_timing.assets import Repository
from dex_timing.cpu import CounterCPU
from dex_timing.new_entry import audit_description, audit_description_publication, audit_publication, audit_resident_layout, display_clock_matches
from dex_timing.new_entry_sweep import ORIGINAL, ADDITIONAL, audit, cases
from dex_timing.assets import Event

ROOT = Path(__file__).resolve().parents[1]


class InputSweepTests(unittest.TestCase):
    def fixture(self):
        asset = SimpleNamespace(name='test', events=[Event(0, 2, 0), Event(1, 3, 0)], sample_blocks=0)
        case = dict(name='baseline', family='baseline')
        trace = []
        for serial, (frame, duration, display) in enumerate(((0, 2, 10), (1, 3, 12), (0, 0, 15)), 1):
            trace.append(dict(event='script_frame', serial=serial, command=frame, duration=duration))
            trace.append(dict(event='published', serial=serial, display=display, mode=1, ly=151, misses=0))
        for display, serial, mask in ((11, 1, 1), (12, 1, 1), (13, 2, 2), (14, 2, 2), (15, 2, 2), (16, 3, 1)):
            trace.append(dict(event='display', type=0, phase=1, serial=serial, number=display,
                              t=display * 70224, map_mask=mask, pixel_mask=mask))
        trace.append(dict(event='animation_finished', hvblank=0, frame_counter=0))
        return asset, trace, case

    def test_sweep_crosses_each_interval_and_keeps_twenty_species(self):
        self.assertEqual(len(set(ORIGINAL + ADDITIONAL)), 20)
        self.assertTrue({'rampardos', 'kyogre'} <= set(ADDITIONAL))
        suite = cases(275, 50)
        self.assertEqual(len({c['name'] for c in suite}), len(suite))
        self.assertEqual([c['windows'][0][1] for c in suite if c['family'] == 'page'], list(range(278)))
        self.assertEqual([c['windows'][1][1] for c in suite if c['family'] == 'exit'], list(range(278)))
        self.assertEqual(sum(c['family'] == 'startup' for c in suite), 100)

    def test_auditor_accepts_exact_sequence(self):
        self.assertEqual(audit(*self.fixture())['status'], 'pass')

    def test_vblank_line_zero_is_not_visible_line_zero(self):
        asset, trace, case = self.fixture()
        publication = next(e for e in trace if e['event'] == 'published')
        publication['ly'] = 0
        self.assertEqual(audit(asset, trace, case)['status'], 'pass')
        for mode in (0, 2, 3):
            publication['mode'] = mode
            self.assertEqual(audit(asset, trace, case)['status'], 'fail')

    def test_auditor_rejects_late_publication_wrong_pixels_and_leaked_owner(self):
        asset, original, case = self.fixture()
        for event, field, bad in (('published', 'display', 9), ('display', 'pixel_mask', 0),
                                  ('animation_finished', 'hvblank', 0x88)):
            trace = deepcopy(original)
            next(e for e in trace if e['event'] == event)[field] = bad
            self.assertEqual(audit(asset, trace, case)['status'], 'fail', field)

    def test_auditor_rejects_both_miss_breakpoints(self):
        for event in ('animation_miss', 'audio_empty'):
            asset, trace, case = self.fixture()
            trace.append(dict(event=event))
            self.assertEqual(audit(asset, trace, case)['status'], 'fail')

    def test_missing_exit_is_not_successful_completion(self):
        asset, trace, _ = self.fixture()
        result = audit(asset, trace, dict(name='exit-000', family='exit'))
        self.assertTrue(any(e['reason'] == 'exit tap not accepted' for e in result['errors']))

    def description_fixture(self):
        trace = [dict(event='input', keys=16, display=10, t=10 * 70224),
                 dict(event='description', dex_status=1, display=11, t=11 * 70224),
                 dict(event='description_ready', display=11, t=11 * 70224 + 200)]
        for display in (11, 12, 13, 14):
            trace.append(dict(event='description_display', display=display, t=display * 70224,
                              old_map=display < 13, old_pixels=display < 13,
                              new_map=display >= 13, new_pixels=display >= 13))
        return trace

    def test_description_latency_is_input_anchored_not_wait_anchored(self):
        trace = self.description_fixture()
        errors, result = audit_description(trace)
        self.assertFalse(errors)
        self.assertEqual(result['input_to_visible_intervals'], 3)
        self.assertEqual(result['ready_to_visible_intervals'], 2)
        trace.append(dict(event='wait_entry', display=20, t=20 * 70224))
        self.assertEqual(audit_description(trace), (errors, result))

    def test_description_rejects_mixed_pixels_and_reversion(self):
        for display, key in ((12, 'old_pixels'), (13, 'new_map'), (14, 'new_pixels')):
            trace = self.description_fixture()
            next(e for e in trace if e['event'] == 'description_display' and
                 e['display'] == display)[key] = False
            self.assertTrue(audit_description(trace)[0], (display, key))

    def test_description_requires_visible_completion_and_ready_observation(self):
        trace = self.description_fixture()
        self.assertTrue(audit_description([e for e in trace if
                                          e['event'] != 'description_ready'])[0])
        self.assertTrue(audit_description([e for e in trace if e['display'] < 13])[0])

    def test_ppu_clock_removes_batch_time_not_actual_drift(self):
        frames = [dict(number=1, t=1004, ppu_t=1000),
                  dict(number=2, t=71234, ppu_t=71224)]
        self.assertTrue(display_clock_matches(frames))
        frames[1]['ppu_t'] += 1
        self.assertFalse(display_clock_matches(frames))


@unittest.skipUnless((ROOT / 'pokecrystal.gbc').exists(), 'build the ROM first')
class RegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')

    def test_publication_and_miss_contract(self):
        costs = audit_publication(self.repo)
        self.assertEqual(set(costs), {'map', 'first', 'finish'})
        self.assertEqual({name: row['last_write_t'] for name, row in costs.items()},
                         {'map': 1108, 'first': 1704, 'finish': 1708})
        self.assertGreaterEqual(min(c['write_margin_t'] for c in costs.values()), 116)

    def test_every_resident_frame_mapping(self):
        result = audit_resident_layout(self.repo)
        self.assertGreaterEqual(result['assets'], 373)
        self.assertLessEqual(result['max_pairs'], 49)
        self.assertLess(result['max_tile'], 256)

    def test_description_publication_is_bounded_and_disjoint(self):
        result = audit_description_publication(self.repo)
        self.assertEqual(result['cells'], 91)
        self.assertGreater(result['write_margin_t'], 0)

    def test_final_picture_ack_retains_owner_until_description_commits(self):
        cpu = CounterCPU(self.repo.rom, self.repo.symbols)
        for name, value in [('hVBlank', 0x88), ('hOAMUpdate', 1),
                            ('wNewDexEntryAnimFlags', 0x55), ('wFrameCounter', 1),
                            ('wNewDexEntryAnimSavedVBlank', 0),
                            ('wNewDexEntryAnimSavedOAM', 0)]:
            cpu.field(name, value)
        cpu.run('NewDexEntry_ServiceAnimation')
        bank, at = self.repo.symbols['wNewDexEntryAnimFlags']
        self.assertEqual(cpu.wram[bank][at & 4095], 0x55)
        self.assertEqual(cpu.read(self.repo.symbols['hVBlank'][1]), 0x88)
        cpu.field('wNewDexEntryAnimFlags', 0x15)
        cpu.run('NewDexEntry_ServiceAnimation')
        self.assertEqual(cpu.wram[bank][at & 4095], 0)
        self.assertEqual(cpu.read(self.repo.symbols['hVBlank'][1]), 0)
        self.assertEqual(cpu.read(self.repo.symbols['wFrameCounter'][1]), 0)

    def test_aliases_do_not_allocate_new_ram(self):
        for new, old in [('wNewDexEntryAnimPairs', 'wTempTilemap'),
                         ('wNewDexEntryAnimFlags', 'wPokeAnimStruct'),
                         ('wNewDexEntryAnimMap', 'wPokeAnimFrameTiles')]:
            self.assertEqual(self.repo.symbols[new], self.repo.symbols[old])
        self.assertEqual(self.repo.symbols['sNewDexEntryUploadBuffer'], (0, 0xa320))

    def test_cancel_restores_owner_and_wram_bank(self):
        cpu = CounterCPU(self.repo.rom, self.repo.symbols)
        for name, value in [('hVBlank', 0x88), ('hOAMUpdate', 1),
                            ('wNewDexEntryAnimFlags', 3), ('wFrameCounter', 1),
                            ('wNewDexEntryAnimSavedVBlank', 0),
                            ('wNewDexEntryAnimSavedOAM', 0)]:
            cpu.field(name, value)
        cpu.ram[0xff70] = 6
        cpu.run('NewDexEntry_CancelAnimation')
        self.assertEqual(cpu.ram[0xff70], 6)
        for name in ('hVBlank', 'hOAMUpdate', 'wFrameCounter'):
            self.assertEqual(cpu.read(self.repo.symbols[name][1]), 0)
        bank, at = self.repo.symbols['wNewDexEntryAnimFlags']
        self.assertEqual(cpu.wram[bank][at & 4095], 0)
        cpu.field('hVBlank', 7)
        cpu.field('hOAMUpdate', 1)
        cpu.run('NewDexEntry_CancelAnimation')
        self.assertEqual(cpu.read(self.repo.symbols['hVBlank'][1]), 7)
        self.assertEqual(cpu.read(self.repo.symbols['hOAMUpdate'][1]), 1)

    def test_delay_hook_preserves_all_caller_registers(self):
        for owner in (0, 7, 0x80, 0x88):
            cpu = CounterCPU(self.repo.rom, self.repo.symbols)
            cpu.field('hVBlank', owner)
            cpu.field('wNewDexEntryAnimFlags', 3)
            cpu.r = [1, 2, 3, 4, 5, 6, 0, 0]
            cpu.f = 0x80
            before = tuple(cpu.r), cpu.f
            cpu.run('NewDexEntry_ServiceAfterDelayFrame')
            self.assertEqual((tuple(cpu.r), cpu.f), before)
            self.assertEqual(cpu.ram[0xff70], 1)

    def test_page_service_preserves_registers_and_does_not_refill_audio(self):
        audio_service = self.repo.symbols['ServiceSampledCryAsync'][1]

        class AnimationOnlyCPU(CounterCPU):
            def step(self):
                if self.pc == audio_service:
                    raise AssertionError('Inner description service entered audio refill')
                super().step()

        for owner in (0, 7, 0x80, 0x88):
            cpu = AnimationOnlyCPU(self.repo.rom, self.repo.symbols)
            cpu.field('hVBlank', owner)
            cpu.field('wNewDexEntryAnimFlags', 3)
            # An inner text service must not enter the audio path even if active.
            cpu.field('hSampledCryTimer', 1)
            cpu.ram[0xff70] = 6
            cpu.r = [1, 2, 3, 4, 5, 6, 0, 7]
            cpu.f = 0xb0
            before = tuple(cpu.r), cpu.f
            cpu.run('NewDexEntry_DisplayPage2.ServiceAnimation', max_steps=200)
            self.assertEqual((tuple(cpu.r), cpu.f), before)
            self.assertEqual(cpu.ram[0xff70], 6)

    def test_publication_between_flag_checks_cannot_overwrite_unacknowledged_map(self):
        symbols = self.repo.symbols
        build = symbols['NewDexEntry_ServiceAnimation.build'][1]
        make_map = symbols['NewDexEntry_BuildAnimationMap'][1]
        backing = symbols['wTilemap'][1] + 21
        for after_snapshot in (False, True):
            with self.subTest(after_snapshot=after_snapshot):
                cpu = CounterCPU(self.repo.rom, symbols)
                cpu.field('wNewDexEntryAnimFlags', 3)  # ACTIVE | READY
                bank, at = symbols['wNewDexEntryAnimMap']
                cpu.wram[bank][at & 4095:(at & 4095) + 49] = bytes(range(49))
                for row in range(7):
                    cpu.ram[backing + 20 * row:backing + 20 * row + 7] = b'\xcc' * 7
                cpu.bank, cpu.pc = symbols['NewDexEntry_ServiceAnimation']
                cpu.push(0xffff)
                injected = False
                for _ in range(1024):
                    if cpu.pc == build + (3 if after_snapshot else 0) and not injected:
                        # Model only the ISR's state transition, not hardware time.
                        cpu.field('wNewDexEntryAnimFlags', 17)  # ACTIVE | ACK
                        injected = True
                    if cpu.pc in (make_map, 0xffff):
                        break
                    cpu.step()
                self.assertTrue(injected)
                picture = b''.join(cpu.ram[backing + 20 * row:backing + 20 * row + 7]
                                   for row in range(7))
                if after_snapshot:
                    self.assertEqual(cpu.pc, 0xffff)
                    self.assertEqual(picture, b'\xcc' * 49)
                    self.assertEqual(cpu.wram[2][symbols['wNewDexEntryAnimFlags'][1] & 4095], 17)
                else:
                    self.assertEqual(cpu.pc, make_map)
                    self.assertEqual(picture, bytes(range(49)))
                    self.assertEqual(cpu.wram[2][symbols['wNewDexEntryAnimFlags'][1] & 4095], 1)

    def test_nonquiet_vblank_keeps_original_viewport_budget(self):
        symbols = self.repo.symbols
        normal = symbols['VBlank_Normal'][1]
        graphics = symbols['VBlank_Normal.viewport_owned'][1]
        dispatch = symbols['NewDexEntry_VBlankDispatch'][1]
        gate = self.repo.rom.index(bytes((0xf0, symbols['hVBlank'][1] & 255)), normal, graphics)
        for owner in (0, 7, 0x80, 0x87, 0x88):
            cpu = CounterCPU(self.repo.rom, symbols)
            cpu.allowed_io.update((0xff42, 0xff43, 0xff4a, 0xff4b))
            cpu.field('hVBlank', owner)
            cpu.pc = gate
            for _ in range(16):
                cpu.step()
                if cpu.pc in (graphics, dispatch):
                    break
            self.assertEqual(cpu.pc, dispatch if owner & 128 else graphics)
            # Original LDH/BIT/JR gate: 32 T taken, or 28 T + 96 T viewport.
            self.assertEqual(cpu.cycles, 32 if owner & 128 else 124)


if __name__ == '__main__':
    unittest.main()
