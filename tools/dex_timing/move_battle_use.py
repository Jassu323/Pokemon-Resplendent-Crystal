"""Native battle-presentation witnesses and permanent move-discovery contracts."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from .move_persistence import boot, call, core, read, FRAME_MS
from .move_acquisition import direct, fixture, ram, live_indices
from move_discovery_assets import move_bitmap
from tools.pokedex_info_assets import constants

STEM = 'pokecrystal-dex-moves-battle-use'
CHARGES = ('FLY', 'DIG', 'SOLARBEAM', 'SKULL_BASH', 'SKY_ATTACK', 'RAZOR_WIND')
EXTRA_KINDS = ('bide',)
KINDS = ('ordinary', 'miss', 'immune', 'effect-fail', 'selected-only', 'sleep', 'freeze',
         'flinch', 'recharge', 'disabled', 'paralysis', 'confusion', 'switch-action',
         'focus', 'focus-disrupted', 'focus-already', 'focus-switch',
         'metronome', 'sleep-talk', 'sleep-talk-awake', 'sleep-talk-only-self',
         'sleep-talk-disabled', 'sleep-talk-charge-only', 'mirror', 'mirror-charge',
         'mirror-fail', 'sketch', 'sketch-copy-only', 'mimic', 'transform',
         'borrowed-use', 'struggle', 'trainer', 'tower', 'tutorial', 'scripted',
         'pre-dex', 'solar-sun', 'disobedience', 'disobedience-substitution',
         'metronome-rejections', 'scene-off', 'cancel-selection', 'cannot-move') + tuple('charge-' + n for n in CHARGES)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def witness(driver, symbols, label, actor):
    b, p = symbols[label]
    rb, address = symbols['wEnemyMoveStruct' if actor else 'wPlayerMoveStruct']
    tb, table = symbols['wMoveIndexTableEntries']
    driver.command(f'witness {b} {p} {rb} 65535 {tb} {table}')


def invoke(driver, symbols, label, budget=1800):
    b, p = symbols[label]
    driver.command(f'begin {b} {p} 0 0')
    elapsed = 0
    for n in range(budget // 16):
        result = driver.command(f'resume 16 {16 if n % 2 == 0 else 0}')
        elapsed += result['elapsed']
        if result['hit']:
            return dict(result, elapsed=elapsed)
    raise AssertionError(f'Native battle routine did not return: {label}: {result}')


def reach(driver, symbols, label, budget=1800):
    b, p = symbols[label]
    for n in range(budget // 8):
        result = driver.command(f'until {b} {p} 8 {16 if n % 2 else 0}')
        if result['hit']:
            return result
    raise AssertionError(f'Normal battle input did not reach {label}: {result}')


def finish_owner(driver, budget=1800, follow=True):
    if follow:
        driver.command('follow')
    for n in range(budget // 16):
        result = driver.command(f'resume 16 {16 if n % 2 else 0}')
        if result['hit']:
            return result
    raise AssertionError(f'Actual battle owner did not return: {result}')


def contract(config, target):
    symbols = config['symbols']
    driver = boot(config, Path(config['battery']), target / 'contracts.log')
    records = []
    durations = []
    try:
        driver.command(f'load {config["checkpoint"]}')
        driver.command(f'trace {target / "contracts-sram.csv"}')
        table_bank, table = symbols['wMoveIndexTableEntries']
        for bank in range(1, 8):
            for actor in (0, 1):
                call(driver, symbols, 'SetEnemyTurn' if actor else 'SetPlayerTurn')
                struct = 'wEnemyMoveStruct' if actor else 'wPlayerMoveStruct'
                fixture(driver, symbols, struct, [1])
                fixture(driver, symbols, 'wBattleMode', [1 + actor])
                for index in (*range(1, 334), 0, 334, 512, 65535):
                    call(driver, symbols, 'MoveDiscovery_Clear')
                    driver.command(f'fixture {table_bank} {table} {index.to_bytes(2, "little").hex()}')
                    driver.command(f'io 65392 {bank}')
                    b, p = symbols['MoveDiscovery_BattleUse']
                    owner = driver.command('peek')
                    driver.command(f'begin {b} {p} 42330 23205')
                    if not driver.command(f'until {b} {p} 4 0')['hit']:
                        raise AssertionError('Wrapper entry not reached')
                    driver.command('regs 27056 42330 23205 4660')
                    before = driver.command('peek')
                    driver.command('follow')
                    after = driver.command('resume 8 0')
                    if not after['hit'] or any(after[n] != before[n] for n in ('af', 'bc', 'de', 'hl', 'svbk', 'sram_bank', 'sram_enabled', 'double_speed')):
                        raise AssertionError(f'Wrapper register/bank contract: {before}: {after}')
                    expected = move_bitmap([index]) if 1 <= index <= 333 else bytes(64)
                    if read(driver, symbols)[:64] != expected:
                        raise AssertionError(f'Actor/index contract: {bank}/{actor}/{index}')
                    durations.append(after['elapsed'] / 140448)
                    returned = driver.command(f'until {owner["bank"]} {owner["pc"]} 8 0')
                    if not returned['hit'] or returned['sp'] != owner['sp']:
                        raise AssertionError('Contract observer did not unwind its native far call')
                    records.append(dict(bank=bank, actor=actor, index=index))
        for mode in (0, 3, 255):
            fixture(driver, symbols, 'wBattleMode', [mode])
            call(driver, symbols, 'MoveDiscovery_Clear')
            call(driver, symbols, 'MoveDiscovery_BattleUse')
            if read(driver, symbols)[:64] != bytes(64):
                raise AssertionError('Non-battle guard discovered a move')
            records.append(dict(mode=mode))
        for live in (0, 255):
            fixture(driver, symbols, 'wBattleMode', [1])
            call(driver, symbols, 'SetPlayerTurn')
            fixture(driver, symbols, 'wPlayerMoveStruct', [live])
            call(driver, symbols, 'MoveDiscovery_Clear')
            call(driver, symbols, 'MoveDiscovery_BattleUse')
            if read(driver, symbols)[:64] != bytes(64):
                raise AssertionError('Invalid live identity discovered a move')
            records.append(dict(live=live))
        call(driver, symbols, 'MoveDiscovery_Clear')
        fixture(driver, symbols, 'wPlayerMoveStruct', [1])
        for index in range(1, 334):
            driver.command(f'fixture {table_bank} {table} {index.to_bytes(2, "little").hex()}')
            call(driver, symbols, 'MoveDiscovery_BattleUse')
        if read(driver, symbols)[:64] != move_bitmap(range(1, 334)):
            raise AssertionError('Transient reuse lost permanent discoveries')
        call(driver, symbols, 'ForceGarbageCollection')
        if read(driver, symbols)[:64] != move_bitmap(range(1, 334)):
            raise AssertionError('Garbage collection changed battle discoveries')
        records.append(dict(transient_reuse=333, garbage_collection=True))
        driver.command('trace off')
        if (target / 'contracts-sram.csv').read_bytes():
            raise AssertionError('Battle discovery wrote SRAM')
    finally:
        driver.close()
    timing = {n: dict(frames=fn(durations), ms=fn(durations) * FRAME_MS)
              for n, fn in (('min', min), ('median', statistics.median), ('max', max))}
    result = dict(cases=len(records), rows=records, wrapper_body_latency=timing, issues=[])
    write_json(target / 'contracts.json', result)
    return result


def semantic(task):
    config, kind, actor, quarter, target = task
    target = Path(target) / f'{kind}-{actor}-q{quarter}'
    target.mkdir(exist_ok=True)
    symbols, values = config['symbols'], config['moves']
    driver = boot(config, Path(config['battery']), target / 'native.log')
    row = dict(case=kind, actor=actor, phase=quarter, issues=[],
               fixture='Fresh same-link wild BattleMenu checkpoint; declared battle data only; native ROM turn/effect caller.')
    try:
        driver.command(f'load {config["checkpoint"]}')
        driver.command(f'cycles {quarter * 35112} 0')
        driver.command('io 65392 1')
        call(driver, symbols, 'MoveDiscovery_Clear')
        call(driver, symbols, 'SetEnemyTurn' if actor else 'SetPlayerTurn')
        side, other = ('Enemy', 'Player') if actor else ('Player', 'Enemy')
        mon, opponent = ('wEnemyMon', 'wBattleMon') if actor else ('wBattleMon', 'wEnemyMon')
        move = ('FOCUS_PUNCH' if kind.startswith('focus') else
                'SLEEP_TALK' if kind.startswith('sleep-talk') else
                'MIRROR_MOVE' if kind.startswith('mirror') else
                'SKETCH' if kind.startswith('sketch') else
                kind[7:] if kind.startswith('charge-') else
                {'effect-fail': 'SPLASH', 'metronome': 'METRONOME', 'metronome-rejections': 'METRONOME', 'mimic': 'MIMIC',
                 'transform': 'TRANSFORM', 'borrowed-use': 'THUNDERBOLT', 'struggle': 'STRUGGLE',
                 'solar-sun': 'SOLARBEAM', 'bide': 'BIDE'}.get(kind, 'POUND'))
        ids = {name: direct(driver, symbols, 'GetMoveIDFromIndex', hl=values[name])['af'] >> 8
               for name in dict.fromkeys((move, 'SPLASH', 'SURF', 'FLY', 'THUNDERBOLT'))}
        if kind.startswith('sketch'):
            species = constants(ROOT / 'constants/pokemon_constants.asm')['SMEARGLE']
            live = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=species)['af'] >> 8
            fixture(driver, symbols, mon + 'Species', [live])
            fixture(driver, symbols, 'wOTPartyMon1Species' if actor else 'wPartyMon1Species', [live])
        for prefix in ('wPlayer', 'wEnemy'):
            for status in range(1, 6):
                fixture(driver, symbols, prefix + f'SubStatus{status}', [0])
        for prefix in ('wBattleMon', 'wEnemyMon', 'wPartyMon1'):
            fixture(driver, symbols, prefix + 'Status', [0])
            fixture(driver, symbols, prefix + 'Level', [50])
            fixture(driver, symbols, prefix + 'HP', (900).to_bytes(2, 'big'))
            fixture(driver, symbols, prefix + 'MaxHP', (1000).to_bytes(2, 'big'))
            fixture(driver, symbols, prefix + 'Moves', [ids[move], 0, 0, 0] if prefix == mon or prefix == 'wPartyMon1' and not actor else [ids['SPLASH'], 0, 0, 0])
            fixture(driver, symbols, prefix + 'PP', [40] * 4)
        for prefix in ('wBattleMon', 'wEnemyMon'):
            fixture(driver, symbols, prefix + 'Type', [21, 21])
            fixture(driver, symbols, prefix + 'Stats', b'\x00\x50\x00\xc8\x00\x64\x00\x50\x00\xc8')
        for name in ('wPlayerStats', 'wEnemyStats', 'wPartyMon1Stats'):
            fixture(driver, symbols, name, b'\x00\x50\x00\xc8\x00\x64\x00\x50\x00\xc8')
        for prefix in ('wPlayer', 'wEnemy'):
            fixture(driver, symbols, prefix + 'StatLevels', [7] * 8)
        for name in ('wCurMoveNum', 'wCurEnemyMoveNum', 'wBattlePlayerAction', 'wBattleType',
                     'wPlayerCharging', 'wEnemyCharging', 'wFocusPunchFlags', 'wDisabledMove',
                     'wEnemyDisabledMove', 'wPlayerDisableCount', 'wEnemyDisableCount', 'wAlreadyDisobeyed',
                     'wInputType', 'wJoypadDisable', 'wGameLogicPaused'):
            fixture(driver, symbols, name, [0])
        fixture(driver, symbols, 'wLinkMode', [0])
        fixture(driver, symbols, 'wJohtoBadges', [255])
        fixture(driver, symbols, 'wBattleMode', [2 if kind in ('trainer', 'tower') else 1])
        fixture(driver, symbols, 'wInBattleTowerBattle', [int(kind == 'tower')])
        fixture(driver, symbols, 'wBattleType', [3 if kind == 'tutorial' else 12 if kind == 'scripted' else 0])
        fixture(driver, symbols, 'wOTPartyCount', [1])
        fixture(driver, symbols, 'wCurOTMon', [0])
        fixture(driver, symbols, 'wOTPartyMon1PP', [40] * 4)
        fixture(driver, symbols, 'wCurEnemyMove' if actor else 'wCurPlayerMove', [ids[move]])
        fixture(driver, symbols, 'w' + other + 'SubStatus3', [8])
        if actor:
            fixture(driver, symbols, 'wWildMonMoves', [ids[move], 0, 0, 0])
            fixture(driver, symbols, 'wWildMonPP', [40] * 4)
        call(driver, symbols, 'UpdateMoveData')
        pb, pa = symbols['wPlayerMoveStruct']
        eb, ea = symbols['wEnemyMoveStruct']
        driver.command(f'actors {symbols["hBattleTurn"][1]} {pb} {pa} {eb} {ea}')
        for label in ('DisplayUsedMoveText', 'BattleCommand_Charge.awake', 'Battle_PlayFocusPunchTightenAnim'):
            witness(driver, symbols, label, actor)
        b, p = symbols['MoveDiscovery_BattleUse']
        driver.command(f'watch {b} {p}')
        driver.events.clear()
        expected = {values[move]}
        entry = 'DoEnemyTurn' if actor else 'DoPlayerTurn'
        if kind in ('selected-only', 'cancel-selection'):
            entry, expected = None, set()
        elif kind == 'cannot-move':
            expected = set()
        elif kind in ('sleep', 'freeze', 'paralysis'):
            fixture(driver, symbols, mon + 'Status', [{'sleep': 3, 'freeze': 32, 'paralysis': 64}[kind]])
            if kind != 'paralysis':
                expected = set()
        elif kind in ('flinch', 'recharge', 'confusion'):
            fixture(driver, symbols, 'w' + side + ('SubStatus4' if kind == 'recharge' else 'SubStatus3'),
                    [{'flinch': 8, 'recharge': 32, 'confusion': 128}[kind]])
            if kind == 'confusion':
                fixture(driver, symbols, 'w' + side + 'ConfuseCount', [3])
            else:
                expected = set()
        elif kind == 'disabled':
            fixture(driver, symbols, 'wEnemyDisabledMove' if actor else 'wDisabledMove', [ids[move]])
            fixture(driver, symbols, 'w' + side + 'DisableCount', [3])
            expected = set()
        elif kind in ('switch-action', 'focus-switch'):
            fixture(driver, symbols, 'wBattlePlayerAction', [2])
            if not actor:
                expected = set()
        elif kind == 'immune':
            fixture(driver, symbols, opponent + 'Type', [8, 8])
        elif kind == 'miss':
            fixture(driver, symbols, 'w' + other + 'SubStatus3', [64])
        elif kind.startswith('sleep-talk'):
            fixture(driver, symbols, mon + 'Status', [0 if kind == 'sleep-talk-awake' else 3])
            second = 'FLY' if kind == 'sleep-talk-charge-only' else 'SURF'
            fixture(driver, symbols, mon + 'Moves', [ids[move], 0 if kind == 'sleep-talk-only-self' else ids[second], 0, 0])
            if kind == 'sleep-talk-disabled':
                fixture(driver, symbols, 'wEnemyDisabledMove' if actor else 'wDisabledMove', [ids['SURF']])
                fixture(driver, symbols, 'w' + side + 'DisableCount', [3])
            if kind == 'sleep-talk':
                expected.add(values['SURF'])
        elif kind.startswith(('mirror', 'sketch')) or kind == 'mimic':
            copied = 'SOLARBEAM' if kind == 'mirror-charge' else 'SURF'
            if copied not in ids:
                ids[copied] = direct(driver, symbols, 'GetMoveIDFromIndex', hl=values[copied])['af'] >> 8
            fixture(driver, symbols, 'wLastPlayerCounterMove' if actor else 'wLastEnemyCounterMove',
                    [0 if kind == 'mirror-fail' else ids[copied]])
            if kind in ('mirror', 'mirror-charge'):
                expected.add(values[copied])
            if kind == 'sketch-copy-only':
                entry, expected = 'BattleCommand_Sketch', set()
        elif kind == 'transform':
            fixture(driver, symbols, opponent + 'Moves', [ids[n] for n in ('SURF', 'FLY', 'THUNDERBOLT', 'SPLASH')])
        elif kind == 'borrowed-use':
            fixture(driver, symbols, 'w' + side + 'SubStatus5', [8])
        elif kind == 'pre-dex':
            fixture(driver, symbols, 'wStatusFlags', [ram(driver, symbols, 'wStatusFlags')[0] & ~1])
        elif kind == 'solar-sun':
            fixture(driver, symbols, 'wBattleWeather', [2])
        elif kind in ('disobedience', 'disobedience-substitution') and not actor:
            fixture(driver, symbols, 'wJohtoBadges', [0])
            fixture(driver, symbols, mon + 'Level', [100])
            fixture(driver, symbols, 'wPartyMon1ID', b'\xfe\xed')
            fixture(driver, symbols, mon + 'Moves', [ids[move], ids['SURF'], 0, 0])
            fixture(driver, symbols, 'w2DMenuNumRows', [2])
        elif kind == 'metronome-rejections':
            ids['POUND'] = direct(driver, symbols, 'GetMoveIDFromIndex', hl=values['POUND'])['af'] >> 8
            fixture(driver, symbols, mon + 'Moves', [ids[move], ids['POUND'], 0, 0])
        elif kind == 'scene-off':
            fixture(driver, symbols, 'wOptions', [ram(driver, symbols, 'wOptions')[0] | 128])
        prepared_fields = [mon + 'Status', 'w' + side + 'SubStatus3', 'w' + side + 'SubStatus4',
                           'w' + side + 'SubStatus5', 'w' + side + 'ConfuseCount',
                           'wEnemyDisabledMove' if actor else 'wDisabledMove',
                           'w' + side + 'DisableCount', 'wBattleType', 'wBattleMode', 'wInBattleTowerBattle']
        if kind.startswith(('mirror', 'sketch')) or kind == 'mimic':
            prepared_fields += ['wLastPlayerCounterMove' if actor else 'wLastEnemyCounterMove']
        prepared = {name: ram(driver, symbols, name) for name in prepared_fields}
        fixture(driver, symbols, 'wBattleType', [0])
        fixture(driver, symbols, 'wBattleMode', [1])
        fixture(driver, symbols, 'wInBattleTowerBattle', [0])
        if kind in ('disabled', 'sleep-talk-disabled'):
            fixture(driver, symbols, 'wEnemyDisabledMove' if actor else 'wDisabledMove', [0])
            fixture(driver, symbols, 'w' + side + 'DisableCount', [0])
        if kind.startswith('focus'):
            entry = 'Battle_FocusPunchMessageEnemy' if actor else 'Battle_FocusPunchMessagePlayer'
            # Enter through real Fight/MoveSelection input. Guard fixtures apply
            # at the original message entry, before its first instruction.
            action = ram(driver, symbols, 'wBattlePlayerAction')
            fixture(driver, symbols, 'wBattlePlayerAction', [0])
            reach(driver, symbols, entry)
            fixture(driver, symbols, 'wBattlePlayerAction', action)
            if kind == 'focus-already':
                fixture(driver, symbols, 'wFocusPunchFlags', [1 << actor])
                expected = set()
            finish_owner(driver)
            if read(driver, symbols)[:64] != move_bitmap(expected):
                raise AssertionError('First focus presentation did not discover immediately')
            if kind == 'focus-disrupted':
                fixture(driver, symbols, 'wFocusPunchFlags', [(1 << actor) | (4 << actor)])
                reach(driver, symbols, 'DoEnemyTurn' if actor else 'DoPlayerTurn')
                finish_owner(driver)
            entry = None
        if entry:
            if kind == 'sketch-copy-only':
                # Isolate the existing replacement effect, without presenting
                # Sketch or the donor move as used in this fixture.
                reach(driver, symbols, entry)
                for name, value in prepared.items():
                    fixture(driver, symbols, name, value)
                call(driver, symbols, 'MoveDiscovery_Clear')
                driver.events.clear()
                finish_owner(driver)
            else:
                action = ram(driver, symbols, 'wBattlePlayerAction')
                fixture(driver, symbols, 'wBattlePlayerAction', [0])
                reach(driver, symbols, entry)
                fixture(driver, symbols, 'wBattlePlayerAction', action)
                fixture(driver, symbols, 'wCurEnemyMove' if actor else 'wCurPlayerMove', [255 if kind == 'cannot-move' else ids[move]])
                fixture(driver, symbols, 'wCurEnemyMoveNum' if actor else 'wCurMoveNum', [0])
                for name, value in prepared.items():
                    fixture(driver, symbols, name, value)
                if kind == 'transform':
                    fixture(driver, symbols, 'w' + other + 'SubStatus3', [0])
                if kind == 'metronome-rejections':
                    driver.command('follow')
                    b, p = symbols['BattleCommand_Metronome.GetMove']
                    for candidate in ('STRUGGLE', 'POUND', 'SURF'):
                        if not driver.command(f'until {b} {p + 3} 900 0')['hit']:
                            raise AssertionError('Metronome candidate return not reached')
                        registers = driver.command('peek')
                        driver.command(f'regs {registers["af"]} {values[candidate]} {registers["de"]} {registers["hl"]}')
                    row['controlled_rng_candidates'] = ['STRUGGLE (exception)', 'POUND (already owned)', 'SURF (accepted)']
                    finish_owner(driver, follow=False)
                elif kind == 'disobedience-substitution' and not actor:
                    driver.command('follow')
                    for label, result in (('BattleCommand_CheckObedience.rand1', 160),
                                          ('BattleCommand_CheckObedience.rand2', 0),
                                          ('BattleCommand_CheckObedience.RandomMove', 1)):
                        b, p = symbols[label]
                        if not driver.command(f'until {b} {p + 3} 900 0')['hit']:
                            raise AssertionError('Disobedience random-result boundary not reached')
                        registers = driver.command('peek')
                        driver.command(f'regs {(result << 8) | (registers["af"] & 255)} {registers["bc"]} {registers["de"]} {registers["hl"]}')
                    row['controlled_rng_results'] = [160, 0, 1]
                    expected = {values['SURF']}
                    finish_owner(driver, follow=False)
                else:
                    finish_owner(driver)
        elif kind == 'selected-only':
            driver.command('run 16 0')
        elif kind == 'cancel-selection':
            reach(driver, symbols, 'MoveSelectionScreen.menu_loop')
            b, p = symbols['BattleMenu.loop']
            if not driver.command(f'until {b} {p} 300 32')['hit']:
                raise AssertionError('Cancel did not return from move selection')
        presentations = [e for e in driver.events if e['event'] == 'witness' and e['point'] < 3]
        presented = {e['index'] for e in presentations if e['actor'] == actor}
        all_presented = {e['index'] for e in presentations}
        # Chance branches are checked against independent presentation boundaries,
        # never against the newly added marking routine or its bitmap.
        if kind in ('paralysis', 'confusion', 'disobedience'):
            expected = presented
        if kind == 'metronome':
            expected = presented
            if values['METRONOME'] not in expected or len(expected) < 2:
                raise AssertionError('Metronome did not present both caller and accepted move')
        if kind == 'metronome-rejections':
            expected = {values['METRONOME'], values['SURF']}
        actual = read(driver, symbols)[:64]
        if actual != move_bitmap(all_presented) or presented != expected:
            raise AssertionError(f'{kind}/{actor}/q{quarter}: expected {sorted(expected)}; witnessed {sorted(presented)}; flags {actual.hex()}')
        row.update(expected=sorted(expected), all_presented=sorted(all_presented), witnessed=presentations, bitmap=actual.hex(),
                   hook_invocations=driver.command('watchcounts')['hits'][0],
                   final=driver.command('peek'))
        if kind.startswith('charge-') or kind == 'mirror-charge':
            if not ram(driver, symbols, 'w' + side + 'SubStatus3')[0] & 16:
                raise AssertionError('First accepted charge did not remain charged')
            row['discovered_before_attack_turn'] = True
            fixture(driver, symbols, 'w' + side + 'SubStatus3', [0])
            if read(driver, symbols)[:64] != actual:
                raise AssertionError('Canceling a pending charge removed its discovery')
            row['charge_cancellation_keeps_discovery'] = True
        if kind in ('sketch', 'sketch-copy-only', 'mimic', 'transform'):
            copied = live_indices(driver, symbols, ram(driver, symbols, mon + 'Moves', 4))
            if values['SURF'] not in copied:
                raise AssertionError('Declared copy/transform fixture did not actually copy Surf')
            row['copied_moves'] = copied
        write_json(target / 'result.json', row)
        return row
    finally:
        driver.close()


def roundtrip(config, output):
    """Actual move input, flee, normal Save menu, cold reload and Dex snapshot."""
    target = output / 'battle-use/roundtrip'
    target.mkdir(exist_ok=True)
    setups = sorted((output / 'runtime/animation/setup/acquisition').glob('*/config.json'))
    setup = json.loads(setups[-1].read_text())
    symbols = config['symbols']
    driver = boot(config, Path(config['battery']), target / 'native.log')
    saved = target / 'saved-after-battle.sav'
    try:
        driver.command(f'load {setup["fixtures"]["POUND"]["player"]}')
        call(driver, symbols, 'MoveDiscovery_Clear')
        pb, pa = symbols['wPlayerMoveStruct']
        eb, ea = symbols['wEnemyMoveStruct']
        driver.command(f'actors {symbols["hBattleTurn"][1]} {pb} {pa} {eb} {ea}')
        for label in ('DisplayUsedMoveText', 'BattleCommand_Charge.awake', 'Battle_PlayFocusPunchTightenAnim'):
            witness(driver, symbols, label, 0)
        driver.events.clear()
        reach(driver, symbols, 'DoPlayerTurn')
        finish_owner(driver)
        reach(driver, symbols, 'BattleMenu.loop')
        expected = move_bitmap({e['index'] for e in driver.events if e['event'] == 'witness'})
        if read(driver, symbols)[:64] != expected or not expected[0] & 1:
            raise AssertionError('Normal battle did not record its presented moves')
        driver.command('run 4 0')
        driver.command('run 4 8')
        driver.command('run 4 0')
        driver.command('run 4 1')
        reach(driver, symbols, 'HandleMapTimeAndJoypad')
        if driver.command('peek')['double_speed'] != 1:
            raise AssertionError('Flee did not restore world speed')
        b, p = symbols['StartMenu.loop']
        if not driver.command(f'until {b} {p} 400 128')['hit']:
            raise AssertionError('Post-battle Start menu did not open')
        driver.command('run 4 0')
        menu = ram(driver, symbols, 'wMenuItemsList', 16)
        save_row = list(menu[1:menu[0] + 1]).index(4) + 1
        for _ in range(10):
            if ram(driver, symbols, 'wMenuCursorPosition')[0] == save_row:
                break
            driver.command('run 4 8')
            driver.command('run 4 0')
        reach(driver, symbols, 'SaveGameData')
        reach(driver, symbols, 'ResumeGameLogic')
        b, p = symbols['HandleMapTimeAndJoypad']
        if not driver.command(f'until {b} {p} 400 0')['hit']:
            raise AssertionError('Normal Save did not return to map')
        driver.command(f'battery {saved}')
    finally:
        driver.close()
    driver = boot(config, saved, target / 'cold-reload.log')
    try:
        if read(driver, symbols)[:64] != expected:
            raise AssertionError('Battle-only discoveries did not survive cold reload')
    finally:
        driver.close()
    from .assets import Repository
    from .cold_listing import Driver, bootstrap
    from .info_ui import BOOT
    from .moves_mode import enter, audit, capture, state
    from .info_ui import press
    repo = Repository(output / 'candidate', Path(config['rom']), output / f'{STEM}.sym')
    dex_path = output / 'modern/config.json'
    if not dex_path.exists():
        dex_path = output / 'dex-regression/modern/config.json'
    dex = json.loads(dex_path.read_text())
    if dex['hashes']['rom_sha256'] != sha256(Path(config['rom']).read_bytes()):
        raise AssertionError('Battle roundtrip Dex checkpoint belongs to a different ROM')
    driver = Driver(dex['core'], config['rom'], BOOT, saved, target / 'moves-ui.log')
    try:
        bootstrap(driver)
        enter(driver, repo)
        manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
        manifest.update(fixture='mixed', unknown=[n for n in range(1, 334) if not expected[(n - 1) // 8] & 1 << ((n - 1) % 8)])
        audit(driver, repo, manifest)
        capture(driver, target / 'battle-discoveries-unseen.png')
        current = state(driver, repo)
        ordinal = manifest['orders'][current['sort']].index(1)
        for _ in range(42):
            current = state(driver, repo)
            if ordinal - current['scroll'] - current['cursor'] < 8:
                break
            press(driver, 'right')
        for _ in range(8):
            if state(driver, repo)['selected'] == 1:
                break
            press(driver, 'down')
        if state(driver, repo)['selected'] != 1:
            raise AssertionError('Could not display the newly discovered Pound entry')
        audit(driver, repo, manifest)
        capture(driver, target / 'battle-discoveries.png')
    finally:
        driver.close()
    result = dict(actual_battle_input=True, fled=True, normal_save=True,
                  cold_reload=True, dex_snapshot=True, visible_known_entry=1,
                  bitmap=expected.hex(), issues=[])
    write_json(target / 'result.json', result)
    return result


def run(output, jobs, only=None, kinds=None):
    target = output / 'battle-use'
    target.mkdir(exist_ok=True)
    symbols = read_symbols(output / f'{STEM}.sym')
    cfg = dict(rom=str(output / f'{STEM}.gbc'), symbols=symbols,
               core=str(core(output, target_root=target)),
               battery=str(output / f'{STEM}.sav'),
               checkpoint=str(output / 'runtime/menus/acquisition/battle/battle-main.s0'),
               moves=constants(ROOT / 'constants/move_constants.asm'))
    if only == 'roundtrip':
        integration = roundtrip(cfg, output)
        report_path = output / 'battle-use-qualification.json'
        if report_path.exists():
            report = json.loads(report_path.read_text())
            if report['rom_sha256'] != sha256(Path(cfg['rom']).read_bytes()):
                raise AssertionError('Cannot attach roundtrip to a different qualified ROM')
            report['roundtrip'] = integration
            write_json(report_path, report)
        print(json.dumps(integration))
        return
    contracts = contract(cfg, target) if only != 'semantic' else None
    rows = []
    if only != 'contract':
        tasks = [(cfg, kind, actor, q, str(target)) for kind in (kinds or KINDS) for actor in (0, 1) for q in range(4)]
        with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
            for row in pool.map(semantic, tasks):
                rows.append(row)
                if len(rows) % 16 == 0:
                    print(json.dumps(dict(done=len(rows), total=len(tasks), case=row['case'])), flush=True)
        if not kinds:
            write_json(target / 'semantic.json', dict(cases=len(rows), results=rows, issues=[]))
    if kinds:
        write_json(target / ('supplemental-' + '-'.join(kinds) + '.json'),
                   dict(cases=len(rows), results=rows, issues=[]))
        return
    if only == 'contract':
        return
    if contracts is None:
        contracts = json.loads((target / 'contracts.json').read_text())
    integration = roundtrip(cfg, output)
    result = dict(rom_sha256=sha256(Path(cfg['rom']).read_bytes()),
                  contract_cases=contracts['cases'], semantic_cases=len(rows),
                  cases=contracts['cases'] + len(rows),
                  wrapper_body_latency=contracts['wrapper_body_latency'],
                  semantics=rows, roundtrip=integration, issues=[])
    write_json(output / 'battle-use-qualification.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'semantics'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--only', choices=('contract', 'semantic', 'roundtrip'))
    parser.add_argument('--kinds', choices=KINDS + EXTRA_KINDS, nargs='+')
    args = parser.parse_args()
    run(args.output.resolve(), args.jobs, args.only, args.kinds)


if __name__ == '__main__':
    main()
