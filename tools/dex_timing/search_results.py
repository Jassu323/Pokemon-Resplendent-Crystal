"""Native Results portrait/OAM coherency and normal-input scrolling latency."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path

from . import performance
from .area_ui import reach
from .assets import Repository, offset
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT, press
from .listing_options import configuration, LABELS
from .search_qualification import ram, choose_types, expected_results, selector_types
from .search_ranked import prepare, icon_data
from .legacy_listing import private_battery
from pokedex_info_assets import species


@lru_cache(maxsize=1024)
def portrait(rom, sym, permanent):
    repo = Repository(ROOT, Path(rom), Path(sym))
    name = species()[permanent - 1]
    name = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(name, name.lower())
    asset = repo.load([name])[0]
    base = [bytes(16) for _ in range(49)]
    for x in range(asset.width):
        for y in range(asset.width):
            at = x * asset.width + y
            base[(x + int(asset.width != 7)) * 7 + y + 7 - asset.width] = asset.dictionary[at * 16:(at + 1) * 16]
    at = offset(repo.symbols['PokemonPalettes']) + permanent * 8
    palette = b'\xff\x7f' + repo.rom[at:at + 4] + b'\0\0'
    at = offset(repo.symbols['PokemonNames']) + (permanent - 1) * 10
    return b''.join(base), palette, repo.rom[at:at + 10].split(b'\x50')[0]


def frame_audit(repo, frame):
    actual = bytes.fromhex(frame['name'])
    table = offset(repo.symbols['PokemonNames'])
    matches = [value for value in range(1, len(species()) + 1)
               if repo.rom[table + (value - 1) * 10:table + value * 10].split(b'\x50')[0].ljust(10, b'\x7f') == actual]
    if len(matches) != 1:
        raise RuntimeError('Results visible cursor does not identify one intact species name')
    picture, palette, name = portrait(str(repo.rom_path), str(repo.rom_path.with_suffix('.sym')), matches[0])
    if bytes.fromhex(frame['portrait']) != picture:
        raise RuntimeError('Results portrait differs from the selected species base-only graphics')
    if bytes.fromhex(frame['bgpal']) != palette:
        raise RuntimeError('Results portrait colors do not match the selected species')
    if not bytes.fromhex(frame['name']).startswith(name):
        raise RuntimeError('Results name and portrait are different species on a visible scanout')


def visual_audit(driver, repo, expected):
    state = driver.command('peek')
    permanent = expected[state['index']]
    hardware = driver.command('searchui')
    oam = bytes.fromhex(hardware['oam'])
    palettes = bytes.fromhex(hardware['obj_palettes'])
    bg, attrs = (bytes.fromhex(hardware[key]) for key in ('map', 'attrs'))
    for line in (9, 10):
        if bg[line * 32:line * 32 + 8] != b'\x31' * 8:
            raise RuntimeError('Results gap still uses the dark panel fill')
    for line in (8, 9, 10):
        if attrs[line * 32:line * 32 + 9] != bytes(9):
            raise RuntimeError('Portrait bottom/listing corner overrides the dark UI border palette')
    for line, tile in ((8, 0x53), (9, 0x69), (10, 0x6a)):
        if bg[line * 32 + 8] != tile:
            raise RuntimeError('Results listing lower-left border tile is missing')
    at = offset(repo.symbols['PokedexUIPalette'])
    if bytes.fromhex(hardware['bg_palettes'])[:8] != repo.rom[at:at + 8]:
        raise RuntimeError('Results border/UI hardware palette does not retain its dark pixels')
    y = 24 + state['cursor'] * 16
    corners = bytes(v for row, x, flags in ((y, 72, 0), (y, 151, 32),
                                            (y + 15, 72, 64), (y + 15, 151, 96))
                    for v in (row, x, 0x40, flags))
    if oam[:16] != corners:
        raise RuntimeError('Results does not use the small four-corner cursor')
    for tile, label in ((0x40, 'PokedexListCursorGFX'), (0x41, 'PokedexCaughtBallGFX')):
        actual = bytes.fromhex(driver.command(f'inspectvram 0 {0x8000 + tile * 16} 16')['bytes'])
        at = offset(repo.symbols[label])
        if actual != repo.rom[at:at + 16]:
            raise RuntimeError('Results cursor/caught-ball resident artwork was overwritten')
    for index, label in enumerate(('PokedexListCursorPalette', 'PokedexListCaughtBallPalette')):
        at = offset(repo.symbols[label])
        if palettes[index * 8:index * 8 + 8] != repo.rom[at:at + 8]:
            raise RuntimeError('Results cursor/caught ball has the wrong palette')
    caught = ram(driver, repo, 'wPokedexCaught', (len(species()) + 7) // 8)
    for row in range(4):
        index = state['scroll'] + row
        sprite = oam[16 + row * 4:20 + row * 4]
        ball = b'\0' * 4
        if index < len(expected):
            value = expected[index] - 1
            if caught[value // 8] & 1 << (value % 8):
                ball = bytes((32 + row * 16, 71, 0x41, 1))
        if sprite != ball:
            raise RuntimeError('Results caught ball does not match its row/caught flag')
    one, two = (ram(driver, repo, label)[0] for label in ('wDexSearchMonType1', 'wDexSearchMonType2'))
    for field, value in enumerate((one, two if two != one else 0)):
        sprites = oam[32 + field * 16:48 + field * 16]
        if not value:
            if any(sprites):
                raise RuntimeError('Results retains a badge for None or a duplicate type')
            continue
        gfx, pal = icon_data(str(repo.rom_path), str(repo.rom_path.with_suffix('.sym')), value)
        tile = 0x28 + field * 4
        if sprites != bytes(v for i in range(4) for v in (128 + field * 8, 88 + i * 8, tile + i, 10 + field)):
            raise RuntimeError('Results type badge OAM placement is incorrect')
        actual = bytes.fromhex(driver.command(f'inspectvram 1 {0x8000 + tile * 16} 64')['bytes'])
        if actual != gfx or palettes[16 + field * 8:24 + field * 8] != pal:
            raise RuntimeError('Results badge tiles/palettes differ from the selected types')
    peak = max(sum(0 < oam[i] <= line + 16 < oam[i] + 8 for i in range(0, 160, 4)) for line in range(144))
    if peak > 4 or sum(bool(oam[i]) for i in range(0, 160, 4)) > 16:
        raise RuntimeError('Results exceeds its OAM scanline/total budget')
    frame_audit(repo, dict(permanent=permanent, portrait=driver.command('inspectvram 0 36864 784')['bytes'],
                           bgpal=hardware['bg_palettes'][16:32],
                           name=driver.command('ui')['window'][(2 + state['cursor'] * 2) * 40 + 2:][:20]))


def run_case(task):
    config, one, two, target = task
    output = Path(target)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    name = f'{config["listing_style"]}-{config["order"]}-{one}-{two}'
    if config.get('flags'):
        name += '-' + config['flags']
        battery = output / (name + '.sav')
        private_battery(config, battery, presentation=int(config['listing_style'] == 'legacy'),
                        order_mode=LABELS.index(config['order']),
                        uncaught=tuple(range(0, len(species()), 2 if config['flags'] == 'mixed' else 1)))
        config = dict(config, battery=str(battery))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    row = dict(presentation=config['listing_style'], order=config['order'], types=[one, two], issues=[])
    try:
        if config.get('flags'):
            bootstrap(driver, expected_mode=LABELS.index(config['order']))
            press(driver, 'start')
            press(driver, 'down')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['a'])
        else:
            driver.command(f'load {config["checkpoint"]}')
        choose_types(driver, repo, one, two)
        press(driver, 'down')
        reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen', KEY['a'])
        driver.run(frames=2)
        manifest = json.loads((Path(config['rom']).parent / 'sort-manifest.json').read_text())
        expected = expected_results(manifest['orders'][config['order']], (one, two), (), True, selector_types(repo))
        visual_audit(driver, repo, expected)
        driver.events.clear()
        driver.command('perf 1')
        visited = [expected[0]]
        for _ in range(min(len(expected) - 1, 4) if config.get('badges_only') else len(expected) - 1):
            press(driver, 'down')
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            visual_audit(driver, repo, expected)
            visited.append(expected[driver.command('peek')['index']])
        if visited != expected[:len(visited)]:
            raise RuntimeError('Held/individual Results scrolling skipped or duplicated a species')
        if not config.get('badges_only'):
            driver.run(frames=60, key='down')
            if driver.command('peek')['index'] != len(expected) - 1:
                raise RuntimeError('Results scrolled past its bounded bottom')
        driver.run(frames=80, key='up')
        driver.run(frames=4)
        visual_audit(driver, repo, expected)
        driver.command('perf 0')
        frames = [event for event in driver.events if event['event'] == 'results_scanout']
        for frame in frames:
            frame_audit(repo, frame)
        uploads = [event for event in driver.events if event['event'] == 'results_dma_start']
        if not uploads or any(not 64 <= event['ly'] < 79 for event in uploads):
            raise RuntimeError('Portrait upload began inside its visible scan or missed the safe HDMA interval')
        row.update(visited=visited, scanouts=len(frames), peak_sprites=16,
                   uploads=len(uploads), upload_min_ly=min(event['ly'] for event in uploads),
                   upload_max_ly=max(event['ly'] for event in uploads))
    except (RuntimeError, ValueError) as error:
        row['issues'].append(str(error))
        driver.evidence(output / (name + '-error'))
    finally:
        driver.close()
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--badges', action='store_true')
    parser.add_argument('--flags', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    configs = prepare(args.source.resolve(), output)
    repo = Repository(ROOT, Path(configs[0]['rom']), Path(configs[0]['sym']))
    dma_bank, dma_pc = repo.symbols['_continue_HDMATransfer.rstat_loop_2']
    at = offset((dma_bank, dma_pc))
    dma_pc += repo.rom[at:at + 32].index(b'\xe0\x55')
    core = performance.core(repo, output / 'results-core',
                            extra_flags=('-DDEX_SEARCH_RESULTS_TRACE',
                                         f'-DRESULTS_DMA_BANK={dma_bank}', f'-DRESULTS_DMA_PC={dma_pc}',
                                         f'-DRESULTS_ORDER_OFFSET={repo.symbols["wPokedexOrder"][1] & 4095}'))
    for config in configs:
        config['core'] = str(core)
    if args.flags:
        tasks = [(dict(config, badges_only=True, flags=flags), one, two, str(output))
                 for config in configs for flags in ('mixed', 'uncaught')
                 for one, two in ((13, 0), (18, 12), (7, 8))]
    elif args.badges:
        tasks = [(dict(config, badges_only=True), 13, two, str(output))
                 for config in configs for two in range(19)]
    else:
        tasks = [(config, one, 0, str(output)) for config in configs
                 for one in (range(1, 19) if not args.smoke else (13,))]
    with ProcessPoolExecutor(max_workers=min(args.jobs, 6)) as pool:
        rows = list(pool.map(run_case, tasks))
    summary = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows),
                   unique_species=len(set(value for row in rows for value in row.get('visited', ()))),
                   scroll_checks=sum(len(row.get('visited', ())) for row in rows),
                   scanouts=sum(row.get('scanouts', 0) for row in rows), results=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'results'}))
    for row in rows:
        if row['issues']:
            print(json.dumps(row))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
