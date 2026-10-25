"""Add discoveries without altering core save data, existing flags or RTC bytes."""
import argparse
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import random
import re
import tempfile

from dex_timing.assets import read_symbols, sha256
from dex_timing.move_persistence import core_valid
from move_discovery_assets import address, decode_record, identity, seed_records

ROOT = Path(__file__).resolve().parents[1]


def catalogue():
    text = (ROOT / 'constants/move_constants.asm').read_text().split('DEF NUM_ATTACKS')[0]
    return [name for name in re.findall(r'^\s*const\s+(\w+)', text, re.M) if name != 'NO_MOVE']


def inspect(data, symbols, total):
    if len(data) < 32768:
        raise ValueError('Battery is shorter than the cartridge SRAM')
    records = {}
    for prefix in ('s', 'sBackup'):
        if not core_valid(data, symbols, prefix):
            raise ValueError(f'{prefix} core/conversion checksum is invalid')
        record = decode_record(data, symbols, prefix)
        if record['status'] != 'valid':
            raise ValueError(f'{prefix} discovery record is {record["status"]}; migrate/repair first')
        records[prefix] = record['bitmap']
    if identity(data, symbols, 's') != identity(data, symbols, 'sBackup'):
        raise ValueError('Primary and backup belong to different player identities')
    merged = bytes(a | b for a, b in zip(records['s'], records['sBackup']))
    seen = [n for n in range(1, total + 1) if merged[(n - 1) // 8] & 1 << ((n - 1) & 7)]
    return merged, seen


def update(data, symbols, total, fraction, seed):
    fraction = Fraction(fraction)
    if not 0 <= fraction <= 1 or not 1 <= total <= 512:
        raise ValueError('Invalid fraction or move count')
    bitmap, seen = inspect(data, symbols, total)
    target = math.ceil(total * fraction)
    unseen = [n for n in range(1, total + 1) if n not in seen]
    added = random.Random(seed).sample(unseen, max(0, target - len(seen)))
    flags = bytearray(bitmap)
    for n in added:
        flags[(n - 1) // 8] |= 1 << ((n - 1) & 7)
    result = seed_records(data, symbols, bytes(flags))
    allowed = {address(symbols, prefix + 'MoveDiscovery') + n
               for prefix in ('s', 'sBackup') for n in range(72)}
    changed = [n for n, (old, new) in enumerate(zip(data, result)) if old != new]
    if len(result) != len(data) or set(changed) - allowed:
        raise AssertionError('Update changed bytes outside the two discovery records')
    after_bitmap, after = inspect(result, symbols, total)
    if any(old & new != old for old, new in zip(bitmap, after_bitmap)):
        raise AssertionError('Existing flags were cleared')
    if len(after) != max(target, len(seen)):
        raise AssertionError('Wrong final discovery count')
    return result, dict(total=total, before=len(seen), after=len(after), added=sorted(added),
                        requested_target=target, percent=100 * len(after) / total,
                        changed_bytes=len(changed), existing_flags_preserved=True,
                        core_and_rtc_unchanged=True, both_records_valid=True, seed=seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'apply'))
    parser.add_argument('--save', type=Path, required=True)
    parser.add_argument('--symbols', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--fraction', default='0.60')
    parser.add_argument('--seed', type=int, default=20261013)
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    symbols = read_symbols(args.symbols)
    source = args.save.resolve()
    before = source.read_bytes()
    names = catalogue()
    if args.action == 'inspect':
        _, seen = inspect(before, symbols, len(names))
        print(json.dumps(dict(path=str(source), total=len(names), seen=len(seen),
                              percent=100 * len(seen) / len(names), sha256=sha256(before))))
        return
    if args.backup is None or args.backup.exists():
        raise ValueError('Choose a new backup file before replacing the battery')
    after, record = update(before, symbols, len(names), args.fraction, args.seed)
    args.backup.parent.mkdir(parents=True, exist_ok=True)
    args.backup.write_bytes(before)
    if source.read_bytes() != before:
        raise RuntimeError('Live battery changed; close the emulator and retry with a new backup')
    handle, temporary = tempfile.mkstemp(prefix=source.name + '.', suffix='.tmp', dir=source.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, source.stat().st_mode & 0o777)
        os.replace(temporary, source)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    if source.read_bytes() != after or args.backup.read_bytes() != before:
        raise AssertionError('Written battery/backup does not match verified bytes')
    record.update(path=str(source), backup=str(args.backup), before_sha256=sha256(before),
                  after_sha256=sha256(after), added_names=[names[n - 1] for n in record['added']])
    args.backup.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k not in ('added', 'added_names')}, indent=2))


if __name__ == '__main__':
    main()
