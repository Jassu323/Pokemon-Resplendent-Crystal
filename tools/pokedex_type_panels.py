"""Generate Type lower-panel layout records from existing chart/palette/tile data."""
import argparse
from pathlib import Path
import re

from pokedex_info_assets import constants


def generate(root, output):
    types = constants(root / 'constants/type_constants.asm')
    factors = {name: int(value) for name, value in re.findall(
        r'DEF\s+(\w+)\s+EQU\s+(\d+)\s*(?:;.*)?$',
        (root / 'constants/battle_constants.asm').read_text(), re.M)}
    owner = (root / 'engine/pokedex/pokedex_types.asm').read_text()
    alphabet = owner.split('.Alphabetical:', 1)[1].split('.LoadGraphics:', 1)[0]
    names = [name.strip() for row in re.findall(r'^\s*db (.+)$', alphabet, re.M)
             for name in row.split(',')]
    assert len(names) == 18 and len(set(names)) == 18
    ids = [types[name] for name in names]
    matrix = [[10] * 18 for _ in names]
    for line in (root / 'data/types/type_matchups.asm').read_text().splitlines():
        line = line.split(';', 1)[0].strip()
        if not line.startswith('db '):
            continue
        values = [value.strip() for value in line[3:].split(',')]
        if values == ['-1']:
            break
        if values == ['-2']:
            continue
        attack, defense, factor = values
        matrix[ids.index(types[attack])][ids.index(types[defense])] = factors[factor]
    slots = owner.split('.Slots:', 1)[1].split('ASSERT @ - .Slots', 1)[0]
    tile_ids = [tile for low, high in re.findall(r'FOR tile_id, \$([0-9a-f]+), \$([0-9a-f]+)', slots)
                for tile in range(int(low, 16), int(high, 16))]
    assert len(tile_ids) == 178
    accents = []
    for name in names:
        stem = 'psychic' if name == 'PSYCHIC_TYPE' else name.lower()
        colors = re.findall(r'RGB\s+(\d+),\s*(\d+),\s*(\d+)',
                            (root / f'gfx/types/{stem}.pal').read_text())
        r, g, b = map(int, colors[2])
        accents.append((r | g << 5 | b << 10).to_bytes(2, 'little'))
    chars = {char: int(value, 16) for char, value in re.findall(
        r'charmap\s+"(.)"\s*,\s*\$([0-9a-f]+)',
        (root / 'constants/charmap.asm').read_text().split('; Japanese control')[0], re.I)}
    lines = ['; Generated from the canonical chart and existing tiles. Do not edit.',
             'PokedexTypes_PanelPointers:']
    lines += [f'\tdw PokedexTypes_Panel_{name}' for name in names]
    for defense, name in enumerate(names):
        weak = [i for i in range(18) if matrix[i][defense] == 20]
        resist = [i for i in range(18) if matrix[i][defense] == 5
                  or name == 'STEEL' and matrix[i][defense] == 0]
        immune = [] if name == 'STEEL' else [i for i in range(18) if matrix[i][defense] == 0]
        rrow = 3 if len(weak) > 4 else 2
        metadata = [len(immune), len(weak), len(resist), rrow + 12]
        ordered = weak + resist + immune
        metadata += ordered + [255] * (18 - len(ordered))
        tiles, attrs, palette = [0x32] * 100, [0] * 100, bytearray(40)
        for y in range(5):
            tiles[y * 20] = tiles[y * 20 + 19] = 0x29
            attrs[y * 20], attrs[y * 20 + 19] = 8, 8 | 32
        for label, row, listing in (('W', 0, weak), ('R', rrow, resist), ('I', 4, immune)):
            if label == 'I' and not immune:
                continue
            tiles[row * 20 + 1:row * 20 + 3] = [chars[label], chars[':']]
            for index, type_ in enumerate(listing):
                y, col = row + index // 4, index % 4
                assert y < 5, (name, label, listing)
                x = 3 + col * 4
                tiles[y * 20 + x:y * 20 + x + 4] = tile_ids[type_ * 4:type_ * 4 + 4]
                attrs[y * 20 + x:y * 20 + x + 4] = [8 | col + 1] * 4
                palette[y * 8 + col * 2:y * 8 + col * 2 + 2] = accents[type_]
        payload = bytes(metadata + tiles + attrs) + palette
        assert len(payload) == 262
        lines.append(f'PokedexTypes_Panel_{name}:')
        for start in range(0, len(payload), 16):
            lines.append('\tdb ' + ', '.join(f'${value:02x}' for value in payload[start:start + 16]))
        lines.append(f'ASSERT @ - PokedexTypes_Panel_{name} == 262')
    output.write_text('\n'.join(lines) + '\n')
    return dict(types=18, records=18 * 262, index=36)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(generate(args.root, args.output))
