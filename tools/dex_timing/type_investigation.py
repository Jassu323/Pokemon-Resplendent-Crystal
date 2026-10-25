"""Private diagnostic ablations for the Type Matchups regression findings."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from .assets import Repository, sha256
from .cold_listing import ROOT, Driver, bootstrap
from .performance import core
from .type_matchups import BOOT, capture, enter_types
from . import animation_reference as motion, global_speed as speed
from tools.pokedex_info_assets import constants

SOURCE = ROOT / 'build/dex-types-cursors-20261011'
CAMPAIGN = ROOT / 'build/dex-types-full-regression-20261012'
OUTPUT = ROOT / 'build/dex-types-investigation-20261012'
MOVES = ('WATERFALL', 'WATER_PULSE', 'SURF', 'THUNDERBOLT')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def trace_ice():
    target = OUTPUT / 'ice-trace'
    repo = Repository(SOURCE / 'candidate', SOURCE / 'pokecrystal-dex-types.gbc',
                      SOURCE / 'pokecrystal-dex-types.sym')
    bank, pc = repo.symbols['PokedexTypes_Initialize.TransferTile']
    executable = core(repo, target, {}, ('-DDEX_TYPES_UPLOAD_DIAGNOSTIC',
                      f'-DDIAG_TRANSFER_BANK={bank}', f'-DDIAG_TRANSFER_PC={pc}',
                      f'-DS_wPokedexWRAM0Scratch={repo.symbols["wPokedexWRAM0Scratch"][1]}'))
    driver = Driver(executable, repo.rom_path, BOOT, SOURCE / 'pokecrystal-dex-types.sav',
                    target / 'trace.log')
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        enter_types(driver, repo, True)
        capture(driver, target / 'ice.png')
        write(target / 'events.json', [e for e in driver.events if e['event'].startswith('ice_')])
    finally:
        driver.close()
    print(json.dumps([e for e in driver.events if e['event'] in ('ice_change', 'ice_upload')]), flush=True)


def prepare_ablation(name):
    target = OUTPUT / name
    target.mkdir(parents=True, exist_ok=False)
    candidate = target / 'candidate'
    shutil.copytree(SOURCE / 'candidate', candidate)
    lcd = candidate / 'home/lcd.asm'
    vblank = candidate / 'home/vblank.asm'
    # Controlled mechanical removal only; these builds must not enter Types.
    if name in ('lcd-original', 'interrupts-original'):
        before = lcd.read_text()
        old = '\tcp $ff\n\tjp z, PokedexTypes_LCD\n'
        assert before.count(old) == 1
        lcd.write_text(before.replace(old, ''))
    if name in ('vblank-original', 'interrupts-original'):
        before = vblank.read_text()
        start = before.index('\t; Type Matchups\' ROM0 raster handler')
        end = before.index('\n\t; vblank-sensitive operations are done', start)
        vblank.write_text(before[:start] + before[end:])
    with (target / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j6', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(candidate / f'pokecrystal.{suffix}', target / f'pokecrystal.{suffix}')
    print(json.dumps(dict(variant=name, rom_sha256=sha256((target / 'pokecrystal.gbc').read_bytes()))), flush=True)


def configs():
    result = []
    parent = CAMPAIGN / 'runtime/animation/setup'
    for variant in ('baseline', 'acquisition'):
        paths = list((parent / variant).glob('*-acquisition-100-*/config.json'))
        assert len(paths) == 1, paths
        cfg = json.loads(paths[0].read_text())
        cfg.update(output_root=str(OUTPUT / 'battles'), capture_images=False, post_menu_frames=32)
        result.append(cfg)
    for variant in ('lcd-original', 'vblank-original', 'interrupts-original'):
        target = OUTPUT / variant
        config = dict(variant=variant, root=str(target / 'candidate'),
                      rom=str(target / 'pokecrystal.gbc'), sym=str(target / 'pokecrystal.sym'),
                      battery=str(CAMPAIGN / 'legacy-input.sav'), expected_double_speed=0,
                      expected_battle_speed=0, fresh_battle_fixture=True)
        motion.OUTPUT = OUTPUT / 'runtime/animation'
        motion.configuration = lambda _: config
        cfg = motion.prepare(variant, list(MOVES), 'investigation', coherent=True)
        cfg.update(output_root=str(OUTPUT / 'battles'), capture_images=False, post_menu_frames=32)
        result.append(cfg)
    write(OUTPUT / 'battle-configs.json', result)
    return result


def battles():
    path = OUTPUT / 'battle-configs.json'
    configurations = json.loads(path.read_text()) if path.exists() else configs()
    values = constants(ROOT / 'constants/move_constants.asm')
    tasks = [(cfg, move, values[move], side, q) for cfg in configurations
             for move in MOVES for side in ('player', 'foe') for q in (0, 17556, 35112, 52668)]
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(speed.move_job, tasks))
    write(OUTPUT / 'battles.json', rows)
    assert not any(r['issues'] for r in rows), [r for r in rows if r['issues']]
    print(json.dumps(dict(cases=len(rows), issues=0)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('ice', 'prepare', 'battles'))
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.action == 'ice':
        trace_ice()
    elif args.action == 'prepare':
        for name in ('lcd-original', 'vblank-original', 'interrupts-original'):
            prepare_ablation(name)
    else:
        battles()
