"""Current private-link bookmark ownership, allocation and result contracts."""
import json
from pathlib import Path
import unittest

from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT
from dex_timing.pokemon_position import expected

BASE = ROOT / 'build/dex-position-memory-20261014'


class DexPositionTests(unittest.TestCase):
    def report(self, name):
        return json.loads((BASE / name).read_text())

    def test_qualified_link_and_resource_budget(self):
        data = self.report('position-memory-manifest.json')
        self.assertEqual(sha256((BASE / 'candidate/pokecrystal.gbc').read_bytes()), data['candidate_sha256'])
        self.assertEqual(data['pokemon_delta']['ROMX'], 275)
        self.assertEqual(data['delta']['ROMX'], 518)
        self.assertTrue(all(value == 0 for key, value in data['delta'].items() if key != 'ROMX'))
        integration = None
        if data['production_integrated']:
            integration = json.loads(Path(data['production_integration_receipt']).read_text())
            self.assertEqual(integration['status'], 'Passed: approved prototype integrated into production')
            self.assertTrue(integration['exact_approved_match'])
            self.assertEqual(sha256((ROOT / 'pokecrystal.gbc').read_bytes()), data['candidate_sha256'])
            for name, digest in integration['production_artifacts'].items():
                self.assertEqual(sha256(Path(name).read_bytes()), digest, name)
            for name, digest in integration['approved_source'].items():
                self.assertEqual(sha256((ROOT / name).read_bytes()), digest, name)
        for name, digest in data['protected'].items():
            path = Path(name)
            if integration and name in integration['before_artifacts']:
                self.assertEqual(integration['before_artifacts'][name], digest)
                path = Path(data['production_integration_receipt']).parent / 'before' / path.name
            self.assertEqual(sha256(path.read_bytes()), digest, name)

    def test_eight_padding_bytes_and_no_moved_ram(self):
        before = read_symbols(BASE / 'rollback/pokecrystal.sym')
        after = read_symbols(BASE / 'candidate/pokecrystal.sym')
        for name, pair in before.items():
            if pair[1] >= 0xa000:
                self.assertEqual(after[name], pair, name)
        for name, address in (('wMovesDexBookmarkTag', 0xd9e4),
                              ('wPokemonDexBookmarkTag', 0xd9e8),
                              ('wPokemonDexBookmarkSpecies', 0xd9e9),
                              ('wPokemonDexBookmarkCell', 0xd9eb),
                              ('wPokecenter2FSceneID', 0xd9f0)):
            self.assertEqual(after[name], (1, address))

    def test_capture_only_at_ordinary_exit_before_shared_exit(self):
        source = (BASE / 'candidate/engine/pokedex/pokedex.asm').read_text()
        self.assertEqual(source.count('call Pokedex_RememberListingPosition'), 1)
        self.assertIn('.b\n\tcall Pokedex_RememberListingPosition\n\tcall Pokedex_StopGridIconAnimation', source)
        init = source.split('InitPokedex:', 1)[1].split('Pokedex_ClearLockedIDs:', 1)[0]
        self.assertLess(init.index('Pokedex_InitListingPresentation'), init.index('Pokedex_RestoreListingPosition'))
        self.assertLess(init.index('Pokedex_RestoreListingPosition'), init.index('Pokedex_EnsureGridCache'))

    def test_legacy_restorer_replaced_not_kept_as_dead_code(self):
        symbols = read_symbols(BASE / 'candidate/pokecrystal.sym')
        self.assertNotIn('Pokedex_InitCursorPosition', symbols)
        source = (BASE / 'candidate/engine/pokedex/pokedex_position.asm').read_text()
        self.assertNotIn('Pokedex_GetSelectedMon', source)
        self.assertNotIn('GetPokemonIDFromIndex', source)
        self.assertNotIn('wPrevDexEntry', source)

    def test_continue_discards_both_bookmarks_not_preferences(self):
        source = (BASE / 'candidate/engine/menus/intro_menu.asm').read_text()
        body = source.split('.Check2Pass:', 1)[1].split('ld a, $8', 1)[0]
        self.assertIn('ld hl, wMovesDexBookmarkTag', body)
        self.assertEqual(body.count('ld [hli], a'), 7)
        self.assertEqual(body.count('ld [hl], a'), 1)
        self.assertNotIn('wLastDexMode', body)
        self.assertNotIn('wLastDexPresentation', body)
        self.assertNotIn('wLastMovesDexSort', body)

    def test_native_full_viewports_and_changed_orders(self):
        data = self.report('pokemon-position-tests/helpers.json')
        self.assertEqual(data['counts']['legal_round_trips'], 11022)
        self.assertEqual(data['counts']['changed_order_and_insertions'], 30)
        self.assertEqual(data['cases'], 16176)
        for key in ('no_sram_write', 'registers_and_banks_preserved', 'transient_ids_unchanged'):
            self.assertTrue(data[key], key)
        self.assertFalse(data['issues'])

    def test_normal_inputs_cover_each_cell_and_layout(self):
        data = self.report('pokemon-position-tests/ui.json')
        self.assertEqual({(r['style'], r['order'], r['cell']) for r in data['rows']},
            {(style, order, cell) for style in range(2) for order in range(3)
             for cell in range(7 if style else 9)})
        self.assertFalse(data['issues'])

    def test_search_moves_save_reset_and_recovery(self):
        data = self.report('pokemon-position-tests/integration.json')
        self.assertEqual(data['cases'], 6)
        self.assertTrue(all(all(row[key] for key in ('selected_paging', 'search_isolated',
            'moves_independent', 'save_retained', 'soft_reset_first', 'cold_continue_first'))
            for row in data['rows']))
        lifecycle = self.report('pokemon-position-tests/lifecycle.json')
        self.assertEqual(lifecycle['cases'], 13)
        self.assertFalse(lifecycle['issues'])
        self.assertEqual(self.report('pokemon-position-tests/sparse.json')['cases'], 6)

    def test_geometry_preserves_identity_and_legal_aligned_viewports(self):
        for size in range(1, 374):
            for ordinal in {0, size // 2, size - 1}:
                for style in (0, 1):
                    for cell in range(7 if style else 9):
                        result = expected(style, size, ordinal, cell)
                        scroll = int.from_bytes(result[:2], 'little')
                        self.assertEqual(scroll + result[2], ordinal)
                        self.assertLess(result[2], 7 if style else 9)
                        self.assertLess(ordinal, size)
                        if not style:
                            self.assertEqual(scroll % 3, 0)

    def test_audio_uses_exact_hardware_timing_not_global_entry_median(self):
        data = self.report('lifecycle/audio-hardware-proof.json')
        self.assertEqual(data['cases'], 12)
        self.assertEqual(data['mismatches'], 0)
        self.assertTrue(all(row['identical_registers_and_relative_hardware_timing'] and row['qualified'] for row in data['rows']))

    def test_warm_timing_includes_all_targets_orders_and_phases(self):
        data = self.report('pokemon-position-tests/warm-timing.json')
        self.assertEqual(data['cases'], 144)
        self.assertEqual(len(data['pairs']), 72)
        self.assertEqual({(r['style'], r['order'], r['target'], r['phase']) for r in data['pairs']},
            {(style, order, target, phase) for style in range(2) for order in range(3)
             for target in (0, 186, 372) for phase in range(4)})
        self.assertTrue(all(row['after'] == row['before'] for row in data['rows'] if row['variant'] == 'integrated'))
        self.assertFalse(data['issues'])


if __name__ == '__main__':
    unittest.main()
