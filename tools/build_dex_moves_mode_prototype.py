"""Build the visual Moves encyclopedia without changing production or SRAM."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from dex_timing.assets import sha256
from dex_timing.cold_listing import ROOT
from pokedex_moves_mode_assets import compile_tables


def build(source, output, jobs=8, relink=False, unknown=False):
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build output')
    candidate = output / 'candidate'
    baseline = {s: sha256((ROOT / f'pokecrystal.{s}').read_bytes()) for s in ('gbc', 'sym', 'map')}
    if not relink:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(source / 'candidate', candidate)
        dex = candidate / 'engine/pokedex/pokedex.asm'
        replace(dex, '\tconst DEXSTATE_POPOVER\n', '\tconst DEXSTATE_POPOVER\n'
                '\tconst DEXSTATE_MOVES_MODE_INIT\n\tconst DEXSTATE_MOVES_MODE_UPDATE\n'
                '\tconst DEXSTATE_MOVES_MODE_SORT\n')
        replace(dex, '\tconst DEXSELECT_STATE_UNOWN_RETURN\n',
                '\tconst DEXSELECT_STATE_UNOWN_RETURN\n\tconst DEXSELECT_STATE_MOVES_RETURN\n')
        replace(dex, '\tdw Pokedex_UpdatePopover\n', '\tdw Pokedex_UpdatePopover\n'
                '\tdw Pokedex_InitMovesMode\n\tdw Pokedex_UpdateMovesMode\n'
                '\tdw Pokedex_UpdateMovesModeSort\n')
        replace(dex, 'Pokedex_UpdatePopover:\n', 'Pokedex_InitMovesMode:\n'
                '\tfarcall PokedexMovesMode_Initialize\n\tret\n'
                'Pokedex_UpdateMovesMode:\n\tfarcall PokedexMovesMode_Update\n\tret\n'
                'Pokedex_UpdateMovesModeSort:\n\tfarcall PokedexMovesMode_SortUpdate\n\tret\n\n'
                'Pokedex_UpdatePopover:\n')
        legacy = candidate / 'engine/pokedex/pokedex_legacy.asm'
        replace(legacy, '\tld a, [wPokedexSelectedState]\n\tcp DEXSELECT_STATE_UNOWN_RETURN\n',
                '\tld a, [wPokedexSelectedState]\n\tcp DEXSELECT_STATE_MOVES_RETURN\n'
                '\tjr nz, .ordinary_return\n\tld a, [wUnlockedUnownMode]\n\tand a\n'
                '\tld a, 3\n\tjr nz, .cursor\n\tdec a\n\tjr .cursor\n.ordinary_return\n'
                '\tld a, [wPokedexSelectedState]\n\tcp DEXSELECT_STATE_UNOWN_RETURN\n')
        replace(legacy, '.other\n; Future modes can be highlighted without changing the Listing or its order.\n',
                '.other\n\tcp DEXMENU_MOVES\n\tjr nz, .unown_check\n'
                '\tcall PokedexListing_BeginMenuTransition\n\tld a, DEXSTATE_MOVES_MODE_INIT\n'
                '\tld [wJumptableIndex], a\n\tret\n.unown_check\n')
        replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/pokedex_search.asm"',
                'INCLUDE "engine/pokedex/pokedex_search.asm"\n'
                'INCLUDE "engine/pokedex/pokedex_moves_mode.asm"')
    module = (ROOT / 'tools/dex_timing/probes/pokedex_moves_mode.asm').read_text()
    if unknown:
        module = 'DEF DEX_MOVES_MODE_UNKNOWN EQU 1\n' + module
    (candidate / 'engine/pokedex/pokedex_moves_mode.asm').write_text(module)
    shutil.copy2(ROOT / 'tools/pokedex_moves_assets.py', candidate / 'tools/pokedex_moves_assets.py')
    tables, manifest = compile_tables(candidate)
    generated = candidate / 'build/dex-moves-mode-assets'
    generated.mkdir(parents=True, exist_ok=True)
    (generated / 'tables.asm').write_text(tables)
    seen = bytearray(b'\xff' * ((len(manifest['moves']) + 7) // 8))
    for index in manifest['unknown']:
        seen[(index - 1) // 8] &= ~(1 << ((index - 1) & 7))
    (generated / 'seen.asm').write_text('\tdb ' + ', '.join(f'${b:02x}' for b in seen) + '\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    stem = 'pokecrystal-dex-moves-mode-unknown' if unknown else 'pokecrystal-dex-moves-mode'
    for suffix, digest in baseline.items():
        shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
        for alias in ('pokecrystal-dex-options', 'pokecrystal-dex-search'):
            shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'{alias}.{suffix}')
        if sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()) != digest:
            raise ValueError('Production output changed')
    battery = source / 'pokecrystal-dex-search.sav'
    shutil.copy2(battery, output / f'{stem}.sav')
    shutil.copy2(source / 'sort-manifest.json', output / 'sort-manifest.json')
    manifest.update(source=str(source), stem=stem, fixture='mixed' if unknown else 'all_seen',
                    production_hashes=baseline,
                    rom_sha256=sha256((output / f'{stem}.gbc').read_bytes()),
                    save_sha256=sha256((output / f'{stem}.sav').read_bytes()))
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--relink', action='store_true')
    parser.add_argument('--unknown', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    manifest = build(args.source.resolve(), args.output.resolve(), args.jobs, args.relink, args.unknown)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.output.resolve() / f"{manifest['stem']}.sav")
    print(json.dumps({k: manifest[k] for k in ('stem', 'fixture', 'rom_sha256')}))


if __name__ == '__main__':
    main()
