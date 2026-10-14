"""Audit retired mobile Slowpoke copies in a private, matching-link build."""
import argparse
import difflib
import json
from pathlib import Path
import re
import shutil
import subprocess

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from .dex_unused_scope import LABEL, TOKEN, UNITS, clean
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-new-entry-visual-20261014-red-footer/candidate'
OUTPUT = ROOT / 'build/dex-mobile-slowpoke-audit-20261014'
FILES = ('mobile/fixed_words.asm', 'mobile/mobile_5c.asm',
         'mobile/mobile_45_stadium.asm')
COPIES = (('mobile/fixed_words.asm', 'EZChatSlowpokeLZ', 'MobileEZChatCategoryNames'),
          ('mobile/mobile_5c.asm', 'PasswordSlowpokeLZ', 'String_172e31'))
GUARDS = (('mobile/fixed_words.asm', 'Function11c1ab', 'Function11c1b9'),
          ('mobile/mobile_45_stadium.asm', 'Function11765d', 'Function11766b'),
          ('mobile/mobile_5c.asm', 'Function1719c8', 'Function1719d6'))


def edit(originals, *, assets=False, loads=False, guards=False):
    result = dict(originals)
    if assets:
        for file, label, _ in COPIES:
            needle = f'{label}:\nINCBIN "gfx/pokedex/slowpoke.2bpp.lz"\n'
            assert result[file].count(needle) == 1, label
            result[file] = result[file].replace(needle, '')
    if loads:
        for file, label, _ in COPIES:
            needle = f'\tld hl, {label}\n\tld de, vTiles0'
            if label == 'PasswordSlowpokeLZ':
                needle += ' tile $00'
            needle += '\n\tcall Decompress\n'
            expected = 1 if label == 'EZChatSlowpokeLZ' else 2
            assert result[file].count(needle) == expected, label
            result[file] = result[file].replace(needle, '')
    if guards:
        for file, first, last in GUARDS:
            start = result[file].index(f'{first}:\n')
            end = result[file].index(f'{last}:\n', start)
            comment = '; Retired mobile screen; preserve public entry IDs. See docs/battle_tower_regression_suite.md.\n'
            result[file] = result[file][:start] + comment + f'{first}:\n\tret\n\n' + result[file][end:]
    return result


def included_files(base):
    pending, included = list(UNITS), set()
    while pending:
        name = pending.pop()
        if name in included or not (base / name).is_file():
            continue
        included.add(name)
        pending.extend(re.findall(r'^\s*INCLUDE\s+"([^"]+)"',
                                  (base / name).read_text(), re.M))
    return included


def references(base, targets):
    included = included_files(base)
    found = {target: [] for target in targets}
    for path in sorted(base.rglob('*.asm')):
        name = path.relative_to(base).as_posix()
        if name.startswith(('build/', 'tools/')):
            continue
        owner = None
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = clean(line)
            match = LABEL.match(code)
            if match:
                owner = match[1]
                code = code[match.end():]
            for token in set(TOKEN.findall(code)) & set(targets):
                found[token].append(dict(file=name, line=number, owner=owner,
                                         included=name in included, code=line.strip()))
    return dict(references=found, mobile_menu_included='mobile/mobile_menu.asm' in included,
                caveat='Include closure and textual operands, not proof of dynamic reachability.')


