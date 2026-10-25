"""Validate runtime display inputs; retain only the shared Moves Search index."""
import argparse
from pathlib import Path
import re

from pokedex_info_assets import evolution_graph, future_stages, species
from pokedex_moves_assets import compile as validate_moves


def compile(root):
    validate_moves(root, validate_only=True)
    graph = evolution_graph(root)
    parents = {}
    for name, edges in graph.items():
        if 1 + (len(future_stages(graph, name)) + 1) // 2 > 19:
            raise ValueError(f'{name} exceeds the runtime Info page capacity')
        for target, method in edges:
            if target not in graph or target in parents:
                raise ValueError(f'Invalid/ambiguous native parent: {name} -> {target}')
            parents[target] = name
            if method[0] not in ('EVOLVE_LEVEL', 'EVOLVE_ITEM', 'EVOLVE_TRADE', 'EVOLVE_HAPPINESS', 'EVOLVE_STAT'):
                raise ValueError(method)
    names = re.findall(r'^\s*li "([^"]+)"', (root / 'data/moves/names.asm').read_text(), re.M)
    asm = ['; Shared by Selected Moves and the separate Moves Dex/Search.', 'PokedexMovesNamePointers:']
    cursor = 0
    for name in names:
        asm += [f'\tdw MoveNames + {cursor}']
        cursor += len(name) + 1
    asm += [f'ASSERT MoveNames + {cursor} <= $8000',
            'ASSERT (@ - PokedexMovesNamePointers) / 2 == NUM_ATTACKS']
    output = root / 'build/dex-runtime-display-assets'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'shared-name-pointers.asm').write_text('\n'.join(asm) + '\n')
    return dict(species=len(species(root)), shared_move_name_pointers=len(names),
                generated_info_graphics_bytes=0, generated_species_display_tables_bytes=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(compile(args.root))
