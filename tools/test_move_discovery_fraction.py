"""Narrow safety checks for the player-requested offline discovery edit."""
from fractions import Fraction
import unittest

from dex_timing.assets import read_symbols
from dex_timing.cold_listing import ROOT
from move_discovery_assets import address, encode_record, seed_records
from set_move_discovery_fraction import inspect, update


class DiscoveryFractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.symbols = read_symbols(ROOT / 'pokecrystal.sym')
        cls.original = (ROOT / 'build/dex-moves-search-final-review-20261011/all-seen-tests.sav').read_bytes()

    def sample(self, indices):
        flags = bytearray(64)
        for n in indices:
            flags[(n-1)//8] |= 1 << ((n-1)&7)
        return seed_records(self.original, self.symbols, flags)

    def test_reaches_two_hundred_preserving_existing_and_rtc(self):
        source = self.sample([1, 165, 256, 333, 512])
        after, record = update(source, self.symbols, 333, Fraction(3, 5), 7)
        bitmap, seen = inspect(after, self.symbols, 333)
        self.assertEqual(len(seen), 200)
        self.assertTrue({1, 165, 256, 333}.issubset(seen))
        self.assertTrue(bitmap[63] & 128)
        self.assertEqual(after[32768:], source[32768:])
        self.assertTrue(record['core_and_rtc_unchanged'])

    def test_union_keeps_backup_discoveries(self):
        source = bytearray(self.sample([1]))
        flags = bytearray(64)
        flags[41] = 16
        at = address(self.symbols, 'sBackupMoveDiscovery')
        source[at:at+72] = encode_record(source, self.symbols, 'sBackup', flags)
        after, _ = update(source, self.symbols, 333, '0.60', 4)
        self.assertTrue({1, 333}.issubset(inspect(after, self.symbols, 333)[1]))

    def test_above_target_never_removes_flags(self):
        source = self.sample(range(1, 251))
        after, record = update(source, self.symbols, 333, '0.60', 9)
        self.assertEqual(after, source)
        self.assertEqual(record['after'], 250)

    def test_random_selection_is_repeatable(self):
        source = self.sample([165])
        self.assertEqual(update(source, self.symbols, 333, '0.60', 4),
                         update(source, self.symbols, 333, '0.60', 4))

    def test_bad_core_or_discovery_is_rejected(self):
        for label in ('sChecksum', 'sMoveDiscovery', 'sBackupMoveDiscovery'):
            source = bytearray(self.sample([1]))
            source[address(self.symbols, label)] ^= 1
            with self.assertRaises(ValueError):
                update(source, self.symbols, 333, '0.60', 4)


if __name__ == '__main__':
    unittest.main()
