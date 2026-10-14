"""Boundaries for the private mobile Slowpoke retirement audit."""
import unittest

from dex_timing.mobile_slowpoke_cleanup import BASE, COPIES, FILES, GUARDS, edit, included_files


class MobileSlowpokeCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {name: (BASE / name).read_text() for name in FILES}

    def test_assets_only_leaves_three_real_references(self):
        changes = edit(self.originals, assets=True)
        for file, label, _ in COPIES:
            self.assertNotIn(f'{label}:\n', changes[file])
        self.assertEqual(sum(text.count('ld hl, EZChatSlowpokeLZ') for text in changes.values()), 1)
        self.assertEqual(sum(text.count('ld hl, PasswordSlowpokeLZ') for text in changes.values()), 2)

    def test_load_removal_preserves_font_and_lcd_setup(self):
        changes = edit(self.originals, assets=True, loads=True)
        for label in ('EZChatSlowpokeLZ', 'PasswordSlowpokeLZ'):
            self.assertFalse(any(label in text for text in changes.values()))
        for file in FILES:
            for instruction in ('call DisableLCD', 'call EnableLCD', 'ld hl, AsciiFontGFX'):
                self.assertEqual(changes[file].count(instruction), self.originals[file].count(instruction))

    def test_guards_preserve_following_helpers_and_public_labels(self):
        changes = edit(self.originals, assets=True, loads=True, guards=True)
        for file, first, last in GUARDS:
            self.assertIn(f'{first}:\n\tret\n\n{last}:\n', changes[file])
        for label in ('GiveOddEgg:', 'CheckBTMonMovesForErrors:', 'Function171ccd:', 'Function171cf0:'):
            self.assertTrue(any(label in text for text in changes.values()))
        self.assertIn('INCLUDE "engine/events/battle_tower/battle_tower.asm"', changes['mobile/mobile_5c.asm'])

    def test_mobile_menu_not_included_but_assets_owners_are(self):
        files = included_files(BASE)
        self.assertNotIn('mobile/mobile_menu.asm', files)
        for file in FILES:
            self.assertIn(file, files)


if __name__ == '__main__':
    unittest.main()
