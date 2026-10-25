"""Create isolated battery saves for manual animation A/B review.

Party moves use dynamic IDs; stored PC moves use 14-bit indexes in move/PP
bytes, matching BillsPC_ConvertPartyMonToBoxMon. Both save records and their
conversion-table checksums are rebuilt. Never edits the user's live save.
"""
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import re
import shutil

from .assets import Repository, offset, sha256
from .cold_listing import ROOT, Driver
from .global_speed import BASE, BATTERY, REQUESTED, ADDED_NEW, ADDED_OLD, compile_core
from .shared_menu_fixtures import make_fixture
from . import shared_menu_regression as menu, performance_audio as audio
from tools.pokedex_info_assets import constants

REVIEW = BASE / 'manual-review-v2'

PARTY = (
    ('KYOGRE', 'BIGDIFF', ('POISON_GAS', 'SURF', 'WHIRLPOOL', 'LEAF_BLADE')),
    ('GARCHOMP', 'HEAVY', ('HYDRO_PUMP', 'SUPERPOWER', 'FIRE_BLAST', 'WATER_PULSE')),
    ('LUXRAY', 'RESTORE', ('THUNDERBOLT', 'THUNDERSHOCK', 'CAUSTIC', 'DRAGON_DANCE')),
    ('RAYQUAZA', 'CHARGE', ('SOLARBEAM', 'DAZZLING_GLEAM', 'OVERHEAT', 'PETAL_DANCE')),
    ('MEGANIUM', 'LEAVES', ('RAZOR_LEAF', 'MAGICAL_LEAF', 'SEISMIC_TOSS', 'EARTHQUAKE')),
    ('DUSKNOIR', 'MORE', ('SLUDGE_WAVE', 'SLUDGE_BOMB', 'METEOR_DIVE', 'AERIAL_CRASH')),
)


