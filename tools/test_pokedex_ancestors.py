"""Precomputed production ancestor tables, page groups and font ownership."""
import unittest

from dex_timing.assets import Repository, offset, read_symbols
from dex_timing.costs import machine
from dex_timing.cold_listing import ROOT
from pokedex_info_assets import Compiler, evolution_graph, future_stages, pack


class AncestorAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = Compiler(ROOT)
        cls.data = cls.compiler.compile(ancestors=True)

    def test_bayleef_and_meganium_keep_group_order_and_edge_requirements(self):
        self.assertEqual(self.data['headings']['BAYLEEF'], ['Stats', 'Evolutions', 'Evolves from'])
        self.assertEqual(self.data['headings']['MEGANIUM'], ['Stats', 'Evolves from'])
        for name, expected in (
            ('BAYLEEF', [('Meganium', 'Level 32', ''), ('Chikorita', 'Level 16', '')]),
            ('MEGANIUM', [('Chikorita', 'Level 16', ''), ('Bayleef', 'Level 32', '')])):
            actual = [self.data['records'][record][2] for page in self.data['pages'][name] for record in page]
            self.assertEqual(actual, expected)

    def test_all_chains_are_earliest_first_without_sibling_branches(self):
        graph = evolution_graph(ROOT)
        parents = {child:(parent, method) for parent, entries in graph.items() for child, method in entries}
        for name in self.data['names']:
            chain, node = [], name
            while node in parents:
                node, method = parents[node]
                chain.insert(0, node)
            actual = [self.data['records'][record][0]
                      for page, heading in zip(self.data['pages'][name], self.data['headings'][name][1:])
                      if heading == 'Evolves from' for record in page]
            self.assertEqual(actual, chain, name)

    def test_every_page_fits_and_odd_groups_remain_separate(self):
        for name, pages in self.data['pages'].items():
            self.assertLessEqual(1 + len(pages), 19, name)
            for page in pages:
                self.assertLessEqual(len(page), 2)
                tiles = {tile for record in page for line in self.data['records'][record][1]
                         for tile in self.data['lines'][line][1]}
                self.assertLessEqual(len(tiles), 40, name)
        self.assertEqual(list(map(len, self.data['pages']['BAYLEEF'])), [1, 1])
        self.assertEqual(self.data['headings']['FARFETCH_D'], ['Stats'])

    def test_heading_has_exactly_thirteen_bank_one_tiles(self):
        title = self.data['titles']['Evolves from']
        self.assertEqual(title['cells'], list(range(0xb5, 0xc2)))
        self.assertEqual(title['bank'], 1)
        pixels = self.compiler.text('Evolves from', 5)
        self.assertEqual(title['tiles'], [pack([row[x:x+8] for row in pixels])
                                        for x in range(0, len(pixels[0]), 8)])


