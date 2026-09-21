"""Read-only import and independent-core calibration of additional owner states.

The supplied emulator states and SRAM are never written. Only sanitized initial
volatile memory enters the portable fixture; later core states are comparisons.
Exeggcute also exercises the captured slow timer and synthesized-cry channels.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from ..assets import Repository,sha256
from ..fixtures import pack,unpack
from ..full_replay import summarize
from ..scheduler_experiment import ROOT
from .compare_core import parse_core
from .compare_save_state import replay_from_export,compare_instructions

SLOTS={'garchomp':7,'bastiodon':6,'rampardos':5,'rayquaza':4,
       'kyogre':3,'metagross':2,'exeggcute':1}


def import_case(job):
    species,states,core,directory,fixtures,provenance=job
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    state=Path(states)/f'pokecrystal.s{SLOTS[species]}'
    before=sha256(state.read_bytes())
    prefix=Path(directory)/species
    memory=prefix.with_suffix('.memory.bin')
    trace=prefix.with_suffix('.trace.txt')
    process=subprocess.run([str(core),'--full','--state',str(ROOT/'pokecrystal.gbc'),
        str(state),str(trace),str(memory)],
        check=True,capture_output=True,text=True)
    prefix.with_suffix('.core.txt').write_text(process.stdout)
    # A synth control may finish without hitting the first-miss probe.
    points=parse_core(process.stdout,full=len(process.stdout.splitlines())==18)
    payload=memory.read_bytes()
    report=dict(scope='ACTUAL_STARTING_SAVE_STATE_CALIBRATION',species=species,
        slot=SLOTS[species],state_sha256=before,**repo.hashes,**provenance,core_points=points)
    fixture=pack(payload,report)
    portable=Path(fixtures)/f'{species}_initial_volatile.json'
    if portable.exists() and json.loads(portable.read_text()) != fixture:
        raise ValueError(f'Refusing to replace a different initial fixture: {portable}')
    # Validate the sanitized data too, not just the larger raw export.
    sanitized,initial=unpack(fixture,repo)
    replay=replay_from_export(repo,sanitized,points,species)
    run,comparison=compare_instructions(replay,trace.read_text(),full=True)
    keys=('ly','mode','counter','cache','remaining','compressed','read_address',
          'write_address','source_address','anim','trace')
    differences=[[key for key in keys if h[key]!=c[key]] for h,c in zip(run['points'],points)]
    deltas=[h['t']-606-c['t'] for h,c in zip(run['points'],points)]
    report.update(host=run,instruction_comparison=comparison,state_differences=differences,
                  cumulative_deltas=deltas,summary=summarize(run,replay.asset))
    result=dict(species=species,slot=SLOTS[species],identical=comparison['identical'],
        instruction_count=comparison['host_instructions'],state_match=not any(differences),
        timing_match=not any(deltas),misses=len(report['summary']['misses']),
        late_publications=sum(p['late_intervals']>0 for p in report['summary']['publications']))
    if sha256(state.read_bytes())!=before:
        raise RuntimeError('Source save state changed during import')
    if not portable.exists():
        portable.write_text(json.dumps(fixture,indent=2)+'\n')
    report['fixture_sha256']=sha256(portable.read_bytes())
    prefix.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states',type=Path,required=True)
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--sameboy-source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--species',nargs='+',choices=SLOTS,default=list(SLOTS))
    parser.add_argument('--jobs',type=int,default=4)
    args=parser.parse_args()
    if args.jobs<1:
        parser.error('Positive worker count required')
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    # The standalone core runner contains addresses for this pinned ROM.
    unpack(json.loads((ROOT/'tools/dex_timing/fixtures/luxray_initial_volatile.json').read_text()),repo)
    if args.states.resolve() in (args.output.resolve(),args.fixtures.resolve()):
        parser.error('Reports must not be written into the emulator state directory')
    args.output.mkdir(parents=True,exist_ok=True)
    args.fixtures.mkdir(parents=True,exist_ok=True)
    provenance=dict(core_revision=subprocess.check_output(
        ['git','-C',str(args.sameboy_source),'rev-parse','HEAD'],text=True).strip(),
        core_sha256=sha256(args.core.read_bytes()),
        reference_runner_source_sha256=sha256((ROOT/'tools/dex_timing/probes/core_replay.c').read_bytes()),
        host_sources={str(p.relative_to(ROOT)):sha256(p.read_bytes())
                      for p in sorted((ROOT/'tools/dex_timing').rglob('*.py'))})
    jobs=[(s,args.states,args.core,args.output,args.fixtures,provenance) for s in args.species]
    with ProcessPoolExecutor(args.jobs) as pool:
        results=list(pool.map(import_case,jobs))
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    for result in results:
        print(json.dumps(result,sort_keys=True),flush=True)
    return int(any(not r.get('identical',True) or not r.get('state_match',True)
                   or not r.get('timing_match',True) for r in results))


if __name__=='__main__':
    raise SystemExit(main())
