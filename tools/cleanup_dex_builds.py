"""Compact approved Dex build history; retain recipes, reports and live fixtures.

Raw per-frame/per-instruction traces, captured PCM, temporary emulator states,
compiled observers and intermediate converted assets are deliberately retired.
Source, ROMs, batteries, JSON evidence and screenshots are verified in archives
before any loose build family is removed. Only named Dex build families qualify.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
DEST = ROOT / 'research_artifacts/dex-build-history-20261012'
CURRENT = BUILD / 'dex-types-production-runtime-20261012'
SOURCE_DIRS = {'candidate', 'source', 'sources', 'host-source', 'source-snapshots', 'inputs'}
INTERMEDIATE = {'.o', '.pyc', '.lz', '.1bpp', '.2bpp', '.gbcpal', '.dimensions',
                '.dexanim', '.dextimeline', '.dexschedule', '.d', '.exe'}
EVIDENCE = {'.json', '.asm', '.py', '.c', '.h', '.inc', '.sh', '.md', '.txt',
            '.toml', '.ini', '.pal', '.patch', '.diff', '.png', '.jpg', '.gif',
            '.mp4', '.gbc', '.gb', '.sym', '.map', '.sav', '.tar'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def paths(directory):
    for base, dirs, names in os.walk(directory, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != '.git' and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if path.is_file() and not path.is_symlink():
                yield path


def inventory(directory):
    h, total, count = hashlib.sha256(), 0, 0
    for path in paths(directory):
        s = path.stat()
        h.update(json.dumps((str(path.relative_to(directory)), s.st_size,
                             s.st_mtime_ns, s.st_ino)).encode())
        total += s.st_size
        count += 1
    return dict(metadata_sha256=h.hexdigest(), bytes=total, files=count)


def eligible():
    for path in sorted(BUILD.iterdir()):
        if path.is_dir() and not path.is_symlink() and (
                path.name.startswith('dex-') or path.name.startswith('moves-dex-production-integration-')):
            if not path.name.endswith('-assets'):
                yield path


def keep(path, directory):
    relative = path.relative_to(directory)
    if SOURCE_DIRS.intersection(relative.parts):
        return not ({'.git', 'build', '__pycache__', '.venv', 'node_modules'}.intersection(relative.parts)
                    or path.suffix in INTERMEDIATE)
    if path.suffix in EVIDENCE or path.name in {'Makefile', '.gitignore', '.gitattributes', '.rgbds-version'}:
        return True
    if path.name.endswith('.tar.gz'):
        return True
    return path.suffix == '.log' and ('campaign-logs' in relative.parts or
             path.name.endswith('-run.log') or path.name == 'build.log')


def fixtures():
    result = set()
    reference = BUILD / 'dex-moves-search-final-review-20261011'
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'moves-mode-manifest.json'):
        result.add(reference / name)
    source = Path(json.loads((reference / 'moves-mode-manifest.json').read_text())['sort_memory_source'])
    manifest = source / 'moves-mode-manifest.json'
    result.add(manifest)
    stem = json.loads(manifest.read_text())['stem']
    result.add(source / 'battle-review' / (stem + '.sav'))
    unown = BUILD / 'dex-unown-black-20261011/unown-manifest.json'
    result.add(unown)
    data = json.loads(unown.read_text())
    for key in ('base', 'original_defect_base', 'background_defect_base'):
        parent = Path(data[key])
        config_path = parent / 'dex-regression/modern/config.json'
        result.add(config_path)
        config = json.loads(config_path.read_text())
        result.update(Path(config[k]) for k in ('rom', 'sym', 'battery', 'core'))
        result.update(p for p in paths(parent / 'candidate') if keep(p, parent))
        # Negative visual controls consume converted graphics sidecars as well
        # as ROM bytes. Keep their live graphics, not only rebuildable sources.
        result.update(paths(parent / 'candidate/gfx'))
    for path in result:
        if not path.is_file() or not path.resolve().is_relative_to(BUILD):
            raise ValueError('Missing/unsafe retained fixture: ' + str(path))
    return result


def verify(target, records):
    pending = {r['path']: r for r in records}
    with tarfile.open(target, 'r|gz') as saved:
        for member in saved:
            row = pending.pop(member.name)
            assert member.isfile() and member.size == row['bytes']
            h = hashlib.sha256()
            stream = saved.extractfile(member)
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
            assert h.hexdigest() == row['sha256'], member.name
    assert not pending


def compact(directory, retained):
    target = DEST / (directory.name + '.tar.gz')
    manifest_path = DEST / (directory.name + '.json.gz')
    if manifest_path.exists():
        with gzip.open(manifest_path, 'rt') as stream:
            data = json.load(stream)
        assert digest(target) == data['archive_sha256']
        assert inventory(directory) == data['original'], directory
        return data
    before = inventory(directory)
    records = []
    temporary = target.with_suffix('.partial')
    with tarfile.open(temporary, 'w:gz', compresslevel=6) as saved:
        for path in paths(directory):
            if not keep(path, directory) and path not in retained:
                continue
            relative = path.relative_to(BUILD).as_posix()
            records.append(dict(path=relative, bytes=path.stat().st_size, sha256=digest(path)))
            saved.add(path, arcname=relative, recursive=False)
    assert inventory(directory) == before, 'Build changed while archiving: ' + str(directory)
    verify(temporary, records)
    temporary.rename(target)
    data = dict(family=directory.name, original=before, archive=target.name,
                archive_sha256=digest(target), archive_bytes=target.stat().st_size,
                verified=True, files=records)
    with gzip.open(manifest_path, 'wt', compresslevel=6) as stream:
        json.dump(data, stream)
    print(json.dumps({k: v for k, v in data.items() if k != 'files'}), flush=True)
    return data


def run(apply, jobs):
    selected = list(eligible())
    retained = fixtures()
    if not apply:
        values = [(d.name, inventory(d)) for d in selected]
        print(json.dumps(dict(families=values, bytes=sum(v['bytes'] for _, v in values),
                              retained_fixture_files=len(retained), apply=False), indent=2))
        return
    acceptance = json.loads((CURRENT / 'runtime-regression/full-regression.json').read_text())
    assert acceptance['merge_ready'] and not acceptance['issues'], 'Integration regression must pass first'
    assert digest(ROOT / 'pokecrystal.gbc') == acceptance['rom_sha256']
    DEST.mkdir(parents=True, exist_ok=True)
    before = int(subprocess.check_output(['du', '-sk', str(BUILD)]).split()[0]) * 1024
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        archived = list(pool.map(lambda d: compact(d, retained), selected))
    # Every archive is verified before deleting even the first build family.
    for data in archived:
        directory = BUILD / data['family']
        assert directory.parent == BUILD and not directory.is_symlink()
        assert inventory(directory) == data['original'], directory
    preserve = set(retained)
    for path in paths(CURRENT):
        relative = path.relative_to(CURRENT)
        if (path.name in {'full-regression.json', 'phase-results.json', 'campaign-manifest.json',
                          'integration-summary.json', 'report.json', 'summary.json'}
                or relative.parts[0] == 'runtime' and path.parent == CURRENT / 'runtime'
                or path.suffix == '.png' and not SOURCE_DIRS.intersection(relative.parts)):
            preserve.add(path)
    for data in archived:
        directory = BUILD / data['family']
        members = {r['path'] for r in data['files']}
        needed = {p.relative_to(BUILD).as_posix() for p in preserve if p.is_relative_to(directory)}
        assert needed <= members, 'Retained path omitted from verified archive'
        shutil.rmtree(directory)
        if needed:
            with tarfile.open(DEST / data['archive'], 'r|gz') as saved:
                for member in saved:
                    if member.name in needed:
                        saved.extract(member, BUILD, filter='data')
        print('Cleaned ' + data['family'], flush=True)
    assert all(path.is_file() for path in preserve)
    assert digest(ROOT / 'pokecrystal.gbc') == acceptance['rom_sha256']
    after = int(subprocess.check_output(['du', '-sk', str(BUILD)]).split()[0]) * 1024
    archive_bytes = sum(v['archive_bytes'] for v in archived)
    record = dict(date='2026-10-12', verified=True, before_build_bytes=before,
                  after_build_bytes=after, archive_bytes=archive_bytes,
                  net_reclaimed_bytes=before-after-archive_bytes,
                  families=len(archived), production_sha256=acceptance['rom_sha256'],
                  retained_fixture_paths=sorted(str(p.relative_to(ROOT)) for p in retained),
                  policy='Compact source/reports/ROMs/batteries/screenshots retained; raw traces/PCM/states/intermediates retired')
    (DEST / 'cleanup.json').write_text(json.dumps(record, indent=2) + '\n')
    summary = {k: v for k, v in record.items() if k != 'retained_fixture_paths'}
    summary['live_fixture_files'] = len(record['retained_fixture_paths'])
    print(json.dumps(summary, indent=2), flush=True)


def verify_retained():
    record = json.loads((DEST / 'cleanup.json').read_text())
    manifests = sorted(DEST.glob('*.json.gz'))
    assert len(manifests) == record['families']
    pending = set(record['retained_fixture_paths'])
    for path in manifests:
        with gzip.open(path, 'rt') as stream:
            data = json.load(stream)
        target = DEST / data['archive']
        assert digest(target) == data['archive_sha256'], target
        verify(target, data['files'])
        for row in data['files']:
            relative = 'build/' + row['path']
            if relative in pending:
                live = ROOT / relative
                assert live.is_file() and digest(live) == row['sha256'], live
                pending.remove(relative)
    assert not pending, 'Live fixture absent from archive manifests'
    print(json.dumps(dict(verified_archives=len(manifests),
                         live_fixtures=len(record['retained_fixture_paths']),
                         current_rom_matches_cleanup=digest(ROOT / 'pokecrystal.gbc') == record['production_sha256'])))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--apply', action='store_true')
    cli.add_argument('--jobs', type=int, default=4)
    cli.add_argument('--verify', action='store_true')
    args = cli.parse_args()
    if args.verify and args.apply:
        cli.error('Choose verification or cleanup, not both')
    if args.verify:
        verify_retained()
    else:
        run(args.apply, args.jobs)
