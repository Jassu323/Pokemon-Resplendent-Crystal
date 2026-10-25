"""Compare four user stops with a full, actual-initial-state owner replay.

Later captured values are assertions only. The reference core loads the source
state read-only; the host receives its initial volatile memory, not PPU internals
or any later state. This tool does not build or modify the game.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from .assets import Repository, sha256
from .cpu import ModelError
from .fixtures import pack
from .followup import read_debugger_clock
from .full_replay import summarize
from .probes.compare_core import parse_core
from .probes.compare_save_state import replay_from_export, compare_instructions

ROOT = Path(__file__).resolve().parents[2]
LABELS = ('Starting State', 'First Animation Miss', 'Cry Stop', 'Completed')
SYMBOLS = ('Pokedex_VBlankAnimationFrontpicMap.deadline_reached',
           'Pokedex_CountAnimationUnderflow', 'StopSampledCryAsync_NoInterruptControl',
           'DelayFrame.halt')
KEYS = ('t', 'pc', 'bank', 'af', 'bc', 'de', 'hl', 'sp', 'ime', 'ly', 'mode',
        'if_raw', 'ie', 'audio', 'audio_cache', 'timers', 'anim', 'trace')
IDENTITY = {
    'rom_sha256':'7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f',
    'sym_sha256':'1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5'}


def read_capture(text, symbols):
    points = []
    for section in text.replace('&#x20;', ' ').split('-----'):
        if not section.strip():
            continue
        label = section.strip().splitlines()[0].rstrip(':')
        if len(points) >= 4 or label != LABELS[len(points)]:
            raise ModelError('Expected the four ordered end-to-end stops')
        memory, point = {}, {'label':label}
        for bank, address, values in re.findall(
                r'(?im)^\s*([\da-f]{2}):([\da-f]{4}):\s+((?:[\da-f]{2}(?:[ \t]+|$))+)', section):
            for i, value in enumerate(values.split()):
                key, value = (int(bank, 16), int(address, 16)+i), int(value, 16)
                if key in memory and memory[key] != value:
                    raise ModelError(f'Conflicting memory samples at {label}')
                memory[key] = value
        for name, value in re.findall(r'(?im)^\s*(AF|BC|DE|HL|SP|PC)\s*=\s*\$([\da-f]+)', section):
            name, value = name.lower(), int(value, 16)
            if name in point and point[name] != value:
                raise ModelError(f'Conflicting duplicate registers at {label}')
            point[name] = value
        try:
            clock = read_debugger_clock(section)
            if not clock or clock['keep'] != bool(points):
                raise ModelError('Use an initial ticks reset followed by three ticks keep stops')
            point['t'] = clock['t_cycles'] if points else 0
            ime = re.findall(r'(?m)^IME = (Enabled|Disabled)', section)
            if not ime or len(set(ime)) != 1:
                raise ModelError(f'Missing/conflicting IME at {label}')
            point['ime'] = int(ime[0] == 'Enabled')
            bank = re.search(r'(?m)^\s*1\. \$([\da-f]+):\$([\da-f]+)', section)
            point['bank'] = int(bank[1], 16)
            if int(bank[2], 16) != point['pc'] or (point['bank'], point['pc']) != symbols[SYMBOLS[len(points)]]:
                raise ModelError(f'{label} must stop at the linked symbol')
            point['ly'] = int(re.search(r'(?m)^LY: (\d+)', section)[1])
            point['mode'] = int(re.search(r'Current mode: Mode (\d)', section)[1])
            state = re.search(r'Current state: (.+)', section)[1]
            if match := re.fullmatch(r'Sleeping \((\d+) cycles to next event\)', state):
                point['remain'] = int(match[1])
            elif match := re.fullmatch(r'Rendering pixel \((\d+)/160\)', state):
                point['pixel'] = int(match[1])
            else:
                raise ModelError(f'Unsupported captured LCD state: {state}')
            hardware = {int(a,16):int(v,16) for a,v in re.findall(
                r'(?i)print/x \[\$([\da-f]+)\]:\s*=\$([\da-f]+)', section)}
            point.update(if_raw=hardware[0xff0f], ie=hardware[0xffff])
            for key, bank, address, size in (('anim',0,0xc72e,27), ('trace',0,0xc758,139),
                    ('audio',0,0xffee,6), ('audio_cache',4,0xdff4,8), ('timers',0,0xff04,4)):
                point[key] = [memory[bank,address+i] for i in range(size)]
            if any(key not in point for key in KEYS):
                raise ModelError(f'Incomplete register/memory capture at {label}')
        except (KeyError, TypeError, IndexError) as error:
            raise ModelError(f'Incomplete end-to-end capture at {label}') from error
        points.append(point)
    if len(points) != 4 or any(a['t'] >= b['t'] for a,b in zip(points,points[1:])):
        raise ModelError('Expected four stops with increasing cumulative elapsed ticks')
    return points


def host_points(run):
    audio = [p for p in run['lifecycle'] if p['kind'] == SYMBOLS[2]]
    if len(run['points']) != 6 or len(audio) != 1:
        raise ModelError('Expected a complete owner run and one cry-stop event')
    origin = run['points'][0]['t']
    return [dict(p,t=p['t']-origin) for p in
            (run['points'][0], run['points'][4], audio[0], run['points'][-1])]


def differences(actual, expected, ppu=False):
    if len(actual) != len(expected):
        raise ModelError('Checkpoint count mismatch')
    result = []
    for a,b in zip(actual,expected):
        a = dict(a,bank=0 if a['pc'] < 0x4000 else a['bank'])
        b = dict(b,bank=0 if b['pc'] < 0x4000 else b['bank'])
        keys = (*KEYS, *(k for k in ('remain','pixel') if ppu and k in b))
        result.append([{'field':k,'expected':b[k],'actual':a[k]} for k in keys if a[k] != b[k]])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--species',choices=('dusknoir','weavile'),required=True)
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--sameboy-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixture-output',type=Path,help='Optional portable initial-memory fixture, not an emulator state')
    args = p.parse_args()
    rom, sym = ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym'
    repo = Repository(ROOT,rom,sym)
    if repo.hashes != IDENTITY:
        p.error('The reference runner and capture addresses require the pinned ROM and symbols')
    expected = read_capture(args.capture.read_text(),repo.symbols)
    trace = args.output.with_suffix('.trace.txt')
    memory = args.output.with_suffix('.memory.bin')
    inputs = {path.resolve():sha256(path.read_bytes()) for path in (args.state,args.capture,args.core,rom,sym)}
    outputs = [args.output,trace,memory]+([args.fixture_output] if args.fixture_output else [])
    if len({path.resolve() for path in outputs}) != len(outputs) or any(path.resolve() in inputs for path in outputs):
        p.error('Diagnostic outputs must be distinct and must not overwrite inputs')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    reference = subprocess.run([str(args.core),'--end-to-end','--state',str(rom),str(args.state),
        str(trace),str(memory)],check=True,capture_output=True,text=True)
    core = parse_core(reference.stdout,end_to_end=True)
    # This control starts with physical RAM and a reconstructed supported PPU
    # phase. Agreement shows the raw emulator's private state is not required.
    control = parse_core(subprocess.check_output([str(args.core),'--end-to-end',str(rom),str(memory)],
                                                 text=True),end_to_end=True)
    replay = replay_from_export(repo,memory.read_bytes(),core,species=args.species)
    run, instructions = compare_instructions(replay,trace.read_text(),full=True)
    host = host_points(run)
    report = {'scope':'ACTUAL_INITIAL_STATE_FOUR_CAPTURED_STOPS_FULL_REPLAY',
        'species':args.species, **repo.hashes,
        'state_sha256':inputs[args.state.resolve()], 'capture_sha256':inputs[args.capture.resolve()],
        'core_sha256':inputs[args.core.resolve()],
        'core_revision':subprocess.check_output(['git','-C',str(args.sameboy_source),'rev-parse','HEAD'],text=True).strip(),
        'core_source_dirty':bool(subprocess.check_output(['git','-C',str(args.sameboy_source),'status','--porcelain'],text=True).strip()),
        'host_sources':{str(path.relative_to(ROOT)):sha256(path.read_bytes())
                        for path in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        'reference_runner_source_sha256':sha256((ROOT/'tools/dex_timing/probes/core_replay.c').read_bytes()),
        'captured':expected, 'core_points':core, 'host_points':host, 'host':run,
        'summary':summarize(run,replay.asset), 'instruction_comparison':instructions,
        'core_capture_differences':differences(core,expected,ppu=True),
        'host_capture_differences':differences(host,expected),
        'synthetic_ppu_control_differences':differences(control,core,ppu=True),
        'assumptions':['CGB-E, normal speed, no input, pinned Selected BG-only layout',
            'Only initial CPU/WRAM/VRAM/IO supplied to host; later captures are assertions',
            'Host does not model pixel output or APU waveform quality']}
    if any(sha256(path.read_bytes()) != digest for path,digest in inputs.items()):
        raise RuntimeError('A diagnostic input changed during the replay')
    report['passed'] = instructions['identical'] and not any(
        any(report[key]) for key in ('core_capture_differences','host_capture_differences','synthetic_ppu_control_differences'))
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    if args.fixture_output and report['passed']:
        args.fixture_output.write_text(json.dumps(pack(memory.read_bytes(),report),indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('species','passed','instruction_comparison',
        'core_capture_differences','host_capture_differences','synthetic_ppu_control_differences')},indent=2))
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
