"""Read-only, first-publication save-state calibration of the host probe.

The reference core loads an actual state and exports initial memory once. Later
core snapshots are comparisons, never injected into the host. The game and the
source state are not modified. Reports and memory exports stay under --output's
directory, not in the emulator's Games directory.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from dex_timing.assets import Repository, sha256
from dex_timing.model import Profile
from dex_timing.probes.compare_core import parse_core
from dex_timing.replay import ReplayCPU, OwnerReplay


BankReadbackCPU = ReplayCPU  # Compatibility for earlier diagnostic callers.


def observed_differences(points,capture):
    return {name:[key for key,value in capture[name].items() if point[key]!=value]
            for name,point in (('initial',points[0]),('final',points[-1]))}


def read_export(payload):
    if len(payload)!=114760 or payload[:8]!=b'DEXCORE1':
        raise ValueError('Invalid reference-core memory export')
    header=struct.unpack_from('<16I',payload,8)
    return header, payload[72:65608], payload[65608:98376], payload[98376:]


def replay_from_export(repo, payload, points, species='luxray', replay_class=OwnerReplay):
    h,memory,banks,vram=read_export(payload)
    timer_config=(h[12],h[13]&7)
    if (h[0]!=606 or h[6]!=0x5ea5 or h[7]!=0x77 or h[15]!=15 or
            timer_config not in ((56,6),(0,4)) or
            (timer_config==(0,4) and species!='exeggcute')):
        raise ValueError('Unsupported initial owner/timer/interrupt configuration')
    if points[0]['div_cycles']!=-3 or points[0]['div_state']!=2 or points[0]['pending_cycles']:
        raise ValueError('Unmodeled initial divider/prefetch phase')
    if (points[0]['ly']!=145 or points[0]['remain']!=300 or points[0]['ime'] or
            points[0]['model']!=0x205 or (points[0]['scx'],points[0]['wx'],points[0]['wy'])!=(5,167,0)):
        raise ValueError('Expected masked publication at the captured LCD phase')
    regs=dict(zip(('AF','BC','DE','HL','SP','PC'),h[1:7]))
    captured_memory=[(0,a,memory[a]) for a in (*range(0xc000,0xd000),*range(0xff80,0x10000))]
    captured_memory.extend((b,0xd000+i,banks[4096*b+i]) for b in range(1,8) for i in range(4096))
    stop={'label':'Publication','ly':145,'div':h[10]>>8,'tima':h[11],
          'capture':{'registers':regs,'memory':captured_memory,
                     'hardware':{str(0xff0f):h[14]}}}
    stops=[stop]+[{'label':label} for label in ('StageEntry','ProducerEntry','FrameWait','FirstMiss')]
    next_reload=64*(256-h[11])-(h[10]&63)+4
    phase=(h[0]+next_reload-1)%12800+1
    replay=replay_class(repo,repo.load([species])[0],stops,
        Profile(hblank_dot=257,audio_phase_t=phase,audio_played_at_publication=4),h[0],h[10]&255,
        timer_state=tuple(h[10:14]))
    cpu=replay.cpu
    # Replace the constructor's synthetic stack and uncaptured memory with the
    # complete initial export. Physical VRAM is not read through a blocked bus.
    cpu.ram[:]=memory
    cpu.wram=[bytearray(banks[i:i+4096]) for i in range(0,32768,4096)]
    cpu.vram=[bytearray(vram[i:i+8192]) for i in range(0,16384,8192)]
    cpu.r[7],cpu.f=h[1]>>8,h[1]&0xf0
    for i,value in enumerate(h[2:5]): cpu.set_pair(i,value)
    cpu.sp,cpu.pc,cpu.bank=h[5:8]
    cpu.ram[0xff70],cpu.ram[0xff4f]=h[8:10]
    replay.points=[replay.snapshot('Publication')]
    replay.reset_audio_audit()
    return replay


def compare_instructions(replay, core_trace, full=False):
    original=replay.cpu.step
    host=[]
    origin=replay.clock.t
    def log_step():
        cpu=replay.cpu
        host.append((replay.clock.t-origin,cpu.bank if cpu.pc>=0x4000 else 0,cpu.pc,
                     cpu.r[7]*256+cpu.f,*(cpu.pair(i) for i in range(3)),cpu.sp))
        original()
    replay.cpu.step=log_step
    try:
        run=replay.run(full=full)
    finally:
        replay.cpu.step=original
    core=[(int(v[0]),*(int(n,16) for n in v[1:8]))
          for v in (line.split() for line in core_trace.splitlines())]
    first=next((i for i,(a,b) in enumerate(zip(host,core)) if a!=b),None)
    first_timing=next((i for i,(a,b) in enumerate(zip(host,core)) if a[:3]!=b[:3]),None)
    comparison={'host_instructions':len(host),'core_instructions':len(core),
                'identical':host==core,'first_differing_index':first,
                'timing_identical':[x[:3] for x in host]==[x[:3] for x in core],
                'first_timing_difference':first_timing}
    if first is not None:
        comparison['host_context']=host[max(0,first-3):first+4]
        comparison['core_context']=core[max(0,first-3):first+4]
    if first_timing is not None:
        comparison['host_timing_context']=host[max(0,first_timing-3):first_timing+4]
        comparison['core_timing_context']=core[max(0,first_timing-3):first_timing+4]
    return run,comparison


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--sameboy-source',type=Path,required=True)
    parser.add_argument('--capture',type=Path,default=ROOT/'tools/dex_timing/fixtures/luxray_save_state_capture.json')
    parser.add_argument('--full',action='store_true',help='Continue through animation and cry cleanup')
    args=parser.parse_args()
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    if repo.hashes['rom_sha256']!='7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f':
        parser.error('Save-state addresses require the captured ROM')
    state_hash=sha256(args.state.read_bytes())
    capture=json.loads(args.capture.read_text())
    if state_hash!=capture['state_sha256'] or any(repo.hashes[key]!=capture[key] for key in repo.hashes):
        parser.error('Capture, state, ROM and symbol identities must match')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    trace=args.output.with_suffix('.trace.txt')
    memory=args.output.with_suffix('.memory.bin')
    inputs={p.resolve() for p in (args.state,args.core,args.capture,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')}
    if any(p.resolve() in inputs for p in (args.output,trace,memory)):
        parser.error('Diagnostic output must not overwrite an input')
    prefix=[str(args.core)]+(['--full'] if args.full else [])
    result=subprocess.run([*prefix,'--state',str(ROOT/'pokecrystal.gbc'),str(args.state),
                           str(trace),str(memory)],capture_output=True,text=True,check=True)
    points=parse_core(result.stdout, full=args.full)
    control=parse_core(subprocess.check_output(
        [*prefix,str(ROOT/'pokecrystal.gbc'),str(memory)],text=True), full=args.full)
    control_keys=('t','af','bc','de','hl','sp','ly','mode','div','tima','anim','trace')
    control_differences=[[key for key in control_keys if a[key]!=b[key]]
                         for a,b in zip(control,points)]
    replay=replay_from_export(repo,memory.read_bytes(),points)
    run,comparison=compare_instructions(replay,trace.read_text(),full=args.full)
    differences=[]
    keys=('ly','mode','counter','cache','remaining','compressed','read_address','write_address',
          'source_address','anim','trace')
    for host,core in zip(run['points'],points):
        differences.append([key for key in keys if host[key]!=core[key]])
    document={'scope':'ACTUAL_SAVE_STATE_FULL_REPLAY' if args.full else 'ACTUAL_SAVE_STATE_FIRST_MISS_CALIBRATION',
              'state_sha256':state_hash,**repo.hashes,'core_sha256':sha256(args.core.read_bytes()),
              'capture_sha256':sha256(args.capture.read_bytes()),
              'core_revision':subprocess.check_output(['git','-C',str(args.sameboy_source),'rev-parse','HEAD'],text=True).strip(),
              'core_source_dirty':bool(subprocess.check_output(['git','-C',str(args.sameboy_source),'status','--porcelain'],text=True).strip()),
              'core_points':points,'host':run,'instruction_comparison':comparison,
              'actual_memory_synthetic_ppu_control':{'elapsed_t':[p['t'] for p in control],
                                                     'state_differences':control_differences},
              'observed_differences':observed_differences(points[:5],capture),
              'cumulative_deltas':[p['t']-606-c['t'] for p,c in zip(run['points'],points)],
              'state_differences':differences}
    if sha256(args.state.read_bytes())!=state_hash:
        raise RuntimeError('Source state changed during analysis')
    args.output.write_text(json.dumps(document,indent=2)+'\n')
    print(json.dumps({key:document[key] for key in ('observed_differences','cumulative_deltas','state_differences','instruction_comparison')}))
    if (any(document['cumulative_deltas']) or any(differences) or any(control_differences) or not comparison['identical'] or
            any(document['observed_differences'].values())):
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
