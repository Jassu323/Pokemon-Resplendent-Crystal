"""Build stage-two discovery hooks over the accepted private scrollbar owner."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_options_prototype import replace
from build_move_discovery_prototype import publish_copy
from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT

STEM = 'pokecrystal-dex-moves-acquisition'


def hook(name):
    return f'\tmove_discovery_hook MoveDiscovery_{name}\n'


def build(source, output, jobs=6, relink=False):
    if not all(p.is_relative_to(ROOT / 'build') for p in (source, output)):
        raise ValueError('Use private build paths')
    manifest = json.loads((source / 'moves-mode-manifest.json').read_text())
    protected = dict(manifest['protected_inputs'])
    for p in [*(ROOT / f'pokecrystal.{s}' for s in ('gbc', 'sym', 'map')),
              *(source / f'pokecrystal-dex-moves-scrollbar.{s}' for s in ('gbc', 'sym', 'map', 'sav'))]:
        protected[str(p)] = sha256(p.read_bytes())
    candidate = output / 'candidate'
    if not relink:
        if output.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(source / 'candidate', candidate)
    else:
        # Reapply only our prototype sources, never another checkout's changes.
        for name in ('macros/farcall.asm', 'engine/pokemon/learn.asm', 'engine/pokemon/move_mon.asm',
                     'engine/items/item_effects.asm', 'engine/events/npc_trade.asm',
                     'engine/events/dratini.asm', 'engine/pokemon/caught_data.asm',
                     'engine/pokemon/breeding.asm', 'engine/menus/save.asm', 'main.asm'):
            shutil.copy2(source / 'candidate' / name, candidate / name)
    macro = candidate / 'macros/farcall.asm'
    macro.write_text(macro.read_text() + '\n; Discovery hooks preserve caller flags and pointers.\n'
                     'MACRO move_discovery_hook\n\tpush af\n\tpush hl\n'
                     '\tfarcall \\1\n\tpop hl\n\tpop af\nENDM\n')
    replace(candidate / 'main.asm', 'INCLUDE "engine/pokedex/move_discovery.asm"',
            'INCLUDE "engine/pokedex/move_discovery.asm"\n'
            'INCLUDE "engine/pokedex/move_acquisition.asm"')
    shutil.copy2(ROOT / 'tools/dex_timing/probes/move_acquisition.asm',
                 candidate / 'engine/pokedex/move_acquisition.asm')
    text = (ROOT / 'tools/dex_timing/probes/move_discovery.asm').read_text()
    for copy in ('Primary', 'Backup'):
        text = text.replace(f'    jp MoveDiscovery_Repair{copy}\n', '    ret\n', 1)
    (candidate / 'engine/pokedex/move_discovery.asm').write_text(text)
    save = candidate / 'engine/menus/save.asm'
    for copy in ('Primary', 'Backup'):
        replace(save, f'\tfarcall MoveDiscovery_Load{copy}\n\tcall LoadBox\n',
                f'\tfarcall MoveDiscovery_Load{copy}\n\tcall LoadBox\n' + hook('Bootstrap' + copy))
    replace(candidate / 'engine/pokemon/learn.asm', '.learned\n\tld hl, LearnedMoveText',
            '.learned\n' + hook('Learned') + '\tld hl, LearnedMoveText')
    mon = candidate / 'engine/pokemon/move_mon.asm'
    replace(mon, '.skip_nickname\n\tpop bc\n\tpop de\n\tld a, b',
            '.skip_nickname\n\tpop bc\n\tpop de\n' + hook('Gift') + '\tld a, b')
    replace(mon, '\tldh a, [hMultiplicand + 2]\n\tld [hl], a\n\tand a\n\tret\n\nGetLastPartyMon:',
            '\tldh a, [hMultiplicand + 2]\n\tld [hl], a\n' + hook('LastParty') +
            '\tand a\n\tret\n\nGetLastPartyMon:')
    items = candidate / 'engine/items/item_effects.asm'
    replace(items, '\tpredef TryAddMonToParty\n\n\tfarcall SetCaughtData',
            '\tpredef TryAddMonToParty\n\tjr nc, .discovery_party_done\n' + hook('LastParty') +
            '.discovery_party_done\n\n\tfarcall SetCaughtData')
    replace(items, '\tpredef SendMonIntoBox\n\n\tfarcall SetBoxMonCaughtData',
            '\tpredef SendMonIntoBox\n\tjr nc, .discovery_box_done\n' + hook('FirstBox') +
            '.discovery_box_done\n\n\tfarcall SetBoxMonCaughtData')
    replace(candidate / 'engine/events/npc_trade.asm', '\tfarcall ComputeNPCTrademonStats\n',
            '\tfarcall ComputeNPCTrademonStats\n' + hook('LastParty'))
    dratini = candidate / 'engine/events/dratini.asm'
    replace(dratini, '\tld [de], a ; give the Pokémon the new move\n',
            '\tld [de], a ; give the Pokémon the new move\n'
            '\tpush bc\n\tld c, a\n' + hook('MarkLiveID') + '\tpop bc\n')
    contest = candidate / 'engine/pokemon/caught_data.asm'
    replace(contest, '\tld [hl], a\n\tfarcall BugContest_ClearContestMon\n\txor a ; BUGCONTEST_CAUGHT_MON',
            '\tld [hl], a\n' + hook('LastParty') +
            '\tfarcall BugContest_ClearContestMon\n\txor a ; BUGCONTEST_CAUGHT_MON')
    replace(contest, '\tcall CloseSRAM\n\n.BoxFull:',
            '\tcall CloseSRAM\n' + hook('FirstBox') + '\n.BoxFull:')
    replace(candidate / 'engine/pokemon/breeding.asm', '\tld [de], a\n\tld [wNamedObjectIndex], a\n\tld [wCurSpecies], a',
            '\tld [de], a\n' + hook('CurrentParty') + '\tld [wNamedObjectIndex], a\n\tld [wCurSpecies], a')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', f'-j{min(jobs, 8)}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        for stem in (STEM, 'pokecrystal-dex-moves-mode', 'pokecrystal-dex-moves-persistence',
                     'pokecrystal-dex-options', 'pokecrystal-dex-search'):
            publish_copy(candidate / f'pokecrystal.{suffix}', output / f'{stem}.{suffix}')
    for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'sparse-review.sav'):
        shutil.copy2(source / name, output / name)
    for stem in (STEM, 'pokecrystal-dex-moves-persistence'):
        shutil.copy2(source / 'sparse-review.sav', output / f'{stem}.sav')
    symbols = read_symbols(output / f'{STEM}.sym')
    manifest.update(source=str(source), stem=STEM, persistence_stage=2,
                    acquisition_hooks=True, battle_use_hooks=False, legacy_bootstrap=True,
                    protected_inputs=protected, rom_sha256=sha256((output / f'{STEM}.gbc').read_bytes()))
    for name, pair in read_symbols(source / 'pokecrystal-dex-moves-mode.sym').items():
        if name.startswith(('s', 'w')) and pair[1] >= 0xa000 and name in symbols and symbols[name] != pair:
            raise AssertionError(f'Memory location moved: {name}')
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
    args = parser.parse_args()
    result = build(args.source.resolve(), args.output.resolve(), args.jobs, args.relink)
    if args.prepare:
        from dex_timing.listing_options import prepare
        prepare(args.output.resolve(), args.output.resolve() / 'all-seen-tests.sav')
    print(json.dumps({k: result[k] for k in ('stem', 'rom_sha256', 'persistence_stage')}))


if __name__ == '__main__':
    main()
