"""Remember Moves sorting over the accepted private discovery prototype."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from build_move_discovery_prototype import publish_copy
from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT

STEM = 'pokecrystal-dex-moves-sort-memory'


def build(source, output, jobs=4):
    if not all(p.is_relative_to(ROOT / 'build') for p in (source, output)):
        raise ValueError('Use private build paths')
    if output.exists():
        raise ValueError('Use a fresh output directory')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    if manifest['persistence_stage'] != 3 or not manifest.get('struggle_at_pokedex'):
        raise ValueError('Start with the current battle-use/Struggle prototype')
    protected = dict(manifest['protected_inputs'])
    for suffix in ('gbc', 'sym', 'map', 'sav'):
        path = source / (manifest['stem'] + '.' + suffix)
        protected[str(path)] = sha256(path.read_bytes())
    for name in ('moves-mode-manifest.json', 'pokedex-gift-qualification.json',
                 'battle-review/' + manifest['stem'] + '.sav'):
        path = source / name
        protected[str(path)] = sha256(path.read_bytes())
    candidate = output / 'candidate'
    shutil.copytree(source / 'candidate', candidate)
    replace(candidate / 'ram/wram.asm',
            'wFarfetchdPosition:: db\n\n\tds 13\n',
            'wFarfetchdPosition:: db\n\n'
            'wLastMovesDexSort:: db ; saved padding; $a0 Type, $a1 Alphabet\n\tds 12\n')
    module = candidate / 'engine/pokedex/pokedex_moves_mode.asm'
    replace(module, '    ld [wPokedexResidentFootprintSpecies], a\n    call ClearSprites\n',
            '    ld [wPokedexResidentFootprintSpecies], a\n'
            '    call PokedexMovesMode_RestoreSort\n    call ClearSprites\n')
    replace(module, '    ld a, [wDexArrowCursorPosIndex]\n    ld hl, wMovesModeSort\n',
            '    ld a, [wDexArrowCursorPosIndex]\n'
            '    call PokedexMovesMode_RememberSort\n    ld hl, wMovesModeSort\n')
    with module.open('a') as stream:
        stream.write('\n' + (ROOT / 'tools/dex_timing/probes/moves_sort_memory.asm').read_text())
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-mode', 'pokecrystal-dex-moves-persistence',
                     'pokecrystal-dex-options', 'pokecrystal-dex-search', 'pokecrystal-dex-moves-battle-use'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'sparse-review.sav'):
        shutil.copy2(source / name, output / name)
    shutil.copy2(output / 'sparse-review.sav', output / 'pokecrystal-dex-moves-persistence.sav')
    shutil.copy2(source / (manifest['stem'] + '.sav'), output / f'{STEM}.sav')
    review = output / 'battle-review'
    review.mkdir()
    shutil.copy2(source / 'battle-review' / (manifest['stem'] + '.sav'), review / f'{STEM}.sav')
    shutil.copy2(output / f'{STEM}.gbc', review / f'{STEM}.gbc')
    old_symbols = read_symbols(source / (manifest['stem'] + '.sym'))
    symbols = read_symbols(output / f'{STEM}.sym')
    for name, pair in old_symbols.items():
        if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in symbols and pair != symbols[name]:
            raise AssertionError(f'Existing memory location moved: {name}')
    if symbols['wLastMovesDexSort'] != (1, 0xd9e3):
        raise AssertionError('Sort preference did not occupy the expected saved padding')
    manifest.update(sort_memory_source=str(source), stem=STEM, moves_sort_memory=True,
                    sort_memory_tag=0xa0, protected_inputs=protected,
                    rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()))
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected input changed: {path}')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    result = build(args.source.resolve(), args.output.resolve(), args.jobs)
    print(json.dumps({k: result[k] for k in ('stem', 'rom_sha256', 'moves_sort_memory')}))


if __name__ == '__main__':
    main()
