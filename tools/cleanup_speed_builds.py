"""Verify lossless historical archives before removing loose speed-trial outputs.

Only the explicitly listed ignored build families are eligible. Current source
snapshots, review files, aggregate reports and videos stay at their original
paths. This does not touch production or the retained Thunderbolt research.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import stat
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
DEST = BUILD / 'retained-history-20261005'
FAMILIES = (
    'dex-performance-20261003', 'dex-performance-20261004',
    'global-speed-20261004', 'global-animation-timing-20261004',
    'battle-pacing-20261004', 'battle-motion-reference-20261004',
    'battle-normal-speed-20261004', 'polished-battle-comparison-20261004',
    'thunderbolt-comparison-20261004',
)
KEEP_TREES = (
    'battle-normal-speed-20261004/prototype',
    'battle-normal-speed-20261004/manual-review',
    'battle-normal-speed-20261004/registration',
    'global-speed-20261004/final/candidate',
)
REPORTS = {
    'report.json', 'summary.json', 'comparison.json', 'measurements.json',
    'archive.json', 'manifest.json', 'provenance.json', 'qualification.json',
    'custom-menus.json', 'resources.json', 'move-timings.csv', 'videos.json',
    'inventory-palette-audit.json', 'animation-review.json',
}


def keep(path):
    if path.name == '.DS_Store':
        return True
    relative = path.relative_to(BUILD).as_posix()
    if any(relative == tree or relative.startswith(tree + '/') for tree in KEEP_TREES):
        return True
    if path.suffix in ('.mp4', '.mkv'):
        return True
    parts = path.relative_to(BUILD).parts
    if 'candidate' in parts or 'source' in parts:
        return False
    if 'visuals' in parts and path.suffix in ('.png', '.json', '.txt'):
        return True
    if path.name in REPORTS and path.stat().st_size <= 8 * 1024**2:
        return True
    if len(parts) <= 3 and path.suffix in ('.gbc', '.sym', '.map', '.json', '.csv', '.md', '.py', '.sh'):
        return True
    return False


def files(directory):
    for base, dirs, names in os.walk(directory, followlinks=False):
        for name in dirs[:]:
            path = Path(base) / name
            if path.is_symlink():
                dirs.remove(name)
                yield path
        for name in names:
            yield Path(base) / name


def digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


class HashReader:
    def __init__(self, stream):
        self.stream = stream
        self.hash = hashlib.sha256()

    def read(self, length):
        block = self.stream.read(length)
        self.hash.update(block)
        return block


def verify(target, records):
    expected = {record['path']: record for record in records}
    count = 0
    with tarfile.open(target, 'r|gz') as archive:
        for member in archive:
            record = expected.pop(member.name)
            if member.issym():
                assert member.linkname == record['link'], member.name
            else:
                assert member.isfile() and member.size == record['bytes'], member.name
                with archive.extractfile(member) as stream:
                    assert digest(stream) == record['sha256'], member.name
            count += 1
    assert not expected, 'Missing archived files'
    return count


def archive_family(item):
    name, paths = item
    target = DEST / (name + '.tar.gz')
    manifest = DEST / (name + '.json')
    if target.exists() or manifest.exists():
        raise FileExistsError('Refusing to overwrite historical archive: ' + name)
    temporary = target.with_suffix('.partial')
    records = []
    with tarfile.open(temporary, 'w:gz', compresslevel=6, dereference=False) as archive:
        for path in paths:
            before = path.lstat()
            relative = path.relative_to(ROOT).as_posix()
            record = dict(path=relative, bytes=before.st_size,
                          mtime_ns=before.st_mtime_ns, inode=before.st_ino)
            info = archive.gettarinfo(str(path), arcname=relative)
            if stat.S_ISLNK(before.st_mode):
                record['link'] = os.readlink(path)
                archive.addfile(info)
            elif stat.S_ISREG(before.st_mode):
                with path.open('rb') as stream:
                    reader = HashReader(stream)
                    archive.addfile(info, reader)
                    record['sha256'] = reader.hash.hexdigest()
            else:
                raise ValueError('Unsupported generated output: ' + str(path))
            after = path.lstat()
            assert (after.st_size, after.st_mtime_ns, after.st_ino) == (
                before.st_size, before.st_mtime_ns, before.st_ino), path
            records.append(record)
    verify(temporary, records)
    temporary.rename(target)
    with target.open('rb') as stream:
        archive_hash = digest(stream)
    data = dict(family=name, verified=True, archive=target.name,
                archive_sha256=archive_hash, archive_bytes=target.stat().st_size,
                original_bytes=sum(record['bytes'] for record in records), files=records)
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Verified {name}: {len(records):,} files, '
          f'{data["original_bytes"] / 1024**3:.2f} -> {data["archive_bytes"] / 1024**3:.2f} GiB', flush=True)
    return data


def verified_family(name):
    data = json.loads((DEST / (name + '.json')).read_text())
    assert data['family'] == name and data['verified'], name
    target = DEST / data['archive']
    assert target.parent == DEST and not target.is_symlink(), target
    with target.open('rb') as stream:
        assert digest(stream) == data['archive_sha256'], target
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--finish', action='store_true',
                        help='Resume removal using already verified archives and unchanged archive hashes')
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    if args.apply and args.finish:
        parser.error('Choose --apply or --finish, not both')
    if (args.apply or args.finish) and (DEST / 'compact/cleanup.json').exists():
        parser.error('This first-pass archive was superseded by compact_build_evidence.py; '
                     'use its --verify option instead of recreating retired history')
    selections, retained = [], []
    for name in FAMILIES:
        directory = BUILD / name
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise ValueError('Build family must not be a symlink: ' + name)
        remove = []
        for path in files(directory):
            (retained if not path.is_symlink() and keep(path) else remove).append(path)
        selections.append((name, sorted(remove)))
    selected_bytes = sum(path.lstat().st_size for _, paths in selections for path in paths)
    print(json.dumps(dict(eligible_files=sum(len(paths) for _, paths in selections),
                          eligible_gib=selected_bytes / 1024**3,
                          retained_files=len(retained), apply=args.apply,
                          finish=args.finish), indent=2), flush=True)
    if not (args.apply or args.finish):
        return
    DEST.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        if args.finish:
            records = list(pool.map(verified_family, FAMILIES))
        else:
            records = list(pool.map(archive_family, selections))
    # No loose file is removed until every family has a verified archive.
    removed, changed_metadata = 0, []
    checked_parents = set()
    for data in records:
        for record in data['files']:
            path = ROOT / record['path']
            assert BUILD in path.parents, path
            if path.parent not in checked_parents:
                assert path.parent.resolve().is_relative_to(BUILD), path
                checked_parents.add(path.parent)
            if args.finish and not os.path.lexists(path):
                removed += record['bytes']
                continue
            current = path.lstat()
            if path.name == '.DS_Store' and (current.st_size, current.st_mtime_ns, current.st_ino) != (
                    record['bytes'], record['mtime_ns'], record['inode']):
                changed_metadata.append(record['path'])
                continue
            assert (current.st_size, current.st_mtime_ns, current.st_ino) == (
                record['bytes'], record['mtime_ns'], record['inode']), path
            path.unlink()
            removed += record['bytes']
    for name in FAMILIES:
        directory = BUILD / name
        for base, _, _ in os.walk(directory, topdown=False, followlinks=False):
            try:
                Path(base).rmdir()
            except OSError:
                pass
    archive_bytes = sum(data['archive_bytes'] for data in records)
    result = dict(date='2026-10-05', families=[{key: value for key, value in data.items()
                  if key != 'files'} for data in records], removed_bytes=removed,
                  archive_bytes=archive_bytes, net_reclaimed_gib=(removed - archive_bytes) / 1024**3,
                  preserved_changed_finder_metadata=changed_metadata,
                  retained_paths=[str(path.relative_to(ROOT)) for path in retained
                                  if os.path.lexists(path)])
    (DEST / 'cleanup.json').write_text(json.dumps(result, indent=2) + '\n')
    (DEST / 'README.md').write_text(
        '# Speed Investigation Archive\n\nVerified 2026-10-05 before removing loose outputs.\n\n'
        'Each family `.tar.gz` retains its former relative `build/` paths. Each matching\n'
        'JSON manifest contains member hashes and the archive hash. Aggregate reports,\n'
        'videos, current review files and accepted source snapshots remain directly usable.\n'
        'The root `research_artifacts/thunderbolt-comparison-20261004/` was not touched.\n\n'
        'Rebuild recipes remain under `tools/`; older snapshot/input paths are recoverable\n'
        'from these local archives. Inspect with `tar -tzf ARCHIVE`; extract into a fresh\n'
        'scratch directory, not over the current build or working checkout. Resume an interrupted\n'
        'removal with `python3 tools/cleanup_speed_builds.py --finish`; archive hashes are checked\n'
        'again and changed Finder metadata is preserved. This is a local\n'
        'archive, not a GitHub backup. `cleanup.json` records disk reclamation and retained files.\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('families', 'retained_paths')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
