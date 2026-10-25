"""Host-only regression tests. No emulator, save file or ROM writes."""

from dataclasses import replace
from copy import deepcopy
import hashlib
import json
import os
import struct
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dex_timing.assets import Repository, decompress, timeline, schedule, offset, Event, sha256
from dex_timing.costs import (benchmark, audio_benchmark, publication_benchmark,
                             verify_hdma_contract, trace_span, owner_prefix_benchmark,
                             owner_shell_benchmark, path_cost)
from dex_timing.cpu import CounterCPU, ModelError
from dex_timing.model import Clock, Profile, FRAME, LINE, expand_loop, simulate
from dex_timing.traces import span, decode_trace, read_captures
from dex_timing.followup import observed_legs, read_stops, read_debugger_clock, captured_trace_differences, compare_linked_replay, STOPS
from dex_timing.replay import OwnerReplay, captured_state_differences, matches_captured_states, matching_div_phases

ROOT = Path(os.environ.get('DEX_TIMING_REFERENCE_ROOT', Path(__file__).resolve().parents[1]))


class InstructionTests(unittest.TestCase):
    def cpu(self, program):
        rom = bytearray(0x8000)
        rom[0x100:0x100+len(program)] = bytes(program)
        return CounterCPU(rom, {"test": (0, 0x100), "hROMBank": (0, 0xFF9D)})

    def test_conditional_loop_cycles(self):
        cpu = self.cpu([0x21, 0, 0xC1, 0x06, 3, 0x2A, 0x80, 0x05, 0x20, 0xFB, 0xC9])
        cpu.block(0xC100, bytes([1, 2, 3]))
        self.assertEqual(cpu.run("test"), 116)
        self.assertEqual(cpu.r[7], 4)
        self.assertEqual(cpu.pair(2), 0xC103)

    def test_conditional_call_both_paths(self):
        # XOR A; CALL NZ,$0107 (not taken); CALL Z,$0109; RET; RET
        cpu = self.cpu([0xAF, 0xC4, 7, 1, 0xCC, 9, 1, 0xC9, 0, 0xC9])
        self.assertEqual(cpu.run("test"), 4+12+24+16+16)

    def test_push_pop_af_masks_unused_flags(self):
        cpu = self.cpu([0x01, 0xFF, 0x12, 0xC5, 0xF1, 0xC9])
        self.assertEqual(cpu.run("test"), 12+16+12+16)
        self.assertEqual((cpu.r[7], cpu.f), (0x12, 0xF0))

    def test_alu_flags(self):
        cpu = self.cpu([0x3E, 0xFF, 0xC6, 1, 0xC9])
        cpu.run("test")
        self.assertEqual((cpu.r[7], cpu.f), (0, 0xB0))
        cpu = self.cpu([0x3E, 0, 0xDE, 0, 0xC9])
        cpu.f = cpu.C
        cpu.run("test")
        self.assertEqual((cpu.r[7], cpu.f), (255, 0x70))

    def test_inc_preserves_carry(self):
        cpu = self.cpu([0x3E, 15, 0x37, 0x3C, 0xC9])
        cpu.run("test")
        self.assertEqual((cpu.r[7], cpu.f), (16, 0x30))

    def test_cb_memory_and_bit_timing(self):
        cpu = self.cpu([0x21, 0, 0xC1, 0xCB, 0x06, 0xCB, 0x46, 0xC9])
        cpu.write(0xC100, 128)
        self.assertEqual(cpu.run("test"), 12+16+12+16)
        self.assertEqual(cpu.read(0xC100), 1)
        self.assertEqual(cpu.f, 0x30)

    def test_banked_wram_and_restore(self):
        cpu = self.cpu([0x3E, 6, 0xE0, 0x70, 0x3E, 0x42, 0xEA, 0, 0xD0, 0xC9])
        cpu.run("test")
        self.assertEqual(cpu.wram[6][0], 0x42)
        self.assertEqual(cpu.wram[1][0], 0)

    def test_banked_rom(self):
        cpu = self.cpu([0x3E, 1, 0xEA, 0, 0x20, 0xFA, 0, 0x40, 0xC9])
        cpu.rom[0x4000] = 0x5A
        cpu.run("test")
        self.assertEqual(cpu.r[7], 0x5A)

    def test_unknown_opcode_fails_closed(self):
        with self.assertRaisesRegex(ModelError, "Unsupported instruction"):
            self.cpu([0xD3]).run("test")

    def test_unmodeled_hardware_fails_closed(self):
        with self.assertRaisesRegex(ModelError, "hardware read"):
            self.cpu([0xF0, 0x44, 0xC9]).run("test")

    def test_busy_wait_budget(self):
        with self.assertRaisesRegex(ModelError, "budget exceeded"):
            self.cpu([0x18, 0xFE]).run("test", max_steps=10)

    def test_trace_uses_io_read_not_delayed_store(self):
        cpu = self.cpu([0xF0, 0x44, 0xEA, 0, 0xC1, 0, 0, 0xF0, 0x44, 0,
                        0xEA, 1, 0xC1, 0xC9])
        cpu.allowed_io.add(0xFF44)
        cpu.symbols.update(wPokedexAnimTraceStartLY=(0, 0xC100),
                           wPokedexAnimTraceEndLY=(0, 0xC101))
        cpu.record_writes = True
        cpu.run("test")
        self.assertEqual(trace_span(cpu, "Start", "End"), 36)

    def test_fixture_input_read_is_independent_of_output_write(self):
        cpu = self.cpu([0x3E, 0x20, 0xE0, 0, 0xF0, 0, 0xC9])
        cpu.allowed_io.add(0xFF00)
        cpu.io_read_values[0xFF00] = 15
        cpu.run("test")
        self.assertEqual(cpu.r[7], 15)
        self.assertEqual(cpu.ram[0xFF00], 0x20)


class AssetTests(unittest.TestCase):
    def test_every_lz_command(self):
        data = bytes([0x02, 1, 2, 4, 0x21, 0x7E, 0x42, 0xAA, 0xBB, 0x62,
                      0x82, 0x82, 0xA2, 0, 0, 0xC2, 0, 2, 0xFF])
        stream = decompress(data)
        self.assertEqual(stream.output, bytes([1, 2, 4, 126, 126, 170, 187, 170] + [0]*6 + [128, 64, 32, 4, 2, 1]))
        self.assertEqual({c for c, _ in stream.commands}, set(range(7)))

    def test_overlapping_repeat(self):
        self.assertEqual(decompress(bytes([0, 65, 0x83, 0x80, 255])).output, b"AAAAA")

    def test_long_literal(self):
        self.assertEqual(decompress(bytes([0xE0, 32])+bytes(range(33))+b"\xff").output, bytes(range(33)))

    def test_long_count_rollover(self):
        self.assertEqual(decompress(bytes([0xED, 0, 255])).output, bytes(257))

    def test_bad_rewrite_rejected(self):
        with self.assertRaises(ModelError):
            decompress(bytes([0x80, 0x80, 255]))

    def test_truncation_and_limit(self):
        for data, limit in ((bytes([0x02, 1]), 4096), (bytes([0x63, 255]), 3)):
            with self.assertRaises(ModelError):
                decompress(data, output_limit=limit)

    def test_separate_stream_history(self):
        first = decompress(bytes([0, 65, 255, 0x80, 0x80, 255]))
        with self.assertRaises(ModelError):
            decompress(bytes([0, 65, 255, 0x80, 0x80, 255]), first.end)

    def test_timeline_finish_and_extended_duration(self):
        events, loop = timeline(bytes([0x12, 49, 0x20, 20, 55, 0xF0]), 3, 55)
        self.assertEqual(events, [Event(1, 2, 49), Event(2, 20, 55)])
        self.assertIsNone(loop)

    def test_timeline_loop_boundary(self):
        events, loop = timeline(bytes([0x12, 49, 0x23, 55, 0xF1, 5, 0]), 3, 55)
        self.assertEqual(loop, 1)
        self.assertEqual(len(expand_loop(events, loop, 3)), 4)

    def test_bad_timeline_loop(self):
        with self.assertRaises(ModelError):
            timeline(bytes([0x12, 49, 0xF1, 4, 0]), 2, 49)

    def test_signed_deadline_horizon(self):
        with self.assertRaises(ModelError):
            timeline(bytes([0x10, 128, 49, 0xF0]), 2, 49)

    def test_schedule_rle_and_loop(self):
        actions, loop = schedule(bytes([2, 0xC2, 0x40, 4, 0]))
        self.assertEqual(actions, [0, 0, 3, 3])
        self.assertEqual(loop, 2)

    def test_reserved_schedule_rejected(self):
        with self.assertRaises(ModelError):
            schedule(bytes([0x81, 0]))

    def test_rom_offsets(self):
        self.assertEqual(offset((0xA0, 0x4000)), 0x280000)
        with self.assertRaises(ModelError):
            offset((4, 0xD000))


class ClockTests(unittest.TestCase):
    def clock(self, **kwargs):
        return Clock(Profile(lcd_stat_enabled=False, **kwargs), {"timer_irq_t": [100]}, 0)

    def test_frame_and_scanline(self):
        c = self.clock()
        self.assertEqual(c.ly, 144)
        c.work(10*LINE)
        self.assertEqual(c.ly, 0)
        c.work(144*LINE)
        self.assertEqual(c.ly, 144)

    def test_irq_steals_cpu_time(self):
        c = Clock(Profile(lcd_stat_enabled=False), {"timer_irq_t": [100]}, 100)
        c.work(12801)
        self.assertEqual(c.t, 12901)
        self.assertEqual(c.cache, 30)

    def test_wait_does_not_add_irq_twice(self):
        c = Clock(Profile(lcd_stat_enabled=False), {"timer_irq_t": [100]}, 100)
        c.wait(13000)
        self.assertEqual(c.t, 13000)
        self.assertEqual(c.totals["timer_irq"], 100)

    def test_hdma_scanline_cutoff(self):
        early, late = self.clock(), self.clock()
        early.t = (10+106)*LINE
        late.t = (10+108)*LINE
        early.hdma(20)
        late.hdma(20)
        self.assertLess(early.t, FRAME)
        self.assertGreater(late.t, FRAME)

    def test_late_18_tile_cutoff(self):
        c = self.clock()
        c.t = (10+110)*LINE
        c.hdma(18)
        self.assertGreater(c.t, FRAME)

    def test_hdma_never_transfers_in_vblank(self):
        c = self.clock()
        c.hdma(1)
        launch = c.events[-1]
        self.assertGreaterEqual(launch["first_block_t"], 10*LINE)
        self.assertEqual(c.totals["dma_cpu_halt"], 32)

    def test_ly_zero_during_last_vblank_line_is_not_visible_mode(self):
        c = self.clock()
        c.t = 9*LINE+8
        self.assertEqual((c.ly, c.physical_line, c.mode), (0, 153, 1))
        c.t = 10*LINE
        self.assertEqual((c.ly, c.physical_line, c.mode), (0, 0, 2))

    def test_stat_read_occurs_inside_instruction(self):
        c = self.clock(hblank_dot=252)
        c.t = 10*LINE+248
        self.assertEqual(c.mode, 3)
        self.assertEqual(c.read_instruction(12, 8, lambda: c.mode, "read"), 0)
        self.assertEqual(c.t, 10*LINE+260)

    def test_footer_wait_retries_instead_of_charging_fixed_delay(self):
        c = self.clock(hblank_dot=252)
        c.t = 10*LINE+80
        c.footer_wait()
        self.assertGreater(c.events[-1]["busy_polls"], 0)
        self.assertGreaterEqual(c.dot, 252)
        c.t = 10*LINE+300
        begin = c.t
        c.footer_wait()
        self.assertEqual(c.t-begin, 28)
        self.assertEqual(c.events[-1]["busy_polls"], 0)

    def test_footer_vblank_poll_does_not_wait_for_visible_lines(self):
        c = self.clock()
        c.footer_wait()
        self.assertEqual(c.t, 28)

    def test_interrupts_do_not_split_an_instruction(self):
        c = Clock(Profile(lcd_stat_enabled=False, audio_phase_t=1), {"timer_irq_t": [100]}, 100)
        value = c.read_instruction(12, 8, lambda: c.cache, "read")
        self.assertEqual(value, 31)
        self.assertEqual(c.cache, 30)
        self.assertEqual(c.t, 112)

    def test_delay_frame_wakes_for_audio_before_vblank(self):
        paths = {"halt_t": 4, "after_vblank": [4, 16, 4, 8, 24],
                 "after_other_irq": [4, 16, 4, 12], "after_service": [16, 12]}
        c = Clock(Profile(lcd_stat_enabled=False, audio_phase_t=100), {"timer_irq_t": [100]}, 32)
        c.run_path(["arm"], "arm")
        c.delay_frame(paths)
        self.assertEqual(c.vblank_count, 1)
        self.assertGreater(c.events[-1]["wake_count"], 1)
        self.assertEqual(c.t, FRAME+84)

    def test_vblank_before_arm_requires_another_vblank(self):
        paths = {"halt_t": 4, "after_vblank": [4, 16, 4, 8, 24],
                 "after_other_irq": [4, 16, 4, 12], "after_service": [16, 12]}
        c = self.clock()
        c.wait(FRAME)
        c.run_path(["arm"], "arm")
        c.delay_frame(paths)
        self.assertEqual(c.vblank_count, 2)

    def test_vblank_during_arm_is_observed_by_subsequent_flag_check(self):
        paths = {"halt_t": 4, "after_vblank": [4, 16, 4, 8, 24],
                 "after_other_irq": [4, 16, 4, 12], "after_service": [16, 12]}
        c = Clock(Profile(hblank_dot=252), {"lcd_irq_t": 108}, 0)
        c.wait(FRAME-8)
        c.run_path(["arm"], "arm")
        self.assertEqual((c.wait_armed_count, c.vblank_count), (0, 1))
        c.delay_frame(paths)
        self.assertEqual(c.vblank_count, 1)
        self.assertLess(c.t, 2*FRAME)

    def test_irq_already_pending_does_not_wake_a_future_halt(self):
        paths = {"halt_t": 4, "after_vblank": [4, 16, 4, 8, 24],
                 "after_other_irq": [4, 16, 4, 12], "after_service": [16, 12]}
        c = self.clock()
        c.audio["lcd_irq_t"] = 108
        c.wait_armed_count = -1
        c.pending.add("lcd")
        c.delay_frame(paths)
        self.assertEqual(c.vblank_count, 1)
        self.assertEqual(c.events[-1]["wake_count"], 1)

    def test_hdma_irq_overlap(self):
        noirq = self.clock()
        irq = Clock(Profile(lcd_stat_enabled=False), {"timer_irq_t": [100]}, 100)
        for c in (noirq, irq):
            c.t = 10*LINE
            c.hdma(20)
        self.assertLess(abs(noirq.t-irq.t), 200)
        self.assertGreater(irq.totals.get("timer_irq", 0), 0)

    def test_depletion_is_not_natural_completion(self):
        c = Clock(Profile(lcd_stat_enabled=False), {"timer_irq_t": [100]}, 100)
        c.cache = 0
        c.work(12800)
        self.assertEqual(c.audio_underrun, 12800)
        c = Clock(Profile(lcd_stat_enabled=False), {"timer_irq_t": [100]}, 1)
        c.work(12800)
        self.assertIsNone(c.audio_underrun)

    def test_refill_is_progressive(self):
        audio = {"timer_irq_t": [100], "refill": {"2": [{"t": 20000, "publish_t": [1000, 18000]}]}}
        c = Clock(Profile(lcd_stat_enabled=False), audio, 34)
        c.cache = 0
        c.refill()
        self.assertIsNone(c.audio_underrun)
        self.assertEqual(c.cache, 1)

    def test_cache_publish_precedes_irq_on_same_boundary(self):
        audio = {"timer_irq_t": [100], "refill": {"1": [{"t": 12800, "publish_t": [12800]}]}}
        c = Clock(Profile(lcd_stat_enabled=False), audio, 33)
        c.cache = 0
        c.refill()
        self.assertIsNone(c.audio_underrun)
        self.assertEqual(c.cache, 0)

    def test_invalid_profile_number(self):
        with self.assertRaises(ModelError):
            Profile(outer_loop_t=float("nan")).validate()

    def test_timer_phase_is_explicit_and_bounded(self):
        for phase in (0, 12801, 1.5):
            with self.assertRaises(ModelError):
                Profile(audio_phase_t=phase).validate()
        c = Clock(Profile(lcd_stat_enabled=False, audio_phase_t=64), {"timer_irq_t": [100]}, 100)
        c.work(64)
        self.assertEqual(c.irq_counts["timer"]["delivered"], 1)
        self.assertEqual(c.next_timer, 12864)

    def test_lcd_visible_lines_only(self):
        c = Clock(Profile(), {"lcd_irq_t": 108}, 0)
        c.wait(10*LINE)
        self.assertEqual(c.irq_counts["lcd"]["delivered"], 0)
        c.wait(FRAME)
        self.assertEqual(c.irq_counts["lcd"], {"requested": 144, "delivered": 144, "coalesced": 0})
        self.assertEqual(c.totals["lcd_irq"], 144*108)

    def test_masked_lcd_requests_coalesce(self):
        c = Clock(Profile(), {"lcd_irq_t": 108}, 0)
        c.work(14*LINE, masked=True)
        self.assertEqual(c.irq_counts["lcd"], {"requested": 4, "delivered": 0, "coalesced": 3})
        c.work(0)
        self.assertEqual(c.totals["lcd_irq"], 108)

    def test_irq_priority(self):
        c = Clock(Profile(), {"lcd_irq_t": 108, "timer_irq_t": [100]}, 100)
        c.next_vblank = c.next_lcd = c.next_timer = 100
        c.work(100)
        kinds = [k for k in c.totals if k in ("vblank", "lcd_irq", "timer_irq")]
        self.assertEqual(kinds, ["vblank", "lcd_irq", "timer_irq"])

    def test_timer_masks_and_coalesces_lcd_not_ppu(self):
        c = Clock(Profile(), {"lcd_irq_t": 108, "timer_irq_t": [1480]}, 100)
        c.wait(15200)
        self.assertEqual(c.t, 15200)
        self.assertGreater(c.irq_counts["lcd"]["coalesced"], 0)
        self.assertEqual(c.irq_counts["timer"]["delivered"], 1)

    def test_lcd_does_not_stop_hdma_train(self):
        c = Clock(Profile(), {"lcd_irq_t": 108}, 0)
        c.wait(10*LINE)
        begin = c.t
        c.hdma(20)
        self.assertEqual(c.totals["dma_cpu_halt"], 20*32)
        self.assertEqual(c.irq_counts["lcd"]["delivered"], 20)
        self.assertLess(c.t-begin, 21*LINE)

    def test_reject_unsupported_speed_or_prefill(self):
        with self.assertRaises(ModelError):
            Profile(prefill=191).validate()


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = json.loads((ROOT/"tools/dex_timing/fixtures/known_misses.json").read_text())["captures"]

    def test_known_misses_are_preserved(self):
        for fixture in self.fixtures:
            decoded = decode_trace(bytes.fromhex(fixture["hex"]))
            miss = next(r for r in decoded["records"] if r["action"] == 0x82)
            for actual, expected in (("frame", "frame"), ("deadline", "deadline"),
                                     ("loaded_tiles", "loaded"), ("upload_offset", "uploaded")):
                self.assertEqual(miss[actual], fixture["expected"][expected])
            self.assertEqual(decoded["calibration_status"], "UNBOUND_OBSERVATION")

    def test_producer_call_gap(self):
        decoded = decode_trace(bytes.fromhex(self.fixtures[0]["hex"]))
        self.assertEqual(decoded["producer_gaps"][0]["missing_display_intervals"], 1)

    def test_luxray_idle_run(self):
        decoded = decode_trace(bytes.fromhex(self.fixtures[1]["hex"]))
        self.assertEqual(sum(r["action"] == 0x10 for r in decoded["records"]), 4)

    def test_counter_wrap_and_scanline_origin(self):
        self.assertEqual(span((255, 143), (0, 144))["nominal_t"], LINE)
        self.assertEqual(span((1, 153), (1, 0))["nominal_t"], LINE)

    def test_unknown_schema_or_short_data(self):
        with self.assertRaises(ModelError):
            decode_trace(bytes(139))
        with self.assertRaises(ModelError):
            decode_trace(bytes([0xD7, 6]))

    def test_text_dump_roundtrip(self):
        raw = bytes.fromhex(self.fixtures[0]["hex"])
        text = "\n".join(f"00:{0xC758+i:04x}: {raw[i:i+16].hex(' ')}" for i in range(0, len(raw), 16))
        self.assertEqual(read_captures(text)[0], decode_trace(raw))
        self.assertEqual(len(read_captures(text+"\n"+text)), 2)

    def test_incomplete_dump_rejected(self):
        with self.assertRaisesRegex(ModelError, "Incomplete"):
            read_captures("00:c758: d7 06 00")


