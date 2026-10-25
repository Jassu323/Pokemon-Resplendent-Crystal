"""Preserve the rejected VRAM renderer independently of disposable builds."""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import tarfile

from dex_timing.assets import sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'build/dex-selected-ancestors-vram-20261012-v6'
SAMPLED = ROOT / 'build/dex-selected-sampled-vram-20261013-v2'
ARCHIVE = ROOT / 'docs/archived/selected-vram-ancestors-20261013'
EXPECTED = '07bec143ad5138fed762476fdc8df9bd8f57011e121b6d4b1cbf1d5b4efb23d2'
ASSETS = {'dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets', 'dex-runtime-display-assets'}
INTEGRATION = ROOT / 'build/dex-selected-ancestors-integration-20261013/precomputed'
CONTROL = ROOT / 'build/dex-selected-production-control-20261012-v1'


def retained(path):
    return ('__pycache__' not in path.parts and path.suffix not in
            {'.o', '.gbc', '.gb', '.sym', '.map', '.pyc', '.sav', '.rtc'} and
            (path.parts[0] != 'build' or len(path.parts) > 1 and path.parts[1] in ASSETS))


def pack(source, destination):
    with tarfile.open(destination, 'w:xz', preset=6) as archive:
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if path.is_file() and retained(relative):
                archive.add(path, arcname=str(relative), recursive=False)


def text_paths(root):
    paths = set()
    for directory, folders, files in os.walk(root):
        folders[:] = [name for name in folders if name not in
                      {'.git', 'build', 'docs', 'research_artifacts', '__pycache__'}]
        for name in files:
            path = Path(directory) / name
            if path.suffix in ('.asm', '.py', '.mk') or name == 'Makefile':
                paths.add(path.relative_to(root))
    return paths


def seal():
    verify()
    path = ARCHIVE / 'manifest.json'
    manifest = json.loads(path.read_text())
    for source in sorted(ARCHIVE.rglob('*')):
        if source.is_file() and source != path:
            manifest['files'].setdefault(str(source.relative_to(ARCHIVE)), sha256(source.read_bytes()))
    path.write_text(json.dumps(manifest, indent=2) + '\n')


def diff(left, right, destination, display_only=False):
    parts = []
    display_tools = {'pokedex_info_assets.py', 'pokedex_moves_assets.py',
                     'pokedex_runtime_display_assets.py', 'pokedex_semantic_display_assets.py'}
    for name in sorted(text_paths(left) | text_paths(right)):
        if display_only and name.parts[0] == 'tools' and str(name) not in {
                'tools/' + item for item in display_tools}:
            continue
        a, b = left / name, right / name
        old, new = a.read_text() if a.exists() else '', b.read_text() if b.exists() else ''
        if old != new:
            parts.extend(difflib.unified_diff(old.splitlines(keepends=True),
                new.splitlines(keepends=True), fromfile='a/' + str(name) if a.exists() else '/dev/null',
                tofile='b/' + str(name) if b.exists() else '/dev/null'))
    destination.write_text(''.join(parts))


