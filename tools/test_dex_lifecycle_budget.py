"""Reject real display changes while allowing the native water palette phase."""
import copy
import unittest

from dex_timing.dex_lifecycle_budget import visual_audit
from test_dex_lifecycle_review import alter, snapshot


def water_snapshot():
    ui = snapshot()
    data = bytearray.fromhex(ui['palettes'])
    data[24:30] = bytes((0x12, 0x34, 0x56, 0x78, 0x9a, 0x0b))
    ui['palettes'] = data.hex()
    return ui


class BudgetVisualAuditTest(unittest.TestCase):
    def test_native_water_phases(self):
        for color in (bytes((0x12, 0x34)), bytes((0x56, 0x78)), bytes((0x9a, 0x0b))):
            old, new = water_snapshot(), water_snapshot()
            data = bytearray.fromhex(new['palettes'])
            data[24:26] = color
            new['palettes'] = data.hex()
            self.assertFalse(visual_audit(old, new, 0, 'menu')['issues'])

    def test_unknown_water_color_is_rejected(self):
        old, new = water_snapshot(), water_snapshot()
        alter(new, 'palettes', 24, 0xff)
        self.assertIn('palettes', visual_audit(old, new, 0, 'menu')['issues'])

    def test_other_palette_bytes_are_not_ignored(self):
        for at in (0, 23, 26, 29, 30, 63):
            old, new = water_snapshot(), water_snapshot()
            alter(new, 'palettes', 24, 0x56)
            alter(new, 'palettes', 25, 0x78)
            alter(new, 'palettes', at, 0xff)
            self.assertIn('palettes', visual_audit(old, new, 0, 'menu')['issues'])

    def test_water_exception_does_not_apply_to_listing(self):
        old, new = water_snapshot(), water_snapshot()
        alter(new, 'palettes', 24, 0x56)
        alter(new, 'palettes', 25, 0x78)
        self.assertIn('palettes', visual_audit(old, new, 0, 'listing')['issues'])

    def test_water_exception_does_not_hide_geometry_or_obj_changes(self):
        for field in ('map', 'attrs', 'picture', 'obj_palettes', 'oam'):
            old, new = water_snapshot(), water_snapshot()
            alter(new, 'palettes', 24, 0x56)
            alter(new, 'palettes', 25, 0x78)
            alter(new, field, 0, 1)
            self.assertIn(field, visual_audit(old, new, 0, 'menu')['issues'])
        old, new = water_snapshot(), water_snapshot()
        new['scx'] += 1
        self.assertIn('scx', visual_audit(old, new, 0, 'menu')['issues'])

    def test_audit_does_not_mutate_inputs(self):
        old, new = water_snapshot(), water_snapshot()
        alter(new, 'palettes', 24, 0x56)
        alter(new, 'palettes', 25, 0x78)
        before = copy.deepcopy((old, new))
        visual_audit(old, new, 0, 'menu')
        self.assertEqual((old, new), before)


if __name__ == '__main__':
    unittest.main()
