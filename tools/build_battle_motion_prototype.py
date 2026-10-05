"""Private per-function motion trial; never gates the shared animation update."""
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_performance_prototype import ROOT, replace
from dex_timing.assets import sha256
from dex_timing.animation_reference import OUTPUT, PROTOTYPE, FRAME
from pokedex_info_assets import constants

BASE = ROOT / 'build/global-speed-20261004/final'


def interpolate(points, frames, signed=False):
    """Fill physical intervals between measured poses, not hold a whole update."""
    times = [p[0] for p in points]
    source = [[v - 256 if signed and v >= 128 else v for v in p[1]] for p in points]
    result = []
    for frame in range(frames):
        t = frame * times[-1] / max(1, frames - 1)
        i = min(max(1, bisect_right(times, t)), len(times)-1)
        fraction = (t-times[i-1]) / max(1e-9, times[i]-times[i-1])
        result.append([round(a+(b-a)*fraction) & 255 for a,b in zip(source[i-1],source[i])])
    return result


def curves():
    reference = json.loads((OUTPUT / 'reference.json').read_text())
    values = constants(ROOT / 'constants/battle_anim_constants.asm')
    tables = {}
    metadata = []

    def objects(move, side='player'):
        row = next(r for r in reference['rows'] if (r['variant'],r['move'],r['side'],r['quarter']) ==
                   ('production',move,side,0))
        return row['invocations'][0]['scripts'][0]['objects']

    def add(label, obj, frames, fields, signed=False, samples=None, normalize=None):
        samples = samples or obj['samples']
        start = samples[0]['t']
        points = [((s['t']-start)/FRAME,[s['data'][i] for i in fields]) for s in samples]
        if normalize:
            points = [(t,normalize(v)) for t,v in points]
        tables[label] = interpolate(points,frames,signed)
        metadata.append(dict(label=label,frames=frames,source_function=obj['function'],
                             source_lifetime=obj['lifetime'],fields=fields))

    water = objects('WATER_PULSE')
    drift = values['BATTLE_ANIM_FUNC_WATER_PULSE_DRIFT_BUBBLE']
    durations = [63,57,38,73,51]
    for param,duration in enumerate(durations):
        obj = next(o for o in water if o['function']==drift and o['samples'][0]['data'][12]==param)
        add(f'MotionScatter{param}',obj,duration,(10,11),True)
    for param in range(8):
        # Only 0-3 occur in this script. The remaining simple drift directions
        # are generated analytically, keeping every defined parameter valid.
        dx,dy = ((1,-1),(-1,1),(-1,-1),(1,1),(0,-1),(0,1),(1,0),(-1,0))[param]
        tables[f'MotionPath{param}'] = [[round(dx*(n+1)*19/40)&255,round(dy*(n+1)*19/40)&255] for n in range(40)]
    ring = next(o for o in water if o['function']==values['BATTLE_ANIM_FUNC_USER_TO_TARGET_DISAPPEAR'])
    add('MotionWaterRing',ring,64,(8,9))
    for param in range(4):
        obj = next(o for o in water if o['function']==values['BATTLE_ANIM_FUNC_WATERFALL_BUBBLE'] and
                   o['samples'][0]['data'][12]==param)
        x,y = obj['samples'][0]['data'][8:10]
        add(f'MotionWaterTarget{param}',obj,60 if param<2 else 48,(8,9),True,
            normalize=lambda v,x=x,y=y:[(v[0]-x)&255,(v[1]-y)&255])
    for side in ('player','foe'):
        for lane,param in enumerate((0x92,0xb3,0xf4)):
            obj = next(o for o in objects('CAUSTIC',side) if o['function']==values['BATTLE_ANIM_FUNC_CAUSTIC_BUBBLE']
                       and o['samples'][0]['data'][12]==param)
            samples = [s for s in obj['samples'] if s['data'][15]<3]
            base = samples[0]['data'][9]
            add(f'MotionCaustic{side}{lane}',obj,(63,64,68)[lane],(8,9),False,samples,
                lambda v,base=base:[v[0],v[1]-base])
    for param in range(5):
        obj = next(o for o in objects('SUPERPOWER') if o['function']==values['BATTLE_ANIM_FUNC_SUPERPOWER_ROCK_CHIP']
                   and o['samples'][0]['data'][12]==param)
        base = obj['samples'][0]['data'][9]
        add(f'MotionSuperChip{param}',obj,round(obj['lifetime']),(8,9),True,
            normalize=lambda v,base=base:[0,(v[1]-base)&255])
    # Continuous unwrapped angle/radius progression. The six initial phases
    # remain runtime parameters; no object positions or side-specific stalls
    # are baked into the orbit.
    angle = 0
    source = []
    speed = 1
    for age in range(1,81):
        radius = 24 if age<61 else 24+4*(age-60)
        source.append((age-1,[angle,radius]))
        if age in (6,12,18):
            speed += 1
        angle += speed
    tables['MotionDragonOrbit'] = interpolate(source,92)
    lines = ['; PRIVATE motion trial: generated from retained production references.',
             'SECTION "Battle Motion Reference", ROMX, BANK[$ba]',
             'INCLUDE "engine/battle_anims/motion_reader.asm"']
    for label,data in tables.items():
        assert 1<len(data)<256 and all(len(row)==2 for row in data)
        lines.extend((label+':',f'\tdb {len(data)}'))
        for i in range(0,len(data),8):
            lines.append('\tdb '+', '.join(str(v) for row in data[i:i+8] for v in row))
    return '\n'.join(lines)+'\n',dict(tables=metadata,payload=sum(1+2*len(v) for v in tables.values()))


