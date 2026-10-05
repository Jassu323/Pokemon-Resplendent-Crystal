"""Private, reference-derived local retiming for the complete move review suite."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

from tools.build_battle_motion_prototype import edit_block, interpolate
from tools.dex_timing.animation_reference import OUTPUT, FRAME, summarize
from tools.dex_timing.assets import Repository, sha256
from tools.dex_timing.motion_expansion import profile
from tools.pokedex_info_assets import constants

ROOT = Path(__file__).resolve().parents[1]
BASE = OUTPUT / 'prototype-surf-cleanup'
DEST = OUTPUT / 'prototype-expanded'
ACCEPTED = set('SURF WATER_PULSE DRAGON_DANCE CAUSTIC SOLARBEAM DAZZLING_GLEAM SUPERPOWER THUNDERBOLT PETAL_DANCE'.split())
PHASES = (0, 17556, 35112, 52668)


def source_labels(path):
    lines, labels, owner, n = [], {}, None, 0
    for line in path.read_text().splitlines():
        match = re.match(r'^(\w+)::?$', line)
        if match:
            owner, n = match[1], 0
        if line.strip().startswith('anim_wait '):
            label = f'MotionWait{n}'
            lines.append('.' + label + ':')
            labels[owner + '.' + label] = line
            n += 1
        lines.append(line)
    path.write_text('\n'.join(lines) + '\n')
    return labels


def wait_plan(checkout, labels):
    repo = Repository(checkout, checkout/'pokecrystal.gbc', checkout/'pokecrystal.sym')
    lookup = {repo.symbols[name][1] + 1: name for name in labels}
    changes = defaultdict(list)
    evidence = []
    moves = json.loads((OUTPUT/'expansion/phases-surf-cleanup.json').read_text())['summary']
    for row in moves:
        move = row['move']
        if row['side'] != 'player' or move in ACCEPTED or row['delta'] > -2:
            continue
        for phase in PHASES:
            normal = profile(('production', move, 'player', phase))['scripts']
            current = profile(('surf-cleanup', move, 'player', phase))['scripts']
            for a, b in zip(normal, current):
                if len(a['stages']) != len(b['stages']):
                    continue
                for old, new in zip(a['stages'], b['stages']):
                    if old['wait'] != new['wait'] or not new['wait']:
                        continue
                    label = lookup.get(new['pc'])
                    if label is None:
                        continue
                    difference = old['elapsed'] - new['elapsed']
                    changes[label].append(difference)
                    evidence.append(dict(move=move, phase=phase, label=label, wait=new['wait'], delta=difference))
    plan = {}
    protected = set()
    for move in ACCEPTED:
        for script in profile(('surf-cleanup',move,'player',0))['scripts']:
            protected.update(lookup.get(stage['pc']) for stage in script['stages'])
    for label, diffs in changes.items():
        if label in protected:
            continue
        extra = round(statistics.median(diffs))
        if extra <= 0:
            continue
        raw = labels[label].split('anim_wait ')[1].split(';')[0].strip()
        old = int(raw.replace('$','0x'), 0)
        plan[label] = dict(old=old, new=old+extra, extra=extra)
    # Gust and Sonicboom intentionally share a vanilla entry. Clone the former
    # instead of changing Sonicboom, which is outside this review suite.
    return plan, evidence


def apply_waits(checkout, plan):
    path = checkout/'data/moves/animations.asm'
    text = path.read_text()
    for label, item in plan.items():
        local = label.rsplit('.', 1)[1]
        owner = label.rsplit('.', 1)[0]
        def change(block, local=local, item=item):
            pattern = r'(\.' + local + r':\n\s*)anim_wait [^\n]+'
            value = item['new']
            waits = []
            while value > 207:
                waits.append(207)
                value -= 207
            waits.append(value)
            replacement = r'\1' + '\n\t'.join('anim_wait '+str(v) for v in waits)
            result, count = re.subn(pattern, replacement, block)
            assert count == 1, label
            return result
        if owner in ('BattleAnim_Gust','BattleAnim_Sonicboom'):
            continue
        edit_block(path, owner, change)
    # Keep unrelated aliases and shared subroutines byte-for-byte unless they
    # were actually used by a reviewed move. Their consumers are regressed.
    if any(name.startswith('BattleAnim_Sonicboom.') for name in plan):
        text = path.read_text()
        start = text.index('BattleAnim_Gust:\n')
        alias = text.index('BattleAnim_Sonicboom:\n',start)
        end = text.index('\nBattleAnim_',alias+len('BattleAnim_Sonicboom:'))
        block = text[start:end]
        original = block.replace('BattleAnim_Gust:\n', '')
        clone = block.replace('BattleAnim_Gust:\n', '').replace('BattleAnim_Sonicboom:', 'BattleMotion_Gust:')
        for label, item in plan.items():
            if label.startswith('BattleAnim_Sonicboom.'):
                local = label.rsplit('.',1)[1]
                clone = re.sub(r'(\.'+local+r':\n\s*)anim_wait [^\n]+',
                               lambda m:m[1]+'anim_wait '+str(item['new']), clone)
        path.write_text(text[:start]+'BattleAnim_Gust:\n\tanim_jump BattleMotion_Gust\n'+original+text[end:]+'\n'+clone+'\n')


def histories(move, side='player'):
    return summarize(OUTPUT/'regression/production'/f'{move.lower()}-{side}-q0/result.json')['invocations'][0]['scripts'][0]['objects']


def local_motion(checkout):
    ids = constants(ROOT/'constants/battle_anim_constants.asm')
    # Each replaces only a pure motion function for the named move. Native
    # script-owned sound, impact spawning and BG teardown remain unchanged.
    selected = (
        ('LEAF_BLADE', 'LEAF_BLADE', 'BattleAnimFunc_LeafBlade', None),
        ('LEAF_BLADE', 'LEAF_BLADE_CHIP', 'BattleAnimFunc_LeafBladeChip', None),
        ('RECOVER', 'RECOVER', 'BattleAnimFunc_Recover', None),
        ('POISON_GAS', 'POISON_GAS', 'BattleAnimFunc_PoisonGas', (44,80)),
        ('GUST', 'GUST', 'BattleAnimFunc_Gust', None),
        ('WHIRLPOOL', 'GUST', 'BattleAnimFunc_Gust', None),
        ('WATERFALL', 'WATERFALL_BUBBLE', 'BattleAnimFunc_WaterfallBubble', None),
        ('SEISMIC_TOSS', 'ROCK_SMASH', 'BattleAnimFunc_RockSmash', None),
        ('PSYCHIC_M', 'USER_TO_TARGET_DISAPPEAR', 'BattleAnimFunc_MoveFromUserToTargetAndDisappear', (64,88)),
    )
    groups, tables, metadata = defaultdict(list), [], []
    for move, function, native, base in selected:
        function_id = ids['BATTLE_ANIM_FUNC_'+function]
        objects = [o for o in histories(move) if o['function'] == function_id]
        def original_param(obj):
            data = obj['samples'][0]['data']
            if function == 'RECOVER':
                return 0x30 + ((data[16]-1)//8 & 7)
            if function == 'GUST':
                return 0
            return data[12]
        for param in sorted({original_param(o) for o in objects}):
            obj = next(o for o in objects if original_param(o)==param)
            frames = max(2, round(obj['lifetime']))
            label = f'Expanded_{move}_{function}_{param}'
            for side in ('player','foe'):
                candidates = [o for o in histories(move,side) if o['function']==function_id and original_param(o)==param]
                source = candidates[0] if candidates else obj
                start = source['samples'][0]['t']
                x,y = base or source['samples'][0]['data'][8:10]
                points = []
                for sample in source['samples']:
                    data = sample['data']
                    dy = data[9]-y
                    if side=='foe' and data[1]&1:
                        dy = -dy
                    points.append(((sample['t']-start)/FRAME,
                                   [(data[8]-x+data[10])&255, (dy+data[11])&255]))
                data = interpolate(points, frames, True)
                tables.extend((label+'_'+side+':', f'\tdw {frames}'))
                for i in range(0,frames,8):
                    tables.append('\tdb '+', '.join(str(v) for pair in data[i:i+8] for v in pair))
            groups[native].append((move,param,label,obj['frameset']))
            metadata.append(dict(move=move,param=param,label=label,frames=frames,function=function,
                                 normal_lifetime=obj['lifetime'],bytes=4+4*frames))
    reader = (ROOT/'tools/dex_timing/probes/battle_motion_expanded_reader.asm').read_text()
    payload = sum(r['bytes'] for r in metadata)
    assert payload + 128 < 16384, payload
    (checkout/'engine/battle_anims/motion_tables.asm').write_text(
        (checkout/'engine/battle_anims/motion_tables.asm').read_text()+
        '\nSECTION "Battle Expanded Motion", ROMX, BANK[$bb]\n'+reader+'\n'+'\n'.join(tables)+'\n')
    generated = []
    for native, rows in groups.items():
        name = native.replace('BattleAnimFunc_', 'BattleExpanded_')
        generated.append(name+':')
        for move,param,label,frameset in rows:
            generated.extend((f'\tld de, {move}', '\tcall BattleExpanded_Matches',
                              f'\tjr nz, .next_{label}', '\tld hl, BATTLEANIMSTRUCT_PARAM',
                              '\tadd hl, bc', '\tld a, [hl]', f'\tcp {param}',
                              f'\tjr nz, .next_{label}'))
            if native == 'BattleAnimFunc_RockSmash':
                generated.extend(('\tld hl, BATTLEANIMSTRUCT_VAR1','\tadd hl, bc','\tld a, [hli]',
                                  '\tor [hl]',f'\tjr nz, .sample_{label}',f'\tld de, {frameset}',
                                  '\tcallfar ReinitBattleAnimFrameset',f'.sample_{label}'))
            generated.extend((f'\tld de, {label}_player','\tldh a, [hBattleTurn]','\tand a',
                              f'\tjr z, .read_{label}',f'\tld de, {label}_foe',f'.read_{label}',
                              '\tcall BattleExpanded_Read16', f'\tjr c, .done_{label}',
                              '\tld hl, BATTLEANIMSTRUCT_XOFFSET', '\tadd hl, bc',
                              '\tld [hl], d', '\tinc hl', '\tld [hl], e', '\tscf', '\tret',
                              f'.done_{label}', '\tcallfar BattleAnimExt_Deinit', '\tscf', '\tret',
                              f'.next_{label}'))
        generated.extend(('\tand a', '\tret'))
        path = checkout/'engine/battle_anims/functions.asm'
        if native == 'BattleAnimFunc_WaterfallBubble':
            path = checkout/'engine/battle_anims/extension_functions.asm'
        def hook(block, name=name):
            prefix = '\tcallfar '+name+'\n\tret c\n'
            if native == 'BattleAnimFunc_LeafBlade':
                prefix = ('\tld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX\n\tadd hl, bc\n'
                          '\tld a, [hl]\n\tand a\n\tjr z, .expanded_init\n'+prefix+'.expanded_init\n')
            return block.replace(':\n', ':\n'+prefix, 1)
        edit_block(path,native,hook)
    generated.extend(('BattleExpanded_Matches:', '\tld a, [wFXAnimID]', '\tcp e', '\tret nz',
                      '\tld a, [wFXAnimID + 1]', '\tcp d', '\tret'))
    # Native charge motion keeps its fractional accumulator; only the delta
    # changes. No frame gate or alternate trig routine is introduced.
    path = checkout/'engine/battle_anims/motion_functions.asm'
    text = path.read_text()
    text = text.replace('\tld hl, -$80\n\tjr .done\n.solar',
        '\tld de, WILD_CHARGE\n\tcall .matches\n\tjr z, .other_charge\n'
        '\tld de, SHOCK_WAVE\n\tcall .matches\n\tjr z, .other_charge\n'
        '\tld de, SHADOW_BALL\n\tcall .matches\n\tjr z, .shadow_charge\n'
        '\tld hl, -$80\n\tjr .done\n.other_charge\n\tld hl, -$6a\n\tjr .done\n'
        '.shadow_charge\n\tld hl, -$5c\n\tjr .done\n.solar')
    path.write_text(text)
    tables_path=checkout/'engine/battle_anims/motion_tables.asm'
    tables_path.write_text(tables_path.read_text()+'\n'+'\n'.join(generated)+'\n')
    # Preserve Razor/Magical Leaf's native states and its one-hit ownership.
    # Fractional travel and finer angular steps avoid pausing its whole object.
    functions = checkout/'engine/battle_anims/functions.asm'
    def leaf(block):
        block = block.replace('ld [hl], $40','ld [hl], $80').replace('cp $30','cp $60')
        block = block.replace('\tdec [hl]\n\tcall BattleAnim_Sine',
                              '\tdec [hl]\n\tsrl a\n\tcall BattleAnim_Sine')
        block = block.replace('\tcall BattleAnim_ScatterHorizontal\n',
            '\tcall BattleAnim_ScatterHorizontal\n\tsra d\n\trr e\n')
        block = block.replace('\tld de, $80\n','\tld de, $60\n')
        return block
    edit_block(functions,'BattleAnimFunc_RazorLeaf',leaf)
    edit_block(functions,'BattleAnimFunc_RazorLeaf_Step',lambda b:
        b.replace('add RAZOR_LEAF_STEP_X','add RAZOR_LEAF_STEP_X / 2')
         .replace('sub RAZOR_LEAF_ENEMY_STEP_Y','sub RAZOR_LEAF_ENEMY_STEP_Y / 2'))
    return dict(tables=metadata, payload=payload)


def frame_plan(checkout):
    rules = {}
    selected = {'HYDRO_PUMP':2, 'LEAF_BLADE':2, 'SEISMIC_TOSS':2,
                'RAZOR_LEAF':2,'MAGICAL_LEAF':2,
                'GUST':2, 'SHADOW_BALL':1.3, 'WILD_CHARGE':1.2, 'SHOCK_WAVE':1.2}
    ids = constants(ROOT/'constants/battle_anim_constants.asm')
    null = ids['BATTLE_ANIM_FUNC_NULL']
    for move, scale in selected.items():
        for obj in histories(move):
            if obj['function'] != null:
                continue
            for sample in obj['samples']:
                a = sample['data']
                frameset = a[3] + 256*a[4]
                if frameset not in rules.get(move,{}):
                    rules.setdefault(move,{})[frameset] = scale
    lines = ['BattleExpanded_FrameDuration:', '\tld de, WATERFALL','\tcall BattleExpanded_Matches',
             '\tjr nz, .other_frames','\tld hl, BATTLEANIMSTRUCT_FRAMESET_ID','\tadd hl, bc',
             '\tld a, [hli]','\tcp LOW(BATTLE_ANIM_FRAMESET_WATERFALL_BUBBLE)',
             '\tjr nz, .other_frames','\tld a, [hl]','\tcp HIGH(BATTLE_ANIM_FRAMESET_WATERFALL_BUBBLE)',
             '\tjr nz, .other_frames','\tld hl, BATTLEANIMSTRUCT_PARAM','\tadd hl, bc',
             '\tbit 1, [hl]','\tld e, 49','\tjr z, .bubble_duration','\tld e, 44',
             '.bubble_duration','\tld hl, BATTLEANIMSTRUCT_DURATION','\tadd hl, bc','\tld [hl], e',
             '\tscf','\tret','.other_frames']
    for move, framesets in rules.items():
        for frameset,scale in framesets.items():
            label=f'.next_{move}_{frameset}'
            lines.extend((f'\tld de, {move}', '\tcall BattleExpanded_Matches', f'\tjr nz, {label}',
                          '\tld hl, BATTLEANIMSTRUCT_FRAMESET_ID', '\tadd hl, bc',
                          '\tld a, [hli]', f'\tcp LOW({frameset})', f'\tjr nz, {label}',
                          '\tld a, [hl]', f'\tcp HIGH({frameset})', f'\tjr nz, {label}',
                          '\tld hl, BATTLEANIMSTRUCT_DURATION', '\tadd hl, bc'))
            # d+1 is the full held-pose duration, not just the encoded d byte.
            if scale == 2:
                lines.extend(('\tld a, [hl]', '\tadd a', '\tinc a', '\tld [hl], a'))
            else:
                lines.extend(('\tld a, [hl]', '\tld e, a', '\tsrl a', '\tsrl a', '\tadd e',
                              '\tld [hl], a'))
            lines.extend(('\tscf', '\tret', label))
    lines.extend(('\tand a','\tret'))
    path=checkout/'engine/battle_anims/motion_functions.asm'
    text=path.read_text().replace('BattleMotion_FrameDuration:\n',
        'BattleMotion_FrameDuration:\n\tcallfar BattleExpanded_FrameDuration\n\tret c\n')
    path.write_text(text)
    tables_path=checkout/'engine/battle_anims/motion_tables.asm'
    tables_path.write_text(tables_path.read_text()+'\n'+'\n'.join(lines)+'\n')
    # Extended poses have a separate loader. Save both its OAM ID and flip
    # flags; touching only the regular loader would lengthen waits while the
    # Hydro Pump column itself still disappeared twice as quickly.
    path=checkout/'engine/battle_anims/extension_frame_oam.asm'
    text=path.read_text()
    anchor='\tld [hl], a\n\tld a, d\n\tand OAM_YFLIP << 1 | OAM_XFLIP << 1\n'
    assert text.count(anchor)==1
    text=text.replace(anchor,'\tld [hl], a\n\tpush bc\n\tpush de\n\tpush hl\n'
        '\tcallfar BattleExpanded_FrameDuration\n\tpop hl\n\tpop de\n\tpop bc\n'
        '\tld a, d\n\tand OAM_YFLIP << 1 | OAM_XFLIP << 1\n')
    path.write_text(text)
    return rules


def burst_plan(move, count, wait):
    captures = []
    for phase in PHASES:
        stages = profile(('production',move,'player',phase))['scripts'][0]['stages']
        group = [s for s in stages if s['wait']==wait][:count]
        assert len(group)==count, (move,phase)
        captures.append(group)
    return [max(0,round(statistics.median(r[i]['elapsed'] for r in captures))-1)
            for i in range(count)]


def retime_bursts(checkout):
    """Keep object updates live; vary only the gap before the next spawn."""
    path = checkout/'data/moves/animations.asm'
    rows = {}
    for move,owner,obj,count,wait in (
        ('POISON_GAS','BattleAnim_PoisonGas','BATTLE_ANIM_OBJ_POISON_GAS, 44, 80, $2',10,8),
        ('WHIRLPOOL','BattleAnim_Whirlpool','BATTLE_ANIM_OBJ_GUST, 132, 72, $0',9,6)):
        gaps=burst_plan(move,count,wait)
        def change(block,gaps=gaps,obj=obj,count=count):
            pattern=(r'\.loop\n\s*anim_obj '+re.escape(obj)+
                     r'\n\.MotionWait\d+:\n\s*anim_wait \d+\n\s*anim_loop '+str(count)+r', \.loop')
            replacement='\n'.join(f'\tanim_obj {obj}\n.BurstWait{i}:\n\tanim_wait {gap}'
                                  for i,gap in enumerate(gaps))
            result,n=re.subn(pattern,replacement,block)
            assert n==1,owner
            return result
        edit_block(path,owner,change)
        rows[move]=gaps
    return rows


def build(jobs, refresh=False, output=DEST, refine_bursts=False):
    production = sha256((ROOT/'pokecrystal.gbc').read_bytes())
    checkout = output/'candidate'
    output.mkdir(parents=True,exist_ok=True)
    if checkout.exists():
        if not refresh:
            raise ValueError('Expanded checkout already exists; use --refresh for generated private sources.')
        for name in ('functions.asm','extension_functions.asm','extension_frame_oam.asm','motion_functions.asm','motion_tables.asm'):
            shutil.copy2(BASE/'candidate/engine/battle_anims'/name,checkout/'engine/battle_anims'/name)
        shutil.copy2(BASE/'candidate/data/moves/animations.asm',checkout/'data/moves/animations.asm')
    else:
        shutil.copytree(BASE/'candidate',checkout,
                    ignore=shutil.ignore_patterns('.git','build','*.o','pokecrystal.gbc','pokecrystal.sym','pokecrystal.map'))
        shutil.copytree(BASE/'candidate/build/dex-performance-assets',checkout/'build/dex-performance-assets')
    labels = source_labels(checkout/'data/moves/animations.asm')
    with (output/'label-build.log').open('w') as log:
        subprocess.run(['make','-s','-j'+str(jobs),'pokecrystal.gbc'],cwd=checkout,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert sha256((checkout/'pokecrystal.gbc').read_bytes()) == sha256((BASE/'pokecrystal-targeted-motion.gbc').read_bytes())
    plan, evidence = wait_plan(checkout, labels)
    apply_waits(checkout,plan)
    motion = local_motion(checkout)
    frames = frame_plan(checkout)
    bursts=retime_bursts(checkout) if refine_bursts else {}
    with (output/'build.log').open('w') as log:
        subprocess.run(['make','-s','-j'+str(jobs),'pokecrystal.gbc'],cwd=checkout,stdout=log,stderr=subprocess.STDOUT,check=True)
    for ext in ('gbc','sym','map'):
        shutil.copy2(checkout/('pokecrystal.'+ext),output/('pokecrystal-targeted-motion.'+ext))
    report=dict(waits=plan,evidence=evidence,motion=motion,frames=frames,bursts=bursts,
                production_sha=production,sha256=sha256((checkout/'pokecrystal.gbc').read_bytes()))
    assert production == sha256((ROOT/'pokecrystal.gbc').read_bytes())
    (output/'expansion.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(waits=len(plan),payload=motion['payload'],sha256=report['sha256'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=24)
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--output',type=Path,default=DEST)
    parser.add_argument('--refine-bursts',action='store_true')
    args=parser.parse_args()
    build(args.jobs,args.refresh,args.output,args.refine_bursts)
