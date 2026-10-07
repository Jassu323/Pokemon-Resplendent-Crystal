"""Reproduce an isolated Search repair trial from the accepted Options build."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from dex_timing.assets import sha256
from dex_timing.cold_listing import ROOT


def build(source, output, jobs, variant):
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh private build output')
    baseline = {suffix: sha256((ROOT / f'pokecrystal.{suffix}').read_bytes())
                for suffix in ('gbc', 'sym', 'map')}
    candidate = output / 'candidate'
    shutil.copytree(source / 'candidate', candidate)
    if variant in ('palette', 'combined', 'cursor'):
        replace(candidate / 'engine/gfx/cgb_layouts.asm',
                '_CGB_PokedexSearchOption:\n',
                '_CGB_PokedexSearchOption:\n\tld hl, PartyMenuOBPals\n'
                '\tld de, wOBPals1\n\tcall LoadHLPaletteIntoDE\n')
    if variant in ('reveal', 'combined', 'cursor'):
        replace(candidate / 'engine/pokedex/pokedex.asm',
                '\tld a, SCGB_POKEDEX_SEARCH_OPTION\n\tcall Pokedex_GetSGBLayout\n'
                '\tcall Pokedex_IncrementDexPointer\n',
                '\tld a, SCGB_POKEDEX_SEARCH_OPTION\n\tcall Pokedex_GetSGBLayout\n'
                '\tfarcall PokedexListing_RevealMenu\n\tcall Pokedex_IncrementDexPointer\n')
    if variant in ('combined', 'cursor'):
        replace(candidate / 'engine/pokedex/pokedex.asm',
                '\tld a, SCGB_POKEDEX\n\tcall Pokedex_GetSGBLayout\n'
                '\tcall Pokedex_IncrementDexPointer\n',
                '\tld a, SCGB_POKEDEX\n\tcall Pokedex_GetSGBLayout\n'
                '\tfarcall PokedexListing_RevealMenu\n\tcall Pokedex_IncrementDexPointer\n')
        replace(candidate / 'engine/pokedex/pokedex.asm',
                '\tcall ByteFill\n\tcall Pokedex_SetBGMapMode4\n'
                '\tcall Pokedex_ResetBGMapMode\n\tfarcall DrawPokedexSearchResultsWindow\n',
                '\tcall ByteFill\n\tfarcall DrawPokedexSearchResultsWindow\n'
                '\tcall Pokedex_SetBGMapMode4\n\tcall Pokedex_ResetBGMapMode\n')
        three = candidate / 'engine/pokedex/pokedex_3.asm'
        replace(three, '\tdb   "Esults"\n', '\tdb   "esults"\n')
        replace(three, '\tnext "D!@"\n', '\tnext "d!@"\n')
        replace(three, '\thlcoord 5, 0\n\tld [hl], $3f\n'
                '\thlcoord 5, 10\n\tld [hl], $40\n',
                '\thlcoord 5, 0\n\tld [hl], POKEDEX_LEGACY_ARROW_TILE\n'
                '\thlcoord 5, 10\n\tld [hl], POKEDEX_LEGACY_ARROW_TILE\n'
                '\thlcoord 5, 10, wAttrmap\n\tld [hl], BG_YFLIP\n')
    if variant == 'cursor':
        replace(candidate / 'engine/gfx/cgb_layouts.asm',
                '\tld hl, PokedexCursorPalette\n\tld de, wOBPals1 palette 7 ; green cursor palette\n'
                '\tld bc, 1 palettes\n\tld a, BANK(wOBPals1)\n\tcall FarCopyWRAM\n\tret\n',
                '\tld hl, PokedexCursorPalette\n\tld de, wOBPals1 palette 7 ; green cursor palette\n'
                '\tld bc, 1 palettes\n\tld a, BANK(wOBPals1)\n\tcall FarCopyWRAM\n'
                '\tld a, [wJumptableIndex]\n\tsub DEXSTATE_SEARCH_RESULTS_SCR\n'
                '\tcp 2\n\tret nc\n\tld hl, PokedexListDarkGray\n'
                '\tld de, wOBPals1 palette 7 + 3 colors\n\tld bc, 1 colors\n'
                '\tld a, BANK(wOBPals1)\n\tcall FarCopyWRAM\n\tret\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in baseline:
        shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'pokecrystal-dex-options.{suffix}')
        shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'pokecrystal-dex-search.{suffix}')
        if sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()) != baseline[suffix]:
            raise ValueError('Production output changed')
    shutil.copy2(source / 'sort-manifest.json', output / 'sort-manifest.json')
    (output / 'probe.json').write_text(json.dumps(dict(variant=variant, source=str(source),
        production_hashes=baseline, rom_sha256=sha256((output / 'pokecrystal-dex-options.gbc').read_bytes())),
        indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=('palette', 'reveal', 'combined', 'cursor'), default='combined')
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--battery', type=Path)
    args = parser.parse_args()
    if args.prepare and args.battery is None:
        parser.error('--prepare requires an isolated --battery fixture')
    build(args.source.resolve(), args.output.resolve(), min(args.jobs, 8), args.variant)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.battery.resolve())
        shutil.copy2(args.output / 'pokecrystal-dex-options.sav', args.output / 'pokecrystal-dex-search.sav')


if __name__ == '__main__':
    main()
