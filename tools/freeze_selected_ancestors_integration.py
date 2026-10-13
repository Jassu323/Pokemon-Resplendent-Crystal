"""Freeze the integrated precomputed ancestor build for full qualification."""
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.assets import sha256
from dex_timing.info_ui import fixture
from build_dex_unown_prototype import resources
from build_selected_runtime_prototype import DONOR

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build/dex-selected-ancestors-integration-20261013/precomputed'
BEFORE = ROOT / 'build/dex-selected-ancestors-vram-20261012-v6'


def freeze():
    if OUTPUT.exists():
        raise ValueError('Use a fresh integration snapshot')
    OUTPUT.mkdir(parents=True)
    candidate = OUTPUT / 'candidate'
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                                    cwd=ROOT).decode().split('\0')
    for name in paths:
        source = ROOT / name
        if name and source.is_file() and not name.startswith('docs/archived/selected-vram-ancestors-20261013/'):
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    for stem in ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime', 'pokecrystal-ancestors'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(ROOT / f'pokecrystal.{ext}', OUTPUT / f'{stem}.{ext}')
        fixture(DONOR, OUTPUT / f'{stem}.sav')
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', candidate / f'pokecrystal.{ext}')
    shutil.copy2(BEFORE / 'rollback-source.tar', OUTPUT / 'rollback-source.tar')
    shutil.copytree(BEFORE / 'rollback', OUTPUT / 'rollback')
    old, new = resources(OUTPUT / 'rollback/pokecrystal.map'), resources(ROOT / 'pokecrystal.map')
    manifest = dict(rom_sha256=sha256((ROOT / 'pokecrystal.gbc').read_bytes()),
                    baseline_sha256=sha256((OUTPUT / 'rollback/pokecrystal.gbc').read_bytes()),
                    delta={name:new[name]-old[name] for name in old},
                    production_integrated=True, temporary_evolution_fixture_included=False,
                    method='Precomputed glyphs, headings, numbers and display records retained')
    (OUTPUT / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    freeze()
