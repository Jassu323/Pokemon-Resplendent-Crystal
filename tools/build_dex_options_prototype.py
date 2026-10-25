"""Build private Modern/Legacy Listing Options popups, never production."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.cold_listing import ROOT
from dex_timing.assets import sha256
from pokedex_sort_assets import compile_tables


def replace(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f'Expected exactly one patch anchor in {path}: {old!r}')
    path.write_text(text.replace(old, new))


def build(output, jobs, relink=False, without_records=False):
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Prototype outputs must be inside build/')
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / 'candidate'
    hashes = {s: sha256((ROOT / f'pokecrystal.{s}').read_bytes()) for s in ('gbc', 'sym', 'map')}
    if not relink:
        if candidate.exists():
            raise ValueError('Use a fresh output directory or --relink')
        paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                         '--exclude-standard'], cwd=ROOT).decode().split('\0')
        for name in dict.fromkeys(paths):
            source = ROOT / name
            if name and source.is_file():
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
        dex = candidate / 'engine/pokedex/pokedex.asm'
        replace(dex, '\tconst DEXSTATE_EXIT\n', '\tconst DEXSTATE_EXIT\n\tconst DEXSTATE_POPOVER\n')
        replace(dex, '\tdw Pokedex_Exit\n', '\tdw Pokedex_Exit\n\tdw Pokedex_UpdatePopover\n')
        replace(dex, '\nPokedex_IncrementDexPointer:',
                '\nPokedex_UpdatePopover:\n\tfarcall PokedexPopover_Update\n\tret\n\nPokedex_IncrementDexPointer:')
        # Empty Alphabet has no first word. Resolve a valid unseen placeholder
        # instead of passing its $ffff terminator into the species-ID allocator.
        replace(dex, 'Pokedex_GetSelectedMon:\n',
                'Pokedex_GetSelectedMon:\n\tld hl, wDexListingEnd\n\tld a, [hli]\n'
                '\tor [hl]\n\tjr nz, .nonempty\n\tld hl, CHIKORITA\n'
                '\tjp Pokedex_ResolveSpeciesIndex\n.nonempty\n')
        replace(dex, '\tpush hl\n\tcall GetPokemonIDFromIndex\n\tld l, LOCKED_MON_ID_DEX_SELECTED',
                'Pokedex_ResolveSpeciesIndex:\n\tpush hl\n\tcall GetPokemonIDFromIndex\n'
                '\tld l, LOCKED_MON_ID_DEX_SELECTED')
        replace(dex, '''
.start
	call Pokedex_StopGridIconAnimation
	call Pokedex_BlackOutBG
	ld a, DEXSTATE_SEARCH_SCR
	ld [wJumptableIndex], a
	xor a
	ldh [hSCX], a
	ld a, $a7
	ldh [hWX], a
	call DelayFrame
	ret
''', '\n.start\n\tfarcall PokedexPopover_Open\n\tret\n')
        replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/pokedex_legacy.asm"',
                'INCLUDE "engine/pokedex/pokedex_legacy.asm"\nINCLUDE "engine/pokedex/pokedex_popover.asm"')
        (candidate / 'engine/pokedex/order.asm').write_text(
            'Pokedex_OrderMonsByMode:\n\tfarcall PokedexPopover_OrderMons\n\tret\n'
            'Pokedex_ABCMode:\n\tld a, [wCurDexMode]\n\tpush af\n\tld a, DEXMODE_ABC\n'
            '\tld [wCurDexMode], a\n\tfarcall PokedexPopover_OrderMons\n'
            '\tpop af\n\tld [wCurDexMode], a\n\tret\n')
        three = candidate / 'engine/pokedex/pokedex_3.asm'
        # VBlank cannot use FarCall's shared scratch while interrupting a farcall.
        replace(three, 'Pokedex_VBlankDispatch::\n', '''Pokedex_VBlankDispatch::
    ld a, [wJumptableIndex]
    cp DEXSTATE_POPOVER
    jr nz, .ordinary
    call PokedexPopover_VBlank
    scf
    ret
.ordinary
''')
        replace(three, 'Pokedex_UploadPendingGridCacheRow:\n', '''Pokedex_UploadPendingGridCacheRow:
    ld a, [wJumptableIndex]
    cp DEXSTATE_POPOVER
    jr nz, .ordinary
    farcall PokedexPopover_StageCacheRow
    ret c
.ordinary
''')
    if 'SECTION "bank77", ROMX' in (candidate / 'main.asm').read_text():
        replace(candidate / 'main.asm', 'SECTION "bank77", ROMX',
                'SECTION FRAGMENT "bank77", ROMX')
    source = (ROOT / 'tools/dex_timing/probes/pokedex_popover.asm').read_text()
    if without_records:
        source = 'DEF DEX_SORT_WITHOUT_RECORDS EQU 1\n' + source
    (candidate / 'engine/pokedex/pokedex_popover.asm').write_text(source)
    tables, manifest = compile_tables(candidate, records=not without_records)
    manifest['records'] = not without_records
    manifest['changed_sort_cursor'] = 'beginning'
    manifest['presentations'] = ['modern', 'legacy']
    manifest['modern_sort_shift_px'] = 3
    generated = candidate / 'build/dex-sort-assets'
    generated.mkdir(parents=True, exist_ok=True)
    (generated / 'tables.asm').write_text(tables)
    (output / 'sort-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in hashes:
        shutil.copy2(candidate / f'pokecrystal.{suffix}', output / f'pokecrystal-dex-options.{suffix}')
        if sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()) != hashes[suffix]:
            raise ValueError('Production output changed')
    (output / 'production-hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=10)
    parser.add_argument('--relink', action='store_true')
    parser.add_argument('--without-records', action='store_true')
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs, args.relink, args.without_records)


if __name__ == '__main__':
    main()
