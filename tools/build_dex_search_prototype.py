"""Build ranked type Search and compact selectors in an isolated candidate."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from dex_timing.assets import sha256
from dex_timing.cold_listing import ROOT


def build(source, output, jobs, results=False):
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh private build output')
    baseline = {suffix: sha256((ROOT / f'pokecrystal.{suffix}').read_bytes())
                for suffix in ('gbc', 'sym', 'map')}
    candidate = output / 'candidate'
    shutil.copytree(source / 'candidate', candidate)
    module = ROOT / 'tools/dex_timing/probes/pokedex_search.asm'
    shutil.copy2(module, candidate / 'engine/pokedex/pokedex_search.asm')
    replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/pokedex_popover.asm"',
            'INCLUDE "engine/pokedex/pokedex_popover.asm"\nINCLUDE "engine/pokedex/pokedex_search.asm"')
    replace(candidate / 'engine/pokedex/pokedex_info.asm', 'PokedexInfo_StageTypePalettes:\n',
            'PokedexInfo_CopyCompactTypeTilesByC:\n\tld a, c\n'
            '\tjp PokedexInfo_LoadTypeSprites.CopyType\n\nPokedexInfo_StageTypePalettes:\n')
    dex = candidate / 'engine/pokedex/pokedex.asm'
    replace(dex, 'Pokedex_InitSearchScreen:\n',
            'Pokedex_InitSearchScreen:\n\tfarcall PokedexSearch_Initialize\n')
    text = dex.read_text()
    start, end = text.index('Pokedex_PlaceSearchScreenTypeStrings:\n'), text.index('Pokedex_PlaceTypeString:\n')
    text = text[:start] + ('Pokedex_PlaceSearchScreenTypeStrings:\n'
            '\tfarcall PokedexSearch_DrawFields\n\tfarcall PokedexSearch_UpdateIcons\n'
            '\tld a, 1\n\tldh [hBGMapMode], a\n\tret\n\n'
            'PokedexSearch_DrawFieldText:\n\tldh a, [hCGB]\n\tand a\n\tjr nz, .second\n'
            '\tld a, [wDexSearchMonType1]\n\thlcoord 9, 4\n\tcall Pokedex_PlaceTypeString\n'
            '.second\n\tldh a, [hCGB]\n\tand a\n\tjr z, .text\n'
            '\tld a, [wDexSearchMonType2]\n\tand a\n\tret nz\n'
            '.text\n\tld a, [wDexSearchMonType2]\n\thlcoord 9, 6\n'
            '\tjp Pokedex_PlaceTypeString\n\n') + text[end:]
    start, end = text.index('Pokedex_SearchForMons:\n'), text.index('INCLUDE "data/types/search_types.asm"')
    text = text[:start] + ('Pokedex_SearchForMons:\n\tfarcall PokedexSearch_Filter\n\tret\n\n') + text[end:]
    dex.write_text(text)
    for label in ('.cancel', '.MenuAction_Cancel:'):
        replace(dex, label + '\n\tcall Pokedex_BlackOutBG\n\tld a, DEXSTATE_MAIN_SCR\n',
                label + '\n\tfarcall PokedexSearch_Leave\n\tfarcall PokedexListing_BeginMenuTransition\n'
                '\tld a, DEXSTATE_MAIN_SCR\n')
    replace(dex, '\tcall Pokedex_BlackOutBG\n\tld a, DEXSTATE_SEARCH_RESULTS_SCR\n',
            '\tfarcall PokedexSearch_Leave\n\tfarcall PokedexListing_BeginMenuTransition\n'
            '\tld a, DEXSTATE_SEARCH_RESULTS_SCR\n')
    replace(dex, '\tcall Pokedex_BlackOutBG\n\tcall ClearSprites\n\tfarcall Pokedex_OrderMonsByMode\n',
            '\tfarcall PokedexListing_BeginMenuTransition\n\tfarcall Pokedex_OrderMonsByMode\n')
    replace(candidate / 'engine/pokedex/pokedex_3.asm', 'Pokedex_VBlankDispatch::\n',
            '''Pokedex_VBlankDispatch::
    ld a, [wJumptableIndex]
    sub DEXSTATE_SEARCH_SCR
    cp 2
    jr nc, .not_search
    call PokedexSearch_VBlank
    scf
    ret
.not_search
''')
    if results:
        from dex_timing.search_results_patch import patch
        patch(candidate, ROOT)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in baseline:
        for stem in ('pokecrystal-dex-options', 'pokecrystal-dex-search'):
            shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
        if sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()) != baseline[suffix]:
            raise ValueError('Production output changed')
    shutil.copy2(source / 'sort-manifest.json', output / 'sort-manifest.json')
    (output / 'search-manifest.json').write_text(json.dumps(dict(source=str(source),
        ranking=['both', 'type1_only', 'type2_only'], compact_type_icons=True,
        modern_results=results, alphabetical_types=results,
        results_module_sha256=sha256((ROOT / 'tools/dex_timing/probes/pokedex_search_results.asm').read_bytes()) if results else None,
        results_patch_sha256=sha256((ROOT / 'tools/dex_timing/search_results_patch.py').read_bytes()) if results else None,
        production_hashes=baseline, module_sha256=sha256(module.read_bytes()),
        rom_sha256=sha256((output / 'pokecrystal-dex-search.gbc').read_bytes())), indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--battery', type=Path)
    parser.add_argument('--results', action='store_true')
    args = parser.parse_args()
    if args.prepare and args.battery is None:
        parser.error('--prepare requires an isolated --battery')
    build(args.source.resolve(), args.output.resolve(), min(args.jobs, 8), args.results)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.battery.resolve())
        shutil.copy2(args.output / 'pokecrystal-dex-options.sav', args.output / 'pokecrystal-dex-search.sav')


if __name__ == '__main__':
    main()
