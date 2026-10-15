"""Freeze, qualify and account for the production nine-byte Description fix."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from . import dex_cleanup_campaign as campaign
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-description-fix-integration-20261014'
TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def freeze(jobs):
    if BASE.exists() or not BASE.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private integration directory')
    BASE.mkdir(parents=True)
    baseline = BASE / 'baseline-source'
    # The current checkout includes accepted, uncommitted cleanup work.
    # Seed converted assets, then overlay the actual checkout, not Git HEAD.
    shutil.copytree(ROOT / 'build/dex-cleanup-20261014/candidate', baseline,
        ignore=shutil.ignore_patterns('*.o', '*.d', '__pycache__', '*.pyc'))
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    tracked.append('engine/pokedex/new_entry_visual.asm')
    for name in tracked:
        source, destination = ROOT / name, baseline / name
        if source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        elif destination.is_file():
            destination.unlink()
    shutil.copytree(ROOT / 'tools', baseline / 'tools', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(ROOT / 'gfx', baseline / 'gfx', dirs_exist_ok=True)
    for name in TABLES:
        shutil.copytree(ROOT / 'build' / name, baseline / 'build' / name, dirs_exist_ok=True)
    hashes = {ext: sha256((ROOT / f'pokecrystal.{ext}').read_bytes())
              for ext in ('gbc', 'sym', 'map')}
    with (BASE / 'baseline-build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', '-W', 'main.asm', '-W', 'ram.asm',
                        'pokecrystal.gbc'], cwd=baseline, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    assert sha256((baseline / 'pokecrystal.gbc').read_bytes()) == hashes['gbc'], \
        'Frozen source does not reproduce production'
    rollback = BASE / 'rollback'
    rollback.mkdir()
    for ext in hashes:
        shutil.copy2(ROOT / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    with tarfile.open(BASE / 'rollback-source.tar', 'w') as archive:
        def retained(member):
            return None if member.name.endswith(('.o', '.d', '.pyc')) else member
        for path in baseline.iterdir():
            if path.name not in ('pokecrystal.gbc', 'pokecrystal.sym', 'pokecrystal.map'):
                archive.add(path, arcname=path.name, filter=retained)
    record = dict(baseline_sha256=hashes['gbc'], baseline_hashes=hashes,
                  baseline_rebuild_exact=True, baseline_source=str(baseline))
    write(BASE / 'integration.json', record)
    print(json.dumps(record, indent=2), flush=True)


def prepare():
    candidate = BASE / 'candidate'
    shutil.copytree(BASE / 'baseline-source', candidate,
        ignore=shutil.ignore_patterns('*.o', '*.d', '__pycache__', '*.pyc'))
    shutil.copy2(ROOT / 'engine/pokedex/pokedex_3.asm', candidate / 'engine/pokedex/pokedex_3.asm')
    shutil.copytree(ROOT / 'tools', candidate / 'tools', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', candidate / f'pokecrystal.{ext}')
    old, new = resources(BASE / 'rollback/pokecrystal.map'), resources(ROOT / 'pokecrystal.map')
    delta = {key: new[key] - value for key, value in old.items()}
    assert delta == dict(ROM0=0, ROMX=9, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0), delta
    before, after = read_symbols(BASE / 'rollback/pokecrystal.sym'), read_symbols(ROOT / 'pokecrystal.sym')
    moved = [name for name, pair in before.items() if pair[1] >= 0xa000
             and name in after and pair != after[name]]
    assert not moved, moved
    expected = ROOT / 'build/dex-description-latency-20261014/pending-aware/candidate/pokecrystal.gbc'
    digest = sha256((ROOT / 'pokecrystal.gbc').read_bytes())
    assert digest == sha256(expected.read_bytes()), 'Integrated ROM differs from the focused candidate'
    for stem in ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime',
                 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(ROOT / f'pokecrystal.{ext}', BASE / f'{stem}.{ext}')
        shutil.copy2(ROOT / 'build/dex-cleanup-20261014/pokecrystal-dex-types.sav',
                     BASE / f'{stem}.sav')
    record = json.loads((BASE / 'integration.json').read_text())
    record.update(rom_sha256=digest, delta=delta, moved_ram_labels=moved,
                  matches_focused_candidate=True, qualification='Fresh full regression pending')
    write(BASE / 'integration.json', record)
    campaign.BASE = BASE
    campaign.prepare()
    print(json.dumps(record, indent=2), flush=True)


def focused(jobs):
    from . import description_latency as latency, performance, legacy_listing, listing_options
    from .assets import Repository
    from .cold_listing import Driver, bootstrap, prepare_states
    from .info_ui import BOOT, fixture
    latency.BASE = BASE
    source = BASE / 'runtime'
    latency.RUN_TAG = 'integrated'
    for action in ('test', 'moves', 'visibility'):
        if getattr(latency, action)('runtime', jobs):
            raise RuntimeError('Focused ' + action + ' qualification failed')
    if latency.test('runtime', jobs, all_species=True):
        raise RuntimeError('Full-species Description qualification failed')
    models(jobs)


def models(jobs):
    from . import description_latency as latency, performance, legacy_listing, listing_options
    from .assets import Repository
    from .cold_listing import Driver, bootstrap, prepare_states
    from .info_ui import BOOT, fixture
    source = BASE / 'runtime'
    results = []
    for model in ('0', 'A', 'B', 'C', 'D', 'E'):
        target = BASE / 'description-models' / model
        completed = target / 'returns/summary.json'
        if completed.exists():
            record = json.loads(completed.read_text())
            assert record['cases'] == 256 and not record['failures'], record
            assert record['protected_inputs_unchanged'] and record['private_inputs_unchanged']
            config = json.loads((target / 'modern/config.json').read_text())
            assert config['hashes']['rom_sha256'] == sha256((source / 'pokecrystal-dex-types.gbc').read_bytes())
            results.append(dict(model=model, cases=record['cases'], failures=0,
                                rom_sha256=config['hashes']['rom_sha256']))
            continue
        target.mkdir(parents=True, exist_ok=False)
        repo = Repository(source / 'candidate', source / 'pokecrystal-dex-types.gbc',
                          source / 'pokecrystal-dex-types.sym')
        modern = target / 'modern'
        binary = performance.core(repo, modern, listing_options.POINTS,
                                 (f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}',))
        battery, states = modern / 'private.sav', modern / 'listing-states'
        seed = modern / 'modern-input.sav'
        legacy_listing.private_battery(dict(rom=str(repo.rom_path),
            sym=str(source / 'pokecrystal-dex-types.sym'),
            battery=str(source / 'pokecrystal-dex-types.sav')), seed,
            presentation=0, order_mode=0)
        fixture(seed, battery)
        states.mkdir()
        driver = Driver(binary, repo.rom_path, BOOT, battery, modern / 'bootstrap.log')
        try:
            bootstrap(driver)
            prepare_states(driver, states, len(performance.names()))
        finally:
            driver.close()
        config = dict(core=str(binary.resolve()), rom=str(repo.rom_path),
            sym=str(source / 'pokecrystal-dex-types.sym'), battery=str(battery),
            states=str(states), names=performance.names(), output=str(modern),
            hashes=repo.hashes, listing_style='modern', exact_playback=True, model=model)
        write(modern / 'config.json', config)
        legacy = legacy_listing.prepare_legacy(target / 'legacy', config)
        tasks = []
        for style, original in (('modern', config), ('legacy', legacy)):
            for view in (1, 2):
                output = target / f'{style}-view-{view}'
                output.mkdir()
                local = dict(original, output=str(output), source_view=view)
                tasks.extend(latency.cases(local, model))
        folder = target / 'returns'
        folder.mkdir()
        if latency.run(folder, tasks, jobs):
            raise RuntimeError('CGB ' + model + ' Description qualification failed')
        results.append(dict(model=model, cases=len(tasks), failures=0, rom_sha256=repo.hashes['rom_sha256']))
        write(BASE / 'description-models/summary.json', dict(models=results,
              cases=sum(row['cases'] for row in results), failures=0))
    write(BASE / 'description-models/summary.json', dict(models=results,
          cases=sum(row['cases'] for row in results), failures=0))


def response_violations(rows, maximum_frames=8):
    return [row for row in rows if not row.get('complete_visible') or
            row['complete_visible']['frames'] > maximum_frames]


def audit_latency():
    path = BASE / 'runtime/all-species-integrated/summary.json'
    record = json.loads(path.read_text())
    baseline = json.loads((ROOT / 'build/dex-description-latency-20261014/current/all-species-audio/summary.json').read_text())
    failures = response_violations(record['rows'])
    negative = response_violations(baseline['rows'])
    assert record['cases'] == baseline['cases'] == 1492
    assert record['failures'] == 0 and record['protected_inputs_unchanged'] and record['private_inputs_unchanged']
    assert not failures, 'Description complete-display latency exceeds eight frames'
    assert negative, 'Latency control did not detect the pre-fix publication starvation'
    result = dict(cases=record['cases'], failures=0, maximum_allowed_frames=8,
        maximum_allowed_ms=8 * 70224 * 1000 / 4194304,
        maximum_observed_frames=max(row['complete_visible']['frames'] for row in record['rows']),
        baseline_rejected_cases=len(negative), source=str(path),
        scope='Caught active Info internal-paging returns at ages 0/8; not a universal UI budget')
    write(BASE / 'description-response-budget.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'prepare', 'focused', 'models', 'audit-latency', 'standard', 'animations',
        'selected', 'displays', 'registration', 'lifecycle', 'lifecycle-audit', 'routes',
        'exit-matrix', 'audio', 'audio-registers', 'report'))
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    BASE = args.base.resolve()
    campaign.BASE = BASE
    if args.action == 'freeze':
        freeze(args.jobs)
    elif args.action == 'prepare':
        prepare()
    elif args.action == 'focused':
        focused(args.jobs)
    elif args.action == 'models':
        models(args.jobs)
    elif args.action == 'audit-latency':
        audit_latency()
    elif args.action in ('standard', 'report'):
        raise SystemExit(campaign.standard(['report'] if args.action == 'report' else args.phases))
    else:
        campaign.extras(args.action.replace('-', '_'))
