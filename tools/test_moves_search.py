"""Published Moves search identity, artwork, memory and qualification contracts."""
import json
import os
from pathlib import Path
import unittest

from PIL import Image
from dex_timing.assets import read_symbols, sha256, offset
from dex_timing.cold_listing import ROOT
from dex_timing.moves_search import STEM, keyboard_neighbor


class MovesSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / os.environ.get('MOVES_SEARCH_BUILD', 'build/dex-moves-search-20261010')
        cls.manifest = json.loads((cls.output / 'moves-mode-manifest.json').read_text())
        cls.symbols = read_symbols(cls.output / f'{STEM}.sym')
        cls.rom = (cls.output / f'{STEM}.gbc').read_bytes()

    def test_current_base_and_production_are_protected(self):
        source = Path(self.manifest['search_rollback'])
        self.assertEqual(source.name, 'dex-moves-sort-memory-20261008')
        self.assertEqual(sha256((source / 'pokecrystal-dex-moves-sort-memory.gbc').read_bytes()),
                         'f64ab16071231f4d0830b09d92b89c5b5de405519e8bccbd2c181eb9e8c958e8')
        for path, expected in self.manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), expected, path)
        self.assertEqual(sha256(self.rom), self.manifest['rom_sha256'])
        if self.manifest.get('moves_search_keyboard'):
            previous = Path(self.manifest['keyboard_rollback'])
            self.assertEqual(previous.name, 'dex-moves-search-20261010')
            self.assertEqual(sha256((previous / f'{STEM}.gbc').read_bytes()),
                             '1dc9ce2f134fe4c3cf27970682fede4bab42676161bb591eee47100d11737f73')

    def test_no_save_layout_or_gameplay_discovery_changes(self):
        source = Path(self.manifest['source']) / 'candidate'
        candidate = self.output / 'candidate'
        changes = {p.relative_to(candidate).as_posix() for p in candidate.rglob('*.asm')
                   if p.read_bytes() != (source / p.relative_to(candidate)).read_bytes()}
        expected = {'engine/pokedex/pokedex_moves_mode.asm'} if self.manifest.get('moves_search_standard_end') else {
                    'engine/pokedex/pokedex_moves_mode.asm', 'engine/pokedex/pokedex_3.asm'} if self.manifest.get('moves_search_naming_animation') else {
                    'engine/pokedex/pokedex_moves_mode.asm'} if self.manifest.get('moves_search_form_polish') else {
                    'engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_search.asm',
                    'engine/pokedex/pokedex_moves_mode.asm'} if self.manifest.get('moves_search_visual_repairs') else {
                        'engine/pokedex/pokedex_moves_mode.asm'} if self.manifest.get('moves_search_keyboard') else {
            'engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_3.asm', 'engine/pokedex/pokedex_moves_mode.asm'}
        self.assertEqual(changes, expected)
        for name in ('ram/wram.asm', 'ram/sram.asm', 'ram/hram.asm'):
            self.assertEqual((source / name).read_bytes(), (candidate / name).read_bytes())
        for name, pair in read_symbols(source / 'pokecrystal.sym').items():
            if name.startswith(('w', 's', 'h')) and pair[1] >= 0xa000:
                self.assertEqual(pair, self.symbols[name], name)

    def test_supplied_artwork_uses_opaque_source_greys(self):
        for name, size in (('pokedex_moves_search_left_border', (8, 8)),
                           ('pokedex_search_results_footer', (64, 8))):
            path = ROOT / f'gfx/pokedex/{name}.png'
            with Image.open(path) as image:
                self.assertEqual(image.size, size)
                self.assertEqual(set(image.convert('RGBA').get_flattened_data()),
                                 {(255, 255, 255, 255), (170, 170, 170, 255), (85, 85, 85, 255)})
            self.assertEqual(sha256(path.read_bytes()), self.manifest['search_assets'][name])

    def test_filter_and_navigation_evidence_has_no_failures(self):
        for name, expected in (('filter.json', 1692), ('ui.json', 10),
                               ('navigation/summary.json', 2686),
                               ('transitions/summary.json', 11 if self.manifest.get('moves_search_keyboard') else 9),
                               ('surrounding/summary.json', 2)):
            data = json.loads((self.output / 'search-tests' / name).read_text())
            self.assertEqual(data['cases'], expected)
            self.assertEqual(data['issues'], [])
        self.assertEqual((self.output / 'search-tests/filter-sram.csv').read_bytes(), b'')

    def test_keyboard_and_results_do_not_use_naming_union_or_transient_ids(self):
        text = (self.output / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
        source = text[text.index('PokedexMovesSearch_Reset:'):]
        for forbidden in ('NamingScreenDestinationPointer', 'GetMoveIDFromIndex',
                          'MoveDiscovery_MarkIndex', 'OpenSRAM', 'SaveGame'):
            self.assertNotIn(forbidden, source)
        self.assertIn('db "abcdefghijklmnopqrstuvwxyz -"', source)
        self.assertIn('ASSERT wMovesSearchResults + NUM_ATTACKS * 2 <= $e000', text)
        self.assertIn('cp MOVE_NAME_LENGTH - 1', source)

    def test_keyboard_wraps_rows_and_all_commands_are_reachable(self):
        for position in range(27):
            self.assertEqual(keyboard_neighbor(keyboard_neighbor(position, 'left'), 'right'), position)
            self.assertEqual(keyboard_neighbor(position, 'left') // 9, position // 9)
        pending, visited = [0], {0}
        while pending:
            for key in ('up', 'down', 'left', 'right'):
                target = keyboard_neighbor(pending[-1], key)
                self.assertIn(target, range(29))
                if target not in visited:
                    visited.add(target)
                    pending.insert(0, target)
            pending.pop()
        self.assertEqual(visited, set(range(29)))

    def test_keyboard_controls_and_layout_are_qualified(self):
        if not self.manifest.get('moves_search_keyboard'):
            self.skipTest('Original lowercase-only keyboard')
        evidence = json.loads((self.output / 'search-tests/ui.json').read_text())
        controls = next(row['keyboard'] for row in evidence['rows'] if row['seen'] == 333)
        self.assertEqual(controls['navigation'], 232)
        self.assertEqual(controls['character_limit'], 12)
        for name, value in controls.items():
            if name not in ('navigation', 'character_limit'):
                self.assertTrue(value, name)

    def test_screenshot_defects_and_all_type_returns_are_qualified(self):
        if not self.manifest.get('moves_search_visual_repairs'):
            self.skipTest('Original visual prototype')
        evidence = json.loads((self.output / 'search-tests/visual/summary.json').read_text())
        self.assertEqual(evidence['issues'], [])
        self.assertEqual(len(evidence['baseline']['findings']), 7)
        self.assertTrue(evidence['baseline']['category_corruption_persists_on_cancel'])
        self.assertGreaterEqual(evidence['cases'], 1300)
        self.assertEqual([row['type_searches'] for row in evidence['rows']], [19, 19])
        previous = Path(self.manifest['visual_rollback'])
        self.assertEqual(sha256((previous / f'{STEM}.gbc').read_bytes()),
                         '8f2d3885886aad19e538b3e3a3e0f38502581ea4b9ea28f451d5072a460d4729')

    def test_current_link_sort_persistence_is_qualified(self):
        if not self.manifest.get('moves_search_visual_repairs'):
            self.skipTest('Original visual prototype')
        for path, cases in (('helpers.json', 4096), ('ui/summary.json', 16),
                            ('saves/summary.json', 11)):
            result = json.loads((self.output / 'sort-memory' / path).read_text())
            self.assertEqual(result['cases'], cases)
            self.assertEqual(result['issues'], [])
        timing = json.loads((self.output / 'sort-memory/timing/summary.json').read_text())
        self.assertEqual(timing['issues'], [])
        self.assertTrue(all(abs(r['ms']['delta']) < 0.2 for r in timing['summary'].values()))

    def test_current_link_full_pokemon_dex_regression_is_qualified(self):
        if not self.manifest.get('moves_search_visual_repairs'):
            self.skipTest('Original visual prototype')
        report = json.loads((self.output / 'dex-regression/summary.json').read_text())
        self.assertEqual(report['rom_sha256'], sha256(self.rom))
        self.assertEqual(report['failures'], 0)
        self.assertGreaterEqual(report['cases'], 4400)
        self.assertEqual(report['suites']['popover-qualification']['cases'], 373 * 3 * 2)
        self.assertEqual(report['suites']['selected']['cases'], 1178)
        self.assertEqual(report['suites']['mode-transitions']['transitions'], 192)
        self.assertEqual(len(report['suites']), 12)

    def test_current_link_tracking_and_receipt_hooks_are_qualified(self):
        if not self.manifest.get('moves_search_visual_repairs'):
            self.skipTest('Original visual prototype')
        data = json.loads((self.output / 'tracking-regression/summary.json').read_text())
        self.assertEqual(data['helper_cases'], 2380)
        self.assertEqual(data['snapshot_cases'], 4)
        self.assertEqual(data['issues'], [])
        for path, cases in (('acquisition-qualification.json', 12276),
                            ('acquisition-sources.json', 59)):
            data = json.loads((self.output / path).read_text())
            self.assertEqual(data['rom_sha256'], sha256(self.rom))
            self.assertEqual(data['cases'], cases)
            self.assertEqual(data['issues'], [])

    def test_compact_footer_query_gap_and_standard_blink_are_qualified(self):
        if not self.manifest.get('moves_search_form_polish'):
            self.skipTest('Earlier form prototype')
        data = json.loads((self.output / 'search-tests/form-polish/summary.json').read_text())
        self.assertEqual(data['native_blink_cases'], 1024)
        self.assertEqual(data['hardware_frames'], 256)
        self.assertEqual(data['populated_name_column'], 7)
        self.assertEqual(data['placeholder_column'], 10)
        self.assertTrue(data['shortened_footer'])
        self.assertTrue(data['start_unchanged'])
        self.assertEqual(data['issues'], [])
        source = Path(self.manifest['form_rollback'])
        self.assertEqual(sha256((source / f'{STEM}.gbc').read_bytes()),
                         '8d29d6129b1a53688502773fb000f58b25e389b32b4d37046b53a296f1ef29d0')

    def test_naming_cursor_animation_and_updated_footer_are_qualified(self):
        if not self.manifest.get('moves_search_naming_animation'):
            self.skipTest('Earlier solid-box keyboard')
        data = json.loads((self.output / 'search-tests/naming-cursor/summary.json').read_text())
        self.assertEqual(data['cases'], 3840)
        self.assertEqual(data['native_cases'], 1856)
        self.assertEqual(data['rendered_frames'], 1856)
        self.assertEqual(data['visible_display_frames'], 4)
        self.assertEqual(data['hidden_display_frames'], 4)
        for name in ('all_29_positions', 'both_cases', 'phase_not_reset',
                     'shared_engine_unchanged', 'updated_footer_linked', 'rendered_cursor_pixels'):
            self.assertTrue(data[name], name)
        self.assertEqual(data['issues'], [])
        source = Path(self.manifest['text_cursor_rollback'])
        self.assertEqual(sha256((source / f'{STEM}.gbc').read_bytes()),
                         'cdb3a632a653eb679ad19f7e7e3889260a77b69d179495aa26d788169cfaaba1')

    def test_end_cursor_matches_standard_geometry(self):
        if not self.manifest.get('moves_search_standard_end'):
            self.skipTest('Earlier fitted End box')
        data = json.loads((self.output / 'search-tests/naming-cursor/summary.json').read_text())
        self.assertTrue(data['end_matches_standard_oam'])
        self.assertEqual((data['end_width'], data['end_height'], data['end_column']), (40, 9, 15))
        source = Path(self.manifest['end_cursor_rollback'])
        self.assertEqual(sha256((source / f'{STEM}.gbc').read_bytes()),
                         'f22841b840f4c0bab8d58be9e2543351c4817c750eae26575f49e7a9b01e7174')
        from dex_timing.moves_search import full_regression_report
        regression = full_regression_report(self.output)
        self.assertEqual(regression['issues'], [])
        self.assertEqual(regression['paired_audio_cases'], 480)
        self.assertTrue(regression['sampled_cry_known_misses']['same'])


if __name__ == '__main__':
    unittest.main()
