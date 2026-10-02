"""Negative controls for the host-only cry handoff investigation."""
import unittest
import struct
from pathlib import Path

from dex_timing.assets import Repository, offset
from dex_timing.costs import machine
from dex_timing.cry_ownership import (
    cancellation_issues, cancellation_pairs, cases, check_incoming_header, sparse_fixture,
    state_without_wall_clock, summarize, validate_output,
)


class CryOwnershipTests(unittest.TestCase):
    def event(self, phase, t=10, audio=1, remaining=100, **fields):
        return dict(phase=phase, t=t, audio=audio, remaining=remaining, selected=315,
                    cur_channel=4, sfx_flags=[33, 33, 0, 33], **fields)

    def test_outgoing_and_incoming_empty_are_separate(self):
        trace = [self.event('sample_empty', 5), self.event('sample_empty', 15),
                 self.event('sample_arm', 20), self.event('sample_empty', 25)]
        summary = summarize(trace, 10, 315)
        self.assertEqual([r['t'] for r in summary['outgoing_cache_empty']], [15])
        self.assertEqual(summary['sample_empty_count'], 2)

    def test_natural_stop_is_not_exhaustion(self):
        summary = summarize([self.event('sample_stop', remaining=0)], 0, 315)
        self.assertEqual(summary['outgoing_cache_empty'], [])
        self.assertEqual(summary['sampled_stops'][0]['remaining'], 0)

    def test_resumed_synth_is_detected_after_natural_sample_completion(self):
        trace = [self.event('sample_arm', 10), self.event('sample_stop', 20, remaining=0),
                 self.event('synth_note', 25, audio=0)]
        self.assertEqual(len(summarize(trace, 5, 315)['synthesized_notes_after_incoming_sample']), 1)

    def test_music_notes_and_notes_before_sample_are_not_resumption(self):
        trace = [self.event('synth_note', 5, audio=0), self.event('sample_arm', 10),
                 dict(self.event('synth_note', 20, audio=0), cur_channel=0)]
        self.assertEqual(summarize(trace, 0, 315)['synthesized_notes_after_incoming_sample'], [])

    def test_correct_header_and_block_count_are_independently_required(self):
        trace = [self.event('sample_start', sample_bank=143, de=0x53a0),
                 self.event('sample_arm', remaining=508)]
        self.assertEqual(check_incoming_header(trace, 0, (143, 0x53a0), 508)['issues'], [])
        trace[0]['de'] += 16
        self.assertEqual(check_incoming_header(trace, 0, (143, 0x53a0), 508)['issues'], ['incoming_header'])
        trace[1]['remaining'] = 53662
        self.assertEqual(check_incoming_header(trace, 0, (143, 0x53a0), 508)['issues'],
                         ['incoming_header', 'incoming_block_count'])

    def test_missing_incoming_sample_cannot_pass(self):
        self.assertEqual(check_incoming_header([], 0, (143, 0x53a0), 508)['issues'],
                         ['incoming_header', 'incoming_block_count'])

    def test_outgoing_sample_events_cannot_supply_incoming_header(self):
        trace = [self.event('sample_start', t=5, sample_bank=143, de=0x53a0),
                 self.event('sample_arm', t=6, remaining=508)]
        self.assertEqual(check_incoming_header(trace, 10, (143, 0x53a0), 508)['issues'],
                         ['incoming_header', 'incoming_block_count'])

    def test_synth_destination_must_not_arm_a_sample(self):
        self.assertEqual(check_incoming_header([], 0, None, 0)['issues'], [])
        self.assertEqual(check_incoming_header([self.event('sample_arm')], 0, None, 0)['issues'],
                         ['unexpected_sample'])

    def test_matrix_includes_early_and_settled_controls(self):
        matrix = cases([0, 4, 16, 40])
        self.assertEqual(len(matrix), 40)
        self.assertEqual(sum(c['delay'] is None for c in matrix), 8)
        self.assertEqual(sum(c['action'] == 'page' for c in matrix), 25)
        self.assertEqual(sum(c['action'] == 'leave' for c in matrix), 15)

    def test_prototype_acceptance_rejects_every_ownership_symptom(self):
        self.assertEqual(cancellation_issues({}), [])
        self.assertEqual(cancellation_issues(dict(
            summary=dict(sample_empty_count=1, synthesized_notes_after_incoming_sample=[{}]),
            animation_misses=1)), ['sample_empty', 'resumed_synth', 'animation_miss'])

    def test_diagnostic_output_cannot_replace_inputs_or_main_build(self):
        root = Path('/private/tmp/cry-owner-tests')
        inputs = [root / 'build/accepted/input-copy.gbc', root / 'build/accepted']
        self.assertEqual(validate_output(root / 'build/diagnostic', inputs, root),
                         root / 'build/diagnostic')
        for invalid in (root, root / 'build', root / 'build/accepted', root / 'outside'):
            with self.assertRaises(ValueError):
                validate_output(invalid, inputs, root)

    def test_fixture_cannot_overwrite_source_battery(self):
        source = Path('/private/tmp/cry-owner-tests/battery.sav')
        with self.assertRaisesRegex(ValueError, 'must not replace'):
            sparse_fixture(None, source, source)

    def state(self):
        payload = bytearray(b'EMAS' + bytes(4))
        for name in ('core', 'dma', 'mbc', 'hram', 'timing', 'apu', 'rtc', 'video', 'accessory'):
            data = bytes(32 if name == 'rtc' else 8)
            payload += struct.pack('<I', len(data)) + data
        bess = len(payload)
        payload += b'RTC ' + struct.pack('<I', 48) + bytes(48)
        payload += b'END ' + bytes(4)
        payload += struct.pack('<I', bess) + b'BESS'
        return payload

    def test_only_wall_clock_bytes_are_normalized(self):
        original = self.state()
        changed = bytearray(original)
        rtc = 8 + 6 * 12 + 4
        changed[rtc] = changed[rtc + 16] = 1
        bess = struct.unpack_from('<I', changed, len(changed) - 8)[0]
        changed[bess + 8] = 1
        self.assertEqual(state_without_wall_clock(original), state_without_wall_clock(changed))
        for position in (12, rtc + 24):
            control = bytearray(changed)
            control[position] ^= 1
            self.assertNotEqual(state_without_wall_clock(original), state_without_wall_clock(control))

    def test_state_comparison_rejects_unknown_layout(self):
        with self.assertRaisesRegex(ValueError, 'Expected little-endian'):
            state_without_wall_clock(bytes(100))

    def test_cancellation_pairs_require_a_matching_return(self):
        entry, returned = self.event('cancel_entry'), self.event('cancel_return')
        self.assertEqual(cancellation_pairs([entry, returned]), [(entry, returned)])
        for trace in ([entry], [returned]):
            with self.assertRaises(ValueError):
                cancellation_pairs(trace)


class LinkedCryCancellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        if not (root / 'pokecrystal.gbc').exists():
            raise unittest.SkipTest('Build the current ROM for cancellation contracts')
        cls.repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
        if 'PokedexSelectedMon_CancelCry' not in cls.repo.symbols:
            raise unittest.SkipTest('This ROM predates the Dex-local cry cancellation helper')

    def cpu(self, flags=(0, 0, 0, 0)):
        cpu = machine(self.repo)
        cpu.allowed_io.update((*range(0xff05, 0xff08), 0xff0f, *range(0xff10, 0xff27)))
        cpu.r = [0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0, 0xde]
        cpu.f = 0xb0
        for channel, value in enumerate(flags, 5):
            cpu.field(f'wChannel{channel}Flags1', value)
        for name, value in (('wVolume', 0x22), ('wLastVolume', 0x77),
                            ('wSFXPriority', 1), ('wPitchSweep', 7)):
            cpu.field(name, value)
        cpu.field('wChannel6PitchOffset', 0x1234, 2)
        cpu.field('wChannel8PitchOffset', 0x5678, 2)
        return cpu

    def run_preserving_registers(self, cpu):
        registers, flags, sp = list(cpu.r), cpu.f, cpu.sp
        cycles = cpu.run('PokedexSelectedMon_CancelCry')
        self.assertEqual(cpu.r, registers)
        self.assertEqual(cpu.f, flags)
        self.assertEqual(cpu.sp, sp)
        return cycles

    def value(self, cpu, name, size=1):
        return int.from_bytes(cpu.data(self.repo.symbols[name][1], size), 'little')

    def test_only_three_accepted_owner_boundaries_call_the_helper(self):
        symbols = self.repo.symbols
        at = symbols['PokedexSelectedMon_CancelCry'][1]
        call = bytes((0xcd, at & 255, at >> 8))
        for start, end in (('ChangeSpecies', 'Leave'), ('Leave', 'Area'), ('Area', 'StageDescription')):
            code = self.repo.rom[offset(symbols['PokedexSelectedMon_' + start]):
                                 offset(symbols['PokedexSelectedMon_' + end])]
            text_cancel = symbols.get('PokedexSelectedMon_CancelDescriptionText')
            prefix = bytes((0xcd, text_cancel[1] & 255, text_cancel[1] >> 8)) if text_cancel else b''
            self.assertTrue(code.startswith(prefix))
            self.assertEqual(code[len(prefix) + 5:len(prefix) + 8], call)
            self.assertEqual(code.count(call), 1)
        code = self.repo.rom[offset(symbols['PokedexSelectedMon_ToggleDescriptionPage']):
                             offset(symbols['PokedexSelectedMon_ChangeSpecies'])]
        self.assertNotIn(call, code)
        self.assertEqual(symbols['PokedexSelectedMon_CancelCry.end'][1] - at, 118)

    def test_inactive_and_noncry_channels_are_untouched(self):
        cpu = self.cpu((0, 1, 0x20, 0x40))
        before = bytes(cpu.ram[0xc100:0xc400]), bytes(cpu.ram[0xff00:0xff80])
        self.assertEqual(self.run_preserving_registers(cpu), 368)
        self.assertEqual(before, (bytes(cpu.ram[0xc100:0xc400]), bytes(cpu.ram[0xff00:0xff80])))

    def test_active_cries_do_not_clear_unrelated_sfx_or_music(self):
        for mask in range(1, 16):
            with self.subTest(mask=mask):
                flags = tuple(0x21 if mask & (1 << i) else 1 for i in range(4))
                cpu = self.cpu(flags)
                music = bytes(cpu.ram[0xc100:self.repo.symbols['wChannel5'][1]])
                self.run_preserving_registers(cpu)
                self.assertEqual([self.value(cpu, f'wChannel{i}Flags1') for i in range(5, 9)],
                                 [0 if f == 0x21 else f for f in flags])
                self.assertEqual(bytes(cpu.ram[0xc100:self.repo.symbols['wChannel5'][1]]), music)
                self.assertEqual(self.value(cpu, 'wVolume'), 0x77)
                for name in ('wLastVolume', 'wSFXPriority'):
                    self.assertEqual(self.value(cpu, name), 0)
                for name in ('wChannel6PitchOffset', 'wChannel8PitchOffset'):
                    self.assertEqual(self.value(cpu, name, 2), 0)

    def test_zero_saved_volume_is_not_written_to_current_volume(self):
        cpu = self.cpu((0x21, 0, 0, 0))
        cpu.field('wLastVolume', 0)
        self.run_preserving_registers(cpu)
        self.assertEqual(self.value(cpu, 'wVolume'), 0x22)

    def test_sample_stop_precedes_synth_hardware_mute(self):
        cpu = self.cpu((0, 0, 0x21, 0))
        cpu.field('hSampledCryTimer', 1)
        cpu.field('hSampledCryBlocks', 123, 2)
        cpu.field('hSampledCrySavedIE', 0x0b)
        cpu.field('hSampledCrySavedTAC', 4)
        cpu.field('hSampledCrySavedTIMA', 17)
        cpu.field('hSampledCrySavedTMA', 23)
        cpu.field('hSampledCrySavedAUD3ENA', 0x80)
        cpu.field('hSampledCrySavedAUDVOL', 0x77)
        cpu.record_writes = True
        self.run_preserving_registers(cpu)
        self.assertEqual(self.value(cpu, 'hSampledCryTimer'), 0)
        self.assertEqual(self.value(cpu, 'hSampledCryBlocks', 2), 0)
        self.assertEqual(cpu.ram[0xff1a], 0)
        self.assertEqual([v for _, a, v in cpu.writes if a == 0xff1a], [0, 0x80, 0])
        self.assertEqual([cpu.ram[a] for a in (0xffff, 0xff07, 0xff05, 0xff06)], [0x0b, 4, 17, 23])

    def test_inactive_sample_does_not_restore_stale_saved_hardware(self):
        cpu = self.cpu()
        cpu.field('hSampledCrySavedIE', 0xff)
        cpu.field('hSampledCrySavedAUD3ENA', 0x80)
        cpu.ram[0xffff], cpu.ram[0xff1a] = 0x0b, 0
        self.run_preserving_registers(cpu)
        self.assertEqual((cpu.ram[0xffff], cpu.ram[0xff1a]), (0x0b, 0))


if __name__ == '__main__':
    unittest.main()
