"""Held-D-pad Listing cadence and visible cache checks on private ROM copies."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics

from .assets import Repository
from .cold_listing import Driver, ROOT
from .info_ui import BOOT
from .listing_restoration import compile_observer, listing_snapshot, check_listing_snapshot
from .performance import T, HZ


def run_case(job):
    config, index, direction = job
    out = Path(config['output']) / f'{index:03}-{direction}'
    out.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], out / 'core.log')
    reference = Driver(config['core'], config['rom'], BOOT, config['battery'], out / 'reference.log')
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.run(('end_loop',), frames=10)
        start = driver.command('peek')
        previous = start['index']
        changes = []
        while driver.command('peek')['t'] - start['t'] < 120 * T:
            state = driver.run(('end_loop',), frames=20, key=direction)
            if state['hit'] != 'end_loop':
                raise RuntimeError('Listing loop stalled while holding D-pad')
            if state['index'] != previous:
                changes.append(dict(t=state['t'] - start['t'], index=state['index']))
                previous = state['index']
        driver.run(frames=5)
        actual = listing_snapshot(driver, out / 'final')
        target = min(actual['listing_scroll'] + 6, len(config['names']) - 1)
        reference.command(f'load {config["states"]}/listing-{target:03}.s0')
        expected = listing_snapshot(reference, out / 'reference')
        issues = check_listing_snapshot(actual, expected, len(config['names']), all_rows=False)
        if not changes:
            issues.append('no_scroll_changes')
        gaps = [b['t'] - a['t'] for a, b in zip(changes, changes[1:])]
        result = dict(index=index, direction=direction, changes=changes, issues=issues,
                      accepted=len(changes), first_ms=changes[0]['t']*1000/HZ if changes else None,
                      first_frames=changes[0]['t']/T if changes else None,
                      median_gap_frames=statistics.median(gaps)/T if gaps else None,
                      maximum_gap_frames=max(gaps)/T if gaps else None)
        driver.command(f'image {out / "final.ppm"}')
    finally:
        driver.close()
        reference.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    binary = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', args.output)
    config.update(core=str(binary), output=str(args.output.resolve()))
    tasks = [(config, index, direction) for index in (0, 180, len(config['names']) - 1)
             for direction in ('up', 'down')]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(run_case, tasks))
    report = dict(results=results, failures=sum(bool(r['issues']) for r in results))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
