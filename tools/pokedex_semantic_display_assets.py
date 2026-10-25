"""Keep semantic Selected indexes while omitting prepared display pixels."""
import argparse
import json
from pathlib import Path

from pokedex_info_assets import evolution_graph, future_stages, previous_stages, species
from pokedex_moves_assets import compile as compile_moves


def compile(root):
    ancestors = 'DEF DEX_RUNTIME_ANCESTORS EQU 1' in (root / 'includes.asm').read_text()
    names = species(root)
    graph = evolution_graph(root)
    # Lists are deduplicated as whole semantic sequences, not bitmap glyphs.
    lists = {}
    asm = ['; Semantic target/method records; no generated text pixels.',
           'PokedexInfoSemanticSpecies:']
    for name in names:
        groups = [future_stages(graph, name)]
        if ancestors:
            groups.append(previous_stages(graph, name))
        if 1 + sum((len(group) + 1) // 2 for group in groups) > 19:
            raise ValueError(f'{name} exceeds the Info page limit')
        for group in groups:
            records = tuple((target, tuple(method)) for target, method in group)
            number = lists.setdefault(records, len(lists))
            asm += [f'\tdb {len(records)}', f'\tdw PokedexInfoSemanticList{number}']
    for records, number in lists.items():
        asm += [f'PokedexInfoSemanticList{number}:']
        for target, method in records:
            kind, parameter, *extra = method
            asm += [f'\tdw {target}', f'\tdb {kind}, {parameter}, {extra[0] if extra else 0}']
    asm += ['PokedexInfoSemanticEnd:']
    output = root / 'build/dex-runtime-display-assets'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'semantic-info.asm').write_text('\n'.join(asm) + '\n')
    moves = compile_moves(root)
    report = dict(species=len(names), distinct_lists=len(lists),
                  semantic_info_bytes=(6 if ancestors else 3) * len(names) + 5 * sum(map(len, lists)),
                  ancestors=ancestors, ancestor_species=sum(bool(previous_stages(graph, n)) for n in names),
                  generated_info_pixel_bytes=0, moves_species=len(moves))
    (output / 'semantic-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    print(compile(parser.parse_args().root))
