"""Full linked owner replay against an independent SameBoy reference core.

Actual Luxray, Weavile and Dusknoir initial-memory fixtures are reproducible
without reopening the user's states. Other species use synthetic extensions of partial
captures; their later results are predictions, not new hardware measurements.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from .assets import Repository, sha256
from .fixtures import unpack
from .followup import read_stops, observed_legs, captured_trace_differences
from .model import Profile, FRAME, CPU_HZ
from .replay import OwnerReplay, captured_state_differences, matching_div_phases
from .probes.compare_core import parse_core
from .probes.compare_save_state import replay_from_export, compare_instructions
from .probes.export_core_fixture import fixture_bytes

ROOT = Path(__file__).resolve().parents[2]
ACTUAL = ('luxray','weavile','dusknoir')
# Previously constrained publication-phase candidates, not fitted operation costs.
PARTIAL = {'bastiodon':(322,224),
           'garchomp':(738,192), 'rampardos':(418,0), 'rayquaza':(626,48),
           'kyogre':(694,44), 'metagross':(546,128)}


def summarize(run, asset):
    origin = run['points'][0]['t']
    events = run['lifecycle']
    publications = [p for p in events if p['kind'].endswith('.display_recorded')]
    misses = [p for p in events if p['kind'] == 'Pokedex_CountAnimationUnderflow']
    audio = [p for p in events if p['kind'] == 'StopSampledCryAsync_NoInterruptControl']
    deadlines, due = [], 0
    for event in asset.events:
        deadlines.append(due)
        due += event.duration
    deadlines.append(due)
    publication_rows = []
    for index,p in enumerate(publications):
        interval = p['t']//FRAME-origin//FRAME
        publication_rows.append({'t':p['t']-origin,'interval':interval,
            'event':p['trace'][5], 'frame':p['anim'][6], 'deadline':p['anim'][11],
            'expected_interval':deadlines[index], 'late_intervals':interval-deadlines[index]})
    operations = {}
    for operation in run['operations']:
        group = operations.setdefault(operation['kind'],{'calls':0,'instruction_t':0,
            'interrupt_t':0,'elapsed_t':0,'max_elapsed_t':0})
        group['calls'] += 1
        for key in ('instruction_t','interrupt_t','elapsed_t'):
            group[key] += operation[key]
        group['max_elapsed_t'] = max(group['max_elapsed_t'],operation['elapsed_t'])
    if len(publications) != len(deadlines):
        raise ValueError(f'{asset.name}: incomplete publication sequence')
    return {'species':asset.name,
            'timeline_scope':'main_animation_plus_base_hold_and_idle',
            'full_sequence_intervals':sum(e.duration for e in asset.events),
            'mainline_cleanup_is_not_animation_duration':True,
            'completion_t':run['points'][-1]['t']-origin,
            'completion_seconds':(run['points'][-1]['t']-origin)/CPU_HZ,
            'publications':publication_rows,
            'misses':[{'t':p['t']-origin,'event':p['trace'][5], 'frame':p['anim'][6],
                       'uploaded':p['anim'][9], 'needed':p['anim'][5], 'cache':p['cache'],
                       'remaining_dictionary':p['dictionary_remaining']} for p in misses],
            'audio_stops':[{'t':p['t']-origin,'remaining':p['remaining'],'cache':p['cache'],
                            'reason':'underrun' if p['remaining'] else 'natural'} for p in audio],
            'hdma_tiles':sum(d['tiles'] for d in run['hdma']),
            'hdma_trains':len(run['hdma']),'operations':operations}


def run_case(job):
    name, core, directory, provenance = job
    repo = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    asset = repo.load([name])[0]
    path = Path(directory)/name
    stops = None
    if name in ACTUAL:
        document = json.loads((ROOT/f'tools/dex_timing/fixtures/{name}_initial_volatile.json').read_text())
        payload, _ = unpack(document,repo)
        scope = 'ACTUAL_INITIAL_MEMORY_CORE_VALIDATED_CONTINUATION'
    else:
        capture = ROOT/f'tools/dex_timing/fixtures/{name}_owner_followup.txt'
        stops = read_stops(capture.read_text(),repo.symbols)
        phase, low = PARTIAL[name]
        seed = OwnerReplay(repo,asset,stops,Profile(hblank_dot=257,audio_phase_t=phase,
                           audio_played_at_publication=4),606,low)
        # Partial captures omit timer restoration and all music-channel state.
        # Use a documented silent post-cry control, not invented live music.
        seed.cpu.field('hSampledCrySavedIE',15)
        seed.cpu.field('hSampledCrySavedTAC',0)
        payload = fixture_bytes(seed,stops,606,low)
        scope = 'PARTIAL_CAPTURE_SYNTHETIC_CONTINUATION'
    path.with_suffix('.memory.bin').write_bytes(payload)
    trace_path = path.with_suffix('.trace.txt')
    reference = subprocess.run([str(core),'--full',str(ROOT/'pokecrystal.gbc'),
        str(path.with_suffix('.memory.bin')),str(trace_path)],check=True,text=True,capture_output=True)
    points = parse_core(reference.stdout,full=True)
    replay = replay_from_export(repo,payload,points,species=name)
    run, comparison = compare_instructions(replay,trace_path.read_text(),full=True)
    keys = ('ly','mode','counter','cache','remaining','compressed','read_address','write_address',
            'source_address','anim','trace')
    differences = [[key for key in keys if h[key] != c[key]] for h,c in zip(run['points'],points)]
    deltas = [h['t']-606-c['t'] for h,c in zip(run['points'],points)]
    result = {'scope':scope,**repo.hashes,**provenance,'input_sha256':sha256(payload),
              'core_sha256':sha256(Path(core).read_bytes()),'summary':summarize(run,asset),
              'instruction_comparison':comparison,'core_points':points,'host':run,
              'state_differences':differences,'cumulative_deltas':deltas}
    if stops:
        result['captured_first_miss_comparison'] = {
            'state_differences':captured_state_differences(repo,run['points'][:5],stops),
            'trace_differences':captured_trace_differences(repo,run['points'][:5],stops),
            'matching_div_low':matching_div_phases(run['points'][:5],stops,PARTIAL[name][0]),
            'observed_legs':observed_legs(stops)}
    path.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    return dict(result['summary'],scope=scope,identical=comparison['identical'],
                instruction_count=comparison['host_instructions'],
                state_match=not any(differences),timing_match=not any(deltas))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sameboy-source',type=Path,required=True)
    p.add_argument('--species',nargs='+',choices=[*ACTUAL,*PARTIAL],default=[*ACTUAL,*PARTIAL])
    p.add_argument('--jobs',type=int,default=8)
    args = p.parse_args()
    if args.jobs < 1 or len(set(args.species)) != len(args.species):
        p.error('Use a positive worker count and distinct species')
    repo = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    document = json.loads((ROOT/'tools/dex_timing/fixtures/luxray_initial_volatile.json').read_text())
    # The standalone reference runner contains addresses for this pinned ROM.
    # Check even partial-only runs, before creating any outputs or workers.
    unpack(document,repo)
    provenance = {
        'core_revision':subprocess.check_output(
            ['git','-C',str(args.sameboy_source),'rev-parse','HEAD'],text=True).strip(),
        'core_source_dirty':bool(subprocess.check_output(
            ['git','-C',str(args.sameboy_source),'status','--porcelain'],text=True).strip()),
        'host_sources':{str(path.relative_to(ROOT)):sha256(path.read_bytes())
                        for path in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        'reference_runner_source_sha256':sha256(
            (ROOT/'tools/dex_timing/probes/core_replay.c').read_bytes()),
        'assumptions':['Pinned CGB-E, normal speed, no input, Selected BG-only layout',
            'Only initial memory is supplied; later snapshots are comparisons',
            'Partial captures use reconstructed caller state and silent post-cry music',
            'Instruction/core agreement is not new hardware or user capture evidence']}
    args.output.mkdir(parents=True,exist_ok=True)
    with ProcessPoolExecutor(args.jobs) as pool:
        results = list(pool.map(run_case,[(n,args.core,args.output,provenance) for n in args.species]))
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    for r in results:
        print(json.dumps({k:r[k] for k in ('species','scope','identical','instruction_count',
              'state_match','timing_match','full_sequence_intervals','audio_stops')} | {
                  'misses':len(r['misses']),
                  'late_publications':sum(p['late_intervals'] > 0 for p in r['publications'])},
              sort_keys=True),flush=True)
    return int(any(not r['identical'] or not r['state_match'] or not r['timing_match'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
