"""Measure cleanup against the accepted New Entry snapshot, never production."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess

from .assets import sha256
from .cold_listing import ROOT
from .dex_unused_scope import GROUPS, remove
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-new-entry-visual-20261014-red-footer/candidate'
OUTPUT = ROOT / 'build/dex-unused-post-entry-20261014'


def edit(originals, groups, *, roamer=False, wrap=False, prefix=False, fonts=False,
         mark=False, query=False, compatibility=False, edge=False, adapter=False, shell=False):
    result = dict(originals)
    if shell:
        name = 'engine/pokedex/pokedex.asm'
        result[name] = remove(result[name], 'Pokedex_DrawDexEntryScreenBG', 'Pokedex_DrawOptionScreenBG')
    for group in groups:
        for file, first, last in GROUPS[group]:
            result[file] = remove(result[file], first, last)
    if roamer:
        name = 'engine/overworld/wildmons.asm'
        text = result[name]
        start, end = text.index('FindNest:\n'), text.index('.AppendNest:\n')
        result[name] = text[:start] + 'FindNest:\n' + text[end:]
        name = 'engine/pokedex/pokedex_3.asm'
        result[name] = remove(result[name], 'Pokedex_PrepareGridCacheRefill', 'Pokedex_PrepareGridCacheRow')
    if wrap:
        name = 'engine/pokedex/pokedex_animation.asm'
        result[name] = result[name].replace('\tfarcall Pokedex_FinalizeWrappedGridCache\n', '')
        name = 'engine/pokedex/pokedex_3.asm'
        end = 'LoadQuestionMarkPic' if 'old-grid-refill' in groups else 'PokedexPerf_LegacyFinalizeWrappedGridCache'
        result[name] = remove(result[name], 'Pokedex_FinalizeWrappedGridCache', end)
    if prefix:
        name = 'engine/pokedex/pokedex.asm'
        result[name] = result[name].replace('INCBIN "gfx/pokedex/slowpoke.2bpp.lz"',
                                          'INCBIN "build/slowpoke-dex-prefix.lz"')
    if fonts:
        name = 'engine/pokedex/pokedex.asm'
        start = result[name].index('_NewPokedexEntry:\n')
        tail = result[name][start:]
        needle = '\tcall DisableLCD\n\tcall LoadStandardFont\n\tcall LoadFontsExtra\n'
        assert tail.count(needle) == 1
        result[name] = result[name][:start] + tail.replace(needle, '', 1)
    if mark:
        name = 'engine/pokedex/move_acquisition.asm'
        result[name] = remove(result[name], 'MoveDiscovery_MarkMoveList', 'MoveDiscovery_Learned')
    if query:
        name = 'engine/pokedex/move_discovery.asm'
        result[name] = remove(result[name], 'MoveDiscovery_CheckIndex', 'MoveDiscovery_MarkIndex')
    if compatibility:
        name = 'engine/pokedex/pokedex.asm'
        text = result[name].replace('\tcall Pokedex_CheckSGB\n\tjr nz, .LoadPokedexLZ\n\tfarcall LoadSGBPokedexGFX\n\tjr .LoadPokedexSlowpokeLZ\n', '')
        start = text.index('\tldh a, [hCGB]\n', text.index('Pokedex_UpdateUnownMode:'))
        end = text.index('.done\n\tret\n', start)
        result[name] = remove(text[:start] + text[end:], 'Pokedex_CheckSGB', 'Pokedex_LoadUnownFont')
        name = 'engine/pokedex/pokedex_3.asm'
        result[name] = result[name][result[name].index('ASSERT POKEDEX_GRID_CENTER_GFX'):]
    if edge:
        name = 'engine/pokedex/pokedex_description.asm'
        text = result[name]
        start, end = text.index('Pokedex_InitListingRightEdge:\n'), text.index('Pokedex_CopyDescriptionRightEdge:\n')
        section = text[start:end].replace('\tldh a, [hCGB]\n\tand a\n\tjr z, .compat\n', '')
        section = section[:section.index('.compat\n')]
        result[name] = text[:start] + section + '\n' + text[end:]
        name = 'engine/pokedex/pokedex_3.asm'
        result[name] = remove(result[name], 'DrawDexEntryScreenRightEdge', 'Pokedex_FillColumn2')
    if adapter:
        name = 'engine/pokedex/new_entry_visual.asm'
        text = result[name]
        start = text.index('\tldh a, [hCGB]\n')
        end = text.index('\n.cgb\n', start) + len('\n.cgb\n')
        result[name] = text[:start] + text[end:]
    return result


def run(base, output, jobs):
    target = output / 'trials'
    if target.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a new private trial directory under build/')
    target.mkdir(parents=True)
    candidate = target / 'candidate'
    shutil.copytree(base, candidate, ignore=shutil.ignore_patterns('*.o', '*.d', '*.orig', '*.rej'))
    files = {file for blocks in GROUPS.values() for file, _, _ in blocks}
    files.update(('engine/overworld/wildmons.asm', 'engine/pokedex/pokedex_description.asm',
                  'engine/pokedex/new_entry_visual.asm', 'main.asm'))
    originals = {name: (base / name).read_text() for name in files}
    raw = (base / 'gfx/pokedex/slowpoke.2bpp').read_bytes()[:48 * 16]
    compressed = subprocess.check_output([str(ROOT / 'tools/lzcomp'), '-b', '-', '-'], input=raw)
    assert subprocess.check_output([str(ROOT / 'tools/lzcomp'), '-u', '-', '-'], input=compressed) == raw
    (candidate / 'build/slowpoke-dex-prefix.lz').write_bytes(compressed)
    safe = [group for group in GROUPS if group != 'test-only-discovery-apis']
    variants = [dict(name='baseline-control', groups=[]), dict(name='old-registration-shell', groups=[]),
                dict(name='all-unreachable', groups=safe, roamer=True),
                dict(name='code-recommended', groups=safe, roamer=True, wrap=True),
                dict(name='code-plus-slowpoke', groups=safe, roamer=True, wrap=True, prefix=True),
                dict(name='mark-wrapper', groups=[], mark=True),
                dict(name='query-api', groups=[], query=True),
                dict(name='duplicate-registration-setup', groups=[], fonts=True),
                dict(name='sgb-policy', groups=[], compatibility=True),
                dict(name='listing-edge-cgb-policy', groups=[], edge=True),
                dict(name='new-entry-adapter-cgb-policy', groups=[], adapter=True),
                dict(name='all-cgb-policy', groups=[], compatibility=True, edge=True, adapter=True),
                dict(name='recommended-plus-mark', groups=safe, roamer=True, wrap=True, prefix=True, mark=True)]
    before = resources(base / 'pokecrystal.map')
    protected = {str(p): sha256(p.read_bytes()) for p in
                 (ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map', base / 'pokecrystal.gbc')}
    rows = []
    for variant in variants:
        name = variant['name']
        options = {k: v for k, v in variant.items() if k != 'name'}
        options['shell'] = name == 'old-registration-shell' or variant.get('roamer', False)
        changes = edit(originals, **options)
        if 'old-batch-guard' in variant['groups']:
            changes['main.asm'] = changes['main.asm'].replace('INCLUDE "engine/pokedex/performance_idle.asm"\n', '')
        # Explicit mechanical deletions only in the private snapshot.
        for file, contents in changes.items():
            (candidate / file).write_text(contents)
        for object_ in ('main.o', 'ram.o'):
            (candidate / object_).unlink(missing_ok=True)
        log = target / f'{name}.log'
        with log.open('w') as stream:
            result = subprocess.run(['make', '-s', f'-j{jobs}', '-W', 'main.asm', '-W', 'ram.asm', 'pokecrystal.gbc'],
                                    cwd=candidate, stdout=stream, stderr=subprocess.STDOUT)
        row = dict(name=name, build_exit_code=result.returncode, options=variant)
        if not result.returncode:
            row['reclaimed'] = {k: v - resources(candidate / 'pokecrystal.map')[k] for k, v in before.items()}
            row['rom_sha256'] = sha256((candidate / 'pokecrystal.gbc').read_bytes())
            for ext in ('gbc', 'sym', 'map'):
                shutil.copy2(candidate / f'pokecrystal.{ext}', target / f'{name}.{ext}')
            if name == 'baseline-control':
                assert row['rom_sha256'] == protected[str(base / 'pokecrystal.gbc')], 'Control link changed'
            patch = ''.join(line for file in sorted(changes) for line in difflib.unified_diff(
                originals[file].splitlines(keepends=True), changes[file].splitlines(keepends=True),
                fromfile='a/' + file, tofile='b/' + file))
            (target / f'{name}.patch').write_text(patch)
        else:
            row['diagnostic'] = log.read_text()[-3000:]
        rows.append(row)
        (target / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)
    assert all(sha256(Path(p).read_bytes()) == digest for p, digest in protected.items())
    (output / 'manifest.json').write_text(json.dumps(dict(base=str(base), baseline=before,
        protected=protected, qualification='Private build/link measurements only; runtime suite not run'), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    run(args.base.resolve(), args.output.resolve(), args.jobs)
