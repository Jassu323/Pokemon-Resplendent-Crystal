"""Compile bounded Dex Moves indexes over authoritative game data."""
import json
from pathlib import Path
import re
from pokedex_info_assets import species, constants, evolution_graph, future_stages

ROOT = Path(__file__).resolve().parents[1]

def family_egg_sources(root, names, eggs):
    graph = evolution_graph(root)
    parents = dict(zip(names, names))

    def family(name):
        while parents[name] != name:
            parents[name] = parents[parents[name]]
            name = parents[name]
        return name

    for name, edges in graph.items():
        for target, _ in edges:
            if target not in parents:
                raise ValueError(f'Unknown evolution target: {name} -> {target}')
            parents[family(target)] = family(name)
    for name in names:
        future_stages(graph, name)

    families = {}
    for name in names:
        families.setdefault(family(name), []).append(name)
    sources = {}
    for members in families.values():
        lists = {}
        for name in members:
            if eggs[name]:
                lists.setdefault(tuple(eggs[name]), name)
        if len(lists) > 1:
            raise ValueError('Conflicting egg-move lists in evolution family: ' + ', '.join(members))
        source = next(iter(lists.values()), None)
        for name in members:
            sources[name] = source or name
    return sources

def compile(root=ROOT):
    names = species(root)
    moves = constants(root / 'constants/move_constants.asm')
    move_names = re.findall(r'^\s*li "([^"]+)"', (root / 'data/moves/names.asm').read_text(), re.M)
    machine = re.findall(r'^\s*add_(tm|hm|mt)\s+(\w+)', (root / 'constants/item_constants.asm').read_text(), re.M)
    if len(machine) != 60 or moves.get('LEEK_SLAP') != len(move_names):
        raise ValueError('Move/name or machine cardinality changed')
    levels, eggs, level_pointer, egg_pointer = {}, {}, {}, {}
    for suffix in ('kanto', 'johto', 'custom'):
        text = (root / f'data/pokemon/evos_attacks_{suffix}.asm').read_text()
        pointers = re.findall(r'^\s*dw (\w+EvosAttacks)', text, re.M)
        blocks = dict(re.findall(r'^(\w+EvosAttacks):\s*\n(.*?)(?=^\w+EvosAttacks:|\Z)', text, re.M | re.S))
        start = len(levels)
        for name, pointer in zip(names[start:start + len(pointers)], pointers):
            block = blocks[pointer]
            if block.count('db 0') < 2:
                raise ValueError(f'Unexpected evolution/learnset delimiters: {name}')
            evos, learn = re.split(r'\bdb 0\b', block, maxsplit=1)
            offset = 1 + sum(5 if 'EVOLVE_STAT' in line else 4
                             for line in evos.splitlines() if re.search(r'\bdbb?w?bw?\s+EVOLVE_', line))
            levels[name] = [(int(a), b) for a, b in re.findall(r'^\s*dbw\s+(\d+),\s*(\w+)', learn, re.M)]
            level_pointer[name] = f'{pointer} + {offset}'
        text = (root / f'data/pokemon/egg_moves_{suffix}.asm').read_text()
        pointers = re.findall(r'^\s*dw (\w+)\s*(?:;[^\n]*)?$', text.split('\n\n', 2)[1], re.M)
        blocks = dict(re.findall(r'^(\w+):\s*\n(.*?)(?=^\w+:|\Z)', text, re.M | re.S))
        start = len(eggs)
        for name, pointer in zip(names[start:start + len(pointers)], pointers):
            eggs[name] = re.findall(r'^\s*dw\s+(\w+)', blocks[pointer], re.M)
            egg_pointer[name] = pointer
    if list(levels) != names or list(eggs) != names:
        raise ValueError('Species pointer order changed')
    # Family inheritance changes Dex pointers only, never the game's egg lists.
    egg_sources = family_egg_sources(root, names, eggs)
    asm = ['; Generated Moves metadata. Source learnsets remain authoritative.', 'PokedexMovesSpecies:']
    manifest = {}
    for name in names:
        stem = {'PORYGON_Z': 'porygonz'}.get(name, name.lower())
        text = (root / f'data/pokemon/base_stats/{stem}.asm').read_text()
        line = re.search(r'^\s*tmhm\s*(.*?)$', text, re.M)[1].split(';')[0]
        eligible = {s.strip() for s in line.split(',') if s.strip()}
        tm = [i + 1 for i, (kind, move) in enumerate(machine[:57]) if move in eligible]
        tutors = [i + 1 for i, (kind, move) in enumerate(machine[57:]) if move in eligible]
        streams = [levels[name], [(n, machine[n - 1][1]) for n in tm],
                   [(n, machine[n + 56][1]) for n in tutors], [(0, m) for m in eggs[egg_sources[name]]]]
        pages = [(kind, rows[first:first + 5]) for kind, rows in enumerate(streams) for first in range(0, len(rows), 5)]
        if len(pages) > 19:
            raise ValueError(f'{name} needs {len(pages)} Moves pages; limit is 19')
        for rows in streams:
            if len(rows) > 255 or any(m not in moves or moves[m] == 0 for _, m in rows):
                raise ValueError(f'Invalid Moves data: {name}')
        manifest[name] = dict(streams=streams, pages=pages, machines=tm, tutors=tutors,
                              egg_source=egg_sources[name], egg_pointer=egg_pointer[egg_sources[name]])
        asm += [f'\tdb {max(1, len(pages))}']
        for count, pointer in zip(map(len, streams), (level_pointer[name], f'.tm_{name}', f'.tut_{name}', egg_pointer[egg_sources[name]])):
            asm += [f'\tdb {count}, BANK({pointer.split()[0]})', f'\tdw {pointer}']
    for name in names:
        asm += [f'.tm_{name}:', '\tdb ' + ', '.join(map(str, manifest[name]['machines'] or [0])),
                f'.tut_{name}:', '\tdb ' + ', '.join(map(str, manifest[name]['tutors'] or [0]))]
    asm += ['PokedexMovesNamePointers:']
    at = 0
    for text in move_names:
        asm += [f'\tdw MoveNames + {at}']
        at += len(text) + 1
    asm += [f'ASSERT MoveNames + {at} <= $8000', 'PokedexMovesMachineMoves:']
    asm += [f'\tdw {move}' for _, move in machine]
    output = root / 'build/dex-moves-assets'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'tables.asm').write_text('\n'.join(asm) + '\n')
    (output / 'evos_exports.asm').write_text('\n'.join('EXPORT ' + p.split()[0] for p in level_pointer.values()) + '\n')
    (output / 'egg_exports.asm').write_text('\n'.join('EXPORT ' + p for p in sorted(set(egg_pointer.values()))) + '\n')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    level = (root / 'gfx/font/font_battle_extra.2bpp').read_bytes()[14 * 16:15 * 16]
    (output / 'level.2bpp').write_bytes(bytes(v for y in range(8) for v in (0, (~(level[2*y] | level[2*y+1])) & 255)))
    return manifest

if __name__ == '__main__':
    data = compile()
    print(json.dumps(dict(species=len(data), pages=sum(len(d['pages']) for d in data.values()),
                         max_pages=max(len(d['pages']) for d in data.values()))))
