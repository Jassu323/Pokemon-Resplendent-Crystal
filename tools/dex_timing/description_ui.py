"""Read-only Description UI audit through the normal-input SameBoy runner.

Requires current-build cold-listing checkpoints. Captures native-resolution
screenshots, both description pages, and the next internally paged species.
No game memory, save flags, or ROM instructions are patched.
"""
import argparse
import json
from pathlib import Path
import re

from .assets import Repository, offset
from .cold_listing import Driver, ROOT, move, predecessor


def linked(repo, label, size):
    start = offset(repo.symbols[label])
    return repo.rom[start:start + size]


def expected_types(repo, name):
    values, value = {}, 0
    for line in (repo.root / 'constants/type_constants.asm').read_text().splitlines():
        if match := re.match(r'\s*const_next\s+(\d+)', line):
            value = int(match[1])
        elif match := re.match(r'\s*const\s+(\w+)', line):
            values[match[1]] = value
            value += 1
    stem = 'unown' if name == 'unown_a' else name
    source = (repo.root / f'data/pokemon/base_stats/{stem}.asm').read_text()
    match = re.search(r'db\s+(\w+)\s*,\s*(\w+)\s*;\s*type', source)
    if not match:
        raise ValueError(f'Missing base-stat types for {name}')
    return [values[match[1]], values[match[2]]]


def audit(repo, ui):
    tilemap, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    types = ui['types']
    palettes = bytes.fromhex(ui['palettes'])
    issues = []
    shell = linked(repo, 'PokedexDescriptionTilemap', 360)
    edge = linked(repo, 'PokedexDescriptionRightEdge', 18)
    for y in range(18):
        for x in range(21):
            fixed = y in (0, 8, 16) or x in (0, 20) or (x == 8 and 1 <= y <= 7)
            expected = edge[y] if x == 20 else shell[y * 20 + x]
            if y == 8 and x == 2 and ui['page']:
                expected = 0x79
            if fixed and (tilemap[y * 21 + x] != expected or attrs[y * 21 + x]):
                issues.append(f'shell_{x}_{y}')
    if bytes.fromhex(ui['border_gfx']) != linked(repo, 'PokedexDescriptionGFX', 160):
        issues.append('border_graphics')
    for slot, type_id in enumerate(types if types[0] != types[1] else types[:1]):
        if not 0 <= type_id < 29:
            issues.append('invalid_type')
            continue
        ptr = linked(repo, 'CompactTypeIconGFXPointers', 29 * 3)[type_id * 3:type_id * 3 + 3]
        start = offset((ptr[0], int.from_bytes(ptr[1:], 'little')))
        expected_gfx = bytearray(repo.rom[start:start + 64])
        for address, mask in ((0, 128), (14, 128), (48, 1), (62, 1)):
            expected_gfx[address] |= mask
        if bytes.fromhex(ui['type_gfx'])[slot * 64:(slot + 1) * 64] != expected_gfx:
            issues.append(f'type_graphics_{slot}')
        x = 9 + 5 * slot
        cells = slice(7 * 21 + x, 7 * 21 + x + 4)
        if tilemap[cells] != bytes(range(0x64 + 4 * slot, 0x68 + 4 * slot)):
            issues.append(f'type_tiles_{slot}')
        if attrs[cells] != bytes([14 + slot] * 4):
            issues.append(f'type_attrs_{slot}')
        pointers = linked(repo, 'TypeIconPalettePointers', 29 * 2)
        address = int.from_bytes(pointers[2 * type_id:2 * type_id + 2], 'little')
        start = offset((repo.symbols['TypeIconPalettes'][0], address))
        palette = bytearray(repo.rom[start:start + 8])
        palette[2:4] = bytes((0xa5, 0x14))
        if palettes[(6 + slot) * 8:(7 + slot) * 8] != palette:
            issues.append(f'type_palette_{slot}')
    if types[0] == types[1]:
        cells = slice(7 * 21 + 14, 7 * 21 + 18)
        if tilemap[cells] != bytes([0x32] * 4) or any(attrs[cells]):
            issues.append('stale_second_type')
    if palettes[16:24] != bytes((255, 127, 0, 0, 0, 0, 165, 20)):
        issues.append('footprint_palette')
    if any(attrs[y * 21 + x] != 10 for y in (1, 2) for x in (18, 19)):
        issues.append('footprint_attrs')
    page_tiles = bytes((0x77, 0x7a if ui['page'] else 0x78))
    if tilemap[9 * 21 + 1:9 * 21 + 3] != page_tiles:
        issues.append('page_badge')
    return issues


def settle(driver):
    for _ in range(2400):
        state = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=120)
        if state['hit'] != 'selected':
            raise RuntimeError(f'Playback did not settle safely: {state}')
        if state['playback'] == 3 and not state['audio'] and not state['sfx']:
            return state
    raise RuntimeError('Playback did not finish')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', nargs='+', default=[
        'chikorita', 'meganium', 'togetic', 'weavile', 'dusknoir', 'metagross',
        'luxray', 'unown_a', 'seviper', 'mew', 'drapion'])
    parser.add_argument('--all-species', action='store_true')
    args = parser.parse_args()
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    origin = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(origin[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Regenerate checkpoints for the current ROM and symbols')
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in names]
    args.output.mkdir(parents=True, exist_ok=True)
    driver = Driver(args.checkpoints / 'cold-listing-core', args.checkpoints / 'input-copy.gbc',
        Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
        args.checkpoints / 'input-copy.sav', args.output / 'core.log')
    results = []
    try:
        for name in names if args.all_species else args.species:
            index = names.index(name)
            prior, direction = predecessor(index)
            driver.command(f'load {args.checkpoints / "listing-states" / f"listing-{prior:03}.s0"}')
            driver.command('rawcolor')
            move(driver, direction, index)
            driver.run(('accept',), key='a')
            settle(driver)
            for page in (0, 1, 0):
                driver.run(frames=2)
                ui = driver.command('ui')
                issues = audit(repo, ui)
                if ui['types'] != expected_types(repo, name):
                    issues.append('wrong_species_types')
                if ui['page'] != page:
                    issues.append('wrong_page')
                label = f'{name}-page{page + 1}'
                driver.command(f'image {args.output / label}.ppm')
                (args.output / f'{label}.json').write_text(json.dumps(ui, indent=2) + '\n')
                results.append(dict(species=name, page=page, issues=issues))
                driver.run(frames=2, key='a')
                driver.run(frames=2)
            target = index + 1 if index + 1 < len(names) else index - 1
            driver.run(('change_species',), key='down' if target > index else 'up')
            state = settle(driver)
            driver.run(frames=2)
            ui = driver.command('ui')
            issues = audit(repo, ui)
            if ui['types'] != expected_types(repo, names[target]):
                issues.append('wrong_species_types')
            if state['selected_index'] != target:
                issues.append('wrong_paging_destination')
            results.append(dict(species=names[target], path='internal_paging', issues=issues))
    finally:
        driver.close()
    (args.output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(dict(checked=len(results), failures=[r for r in results if r['issues']])))
    return int(any(r['issues'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
