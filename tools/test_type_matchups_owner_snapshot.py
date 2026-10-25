"""Keep Type return checks on the visible owner's actual picture tiles."""
import unittest

from tools.dex_timing.type_matchups import owner_signature


class Driver:
    def __init__(self):
        self.requests = []

    def command(self, command):
        self.requests.append(command)
        if command == 'ui':
            return dict(map='00' * 378, attrs='00' * 378, palettes='00' * 64,
                        scx=0, scy=0, wx=167, wy=0, picture='old-corner', legacy_gfx='legacy')
        _, bank, address, size = command.split()
        return dict(bytes=(f'{int(bank) + 1:02x}' * int(size)))


class OwnerSnapshotTests(unittest.TestCase):
    def test_unown_reads_centered_base_and_resident_font(self):
        driver = Driver()
        result = owner_signature(driver, 2)
        self.assertEqual(result['picture'], '01' * 784)
        self.assertEqual(result['unown_font'], '02' * 432)
        self.assertEqual(result['unown_blank'], '02' * 16)
        self.assertEqual(driver.requests[1:], ['inspectvram 0 36864 784',
                                             'inspectvram 1 35664 432',
                                             'inspectvram 1 37664 16'])

    def test_regular_owner_keeps_its_generic_portrait_oracle(self):
        driver = Driver()
        result = owner_signature(driver, 1)
        self.assertEqual(result['picture'], 'old-corner')
        self.assertEqual(driver.requests, ['ui'])


if __name__ == '__main__':
    unittest.main()
