"""Normal-key menu/overworld regressions plus linked caller-contract fixtures."""
import argparse
import json
from pathlib import Path
import re

from .assets import Repository
from .cold_listing import Driver, FRAME, KEY, ROOT, build_core
from .direction_changes import load_trace
from .direction_changes import ORDERS
from .cry_ownership import validate_output

BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
KEY = dict(KEY, select=64)
FIELDS = '''hJoypadDown hJoyPressed hJoyReleased hJoyDown hJoyLast hInMenu
    wTextDelayFrames wMenuCursorPosition wMenuCursorX wMenuCursorY wMenuJoypad
    wCurPocket wJumptableIndex wDexListingCursor wDexListingScrollOffset
    wPokedexSelectedIndex wDexArrowCursorPosIndex wPokegearCard
    wXCoord wYCoord wPlayerDirection wMapGroup wMapNumber wPlayerState
    wPartyCount wInputType wAutoInputLength wNamingScreenLetterCase
    wNamingScreenCurNameLength wBattleMode w2DMenuNumRows w2DMenuNumCols
    w2DMenuFlags1 w2DMenuFlags2 wMenuSelection wOptions wOptions2 wPartyMenuCursor
    wPokegearPhoneCursorPosition wPokegearPhoneScrollPosition wPokegearMapCursorLandmark
    wPokegearMapRegion wPokegearFlags wWalkingDirection wPlayerStepFlags
    wPlayerStepDirection wPlayerStepVectorX wPlayerStepVectorY
    wBillsPC_CursorPosition wBillsPC_ScrollPosition wBillsPC_LoadedBox'''.split()
FIELDS += '''wDexSearchMonType1 wDexSearchMonType2 wNamingScreenLastCharacter
    wNamingScreenType wNamingScreenDestinationPointer wMenuScrollPosition
    wMenuDataItems wMonSubmenuCount wMapEventStatus wItemsPocketCursor
    wKeyItemsPocketCursor wBallsPocketCursor wBerriesPocketCursor wMedicinePocketCursor
    wItemsPocketScrollPosition wKeyItemsPocketScrollPosition wBallsPocketScrollPosition
    wBerriesPocketScrollPosition wMedicinePocketScrollPosition wSwitchItem
    wItemQuantityChange wCurItemQuantity wBattleMenuCursorPosition
    wCardFlipCursorX wCardFlipCursorY wDexCurUnownIndex wUnownPuzzleCursorPosition
    wHoldingUnownPuzzlePiece wUnownPuzzleHeldPiece wSolvedUnownPuzzle
    wMapStatus wScriptRunning wPackJumptableIndex wPackUsedItem
    wTilePermissions wPlayerTileCollision wPlayerLastTile wMapWidth wMapHeight
    wMapTileset wPlayerMapX wPlayerMapY wPlayerLastMapX wPlayerLastMapY
    wPlayerMovementType wStateFlags wPlayerFacing'''.split()

MENUS = {
    'dex': (1, 'Pokedex_UpdateMainScreen'),
    'party': (2, 'PartyMenuSelect'),
    'pack': (3, 'Pack.loop'),
    'pokegear': (4, 'PokeGear.loop'),
    'trainer-card': (5, 'TrainerCard.loop'),
    'options': (7, '_Option.joypad_loop'),
}


def compile_observer(repo, source, output):
    output.mkdir(parents=True, exist_ok=True)
    header = (output / 'shared-menu-symbols.h').resolve()
    lines = [f'#define M_{name} 0x{repo.symbols[name][1]:04x}'
             for name in ('JoyTextDelay', 'hJoyPressed', 'hJoyDown', 'hJoyLast', 'hInMenu')]
    lines.append('static const struct { const char *name; unsigned bank,address,size; } shared_fields[] = {')
    for name in FIELDS:
        bank, address = repo.symbols[name]
        size = 2 if name in ('wDexListingScrollOffset', 'wPokedexSelectedIndex', 'wNamingScreenDestinationPointer') else 1
        lines.append(f'{{"{name}",{bank},0x{address:04x},{size}}},')
    lines.append('};')
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DSHARED_MENU_INPUT_TRACE', f'-DSHARED_MENU_INPUT_SYMBOLS="{header}"'))


def run(driver, repo, label=None, frames=1, keys=0):
    bank, pc = repo.symbols[label] if label else (0, 0xffff)
    return driver.command(f'mr {bank} {pc} {int(frames * FRAME)} {keys}')


def at(state, repo, label):
    bank, pc = repo.symbols[label]
    return state['pc'] == pc and (pc < 0x4000 or state['bank'] == bank)


