"""Time Search filtering, authored delay and visible Results with normal inputs."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from . import performance
from .area_ui import reach
from .assets import Repository
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT, press
from .legacy_listing import private_battery
from .listing_options import configuration, LABELS
from .search_qualification import choose_types, named_types


def interval(cycles):
    return dict(ms=cycles * 1000 / performance.HZ, frames=cycles / performance.T)


def run_case(task):
    config, count, mode, values, name, target = task
    output = Path(target)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    label = f'{count}-{mode}-{name}'
    battery = output / (label + '.sav')
    private_battery(config, battery, presentation=0, order_mode=mode,
                    unseen=tuple(range(count, len(config['names']))))
    driver = Driver(config['core'], config['rom'], BOOT, battery, output / (label + '.log'))
    result = dict(seen=count, mode=LABELS[mode], types=name, issues=[])
    try:
        bootstrap(driver, expected_mode=mode)
        driver.run(frames=4)
        result['scanned_slots'] = driver.command('peek')['end']
        press(driver, 'start')
        press(driver, 'down')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['a'])
        driver.run(frames=2)
        choose_types(driver, repo, *values)
        press(driver, 'up')
        press(driver, 'down')
        press(driver, 'down')
        driver.run(frames=4)
        driver.events.clear()
        before = driver.command('perf 1')
        reach(driver, repo, 'AnimateDexSearchSlowpoke', KEY['a'])
        bank, address = repo.symbols['wDexSearchResultCount']
        result['matches'] = int.from_bytes(bytes.fromhex(
            driver.command(f'perfram {bank} {address} 2')['bytes']), 'little')
        if result['matches']:
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            driver.run(frames=2)
            final_point = 'results_init'
        else:
            reach(driver, repo, 'Pokedex_DisplayTypeNotFoundMessage')
            driver.run(frames=12)
            final_point = 'no_match'
        driver.command('perf 0')
        events = driver.events
        phases = [event for event in events if event['event'] == 'perf_phase']
        costs = [event for event in events if event['event'] == 'perf_cost']
        frames = [event for event in events if event['event'] == 'perf_frame']
        accepted = next(event['t'] for event in phases if event['name'] == 'search_accept')
        for name in ('filter', 'slowpoke', 'results_init'):
            measured = [event['elapsed'] for event in costs if event['name'] == name]
            if measured:
                result[name] = interval(sum(measured))
        result['input_accept'] = interval(accepted - before['t'])
        result['algorithm_done'] = interval(next(
            event['t'] + event['elapsed'] for event in costs if event['name'] == 'filter') - before['t'])
        first = next(event for event in frames if event['lower'] != before['lower'])
        result['first_motion'] = interval(first['boundary_t'] - before['t'])
        final_start = next(event['t'] for event in phases if event['name'] == final_point)
        final = next(event for event in frames
                     if event['boundary_t'] >= final_start and event['full'] == frames[-1]['full'])
        result['visible_result' if result['matches'] else 'visible_no_match'] = interval(
            final['boundary_t'] - before['t'])
        result['animation_to_final_pixels'] = interval(final['boundary_t'] - next(
            event['t'] + event['elapsed'] for event in costs if event['name'] == 'slowpoke'))
        (output / (label + '.json')).write_text(json.dumps(dict(result=result, events=events), indent=2) + '\n')
    except (RuntimeError, ValueError, StopIteration) as error:
        result['issues'].append(str(error) or type(error).__name__)
        driver.evidence(output / (label + '-error'))
    finally:
        driver.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh private build/ output')
    output.mkdir(parents=True)
    config = configuration(args.source.resolve())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    config['core'] = str(performance.core(repo, output / 'core', {
        'search_accept': ('Pokedex_UpdateSearchScreen.MenuAction_BeginSearch', False),
        'filter': ('Pokedex_SearchForMons', True),
        'slowpoke': ('AnimateDexSearchSlowpoke', True),
        'results_init': ('Pokedex_InitSearchResultsScreen', True),
        'results_ready': ('Pokedex_UpdateSearchResultsScreen', False),
        'no_match': ('Pokedex_DisplayTypeNotFoundMessage', True),
    }))
    choices = ((*named_types(repo, 'GRASS'), 'Grass'),
               (*named_types(repo, 'WATER', 'FLYING'), 'Water-Flying'),
               (*named_types(repo, 'FIRE', 'NORMAL'), 'Fire-Normal'))
    tasks = [(config, count, mode, (one, two), name, str(output))
             for count in (5, 50, len(config['names']))
             for mode in range(3) for one, two, name in choices]
    with ProcessPoolExecutor(max_workers=min(args.jobs, 6)) as pool:
        rows = list(pool.map(run_case, tasks))
    summary = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows),
                   rom_sha256=repo.hashes['rom_sha256'], results=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
