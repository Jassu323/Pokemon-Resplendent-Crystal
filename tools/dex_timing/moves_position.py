"""Native permanent-identity, bank and persistence checks for Moves bookmarks."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import statistics

from .assets import Repository, read_symbols, sha256
from .cold_listing import ROOT
from .move_persistence import boot, core, read, call
from .move_acquisition import fixture, ram
from .moves_sort_memory import register_call
from .info_ui import BOOT, press
from .area_ui import reach
from .legacy_listing import private_battery
from .moves_mode import enter, sort, state, audit, open_sort, capture
from .listing_options import memory
from .cold_listing import Driver, bootstrap

BASE = ROOT / 'build/dex-moves-position-20261014'
STEM = 'pokecrystal-dex-moves-position'
TAG = 0xb0


def write(name, data):
    (BASE / 'position-tests').mkdir(exist_ok=True)
    (BASE / 'position-tests' / (name + '.json')).write_text(json.dumps(data, indent=2) + '\n')


def prepare():
    target = BASE / 'position-tests'
    target.mkdir(exist_ok=True)
    config = dict(rom=str(BASE / f'{STEM}.gbc'), symbols=read_symbols(BASE / f'{STEM}.sym'),
                  core=str(core(BASE, stem=STEM, target_root=target)))
    write('config', config)


def helpers():
    config = json.loads((BASE / 'position-tests/config.json').read_text())
    symbols = config['symbols']
    manifest = json.loads((ROOT / 'build/dex-moves-mode-assets/manifest.json').read_text())
    orders = manifest['orders']
    driver = boot(config, BASE / f'{STEM}.sav', BASE / 'position-tests/helpers.log')
    counts, times = {}, []
    seen = read(driver, symbols)
    scratch = 'wPokedexInfoGFX'
    target = BASE / 'position-tests/helpers-sram.csv'
    try:
        driver.command(f'trace {target}')
        for order, values in enumerate(orders):
            for scroll in range(len(values) - 7):
                for row in range(8):
                    move = values[scroll + row]
                    value = bytes([TAG | order]) + move.to_bytes(2, 'little') + bytes([row])
                    fixture(driver, symbols, 'wMovesDexBookmarkTag', value)
                    before = bytes([order]) + b'\xa3' * 47
                    fixture(driver, symbols, scratch, before)
                    bank = (scroll + row) % 8
                    driver.command(f'io 65392 {bank}')
                    result = register_call(driver, symbols, 'PokedexMovesMode_RestorePosition', 0x69b0)
                    expected = bytes([order, row]) + scroll.to_bytes(2, 'little') + before[4:]
                    assert ram(driver, symbols, scratch, 48) == expected, (order, scroll, row)
                    assert ram(driver, symbols, 'wMovesDexBookmarkTag', 4) == value
                    counts['valid_viewports'] = counts.get('valid_viewports', 0) + 1
                    times.append(result['elapsed'] * 1000 / 8388608)
        for bank in range(8):
            for order in range(2):
                for move in range(1, len(orders[order]) + 1):
                    row = (move + bank) % 8
                    before = bytearray(b'\xa5' * 48)
                    before[:6] = bytes([order, row, 0, 0]) + move.to_bytes(2, 'little')
                    fixture(driver, symbols, scratch, before)
                    driver.command('fixture 3 56384 00')
                    fixture(driver, symbols, 'wMovesDexBookmarkTag', b'\x55' * 4)
                    adjacent = ram(driver, symbols, 'wLastMovesDexSort', 13)
                    driver.command(f'io 65392 {bank}')
                    register_call(driver, symbols, 'PokedexMovesMode_RememberPosition', 0x69b0)
                    assert ram(driver, symbols, scratch, 48) == before
                    expected = bytearray(adjacent)
                    expected[1:5] = bytes([TAG | order]) + move.to_bytes(2, 'little') + bytes([row])
                    assert ram(driver, symbols, 'wLastMovesDexSort', 13) == expected
                    counts['remember_register_bank'] = counts.get('remember_register_bank', 0) + 1
        invalid = [(tag, 1, 0, 0) for tag in range(256) if tag != TAG]
        invalid += [(TAG, move, 0, 0) for move in (0, 334, 512, 513, 65535, *(high << 8 for high in range(2, 256))) ]
        invalid += [(TAG, 1, row, 0) for row in range(8, 256)]
        invalid += [(TAG | 1, 1, 0, 0), (TAG, 1, 0, 1)]
        for index, (tag, move, row, order) in enumerate(invalid):
            value = bytes([tag]) + move.to_bytes(2, 'little') + bytes([row])
            fixture(driver, symbols, 'wMovesDexBookmarkTag', value)
            before = bytes([order]) + b'\xa3' * 47
            fixture(driver, symbols, scratch, before)
            driver.command(f'io 65392 {index % 8}')
            register_call(driver, symbols, 'PokedexMovesMode_RestorePosition', 0x69b0)
            assert ram(driver, symbols, scratch, 48) == bytes([order, 0, 0, 0]) + before[4:]
            assert ram(driver, symbols, 'wMovesDexBookmarkTag', 4) == value
        counts['invalid_restore'] = len(invalid)
        for order in range(2):
            for index, move in enumerate(orders[order]):
                for row in (0, 7):
                    fixture(driver, symbols, 'wMovesDexBookmarkTag', bytes([TAG | order]) + move.to_bytes(2, 'little') + bytes([row]))
                    fixture(driver, symbols, scratch, bytes([order]) + bytes(47))
                    register_call(driver, symbols, 'PokedexMovesMode_RestorePosition', 0x69b0)
                    scroll = max(0, min(len(orders[order]) - 8, index - row))
                    expected = bytes([order, index - scroll]) + scroll.to_bytes(2, 'little')
                    assert ram(driver, symbols, scratch, 4) == expected
                    counts['boundary_clamp'] = counts.get('boundary_clamp', 0) + 1
        driver.command('fixture 3 56384 01')
        before = ram(driver, symbols, 'wMovesDexBookmarkTag', 4)
        register_call(driver, symbols, 'PokedexMovesMode_RememberPosition', 0x69b0)
        assert ram(driver, symbols, 'wMovesDexBookmarkTag', 4) == before
        counts['search_result_guard'] = 1
        call(driver, symbols, 'ForceGarbageCollection')
        assert read(driver, symbols) == seen
        assert ram(driver, symbols, 'wMovesDexBookmarkTag', 4) == before
        driver.command('trace off')
        assert not target.read_bytes(), 'Bookmark helpers wrote SRAM'
    finally:
        driver.close()
    write('helpers', dict(cases=sum(counts.values()), counts=counts, issues=[],
                         restore_ms=dict(minimum=min(times), median=statistics.median(times), maximum=max(times)),
                         no_sram_write=True, registers_and_banks_preserved=True, discovery_and_gc_preserved=True))
    print(json.dumps(dict(counts=counts, restore_ms=(min(times), statistics.median(times), max(times))), indent=2), flush=True)


def visual_config():
    folder = BASE / 'runtime-regression'
    cfg = json.loads((folder / 'search-tests/config.json').read_text())
    cfg['core'] = cfg['visual_core']
    cfg['battery'] = str(BASE / f'{STEM}.sav')
    repo = Repository(BASE / 'candidate', Path(cfg['rom']), Path(cfg['sym']))
    manifest = json.loads((folder / 'moves-mode-manifest.json').read_text())
    return cfg, repo, manifest


def fresh(name):
    path = BASE / 'position-tests' / name
    attempt = 1
    while path.exists():
        attempt += 1
        path = BASE / 'position-tests' / f'{name}-attempt-{attempt}'
    path.mkdir()
    return path


def bookmark(driver, repo):
    bank, at = repo.symbols['wMovesDexBookmarkTag']
    return memory(driver, bank, at, 4)


def visual_audit(driver, repo, manifest):
    bank, at = repo.symbols['wPokedexInfoGFX']
    seen = memory(driver, bank, at + 576, 64)
    unknown = [i for i in range(1, 334) if not seen[(i - 1) // 8] & (1 << ((i - 1) & 7))]
    audit(driver, repo, dict(manifest, fixture='mixed', unknown=unknown))


def ui():
    from .moves_search import open_search, search, row as search_row
    from .moves_sort_memory import close_dex, return_listing
    cfg, repo, manifest = visual_config()
    target = fresh('ui')
    rows = []
    for style in (0, 1):
        for order in (0, 1):
            for cursor in range(8):
                directory = target / f'{style}-{order}-{cursor}'
                directory.mkdir()
                battery = directory / 'private.sav'
                private_battery(cfg, battery, presentation=style, order_mode=cursor % 3, unown_unlocked=True)
                driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'trace.log')
                try:
                    bootstrap(driver, expected_mode=cursor % 3)
                    enter(driver, repo)
                    sort(driver, repo, 1 - order)
                    sort(driver, repo, order)
                    for _ in range(2):
                        press(driver, 'right')
                    for _ in range(cursor):
                        press(driver, 'down')
                    before = state(driver, repo)
                    assert before['scroll'] == 16 and before['cursor'] == cursor
                    expected = bytes([TAG | order]) + before['selected'].to_bytes(2, 'little') + bytes([cursor])
                    assert bookmark(driver, repo) == expected
                    visual_audit(driver, repo, manifest)
                    press(driver, 'select' if cursor & 1 else 'b')
                    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                    press(driver, 'a')
                    reach(driver, repo, 'PokedexMovesMode_Update')
                    assert state(driver, repo) == before
                    open_search(driver, repo)
                    assert bookmark(driver, repo) == expected
                    search(driver, repo)
                    if memory(driver, 3, 56385, 2) != b'\x00\x00':
                        press(driver, 'down')
                    assert bookmark(driver, repo) == expected
                    if cursor & 1:
                        press(driver, 'select')
                        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                        press(driver, 'a')
                        reach(driver, repo, 'PokedexMovesMode_Update')
                    else:
                        press(driver, 'b')
                        reach(driver, repo, 'PokedexMovesSearch_Update')
                        press(driver, 'b')
                        reach(driver, repo, 'PokedexMovesMode_Update')
                    assert state(driver, repo) == before
                    assert bookmark(driver, repo) == expected
                    for cancel in ('b', 'start'):
                        open_sort(driver, repo)
                        press(driver, 'down')
                        press(driver, cancel)
                        reach(driver, repo, 'PokedexMovesMode_Update')
                        assert state(driver, repo) == before
                    sort(driver, repo, order)
                    assert state(driver, repo) == before
                    close_dex(driver, repo)
                    bootstrap(driver, expected_mode=cursor % 3)
                    enter(driver, repo)
                    assert state(driver, repo) == before
                    visual_audit(driver, repo, manifest)
                    sort(driver, repo, 1 - order)
                    changed = state(driver, repo)
                    assert not changed['scroll'] and not changed['cursor']
                    sort(driver, repo, order)
                    changed = state(driver, repo)
                    assert not changed['scroll'] and not changed['cursor']
                    if cursor == 7:
                        capture(driver, directory / 'changed-sort.png')
                    rows.append(dict(style=style, order=order, cursor=cursor, issues=[]))
                finally:
                    driver.close()
    write('ui', dict(cases=len(rows), rows=rows, issues=[]))
    print(json.dumps(dict(ui_cases=len(rows), issues=[])), flush=True)


def saves():
    from .moves_sort_memory import close_dex, save_visual
    from .move_persistence import checksum, core_valid, lifecycle
    from move_discovery_assets import address
    cfg, repo, manifest = visual_config()
    symbols = repo.symbols
    native = json.loads((BASE / 'position-tests/config.json').read_text())
    target = fresh('saves')
    rows, saved_inputs = [], []
    for order in (0, 1):
        initial = target / f'input-{order}.sav'
        private_battery(cfg, initial, presentation=order, order_mode=0, unown_unlocked=True)
        driver = Driver(cfg['core'], cfg['rom'], BOOT, initial, target / f'save-{order}.log')
        saved = target / f'normal-{order}.sav'
        try:
            bootstrap(driver)
            enter(driver, repo)
            sort(driver, repo, 1 - order)
            sort(driver, repo, order)
            for _ in range(19):
                press(driver, 'right')
            for _ in range(5):
                press(driver, 'down')
            expected_state = state(driver, repo)
            expected = bookmark(driver, repo)
            close_dex(driver, repo)
            save_visual(driver, repo, saved)
        finally:
            driver.close()
        saved_inputs.append(saved)
        for prefix in ('s', 'sBackup'):
            at = address(symbols, prefix + 'PlayerData') + symbols['wMovesDexBookmarkTag'][1] - symbols['wPlayerData'][1]
            assert saved.read_bytes()[at:at + 4] == expected and core_valid(saved.read_bytes(), symbols, prefix)
        driver = Driver(cfg['core'], cfg['rom'], BOOT, saved, target / f'cold-{order}.log')
        try:
            bootstrap(driver)
            enter(driver, repo)
            assert state(driver, repo) == expected_state
            assert bookmark(driver, repo) == expected
            visual_audit(driver, repo, manifest)
            capture(driver, target / f'restored-{order}.png')
        finally:
            driver.close()
        rows.append(dict(kind='normal-save-cold-reload', order=order, issues=[]))
        for kind in ('primary-wins', 'bad-primary', 'bad-backup', 'legacy-zero', 'invalid-row', 'invalid-id', 'wrong-sort'):
            data = bytearray(saved.read_bytes())
            wanted = expected
            for prefix in ('s', 'sBackup'):
                at = address(symbols, prefix + 'PlayerData') + symbols['wMovesDexBookmarkTag'][1] - symbols['wPlayerData'][1]
                value = bytearray(expected)
                if prefix == 'sBackup' and kind in ('primary-wins', 'bad-primary'):
                    value[3] = 0
                if kind == 'legacy-zero':
                    value[:] = bytes(4)
                elif kind == 'invalid-row':
                    value[3] = 255
                elif kind == 'invalid-id':
                    value[1:3] = b'\xff\xff'
                elif kind == 'wrong-sort':
                    value[0] ^= 1
                data[at:at + 4] = value
                checksum(data, symbols, prefix)
                if prefix == ('sBackup' if kind == 'bad-primary' else 's'):
                    wanted = bytes(value)
            if kind.startswith('bad-'):
                prefix = 's' if kind == 'bad-primary' else 'sBackup'
                data[address(symbols, prefix + 'Checksum')] ^= 1
            battery = target / f'{kind}-{order}.sav'
            battery.write_bytes(data)
            driver = boot(native, battery, target / f'{kind}-{order}.log')
            try:
                assert ram(driver, symbols, 'wMovesDexBookmarkTag', 4) == wanted
                fixture(driver, symbols, 'wPokedexInfoGFX', bytes([order]) + bytes(47))
                register_call(driver, symbols, 'PokedexMovesMode_RestorePosition', 0x69b0)
                restored = ram(driver, symbols, 'wPokedexInfoGFX', 4)
                if kind in ('legacy-zero', 'invalid-row', 'invalid-id', 'wrong-sort'):
                    assert restored == bytes([order, 0, 0, 0])
                else:
                    assert restored[1] == wanted[3]
            finally:
                driver.close()
            rows.append(dict(kind=kind, order=order, issues=[]))
    shutil.copy2(saved_inputs[-1], target / 'save-4.sav')
    lifecycle_count = lifecycle(native, target)
    for prefix in ('s', 'sBackup'):
        at = address(symbols, prefix + 'PlayerData') + symbols['wMovesDexBookmarkTag'][1] - symbols['wPlayerData'][1]
        assert (target / 'new-game-saved.sav').read_bytes()[at:at + 4] == bytes(4)
    write('saves', dict(cases=len(rows), rows=rows, lifecycle_cases=lifecycle_count, issues=[]))
    print(json.dumps(dict(save_cases=len(rows), lifecycle=lifecycle_count)), flush=True)


def timing():
    from .moves_mode import state
    from .mode_transitions import capture as transition_capture
    cfg, _, _ = visual_config()
    target = fresh('timing')
    rows = []
    manifest = json.loads((ROOT / 'build/dex-moves-mode-assets/manifest.json').read_text())
    for variant, source in (('baseline', BASE / 'baseline-source'), ('candidate', BASE / 'candidate')):
        from .performance import core as visual_core
        repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
        directory = target / variant
        directory.mkdir()
        executable = visual_core(repo, directory, {})
        config = dict(cfg, core=str(executable), rom=str(repo.rom_path), sym=str(source / 'pokecrystal.sym'))
        for order in (0, 1):
            for position in (0, 166, 332):
                for phase in range(4):
                    output = directory / f'{order}-{position}-{phase}'
                    output.mkdir()
                    battery = output / 'private.sav'
                    private_battery(config, battery, presentation=0, order_mode=0, unown_unlocked=True)
                    # Seed saved semantic input only; all entry/display work uses real buttons.
                    from .move_persistence import checksum
                    from move_discovery_assets import address
                    data = bytearray(battery.read_bytes())
                    move = manifest['orders'][order][position]
                    row = min(7, position)
                    for prefix in ('s', 'sBackup'):
                        at = address(repo.symbols, prefix + 'PlayerData') + repo.symbols['wLastMovesDexSort'][1] - repo.symbols['wPlayerData'][1]
                        data[at:at + 5] = bytes([0xa0 | order, TAG | order]) + move.to_bytes(2, 'little') + bytes([row])
                        checksum(data, repo.symbols, prefix)
                    battery.write_bytes(data)
                    driver = Driver(executable, repo.rom_path, BOOT, battery, output / 'trace.log')
                    try:
                        bootstrap(driver)
                        from .legacy_listing import open_mode_screen
                        open_mode_screen(driver)
                        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                        for _ in range(3):
                            press(driver, 'down')
                        driver.command('rawcolor')
                        driver.run(frames=2 + phase / 4)
                        record = transition_capture(driver, output, 'entry', 'a',
                            lambda: reach(driver, repo, 'PokedexMovesMode_Update'))
                        assert not record['issues']
                        rows.append(dict(variant=variant, order=order, position=position, phase=phase,
                                         state=state(driver, repo), **record))
                    finally:
                        driver.close()
    pairs = []
    old = {(r['order'], r['position'], r['phase']):r for r in rows if r['variant'] == 'baseline'}
    for row in rows:
        if row['variant'] == 'candidate':
            prior = old[row['order'], row['position'], row['phase']]
            pairs.append(dict(order=row['order'], position=row['position'], phase=row['phase'],
                              delta_ms=row['complete_ms'] - prior['complete_ms'],
                              delta_frames=row['complete_frames'] - prior['complete_frames']))
    write('timing', dict(cases=len(rows), rows=rows, pairs=pairs, issues=[],
                         median_delta_ms=statistics.median(r['delta_ms'] for r in pairs),
                         maximum_delta_ms=max(r['delta_ms'] for r in pairs)))
    print(json.dumps(dict(timing_cases=len(rows), median_delta_ms=statistics.median(r['delta_ms'] for r in pairs),
                         maximum_delta_ms=max(r['delta_ms'] for r in pairs))), flush=True)


def save_edges():
    from .moves_sort_memory import close_dex, save_visual
    from .move_persistence import core_valid
    from move_discovery_assets import address
    cfg, repo, _ = visual_config()
    symbols = repo.symbols
    native = json.loads((BASE / 'position-tests/config.json').read_text())
    saved = sorted((BASE / 'position-tests').glob('saves*/normal-0.sav'))[-1]
    other = saved.with_name('normal-1.sav')
    target = fresh('save-edges')
    fields = lambda data, prefix: data[address(symbols, prefix + 'PlayerData') + symbols['wLastMovesDexSort'][1] - symbols['wPlayerData'][1]:][:5]
    old, new = fields(saved.read_bytes(), 's'), fields(other.read_bytes(), 's')
    assert old != new
    trace = target / 'normal-save-writes.csv'
    driver = boot(native, saved, target / 'native.log')
    try:
        driver.command(f'battery {target}/before.sav')
        fixture(driver, symbols, 'wLastMovesDexSort', new)
        driver.command(f'trace {trace}')
        call(driver, symbols, 'SaveGameData')
        driver.command('trace off')
    finally:
        driver.close()
    data = bytearray((target / 'before.sav').read_bytes())
    relevant = set()
    for prefix in ('s', 'sBackup'):
        start = address(symbols, prefix + 'PlayerData') + symbols['wLastMovesDexSort'][1] - symbols['wPlayerData'][1]
        relevant.update(range(start, start + 5))
        relevant.update(range(address(symbols, prefix + 'Checksum'), address(symbols, prefix + 'Checksum') + 2))
    rows = []
    for number, values in enumerate(csv.reader(trace.open())):
        bank, at, value, _, _ = map(int, values)
        offset = bank * 8192 + at - 0xa000
        data[offset] = value
        if offset not in relevant:
            continue
        prefix = 's' if core_valid(data, symbols, 's') else 'sBackup'
        assert core_valid(data, symbols, prefix)
        expected = fields(data, prefix)
        assert expected in (old, new), (number, expected.hex())
        battery = target / f'cut-{number}.sav'
        battery.write_bytes(data)
        driver = boot(native, battery, target / f'cut-{number}.log')
        try:
            assert ram(driver, symbols, 'wLastMovesDexSort', 5) == expected
        finally:
            driver.close()
        rows.append(dict(write=number, selected_copy=prefix, recovered=expected.hex()))
    assert len(rows) == 14
    canceled = target / 'canceled-save.sav'
    driver = Driver(cfg['core'], cfg['rom'], BOOT, saved, target / 'canceled-save.log')
    try:
        bootstrap(driver)
        enter(driver, repo)
        press(driver, 'down')
        assert bookmark(driver, repo) != old[1:]
        close_dex(driver, repo)
        save_visual(driver, repo, canceled, accepted=False)
    finally:
        driver.close()
    for prefix in ('s', 'sBackup'):
        assert fields(canceled.read_bytes(), prefix) == fields(saved.read_bytes(), prefix)
    canceled_new_game = saved.with_name('new-game-canceled.sav')
    for prefix in ('s', 'sBackup'):
        assert fields(canceled_new_game.read_bytes(), prefix) == fields(other.read_bytes(), prefix)
    write('save-edges', dict(cases=len(rows) + 2, interrupted_save_cases=len(rows), rows=rows,
                             canceled_save_preserved=True, canceled_new_game_preserved=True, issues=[]))
    print(json.dumps(dict(interrupted_cases=len(rows), canceled_save=True, canceled_new_game=True)), flush=True)


def owners():
    from .moves_sort_memory import return_listing
    from .description_ui import settle
    from .info_ui import ready as info_ready
    from .moves_ui import ready as selected_moves_ready
    from move_discovery_assets import seed_records, move_bitmap
    cfg, repo, manifest = visual_config()
    target = fresh('owners')
    rows = []
    for style in (0, 1):
        for order in (0, 1):
            directory = target / f'{style}-{order}'
            directory.mkdir()
            battery = directory / 'mixed.sav'
            private_battery(cfg, battery, presentation=style, order_mode=0, unown_unlocked=True)
            battery.write_bytes(seed_records(battery.read_bytes(), repo.symbols, move_bitmap(range(1, 334, 2))))
            driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'trace.log')
            try:
                bootstrap(driver)
                enter(driver, repo)
                sort(driver, repo, 1 - order)
                sort(driver, repo, order)
                for _ in range(4):
                    press(driver, 'right')
                press(driver, 'down')
                # Choose an unseen entry deliberately, then preserve its unknown panel.
                for _ in range(8):
                    if state(driver, repo)['selected'] % 2 == 0:
                        break
                    press(driver, 'down')
                before = state(driver, repo)
                assert before['selected'] % 2 == 0
                expected = bookmark(driver, repo)
                visual_audit(driver, repo, manifest)
                capture(driver, directory / 'unseen-before.png')
                for owner in ('info', 'moves', 'unown', 'types'):
                    return_listing(driver, repo)
                    if owner in ('info', 'moves'):
                        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                        settle(driver)
                        press(driver, 'right')
                        if owner == 'moves':
                            press(driver, 'right')
                        press(driver, 'a')
                        info_ready(driver, 0) if owner == 'info' else selected_moves_ready(driver)
                        press(driver, 'b')
                        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
                        driver.run(('end_loop',))
                    else:
                        from .legacy_listing import open_mode_screen
                        open_mode_screen(driver)
                        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                        desired = 2 if owner == 'unown' else 4
                        current = driver.command('ui')['footer_cursor']
                        for _ in range(abs(desired - current)):
                            press(driver, 'down' if desired > current else 'up')
                        press(driver, 'a')
                        reach(driver, repo, 'Pokedex_UpdateUnownMode' if owner == 'unown' else 'PokedexTypes_Update')
                        press(driver, 'right')
                        press(driver, 'b')
                        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                        press(driver, 'b')
                        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
                        driver.run(('end_loop',))
                    enter(driver, repo)
                    assert state(driver, repo) == before
                    assert bookmark(driver, repo) == expected
                    visual_audit(driver, repo, manifest)
                    rows.append(dict(style=style, order=order, owner=owner, unseen_identity=before['selected'], issues=[]))
                capture(driver, directory / 'unseen-restored.png')
            finally:
                driver.close()
    write('owners', dict(cases=len(rows), rows=rows, issues=[]))
    print(json.dumps(dict(owner_cases=len(rows), issues=[])), flush=True)


def search_edges():
    from .moves_search import open_search, search, keyboard, type_, row, finish_text
    cfg, repo, manifest = visual_config()
    target = fresh('search-edges')
    rows = []
    for order in (0, 1):
        for direct_exit in (False, True):
            directory = target / f'{order}-{int(direct_exit)}'
            directory.mkdir()
            battery = directory / 'private.sav'
            private_battery(cfg, battery, presentation=order, unown_unlocked=True)
            driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'trace.log')
            try:
                bootstrap(driver)
                enter(driver, repo)
                sort(driver, repo, order)
                press(driver, 'right')
                press(driver, 'right')
                press(driver, 'down')
                before, expected = state(driver, repo), bookmark(driver, repo)
                open_search(driver, repo)
                row(driver, repo, 1)
                press(driver, 'a')
                reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
                finish_text(driver, repo)
                assert bookmark(driver, repo) == expected
                type_(driver, repo, 0)
                keyboard(driver, repo, 'zzz')
                assert bookmark(driver, repo) == expected
                search(driver, repo)
                assert memory(driver, 3, 56385, 2) == bytes(2)
                for key in ('up', 'down', 'left', 'right'):
                    press(driver, key)
                assert bookmark(driver, repo) == expected
                if direct_exit:
                    press(driver, 'select')
                    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                    press(driver, 'a')
                    reach(driver, repo, 'PokedexMovesMode_Update')
                else:
                    press(driver, 'b')
                    reach(driver, repo, 'PokedexMovesSearch_Update')
                    press(driver, 'b')
                    reach(driver, repo, 'PokedexMovesMode_Update')
                assert state(driver, repo) == before
                visual_audit(driver, repo, manifest)
                rows.append(dict(order=order, direct_exit=direct_exit, zero_results=True, keyboard=True, issues=[]))
            finally:
                driver.close()
    write('search-edges', dict(cases=len(rows), rows=rows, issues=[]))
    print(json.dumps(dict(search_edge_cases=len(rows), issues=[])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'helpers', 'ui', 'saves', 'timing', 'save_edges', 'owners', 'search_edges'))
    args = parser.parse_args()
    globals()[args.action]()
