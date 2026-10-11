"""Native preference, menu and Save/Continue checks for Moves sort memory."""
import argparse
import json
from pathlib import Path
import re
import shutil
import statistics

from .assets import Repository, read_symbols, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press
from .area_ui import reach
from .legacy_listing import private_battery
from .listing_options import memory
from .move_acquisition import fixture, ram
from .move_persistence import boot, call, core, read, checksum, lifecycle, core_valid
from .move_persistence_integration import timing_case
from .moves_mode import enter, sort, state, audit, audit_sort, capture, open_sort
from .performance import core as visual_core, names
from move_discovery_assets import address, decode_record, rebind_fixture

STEM = 'pokecrystal-dex-moves-sort-memory'
TAG = 0xa0


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(output):
    target = output / 'sort-memory'
    target.mkdir(exist_ok=True)
    repo = Repository(output / 'candidate', output / f'{STEM}.gbc', output / f'{STEM}.sym')
    directory = output / 'modern'
    executable = visual_core(repo, directory)
    config = dict(rom=str(repo.rom_path), sym=str(output / f'{STEM}.sym'), core=str(executable),
                  battery=str(output / 'all-seen-tests.sav'), names=names(), output=str(directory),
                  hashes=dict(rom_sha256=sha256(repo.rom)),
                  note='Same-link runner and cold batteries only; no older checkpoints reused.')
    write_json(directory / 'config.json', config)
    native = dict(rom=str(repo.rom_path), symbols=repo.symbols,
                  core=str(core(output, target_root=target)))
    write_json(target / 'native-config.json', native)
    return dict(rom_sha256=sha256(repo.rom), issues=[])


def native_config(output):
    return json.loads((output / 'sort-memory/native-config.json').read_text())


def register_call(driver, symbols, label, af):
    b, pc = symbols[label]
    owner = driver.command('peek')
    driver.command(f'begin {b} {pc} 42330 23205')
    if not driver.command(f'until {b} {pc} 4 0')['hit']:
        raise AssertionError('Preference helper entry was not reached')
    driver.command(f'regs {af} 42330 23205 4660')
    before = driver.command('peek')
    driver.command('follow')
    after = driver.command('resume 8 0')
    if not after['hit'] or any(before[n] != after[n] for n in (
            'af', 'bc', 'de', 'hl', 'svbk', 'sram_bank', 'sram_enabled', 'double_speed')):
        raise AssertionError(f'Preference helper lost context: {label}: {before}: {after}')
    returned = driver.command(f'until {owner["bank"]} {owner["pc"]} 8 0')
    if not returned['hit'] or returned['sp'] != owner['sp']:
        raise AssertionError('Native preference observer did not unwind')
    return after


