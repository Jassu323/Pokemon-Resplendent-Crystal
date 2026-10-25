import unittest
from types import SimpleNamespace

from dex_timing.performance import HZ, T, result_timing, summarize
from dex_timing.listing_restoration import summarize as restoration_summary
from dex_timing.cold_listing import audit
from dex_timing.performance_audio import audio_segments, compare_playback


class PerformanceMeasurementTests(unittest.TestCase):
    def frame(self, at, value, display=1):
        return dict(event='perf_frame', t=at, lower=value, stable=value,
                    full=value, display=display)

    def test_physical_intervals_and_ms_share_the_same_clock(self):
        events = [self.frame(T, 2), self.frame(2 * T, 3, 2)]
        row = result_timing(events, {'lower': 1}, {'lower': 3},
                            'lower', 0, 16)
        self.assertEqual(row['first_visible']['frames'], 1)
        self.assertEqual(row['first_visible']['cycles'], T)
        self.assertAlmostEqual(row['first_visible']['ms'], 1000 * T / HZ)

    def test_unchanged_page_is_not_a_zero_latency_publication(self):
        row = result_timing([self.frame(T, 1), self.frame(2 * T, 1)],
                            {'lower': 1}, {'lower': 1}, 'lower', 0, 16)
        self.assertTrue(row['no_pixel_change'])
        self.assertIsNone(row['first_visible'])
        self.assertIsNone(row['complete_visible'])

    def test_changes_before_acceptance_do_not_count_as_input_response(self):
        row = result_timing([self.frame(10, 2), self.frame(T, 3),
                             self.frame(2 * T, 3)],
                            {'lower': 1}, {'lower': 3}, 'lower', 0, 100)
        self.assertEqual(row['first_visible']['cycles'], T)

    def test_rapid_final_target_must_occur_after_final_release(self):
        events = [self.frame(T, 2), self.frame(2 * T, 3),
                  self.frame(3 * T, 2), self.frame(4 * T, 2)]
        row = result_timing(events, {'lower': 1}, {'lower': 2},
                            'lower', 0, 16, completion_after=2 * T + 1)
        self.assertEqual(row['first_visible']['cycles'], T)
        self.assertEqual(row['complete_visible']['cycles'], 3 * T)

    def test_inclusive_parent_costs_are_not_added_to_children(self):
        events = [self.frame(T, 2), self.frame(2 * T, 2),
                  dict(event='perf_cost', name='parent', elapsed=100),
                  dict(event='perf_cost', name='child', elapsed=60)]
        row = result_timing(events, {'lower': 1}, {'lower': 2},
                            'lower', 0, 16)
        self.assertEqual(row['costs']['parent']['total_cycles'], 100)
        self.assertEqual(row['costs']['child']['total_cycles'], 60)

    def test_summary_keeps_first_and_complete_separate(self):
        rows = [dict(action='area', phase='settled', status='pass',
                     first_visible={'frames': 2}, complete_visible={'frames': 15})]
        entry = summarize(rows)[0]
        self.assertEqual(entry['first_visible']['median_frames'], 2)
        self.assertEqual(entry['complete_visible']['median_frames'], 15)

    def test_species_mask_is_response_but_not_panel_completion(self):
        events = [dict(event='perf_frame', t=T, full=2, stable=1, display=1),
                  dict(event='perf_frame', t=2 * T, full=3, stable=3, display=2),
                  dict(event='perf_frame', t=3 * T, full=3, stable=3, display=3)]
        row = result_timing(events, {'full': 1, 'stable': 1},
                            {'full': 3, 'stable': 3}, 'stable', 0, 16,
                            first_key='full')
        self.assertEqual(row['first_visible']['frames'], 1)
        self.assertEqual(row['complete_visible']['frames'], 2)

    def test_listing_summary_ignores_an_earlier_species_publication(self):
        def phase(name, t):
            return dict(event='phase', phase=name, t=t, ly=145, stat=1,
                        physical_line=145, display=1, bg_dirty=0, obj_dirty=0,
                        state=5, owner_transition=2, vram='', bg_pal='', obj_pal='',
                        target_bg='', target_obj='')
        trace = [phase('owner_dispatch', 100), phase('owner_wx', 110),
                 phase('bg_pal_commit', 120), phase('owner_done', 130),
                 phase('owner_returned', 140), phase('leave', 1000),
                 dict(event='line', physical_line=144, boundary_t=1100),
                 phase('owner_dispatch', 1200), phase('owner_wx', 1210),
                 phase('listing_bg_pal_commit', 1220), phase('owner_oam_return', 1230),
                 phase('owner_done', 1240), phase('owner_returned', 1250),
                 phase('listing_revealed', 1260),
                 dict(event='line', physical_line=0, boundary_t=5660)]
        row = restoration_summary(trace, {'vram': ''})
        self.assertEqual(row['commit_cycles'], 40)
        self.assertEqual(row['maps_vblank_margin'], 4440)
        self.assertEqual(row['return_cycles'], 260)


class AudioComparisonTests(unittest.TestCase):
    def row(self, wave='0001', tac=6, remaining=0):
        events = [dict(event='perf_phase', name='audio_arm', t=0, remaining=2),
                  dict(event='wave_block', wave=wave, frequency=1848, speed=0, t=10),
                  dict(event='perf_phase', name='timer_block', t=12800, tac=tac, tma=56),
                  dict(event='perf_phase', name='timer_block', t=25600, tac=tac, tma=56),
                  dict(event='audio_stop', t=25620, remaining=remaining)]
        return dict(issues=[], segments=audio_segments(events))

    def test_timer_entry_jitter_does_not_change_sample_identity(self):
        a, b = self.row(), self.row()
        b['segments'][0]['median_period'] += 4
        self.assertEqual(compare_playback(a, b), [])

    def test_comparison_rejects_wave_timer_and_exhaustion_changes(self):
        for row, key in ((self.row(wave='0100'), 'wave_sha256'),
                         (self.row(tac=7), 'timer_configs'),
                         (self.row(remaining=1), 'exhaustion')):
            self.assertTrue(any(key in issue for issue in compare_playback(self.row(), row)))

    def test_rejected_setup_is_not_counted_as_a_playback_pass(self):
        row = self.row()
        row['issues'] = ['menu not reached']
        self.assertEqual(compare_playback(self.row(), row), ['test setup rejected'])


class PlaybackClockAuditTests(unittest.TestCase):
    def clock_issues(self, accepted_speed, final_speed, expected=0):
        asset = SimpleNamespace(width=7, sample_blocks=0, events=[])
        accepted = dict(loaded=49, dictionary_services=0, upload_services=0,
                        double_speed=accepted_speed, t=0)
        final = dict(playback=3, audio=0, sfx=0, double_speed=final_speed)
        return audit(asset, accepted, [], final, expected_double_speed=expected)['issues']

    def test_normal_contract_rejects_double_speed_at_either_endpoint(self):
        for accepted, final in ((1, 0), (0, 1), (1, 1)):
            self.assertIn('unexpected_double_speed', self.clock_issues(accepted, final))

    def test_prototype_contract_still_rejects_a_speed_leak(self):
        self.assertNotIn('unexpected_double_speed', self.clock_issues(1, 1, 1))
        for accepted, final in ((0, 1), (1, 0), (0, 0)):
            self.assertIn('unexpected_double_speed', self.clock_issues(accepted, final, 1))


if __name__ == '__main__':
    unittest.main()
