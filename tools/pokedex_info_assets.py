"""Compile Dex Info's local glyphs and evolution display records.

The game copies prepared tiles rather than shifting glyphs or walking the
evolution graph during playback. Outputs are disposable build artifacts.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LABELS = ('HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe')
TITLE_CELLS = {'Stats': tuple(range(0xca, 0xd0)),
               'Evolutions': (*range(0xd7, 0xdf), 0xe4, 0xe5, 0xcf)}
COLORS = ((13, 27, 2, 11, 22, 2), (29, 25, 3, 25, 22, 3),
          (28, 12, 2, 23, 10, 2), (2, 24, 29, 2, 19, 24),
          (9, 13, 27, 8, 11, 22), (26, 4, 21, 20, 3, 16))


def species(root=ROOT):
    text = (root / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0]
    return re.findall(r'^\s*const\s+(\w+)', text, re.M)


def constants(path):
    result, value = {}, 0
    for line in path.read_text().splitlines():
        if match := re.match(r'\s*const_def(?:\s+(\d+))?', line):
            value = int(match[1] or 0)
        elif match := re.match(r'\s*const_next\s+(\d+)', line):
            value = int(match[1])
        elif match := re.match(r'\s*const\s+(\w+)', line):
            result[match[1]] = value
            value += 1
    return result


def evolution_graph(root=ROOT):
    names = species(root)
    pointers, blocks = [], {}
    for suffix in ('kanto', 'johto', 'custom'):
        text = (root / f'data/pokemon/evos_attacks_{suffix}.asm').read_text()
        pointers += re.findall(r'^\s*dw\s+(\w+EvosAttacks)', text, re.M)
        for match in re.finditer(r'^(\w+EvosAttacks):\s*\n(.*?)(?=^\w+EvosAttacks:|\Z)', text, re.M | re.S):
            edges = []
            for line in match[2].splitlines():
                line = line.split(';')[0].strip()
                if re.match(r'db\s+0\b', line):
                    break
                if entry := re.match(r'dbb?w?bw?\s+(EVOLVE_\w+)\s*,\s*(.*)', line):
                    fields = [entry[1]] + [s.strip() for s in entry[2].split(',')]
                    edges.append((fields[-1], fields[:-1]))
            blocks[match[1]] = edges
    if len(pointers) != len(names):
        raise ValueError('Evolution pointers and species constants disagree')
    return dict(zip(names, (blocks[p] for p in pointers)))


def future_stages(graph, name, ancestors=()):
    if name in ancestors:
        raise ValueError(f'Evolution cycle: {ancestors + (name,)}')
    result = []
    for target, method in graph[name]:
        result.append((target, method))
        result.extend(future_stages(graph, target, ancestors + (name,)))
    return result


def width(value):
    return min(101, 2 * (value // 5))


def pack(pixels):
    result = bytearray()
    for row in pixels:
        result += bytes((sum((p & 1) << (7 - x) for x, p in enumerate(row)),
                         sum((p >> 1) << (7 - x) for x, p in enumerate(row))))
    return bytes(result)


def unpack(tile):
    return [[((tile[2 * y] >> (7 - x)) & 1) |
             (((tile[2 * y + 1] >> (7 - x)) & 1) << 1)
             for x in range(8)] for y in range(8)]


class Compiler:
    def __init__(self, root=ROOT):
        self.root = root
        self.font = (root / 'gfx/font/font.1bpp').read_bytes()
        battle_font = (root / 'gfx/font/font_battle_extra.2bpp').read_bytes()
        level = battle_font[14 * 16:15 * 16]
        self.level_glyph = bytes(level[y] | level[y + 1] for y in range(0, 16, 2))
        bars = (root / 'gfx/pokedex/dex_stat_bar.2bpp').read_bytes()
        if len(bars) != 10 * 16:
            raise ValueError('The stat bar sheet must contain exactly ten tiles')
        # Source art: background=0, fill=1, border=2. Local BG palettes use
        # white=0, border=1, fill=2, background=3.
        self.bars = [[[3, 2, 1, 0][p] for p in row]
                     for i in range(10) for row in unpack(bars[i * 16:i * 16 + 16])]
        self.bars = [self.bars[i * 8:i * 8 + 8] for i in range(10)]
        self.chars = {m[1]: int(m[2], 16) for m in re.finditer(
            r'charmap\s+"(.)"\s*,\s*\$([0-9a-f]+)',
            (root / 'constants/charmap.asm').read_text().split('; Japanese control')[0], re.I)}
        # Do not use the later Japanese charmap's ASCII aliases.
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789':
            self.chars[c] = (128 + ord(c) - ord('A') if c.isupper() else
                             160 + ord(c) - ord('a') if c.islower() else 246 + int(c))
        self.pool, self.ids = [], {}
        self.lines = {}

    def glyph(self, char):
        if char == '<LV>':
            return self.level_glyph
        comparisons = {'>': (0, 64, 32, 16, 32, 64, 0, 0),
                       '<': (0, 16, 32, 64, 32, 16, 0, 0),
                       '=': (0, 0, 112, 0, 112, 0, 0, 0)}
        if char in comparisons:
            return comparisons[char]
        if char == ' ':
            return bytes(8)
        code = self.chars[char]
        if code < 128:
            raise ValueError(f'Unsupported local Info character: {char}')
        return self.font[(code - 128) * 8:(code - 127) * 8]

    def tile(self, pixels):
        tile = pack(pixels)
        if tile not in self.ids:
            self.ids[tile] = len(self.pool)
            self.pool.append(tile)
        return self.ids[tile]

    def text(self, text, phase, count=None, background=2):
        glyphs = re.findall(r'<LV>|.', text)
        count = count or (phase + len(glyphs) * 8 + 7) // 8
        pixels = [[background] * (count * 8) for _ in range(8)]
        for index, char in enumerate(glyphs):
            for y, byte in enumerate(self.glyph(char)):
                for x in range(8):
                    if byte & (128 >> x):
                        pixels[y][phase + index * 8 + x] = 0
        return pixels

    def line(self, text):
        if text not in self.lines:
            pixels = (self.compact_text(text) if len(re.findall(r'<LV>|.', text)) > 15 else
                      self.text(text, 5)) if text else []
            self.lines[text] = [self.tile([row[x:x + 8] for row in pixels])
                                for x in range(0, len(pixels[0]) if pixels else 0, 8)]
        return list(self.lines).index(text)

    def compact_text(self, text):
        # Long combined requirements retain every word, but omit glyph padding.
        pixels = [[2] * 5 for _ in range(8)]
        for char in re.findall(r'<LV>|.', text):
            glyph = self.glyph(char)
            ink = [x for x in range(8) if any(byte & (128 >> x) for byte in glyph)]
            columns = range(min(ink), max(ink) + 1) if ink else range(4)
            for y, byte in enumerate(glyph):
                pixels[y].extend(0 if ink and byte & (128 >> x) else 2 for x in columns)
                if ink:
                    pixels[y].append(2)
        length = len(pixels[0])
        if length > 16 * 8:
            raise ValueError(f'Evolution requirement exceeds the panel: {text}')
        for row in pixels:
            row.extend([2] * (-length % 8))
        return pixels

    def titles(self):
        result, resident = {}, {}
        for text, cells in TITLE_CELLS.items():
            if any(any(self.font[(cell - 128) * 8:(cell - 127) * 8]) for cell in cells):
                raise ValueError('Info title allocation is no longer an unused font gap')
            pixels = self.text(text, 5)
            tiles = [pack([row[x:x + 8] for row in pixels])
                     for x in range(0, len(pixels[0]), 8)]
            if len(tiles) != len(cells):
                raise ValueError(f'Info title allocation changed: {text}')
            for cell, tile in zip(cells, tiles):
                if cell in resident and resident[cell] != tile:
                    raise ValueError('Shared Info title cells must contain identical pixels')
                resident[cell] = tile
            result[text] = dict(cells=list(cells), tiles=tiles)
        return result

    def compile(self):
        graph, names = evolution_graph(self.root), species(self.root)
        display = re.findall(r'\bdname\s+"([^"]+)"',
            (self.root / 'data/pokemon/names.asm').read_text().split('PokemonNames::')[1])
        display = dict(zip(names, display))
        item_ids = constants(self.root / 'constants/item_constants.asm')
        items = re.findall(r'\bli\s+"([^"]+)"', (self.root / 'data/items/names.asm').read_text())
        records, roots = {}, {}
        def condition(method):
            kind, param, *extra = method
            if kind == 'EVOLVE_LEVEL':
                return f'Level {param}', ''
            if kind == 'EVOLVE_ITEM':
                return items[item_ids[param] - 1], ''
            if kind == 'EVOLVE_TRADE':
                return 'Trade' if param == '-1' else f'Trade {items[item_ids[param] - 1]}', ''
            if kind == 'EVOLVE_HAPPINESS':
                return 'friendship', ''
            if kind == 'EVOLVE_STAT':
                compare = {'ATK_GT_DEF': '>', 'ATK_LT_DEF': '<', 'ATK_EQ_DEF': '='}[extra[0]]
                return f'<LV>{param} Atk {compare} Def', ''
            raise ValueError(kind)
        for name in names:
            roots[name] = []
            for target, method in future_stages(graph, name):
                key = (target, tuple(method))
                if key not in records:
                    texts = (display[target], *condition(method))
                    if texts[2]:
                        raise ValueError('Evolution entries must fit a name and one requirement line')
                    records[key] = (target, [self.line(t) for t in texts], texts)
                roots[name].append(list(records).index(key))
            if 1 + (len(roots[name]) + 1) // 2 > 4:
                raise ValueError(f'{name} requires additional resident page badges')
            for first in range(0, len(roots[name]), 2):
                used = {tile for i in roots[name][first:first + 2]
                        for line in list(records.values())[i][1]
                        for tile in list(self.lines.values())[line]}
                if len(used) > 40:
                    raise ValueError(f'{name} evolution page requires {len(used)} unique tiles; capacity is 40')
        label_chars = ''.join(dict.fromkeys(''.join(LABELS)))
        shared = [self.tile(self.text(c, 1, 1)) for c in label_chars]
        label_map = [[label_chars.index(c) for c in text] for text in LABELS]
        for terminal in (1, 3, 5, 7, 8):
            source = self.bars[8 if terminal == 8 else 4 + terminal // 2]
            pixels = [row[:] if terminal == 8 else row[1:terminal + 1] + [3] * (8 - terminal)
                      for row in source]
            shared.append(self.tile(pixels))
        numbers = []
        for value in range(256):
            pixels = self.text(f'{value:3}', 5, 4)
            for row in pixels:
                row[24:] = [3 if p == 2 else p for p in row[24:]]
            source = self.bars[0 if width(value) == 2 else 9]
            for y in range(8):
                for x in range(min(3, width(value))):
                    pixels[y][29 + x] = source[y][x]
            numbers.append([self.tile([row[x:x + 8] for row in pixels]) for x in range(0, 32, 8)])
        stats = {}
        for name in names:
            stem = {'UNOWN': 'unown', 'PORYGON_Z': 'porygonz'}.get(name, name.lower())
            text = (self.root / f'data/pokemon/base_stats/{stem}.asm').read_text()
            match = re.search(r'\bdb\s+((?:\d+\s*,\s*){5}\d+)\s*\n\s*;\s*hp', text, re.I)
            values = list(map(int, match[1].split(',')))
            values = [values[i] for i in (0, 1, 2, 4, 5, 3)]
            if any(width(v) > 99 for v in values[1:]):
                raise ValueError(f'{name} needs an additional non-HP endpoint')
            stats[name] = values
            used = set(shared)
            used.update(tile for value in values for tile in numbers[value])
            if len(used) > 40:
                raise ValueError(f'{name} Stats page requires {len(used)} unique tiles; capacity is 40')
        return dict(names=names, roots=roots, records=list(records.values()),
                    lines=list(self.lines.items()), shared=shared, labels=label_map,
                    numbers=numbers, stats=stats, titles=self.titles())

    def write(self, destination):
        data = self.compile()
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'tiles.2bpp').write_bytes(b''.join(self.pool))
        # Both headings end in the same partial 's' tile, sharing cell $cf.
        title_tiles = {cell: tile for title in data['titles'].values()
                       for cell, tile in zip(title['cells'], title['tiles'])}
        (destination / 'titles.2bpp').write_bytes(b''.join(title_tiles.values()))
        pointer = lambda tile: f'PokedexInfoTileGFX + {tile} * TILE_SIZE'
        asm = ['; Generated by tools/pokedex_info_assets.py; do not edit.', 'PokedexInfoSpecies:']
        for name in data['names']:
            asm += [f'\tdb {len(data["roots"][name])}', f'\tdw .{name}']
        for name in data['names']:
            asm += [f'.{name}:']
            asm += [f'\tdw PokedexInfoEvolution{i}' for i in data['roots'][name]]
        for i, (target, lines, _) in enumerate(data['records']):
            asm += [f'PokedexInfoEvolution{i}:', f'\tdw {target}']
            asm += ['\tdw ' + ', '.join(f'PokedexInfoLine{line}' for line in lines)]
        for i, (_, tiles) in enumerate(data['lines']):
            asm += [f'PokedexInfoLine{i}:', f'\tdb {len(tiles)}']
            asm += ['\tdw ' + pointer(tile) for tile in tiles]
        asm += ['PokedexInfoShared:'] + ['\tdw ' + pointer(tile) for tile in data['shared']]
        asm += ['PokedexInfoLabelTiles:']
        asm += ['\tdb ' + ', '.join(map(str, row + [255] * (3 - len(row)))) for row in data['labels']]
        asm += ['PokedexInfoNumbers:']
        asm += ['\tdw ' + ', '.join(map(pointer, row)) for row in data['numbers']]
        for text, title in data['titles'].items():
            asm += [f'PokedexInfo{text}Title:',
                    '\tdb ' + ', '.join(f'${cell:02x}' for cell in title['cells']) + ', "@"']
        (destination / 'tables.asm').write_text('\n'.join(asm) + '\n')
        report = dict(species=len(data['names']), records=len(data['records']),
                      glyph_tiles=len(self.pool), glyph_bytes=len(self.pool) * 16,
                      title_tiles=len(title_tiles),
                      max_evolution_tiles=max(sum(len(data['lines'][line][1])
                         for i in records[first:first + 2] for line in data['records'][i][1])
                         for records in data['roots'].values() for first in range(0, len(records), 2)),
                      max_evolution_unique_tiles=max(len({tile
                         for i in records[first:first + 2] for line in data['records'][i][1]
                         for tile in data['lines'][line][1]})
                         for records in data['roots'].values() for first in range(0, len(records), 2)),
                      stats=data['stats'], evolutions={name: [data['records'][i][2]
                        for i in records] for name, records in data['roots'].items()})
        (destination / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k not in ('stats', 'evolutions')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/dex-info-assets')
    Compiler().write(parser.parse_args().output)
