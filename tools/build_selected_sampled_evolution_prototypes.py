"""Build a matched, private sampled-cry evolution comparison pair."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_selected_runtime_prototype import ROOT, DONOR, STEM, prepare
from build_dex_unown_prototype import resources
from dex_timing.assets import sha256
from dex_timing.info_ui import fixture
from pokedex_info_assets import Compiler, evolution_graph

VRAM = ROOT / 'build/dex-selected-ancestors-vram-20261012-v6'
EXPECTED_VRAM = '07bec143ad5138fed762476fdc8df9bd8f57011e121b6d4b1cbf1d5b4efb23d2'
PATCH = ROOT / 'tools/dex_timing/probes/selected_sampled_evolutions.diff'


def build(output, variant, jobs):
    prepare(output)
    candidate = output / 'candidate'
    if variant == 'vram':
        if sha256((VRAM / f'{STEM}.gbc').read_bytes()) != EXPECTED_VRAM:
            raise ValueError('Reviewed VRAM source changed')
        shutil.copytree(VRAM / 'candidate', candidate, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('build', 'gfx', '*.o', '*.gbc',
                                                     '*.sym', '*.map', '__pycache__'))
        for source in (VRAM / 'candidate/gfx').rglob('*.asm'):
            shutil.copy2(source, candidate / source.relative_to(VRAM / 'candidate'))
    shutil.copy2(ROOT / 'tools/pokedex_info_assets.py', candidate / 'tools/pokedex_info_assets.py')
    before = evolution_graph(candidate)
    subprocess.run(['patch', '-p1', '--fuzz=0', '--input', str(PATCH)], cwd=candidate, check=True)
    after = evolution_graph(candidate)
    changed = {name: dict(before=before[name], after=after[name])
               for name in before if before[name] != after[name]}
    assert set(changed) == {'TREECKO', 'GROVYLE', 'TORCHIC', 'COMBUSKEN', 'MUDKIP',
                            'MARSHTOMP', 'MAGNETON', 'PILOSWINE'}
    Compiler(candidate).write(candidate / 'build/dex-info-assets')
    if variant == 'vram':
        subprocess.run(['python3', str(candidate / 'tools/pokedex_semantic_display_assets.py'),
                        '--root', str(candidate)], check=True, cwd=ROOT)
        subprocess.run(['python3', str(candidate / 'tools/pokedex_runtime_display_assets.py'),
                        '--root', str(candidate)], check=True, cwd=ROOT)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    review = f'pokecrystal-dex-sampled-evolutions-{variant}'
    for stem in (STEM, review):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'{stem}.{ext}')
        fixture(DONOR, output / f'{stem}.sav')
    manifest = json.loads((output / 'runtime-manifest.json').read_text())
    for path, digest in manifest['protected_inputs'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    base = VRAM / 'candidate' if variant == 'vram' else ROOT
    manifest.update(variant=variant, configured_edges=changed,
                    testing_only_final_stage_requirement='Level 40; not a balance decision',
                    base_vram_sha256=EXPECTED_VRAM if variant == 'vram' else None,
                    rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                    delta={name: resources(candidate / 'pokecrystal.map')[name] - value
                           for name, value in resources(ROOT / 'pokecrystal.map').items()},
                    configuration_delta={name: resources(candidate / 'pokecrystal.map')[name] - value
                                         for name, value in resources(base / 'pokecrystal.map').items()},
                    fixture_sha256=sha256((output / f'{STEM}.sav').read_bytes()),
                    production_unchanged=True)
    (output / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=('production', 'vram'), required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    build(args.output.resolve(), args.variant, args.jobs)
