#!/usr/bin/env python3
"""Clock, publication and cache checks for the Listing-restoration observer."""
import unittest

from dex_timing.listing_restoration import (
    check_listing_snapshot, physical_vblank_bounds, restoration_failures,
)


class ListingRestorationTimingTests(unittest.TestCase):
    def line(self, line, boundary):
        return dict(event='line', physical_line=line, boundary_t=boundary, t=boundary + 4)

    def test_uses_physical_boundaries_not_callback_batch_end(self):
        trace = [self.line(144, 0), self.line(0, 4560)]
        self.assertEqual(physical_vblank_bounds(trace, 364), (0, 4560))
        self.assertEqual(physical_vblank_bounds(trace, 364)[1] - 364, 4196)

    def test_ly_zero_during_physical_line_153_is_not_frame_start(self):
        trace = [self.line(144, 0),
                 dict(event='phase', t=4200, ly=0, physical_line=153),
                 self.line(0, 4560)]
        self.assertEqual(physical_vblank_bounds(trace, 364), (0, 4560))

    def test_selects_current_commit_interval(self):
        trace = [self.line(144, 0), self.line(0, 4560),
                 self.line(144, 70224), self.line(0, 74784)]
        self.assertEqual(physical_vblank_bounds(trace, 70588), (70224, 74784))

    def test_lcd_restart_interval_is_not_accepted_as_full_vblank(self):
        trace = [self.line(144, 0), self.line(0, 528)]
        with self.assertRaisesRegex(ValueError, 'Physical VBlank boundaries'):
            physical_vblank_bounds(trace, 364)


class ListingPublicationTests(unittest.TestCase):
    def summary(self):
        return dict(blocked_palette_writes=[], visible_palette_mismatch_bytes=dict(bg=[], obj=[]),
                    white_frames=0, lcd_changes=[], maps_vblank_margin=500, palette_write_count=96,
                    bg_palette_first_use_margin=6000, obj_palette_first_use_margin=3000,
                    oam_first_use_margin=2000)

    def test_guarded_publication_passes_without_single_vblank_return_requirement(self):
        summary = self.summary()
        summary['return_vblank_margin'] = -6000
        self.assertEqual(restoration_failures(summary), [])

    def test_rejected_write_fails_even_if_old_palette_happens_to_match(self):
        summary = self.summary()
        summary['blocked_palette_writes'] = [dict(address=0xff6b)]
        self.assertIn('blocked_palette_write', restoration_failures(summary))

    def test_lcd_flash_fails(self):
        summary = self.summary()
        summary.update(white_frames=1, lcd_changes=[dict(address=0xff40)])
        self.assertEqual(restoration_failures(summary), ['white_frame', 'lcd_toggled'])

    def test_each_publication_boundary_is_required(self):
        for name in ('maps_vblank_margin', 'bg_palette_first_use_margin',
                     'obj_palette_first_use_margin', 'oam_first_use_margin'):
            with self.subTest(name=name):
                summary = self.summary()
                summary[name] = 0
                self.assertEqual(restoration_failures(summary), [name])

    def test_complete_palette_payload_is_required(self):
        summary = self.summary()
        summary['palette_write_count'] = 95
        self.assertEqual(restoration_failures(summary), ['palette_write_count'])


class ListingCacheTests(unittest.TestCase):
    def snapshot(self, scroll=3, top=1):
        tags = bytearray(10)
        vram = bytearray(0x4000)
        for delta in range(-1, 4):
            slot = (top + delta) % 5
            tag = max(-1, scroll + delta * 3) & 65535
            tags[slot * 2:slot * 2 + 2] = tag.to_bytes(2, 'little')
            for start in (0x2000, 0x3000, 0x2d20):
                vram[start + slot * 128:start + (slot + 1) * 128] = bytes([tag & 255]) * 128
        return dict(listing_scroll=scroll, grid_top=top, grid_tags=tags.hex(), vram=vram.hex(),
                    grid_presence=bytes(int(scroll + i < 373) for i in range(9)).hex(),
                    grid_flags='01' * 9, grid_palettes='02' * 9,
                    bg_pal='03' * 64, obj_pal='04' * 64,
                    target_bg='03' * 64, target_obj='04' * 64)

    def test_ring_rotation_compares_absolute_rows(self):
        self.assertEqual(check_listing_snapshot(self.snapshot(top=3), self.snapshot(), 373), [])

    def test_corrupted_visible_tile_is_detected(self):
        actual = self.snapshot()
        vram = bytearray.fromhex(actual['vram'])
        vram[0x2000 + 128] ^= 1
        actual['vram'] = vram.hex()
        self.assertIn('cache_tiles_3', check_listing_snapshot(actual, self.snapshot(), 373))

    def test_unused_look_behind_bytes_do_not_require_blank_tiles(self):
        actual = self.snapshot(scroll=0)
        vram = bytearray.fromhex(actual['vram'])
        vram[0x2000] ^= 1
        actual['vram'] = vram.hex()
        self.assertEqual(check_listing_snapshot(actual, self.snapshot(scroll=0), 373), [])

    def test_navigation_may_invalidate_unused_end_look_ahead(self):
        actual = self.snapshot(scroll=366)
        tags = bytearray.fromhex(actual['grid_tags'])
        tags[8:10] = b'\xff\xff'
        actual['grid_tags'] = tags.hex()
        expected = self.snapshot(scroll=366)
        self.assertEqual(check_listing_snapshot(actual, expected, 373, all_rows=False), [])
        self.assertIn('cache_tag_4', check_listing_snapshot(actual, expected, 373))

    def test_temporary_id_lifetime_is_separate_from_graphics_acceptance(self):
        actual, expected = self.snapshot(), self.snapshot()
        actual['grid_indices'], expected['grid_indices'] = [0] * 9, list(range(1, 10))
        self.assertEqual(check_listing_snapshot(actual, expected, 373), [])

    def test_retained_id_cannot_pass_as_presence(self):
        actual = self.snapshot()
        actual['grid_presence'] = '010101525354010101'
        problems = check_listing_snapshot(actual, self.snapshot(), 373)
        self.assertIn('grid_presence_not_boolean', problems)
        self.assertIn('grid_presence', problems)

    def test_unseen_entry_is_still_occupied(self):
        actual = self.snapshot()
        actual['grid_flags'] = '00' * 9
        expected = dict(actual)
        self.assertEqual(check_listing_snapshot(actual, expected, 373), [])
        actual['grid_presence'] = '00' + '01' * 8
        self.assertIn('grid_presence', check_listing_snapshot(actual, expected, 373))

    def test_partial_final_row_has_only_real_entries_occupied(self):
        actual = self.snapshot(scroll=366)
        self.assertEqual(actual['grid_presence'], '010101010101010000')
        self.assertEqual(check_listing_snapshot(actual, self.snapshot(scroll=366), 373), [])
        actual['grid_presence'] = '01' * 9
        self.assertIn('grid_presence', check_listing_snapshot(actual, self.snapshot(scroll=366), 373))

    def test_truncated_presence_array_fails(self):
        actual = self.snapshot()
        actual['grid_presence'] = '01' * 8
        self.assertIn('grid_presence', check_listing_snapshot(actual, self.snapshot(), 373))


if __name__ == '__main__':
    unittest.main()
