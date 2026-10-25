#!/usr/bin/env python3
"""Negative controls for the actual-input cold Listing audit."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from dex_timing.assets import Event, Plan
from dex_timing.cold_listing import FRAME, audit, expected_picture, predecessor
from dex_timing.recovery_experiment import initial_asset_maps


class ColdListingTests(unittest.TestCase):
    def fixture(self):
        asset = SimpleNamespace(width=7, dictionary=b''.join(bytes([i]) * 16 for i in range(50)),
            plans=[Plan(49, ()), Plan(50, ((0, 49), (129, 8)))],
            events=[Event(1, 4, 50), Event(0, 3, 50)], sample_blocks=100)
        accepted = dict(loaded=49, dictionary_services=0, upload_services=0, t=0)
        final = dict(playback=3, audio=0, sfx=0)
        events = []
        for i, (frame, elapsed) in enumerate(((1, 0), (0, 4), (0, 7))):
            events.append(dict(event='publish', t=FRAME * (elapsed + 8), tick=(253 + elapsed) & 255,
                frame=frame, ordinal=i + 1, slot=i & 1, ly=148,
                map=b''.join(initial_asset_maps(asset, frame, i & 1)).hex(),
                picture=expected_picture(asset, frame).hex()))
        events.append(dict(event='reveal', t=6 * FRAME,
            map=b''.join(initial_asset_maps(asset, 0, 0)).hex(), picture=expected_picture(asset, 0).hex()))
        events.append(dict(event='audio_stop', remaining=0, t=20 * FRAME))
        return asset, accepted, events, final

    def test_clean_sampled_playback_with_counter_wrap(self):
        result = audit(*self.fixture())
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['actual_intervals'], 7)

    def test_warming_cannot_pass_as_cold(self):
        for key in ('loaded', 'dictionary_services', 'upload_services'):
            args = self.fixture()
            args[1][key] += 1
            self.assertIn('not_cold', audit(*args)['issues'])

    def test_initial_static_portrait_is_checked(self):
        args = self.fixture()
        args[2][-2]['picture'] = bytes(49 * 16).hex()
        self.assertIn('static_reveal_tiles', audit(*args)['issues'])

    def test_normal_speed_is_required(self):
        args = self.fixture()
        args[1]['double_speed'] = 1
        self.assertIn('unexpected_double_speed', audit(*args)['issues'])

    def test_explicit_animation_and_audio_misses(self):
        for kind in ('animation_miss', 'audio_miss'):
            args = self.fixture()
            args[2].append(dict(event=kind))
            self.assertIn(kind, audit(*args)['issues'])

    def test_sampled_completion_requires_a_natural_stop(self):
        for missing in (True, False):
            args = self.fixture()
            if missing:
                args[2].pop()
            else:
                args[2][-1]['remaining'] = 1
            self.assertIn('sampled_cry_incomplete', audit(*args)['issues'])

    def test_synth_does_not_require_sampled_stop(self):
        args = self.fixture()
        args[0].sample_blocks = 0
        args[2].pop()
        self.assertEqual(audit(*args)['issues'], [])

    def test_tilemap_and_pixels_are_independent(self):
        for field, issue in (('map', 'tilemap_event_1'), ('picture', 'tile_pixels_event_1')):
            args = self.fixture()
            data = bytearray.fromhex(args[2][0][field])
            data[0] ^= 1
            args[2][0][field] = data.hex()
            self.assertIn(issue, audit(*args)['issues'])

    def test_late_event_is_not_hidden_by_completion(self):
        args = self.fixture()
        args[2][1]['tick'] += 1
        self.assertIn('timeline_event_2', audit(*args)['issues'])

    def test_whole_counter_wrap_stall_is_not_hidden(self):
        args = self.fixture()
        args[2][1]['t'] += FRAME * 256
        self.assertIn('hardware_interval_event_2', audit(*args)['issues'])

    def test_missing_or_duplicated_publication(self):
        for duplicate in (True, False):
            args = self.fixture()
            if duplicate:
                args[2].insert(1, deepcopy(args[2][0]))
            else:
                args[2].pop(1)
            self.assertIn('publication_count', audit(*args)['issues'])

    def test_vblank_and_completion_checks(self):
        args = self.fixture()
        args[2][0]['ly'] = 140
        args[3]['sfx'] = 1
        issues = audit(*args)['issues']
        self.assertIn('publication_outside_vblank_1', issues)
        self.assertIn('playback_not_finished', issues)

    def test_small_portrait_padding_and_column_major_dictionary(self):
        asset = SimpleNamespace(width=5,
            dictionary=b''.join(bytes([i + 1]) * 16 for i in range(25)), plans=[Plan(25, ())])
        pic = expected_picture(asset, 0)
        self.assertEqual(pic[:7 * 2 * 16], bytes(7 * 2 * 16))
        self.assertEqual(pic[(2 * 7 + 1) * 16:(2 * 7 + 2) * 16], bytes([1]) * 16)
        self.assertEqual(pic[(2 * 7 + 2) * 16:(2 * 7 + 3) * 16], bytes([6]) * 16)

    def test_every_species_has_adjacent_in_range_predecessor(self):
        for index in range(373):
            prior, direction = predecessor(index)
            self.assertTrue(0 <= prior < 373)
            self.assertNotEqual(prior, index)
            self.assertEqual(index - prior, dict(left=-1, right=1, down=3)[direction])


if __name__ == '__main__':
    unittest.main()
