"""Small isolated controls for the durable fixture restore boundary."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools.dex_timing import regression_fixtures as fixtures


class FixtureBundleTests(unittest.TestCase):
    def bundle(self, base, name='build/seed.json', data=b'{"path":"@ROOT@/build/input.sav"}'):
        bundle = base / 'bundle'
        bundle.mkdir()
        archive = bundle / 'inputs.tar.xz'
        with tarfile.open(archive, 'w:xz') as target:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            target.addfile(member, io.BytesIO(data))
        manifest = dict(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            archive_bytes=archive.stat().st_size,
            files=[dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                        portable_json=name.endswith('.json'))])
        (bundle / 'manifest.json').write_text(json.dumps(manifest))
        return bundle

    def test_portable_restore_is_idempotent_and_does_not_touch_main_save(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            bundle = self.bundle(root)
            (root / 'pokecrystal.sav').write_bytes(b'protected player save')
            with patch.object(fixtures, 'ROOT', root):
                self.assertEqual(fixtures.restore(root, bundle)['restored'], 1)
                self.assertEqual(fixtures.restore(root, bundle)['restored'], 0)
            self.assertEqual(json.loads((root / 'build/seed.json').read_text())['path'],
                             str(root / 'build/input.sav'))
            self.assertEqual((root / 'pokecrystal.sav').read_bytes(), b'protected player save')

    def test_different_existing_inputs_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            bundle = self.bundle(root)
            (root / 'build').mkdir()
            (root / 'build/seed.json').write_bytes(b'user work')
            with patch.object(fixtures, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Existing fixture differs'):
                fixtures.restore(root, bundle)
            self.assertEqual((root / 'build/seed.json').read_bytes(), b'user work')

    def test_paths_outside_build_are_rejected(self):
        for name in ('build', '../pokecrystal.sav', '/tmp/fixture', 'docs/fixture', 'build/../pokecrystal.sav'):
            with self.subTest(path=name), self.assertRaises(ValueError):
                fixtures.safe_path(name)

    def test_corruption_and_symlink_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            bundle = self.bundle(root)
            (root / 'outside').mkdir()
            (root / 'build').symlink_to(root / 'outside', target_is_directory=True)
            with patch.object(fixtures, 'ROOT', root), self.assertRaisesRegex(ValueError, 'symlinked'):
                fixtures.restore(root, bundle)
            with (bundle / 'inputs.tar.xz').open('ab') as stream:
                stream.write(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                fixtures.payload(bundle)

    def test_concurrent_restores_share_a_single_writer(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            bundle = self.bundle(root)
            with patch.object(fixtures, 'ROOT', root), ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: fixtures.restore(root, bundle), range(2)))
            self.assertEqual(sorted(row['restored'] for row in results), [0, 1])


if __name__ == '__main__':
    unittest.main()
