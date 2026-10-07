import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image
from dex_timing.assets import Repository, offset
from dex_timing.listing_options import grid_audit
from pokedex_sort_assets import ROOT, compile_tables


class SortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / os.environ.get('DEX_OPTIONS_BUILD', 'build/dex-options-prototype-20261005c')
        cls.repo = Repository(ROOT, cls.output / 'pokecrystal-dex-options.gbc',
                              cls.output / 'pokecrystal-dex-options.sym')
        cls.text, cls.manifest = compile_tables()

    def fixture(self, root):
        for name in ('constants/pokemon_constants.asm', 'data/pokemon/names.asm',
                     'data/pokemon/dex_order_new.asm'):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def test_all_orders_cover_every_species_once(self):
        orders = self.manifest['orders']
        self.assertEqual(self.manifest['species'], 373)
        family = orders['NewPokedexOrder']
        for order in orders.values():
            self.assertEqual(len(order), 373)
            self.assertEqual(set(order), set(family))
        national = orders['NationalPokedexOrder']
        numbers = [self.manifest['national'][name] for name in national]
        self.assertEqual(numbers, sorted(numbers))
        self.assertLess(national.index('SHROOMISH'), national.index('GALLADE'))
        alpha = orders['AlphabeticalPokedexOrder']
        self.assertLess(alpha.index('ABRA'), alpha.index('ABSOL'))
        self.assertLess(alpha.index('BANETTE'), alpha.index('BUNEARY'))

    def test_linked_word_tables_and_seen_metadata_match_sources(self):
        constants = list(self.manifest['national'])
        manifest = json.loads((self.output / 'sort-manifest.json').read_text())
        for label, order in self.manifest['orders'].items():
            words = offset(self.repo.symbols[label])
            record_symbol = self.repo.symbols.get(label + 'Records')
            self.assertEqual(record_symbol is not None, manifest.get('records', True))
            records = offset(record_symbol) if record_symbol else None
            for position, name in enumerate(order):
                index = constants.index(name) + 1
                word = index.to_bytes(2, 'little')
                self.assertEqual(self.repo.rom[words + 2 * position:words + 2 * position + 2], word)
                if records is not None:
                    self.assertEqual(self.repo.rom[records + 4 * position:records + 4 * position + 4],
                                     word + bytes(((index - 1) // 8, 1 << ((index - 1) % 8))))

    def test_records_free_generation_keeps_identical_compact_orders(self):
        text, manifest = compile_tables(records=False)
        self.assertEqual(manifest, self.manifest)
        self.assertNotIn('OrderRecords', text)
        for label, order in manifest['orders'].items():
            self.assertIn(label + ':', text)
            self.assertEqual(text.count('\tdw '), 3 * len(order))

    def test_user_art_is_opaque_and_linked_without_pixel_changes(self):
        image = Image.open(ROOT / 'gfx/pokedex/pokedex_popover_sheet.png').convert('RGBA')
        self.assertEqual(image.size, (32, 16))
        self.assertEqual({image.getpixel((x, y)) for y in range(16) for x in range(32)},
                         {(255, 255, 255, 255), (85, 85, 85, 255)})
        data = bytearray()
        for ty in range(2):
            for tx in range(4):
                for y in range(8):
                    plane = sum((image.getpixel((tx * 8 + x, ty * 8 + y))[0] == 85) << (7 - x)
                                for x in range(8))
                    data.extend((0, plane))
        start = offset(self.repo.symbols['PokedexPopover_BorderGFX'])
        self.assertEqual(self.repo.rom[start:start + 128], bytes(data))

    def test_national_label_uses_the_existing_eight_cell_font(self):
        symbol = 'PokedexPopover_Sort' if 'PokedexPopover_Sort' in self.repo.symbols else 'PokedexPopover_Draw.Sort'
        start = offset(self.repo.symbols[symbol])
        labels = self.repo.rom[start:start + 27].split(bytes((0x4e,)))
        self.assertEqual(labels[1], bytes((0x8d, 0xa0, 0xb3, 0xd1, 0x7f, 0x83, 0xa4, 0xb7)))
        source = (ROOT / 'tools/dex_timing/probes/pokedex_popover.asm').read_text()
        self.assertNotIn('label-abbreviation', source)

    def test_modern_border_is_the_six_user_tiles_without_pixel_changes(self):
        if 'PokedexPopover_ModernBorderGFX' not in self.repo.symbols:
            self.skipTest('Historical prototype has no shifted border')
        with Image.open(ROOT / 'gfx/pokedex/pokedex_popover_sheet_modern.png') as source:
            image = source.convert('RGBA')
        self.assertEqual(image.size, (16, 24))
        self.assertEqual({image.getpixel((x, y)) for y in range(24) for x in range(16)},
                         {(255, 255, 255, 255), (85, 85, 85, 255)})
        data = bytearray()
        for ty in range(3):
            for tx in range(2):
                for y in range(8):
                    plane = sum((image.getpixel((tx * 8 + x, ty * 8 + y))[0] == 85) << (7 - x)
                                for x in range(8))
                    data.extend((0, plane))
        start = offset(self.repo.symbols['PokedexPopover_ModernBorderGFX'])
        self.assertEqual(self.repo.rom[start:start + 96], bytes(data))

    def test_shifted_labels_and_borders_fit_the_inactive_info_atlas(self):
        if 'PokedexPopover_ShiftCells' not in self.repo.symbols:
            self.skipTest('Historical prototype has no shifted labels')
        table = offset(self.repo.symbols['PokedexInfoAtlasCells'])
        atlas = self.repo.rom[table:table + 80:2]
        start = offset(self.repo.symbols['PokedexPopover_ShiftCells'])
        shifted = self.repo.rom[start:start + 31]
        borders = set(range(0xfa, 0x100)) | {0x28, 0x29}
        self.assertEqual(len(set(shifted)), 31)
        self.assertFalse(set(shifted) & borders)
        self.assertEqual(len(set(shifted) | borders), 39)
        self.assertTrue((set(shifted) | borders) <= set(atlas))

    def test_displayed_name_edits_regenerate_alphabet_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            names = root / 'data/pokemon/names.asm'
            names.write_text(names.read_text().replace('"Chikorita"', '"ZZZTEST"', 1))
            _, result = compile_tables(root)
            self.assertEqual(result['orders']['AlphabeticalPokedexOrder'][-1], 'CHIKORITA')
            self.assertEqual(result['orders']['NewPokedexOrder'], self.manifest['orders']['NewPokedexOrder'])

    def test_new_species_metadata_regenerates_all_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            source = root / 'constants/pokemon_constants.asm'
            source.write_text(source.read_text().replace('DEF NUM_POKEMON',
                              '\tconst DEX_TEST ; NatDex 999\nDEF NUM_POKEMON', 1))
            names = root / 'data/pokemon/names.asm'
            names.write_text(names.read_text() + '\n\tdname "ZZZTEST"\n')
            order = root / 'data/pokemon/dex_order_new.asm'
            order.write_text(order.read_text() + '\n\tdw DEX_TEST\n')
            _, result = compile_tables(root)
            self.assertEqual(result['species'], 374)
            for sequence in result['orders'].values():
                self.assertEqual(sequence[-1], 'DEX_TEST')
            source.write_text(source.read_text().replace('NatDex 999', 'NatDex 152'))
            with self.assertRaisesRegex(ValueError, 'Duplicate National'):
                compile_tables(root)
            source.write_text(source.read_text().replace('NatDex 152', 'missing metadata'))
            with self.assertRaisesRegex(ValueError, 'explicit NatDex'):
                compile_tables(root)

    def test_incomplete_family_order_fails_instead_of_silently_dropping_species(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            order = root / 'data/pokemon/dex_order_new.asm'
            order.write_text(order.read_text().replace('\tdw CHIKORITA', '\tdw BAYLEEF', 1))
            with self.assertRaisesRegex(ValueError, 'every species exactly once'):
                compile_tables(root)

    def test_no_new_rom0_or_physical_ram_sections(self):
        before = (ROOT / 'pokecrystal.map').read_text().split('\n\n')[0].splitlines()
        after = (self.output / 'pokecrystal-dex-options.map').read_text().split('\n\n')[0].splitlines()
        for label in ('ROM0', 'WRAM0', 'WRAMX', 'HRAM', 'SRAM'):
            self.assertEqual(next(line for line in before if label + ':' in line),
                             next(line for line in after if label + ':' in line))

    def test_grid_oracle_rejects_stale_tiles_with_valid_tags_and_palettes(self):
        constants = list(self.manifest['national'])
        order = [constants.index(name) + 1
                 for name in self.manifest['orders']['NewPokedexOrder'][:9]]
        vram = bytearray(8192)
        tags = bytearray(b'\xff' * 10)
        palettes = bytearray()
        table = offset(self.repo.symbols['MonMenuIcons'])
        icons = []
        for permanent in order:
            at = table + (permanent - 1) * 4
            bank, low, high, palette = self.repo.rom[at:at + 4]
            source = offset((bank, low | high << 8))
            icons.append(self.repo.rom[source:source + 128])
            palettes.append(palette >> 4)
        for row in range(3):
            physical = row + 1
            tags[physical * 2:physical * 2 + 2] = (row * 3).to_bytes(2, 'little')
            left, center, right = icons[row * 3:row * 3 + 3]
            for address, data in ((0, center), (0x1000, left[:64] + right[:64]),
                                  (0xd20, left[64:] + right[64:])):
                start = address + physical * 128
                vram[start:start + 128] = data
        ram = {self.repo.symbols[name][1]: data for name, data in (
            ('wPokedexGridTopPhysicalRow', bytes((1,))),
            ('wPokedexGridCacheRowOffsets', tags),
            ('wPokedexGridIconPalettes', palettes))}

        class Snapshot:
            def command(self, command):
                if command == 'peek':
                    return dict(presentation=0, end=9, scroll=0)
                operation, bank, address, size = command.split()
                address, size = int(address), int(size)
                data = ram[address] if operation == 'perfram' else vram[address & 8191:(address & 8191) + size]
                return dict(bytes=bytes(data).hex())

        grid_audit(Snapshot(), self.repo, order)
        vram[128] ^= 1
        with self.assertRaisesRegex(RuntimeError, 'Stale grid graphics: center, row 0'):
            grid_audit(Snapshot(), self.repo, order)


if __name__ == '__main__':
    unittest.main()
