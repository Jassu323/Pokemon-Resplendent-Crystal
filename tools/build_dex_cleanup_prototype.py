"""Build all approved Dex removals and retain their original graphics."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import sha256, read_symbols
from dex_timing.cold_listing import ROOT
from dex_timing.dex_post_entry_cleanup import BASE, edit
from dex_timing.dex_unused_scope import GROUPS
from dex_timing.mobile_slowpoke_cleanup import FILES as MOBILE_FILES, edit as mobile_edit
from build_dex_unown_prototype import resources

OUTPUT = ROOT / 'build/dex-cleanup-20261014'
TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')


def build(output, jobs):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh output under build/')
    output.mkdir(parents=True)
    protected = {str(ROOT / f'pokecrystal.{ext}'): sha256((ROOT / f'pokecrystal.{ext}').read_bytes())
                 for ext in ('gbc', 'sym', 'map')}
    archive = output / 'rollback-source.tar'
    subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
    with tarfile.open(archive, 'a') as saved:
        saved.add(ROOT / 'gfx', arcname='gfx')
        saved.add(ROOT / 'tools', arcname='tools')
        for name in TABLES:
            saved.add(ROOT / 'build' / name, arcname='build/' + name)
    rollback = output / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    candidate = output / 'candidate'
    shutil.copytree(BASE, candidate, ignore=shutil.ignore_patterns('*.o', '*.d', '*.orig', '*.rej'))
    shutil.copytree(ROOT / 'tools', candidate / 'tools', dirs_exist_ok=True)
    files = {file for blocks in GROUPS.values() for file, _, _ in blocks}
    files.update(('engine/overworld/wildmons.asm', 'engine/pokedex/pokedex_description.asm',
                  'engine/pokedex/new_entry_visual.asm', 'engine/pokedex/performance_indexed.asm', 'main.asm'))
    originals = {file: (BASE / file).read_text() for file in files}
    groups = [name for name in GROUPS if name != 'test-only-discovery-apis']
    changes = edit(originals, groups, roamer=True, wrap=True, fonts=True, mark=True,
                   query=True, compatibility=True, edge=True, adapter=True, shell=True)
    changes['main.asm'] = changes['main.asm'].replace('INCLUDE "engine/pokedex/performance_idle.asm"\n', '')
    for file in ('engine/overworld/wildmons.asm', 'engine/pokedex/performance_indexed.asm'):
        changes[file] = changes[file].replace('FindNest', 'PokedexArea_RoamerNests')
    changes['engine/pokedex/pokedex.asm'] = changes['engine/pokedex/pokedex.asm'].replace(
        'INCBIN "gfx/pokedex/slowpoke.2bpp.lz"', 'INCBIN "gfx/pokedex/slowpoke_dex.2bpp.lz"')
    mobile_originals = {file: (BASE / file).read_text() for file in MOBILE_FILES}
    changes.update(mobile_edit(mobile_originals, assets=True, loads=True, guards=True))
    originals.update(mobile_originals)
    for file, text in changes.items():
        (candidate / file).write_text(text)
    (candidate / 'engine/pokedex/performance_idle.asm').unlink()
    gfx_archive = candidate / 'gfx/archived/pokedex'
    gfx_archive.mkdir(parents=True)
    graphics = []
    for stem in ('slowpoke', 'pokedex_sgb'):
        for ext in ('png', '2bpp', '2bpp.lz'):
            source = candidate / f'gfx/pokedex/{stem}.{ext}'
            destination = gfx_archive / source.name
            graphics.append(dict(original=str(source.relative_to(candidate)),
                                 archived=str(destination.relative_to(candidate)),
                                 sha256=sha256(source.read_bytes())))
            shutil.move(source, destination)
    page = (candidate / 'gfx/pokedex/pokedex_page_numbers.2bpp').read_bytes()
    (gfx_archive / 'unused_info_page_numbers.2bpp').write_bytes(page[6 * 16:10 * 16])
    shutil.copy2(candidate / 'gfx/pokedex/pokedex_page_numbers.png',
                 gfx_archive / 'info_page_numbers_source.png')
    make = candidate / 'Makefile'
    text = make.read_text().replace('gfx/pokedex/pokedex_sgb.2bpp: tools/gfx += --trim-whitespace\n', '')
    needle = 'gfx/pokedex/slowpoke.2bpp: tools/gfx += --trim-whitespace\n'
    assert text.count(needle) == 1
    text = text.replace(needle, 'gfx/archived/pokedex/slowpoke.2bpp: tools/gfx += --trim-whitespace\n'
        'gfx/pokedex/slowpoke_dex.2bpp: gfx/archived/pokedex/slowpoke.2bpp\n'
        '\tdd if=$< of=$@ bs=16 count=48\n')
    make.write_text(text)
    ignore = candidate / '.gitignore'
    ignore.write_text(ignore.read_text() + '\n# Exact retired graphics retained for future reuse\n'
        '!gfx/archived/pokedex/*.2bpp\n!gfx/archived/pokedex/*.2bpp.lz\n')
    for file in ('Makefile', '.gitignore'):
        originals[file] = (BASE / file).read_text()
        changes[file] = (candidate / file).read_text()
    (gfx_archive / 'README.md').write_text((ROOT / 'tools/dex_timing/probes/dex_graphics_archive.md').read_text())
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', '-W', 'main.asm', '-W', 'ram.asm', 'pokecrystal.gbc'],
                       cwd=candidate, stdout=log, stderr=subprocess.STDOUT, check=True)
    before, after = resources(BASE / 'pokecrystal.map'), resources(candidate / 'pokecrystal.map')
    reclaimed = {key: value - after[key] for key, value in before.items()}
    assert reclaimed == dict(ROM0=0, ROMX=2970, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0), reclaimed
    symbols = read_symbols(candidate / 'pokecrystal.sym')
    prior_symbols = read_symbols(BASE / 'pokecrystal.sym')
    moved = [name for name, pair in prior_symbols.items() if pair[1] >= 0xa000
             and name in symbols and pair != symbols[name]]
    assert not moved, moved
    for stem in ('pokecrystal-dex-cleanup', 'pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime',
                 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'{stem}.{ext}')
        shutil.copy2(ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav',
                     output / f'{stem}.sav')
    patch = ''.join(line for file in sorted(changes) for line in difflib.unified_diff(
        originals[file].splitlines(keepends=True), changes[file].splitlines(keepends=True),
        fromfile='a/' + file, tofile='b/' + file))
    (output / 'cleanup-from-accepted.patch').write_text(patch)
    assert all(sha256(Path(path).read_bytes()) == digest for path, digest in protected.items())
    baseline = resources(rollback / 'pokecrystal.map')
    result = dict(candidate=str(candidate), rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                  baseline_sha256=protected[str(ROOT / 'pokecrystal.gbc')],
                  reclaimed_from_accepted=reclaimed,
                  net_delta_from_production={key: after[key] - value for key, value in baseline.items()},
                  moved_ram_labels=moved, archived_graphics=graphics, protected=protected,
                  qualification='Fresh build only; full regression pending')
    (output / 'cleanup-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs)
