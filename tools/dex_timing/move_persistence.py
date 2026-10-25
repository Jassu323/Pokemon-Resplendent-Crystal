"""Cold-boot native qualification of the discovery save extension."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path
import random
import subprocess

from .assets import read_symbols, sha256
from .cold_listing import Driver, ROOT
from .info_ui import BOOT
from move_discovery_assets import address, decode_record, encode_record, move_bitmap, seed_records

STEM = 'pokecrystal-dex-moves-persistence'
FRAME_MS = 70224 / 4194304 * 1000


def core(output, stem=STEM, target_root=None):
    repo_symbols = read_symbols(output / f'{stem}.sym')
    target = (target_root or output) / ('persistence-core' if stem == STEM else 'baseline-persistence-core')
    target.mkdir(exist_ok=True)
    header = target / 'symbols.h'
    header.write_text(f'#define S_FarCall_hl {repo_symbols["FarCall_hl"][1]}\n')
    source = Path.home() / 'Documents/GitHub/SameBoy'
    files = ('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
             'sm83_cpu timing workboy').split()
    executable = target / 'runner'
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(source), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING',
                    '-DGB_VERSION="move-persistence"', '-include', str(header),
                    str(ROOT / 'tools/dex_timing/probes/move_persistence.c'),
                    *(str(source / 'Core' / f'{file}.c') for file in files),
                    '-o', str(executable)], check=True)
    return executable


def call(driver, symbols, name, index=0, bc=0xa55a):
    bank, pc = symbols[name]
    result = driver.command(f'call {bank} {pc} {bc} {index}')
    if not result['hit']:
        raise AssertionError(f'Native call did not return: {name}: {result}')
    result['intervals'] = result['elapsed'] / 140448
    result['ms'] = result['intervals'] * FRAME_MS
    return result


def read(driver, symbols):
    bank, pc = symbols['wMoveDiscoverySeen']
    return bytes.fromhex(driver.command(f'read {bank} {pc} 66')['bytes'])


def boot(config, battery, log, trace=None):
    driver = Driver(config['core'], config['rom'], BOOT, battery, log)
    if trace:
        driver.command(f'trace {trace}')
    bank, pc = config['symbols']['HandleMapTimeAndJoypad']
    for _ in range(15):
        result = driver.command(f'until {bank} {pc} 180 16')
        if result['hit']:
            return driver
        driver.command('run 10 0')
    driver.close()
    raise AssertionError('Cold Continue did not reach the overworld')


def input_call(driver, symbols, name, *, af=0, bc=0xa55a, de=0x5aa5, hl=0):
    """Set inputs at a real banked callee, then unwind the native far call."""
    owner = driver.command('peek')
    bank, pc = symbols[name]
    driver.command(f'begin {bank} {pc} {bc} {de}')
    if not driver.command(f'until {bank} {pc} 4 0')['hit']:
        raise AssertionError('Banked helper entry not reached: ' + name)
    driver.command(f'regs {af} {bc} {de} {hl}')
    driver.command('follow')
    result = driver.command('resume 16 0')
    if not result['hit']:
        raise AssertionError('Banked helper did not return: ' + name)
    returned = driver.command(f'until {owner["bank"]} {owner["pc"]} 8 0')
    if not returned['hit'] or returned['sp'] != owner['sp']:
        raise AssertionError('Observer far call did not unwind: ' + name)
    return result


def helper_tests(config, output):
    symbols = config['symbols']
    driver = boot(config, output / 'empty.sav', output / 'helpers.log')
    records = []
    try:
        before_path = output / 'helpers-before.sav'
        driver.command(f'battery {before_path}')
        for bank in range(1, 8):
            driver.command(f'io 65392 {bank}')
            for index in (*range(1, 334), 0, 334, 512, 513, 0x7fff, 0x8000, 0xffff):
                call(driver, symbols, 'MoveDiscovery_Clear')
                marked = call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
                expected = move_bitmap([index]) if 1 <= index <= 333 else bytes(64)
                if read(driver, symbols)[:64] != expected:
                    raise AssertionError(f'Wrong native bit: bank {bank}, move {index}')
                valid = 1 <= index <= 333
                if bool(marked['af'] & 0x10) != valid or marked['bc'] != 0xa55a or marked['de'] != index:
                    raise AssertionError(f'Flag/register contract: {marked}')
                if marked['svbk'] & 7 != bank:
                    raise AssertionError('WRAM bank not restored')
                located = call(driver, symbols, 'MoveDiscovery_BitAddress', index)
                if bool(located['af'] & 0x10) == valid or located['svbk'] & 7 != bank:
                    raise AssertionError('Bit-address validity/bank contract changed')
                if valid:
                    if located['hl'] != symbols['wMoveDiscoverySeen'][1] + (index - 1) // 8:
                        raise AssertionError('Wrong production byte address')
                    if located['bc'] >> 8 != 1 << ((index - 1) % 8):
                        raise AssertionError('Wrong production bit mask')
                    # Query the same snapshot and helper that the live Moves UI uses.
                    snap = call(driver, symbols, 'PokedexMovesMode_SnapshotSeen')
                    if snap['svbk'] & 7 != symbols['wPokedexInfoGFX'][0]:
                        raise AssertionError('Snapshot did not select its owning bank')
                    for query, seen in ((index, True), (index % 333 + 1, False)):
                        checked = input_call(driver, symbols, 'PokedexMovesMode_IsSeen', hl=query)
                        if bool(checked['af'] & 0x10) != seen or checked['hl'] != query:
                            raise AssertionError('Moves UI snapshot query/HL contract changed')
                        if checked['svbk'] & 7 != symbols['wPokedexInfoGFX'][0]:
                            raise AssertionError('Moves UI query changed its owning bank')
                    driver.command(f'io 65392 {bank}')
                call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
                if read(driver, symbols)[:64] != expected:
                    raise AssertionError('Duplicate mark changed another bit')
                records.append(dict(bank=bank, index=index, ms=marked['ms']))
        driver.command('io 65392 1')
        call(driver, symbols, 'MoveDiscovery_Clear')
        indices = list(range(1, 334))
        random.Random(739).shuffle(indices)
        for index in indices:
            call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
        before = read(driver, symbols)[:64]
        call(driver, symbols, 'ForceGarbageCollection')
        if read(driver, symbols)[:64] != before:
            raise AssertionError('Conversion table GC changed permanent discovery')
        after_path = output / 'helpers-after.sav'
        driver.command(f'battery {after_path}')
        if before_path.read_bytes()[:32768] != after_path.read_bytes()[:32768]:
            raise AssertionError('Flag helpers or GC wrote battery RAM')
    finally:
        driver.close()
    (output / 'helpers.json').write_text(json.dumps(records, indent=2) + '\n')
    return len(records)


def snapshot_tests(config, output):
    symbols = config['symbols']
    driver = boot(config, output / 'empty.sav', output / 'snapshot.log')
    try:
        bank, start = symbols['wPokedexInfoGFX']
        for indices in ([], [1], [255, 256, 257, 333], list(range(1, 334))):
            call(driver, symbols, 'MoveDiscovery_Clear')
            for index in indices:
                call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
            before = bytes.fromhex(driver.command(f'read {bank} {start} 640')['bytes'])
            driver.command(f'io 65392 {bank}')
            result = call(driver, symbols, 'PokedexMovesMode_SnapshotSeen')
            after = bytes.fromhex(driver.command(f'read {bank} {start} 640')['bytes'])
            expected = move_bitmap(indices)
            if after[:576] != before[:576] or after[576:] != expected or read(driver, symbols)[:64] != expected:
                raise AssertionError('Snapshot copy changed unrelated scratch or live flags')
            if result['svbk'] & 7 != bank:
                raise AssertionError('Snapshot did not return in the owner bank')
    finally:
        driver.close()
    return 4


def cold_case(task):
    config, path, expected, status, blocked = task
    if 'MoveDiscovery_BootstrapOwned' in config['symbols'] and status in (2, 3, 4) and not blocked:
        from .move_acquisition import expected_migration
        prefix = 's' if core_valid(path.read_bytes(), config['symbols'], 's') else 'sBackup'
        owned = expected_migration(path.read_bytes(), config['symbols'], prefix)
        expected = bytes(a | b for a, b in zip(expected, owned))
    driver = boot(config, path, path.with_suffix('.log'))
    try:
        actual = read(driver, config['symbols'])
        if actual != expected + bytes((status, blocked)):
            raise AssertionError(f'{path.name}: expected {status}/{blocked}, got {actual.hex()}')
        repaired = path.with_suffix('.repaired.sav')
        driver.command(f'battery {repaired}')
        data = repaired.read_bytes()
        selected_primary = core_valid(path.read_bytes(), config['symbols'], 's')
        repaired_prefix = 'sBackup' if selected_primary else 's'
        if not blocked and decode_record(data, config['symbols'], repaired_prefix) != dict(status='valid', bitmap=expected):
            raise AssertionError(f'{path.name}: automatic mirror repair has wrong record')
        if blocked:
            original = path.read_bytes()
            for prefix in ('s', 'sBackup'):
                at = address(config['symbols'], prefix + 'MoveDiscovery')
                if data[at:at + 136] != original[at:at + 136]:
                    raise AssertionError('Unsupported record overwritten during repair')
        return dict(case=path.name, status=status, blocked=blocked)
    finally:
        driver.close()


def core_valid(data, symbols, prefix):
    start, end = (address(symbols, prefix + field) for field in ('SaveData', 'SaveDataEnd'))
    check = address(symbols, prefix + 'Checksum')
    actual = int.from_bytes(data[check:check + 2], 'little')
    move = address(symbols, prefix + 'MoveIndexTable')
    size = symbols['wMoveIndexTableEnd'][1] - symbols['wMoveIndexTable'][1]
    conversion = address(symbols, prefix + 'ConversionTableChecksum')
    return actual == sum(data[start:end]) & 65535 and (
        int.from_bytes(data[conversion:conversion + 2], 'little') == sum(data[move:move + size]) & 65535)


def checksum(data, symbols, prefix):
    start, end = (address(symbols, prefix + field) for field in ('SaveData', 'SaveDataEnd'))
    at = address(symbols, prefix + 'Checksum')
    data[at:at + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')


def fixture_cases(config, output, original):
    symbols = config['symbols']
    primary = address(symbols, 'sMoveDiscovery')
    backup = address(symbols, 'sBackupMoveDiscovery')
    one, two = move_bitmap([1, 255, 256, 257, 333]), move_bitmap([2, 57, 85, 166])
    valid = bytearray(seed_records(original, symbols, one))
    tasks = []
    def add(name, data, expected=one, status=1, blocked=0):
        path = output / (name + '.sav')
        path.write_bytes(data)
        tasks.append((config, path, expected, status, blocked))
    add('both-valid', valid)
    generator = random.Random(91)
    for pattern in (bytes(64), bytes([255]) * 64,
                    bytes(generator.randrange(256) for _ in range(64)), two):
        add('pattern-' + str(len(tasks)), seed_records(original, symbols, pattern), pattern)
    different = valid.copy()
    different[backup:backup + 72] = encode_record(different, symbols, 'sBackup', two)
    add('different-valid-primary-wins', different)
    damaged = valid.copy()
    damaged[address(symbols, 'sChecksum')] ^= 1
    add('bad-primary-core-backup-load', damaged)
    damaged = valid.copy()
    damaged[address(symbols, 'sBackupChecksum')] ^= 1
    add('bad-backup-core-primary-load', damaged)
    for byte in range(72):
        for bit in range(8):
            damaged = valid.copy()
            damaged[primary + byte] ^= 1 << bit
            add(f'primary-bit-{byte:02}-{bit}', damaged, status=2)
            damaged = valid.copy()
            damaged[backup + byte] ^= 1 << bit
            add(f'backup-bit-{byte:02}-{bit}', damaged)
    for prefix, at in (('s', primary), ('sBackup', backup)):
        missing = valid.copy()
        missing[at:at + 72] = bytes(72)
        add(prefix + '-missing', missing, status=2 if prefix == 's' else 1)
    for fill in (bytes(136), bytes([255]) * 136, original[primary:primary + 136],
                 b'MD' + bytes([1, 64]) + bytes(132)):
        legacy = valid.copy()
        legacy[primary:primary + 136] = fill
        legacy[backup:backup + 136] = fill
        add('legacy-' + str(len(tasks)), legacy, bytes(64), 4 if fill[:2] == b'MD' else 3)
    for prefix, at in (('s', primary), ('sBackup', backup)):
        for version, length in ((2, 64), (1, 128), (99, 42)):
            future = valid.copy()
            record = encode_record(future, symbols, prefix, bytes([0x55]) * length, version)
            future[at:at + len(record)] = record
            add(f'future-{prefix}-{version}-{length}', future, one,
                2 if prefix == 's' else 1, 1)
    foreign = valid.copy()
    foreign[primary] = 0
    foreign[address(symbols, 'sBackupPlayerData')] ^= 1
    checksum(foreign, symbols, 'sBackup')
    foreign[backup:backup + 72] = encode_record(foreign, symbols, 'sBackup', two)
    add('foreign-playthrough', foreign, bytes(64), 3)
    foreign = valid.copy()
    foreign[primary] = 0
    secret = address(symbols, 'sBackupPlayerData') + symbols['wSecretID'][1] - symbols['wPlayerData'][1]
    foreign[secret] ^= 1
    checksum(foreign, symbols, 'sBackup')
    foreign[backup:backup + 72] = encode_record(foreign, symbols, 'sBackup', two)
    add('foreign-secret-id', foreign, bytes(64), 3)
    different_parent = valid.copy()
    different_parent[primary + 6] ^= 1
    time = address(symbols, 'sBackupPlayerData') + symbols['wGameTimeFrames'][1] - symbols['wPlayerData'][1]
    different_parent[time] ^= 1
    checksum(different_parent, symbols, 'sBackup')
    different_parent[backup:backup + 72] = encode_record(different_parent, symbols, 'sBackup', two)
    add('same-playthrough-different-parent', different_parent, two, 2)
    invalid_donor = valid.copy()
    invalid_donor[primary] = 0
    invalid_donor[address(symbols, 'sBackupChecksum')] ^= 1
    add('invalid-core-donor-rejected', invalid_donor, bytes(64), 3)
    invalid_moves = valid.copy()
    invalid_moves[address(symbols, 'sMoveIndexTable')] ^= 1
    add('bad-primary-conversion-checksum', invalid_moves)
    stale = valid.copy()
    stale[primary + 4] ^= 1
    stale[backup] = 0
    add('parent-mismatch', stale, bytes(64), 4)
    return tasks


def repair_interruptions(config, output):
    symbols = config['symbols']
    expected = move_bitmap(range(1, 334))
    data = bytearray(seed_records((output / 'empty.sav').read_bytes(), symbols, expected))
    data[address(symbols, 'sMoveDiscovery') + 6] ^= 1
    source = output / 'repair-source.sav'
    source.write_bytes(data)
    trace = output / 'repair.csv'
    driver = boot(config, source, output / 'repair.log', trace=trace)
    try:
        if read(driver, symbols)[:64] != expected:
            raise AssertionError('Repair-source flags not recovered')
    finally:
        driver.close()
    tasks = []
    allowed = {at for prefix in ('s', 'sBackup') for at in
               range(address(symbols, prefix + 'MoveDiscovery'), address(symbols, prefix + 'MoveDiscovery') + 72)}
    checks = {address(symbols, prefix + 'Checksum') + byte
              for prefix in ('s', 'sBackup') for byte in range(2)}
    with trace.open() as file:
        for number, row in enumerate(csv.reader(file)):
            bank, location, value, _, _ = map(int, row)
            at = bank * 8192 + location - 0xa000
            data[at] = value
            if at not in allowed | checks:
                continue
            primary = decode_record(data, symbols, 's')
            backup = decode_record(data, symbols, 'sBackup')
            if primary['status'] == 'valid' and core_valid(data, symbols, 's'):
                bitmap, status = primary['bitmap'], 1
            elif backup['status'] == 'valid' and core_valid(data, symbols, 'sBackup'):
                bitmap, status = backup['bitmap'], 2
            else:
                raise AssertionError('Repair destroyed its only valid discovery record')
            if bitmap != expected:
                raise AssertionError('Repair accepted partial discoveries')
            path = output / f'repair-cut-{number:05}.sav'
            path.write_bytes(data)
            tasks.append((config, path, expected, status, 0))
    if len(tasks) != 150:
        raise AssertionError(f'Unexpected selected/donor repair writes: {len(tasks)}')
    return tasks


def save_roundtrips(config, output):
    symbols = config['symbols']
    records = []
    patterns = [[], [1], [255, 256, 257, 333], list(range(1, 334, 2)), list(range(1, 334))]
    for i, indices in enumerate(patterns):
        driver = boot(config, output / 'empty.sav', output / f'save-{i}.log')
        try:
            for index in indices:
                call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
            expected = move_bitmap(indices)
            before = output / f'save-{i}-before.sav'
            driver.command(f'battery {before}')
            trace = output / f'save-{i}.csv'
            driver.command(f'trace {trace}')
            timing = call(driver, symbols, 'SaveGameData')
            driver.command('trace off')
            battery = output / f'save-{i}.sav'
            driver.command(f'battery {battery}')
            saved = battery.read_bytes()
            for prefix in ('s', 'sBackup'):
                if not core_valid(saved, symbols, prefix) or decode_record(saved, symbols, prefix) != dict(status='valid', bitmap=expected):
                    raise AssertionError('Saved record differs from independent decoder')
                at = address(symbols, prefix + 'MoveDiscovery')
                with trace.open() as file:
                    writes = [(bank * 8192 + location - 0xa000, value)
                              for bank, location, value, _, _ in (map(int, row) for row in csv.reader(file))]
                extension = [(location, value) for location, value in writes if at <= location < at + 72]
                if len(extension) != 74 or extension[:2] != [(at, 0), (at + 1, 0)] or extension[-2:] != [(at, 0x4d), (at + 1, 0x44)]:
                    raise AssertionError('Extension marker was not invalidated first/committed last')
            # Unsaved live progress must not appear in the battery.
            call(driver, symbols, 'MoveDiscovery_MarkIndex', 2)
            unsaved = output / f'save-{i}-unsaved.sav'
            driver.command(f'battery {unsaved}')
            records.append(dict(pattern=i, indices=len(indices), timing=timing,
                                trace=str(trace), battery=str(battery), before=str(before)))
        finally:
            driver.close()
        cold_case((config, battery, expected, 1, 0))
        cold_case((config, unsaved, expected, 1, 0))
    return records


def interrupted_cases(config, output, saves):
    symbols = config['symbols']
    extension = {prefix: (address(symbols, prefix + 'MoveDiscovery'),
                          address(symbols, prefix + 'MoveDiscovery') + 72)
                 for prefix in ('s', 'sBackup')}
    expected_new = move_bitmap(range(1, 334))
    record = saves[-1]
    data = bytearray(Path(record['before']).read_bytes())
    rows = list(csv.reader(Path(record['trace']).open()))
    tasks = []
    for i, row in enumerate(rows):
        bank, location, value, _, _ = map(int, row)
        at = bank * 8192 + location - 0xa000
        data[at] = value
        is_extension = any(start <= at < end for start, end in extension.values())
        boundary = at in {address(symbols, prefix + 'Checksum') + n
                          for prefix in ('s', 'sBackup') for n in range(2)}
        if not is_extension and not boundary:
            continue
        primary_valid = core_valid(data, symbols, 's')
        selected = 's' if primary_valid else 'sBackup'
        other = 'sBackup' if primary_valid else 's'
        selected_record = decode_record(data, symbols, selected)
        other_record = decode_record(data, symbols, other)
        if selected_record['status'] == 'valid':
            expected, status = selected_record['bitmap'], 1
        elif core_valid(data, symbols, other) and other_record['status'] == 'valid':
            expected, status = other_record['bitmap'], 2
        else:
            expected, status = bytes(64), 3 if selected_record['status'] == 'legacy' else 4
        if expected not in (bytes(64), expected_new):
            raise AssertionError('Oracle accepted partial write')
        path = output / f'powercut-{i:05}.sav'
        path.write_bytes(data)
        tasks.append((config, path, expected, status, 0))
    if len(tasks) != 152:
        raise AssertionError(f'Unexpected native extension/checksum write count: {len(tasks)}')
    return tasks


def lifecycle(config, output):
    symbols = config['symbols']
    source = output / 'save-4.sav'
    driver = Driver(config['core'], config['rom'], BOOT, source, output / 'new-game.log')
    try:
        bank, pc = symbols['MainMenuJoypadLoop.loop']
        if not driver.command(f'until {bank} {pc} 1200 16')['hit']:
            raise AssertionError('Could not reach main menu from a fresh boot')
        driver.command('run 8 0')
        for index in range(1, 334):
            call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
        if read(driver, symbols)[:64] != move_bitmap(range(1, 334)):
            raise AssertionError('New Game starting fixture is not populated')
        original = output / 'new-game-before.sav'
        driver.command(f'battery {original}')
        driver.command('run 8 8')
        driver.command('run 8 0')
        menu_bank, menu_pc = symbols['wMenuCursorPosition']
        cursor = bytes.fromhex(driver.command(f'read {menu_bank} {menu_pc} 1')['bytes'])[0]
        if cursor != 2:
            raise AssertionError(f'New Game was not selected: cursor {cursor}')
        bank, pc = symbols['NewGame_ClearTilemapEtc']
        if not driver.command(f'until {bank} {pc} 300 16')['hit']:
            raise AssertionError('New Game reset did not complete through its normal caller')
        if read(driver, symbols) != bytes(66):
            raise AssertionError('New Game leaks live discoveries')
        canceled = output / 'new-game-canceled.sav'
        driver.command(f'battery {canceled}')
        for prefix in ('s', 'sBackup'):
            if decode_record(canceled.read_bytes(), symbols, prefix) != decode_record(original.read_bytes(), symbols, prefix):
                raise AssertionError('Starting New Game changed old discovery record')
        call(driver, symbols, 'ErasePreviousSave')
        erased = output / 'approved-overwrite.sav'
        driver.command(f'battery {erased}')
        for prefix in ('s', 'sBackup'):
            if decode_record(erased.read_bytes(), symbols, prefix)['status'] != 'legacy':
                raise AssertionError('Approved overwrite leaves old extension recoverable')
        call(driver, symbols, 'SaveGameData')
        replacement = output / 'new-game-saved.sav'
        driver.command(f'battery {replacement}')
        for prefix in ('s', 'sBackup'):
            if decode_record(replacement.read_bytes(), symbols, prefix) != dict(status='valid', bitmap=bytes(64)):
                raise AssertionError('Approved replacement retained old discovery')
        call(driver, symbols, 'EmptyAllSRAMBanks')
        deleted = output / 'deleted.sav'
        driver.command(f'battery {deleted}')
        if any(deleted.read_bytes()[:32768]):
            raise AssertionError('Delete-save leaves battery data')
    finally:
        driver.close()
    return 5


def qualify(output, baseline, jobs=6):
    executable = core(output)
    symbols = read_symbols(output / f'{STEM}.sym')
    baseline_symbols = read_symbols(baseline / 'pokecrystal-dex-moves-mode.sym')
    for name, pair in baseline_symbols.items():
        if name.startswith(('s', 'w')) and pair[1] >= 0xa000 and name in symbols:
            if symbols[name] != pair:
                raise AssertionError(f'Existing memory location moved: {name}')
    target = output / 'persistence-qualification'
    target.mkdir(exist_ok=True)
    config = dict(core=str(executable), rom=str(output / f'{STEM}.gbc'), symbols=symbols)
    original = (output / 'legacy-input.sav').read_bytes()
    empty = seed_records(original, symbols, bytes(64))
    (target / 'empty.sav').write_bytes(empty)
    helper_count = helper_tests(config, target)
    snapshot_count = snapshot_tests(config, target)
    print(f'Native helper cases passed: {helper_count}', flush=True)
    saves = save_roundtrips(config, target)
    tasks = fixture_cases(config, target, original)
    tasks += interrupted_cases(config, target, saves)
    tasks += repair_interruptions(config, target)
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        records = []
        for number, record in enumerate(pool.map(cold_case, tasks), 1):
            records.append(record)
            if not number % 200:
                print(f'Cold boots passed: {number}/{len(tasks)}', flush=True)
    lifecycle_count = lifecycle(config, target)
    baseline_core = core(baseline, 'pokecrystal-dex-moves-mode', target_root=output)
    control = dict(core=str(baseline_core), rom=str(baseline / 'pokecrystal-dex-moves-mode.gbc'),
                   symbols=baseline_symbols)
    driver = boot(control, output / 'legacy-input.sav', target / 'baseline-save.log')
    try:
        baseline_time = call(driver, baseline_symbols, 'SaveGameData')
    finally:
        driver.close()
    result = dict(rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                  helper_cases=helper_count, snapshot_cases=snapshot_count,
                  cold_boot_cases=len(records) + len(saves) * 2,
                  interrupted_write_cases=sum(record['case'].startswith('powercut') for record in records),
                  interrupted_repair_cases=sum(record['case'].startswith('repair-cut') for record in records),
                  lifecycle_cases=lifecycle_count, saves=saves, baseline_save=baseline_time,
                  no_save_states=True, workers=min(jobs, 6), issues=[])
    (target / 'cold-boots.json').write_text(json.dumps(records, indent=2) + '\n')
    (output / 'persistence-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('saves', 'baseline_save')}, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    qualify(args.output.resolve(), args.baseline.resolve(), args.jobs)


if __name__ == '__main__':
    main()
