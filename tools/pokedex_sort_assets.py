"""Compile private Dex sort tables from the current species/name/order sources."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def compile_tables(root=ROOT, *, records=True):
    source = (root / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0]
    entries = re.findall(r'^\s*const\s+(\w+)\s*;([^\n]*)', source, re.M)
    species = [name for name, _ in entries]
    numbers = {}
    for index, (name, comment) in enumerate(entries, 1):
        match = re.search(r'NatDex\s+(\d+)', comment)
        if index > 251 and not match:
            raise ValueError(f'{name} needs an explicit NatDex number in pokemon_constants.asm')
        numbers[name] = int(match[1]) if match else index
    if len(set(numbers.values())) != len(species):
        raise ValueError('Duplicate National Dex numbers')
    names = re.findall(r'^\s*dname\s+"([^"]+)"',
                       (root / 'data/pokemon/names.asm').read_text().split('PokemonNames::')[1], re.M)
    if len(names) != len(species):
        raise ValueError('Species constants and displayed names disagree')
    new = re.findall(r'^\s*dw\s+(\w+)\s*$',
                     (root / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    if len(new) != len(species) or set(new) != set(species):
        raise ValueError('Family order must contain every species exactly once')
    # Punctuation is ignored; gender tokens retain deterministic female/male order.
    def key(value):
        value = value.replace('<FEMALE>', 'F').replace('<MALE>', 'M')
        return re.sub(r'[^A-Z0-9]', '', value.upper())
    display = dict(zip(species, names))
    alpha = sorted(species, key=lambda name: (key(display[name]), numbers[name]))
    orders = {'NewPokedexOrder': new,
              'NationalPokedexOrder': sorted(species, key=numbers.__getitem__),
              'AlphabeticalPokedexOrder': alpha}
    ids = {name: index for index, name in enumerate(species, 1)}
    lines = ['; Generated from species constants, displayed names and authored family order.']
    for label, order in orders.items():
        lines.append(label + ':')
        lines.extend(f'\tdw {name}' for name in order)
        lines.append(f'ASSERT @ - {label} == NUM_POKEMON * 2')
        if records:
            lines.append(label + 'Records:')
            for name in order:
                flag = ids[name] - 1
                lines.extend((f'\tdw {name}', f'\tdb {flag // 8}, ${1 << (flag % 8):02x}'))
            lines.append(f'ASSERT @ - {label}Records == NUM_POKEMON * 4')
    return '\n'.join(lines) + '\n', dict(species=len(species), orders=orders, national=numbers, names=display)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--without-records', action='store_true')
    args = parser.parse_args()
    text, manifest = compile_tables(args.root, records=not args.without_records)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'tables.asm').write_text(text)
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