def helpers(output):
    config = native_config(output)
    symbols = config['symbols']
    target = output / 'sort-memory'
    driver = boot(config, output / f'{STEM}.sav', target / 'helpers.log')
    rows = []
    try:
        flags = read(driver, symbols)
        driver.command(f'trace {target / "helpers-sram.csv"}')
        for bank in range(8):
            for value in range(256):
                fixture(driver, symbols, 'wLastMovesDexSort', [value])
                fixture(driver, symbols, 'wPokedexInfoGFX', [0x7e])
                scratch = ram(driver, symbols, 'wPokedexInfoGFX', 48)
                saved = ram(driver, symbols, 'wFarfetchdPosition', 15)
                driver.command(f'io 65392 {bank}')
                row = register_call(driver, symbols, 'PokedexMovesMode_RestoreSort', 0x69b0)
                expected = bytes((int(value == TAG + 1),)) + scratch[1:]
                if ram(driver, symbols, 'wPokedexInfoGFX', 48) != expected or ram(driver, symbols, 'wFarfetchdPosition', 15) != saved:
                    raise AssertionError(f'Restore changed unrelated state: {bank}/{value}')
                rows.append(dict(helper='restore', bank=bank, value=value, ticks=row['elapsed']))
                fixture(driver, symbols, 'wLastMovesDexSort', [0x5a])
                saved = ram(driver, symbols, 'wFarfetchdPosition', 15)
                scratch = ram(driver, symbols, 'wPokedexInfoGFX', 48)
                row = register_call(driver, symbols, 'PokedexMovesMode_RememberSort', (value << 8) | 0xb0)
                expected = bytearray(saved)
                if value < 2:
                    expected[1] = TAG | value
                if ram(driver, symbols, 'wFarfetchdPosition', 15) != expected or ram(driver, symbols, 'wPokedexInfoGFX', 48) != scratch:
                    raise AssertionError(f'Remember changed unrelated state: {bank}/{value}')
                rows.append(dict(helper='remember', bank=bank, value=value, ticks=row['elapsed']))
        if read(driver, symbols) != flags:
            raise AssertionError('Sort preference changed move discovery')
        driver.command('trace off')
        if (target / 'helpers-sram.csv').read_bytes():
            raise AssertionError('Preference helpers wrote SRAM')
    finally:
        driver.close()
    result = dict(cases=len(rows), rows=rows, all_registers_and_banks_restored=True,
                  adjacent_saved_bytes_preserved=True, no_immediate_sram_write=True, issues=[])
    write_json(target / 'helpers.json', result)
    return dict(cases=len(rows), issues=[])


def visual_preference(driver, repo):
    bank, at = repo.symbols['wLastMovesDexSort']
    return memory(driver, bank, at, 1)[0]


def return_listing(driver, repo):
    press(driver, 'b')
    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
    press(driver, 'b')
    if driver.run(('listing',), frames=600)['hit'] != 'listing':
        raise AssertionError('Moves did not return to the species listing')
    driver.run(('end_loop',))
    driver.run(('end_loop',))


def close_dex(driver, repo):
    return_listing(driver, repo)
    reach(driver, repo, 'StartMenu.loop', key=32)
    driver.run(frames=8)
    reach(driver, repo, 'StartMenu.b', key=32)
    reach(driver, repo, 'HandleMapTimeAndJoypad')
    driver.run(frames=2)


def save_visual(driver, repo, destination, accepted=True):
    reach(driver, repo, 'StartMenu.loop', key=128)
    driver.run(frames=8)
    bank, at = repo.symbols['wMenuItemsList']
    items = memory(driver, bank, at, 16)
    row = list(items[1:items[0] + 1]).index(4) + 1
    for _ in range(12):
        bank, at = repo.symbols['wMenuCursorPosition']
        if memory(driver, bank, at, 1)[0] == row:
            break
        driver.run(frames=4, key='down')
        driver.run(frames=8)
    else:
        raise AssertionError('Could not select Save')
    reach(driver, repo, 'SaveMenu', key=16)
    driver.run(frames=8)
    reach(driver, repo, 'PlaceYesNoBox', key=16)
    driver.run(frames=8)
    if accepted:
        reach(driver, repo, 'SaveGameData', key=16)
        reach(driver, repo, 'ResumeGameLogic', key=16)
    else:
        reach(driver, repo, 'StartMenu.loop', key=32)
        driver.run(frames=8)
        reach(driver, repo, 'StartMenu.b', key=32)
    reach(driver, repo, 'HandleMapTimeAndJoypad')
    driver.command(f'perfbattery {destination}')


