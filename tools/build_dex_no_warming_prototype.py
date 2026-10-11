"""Build a private, committed-production comparison without Listing warming."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import read_symbols, sha256


ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-no-warming'
REVIEW = ROOT / 'build/dex-moves-search-final-review-20261011'
OWNERS = ('engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm',
          'engine/pokedex/pokedex_animation.asm', 'engine/pokedex/pokedex_popover.asm')


def publish(source, target):
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(source / f'pokecrystal.{suffix}', target / f'{STEM}.{suffix}')
        # Existing qualification modules use these stable trial basenames.
        for name in ('pokecrystal-dex-moves-search', 'pokecrystal-dex-moves-mode'):
            shutil.copy2(source / f'pokecrystal.{suffix}', target / f'{name}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json'):
        shutil.copy2(REVIEW / name, target / name)
    shutil.copy2(REVIEW / 'pokecrystal-dex-moves-search.sav', target / f'{STEM}.sav')
    shutil.copy2(REVIEW / 'pokecrystal-dex-moves-search.sav',
                 target / 'pokecrystal-dex-moves-search.sav')
    # These manifests supply reviewed fixture definitions, not old protection claims.
    shutil.copy2(REVIEW / 'moves-mode-manifest.json', target / 'moves-mode-manifest.json')
    review = target / 'all-seen-review'
    review.mkdir(exist_ok=True)
    shutil.copy2(source / 'pokecrystal.gbc', review / f'{STEM}.gbc')
    shutil.copy2(REVIEW / 'all-seen-review/pokecrystal-dex-moves-search.sav', review / f'{STEM}.sav')


def build(output, jobs):
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh private build directory')
    if subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT).strip():
        raise ValueError('Build from committed production, with no tracked source changes')
    production = {name: sha256((ROOT / name).read_bytes()) for name in
                  ('pokecrystal.gbc', 'pokecrystal.sym', 'pokecrystal.map')}
    output.mkdir(parents=True)
    baseline = output / 'baseline'
    baseline.mkdir()
    archive = output / 'committed-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    with tarfile.open(archive) as source:
        source.extractall(baseline / 'candidate', filter='data')
    with (baseline / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=baseline / 'candidate',
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    if sha256((baseline / 'candidate/pokecrystal.gbc').read_bytes()) != production['pokecrystal.gbc']:
        raise AssertionError('Fresh committed baseline differs from production ROM')
    publish(baseline / 'candidate', baseline)
    candidate = output / 'candidate'
    shutil.copytree(baseline / 'candidate', candidate)
    removed = {}
    for name in OWNERS[:3]:
        path = candidate / name
        text = path.read_text()
        call = '\tcall Pokedex_StartAnimationPrefetch\n' if name == OWNERS[2] else '\tfarcall Pokedex_StartAnimationPrefetch\n'
        if text.count(call) != 2:
            raise AssertionError(f'Listing startup call count changed: {name}')
        text = text.replace(call, '')
        removed[name] = {'startup_calls': 2}
        if name != OWNERS[2]:
            idle = '\tfarcall Pokedex_ServiceAnimationProducer\n'
            if text.count(idle) != 1:
                raise AssertionError(f'Listing idle call count changed: {name}')
            text = text.replace(idle, '')
            removed[name]['idle_calls'] = 1
        path.write_text(text)
    path = candidate / OWNERS[3]
    text = path.read_text()
    wrapper = '    ldh a, [rSVBK]\n    push af\n    ld a, BANK(wPokedexSeen)\n    ldh [rSVBK], a\n    farcall Pokedex_StartAnimationPrefetch\n    pop af\n    ldh [rSVBK], a\n'
    if text.count(wrapper) != 1:
        raise AssertionError('Popup-only warming bank wrapper changed')
    path.write_text(text.replace(wrapper, ''))
    removed[OWNERS[3]] = {'startup_calls': 1, 'bank_wrapper_removed': True}
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    publish(candidate, output)
    before = read_symbols(baseline / f'{STEM}.sym')
    after = read_symbols(output / f'{STEM}.sym')
    for name, pair in before.items():
        if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in after:
            if pair != after[name]:
                raise AssertionError(f'Memory address moved: {name}')
    for name, expected in production.items():
        if sha256((ROOT / name).read_bytes()) != expected:
            raise AssertionError(f'Production output changed: {name}')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    protected = {str(ROOT / name): sha256((ROOT / name).read_bytes())
                 for name in tracked if name and (ROOT / name).is_file()}
    protected.update({str(ROOT / name): value for name, value in production.items()})
    manifest = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                    baseline_rom_sha256=production['pokecrystal.gbc'],
                    rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                    removed=removed, protected_inputs=protected,
                    compiled_source_changes=list(OWNERS), memory_addresses_unchanged=True,
                    new_artwork=False, production_unchanged=True)
    (output / 'no-warming-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'protected_inputs'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    build(args.output, args.jobs)
