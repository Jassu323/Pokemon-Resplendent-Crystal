"""Qualify zero/one/sparse discovery presentation and measure native save/load."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from .assets import read_symbols, sha256
from .cold_listing import Driver
from .info_ui import BOOT
from .moves_mode import sweep, page_sweep
from .move_persistence import STEM, boot, call, helper_tests, save_roundtrips
from move_discovery_assets import address, move_bitmap, seed_records


def compare_visual_baseline(output, baseline):
    from PIL import Image, ImageChops
    cases = []
    names = [f'interface-{presentation}-{phase}/sort-popup.png'
             for presentation in (0, 1) for phase in range(8)]
    names += [f'interface-{presentation}-0/selected-second-entry.png' for presentation in (0, 1)]
    for name in names:
        with Image.open(output / 'moves-mode-qualification' / name) as current, \
                Image.open(baseline / 'moves-mode-qualification' / name) as reference:
            difference = ImageChops.difference(current.convert('RGB'), reference.convert('RGB')).getbbox()
        cases.append(dict(image=name, different_pixels_box=difference))
    result = dict(cases=len(cases), issues=[case for case in cases if case['different_pixels_box']],
                  baseline=str(baseline), results=cases)
    (output / 'persistence-visual-parity.json').write_text(json.dumps(result, indent=2) + '\n')
    if result['issues']:
        raise AssertionError('Persistence changed accepted visual pixels')
    return result


def save_menu_case(config, target, accepted):
    symbols = config['symbols']
    driver = boot(config, target.parent / 'persistence-qualification/empty.sav',
                  target / f'save-menu-{accepted}.log')

    def until(name, key=0, frames=400):
        bank, pc = symbols[name]
        if not driver.command(f'until {bank} {pc} {frames} {key}')['hit']:
            raise AssertionError(f'Normal Save menu did not reach {name}')

    def live(name, size=1):
        bank, pc = symbols[name]
        return bytes.fromhex(driver.command(f'read {bank} {pc} {size}')['bytes'])

    try:
        for index in (1, 256, 333):
            call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
        until('StartMenu.loop', 128)
        driver.command('run 4 0')
        menu = live('wMenuItemsList', 16)
        save_row = list(menu[1:menu[0] + 1]).index(4) + 1
        for _ in range(10):
            if live('wMenuCursorPosition')[0] == save_row:
                break
            driver.command('run 4 8')
            driver.command('run 4 0')
        if live('wMenuCursorPosition')[0] != save_row:
            raise AssertionError('Could not select Save normally')
        until('SaveMenu', 16)
        driver.command('run 4 0')
        until('PlaceYesNoBox', 16)
        driver.command('run 8 0')
        if accepted:
            until('SaveGameData', 16)
            if live('wGameLogicPaused') != b'\x01':
                raise AssertionError('Normal Save did not pause gameplay')
            until('ResumeGameLogic', 16)
            until('HandleMapTimeAndJoypad', 0)
            if live('wGameLogicPaused') != b'\x00':
                raise AssertionError('Normal Save left gameplay paused')
        else:
            until('StartMenu.loop', 32)
            driver.command('run 4 0')
            until('HandleMapTimeAndJoypad', 32)
        saved = target / f'save-menu-{accepted}.sav'
        driver.command(f'battery {saved}')
    finally:
        driver.close()
    from .move_persistence import cold_case
    expected = move_bitmap([1, 256, 333]) if accepted else bytes(64)
    cold_case((config, saved, expected, 1, 0))
    return dict(accepted=accepted, saved=str(saved), cold_reload=True)


def timing_case(config, battery, log):
    driver = Driver(config['core'], config['rom'], BOOT, battery, log)
    try:
        bank, pc = config['symbols']['TryLoadSaveFile']
        for _ in range(15):
            if driver.command(f'until {bank} {pc} 180 16')['hit']:
                break
            driver.command('run 10 0')
        else:
            raise AssertionError('Could not reach real Continue load')
        result = call(driver, config['symbols'], 'TryLoadSaveFile')
        if result['af'] & 0x10:
            raise AssertionError('Save load rejected valid fixture')
        return result
    finally:
        driver.close()


def compare_save_write_addresses(native, reference, battery, target):
    records = []
    for name, config in (('baseline', reference), ('candidate', native)):
        driver = boot(config, battery, target / f'write-parity-{name}.log')
        trace = target / f'write-parity-{name}.csv'
        try:
            driver.command(f'trace {trace}')
            call(driver, config['symbols'], 'SaveGameData')
            driver.command('trace off')
        finally:
            driver.close()
        with trace.open() as file:
            writes = [(bank * 8192 + location - 0xa000)
                      for bank, location, _, _, _ in (map(int, row) for row in csv.reader(file))]
        if name == 'candidate':
            addresses = {location for prefix in ('s', 'sBackup') for location in
                         range(address(native['symbols'], prefix + 'MoveDiscovery'),
                               address(native['symbols'], prefix + 'MoveDiscovery') + 72)}
            writes = [location for location in writes if location not in addresses]
        records.append(writes)
    if records[0] != records[1]:
        raise AssertionError('Persistence changed ordinary save write addresses/order')
    return dict(existing_writes=len(records[0]), exact_address_sequence=True)


def qualify(output, baseline, jobs=6):
    compare_visual_baseline(output, baseline)
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    config = json.loads((output / 'modern/config.json').read_text())
    symbols = read_symbols(output / f'{STEM}.sym')
    target = output / 'persistence-ui'
    target.mkdir(exist_ok=True)
    original = (output / 'all-seen-tests.sav').read_bytes()
    tasks = []
    for name, indices in (('zero', []), ('one', [manifest['orders'][0][0]]),
                          ('review', manifest['review_seen'])):
        directory = target / name
        directory.mkdir(exist_ok=True)
        battery = directory / 'private.sav'
        battery.write_bytes(seed_records(original, symbols, move_bitmap(indices)))
        fixture = dict(manifest, fixture='mixed', unknown=[i for i in range(1, 334) if i not in indices])
        for order in (0, 1):
            tasks.append((dict(config, battery=str(battery)), fixture, order, str(directory)))
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        records = list(pool.map(sweep, tasks))
        pages = list(pool.map(page_sweep, tasks))
    if any(record['issues'] for record in records + pages):
        raise AssertionError('Persistent zero/one/mixed presentation failed')
    native = dict(core=str(output / 'persistence-core/runner'), rom=str(output / f'{STEM}.gbc'),
                  symbols=symbols)
    reference_symbols = read_symbols(baseline / 'pokecrystal-dex-moves-mode.sym')
    reference = dict(core=str(output / 'baseline-persistence-core/runner'),
                     rom=str(baseline / 'pokecrystal-dex-moves-mode.gbc'), symbols=reference_symbols)
    write_parity = compare_save_write_addresses(native, reference, output / 'legacy-input.sav', target)
    save_menus = [save_menu_case(native, target, accepted) for accepted in (False, True)]
    load_timings = {}
    for name, fixture in (('valid', output / 'all-seen-tests.sav'), ('legacy', output / 'legacy-input.sav'),
                          ('recovery', output / 'persistence-qualification/repair-source.sav')):
        load_timings[name] = timing_case(native, fixture, target / f'load-{name}.log')
    load_timings['baseline'] = timing_case(reference, output / 'legacy-input.sav', target / 'load-baseline.log')
    # Recheck the final host assertions against the qualified link and native write traces.
    helper_tests(native, output / 'persistence-qualification')
    save_roundtrips(native, output / 'persistence-qualification')
    opaque_tests = []
    for prefix in ('s', 'sBackup'):
        source = output / 'persistence-qualification' / f'future-{prefix}-2-64.sav'
        driver = boot(native, source, target / f'opaque-{prefix}.log')
        try:
            call(driver, symbols, 'SaveGameData')
            saved = target / f'opaque-{prefix}.sav'
            driver.command(f'battery {saved}')
            for copy in ('s', 'sBackup'):
                at = address(symbols, copy + 'MoveDiscovery')
                if source.read_bytes()[at:at + 136] != saved.read_bytes()[at:at + 136]:
                    raise AssertionError('Manual saving overwrote opaque newer records')
            opaque_tests.append(prefix)
        finally:
            driver.close()
    result = dict(rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                  cases=sum(record['cases'] for record in records + pages),
                  moves=records, pages=pages, load_timings=load_timings,
                  normal_save_menu=save_menus,
                  save_write_parity=write_parity,
                  opaque_manual_saves=len(opaque_tests), final_helper_and_write_assertions=True,
                  issues=[])
    (output / 'persistence-ui-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('moves', 'pages', 'load_timings')}))
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
