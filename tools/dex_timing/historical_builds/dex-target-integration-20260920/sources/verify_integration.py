"""Recheck the compiled target rule against archived starts and prototype runs."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from dex_timing.assets import Repository, offset, sha256, timeline
from dex_timing.integrated_replay import SPECIES
from dex_timing.probes.compare_core import parse_core
from dex_timing.probes.compare_save_state import compare_instructions
from dex_timing.probes.current_state import RECORDED_SPECIES, audit, eager_tail_control, from_export
from dex_timing.scheduler_experiment import candidate_summary
from dex_timing.target_regression import FAILURES

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PRIOR = ROOT/'build/dex-target-regression-20260920'
FOLLOWUP = ROOT/'build/dex-target-regression-spheal-20260920'
CORE = ROOT/'build/dex-scheduler-integrated/final-core-check/sameboy-linked-replay'
NAMES = (*SPECIES, *RECORDED_SPECIES)
PHASES = (None, 64, 2048, 4096, 6400, 9600, 12800)


def archive(name):
    return FOLLOWUP if name in ('spheal', 'sealeo', 'snorlax') else PRIOR


def verify_prototype(report, prior, directory):
    # The imported-state replay records fewer optional cost spans than the
    # relocated-start class. Compare their timing outcome and common spans.
    summary, old = report['summary'], json.loads(prior.read_text())['summary']
    report['result']['prototype_timing_identical'] = (
        {k: v for k, v in summary.items() if k != 'operations'} ==
        {k: v for k, v in old.items() if k != 'operations'} and
        all(value == old['operations'][key] for key, value in summary['operations'].items()))
    assert report['result']['prototype_timing_identical'], report['result']
    if report['result']['timer_phase'] is None:
        paths = (directory/'linked.trace.txt.gz', prior.with_name('eager.trace.txt.gz'))
        hashes = []
        for path in paths:
            with gzip.open(path, 'rb') as stream:
                hashes.append(hashlib.file_digest(stream, 'sha256').hexdigest())
        report['result']['prototype_trace_identical'] = hashes[0] == hashes[1]
        assert report['result']['prototype_trace_identical'], report['result']


def verify_binary():
    old = Repository(ROOT, OUT/'baseline/pokecrystal.gbc', OUT/'baseline/pokecrystal.sym')
    new = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    assert old.symbols == new.symbols
    assert (OUT/'baseline/pokecrystal.sym').read_bytes() == (ROOT/'pokecrystal.sym').read_bytes()
    assert (OUT/'baseline/pokecrystal.map').read_bytes() == (ROOT/'pokecrystal.map').read_bytes()
    expected, rows = bytearray(old.rom), []
    for b in new.load():
        start = offset(old.symbols[b.labels['timeline']])
        old_events, old_loop = timeline(old.rom[start:start+b.sizes['timeline']],
                                        len(b.plans), b.total)
        a = replace(b, events=old_events, event_loop=old_loop)
        assert b.events == [e if i == 0 else replace(e, target=a.total)
                            for i, e in enumerate(a.events)]
        assert (a.sizes, a.event_loop, a.plans, a.dictionary, a.labels) == (
                b.sizes, b.event_loop, b.plans, b.dictionary, b.labels)
        control = SimpleNamespace(repo=old, asset=a, cpu=SimpleNamespace(rom=old.rom))
        changes = eager_tail_control(control)
        for c in changes:
            expected[c['offset']] = c['after']
        rows.append(dict(species=a.name, target_bytes_changed=len(changes),
                         startup_target=a.events[0].target, total=a.total))
    checksum = (sum(expected[:0x14e]) + sum(expected[0x150:])) & 65535
    expected[0x14e:0x150] = checksum.to_bytes(2, 'big')
    assert bytes(expected) == new.rom, 'Compiled ROM differs beyond targets and global checksum'
    report = dict(before=old.hashes, after=new.hashes, rom_size=len(new.rom),
        symbols_identical=True, map_identical=True, exact_expected_rom=True,
        assets=len(rows), changed_assets=sum(bool(r['target_bytes_changed']) for r in rows),
        target_bytes_changed=sum(r['target_bytes_changed'] for r in rows), rows=rows)
    (OUT/'binary-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}), flush=True)


def run_case(job):
    name, phase = job
    directory = OUT/name/('captured' if phase is None else f'phase-{phase}')
    directory.mkdir(parents=True, exist_ok=True)
    captured = OUT/name/'captured'
    prior = archive(name)/name/directory.name/'eager.json'
    repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    cached = directory/'linked.json'
    if phase is None and cached.exists():
        report = json.loads(cached.read_text())
        assert all(report[k] == v for k, v in repo.hashes.items())
        assert report['instruction_comparison']['identical']
        assert not any(report['result'][k] for k in FAILURES)
        report['result'].pop('prototype_summary_identical', None)
        verify_prototype(report, prior, directory)
        cached.write_text(json.dumps(report, indent=2)+'\n')
        return report['result']
    comparison = None
    if phase is None:
        trace, memory = captured/'linked.trace.txt', captured/'input.memory.bin'
        if name in RECORDED_SPECIES:
            source = archive(name)/'inputs'/f'{name}.state'
            command = [str(CORE), '--full', '--state', str(ROOT/'pokecrystal.gbc'),
                       str(source), str(trace), str(memory)]
        else:
            source = archive(name)/name/'captured/baseline.memory.bin'
            shutil.copy2(source, memory)
            command = [str(CORE), '--full', str(ROOT/'pokecrystal.gbc'), str(memory), str(trace)]
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        (captured/'linked.core.txt').write_text(result.stdout)
    initial = parse_core((captured/'linked.core.txt').read_text(),
                         full=True, allow_no_miss=True)[0]
    replay = from_export(repo, (captured/'input.memory.bin').read_bytes(), initial, name)
    if phase is None:
        run, comparison = compare_instructions(replay, trace.read_text(), full=True)
        with trace.open('rb') as src, gzip.open(str(trace)+'.gz', 'wb', compresslevel=1) as dest:
            shutil.copyfileobj(src, dest)
        trace.unlink()
        assert comparison['identical'], comparison
    else:
        replay.set_timer_phase(phase)
        run = replay.run(full=True)
    summary, checks = candidate_summary(run, replay.asset), audit(replay)
    hardware = checks['hardware']
    row = dict(species=name, timer_phase=phase,
        intervals=summary['full_sequence_intervals'], misses=len(summary['misses']),
        late=sum(p['late_intervals'] != 0 for p in summary['publications']),
        duplicates=len(summary['duplicate_publications']),
        wrong_tiles=checks['wrong_tile_publications'], wrong_maps=checks['wrong_map_publications'],
        audio_underruns=sum(p['reason'] == 'underrun' for p in summary['audio_stops']),
        minimum_finish_margin=min((p['margin_t'] for p in checks['finishes']), default=None),
        **{k: hardware[k] for k in ('gdma_outside_vblank', 'writes_outside_vblank',
                                   'latest_gdma_end_phase')})
    if comparison:
        row.update(core_identical=comparison['identical'],
                   instruction_starts=comparison['host_instructions'])
    report = dict(scope='COMPILED_TARGET_INTEGRATION', **repo.hashes,
        result=row, summary=summary, audit=checks, host=run,
        instruction_comparison=comparison, prior_report=str(prior))
    verify_prototype(report, prior, directory)
    (directory/'linked.json').write_text(json.dumps(report, indent=2)+'\n')
    assert not any(row[k] for k in FAILURES), row
    return row


def main():
    verify_binary()
    inputs = [ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym', CORE]
    inputs += [archive(n)/'inputs'/f'{n}.state' if n in RECORDED_SPECIES else
               archive(n)/n/'captured/baseline.memory.bin' for n in NAMES]
    inputs += [Path('/Applications/SameBoy/Games/pokecrystal.gbc')]
    hashes = {str(p): sha256(p.read_bytes()) for p in inputs}
    (OUT/'manifest.json').write_text(json.dumps(dict(inputs=hashes, species=NAMES,
        timer_phases=PHASES, scope='Compiled ROM, archived starts, no gameplay input'), indent=2)+'\n')
    rows = []
    try:
        with ProcessPoolExecutor(8) as pool:
            for phases in ([None], PHASES[1:]):
                futures = [pool.submit(run_case, (name, phase)) for name in NAMES for phase in phases]
                for future in as_completed(futures):
                    row = future.result()
                    rows.append(row)
                    (OUT/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
                    print(json.dumps(row), flush=True)
    finally:
        for path, expected in hashes.items():
            assert sha256(Path(path).read_bytes()) == expected, path
    print(json.dumps(dict(passed=len(rows), core_matches=sum(r.get('core_identical', False) for r in rows),
        instruction_starts=sum(r.get('instruction_starts', 0) for r in rows))), flush=True)


if __name__ == '__main__':
    main()
