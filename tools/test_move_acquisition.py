"""Stage-two hook coverage and accepted-baseline ownership contracts."""
import json
import os
from pathlib import Path
import re
import unittest

from dex_timing.assets import read_symbols, sha256, offset
from dex_timing.cold_listing import ROOT
from dex_timing.move_acquisition import owned_indices


class AcquisitionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = ROOT / os.environ.get('MOVE_DISCOVERY_BUILD', 'build/dex-moves-acquisition-20261008')
        cls.manifest = json.loads((cls.build / 'moves-mode-manifest.json').read_text())
        cls.baseline = Path(cls.manifest['source'])
        cls.source = cls.build / 'candidate'
        cls.symbols = read_symbols(cls.build / 'pokecrystal-dex-moves-acquisition.sym')

    def test_stage_boundary(self):
        self.assertIn(self.manifest['persistence_stage'], (2, 3))
        self.assertTrue(self.manifest['acquisition_hooks'])
        self.assertTrue(self.manifest['legacy_bootstrap'])
        self.assertEqual(self.manifest['battle_use_hooks'], self.manifest['persistence_stage'] == 3)

    def test_no_memory_reallocation(self):
        before = read_symbols(self.baseline / 'pokecrystal-dex-moves-mode.sym')
        for name, pair in before.items():
            if name.startswith(('s', 'w')) and pair[1] >= 0xa000 and name in self.symbols:
                self.assertEqual(pair, self.symbols[name], name)

    def test_no_animation_or_audio_changes(self):
        for directory in ('engine/battle_anims', 'audio', 'home'):
            for path in (self.baseline / 'candidate' / directory).rglob('*'):
                if path.is_file():
                    relative = path.relative_to(self.baseline / 'candidate')
                    self.assertEqual(path.read_bytes(), (self.source / relative).read_bytes(), str(relative))

    def test_no_generated_or_modified_visual_assets(self):
        for path in (self.baseline / 'candidate/gfx/pokedex').rglob('*.png'):
            self.assertEqual(path.read_bytes(), (self.source / 'gfx/pokedex' / path.name).read_bytes())

    def test_preserving_hook_macro(self):
        text = (self.source / 'macros/farcall.asm').read_text()
        self.assertIn('MACRO move_discovery_hook\n\tpush af\n\tpush hl\n\tfarcall \\1\n\tpop hl\n\tpop af\nENDM', text)

    def test_generic_generation_has_no_blanket_hook(self):
        text = (self.source / 'engine/pokemon/move_mon.asm').read_text()
        for label in ('TryAddMonToParty:', 'GeneratePartyMonStats:', 'GiveEgg::'):
            body = text.split(label, 1)[1]
            body = re.split(r'(?m)^[A-Za-z_][A-Za-z_0-9]*::?', body, maxsplit=1)[0]
            self.assertNotIn('move_discovery_hook', body, label)

    def test_recovery_bootstrap_after_active_box_load(self):
        text = (self.source / 'engine/menus/save.asm').read_text()
        for copy in ('Primary', 'Backup'):
            self.assertIn(f'farcall MoveDiscovery_Load{copy}\n\tcall LoadBox\n\tmove_discovery_hook MoveDiscovery_Bootstrap{copy}', text)

    def test_move_orders_unchanged(self):
        before = read_symbols(self.baseline / 'pokecrystal-dex-moves-mode.sym')
        old = (self.baseline / 'pokecrystal-dex-moves-mode.gbc').read_bytes()
        new = (self.build / 'pokecrystal-dex-moves-acquisition.gbc').read_bytes()
        for label in ('PokedexMovesModeTypeOrder', 'PokedexMovesModeNameOrder'):
            a, b = offset(before[label]), offset(self.symbols[label])
            self.assertEqual(old[a:a + 668], new[b:b + 668])

    def test_owned_oracle_and_maximum_capacity(self):
        self.assertEqual(owned_indices((self.build / 'legacy-input.sav').read_bytes(), self.symbols), [33, 34, 50, 75, 77, 93, 115])
        for n in range(1, 15):
            self.assertEqual(owned_indices((self.build / f'acquisition-qualification/legacy-full-current-{n}.sav').read_bytes(), self.symbols), list(range(1, 334)))

    def test_protected_artifacts_and_review_link(self):
        self.assertEqual(sha256((self.build / 'pokecrystal-dex-moves-acquisition.gbc').read_bytes()), self.manifest['rom_sha256'])
        for path, expected in self.manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), expected, path)

    def test_native_source_report_and_pending_contest(self):
        report = json.loads((self.build / 'acquisition-sources.json').read_text())
        self.assertEqual(report['rom_sha256'], self.manifest['rom_sha256'])
        self.assertFalse(report['issues'])
        rows = {r['case']: r for r in report['results']}
        self.assertEqual(rows['contest-pending']['entry'], 'BugContest_SetCaughtContestMon')
        self.assertEqual(rows['contest-pending']['discovered'], [])
        self.assertFalse(any(rows['contest-pending']['hook_hits'].values()))
        for kind in ('failed', 'trainer', 'full', 'tutorial'):
            row = rows['ball-' + kind]
            self.assertEqual(row['entry'], 'PokeBallEffect')
            self.assertFalse(row['discovered'])
            self.assertFalse(any(row['hook_hits'].values()))
        for owner in ('man', 'lady'):
            for outcome in ('success', 'decline', 'poor', 'full'):
                row = rows[f'daycare-service-{owner}-{outcome}']
                self.assertFalse(row['issues'])
                self.assertEqual(bool(row['discovered']), outcome == 'success')


if __name__ == '__main__':
    unittest.main()
