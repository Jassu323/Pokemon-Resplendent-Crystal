"""Build and qualify the two Listing presentations without replacing production."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from . import cold_listing, performance
from .assets import Repository, sha256, offset
from .cold_listing import ROOT, Driver, move, KEY, bootstrap
from .info_ui import BOOT, press, ready as info_ready
from .moves_ui import ready as moves_ready
from .description_ui import settle
from .assets import read_symbols
from .area_ui import reach


def build(output, jobs, refresh=False):
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / 'candidate'
    if candidate.exists() and not refresh:
        raise ValueError('Use a fresh prototype output directory')
    paths = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT
    ).decode().split('\0')
    for name in dict.fromkeys(paths):
        source = ROOT / name
        if name and source.is_file():
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    hashes = {suffix: sha256((ROOT / f'pokecrystal.{suffix}').read_bytes())
              for suffix in ('gbc', 'sym', 'map')}
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in hashes:
        shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'pokecrystal-dex-legacy.{suffix}')
        if sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()) != hashes[suffix]:
            raise ValueError('Production output changed')
    (output / 'production-hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


def open_mode_screen(driver):
    press(driver, 'select')
    for _ in range(120):
        state = driver.command('peek')
        if state['jumptable'] == 8:
            return
        driver.run(frames=1)
    raise RuntimeError('Listing mode screen did not initialize')


def select_presentation(driver, target):
    open_mode_screen(driver)
    current = driver.command('ui')['footer_cursor']
    # This field is the shared arrow-menu cursor, also used by the mode menu.
    for _ in range(abs(target - current)):
        press(driver, 'down' if target > current else 'up')
    press(driver, 'a')
    state = driver.run(('listing',), frames=600)
    if state['hit'] != 'listing':
        raise RuntimeError(f'Mode selection did not return to Listing: {state}')
    driver.run(('end_loop',))
    driver.run(('end_loop',))
    if driver.command('peek').get('presentation', target) != target:
        raise RuntimeError('Wrong Listing presentation after mode selection')


def layout_audit(repo, state, ui, unseen=(), uncaught=(), order=None):
    issues = []
    window = bytes.fromhex(ui['window'])
    attrs = bytes.fromhex(ui['window_attrs'])
    names = offset(repo.symbols['PokemonNames'])
    family = offset(repo.symbols['NewPokedexOrder'])
    for row in range(7):
        index = state['scroll'] + row
        text = b''
        if index < state['end']:
            species = order[index] if order is not None else int.from_bytes(
                repo.rom[family + 2 * index:family + 2 * index + 2], 'little')
            text = repo.rom[names + 10 * (species - 1):names + 10 * species].split(b'\x50')[0]
            if index in unseen:
                from pokedex_info_assets import Compiler
                text = bytes([Compiler().chars['-']] * 5)
        expected = text.ljust(10, b'\x7f')
        at = (2 + row * 2) * 20 + 1
        if window[at:at + 10] != expected:
            issues.append(f'row_{row}_name')
    if window[5] != 0x7e or window[16 * 20 + 5] != 0x7e or attrs[16 * 20 + 5] != 0x40:
        issues.append('navigation_marker')
    background = bytes.fromhex(ui['map'])
    background_attrs = bytes.fromhex(ui['attrs'])
    for row in range(17):
        expected = 0x63 if row in (0, 16) else 0x62 if row == 8 else 0x64
        at = row * 21 + 8
        if background[at] != expected or background_attrs[at] != (0x40 if row == 16 else 0):
            issues.append(f'divider_{row}')
    at = offset(repo.symbols['PokedexLegacyGFX'])
    if bytes.fromhex(ui['legacy_gfx']) != repo.rom[at:at + 64]:
        issues.append('resident_legacy_gfx')
    oam = bytes.fromhex(ui['oam'])
    y = 24 + 16 * state['cursor']
    cursor = bytes((y, 72, 0x40, 0, y, 151, 0x40, 0x20,
                    y + 15, 72, 0x40, 0x40, y + 15, 151, 0x40, 0x60))
    if oam[:16] != cursor:
        issues.append('cursor')
    balls = bytes(v for row in range(7) if state['scroll'] + row < state['end']
                  and state['scroll'] + row not in unseen and state['scroll'] + row not in uncaught
                  for v in (32 + 16 * row, 71, 0x41, 1))
    if oam[16:16 + len(balls)] != balls:
        issues.append('caught_marks')
    thumb = 16 + len(balls)
    if oam[thumb + 1:thumb + 4] != bytes((161, 15, 5)) or not 20 <= oam[thumb] <= 141:
        issues.append('scrollbar')
    if ui['wx'] != 71 or ui['scx'] != 5:
        issues.append('split_layout')
    return issues


def listing_case(task):
    config, index = task
    out = Path(config['output'])
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], out / f'{index:03}.log')
    issues, timings, pages = [], [], 0
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        driver.run(frames=2)
        state = driver.command('peek')
        issues += layout_audit(repo, state, driver.command('ui'))
        # Both SELECT and START are ignored by Selected Mon, including while
        # its animation/cry and lower-panel producer are active.
        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
        for key in ('select', 'start'):
            press(driver, key)
            selected = driver.command('peek')
            if selected['jumptable'] != 3 or selected['presentation'] != 1:
                issues.append('selected_mode_entry')
        settle(driver)
        press(driver, 'right')
        press(driver, 'a')
        ui = info_ready(driver, 0)
        count = ui['info_pages']
        # Exercise every Info page with a real B-return, then reopen it.
        for page in range(count):
            if page:
                driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                press(driver, 'right')
                press(driver, 'a')
                info_ready(driver, 0)
                for _ in range(page):
                    press(driver, 'a')
                info_ready(driver, page)
            for key in ('select', 'start'):
                press(driver, key)
                if driver.command('peek')['jumptable'] != 3:
                    issues.append('info_mode_entry')
            before = driver.run(('leave',), key='b')
            after = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            if after['hit'] != 'listing' or after['index'] != index:
                raise RuntimeError('Info B-return lost selection')
            timings.append((after['t'] - before['t']) / 70224)
            driver.run(frames=2)
            issues += layout_audit(repo, driver.command('peek'), driver.command('ui'))
            pages += 1
        # Moves must use the same Legacy return, with no grid repair or stale
        # type/evolution OAM left behind.
        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
        press(driver, 'right')
        press(driver, 'right')
        press(driver, 'a')
        moves_ready(driver)
        press(driver, 'select')
        if driver.command('peek')['jumptable'] != 3:
            issues.append('moves_mode_entry')
        driver.run(('leave',), key='b')
        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(frames=2)
        issues += layout_audit(repo, driver.command('peek'), driver.command('ui'))
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            issues.append('playback_miss')
        if issues:
            driver.evidence(out / f'{index:03}-failure')
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(out / f'{index:03}-error')
    finally:
        driver.close()
    return dict(index=index, species=config['names'][index], issues=issues, pages=pages, return_frames=timings)


def qualify(output, jobs):
    config = json.loads((output / 'legacy/config.json').read_text())
    out = output / 'listing-qualification'
    out.mkdir(exist_ok=True)
    config['output'] = str(out.resolve())
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(listing_case, [(config, i) for i in range(len(config['names']))]))
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}), flush=True)
    return int(bool(summary['failures']))


def navigation_case(task):
    from PIL import Image

    config, index, key = task
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    output = Path(config['output'])
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                    output / f'{index:03}-{key}.log')
    issues, observations = [], []
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        driver.run(frames=2)
        with tempfile.TemporaryDirectory(prefix='dex-legacy-navigation-') as directory:
            frames = Path(directory)
            driver.command(f'image {frames}/old.ppm')
            old = Image.open(frames / 'old.ppm').convert('RGB').tobytes()
            driver.command(f'perfimages {frames}/display')
            driver.command('perf 1')
            move(driver, key)
            driver.run(frames=3)
            driver.command('perfimages -')
            driver.command('perf 0')
            driver.command(f'image {frames}/new.ppm')
            new = Image.open(frames / 'new.ppm').convert('RGB').tobytes()
            for path in sorted(frames.glob('display-*.ppm')):
                pixels = Image.open(path).convert('RGB').tobytes()
                kind = 'old' if pixels == old else 'new' if pixels == new else 'mixed'
                observations.append(kind)
                if kind == 'mixed':
                    issues.append('mixed_display_frame')
                    shutil.copy2(path, output / f'{index:03}-{key}-{path.name}')
            if 'new' not in observations:
                issues.append('new_selection_not_displayed')
        state = driver.command('peek')
        if key in ('up', 'down'):
            expected = (index + (1 if key == 'down' else -1)) % state['end']
            if state['index'] != expected:
                issues.append('wrong_navigation_index')
        issues += layout_audit(repo, state, driver.command('ui'))
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / f'{index:03}-{key}-error')
    finally:
        driver.close()
    return dict(index=index, direction=key, issues=issues, displayed=observations)


def navigation_tests(output, jobs):
    config = json.loads((output / 'legacy/config.json').read_text())
    target = output / 'navigation'
    target.mkdir(exist_ok=True)
    config['output'] = str(target.resolve())
    tasks = [(config, index, 'down') for index in range(len(config['names']))]
    # Reverse motion and seven-row page jumps straddle both viewport and
    # 16-bit species/index boundaries, without modifying game memory.
    for index in (0, 1, 6, 7, 8, 254, 255, 256, 365, 371, 372):
        tasks.append((config, index, 'up'))
    for index in (0, 1, 6, 7, 254, 255, 256, 365):
        tasks.append((config, index, 'right'))
    for index in (7, 8, 254, 255, 256, 365, 372):
        tasks.append((config, index, 'left'))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(navigation_case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}), flush=True)
    return int(bool(summary['failures']))


def private_battery(config, target, *, presentation=1, unseen=(), uncaught=(),
                    order_mode=None, unown_unlocked=None):
    """Change only private fixture records, preserving offsets and checksums."""
    symbols = read_symbols(Path(config['sym']))
    data = bytearray(Path(config['battery']).read_bytes())
    ram = lambda name: symbols[name][1]
    def address(name):
        bank, at = symbols[name]
        return bank * 8192 + at - 0xa000
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    order = offset(repo.symbols['NewPokedexOrder'])
    for prefix in ('s', 'sBackup'):
        at = address(prefix + 'PlayerData') + ram('wLastDexPresentation') - ram('wPlayerData')
        data[at] = presentation
        if order_mode is not None:
            at = address(prefix + 'PlayerData') + ram('wLastDexMode') - ram('wPlayerData')
            data[at] = order_mode
        if unown_unlocked is not None:
            at = address(prefix + 'PlayerData') + ram('wStatusFlags') - ram('wPlayerData')
            data[at] = (data[at] | 2) if unown_unlocked else (data[at] & ~2)
            if unown_unlocked:
                at = address(prefix + 'PokemonData') + ram('wUnownDex') - ram('wPokemonData')
                data[at:at + 26] = bytes(range(1, 27))
                at = address(prefix + 'PokemonData') + ram('wFirstUnownSeen') - ram('wPokemonData')
                data[at] = 1
        for field, entries in (('Seen', unseen), ('Caught', (*unseen, *uncaught))):
            at = address(prefix + 'PokemonData') + ram('wPokedex' + field) - ram('wPokemonData')
            for index in entries:
                species = int.from_bytes(repo.rom[order + 2 * index:order + 2 * index + 2], 'little') - 1
                data[at + species // 8] &= ~(1 << (species & 7))
        start, end = address(prefix + 'SaveData'), address(prefix + 'SaveDataEnd')
        at = address(prefix + 'Checksum')
        data[at:at + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')
    target.write_bytes(data)


def mode_tests(output):
    config = json.loads((output / 'legacy/config.json').read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    records = []
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'mode-tests.log')
    try:
        for index in (0, 8, 9, 254, 255, 256, 370, 372):
            driver.command(f'load {config["states"]}/listing-{index:03}.s0')
            for presentation in (0, 1):
                select_presentation(driver, presentation)
                state = driver.command('peek')
                if state['index'] != index or state['presentation'] != presentation:
                    raise RuntimeError(f'Mode changed the selected species: {state}')
            # Mode-menu cancellation must restart clean preparation rather
            # than retaining a payload used for the menu cursor table.
            driver.run(frames=120)
            open_mode_screen(driver)
            press(driver, 'b')
            returned = driver.run(('listing',), frames=600)
            if returned['hit'] != 'listing':
                raise RuntimeError('Mode menu cancellation did not return to Listing')
            driver.run(('end_loop',))
            driver.run(('end_loop',))
            driver.events.clear()
            driver.command('audit 1')
            accepted = driver.run(('accept',), key='a')
            if accepted['hit'] != 'accept':
                raise RuntimeError('Mode cancellation did not accept Selected entry')
            final = settle(driver)
            asset = repo.load([config['names'][index]])[0]
            result = cold_listing.audit(asset, accepted, driver.events, final, cold=False,
                                        expected_double_speed=1)
            if result['issues']:
                raise RuntimeError(f'Mode cancellation playback: {result}')
            records.append(dict(test='mode_roundtrip', index=index, issues=[]))
        # Close and reopen through real overworld/start-menu inputs. The
        # preference lives in the existing saved player-data padding byte.
        driver.command(f'load {config["states"]}/listing-000.s0')
        select_presentation(driver, 0)
        select_presentation(driver, 1)
        returned = driver.run(('start_menu',), frames=600, key='b')
        if returned['hit'] != 'start_menu':
            raise RuntimeError('Could not close Dex to the start menu')
        driver.run(('start_menu',))
        driver.run(('start_menu',))
        returned = driver.run(('overworld',), frames=600, key='b')
        if returned['hit'] != 'overworld':
            raise RuntimeError('Could not close the start menu')
        cold_listing.bootstrap(driver)
        if driver.command('peek')['presentation'] != 1:
            raise RuntimeError('Listing preference did not survive closing the Dex')
        records.append(dict(test='reopen_preference', issues=[]))
    finally:
        driver.close()
    control = output / 'seen-control.sav'
    private_battery(config, control, unseen=(1,), uncaught=(2,))
    driver = Driver(config['core'], config['rom'], BOOT, control, output / 'seen-control.log')
    try:
        cold_listing.bootstrap(driver)
        driver.command('rawcolor')
        driver.run(frames=2)
        state = driver.command('peek')
        issues = layout_audit(repo, state, driver.command('ui'), unseen=(1,), uncaught=(2,))
        move(driver, 'down', 1)
        driver.run(frames=2)
        press(driver, 'a')
        if driver.command('peek')['jumptable'] != 1:
            issues.append('unseen_selection_allowed')
        move(driver, 'down', 2)
        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
        press(driver, 'right')
        press(driver, 'a')
        ui = info_ready(driver, 0)
        if ui['caught'] or ui['info_tiles'] or ui['info_minis']:
            issues.append('uncaught_info_not_blank')
        settle(driver)
        if issues:
            raise RuntimeError(f'Seen/caught control: {issues}')
        driver.command(f'image {output / "uncaught-info.ppm"}')
        records.append(dict(test='seen_caught_control', issues=[]))
    finally:
        driver.close()
    private_battery(config, output / 'pokecrystal-dex-legacy.sav')
    (output / 'mode-tests.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(dict(mode_cases=len(records), failures=0)))
    return 0


def menu_tests(output):
    from .shared_menu_fixtures import make_fixture

    config = json.loads((output / 'legacy/config.json').read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    records = []
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'search-tests.log')
    try:
        for presentation in (0, 1):
            for warmed in (False, True):
                driver.command(f'load {config["states"]}/listing-000.s0')
                select_presentation(driver, presentation)
                if warmed:
                    driver.run(frames=120)
                press(driver, 'start')
                reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                driver.run(frames=2)
                press(driver, 'down')
                press(driver, 'down')
                press(driver, 'a')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
                driver.run(frames=2)
                driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
                settle(driver)
                press(driver, 'select')
                if driver.command('peek')['jumptable'] != 3:
                    raise RuntimeError('Search Selected allowed mode switching')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen', key=KEY['b'])
                driver.run(frames=2)
                press(driver, 'b')
                reach(driver, repo, 'Pokedex_UpdateSearchScreen')
                driver.run(frames=2)
                press(driver, 'b')
                returned = driver.run(('listing',), frames=600)
                driver.run(frames=2)
                if returned['hit'] != 'listing' or returned['presentation'] != presentation:
                    raise RuntimeError('Search changed the presentation')
                if presentation:
                    # Reach row seven, not merely the four-row Search limit.
                    for index in range(1, 7):
                        move(driver, 'down', index)
                        driver.run(('end_loop',))
                        driver.run(('end_loop',))
                    state = driver.command('peek')
                    if state['scroll'] or state['cursor'] != 6:
                        raise RuntimeError('Legacy retained the Search navigation height')
                    issues = layout_audit(repo, state, driver.command('ui'))
                    if issues:
                        raise RuntimeError(f'Search Listing restoration: {issues}')
                if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
                    raise RuntimeError('Search playback miss')
                records.append(dict(test='search_roundtrip', presentation=presentation,
                                    warmed=warmed, issues=[]))
    finally:
        driver.close()
    # Use an isolated, checksum-verified fixture with all 26 Unown forms.
    fixture_path = output / 'unown-menu.sav'
    make_fixture(repo, Path(config['battery']), fixture_path)
    for presentation in (0, 1):
        driver = Driver(config['core'], config['rom'], BOOT, fixture_path,
                        output / f'unown-menu-{presentation}.log')
        try:
            bootstrap(driver)
            select_presentation(driver, presentation)
            open_mode_screen(driver)
            current = driver.command('ui')['footer_cursor']
            for _ in range(2 - current):
                press(driver, 'down')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateUnownMode')
            driver.run(frames=2)
            press(driver, 'right')
            press(driver, 'left')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            driver.run(frames=2)
            press(driver, 'b')
            returned = driver.run(('listing',), frames=600)
            if returned['hit'] != 'listing' or returned['presentation'] != presentation:
                raise RuntimeError('Unown changed the Listing presentation')
            records.append(dict(test='unown_roundtrip', presentation=presentation, issues=[]))
        finally:
            driver.close()
    (output / 'menu-tests.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(dict(menu_cases=len(records), failures=0)))
    return 0


def prepare_legacy(output, modern):
    output.mkdir(parents=True, exist_ok=True)
    states = output / 'listing-states'
    states.mkdir(exist_ok=True)
    driver = Driver(modern['core'], modern['rom'], BOOT, modern['battery'], output / 'prepare.log')
    try:
        driver.command(f'load {modern["states"]}/listing-000.s0')
        select_presentation(driver, 1)
        if driver.command('peek')['index'] != 0:
            raise RuntimeError('Mode switching changed the selected species')
        driver.command(f'image {output / "legacy-chikorita.ppm"}')
        for index in range(len(modern['names'])):
            if index:
                move(driver, 'down', index)
            driver.run(('end_loop',))
            state = driver.run(('end_loop',))
            if state['index'] != index or state['joy']:
                raise RuntimeError(f'Unexpected Legacy checkpoint: {state}')
            driver.command(f'save {states / f"listing-{index:03}.s0"}')
            if index % 30 == 0:
                print(f'Legacy checkpoints: {index + 1}/{len(modern["names"])}', flush=True)
    finally:
        driver.close()
    config = dict(modern, states=str(states.resolve()), output=str(output.resolve()), listing_style='legacy')
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'refresh', 'prepare', 'qualify', 'modes', 'navigation', 'menus'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--battery', type=Path,
                        default=ROOT / 'build/production-speed-integration-20261005/seed.sav')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    if args.action in ('build', 'refresh'):
        build(output, args.jobs, refresh=args.action == 'refresh')
    elif args.action == 'qualify':
        return qualify(output, args.jobs)
    elif args.action == 'modes':
        return mode_tests(output)
    elif args.action == 'navigation':
        return navigation_tests(output, args.jobs)
    elif args.action == 'menus':
        return menu_tests(output)
    else:
        modern_dir = output / 'modern'
        config_file = modern_dir / 'config.json'
        modern = performance.prepare(output / 'pokecrystal-dex-legacy.gbc',
                                     output / 'pokecrystal-dex-legacy.sym', args.battery, modern_dir)
        prepare_legacy(output / 'legacy', modern)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
