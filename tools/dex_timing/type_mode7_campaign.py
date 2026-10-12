"""Run the established full regression independently for either Type variant."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .cold_listing import ROOT

BASE = ROOT / 'build/dex-types-mode7-20261012'
PHASES = ('setup', 'dex', 'moves', 'persistence', 'discovery', 'gameplay',
          'battle-discovery', 'timing', 'readiness', 'host', 'historical-host',
          'gift', 'chart', 'diagnose-types')


def run(variant, phases=None):
    source = BASE / variant
    output = BASE / (variant + '-regression')
    result_path = output / 'phase-results.json'
    results = json.loads(result_path.read_text()) if phases and result_path.exists() else []
    for phase in phases or PHASES + ('arrows', 'report'):
        command = [sys.executable, '-m', 'tools.dex_timing.' +
                   ('dex_arrow_cursors' if phase == 'arrows' else 'type_full_regression')]
        if phase != 'arrows':
            command.append(phase)
        command += ['--output', str(source if phase == 'arrows' else output)]
        started = time.monotonic()
        print(json.dumps(dict(variant=variant,phase=phase,start=True)),flush=True)
        previous = next((row for row in results if row['phase']==phase),None)
        attempts = (previous.get('previous_attempts',[]) +
                    [{k:v for k,v in previous.items() if k!='previous_attempts'}]) if previous else []
        log_path = output / (f'{phase}-retry-{len(attempts)}-run.log' if attempts else f'{phase}-run.log')
        with log_path.open('w') as log:
            result = subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        row = dict(phase=phase,exit_code=result.returncode,seconds=round(time.monotonic()-started,2))
        row['log'] = str(log_path)
        if previous:
            row['previous_attempts'] = attempts
        # A selected retry can finish while unrelated phases are still running.
        # Merge only this phase, not the status snapshot loaded at startup.
        with (output / 'phase-results.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            results = json.loads(result_path.read_text()) if result_path.exists() else []
            current = next((r for r in results if r['phase'] == phase), None)
            if current:
                results[results.index(current)] = row
            else:
                results.append(row)
            temporary = output / f'phase-results-{os.getpid()}.tmp'
            temporary.write_text(json.dumps(results, indent=2) + '\n')
            temporary.replace(result_path)
            fcntl.flock(lock, fcntl.LOCK_UN)
        print(json.dumps(row),flush=True)
    return int(any(row['exit_code'] for row in results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',choices=('runtime','precomputed'),required=True)
    parser.add_argument('--base',type=Path,default=BASE)
    parser.add_argument('--phases',nargs='+',choices=PHASES+('arrows','report'))
    args = parser.parse_args()
    BASE = args.base.resolve()
    raise SystemExit(run(args.variant,args.phases))
