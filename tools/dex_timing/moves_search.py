"""Native filtering contracts and normal-button Moves search qualification."""
import argparse
import json
from pathlib import Path
import statistics

from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press
from .area_ui import reach
from .performance import core as visual_core
from .move_persistence import core as native_core, boot, call, read
from .moves_mode import enter, sort, state, capture, audit, sweep, page_sweep
from .listing_options import memory
from move_discovery_assets import move_bitmap, seed_records, decode_record

STEM = 'pokecrystal-dex-moves-search'
WORK = 0xdc40
RESULTS = 0xdc80


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def repository(output):
    return Repository(output / 'candidate', output / f'{STEM}.gbc', output / f'{STEM}.sym')


def prepare(output):
    target = output / 'search-tests'
    target.mkdir(exist_ok=True)
    repo = repository(output)
    visual = visual_core(repo, target / 'visual-core', {
        'moves_filter': ('PokedexMovesSearch_Filter', True),
        'moves_draw': ('PokedexMovesMode_Draw', True),
        'moves_search': ('PokedexMovesSearch_Update', False),
        'moves_text': ('PokedexMovesSearch_TextUpdate', False),
        'moves_list': ('PokedexMovesMode_Update', False),
    })
    native = native_core(output, STEM, target)
    config = dict(rom=str(repo.rom_path), sym=str(output / f'{STEM}.sym'),
                  core=str(native), visual_core=str(visual), symbols=repo.symbols)
    write_json(target / 'config.json', config)
    return dict(issues=[], rom_sha256=sha256(repo.rom))


def fixture_at(driver, address, data):
    driver.command(f'fixture 3 {address} {bytes(data).hex()}')


def native_read(driver, address, size):
    return bytes.fromhex(driver.command(f'read 3 {address} {size}')['bytes'])


def filter_tests(output):
    config = json.loads((output / 'search-tests/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    symbols = config['symbols']
    driver = boot(config, output / f'{STEM}.sav', output / 'search-tests/filter.log')
    rows = []
    try:
        canonical = read(driver, symbols)
        driver.command(f'trace {output / "search-tests/filter-sram.csv"}')
        sentinel = bytes([0x5a]) * 666
        fixture_at(driver, RESULTS, sentinel)
        fixture_at(driver, RESULTS + 666, bytes([0xb7]) * 32)
        protected = [(b, a, n) for b, a, n in (
            (*symbols['wPokedexOrder'], 748), (*symbols['wMoveIndexTable'], 768),
            (*symbols['wLastMovesDexSort'], 1))]
        before = [bytes.fromhex(driver.command(f'read {b} {a} {n}')['bytes']) for b, a, n in protected]
        seen_sets = [set(), {1, 2, 10, 165, 255, 256, 257, 333}, set(range(1, 334))]
        queries = ('', 'double', 'PUNCH', 'beam', 'conversion', 'poison', '-', ' ', 'zzzz')
        for seen in seen_sets:
            fixture_at(driver, symbols['wPokedexInfoGFX'][1] + 576, move_bitmap(seen))
            for order in range(2):
                fixture_at(driver, symbols['wPokedexInfoGFX'][1], [order])
                cases = [(type_, query) for type_ in range(19) for query in queries]
                if len(seen) == 333:
                    cases += [(0, m['name']) for m in manifest['moves']]
                for number, (type_, query) in enumerate(cases):
                    fixture_at(driver, WORK + 6, [type_])
                    encoded = encode(query) + b'\x50'
                    fixture_at(driver, WORK + 16, encoded.ljust(13, b'\x50'))
                    incoming = (number % 8)
                    driver.command(f'io 65392 {incoming}')
                    row = call(driver, symbols, 'PokedexMovesSearch_Filter')
                    if row['svbk'] & 7 != incoming:
                        raise AssertionError('Filter lost its incoming WRAM bank')
                    count = int.from_bytes(native_read(driver, WORK + 1, 2), 'little')
                    data = native_read(driver, RESULTS, count * 2)
                    actual = [int.from_bytes(data[n:n + 2], 'little') for n in range(0, len(data), 2)]
                    expected = [i for i in manifest['orders'][order] if i in seen and
                                (not type_ or manifest['moves'][i - 1]['type'] == manifest['types'][type_ - 1]) and
                                query.lower() in manifest['moves'][i - 1]['name'].lower()]
                    if actual != expected:
                        raise AssertionError(f'Filter differs: {len(seen)}/{order}/{type_}/{query}: {actual} != {expected}')
                    if native_read(driver, RESULTS + 666, 32) != bytes([0xb7]) * 32:
                        raise AssertionError('Result buffer overflow')
                    rows.append(dict(seen=len(seen), order=order, type=type_, query=query,
                                     count=count, ms=row['ms']))
        for (b, a, n), expected in zip(protected, before):
            if bytes.fromhex(driver.command(f'read {b} {a} {n}')['bytes']) != expected:
                raise AssertionError('Search changed an unrelated order, ID table or preference')
        if read(driver, symbols) != canonical:
            raise AssertionError('Searching revealed moves')
        driver.command('trace off')
        if (output / 'search-tests/filter-sram.csv').read_bytes():
            raise AssertionError('Filtering wrote SRAM')
    finally:
        driver.close()
    result = dict(cases=len(rows), rows=rows, issues=[],
                  max_ms=max(r['ms'] for r in rows), median_ms=statistics.median(r['ms'] for r in rows))
    write_json(output / 'search-tests/filter.json', result)
    return {k: result[k] for k in ('cases', 'max_ms', 'median_ms', 'issues')}


def encode(text):
    from .dex_modes import encode as original
    return original(text)


def open_search(driver, repo):
    press(driver, 'start')
    reach(driver, repo, 'PokedexMovesSearch_OptionsUpdate')
    press(driver, 'down')
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesSearch_Update')
    driver.run(frames=4)
    form_audit(driver, repo)


def form_audit(driver, repo):
    ui = driver.command('ui')
    tiles = bytes.fromhex(ui['map'])
    for row_, label in ((4, 'Type'), (6, 'Name')):
        if tiles[row_ * 21 + 2:row_ * 21 + 6] != encode(label):
            raise AssertionError('Moves Search parameter labels are not shifted left')
    if tiles[4 * 21 + 7] != 0x3d or tiles[4 * 21 + 16] != 0x3e:
        raise AssertionError('Moves Search arrows are not aligned with the shifted row')
    query = memory(driver, 3, WORK + 16, 13).split(b'\x50')[0]
    start, expected = (7 if 'PokedexMovesSearch_BlinkCursor' in repo.symbols else 6, query) if query else (10, encode('----'))
    if tiles[6 * 21 + start:6 * 21 + start + len(expected)] != expected:
        raise AssertionError('Search name/placeholder does not align with the type field')
    if not query and tiles[6 * 21 + 6:6 * 21 + 10] != b'\x32' * 4:
        raise AssertionError('Empty name still places hyphens adjacent to its label')
    if 'PokedexMovesSearch_BlinkCursor' in repo.symbols and tiles[6 * 21 + 6] != 0x32:
        raise AssertionError('Name lacks its one-tile gap before the query')
    selected = memory(driver, 3, WORK + 7, 1)[0]
    for index, (y, x) in enumerate(((4, 1), (6, 1), (13, 2), (15, 2))):
        expected = (0xed, 0x7f) if index == selected and 'PokedexMovesSearch_BlinkCursor' in repo.symbols else (
            (0xed,) if index == selected else (0x32,))
        if tiles[y * 21 + x] not in expected:
            raise AssertionError('Search cursor is not on its selected form row')


def row(driver, repo, desired):
    current = memory(driver, 3, WORK + 7, 1)[0]
    for _ in range((desired - current) % 4):
        press(driver, 'down')
        reach(driver, repo, 'PokedexMovesSearch_Update')
        driver.run(frames=2)
        if 'PokedexSearch_AlignedFields' in repo.symbols:
            form_audit(driver, repo)


def type_(driver, repo, desired):
    row(driver, repo, 0)
    for _ in range(20):
        current = memory(driver, 3, WORK + 6, 1)[0]
        if current == desired:
            form_audit(driver, repo)
            return
        press(driver, 'left' if desired < current else 'right')
        reach(driver, repo, 'PokedexMovesSearch_Update')
        driver.run(frames=2)
    raise AssertionError('Type selector did not reach the requested field')


def keyboard_neighbor(position, key):
    if position < 27:
        row_, column = divmod(position, 9)
        if key in ('left', 'right'):
            return row_ * 9 + (column + (-1 if key == 'left' else 1)) % 9
        if key == 'up':
            return position - 9 if row_ else 27 if column < 5 else 28
        return position + 9 if row_ < 2 else 27 if column < 5 else 28
    return {'left': 55 - position, 'right': 55 - position,
            'up': 18 if position == 27 else 25,
            'down': 28 if position == 27 else 7}[key]


def keyboard_position(driver, repo, target):
    from collections import deque
    current = memory(driver, 3, WORK + 12, 1)[0]
    pending, visited = deque([(current, [])]), {current}
    while pending:
        position, path = pending.popleft()
        if position == target:
            break
        for key in ('up', 'down', 'left', 'right'):
            neighbor = keyboard_neighbor(position, key)
            if neighbor not in visited:
                visited.add(neighbor)
                pending.append((neighbor, path + [key]))
    else:
        raise AssertionError('Keyboard key is unreachable')
    for key in path:
        press(driver, key)
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=2)
    if memory(driver, 3, WORK + 12, 1)[0] != target:
        raise AssertionError('Keyboard cursor differs from the navigation model')


def finish_text(driver, repo):
    previous = memory(driver, 3, WORK + 16, 13)
    press(driver, 'start')
    reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
    driver.run(frames=2)
    if memory(driver, 3, WORK + 12, 1)[0] != 28 or memory(driver, 3, WORK + 16, 13) != previous:
        raise AssertionError('Start did not highlight END without accepting the draft')
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesSearch_Update')
    driver.run(frames=4)
    form_audit(driver, repo)


def keyboard(driver, repo, text):
    row(driver, repo, 1)
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
    driver.run(frames=4)
    while memory(driver, 3, WORK + 13, 1)[0]:
        press(driver, 'b')
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=2)
    for character in text:
        target = 'abcdefghijklmnopqrstuvwxyz -'.index(character.lower())
        desired_case = int(not character.isupper())
        if memory(driver, 3, WORK + 14, 1)[0] != desired_case:
            press(driver, 'select')
            reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
            driver.run(frames=2)
        keyboard_position(driver, repo, target)
        press(driver, 'a')
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=2)
        keyboard_audit(driver, repo)
    expected = encode(text[:12]) + b'\x50'
    if memory(driver, 3, WORK + 32, len(expected)) != expected or memory(driver, 3, WORK + 13, 1)[0] != min(12, len(text)):
        raise AssertionError('Keyboard text or twelve-character bound differs')
    if len(text) == 12 and memory(driver, 3, WORK + 12, 1)[0] != 28:
        raise AssertionError('Reaching the character limit did not highlight END')
    finish_text(driver, repo)


