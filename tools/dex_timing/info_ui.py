"""Normal-input Info rendering, paging, and playback regression.

All-caught fixture changes are confined to a new battery copy in build/.
The emulator commands never patch live RAM, instructions, or producer state.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

from .assets import Repository, read_symbols, sha256, offset
from .cold_listing import Driver, ROOT, build_core, bootstrap, prepare_states, move, predecessor, audit
from .description_ui import (expected_types, audit_type_sprites, audit_footprint,
                             linked, settle, audit as description_audit,
                             settle_description_text)
from pokedex_info_assets import Compiler, LABELS, width, species

BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')


def fixture(source, destination, caught=True):
    """Update both save records and their checksums, leaving the original alone."""
    symbols = read_symbols(ROOT / 'pokecrystal.sym')
    data = bytearray(source.read_bytes())
    original = bytes(data)
    ram = lambda name: symbols[name][1]
    def address(name):
        bank, at = symbols[name]
        return bank * 8192 + at - 0xa000
    for prefix in ('s', 'sBackup'):
        for field in ('Seen', 'Caught'):
            start = address(prefix + 'PokemonData') + ram('wPokedex' + field) - ram('wPokemonData')
            for index in range(len(species())):
                if field == 'Seen' or caught:
                    data[start + index // 8] |= 1 << (index & 7)
                else:
                    data[start + index // 8] &= ~(1 << (index & 7))
        start, end = address(prefix + 'SaveData'), address(prefix + 'SaveDataEnd')
        at = address(prefix + 'Checksum')
        data[at:at + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    assert source.read_bytes() == original


def type_audit(repo, name, ui):
    issues = audit_footprint(repo, name, ui) + audit_type_sprites(repo, ui)
    types = expected_types(repo, name)
    if ui['types'] != types:
        issues.append('type_species')
    return issues


def info_audit(compiler, data, name, page, ui, repo=None):
    constant = {'unown_a': 'UNOWN', 'porygonz': 'PORYGON_Z'}.get(name, name.upper())
    issues = []
    if ui['view'] != 1 or ui['info_page'] != page or ui['info_state']:
        issues.append('info_owner')
    if ui['info_pages'] != 1 + (len(data['roots'][constant]) + 1) // 2:
        issues.append('page_count')
    raw = bytes.fromhex(ui['lower_tiles'])
    def tile(row, col):
        start = ((row - 8) * 21 + col) * 16
        return raw[start:start + 16]
    attrs = bytes.fromhex(ui['attrs'])
    tilemap = bytes.fromhex(ui['map'])
    if repo and 'PokedexBadgeSingleGFX' in repo.symbols:
        from .moves_ui import badge_audit
        issues += badge_audit(repo, ui, page + 1)
    else:
        upper = (0x73, 0x79, 0x7b, 0x7d)[page]
        lower = (0x78, 0x7a, 0x7c, 0x7e)[page]
        if tilemap[8 * 21 + 2] != upper or tilemap[9 * 21 + 1:9 * 21 + 3] != bytes((0x77, lower)):
            issues.append('page_badge')
    if not ui['caught']:
        if ui['info_tiles'] or ui['info_minis'] or any(bytes.fromhex(ui['oam'])[32:64]):
            issues.append('uncaught_information')
        for row in range(9, 16):
            for col in range(3 if row == 9 else 1, 20):
                if tilemap[row * 21 + col] != 0x32 or attrs[row * 21 + col]:
                    issues.append(f'uncaught_content_{row}_{col}')
        return issues
    title = data['titles']['Evolutions' if page else 'Stats']
    for col, (cell, pixels) in enumerate(zip(title['cells'], title['tiles']), 4):
        if (tilemap[9 * 21 + col] != cell or attrs[9 * 21 + col]
                or tile(9, col) != pixels):
            issues.append(f'title_{col}')
    if tilemap[9 * 21 + 3] != 0x32:
        issues.append('title_gutter')
    if not page:
        if repo and bytes.fromhex(ui['palettes'])[16:64] != linked(repo, 'PokedexInfoStatPalettes', 48):
            issues.append('stat_colors')
        for row, value in enumerate(data['stats'][constant]):
            for col, source in enumerate(data['numbers'][value]):
                if tile(10 + row, 4 + col) != compiler.pool[source]:
                    issues.append(f'number_{row}_{col}')
            label = data['labels'][row]
            for col, index in enumerate(label):
                if tile(10 + row, 1 + col) != compiler.pool[data['shared'][index]]:
                    issues.append(f'label_{row}_{col}')
            if attrs[(10 + row) * 21 + 7] & 7 != row + 2:
                issues.append(f'stat_palette_{row}')
            remaining, col = max(0, width(value) - 3), 8
            while remaining and col < 20:
                if remaining > 8:
                    index, take = 14, 8
                else:
                    index, take = 10 + (remaining - 1) // 2, remaining
                if tile(10 + row, col) != compiler.pool[data['shared'][index]]:
                    issues.append(f'bar_{row}_{col}')
                remaining -= take
                col += 1
        hp = width(data['stats'][constant][0])
        endpoint = bytes.fromhex(ui['oam'])[32:36]
        expected = bytes((96, 163, 0x58 + (hp == 101), 12)) if hp >= 100 else bytes(4)
        if endpoint != expected:
            issues.append('hp_endpoint')
    else:
        entries = data['roots'][constant][(page - 1) * 2:page * 2]
        if ui['info_minis'] != len(entries):
            issues.append('mini_count')
        for entry, record in enumerate(entries):
            if repo:
                target = data['names'].index(data['records'][record][0])
                ptr = linked(repo, 'MonMenuIcons', len(data['names']) * 4)[target * 4:target * 4 + 4]
                at = offset((ptr[0], int.from_bytes(ptr[1:3], 'little')))
                if bytes.fromhex(ui['mini_gfx'])[entry * 128:(entry + 1) * 128] != repo.rom[at:at + 128]:
                    issues.append(f'minisprite_graphics_{entry}')
                pal = linked(repo, 'PartyMenuOBPals', 16 * 8)[(ptr[3] >> 4) * 8:(ptr[3] >> 4) * 8 + 8]
                if bytes.fromhex(ui['obj_palettes'])[(entry + 2) * 8:(entry + 3) * 8] != pal:
                    issues.append(f'minisprite_palette_{entry}')
            oam = bytes.fromhex(ui['oam'])[32 + entry * 16:48 + entry * 16]
            positions = bytes(v for y, x in ((104 + entry * 24, 16),
                                           (104 + entry * 24, 24),
                                           (112 + entry * 24, 16),
                                           (112 + entry * 24, 24)) for v in (y, x))
            if bytes(v for index, v in enumerate(oam) if index % 4 < 2) != positions:
                issues.append(f'minisprite_position_{entry}')
            for line, line_id in enumerate(data['records'][record][1][:2]):
                for col, source in enumerate(data['lines'][line_id][1]):
                    if tile(11 + entry * 3 + line, 4 + col) != compiler.pool[source]:
                        issues.append(f'evolution_{entry}_{line}_{col}')
        if ui['info_tiles'] > 40:
            issues.append('atlas_overflow')
    return issues


def press(driver, key):
    result = driver.run(('animation_miss', 'audio_miss'), frames=2, key=key)
    if result['hit']:
        raise RuntimeError(f'Playback miss during {key}: {result}')
    result = driver.run(('animation_miss', 'audio_miss'), frames=2)
    if result['hit']:
        raise RuntimeError(f'Playback miss after {key}: {result}')


def ready(driver, page):
    for _ in range(240):
        ui = driver.command('ui')
        if ui['view'] == 1 and (page is None or ui['info_page'] == page) and ui['info_state'] == 0 and not ui['owner_transition'] and not ui.get('info_pending_page', 0):
            driver.run(('animation_miss', 'audio_miss'), frames=1)
            check = driver.command('ui')
            if check['info_state'] == 0 and not check['owner_transition'] and not check.get('info_pending_page', 0):
                return check
        state = driver.run(('animation_miss', 'audio_miss'), frames=1)
        if state['hit']:
            raise RuntimeError(f'Playback miss preparing Info: {state}')
    raise RuntimeError('Info job did not publish')


def run_stress(task):
    config, index, name, offset, family = task
    from .description_paging import description_pages
    repo = Repository(ROOT, Path(config['rom']), Path(config.get('sym', ROOT / 'pokecrystal.sym')))
    compiler = Compiler()
    data = compiler.compile()
    output = Path(config['output'])
    label = f'{name}-{offset}-{family}'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (label + '.log'))
    issues = []
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        move(driver, direction, index)
        driver.command('audit 1')
        driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        press(driver, 'right')
        press(driver, 'a')
        if offset == 'settled':
            settle(driver)
        else:
            result = driver.run(('animation_miss', 'audio_miss'), frames=int(offset))
            if result['hit']:
                raise RuntimeError(f'Miss before cancellation: {result}')
        if family == 'mash-a':
            for _ in range(12):
                press(driver, 'a')
        elif family == 'hold-a':
            result = driver.run(('animation_miss', 'audio_miss'), frames=60, key='a')
            if result['hit']:
                raise RuntimeError(f'Miss with held A: {result}')
            driver.run(('animation_miss', 'audio_miss'), frames=4)
        elif family == 'description':
            press(driver, 'left')
            press(driver, 'a')
            settle_description_text(driver, description_pages(repo, name)[0])
            ui = driver.command('ui')
            issues += description_audit(repo, ui) + type_audit(repo, name, ui)
            if ui['view'] or any(bytes.fromhex(ui['oam'])[32:64]):
                issues.append('description_cancel_owner')
            settle(driver)
        elif family == 'listing':
            driver.run(('leave',), key='b')
            result = driver.run(('listing',), frames=1200)
            if result['hit'] != 'listing':
                issues.append('listing_cancel')
        elif family == 'species':
            target = index + 1 if index < 372 else index - 1
            driver.events.clear()
            accepted = driver.run(('change_species',), key='down' if target > index else 'up')
            driver.run(('selected', 'animation_miss', 'audio_miss'))
            ui = ready(driver, 0)
            target_name = config['names'][target]
            issues += type_audit(repo, target_name, ui) + info_audit(compiler, data, target_name, 0, ui, repo)
            if ui['footer_cursor'] != 1:
                issues.append('species_cancel_cursor')
            final = settle(driver)
            reveal = next(e['t'] for e in driver.events if e['event'] == 'reveal')
            incoming_events = [e for e in driver.events if e['t'] >= reveal]
            issues += audit(repo.load([target_name])[0], accepted, incoming_events,
                            final, cold=False)['issues']
        else:
            raise ValueError(family)
        if family in ('mash-a', 'hold-a'):
            ui = ready(driver, None)
            issues += type_audit(repo, name, ui) + info_audit(compiler, data, name, ui['info_page'], ui, repo)
            settle(driver)
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            issues.append('playback_miss')
        (output / (label + '.json')).write_text(json.dumps(driver.events, indent=2) + '\n')
    except Exception as error:
        issues.append(str(error))
        driver.evidence(output / (label + '-failure'))
    finally:
        driver.close()
    return dict(species=name, phase=offset, family=family, issues=issues)


def run_case(task):
    config, index, name, offset = task
    output = Path(config['output'])
    repo = Repository(ROOT, Path(config['rom']), Path(config.get('sym', ROOT / 'pokecrystal.sym')))
    compiler = Compiler()
    data = compiler.compile()
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / f'{name}-{offset}.log')
    issues, pages, timings, playback, slice_costs = [], [], [], [], {}
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        if offset == 'settled':
            settle(driver)
        else:
            driver.run(('animation_miss', 'audio_miss'), frames=int(offset))
        press(driver, 'right')
        start = driver.command('peek')['t']
        press(driver, 'a')
        ui = ready(driver, 0)
        timings.append((driver.command('peek')['t'] - start) / 70224)
        page_count = ui['info_pages']
        for page in range(page_count):
            if page:
                press(driver, 'a')
                ui = ready(driver, page)
            issues += type_audit(repo, name, ui) + info_audit(compiler, data, name, page, ui, repo)
            if ui['caught'] != int(not config['uncaught']):
                issues.append('caught_fixture_mismatch')
            pages.append(ui)
            if offset == 'settled':
                driver.command(f'image {output / name}-info-{page + 1}.ppm')
            if page and ui['info_minis']:
                before = bytes.fromhex(ui['oam'])[34]
                driver.run(('animation_miss', 'audio_miss'), frames=8)
                after = bytes.fromhex(driver.command('ui')['oam'])[34]
                if before == after:
                    issues.append('minisprite_not_animated')
        press(driver, 'a')
        ui = ready(driver, 0)
        issues += info_audit(compiler, data, name, 0, ui, repo)
        final = settle(driver)
        result = audit(repo.load([name])[0], accepted, driver.events, final)
        playback.append(result)
        issues += result['issues']
        source_events = list(driver.events)
        for event in source_events:
            if event['event'] == 'info_slice':
                key = str(event['state'])
                slice_costs[key] = max(slice_costs.get(key, 0), event['elapsed'])
        # Internal species paging while Info owns the panel must reset to Stats.
        target = index + 1 if index < 372 else index - 1
        driver.events.clear()
        accepted = driver.run(('change_species',), key='down' if target > index else 'up')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        ui = ready(driver, 0)
        names = config['names']
        issues += type_audit(repo, names[target], ui) + info_audit(compiler, data, names[target], 0, ui, repo)
        if ui['footer_cursor'] != 1:
            issues.append('internal_info_cursor')
        final = settle(driver)
        result = audit(repo.load([names[target]])[0], accepted, driver.events, final, cold=False)
        playback.append(result)
        issues += result['issues']
        press(driver, 'a')
        next_page = int(ui['info_pages'] > 1)
        ui = ready(driver, next_page)
        issues += info_audit(compiler, data, names[target], next_page, ui, repo)
        # Restore Description without restarting its animation or cry.
        press(driver, 'left')
        press(driver, 'a')
        for _ in range(100):
            driver.run(('animation_miss', 'audio_miss'), frames=1)
            ui = driver.command('ui')
            if ui['view'] == 0 and not ui['owner_transition'] and not any(bytes.fromhex(ui['oam'])[32:64]):
                break
        else:
            issues.append('description_restore')
        if not config['uncaught']:
            from .description_paging import description_pages
            settle_description_text(driver, description_pages(repo, names[target])[0])
        ui = driver.command('ui')
        issues += description_audit(repo, ui)
        if config['uncaught']:
            tilemap = bytes.fromhex(ui['map'])
            for row in range(9, 16):
                for col in range(3 if row == 9 else 1, 20):
                    if tilemap[row * 21 + col] != 0x32:
                        issues.append(f'uncaught_description_{row}_{col}')
        driver.run(('leave',), key='b')
        state = driver.run(('listing',), frames=1200)
        if state['hit'] != 'listing':
            issues.append('listing_return')
        misses = [event for event in driver.events if event['event'] in ('animation_miss', 'audio_miss')]
        if misses:
            issues.append('playback_miss')
        (output / f'{name}-{offset}.json').write_text(json.dumps(dict(
            pages=pages, source_events=source_events, events=driver.events), indent=2) + '\n')
    except Exception as error:
        issues.append(str(error))
        driver.evidence(output / f'{name}-{offset}-failure')
    finally:
        driver.close()
    return dict(species=name, phase=offset, issues=issues, stats_ready_frames=timings,
                slice_costs=slice_costs, playback=playback)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--phases', nargs='+', default=['0', '8', '32', 'settled'])
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--reuse', action='store_true')
    parser.add_argument('--uncaught', action='store_true')
    parser.add_argument('--stress', action='store_true', help='Rapid inputs and cancellation of unfinished Info jobs')
    parser.add_argument('--families', nargs='+', choices=['mash-a', 'hold-a', 'description', 'listing', 'species'],
                        help='Optional subset of stress families')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.rom, args.sym)
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    names = [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower()) for n in names]
    battery = args.output / 'fixture.sav'
    fixture(args.battery, battery, not args.uncaught)
    core = build_core(repo, Path.home() / 'Documents/GitHub/SameBoy', args.output)
    states = args.output / 'listing-states'
    states.mkdir(exist_ok=True)
    provenance = dict(repo.hashes, battery_sha256=sha256(battery.read_bytes()))
    checkpoint_manifest = args.output / 'provenance.json'
    if args.reuse and (not checkpoint_manifest.exists() or json.loads(checkpoint_manifest.read_text()) != provenance):
        raise ValueError('Regenerate checkpoints for the current ROM, symbols, and private save')
    if not args.reuse:
        driver = Driver(core, args.rom, BOOT, battery, args.output / 'bootstrap.log')
        try:
            bootstrap(driver)
            prepare_states(driver, states, len(names))
        finally:
            driver.close()
        checkpoint_manifest.write_text(json.dumps(provenance, indent=2) + '\n')
    config = dict(core=str(core), rom=str(args.rom), sym=str(args.sym), battery=str(battery),
                  states=str(states), output=str(args.output), names=names, uncaught=args.uncaught)
    tasks = [(config, i, name, phase) for i, name in enumerate(names)
             if not args.species or name in args.species for phase in args.phases]
    runner = run_case
    if args.stress:
        runner = run_stress
        tasks = [(*task, family) for task in tasks
                 for family in (args.families or ('mash-a', 'hold-a', 'description', 'listing', 'species'))]
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(runner, tasks):
            rows.append(row)
            print(json.dumps(row), flush=True)
            (args.output / 'report.json').write_text(json.dumps(rows, indent=2) + '\n')
    totals = dict(tested=len(rows), passed=sum(not row['issues'] for row in rows))
    (args.output / 'totals.json').write_text(json.dumps(totals, indent=2) + '\n')
    print(json.dumps(totals))
    return int(totals['tested'] != totals['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
