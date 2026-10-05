"""Normal-input cache-content checks for the private frame-0 repair prototype."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import shutil

from .assets import Repository
from .cold_listing import Driver, ROOT, move, predecessor
from .description_ui import settle
from .info_ui import BOOT, press, ready
from .listing_restoration import compile_observer, follow_up
from pokedex_info_assets import Compiler


def run_case(job):
    config, name, page, distance, cancel_age = job
    label = f'{name}-p{page}-down{distance}-cancel{cancel_age}'
    output = Path(config['output']) / label
    output.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'core.log')
    reference = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'reference.log')
    result = dict(species=name, page=page, distance=distance, cancel_age=cancel_age, issues=[])
    try:
        index = config['names'].index(name)
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        move(driver, direction, index)
        driver.run(('accept',), key='a')
        driver.run(('selected',), frames=600)
        settle(driver)
        press(driver, 'right')
        if cancel_age is None:
            press(driver, 'a')
            ready(driver, 0)
            for next_page in range(1, page + 1):
                press(driver, 'a')
                ready(driver, next_page)
        else:
            driver.run(frames=1, key='a')
            if cancel_age:
                driver.run(frames=cancel_age)
        for _ in range(distance):
            driver.run(frames=2)
            changed = driver.run(('change_species',), key='down')
            if changed['hit'] != 'change_species':
                raise RuntimeError('Internal paging was not accepted')
            driver.run(('selected',), frames=600)
            ready(driver, 0)
            settle(driver)
        driver.run(frames=2)
        left = driver.run(('leave',), key='b')
        returned = driver.run(('listing',), frames=600)
        if left['hit'] != 'leave' or returned['hit'] != 'listing':
            raise RuntimeError('B-return did not finish')
        driver.run(frames=5)
        result['follow_up'] = follow_up(driver, reference, Path(config['checkpoints']),
                                        output / 'follow-up', len(config['names']),
                                        require_lookahead=config['require_lookahead'])
        result['issues'] += result['follow_up']['issues']
    except Exception as error:
        result['issues'].append(f'{type(error).__name__}: {error}')
    finally:
        driver.close()
        reference.close()
    (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    if config.get('compress_traces'):
        for path in output.rglob('*.jsonl'):
            with path.open('rb') as source, gzip.open(str(path) + '.gz', 'wb', compresslevel=1) as target:
                shutil.copyfileobj(source, target)
            path.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--compress-traces', action='store_true',
                        help='Losslessly compress retained snapshots and navigation traces')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    if repo.hashes != config['hashes']:
        raise ValueError('Checkpoints do not match the candidate cartridge')
    binary = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', args.output)
    checkpoints = args.output / 'checkpoints'
    checkpoints.mkdir(exist_ok=True)
    (checkpoints / 'listing-states').symlink_to(config['states'], target_is_directory=True)
    config.update(core=str(binary), output=str(args.output.resolve()), checkpoints=str(checkpoints.resolve()),
                  compress_traces=args.compress_traces,
                  require_lookahead='PokedexPerf_PrepareIncomingGridRow' not in repo.symbols)
    data = Compiler().compile()
    targets = args.species or config['names']
    important = {'chikorita', 'eevee', 'tyrogue', 'dusknoir', 'weavile', 'luxray', 'garchomp',
                 'bastiodon', 'rampardos', 'groudon', 'kyogre', 'metagross', 'chansey',
                 'unown_a', 'seviper', 'exeggcute', 'mewtwo', config['names'][-1]}
    tasks = []
    for name in targets:
        constant = {'unown_a': 'UNOWN', 'porygonz': 'PORYGON_Z'}.get(name, name.upper())
        pages = 1 + (len(data['roots'][constant]) + 1) // 2
        tasks += [(config, name, page, 0, None) for page in range(pages)]
        if name in important:
            remaining = len(config['names']) - 1 - config['names'].index(name)
            tasks += [(config, name, 0, distance, None)
                      for distance in (1, 9, 30) if distance <= remaining]
            tasks += [(config, name, 0, 0, age) for age in (0, 1, 3, 6)]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(run_case, tasks):
            results.append(row)
            if len(results) % 50 == 0 or row['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), species=row['species'],
                                      issues=row['issues'])), flush=True)
    failed = [row for row in results if row['issues']]
    summary = dict(cases=len(results), failures=len(failed), results=results)
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), failures=len(failed))), flush=True)
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