def edit_block(path,label,operation):
    text = path.read_text()
    start = text.index(label+':\n')
    end = text.find('\nBattleAnim',start+len(label)+2)
    if end<0: end=len(text)
    path.write_text(text[:start]+operation(text[start:end])+text[end:])


def finish_surf(block):
    anchor = '\tjr c, .move_down\n\txor a\n'
    terminal = '\tinc a\n\tinc a\n\tld [hl], a\n\tsub $10\n'
    assert block.count(anchor) == block.count(terminal) == 1
    return block.replace(anchor, '\tjr c, .move_down\n.finish\n\txor a\n').replace(
        terminal, '\tinc a\n\tinc a\n\tld [hl], a\n\tcp $70\n\tjr nc, .finish\n\tsub $10\n')


def patch(checkout, surf_production=False, intro_visible=False, surf_cleanup=False):
    generated,metadata = curves()
    (checkout/'engine/battle_anims/motion_tables.asm').write_text(generated)
    shutil.copy2(ROOT/'tools/dex_timing/probes/battle_motion_reader.asm',checkout/'engine/battle_anims/motion_reader.asm')
    shutil.copy2(ROOT/'tools/dex_timing/probes/battle_motion_functions.asm',checkout/'engine/battle_anims/motion_functions.asm')
    replace(checkout/'main.asm','INCLUDE "engine/battle_anims/extension_functions.asm"',
        'INCLUDE "engine/battle_anims/extension_functions.asm"\nINCLUDE "engine/battle_anims/motion_functions.asm"\n'
        '\nINCLUDE "engine/battle_anims/motion_tables.asm"')
    replace(checkout/'engine/battle_anims/helpers.asm',
        '\tld [hl], a\n\tpop hl\n.okay\n',
        '\tld [hl], a\n\tpush bc\n\tpush de\n\tcallfar BattleMotion_FrameDuration\n\tpop de\n\tpop bc\n\tpop hl\n.okay\n')
    functions = checkout/'engine/battle_anims/functions.asm'
    replace(functions,'BattleAnimFunc_MoveFromUserToTargetAndDisappear:\n',
        'BattleAnimFunc_MoveFromUserToTargetAndDisappear:\n'
        '\tld hl, BATTLEANIMSTRUCT_FRAMESET_ID\n\tadd hl, bc\n\tld a, [hli]\n'
        '\tcp LOW(BATTLE_ANIM_FRAMESET_WATER_PULSE_RING)\n\tjr nz, .original\n'
        '\tld a, [hl]\n\tcp HIGH(BATTLE_ANIM_FRAMESET_WATER_PULSE_RING)\n'
        '\tjp z, BattleMotion_WaterRing\n.original\n')
    edit_block(functions,'BattleAnimFunc_DragonDanceOrb',lambda b:
        'BattleAnimFunc_DragonDanceOrb:\n\tjp BattleMotion_DragonOrbit\n')
    edit_block(functions,'BattleAnimFunc_SuperpowerRockChip',lambda b:
        'BattleAnimFunc_SuperpowerRockChip:\n\tjp BattleMotion_SuperChip\n')
    edit_block(functions,'BattleAnimFunc_SolarBeam',lambda b:b.replace('\tld hl, -$80\n',
        '\tcall BattleMotion_ChargeDelta\n'))
    edit_block(functions,'BattleAnimFunc_Surf',lambda b:b.replace('.move\n\tdec a\n',
        '.move\n\tpush hl\n\tpush de\n\tld d, a\n\tcall BattleMotion_SurfStep\n\tld a, d\n\tpop de\n\tpop hl\n'
        '\tjr nc, .wave\n\tdec a\n\tld [hl], a\n.wave\n').replace('.move_down\n\tinc a\n\tinc a\n',
        '.move_down\n\tpush hl\n\tpush de\n\tld d, a\n\tcall BattleMotion_SurfStep\n\tld a, d\n\tpop de\n\tpop hl\n'
        '\tjr nc, .same_y\n\tinc a\n\tinc a\n.same_y\n'))
    if surf_production:
        # Keep Surf's own motion and wave rotation at the measured production
        # cadence, without gating the shared object/background/SFX loop.
        edit_block(functions, 'BattleAnimFunc_Surf', lambda b:
            b.replace('\tjr nc, .wave\n', '\tret nc\n').replace('.wave\n', '')
             .replace('\tjr nc, .same_y\n', '\tret nc\n').replace('.same_y\n', ''))
        replace(checkout/'engine/battle_anims/motion_functions.asm',
                '\tadd 5\n\tcp 8\n\tjr c, .no_step\n\tsub 8\n',
                '\tadd 1\n\tcp 2\n\tjr c, .no_step\n\tsub 2\n')
        replace(checkout/'engine/battle_anims/bg_effects.asm',
                '\tpush bc\n\tcall .RotatewSurfWaveBGEffect\n',
                '\tld hl, BG_EFFECT_STRUCT_PARAM\n\tadd hl, bc\n'
                '\tld a, [hl]\n\txor 1\n\tld [hl], a\n\tret nz\n'
                '\tpush bc\n\tcall .RotatewSurfWaveBGEffect\n')
    if surf_cleanup:
        assert surf_production
        edit_block(functions, 'BattleAnimFunc_Surf', finish_surf)
    extensions = checkout/'engine/battle_anims/extension_functions.asm'
    edit_block(extensions,'BattleAnimFunc_WaterPulseDriftBubble',lambda b:
        'BattleAnimFunc_WaterPulseDriftBubble:\n\tjp BattleMotion_WaterDrift\n')
    replace(extensions,'BattleAnimFunc_WaterfallBubble:\n',
        'BattleAnimFunc_WaterfallBubble:\n\tld a, [wFXAnimID]\n\tcp LOW(WATER_PULSE)\n'
        '\tjr nz, .original\n\tld a, [wFXAnimID + 1]\n\tcp HIGH(WATER_PULSE)\n'
        '\tjp z, BattleMotion_WaterTarget\n.original\n')
    def caustic(block):
        a,b = block.index('\n.launch\n')+1,block.index('\n.start_pop\n')+1
        block=block[:a]+'.launch\n\tcall BattleMotion_Caustic\n\tret nc\n'+block[b:]
        block=block.replace('\tld [hl], 12\n','\tld [hl], 0\n')
        block=block.replace('\tret z\n\tld hl, BATTLEANIMSTRUCT_YCOORD',
                            '\tjr z, .remember_y\n\tld hl, BATTLEANIMSTRUCT_YCOORD',1)
        anchor='\tld [hl], a\n\tret\n\n.ApplyLaneYOffset:'
        block=block.replace(anchor,'\tld [hl], a\n.remember_y\n'
            '\tld hl, BATTLEANIMSTRUCT_YCOORD\n\tadd hl, bc\n\tld a, [hl]\n'
            '\tld hl, BATTLEANIMSTRUCT_VAR2\n\tadd hl, bc\n\tld [hl], a\n\tret\n\n.ApplyLaneYOffset:',1)
        # State two is not used by this private curve path; keep the jump-table
        # entry valid. The pop/frameset/sound/droplet code remains native.
        block=block.replace('\tdw .drift\n','\tdw .launch\n')
        block=block.replace('.start_pop\n\tcall BattleAnimExt_IncAnonJumptableIndex\n',
            '.start_pop\n\tld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX\n\tadd hl, bc\n\tld [hl], 3\n')
        a,b=block.index('.Decelerate:'),block.index('.SpawnDroplet:')
        return block[:a]+block[b:]
    edit_block(extensions,'BattleAnimFunc_CausticBubble',caustic)
    scripts=checkout/'data/moves/animations.asm'
    edit_block(scripts,'BattleAnim_Surf',lambda b:
        b.replace('anim_wait 32', 'anim_wait '+str(66 if surf_production else 53))
         .replace('anim_wait 56', 'anim_wait '+str(104 if surf_production else 94)))
    edit_block(scripts,'BattleAnim_WaterPulse',lambda b:b.replace('anim_wait 10','anim_wait 12').replace('anim_wait 50','anim_wait 75')
        .replace('anim_wait 5','anim_wait 11').replace('anim_wait 4','anim_wait 7').replace('anim_wait 28','anim_wait 43'))
    # Ring spacing gets its own shorter cadence, independent of the path-bubble phase.
    edit_block(scripts,'BattleAnim_WaterPulse',lambda b:b.replace('64, 92, $2\n\tanim_wait 11','64, 92, $2\n\tanim_wait 7'))
    edit_block(scripts,'BattleAnim_DragonDance',lambda b:b.replace('anim_wait 30','anim_wait 40'))
    edit_block(scripts,'BattleAnim_Caustic',lambda b:b.replace('anim_wait 10','anim_wait 11').replace('anim_wait 96','anim_wait 101'))
    edit_block(scripts,'BattleAnim_Solarbeam',lambda b:b.replace('anim_wait 104','anim_wait 138'))
    edit_block(scripts,'BattleAnim_DazzlingGleam',lambda b:b.replace('anim_wait 144','anim_wait 176'))
    edit_block(scripts,'BattleAnim_Superpower',lambda b:b.replace('$78, $2, $20','$bc, $2, $20')
        .replace('anim_wait 24','anim_wait 39').replace('anim_wait 6','anim_wait 11').replace('anim_wait 104','anim_wait 137')
        .replace('BattleAnimSub_MegaPunchHits','BattleMotion_SuperpowerHits'))
    text=scripts.read_text(); a=text.index('BattleAnimSub_MegaPunchHits:');b=text.index('\nBattleAnimSub_',a+1)
    scripts.write_text(text+'\n'+text[a:b].replace('BattleAnimSub_MegaPunchHits:','BattleMotion_SuperpowerHits:').replace('anim_wait 6','anim_wait 7')+'\n')
    framesets=checkout/'data/battle_anims/framesets.asm'
    replace(framesets,'.Frameset_WaterPulseBubble:\n\toamframe BATTLE_ANIM_OAMSET_14, 24',
                      '.Frameset_WaterPulseBubble:\n\toamframe BATTLE_ANIM_OAMSET_14, 44')
    text=framesets.read_text(); a=text.index('.Frameset_WaterPulseRing:');b=text.index('.Frameset_WaterPulseBubble:',a)
    framesets.write_text(text[:a]+text[a:b].replace(',  5',', 10')+text[b:])
    if intro_visible:
        replace(checkout/'engine/battle/sliding_intro.asm',
                '.loop2\n\tldh a, [rLY]\n\tcp $60\n',
                '.loop2\n\tldh a, [rLY]\n\tcp LY_VBLANK\n\tjr nc, .loop2\n\tcp $60\n')
    return metadata


