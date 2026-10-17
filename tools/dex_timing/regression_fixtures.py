"""Restore only durable regression inputs, never historical run outputs."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

from .cold_listing import ROOT

BUNDLE = ROOT / 'tools/regression_fixtures/dex'
NUMERIC_REFERENCE = Path('build/interactive-registration-fixed-full-20261016/baseline-source')
MOVES_REFERENCE = Path('build/dex-moves-search-final-review-20261011')
KEYBOARD_CONTROL = Path('build/dex-moves-search-keyboard-20261010')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or len(path.parts) < 2 or path.parts[0] != 'build':
        raise ValueError('Fixture destination must be inside build/: ' + name)
    return Path(*path.parts)


def map_paths(value, root):
    if isinstance(value, str):
        return str(root) + value[len('@ROOT@'):] if value.startswith('@ROOT@/') else value
    if isinstance(value, list):
        return [map_paths(item, root) for item in value]
    if isinstance(value, dict):
        return {map_paths(key, root): map_paths(item, root) for key, item in value.items()}
    return value


def payload(bundle=BUNDLE):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    archive = bundle / 'inputs.tar.xz'
    if digest(archive.read_bytes()) != manifest['archive_sha256']:
        raise ValueError('Regression fixture archive checksum differs')
    expected = {row['path']: row for row in manifest['files']}
    if len(expected) != len(manifest['files']):
        raise ValueError('Duplicate fixture paths')
    result = []
    with tarfile.open(archive, 'r:xz') as source:
        for member in source:
            safe_path(member.name)
            row = expected.pop(member.name, None)
            if row is None or not member.isfile() or member.size != row['bytes']:
                raise ValueError('Unexpected fixture archive member: ' + member.name)
            data = source.extractfile(member).read()
            if digest(data) != row['sha256']:
                raise ValueError('Fixture member checksum differs: ' + member.name)
            result.append((row, data))
    if expected:
        raise ValueError('Missing fixture archive members')
    return manifest, result


def restore(root=ROOT, bundle=BUNDLE):
    root = Path(root).resolve()
    if root != ROOT and not root.is_relative_to(ROOT / 'build'):
        raise ValueError('Restore only into this checkout or a private build/ directory')
    manifest, records = payload(bundle)
    build = root / 'build'
    if build.is_symlink():
        raise ValueError('Refusing a symlinked fixture destination: ' + str(build))
    build.mkdir(parents=True, exist_ok=True)
    lock_path = build / '.regression-fixture-restore.lock'
    if lock_path.is_symlink():
        raise ValueError('Refusing a symlinked restore lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return restore_records(root, manifest, records)


def restore_records(root, manifest, records):
    pending = []
    for row, data in records:
        target = root / safe_path(row['path'])
        # Do not follow a legacy directory alias into another checkout.
        if any(parent.is_symlink() for parent in (target, *target.parents) if parent != root):
            raise ValueError('Refusing a symlinked fixture destination: ' + str(target))
        if row.get('portable_json'):
            data = (json.dumps(map_paths(json.loads(data), root), indent=2) + '\n').encode()
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError('Existing fixture differs; preserve it before restoring: ' + str(target))
        else:
            pending.append((target, data))
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    return dict(files=len(records), restored=len(pending), archive_bytes=manifest['archive_bytes'])


def require(relative):
    target = ROOT / safe_path(str(relative))
    if not target.exists():
        restore()
    return target


def numeric_reference():
    require(NUMERIC_REFERENCE / 'pokecrystal.gbc')
    require(NUMERIC_REFERENCE / 'pokecrystal.sym')
    return ROOT / NUMERIC_REFERENCE


def native_controls(root=ROOT, keyboard=True):
    """Compile observers from maintained tools, not archived machine binaries."""
    from .assets import Repository
    from .performance import core
    root = Path(root).resolve()
    manifest = json.loads((root / 'build/dex-unown-black-20261011/unown-manifest.json').read_text())
    paths = {Path(manifest[key]) for key in ('base', 'original_defect_base', 'background_defect_base')}
    for path in sorted(paths):
        config_path = path / 'dex-regression/modern/config.json'
        config = json.loads(config_path.read_text())
        executable = Path(config['core'])
        if not executable.is_file():
            repo = Repository(path / 'candidate', config['rom'], config['sym'])
            actual = core(repo, executable.parent)
            if actual != executable:
                raise ValueError('Unexpected native observer destination')
    if keyboard:
        from .moves_search import prepare
        path = root / KEYBOARD_CONTROL
        if not (path / 'search-tests/config.json').is_file():
            prepare(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'restore'))
    parser.add_argument('--destination', type=Path, default=ROOT)
    parser.add_argument('--compile-controls', action='store_true')
    args = parser.parse_args()
    if args.action == 'verify':
        manifest, records = payload()
        result = dict(verified=True, files=len(records), archive_bytes=manifest['archive_bytes'])
    else:
        result = restore(args.destination)
        if args.compile_controls:
            native_controls(args.destination)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
