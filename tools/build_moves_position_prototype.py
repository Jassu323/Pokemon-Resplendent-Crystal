"""Freeze production and link a private shared Moves bookmark prototype."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import read_symbols, sha256
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/dex-moves-position-20261014'
TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')
STEM = 'pokecrystal-dex-moves-position'


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare(jobs):
    if BASE.exists():
        raise ValueError('Use a fresh private output directory')
    BASE.mkdir(parents=True)
    protected = {str(path): sha256(path.read_bytes()) for path in
                 [*(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')),
                  *ROOT.glob('pokecrystal*.sav')]}
    baseline = BASE / 'baseline-source'
    baseline.mkdir()
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in names:
        source = ROOT / name
        if name and source.is_file():
            target = baseline / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    ignored = shutil.ignore_patterns('*.o', '*.d', '*.pyc', '__pycache__')
    for name in ('gfx', 'tools', *('build/' + name for name in TABLES)):
        shutil.copytree(ROOT / name, baseline / name, dirs_exist_ok=True, ignore=ignored)
    with (BASE / 'baseline-build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=baseline,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    assert sha256((baseline / 'pokecrystal.gbc').read_bytes()) == protected[str(ROOT / 'pokecrystal.gbc')]
    shutil.copytree(baseline, BASE / 'candidate', ignore=ignored)
    rollback = BASE / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(baseline / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    with tarfile.open(BASE / 'rollback-source.tar', 'w') as archive:
        for path in baseline.iterdir():
            archive.add(path, arcname=path.name,
                        filter=lambda member: None if member.name.endswith(('.o', '.d', '.pyc')) else member)
    result = dict(protected=protected, baseline_sha256=protected[str(ROOT / 'pokecrystal.gbc')],
                  source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  production_integrated=False, status='Frozen; candidate changes pending')
    write(BASE / 'position-manifest.json', result)
    print(json.dumps(result, indent=2), flush=True)


def apply(jobs):
    subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes/moves_position.diff')],
                   cwd=BASE / 'candidate', check=True)


def build(jobs):
    candidate = BASE / 'candidate'
    with (BASE / 'candidate-build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    result = json.loads((BASE / 'position-manifest.json').read_text())
    old, new = resources(BASE / 'rollback/pokecrystal.map'), resources(candidate / 'pokecrystal.map')
    result['delta'] = {key: new[key] - old[key] for key in old}
    assert all(value == 0 for key, value in result['delta'].items() if key != 'ROMX')
    before, after = read_symbols(BASE / 'rollback/pokecrystal.sym'), read_symbols(candidate / 'pokecrystal.sym')
    result['moved_ram_labels'] = [name for name, pair in before.items()
                                 if pair[1] >= 0xa000 and name in after and pair != after[name]]
    assert not result['moved_ram_labels']
    owners = ('engine/pokedex/pokedex_moves_mode.asm', 'ram/wram.asm')
    patch = ''
    for name in owners:
        a, b = BASE / 'baseline-source' / name, candidate / name
        patch += ''.join(difflib.unified_diff(a.read_text().splitlines(True), b.read_text().splitlines(True),
                                            fromfile='a/' + name, tofile='b/' + name))
    (BASE / 'candidate.diff').write_text(patch)
    for stem in (STEM, 'pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime', 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map'):
            destination = BASE / f'{stem}.{ext}'
            if not destination.exists():
                destination.symlink_to(candidate / f'pokecrystal.{ext}')
        shutil.copy2(ROOT / 'build/dex-unown-transition-regression-20261014/pokecrystal-dex-unown-transitions.sav',
                     BASE / f'{stem}.sav')
    result.update(candidate_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                  changed_owners=list(owners), saved_padding_assigned=4, status='Built; qualification pending')
    for path, digest in result['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    write(BASE / 'position-manifest.json', result)
    print(json.dumps({key: result[key] for key in ('candidate_sha256', 'delta', 'saved_padding_assigned')}, indent=2))


def publish(jobs):
    result = json.loads((BASE / 'position-manifest.json').read_text())
    assert result.get('full_regression_passed') is True
    from move_discovery_assets import seed_records, move_bitmap
    original_save = sorted((BASE / 'position-tests').glob('saves*/normal-1.sav'))[-1]
    symbols = read_symbols(BASE / 'candidate/pokecrystal.sym')
    moves = json.loads((ROOT / 'build/dex-moves-mode-assets/manifest.json').read_text())['moves']
    source = BASE / 'review-all-moves.sav'
    source.write_bytes(seed_records(original_save.read_bytes(), symbols, move_bitmap(range(1, len(moves) + 1))))
    sources = {ext: BASE / 'candidate' / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')}
    sources['sav'] = source
    review = BASE / 'review'
    review.mkdir(exist_ok=True)
    if any((review / f'{STEM}.{ext}').exists() for ext in sources):
        raise ValueError('Do not overwrite existing review files')
    outputs = {}
    for ext, original in sources.items():
        destination = review / f'{STEM}.{ext}'
        if destination.exists():
            raise ValueError('Do not overwrite an existing review file: ' + str(destination))
        shutil.copy2(original, destination)
        outputs[str(destination)] = sha256(destination.read_bytes())
    result['review_files'] = outputs
    result['review_save_note'] = 'Private all-moves-seen fixture with a normally saved Alphabet bookmark; not the player battery'
    write(BASE / 'position-manifest.json', result)
    print(json.dumps(outputs, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'apply', 'build', 'publish'))
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    globals()[args.action](args.jobs)
