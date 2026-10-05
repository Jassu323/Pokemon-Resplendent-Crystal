"""Private, checksum-verified battery fixtures for otherwise inaccessible menus."""
import argparse
import json
from pathlib import Path
import re

from .assets import Repository, offset, sha256
from .cry_ownership import validate_output


def make_fixture(repo, source, output, location=None, capture=False, extra_fields=None):
    output = validate_output(output, (source, repo.root / 'pokecrystal.gbc'))
    symbols = repo.symbols
    before = source.read_bytes()
    after = bytearray(before)
    allowed = set()
    changes = {}

    def sram(name):
        bank, address = symbols[name]
        if not 0xa000 <= address <= 0xc000:
            raise ValueError(f'Not a saved field: {name}')
        return bank * 0x2000 + address - 0xa000

    def saved(prefix, name, size):
        bank, address = symbols[name]
        for block in ('PlayerData', 'CurMapData', 'PokemonData'):
            block_bank, start = symbols['w' + block]
            end = symbols['w' + block + 'End'][1]
            if bank == block_bank and start <= address and address + size <= end:
                return sram(prefix + block) + address - start
        raise ValueError(f'Field outside saved blocks: {name}')

    def write(name, data):
        changes[name] = list(data)
        for prefix in ('s', 'sBackup'):
            at = saved(prefix, name, len(data))
            after[at:at + len(data)] = data
            allowed.update(range(at, at + len(data)))

    def verify(data):
        for prefix in ('s', 'sBackup'):
            start, end, checksum = (sram(prefix + name) for name in ('SaveData', 'SaveDataEnd', 'Checksum'))
            if sum(data[start:end]) & 65535 != int.from_bytes(data[checksum:checksum + 2], 'little'):
                raise ValueError(f'Invalid {prefix} battery checksum')

    verify(before)
    # Item IDs are fixed cartridge constants; verify them before constructing lists.
    names = re.findall(r'^\s*const\s+(\w+)',
                       (repo.root / 'constants/item_constants.asm').read_text().split('DEF NUM_ITEMS')[0], re.M)
    ids = {'RARE_CANDY': 0x20, 'NUGGET': 0x24, 'EON_MAIL': 0xb9,
           'TMHM_CASE': 0x64, 'APRICORN_BOX': 0x5a, 'COIN_CASE': 0x36, 'BICYCLE': 0x07}
    for name, number in ids.items():
        if names[number] != name:
            raise ValueError(f'Item numbering changed: {name}')
    write('wNumItems', bytes((3,)))
    write('wItems', bytes((ids['RARE_CANDY'], 76, ids['NUGGET'], 20, ids['EON_MAIL'], 5, 255)))
    write('wNumKeyItems', bytes((4,)))
    write('wKeyItems', bytes((ids['TMHM_CASE'], ids['APRICORN_BOX'], ids['COIN_CASE'], ids['BICYCLE'], 255)))
    write('wTMsHMs', bytes((1,)) * 57)
    write('wApricornQuantities', bytes((10,)) * 7)
    write('wCoins', (999).to_bytes(2, 'big'))
    write('wPokegearFlags', bytes((before[saved('s', 'wPokegearFlags', 1)] | 2,)))
    write('wPhoneList', bytes((1, 2, 3, 4)) + bytes(7))
    write('wStatusFlags', bytes((before[saved('s', 'wStatusFlags', 1)] | 2,)))
    write('wUnownDex', bytes(range(1, 27)))
    write('wFirstUnownSeen', bytes((1,)))
    if capture:
        if names[1] != 'MASTER_BALL':
            raise ValueError('Master Ball item numbering changed')
        write('wNumBalls', bytes((1,)))
        write('wBalls', bytes((1, 99, 255)))
        size = symbols['wEndPokedexCaught'][1] - symbols['wPokedexCaught'][1]
        write('wPokedexCaught', bytes(size))
    if location:
        map_name, x, y = location
        group, number = 0, 0
        maps = {}
        for line in (repo.root / 'constants/map_constants.asm').read_text().splitlines():
            if re.match(r'^\s*newgroup\s+\w+', line):
                group, number = group + 1, 0
            match = re.match(r'^\s*map_const\s+(\w+),', line)
            if match:
                number += 1
                maps[match[1]] = (group, number)
        group, number = maps[map_name]
        for name, value in (('wMapGroup', group), ('wMapNumber', number), ('wXCoord', x), ('wYCoord', y)):
            write(name, bytes((value,)))
        # Continue preserves the saved object table, including the player's
        # camera coordinates. A map-only edit leaves an inconsistent fixture.
        for axis, number in (('X', x + 4), ('Y', y + 4)):
            for name in ('wPlayerMap' + axis, 'wPlayerLastMap' + axis,
                         'wPlayerInit' + axis, 'wPlayerObject' + axis + 'Coord'):
                write(name, bytes((number,)))
        label = re.search(r'^\s*map_attributes\s+(\w+),\s*' + map_name + r',',
                          (repo.root / 'data/maps/attributes.asm').read_text(), re.M)[1]
        attributes = offset(symbols[label + '_MapAttributes'])
        border, height, width, bank = repo.rom[attributes:attributes + 4]
        blocks = offset((bank, int.from_bytes(repo.rom[attributes + 4:attributes + 6], 'little')))
        origin_x, origin_y = x // 2 - 2, y // 2 - 2
        screen = bytes(repo.rom[blocks + row * width + col]
                       if 0 <= row < height and 0 <= col < width else border
                       for row in range(origin_y, origin_y + 5)
                       for col in range(origin_x, origin_x + 6))
        # Continue overlays this saved block window onto the freshly loaded map.
        write('wScreenSave', screen)
        cursor = offset(symbols[label + '_MapEvents']) + 2
        for size in (5, 8, 5):
            count = repo.rom[cursor]
            cursor += 1 + count * size
        count = repo.rom[cursor]
        cursor += 1
        if count > 15:
            raise ValueError('Fixture map exceeds the saved object table')
        objects = bytearray(bytes((255,)) + bytes(15)) * 15
        for index in range(count):
            objects[index * 16 + 1:index * 16 + 14] = repo.rom[cursor:cursor + 13]
            cursor += 13
        write('wMap1Object', objects)
        write('wObject1Struct', bytes(40 * 12))
        write('wObjectMasks', bytes(16))

    for name, data in (extra_fields or {}).items():
        write(name, bytes(data))
    for prefix in ('s', 'sBackup'):
        start, end, checksum = (sram(prefix + name) for name in ('SaveData', 'SaveDataEnd', 'Checksum'))
        after[checksum:checksum + 2] = (sum(after[start:end]) & 65535).to_bytes(2, 'little')
        allowed.update((checksum, checksum + 1))
    verify(after)
    changed = {index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]}
    if not changed <= allowed or len(before) != len(after) or before[0x8000:] != after[0x8000:]:
        raise RuntimeError('Fixture changed bytes outside its declared fields/checksums')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(after)
    if source.read_bytes() != before:
        raise RuntimeError('Source battery changed during fixture generation')
    result = dict(source=str(source), fixture=str(output), source_sha256=sha256(before),
                  fixture_sha256=sha256(after), location=location, capture=capture, edits=changes,
                  changed_bytes=len(changed), source_unchanged=True, checksums_valid=True,
                  note='Only this ignored test-save copy is edited; menu entry still uses normal controller input.')
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--location', nargs=3, metavar=('MAP', 'X', 'Y'))
    parser.add_argument('--capture', action='store_true', help='Only this test copy: Master Balls and no caught flags')
    args = parser.parse_args()
    root = args.root.resolve()
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    location = (args.location[0], int(args.location[1]), int(args.location[2])) if args.location else None
    print(json.dumps(make_fixture(repo, args.source.resolve(), args.output.resolve(), location, args.capture), indent=2))


if __name__ == '__main__':
    main()
