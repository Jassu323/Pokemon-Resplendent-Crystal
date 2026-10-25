#!/usr/bin/env python3
"""Verify the candidate min/max 2-bit pair lookup against every cry asset."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import os
import pathlib
import re
import sys


TABLE_START = "SampledCryMinMax2PairLookup"
TABLE_END = "SampledCryMinMax2PairLookupEnd"
TABLE_SIZE = 0x1000
BLOCK_SIZE = 9
DECODED_BYTES_PER_BLOCK = 16


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument("--rom", type=pathlib.Path, required=True)
	parser.add_argument("--sym", type=pathlib.Path, required=True)
	parser.add_argument("--assets", type=pathlib.Path, required=True)
	parser.add_argument(
		"--jobs",
		type=int,
		default=min(os.cpu_count() or 1, 8),
		help="parallel asset checks (default: up to 8)",
	)
	return parser.parse_args()


def load_reference_decoder(tools_dir: pathlib.Path):
	spec = importlib.util.spec_from_file_location("wav2pcm4", tools_dir / "wav2pcm4.py")
	if spec is None or spec.loader is None:
		raise RuntimeError("could not load tools/wav2pcm4.py")
	module = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = module
	spec.loader.exec_module(module)
	return module.decode_minmax2, module.minmax2_levels


def read_symbol(path: pathlib.Path, symbol: str) -> tuple[int, int]:
	pattern = re.compile(rf"^([0-9a-fA-F]+):([0-9a-fA-F]+) {re.escape(symbol)}$")
	for line in path.read_text(encoding="utf-8").splitlines():
		match = pattern.match(line)
		if match:
			return int(match.group(1), 16), int(match.group(2), 16)
	raise ValueError(f"missing symbol {symbol} in {path}")


def rom_offset(bank: int, address: int) -> int:
	if bank == 0:
		if not 0 <= address < 0x4000:
			raise ValueError(f"invalid ROM0 address ${address:04x}")
		return address
	if not 0x4000 <= address < 0x8000:
		raise ValueError(f"invalid ROMX address ${bank:02x}:${address:04x}")
	return bank * 0x4000 + address - 0x4000


def extract_table(rom_path: pathlib.Path, sym_path: pathlib.Path) -> tuple[bytes, int, int]:
	start_bank, start_address = read_symbol(sym_path, TABLE_START)
	end_bank, end_address = read_symbol(sym_path, TABLE_END)
	if start_bank != end_bank:
		raise ValueError("lookup table crosses a ROM bank")
	if end_address - start_address != TABLE_SIZE:
		raise ValueError(
			f"lookup table is {end_address - start_address} bytes; expected {TABLE_SIZE}"
		)
	if start_address & 0x0FFF:
		raise ValueError(f"lookup table is not 4 KiB aligned: ${start_address:04x}")
	offset = rom_offset(start_bank, start_address)
	rom = rom_path.read_bytes()
	table = rom[offset : offset + TABLE_SIZE]
	if len(table) != TABLE_SIZE:
		raise ValueError("lookup table extends beyond the ROM image")
	return table, start_bank, start_address


def verify_exhaustive(table: bytes, minmax2_levels) -> int:
	comparisons = 0
	for header in range(0x100):
		levels = minmax2_levels(header >> 4, header & 0x0F)
		base = header << 4
		for selectors in range(0x100):
			expected_first = (
				(levels[(selectors >> 6) & 0x03] << 4)
				| levels[(selectors >> 4) & 0x03]
			)
			expected_second = (
				(levels[(selectors >> 2) & 0x03] << 4)
				| levels[selectors & 0x03]
			)
			actual_first = table[base | (selectors >> 4)]
			actual_second = table[base | (selectors & 0x0F)]
			if (actual_first, actual_second) != (expected_first, expected_second):
				raise ValueError(
					"lookup mismatch at "
					f"header ${header:02x}, selectors ${selectors:02x}: "
					f"expected ${expected_first:02x} ${expected_second:02x}, "
					f"got ${actual_first:02x} ${actual_second:02x}"
				)
			comparisons += 1
	return comparisons


def pack_nibbles(nibbles: list[int]) -> bytes:
	if len(nibbles) % 2:
		raise ValueError("reference decoder returned an odd nibble count")
	return bytes(
		(nibbles[index] << 4) | nibbles[index + 1]
		for index in range(0, len(nibbles), 2)
	)


def decode_with_lookup(payload: bytes, table: bytes) -> bytes:
	if len(payload) % BLOCK_SIZE:
		raise ValueError("min/max 2-bit payload must be a multiple of 9 bytes")
	decoded = bytearray()
	for block_offset in range(0, len(payload), BLOCK_SIZE):
		base = payload[block_offset] << 4
		for selectors in payload[block_offset + 1 : block_offset + BLOCK_SIZE]:
			decoded.append(table[base | (selectors >> 4)])
			decoded.append(table[base | (selectors & 0x0F)])
	return bytes(decoded)


def verify_asset(path: pathlib.Path, table: bytes, tools_dir: pathlib.Path) -> tuple[str, int, int]:
	decode_minmax2, _ = load_reference_decoder(tools_dir)
	payload = path.read_bytes()
	if len(payload) % BLOCK_SIZE:
		raise ValueError(f"{path}: size {len(payload)} is not divisible by {BLOCK_SIZE}")
	expected = pack_nibbles(decode_minmax2(payload))
	actual = decode_with_lookup(payload, table)
	if actual != expected:
		index = next(index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
		block = index // DECODED_BYTES_PER_BLOCK
		within_block = index % DECODED_BYTES_PER_BLOCK
		raise ValueError(
			f"{path}: mismatch in block {block}, decoded byte {within_block}: "
			f"expected ${expected[index]:02x}, got ${actual[index]:02x}; "
			f"source={payload[block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE].hex()}"
		)
	return path.name, len(payload) // BLOCK_SIZE, len(actual)


def main() -> int:
	args = parse_args()
	if args.jobs < 1:
		raise SystemExit("--jobs must be at least 1")
	tools_dir = pathlib.Path(__file__).resolve().parent
	_, minmax2_levels = load_reference_decoder(tools_dir)
	table, bank, address = extract_table(args.rom, args.sym)
	combinations = verify_exhaustive(table, minmax2_levels)

	assets = sorted(args.assets.glob("*.mm2"))
	if not assets:
		raise ValueError(f"no .mm2 assets found under {args.assets}")
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
		results = list(
			executor.map(
				lambda path: verify_asset(path, table, tools_dir),
				assets,
			)
		)

	total_blocks = sum(result[1] for result in results)
	total_decoded_bytes = sum(result[2] for result in results)
	worker_label = "worker" if args.jobs == 1 else "workers"
	print(
		f"PASS: ROM lookup at ${bank:02x}:${address:04x} matches "
		f"{combinations} header/selector-byte combinations"
	)
	print(
		f"PASS: {len(results)} sampled cries, {total_blocks} compressed blocks, "
		f"{total_decoded_bytes} decoded bytes matched byte-for-byte using "
		f"{args.jobs} {worker_label}"
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