def keyboard_navigation(driver, repo):
    for case in range(2):
        if memory(driver, 3, WORK + 14, 1)[0] != case:
            press(driver, 'select')
            reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
            driver.run(frames=2)
        for position in range(29):
            for key in ('up', 'down', 'left', 'right'):
                keyboard_position(driver, repo, position)
                expected = keyboard_neighbor(position, key)
                press(driver, key)
                reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
                driver.run(frames=2)
                if memory(driver, 3, WORK + 12, 1)[0] != expected:
                    raise AssertionError(f'Keyboard {key} from {position}/{case} differs')
                keyboard_audit(driver, repo)
    keyboard_position(driver, repo, 0)


def keyboard_audit(driver, repo):
    ui = driver.command('ui')
    tiles, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    case = memory(driver, 3, WORK + 14, 1)[0]
    alphabet = 'abcdefghijklmnopqrstuvwxyz ' if case else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ '
    for position, code in enumerate(encode(alphabet)):
        row_, column = divmod(position, 9)
        at = (8 + row_ * 2) * 21 + 2 + column * 2
        if tiles[at] != code or attrs[at] != 0:
            raise AssertionError(f'Keyboard glyph or case differs at {position}/{case}: '
                                 f'{tiles[at]:02x}/{attrs[at]:02x} != {code:02x}/00')
    standard_end = 'PokedexMovesSearch_StandardEndCursor' in repo.symbols
    end_column = 15 if standard_end else 16
    if tiles[14 * 21 + 2] != encode('-')[0] or tiles[15 * 21 + end_column:15 * 21 + end_column + 3] != encode('End'):
        raise AssertionError('Hyphen/END command layout differs')
    if tiles[16 * 21 + 1:16 * 21 + 19] != bytes([0x39]) * 18:
        raise AssertionError('Expanded keyboard bottom border differs')
    if any(attrs[row_ * 21 + 19] != 8 for row_ in range(8, 16)):
        raise AssertionError('Expanded right border attributes differ')
    position = memory(driver, 3, WORK + 12, 1)[0]
    if position == 28:
        if standard_end:
            y, x = 136, 120
            at = offset(repo.symbols['SpriteAnimOAMData.OAMData_TextEntryCursorBig'])
            data = repo.rom[at:at + 41]
            if data[0] != 10:
                raise AssertionError('Standard naming command box no longer has ten sprites')
            shape = [(int.from_bytes(data[i:i + 1], signed=True),
                      int.from_bytes(data[i + 1:i + 2], signed=True), data[i + 2], data[i + 3])
                     for i in range(1, 41, 4)]
        else:
            y, x = 136, 136
            shape = [(-1, -1, 0, 0), (-1, 0, 1, 0), (-1, 8, 1, 0), (-1, 16, 0, 32),
                     (0, -1, 0, 64), (0, 0, 1, 64), (0, 8, 1, 64), (0, 16, 0, 96)]
    else:
        y, x = 80 + position // 9 * 16, 24 + position % 9 * 16
        shape = [(-1, -1, 0, 0), (-1, 0, 0, 32), (0, -1, 0, 64), (0, 0, 0, 96)]
    expected = bytes(value for dy, dx, tile, flags in shape
                     for value in (y + dy, x + dx, 0x76 + tile, 8 | flags))
    cursor_states = (expected.ljust(160, b'\0'), bytes(160)) if 'PokedexMovesSearch_AnimateTextCursor' in repo.symbols else (
        expected.ljust(160, b'\0'),)
    if bytes.fromhex(ui['oam']) not in cursor_states or (ui['scx'], ui['wx']) != (0, 167):
        raise AssertionError('Keyboard cursor or viewport differs')
    at = offset(repo.symbols['NamingScreenGFX_Cursor'])
    if bytes.fromhex(driver.command('inspectvram 1 34656 32')['bytes']) != repo.rom[at:at + 32]:
        raise AssertionError('Keyboard does not reuse the naming-screen box graphics')
    if bytes.fromhex(ui['obj_palettes'])[:8] != b'\0\0' + b'\xff\x7f' * 3:
        raise AssertionError('Keyboard box is not white')
    length = memory(driver, 3, WORK + 13, 1)[0]
    for column in range(length, 12):
        expected = 0x74 if column == length else 0x75
        if tiles[6 * 21 + 3 + column] != expected:
            raise AssertionError('Only the current text insertion position should be lowered')
    for label, tile in (('NamingScreenGFX_UnderLine', 0x74), ('NamingScreenGFX_MiddleLine', 0x75)):
        at = offset(repo.symbols[label])
        expected = bytes(value for byte in repo.rom[at:at + 8] for value in (0, 255 - byte))
        if bytes.fromhex(driver.command(f'inspectvram 1 {0x9000 + tile * 16} 16')['bytes']) != expected:
            raise AssertionError('Text dashes do not reuse the naming screen graphics')


