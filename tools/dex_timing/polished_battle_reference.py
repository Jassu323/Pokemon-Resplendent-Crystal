"""Native Polished battle comparison without cartridge timing modifications."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import subprocess

from tools.pokedex_info_assets import constants
from .assets import read_symbols, sha256
from .cold_listing import Driver, ROOT, FRAME, KEY
from .shared_menu_regression import BOOT
from .new_entry import CORE_FILES

OUTPUT = ROOT / 'build/polished-battle-comparison-20261004'
SOURCE = OUTPUT / 'source'
MOVES = 'SURF RAZOR_LEAF GUST WHIRLPOOL ROCK_SLIDE EARTHQUAKE'.split()


def configuration():
    rom = SOURCE / 'polishedcrystal-3.2.3.gbc'
    sym = rom.with_suffix('.sym')
    return dict(rom=str(rom), sym=str(sym), core=str(OUTPUT/'setup/polished-core'),
                battery=str(OUTPUT/'setup/blank.sav'), symbols=read_symbols(sym))


def compile_core(cfg):
    folder=OUTPUT/'setup'
    folder.mkdir(exist_ok=True)
    symbols=cfg['symbols']
    lines=['#ifndef POLISHED_REFERENCE_SYMBOLS','#define POLISHED_REFERENCE_SYMBOLS']
    for name,(bank,pc) in symbols.items():
        if name.startswith(('w','h')) and '.' not in name:
            lines.extend((f'#define S_{name} {pc}',f'#define B_{name} {bank}'))
    for name in ('hSampledCryBlocks',):
        lines.append(f'#define S_{name} 0')
    lines.extend(('#define S_wMenuCursorPosition S_wMenuCursorY',
                  '#define PERF_ANIM_OBJECT_BYTES 240'))
    for n in range(5,9):
        lines.append(f'#define S_wChannel{n}Flags1 S_wChannel{n}Flags')
    profile={
        'battle_anim':('_PlayBattleAnim',True),'battle_script':('RunBattleAnimScript',True),
        'anim_tick':('RunBattleAnimScript.playframe',False),
        'anim_ready':('RunBattleAnimScript.not_rollout',False),
        'anim_command':('RunBattleAnimCommand',True),'anim_bg':('_ExecuteBGEffects',True),
        'anim_oam':('BattleAnim_UpdateOAM_All',True),'anim_object':('DoBattleAnimFrame',True),
        'anim_frame':('GetBattleAnimFrame',True),'anim_sine':('Sine',True),
        'anim_ly':('PushLYOverrides',True),'anim_pals':('BattleAnimRequestPals',True),
        'anim_wait':('DelayFrame',True),'anim_sound_wait':('WaitSFX',True),
        'sound':('PlaySFX',False),'stereo_sound':('PlayStereoSFX',False),
    }
    lines.append('static const struct { unsigned bank, pc; const char *name; bool span; } perf_points[] = {')
    for name,(label,span) in profile.items():
        bank,pc=symbols[label]
        lines.append(f'{{{bank},{pc},"{name}",{str(span).lower()}}},')
    lines.extend(('};','#endif'))
    header=folder/'symbols.h'
    header.write_text('\n'.join(lines)+'\n')
    sameboy=Path.home()/'Documents/GitHub/SameBoy'
    subprocess.run(['clang','-O2','-std=c11','-I'+str(sameboy),'-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER','-DGB_DISABLE_REWIND','-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH','-DGB_DISABLE_TIMEKEEPING','-DGB_VERSION="polished-reference"',
        f'-DPOLISHED_SYMBOLS="{header}"',f'-DDEX_PERFORMANCE_SYMBOLS="{header}"',
        '-DDEX_BATTLE_TIMING_TRACE','-DDEX_ANIMATION_REFERENCE_TRACE',
        str(ROOT/'tools/dex_timing/probes/polished_battle_reference.c'),
        *(str(sameboy/'Core'/(f+'.c')) for f in CORE_FILES),'-o',cfg['core']],check=True)
    Path(cfg['battery']).write_bytes(bytes(32768))


def run(driver,frames=1,keys=0):
    return driver.command(f'run 0 {round(frames*FRAME)} {keys}')


def reach(driver,cfg,label,keys=0,frames=600):
    bank,pc=cfg['symbols'][label]
    value=driver.command(f'restorerun {bank} {pc} {round(frames*FRAME)} {keys}')
    if value['hit']<0:
        raise RuntimeError(f'Did not reach {label}: {value}')
    return value


def put(driver,cfg,label,value):
    bank,pc=cfg['symbols'][label]
    for i,v in enumerate(value if isinstance(value,(bytes,list,tuple)) else [value]):
        driver.command(f'put {bank} {pc+i} {v}')


def prepare(cfg):
    core=Path(cfg['core'])
    if not core.exists(): compile_core(cfg)
    donor=OUTPUT/'setup/battle-main.s0'
    if donor.exists(): return
    driver=Driver(cfg['core'],cfg['rom'],BOOT,cfg['battery'],OUTPUT/'setup/bootstrap.log')
    try:
        bank,pc=cfg['symbols']['OptionsShared_RunLoop.loop']
        for n in range(600):
            r=driver.command(f'restorerun {bank} {pc} {20*FRAME} {KEY["a"] if n%2==0 else 0}')
            if r['hit']>=0: break
        else: raise RuntimeError('Initial options were not reached')
        run(driver,2,0)
        run(driver,10,KEY['b'])
        bank,pc=cfg['symbols']['FinishContinueFunction']
        for n in range(600):
            keys=KEY['a']|KEY['start'] if n%2==0 else 0
            r=driver.command(f'restorerun {bank} {pc} {20*FRAME} {keys}')
            if r['hit']>=0: break
        else:
            driver.command(f'image {OUTPUT}/setup/intro-stopped.ppm')
            raise RuntimeError('New-game introduction did not finish')
        values=constants(SOURCE/'constants/pokemon_constants.asm')
        put(driver,cfg,'wCurPartySpecies',values['MEGANIUM'])
        put(driver,cfg,'wCurPartyLevel',50)
        put(driver,cfg,'wCurForm',1)
        put(driver,cfg,'wMonType',0)
        bank,pc=cfg['symbols']['TryAddMonToParty']
        reply=driver.command(f'invoke {bank} {pc}')
        if reply.get('error') or driver.command('m')['party']!=1:
            raise RuntimeError('Native party initialization failed')
        reach(driver,cfg,'HandleMapTimeAndJoypad',frames=600)
        put(driver,cfg,'wCurPartySpecies',values['HOOTHOOT'])
        put(driver,cfg,'wTempWildMonSpecies',values['HOOTHOOT'])
        put(driver,cfg,'wWildMonForm',1)
        put(driver,cfg,'wCurPartyLevel',50)
        put(driver,cfg,'wCurForm',1)
        put(driver,cfg,'wOtherTrainerClass',0)
        put(driver,cfg,'wBattleType',0)
        bank,pc=cfg['symbols']['StartBattle']
        driver.command(f'enter {bank} {pc}')
        bank,pc=cfg['symbols']['BattleMenu.loop']
        for n in range(180):
            r=driver.command(f'restorerun {bank} {pc} {20*FRAME} {KEY["a"] if n%2==0 else 0}')
            if r['hit']>=0: break
        else: raise RuntimeError(f'Battle menu was not reached: {r}')
        run(driver,4)
        driver.command(f'save {donor}')
        driver.command(f'image {OUTPUT}/setup/battle-main.ppm')
        (OUTPUT/'setup/donor.json').write_text(json.dumps(driver.command('m'),indent=2)+'\n')
    finally:
        driver.command(f'image {OUTPUT}/setup/last-bootstrap.ppm')
        (OUTPUT/'setup/last-bootstrap.json').write_text(json.dumps(driver.command('m'),indent=2)+'\n')
        driver.close()


def execute(task):
    cfg,move,side,q=task
    observe=cfg.get('observe',True)
    folder=OUTPUT/('replays/polished' if observe else 'controls/polished')/f'{move.lower()}-{side}-q{q}'
    folder.mkdir(parents=True,exist_ok=True)
    driver=Driver(cfg['core'],cfg['rom'],BOOT,cfg['battery'],folder/'run.log')
    result=dict(variant='polished',move=move,side=side,quarter=q,issues=[])
    try:
        driver.command(f'load {OUTPUT}/setup/battle-main.s0')
        values=constants(SOURCE/'constants/move_constants.asm')
        target=values[move]
        idle=values['SPLASH']
        for who in ('BattleMon','EnemyMon','PartyMon1'):
            value=target if ((who=='EnemyMon')==(side=='foe')) else idle
            put(driver,cfg,'w'+who+'Moves',[value,0,0,0])
            put(driver,cfg,'w'+who+'PP',[60,0,0,0])
            put(driver,cfg,'w'+who+'Level',50)
            put(driver,cfg,'w'+who+'Status',0)
            for field in ('HP','MaxHP'):
                put(driver,cfg,'w'+who+field,(900).to_bytes(2,'big'))
            put(driver,cfg,'w'+who+'Stats',b''.join((200 if i in (1,4) else 80).to_bytes(2,'big') for i in range(5)))
        type_values=constants(SOURCE/'constants/type_constants.asm')
        for label in ('wBattleMonType','wEnemyMonType'):
            put(driver,cfg,label,[type_values['WATER']]*2)
        for label in ('wPlayerStatLevels','wEnemyStatLevels'):
            put(driver,cfg,label,[7,7,7,7,7,13,7,7])
        for who in ('Player','Enemy'):
            for n in range(1,6):
                label=f'w{who}SubStatus{n}'
                if label in cfg['symbols']: put(driver,cfg,label,0)
        # Polished chooses the enemy action before displaying the main menu.
        # Re-run its own AI after replacing the available move set.
        for label in ('AIChooseMove','SetPlayerTurn'):
            bank,pc=cfg['symbols'][label]
            reply=driver.command(f'invoke {bank} {pc}')
            if reply.get('error'): raise RuntimeError(f'Fixture call failed: {label}')
        run(driver,frames=q/FRAME)
        result['capture_start_t']=driver.command('m')['t']
        if observe: driver.command('perf 1')
        if observe and q==0:
            driver.command(f'perfimages {folder}/frame')
            driver.command(f'perfaudio {folder}/audio.raw')
        driver.events.clear()
        reach(driver,cfg,'MoveSelectionScreen.menu_loop',KEY['a'])
        run(driver,1)
        bank,pc=cfg['symbols']['BattleMenu.loop']
        for n in range(180):
            r=driver.command(f'restorerun {bank} {pc} {20*FRAME} {KEY["a"] if n%2==0 else 0}')
            if r['hit']>=0: break
        else: raise RuntimeError(f'Battle menu was not reached after move: {r}')
        run(driver,20)
        result['final']=driver.command('m')
        if not result['final']['double_speed'] or result['final']['crash']:
            result['issues'].append('Unexpected speed/crash state')
        requested=[e for e in driver.events if e['event']=='perf_phase' and e['name']=='battle_anim'
                   and e['anim_id']==target and e['turn']==(side=='foe')]
        costs=[e for e in driver.events if e['event']=='perf_cost' and e['name']=='battle_anim']
        result['requested_animations']=[dict(start=e,elapsed_t=next((c['elapsed'] for c in costs if c['t']==e['t']),None))
                                        for e in requested]
        if observe and (not requested or any(e['elapsed_t'] is None for e in result['requested_animations'])):
            result['issues'].append('Requested native animation did not complete')
    except Exception as error:
        result['issues'].append(str(error))
        driver.command(f'image {folder}/failure.ppm')
    finally:
        with gzip.open(folder/'events.jsonl.gz','wt') as stream:
            stream.write(''.join(json.dumps(e)+'\n' for e in driver.events))
        driver.close()
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--parity-only',action='store_true')
    parser.add_argument('--jobs',type=int,default=16)
    args=parser.parse_args()
    cfg=configuration()
    prepare(cfg)
    (OUTPUT/'configuration.json').write_text(json.dumps(dict(cfg,rom_sha256=sha256(Path(cfg['rom']).read_bytes())),indent=2)+'\n')
    if args.prepare_only: return
    if args.parity_only:
        tasks=[(dict(cfg,observe=False),m,s,0) for m in MOVES for s in ('player','foe')]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            rows=list(pool.map(execute,tasks))
        pairs=[]
        for row in rows:
            path=OUTPUT/'replays/polished'/f'{row["move"].lower()}-{row["side"]}-q0/result.json'
            baseline=json.loads(path.read_text())
            pairs.append(dict(move=row['move'],side=row['side'],equal=row['final']==baseline['final'],issues=row['issues']))
        (OUTPUT/'observer-parity.json').write_text(json.dumps(pairs,indent=2)+'\n')
        print(json.dumps(pairs),flush=True)
        return
    tasks=[(cfg,m,s,q) for m in MOVES for s in ('player','foe') for q in (0,17556,35112,52668)]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        rows=list(pool.map(execute,tasks))
    (OUTPUT/'polished-results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(dict(cases=len(rows),failures=[r for r in rows if r['issues']])),flush=True)


if __name__=='__main__': main()