def build(jobs,relink=False,output=PROTOTYPE,surf_production=False,intro_visible=False,surf_cleanup=False):
    inputs={str(p):sha256(p.read_bytes()) for p in (ROOT/'pokecrystal.gbc',BASE/'pokecrystal-global-double-speed.gbc')}
    output.mkdir(parents=True, exist_ok=True)
    checkout=output/'candidate'
    if not relink:
        if checkout.exists(): raise ValueError('Use --relink for the existing private checkout')
        shutil.copytree(BASE/'candidate',checkout,ignore=shutil.ignore_patterns('.git','build','*.o','pokecrystal.gbc','pokecrystal.sym','pokecrystal.map'))
        shutil.copytree(BASE/'candidate/build/dex-performance-assets',checkout/'build/dex-performance-assets')
        metadata=patch(checkout, surf_production, intro_visible, surf_cleanup)
        (output/'curves.json').write_text(json.dumps(metadata,indent=2)+'\n')
    with (output/'build.log').open('w') as log:
        subprocess.run(['make','-s','-j'+str(jobs),'pokecrystal.gbc'],cwd=checkout,stdout=log,stderr=subprocess.STDOUT,check=True)
    for ext in ('gbc','sym','map'):
        shutil.copy2(checkout/('pokecrystal.'+ext),output/('pokecrystal-targeted-motion.'+ext))
    assert inputs=={p:sha256(Path(p).read_bytes()) for p in inputs}
    report=dict(unchanged=inputs,rom=str(output/'pokecrystal-targeted-motion.gbc'),
                surf_target='production' if surf_production else 'intermediate',
                intro_visible_window=intro_visible,
                surf_same_update_cleanup=surf_cleanup,
                sha256=sha256((checkout/'pokecrystal.gbc').read_bytes()))
    (output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=24)
    parser.add_argument('--relink',action='store_true')
    parser.add_argument('--output',type=Path,default=PROTOTYPE)
    parser.add_argument('--surf-production',action='store_true')
    parser.add_argument('--intro-visible',action='store_true')
    parser.add_argument('--surf-cleanup',action='store_true')
    args=parser.parse_args()
    print(json.dumps(build(args.jobs,args.relink,args.output,args.surf_production,args.intro_visible,args.surf_cleanup)))
