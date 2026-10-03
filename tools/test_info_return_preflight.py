"""Negative controls for the private Info-return relocation acceptance checks."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from dex_timing.info_return_preflight import transform
from dex_timing.info_return_regression import preservation_audit


class RelocationOracleTests(unittest.TestCase):
    def run_audit(self, *, tile_error=False, palette_error=False,
                  retained_reference=False, changed_frame=False, permanent_error=False):
        before = bytearray(0x4000)
        cell = 0x1800 + 10 * 32 + 1
        before[cell], before[cell + 0x2000] = 3, 8
        before[0x3030:0x3040] = bytes(range(16))
        after = bytearray(before)
        after[cell] = 3 if retained_reference else 0xfa
        after[0x2fa0:0x2fb0] = before[0x3030:0x3040]
        if tile_error:
            after[0x2fa0] ^= 1
        if permanent_error:
            after[0x1800 + 9 * 32 + 1] = 0x32
        base = dict(event='phase', state=5, scroll=[5, 0, 167, 0],
                    bg_pal='00', obj_pal='00', oam='00')
        rows = [dict(base, phase='leave', t=0, vram=before.hex()),
                dict(base, phase='info_return_relocate', t=4, vram=before.hex()),
                dict(base, phase='info_return_published', t=12, vram=after.hex(),
                     bg_pal='01' if palette_error else '00')]
        rows += [dict(event='frame', state=5, scroll=[5, 0, 167, 0]) for _ in range(2)]
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'trace.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
            image = Image.new('RGB', (160, 144))
            image.save(output / 'trace-001.ppm')
            if changed_frame:
                image.putpixel((10, 80), (255, 255, 255))
            image.save(output / 'trace-002.ppm')
            return preservation_audit(output)

    def test_identical_relocated_pixels_pass(self):
        result = self.run_audit()
        self.assertEqual(result['translation_issues'], [])
        self.assertEqual(result['changed_outgoing_frames'], [])
        self.assertEqual(result['exposed_tile_replacements'], 0)
        self.assertEqual(result['borrowed_cells'], 1)
        self.assertEqual(result['relocation_cycles'], 8)

    def test_wrong_tile_payload_fails(self):
        self.assertIn('tile_10_1', self.run_audit(tile_error=True)['translation_issues'])

    def test_palette_change_fails(self):
        self.assertIn('bg_pal', self.run_audit(palette_error=True)['translation_issues'])

    def test_retained_borrowed_reference_fails(self):
        self.assertIn('borrowed_references_survived',
                      self.run_audit(retained_reference=True)['translation_issues'])

    def test_changed_permanent_cell_fails(self):
        self.assertIn('permanent_cell_9_1',
                      self.run_audit(permanent_error=True)['translation_issues'])

    def test_changed_outgoing_display_fails(self):
        self.assertEqual(self.run_audit(changed_frame=True)['changed_outgoing_frames'], [2])


class PrivateTransformTests(unittest.TestCase):
    def test_missing_or_ambiguous_anchor_fails_without_writing(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'probe.asm'
            for original in ('other\n', 'anchor\nanchor\n'):
                path.write_text(original)
                with self.assertRaisesRegex(ValueError, 'anchor changed'):
                    transform(path, 'anchor\n', 'replacement\n')
                self.assertEqual(path.read_text(), original)

    def test_exact_anchor_preserves_surrounding_source(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'probe.asm'
            path.write_text('before\nanchor\nafter\n')
            transform(path, 'anchor\n', 'replacement\n')
            self.assertEqual(path.read_text(), 'before\nreplacement\nafter\n')


if __name__ == '__main__':
    unittest.main()
