"""Compile immutable recovery-only atlas data for the third architecture trial."""
import argparse
import json
from pathlib import Path

from pokedex_info_assets import Compiler


def compile(root):
    compiler = Compiler(root)
    data = compiler.compile(ancestors='DEF DEX_RUNTIME_ANCESTORS EQU 1' in (root / 'includes.asm').read_text())
    vectors, lists = {}, {}
    asm = ['; Recovery only: main page rendering still composes native pixels.', 'PokedexROMRestoreSpecies:']
    for name in data['names']:
        pages = []
        for records in data['pages'][name]:
            tiles = []
            for record in records:
                for line in data['records'][record][1]:
                    for tile in data['lines'][line][1]:
                        if tile not in tiles:
                            tiles.append(tile)
            pages.append(vectors.setdefault(tuple(tiles), len(vectors)))
        index = lists.setdefault(tuple(pages), len(lists))
        asm += [f'\tdw PokedexROMRestoreList{index}']
    for pages, index in lists.items():
        asm += [f'PokedexROMRestoreList{index}:']
        asm += [f'\tdw PokedexROMRestoreVector{page}' for page in pages]
    pointer = lambda tile: f'PokedexROMRestoreGFX + {tile} * TILE_SIZE'
    for tiles, index in vectors.items():
        asm += [f'PokedexROMRestoreVector{index}:', '\tdw ' + ', '.join(map(pointer, tiles))]
    asm += ['PokedexROMRestoreShared:', '\tdw ' + ', '.join(map(pointer, data['shared'])),
            'PokedexROMRestoreNumbers:']
    asm += ['\tdw ' + ', '.join(map(pointer, row)) for row in data['numbers']]
    asm += ['PokedexROMRestoreMetadataEnd:']
    output = root / 'build/dex-runtime-display-assets'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'rom-restore.asm').write_text('\n'.join(asm) + '\n')
    (output / 'rom-restore.2bpp').write_bytes(b''.join(compiler.pool))
    report = dict(glyph_bytes=len(compiler.pool) * 16,
                  species_index_bytes=2 * len(data['names']),
                  evolution_list_bytes=sum(map(len, lists)) * 2,
                  evolution_vector_bytes=sum(map(len, vectors)) * 2,
                  shared_pointer_bytes=2 * len(data['shared']), number_pointer_bytes=256 * 8)
    (output / 'rom-restore-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    print(compile(parser.parse_args().root))
