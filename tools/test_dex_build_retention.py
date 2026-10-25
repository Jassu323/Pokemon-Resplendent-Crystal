"""Guard the destructive build-retention workflow with small isolated fixtures."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import cleanup_dex_builds as cleanup


class RetentionTests(unittest.TestCase):
    def test_retention_policy(self):
        directory = Path('/example/dex-review')
        for name in ('candidate/engine/menu.asm', 'candidate/audio/sample.wav',
                     'results/summary.json', 'images/steel.png', 'rom.gbc',
                     'review.sav', 'campaign-logs/host.log', 'dex-run.log'):
            self.assertTrue(cleanup.keep(directory / name, directory), name)
        for name in ('trace.jsonl', 'trace.jsonl.gz', 'raster.csv', 'captured.wav',
                     'checkpoint.s0', 'trace.log', 'candidate/main.o',
                     'candidate/build/raw.json', 'candidate/gfx/front.dexanim'):
            self.assertFalse(cleanup.keep(directory / name, directory), name)

    def test_inventory_detects_changed_content_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            path = directory / 'summary.json'
            path.write_text('{}')
            before = cleanup.inventory(directory)
            path.write_text('{"changed": true}')
            self.assertNotEqual(before, cleanup.inventory(directory))

    def test_selection_excludes_assets_unrelated_directories_and_links(self):
        with tempfile.TemporaryDirectory() as folder:
            build = Path(folder)
            for name in ('dex-old-review', 'dex-info-assets', 'battle-history', 'user-work'):
                (build / name).mkdir()
            (build / 'dex-linked').symlink_to(build / 'user-work', target_is_directory=True)
            with patch.object(cleanup, 'BUILD', build):
                self.assertEqual([p.name for p in cleanup.eligible()], ['dex-old-review'])

    def test_compaction_retains_explicit_binary_fixture_and_verifies_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            build, destination = root / 'build', root / 'archive'
            directory = build / 'dex-test'
            directory.mkdir(parents=True)
            destination.mkdir()
            (directory / 'summary.json').write_text('{}')
            (directory / 'trace.csv').write_bytes(b'disposable')
            core = directory / 'native-core'
            core.write_bytes(b'explicit fixture executable')
            with patch.object(cleanup, 'BUILD', build), patch.object(cleanup, 'DEST', destination):
                record = cleanup.compact(directory, {core})
                self.assertTrue(record['verified'])
                self.assertEqual({r['path'] for r in record['files']},
                                 {'dex-test/summary.json', 'dex-test/native-core'})
                cleanup.verify(destination / record['archive'], record['files'])
                self.assertEqual(cleanup.digest(destination / record['archive']), record['archive_sha256'])
                (directory / 'summary.json').write_text('{"changed": true}')
                with self.assertRaises(AssertionError):
                    cleanup.compact(directory, {core})

    def exercise_cleanup(self, accepted):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            build, destination = root / 'build', root / 'archives'
            current = build / 'dex-test-current'
            reports = current / 'runtime-regression'
            reports.mkdir(parents=True)
            rom = b'unchanged production ROM'
            (root / 'pokecrystal.gbc').write_bytes(rom)
            (root / 'user.txt').write_text('unrelated work')
            receipt = reports / 'full-regression.json'
            receipt.write_text(json.dumps(dict(merge_ready=accepted, issues=[],
                               rom_sha256=hashlib.sha256(rom).hexdigest())))
            required = current / 'fixtures/native-core'
            required.parent.mkdir()
            required.write_bytes(b'keep executable fixture')
            required.chmod(0o755)
            raw = current / 'raw.csv'
            raw.write_bytes(b'not an authored source')
            source = current / 'candidate/menu.asm'
            source.parent.mkdir()
            source.write_text('ret\n')
            with patch.object(cleanup, 'ROOT', root), patch.object(cleanup, 'BUILD', build), \
                    patch.object(cleanup, 'DEST', destination), patch.object(cleanup, 'CURRENT', current), \
                    patch.object(cleanup, 'fixtures', return_value={required}), \
                    contextlib.redirect_stdout(io.StringIO()):
                if not accepted:
                    with self.assertRaises(AssertionError):
                        cleanup.run(True, 1)
                    self.assertTrue(raw.exists())
                    self.assertFalse(destination.exists())
                else:
                    cleanup.run(True, 1)
                    self.assertFalse(raw.exists())
                    self.assertFalse(source.exists())
                    self.assertEqual(required.read_bytes(), b'keep executable fixture')
                    self.assertTrue(required.stat().st_mode & 0o100)
                    self.assertTrue(receipt.exists())
                    cleanup.verify_retained()
                    required.write_bytes(b'corrupted live fixture')
                    with self.assertRaises(AssertionError):
                        cleanup.verify_retained()
                    required.write_bytes(b'keep executable fixture')
                    self.assertTrue((destination / 'cleanup.json').exists())
                self.assertEqual((root / 'pokecrystal.gbc').read_bytes(), rom)
                self.assertEqual((root / 'user.txt').read_text(), 'unrelated work')

    def test_cleanup_restores_live_fixtures_and_preserves_root(self):
        self.exercise_cleanup(True)

    def test_cleanup_refuses_unaccepted_integration(self):
        self.exercise_cleanup(False)


if __name__ == '__main__':
    unittest.main()
