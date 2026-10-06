"""Parallel regressions sharing only matching, normal-input checkpoints."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from functools import partial
from pathlib import Path

from . import cold_listing, info_ui, moves_ui, area_ui
from .assets import Repository
from .cold_listing import ROOT
from .info_ui import BOOT

BASE_AUDIT = cold_listing.audit


def run(job):
    suite, task = job
    expected = task[0].get('expected_double_speed', 0)
    for module in (cold_listing, info_ui, moves_ui, area_ui):
        module.audit = partial(BASE_AUDIT, expected_double_speed=expected)
        if task[0].get('listing_style') == 'legacy':
            module.predecessor = partial(legacy_predecessor, count=len(task[0]['names']))
    function = {'info': info_ui.run_case, 'info-stress': info_ui.run_stress,
                'moves': moves_ui.run_case, 'moves-stress': moves_ui.run_stress,
                'cold': cold_listing.run_case, 'paging': cold_listing.run_case, 'warm': cold_listing.run_case,
                'area': area_ui.run_case}[suite]
    result = function(task)
    return dict(suite=suite, result=result,
                passed=not result.get('issues') and result.get('status', 'pass') == 'pass'
                and result.get('return_to_listing', 'pass') == 'pass')


def legacy_predecessor(index, count=373):
    if index == count - 1 and count > 1:
        return (0, 'up')
    return ((index - 1) % count, 'down')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suites', nargs='+', default=['info', 'moves', 'cold', 'paging', 'area', 'info-stress', 'moves-stress'])
    parser.add_argument('--jobs', type=int, default=20)
    parser.add_argument('--expected-double-speed', action='store_true',
                        help='Require speed 1 at both accepted input and playback completion')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    config['expected_double_speed'] = int(args.expected_double_speed)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    assets = {asset.name: asset for asset in repo.load(config['names'])}
    tasks = []
    important = {'chikorita', 'meganium', 'dusknoir', 'weavile', 'luxray', 'garchomp',
                 'bastiodon', 'rampardos', 'kyogre', 'groudon', 'rayquaza', 'metagross',
                 'chansey', 'snorlax', 'unown_a', 'seviper', 'eevee', 'tyrogue', 'exeggcute', 'mewtwo'}
    for suite in args.suites:
        output = (args.output / suite).resolve()
        output.mkdir(parents=True, exist_ok=True)
        local = dict(config, output=str(output), boot=str(BOOT), uncaught=False, paging=suite == 'paging',
                     warm=suite == 'warm', follow_up=True, repeat_area=True)
        if suite in ('cold', 'paging', 'warm'):
            (output / 'listing-states').symlink_to(config['states'], target_is_directory=True)
        for index, name in enumerate(config['names']):
            if suite in ('cold', 'paging', 'warm'):
                tasks.append((suite, (local, index, assets[name])))
            elif suite in ('info', 'moves'):
                for phase in (('0', '8', '32', 'settled') if suite == 'info' else ('0', 'settled')):
                    tasks.append((suite, (local, index, name, phase)))
            elif suite in ('info-stress', 'moves-stress') and name in important:
                families = ('mash-a', 'hold-a', 'description', 'listing', 'species') if suite == 'info-stress' else ('mash-a', 'hold-a', 'description', 'listing', 'species', 'a-b', 'info')
                for phase in ('0', '8', '32', 'settled'):
                    for family in families:
                        tasks.append((suite, (local, index, name, phase, family)))
            elif suite == 'area':
                for view in ('description', 'info', 'moves'):
                    for phase in ('0', 'settled'):
                        tasks.append((suite, (local, name, view, phase, 'b', 0)))
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(run, tasks):
            results.append(result)
            if len(results) % 100 == 0 or not result['passed']:
                print(json.dumps(dict(done=len(results), total=len(tasks), suite=result['suite'],
                                     passed=result['passed'], species=result['result'].get('species'),
                                     issues=result['result'].get('issues'), error=result['result'].get('error'))), flush=True)
    summary = {suite: dict(cases=sum(r['suite'] == suite for r in results),
                           failures=sum(r['suite'] == suite and not r['passed'] for r in results)) for suite in args.suites}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'summary.json').write_text(json.dumps(dict(summary=summary, results=results), indent=2) + '\n')
    print(json.dumps(summary))
    return int(any(not r['passed'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
