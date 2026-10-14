"""Read-only VRAM ownership preflight for the New Entry Description layout."""
import json

from .assets import Repository
from .cold_listing import ROOT


def resident_cells(asset):
    indices = list(range(49))
    for source in range(asset.total - asset.width * asset.width):
        tile = 49 + source
        indices.append(tile + (tile >= 127))
    if max(indices) > 255:
        raise ValueError('Resident dictionary exceeds the signed BG region: ' + asset.name)
    return {0x9000 + (tile if tile < 128 else tile - 256) * 16 for tile in indices}


def run():
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    assets = repo.load()
    regions = {
        'description_type_objs': set(range(0x8280, 0x8380, 16)),
        'info_mini_and_hp_objs': set(range(0x8380, 0x85a0, 16)),
        'normal_description_footprint': set(range(0x8b10, 0x8b50, 16)),
        'alternate_description_footprint': set(range(0x96c0, 0x9700, 16)),
        'info_atlas_a': {0x9000 + (tile if tile < 128 else tile - 256) * 16
                         for tile in (*range(0xfa, 0x100), *range(0x28, 0x32),
                                      *range(0x78, 0x80), *range(0x64, 0x6c), *range(0x70, 0x78))},
        'info_atlas_b': set(range(0x9000, 0x9280, 16)),
    }
    result = dict(baseline=repo.hashes, asset_count=len(assets),
                  max_dictionary_tiles=max(a.total for a in assets),
                  max_tail_tiles=max(a.total - a.width * a.width for a in assets),
                  bank1_regions={})
    for name, cells in regions.items():
        collisions = [{"asset": a.name, "overlapping_tiles": len(resident_cells(a) & cells)}
                      for a in assets if resident_cells(a) & cells]
        result['bank1_regions'][name] = dict(tiles=len(cells), collisions=len(collisions),
                                           examples=collisions[:12])
    output = ROOT / 'build/dex-new-entry-description-scope-20261013'
    output.mkdir(exist_ok=True)
    (output / 'memory-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run()