def comparison():
    from dex_timing.selected_comparison import paired, startup, entry_delta
    from pokedex_info_assets import Compiler

    def load(source, name):
        return json.loads((source / name / 'summary.json').read_text())

    current = json.loads((INTEGRATION / 'runtime-manifest.json').read_text())
    fallback = json.loads((SOURCE / 'runtime-manifest.json').read_text())
    if fallback['rom_sha256'] != EXPECTED:
        raise ValueError('Fallback comparison no longer matches the archive')
    if sha256((ROOT / 'pokecrystal.gbc').read_bytes()) != current['rom_sha256']:
        raise ValueError('Production comparison no longer matches the integration')
    old, new = Compiler().compile(), Compiler().compile(ancestors=True)
    record = dict(production=current, vram=fallback,
                  vram_minus_production_bytes={name: fallback['delta'][name] - value
                                               for name, value in current['delta'].items()},
                  timings={})
    for name in ('architecture-timing', 'feature-timing'):
        before, after = load(INTEGRATION, name), load(SOURCE, name)
        if before['failures'] or after['failures']:
            raise ValueError('Do not summarize failing native timing cases')
        record['timings'][name] = dict(
            production_cases=before['cases'], vram_cases=after['cases'],
            vram_vs_production=paired(before['rows'], after['rows'], new, new))
    record['timings']['production_vs_before'] = paired(
        load(CONTROL, 'architecture-timing')['rows'],
        load(INTEGRATION, 'architecture-timing')['rows'], old, new)
    record['timings']['startup_vram_vs_production'] = startup(
        load(INTEGRATION, 'startup-timing')['rows'], load(SOURCE, 'startup-timing')['rows'])
    record['timings']['entry_vram_vs_production'] = entry_delta(
        load(INTEGRATION, 'entry-timing')['rows'], load(SOURCE, 'entry-timing')['rows'])
    (ARCHIVE / 'production-ancestors-comparison.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record['vram_minus_production_bytes']), flush=True)


def create():
    if ARCHIVE.exists():
        raise ValueError('Archive exists; verify it instead of replacing preserved evidence')
    if sha256((SOURCE / 'pokecrystal-dex-selected-runtime.gbc').read_bytes()) != EXPECTED:
        raise ValueError('Reviewed VRAM cartridge changed')
    ARCHIVE.mkdir(parents=True)
    workspace = ROOT / 'build/dex-vram-archive-staging-20261013'
    workspace.mkdir()
    baseline = workspace / 'baseline'
    with tarfile.open(SOURCE / 'rollback-source.tar') as archive:
        archive.extractall(baseline, filter='data')
    shutil.copytree(ROOT / 'gfx', baseline / 'gfx', dirs_exist_ok=True)
    for name in ASSETS - {'dex-runtime-display-assets'}:
        shutil.copytree(ROOT / 'build' / name, baseline / 'build' / name)
    pack(baseline, ARCHIVE / 'production-before-ancestors.tar.xz')
    pack(SOURCE / 'candidate', ARCHIVE / 'vram-ancestors-source.tar.xz')
    pack(SAMPLED / 'candidate', ARCHIVE / 'vram-sampled-evolutions-source.tar.xz')
    for label, source in (('production-before-ancestors', SOURCE / 'rollback/pokecrystal'),
                          ('vram-ancestors', SOURCE / 'pokecrystal-dex-selected-runtime'),
                          ('vram-sampled-evolutions', SAMPLED / 'pokecrystal-dex-selected-runtime')):
        target = ARCHIVE / (label + '-cartridge.tar.xz')
        with tarfile.open(target, 'w:xz') as archive:
            for suffix in ('gbc', 'sym', 'map', 'sav'):
                path = source.with_suffix('.' + suffix)
                if path.exists():
                    archive.add(path, arcname='pokecrystal.' + suffix)
    diff(baseline, SOURCE / 'candidate', ARCHIVE / 'production-before-to-vram.diff')
    diff(SOURCE / 'candidate', SAMPLED / 'candidate', ARCHIVE / 'sampled-evolution-fixture.diff')
    for label, source in (('architecture', ROOT / 'build/dex-selected-architecture-comparison-20261012/summary.json'),
                          ('sampled-cries', ROOT / 'build/dex-selected-sampled-comparison-20261013/summary.json')):
        shutil.copy2(source, ARCHIVE / (label + '-comparison.json'))
    for name in ('pokedex_selected_architecture_comparison.md', 'pokedex_selected_runtime_prototype.md',
                 'full_regression_suite.md', 'battle_animation_interrupt_timing_contract.md'):
        shutil.copy2(ROOT / 'docs' / name, ARCHIVE / name)
    recipe = ARCHIVE / 'recipes'
    recipe.mkdir()
    for name in ('build_selected_runtime_prototype.py', 'build_selected_semantic_prototype.py',
                 'build_selected_sampled_evolution_prototypes.py', 'pokedex_info_assets.py',
                 'pokedex_runtime_display_assets.py', 'pokedex_semantic_display_assets.py',
                 'pokedex_moves_assets.py'):
        shutil.copy2(ROOT / 'tools' / name, recipe / name)
    shutil.copytree(ROOT / 'tools/dex_timing/probes/selected_runtime', recipe / 'selected_runtime')
    for name in ('selected_runtime.diff', 'selected_semantic.diff', 'selected_semantic_level.diff',
                 'selected_ancestors.diff', 'selected_ancestors.asm', 'selected_sampled_evolutions.diff'):
        shutil.copy2(ROOT / 'tools/dex_timing/probes' / name, recipe / name)
    manifest = dict(base_commit='f4182c81fc19a637feffa7b17e8fa01a7d4e77df',
                    vram_rom_sha256=EXPECTED, production_before_sha256=
                    sha256((SOURCE / 'rollback/pokecrystal.gbc').read_bytes()),
                    format='Complete sources including generated graphics; immutable review cartridges; rebase diffs',
                    files={str(path.relative_to(ARCHIVE)): sha256(path.read_bytes())
                           for path in sorted(ARCHIVE.rglob('*')) if path.is_file()})
    (ARCHIVE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(archive=str(ARCHIVE), files=len(manifest['files']),
                         bytes=sum(path.stat().st_size for path in ARCHIVE.rglob('*') if path.is_file()))), flush=True)


def restore(destination, variant):
    if destination.exists() or not destination.resolve().is_relative_to(ROOT / 'build'):
        raise ValueError('Restore only to a fresh private directory under build/')
    verify()
    destination.mkdir(parents=True)
    with tarfile.open(ARCHIVE / (variant + '-source.tar.xz' if variant.startswith('vram') else
                                 variant + '.tar.xz')) as archive:
        archive.extractall(destination, filter='data')
    with tarfile.open(ARCHIVE / (variant + '-cartridge.tar.xz')) as archive:
        archive.extractall(destination, filter='data')
    print(str(destination), flush=True)


def verify():
    manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha256((ARCHIVE / name).read_bytes()) != digest:
            raise ValueError('Archived file checksum changed: ' + name)
    for path in ARCHIVE.glob('*.tar.xz'):
        with tarfile.open(path) as archive:
            for member in archive:
                if member.isfile():
                    archive.extractfile(member).read()
    print('All archived checksums and compressed streams verified', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('create', 'verify', 'restore', 'production-diff', 'comparison', 'seal'))
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--variant', choices=('vram-ancestors', 'vram-sampled-evolutions',
                                             'production-before-ancestors'), default='vram-ancestors')
    args = parser.parse_args()
    if args.action == 'create':
        create()
    elif args.action == 'restore':
        restore(args.destination.resolve(), args.variant)
    elif args.action == 'production-diff':
        diff(ROOT, SOURCE / 'candidate', ARCHIVE / 'production-ancestors-to-vram.diff',
             display_only=True)
    elif args.action == 'comparison':
        comparison()
    elif args.action == 'seal':
        seal()
    else:
        verify()
