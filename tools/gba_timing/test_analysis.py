"""Small analysis-contract tests; native replay parity is a separate audit."""
import unittest
from .analyze import groups, display_groups
from .thunderbolt import symbols


class AnalysisTests(unittest.TestCase):
    def test_holds_are_contiguous_not_total_occurrences(self):
        rows=[dict(pose=p) for p in [1,1,2,1]]
        self.assertEqual([len(x) for x in groups(rows,lambda x:x['pose'])],[2,1,1])

    def test_collision_uses_battle_animation_end(self):
        s=symbols()
        self.assertEqual(s['BattleAnimEnd'],0x080a3fc4)
        self.assertLess(s['HandleInputChooseAction'],s['DoMoveAnim'])

    def test_missing_display_does_not_extend_a_hold(self):
        rows=[dict(frame=f,pose=1) for f in [1,2,4,5]]
        self.assertEqual([len(x) for x in display_groups(rows,lambda x:x['pose'],'frame')],[2,2])


if __name__=='__main__': unittest.main()
