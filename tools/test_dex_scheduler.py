#!/usr/bin/env python3
"""Decision and ownership contracts against the CURRENT linked Dex scheduler.

Hardware registers are frozen in these unit fixtures. Full timed execution and
independent SameBoy comparison are provided by dex_timing.integrated_replay.
"""
from itertools import product
from pathlib import Path
import unittest

from dex_timing.assets import Repository, offset
from dex_timing.costs import machine, run_to
from dex_timing.finish_bounds import check

ROOT = Path(__file__).resolve().parents[1]


class SchedulerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
        cls.bounds = check(cls.repo)

    def cpu(self):
        cpu = machine(self.repo)
        cpu.allowed_io.update((0xff00, 0xff04, 0xff06, 0xff07, 0xff40, 0xff41,
                               0xff42, 0xff43, 0xff44, 0xff46, 0xff4a, 0xff4b,
                               0xff4d, *range(0xff51, 0xff56)))
        cpu.io_read_values[0xff00] = 15
        return cpu

    def value(self, cpu, name):
        return cpu.read(self.repo.symbols[name][1])

    def admission(self, count=1, timer_class=2):
        cpu = self.cpu()
        cpu.r[2] = count
        cpu.ram[0xff40] = 0x80
        cpu.ram[0xff07] = (0, 4, 6)[timer_class]
        cpu.ram[0xff06] = 56 if timer_class == 2 else 0
        for name, value in (('hSampledCryTimer', int(timer_class == 2)),
                            ('hLCDCPointer', 0), ('hVBlankCounter', 10),
                            ('wPokedexAnimDeadline', 12),
                            ('wSampledCryBlockPeriod', 200),
                            ('wSampledCryCacheCount', 32)):
            cpu.field(name, value)
        cpu.field('hSampledCryBlocks', 557, 2)
        return cpu

    def test_generated_finishing_bounds(self):
        self.assertTrue(self.bounds['matches'])
        self.assertEqual(self.bounds['inequality_cases'], 216000)

    def test_timeline_preserves_startup_and_allows_full_post_start_decode(self):
        for asset in self.repo.load():
            with self.subTest(species=asset.name):
                expected_start = min(asset.total, asset.width * asset.width + 96)
                event = 0
                for _ in range(3):
                    expected_start = max(expected_start,
                        asset.plans[asset.events[event].frame].high_water)
                    event += 1
                    if event == len(asset.events):
                        if asset.event_loop is None:
                            break
                        event = asset.event_loop
                self.assertEqual(asset.events[0].target, expected_start)
                self.assertTrue(all(e.target == asset.total for e in asset.events[1:]))

    def test_regular_work_readiness_and_once_per_display_tick(self):
        for flags, already, ready, below in product(range(128), (False, True),
                                                    (False, True), (False, True)):
            cpu = self.cpu()
            for name, value in (
                ('hVBlankCounter', 17), ('wPokedexAnimWorkTick', 17 if already else 16),
                ('wPokedexAnimFlags', flags), ('wPokedexAnimStageTileCount', 7),
                ('wPokedexAnimUploadOffset', 2), ('wPokedexAnimDictionaryTileCount', 100),
                ('wPokedexAnimDictionaryTilesRemaining', 20),
                ('wPokedexAnimDictionaryTarget', 81 if below else 80),
            ):
                cpu.field(name, value)
            cpu.block(self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460,
                      bytes((70, 71, 79 if ready else 80, 81, 82, 83, 84)))
            expected = 0 if already else 0xc0 if (flags & 0x7c) == 4 and ready else 0x40 if below else 0
            cpu.run('Pokedex_ChooseAnimationWork')
            self.assertEqual(cpu.r[7], expected)
            self.assertEqual(self.value(cpu, 'wPokedexAnimWorkTick'),
                             17 if expected or already else 16)

    def test_admission_boundary_bank_restore_and_counter_wrap(self):
        for cls, count, enough in product(range(3), range(1, 21), (False, True)):
            limit = self.bounds['latest_ly_exclusive'][cls][count-1]
            for ly in (0, limit-1, limit, 143, 144):
                cpu = self.admission(count, cls)
                cpu.ram[0xff44] = ly
                cpu.ram[0xff41] = 1 if ly >= 144 else 0
                cpu.field('wSampledCryCacheCount', self.bounds['audio_minimum'][count-1] - int(not enough))
                cpu.ram[0xff70] = 6
                cpu.run('Pokedex_AdmitAnimationFinish')
                self.assertEqual(bool(cpu.f & 0x10), ly < limit and (cls != 2 or enough))
                self.assertEqual(cpu.ram[0xff70], 6)
        for tick, delta in product((0, 127, 254, 255), (0, 1, 127, 128, 255)):
            cpu = self.admission()
            cpu.field('hVBlankCounter', tick)
            cpu.field('wPokedexAnimDeadline', (tick+1+delta) & 255)
            cpu.run('Pokedex_AdmitAnimationFinish')
            self.assertEqual(bool(cpu.f & 0x10), delta < 128)

    def test_unsupported_hardware_and_short_tail_fail_closed(self):
        for port, value in ((0xff4d, 0x80), (0xff40, 0), (0xff07, 5),
                            (0xff07, 7), (0xff06, 57), (0xff06, 55),
                            (0xff41, 1)):
            cpu = self.admission()
            cpu.ram[port] = value
            cpu.run('Pokedex_AdmitAnimationFinish')
            self.assertFalse(cpu.f & 0x10)
        for name, value in (('hLCDCPointer', 1), ('wSampledCryBlockPeriod', 201)):
            cpu = self.admission()
            cpu.field(name, value)
            cpu.run('Pokedex_AdmitAnimationFinish')
            self.assertFalse(cpu.f & 0x10)
        for remaining in (0, 1, 3):
            cpu = self.admission()
            cpu.field('hSampledCryBlocks', remaining, 2)
            cpu.field('wSampledCryCacheCount', remaining)
            cpu.run('Pokedex_AdmitAnimationFinish')
            self.assertTrue(cpu.f & 0x10)

    def test_quiet_acquisition_and_release(self):
        requests = ('hVBlank', 'hBGMapUpdate', 'hCGBPalUpdate', 'hDMATransfer',
                    'hBGMapMode', 'hMapAnims', 'wRequested1bppSize',
                    'wRequested2bppSize', 'wPokedexOwnerTransition')
        for bad in (None, *requests, 0xff42, 0xff43, 0xff4a, 0xff4b):
            cpu = self.cpu()
            cpu.field('hVBlankCounter', 0)
            cpu.field('wPokedexAnimLoopTick', 255)
            if isinstance(bad, str):
                cpu.field(bad, 1)
            elif bad:
                cpu.ram[bad] = 1
            cpu.run('Pokedex_AcquireQuietAnimationOwner')
            self.assertEqual(bool(self.value(cpu, 'hVBlank') & 0x80), bad is None)
            self.assertEqual(self.value(cpu, 'wPokedexAnimLoopTick'), 255)
            if bad is None:
                self.assertEqual(self.value(cpu, 'wPokedexAnimWorkTick'), 255)
                self.assertEqual(self.value(cpu, 'hOAMUpdate'), 1)
        for handler, flags in product((0, 7), (3, 15, 0x23, 0x43)):
            cpu = self.cpu()
            cpu.field('hVBlank', handler)
            cpu.field('wPokedexAnimFlags', flags)
            cpu.run('Pokedex_AcquireQuietAnimationOwner')
            self.assertEqual(bool(self.value(cpu, 'hVBlank') & 0x80), not flags & 0x60)
        # The common early-paging case releases a queued map, cancels it, then
        # reveals another species while the now-idle Dex handler is still 7.
        cpu = self.cpu()
        cpu.field('hVBlank', 0x87)
        cpu.field('wPokedexAnimFlags', 0x23)
        cpu.run('Pokedex_CancelAnimationPrefetch')
        cpu.field('wPokedexAnimFlags', 15)
        cpu.run('Pokedex_AcquireQuietAnimationOwner')
        self.assertEqual(self.value(cpu, 'hVBlank'), 0x80)
        for handler in range(8):
            cpu = self.cpu()
            cpu.field('hVBlank', 0x80 | handler)
            cpu.field('hOAMUpdate', 1)
            cpu.field('wPokedexAnimSchedulerControl', 3)
            cpu.run('Pokedex_ReleaseQuietAnimationOwner')
            self.assertEqual(self.value(cpu, 'hVBlank'), handler)
            self.assertEqual(self.value(cpu, 'hOAMUpdate'), 0)
            self.assertEqual(self.value(cpu, 'wPokedexAnimSchedulerControl'), 0)

    def test_finish_requires_one_complete_ready_hidden_remainder(self):
        def prepared(count):
            cpu = self.admission(count)
            for name, value in (
                ('hVBlank', 0x80), ('wPokedexAnimPlaybackState', 2),
                ('wPokedexAnimFlags', 7), ('wPokedexAnimStageSlot', 1),
                ('wPokedexAnimDisplaySlot', 0), ('wPokedexAnimStageTileCount', count),
                ('wPokedexAnimUploadOffset', 0), ('wPokedexAnimDictionaryTileCount', 127),
                ('wPokedexAnimDictionaryTilesRemaining', 0),
            ):
                cpu.field(name, value)
            cpu.block(self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460, bytes(range(49)))
            return cpu
        for count in range(1, 21):
            cpu = prepared(count)
            run_to(cpu, 'Pokedex_TryFinishAnimationStage', 'Pokedex_ServiceAnimationUploadChunk')
            self.assertEqual(self.value(cpu, 'wPokedexAnimSchedulerControl') & 2, 2)
        for name, value in (
            ('hVBlank', 0), ('wPokedexAnimSchedulerControl', 2),
            ('wPokedexAnimPlaybackState', 1), ('wPokedexAnimFlags', 3),
            ('wPokedexAnimFlags', 15), ('wPokedexAnimFlags', 23),
            ('wPokedexAnimFlags', 39), ('wPokedexAnimFlags', 71),
            ('wPokedexAnimStageSlot', 0), ('wPokedexAnimStageTileCount', 0),
            ('wPokedexAnimStageTileCount', 21), ('wPokedexAnimUploadOffset', 9),
            ('wPokedexAnimDictionaryTilesRemaining', 120),
        ):
            cpu = prepared(8)
            cpu.field(name, value)
            before = self.value(cpu, 'wPokedexAnimUploadOffset')
            cpu.run('Pokedex_TryFinishAnimationStage')
            self.assertEqual(self.value(cpu, 'wPokedexAnimUploadOffset'), before)

    def test_cancellation_preserves_outer_clock(self):
        cpu = self.cpu()
        cpu.field('hVBlank', 0x87)
        cpu.field('wPokedexAnimLoopTick', 255)
        cpu.run('Pokedex_CancelAnimationPrefetch')
        self.assertEqual(self.value(cpu, 'wPokedexAnimLoopTick'), 255)
        self.assertEqual(self.value(cpu, 'hVBlank'), 7)
        self.assertEqual(self.value(cpu, 'wPokedexAnimFlags'), 0)

    def test_owner_waits_only_if_this_iteration_has_not_crossed_vblank(self):
        for before, now in ((0, 1), (254, 255), (255, 0)):
            cpu = self.cpu()
            cpu.field('hVBlank', 0x80)
            cpu.field('wPokedexAnimLoopTick', before)
            cpu.field('hVBlankCounter', now)
            cpu.run('Pokedex_EndOwnerLoop')
            self.assertEqual(self.value(cpu, 'wPokedexAnimSchedulerControl'), 1)
        cpu = self.cpu()
        cpu.field('hVBlank', 0x80)
        cpu.field('wPokedexAnimLoopTick', 12)
        cpu.field('hVBlankCounter', 12)
        run_to(cpu, 'Pokedex_EndOwnerLoop', 'Pokedex_EndOwnerLoop.wait')
        self.assertEqual(self.value(cpu, 'wVBlankOccurred'), 1)
        # An interrupt after the clock read must not have its acknowledgment
        # overwritten by a later wait-arm store. Model that precise interleave.
        cpu = self.cpu()
        cpu.field('hVBlank', 0x80)
        cpu.field('wPokedexAnimLoopTick', 12)
        cpu.field('hVBlankCounter', 12)
        bank, pc = self.repo.symbols['Pokedex_EndOwnerLoop']
        cpu.bank, cpu.pc = bank, pc
        cpu.push(0xffff)
        injected = False
        while cpu.pc != self.repo.symbols['Pokedex_EndOwnerLoop.wait'][1]:
            reads_clock = (cpu.read(cpu.pc) == 0xf0 and
                           cpu.read(cpu.pc+1) == (self.repo.symbols['hVBlankCounter'][1] & 255))
            cpu.step()
            if reads_clock:
                cpu.field('hVBlankCounter', 13)
                cpu.field('wVBlankOccurred', 0)
                injected = True
        self.assertTrue(injected)
        self.assertEqual(self.value(cpu, 'wVBlankOccurred'), 0)
        cpu = self.cpu()
        run_to(cpu, 'Pokedex_EndOwnerLoop', 'DelayFrame')

    def test_pending_or_published_maps_are_not_requeued(self):
        for flags in (0x20, 0x40, 0x60):
            cpu = self.cpu()
            cpu.field('wPokedexAnimFlags', flags)
            cpu.set_pair(1, 0xcb9c)
            cpu.record_writes = True
            cpu.run('Pokedex_CommitAnimationFrontpicMap')
            # cpu.run installs hROMBank and a sentinel return on the test stack.
            stores = [addr for _, addr, _ in cpu.writes if not 0xc000 <= addr < 0xc100
                      and addr != self.repo.symbols['hROMBank'][1]]
            self.assertEqual(stores, [])

    def test_publication_window_and_critical_transfer_budget(self):
        for quiet, ly in product((False, True), (0, 143, 144, 145, 146, 148, 149, 153)):
            cpu = self.cpu()
            cpu.field('hVBlank', 0x87 if quiet else 7)
            cpu.field('wPokedexAnimFlags', 0x23)
            cpu.field('wPokedexAnimDeadline', 1)
            cpu.ram[0xff44] = ly
            cpu.run('Pokedex_VBlankAnimationFrontpicMap')
            self.assertEqual(bool(self.value(cpu, 'wPokedexAnimFlags') & 0x40),
                             144 <= ly < (149 if quiet else 146))
        maximum = 0
        for frame, published, late, carry, max_late in product(
                (0, 1), (0, 1, 255), (0, 1, 127), (0, 255), (0, 255)):
            cpu = self.cpu()
            for name, value in (
                ('hSampledCryTimer', 1), ('wGameTimerPaused', 1),
                ('wPokedexSelectedState', 1), ('hVBlank', 0x87),
                ('wPokedexAnimFlags', 0x23), ('wPokedexAnimDeadline', (1-late) & 255),
                ('hOAMUpdate', 1), ('wPokedexAnimStageFrameID', frame),
                ('wPokedexAnimDebugMapPublishes', published),
                ('wPokedexAnimDebugTotalLate', carry), ('wPokedexAnimDebugMaxLate', max_late),
            ):
                cpu.field(name, value)
            cpu.ram[0xff44] = 144
            begin, end = (offset(self.repo.symbols[n]) for n in ('OAMDMACode', 'OAMDMACode.End'))
            cpu.block(self.repo.symbols['hTransferShadowOAM'][1], self.repo.rom[begin:end])
            run_to(cpu, 'VBlank', 'Pokedex_VBlankAnimationFrontpicMap.have_cutoff')
            origin, stalls, critical = cpu.cycles, 0, 0
            cpu.record_writes = True
            while cpu.pc != self.repo.symbols['VBlank_Normal.done_oam'][1]:
                start = len(cpu.writes)
                cpu.step()
                for _, address, value in cpu.writes[start:]:
                    if address == 0xff55:
                        self.assertFalse(value & 128)
                        stalls += (value+1)*32+4
                        critical = max(critical, cpu.cycles-origin+stalls)
                    self.assertNotIn(address, (0xff42, 0xff43, 0xff4a, 0xff4b, 0xff46))
            maximum = max(maximum, critical)
        margin = (154-148)*456-455-maximum
        self.assertGreater(margin, 0)
        print(f'Quiet publication: critical <= {maximum} T; latest-accepted LY margin >= {margin} T')


if __name__ == '__main__':
    unittest.main()
