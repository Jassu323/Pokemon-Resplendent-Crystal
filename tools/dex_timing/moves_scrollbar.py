"""Visual review and input/asset checks for the supplied Moves scrollbar."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import statistics
import unittest

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press
from .moves_mode import enter, sort, audit, audit_sort, capture, state, sweep, page_sweep
from .area_ui import reach


def qualify(output):
    config = json.loads((output / 'modern/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    target = output / 'scrollbar-visual'
    target.mkdir(exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], target / 'trace.log')
    records = []
    try:
        bootstrap(driver)
        enter(driver, repo)
        for order in (0, 1):
            sort(driver, repo, order)

            def record(name):
                current = audit(driver, repo, manifest)
                path = target / f'{order}-{name}.png'
                capture(driver, path)
                records.append(dict(name=name, order=order, state=current, image=str(path)))

            record('first')
            press(driver, 'right')
            record('page-right')
            for _ in range(19):
                press(driver, 'right')
            record('middle')
            for _ in range(21):
                press(driver, 'right')
            record('last-page')
            if state(driver, repo)['scroll'] != len(manifest['moves']) - 8:
                raise AssertionError('Page jump did not reach the bottom')
            base = driver.command('ui')
            press(driver, 'start')
            reach(driver, repo, 'PokedexMovesMode_SortUpdate')
            audit_sort(driver, repo, base)
            capture(driver, target / f'{order}-popup-bottom.png')
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesMode_Update')
            record('popup-cancelled')
            for _ in range(8):
                press(driver, 'down')
            record('wrapped-top')
            if state(driver, repo)['scroll'] != 0:
                raise AssertionError('Down wrap did not reset the thumb')
            press(driver, 'up')
            record('wrapped-bottom')
            if state(driver, repo)['cursor'] != 7:
                raise AssertionError('Up wrap did not reach the final row')
            sort(driver, repo, 1 - order)
            record('changed-sort')
            if state(driver, repo)['scroll'] != 0:
                raise AssertionError('Changed sort did not reset the thumb')
    finally:
        driver.close()
    result = dict(rom_sha256=sha256(Path(config['rom']).read_bytes()), cases=len(records),
                  records=records, issues=[])
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('rom_sha256', 'cases', 'issues')}))
    return result


def mixed_entries(output, jobs):
    from move_discovery_assets import move_bitmap, seed_records
    config = json.loads((output / 'modern/config.json').read_text())
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    target = output / 'scrollbar-mixed'
    target.mkdir(exist_ok=True)
    tasks = []
    for name, indices in (('zero', []), ('one', manifest['orders'][0][:1]),
                          ('review', manifest['review_seen'])):
        directory = target / name
        directory.mkdir(exist_ok=True)
        battery = directory / 'private.sav'
        battery.write_bytes(seed_records((output / 'all-seen-tests.sav').read_bytes(),
                                        repo.symbols, move_bitmap(indices)))
        fixture = dict(manifest, fixture='mixed',
                       unknown=[i for i in range(1, len(manifest['moves']) + 1) if i not in indices])
        tasks += [(dict(config, battery=str(battery)), fixture, order, str(directory)) for order in (0, 1)]
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        results = list(pool.map(sweep, tasks))
        pages = list(pool.map(page_sweep, tasks))
    summary = dict(cases=sum(r['cases'] for r in results + pages), results=results, pages=pages,
                   failures=sum(bool(r['issues']) for r in results + pages))
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('cases', 'failures')}))
    if summary['failures']:
        raise AssertionError('Unseen entry scrollbar checks failed')
    return summary


def adjacent_regression(output, jobs):
    from .performance_regression import run
    important = {'chikorita', 'meganium', 'dusknoir', 'weavile', 'luxray', 'garchomp',
                 'bastiodon', 'rampardos', 'kyogre', 'groudon', 'rayquaza', 'metagross',
                 'chansey', 'snorlax', 'unown_a', 'seviper', 'eevee', 'tyrogue', 'exeggcute', 'mewtwo'}
    tasks = []
    for style in ('modern', 'legacy'):
        config = json.loads((output / style / 'config.json').read_text())
        config.update(listing_style=style, expected_double_speed=1)
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        assets = {asset.name: asset for asset in repo.load(config['names'])}
        for suite in ('cold', 'warm', 'paging', 'info', 'moves', 'area', 'info-stress', 'moves-stress'):
            directory = output / 'scrollbar-adjacent' / style / suite
            directory.mkdir(parents=True, exist_ok=True)
            local = dict(config, output=str(directory), boot=str(BOOT), uncaught=False,
                         paging=suite == 'paging', warm=suite == 'warm', follow_up=True, repeat_area=True)
            if suite in ('cold', 'warm', 'paging'):
                (directory / 'listing-states').symlink_to(config['states'], target_is_directory=True)
            for index, name in enumerate(config['names']):
                if name not in important:
                    continue
                if suite in ('cold', 'warm', 'paging'):
                    tasks.append((suite, (local, index, assets[name])))
                elif suite in ('info', 'moves'):
                    for phase in (('0', '8', '32', 'settled') if suite == 'info' else ('0', 'settled')):
                        tasks.append((suite, (local, index, name, phase)))
                elif suite == 'area':
                    for view in ('description', 'info', 'moves'):
                        for phase in ('0', 'settled'):
                            tasks.append((suite, (local, name, view, phase, 'b', 0)))
                else:
                    families = ('mash-a', 'hold-a', 'description', 'listing', 'species') if suite == 'info-stress' else (
                        'mash-a', 'hold-a', 'description', 'listing', 'species', 'a-b', 'info')
                    for phase in ('0', '8', '32', 'settled'):
                        for family in families:
                            tasks.append((suite, (local, index, name, phase, family)))
    results = []
    with ProcessPoolExecutor(max_workers=min(jobs, 6)) as pool:
        for result in pool.map(run, tasks):
            results.append(result)
            if len(results) % 100 == 0 or not result['passed']:
                print(json.dumps(dict(done=len(results), total=len(tasks), suite=result['suite'],
                                      passed=result['passed'])), flush=True)
    summary = dict(cases=len(results), species=sorted(important),
                   failures=sum(not row['passed'] for row in results), results=results)
    (output / 'scrollbar-adjacent/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if summary['failures']:
        raise AssertionError('Adjacent Dex regression failed')
    return summary


def final_qualification(output):
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    digest = sha256((output / (manifest['stem'] + '.gbc')).read_bytes())
    if digest != manifest['rom_sha256']:
        raise AssertionError('Cartridge changed after qualification')
    reports = {}
    for name in ('moves-mode-qualification/summary.json', 'scrollbar-visual/summary.json',
                 'scrollbar-mixed/summary.json', 'scrollbar-adjacent/summary.json'):
        path = output / name
        result = json.loads(path.read_text())
        if result.get('issues') or result.get('failures') or result.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Qualification failed: {name}')
        reports[name] = {key: result[key] for key in (
            'cases', 'page_cases', 'interface_cases', 'interface_checks', 'transitions') if key in result}
    for style in ('modern', 'legacy'):
        config = json.loads((output / style / 'config.json').read_text())
        if config['hashes']['rom_sha256'] != digest:
            raise AssertionError('Observers/checkpoints belong to another link')
    for path, expected in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != expected:
            raise AssertionError(f'Protected input changed: {path}')
    current = json.loads((output / 'moves-mode-qualification/summary.json').read_text())
    baseline = Path(current.get('alignment', {}).get('baseline', manifest['source']))
    old = json.loads((baseline / 'moves-mode-qualification/summary.json').read_text())
    previous = {(row['presentation'], row['phase']): row['transitions'] for row in old['interfaces']}
    latency = {}
    for name in current['interfaces'][0]['transitions']:
        latency[name] = {}
        for field in ('first_frames', 'complete_frames'):
            values = [row['transitions'][name][field] - previous[row['presentation'], row['phase']][name][field]
                      for row in current['interfaces']]
            latency[name][field] = dict(min=min(values), median=statistics.median(values), max=max(values))
    for name in ('MOVE_DISCOVERY_BUILD', 'DEX_MOVES_MODE_BUILD', 'DEX_OPTIONS_BUILD', 'DEX_SEARCH_BUILD'):
        os.environ[name] = str(output)
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'tools.test_move_discovery', 'tools.test_pokedex_moves_mode', 'tools.test_pokedex_moves',
        'tools.test_pokedex_sort', 'tools.test_pokedex_search_results'])
    host = unittest.TextTestRunner().run(suite)
    if not host.wasSuccessful():
        raise AssertionError('Final host tests failed')
    from .assets import read_symbols, offset
    symbols = read_symbols(output / (manifest['stem'] + '.sym'))
    old_symbols = read_symbols(baseline / 'pokecrystal-dex-moves-persistence.sym')
    rom = (output / (manifest['stem'] + '.gbc')).read_bytes()
    original = (baseline / 'pokecrystal-dex-moves-persistence.gbc').read_bytes()
    at, prior = offset(symbols['MoveDiscovery_CheckIndex']), offset(old_symbols['MoveDiscovery_CheckIndex'])
    # The complete isolated storage library has no renderer dependency.
    if rom[at:at + 843] != original[prior:prior + 843]:
        raise AssertionError('Scrollbar changed the persistence library')
    pixels = pixel_audit(output, Repository(ROOT, output / (manifest['stem'] + '.gbc'),
                                          output / (manifest['stem'] + '.sym')))
    result = dict(rom_sha256=digest, host_tests=host.testsRun, reports=reports,
                  scrollbar_pixel_audit=pixels,
                  sort_popup_alignment=current.get('alignment'), latency_baseline=str(baseline),
                  latency_delta_display_intervals=latency, production_unchanged=True,
                  prior_persistence_unchanged=True, persistence_library_bytes_unchanged=843,
                  gameplay_hooks=False, issues=[])
    (output / 'final-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('rom_sha256', 'host_tests', 'reports', 'issues')}))
    return result


def pixel_audit(output, repo):
    from PIL import Image
    from .assets import offset

    def palette(label):
        at = offset(repo.symbols[label])
        result = []
        for i in range(4):
            word = int.from_bytes(repo.rom[at + i * 2:at + i * 2 + 2], 'little')
            values = [(word >> shift) & 31 for shift in (0, 5, 10)]
            result.append(tuple((v << 3) | (v >> 2) for v in values))
        return result

    bg, obj = palette('PokedexUIPalette'), palette('PokedexListScrollThumbPalette')
    colors = {255: bg[0], 170: bg[1], 85: bg[2]}
    with Image.open(output / 'candidate/gfx/pokedex/pokedex_moves_scroll_bar_and_borders.png') as source:
        source = source.convert('RGB')
        art = [source.getpixel((x, y))[0] for y in range(24) for x in range(16)]
    thumb = (output / 'candidate/gfx/pokedex/slowpoke.2bpp').read_bytes()[15 * 16:16 * 16]
    visual = json.loads((output / 'scrollbar-visual/summary.json').read_text())
    checks = 0
    for record in visual['records']:
        scroll = record['state']['scroll']
        maximum = len(json.loads((output / 'moves-mode-manifest.json').read_text())['moves']) - 8
        thumb_y = 4 + (scroll * 65 + maximum // 2) // maximum
        with Image.open(record['image']) as image:
            image = image.convert('RGB')
            for y in range(80):
                source_y = y if y < 8 else 16 + y - 72 if y >= 72 else 8 + y % 8
                for x in range(147, 160):
                    expected = colors[art[source_y * 16 + x - 147]]
                    if 152 <= x < 160 and thumb_y <= y < thumb_y + 8:
                        dy, bit = y - thumb_y, 7 - (x - 152)
                        code = ((thumb[dy * 2] >> bit) & 1) | (((thumb[dy * 2 + 1] >> bit) & 1) << 1)
                        if code:
                            expected = obj[code]
                    if image.getpixel((x, y)) != expected:
                        raise AssertionError(f'Scrollbar render differs: {record["image"]} pixel {x},{y}')
                    checks += 1
    return dict(images=len(visual['records']), pixel_checks=checks, mismatches=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mixed', action='store_true')
    parser.add_argument('--adjacent', action='store_true')
    parser.add_argument('--final', action='store_true')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use private build paths')
    if args.all:
        from .moves_mode import qualify as qualify_moves
        qualify(output)
        if qualify_moves(output, min(args.jobs, 6)):
            raise AssertionError('Moves navigation/transition checks failed')
        mixed_entries(output, args.jobs)
        adjacent_regression(output, args.jobs)
        final_qualification(output)
    elif args.final:
        final_qualification(output)
    elif args.adjacent:
        adjacent_regression(output, args.jobs)
    elif args.mixed:
        mixed_entries(output, args.jobs)
    else:
        qualify(output)


if __name__ == '__main__':
    main()
