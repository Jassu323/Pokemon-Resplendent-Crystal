"""Acceptance and negative controls for shared-menu input diagnostics."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from dex_timing.shared_input_contracts import callers, compare, value


class SharedInputContractTests(unittest.TestCase):
    def sample(self, pressed=0x10, down=0x51, last=0x51):
        return dict(t=400, registers=list(range(8)), flags=0x10, sp=0xc0f0,
                    bank=1, fields=dict(hJoyPressed=pressed, hJoyDown=down,
                                        hJoyLast=last, wTextDelayFrames=15))

    def pair(self, menu=1, **kwargs):
        baseline = self.sample(**kwargs)
        candidate = deepcopy(baseline)
        fresh = baseline['fields']['hJoyPressed'] & 0xf0
        if menu and fresh:
            candidate['fields']['hJoyLast'] = (baseline['fields']['hJoyDown'] & 15) | fresh
        return baseline, candidate

    def test_fresh_direction_keeps_held_buttons_not_old_axis(self):
        pair = self.pair()
        pair[1]['t'] += 72
        self.assertEqual(pair[1]['fields']['hJoyLast'], 0x11)
        self.assertEqual(compare(pair, 1, 'fresh'), ('fresh_direction', 72))

    def test_non_menu_result_is_unchanged(self):
        pair = self.pair(menu=0)
        self.assertEqual(pair[1]['fields']['hJoyLast'], 0x51)
        self.assertEqual(compare(pair, 0, 'walking'), ('non_menu', 0))

    def test_button_only_press_does_not_filter_held_directions(self):
        pair = self.pair(pressed=1)
        self.assertEqual(pair[1]['fields']['hJoyLast'], 0x51)
        self.assertEqual(compare(pair, 1, 'button')[0], 'other_menu_input')

    def test_suppressed_repeat_remains_suppressed(self):
        pair = self.pair(pressed=0, last=0)
        self.assertEqual(pair[1]['fields']['hJoyLast'], 0)
        compare(pair, 1, 'suppressed')

    def test_simultaneous_new_directions_are_preserved(self):
        pair = self.pair(pressed=0x50)
        self.assertEqual(pair[1]['fields']['hJoyLast'], 0x51)
        compare(pair, 1, 'simultaneous')

    def test_wrong_old_axis_mask_is_rejected(self):
        pair = self.pair()
        pair[1]['fields']['hJoyLast'] = 0x51
        with self.assertRaises(RuntimeError):
            compare(pair, 1, 'old axis')

    def test_register_flags_bank_and_stack_changes_are_rejected(self):
        for key in ('registers', 'flags', 'bank', 'sp'):
            with self.subTest(key=key):
                pair = self.pair()
                pair[1][key] = [] if key == 'registers' else 0
                with self.assertRaises(RuntimeError):
                    compare(pair, 1, key)

    def test_raw_mirror_and_repeat_timer_changes_are_rejected(self):
        for key in ('hJoyPressed', 'hJoyDown', 'wTextDelayFrames'):
            with self.subTest(key=key):
                pair = self.pair()
                pair[1]['fields'][key] ^= 1
                with self.assertRaises(RuntimeError):
                    compare(pair, 1, key)

    def test_auto_input_pointer_is_read_as_a_word(self):
        class CPU:
            symbols = {'wAutoInputAddress': (1, 0xd000), 'wAutoInputLength': (1, 0xd002)}

            def read(self, address):
                return {0xd000: 0x34, 0xd001: 0x12, 0xd002: 5}[address]

        self.assertEqual(value(CPU(), 'wAutoInputAddress'), 0x1234)
        self.assertEqual(value(CPU(), 'wAutoInputLength'), 5)

    def test_caller_inventory_includes_mobile_and_excludes_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'mobile').mkdir()
            (root / 'mobile/menu.asm').write_text(
                'MobileMenu:\n.loop\n\tcall JoyTextDelay ; accepted\n; jp JoyTextDelay\n')
            result = callers(root)
        self.assertEqual(result, [dict(path='mobile/menu.asm', line=3, owner='MobileMenu.loop')])


if __name__ == '__main__':
    unittest.main()
