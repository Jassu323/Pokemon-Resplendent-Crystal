"""Portable, hash-bound volatile-memory input for the linked owner replay.

This is not an emulator save state. Cartridge ROM/SRAM and echo/OAM bus reads
are discarded; physical WRAM/VRAM and register values are retained. No PPU or
APU internals, user save file, or later expected state is supplied to the model.
"""
import argparse
import base64
import json
from pathlib import Path
import zlib

from .assets import sha256
from .probes.compare_save_state import read_export


def pack(payload, report):
    read_export(payload)
    sanitized = bytearray(payload)
    sanitized[72:72+0xc000] = bytes(0xc000)
    sanitized[72+0xe000:72+0xff00] = bytes(0x1f00)
    return {'format':'dex-volatile-v1',
            'scope':'actual_initial_volatile_memory_no_later_state_injection',
            **{k:report[k] for k in ('rom_sha256','sym_sha256','state_sha256','core_revision')},
            'initial':report['core_points'][0],
            'payload_sha256':sha256(sanitized),
            'payload_zlib_base85':base64.b85encode(zlib.compress(sanitized,9)).decode('ascii')}


def unpack(document, repo):
    if document['format'] != 'dex-volatile-v1' or any(
            repo.hashes[k] != document[k] for k in repo.hashes):
        raise ValueError('Fixture format/ROM/symbol identity mismatch')
    payload = zlib.decompress(base64.b85decode(document['payload_zlib_base85']))
    read_export(payload)
    if sha256(payload) != document['payload_sha256']:
        raise ValueError('Fixture payload hash mismatch')
    return payload, [document['initial']]


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.resolve() in (args.export.resolve(),args.report.resolve()):
        p.error('Output must not overwrite an input')
    args.output.write_text(json.dumps(pack(args.export.read_bytes(),json.loads(args.report.read_text())),indent=2)+'\n')
    print(f'Packed volatile-memory fixture: {args.output.stat().st_size} bytes')
