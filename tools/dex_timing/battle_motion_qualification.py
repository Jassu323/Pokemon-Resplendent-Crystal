"""Reuse the native menu, cry, Dex and save suites for the private motion ROM."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
from pathlib import Path
import shutil
import subprocess

from .animation_reference import OUTPUT, PROTOTYPE, TARGETS, configuration
from .assets import Repository, offset
from .cold_listing import ROOT
from . import global_speed as speed, performance, performance_audio as audio
from . import global_review_save as review, battle_pacing


def audio_config(quarter,variant='targeted',output=OUTPUT):
    cfg=configuration(variant)
    cfg['battery']=str(speed.BATTERY)
    return audio.prepare(cfg,output/'audio'/f'q{quarter}',0,quarter)


def audio_suite(jobs,variant='targeted'):
    with ProcessPoolExecutor(max_workers=4) as pool:
        configs=list(pool.map(partial(audio_config,variant=variant,output=OUTPUT),(0,17556,35112,52668)))
    tasks=[]
    for cfg in configs:
        folder=Path(cfg['output'])
        repo=Repository(ROOT,Path(cfg['rom']),Path(cfg['sym']))
        factory=audio.factory(repo,folder)
        base=offset(repo.symbols['NewPokedexOrder'])
        for name in audio.SPECIES:
            n=performance.names().index(name)
            index=int.from_bytes(repo.rom[base+2*n:base+2*n+2],'little')
            for context in ('player','blocking','stereo'):
                donor=cfg['states']['caterpie']['encounter'] if context=='player' else str(folder/'party.s0')
                state=folder/f'{name}-{context}.s0'
                subprocess.run([str(factory),cfg['rom'],donor,str(index),context,str(state)],capture_output=True,check=True)
                cfg['states'][name][context]=str(state)
            tasks.extend((cfg,name,c) for c in ('stats','catch','faint','player','blocking','stereo'))
    results=[]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(audio.execute,tasks):
            results.append(row)
            if len(results)%40==0 or row['issues']:
                print(json.dumps(dict(done=len(results),total=len(tasks),issues=row['issues'])),flush=True)
    (OUTPUT/'audio/report.json').write_text(json.dumps(dict(configurations=configs,results=results),indent=2)+'\n')
    battle_pacing.OUTPUT=OUTPUT
    battle_pacing.compare_audio(results)
    print(json.dumps(dict(cases=len(results),failures=sum(bool(r['issues']) for r in results))),flush=True)


def manual(mode='targeted'):
    folder=OUTPUT/'manual-review'
    folder.mkdir(exist_ok=True)
    party=(
        ('KYOGRE','WATER',('SURF','WATER_PULSE','CAUSTIC','THUNDERBOLT')),
        ('GARCHOMP','PACE',('DRAGON_DANCE','SUPERPOWER','SOLARBEAM','DAZZLING_GLEAM')),
        ('RAYQUAZA','CHARGE',('SHOCK_WAVE','WILD_CHARGE','VOLT_TACKLE','ENERGY_BALL')),
        ('DUSKNOIR','CONTROL',('SHADOW_BALL','PETAL_DANCE','THUNDERSHOCK','FIRE_BLAST')),
        ('MEGANIUM','LEAVES',('RAZOR_LEAF','MAGICAL_LEAF','SEISMIC_TOSS','EARTHQUAKE')),
        ('METAGROSS','HEAVY',('HYDRO_PUMP','OVERHEAT','METEOR_DIVE','AERIAL_CRASH')))
    if mode.startswith('expanded'):
        party=(
            ('KYOGRE','WATER',('SURF','WATER_PULSE','HYDRO_PUMP','WATERFALL')),
            ('MEGANIUM','LEAVES',('LEAF_BLADE','RAZOR_LEAF','MAGICAL_LEAF','PETAL_DANCE')),
            ('DUSKNOIR','HAZE',('POISON_GAS','CAUSTIC','WHIRLPOOL','GUST')),
            ('GARCHOMP','CHARGE',('DRAGON_DANCE','SUPERPOWER','SOLARBEAM','DAZZLING_GLEAM')),
            ('MEWTWO','MIND',('PSYCHIC_M','RECOVER','SHADOW_BALL','SEISMIC_TOSS')),
            ('METAGROSS','OTHER',('THUNDERBOLT','SHOCK_WAVE','WILD_CHARGE','FIRE_BLAST')))
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    report=review.create(repo,speed.BATTERY,folder/'animation-review.sav',party,
                         TARGETS+['VOLT_TACKLE','ENERGY_BALL'] if mode.startswith('expanded') else TARGETS)
    for arm,source in (('normal',ROOT/'pokecrystal'),('double',speed.BASE/'final/pokecrystal-global-double-speed'),
                        (mode,PROTOTYPE/'pokecrystal-targeted-motion')):
        target=folder/arm/('pokecrystal-animation-'+arm)
        target.parent.mkdir(exist_ok=True)
        for ext in ('.gbc','.sym','.map'):
            shutil.copy2(source.with_suffix(ext),target.with_suffix(ext))
        shutil.copy2(folder/'animation-review.sav',target.with_suffix('.sav'))
    (folder/'animation-review.json').write_text(json.dumps(report,indent=2)+'\n')
    with ProcessPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(partial(review.verify,review=folder),('normal','double',mode)))
    (folder/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(verified_arms=len(results),moves=report['moves'])),flush=True)


def main():
    global OUTPUT, PROTOTYPE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',choices=('audio','menus','dex-prepare','manual'))
    parser.add_argument('--jobs',type=int,default=24)
    parser.add_argument('--variant',default='targeted')
    args=parser.parse_args()
    if args.variant!='targeted':
        PROTOTYPE=Path(configuration(args.variant)['rom']).parent
        OUTPUT=OUTPUT/(args.variant+'-qualification')
        OUTPUT.mkdir(parents=True,exist_ok=True)
    if args.suite=='audio':return audio_suite(args.jobs,args.variant)
    if args.suite=='manual':return manual(args.variant)
    cfg=configuration(args.variant)
    cfg.update(battery=str(speed.BATTERY),menu_output=str(OUTPUT/'menus'))
    if args.suite=='menus':
        with ProcessPoolExecutor(max_workers=5) as pool:
            rows=list(pool.map(speed.menu_job,[(cfg,place) for place in ('standard','battle','mart','puzzle','game-corner')]))
        (OUTPUT/'menus/report.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(json.dumps(rows),flush=True)
    else:
        result=performance.prepare(Path(cfg['rom']),Path(cfg['sym']),speed.BATTERY,OUTPUT/'dex-setup')
        print(json.dumps(dict(config=str(OUTPUT/'dex-setup/config.json'))),flush=True)


if __name__=='__main__':
    main()
