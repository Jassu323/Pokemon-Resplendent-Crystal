"""Native gameplay scenarios for the private global-speed qualification."""
import argparse
from collections import deque
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import subprocess

from .assets import Repository, offset
from .cold_listing import Driver, KEY, FRAME, ROOT
from .global_speed import BASE, configuration, compile_core, save_events
from . import shared_menu_regression as menu, performance_audio as audio
from .new_entry import CORE_FILES
from .shared_menu_fixtures import make_fixture


def event_constants():
    values, number = {}, 0
    for line in (ROOT / 'constants/event_flags.asm').read_text().splitlines():
        line = line.split(';')[0].strip()
        if line.startswith(('const_next ', 'const_def ')):
            number = int(line.split()[1].replace('$', '0x'), 0)
        elif line.startswith('const_skip'):
            number += int(line.split()[1], 0) if len(line.split()) > 1 else 1
        elif line.startswith('const '):
            values[line.split()[1]] = number
            number += 1
    return values


def saved(repo, source, name, size):
    bank, address = repo.symbols[name]
    for block in ('PlayerData', 'CurMapData', 'PokemonData'):
        b, start = repo.symbols['w' + block]
        if b == bank and start <= address < repo.symbols['w' + block + 'End'][1]:
            sb, sa = repo.symbols['s' + block]
            at = sb * 8192 + sa - 0xa000 + address - start
            return source.read_bytes()[at:at + size]
    raise ValueError(name)


def new_driver(variant, scenario, location, extra=None):
    cfg = configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = BASE / 'gameplay' / variant / scenario
    output.mkdir(parents=True, exist_ok=True)
    core = compile_core(repo, output)
    battery = output / 'private.sav'
    make_fixture(repo, Path(cfg['battery']), battery, location, extra_fields=extra)
    driver = Driver(core, cfg['rom'], menu.BOOT, battery, output / 'run.log')
    return cfg, repo, output, driver


def checked(row, condition, reason):
    if not condition:
        row['issues'].append(reason)


def scenario_factory(repo, output):
    labels = '''wReceiveCallDelay_MinsRemaining wTimeCyclesSinceLastCall wPhoneList
        wPartyMon1Level wPartyMon1Exp wPartyMon1Happiness wPartySpecies wPartyCount
        wPartyMon1Species wPartyMon1 wPartyMon2 wPartyMon1Nickname wPartyMon1OT
        wStepCount wRepelEffect'''.split()
    header = output / 'scenario-symbols.h'
    header.write_text('\n'.join(f'#define B_{n} {repo.symbols[n][0]}\n#define S_{n} {repo.symbols[n][1]}' for n in labels) + '\n')
    sameboy = Path.home() / 'Documents/GitHub/SameBoy'
    binary = output / 'scenario-factory'
    subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="scenario-fixture"',
        f'-DGLOBAL_GAMEPLAY_SYMBOLS="{header}"', str(ROOT / 'tools/dex_timing/probes/global_gameplay_fixture.c'),
        *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(binary)], check=True)
    return binary


def generated(driver, repo, output, kind):
    donor, state = output / 'scenario-donor.s0', output / 'scenario.s0'
    driver.command(f'save {donor}')
    subprocess.run([str(scenario_factory(repo, output)), str(repo.rom_path),
                    str(donor), kind, str(state)], check=True, capture_output=True)
    driver.command(f'load {state}')


def phone(driver, repo, row, output):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    driver.command('perf 1')
    driver.events.clear()
    for attempt in range(32):
        generated(driver, repo, output, 'phone')
        menu.run(driver, repo, frames=32)
        if any(e['event'] == 'perf_phase' and e['name'] == 'phone' for e in driver.events):
            break
    row['expired_timer_attempts'] = attempt + 1
    checked(row, any(e['event'] == 'perf_phase' and e['name'] == 'phone' for e in driver.events), 'random incoming phone call not dispatched')
    for _ in range(80):
        menu.tap(driver, repo, 'a', released=16)
        state = driver.command('m')
        if state['wScriptRunning'] == 0 and not state['hInMenu']:
            break
    checked(row, driver.command('m')['wScriptRunning'] == 0, 'phone script did not return')