def boot_overworld(driver, repo):
    for _ in range(180):
        state = run(driver, repo, 'HandleMapTimeAndJoypad', 20, KEY['a'])
        if at(state, repo, 'HandleMapTimeAndJoypad'):
            run(driver, repo, frames=12)
            return driver.command('m')
        run(driver, repo, frames=10)
    raise RuntimeError('Could not continue the copied battery')


def smoke(output, repo, core, battery):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'smoke.log')
    try:
        driver.command(f'mtrace {output / "smoke.jsonl"}')
        start = boot_overworld(driver, repo)
        driver.command(f'save {output / "overworld.s0"}')
        state = run(driver, repo, 'StartMenu.loop', 180, KEY['start'])
        if not at(state, repo, 'StartMenu.loop'):
            raise RuntimeError('Start menu did not open')
        run(driver, repo, frames=2)
        driver.command(f'save {output / "start-menu.s0"}')
        driver.command(f'image {output / "start-menu.ppm"}')
        driver.command('mstop')
        result = dict(overworld=start, start_menu=driver.command('m'),
                      trace=load_trace(output / 'smoke.jsonl'))
        (output / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


def tap(driver, repo, key, held=4, released=4):
    state = run(driver, repo, frames=held, keys=KEY.get(key, key) if isinstance(key, str) else key)
    return run(driver, repo, frames=released) if released else state


def enter_start_item(driver, repo, output, row, label):
    driver.command(f'load {output / "start-menu.s0"}')
    run(driver, repo, frames=4)
    for _ in range(10):
        state = driver.command('m')
        if state['wMenuCursorY'] == row:
            break
        tap(driver, repo, 'down')
    else:
        raise RuntimeError(f'Could not choose Start row {row}: {state}')
    state = run(driver, repo, label, 600, KEY['a'])
    if not at(state, repo, label):
        raise RuntimeError(f'Could not enter {label}: {state}')
    run(driver, repo, frames=40)
    return driver.command('m')


def save_menu(driver, repo, output, name, label, frames=40):
    run(driver, repo, frames=frames)
    state = driver.command('m')
    driver.command(f'save {output / (name + ".s0")}')
    driver.command(f'image {output / (name + ".ppm")}')
    return dict(state, input_loop=label)


def press_until(driver, repo, label, key='a', attempts=40):
    for _ in range(attempts):
        state = run(driver, repo, label, 8, KEY[key])
        if at(state, repo, label):
            return state
        state = run(driver, repo, label, 8)
        if at(state, repo, label):
            return state
    raise RuntimeError(f'Could not reach {label} using {key}: {state}')


def walk_to(driver, repo, axis, target):
    field = 'wXCoord' if axis == 'x' else 'wYCoord'
    for _ in range(600):
        state = driver.command('m')
        if state[field] == target:
            run(driver, repo, frames=24)
            return state
        direction = ('right' if state[field] < target else 'left') if axis == 'x' else ('down' if state[field] < target else 'up')
        run(driver, repo, frames=1, keys=KEY[direction])
    raise RuntimeError(f'Could not walk {axis} to {target}: {state}')


def walk_through_door(driver, repo, direction, map_number):
    for _ in range(400):
        state = run(driver, repo, frames=1, keys=KEY[direction])
        if state['wMapNumber'] == map_number:
            run(driver, repo, frames=100)
            return
    raise RuntimeError(f'Could not enter map {map_number}: {state}')


def settle_map_input(driver, repo):
    """Finish Continue's UI handoff through an ordinary Start/B round trip."""
    state = run(driver, repo, 'StartMenu.loop', 180, KEY['start'])
    if not at(state, repo, 'StartMenu.loop'):
        raise RuntimeError(f'Could not settle the map input owner: {state}')
    run(driver, repo, frames=40)
    tap(driver, repo, 'b', released=100)


def extra_menu_states(output, repo, core, battery):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'extra-menu-setup.log')
    rows = {}
    try:
        driver.command(f'load {output / "party.s0"}')
        press_until(driver, repo, 'MonMenuLoop')
        rows['party-actions'] = save_menu(driver, repo, output, 'party-actions', 'MonMenuLoop')
        press_until(driver, repo, 'StatsScreenMain.loop')
        rows['stats'] = save_menu(driver, repo, output, 'stats', 'StatsScreenMain.loop', 240)

        driver.command(f'load {output / "pack.s0"}')
        press_until(driver, repo, 'Pack_VerticalMenu')
        rows['pack-actions'] = save_menu(driver, repo, output, 'pack-actions', 'Pack_VerticalMenu')
        tap(driver, repo, 'down')
        tap(driver, repo, 'down')
        press_until(driver, repo, 'Pack_SelectQuantityToToss.loop')
        rows['pack-quantity'] = save_menu(driver, repo, output, 'pack-quantity', 'Pack_SelectQuantityToToss.loop')
        driver.command(f'load {output / "pack.s0"}')
        press_until(driver, repo, 'Pack_TwoOptionMenu', 'start')
        rows['pack-sort'] = save_menu(driver, repo, output, 'pack-sort', 'Pack_TwoOptionMenu')

        driver.command(f'load {output / "pokegear.s0"}')
        tap(driver, repo, 'right', released=80)
        rows['town-map'] = save_menu(driver, repo, output, 'town-map', 'PokegearMap_JohtoMap')
        if rows['town-map']['wPokegearCard'] != 1:
            raise RuntimeError('Town-map fixture did not settle on the map card')
        tap(driver, repo, 'right', released=80)
        rows['phone'] = save_menu(driver, repo, output, 'phone', 'PokegearPhone_Joypad')
        if rows['phone']['wPokegearCard'] != 2:
            raise RuntimeError('Phone fixture did not settle on the phone card')

        for pocket in range(5):
            driver.command(f'load {output / "pack.s0"}')
            for _ in range(30):
                if driver.command('m')['wCurPocket'] == pocket:
                    break
                tap(driver, repo, 'right', released=40)
            else:
                raise RuntimeError(f'Could not reach pocket {pocket}')
            name = f'pack-pocket-{pocket}'
            rows[name] = save_menu(driver, repo, output, name, 'Pack.loop')
            if rows[name]['wCurPocket'] != pocket:
                raise RuntimeError(f'Incorrect Pack pocket fixture: {name}')

        driver.command(f'load {output / "party-actions.s0"}')
        tap(driver, repo, 'down')
        tap(driver, repo, 'down')
        press_until(driver, repo, 'MoveScreenLoop')
        rows['moves'] = save_menu(driver, repo, output, 'moves', 'MoveScreenLoop')

        enter_start_item(driver, repo, output, 6, 'SaveTheGame_yesorno')
        rows['save-prompt'] = save_menu(driver, repo, output, 'save-prompt', 'SaveTheGame_yesorno')

        driver.command(f'load {output / "dex.s0"}')
        press_until(driver, repo, 'Pokedex_UpdateOptionScreen', 'select')
        rows['dex-options'] = save_menu(driver, repo, output, 'dex-options', 'Pokedex_UpdateOptionScreen')
        driver.command(f'load {output / "dex.s0"}')
        press_until(driver, repo, 'Pokedex_UpdateSearchScreen', 'start')
        rows['dex-search'] = save_menu(driver, repo, output, 'dex-search', 'Pokedex_UpdateSearchScreen')

        driver.command(f'load {output / "overworld.s0"}')
        run(driver, repo, frames=80)
        driver.command(f'save {output / "overworld-ready.s0"}')
        walk_to(driver, repo, 'x', 29)
        for _ in range(20):
            tap(driver, repo, 'up', held=3, released=20)
            state = driver.command('m')
            if state['wMapGroup'] == 26 and state['wMapNumber'] == 5:
                break
        else:
            raise RuntimeError(f'Could not enter Cherrygrove Pokemon Center: {state}')
        run(driver, repo, frames=80)
        walk_to(driver, repo, 'y', 4)
        walk_to(driver, repo, 'x', 9)
        walk_to(driver, repo, 'y', 2)
        tap(driver, repo, 'up', held=3, released=12)
        press_until(driver, repo, 'PokemonCenterPC.loop')
        rows['pc-main'] = save_menu(driver, repo, output, 'pc-main', 'PokemonCenterPC.loop')
        press_until(driver, repo, '_BillsPC.loop')
        rows['pc-pokemon'] = save_menu(driver, repo, output, 'pc-pokemon', '_BillsPC.loop')
        press_until(driver, repo, '_WithdrawPKMN.loop')
        rows['pc-withdraw'] = save_menu(driver, repo, output, 'pc-withdraw', '_WithdrawPKMN.loop')
        driver.command(f'load {output / "pc-pokemon.s0"}')
        tap(driver, repo, 'down')
        press_until(driver, repo, '_DepositPKMN.loop')
        rows['pc-deposit'] = save_menu(driver, repo, output, 'pc-deposit', '_DepositPKMN.loop')
        driver.command(f'load {output / "pc-pokemon.s0"}')
        tap(driver, repo, 'down')
        tap(driver, repo, 'down')
        press_until(driver, repo, '_ChangeBox.loop')
        rows['pc-boxes'] = save_menu(driver, repo, output, 'pc-boxes', '_ChangeBox.loop')
        press_until(driver, repo, 'BillsPC_ChangeBoxSubmenu')
        rows['pc-box-actions'] = save_menu(driver, repo, output, 'pc-box-actions', 'BillsPC_ChangeBoxSubmenu')
        tap(driver, repo, 'down')
        press_until(driver, repo, 'NamingScreen.loop')
        rows['naming'] = save_menu(driver, repo, output, 'naming', 'NamingScreen.loop')
        return rows
    finally:
        (output / 'extra-menu-states.json').write_text(json.dumps(rows, indent=2) + '\n')
        driver.close()


