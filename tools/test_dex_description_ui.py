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
        attrs, gfx, palettes, obj_palettes, oam = (bytearray(378), bytearray(128),
                                               bytearray(64), bytearray(64), bytearray(160))
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
            for at in range(0, 64, 2):
                icon[at] = ~(icon[at] ^ icon[at + 1]) & 255
            gfx[slot * 64:(slot + 1) * 64] = icon
            base = 0x30 if alternate else 0x28
            for i in range(4):
                at = slot * 16 + i * 4
                oam[at:at + 4] = bytes((72, 75 + slot * 40 + i * 8, base + slot * 4 + i, 8 + slot))
            pointers = linked(repo, 'TypeIconPalettePointers', 58)
            address = int.from_bytes(pointers[2 * type_id:2 * type_id + 2], 'little')
            start = offset((repo.symbols['TypeIconPalettes'][0], address))
            palette = bytearray(repo.rom[start:start + 8])
            palette[2:4] = palette[0:2]
            obj_palettes[slot * 8:(slot + 1) * 8] = palette
        if page:
            tilemap[8 * 21 + 2] = 0x79
            tilemap[9 * 21 + 2] = 0x7a
        return dict(page=page, types=types, map=tilemap.hex(), attrs=attrs.hex(),
                    palettes=palettes.hex(), obj_palettes=obj_palettes.hex(),
                    oam=oam.hex(), type_gfx=gfx.hex(),
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
                                    ('oam', 17, 'type_oam_1_0'),
                                    ('map', 7 * 21 + 14, 'old_bg_type_tiles'),
                                    ('obj_palettes', 8, 'type_palette_1')):
            corrupt = deepcopy(ui)
            data = bytearray.fromhex(corrupt[field])
            data[index] ^= 1
            corrupt[field] = data.hex()
            self.assertIn(issue, audit(self.repo, corrupt))

    def test_monotype_does_not_leave_previous_second_badge(self):
        ui = self.fixture()
        data = bytearray.fromhex(ui['oam'])
        data[16] = 72
        ui['oam'] = data.hex()
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

    def test_page_badge_uses_standalone_sheet_without_growing_shell(self):
        sheet = (ROOT / 'gfx/pokedex/pokedex_page_numbers.2bpp').read_bytes()
        self.assertEqual(len(sheet), 20 * 16)
        start = self.repo.symbols['PokedexDescriptionGFX'][1]
        end = self.repo.symbols['PokedexDescriptionGFXEnd'][1]
        self.assertEqual(end - start, 10 * 16)
        shell = linked(self.repo, 'PokedexDescriptionGFX', 10 * 16)
        for destination, source in ((1, 0), (2, 2), (6, 1), (7, 3), (8, 4), (9, 5)):
            self.assertEqual(shell[destination * 16:(destination + 1) * 16],
                             sheet[source * 16:(source + 1) * 16])

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
