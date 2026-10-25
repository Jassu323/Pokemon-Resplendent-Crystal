"""Check the production Moves Dex link without private rollback assumptions."""
from pathlib import Path
import unittest

from dex_timing.assets import Repository, offset
from pokedex_moves_mode_assets import compile_tables as compile_moves, TYPES
from pokedex_sort_assets import compile_tables as compile_species


ROOT = Path(__file__).resolve().parents[1]


class ProductionMovesDexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        cls.moves_asm, cls.moves = compile_moves(ROOT)
        cls.species_asm, cls.species = compile_species(ROOT)

    def linked(self, label, size):
        start = offset(self.repo.symbols[label])
        return self.repo.rom[start:start + size]

    def test_generated_inputs_match_current_source(self):
        for path, expected in (
            ('build/dex-moves-mode-assets/tables.asm', self.moves_asm),
            ('build/dex-sort-assets/tables.asm', self.species_asm),
        ):
            self.assertEqual((ROOT / path).read_text(), expected)

    def test_both_move_orders_are_complete_and_linked(self):
        expected_ids = list(range(1, len(self.moves['moves']) + 1))
        for label, order in zip(('PokedexMovesModeTypeOrder', 'PokedexMovesModeNameOrder'),
                                self.moves['orders']):
            self.assertEqual(sorted(order), expected_ids)
            expected = b''.join(i.to_bytes(2, 'little') for i in order + [0])
            self.assertEqual(self.linked(label, len(expected)), expected)
        self.assertEqual(list(TYPES), sorted(TYPES))
        self.assertEqual((TYPES[0], TYPES[-1]), ('BUG', 'WATER'))

    def test_species_orders_and_seen_records_are_linked(self):
        authored = self.species['orders']['NewPokedexOrder']
        ids = dict(zip(self.species['national'], range(1, len(authored) + 1)))
        for label, order in self.species['orders'].items():
            words = b''.join(ids[name].to_bytes(2, 'little') for name in order)
            records = b''.join(ids[name].to_bytes(2, 'little') +
                               bytes(((ids[name] - 1) // 8, 1 << ((ids[name] - 1) % 8)))
                               for name in order)
            self.assertEqual(self.linked(label, len(words)), words)
            self.assertEqual(self.linked(label + 'Records', len(records)), records)

    def test_end_cursor_matches_the_native_ten_sprite_box(self):
        native = self.linked('SpriteAnimOAMData.OAMData_TextEntryCursorBig', 41)
        self.assertEqual(native[0], 10)
        self.assertEqual(self.linked('PokedexMovesSearch_DrawText.CommandCursor', 40),
                         native[1:])
        source = (ROOT / 'engine/pokedex/pokedex_moves_mode.asm').read_text()
        self.assertIn('hlcoord 15, 15\n    ld de, .End', source)

    def test_save_extension_preserves_checksum_boundaries(self):
        for prefix in ('s', 'sBackup'):
            start = self.repo.symbols[prefix + 'MoveDiscovery']
            self.assertEqual(start, self.repo.symbols[prefix + 'SaveDataEnd'])
            checksum = self.repo.symbols[prefix + 'Checksum']
            self.assertEqual(checksum, (start[0], start[1] + 136))
        seen = self.repo.symbols['wMoveDiscoverySeen']
        self.assertEqual(seen, (2, 0xd500))
        self.assertEqual(self.repo.symbols['wMoveDiscoveryEnd'], (2, seen[1] + 66))

    def test_production_owners_and_gift_hook_are_included(self):
        source = (ROOT / 'main.asm').read_text()
        for name in ('move_discovery', 'move_acquisition', 'move_battle_use',
                     'move_pokedex_gift', 'pokedex_moves_mode', 'pokedex_popover',
                     'pokedex_search', 'pokedex_search_results'):
            self.assertIn(f'INCLUDE "engine/pokedex/{name}.asm"', source)
        self.assertIn('callasm MoveDiscovery_PokedexGift',
                      (ROOT / 'maps/MrPokemonsHouse.asm').read_text())

    def test_normal_save_and_new_game_include_discovery_lifecycle(self):
        save = (ROOT / 'engine/menus/save.asm').read_text()
        for hook in ('Invalidate', 'SavePrimary', 'SaveBackup', 'Clear',
                     'LoadPrimary', 'LoadBackup'):
            self.assertIn('farcall MoveDiscovery_' + hook, save)
        new_game = (ROOT / 'engine/menus/intro_menu.asm').read_text()
        self.assertIn('ld hl, wMoveDiscoverySeen', new_game)
        self.assertIn('ld bc, wMoveDiscoveryEnd - wMoveDiscoverySeen', new_game)

    def test_clean_build_inputs_do_not_require_a_private_seen_fixture(self):
        makefile = (ROOT / 'Makefile').read_text()
        self.assertIn('build/dex-sort-assets/tables.asm: $(sort_asset_inputs)', makefile)
        self.assertIn('build/dex-moves-mode-assets/tables.asm: $(moves_mode_asset_inputs)', makefile)
        source = (ROOT / 'engine/pokedex/pokedex_moves_mode.asm').read_text()
        self.assertNotIn('dex-moves-mode-assets/seen.asm', source)
        for name in ('pokedex_moves_scroll_bar_and_borders',
                     'pokedex_moves_search_left_border', 'pokedex_search_results_footer'):
            self.assertTrue((ROOT / 'gfx/pokedex' / (name + '.png')).is_file())


if __name__ == '__main__':
    unittest.main()