def party_scenario(driver, repo, row, output, variant, kind):
    folder = Path(configuration(variant).get('audio_fixture_dir', BASE / 'audio' / f'{variant}-q0-v0'))
    driver.command(f'load {folder / "caterpie-party.s0"}')
    generated(driver, repo, output, 'egg' if kind == 'egg' else 'level')
    driver.command('perf 1')
    driver.events.clear()
    audio.until(driver, repo, 'StartMenu.loop', key='b')
    menu.tap(driver, repo, 'b', released=60)
    if kind == 'egg':
        driver.command('perf 1')
        driver.events.clear()
        hatched = False
        for step in range(400):
            menu.run(driver, repo, frames=16, keys=KEY['up'] if (step // 4) % 2 == 0 else KEY['down'])
            menu.tap(driver, repo, 'b', released=4)
            if audio.value(driver, repo, 'wPartySpecies') != 0xfd:
                hatched = True
                break
        checked(row, hatched, 'ready egg did not hatch through overworld steps')
        for _ in range(100):
            menu.tap(driver, repo, 'b', released=16)
            if not driver.command('m')['hInMenu'] and not driver.command('m')['wScriptRunning']:
                break
    else:
        audio.until(driver, repo, 'StartMenu.loop', key='start')
        menu.run(driver, repo, frames=4)
        driver.command(f'save {output / "start-menu.s0"}')
        menu.enter_start_item(driver, repo, output, 3, 'Pack.loop')
        for _ in range(12):
            if driver.command('m')['wCurPocket'] == 0:
                break
            menu.tap(driver, repo, 'right', released=40)
        audio.until(driver, repo, 'Pack_VerticalMenu')
        audio.until(driver, repo, 'PartyMenuSelect')
        menu.tap(driver, repo, 'a', released=300)
        for _ in range(80):
            menu.tap(driver, repo, 'a', released=30)
            species = audio.value(driver, repo, 'wPartyMon1Species')
            bank, address = repo.symbols['wPokemonIndexTableEntries']
            current_index = int.from_bytes(bytes.fromhex(driver.command(
                f'perfram {bank} {address + (species - 1)*2} 2')['bytes']), 'little')
            if current_index == 11:
                break
        checked(row, audio.value(driver, repo, 'wPartyMon1Level') == 7, 'Rare Candy did not level up')
        species = audio.value(driver, repo, 'wPartyMon1Species')
        index = audio.value(driver, repo, 'wPokemonIndexTableEntries' , 1024).to_bytes(1024, 'little')
        row['evolved_index'] = int.from_bytes(index[(species - 1)*2:species*2], 'little')
        checked(row, row['evolved_index'] == 11, 'Caterpie did not evolve to Metapod')
    row['final'] = driver.command('m')


def navigation(driver, repo, row):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    before = driver.command('m')
    menu.walk_to(driver, repo, 'x', 23)
    menu.walk_to(driver, repo, 'y', 4)
    initial = driver.command('perf 1')
    driver.events.clear()
    menu.walk_through_door(driver, repo, 'up', 4)
    entered = driver.command('m')
    menu.walk_to(driver, repo, 'x', 3)
    menu.walk_to(driver, repo, 'y', 5)
    menu.walk_through_door(driver, repo, 'down', 3)
    left = driver.command('m')
    checked(row, entered['wMapNumber'] == 4 and left['wMapNumber'] == 3, 'building warp roundtrip')
    menu.walk_to(driver, repo, 'x', 17)
    for _ in range(240):
        state = menu.run(driver, repo, frames=1, keys=KEY['up'])
        if (state['wMapGroup'], state['wMapNumber']) != (left['wMapGroup'], left['wMapNumber']):
            break
    checked(row, (state['wMapGroup'], state['wMapNumber']) != (left['wMapGroup'], left['wMapNumber']), 'connected-map crossing')
    row.update(before=before, entered=entered, left=left, connected=state, initial=initial)


def purchase(driver, repo, row, variant):
    folder = BASE / 'menus' / variant / 'mart'
    driver.command(f'load {folder / "mart-buy.s0"}')
    before_money = audio.value(driver, repo, 'wMoney', 3)
    before_items = audio.value(driver, repo, 'wNumItems')
    audio.until(driver, repo, 'StandardMartAskPurchaseQuantity')
    # Default quantity one; confirmation is handled by the native yes/no menu.
    audio.until(driver, repo, 'BuyMenuLoop')
    after_money = audio.value(driver, repo, 'wMoney', 3)
    checked(row, before_money != after_money, 'purchase did not change money')
    for _ in range(20):
        menu.tap(driver, repo, 'b', released=40)
        state = driver.command('m')
        if not state['hInMenu'] and state['wScriptRunning'] == 0:
            break
    menu.run(driver, repo, 'StartMenu.loop', 180, KEY['start'])
    menu.run(driver, repo, frames=40)
    driver.command(f'save {folder / "start-menu.s0"}')
    menu.enter_start_item(driver, repo, folder, 3, 'Pack.loop')
    menu.run(driver, repo, frames=60)
    row.update(before_money=before_money, after_money=after_money, before_items=before_items,
               after_items=audio.value(driver, repo, 'wNumItems'), pack=driver.command('m'))
    driver.command(f'image {folder / "after-purchase.ppm"}')


def puzzle_path(start, target):
    todo, seen = deque([(start, [])]), {start}
    while todo:
        n, path = todo.popleft()
        if n == target:
            return path
        choices = {'up': n - 6 if n >= 6 else n,
                   'down': n + 6 if n < 30 and n not in (25, 26, 27, 28) else n,
                   'left': (30 if n == 35 else n - 1) if n % 6 else n,
                   'right': (35 if n == 30 else n + 1) if n % 6 != 5 else n}
        for key, destination in choices.items():
            if destination not in seen:
                seen.add(destination)
                todo.append((destination, path + [key]))
    raise RuntimeError('Puzzle cursor route unreachable')


def solve_puzzle(driver, repo, row, variant):
    folder = BASE / 'menus' / variant / 'puzzle'
    driver.command(f'load {folder / "unown-puzzle.s0"}')
    menu.run(driver, repo, frames=4)
    initial = list(audio.value(driver, repo, 'wPuzzlePieces', 36).to_bytes(36, 'little'))
    checked(row, sorted(v for v in initial if v) == list(range(1, 17)), 'initial puzzle does not contain each piece once')
    for piece in range(1, 17):
        pieces = list(audio.value(driver, repo, 'wPuzzlePieces', 36).to_bytes(36, 'little'))
        start = pieces.index(piece)
        target = (1 + (piece - 1) // 4) * 6 + 1 + (piece - 1) % 4
        for destination in (start, target):
            cursor = driver.command('m')['wUnownPuzzleCursorPosition']
            for key in puzzle_path(cursor, destination):
                menu.tap(driver, repo, key, held=4, released=24)
            checked(row, driver.command('m')['wUnownPuzzleCursorPosition'] == destination, 'puzzle cursor movement mismatch')
            if piece == 16 and destination == target:
                audio.until(driver, repo, 'SimpleWaitPressAorB')
                menu.tap(driver, repo, 'a', released=180)
            else:
                menu.tap(driver, repo, 'a', held=4, released=100)
    row.update(initial_pieces=initial, solved=audio.value(driver, repo, 'wSolvedUnownPuzzle'), final=driver.command('m'))
    checked(row, row['solved'] == 1, 'puzzle completion flag not set')


def fishing(driver, repo, row):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    menu.tap(driver, repo, 'left', held=3, released=14)
    menu.run(driver, repo, 'StartMenu.loop', 180, KEY['start'])
    menu.run(driver, repo, frames=8)
    for _ in range(12):
        if driver.command('m')['wMenuCursorY'] == 3:
            break
        menu.tap(driver, repo, 'down')
    audio.until(driver, repo, 'Pack.loop')
    for _ in range(6):
        if driver.command('m')['wCurPocket'] == 2:
            break
        menu.tap(driver, repo, 'right', released=30)
    menu.tap(driver, repo, 'down', released=40)
    checked(row, driver.command('m')['wKeyItemsPocketCursor'] == 5, 'Old Rod selection')
    driver.command('perf 1')
    driver.events.clear()
    audio.until(driver, repo, 'Pack_VerticalMenu')
    menu.tap(driver, repo, 'a', released=160)
    for _ in range(20):
        menu.tap(driver, repo, 'a', released=20)
        if any(e['event'] == 'perf_phase' and e['name'] == 'fish' for e in driver.events):
            break
    checked(row, any(e['event'] == 'perf_phase' and e['name'] == 'fish' for e in driver.events), 'native fishing dispatch not reached')
    row['result'] = audio.value(driver, repo, 'wFishingResult')
    row['final'] = driver.command('m')


def trainer(driver, repo, row):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    menu.walk_through_door(driver, repo, 'down', 1)
    state = driver.command('m')
    blocks_at = offset(repo.symbols['Route30_Blocks'])
    coll_at = offset(repo.symbols['TilesetJohtoColl'])
    collision = lambda x, y: repo.rom[coll_at + repo.rom[blocks_at + y//2*10 + x//2]*4 + y%2*2 + x%2]
    start, target = (state['wXCoord'], state['wYCoord']), (2, 29)
    todo, seen, route = deque([(start, [])]), {start}, None
    while todo:
        (x, y), path = todo.popleft()
        if (x, y) == target:
            route = path
            break
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            cell = x + dx, y + dy
            if (cell not in seen and 0 <= cell[0] < 20 and 0 <= cell[1] < 54
                    and cell not in ((5, 39), (2, 28)) and collision(*cell) in (0, 0x10, 0x14, 0x18)):
                seen.add(cell)
                todo.append((cell, path + [cell]))
    if route is None:
        raise RuntimeError('No land-only route to Joey')
    row['walking_route'] = route
    for x, y in route:
        current = driver.command('m')
        menu.walk_to(driver, repo, 'x' if current['wXCoord'] != x else 'y', x if current['wXCoord'] != x else y)
    menu.tap(driver, repo, 'up', held=3, released=14)
    driver.command('audit 1')
    driver.command('perf 1')
    driver.events.clear()
    audio.until(driver, repo, 'BattleMenu.loop', attempts=220)
    checked(row, audio.value(driver, repo, 'wBattleMode') == 2, 'trainer battle did not start')
    audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
    # Original level-32 Meganium outclasses Joey's unmodified level-4 Rattata.
    for turn in range(8):
        menu.tap(driver, repo, 'a', released=240)
        if audio.value(driver, repo, 'wBattleMode') == 0:
            break
        if audio.value(driver, repo, 'wBattleEnded'):
            break
    for _ in range(20):
        menu.tap(driver, repo, 'a', released=20)
        if audio.value(driver, repo, 'wBattleMode') == 0:
            break
    checked(row, audio.value(driver, repo, 'wBattleMode') == 0, 'trainer battle did not finish')
    # Clearing the battle flag precedes the hidden map reload/speed handoff.
    menu.run(driver, repo, frames=240)
    row['final'] = driver.command('m')


def pc_catch(driver, repo, row, output, variant):
    source = Path(configuration(variant).get('audio_fixture_dir', BASE / 'audio' / f'{variant}-q0-v0'))
    driver.command(f'load {source / "dusknoir-encounter.s0"}')
    generated(driver, repo, output, 'full-party')
    driver.command('perf 1')
    driver.command('audit 1')
    driver.events.clear()
    audio.until(driver, repo, 'BattleMenu.loop')
    menu.run(driver, repo, frames=40)
    menu.tap(driver, repo, 'down')
    audio.until(driver, repo, 'BattlePack.loop')
    for _ in range(10):
        if audio.value(driver, repo, 'wCurPocket') == 1:
            break
        menu.tap(driver, repo, 'right', released=30)
    audio.until(driver, repo, 'NewPokedexEntry')
    audio.until(driver, repo, 'NewPokedexEntry.WaitPressAorB_AnimateFrontpic', key=None)
    menu.run(driver, repo, frames=240)
    audio.until(driver, repo, 'NewPokedexEntry.ReturnFromDexRegistration')
    audio.until(driver, repo, 'PokeBallEffect.SendToPC', key='b')
    row['sent_to_pc'] = True
    for _ in range(80):
        menu.tap(driver, repo, 'b', released=40)
        if not audio.value(driver, repo, 'wBattleMode'):
            break
    checked(row, audio.value(driver, repo, 'wBattleMode') == 0, 'full-party catch did not return')
    checked(row, audio.value(driver, repo, 'wPartyCount') == 6, 'full-party catch changed party count')
    menu.run(driver, repo, frames=240)
    row['final'] = driver.command('m')


def heal_save(driver, repo, row, output, cfg):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    menu.walk_to(driver, repo, 'x', 29)
    menu.walk_to(driver, repo, 'y', 4)
    menu.walk_through_door(driver, repo, 'up', 5)
    menu.walk_to(driver, repo, 'x', 3)
    menu.walk_to(driver, repo, 'y', 3)
    menu.tap(driver, repo, 'up', held=3, released=10)
    driver.command('perf 1')
    driver.events.clear()
    audio.until(driver, repo, 'HealParty')
    for _ in range(30):
        menu.tap(driver, repo, 'a', released=40)
        if not driver.command('m')['wScriptRunning']:
            break
    row['healed'] = audio.value(driver, repo, 'wPartyMon1HP', 2) == audio.value(driver, repo, 'wPartyMon1MaxHP', 2)
    checked(row, row['healed'], 'nurse did not restore HP')
    audio.until(driver, repo, 'StartMenu.loop', key='start')
    menu.run(driver, repo, frames=4)
    for _ in range(12):
        if driver.command('m')['wMenuCursorY'] == 6:
            break
        menu.tap(driver, repo, 'down')
    audio.until(driver, repo, 'SaveGameData')
    menu.run(driver, repo, frames=180)
    copy = output / 'saved-in-game.sav'
    driver.command(f'perfbattery {copy}')
    row['saved'] = True
    core = compile_core(repo, output / 'reboot')
    reboot = Driver(core, cfg['rom'], menu.BOOT, copy, output / 'reboot.log')
    try:
        row['reboot'] = menu.boot_overworld(reboot, repo)
        checked(row, row['reboot']['wMapNumber'] == 5 and row['reboot']['double_speed'] == cfg['expected_double_speed'], 'saved location or CPU policy changed on reboot')
        reset = menu.run(reboot, repo, 'Reset', 180, 0xf0)
        checked(row, menu.at(reset, repo, 'Reset'), 'native soft reset not dispatched')
        menu.run(reboot, repo, frames=40)
        row['soft_reset'] = menu.boot_overworld(reboot, repo)
        checked(row, row['soft_reset']['double_speed'] == cfg['expected_double_speed'], 'CPU policy changed after soft reset')
    finally:
        reboot.close()


def scenario(item):
    variant, kind = item
    cfg = configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    source = Path(cfg['battery'])
    extras = {}
    location = ('CHERRYGROVE_CITY', 20, 4)
    if kind == 'fishing':
        location = ('CHERRYGROVE_CITY', 10, 12)
        extras = {'wNumKeyItems': [5], 'wKeyItems': [0x64, 0x5a, 0x36, 7, 0x3a, 255]}
    elif kind == 'trainer':
        location = ('ROUTE_30_BERRY_HOUSE', 2, 6)
        size = repo.symbols['wCurBox'][1] - repo.symbols['wEventFlags'][1]
        flags = bytearray(saved(repo, source, 'wEventFlags', size))
        constants = event_constants()
        for name, enabled in (('EVENT_BEAT_YOUNGSTER_JOEY', False), ('EVENT_ROUTE_30_YOUNGSTER_JOEY', False), ('EVENT_ROUTE_30_BATTLE', True)):
            n = constants[name]
            flags[n // 8] = flags[n // 8] | 1 << (n % 8) if enabled else flags[n // 8] & ~(1 << (n % 8))
        extras['wEventFlags'] = flags
        extras['wRepelEffect'] = [200]
    elif kind == 'purchase':
        extras['wMoney'] = (50000).to_bytes(3, 'big')
    row = dict(variant=variant, scenario=kind, issues=[])
    driver = None
    try:
        cfg, repo, output, driver = new_driver(variant, kind, location, extras)
        if kind in ('navigation', 'purchase', 'puzzle'):
            {'navigation': navigation, 'purchase': purchase, 'puzzle': solve_puzzle}[kind](
                driver, repo, row, variant) if kind != 'navigation' else navigation(driver, repo, row)
        elif kind == 'pc-catch':
            pc_catch(driver, repo, row, output, variant)
        elif kind == 'heal-save':
            heal_save(driver, repo, row, output, cfg)
        elif kind in ('phone', 'level', 'egg'):
            if kind == 'phone':
                phone(driver, repo, row, output)
            else:
                party_scenario(driver, repo, row, output, variant, kind)
        else:
            {'fishing': fishing, 'trainer': trainer}[kind](driver, repo, row)
        final = driver.command('m')
        checked(row, final['double_speed'] == cfg['expected_double_speed'], 'CPU speed changed')
        row['playback_misses'] = [e for e in driver.events if e['event'] in ('audio_miss', 'animation_miss')]
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        if driver:
            save_events(output / 'events.jsonl.gz', driver.events)
            driver.command(f'image {output / "final.ppm"}')
            driver.close()
    output = BASE / 'gameplay' / variant / kind
    output.mkdir(parents=True, exist_ok=True)
    (output / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variants', nargs='+', default=['production', 'full'])
    parser.add_argument('--scenarios', nargs='+', default=['navigation', 'purchase', 'puzzle', 'fishing', 'trainer', 'phone', 'level', 'egg', 'pc-catch', 'heal-save'])
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=10) as pool:
        rows = list(pool.map(scenario, [(v, s) for v in args.variants for s in args.scenarios]))
    (BASE / 'gameplay/report.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps([{k: v for k, v in row.items() if k in ('variant', 'scenario', 'issues')} for row in rows]))


if __name__ == '__main__':
    main()
