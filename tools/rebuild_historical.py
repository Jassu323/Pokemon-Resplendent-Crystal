"""Inspect/restore historical build recipes without touching production or saves.

Basic use: --list, or --id NAME --output /private/tmp/reproduction.
--build-reference builds the frozen instrumented source in that isolated output.
--build-source rebuilds a recorded Git/source baseline and verifies its ROM hash.
--overlay reconstructs a supported private cartridge from a hash-matching base.
Other experiments use the preserved script/module and recorded parameter grid;
this tool deliberately does not invent missing save states or timer phases.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'tools/dex_timing/historical_builds'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_symbols(path):
    result = {}
    for line in path.read_text().splitlines():
        if match := re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]+)\s+(\S+)', line):
            result[match[3]] = int(match[1], 16), int(match[2], 16)
    return result


def offset(symbol):
    bank, pc = symbol
    return bank * 0x4000 + pc - (0x4000 if bank else 0)


def restore_sources(record, output):
    if output.resolve() == ROOT or ROOT in output.resolve().parents and output.name in ('tools', 'engine', 'docs'):
        raise ValueError('Use an isolated output directory')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be new or empty')
    output.mkdir(parents=True, exist_ok=True)
    source = ARCHIVE / record['name'] / 'sources'
    if source.exists():
        shutil.copytree(source, output / 'sources')
    (output / 'recipe.json').write_text(json.dumps(record, indent=2) + '\n')


def build_source(manifest, record, output, jobs, reference=False):
    if reference:
        if record['name'] != 'dex-scheduler-reference-20260920':
            raise ValueError('--build-reference requires the frozen reference ID')
        commit = manifest['reference_commit']
    else:
        commit = record.get('source_commit')
        if not commit:
            raise ValueError('This ID has no recorded Git/source baseline')
    source = output / 'checkout'
    source.mkdir()
    blob = subprocess.check_output(['git', 'archive', commit], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        archive.extractall(source, filter='data')
    shutil.copytree(output / 'sources', source, dirs_exist_ok=True)
    subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=source, check=True)
    expected = record['identities'].get('pokecrystal.gbc')
    actual = sha(source / 'pokecrystal.gbc')
    if not expected or actual != expected:
        raise ValueError(f'Historical source ROM mismatch: expected {expected}, got {actual}')
    print(json.dumps(dict(rom=str(source / 'pokecrystal.gbc'), sha256=actual, matching_historical_rom=True)))


def overlay(record, output, base_rom, base_sym):
    metadata = record.get('outcomes', {}).get('builds.json')
    if not metadata or 'accepted_sha256' not in metadata:
        raise ValueError('This ID has no supported fixed-address cartridge overlay; use its archived recipe')
    if sha(base_rom) != metadata['accepted_sha256']:
        raise ValueError('Overlay base ROM hash mismatch; never patch a different link')
    sources = output / 'sources'
    bindings = sources / 'private-overlay.asm'
    if not bindings.exists():
        raise ValueError('The overlay binding source is missing')
    text = re.sub(r'INCLUDE "[^"]*/([^/"]+)"', r'INCLUDE "\1"', bindings.read_text())
    bindings.write_text(text)
    obj, binary, symbols = [output / ('overlay.' + suffix) for suffix in ('o', 'bin', 'sym')]
    subprocess.run(['rgbasm', '-o', str(obj), str(bindings)], cwd=sources, check=True)
    subprocess.run(['rgblink', '-o', str(binary), '-n', str(symbols), str(obj)], check=True)
    linked, image = binary.read_bytes(), bytearray(base_rom.read_bytes())
    labels = read_symbols(symbols)
    if 'helper_sizes' in metadata:
        blocks = [(name, name.removesuffix('Start') + 'End') for name in metadata['helper_sizes']]
    else:
        blocks = [('PrototypeSelectiveMask', 'PrototypeSelectiveMaskEnd')]
    for begin, end in blocks:
        a, b = offset(labels[begin]), offset(labels[end])
        if len(set(image[a:b])) != 1 or image[a] not in (0, 255):
            raise ValueError('Overlay would replace used ROM bytes')
        image[a:b] = linked[a:b]
    if isinstance(metadata.get('patches'), list):
        for patch in metadata['patches']:
            at = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            if image[at:at + len(before)] != before or len(before) != len(after):
                raise ValueError('Overlay patch site differs from the recorded base')
            image[at:at + len(after)] = after
    else:
        base_labels = read_symbols(base_sym)
        a, b = [offset(base_labels[name]) for name in ('Pokedex_BlackOutSelectedMonBG', 'Pokedex_VBlankDispatch')]
        bank, pc = base_labels['Pokedex_BlackOutBG']
        rst = 0xc7 + base_labels['FarCall'][1]
        before = bytes((0x3e, bank, 0x21, pc & 255, pc >> 8, rst))
        if bytes(image[a:b]).count(before) != 1:
            raise ValueError('Selective-mask caller does not match')
        at = a + bytes(image[a:b]).index(before)
        bank, pc = labels['PrototypeSelectiveMask']
        image[at:at + 6] = bytes((0x3e, bank, 0x21, pc & 255, pc >> 8, rst))
    rom = output / (record['name'] + '.gbc')
    rom.write_bytes(image)
    subprocess.run(['rgbfix', '-v', str(rom)], check=True)
    symbols = rom.with_suffix('.sym')
    symbols.write_text(base_sym.read_text() + '\n' + '\n'.join(
        f'{bank:02x}:{pc:04x} {name}' for name, (bank, pc) in labels.items() if name.startswith('Prototype')) + '\n')
    actual = sha(rom)
    if actual != metadata['prototype_sha256']:
        raise ValueError('Reconstructed overlay hash differs from the recorded prototype')
    print(json.dumps(dict(rom=str(rom), symbols=str(symbols), sha256=actual, matching_historical_rom=True)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--id')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--build-reference', action='store_true')
    parser.add_argument('--build-source', action='store_true')
    parser.add_argument('--overlay', action='store_true')
    parser.add_argument('--base-rom', type=Path)
    parser.add_argument('--base-sym', type=Path)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
    records = {record['name']: record for record in manifest['records']}
    if args.list:
        print('\n'.join(records))
        return
    if args.id not in records:
        parser.error('Choose an archived ID from --list')
    if args.jobs < 1 or sum((args.build_reference, args.build_source, args.overlay)) > 1:
        parser.error('Choose one build mode and a positive worker count')
    record = records[args.id]
    if args.output:
        restore_sources(record, args.output.resolve())
    if args.build_reference or args.build_source:
        if not args.output:
            parser.error('Source builds require --output')
        build_source(manifest, record, args.output.resolve(), args.jobs, args.build_reference)
    elif args.overlay:
        if not args.output or not args.base_rom or not args.base_sym:
            parser.error('--overlay requires --output, --base-rom and --base-sym')
        overlay(record, args.output.resolve(), args.base_rom.resolve(), args.base_sym.resolve())
    else:
        print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
