"""Preserve tested Type variants and integrate only their reviewed source delta."""
import argparse
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'build/dex-types-mode7-audio-20261012'
DEST = ROOT / 'research_artifacts/type-matchups-retained-20261012'
OUTPUT = ROOT / 'build/dex-types-production-runtime-20261012'
STEM = 'pokecrystal-dex-types'
GENERATED = {'.o', '.pyc', '.lz', '.1bpp', '.2bpp', '.gbcpal', '.dimensions',
             '.dexanim', '.dextimeline', '.dexschedule', '.map', '.sym', '.gbc',
             '.sav', '.rtc', '.s0', '.s1', '.s2', '.s3', '.s4', '.s5', '.s6', '.s7'}


def digest(path):
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_files(directory):
    for base, dirs, names in os.walk(directory, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', 'build', '__pycache__',
                         '.venv', 'node_modules', 'research_artifacts'}
                         and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if path.is_file() and not path.is_symlink() and path.suffix not in GENERATED:
                yield path


def archive(name, entries):
    target = DEST / (name + '.tar.gz')
    manifest_path = DEST / (name + '.json')
    if target.exists() or manifest_path.exists():
        raise ValueError('Refusing to replace retained archive: ' + name)
    records = []
    with tarfile.open(target, 'w:gz', compresslevel=6) as output:
        for source, relative in entries:
            records.append(dict(path=relative, bytes=source.stat().st_size, sha256=digest(source)))
            output.add(source, arcname=relative, recursive=False)
    expected = {r['path']: r for r in records}
    with tarfile.open(target, 'r:gz') as saved:
        for member in saved:
            record = expected.pop(member.name)
            assert member.isfile() and member.size == record['bytes']
            stream = saved.extractfile(member)
            h = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
            assert h.hexdigest() == record['sha256'], member.name
    assert not expected
    data = dict(archive=target.name, verified=True, sha256=digest(target),
                bytes=target.stat().st_size, files=records)
    manifest_path.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({k: v for k, v in data.items() if k != 'files'}), flush=True)
    return data


def preserve():
    DEST.mkdir(parents=True, exist_ok=True)
    for variant in ('runtime', 'precomputed'):
        directory = REVIEW / variant
        entries = [(p, 'candidate/' + p.relative_to(directory / 'candidate').as_posix())
                   for p in source_files(directory / 'candidate')]
        entries += [(directory / f'{STEM}.{ext}', f'{STEM}.{ext}')
                    for ext in ('gbc', 'sym', 'map', 'sav')]
        entries += [(directory / 'rollback-source.tar', 'rollback-source.tar')]
        for name in ('full-regression.json', 'phase-results.json'):
            entries.append((REVIEW / (variant + '-regression') / name, 'evidence/' + name))
        for name in ('comparison.json', 'all-animations/report.json',
                     'chart-phase-check/summary.json', 'chart-phase-check-100/summary.json'):
            entries.append((REVIEW / name, 'evidence/' + name))
        for name in ('audio-stress/summary.json', 'audio-navigation/summary.json',
                     'type-tests/summary.json', 'arrow-tests/summary.json'):
            entries.append((directory / name, 'evidence/' + name))
        archive(variant + '-approved', entries)
    entries = [(p, 'candidate/' + p.relative_to(ROOT).as_posix()) for p in source_files(ROOT)]
    # The player's battery is deliberately excluded from the production backup.
    entries += [(ROOT / f'pokecrystal.{ext}', f'pokecrystal.{ext}') for ext in ('gbc', 'sym', 'map')]
    archive('production-before-integration', entries)
    patch = []
    a, b = REVIEW / 'runtime/candidate', REVIEW / 'precomputed/candidate'
    for name in ('Makefile', 'engine/pokedex/pokedex_types_mode7_config.asm',
                 'engine/pokedex/pokedex_types_mode7_records.asm'):
        patch += difflib.unified_diff((a / name).read_text().splitlines(keepends=True),
                  (b / name).read_text().splitlines(keepends=True),
                  fromfile='a/' + name, tofile='b/' + name)
    path = ROOT / 'tools/dex_timing/probes/type_mode7_precomputed_fallback.patch'
    path.write_text(''.join(patch))
    (DEST / 'fallback-patch.sha256').write_text(digest(path) + '\n')


def integration_plan():
    candidate = REVIEW / 'runtime/candidate'
    old = {}
    with tarfile.open(REVIEW / 'runtime/rollback-source.tar') as saved:
        for member in saved:
            if member.isfile():
                old[member.name] = saved.extractfile(member).read()
    names = ['Makefile', 'main.asm', 'audio.asm', 'data/types/type_matchups.asm',
             'home/lcd.asm', 'home/vblank.asm']
    names += [p.relative_to(candidate).as_posix() for p in
              sorted((candidate / 'engine/pokedex').glob('*.asm'))]
    changes = []
    for name in names:
        before = old.get(name, b'')
        after = (candidate / name).read_bytes()
        if before == after:
            continue
        current = (ROOT / name).read_bytes() if (ROOT / name).exists() else b''
        # Comments added for the timing warning are already present in the tested
        # candidate. Never overwrite a different concurrent gameplay edit.
        if current not in (before, after) and name != 'home/vblank.asm':
            raise ValueError('Concurrent edit needs review: ' + name)
        if name == 'home/vblank.asm' and current not in (before, after):
            merged = subprocess.run(['git', 'merge-file', '-p', str(ROOT / name),
                         '/dev/stdin', str(candidate / name)], input=before,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if merged.returncode or merged.stdout != after:
                raise ValueError('VBlank warning merge requires manual review')
        changes.append(dict(path=name, before_sha256=hashlib.sha256(current).hexdigest(),
                            source_sha256=digest(candidate / name)))
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'integration-plan.json').write_text(json.dumps(changes, indent=2) + '\n')
    print(json.dumps(changes, indent=2))