def menu_states(output, repo, core, battery):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'menu-setup.log')
    rows = {}
    try:
        for name, (row, label) in MENUS.items():
            rows[name] = enter_start_item(driver, repo, output, row, label)
            driver.command(f'save {output / (name + ".s0")}')
            driver.command(f'image {output / (name + ".ppm")}')
        (output / 'menu-states.json').write_text(json.dumps(rows, indent=2) + '\n')
        return rows
    finally:
        driver.close()


def expanded_menu_states(output, repo, core, battery):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'expanded-menu-setup.log')
    rows = {}
    try:
        driver.command(f'load {output / "pack-pocket-2.s0"}')
        press_until(driver, repo, 'Pack_VerticalMenu')
        press_until(driver, repo, 'TMHMCase.loop')
        rows['tmhm'] = save_menu(driver, repo, output, 'tmhm', 'TMHMCase.loop')
        press_until(driver, repo, 'TMHMCase_ItemMenu')
        rows['tmhm-actions'] = save_menu(driver, repo, output, 'tmhm-actions', 'TMHMCase_ItemMenu')

        driver.command(f'load {output / "pack-pocket-2.s0"}')
        tap(driver, repo, 'right')
        press_until(driver, repo, 'Pack_VerticalMenu')
        press_until(driver, repo, 'ApricornBox.loop')
        rows['apricorn'] = save_menu(driver, repo, output, 'apricorn', 'ApricornBox.loop')
        press_until(driver, repo, 'ApricornBox_ItemMenu')
        rows['apricorn-actions'] = save_menu(driver, repo, output, 'apricorn-actions', 'ApricornBox_ItemMenu')

        driver.command(f'load {output / "phone.s0"}')
        press_until(driver, repo, 'PokegearPhoneContactSubmenu.loop')
        rows['phone-actions'] = save_menu(driver, repo, output, 'phone-actions', 'PokegearPhoneContactSubmenu.loop')
        driver.command(f'load {output / "phone.s0"}')
        tap(driver, repo, 'right', released=80)
        rows['radio'] = save_menu(driver, repo, output, 'radio', 'PokegearRadio_Joypad')
        if rows['radio']['wPokegearCard'] != 3:
            raise RuntimeError('Radio fixture did not settle on the radio card')

        driver.command(f'load {output / "dex-options.s0"}')
        for _ in range(3):
            tap(driver, repo, 'down')
        press_until(driver, repo, 'Pokedex_UpdateUnownMode')
        rows['dex-unown'] = save_menu(driver, repo, output, 'dex-unown', 'Pokedex_UpdateUnownMode')
        driver.command(f'load {output / "dex-search.s0"}')
        tap(driver, repo, 'down')
        tap(driver, repo, 'down')
        press_until(driver, repo, 'Pokedex_UpdateSearchResultsScreen', attempts=160)
        rows['dex-results'] = save_menu(driver, repo, output, 'dex-results', 'Pokedex_UpdateSearchResultsScreen')

        driver.command(f'load {output / "pc-pokemon.s0"}')
        for _ in range(3):
            tap(driver, repo, 'down')
        press_until(driver, repo, '_MovePKMNWithoutMail.loop', attempts=160)
        rows['pc-move'] = save_menu(driver, repo, output, 'pc-move', '_MovePKMNWithoutMail.loop')
        driver.command(f'load {output / "pc-main.s0"}')
        tap(driver, repo, 'down')
        press_until(driver, repo, '_PlayersPC.loop')
        rows['pc-items-main'] = save_menu(driver, repo, output, 'pc-items-main', '_PlayersPC.loop')
        press_until(driver, repo, 'PlayerWithdrawItemMenu.loop')
        rows['pc-items-withdraw'] = save_menu(driver, repo, output, 'pc-items-withdraw', 'PlayerWithdrawItemMenu.loop')
        driver.command(f'load {output / "pc-items-main.s0"}')
        tap(driver, repo, 'down')
        press_until(driver, repo, 'PlayerDepositItemMenu.loop')
        rows['pc-items-deposit'] = save_menu(driver, repo, output, 'pc-items-deposit', 'PlayerDepositItemMenu.loop')

        driver.command(f'load {output / "party-actions.s0"}')
        for _ in range(3):
            tap(driver, repo, 'down')
        press_until(driver, repo, 'VerticalMenu')
        rows['party-item-actions'] = save_menu(driver, repo, output, 'party-item-actions', 'VerticalMenu')
        press_until(driver, repo, 'DepositSellPack.loop')
        rows['give-pack'] = save_menu(driver, repo, output, 'give-pack', 'DepositSellPack.loop')
        # Enter mail from the normal Pack. Its three-column first row puts
        # Eon Mail two cells to the right, not a row below Rare Candy.
        driver.command(f'load {output / "pack.s0"}')
        tap(driver, repo, 'right')
        tap(driver, repo, 'right')
        press_until(driver, repo, 'Pack_VerticalMenu')
        press_until(driver, repo, 'PartyMenuSelect')
        run(driver, repo, frames=40)
        press_until(driver, repo, '_ComposeMailMessage.DoMailEntry', attempts=160)
        rows['mail'] = save_menu(driver, repo, output, 'mail', '_ComposeMailMessage.DoMailEntry')
        return rows
    finally:
        (output / 'expanded-menu-states.json').write_text(json.dumps(rows, indent=2) + '\n')
        driver.close()


