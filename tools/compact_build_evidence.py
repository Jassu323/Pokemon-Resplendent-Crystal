"""Compact approved speed-trial history and losslessly archive current evidence.

Superseded per-test traces/frames/audio are deliberately retired. Source,
reports, ROMs, saves/states and review media survive with verified hashes.
Current production qualification is lossless. Thunderbolt research is excluded.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile

from cleanup_speed_builds import FAMILIES, HashReader, digest, files

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
HISTORY = BUILD / 'retained-history-20261005'
DEST = HISTORY / 'compact'
CURRENT = 'production-speed-integration-20261005'
OLD = tuple(name for name in FAMILIES if name != 'thunderbolt-comparison-20261004')
ROM_EXTENSIONS = {'.gbc', '.gba', '.sym', '.map', '.elf', '.sav', '.s0', '.state', '.ips'}
SOURCE_EXTENSIONS = {'.asm', '.py', '.c', '.h', '.cpp', '.cc', '.m', '.mm', '.sh',
                     '.md', '.txt', '.toml', '.ini', '.link', '.pal', '.patch', '.diff', '.mk'}
MEDIA_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.png', '.gif'}
SOURCE_DIRS = {'candidate', 'source', 'host-source', 'source-snapshots', 'inputs'}
GENERATED_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', 'build'}
GENERATED_EXTENSIONS = {'.o', '.pyc', '.lz', '.1bpp', '.2bpp', '.gbcpal', '.d',
                        '.ppm', '.jsonl', '.wav', '.raw'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def historical_keep(name):
    path = PurePosixPath(name)
    if path.suffix in ROM_EXTENSIONS | SOURCE_EXTENSIONS | MEDIA_EXTENSIONS:
        return True
    if path.suffix == '.csv' or path.name in ('Makefile', 'makefile', '.gitignore', '.gitattributes'):
        return True
    # Individual result/reference JSON can feed historical prototype builders.
    # Keep it too, not just top-level summaries, while dropping bulk JSONL.
    if path.suffix == '.json':
        return True
    # Preserve authored binary assets in snapshots, but not their compiled
    # derivatives or nested bulk captures. Never follow archived symlinks.
    for i, part in enumerate(path.parts):
        if part in SOURCE_DIRS:
            tail = path.parts[i + 1:]
            return not (GENERATED_DIRS.intersection(tail) or
                        path.suffix in GENERATED_EXTENSIONS or
                        path.name.endswith(('.jsonl.gz', '.raw.gz', '.tar.gz', '.tar')))
    return False


def current_bulk(path):
    return (path.suffix in {'.jsonl', '.ppm', '.wav', '.raw'} or
            path.name.endswith(('.jsonl.gz', '.raw.gz')) or path.name == 'result.json')


def safe_relative(name, family):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and
            path.parts[:2] == ('build', family), 'Unsafe archive member: ' + name)


def file_hash(path):
    with path.open('rb') as stream:
        return digest(stream)


def verify_archive(path, records):
    pending = {r['path']: r for r in records}
    require(len(pending) == len(records), 'Duplicate archive members')
    with tarfile.open(path, 'r|gz') as archive:
        for member in archive:
            require(member.name in pending, 'Unexpected member: ' + member.name)
            record = pending.pop(member.name)
            if member.issym():
                require(member.linkname == record['link'], 'Changed symlink: ' + member.name)
            else:
                require(member.isfile() and member.size == record['bytes'], 'Changed size: ' + member.name)
                with archive.extractfile(member) as stream:
                    require(digest(stream) == record['sha256'], 'Changed content: ' + member.name)
    require(not pending, 'Missing archive members')


def finish_archive(family, temporary, records, extra):
    verify_archive(temporary, records)
    target = DEST / (family + '.tar.gz')
    temporary.rename(target)
    data = dict(family=family, archive=target.name, archive_bytes=target.stat().st_size,
                archive_sha256=file_hash(target), verified=True, files=records, **extra)
    (DEST / (family + '.json')).write_text(json.dumps(data, indent=2) + '\n')
    print(f'Verified {family}: {len(records):,} retained files, '
          f'{data["archive_bytes"] / 1024**3:.3f} GiB', flush=True)
    return data


def original_catalog(path):
    target = DEST / 'original-manifests' / (path.name + '.gz')
    target.parent.mkdir(exist_ok=True)
    expected = file_hash(path)
    if not target.exists():
        temporary = target.with_suffix('.partial')
        require(not temporary.exists(), 'Incomplete catalog exists: ' + str(temporary))
        with path.open('rb') as source, gzip.open(temporary, 'wb', compresslevel=6) as destination:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                destination.write(block)
        temporary.rename(target)
    with gzip.open(target, 'rb') as stream:
        require(digest(stream) == expected, 'Original catalog did not round-trip')
    return dict(path=str(target.relative_to(HISTORY)), sha256=expected)


def compact_history(family):
    catalog = HISTORY / (family + '.json')
    original = json.loads(catalog.read_text())
    source = HISTORY / original['archive']
    require(source.parent == HISTORY and not source.is_symlink(), 'Unsafe source archive')
    require(file_hash(source) == original['archive_sha256'], 'Original archive changed: ' + family)
    expected = {r['path']: r for r in original['files']}
    require(len(expected) == len(original['files']), 'Duplicate original member')
    for name in expected:
        safe_relative(name, family)
    temporary = DEST / (family + '.partial')
    require(not temporary.exists(), 'Incomplete archive exists: ' + str(temporary))
    records = []
    with tarfile.open(source, 'r|gz') as incoming, tarfile.open(temporary, 'w:gz', compresslevel=6) as outgoing:
        for member in incoming:
            require(member.name in expected, 'Unexpected original member: ' + member.name)
            record = expected.pop(member.name)
            if not historical_keep(member.name):
                continue
            if member.issym():
                require(member.linkname == record['link'], 'Changed original symlink')
                outgoing.addfile(member)
            else:
                require(member.isfile() and member.size == record['bytes'], 'Changed original size')
                with incoming.extractfile(member) as stream:
                    reader = HashReader(stream)
                    outgoing.addfile(member, reader)
                    require(reader.hash.hexdigest() == record['sha256'], 'Changed original content')
            records.append(record)
    require(not expected, 'Missing original archive members')
    return finish_archive(family, temporary, records, dict(
        policy='curated-history', former_archive=source.name,
        former_archive_bytes=source.stat().st_size,
        former_archive_sha256=original['archive_sha256'],
        original_catalog=original_catalog(catalog),
        former_members=len(original['files']), retired_members=len(original['files']) - len(records)))


def archive_current(paths):
    temporary = DEST / (CURRENT + '.partial')
    require(not temporary.exists(), 'Incomplete current archive exists')
    records = []
    with tarfile.open(temporary, 'w:gz', compresslevel=6, dereference=False) as archive:
        for path in paths:
            before = path.lstat()
            require(stat.S_ISREG(before.st_mode), 'Current evidence must be a regular file')
            name = path.relative_to(ROOT).as_posix()
            safe_relative(name, CURRENT)
            info = archive.gettarinfo(str(path), arcname=name)
            with path.open('rb') as stream:
                reader = HashReader(stream)
                archive.addfile(info, reader)
            after = path.lstat()
            require((before.st_size, before.st_mtime_ns, before.st_ino) ==
                    (after.st_size, after.st_mtime_ns, after.st_ino), 'Current file changed: ' + name)
            records.append(dict(path=name, bytes=before.st_size, mtime_ns=before.st_mtime_ns,
                                inode=before.st_ino, sha256=reader.hash.hexdigest()))
    return finish_archive(CURRENT, temporary, records, dict(policy='lossless-current',
                          original_bytes=sum(r['bytes'] for r in records)))


def existing(family):
    path = DEST / (family + '.json')
    if not path.exists():
        require(not (DEST / (family + '.tar.gz')).exists(), 'Archive has no catalog: ' + family)
        return None
    data = json.loads(path.read_text())
    target = DEST / data['archive']
    require(data['verified'] and data['family'] == family and target.parent == DEST and
            not target.is_symlink(), 'Invalid retained catalog: ' + family)
    require(file_hash(target) == data['archive_sha256'], 'Retained archive changed: ' + family)
    verify_archive(target, data['files'])
    if data['policy'] == 'curated-history':
        with gzip.open(HISTORY / data['original_catalog']['path'], 'rb') as stream:
            require(digest(stream) == data['original_catalog']['sha256'], 'Original catalog changed')
    return data


def protected_hashes():
    paths = [ROOT / ('pokecrystal' + ext) for ext in ('.gbc', '.sym', '.map')]
    for tree in (BUILD / 'battle-normal-speed-20261004/manual-review',
                 BUILD / 'battle-normal-speed-20261004/prototype',
                 ROOT / 'research_artifacts/thunderbolt-comparison-20261004'):
        paths.extend(p for p in files(tree) if p.suffix in ROM_EXTENSIONS | MEDIA_EXTENSIONS or
                     p.name in ('manifest.json', 'captures-and-replay-inputs.tar.gz'))
    return {str(p): file_hash(p) for p in paths if p.is_file() and not p.is_symlink()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--verify', action='store_true', help='Recheck retained archive members without changing files')
    parser.add_argument('--jobs', type=int, default=3)
    args = parser.parse_args()
    require(1 <= args.jobs <= 3, 'Use one to three archive workers to preserve CPU headroom')
    require(not (args.apply and args.verify), 'Choose --apply or --verify')
    if args.verify:
        require((DEST / 'cleanup.json').exists(), 'Cleanup has not completed')
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            records = list(pool.map(existing, (*OLD, CURRENT)))
        require(all(records), 'Missing retained archive catalog')
        print(json.dumps(dict(verified_families=len(records),
                              verified_members=sum(len(r['files']) for r in records))), flush=True)
        return
    require(not (args.apply and (DEST / 'cleanup.json').exists()),
            'This cleanup already completed; use --verify, not --apply')
    current = sorted(p for p in files(BUILD / CURRENT) if not p.is_symlink() and current_bulk(p))
    old_bytes = sum((HISTORY / (name + '.tar.gz')).stat().st_size for name in OLD
                    if (HISTORY / (name + '.tar.gz')).exists())
    print(json.dumps(dict(historical_archive_gib=old_bytes / 1024**3,
                          lossless_current_gib=sum(p.stat().st_size for p in current) / 1024**3,
                          current_files=len(current), apply=args.apply), indent=2), flush=True)
    if not args.apply:
        return
    before = protected_hashes()
    DEST.mkdir(exist_ok=True)
    retained, pending = [], []
    for name in (*OLD, CURRENT):
        data = existing(name)
        if data is None:
            pending.append(name)
        else:
            retained.append(data)
    def archive(name):
        return archive_current(current) if name == CURRENT else compact_history(name)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        retained.extend(pool.map(archive, pending))
    require(before == protected_hashes(), 'Protected production/review/research files changed')
    # All replacement archives and catalogs have passed round-trip verification.
    # Retire originals only when their identity still matches the recorded input.
    removed = 0
    for data in retained:
        if data['policy'] == 'curated-history':
            source = HISTORY / data['former_archive']
            if source.exists():
                require(file_hash(source) == data['former_archive_sha256'], 'Original archive changed before retirement')
                removed += source.stat().st_size
                source.unlink()
            catalog = HISTORY / (data['family'] + '.json')
            if catalog.exists():
                require(file_hash(catalog) == data['original_catalog']['sha256'], 'Original catalog changed before retirement')
                removed += catalog.stat().st_size
                catalog.unlink()
        else:
            for record in data['files']:
                safe_relative(record['path'], CURRENT)
                path = ROOT / record['path']
                if not path.exists():
                    continue
                require(path.parent.resolve().is_relative_to(BUILD / CURRENT) and not path.is_symlink(), 'Unsafe current path')
                state = path.stat()
                require((state.st_size, state.st_mtime_ns, state.st_ino) ==
                        (record['bytes'], record['mtime_ns'], record['inode']), 'Current evidence changed before removal')
                removed += state.st_size
                path.unlink()
    require(before == protected_hashes(), 'Protected content changed during retirement')
    added = sum((DEST / d['archive']).stat().st_size + (DEST / (d['family'] + '.json')).stat().st_size for d in retained)
    added += sum(p.stat().st_size for p in (DEST / 'original-manifests').glob('*.gz'))
    result = dict(removed_bytes=removed, retained_archive_bytes=added,
                  net_reclaimed_gib=(removed - added) / 1024**3,
                  protected_files=len(before), protected_hashes=before,
                  families=[{k: v for k, v in d.items() if k != 'files'} for d in retained])
    (DEST / 'cleanup.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('families', 'protected_hashes')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