def integrate():
    changes = json.loads((DEST / 'integration-plan.json').read_text())
    for row in changes:
        target = ROOT / row['path']
        current = target.read_bytes() if target.exists() else b''
        assert hashlib.sha256(current).hexdigest() == row['before_sha256'], row['path']
        source = REVIEW / 'runtime/candidate' / row['path']
        assert digest(source) == row['source_sha256']
    for row in changes:
        target = ROOT / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVIEW / 'runtime/candidate' / row['path'], target)
    print('Copied only the reviewed runtime source delta; production still needs rebuilding.')


def snapshot():
    target = OUTPUT / 'runtime'
    if target.exists():
        raise ValueError('Integration snapshot already exists')
    candidate = target / 'candidate'
    for path in source_files(ROOT):
        destination = candidate / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    # Native visual checks also read converted sidecars (including Unown forms)
    # that are not all direct dependencies of the normal ROM target.
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    for assets in (ROOT / 'build').glob('dex-*-assets'):
        if assets.is_dir():
            shutil.copytree(assets, candidate / 'build' / assets.name, dirs_exist_ok=True)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', target / f'{STEM}.{ext}')
        shutil.copy2(ROOT / f'pokecrystal.{ext}', candidate / f'pokecrystal.{ext}')
    shutil.copy2(REVIEW / f'runtime/{STEM}.sav', target / f'{STEM}.sav')
    shutil.copy2(REVIEW / 'runtime/rollback-source.tar', target / 'rollback-source.tar')
    baseline = OUTPUT / 'before-integration'
    with tarfile.open(DEST / 'production-before-integration.tar.gz') as saved:
        for ext in ('gbc', 'sym', 'map'):
            member = saved.getmember(f'pokecrystal.{ext}')
            saved.extract(member, baseline, filter='data')
    print(json.dumps(dict(output=str(OUTPUT), integrated_sha256=digest(ROOT / 'pokecrystal.gbc'),
                         approved_runtime_sha256=digest(REVIEW / f'runtime/{STEM}.gbc'))))


def animation_inputs():
    campaign = OUTPUT / 'runtime-regression'
    configs = []
    for variant, folder, stem in (('production', campaign / 'baseline', 'pokecrystal-dex-moves-mode'),
                                  ('runtime', OUTPUT / 'runtime', STEM)):
        configs.append(dict(variant=variant, root=str(folder / 'candidate'),
                            rom=str(folder / (stem + '.gbc')), sym=str(folder / (stem + '.sym')),
                            battery=str(campaign / 'legacy-input.sav'), expected_double_speed=0,
                            expected_battle_speed=0, fresh_battle_fixture=True))
    (OUTPUT / 'animation-inputs.json').write_text(json.dumps(configs, indent=2) + '\n')
    target = OUTPUT / 'diagnostic-original-chart/candidate'
    shutil.copytree(OUTPUT / 'runtime/candidate', target)
    with tarfile.open(OUTPUT / 'runtime/rollback-source.tar') as saved:
        chart = saved.extractfile('data/types/type_matchups.asm').read()
    (target / 'data/types/type_matchups.asm').write_bytes(chart + b'TypeMatchupsEnd::\n')
    with (target.parent / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j6', 'pokecrystal.gbc'], cwd=target,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    assert digest(target / 'pokecrystal.gbc') != digest(ROOT / 'pokecrystal.gbc')
    print(json.dumps(dict(configurations=str(OUTPUT / 'animation-inputs.json'),
                         chart_ablation_sha256=digest(target / 'pokecrystal.gbc'))))


def collect_retry():
    folder = OUTPUT / 'runtime-regression'
    successful = json.loads((folder / 'dex-successful-retry-phase-results.json').read_text())
    row = next(r for r in successful if r['phase'] == 'dex')
    assert row['exit_code'] == 0 and row['previous_attempts']
    actual = json.loads((folder / 'campaign-logs/dex.json').read_text())
    assert not actual['issues'] and all(r['exit_code'] == 0 for r in actual['results'])
    dex = json.loads((folder / 'dex-regression/summary.json').read_text())
    assert dex['cases'] == 4479 and not dex['failures']
    with (folder / 'phase-results.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = folder / 'phase-results.json'
        rows = json.loads(path.read_text())
        old = next(r for r in rows if r['phase'] == 'dex')
        rows[rows.index(old)] = row
        path.write_text(json.dumps(rows, indent=2) + '\n')
        fcntl.flock(lock, fcntl.LOCK_UN)
    print('Collected the actual successful Dex retry; initial failed attempt remains recorded.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preserve', 'plan', 'integrate', 'snapshot', 'animation-inputs', 'collect-retry'))
    args = parser.parse_args()
    {'preserve': preserve, 'plan': integration_plan, 'integrate': integrate, 'snapshot': snapshot,
     'animation-inputs': animation_inputs, 'collect-retry': collect_retry}[args.action]()
