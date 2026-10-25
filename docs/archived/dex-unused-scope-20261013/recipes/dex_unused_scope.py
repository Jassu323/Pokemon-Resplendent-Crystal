"""Inventory linked Dex labels and static references in production inputs."""
import json
import difflib
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

from .assets import read_symbols
from .cold_listing import ROOT

OUTPUT = ROOT / 'build/dex-unused-scope-20261013'
UNITS = ('audio.asm', 'home.asm', 'main.asm', 'ram.asm', 'data/text/common.asm',
         'data/maps/map_data.asm', 'data/pokemon/dex_entries.asm',
         'data/pokemon/egg_moves.asm', 'data/pokemon/evos_attacks.asm',
         'engine/movie/credits.asm', 'engine/overworld/events.asm',
         'gfx/misc.asm', 'gfx/pics.asm', 'gfx/sprites.asm', 'gfx/tilesets.asm', 'includes.asm')
LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)(?:::|:)')
TOKEN = re.compile(r'(?<![A-Za-z0-9_.])([A-Za-z_][A-Za-z0-9_]*)(?:\.[A-Za-z0-9_]+)?')


def clean(line):
    # Strings can contain semicolons and apparent symbols; neither is code.
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', line).split(';', 1)[0]


def inventory():
    files = set()
    pending = list(UNITS)
    while pending:
        name = pending.pop()
        if name in files or not (ROOT / name).exists():
            continue
        files.add(name)
        for match in re.finditer(r'^\s*INCLUDE\s+"([^"]+)"', (ROOT / name).read_text(), re.M):
            pending.append(match[1])
    symbols = read_symbols(ROOT / 'pokecrystal.sym')
    blocks, references = [], {}
    for name in sorted(files):
        lines = (ROOT / name).read_text().splitlines()
        labels = [(n, m[1]) for n, line in enumerate(lines) if (m := LABEL.match(clean(line)))]
        current = None
        for number, line in enumerate(lines):
            code = clean(line)
            match = LABEL.match(code)
            if match:
                current = match[1]
                code = code[match.end():]
            for token in TOKEN.findall(code):
                if token in symbols:
                    references.setdefault(token, []).append(dict(file=name, line=number + 1,
                        owner=current, code=line.strip()))
        for index, (line, label) in enumerate(labels):
            if label not in symbols:
                continue
            bank, pc = symbols[label]
            if pc >= 0x8000:
                continue
            end_line = labels[index + 1][0] if index + 1 < len(labels) else len(lines)
            following = next((symbols[n] for _, n in labels[index + 1:]
                              if n in symbols and symbols[n][0] == bank and symbols[n][1] >= pc), None)
            if following:
                end = following[1]
            else:
                # This is only an inventory bound; confirm include/section edges manually.
                end = min((p for n, (b, p) in symbols.items()
                           if b == bank and pc < p < 0x8000 and '.' not in n), default=0x8000)
            blocks.append(dict(label=label, file=name, line=line + 1, end_line=end_line,
                               bank=bank, pc=pc, bytes=end - pc))
    for block in blocks:
        block['references'] = [r for r in references.get(block['label'], [])
                               if r['owner'] != block['label']]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                  inputs=sorted(files), blocks=blocks, references=references,
                  warning='Static references only. Audit fallthrough, macros, dispatch and conditional paths.')
    (OUTPUT / 'inventory.json').write_text(json.dumps(result, indent=2) + '\n')
    candidates = [b for b in blocks if b['file'].startswith('engine/pokedex/') and
                  not b['references'] and b['bytes']]
    print(json.dumps([{k: b[k] for k in ('label', 'file', 'line', 'bytes')} for b in candidates], indent=2))


