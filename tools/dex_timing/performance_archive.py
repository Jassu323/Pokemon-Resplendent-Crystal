"""Losslessly compress this investigation's large generated listening/log files.

Never walks outside build/, follows symlinks, or removes the only verified copy.
Small build logs, states, ROMs, reports and representative WAVs remain untouched.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
from pathlib import Path
import shutil

from .cold_listing import ROOT


def digest(path, compressed=False):
    opener = gzip.open if compressed else open
    value = hashlib.sha256()
    with opener(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def compress(path):
    before = path.stat().st_size
    target = path.with_suffix(path.suffix + '.gz')
    expected = digest(path)
    with path.open('rb') as source, gzip.open(target, 'wb', compresslevel=6) as out:
        shutil.copyfileobj(source, out, 1024 * 1024)
    if digest(target, True) != expected or digest(path) != expected:
        raise RuntimeError(f'Archive verification failed: {path}')
    after = target.stat().st_size
    path.unlink()
    return before - after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if ROOT / 'build' not in directory.parents:
        parser.error('Choose an investigation directory inside build/')
    paths = []
    for path in directory.rglob('*'):
        if not path.is_file() or path.is_symlink() or directory not in path.resolve().parents:
            continue
        if path.suffix not in ('.wav', '.log', '.jsonl') or path.stat().st_size < 200_000:
            continue
        if path.suffix == '.wav' and ('listening' in path.parts or 'lifecycle' in path.parts or
            ('dusknoir' in str(path) and any(arm in str(path) for arm in ('baseline-q0/', 'candidate-post-dex-q0/')))):
            continue
        if path.with_suffix(path.suffix + '.gz').exists():
            continue
        paths.append(path)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reclaimed = sum(pool.map(compress, paths))
    print(f'Verified lossless archives: {len(paths)}; reclaimed {reclaimed / 1024**3:.2f} GiB')


if __name__ == '__main__':
    main()
