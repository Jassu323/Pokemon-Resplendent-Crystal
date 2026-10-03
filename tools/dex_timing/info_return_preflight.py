"""Relink an isolated Info-return relocation prototype from the current tree.

No production assembly, ROM, symbols or battery is modified. Source transforms
are confined to the private checkout and fail if their exact anchors change.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from .assets import sha256
from .cold_listing import ROOT


def transform(path, old, new):
    original = path.read_text()
    if original.count(old) != 1:
        raise ValueError(f'Private build anchor changed: {path}: {old!r}')
    path.write_text(original.replace(old, new))


def build(output, jobs, mode='readback', source=ROOT):
    output = output.resolve()
    source = source.resolve()
    if not output.is_relative_to((ROOT / 'build').resolve()) or output.exists():
        raise ValueError('Use a new output directory under build/')
    if 'PokedexInfo_PreserveReturnPanel' in (source / 'engine/pokedex/pokedex_detail.asm').read_text():
        raise ValueError('Return preservation is already integrated; use --source with the saved preflight baseline')
    production = [source / f'pokecrystal.{suffix}' for suffix in ('gbc', 'sym', 'map')]
    hashes = {str(p): sha256(p.read_bytes()) for p in production}
    output.mkdir(parents=True)
    baseline, candidate = (output / name for name in ('baseline', 'candidate'))
    baseline.mkdir()
    if source == ROOT:
        paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                         '--exclude-standard'], cwd=ROOT).decode().split('\0')
        for name in dict.fromkeys(paths):
            original = source / name
            if name and original.is_file():
                target = baseline / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
        # Generated graphics retain the accepted compression and timing assets.
        shutil.copytree(source / 'gfx', baseline / 'gfx', dirs_exist_ok=True)
    else:
        shutil.copytree(source, baseline, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
    def make(directory, label):
        with (output / f'{label}-build.log').open('w') as log:
            subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=directory,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    make(baseline, 'baseline')
    if sha256((baseline / 'pokecrystal.gbc').read_bytes()) != hashes[str(production[0])]:
        raise ValueError('Fresh source baseline differs from production ROM')
    shutil.copytree(baseline, candidate)
    transform(candidate / 'engine/pokedex/pokedex.asm', '\tconst POKEDEX_OWNER_TRANSITION_INFO\n',
              '\tconst POKEDEX_OWNER_TRANSITION_INFO\n\tconst POKEDEX_OWNER_TRANSITION_INFO_RETURN\n')
    transform(candidate / 'engine/pokedex/pokedex_detail.asm',
              '\tfarcall PokedexInfo_RestoreListingCache\n\tcall PokedexSelectedMon_CancelCry\n\tcall Pokedex_CancelAnimationPrefetch\n',
              '\tcall PokedexSelectedMon_CancelCry\n\tcall Pokedex_CancelAnimationPrefetch\n'
              '\tfarcall PokedexInfo_PreserveReturnPanel\n\tfarcall PokedexInfo_RestoreListingCache\n')
    transform(candidate / 'engine/pokedex/pokedex_info.asm',
              'PokedexInfo_RestoreListingCache:\n',
              f'INCLUDE "tools/dex_timing/probes/info_return_{"records" if mode == "records" else "relocation"}.asm"\n\nPokedexInfo_RestoreListingCache:\n')
    transform(candidate / 'engine/pokedex/pokedex_3.asm',
              '\tld a, [wPokedexOwnerTransition]\n\tcp POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT\n\tret z\n',
              '\tld a, [wPokedexOwnerTransition]\n\tcp POKEDEX_OWNER_TRANSITION_INFO_RETURN\n'
              '\tjp z, Pokedex_VBlankInfoReturn\n\tcp POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT\n\tret z\n')
    transform(candidate / 'engine/pokedex/pokedex_info_publish.asm',
              'Pokedex_VBlankInfo:\n',
              'INCLUDE "tools/dex_timing/probes/info_return_publish.asm"\n\nPokedex_VBlankInfo:\n')
    if mode == 'records':
        transform(candidate / 'ram/wram.asm', 'wPokedexInfoWorkspaceEnd::\n',
                  '; PRIVATE PREFLIGHT: two atlas-specific committed-page records.\n'
                  'wPokedexInfoReturnRecordA:: ds 7 * TILEMAP_WIDTH + 40 * 2 + 1\n'
                  'wPokedexInfoReturnRecordB:: ds 7 * TILEMAP_WIDTH + 40 * 2 + 1\n'
                  'wPokedexInfoVisible:: db\n'
                  'wPokedexInfoWorkspaceEnd::\n')
        transform(candidate / 'engine/pokedex/pokedex.asm',
                  '\tconst POKEDEX_INFO_MINI_UPLOAD\n',
                  '\tconst POKEDEX_INFO_MINI_UPLOAD\n\tconst POKEDEX_INFO_RECORD\n')
        transform(candidate / 'engine/pokedex/pokedex_info.asm',
                  '\tcp POKEDEX_INFO_PLAN\n\tret nz\n',
                  '\tcp POKEDEX_INFO_RECORD\n\tjp z, PokedexInfo_RecordPage\n'
                  '\tcp POKEDEX_INFO_PLAN\n\tret nz\n')
        info_source = candidate / 'engine/pokedex/pokedex_info.asm'
        original = info_source.read_text()
        old = '\tld a, POKEDEX_INFO_READY\n\tld [wPokedexInfoState], a\n\tret\n'
        if original.count(old) != 2:
            raise ValueError('Info ready-state anchors changed')
        info_source.write_text(original.replace(old, '\tjp PokedexInfo_BeginRecord\n'))
        transform(candidate / 'engine/pokedex/pokedex_info_publish.asm',
                  '\tcp POKEDEX_INFO_READY\n\tret nz\n\tld a, [wPokedexSelectedView]\n'
                  '\tcp DEXSELECT_VIEW_INFO\n\tret nz\n.oam\n',
                  '\tcp POKEDEX_INFO_READY\n\tjr nz, .not_info\n\tld a, [wPokedexSelectedView]\n'
                  '\tcp DEXSELECT_VIEW_INFO\n\tjr nz, .not_info\n'
                  '\tld a, TRUE\n\tld [wPokedexInfoVisible], a\n.oam\n')
        transform(candidate / 'engine/pokedex/pokedex_info_publish.asm',
                  '\tld [wPokedexInfoState], a\n\tret\n\nPokedex_InfoAnimateMinis:',
                  '\tld [wPokedexInfoState], a\n\tret\n.not_info\n'
                  '\txor a\n\tld [wPokedexInfoVisible], a\n\tret\n\nPokedex_InfoAnimateMinis:')
        transform(candidate / 'engine/pokedex/pokedex_3.asm',
                  '\tld [wPokedexDescriptionTextState], a\n\tld [wPokedexOwnerTransition], a\n',
                  '\tld [wPokedexDescriptionTextState], a\n\tld [wPokedexInfoVisible], a\n'
                  '\tld [wPokedexOwnerTransition], a\n')
    make(candidate, 'candidate')
    diagnostic = output / f'pokecrystal-info-return-{"records" if mode == "records" else "relocation"}.gbc'
    for suffix in ('.gbc', '.sym', '.map'):
        shutil.copy2(candidate / ('pokecrystal' + suffix), diagnostic.with_suffix(suffix))
    if any(sha256(p.read_bytes()) != hashes[str(p)] for p in production):
        raise RuntimeError('Production build identity changed')
    result = dict(mode=mode, source=str(source), production_hashes=hashes, baseline=str(baseline), candidate=str(candidate),
                  diagnostic=str(diagnostic), production_unchanged=True,
                  diagnostic_sha256=sha256(diagnostic.read_bytes()))
    (output / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--mode', choices=('readback', 'records'), default='readback')
    parser.add_argument('--source', type=Path, default=ROOT,
                        help='Saved pre-integration source tree for historical A/B reproduction')
    args = parser.parse_args()
    build(args.output, args.jobs, args.mode, args.source)
