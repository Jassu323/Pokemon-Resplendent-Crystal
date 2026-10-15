"""Record and publish the private session-only Pokemon/Moves bookmark link."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.assets import read_symbols, sha256
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/dex-position-memory-20261014'
PRIOR = ROOT / 'build/dex-moves-position-session-20261014'
CONTROL = ROOT / 'build/dex-moves-position-20261014'
STEM = 'pokecrystal-dex-position-memory'


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare():
    if BASE.exists() or not BASE.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh output under build')
    BASE.mkdir(parents=True)
    shutil.copytree(CONTROL / 'baseline-source', BASE / 'candidate',
                    ignore=shutil.ignore_patterns('*.o', '*.d', '*.pyc', '__pycache__'))
    subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes/pokemon_position.diff')],
                   cwd=BASE / 'candidate', check=True)
    freeze()


def freeze():
    path = BASE / 'position-memory-manifest.json'
    if path.exists():
        raise ValueError('Refusing to replace the frozen manifest')
    protected = {str(p): sha256(p.read_bytes()) for p in (
        *(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')),
        *ROOT.glob('pokecrystal*.sav'), * (PRIOR / 'review').iterdir()) if p.is_file()}
    assert protected[str(ROOT / 'pokecrystal.gbc')] == sha256((CONTROL / 'rollback/pokecrystal.gbc').read_bytes())
    for name in ('baseline-source', 'rollback', 'rollback-source.tar'):
        (BASE / name).symlink_to(CONTROL / name, target_is_directory=name != 'rollback-source.tar')
    write(path, dict(protected=protected, base=str(PRIOR), baseline=str(CONTROL),
        baseline_sha256=protected[str(ROOT / 'pokecrystal.gbc')],
        prior_sha256=sha256((PRIOR / 'candidate/pokecrystal.gbc').read_bytes()),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        full_regression_passed=False, production_integrated=False))


def build(jobs):
    attempt = 1
    log_path = BASE / 'build.log'
    while log_path.exists():
        attempt += 1
        log_path = BASE / f'build-attempt-{attempt}.log'
    with log_path.open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=BASE / 'candidate',
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    path = BASE / 'position-memory-manifest.json'
    record = json.loads(path.read_text())
    old = resources(BASE / 'rollback/pokecrystal.map')
    prior = resources(PRIOR / 'candidate/pokecrystal.map')
    new = resources(BASE / 'candidate/pokecrystal.map')
    record['delta'] = {key: new[key] - old[key] for key in old}
    record['pokemon_delta'] = {key: new[key] - prior[key] for key in old}
    assert all(value == 0 for key, value in record['delta'].items() if key != 'ROMX')
    old_symbols = read_symbols(BASE / 'rollback/pokecrystal.sym')
    symbols = read_symbols(BASE / 'candidate/pokecrystal.sym')
    assert 'Pokedex_InitCursorPosition' not in symbols
    record['moved_ram_labels'] = [name for name, pair in old_symbols.items()
        if pair[1] >= 0xa000 and symbols.get(name) != pair]
    assert not record['moved_ram_labels']
    names = {str(p.relative_to(BASE / side)) for side in ('baseline-source', 'candidate')
             for p in (BASE / side).rglob('*.asm')}
    changed, patch = [], ''
    for name in sorted(names):
        a, b = BASE / 'baseline-source' / name, BASE / 'candidate' / name
        old_text, new_text = a.read_text() if a.exists() else '', b.read_text() if b.exists() else ''
        if old_text != new_text:
            changed.append(name)
            patch += ''.join(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True),
                fromfile='a/' + name if a.exists() else '/dev/null',
                tofile='b/' + name if b.exists() else '/dev/null'))
    expected = {'engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm',
                'engine/pokedex/pokedex_moves_mode.asm', 'engine/pokedex/pokedex_position.asm',
                'engine/menus/intro_menu.asm', 'ram/wram.asm'}
    assert set(changed) == expected, changed
    (BASE / 'candidate.diff').write_text(patch)
    for stem in (STEM, 'pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime',
                 'pokecrystal-dex-unown-fast', 'pokecrystal-dex-moves-position'):
        for ext in ('gbc', 'sym', 'map'):
            destination = BASE / f'{stem}.{ext}'
            if not destination.exists():
                destination.symlink_to(BASE / 'candidate' / f'pokecrystal.{ext}')
        destination = BASE / f'{stem}.sav'
        if not destination.exists():
            shutil.copy2(CONTROL / 'review-all-moves.sav', destination)
    record.update(candidate_sha256=sha256((BASE / 'candidate/pokecrystal.gbc').read_bytes()),
                  changed_owners=changed, saved_padding_assigned=8, saved_padding_remaining=4)
    for name, digest in record['protected'].items():
        assert sha256(Path(name).read_bytes()) == digest, name
    write(path, record)
    print(json.dumps({key: record[key] for key in ('candidate_sha256', 'delta', 'pokemon_delta')}, indent=2))


def publish():
    manifest = json.loads((BASE / 'position-memory-manifest.json').read_text())
    assert manifest['full_regression_passed'] is True
    target = BASE / 'review'
    target.mkdir(exist_ok=False)
    for ext in ('gbc', 'sym', 'map', 'sav'):
        shutil.copy2(BASE / f'{STEM}.{ext}', target / f'{STEM}.{ext}')
    manifest['review_files'] = {str(p): sha256(p.read_bytes()) for p in target.iterdir()}
    write(BASE / 'position-memory-manifest.json', manifest)
    print(json.dumps(manifest['review_files'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'freeze', 'build', 'publish'))
    parser.add_argument('--output', type=Path, default=BASE)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    BASE = args.output.resolve()
    if not BASE.is_relative_to(ROOT / 'build'):
        raise ValueError('Prototype outputs must stay under build')
    build(args.jobs) if args.action == 'build' else globals()[args.action]()
