"""Build-time Area index parity and source validation checks."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pokedex_area_assets import ROOT, compile_assets, encounters
from dex_timing.assets import Repository, offset
from dex_timing.area_ui import nests
from pokedex_info_assets import species


class AreaAssetsTest(unittest.TestCase):
    def test_every_species_matches_native_tables(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        _, palettes, generated = compile_assets()
        for index, name in enumerate(species(), 1):
            for region in (0, 1):
                with self.subTest(species=name, region=region):
                    self.assertEqual(generated[name, region], nests(repo, index, region))
        at = offset(repo.symbols['TownMapPals.PalMap'])
        expected = bytes((repo.rom[at + i // 2] >> (4 * (i & 1))) & 7 if i < 96 else 0 for i in range(256))
        self.assertEqual(palettes, expected)

    def test_rejects_incomplete_encounter_record(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'water.asm'
            path.write_text('def_water_wildmons ROUTE_30\ndbwbb 100, CATERPIE, 2, 2\nend_water_wildmons\n')
            with self.assertRaisesRegex(ValueError, 'Expected 3 encounter slots'):
                encounters(path, 'water')

    def test_encounter_order_is_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'water.asm'
            path.write_text('def_water_wildmons ROUTE_30\n' +
                           ''.join(f'dbwbb 30, {name}, 2, 2\n' for name in ('CATERPIE', 'MEW', 'CATERPIE')) +
                           'end_water_wildmons\n')
            self.assertEqual(encounters(path, 'water'), [('ROUTE_30', ['CATERPIE', 'MEW', 'CATERPIE'])])


if __name__ == '__main__':
    unittest.main()
