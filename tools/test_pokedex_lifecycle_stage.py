"""Linked safeguards for the Dex-only Stage entry and committed-white exit."""
from pathlib import Path
import unittest

from dex_timing.assets import Repository, offset

ROOT = Path(__file__).resolve().parents[1]


class StageLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'pokecrystal.gbc').exists():
            raise unittest.SkipTest('Build the production ROM first')
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')

    def call(self, label):
        pc = self.repo.symbols[label][1]
        return bytes((0xcd, pc & 255, pc >> 8))

    def body(self, first, last):
        return self.repo.rom[offset(self.repo.symbols[first]):offset(self.repo.symbols[last])]

    def test_init_prepares_with_lcd_off(self):
        start = offset(self.repo.symbols['InitPokedex'])
        expected = b''.join(self.call(label) for label in
                            ('ClearPalettes', 'ClearSprites', 'Pokedex_LoadGFX', 'ClearTilemap'))
        self.assertEqual(self.repo.rom[start:start + len(expected)], expected)

    def test_exit_sound_finishes_before_white_is_committed(self):
        sequence = b''.join(self.call(label) for label in
                             ('PlaySFX', 'WaitSFX', 'ClearSprites', 'ClearPalettes', 'DelayFrame'))
        self.assertIn(sequence, self.body('Pokedex.exit', 'InitPokedex'))

    def test_only_dex_uses_local_close(self):
        body = self.body('StartMenu_Pokedex', 'StartMenu_Pokegear')
        self.assertIn(self.call('Pokedex_CloseSubmenu'), body)
        self.assertNotIn(self.call('CloseSubmenu'), body)
        self.assertIn(self.call('CloseSubmenu'), self.body('StartMenu_Pokegear', 'Pokedex_CloseSubmenu'))

    def test_palette_guard_survives_map_copy_and_display_wait(self):
        pal = self.repo.symbols['hCGBPalUpdate'][1] & 255
        sequence = (bytes((0xf0, pal, 0xf5, 0xaf, 0xe0, pal)) +
                    self.call('CGBOnly_CopyTilemapAtOnce') + self.call('DelayFrame') +
                    bytes((0xf1, 0xe0, pal)))
        self.assertIn(sequence, self.body('Pokedex_CloseSubmenu', 'StartMenu_Pack'))

    def test_new_helpers_live_in_switchable_rom(self):
        for label in ('Pokedex_CloseSubmenu', 'Pokedex_InitListingRightEdge'):
            bank, pc = self.repo.symbols[label]
            self.assertGreater(bank, 0)
            self.assertTrue(0x4000 <= pc < 0x8000)


if __name__ == '__main__':
    unittest.main()
