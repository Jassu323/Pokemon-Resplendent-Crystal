"""Freeze production and build the private Selected runtime-display trial."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import read_symbols, sha256
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-selected-runtime'
DONOR = ROOT / 'build/dex-unown-fast-20261012-v5/pokecrystal-dex-unown-fast.sav'


def prepare(output):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private build directory')
    changes = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT).decode().splitlines()
    if any(not name.startswith(('tools/', 'docs/')) for name in changes):
        raise ValueError('Production game sources must be clean')
    output.mkdir(parents=True)
    protected = {str(ROOT / f'pokecrystal.{ext}'): sha256((ROOT / f'pokecrystal.{ext}').read_bytes())
                 for ext in ('gbc', 'sym', 'map')}
    archive = output / 'rollback-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    candidate = output / 'candidate'
    with tarfile.open(archive) as source:
        source.extractall(candidate, filter='data')
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    rollback = output / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    manifest = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                    protected_inputs=protected, stem=STEM, scope='Selected Description/Info/Moves; Area unchanged')
    (output / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def finish(output, jobs, apply=True):
    candidate = output / 'candidate'
    if apply:
        patch = ROOT / 'tools/dex_timing/probes/selected_runtime.diff'
        subprocess.run(['patch', '-p1', '--input', str(patch)], cwd=candidate, check=True)
        for path in (ROOT / 'tools/dex_timing/probes/selected_runtime').glob('*.asm'):
            shutil.copy2(path, candidate / 'engine/pokedex' / path.name)
    shutil.copy2(ROOT / 'tools/pokedex_runtime_display_assets.py', candidate / 'tools/pokedex_runtime_display_assets.py')
    shutil.copy2(ROOT / 'tools/pokedex_moves_assets.py', candidate / 'tools/pokedex_moves_assets.py')
    subprocess.run(['python3', str(ROOT / 'tools/pokedex_runtime_display_assets.py'), '--root', str(candidate)],
                   cwd=ROOT, check=True)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for stem in (STEM, 'pokecrystal-dex-types'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'{stem}.{ext}')
        shutil.copy2(DONOR, output / f'{stem}.sav')
    manifest = json.loads((output / 'runtime-manifest.json').read_text())
    for path, digest in manifest['protected_inputs'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    old, new = read_symbols(ROOT / 'pokecrystal.sym'), read_symbols(candidate / 'pokecrystal.sym')
    manifest.update(rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                    delta={name: resources(candidate / 'pokecrystal.map')[name] - value
                           for name, value in resources(ROOT / 'pokecrystal.map').items()},
                    changed_ram_labels=[name for name, pair in old.items() if name.startswith(('s','w','h'))
                                        and pair[1] >= 0xa000 and name in new and pair != new[name]],
                    production_unchanged=True)
    (output / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--finish-edited', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.finish_edited:
        finish(output, args.jobs, False)
    else:
        prepare(output)
        if not args.prepare_only:
            finish(output, args.jobs)
