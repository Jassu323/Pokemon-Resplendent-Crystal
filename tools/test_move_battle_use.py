"""Linked private stage-three hook and ownership contracts."""
import json
import os
from pathlib import Path
import re
import unittest

from tools.dex_timing.assets import read_symbols, sha256

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('MOVE_DISCOVERY_BUILD', ROOT / 'build/dex-moves-battle-use-20261008'))


@unittest.skipUnless((BUILD / 'moves-mode-manifest.json').exists(), 'Private battle prototype not built')
class BattleUse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((BUILD / 'moves-mode-manifest.json').read_text())
        cls.source = Path(cls.manifest['source'])
        cls.current = BUILD / 'candidate'

    def test_stage_boundary(self):
        self.assertEqual(self.manifest['persistence_stage'], 3)
        self.assertTrue(self.manifest['battle_use_hooks'])
        self.assertTrue(self.manifest['acquisition_hooks'])

    def test_only_three_battle_files_changed(self):
        changed = {p.relative_to(self.current / 'engine/battle').as_posix()
                   for p in (self.current / 'engine/battle').rglob('*.asm')
                   if p.read_bytes() != (self.source / 'candidate/engine/battle' / p.relative_to(self.current / 'engine/battle')).read_bytes()}
        self.assertEqual(changed, {'core.asm', 'effect_commands.asm', 'used_move_text.asm'})
        self.assertEqual((self.current / 'engine/battle/core.asm').read_text().count('farcall MoveDiscovery_BattleUse'), 1)

    def test_memory_addresses_unchanged(self):
        old = read_symbols(self.source / 'pokecrystal-dex-moves-mode.sym')
        new = read_symbols(BUILD / (self.manifest['stem'] + '.sym'))
        for name in old.keys() & new.keys():
            if name.startswith(('s', 'w', 'h')) and old[name][1] >= 0xa000:
                self.assertEqual(new[name], old[name], name)

    def test_animations_and_home_unchanged(self):
        for directory in ('home', 'engine/battle_anims', 'audio', 'data/battle_anims'):
            for path in (self.current / directory).rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (self.source / 'candidate' / path.relative_to(self.current)).read_bytes(), str(path))

    def test_wrapper_does_not_save(self):
        text = (self.current / 'engine/pokedex/move_battle_use.asm').read_text()
        self.assertIn('farcall MoveDiscovery_MarkLiveID', text)
        self.assertNotIn('SaveGame', text)
        self.assertNotIn('OpenSRAM', text)
        self.assertIn('cp 3', text)

    def test_presentation_boundaries(self):
        text = (self.current / 'engine/battle/used_move_text.asm').read_text()
        self.assertIn('call BattleTextbox\n\tmove_discovery_hook MoveDiscovery_BattleUse\n\tjp WaitBGMap', text)
        text = (self.current / 'engine/battle/effect_commands.asm').read_text()
        start = text.index('BattleCommand_Charge:')
        hook = text.index('move_discovery_hook MoveDiscovery_BattleUse', start)
        self.assertLess(text.index('.awake\n', start), hook)
        self.assertLess(text.index('set SUBSTATUS_CHARGED, [hl]', start), hook)

    def test_native_semantics(self):
        result = json.loads((BUILD / 'battle-use-qualification.json').read_text())
        self.assertEqual(result['rom_sha256'], self.manifest['rom_sha256'])
        self.assertEqual(result['contract_cases'], 4724)
        self.assertEqual(result['semantic_cases'], 400)
        self.assertFalse(result['issues'])
        self.assertEqual(len({(r['case'], r['actor'], r['phase']) for r in result['semantics']}), 400)
        for row in result['semantics']:
            self.assertFalse(row['issues'])
            if row['case'] == 'metronome-rejections':
                self.assertEqual(row['expected'], [57, 118])
            if row['case'] == 'disobedience-substitution' and not row['actor']:
                self.assertEqual(row['expected'], [57])

    def test_battle_save_dex_roundtrip(self):
        result = json.loads((BUILD / 'battle-use/roundtrip/result.json').read_text())
        self.assertFalse(result['issues'])
        for name in ('actual_battle_input', 'fled', 'normal_save', 'cold_reload', 'dex_snapshot'):
            self.assertTrue(result[name], name)
        self.assertEqual(result['visible_known_entry'], 1)

    def test_effect_script_presentation_coverage(self):
        text = (self.current / 'data/moves/effects.asm').read_text()
        blocks = re.split(r'^([A-Za-z_][A-Za-z_0-9]*):.*$', text, flags=re.M)
        scripts = {blocks[n]: blocks[n + 1] for n in range(1, len(blocks), 2)
                   if re.search(r'^\s+endmove\s*$', blocks[n + 1], re.M)}
        self.assertEqual(len(scripts), 114)
        for name, body in scripts.items():
            self.assertRegex(body, r'(?m)^\s+(movebegin|usedmovetext|focuspunch)\s*$', name)
        result = json.loads((BUILD / 'battle-use/supplemental-bide.json').read_text())
        self.assertEqual(result['cases'], 8)
        self.assertFalse(result['issues'])
        for row in result['results']:
            self.assertFalse(row['issues'])
            self.assertEqual(row['expected'], [117])

    def test_manual_battle_review(self):
        folder = BUILD / 'battle-review'
        result = json.loads((folder / 'review.json').read_text())
        stem = self.manifest['stem']
        self.assertEqual(sha256((folder / (stem + '.gbc')).read_bytes()), result['rom_sha256'])
        self.assertEqual(sha256((folder / (stem + '.sav')).read_bytes()), result['save_sha256'])
        self.assertTrue(result['cold_reload_verified'])
        self.assertEqual(result['cold_reload_pc_pokemon_verified'], 18)
        self.assertEqual(result['cold_reload_pc_moves_verified'], 69)
        self.assertEqual(result['moves'], 93)
        self.assertFalse(result['issues'])

    def test_protected_inputs(self):
        for path, digest in self.manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), digest, path)


if __name__ == '__main__':
    unittest.main()