def keyboard_controls(driver, repo, directory):
    def key(button):
        press(driver, button)
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=2)
        keyboard_audit(driver, repo)
    def check(text, case):
        expected = encode(text) + b'\x50'
        if memory(driver, 3, WORK + 32, len(expected)) != expected or memory(driver, 3, WORK + 14, 1)[0] != case:
            raise AssertionError('Text editing changed its casing or draft unexpectedly')
    check('', 0)
    keyboard_audit(driver, repo)
    capture(driver, directory / 'text-entry-uppercase.png')
    key('a')
    check('A', 0)
    key('select')
    check('A', 1)
    key('a')
    check('Aa', 1)
    key('b')
    check('A', 1)
    key('b')
    check('', 1)
    key('b')
    check('', 1)
    capture(driver, directory / 'text-entry-lowercase.png')
    keyboard_position(driver, repo, 27)
    key('a')
    keyboard_position(driver, repo, 26)
    key('a')
    check('- ', 1)
    key('b')
    key('b')
    key('start')
    check('', 1)
    capture(driver, directory / 'text-entry-end.png')
    key('select')
    check('', 0)
    finish_text(driver, repo)
    if memory(driver, 3, WORK + 16, 1) != b'\x50':
        raise AssertionError('Empty END did not clear the name filter')
    row(driver, repo, 1)
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
    driver.run(frames=4)
    check('', 0)
    keyboard_navigation(driver, repo)
    keyboard_audit(driver, repo)
    finish_text(driver, repo)
    keyboard(driver, repo, 'AbCdEfGhIjKl')
    keyboard(driver, repo, 'AbCdEfGhIjKlZ')
    if memory(driver, 3, WORK + 16, 13) != encode('AbCdEfGhIjKl') + b'\x50':
        raise AssertionError('The thirteenth character escaped the bound')
    row(driver, repo, 1)
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
    driver.run(frames=4)
    check('AbCdEfGhIjKl', 0)
    capture(driver, directory / 'text-entry-populated.png')
    finish_text(driver, repo)
    keyboard(driver, repo, '')
    return dict(navigation=232, default_uppercase=True, case_preserves_text=True,
                backspace_to_empty_preserves_case=True, empty_backspace_noop=True,
                start_highlights_end=True, end_accepts_empty=True, character_limit=12,
                reopening_uppercase=True, mixed_case=True, hyphen_space=True)


def search(driver, repo):
    row(driver, repo, 2)
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesMode_Update', frames=600)
    driver.run(frames=4)


