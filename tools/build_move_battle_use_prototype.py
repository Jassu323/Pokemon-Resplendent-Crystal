"""Build battle-use discovery over the accepted stage-two private owner."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from build_move_discovery_prototype import publish_copy
from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT

STEM = 'pokecrystal-dex-moves-battle-use'


def build(source, output, jobs=6, relink=False, grant_struggle=False):
    if not all(p.is_relative_to(ROOT / 'build') for p in (source, output)):
        raise ValueError('Use private build paths')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    if manifest['persistence_stage'] != 2 or not manifest['acquisition_hooks']:
        raise ValueError('Start with the accepted acquisition/learning prototype')
    protected = dict(manifest['protected_inputs'])
    for suffix in ('gbc', 'sym', 'map', 'sav'):
        path = source / f'pokecrystal-dex-moves-acquisition.{suffix}'
        protected[str(path)] = sha256(path.read_bytes())
    candidate = output / 'candidate'
    files = ('main.asm', 'engine/battle/core.asm', 'engine/battle/effect_commands.asm',
             'engine/battle/used_move_text.asm', 'maps/MrPokemonsHouse.asm')
    if relink:
        for name in files:
            shutil.copy2(source / 'candidate' / name, candidate / name)
    else:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(source / 'candidate', candidate)
    replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/move_acquisition.asm"',
            'INCLUDE "engine/pokedex/move_acquisition.asm"\n'
            'INCLUDE "engine/pokedex/move_battle_use.asm"')
    shutil.copy2(ROOT / 'tools/dex_timing/probes/move_battle_use.asm',
                 candidate / 'engine/pokedex/move_battle_use.asm')
    hook = '\tmove_discovery_hook MoveDiscovery_BattleUse\n'
    replace(candidate / 'engine/battle/used_move_text.asm',
            '\tcall BattleTextbox\n\tjp WaitBGMap\n',
            '\tcall BattleTextbox\n' + hook + '\tjp WaitBGMap\n')
    replace(candidate / 'engine/battle/effect_commands.asm',
            '.awake\n\tld a, BATTLE_VARS_SUBSTATUS3\n\tcall GetBattleVarAddr\n\tset SUBSTATUS_CHARGED, [hl]\n',
            '.awake\n\tld a, BATTLE_VARS_SUBSTATUS3\n\tcall GetBattleVarAddr\n\tset SUBSTATUS_CHARGED, [hl]\n' + hook)
    replace(candidate / 'engine/battle/core.asm', 'Battle_PlayFocusPunchTightenAnim:\n',
            'Battle_PlayFocusPunchTightenAnim:\n\tfarcall MoveDiscovery_BattleUse\n')
    if grant_struggle:
        replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/move_battle_use.asm"',
                'INCLUDE "engine/pokedex/move_battle_use.asm"\n'
                'INCLUDE "engine/pokedex/move_pokedex_gift.asm"')
        shutil.copy2(ROOT / 'tools/dex_timing/probes/move_pokedex_gift.asm',
                     candidate / 'engine/pokedex/move_pokedex_gift.asm')
        replace(candidate / 'maps/MrPokemonsHouse.asm', '\tsetflag ENGINE_POKEDEX\n',
                '.ReceivePokedex:\n\tsetflag ENGINE_POKEDEX\n'
                '\tcallasm MoveDiscovery_PokedexGift\n.PokedexRecorded:\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-acquisition', 'pokecrystal-dex-moves-mode',
                     'pokecrystal-dex-moves-persistence', 'pokecrystal-dex-options', 'pokecrystal-dex-search'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'sparse-review.sav'):
        shutil.copy2(source / name, output / name)
    shutil.copy2(source / 'pokecrystal-dex-moves-acquisition.sav', output / f'{STEM}.sav')
    shutil.copy2(source / 'sparse-review.sav', output / 'pokecrystal-dex-moves-persistence.sav')
    symbols = read_symbols(output / f'{STEM}.sym')
    for name, pair in read_symbols(source / 'pokecrystal-dex-moves-mode.sym').items():
        if name.startswith(('s', 'w')) and pair[1] >= 0xa000 and name in symbols and symbols[name] != pair:
            raise AssertionError(f'Memory location moved: {name}')
    manifest.update(source=str(source), stem=STEM, persistence_stage=3, battle_use_hooks=True,
                    protected_inputs=protected, rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()))
    if grant_struggle:
        manifest['struggle_at_pokedex'] = True
    (output / 'moves-mode-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected input changed: {path}')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--relink', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--grant-struggle', action='store_true')
    args = parser.parse_args()
    result = build(args.source.resolve(), args.output.resolve(), args.jobs, args.relink,
                   args.grant_struggle)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.output.resolve() / 'all-seen-tests.sav')
    print(json.dumps({k: result[k] for k in ('stem', 'rom_sha256', 'persistence_stage')}))


if __name__ == '__main__':
    main()
