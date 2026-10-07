"""A/B Results page latency, measured from input to first/final changed pixels."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from PIL import Image

from . import performance
from .area_ui import reach
from .assets import Repository
from .cold_listing import ROOT, Driver, KEY
from .info_ui import BOOT, press
from .search_qualification import choose_types, named_types
from .search_ranked import prepare


def run_case(task):
    config, query, kind, target = task
    output = Path(target)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    name = f'{config["listing_style"]}-{config["order"]}-{query[0]}-{kind}'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    result = dict(presentation=config['listing_style'], order=config['order'], query=query,
                  kind=kind, issues=[])
    try:
        driver.command(f'load {config["checkpoint"]}')
        choose_types(driver, repo, *named_types(repo, *query))
        press(driver, 'down')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen', KEY['a'])
        driver.run(frames=4)
        if kind == 'scroll':
            for _ in range(3):
                press(driver, 'down')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
        driver.events.clear()
        prefix = output / name
        driver.command(f'image {prefix}-before.ppm')
        before = driver.command('perf 1')
        driver.command(f'perfimages {prefix}')
        driver.run(frames=2, key='down')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
        driver.run(frames=4)
        driver.command('perfimages -')
        driver.command('perf 0')
        with Image.open(str(prefix) + '-before.ppm') as image:
            original = image.tobytes()
        frames = [event for event in driver.events if event['event'] == 'perf_frame']
        pixels = []
        for frame in frames:
            with Image.open(f'{prefix}-{frame["display"]:03}.ppm') as image:
                pixels.append(image.tobytes())
        first = next(i for i, pixels in enumerate(pixels) if pixels != original)
        complete = next(i for i, image in enumerate(pixels) if image == pixels[-1])
        for label, index in (('first', first), ('complete', complete)):
            elapsed = frames[index]['boundary_t'] - before['t']
            result[label] = dict(ms=elapsed * 1000 / performance.HZ, frames=elapsed / performance.T)
        result['end_index'] = driver.command('peek')['index']
        if result['end_index'] != (4 if kind == 'scroll' else 1):
            raise RuntimeError('Latency trial did not move exactly one result')
        result['costs'] = [e for e in driver.events if e['event'] == 'perf_cost']
        (output / (name + '.json')).write_text(json.dumps(dict(result=result, events=driver.events), indent=2) + '\n')
    except (RuntimeError, ValueError, StopIteration) as error:
        result['issues'].append(str(error) or type(error).__name__)
        driver.evidence(output / (name + '-error'))
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
    configs = prepare(args.source.resolve(), output)
    repo = Repository(ROOT, Path(configs[0]['rom']), Path(configs[0]['sym']))
    compiled = performance.core(repo, output / 'timing-core', {
        'results_scroll': ('PokedexResults_Scroll', True),
        'old_results_listing': ('Pokedex_PrintListing', True),
    })
    for config in configs:
        config['core'] = str(compiled)
    tasks = [(config, query, kind, str(output)) for config in configs
             for query in (('NORMAL', None), ('WATER', 'ICE'), ('GRASS', None))
             for kind in ('cursor', 'scroll')]
    with ProcessPoolExecutor(max_workers=min(args.jobs, 6)) as pool:
        rows = list(pool.map(run_case, tasks))
    summary = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows), results=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'results'}))
    for row in rows:
        if row['issues']:
            print(json.dumps(row))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
