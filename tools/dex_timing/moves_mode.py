"""Native, normal-input checks of the visual-only Moves encyclopedia."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

from .assets import Repository, offset
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press, ready as info_ready, info_audit, type_audit
from .moves_ui import ready as moves_ready
from .description_ui import settle
from .legacy_listing import open_mode_screen, private_battery
from .listing_options import memory, listing_audit, order_audit, LABELS
from .area_ui import reach
from .dex_modes import encode, audit_menu
from .mode_transitions import capture as transition_capture
from .search_qualification import slowpoke_audit
from pokedex_info_assets import Compiler, constants


def state(driver, repo):
    bank, address = repo.symbols['wPokedexInfoGFX']
    data = memory(driver, bank, address, 18)
    return dict(sort=data[0], cursor=data[1], scroll=int.from_bytes(data[2:4], 'little'),
                selected=int.from_bytes(data[4:6], 'little'))


def enter(driver, repo, unlocked=None):
    open_mode_screen(driver)
    if unlocked is None:
        tiles = bytes.fromhex(driver.command('ui')['map'])
        unlocked = tiles[7 * 21 + 3:7 * 21 + 17] == encode('Unown Dex Mode')
    row = 3 if unlocked else 2
    current = driver.command('ui')['footer_cursor']
    for _ in range(abs(row - current)):
        press(driver, 'down' if row > current else 'up')
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesMode_Update')
    driver.run(frames=2)


def open_sort(driver, repo):
    press(driver, 'start')
    if 'PokedexMovesSearch_OptionsUpdate' in repo.symbols:
        reach(driver, repo, 'PokedexMovesSearch_OptionsUpdate')
        press(driver, 'a')
    reach(driver, repo, 'PokedexMovesMode_SortUpdate')


def sort(driver, repo, target):
    open_sort(driver, repo)
    if driver.command('ui')['footer_cursor'] != target:
        press(driver, 'down')
    press(driver, 'a')
    reach(driver, repo, 'PokedexMovesMode_Update')
    driver.run(frames=2)


def description(repo, index):
    at = offset(repo.symbols['MoveDescriptions1']) + 2 * (index - 1)
    pointer = int.from_bytes(repo.rom[at:at + 2], 'little')
    at = offset((repo.symbols['MoveDescriptions1'][0], pointer))
    chars = {name: int(value, 16) for name, value in re.findall(
        r'charmap "([^"]+)",\s*\$(\w+)', (ROOT / 'constants/charmap.asm').read_text())}
    lines = [bytearray()]
    for byte in repo.rom[at:at + 160]:
        if byte == 0x50:
            return [bytes(line) for line in lines]
        if byte in (chars['<LINE>'], chars['<NEXT>'], chars['<LF>']):
            lines.append(bytearray())
        else:
            lines[-1].append(byte)
    raise ValueError('Unterminated move description')


def audit(driver, repo, manifest):
    ui, current = driver.command('ui'), state(driver, repo)
    tiles, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    result_order = manifest.get('result_order')
    if 'PokedexMovesSearch_DrawCompactFooter' in repo.symbols and result_order is None:
        source = offset(repo.symbols['String_SELECT_MODE'])
        start = offset(repo.symbols['String_START_OPTION'])
        expected = b'\x31' + repo.rom[source:source + 7] + b'\x3c\x31' + repo.rom[start + 1:start + 10] + b'\x31'
        if tiles[17 * 21:17 * 21 + 20] != expected or any(attrs[17 * 21:17 * 21 + 20]):
            raise ValueError('Compact Moves footer changed its text, cap or Start placement')
    order = result_order if result_order is not None else manifest['orders'][current['sort']]
    unknown = set(manifest['unknown']) if manifest['fixture'] == 'mixed' else set()
    if manifest.get('persistence_stage') in (1, 2, 3):
        from move_discovery_assets import move_bitmap
        bank, address = repo.symbols['wPokedexInfoGFX']
        expected = move_bitmap(i for i in range(1, len(manifest['moves']) + 1) if i not in unknown)
        if memory(driver, bank, address + 576, 64) != expected:
            raise ValueError('Menu-lifetime discovery snapshot changed')
        bank, address = repo.symbols['wMoveDiscoverySeen']
        if memory(driver, bank, address, 64) != expected:
            raise ValueError('Moves menu changed canonical discovery flags')
    if (ui['scx'], ui['wx'], ui['wy']) != (5, 167, 0):
        raise ValueError('Moves viewport/window differs')
    scrollbar = manifest.get('scrollbar', False)
    name_column = 7 if scrollbar else 8
    for row in range(8):
        if current['scroll'] + row >= len(order):
            start = (row + 1) * 21 + name_column - 1
            if tiles[start:start + 13] != b'\x32' * 13:
                raise ValueError('Empty result row retains old text/cursor')
            continue
        index = order[current['scroll'] + row]
        name = '-----' if index in unknown else manifest['moves'][index - 1]['name']
        start = (row + 1) * 21 + name_column
        if tiles[start:start + 12] != encode(name).ljust(12, b'\x32'):
            raise ValueError(f'Move row {row} differs: index {index}')
        cursor = tiles[(row + 1) * 21 + name_column - 1]
        expected_cursor = ((0xed,0x32) if 'PokedexMovesMode_BlinkCursor' in repo.symbols else (0xed,))
        if cursor not in (expected_cursor if row == current['cursor'] else (0x32,)):
            raise ValueError('Moves cursor differs')
    index = order[current['scroll'] + current['cursor']]
    if current['selected'] != index:
        raise ValueError('Move panel identity differs')
    oam = bytes.fromhex(ui['oam'])
    if scrollbar:
        maximum = max(0, len(order) - 8)
        y = 20 + (current['scroll'] * 65 + maximum // 2) // maximum if maximum else 20
        if oam[24:28] != bytes((y, 160, 15, 3)) or any(oam[28:]):
            raise ValueError('Moves scrollbar thumb position/OAM differs')
        at = offset(repo.symbols['PokedexMovesModeScrollbarGFX'])
        if bytes.fromhex(driver.command('inspectvram 1 35744 96')['bytes']) != repo.rom[at:at + 96]:
            raise ValueError('Moves scrollbar did not retain the supplied graphics')
        for row in range(10):
            first = 0xba if row == 0 else 0xbe if row == 9 else 0xbc
            if tiles[row * 21 + 19:row * 21 + 21] != bytes((first, first + 1)):
                raise ValueError('Moves scrollbar BG tiles differ')
        expected_palette = repo.rom[offset(repo.symbols['PokedexListScrollThumbPalette']):][:8]
        if bytes.fromhex(ui['obj_palettes'])[24:32] != expected_palette:
            raise ValueError('Moves scrollbar thumb palette differs')
    if index in unknown:
        if any(oam[:24] if scrollbar else oam):
            raise ValueError('Unknown entry still has icons')
        for row in range(1, 9):
            if tiles[row * 21 + 1:row * 21 + 5] != b'\x32' * 4:
                raise ValueError('Unknown entry leaks stats')
        lines = []
    else:
        at = offset(repo.symbols['Moves1']) + (index - 1) * 6
        record = repo.rom[at:at + 6]
        effects = constants(ROOT / 'constants/move_effect_constants.asm')
        percent = lambda n: (n * 100 // 256 + 1) if n * 100 // 256 else 0
        values = ('---' if record[1] < 2 else str(record[1]),
                  '---' if record[0] == effects['EFFECT_ALWAYS_HIT'] else str(percent(record[3])),
                  str(percent(record[5])) if record[5] else '---')
        for row, label, value in zip((3, 5, 7), ('Pow', 'Acc', 'Eff'), values):
            for y, text in ((row, label), (row + 1, value)):
                start = y * 21 + 1
                if tiles[start:start + 3] != encode(text).ljust(3, b'\x32'):
                    raise ValueError(f'{label} differs for move {index}: {value}')
        types = offset(repo.symbols['CompactTypeIconGFXPointers']) + record[2] * 3
        bank = repo.rom[types]
        pointer = int.from_bytes(repo.rom[types + 1:types + 3], 'little')
        expected = bytearray(repo.rom[offset((bank, pointer)):][:64])
        for i in (0, 14):
            expected[i] |= 128
        for i in (48, 62):
            expected[i] |= 1
        for i in range(0, 64, 2):
            expected[i] = ~(expected[i] ^ expected[i + 1]) & 255
        tile = oam[2]
        if tile not in (0x28, 0x2c) or bytes.fromhex(driver.command(
                f'inspectvram 1 {0x8000 + tile * 16} 64')['bytes']) != expected:
            raise ValueError('Type icon graphics differ')
        type_x = 11 if 'PokedexMovesMode_AlignedIcons' in repo.symbols else 10
        type_oam = bytes(v for i in range(4) for v in (24, type_x + i * 8, tile + i, 9))
        category = 2 if record[1] < 2 else int(record[2] >= 20)
        category_oam = bytes(v for i in range(2) for v in (32, 18 + i * 8, 0x30 + category * 2 + i, 10))
        if oam[:24] != type_oam + category_oam or (not scrollbar and any(oam[24:])):
            raise ValueError('Type/category OAM differs')
        category_at = offset(repo.symbols['TMHMCaseCategoryIconGFX'])
        if bytes.fromhex(driver.command('inspectvram 1 33536 96')['bytes']) != repo.rom[category_at:category_at + 96]:
            raise ValueError('Category graphics were overwritten by a previous owner')
        pals = offset(repo.symbols['TypeIconPalettePointers']) + record[2] * 2
        pointer = int.from_bytes(repo.rom[pals:pals + 2], 'little')
        expected_pal = bytearray(repo.rom[offset((repo.symbols['TypeIconPalettes'][0], pointer)):][:8])
        expected_pal[2:4] = expected_pal[:2]
        hardware = bytes.fromhex(ui['obj_palettes'])
        if hardware[8:16] != expected_pal:
            raise ValueError('Type palette differs')
        label = ('TMHMCasePhysicalCategoryIconPalette', 'TMHMCaseSpecialCategoryIconPalette',
                 'TMHMCaseStatusCategoryIconPalette')[category]
        if hardware[16:24] != repo.rom[offset(repo.symbols[label]):][:8]:
            raise ValueError('Category palette differs')
        lines = description(repo, index)
    if len(lines) > 6 or any(len(line) > 19 for line in lines):
        raise ValueError(f'Description exceeds panel for move {index}')
    for row in range(6):
        line = lines[row] if row < len(lines) else b''
        start = (row + 10) * 21 + 1
        if tiles[start:start + 19] != line.ljust(19, b'\x32'):
            raise ValueError(f'Description row {row} differs for move {index}')
    for row in range(18):
        for column in range(21):
            expected = 8 if scrollbar and row < 10 and column >= 19 else 0
            if result_order is not None and row == 17 and 7 <= column < 15:
                expected = 8
            if attrs[row * 21 + column] != expected:
                raise ValueError('Moves text/borders use unexpected attributes')
    return current


def capture(driver, path):
    from PIL import Image
    driver.command('rawcolor')
    driver.run(frames=2)
    driver.command(f'image {path.with_suffix(".ppm")}')
    with Image.open(path.with_suffix('.ppm')) as image:
        image.save(path)
        image.resize((640, 576), Image.Resampling.NEAREST).save(path.with_stem(path.stem + '-4x'))


SORT_TEXT_CELLS = (0x2c, 0x2d, 0x2e, 0x2f, 0x30, 0x31, 0x78, 0x79, 0x7a,
                   0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x64, 0x65, 0x66, 0x67,
                   0x68, 0x69, 0x6a)


def font_glyph(repo, code):
    if code < 0x80:
        return bytes(8)
    at = offset(repo.symbols['Font']) + (code - 0x80) * 8
    return repo.rom[at:at + 8]


def shifted_glyph(repo, code, previous):
    shift = 7 if 'PokedexMovesMode_ShiftSortBorder' in repo.symbols else 3
    return bytes(value for left, right in zip(font_glyph(repo, previous), font_glyph(repo, code))
                 for value in (0, ~((left << shift & 255) | (right >> (8 - shift))) & 255))


def sort_text_gfx(repo):
    shift = 7 if 'PokedexMovesMode_ShiftSortBorder' in repo.symbols else 3
    result = []
    for text in ('Type     ', 'Alphabet '):
        previous = 0x7f
        for code in encode(text):
            result.append(shifted_glyph(repo, code, previous))
            previous = code
    result.append(shifted_glyph(repo, 0xed, 0x7f))
    for first in (0, 9):
        variant = bytearray(result[first])
        for row, value in enumerate(font_glyph(repo, 0xed)):
            variant[row * 2 + 1] &= ~(value << shift & 255) & 255
        result.append(bytes(variant))
    return result


def sort_border_gfx(repo):
    at = offset(repo.symbols['PokedexPopover_BorderGFX'])
    result = [bytearray(repo.rom[at + i * 16:at + (i + 1) * 16]) for i in range(8)]
    if 'PokedexMovesMode_PrepareSortText' not in repo.symbols:
        return result
    for tile in (0, 3, 4):
        result[tile] = bytes((value >> 1) | (128 if byte & 1 else 0)
                             for byte, value in enumerate(result[tile]))
    for tile in (2, 6, 7):
        result[tile] = bytes((value >> 1) | (value & 128) for value in result[tile])
    at = offset(repo.symbols['PokedexMovesModeScrollbarGFX']) + 32
    result.append(bytes(value & 127 for value in repo.rom[at:at + 16]))
    return result


def sort_right_gfx(repo, chars):
    at = offset(repo.symbols['PokedexPopover_ModernBorderGFX'])
    result = []
    scrollbar = 'PokedexMovesModeScrollbarGFX' in repo.symbols
    if scrollbar:
        source = offset(repo.symbols['PokedexMovesModeScrollbarGFX']) + 32
        uncovered = repo.rom[source:source + 16]
    for row, code in enumerate(chars):
        tile = 0 if row == 0 else 4 if row == 4 else 2
        template = repo.rom[at + tile * 16:at + (tile + 1) * 16]
        mirrored = [int(f'{value:08b}'[::-1], 2) & 0xf8 for value in template]
        if scrollbar:
            for i, byte in enumerate(uncovered):
                mirrored[i] |= byte & 7
        else:
            for y, glyph in enumerate(font_glyph(repo, code)):
                mirrored[y * 2 + 1] |= ~glyph & 7
        result.append(bytes(mirrored))
    return result


def audit_sort(driver, repo, base=None):
    ui = driver.command('ui')
    tiles, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    if (ui['scx'], ui['wx'], ui['wy']) != (5, 167, 0):
        raise ValueError('Sort popup changed the viewport')
    shifted = 'PokedexMovesMode_ShiftSortBorder' in repo.symbols
    aligned = 'PokedexMovesMode_PrepareSortText' not in repo.symbols
    top, bottom = (2, 6) if aligned else (3, 7)
    option_rows = (top + 1, top + 3)
    right_column = 18 if shifted or aligned else 19
    outer_column = 18 if aligned else 19
    for row in range(top, bottom + 1):
        for column in range(6, outer_column + 1):
            at = row * 21 + column
            expected_attr = 0
            if row in (top, bottom) or column >= right_column:
                expected_attr = 8
            if column == 6:
                expected_attr = 8 if shifted or aligned else 0x28
            if not aligned and row in option_rows and (8 <= column <= 16 or (
                    column == 7 and option_rows.index(row) == ui['footer_cursor'])):
                expected_attr = 8
            if attrs[at] != expected_attr:
                raise ValueError('Sort frame has incorrect VRAM-bank attributes')
            if shifted and column == 19:
                expected = 0x2a
            elif row == top:
                expected = 0xfa if column == 6 else 0xfc if column == right_column else 0xfb
            elif row == bottom:
                expected = 0xfe if column == 6 else 0x28 if column == right_column else 0xff
            elif column in (6, right_column):
                expected = 0xfd if column == 6 else 0x29 if shifted or aligned else 0x29 + row - 4
            else:
                if row == top + 2 or column in (17, 18):
                    if tiles[at] != 0x32:
                        raise ValueError('Sort interior differs')
                continue
            if tiles[at] != expected:
                raise ValueError('Sort frame still uses the main screen border')
    for option, row in enumerate(option_rows):
        expected = bytearray(encode(('Type', 'Alphabet')[option]).ljust(9, b'\x32')) if aligned else bytearray(
            SORT_TEXT_CELLS[option * 9:option * 9 + 9])
        selected = option == ui['footer_cursor']
        if selected and not aligned:
            expected[0] = 0x69 + option
        at = row * 21 + 8
        if tiles[at:at + 9] != expected:
            raise ValueError('Sort option text differs')
        expected_cursor = ((0xed, 0x32) if aligned and selected and
                           'PokedexMovesMode_BlinkCursor' in repo.symbols else
                           ((0xed if aligned else 0x68) if selected else 0x32,))
        if tiles[row * 21 + 7] not in expected_cursor:
            raise ValueError('Sort option cursor differs')
    def gfx(cell, bank=1):
        address = 0x9000 + (cell if cell < 128 else cell - 256) * 16
        return bytes.fromhex(driver.command(f'inspectvram {bank} {address} 16')['bytes'])

    if aligned:
        for code in set(encode('TypeAlphabet')) | {0xed}:
            expected = bytes(v for row in font_glyph(repo, code) for v in (0, row ^ 255))
            if gfx(code, 0) != expected:
                raise ValueError('Tile-aligned popup changed the native font/cursor graphics')
    else:
        for cell, expected in zip(SORT_TEXT_CELLS, sort_text_gfx(repo)):
            if gfx(cell) != expected:
                raise ValueError(f'Shifted text/cursor graphics differ in cell {cell:02x}')
    if shifted or aligned:
        for cell, expected in zip((0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff, 0x28, 0x29, 0x2a),
                                  sort_border_gfx(repo)):
            if gfx(cell) != expected:
                raise ValueError('Repacked popup border differs from supplied art')
    else:
        modern = offset(repo.symbols['PokedexPopover_ModernBorderGFX'])
        original = offset(repo.symbols['PokedexPopover_BorderGFX'])
        for cell, at in ((0xfa, modern + 16), (0xfd, modern + 48), (0xfe, modern + 80),
                         (0xfb, original + 16), (0xff, original + 80)):
            if gfx(cell) != repo.rom[at:at + 16]:
                raise ValueError('Mirrored popup border differs from supplied art')
    bank, address = repo.symbols['wPokedexInfoGFX']
    chars = memory(driver, bank, address + 34, 5) if not (shifted or aligned) else b''
    if base:
        base_tiles, base_attrs = bytes.fromhex(base['map']), bytes.fromhex(base['attrs'])
        if not (shifted or aligned) and chars != bytes(base_tiles[row * 21 + 19] for row in range(3, 8)):
            raise ValueError('Popup did not preserve the underlying right-edge glyphs')
        for row in range(18):
            for column in range(21):
                if top <= row <= bottom and 6 <= column <= outer_column:
                    continue
                at = row * 21 + column
                if tiles[at] != base_tiles[at] or attrs[at] != base_attrs[at]:
                    raise ValueError('Popup changed the surrounding page')
        for key in ('oam', 'obj_palettes', 'bg_palettes'):
            if key in base and ui[key] != base[key]:
                raise ValueError(f'Popup changed {key}')
    if not (shifted or aligned):
        for cell, expected in zip((0xfc, 0x29, 0x2a, 0x2b, 0x28), sort_right_gfx(repo, chars)):
            if gfx(cell) != expected:
                raise ValueError('Popup right edge lost the uncovered move-name pixels')


def page_sweep(task):
    config, manifest, target, output = task
    output = Path(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / f'pages-{target}.log')
    issues, cases = [], 0
    last_page = len(manifest['moves']) - 8
    try:
        bootstrap(driver)
        enter(driver, repo)
        sort(driver, repo, target)
        for row in range(8):
            if row:
                press(driver, 'down')
            for key, step, end in (('right', 8, last_page), ('left', -8, 0)):
                while True:
                    before = state(driver, repo)
                    press(driver, key)
                    current = audit(driver, repo, manifest)
                    expected = max(0, min(last_page, before['scroll'] + step))
                    if current['scroll'] != expected or current['cursor'] != row:
                        raise ValueError(f'{key} page jump differs at {before}: {current}')
                    cases += 1
                    if before['scroll'] == end:
                        break
            if state(driver, repo)['scroll']:
                raise ValueError('Left paging did not stop at the first page')
        for key, expected in (('right', last_page), ('left', 0)):
            driver.run(frames=400, key=key)
            driver.run(frames=4)
            current = audit(driver, repo, manifest)
            if current['scroll'] != expected or current['cursor'] != 7:
                raise ValueError('Held page input did not stop at the endpoint')
            cases += 1
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / f'pages-{target}-failure')
        capture(driver, output / f'pages-{target}-failure.png')
    finally:
        driver.close()
    return dict(sort=target, cases=cases, issues=issues)


def sweep(task):
    config, manifest, target, output = task
    output = Path(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / f'sweep-{target}.log')
    issues, cases = [], 0
    try:
        bootstrap(driver)
        enter(driver, repo)
        sort(driver, repo, target)
        capture(driver, output / f'moves-mode-sort-{target}.png')
        for ordinal in range(len(manifest['moves'])):
            current = audit(driver, repo, manifest)
            if current['scroll'] + current['cursor'] != ordinal:
                raise ValueError(f'Navigation skipped ordinal {ordinal}: {current}')
            if manifest['moves'][current['selected'] - 1]['symbol'] == 'DOUBLE_EDGE':
                capture(driver, output / f'double-edge-{target}.png')
            cases += 1
            base = driver.command('ui')
            open_sort(driver, repo)
            audit_sort(driver, repo, base)
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesMode_Update')
            if audit(driver, repo, manifest) != current:
                raise ValueError('Cancelling popup changed the selected move')
            cases += 1
            press(driver, 'down')
        if audit(driver, repo, manifest)['scroll']:
            raise ValueError('Down did not wrap to top')
        press(driver, 'up')
        current = audit(driver, repo, manifest)
        if current['scroll'] + current['cursor'] != len(manifest['moves']) - 1:
            raise ValueError('Up did not wrap to bottom')
        cases += 2
        sort(driver, repo, 1 - target)
        if audit(driver, repo, manifest)['scroll'] or state(driver, repo)['cursor']:
            raise ValueError('Changed sort did not reset selection')
        cases += 1
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / f'sweep-{target}-failure')
        (output / f'sweep-{target}-failure.json').write_text(json.dumps(driver.command('ui'), indent=2))
        capture(driver, output / f'sweep-{target}-failure.png')
    finally:
        driver.close()
    return dict(sort=target, cases=cases, issues=issues)


def interface_case(task):
    config, manifest, presentation, phase, fixture, output = task
    output = Path(output) / f'interface-{presentation}-{phase}'
    output.mkdir(exist_ok=True)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, fixture, output / 'trace.log')
    issues, transitions, checks = [], {}, 0
    unlocked = bool(phase & 1)
    try:
        bootstrap(driver)
        prior = phase % 4
        if prior:
            driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
            settle(driver)
            for _ in range(prior):
                press(driver, 'right')
            press(driver, 'a')
            if prior == 1:
                info_ready(driver, 0)
            elif prior == 2:
                moves_ready(driver)
            else:
                reach(driver, repo, 'Pokedex_GetArea.loop')
                reach(driver, repo, 'PokedexSelectedMon_Area.map_returned', 32)
                driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            press(driver, 'b')
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(('end_loop',))
        open_mode_screen(driver)
        row = 3 if unlocked else 2
        for _ in range(row - presentation):
            press(driver, 'down')
        driver.command('rawcolor')

        def ready():
            reach(driver, repo, 'PokedexMovesMode_Update')

        def modal_ready():
            reach(driver, repo, 'PokedexMovesMode_SortUpdate')

        def record(name, key, finish):
            driver.run(frames=phase / 8)
            transitions[name] = transition_capture(driver, output, name, key, finish)
            issues.extend(name + ':' + issue for issue in transitions[name]['issues'])

        record('enter', 'a', ready)
        audit(driver, repo, manifest)
        record('down', 'down', ready)
        if state(driver, repo)['cursor'] != 1:
            raise ValueError('First downward input was not accepted')
        audit(driver, repo, manifest)
        if phase == 0:
            capture(driver, output / 'selected-second-entry.png')
        record('up', 'up', ready)
        audit(driver, repo, manifest)
        record('page-right', 'right', ready)
        current = audit(driver, repo, manifest)
        if (current['scroll'], current['cursor']) != (8, 0):
            raise ValueError('Right did not move a full eight-row page')
        record('page-left', 'left', ready)
        current = audit(driver, repo, manifest)
        if (current['scroll'], current['cursor']) != (0, 0):
            raise ValueError('Left did not return a full eight-row page')
        base = driver.command('ui')
        record('sort-open', 'start', modal_ready)
        audit_sort(driver, repo, base)
        record('sort-highlight', 'down', modal_ready)
        audit_sort(driver, repo, base)
        capture(driver, output / 'sort-popup.png')
        record('sort-change', 'a', ready)
        if state(driver, repo)['sort'] != 1 or state(driver, repo)['scroll']:
            raise ValueError('New sort did not select its first entry')
        audit(driver, repo, manifest)
        base = driver.command('ui')
        record('sort-reopen', 'start', modal_ready)
        audit_sort(driver, repo, base)
        record('sort-cancel', 'b', ready)
        if state(driver, repo)['sort'] != 1:
            raise ValueError('Sort cancellation changed the order')
        press(driver, 'start')
        modal_ready()
        audit_sort(driver, repo)
        press(driver, 'a')
        ready()
        audit(driver, repo, manifest)
        checks += 1
        for _ in range(16):
            press(driver, 'down')
            audit(driver, repo, manifest)
            checks += 1
        before = state(driver, repo)
        press(driver, 'start')
        modal_ready()
        audit_sort(driver, repo)
        press(driver, 'a')
        ready()
        if state(driver, repo) != before:
            raise ValueError('Same-sort confirmation changed a scrolled selection')
        checks += 1
        driver.run(frames=90, key='down')
        driver.run(frames=4)
        audit(driver, repo, manifest)
        checks += 1
        for _ in range(12):
            press(driver, 'up')
            press(driver, 'down')
            audit(driver, repo, manifest)
            checks += 1
        record('return-modes', 'select' if phase & 1 else 'b',
               lambda: reach(driver, repo, 'Pokedex_UpdateOptionScreen'))
        issues += audit_menu(driver.command('ui'), unlocked, row)
        press(driver, 'b')
        if driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)['hit'] != 'listing':
            raise ValueError('Failed to return to species Listing')
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        orders = json.loads((Path(config['rom']).parent / 'sort-manifest.json').read_text())
        listing_audit(driver, repo, order_audit(driver, repo, orders['orders'][LABELS[0]]))
        if driver.command('peek')['presentation'] != presentation:
            raise ValueError('Moves Mode changed species presentation')
        checks += 1
        press(driver, 'start')
        press(driver, 'down')
        press(driver, 'a')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen')
        slowpoke_audit(driver, repo)
        press(driver, 'b')
        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        listing_audit(driver, repo, order_audit(driver, repo, orders['orders'][LABELS[0]]))
        checks += 1
        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
        settle(driver)
        view = 1 if prior == 1 else phase % 3 + 1
        for _ in range(view):
            press(driver, 'right')
        press(driver, 'a')
        if view == 1:
            ui = info_ready(driver, 0)
            compiler = Compiler()
            data = compiler.compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
            name = config['names'][driver.command('peek')['index']]
            issues += type_audit(repo, name, ui) + info_audit(compiler, data, name, 0, ui, repo)
        elif view == 2:
            moves_ready(driver)
        else:
            reach(driver, repo, 'Pokedex_GetArea.loop')
            reach(driver, repo, 'PokedexSelectedMon_Area.map_returned', 32)
            driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        press(driver, 'b')
        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        listing_audit(driver, repo, order_audit(driver, repo, orders['orders'][LABELS[0]]))
        checks += 1
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / 'failure')
    finally:
        driver.close()
    return dict(presentation=presentation, phase=phase, checks=checks,
                transitions=transitions, issues=issues)


def alignment_audit(output, baseline):
    from PIL import Image, ImageChops
    current = output / 'moves-mode-qualification'
    previous = baseline / 'moves-mode-qualification'
    old_manifest = json.loads((baseline / 'moves-mode-manifest.json').read_text())
    new_manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    old_bounds = old_manifest.get('sort_popup_bounds', [48, 24, 152, 64]
                                  if old_manifest.get('scrollbar') else [51, 24, 155, 64])
    new_bounds = new_manifest.get('sort_popup_bounds', [48, 24, 152, 64])
    cases, issues = 0, []
    for presentation in (0, 1):
        for phase in range(8):
            name = f'interface-{presentation}-{phase}'
            with Image.open(previous / name / 'sort-open/display-001.png') as image:
                expected = image.convert('RGB')
            with Image.open(previous / name / 'sort-popup.png') as image:
                expected.paste(image.crop(tuple(old_bounds)), tuple(new_bounds[:2]))
            with Image.open(current / name / 'sort-popup.png') as image:
                difference = ImageChops.difference(expected, image.convert('RGB')).getbbox()
            if difference:
                issues.append(dict(case=name, different_pixels_box=difference))
            cases += 1
    summary = dict(cases=cases, issues=issues, baseline=str(baseline),
                   old_bounds=old_bounds, new_bounds=new_bounds)
    (current / 'alignment.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def qualify(output, jobs, baseline=None):
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    config = json.loads((output / 'modern/config.json').read_text())
    target = output / 'moves-mode-qualification'
    target.mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        results = list(pool.map(sweep, [(config, manifest, order, str(target)) for order in (0, 1)]))
        pages = list(pool.map(page_sweep, [(config, manifest, order, str(target)) for order in (0, 1)]))
        tasks = []
        for presentation in (0, 1):
            for phase in range(8):
                fixture = target / f'fixture-{presentation}-{phase}.sav'
                private_battery(config, fixture, presentation=presentation, unown_unlocked=bool(phase & 1))
                tasks.append((config, manifest, presentation, phase, str(fixture), str(target)))
        interfaces = list(pool.map(interface_case, tasks))
    summary = dict(cases=sum(r['cases'] for r in results),
                   page_cases=sum(r['cases'] for r in pages),
                   interface_cases=len(interfaces), interface_checks=sum(r['checks'] for r in interfaces),
                   transitions=sum(len(r['transitions']) for r in interfaces),
                   failures=sum(bool(r['issues']) for r in results + pages + interfaces),
                   results=results, pages=pages, interfaces=interfaces)
    if baseline:
        summary['alignment'] = alignment_audit(output, baseline)
        summary['failures'] += bool(summary['alignment']['issues'])
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('results', 'pages', 'interfaces')}))
    for row in results + pages + interfaces:
        if row['issues']:
            print(json.dumps({k: v for k, v in row.items() if k != 'transitions'}))
    return int(bool(summary['failures']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    return qualify(args.output.resolve(), args.jobs, args.baseline.resolve() if args.baseline else None)


if __name__ == '__main__':
    raise SystemExit(main())
