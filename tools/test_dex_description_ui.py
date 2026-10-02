from copy import deepcopy
import unittest

from dex_timing.assets import Repository, offset
from dex_timing.cold_listing import ROOT
from dex_timing.description_ui import audit, expected_types, linked


@unittest.skipUnless((ROOT / 'pokecrystal.gbc').exists(), 'current linked ROM required')
class DescriptionUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        if 'PokedexDescriptionTilemap' not in cls.repo.symbols:
            raise unittest.SkipTest('rebuild the Description UI implementation')

    def fixture(self, types=(22, 22), page=0, alternate=False):
        repo = self.repo
        shell = linked(repo, 'PokedexDescriptionTilemap', 360)
        edge = linked(repo, 'PokedexDescriptionRightEdge', 18)
        tilemap = bytearray(b''.join(shell[y * 20:(y + 1) * 20] + edge[y:y + 1]
                                   for y in range(18)))
        attrs, gfx, palettes = bytearray(378), bytearray(128), bytearray(64)
        palettes[16:24] = bytes((255, 127, 0, 0, 0, 0, 165, 20))
        for y in (1, 2):
            for x in (18, 19):
                attrs[y * 21 + x] = 10
                tilemap[y * 21 + x] = (0x6c if alternate else 0xb1) + 2 * (y - 1) + x - 18
        for slot, type_id in enumerate(types if types[0] != types[1] else types[:1]):
            pointer = linked(repo, 'CompactTypeIconGFXPointers', 87)[3 * type_id:3 * type_id + 3]
            start = offset((pointer[0], int.from_bytes(pointer[1:], 'little')))
            icon = bytearray(repo.rom[start:start + 64])
            for address, mask in ((0, 128), (14, 128), (48, 1), (62, 1)):
                icon[address] |= mask
            gfx[slot * 64:(slot + 1) * 64] = icon
            cells = slice(7 * 21 + 9 + 5 * slot, 7 * 21 + 13 + 5 * slot)
            base = 0x70 if alternate else 0x64
            tilemap[cells] = bytes(range(base + 4 * slot, base + 4 * slot + 4))
            attrs[cells] = bytes([14 + slot] * 4)
            pointers = linked(repo, 'TypeIconPalettePointers', 58)
            address = int.from_bytes(pointers[2 * type_id:2 * type_id + 2], 'little')
            start = offset((repo.symbols['TypeIconPalettes'][0], address))
            palette = bytearray(repo.rom[start:start + 8])
            palette[2:4] = bytes((165, 20))
            palettes[(6 + slot) * 8:(7 + slot) * 8] = palette
        if page:
            tilemap[8 * 21 + 2] = 0x79
            tilemap[9 * 21 + 2] = 0x7a
        return dict(page=page, types=types, map=tilemap.hex(), attrs=attrs.hex(),
                    palettes=palettes.hex(), type_gfx=gfx.hex(),
                    border_gfx=linked(repo, 'PokedexDescriptionGFX', 160).hex())

    def test_single_and_dual_types_on_both_pages(self):
        for type_id in range(29):
            for types in ((type_id, type_id), (type_id, (type_id + 1) % 29)):
                for page in (0, 1):
                    for alternate in (False, True):
                        self.assertEqual(audit(self.repo, self.fixture(types, page, alternate)), [])

    def test_icons_cannot_mix_buffer_sets(self):
        ui = self.fixture(alternate=True)
        data = bytearray.fromhex(ui['map'])
        data[21 + 18] = 0xb1
        ui['map'] = data.hex()
        self.assertIn('footprint_tiles', audit(self.repo, ui))

    def test_type_graphics_attributes_and_palette_are_checked_independently(self):
        ui = self.fixture((22, 28))
        for field, index, issue in (('type_gfx', 64, 'type_graphics_1'),
                                    ('attrs', 7 * 21 + 14, 'type_attrs_1'),
                                    ('map', 7 * 21 + 14, 'type_tiles_1'),
                                    ('palettes', 56, 'type_palette_1')):
            corrupt = deepcopy(ui)
            data = bytearray.fromhex(corrupt[field])
            data[index] ^= 1
            corrupt[field] = data.hex()
            self.assertIn(issue, audit(self.repo, corrupt))

    def test_monotype_does_not_leave_previous_second_badge(self):
        ui = self.fixture()
        data = bytearray.fromhex(ui['map'])
        data[7 * 21 + 14] = 0x68
        ui['map'] = data.hex()
        self.assertIn('stale_second_type', audit(self.repo, ui))

    def test_right_edge_palette_and_tiles_are_checked(self):
        for field in ('map', 'attrs'):
            ui = self.fixture()
            data = bytearray.fromhex(ui[field])
            data[7 * 21 + 20] ^= 1
            ui[field] = data.hex()
            self.assertIn('shell_20_7', audit(self.repo, ui))

    def test_page_number_must_match_page(self):
        ui = self.fixture(page=0)
        ui['page'] = 1
        issues = audit(self.repo, ui)
        self.assertIn('page_badge', issues)
        self.assertIn('shell_2_8', issues)

    def test_footprint_is_not_using_the_ui_black_background(self):
        ui = self.fixture()
        data = bytearray.fromhex(ui['palettes'])
        data[22:24] = bytes(2)
        ui['palettes'] = data.hex()
        self.assertIn('footprint_palette', audit(self.repo, ui))

    def test_source_type_resolution_includes_extended_species(self):
        self.assertEqual(expected_types(self.repo, 'chikorita'), [22, 22])
        self.assertEqual(expected_types(self.repo, 'weavile'), [8, 25])
        self.assertEqual(expected_types(self.repo, 'unown_a'), [24, 24])


if __name__ == '__main__':
    unittest.main()
