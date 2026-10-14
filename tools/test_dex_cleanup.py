"""Linked cleanup boundaries and preserved graphics, independent of UI fixtures."""
import os
from pathlib import Path
import unittest

from dex_timing.assets import Repository, decompress, offset
from dex_timing.cold_listing import ROOT


class DexCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ.get('DEX_CLEANUP_SOURCE', ROOT / 'build/dex-cleanup-20261014/candidate'))
        cls.repo = Repository(cls.root, cls.root / 'pokecrystal.gbc', cls.root / 'pokecrystal.sym')

    def test_retired_labels_are_absent_and_live_owners_remain(self):
        for label in ('MoveDiscovery_CheckIndex', 'MoveDiscovery_MarkMoveList', 'LoadSGBPokedexGFX',
                      'LoadSGBPokedexGFX2', 'SGBPokedexGFX_LZ', 'DrawDexEntryScreenRightEdge',
                      'PokedexInfoPageGFX', 'Pokedex_DrawDexEntryScreenBG', 'Pokedex_DrawOptionScreenBG',
                      'FindNest', 'EZChatSlowpokeLZ', 'PasswordSlowpokeLZ', 'PokedexPerf_CanBatch'):
            self.assertNotIn(label, self.repo.symbols)
        for label in ('MoveDiscovery_BitAddress', 'MoveDiscovery_MarkIndex', 'PokedexMovesMode_IsSeen',
                      'PokedexMovesMode_SnapshotSeen', 'PokedexArea_RoamerNests.RoamMon1',
                      'PokedexArea_RoamerNests.RoamMon2', 'Pokedex_FillColumn2', '_NewPokedexEntry',
                      'Pokedex_DisplayDescriptionEntry', 'NewDexEntry_RedFooterPalette',
                      'BattleTowerRoomMenu', 'BattleTowerAction', 'GiveOddEgg'):
            self.assertIn(label, self.repo.symbols)
        self.assertEqual(self.repo.rom[0x143], 0xc0)

    def test_archived_sheets_and_all_live_slowpoke_frames_are_preserved(self):
        archive = self.root / 'gfx/archived/pokedex'
        original = (archive / 'slowpoke.2bpp').read_bytes()
        retained = decompress(self.repo.rom, offset(self.repo.symbols['PokedexSlowpokeLZ']), 880).output
        self.assertEqual(len(original), 880)
        self.assertEqual(retained, original[:768])
        for frame in range(5):
            for tile in (0, 1, 2, 16, 17, 18, 32, 33, 34):
                at = (tile + frame * 3) * 16
                self.assertEqual(retained[at:at + 16], original[at:at + 16])
        self.assertEqual(retained[15 * 16:16 * 16], original[15 * 16:16 * 16])
        self.assertEqual((archive / 'unused_info_page_numbers.2bpp').read_bytes(),
                         (self.root / 'gfx/pokedex/pokedex_page_numbers.2bpp').read_bytes()[96:160])
        for name in ('slowpoke.png', 'pokedex_sgb.png', 'pokedex_sgb.2bpp', 'pokedex_sgb.2bpp.lz',
                     'info_page_numbers_source.png'):
            self.assertTrue((archive / name).is_file(), name)

    def test_retired_mobile_entries_are_safe_returns_without_reindexing_specials(self):
        for name in ('Function11c1ab', 'Function11765d', 'Function1719c8'):
            self.assertEqual(self.repo.rom[offset(self.repo.symbols[name])], 0xc9)
        table = offset(self.repo.symbols['Function11c1abSpecial'])
        bank, pc = self.repo.symbols['Function11c1ab']
        self.assertEqual(self.repo.rom[table:table + 3], bytes((bank, pc & 255, pc >> 8)))


if __name__ == '__main__':
    unittest.main()