class FollowupTests(unittest.TestCase):
    def test_debugger_clock_reset_is_distinct_from_elapsed_count(self):
        result = read_debugger_clock('ticks:\nT-cycles: 100\nM-cycles: 25\nAbsolute 8MHz ticks: 200\nTick count reset.\n')
        self.assertEqual(result, dict(keep=False, t_cycles=100, absolute_8mhz_ticks=200))

    def test_debugger_clock_keep_and_absence(self):
        result = read_debugger_clock('ticks keep:\nT-cycles: 36\nM-cycles: 9\nAbsolute 8MHz ticks: 72\n')
        self.assertEqual(result, dict(keep=True, t_cycles=36, absolute_8mhz_ticks=72))
        self.assertIsNone(read_debugger_clock('registers:\n'))

    def test_debugger_clock_rejects_missing_reset_and_wrong_speed(self):
        with self.assertRaisesRegex(ModelError, 'reset'):
            read_debugger_clock('ticks:\nT-cycles: 36\nM-cycles: 9\nAbsolute 8MHz ticks: 72\n')
        with self.assertRaisesRegex(ModelError, 'normal speed'):
            read_debugger_clock('ticks keep:\nT-cycles: 36\nM-cycles: 9\nAbsolute 8MHz ticks: 36\n')

    def stops(self):
        # Clock bytes only from the five-stop Weavile capture; no fitted costs.
        counters = (0xaa, 0xab, 0xab, 0xac, 0xad)
        lines = (145, 73, 139, 153, 76)
        div = (0x4e, 0xe0, 0x56, 0x6e, 0x09)
        tima = (0xfe, 0xf0, 0x6f, 0xce, 0xfd)
        remaining = (201, 198, 195, 195, 187)
        compressed = (173, 165, 165, 165, 157)
        return [dict(label=label, counter=counters[i], physical_line=lines[i], div=div[i],
                     tima=tima[i], remaining=remaining[i], compressed=compressed[i])
                for i, label in enumerate(STOPS)]

    def test_timer_and_div_resolve_display_intervals(self):
        legs = observed_legs(self.stops())
        self.assertEqual([l["nominal_t"] for l in legs], [37504, 30144, 6080, 105408])
        self.assertEqual([l["blocks_decoded"] for l in legs], [8, 0, 0, 8])

    def test_inconsistent_div_rejected(self):
        stops = self.stops()
        stops[2]["div"] += 10
        with self.assertRaisesRegex(ModelError, "Inconsistent|inconsistent"):
            observed_legs(stops)

    def test_partial_hardware_stop_rejected(self):
        with self.assertRaisesRegex(ModelError, "Incomplete"):
            read_stops("Publication:\nregisters:\n", {})

    def test_empty_followup_rejected(self):
        with self.assertRaisesRegex(ModelError, "Expected Publication"):
            read_stops("", {})

    def test_frame_miss_alias_requires_known_matching_pc(self):
        for symbols in ({}, {"Pokedex_CountAnimationUnderflow": (0xa0, 0x67fc)}):
            with self.subTest(symbols=symbols), self.assertRaisesRegex(ModelError, "alias"):
                read_stops("Frame Miss:\nregisters:\nPC = $1234\n", symbols)

    def test_joint_timer_phase_rejects_independent_stop_fits(self):
        stops = self.stops()
        points = [{"t": t} for t in (600, 38068, 68212, 74340, 179720)]
        self.assertEqual(matching_div_phases(points, stops, 696), [36])
        stops[2]["tima"] += 1
        self.assertEqual(matching_div_phases(points, stops, 696), [])

    def test_joint_div_phase_must_also_match_timer_edges(self):
        stops = self.stops()
        points = [{"t": t} for t in (600, 38068, 68212, 74340, 179720)]
        stops[4]["div"] += 1
        self.assertEqual(matching_div_phases(points, stops, 696), [100])
        stops[4]["div"] += 1
        self.assertEqual(matching_div_phases(points, stops, 696), [])


class CoreProbeTests(unittest.TestCase):
    def end_to_end_capture(self, name='weavile'):
        from dex_timing.end_to_end import read_capture, SYMBOLS
        text = (ROOT/f'tools/dex_timing/fixtures/{name}_end_to_end.txt').read_text()
        symbols = dict(zip(SYMBOLS, ((0x77,0x5ea5),(0xa0,0x67fc),(0,0x0063),(0,0x047e))))
        return text, symbols, read_capture(text, symbols)

    def test_end_to_end_capture_resets_origin_and_retains_cry_state(self):
        _, _, weavile = self.end_to_end_capture()
        _, _, dusknoir = self.end_to_end_capture('dusknoir')
        self.assertEqual([p['t'] for p in weavile], [0,181132,2572872,5493520])
        self.assertEqual([p['t'] for p in dusknoir], [0,508736,2816412,12240048])
        self.assertEqual(weavile[2]['audio'][4:], [0,0])
        self.assertEqual(dusknoir[2]['audio'][4:], [0x4d,1])
        self.assertEqual(dusknoir[2]['audio_cache'][0], 0)
        self.assertEqual(dusknoir[3]['audio_cache'][0], 8)
        self.assertEqual(weavile[1]['pixel'], 154)
        self.assertEqual(dusknoir[2]['remain'], 142)

    def test_end_to_end_capture_rejects_incomplete_or_conflicting_samples(self):
        from dex_timing.end_to_end import read_capture
        text, symbols, _ = self.end_to_end_capture()
        cases = (text.rsplit('-----',1)[0], text.replace('ticks keep:', 'ticks:', 1),
                 text.replace('AF  = $00c0', 'AF  = $01c0', 1),
                 text.replace('00:ff04: 43 3b 38 fe', '00:ff04: 43 3b 38', 1),
                 text.replace('1. $77:$5ea5', '1. $77:$5ea4', 1))
        for bad in cases:
            with self.subTest(capture=bad[:20]), self.assertRaises(ModelError):
                read_capture(bad, symbols)

    def test_end_to_end_comparison_normalizes_rom0_banks_and_checks_state(self):
        from dex_timing.end_to_end import differences
        _, _, points = self.end_to_end_capture()
        actual = deepcopy(points)
        actual[-1]['bank'] = 0x10
        self.assertFalse(any(differences(actual, points, ppu=True)))
        actual[-1]['t'] += 4
        actual[2]['audio'][4] += 1
        found = differences(actual, points)
        self.assertEqual(found[2][0]['field'], 'audio')
        self.assertEqual(found[3][0]['field'], 't')

    def core_text(self):
        return '\n'.join(f'stop={i} t={i*100} pc=5ea5 bank=77 div=44f0 tima=ff read_address=d040\n'
                         + '00'*27+'\n'+'00'*139 for i in range(5))

    def test_reference_core_parser_handles_hex_and_decimal(self):
        from dex_timing.probes.compare_core import parse_core
        points = parse_core(self.core_text())
        self.assertEqual([p['t'] for p in points], [0, 100, 200, 300, 400])
        self.assertEqual(points[0]['pc'], 0x5ea5)
        self.assertEqual(points[0]['div'], 0x44f0)
        self.assertEqual(points[0]['read_address'], 0xd040)
        self.assertEqual(points[0]['trace'], [0]*139)

    def test_reference_core_parser_rejects_incomplete_or_reordered_stops(self):
        from dex_timing.probes.compare_core import parse_core
        with self.assertRaises(ValueError):
            parse_core(self.core_text().split('\n', 1)[1])
        with self.assertRaises(ValueError):
            parse_core(self.core_text().replace('stop=2', 'stop=3'))

    def test_reference_core_parser_rejects_short_memory_dump(self):
        from dex_timing.probes.compare_core import parse_core
        with self.assertRaises(ValueError):
            parse_core(self.core_text().replace('00'*139, '00'*138, 1))

    def test_full_core_parser_requires_completion_snapshot(self):
        from dex_timing.probes.compare_core import parse_core
        text = self.core_text()+'\nstop=5 t=500 pc=047e bank=10\n'+'00'*27+'\n'+'00'*139
        self.assertEqual(parse_core(text, full=True)[-1]['t'], 500)
        with self.assertRaises(ValueError):
            parse_core(self.core_text(), full=True)
        with self.assertRaises(ValueError):
            parse_core(text)

    def test_end_to_end_core_parser_requires_four_stops_and_reads_byte_fields(self):
        from dex_timing.probes.compare_core import parse_core
        text = '\n'.join(self.core_text().splitlines()[:12])
        text = text.replace('read_address=d040',
                            'read_address=d040 audio=8940d0012902 audio_cache=1c0d02224100d2c8 timers=9bfe38fe')
        points = parse_core(text, end_to_end=True)
        self.assertEqual(points[0]['audio'], [0x89,0x40,0xd0,1,0x29,2])
        self.assertEqual(points[0]['timers'], [0x9b,0xfe,0x38,0xfe])
        with self.assertRaises(ValueError):
            parse_core(self.core_text(), end_to_end=True)

    def test_deferred_hdma_requests_coalesce(self):
        from dex_timing.replay import ReplayClock
        clock = ReplayClock(Profile(hblank_dot=257), {}, 0)
        clock.t = 100
        clock.dma = [40, 80]
        clock._collect()
        self.assertEqual(clock.dma_due, 1)
        self.assertEqual(clock.dma, [])

    def test_saved_memory_export_is_split_without_bank_aliasing(self):
        from dex_timing.probes.compare_save_state import read_export
        header=tuple(range(16))
        payload=(b'DEXCORE1'+struct.pack('<16I',*header)+bytes([1])*65536+
                 bytes([2])*32768+bytes([3])*16384)
        h,memory,banks,vram=read_export(payload)
        self.assertEqual(h,header)
        self.assertEqual(memory,bytes([1])*65536)
        self.assertEqual(banks,bytes([2])*32768)
        self.assertEqual(vram,bytes([3])*16384)
        for bad in (payload[:-1],payload+b'\0',b'INVALID!'+payload[8:]):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):
                read_export(bad)

    def test_saved_capture_observations_are_not_intermediate_core_predictions(self):
        from dex_timing.probes.compare_save_state import observed_differences
        capture=json.loads((ROOT/'tools/dex_timing/fixtures/luxray_save_state_capture.json').read_text())
        points=[dict(capture['initial']),{'t':12345},dict(capture['final'])]
        self.assertEqual(observed_differences(points,capture),{'initial':[],'final':[]})
        points[-1]['t']+=8
        points[-1]['oam_index']+=4
        self.assertEqual(observed_differences(points,capture),{'initial':[],'final':['t','oam_index']})
        ticks=capture['final_ticks_keep']
        self.assertEqual(ticks['t_cycles'],ticks['m_cycles']*4)
        self.assertEqual(ticks['absolute_8mhz_ticks'],ticks['t_cycles']*2)

    def test_saved_memory_probe_readback_preserves_bank_reserved_bits(self):
        from dex_timing.probes.compare_save_state import BankReadbackCPU
        cpu=BankReadbackCPU(bytes(32768),{})
        cpu.allowed_io.add(0xff00)
        for bank in range(8):
            cpu.write(0xff70,bank)
            self.assertEqual(cpu.read(0xff70),0xf8|bank)
        for bank in range(2):
            cpu.write(0xff4f,bank)
            self.assertEqual(cpu.read(0xff4f),0xfe|bank)
        for select in (0,0x10,0x20,0x30):
            cpu.write(0xff00,select)
            self.assertEqual(cpu.read(0xff00),0xcf|select)


