"""Compare independent SameBoy core runs with one synthetic host fixture.

This is a diagnostic, not a captured emulator state or a game test runner.
Compile core_replay.c against the local SameBoy checkout before using it.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from dex_timing.assets import Repository, sha256
from dex_timing.followup import read_stops, observed_legs
from dex_timing.model import Profile
from dex_timing.probes.export_core_fixture import fixture_bytes
from dex_timing.replay import OwnerReplay, matching_div_phases


def parse_core(text, full=False, end_to_end=False, allow_no_miss=False):
    lines=text.splitlines()
    no_miss=allow_no_miss and full and not end_to_end and len(lines)==15
    if not no_miss and len(lines)!=(12 if end_to_end else 18 if full else 15):
        raise ValueError('Expected complete reference-core snapshots')
    snapshots=[]
    hex_fields={'pc','bank','af','bc','de','hl','sp','div','tima',
                'read_address','write_address','source_address'}
    for i in range(0,len(lines),3):
        point={k:list(bytes.fromhex(v)) if k in ('audio','audio_cache','timers')
               else int(v,16 if k in hex_fields else 10)
               for k,v in (part.split('=') for part in lines[i].split())}
        point['anim']=list(bytes.fromhex(lines[i+1]))
        point['trace']=list(bytes.fromhex(lines[i+2]))
        if point['stop']!=i//3 or len(point['anim'])!=27 or len(point['trace'])!=139:
            raise ValueError('Invalid reference-core snapshot')
        for name,size in (('audio',6),('audio_cache',8),('timers',4)):
            if name in point and len(point[name])!=size:
                raise ValueError('Invalid reference-core byte field')
        snapshots.append(point)
    if no_miss and (snapshots[-1]['anim'][10]!=3 or snapshots[-1].get('audio',[0]*4)[3]):
        raise ValueError('Missing reference-core completion in no-miss run')
    return snapshots


def capture_differences(points, stops):
    differences=[]
    for p,s in zip(points,stops):
        mem={(b,a):v for b,a,v in s['capture']['memory']}
        expected={key:s[key] for key in ('ly','counter','cache','remaining','compressed',
                                         'read_address','write_address','source_address','tima')}
        expected.update(mode=s['stat']&3, div=s['div']*256,
                        anim=[mem[0,0xc72e+i] for i in range(27)],
                        trace=[mem[0,0xc758+i] for i in range(139)])
        expected['if']=s['capture']['hardware'][str(0xff0f)]&15
        actual=dict(p,div=p['div']&0xff00)
        differences.append([key for key,value in expected.items() if actual[key]!=value])
    return differences


def instruction_comparison(replay, core_trace):
    host=[]
    original_step=replay.cpu.step
    def log_step():
        cpu=replay.cpu
        host.append((replay.clock.t-606,cpu.bank if cpu.pc>=0x4000 else 0,cpu.pc))
        original_step()
    replay.cpu.step=log_step
    try:
        run=replay.run()
    finally:
        replay.cpu.step=original_step
    core=[(int(v[0]),int(v[1],16),int(v[2],16))
          for v in (line.split() for line in core_trace.splitlines())]
    first=next((i for i,(a,b) in enumerate(zip(host,core)) if a!=b),None)
    return {'host_instructions':len(host),'core_instructions':len(core),
            'identical':host==core,'first_differing_index':first,
            'host_elapsed_t':run['elapsed_t']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--sweep',action='store_true',help='Test all initially compatible divider phases')
    parser.add_argument('--trace',action='store_true',help='Compare every executed non-HALT instruction start')
    parser.add_argument('--sameboy-source',type=Path,help='Record the local core source revision')
    args=parser.parse_args()
    if args.sweep and args.trace:
        parser.error('Instruction trace comparison is a single-state diagnostic')
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    if repo.hashes['rom_sha256']!='7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f':
        parser.error('Reference-core addresses require the captured ROM')
    capture=ROOT/'tools/dex_timing/fixtures/luxray_exact_followup.txt'
    stops=read_stops(capture.read_text(),repo.symbols)
    asset=repo.load(['luxray'])[0]
    expected=[0]+[s['debugger_clock']['t_cycles'] for s in stops[1:]]
    candidates=[(658,16)]
    if args.sweep:
        candidates=[(phase,low) for phase in range(2,12801,4)
                    for low in matching_div_phases([{'t':606}],stops[:1],phase)]
    results=[]
    with tempfile.TemporaryDirectory(prefix='dex-core-') as directory:
        path=Path(directory)/'fixture.bin'
        trace_path=Path(directory)/'trace.txt'
        for phase,low in candidates:
            replay=OwnerReplay(repo,asset,stops,Profile(hblank_dot=257,
                audio_phase_t=phase,audio_played_at_publication=4),606,low)
            path.write_bytes(fixture_bytes(replay,stops,606,low))
            for subphase in range(-3,1) if args.sweep else (-3,):
                run=subprocess.run([args.core,str(ROOT/'pokecrystal.gbc'),str(path),
                                    str(trace_path) if args.trace else '-',str(subphase)],
                                   check=True,text=True,capture_output=True)
                points=parse_core(run.stdout)
                trace_diffs=[]
                for p,s in zip(points,stops):
                    mem={(b,a):v for b,a,v in s['capture']['memory']}
                    trace_diffs.append(sum(v!=mem[0,0xc758+i] for i,v in enumerate(p['trace'])))
                results.append({'phase':phase,'div_low':low,'div_subphase':subphase,
                    'deltas':[p['t']-t for p,t in zip(points,expected)],
                    'trace_differences':trace_diffs,'capture_differences':capture_differences(points,stops),
                    'points':points})
                if args.trace:
                    results[-1]['instruction_comparison']=instruction_comparison(replay,trace_path.read_text())
    document={'scope':'SYNTHETIC_REFERENCE_NOT_SAVE_STATE','rom_sha256':repo.hashes['rom_sha256'],
              'capture_sha256':sha256(capture.read_bytes()),'core_sha256':sha256(Path(args.core).read_bytes()),
              'observed_legs':observed_legs(stops),'results':results,
              'fixture_assumptions':['CGB-E, normal speed, SCX 5, WX 167, WY 0, LCDC e3, STAT mode-0 enabled',
                  'Uncaptured scroll/window shadows retain the captured hardware configuration',
                  'No input; initial OAM and uncaptured pixel buffers are zeroed',
                  'Reconstructed caller stack and verified dictionary prefix, not an emulator save state',
                  'Later captures are comparisons only; no later state is injected']}
    if args.sameboy_source:
        document['core_revision']=subprocess.check_output(
            ['git','-C',str(args.sameboy_source),'rev-parse','HEAD'],text=True).strip()
        document['core_source_dirty']=bool(subprocess.check_output(
            ['git','-C',str(args.sameboy_source),'status','--porcelain'],text=True).strip())
    Path(args.output).write_text(json.dumps(document,indent=2)+'\n')
    groups=Counter(tuple(r['deltas']) for r in results)
    print(json.dumps({'runs':len(results),'elapsed_delta_groups':dict((str(k),v) for k,v in groups.items()),
                      'exact_timing_runs':sum(not any(r['deltas']) for r in results),
                      'instruction_comparison':results[0].get('instruction_comparison')}))


if __name__=='__main__':
    main()
