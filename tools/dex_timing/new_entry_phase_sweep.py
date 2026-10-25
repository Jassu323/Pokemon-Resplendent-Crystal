"""Synthetic timer-phase stress for New Entry, separate from real-input acceptance.

Only the first TIMA interval is varied, at the actual disabled-timer startup
write. TMA, subsequent periods, code, producer state and CPU/PPU timing are not
patched. This tests a 64-T grid, not every possible CPU/PPU entry state.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import json
import os
from pathlib import Path
import subprocess

from .assets import Repository, sha256
from .new_entry import ROOT, compile_core
from .new_entry_sweep import ORIGINAL, audit


def run_case(job):
    config, asset, clocks, mode = job
    name = f'{asset.name}-{clocks:03}-{mode}'
    process = subprocess.run(
        [config['binary'], config['rom'], config['states'][asset.name],
         config['references'][asset.name], str(mode)], capture_output=True, text=True,
        timeout=180, env={**os.environ, 'REGISTRATION_COMPACT': '1',
                          'REGISTRATION_TIMER_FIRST_CLOCKS': str(clocks)})
    trace = [json.loads(line) for line in process.stdout.splitlines()]
    # The fixed input modes are smoke checks, not the exhaustive tap matrix.
    result = audit(asset, trace, dict(name=name, family='stress'))
    applied = [e for e in trace if e['event'] == 'synthetic_timer_phase']
    if process.returncode or len(applied) != 1 or applied[0]['first_clocks'] != clocks:
        result['status'] = 'fail'
        result['errors'].append(dict(reason='phase injection or runner failed',
                                     code=process.returncode, applied=applied,
                                     stderr=process.stderr[-3000:]))
    if (mode and not result['page2']) or (mode == 2 and not result['returned']):
        result['status'] = 'fail'
        result['errors'].append(dict(reason='representative input was not accepted'))
    result.update(first_timer_clocks=clocks, input_mode=mode, synthetic_phase=applied)
    if result['status'] == 'fail' or clocks in (1, 200):
        prefix = Path(config['output']) / name
        with gzip.open(prefix.with_suffix('.jsonl.gz'), 'wt') as output:
            output.write(process.stdout)
        prefix.with_suffix('.stderr').write_text(process.stderr)
        result['trace'] = str(prefix.with_suffix('.jsonl.gz'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--sweep', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--all-input-modes', action='store_true',
                        help='Exercise description/exit as well as completion for every sampled species')
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / 'build'):
        parser.error('Generated phase-test output must stay under ignored build/')
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.rom, args.sym)
    real = json.loads((args.sweep / 'report.json').read_text())
    assert all(real[k] == v for k, v in repo.hashes.items())
    assets = [a for a in repo.load(list(real['fixtures'])) if a.sample_blocks]
    binary = compile_core(repo, args.sameboy, args.output, 'trace')
    config = dict(binary=str(binary), rom=str(args.rom), output=str(args.output),
                  states={}, references={})
    for asset in assets:
        name = asset.name
        state = (args.registration / f'{name}-registration.s0' if name in ORIGINAL
                 else args.sweep / f'{name}-generated.s0')
        assert sha256(state.read_bytes()) == real['fixtures'][name]['state_sha256']
        config['states'][name] = str(state)
        config['references'][name] = str(args.sweep / f'{name}.references')
    # New Entry uses the normal 200 timer-clock period. The probe rejects an
    # unexpected reload; records below independently verify that contract.
    jobs = [(config, asset, clocks, mode) for asset in assets
            for clocks in range(1, 201)
            for mode in ((0, 1, 2) if args.all_input_modes or asset.name == 'dusknoir' else (0,))]
    report = dict(**repo.hashes, synthetic=True, scope=__doc__, runs=[],
                  all_input_modes=args.all_input_modes,
                  fixture_sources=str(args.sweep / 'report.json'),
                  fixture_provenance=real['fixtures'],
                  sameboy_commit=subprocess.check_output(
                      ['git', '-C', str(args.sameboy), 'rev-parse', 'HEAD'], text=True).strip(),
                  sameboy_core_sha256=sha256(b''.join(str(p.relative_to(args.sameboy)).encode() + b'\0' + p.read_bytes()
                      for p in sorted((args.sameboy / 'Core').rglob('*')) if p.suffix in ('.h', '.c'))),
                  host_sources={str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in (
                      Path(__file__), ROOT / 'tools/dex_timing/new_entry.py',
                      ROOT / 'tools/dex_timing/new_entry_sweep.py',
                      ROOT / 'tools/dex_timing/probes/new_entry_trace.c')},
                  binary_sha256=sha256(binary.read_bytes()))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool, (args.output / 'results.jsonl').open('w') as output:
        futures = [pool.submit(run_case, job) for job in jobs]
        failures = 0
        for i, future in enumerate(as_completed(futures), 1):
            row = future.result()
            assert all(e['period'] == 200 for e in row['synthetic_phase'])
            report['runs'].append(row)
            output.write(json.dumps(row) + '\n')
            output.flush()
            failures += row['status'] != 'pass'
            if row['status'] != 'pass' or i % 100 == 0 or i == len(jobs):
                print(json.dumps(dict(done=i, total=len(jobs), failures=failures,
                                     latest=row['case'], errors=row['errors'][:2])), flush=True)
    report['summary'] = dict(species=len(assets), cases=len(jobs), failed=failures,
                             checked_displays=sum(r['checked_displays'] for r in report['runs']))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
