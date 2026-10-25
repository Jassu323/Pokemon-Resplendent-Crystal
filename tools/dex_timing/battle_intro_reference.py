"""Host-only native sliding-intro cadence comparison for private speed builds."""
import argparse
from collections import deque
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics
import subprocess

from PIL import Image, ImageChops

from . import animation_reference as motion, global_speed as speed
from . import performance, performance_audio as audio, shared_menu_regression as menu
from .assets import Repository, offset
from .cold_listing import Driver, FRAME, KEY, ROOT
from .shared_menu_fixtures import make_fixture

OUTPUT = motion.OUTPUT / 'wild-intro'
SPECIES = 'caterpie mewtwo dusknoir metagross luxray garchomp bastiodon weavile'.split()


def prepare(variant):
    cfg = motion.configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = OUTPUT / 'setup' / variant
    points = dict(speed.EXTRA, intro=('BattleIntroSlidingPics', True),
                  intro_step=('BattleIntroSlidingPics.subfunction5', True),
                  intro_oam=('BattleIntroSlidingPics.subfunction3', True),
                  intro_delay=('BattleIntroSlidingPics.DelayFrame', True),
                  frontpic=('BattleFrontpicProducer_Service', True))
    performance.core(repo, output, points)
    header = output / 'performance-symbols.h'
    with header.open('a') as stream:
        for name in ('hSCX', 'wBattleFrontpicProducerState', 'hDMATransfer'):
            stream.write(f'#define S_{name} {repo.symbols[name][1]}\n')
    binary = menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_INTRO_TRACE',
         f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"'))
    battery = output / 'private.sav'
    make_fixture(repo, speed.BATTERY, battery, ('ROUTE_30', 13, 49))
    driver = Driver(binary, cfg['rom'], menu.BOOT, battery, output / 'setup.log')
    try:
        menu.boot_overworld(driver, repo)
        menu.settle_map_input(driver, repo)
        driver.command(f'save {output / "overworld.s0"}')
        for q in (0, 17556, 35112, 52668):
            driver.command(f'load {output / "overworld.s0"}')
            driver.command(f'run 0 {q} 0')
            bank, pc = repo.symbols['LoadEnemyMon']
            for n in range(300):
                key = 'up' if (n // 20) % 2 == 0 else 'down'
                state = driver.command(f'restorerun {bank} {pc} {12*FRAME} {KEY[key]}')
                if audio.at(state, repo, 'LoadEnemyMon'):
                    break
            else:
                raise RuntimeError('No native encounter')
            driver.command(f'save {output / ("encounter-q"+str(q)+".s0")}')
    finally:
        driver.close()
    factory = audio.factory(repo, output)
    order = offset(repo.symbols['NewPokedexOrder'])
    cfg.update(core=str(binary), battery=str(battery), fixtures={})
    for species in SPECIES:
        ordinal = performance.names().index(species)
        index = int.from_bytes(repo.rom[order+ordinal*2:order+ordinal*2+2], 'little')
        cfg['fixtures'][species] = {}
        for q in (0, 17556, 35112, 52668):
            destination = output / f'{species}-q{q}.s0'
            subprocess.run([str(factory), cfg['rom'], str(output / f'encounter-q{q}.s0'),
                            str(index), 'encounter', str(destination)], check=True, capture_output=True)
            cfg['fixtures'][species][str(q)] = str(destination)
    (output / 'config.json').write_text(json.dumps(cfg, indent=2)+'\n')
    return cfg


def job(task):
    cfg, species, quarter = task
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = OUTPUT / cfg['variant'] / f'{species}-q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    driver = Driver(cfg['core'], cfg['rom'], menu.BOOT, cfg['battery'], output / 'run.log')
    try:
        driver.command(f'load {cfg["fixtures"][species][str(quarter)]}')
        if not audio.at(driver.command('m'), repo, 'BattleIntroSlidingPics'):
            audio.run(driver, repo, 'BattleIntroSlidingPics', frames=600)
        driver.command('perf 1')
        driver.events.clear()
        driver.command(f'perfimages {output / "frame"}')
        # Fresh presses must dismiss post-intro text; holding A throughout
        # the slide does not guarantee the following text accepts an input.
        audio.until(driver, repo, 'LoadBattleMenuGraphic.loop', attempts=220)
        events = driver.events.copy()
        speed.save_events(output / 'events.jsonl.gz', events)
    finally:
        driver.close()
    span = next(e for e in events if e['event']=='perf_cost' and e['name']=='intro')
    start, end = span['t'], span['t']+span['elapsed']
    steps = [e for e in events if e['event']=='perf_phase' and e['name']=='intro_step' and start<=e['t']<end]
    displays = [e for e in events if e['event']=='intro_display' and start<=e['t']<end]
    x = [bytes.fromhex(e['oam'])[1] for e in displays]
    frames = [e for e in events if e['event']=='perf_frame' and start<=e['t']<end]
    translations = []
    for previous, current in zip(frames, frames[1:]):
        a = Image.open(output / f'frame-{previous["display"]:03d}.ppm').convert('RGB')
        b = Image.open(output / f'frame-{current["display"]:03d}.ppm').convert('RGB')
        # Above the trainer's OAM: the foe is a static BG picture during the
        # slide. Compare a fixed interior crop, excluding incoming edge pixels.
        errors = []
        for shift in (0, 2, 4):
            histogram = ImageChops.difference(a.crop((4-shift,0,160-shift,44)),
                                             b.crop((4,0,160,44))).histogram()
            errors.append(sum(histogram)-sum(histogram[i] for i in (0,256,512)))
        translations.append(dict(display=current['display'], errors=errors,
                                 shift=(0,2,4)[errors.index(min(errors))]))
    # Initial setup can legitimately show the same position twice. Exclude
    # its first three displays, not any irregular movement later in the slide.
    irregular = [t for t in translations if 4<=t['display']<frames[-1]['display']
                 and t['errors'][1]!=0]
    result = dict(variant=cfg['variant'], species=species, quarter=quarter,
        intervals=span['elapsed']/FRAME, ms=span['elapsed']*1000/4194304,
        steps=len(steps), step_lines=[e['ly'] for e in steps],
        step_gaps=[(b['t']-a['t'])/FRAME for a,b in zip(steps,steps[1:])],
        display_x=x, x_deltas=[(a-b)&255 for a,b in zip(x,x[1:])],
        producer_at_display=[e['producer'] for e in displays],
        pixel_translations=translations, irregular_translations=irregular,
        issues=[e for e in events if e['event'] in ('audio_miss','miss','illegal')])
    (output / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def prepare_trainer(cfg, quarter=0):
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = OUTPUT / 'setup' / cfg['variant']
    battery = output / f'trainer-q{quarter}.sav'
    # This baseline fixture already declares Joey unbeaten and the Route 30
    # battle accessible. No battle/PPU/audio work is skipped or patched.
    source = Path(cfg.get('trainer_seed', speed.BASE / 'gameplay/production/trainer/private.sav'))
    make_fixture(repo, source, battery, ('ROUTE_30_BERRY_HOUSE',2,6))
    driver = Driver(cfg['core'], cfg['rom'], menu.BOOT, battery, output / f'trainer-q{quarter}-setup.log')
    try:
        menu.boot_overworld(driver,repo)
        menu.settle_map_input(driver,repo)
        menu.walk_through_door(driver,repo,'down',1)
        state = driver.command('m')
        blocks = offset(repo.symbols['Route30_Blocks'])
        collision = offset(repo.symbols['TilesetJohtoColl'])
        start = (state['wXCoord'],state['wYCoord'])
        todo, seen = deque([(start,[])]), {start}
        route = None
        while todo:
            (x,y),path = todo.popleft()
            if (x,y)==(2,29):
                route=path
                break
            for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
                cell=(x+dx,y+dy)
                if cell in seen or cell in ((5,39),(2,28)) or not (0<=cell[0]<20 and 0<=cell[1]<54):
                    continue
                tile=repo.rom[blocks+cell[1]//2*10+cell[0]//2]
                if repo.rom[collision+tile*4+cell[1]%2*2+cell[0]%2] in (0,0x10,0x14,0x18):
                    seen.add(cell)
                    todo.append((cell,path+[cell]))
        if route is None:
            raise RuntimeError('No native path to Joey')
        for x,y in route:
            current=driver.command('m')
            axis='x' if current['wXCoord']!=x else 'y'
            menu.walk_to(driver,repo,axis,x if axis=='x' else y)
        menu.run(driver, repo, frames=quarter/FRAME)
        menu.tap(driver,repo,'up',held=3,released=14)
        audio.until(driver,repo,'BattleIntroSlidingPics',attempts=220)
        state=output/f'joey-q{quarter}.s0'
        driver.command(f'save {state}')
    finally:
        driver.close()
    cfg=dict(cfg,battery=str(battery),fixtures={'joey':{str(quarter):str(state)}})
    return cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variants', nargs='+', default=['production','surf-production'])
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--trainer', action='store_true')
    args = parser.parse_args()
    if args.trainer:
        configs = [prepare_trainer(json.loads((OUTPUT/'setup'/v/'config.json').read_text())) for v in args.variants]
        tasks = [(cfg,'joey',0) for cfg in configs]
    else:
        configs = [prepare(v) for v in args.variants]
        tasks = [(cfg,s,q) for cfg in configs for s in SPECIES for q in (0,17556,35112,52668)]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(job, tasks))
    (OUTPUT / (('trainer-' if args.trainer else 'report-')+'-'.join(args.variants)+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([dict(variant=v,species=s,intervals=statistics.median(r['intervals'] for r in rows
                if r['variant']==v and r['species']==s),
            irregular_displays=sum(len(r['irregular_translations']) for r in rows
                if r['variant']==v and r['species']==s))
            for v in args.variants for s in (['joey'] if args.trainer else SPECIES)]))


if __name__=='__main__':
    main()