def create(repo, source, output, party=PARTY, extra_moves=('DRAGON_DANCE',), level=30):
    original = source.read_bytes()
    stage = output.with_name('review-location.sav')
    make_fixture(repo, source, stage, ('CHERRYGROVE_POKECENTER_1F', 3, 3))
    before = stage.read_bytes()
    data = bytearray(before)
    symbols = repo.symbols
    names = re.findall(r'^\s*const\s+(\w+)',
                       (repo.root / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
    species = {n: i + 1 for i, n in enumerate(names)}
    moves = constants(repo.root / 'constants/move_constants.asm')
    assert moves['NO_MOVE'] == 0 and moves['HYDRO_PUMP'] == 0x38
    selected = {m for _, _, row in party for m in row}
    ordered = list(dict.fromkeys(REQUESTED + ADDED_NEW + ADDED_OLD + list(extra_moves)))
    remaining = [m for m in ordered if m not in selected]
    box_species = ('MEWTWO', 'SPHEAL', 'SNORLAX', 'WEAVILE', 'METAGROSS', 'EXEGGCUTE')
    records = [dict(species=s, nickname=n, moves=list(ms), place=f'Party {i + 1}')
               for i, (s, n, ms) in enumerate(party)]
    records += [dict(species=box_species[i % len(box_species)], nickname=f'MOVE{i + 7:02d}',
                     moves=remaining[4 * i:4 * i + 4], place=f'Box 14 slot {i + 1}')
                for i in range((len(remaining) + 3) // 4)]
    assert len(party) == 6 and len(records) <= 26
    move_count = len({m for r in records for m in r['moves']})
    assert move_count == len(set(ordered) | selected)

    def sram(label):
        bank, address = symbols[label]
        assert 0xa000 <= address <= 0xc000
        return bank * 8192 + address - 0xa000

    def saved(prefix, label, size):
        bank, at = symbols[label]
        for block in ('PlayerData', 'CurMapData', 'PokemonData'):
            b, start = symbols['w' + block]
            if b == bank and start <= at and at + size <= symbols['w' + block + 'End'][1]:
                return sram(prefix + block) + at - start
        raise ValueError(label)

    def write(label, value):
        for prefix in ('s', 'sBackup'):
            at = saved(prefix, label, len(value))
            data[at:at + len(value)] = value

    def text(value, size=11):
        encoded = bytes(128 + ord(c) - 65 if c.isupper() else 246 + int(c) for c in value)
        assert len(encoded) < size
        return encoded + bytes((80,)) * (size - len(encoded))

    mon_ids = {n: i + 1 for i, n in enumerate(dict.fromkeys(r['species'] for r in records))}
    move_ids = {n: i + 1 for i, n in enumerate(dict.fromkeys(m for r in records[:6] for m in r['moves']))}
    for label, indexes in (('Pokemon', mon_ids), ('Move', move_ids)):
        size = symbols[f'w{label}IndexTableEnd'][1] - symbols[f'w{label}IndexTable'][1]
        table = bytearray(size)
        table[0] = len(indexes)
        for name, id_ in indexes.items():
            value = (species if label == 'Pokemon' else moves)[name]
            table[2 * id_:2 * id_ + 2] = value.to_bytes(2, 'little')
        for prefix in ('s', 'sBackup'):
            at = sram(prefix + label + 'IndexTable')
            data[at:at + size] = table

    ot_id = data[saved('s', 'wPlayerID', 2):saved('s', 'wPlayerID', 2) + 2]
    ot = data[saved('s', 'wPlayerName', 11):saved('s', 'wPlayerName', 11) + 11]
    assert 1 <= level <= 100
    size = symbols['wCurBaseDataEnd'][1] - symbols['wCurBaseData'][1]
    split = species['HARIYAMA']
    growth_offset = symbols['wBaseGrowthRate'][1] - symbols['wCurBaseData'][1]
    def mon(record, boxed):
        index = species[record['species']]
        at = offset(symbols['BaseData1' if index <= split else 'BaseData2'])
        at += size * (index - 1 if index <= split else index - split - 1)
        base = repo.rom[at:at + size]
        result = bytearray(32 if boxed else 48)
        result[0] = mon_ids[record['species']]
        result[6:8] = ot_id
        curve = offset(symbols['GrowthRates']) + 4 * base[growth_offset]
        ratio, square, linear, constant = repo.rom[curve:curve + 4]
        exp = (ratio >> 4) * level ** 3 // (ratio & 15)
        exp += (-1 if square & 128 else 1) * (square & 127) * level ** 2 + linear * level - constant
        result[8:11] = max(0, exp).to_bytes(3, 'big')
        result[21:23] = bytes((255, 255))
        result[27] = 255
        result[31] = level
        for i, name in enumerate(record['moves']):
            index = moves[name]
            if boxed:
                result[2 + i] = index & 255
                result[23 + i] = index >> 8
            else:
                result[2 + i] = move_ids[name]
                result[23 + i] = repo.rom[offset(symbols['Moves1']) + 6 * (index - 1) + 4]
        if not boxed:
            hp = (2 * (base[1] + 15) * level) // 100 + level + 10
            result[34:36] = result[36:38] = hp.to_bytes(2, 'big')
            for i, value in enumerate(base[2:7]):
                result[38 + 2 * i:40 + 2 * i] = (2 * (value + 15) * level // 100 + 5).to_bytes(2, 'big')
        return result

    write('wPartyCount', bytes((6,)))
    write('wPartySpecies', bytes(mon_ids[r['species']] for r in records[:6]) + bytes((255,)))
    for i, record in enumerate(records[:6], 1):
        write(f'wPartyMon{i}', mon(record, False))
        write(f'wPartyMon{i}Nickname', text(record['nickname']))
        write(f'wPartyMon{i}OT', ot)
    write('wCurBox', bytes((13,)))
    box_names = bytearray(data[saved('s', 'wBoxNames', 14 * 9):saved('s', 'wBoxNames', 14 * 9) + 14 * 9])
    box_names[13 * 9:14 * 9] = text('ANIMS', 9)
    write('wBoxNames', box_names)
    boxed = records[6:]
    start, end = sram('sBox14'), sram('sBox14End')
    data[start:end] = bytes(end - start)
    data[start] = len(boxed)
    data[start + 1:start + 1 + len(boxed)] = bytes(mon_ids[r['species']] for r in boxed)
    data[start + 1 + len(boxed)] = 255
    at = sram('sBox14PokemonIndexes')
    data[at:at + 40] = bytes(40)
    for i, record in enumerate(boxed, 1):
        at = sram(f'sBox14Mon{i}')
        data[at:at + 32] = mon(record, True)
        at = sram(f'sBox14Mon{i}OT')
        data[at:at + 11] = ot
        at = sram(f'sBox14Mon{i}Nickname')
        data[at:at + 11] = text(record['nickname'])
        at = sram('sBox14PokemonIndexes') + 2 * (i - 1)
        data[at:at + 2] = species[record['species']].to_bytes(2, 'little')
    write('wRepelEffect', bytes((0,)))
    for prefix in ('s', 'sBackup'):
        at = sram(prefix + 'MoveIndexTable')
        size = symbols['wMoveIndexTableEnd'][1] - symbols['wMoveIndexTable'][1]
        checksum = sram(prefix + 'ConversionTableChecksum')
        data[checksum:checksum + 2] = (sum(data[at:at + size]) & 65535).to_bytes(2, 'little')
        a, b, checksum = (sram(prefix + n) for n in ('SaveData', 'SaveDataEnd', 'Checksum'))
        data[checksum:checksum + 2] = (sum(data[a:b]) & 65535).to_bytes(2, 'little')
    assert len(data) == len(before) and data[32768:] == before[32768:]
    assert source.read_bytes() == original
    for prefix in ('s', 'sBackup'):
        a, b, checksum = (sram(prefix + n) for n in ('SaveData', 'SaveDataEnd', 'Checksum'))
        assert int.from_bytes(data[checksum:checksum + 2], 'little') == sum(data[a:b]) & 65535
        a = sram(prefix + 'MoveIndexTable')
        checksum = sram(prefix + 'ConversionTableChecksum')
        assert int.from_bytes(data[checksum:checksum + 2], 'little') == sum(data[a:a + 512]) & 65535
    output.write_bytes(data)
    report = dict(level=level, box=14, moves=move_count, pokemon=len(records), records=records,
                  sha256=sha256(data), source=str(source), source_unchanged=True)
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def verify(mode, review=REVIEW):
    folder = review / mode
    stem = folder / ('pokecrystal-animation-' + mode)
    repo = Repository(ROOT, stem.with_suffix('.gbc'), stem.with_suffix('.sym'))
    output = folder / 'verification'
    output.mkdir(exist_ok=True)
    driver = Driver(compile_core(repo, output), stem.with_suffix('.gbc'), menu.BOOT,
                    stem.with_suffix('.sav'), output / 'run.log')
    records = json.loads((folder.parent / 'animation-review.json').read_text())['records']
    species = re.findall(r'^\s*const\s+(\w+)', (ROOT / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
    moves = constants(ROOT / 'constants/move_constants.asm')
    # Cross-check the linked name strings independently of the constant parser.
    name_at = offset(repo.symbols['MoveNames'])
    linked_names = repo.rom[name_at:].split(bytes((80,)))
    source_names = re.findall(r'^\s*li\s+"([^"]+)"', (ROOT / 'data/moves/names.asm').read_text(), re.M)
    charmap = {char: int(value, 16) for char, value in re.findall(
        r'^\s*charmap "([^"]+)",\s*\$([0-9a-fA-F]+)',
        (ROOT / 'constants/charmap.asm').read_text().split('newcharmap')[0], re.M)}
    checked_names = []
    def verify_names(actual, record):
        for index, move in zip(actual, record['moves']):
            key = {'PSYCHIC_M': 'PSYCHIC', 'DAZZLING_GLEAM': 'DAZZLEGLEAM',
                   'DISARMING_VOICE': 'DISARMVOICE'}.get(move, move).replace('_', '')
            expected = next(n for n in source_names if re.sub(r'[^A-Za-z]', '', n).upper() == key)
            encoded = bytes(charmap[c] for c in expected)
            assert linked_names[index - 1] == encoded, (move, index, linked_names[index - 1], encoded)
            checked_names.append(dict(move=move, index=index, linked_name=expected))
    def ram(name, n):
        b, a = repo.symbols[name]
        return bytes.fromhex(driver.command(f'perfram {b} {a} {n}')['bytes'])
    def indexes(ids, name):
        table = ram('w' + name + 'IndexTableEntries', 200 if name == 'Pokemon' else 460)
        return [int.from_bytes(table[2 * (id_ - 1):2 * id_], 'little') if id_ else 0 for id_ in ids]
    try:
        menu.boot_overworld(driver, repo)
        menu.settle_map_input(driver, repo)
        assert driver.command('m')['double_speed'] == int(mode != 'normal')
        assert ram('wPartyCount', 1) == bytes((6,))
        assert indexes(ram('wPartySpecies', 6), 'Pokemon') == [species.index(r['species']) + 1 for r in records[:6]]
        for i, record in enumerate(records[:6], 1):
            actual = indexes(ram(f'wPartyMon{i}Moves', 4), 'Move')
            assert actual == [moves[m] for m in record['moves']]
            verify_names(actual, record)
            assert all(ram(f'wPartyMon{i}PP', 4)), record
        snapshot = output / 'booted.sav'
        assert driver.command(f'perfbattery {snapshot}')['error'] == 0
        data = snapshot.read_bytes()
        def saved(label, size):
            b, a = repo.symbols[label]
            at = b * 8192 + a - 0xa000
            return data[at:at + size]
        assert saved('sBoxCount', 1) == bytes((len(records) - 6,))
        for i, record in enumerate(records[6:], 1):
            actual = indexes(saved(f'sBoxMon{i}Moves', 4), 'Move')
            expected = [moves[m] for m in record['moves']]
            assert actual == expected + [0] * (4 - len(expected)), (i, actual, expected)
            verify_names(actual, record)
            assert all(saved(f'sBoxMon{i}PP', 4)[:len(expected)]), record
            assert indexes(saved(f'sBoxMon{i}Species', 1), 'Pokemon') == [species.index(record['species']) + 1]
        driver.command(f'image {output / "overworld.ppm"}')
        menu.walk_to(driver, repo, 'y', 4)
        menu.walk_to(driver, repo, 'x', 9)
        menu.walk_to(driver, repo, 'y', 2)
        menu.tap(driver, repo, 'up', held=3, released=12)
        audio.until(driver, repo, 'PokemonCenterPC.loop')
        audio.until(driver, repo, '_BillsPC.loop')
        menu.run(driver, repo, frames=40)
        menu.tap(driver, repo, 'down', released=20)
        assert driver.command('m')['wMenuCursorY'] == 2
        audio.until(driver, repo, '_DepositPKMN.loop')
        menu.run(driver, repo, frames=40)
        audio.until(driver, repo, 'BillsPCDepositFuncDeposit')
        menu.run(driver, repo, frames=180)
        assert ram('wPartyCount', 1) == bytes((5,))
        audio.until(driver, repo, '_BillsPC.loop', key='b')
        menu.run(driver, repo, frames=20)
        menu.tap(driver, repo, 'up', released=12)
        audio.until(driver, repo, '_WithdrawPKMN.loop')
        menu.run(driver, repo, frames=50)
        driver.command(f'image {output / "box.ppm"}')
        audio.until(driver, repo, 'BillsPC_Withdraw')
        audio.until(driver, repo, 'TryWithdrawPokemon')
        menu.run(driver, repo, frames=180)
        assert ram('wPartyCount', 1) == bytes((6,))
        assert indexes(ram('wPartyMon6Moves', 4), 'Move') == [moves[m] for m in records[6]['moves']]
        assert indexes(ram('wPartyMon6Species', 1), 'Pokemon') == [species.index(records[6]['species']) + 1]
        result = dict(mode=mode, valid_boot=True, moves_verified=len(checked_names), linked_names=checked_names,
                      native_deposit_withdraw=True, speed=int(mode != 'normal'))
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        driver.command(f'image {output / "last.ppm"}')
        driver.close()


def main():
    output = REVIEW
    output.mkdir(exist_ok=True)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    report = create(repo, BATTERY, output / 'animation-review.sav')
    for mode, source in (('normal', ROOT / 'pokecrystal'),
                         ('double', BASE / 'final/pokecrystal-global-double-speed')):
        folder = output / mode
        folder.mkdir(exist_ok=True)
        target = folder / ('pokecrystal-animation-' + mode)
        for suffix in ('.gbc', '.sym', '.map'):
            shutil.copy2(source.with_suffix(suffix), target.with_suffix(suffix))
        shutil.copy2(output / 'animation-review.sav', target.with_suffix('.sav'))
    lines = ['# Animation A/B review saves', '',
        'Two ROMs with byte-identical starting battery saves. The normal arm is',
        'unchanged production; the double arm is the qualified global-speed prototype.',
        'Boot and Continue. Do not share CPU save states between differently linked ROMs.', '',
        'Start in Cherrygrove Pokecenter with six level-30 party Pokemon. Remaining',
        'tested moves are on fourteen Pokemon in Box 14, named ANIMS. This isolated',
        'fixture replaces the party and Box 14 only in a test copy, not your live save.',
        'Moves need not be legal learnsets. PP and stats are populated for battle use.',
        'Deposit a party member to make room before withdrawing a boxed review Pokemon.', '',
        'Use the same move in comparable battles. Different DIV/RNG phases can change',
        'hit counts, misses or follow-up turns; compare the matching animation, not',
        'total battle duration. Healing or a fresh copy restores PP between sessions.', '',
        '| Location | Nickname | Species | Moves |', '| --- | --- | --- | --- |']
    for row in report['records']:
        lines.append('| ' + ' | '.join((row['place'], row['nickname'], row['species'], ', '.join(row['moves']))) + ' |')
    (output / 'README.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(report))
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(verify, ('normal', 'double')))
    (output / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
