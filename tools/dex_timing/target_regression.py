"""Host-only regression of earlier post-start dictionary targets.

Keep event 1, startup RAM, all instructions and work limits unchanged. Later
events target the full dictionary, exactly as in the Groudon control. Private
diagnostic ROMs may be passed to the independent core; never replace the game.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
import gzip
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from .assets import Repository, offset, sha256, timeline
from .cpu import ModelError
from .integrated_replay import SPECIES, make_replay
from .probes.compare_core import parse_core
from .probes.compare_save_state import compare_instructions
from .probes.current_state import RECORDED_SPECIES, audit, eager_tail_control, from_export
from .scheduler_experiment import candidate_summary

ROOT = Path(__file__).resolve().parents[2]
FAILURES = ('misses', 'late', 'duplicates', 'wrong_tiles', 'wrong_maps',
            'audio_underruns', 'gdma_outside_vblank', 'writes_outside_vblank')


def validate_targets(repo):
    """Check every asset's private control, not just the timed capture set."""
    rows = []
    for asset in repo.load():
        control = SimpleNamespace(repo=repo, asset=asset, cpu=SimpleNamespace(rom=repo.rom))
        changes = eager_tail_control(control)
        start = offset(repo.symbols[asset.labels['timeline']])
        size = asset.sizes['timeline']
        events, loop = timeline(control.cpu.rom[start:start+size], len(asset.plans), asset.total)
        expected = [e if i == 0 else replace(e, target=asset.total)
                    for i, e in enumerate(asset.events)]
        actual_changes = [(i, a, b) for i, (a, b) in
                          enumerate(zip(repo.rom[start:start+size], control.cpu.rom[start:start+size]), start)
                          if a != b]
        if (events != expected or loop != asset.event_loop or
                actual_changes != [(c['offset'], c['before'], c['after']) for c in changes] or
                control.cpu.rom[:start] != repo.rom[:start] or
                control.cpu.rom[start+size:] != repo.rom[start+size:]):
            raise ModelError(f'Unexpected target-control mutation: {asset.name}')
        rows.append(dict(species=asset.name, events=len(events),
            target_bytes_changed=len(changes), total=asset.total,
            used_extent=max(asset.plans[e.frame].high_water for e in events),
            startup_target=events[0].target))
    return rows


def make_case(config, name, directory):
    repo = Repository(ROOT, config['rom'], config['sym'])
    if name in config['states']:
        # Export actual volatile state and calibrate its LCD phase before any
        # candidate or synthetic phase changes. Source state is read-only.
        memory, trace = directory/'input.memory.bin', directory/'baseline.trace.txt'
        result = subprocess.run([config['core'], '--full', '--state', config['rom'],
            config['states'][name], str(trace), str(memory)], check=True, text=True,
            capture_output=True)
        (directory/'baseline.core.txt').write_text(result.stdout)
        initial = parse_core(result.stdout, full=True, allow_no_miss=True)[0]
        payload = memory.read_bytes()
        factory = lambda: from_export(repo, payload, initial, name)
        identity = dict(scope='ACTUAL_CURRENT_LINK_START',
            state_sha256=sha256(Path(config['states'][name]).read_bytes()))
    else:
        reference = Path(config['reference'])
        old = Repository(reference, reference/'pokecrystal.gbc', reference/'pokecrystal.sym')
        factory = lambda: make_replay(old, repo, name)[0]
        identity = dict(scope='RELOCATED_PRIOR_CAPTURE', reference=old.hashes)
    return repo, factory, identity


def evaluate(replay, config, directory, policy, phase, identity, core_input=None):
    changes = eager_tail_control(replay) if policy == 'eager' else []
    if phase is not None:
        replay.set_timer_phase(phase)
    comparison = None
    if phase is None:
        trace = directory/f'{policy}.trace.txt'
        private_rom = directory/f'{policy}.diagnostic.gbc'
        if changes:
            private_rom.write_bytes(replay.cpu.rom)
            rom = str(private_rom)
        else:
            rom = config['rom']
        if not (policy == 'baseline' and core_input):
            if core_input:
                command = [config['core'], '--full', '--state', rom, core_input, str(trace)]
            else:
                memory = directory/f'{policy}.memory.bin'
                memory.write_bytes(replay.export())
                command = [config['core'], '--full', rom, str(memory), str(trace)]
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            (directory/f'{policy}.core.txt').write_text(result.stdout)
        run, comparison = compare_instructions(replay, trace.read_text(), full=True)
        # These traces are newly generated diagnostics, not user inputs.
        with trace.open('rb') as source, gzip.open(str(trace)+'.gz', 'wb', compresslevel=1) as target:
            shutil.copyfileobj(source, target)
        trace.unlink()
    else:
        run = replay.run(full=True)
    summary, checks = candidate_summary(run, replay.asset), audit(replay)
    hardware = checks['hardware']
    row = dict(species=replay.asset.name, policy=policy, timer_phase=phase,
        intervals=summary['full_sequence_intervals'], misses=len(summary['misses']),
        late=sum(p['late_intervals'] != 0 for p in summary['publications']),
        duplicates=len(summary['duplicate_publications']),
        wrong_tiles=checks['wrong_tile_publications'], wrong_maps=checks['wrong_map_publications'],
        audio_underruns=sum(p['reason'] == 'underrun' for p in summary['audio_stops']),
        finishes=len(checks['finishes']),
        minimum_finish_margin=min((p['margin_t'] for p in checks['finishes']), default=None),
        **{k: hardware[k] for k in ('gdma_outside_vblank', 'writes_outside_vblank', 'latest_gdma_end_phase')})
    if comparison:
        row.update(core_identical=comparison['identical'],
                   instruction_starts=comparison['host_instructions'])
    report = dict(scope='HOST_ONLY_TARGET_REGRESSION', **replay.repo.hashes,
        input=identity, result=row, summary=summary, audit=checks, host=run,
        target_changes=changes, private_rom_sha256=sha256(replay.cpu.rom),
        instruction_comparison=comparison)
    (directory/f'{policy}.json').write_text(json.dumps(report, indent=2)+'\n')
    if comparison and not comparison['identical']:
        raise ModelError(f'Independent-core mismatch: {replay.asset.name}/{policy}; see report')
    return row


