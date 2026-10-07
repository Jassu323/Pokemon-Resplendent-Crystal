"""Read-only Selected-page latency and routine-cost comparisons in SameBoy.

Inputs are normal buttons on private battery/checkpoint copies. Measurements
use rendered pixels, not a service-call count or an assumed VBlank clock.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re
import statistics

from .assets import Repository, sha256
from .cold_listing import ROOT, Driver, build_core, bootstrap, prepare_states, move, predecessor, audit
from .description_ui import settle, settle_description_text
from .description_paging import description_pages
from .info_ui import BOOT, fixture, press, ready, info_audit, type_audit
from .moves_ui import ready as moves_ready, content_audit
from .area_ui import reach, map_audit, shell_audit
from pokedex_info_assets import Compiler

T = 70224
HZ = 4194304
POINTS = {
    'idle_upload': ('PokedexPerf_IdleUpload', True),
    'activate_info': ('PokedexInfo_Activate', True),
    'info_service': ('PokedexInfo_Service', True),
    'info_initialize': ('PokedexInfo_Initialize', True),
    'info_clear': ('PokedexInfo_ClearRow', True),
    'info_stats_plan': ('PokedexInfo_PlanStats', True),
    'info_evo_plan': ('PokedexInfo_PlanEvolution', True),
    'info_copy': ('PokedexInfo_CopyTiles', True),
    'info_upload': ('PokedexInfo_UploadTiles', True),
    'info_record': ('PokedexInfo_RecordPage', True),
    'info_publish': ('Pokedex_VBlankInfoAssets', False),
    'info_preserve_return': ('PokedexInfo_PreserveReturnPanel', True),
    'cache_repair': ('Pokedex_RepairGridCache', True),
    'cache_prime': ('Pokedex_PrimeGridCache', True),
    'repair_frame0': ('PokedexPerf_RepairFrame0', True),
    'area_start': ('Pokedex_GetArea', False),
    'area_loop': ('Pokedex_GetArea.loop', False),
    'area_handoff': ('PokedexSelectedMon_Area.map_returned', False),
    'stage_selected': ('PokedexSelectedMon_StageDescription', True),
    'prepare_picture': ('Pokedex_PrepareSelectedMonTiles', True),
    'town_gfx': ('LoadTownMapGFX', True),
    'town_maps': ('TownMapBGUpdate', True),
    'town_pals': ('TownMapPals', True),
    'find_nests': ('FindNest', True),
    'area_nests': ('Pokedex_GetArea.GetAndPlaceNest', True),
    'get_base': ('GetBaseData', True),
    'selected_loop': ('PokedexSelectedMon_Update', False),
    'listing_reveal': ('Pokedex_InitMainScreen.revealed', False),
}


def core(repo, output, extra_points=None, extra_flags=()):
    output.mkdir(parents=True, exist_ok=True)
    header = (output / 'performance-symbols.h').resolve()
    lines = ['static const struct { unsigned bank, pc; const char *name; bool span; } perf_points[] = {']
    for name, (label, span) in dict(POINTS, **(extra_points or {})).items():
        if label in repo.symbols:
            bank, pc = repo.symbols[label]
            lines.append(f'{{{bank}, {pc}, "{name}", {str(span).lower()}}},')
    lines.append('};')
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
                      ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE',
                       f'-DDEX_PERFORMANCE_SYMBOLS="{header}"', *extra_flags))


def names():
    return [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower())
            for n in re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)]


def prepare(rom, sym, battery, output):
    repo = Repository(ROOT, rom, sym)
    compiled = core(repo, output)
    copied = output / 'private.sav'
    fixture(battery, copied)
    states = output / 'listing-states'
    states.mkdir(exist_ok=True)
    driver = Driver(compiled, rom, BOOT, copied, output / 'bootstrap.log')
    try:
        bootstrap(driver)
        prepare_states(driver, states, len(names()))
    finally:
        driver.close()
    config = dict(core=str(compiled.resolve()), rom=str(rom.resolve()), sym=str(sym.resolve()),
                  battery=str(copied.resolve()), states=str(states.resolve()), names=names(),
                  output=str(output.resolve()), hashes=repo.hashes)
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    return config


@lru_cache(maxsize=4)
def data(rom, sym):
    repo = Repository(ROOT, Path(rom), Path(sym))
    compiler = Compiler()
    return repo, compiler, compiler.compile()


def cycles(driver, amount, key=0):
    return driver.command(f'run 0 {int(amount)} {key}')


def cursor(driver, target):
    previous = driver.command('ui')['footer_cursor']
    for _ in range(abs(previous - target)):
        press(driver, 'right' if target > previous else 'left')


def view(driver, repo, name, target, page=0):
    cursor(driver, target)
    press(driver, 'a')
    if target == 1:
        ready(driver, None)
        while driver.command('ui')['info_page'] != page:
            target = (driver.command('ui')['info_page'] + 1) % driver.command('ui')['info_pages']
            press(driver, 'a')
            ready(driver, target)
    elif target == 2:
        moves_ready(driver, page)
    else:
        settle_description_text(driver, description_pages(repo, name)[page])


def result_timing(events, initial, final, key, pressed, accepted, completion_after=None, first_key=None):
    frames = [e for e in events if e['event'] == 'perf_frame']
    # A normal page's final stable crop excludes ongoing portrait/mini motion.
    # Area can blink marker OAM; the final two observations allow either phase.
    targets = {e[key] for e in frames[-2:]} | {final[key]}
    first_key = first_key or key
    changed = [e for e in frames if e['t'] >= accepted and e[first_key] != initial[first_key]]
    complete = [e for e in frames if e['t'] >= max(accepted, completion_after or accepted) and e[key] in targets]
    noop = not changed and final[key] == initial[key]
    def interval(event):
        if event is None:
            return None
        elapsed = event['t'] - pressed
        return dict(cycles=elapsed, ms=elapsed * 1000 / HZ, frames=elapsed / T,
                    displayed_frames=event['display'])
    first = changed[0] if changed else None
    done = complete[0] if complete and not noop else None
    costs = defaultdict(list)
    for event in events:
        if event['event'] == 'perf_cost':
            costs[event['name']].append(event['elapsed'])
    return dict(first_visible=interval(first), complete_visible=interval(done), no_pixel_change=noop,
                input_accept_ms=(accepted - pressed) * 1000 / HZ,
                input_accept_frames=(accepted - pressed) / T,
                costs={name: dict(calls=len(rows), total_cycles=sum(rows), maximum=max(rows),
                                  ms=sum(rows) * 1000 / HZ) for name, rows in costs.items()},
                rendered_frames=len(frames))


def run_case(job):
    config, name, action, phase, page, input_phase = job
    repo, compiler, generated = data(config['rom'], config['sym'])
    label = f'{name}-{action}-{phase}-p{page}-q{input_phase}'
    out = Path(config['output']) / 'measurements'
    out.mkdir(exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], out / (label + '.log'))
    result = dict(species=name, action=action, phase=phase, page=page, input_phase=input_phase, issues=[])
    try:
        index = config['names'].index(name)
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.command('audit 1')
        driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        if phase == 'settled':
            settle(driver)
        else:
            driver.run(('animation_miss', 'audio_miss'), frames=int(phase))
        if action.startswith('moves-'):
            view(driver, repo, name, 2)
        elif action.startswith('info-') or action in ('cycle', 'rapid', 'listing', 'species'):
            view(driver, repo, name, 1, page)
        if action in ('info-description-listing', 'info-moves-listing'):
            view(driver, repo, name, 0 if action == 'info-description-listing' else 2)
        if action == 'info-area-return':
            cursor(driver, 3)
            driver.run(('footer_accept',), key='a')
            reach(driver, repo, 'Pokedex_GetArea.loop')
            driver.run(frames=3)
        elif action.endswith('area'):
            cursor(driver, 3)
        elif action.endswith('info'):
            cursor(driver, 1)
        if input_phase:
            cycles(driver, input_phase)
        before = driver.command('peek')
        result['playback_at_input'] = {k: before[k] for k in ('playback', 'audio', 'remaining', 'sfx', 'ly')}
        initial = driver.command('perf 1')
        result['initial_hashes'] = initial
        driver.events.clear()
        pressed = initial['t']
        if action in ('description-info', 'moves-info', 'cycle'):
            target_page = (page + 1) % driver.command('ui')['info_pages'] if action == 'cycle' else 0
            accepted = driver.run(('footer_accept', 'animation_miss', 'audio_miss'), key='a')
            driver.run(('animation_miss', 'audio_miss'), frames=1)
            ready(driver, target_page)
            ui = driver.command('ui')
            result['issues'] += info_audit(compiler, generated, name, ui['info_page'], ui, repo)
            result['issues'] += type_audit(repo, name, ui)
            hash_key = 'lower'
        elif action == 'rapid':
            accepted = driver.run(('footer_accept', 'animation_miss', 'audio_miss'), key='a')
            driver.run(('animation_miss', 'audio_miss'), frames=2)
            # Fifteen separate 2-on/2-off presses, not one held key.
            for _ in range(14):
                driver.run(('animation_miss', 'audio_miss'), frames=2, key='a')
                driver.run(('animation_miss', 'audio_miss'), frames=2)
            result['last_release_t'] = driver.command('peek')['t']
            ready(driver, None)
            ui = driver.command('ui')
            result['final_page'] = ui['info_page']
            result['issues'] += info_audit(compiler, generated, name, ui['info_page'], ui, repo)
            hash_key = 'lower'
        elif action in ('description-area', 'moves-area', 'info-area'):
            accepted = driver.run(('footer_accept', 'animation_miss', 'audio_miss'), key='a')
            ready_at = reach(driver, repo, 'Pokedex_GetArea.loop')
            result['ready_t'] = ready_at['t']
            driver.run(frames=3)
            issues, _ = map_audit(repo, index, driver.command('area'), driver.command('ui'))
            result['issues'] += issues
            hash_key = 'full'
        elif action == 'info-area-return':
            handoff = reach(driver, repo, 'PokedexSelectedMon_Area.map_returned', 32)
            accepted = handoff
            restored = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            result['ready_t'] = restored['t']
            driver.run(frames=2)
            ui = driver.command('ui')
            result['issues'] += info_audit(compiler, generated, name, page, ui, repo) + shell_audit(ui)
            hash_key = 'stable'
        elif action == 'listing' or action.endswith('-listing'):
            accepted = driver.run(('leave', 'animation_miss', 'audio_miss'), key='b')
            restored = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            result['ready_t'] = restored['t']
            driver.run(frames=3)
            if restored['index'] != index:
                result['issues'].append('listing_index')
            hash_key = 'stable'
        elif action == 'species':
            accepted = driver.run(('change_species', 'animation_miss', 'audio_miss'), key='down' if index < 372 else 'up')
            driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            ready(driver, 0)
            target = driver.command('peek')['selected_index']
            ui = driver.command('ui')
            result['target'] = config['names'][target]
            result['issues'] += info_audit(compiler, generated, result['target'], 0, ui, repo)
            hash_key = 'stable'
        else:
            raise ValueError(action)
        driver.run(('animation_miss', 'audio_miss'), frames=2)
        events = list(driver.events)
        final = driver.command('perf 0')
        result.update(result_timing(events, initial, final, hash_key, pressed, accepted['t'],
                                    result.get('last_release_t'),
                                    first_key='full' if action == 'species' or action == 'listing' or action.endswith('-listing') else hash_key))
        if action == 'rapid':
            publishes = [e for e in events if e['event'] == 'perf_phase' and e['name'] == 'info_publish']
            result['publications_during_presses'] = sum(e['t'] < result['last_release_t'] for e in publishes)
            result['publication_count'] = len(publishes)
            result['activation_count'] = sum(e['event'] == 'perf_phase' and e['name'] == 'activate_info'
                                             for e in events)
            expected = (page + result['activation_count']) % ui['info_pages']
            result['expected_final_page'] = expected
            if result['final_page'] != expected:
                result['issues'].append('rapid_request_count')
            if result['complete_visible']:
                result['after_last_release_frames'] = (pressed + result['complete_visible']['cycles'] - result['last_release_t']) / T
        result['issues'] += [e['event'] for e in events if e['event'] in ('animation_miss', 'audio_miss')]
        (out / (label + '-trace.json')).write_text(json.dumps(events, separators=(',', ':')))
        # Complete remaining playback and audit its exact physical timeline.
        if action in ('description-info', 'moves-info', 'cycle', 'rapid', 'species'):
            settle(driver)
            if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
                result['issues'].append('playback_miss_after_measurement')
        result['status'] = 'pass' if not result['issues'] else 'fail'
    except Exception as error:
        result.update(status='error', error=str(error))
        driver.evidence(out / (label + '-failure'))
    finally:
        driver.close()
    (out / (label + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['action'], row['phase'])].append(row)
    result = []
    for (action, phase), cases in sorted(groups.items()):
        entry = dict(action=action, phase=phase, cases=len(cases), errors=[r for r in cases if r['status'] != 'pass'])
        for metric in ('first_visible', 'complete_visible'):
            values = [r[metric]['frames'] for r in cases if r.get(metric)]
            if values:
                entry[metric] = dict(min_frames=min(values), median_frames=statistics.median(values), max_frames=max(values),
                    min_ms=min(values)*T/HZ*1000, median_ms=statistics.median(values)*T/HZ*1000, max_ms=max(values)*T/HZ*1000)
        result.append(entry)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--battery', type=Path, default=Path('/Applications/SameBoy/Games/pokecrystal.sav'))
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--config', type=Path, help='Reuse matching checkpoints without replacing their earlier results')
    parser.add_argument('--species', nargs='+', default=['chikorita', 'dusknoir', 'weavile', 'eevee'])
    parser.add_argument('--actions', nargs='+', default=['description-info', 'moves-info', 'description-area',
        'moves-area', 'info-area', 'info-area-return', 'listing', 'cycle', 'rapid', 'species'])
    parser.add_argument('--phases', nargs='+', default=['0', 'settled'])
    parser.add_argument('--input-phases', nargs='+', type=int, default=[0])
    parser.add_argument('--all-info-pages', action='store_true')
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = prepare(args.rom, args.sym, args.battery, output) if args.prepare else json.loads((args.config or output / 'config.json').read_text())
    config = dict(config, output=str(output))
    _, _, generated = data(config['rom'], config['sym'])
    tasks = []
    for name in dict.fromkeys(args.species):
        constant = {'unown_a': 'UNOWN', 'porygonz': 'PORYGON_Z'}.get(name, name.upper())
        count = 1 + (len(generated['roots'][constant]) + 1) // 2
        for action in args.actions:
            pages = range(count) if args.all_info_pages and action in ('listing', 'cycle', 'info-area-return', 'info-area') else [0]
            tasks.extend((config, name, action, phase, page, q) for page in pages for phase in args.phases for q in args.input_phases)
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(run_case, tasks):
            rows.append(row)
            if len(rows) % 50 == 0 or row['status'] != 'pass':
                print(json.dumps(dict(done=len(rows), total=len(tasks), species=row['species'], action=row['action'], status=row['status'],
                                     issues=row['issues'], error=row.get('error'))), flush=True)
    report = dict(provenance=config, cases=len(rows), failures=sum(r['status'] != 'pass' for r in rows),
                  summary=summarize(rows), results=rows)
    (output / 'performance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=report['cases'], failures=report['failures'], summary=report['summary'])), flush=True)
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
