"""Pin the accepted Moves cartridge and build a private persistence-only owner."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from build_dex_options_prototype import replace
from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT
from move_discovery_assets import seed_records, move_bitmap


STEM = 'pokecrystal-dex-moves-persistence'


def publish_copy(source, target):
    temporary = target.with_name('.' + target.name + '.new')
    shutil.copy2(source, temporary)
    temporary.replace(target)


def rollback(source, target):
    target.mkdir(parents=True, exist_ok=False)
    stem = 'pokecrystal-dex-moves-mode'
    files = [source / f'{stem}.{suffix}' for suffix in ('gbc', 'sym', 'map', 'sav')]
    files += [source / name for name in ('moves-mode-manifest.json', 'alignment-qualification.json')]
    for path in files:
        shutil.copy2(path, target / path.name)
    archive = target / 'accepted-candidate.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(source / 'candidate', arcname='candidate')
    hashes = {path.name: sha256((target / path.name).read_bytes()) for path in files}
    hashes[archive.name] = sha256(archive.read_bytes())
    pin = dict(status='safe rollback before discovery persistence', source=str(source),
               files=hashes, accepted_qualification='5684 native cases / 42 host tests',
               production_promotion=False)
    (target / 'rollback.json').write_text(json.dumps(pin, indent=2) + '\n')
    return pin


def build(source, output, pin_dir, jobs=8, relink=False):
    for path in (source, output, pin_dir):
        if not path.is_relative_to(ROOT / 'build'):
            raise ValueError('Use private build paths')
    protected = {str(ROOT / f'pokecrystal.{s}'): sha256((ROOT / f'pokecrystal.{s}').read_bytes())
                 for s in ('gbc', 'sym', 'map')}
    protected.update({str(source / f'pokecrystal-dex-moves-mode.{s}'):
                      sha256((source / f'pokecrystal-dex-moves-mode.{s}').read_bytes())
                      for s in ('gbc', 'sym', 'map', 'sav')})
    candidate = output / 'candidate'
    if not relink:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        rollback(source, pin_dir)
        shutil.copytree(source / 'candidate', candidate)
        replace(candidate / 'ram/wram.asm', 'SECTION "Bug Contest WRAM", WRAMX, BANK[2]',
                'SECTION "Move Discovery Flags", WRAMX, BANK[2]\n'
                'wMoveDiscoverySeen:: ds 64\n'
                'wMoveDiscoveryStatus:: db\n'
                'wMoveDiscoveryWriteBlocked:: db\n'
                'wMoveDiscoveryEnd::\n\n'
                'SECTION "Bug Contest WRAM", WRAMX, BANK[2]')
        replace(candidate / 'layout.link', '\t"16-bit WRAM tables"\nWRAMX 3',
                '\t"16-bit WRAM tables"\n\t"Move Discovery Flags"\nWRAMX 3')
        for prefix in ('s', 'sBackup'):
            replace(candidate / 'ram/sram.asm', prefix + 'SaveDataEnd::\n\n\tds $88',
                    prefix + 'SaveDataEnd::\n\n' + prefix + 'MoveDiscovery:: ds 72\n'
                    '\tds $88 - 72')
        replace(candidate / 'engine/menus/intro_menu.asm',
                '\tld bc, wMoveIndexTableEnd - wMoveIndexTable\n\tcall ByteFill\n',
                '\tld bc, wMoveIndexTableEnd - wMoveIndexTable\n\tcall ByteFill\n'
                '\tld hl, wMoveDiscoverySeen\n'
                '\tld bc, wMoveDiscoveryEnd - wMoveDiscoverySeen\n\tcall ByteFill\n')
        save = candidate / 'engine/menus/save.asm'
        for prefix, helper in (('s', 'Primary'), ('sBackup', 'Backup')):
            replace(save, '\tcall Checksum\n\tld a, e\n\tld [' + prefix + 'Checksum + 0], a',
                    '\tcall Checksum\n\tpush de\n\tfarcall MoveDiscovery_Save' + helper +
                    '\n\tpop de\n\tld a, e\n\tld [' + prefix + 'Checksum + 0], a')
        replace(save, 'TryLoadSaveFile:\n\tcall VerifyChecksum',
                'TryLoadSaveFile:\n\tfarcall MoveDiscovery_Clear\n\tcall VerifyChecksum')
        replace(save, '\tcall LoadIndexTables\n\tcall LoadBox\n',
                '\tcall LoadIndexTables\n\tfarcall MoveDiscovery_LoadPrimary\n\tcall LoadBox\n')
        replace(save, '\tcall LoadBackupIndexTables\n\tcall LoadBox\n',
                '\tcall LoadBackupIndexTables\n\tfarcall MoveDiscovery_LoadBackup\n\tcall LoadBox\n')
        replace(save, 'ErasePreviousSave:\n\tcall EraseBoxes',
                'ErasePreviousSave:\n\tfarcall MoveDiscovery_Invalidate\n\tcall EraseBoxes')
        replace(candidate / 'main.asm', 'INCLUDE "engine/menus/save.asm"',
                'INCLUDE "engine/menus/save.asm"\nINCLUDE "engine/pokedex/move_discovery.asm"')
    module = candidate / 'engine/pokedex/pokedex_moves_mode.asm'
    text = (source / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
    text = text.replace('; Visual-only owner. Discovery and save storage are deliberately deferred.',
                        '; Persistence owner. Gameplay discovery hooks are deliberately deferred.')
    text = text.replace('DEF wMovesModeFont       EQU $dc00',
                        'DEF wMovesModeSeenSnapshot EQUS "wPokedexInfoGFX + 36 tiles"\n'
                        'ASSERT wMovesModeBorderGFX + 21 tiles <= wMovesModeSeenSnapshot\n'
                        'ASSERT wMovesModeSeenSnapshot + 64 <= wPokedexInfoGFX + 40 tiles\n'
                        'DEF wMovesModeFont       EQU $dc00')
    text = text.replace('    farcall Pokedex_CancelAnimationPrefetch\n',
                        '    farcall Pokedex_CancelAnimationPrefetch\n'
                        '    call PokedexMovesMode_SnapshotSeen\n', 1)
    start, end = text.index('PokedexMovesMode_IsSeen:'), text.index('PokedexMovesMode_Draw:')
    query = text[start:end]
    query = query.replace('IF DEF(DEX_MOVES_MODE_UNKNOWN)\n', '')
    query = query.replace('PokedexMovesModeSeenFixture', 'wMovesModeSeenSnapshot')
    query = query.replace('ELSE\n    scf\n    ret\nENDC\n', '')
    snapshot = ('PokedexMovesMode_SnapshotSeen:\n'
                '    ; Gameplay is paused while this owner is active. Refresh on every entry.\n'
                '    ld hl, wMoveDiscoverySeen\n'
                '    ld de, wMovesModeSeenSnapshot\n'
                '    ld b, 64\n'
                '.copy\n'
                '    ld a, BANK(wMoveDiscoverySeen)\n'
                '    ldh [rSVBK], a\n'
                '    ld a, [hli]\n'
                '    ld c, a\n'
                '    ld a, BANK(wPokedexInfoGFX)\n'
                '    ldh [rSVBK], a\n'
                '    ld a, c\n'
                '    ld [de], a\n'
                '    inc de\n'
                '    dec b\n'
                '    jr nz, .copy\n'
                '    ret\n\n')
    module.write_text(text[:start] + query + snapshot + text[end:])
    shutil.copy2(ROOT / 'tools/dex_timing/probes/move_discovery.asm',
                 candidate / 'engine/pokedex/move_discovery.asm')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-mode', 'pokecrystal-dex-options', 'pokecrystal-dex-search'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    symbols = read_symbols(output / f'{STEM}.sym')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    original = (source / 'pokecrystal-dex-moves-mode.sav').read_bytes()
    (output / 'legacy-input.sav').write_bytes(original)
    all_seen = move_bitmap(range(1, len(manifest['moves']) + 1))
    (output / 'all-seen-tests.sav').write_bytes(seed_records(original, symbols, all_seen))
    review_names = {name.casefold() for name in
                    ('Tackle', 'Growl', 'Vine Whip', 'Leech Seed', 'PoisonPowder', 'Double-Edge',
                     'Surf', 'Thunderbolt', 'Water Pulse', 'Dragon Dance', 'Caustic', 'Sketch')}
    review_indices = [entry['index'] for entry in manifest['moves']
                      if entry['name'].casefold() in review_names]
    found = {entry['name'].casefold() for entry in manifest['moves'] if entry['index'] in review_indices}
    if found != review_names:
        raise ValueError(f'Missing review moves: {sorted(review_names - found)}')
    review_indices = sorted(set(review_indices + [1, 255, 256, 257, 333] +
                                manifest['orders'][0][:5] + manifest['orders'][1][:3]))
    (output / f'{STEM}.sav').write_bytes(seed_records(original, symbols, move_bitmap(review_indices)))
    shutil.copy2(source / 'sort-manifest.json', output / 'sort-manifest.json')
    manifest.update(source=str(source), fixture='all_seen', rollback=str(pin_dir), stem=STEM,
                    persistence_stage=1, protected_inputs=protected,
                    review_seen=review_indices, event_hooks=False, legacy_bootstrap=False,
                    egg_policy='at hatch', production_hashes={suffix: protected[str(ROOT / f'pokecrystal.{suffix}')]
                                                             for suffix in ('gbc', 'sym', 'map')},
                    rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()))
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise RuntimeError('A protected input changed')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rollback', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--relink', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    manifest = build(args.source.resolve(), args.output.resolve(), args.rollback.resolve(),
                     args.jobs, args.relink)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.output.resolve() / 'all-seen-tests.sav')
    print(json.dumps({key: manifest[key] for key in ('stem', 'rom_sha256', 'review_seen')}))


if __name__ == '__main__':
    main()
