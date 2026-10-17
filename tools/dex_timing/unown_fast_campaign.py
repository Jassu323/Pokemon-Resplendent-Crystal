"""Qualify the private Unown link using established native Dex campaigns."""
import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import gzip
import subprocess
import sys
import tarfile
import tempfile

from PIL import Image

from . import type_full_regression as campaign
from . import performance, listing_options
from .unown_comparison import battery
from .assets import read_symbols, sha256
from .cold_listing import Driver, KEY
from .info_ui import BOOT
from .unown_performance import reach


def setup(output):
    source = Path(json.loads((output / 'campaign-manifest.json').read_text())['source'])
    baseline = output / 'baseline/candidate'
    shutil.copytree(source / 'candidate/gfx', baseline / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(source / 'candidate/build' / name, baseline / 'build' / name, dirs_exist_ok=True)
    review = source / 'all-unown-review'
    review.mkdir(exist_ok=True)
    stem = 'pokecrystal-dex-unown-fast'
    shutil.copy2(source / f'{stem}.gbc', review / f'{stem}.gbc')
    battery(source / f'{stem}.sav', read_symbols(source / f'{stem}.sym'),
            review / f'{stem}.sav', 26, True)
    return campaign.run(output, 'setup')


def regular_timing(output, jobs):
    target = output / 'regular-selection-timing'
    target.mkdir(exist_ok=True)
    tasks = []
    for style in ('modern', 'legacy'):
        config = listing_options.configuration(output / 'dex-regression', style)
        folder = target / style
        folder.mkdir(exist_ok=True)
        config = dict(config, output=str(folder))
        for name in ('chikorita', 'dusknoir', 'weavile', 'eevee', 'unown_a', 'porygonz'):
            for phase in (0, 1, 2, 3):
                tasks.append((config, name, 'species', 'settled', 0, phase))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(performance.run_case, tasks))
    result = dict(cases=len(rows), failures=sum(row['status'] != 'pass' for row in rows),
                  metric='Complete selected Info owner; portrait animation excluded from stable crop',
                  summary=performance.summarize(rows), results=rows)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}), flush=True)
    return int(bool(result['failures']))


def listing_case(task):
    output, variant, style, phase, index = task
    base = Path(output) / ('baseline' if variant == 'baseline' else '')
    config = listing_options.configuration(base / 'dex-regression', style)
    folder = Path(output) / 'listing-selection-timing'
    repo = performance.Repository(base / 'candidate', Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                    folder / f'{variant}-{style}-{index}-q{phase}.log')
    captures = tempfile.TemporaryDirectory(prefix='unown-listing-comparison-')
    images = Path(captures.name)
    # Exclude ongoing grid animation and the scrollbar from portrait latency.
    def picture(path):
        with Image.open(path) as image:
            return hashlib.sha256(image.convert('RGB').crop((0, 8, 54, 64)).tobytes()).hexdigest()
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.run(frames=4)
        if phase:
            driver.command(f'run 0 {phase} 0')
        driver.command(f'image {images}/before.ppm')
        initial = driver.command('perf 1')
        initial['picture'] = picture(images / 'before.ppm')
        driver.events.clear()
        driver.command(f'perfimages {images}/frame')
        changed = ('PokedexLegacy_UpdateMainScreen.changed' if style == 'legacy'
                   else 'Pokedex_UpdateMainScreen.selection_changed')
        loop = ('PokedexLegacy_UpdateMainScreen' if style == 'legacy'
                else 'Pokedex_UpdateMainScreen')
        accepted = reach(driver, repo.symbols, changed, KEY['down'])
        reach(driver, repo.symbols, loop)
        driver.run(frames=4)
        final = driver.command('perf 0')
        driver.command('perfimages -')
        driver.command(f'image {images}/after.ppm')
        final['picture'] = picture(images / 'after.ppm')
        for event in driver.events:
            if event['event'] == 'perf_frame':
                event['picture'] = picture(images / f'frame-{event["display"]:03}.ppm')
        result = dict(variant=variant, style=style, phase=phase, index=index,
                      portrait=performance.result_timing(list(driver.events), initial, final,
                                                         'picture', initial['t'], accepted['t']),
                      **performance.result_timing(list(driver.events), initial, final,
                                                  'full', initial['t'], accepted['t']))
        if not result['complete_visible']:
            raise RuntimeError(f'No complete {style} selection observed')
        return result
    finally:
        driver.close()
        captures.cleanup()


