"""Read-only native Surf teardown audit of unchanged production/prototype ROMs."""
from concurrent.futures import ProcessPoolExecutor
import argparse
import json
from pathlib import Path

from PIL import Image

from tools.pokedex_info_assets import constants
from .assets import Repository
from .cold_listing import ROOT, Driver, FRAME
from . import animation_reference as reference
from . import global_speed as speed, performance, performance_audio as audio
from . import shared_menu_regression as menu

OUTPUT = reference.OUTPUT / 'surf-cleanup-diagnostic'
VARIANTS = ('production', 'targeted', 'surf-intro')
MOVES = ('SURF', 'CAUSTIC')


def prepare(variant):
    cfg = json.loads((reference.OUTPUT / 'setup' / variant / 'config.json').read_text())
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    folder = OUTPUT / 'observers' / variant
    points = dict(reference.timing.POINTS,
                  anim_owner=('PlayBattleAnim', True),
                  surf_check=('BattleAnimFunc_Surf.three', False),
                  surf_deinit=('BattleAnimFunc_Surf.four', False))
    performance.core(repo, folder, points)
    header = folder / 'performance-symbols.h'
    with header.open('a') as out:
        for label in ('wBattleAnimAddress', 'wBattleAnimDelay', 'wBattleAnimParam',
                      'wActiveAnimObjects', 'wBGEffect1', 'hLCDCPointer',
                      'hLYOverrideStart', 'hLYOverrideEnd', 'hSCY', 'LCD', 'wLYOverrides'):
            out.write(f'#define S_{label} {repo.symbols[label][1]}\n')
        out.write(f'#define S_wActiveAnimObjects_bank {repo.symbols["wActiveAnimObjects"][0]}\n')
    cfg['core'] = str(menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', folder,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_TIMING_TRACE',
         '-DDEX_ANIMATION_REFERENCE_TRACE', '-DDEX_SURF_CLEANUP_TRACE',
         f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"')))
    cfg.update(output_root=str(OUTPUT / 'replays'), capture_images=False, post_menu_frames=60)
    (folder / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')
    return cfg


def case(task):
    cfg, move, index, side, phase = task
    speed.move_job(task)
    folder = Path(cfg['output_root']) / cfg['variant'] / f'{move.lower()}-{side}-q{phase}'
    source = reference.events(folder)
    result = json.loads((folder / 'result.json').read_text())
    first = result['requested_animations'][0]
    begin, end = first['start']['t'], first['start']['t'] + first['elapsed_t']
    scripts = sorted((e for e in source if e['event'] == 'perf_cost' and e['name'] == 'battle_script'
                      and begin <= e['t'] < end), key=lambda e: e['t'])
    primary = scripts[0]
    checks = [e for e in source if e['event'] == 'surf_cleanup']
    relevant = [e for e in checks if primary['t'] <= e['t'] <= end]
    deinit = [e for e in relevant if e['point'] == 'surf_deinit']
    returns = [e for e in relevant if e['point'] in ('battle_script', 'battle_anim')]
    owner = next((e for e in checks if e['point'] == 'anim_owner' and end <= e['t'] <= end + 1000), None)
    row = dict(variant=cfg['variant'], move=move, side=side, phase=phase, issues=result['issues'],
               primary_intervals=primary['elapsed']/FRAME, cleanup_calls=len(deinit),
               script_returns=returns, owner_return=owner,
               cleanup_violation=owner is None or owner['lcd_pointer'] != 0,
               wrong_bank_read_samples=[e for e in source if e['event'] == 'surf_wrong_bank'],
               wrong_bank_reads=checks[-1]['wrong_bank_reads'],
               lingering_frames=[e for e in checks if e['point'] == 'display' and e['t'] > end
                                 and e['lcd_pointer'] == 0x42 and e['svbk'] != 5])
    previous = json.loads((reference.OUTPUT / 'replays' / cfg['variant'] /
                           folder.name / 'result.json').read_text())
    row['instrumentation_timing_parity'] = result['requested_animations'] == previous['requested_animations']
    Image.open(folder / 'final.ppm').resize((640, 576), Image.Resampling.NEAREST).save(folder / 'final.png')
    (folder / 'cleanup.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def recovery(cfg):
    """Reproduce, idle at the real battle menu, then flee using normal input."""
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    folder = OUTPUT / 'battle-exit'
    folder.mkdir(exist_ok=True)
    driver = Driver(cfg['core'], cfg['rom'], menu.BOOT, cfg['battery'], folder / 'run.log')
    try:
        # Surf goes last in this control, so the other-side Splash cannot
        # subsequently mask the missing cleanup by resetting its own scroll.
        driver.command(f'load {cfg["fixtures"]["SURF"]["foe"]}')
        driver.command('perf 1')
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        index = constants(ROOT / 'constants/move_constants.asm')['SURF']
        for _ in range(8):
            audio.until(driver, repo, 'BattleMenu.loop', attempts=200)
            if any(e['event'] == 'perf_phase' and e['name'] == 'battle_anim'
                   and e['anim_id'] == index and e['turn'] == 1 for e in driver.events):
                break
            audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        else:
            raise RuntimeError('Recovery test did not execute Surf')
        menu.run(driver, repo, frames=60)
        before = dict(state=driver.command('m'),
                      lcd_pointer=audio.value(driver, repo, 'hLCDCPointer'))
        speed.save_events(folder / 'events.jsonl.gz', driver.events)
        (folder / 'before.json').write_text(json.dumps(before, indent=2) + '\n')
        expected = 0x42 if cfg['variant']=='surf-intro' else 0
        if before['lcd_pointer'] != expected:
            raise RuntimeError('Unexpected scroll ownership at the completed battle menu')
        driver.command(f'image {folder / "before.ppm"}')
        menu.tap(driver, repo, 'right')
        menu.tap(driver, repo, 'down')
        selected = driver.command('m')
        after = audio.until(driver, repo, 'HandleMapTimeAndJoypad', attempts=300)
        menu.run(driver, repo, frames=60)
        after = dict(state=driver.command('m'),
                     lcd_pointer=audio.value(driver, repo, 'hLCDCPointer'))
        driver.command(f'image {folder / "after.ppm"}')
        speed.save_events(folder / 'events.jsonl.gz', driver.events)
        result = dict(before=before, selected=selected, after=after)
        for name in ('before', 'after'):
            Image.open(folder / f'{name}.ppm').resize((640, 576), Image.Resampling.NEAREST).save(folder / f'{name}.png')
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


def main():
    global OUTPUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variants',nargs='+',default=VARIANTS)
    args=parser.parse_args()
    if args.variants != list(VARIANTS) and tuple(args.variants) != VARIANTS:
        OUTPUT=reference.OUTPUT/('surf-cleanup-diagnostic-'+'-'.join(args.variants))
    configs = [prepare(v) for v in args.variants]
    values = constants(ROOT / 'constants/move_constants.asm')
    tasks = [(cfg, move, values[move], side, phase) for cfg in configs for move in MOVES
             for side in ('player', 'foe') for phase in (0, 17556, 35112, 52668)]
    with ProcessPoolExecutor(max_workers=24) as pool:
        rows = list(pool.map(case, tasks))
    data = dict(cases=len(rows), rows=rows, battle_exit=recovery(configs[-1]))
    (OUTPUT / 'report.json').write_text(json.dumps(data, indent=2) + '\n')
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if k not in ('lingering_frames', 'script_returns', 'wrong_bank_read_samples')}
                         | dict(script_returns=[(e['lcd_pointer'], e['surf_state'], e['surf_y'])
                                                for e in row['script_returns']],
                                lingering_frames=len(row['lingering_frames']))), flush=True)


if __name__ == '__main__':
    main()