def location_menu_states(output, repo, core, battery, location):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'location-setup.log')
    rows = {}
    try:
        boot_overworld(driver, repo)
        settle_map_input(driver, repo)
        driver.command(f'save {output / "location-overworld.s0"}')
        if location == 'game-corner':
            tap(driver, repo, 'left', held=3, released=14)
            press_until(driver, repo, '_CardFlip.loop', attempts=160)
            rows['card-flip'] = save_menu(driver, repo, output, 'card-flip', '_CardFlip.loop')
            press_until(driver, repo, '_CardFlip.betloop')
            rows['card-bet'] = save_menu(driver, repo, output, 'card-bet', '_CardFlip.betloop')
        elif location == 'puzzle':
            tap(driver, repo, 'up', held=3, released=14)
            press_until(driver, repo, '_UnownPuzzle.loop', attempts=160)
            rows['unown-puzzle'] = save_menu(driver, repo, output, 'unown-puzzle', '_UnownPuzzle.loop')
        elif location == 'mart':
            # Continue intentionally preserves saved object structs. Re-enter
            # through the real door to instantiate the private map's clerk.
            walk_to(driver, repo, 'x', 3)
            walk_through_door(driver, repo, 'down', 3)
            walk_to(driver, repo, 'x', 23)
            walk_to(driver, repo, 'y', 4)
            walk_through_door(driver, repo, 'up', 4)
            walk_to(driver, repo, 'x', 3)
            walk_to(driver, repo, 'y', 3)
            tap(driver, repo, 'left', held=3, released=14)
            press_until(driver, repo, 'StandardMart.loop')
            rows['mart-main'] = save_menu(driver, repo, output, 'mart-main', 'StandardMart.loop')
            press_until(driver, repo, 'BuyMenuLoop')
            rows['mart-buy'] = save_menu(driver, repo, output, 'mart-buy', 'BuyMenuLoop')
            press_until(driver, repo, 'StandardMartAskPurchaseQuantity')
            rows['mart-quantity'] = save_menu(driver, repo, output, 'mart-quantity', 'StandardMartAskPurchaseQuantity')
            driver.command(f'load {output / "mart-main.s0"}')
            tap(driver, repo, 'down')
            press_until(driver, repo, 'SellMenu.loop')
            rows['mart-sell'] = save_menu(driver, repo, output, 'mart-sell', 'SellMenu.loop')
        elif location == 'battle':
            for attempts in range(160):
                direction = 'left' if attempts % 2 else 'right'
                state = run(driver, repo, 'LoadBattleMenuGraphic.loop', 20, KEY[direction])
                if at(state, repo, 'LoadBattleMenuGraphic.loop'):
                    break
                state = run(driver, repo, 'LoadBattleMenuGraphic.loop', 60, KEY['a'])
                if at(state, repo, 'LoadBattleMenuGraphic.loop'):
                    break
                run(driver, repo, frames=8)
            else:
                raise RuntimeError(f'Could not begin a grass battle: {state}')
            rows['battle-main'] = save_menu(driver, repo, output, 'battle-main', 'LoadBattleMenuGraphic.loop')
            press_until(driver, repo, 'MoveSelectionScreen.menu_loop')
            rows['battle-moves'] = save_menu(driver, repo, output, 'battle-moves', 'MoveSelectionScreen.menu_loop')
            driver.command(f'load {output / "battle-main.s0"}')
            tap(driver, repo, 'down')
            press_until(driver, repo, 'BattlePack.loop')
            rows['battle-pack'] = save_menu(driver, repo, output, 'battle-pack', 'BattlePack.loop')
            driver.command(f'load {output / "battle-main.s0"}')
            tap(driver, repo, 'right')
            press_until(driver, repo, 'PartyMenuSelect')
            rows['battle-party'] = save_menu(driver, repo, output, 'battle-party', 'PartyMenuSelect')
        else:
            raise ValueError(f'Unknown location: {location}')
        return rows
    finally:
        (output / 'location-menu-states.json').write_text(json.dumps(rows, indent=2) + '\n')
        driver.close()