def listing_timing(output, jobs):
    target = output / 'listing-selection-timing'
    target.mkdir(exist_ok=True)
    tasks = [(str(output), variant, style, phase, index)
             for variant in ('baseline', 'candidate') for style in ('modern', 'legacy')
             for phase in (0, 17556, 35112, 52668) for index in (0, 8, 24, 100, 255, 371)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(listing_case, tasks))
    result = dict(cases=len(rows), results=rows)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), styles=['modern', 'legacy'])), flush=True)
    return 0


def restore_negative(output):
    from .regression_fixtures import require, restore, KEYBOARD_CONTROL
    from .moves_search import prepare
    restore()
    restored = require(KEYBOARD_CONTROL / 'pokecrystal-dex-moves-search.gbc').parent
    if not (restored / 'search-tests/config.json').is_file():
        prepare(restored)
    manifest = output / 'moves-mode-manifest.json'
    data = json.loads(manifest.read_text())
    data['visual_rollback'] = str(restored)
    donor = require('build/dex-moves-struggle-grant-20261008/moves-mode-manifest.json').parent
    data['sort_memory_source'] = str(donor)
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(restored_negative_control=str(restored), archived_batteries_restored=True,
                          archive_verified=True)), flush=True)
    return 0


def model(task):
    source, name = task
    existing = source / ('model-' + name) / 'summary.json'
    if existing.exists():
        data = json.loads(existing.read_text())
        assert data['rom_sha256'] == sha256((source / 'pokecrystal-dex-unown-fast.gbc').read_bytes())
        assert data['cases'] == 112 and all(row.get('whole_frame_checks') for row in data['records'])
        return dict(model=name, exit_code=0, matching_existing_report=True)
    command = [sys.executable, '-m', 'tools.dex_timing.unown_performance', '--source',
               str(source / 'candidate'), '--output', str(source / ('model-' + name)), '--model', name]
    with (source / ('model-' + name + '.log')).open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    return dict(model=name, exit_code=result.returncode)


def models(output, jobs):
    source = Path(json.loads((output / 'campaign-manifest.json').read_text())['source'])
    with ProcessPoolExecutor(max_workers=min(jobs, 3)) as pool:
        rows = list(pool.map(model, [(source, name) for name in ('0', 'A', 'B', 'C', 'D')]))
    print(json.dumps(rows), flush=True)
    return int(any(row['exit_code'] for row in rows))


def final(output, jobs):
    assert setup(output) == 0
    restore_negative(output)
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(campaign.run, output, name)
                   for name in ('dex', 'moves', 'persistence', 'gameplay')}
        for name, future in futures.items():
            results[name] = future.result()
    # Save timing needs the fresh persistence/migration fixtures first.
    results['timing'] = campaign.run(output, 'timing')
    results['host'] = campaign.host(output)
    results['regular-timing'] = regular_timing(output, jobs)
    results['listing-timing'] = listing_timing(output, jobs)
    results['models'] = models(output, jobs)
    (output / 'unown-campaign.json').write_text(json.dumps(results, indent=2) + '\n')
    return int(any(results.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('setup', 'dex', 'moves', 'host', 'gameplay',
                                         'regular-timing', 'listing-timing', 'timing', 'restore-negative', 'models', 'final'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    output = args.output.resolve()
    actions = {'setup': lambda: setup(output),
               'regular-timing': lambda: regular_timing(output, args.jobs),
               'listing-timing': lambda: listing_timing(output, args.jobs),
               'restore-negative': lambda: restore_negative(output),
               'models': lambda: models(output, args.jobs),
               'final': lambda: final(output, args.jobs),
               'host': lambda: campaign.host(output)}
    result = actions[args.phase]() if args.phase in actions else campaign.run(output, args.phase)
    raise SystemExit(result)