class SchedulerPolicyTests(unittest.TestCase):
    def policy(self, name='early'):
        from dex_timing.scheduler_experiment import ExperimentReplay
        replay = ExperimentReplay.__new__(ExperimentReplay)
        replay.policy = name
        replay.last_action_tick = None
        replay.retired_jobs, replay.expired_jobs = set(), []
        replay.repo = SimpleNamespace(symbols={'wPokedexWRAM0Scratch':(0,0xc800),
                                             'wPokedexAnimResidentFrameIDs':(0,0xc735)})
        replay.cpu = CounterCPU(bytes(0x8000), {})
        replay.cpu.ram[0xcc60:0xcc60+49] = bytes(range(49))
        state = {'counter':255,'interval':5,'flags':5,'event':2,'loaded':49,
                 'uploaded':0,'needed':25,'remaining_dictionary':0,'target':49,'ly':0,
                 'slot':0,'frame':2}
        return replay, state

    def test_ready_prefix_is_bounded_and_stops_at_undecoded_source(self):
        from dex_timing.scheduler_experiment import ready_prefix
        self.assertEqual(ready_prefix(list(range(49)),0,49,49),20)
        self.assertEqual(ready_prefix(list(range(49)),20,49,23),3)
        self.assertEqual(ready_prefix([4,40,5],0,3,20),1)
        self.assertEqual(ready_prefix([1],1,1,20),0)
        with self.assertRaises(ModelError):
            ready_prefix([1],2,1,20)

    def test_completed_bytes_and_ownership_gate_uploads(self):
        replay, state = self.policy()
        self.assertEqual(replay.choose_action(state)[0],0xc0)
        for flags in (0,1,5|8,5|32,5|64,5|16):
            self.assertEqual(replay.choose_action(dict(state,flags=flags))[0],0)
        self.assertEqual(replay.choose_action(dict(state,loaded=0,remaining_dictionary=49))[0],0x40)

    def test_display_quota_wraps_without_skipping_progress(self):
        replay, state = self.policy()
        replay.last_action_tick = 255
        self.assertEqual(replay.choose_action(state)[0],0)
        self.assertEqual(replay.choose_action(dict(state,counter=0))[0],0xc0)

    def test_clock_job_not_consumed_until_target_complete(self):
        from dex_timing.scheduler_experiment import Job
        replay, state = self.policy('clock')
        replay.jobs = [Job(5,0xc0,2,20)]
        self.assertEqual(replay.choose_action(dict(state,interval=4))[0],0)
        self.assertEqual(replay.choose_action(state)[0],0xc0)
        self.assertEqual(replay.choose_action(dict(state,uploaded=10))[0],0xc0)
        self.assertFalse(replay.retired_jobs)
        self.assertEqual(replay.choose_action(dict(state,uploaded=20))[0],0)
        self.assertEqual(replay.retired_jobs,{0})

    def test_expired_stage_job_is_reported_not_uploaded_into_new_stage(self):
        from dex_timing.scheduler_experiment import Job
        replay, state = self.policy('clock')
        replay.jobs = [Job(0,0xc0,1,20)]
        self.assertEqual(replay.choose_action(state)[0],0)
        self.assertEqual(len(replay.expired_jobs),1)

    def test_failed_placeholder_is_not_completed_schedule_work(self):
        from dex_timing.scheduler_experiment import Job
        replay, state = self.policy('clock')
        replay.jobs = [Job(0,0xc0,2,20)]
        self.assertEqual(replay.choose_action(dict(state,flags=13,needed=0))[0],0)
        self.assertFalse(replay.retired_jobs)
        replay.cpu.ram[0xc735] = state['frame']
        self.assertEqual(replay.choose_action(dict(state,flags=13,needed=0))[0],0)
        self.assertEqual(replay.retired_jobs,{0})

    def test_window_gate_accounts_for_gather_reserve(self):
        replay, state = self.policy('window')
        self.assertEqual(replay.choose_action(dict(state,ly=59))[0],0xc0)
        self.assertEqual(replay.choose_action(dict(state,ly=60))[0],0)

    def test_nonidle_schedule_jobs_have_display_release_and_event_owner(self):
        from dex_timing.assets import Plan
        from dex_timing.scheduler_experiment import Job, jobs_from_schedule
        asset = SimpleNamespace(events=[Event(1,3,10),Event(2,3,10)],
            plans={2:Plan(10,((0,5),(1,6)))},actions=[0,1,3,0,0,0],total=10)
        self.assertEqual(jobs_from_schedule(asset,4),[Job(1,0x40,0,10),Job(2,0xc0,2,2)])


class BudgetModelTests(unittest.TestCase):
    def test_physical_vblank_audit_does_not_confuse_wrap_with_safety(self):
        from dex_timing.budget_experiment import within_vblank
        self.assertTrue(within_vblank(606,4560))
        self.assertTrue(within_vblank(FRAME+606,FRAME+4560))
        self.assertFalse(within_vblank(4500,4561))
        self.assertFalse(within_vblank(FRAME-8,FRAME))
        self.assertFalse(within_vblank(6000,6004))
        self.assertFalse(within_vblank(606,606))

    def test_oam_completion_is_a_deadline_not_an_extra_cpu_stall(self):
        from dex_timing.budget_experiment import audit_hardware
        replay = SimpleNamespace(gdma_spans=[dict(start_t=100,end_t=552)],
            hardware_writes=[dict(t=3994,address=0xff46,interrupt=True),
                             dict(t=3000,address=0xff43,interrupt=True),
                             dict(t=6000,address=0xff43,interrupt=False)])
        audit = audit_hardware(replay)
        self.assertEqual(audit['gdma_outside_vblank'],0)
        self.assertEqual(audit['writes_outside_vblank'],1)
        self.assertEqual(audit['latest_write_end_phase'],4642)
        self.assertEqual(len(audit['interrupt_hardware_writes']),2)

    def test_prefix_response_bound_is_pessimistic_and_validates_units(self):
        from dex_timing.budget_experiment import visible_prefix_bound
        values = [visible_prefix_bound(x) for x in (1024,5000,10000,20000)]
        self.assertEqual(values,sorted(values))
        self.assertGreater(values[0],1024+1480+108)
        for value in (0,-4,5):
            with self.assertRaises(ModelError):
                visible_prefix_bound(value)

    def test_window_preference_decodes_only_when_useful_not_arbitrary_idle(self):
        from dex_timing.budget_experiment import BudgetReplay
        original, state = SchedulerPolicyTests().policy('tail')
        replay = BudgetReplay.__new__(BudgetReplay)
        replay.__dict__.update(original.__dict__)
        replay.admission = True
        replay.upload_prefix_bounds = {20:35276}
        replay.clock = Clock(Profile(),False)
        replay.clock.t = 10*LINE  # Physical line 0.
        state.update(remaining_dictionary=6,target=55)
        self.assertEqual(replay.choose_action(state)[0],0xc0)
        replay.clock.t = 120*LINE  # Physical line 110; too late for gather.
        self.assertEqual(replay.choose_action(state),(0x40,'decode_instead_of_poor_upload_window'))
        self.assertEqual(replay.choose_action(dict(state,remaining_dictionary=0))[0],0xc0)
        replay.last_action_tick = state['counter']
        self.assertEqual(replay.choose_action(state)[0],0)


@unittest.skipUnless((ROOT/"pokecrystal.gbc").exists() and (ROOT/"pokecrystal.sym").exists(), "matching linked ROM required")
class QueueCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dex_timing.queue_experiment import queue_prototype,PINNED_ROM
        cls.repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
        if cls.repo.hashes['rom_sha256'] != PINNED_ROM:
            raise unittest.SkipTest('queue-copy prototype is bound to the captured ROM')
        cls.prototype=queue_prototype(cls.repo)

    def test_private_image_changes_only_two_helpers_and_four_call_operands(self):
        from dex_timing.queue_experiment import ORIGINAL,queue_prototype
        before=self.repo.rom
        allowed=set()
        for helper in self.prototype.manifest['helpers']:
            start=offset((helper['bank'],helper['new_address']))
            allowed.update(range(start,start+helper['new_size']))
            old=offset((helper['bank'],helper['old_address']))
            self.assertEqual(self.prototype.image[old:old+helper['old_size']],ORIGINAL[helper['name']])
        for call in self.prototype.manifest['calls']:
            start=offset((call['bank'],call['address']))
            allowed.update((start+1,start+2))
        changed={i for i,(a,b) in enumerate(zip(before,self.prototype.image)) if a!=b}
        self.assertTrue(changed)
        self.assertFalse(changed-allowed)
        self.assertEqual(len(before),len(self.prototype.image))
        self.assertEqual(self.prototype.manifest['private_padding_bytes'],78)
        self.assertEqual(self.prototype.manifest['eventual_replacement_romx_delta'],30)
        altered=bytearray(before)
        altered[offset((0x77,0x7c00))]=1
        with self.assertRaises(ModelError):
            queue_prototype(SimpleNamespace(rom=bytes(altered),symbols=self.repo.symbols))
        self.assertIs(self.repo.rom,before)
        self.assertEqual(sha256((ROOT/'pokecrystal.gbc').read_bytes()),sha256(before))

    def test_unrolled_helpers_preserve_bytes_write_order_and_exit_registers(self):
        from dex_timing.queue_experiment import PACKED,STRIDED
        from dex_timing.costs import machine
        for name in (PACKED,STRIDED):
            for low in range(256):
                for source_low in (0,249,255):
                    for flags in (0,0xf0):
                        with self.subTest(helper=name,dest_low=low,source_low=source_low,flags=flags):
                            pair=[]
                            for optimized in (False,True):
                                cpu=machine(self.repo)
                                cpu.rom=self.prototype.image if optimized else self.repo.rom
                                cpu.symbols=dict(cpu.symbols,probe=self.prototype.entries[name] if optimized else self.repo.symbols[name])
                                cpu.ram[0xc100:0xd000]=bytes([0xa5])*0xf00
                                cpu.wram[3][:]=bytes([0x5a])*4096
                                cpu.ram[0xff70]=3
                                source,dest=0xc300+source_low,(0xd400 if name==STRIDED else 0xc900)+low
                                cpu.block(source,bytes((i*73+19)&255 for i in range(256)))
                                cpu.set_pair(0,0x91a3)
                                cpu.set_pair(1,dest)
                                cpu.set_pair(2,source)
                                cpu.r[7],cpu.f=0xc7,flags
                                cpu.record_writes=True
                                cpu.run('probe')
                                pair.append(cpu)
                            native,unrolled=pair
                            self.assertEqual(native.cycles-unrolled.cycles,804)
                            self.assertEqual((native.r,native.f,native.sp,native.bank),
                                             (unrolled.r,unrolled.f,unrolled.sp,unrolled.bank))
                            self.assertEqual(native.ram,unrolled.ram)
                            self.assertEqual(native.wram,unrolled.wram)
                            writes=[[(a,v) for _,a,v in cpu.writes if dest<=a<dest+224] for cpu in pair]
                            self.assertEqual(writes[0],writes[1])
                            self.assertEqual(len(writes[0]),49)
                            self.assertEqual(native.ram[0xff70],3)

    def test_whole_queue_preserves_buffers_bank_restore_and_pending_handoff(self):
        from dex_timing.costs import machine
        for slot in (0,1):
            for frame in (0,1):
                for bank in (1,3,6):
                    for ring in range(5):
                        with self.subTest(slot=slot,frame=frame,bank=bank,ring=ring):
                            pair=[]
                            for optimized in (False,True):
                                cpu=machine(self.repo)
                                cpu.rom=self.prototype.image if optimized else self.repo.rom
                                cpu.ram[0xc100:0xd000]=bytes([0xa5])*0xf00
                                for b in range(1,8):
                                    cpu.wram[b][:]=bytes([0x30+b])*4096
                                cpu.ram[0xff70]=bank
                                for name,value in (('hCGB',1),('wPokedexAnimFlags',15),
                                        ('wPokedexAnimPlaybackState',2),('wPokedexAnimStageFrameID',frame),
                                        ('wPokedexAnimStageSlot',slot),('wPokedexAnimDebugMapPublishes',1),
                                        ('wPokedexAnimDebugMinReadyLead',255),('wPokedexAnimTraceHead',ring)):
                                    cpu.field(name,value)
                                scratch=self.repo.symbols['wPokedexWRAM0Scratch'][1]
                                source=scratch+(0x310 if frame==0 else 0x39c if slot==0 else 0x3fe)
                                cpu.block(source,bytes((i*73+19)&255 for i in range(98)))
                                cpu.record_writes=True
                                cpu.run('Pokedex_CommitDescriptionAnimation')
                                pair.append(cpu)
                            native,unrolled=pair
                            self.assertEqual(native.cycles-unrolled.cycles,3216)
                            self.assertEqual((native.r,native.f,native.sp,native.bank),
                                             (unrolled.r,unrolled.f,unrolled.sp,unrolled.bank))
                            self.assertEqual(native.ram,unrolled.ram)
                            self.assertEqual(native.wram,unrolled.wram)
                            self.assertEqual(native.vram,unrolled.vram)
                            self.assertEqual(unrolled.ram[0xff70],bank)
                            for cpu in pair:
                                flag=self.repo.symbols['wPokedexAnimFlags'][1]
                                pending=next(t for t,a,v in cpu.writes if a==flag and v&32)
                                copies=[t for t,a,_ in cpu.writes if 0xd021<=a<=0xd027+6*32 or 0xd261<=a<=0xd267+6*32]
                                self.assertEqual(len(copies),98)
                                self.assertGreater(pending,max(copies))

    def test_queue_cost_is_measured_from_executable_instructions(self):
        from dex_timing.queue_experiment import queue_profile
        from dex_timing.finish_experiment import finishing_costs
        native=queue_profile(self.repo)
        unrolled=queue_profile(self.repo,self.prototype)
        self.assertEqual((native['total_t'],unrolled['total_t']),(12596,9380))
        self.assertEqual((native['row_copies_t'],unrolled['row_copies_t']),(9936,6720))
        self.assertEqual(native['other_queue_t'],unrolled['other_queue_t'])
        costs=finishing_costs(self.repo,self.prototype.image)
        self.assertEqual(costs[10]['chain_bound_t'],41940)
        self.assertEqual(costs[7]['chain_bound_inactive_timer_t'],29132)

    def test_unrolled_queue_closes_known_actual_garchomp_counterexamples(self):
        from dex_timing.queue_experiment import QueueReplay
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.scheduler_experiment import candidate_summary
        from dex_timing.finish_experiment import audit_audio_reserve
        from dex_timing.budget_experiment import audit_hardware
        for phase,dispatch,guard,finish in ((None,1024,64,256),(3264,1024,64,256),
                (None,2048,64,1024),(None,2048,256,1024)):
            with self.subTest(phase=phase,dispatch=dispatch,guard=guard,finish=finish):
                replay,_=initial_replay(self.repo,'garchomp',QueueReplay,use_additional_actual=True)
                replay.configure_queue('row-unrolled',dispatch,guard,finish)
                if phase is not None:
                    replay.perturb_timer_phase(phase)
                summary=candidate_summary(replay.run(full=True),replay.asset)
                self.assertEqual(summary['full_sequence_intervals'],110)
                self.assertFalse(summary['misses'])
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                self.assertTrue(summary['audio_stops'])
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
                self.assertTrue(all(s['within_bound'] and not s['crossed_vblank'] for s in replay.finish_spans))
                self.assertTrue(all(s['ok'] for s in audit_audio_reserve(replay)))
                self.assertFalse(any(p['admitted'] and p['available_t']<p['chain_bound_t']
                                     for p in replay.finish_attempts))
                audit=audit_hardware(replay)
                self.assertEqual((audit['gdma_outside_vblank'],audit['writes_outside_vblank']),(0,0))
                self.assertIsNone(replay.open_finish)
                self.assertEqual(sha256(self.repo.rom),self.prototype.manifest['base_rom_sha256'])


