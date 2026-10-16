"""Native Pay Day -> capture -> registration -> payout positive controls."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import subprocess
import traceback

from . import gotcha_boundary as catch, performance_audio as audio, shared_menu_regression as menu
from . import global_review_save as review
from .cold_listing import Driver, ROOT
from .new_entry import CORE_FILES


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def factory(repo, folder):
    folder.mkdir()
    lines=[]
    for key,label in dict(ENEMY='LoadEnemyMon',ALLOCATE='GetMoveIDFromIndex').items():
        bank,pc=repo.symbols[label]
        lines += [f'#define B_{key} {bank}',f'#define P_{key} {pc}']
    for label in ('wMoveIndexTableEntries','wPartyMon1Moves','wPartyMon1PP','wPartyMon1Item','wCurPartyLevel','wMoney'):
        bank,at=repo.symbols[label]
        lines += [f'#define B_{label} {bank}',f'#define S_{label} {at}']
    header=folder/'symbols.h';header.write_text('\n'.join(lines)+'\n')
    binary=folder/'fixture';sameboy=Path.home()/'Documents/GitHub/SameBoy'
    subprocess.run(['clang','-O2','-std=c11','-I'+str(sameboy),'-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER','-DGB_DISABLE_REWIND','-DGB_DISABLE_CHEATS','-DGB_DISABLE_CHEAT_SEARCH',
        '-DGB_DISABLE_TIMEKEEPING','-DGB_VERSION="payday-control"',
        f'-DPAYDAY_FIXTURE_SYMBOLS="{header}"',str(ROOT/'tools/dex_timing/probes/registration_payday_fixture.c'),
        *(str(sameboy/'Core'/(f+'.c')) for f in CORE_FILES),'-o',str(binary)],check=True)
    return str(binary)


def setup(source, output, battery, variant):
    output.mkdir(parents=True)
    config=dict(root=str(source),rom=str(source/'pokecrystal.gbc'),sym=str(source/'pokecrystal.sym'),
                battery=str(battery),expected_double_speed=1,variant=variant)
    repo=catch.repo_for(config)
    seed=output/'party.sav'
    party=(('BULBASAUR','LEARN',('BODY_SLAM','THUNDERBOLT','WATER_PULSE','POISON_GAS')),
           ('CATERPIE','EVOLVE',('TACKLE','STRING_SHOT','BODY_SLAM','POISON_GAS')),*review.PARTY[2:])
    review.create(repo,battery,seed,party,level=6)
    config['battery']=str(seed)
    previous=audio.SPECIES
    try:
        audio.SPECIES=('caterpie',)
        config=audio.prepare(config,output/'native',0,0)
    finally:audio.SPECIES=previous
    repo=catch.repo_for(config)
    config['core']=str(catch.compiler(repo,output/'observer'))
    config['factory']=factory(repo,output/'fixture')
    write(output/'config.json',config)
    return config


def balance(driver,repo):
    return int.from_bytes(catch.ram(driver,repo,'wMoney',3),'big')


def amount(driver,repo):
    return int.from_bytes(catch.ram(driver,repo,'wPayDayMoney',3),'big')


def execute(task):
    config,output,coin,capped=task
    repo=catch.repo_for(config)
    folder=output/config['variant']/f'coin{coin}-cap{capped}';folder.mkdir(parents=True)
    initial=999995 if capped else 2137
    state=folder/'fixture.s0'
    fixture=subprocess.run([config['factory'],config['rom'],config['states']['caterpie']['encounter'],
        str(coin),str(initial),str(state)],check=True,capture_output=True,text=True)
    row=dict(variant=config['variant'],coin=coin,capped=capped,fixture=json.loads(fixture.stdout),issues=[],**repo.hashes)
    driver=Driver(config['core'],config['rom'],menu.BOOT,config['battery'],folder/'native.log')
    try:
        driver.command(f'load {state}');driver.command('perf 1');driver.events.clear()
        audio.until(driver,repo,'BattleMenu.loop')
        menu.run(driver,repo,frames=24)
        row['before']=balance(driver,repo)
        row['level']=catch.number(driver,repo,'wBattleMonLevel')
        assert row['before']==initial and amount(driver,repo)==0
        assert catch.permanent(driver,repo,catch.ram(driver,repo,'wBattleMonMoves',4),'Move')[0]==6
        audio.until(driver,repo,'BattleCommand_PayDay')
        row['native_move_reached']=True
        audio.until(driver,repo,'BattleMenu.loop')
        row['earned']=amount(driver,repo)
        row['amulet_flag']=catch.number(driver,repo,'wAmuletCoin')
        assert row['earned']==2*row['level'] and row['amulet_flag']==coin
        menu.tap(driver,repo,'down')
        audio.until(driver,repo,'BattlePack.loop')
        for _ in range(10):
            if catch.number(driver,repo,'wCurPocket')==1:break
            menu.tap(driver,repo,'right',released=30)
        audio.until(driver,repo,'NewPokedexEntry')
        row['before_registration']=amount(driver,repo)
        interactive='NewDexRegistration_Loop' in repo.symbols
        audio.until(driver,repo,'NewDexRegistration_Loop' if interactive else
                    'NewPokedexEntry.WaitPressAorB_AnimateFrontpic',key=None)
        menu.run(driver,repo,frames=180)
        if interactive and coin:
            menu.tap(driver,repo,'right')
            if capped:menu.tap(driver,repo,'right')
            menu.tap(driver,repo,'a');menu.run(driver,repo,frames=120)
        audio.until(driver,repo,'PokeBallEffect.skip_pokedex',key='b')
        row['after_registration']=amount(driver,repo)
        assert row['after_registration']==row['earned']==row['before_registration']
        audio.until(driver,repo,'CheckPayDay',key='b')
        row['before_payout']=amount(driver,repo)
        assert row['before_payout']==row['earned']
        catch.world(driver,repo,'b')
        row['after']=balance(driver,repo)
        row['expected']=min(999999,initial+row['earned']*(2 if coin else 1))
        assert row['after']==row['expected']
        driver.command(f'image {folder/"returned.ppm"}')
    except Exception as error:
        row['issues'].append(f'{type(error).__name__}: {error}');row['traceback']=traceback.format_exc()
    finally:
        with gzip.open(folder/'events.jsonl.gz','wt') as stream:
            stream.write(''.join(json.dumps(e)+'\n' for e in driver.events))
        driver.close()
    row['native_warnings']=(folder/'native.log').read_text()
    write(folder/'result.json',row)
    print(json.dumps(row),flush=True)
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--battery',type=Path,default=catch.SEED);p.add_argument('--jobs',type=int,default=6)
    args=p.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use fresh build output')
    configs=[setup(source.resolve(),output/'setup'/variant,args.battery.resolve(),variant)
             for source,variant in ((args.baseline,'production'),(args.candidate,'candidate'))]
    tasks=[(cfg,output/'runs',coin,cap) for cfg in configs for coin in (0,1) for cap in (0,1)]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:rows=list(pool.map(execute,tasks))
    record=dict(cases=len(rows),failures=sum(bool(r['issues'] or r['native_warnings']) for r in rows),
                results=rows,scope='Actual native use of Pay Day before capture, with coin and wallet cap')
    write(output/'report.json',record)
    return int(bool(record['failures']))


if __name__=='__main__':raise SystemExit(main())