def run_case(job):
    config, name, phase = job
    suffix = 'captured' if phase is None else f'phase-{phase}'
    directory = Path(config['output'])/name/suffix
    directory.mkdir(parents=True, exist_ok=True)
    if phase is None:
        repo, factory, identity = make_case(config, name, directory)
    else:
        repo = Repository(ROOT, config['rom'], config['sym'])
        if name in config['states']:
            captured = Path(config['output'])/name/'captured'
            payload = (captured/'input.memory.bin').read_bytes()
            initial = parse_core((captured/'baseline.core.txt').read_text(),
                                 full=True, allow_no_miss=True)[0]
            factory = lambda: from_export(repo, payload, initial, name)
            identity = dict(scope='ACTUAL_START_WITH_SYNTHETIC_TIMER_PHASE')
        else:
            reference = Path(config['reference'])
            old = Repository(reference, reference/'pokecrystal.gbc', reference/'pokecrystal.sym')
            factory = lambda: make_replay(old, repo, name)[0]
            identity = dict(scope='RELOCATED_START_WITH_SYNTHETIC_TIMER_PHASE')
    return [evaluate(factory(), config, directory, policy, phase, identity,
                     config['states'].get(name)) for policy in ('baseline', 'eager')]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--sym', type=Path, default=ROOT/'pokecrystal.sym')
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--core', type=Path, required=True)
    p.add_argument('--state-directory', type=Path, required=True)
    p.add_argument('--groudon-state', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--species', nargs='+', choices=(*SPECIES, *RECORDED_SPECIES),
                   default=(*SPECIES, *RECORDED_SPECIES))
    p.add_argument('--jobs', type=int, default=8)
    p.add_argument('--timer-phases', type=int, nargs='*', default=[64, 2048, 4096, 6400, 9600, 12800])
    a = p.parse_args()
    if a.jobs < 1 or any(not 64 <= v <= 12800 or v % 4 for v in a.timer_phases):
        p.error('Positive jobs and M-cycle-aligned timer phases in 64..12800 are required')
    if a.output.resolve().is_relative_to(a.state_directory.resolve()):
        p.error('Output must be outside the emulator directory')
    names = tuple(dict.fromkeys(a.species))
    inputs = {'groudon': a.groudon_state}
    inputs.update({name: a.state_directory/f'pokecrystal.s{slot}' for slot, name in
                   ((3, 'milotic'), (4, 'drapion'), (5, 'rhyperior'), (6, 'yanmega'),
                    (7, 'spheal'), (8, 'sealeo'), (9, 'snorlax'))})
    inputs = {name: path for name, path in inputs.items() if name in names}
    paths = [a.rom, a.sym, a.core, *inputs.values()]
    hashes = {str(path.resolve()): sha256(path.read_bytes()) for path in paths}
    snapshots = a.output/'inputs'
    snapshots.mkdir(parents=True, exist_ok=True)
    states = {}
    for name, path in inputs.items():
        destination = snapshots/f'{name}.state'
        shutil.copy2(path, destination)
        states[name] = str(destination.resolve())
    repo = Repository(ROOT, a.rom, a.sym)
    structures = validate_targets(repo)
    (a.output/'asset-validation.json').write_text(json.dumps(structures, indent=2)+'\n')
    config = {key: str(getattr(a, key).resolve()) for key in
              ('rom', 'sym', 'reference', 'core', 'output')}
    config['states'] = states
    manifest = dict(inputs=hashes, species=names, timer_phases=a.timer_phases,
        policy='Full dictionary target after event 1; identical captured startup and CPU code',
        structural_assets=len(structures),
        host_sources={str(path.relative_to(ROOT)): sha256(path.read_bytes())
                      for path in sorted((ROOT/'tools/dex_timing').rglob('*.py'))})
    (a.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    rows = []
    try:
        with ProcessPoolExecutor(a.jobs) as pool:
            # A core-checked baseline/candidate pair must pass calibration before
            # any phase controls are accepted as informative.
            for phases in ([None], a.timer_phases):
                futures = [pool.submit(run_case, (config, name, phase))
                           for name in names for phase in phases]
                for future in as_completed(futures):
                    result = future.result()
                    rows.extend(result)
                    (a.output/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
                    for row in result:
                        print(json.dumps(row), flush=True)
    finally:
        for path, expected in hashes.items():
            if sha256(Path(path).read_bytes()) != expected:
                raise ModelError(f'Diagnostic input changed: {path}')
    return int(any(any(row[k] for k in FAILURES) for row in rows if row['policy'] == 'eager'))


if __name__ == '__main__':
    raise SystemExit(main())
