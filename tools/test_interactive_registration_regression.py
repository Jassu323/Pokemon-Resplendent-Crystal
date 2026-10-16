"""Host-only tests for exhaustive coverage and physical timing calculations."""
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from dex_timing.interactive_registration_regression import (
    FRAME, HZ, REPRESENTATIVE, ROOT, coverage_plan, fnv, frame_matches,
    metric_stats, operation_group, operations, species_constants, timing, latency_targets)


class InteractiveRegistrationHarnessTests(unittest.TestCase):
    def test_latency_diagnostics_follow_actual_alerts_not_previous_species(self):
        table=dict(alerts=[dict(species='diglett',operation='view1-wrap'),
            dict(species='farfetch_d',operation='view1-page0'),
            dict(species='diglett',operation='view1-wrap')])
        with patch.object(Path,'read_text',return_value=json.dumps(table)):
            self.assertEqual(latency_targets(dict(output='unused')),
                [('diglett','view1-wrap'),('farfetch_d','view1-page0')])

    def test_twenty_representatives_exist(self):
        names = {n.lower().replace('porygon_z', 'porygonz') for n in species_constants(ROOT)}
        self.assertEqual(len(REPRESENTATIVE), 20)
        self.assertEqual(len(set(REPRESENTATIVE)), 20)
        self.assertLessEqual(set(REPRESENTATIVE), names)

    def test_every_page_and_directed_tab_pair(self):
        row = dict(info_pages=5, moves_pages=19)
        cases = operations(row)
        self.assertEqual({(x['source'], x['view']) for x in cases if 'source' in x},
                         {(a, b) for a in range(3) for b in range(3) if a != b})
        self.assertEqual({x['page'] for x in cases if x['view'] == 1}, set(range(5)))
        self.assertEqual({x['page'] for x in cases if x['view'] == 2}, set(range(19)))
        self.assertEqual({x['page'] for x in cases if x['view'] == 0}, {0, 1})

    def test_one_page_info_wrap_is_valid(self):
        cases = operations(dict(info_pages=1, moves_pages=1))
        self.assertFalse(any(x['view'] == 1 and x['page'] == 1 for x in cases))
        self.assertEqual([x['page'] for x in cases if x['name'] == 'view1-wrap'], [0])

    def test_pending_and_transition_are_not_complete(self):
        frame = dict(view=1, info_page=2, info_state=0, info_pending=0, transition=0)
        self.assertTrue(frame_matches(frame, 1, 2))
        for field in ('info_state', 'info_pending', 'transition'):
            self.assertFalse(frame_matches(dict(frame, **{field: 1}), 1, 2))

    def test_physical_publication_and_display_are_distinct(self):
        accepted = 1000
        events = [dict(event='interactive_phase', point='info_request', t=accepted),
                  dict(event='interactive_phase', point='info_published', t=accepted + FRAME,
                       view=1, info_page=0, display=1),
                  dict(event='interactive_frame', t=accepted + 2 * FRAME, display=2,
                       view=1, info_page=0, info_state=0, info_pending=0, transition=0,
                       upper=11, panel=22)]
        result = timing(events, 0, 1, 0, dict(upper=11, panel=22))
        self.assertEqual(result['request_to_published']['display_frames'], 1)
        self.assertEqual(result['request_to_displayed']['display_frames'], 2)
        self.assertAlmostEqual(result['request_to_published']['ms'], FRAME * 1000 / HZ)
        self.assertTrue(result['pixel_parity'])

    def test_stale_identical_frame_cannot_complete_a_fresh_wrap(self):
        def frame(t, display):
            return dict(event='interactive_frame', t=t, display=display, view=2,
                        moves_page=0, moves_state=0, transition=0, upper=11, panel=22)
        events = [frame(100, 1),
                  dict(event='interactive_phase', point='moves_request', t=1000),
                  frame(1100, 2),
                  dict(event='interactive_phase', point='moves_published', t=2000,
                       display=3, view=2, moves_page=0),
                  frame(3000, 4)]
        result = timing(events, 0, 2, 0, dict(upper=11, panel=22))
        self.assertEqual(result['complete_visible_t'], 3000)
        self.assertEqual(result['request_to_displayed']['t_cycles'], 2000)

    def test_matching_frame_in_publication_display_is_still_stale(self):
        events = [dict(event='interactive_phase', point='moves_request', t=100),
                  dict(event='interactive_phase', point='moves_published', t=200,
                       display=3, view=2, moves_page=0)]
        for t, display in ((201, 3), (300, 4)):
            events.append(dict(event='interactive_frame', t=t, display=display, view=2,
                moves_page=0, moves_state=0, transition=0, upper=11, panel=22))
        self.assertEqual(timing(events, 0, 2, 0)['complete_visible_t'], 300)

    def test_operation_groups_include_initial_tab_activations(self):
        cases = operations(dict(info_pages=2, moves_pages=2))
        self.assertEqual({operation_group(o) for o in cases},
            {'Desc page/wrap', 'Info page/wrap', 'Mov page/wrap',
             'Desc -> Info', 'Desc -> Mov', 'Info -> Desc',
             'Info -> Mov', 'Mov -> Desc', 'Mov -> Info'})

    def test_summary_takes_median_of_paired_deltas(self):
        rows = []
        for i, (a, b) in enumerate(((1, 10), (20, 2), (30, 31))):
            rows.append(dict(species='a', operation=str(i), request_to_displayed=dict(
                selected=dict(ms=a), registration=dict(ms=b), delta_ms=b - a)))
        summary = metric_stats(rows, 'request_to_displayed')
        self.assertEqual(summary['delta']['median_ms'], 1)
        self.assertEqual(summary['delta']['maximum_ms'], 9)
        self.assertEqual(summary['maximum_delta_case']['operation'], '0')
        self.assertAlmostEqual(summary['delta']['maximum_display_frames'], 9 * HZ / 1000 / FRAME)

    def test_wrong_pixels_cannot_pass_from_idle_flags(self):
        frame = dict(event='interactive_frame', t=FRAME, display=1, view=0, desc=0,
                     desc_state=0, transition=0, upper=1, panel=2)
        result = timing([frame], 0, 0, 0, dict(upper=1, panel=3))
        self.assertFalse(result['pixel_parity'])
        self.assertIsNone(result['request_to_displayed'])

    def test_fnv_matches_native_byte_hash(self):
        self.assertEqual(fnv(b''), 2166136261)
        self.assertEqual(fnv(b'hello'), 0x4f9f2cab)

    def test_coverage_uses_actual_page_counts(self):
        row = dict(base='a', info_pages=1, moves_pages=2)
        result = coverage_plan([row])
        self.assertEqual(result['info_pages'], 1)
        self.assertEqual(result['moves_pages'], 2)
        self.assertEqual(result['committed_B_End_exits'], 10)
        self.assertEqual(result['input_stress_cases'], 32)


if __name__ == '__main__':
    unittest.main()