@unittest.skipUnless((ROOT/'pokecrystal.gbc').exists(), 'captured ROM required')
class GatherCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dex_timing.gather_experiment import gather_prototype
        from dex_timing.queue_experiment import queue_prototype,PINNED_ROM
        cls.repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
        if cls.repo.hashes['rom_sha256']!=PINNED_ROM:
            raise unittest.SkipTest('gather prototype requires captured ROM')
        cls.prototype=gather_prototype(cls.repo,queue_prototype(cls.repo).image)

    def test_private_gather_image_is_bounded_and_fail_closed(self):
        from dex_timing.gather_experiment import gather_prototype,NAME,ORIGINAL
        from dex_timing.queue_experiment import queue_prototype
        base=queue_prototype(self.repo).image
        m=self.prototype.manifest
        entry,target=offset((m['bank'],m['entry'])),offset((m['bank'],m['target']))
        allowed=set(range(entry,entry+3))|set(range(target,target+len(bytes.fromhex(m['replacement_bytes']))))
        changed={i for i,(a,b) in enumerate(zip(base,self.prototype.image)) if a!=b}
        self.assertFalse(changed-allowed)
        self.assertEqual(m['eventual_replacement_romx_delta'],42)
        self.assertEqual(m['trampoline_t'],16)
        self.assertEqual(self.repo.rom[entry:entry+len(ORIGINAL)],ORIGINAL)
        altered=bytearray(base)
        altered[target]=1
        with self.assertRaises(ModelError):
            gather_prototype(self.repo,bytes(altered))

    def test_gather_preserves_partial_prefixes_payload_and_registers(self):
        from dex_timing.costs import machine
        from dex_timing.gather_experiment import NAME
        fixtures=[(7,n,u,r,high) for n in range(50) for u in sorted({0,min(n,20),n})
                  for r in (0,1,6,20,49) for high in (0,127)]
        fixtures += [(flags,49,0,49,0) for flags in (0,3,15)]
        for flags,needed,uploaded,ready,high in fixtures:
            with self.subTest(flags=flags,n=needed,u=uploaded,r=ready,high=high):
                pair=[]
                for optimized in (False,True):
                    cpu=machine(self.repo)
                    cpu.rom=self.prototype.image if optimized else self.repo.rom
                    cpu.ram[0xc700:0xcce6]=bytes([0xa5])*(0xcce6-0xc700)
                    cpu.wram[6][:]=bytes((i*73+19)&255 for i in range(4096))
                    cpu.ram[0xff70]=6
                    for name,value in (('wPokedexAnimFlags',flags),('wPokedexAnimStageTileCount',needed),
                            ('wPokedexAnimUploadOffset',uploaded),('wPokedexAnimDictionaryTileCount',255),
                            ('wPokedexAnimDictionaryTilesRemaining',255-high-uploaded-ready)):
                        cpu.field(name,value)
                    cpu.block(0xcc60,bytes(range(high,high+49)))
                    cpu.f=0xf0
                    cpu.record_writes=True
                    cpu.run(NAME)
                    pair.append(cpu)
                a,b=pair
                count=min(20,needed-uploaded,ready) if flags==7 else 0
                self.assertEqual(a.r[1],count)
                self.assertEqual(a.cycles-b.cycles,252*count-16)
                self.assertEqual((a.r,a.f,a.sp,a.bank),(b.r,b.f,b.sp,b.bank))
                self.assertEqual(a.ram,b.ram)
                self.assertEqual(a.wram,b.wram)
                self.assertEqual(a.vram,b.vram)
                writes=[[(address,value) for _,address,value in c.writes if 0xc800<=address<0xcb10] for c in pair]
                self.assertEqual(writes[0],writes[1])
                self.assertEqual(len(writes[0]),16*count)

    def test_finishing_envelope_includes_executable_gather_and_trampoline(self):
        from dex_timing.finish_experiment import finishing_costs
        from dex_timing.queue_experiment import queue_prototype
        queue=finishing_costs(self.repo,queue_prototype(self.repo).image)
        tile=finishing_costs(self.repo,self.prototype.image,self.prototype.image)
        for count in range(1,21):
            self.assertEqual(queue[count]['upload_prefix_t']-tile[count]['upload_prefix_t'],252*count-16)
            self.assertEqual(queue[count]['queue_t'],tile[count]['queue_t'])
            self.assertEqual(queue[count]['helper_allowance_t'],tile[count]['helper_allowance_t'])
            self.assertLess(tile[count]['chain_bound_t'],queue[count]['chain_bound_t'])

    def test_previous_smallest_headroom_case_still_finishes(self):
        from dex_timing.queue_experiment import QueueReplay
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.finish_experiment import replay_document
        replay,identity=initial_replay(self.repo,'garchomp',QueueReplay,True)
        replay.configure_queue('tile-unrolled',2048,256,1024)
        replay.perturb_timer_phase(7464)
        doc=replay_document(self.repo,replay,identity,replay.run(full=True),{})
        for key in ('misses','late_publications','duplicates','wrong_slots','wrong_maps','cry_underruns',
                    'bound_overruns','finishing_vblank_crossings','audio_reserve_violations',
                    'gdma_outside_vblank','writes_outside_vblank'):
            self.assertEqual(doc['result'][key],0,key)
        self.assertGreater(min(s['start']['available_t']-s['start']['chain_bound_t']
                               for s in replay.finish_spans),556)

    def test_explicit_margin_is_reserved_not_removed_from_measured_cost(self):
        from dex_timing.finish_experiment import finish_admission
        state=dict(ly=40,deadline=2,counter=0)
        available=(143-40)*LINE
        costs=dict(chain_bound_t=available-1024,launch_bound_t=100,
                   chain_bound_inactive_timer_t=available-1024,launch_bound_inactive_timer_t=100)
        a=finish_admission(state,8,costs,False,0,200,0,True,0)
        b=finish_admission(state,8,costs,False,0,200,0,True,4096)
        self.assertTrue(a['admitted'])
        self.assertFalse(b['admitted'])
        self.assertEqual(a['chain_bound_t'],b['chain_bound_t'])
        self.assertEqual(b['minimum_margin_t'],4096)


class SynthRegisterTests(unittest.TestCase):
    def controls(self):
        from dex_timing.sound_registers import SoundRegisters
        ram=bytearray(65536)
        ram[0xff26]=0x8b
        return SoundRegisters(ram)

    def test_read_masks_and_read_only_status(self):
        s=self.controls()
        self.assertEqual(s.read(0xff26),0xfb)
        s.write(0xff26,0x80)
        self.assertEqual(s.read(0xff26),0xfb)
        self.assertEqual(s.read(0xff11),0x3f)
        self.assertEqual(s.read(0xff1c),0x9f)

    def test_dac_disable_and_restart(self):
        s=self.controls()
        s.write(0xff12,0)
        self.assertEqual(s.read(0xff26),0xfa)
        s.ram[0xff12]=8
        s.write(0xff14,0x80)
        self.assertEqual(s.read(0xff26),0xfb)

    def test_unsupported_apu_state_fails_closed(self):
        s=self.controls()
        for address,value in ((0xff26,0),(0xff14,0xc0),(0xff10,1)):
            with self.assertRaises(ModelError):
                s.write(address,value)
        s.active|=4
        with self.assertRaises(ModelError):
            s.read(0xff30)


