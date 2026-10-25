"""Build private semantic-ROM / RAM- or VRAM-restoration architecture trials."""
import argparse
from pathlib import Path
import shutil
import subprocess

from build_selected_runtime_prototype import ROOT, prepare, finish


def build(output, restore, jobs, ancestors=False):
    prepare(output)
    candidate = output / 'candidate'
    for name in ('selected_runtime.diff', 'selected_semantic.diff'):
        subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes' / name)],
                       cwd=candidate, check=True)
    for path in (ROOT / 'tools/dex_timing/probes/selected_runtime').glob('*.asm'):
        shutil.copy2(path, candidate / 'engine/pokedex' / path.name)
    for name in ('engine/pokedex/pokedex_moves.asm', 'data/pokemon/evos_attacks.asm',
                 'data/pokemon/egg_moves.asm'):
        shutil.copy2(ROOT / name, candidate / name)
    # The level marker still comes from the native battle font, not a second bitmap.
    subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes/selected_semantic_level.diff')],
                   cwd=candidate, check=True)
    constants = candidate / 'includes.asm'
    defines = 'DEF DEX_RUNTIME_SEMANTIC EQU 1\n'
    if ancestors:
        defines += 'DEF DEX_RUNTIME_ANCESTORS EQU 1\n'
    if restore == 'vram':
        defines += 'DEF DEX_RUNTIME_RESTORE_VRAM EQU 1\n'
    elif restore == 'rom':
        defines += 'DEF DEX_RUNTIME_RESTORE_ROM EQU 1\n'
    constants.write_text(defines + constants.read_text())
    shutil.copy2(ROOT / 'tools/pokedex_info_assets.py', candidate / 'tools/pokedex_info_assets.py')
    shutil.copy2(ROOT / 'tools/pokedex_semantic_display_assets.py', candidate / 'tools/pokedex_semantic_display_assets.py')
    shutil.copy2(ROOT / 'tools/pokedex_moves_assets.py', candidate / 'tools/pokedex_moves_assets.py')
    if restore == 'rom':
        shutil.copy2(ROOT / 'tools/pokedex_rom_restore_assets.py', candidate / 'tools/pokedex_rom_restore_assets.py')
        shutil.copy2(ROOT / 'tools/dex_timing/probes/selected_rom_restore.asm', candidate / 'engine/pokedex/pokedex_rom_restore.asm')
        subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes/selected_rom_restore.diff')],
                       cwd=candidate, check=True)
        subprocess.run(['python3', str(candidate / 'tools/pokedex_rom_restore_assets.py'), '--root', str(candidate)],
                       cwd=ROOT, check=True)
    if ancestors:
        shutil.copy2(ROOT / 'tools/dex_timing/probes/selected_ancestors.asm', candidate / 'engine/pokedex/pokedex_ancestors.asm')
        subprocess.run(['patch', '-p1', '--input', str(ROOT / 'tools/dex_timing/probes/selected_ancestors.diff')],
                       cwd=candidate, check=True)
    subprocess.run(['python3', str(candidate / 'tools/pokedex_semantic_display_assets.py'), '--root', str(candidate)],
                   cwd=ROOT, check=True)
    finish(output, jobs, False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--restore', choices=('ram', 'vram', 'rom'), required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--ancestors', action='store_true')
    args = parser.parse_args()
    build(args.output.resolve(), args.restore, args.jobs, args.ancestors)
