"""Sequential two-worker lanes for the private battle-discovery regression."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def tasks(output, baseline, lane):
    out, old = str(output), str(baseline)
    common = ['--output', out, '--baseline', old]
    jobs = ['--jobs', '2']
    if lane == 'discovery':
        return [('move_battle_use', ['--output', out, '--only', 'semantic', *jobs]),
                ('battle_use_campaign', ['data', *common, '--start', '4']),
                ('battle_use_review', ['--output', out]),
                ('move_battle_use', ['--output', out, '--only', 'semantic', '--kinds', 'bide', *jobs])]
    if lane == 'dex':
        return [('performance_regression', ['--config', str(output / 'legacy/config.json'),
                 '--output', str(output / 'regression-legacy'), '--suites', 'info', 'moves', 'cold',
                 'paging', 'warm', 'area', 'info-stress', 'moves-stress', *jobs, '--expected-double-speed']),
                ('performance_regression', ['--config', str(output / 'modern/config.json'),
                 '--output', str(output / 'regression-modern-warm'), '--suites', 'warm', *jobs,
                 '--expected-double-speed'])]
    if lane == 'ui':
        return [('moves_mode', [*common, *jobs]),
                ('moves_scrollbar', ['--output', out, *jobs]),
                ('moves_scrollbar', ['--output', out, '--mixed', *jobs]),
                ('listing_options', ['integration', '--output', out, *jobs]),
                ('listing_options', ['modal', '--output', out, *jobs]),
                ('search_ranked', ['--source', out, '--output', str(output / 'search-qualification'), *jobs]),
                ('search_ranked', ['--source', out, '--output', str(output / 'search-sparse'), '--sparse', *jobs]),
                ('search_ranked', ['--source', out, '--output', str(output / 'search-stress'), '--stress', *jobs]),
                ('search_results', ['--source', out, '--output', str(output / 'search-results-qualification'), *jobs]),
                ('search_results', ['--source', out, '--output', str(output / 'search-results-badges'), '--badges', *jobs]),
                ('search_qualification', ['--source', out, '--defaults', *jobs]),
                ('search_qualification', ['--source', out, '--returns', *jobs]),
                ('mode_transitions', ['--output', out, '--indices', '0,8,254,372', '--phases', '4', *jobs])]
    return [('move_acquisition', ['--output', out, *jobs]),
            ('move_acquisition', ['--output', out, '--sources', *jobs]),
            ('move_acquisition', ['--output', out, '--migration', *jobs]),
            ('move_acquisition', ['--output', out, '--interruptions', *jobs]),
            ('acquisition_regression', ['audio', *common, *jobs]),
            ('acquisition_regression', ['gameplay', *common, *jobs]),
            ('acquisition_regression', ['custom', *common, *jobs]),
            ('acquisition_regression', ['transitions', *common, *jobs]),
            ('acquisition_report', ['readiness', *common]),
            ('acquisition_performance', common),
            ('acquisition_report', ['review', '--output', out])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lane', choices=('dex', 'ui', 'data', 'discovery'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--start', type=int, default=0)
    args = parser.parse_args()
    output, baseline = args.output.resolve(), args.baseline.resolve()
    folder = output / 'campaign'
    folder.mkdir(exist_ok=True)
    records = []
    env = dict(os.environ, PYTHONPATH='tools')
    for n, (module, options) in enumerate(tasks(output, baseline, args.lane)):
        if n < args.start:
            continue
        print(json.dumps(dict(lane=args.lane, step=n, module=module, state='running')), flush=True)
        log = folder / f'{args.lane}-{n:02}-{module}.log'
        with log.open('w') as stream:
            result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + module, *options],
                                    env=env, stdout=stream, stderr=subprocess.STDOUT)
        records.append(dict(module=module, step=n, exit_code=result.returncode, log=str(log)))
        (folder / f'{args.lane}.json').write_text(json.dumps(records, indent=2) + '\n')
        print(json.dumps(dict(lane=args.lane, step=n, state='passed' if not result.returncode else 'failed')), flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
