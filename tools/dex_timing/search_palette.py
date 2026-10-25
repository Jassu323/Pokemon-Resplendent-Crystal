"""Read-only Search palette/layout comparison using normal isolated inputs."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from .assets import Repository, offset, decompress, read_symbols
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT, press
from .description_ui import settle
from .area_ui import reach
from .listing_options import configuration, choose, listing_audit, order_audit, LABELS
from .legacy_listing import private_battery
from . import performance
from .vanilla_performance import compile_core


def snapshot(driver, repo, output, name):
    driver.run(frames=2)
    state = driver.command('searchui')
    for label in ('wOBPals1', 'wOBPals2', 'wDexSearchSlowpokeFrame',
                  'hOAMUpdate', 'hCGBPalUpdate', 'wDexSearchMonType1',
                  'wDexSearchMonType2', 'wDexSearchResultCount'):
        if label in repo.symbols:
            bank, address = repo.symbols[label]
            size = 64 if 'Pals' in label else 2 if label.endswith('Count') and 'PokedexSelectedMon_Update' in repo.symbols else 1
            state[label] = driver.command(f'perfram {bank} {address} {size}')['bytes']
    actual = bytes.fromhex(driver.command('inspectvram 0 32768 880')['bytes'])
    expected = decompress(repo.rom, offset(repo.symbols['PokedexSlowpokeLZ']), 880).output
    state['slowpoke_graphics_match'] = actual == expected
    state['graphics_mismatches'] = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
    driver.command(f'image {output}/{name}.ppm')
    with Image.open(output / (name + '.ppm')) as image:
        image.save(output / (name + '.png'))
        image.resize((640, 576), Image.Resampling.NEAREST).save(output / (name + '-4x.png'))
    (output / (name + '.json')).write_text(json.dumps(state, indent=2) + '\n')
    return state


def prototype(source, output, presentation, mode, warmed, index=0, production=False, last=False, measure=False, types=None):
    if measure and types is not None:
        raise ValueError('Measure entry separately from the type-selection sequence')
    config = configuration(source, presentation)
    if production:
        if measure:
            raise ValueError('Entry measurements use the current popup A-input path')
        config.update(rom=str(ROOT / 'pokecrystal.gbc'), sym=str(ROOT / 'pokecrystal.sym'))
        private = output / 'private.sav'
        if 'wLastDexPresentation' in read_symbols(Path(config['sym'])):
            private_battery(config, private, presentation=int(presentation == 'legacy'), order_mode=mode)
        else:
            from .info_ui import fixture
            if presentation != 'modern' or mode:
                raise ValueError('Historical production binary has only Modern mode')
            fixture(Path(config['battery']), private)
        config['battery'] = str(private)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    config['core'] = str(performance.core(repo, output / 'core', {
        'search_init': ('Pokedex_InitSearchScreen', True),
        'search_layout': ('_CGB_PokedexSearchOption', True),
        'search_update': ('Pokedex_UpdateSearchScreen', False),
        'search_animation': ('AnimateDexSearchSlowpoke', True),
        'search_pose': ('DoDexSearchSlowpokeFrame', True),
        'usual_pals': ('Pokedex_ApplyUsualPals', True),
    }))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'run.log')
    records = {}
    try:
        if production:
            bootstrap(driver, expected_mode=mode)
        else:
            driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        if mode and not production:
            choose(driver, mode)
        driver.run(frames=120 if warmed else 2)
        records['listing'] = snapshot(driver, repo, output, 'listing')
        press(driver, 'start')
        if not production:
            press(driver, 'down')
        before = driver.command('perf 1') if measure else None
        if measure:
            driver.events.clear()
            driver.command(f'perfimages {output}/search-enter')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['a'] if not production else 0)
        if types is not None:
            from .search_qualification import choose_types
            choose_types(driver, repo, *types)
            press(driver, 'up')
        records['search-first'] = snapshot(driver, repo, output, 'search-first')
        if measure:
            driver.command('perfimages -')
            driver.command('perf 0')
            frames = [event for event in driver.events if event['event'] == 'perf_frame']
            first = next(event for event in frames if event['full'] != before['full'])
            complete = next(event for event in frames if event['full'] == frames[-1]['full'])
            (output / 'entry-timing.json').write_text(json.dumps(dict(
                first_ms=(first['boundary_t'] - before['t']) / performance.HZ * 1000,
                first_frames=(first['boundary_t'] - before['t']) / performance.T,
                complete_ms=(complete['boundary_t'] - before['t']) / performance.HZ * 1000,
                complete_frames=(complete['boundary_t'] - before['t']) / performance.T,
                events=driver.events), indent=2) + '\n')
        press(driver, 'down')
        press(driver, 'down')
        reach(driver, repo, 'AnimateDexSearchSlowpoke', KEY['a'])
        for frame in range(5):
            reach(driver, repo, 'DoDexSearchSlowpokeFrame')
            records[f'animation-{frame}'] = snapshot(driver, repo, output, f'animation-{frame}')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
        records['results'] = snapshot(driver, repo, output, 'results')
        if last:
            count = int.from_bytes(bytes.fromhex(records['results']['wDexSearchResultCount']), 'little')
            for _ in range(count - 1):
                press(driver, 'down')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            records['results-last'] = snapshot(driver, repo, output, 'results-last')
            records['results-last']['listing'] = driver.command('peek')
            records['results-last']['ui'] = driver.command('ui')
        reach(driver, repo, 'PokedexSelectedMon_Update', KEY['a'])
        driver.run(frames=2)
        settle(driver)
        driver.run(('leave',), key='b')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
        records['results-from-selected'] = snapshot(driver, repo, output, 'results-from-selected')
        press(driver, 'b')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen')
        records['search-from-results'] = snapshot(driver, repo, output, 'search-from-results')
        press(driver, 'b')
        driver.run(('listing',), frames=600)
        driver.run(frames=4)
        if not production:
            manifest = json.loads((source / 'sort-manifest.json').read_text())
            listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[mode]]))
        records['listing-return'] = snapshot(driver, repo, output, 'listing-return')
    finally:
        driver.close()
    (output / 'captures.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def vanilla(source, battery, output):
    repo = SimpleNamespace(rom=(source / 'pokecrystal.gbc').read_bytes(),
                           symbols=read_symbols(source / 'pokecrystal.sym'))
    driver = Driver(compile_core(source, output), source / 'pokecrystal.gbc', BOOT,
                    battery, output / 'run.log')
    records = {}
    try:
        bootstrap(driver)
        driver.command('rawcolor')
        records['listing'] = snapshot(driver, repo, output, 'listing')
        press(driver, 'start')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen')
        records['search-first'] = snapshot(driver, repo, output, 'search-first')
        press(driver, 'down')
        press(driver, 'down')
        reach(driver, repo, 'AnimateDexSearchSlowpoke', KEY['a'])
        for frame in range(5):
            reach(driver, repo, 'DoDexSearchSlowpokeFrame')
            records[f'animation-{frame}'] = snapshot(driver, repo, output, f'animation-{frame}')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
        records['results'] = snapshot(driver, repo, output, 'results')
        press(driver, 'b')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen')
        records['search-from-results'] = snapshot(driver, repo, output, 'search-from-results')
    finally:
        driver.close()
    (output / 'captures.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--presentation', choices=('modern', 'legacy'), default='modern')
    parser.add_argument('--mode', type=int, default=0)
    parser.add_argument('--warmed', action='store_true')
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--last', action='store_true')
    parser.add_argument('--measure', action='store_true')
    parser.add_argument('--types', type=int, nargs=2)
    parser.add_argument('--vanilla-battery', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use an isolated build output')
    output.mkdir(parents=True, exist_ok=True)
    if args.vanilla_battery:
        records = vanilla(args.source.resolve(), args.vanilla_battery.resolve(), output)
    else:
        records = prototype(args.source.resolve(), output, args.presentation, args.mode, args.warmed,
                            production=args.production, last=args.last, measure=args.measure, types=args.types)
    print(json.dumps({name: dict(obj0=row['obj_palettes'][:16],
                               graphics_match=row['slowpoke_graphics_match'],
                               oam_hold=row.get('hOAMUpdate')) for name, row in records.items()}, indent=2))


if __name__ == '__main__':
    main()
