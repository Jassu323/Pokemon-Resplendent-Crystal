"""Private motion-table invariants; native replays check publication and sound."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tools'))
from build_battle_motion_prototype import interpolate, curves, finish_surf
from dex_timing.battle_pacing import playback_signature
from tools.build_battle_motion_expansion import burst_plan, retime_bursts


class MotionTests(unittest.TestCase):
    def test_signed_motion_does_not_cross_the_screen(self):
        points=[(0,[0,255]),(2,[254,253])]
        self.assertEqual(interpolate(points,3,True),[[0,255],[255,254],[254,253]])

    def test_mixed_unsigned_x_and_signed_y(self):
        self.assertEqual(interpolate([(0,[64,0]),(2,[66,-2])],3),[[64,0],[65,255],[66,254]])

    def test_unwrapped_angles_wrap_only_after_interpolation(self):
        self.assertEqual(interpolate([(0,[254,24]),(2,[258,28])],3),[[254,24],[0,26],[2,28]])

    def test_single_and_multi_frame_bounds(self):
        points=[(0,[0,0]),(4,[8,16])]
        self.assertEqual(len(interpolate(points,92)),92)
        self.assertEqual(interpolate(points,1),[[0,0]])

    def test_all_generated_tables_fit_the_byte_age(self):
        source,metadata=curves()
        self.assertEqual(metadata['payload'],4114)
        self.assertIn('BANK[$ba]',source)
        self.assertNotIn('DelayFrame',source)

    def test_runtime_has_no_clock_or_new_workspace(self):
        source=(ROOT/'tools/dex_timing/probes/battle_motion_functions.asm').read_text()
        self.assertNotIn('DelayFrame',source)
        self.assertNotIn('hVBlankCounter',source)
        self.assertNotRegex(source,r'(?m)^\s*(?:\w+::?\s*)?ds\s')
        self.assertIn('BATTLEANIMSTRUCT_VAR1',source)
        self.assertIn('BATTLEANIMSTRUCT_VAR2',source)

    def test_surf_finishes_on_the_terminal_step(self):
        source=(ROOT/'engine/battle_anims/functions.asm').read_text()
        source=source[source.index('BattleAnimFunc_Surf:'):source.index('BattleAnimFunc_Sing:')]
        changed=finish_surf(source)
        self.assertIn('\tld [hl], a\n\tcp $70\n\tjr nc, .finish\n',changed)
        self.assertEqual(changed.count('.finish\n'),2)
        self.assertNotIn('DelayFrame',changed)

    def test_audio_signature_survives_json_roundtrip(self):
        import json
        row=dict(segments=[dict(expected_blocks=2,blocks=2,wave_sha256='abc',
                               frequencies=[1848],timer_configs=[(7,156)])])
        self.assertEqual(playback_signature(row),playback_signature(json.loads(json.dumps(row))))

    def test_burst_targets_use_each_spawn_gap_not_the_loop_median(self):
        def reference(task):
            return {'scripts':[{'stages':[{'wait':6,'elapsed':n} for n in (7.2,8.1,14.1)]}]}
        with patch('tools.build_battle_motion_expansion.profile',side_effect=reference):
            self.assertEqual(burst_plan('WHIRLPOOL',3,6),[6,7,13])

    def test_burst_rewrite_preserves_tail_and_updates_each_tick(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            path=root/'data/moves/animations.asm'
            path.parent.mkdir(parents=True)
            path.write_text('BattleAnim_PoisonGas:\n.loop\n'
                '\tanim_obj BATTLE_ANIM_OBJ_POISON_GAS, 44, 80, $2\n.MotionWait0:\n'
                '\tanim_wait 8\n\tanim_loop 10, .loop\n\tanim_wait 207\n\tanim_ret\n'
                'BattleAnim_Whirlpool:\n.loop\n'
                '\tanim_obj BATTLE_ANIM_OBJ_GUST, 132, 72, $0\n.MotionWait1:\n'
                '\tanim_wait 13\n\tanim_loop 9, .loop\n\tanim_wait 129\n\tanim_ret\n')
            with patch('tools.build_battle_motion_expansion.burst_plan',
                       side_effect=lambda move,count,wait:list(range(count))):
                rows=retime_bursts(root)
            text=path.read_text()
            self.assertEqual(len(rows['POISON_GAS']),10)
            self.assertEqual(text.count('anim_obj '),19)
            self.assertIn('\tanim_wait 207\n',text)
            self.assertIn('\tanim_wait 129\n',text)
            self.assertNotIn('anim_loop',text)
            self.assertNotIn('DelayFrame',text)

    def test_expanded_counter_preserves_caller_object_pointer(self):
        text=(ROOT/'tools/dex_timing/probes/battle_motion_expanded_reader.asm').read_text()
        self.assertIn('\tld c, [hl]\n\tinc [hl]\n\tinc hl\n\tld b, [hl]\n\tjr nz, .incremented',text)
        self.assertEqual(text.count('\tpush bc\n'),1)
        self.assertEqual(text.count('\tpop bc\n'),2)
        self.assertIn('\tadd hl, bc\n\tadd hl, bc\n',text)
        self.assertNotIn('DelayFrame',text)


if __name__=='__main__':unittest.main()
