"""Mechanically promote the tested cleanup, refusing changed baseline inputs."""
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.assets import sha256
from dex_timing.cold_listing import ROOT

BASE = ROOT / 'build/dex-cleanup-20261014'


def promote():
    baseline = BASE / 'runtime-regression/baseline/candidate'
    candidate = BASE / 'candidate'
    manifest = json.loads((BASE / 'cleanup-manifest.json').read_text())
    assert sha256((candidate / 'pokecrystal.gbc').read_bytes()) == manifest['rom_sha256']
    for path, digest in manifest['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, 'Production link changed: ' + path
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    files = [name for name in tracked if name.endswith(('.asm', '.inc')) or name in ('Makefile', '.gitignore')]
    additions = ['engine/pokedex/new_entry_visual.asm']
    changes = []
    for name in files:
        before, after = baseline / name, candidate / name
        if before.exists() and (not after.exists() or before.read_bytes() != after.read_bytes()):
            assert (ROOT / name).read_bytes() == before.read_bytes(), 'Unrelated source edits: ' + name
            changes.append(name)
    for name in additions:
        assert not (ROOT / name).exists(), 'Existing addition: ' + name
    # Validate every move before writing anything to the shared checkout.
    for record in manifest['archived_graphics']:
        assert sha256((ROOT / record['original']).read_bytes()) == record['sha256']
        assert not (ROOT / record['archived']).exists()
    saved = BASE / 'promotion-rollback'
    saved.mkdir(exist_ok=False)
    for name in changes:
        destination = saved / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    for name in changes + additions:
        if (candidate / name).exists():
            shutil.copy2(candidate / name, ROOT / name)
        else:
            (ROOT / name).unlink()
    for record in manifest['archived_graphics']:
        destination = ROOT / record['archived']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(ROOT / record['original'], destination)
    for source in (candidate / 'gfx/archived/pokedex').iterdir():
        destination = ROOT / 'gfx/archived/pokedex' / source.name
        if not destination.exists():
            shutil.copy2(source, destination)
        assert destination.read_bytes() == source.read_bytes()
    write = dict(changed=changes, added=additions, expected_rom_sha256=manifest['rom_sha256'],
                 rollback=str(saved), archived=manifest['archived_graphics'])
    (BASE / 'promotion-manifest.json').write_text(json.dumps(write, indent=2) + '\n')
    print(json.dumps(write, indent=2))


if __name__ == '__main__':
    promote()
