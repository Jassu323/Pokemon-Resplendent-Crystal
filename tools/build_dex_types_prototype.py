"""Prepare and publish the isolated Type Matchups review build."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import difflib

ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-types'
OUTPUT = ROOT / 'build/dex-types-cursors-20261011'
PATCH = ROOT / 'tools/dex_timing/probes/type_matchups_mode.patch'
SOURCE_FILES = ('engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm',
                'main.asm', 'home/lcd.asm', 'home/vblank.asm',
                'data/types/type_matchups.asm', 'engine/pokedex/pokedex_types.asm',
                'engine/pokedex/pokedex_popover.asm', 'engine/pokedex/pokedex_moves_mode.asm',
                'engine/pokedex/pokedex_3.asm')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private build directory')
    output.mkdir(parents=True)
    rollback = output / 'rollback'
    rollback.mkdir()
    protected = {}
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in paths:
        path = ROOT / name
        if name and path.is_file():
            protected[name] = digest(path)
    for suffix in ('gbc', 'sym', 'map'):
        path = ROOT / f'pokecrystal.{suffix}'
        protected[path.name] = digest(path)
        shutil.copy2(path, rollback / path.name)
    archive = output / 'rollback-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    candidate = output / 'candidate'
    with tarfile.open(archive) as source:
        source.extractall(candidate, filter='data')
    # Existing converted art is copied unchanged; no new image assets are made.
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    if PATCH.exists():
        subprocess.run(['patch','--batch','-p1','-i',str(PATCH)],cwd=candidate,check=True)
    source_save = ROOT / 'build/dex-unown-black-20261011/all-unown-review/pokecrystal-dex-unown-fix.sav'
    shutil.copy2(source_save, output / f'{STEM}.sav')
    protected[str(source_save)] = digest(source_save)
    manifest = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                    production_sha256=protected['pokecrystal.gbc'], protected_inputs=protected,
                    save_sha256=digest(output / f'{STEM}.sav'), new_artwork=False)
    (output / 'types-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(candidate)


def capture_patch(output):
    changes = []
    with tarfile.open(output / 'rollback-source.tar') as original:
        for name in SOURCE_FILES:
            try:
                before = original.extractfile(name).read().decode().splitlines(keepends=True)
                old_name = 'a/' + name
            except KeyError:
                before,old_name = [],'/dev/null'
            after = (output / 'candidate' / name).read_text().splitlines(keepends=True)
            changes.extend(difflib.unified_diff(before,after,fromfile=old_name,tofile='b/'+name))
    PATCH.write_text(''.join(changes))
    print(PATCH)


def build(output, jobs):
    manifest = json.loads((output / 'types-manifest.json').read_text())
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=output / 'candidate',
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(output / 'candidate' / f'pokecrystal.{suffix}', output / f'{STEM}.{suffix}')
    outside_game_changes = []
    for name, expected in manifest['protected_inputs'].items():
        path = Path(name) if name.startswith('/') else ROOT / name
        if not path.is_file() or digest(path) != expected:
            if name.startswith('docs/') or name in ('.gitignore','tools/dex_timing/probes/cold_listing.c',
                    'tools/dex_timing/listing_options.py','tools/dex_timing/moves_mode.py'):
                outside_game_changes.append(name)
                continue
            raise AssertionError(f'Protected input changed: {name}')
    manifest.update(rom_sha256=digest(output / f'{STEM}.gbc'), production_unchanged=True,
                    outside_game_changes=outside_game_changes)
    (output / 'types-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'protected_inputs'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'build','capture-patch'])
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    output = args.output.resolve()
    if args.action == 'prepare':
        prepare(output)
    elif args.action == 'capture-patch':
        capture_patch(output)
    else:
        build(output,args.jobs)
