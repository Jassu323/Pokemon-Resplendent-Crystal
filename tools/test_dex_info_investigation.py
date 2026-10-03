"""Independent evidence checks for the Info investigation, not a fix oracle."""
from types import SimpleNamespace
import unittest

from dex_timing.assets import Repository
from dex_timing.cold_listing import ROOT
from dex_timing.info_investigation import (
    graph_audit, linked_evolutions, replaced_visible_tiles, visible_atlas_b_cells,
)


class BorrowedAtlasTests(unittest.TestCase):
    def vram(self, tile=3, attr=8):
        vram = bytearray(0x4000)
        vram[0x1800 + 10 * 32 + 1] = tile
        vram[0x3800 + 10 * 32 + 1] = attr
        return vram

    def test_visible_bank1_frame0_reference_is_borrowed(self):
        self.assertEqual(visible_atlas_b_cells(self.vram()), [(10, 1, 3)])
        self.assertEqual(visible_atlas_b_cells(self.vram(attr=0)), [])
        self.assertEqual(visible_atlas_b_cells(self.vram(tile=40)), [])

    def test_tile_replacement_without_map_replacement_is_exposed(self):
        before, after = self.vram(), self.vram()
        after[0x3000 + 3 * 16] = 1
        self.assertEqual(replaced_visible_tiles(before, after), [(10, 1, 3)])

    def test_masked_map_does_not_count_as_exposed_replacement(self):
        before, after = self.vram(), self.vram(attr=0)
        after[0x3000 + 3 * 16] = 1
        self.assertEqual(replaced_visible_tiles(before, after), [])

    def test_unrelated_atlas_writes_are_ignored(self):
        before, after = self.vram(), self.vram()
        after[0x3000 + 4 * 16] = 1
        self.assertEqual(replaced_visible_tiles(before, after), [])


class IndependentGraphTests(unittest.TestCase):
    def test_invalid_runtime_pointer_is_not_a_missing_evolution(self):
        repo = SimpleNamespace(rom=bytes(0x8000), symbols={'EvosAttacksPointers1': (1, 0x4000)})
        with self.assertRaisesRegex(ValueError, 'Invalid evolution pointer'):
            linked_evolutions(repo, ['A'])

    def test_all_linked_future_lists_match_gameplay_tables(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        report = graph_audit(repo)
        self.assertEqual(report['species'], 373)
        self.assertEqual(report['source_linked_mismatches'], [])
        self.assertEqual(report['linked_info_future_mismatches'], [])


if __name__ == '__main__':
    unittest.main()
