"""Native stage-two discovery tests and an independent legacy ownership oracle."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from .assets import read_symbols, sha256, offset
from .move_persistence import boot, call, core, read, checksum, core_valid, cold_case, STEM
from move_discovery_assets import address, move_bitmap, seed_records, decode_record
from tools.pokedex_info_assets import constants
from .cold_listing import ROOT, KEY


def saved_field(data, symbols, name, size=1, prefix='s'):
    bank, at = symbols[name]
    for block in ('PlayerData', 'CurMapData', 'PokemonData'):
        b, start = symbols['w' + block]
        if b == bank and start <= at < symbols['w' + block + 'End'][1]:
            offset = address(symbols, prefix + block) + at - start
            return data[offset:offset + size]
    raise ValueError(name)


def owned_indices(data, symbols, prefix='s'):
    """Decode saved ownership without running conversion, GC, or the ROM walker."""
    entries = address(symbols, prefix + 'MoveIndexTable') + (
        symbols['wMoveIndexTableEntries'][1] - symbols['wMoveIndexTable'][1])
    capacity = (symbols['wMoveIndexTableEntriesEnd'][1] - symbols['wMoveIndexTableEntries'][1]) // 2
    def live(value):
        if not 1 <= value <= capacity:
            return 0
        return int.from_bytes(data[entries + (value - 1) * 2:entries + value * 2], 'little')
    moves = set()
    species = saved_field(data, symbols, 'wPartySpecies', 6)
    for slot in range(min(6, saved_field(data, symbols, 'wPartyCount')[0])):
        if species[slot] not in (0, 0xfd, 0xff):
            moves.update(live(v) for v in saved_field(data, symbols, f'wPartyMon{slot + 1}Moves', 4))
    for slot, owner in ((1, 'wDayCareMan'), (2, 'wDayCareLady')):
        if saved_field(data, symbols, owner)[0] & 1 and saved_field(data, symbols, f'wBreedMon{slot}Species')[0] not in (0, 0xfd, 0xff):
            moves.update(live(v) for v in saved_field(data, symbols, f'wBreedMon{slot}Moves', 4))
    length = symbols['sBoxMon2'][1] - symbols['sBoxMon1'][1]
    move_offset = symbols['sBoxMon1Moves'][1] - symbols['sBoxMon1'][1]
    pp_offset = symbols['sBoxMon1PP'][1] - symbols['sBoxMon1'][1]
    for box in range(1, 15):
        at = address(symbols, f'sBox{box}')
        for slot in range(min(20, data[at])):
            if data[at + 1 + slot] in (0, 0xfd, 0xff):
                continue
            mon = at + 22 + slot * length
            moves.update(data[mon + move_offset + n] | (data[mon + pp_offset + n] & 63) << 8
                         for n in range(4))
    return sorted(n for n in moves if 1 <= n <= 333)


def expected_migration(data, symbols, prefix='s'):
    return move_bitmap(owned_indices(data, symbols, prefix))


def fixture(driver, symbols, name, data):
    bank, at = symbols[name]
    driver.command(f'fixture {bank} {at} {bytes(data).hex()}')


def direct(driver, symbols, name, af=0, bc=0xa55a, de=0x5aa5, hl=0):
    bank, pc = symbols[name]
    if bank:
        raise ValueError('Direct input helper must be in HOME')
    row = driver.command(f'direct {pc} {af} {bc} {de} {hl}')
    if not row['hit']:
        raise AssertionError(f'{name} did not return')
    return row


def ram(driver, symbols, name, size=1):
    bank, at = symbols[name]
    return bytes.fromhex(driver.command(f'read {bank} {at} {size}')['bytes'])


def live_indices(driver, symbols, ids):
    return [direct(driver, symbols, 'GetMoveIndexFromID', af=n << 8)['hl'] for n in ids if n]


def source_case(task):
    config, kind, target = task
    target = Path(target)
    symbols = config['symbols']
    driver = boot(config, target / 'empty.sav', target / (kind + '.log'))
    moves = constants(ROOT / 'constants/move_constants.asm')
    pokemon = constants(ROOT / 'constants/pokemon_constants.asm')
    result = dict(case=kind, issues=[], controlled_fixture=True, actual_rom_caller=True)
    try:
        if kind in ('learn-battle', 'learn-transformed', 'learn-other-mon') or kind.startswith('ball-'):
            setups = sorted((target.parent / 'runtime/animation/setup/acquisition').glob('*/config.json'))
            if not setups:
                raise AssertionError('Battle source testing requires a freshly linked real-battle checkpoint')
            checkpoint = json.loads(setups[-1].read_text())['fixtures']['POUND']['player']
            if driver.command(f'load {checkpoint}').get('error'):
                raise AssertionError('Could not load the declared battle fixture')
            result['native_battle_checkpoint'] = checkpoint
            if kind in ('ball-failed', 'ball-tutorial'):
                # The ball handler restores the battle from its Pack owner.
                # A battle-menu-only checkpoint is not a valid item caller.
                driver.command('run 4 0')
                driver.command(f'run 4 {KEY["down"]}')
                driver.command('run 4 0')
                b, p = symbols['BattlePack.loop']
                state = driver.command(f'until {b} {p} 600 16')
                if not state['hit']:
                    raise AssertionError('Ball source did not enter the real battle Pack')
                driver.command('run 4 0')
                result['native_pack_owner'] = True
        call(driver, symbols, 'MoveDiscovery_Clear')
        driver.command('io 65392 1')
        species = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=pokemon['BULBASAUR'])['af'] >> 8
        ids = [direct(driver, symbols, 'GetMoveIDFromIndex', hl=moves[n])['af'] >> 8
               for n in ('TACKLE', 'GROWL', 'LEECH_SEED', 'VINE_WHIP', 'SOLARBEAM')]
        if kind.startswith('hm-'):
            ids[4] = direct(driver, symbols, 'GetMoveIDFromIndex', hl=moves['CUT'])['af'] >> 8
        fixture(driver, symbols, 'wBattleMode', [0])
        fixture(driver, symbols, 'wMonType', [0])
        fixture(driver, symbols, 'wCurPartyMon', [0])
        fixture(driver, symbols, 'wCurPartyLevel', [7])
        fixture(driver, symbols, 'wCurPartySpecies', [species])
        fixture(driver, symbols, 'wTempSpecies', [species])
        fixture(driver, symbols, 'wPartyCount', [1])
        fixture(driver, symbols, 'wPartySpecies', [species, 255])
        fixture(driver, symbols, 'wPartyMon1Species', [species])
        fixture(driver, symbols, 'wPartyMon1Level', [7])
        fixture(driver, symbols, 'wPartyMon1Moves', ids[:4])
        fixture(driver, symbols, 'wPartyMon1PP', [35, 40, 10, 25])
        fixture(driver, symbols, 'sBoxCount', [0, 255])
        fixture(driver, symbols, 'wPutativeTMHMMove', [ids[4]])
        fixture(driver, symbols, 'wNamedObjectIndex', [ids[4]])
        entry, bc, de, keys = 'LearnMove', 0, 0, (16, 0)
        expected = move_bitmap([moves['CUT' if kind.startswith('hm-') else 'SOLARBEAM']])
        destination = None
        if kind.startswith(('learn-', 'tm-', 'hm-', 'tutor-', 'level-', 'evolution-')):
            if 'empty' in kind or 'success' in kind or 'battle' in kind or 'transformed' in kind or 'other-mon' in kind:
                fixture(driver, symbols, 'wPartyMon1Moves', [ids[0], 0, 0, 0])
            if any(n in kind for n in ('battle', 'transformed', 'other-mon')):
                fixture(driver, symbols, 'wGameLogicPaused', [0])
                fixture(driver, symbols, 'wJoypadDisable', [0])
                fixture(driver, symbols, 'wInputType', [0])
                fixture(driver, symbols, 'wBattleMode', [1])
                fixture(driver, symbols, 'wCurBattleMon', [int('other-mon' in kind)])
                fixture(driver, symbols, 'wPlayerSubStatus5', [8 if 'transformed' in kind else 0])
                fixture(driver, symbols, 'wBattleMonMoves', ids[:4])
            if 'decline' in kind:
                keys = (32, 0, 16, 0)
                expected = bytes(64)
            if kind.startswith('tm-'):
                entry = 'TeachTMHM'
                fixture(driver, symbols, 'wCurItem', [0xd7])
            if kind.startswith('hm-'):
                entry = 'TeachTMHM'
                fixture(driver, symbols, 'wCurItem', [0xf4])
            if kind.startswith('tutor-'):
                entry = 'CheckCanLearnMoveTutorMove'
            if 'known' in kind:
                fixture(driver, symbols, 'wPartyMon1Moves', [ids[4], 0, 0, 0])
                expected = bytes(64)
            if 'incompatible' in kind:
                splash = direct(driver, symbols, 'GetMoveIDFromIndex', hl=moves['SPLASH'])['af'] >> 8
                fixture(driver, symbols, 'wPutativeTMHMMove', [splash])
                fixture(driver, symbols, 'wNamedObjectIndex', [splash])
                expected = bytes(64)
            if kind.startswith('level-'):
                entry = 'LearnLevelMoves'
                fixture(driver, symbols, 'wTempSpecies', [species])
                # Bulbasaur's level-seven move is resolved independently below.
                fixture(driver, symbols, 'wPartyMon1Moves', [ids[0], 0, 0, 0])
                expected = None if 'success' in kind else bytes(64)
                if 'decline' in kind:
                    fixture(driver, symbols, 'wPartyMon1Moves', [ids[0], ids[1], ids[1], ids[1]])
            if kind.startswith('evolution-'):
                entry = 'LearnEvolutionMove'
                evolved = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=pokemon['PERSIAN'])['af'] >> 8
                fixture(driver, symbols, 'wTempSpecies', [evolved])
                fixture(driver, symbols, 'wCurPartySpecies', [evolved])
                at = offset(symbols['EvolutionMoves']) + (pokemon['PERSIAN'] - 1) * 2
                driver.command(f'romfixture {at} {moves["SOLARBEAM"].to_bytes(2, "little").hex()}')
                result['data_only_fixture'] = 'All shipped evolution moves are NO_MOVE; configure one table entry in this emulator instance only.'
                expected = None if 'success' in kind else bytes(64)
        elif kind.startswith('ball-'):
            entry, expected = 'PokeBallEffect', bytes(64)
            fixture(driver, symbols, 'wBattleMode', [2 if kind == 'ball-trainer' else 1])
            fixture(driver, symbols, 'wBattleType', [0])
            fixture(driver, symbols, 'wCurItem', [5 if kind == 'ball-failed' else 1])
            fixture(driver, symbols, 'wEnemyMonCatchRate', [0])
            fixture(driver, symbols, 'wEnemyMonStatus', [0])
            fixture(driver, symbols, 'wEnemyMonHP', bytes([0, 255, 0, 255]))
            if kind in ('ball-failed', 'ball-tutorial'):
                fixture(driver, symbols, 'wNumBalls', [1])
                fixture(driver, symbols, 'wBalls', [5 if kind == 'ball-failed' else 1, 99, 255])
            if kind == 'ball-full':
                fixture(driver, symbols, 'wPartyCount', [6])
                fixture(driver, symbols, 'sBoxCount', [20])
        elif kind.startswith('gift-'):
            entry, keys, destination = 'GivePoke', (32, 0), 'party'
            fixture(driver, symbols, 'wCurItem', [0])
            expected = None
            if 'extended' in kind:
                extended = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=pokemon['GARCHOMP'])['af'] >> 8
                fixture(driver, symbols, 'wCurPartySpecies', [extended])
                fixture(driver, symbols, 'wCurPartyLevel', [100])
                at = offset(symbols['GarchompEvosAttacks']) + 2
                driver.command(f'romfixture {at} {moves["CAUSTIC"].to_bytes(2, "little").hex()}')
                result['data_only_fixture'] = 'Garchomp currently has only Tackle; replace its one learnset word in this emulator instance to exercise an extended acquired move.'
            if 'pre-dex' in kind:
                fixture(driver, symbols, 'wStatusFlags', [ram(driver, symbols, 'wStatusFlags')[0] & ~1])
            if 'box' in kind or 'full' in kind:
                fixture(driver, symbols, 'wPartyCount', [6])
                fixture(driver, symbols, 'wPartySpecies', [species] * 6 + [255])
                destination = 'box'
            if 'full' in kind:
                fixture(driver, symbols, 'sBoxCount', [20])
                expected, destination = bytes(64), None
        elif kind.startswith('egg-'):
            keys = (32, 0)
            if kind in ('egg-receipt', 'egg-full'):
                entry, expected = 'GiveEgg', bytes(64)
                if kind == 'egg-full':
                    fixture(driver, symbols, 'wPartyCount', [6])
            else:
                entry = 'HatchEggs'
                fixture(driver, symbols, 'wPartySpecies', [0xfd, 255])
                fixture(driver, symbols, 'wPartyMon1Happiness', [0 if kind == 'egg-hatch' else 5])
                expected = move_bitmap([moves[n] for n in ('TACKLE', 'GROWL', 'LEECH_SEED', 'VINE_WHIP')]) if kind == 'egg-hatch' else bytes(64)
        elif kind.startswith('daycare-'):
            entry, expected, destination = 'RetrieveBreedmon', None, 'party'
            mon = ram(driver, symbols, 'wPartyMon1', symbols['wPartyMon1BoxEnd'][1] - symbols['wPartyMon1'][1])
            slot = 2 if 'lady' in kind else 1
            fixture(driver, symbols, f'wBreedMon{slot}', mon)
            fixture(driver, symbols, f'wBreedMon{slot}Nickname', b'TEST\x50' + bytes(6))
            fixture(driver, symbols, f'wBreedMon{slot}OT', b'TEST\x50' + bytes(6))
            fixture(driver, symbols, 'wPokemonWithdrawDepositParameter', [slot - 1])
            if 'full' in kind:
                fixture(driver, symbols, 'wPartyCount', [6])
                expected, destination = bytes(64), None
            if 'service' in kind:
                entry = 'DayCareLady' if slot == 2 else 'DayCareMan'
                fixture(driver, symbols, 'wDayCareLady' if slot == 2 else 'wDayCareMan', [1])
                fixture(driver, symbols, 'wMoney', (10000).to_bytes(3, 'big'))
                if 'decline' in kind:
                    keys, expected, destination = (32, 0), bytes(64), None
                if 'poor' in kind:
                    fixture(driver, symbols, 'wMoney', bytes(3))
                    expected, destination = bytes(64), None
        elif kind == 'contest-pending':
            entry, expected, keys = 'BugContest_SetCaughtContestMon', bytes(64), (32, 0)
            fixture(driver, symbols, 'wContestMonSpecies', [0])
            fixture(driver, symbols, 'wTempEnemyMonSpecies', [species])
        elif kind.startswith('contest-'):
            entry, keys, expected, destination = 'CheckPartyFullAfterContest', (32, 0), None, 'party'
            mon = ram(driver, symbols, 'wPartyMon1', symbols['wPartyMon1StructEnd'][1] - symbols['wPartyMon1'][1])
            fixture(driver, symbols, 'wContestMon', mon)
            if 'box' in kind or 'full' in kind:
                fixture(driver, symbols, 'wPartyCount', [6])
                destination = 'box'
            if 'full' in kind:
                fixture(driver, symbols, 'sBoxCount', [20])
                expected, destination = bytes(64), None
            if 'none' in kind:
                fixture(driver, symbols, 'wContestMonSpecies', [0])
                expected, destination = bytes(64), None
        elif kind.startswith('dratini-'):
            entry, expected = 'GiveDratini', None
            dratini = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=pokemon['DRATINI'])['af'] >> 8
            fixture(driver, symbols, 'wPartyMon1Species', [dratini])
            fixture(driver, symbols, 'wPartySpecies', [dratini, 255])
            fixture(driver, symbols, 'wScriptVar', [2 if 'skip' in kind else int('normal' in kind)])
            if 'skip' in kind:
                expected = bytes(64)
            else:
                destination = 'party'
        elif kind.startswith('trade-'):
            entry, expected = 'NPCTrade', bytes(64)
            fixture(driver, symbols, 'wTradeFlags', [0])
            if kind == 'trade-success':
                entry, expected, destination = 'NPCTrade', None, 'party'
                requested = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=pokemon['ABRA'])['af'] >> 8
                fixture(driver, symbols, 'wPartySpecies', [requested, 255])
                fixture(driver, symbols, 'wPartyMon1Species', [requested])
            if kind == 'trade-decline':
                keys = (32, 0)
        elif kind == 'enemy-generation':
            entry, expected = 'TryAddMonToParty', bytes(64)
            fixture(driver, symbols, 'wMonType', [4])
        else:
            raise ValueError(kind)
        hook_names = ('Learned', 'Gift', 'LastParty', 'CurrentParty', 'FirstBox', 'MarkLiveID')
        for name in hook_names:
            bank, pc = symbols['MoveDiscovery_' + name]
            driver.command(f'watch {bank} {pc}')
        before_moves = ram(driver, symbols, 'wPartyMon1Moves', 4)
        result['input_context'] = {n: list(ram(driver, symbols, n)) for n in
                                   ('wInputType', 'wJoypadDisable', 'wGameLogicPaused', 'wBattleMode', 'wCurBattleMon', 'wPlayerSubStatus5')}
        bank, pc = symbols[entry]
        result['entry'] = entry
        if kind in ('ball-failed', 'ball-tutorial'):
            for _ in range(6):
                if ram(driver, symbols, 'wCurPocket')[0] == 1:
                    break
                driver.command(f'run 4 {KEY["right"]}')
                driver.command('run 40 0')
            else:
                raise AssertionError('Could not select Balls pocket')
            for n in range(150):
                state = driver.command(f'until {bank} {pc} 8 {16 if n % 2 == 0 else 0}')
                if state['hit']:
                    break
            else:
                raise AssertionError('Actual ball selection did not reach the item effect')
            if kind == 'ball-tutorial':
                tutorial = constants(ROOT / 'constants/battle_constants.asm')['BATTLETYPE_TUTORIAL']
                fixture(driver, symbols, 'wBattleType', [tutorial])
                result['tutorial_type_at_effect_entry'] = True
            driver.command('follow')
            result['ordinary_ball_selection'] = True
        else:
            driver.command(f'begin {bank} {pc} {bc} {de}')
        if 'decline' in kind and kind.startswith(('learn-', 'tm-', 'hm-', 'tutor-', 'level-', 'evolution-')):
            def until(label, key):
                b, p = symbols[label]
                for n in range(150):
                    state = driver.command(f'until {b} {p} 8 {key if n % 2 == 0 else 0}')
                    if state['hit']:
                        return
                raise AssertionError(f'Decline fixture did not reach {label}: {state}')
            until('ForgetMove', 0)
            until('LearnMove.cancel', 32)
            until('PlaceYesNoBox', 16)
            keys = (0, 16)
        if kind in ('learn-battle', 'learn-transformed', 'learn-other-mon'):
            b, p = symbols['LearnMove.learned']
            # Ten-byte preserving hook, immediately before the existing message.
            returned = driver.command(f'until {b} {p + 10} 1200 0')
            if not returned['hit']:
                raise AssertionError('Battle learning did not reach its committed hook boundary')
            result['commit_boundary_only'] = True
        else:
            for n in range(500):
                returned = driver.command(f'resume 8 {keys[n % len(keys)]}')
                if returned['hit']:
                    break
            else:
                raise AssertionError(f'{kind}: caller did not finish: {returned}')
        result['return'] = returned
        result['hook_hits'] = dict(zip(hook_names, driver.command('watchcounts')['hits']))
        if expected is None:
            if destination == 'box':
                direct(driver, symbols, 'OpenSRAM', af=symbols['sBoxMon1Moves'][0] << 8)
                saved = target / (kind + '-received.sav')
                driver.command(f'battery {saved}')
                at = address(symbols, 'sBoxMon1Moves')
                received = saved.read_bytes()[at:at + 4]
            elif destination == 'party':
                slot = ram(driver, symbols, 'wPartyCount')[0]
                received = ram(driver, symbols, f'wPartyMon{slot}Moves', 4)
            else:
                after = ram(driver, symbols, 'wPartyMon1Moves', 4)
                received = [m for m in after if m and m not in before_moves]
            indices = live_indices(driver, symbols, received)
            if not indices:
                raise AssertionError('Positive source did not actually acquire or learn a move')
            expected = move_bitmap(indices)
            result['received_indices'] = indices
            if 'extended' in kind and not any(n > 255 for n in indices):
                raise AssertionError('Extended acquisition did not exercise a high permanent move index')
        if read(driver, symbols)[:64] != expected:
            raise AssertionError(f'{kind}: unexpected discovery bitmap: {read(driver, symbols)[:64].hex()} vs {expected.hex()}')
        result['discovered'] = [n for n in range(1, 334) if expected[(n - 1) // 8] & 1 << ((n - 1) % 8)]
        if kind.startswith('ball-'):
            result['wild_mon'] = ram(driver, symbols, 'wWildMon')[0]
            if any(result['hook_hits'].values()):
                raise AssertionError('Rejected/tutorial ball use reached an acquisition hook')
            if kind == 'ball-failed' and result['wild_mon']:
                raise AssertionError('Declared failed-catch fixture did not roll a failed catch')
        if kind.startswith('daycare-service'):
            owner = 'wDayCareLady' if 'lady' in kind else 'wDayCareMan'
            occupied = bool(ram(driver, symbols, owner)[0] & 1)
            money = int.from_bytes(ram(driver, symbols, 'wMoney', 3), 'big')
            success = 'success' in kind
            level = ram(driver, symbols, f'wPartyMon{ram(driver, symbols, "wPartyCount")[0]}Level')[0] if success else None
            price = 100 * (level - 7 + 1) if success else 0
            if occupied == success or money != (10000 - price if success else 0 if 'poor' in kind else 10000):
                raise AssertionError(f'Daycare service occupancy/payment mismatch: {occupied}/{money}')
            result.update(daycare_occupied=occupied, money_after=money, received_level=level, price=price)
        if not any(expected) and result['hook_hits']['Learned']:
            raise AssertionError('Declined learning reached successful commit')
        result['party_moves_before'] = list(before_moves)
        result['party_moves_after'] = list(ram(driver, symbols, 'wPartyMon1Moves', 4))
        if kind == 'learn-battle' and ram(driver, symbols, 'wBattleMonMoves', 4) != ram(driver, symbols, 'wPartyMon1Moves', 4):
            raise AssertionError('Battle learning did not synchronize its live moves')
        if kind in ('learn-transformed', 'learn-other-mon') and ram(driver, symbols, 'wBattleMonMoves', 4) != bytes(ids[:4]):
            raise AssertionError('Learning overwrote a transformed or unrelated battle moveset')
    except Exception as error:
        result['issues'].append(str(error))
    finally:
        driver.close()
    (target / (kind + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def helpers(config, target):
    symbols = config['symbols']
    driver = boot(config, target / 'empty.sav', target / 'acquisition-helpers.log')
    cases = 0
    timings = {}
    try:
        before = target / 'helpers-before.sav'
        driver.command(f'battery {before}')
        entries = symbols['wMoveIndexTableEntries'][1]
        for bank in range(1, 8):
            driver.command(f'io 65392 {bank}')
            for index in (*range(1, 334), 0, 334, 512, 0x3fff, 0xffff):
                call(driver, symbols, 'MoveDiscovery_Clear')
                driver.command(f'fixture 2 {entries} {index.to_bytes(2, "little").hex()}')
                result = call(driver, symbols, 'MoveDiscovery_MarkLiveID', 0x5aa5, bc=0xa501)
                expected = move_bitmap([index]) if 1 <= index <= 333 else bytes(64)
                if read(driver, symbols)[:64] != expected or result['bc'] != 0xa501 or result['de'] != 0x5aa5 or result['svbk'] & 7 != bank:
                    raise AssertionError(f'Live ID contract: {bank}/{index}: {result}')
                if bool(result['af'] & 16) != (1 <= index <= 333):
                    raise AssertionError('Live ID validity result')
                timings.setdefault('live_ms', []).append(result['ms'])
                cases += 1
        # One transient byte identity is reused across every permanent move.
        call(driver, symbols, 'MoveDiscovery_Clear')
        for index in range(1, 334):
            driver.command(f'fixture 2 {entries} {index.to_bytes(2, "little").hex()}')
            call(driver, symbols, 'MoveDiscovery_MarkLiveID', bc=1)
        if read(driver, symbols)[:64] != move_bitmap(range(1, 334)):
            raise AssertionError('Transient reuse changed permanent flags')
        cases += 333
        driver.command('io 65392 1')
        direct(driver, symbols, 'GetMoveIDFromIndex', hl=333)
        before_gc = read(driver, symbols)[:64]
        call(driver, symbols, 'ForceGarbageCollection')
        if read(driver, symbols)[:64] != before_gc:
            raise AssertionError('GC altered discoveries')
        cases += 1
        # Packed high bits and PP-Up bits, including invalid reserved indices.
        packed = symbols['wBufferMonMoves'][1]
        pp = symbols['wBufferMonPP'][1]
        for bank in range(1, 8):
            driver.command(f'io 65392 {bank}')
            for index in (*range(1, 334), 0, 334, 512, 0x3fff):
                for ups in (0, 0x40, 0x80, 0xc0):
                    call(driver, symbols, 'MoveDiscovery_Clear')
                    driver.command(f'fixture {bank} {packed} {bytes([index & 255, 0, 0, 0]).hex()}')
                    driver.command(f'fixture {bank} {pp} {bytes([(index >> 8) | ups, 0, 0, 0]).hex()}')
                    result = call(driver, symbols, 'MoveDiscovery_PackedMoves', packed)
                    if read(driver, symbols)[:64] != (move_bitmap([index]) if 1 <= index <= 333 else bytes(64)):
                        raise AssertionError(f'Packed index decode: {bank}/{index}/{ups}')
                    if result['bc'] != 0xa55a or result['de'] != packed or result['svbk'] & 7 != bank:
                        raise AssertionError('Packed walker register/bank contract')
                    cases += 1
        for bank in range(1, 8):
            for sram in range(5):
                direct(driver, symbols, 'OpenSRAM', af=(sram if sram < 4 else 255) << 8)
                driver.command(f'io 65392 {bank}')
                before_state = driver.command('peek')
                for name in ('MoveDiscovery_FirstBox', 'MoveDiscovery_LastParty', 'MoveDiscovery_CurrentParty',
                             'MoveDiscovery_BootstrapOwned'):
                    result = call(driver, symbols, name, 0x5aa5)
                    if result['bc'] != 0xa55a or result['de'] != 0x5aa5 or result['svbk'] & 7 != bank or result['bank'] != before_state['bank']:
                        raise AssertionError(f'Ownership context restoration: {name}: {result}')
                    if result['sram_enabled'] != before_state['sram_enabled'] or (before_state['sram_enabled'] and result['sram_bank'] != before_state['sram_bank']):
                        raise AssertionError(f'SRAM ownership not restored: {name}')
                    cases += 1
        after = target / 'helpers-after.sav'
        driver.command(f'battery {after}')
        if before.read_bytes()[:32768] != after.read_bytes()[:32768]:
            raise AssertionError('Receipt helpers wrote SRAM')
    finally:
        driver.close()
    return dict(cases=cases, timings=timings, issues=[])


def migration_fixtures(config, target, source):
    symbols = config['symbols']
    length = symbols['sBoxMon2'][1] - symbols['sBoxMon1'][1]
    moves_offset = symbols['sBoxMon1Moves'][1] - symbols['sBoxMon1'][1]
    pp_offset = symbols['sBoxMon1PP'][1] - symbols['sBoxMon1'][1]
    tasks = []
    for current in range(14):
        data = bytearray(source)
        for box in range(1, 15):
            at = address(symbols, f'sBox{box}')
            data[at:at + 22] = bytes([20] + [1] * 20 + [255])
            species_indexes = address(symbols, f'sBox{box}PokemonIndexes')
            data[species_indexes:species_indexes + 40] = b'\x01\x00' * 20
            for slot in range(20):
                mon = at + 22 + slot * length
                data[mon] = 1
                for n in range(4):
                    index = ((box - 1) * 80 + slot * 4 + n) % 333 + 1
                    data[mon + moves_offset + n] = index & 255
                    data[mon + pp_offset + n] = index >> 8 | (n % 4) << 6
        for prefix in ('s', 'sBackup'):
            def write(name, value):
                bank, at = symbols[name]
                for block in ('PlayerData', 'CurMapData', 'PokemonData'):
                    b, start = symbols['w' + block]
                    if b == bank and start <= at < symbols['w' + block + 'End'][1]:
                        dest = address(symbols, prefix + block) + at - start
                        data[dest:dest + len(value)] = value
                        return
                raise ValueError(name)
            write('wCurBox', bytes([current]))
            write('wPartyCount', bytes([6]))
            original_species = saved_field(source, symbols, 'wPartySpecies')[0]
            write('wPartySpecies', bytes([original_species] * 6 + [255]))
            template = saved_field(source, symbols, 'wPartyMon1',
                                   symbols['wPartyMon1StructEnd'][1] - symbols['wPartyMon1'][1])
            for slot in range(1, 7):
                write(f'wPartyMon{slot}', template)
            for slot, name in ((1, 'wDayCareMan'), (2, 'wDayCareLady')):
                write(name, b'\x01')
                write(f'wBreedMon{slot}', template[:length])
            checksum(data, symbols, prefix)
            at = address(symbols, prefix + 'MoveDiscovery')
            data[at:at + 136] = bytes(136)
        path = target / f'legacy-full-current-{current + 1}.sav'
        path.write_bytes(data)
        if owned_indices(data, symbols) != list(range(1, 334)):
            raise AssertionError('Maximum-capacity oracle fixture is not exhaustive')
        tasks.append((config, path, bytes(64), 3, 0))
    # A legacy fixture's existing ownership is preserved, not released history.
    tasks.append((config, target.parent / 'legacy-input.sav', bytes(64), 3, 0))
    return tasks


def migration_tests(config, target, source, jobs):
    tasks = migration_fixtures(config, target, source)
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        records = list(pool.map(cold_case, tasks))
    symbols = config['symbols']
    driver = boot(config, target / 'empty.sav', target / 'migration-read-only.log')
    try:
        before = target / 'migration-before.sav'
        driver.command(f'battery {before}')
        call(driver, symbols, 'MoveDiscovery_Clear')
        context = driver.command('peek')
        seen = call(driver, symbols, 'MoveDiscovery_BootstrapOwned')
        after = target / 'migration-after.sav'
        driver.command(f'battery {after}')
        if before.read_bytes()[:32768] != after.read_bytes()[:32768]:
            raise AssertionError('Read-only bootstrap altered PC or save data')
        if read(driver, symbols)[:64] != expected_migration(source, symbols):
            raise AssertionError('Read-only bootstrap differs from saved-ownership oracle')
        if seen['svbk'] != context['svbk'] or seen['sram_enabled'] != context['sram_enabled']:
            raise AssertionError('Read-only scan lost caller ownership')
    finally:
        driver.close()
    live = migration_live_cases(config, target)
    return dict(cases=len(records) + 1 + len(live), cold_loads=records, live_edge_cases=live, read_only_time=seen,
                maximum_pokemon=288, maximum_move_slots=1152, issues=[])


def migration_live_cases(config, target):
    symbols = config['symbols']
    driver = boot(config, target / 'empty.sav', target / 'migration-live-edges.log')
    records = []
    length = symbols['sBoxMon2'][1] - symbols['sBoxMon1'][1]
    mo = symbols['sBoxMon1Moves'][1] - symbols['sBoxMon1'][1]
    pp = symbols['sBoxMon1PP'][1] - symbols['sBoxMon1'][1]
    try:
        ids = {n: direct(driver, symbols, 'GetMoveIDFromIndex', hl=n)['af'] >> 8
               for n in (*range(1, 7), 20, 255, 256, 333)}

        def reset():
            call(driver, symbols, 'MoveDiscovery_Clear')
            fixture(driver, symbols, 'wPartyCount', [0])
            fixture(driver, symbols, 'wDayCareMan', [0])
            fixture(driver, symbols, 'wDayCareLady', [0])
            fixture(driver, symbols, 'wCurBox', [0])
            fixture(driver, symbols, 'sBoxCount', [0])
            for box in range(1, 15):
                fixture(driver, symbols, f'sBox{box}', [0])

        def packed_box(box, indexes, species=None, count=None):
            data = bytearray(22 + 20 * length)
            data[0] = len(indexes) if count is None else count
            data[1:1 + len(indexes)] = bytes(species or [1] * len(indexes))
            for slot, n in enumerate(indexes):
                data[22 + slot * length + mo:22 + slot * length + mo + 4] = bytes([n & 255, 0, 0, 0])
                data[22 + slot * length + pp:22 + slot * length + pp + 4] = bytes([(n >> 8) | 0xc0, 0, 0, 0])
            fixture(driver, symbols, f'sBox{box}', data)

        def check(name, expected):
            before = target / 'live-edge-before.sav'
            after = target / 'live-edge-after.sav'
            driver.command(f'battery {before}')
            table = ram(driver, symbols, 'wMoveIndexTable', 512)
            result = call(driver, symbols, 'MoveDiscovery_BootstrapOwned')
            driver.command(f'battery {after}')
            if read(driver, symbols)[:64] != move_bitmap(expected):
                raise AssertionError(f'Ownership boundary mismatch: {name}')
            if table != ram(driver, symbols, 'wMoveIndexTable', 512):
                raise AssertionError(f'Ownership scan allocated live identities: {name}')
            if before.read_bytes()[:32768] != after.read_bytes()[:32768]:
                raise AssertionError(f'Ownership scan modified SRAM: {name}')
            records.append(dict(case=name, expected=sorted(expected), time=result))

        reset()
        check('empty-ownership', [])
        for count, species in ((6, [1, 0xfd, 0, 255, 1, 1]), (255, [1] * 6)):
            reset()
            fixture(driver, symbols, 'wPartyCount', [count])
            fixture(driver, symbols, 'wPartySpecies', species)
            for slot in range(1, 7):
                fixture(driver, symbols, f'wPartyMon{slot}Moves', [ids[slot], 0, 0, 0])
            check('party-eggs-and-sentinels' if count == 6 else 'party-corrupt-count-bound',
                  [1, 5, 6] if count == 6 else list(range(1, 7)))
        for man, lady in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 2), (3, 3)):
            reset()
            for slot, name, occupied in ((1, 'wDayCareMan', man), (2, 'wDayCareLady', lady)):
                fixture(driver, symbols, name, [occupied])
                fixture(driver, symbols, f'wBreedMon{slot}Species', [1])
                fixture(driver, symbols, f'wBreedMon{slot}Moves', [ids[255 + slot], 0, 0, 0] if slot == 1 else [ids[333], 0, 0, 0])
            check(f'daycare-occupancy-{man}-{lady}',
                  ([256] if man & 1 else []) + ([333] if lady & 1 else []))
        reset()
        fixture(driver, symbols, 'wDayCareMan', [1])
        fixture(driver, symbols, 'wBreedMon1Species', [0xfd])
        fixture(driver, symbols, 'wBreedMon1Moves', [ids[333], 0, 0, 0])
        check('daycare-egg-skipped', [])
        reset()
        fixture(driver, symbols, 'sBoxCount', [1, 1, 255])
        fixture(driver, symbols, 'sBoxMon1Moves', [ids[20], 0, 0, 0])
        packed_box(1, [30])
        packed_box(2, [40])
        check('live-active-box-skips-stale-stored-copy', [20, 40])
        reset()
        fixture(driver, symbols, 'sBoxCount', [1, 0xfd, 255])
        fixture(driver, symbols, 'sBoxMon1Moves', [ids[333], 0, 0, 0])
        packed_box(2, [255, 256, 333, 334], [0xfd, 1, 1, 1])
        check('active-and-inactive-eggs-invalid-packed-index', [256, 333])
        reset()
        packed_box(2, list(range(100, 120)), count=255)
        check('inactive-corrupt-count-bound-and-pp-ups', list(range(100, 120)))
    finally:
        driver.close()
    return records


def migration_interruption_case(task):
    config, path = task
    symbols = config['symbols']
    driver = boot(config, path, path.with_suffix('.log'))
    try:
        expected = move_bitmap(range(1, 334))
        if read(driver, symbols)[:64] != expected:
            raise AssertionError(f'{path.name}: interrupted migration lost owned discoveries')
        repaired = path.with_suffix('.repaired.sav')
        driver.command(f'battery {repaired}')
        data = repaired.read_bytes()
        for prefix in ('s', 'sBackup'):
            if not core_valid(data, symbols, prefix) or decode_record(data, symbols, prefix) != dict(status='valid', bitmap=expected):
                raise AssertionError(f'{path.name}: migration did not repair both complete records')
    finally:
        driver.close()
    return dict(case=path.name, issues=[])


def interrupted_migration(config, target, jobs):
    symbols = config['symbols']
    source = target / 'legacy-full-current-1.sav'
    trace = target / 'full-migration-writes.csv'
    driver = boot(config, source, target / 'full-migration-writes.log', trace=trace)
    driver.close()
    data = bytearray(source.read_bytes())
    boundaries = {at for prefix in ('s', 'sBackup') for at in
                  range(address(symbols, prefix + 'MoveDiscovery'), address(symbols, prefix + 'MoveDiscovery') + 72)}
    boundaries.update(address(symbols, prefix + 'Checksum') + n
                      for prefix in ('s', 'sBackup') for n in range(2))
    tasks = []
    with trace.open() as file:
        for number, row in enumerate(csv.reader(file)):
            bank, location, value, _, _ = map(int, row)
            at = bank * 8192 + location - 0xa000
            data[at] = value
            if at in boundaries:
                path = target / f'full-migration-cut-{number:05}.sav'
                path.write_bytes(data)
                tasks.append((config, path))
    if len(tasks) != 150:
        raise AssertionError(f'Unexpected migration record/checksum write count: {len(tasks)}')
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        records = list(pool.map(migration_interruption_case, tasks))
    return dict(cases=len(records), results=records, issues=[])


def qualify(output, jobs=6, sources=False, migration=False, interruptions=False):
    target = output / 'acquisition-qualification'
    target.mkdir(exist_ok=True)
    symbols = read_symbols(output / f'{STEM}.sym')
    config = dict(rom=str(output / f'{STEM}.gbc'), symbols=symbols, core=str(core(output)))
    (target / 'empty.sav').write_bytes(seed_records((output / 'legacy-input.sav').read_bytes(), symbols, bytes(64)))
    if interruptions:
        result = interrupted_migration(config, target, jobs)
    elif migration:
        result = migration_tests(config, target, (output / 'legacy-input.sav').read_bytes(), jobs)
    elif sources:
        kinds = ('learn-empty', 'learn-replace', 'learn-decline', 'learn-battle', 'learn-transformed', 'learn-other-mon', 'tm-success', 'tm-known',
                 'tm-incompatible', 'tm-decline', 'tutor-success', 'tutor-known', 'tutor-incompatible',
                 'hm-success', 'hm-known', 'hm-incompatible', 'hm-decline',
                 'tutor-decline', 'level-success', 'level-decline', 'evolution-success', 'evolution-decline',
                 'ball-failed', 'ball-trainer', 'ball-full', 'ball-tutorial',
                 'gift-party', 'gift-box', 'gift-full', 'gift-pre-dex', 'gift-extended', 'gift-box-extended', 'egg-receipt', 'egg-full', 'egg-hatch', 'egg-not-ready',
                 'daycare-man', 'daycare-lady', 'daycare-full', 'contest-party', 'contest-box',
                 'daycare-service-man-success', 'daycare-service-lady-success',
                 'daycare-service-man-decline', 'daycare-service-lady-decline',
                 'daycare-service-man-poor', 'daycare-service-lady-poor',
                 'daycare-service-man-full', 'daycare-service-lady-full',
                 'contest-none', 'contest-full', 'dratini-special', 'dratini-normal', 'dratini-skip',
                 'trade-success', 'trade-decline', 'trade-wrong', 'contest-pending', 'enemy-generation')
        with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
            records = list(pool.map(source_case, [(config, kind, str(target)) for kind in kinds]))
        result = dict(cases=len(records), results=records, issues=[r for r in records if r['issues']])
    else:
        result = helpers(config, target)
    result.update(rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                  legacy_owned=owned_indices((output / 'legacy-input.sav').read_bytes(), symbols))
    report = 'acquisition-migration-interruptions.json' if interruptions else 'acquisition-migration.json' if migration else 'acquisition-sources.json' if sources else 'acquisition-qualification.json'
    (output / report).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('timings', 'results')}))
    if result['issues']:
        raise AssertionError(f'{len(result["issues"])} failing acquisition cases')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--sources', action='store_true')
    parser.add_argument('--migration', action='store_true')
    parser.add_argument('--interruptions', action='store_true')
    args = parser.parse_args()
    qualify(args.output.resolve(), args.jobs, args.sources, args.migration, args.interruptions)


if __name__ == '__main__':
    main()
