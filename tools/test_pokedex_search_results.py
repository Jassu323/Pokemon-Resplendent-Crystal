import os
from pathlib import Path
import unittest

from dex_timing.assets import Repository, offset
from dex_timing.cold_listing import ROOT
from dex_timing.search_results_patch import ALPHABETICAL_TYPES


class SearchResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / os.environ.get('DEX_SEARCH_BUILD', 'build/dex-search-results-20261006d')
        cls.repo = Repository(ROOT, cls.output / 'pokecrystal-dex-search.gbc',
                              cls.output / 'pokecrystal-dex-search.sym')

    def test_alphabetical_selector_preserves_gameplay_type_values(self):
        types = {'NORMAL': 0, 'FIGHTING': 1, 'FLYING': 2, 'POISON': 3, 'GROUND': 4,
                 'ROCK': 5, 'BUG': 7, 'DARK': 8, 'STEEL': 9, 'FIRE': 20, 'WATER': 21,
                 'GRASS': 22, 'ELECTRIC': 23, 'PSYCHIC_TYPE': 24, 'ICE': 25,
                 'DRAGON': 26, 'GHOST': 27, 'FAIRY': 28}
        labels = [name.removesuffix('_TYPE') for name in ALPHABETICAL_TYPES]
        self.assertEqual(labels, sorted(labels))
        start = offset(self.repo.symbols['PokedexTypeSearchConversionTable'])
        self.assertEqual(self.repo.rom[start:start + 18], bytes(types[name] for name in ALPHABETICAL_TYPES))

    def test_fallback_strings_match_the_alphabetical_badges(self):
        start = offset(self.repo.symbols['PokedexTypeSearchStrings'])
        for index, name in enumerate(ALPHABETICAL_TYPES, 1):
            text = self.repo.rom[start + index * 9:start + index * 9 + 8]
            letters = ''.join(chr(value - 0x80 + ord('A')) for value in text if value != 0x7f)
            self.assertEqual(letters, name.removesuffix('_TYPE'))

    def test_default_bug_and_none_start_at_the_beginning(self):
        self.assertEqual(ALPHABETICAL_TYPES[0], 'BUG')
        source = (self.output / 'candidate/engine/pokedex/pokedex.asm').read_text()
        self.assertIn('ld a, 1 ; Bug starts the alphabetical selector', source)
        self.assertIn('xor a\n\tld [wDexSearchMonType2], a', source)

    def test_search_header_uses_orange_tiles_before_drawing_the_title(self):
        source = (self.output / 'candidate/engine/pokedex/pokedex.asm').read_text()
        start = source.index('Pokedex_DrawSearchScreenBG:')
        end = source.index('Pokedex_DrawSearchResultsScreenBG:', start)
        header = source[start:end]
        self.assertIn('.Header\n\thlcoord 0, 0\n\tld a, $31\n'
                      '\tld bc, 2 * SCREEN_WIDTH\n\tcall ByteFill', header)
        self.assertLess(header.index('.Header'), header.index('ld de, .Title'))

    def test_results_maps_and_search_records_have_disjoint_lifetimes_and_bounds(self):
        symbols = self.repo.symbols
        self.assertEqual(symbols['wPokedexOwnerTilemapBuffer'], (3, 0xd000))
        self.assertEqual(symbols['wPokedexOwnerAttrmapBuffer'], (3, 0xd240))
        self.assertEqual(0xd240 + 32 * 18, 0xd480)
        self.assertLessEqual(0xd480 + 373 * 3, 0xdc00)
        self.assertEqual(symbols['wPokedexInfoGFX'][0], 3)

    def test_results_uses_base_only_loader_and_not_vanilla_dictionary(self):
        source = (self.output / 'candidate/engine/pokedex/pokedex_search_results.asm').read_text()
        self.assertIn('farcall Pokedex_PrepareSelectedMonTiles', source)
        self.assertIn('farcall Pokedex_PrepareAndCommitSelectedMonGFX', source)
        self.assertNotIn('Pokedex_PrintListing', source)
        self.assertNotIn('GetMonFrontpic', source)

    def test_slowpoke_animation_source_is_unchanged(self):
        path = Path('engine/pokedex/pokedex_2.asm')
        self.assertEqual((self.output / 'candidate' / path).read_bytes(), (ROOT / path).read_bytes())

    def test_border_palette_is_not_replaced_by_the_orange_gap_palette(self):
        source = (self.output / 'candidate/engine/gfx/cgb_layouts.asm').read_text()
        helpers = source[source.index('CGB_PokedexResultsAttributes:'):]
        attributes = helpers[:helpers.index('CGB_PokedexResultsStagePalettes:')]
        self.assertNotIn('ld a, 2', attributes)
        self.assertNotIn('.OutsidePalette', helpers)
        source = (self.output / 'candidate/engine/pokedex/pokedex.asm').read_text()
        gap = source[source.index('PokedexResults_DrawBG:'):]
        self.assertIn('hlcoord 0, 9\n    lb bc, 2, 8\n    ld a, $31', gap)


if __name__ == '__main__':
    unittest.main()
