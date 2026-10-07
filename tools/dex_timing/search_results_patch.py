"""Isolated Results renderer patch, leaving production source untouched."""
from pathlib import Path
import re
import shutil

from build_dex_options_prototype import replace


ALPHABETICAL_TYPES = ('BUG', 'DARK', 'DRAGON', 'ELECTRIC', 'FAIRY', 'FIGHTING',
                     'FIRE', 'FLYING', 'GHOST', 'GRASS', 'GROUND', 'ICE',
                     'NORMAL', 'POISON', 'PSYCHIC_TYPE', 'ROCK', 'STEEL', 'WATER')


def patch(candidate, root):
    shutil.copy2(root / 'tools/dex_timing/probes/pokedex_search_results.asm',
                 candidate / 'engine/pokedex/pokedex_search_results.asm')
    replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/pokedex_search.asm"',
            'INCLUDE "engine/pokedex/pokedex_search.asm"\n'
            'INCLUDE "engine/pokedex/pokedex_search_results.asm"')
    table = candidate / 'data/types/search_types.asm'
    text = table.read_text()
    entries = iter(ALPHABETICAL_TYPES)
    text = re.sub(r'(?m)^\s*db \w+\s*$', lambda _: '\tdb ' + next(entries), text)
    table.write_text(text)
    strings = candidate / 'data/types/search_strings.asm'
    text = strings.read_text()
    choices = re.findall(r'^\s*db "([^"]+)"', text, re.M)
    original = re.findall(r'^\s*db (\w+)\s*$', (root / 'data/types/search_types.asm').read_text(), re.M)
    labels = dict(zip(original, choices[1:]))
    replacement = iter([choices[0]] + [labels[name] for name in ALPHABETICAL_TYPES])
    text = re.sub(r'(?m)^\s*db "[^"]+"', lambda _: '\tdb "' + next(replacement) + '"', text)
    strings.write_text(text)
    dex = candidate / 'engine/pokedex/pokedex.asm'
    text = dex.read_text()
    text = text.replace('ld a, NORMAL + 1', 'ld a, 1 ; Bug starts the alphabetical selector')
    old = 'Pokedex_DrawSearchScreenBG:\n\tcall Pokedex_FillBackgroundColor2\n'
    if text.count(old) != 1:
        raise ValueError('Search background initializer changed')
    text = text.replace(old, old + '.Header\n\thlcoord 0, 0\n'
                        '\tld a, $31\n\tld bc, 2 * SCREEN_WIDTH\n\tcall ByteFill\n')
    start = text.index('Pokedex_InitSearchResultsScreen:\n')
    end = text.index('Pokedex_UpdateSearchResultsScreen:\n', start)
    text = text[:start] + ('Pokedex_InitSearchResultsScreen:\n'
                          '\tfarcall PokedexResults_Initialize\n'
                          '\tjp Pokedex_IncrementDexPointer\n\n') + text[end:]
    old = ('\tcall Pokedex_UpdateSearchResultsCursorOAM\n\txor a\n'
           '\tldh [hBGMapMode], a\n\tcall Pokedex_PrintListing\n'
           '\tcall Pokedex_SetBGMapMode3\n\tcall Pokedex_ResetBGMapMode\n\tret')
    if text.count(old) != 1:
        raise ValueError('Results scroll body changed')
    text = text.replace(old, '\tfarcall PokedexResults_Scroll\n\tret')
    start = text.index('Pokedex_PrintListing:\n')
    end = text.index('Pokedex_PrintNumberIfOldMode:\n', start)
    names = text[start:end].replace('Pokedex_PrintListing:', 'PokedexResults_PrintNames:')
    names = names.replace('\tjp Pokedex_LoadSelectedMonTiles', '\tret')
    names = names.replace('\tcall Pokedex_PlaceCaughtSymbolIfCaught', '\tinc hl')
    text += '\n' + names + '''
PokedexResults_DrawBG:
    call Pokedex_DrawSearchResultsScreenBG
    hlcoord 0, 9
    lb bc, 2, 8
    ld a, $31
    call Pokedex_FillBox
    farcall CGB_PokedexResultsAttributes
    ret
'''
    dex.write_text(text)
    legacy = candidate / 'engine/pokedex/pokedex_legacy.asm'
    with legacy.open('a') as file:
        file.write('\nPokedexResults_GetRowSpecies:\n\tld a, c\n\tjp PokedexLegacy_GetRowSpecies\n')
    cgb = candidate / 'engine/gfx/cgb_layouts.asm'
    with cgb.open('a') as file:
        file.write('''
CGB_PokedexResultsAttributes:
    xor a
    hlcoord 0, 0, wAttrmap
    ld bc, SCREEN_AREA
    call ByteFill
    hlcoord 1, 1, wAttrmap
    lb bc, 7, 7
    ld a, 1
    call FillBoxCGB
    ret

CGB_PokedexResultsStagePalettes:
    call ResetBGPals
    ld hl, PokedexUIPalette
    ld de, wBGPals1 palette 0
    call LoadHLPaletteIntoDE
    call CGB_PokedexLoadFrontpicPalette
    ld hl, PokedexListCursorPalette
    ld de, wOBPals1 palette 0
    call LoadHLPaletteIntoDE
    ld hl, PokedexListCaughtBallPalette
    ld de, wOBPals1 palette 1
    jp LoadHLPaletteIntoDE
''')
