"""Native and real-input qualification of session-only Pokemon bookmarks."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics

from .assets import Repository, offset, read_symbols, sha256
from .cold_listing import ROOT, Driver, bootstrap, move
from .move_persistence import core as native_core, boot, call, read
from .move_acquisition import fixture, ram
from .moves_sort_memory import register_call
from .performance import core
from .info_ui import BOOT, press
from .area_ui import reach
from .legacy_listing import private_battery, layout_audit, select_presentation
from .listing_options import memory, choose, grid_audit, listing_audit
from .moves_mode import capture

BASE = ROOT / 'build/dex-position-memory-20261014'
STEM = 'pokecrystal-dex-position-memory'
LABELS = ('NewPokedexOrder', 'NationalPokedexOrder', 'AlphabeticalPokedexOrder')


def write(name, value):
    (BASE / 'pokemon-position-tests' / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')


def prepare():
    output = BASE / 'pokemon-position-tests'
    output.mkdir(exist_ok=False)
    repo = Repository(BASE / 'candidate', BASE / f'{STEM}.gbc', BASE / f'{STEM}.sym')
    config = dict(rom=str(repo.rom_path), sym=str(BASE / f'{STEM}.sym'),
                  battery=str(BASE / f'{STEM}.sav'), symbols=repo.symbols,
                  core=str(core(repo, output / 'visual')),
                  native_core=str(native_core(BASE, stem=STEM, target_root=output)),
                  rom_sha256=sha256(repo.rom))
    write('config', config)


def configuration():
    cfg = json.loads((BASE / 'pokemon-position-tests/config.json').read_text())
    return cfg, Repository(BASE / 'candidate', Path(cfg['rom']), Path(cfg['sym']))


def orders(repo):
    # NUM_POKEMON is the linked authored order length, not its reserved capacity.
    count = json.loads((ROOT / 'build/dex-sort-assets/manifest.json').read_text())['species']
    return [[int.from_bytes(repo.rom[offset(repo.symbols[label]) + i * 2:
                     offset(repo.symbols[label]) + i * 2 + 2], 'little')
             for i in range(count)] for label in LABELS]


def expected(style, size, ordinal, cell):
    if style:
        scroll = max(0, min(max(size - 7, 0), ordinal - cell))
    else:
        scroll = max(0, min(max((size + 2) // 3 - 3, 0) * 3,
                            (ordinal // 3 - cell // 3) * 3))
    return scroll.to_bytes(2, 'little') + bytes([ordinal - scroll])


def helpers():
    cfg, repo = configuration()
    cfg['core'] = cfg['native_core']
    symbols = repo.symbols
    output = BASE / 'pokemon-position-tests'
    driver = boot(cfg, cfg['battery'], output / 'helpers.log')
    counts, times = {}, []
    trace = output / 'helpers-sram.csv'
    try:
        discoveries = read(driver, symbols)
        ids = ram(driver, symbols, 'wPokemonIndexTable',
                  symbols['wPokemonIndexTableEnd'][1] - symbols['wPokemonIndexTable'][1])
        moves = ram(driver, symbols, 'wLastMovesDexSort', 5)
        driver.command(f'trace {trace}')
        for order, values in enumerate(orders(repo)):
            fixture(driver, symbols, 'wPokedexOrder', b''.join(i.to_bytes(2, 'little') for i in values))
            fixture(driver, symbols, 'wDexListingEnd', len(values).to_bytes(2, 'little'))
            fixture(driver, symbols, 'wCurDexMode', bytes([order]))
            for style in (0, 1):
                fixture(driver, symbols, 'wPokedexListingPresentation', bytes([style]))
                height = 7 if style else 9
                fixture(driver, symbols, 'wDexListingHeight', bytes([height]))
                maximum = max(len(values) - 7, 0) if style else max((len(values) + 2) // 3 - 3, 0) * 3
                for scroll in range(0, maximum + 1, 1 if style else 3):
                    for cell in range(min(height, len(values) - scroll)):
                        wanted = scroll.to_bytes(2, 'little') + bytes([cell])
                        value = bytes([0xc0 | style << 2 | order]) + values[scroll + cell].to_bytes(2, 'little') + bytes([cell])
                        fixture(driver, symbols, 'wDexListingScrollOffset', wanted)
                        driver.command(f'io 65392 {(scroll + cell) % 8}')
                        register_call(driver, symbols, 'Pokedex_RememberListingPosition', 0x69b0)
                        assert ram(driver, symbols, 'wPokemonDexBookmarkTag', 4) == value
                        fixture(driver, symbols, 'wDexListingScrollOffset', b'\xa5\xa5\xa5')
                        measured = register_call(driver, symbols, 'Pokedex_RestoreListingPosition', 0x69b0)
                        assert ram(driver, symbols, 'wDexListingScrollOffset', 3) == wanted, (style, order, scroll, cell)
                        assert ram(driver, symbols, 'wPokemonDexBookmarkTag', 4) == value
                        assert ram(driver, symbols, 'wLastMovesDexSort', 5) == moves
                        times.append(measured['elapsed'] * 1000 / 8388608)
                        counts['legal_round_trips'] = counts.get('legal_round_trips', 0) + 1
                for size in (0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 254, 255, 256, 257, 372, 373):
                    fixture(driver, symbols, 'wDexListingEnd', size.to_bytes(2, 'little'))
                    for ordinal in sorted({0, size // 2, max(size - 1, 0)}):
                        for cell in range(height):
                            value = bytes([0xc0 | style << 2 | order]) + values[ordinal].to_bytes(2, 'little') + bytes([cell])
                            fixture(driver, symbols, 'wPokemonDexBookmarkTag', value)
                            fixture(driver, symbols, 'wDexListingScrollOffset', b'\xff\xff\xff')
                            register_call(driver, symbols, 'Pokedex_RestoreListingPosition', 0x69b0)
                            want = expected(style, size, ordinal, cell) if size else bytes(3)
                            assert ram(driver, symbols, 'wDexListingScrollOffset', 3) == want, (style, size, ordinal, cell)
                            counts['short_and_boundary_lists'] = counts.get('short_and_boundary_lists', 0) + 1
                fixture(driver, symbols, 'wDexListingEnd', len(values).to_bytes(2, 'little'))
                valid_tag = 0xc0 | style << 2 | order
                malformed = [bytes([tag]) + values[100].to_bytes(2, 'little') + bytes([0])
                             for tag in range(256) if tag != valid_tag]
                malformed += [bytes([valid_tag]) + values[100].to_bytes(2, 'little') + bytes([cell])
                              for cell in range(height, 256)]
                malformed += [bytes([valid_tag]) + identity.to_bytes(2, 'little') + bytes([0])
                              for identity in (0, 374, 512, 65535)]
                for number, value in enumerate(malformed):
                    fixture(driver, symbols, 'wPokemonDexBookmarkTag', value)
                    fixture(driver, symbols, 'wDexListingScrollOffset', b'\xff\xff\xff')
                    driver.command(f'io 65392 {number % 8}')
                    register_call(driver, symbols, 'Pokedex_RestoreListingPosition', 0x69b0)
                    assert ram(driver, symbols, 'wDexListingScrollOffset', 3) == bytes(3)
                    assert ram(driver, symbols, 'wPokemonDexBookmarkTag', 4) == value
                counts['malformed_restore'] = counts.get('malformed_restore', 0) + len(malformed)
                for scroll, cell in ((0, height), (373, 0), (65535, 1)):
                    value = ram(driver, symbols, 'wPokemonDexBookmarkTag', 4)
                    fixture(driver, symbols, 'wDexListingScrollOffset', scroll.to_bytes(2, 'little') + bytes([cell]))
                    register_call(driver, symbols, 'Pokedex_RememberListingPosition', 0x69b0)
                    assert ram(driver, symbols, 'wPokemonDexBookmarkTag', 4) == value
                    counts['invalid_capture'] = counts.get('invalid_capture', 0) + 1
                identity = values[100]
                value = bytes([valid_tag]) + identity.to_bytes(2, 'little') + bytes([5])
                for changed in (values[::-1], values[75:] + values[:75],
                                [v for v in values if v != identity], values[::2], values):
                    fixture(driver, symbols, 'wPokemonDexBookmarkTag', value)
                    fixture(driver, symbols, 'wPokedexOrder', b''.join(v.to_bytes(2, 'little') for v in changed))
                    fixture(driver, symbols, 'wDexListingEnd', len(changed).to_bytes(2, 'little'))
                    register_call(driver, symbols, 'Pokedex_RestoreListingPosition', 0x69b0)
                    want = expected(style, len(changed), changed.index(identity), 5) if identity in changed else bytes(3)
                    assert ram(driver, symbols, 'wDexListingScrollOffset', 3) == want
                    counts['changed_order_and_insertions'] = counts.get('changed_order_and_insertions', 0) + 1
                fixture(driver, symbols, 'wPokedexOrder', b''.join(v.to_bytes(2, 'little') for v in values))
                fixture(driver, symbols, 'wDexListingEnd', len(values).to_bytes(2, 'little'))
        assert read(driver, symbols) == discoveries
        assert ram(driver, symbols, 'wPokemonIndexTable', len(ids)) == ids
        value = ram(driver, symbols, 'wPokemonDexBookmarkTag', 4)
        call(driver, symbols, 'ForceGarbageCollection')
        assert ram(driver, symbols, 'wPokemonDexBookmarkTag', 4) == value
        assert read(driver, symbols) == discoveries
        driver.command('trace off')
        assert trace.stat().st_size == 0
    finally:
        driver.close()
    result = dict(cases=sum(counts.values()), counts=counts, issues=[], no_sram_write=True,
                  registers_and_banks_preserved=True, transient_ids_unchanged=True,
                  restore_ms=dict(minimum=min(times), median=statistics.median(times), maximum=max(times)))
    write('helpers', result)
    print(json.dumps(result, indent=2), flush=True)


def close(driver, repo):
    reach(driver, repo, 'StartMenu.loop', key=32)
    driver.run(frames=8)
    reach(driver, repo, 'StartMenu.b', key=32)
    reach(driver, repo, 'HandleMapTimeAndJoypad')
    driver.run(frames=2)


def listing(driver):
    state = driver.command('peek')
    return {name: state[name] for name in ('presentation', 'mode', 'scroll', 'cursor', 'index', 'end')}


def navigate(driver, key):
    result = move(driver, key)
    driver.run(('end_loop',))
    driver.run(('end_loop',))
    return result


def fresh(name):
    output = BASE / 'pokemon-position-tests' / name
    attempt = 1
    while output.exists():
        attempt += 1
        output = BASE / 'pokemon-position-tests' / f'{name}-attempt-{attempt}'
    output.mkdir()
    return output


def audit(driver, repo):
    current = listing(driver)
    bank, at = repo.symbols['wPokedexOrder']
    data = memory(driver, bank, at, current['end'] * 2)
    values = [int.from_bytes(data[i:i + 2], 'little') for i in range(0, len(data), 2)]
    bank, at = repo.symbols['wPokedexSeen']
    seen = memory(driver, bank, at, 47)
    unseen = {value for value in values if not seen[(value - 1) // 8] & 1 << ((value - 1) & 7)}
    listing_audit(driver, repo, values, unseen)
    return values[current['index']]


def ui():
    cfg, repo = configuration()
    output = fresh('ui')
    rows = []
    for style in (0, 1):
        for order in range(3):
            for cell in range(7 if style else 9):
                directory = output / f'{style}-{order}-{cell}'
                directory.mkdir()
                battery = directory / 'private.sav'
                private_battery(cfg, battery, presentation=style, order_mode=order, unown_unlocked=True)
                driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'trace.log')
                try:
                    bootstrap(driver, expected_mode=order)
                    assert memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 8) == bytes(8)
                    choose(driver, (order + 1) % 3)
                    assert listing(driver)['index'] == 0
                    choose(driver, order)
                    if style:
                        navigate(driver, 'right')
                        navigate(driver, 'right')
                        for _ in range(cell):
                            navigate(driver, 'down')
                    else:
                        for _ in range(10):
                            navigate(driver, 'down')
                        for _ in range(2):
                            navigate(driver, 'up')
                        for _ in range(cell % 3):
                            navigate(driver, 'right')
                        for _ in range(cell // 3):
                            navigate(driver, 'down')
                    before = listing(driver)
                    assert before['cursor'] == cell, before
                    identity = audit(driver, repo)
                    capture(driver, directory / 'before.png')
                    choose(driver, order)
                    assert listing(driver) == before
                    close(driver, repo)
                    value = bytes([0xc0 | style << 2 | order]) + identity.to_bytes(2, 'little') + bytes([cell])
                    assert memory(driver, 1, repo.symbols['wPokemonDexBookmarkTag'][1], 4) == value
                    bootstrap(driver, expected_mode=order)
                    assert listing(driver) == before, (before, listing(driver))
                    assert audit(driver, repo) == identity
                    capture(driver, directory / 'restored.png')
                    if cell == 0:
                        select_presentation(driver, 1 - style)
                        assert listing(driver)['index'] == before['index']
                        select_presentation(driver, style)
                        converted = listing(driver)
                        assert converted['index'] == before['index']
                        close(driver, repo)
                        bootstrap(driver, expected_mode=order)
                        assert listing(driver) == converted
                        assert audit(driver, repo) == identity
                    rows.append(dict(style=style, order=order, cell=cell, identity=identity,
                                     restored=before, issues=[]))
                finally:
                    driver.close()
    write('ui', dict(cases=len(rows), rows=rows, issues=[], evidence=str(output)))
    print(json.dumps(dict(cases=len(rows), issues=[])), flush=True)


def integration():
    from .description_ui import settle
    from .moves_mode import enter as enter_moves, sort as sort_moves, state as moves_state
    from .moves_sort_memory import return_listing, save_visual
    from .moves_position_session import reopen_after_save
    cfg, repo = configuration()
    output = fresh('integration')
    rows = []
    for style in (0, 1):
        for order in range(3):
            directory = output / f'{style}-{order}'
            directory.mkdir()
            battery = directory / 'private.sav'
            private_battery(cfg, battery, presentation=style, order_mode=order, unown_unlocked=True)
            driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'session.log')
            try:
                bootstrap(driver, expected_mode=order)
                for _ in range(12):
                    navigate(driver, 'down')
                before = listing(driver)
                assert before['index'] > 8
                # Browse Selected pages; the returned ordinary species is authoritative.
                driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                settle(driver)
                press(driver, 'down')
                settle(driver)
                press(driver, 'b')
                reach(driver, repo, 'Pokedex_UpdateMainScreen')
                driver.run(('end_loop',))
                before = listing(driver)
                identity = audit(driver, repo)
                # Default Bug Search, then Selected paging inside its temporary order.
                press(driver, 'start')
                press(driver, 'down')
                press(driver, 'a')
                reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                press(driver, 'down')
                press(driver, 'down')
                press(driver, 'a')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
                driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                settle(driver)
                press(driver, 'down')
                settle(driver)
                press(driver, 'b')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
                press(driver, 'b')
                reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                press(driver, 'b')
                reach(driver, repo, 'Pokedex_UpdateMainScreen')
                driver.run(('end_loop',))
                assert listing(driver) == before, 'Search or Selected Results replaced ordinary state'
                # Give Moves an independent nonzero bookmark before saving Pokemon state.
                enter_moves(driver, repo)
                sort_moves(driver, repo, 1)
                press(driver, 'right')
                press(driver, 'down')
                remembered_moves = moves_state(driver, repo)
                moves_bookmark = memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 4)
                return_listing(driver, repo)
                assert listing(driver) == before
                close(driver, repo)
                pokemon_bookmark = memory(driver, 1, repo.symbols['wPokemonDexBookmarkTag'][1], 4)
                assert pokemon_bookmark[1:3] == identity.to_bytes(2, 'little')
                saved = directory / 'normal.sav'
                save_visual(driver, repo, saved)
                assert memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 8) == moves_bookmark + pokemon_bookmark
                reopen_after_save(driver, repo)
                assert listing(driver) == before
                enter_moves(driver, repo)
                assert moves_state(driver, repo) == remembered_moves
                return_listing(driver, repo)
                assert listing(driver) == before
                close(driver, repo)
                reach(driver, repo, 'Reset', key=240)
                driver.run(frames=90)
                bootstrap(driver, expected_mode=order)
                assert memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 8) == bytes(8)
                assert listing(driver)['index'] == 0 and listing(driver)['presentation'] == style
                audit(driver, repo)
                capture(driver, directory / 'soft-reset.png')
            finally:
                driver.close()
            driver = Driver(cfg['core'], cfg['rom'], BOOT, saved, directory / 'cold.log')
            try:
                bootstrap(driver, expected_mode=order)
                assert listing(driver)['index'] == 0 and listing(driver)['presentation'] == style
                assert memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 8) == bytes(8)
                audit(driver, repo)
                enter_moves(driver, repo)
                assert moves_state(driver, repo)['sort'] == 1
                assert moves_state(driver, repo)['scroll'] == moves_state(driver, repo)['cursor'] == 0
                capture(driver, directory / 'moves-cold-reset.png')
            finally:
                driver.close()
            rows.append(dict(style=style, order=order, before=before, identity=identity,
                             selected_paging=True, search_isolated=True, moves_independent=True,
                             save_retained=True, soft_reset_first=True, cold_continue_first=True, issues=[]))
            print(json.dumps(rows[-1]), flush=True)
    write('integration', dict(cases=len(rows), rows=rows, issues=[], evidence=str(output)))


def lifecycle():
    from move_discovery_assets import address
    cfg, repo = configuration()
    cfg['core'] = cfg['native_core']
    output = fresh('lifecycle')
    rows = []
    integration_root = Path(json.loads((BASE / 'pokemon-position-tests/integration.json').read_text())['evidence'])
    for style in (0, 1):
        for order in range(3):
            source = integration_root / f'{style}-{order}/normal.sav'
            for damaged in ('s', 'sBackup'):
                data = bytearray(source.read_bytes())
                data[address(repo.symbols, damaged + 'Checksum')] ^= 0x80
                battery = output / f'{style}-{order}-{damaged}.sav'
                battery.write_bytes(data)
                driver = boot(cfg, battery, battery.with_suffix('.log'))
                try:
                    assert ram(driver, repo.symbols, 'wMovesDexBookmarkTag', 8) == bytes(8)
                    assert ram(driver, repo.symbols, 'wLastDexMode', 2) == bytes([order, style])
                    assert ram(driver, repo.symbols, 'wLastMovesDexSort', 1) == b'\xa1'
                finally:
                    driver.close()
                rows.append(dict(style=style, order=order, corrupt_copy=damaged,
                                 reset_first=True, preferences_preserved=True))
    driver = Driver(cfg['core'], cfg['rom'], BOOT, integration_root / '1-2/normal.sav', output / 'new-game.log')
    try:
        bank, pc = repo.symbols['MainMenuJoypadLoop.loop']
        assert driver.command(f'until {bank} {pc} 1200 16')['hit']
        driver.command('run 8 0')
        fixture(driver, repo.symbols, 'wMovesDexBookmarkTag', b'\xb1\x43\x00\x05\xc6\x01\x01\x06')
        driver.command(f'battery {output}/before-new-game.sav')
        driver.command('run 8 8')
        driver.command('run 8 0')
        assert ram(driver, repo.symbols, 'wMenuCursorPosition', 1) == b'\x02'
        bank, pc = repo.symbols['NewGame_ClearTilemapEtc']
        assert driver.command(f'until {bank} {pc} 300 16')['hit']
        assert ram(driver, repo.symbols, 'wMovesDexBookmarkTag', 8) == bytes(8)
        assert ram(driver, repo.symbols, 'wLastMovesDexSort', 1) == bytes(1)
        assert ram(driver, repo.symbols, 'wLastDexMode', 2) == bytes(2)
        driver.command(f'battery {output}/after-new-game.sav')
        for prefix in ('s', 'sBackup'):
            at = address(repo.symbols, prefix + 'PlayerData')
            at += repo.symbols['wMovesDexBookmarkTag'][1] - repo.symbols['wPlayerData'][1]
            assert (output / 'before-new-game.sav').read_bytes()[at:at + 8] == (output / 'after-new-game.sav').read_bytes()[at:at + 8]
    finally:
        driver.close()
    rows.append(dict(new_game=True, bookmarks_and_preferences_cleared=True))
    write('lifecycle', dict(cases=len(rows), rows=rows, issues=[], evidence=str(output)))
    print(json.dumps(dict(cases=len(rows), issues=[])), flush=True)


def sparse():
    cfg, repo = configuration()
    output = fresh('sparse')
    rows = []
    for style in (0, 1):
        for order in range(3):
            directory = output / f'{style}-{order}'
            directory.mkdir()
            battery = directory / 'private.sav'
            private_battery(cfg, battery, presentation=style, order_mode=order,
                            unseen=tuple(range(0, 373, 2)), unown_unlocked=True)
            driver = Driver(cfg['core'], cfg['rom'], BOOT, battery, directory / 'trace.log')
            try:
                bootstrap(driver, expected_mode=order)
                if order != 2:
                    # Find an unknown entry using real listing controls.
                    for _ in range(32):
                        identity = audit(driver, repo)
                        bank, at = repo.symbols['wPokedexSeen']
                        seen = memory(driver, bank, at + (identity - 1) // 8, 1)[0]
                        if not seen & 1 << ((identity - 1) & 7):
                            break
                        navigate(driver, 'down')
                    else:
                        raise AssertionError('Sparse fixture did not expose an unknown selection')
                else:
                    for _ in range(8):
                        navigate(driver, 'down')
                    identity = audit(driver, repo)
                before = listing(driver)
                close(driver, repo)
                bootstrap(driver, expected_mode=order)
                assert audit(driver, repo) == identity
                assert listing(driver) == before
                capture(driver, directory / 'restored.png')
                rows.append(dict(style=style, order=order, identity=identity,
                                 unseen=order != 2, sparse_alphabet=order == 2,
                                 before=before, after=listing(driver), issues=[]))
            finally:
                driver.close()
    write('sparse', dict(cases=len(rows), rows=rows, issues=[], evidence=str(output)))
    print(json.dumps(dict(cases=len(rows), issues=[])), flush=True)


def warm_case(task):
    from . import dex_lifecycle_review as life
    variant, style, order, target, phase, output = task
    folder = Path(output) / f'{variant}-{style}-{order}-{target}-{phase}'
    folder.mkdir()
    source = BASE / ('rollback' if variant == 'baseline' else 'candidate')
    cfg = json.loads((BASE / f'lifecycle/{variant}/E/config.json').read_text())
    repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
    driver = Driver(cfg['core'], repo.rom_path, BOOT, cfg['fixtures'][f'{style}-{order}'], folder / 'trace.log')
    try:
        life.open_menu(driver)
        reach(driver, repo, 'Pokedex_UpdateMainScreen', key=16)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        if style:
            while listing(driver)['index'] + 7 <= target and listing(driver)['scroll'] < 366:
                navigate(driver, 'right')
            while listing(driver)['index'] < target:
                navigate(driver, 'down')
            while listing(driver)['index'] > target:
                navigate(driver, 'up')
        else:
            for _ in range(target // 3):
                navigate(driver, 'down')
            for _ in range(target % 3):
                navigate(driver, 'right')
        before = listing(driver)
        assert before['index'] == target and before['mode'] == order and before['presentation'] == style
        driver.run(frames=phase / 4)
        leave, _ = life.measured(driver, repo, 'StartMenu.loop', 'b', folder, 'exit', False)
        entry, _ = life.measured(driver, repo, 'Pokedex_UpdateMainScreen', 'a', folder, 'entry', False)
        after = listing(driver)
        if variant == 'integrated':
            assert after == before
            audit(driver, repo)
        return dict(variant=variant, style=style, order=order, target=target, phase=phase,
                    before=before, after=after, entry=entry, exit=leave, issues=[])
    finally:
        driver.close()


def warm_timing():
    output = fresh('warm-timing')
    tasks = [(variant, style, order, target, phase, str(output))
             for variant in ('baseline', 'integrated') for style in (0, 1)
             for order in range(3) for target in (0, 186, 372) for phase in range(4)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(warm_case, tasks))
    original = {(r['style'], r['order'], r['target'], r['phase']): r
                for r in rows if r['variant'] == 'baseline'}
    pairs = []
    frame_ms = 70224 * 1000 / 4194304
    for row in rows:
        if row['variant'] != 'integrated':
            continue
        prior = original[row['style'], row['order'], row['target'], row['phase']]
        record = {key: row[key] for key in ('style', 'order', 'target', 'phase')}
        for direction in ('entry', 'exit'):
            for metric in ('input_to_ready_ms', 'complete_screen_ms'):
                delta = row[direction][metric] - prior[direction][metric]
                record[direction + '_' + metric] = delta
                record[direction + '_' + metric.replace('_ms', '_frames')] = delta / frame_ms
        pairs.append(record)
    summaries = {}
    for target in (0, 186, 372):
        summaries[target] = {}
        for direction in ('entry', 'exit'):
            values = [r[direction + '_input_to_ready_ms'] for r in pairs if r['target'] == target]
            summaries[target][direction] = dict(median_delta_ms=statistics.median(values),
                median_delta_frames=statistics.median(values) / frame_ms,
                maximum_delta_ms=max(values), maximum_delta_frames=max(values) / frame_ms)
    result = dict(cases=len(rows), pairs=pairs, rows=rows, summaries=summaries, issues=[], evidence=str(output),
        note='Normal controls. Production reopens using its existing position policy; the candidate restores the requested position. These are user-workflow comparisons, not identical portrait-rendering workloads.')
    write('warm-timing', result)
    print(json.dumps(dict(cases=len(rows), summaries=summaries), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'helpers', 'ui', 'integration', 'lifecycle', 'sparse', 'warm_timing'))
    parser.add_argument('--base', type=Path, default=BASE)
    args = parser.parse_args()
    BASE = args.base.resolve()
    globals()[args.action]()
