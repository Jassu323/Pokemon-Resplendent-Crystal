"""Read-only checks for the historical Dex-bug observer's assertions."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from dex_timing.backlog_revalidation import marker_issues, window_pixels


class HistoricalDexObservationTests(unittest.TestCase):
    def fixture(self):
        palette = b'\xff\x7f\x1f\x00\xe0\x03\x00\x00'
        rom = bytes(0x200) + palette + bytes(range(16))
        repo = SimpleNamespace(rom=rom, symbols=dict(
            PokedexListCaughtBallPalette=(0, 0x200), PokedexCaughtBallGFX=(0, 0x208)))
        vram = bytearray(0x4000)
        vram[0x410:0x420] = bytes(range(16))
        oam = bytearray(160)
        for i in range(9):
            oam[(12 + i) * 4:(13 + i) * 4] = bytes((60 + 32 * (i // 3), 72 + 32 * (i % 3), 0x41, 1))
        oam[84:100] = b''.join(bytes((50 + dy, 74 + dx, 0x40, attr)) for dy, dx, attr in (
            (0, 0, 0), (0, 20, 32), (20, 0, 64), (20, 20, 96)))
        snapshot = dict(vram=vram.hex(), lcd=0xe3, bg_pal=(palette * 8).hex(),
            obj_pal=(palette * 8).hex(), target_obj=(palette * 8).hex(),
            oam=oam.hex(), grid_flags='03' * 9, cursor=0)
        return repo, snapshot

    def test_correct_hardware_marker_contract_passes(self):
        repo, snapshot = self.fixture()
        self.assertEqual(marker_issues(repo, snapshot), [])

    def test_target_palette_alone_cannot_hide_wrong_hardware_colors(self):
        repo, snapshot = self.fixture()
        actual = bytearray.fromhex(snapshot['obj_pal'])
        actual[10] ^= 1
        snapshot['obj_pal'] = actual.hex()
        self.assertIn('caught_ball_hardware_palette', marker_issues(repo, snapshot))

    def test_wrong_obj_palette_selection_is_detected(self):
        repo, snapshot = self.fixture()
        oam = bytearray.fromhex(snapshot['oam'])
        oam[12 * 4 + 3] = 3
        snapshot['oam'] = oam.hex()
        self.assertIn('caught_ball_oam_0', marker_issues(repo, snapshot))

    def test_intermediate_cursor_is_detected(self):
        repo, snapshot = self.fixture()
        oam = bytearray.fromhex(snapshot['oam'])
        oam[85] += 32
        snapshot['oam'] = oam.hex()
        self.assertIn('cursor_geometry', marker_issues(repo, snapshot))

    def test_missing_uncaught_marker_is_expected(self):
        repo, snapshot = self.fixture()
        oam = bytearray.fromhex(snapshot['oam'])
        oam[48:52] = bytes(4)
        snapshot.update(grid_flags='01' + '03' * 8, oam=oam.hex())
        self.assertEqual(marker_issues(repo, snapshot), [])

    def test_equivalent_dynamic_tile_numbers_are_not_placeholder_text(self):
        _, before = self.fixture()
        vram = bytearray.fromhex(before['vram'])
        vram[0x1010:0x1020] = bytes((0x55, 0xaa)) * 8
        vram[0x1020:0x1030] = vram[0x1010:0x1020]
        vram[0x1c00] = 1
        before['vram'] = vram.hex()
        after = deepcopy(before)
        vram[0x1c00] = 2
        after['vram'] = vram.hex()
        self.assertEqual(window_pixels(before), window_pixels(after))

    def test_changed_header_pixels_are_detected(self):
        _, before = self.fixture()
        after = deepcopy(before)
        vram = bytearray.fromhex(before['vram'])
        vram[0x1010:0x1020] = b'\xff\x00' * 8
        vram[0x1c00] = 1
        after['vram'] = vram.hex()
        self.assertNotEqual(window_pixels(before), window_pixels(after))

    def test_legitimate_grid_icon_animation_does_not_change_header_check(self):
        _, before = self.fixture()
        after = deepcopy(before)
        vram = bytearray.fromhex(before['vram'])
        vram[0x1c00 + 5 * 32] = 1
        vram[0x1010:0x1020] = b'\xff\x00' * 8
        after['vram'] = vram.hex()
        self.assertEqual(window_pixels(before), window_pixels(after))


if __name__ == '__main__':
    unittest.main()
