"""Linked shutdown contracts; the hardware-edge replay lives in build/."""
import unittest
from pathlib import Path

from dex_timing.assets import Repository, offset
from dex_timing.costs import machine


class SampledCryShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')

    def shutdown(self, label, pending, tac=0):
        cpu = machine(self.repo)
        cpu.allowed_io.update((0xff05, 0xff06, 0xff07, 0xff0f, *range(0xff10, 0xff27)))
        cpu.field('hSampledCryTimer', 1)
        cpu.field('hSampledCryBlocks', 557, 2)
        saved = {'TIMA': 73, 'TMA': 91, 'TAC': tac, 'IE': 15,
                 'AUD3ENA': 128, 'AUD3LEN': 31, 'AUD3LEVEL': 32,
                 'AUD3LOW': 87, 'AUD3HIGH': 3, 'AUDTERM': 85, 'AUDVOL': 119}
        for name, value in saved.items():
            cpu.field('hSampledCrySaved' + name, value)
        cpu.ram[0xff0f] = pending
        cpu.record_writes = True
        cycles = cpu.run(label)
        return cpu, cycles, saved

    def test_timer_shutdown_never_touches_interrupt_requests(self):
        for pending in range(32):
            with self.subTest(pending=pending):
                cpu, _, _ = self.shutdown('StopSampledCryAsync_FromTimer', pending)
                self.assertEqual(cpu.ram[0xff0f], pending)
                self.assertFalse(any(at == 0xff0f for _, at, _ in cpu.writes + cpu.io_reads))

    def test_manual_cancellation_still_clears_only_timer_flag(self):
        for pending in range(32):
            cpu, _, _ = self.shutdown('StopSampledCryAsync_NoInterruptControl', pending)
            self.assertEqual(cpu.ram[0xff0f], pending & ~4)

    def test_both_paths_restore_identical_audio_timer_state(self):
        registers = {'TIMA': 0xff05, 'TMA': 0xff06, 'TAC': 0xff07, 'IE': 0xffff,
                     'AUD3ENA': 0xff1a, 'AUD3LEN': 0xff1b, 'AUD3LEVEL': 0xff1c,
                     'AUD3LOW': 0xff1d, 'AUD3HIGH': 0xff1e,
                     'AUDTERM': 0xff25, 'AUDVOL': 0xff24}
        for tac in (0, 4, 5, 6, 7):
            results = []
            for label in ('StopSampledCryAsync_FromTimer', 'StopSampledCryAsync_NoInterruptControl'):
                cpu, cycles, saved = self.shutdown(label, 3, tac)
                for name, address in registers.items():
                    self.assertEqual(cpu.ram[address], saved[name])
                for name in ('hSampledCryTimer', 'hSampledCryBlocks'):
                    self.assertEqual(cpu.data(self.repo.symbols[name][1], 1 if name.endswith('Timer') else 2),
                                     bytes(1 if name.endswith('Timer') else 2))
                results.append((cpu.r, cpu.f, cpu.sp, cycles))
            self.assertEqual(results[0][:3], results[1][:3])
            self.assertEqual(results[1][3] - results[0][3], 56)

    def test_both_irq_stop_branches_use_acknowledged_path(self):
        symbols = self.repo.symbols
        timer = symbols['StopSampledCryAsync_FromTimer'][1]
        manual = symbols['StopSampledCryAsync_NoInterruptControl'][1]
        code = self.repo.rom[offset(symbols['SampledCry_AsyncTimerTick']):
                             offset(symbols['SampledCry_CopyNextCachedBlock'])]
        self.assertEqual(code.count(bytes((0xc3, timer & 255, timer >> 8))), 2)
        self.assertNotIn(bytes((0xc3, manual & 255, manual >> 8)), code)


if __name__ == '__main__':
    unittest.main()
