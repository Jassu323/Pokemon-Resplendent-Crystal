"""Negative controls for the independent Tower oracle and acceptance gate."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.dex_timing import battle_tower as tower
from tools.dex_timing.assets import Repository, offset, sha256
from tools.dex_timing.cold_listing import ROOT


class BattleTowerSuiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build', prefix='tower-controls-')
        self.folder = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        self.cfg = dict(root=str(ROOT), rom=str(self.repo.rom_path), sym=str(ROOT / 'pokecrystal.sym'))

    def test_catalog_control_and_corrupted_species(self):
        rows = tower.data(self.cfg, self.folder)
        self.assertEqual(len(rows), 242)
        self.assertFalse(any(row['issues'] for row in rows))
        altered = copy.copy(self.repo)
        payload = bytearray(altered.rom)
        payload[offset(altered.symbols['BattleTowerMons'])] ^= 1
        altered.rom = bytes(payload)
        with patch.object(tower, 'Repository', return_value=altered):
            self.assertTrue(tower.data(self.cfg, self.folder)[0]['issues'])

    def test_corrupted_action_pointer(self):
        altered = copy.copy(self.repo)
        payload = bytearray(altered.rom)
        at = offset(altered.symbols['BattleTowerAction.dw'])
        payload[at:at + 2] = bytes(2)
        altered.rom = bytes(payload)
        with patch.object(tower, 'Repository', return_value=altered):
            self.assertTrue(tower.data(self.cfg, self.folder)[210]['issues'])

    def test_candidate_only_failure_is_not_accepted(self):
        for variant in ('baseline', 'candidate'):
            (self.folder / variant).mkdir()
        variants = {name: dict(tag=name) for name in ('baseline', 'candidate')}
        def records(cfg, folder):
            return [dict(case='same-case', issues=['Injected failure'] if cfg['tag'] == 'candidate' else [])]
        with patch.object(tower, 'configs', return_value=variants), patch.object(tower, 'data', side_effect=records), redirect_stdout(io.StringIO()):
            self.assertEqual(tower.run(self.folder, 'data'), 1)
        self.assertFalse(json.loads((self.folder / 'data-comparison.json').read_text())['no_new_failures'])

    def test_truncated_phase_cannot_pass_report(self):
        protected = self.folder / 'input.bin'
        protected.write_bytes(b'control')
        tower.write(self.folder / 'config.json', dict(protected={str(protected): sha256(protected.read_bytes())},
            variants={name: dict(rom_sha256='control') for name in ('baseline', 'candidate')}))
        for variant in ('baseline', 'candidate'):
            (self.folder / variant / 'data').mkdir(parents=True)
            tower.write(self.folder / variant / 'data/summary.json', dict(cases=1, failures=0, results=[dict(case='only-one', issues=[])]))
        tower.write(self.folder / 'data-comparison.json', dict(no_new_failures=True))
        with patch.object(tower, 'PHASES', ('data',)), patch.object(tower, 'EXPECTED_CASES', dict(data=2)), redirect_stdout(io.StringIO()):
            self.assertEqual(tower.report(self.folder), 1)
        result = json.loads((self.folder / 'report.json').read_text())
        self.assertFalse(result['coverage_complete'])
        self.assertFalse(result['clean'])
        self.assertFalse(result['no_new_failures'])


if __name__ == '__main__':
    unittest.main()