@unittest.skipUnless((ROOT / 'pokecrystal.sym').exists(), 'Linked production required')
class AncestorLinkedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        if 'PokedexInfoAncestorTitleGFX' not in cls.repo.symbols:
            raise unittest.SkipTest('Precomputed ancestor production is not enabled')
        cls.data = Compiler(ROOT).compile(ancestors=True)

    def test_all_native_headers_records_selectors_and_titles(self):
        graph = evolution_graph(ROOT)
        parents = {child:(parent, method) for parent, entries in graph.items() for child, method in entries}
        bank, table = self.repo.symbols['PokedexInfoSpecies']
        for index, name in enumerate(self.data['names'], 1):
            chain, node = [], name
            while node in parents:
                node, method = parents[node]
                chain.insert(0, node)
            groups = [[target for target, method in future_stages(graph, name)], chain]
            cpu = machine(self.repo)
            cpu.write(0xff70, 3)
            cpu.field('wPrevDexEntry', index, 2)
            cpu.run('PokedexAncestors_PageCount')
            expected_pages = 1 + sum((len(group)+1)//2 for group in groups)
            self.assertEqual(cpu.read(self.repo.symbols['wPokedexInfoPageCount'][1]), expected_pages)
            cursor = 1
            for group_number, group in enumerate(groups):
                at = offset((bank, table + (index-1)*6 + group_number*3))
                self.assertEqual(self.repo.rom[at], len(group))
                pointer = int.from_bytes(self.repo.rom[at+1:at+3], 'little')
                for local in range((len(group)+1)//2):
                    with self.subTest(species=name, page=cursor):
                        cpu.field('wPokedexInfoPage', cursor)
                        cpu.run('PokedexAncestors_SelectPage')
                        self.assertEqual(cpu.pair(2), pointer + local*4)
                        first = offset((bank, cpu.pair(2)))
                        entries = group[local*2:local*2+2]
                        actual = []
                        for entry in range(len(entries)):
                            record = int.from_bytes(self.repo.rom[first+entry*2:first+entry*2+2], 'little')
                            record = offset((bank, record))
                            target = int.from_bytes(self.repo.rom[record:record+2], 'little')
                            actual.append(self.data['names'][target-1])
                        self.assertEqual(actual, entries)
                        cpu.run('PokedexAncestors_DrawTitle')
                        title = self.data['titles'][self.data['headings'][name][cursor]]
                        maps = self.repo.symbols['wPokedexOwnerTilemapBuffer'][1] + 9*32 + 4
                        attrs = self.repo.symbols['wPokedexOwnerAttrmapBuffer'][1] + 9*32 + 4
                        self.assertEqual(cpu.data(maps, len(title['cells'])), bytes(title['cells']))
                        self.assertEqual(cpu.data(attrs, len(title['cells'])),
                                         bytes([title.get('bank',0)*8]*len(title['cells'])))
                    cursor += 1

    def test_static_heading_preserves_atlases_sidebar_and_caller_banks(self):
        cpu = machine(self.repo)
        cpu.allowed_io.add(0xff40)
        cpu.write(0xff70, 3)
        cpu.write(0xff4f, 0)
        cpu.field('wPrevDexEntry', self.data['names'].index('MEGANIUM')+1, 2)
        cpu.field('wPokedexInfoCaught', 1)
        cpu.vram[0][:] = bytes([0x75])*8192
        cpu.vram[1][:] = bytes([0x69])*8192
        before = bytes(cpu.vram[1])
        cpu.run('PokedexAncestors_PrepareTitle')
        self.assertEqual(cpu.ram[0xff70], 3)
        self.assertEqual(cpu.ram[0xff4f], 0)
        expected = b''.join(self.data['titles']['Evolves from']['tiles'])
        self.assertEqual(bytes(cpu.vram[1][0xb50:0xc20]), expected)
        self.assertEqual(bytes(cpu.vram[1][:0xb50]), before[:0xb50])
        self.assertEqual(bytes(cpu.vram[1][0xc20:]), before[0xc20:])
        self.assertEqual(bytes(cpu.vram[0]), bytes([0x75])*8192)

    def test_unown_restoration_is_exact_and_preserves_banks(self):
        cpu = machine(self.repo)
        cpu.allowed_io.add(0xff40)
        cpu.write(0xff70, 5)
        cpu.write(0xff4f, 0)
        cpu.vram[1][:] = bytes([0x69])*8192
        cpu.run('PokedexAncestors_RestoreUnownFont')
        source = offset(self.repo.symbols['UnownFont'])
        self.assertEqual(bytes(cpu.vram[1][0xb50:0xc20]),
                         bytes(value ^ 255 for value in self.repo.rom[source:source+208]))
        self.assertEqual(cpu.ram[0xff70], 5)
        self.assertEqual(cpu.ram[0xff4f], 0)

    def test_original_live_ram_addresses_and_region_sizes_are_unchanged(self):
        before = read_symbols(ROOT / 'build/dex-selected-ancestors-vram-20261012-v6/rollback/pokecrystal.sym')
        for name, value in before.items():
            if name.startswith(('w','s','h')) and value[1] >= 0xa000 and name in self.repo.symbols:
                self.assertEqual(self.repo.symbols[name], value, name)


if __name__ == '__main__':
    unittest.main()
