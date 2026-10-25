"""Freeze committed production and build an isolated static Unown prototype."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import sha256, read_symbols
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-unown-fast'
REVIEW = ROOT / 'build/dex-moves-search-final-review-20261011'
DONOR = ROOT / 'build/dex-types-production-runtime-20261012/runtime/pokecrystal-dex-types.sav'


def build(output, jobs):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private build directory')
    changes = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT).decode().splitlines()
    if any(not name.startswith(('tools/', 'docs/')) for name in changes):
        raise ValueError('Production must have no tracked modifications')
    protected = {str(ROOT / f'pokecrystal.{ext}'): sha256((ROOT / f'pokecrystal.{ext}').read_bytes())
                 for ext in ('gbc', 'sym', 'map')}
    output.mkdir(parents=True)
    archive = output / 'rollback-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    candidate = output / 'candidate'
    with tarfile.open(archive) as source:
        source.extractall(candidate, filter='data')
    # Visual/linked host oracles also require current converted graphics/tables.
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    rollback = output / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    probes = ROOT / 'tools/dex_timing/probes'
    subprocess.run(['patch', '-p1', '--input', str(probes / 'unown_fast.diff')], cwd=candidate, check=True)
    shutil.copy2(probes / 'unown_fast.asm', candidate / 'engine/pokedex/pokedex_unown_static.asm')
    shutil.copy2(probes / 'unown_decode.asm', candidate / 'engine/pokedex/pokedex_unown_decode.asm')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for stem in (STEM, 'pokecrystal-dex-types', 'pokecrystal-dex-unown-fix',
                 'pokecrystal-dex-moves-search', 'pokecrystal-dex-moves-mode'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'{stem}.{ext}')
        shutil.copy2(DONOR, output / f'{stem}.sav')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'moves-mode-manifest.json'):
        shutil.copy2(REVIEW / name, output / name)
    old = read_symbols(ROOT / 'pokecrystal.sym')
    new = read_symbols(candidate / 'pokecrystal.sym')
    moved = [name for name, pair in old.items() if pair[1] >= 0xa000
             and name.startswith(('s', 'w', 'h')) and name in new and pair != new[name]]
    if moved:
        raise AssertionError(f'RAM addresses moved: {moved}')
    delta = {name: resources(candidate / 'pokecrystal.map')[name] - value
             for name, value in resources(ROOT / 'pokecrystal.map').items()}
    for path, digest in protected.items():
        assert sha256(Path(path).read_bytes()) == digest, path
    result = dict(stem=STEM, head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                  rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                  rollback_rom_sha256=protected[str(ROOT / 'pokecrystal.gbc')], delta=delta,
                  protected_inputs=protected, new_artwork=False, memory_addresses_unchanged=True,
                  red_background=True, black_panels=True, production_unchanged=True)
    (output / 'unown-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs)
