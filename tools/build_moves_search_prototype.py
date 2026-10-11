"""Add temporary Moves search over the protected sort-remembrance prototype."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from build_move_discovery_prototype import publish_copy
from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT

STEM = 'pokecrystal-dex-moves-search'


def replace_routine(text, start, end, replacement):
    first, last = text.index(start + ':'), text.index(end + ':')
    return text[:first] + replacement + '\n\n' + text[last:]


def repair_visual_owners(candidate, text):
    load = '''    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld de, TMHMCaseCategoryIconGFX
    ld hl, vTiles3 tile MOVES_MODE_CATEGORY_TILE
    lb bc, BANK(TMHMCaseCategoryIconGFX), 6
    call Get2bpp
    pop af
    ldh [rVBK], a
'''
    if text.count(load) != 1:
        raise AssertionError('Category graphics initialization changed')
    text = text.replace(load, '    call PokedexMovesMode_LoadCategoryGFX\n', 1)
    text = text.replace('PokedexMovesMode_LoadScrollbarGFX:',
                        'PokedexMovesMode_LoadCategoryGFX:\n' + load + '    ret\n\n'
                        'PokedexMovesMode_LoadScrollbarGFX:', 1)
    text = text.replace('PokedexMovesMode_PrepareIcons:',
                        'PokedexMovesMode_AlignedIcons:\nPokedexMovesMode_PrepareIcons:', 1)
    text = text.replace('    ld d, 24\n    ld e, 10\n', '    ld d, 24\n    ld e, 11\n', 1)
    text = text.replace('PokedexMovesMode_DrawPopupFrame:\n',
                        'PokedexMovesMode_DrawPopupFrame:\n'
                        '    hlcoord 7, 3\n    lb bc, 3, 11\n    ld a, $32\n'
                        '    call FillBoxWithByte\n'
                        '    hlcoord 7, 3, wAttrmap\n    lb bc, 3, 11\n    xor a\n'
                        '    call FillBoxWithByte\n', 1)
    text = text.replace('    ld hl, String_SELECT_MODE\n    decoord 1, 17\n    ld bc, 18\n'
                        '    ld a, BANK(String_SELECT_MODE)\n    call FarCopyBytes\n',
                        '    call PokedexMovesSearch_DrawCompactFooter\n', 1)
    dex = candidate / 'engine/pokedex/pokedex.asm'
    original = dex.read_text()
    bg = original[original.index('Pokedex_DrawSearchScreenBG:'):original.index('Pokedex_DrawSearchResultsScreenBG:')]
    shifted = bg.replace('hlcoord 8, 4', 'hlcoord 7, 4').replace('hlcoord 8, 6', 'hlcoord 7, 6').replace(
        'hlcoord 3, 4', 'hlcoord 2, 4')
    original = original.replace(bg, shifted, 1)
    original = original.replace('dwcoord 2, 4  ; TYPE 1', 'dwcoord 1, 4  ; TYPE 1').replace(
        'dwcoord 2, 6  ; TYPE 2', 'dwcoord 1, 6  ; TYPE 2')
    start, end = original.index('PokedexSearch_DrawFieldText:'), original.index('Pokedex_PlaceTypeString:')
    fields = original[start:end].replace('hlcoord 9, 4', 'hlcoord 8, 4').replace('hlcoord 9, 6', 'hlcoord 8, 6')
    original = original[:start] + fields + original[end:]
    dex.write_text(original)
    search = candidate / 'engine/pokedex/pokedex_search.asm'
    original = search.read_text()
    if 'PokedexSearch_AlignedFields:' not in original:
        original = original.replace('PokedexSearch_DrawFields:',
                                    'PokedexSearch_AlignedFields:\nPokedexSearch_DrawFields:', 1)
    original = original.replace('hlcoord 9, 3', 'hlcoord 8, 3').replace('hlcoord 9, 4', 'hlcoord 8, 4').replace(
        'hlcoord 9, 6', 'hlcoord 8, 6').replace('debgcoord 9, 4', 'debgcoord 8, 4').replace('debgcoord 9, 6', 'debgcoord 8, 6')
    original = original.replace('ld a, 96 ; centered in the existing field: screen x=88',
                                'ld a, 88 ; shifted field: screen x=80').replace('    add 96\n', '    add 88\n')
    search.write_text(original)
    return text


def build(source, output, jobs=4, relink=False):
    if not all(p.is_relative_to(ROOT / 'build') for p in (source, output)):
        raise ValueError('Use private build paths')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    if not manifest.get('moves_sort_memory'):
        raise ValueError('Use the accepted sort-memory prototype')
    protected = dict(manifest['protected_inputs'])
    for path in source.rglob('*'):
        if path.is_file() and (path.suffix in ('.gbc', '.sym', '.map', '.sav') or
                               path.name == 'moves-mode-manifest.json'):
            protected[str(path)] = sha256(path.read_bytes())
    candidate = output / 'candidate'
    if not relink:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(source / 'candidate', candidate)
    for name in ('pokedex_moves_search_left_border', 'pokedex_search_results_footer'):
        shutil.copy2(ROOT / f'gfx/pokedex/{name}.png', candidate / f'gfx/pokedex/{name}.png')
        # Refresh packed graphics even if an edited/copied PNG has an older mtime.
        (candidate / f'gfx/pokedex/{name}.2bpp').unlink(missing_ok=True)
    dex = candidate / 'engine/pokedex/pokedex.asm'
    if not relink and not manifest.get('moves_search'):
        replace(dex, '\tconst DEXSTATE_MOVES_MODE_SORT\n',
                '\tconst DEXSTATE_MOVES_MODE_SORT\n\tconst DEXSTATE_MOVES_OPTIONS\n'
                '\tconst DEXSTATE_MOVES_SEARCH\n\tconst DEXSTATE_MOVES_TEXT_ENTRY\n')
        replace(dex, '\tdw Pokedex_UpdateMovesModeSort\n',
                '\tdw Pokedex_UpdateMovesModeSort\n\tdw Pokedex_UpdateMovesOptions\n'
                '\tdw Pokedex_UpdateMovesSearch\n\tdw Pokedex_UpdateMovesTextEntry\n')
        replace(dex, 'Pokedex_UpdatePopover:\n',
                'Pokedex_UpdateMovesOptions:\n\tfarcall PokedexMovesSearch_OptionsUpdate\n\tret\n'
                'Pokedex_UpdateMovesSearch:\n\tfarcall PokedexMovesSearch_Update\n\tret\n'
                'Pokedex_UpdateMovesTextEntry:\n\tfarcall PokedexMovesSearch_TextUpdate\n\tret\n\n'
                'Pokedex_UpdatePopover:\n')
        replace(candidate / 'engine/pokedex/pokedex_3.asm',
                '    ld a, [wJumptableIndex]\n    sub DEXSTATE_SEARCH_SCR\n',
                '    ld a, [wJumptableIndex]\n    cp DEXSTATE_MOVES_SEARCH\n'
                '    jr z, .moves_search\n    sub DEXSTATE_SEARCH_SCR\n')
        replace(candidate / 'engine/pokedex/pokedex_3.asm',
                '    call PokedexSearch_VBlank\n',
                '.moves_search\n    call PokedexSearch_VBlank\n')
    # Rebuild the search owner from its original base while retaining other owners.
    search_base = Path(manifest['search_rollback']) if manifest.get('moves_search') else source
    text = (search_base / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
    search = (ROOT / 'tools/dex_timing/probes/moves_search.asm').read_text()
    update, extra = search.split('; END REPLACEMENT UPDATE\n', 1)
    text = replace_routine(text, 'PokedexMovesMode_Update', 'PokedexMovesMode_SortUpdate', update)
    text = text.replace('    call PokedexMovesMode_RestoreSort\n',
                        '    call PokedexMovesMode_RestoreSort\n    call PokedexMovesSearch_Reset\n', 1)
    text = text.replace('    add hl, hl\n    ld de, PokedexMovesModeTypeOrder\n',
                        '    ld a, [wMovesSearchActive]\n    and a\n'
                        '    jr z, .regular\n    add hl, hl\n    ld de, wMovesSearchResults\n'
                        '    add hl, de\n    ld a, [hli]\n    ld h, [hl]\n    ld l, a\n    ret\n'
                        '.regular\n    add hl, hl\n    ld de, PokedexMovesModeTypeOrder\n', 1)
    first = text.index('PokedexMovesMode_PageRight:')
    last = text.index('PokedexMovesMode_StorePage:')
    page = text[first:last].replace('    ld de, NUM_ATTACKS - 8\n',
                                   '    push hl\n    call PokedexMovesSearch_MaxScroll\n'
                                   '    ld d, h\n    ld e, l\n    pop hl\n')
    text = text[:first] + page + text[last:]
    text = text.replace('    call PokedexMovesMode_DrawShell\n',
                        '    call PokedexMovesMode_DrawShell\n    call ClearSprites\n', 1)
    text = text.replace('    call PokedexMovesMode_GetMove\n    push hl\n',
                        '    push hl\n    call PokedexMovesSearch_Count\n    ld d, h\n    ld e, l\n'
                        '    pop hl\n    ld a, h\n    cp d\n    jr c, .valid\n'
                        '    jr nz, .rows_done\n    ld a, l\n    cp e\n    jr nc, .rows_done\n'
                        '.valid\n    call PokedexMovesMode_GetMove\n    push hl\n', 1)
    text = text.replace('    call PokedexMovesMode_DrawScrollbar\n',
                        '.rows_done\n    call PokedexMovesMode_DrawScrollbar\n', 1)
    text = text.replace('PokedexMovesMode_DrawSort:\n    ld a, [wMovesModeSort]\n'
                        '    ld [wDexArrowCursorPosIndex], a\n',
                        'PokedexMovesMode_DrawSort:\n    ld a, [wMovesModeSort]\n'
                        '    ld [wDexArrowCursorPosIndex], a\n'
                        '    call PokedexMovesMode_DrawPopupFrame\n'
                        '    call PokedexMovesMode_DrawSortRows\n'
                        '    jp PokedexMovesMode_Publish\n\nPokedexMovesMode_DrawPopupFrame:\n', 1)
    text = text.replace('    call PokedexMovesMode_DrawSortRows\n'
                        '    jp PokedexMovesMode_Publish\n\nPokedexMovesMode_DrawSortRows:',
                        '    ret\n\nPokedexMovesMode_DrawSortRows:', 1)
    text = text.replace('    ld hl, String_SELECT_MODE\n',
                        '    ld a, [wMovesSearchActive]\n    and a\n'
                        '    jr z, .regular_footer\n    call PokedexMovesSearch_DrawFooter\n'
                        '    jr .footer_done\n.regular_footer\n    ld hl, String_SELECT_MODE\n', 1)
    text = text.replace('    hlcoord 19, 0\n', '.footer_done\n    hlcoord 19, 0\n', 1)
    text = text.replace('    ld bc, (NUM_ATTACKS - 8) / 2\n    add hl, bc\n'
                        '    ld de, -(NUM_ATTACKS - 8)\n',
                        '    push hl\n    call PokedexMovesSearch_MaxScroll\n'
                        '    ld a, h\n    or l\n    jr nz, .nonzero\n'
                        '    pop hl\n    ld b, 0\n    jr .position\n.nonzero\n'
                        '    ld b, h\n    ld c, l\n    srl b\n    rr c\n'
                        '    xor a\n    sub l\n    ld e, a\n    ld a, 0\n'
                        '    sbc h\n    ld d, a\n    pop hl\n    add hl, bc\n', 1)
    text = text.replace('    ld a, b\n    add 20\n', '.position\n    ld a, b\n    add 20\n', 1)
    text = repair_visual_owners(candidate, text)
    (candidate / 'engine/pokedex/pokedex_moves_mode.asm').write_text(text + '\n' + extra)
    vblank = candidate / 'engine/pokedex/pokedex_3.asm'
    if '.not_moves_text' not in vblank.read_text():
        replace(vblank, 'Pokedex_VBlankDispatch::\n    ld a, [wJumptableIndex]\n',
                'Pokedex_VBlankDispatch::\n    ld a, [wJumptableIndex]\n'
                '    cp DEXSTATE_MOVES_TEXT_ENTRY\n    jr nz, .not_moves_text\n'
                '    scf\n    ret\n'
                '.not_moves_text\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 4)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-mode', 'pokecrystal-dex-moves-persistence',
                     'pokecrystal-dex-moves-sort-memory', 'pokecrystal-dex-moves-battle-use'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'sparse-review.sav'):
        shutil.copy2(source / name, output / name)
    shutil.copy2(source / (manifest['stem'] + '.sav'), output / f'{STEM}.sav')
    shutil.copy2(source / 'pokecrystal-dex-moves-persistence.sav',
                 output / 'pokecrystal-dex-moves-persistence.sav')
    shutil.copy2(output / f'{STEM}.sav', output / 'pokecrystal-dex-moves-sort-memory.sav')
    shutil.copy2(output / f'{STEM}.sav', output / 'pokecrystal-dex-moves-battle-use.sav')
    (output / 'battle-review').mkdir(exist_ok=True)
    review = output / 'all-seen-review'
    review.mkdir(exist_ok=True)
    shutil.copy2(output / 'all-seen-tests.sav', review / f'{STEM}.sav')
    shutil.copy2(output / f'{STEM}.gbc', review / f'{STEM}.gbc')
    old_symbols = read_symbols(source / (manifest['stem'] + '.sym'))
    symbols = read_symbols(output / f'{STEM}.sym')
    for name, pair in old_symbols.items():
        if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in symbols and pair != symbols[name]:
            raise AssertionError(f'Existing memory location moved: {name}')
    if manifest.get('moves_search_naming_animation'):
        manifest['end_cursor_rollback'] = str(source)
    elif manifest.get('moves_search_form_polish'):
        manifest['text_cursor_rollback'] = str(source)
    elif manifest.get('moves_search_visual_repairs'):
        manifest['form_rollback'] = str(source)
    elif manifest.get('moves_search'):
        key = 'visual_rollback' if manifest.get('moves_search_keyboard') else 'keyboard_rollback'
        manifest[key] = str(source)
        manifest['moves_search_keyboard'] = True
    manifest['moves_search_visual_repairs'] = True
    manifest['moves_search_form_polish'] = True
    manifest['moves_search_naming_animation'] = True
    manifest['moves_search_standard_end'] = True
    manifest.update(source=str(source), moves_search=True, stem=STEM,
                    search_rollback=str(search_base), protected_inputs=protected,
                    rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                    search_assets={name: sha256((ROOT / f'gfx/pokedex/{name}.png').read_bytes())
                                   for name in ('pokedex_moves_search_left_border', 'pokedex_search_results_footer')})
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'rollback.json').write_text(json.dumps(dict(
        status='protected input prototype; safe rollback before this update',
        source=str(source), files={path: digest for path, digest in protected.items()
                                  if Path(path).is_relative_to(source)}), indent=2) + '\n')
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected input changed: {path}')
    return {k: manifest[k] for k in ('stem', 'rom_sha256', 'search_rollback')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--relink', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.source.resolve(), args.output.resolve(), args.jobs, args.relink)))
