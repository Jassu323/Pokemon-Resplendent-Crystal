"""Ranked Search pairs and frame-by-frame compact-icon publication audits."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image

from . import performance
from .area_ui import reach
from .assets import Repository, offset
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT, press
from .listing_options import configuration, choose, LABELS
from .legacy_listing import private_battery
from .search_qualification import expected_results, icons_audit, ram, source_types, choose_types, selector_types


@lru_cache(maxsize=32)
def icon_data(rom, sym, selected):
    repo = Repository(ROOT, Path(rom), Path(sym))
    actual = repo.rom[offset(repo.symbols['PokedexTypeSearchConversionTable']) + selected - 1]
    at = offset(repo.symbols['CompactTypeIconGFXPointers']) + actual * 3
    bank, address = repo.rom[at], int.from_bytes(repo.rom[at + 1:at + 3], 'little')
    tile = bytearray(repo.rom[offset((bank, address)):][:64])
    for i in (0, 14):
        tile[i] |= 128
    for i in (48, 62):
        tile[i] |= 1
    for i in range(0, 64, 2):
        tile[i] = ~(tile[i] ^ tile[i + 1]) & 255
    at = offset(repo.symbols['TypeIconPalettePointers']) + actual * 2
    address = int.from_bytes(repo.rom[at:at + 2], 'little')
    palette = bytearray(repo.rom[offset((repo.symbols['TypeIconPalettes'][0], address)):][:8])
    palette[2:4] = palette[:2]
    return bytes(tile), bytes(palette)


def scanout_audit(config, frames):
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    none = repo.rom[offset(repo.symbols['PokedexTypeSearchStrings']):][:8]
    for frame in frames:
        selected = bytes.fromhex(frame['committed'])
        oam, tiles, palettes, fields = (bytes.fromhex(frame[key])
                                        for key in ('oam', 'tiles', 'palettes', 'fields'))
        buffer = oam[2] - 0x28
        if buffer not in (0, 8):
            raise RuntimeError('Visible scanout references an invalid icon buffer')
        for field, value in enumerate(selected):
            sprite = oam[field * 16:field * 16 + 16]
            expected_field = none if not value else b'\x7f' * 8
            if fields[field * 8:field * 8 + 8] != expected_field:
                raise RuntimeError('Visible BG placeholder and type icon were not committed together')
            if not value:
                if any(sprite):
                    raise RuntimeError('Visible scanout retains an icon for None')
                continue
            expected, pal = icon_data(config['rom'], config['sym'], value)
            start = buffer * 16 + field * 64
            if tiles[start:start + 64] != expected or palettes[field * 8:field * 8 + 8] != pal:
                raise RuntimeError('Visible scanout pairs a new icon with old graphics/colors')
            if sprite != bytes(v for i in range(4) for v in
                               (48 + field * 16, 96 + i * 8, 0x28 + buffer + field * 4 + i, 9 + field)):
                raise RuntimeError('Visible scanout contains a partially written icon OAM row')


def prepare(source, output):
    output.mkdir(parents=True, exist_ok=True)
    initial = configuration(source)
    repo = Repository(ROOT, Path(initial['rom']), Path(initial['sym']))
    compiled = performance.core(repo, output / 'core', extra_flags=('-DDEX_SEARCH_ICON_TRACE',))
    configs = []
    for style in ('modern', 'legacy'):
        config = configuration(source, style)
        config['core'] = str(compiled)
        for mode in range(3):
            checkpoint = output / f'{style}-{mode}.s0'
            driver = Driver(compiled, config['rom'], BOOT, config['battery'], output / f'{style}-{mode}-prepare.log')
            try:
                driver.command(f'load {config["states"]}/listing-000.s0')
                if mode:
                    choose(driver, mode)
                press(driver, 'start')
                press(driver, 'down')
                reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['a'])
                driver.run(frames=2)
                icons_audit(driver, repo)
                driver.command(f'save {checkpoint}')
            finally:
                driver.close()
            configs.append(dict(config, checkpoint=str(checkpoint), order=LABELS[mode]))
    (output / 'configs.json').write_text(json.dumps(configs, indent=2) + '\n')
    return configs


def run_pair(task):
    config, one, two, target = task
    output = Path(target)
    name = f'{config["listing_style"]}-{config["order"]}-{one}-{two}'
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    manifest = json.loads((Path(config['rom']).parent / 'sort-manifest.json').read_text())
    unseen = ()
    if 'seen_count' in config:
        count = config['seen_count']
        name += f'-seen{count}'
        battery = output / (name + '.sav')
        private_battery(config, battery, presentation=int(config['listing_style'] == 'legacy'),
                        order_mode=LABELS.index(config['order']),
                        unseen=tuple(range(count, len(manifest['orders'][LABELS[0]]))),
                        uncaught=tuple(range(count)))
        ids = source_types()[1]
        unseen = tuple(ids[name] for name in manifest['orders'][LABELS[0]][count:])
        config = dict(config, battery=str(battery))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    result = dict(presentation=config['listing_style'], order=config['order'], types=[one, two], issues=[])
    try:
        if 'seen_count' in config:
            bootstrap(driver, expected_mode=LABELS.index(config['order']))
            press(driver, 'start')
            press(driver, 'down')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['a'])
            driver.run(frames=2)
            result['seen_count'] = config['seen_count']
        else:
            driver.command(f'load {config["checkpoint"]}')
        driver.command('perf 1')
        choose_types(driver, repo, one, two)
        press(driver, 'down')
        driver.run(frames=2)
        icons_audit(driver, repo)
        if tuple(ram(driver, repo, label)[0] for label in ('wDexSearchMonType1', 'wDexSearchMonType2')) != (one, two):
            raise RuntimeError('Type selection dropped a normal input')
        frames = [e for e in driver.events if e['event'] == 'search_icon_scanout']
        scanout_audit(config, frames)
        driver.command('perf 0')
        reach(driver, repo, 'AnimateDexSearchSlowpoke', KEY['a'])
        expected = expected_results(manifest['orders'][config['order']], (one, two), unseen,
                                    ranked=True, table=selector_types(repo))
        actual = ram(driver, repo, 'wPokedexOrder', len(expected) * 2) if expected else b''
        if actual != b''.join(value.to_bytes(2, 'little') for value in expected):
            raise RuntimeError('Both/Type1-only/Type2-only groups differ from the source-data oracle')
        count = int.from_bytes(ram(driver, repo, 'wDexSearchResultCount', 2), 'little')
        if count != len(expected) or len(set(expected)) != len(expected):
            raise RuntimeError('Result count or duplicate suppression is incorrect')
        if ram(driver, repo, 'wPokedexOrder', (count + 1) * 2)[-2:] != b'\xff\xff':
            raise RuntimeError('Filtered order has no valid terminator')
        result.update(matches=count, scanouts=len(frames))
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
        driver.evidence(output / (name + '-error'))
    finally:
        driver.close()
    return result


def run_stress(task):
    config, phase, kind, target = task
    output = Path(target)
    name = f'{config["listing_style"]}-{config["order"]}-{phase}-{kind}'
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    result = dict(presentation=config['listing_style'], order=config['order'], phase=phase,
                  kind=kind, issues=[])
    try:
        driver.command(f'load {config["checkpoint"]}')
        driver.run(frames=phase / 8)
        if kind == 'none_timing':
            press(driver, 'down')
            press(driver, 'left')
        before = driver.command('perf 1')
        if kind.endswith('timing'):
            prefix = output / name
            driver.command(f'image {prefix}-before.ppm')
            driver.command(f'perfimages {prefix}')
            driver.run(frames=2, key='right')
            driver.run(frames=6)
            driver.command('perfimages -')
            field = (88, 48, 120, 56) if kind == 'none_timing' else (88, 32, 120, 40)
            with Image.open(str(prefix) + '-before.ppm') as image:
                pixels = image.crop(field).tobytes()
            for frame in (e for e in driver.events if e['event'] == 'perf_frame'):
                path = Path(f'{prefix}-{frame["display"]:03}.ppm')
                with Image.open(path) as image:
                    changed = image.crop(field).tobytes() != pixels
                if changed:
                    elapsed = frame['boundary_t'] - before['t']
                    result['first_visible'] = dict(ms=elapsed * 1000 / performance.HZ,
                                                  frames=elapsed / performance.T)
                    break
            if 'first_visible' not in result:
                raise RuntimeError('Type field did not visibly respond in eight display intervals')
        elif kind == 'rapid':
            for _ in range(36):
                driver.run(frames=1, key='a')
                driver.run(frames=1)
        elif kind == 'hold':
            driver.run(frames=120, key='right')
            driver.run(frames=2)
        elif kind == 'reverse':
            for _ in range(12):
                driver.run(frames=3, key='right')
                driver.run(frames=3, key='left')
        elif kind == 'fields':
            for _ in range(8):
                for key in ('down', 'right', 'up', 'left'):
                    driver.run(frames=2, key=key)
        elif kind == 'none_wrap':
            press(driver, 'down')
            driver.run(frames=120, key='left')
            driver.run(frames=120, key='right')
        elif kind == 'cancel':
            driver.run(frames=0.25, key='right')
            reach(driver, repo, 'PokedexSearch_Leave', KEY['b'])
        else:
            raise ValueError(kind)
        if kind != 'cancel':
            driver.run(frames=4)
        icons_audit(driver, repo)
        frames = [e for e in driver.events if e['event'] == 'search_icon_scanout']
        scanout_audit(config, frames)
        result['scanouts'] = len(frames)
        driver.command('perf 0')
        if kind == 'cancel':
            state = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600, key='b')
            if state['hit'] != 'listing':
                raise RuntimeError('B did not return from the updated Search field')
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
        driver.evidence(output / (name + '-error'))
    finally:
        driver.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--stress', action='store_true')
    parser.add_argument('--sparse', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build output')
    configs = prepare(args.source.resolve(), output)
    if args.stress:
        tasks = [(config, phase, kind, str(output)) for config in configs for phase in range(4)
                 for kind in ('rapid', 'hold', 'reverse', 'fields', 'none_wrap', 'cancel',
                              'icon_timing', 'none_timing')]
    elif args.sparse:
        tasks = [(dict(config, seen_count=count), one, two, str(output))
                 for config in configs for count in (0, 5, 50, len(config['names']))
                 for one, two in ((4, 0), (2, 10), (10, 2), (4, 4), (6, 16), (1, 0))]
    else:
        choices = ((2, 10), (10, 2), (4, 0), (4, 4)) if args.smoke else (
            (one, two) for one in range(1, 19) for two in range(19))
        choices = tuple(choices)
        tasks = [(config, one, two, str(output)) for config in configs for one, two in choices]
    with ProcessPoolExecutor(max_workers=min(args.jobs, 6)) as pool:
        rows = []
        for row in pool.map(run_stress if args.stress else run_pair, tasks):
            rows.append(row)
            if len(rows) % 100 == 0:
                print(json.dumps(dict(done=len(rows), total=len(tasks))), flush=True)
    summary = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows),
                   scanouts=sum(row.get('scanouts', 0) for row in rows), results=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    print(json.dumps([row for row in rows if row['issues']], indent=2))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