def audit_results(driver, repo, manifest, indices):
    ui, current = driver.command('ui'), state(driver, repo)
    count = int.from_bytes(memory(driver, 3, WORK + 1, 2), 'little')
    raw = memory(driver, 3, RESULTS, count * 2) if count else b''
    actual = [int.from_bytes(raw[n:n + 2], 'little') for n in range(0, len(raw), 2)]
    if actual != indices or memory(driver, 3, WORK, 1) != b'\x01':
        raise AssertionError('Normal-input results differ')
    if count:
        expected = dict(manifest)
        expected['result_order'] = indices
        expected['fixture'] = 'mixed'
        snapshot = memory(driver, 3, repo.symbols['wPokedexInfoGFX'][1] + 576, 64)
        expected['unknown'] = [i for i in range(1, 334) if not snapshot[(i - 1) // 8] & (1 << ((i - 1) & 7))]
        audit(driver, repo, expected)
    else:
        if any(bytes.fromhex(ui['oam'])[:24]):
            raise AssertionError('Empty results leaked old icons')
    if (ui['scx'], ui['wx']) != (5, 167):
        raise AssertionError('Results viewport differs')
    oam = bytes.fromhex(ui['oam'])
    maximum = max(0, count - 8)
    y = 20 + (current['scroll'] * 65 + maximum // 2) // maximum if maximum else 20
    if oam[24:28] != bytes((y, 160, 15, 3)):
        raise AssertionError('Variable-count scrollbar differs')
    footer_audit(driver, repo)
    return current


def footer_audit(driver, repo):
    at = offset(repo.symbols['PokedexMovesSearchFooterGFX'])
    source = repo.rom[at:at + 128]
    rows = [[sum(((source[(x // 8) * 16 + y * 2 + plane] >> (7 - x % 8)) & 1) << plane
                 for plane in range(2)) for x in range(64)] for y in range(8)]
    if any(pixel != 1 for row_ in rows for pixel in row_[:3]):
        raise AssertionError('Footer source has no margin for a lossless 3px shift')
    shifted = [row_[3:] + [1] * 3 for row_ in rows]
    expected = bytes(sum(((shifted[y][tile * 8 + x] >> plane) & 1) << (7 - x) for x in range(8))
                     for tile in range(8) for y in range(8) for plane in range(2))
    if bytes.fromhex(driver.command('inspectvram 1 38784 128')['bytes']) != expected:
        raise AssertionError('Search Results footer is not shifted exactly 3px left')


def options_audit(driver, repo):
    tiles, attrs = (bytes.fromhex(driver.command('ui')[key]) for key in ('map', 'attrs'))
    if tiles[4 * 21 + 7:4 * 21 + 18] != b'\x32' * 11:
        raise AssertionError('Options middle row exposes the underlying Moves list')
    for row_, label in ((3, 'Sort'), (5, 'Search')):
        if tiles[row_ * 21 + 8:row_ * 21 + 8 + len(label)] != encode(label):
            raise AssertionError('Options label differs')
    for row_ in range(3, 6):
        if attrs[row_ * 21 + 7:row_ * 21 + 18] != bytes(11):
            raise AssertionError('Options interior retains background tile attributes')


def pokemon_form_audit(driver, repo):
    tiles = bytes.fromhex(driver.command('ui')['map'])
    for row_, label in ((4, 'Type1'), (6, 'Type2')):
        if tiles[row_ * 21 + 2:row_ * 21 + 7] != encode(label):
            raise AssertionError('Pokemon Search parameter label did not move left')
        if tiles[row_ * 21 + 7] != 0x3d or tiles[row_ * 21 + 16] != 0x3e:
            raise AssertionError('Pokemon Search parameter arrows did not move left')


def baseline_visual_reproduction(output):
    previous = Path(json.loads((output / 'moves-mode-manifest.json').read_text())['visual_rollback'])
    config = json.loads((previous / 'search-tests/config.json').read_text())
    repo = repository(previous)
    directory = output / 'search-tests/visual/baseline'
    directory.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['visual_core'], config['rom'], BOOT,
                    previous / 'all-seen-tests.sav', directory / 'ui.log')
    findings = []
    try:
        bootstrap(driver)
        enter(driver, repo)
        if bytes.fromhex(driver.command('ui')['oam'])[1] == 10:
            findings.append('moves-type-badge-1px-left-of-requested-position')
        press(driver, 'start')
        reach(driver, repo, 'PokedexMovesSearch_OptionsUpdate')
        driver.run(frames=4)
        try:
            options_audit(driver, repo)
        except AssertionError:
            findings.append('options-middle-row-retains-background-text')
        capture(driver, directory / 'options.png')
        press(driver, 'down')
        press(driver, 'a')
        reach(driver, repo, 'PokedexMovesSearch_Update')
        driver.run(frames=4)
        try:
            form_audit(driver, repo)
        except AssertionError:
            findings.append('search-rows-and-empty-name-placeholder-misaligned')
        capture(driver, directory / 'form.png')
        row(driver, repo, 1)
        press(driver, 'a')
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=4)
        ui = driver.command('ui')
        if not any(bytes.fromhex(ui['oam'])):
            findings.append('keyboard-uses-background-arrow-not-naming-box')
        slots = bytes.fromhex(ui['map'])[6 * 21 + 3:6 * 21 + 15]
        if slots == bytes([0x74]) * 12:
            findings.append('all-text-slots-lowered-instead-of-current-slot-only')
        capture(driver, directory / 'keyboard.png')
        press(driver, 'start')
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        press(driver, 'a')
        reach(driver, repo, 'PokedexMovesSearch_Update')
        row(driver, repo, 0)
        for key in ('right', 'right', 'left', 'left', 'left'):
            press(driver, key)
            reach(driver, repo, 'PokedexMovesSearch_Update')
            driver.run(frames=2)
        search(driver, repo)
        at = offset(repo.symbols['TMHMCaseCategoryIconGFX'])
        expected = repo.rom[at:at + 96]
        if bytes.fromhex(driver.command('inspectvram 1 33536 96')['bytes']) != expected:
            findings.append('search-overwrites-category-resident-graphics')
        try:
            footer_audit(driver, repo)
        except AssertionError:
            findings.append('results-footer-not-shifted-3px-left')
        capture(driver, directory / 'results.png')
        press(driver, 'b')
        reach(driver, repo, 'PokedexMovesSearch_Update')
        press(driver, 'b')
        reach(driver, repo, 'PokedexMovesMode_Update')
        driver.run(frames=3)
        persists = bytes.fromhex(driver.command('inspectvram 1 33536 96')['bytes']) != expected
        if not persists or len(findings) != 7:
            raise AssertionError(f'Baseline defects were not reproduced: {findings}, persistence={persists}')
    finally:
        driver.close()
    return dict(findings=findings, category_corruption_persists_on_cancel=persists)


def visual_tests(output):
    from .legacy_listing import select_presentation
    from .search_qualification import slowpoke_audit
    config = json.loads((output / 'search-tests/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/visual'
    target.mkdir(exist_ok=True)
    baseline = baseline_visual_reproduction(output)
    rows, checked = [], 0
    for order in range(2):
        directory = target / f'order-{order}'
        directory.mkdir(exist_ok=True)
        driver = Driver(config['visual_core'], config['rom'], BOOT,
                        output / 'all-seen-tests.sav', directory / 'ui.log')
        try:
            bootstrap(driver)
            enter(driver, repo)
            sort(driver, repo, order)
            before = state(driver, repo)
            flags = memory(driver, *repo.symbols['wMoveDiscoverySeen'], 66)
            for selected_type in range(19):
                press(driver, 'start')
                reach(driver, repo, 'PokedexMovesSearch_OptionsUpdate')
                driver.run(frames=3)
                options_audit(driver, repo)
                if not selected_type:
                    capture(driver, directory / 'options.png')
                press(driver, 'down')
                press(driver, 'a')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                driver.run(frames=4)
                type_(driver, repo, selected_type)
                if selected_type in (0, 1):
                    capture(driver, directory / f'form-{selected_type}.png')
                search(driver, repo)
                indices = [i for i in manifest['orders'][order] if not selected_type or
                           manifest['moves'][i - 1]['type'] == manifest['types'][selected_type - 1]]
                for _ in range(max(1, len(indices))):
                    audit_results(driver, repo, manifest, indices)
                    press(driver, 'down')
                    reach(driver, repo, 'PokedexMovesMode_Update')
                    driver.run(frames=2)
                    checked += 1
                if selected_type == 0:
                    capture(driver, directory / 'results-all.png')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                driver.run(frames=3)
                form_audit(driver, repo)
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesMode_Update')
                driver.run(frames=3)
                audit(driver, repo, manifest)
                if state(driver, repo) != before or memory(driver, *repo.symbols['wMoveDiscoverySeen'], 66) != flags:
                    raise AssertionError('Repeated searches changed position, sort or discovery state')
            rows.append(dict(order=order, type_searches=19, all_moves_checked=True))
        finally:
            driver.close()
    for presentation in (0, 1):
        directory = target / f'pokemon-{presentation}'
        directory.mkdir(exist_ok=True)
        driver = Driver(config['visual_core'], config['rom'], BOOT,
                        output / 'all-seen-tests.sav', directory / 'ui.log')
        try:
            bootstrap(driver)
            if presentation:
                select_presentation(driver, presentation)
            press(driver, 'start')
            press(driver, 'down')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            driver.run(frames=3)
            pokemon_form_audit(driver, repo)
            capture(driver, directory / 'search.png')
            for field in range(2):
                for _ in range(18 if not field else 19):
                    press(driver, 'a')
                    reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                    driver.run(frames=3)
                    slowpoke_audit(driver, repo)
                    pokemon_form_audit(driver, repo)
                    checked += 1
                press(driver, 'down')
        finally:
            driver.close()
    result = dict(cases=checked, rows=rows, baseline=baseline, issues=[])
    write_json(target / 'summary.json', result)
    return {k: v for k, v in result.items() if k != 'rows'}


def transition_tests(output):
    from .mode_transitions import capture as transition_capture
    from .search_qualification import slowpoke_audit
    config = json.loads((output / 'search-tests/config.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/transitions'
    target.mkdir(exist_ok=True)
    driver = Driver(config['visual_core'], config['rom'], BOOT,
                    output / 'all-seen-tests.sav', target / 'ui.log')
    rows = {}
    try:
        bootstrap(driver)
        enter(driver, repo)
        driver.command('rawcolor')
        def capture_(name, key, label):
            ignored = ((64, 72, 88, 96),) if name == 'results-open' else ()
            if 'PokedexMovesSearch_AnimateTextCursor' in repo.symbols and name.startswith('text-'):
                end_left = 112 if 'PokedexMovesSearch_StandardEndCursor' in repo.symbols else 127
                position = memory(driver, 3, WORK + 12, 1)[0]
                if position == 28:
                    ignored += ((end_left, 119, 152, 128),)
                else:
                    x, y = 15 + position % 9 * 16, 63 + position // 9 * 16
                    ignored += ((x, y, x + 9, y + 9),)
                if name == 'text-end-shortcut':
                    ignored += ((end_left, 119, 152, 128),)
            rows[name] = transition_capture(driver, target, name, key,
                                            lambda: reach(driver, repo, label),
                                            ignore_regions=ignored)
            if name == 'text-end-shortcut' and rows[name]['unchanged_static_owner']:
                keyboard_audit(driver, repo)
                if memory(driver, 3, WORK + 12, 1)[0] != 28:
                    raise AssertionError('Start did not move the flashing cursor to End')
                rows[name]['issues'] = [issue for issue in rows[name]['issues']
                                       if issue != 'destination_not_displayed']
        capture_('options-open', 'start', 'PokedexMovesSearch_OptionsUpdate')
        press(driver, 'down')
        capture_('search-open', 'a', 'PokedexMovesSearch_Update')
        slowpoke_audit(driver, repo)
        row(driver, repo, 1)
        capture_('text-open', 'a', 'PokedexMovesSearch_TextUpdate')
        capture_('text-insert', 'a', 'PokedexMovesSearch_TextUpdate')
        capture_('text-delete', 'b', 'PokedexMovesSearch_TextUpdate')
        capture_('text-case', 'select', 'PokedexMovesSearch_TextUpdate')
        capture_('text-end-shortcut', 'start', 'PokedexMovesSearch_TextUpdate')
        capture_('text-accept', 'a', 'PokedexMovesSearch_Update')
        slowpoke_audit(driver, repo)
        row(driver, repo, 2)
        capture_('results-open', 'a', 'PokedexMovesMode_Update')
        capture_('results-back', 'b', 'PokedexMovesSearch_Update')
        slowpoke_audit(driver, repo)
        capture_('search-cancel', 'b', 'PokedexMovesMode_Update')
    finally:
        driver.close()
    result = dict(cases=len(rows), rows=rows,
                  issues=[name + ':' + issue for name, row_ in rows.items() for issue in row_['issues']])
    write_json(target / 'summary.json', result)
    if result['issues']:
        raise AssertionError(result['issues'])
    return dict(cases=len(rows), issues=[])


def ui_tests(output):
    config = json.loads((output / 'search-tests/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/ui'
    target.mkdir(exist_ok=True)
    rows = []
    for seen_count in (0, 1, 2, 7, 8, 9, 50, 255, 256, 333):
        directory = target / f'seen-{seen_count}'
        directory.mkdir(exist_ok=True)
        seen = set(range(1, seen_count + 1))
        battery = directory / 'input.sav'
        battery.write_bytes(seed_records((output / 'all-seen-tests.sav').read_bytes(), repo.symbols, move_bitmap(seen)))
        driver = Driver(config['visual_core'], config['rom'], BOOT, battery, directory / 'ui.log')
        try:
            bootstrap(driver)
            enter(driver, repo)
            sort(driver, repo, seen_count % 2)
            press(driver, 'right')
            driver.run(frames=4)
            before = state(driver, repo)
            canonical = memory(driver, *repo.symbols['wMoveDiscoverySeen'], 66)
            open_search(driver, repo)
            if seen_count == 333:
                capture(driver, directory / 'form.png')
                row(driver, repo, 1)
                press(driver, 'a')
                reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
                driver.run(frames=4)
                controls = keyboard_controls(driver, repo, directory)
                type_(driver, repo, 0)
                keyboard(driver, repo, 'DoUbLe')
                capture(driver, directory / 'form-double.png')
                search(driver, repo)
                expected = [i for i in manifest['orders'][before['sort']] if 'double' in manifest['moves'][i - 1]['name'].lower()]
                audit_results(driver, repo, manifest, expected)
                capture(driver, directory / 'results-double.png')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                driver.run(frames=4)
                keyboard(driver, repo, 'DOUBLE')
                if memory(driver, 3, WORK + 16, 7) != encode('DOUBLE') + b'\x50':
                    raise AssertionError('Uppercase entry was not retained')
                type_(driver, repo, 1)
                search(driver, repo)
                audit_results(driver, repo, manifest, [])
                capture(driver, directory / 'results-empty.png')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                driver.run(frames=4)
                keyboard(driver, repo, 'poison')
                type_(driver, repo, 14)
                search(driver, repo)
                combined = [i for i in manifest['orders'][before['sort']] if
                            manifest['moves'][i - 1]['type'] == 'POISON' and
                            'poison' in manifest['moves'][i - 1]['name'].lower()]
                audit_results(driver, repo, manifest, combined)
                capture(driver, directory / 'results-poison.png')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                driver.run(frames=4)
                keyboard(driver, repo, 'abcdefghijkla')
                if memory(driver, 3, WORK + 16, 13) != encode('abcdefghijkl') + b'\x50':
                    raise AssertionError('Full-length confirmation changed the query')
                keyboard(driver, repo, '')
            type_(driver, repo, 0)
            search(driver, repo)
            expected = [i for i in manifest['orders'][before['sort']] if i in seen]
            current = audit_results(driver, repo, manifest, expected)
            if seen_count == 333:
                capture(driver, directory / 'results-all.png')
            for key in ('up', 'down', 'right', 'left', 'down', 'up'):
                old = state(driver, repo)
                expected_scroll, expected_cursor = old['scroll'], old['cursor']
                if seen_count:
                    if key == 'up':
                        if expected_cursor:
                            expected_cursor -= 1
                        elif expected_scroll:
                            expected_scroll -= 1
                        else:
                            expected_scroll, expected_cursor = max(0, seen_count - 8), min(7, seen_count - 1)
                    elif key == 'down':
                        if expected_scroll + expected_cursor == seen_count - 1:
                            expected_scroll = expected_cursor = 0
                        elif expected_cursor == 7:
                            expected_scroll += 1
                        else:
                            expected_cursor += 1
                    else:
                        expected_scroll = max(0, min(max(0, seen_count - 8), expected_scroll + (8 if key == 'right' else -8)))
                press(driver, key)
                reach(driver, repo, 'PokedexMovesMode_Update')
                driver.run(frames=3)
                current = audit_results(driver, repo, manifest, expected)
                if (current['scroll'], current['cursor']) != (expected_scroll, expected_cursor):
                    raise AssertionError(f'Results {key} did not follow the expected wrapping/page rule')
                if current['scroll'] > max(0, seen_count - 8) or (seen_count and current['scroll'] + current['cursor'] >= seen_count):
                    raise AssertionError('Result navigation escaped its bounds')
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesSearch_Update')
            driver.run(frames=3)
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesMode_Update')
            driver.run(frames=3)
            if state(driver, repo) != before:
                raise AssertionError('Search did not restore the original list position/panel')
            if memory(driver, *repo.symbols['wMoveDiscoverySeen'], 66) != canonical:
                raise AssertionError('Search changed discoveries')
            rows.append(dict(seen=seen_count, order=before['sort'], navigation_checks=6, normal_input=True,
                             **(dict(keyboard=controls) if seen_count == 333 else {})))
        finally:
            driver.close()
    result = dict(cases=len(rows), rows=rows, issues=[])
    write_json(output / 'search-tests/ui.json', result)
    return result


def navigation_tests(output):
    from concurrent.futures import ProcessPoolExecutor
    config = json.loads((output / 'search-tests/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    target = output / 'search-tests/navigation'
    target.mkdir(exist_ok=True)
    visual = dict(config, core=config['visual_core'], battery=str(output / 'all-seen-tests.sav'))
    jobs = [(visual, manifest, order, str(target)) for order in range(2)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(sweep, jobs)) + list(pool.map(page_sweep, jobs))
    result = dict(cases=sum(r['cases'] for r in rows), rows=rows,
                  issues=[issue for r in rows for issue in r['issues']])
    write_json(target / 'summary.json', result)
    if result['issues']:
        raise AssertionError(result['issues'])
    return result


def surrounding_tests(output):
    from .legacy_listing import select_presentation, open_mode_screen
    from .listing_options import listing_audit, order_audit, LABELS
    from .description_ui import settle
    from .info_ui import ready as info_ready, type_audit
    from .moves_ui import ready as selected_moves_ready
    from .search_qualification import slowpoke_audit, choose_types, named_types, expected_results, results_audit, selector_types
    from .moves_sort_memory import close_dex, save_visual
    config = json.loads((output / 'search-tests/config.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/surrounding'
    target.mkdir(exist_ok=True)
    orders = json.loads((output / 'sort-manifest.json').read_text())
    rows = []
    for presentation in (0, 1):
        directory = target / str(presentation)
        directory.mkdir(exist_ok=True)
        driver = Driver(config['visual_core'], config['rom'], BOOT,
                        output / 'all-seen-tests.sav', directory / 'ui.log')
        try:
            bootstrap(driver)
            if presentation:
                select_presentation(driver, presentation)
            enter(driver, repo)
            open_search(driver, repo)
            type_(driver, repo, 0)
            search(driver, repo)
            press(driver, 'select')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            driver.run(frames=4)
            press(driver, 'b')
            driver.run(('listing',), frames=600)
            driver.run(('end_loop',))
            order = order_audit(driver, repo, orders['orders'][LABELS[0]])
            listing_audit(driver, repo, order)
            driver.run(('selected',), frames=600, key='a')
            settle(driver)
            first_name = orders['orders'][LABELS[0]][0].lower()
            if type_audit(repo, first_name, driver.command('ui')):
                raise AssertionError('Selected Pokemon picture/type restoration differs')
            press(driver, 'right')
            press(driver, 'a')
            info_ready(driver, 0)
            press(driver, 'right')
            press(driver, 'a')
            selected_moves_ready(driver, 0)
            press(driver, 'b')
            driver.run(('listing',), frames=600)
            driver.run(('end_loop',))
            press(driver, 'start')
            press(driver, 'down')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            slowpoke_audit(driver, repo)
            selected = named_types(repo, 'WATER', 'ICE')
            choose_types(driver, repo, *selected)
            press(driver, 'down')
            expected = expected_results(orders['orders'][LABELS[0]], selected, (), True, selector_types(repo))
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            results_audit(driver, repo, expected)
            press(driver, 'down')
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            results_audit(driver, repo, expected)
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            slowpoke_audit(driver, repo)
            press(driver, 'b')
            driver.run(('listing',), frames=600)
            driver.run(('end_loop',))
            listing_audit(driver, repo, order)
            enter(driver, repo)
            close_dex(driver, repo)
            saved = directory / 'normal-save.sav'
            save_visual(driver, repo, saved)
            for prefix in ('s', 'sBackup'):
                if decode_record(saved.read_bytes(), repo.symbols, prefix)['bitmap'] != move_bitmap(range(1, 334)):
                    raise AssertionError('Search/normal Save changed discoveries')
            rows.append(dict(presentation=presentation, pokemon_results=len(expected),
                             selected_views=['description', 'info', 'moves'], normal_save=True))
        finally:
            driver.close()
        reloaded = Driver(config['visual_core'], config['rom'], BOOT, saved, directory / 'reload.log')
        try:
            bootstrap(reloaded)
            enter(reloaded, repo)
            if memory(reloaded, *repo.symbols['wMoveDiscoverySeen'], 64) != move_bitmap(range(1, 334)):
                raise AssertionError('Normal Continue after Search lost discoveries')
        finally:
            reloaded.close()
    result = dict(cases=len(rows), rows=rows, issues=[])
    write_json(target / 'summary.json', result)
    return result


def form_polish_tests(output):
    from .move_acquisition import fixture, ram
    from .search_qualification import slowpoke_audit
    config = json.loads((output / 'search-tests/config.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/form-polish'
    target.mkdir(exist_ok=True)
    driver = boot(config, output / f'{STEM}.sav', target / 'native.log')
    native_cases = 0
    coordinates = ((4, 1), (6, 1), (13, 2), (15, 2))
    try:
        original = read(driver, repo.symbols)
        for row_, (y, x) in enumerate(coordinates):
            for bank in range(8):
                fixture(driver, repo.symbols, 'wDexArrowCursorPosIndex', [row_])
                fixture(driver, repo.symbols, 'wDexArrowCursorBlinkCounter', [0])
                driver.command(f'io 65392 {bank}')
                for phase in range(32):
                    returned = call(driver, repo.symbols, 'PokedexMovesSearch_BlinkCursor')
                    address = repo.symbols['wTilemap'][1] + y * 20 + x
                    actual = bytes.fromhex(driver.command(f'read 0 {address} 1')['bytes'])[0]
                    if actual != (0xed if not phase & 8 else 0x7f):
                        raise AssertionError('Moves cursor differs from standard eight-update blink phases')
                    if ram(driver, repo.symbols, 'wDexArrowCursorBlinkCounter') != bytes([phase + 1]):
                        raise AssertionError('Moves cursor blink counter differs from Pokemon Search')
                    if returned['svbk'] & 7 != bank:
                        raise AssertionError('Blink helper lost its incoming WRAM bank')
                    native_cases += 1
        if read(driver, repo.symbols) != original:
            raise AssertionError('Blinking changed move discoveries')
    finally:
        driver.close()
    driver = Driver(config['visual_core'], config['rom'], BOOT,
                    output / 'all-seen-tests.sav', target / 'ui.log')
    hardware_frames = 0
    try:
        bootstrap(driver)
        enter(driver, repo)
        manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
        audit(driver, repo, manifest)
        capture(driver, target / 'compact-footer.png')
        open_search(driver, repo)
        type_(driver, repo, 0)
        for text, label in (('', 'blank'), ('TAC', 'tac'), ('AbCdEfGhIjKl', 'twelve')):
            keyboard(driver, repo, text)
            form_audit(driver, repo)
            capture(driver, target / f'name-{label}.png')
        keyboard(driver, repo, 'TAC')
        type_(driver, repo, 1)
        for selected, (y, x) in enumerate(coordinates):
            row(driver, repo, selected)
            slowpoke_audit(driver, repo)
            phases = set()
            for _ in range(64):
                driver.run(frames=1)
                form_audit(driver, repo)
                tiles = bytes.fromhex(driver.command('ui')['map'])
                code = tiles[y * 21 + x]
                if code not in phases:
                    capture(driver, target / f'cursor-{selected}-{"visible" if code == 0xed else "hidden"}.png')
                phases.add(code)
                hardware_frames += 1
            if phases != {0xed, 0x7f}:
                raise AssertionError('Search cursor does not blink on the rendered screen')
        row(driver, repo, 1)
        for _ in range(20):
            tiles = bytes.fromhex(driver.command('ui')['map'])
            if tiles[6 * 21 + 1] == 0xed:
                break
            driver.run(frames=1)
        capture(driver, target / 'search-tac.png')
    finally:
        driver.close()
    result = dict(cases=native_cases + hardware_frames + 4, native_blink_cases=native_cases,
                  hardware_frames=hardware_frames, populated_name_column=7,
                  placeholder_column=10, shortened_footer=True, start_unchanged=True, issues=[])
    write_json(target / 'summary.json', result)
    return result


def naming_cursor_tests(output):
    from itertools import groupby
    from PIL import Image
    from .cold_listing import KEY
    from .move_acquisition import fixture, ram
    config = json.loads((output / 'search-tests/config.json').read_text())
    repo = repository(output)
    target = output / 'search-tests/naming-cursor'
    target.mkdir(exist_ok=True)
    runs = lambda values: [len(list(group)) for _, group in groupby(values)]
    reference = {}
    driver = boot(config, output / f'{STEM}.sav', target / 'naming-reference.log')
    try:
        bank, address = repo.symbols['NamingScreen']
        driver.command(f'begin {bank} {address} 256 {RESULTS}')
        bank, address = repo.symbols['NamingScreenJoypadLoop']
        def advance(key=0):
            elapsed = 0
            while elapsed < 140448:
                row_ = driver.command(f'until {bank} {address} 180 {key}')
                if not row_['hit']:
                    raise AssertionError('Regular naming cursor loop did not advance')
                # An interrupt can return to this breakpoint before the call executes.
                elapsed += row_['elapsed']
            return elapsed / 140448
        for _ in range(2):
            advance()
        for kind in ('letter', 'end'):
            if kind == 'end':
                advance(KEY['start'])
                advance()
            phases, intervals, evidence = [], [], []
            for _ in range(64):
                oam = ram(driver, repo.symbols, 'wShadowOAM', 160)
                phases.append(any(oam[i + 2] in (0x7e, 0x7f) for i in range(0, 160, 4) if oam[i]))
                evidence.append(oam.hex())
                intervals.append(advance())
            write_json(target / f'reference-{kind}.json', dict(phases=phases, intervals=intervals, oam=evidence))
            if set(phases) != {False, True} or set(runs(phases)[1:-1]) != {2}:
                raise AssertionError(f'Regular naming cursor differs from its two-update frameset: {kind}/{runs(phases)}')
            if not all(1.7 < n < 2.3 for n in intervals):
                raise AssertionError('Naming cursor no longer advances every two display frames')
            reference[kind] = dict(samples=64, visible_updates=2, hidden_updates=2,
                                   visible_display_frames=4, hidden_display_frames=4)
    finally:
        driver.close()

    driver = boot(config, output / f'{STEM}.sav', target / 'native.log')
    native_checks = 0
    try:
        original = read(driver, repo.symbols)
        driver.command('io 65392 3')
        shared_before = ram(driver, repo.symbols, 'wSpriteAnimData',
                               repo.symbols['wSpriteAnimDataEnd'][1] - repo.symbols['wSpriteAnimData'][1])
        for case in range(2):
            fixture_at(driver, WORK + 14, [case])
            for position in range(29):
                fixture_at(driver, WORK + 12, [position])
                call(driver, repo.symbols, 'PokedexMovesSearch_InitTextCursor')
                call(driver, repo.symbols, 'PokedexMovesSearch_DrawTextCursor')
                # Independent instance of the same native frameset, not a copied blink algorithm.
                instance = bytearray(16)
                instance[1], instance[10] = (9 if position == 28 else 8), 255
                fixture_at(driver, RESULTS + 16, instance)
                def reference_frame():
                    frame = call(driver, repo.symbols, 'GetSpriteAnimFrame', bc=RESULTS + 16)
                    # The native runner's FarCall also replaces A with the caller bank.
                    return repo.rom[offset((repo.symbols['GetSpriteAnimFrame'][0], frame['hl'] - 1))]
                visible = reference_frame()
                phases = set()
                for step in range(1, 33):
                    if not step % 2:
                        visible = reference_frame()
                    fixture(driver, repo.symbols, 'wCurSpriteOAMFlags', [0x55])
                    call(driver, repo.symbols, 'PokedexMovesSearch_AnimateTextCursor')
                    actual = native_read(driver, WORK + 45, 1)[0]
                    phases.add(actual == 0xfd)
                    oam = ram(driver, repo.symbols, 'wShadowOAM', 160)
                    if (actual == 0xfd) != (visible == 0xfd) or bool(any(oam)) != (visible != 0xfd):
                        raise AssertionError('Dex keyboard does not follow the naming frameset')
                    if ram(driver, repo.symbols, 'wCurSpriteOAMFlags') != b'\x55':
                        raise AssertionError('Cursor changed shared sprite-engine flags')
                    before = native_read(driver, RESULTS, 16)
                    timer = native_read(driver, WORK + 15, 1)
                    call(driver, repo.symbols, 'PokedexMovesSearch_DrawTextCursor')
                    if native_read(driver, RESULTS, 16) != before or native_read(driver, WORK + 15, 1) != timer:
                        raise AssertionError('Redrawing/moving the box restarted its animation')
                    native_checks += 1
                if phases != {False, True}:
                    raise AssertionError('Native cursor did not exercise both animation phases')
        fixture(driver, repo.symbols, 'wCurSpriteOAMFlags', [shared_before[
            repo.symbols['wCurSpriteOAMFlags'][1] - repo.symbols['wSpriteAnimData'][1]]])
        if ram(driver, repo.symbols, 'wSpriteAnimData', len(shared_before)) != shared_before:
            raise AssertionError('Dex cursor modified the shared sprite-animation workspace')
        if read(driver, repo.symbols) != original:
            raise AssertionError('Animating the keyboard changed move discoveries')
    finally:
        driver.close()

    driver = Driver(config['visual_core'], config['rom'], BOOT,
                    output / 'all-seen-tests.sav', target / 'ui.log')
    rendered = 0
    try:
        bootstrap(driver)
        driver.command('rawcolor')
        enter(driver, repo)
        open_search(driver, repo)
        row(driver, repo, 1)
        press(driver, 'a')
        reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
        driver.run(frames=4)
        for case in range(2):
            if memory(driver, 3, WORK + 14, 1)[0] != case:
                press(driver, 'select')
                reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
                driver.run(frames=2)
            for position in range(29):
                keyboard_position(driver, repo, position)
                phases = []
                captured = set()
                for _ in range(32):
                    driver.run(frames=1)
                    keyboard_audit(driver, repo)
                    visible = bool(any(bytes.fromhex(driver.command('ui')['oam'])))
                    phases.append(visible)
                    if position in (0, 28) and visible not in captured and len(phases) > 1 and phases[-2] == visible:
                        path = target / f'{case}-{position}-{"visible" if visible else "hidden"}.png'
                        # Capture this frame without the ordinary helper's two-frame settle.
                        driver.command(f'image {path.with_suffix(".ppm")}')
                        with Image.open(path.with_suffix('.ppm')) as picture:
                            picture.save(path)
                            picture.resize((640, 576), Image.Resampling.NEAREST).save(
                                path.with_stem(path.stem + '-4x'))
                        captured.add(visible)
                    rendered += 1
                if set(phases) != {False, True} or set(runs(phases)[1:-1]) != {4}:
                    raise AssertionError(f'Keyboard blink cadence differs at {case}/{position}: {runs(phases)}')
        finish_text(driver, repo)
        type_(driver, repo, 0)
        search(driver, repo)
        footer_audit(driver, repo)
        capture(driver, target / 'updated-footer.png')
    finally:
        driver.close()
    standard_end = 'PokedexMovesSearch_StandardEndCursor' in repo.symbols
    for case in range(2):
        for position, count in ((0, 32), (28, 94 if standard_end else 64)):
            with Image.open(target / f'{case}-{position}-visible.png') as picture:
                visible = picture.convert('RGB')
            with Image.open(target / f'{case}-{position}-hidden.png') as picture:
                hidden = picture.convert('RGB')
            changed = [(x, y) for y in range(144) for x in range(160)
                       if visible.getpixel((x, y)) != hidden.getpixel((x, y))]
            if len(changed) != count or any(visible.getpixel(pixel) != (255, 255, 255)
                                            for pixel in changed):
                raise AssertionError('Rendered cursor pixels do not match the white box phases')
            expected = (112, 119, 151, 127) if position == 28 and standard_end else (
                (127, 119, 151, 127) if position == 28 else (15, 63, 23, 71))
            bounds = (min(x for x, y in changed), min(y for x, y in changed),
                      max(x for x, y in changed), max(y for x, y in changed))
            if bounds != expected:
                raise AssertionError('Cursor pixel dimensions or placement differ')
    with Image.open(ROOT / 'gfx/pokedex/pokedex_search_results_footer.png') as image:
        pixels = image.convert('RGB')
        levels = {(255, 255, 255): 0, (170, 170, 170): 1, (85, 85, 85): 2}
        expected = bytes(sum(((levels[pixels.getpixel((tile * 8 + x, y))] >> plane) & 1) << (7 - x)
                             for x in range(8)) for tile in range(8) for y in range(8) for plane in range(2))
    at = offset(repo.symbols['PokedexMovesSearchFooterGFX'])
    if repo.rom[at:at + 128] != expected:
        raise AssertionError('Edited footer PNG was not rebuilt into this ROM')
    result = dict(cases=native_checks + rendered + 128, native_cases=native_checks,
                  rendered_frames=rendered, reference=reference, all_29_positions=True,
                  both_cases=True, phase_not_reset=True, shared_engine_unchanged=True,
                  updated_footer_linked=True, rendered_cursor_pixels=True,
                  end_matches_standard_oam=standard_end, end_width=40 if standard_end else 25,
                  end_height=9, end_column=15 if standard_end else 16,
                  visible_display_frames=4, hidden_display_frames=4,
                  issues=[])
    write_json(target / 'summary.json', result)
    return result


def tracking_tests(output):
    from . import move_acquisition, move_persistence, animation_reference
    config = json.loads((output / 'search-tests/config.json').read_text())
    target = output / 'tracking-regression'
    target.mkdir(exist_ok=True)
    (target / 'empty.sav').write_bytes(seed_records(
        (output / 'legacy-input.sav').read_bytes(), config['symbols'], bytes(64)))
    result = dict(helper_cases=move_persistence.helper_tests(config, target),
                  snapshot_cases=move_persistence.snapshot_tests(config, target), issues=[])
    write_json(target / 'summary.json', result)
    move_acquisition.qualify(output, jobs=6)
    previous_output, previous_configuration = animation_reference.OUTPUT, animation_reference.configuration
    try:
        animation_reference.OUTPUT = output / 'runtime/animation'
        animation_reference.configuration = lambda variant: dict(
            variant='acquisition', root=str(output / 'candidate'), rom=config['rom'],
            sym=config['sym'], battery=str(output / 'legacy-input.sav'), expected_double_speed=0,
            expected_battle_speed=0, fresh_battle_fixture=True, capture_images=False)
        animation_reference.prepare('acquisition', ['POUND'], 'search-form-regression', coherent=True)
    finally:
        animation_reference.OUTPUT, animation_reference.configuration = previous_output, previous_configuration
    move_acquisition.qualify(output, jobs=6, sources=True)
    return result


def host_tests(output):
    import os
    import unittest
    for name in ('MOVES_SEARCH_BUILD', 'DEX_MOVES_MODE_BUILD', 'MOVE_DISCOVERY_BUILD'):
        os.environ[name] = str(output)
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'tools.test_moves_search', 'tools.test_pokedex_moves_mode',
        'tools.test_move_discovery', 'tools.test_moves_sort_memory'])
    tests = unittest.TextTestRunner().run(suite)
    result = dict(cases=tests.testsRun, passed=tests.testsRun - len(tests.skipped) -
                  len(tests.failures) - len(tests.errors), skipped=len(tests.skipped),
                  issues=[str(row) for row in tests.failures + tests.errors])
    write_json(output / 'search-tests/host.json', result)
    if not tests.wasSuccessful():
        raise AssertionError('Host contract suite failed')
    return result


def full_regression_report(output):
    """Require fresh paired campaigns before publishing the final UI review."""
    from .performance_audio import compare_playback
    digest = sha256((output / f'{STEM}.gbc').read_bytes())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    baseline = sha256((Path(manifest['end_cursor_rollback']) / f'{STEM}.gbc').read_bytes())
    names = [f'acquisition-{name}-regression.json' for name in
             ('menus', 'gameplay', 'moves', 'audio', 'transitions', 'custom')]
    names += ['persistence-qualification.json', 'acquisition-migration.json',
              'acquisition-migration-interruptions.json', 'battle-use-qualification.json',
              'battle-use/supplemental-bide.json', 'acquisition-popup-readiness.json',
              'acquisition-performance.json']
    records, reports = {}, {}
    for name in names:
        path = output / name
        data = path.read_bytes()
        record = json.loads(data)
        if record.get('issues') or record.get('failures'):
            raise AssertionError(f'Unresolved full-regression issue: {name}')
        if record.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Full regression used a different ROM: {name}')
        if record.get('baseline_sha256', baseline) != baseline:
            raise AssertionError(f'Full regression used a different baseline: {name}')
        records[name] = record
        fields = ('cases', 'helper_cases', 'snapshot_cases', 'cold_boot_cases',
                  'lifecycle_cases', 'interrupted_write_cases', 'interrupted_repair_cases',
                  'contract_cases', 'semantic_cases', 'issues')
        reports[name] = dict(sha256=sha256(data),
                             summary={k: record[k] for k in fields if k in record})
    for name, cases in (('menus', 10), ('gameplay', 22), ('moves', 1600),
                        ('audio', 960), ('transitions', 24), ('custom', 2)):
        if records[f'acquisition-{name}-regression.json']['cases'] != cases:
            raise AssertionError(f'Incomplete {name} campaign')
    battle = records['battle-use-qualification.json']
    if (battle['contract_cases'], battle['semantic_cases']) != (4724, 400):
        raise AssertionError('Incomplete battle-use discovery campaign')
    if not all(battle['roundtrip'][k] for k in ('actual_battle_input', 'normal_save', 'cold_reload', 'dex_snapshot')):
        raise AssertionError('Battle-use Save/Continue roundtrip is incomplete')
    if records['battle-use/supplemental-bide.json']['cases'] != 8:
        raise AssertionError('Missing supplemental Bide campaign')
    if records['acquisition-migration-interruptions.json']['cases'] != 150:
        raise AssertionError('Incomplete interrupted migration campaign')
    audio_rows = records['acquisition-audio-regression.json']['results']
    # Audio execution records are ordered by build, unlike the battle records.
    audio_baseline = audio_rows[:len(audio_rows) // 2]
    audio_after = audio_rows[len(audio_rows) // 2:]
    audio_before = {(r['species'], r['context'], r['quarter']): r
                    for r in audio_baseline}
    for row in audio_after:
        key = row['species'], row['context'], row['quarter']
        if compare_playback(audio_before[key], row):
            raise AssertionError(f'Sampled cry playback changed: {key}')
    def known(rows):
        return sorted((r['species'], r['context'], r['quarter'], m['remaining'])
                      for r in rows for m in r['known_misses'])
    old_misses, new_misses = known(audio_before.values()), known(audio_after)
    if old_misses != new_misses:
        raise AssertionError('Sampled cry known misses changed')
    moves = records['acquisition-moves-regression.json']['results']
    motion = {(r['move'], r['side'], r['quarter']): r
              for r in moves if r['variant'] == 'baseline'}
    differences = [(r['requested_animations'][0]['elapsed_t'] -
                    motion[r['move'], r['side'], r['quarter']]['requested_animations'][0]['elapsed_t']) / 70224
                   for r in moves if r['variant'] == 'acquisition']
    if len(differences) != 800 or len(audio_after) != 480:
        raise AssertionError('Incomplete paired battle/audio campaign')
    custom = records['acquisition-custom-regression.json']['results']
    custom_before = {r['label']: r for r in custom[0]['rows']}
    for row in custom[1]['rows']:
        for field in ('palette_set', 'pixel_set', 'oam_set'):
            if row[field] != custom_before[row['label']][field]:
                raise AssertionError(f'Custom menu visual changed: {row["label"]}/{field}')
    custom_delta = {}
    for field in ('first', 'complete'):
        values = [r[field]['frames'] - custom_before[r['label']][field]['frames']
                  for r in custom[1]['rows'] if r[field] and custom_before[r['label']][field]]
        custom_delta[field] = dict(min=min(values), median=statistics.median(values), max=max(values))
    return dict(reports=reports, paired_audio_cases=len(audio_after),
                sampled_cry_known_misses=dict(baseline=len(old_misses), current=len(new_misses), same=True),
                first_requested_animation_delta_intervals=dict(min=min(differences),
                    median=statistics.median(differences), max=max(differences)),
                menu_input_contracts=sum(r['inputs'] for r in records['acquisition-menus-regression.json']['results']),
                custom_menu_cases=sum(r['cases'] for r in custom), custom_menu_visuals_unchanged=True,
                custom_menu_pixel_metric_delta_intervals=custom_delta,
                popup_readiness=records['acquisition-popup-readiness.json']['summary'],
                save_load_migration_timing=records['acquisition-performance.json']['summary'], issues=[])


def qualify(output):
    import re
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    suites = {name: json.loads((output / 'search-tests' / path).read_text()) for name, path in (
        ('filter', 'filter.json'), ('ui', 'ui.json'), ('navigation', 'navigation/summary.json'),
        ('transitions', 'transitions/summary.json'), ('surrounding', 'surrounding/summary.json'))}
    if manifest.get('moves_search_visual_repairs'):
        suites['visual'] = json.loads((output / 'search-tests/visual/summary.json').read_text())
        for name, path in (('sort_helpers', 'helpers.json'), ('sort_ui', 'ui/summary.json'),
                           ('sort_saves', 'saves/summary.json')):
            suites[name] = json.loads((output / 'sort-memory' / path).read_text())
        for name, path in (('tracking', 'tracking-regression/summary.json'),
                           ('acquisition_helpers', 'acquisition-qualification.json'),
                           ('acquisition_sources', 'acquisition-sources.json'),
                           ('host', 'search-tests/host.json')):
            suites[name] = json.loads((output / path).read_text())
        from .moves_search_dex_regression import qualify as dex_qualify
        pokemon_dex = dex_qualify(output)
    if manifest.get('moves_search_form_polish'):
        suites['form_polish'] = json.loads((output / 'search-tests/form-polish/summary.json').read_text())
    if manifest.get('moves_search_naming_animation'):
        suites['naming_cursor'] = json.loads((output / 'search-tests/naming-cursor/summary.json').read_text())
    if manifest.get('moves_search_standard_end'):
        full_regression = full_regression_report(output)
    if any(suite['issues'] for suite in suites.values()):
        raise AssertionError('A qualification suite has unresolved issues')
    for path, expected in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != expected:
            raise AssertionError('Protected base or production changed')
    def resources(path):
        return {name: int(value) for name, value in re.findall(
            r'^\s*(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used', path.read_text(), re.M)}
    source = Path(manifest['search_rollback'])
    before = resources(source / 'pokecrystal-dex-moves-sort-memory.map')
    after = resources(output / f'{STEM}.map')
    result = dict(rom_sha256=manifest['rom_sha256'], rollback=str(source),
                  protected_files=len(manifest['protected_inputs']), issues=[],
                  resources=after, delta={k: after[k] - before[k] for k in before},
                  suites={name: {k: v for k, v in data.items() if k not in ('rows', 'results', 'timings')}
                          for name, data in suites.items()},
                  review_files={str(p.relative_to(output)): sha256(p.read_bytes()) for p in (
                      output / f'{STEM}.gbc', output / f'{STEM}.sav',
                      output / 'all-seen-review' / f'{STEM}.gbc', output / 'all-seen-review' / f'{STEM}.sav')},
                  build_workers=4, native_navigation_workers=2,
                  battle_audio_campaign='unchanged source owners; prior qualification retained, not rerun')
    if manifest.get('keyboard_rollback'):
        keyboard_source = Path(manifest['keyboard_rollback'])
        keyboard_before = resources(keyboard_source / f'{STEM}.map')
        result.update(keyboard_rollback=str(keyboard_source),
                      keyboard_delta={k: after[k] - keyboard_before[k] for k in after})
    if manifest.get('visual_rollback'):
        visual_source = Path(manifest['visual_rollback'])
        visual_before = resources(visual_source / f'{STEM}.map')
        result.update(visual_rollback=str(visual_source),
                      visual_delta={k: after[k] - visual_before[k] for k in after})
    if manifest.get('form_rollback'):
        form_source = Path(manifest['form_rollback'])
        form_before = resources(form_source / f'{STEM}.map')
        result.update(form_rollback=str(form_source),
                      form_delta={k: after[k] - form_before[k] for k in after})
    if manifest.get('text_cursor_rollback'):
        cursor_source = Path(manifest['text_cursor_rollback'])
        cursor_before = resources(cursor_source / f'{STEM}.map')
        result.update(text_cursor_rollback=str(cursor_source),
                      text_cursor_delta={k: after[k] - cursor_before[k] for k in after})
    if manifest.get('end_cursor_rollback'):
        end_source = Path(manifest['end_cursor_rollback'])
        end_before = resources(end_source / f'{STEM}.map')
        result.update(end_cursor_rollback=str(end_source),
                      end_cursor_delta={k: after[k] - end_before[k] for k in after})
    if manifest.get('moves_search_visual_repairs'):
        result.update(pokemon_dex=pokemon_dex,
                      save_load_timing=json.loads((output / 'sort-memory/timing/summary.json').read_text())['summary'],
                      pokemon_dex_workers=6, asset_changes_required=False)
    if manifest.get('moves_search_standard_end'):
        result.update(full_regression=full_regression,
                      battle_audio_campaign='fresh current-link campaigns paired with the accepted cursor prototype')
    write_json(output / 'search-qualification.json', result)
    return {k: result[k] for k in ('rom_sha256', 'protected_files', 'delta', 'keyboard_delta', 'visual_delta', 'form_delta', 'text_cursor_delta', 'end_cursor_delta', 'issues') if k in result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'filter', 'ui', 'visual', 'navigation', 'transitions', 'surrounding', 'polish', 'cursor', 'tracking', 'host', 'qualify'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({'prepare': prepare, 'filter': filter_tests, 'ui': ui_tests, 'visual': visual_tests,
                      'navigation': navigation_tests, 'transitions': transition_tests,
                      'surrounding': surrounding_tests, 'polish': form_polish_tests,
                      'cursor': naming_cursor_tests,
                      'tracking': tracking_tests, 'host': host_tests,
                      'qualify': qualify}[args.action](args.output.resolve())))
