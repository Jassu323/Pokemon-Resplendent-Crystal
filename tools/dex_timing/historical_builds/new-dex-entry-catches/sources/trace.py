"""Registration audit of frozen checkpoints; production ROM/source untouched."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('REGISTRATION_OUT', SOURCE))
SPECIES=os.environ.get('REGISTRATION_SPECIES','caterpie,luxray,metagross,dusknoir').split(',')
sys.path.insert(0,str(ROOT))
from tools.dex_timing.assets import Repository, sha256
from tools.dex_timing.cold_listing import expected_picture

repo=Repository(ROOT,OUT/'fixture.gbc',OUT/'fixture.sym')
parser=argparse.ArgumentParser()
parser.add_argument('--variant',choices=['baseline','resident','resident-bulk'],default='baseline')
parser.add_argument('--input',choices=['none','description','exit'],default='none')
args=parser.parse_args()
sym=repo.symbols
variant=args.variant
rom_path=OUT/'fixture.gbc'
if variant!='baseline':
    from preflight import build
    _,draft,_=build()
    sym.update(draft)
    rom_path=OUT/f'{variant}-private.gbc'
fields='''wPokeAnimSceneIndex wPokeAnimIdleFlag wPokeAnimCommand wPokeAnimParameter
wPokeAnimWaitCounter hSampledCryTimer hSampledCryBlocks hDMATransfer
wPokeAnimJumptableIndex hVBlank wFrameCounter wPokedexStatus wTilemap'''.split()
event_names={
    'entry':('NewPokedexEntry',0),
    'wait_entry':('NewPokedexEntry.WaitPressAorB_AnimateFrontpic',1),
    'script_frame':('PokeAnim_GetFrame',2),
    'script_end':('PokeAnim_End',3),
    'animation_finished':('PokeAnim_Finish',4),
    'audio_start':('SampledCry_ArmCachedPlayback',0),
    'audio_stop':('StopSampledCryAsync_NoInterruptControl',0),
    'audio_empty':('@audio_empty',0),
}
functions=[
    ('NewPokedexEntry.AnimateFrontpicFrame',1,0),('SetUpPokeAnim',1,0),
    ('PokeAnim_GetFrame',1,0),('PokeAnim_PlaceGraphic',1,0),
    ('PokeAnim_CountBitmaskTiles',1,0),('PokeAnim_ConvertAndApplyBitmask',1,0),
    ('PokeAnim_CopyBitmaskToBuffer',1,0),('PokeAnim_GetBitmaskIndex',1,0),
    ('HDMATransferTilemapToWRAMBank3',1,0),('HDMATransferAttrmapToWRAMBank3',1,0),
    ('PadTilemapForHDMATransfer',1,0),('PadAttrmapForHDMATransfer',1,0),
    ('WaitDMATransfer',1,0),('DelayFrame',1,0),
    ('ServiceSampledCryAsync',1,0),('SampledCry_FillRollingCache',1,0),
    ('SampledCry_DecodePairBatch',1,0),
    ('VBlank',0,0),('LCD',0,0),('SampledCryTimer',0,0),
    ('DMATransfer',1,1),('Decompress',1,0),('Request2bpp',1,0),
    ('GetAnimatedFrontpic',1,0),('Pokedex_LoadGFX',1,0),('StartSampledCryAsync',1,0),
    ('_NewPokedexEntry',1,0),('RotateThreePalettesLeft',1,0),
]
if variant!='baseline':
    event_names['script_frame']=('ProtoPrepared',2)
    del event_names['script_end']
    event_names['published']=('ProtoPublished',5)
    event_names['animation_finished']=('ProtoCompleted',4)
    event_names['cancel_begin']=('ProtoCancel',6)
    event_names['description']=('DisplayDexEntry',0)
    functions += [(name,1,0) for name in ('ProtoInitialize','ProtoBuild','ProtoPublish',
                                         'ProtoService','ProtoCopyBacking','ProtoCopyVRAM',
                                         'ProtoFillBacking','ProtoFillVRAM','ProtoUpload')]
sym['@audio_empty']=(0,sym['SampledCry_AsyncTimerTick.has_decoded_block'][1]-6)
lines=[f'#define S_{name} 0x{sym[name][1]:04x}' for name in fields]
b,p=sym['NewPokedexEntry']
lines += [f'#define B_ENTRY {b}',f'#define P_ENTRY 0x{p:04x}',
          'enum { E_WAIT=1, E_FRAME=2, E_END=3, E_FINISH=4, E_PUBLISH=5, E_EXIT=6, F_DMA=1 };',
          'static const struct { const char *name; unsigned bank,pc,kind; } events[] = {']
for event,(label,kind) in event_names.items():
    b,p=sym[label]; lines.append(f'{{"{event}",{b},0x{p:04x},{kind}}},')
lines += ['};','static const struct { const char *name; unsigned bank,pc,log,kind; } functions[] = {']
for label,log,kind in functions:
    b,p=sym[label];lines.append(f'{{"{label}",{b},0x{p:04x},{log},{kind}}},')
lines += ['};']
header=OUT/'trace_symbols.h';header.write_text('\n'.join(lines)+'\n')
sameboy=Path.home()/'Documents/GitHub/SameBoy'
core=OUT/('registration-trace' if variant=='baseline' else f'{variant}-trace')
files=('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
       'sm83_cpu timing workboy').split()
subprocess.run(['clang','-O2','-std=c11','-I'+str(sameboy),'-DGB_INTERNAL',
    '-DGB_DISABLE_DEBUGGER','-DGB_DISABLE_REWIND','-DGB_DISABLE_CHEATS',
    '-DGB_DISABLE_CHEAT_SEARCH','-DGB_DISABLE_TIMEKEEPING','-DGB_VERSION="registration-trace"',
    '-include',str(header),str(SOURCE/'registration_trace.c'),
    *(str(sameboy/'Core'/f'{f}.c') for f in files),'-o',str(core)],check=True)
for asset in repo.load(SPECIES):
    refs=OUT/f'{asset.name}.references'
    refs.write_bytes(bytes([len(asset.plans)])+b''.join(expected_picture(asset,i) for i in range(len(asset.plans))))
    suffix='' if variant=='baseline' else f'-{variant}'
    if args.input!='none': suffix+=f'-{args.input}'
    with (OUT/f'{asset.name}{suffix}-trace.jsonl').open('w') as output, (OUT/f'{asset.name}{suffix}-trace.stderr').open('w') as errors:
        result=subprocess.run([str(core),str(rom_path),str(OUT/f'{asset.name}-registration.s0'),str(refs),
                               str(['none','description','exit'].index(args.input))],
                              stdout=output,stderr=errors,timeout=120,
                              env={**os.environ,'REGISTRATION_FRAMES':str(OUT/f'{asset.name}{suffix}')})
    print(asset.name,result.returncode,flush=True)
    assert result.returncode==0