GROUPS = {
    'old-options': [('engine/pokedex/pokedex.asm', 'Pokedex_DrawOptionScreenBG', 'Pokedex_DrawSearchScreenBG')],
    'old-mode-explanations': [('engine/pokedex/pokedex.asm', 'Pokedex_DisplayModeDescription', 'Pokedex_UpdateSearchMonType')],
    'old-list-printer': [('engine/pokedex/pokedex.asm', 'Pokedex_PrintListing', 'Pokedex_PrintNumberIfOldMode'),
                         ('engine/pokedex/pokedex.asm', 'Pokedex_PlaceCaughtSymbolIfCaught', 'Pokedex_PlaceDefaultStringIfNotSeen')],
    'large-oam-cursors': [('engine/pokedex/pokedex.asm', 'Pokedex_UpdateCursorOAM', 'Pokedex_PutScrollbarOAM')],
    'old-selected-navigation': [('engine/pokedex/pokedex.asm', 'Pokedex_NextOrPreviousDexEntry', 'Pokedex_GridHandleDPadInput')],
    'unused-helper-stubs': [('engine/pokedex/pokedex.asm', 'Pokedex_GetMonAtOrderIndexDE', 'Pokedex_GetSelectionRenderKey'),
                            ('engine/pokedex/pokedex_detail.asm', 'PokedexSelectedMon_Unavailable', 'PokedexSelectedMon_Info')],
    'results-type-text': [('engine/pokedex/pokedex.asm', 'Pokedex_PlaceSearchResultsTypeStrings', 'Pokedex_DrawUnownModeBG')],
    'old-bg-mode-wrappers': [('engine/pokedex/pokedex.asm', 'Pokedex_SetBGMapMode4', 'Pokedex_ResetBGMapMode')],
    'old-animation-stop': [('engine/pokedex/pokedex_animation.asm', 'Pokedex_RestoreBaseFrontpicMap', 'Pokedex_GetAnimationStageMap')],
    'old-grid-refill': [('engine/pokedex/pokedex_3.asm', 'PokedexPerf_LegacyFinalizeWrappedGridCache', 'LoadQuestionMarkPic')],
    'old-batch-guard': [('engine/pokedex/performance_idle.asm', 'PokedexPerf_CanBatch', None)],
    'old-info-copy': [('engine/pokedex/pokedex_info.asm', 'PokedexInfo_CopyTiles_Legacy', 'PokedexInfo_UploadTiles')],
    'unused-page-graphics': [('engine/pokedex/pokedex_description.asm', 'PokedexInfoPageGFX', 'PokedexDescriptionGFX')],
    'orphan-printer-helper': [('engine/pokedex/pokedex_2.asm', 'GetDexEntryPagePointer', 'INCLUDE "data/pokemon/dex_entry_pointers.asm"')],
    'test-only-discovery-apis': [('engine/pokedex/move_discovery.asm', 'MoveDiscovery_CheckIndex', 'MoveDiscovery_MarkIndex'),
                                ('engine/pokedex/move_acquisition.asm', 'MoveDiscovery_MarkMoveList', 'MoveDiscovery_Learned')],
    'unused-strings': [('engine/pokedex/pokedex_2.asm', 'POKeString', 'GetDexEntryPointer')],
}


def remove(text, first, last):
    start = re.search(r'^' + re.escape(first) + r'(?=[:\s]|$)', text, re.M)
    if start is None:
        raise ValueError('Missing start: ' + first)
    if last is None:
        end = len(text)
    else:
        match = re.search(r'^' + re.escape(last) + r'(?=[:\s]|$)', text[start.end():], re.M)
        if match is None:
            raise ValueError('Missing end: ' + last)
        end = start.end() + match.start()
    return text[:start.start()] + text[end:]


