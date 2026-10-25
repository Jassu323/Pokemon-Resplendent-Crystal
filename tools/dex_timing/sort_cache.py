"""Cross-order grid-cache regression using matching normal-input checkpoints."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from .assets import Repository
from .cold_listing import ROOT, Driver, move
from .info_ui import BOOT, press
from .listing_options import LABELS, choose, configuration, listing_audit, order_audit, popup

POSITIONS = (*range(10), 150, 372)


def prepare(config, manifest, output):
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'prepare.log')
    try:
        for mode in range(3):
            driver.command(f'load {config["states"]}/listing-000.s0')
            choose(driver, mode)
            order = order_audit(driver, repo, manifest['orders'][LABELS[mode]])
            listing_audit(driver, repo, order)
            base = output / f'base-{mode}.s0'
            driver.command(f'save {base}')
            for position in POSITIONS:
                driver.command(f'load {base}')
                if position == 372:
                    route = ('up',)
                elif config['listing_style'] == 'legacy':
                    route = ('down',) * position
                else:
                    route = ('right',) * (position % 3) + ('down',) * (position // 3)
                for key in route:
                    move(driver, key)
                    driver.run(('end_loop',))
                    driver.run(('end_loop',))
                if driver.command('peek')['index'] != position:
                    raise RuntimeError('Checkpoint navigation missed its target')
                listing_audit(driver, repo, order)
                driver.command(f'save {output / f"{mode}-{position:03}.s0"}')
    finally:
        driver.close()


def case(task):
    config, manifest, output, initial, position, target, phase, warm = task
    output = Path(output)
    name = f'{initial}-{position:03}-{target}-q{phase}-w{int(warm)}'
    result = dict(initial=initial, position=position, target=target, phase=phase,
                  warm=warm, presentation=config['listing_style'], issues=[])
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    try:
        driver.command(f'load {output / f"{initial}-{position:03}.s0"}')
        original = driver.command('peek')
        listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[initial]]))
        driver.command('audit 1')
        if warm:
            driver.run(('animation_miss', 'audio_miss'), frames=120)
        press(driver, 'start')
        popup(driver, 0, 0)
        press(driver, 'a')
        popup(driver, 1, initial)
        for _ in range(abs(target - initial)):
            press(driver, 'down' if target > initial else 'up')
        driver.run(frames=2 + phase / 8)
        press(driver, 'a')
        returned = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        if returned['hit'] != 'listing' or returned['mode'] != target:
            raise RuntimeError('Sort did not finish in its Listing owner')
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        state = driver.command('peek')
        expected = tuple(original[key] for key in ('index', 'cursor', 'scroll')) if target == initial else (0, 0, 0)
        if tuple(state[key] for key in ('index', 'cursor', 'scroll')) != expected:
            raise RuntimeError('Sort cursor/viewport policy failed')
        order = order_audit(driver, repo, manifest['orders'][LABELS[target]])
        listing_audit(driver, repo, order)
        # Neither icon animation nor the first wrap/refill may repair a page
        # that was wrong at reveal. Audit immediately and again after each.
        driver.run(('animation_miss', 'audio_miss'), frames=32)
        listing_audit(driver, repo, order)
        for key in ('up', 'down', 'down', 'down', 'down', 'up', 'up', 'up'):
            move(driver, key)
            driver.run(('end_loop',))
            driver.run(('end_loop',))
            listing_audit(driver, repo, order)
        for repeated in ((target + 1) % 3, (target + 2) % 3, target):
            choose(driver, repeated)
            listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[repeated]]))
        if any(event['event'] in ('animation_miss', 'audio_miss') for event in driver.events):
            raise RuntimeError('Playback miss during sort/cache stress')
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
        driver.evidence(output / (name + '-error'))
    finally:
        driver.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=10)
    parser.add_argument('--presentation', choices=('modern', 'legacy'), default='modern')
    args = parser.parse_args()
    build = args.output.resolve()
    if not build.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    config = configuration(build, args.presentation)
    manifest = json.loads((build / 'sort-manifest.json').read_text())
    output = build / ('sort-cache-qualification-legacy' if args.presentation == 'legacy'
                      else 'sort-cache-qualification')
    output.mkdir(exist_ok=True)
    prepare(config, manifest, output)
    tasks = [(config, manifest, str(output), initial, position, target, phase, warm)
             for initial in range(3) for position in POSITIONS for target in range(3)
             for phase in range(8) for warm in (False, True)]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(case, tasks):
            results.append(result)
            if len(results) % 100 == 0 or result['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), result=result)), flush=True)
    summary = dict(cases=len(results), failures=sum(bool(row['issues']) for row in results), results=results)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'results'}))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
