"""Source-boundary safety checks for private cleanup measurements."""
import unittest

from tools.dex_timing.dex_post_entry_cleanup import edit


class CleanupBoundaryTests(unittest.TestCase):
    def test_adapter_removes_fallback_through_the_label_not_the_branch_operand(self):
        source = ('NewDexEntry_VisualLayout::\n\tldh a, [hCGB]\n\tand a\n\tjr nz, .cgb\n'
                  '\tld b, SCGB_POKEDEX\n\tcall GetSGBLayout\n\tret\n.cgb\n'
                  '\tfarcall CGB_PokedexBuildSelectedMonLayout\n\tret\n')
        key = 'engine/pokedex/new_entry_visual.asm'
        result = edit({key: source}, [], adapter=True)[key]
        self.assertNotIn('hCGB', result)
        self.assertNotIn('GetSGBLayout', result)
        self.assertIn('CGB_PokedexBuildSelectedMonLayout', result)

    def test_registration_shell_is_removed_before_its_options_boundary(self):
        key = 'engine/pokedex/pokedex.asm'
        source = ('Pokedex_DrawDexEntryScreenBG:\n\tdb 1\nPokedex_DrawOptionScreenBG:\n'
                  '\tdb 2\nPokedex_DrawSearchScreenBG:\n\tret\n')
        result = edit({key: source}, ['old-options'], shell=True)[key]
        self.assertEqual(result, 'Pokedex_DrawSearchScreenBG:\n\tret\n')

    def test_wrap_stub_removal_survives_removing_the_old_refill_caller_first(self):
        key = 'engine/pokedex/pokedex_3.asm'
        source = ('Pokedex_FinalizeWrappedGridCache:\n\tret\n'
                  'PokedexPerf_LegacyFinalizeWrappedGridCache:\n\tdb 1\nLoadQuestionMarkPic:\n\tret\n')
        other = 'engine/pokedex/pokedex_animation.asm'
        result = edit({key: source, other: '\tfarcall Pokedex_FinalizeWrappedGridCache\n'},
                      ['old-grid-refill'], wrap=True)
        self.assertEqual(result[key], 'LoadQuestionMarkPic:\n\tret\n')
        self.assertEqual(result[other], '')


if __name__ == '__main__':
    unittest.main()
