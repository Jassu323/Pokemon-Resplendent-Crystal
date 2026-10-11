"""Independent native Unown content, blank-pixel and normal-input checks."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import random

from PIL import Image

from .assets import Repository, offset, sha256
from .cold_listing import Driver, bootstrap, audit
from .description_ui import settle
from .dex_modes import audit_menu
from .info_ui import BOOT, ready as info_ready
from .moves_ui import ready as moves_ready
from .unown_comparison import battery
from .move_persistence import boot, call, core


COORDS = ([(4, y, 3, y) for y in range(11, 3, -1)] +
          [(4, 3, 3, 2)] + [(x, 3, x, 2) for x in range(5, 14)] +
          [(14, 3, 15, 2)] + [(14, y, 15, y) for y in range(4, 11)])
STEM = 'pokecrystal-dex-unown-fix'
OUTER_CELLS = [(x, y) for y in range(18) for x in range(20)
               if not (2 <= x < 17 and (1 <= y < 13 or 14 <= y < 17))]
OUTER_RED = bytes((214, 82, 49))
BLACK_UI_PALETTE = bytes.fromhex('ff7f5a1900000000')
PORTRAIT_CELLS = {(x, y) for y in range(5, 12) for x in range(6, 13)}


def orders():
    result = {f'single-{n:02}': [n] for n in range(1, 27)}
    for n in (2, 3, 5, 8, 9, 11, 18, 19, 20, 25, 26):
        ascending = list(range(1, n + 1))
        result[f'ascending-{n:02}'] = ascending
        result[f'reversed-{n:02}'] = ascending[::-1]
        result[f'rotated-{n:02}'] = ascending[n // 2:] + ascending[:n // 2]
    result['sparse-no-a'] = [26, 8, 19, 2, 14]
    result['sparse-a-middle'] = [26, 8, 1, 19, 2, 14]
    shuffled = list(range(1, 27))
    random.Random(261011).shuffle(shuffled)
    result['shuffled-26'] = shuffled
    return result


def memory(driver, symbols, label, size=1):
    bank, address = symbols[label]
    return bytes.fromhex(driver.command(f'perfram {bank} {address} {size}')['bytes'])


def reach(driver, symbols, label):
    bank, pc = symbols[label]
    result = driver.command(f'restorerun {bank} {pc} {600 * 70224} 0')
    if result['hit'] < 0:
        raise RuntimeError(f'Timed out reaching {label}')


def press(driver, key):
    driver.run(frames=2, key=key)
    driver.run(frames=2)


def expected_picture(asset):
    picture = bytearray(49 * 16)
    for x in range(asset.width):
        for y in range(asset.width):
            source = (x * asset.width + y) * 16
            target = ((x + (asset.width != 7)) * 7 + y + 7 - asset.width) * 16
            picture[target:target + 16] = asset.dictionary[source:source + 16]
    return bytes(picture)


def word(repo, form):
    label = 'UnownWord' + chr(64 + form)
    start = offset(repo.symbols[label])
    return repo.rom[start:repo.rom.index(255, start)]


def audit_content(driver, repo, caught, index, folder, save_image, red_background=False, black_panels=False):
    symbols = repo.symbols
    ui = driver.command('ui')
    tilemap, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    issues = []
    if memory(driver, symbols, 'wDexUnownCount')[0] != len(caught):
        issues.append('wrong_caught_count')
    if memory(driver, symbols, 'wDexCurUnownIndex')[0] != index:
        issues.append('wrong_selected_index')
    if memory(driver, symbols, 'wUnownDex', 26) != bytes(caught) + bytes(26 - len(caught)):
        issues.append('caught_order_changed')
    cells = {}
    for n, (x, y, cx, cy) in enumerate(COORDS):
        cells[(x, y)] = 0xb4 + caught[n] if n < len(caught) else 0x32
        cells[(cx, cy)] = 0xcf if n == index else 0x32
    selected_word = word(repo, caught[index])
    # FIRST_UNOWN_CHAR is $40; the resident alphabet begins at $b5.
    for n in range(12):
        cells[(4 + n, 15)] = selected_word[n] - 0x40 + 0xb5 if n < len(selected_word) else 0x32
    for (x, y), tile in cells.items():
        at = y * 21 + x
        if tilemap[at] != tile or attrs[at] != 8:
            issues.append(f'overlay_tile_or_bank:{x},{y}')
    if red_background:
        for x, y in OUTER_CELLS:
            at = y * 21 + x
            if tilemap[at] != 0x31 or attrs[at] != 0:
                issues.append(f'outer_background_tile_or_bank:{x},{y}')
    black_cells = set()
    if black_panels:
        if bytes.fromhex(ui['palettes'])[:8] != BLACK_UI_PALETTE:
            issues.append('black_panel_palette')
        for y in range(18):
            for x in range(20):
                at = y * 21 + x
                if (attrs[at] & 7 == 1) != ((x, y) in PORTRAIT_CELLS):
                    issues.append(f'portrait_palette_bounds:{x},{y}')
                if 2 < x < 16 and (1 < y < 12 or y == 15) and (x, y) not in PORTRAIT_CELLS:
                    if tilemap[at] == 0x7f or (x, y) in cells and cells[(x, y)] == 0x32:
                        black_cells.add((x, y))
                        if attrs[at] & 7:
                            issues.append(f'black_panel_attribute:{x},{y}')
    font = bytes.fromhex(driver.command('inspectvram 1 35664 432')['bytes'])
    start = offset(symbols['UnownFont'])
    if font != bytes(v ^ 255 for v in repo.rom[start:start + 432]):
        issues.append('resident_font_changed')
    blank = bytes.fromhex(driver.command('inspectvram 1 37664 16')['bytes'])
    if blank != bytes((0, 255)) * 8:
        issues.append('resident_blank_changed')
    picture = bytes.fromhex(driver.command('inspectvram 0 36864 784')['bytes'])
    asset = repo.load(['unown_' + chr(96 + caught[index])])[0]
    if picture != expected_picture(asset):
        issues.append('wrong_frontpic')
    # Validate displayed pixels, not only the software map. These are native
    # captures; conversion to PNG does not recolor or replace graphics.
    path = folder / f'form-{index:02}.ppm'
    driver.command(f'image {path}')
    with Image.open(path) as image:
        pixels = image.convert('RGB')
        palette = bytes.fromhex(ui['palettes'])[:8]
        colors = []
        for n in range(4):
            value = int.from_bytes(palette[n * 2:n * 2 + 2], 'little')
            channels = [(value >> shift) & 31 for shift in (0, 5, 10)]
            colors.append(tuple((value << 3) | (value >> 2) for value in channels))
        for (x, y), tile in cells.items():
            data = blank if tile == 0x32 else font[(tile - 0xb5) * 16:(tile - 0xb4) * 16]
            expected = []
            for row in range(8):
                for column in range(8):
                    bit = 7 - column
                    color = (data[row * 2] >> bit & 1) | ((data[row * 2 + 1] >> bit & 1) << 1)
                    expected.append(colors[color])
            actual = pixels.crop((x * 8, y * 8, (x + 1) * 8, (y + 1) * 8)).tobytes()
            if actual != bytes(channel for pixel in expected for channel in pixel):
                issues.append(f'overlay_pixels:{x},{y}')
        if red_background:
            for x, y in OUTER_CELLS:
                actual = pixels.crop((x * 8, y * 8, (x + 1) * 8, (y + 1) * 8)).tobytes()
                if actual != OUTER_RED * 64:
                    issues.append(f'outer_background_pixels:{x},{y}')
        for x, y in black_cells:
            actual = pixels.crop((x * 8, y * 8, (x + 1) * 8, (y + 1) * 8)).tobytes()
            if actual != bytes(64 * 3):
                issues.append(f'black_panel_pixels:{x},{y}')
        if black_panels:
            mon_palette = bytes.fromhex(ui['palettes'])[8:16]
            mon_colors = []
            for n in range(4):
                value = int.from_bytes(mon_palette[n * 2:n * 2 + 2], 'little')
                mon_colors.append(tuple(((value >> shift & 31) << 3) | (value >> shift & 31) >> 2
                                        for shift in (0, 5, 10)))
            for x, y in PORTRAIT_CELLS:
                tile = tilemap[y * 21 + x]
                data = picture[tile * 16:(tile + 1) * 16]
                if len(data) != 16:
                    issues.append(f'portrait_tile:{x},{y}')
                    continue
                expected = bytes(channel for row in range(8) for bit in range(7, -1, -1)
                                 for channel in mon_colors[(data[row * 2] >> bit & 1) |
                                                           ((data[row * 2 + 1] >> bit & 1) << 1)])
                actual = pixels.crop((x * 8, y * 8, (x + 1) * 8, (y + 1) * 8)).tobytes()
                if actual != expected:
                    issues.append(f'portrait_pixels:{x},{y}')
        if save_image or issues:
            pixels.save(path.with_suffix('.png'))
    path.unlink()
    if issues:
        (folder / f'form-{index:02}.json').write_text(json.dumps(ui, indent=2) + '\n')
    return dict(index=index, form=caught[index], issues=issues, overlay_cells=len(cells),
                background_cells=len(OUTER_CELLS) if red_background else 0,
                black_panel_cells=len(black_cells), portrait_palette_cells=49 if black_panels else 0)


def case(task):
    config, source, target, name, caught, presentation, phase = task
    folder = Path(target) / f'{name}-p{presentation}-q{phase}'
    folder.mkdir(exist_ok=True)
    repo = Repository(source, Path(config['rom']), Path(config['sym']))
    fixture = folder / 'input.sav'
    battery(Path(config['battery']), repo.symbols, fixture, len(caught), True,
            caught_order=caught, presentation=presentation)
    before_hash = sha256(fixture.read_bytes())
    driver = Driver(config['core'], config['rom'], BOOT, fixture, folder / 'trace.log')
    issues, records = [], []
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        original = driver.command('peek')
        original_letter = memory(driver, repo.symbols, 'wUnownLetter')
        if config.get('prior_view'):
            driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
            settle(driver)
            press(driver, 'right')
            if config['prior_view'] == 'moves':
                press(driver, 'right')
            press(driver, 'a')
            if config['prior_view'] == 'info':
                info_ready(driver, 0)
            else:
                moves_ready(driver)
            press(driver, 'b')
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(('end_loop',))
        driver.run(frames=2 + phase / 8)
        press(driver, 'select')
        reach(driver, repo.symbols, 'Pokedex_UpdateOptionScreen')
        for _ in range(2 - presentation):
            press(driver, 'down')
        press(driver, 'a')
        reach(driver, repo.symbols, 'Pokedex_UpdateUnownMode')
        driver.run(frames=4)
        for index in range(len(caught)):
            record = audit_content(driver, repo, caught, index, folder, index in (0, len(caught) - 1),
                                   config.get('red_background', False), config.get('black_panels', False))
            records.append(record)
            issues.extend(f'forward-{index}:{value}' for value in record['issues'])
            if memory(driver, repo.symbols, 'wUnownLetter') != original_letter:
                issues.append('unown_letter_not_restored')
            if index + 1 < len(caught):
                press(driver, 'right')
                reach(driver, repo.symbols, 'Pokedex_UpdateUnownMode')
                driver.run(frames=4)
        press(driver, 'right')
        if memory(driver, repo.symbols, 'wDexCurUnownIndex')[0] != len(caught) - 1:
            issues.append('right_boundary_not_bounded')
        for index in range(len(caught) - 2, -1, -1):
            press(driver, 'left')
            reach(driver, repo.symbols, 'Pokedex_UpdateUnownMode')
            driver.run(frames=4)
            record = audit_content(driver, repo, caught, index, folder, False,
                                   config.get('red_background', False), config.get('black_panels', False))
            records.append(record)
            issues.extend(f'backward-{index}:{value}' for value in record['issues'])
        press(driver, 'left')
        if memory(driver, repo.symbols, 'wDexCurUnownIndex')[0]:
            issues.append('left_boundary_not_bounded')
        press(driver, 'a' if phase else 'b')
        reach(driver, repo.symbols, 'Pokedex_UpdateOptionScreen')
        issues.extend('return_menu:' + v for v in audit_menu(driver.command('ui'), True, 2))
        press(driver, 'b')
        driver.run(('listing',), frames=600)
        driver.run(('end_loop',))
        returned = driver.command('peek')
        if returned['index'] != original['index'] or returned['presentation'] != presentation:
            issues.append('listing_position_or_presentation_changed')
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept', 'animation_miss', 'audio_miss'), key='a')
        final = settle(driver)
        asset = repo.load([config['names'][original['index']]])[0]
        playback = audit(asset, accepted, driver.events, final, cold=False, expected_double_speed=1)
        issues.extend('post_return:' + value for value in playback['issues'])
        if sha256(fixture.read_bytes()) != before_hash:
            issues.append('source_battery_changed')
    except (RuntimeError, ValueError, IndexError) as error:
        issues.append(str(error))
        driver.evidence(folder / 'failure')
    finally:
        driver.close()
    result = dict(name=name, caught=caught, presentation=presentation, phase=phase,
                  checks=len(records), results=records, issues=issues)
    (folder / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def draw_units(output, target):
    symbols = Repository(output / 'candidate', output / f'{STEM}.gbc', output / f'{STEM}.sym').symbols
    config = dict(core=str(core(output, STEM, target)), rom=str(output / f'{STEM}.gbc'), symbols=symbols)
    driver = boot(config, output / f'{STEM}.sav', target / 'draw-units.log')
    red_background = json.loads((output / 'unown-manifest.json').read_text()).get('red_background', False)
    records = []
    def write(label, data):
        bank, at = symbols[label]
        driver.command(f'fixture {bank} {at} {bytes(data).hex()}')
    def read(label, size):
        bank, at = symbols[label]
        return bytes.fromhex(driver.command(f'read {bank} {at} {size}')['bytes'])
    try:
        for cgb in (0, 1):
            driver.command(f'hram {symbols["hCGB"][1]} {cgb}')
            for name, caught in dict(empty=[], **orders()).items():
                write('wUnownDex', caught + [0] * (26 - len(caught)))
                # Poison the byte after the full-capacity array to catch a lost bound.
                bank, at = symbols['wUnownDex']
                previous = driver.command(f'read {bank} {at + 26} 1')['bytes']
                driver.command(f'fixture {bank} {at + 26} ff')
                state = driver.command('run 0 0')
                result = call(driver, symbols, 'Pokedex_DrawUnownModeBG')
                tilemap = read('wTilemap', 360)
                count = read('wDexUnownCount', 1)[0]
                expected_base = 0xb5 if cgb else 0x40
                issues = []
                if count != len(caught) or result['de'] != len(caught) or result['bc'] >> 8 != len(caught):
                    issues.append('loop_count_or_registers')
                if result['bc'] & 255 != 26 - len(caught):
                    issues.append('remaining_counter')
                if read('wUnownDex', 26) != bytes(caught) + bytes(26 - len(caught)):
                    issues.append('caught_array_changed')
                if driver.command(f'read {bank} {at + 26} 1')['bytes'] != 'ff':
                    issues.append('array_guard_changed')
                if any(result[key] != state[key] for key in ('bank', 'svbk', 'sp', 'sram_enabled', 'sram_bank')):
                    issues.append('bank_stack_or_sram_not_restored')
                for n, (x, y, cx, cy) in enumerate(COORDS):
                    if n < len(caught) and tilemap[y * 20 + x] != expected_base + caught[n] - 1:
                        issues.append(f'letter:{n}')
                    if cgb and (tilemap[cy * 20 + cx] != 0x32 or
                                n >= len(caught) and tilemap[y * 20 + x] != 0x32):
                        issues.append(f'blank:{n}')
                expected_background = 0x31 if red_background and cgb else 0x32
                if any(tilemap[y * 20 + x] != expected_background for x, y in OUTER_CELLS):
                    issues.append('outer_background')
                driver.command(f'fixture {bank} {at + 26} {previous}')
                records.append(dict(cgb=cgb, name=name, count=count, issues=issues))
    finally:
        driver.close()
    (target / 'draw-units.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def run(output, jobs, smoke):
    target = output / ('unown-smoke' if smoke else 'unown-tests')
    target.mkdir(exist_ok=True)
    config = json.loads((output / 'dex-regression/modern/config.json').read_text())
    manifest = json.loads((output / 'unown-manifest.json').read_text())
    config['red_background'] = manifest.get('red_background', False)
    config['black_panels'] = manifest.get('black_panels', False)
    cases = {'ascending-26': list(range(1, 27)), 'single-01': [1]} if smoke else orders()
    tasks = [(config, str(output / 'candidate'), str(target), name, caught, presentation, phase)
             for name, caught in cases.items() for presentation in (0, 1)
             for phase in ((0, 3) if name in ('ascending-26', 'sparse-a-middle') else (0,))]
    if not smoke:
        tasks += [(dict(config, prior_view=view), str(output / 'candidate'), str(target),
                   name + '-' + view, cases[name], presentation, 0)
                  for view in ('info', 'moves') for name in ('single-01', 'ascending-26')
                  for presentation in (0, 1)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(case, tasks))
    units = draw_units(output, target)
    controls = []
    if not smoke:
        base = Path(manifest.get('original_defect_base', manifest['base']))
        old = json.loads((base / 'dex-regression/modern/config.json').read_text())
        old['red_background'] = config['red_background']
        for name in ('single-01', 'ascending-26'):
            row = case((old, str(base / 'candidate'), str(target), 'negative-' + name,
                        cases[name], 0, 0))
            pixels_failed = any('overlay_pixels' in value for value in row['issues'])
            count_failed = name != 'ascending-26' or any('wrong_caught_count' in value for value in row['issues'])
            controls.append(dict(name=name, original_failure_detected=pixels_failed and count_failed,
                                 issues=row['issues']))
        if config['red_background']:
            prior = Path(manifest.get('background_defect_base', manifest['base']))
            previous = json.loads((prior / 'dex-regression/modern/config.json').read_text())
            previous['red_background'] = True
            row = case((previous, str(prior / 'candidate'), str(target),
                        'negative-prior-background', [1], 0, 0))
            background_failed = any('outer_background_pixels' in value for value in row['issues'])
            only_background = all(':outer_background_' in value for value in row['issues'])
            controls.append(dict(name='prior-background', original_failure_detected=background_failed and only_background,
                                 issues=row['issues']))
        if config['black_panels']:
            prior = Path(manifest['base'])
            previous = json.loads((prior / 'dex-regression/modern/config.json').read_text())
            previous.update(red_background=True, black_panels=True)
            row = case((previous, str(prior / 'candidate'), str(target),
                        'negative-prior-panels', [1], 0, 0))
            detected = any('black_panel_pixels' in value for value in row['issues']) and any(
                'portrait_palette_bounds' in value for value in row['issues'])
            only_panels = all(any(':' + prefix in value for prefix in (
                'black_panel_', 'portrait_palette_bounds')) for value in row['issues'])
            controls.append(dict(name='prior-panels', original_failure_detected=detected and only_panels,
                                 issues=row['issues']))
    result = dict(rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()), cases=len(rows),
                  form_selections=sum(row['checks'] for row in rows),
                  overlay_cells=sum(r['overlay_cells'] for row in rows for r in row['results']),
                  background_cells=sum(r['background_cells'] for row in rows for r in row['results']),
                  black_panel_cells=sum(r['black_panel_cells'] for row in rows for r in row['results']),
                  portrait_palette_cells=sum(r['portrait_palette_cells'] for row in rows for r in row['results']),
                  draw_unit_cases=len(units), failures=sum(bool(row['issues']) for row in rows) +
                  sum(bool(row['issues']) for row in units) +
                  sum(not row['original_failure_detected'] for row in controls),
                  results=rows, draw_units=units, negative_controls=controls)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('results', 'draw_units', 'negative_controls')}), flush=True)
    return int(bool(result['failures']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    raise SystemExit(run(args.output.resolve(), args.jobs, args.smoke))
