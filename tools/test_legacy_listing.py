"""Small linked Legacy contracts; native display/input suites remain authoritative."""
import os
from pathlib import Path
import unittest

from PIL import Image

from dex_timing.assets import Repository, offset, decompress
from dex_timing.costs import machine

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('DEX_LEGACY_BUILD', ROOT / 'build/dex-legacy-borders-prototype'))


@unittest.skipUnless((BUILD / 'pokecrystal-dex-legacy.gbc').exists(), 'private Legacy link required')
class LegacyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, BUILD / 'pokecrystal-dex-legacy.gbc',
                              BUILD / 'pokecrystal-dex-legacy.sym')

    def test_presentation_is_separate_from_order_and_fits_saved_padding(self):
        symbols = self.repo.symbols
        self.assertEqual(symbols['wLastDexPresentation'][1], symbols['wLastDexMode'][1] + 1)
        self.assertEqual(symbols['wWhichRegisteredItem'][1], symbols['wLastDexPresentation'][1] + 1)
        self.assertNotEqual(symbols['wPokedexListingPresentation'], symbols['wCurDexMode'])
        parent = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for name in ('wWhichRegisteredItem', 'wPlayerDataEnd', 'wPokemonDataEnd',
                     'wPokedexAnimSchedulerControl', 'wPokedexWRAM0ScratchEnd'):
            self.assertEqual(symbols[name], parent.symbols[name])

    def test_legacy_and_modern_start_with_their_own_navigation_height(self):
        for presentation, height in ((0, 9), (1, 7)):
            cpu = machine(self.repo)
            cpu.field('wPokedexListingPresentation', presentation)
            cpu.field('wPrevDexEntry', 0, 2)
            cpu.field('wDexListingEnd', 373, 2)
            cpu.run('Pokedex_InitListingPresentation')
            self.assertEqual(cpu.read(self.repo.symbols['wDexListingHeight'][1]), height)

    def test_row_lookup_uses_full_16_bit_indices_and_restores_bank(self):
        order = b''.join((i + 1).to_bytes(2, 'little') for i in range(373))
        for scroll in (0, 1, 249, 254, 255, 256, 366, 372):
            for row in range(7):
                cpu = machine(self.repo)
                bank, address = self.repo.symbols['wPokedexOrder']
                cpu.ram[0xff70] = bank
                cpu.block(address, order)
                cpu.ram[0xff70] = 7
                cpu.field('wDexListingScrollOffset', scroll, 2)
                cpu.field('wDexListingEnd', 373, 2)
                cpu.r[7] = row
                cpu.run('PokedexLegacy_GetRowSpecies')
                self.assertEqual(cpu.pair(1), scroll + row + 1 if scroll + row < 373 else 0)
                self.assertEqual(cpu.ram[0xff70], 7)

    def test_empty_and_short_rows_are_absent(self):
        for end in (0, 1, 3, 6):
            for row in range(end, 7):
                cpu = machine(self.repo)
                cpu.field('wDexListingEnd', end, 2)
                cpu.r[7] = row
                cpu.run('PokedexLegacy_GetRowSpecies')
                self.assertEqual(cpu.pair(1), 0)

    def test_legacy_wraps_both_boundaries_for_short_and_full_lists(self):
        for end in (0, 1, 2, 6, 7, 8, 255, 256, 373):
            for direction in ('up', 'down'):
                cpu = machine(self.repo)
                cpu.field('wDexListingHeight', 7)
                cpu.field('wDexListingEnd', end, 2)
                selected = max(0, end - 1) if direction == 'down' else 0
                scroll = max(0, end - 7) if direction == 'down' else 0
                cpu.field('wDexListingScrollOffset', scroll, 2)
                cpu.field('wDexListingCursor', selected - scroll)
                cpu.field('hJoyLast', 0x80 if direction == 'down' else 0x40)
                cpu.run('PokedexLegacy_HandleDPadInput')
                cursor = cpu.read(self.repo.symbols['wDexListingCursor'][1])
                at = self.repo.symbols['wDexListingScrollOffset'][1]
                actual_scroll = int.from_bytes(cpu.data(at, 2), 'little')
                target = max(0, end - 1) if direction == 'up' else 0
                self.assertEqual(actual_scroll + cursor, target)
                self.assertEqual(actual_scroll, max(0, end - 7) if direction == 'up' else 0)

    def test_shared_search_controller_stays_bounded(self):
        for direction, scroll, cursor in (('up', 0, 0), ('down', 369, 3)):
            cpu = machine(self.repo)
            cpu.field('wDexListingHeight', 4)
            cpu.field('wDexListingEnd', 373, 2)
            cpu.field('wDexListingScrollOffset', scroll, 2)
            cpu.field('wDexListingCursor', cursor)
            cpu.field('hJoyLast', 0x80 if direction == 'down' else 0x40)
            cpu.run('Pokedex_ListingHandleDPadInput')
            self.assertEqual(cpu.read(self.repo.symbols['wDexListingCursor'][1]), cursor)
            at = self.repo.symbols['wDexListingScrollOffset'][1]
            self.assertEqual(int.from_bytes(cpu.data(at, 2), 'little'), scroll)

    def test_consolidated_legacy_cells_are_linked_from_the_shared_sheet(self):
        path = ROOT / 'gfx/pokedex/pokedex.png'
        with Image.open(path) as image:
            self.assertEqual(image.size, (128, 40))
        bank, address = self.repo.symbols['PokedexLegacyGFX']
        self.assertEqual(bank, 0xba)
        binary = (BUILD / 'candidate/gfx/pokedex/pokedex.2bpp').read_bytes()[64 * 16:68 * 16]
        self.assertEqual(len(binary), 64)
        at = offset((bank, address))
        self.assertEqual(self.repo.rom[at:at + 64], binary)

    def test_core_ui_load_stops_before_the_description_page_graphics(self):
        expected = (BUILD / 'candidate/gfx/pokedex/pokedex.2bpp').read_bytes()[:64 * 16]
        actual = decompress(self.repo.rom, offset(self.repo.symbols['PokedexLZ']), 64 * 16).output
        self.assertEqual(len(actual), 64 * 16)
        self.assertEqual(actual, expected)

    def test_border_pixels_match_the_fixed_bg_window_split(self):
        colors = {(85, 85, 85): 'D', (170, 170, 170): 'R', (255, 255, 255): 'W'}
        expected = (
            ('DWRWDDDD', 'DWRWDDDD', 'WWRWDDDD', 'RRRWDDDD',
             'RRRWDDDD', 'WWRWDDDD', 'DWRWDDDD', 'DWRWDDDD'),
            ('RRRRRRRR',) * 5 + ('WWRWWWWW', 'DWRWDDDD', 'DWRWDDDD'),
            ('DWRWDDDD',) * 8,
        )
        with Image.open(ROOT / 'gfx/pokedex/pokedex.png') as image:
            image = image.convert('RGB')
            for tile, rows in enumerate(expected):
                actual = tuple(''.join(colors[image.getpixel((tile * 8 + x, 32 + y))]
                                       for x in range(8)) for y in range(8))
                self.assertEqual(actual, rows)


if __name__ == '__main__':
    unittest.main()