def ui_tests(output):
    config = json.loads((output / 'modern/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = Repository(output / 'candidate', Path(config['rom']), Path(config['sym']))
    target = output / 'sort-memory/ui'
    target.mkdir(exist_ok=True)
    rows = []
    for presentation in (0, 1):
        for order in (0, 1):
            for phase in range(4):
                directory = target / f'{presentation}-{order}-{phase}'
                directory.mkdir(exist_ok=True)
                battery = directory / 'input.sav'
                species_order = phase % 3
                private_battery(config, battery, presentation=presentation, order_mode=species_order,
                                unown_unlocked=bool(phase & 1))
                driver = Driver(config['core'], config['rom'], BOOT, battery, directory / 'ui.log')
                try:
                    bootstrap(driver, expected_mode=species_order)
                    enter(driver, repo)
                    if state(driver, repo)['sort'] != 0:
                        raise AssertionError('Legacy/default padding did not begin in Type')
                    driver.run(frames=phase / 4)
                    sort(driver, repo, order)
                    audit(driver, repo, manifest)
                    if visual_preference(driver, repo) != TAG | order:
                        raise AssertionError('Confirmed sort did not update its preference')
                    for _ in range(19):
                        press(driver, 'down')
                    before = state(driver, repo)
                    for cancel in ('b', 'start'):
                        base = driver.command('ui')
                        open_sort(driver, repo)
                        press(driver, 'down')
                        audit_sort(driver, repo, base)
                        press(driver, cancel)
                        reach(driver, repo, 'PokedexMovesMode_Update')
                        if state(driver, repo) != before or visual_preference(driver, repo) != TAG | order:
                            raise AssertionError('Canceled sort changed position or preference')
                    sort(driver, repo, order)
                    if state(driver, repo) != before:
                        raise AssertionError('Same-sort confirmation reset position')
                    sort(driver, repo, 1 - order)
                    if state(driver, repo)['scroll'] or state(driver, repo)['cursor']:
                        raise AssertionError('Changed sort did not reset position')
                    sort(driver, repo, order)
                    press(driver, 'select' if phase & 1 else 'b')
                    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
                    press(driver, 'a')
                    reach(driver, repo, 'PokedexMovesMode_Update')
                    driver.run(frames=2)
                    if state(driver, repo)['sort'] != order or state(driver, repo)['scroll'] or state(driver, repo)['cursor']:
                        raise AssertionError('Mode reentry lost sort or retained a deferred position')
                    audit(driver, repo, manifest)
                    return_listing(driver, repo)
                    listing = driver.command('peek')
                    if (listing['presentation'], listing['mode']) != (presentation, species_order):
                        raise AssertionError('Moves sort changed species presentation/order')
                    enter(driver, repo)
                    if state(driver, repo)['sort'] != order:
                        raise AssertionError('Other Dex ownership overwrote the saved preference')
                    close_dex(driver, repo)
                    bootstrap(driver, expected_mode=species_order)
                    enter(driver, repo)
                    if state(driver, repo)['sort'] != order:
                        raise AssertionError('Closing/reopening the Dex lost sort')
                    audit(driver, repo, manifest)
                    if phase == 0:
                        capture(driver, directory / 'remembered.png')
                    rows.append(dict(presentation=presentation, order=order, phase=phase,
                                     species_order=species_order, issues=[]))
                finally:
                    driver.close()
    write_json(target / 'summary.json', dict(cases=len(rows), rows=rows, issues=[]))
    return dict(cases=len(rows), issues=[])


def saved_preference(data, symbols, prefix='s'):
    at = address(symbols, prefix + 'PlayerData') + symbols['wLastMovesDexSort'][1] - symbols['wPlayerData'][1]
    return data[at]


def cold_check(config, battery, log, expected_raw, bitmap):
    driver = boot(config, battery, log)
    try:
        if ram(driver, config['symbols'], 'wLastMovesDexSort')[0] != expected_raw:
            raise AssertionError('Cold Continue selected the wrong saved preference')
        if read(driver, config['symbols'])[:64] != bitmap:
            raise AssertionError('Preference persistence changed discoveries')
        call(driver, config['symbols'], 'PokedexMovesMode_RestoreSort')
        if ram(driver, config['symbols'], 'wPokedexInfoGFX')[0] != int(expected_raw == TAG + 1):
            raise AssertionError('Cold loaded preference decoded incorrectly')
        repaired = battery.with_suffix('.reloaded.sav')
        driver.command(f'battery {repaired}')
        return repaired
    finally:
        driver.close()


def save_tests(output):
    config = json.loads((output / 'modern/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    native = native_config(output)
    repo = Repository(output / 'candidate', Path(config['rom']), Path(config['sym']))
    symbols = repo.symbols
    source = Path(manifest['sort_memory_source'])
    source_stem = json.loads((source / 'moves-mode-manifest.json').read_text())['stem']
    target = output / 'sort-memory/saves'
    target.mkdir(exist_ok=True)
    rows = []
    for label, initial, destination in (
            ('natural', source / f'{source_stem}.sav', output / f'{STEM}.sav'),
            ('battle', source / 'battle-review' / f'{source_stem}.sav', output / 'battle-review' / f'{STEM}.sav')):
        bitmap = decode_record(initial.read_bytes(), symbols, 's')['bitmap']
        seen = {n for n in range(1, 334) if bitmap[(n - 1) // 8] & 1 << ((n - 1) & 7)}
        ui_manifest = dict(manifest, fixture='mixed', unknown=[n for n in range(1, 334) if n not in seen])
        for order in (0, 1):
            saved = target / f'{label}-{order}.sav'
            driver = Driver(config['core'], config['rom'], BOOT, initial, target / f'{label}-{order}.log')
            try:
                bootstrap(driver)
                enter(driver, repo)
                sort(driver, repo, order)
                audit(driver, repo, ui_manifest)
                close_dex(driver, repo)
                save_visual(driver, repo, saved)
            finally:
                driver.close()
            for prefix in ('s', 'sBackup'):
                if saved_preference(saved.read_bytes(), symbols, prefix) != TAG | order:
                    raise AssertionError('Normal Save did not write both preference copies')
                if decode_record(saved.read_bytes(), symbols, prefix) != dict(status='valid', bitmap=bitmap):
                    raise AssertionError('Preference Save changed discovery extension')
            cold_check(native, saved, target / f'{label}-{order}-native-reload.log', TAG | order, bitmap)
            driver = Driver(config['core'], config['rom'], BOOT, saved, target / f'{label}-{order}-ui-reload.log')
            try:
                bootstrap(driver)
                enter(driver, repo)
                audit(driver, repo, ui_manifest)
                if state(driver, repo)['sort'] != order:
                    raise AssertionError('Normal Save/cold Dex reentry lost sort')
                if label == 'battle':
                    capture(driver, target / f'battle-{order}.png')
            finally:
                driver.close()
            rows.append(dict(fixture=label, order=order, normal_inputs=True, cold_reload=True))
            if order == 1:
                shutil.copy2(saved, destination)
    base = (target / 'natural-1.sav').read_bytes()
    bitmap = decode_record(base, symbols, 's')['bitmap']
    for kind in ('primary-wins', 'bad-primary', 'bad-backup', 'legacy-zero', 'legacy-one', 'invalid-255'):
        data = bytearray(base)
        raw = {'legacy-zero': 0, 'legacy-one': 1, 'invalid-255': 255}.get(kind, TAG + 1)
        for prefix in ('s', 'sBackup'):
            at = address(symbols, prefix + 'PlayerData') + symbols['wLastMovesDexSort'][1] - symbols['wPlayerData'][1]
            data[at] = TAG if prefix == 'sBackup' and kind in ('primary-wins', 'bad-primary') else raw
            checksum(data, symbols, prefix)
        data = bytearray(rebind_fixture(base, data, symbols))
        if kind.startswith('bad-'):
            prefix = 's' if kind == 'bad-primary' else 'sBackup'
            data[address(symbols, prefix + 'Checksum')] ^= 1
        battery = target / f'{kind}.sav'
        battery.write_bytes(data)
        expected = TAG if kind == 'bad-primary' else raw
        repaired = cold_check(native, battery, target / f'{kind}.log', expected, bitmap)
        for prefix in ('s', 'sBackup'):
            if saved_preference(repaired.read_bytes(), symbols, prefix) != expected or not core_valid(repaired.read_bytes(), symbols, prefix):
                raise AssertionError('Backup repair lost preference or damaged core checksums')
        rows.append(dict(case=kind, expected_raw=expected, cold_reload=True))
    initial = source / f'{source_stem}.sav'
    driver = Driver(config['core'], config['rom'], BOOT, initial, target / 'canceled-save.log')
    canceled = target / 'canceled-save.sav'
    try:
        bootstrap(driver)
        enter(driver, repo)
        sort(driver, repo, 1)
        close_dex(driver, repo)
        save_visual(driver, repo, canceled, accepted=False)
    finally:
        driver.close()
    before = initial.read_bytes()
    for prefix in ('s', 'sBackup'):
        if saved_preference(canceled.read_bytes(), symbols, prefix) != saved_preference(before, symbols, prefix):
            raise AssertionError('Declining Save wrote a preference')
    cold_check(native, canceled, target / 'canceled-save-reload.log', saved_preference(before, symbols),
               decode_record(before, symbols, 's')['bitmap'])
    rows.append(dict(case='canceled-save', cold_reload=True))
    shutil.copy2(output / f'{STEM}.sav', target / 'save-4.sav')
    lifecycle_count = lifecycle(native, target)
    for prefix in ('s', 'sBackup'):
        if saved_preference((target / 'new-game-saved.sav').read_bytes(), symbols, prefix):
            raise AssertionError('New Game did not restore the default preference')
    driver = Driver(native['core'], native['rom'], BOOT, output / f'{STEM}.sav', target / 'new-game-live.log')
    try:
        bank, pc = symbols['MainMenuJoypadLoop.loop']
        if not driver.command(f'until {bank} {pc} 1200 16')['hit']:
            raise AssertionError('Could not reach the New Game menu')
        fixture(driver, symbols, 'wLastMovesDexSort', [TAG + 1])
        driver.command('run 8 0')
        driver.command('run 8 8')
        driver.command('run 8 0')
        bank, pc = symbols['NewGame_ClearTilemapEtc']
        if not driver.command(f'until {bank} {pc} 300 16')['hit'] or ram(driver, symbols, 'wLastMovesDexSort') != b'\x00':
            raise AssertionError('Normal New Game retained a live Alphabet preference')
    finally:
        driver.close()
    result = dict(cases=len(rows), rows=rows, lifecycle_cases=lifecycle_count + 1,
                  review=[dict(path=str(path), sha256=sha256(path.read_bytes()), order='Alphabet') for path in
                          (output / f'{STEM}.sav', output / 'battle-review' / f'{STEM}.sav')], issues=[])
    write_json(target / 'summary.json', result)
    return result


def timings(output):
    native = native_config(output)
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    source = Path(manifest['sort_memory_source'])
    target = output / 'sort-memory/timing'
    target.mkdir(exist_ok=True)
    baseline = dict(rom=str(source / 'pokecrystal-dex-moves-persistence.gbc'),
                    symbols=read_symbols(source / 'pokecrystal-dex-moves-persistence.sym'),
                    core=str(core(source, target_root=target)))
    rows = {}
    for label, config in (('baseline', baseline), ('candidate', native)):
        rows[label] = dict(load=[timing_case(config, output / f'{STEM}.sav', target / f'{label}-load-{n}.log') for n in range(4)])
        driver = boot(config, output / f'{STEM}.sav', target / f'{label}-save.log')
        try:
            rows[label]['save'] = [call(driver, config['symbols'], 'SaveGameData') for _ in range(4)]
        finally:
            driver.close()
    result = dict(rows=rows, summary={kind: {field: dict(
        baseline=statistics.median(r[field] for r in rows['baseline'][kind]),
        candidate=statistics.median(r[field] for r in rows['candidate'][kind]),
        delta=statistics.median(r[field] for r in rows['candidate'][kind]) - statistics.median(r[field] for r in rows['baseline'][kind]))
        for field in ('ms', 'intervals')} for kind in ('load', 'save')}, issues=[])
    write_json(target / 'summary.json', result)
    return result['summary']


def qualify(output):
    manifest_path = output / 'moves-mode-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    source = Path(manifest['sort_memory_source'])
    current, previous = output / 'candidate', source / 'candidate'
    changed = sorted(p.relative_to(current).as_posix() for p in current.rglob('*.asm')
                     if not (previous / p.relative_to(current)).exists()
                     or p.read_bytes() != (previous / p.relative_to(current)).read_bytes())
    if changed != ['engine/pokedex/pokedex_moves_mode.asm', 'ram/wram.asm']:
        raise AssertionError(f'Unexpected source changes: {changed}')
    for path, digest in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected input changed: {path}')
    reports = {name: json.loads((output / path).read_text()) for name, path in (
        ('helpers', 'sort-memory/helpers.json'), ('ui', 'sort-memory/ui/summary.json'),
        ('saves', 'sort-memory/saves/summary.json'), ('timing', 'sort-memory/timing/summary.json'),
        ('moves', 'moves-mode-qualification/summary.json'))}
    if any(row.get('issues') or row.get('failures') for row in reports.values()):
        raise AssertionError('Qualification contains an unresolved issue')
    def resource(path):
        return {name: int(used) for name, used in re.findall(
            r'^\s*(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used', path.read_text(), re.M)}
    now = resource(output / f'{STEM}.map')
    before = resource(source / 'pokecrystal-dex-moves-battle-use.map')
    deltas = {name: used - before[name] for name, used in now.items()}
    if deltas != dict(ROM0=0, ROMX=65, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0):
        raise AssertionError(f'Unexpected memory costs: {deltas}')
    prior = json.loads((ROOT / 'build/dex-moves-battle-use-20261008/moves-mode-qualification/summary.json').read_text())
    transitions = []
    for old, new in zip(prior['interfaces'], reports['moves']['interfaces'], strict=True):
        for name, row in new['transitions'].items():
            transitions.append(dict(presentation=new['presentation'], phase=new['phase'], name=name,
                first_delta=row['first_frames'] - old['transitions'][name]['first_frames'],
                complete_delta=row['complete_frames'] - old['transitions'][name]['complete_frames']))
    review = reports['saves']['review']
    for row in review:
        if sha256(Path(row['path']).read_bytes()) != row['sha256']:
            raise AssertionError('Review save no longer matches its tested copy')
    manifest.update(manual_review_save_sha256=review[0]['sha256'], sort_memory_review=review)
    write_json(manifest_path, manifest)
    result = dict(rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                  source=str(source), source_delta=changed, resource_delta=deltas,
                  protected_inputs=len(manifest['protected_inputs']), review=review,
                  helper_cases=reports['helpers']['cases'], ui_cases=reports['ui']['cases'],
                  save_cases=reports['saves']['cases'], lifecycle_cases=reports['saves']['lifecycle_cases'],
                  moves_navigation_cases=reports['moves']['cases'],
                  moves_page_cases=reports['moves']['page_cases'],
                  moves_interface_checks=reports['moves']['interface_checks'],
                  transition_cases=len(transitions), transition_deltas=transitions,
                  timing=reports['timing']['summary'], issues=[])
    write_json(output / 'sort-memory-qualification.json', result)
    return {name: value for name, value in result.items() if name != 'transition_deltas'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'helpers', 'ui', 'saves', 'timing', 'qualify'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build path')
    result = {'prepare': prepare, 'helpers': helpers, 'ui': ui_tests,
              'saves': save_tests, 'timing': timings, 'qualify': qualify}[args.action](output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
