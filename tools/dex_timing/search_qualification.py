"""Search ownership/content checks with private saves and normal button inputs."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re

from .assets import Repository, offset, decompress
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT, press, ready
from .description_ui import settle
from .area_ui import reach
from .listing_options import configuration, choose, order_audit, listing_audit, LABELS
from .legacy_listing import open_mode_screen, private_battery
from pokedex_info_assets import species
from .search_results_patch import ALPHABETICAL_TYPES


def ram(driver, repo, name, size=1):
    bank, address = repo.symbols[name]
    return bytes.fromhex(driver.command(f'perfram {bank} {address} {size}')['bytes'])


def slowpoke_audit(driver, repo):
    driver.run(frames=2)
    ui = driver.command('searchui')
    if ram(driver, repo, 'hOAMUpdate') != b'\0':
        raise RuntimeError('Search sprite DMA is still suspended')
    palette = repo.rom[offset(repo.symbols['PartyMenuOBPals']):][:8]
    expected = b''.join(palette[i * 2:i * 2 + 2] for i in (0, 0, 2, 3))
    if bytes.fromhex(ui['obj_palettes'])[:8] != expected:
        raise RuntimeError('Slowpoke does not own its established OBJ0 palette')
    expected = bytearray(repo.rom[offset(repo.symbols['DoDexSearchSlowpokeFrame.SlowpokeSpriteData']):][:36])
    pose = ram(driver, repo, 'wDexSearchSlowpokeFrame')[0]
    for index in range(2, 36, 4):
        expected[index] += pose * 3
    if bytes.fromhex(ui['oam'])[:36] != expected:
        raise RuntimeError('Slowpoke hardware OAM does not show the requested pose')
    actual = bytes.fromhex(driver.command('inspectvram 0 32768 880')['bytes'])
    if actual != decompress(repo.rom, offset(repo.symbols['PokedexSlowpokeLZ']), 880).output:
        raise RuntimeError('Slowpoke resident graphics were overwritten')
    if 'PokedexSearch_Filter' in repo.symbols:
        icons_audit(driver, repo, ui)
    return pose


def icons_audit(driver, repo, ui=None):
    ui = ui or driver.command('searchui')
    if 'Pokedex_DrawSearchScreenBG.Header' in repo.symbols:
        bg, attrs = (bytes.fromhex(ui[key]) for key in ('map', 'attrs'))
        title = bytes((0x3b, 0x7f, 0x92, 0xa4, 0xa0, 0xb1, 0xa2, 0xa7, 0x7f, 0x3c))
        if bg[:20] != b'\x31' * 20 or bg[32:52] != title + b'\x31' * 10:
            raise RuntimeError('Search header retains dark fill outside its rounded title')
        if attrs[:20] != bytes(20) or attrs[32:52] != bytes(20):
            raise RuntimeError('Search header does not use the standard UI palette')
    hardware = bytes.fromhex(ui['oam'])
    palettes = bytes.fromhex(ui['obj_palettes'])
    conversion = offset(repo.symbols['PokedexTypeSearchConversionTable'])
    gfx = offset(repo.symbols['CompactTypeIconGFXPointers'])
    pals = offset(repo.symbols['TypeIconPalettePointers'])
    buffer = hardware[38] - 0x28
    if buffer not in (0, 8):
        raise RuntimeError('Search type icon buffer is outside the reserved OBJ tiles')
    for field, label in enumerate(('wDexSearchMonType1', 'wDexSearchMonType2')):
        selected = ram(driver, repo, label)[0]
        sprites = hardware[36 + field * 16:52 + field * 16]
        if not selected:
            if any(sprites):
                raise RuntimeError('None still has a visible Search type icon')
            continue
        actual_type = repo.rom[conversion + selected - 1]
        at = gfx + actual_type * 3
        bank, address = repo.rom[at], int.from_bytes(repo.rom[at + 1:at + 3], 'little')
        expected = bytearray(repo.rom[offset((bank, address)):][:64])
        for i in (0, 14):
            expected[i] |= 128
        for i in (48, 62):
            expected[i] |= 1
        for i in range(0, 64, 2):
            expected[i] = ~(expected[i] ^ expected[i + 1]) & 255
        tile = 0x28 + buffer + field * 4
        if bytes.fromhex(driver.command(f'inspectvram 1 {0x8000 + tile * 16} 64')['bytes']) != expected:
            raise RuntimeError('Search icon differs from the existing compact artwork')
        expected_oam = bytes(value for i in range(4)
                             for value in (48 + field * 16, 96 + i * 8, tile + i, 9 + field))
        if sprites != expected_oam:
            raise RuntimeError('Search icon OAM position/ownership is incorrect')
        address = int.from_bytes(repo.rom[pals + actual_type * 2:pals + actual_type * 2 + 2], 'little')
        expected_palette = bytearray(repo.rom[offset((repo.symbols['TypeIconPalettes'][0], address)):][:8])
        expected_palette[2:4] = expected_palette[:2]
        if palettes[8 + field * 8:16 + field * 8] != expected_palette:
            raise RuntimeError('Search icon palette is not committed with its tiles')
    peak = max(sum(0 < hardware[i] <= y + 16 < hardware[i] + 8
                   for i in range(0, 160, 4)) for y in range(144))
    if peak > 4 or sum(bool(hardware[i]) for i in range(0, 160, 4)) > 17:
        raise RuntimeError('Search OAM exceeds the planned total/scanline budget')


@lru_cache(maxsize=1)
def source_types():
    table = re.findall(r'^\s*db (\w+)\s*$', (ROOT / 'data/types/search_types.asm').read_text(), re.M)
    ids = {name: i + 1 for i, name in enumerate(species())}
    types = {}
    for name in ids:
        basename = {'UNOWN': 'unown', 'PORYGON_Z': 'porygonz'}.get(name, name.lower())
        text = (ROOT / f'data/pokemon/base_stats/{basename}.asm').read_text()
        match = re.search(r'^\s*db\s+(\w+)\s*,\s*(\w+)\s*; type', text, re.M)
        if match is None:
            raise ValueError(f'Type oracle has no source pair for {name}')
        types[name] = match.groups()
    return table, ids, types


def selector_types(repo):
    return ALPHABETICAL_TYPES if 'PokedexResults_Initialize' in repo.symbols else source_types()[0]


def choose_types(driver, repo, one, two):
    current = ram(driver, repo, 'wDexSearchMonType1')[0]
    for _ in range((one - current) % 18):
        press(driver, 'right')
    press(driver, 'down')
    current = ram(driver, repo, 'wDexSearchMonType2')[0]
    for _ in range((two - current) % 19):
        press(driver, 'right')


def named_types(repo, one, two=None):
    table = selector_types(repo)
    return table.index(one) + 1, table.index(two) + 1 if two else 0


def expected_results(order, selected, unseen, ranked=False, table=None):
    original, ids, types = source_types()
    table = table or original
    required = [table[value - 1] for value in selected if value]
    groups = ([], [], [])
    for name in order:
        if ids[name] in unseen:
            continue
        one = required[0] in types[name]
        two = len(required) > 1 and required[1] in types[name]
        if len(required) == 1:
            group = 0 if one else None
        elif one and two:
            group = 0
        elif ranked and one:
            group = 1
        elif ranked and two:
            group = 2
        else:
            group = None
        if group is not None:
            groups[group].append(ids[name])
    return [value for group in groups for value in group]


def results_audit(driver, repo, expected):
    driver.run(frames=2)
    count = int.from_bytes(ram(driver, repo, 'wDexSearchResultCount', 2), 'little')
    actual = ram(driver, repo, 'wPokedexOrder', len(expected) * 2)
    if count != len(expected) or actual != b''.join(value.to_bytes(2, 'little') for value in expected):
        raise RuntimeError('Filtered species differ from the independent source-type oracle')
    ui = driver.command('ui')
    window, attrs = (bytes.fromhex(ui[key]) for key in ('window', 'window_attrs'))
    if window[5] != 0x7e or window[10 * 20 + 5] != 0x7e or attrs[10 * 20 + 5] != 0x40:
        raise RuntimeError('Results one-tile up/down marker is not resident and correctly flipped')
    hardware_state = driver.command('searchui')
    hardware = bytes.fromhex(hardware_state['oam'])
    if 'PokedexResults_Initialize' in repo.symbols:
        from .search_results import visual_audit
        visual_audit(driver, repo, expected)
    elif not all(hardware[index] and hardware[index + 3] & 7 == 7 for index in range(0, 16, 4)):
        raise RuntimeError('Results hardware selection outline is missing')
    if 'PokedexResults_Initialize' not in repo.symbols and bytes.fromhex(hardware_state['obj_palettes'])[62:64] != repo.rom[offset(repo.symbols['PokedexListDarkGray']):][:2]:
        raise RuntimeError('Results cursor still has opaque black panel cutouts')
    # The split suffix must retain the mixed-case style across the BG/Window seam.
    if window[12 * 20:12 * 20 + 6] != bytes((0xa4, 0xb2, 0xb4, 0xab, 0xb3, 0xb2)):
        raise RuntimeError('Search Results suffix has a capitalization seam')
    if window[16 * 20:16 * 20 + 2] != bytes((0xa3, 0xe7)):
        raise RuntimeError('Found suffix has a capitalization seam')


def run_case(task):
    config, index, mode, phase, kind, target = task
    output = Path(target)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    name = f'{index}-{mode}-{phase}-{kind}'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (name + '.log'))
    issues, poses = [], []
    manifest = json.loads((Path(config['rom']).parent / 'sort-manifest.json').read_text())
    try:
        unseen = ()
        if kind in ('none', 'default_empty') and 'PokedexSearch_Filter' in repo.symbols:
            driver.close()
            battery = output / (name + '.sav')
            private_battery(config, battery, presentation=int(config['listing_style'] == 'legacy'),
                            order_mode=0, unseen=tuple(range(5, len(species()))))
            unseen = set(manifest['orders'][LABELS[0]][5:])
            unseen = tuple(i + 1 for i, value in enumerate(species()) if value in unseen)
            driver = Driver(config['core'], config['rom'], BOOT, battery, output / (name + '.log'))
            bootstrap(driver)
        else:
            driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        if mode:
            choose(driver, mode)
        original = driver.command('peek')
        driver.command('audit 1')
        driver.run(frames=2 + phase / 8)
        if kind == 'selected':
            driver.run(('accept',), key='a')
            settle(driver)
            press(driver, 'right')
            press(driver, 'a')
            ready(driver, 0)
            driver.run(('leave',), key='b')
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(frames=2)
        elif kind == 'modes':
            open_mode_screen(driver)
            press(driver, 'b')
            driver.run(('listing',), frames=600)
            driver.run(frames=2)
        press(driver, 'start')
        press(driver, 'down')
        press(driver, 'a')
        reach(driver, repo, 'Pokedex_UpdateSearchScreen')
        poses.append(slowpoke_audit(driver, repo))
        if 'Pokedex_DrawSearchScreenBG.Header' in repo.symbols:
            initial_types = tuple(ram(driver, repo, label)[0]
                                  for label in ('wDexSearchMonType1', 'wDexSearchMonType2'))
            if initial_types != (1, 0):
                raise RuntimeError('Search did not initialize to Bug/None')
        if kind == 'controls':
            initial = ram(driver, repo, 'wDexSearchMonType1')
            for _ in range(18):
                press(driver, 'a')
                slowpoke_audit(driver, repo)
            if ram(driver, repo, 'wDexSearchMonType1') != initial:
                raise RuntimeError('Type1 did not wrap through all 18 choices')
            press(driver, 'down')
            for _ in range(19):
                press(driver, 'right')
                slowpoke_audit(driver, repo)
            if ram(driver, repo, 'wDexSearchMonType2') != b'\0':
                raise RuntimeError('Type2 did not wrap through 18 choices and None')
            press(driver, 'left')
            press(driver, 'right')
            press(driver, 'up')
        elif kind == 'none' and 'PokedexSearch_Filter' in repo.symbols:
            choose_types(driver, repo, *named_types(repo, 'ICE', 'DARK'))
            press(driver, 'up')
        elif kind in ('dual', 'none'):
            choose_types(driver, repo, *named_types(repo, 'FIRE', 'FLYING' if kind == 'dual' else 'NORMAL'))
            press(driver, 'up')
        selected = tuple(ram(driver, repo, label)[0] for label in ('wDexSearchMonType1', 'wDexSearchMonType2'))
        expected = expected_results(manifest['orders'][LABELS[mode]], selected, unseen,
                                    ranked='PokedexSearch_Filter' in repo.symbols, table=selector_types(repo))
        press(driver, 'down')
        press(driver, 'down')
        driver.command('perf 1')
        reach(driver, repo, 'AnimateDexSearchSlowpoke', KEY['a'])
        for _ in range(25):
            reach(driver, repo, 'DoDexSearchSlowpokeFrame')
            poses.append(slowpoke_audit(driver, repo))
        if expected:
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            results_audit(driver, repo, expected)
            press(driver, 'down')
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            driver.run(frames=2)
            if len(expected) > 1 and driver.command('peek')['index'] != 1:
                raise RuntimeError('Results D-pad failed to move one row')
            if kind in ('selected', 'modes'):
                reach(driver, repo, 'PokedexSelectedMon_Update', KEY['a'])
                driver.run(frames=2)
                settle(driver)
                press(driver, 'right')
                press(driver, 'a')
                ready(driver, 0)
                press(driver, 'a')
                ready(driver, None)
                driver.run(('leave',), key='b')
                reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
                results_audit(driver, repo, expected)
            reach(driver, repo, 'Pokedex_UpdateSearchScreen', KEY['b'])
            driver.run(frames=2)
            slowpoke_audit(driver, repo)
        else:
            # The native no-match dialog remains an input-driven path.
            reach(driver, repo, 'Pokedex_DisplayTypeNotFoundMessage')
            driver.run(frames=120, key='a')
            driver.run(frames=4)
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            slowpoke_audit(driver, repo)
        driver.command('perf 0')
        press(driver, 'b')
        driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(frames=4)
        current = driver.command('peek')
        if (current['index'], current['mode'], current['presentation']) != (
                original['index'], original['mode'], original['presentation']):
            raise RuntimeError('Search roundtrip changed the Listing selection or owner')
        listing_audit(driver, repo, order_audit(driver, repo, manifest['orders'][LABELS[mode]], unseen), unseen)
        if any(event['event'] in ('animation_miss', 'audio_miss') for event in driver.events):
            raise RuntimeError('Playback underrun during a Search/Selected roundtrip')
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / (name + '-error'))
    finally:
        driver.close()
    return dict(index=index, mode=mode, phase=phase, kind=kind,
                presentation=config['listing_style'], poses=poses, issues=issues)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--returns', action='store_true')
    parser.add_argument('--defaults', action='store_true')
    args = parser.parse_args()
    output = args.source.resolve()
    target = output / ('search-default-empty' if args.defaults else
                       'search-listing-returns' if args.returns else 'search-qualification')
    target.mkdir(exist_ok=True)
    tasks = []
    for style in ('modern', 'legacy'):
        config = configuration(output, style)
        local = target / style
        local.mkdir(exist_ok=True)
        if args.defaults:
            tasks += [(config, 0, mode, phase, 'default_empty', str(local))
                      for mode in range(3) for phase in range(4)]
        elif args.returns:
            tasks += [(config, index, 0, index % 4, kind, str(local))
                      for index in (8, 9, 254, 255, 256, 372) for kind in ('plain', 'dual', 'selected')]
        else:
            tasks += [(config, 0, mode, phase, kind, str(local)) for mode in (range(1) if args.smoke else range(3))
                      for phase in (range(1) if args.smoke else range(4))
                      for kind in ('plain', 'controls', 'dual', 'none', 'selected', 'modes')]
    with ProcessPoolExecutor(max_workers=min(args.jobs, 6)) as pool:
        results = list(pool.map(run_case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(row['issues']) for row in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'results'}))
    print(json.dumps([row for row in results if row['issues']], indent=2))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
