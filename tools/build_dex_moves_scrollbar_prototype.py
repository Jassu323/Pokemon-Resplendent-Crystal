"""Add the supplied scrollbar art to a private persistence-stage cartridge."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_move_discovery_prototype import publish_copy
from dex_timing.assets import sha256
from dex_timing.cold_listing import ROOT


STEM = 'pokecrystal-dex-moves-scrollbar'
ART = 'gfx/pokedex/pokedex_moves_scroll_bar_and_borders.png'


def build(source, output, jobs=8, relink=False):
    if not all(path.is_relative_to(ROOT / 'build') for path in (source, output)):
        raise ValueError('Use private build paths')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    if manifest.get('persistence_stage') != 1:
        raise ValueError('The scrollbar trial must retain the persistence stage')
    protected = dict(manifest['protected_inputs'])
    for path in [*(ROOT / f'pokecrystal.{s}' for s in ('gbc', 'sym', 'map')),
                 *(source / f'pokecrystal-dex-moves-persistence.{s}'
                   for s in ('gbc', 'sym', 'map', 'sav'))]:
        protected[str(path)] = sha256(path.read_bytes())
    candidate = output / 'candidate'
    if not relink:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(source / 'candidate', candidate)
    shutil.copy2(ROOT / ART, candidate / ART)
    original = (source / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
    text = (ROOT / 'tools/dex_timing/probes/pokedex_moves_mode.asm').read_text()
    text = text.replace(text.splitlines()[0], original.splitlines()[0], 1)
    start = original.index('DEF wMovesModeSeenSnapshot')
    end = original.index('DEF wMovesModeFont')
    marker = 'DEF MOVES_MODE_CATEGORY_TILE'
    text = text.replace(marker, original[start:end] + marker, 1)
    marker = '    farcall Pokedex_CancelAnimationPrefetch\n'
    text = text.replace(marker, marker + '    call PokedexMovesMode_SnapshotSeen\n', 1)
    start, end = text.index('PokedexMovesMode_IsSeen:'), text.index('PokedexMovesMode_Draw:')
    prior_start, prior_end = original.index('PokedexMovesMode_IsSeen:'), original.index('PokedexMovesMode_Draw:')
    text = text[:start] + original[prior_start:prior_end] + text[end:]
    (candidate / 'engine/pokedex/pokedex_moves_mode.asm').write_text(text)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-mode', 'pokecrystal-dex-moves-persistence',
                     'pokecrystal-dex-options', 'pokecrystal-dex-search'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json'):
        shutil.copy2(source / name, output / name)
    shutil.copy2(source / 'all-seen-tests.sav', output / f'{STEM}.sav')
    shutil.copy2(source / 'pokecrystal-dex-moves-persistence.sav', output / 'sparse-review.sav')
    shutil.copy2(source / 'pokecrystal-dex-moves-persistence.sav',
                 output / 'pokecrystal-dex-moves-persistence.sav')
    manifest.update(source=str(source), stem=STEM, scrollbar=True, protected_inputs=protected,
                    rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()),
                    sort_popup_bounds=[43, 16, 147, 56],
                    manual_save='all moves seeded for visual review',
                    scrollbar_art_sha256=sha256((ROOT / ART).read_bytes()))
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for path, expected in protected.items():
        if sha256(Path(path).read_bytes()) != expected:
            raise AssertionError(f'Protected input changed: {path}')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--relink', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = build(args.source.resolve(), output, args.jobs, args.relink)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(output, output / 'all-seen-tests.sav')
    print(json.dumps({key: manifest[key] for key in ('stem', 'rom_sha256', 'scrollbar')}))


if __name__ == '__main__':
    main()
