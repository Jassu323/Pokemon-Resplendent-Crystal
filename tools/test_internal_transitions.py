#!/usr/bin/env python3
"""Publication-order checks for the host-only internal transition observer."""
import unittest
from pathlib import Path

from dex_timing.assets import Repository, offset
from dex_timing.costs import machine, run_to
from dex_timing.internal_transitions import summarize


class InternalTransitionTests(unittest.TestCase):
    def trace(self):
        names = ('change', 'hidden', 'stage', 'static_prepare', 'static_upload',
                 'static_ready', 'prime', 'prime_done', 'layout_done',
                 'stage_maps', 'copy_backing', 'reveal', 'revealed')
        return [dict(event='phase', phase=name, t=100 + i * 10, ly=144,
                     physical_line=144, display=i, pal_update=0,
                     header_hash='incoming' if name == 'revealed' else 'outgoing')
                for i, name in enumerate(names)]

    def frame(self, t, display, header, black=False):
        return dict(event='frame', t=t, display=display, pal_update=0, state=2,
                    black=black, header_hash=header, front_hash='portrait')

    def test_black_staging_is_not_mixed_identity(self):
        trace = self.trace() + [self.frame(160, 1, 'black', True)]
        result = summarize(trace, [])
        self.assertEqual(result['black_frames'], 1)
        self.assertEqual(result['visible_staging_frames'], [])
        self.assertEqual(result['unexpected_visible_header_frames'], [])

    def test_same_type_header_hash_cannot_hide_premature_reveal(self):
        trace = self.trace() + [self.frame(160, 1, 'outgoing')]
        result = summarize(trace, [])
        self.assertEqual(result['unexpected_visible_header_frames'], [])
        self.assertEqual(result['visible_staging_frames'], [1])

    def test_old_page_can_remain_visible_during_ram_preparation(self):
        trace = self.trace() + [self.frame(140, 1, 'outgoing')]
        self.assertEqual(summarize(trace, [])['visible_staging_frames'], [])

    def test_palette_flush_before_reveal_is_reported(self):
        trace = self.trace() + [dict(event='phase', phase='palette_flush', t=185,
                                    ly=145, physical_line=145, display=8,
                                    pal_update=1, header_hash='outgoing')]
        trace.sort(key=lambda e: e['t'])
        self.assertEqual(summarize(trace, [])['early_palette_flushes'],
                         [dict(t=185, ly=145, physical_line=145)])

    def test_outgoing_publication_is_not_incoming_start(self):
        events = [dict(event='publish', t=99), dict(event='publish', t=250)]
        self.assertEqual(summarize(self.trace(), events)['first_publication_t'], 250)

    def test_blocked_palette_write_remains_a_separate_failure(self):
        write = dict(event='write', t=190, address=0xff69, pal_blocked=True)
        self.assertEqual(summarize(self.trace() + [write], [])['blocked_palette_writes'], [write])

    def test_ly_zero_on_physical_line_153_is_still_vblank(self):
        trace = self.trace() + [dict(event='phase', phase='fast_commit', t=190,
            ly=144, physical_line=144, display=8, pal_update=0, header_hash='outgoing'),
            dict(event='phase', phase='fast_commit_done', t=210, ly=0,
                 physical_line=153, display=8, pal_update=0, header_hash='outgoing'),
            dict(event='write', t=205, address=0xff69, pal_blocked=False,
                 ly=0, physical_line=153)]
        self.assertEqual(summarize(trace, [])['publication_outside_vblank'], [])
        trace[-1]['physical_line'] = 0
        self.assertEqual(summarize(trace, [])['publication_outside_vblank'], [trace[-1]])


