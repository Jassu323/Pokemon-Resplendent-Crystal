"""Private whole-game speed qualification using native input and declared fixtures.

The runner measures physical LCD time. Fixtures do not change speed, timing,
PPU state, audio state, instruction execution or animation-ready flags.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import re
import statistics
import subprocess

from .assets import Repository
from .cold_listing import Driver, ROOT, FRAME, KEY
from . import performance, performance_audio as audio, shared_menu_regression as menu
from .new_entry import CORE_FILES
from .shared_menu_fixtures import make_fixture

BASE = ROOT / 'build/global-speed-20261004'
BATTERY = ROOT / 'build/dex-performance-20261004/combined-no-lookahead/measurements/private.sav'
REQUESTED = '''THUNDERSHOCK THUNDERBOLT THUNDER HYDRO_PUMP WATER_PULSE WATERFALL
SLEEP_POWDER STUN_SPORE POISONPOWDER SPORE FIRE_BLAST ACID CAUSTIC CORROSION WISH
DISARMING_VOICE FAIRY_WIND SILVER_WIND SLUDGE_WAVE SLUDGE_BOMB SUPERPOWER WILD_CHARGE
SHOCK_WAVE LEAF_BLADE FORCE_PALM RAZOR_LEAF MAGICAL_LEAF SEISMIC_TOSS AROMATHERAPY
PETAL_DANCE OUTRAGE DRAGON_CLAW METEOR_DIVE AERIAL_CRASH PILEDRIVER OVERHEAT POISON_GAS'''.split()
ADDED_NEW = '''HEAT_WAVE WILL_O_WISP BRICK_BREAK METEOR_MASH SIGNAL_BEAM SHADOW_PUNCH
EXTRASENSORY BULLET_SEED IRON_DEFENSE MUD_SHOT MOONBLAST DAZZLING_GLEAM'''.split()
ADDED_OLD = '''POUND KARATE_CHOP DOUBLESLAP FIRE_PUNCH ICE_PUNCH THUNDERPUNCH BODY_SLAM
SWORDS_DANCE CUT GUST FLY VINE_WHIP DOUBLE_KICK SURF ICE_BEAM BLIZZARD HYPER_BEAM
EARTHQUAKE DIG PSYCHIC_M RECOVER SELFDESTRUCT EXPLOSION SWIFT SOLARBEAM SHADOW_BALL
ROLLOUT RAIN_DANCE SUNNY_DAY WHIRLPOOL'''.split()
EXTRA = dict(audio.EXTRA, battle_anim=('_PlayBattleAnim', True),
             battle_script=('RunBattleAnimScript', True), battle_step=('RunBattleAnimCommand', False),
             pack_update=('Pack_UpdatePocket', True), tm_update=('TMHMCase_UpdateSelection', True),
             apricorn_update=('ApricornBox_UpdateSelection', True),
             fish=('FishFunction', True), phone=('Phone_StartRinging', False),
             heal=('HealParty', True), save_game=('SaveGameData', True),
             heal_animation=('HealMachineAnim', True),
             evolution=('EvolutionAnimation', True), egg_hatch=('EggHatch_AnimationSequence', True))


def configuration(variant):
    if variant == 'production':
        return dict(rom=str(ROOT / 'pokecrystal.gbc'), sym=str(ROOT / 'pokecrystal.sym'),
                    root=str(ROOT), battery=str(BATTERY), expected_double_speed=0)
    if variant == 'battle-normal':
        folder = ROOT / 'build/battle-normal-speed-20261004/prototype'
        return dict(rom=str(folder / 'pokecrystal-battle-normal-speed.gbc'),
                    sym=str(folder / 'pokecrystal-battle-normal-speed.sym'), root=str(folder / 'candidate'),
                    battery=str(BATTERY), expected_double_speed=1, expected_battle_speed=0,
                    audio_fixture_dir=str(ROOT / 'build/battle-normal-speed-20261004/audio/battle-normal/q0'))
    folder = BASE / variant
    return dict(rom=str(folder / 'pokecrystal-global-double-speed.gbc'),
                sym=str(folder / 'pokecrystal-global-double-speed.sym'), root=str(folder / 'candidate'),
                battery=str(BATTERY), expected_double_speed=1)


def compile_core(repo, output):
    bank, pc = repo.symbols['SampledCry_RestartCH3']
    repo.symbols['@wave_committed'] = bank, pc + 23
    performance.core(repo, output, EXTRA)
    header = (output / 'performance-symbols.h').resolve()
    return menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
                                 ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE',
                                  f'-DDEX_PERFORMANCE_SYMBOLS="{header}"'))


def save_events(path, events):
    with gzip.open(path, 'wt') as stream:
        stream.write(''.join(json.dumps(e) + '\n' for e in events))


def menu_job(item):
    arm, location = item
    cfg = arm if isinstance(arm, dict) else configuration(arm)
    variant = cfg.get('variant', arm)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = Path(cfg.get('menu_output', BASE / 'menus')) / variant / location
    output.mkdir(parents=True, exist_ok=True)
    places = dict(standard=None, battle=('ROUTE_30', 13, 49),
                  mart=('CHERRYGROVE_MART', 3, 3), puzzle=('RUINS_OF_ALPH_KABUTO_CHAMBER', 3, 4),
                  **{'game-corner': ('GOLDENROD_GAME_CORNER', 14, 9)})
    battery = output / 'private.sav'
    make_fixture(repo, Path(cfg['battery']), battery, places[location])
    core = compile_core(repo, output)
    if location == 'standard':
        menu.smoke(output, repo, core, battery)
        states = menu.menu_states(output, repo, core, battery)
        states.update(menu.extra_menu_states(output, repo, core, battery))
        expanded = menu.expanded_menu_states(output, repo, core, battery)
        states.update(expanded)
        states['start-menu'] = {}
    else:
        states = menu.location_menu_states(output, repo, core, battery, location)
    inputs = menu.menu_inputs(output, repo, core, battery, states)
    controls = menu.menu_controls(output, repo, core, battery, states)
    result = dict(variant=variant, location=location, states=list(states),
                  inputs=inputs['cases'], wrong_masks=inputs['wrong_masks'],
                  register_failures=inputs['register_failures'], controls=controls)
    if location == 'standard':
        result['movement'] = menu.overworld_inputs(output, repo, core, battery)
        result['returns'] = menu.menu_returns(output, repo, core, battery,
                                             [s for s in states if s != 'start-menu'])
        menu.bicycle_state(output, repo, core, battery)
        result['bicycle'] = menu.overworld_inputs(output, repo, core, battery, 'bike')
    driver = Driver(core, cfg['rom'], menu.BOOT, battery, output / 'visuals.log')
    try:
        visuals = {}
        for name in states:
            driver.command(f'load {output / (name + ".s0")}')
            initial = driver.command('perf 1')
            driver.events.clear()
            menu.run(driver, repo, frames=64)
            frames = [e for e in driver.events if e['event'] == 'perf_frame']
            snapshot = driver.command('m')
            expected = cfg.get('expected_battle_speed', cfg['expected_double_speed']) if location == 'battle' else cfg['expected_double_speed']
            if snapshot['double_speed'] != expected:
                raise RuntimeError(f'Wrong speed in {name}')
            driver.command(f'image {output / (name + "-qualified.ppm")}')
            visuals[name] = dict(initial=initial, frames=frames, state=snapshot)
        (output / 'visuals.json').write_text(json.dumps(visuals, indent=2) + '\n')
    finally:
        driver.close()
    (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    return dict(variant=variant, location=location, inputs=result['inputs'],
                wrong_masks=result['wrong_masks'], register_failures=result['register_failures'])


def audio_job(item):
    variant, quarter, visits = item
    cfg = configuration(variant)
    output = BASE / 'audio' / f'{variant}-q{quarter}-v{visits}'
    prepared = audio.prepare(cfg, output, visits, quarter)
    prepared['variant'] = variant
    prepared['expected_double_speed'] = cfg['expected_double_speed']
    (output / 'config.json').write_text(json.dumps(prepared, indent=2) + '\n')
    return prepared


def audio_suite(variants, workers, smoke):
    setups = [(v, q, visits) for v in variants for q in ((0,) if smoke else (0, 17556, 35112, 52668))
              for visits in ((0,) if v == 'production' else (0, 1))]
    with ProcessPoolExecutor(max_workers=8) as pool:
        configurations = list(pool.map(audio_job, setups))
    tasks = []
    for cfg in configurations:
        output = Path(cfg['output'])
        repo = Repository(ROOT, Path(cfg['rom']), Path(cfg['sym']))
        factory = audio.factory(repo, output)
        order_at = repo.symbols['NewPokedexOrder']
        from .assets import offset
        for name in (('dusknoir', 'caterpie') if smoke else audio.SPECIES):
            n = performance.names().index(name)
            index = int.from_bytes(repo.rom[offset(order_at) + n * 2:offset(order_at) + n * 2 + 2], 'little')
            for context in ('player', 'blocking', 'stereo'):
                donor = cfg['states']['caterpie']['encounter'] if context == 'player' else str(output / 'party.s0')
                state = output / f'{name}-{context}.s0'
                subprocess.run([str(factory), cfg['rom'], donor, str(index), context, str(state)],
                               capture_output=True, check=True)
                cfg['states'][name][context] = str(state)
            tasks.extend((cfg, name, context) for context in ('stats', 'catch', 'faint', 'player', 'blocking', 'stereo'))
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, row in enumerate(pool.map(audio.execute, tasks)):
            row['variant'] = tasks[i][0]['variant']
            row['visits'] = tasks[i][0]['visits']
            results.append(row)
            if (i + 1) % 40 == 0 or row['issues']:
                print(json.dumps(dict(done=i+1, total=len(tasks), species=row['species'], context=row['context'], issues=row['issues'])), flush=True)
    output = BASE / 'audio'
    report_name = 'report.json' if variants == ['production', 'full'] else 'report-' + '-'.join(variants) + '.json'
    (output / report_name).write_text(json.dumps(dict(configurations=configurations, results=results,
                                                      cases=len(results)), indent=2) + '\n')
    return results


def compile_factory(repo, output):
    labels = '''wBattleMode wBattleMonMoves wEnemyMonMoves wPartyMon1Moves wMoveIndexTableEntries
    wBattleMonPP wEnemyMonPP wPartyMon1PP wBattleMonLevel wEnemyMonLevel wPartyMon1Level
    wBattleMonStatus wEnemyMonStatus wPartyMon1Status wBattleMonHP wEnemyMonHP wPartyMon1HP
    wBattleMonMaxHP wEnemyMonMaxHP wPartyMon1MaxHP wBattleMonStats wEnemyMonStats
    wPlayerSubStatus1 wEnemySubStatus1 wPlayerStatLevels wEnemyStatLevels wBattleMonType
    wEnemyMonType wBattleWeather wPlayerStats wEnemyStats wPartyMon1Stats'''.split()
    lines = []
    for name in labels:
        bank, pc = repo.symbols[name]
        lines += [f'#define B_{name} {bank}', f'#define S_{name} {pc}']
    lines.append(f'#define P_ALLOCATE {repo.symbols["GetMoveIDFromIndex"][1]}')
    header = output / 'battle-fixture-symbols.h'
    header.write_text('\n'.join(lines) + '\n')
    sameboy = Path.home() / 'Documents/GitHub/SameBoy'
    binary = output / 'battle-fixture'
    subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="global-fixture"',
                    f'-DGLOBAL_BATTLE_SYMBOLS="{header}"',
                    str(ROOT / 'tools/dex_timing/probes/global_battle_fixture.c'),
                    *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(binary)], check=True)
    return binary


def move_job(item):
    cfg, move, index, side, quarter = item
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = Path(cfg.get('output_root', BASE / 'moves')) / cfg['variant'] / f'{move.lower()}-{side}-q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    driver = Driver(cfg['core'], cfg['rom'], menu.BOOT, cfg['battery'], output / 'run.log')
    result = dict(variant=cfg['variant'], move=move, index=index, side=side, quarter=quarter, issues=[])
    try:
        driver.command(f'load {cfg["fixtures"][move][side]}')
        menu.run(driver, repo, frames=quarter / FRAME)
        driver.command('audit 1')
        driver.command('perf 1')
        capture = cfg.get('capture_images', False) and quarter == 0 and move in cfg.get('capture_moves', ())
        if capture:
            result['capture_start_t'] = driver.command('m')['t']
            driver.command(f'perfimages {output / "frame"}')
            driver.command(f'perfaudio {output / "audio.raw"}')
        driver.events.clear()
        # Normal battle selection; the other combatant knows only Splash.
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        found = False
        for turn in range(8):
            if move in ('SELFDESTRUCT', 'EXPLOSION', 'WILD_CHARGE', 'VOLT_TACKLE', 'PETAL_DANCE', 'OUTRAGE', 'ROLLOUT'):
                # These moves intentionally leave the turn menu (faint/switch
                # or battle victory); completion is the actual anim return.
                required = 3 if move in ('PETAL_DANCE', 'OUTRAGE') else 1
                for step in range(800):
                    menu.run(driver, repo, frames=8, keys=KEY['a'] if step % 2 == 0 else 0)
                    starts = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'battle_anim'
                              and e['anim_id'] == index and e['turn'] == (side == 'foe')]
                    returned = {e['t'] for e in driver.events if e['event'] == 'perf_cost' and e['name'] == 'battle_anim'}
                    if sum(e['t'] in returned for e in starts) >= required:
                        menu.run(driver, repo, frames=60)
                        break
            else:
                audio.until(driver, repo, 'BattleMenu.loop', attempts=200)
            animations = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'battle_anim'
                          and e['anim_id'] == index and e['turn'] == (side == 'foe')]
            if animations:
                found = True
                if move in ('PETAL_DANCE', 'OUTRAGE') or move not in ('WISH', 'FLY', 'DIG', 'SOLARBEAM') or turn >= 2:
                    break
            audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        if not found:
            result['issues'].append('requested move animation was not executed by the requested side')
        if cfg.get('post_menu_frames', 0):
            menu.run(driver, repo, frames=cfg['post_menu_frames'])
        phases = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'battle_anim']
        costs = [e for e in driver.events if e['event'] == 'perf_cost' and e['name'] == 'battle_anim']
        result['animations'] = [dict(start=p, elapsed_t=next((c['elapsed'] for c in costs if c['t'] == p['t']), None)) for p in phases]
        result['requested_animations'] = [a for a in result['animations'] if a['start']['anim_id'] == index and a['start']['turn'] == (side == 'foe')]
        result['frames'] = [e for e in driver.events if e['event'] == 'perf_frame']
        result['final'] = driver.command('m')
        if result['final']['double_speed'] != cfg['expected_double_speed']:
            result['issues'].append('CPU speed changed during battle')
        result['misses'] = [e for e in driver.events if e['event'] in ('animation_miss', 'audio_miss')]
        if result['misses']:
            result['issues'].append('playback miss during move execution')
        driver.command(f'image {output / "final.ppm"}')
    except Exception as error:
        result['issues'].append(str(error))
    finally:
        if cfg.get('capture_images', False) and quarter == 0 and move in cfg.get('capture_moves', ()):
            driver.command('perfaudio -')
            driver.command('perfimages -')
        save_events(output / 'events.jsonl.gz', driver.events)
        driver.close()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return {k: v for k, v in result.items() if k != 'frames'}


def moves_suite(variants, workers, smoke, selected=None):
    constants = re.findall(r'^\s*const\s+(\w+)', (ROOT / 'constants/move_constants.asm').read_text().split('DEF NUM_ATTACKS')[0], re.M)
    moves = selected or (['THUNDERSHOCK', 'WISH', 'POISON_GAS', 'CAUSTIC'] if smoke else REQUESTED + ADDED_NEW + ADDED_OLD)
    tasks = []
    for variant in variants:
        cfg = configuration(variant)
        cfg['variant'] = variant
        output = BASE / 'moves' / variant
        output.mkdir(parents=True, exist_ok=True)
        repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
        cfg['core'] = str(compile_core(repo, output))
        cfg['battery'] = str(BASE / 'menus' / variant / 'battle/private.sav')
        donor = BASE / 'menus' / variant / 'battle/battle-main.s0'
        factory = compile_factory(repo, output)
        fixtures = {}
        for move in moves:
            fixtures[move] = {}
            index = constants.index(move)
            for side in ('player', 'foe'):
                state = output / f'{move.lower()}-{side}.s0'
                subprocess.run([str(factory), cfg['rom'], str(donor), str(index), side, str(state)],
                               capture_output=True, check=True)
                fixtures[move][side] = str(state)
        cfg['fixtures'] = fixtures
        for move in moves:
            for side in ('player', 'foe'):
                for quarter in ((0,) if smoke else (0, 17556, 35112, 52668)):
                    tasks.append((cfg, move, constants.index(move), side, quarter))
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for row in pool.map(move_job, tasks):
            results.append(row)
            if len(results) % 32 == 0 or row['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), variant=row['variant'], move=row['move'], side=row['side'], issues=row['issues'])), flush=True)
    report = ('report-' + '-'.join(variants) + '.json') if not selected else ('retests-' + '-'.join(variants) + '.json')
    (BASE / 'moves' / report).write_text(json.dumps(dict(moves=moves, cases=len(results), results=results), indent=2) + '\n')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('menus', 'audio', 'moves'), required=True)
    parser.add_argument('--variants', nargs='+', default=['production', 'full'])
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--moves', nargs='+')
    parser.add_argument('--locations', nargs='+', default=['standard', 'battle', 'mart', 'puzzle', 'game-corner'])
    args = parser.parse_args()
    if args.suite == 'menus':
        with ProcessPoolExecutor(max_workers=10) as pool:
            for result in pool.map(menu_job, [(v, p) for v in args.variants for p in args.locations]):
                print(json.dumps(result), flush=True)
    elif args.suite == 'audio':
        audio_suite(args.variants, args.jobs, args.smoke)
    else:
        moves_suite(args.variants, args.jobs, args.smoke, args.moves)


if __name__ == '__main__':
    main()
