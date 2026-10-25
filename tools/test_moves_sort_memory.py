"""Private sort-memory source, memory, native-evidence and review contracts."""
import json
import os
from pathlib import Path
import unittest

from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT
from dex_timing.moves_sort_memory import STEM, TAG, saved_preference
from dex_timing.move_persistence import core_valid
from move_discovery_assets import decode_record


class MovesSortMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / os.environ.get('MOVES_SORT_MEMORY_BUILD', 'build/dex-moves-sort-memory-20261008')
        cls.manifest = json.loads((cls.output / 'moves-mode-manifest.json').read_text())
        cls.result = json.loads((cls.output / 'sort-memory-qualification.json').read_text())
        cls.symbols = read_symbols(cls.output / f'{STEM}.sym')
        cls.source = Path(cls.manifest['sort_memory_source'])

    def test_rom_matches_all_qualified_outputs(self):
        actual = sha256((self.output / f'{STEM}.gbc').read_bytes())
        self.assertEqual(actual, self.manifest['rom_sha256'])
        self.assertEqual(actual, self.result['rom_sha256'])
        for name in ('pokecrystal-dex-moves-mode', 'pokecrystal-dex-moves-persistence',
                     'battle-review/' + STEM):
            self.assertEqual(sha256((self.output / f'{name}.gbc').read_bytes()), actual)

    def test_source_delta_is_only_moves_preference_and_reserved_padding(self):
        self.assertEqual(self.result['source_delta'],
                         ['engine/pokedex/pokedex_moves_mode.asm', 'ram/wram.asm'])
        before, after = self.source / 'candidate', self.output / 'candidate'
        changes = {p.relative_to(after).as_posix() for p in after.rglob('*.asm')
                   if not (before / p.relative_to(after)).exists()
                   or p.read_bytes() != (before / p.relative_to(after)).read_bytes()}
        self.assertEqual(changes, set(self.result['source_delta']))
        for path in (after / 'gfx').rglob('*.png'):
            self.assertEqual(path.read_bytes(), (before / path.relative_to(after)).read_bytes())

    def test_old_addresses_and_new_game_clear_region_are_preserved(self):
        old = read_symbols(self.source / 'pokecrystal-dex-moves-battle-use.sym')
        for name, pair in old.items():
            if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in self.symbols:
                self.assertEqual(self.symbols[name], pair, name)
        self.assertEqual(self.symbols['wLastMovesDexSort'], (1, 0xd9e3))
        self.assertLess(self.symbols['wGameData'][1], self.symbols['wLastMovesDexSort'][1])
        self.assertLess(self.symbols['wLastMovesDexSort'][1], self.symbols['wPlayerDataEnd'][1])
        before = (self.source / 'candidate/ram/wram.asm').read_text()
        after = (self.output / 'candidate/ram/wram.asm').read_text()
        self.assertEqual(after.replace('wLastMovesDexSort:: db ; saved padding; $a0 Type, $a1 Alphabet\n\tds 12', '\tds 13'), before)

    def test_confirmation_is_the_only_preference_writer(self):
        source = (self.output / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
        self.assertEqual(source.count('call PokedexMovesMode_RestoreSort'), 1)
        self.assertEqual(source.count('call PokedexMovesMode_RememberSort'), 1)
        self.assertIn('ld a, [wDexArrowCursorPosIndex]\n    call PokedexMovesMode_RememberSort\n    ld hl, wMovesModeSort', source)
        for forbidden in ('OpenSRAM', 'SaveGame', 'MoveDiscovery_MarkIndex'):
            self.assertNotIn(forbidden, source)
        self.assertIn('cp MOVES_SORT_MEMORY_TAG + 1', source)
        self.assertIn('    cp 2\n    jr nc, .done', source)

    def test_all_raw_values_and_wram_banks_are_qualified(self):
        result = json.loads((self.output / 'sort-memory/helpers.json').read_text())
        self.assertEqual(result['cases'], 4096)
        self.assertEqual({(r['helper'], r['bank'], r['value']) for r in result['rows']},
                         {(helper, bank, value) for helper in ('restore', 'remember')
                          for bank in range(8) for value in range(256)})
        self.assertTrue(result['all_registers_and_banks_restored'])
        self.assertTrue(result['adjacent_saved_bytes_preserved'])
        self.assertEqual((self.output / 'sort-memory/helpers-sram.csv').read_bytes(), b'')

    def test_modes_close_reopen_and_canceled_choices_are_qualified(self):
        result = json.loads((self.output / 'sort-memory/ui/summary.json').read_text())
        self.assertEqual(result['cases'], 16)
        self.assertEqual({(r['presentation'], r['order'], r['phase']) for r in result['rows']},
                         {(p, o, f) for p in range(2) for o in range(2) for f in range(4)})
        self.assertTrue(all(not r['issues'] for r in result['rows']))

    def test_save_continue_backup_legacy_and_new_game_are_qualified(self):
        result = json.loads((self.output / 'sort-memory/saves/summary.json').read_text())
        self.assertEqual(result['cases'], 11)
        self.assertEqual(result['lifecycle_cases'], 6)
        self.assertEqual({r['case'] for r in result['rows'] if 'case' in r},
                         {'primary-wins', 'bad-primary', 'bad-backup', 'legacy-zero',
                          'legacy-one', 'invalid-255', 'canceled-save'})
        for prefix in ('s', 'sBackup'):
            new = (self.output / 'sort-memory/saves/new-game-saved.sav').read_bytes()
            self.assertEqual(saved_preference(new, self.symbols, prefix), 0)
            self.assertTrue(core_valid(new, self.symbols, prefix))
            canceled = (self.output / 'sort-memory/saves/new-game-canceled.sav').read_bytes()
            self.assertEqual(saved_preference(canceled, self.symbols, prefix), TAG + 1)

    def test_review_saves_retain_discovery_and_use_alphabet(self):
        for row in self.result['review']:
            path = Path(row['path'])
            self.assertEqual(sha256(path.read_bytes()), row['sha256'])
            source = self.source / ('battle-review' if path.parent.name == 'battle-review' else '') / 'pokecrystal-dex-moves-battle-use.sav'
            for prefix in ('s', 'sBackup'):
                self.assertEqual(saved_preference(path.read_bytes(), self.symbols, prefix), TAG + 1)
                self.assertTrue(core_valid(path.read_bytes(), self.symbols, prefix))
                self.assertEqual(decode_record(path.read_bytes(), self.symbols, prefix),
                                 decode_record(source.read_bytes(), self.symbols, prefix))

    def test_resources_and_full_moves_regression(self):
        self.assertEqual(self.result['resource_delta'],
                         dict(ROM0=0, ROMX=65, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0))
        self.assertEqual(self.result['moves_navigation_cases'], 1338)
        self.assertEqual(self.result['moves_page_cases'], 1348)
        self.assertEqual(self.result['moves_interface_checks'], 544)
        self.assertEqual(self.result['transition_cases'], 176)
        self.assertTrue(all(abs(r['first_delta']) < 0.001 and abs(r['complete_delta']) < 0.001
                            for r in self.result['transition_deltas']))
        self.assertTrue(all(abs(r['ms']['delta']) < 0.2 for r in self.result['timing'].values()))

    def test_rollback_and_production_are_unchanged(self):
        self.assertEqual(self.result['protected_inputs'], 32)
        for path, digest in self.manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), digest, path)
        self.assertFalse(self.result['issues'])


if __name__ == '__main__':
    unittest.main()
