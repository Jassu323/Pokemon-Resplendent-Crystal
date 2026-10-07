"""Normal-input qualification and pixel latency for the private Listing popovers."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import tempfile

from . import performance
from .assets import Repository, offset
from .cold_listing import ROOT, Driver, KEY, bootstrap, audit, move
from .description_ui import settle
from .info_ui import BOOT, press, ready
from .moves_ui import ready as moves_ready
from .area_ui import reach
from .legacy_listing import layout_audit, private_battery, prepare_legacy, select_presentation
from pokedex_info_assets import species, Compiler

LABELS = ('NewPokedexOrder', 'NationalPokedexOrder', 'AlphabeticalPokedexOrder')
POINTS = {
    'popover_open': ('PokedexPopover_Open', True),
    'popover_draw': ('PokedexPopover_Draw', True),
    'popover_publish': ('PokedexPopover_Publish', True),
    'order': ('PokedexPopover_OrderMons', True),
    'resort': ('PokedexPopover_Resort', True),
    'popover_commit': ('PokedexPopover_VBlank', True),
    'popover_commit_done': ('PokedexPopover_VBlank.committed', False),
    'grid_upload': ('PokedexPopover_UploadGrid', True),
    'shift_prepare': ('PokedexPopover_PrepareShiftedText', True),
    'shift_upload': ('PokedexPopover_UploadShiftedText', True),
}


def configuration(output, presentation='modern'):
    return dict(json.loads((output / presentation / 'config.json').read_text()),
                listing_style=presentation)


def configurations(output):
    manifest = json.loads((output / 'sort-manifest.json').read_text())
    return [configuration(output, style) for style in manifest.get('presentations', ['modern'])]


def memory(driver, bank, address, size):
    return bytes.fromhex(driver.command(f'perfram {bank} {address} {size}')['bytes'])


def popup(driver, kind, row):
    state = memory(driver, 3, 0xdc00, 4)
    if state[:2] != bytes((kind, row)) or state[2] or driver.command('peek')['jumptable'] != 14:
        raise RuntimeError(f'Unexpected popup: {state.hex()}')


def choose(driver, mode):
    press(driver, 'start')
    popup(driver, 0, 0)
    press(driver, 'a')
    current = driver.command('peek')['mode']
    popup(driver, 1, current)
    for _ in range(abs(mode - current)):
        press(driver, 'down' if mode > current else 'up')
    press(driver, 'a')
    state = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
    if state['hit'] != 'listing' or state['mode'] != mode:
        raise RuntimeError(f'Sort failed to return: {state}')
    driver.run(('end_loop',))
    driver.run(('end_loop',))
    return driver.command('peek')


def order_audit(driver, repo, order, unseen=()):
    constants = species()
    ids = {name: index for index, name in enumerate(constants, 1)}
    expected = [ids[name] for name in order]
    if driver.command('peek')['mode'] == 2:
        expected = [value for value in expected if value not in unseen]
    end = max((i + 1 for i, value in enumerate(expected) if value not in unseen), default=0)
    bank, address = repo.symbols['wPokedexOrder']
    data = memory(driver, bank, address, len(expected) * 2) if expected else b''
    actual = [int.from_bytes(data[i:i + 2], 'little') for i in range(0, len(data), 2)]
    if actual != expected or driver.command('peek')['end'] != end:
        raise RuntimeError('Active order or last-seen extent differs from generated data')
    mask = memory(driver, 0, repo.symbols['wPokedexWRAM0Scratch'][1] + 0x4d0, (len(constants) + 7) // 8)
    for index, value in enumerate(expected[:end]):
        if bool(mask[index // 8] & 1 << (index & 7)) != (value not in unseen):
            raise RuntimeError(f'Eligibility mismatch at {index}')
    return expected


def title_audit(driver, repo, permanent):
    at = offset(repo.symbols['PokemonNames']) + (permanent - 1) * 10
    expected = repo.rom[at:at + 10].split(b'\x50')[0]
    state = driver.command('peek')
    start = (2 + state['cursor'] * 2) * 20 + 1 if state['presentation'] else 20
    actual = bytes.fromhex(driver.command('ui')['window'])[start:start + 10]
    if not actual.startswith(expected):
        raise RuntimeError('Selected name did not follow its permanent species identity')


def grid_audit(driver, repo, order, unseen=()):
    """Verify both resident icon frames against ROM sources, not cache tags alone."""
    state = driver.command('peek')
    if state['presentation'] or not state['end']:
        return
    top = memory(driver, 0, repo.symbols['wPokedexGridTopPhysicalRow'][1], 1)[0]
    tags = memory(driver, 0, repo.symbols['wPokedexGridCacheRowOffsets'][1], 10)
    palettes = memory(driver, 0, repo.symbols['wPokedexGridIconPalettes'][1], 9)
    table = offset(repo.symbols['MonMenuIcons'])
    for row in range(3):
        physical = (top + row) % 5
        logical = state['scroll'] + row * 3
        tag = int.from_bytes(tags[physical * 2:physical * 2 + 2], 'little')
        if tag != logical:
            raise RuntimeError(f'Grid row tag {tag} does not own offset {logical}')
        icons = []
        for column in range(3):
            position = logical + column
            if position >= state['end'] or order[position] in unseen:
                # Unknown/empty cells do not display these slots. Their
                # shared question-mark tiles are outside the row cache.
                icons.append(None)
                continue
            permanent = order[position]
            at = table + (permanent - 1) * 4
            bank, low, high, palette = repo.rom[at:at + 4]
            source = offset((bank, low | high << 8))
            icons.append(repo.rom[source:source + 128])
            if palettes[row * 3 + column] != palette >> 4:
                raise RuntimeError(f'Grid palette does not match species {permanent} at {position}')
        chunks = [('center', 0x8000, 0, icons[1])]
        for column, chunk in ((0, 0), (2, 64)):
            if icons[column] is not None:
                chunks += [('sides-frame0', 0x9000, chunk, icons[column][:64]),
                           ('sides-frame1', 0x8d20, chunk, icons[column][64:])]
        for name, address, chunk, expected in chunks:
            if expected is None:
                continue
            actual = bytes.fromhex(driver.command(
                f'inspectvram 1 {address + physical * 128 + chunk} {len(expected)}')['bytes'])
            if actual != expected:
                mismatch = next(i for i, (a, b) in enumerate(zip(actual, expected)) if a != b)
                raise RuntimeError(f'Stale grid graphics: {name}, row {logical}, '
                                   f'physical {physical}, byte {mismatch}')


def listing_audit(driver, repo, order, unseen=()):
    state = driver.command('peek')
    if not state['presentation']:
        return grid_audit(driver, repo, order, unseen)
    excluded = tuple(index for index, permanent in enumerate(order) if permanent in unseen)
    issues = layout_audit(repo, state, driver.command('ui'), unseen=excluded, order=order)
    if issues:
        raise RuntimeError('Legacy Listing mismatch: ' + ', '.join(issues))


def prepare(output, battery):
    seed = output / 'seed.sav'
    private_battery(dict(rom=str(output / 'pokecrystal-dex-options.gbc'),
                         sym=str(output / 'pokecrystal-dex-options.sym'), battery=str(battery)),
                    seed, presentation=0, order_mode=0)
    config = performance.prepare(output / 'pokecrystal-dex-options.gbc',
                                 output / 'pokecrystal-dex-options.sym',
                                 seed, output / 'modern')
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    config['core'] = str(performance.core(repo, output / 'popover-core', POINTS).resolve())
    (output / 'modern/config.json').write_text(json.dumps(config, indent=2) + '\n')
    prepare_legacy(output / 'legacy', config)
    shutil.copy2(config['battery'], output / 'pokecrystal-dex-options.sav')


def species_case(task):
    config, index, mode, manifest, output = task
    output = Path(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    name = config['names'][index]
    asset = repo.load([name])[0]
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / f'{index:03}-{mode}.log')
    issues = []
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[0]]))
        state = choose(driver, mode)
        order = order_audit(driver, repo, manifest['orders'][LABELS[mode]])
        listing_audit(driver, repo, order)
        original = species().index(manifest['orders'][LABELS[0]][index]) + 1
        if mode and (state['index'] or state['scroll'] or state['cursor']):
            raise RuntimeError('Changed sort did not reset to the beginning')
        permanent = order[state['index']]
        if not mode and permanent != original:
            raise RuntimeError('Same-sort no-op changed the selected species')
        name = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(
            species()[permanent - 1], species()[permanent - 1].lower())
        asset = repo.load([name])[0]
        title_audit(driver, repo, permanent)
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept', 'animation_miss', 'audio_miss'), key='a')
        settled = settle(driver)
        issues += audit(asset, accepted, driver.events, settled, cold=False, expected_double_speed=1)['issues']
        # The Selected owner must page by the new order, not the authored
        # family's old ordinal. Audit both directions and return to our species.
        for key, destination in (('down', (state['index'] + 1) % len(order)),
                                 ('up', state['index'])):
            driver.events.clear()
            accepted = driver.run(('change_species', 'animation_miss', 'audio_miss'), key=key)
            final = settle(driver)
            target = species()[order[destination] - 1]
            target = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(target, target.lower())
            issues += audit(repo.load([target])[0], accepted, driver.events, final,
                            cold=False, expected_double_speed=1)['issues']
            if final['selected_index'] != destination:
                issues.append('sorted_internal_paging')
        for key in ('start', 'select'):
            press(driver, key)
            if driver.command('peek')['jumptable'] != 3:
                issues.append('selected_menu_entry')
        press(driver, 'right')
        press(driver, 'a')
        ready(driver, 0)
        press(driver, 'right')
        press(driver, 'a')
        moves_ready(driver)
        driver.run(('leave',), key='b')
        returned = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        if returned['hit'] != 'listing' or returned['index'] != state['index'] or returned['mode'] != mode:
            issues.append('selected_return')
        driver.run(frames=2)
        title_audit(driver, repo, permanent)
        listing_audit(driver, repo, order)
        if any(event['event'] in ('animation_miss', 'audio_miss') for event in driver.events):
            issues.append('playback_miss')
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / f'{index:03}-{mode}-error')
    finally:
        driver.close()
    return dict(species=name, mode=mode, presentation=config.get('listing_style', 'modern'), issues=issues)


def qualify(output, jobs):
    manifest = json.loads((output / 'sort-manifest.json').read_text())
    target = output / 'popover-qualification'
    target.mkdir(exist_ok=True)
    tasks = []
    for config in configurations(output):
        local = target / config['listing_style']
        local.mkdir(exist_ok=True)
        tasks += [(config, index, mode, manifest, str(local))
                  for index in range(len(config['names'])) for mode in range(3)]
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for result in pool.map(species_case, tasks):
            results.append(result)
            if len(results) % 100 == 0 or result['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), result=result)), flush=True)
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    return int(bool(summary['failures']))


def edges(output, presentation=0):
    config = configuration(output, 'legacy' if presentation else 'modern')
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    manifest = json.loads((output / 'sort-manifest.json').read_text())
    target = output / ('edges-legacy' if presentation else 'edges')
    target.mkdir(exist_ok=True)
    records = []
    constants = species()
    for unseen in ((), (0, 1, 2, 150, 151, 250, 251, 371, 372), tuple(range(1, 373)), tuple(range(373))):
        for initial in range(3):
            battery = target / f'{len(unseen)}-{initial}.sav'
            private_battery(config, battery, presentation=presentation, unseen=unseen, order_mode=initial)
            driver = Driver(config['core'], config['rom'], BOOT, battery, target / f'{len(unseen)}-{initial}.log')
            issues = []
            try:
                bootstrap(driver, expected_mode=initial)
                excluded = {constants.index(manifest['orders'][LABELS[0]][i]) + 1 for i in unseen}
                listing_audit(driver, repo, order_audit(
                    driver, repo, manifest['orders'][LABELS[initial]], excluded), excluded)
                # No-seen Listing deliberately prohibits menus. Do not invent an input path.
                if driver.command('peek')['end']:
                    for mode in (2, 1, 0, 0):
                        choose(driver, mode)
                        listing_audit(driver, repo, order_audit(
                            driver, repo, manifest['orders'][LABELS[mode]], excluded), excluded)
                    press(driver, 'start')
                    press(driver, 'up')
                    popup(driver, 0, 1)
                    press(driver, 'down')
                    popup(driver, 0, 0)
                    press(driver, 'a')
                    press(driver, 'up')
                    popup(driver, 1, 2)
                    press(driver, 'down')
                    popup(driver, 1, 0)
                    press(driver, 'b')
                    popup(driver, 0, 0)
                    press(driver, 'start')
                    driver.run(('listing',), frames=600)
                records.append(dict(unseen=len(unseen), initial=initial, issues=issues))
            except (RuntimeError, ValueError) as error:
                issues.append(str(error))
                driver.evidence(target / f'{len(unseen)}-{initial}-error')
                records.append(dict(unseen=len(unseen), initial=initial, issues=issues))
            finally:
                driver.close()
    # Explicitly start on an unseen first species, then exclude it with Alphabet.
    battery = target / 'fallback.sav'
    private_battery(config, battery, presentation=presentation, unseen=(0,))
    driver = Driver(config['core'], config['rom'], BOOT, battery, target / 'fallback.log')
    try:
        bootstrap(driver)
        choose(driver, 2)
        title_audit(driver, repo, constants.index(manifest['orders'][LABELS[2]][0]) + 1)
        records.append(dict(scenario='unseen_selection_fallback', issues=[]))
    except (RuntimeError, ValueError) as error:
        records.append(dict(scenario='unseen_selection_fallback', issues=[str(error)]))
    finally:
        driver.close()
    (target / 'summary.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(records, indent=2))
    return int(any(r['issues'] for r in records))


def capture(driver, directory, name):
    from PIL import Image
    path = directory / f'{name}.ppm'
    driver.command(f'image {path}')
    with Image.open(path) as image:
        image.save(path.with_suffix('.png'))
        image.resize((640, 576), Image.Resampling.NEAREST).save(path.with_name(path.stem + '-4x.png'))


def integration(output, jobs):
    from .dex_modes import row_case, mode_ids
    config = configuration(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    target = output / 'integration'
    target.mkdir(exist_ok=True)
    records, mode_tasks = [], []
    for unlocked in (False, True):
        for presentation in (0, 1):
            for order in range(3):
                fixture = target / f'modes-{int(unlocked)}-{presentation}-{order}.sav'
                private_battery(config, fixture, presentation=presentation,
                                order_mode=order, unown_unlocked=unlocked)
                mode_tasks.extend((config, str(fixture), unlocked, presentation, order, row, str(target))
                                  for row in range(len(mode_ids(unlocked))))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        records.extend(pool.map(row_case, mode_tasks))
    for presentation in (0, 1):
        for mode in range(3):
            for warmed in (False, True):
                driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                                target / f'search-{presentation}-{mode}-{int(warmed)}.log')
                issues = []
                try:
                    driver.command(f'load {config["states"]}/listing-000.s0')
                    choose(driver, mode)
                    if presentation:
                        select_presentation(driver, 1)
                    if warmed:
                        driver.run(frames=120)
                    press(driver, 'start')
                    press(driver, 'down')
                    press(driver, 'a')
                    reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                    driver.run(frames=2)
                    press(driver, 'down')
                    press(driver, 'down')
                    press(driver, 'a')
                    reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
                    driver.run(frames=2)
                    driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                    settle(driver)
                    reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen', KEY['b'])
                    driver.run(frames=2)
                    press(driver, 'b')
                    reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                    driver.run(frames=2)
                    press(driver, 'b')
                    returned = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
                    driver.run(frames=2)
                    if (returned['hit'], returned['mode'], returned['presentation']) != ('listing', mode, presentation):
                        issues.append('search_owner_return')
                    manifest = json.loads((output / 'sort-manifest.json').read_text())
                    listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[mode]]))
                    for _ in range(6):
                        index = driver.command('peek')['index'] + (1 if presentation else 3)
                        move(driver, 'down', index)
                        driver.run(('end_loop',))
                        driver.run(('end_loop',))
                    if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
                        issues.append('search_playback_miss')
                    # Ordering and presentation survive closing and reopening.
                    reach(driver, repo, 'StartMenu.loop', KEY['b'])
                    driver.run(('start_menu',))
                    driver.run(('start_menu',))
                    returned = driver.run(('overworld',), frames=600, key='b')
                    if returned['hit'] != 'overworld':
                        raise RuntimeError('Start menu did not close to the overworld')
                    bootstrap(driver, expected_mode=mode)
                    if driver.command('peek')['presentation'] != presentation:
                        issues.append('reopen_presentation')
                except (RuntimeError, ValueError) as error:
                    issues.append(str(error))
                    driver.evidence(target / f'search-{presentation}-{mode}-{int(warmed)}-error')
                finally:
                    driver.close()
                records.append(dict(scenario='search_and_reopen', presentation=presentation,
                                    mode=mode, warmed=warmed, issues=issues))
    summary = dict(cases=len(records), failures=sum(bool(r['issues']) for r in records), results=records)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    return int(bool(summary['failures']))


def measure(output):
    from PIL import Image
    config = configuration(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    target = output / 'visuals'
    target.mkdir(exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], target / 'capture.log')
    records = []
    try:
        driver.command(f'load {config["states"]}/listing-000.s0')
        driver.command('rawcolor')
        driver.run(frames=2)
        capture(driver, target, 'listing-before')
        for name, key, label, rectangle in (
            ('options-open', 'start', 'PokedexPopover_Update', (72, 56, 144, 96)),
            ('sort-open', 'a', 'PokedexPopover_Update', (64, 48, 152, 104)),
            ('sort-cursor', 'down', 'PokedexPopover_Update', (72, 56, 80, 88)),
            ('national-reveal', 'a', 'Pokedex_UpdateMainScreen', (64, 8, 155, 128)),
            ('options-reopen', 'start', 'PokedexPopover_Update', (72, 56, 144, 96)),
            ('sort-reopen', 'a', 'PokedexPopover_Update', (64, 48, 152, 104)),
            ('sort-back', 'b', 'PokedexPopover_Update', (64, 48, 152, 104)),
            ('options-cancel', 'b', 'Pokedex_UpdateMainScreen', (72, 56, 144, 96)),
            ('same-sort-options', 'start', 'PokedexPopover_Update', (72, 56, 144, 96)),
            ('same-sort-open', 'a', 'PokedexPopover_Update', (64, 48, 152, 104)),
            ('same-sort-close', 'a', 'Pokedex_UpdateMainScreen', (64, 48, 152, 104)),
            ('start-close-options', 'start', 'PokedexPopover_Update', (72, 56, 144, 96)),
            ('start-cancel', 'start', 'Pokedex_UpdateMainScreen', (72, 56, 144, 96)),
        ):
            driver.run(frames=2)
            before = target / f'{name}-before.ppm'
            driver.command(f'image {before}')
            driver.events.clear()
            accepted = driver.command('perf 1')
            prefix = target / name
            driver.command(f'perfimages {prefix}')
            # Hold through two physical polls. Stopping at the modal update's
            # entry can release a key before Joypad has sampled it.
            driver.run(('animation_miss', 'audio_miss'), frames=2, key=key)
            driver.run(('animation_miss', 'audio_miss'), frames=18)
            driver.command('perfimages -')
            driver.command('perf 0')
            frames = [event for event in driver.events if event['event'] == 'perf_frame']
            source = Image.open(before).crop(rectangle).tobytes()
            images = [Image.open(target / f'{name}-{e["display"]:03}.ppm').crop(rectangle).tobytes() for e in frames]
            final = images[-1]
            first_any = next(i for i, image in enumerate(images) if image != source)
            # Resident mini animation is not UI responsiveness. The modal or
            # sorted grid is published atomically, then scanned in its entirety.
            completions = [e['t'] for e in driver.events if e['event'] == 'perf_phase'
                           and e['name'] in ('popover_commit_done', 'listing_reveal')]
            if not completions:
                raise RuntimeError(f'No publication checkpoint for {name}')
            complete = next(i for i, event in enumerate(frames) if event['boundary_t'] > completions[-1])
            first = first_any if name == 'national-reveal' else complete
            record = dict(name=name, first_ms=(frames[first]['boundary_t'] - accepted['t']) / performance.HZ * 1000,
                          first_frames=(frames[first]['boundary_t'] - accepted['t']) / performance.T,
                          complete_ms=(frames[complete]['boundary_t'] - accepted['t']) / performance.HZ * 1000,
                          complete_frames=(frames[complete]['boundary_t'] - accepted['t']) / performance.T,
                          independent_grid_change_frames=(frames[first_any]['boundary_t'] - accepted['t']) / performance.T,
                          costs=[e for e in driver.events if e['event'] == 'perf_cost'],
                          phases=[e for e in driver.events if e['event'] == 'perf_phase'])
            records.append(record)
            capture(driver, target, name)
        # Exact latest frames for both modal layouts and their selected-row variants.
        press(driver, 'start')
        capture(driver, target, 'options')
        press(driver, 'a')
        capture(driver, target, 'sort')
        press(driver, 'b')
        press(driver, 'b')
    finally:
        driver.close()
    (target / 'measurements.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps([{k: v for k, v in r.items() if k not in ('costs', 'phases')} for r in records], indent=2))


def visual_case(task):
    from PIL import Image
    config, index, mode, phase, output = task
    output = Path(output)
    name = config['names'][index]
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                    output / f'{name}-{mode}-{phase}.log')
    result = dict(species=name, mode=mode, phase=phase,
                  presentation=config.get('listing_style', 'modern'), issues=[])
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    manifest = json.loads((Path(config['rom']).parent / 'sort-manifest.json').read_text())
    original_species = manifest['orders'][LABELS[0]][index]
    destination_species = manifest['orders'][LABELS[mode]][0] if mode else original_species
    replacement = destination_species != original_species
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        press(driver, 'start')
        press(driver, 'a')
        for _ in range(mode):
            press(driver, 'down')
        driver.run(frames=2 + phase / 8)
        before = bytes.fromhex(driver.command('inspectvram 0 32768 6144')['bytes'])
        driver.events.clear()
        with tempfile.TemporaryDirectory(prefix='dex-popover-frames-') as directory:
            temporary = Path(directory)
            driver.command(f'image {temporary}/old.ppm')
            old = Image.open(temporary / 'old.ppm').convert('RGB')
            asserted = driver.command('perf 1')
            driver.command(f'perfimages {temporary}/display')
            driver.run(('animation_miss', 'audio_miss'), frames=2, key='a')
            driver.run(('animation_miss', 'audio_miss'), frames=64)
            driver.command('perfimages -')
            driver.command('perf 0')
            paths = sorted(temporary.glob('display-*.ppm'))
            frames = [Image.open(path).convert('RGB') for path in paths]
            rectangle = (0, 0, 160, 144) if replacement else (64, 8, 155, 132)
            original = old.crop(rectangle).tobytes()
            references = {frame.crop(rectangle).tobytes() for frame in frames[-32:]}
            # The thumb at x55..59 correctly relocates when the selected
            # species acquires a new ordinal; it is not portrait corruption.
            sidebar = old.crop((0, 0, 54, 132)).tobytes()
            portrait_edge = old.crop((54, 0, 61, 65)).tobytes()
            header = old.crop((64, 8, 155, 24)).tobytes()
            observations = []
            for path, frame in zip(paths, frames):
                pixels = frame.crop(rectangle).tobytes()
                kind = ('old' if pixels == original else 'new' if pixels in references
                        else 'mask' if replacement and not any(frame.tobytes()) else 'mixed')
                observations.append(kind)
                if kind == 'mixed' or (not replacement and (
                        frame.crop((0, 0, 54, 132)).tobytes() != sidebar
                        or frame.crop((54, 0, 61, 65)).tobytes() != portrait_edge
                        or (config.get('listing_style') != 'legacy'
                            and frame.crop((64, 8, 155, 24)).tobytes() != header))):
                    result['issues'].append('partial_or_corrupted_display')
                    frame.save(output / f'{name}-{mode}-{phase}-{path.stem}.png')
            if 'new' not in observations or any(value != 'new' for value in observations[observations.index('new'):]):
                result['issues'].append('non_atomic_reveal')
            if not replacement and bytes.fromhex(driver.command('inspectvram 0 32768 6144')['bytes']) != before:
                result['issues'].append('bank0_graphics_changed')
            commits = [event for event in driver.events
                       if event['event'] == 'perf_cost' and event['name'] == 'popover_commit' and event['elapsed'] > 100]
            result['commit_cycles'] = [event['elapsed'] for event in commits]
            result['old_frames'] = observations.count('old')
            result['new_frames'] = observations.count('new')
            displays = [event for event in driver.events if event['event'] == 'perf_frame']
            visible = observations.index('new')
            first = next(i for i, value in enumerate(observations) if value != 'old')
            result['first_frames'] = (displays[first]['boundary_t'] - asserted['t']) / performance.T
            result['complete_frames'] = (displays[visible]['boundary_t'] - asserted['t']) / performance.T
            result['first_ms'] = result['first_frames'] * performance.T / performance.HZ * 1000
            result['complete_ms'] = result['complete_frames'] * performance.T / performance.HZ * 1000
            result['order_cycles'] = [event['elapsed'] for event in driver.events
                                      if event['event'] == 'perf_cost' and event['name'] == 'order']
            if any(event['elapsed'] > 4300 for event in commits):
                result['issues'].append('vblank_budget')
        if driver.command('peek')['jumptable'] != 1 or driver.command('peek')['mode'] != mode:
            result['issues'].append('sort_owner_or_mode')
        if mode and driver.command('peek')['index']:
            result['issues'].append('sort_cursor_not_reset')
        title_audit(driver, repo, species().index(destination_species) + 1)
        listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[mode]]))
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
    finally:
        driver.close()
    result['issues'] = sorted(set(result['issues']))
    return result


def visuals(output, jobs):
    target = output / 'visual-qualification'
    target.mkdir(exist_ok=True)
    tasks = []
    for config in configurations(output):
        local = target / config['listing_style']
        local.mkdir(exist_ok=True)
        tasks += [(config, config['names'].index(name), mode, phase, str(local))
                  for name in ('chikorita', 'unown_a', 'kyogre', 'regigigas')
                  for mode in range(3) for phase in range(8)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(visual_case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    return int(bool(summary['failures']))


def shifted_text_audit(driver, repo, tiles, attrs):
    font = offset(repo.symbols['Font'])
    start = offset(repo.symbols['PokedexPopover_Sort'])
    labels = repo.rom[start:start + 27].split(bytes((0x4e,)))
    labels[-1] = labels[-1].split(bytes((0x50,)))[0]
    cells = list(range(0x2a, 0x32)) + list(range(0x78, 0x80)) + list(range(0x64, 0x6c)) + list(range(0x70, 0x77))
    payload = b''.join(bytes.fromhex(driver.command(f'inspectvram 1 {address} {size}')['bytes'])
                       for address, size in ((0x92a0, 128), (0x9780, 128), (0x9640, 128), (0x9700, 112)))
    actual = {cell: payload[i * 16:i * 16 + 16] for i, cell in enumerate(cells)}

    def glyph(code):
        return bytes(8) if code == 0x7f else repo.rom[font + (code - 0x80) * 8:font + (code - 0x80 + 1) * 8]

    cursor = memory(driver, 3, 0xdc01, 1)[0]
    triangle = glyph(0xed)
    for row, label in enumerate(labels):
        previous = bytes(8)
        for column, code in enumerate(label.ljust(9, b'\x7f')):
            current = glyph(code)
            expected = bytearray()
            for y, (left, right) in enumerate(zip(previous, current)):
                white = ((left << 5) & 255) | (right >> 3)
                if not column and row == cursor:
                    white |= (triangle[y] << 5) & 255
                expected.extend((0, white ^ 255))
            position = (7 + row * 2) * 20 + 2 + column
            if attrs[position] != 8 or actual.get(tiles[position]) != expected:
                raise RuntimeError(f'Shifted native label/cursor differs at row {row}, cell {column}')
            previous = current
        position = (7 + row * 2) * 20 + 1
        if row == cursor:
            expected = bytes(value for plane in triangle for value in (0, (plane >> 3) ^ 255))
            if attrs[position] != 8 or actual.get(tiles[position]) != expected:
                raise RuntimeError('Shifted cursor body differs from the native font')
        elif (tiles[position], attrs[position]) != (0x7f, 0):
            raise RuntimeError('Inactive shifted cursor was not cleared')


def modal_audit(driver, kind, repo=None):
    ui = driver.command('ui')
    tiles = bytes.fromhex(ui['window'])
    attrs = bytes.fromhex(ui['window_attrs'])
    left, top, width, height = (1, 7, 9, 5) if kind == 0 else (0, 6, 11, 7)
    presentation = driver.command('peek')['presentation']
    shifted = kind == 1 and not presentation and repo is not None and 'PokedexPopover_ShiftCells' in repo.symbols
    top -= presentation
    if shifted:
        width = 12
    for y in range(height):
        for x in range(width):
            position = (top + y) * 20 + left + x
            expected = (0xfa if x == 0 else 0xfc if x == width - 1 else 0xfb) if y == 0 else (
                (0xfe if x == 0 else 0x28 if x == width - 1 else 0xff) if y == height - 1 else (
                    0xfd if x == 0 else 0x29 if x == width - 1 else None))
            if expected is not None and (tiles[position], attrs[position]) != (expected, 8):
                raise RuntimeError('Modal border tile or VRAM-bank attribute differs')
    artwork = memory(driver, 3, 0xdcb0, 128)
    uploaded = bytes.fromhex(driver.command('inspectvram 1 36768 96')['bytes']) + bytes.fromhex(
        driver.command('inspectvram 1 37504 32')['bytes'])
    if uploaded != artwork:
        raise RuntimeError('Modal border upload differs from the user sheet')
    if shifted:
        original = offset(repo.symbols['PokedexPopover_BorderGFX'])
        modern = offset(repo.symbols['PokedexPopover_ModernBorderGFX'])
        expected = bytearray(repo.rom[original:original + 128])
        strip = bytes.fromhex(driver.command('inspectvram 0 38592 16')['bytes'])
        for source, destination in enumerate((0, 2, 3, 7, 4, 6)):
            block = repo.rom[modern + source * 16:modern + (source + 1) * 16]
            if destination in (2, 6, 7):
                block = bytes((new & 0xe0) | (old & 0x1f) for new, old in zip(block, strip))
            expected[destination * 16:(destination + 1) * 16] = block
        if uploaded != expected:
            raise RuntimeError('Shifted border composition changed the outside Listing strip')
        shifted_text_audit(driver, repo, tiles, attrs)
    saved = memory(driver, 3, 0xdc10, 160)
    masked = bytes.fromhex(ui['oam'])
    for index in range(0, 160, 4):
        y, x = saved[index:index + 2]
        x0, x1 = (67, 155) if shifted else (left * 8 + 64, (left + width) * 8 + 64)
        overlap = x > x0 and x < x1 + 8 and y > top * 8 + 8 and y < (top + height) * 8 + 16
        expected = bytes((0,)) + saved[index + 1:index + 4] if overlap else saved[index:index + 4]
        if masked[index:index + 4] != expected:
            raise RuntimeError('Modal leaked or hid an uncovered sprite')
    if kind == 1 and not shifted:
        position = (top + 3) * 20 + 2
        if tiles[position:position + 8] != bytes((0x8d, 0xa0, 0xb3, 0xd1, 0x7f, 0x83, 0xa4, 0xb7)):
            raise RuntimeError('National label did not use the existing font')


def modal_case(task):
    config, index, phase, output = task
    output = Path(output)
    issues = []
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / f'{index}-{phase}.log')
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.run(frames=2 + phase / 8)
        press(driver, 'start')
        popup(driver, 0, 0)
        modal_audit(driver, 0, repo)
        driver.run(('animation_miss', 'audio_miss'), frames=30, key='a')
        driver.run(frames=4)
        popup(driver, 1, 0)
        modal_audit(driver, 1, repo)
        for _ in range(3):
            press(driver, 'down')
            modal_audit(driver, 1, repo)
        driver.run(('animation_miss', 'audio_miss'), frames=30, key='b')
        driver.run(frames=4)
        popup(driver, 0, 0)
        modal_audit(driver, 0, repo)
        press(driver, 'b')
        driver.run(('animation_miss', 'audio_miss'), frames=30, key='start')
        driver.run(frames=4)
        popup(driver, 0, 0)
        press(driver, 'start')
        press(driver, 'start')
        for _ in range(6):
            press(driver, 'a')
        settle(driver)
        if driver.command('peek')['jumptable'] != 3:
            raise RuntimeError('Rapid A did not reach the normal Selected owner')
        driver.run(('leave',), key='b')
        returned = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        if returned['index'] != index or returned['mode'] != 0:
            issues.append('modal_stress_lost_selection')
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            issues.append('modal_stress_playback_miss')
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
    finally:
        driver.close()
    return dict(index=index, phase=phase, presentation=config.get('listing_style', 'modern'), issues=issues)


def modal_tests(output, jobs):
    target = output / 'modal-qualification'
    target.mkdir(exist_ok=True)
    tasks = []
    for config in configurations(output):
        local = target / config['listing_style']
        local.mkdir(exist_ok=True)
        tasks += [(config, index, phase, str(local)) for index in range(9) for phase in range(8)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(modal_case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    return int(bool(summary['failures']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'qualify', 'edges', 'measure', 'integration', 'visuals', 'modal'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=10)
    parser.add_argument('--battery', type=Path,
                        default=ROOT / 'build/production-speed-integration-20261005/seed.sav')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    if args.action == 'qualify':
        return qualify(output, args.jobs)
    if args.action == 'edges':
        return max(edges(output, int(config['listing_style'] == 'legacy'))
                   for config in configurations(output))
    if args.action == 'integration':
        return integration(output, args.jobs)
    if args.action == 'visuals':
        return visuals(output, args.jobs)
    if args.action == 'modal':
        return modal_tests(output, args.jobs)
    return prepare(output, args.battery) if args.action == 'prepare' else measure(output)


if __name__ == '__main__':
    raise SystemExit(main())
