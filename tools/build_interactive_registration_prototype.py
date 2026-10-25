"""Build private interactive-registration and evolution-data prototypes."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.assets import sha256
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/gotcha-boundary-final-20261015/candidate'
DEFAULT = ROOT / 'build/interactive-registration-20261015'


def build(output, jobs, evolution_patch=None):
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh output directory under build/')
    protected = {str(p): sha256(p.read_bytes()) for p in
                 (*(ROOT / f'pokecrystal.{x}' for x in ('gbc', 'sym', 'map')),
                  *ROOT.glob('*.sav'))}
    output.mkdir(parents=True)
    candidate = output / 'candidate'
    shutil.copytree(BASE, candidate)
    # Keep the qualified Gotcha boundary while adopting current data updates.
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    excluded = {'engine/items/item_effects.asm', 'engine/battle/start_battle.asm'}
    for name in filter(None, tracked):
        source, target = ROOT / name, candidate / name
        if name not in excluded and source.is_file() and (
                not target.exists() or source.read_bytes() != target.read_bytes()):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    changes = {}

    if evolution_patch:
        evolution_patch = evolution_patch.resolve()
        if not evolution_patch.is_file():
            raise ValueError(f'Missing evolution patch: {evolution_patch}')
        before_data = {str(p.relative_to(candidate)): p.read_text() for p in
                       (candidate / 'data/pokemon').glob('evos_attacks_*.asm')}
        before_data['data/pokemon/first_stages.asm'] = (
            candidate / 'data/pokemon/first_stages.asm').read_text()
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(evolution_patch)],
                       cwd=candidate, check=True)
        for name, old in before_data.items():
            new = (candidate / name).read_text()
            if old != new:
                changes[name] = old, new

    def replace(name, old, new):
        path = candidate / name
        before = path.read_text()
        if before.count(old) != 1:
            raise ValueError(f'{name}: expected one replacement anchor')
        after = before.replace(old, new)
        path.write_text(after)
        changes[name] = (before, after)

    name = 'engine/pokedex/new_pokedex_entry.asm'
    old = (candidate / name).read_text()
    new = (ROOT / 'tools/dex_timing/probes/interactive_registration.asm').read_text()
    (candidate / name).write_text(new)
    changes[name] = (old, new)
    name = 'engine/battle/capture_speed.asm'
    old = (candidate / name).read_text()
    new = (ROOT / 'tools/dex_timing/probes/gotcha_boundary.asm').read_text()
    (candidate / name).write_text(new)
    changes[name] = (old, new)
    replace('engine/pokedex/pokedex_animation.asm',
            '\tld a, [wPokedexAnimPlaybackState]\n'
            '\tcp POKEDEX_ANIM_PLAYBACK_WAITING\n\tret nz\n\n'
            '\tld a, [wPokedexAnimOwner]\n\tcall PlayMonCry2\n',
            'Pokedex_BeginPreparedDescriptionAnimation::\n'
            '; Fixed-species registration enters after the Listing-only checks.\n'
            '\tld a, [wPokedexAnimPlaybackState]\n'
            '\tcp POKEDEX_ANIM_PLAYBACK_WAITING\n\tret nz\n\n'
            '\tld a, [wPokedexAnimOwner]\n\tcall PlayMonCry2\n')
    replace('engine/events/specials.asm',
            '\tld [wNamedObjectIndex], a\n\tfarcall NewPokedexEntry\n\tcall ExitAllMenus\n',
            '\tld [wNamedObjectIndex], a\n\tfarcall NewPokedexEntry\n'
            '\tcall ReturnToMapFromSubmenu\n\tcall ExitAllMenus\n')
    # Complete evolution metadata exceeds the former combined Info bank.
    # Keep its semantic records local; relocate only the 2 KiB number pointers
    # into spare space alongside their existing glyphs.
    replace('tools/pokedex_info_assets.py',
            "        asm += ['PokedexInfoNumbers:']\n"
            "        asm += ['\\tdw ' + ', '.join(map(pointer, row)) for row in data['numbers']]\n",
            "        numbers = ['; Generated numeric glyph pointers.', 'PokedexInfoNumbers:']\n"
            "        numbers += ['\\tdw ' + ', '.join(map(pointer, row)) for row in data['numbers']]\n"
            "        (destination / 'numbers.asm').write_text('\\n'.join(numbers) + '\\n')\n")
    replace('main.asm',
            'ASSERT PokedexInfoAncestorTitleGFXEnd - PokedexInfoAncestorTitleGFX == 13 tiles\n',
            'ASSERT PokedexInfoAncestorTitleGFXEnd - PokedexInfoAncestorTitleGFX == 13 tiles\n'
            'INCLUDE "build/dex-info-assets/numbers.asm"\n')
    replace('Makefile',
            'build/dex-info-assets/titles.2bpp: build/dex-info-assets/tables.asm\n',
            'build/dex-info-assets/numbers.asm: build/dex-info-assets/tables.asm\n'
            '\t@test -f $@ || python3 -B tools/pokedex_info_assets.py --ancestors\n'
            'build/dex-info-assets/titles.2bpp: build/dex-info-assets/tables.asm\n')
    replace('engine/pokedex/pokedex_info.asm',
            '\tld de, PokedexInfoNumbers\n\tadd hl, de\n\tld b, 4\n.number\n',
            '\tld de, PokedexInfoNumbers\n\tadd hl, de\n'
            '; Stats prepare no minis; the old committed mini pixels live in VRAM.\n'
            '; Borrow eight dead staging bytes for one banked number-pointer row.\n'
            '\tld de, wPokedexInfoMiniGFX\n\tld bc, 8\n'
            '\tld a, BANK(PokedexInfoNumbers)\n\tcall FarCopyBytes\n'
            '\tld hl, wPokedexInfoMiniGFX\n\tld b, 4\n.number\n')
    (output / 'interactive.diff').write_text(''.join(''.join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), fromfile='a/'+name,
        tofile='b/'+name)) for name, (old, new) in changes.items()))
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    before, after = resources(ROOT / 'pokecrystal.map'), resources(candidate / 'pokecrystal.map')
    delta = {n: after[n]-before[n] for n in before}
    for path, expected in protected.items():
        assert sha256(Path(path).read_bytes()) == expected, path
    record = dict(protected=protected, delta=delta,
                  rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                  production_unchanged=True, interactive_registration=True,
                  changed_owners=list(changes), base=str(BASE),
                  evolution_patch=str(evolution_patch) if evolution_patch else None,
                  evolution_patch_sha256=sha256(evolution_patch.read_bytes()) if evolution_patch else None)
    (output / 'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--evolution-patch', type=Path)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs, args.evolution_patch)