def trials():
    from tools.build_dex_unown_prototype import resources
    target = OUTPUT / 'trials'
    existing = target.exists()
    target.mkdir(exist_ok=True)
    archive = target / 'source.tar'
    candidate = target / 'candidate'
    if not existing:
        subprocess.run(['git', 'archive', 'HEAD', '-o', str(archive)], cwd=ROOT, check=True)
        with tarfile.open(archive) as source:
            source.extractall(candidate, filter='data')
        shutil.copytree(ROOT / 'gfx', candidate / 'gfx', dirs_exist_ok=True)
        for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                     'dex-moves-mode-assets', 'dex-sort-assets'):
            shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    elif not (target / 'first-pass-stale-results.json').exists():
        shutil.copy2(target / 'results.json', target / 'first-pass-stale-results.json')
    baseline = resources(ROOT / 'pokecrystal.map')
    files = {name for groups in GROUPS.values() for name, _, _ in groups}
    files.update(('engine/overworld/wildmons.asm', 'ram/wram.asm'))
    source_files = {name: (ROOT / name).read_text() for name in files}
    results = []
    safe = [name for name in GROUPS if name != 'test-only-discovery-apis']
    for group, names in [*( (name, [name]) for name in GROUPS), ('combined-safe', safe),
                         ('combined-with-test-apis', list(GROUPS))]:
        edits = dict(source_files)
        for name in names:
            for file, first, last in GROUPS[name]:
                edits[file] = remove(edits[file], first, last)
        if group in ('unused-strings', 'combined-safe', 'combined-with-test-apis'):
            edits['engine/pokedex/pokedex.asm'] = remove(edits['engine/pokedex/pokedex.asm'], '.Number', '.Height')
        # Bulk mechanical deletion of explicitly inventoried blocks, private only.
        for name, contents in edits.items():
            (candidate / name).write_text(contents)
        for name in ('main.o', 'ram.o'):
            (candidate / name).unlink(missing_ok=True)
        log = target / (group + '.log')
        with log.open('w') as stream:
            # Drop generated objects so rapid private variants cannot reuse a stale link.
            result = subprocess.run(['make', '-s', '-j6', '-W', 'main.asm', '-W', 'ram.asm', 'pokecrystal.gbc'], cwd=candidate,
                                    stdout=stream, stderr=subprocess.STDOUT)
        row = dict(group=group, build_exit_code=result.returncode,
                   groups=names, log=str(log))
        if result.returncode == 0:
            row['reclaimed'] = {k: value - resources(candidate / 'pokecrystal.map')[k]
                                for k, value in baseline.items()}
            for ext in ('gbc', 'sym', 'map'):
                shutil.copy2(candidate / ('pokecrystal.' + ext), target / (group + '.' + ext))
        results.append(row)
        (target / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print(json.dumps(row), flush=True)
        if result.returncode:
            print(log.read_text()[-4000:], flush=True)


def extras():
    from tools.build_dex_unown_prototype import resources
    target = OUTPUT / 'trials'
    candidate = target / 'candidate'
    files = {file for groups in GROUPS.values() for file, _, _ in groups}
    files.update(('engine/overworld/wildmons.asm', 'ram/wram.asm'))
    originals = {name: (ROOT / name).read_text() for name in files}
    raw = (ROOT / 'gfx/pokedex/slowpoke.2bpp').read_bytes()[:48 * 16]
    compressed = subprocess.check_output([str(ROOT / 'tools/lzcomp'), '-b', '-', '-'], input=raw)
    assert subprocess.check_output([str(ROOT / 'tools/lzcomp'), '-u', '-', '-'], input=compressed) == raw
    (candidate / 'build/slowpoke-dex-prefix.lz').write_bytes(compressed)
    baseline = resources(ROOT / 'pokecrystal.map')
    rows = []
    combined = ('combined-unreachable', 'combined-recommended', 'combined-with-asset')
    for group in ('baseline-control', 'refill-chain', 'nest-static-scanner', 'wrap-noop',
                  'erased-registration-footer', 'slowpoke-prefix', 'unused-ram-fields',
                  'sgb-dex-gfx-policy', *combined):
        edits = dict(originals)
        if group == 'refill-chain' or group in combined:
            edits['engine/pokedex/pokedex_3.asm'] = remove(edits['engine/pokedex/pokedex_3.asm'],
                'Pokedex_PrepareGridCacheRefill', 'Pokedex_PrepareGridCacheRow')
            if group == 'refill-chain':
                edits['engine/pokedex/pokedex_3.asm'] = remove(edits['engine/pokedex/pokedex_3.asm'],
                    'PokedexPerf_LegacyFinalizeWrappedGridCache', 'LoadQuestionMarkPic')
        if group == 'nest-static-scanner' or group in combined:
            text = edits['engine/overworld/wildmons.asm']
            start, end = text.index('FindNest:\n'), text.index('.AppendNest:\n')
            edits['engine/overworld/wildmons.asm'] = text[:start] + 'FindNest:\n' + text[end:]
        if group in ('wrap-noop', 'combined-recommended', 'combined-with-asset'):
            edits['engine/pokedex/pokedex_animation.asm'] = edits['engine/pokedex/pokedex_animation.asm'].replace(
                '\tfarcall Pokedex_FinalizeWrappedGridCache\n', '')
            edits['engine/pokedex/pokedex_3.asm'] = remove(edits['engine/pokedex/pokedex_3.asm'],
                'Pokedex_FinalizeWrappedGridCache', 'PokedexPerf_LegacyFinalizeWrappedGridCache')
        if group in ('erased-registration-footer', 'combined-recommended', 'combined-with-asset'):
            text = edits['engine/pokedex/pokedex.asm']
            start, end = text.index('Pokedex_DrawDexEntryScreenBG:'), text.index('Pokedex_DrawOptionScreenBG:')
            section = text[start:end]
            section = section.replace('\thlcoord 0, 17\n\tld de, .MenuItems\n\tcall Pokedex_PlaceString\n', '')
            section = remove(section, '.MenuItems', None)
            edits['engine/pokedex/pokedex.asm'] = text[:start] + section + text[end:]
        if group in ('slowpoke-prefix', 'combined-with-asset'):
            edits['engine/pokedex/pokedex.asm'] = edits['engine/pokedex/pokedex.asm'].replace(
                'INCBIN "gfx/pokedex/slowpoke.2bpp.lz"', 'INCBIN "build/slowpoke-dex-prefix.lz"')
        if group == 'unused-ram-fields':
            for name in ('wBackupDexListingCursor:: db\n', 'wBackupDexListingPage:: dw\n',
                         'wDexLastSeenIndex:: db ; index into wPokedexSeen containing the last non-zero value\n',
                         'wDexLastSeenValue:: db ; value at index\n',
                         '\tds 2 ; retired counter; preserve the established owner/pointer layout\n'):
                assert name in edits['ram/wram.asm']
                edits['ram/wram.asm'] = edits['ram/wram.asm'].replace(name, '')
        if group == 'unused-ram-fields' or group in combined:
            # Remove the already orphaned consumers before measuring RAM cleanup.
            for name in GROUPS:
                if name == 'test-only-discovery-apis':
                    continue
                for file, first, last in GROUPS[name]:
                    edits[file] = remove(edits[file], first, last)
            edits['engine/pokedex/pokedex.asm'] = remove(edits['engine/pokedex/pokedex.asm'], '.Number', '.Height')
        if group == 'sgb-dex-gfx-policy':
            text = edits['engine/pokedex/pokedex.asm']
            text = text.replace('\tcall Pokedex_CheckSGB\n\tjr nz, .LoadPokedexLZ\n\tfarcall LoadSGBPokedexGFX\n\tjr .LoadPokedexSlowpokeLZ\n', '')
            start = text.index('\tldh a, [hCGB]\n', text.index('Pokedex_UpdateUnownMode:'))
            end = text.index('.done\n\tret\n', start)
            text = text[:start] + text[end:]
            edits['engine/pokedex/pokedex.asm'] = remove(text, 'Pokedex_CheckSGB', 'Pokedex_LoadUnownFont')
            text = edits['engine/pokedex/pokedex_3.asm']
            edits['engine/pokedex/pokedex_3.asm'] = text[text.index('ASSERT POKEDEX_GRID_CENTER_GFX'):]
        for name, text in edits.items():
            (candidate / name).write_text(text)
        for name in ('main.o', 'ram.o'):
            (candidate / name).unlink(missing_ok=True)
        log = target / (group + '.log')
        with log.open('w') as stream:
            result = subprocess.run(['make', '-s', '-j6', '-W', 'main.asm', '-W', 'ram.asm',
                                     'pokecrystal.gbc'], cwd=candidate, stdout=stream, stderr=subprocess.STDOUT)
        row = dict(group=group, build_exit_code=result.returncode, log=str(log))
        if result.returncode == 0:
            row['reclaimed'] = {k: v - resources(candidate / 'pokecrystal.map')[k] for k, v in baseline.items()}
            for ext in ('gbc', 'sym', 'map'):
                shutil.copy2(candidate / ('pokecrystal.' + ext), target / (group + '.' + ext))
            patch = []
            for name in sorted(edits):
                patch.extend(difflib.unified_diff(originals[name].splitlines(keepends=True),
                    edits[name].splitlines(keepends=True), fromfile='a/' + name, tofile='b/' + name))
            (target / (group + '.patch')).write_text(''.join(patch))
        rows.append(row)
        (target / 'extras.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)
        if result.returncode:
            print(log.read_text()[-3000:], flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'trials', 'extras'), nargs='?', default='inventory')
    globals()[parser.parse_args().action]()
