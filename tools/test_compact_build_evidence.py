"""Retention and path-boundary checks before destructive build cleanup."""
from pathlib import Path
import hashlib
import io
import tarfile
import tempfile
import unittest

from compact_build_evidence import current_bulk, historical_keep, safe_relative, verify_archive


class RetentionTest(unittest.TestCase):
    def test_preserves_replay_inputs_source_reports_and_media(self):
        for name in ('start.s0', 'private.sav', 'pokecrystal.gbc', 'pokecrystal.sym',
                     'pokecrystal.map', 'report.json', 'config.json', 'summary.csv',
                     'comparison.mp4', 'review.png', 'case/result.json', 'reference.json',
                     'candidate/engine/demo.asm',
                     'candidate/Makefile', 'candidate/data/demo.bin'):
            with self.subTest(name=name):
                self.assertTrue(historical_keep('build/trial/' + name))

    def test_retires_only_old_bulk(self):
        for name in ('frame-001.ppm', 'audio.wav', 'audio.raw.gz', 'events.jsonl',
                     'events.jsonl.gz', 'candidate/main.o',
                     'candidate/build/events.jsonl', 'candidate/gfx/demo.2bpp',
                     'candidate/__pycache__/demo.pyc'):
            with self.subTest(name=name):
                self.assertFalse(historical_keep('build/trial/' + name))

    def test_current_starting_inputs_and_reports_stay_loose(self):
        for name in ('start.s0', 'seed.sav', 'report.json', 'summary.json', 'config.json', 'runner'):
            self.assertFalse(current_bulk(Path(name)))
        for name in ('events.jsonl', 'events.jsonl.gz', 'frame.ppm', 'audio.wav', 'result.json'):
            self.assertTrue(current_bulk(Path(name)))

    def test_refuses_paths_outside_exact_family(self):
        safe_relative('build/trial/seed.sav', 'trial')
        for name in ('/build/trial/seed.sav', 'build/trial/../../save.sav',
                     'build/other/save.sav', 'research_artifacts/trial/save.sav'):
            with self.assertRaises(RuntimeError):
                safe_relative(name, 'trial')

    def test_round_trip_checks_content_and_missing_members(self):
        content = b'preserved replay input'
        record = dict(path='build/trial/start.s0', bytes=len(content),
                      sha256=hashlib.sha256(content).hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'trial.tar.gz'
            with tarfile.open(target, 'w:gz') as archive:
                member = tarfile.TarInfo(record['path'])
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
            verify_archive(target, [record])
            with self.assertRaisesRegex(RuntimeError, 'Changed content'):
                verify_archive(target, [dict(record, sha256='0' * 64)])
            with self.assertRaisesRegex(RuntimeError, 'Missing archive members'):
                verify_archive(target, [record, dict(record, path='build/trial/other.s0')])
            with self.assertRaisesRegex(RuntimeError, 'Duplicate archive members'):
                verify_archive(target, [record, record])


if __name__ == '__main__':
    unittest.main()
