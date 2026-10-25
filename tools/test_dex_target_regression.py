#!/usr/bin/env python3
"""Pure host tests for private target edits and clean no-miss core captures."""
from types import SimpleNamespace
import unittest

from dex_timing.assets import Event, timeline
from dex_timing.cpu import ModelError
from dex_timing.probes.compare_core import parse_core
from dex_timing.probes.current_state import eager_tail_control, validate_capture_timer


class CaptureTimerTests(unittest.TestCase):
    def check(self, sampled, active, timer):
        memory = bytearray(65536)
        memory[0xfff1] = active
        validate_capture_timer(SimpleNamespace(sample_blocks=sampled), memory, timer)

    def test_sampled_timer_is_accepted(self):
        self.check(574, 1, (56, 6))
        self.check(0, 0, (56, 6))

    def test_normal_timer_requires_inactive_sampled_playback_and_synth_species(self):
        self.check(0, 0, (0, 4))
        for sampled, active in ((574, 0), (0, 1), (574, 1)):
            with self.subTest(sampled=sampled, active=active), self.assertRaises(ModelError):
                self.check(sampled, active, (0, 4))

    def test_unknown_timer_is_rejected(self):
        for timer in ((0, 0), (56, 4), (0, 6)):
            with self.subTest(timer=timer), self.assertRaises(ModelError):
                self.check(0, 0, timer)


class TargetControlTests(unittest.TestCase):
    def replay(self, loop=False):
        data = bytes((0x13, 50, 0x20, 20, 72, 0, 18, 25))
        data += bytes((0xf1, 11, 0)) if loop else bytes((0xf0,))
        rom = bytes(0x4000)+data+bytes(32)
        repo = SimpleNamespace(symbols={'Timeline': (1, 0x4000)})
        asset = SimpleNamespace(labels={'timeline': 'Timeline'}, total=96,
            events=[Event(1, 3, 50), Event(2, 20, 72), Event(0, 18, 25)])
        return SimpleNamespace(repo=repo, asset=asset, cpu=SimpleNamespace(rom=rom)), len(data)

    def test_preserves_startup_durations_and_other_bytes(self):
        replay, size = self.replay()
        original = replay.cpu.rom
        changes = eager_tail_control(replay)
        self.assertEqual([c['offset'] for c in changes], [0x4004, 0x4007])
        self.assertEqual([i for i, (a, b) in enumerate(zip(original, replay.cpu.rom)) if a != b],
                         [0x4004, 0x4007])
        events, loop = timeline(replay.cpu.rom[0x4000:0x4000+size], 3, 96)
        self.assertEqual(events, [Event(1, 3, 50), Event(2, 20, 96), Event(0, 18, 96)])
        self.assertIsNone(loop)

    def test_preserves_loop_marker(self):
        replay, size = self.replay(loop=True)
        eager_tail_control(replay)
        self.assertEqual(timeline(replay.cpu.rom[0x4000:0x4000+size], 3, 96)[1], 0)

    def test_invalid_layout_does_not_modify_cpu_rom(self):
        for index, value in ((0x4000, 0x23), (0x4004, 71)):
            with self.subTest(index=index):
                replay, _ = self.replay()
                bad = bytearray(replay.cpu.rom)
                bad[index] = value
                replay.cpu.rom = bytes(bad)
                with self.assertRaises(ModelError):
                    eager_tail_control(replay)
                self.assertEqual(replay.cpu.rom, bytes(bad))


class CoreCaptureTests(unittest.TestCase):
    def text(self, count=5, complete=True, audio_active=False):
        lines = []
        for index in range(count):
            anim, audio = bytearray(27), bytearray(6)
            if index == count-1:
                anim[10] = 3 if complete else 2
                audio[3] = int(audio_active)
            lines.extend((f'stop={index} audio={audio.hex()}', anim.hex(), bytes(139).hex()))
        return '\n'.join(lines)

    def test_clean_completion_without_miss(self):
        self.assertEqual(len(parse_core(self.text(), full=True, allow_no_miss=True)), 5)

    def test_no_miss_format_is_explicit(self):
        with self.assertRaises(ValueError):
            parse_core(self.text(), full=True)

    def test_rejects_incomplete_no_miss_run(self):
        for args in ({'complete': False}, {'audio_active': True}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                parse_core(self.text(**args), full=True, allow_no_miss=True)

    def test_rejects_truncated_snapshot(self):
        with self.assertRaises(ValueError):
            parse_core(self.text().rsplit('\n', 1)[0], full=True, allow_no_miss=True)

    def test_historical_full_miss_format_still_accepted(self):
        for allow in (False, True):
            self.assertEqual(len(parse_core(self.text(count=6), full=True, allow_no_miss=allow)), 6)


if __name__ == '__main__':
    unittest.main()
