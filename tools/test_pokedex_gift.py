"""Focused contracts for the private Pokedex/Struggle award revision."""
import json
import os
from pathlib import Path
import unittest

from tools.dex_timing.assets import read_symbols, sha256
from tools.pokedex_info_assets import constants

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('MOVE_DISCOVERY_BUILD', ROOT / 'build/dex-moves-struggle-grant-20261008'))


@unittest.skipUnless((BUILD / 'pokedex-gift-qualification.json').exists(), 'Private gift revision not qualified')
class PokedexGift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((BUILD / 'moves-mode-manifest.json').read_text())
        cls.report = json.loads((BUILD / 'pokedex-gift-qualification.json').read_text())
        cls.baseline = Path(cls.manifest['prior_battle_baseline'])
        cls.current = BUILD / 'candidate'
        cls.struggle = constants(ROOT / 'constants/move_constants.asm')['STRUGGLE']

    def test_qualified_link(self):
        self.assertTrue(self.manifest['struggle_at_pokedex'])
        self.assertTrue(self.manifest['battle_use_hooks'])
        self.assertEqual(self.report['rom_sha256'], self.manifest['rom_sha256'])
        self.assertEqual(self.report['rom_sha256'], sha256((BUILD / (self.manifest['stem'] + '.gbc')).read_bytes()))
        self.assertFalse(self.report['issues'])

    def test_exact_award_hook(self):
        text = (self.current / 'maps/MrPokemonsHouse.asm').read_text()
        self.assertIn('setflag ENGINE_POKEDEX\n\tcallasm MoveDiscovery_PokedexGift\n', text)
        self.assertEqual(text.count('callasm MoveDiscovery_PokedexGift'), 1)
        helper = (self.current / 'engine/pokedex/move_pokedex_gift.asm').read_text()
        self.assertIn('ld de, STRUGGLE\n    farcall MoveDiscovery_MarkIndex', helper)
        for forbidden in ('GetMoveID', 'GetMoveIndex', 'OpenSRAM', 'SaveGame'):
            self.assertNotIn(forbidden, helper)

    def test_surrounding_owners_unchanged(self):
        for directory in ('home', 'engine/battle', 'engine/battle_anims', 'audio', 'data', 'gfx', 'ram'):
            for path in (self.current / directory).rglob('*'):
                if path.is_file() and path.suffix not in ('.o', '.d'):
                    old = self.baseline / 'candidate' / path.relative_to(self.current)
                    self.assertEqual(path.read_bytes(), old.read_bytes(), str(path))

    def test_storage_addresses_unchanged(self):
        old = read_symbols(self.baseline / (self.manifest['stem'] + '.sym'))
        new = read_symbols(BUILD / (self.manifest['stem'] + '.sym'))
        for name in old.keys() & new.keys():
            if name.startswith(('w', 's', 'h')) and old[name][1] >= 0xa000:
                self.assertEqual(new[name], old[name], name)

    def test_native_awards_and_preservation(self):
        self.assertEqual(self.report['struggle_index'], self.struggle)
        self.assertEqual(self.report['award_cases'], 16)
        self.assertEqual(self.report['repeated_awards'], 16)
        self.assertEqual(self.report['contracts'], 16)
        self.assertTrue(self.report['no_immediate_sram_write'])
        self.assertEqual(self.report['lifecycle_cases'], 5)
        self.assertEqual(self.report['visible_known_entry'], self.struggle)

    def test_review_files(self):
        for row in self.report['review']:
            self.assertEqual(sha256(Path(row['save']).read_bytes()), row['save_sha256'])
            self.assertTrue(row['normal_save'])
            self.assertTrue(row['cold_reload'])
            self.assertIn(self.struggle, row['discovered'])
            if row['fixture'] == 'battle':
                self.assertEqual(row['discovered'], [self.struggle])

    def test_protected_inputs(self):
        for path, digest in self.manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), digest, path)


if __name__ == '__main__':
    unittest.main()
