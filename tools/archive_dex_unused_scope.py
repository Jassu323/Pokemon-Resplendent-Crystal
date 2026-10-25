"""Archive the deferred Dex cleanup assessment and exact link-only prototypes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from archive_selected_vram_ancestors import pack
from dex_timing.assets import sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'build/dex-unused-scope-20261013'
ARCHIVE = ROOT / 'docs/archived/dex-unused-scope-20261013'
VARIANTS = {'baseline': 'baseline-control', 'recommended': 'combined-recommended',
            'with-asset': 'combined-with-asset'}
EXPECTED = 'e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e'


def create():
    if (ARCHIVE / 'manifest.json').exists():
        raise ValueError('Archive already sealed; verify rather than replace it')
    trials = SOURCE / 'trials'
    if sha256((trials / 'baseline-control.gbc').read_bytes()) != EXPECTED:
        raise ValueError('Private unchanged control does not match the assessed production')
    if sha256((ROOT / 'pokecrystal.gbc').read_bytes()) != EXPECTED:
        raise ValueError('Production changed before archival')
    if (trials / 'baseline-control.patch').read_text():
        raise ValueError('Baseline control has source edits')
    if (ARCHIVE / 'baseline-source.tar.xz').exists():
        raise ValueError('Partial archive exists; inspect before rebuilding')
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    staging = ROOT / 'build/dex-unused-archive-staging-20261013'
    if staging.exists():
        raise ValueError('Archive staging already exists')
    with tarfile.open(trials / 'source.tar') as archive:
        archive.extractall(staging, filter='data')
    shutil.copytree(ROOT / 'gfx', staging / 'gfx', dirs_exist_ok=True)
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        shutil.copytree(ROOT / 'build' / name, staging / 'build' / name)
    pack(staging, ARCHIVE / 'baseline-source.tar.xz')
    shutil.copy2(ROOT / 'docs/pokedex_unused_code_scope.md', ARCHIVE / 'findings.md')
    shutil.copy2(ROOT / 'docs/pokedex_selected_bug_backlog.md', ARCHIVE / 'backlog-snapshot.md')
    for name in ('inventory.json', 'trials/results.json', 'trials/extras.json'):
        shutil.copy2(SOURCE / name, ARCHIVE / Path(name).name)
    recipes = ARCHIVE / 'recipes'
    recipes.mkdir()
    shutil.copy2(ROOT / 'tools/dex_timing/dex_unused_scope.py', recipes / 'dex_unused_scope.py')
    shutil.copy2(Path(__file__), recipes / 'archive_dex_unused_scope.py')
    shutil.copy2(ROOT / 'tools/archive_selected_vram_ancestors.py', recipes / 'archive_selected_vram_ancestors.py')
    rows = {r['group']: r for r in json.loads((trials / 'extras.json').read_text())}
    variants = {}
    for name, stem in VARIANTS.items():
        if rows[stem]['build_exit_code']:
            raise ValueError('Do not archive a failed build as a review candidate')
        with tarfile.open(ARCHIVE / (name + '-cartridge.tar.xz'), 'w:xz') as archive:
            for suffix in ('gbc', 'sym', 'map'):
                archive.add(trials / (stem + '.' + suffix), arcname='pokecrystal.' + suffix)
        if name != 'baseline':
            shutil.copy2(trials / (stem + '.patch'), ARCHIVE / (name + '.patch'))
        shutil.copy2(trials / (stem + '.log'), ARCHIVE / (name + '-build.log'))
        variants[name] = dict(rom_sha256=sha256((trials / (stem + '.gbc')).read_bytes()),
                              sym_sha256=sha256((trials / (stem + '.sym')).read_bytes()),
                              reclaimed=rows[stem]['reclaimed'])
    additions = ARCHIVE / 'with-asset-additions/build'
    additions.mkdir(parents=True)
    shutil.copy2(trials / 'candidate/build/slowpoke-dex-prefix.lz', additions / 'slowpoke-dex-prefix.lz')
    manifest = dict(format='deferred-dex-cleanup-v1', date='2026-10-13',
                    base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                    qualification='Source audit and private build/link checks only; no runtime regression acceptance',
                    variants=variants, files={str(p.relative_to(ARCHIVE)): sha256(p.read_bytes())
                        for p in sorted(ARCHIVE.rglob('*')) if p.is_file()})
    (ARCHIVE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    verify()


def verify():
    manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha256((ARCHIVE / name).read_bytes()) != digest:
            raise ValueError('Archived checksum changed: ' + name)
    for path in ARCHIVE.glob('*.tar.xz'):
        with tarfile.open(path) as archive:
            for member in archive:
                if member.isfile():
                    archive.extractfile(member).read()
    print('Archive checksums and compressed streams verified', flush=True)


def restore(destination, variant):
    if destination.exists() or not destination.resolve().is_relative_to(ROOT / 'build'):
        raise ValueError('Restore only to a fresh private directory under build/')
    verify()
    with tarfile.open(ARCHIVE / 'baseline-source.tar.xz') as archive:
        archive.extractall(destination, filter='data')
    if variant != 'baseline':
        subprocess.run(['patch', '-p1', '-i', str(ARCHIVE / (variant + '.patch'))],
                       cwd=destination, check=True)
    if variant == 'with-asset':
        shutil.copytree(ARCHIVE / 'with-asset-additions', destination, dirs_exist_ok=True)
    with tarfile.open(ARCHIVE / (variant + '-cartridge.tar.xz')) as archive:
        archive.extractall(destination, filter='data')
    print(str(destination), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('create', 'verify', 'restore'))
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--variant', choices=VARIANTS, default='recommended')
    args = parser.parse_args()
    if args.action == 'restore':
        if args.destination is None:
            parser.error('restore requires --destination')
        restore(args.destination.resolve(), args.variant)
    else:
        globals()[args.action]()
