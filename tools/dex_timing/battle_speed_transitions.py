"""Continuous native battle entries/returns, with read-only clock safety traces."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from .battle_normal_speed import BASE, cfg, PHASES
from . import global_speed as speed, global_gameplay as gameplay
from . import performance, performance_audio as audio, shared_menu_regression as menu
from .assets import Repository
from .cold_listing import Driver, FRAME, KEY, ROOT
from .shared_menu_fixtures import make_fixture
from . import global_review_save as review


def compiler(repo, output):
    points = dict(speed.EXTRA, switch=('SwitchSpeed', True),
                  enter_speed=('BattleSpeed_EnterNormal', True),
                  leave_speed=('BattleSpeed_LeaveNormal', True),
                  map_disable=('BattleSpeed_MapDisableLCD', True),
                  battle_owner=('StartBattle', True), battle_cleanup=('CleanUpBattleRAM', True))
    performance.core(repo, output, points)
    header = output / 'performance-symbols.h'
    with header.open('a') as stream:
        stream.write(f'#define S_wBattleMode {repo.symbols["wBattleMode"][1]}\n')
    return menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_SPEED_TRACE',
         f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"'))


def encounter(driver, repo):
    for n in range(400):
        state = menu.run(driver, repo, 'LoadEnemyMon', 12, KEY['up' if (n // 20) % 2 == 0 else 'down'])
        if audio.at(state, repo, 'LoadEnemyMon'):
            return
    raise RuntimeError('Native grass encounter did not begin')


def world(driver, repo):
    for _ in range(160):
        menu.tap(driver, repo, 'a', held=4, released=20)
        state = driver.command('m')
        if state['wBattleMode'] == 0 and state['wScriptRunning'] == 0 and state['double_speed'] == 1:
            menu.run(driver, repo, frames=64)
            return driver.command('m')
    raise RuntimeError('Did not restore the double-speed overworld')


def nested(driver, repo, round_):
    if round_ % 4 == 0:
        menu.tap(driver, repo, 'right')
        audio.until(driver, repo, 'PartyMenuSelect')
        # Battle's Switch/Stats/Cancel menu is not the overworld MonMenuLoop.
        audio.until(driver, repo, 'BattleMonMenu')
        menu.run(driver, repo, frames=40)
        menu.tap(driver, repo, 'down', released=12)
        audio.until(driver, repo, 'Battle_StatsScreen')
        audio.until(driver, repo, 'StatsScreenMain.loop', key=None)
        menu.run(driver, repo, frames=240)
        if driver.command('m')['double_speed'] != 0:
            raise RuntimeError('Battle Stats left normal speed')
        audio.until(driver, repo, 'PartyMenuSelect', key='b')
        audio.until(driver, repo, 'BattleMenu.loop', key='b')
    elif round_ % 4 == 1:
        menu.tap(driver, repo, 'down')
        audio.until(driver, repo, 'BattlePack.loop')
        for _ in range(6):
            menu.tap(driver, repo, 'right', released=32)
            if driver.command('m')['double_speed'] != 0:
                raise RuntimeError('Battle Pack left normal speed')
        audio.until(driver, repo, 'BattleMenu.loop', key='b')


def repeat(quarter, count):
    local = cfg()
    repo = Repository(Path(local['root']), Path(local['rom']), Path(local['sym']))
    output = BASE / 'transitions' / f'repeat-q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    binary = compiler(repo, output)
    battery = output / 'private.sav'
    lead_save = output / 'sample-lead.sav'
    party = (review.PARTY[2], *review.PARTY[:2], *review.PARTY[3:])
    review.create(repo, speed.BATTERY, lead_save, party)
    make_fixture(repo, lead_save, battery, ('ROUTE_30', 13, 49))
    driver = Driver(binary, local['rom'], menu.BOOT, battery, output / 'run.log')
    row = dict(quarter=quarter, rounds=[], issues=[])
    try:
        menu.boot_overworld(driver, repo)
        menu.settle_map_input(driver, repo)
        menu.run(driver, repo, frames=quarter/FRAME)
        driver.command('perf 1')
        driver.command('audit 1')
        driver.events.clear()
        for n in range(count):
            if quarter == 0 and n == 0:
                driver.command(f'perfimages {output / "frame"}')
                driver.command(f'perfaudio {output / "audio.raw"}')
            encounter(driver, repo)
            audio.until(driver, repo, 'BattleMenu.loop')
            menu.run(driver, repo, frames=240)
            battle = driver.command('m')
            if battle['double_speed'] != 0:
                raise RuntimeError('Battle did not enter normal speed')
            nested(driver, repo, n)
            # Select Run based on the native 2x2 cursor, not an assumed origin.
            menu.run(driver, repo, frames=40)
            cursor = audio.value(driver, repo, 'wBattleMenuCursorPosition')
            if cursor <= 2:
                menu.tap(driver, repo, 'down')
            cursor = audio.value(driver, repo, 'wBattleMenuCursorPosition')
            if cursor % 2 == 1:
                menu.tap(driver, repo, 'right')
            audio.until(driver, repo, 'BattleMenu_Run')
            returned = world(driver, repo)
            row['rounds'].append(dict(battle=battle, returned=returned))
            if quarter == 0 and n == 0:
                driver.command('perfimages -')
                driver.command('perfaudio -')
            # Exercise independent menu ownership after every true clock return.
            audio.until(driver, repo, 'StartMenu.loop', key='start')
            menu.run(driver, repo, frames=12)
            if n % 4 == 0:
                for _ in range(10):
                    if driver.command('m')['wMenuCursorY'] == 2:
                        break
                    menu.tap(driver, repo, 'down')
                audio.until(driver, repo, 'PartyMenuSelect')
                audio.until(driver, repo, 'MonMenuLoop')
                audio.until(driver, repo, 'StatsScreenMain.loop')
                menu.run(driver, repo, frames=240)
                if driver.command('m')['double_speed'] != 1:
                    raise RuntimeError('Post-battle Stats did not retain double speed')
                audio.until(driver, repo, 'PartyMenuSelect', key='b')
                audio.until(driver, repo, 'StartMenu.loop', key='b')
            menu.run(driver, repo, frames=8)
            menu.tap(driver, repo, 'b', released=80)
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        row['changes'] = [e for e in driver.events if e['event'] == 'speed_change']
        row['switches'] = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'switch']
        row['misses'] = [e for e in driver.events if e['event'] in ('audio_miss', 'animation_miss')]
        speed.save_events(output / 'events.jsonl.gz', driver.events)
        driver.close()
    actual = [e for e in row['changes'] if not e['initial']]
    if len(actual) != 2 * count:
        row['issues'].append(f'Expected {2*count} actual switches; saw {len(actual)}')
    if any(e['lcdc'] & 128 or e['nr52'] & 128 or e['sampled_active'] for e in actual):
        row['issues'].append('Unsafe LCD/APU/sampled ownership at speed switch')
    if 'odd mode' in (output / 'run.log').read_text():
        row['issues'].append('SameBoy odd-mode warning')
    (output / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def loss(quarter):
    local = cfg()
    repo = Repository(Path(local['root']), Path(local['rom']), Path(local['sym']))
    output = BASE / 'transitions' / f'loss-q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    binary = compiler(repo, output)
    source = speed.BASE / 'menus/battle-normal/battle'
    driver = Driver(binary, local['rom'], menu.BOOT, source / 'private.sav', output / 'run.log')
    row = dict(quarter=quarter, kind='whiteout', issues=[])
    try:
        factory = speed.compile_factory(repo, output)
        state = output / 'hyper-beam.s0'
        subprocess.run([str(factory), local['rom'], str(source / 'battle-main.s0'), '63', 'foe', str(state), 'coherent'], check=True, capture_output=True)
        driver.command(f'load {state}')
        labels = 'wBattleMonHP wBattleMonStatus'.split()
        # Build the same declared-data factory with two additional fixture fields.
        scenario = gameplay.scenario_factory(repo, output)
        header = output / 'scenario-symbols.h'
        with header.open('a') as stream:
            for label in labels:
                bank, address = repo.symbols[label]
                stream.write(f'#define B_{label} {bank}\n#define S_{label} {address}\n')
        sameboy = Path.home() / 'Documents/GitHub/SameBoy'
        from .new_entry import CORE_FILES
        subprocess.run(['clang','-O2','-std=c11','-I'+str(sameboy),'-DGB_INTERNAL',
            '-DGB_DISABLE_DEBUGGER','-DGB_DISABLE_REWIND','-DGB_DISABLE_CHEATS',
            '-DGB_DISABLE_CHEAT_SEARCH','-DGB_DISABLE_TIMEKEEPING','-DGB_VERSION="battle-loss-fixture"',
            f'-DGLOBAL_GAMEPLAY_SYMBOLS="{header}"',str(ROOT/'tools/dex_timing/probes/global_gameplay_fixture.c'),
            *(str(sameboy/'Core'/(f+'.c')) for f in CORE_FILES),'-o',str(scenario)],check=True)
        loss_state = output / 'loss.s0'
        subprocess.run([str(scenario), local['rom'], str(state), 'loss', str(loss_state)], check=True, capture_output=True)
        driver.command(f'load {loss_state}')
        menu.run(driver, repo, frames=quarter/FRAME)
        driver.command('perf 1')
        driver.command('audit 1')
        driver.events.clear()
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        row['returned'] = world(driver, repo)
        row['battle_result'] = audio.value(driver, repo, 'wBattleResult')
        if row['battle_result'] & 15 != 1:
            row['issues'].append('Native defeat not observed')
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        row['changes'] = [e for e in driver.events if e['event'] == 'speed_change']
        speed.save_events(output / 'events.jsonl.gz', driver.events)
        driver.close()
    (output / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def level(quarter):
    local = cfg()
    repo = Repository(Path(local['root']), Path(local['rom']), Path(local['sym']))
    output = BASE / 'transitions' / f'level-q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    binary = compiler(repo, output)
    source = output / 'level-party.sav'
    # A learn-move prompt can replace the first move. Do not fill that slot
    # with an undeletable HM or an A-only driver will correctly remain there.
    party = (('CATERPIE', 'EVOLVE', ('BODY_SLAM', 'THUNDERBOLT', 'WATER_PULSE', 'POISON_GAS')), *review.PARTY[1:])
    review.create(repo, speed.BATTERY, source, party, level=6)
    battery = output / 'private.sav'
    make_fixture(repo, source, battery, ('ROUTE_30', 13, 49))
    driver = Driver(binary, local['rom'], menu.BOOT, battery, output / 'run.log')
    row = dict(quarter=quarter, kind='postbattle-evolution', issues=[])
    try:
        menu.boot_overworld(driver, repo)
        menu.settle_map_input(driver, repo)
        gameplay.generated(driver, repo, output, 'postbattle-level')
        menu.run(driver, repo, frames=quarter/FRAME)
        driver.command('perf 1')
        driver.command('audit 1')
        driver.events.clear()
        encounter(driver, repo)
        audio.until(driver, repo, 'BattleMenu.loop')
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        audio.until(driver, repo, 'EvolutionAnimation')
        row['evolution'] = driver.command('m')
        if row['evolution']['double_speed'] != 0:
            row['issues'].append('Post-battle evolution left normal speed')
        row['returned'] = world(driver, repo)
        row['level'] = audio.value(driver, repo, 'wPartyMon1Level')
        id_ = audio.value(driver, repo, 'wPartyMon1Species')
        bank, address = repo.symbols['wPokemonIndexTableEntries']
        row['species_index'] = int.from_bytes(bytes.fromhex(driver.command(
            f'perfram {bank} {address + 2*(id_-1)} 2')['bytes']), 'little')
        if row['level'] != 7 or row['species_index'] != 11:
            row['issues'].append('Native level-up/evolution did not complete')
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        row['changes'] = [e for e in driver.events if e['event'] == 'speed_change']
        row['misses'] = [e for e in driver.events if e['event'] in ('audio_miss', 'animation_miss')]
        speed.save_events(output / 'events.jsonl.gz', driver.events)
        driver.close()
    (output / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def job(task):
    return repeat(task[1], task[2]) if task[0] == 'repeat' else (
        level(task[1]) if task[0] == 'level' else loss(task[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds', type=int, default=16)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--loss-only', action='store_true')
    parser.add_argument('--level-only', action='store_true')
    args = parser.parse_args()
    tasks = [('level', q, 0) for q in PHASES] if args.level_only else (
        ([] if args.loss_only else [('repeat', q, args.rounds) for q in PHASES]) +
        [('loss', q, 0) for q in PHASES] + ([] if args.loss_only else [('level', q, 0) for q in PHASES]))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(job, tasks))
    report = BASE / 'transitions' / ('level-report.json' if args.level_only else 'report.json')
    report.write_text(json.dumps(rows, indent=2) + '\n')
    if args.level_only and (BASE / 'transitions/report.json').exists():
        full = BASE / 'transitions/report.json'
        prior = json.loads(full.read_text())
        changes = {(r.get('kind', 'repeat'), r['quarter']): r for r in rows}
        prior = [changes.get((r.get('kind', 'repeat'), r['quarter']), r) for r in prior]
        full.write_text(json.dumps(prior, indent=2) + '\n')
    print(json.dumps([dict(quarter=r['quarter'], kind=r.get('kind', 'repeat'),
        rounds=len(r.get('rounds', [])), changes=len(r['changes']), issues=r['issues']) for r in rows]))


if __name__ == '__main__':
    main()
