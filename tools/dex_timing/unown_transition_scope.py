"""Private, real-input Unown transition profiling and bounded comparisons."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import difflib
import json
from pathlib import Path
import shutil
import statistics
import subprocess

from .assets import Repository, read_symbols, sha256
from .cold_listing import ROOT, Driver, bootstrap
from .dex_modes import audit_menu
from .info_ui import BOOT, press, ready as info_ready
from .moves_ui import ready as moves_ready
from .description_ui import settle
from .legacy_listing import private_battery, open_mode_screen
from .area_ui import reach
from .mode_transitions import capture
from .performance import core, names, HZ, T
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-unown-transitions-20261014'
DONOR = ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'
TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')
POINTS = {
    'unown_init': ('Pokedex_InitUnownMode', True),
    'unown_return': ('Pokedex_UpdateUnownMode.a_b', False),
    'mode_init': ('PokedexListing_InitModeScreen', True),
    'hide': ('PokedexListing_BeginMenuTransition', True),
    'reveal': ('PokedexListing_RevealMenu', True),
    'font_restore': ('PokedexAncestors_RestoreUnownFont', True),
    'font_upload': ('PokedexAncestors_UploadTitle', True),
    'draw_unown': ('Pokedex_DrawUnownModeBG', True),
    'picture': ('Pokedex_LoadUnownFrontpicTiles', True),
    'static_prepare': ('PokedexUnown_PreparePicture', True),
    'publish': ('PokedexUnown_Publish', True),
    'word': ('PrintUnownWord', True),
    'wait_bg': ('WaitBGMap', True),
    'attrs': ('ApplyAttrmap', True),
    'pals': ('ApplyPals', True),
    'layout_unown': ('_CGB_PokedexUnownMode', True),
    'layout_modes': ('_CGB_PokedexSearchOption', True),
    'usual_pals': ('Pokedex_ApplyUsualPals', True),
    'delay': ('DelayFrame', True),
    'owner_end': ('Pokedex_EndOwnerLoop', True),
    'fast_attrs': ('PokedexUnown_CommitAttributes', True),
    'fast_map': ('PokedexUnown_CommitTilemap', True),
    'hidden_map_upload': ('PokedexPerf_FastTownMap', True),
    'unown_layout_prepare': ('PokedexUnown_PrepareLayout', True),
    'menu_layout_prepare': ('PokedexMenu_PrepareLayout', True),
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def setup(label, model='E'):
    folder = BASE / label
    folder.mkdir(parents=True, exist_ok=True)
    source = ROOT if label == 'current' else folder / 'candidate'
    repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
    output = folder / ('core' if model == 'E' else f'core-{model}')
    binary = core(repo, output, POINTS, (f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}',))
    config = dict(core=str(binary.resolve()), rom=str(repo.rom_path.resolve()),
        sym=str((source / 'pokecrystal.sym').resolve()), battery=str(DONOR), names=names(),
        output=str(folder), hashes=repo.hashes, model=model)
    write(folder / f'config-{model}.json', config)
    return config


def freeze(label):
    target = BASE / label / 'candidate'
    if target.exists():
        raise ValueError('Candidate already exists')
    target.mkdir(parents=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in tracked:
        source = ROOT / name
        if name and source.is_file():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    shutil.copytree(ROOT / 'gfx', target / 'gfx', dirs_exist_ok=True)
    for name in TABLES:
        shutil.copytree(ROOT / 'build' / name, target / 'build' / name, dirs_exist_ok=True)
    # Host tools stay in the main checkout; only cartridge sources are varied.
    print(target, flush=True)


def build(label, jobs):
    folder = BASE / label
    with (folder / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'],
            cwd=folder / 'candidate', stdout=log, stderr=subprocess.STDOUT, check=True)
    old = resources(ROOT / 'pokecrystal.map')
    delta = {key: value - old[key] for key, value in resources(folder / 'candidate/pokecrystal.map').items()}
    before, after = read_symbols(ROOT / 'pokecrystal.sym'), read_symbols(folder / 'candidate/pokecrystal.sym')
    moved = [name for name, pair in before.items() if pair[1] >= 0xa000
             and name in after and pair != after[name]]
    assert not moved, moved
    write(folder / 'resources.json', dict(delta=delta, moved_ram_labels=moved))
    print(json.dumps(dict(label=label, delta=delta)), flush=True)


def profile_capture(driver, output, route, key, ready):
    record = capture(driver, output, route, key, ready)
    costs = defaultdict(list)
    for event in driver.events:
        if event['event'] == 'perf_cost':
            costs[event['name']].append(event['elapsed'])
    record['costs'] = {name: dict(calls=len(rows), ms=sum(rows) * 1000 / HZ,
        frames=sum(rows) / T, maximum_ms=max(rows) * 1000 / HZ) for name, rows in costs.items()}
    record['profile'] = [e for e in driver.events if e['event'] in ('perf_cost', 'perf_phase')]
    return record


def case(task):
    config, style, phase, prior, fixture, output = task
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, fixture, output / 'trace.log')
    records, issues = {}, []
    before = sha256(Path(fixture).read_bytes())
    try:
        bootstrap(driver)
        if prior != 'none':
            driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
            settle(driver)
            press(driver, 'right')
            if prior == 'moves':
                press(driver, 'right')
            press(driver, 'a')
            if prior == 'info':
                ui = info_ready(driver, 0)
                if ui['info_pages'] > 1:
                    press(driver, 'a')
                    info_ready(driver, 1)
            else:
                moves_ready(driver)
            press(driver, 'b')
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(('end_loop',))
        original = driver.command('peek')
        open_mode_screen(driver)
        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
        for _ in range(2 - style):
            press(driver, 'down')
        issues.extend(audit_menu(driver.command('ui'), True, 2))
        driver.command('rawcolor')
        driver.run(frames=2 + phase / 8)
        records['entry'] = profile_capture(driver, output, 'entry', 'a',
            lambda: reach(driver, repo, 'Pokedex_UpdateUnownMode'))
        from .assets import offset
        font = bytes.fromhex(driver.command('inspectvram 1 35664 432')['bytes'])
        start = offset(repo.symbols['UnownFont'])
        if font != bytes(value ^ 255 for value in repo.rom[start:start + 432]):
            issues.append('unown_resident_font')
        press(driver, 'right')
        reach(driver, repo, 'Pokedex_UpdateUnownMode')
        press(driver, 'left')
        reach(driver, repo, 'Pokedex_UpdateUnownMode')
        records['return'] = profile_capture(driver, output, 'return', 'a' if phase & 1 else 'b',
            lambda: reach(driver, repo, 'Pokedex_UpdateOptionScreen'))
        issues.extend(audit_menu(driver.command('ui'), True, 2))
        press(driver, 'b')
        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(('end_loop',))
        final = driver.command('peek')
        if final['index'] != original['index'] or final['presentation'] != style:
            issues.append('origin_not_restored')
        for route, record in records.items():
            issues.extend(route + ':' + issue for issue in record['issues'])
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / 'failure')
    finally:
        driver.close()
    if sha256(Path(fixture).read_bytes()) != before:
        issues.append('private_battery_modified')
    row = dict(style=style, phase=phase, prior=prior, model=config['model'],
        transitions=records, issues=issues)
    write(output / 'summary.json', row)
    return row


def test(label, jobs, phases, prior, model):
    config = json.loads((BASE / label / f'config-{model}.json').read_text())
    target = BASE / label / f'profile-{model}-{prior}-{phases}'
    target.mkdir(parents=True, exist_ok=False)
    protected = {str(path): sha256(path.read_bytes()) for path in
        [DONOR, *(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map'))]}
    tasks = []
    for style in (0, 1):
        fixture = target / f'fixture-{style}.sav'
        private_battery(config, fixture, presentation=style, order_mode=0, unown_unlocked=True)
        for phase in range(phases):
            tasks.append((config, style, phase, prior, str(fixture),
                          str(target / f'{style}-phase-{phase}')))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(case, tasks))
    unchanged = all(sha256(Path(path).read_bytes()) == digest for path, digest in protected.items())
    assert unchanged, 'Protected production/donor input changed'
    timing = {}
    for route in ('entry', 'return'):
        records = [r['transitions'][route] for r in rows if route in r['transitions']]
        timing[route] = {key: dict(median=statistics.median(r[key] for r in records),
            minimum=min(r[key] for r in records), maximum=max(r[key] for r in records))
            for key in ('first_ms', 'first_frames', 'complete_ms', 'complete_frames')}
    summary = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows),
        timings=timing, rows=rows, protected_inputs_unchanged=unchanged,
        hashes=config['hashes'])
    write(target / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2), flush=True)
    return bool(summary['failures'])


def neighbors(label, jobs):
    from .dex_modes import row_case, mode_ids
    from .mode_transitions import case as transition_case
    from .unown_regression import case as form_case, orders
    config = json.loads((BASE / label / 'config-E.json').read_text())
    source = ROOT if label == 'current' else BASE / label / 'candidate'
    manifest = ROOT / 'build/dex-description-fix-integration-20261014/runtime/moves-mode-manifest.json'
    # These are only host-side rendering expectations, not cartridge metadata.
    if source != ROOT:
        shutil.copy2(manifest, source / 'moves-mode-manifest.json')
    config = dict(config, red_background=True, black_panels=True)
    target = BASE / label / 'neighbors'
    target.mkdir(exist_ok=False)
    results = {}
    forms = target / 'forms'
    forms.mkdir()
    form_tasks = [(config, str(source), str(forms), name, caught, style, 0)
                  for name, caught in orders().items() for style in (0, 1)]
    menus = target / 'menus'
    menus.mkdir()
    menu_tasks, transition_tasks = [], []
    for unlocked in (False, True):
        for style in (0, 1):
            for order in (0, 1, 2):
                fixture = menus / f'fixture-{int(unlocked)}-{style}-{order}.sav'
                private_battery(config, fixture, presentation=style, order_mode=order,
                                unown_unlocked=unlocked)
                menu_tasks.extend((config, str(fixture), unlocked, style, order, row, str(menus))
                                  for row in range(len(mode_ids(unlocked))))
                if unlocked and order == 0:
                    transition_tasks.extend((dict(config, prior_view='info'), str(fixture),
                        style, index, phase, str(target))
                        for index in (0, 8, 255, 372) for phase in range(4))
    for name, function, tasks in (('forms', form_case, form_tasks),
                                 ('menus', row_case, menu_tasks),
                                 ('transitions', transition_case, transition_tasks)):
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(function, tasks))
        record = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows)
        if name == 'forms':
            record['form_selections'] = sum(r['checks'] for r in rows)
        if name == 'transitions':
            record['display_transitions'] = sum(len(r['transitions']) for r in rows)
        write(target / f'{name}.json', record)
        results[name] = {k: v for k, v in record.items() if k != 'rows'}
        print(json.dumps(dict(suite=name, **results[name])), flush=True)
    write(target / 'summary.json', results)
    return any(r['failures'] for r in results.values())


def models(label, jobs):
    for model in ('0', 'A', 'B', 'C', 'D'):
        setup(label, model)
        if test(label, jobs, 4, 'info', model):
            return True
    return False


def adjacent_transitions(label, jobs):
    from .mode_transitions import case as transition_case
    config = json.loads((BASE / label / 'config-E.json').read_text())
    target = BASE / label / 'adjacent-transitions'
    target.mkdir(exist_ok=False)
    tasks = []
    for style in (0, 1):
        fixture = target / f'fixture-{style}.sav'
        private_battery(config, fixture, presentation=style, order_mode=0, unown_unlocked=True)
        tasks.extend((dict(config, prior_view='info'), str(fixture), style, index, phase, str(target))
                     for index in (0, 8, 255, 372) for phase in range(4))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(transition_case, tasks))
    record = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows,
                  display_transitions=sum(len(r['transitions']) for r in rows))
    write(target / 'summary.json', record)
    print(json.dumps({k: v for k, v in record.items() if k != 'rows'}), flush=True)
    return bool(record['failures'])


def summarize():
    from PIL import Image
    comparison = {}
    for label in ('waits', 'staged'):
        contexts = {}
        for prior in ('none', 'info', 'moves'):
            path = BASE / label / f'profile-E-{prior}-8/summary.json'
            if not path.exists():
                continue
            trial = json.loads(path.read_text())
            baseline = json.loads((BASE / 'current' / path.relative_to(BASE / label)).read_text())
            paired = []
            for old, new in zip(baseline['rows'], trial['rows']):
                assert (old['style'], old['phase']) == (new['style'], new['phase'])
                for route in ('entry', 'return'):
                    a, b = old['transitions'][route], new['transitions'][route]
                    paired.append(dict(style=new['style'], phase=new['phase'], route=route,
                        ms=b['complete_ms'] - a['complete_ms'],
                        frames=b['complete_frames'] - a['complete_frames']))
            contexts[prior] = dict(current=baseline['timings'], candidate=trial['timings'],
                paired={route: {key: dict(median=statistics.median(row[key] for row in paired if row['route'] == route),
                    minimum=min(row[key] for row in paired if row['route'] == route),
                    maximum=max(row[key] for row in paired if row['route'] == route))
                    for key in ('ms', 'frames')} for route in ('entry', 'return')})
        resources_record = json.loads((BASE / label / 'resources.json').read_text())
        comparison[label] = dict(resources=resources_record, contexts=contexts)
        candidate = BASE / label / 'candidate'
        owners = ('engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm', 'engine/gfx/cgb_layouts.asm')
        patch = ''.join(''.join(difflib.unified_diff((ROOT / name).read_text().splitlines(True),
            (candidate / name).read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
            for name in owners)
        (BASE / label / 'candidate.diff').write_text(patch)
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', BASE / label / f'pokecrystal-dex-unown-{label}.{ext}')
        config = json.loads((BASE / label / 'config-E.json').read_text())
        private_battery(config, BASE / label / f'pokecrystal-dex-unown-{label}.sav',
                        presentation=0, order_mode=0, unown_unlocked=True)
    # Compare actual settled pixels to production, not only each ROM to itself.
    parity = []
    for path in sorted((BASE / 'staged').glob('profile-E-*-8/summary.json')):
        for row in json.loads(path.read_text())['rows']:
            folder = f'{row["style"]}-phase-{row["phase"]}'
            old_row = json.loads((BASE / 'current' / path.parent.name / folder / 'summary.json').read_text())
            for route in ('entry', 'return'):
                old = old_row['transitions'][route]['complete_display_index']
                new = row['transitions'][route]['complete_display_index']
                with Image.open(BASE / 'current' / path.parent.name / folder / route / f'display-{old:03}.png') as a:
                    with Image.open(path.parent / folder / route / f'display-{new:03}.png') as b:
                        aa, bb = a.convert('RGB').tobytes(), b.convert('RGB').tobytes()
                differing = [i for i in range(160 * 144) if aa[i*3:i*3+3] != bb[i*3:i*3+3]
                    and not (route == 'return' and 16 <= i % 160 < 24 and 56 <= i // 160 < 64)]
                parity.append(dict(context=path.parent.name, style=row['style'], phase=row['phase'],
                    route=route, checked_pixels=160 * 144 - (64 if route == 'return' else 0),
                    differing_pixels=len(differing)))
    assert not any(row['differing_pixels'] for row in parity), parity
    old_path = BASE / 'current/adjacent-transitions/summary.json'
    adjacent = {}
    if old_path.exists():
        baseline = json.loads(old_path.read_text())
        candidate = json.loads((BASE / 'staged/neighbors/transitions.json').read_text())
        assert baseline['failures'] == candidate['failures'] == 0
        old_rows = {(r['presentation'], r['index'], r['phase']): r for r in baseline['rows']}
        differences = defaultdict(list)
        for row in candidate['rows']:
            old = old_rows[(row['presentation'], row['index'], row['phase'])]
            for route, record in row['transitions'].items():
                differences[route].append(record['complete_ms'] - old['transitions'][route]['complete_ms'])
        adjacent = {route: dict(median_ms=statistics.median(rows), minimum_ms=min(rows),
            maximum_ms=max(rows), median_frames=statistics.median(rows) * HZ / 1000 / T,
            maximum_frames=max(rows) * HZ / 1000 / T) for route, rows in differences.items()}
    write(BASE / 'comparison.json', dict(variants=comparison, settled_pixel_parity=parity,
                                        adjacent_transition_deltas=adjacent))
    print(json.dumps(dict(visual_pairs=len(parity), differing_pairs=0,
                         comparison=str(BASE / 'comparison.json'))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('setup', 'freeze', 'build', 'test', 'neighbors', 'models',
                                         'adjacent_transitions', 'summarize'))
    parser.add_argument('label')
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--phases', type=int, default=8)
    parser.add_argument('--prior', choices=('none', 'info', 'moves'), default='none')
    parser.add_argument('--model', choices=('0', 'A', 'B', 'C', 'D', 'E'), default='E')
    args = parser.parse_args()
    if Path(args.label).name != args.label or args.phases not in range(1, 9) or args.jobs < 1:
        parser.error('Use one directory name, 1-8 phases and at least one worker')
    if args.action == 'setup':
        setup(args.label, args.model)
    elif args.action == 'freeze':
        freeze(args.label)
    elif args.action == 'build':
        build(args.label, args.jobs)
    elif args.action in ('neighbors', 'models', 'adjacent_transitions'):
        raise SystemExit(globals()[args.action](args.label, args.jobs))
    elif args.action == 'summarize':
        summarize()
    else:
        raise SystemExit(test(args.label, args.jobs, args.phases, args.prior, args.model))