def run(base, output, jobs):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private directory under build/')
    output.mkdir(parents=True)
    candidate = output / 'candidate'
    shutil.copytree(base, candidate, ignore=shutil.ignore_patterns('*.o', '*.d', '*.orig', '*.rej'))
    originals = {name: (base / name).read_text() for name in FILES}
    before = resources(base / 'pokecrystal.map')
    protected = {str(path): sha256(path.read_bytes()) for path in (
        ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map',
        base / 'pokecrystal.gbc', base / 'pokecrystal.sym', base / 'pokecrystal.map')}
    baseline_symbols = read_symbols(base / 'pokecrystal.sym')
    rom = (base / 'pokecrystal.gbc').read_bytes()
    source_blob = (base / 'gfx/pokedex/slowpoke.2bpp.lz').read_bytes()
    copies = []
    for file, label, following in COPIES:
        bank, pc = baseline_symbols[label]
        next_bank, next_pc = baseline_symbols[following]
        assert next_bank == bank
        offset = bank * 0x4000 + pc - 0x4000
        contents = rom[offset:offset + next_pc - pc]
        assert contents == source_blob, label
        copies.append(dict(file=file, label=label, bank=bank, pc=pc,
                           bytes=len(contents), sha256=sha256(contents)))
    targets = [row[1] for row in COPIES] + [row[1] for row in GUARDS]
    targets += ['Function171c87', 'Function171d2b', 'Function11c1b9']
    (output / 'inventory.json').write_text(json.dumps(dict(copies=copies,
        **references(base, targets)), indent=2) + '\n')
    variants = [('baseline-control', {}), ('assets-only-rejected', dict(assets=True)),
                ('assets-and-loads', dict(assets=True, loads=True)),
                ('guarded-retirement', dict(assets=True, loads=True, guards=True))]
    rows = []
    for name, options in variants:
        changes = edit(originals, **options)
        for file, text in changes.items():
            (candidate / file).write_text(text)
        for file in ('main.o', 'ram.o'):
            (candidate / file).unlink(missing_ok=True)
        log = output / f'{name}.log'
        with log.open('w') as stream:
            completed = subprocess.run(['make', '-s', f'-j{jobs}', '-W', 'main.asm',
                                        '-W', 'ram.asm', 'pokecrystal.gbc'], cwd=candidate,
                                       stdout=stream, stderr=subprocess.STDOUT)
        row = dict(name=name, options=options, build_exit_code=completed.returncode)
        patch = ''.join(line for file in FILES for line in difflib.unified_diff(
            originals[file].splitlines(keepends=True), changes[file].splitlines(keepends=True),
            fromfile='a/' + file, tofile='b/' + file))
        (output / f'{name}.patch').write_text(patch)
        if name == 'assets-only-rejected':
            assert completed.returncode != 0, 'Expected dangling asset references'
            row['diagnostic'] = log.read_text()[-6000:]
            assert all(label in row['diagnostic'] for _, label, _ in COPIES)
        else:
            assert completed.returncode == 0, log.read_text()[-4000:]
            row['reclaimed'] = {key: value - resources(candidate / 'pokecrystal.map')[key]
                                for key, value in before.items()}
            row['rom_sha256'] = sha256((candidate / 'pokecrystal.gbc').read_bytes())
            for ext in ('gbc', 'sym', 'map'):
                shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'{name}.{ext}')
            if name == 'baseline-control':
                assert row['rom_sha256'] == protected[str(base / 'pokecrystal.gbc')]
            else:
                symbols = read_symbols(candidate / 'pokecrystal.sym')
                assert all(label not in symbols for _, label, _ in COPIES)
                assert not any(references(candidate, [entry[1] for entry in COPIES])['references'].values())
                assert sha256((candidate / 'gfx/pokedex/slowpoke.2bpp.lz').read_bytes()) == sha256(source_blob)
                if name == 'guarded-retirement':
                    image = (candidate / 'pokecrystal.gbc').read_bytes()
                    for _, label, _ in GUARDS:
                        bank, pc = symbols[label]
                        offset = bank * 0x4000 + pc - 0x4000
                        assert image[offset] == 0xc9, f'Not a RET: {label}'
                    row['retired_entry_opcodes'] = 'Three one-byte RET guards confirmed in linked ROM'
        rows.append(row)
        (output / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)
    assert all(sha256(Path(path).read_bytes()) == digest for path, digest in protected.items())
    (output / 'manifest.json').write_text(json.dumps(dict(base=str(base),
        baseline_resources=before, protected=protected,
        qualification='Private source/reference and build/link audit; no full runtime regression'),
        indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    run(args.base.resolve(), args.output.resolve(), args.jobs)
