"""Compare Selected display architectures with fresh native-input fixtures."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from . import performance, listing_options, selected_runtime, legacy_listing, listing_warming
from .assets import Repository
from .cold_listing import ROOT
from . import moves_search_dex_regression, search_qualification, mode_transitions, type_full_regression
from .cold_listing import Driver, predecessor, move, bootstrap
from .info_ui import BOOT, press, ready
from .area_ui import reach
from .description_ui import settle

REFERENCE = ROOT / 'build/dex-selected-runtime-20261012-v2'
CAMPAIGN = ROOT / 'build/dex-selected-runtime-regression-20261012-v2'


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare(source):
    target = source / 'focused'
    target.mkdir(exist_ok=True)
    stem = source / 'pokecrystal-dex-selected-runtime'
    config = performance.prepare(stem.with_suffix('.gbc'), stem.with_suffix('.sym'),
                                 stem.with_suffix('.sav'), target / 'modern')
    repo = Repository(source / 'candidate', stem.with_suffix('.gbc'), stem.with_suffix('.sym'))
    config['core'] = str(performance.core(repo, target / 'popover-core', listing_options.POINTS).resolve())
    write(target / 'modern/config.json', config)
    legacy_listing.prepare_legacy(target / 'legacy', config)
    print(json.dumps(dict(phase='prepare', hashes=repo.hashes, fresh_checkpoints=True)), flush=True)


def control(source, jobs):
    from tools.build_selected_runtime_prototype import prepare as freeze, DONOR
    freeze(source)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', source / f'pokecrystal-dex-selected-runtime.{ext}')
    shutil.copy2(DONOR, source / 'pokecrystal-dex-selected-runtime.sav')
    prepare(source)
    return 0


def feature(source, jobs):
    from pokedex_info_assets import Compiler
    folder = source / 'feature-timing'
    folder.mkdir(exist_ok=True)
    stem = source / 'pokecrystal-dex-selected-runtime'
    repo = Repository(source / 'candidate', stem.with_suffix('.gbc'), stem.with_suffix('.sym'))
    data = Compiler().compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
    tasks = []
    names = ('bayleef', 'meganium', 'crobat', 'politoed', 'kingdra', 'weavile',
             'dusknoir', 'chansey', 'blissey', 'porygonz', 'steelix', 'charizard')
    for style in ('modern', 'legacy'):
        local = folder / style
        local.mkdir(exist_ok=True)
        config = dict(listing_options.configuration(source / 'focused', style), output=str(local))
        for name in names:
            constant = {'porygonz': 'PORYGON_Z'}.get(name, name.upper())
            for page in range(1 + len(data['pages'][constant])):
                for action in ('cycle', 'listing', 'info-area-return'):
                    tasks.extend(((config, name, action, phase, page, q), style)
                                 for phase in ('0', 'settled') for q in (0, 17556, 35112, 52668))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(feature_case, tasks))
    result = dict(cases=len(rows), failures=sum(row['status'] != 'pass' for row in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    if result['failures']:
        print(json.dumps([r for r in rows if r['status'] != 'pass'][:3]), flush=True)
    return int(bool(result['failures']))


def feature_case(task):
    case, style = task
    return dict(performance.run_case(case), style=style)


def campaign(source, jobs):
    rows = []
    for phase in ('info', 'moves', 'stress', 'timing', 'feature', 'startup', 'entry', 'returns', 'dex', 'modes', 'types', 'host'):
        folder = source / 'qualification'
        folder.mkdir(exist_ok=True)
        log = folder / f'campaign-{phase}.log'
        with log.open('w') as stream:
            result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.selected_architecture',
                                     phase, '--source', str(source), '--jobs', str(jobs)], cwd=ROOT,
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, PYTHONPATH='tools:.'))
        rows.append(dict(phase=phase, exit_code=result.returncode, log=str(log)))
        write(folder / 'campaign.json', rows)
        print(json.dumps(rows[-1]), flush=True)
        if result.returncode:
            print(log.read_text()[-3000:], flush=True)
    return int(any(row['exit_code'] for row in rows))


def modes(source, jobs):
    fixtures(source, jobs)
    result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.mode_transitions',
                             '--output', str(source / 'focused'), '--jobs', str(jobs),
                             '--indices', '1,8', '--phases', '4', '--prior-view', 'info',
                             '--tag', 'ancestor-font-reuse'], cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH='tools:.'))
    return result.returncode


def types(source, jobs):
    result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.type_matchups',
                             '--output', str(source)], cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH='tools:.'))
    return result.returncode


def timing(source, jobs):
    rows, tasks = [], []
    folder = source / 'architecture-timing'
    folder.mkdir(exist_ok=True)
    configs = {}
    for style in ('modern', 'legacy'):
        local = folder / style
        local.mkdir(exist_ok=True)
        configs[style] = dict(listing_options.configuration(source / 'focused', style), output=str(local))
    for name in ('paired-timing', 'extra-timing'):
        reference = json.loads((REFERENCE / name / 'summary.json').read_text())
        for row in reference['rows']:
            if row['variant'] == 'candidate':
                tasks.append((configs[row['style']], row['species'], row['action'], row['phase'],
                              row['input_phase'], 'semantic', row['style']))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(selected_runtime.latency_case, tasks):
            rows.append(row)
            if len(rows) % 100 == 0 or row['status'] != 'pass':
                print(json.dumps(dict(done=len(rows), failures=sum(r['status'] != 'pass' for r in rows))), flush=True)
    result = dict(cases=len(rows), failures=sum(r['status'] != 'pass' for r in rows), rows=rows)
    write(folder / 'summary.json', result)
    return int(bool(result['failures']))


def startup(source, jobs):
    folder = source / 'startup-timing'
    folder.mkdir(exist_ok=True)
    tasks = []
    for style in ('modern', 'legacy'):
        config = dict(listing_options.configuration(source / 'focused', style), output=str(folder))
        tasks.extend((config, 'semantic', style, phase) for phase in (0, 17556, 35112, 52668))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(selected_runtime.startup_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps(result), flush=True)
    return int(bool(result['failures']))


def entry(source, jobs):
    folder = source / 'entry-timing'
    folder.mkdir(exist_ok=True)
    tasks = []
    for style in ('modern', 'legacy'):
        config = listing_options.configuration(source / 'focused', style)
        tasks.extend((config, name, hover, phase, 'candidate', str(folder))
                     for name in listing_warming.SPECIES for hover in listing_warming.HOVERS
                     for phase in listing_warming.PHASES)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(listing_warming.entry_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    return int(bool(result['failures']))


def fixtures(source, jobs):
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(source / f'pokecrystal-dex-selected-runtime.{ext}', source / f'pokecrystal-dex-moves-search.{ext}')
    for name in ('moves-mode-manifest.json', 'sort-manifest.json'):
        shutil.copy2(CAMPAIGN / name, source / name)
    shutil.copy2(source / 'sort-manifest.json', source / 'focused/sort-manifest.json')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    manifest['rom_sha256'] = Repository(source / 'candidate', source / 'pokecrystal-dex-selected-runtime.gbc',
                                       source / 'pokecrystal-dex-selected-runtime.sym').hashes['rom_sha256']
    # The all-Pokemon fixture is not necessarily an all-Moves fixture. Derive
    # the independent save's discovery expectation through normal loading.
    from .moves_mode import memory
    config = listing_options.configuration(source / 'focused')
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], source / 'fixture-discovery.log')
    try:
        bootstrap(driver)
        repo = Repository(source / 'candidate', Path(config['rom']), Path(config['sym']))
        seen = memory(driver, *repo.symbols['wMoveDiscoverySeen'], 64)
    finally:
        driver.close()
    manifest['fixture'] = 'mixed'
    manifest['unknown'] = [index for index in range(1, len(manifest['moves']) + 1)
                           if not seen[(index - 1) // 8] & (1 << ((index - 1) & 7))]
    write(source / 'moves-mode-manifest.json', manifest)
    return 0


def dex(source, jobs, retry=False):
    fixtures(source, jobs)
    folder = source / 'dex-regression'
    if not folder.exists():
        folder.symlink_to(source / 'focused', target_is_directory=True)
    shutil.copy2(source / 'sort-manifest.json', folder / 'sort-manifest.json')
    logs = source / 'qualification'
    logs.mkdir(exist_ok=True)
    commands = [('moves_search_dex_regression', action, '--output', str(source), '--jobs', str(jobs))
                for action in ('listings', 'interfaces', 'selected')]
    commands += [('search_qualification', '--source', str(folder), '--jobs', str(jobs), *flags)
                 for flags in ((), ('--returns',), ('--defaults',))]
    commands += [('mode_transitions', '--output', str(folder), '--jobs', str(jobs),
                  '--indices', '0,8,255,372', '--phases', '4')]
    commands += [('moves_search_dex_regression', 'qualify', '--output', str(source))]
    if retry:
        commands = [command for command in commands if command[0] == 'search_qualification'
                    or (command[0] == 'moves_search_dex_regression' and command[1] in ('interfaces', 'qualify'))]
    rows = []
    for index, command in enumerate(commands):
        tag = 'dex-retry' if retry else 'dex'
        log = logs / f'{tag}-{index:02}-{command[0]}.log'
        with log.open('w') as stream:
            result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + command[0], *command[1:]],
                                    cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, PYTHONPATH='tools:.'))
        rows.append(dict(command=command, exit_code=result.returncode, log=str(log)))
        write(logs / f'{tag}.json', rows)
        print(json.dumps(rows[-1]), flush=True)
        if result.returncode:
            print(log.read_text()[-5000:], flush=True)
    return int(any(row['exit_code'] for row in rows))


def dex_retry(source, jobs):
    return dex(source, jobs, True)


def integration(source, jobs):
    fixtures(source, jobs)
    return listing_options.integration(source / 'focused', jobs)


def qualify(source, jobs):
    print(json.dumps(moves_search_dex_regression.qualify(source)), flush=True)
    return 0


def units(source, jobs):
    folder = source / 'qualification'
    folder.mkdir(exist_ok=True)
    log = folder / 'runtime-units.log'
    with log.open('w') as stream:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'tools.test_selected_runtime_display', '-v'],
                                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                env=dict(os.environ, PYTHONPATH='tools:.', DEX_RUNTIME_SOURCE=str(source / 'candidate')))
    print(log.read_text(), flush=True)
    return result.returncode


def host(source, jobs):
    folder = source / 'campaign-logs'
    folder.mkdir(exist_ok=True)
    if not (source / 'baseline').exists():
        (source / 'baseline').symlink_to(CAMPAIGN / 'baseline', target_is_directory=True)
    return type_full_regression.host(source)


def return_case(task):
    config, name, page, delay = task
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    label = f'{name}-p{page}-cancel{delay}'
    folder = Path(config['output'])
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], folder / (label + '.log'))
    issues = []
    try:
        index = config['names'].index(name)
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.command('audit 1')
        driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        settle(driver)
        performance.view(driver, repo, name, 1, page)
        if delay != 'none':
            press(driver, 'a')
            driver.run(('animation_miss', 'audio_miss'), frames=int(delay))
        driver.run(('leave',), key='b')
        before = driver.command('ui')
        if delay == 'none' and name in ('chikorita', 'eevee', 'slowpoke'):
            driver.command(f'image {folder / (label + "-before.ppm")}')
        reach(driver, repo, 'PokedexInfo_PreserveReturnPanel.done')
        after = driver.command('ui')
        for key in ('lower_tiles', 'attrs', 'picture', 'palettes', 'obj_palettes'):
            if before[key] != after[key]:
                issues.append('return_changed_' + key)
        if delay == 'none' and name in ('chikorita', 'eevee', 'slowpoke'):
            driver.command(f'image {folder / (label + "-after.ppm")}')
        final = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        if final['hit'] != 'listing' or final['index'] != index:
            issues.append('listing_return')
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            issues.append('playback_miss')
        write(folder / (label + '.json'), dict(before=before, after=after, events=driver.events))
    except Exception as error:
        issues.append(str(error))
        driver.evidence(folder / (label + '-failure'))
    finally:
        driver.close()
    return dict(species=name, page=page, delay=delay, issues=issues)


def returns(source, jobs):
    from pokedex_info_assets import Compiler
    folder = source / 'return-pixels'
    folder.mkdir(exist_ok=True)
    config = dict(listing_options.configuration(source / 'focused', 'modern'), output=str(folder))
    repo = Repository(source / 'candidate', Path(config['rom']), Path(config['sym']))
    data = Compiler().compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
    names = ('chikorita', 'eevee', 'tyrogue', 'slowpoke', 'onix', 'kingdra', 'politoed',
             'dusknoir', 'weavile', 'mew', 'chansey', 'porygonz')
    tasks = []
    for name in names:
        constant = {'porygonz': 'PORYGON_Z'}.get(name, name.upper())
        for page in range(1 + len(data['pages'][constant])):
            tasks.extend((config, name, page, delay) for delay in ('none', '0', '4', '12', '32'))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(return_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    if result['failures']:
        print(json.dumps([row for row in rows if row['issues']][:10]), flush=True)
    return int(bool(result['failures']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'control', 'campaign', 'modes', 'types', 'feature', 'info', 'moves', 'stress', 'timing', 'startup', 'entry', 'dex', 'dex-retry', 'units', 'host', 'fixtures', 'returns', 'integration', 'qualify'))
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.phase == 'prepare':
        prepare(source)
        code = 0
    elif args.phase in ('info', 'moves'):
        code = selected_runtime.panels(source, args.jobs, args.phase)
    elif args.phase == 'stress':
        code = selected_runtime.stress(source, args.jobs)
    else:
        code = globals()[args.phase.replace('-', '_')](source, args.jobs)
    raise SystemExit(code)