def menu_inputs(output, repo, core, battery, names):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'menu-inputs.log')
    rows = []
    try:
        for name in names:
            for first, second in ORDERS:
                for mode in ('released', 'overlap'):
                    case = f'{name}-{first}-{second}-{mode}'
                    driver.command(f'load {output / (name + ".s0")}')
                    run(driver, repo, frames=3)
                    before = driver.command('m')
                    path = output / (case + '.jsonl')
                    driver.command(f'mtrace {path}')
                    first_state = tap(driver, repo, first, released=0)
                    if mode == 'released':
                        run(driver, repo, frames=2)
                    second_state = run(driver, repo, frames=4, keys=KEY[second] | (KEY[first] if mode == 'overlap' else 0))
                    final = run(driver, repo, frames=4)
                    driver.command('mstop')
                    trace = load_trace(path)
                    contracts = [e for e in trace if e['event'] == 'contract']
                    row = dict(name=case, menu=name, first=first, second=second, mode=mode,
                               before=before, first_state=first_state, second_state=second_state,
                               final=final, polls=len(contracts), fresh_polls=sum(e['fresh_direction'] for e in contracts),
                               wrong_masks=sum(not e['correct'] for e in contracts),
                               register_failures=sum(not e['registers'] for e in contracts), trace=str(path))
                    rows.append(row)
                    (output / (case + '.json')).write_text(json.dumps(row, indent=2) + '\n')
        result = dict(cases=len(rows), wrong_masks=sum(r['wrong_masks'] for r in rows),
                      register_failures=sum(r['register_failures'] for r in rows), rows=rows)
        (output / 'menu-inputs.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


MOVEMENT_FIELDS = '''wXCoord wYCoord wPlayerDirection wMapGroup wMapNumber
    wPlayerState wWalkingDirection wPlayerStepFlags wPlayerStepDirection
    wPlayerStepVectorX wPlayerStepVectorY hInMenu hJoyPressed hJoyReleased
    hJoyDown hJoyLast'''.split()


def bicycle_state(output, repo, core, battery):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'bicycle-setup.log')
    try:
        driver.command(f'load {output / "pack-pocket-2.s0"}')
        for _ in range(3):
            tap(driver, repo, 'right', released=12)
        if driver.command('m')['wKeyItemsPocketCursor'] != 4:
            raise RuntimeError('Expanded fixture did not select the Bicycle')
        press_until(driver, repo, 'Pack_VerticalMenu')
        press_until(driver, repo, 'HandleMapTimeAndJoypad', attempts=160)
        run(driver, repo, frames=100)
        state = driver.command('m')
        if state['wPlayerState'] != 1 or state['hInMenu']:
            raise RuntimeError(f'Native Bicycle use did not return to cycling: {state}')
        driver.command(f'save {output / "overworld-ready-bike.s0"}')
        return state
    finally:
        driver.close()


