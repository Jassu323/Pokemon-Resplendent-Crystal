"""A settled destination cannot excuse old palettes leaking before the fade."""
import copy
import unittest

from dex_timing.dex_lifecycle_return_repair import reveal_frames


def frame(t, *, palettes=10, white=100, lcdc=0xe3, kind=0):
    return dict(event='perf_frame',boundary_t=t,bgpals=palettes,white=white,lcdc=lcdc,type=kind)


class ReturnRevealTest(unittest.TestCase):
    def events(self, *frames):
        return [frame(0),dict(event='perf_phase',name='enable_lcd',t=10),*frames]

    def test_two_bad_frames_are_detected(self):
        bad = reveal_frames(self.events(frame(11),frame(12),frame(13,palettes=20)))
        self.assertEqual([f['boundary_t'] for f in bad],[11,12])

    def test_white_then_normal_fade_passes(self):
        self.assertFalse(reveal_frames(self.events(frame(11,white=23040),frame(12,palettes=20))))

    def test_old_dex_before_enable_is_not_a_failure(self):
        self.assertFalse(reveal_frames(self.events(frame(9),frame(11,white=23040))))

    def test_disabled_lcd_or_nonphysical_callback_is_not_a_reveal(self):
        self.assertFalse(reveal_frames(self.events(frame(11,lcdc=0x63),frame(12,kind=1))))

    def test_missing_enable_fails_closed(self):
        with self.assertRaises(ValueError):
            reveal_frames([frame(0)])

    def test_no_input_mutation(self):
        events = self.events(frame(11),frame(12,palettes=20))
        before = copy.deepcopy(events)
        reveal_frames(events)
        self.assertEqual(events,before)


if __name__=='__main__':
    unittest.main()
