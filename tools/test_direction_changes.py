"""Negative controls for the read-only Dex input investigation."""
import unittest

from dex_timing.direction_changes import (
    ORDERS, actions, old_horizontal_on_new_vertical, old_vertical_on_new_horizontal, summarize,
)


class DirectionChangeTests(unittest.TestCase):
    def event(self, phase='grid_up', pressed=0x10, last=0x50, **fields):
        return dict(event='phase', phase=phase, pressed=pressed, last=last, **fields)

    def test_matrix_contains_all_eight_ordered_axis_changes(self):
        self.assertEqual(len(ORDERS), 8)
        self.assertEqual(len(set(ORDERS)), 8)
        self.assertTrue(all(a in ('up', 'down') for a, _ in ORDERS[:4]))
        for a, b in ORDERS:
            self.assertIn((b, a), ORDERS)

    def test_new_horizontal_can_expose_held_vertical_in_both_owners(self):
        for owner, phase in (('listing', 'grid_up'), ('selected', 'page')):
            event = self.event(phase=phase)
            self.assertEqual(old_vertical_on_new_horizontal([event], owner), [event])

    def test_real_repeat_is_not_misclassified_as_the_axis_bug(self):
        self.assertEqual(old_vertical_on_new_horizontal(
            [self.event(pressed=0, last=0x40)], 'listing'), [])

    def test_simultaneous_new_diagonal_is_not_an_old_direction(self):
        self.assertEqual(old_vertical_on_new_horizontal(
            [self.event(pressed=0x50)], 'listing'), [])

    def test_correct_horizontal_action_and_pin_changes_are_not_wrong_moves(self):
        for event in (self.event(phase='grid_right'), dict(self.event(), event='input')):
            self.assertEqual(old_vertical_on_new_horizontal([event], 'listing'), [])

    def test_footer_movement_is_not_species_paging(self):
        event = self.event(phase='footer_changed')
        self.assertEqual(actions([event], 'selected'), [event])
        self.assertEqual(old_vertical_on_new_horizontal([event], 'selected'), [])

    def test_new_vertical_must_not_repeat_the_held_footer_direction(self):
        event = self.event(phase='footer_changed', pressed=0x40)
        self.assertEqual(old_horizontal_on_new_vertical([event]), [event])
        for pressed in (0, 0x10, 0x50):
            self.assertEqual(old_horizontal_on_new_vertical(
                [self.event(phase='footer_changed', pressed=pressed)]), [])

    def test_actions_exclude_mirrors_and_cross_owner_handlers(self):
        trace = [self.event(phase='mirror'), self.event(), self.event(phase='page')]
        self.assertEqual(actions(trace, 'listing'), [trace[1]])
        self.assertEqual(actions(trace, 'selected'), [trace[2]])

    def test_summary_keeps_owner_release_and_order_distinct(self):
        rows = [dict(owner='listing', first='up', mode='overlap', wrong_vertical_edges=[{}],
                     wrong_horizontal_edges=[]),
                dict(owner='listing', first='up', mode='released', wrong_vertical_edges=[],
                     wrong_horizontal_edges=[]),
                dict(owner='selected', first='left', mode='overlap', wrong_vertical_edges=[],
                     wrong_horizontal_edges=[])]
        result = summarize(rows)
        self.assertEqual(result['listing']['overlap']['wrong_vertical_first_cases'], 1)
        self.assertEqual(result['listing']['released']['wrong_vertical_first_cases'], 0)
        self.assertEqual(result['selected']['overlap']['horizontal_first_cases'], 1)
        self.assertEqual(result['selected']['released']['cases'], 0)


if __name__ == '__main__':
    unittest.main()
