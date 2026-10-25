"""Independent storage-format, rollback, and address-contract checks."""
import binascii
import json
import os
from pathlib import Path
import random
import unittest

from dex_timing.assets import read_symbols, sha256
from dex_timing.cold_listing import ROOT
from move_discovery_assets import address, decode_record, encode_record, move_bitmap, seed_records, rebind_fixture


class DiscoveryStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = Path(os.environ.get('MOVE_DISCOVERY_BUILD', ROOT / 'build/dex-move-persistence-20261007'))
        cls.symbols = read_symbols(cls.build / 'pokecrystal-dex-moves-persistence.sym')
        cls.original = (cls.build / 'legacy-input.sav').read_bytes()

    def test_crc_reference(self):
        self.assertEqual(binascii.crc_hqx(b'123456789', 0xffff), 0x29b1)

    def test_capacity_and_boundaries(self):
        for index in range(1, 513):
            with self.subTest(index=index):
                actual = move_bitmap([index])
                self.assertEqual(sum(byte.bit_count() for byte in actual), 1)
                self.assertEqual(actual[(index - 1) // 8], 1 << ((index - 1) & 7))
        for index in (0, 513, 0xffff):
            with self.assertRaises(ValueError):
                move_bitmap([index])

    def test_fixture_changes_only_padding(self):
        result = seed_records(self.original, self.symbols, move_bitmap([1, 255, 256, 257, 333]))
        allowed = {at for prefix in ('s', 'sBackup') for at in
                   range(address(self.symbols, prefix + 'MoveDiscovery'),
                         address(self.symbols, prefix + 'MoveDiscovery') + 72)}
        changed = {i for i, (a, b) in enumerate(zip(result, self.original)) if a != b}
        self.assertTrue(changed <= allowed)
        self.assertEqual(len(result), 32816)
        self.assertEqual(result[32768:], self.original[32768:])

    def test_roundtrip_patterns(self):
        generator = random.Random(7)
        for pattern in (bytes(64), bytes([255]) * 64, move_bitmap(range(1, 334)),
                        bytes(generator.randrange(256) for _ in range(64))):
            result = seed_records(self.original, self.symbols, pattern)
            for prefix in ('s', 'sBackup'):
                self.assertEqual(decode_record(result, self.symbols, prefix), dict(status='valid', bitmap=pattern))

    def test_every_record_bit_detected(self):
        original = seed_records(self.original, self.symbols, move_bitmap([1, 256, 333]))
        for prefix in ('s', 'sBackup'):
            at = address(self.symbols, prefix + 'MoveDiscovery')
            for bit in range(72 * 8):
                data = bytearray(original)
                data[at + bit // 8] ^= 1 << (bit & 7)
                self.assertNotEqual(decode_record(data, self.symbols, prefix)['status'], 'valid')

    def test_identity_binding(self):
        data = bytearray(seed_records(self.original, self.symbols, bytes(64)))
        for prefix in ('s', 'sBackup'):
            for offset in (0, 1, self.symbols['wSecretID'][1] - self.symbols['wPlayerData'][1],
                           self.symbols['wSecretID'][1] - self.symbols['wPlayerData'][1] + 1):
                altered = data.copy()
                altered[address(self.symbols, prefix + 'PlayerData') + offset] ^= 1
                self.assertEqual(decode_record(altered, self.symbols, prefix)['status'], 'damaged')

    def test_supported_and_unsupported_formats(self):
        for version, length in ((1, 64), (2, 64), (1, 128), (99, 42)):
            data = bytearray(self.original)
            for prefix in ('s', 'sBackup'):
                record = encode_record(data, self.symbols, prefix, bytes(length), version)
                at = address(self.symbols, prefix + 'MoveDiscovery')
                data[at:at + len(record)] = record
                status = 'valid' if (version, length) == (1, 64) else 'unsupported'
                self.assertEqual(decode_record(data, self.symbols, prefix)['status'], status)

    def test_rebinding_only_private_valid_fixtures(self):
        before = seed_records(self.original, self.symbols, move_bitmap([255, 257]))
        after = bytearray(before)
        for prefix in ('s', 'sBackup'):
            after[address(self.symbols, prefix + 'Checksum')] ^= 1
        result = rebind_fixture(before, after, self.symbols)
        for prefix in ('s', 'sBackup'):
            self.assertEqual(decode_record(result, self.symbols, prefix)['bitmap'], move_bitmap([255, 257]))
        self.assertEqual(rebind_fixture(self.original, self.original, self.symbols), self.original)

    def test_exact_allocations(self):
        self.assertEqual(self.symbols['wMoveDiscoverySeen'], (2, 0xd500))
        self.assertEqual(self.symbols['wMoveDiscoveryEnd'], (2, 0xd542))
        self.assertEqual(self.symbols['sMoveDiscovery'], (1, 0xac88))
        self.assertEqual(self.symbols['sBackupMoveDiscovery'], (0, 0xbe88))
        self.assertEqual(self.symbols['sChecksum'], (1, 0xad10))
        self.assertEqual(self.symbols['sBackupChecksum'], (0, 0xbf10))

    def test_review_seed_matches_display_names_case_insensitively(self):
        manifest = json.loads((self.build / 'moves-mode-manifest.json').read_text())
        names = {manifest['moves'][i - 1]['name'].casefold() for i in manifest['review_seen']}
        self.assertTrue({'surf', 'thunderbolt', 'water pulse', 'dragon dance', 'caustic', 'sketch'} <= names)
        battery = (self.build / 'pokecrystal-dex-moves-persistence.sav').read_bytes()
        expected = move_bitmap(manifest['review_seen'])
        for prefix in ('s', 'sBackup'):
            self.assertEqual(decode_record(battery, self.symbols, prefix), dict(status='valid', bitmap=expected))

    def test_rollback_is_intact(self):
        manifest = json.loads((self.build / 'moves-mode-manifest.json').read_text())
        pin_dir = Path(manifest['rollback'])
        pin = json.loads((pin_dir / 'rollback.json').read_text())
        for filename, expected in pin['files'].items():
            self.assertEqual(sha256((pin_dir / filename).read_bytes()), expected)
        for path, expected in manifest['protected_inputs'].items():
            self.assertEqual(sha256(Path(path).read_bytes()), expected)


if __name__ == '__main__':
    unittest.main()
