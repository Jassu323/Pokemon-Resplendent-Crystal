"""Build the visual-only registration skin in an isolated production snapshot."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import sha256, read_symbols
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
STEM = 'pokecrystal-dex-new-entry-visual'


def build(output, jobs):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private directory under build/')
    protected = {str(ROOT / ('pokecrystal.' + e)): sha256((ROOT / ('pokecrystal.' + e)).read_bytes())
                 for e in ('gbc', 'sym', 'map')}
    output.mkdir(parents=True)
    archive = output / 'rollback-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    candidate = output / 'candidate'
    with tarfile.open(archive) as source:
        source.extractall(candidate, filter='data')
    shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    rollback = output / 'rollback'
    rollback.mkdir()
    for e in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / ('pokecrystal.' + e), rollback / ('pokecrystal.' + e))
    patch = ROOT / 'tools/dex_timing/probes/new_entry_visual.diff'
    subprocess.run(['patch', '-p1', '-i', str(patch)], cwd=candidate, check=True)
    shutil.copy2(ROOT / 'tools/dex_timing/probes/new_entry_visual.asm',
                 candidate / 'engine/pokedex/new_entry_visual.asm')
    shutil.copy2(ROOT / 'tools/test_pokedex_info.py', candidate / 'tools/test_pokedex_info.py')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for e in ('gbc', 'sym', 'map'):
        shutil.copy2(candidate / ('pokecrystal.' + e), output / (STEM + '.' + e))
    before, after = read_symbols(ROOT / 'pokecrystal.sym'), read_symbols(candidate / 'pokecrystal.sym')
    for name, address in before.items():
        if address[1] >= 0xa000 and name in after:
            assert after[name] == address, ('Memory address moved', name)
    delta = {k: v - resources(ROOT / 'pokecrystal.map')[k]
             for k, v in resources(candidate / 'pokecrystal.map').items()}
    assert all(v == 0 for k, v in delta.items() if k != 'ROMX'), delta
    assert all(sha256(Path(p).read_bytes()) == h for p, h in protected.items())
    result = dict(variant='visual-only', rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                  baseline_rom_sha256=protected[str(ROOT / 'pokecrystal.gbc')], delta=delta,
                  new_artwork=False, input_flow_unchanged=True, production_unchanged=True,
                  protected=protected, candidate=str(candidate))
    (output / 'visual-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs)