def area_state(output, repo, core, battery, listing):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'area-setup.log')
    try:
        driver.command(f'load {listing}')
        state = run(driver, repo, 'Pokedex_UpdateSelectedMon', 600, KEY['a'])
        if not at(state, repo, 'Pokedex_UpdateSelectedMon'):
            raise RuntimeError('Could not open the selected Dex entry')
        run(driver, repo, frames=240)
        for _ in range(3):
            tap(driver, repo, 'right', released=20)
        if driver.command('m')['wDexArrowCursorPosIndex'] != 3:
            raise RuntimeError('Could not choose the Area footer')
        press_until(driver, repo, 'Pokedex_GetArea.loop')
        return {'dex-area': save_menu(driver, repo, output, 'dex-area', 'Pokedex_GetArea.loop')}
    finally:
        driver.close()


def overworld_inputs(output, repo, core, battery, mode='walk'):
    prefix = 'movement' if mode == 'walk' else 'bicycle-movement'
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / (prefix + '.log'))
    rows = []
    sequences = {}
    for direction in ('up', 'down', 'left', 'right'):
        sequences[f'tap-{direction}'] = [(3, KEY[direction]), (30, 0)]
        sequences[f'hold-{direction}'] = [(60, KEY[direction]), (40, 0)]
        sequences[f'button-chord-{direction}'] = [(20, KEY[direction] | KEY['b']), (40, 0)]
    for first, second in ORDERS:
        sequences[f'direct-{first}-{second}'] = [(10, KEY[first]), (20, KEY[second]), (40, 0)]
        sequences[f'overlap-{first}-{second}'] = [(10, KEY[first]), (20, KEY[first] | KEY[second]), (40, 0)]
        sequences[f'diagonal-{first}-{second}'] = [(30, KEY[first] | KEY[second]), (40, 0)]
    sequences['blocked-up'] = [(180, KEY['up']), (40, 0)]
    sequences['blocked-down'] = [(180, KEY['down']), (40, 0)]
    try:
        source_state = 'overworld-ready.s0' if mode == 'walk' else 'overworld-ready-bike.s0'
        driver.command(f'load {output / source_state}')
        settle_map_input(driver, repo)
        driver.command(f'save {output / (prefix + "-ready.s0")}')
        driver.command(f'image {output / (prefix + "-ready.ppm")}')
        for name, sequence in sequences.items():
            driver.command(f'load {output / (prefix + "-ready.s0")}')
            path = output / (f'{prefix}-{name}.jsonl')
            driver.command(f'mtrace {path}')
            checkpoints = []
            for frames, keys in sequence:
                state = run(driver, repo, frames=frames, keys=keys)
                checkpoints.append({key: state[key] for key in MOVEMENT_FIELDS})
            driver.command('mstop')
            driver.command(f'image {output / (prefix + "-" + name + ".ppm")}')
            contracts = [event for event in load_trace(path) if event['event'] == 'contract']
            rows.append(dict(name=name, sequence=sequence, checkpoints=checkpoints,
                             wrong_masks=sum(not event['correct'] for event in contracts),
                             register_failures=sum(not event['registers'] for event in contracts)))
        result = dict(cases=len(rows), mode=mode, rows=rows)
        (output / (prefix + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


def menu_controls(output, repo, core, battery, names):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'menu-controls.log')
    rows = []
    controls = {
        **{f'hold-{key}': [(60, KEY[key]), (12, 0)] for key in ('up', 'down', 'left', 'right')},
        **{f'button-{key}': [(4, KEY[key]), (60, 0)] for key in ('a', 'b', 'select', 'start')},
        **{f'chord-{key}': [(4, KEY['right'] | KEY[key]), (60, 0)] for key in ('a', 'b', 'select', 'start')},
    }
    try:
        for menu in names:
            for name, sequence in controls.items():
                driver.command(f'load {output / (menu + ".s0")}')
                run(driver, repo, frames=3)
                before = driver.command('m')
                path = output / f'control-{menu}-{name}.jsonl'
                driver.command(f'mtrace {path}')
                for frames, keys in sequence:
                    state = run(driver, repo, frames=frames, keys=keys)
                driver.command('mstop')
                trace = load_trace(path)
                contracts = [e for e in trace if e['event'] == 'contract']
                final = {key: state[key] for key in FIELDS}
                rows.append(dict(menu=menu, name=name, before=before, final=final,
                                 repeats=[(e['hJoyLast'], e['wTextDelayFrames']) for e in trace
                                          if e['event'] == 'poll_return'],
                                 wrong_masks=sum(not e['correct'] for e in contracts),
                                 register_failures=sum(not e['registers'] for e in contracts)))
        result = dict(cases=len(rows), rows=rows,
                      wrong_masks=sum(r['wrong_masks'] for r in rows),
                      register_failures=sum(r['register_failures'] for r in rows))
        (output / 'menu-controls.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


def menu_returns(output, repo, core, battery, names):
    driver = Driver(core, repo.root / 'pokecrystal.gbc', BOOT, battery, output / 'menu-returns.log')
    rows = []
    try:
        for menu in names:
            driver.command(f'load {output / (menu + ".s0")}')
            if menu in ('naming', 'mail'):
                tap(driver, repo, 'start')
                tap(driver, repo, 'a', released=60)
            exited = False
            for attempts in range(20):
                tap(driver, repo, 'b', held=4, released=30)
                state = run(driver, repo, 'HandleMapTimeAndJoypad', frames=4)
                if at(state, repo, 'HandleMapTimeAndJoypad'):
                    exited = True
                    break
            if not exited:
                raise RuntimeError(f'Could not B-return from {menu}')
            run(driver, repo, frames=40)
            before = driver.command('m')
            after = tap(driver, repo, 'left', held=3, released=30)
            reopened = run(driver, repo, 'StartMenu.loop', frames=180, keys=KEY['start'])
            rows.append(dict(menu=menu, attempts=attempts + 1,
                             before={key: before[key] for key in MOVEMENT_FIELDS},
                             after={key: after[key] for key in MOVEMENT_FIELDS},
                             menu_flag_cleared=before['hInMenu'] == 0 and after['hInMenu'] == 0,
                             start_reopened=at(reopened, repo, 'StartMenu.loop')))
        result = dict(cases=len(rows), rows=rows,
                      failures=sum(not r['menu_flag_cleared'] or not r['start_reopened'] for r in rows))
        (output / 'menu-returns.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--reuse-smoke', action='store_true')
    parser.add_argument('--extras', action='store_true')
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--reuse-states', action='store_true')
    parser.add_argument('--expanded', action='store_true', help='Battery must be the private expanded fixture')
    parser.add_argument('--bicycle', action='store_true', help='Use existing expanded menu states for cycling regressions only')
    parser.add_argument('--area-state', type=Path, help='Use a matching-link Listing checkpoint for Area controls only')
    parser.add_argument('--location', choices=('game-corner', 'puzzle', 'mart', 'battle'))
    args = parser.parse_args()
    root = args.root.resolve()
    protected = [root / 'pokecrystal.gbc', root / 'pokecrystal.sym', args.battery.resolve()]
    if args.area_state:
        protected.append(args.area_state.resolve())
    output = validate_output(args.output, protected)
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    core = compile_observer(repo, args.sameboy, output)
    if args.bicycle:
        bicycle_state(output, repo, core, args.battery.resolve())
        result = overworld_inputs(output, repo, core, args.battery.resolve(), 'bike')
        print(json.dumps({'mode': result['mode'], 'cases': result['cases']}))
        return
    if args.area_state:
        states = area_state(output, repo, core, args.battery.resolve(), args.area_state.resolve())
        inputs = menu_inputs(output, repo, core, args.battery.resolve(), states)
        controls = menu_controls(output, repo, core, args.battery.resolve(), states)
        (output / 'area-menu-states.json').write_text(json.dumps(states, indent=2) + '\n')
        print(json.dumps({'menus': list(states), 'axis_cases': inputs['cases'], 'control_cases': controls['cases']}))
        return
    if args.location:
        states = location_menu_states(output, repo, core, args.battery.resolve(), args.location)
        menu_inputs(output, repo, core, args.battery.resolve(), states)
        menu_controls(output, repo, core, args.battery.resolve(), states)
        print(json.dumps({'location': args.location, 'menus': list(states)}))
        return
    if not args.reuse_smoke:
        smoke(output, repo, core, args.battery.resolve())
    if args.reuse_states:
        states = json.loads((output / 'menu-states.json').read_text())
        states.update(json.loads((output / 'extra-menu-states.json').read_text()))
    else:
        states = menu_states(output, repo, core, args.battery.resolve())
        if args.extras:
            states.update(extra_menu_states(output, repo, core, args.battery.resolve()))
    inputs = menu_inputs(output, repo, core, args.battery.resolve(), ('start-menu', *states))
    print(json.dumps({name: {key: state[key] for key in ('hInMenu', 'wMenuCursorY', 'wJumptableIndex', 'wCurPocket')}
                      for name, state in states.items()}))
    print(json.dumps({key: inputs[key] for key in ('cases', 'wrong_masks', 'register_failures')}))
    if args.controls:
        menu_controls(output, repo, core, args.battery.resolve(), ('start-menu', *states))
        overworld_inputs(output, repo, core, args.battery.resolve())
        menu_returns(output, repo, core, args.battery.resolve(), states)
    if args.expanded:
        expanded = expanded_menu_states(output, repo, core, args.battery.resolve())
        # Keep expanded results distinct from the ordinary save's primary menu matrix.
        for kind, operation in (('inputs', menu_inputs), ('controls', menu_controls), ('returns', menu_returns)):
            path = output / ('menu-' + kind + '.json')
            old = path.read_bytes()
            operation(output, repo, core, args.battery.resolve(), expanded)
            path.rename(output / ('expanded-' + kind + '.json'))
            path.write_bytes(old)


if __name__ == '__main__':
    main()
