"""Checksum-verified private live-roamer fixture for the Area performance test."""
import argparse
import json
from pathlib import Path
import re

from .assets import Repository, sha256
from .cold_listing import ROOT
from .cry_ownership import validate_output


def fixture(repo, source, output):
    output = validate_output(output, (source, ROOT / 'pokecrystal.sav'))
    before = source.read_bytes()
    data = bytearray(before)
    symbols = repo.symbols
    allowed, assigned = set(), {}

    def saved(name):
        bank, address = symbols[name]
        return bank * 8192 + address - 0xa000

    maps, group, number = {}, 0, 0
    for line in (ROOT / 'constants/map_constants.asm').read_text().splitlines():
        if re.match(r'^\s*newgroup\s+', line):
            group, number = group + 1, 0
        match = re.match(r'^\s*map_const\s+(\w+),', line)
        if match:
            number += 1
            maps[match[1]] = group, number
    constants = re.findall(r'^\s*const\s+(\w+)',
                           (ROOT / 'constants/pokemon_constants.asm').read_text(), re.M)
    count = (symbols['wPokemonIndexTableEntriesEnd'][1]
             - symbols['wPokemonIndexTableEntries'][1]) // 2
    entries = symbols['wPokemonIndexTableEntries'][1] - symbols['wPokemonIndexTable'][1]

    def write(at, value):
        data[at:at + len(value)] = value
        allowed.update(range(at, at + len(value)))

    for prefix in ('s', 'sBackup'):
        start, end = saved(prefix + 'SaveData'), saved(prefix + 'SaveDataEnd')
        checksum = saved(prefix + 'Checksum')
        if sum(before[start:end]) & 65535 != int.from_bytes(before[checksum:checksum + 2], 'little'):
            raise ValueError('Invalid source save checksum')
        table = saved(prefix + 'PokemonIndexTable')
        base = table + entries
        values = [int.from_bytes(data[base + i * 2:base + i * 2 + 2], 'little')
                  for i in range(count)]
        for roamer, name, route in ((1, 'RAIKOU', 'ROUTE_42'), (2, 'ENTEI', 'ROUTE_37')):
            # Saved roamer species are transient table IDs, not National indexes.
            index = constants.index(name) + 1
            if index not in values:
                slot = values.index(0)
                values[slot] = index
                write(base + slot * 2, index.to_bytes(2, 'little'))
            transient = values.index(index) + 1
            assigned[prefix + name] = transient
            group, number = maps[route]
            for field, value in (('Species', transient), ('Level', 40),
                                 ('MapGroup', group), ('MapNumber', number)):
                at = (saved(prefix + 'PokemonData')
                      + symbols[f'wRoamMon{roamer}{field}'][1] - symbols['wPokemonData'][1])
                write(at, bytes((value,)))
        write(table, bytes((sum(bool(v) for v in values),)))
        write(checksum, (sum(data[start:end]) & 65535).to_bytes(2, 'little'))
        if sum(data[start:end]) & 65535 != int.from_bytes(data[checksum:checksum + 2], 'little'):
            raise ValueError('Fixture checksum failure')
    changed = {i for i, pair in enumerate(zip(before, data)) if pair[0] != pair[1]}
    if not changed <= allowed or len(before) != len(data) or before[0x8000:] != data[0x8000:]:
        raise ValueError('Fixture changed undeclared data')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    if source.read_bytes() != before:
        raise ValueError('Source save changed')
    report = dict(source=str(source), fixture=str(output), source_sha256=sha256(before),
                  fixture_sha256=sha256(data), assigned_ids=assigned,
                  changed_bytes=len(changed), checksums_valid=True, source_unchanged=True)
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--sym', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fixture(Repository(ROOT, args.rom, args.sym), args.source, args.output)))


if __name__ == '__main__':
    main()
