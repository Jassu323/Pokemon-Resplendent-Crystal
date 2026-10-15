"""Current-link bookmark contracts and opt-in trace retention controls."""
import gzip
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT
from dex_timing.direction_changes import load_trace

BASE = ROOT / 'build/dex-moves-position-20261014'


class MovesPositionTests(unittest.TestCase):
    def result(self, name):
        return json.loads((BASE / 'position-tests' / (name + '.json')).read_text())

    def test_saved_fields_consume_only_four_padding_bytes(self):
        old = read_symbols(BASE / 'rollback/pokecrystal.sym')
        new = read_symbols(BASE / 'candidate/pokecrystal.sym')
        expected = {'wMovesDexBookmarkTag': (1, 0xd9e4),
                    'wMovesDexBookmarkMove': (1, 0xd9e5),
                    'wMovesDexBookmarkRow': (1, 0xd9e7)}
        for name, value in expected.items():
            self.assertEqual(new[name], value)
        for name, value in old.items():
            if value[1] >= 0xa000:
                self.assertEqual(new[name], value, name)
        self.assertEqual(new['wPokecenter2FSceneID'], (1, 0xd9f0))

    def test_private_link_and_resource_limits(self):
        manifest = json.loads((BASE / 'position-manifest.json').read_text())
        self.assertEqual(sha256((BASE / 'candidate/pokecrystal.gbc').read_bytes()), manifest['candidate_sha256'])
        self.assertLessEqual(manifest['delta']['ROMX'], 350)
        self.assertTrue(all(value == 0 for name, value in manifest['delta'].items() if name != 'ROMX'))
        combined_path = ROOT / 'build/dex-position-memory-20261014/position-memory-manifest.json'
        combined = json.loads(combined_path.read_text()) if combined_path.exists() else {}
        integration = None
        if combined.get('production_integrated'):
            integration = json.loads(Path(combined['production_integration_receipt']).read_text())
            self.assertTrue(integration['exact_approved_match'])
            self.assertEqual(sha256((ROOT / 'pokecrystal.gbc').read_bytes()), combined['candidate_sha256'])
        for path, digest in manifest['protected'].items():
            source = Path(path)
            if integration and path in integration['before_artifacts']:
                self.assertEqual(integration['before_artifacts'][path], digest)
                source = Path(combined['production_integration_receipt']).parent / 'before' / source.name
            self.assertEqual(sha256(source.read_bytes()), digest, path)

    def test_helpers_cover_every_legal_viewport_and_all_banks(self):
        result = self.result('helpers')
        self.assertEqual(result['counts']['valid_viewports'], 5216)
        self.assertEqual(result['counts']['remember_register_bank'], 5328)
        self.assertEqual(result['counts']['boundary_clamp'], 1332)
        self.assertTrue(result['no_sram_write'])
        self.assertTrue(result['registers_and_banks_preserved'])
        self.assertTrue(result['discovery_and_gc_preserved'])
        self.assertFalse(result['issues'])

    def test_normal_buttons_cover_all_rows_orders_and_origins(self):
        result = self.result('ui')
        self.assertEqual({(row['style'], row['order'], row['cursor']) for row in result['rows']},
                         {(style, order, cursor) for style in range(2) for order in range(2) for cursor in range(8)})
        self.assertFalse(result['issues'])

    def test_unseen_positions_survive_shared_workspace_owners(self):
        result = self.result('owners')
        self.assertEqual(result['cases'], 16)
        self.assertEqual({row['owner'] for row in result['rows']}, {'info', 'moves', 'unown', 'types'})
        self.assertTrue(all(row['unseen_identity'] % 2 == 0 for row in result['rows']))
        self.assertFalse(result['issues'])

    def test_save_recovery_and_cancellation(self):
        saves, edges = self.result('saves'), self.result('save-edges')
        self.assertEqual(saves['cases'], 16)
        self.assertEqual(saves['lifecycle_cases'], 5)
        self.assertEqual(edges['interrupted_save_cases'], 14)
        self.assertTrue(edges['canceled_save_preserved'])
        self.assertTrue(edges['canceled_new_game_preserved'])
        self.assertFalse(saves['issues'] or edges['issues'])

    def test_entry_timing_is_paired_and_correct_identity_is_restored(self):
        result = self.result('timing')
        orders = json.loads((ROOT / 'build/dex-moves-mode-assets/manifest.json').read_text())['orders']
        self.assertEqual(result['cases'], 48)
        self.assertEqual(len(result['pairs']), 24)
        for row in result['rows']:
            expected = row['position'] if row['variant'] == 'candidate' else 0
            self.assertEqual(row['state']['selected'], orders[row['order']][expected])
            self.assertEqual(row['state']['scroll'] + row['state']['cursor'], expected)

    def test_no_interrupt_or_artwork_changes(self):
        for name in ('home', 'gfx'):
            for path in (BASE / 'baseline-source' / name).rglob('*'):
                if path.is_file() and path.suffix not in ('.o', '.d'):
                    self.assertEqual(path.read_bytes(), (BASE / 'candidate' / path.relative_to(BASE / 'baseline-source')).read_bytes(), str(path))


class TraceRetentionTests(unittest.TestCase):
    def test_compression_is_lossless_replayable_and_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / 'active'
            active.mkdir()
            path = active / 'trace.jsonl'
            data = b'{"event":"one","value":1}\n{"event":"two","value":2}\n'
            path.write_bytes(data)
            outside = root / 'outside.jsonl'
            outside.write_bytes(data)
            with patch.dict(os.environ, DEX_COMPRESS_TRACE_ROOT=str(active)):
                expected = load_trace(path)
                self.assertFalse(path.exists())
                self.assertEqual(gzip.decompress(path.with_suffix('.jsonl.gz').read_bytes()), data)
                self.assertEqual(load_trace(path), expected)
                self.assertEqual(load_trace(outside), expected)
                self.assertTrue(outside.exists())

    def test_default_does_not_replace_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.jsonl'
            path.write_text('{"event":"one"}\n')
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(load_trace(path), [{'event': 'one'}])
                self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