@unittest.skipUnless((ROOT/"pokecrystal.gbc").exists() and (ROOT/"pokecrystal.sym").exists(), "build a matching ROM for linked integration tests")
class LinkedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT/"pokecrystal.gbc", ROOT/"pokecrystal.sym")
        cls.assets = cls.repo.load()

    def test_all_asset_sets_and_partial_chunks(self):
        self.assertGreater(len(self.assets), 251)
        self.assertTrue(any(len(a.streams[-1].output) < 96 for a in self.assets))
        self.assertEqual({c for a in self.assets for s in a.streams for c, _ in s.commands}, set(range(7)))

    def test_exeggcute_matches_actual_core_instruction_fingerprint(self):
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.full_replay import summarize
        from dex_timing.sound_registers import summarize_synth
        reference=json.loads((ROOT/'tools/dex_timing/fixtures/exeggcute_synth_reference.json').read_text())
        if self.repo.hashes['rom_sha256']!=reference['rom_sha256']:
            self.skipTest('synth reference requires captured ROM')
        self.assertEqual(self.repo.hashes['sym_sha256'],reference['sym_sha256'])
        replay,identity=initial_replay(self.repo,'exeggcute',OwnerReplay,True)
        self.assertEqual(identity['fixture_sha256'],reference['initial_fixture_sha256'])
        self.assertEqual((replay.timer_tma,replay.timer_tac,replay.clock.timer_period),(0,4,262144))
        count=0
        digest=hashlib.sha256()
        original=replay.cpu.step
        def step():
            nonlocal count
            c=replay.cpu
            digest.update(struct.pack('<8I',replay.clock.t-606,c.bank if c.pc>=0x4000 else 0,
                c.pc,c.r[7]*256+c.f,*(c.pair(i) for i in range(3)),c.sp))
            count+=1
            original()
        replay.cpu.step=step
        run=replay.run(full=True)
        self.assertEqual(count,reference['instruction_count'])
        self.assertEqual(digest.hexdigest(),reference['instruction_trace_sha256'])
        self.assertEqual(summarize(run,replay.asset)['full_sequence_intervals'],113)
        audio=summarize_synth(run['synth_audio'])
        for key in ('sound_updates','hardware_write_count','hardware_sequence_sha256'):
            self.assertEqual(audio[key],reference[key])
        self.assertEqual([list(r) for r in audio['channel_completion_intervals']],reference['channel_completion_intervals'])
        self.assertTrue(audio['completed'])
        self.assertEqual(audio['max_update_gap_intervals'],1)

    def test_synth_candidate_retains_sound_work_and_exact_animation_intervals(self):
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.queue_experiment import QueueReplay,PINNED_ROM
        from dex_timing.finish_experiment import replay_document
        from dex_timing.sound_registers import summarize_synth
        if self.repo.hashes['rom_sha256']!=PINNED_ROM:
            self.skipTest('synth candidate requires captured ROM')
        reference=json.loads((ROOT/'tools/dex_timing/fixtures/exeggcute_synth_reference.json').read_text())
        for mode in ('row-unrolled','tile-unrolled'):
            for phase in (None,64,262080):
                with self.subTest(mode=mode,phase=phase):
                    replay,identity=initial_replay(self.repo,'exeggcute',QueueReplay,True)
                    replay.configure_queue(mode,2048,256,1024,4096)
                    if phase is not None:
                        replay.perturb_timer_phase(phase)
                    run=replay.run(full=True)
                    doc=replay_document(self.repo,replay,identity,run,{})
                    for key in ('misses','late_publications','duplicates','wrong_slots','wrong_maps',
                            'bound_overruns','finishing_vblank_crossings','audio_reserve_violations',
                            'gdma_outside_vblank','writes_outside_vblank'):
                        self.assertEqual(doc['result'][key],0,key)
                    audio=summarize_synth(run['synth_audio'])
                    self.assertTrue(audio['completed'])
                    self.assertEqual(audio['max_update_gap_intervals'],1)
                    for key in ('sound_updates','hardware_write_count','hardware_sequence_sha256'):
                        self.assertEqual(audio[key],reference[key])
                    self.assertEqual([list(r) for r in audio['channel_completion_intervals']],reference['channel_completion_intervals'])
                    self.assertEqual(doc['summary']['full_sequence_intervals'],113)

    def exact_luxray_text(self):
        if self.repo.hashes['rom_sha256'] != '7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f':
            self.skipTest('exact Luxray fixture is bound to the captured ROM')
        return (ROOT/'tools/dex_timing/fixtures/luxray_exact_followup.txt').read_text()

    def actual_luxray_replay(self):
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()  # All captured inputs are bound to the same ROM.
        document = json.loads((ROOT/'tools/dex_timing/fixtures/luxray_initial_volatile.json').read_text())
        payload, points = unpack(document, self.repo)
        return replay_from_export(self.repo, payload, points), document, payload

    def test_portable_fixture_removes_rom_sram_and_rejects_identity_changes(self):
        from dex_timing.fixtures import unpack
        replay, document, payload = self.actual_luxray_replay()
        self.assertEqual(payload[72:72+0xc000], bytes(0xc000))
        self.assertEqual(payload[72+0xe000:72+0xff00], bytes(0x1f00))
        self.assertEqual(replay.cpu.sp, 0xc0af)
        for key in ('rom_sha256', 'sym_sha256', 'payload_sha256'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                unpack(dict(document, **{key:'0'*64}), self.repo)

    def test_full_actual_luxray_replay_retains_first_miss_and_reaches_cleanup(self):
        from dex_timing.full_replay import summarize
        replay, document, payload = self.actual_luxray_replay()
        run = replay.run(full=True)
        summary = summarize(run, replay.asset)
        self.assertEqual([p['t']-606 for p in run['points']],
                         [0, 36964, 62724, 67956, 2004944, 6477124])
        self.assertEqual(len(summary['misses']), 4)
        self.assertEqual(len(summary['publications']), 15)
        self.assertEqual(sum(p['late_intervals'] > 0 for p in summary['publications']), 2)
        self.assertEqual(summary['full_sequence_intervals'], 92)
        self.assertEqual(summary['audio_stops'],
                         [{'t':6451536,'remaining':0,'cache':0,'reason':'natural'}])
        self.assertTrue(all(p['remaining_dictionary'] == 0 for p in summary['misses']))
        self.assertEqual(replay.cpu.ram[self.repo.symbols['wPokedexAnimPlaybackState'][1]], 3)
        self.assertEqual(replay.timer_tac, 4)  # Original music timer restored.
        self.assertEqual(replay.clock.timer_period, (256-replay.timer_tma)*1024)
        self.assertFalse(replay.open_operations)
        self.assertEqual(document['payload_sha256'], sha256(payload))

    def test_full_actual_weavile_and_dusknoir_match_four_user_checkpoints(self):
        from dex_timing.end_to_end import read_capture, host_points, differences
        from dex_timing.fixtures import unpack
        from dex_timing.full_replay import summarize
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()  # These captures share the same linked build.
        for name, misses, remaining in (('weavile',6,0), ('dusknoir',24,333)):
            with self.subTest(species=name):
                document = json.loads((ROOT/f'tools/dex_timing/fixtures/{name}_initial_volatile.json').read_text())
                payload, points = unpack(document, self.repo)
                replay = replay_from_export(self.repo,payload,points,species=name)
                before = (replay.clock.t,replay.cpu.cycles,replay.advanced)
                replay.snapshot('Read-only snapshot')
                self.assertEqual((replay.clock.t,replay.cpu.cycles,replay.advanced), before)
                run = replay.run(full=True)
                capture = read_capture((ROOT/f'tools/dex_timing/fixtures/{name}_end_to_end.txt').read_text(),self.repo.symbols)
                self.assertFalse(any(differences(host_points(run),capture)))
                summary = summarize(run,replay.asset)
                self.assertEqual(len(summary['misses']), misses)
                self.assertEqual(summary['audio_stops'][0]['remaining'], remaining)
                self.assertEqual(replay.timer_tac, 4)
                self.assertFalse(replay.open_operations)

    def test_full_replay_fails_closed_at_explicit_time_bound(self):
        replay, _, _ = self.actual_luxray_replay()
        with self.assertRaisesRegex(ModelError, 'bounded completion'):
            replay.run(full=True, max_frames=1)

    def test_scheduler_ledger_does_not_change_linked_baseline(self):
        from dex_timing.scheduler_experiment import ExperimentReplay
        from dex_timing.probes.compare_save_state import replay_from_export
        _, document, payload = self.actual_luxray_replay()
        from dex_timing.fixtures import unpack
        _, points = unpack(document,self.repo)
        replay = replay_from_export(self.repo,payload,points,replay_class=ExperimentReplay)
        replay.configure('baseline')
        run = replay.run(full=True)
        self.assertEqual([p['t']-606 for p in run['points']],
                         [0,36964,62724,67956,2004944,6477124])
        self.assertFalse(replay.open_ledger)
        self.assertTrue(replay.publication_checks)
        self.assertFalse(replay.waits)

    def budget_replay(self, species='luxray', cutoff=146, quiet=False, admission=False,
                      policy='tail'):
        from dex_timing.budget_experiment import BudgetReplay
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()
        document = json.loads((ROOT/f'tools/dex_timing/fixtures/{species}_initial_volatile.json').read_text())
        payload, points = unpack(document,self.repo)
        replay = replay_from_export(self.repo,payload,points,species,BudgetReplay)
        replay.configure_budget(cutoff,policy,1024,quiet,admission)
        return replay

    def test_hardware_audit_preserves_calibrated_baseline_timing(self):
        replay = self.budget_replay(policy='baseline')
        run = replay.run(full=True)
        self.assertEqual([p['t']-606 for p in run['points']],
                         [0,36964,62724,67956,2004944,6477124])
        self.assertTrue(replay.guard_reads)
        self.assertTrue(replay.map_checks)
        self.assertFalse(replay.oam_locked)
        self.assertIs(replay.cpu.rom,self.repo.rom)

    def test_wider_window_alone_preserves_unsafe_oam_counterexample(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        replay = self.budget_replay(cutoff=149)
        summary = candidate_summary(replay.run(full=True),replay.asset)
        audit = audit_hardware(replay)
        self.assertFalse(summary['misses'])
        self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
        self.assertEqual(audit['gdma_outside_vblank'],0)
        self.assertEqual(audit['writes_outside_vblank'],1)
        self.assertEqual(audit['latest_write_end_phase'],4642)
        self.assertEqual([r['address'] for r in audit['interrupt_hardware_writes']
                          if not r['inside_vblank']],[0xff46])

    def test_quiet_oam_window_completes_three_actual_continuations(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        for species in ('weavile','luxray','dusknoir'):
            with self.subTest(species=species):
                replay = self.budget_replay(species,149,True)
                run = replay.run(full=True)
                summary, audit = candidate_summary(run,replay.asset),audit_hardware(replay)
                self.assertFalse(summary['misses'])
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                self.assertTrue(summary['audio_stops'])
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(replay.competing_transfers)
                self.assertFalse(audit['gdma_outside_vblank'])
                self.assertFalse(audit['writes_outside_vblank'])
                self.assertEqual(run['totals_t']['policy_oam_lock'],48)
                self.assertFalse(any(p['address']==0xff46 for p in replay.hardware_writes))

    def test_quiet_oam_preconditions_and_lifetime_fail_closed(self):
        replay = self.budget_replay(quiet=True)
        replay.step()
        self.assertTrue(replay.oam_locked)
        self.assertEqual(replay.clock.t,654)
        replay.full = True
        replay.cpu.bank,replay.cpu.pc = self.repo.symbols['Pokedex.main']
        replay.cpu.ram[self.repo.symbols['wShadowOAM'][1]] = 1
        with self.assertRaisesRegex(ModelError,'lifetime'):
            replay.observe()
        replay = self.budget_replay()
        replay.cpu.ram[0xfe00] = 1
        with self.assertRaisesRegex(ModelError,'already-published empty OAM'):
            replay.configure_budget(149,quiet_oam=True)

    def test_publication_branch_bound_does_not_certify_late_line_148(self):
        from dex_timing.budget_experiment import publication_budget
        bounds = publication_budget(self.repo)
        self.assertEqual(len(bounds['rows']),144)
        self.assertEqual(bounds['maxima'],{'False:False':3464,'False:True':3604,
                                          'True:False':2276,'True:True':2416})
        pairs = {(r['frame'],r['published'],r['late'],r['carry'],r['max_late']):r
                 for r in bounds['rows'] if not r['quiet_oam']}
        for r in bounds['rows']:
            if r['quiet_oam']:
                other = pairs[(r['frame'],r['published'],r['late'],r['carry'],r['max_late'])]
                self.assertEqual(other['done_oam_from_cp_t']-r['done_oam_from_cp_t'],700)
        # An LY read can precede the CP boundary by four T. Even when ordinary
        # publication fits at the last possible LY=148 read, a late path does not.
        latest_cp = (149-144)*LINE-1+4
        self.assertLessEqual(latest_cp+2276,10*LINE)
        self.assertGreater(latest_cp+2416,10*LINE)

    def test_upload_prefix_bound_counts_linked_work_not_just_dma(self):
        from dex_timing.budget_experiment import upload_prefix_costs,visible_prefix_bound
        costs = upload_prefix_costs(self.repo)
        self.assertEqual({n:costs[n] for n in (4,8,13,20)},
                         {4:5188,8:8932,13:13612,20:20116})
        self.assertEqual(visible_prefix_bound(costs[20]+124+LINE+128),35276)

    def test_former_dusknoir_phase_failures_are_checked_with_physical_writes(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        for delay, admission in ((2464,False),(10464,True)):
            replay = self.budget_replay('dusknoir',149,True,admission)
            replay.perturb_timer_phase(delay)
            summary = candidate_summary(replay.run(full=True),replay.asset)
            self.assertFalse(summary['misses'])
            self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
            self.assertFalse(audit_hardware(replay)['writes_outside_vblank'])
            self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))

    def test_earlier_safe_window_retains_downstream_dusknoir_failure(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        replay = self.budget_replay('dusknoir',148,True)
        replay.perturb_timer_phase(10464)
        summary = candidate_summary(replay.run(full=True),replay.asset)
        self.assertEqual([(p['event'],p['uploaded'],p['needed'],p['remaining_dictionary'])
                          for p in summary['misses']],[(23,20,31,0)])
        self.assertEqual([(p['event'],p['expected_interval'],p['interval'])
                          for p in summary['publications'] if p['late_intervals']],
                         [(12,45,46),(22,82,83)])
        self.assertEqual(sum(bool(p['mismatched_cells']) for p in replay.map_checks),1)
        self.assertFalse(audit_hardware(replay)['writes_outside_vblank'])

    def recovery_replay(self, species='luxray', **options):
        from dex_timing.recovery_experiment import initial_replay
        self.exact_luxray_text()
        replay,identity = initial_replay(self.repo,species)
        replay.configure_recovery(**options)
        return replay,identity

    def test_steady_publication_bound_has_margin_on_both_bookkeeping_paths(self):
        from dex_timing.budget_experiment import publication_budget
        bounds = publication_budget(self.repo,hold_viewport=True)
        self.assertEqual(len(bounds['rows']),144)
        self.assertEqual(bounds['maxima']['True:False'],1408)
        self.assertEqual(bounds['maxima']['True:True'],1424)
        # Includes CP 144 / JR C before the old upper comparison. The LY read
        # was four T before this boundary. No assumption about the entry dot.
        latest_entry = 5*LINE-1+4
        self.assertEqual(10*LINE-latest_entry-1424,853)
        self.assertGreater(10*LINE-latest_entry-1424,LINE)

    def test_steady_display_contract_rejects_viewport_and_request_changes(self):
        from dex_timing.recovery_experiment import VIEWPORT,REQUESTS
        for name in [*(n for n,_ in VIEWPORT),*REQUESTS,'wPokedexSelectedState']:
            with self.subTest(field=name):
                replay,_ = self.recovery_replay()
                replay.cpu.field(name,replay.field_value(name)^1)
                with self.assertRaisesRegex(ModelError,'Steady-display'):
                    replay.step()
        replay,_ = self.recovery_replay()
        replay.cpu.ram[0xff43] ^= 1
        with self.assertRaisesRegex(ModelError,'viewport ownership'):
            replay.step()

    def test_steady_lower_guard_rejects_ly_zero_with_costed_taken_branch(self):
        replay,_ = self.recovery_replay()
        replay.step()  # Existing OAM lock, 48 T.
        replay.cpu.bank,replay.cpu.pc = replay.cutoff_pc
        replay.cpu.r[7] = 0
        start = replay.clock.t
        replay.step()
        self.assertEqual(replay.clock.t-start,20)
        self.assertEqual(replay.cpu.pc,self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.defer'][1])
        self.assertFalse(replay.range_checks[-1]['admitted'])

    def test_steady_controls_keep_all_three_actual_maps_and_cries_correct(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        for species in ('luxray','weavile','dusknoir'):
            with self.subTest(species=species):
                replay,identity = self.recovery_replay(species)
                run = replay.run(full=True)
                summary = candidate_summary(run,replay.asset)
                self.assertEqual(identity['initial_state_scope'],'ACTUAL_INITIAL_VOLATILE_MEMORY')
                self.assertFalse(summary['misses'])
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(audit_hardware(replay)['gdma_outside_vblank'])
                self.assertFalse(audit_hardware(replay)['interrupt_hardware_writes'])
                self.assertEqual(run['totals_t']['policy_viewport_guard'],64*len(replay.viewport_skips))

    def test_steady_recovery_rejects_late_window_without_hiding_lateness(self):
        from dex_timing.budget_experiment import audit_hardware
        from dex_timing.scheduler_experiment import candidate_summary
        for phase in (2276,4108,4564):
            with self.subTest(phase=phase):
                replay,_ = self.recovery_replay('weavile',forced_entry_phase=phase)
                summary = candidate_summary(replay.run(full=True),replay.asset)
                self.assertIsNotNone(replay.forced_entry)
                self.assertFalse(summary['misses'])
                self.assertEqual(sum(p['late_intervals']>0 for p in summary['publications']),1)
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(audit_hardware(replay)['gdma_outside_vblank'])
                self.assertTrue(any(not p['admitted'] for p in replay.range_checks))

    def test_partial_residents_are_explicit_initial_assumptions_not_future_lead(self):
        from dex_timing.recovery_experiment import initial_replay,seed_partial_residents
        from dex_timing.full_replay import PARTIAL
        for species in PARTIAL:
            with self.subTest(species=species):
                replay,identity = initial_replay(self.repo,species)
                self.assertIn('PARTIAL_CAPTURE_CANONICAL_INITIAL_RESIDENTS',identity['initial_state_scope'])
                before = (bytes(replay.cpu.ram[0xc72e:0xc749]),bytes(replay.cpu.wram[6]),
                          bytes(replay.cpu.vram[1]),bytes(replay.cpu.wram[3]))
                seed_partial_residents(replay)
                self.assertEqual(before,(bytes(replay.cpu.ram[0xc72e:0xc749]),bytes(replay.cpu.wram[6]),
                                         bytes(replay.cpu.vram[1]),bytes(replay.cpu.wram[3])))

    def test_broader_partial_continuations_retain_garchomp_work_failure(self):
        from dex_timing.full_replay import PARTIAL
        from dex_timing.scheduler_experiment import candidate_summary
        for species in PARTIAL:
            with self.subTest(species=species):
                replay,_ = self.recovery_replay(species)
                summary = candidate_summary(replay.run(full=True),replay.asset)
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                if species == 'garchomp':
                    self.assertEqual([(p['event'],p['frame'],p['uploaded'],p['needed'],p['remaining_dictionary'])
                                      for p in summary['misses']],[(5,4,20,30,0)])
                    self.assertEqual(sum(bool(p['mismatched_cells']) for p in replay.map_checks),1)
                else:
                    self.assertFalse(summary['misses'])
                    self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                    self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))

    def finish_replay(self, species='garchomp', **options):
        from dex_timing.finish_experiment import FinishReplay
        from dex_timing.recovery_experiment import initial_replay
        self.exact_luxray_text()
        replay,_=initial_replay(self.repo,species,FinishReplay)
        replay.configure_finish(**options)
        return replay

    def test_finish_bound_counts_queue_and_prices_hardware_not_just_gather(self):
        from dex_timing.finish_experiment import finishing_costs,drained_visible_bound
        costs=finishing_costs(self.repo)
        self.assertEqual(len(costs),20)
        self.assertEqual(costs[10]['upload_prefix_t'],10596)
        self.assertEqual(costs[10]['upload_suffix_t'],552)
        self.assertEqual(costs[10]['queue_t'],12596)
        self.assertEqual(costs[10]['helper_allowance_t'],5300)
        self.assertEqual(costs[10]['chain_bound_t'],46236)
        self.assertEqual(costs[10]['unknown_entry_chain_bound_t'],48256)
        self.assertEqual(costs[10]['inactive_timer_irq_t'],104)
        self.assertEqual(costs[7]['chain_bound_inactive_timer_t'],33428)
        self.assertTrue(all(c['chain_bound_no_timer_t'] < c['chain_bound_inactive_timer_t']
                            < c['chain_bound_t'] for c in costs.values()))
        self.assertTrue(all(costs[i]['chain_bound_t'] < costs[i+1]['chain_bound_t'] for i in range(1,20)))
        for invalid in (0,-4,3):
            with self.assertRaises(ModelError):
                drained_visible_bound(invalid)

    def test_finish_admission_is_coarse_clock_and_fails_closed(self):
        from dex_timing.finish_experiment import finishing_costs,finish_admission
        cost=finishing_costs(self.repo)[10]
        state=dict(deadline=15,counter=14,ly=36)
        result=finish_admission(state,10,cost,True,72,200,146)
        self.assertTrue(result['admitted'])
        self.assertEqual(result['available_t'],48792)
        self.assertEqual(result['cache_reserve'],16)
        for fields in (dict(ly=43),dict(ly=144),dict(deadline=14),dict(ly=153)):
            with self.subTest(fields=fields):
                self.assertFalse(finish_admission(dict(state,**fields),10,cost,True,72,200,146)['admitted'])
        self.assertFalse(finish_admission(state,10,cost,True,15,200,146)['admitted'])
        self.assertFalse(finish_admission(state,10,cost,True,72,160,146)['admitted'])
        # Cached last blocks need no future refill; do not regress Bastiodon.
        self.assertTrue(finish_admission(state,10,cost,True,4,200,4)['admitted'])
        self.assertFalse(finish_admission(state,10,cost,True,3,200,4)['admitted'])

    def test_finish_inactive_timer_still_costs_time_without_sample_playback(self):
        from dex_timing.finish_experiment import finishing_costs,finish_admission
        cost=finishing_costs(self.repo)[7]
        state=dict(deadline=146,counter=145,ly=65)
        self.assertFalse(finish_admission(state,7,cost,True,40,200,146)['admitted'])
        stopped=finish_admission(state,7,cost,False,0,200,0)
        self.assertTrue(stopped['admitted'])
        self.assertEqual(stopped['chain_bound_t'],33428)
        self.assertEqual(stopped['cache_reserve'],0)
        disabled=finish_admission(state,7,cost,False,0,200,0,False)
        self.assertTrue(disabled['admitted'])
        self.assertLess(disabled['chain_bound_t'],stopped['chain_bound_t'])
        with self.assertRaises(ModelError):
            finish_admission(state,7,cost,True,40,200,146,False)

    def test_additional_actual_starting_fixtures_are_sanitized_and_at_owner_entry(self):
        from dex_timing.fixtures import unpack
        from dex_timing.probes.import_starting_states import SLOTS
        self.exact_luxray_text()
        for species in SLOTS:
            with self.subTest(species=species):
                document=json.loads((ROOT/f'tools/dex_timing/fixtures/{species}_initial_volatile.json').read_text())
                payload,points=unpack(document,self.repo)
                self.assertEqual((points[0]['bank'],points[0]['pc']),(0x77,0x5ea5))
                self.assertEqual(payload[72:72+0xc000],bytes(0xc000))
                self.assertEqual(payload[72+0xe000:72+0xff00],bytes(0x1f00))
                self.assertEqual(len(points),1)
                self.assertEqual(document['scope'],'actual_initial_volatile_memory_no_later_state_injection')

    def test_finish_all_nine_actual_nominal_starts_complete_without_hiding_misses(self):
        from dex_timing.finish_experiment import FinishReplay,audit_audio_reserve
        from dex_timing.full_replay import ACTUAL,PARTIAL
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.scheduler_experiment import candidate_summary
        from dex_timing.budget_experiment import audit_hardware
        self.exact_luxray_text()
        for species in (*ACTUAL,*PARTIAL):
            with self.subTest(species=species):
                replay,identity=initial_replay(self.repo,species,FinishReplay,use_additional_actual=True)
                self.assertEqual(identity['initial_state_scope'],'ACTUAL_INITIAL_VOLATILE_MEMORY')
                replay.configure_finish('early-budget')
                summary=candidate_summary(replay.run(full=True),replay.asset)
                self.assertFalse(summary['misses'])
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                self.assertTrue(summary['audio_stops'])
                self.assertTrue(all(p['reason']=='natural' for p in summary['audio_stops']))
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
                self.assertTrue(all(s['within_bound'] and not s['crossed_vblank'] for s in replay.finish_spans))
                self.assertTrue(all(s['ok'] for s in audit_audio_reserve(replay)))
                audit=audit_hardware(replay)
                self.assertEqual((audit['gdma_outside_vblank'],audit['writes_outside_vblank']),(0,0))
                if species=='garchomp':
                    self.assertEqual([(s['start']['event'],s['start']['count'])
                                      for s in replay.finish_spans],[(2,9),(3,7),(5,10),(12,7)])
                    self.assertFalse(replay.finish_spans[-1]['start']['active_audio'])
                    self.assertTrue(replay.finish_spans[-1]['start']['timer_enabled'])

    def test_finish_probe_and_budget_keep_garchomp_event_five_complete(self):
        from dex_timing.scheduler_experiment import candidate_summary
        from dex_timing.finish_experiment import audit_audio_reserve
        from dex_timing.budget_experiment import audit_hardware
        for mode in ('probe','budget','early-budget'):
            with self.subTest(mode=mode):
                replay=self.finish_replay(mode=mode)
                summary=candidate_summary(replay.run(full=True),replay.asset)
                self.assertFalse(summary['misses'])
                self.assertFalse(summary['duplicate_publications'])
                self.assertTrue(all(p['late_intervals']==0 for p in summary['publications']))
                span=next(s for s in replay.finish_spans if s['start']['event']==5)
                self.assertEqual((span['start']['uploaded'],span['start']['needed']),(20,30))
                self.assertEqual(span['upload_end']['uploaded'],30)
                self.assertTrue(span['within_bound'])
                self.assertFalse(span['crossed_vblank'])
                self.assertFalse(any(p['mismatched_cells'] for p in replay.map_checks))
                self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
                self.assertTrue(all(s['ok'] for s in audit_audio_reserve(replay)))
                self.assertFalse(audit_hardware(replay)['gdma_outside_vblank'])
                self.assertIsNone(replay.open_finish)
                self.assertIs(replay.cpu.rom,self.repo.rom)

    def test_finish_eight_tile_control_still_fails_garchomp(self):
        from dex_timing.scheduler_experiment import candidate_summary
        replay=self.finish_replay(mode='eight')
        summary=candidate_summary(replay.run(full=True),replay.asset)
        self.assertEqual([(p['event'],p['uploaded'],p['needed']) for p in summary['misses']],[(5,20,30)])

    def test_finish_high_cost_rejection_remains_a_visible_miss(self):
        from dex_timing.scheduler_experiment import candidate_summary
        replay=self.finish_replay(mode='early-budget',dispatch_t=2048,
                                  viewport_guard_t=256,finish_guard_t=1024)
        summary=candidate_summary(replay.run(full=True),replay.asset)
        self.assertEqual([(p['event'],p['uploaded'],p['needed']) for p in summary['misses']],[(5,20,30)])
        attempt=next(a for a in replay.finish_attempts if a['event']==5)
        self.assertFalse(attempt['admitted'])
        self.assertEqual(attempt['reason'],'insufficient_visible_time')
        self.assertEqual(sum(bool(p['mismatched_cells']) for p in replay.map_checks),1)

    def test_finish_actual_garchomp_phase_margin_failure_is_not_hidden(self):
        from dex_timing.finish_experiment import FinishReplay
        from dex_timing.recovery_experiment import initial_replay
        from dex_timing.scheduler_experiment import candidate_summary
        self.exact_luxray_text()
        replay,_=initial_replay(self.repo,'garchomp',FinishReplay,use_additional_actual=True)
        replay.configure_finish('early-budget')
        replay.perturb_timer_phase(3264)
        summary=candidate_summary(replay.run(full=True),replay.asset)
        self.assertEqual([(p['event'],p['uploaded'],p['needed']) for p in summary['misses']],[(5,20,30)])
        attempt=next(a for a in replay.finish_attempts if a['event']==5)
        self.assertFalse(attempt['admitted'])
        self.assertEqual(attempt['chain_bound_t']-attempt['available_t'],180)
        self.assertFalse(any(not s['within_bound'] for s in replay.finish_spans))
        self.assertEqual(sum(bool(p['mismatched_cells']) for p in replay.map_checks),1)

    def test_selected_wait_guard_reaches_real_caller_and_charges_work(self):
        from dex_timing.scheduler_experiment import ExperimentReplay
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()
        document = json.loads((ROOT/'tools/dex_timing/fixtures/weavile_initial_volatile.json').read_text())
        payload, points = unpack(document,self.repo)
        replay = replay_from_export(self.repo,payload,points,'weavile',ExperimentReplay)
        replay.configure('wait')
        run = replay.run(full=True)
        self.assertTrue(any(w['skipped'] for w in replay.waits))
        self.assertEqual(run['totals_t']['policy_wait_guard'],64*len(replay.waits))
        self.assertFalse(replay.decisions)
        self.assertFalse(replay.open_ledger)

    def test_counterfactual_tail_keeps_full_sequence_and_audio_without_hiding_lateness(self):
        from dex_timing.scheduler_experiment import ExperimentReplay, candidate_summary
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()
        for name, late in (('weavile',0),('luxray',1),('dusknoir',1)):
            document = json.loads((ROOT/f'tools/dex_timing/fixtures/{name}_initial_volatile.json').read_text())
            payload, points = unpack(document,self.repo)
            replay = replay_from_export(self.repo,payload,points,name,ExperimentReplay)
            replay.configure('tail')
            run = replay.run(full=True)
            summary = candidate_summary(run,replay.asset)
            self.assertFalse(summary['misses'])
            self.assertFalse(summary['duplicate_publications'])
            self.assertEqual(sum(p['late_intervals'] > 0 for p in summary['publications']),late)
            self.assertTrue(all(p['remaining'] == 0 for p in summary['audio_stops']))
            self.assertFalse(any(p['mismatched_slot_tiles'] for p in replay.publication_checks))
            self.assertTrue(all(0 < p['needed']-p['uploaded'] <= 8 for p in replay.tail_calls))
            self.assertEqual(sum(x['kind']=='deferred' for x in replay.audio_moves),
                             sum(x['kind']=='serviced_after_owner' for x in replay.audio_moves))
            self.assertFalse(replay.open_ledger)
            self.assertIs(replay.cpu.rom,self.repo.rom)

    def test_timer_phase_control_preserves_latched_interrupt_and_is_not_capture(self):
        from dex_timing.scheduler_experiment import ExperimentReplay
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        _, document, payload = self.actual_luxray_replay()
        _, points = unpack(document,self.repo)
        replay = replay_from_export(self.repo,payload,points,replay_class=ExperimentReplay)
        replay.configure('tail')
        pending = set(replay.clock.pending)
        replay.perturb_timer_phase(2464)
        self.assertEqual(replay.clock.next_timer-replay.clock.t,2464)
        self.assertEqual(replay.clock.pending,pending)
        self.assertEqual((replay.clock.t+replay.div_origin+2464-4) % 64,0)
        with self.assertRaises(ModelError):
            replay.perturb_timer_phase(3)

    def test_phase_sweep_failure_remains_visible(self):
        from dex_timing.scheduler_experiment import ExperimentReplay, candidate_summary
        from dex_timing.fixtures import unpack
        from dex_timing.probes.compare_save_state import replay_from_export
        self.exact_luxray_text()
        document = json.loads((ROOT/'tools/dex_timing/fixtures/dusknoir_initial_volatile.json').read_text())
        payload, points = unpack(document,self.repo)
        replay = replay_from_export(self.repo,payload,points,'dusknoir',ExperimentReplay)
        replay.configure('tail')
        replay.perturb_timer_phase(2464)
        run = replay.run(full=True)
        summary = candidate_summary(run,replay.asset)
        self.assertEqual([(p['event'],p['uploaded'],p['needed']) for p in summary['misses']],[(6,29,34)])
        self.assertEqual(summary['audio_stops'][0]['remaining'],0)
        self.assertEqual(sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),1)

    def test_mode_zero_hdma_launch_is_immediately_pending(self):
        replay, _ = self.captured_replay()
        replay.clock.t = 10*LINE+260
        replay.opcode = 0xe0
        replay.cpu.ram[0xff51:0xff55] = bytes([0xc8,0,0x10,0])
        replay.start_dma(0x81)
        self.assertEqual(sorted(replay.clock.dma), [10*LINE+268,11*LINE+259])

    def test_gdma_copies_to_selected_vram_bank_at_next_boundary(self):
        replay, _ = self.captured_replay()
        replay.cpu.ram[0xc800:0xc810] = bytes(range(16))
        replay.cpu.ram[0xff51:0xff55] = bytes([0xc8,0,0x10,0])
        replay.cpu.ram[0xff4f] = 1
        replay.start_dma(0)
        self.assertNotEqual(replay.cpu.vram[1][0x1000:0x1010], bytes(range(16)))
        replay.step()
        self.assertEqual(replay.cpu.vram[1][0x1000:0x1010], bytes(range(16)))
        self.assertEqual(replay.gdma_due, 0)

    def test_exact_luxray_capture_intervals(self):
        stops = read_stops(self.exact_luxray_text(), self.repo.symbols)
        legs = observed_legs(stops)
        self.assertEqual([s['debugger_clock']['t_cycles'] for s in stops],
                         [71629084, 36964, 62940, 68280, 2004924])
        self.assertEqual([l['nominal_t'] for l in legs], [36964, 25976, 5340, 1936644])
        self.assertEqual([l['timer_nominal_t'] for l in legs], [36928, 25984, 5376, 1936640])
        self.assertTrue(all(l['min_t'] == l['max_t'] == l['nominal_t'] for l in legs))

    def test_exact_luxray_capture_rejects_incomplete_clocks(self):
        text = self.exact_luxray_text()
        with self.assertRaisesRegex(ModelError, 'all four later stops'):
            read_stops(text.replace('ticks keep:', 'missing:', 1), self.repo.symbols)

    def test_exact_luxray_capture_rejects_timer_disagreement(self):
        stops = read_stops(self.exact_luxray_text(), self.repo.symbols)
        stops[-1]['debugger_clock']['t_cycles'] += 1000
        with self.assertRaisesRegex(ModelError, 'disagrees'):
            observed_legs(stops)

    def test_boundary_probe_preserves_luxray_eight_cycle_residual(self):
        from dex_timing.probes.boundary_sensitivity import DeferredClock, DeferredReplay
        stops = read_stops(self.exact_luxray_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == 'luxray')
        profile = Profile(hblank_dot=257, audio_phase_t=658, audio_played_at_publication=4)
        with patch('dex_timing.replay.ReplayClock', DeferredClock):
            replay = DeferredReplay(self.repo, asset, stops, profile, 606, 16)
        result = replay.run()
        self.assertEqual(result['elapsed_t'], [36964, 25976, 5340, 1936652])
        self.assertEqual(captured_state_differences(self.repo, result['points'], stops), [])
        self.assertTrue(all(not s['bytes'] for s in captured_trace_differences(self.repo, result['points'], stops)))
        self.assertIn(16, matching_div_phases(result['points'], stops, 658))
        self.assertEqual([t-l['nominal_t'] for t, l in zip(result['elapsed_t'], observed_legs(stops))], [0, 0, 0, 8])

    def test_reference_core_fixture_preserves_screen_without_mutating_host(self):
        from dex_timing.probes.boundary_sensitivity import DeferredClock, DeferredReplay
        from dex_timing.probes.export_core_fixture import fixture_bytes
        stops = read_stops(self.exact_luxray_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == 'luxray')
        with patch('dex_timing.replay.ReplayClock', DeferredClock):
            replay = DeferredReplay(self.repo, asset, stops,
                Profile(hblank_dot=257, audio_phase_t=658, audio_played_at_publication=4), 606, 16)
        before = bytes(replay.cpu.ram)
        data = fixture_bytes(replay, stops, 606, 16)
        self.assertEqual(len(data), 114760)
        self.assertEqual(data[:8], b'DEXCORE1')
        header = struct.unpack('<16I', data[8:72])
        self.assertEqual(header[0], 606)
        self.assertEqual(header[6:8], (0x5ea5, 0x77))
        self.assertEqual(header[10:16], (0x4410, 0xff, 56, 6, 0, 15))
        for name, expected in (('hSCX', 5), ('hWX', 167), ('hWY', 0)):
            self.assertEqual(data[72+self.repo.symbols[name][1]], expected)
        self.assertEqual(bytes(replay.cpu.ram), before)
        negative = fixture_bytes(replay, stops, 606, 16, zero_scroll_shadows=True)
        self.assertEqual(negative[72:72+65536], before)

    def test_reference_probe_halt_edge_refetches_without_wake_penalty(self):
        from dex_timing.probes.boundary_sensitivity import DeferredClock, PendingHaltReplay
        stops=read_stops(self.exact_luxray_text(),self.repo.symbols)
        asset=next(a for a in self.assets if a.name=='luxray')
        for next_timer,expected_t,pc_delta in ((546,546,0),(554,558,1)):
            with self.subTest(next_timer=next_timer):
                with patch('dex_timing.replay.ReplayClock',DeferredClock):
                    replay=PendingHaltReplay(self.repo,asset,stops,
                        Profile(hblank_dot=257,audio_phase_t=658,audio_played_at_publication=4),606,16)
                pc=self.repo.symbols['DelayFrame.halt'][1]
                replay.cpu.pc=pc
                replay.masked=False
                replay.clock.t=542
                replay.clock.pending=set()
                replay.clock.next_timer=next_timer
                replay.step()
                self.assertEqual(replay.clock.t,expected_t)
                self.assertEqual(replay.cpu.pc,pc+pc_delta)
                self.assertEqual(replay.clock.pending,{'timer'})

    def test_save_state_probe_restores_real_stack_and_rejects_unknown_phase(self):
        from dex_timing.probes.boundary_sensitivity import DeferredClock, DeferredReplay
        from dex_timing.probes.export_core_fixture import fixture_bytes
        from dex_timing.probes.compare_save_state import replay_from_export
        stops=read_stops(self.exact_luxray_text(),self.repo.symbols)
        asset=next(a for a in self.assets if a.name=='luxray')
        with patch('dex_timing.replay.ReplayClock',DeferredClock):
            synthetic=DeferredReplay(self.repo,asset,stops,
                Profile(hblank_dot=257,audio_phase_t=658,audio_played_at_publication=4),606,16)
        synthetic.cpu.sp=0xc0af
        synthetic.cpu.ram[0xc0af:0xc0b1]=bytes([0xfb,0x5c])
        payload=fixture_bytes(synthetic,stops,606,16)
        point={'div_cycles':-3,'div_state':2,'pending_cycles':0,'ly':145,
               'remain':300,'ime':0,'model':0x205,'scx':5,'wx':167,'wy':0}
        replay=replay_from_export(self.repo,payload,[point])
        self.assertEqual(replay.cpu.sp,0xc0af)
        self.assertEqual(replay.cpu.ram[0xc0af:0xc0b1],bytes([0xfb,0x5c]))
        self.assertEqual(replay.clock.next_timer,658)
        self.assertEqual(replay.cpu.wram,synthetic.cpu.wram)
        for key,value in (('div_cycles',-2),('pending_cycles',4),('model',0x203),('scx',0)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                replay_from_export(self.repo,payload,[dict(point,**{key:value})])

    def captured_replay(self, stops=None):
        if self.repo.hashes["rom_sha256"] != "7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f":
            self.skipTest("five-stop regression fixture is bound to the captured ROM")
        if stops is None:
            stops = read_stops((ROOT/"tools/dex_timing/fixtures/weavile_owner_followup.txt").read_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == "weavile")
        profile = Profile(hblank_dot=257, audio_phase_t=678, audio_played_at_publication=4)
        return OwnerReplay(self.repo, asset, stops, profile, 606, 60), stops

    def test_weavile_partial_state_boundary_qualification_is_retained(self):
        replay, stops = self.captured_replay()
        run = replay.run()
        self.assertFalse(matches_captured_states(self.repo, run["points"], stops))
        self.assertEqual(run["elapsed_t"], [37444, 30144, 6128, 105404])
        self.assertEqual(matching_div_phases(run["points"], stops, 678), [60])
        self.assertEqual([d['stop'] for d in captured_state_differences(self.repo,run['points'],stops)],
                         ['Producer Entry','Frame Wait'])
        for elapsed, leg in zip(run["elapsed_t"], observed_legs(stops)):
            self.assertLessEqual(leg["min_t"], elapsed)
            self.assertLessEqual(elapsed, leg["max_t"])

    def test_replay_observes_pc_before_pending_lcd_interrupt(self):
        replay, _ = self.captured_replay()
        point = replay.run()["points"][2]
        self.assertEqual((point["ly"], point["mode"], point["pending"]), (139, 3, []))

    def test_replay_counts_interior_cache_boundary_not_just_wrap(self):
        replay, _ = self.captured_replay()
        costs = replay.run()["irq_costs_t"]
        self.assertEqual(costs, {"vblank": [2780], "lcd": [108], "timer": [1452, 1472]})

    def test_stage_elapsed_is_cpu_work_plus_actual_interrupts(self):
        replay, _ = self.captured_replay()
        a, b = replay.run()["points"][1:3]
        irq_t = {k: b["irq_total_t"][k]-a["irq_total_t"][k] for k in a["irq_total_t"]}
        self.assertEqual(irq_t, {"vblank": 0, "lcd": 60*108, "timer": 3*1452})
        self.assertEqual(b["t"]-a["t"]-sum(irq_t.values()), 19180+128)

    def test_replay_does_not_seed_later_expected_states(self):
        replay, stops = self.captured_replay()
        original = replay.run()
        altered = deepcopy(stops)
        base = self.repo.symbols["wPokedexAnimOwner"][1]
        for value in altered[3]["capture"]["memory"]:
            if value[:2] == [0, base+1]:
                value[2] ^= 8
        replay, _ = self.captured_replay(altered)
        self.assertEqual(replay.run(), original)
        self.assertFalse(matches_captured_states(self.repo, original["points"], altered))

    def test_replay_interrupt_preserves_mainline_registers_and_stack(self):
        replay, _ = self.captured_replay()
        cpu = replay.cpu
        before = (list(cpu.r), cpu.f, cpu.pc, cpu.sp, cpu.bank)
        replay.clock.pending.add('lcd')
        replay.interrupt("lcd")
        self.assertEqual((cpu.r, cpu.f, cpu.pc, cpu.sp, cpu.bank), before)

    def test_replay_rejects_unmodeled_hdma_launch_instruction(self):
        replay, _ = self.captured_replay()
        with self.assertRaisesRegex(ModelError, "LDH write"):
            replay.cpu.write(0xff55, 0x80)

    def test_hdma_armed_after_dot_257_on_physical_line_153_waits_for_visible_line(self):
        replay, _ = self.captured_replay()
        replay.clock.t = 9*LINE+300
        replay.opcode = 0xe0
        replay.cpu.write(0xff55, 0x80)
        self.assertEqual(replay.clock.ly, 0)
        self.assertEqual(replay.clock.mode, 1)
        self.assertEqual(replay.clock.dma, [10*LINE+259])

    def test_hdma_overlap_rejected(self):
        replay, _ = self.captured_replay()
        replay.opcode = 0xe0
        replay.cpu.write(0xff55, 0x80)
        with self.assertRaisesRegex(ModelError, "Overlapping"):
            replay.cpu.write(0xff55, 0x80)

    def captured_luxray_replay(self):
        self.captured_replay()  # Enforce the same ROM-bound fixture guard.
        stops = read_stops(self.exact_luxray_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == "luxray")
        profile = Profile(hblank_dot=257, audio_phase_t=658, audio_played_at_publication=4)
        return OwnerReplay(self.repo, asset, stops, profile, 606, 16), stops

    def test_luxray_pending_timer_is_preserved_without_double_request(self):
        replay, _ = self.captured_luxray_replay()
        replay.clock.pending.add('timer')
        replay.points = [replay.snapshot('Publication')]
        self.assertEqual(replay.points[0]["pending"], ["timer"])
        self.assertEqual(replay.clock.next_timer, 658)
        result = replay.run()
        timer = result["interrupts"]["timer"]
        pending = int('timer' in result['points'][-1]['pending'])
        self.assertEqual(timer["delivered"], timer["requested"]+1-timer['coalesced']-pending)

    def test_luxray_continuous_state_and_timer_match(self):
        replay, stops = self.captured_luxray_replay()
        result = replay.run()
        self.assertTrue(matches_captured_states(self.repo, result["points"], stops))
        self.assertEqual(result["elapsed_t"], [36964, 25976, 5340, 1936652])
        self.assertEqual(matching_div_phases(result["points"], stops, 658), [16])
        self.assertEqual([a-b['nominal_t'] for a,b in zip(result['elapsed_t'],observed_legs(stops))],
                         [0,0,0,8])

    def test_luxray_initial_wait_precedes_vblank(self):
        replay, _ = self.captured_luxray_replay()
        point = replay.run()["points"][3]
        self.assertEqual(point['ly'], 141)
        self.assertLess(point["t"], FRAME)

    def test_luxray_upload_waits_for_next_frame_and_exact_tile_count(self):
        replay, _ = self.captured_luxray_replay()
        result = replay.run()
        self.assertEqual(len(result["hdma"]), 1)
        dma = result["hdma"][0]
        self.assertEqual(dma["tiles"], 17)
        self.assertEqual(len(dma["blocks_t"]), 17)
        self.assertTrue(all(LINE-24 <= b-a <= LINE+24 for a,b in zip(dma["blocks_t"], dma["blocks_t"][1:])))
        self.assertGreater(dma["launch_t"], 10*FRAME)
        self.assertEqual(dma["done_t"], dma["blocks_t"][-1]+36)
        self.assertEqual(replay.dma_remaining, 0)
        self.assertEqual(replay.clock.dma, [])
        asset = next(a for a in self.assets if a.name == "luxray")
        expected = b"".join(asset.dictionary[s*16:s*16+16] for s in asset.plans[1].sources)
        self.assertEqual(bytes(replay.cpu.vram[1][0x800:0x800+17*16]), expected)

    def test_luxray_pass_four_trace_matches_despite_eight_t_residual(self):
        replay, stops = self.captured_luxray_replay()
        point = replay.run()["points"][-1]
        memory = {(b,a):v for b,a,v in stops[-1]["capture"]["memory"]}
        base = self.repo.symbols["wPokedexAnimDebug"][1]
        diffs = [(i,value-memory[0,base+i]) for i,value in enumerate(point["trace"]) if value != memory[0,base+i]]
        self.assertEqual(diffs, [])

    def captured_partial_replay(self, name, stops=None, publication_t=606):
        self.captured_replay()  # Enforce the same ROM-bound fixture guard.
        if stops is None:
            stops = read_stops((ROOT/f"tools/dex_timing/fixtures/{name}_owner_followup.txt").read_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == name)
        phase, low = {"dusknoir": (10158, 180), "bastiodon": (322, 224)}[name]
        profile = Profile(hblank_dot=257, audio_phase_t=phase, audio_played_at_publication=4)
        return OwnerReplay(self.repo, asset, stops, profile, publication_t, low+publication_t-606), stops

    def test_frame_miss_alias_keeps_original_label(self):
        _, stops = self.captured_partial_replay("dusknoir")
        self.assertEqual(stops[-1]["label"], "First Miss")
        self.assertEqual(stops[-1]["source_label"], "Frame Miss")

    def test_partial_dictionary_seeds_only_verified_prefix(self):
        for name in ("dusknoir", "bastiodon"):
            with self.subTest(species=name):
                replay, _ = self.captured_partial_replay(name)
                asset = next(a for a in self.assets if a.name == name)
                self.assertEqual(replay.initial_dictionary_tiles, 145)
                self.assertEqual(bytes(replay.cpu.wram[6][:145*16]), asset.dictionary[:145*16])
                self.assertEqual(bytes(replay.cpu.wram[6][145*16:asset.total*16]), bytes((asset.total-145)*16))

    def test_partial_dictionary_rejects_incorrect_source_pointer(self):
        _, stops = self.captured_partial_replay("dusknoir")
        address = self.repo.symbols["wPokedexAnimDictionaryAddress"][1]
        for value in stops[0]["capture"]["memory"]:
            if value[:2] == [0, address]:
                value[2] ^= 1
        with self.assertRaisesRegex(ModelError, "pointers disagree"):
            self.captured_partial_replay("dusknoir", stops)

    def test_partial_dictionary_rejects_unfinished_stream_boundary(self):
        _, stops = self.captured_partial_replay("dusknoir")
        address = self.repo.symbols["wPokedexAnimDictionaryTilesRemaining"][1]
        for value in stops[0]["capture"]["memory"]:
            if value[:2] == [0, address]:
                value[2] += 1
        with self.assertRaisesRegex(ModelError, "stream boundary"):
            self.captured_partial_replay("dusknoir", stops)

    def test_dusknoir_matches_core_timers_and_entire_trace(self):
        replay, stops = self.captured_partial_replay("dusknoir")
        run = replay.run()
        self.assertTrue(matches_captured_states(self.repo, run["points"], stops))
        self.assertEqual(run["elapsed_t"], [37184, 43968, 3696, 423864])
        self.assertEqual(matching_div_phases(run["points"], stops, 10158), [180])
        self.assertFalse(any(d["bytes"] for d in captured_trace_differences(self.repo, run["points"], stops)))
        for elapsed, leg in zip(run["elapsed_t"], observed_legs(stops)):
            self.assertLessEqual(leg["min_t"], elapsed)
            self.assertLessEqual(elapsed, leg["max_t"])

    def test_partial_dictionary_cases_miss_without_new_decode_work(self):
        for name, remaining, stage in (("dusknoir", 102, 32), ("bastiodon", 68, 37)):
            with self.subTest(species=name):
                replay, _ = self.captured_partial_replay(name)
                run = replay.run()
                base = self.repo.symbols["wPokedexAnimOwner"][1]
                index = self.repo.symbols["wPokedexAnimDictionaryTilesRemaining"][1]-base
                self.assertEqual([p["anim"][index] for p in run["points"]], [remaining]*5)
                self.assertEqual([(d["tiles"], len(d["blocks_t"])) for d in run["hdma"]], [(20,20)])
                self.assertEqual((run["points"][-1]["anim"][9], run["points"][-1]["anim"][5]), (20,stage))

    def test_bastiodon_common_origin_matches_captured_state(self):
        replay, stops = self.captured_partial_replay("bastiodon")
        run = replay.run()
        self.assertEqual(run["elapsed_t"], [37464,47480,3788,279524])
        self.assertEqual(matching_div_phases(run["points"], stops, 322), [224])
        self.assertEqual(captured_state_differences(self.repo, run["points"], stops), [])

    def test_bastiodon_origin_sensitivity_is_not_an_operation_cost_change(self):
        replay, stops = self.captured_partial_replay("bastiodon", publication_t=608)
        run = replay.run()
        baseline, _ = self.captured_partial_replay('bastiodon')
        original = baseline.run()
        self.assertEqual(run['elapsed_t'][1:3], original['elapsed_t'][1:3])
        self.assertNotEqual(run['elapsed_t'], original['elapsed_t'])

    def test_followup_reports_closest_case_without_promoting_it_to_match(self):
        _, stops = self.captured_replay()
        asset = next(a for a in self.assets if a.name == "weavile")
        report = compare_linked_replay(self.repo, asset, stops,
                                      Profile(hblank_dot=257, audio_played_at_publication=4),
                                      606, [678], observed_legs(stops))
        self.assertEqual(report["status"], "RESIDUAL_MISMATCH")
        self.assertIsNone(report["example"])
        self.assertIsNotNone(report["closest"])
        self.assertTrue(report['state_differences'] or report['trace_differences'])

    def test_followup_uses_trace_to_constrain_already_compatible_initial_phases(self):
        _, stops = self.captured_partial_replay("dusknoir")
        asset = next(a for a in self.assets if a.name == "dusknoir")
        report = compare_linked_replay(self.repo, asset, stops,
                                      Profile(hblank_dot=257, audio_played_at_publication=4),
                                      606, [10158,10182], observed_legs(stops))
        self.assertEqual(report["status"], "CAPTURE_CONSISTENT")
        self.assertEqual(report["example"]["phase_t"], 10158)
        self.assertFalse(any(d["bytes"] for d in report["trace_differences"]))

    def captured_expansion_replay(self, name):
        self.captured_replay()  # Enforce the same ROM-bound fixture guard.
        stops = read_stops((ROOT/f"tools/dex_timing/fixtures/{name}_owner_followup.txt").read_text(), self.repo.symbols)
        asset = next(a for a in self.assets if a.name == name)
        phase, low = {"garchomp": (738, 192), "rampardos": (418, 0),
                      "rayquaza": (626, 48), "kyogre": (694, 44),
                      "metagross": (546, 128)}[name]
        profile = Profile(hblank_dot=257, audio_phase_t=phase, audio_played_at_publication=4)
        return OwnerReplay(self.repo, asset, stops, profile, 606, low), stops

    def test_rayquaza_and_kyogre_match_all_stops_timers_and_trace(self):
        for name, phase, low, elapsed in (
                ("rayquaza", 626, 48, [36952, 25012, 5348, 673604]),
                ("kyogre", 694, 44, [37404, 21008, 3672, 538828])):
            with self.subTest(species=name):
                replay, stops = self.captured_expansion_replay(name)
                run = replay.run()
                self.assertTrue(matches_captured_states(self.repo, run["points"], stops))
                self.assertEqual(run["elapsed_t"], elapsed)
                self.assertEqual(matching_div_phases(run["points"], stops, phase), [low, low+64])
                self.assertFalse(any(d["bytes"] for d in captured_trace_differences(self.repo, run["points"], stops)))
                for actual, leg in zip(elapsed, observed_legs(stops)):
                    self.assertLessEqual(leg["min_t"], actual)
                    self.assertLessEqual(actual, leg["max_t"])

    def test_five_new_cases_miss_with_dictionary_ready_and_nonempty_audio(self):
        for name, decoded, remaining, event, uploaded, stage, cache in (
                ("garchomp", 140, 0, 2, 20, 29, 31),
                ("rampardos", 145, 10, 2, 20, 38, 28),
                ("rayquaza", 115, 0, 3, 0, 20, 42),
                ("kyogre", 124, 0, 3, 0, 10, 45),
                ("metagross", 97, 0, 11, 0, 17, 133)):
            with self.subTest(species=name):
                replay, _ = self.captured_expansion_replay(name)
                run = replay.run()
                index = (self.repo.symbols["wPokedexAnimDictionaryTilesRemaining"][1]
                         - self.repo.symbols["wPokedexAnimOwner"][1])
                self.assertEqual(replay.initial_dictionary_tiles, decoded)
                self.assertEqual([p["anim"][index] for p in run["points"]], [remaining]*5)
                miss = run["points"][-1]
                self.assertEqual((miss["trace"][5], miss["anim"][9], miss["anim"][5], miss["cache"]),
                                 (event, uploaded, stage, cache))

    def test_kyogre_legal_upload_still_queues_after_publication_deadline(self):
        replay, _ = self.captured_expansion_replay("kyogre")
        run = replay.run()
        helper = next(p for p in run["observations"] if p["kind"] == "HDMATransfer_Exact_NoDI_Arbitrary")
        queued = next(p for p in run["observations"] if p["kind"] == "Pokedex_RecordAnimationTrace" and p["trace"][25] == 0x81)
        published = [p for p in run["observations"] if p["kind"].endswith(".deadline_reached")]
        self.assertEqual((helper["t"]//FRAME, helper["ly"]), (5, 103))
        self.assertLess(helper["ly"], 128-10)
        self.assertEqual(run["hdma"][0]["tiles"], 10)
        self.assertLess(run["hdma"][0]["done_t"], 6*FRAME)
        self.assertGreater(queued["t"], 6*FRAME)
        self.assertEqual((queued["t"]//FRAME, queued["ly"]), (6, 10))
        self.assertEqual([(p["trace"][5], p["t"]//FRAME) for p in published], [(1, 0), (2, 7)])

    def test_garchomp_common_origin_closes_frame_wait_boundary_residual(self):
        replay, stops = self.captured_expansion_replay("garchomp")
        run = replay.run()
        self.assertEqual(run["elapsed_t"], [37464, 43524, 3680, 283604])
        self.assertEqual(matching_div_phases(run["points"], stops, 738), [192])
        self.assertEqual(captured_state_differences(self.repo, run["points"], stops), [])

    def test_rampardos_common_origin_closes_mode_and_timer_residuals(self):
        replay, stops = self.captured_expansion_replay("rampardos")
        run = replay.run()
        self.assertEqual(run["elapsed_t"], [37464, 48600, 5132, 208416])
        self.assertEqual(matching_div_phases(run["points"], stops, 418), [0,64,128])
        self.assertEqual(captured_state_differences(self.repo, run["points"], stops), [])

    def test_metagross_common_origin_closes_early_timing_residual(self):
        replay, stops = self.captured_expansion_replay("metagross")
        run = replay.run()
        self.assertEqual(run["elapsed_t"], [36964, 15824, 3672, 3002296])
        self.assertEqual(matching_div_phases(run["points"], stops, 546), [128])
        self.assertEqual(captured_state_differences(self.repo, run["points"], stops), [])
        self.assertEqual(captured_trace_differences(self.repo, run["points"], stops)[-1]["bytes"], [])
        self.assertEqual([d["tiles"] for d in run["hdma"]], [3, 3, 17])

    def test_followup_retains_diagnostic_when_no_joint_timer_candidate_exists(self):
        _, stops = self.captured_expansion_replay("metagross")
        asset = next(a for a in self.assets if a.name == "metagross")
        report = compare_linked_replay(self.repo, asset, stops,
                                      Profile(hblank_dot=257, audio_played_at_publication=4),
                                      600, [532], observed_legs(stops))
        self.assertEqual(report["status"], "RESIDUAL_MISMATCH")
        self.assertIsNone(report["example"])
        self.assertIsNone(report["closest"])
        self.assertIsNotNone(report["diagnostic"])
        self.assertFalse(report["diagnostic"]["timer_match"])
        self.assertFalse(report["diagnostic"]["intervals_match"])
        self.assertEqual(report["state_differences"][0]["stop"], "Stage Entry")

    def test_hdma_setup_contract(self):
        verify_hdma_contract(self.repo)

    def test_interrupt_costs_include_vector_and_hardware_entry(self):
        costs = audio_benchmark(self.repo)
        self.assertEqual(costs["lcd_irq_t"], 108)
        self.assertEqual(costs["timer_irq_t"], [1452, 1480])
        self.assertEqual(costs["service_prefix_t"], 292)
        self.assertEqual(costs["service_suffix_t"], 176)

    def test_linked_vblank_baseline_includes_oam_without_double_charge(self):
        costs = publication_benchmark(self.repo)
        self.assertEqual(costs["vblank"], {"idle_t": 2764, "pending_early_t": 3304,
                                          "publish_t": 4212, "publish_check_t": 516})
        self.assertEqual(costs["gdma_t"], 896)

    def test_caller_and_schedule_reload_costs_are_not_free(self):
        asset = next(a for a in self.assets if a.name == "weavile")
        costs = benchmark(self.repo, asset)
        self.assertEqual(costs["owner_shell_t"]["turnover_prefix_t"], 296)
        self.assertEqual(costs["owner_shell_t"]["waiting_commit_t"], 508)
        self.assertGreater(costs["schedule_action_extra_t"][0], 0)
        self.assertEqual(costs["schedule_action_extra_t"][1], 0)

    def test_footer_path_retains_four_polls_and_original_ready_costs(self):
        variants = owner_prefix_benchmark(self.repo)
        self.assertEqual(len(variants), 8)
        for v in variants:
            self.assertEqual(v["steps"].count("stat"), 4)
            self.assertEqual(path_cost(v["steps"]), v["ready_t"])
        self.assertEqual(max(v["ready_t"] for v in variants), 2524)

    def test_delay_paths_and_arming_are_counted_from_linked_rom(self):
        shell = owner_shell_benchmark(self.repo)
        self.assertEqual(sum(shell["delay"]["after_vblank"]), 56)
        self.assertEqual(sum(shell["delay"]["after_other_irq"]), 36)
        self.assertEqual(sum(shell["delay"]["after_service"]), 28)
        for name in ("waiting_after_deadline", "pending_commit", "queue_suffix"):
            self.assertEqual(shell["steps"][name].count("arm"), 1)
        self.assertEqual(shell["deadline_prefix_t"] +
                         sum(shell["deadline_steps"]["future"]) +
                         shell["waiting_after_deadline_t"], shell["waiting_commit_t"])
        self.assertGreater(shell["underflow_after_deadline_t"], 1000)

    def test_linked_byte_mismatch_rejected(self):
        repo = Repository(ROOT, ROOT/"pokecrystal.gbc", ROOT/"pokecrystal.sym")
        data = bytearray(repo.rom)
        data[offset(repo.symbols["WeavileDexAnimationPlan"])] ^= 1
        repo.rom = bytes(data)
        with self.assertRaisesRegex(ModelError, "ROM/asset mismatch"):
            repo.load(["weavile"])

    def test_frame_construction_and_impossible_schedule(self):
        a = next(a for a in self.assets if a.name == "weavile")
        costs = benchmark(self.repo, a)
        audio, pub = audio_benchmark(self.repo), publication_benchmark(self.repo)
        impossible = replace(a, actions=[0]*4096, action_loop=None)
        costs = dict(costs, schedule_action_extra_t=[0]*4096)
        result = simulate(impossible, costs, audio, pub, Profile(), audio_enabled=False)
        self.assertIsNotNone(result["animation_miss"])
        self.assertEqual(result["status"], "MODEL_MISS")
        self.assertEqual(result["startup_actual_loaded_tiles"], a.total)

    def test_no_miss_never_certifies(self):
        a = next(a for a in self.assets if a.name == "chikorita")
        costs = benchmark(self.repo, a)
        audio, pub = audio_benchmark(self.repo), publication_benchmark(self.repo)
        result = simulate(a, costs, audio, pub, Profile(), audio_enabled=False)
        self.assertNotEqual(result["status"], "PASS")
        self.assertTrue(result["unknown_costs"])

    def test_late_ready_map_is_not_a_producer_underrun(self):
        asset = next(a for a in self.assets if a.name == "chikorita")
        costs = benchmark(self.repo, asset)
        # Two base-map events need no production, but deliberately enter late.
        synthetic = replace(asset, events=[Event(0, 1, asset.width**2)]*2,
                            event_loop=None, actions=[0]*16, action_loop=None)
        costs = dict(costs, schedule_action_extra_t=[0]*16)
        result = simulate(synthetic, costs, audio_benchmark(self.repo),
                          publication_benchmark(self.repo), Profile(),
                          initial_ly=143, audio_enabled=False)
        self.assertIsNone(result["animation_miss"])
        self.assertTrue(any(p.get("late_intervals", 0) for p in result["publishes"]))
        self.assertEqual(result["status"], "MODEL_MISS")

    def test_warm_does_not_assume_whole_dictionary(self):
        a = next(a for a in self.assets if a.name == "dusknoir")
        costs = benchmark(self.repo, a)
        audio, pub = audio_benchmark(self.repo), publication_benchmark(self.repo)
        result = simulate(a, costs, audio, pub, Profile(), path="warm", audio_enabled=False)
        self.assertEqual(result["startup_actual_loaded_tiles"], 145)
        self.assertLess(result["startup_actual_loaded_tiles"], a.total)

    def test_weavile_owner_wait_loses_one_producer_opportunity(self):
        asset = next(a for a in self.assets if a.name == "weavile")
        profile = Profile(hblank_dot=257, audio_phase_t=696, audio_played_at_publication=4)
        result = simulate(asset, benchmark(self.repo, asset), audio_benchmark(self.repo),
                          publication_benchmark(self.repo), profile)
        miss = result["animation_miss"]
        self.assertEqual((miss["event"], miss["frame"], miss["uploaded"], miss["action_index"]), (1, 2, 0, 2))
        first, second = result["recent_calls"]
        self.assertEqual(first["producer_begin_t"]//FRAME, 0)
        self.assertEqual(first["frame_wait_t"]//FRAME, 1)
        self.assertEqual(second["producer_begin_t"]//FRAME, 2)

    def test_luxray_first_miss_with_normal_selected_display(self):
        asset = next(a for a in self.assets if a.name == "luxray")
        result = simulate(asset, benchmark(self.repo, asset), audio_benchmark(self.repo),
                          publication_benchmark(self.repo), Profile(hblank_dot=257))
        miss = result["animation_miss"]
        self.assertEqual((miss["event"], miss["frame"], miss["uploaded"], miss["required_uploads"]), (6, 2, 0, 21))
        self.assertEqual(miss["deadline_t"]//FRAME, 29)


if __name__ == "__main__":
    unittest.main()
