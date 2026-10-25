"""Apply the bounded Unown repair to an isolated copy of a reviewed prototype."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from dex_timing.assets import read_symbols, sha256

ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-unown-fix'
BASE_STEM = 'pokecrystal-dex-no-warming'
PATCH = ROOT / 'tools/dex_timing/probes/unown_overlay_fix.diff'
BACKGROUND_PATCH = ROOT / 'tools/dex_timing/probes/unown_background_fix.diff'
BLACK_PATCH = ROOT / 'tools/dex_timing/probes/unown_black_panels.diff'


def resources(path):
    return {name: int(value) for name, value in re.findall(
        r'^\s*(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used', path.read_text(), re.M)}


def build(base, output, jobs, red_background=False, black_panels=False):
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh private build directory')
    prior = json.loads((base / 'unown-manifest.json').read_text()) if red_background or black_panels else {}
    if black_panels and not prior.get('red_background'):
        raise ValueError('Black panels require the reviewed red-backdrop base')
    base_stem = STEM if red_background or black_panels else BASE_STEM
    patch = BLACK_PATCH if black_panels else BACKGROUND_PATCH if red_background else PATCH
    original_base = Path(prior.get('original_defect_base', str(base)))
    background_defect_base = Path(prior['base']) if black_panels else base
    protected = {str(path): sha256(path.read_bytes()) for path in (
        *(ROOT / f'pokecrystal.{suffix}' for suffix in ('gbc', 'sym', 'map')),
        *(base / f'{base_stem}.{suffix}' for suffix in ('gbc', 'sym', 'map', 'sav')))}
    output.mkdir(parents=True)
    candidate = output / 'candidate'
    shutil.copytree(base / 'candidate', candidate)
    subprocess.run(['patch', '-p1', '--input', str(patch)], cwd=candidate, check=True)
    changed = [str(path.relative_to(candidate)) for path in candidate.rglob('*.asm')
               if path.read_bytes() != (base / 'candidate' / path.relative_to(candidate)).read_bytes()]
    expected_owner = 'engine/gfx/cgb_layouts.asm' if black_panels else 'engine/pokedex/pokedex.asm'
    if changed != [expected_owner]:
        raise AssertionError(f'Unexpected game-code owners: {changed}')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for name in (STEM, 'pokecrystal-dex-moves-search', 'pokecrystal-dex-moves-mode'):
            shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'{name}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'moves-mode-manifest.json'):
        shutil.copy2(base / name, output / name)
    for name in (STEM, 'pokecrystal-dex-moves-search'):
        shutil.copy2(base / f'{base_stem}.sav', output / f'{name}.sav')
    review = output / 'all-seen-review'
    review.mkdir()
    shutil.copy2(output / f'{STEM}.gbc', review / f'{STEM}.gbc')
    shutil.copy2(base / 'all-seen-review' / f'{base_stem}.sav', review / f'{STEM}.sav')
    before = read_symbols(base / f'{base_stem}.sym')
    after = read_symbols(output / f'{STEM}.sym')
    for name, pair in before.items():
        if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in after:
            if pair != after[name]:
                raise AssertionError(f'Memory address moved: {name}')
    delta = {name: resources(output / f'{STEM}.map')[name] - value
             for name, value in resources(base / f'{base_stem}.map').items()}
    if any(value for name, value in delta.items() if name != 'ROMX'):
        raise AssertionError(f'Unexpected memory allocation: {delta}')
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected input changed: {path}')
    result = dict(base=str(base), base_stem=base_stem, red_background=red_background or black_panels,
                  black_panels=black_panels, background_defect_base=str(background_defect_base),
                  original_defect_base=str(original_base),
                  production_manifest=str(original_base / 'no-warming-manifest.json'),
                  rollback_rom_sha256=protected[str(base / f'{base_stem}.gbc')],
                  rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()), delta=delta,
                  changed_owners=changed, memory_addresses_unchanged=True,
                  protected_inputs=protected, new_artwork=False, production_unchanged=True)
    (output / 'unown-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'protected_inputs'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--red-background', action='store_true')
    parser.add_argument('--black-panels', action='store_true')
    args = parser.parse_args()
    build(args.base.resolve(), args.output.resolve(), args.jobs, args.red_background, args.black_panels)
