"""Independent paired Battle Tower data, rules, persistence and native-flow suite."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import traceback

from .assets import Repository, offset, sha256
from .cold_listing import ROOT, KEY, Driver
from .info_ui import BOOT
from .move_persistence import boot, call, core, input_call
from .move_acquisition import direct, fixture
from .shared_menu_fixtures import make_fixture
from tools.pokedex_info_assets import constants

DEFAULT = ROOT / 'build/dex-cleanup-20261014/battle-tower-final'
SOURCES = dict(baseline=ROOT / 'build/dex-cleanup-20261014/runtime-regression/baseline/candidate',
               candidate=ROOT / 'build/dex-cleanup-20261014/candidate')
BATTERY = ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'
PR_MERGE = '8d19d3bb6b79efbd7e5ee9f174ee8279d45f28c9'


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def get(driver, symbols, name, count=1):
    bank, at = symbols[name]
    return bytes.fromhex(driver.command(f'read {bank} {at} {count}')['bytes'])


def byte(driver, symbols, name):
    return get(driver, symbols, name)[0]


def check(row, condition, reason):
    if not condition:
        row['issues'].append(reason)


def configs(output):
    return json.loads((output / 'config.json').read_text())['variants']


def native(cfg, folder):
    symbols = {key: tuple(value) for key, value in cfg['symbols'].items()}
    cfg = dict(cfg, symbols=symbols)
    driver = boot(cfg, Path(cfg['battery']), folder / 'native.log')
    for at in (symbols['hRandomAdd'][1], symbols['hRandomSub'][1]):
        driver.command(f'hram {at} 0')
    fixture(driver, symbols, 'wPartyCount', [3])
    live = [direct(driver, symbols, 'GetPokemonIDFromIndex', hl=n)['af'] >> 8 for n in (1, 4, 7)]
    fixture(driver, symbols, 'wPartySpecies', live + [255])
    for slot, species in enumerate(live, 1):
        for suffix, value in (('Species', [species]), ('Item', [0]), ('Level', [10]),
                              ('Moves', [0] * 4), ('PP', [0] * 4), ('Status', [0])):
            fixture(driver, symbols, f'wPartyMon{slot}{suffix}', value)
    driver.command(f'io 65392 {symbols["wPartyMon1"][0]}')
    checkpoint = folder / 'prepared.s0'
    assert not driver.command(f'save {checkpoint}').get('error')
    return cfg, driver, checkpoint, live


def prepare(output, sources, battery):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh independent directory under build/')
    output.mkdir(parents=True)
    protected = {str(battery): sha256(battery.read_bytes())}
    variants = {}
    for variant, source in sources.items():
        folder = output / variant
        folder.mkdir()
        for ext in ('gbc', 'sym', 'map'):
            protected[str(source / f'pokecrystal.{ext}')] = sha256((source / f'pokecrystal.{ext}').read_bytes())
        repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
        private = folder / 'private.sav'
        make_fixture(repo, battery, private, ('BATTLE_TOWER_1F', 7, 7))
        payload = bytearray(private.read_bytes())
        for name, values in (('sBattleTowerChallengeState', [0]), ('sNrOfBeatenBattleTowerTrainers', [0]),
                             ('sBTTrainers', [255] * 7), ('sBattleTowerSaveFileFlags', [2]),
                             ('sBTMonOfTrainers', [0] * 12)):
            bank, pc = repo.symbols[name]
            at = bank * 8192 + pc - 0xa000
            payload[at:at + len(values)] = bytes(values)
        private.write_bytes(payload)
        variants[variant] = dict(root=str(source), rom=str(repo.rom_path), sym=str(source / 'pokecrystal.sym'),
            symbols=repo.symbols, core=str(core(source, stem='pokecrystal', target_root=folder)),
            battery=str(private), rom_sha256=sha256(repo.rom))
    write(output / 'config.json', dict(variants=variants, protected=protected,
          fixture_kind='Copied battery, declared map/Tower fields; no timing or ROM patching',
          pr_merge=PR_MERGE))
    with (output / 'pr16.diff').open('w') as diff:
        subprocess.run(['git', 'diff', PR_MERGE + '^1', PR_MERGE], cwd=ROOT, stdout=diff, check=True)


def catalog(repo):
    source = (repo.root / 'data/battle_tower/parties.asm').read_text()
    entries = re.findall(r'^\s*dw (\w+)\s*\n\s*db (\w+)\s*\n\s*dw ([A-Z_0-9, ]+)\s*$', source, re.M)
    pokemon = constants(repo.root / 'constants/pokemon_constants.asm')
    moves = constants(repo.root / 'constants/move_constants.asm')
    items = constants(repo.root / 'constants/item_constants.asm')
    result = [(pokemon[name], items[item], tuple(0 if move.strip() == '0' else moves[move.strip()] for move in attacks.split(',')))
              for name, item, attacks in entries]
    if len(result) != 210 or any(len(row[2]) != 4 for row in result):
        raise AssertionError('Catalog changed: update the independently parsed source oracle')
    return result


def data(cfg, folder):
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    expected = catalog(repo)
    stride = repo.symbols['wBT_OTMon2'][1] - repo.symbols['wBT_OTMon1'][1] + 5
    start = offset(repo.symbols['BattleTowerMons'])
    level_offset = repo.symbols['wBT_OTMon1Level'][1] - repo.symbols['wBT_OTMon1'][1] + 5
    records = []
    for index, (species, item, moves) in enumerate(expected):
        raw = repo.rom[start + index * stride:start + (index + 1) * stride]
        actual = (int.from_bytes(raw[:2], 'little'), raw[2],
                  tuple(int.from_bytes(raw[n:n + 2], 'little') for n in range(3, 11, 2)))
        row = dict(case=f'mon-{index}', level_group=index // 21 + 1, issues=[])
        check(row, actual == (species, item, moves), 'Linked species/item/moves differ from source')
        check(row, raw[level_offset] == (index // 21 + 1) * 10, 'Wrong catalog level')
        check(row, 1 <= species <= 373 and any(moves) and all(0 <= move <= 333 for move in moves), 'Invalid permanent ID')
        records.append(row)
    table = offset(repo.symbols['BattleTowerAction.dw'])
    for index in range(32):
        target = int.from_bytes(repo.rom[table + 2 * index:table + 2 * index + 2], 'little')
        records.append(dict(case=f'action-pointer-{index}', issues=[] if 0x4000 <= target < 0x8000 else ['Invalid action target']))
    return records


def rules(cfg, folder):
    cfg, driver, checkpoint, live = native(cfg, folder)
    symbols = cfg['symbols']
    rows = []
    try:
        for count in range(7):
            fixture(driver, symbols, 'wPartyCount', [count])
            result = call(driver, symbols, 'CheckBTRule_PartyCountEq3')
            rows.append(dict(case=f'party-count-{count}', issues=[] if bool(result['af'] & 16) == (count != 3) else ['Wrong count restriction']))
        fixture(driver, symbols, 'wPartyCount', [3])
        for pair in (None, (0, 1), (0, 2), (1, 2)):
            species = list(live)
            if pair:
                species[pair[1]] = species[pair[0]]
            fixture(driver, symbols, 'wPartySpecies', species + [255])
            for slot, value in enumerate(species, 1):
                fixture(driver, symbols, f'wPartyMon{slot}Species', [value])
            result = call(driver, symbols, 'CheckBTRule_PartySpeciesAreUnique')
            rows.append(dict(case=f'species-duplicate-{pair}', issues=[] if bool(result['af'] & 16) == bool(pair) else ['Wrong species restriction']))
        for item in range(256):
            for pair in ((0, 1), (0, 2), (1, 2)):
                items = [0, 0, 0]
                items[pair[0]] = items[pair[1]] = item
                for slot, value in enumerate(items, 1):
                    fixture(driver, symbols, f'wPartyMon{slot}Item', [value])
                result = call(driver, symbols, 'CheckBTRule_PartyItemsAreUnique')
                rows.append(dict(case=f'item-{item}-{pair}', issues=[] if bool(result['af'] & 16) == bool(item) else ['Wrong held-item duplicate restriction']))
        for count in range(1, 7):
            for egg in range(-1, count):
                species = [live[n % 3] for n in range(count)]
                if egg >= 0:
                    species[egg] = 253
                fixture(driver, symbols, 'wPartyCount', [count])
                fixture(driver, symbols, 'wPartySpecies', species + [255])
                result = call(driver, symbols, 'CheckBTRule_HasPartyAnEgg')
                rows.append(dict(case=f'egg-{count}-{egg}', issues=[] if bool(result['af'] & 16) == (egg >= 0) else ['Wrong egg restriction']))
        driver.command(f'load {checkpoint}')
        for group in range(1, 11):
            for slot in range(1, 4):
                for edge, level in zip(('minimum', 'below', 'at', 'above', 'maximum'),
                                       (1, group * 10 - 1, group * 10, group * 10 + 1, 100)):
                    fixture(driver, symbols, 'wcd4f', [group])
                    for n in range(1, 4):
                        fixture(driver, symbols, f'wPartyMon{n}Level', [1])
                    fixture(driver, symbols, f'wPartyMon{slot}Level', [level])
                    for bank in range(1, 8):
                        driver.command(f'io 65392 {bank}')
                        result = call(driver, symbols, 'BattleTower_LevelCheck')
                        row = dict(case=f'level-{group}-{slot}-{edge}-{level}-{bank}', issues=[])
                        check(row, bool(result['af'] & 16) == (level > group * 10), 'Wrong level boundary')
                        check(row, result['svbk'] & 7 == bank, 'Level check did not restore WRAM bank')
                        rows.append(row)
        driver.command(f'load {checkpoint}')
        ids = constants(Path(cfg['root']) / 'constants/pokemon_constants.asm')
        for name in ('BULBASAUR', 'MEWTWO', 'MEW', 'LUGIA', 'HO_OH', 'CELEBI', 'TREECKO'):
            species = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=ids[name])['af'] >> 8
            fixture(driver, symbols, 'wPartySpecies', [species, live[1], live[2], 255])
            fixture(driver, symbols, 'wPartyMon1Species', [species])
            for group in range(1, 11):
                for level in (1, 69, 70, 100):
                    fixture(driver, symbols, 'wcd4f', [group])
                    fixture(driver, symbols, 'wPartyMon1Level', [level])
                    driver.command(f'io 65392 3')
                    result = call(driver, symbols, 'BattleTower_UbersCheck')
                    banned = name in ('MEWTWO', 'MEW', 'LUGIA', 'HO_OH', 'CELEBI') and group < 7 and level < 70
                    row = dict(case=f'uber-{name}-{group}-{level}', issues=[])
                    check(row, bool(result['af'] & 16) == banned, 'Wrong legendary restriction')
                    check(row, result['svbk'] & 7 == 3, 'Legendary check did not restore WRAM bank')
                    rows.append(row)
    finally:
        driver.close()
    return rows


def actions(cfg, folder):
    cfg, driver, checkpoint, _ = native(cfg, folder)
    symbols, rows = cfg['symbols'], []
    try:
        for value in range(256):
            fixture(driver, symbols, 'sBattleTowerChallengeState', [value])
            fixture(driver, symbols, 'wScriptVar', [2])
            call(driver, symbols, 'BattleTowerAction')
            rows.append(dict(case=f'get-state-{value}', issues=[] if byte(driver, symbols, 'wScriptVar') == value else ['Challenge state getter changed']))
        for action, expected in ((3, 1), (4, 0), (28, 3), (29, 4)):
            for old in range(5):
                fixture(driver, symbols, 'sBattleTowerChallengeState', [old])
                fixture(driver, symbols, 'wScriptVar', [action])
                call(driver, symbols, 'BattleTowerAction')
                rows.append(dict(case=f'set-state-{action}-{old}', issues=[] if byte(driver, symbols, 'sBattleTowerChallengeState') == expected else ['Wrong challenge state transition']))
        for flags in range(256):
            fixture(driver, symbols, 'sBattleTowerSaveFileFlags', [flags])
            fixture(driver, symbols, 'wScriptVar', [1])
            call(driver, symbols, 'BattleTowerAction')
            rows.append(dict(case=f'explanation-{flags}', issues=[] if byte(driver, symbols, 'sBattleTowerSaveFileFlags') == flags | 2 else ['Explanation setter changed unrelated bits']))
        for group in range(1, 11):
            fixture(driver, symbols, 'wBTChoiceOfLvlGroup', [group])
            call(driver, symbols, 'SaveBattleTowerLevelGroup')
            fixture(driver, symbols, 'wBTChoiceOfLvlGroup', [0])
            call(driver, symbols, 'LoadBattleTowerLevelGroup')
            rows.append(dict(case=f'level-save-{group}', issues=[] if byte(driver, symbols, 'wBTChoiceOfLvlGroup') == group else ['Saved level group did not reload']))
        fixture(driver, symbols, 'sBTTrainers', [7] * 7)
        fixture(driver, symbols, 'sNrOfBeatenBattleTowerTrainers', [7])
        call(driver, symbols, 'ResetBattleTowerTrainersSRAM')
        rows.append(dict(case='reset-streak', issues=[] if get(driver, symbols, 'sBTTrainers', 7) == bytes([255]) * 7 and not byte(driver, symbols, 'sNrOfBeatenBattleTowerTrainers') else ['Streak reset failed']))
        items = constants(Path(cfg['root']) / 'constants/item_constants.asm')
        for reward in range(items['HP_UP'], items['HP_UP'] + 6):
            if reward == items['LUCKY_PUNCH']:
                continue
            for count, same, quantity in ((0, False, 0), (39, False, 0), (40, False, 0), (40, True, 94), (40, True, 95), (40, True, 99)):
                fixture(driver, symbols, 'sBattleTowerReward', [reward])
                fixture(driver, symbols, 'wNumItems', [count])
                inventory = bytearray([items['POTION'], 99] * 40 + [255])
                if same:
                    inventory[:2] = bytes((reward, quantity))
                fixture(driver, symbols, 'wItems', inventory)
                call(driver, symbols, 'BattleTower_GiveReward')
                expected = reward if count < 40 or same and quantity < 95 else items['POTION']
                row = dict(case=f'reward-{reward}-{count}-{same}-{quantity}', issues=[])
                check(row, byte(driver, symbols, 'wScriptVar') == expected, 'Wrong prize capacity decision')
                check(row, get(driver, symbols, 'wItems', 81) == inventory, 'Prize query modified inventory')
                rows.append(row)
        driver.command(f'load {checkpoint}')
        call(driver, symbols, 'SaveGameData')
        for action in range(32):
            driver.command(f'load {checkpoint}')
            fixture(driver, symbols, 's5_a800', [0])
            fixture(driver, symbols, 'wScriptVar', [action])
            result = call(driver, symbols, 'BattleTowerAction')
            rows.append(dict(case=f'action-smoke-{action}', issues=[] if result['hit'] else ['Action did not return']))
        call(driver, symbols, 'SaveGameData')
        for state in range(5):
            fixture(driver, symbols, 'sBattleTowerChallengeState', [state])
            path = folder / f'cold-state-{state}.sav'
            driver.command(f'battery {path}')
            cold = boot(cfg, path, folder / f'cold-state-{state}.log')
            try:
                expected = 3 if state == 4 else state
                rows.append(dict(case=f'cold-state-{state}', issues=[] if byte(cold, symbols, 'sBattleTowerChallengeState') == expected else ['Cold reload changed challenge state']))
            finally:
                cold.close()
    finally:
        driver.close()
    return rows


def teams(cfg, folder):
    cfg, driver, checkpoint, _ = native(cfg, folder)
    symbols, rows = cfg['symbols'], []
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    pool = catalog(repo)
    try:
        discoveries = get(driver, symbols, 'wMoveDiscoverySeen', 64)
        for group in range(1, 11):
            for seed in (1, 73, 211):
                driver.command(f'load {checkpoint}')
                fixture(driver, symbols, 'wBTChoiceOfLvlGroup', [group])
                fixture(driver, symbols, 'sBTMonOfTrainers', bytes(12))
                call(driver, symbols, 'ResetBattleTowerTrainersSRAM')
                driver.command(f'hram {symbols["hRandomAdd"][1]} {seed}')
                driver.command(f'hram {symbols["hRandomSub"][1]} {seed ^ 255}')
                prior, trainers = [], []
                for position in range(7):
                    loaded = call(driver, symbols, 'LoadOpponentTrainerAndPokemon')
                    row = dict(case=f'team-{group}-{seed}-{position}', issues=[], mons=[])
                    check(row, loaded['svbk'] & 7 == 1, 'Trainer loader did not restore WRAM bank')
                    trainer = get(driver, symbols, 'sBTTrainers', 7)[position]
                    check(row, trainer < 70 and trainer not in trainers, 'Trainer repeats within the streak')
                    trainers.append(trainer)
                    chosen, held = [], []
                    for slot in range(1, 4):
                        mon = 'wBT_OTMon' + str(slot)
                        species = direct(driver, symbols, 'GetPokemonIndexFromID', af=byte(driver, symbols, mon) << 8)['hl']
                        attacks = tuple(direct(driver, symbols, 'GetMoveIndexFromID', af=value << 8)['hl'] if value else 0
                                        for value in get(driver, symbols, mon + 'Moves', 4))
                        item, level = byte(driver, symbols, mon + 'Item'), byte(driver, symbols, mon + 'Level')
                        check(row, (species, item, attacks) in pool[(group - 1) * 21:group * 21], 'Loaded mon differs from declared level pool')
                        check(row, level == group * 10, 'Loaded mon has wrong level')
                        check(row, species not in chosen and species not in prior[-6:], 'Current/recent team species repeat')
                        check(row, item not in held, 'Held items repeat within opponent team')
                        chosen.append(species)
                        held.append(item)
                        row['mons'].append(dict(species=species, moves=attacks, item=item, level=level))
                    history = get(driver, symbols, 'sBTMonOfTrainers', 12)
                    check(row, history[:6] == b''.join(value.to_bytes(2, 'little') for value in chosen), 'Newest opponent history is wrong')
                    check(row, history[6:] == b''.join(value.to_bytes(2, 'little') for value in prior[-3:]).ljust(6, b'\0'), 'Previous opponent history is wrong')
                    call(driver, symbols, 'CopyBTTrainer_FromBT_OT_TowBT_OTTemp')
                    check(row, byte(driver, symbols, 'sNrOfBeatenBattleTowerTrainers') == position + 1, 'Streak progress counter did not advance')
                    check(row, byte(driver, symbols, 'sBattleTowerChallengeState') == 2, 'Challenge was not marked in progress')
                    check(row, get(driver, symbols, 'wMoveDiscoverySeen', 64) == discoveries, 'Enemy generation discovered unpresented moves')
                    prior += chosen
                    rows.append(row)
    finally:
        driver.close()
    return rows


def reward_routing(cfg, folder):
    cfg, driver, checkpoint, _ = native(cfg, folder)
    symbols, rows = cfg['symbols'], []
    items = constants(Path(cfg['root']) / 'constants/item_constants.asm')
    try:
        for reward in range(items['HP_UP'], items['HP_UP'] + 6):
            if reward == items['LUCKY_PUNCH']:
                continue
            for name, item_count, medicine_quantity in (('items-full-medicine-free', 40, 0),
                                                        ('medicine-94', 0, 94), ('medicine-95', 0, 95)):
                driver.command(f'load {checkpoint}')
                fixture(driver, symbols, 'sBattleTowerReward', [reward])
                fixture(driver, symbols, 'wNumItems', [item_count])
                fixture(driver, symbols, 'wItems', bytes((items['NUGGET'], 99)) * item_count + b'\xff')
                fixture(driver, symbols, 'wNumMedicine', [40 if medicine_quantity else 0])
                medicine = bytes((items['POTION'], 99)) * 39 + bytes((reward, medicine_quantity, 255)) if medicine_quantity else b'\xff'
                fixture(driver, symbols, 'wMedicine', medicine)
                call(driver, symbols, 'BattleTower_GiveReward')
                actual = byte(driver, symbols, 'wScriptVar')
                expected = reward if medicine_quantity <= 94 else items['POTION']
                row = dict(case=f'prize-routing-{reward}-{name}', issues=[], expected=expected, actual=actual,
                           fixture='Declared full-pocket boundary with legal multiple stacks; 94/95 vitamin stack is the only remaining capacity')
                check(row, actual == expected, 'Prize capacity checks Items instead of Medicine')
                rows.append(row)
    finally:
        driver.close()
    return rows


def fighters(driver, symbols, species, level=10):
    size = symbols['wPartyMon2'][1] - symbols['wPartyMon1'][1]
    template = get(driver, symbols, 'wPartyMon1', size)
    for slot, live in enumerate(species, 1):
        fixture(driver, symbols, f'wPartyMon{slot}', template)
        for suffix, value in (('Species', [live]), ('Item', [0]), ('Level', [level]), ('Status', [0]),
                              ('Moves', [0] * 4), ('PP', [0] * 4),
                              ('HP', (999).to_bytes(2, 'big')), ('MaxHP', (999).to_bytes(2, 'big')),
                              ('Stats', (500).to_bytes(2, 'big') * 5)):
            fixture(driver, symbols, f'wPartyMon{slot}{suffix}', value)
        fixture(driver, symbols, 'wNamedObjectIndex', [live])
        call(driver, symbols, 'GetPokemonName')
        fixture(driver, symbols, f'wPartyMon{slot}Nickname', get(driver, symbols, 'wStringBuffer1', 11))


def regular_attacks(driver, symbols, source):
    attacks = constants(Path(source) / 'constants/move_constants.asm')
    attack = direct(driver, symbols, 'GetMoveIDFromIndex', hl=attacks['AERIAL_ACE'])['af'] >> 8
    for slot in range(1, 4):
        fixture(driver, symbols, f'wPartyMon{slot}Moves', [attack, 0, 0, 0])
        fixture(driver, symbols, f'wPartyMon{slot}PP', [20, 0, 0, 0])


def map_id(source, name):
    group = number = 0
    for line in (Path(source) / 'constants/map_constants.asm').read_text().splitlines():
        if re.match(r'^\s*newgroup\s+\w+', line):
            group, number = group + 1, 0
        match = re.match(r'^\s*map_const\s+(\w+),', line)
        if match:
            number += 1
            if match[1] == name:
                return group, number
    raise ValueError('Unknown map: ' + name)


def interactive_key(driver, symbols, step):
    if not step % 2:
        return 0
    if (not byte(driver, symbols, 'wBattleEnded') and
            byte(driver, symbols, 'wPartyMenuActionText') == 2 and
            not any(get(driver, symbols, 'wBattleMonHP', 2))):
        alive = [slot for slot in range(1, 4) if any(get(driver, symbols, f'wPartyMon{slot}HP', 2))]
        cursor = byte(driver, symbols, 'wMenuCursorY')
        if alive and 1 <= cursor <= 4 and cursor != alive[0]:
            return KEY['down' if cursor < alive[0] else 'up']
    return KEY['a']


def invoke(driver, symbols, label, frames=10000, diagnostic=None):
    bank, pc = symbols[label]
    owner = driver.command('peek')
    driver.command(f'begin {bank} {pc} 0 0')
    total_frames = total_ticks = 0
    for index in range(frames // 16):
        result = driver.command(f'resume 16 {interactive_key(driver, symbols, index)}')
        total_frames += result['frames']
        total_ticks += result['elapsed']
        if result['hit']:
            result.update(frames=total_frames, elapsed=total_ticks)
            return result
    if diagnostic:
        write(diagnostic.with_suffix('.json'), dict(label=label, last=result, owner=owner,
            elapsed_frames=total_frames, elapsed_ticks=total_ticks,
            fields={name: list(get(driver, symbols, name, size)) for name, size in (
                ('wBattleMode', 1), ('wBattleResult', 1), ('wBattleMonHP', 2), ('wEnemyMonHP', 2),
                ('wBattleMonMoves', 4), ('wBattleMonPP', 4), ('wMenuCursorY', 1), ('wPartyCount', 1),
                ('wBattleTowerBattleEnded', 1), ('wInBattleTowerBattle', 1))}))
        driver.command(f'save {diagnostic}.s0')
        driver.command(f'image {diagnostic}.ppm')
        driver.command(f'cpulog {diagnostic}.cpu.csv 1000')
        driver.command('resume 1 0')
    raise AssertionError('Native interactive owner did not return: ' + label)


def reach(driver, symbols, label, key='a', frames=2000):
    bank, pc = symbols[label]
    for index in range(frames // 8):
        result = driver.command(f'until {bank} {pc} 8 {KEY.get(key, 0) if index % 2 else 0}')
        if result['hit']:
            return result
    raise AssertionError('Normal buttons did not reach ' + label)


def tap(driver, key, held=4):
    driver.command(f'run {held} {KEY[key]}')
    driver.command('run 4 0')


def ui(cfg, folder):
    cfg, seed, _, species = native(cfg, folder)
    symbols = cfg['symbols']
    try:
        fighters(seed, symbols, species)
        regular_attacks(seed, symbols, cfg['root'])
        call(seed, symbols, 'LoadMapObjects')
        call(seed, symbols, 'RefreshMapSprites')
        fixture(seed, symbols, 'sBattleTowerChallengeState', [0])
        fixture(seed, symbols, 'sBattleTowerSaveFileFlags', [2])
        call(seed, symbols, 'SaveGameData')
        battery = folder / 'menus.sav'
        seed.command(f'battery {battery}')
    finally:
        seed.close()
    rows = []
    for kind in ('cancel-b', 'cancel-item', 'explanation', 'save-decline', 'level-cancel-b', 'level-cancel-item', 'challenge-entry', 'full-streak', 'loss-return', 'prize-bag-full', 'prize-medicine-full'):
        row = dict(case=kind, issues=[], normal_buttons=True)
        driver = boot(cfg, battery, folder / f'{kind}.log')
        try:
            if kind == 'loss-return':
                for slot in range(1, 4):
                    for suffix, payload in (('HP', b'\0\x01'), ('MaxHP', b'\0\x01'), ('Stats', b'\0\x01' * 5)):
                        fixture(driver, symbols, f'wPartyMon{slot}{suffix}', payload)
                call(driver, symbols, 'SaveGameData')
            if kind in ('prize-bag-full', 'prize-medicine-full'):
                items = constants(Path(cfg['root']) / 'constants/item_constants.asm')
                fixture(driver, symbols, 'sBattleTowerChallengeState', [3])
                fixture(driver, symbols, 'sBattleTowerReward', [items['HP_UP']])
                pocket = 'Items' if kind == 'prize-bag-full' else 'Medicine'
                fixture(driver, symbols, 'wNum' + pocket, [40])
                bag = (bytes((items['NUGGET'], 99)) * 40 + b'\xff'
                       if pocket == 'Items' else bytes((items['POTION'], 99)) * 39 + bytes((items['HP_UP'], 95, 255)))
                fixture(driver, symbols, 'w' + pocket, bag)
                tap(driver, 'up')
                for step in range(128):
                    driver.command(f'run 8 {KEY["a"] if step % 2 else 0}')
                    if step > 8 and not byte(driver, symbols, 'wScriptRunning') and not byte(driver, symbols, 'hInMenu'):
                        break
                check(row, byte(driver, symbols, 'sBattleTowerChallengeState') == 3, 'Unclaimed prize was lost')
                check(row, get(driver, symbols, 'w' + pocket, len(bag)) == bag, 'Full bag was overwritten')
                row['actual_state'] = byte(driver, symbols, 'sBattleTowerChallengeState')
                row['actual_prize'] = byte(driver, symbols, 'sBattleTowerReward')
                if kind == 'prize-bag-full':
                    row['capacity_policy_warning'] = 'Items fullness rejects a vitamin even though Medicine can hold it'
                driver.command(f'image {folder}/{kind}-return.ppm')
                rows.append(row)
                continue
            tap(driver, 'up')
            reach(driver, symbols, 'Menu_ChallengeExplanationCancel')
            reach(driver, symbols, 'StaticMenuJoypad', key=None)
            driver.command('run 8 0')
            driver.command(f'image {folder}/{kind}-challenge-menu.ppm')
            if kind == 'cancel-b':
                tap(driver, 'b')
            elif kind == 'cancel-item':
                tap(driver, 'down')
                tap(driver, 'down')
                tap(driver, 'a')
            elif kind == 'explanation':
                tap(driver, 'down')
                tap(driver, 'a')
                reach(driver, symbols, 'Menu_ChallengeExplanationCancel')
                reach(driver, symbols, 'StaticMenuJoypad', key=None)
                tap(driver, 'b')
            else:
                tap(driver, 'a')
                reach(driver, symbols, 'YesNoBox')
                reach(driver, symbols, 'StaticMenuJoypad', key=None)
                driver.command('run 8 0')
                if kind == 'save-decline':
                    tap(driver, 'down')
                    tap(driver, 'a')
                    reach(driver, symbols, 'Menu_ChallengeExplanationCancel')
                    reach(driver, symbols, 'StaticMenuJoypad', key=None)
                    tap(driver, 'b')
                else:
                    tap(driver, 'a')
                    reach(driver, symbols, 'BattleTowerRoomMenu_UpdatePickLevelMenu')
                    driver.command('run 8 0')
                    driver.command(f'image {folder}/{kind}-levels.ppm')
                    if kind == 'level-cancel-b':
                        tap(driver, 'b')
                    elif kind == 'level-cancel-item':
                        tap(driver, 'down')
                        tap(driver, 'a')
                    else:
                        tap(driver, 'a')
                        reach(driver, symbols, 'RunBattleTowerTrainer')
                        row['entered_actual_battle_script'] = True
                        driver.command(f'image {folder}/{kind}-battle-entry.ppm')
                        if kind == 'challenge-entry':
                            rows.append(row)
                            continue
                        elapsed = 0
                        for step in range(48000 // 16):
                            result = driver.command(f'run 16 {interactive_key(driver, symbols, step)}')
                            elapsed += result['frames']
                            if byte(driver, symbols, 'sBattleTowerChallengeState') == (0 if kind == 'loss-return' else 4) and not byte(driver, symbols, 'wScriptRunning'):
                                break
                        else:
                            raise AssertionError('Normal-button seven-battle streak did not finish')
                        row['elapsed_frames'] = elapsed
                        if kind == 'loss-return':
                            check(row, byte(driver, symbols, 'wBattleResult') == 1, 'Controlled loss did not use loss return path')
                            check(row, driver.command('peek')['double_speed'] == 1, 'Loss return did not restore overworld clock')
                            rows.append(row)
                            driver.command(f'image {folder}/{kind}-return.ppm')
                            continue
                        check(row, byte(driver, symbols, 'sNrOfBeatenBattleTowerTrainers') == 7, 'Seven-battle progress not retained')
                        reward = byte(driver, symbols, 'sBattleTowerReward')
                        bag = get(driver, symbols, 'wMedicine', 2 * byte(driver, symbols, 'wNumMedicine'))
                        row['medicine_after_prize'] = list(bag)
                        row['prize'] = reward
                        check(row, any(bag[n:n + 2] == bytes((reward, 5)) for n in range(0, len(bag), 2)), 'Five-item prize not granted through map script')
                        check(row, (byte(driver, symbols, 'wMapGroup'), byte(driver, symbols, 'wMapNumber')) == map_id(cfg['root'], 'BATTLE_TOWER_1F'), 'Reward did not return to lobby')
                        call(driver, symbols, 'SaveGameData')
                        check(row, not byte(driver, symbols, 'sBattleTowerChallengeState'), 'Prize not finalized by normal save')
                        rows.append(row)
                        driver.command(f'image {folder}/{kind}-prize.ppm')
                        continue
                    reach(driver, symbols, 'BattleTowerRoomMenu2_UpdateYesNoMenu')
                    tap(driver, 'a')
                    reach(driver, symbols, 'Menu_ChallengeExplanationCancel')
                    reach(driver, symbols, 'StaticMenuJoypad', key=None)
                    tap(driver, 'b')
            for _ in range(64):
                tap(driver, 'a')
                if not byte(driver, symbols, 'wScriptRunning') and not byte(driver, symbols, 'hInMenu'):
                    break
            check(row, not byte(driver, symbols, 'wScriptRunning'), 'Tower script did not return to overworld')
            check(row, not byte(driver, symbols, 'hInMenu'), 'Menu ownership was not restored')
            check(row, driver.command('peek')['double_speed'] == 1, 'Overworld clock not restored')
            driver.command(f'image {folder}/{kind}-return.ppm')
        except Exception as error:
            row['issues'].append(str(error))
            row['last'] = driver.command('peek')
            driver.command(f'image {folder}/{kind}-failure.ppm')
            driver.command(f'save {folder}/{kind}-failure.s0')
        finally:
            driver.close()
        rows.append(row)
    return rows


def battles(cfg, folder, regular_moves=False):
    cfg, driver, checkpoint, species = native(cfg, folder)
    symbols, rows = cfg['symbols'], []
    try:
        for group in range(1, 11):
            for position in range(7):
                # Complete map reload/continuation is tested by ui(). Direct
                # owner cases start fresh, never on a preceding battle's VRAM.
                driver.command(f'load {checkpoint}')
                fighters(driver, symbols, species, level=group * 10)
                if regular_moves:
                    regular_attacks(driver, symbols, cfg['root'])
                call(driver, symbols, 'SaveGameData')
                fixture(driver, symbols, 'wBTChoiceOfLvlGroup', [group])
                fixture(driver, symbols, 'sBTMonOfTrainers', bytes(12))
                call(driver, symbols, 'ResetBattleTowerTrainersSRAM')
                for prior in range(position + 1):
                    call(driver, symbols, 'LoadOpponentTrainerAndPokemon')
                    if prior < position:
                        call(driver, symbols, 'CopyBTTrainer_FromBT_OT_TowBT_OTTemp')
                options = byte(driver, symbols, 'wOptions')
                original_flag = byte(driver, symbols, 'wInBattleTowerBattle')
                try:
                    ended = invoke(driver, symbols, 'BattleTowerBattle', frames=60000,
                                   diagnostic=folder / f'timeout-{group}-{position}')
                except AssertionError as error:
                    rows.append(dict(case=f'battle-{group}-{position}', issues=[str(error)], timeout=True))
                    continue
                row = dict(case=f'battle-{group}-{position}', issues=[], elapsed_frames=ended['frames'],
                           fixture='Legal distinct species, no held items, selected-group level, declared HP 999 and stats 500; native ' + ('Aerial Ace' if regular_moves else 'Struggle') + '/AI turn resolution')
                battle_contract(row, driver, symbols, ended, options, original_flag, position)
                driver.command(f'image {folder}/group-{group}-battle-{position}.ppm')
                rows.append(row)
            write(folder / 'progress.json', dict(cases=len(rows), results=rows))
            print(json.dumps(dict(level_group=group, native_battles=7, issues=sum(bool(row['issues']) for row in rows))), flush=True)
    finally:
        driver.close()
    return rows


def battle_contract(row, driver, symbols, ended, options, original_flag, position):
    row['battle_result'] = byte(driver, symbols, 'wBattleResult')
    check(row, row['battle_result'] in (0, 1), 'Invalid native win/loss result')
    check(row, byte(driver, symbols, 'wOptions') == options, 'Tower changed player battle options')
    check(row, byte(driver, symbols, 'wInBattleTowerBattle') == original_flag, 'Tower battle flag not restored')
    check(row, byte(driver, symbols, 'wBattleTowerBattleEnded') == 1, 'Tower battle owner did not finish')
    check(row, byte(driver, symbols, 'sNrOfBeatenBattleTowerTrainers') == position + 1, 'Battle progress counter is wrong')
    check(row, ended['double_speed'] == 0, 'Tower battle did not retain normal speed until map setup')


def recover_timeouts(output):
    """Continue active native calls with a second bounded, recorded budget."""
    from .info_ui import BOOT
    for variant, cfg in configs(output).items():
        symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
        for phase in ('battles', 'battles_moves'):
            folder = output / variant / phase
            result = json.loads((folder / 'summary.json').read_text())
            if not any(row.get('timeout') for row in result['results']):
                continue
            saved = folder / 'summary-before-recovery.json'
            if saved.exists():
                raise ValueError('Recovery already attempted; preserve the fixed two-budget limit')
            shutil.copy2(folder / 'summary.json', saved)
            for row in result['results']:
                if not row.get('timeout'):
                    continue
                _, group, position = row['case'].split('-')
                prefix = folder / f'timeout-{group}-{position}'
                diagnostic = json.loads(prefix.with_suffix('.json').read_text())
                owner = diagnostic['owner']
                driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], folder / f'recovery-{group}-{position}.log')
                try:
                    driver.command(f'load {folder}/prepared.s0')
                    options = byte(driver, symbols, 'wOptions')
                    original_flag = byte(driver, symbols, 'wInBattleTowerBattle')
                    driver.command(f'load {prefix}.s0')
                    elapsed = 0
                    for step in range(60000 // 7):
                        returned = driver.command(f'until {owner["bank"]} {owner["pc"]} 7 {interactive_key(driver, symbols, step)}')
                        elapsed += returned['frames']
                        if returned['hit'] and returned['sp'] == owner['sp']:
                            break
                    else:
                        row['recovery_failed'] = True
                        row['recovery_frames'] = elapsed
                        continue
                    row.update(issues=[], timeout=False, recovered=True, initial_timeout_frames=diagnostic['elapsed_frames'],
                               recovery_frames=elapsed, elapsed_frames=diagnostic['elapsed_frames'] + elapsed)
                    battle_contract(row, driver, symbols, returned, options, original_flag, int(position))
                    driver.command(f'image {folder}/recovered-{group}-{position}.ppm')
                    print(json.dumps(dict(variant=variant, phase=phase, case=row['case'], recovered=True,
                        total_frames=row['elapsed_frames'], issues=row['issues'])), flush=True)
                finally:
                    driver.close()
            result['failures'] = sum(bool(row['issues']) for row in result['results'])
            write(folder / 'summary.json', result)
    for phase in ('battles', 'battles_moves'):
        variants = {v: json.loads((output / v / phase / 'summary.json').read_text()) for v in configs(output)}
        failures = {v: {(r['case'], tuple(r['issues'])) for r in result['results'] if r['issues']} for v, result in variants.items()}
        write(output / f'{phase}-comparison.json', dict(phase=phase,
            no_new_failures=failures['candidate'] <= failures['baseline'],
            baseline_failures=sorted(failures['baseline']), candidate_failures=sorted(failures['candidate']),
            recovery_budget='One additional 60,000 display intervals, seven-frame input cadence; original failure retained'))


def run(output, action):
    handlers = dict(data=data, rules=rules, actions=actions, teams=teams, battles=battles, ui=ui, reward_routing=reward_routing,
                    battles_moves=lambda cfg, folder: battles(cfg, folder, regular_moves=True))
    results = {}
    for variant, cfg in configs(output).items():
        folder = output / variant / action
        if (folder / 'summary.json').exists():
            attempt = 1
            while (output / variant / f'{action}-attempt-{attempt}').exists():
                attempt += 1
            shutil.move(folder, output / variant / f'{action}-attempt-{attempt}')
        folder.mkdir(exist_ok=True)
        print(json.dumps(dict(variant=variant, phase=action, start=True)), flush=True)
        try:
            rows = handlers[action](cfg, folder)
            result = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows), results=rows)
        except Exception:
            result = dict(cases=0, failures=1, fatal=traceback.format_exc(), results=[])
        write(folder / 'summary.json', result)
        results[variant] = result
        print(json.dumps(dict(variant=variant, phase=action, cases=result['cases'], failures=result['failures'],
                             fatal=result.get('fatal'))), flush=True)
    old = {(row['case'], tuple(row['issues'])) for row in results['baseline']['results'] if row['issues']}
    new = {(row['case'], tuple(row['issues'])) for row in results['candidate']['results'] if row['issues']}
    comparison = dict(phase=action, no_new_failures=new <= old and not results['candidate'].get('fatal'),
                      baseline_failures=sorted(old), candidate_failures=sorted(new),
                      baseline_fatal=results['baseline'].get('fatal'), candidate_fatal=results['candidate'].get('fatal'))
    write(output / f'{action}-comparison.json', comparison)
    return int(not comparison['no_new_failures'])


def timeout_audit(output, phases=('battles', 'battles_moves')):
    rows = []
    for variant, cfg in configs(output).items():
        symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
        for phase in phases:
            audit_timeouts(cfg, symbols, output / variant / phase, variant, phase, rows)
    write(output / 'timeout-audit.json', dict(cases=len(rows), results=rows))
    print(json.dumps([dict(variant=r['variant'], phase=r['phase'], case=r['case'], hp_changed=r['hp_changed'], watch_counts=r['watch_counts']) for r in rows]), flush=True)


def audit_timeouts(cfg, symbols, folder, variant, phase, rows):
    for row in json.loads((folder / 'summary.json').read_text())['results']:
        if not row.get('timeout'):
            continue
        _, group, position = row['case'].split('-')
        checkpoint = folder / f'timeout-{group}-{position}.s0'
        driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], folder / f'audit-{group}-{position}.log')
        try:
            driver.command(f'load {checkpoint}')
            labels = ('BattleMoveInfo_UpdateTilemapAndAttrmap.wait', 'BattleAnim_UpdateOAM_All', 'BattleTurn', 'RunBattleTowerTrainer.lost')
            labels = [name for name in labels if name in symbols]
            for name in labels:
                bank, pc = symbols[name]
                driver.command(f'watch {bank} {pc}')
            snapshots = []
            for sample in range(17):
                snapshots.append(dict(sample=sample, cpu=driver.command('peek'),
                    fields={name: list(get(driver, symbols, name, size)) for name, size in (
                        ('wBattleMonHP', 2), ('wEnemyMonHP', 2), ('wBattleTowerBattleEnded', 1), ('wCurPlayerMove', 1),
                        ('wCurEnemyMove', 1), ('hVBlank', 1), ('hBGMapMode', 1))}))
                if sample < 16:
                    driver.command(f'run 64 {interactive_key(driver, symbols, sample)}')
            counts = driver.command('watchcounts')['hits']
            rows.append(dict(variant=variant, phase=phase, case=row['case'], checkpoint=str(checkpoint),
                watch_counts=dict(zip(labels, counts)), snapshots=snapshots,
                hp_changed=len({tuple(s['fields']['wEnemyMonHP']) for s in snapshots}) > 1 or
                           len({tuple(s['fields']['wBattleMonHP']) for s in snapshots}) > 1))
        finally:
            driver.close()


PHASES = ('data', 'rules', 'actions', 'teams', 'reward_routing', 'ui', 'battles_moves', 'battles')
EXPECTED_CASES = dict(data=242, rules=2136, actions=610, teams=210, reward_routing=15, ui=11, battles_moves=70, battles=70)


def import_battles(output, source):
    destination_config = json.loads((output / 'config.json').read_text())
    source_config = json.loads((source / 'config.json').read_text())
    assert destination_config['protected'] == source_config['protected'], 'Different frozen inputs'
    assert all(sha256(Path(path).read_bytes()) == digest for path, digest in source_config['protected'].items())
    for variant, cfg in source_config['variants'].items():
        assert cfg['rom_sha256'] == destination_config['variants'][variant]['rom_sha256']
        for phase in ('battles', 'battles_moves'):
            original = source / variant / phase
            result = json.loads((original / 'summary.json').read_text())
            assert result['cases'] == 70 and not result.get('fatal'), 'Incomplete phase import'
            destination = output / variant / phase
            attempt = 1
            while (output / variant / f'{phase}-attempt-{attempt}').exists():
                attempt += 1
            shutil.move(destination, output / variant / f'{phase}-attempt-{attempt}')
            shutil.copytree(original, destination)
    for phase in ('battles', 'battles_moves'):
        shutil.copy2(source / f'{phase}-comparison.json', output / f'{phase}-comparison.json')
    write(output / 'battle-phase-provenance.json', dict(source=str(source),
        rationale='Fresh independent checkpoints with native prior-position CopyBTTrainer transitions',
        source_config=source_config, replaced_phases=['battles', 'battles_moves']))


def report(output):
    config = json.loads((output / 'config.json').read_text())
    protected = all(sha256(Path(path).read_bytes()) == digest for path, digest in config['protected'].items())
    phases = {}
    complete = True
    for phase in PHASES:
        variants = {variant: json.loads((output / variant / phase / 'summary.json').read_text())
                    for variant in config['variants']}
        phases[phase] = dict(cases={v: r['cases'] for v, r in variants.items()},
                            failures={v: r['failures'] for v, r in variants.items()},
                            fatal={v: r.get('fatal') for v, r in variants.items()},
                            comparison=json.loads((output / f'{phase}-comparison.json').read_text()))
        sets = [{row['case'] for row in result['results']} for result in variants.values()]
        matrix = all(result['cases'] == EXPECTED_CASES[phase] == len(result['results']) == len(cases)
                     for result, cases in zip(variants.values(), sets)) and sets[0] == sets[1]
        coverage = matrix and all(not result.get('fatal') and not any(row.get('blocked') or row.get('timeout')
                                 for row in result['results']) for result in variants.values())
        phases[phase]['case_matrix_present'] = matrix
        phases[phase]['completed_cases'] = {variant: sum(not row.get('blocked') and not row.get('timeout')
            for row in result['results']) for variant, result in variants.items()}
        phases[phase]['coverage_complete'] = coverage
        complete &= coverage
    result = dict(protected_inputs_unchanged=protected, model='CGB_E',
        rom_hashes={v: c['rom_sha256'] for v, c in config['variants'].items()}, phases=phases,
        coverage_complete=complete,
        clean=protected and complete and all(not any(p['failures'].values()) for p in phases.values()),
        no_new_failures=protected and complete and all(p['comparison']['no_new_failures'] for p in phases.values()),
        scope='Data/helpers/native menus and battles; synthetic combat stats. See separate runbook for unscripted/manual coverage and stress failures.')
    write(output / 'report.json', result)
    print(json.dumps(result, indent=2), flush=True)
    return int(not result['clean'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'data', 'rules', 'actions', 'teams', 'reward-routing', 'battles', 'battles-moves', 'ui', 'recompile', 'timeout-audit', 'recover-timeouts', 'import-battles', 'report', 'all'))
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--baseline-source', type=Path, default=SOURCES['baseline'])
    parser.add_argument('--candidate-source', type=Path, default=SOURCES['candidate'])
    parser.add_argument('--battery', type=Path, default=BATTERY)
    parser.add_argument('--source-output', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.output.resolve(), dict(baseline=args.baseline_source.resolve(), candidate=args.candidate_source.resolve()), args.battery.resolve())
    elif args.action == 'recompile':
        for variant, cfg in configs(args.output.resolve()).items():
            core(Path(cfg['root']), stem='pokecrystal', target_root=args.output.resolve() / variant)
    elif args.action == 'timeout-audit':
        timeout_audit(args.output.resolve())
    elif args.action == 'recover-timeouts':
        recover_timeouts(args.output.resolve())
    elif args.action == 'import-battles':
        if not args.source_output:
            parser.error('--source-output is required for import-battles')
        import_battles(args.output.resolve(), args.source_output.resolve())
    elif args.action == 'report':
        raise SystemExit(report(args.output.resolve()))
    elif args.action == 'all':
        for phase in PHASES:
            run(args.output.resolve(), phase)
        timeout_audit(args.output.resolve())
        recover_timeouts(args.output.resolve())
        raise SystemExit(report(args.output.resolve()))
    else:
        raise SystemExit(run(args.output.resolve(), args.action.replace('-', '_')))