class LinkedTransitionContracts(unittest.TestCase):
    """Frozen-register instruction contracts; timed DMA is tested in SameBoy."""
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        if not (root / 'pokecrystal.gbc').exists():
            raise unittest.SkipTest('Production ROM has not been built')
        cls.repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')

    def cpu(self):
        cpu = machine(self.repo)
        cpu.allowed_io.update((0xff41, 0xff46, 0xff47, 0xff48, 0xff4a, 0xff4b,
                               *range(0xff51, 0xff56), *range(0xff68, 0xff6c)))
        cpu.ram[0xff41] = 1
        begin, end = (offset(self.repo.symbols[n]) for n in ('OAMDMACode', 'OAMDMACode.End'))
        cpu.block(self.repo.symbols['hTransferShadowOAM'][1], self.repo.rom[begin:end])
        return cpu

    def value(self, cpu, name):
        return cpu.read(self.repo.symbols[name][1])

    def test_palette_staging_does_not_request_or_publish_hardware_colors(self):
        for bank in (1, 3, 5, 7):
            cpu = self.cpu()
            source = bytes(range(8))
            bg = bytes(range(64))
            cpu.field('wOBPals1', int.from_bytes(source, 'little'), len(source))
            cpu.field('wBGPals2', int.from_bytes(bg, 'little'), len(bg))
            cpu.ram[0xff70] = bank
            cpu.record_writes = True
            cpu.run('PokedexSelectedMon_StageUsualPals')
            self.assertEqual(cpu.ram[0xff70], bank)
            self.assertEqual((cpu.ram[0xff47], cpu.ram[0xff48]), (0xe4, 0xe0))
            self.assertEqual(self.value(cpu, 'hCGBPalUpdate'), 0)
            self.assertFalse(any(a in (0xff69, 0xff6b) for _, a, _ in cpu.writes))
            palette_bank, address = self.repo.symbols['wOBPals2']
            self.assertEqual(bytes(cpu.wram[palette_bank][address - 0xd000:address - 0xd000 + 8]),
                             source[:2] * 2 + source[4:])
            palette_bank, address = self.repo.symbols['wBGPals2']
            self.assertEqual(bytes(cpu.wram[palette_bank][address - 0xd000:address - 0xd000 + 64]), bg)

    def test_internal_publication_owns_stat_bg_and_type_obj_palettes_and_restores_banks(self):
        cpu = self.cpu()
        payload = bytes(range(64))
        cpu.field('wBGPals2', int.from_bytes(payload, 'little'), len(payload))
        cpu.field('wOBPals2', int.from_bytes(payload, 'little'), len(payload))
        cpu.field('wPokedexOwnerTransition', 3)
        cpu.field('wPokedexSelectedBGPaletteDirty', 0xff)
        cpu.field('wPokedexSelectedOBJPaletteDirty', 0xff)
        cpu.ram[0xff44], cpu.ram[0xff70], cpu.ram[0xff4f] = 144, 6, 1
        cpu.record_writes = True
        cpu.run('Pokedex_VBlankOwnerTransition')
        self.assertTrue(cpu.f & 0x10)
        self.assertEqual(bytes(v for _, a, v in cpu.writes if a == 0xff69),
                         payload)
        self.assertEqual(bytes(v for _, a, v in cpu.writes if a == 0xff6b), payload[:48])
        self.assertEqual([v for _, a, v in cpu.writes if a == 0xff55], [35, 35])
        self.assertEqual(sum(a == 0xff46 for _, a, _ in cpu.writes), 1)
        self.assertEqual((cpu.ram[0xff70], cpu.ram[0xff4f]), (6, 1))
        for field in ('wPokedexOwnerTransition', 'wPokedexSelectedBGPaletteDirty',
                      'wPokedexSelectedOBJPaletteDirty'):
            self.assertEqual(self.value(cpu, field), 0)

    def test_late_or_competing_publication_leaves_request_pending(self):
        for ly, competing in ((0, None), (143, None), (145, None), (153, None),
                              (144, 'hBGMapUpdate'), (144, 'hDMATransfer')):
            cpu = self.cpu()
            cpu.field('wPokedexOwnerTransition', 3)
            cpu.field('wPokedexSelectedBGPaletteDirty', 0xff)
            if competing:
                cpu.field(competing, 1)
            cpu.ram[0xff44] = ly
            cpu.record_writes = True
            cpu.run('Pokedex_VBlankOwnerTransition')
            self.assertEqual(self.value(cpu, 'wPokedexOwnerTransition'), 3)
            self.assertEqual(self.value(cpu, 'wPokedexSelectedBGPaletteDirty'), 0xff)
            ports = (0xff46, 0xff4a, 0xff4b, 0xff4f, 0xff70,
                     *range(0xff51, 0xff56), *range(0xff68, 0xff6c))
            self.assertFalse(any(a in ports for _, a, _ in cpu.writes))

    def test_internal_mask_changes_only_the_portrait_target(self):
        cpu = self.cpu()
        bg, obj = bytes(range(64)), bytes(range(64, 128))
        cpu.field('wBGPals2', int.from_bytes(bg, 'little'), len(bg))
        cpu.field('wOBPals2', int.from_bytes(obj, 'little'), len(obj))
        cpu.field('wPokedexSelectedState', 2)
        cpu.ram[0xff70] = 3
        cpu.run('Pokedex_BlackOutSelectedMonBG')
        bank, at = self.repo.symbols['wBGPals2']
        actual = bytes(cpu.wram[bank][at - 0xd000:at - 0xd000 + 64])
        self.assertEqual(actual, bg[:8] + b'\xff\x7f' * 4 + bg[16:])
        bank, at = self.repo.symbols['wOBPals2']
        self.assertEqual(bytes(cpu.wram[bank][at - 0xd000:at - 0xd000 + 64]), obj)
        self.assertEqual(cpu.ram[0xff70], 3)

    def test_internal_mask_holds_oam_until_the_owner_handoff(self):
        cpu = self.cpu()
        oam = bytes(range(160))
        cpu.field('wShadowOAM', int.from_bytes(oam, 'little'), len(oam))
        cpu.field('wPokedexSelectedState', 2)
        run_to(cpu, 'PokedexSelectedMon_BeginHiddenTransition', 'DelayFrame')
        self.assertEqual(self.value(cpu, 'hOAMUpdate'), 1)
        self.assertEqual(self.value(cpu, 'hCGBPalUpdate'), 1)
        at = self.repo.symbols['wShadowOAM'][1]
        self.assertEqual(bytes(cpu.read(at + i) for i in range(160)), oam)


if __name__ == '__main__':
    unittest.main()
