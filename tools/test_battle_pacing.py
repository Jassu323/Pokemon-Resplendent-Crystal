"""Private phase-pacing invariants; native replays validate hardware timing."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_battle_pacing_prototype import patch, record, CHARGES


def simulate(extra, denominator, updates, limit=0, clock=0, natural=None):
    deadline, error, holds, late = clock, 0, 0, 0
    remaining = limit
    active = extra
    gaps = []
    for i in range(updates):
        elapsed = (natural or {}).get(i, 1)
        before = clock
        if active:
            error += active
            gap = 1
            if error >= denominator:
                error -= denominator
                gap += 1
            deadline = (deadline + gap) & 255
        clock = (clock + elapsed) & 255
        if active:
            distance = (deadline - clock) & 255
            if distance & 128:
                late += 1
            else:
                holds += distance
                clock = deadline
            if remaining:
                remaining -= 1
                if not remaining:
                    active = 0
        gaps.append((clock - before) & 255)
    return dict(holds=holds, late=late, gaps=gaps, error=error)


class PacingTests(unittest.TestCase):
    def test_surf_fraction_distributes_holds(self):
        r = simulate(2, 3, 190)
        self.assertEqual(r['holds'], 126)
        self.assertEqual(r['gaps'][:6], [1, 2, 2, 1, 2, 2])

    def test_byte_clock_wrap(self):
        self.assertEqual(simulate(2, 3, 512, clock=254), simulate(2, 3, 512))

    def test_charge_limit_leaves_stationary_tail_unchanged(self):
        r = simulate(34, 81, 144, limit=81)
        self.assertEqual(r['holds'], 34)
        self.assertEqual(r['gaps'][81:], [1] * 63)

    def test_dragon_limit(self):
        r = simulate(10, 81, 141, limit=81)
        self.assertEqual(r['holds'], 10)
        self.assertEqual(r['gaps'][81:], [1] * 60)

    def test_elapsed_work_uses_existing_budget(self):
        r = simulate(1, 1, 40, natural={i: 2 for i in range(40)})
        self.assertEqual(r['holds'], 0)
        self.assertEqual(r['late'], 0)

    def test_late_work_does_not_drop_updates(self):
        r = simulate(1, 3, 60, natural={2: 4})
        self.assertEqual(len(r['gaps']), 60)
        self.assertGreater(r['late'], 0)
        self.assertLess(r['holds'], 20)

    def test_disabled_path(self):
        self.assertEqual(simulate(0, 1, 30)['gaps'], [1] * 30)

    def test_accumulator_fits_byte(self):
        for extra in range(128):
            r = simulate(extra, 127, 600)
            self.assertLess(r['error'], 127)
            self.assertTrue(set(r['gaps']) <= {1, 2})

    def test_invalid_record_rejected(self):
        for args in ((1, 2, 1), (1, 128, 128), (1, 1, 1, 256)):
            with self.assertRaises(AssertionError):
                record(*args)

    def test_private_patch_scope(self):
        files = ('home/vblank.asm', 'ram/wram.asm', 'engine/battle_anims/anim_commands.asm',
                 'macros/scripts/battle_anims.asm', 'data/moves/animations.asm')
        original = {f: (ROOT / f).read_bytes() for f in files}
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            for f in files:
                target = checkout / f
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / f, target)
            phases = patch(checkout)
            self.assertEqual({p['move'] for p in phases},
                             {'Surf', 'WaterPulse', 'DragonDance', 'Thunderbolt', 'Caustic', *CHARGES})
            self.assertEqual(len(phases), 18)
            self.assertNotIn('anim_0xea ', (checkout / 'data/moves/animations.asm').read_text())
            self.assertEqual(sum(p['phase'] == 8 for p in phases), 8)
        self.assertEqual(original, {f: (ROOT / f).read_bytes() for f in files})


if __name__ == '__main__':
    unittest.main()
