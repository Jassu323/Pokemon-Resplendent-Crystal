"""Keep lifecycle visual allowances narrower than real UI regressions."""
import copy
import unittest

from dex_timing.dex_lifecycle_review import visible_ui_differences


def snapshot():
    return dict(map=bytes(378).hex(),attrs=bytes(378).hex(),picture=bytes(784).hex(),
                palettes=bytes(64).hex(),obj_palettes=bytes(64).hex(),
                window=bytes(360).hex(),window_attrs=bytes(360).hex(),oam=bytes(160).hex(),
                lcdc=0xe3,scx=5,scy=0,wx=71,wy=0)


def alter(ui, field, at, value):
    data = bytearray.fromhex(ui[field])
    data[at] = value
    ui[field] = data.hex()


class VisualAuditTest(unittest.TestCase):
    def test_exact(self):
        self.assertFalse(visible_ui_differences(snapshot(),snapshot(),0,'listing')['issues'])

    def test_offscreen_edge_only(self):
        old, new = snapshot(),snapshot()
        alter(new,'window',19,0x67)
        self.assertFalse(visible_ui_differences(old,new,0,'listing')['issues'])
        old['wx'] = new['wx'] = 7
        self.assertTrue(visible_ui_differences(old,new,0,'listing')['issues'])

    def test_whole_hidden_window(self):
        old, new = snapshot(),snapshot()
        old['wy'] = new['wy'] = 144
        alter(new,'window',0,12)
        self.assertFalse(visible_ui_differences(old,new,0,'menu')['issues'])

    def test_side_icon_pair(self):
        old, new = snapshot(),snapshot()
        for row in (5,6,9,10,13,14):
            for column in (1,2,9,10):
                cell = (column-1)%8+(4 if column>=9 else 0)+(2 if row%4==2 else 0)
                first = ((row-5)//4+1)*8+cell
                alter(old,'window',row*20+column,first)
                alter(new,'window',row*20+column,(first+0xd2)&255)
        self.assertFalse(visible_ui_differences(old,new,0,'listing')['issues'])
        alter(new,'window',101,0x1f)
        self.assertTrue(visible_ui_differences(old,new,0,'listing')['issues'])

    def test_center_icon_pair(self):
        old, new = snapshot(),snapshot()
        for sprite in range(12):
            first = (sprite//4+1)*8+sprite%4
            alter(old,'oam',sprite*4+2,first)
            alter(new,'oam',sprite*4+2,first+4)
        self.assertFalse(visible_ui_differences(old,new,0,'listing')['issues'])
        self.assertTrue(visible_ui_differences(old,new,1,'listing')['issues'])
        self.assertTrue(visible_ui_differences(old,new,0,'menu')['issues'])

    def test_icon_position_and_palette_are_not_ignored(self):
        for at in (0,1,3):
            old, new = snapshot(),snapshot()
            alter(new,'oam',at,1)
            self.assertTrue(visible_ui_differences(old,new,0,'listing')['issues'])

    def test_other_fields_are_exact(self):
        for field in ('map','attrs','picture','palettes','obj_palettes'):
            old, new = snapshot(),snapshot()
            alter(new,field,0,1)
            self.assertTrue(visible_ui_differences(old,new,0,'listing')['issues'])
        for field in ('lcdc','scx','scy','wx','wy'):
            old, new = snapshot(),snapshot()
            new[field] += 1
            self.assertTrue(visible_ui_differences(old,new,0,'listing')['issues'])

    def test_audit_does_not_mutate(self):
        old, new = snapshot(),snapshot()
        before = copy.deepcopy((old,new))
        visible_ui_differences(old,new,0,'listing')
        self.assertEqual((old,new),before)


if __name__ == '__main__':
    unittest.main()
