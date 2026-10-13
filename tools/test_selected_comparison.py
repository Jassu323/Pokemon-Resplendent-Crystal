import unittest

from pokedex_info_assets import Compiler
from dex_timing.selected_comparison import page_signature, same_transition


class SelectedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = Compiler().compile()
        cls.new = Compiler().compile(ancestors=True)

    def row(self, name, page, action='cycle'):
        return dict(species=name, page=page, action=action)

    def test_bayleef_forward_page_is_the_same_but_wrap_target_is_not(self):
        self.assertEqual(page_signature(self.old, 'bayleef', 1),
                         page_signature(self.new, 'bayleef', 1))
        self.assertEqual(page_signature(self.new, 'bayleef', 2)[0], 'Evolves from')
        self.assertTrue(same_transition(self.row('bayleef', 0), self.old, self.new))
        self.assertFalse(same_transition(self.row('bayleef', 1), self.old, self.new))

    def test_meganium_noop_must_not_be_paired_with_a_new_page_render(self):
        self.assertEqual(page_signature(self.old, 'meganium', 0), ('Stats',))
        self.assertEqual(page_signature(self.new, 'meganium', 1)[0], 'Evolves from')
        self.assertFalse(same_transition(self.row('meganium', 0), self.old, self.new))

    def test_existing_listing_and_area_returns_remain_pairable(self):
        for action in ('listing', 'info-area-return'):
            self.assertTrue(same_transition(self.row('bayleef', 1, action), self.old, self.new))
            self.assertTrue(same_transition(self.row('meganium', 0, action), self.old, self.new))
            self.assertFalse(same_transition(self.row('bayleef', 2, action), self.old, self.new))


if __name__ == '__main__':
    unittest.main()
