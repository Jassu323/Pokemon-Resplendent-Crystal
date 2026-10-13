"""Independent pixel/data checks for the private Selected runtime renderer."""
import os
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from dex_timing.assets import Repository
from dex_timing.costs import machine
from pokedex_info_assets import Compiler, constants, evolution_graph, future_stages, previous_stages, pack, width

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = Path(os.environ.get('DEX_RUNTIME_SOURCE', ROOT / 'build/dex-selected-runtime-20261012-v2/candidate'))


class RuntimeDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(CANDIDATE, CANDIDATE / 'pokecrystal.gbc', CANDIDATE / 'pokecrystal.sym')
        cls.compiler = Compiler(ROOT)
        cls.ancestors = 'PokedexInfoEvolvesFromTitle' in cls.repo.symbols
        cls.data = cls.compiler.compile(ancestors=cls.ancestors)

    def cpu(self):
        cpu = machine(self.repo)
        cpu.ram[0xff70] = 3
        if self.ancestors:
            cpu.allowed_io.add(0xff40)
        return cpu

    def block(self, cpu, label, size):
        bank, address = self.repo.symbols[label]
        previous = cpu.ram[0xff70]
        if 0xd000 <= address < 0xe000:
            cpu.ram[0xff70] = bank
        try:
            return cpu.data(address, size)
        finally:
            cpu.ram[0xff70] = previous

    def code(self, glyph):
        return {'<LV>': 0x6e, '>': 0x1c, '<': 0x1d, '=': 0x1e}.get(glyph, self.compiler.chars.get(glyph))

    def test_runtime_headings_match_every_resident_pixel(self):
        cpu = self.cpu()
        cpu.run('PokedexRuntime_LoadTitles')
        if self.ancestors:
            cpu.run('PokedexRuntime_LoadAncestorTitle')
        for text, title in self.data['titles'].items():
            cpu.ram[0xff4f] = title.get('bank', 0)
            for cell, tile in zip(title['cells'], title['tiles']):
                with self.subTest(title=text, cell=cell):
                    signed = cell if cell < 128 else cell - 256
                    self.assertEqual(cpu.data(0x9000 + signed * 16, 16), tile)

    def test_all_shared_stat_tiles_match_the_old_assets(self):
        cpu = self.cpu()
        for index, source in enumerate(self.data['shared']):
            with self.subTest(tile=index):
                cpu.run('PokedexRuntime_BuildSharedOne' if 'PokedexRuntime_BuildSharedOne' in self.repo.symbols else 'PokedexRuntime_BuildShared')
                self.assertEqual(cpu.data(self.repo.symbols['wPokedexInfoGFX'][1] + 16 * index, 16),
                                 self.compiler.pool[source])

    def test_all_256_numeric_bar_composites_match(self):
        for value in range(256):
            with self.subTest(value=value):
                cpu = self.cpu()
                cpu.field('wPokedexInfoScratch', value)
                cpu.field('wPokedexInfoWidth', width(value))
                cpu.field('wPokedexInfoTileCount', 15)
                cpu.run('PokedexRuntime_BuildNumbers')
                expected = b''.join(self.compiler.pool[tile] for tile in self.data['numbers'][value])
                self.assertEqual(cpu.data(self.repo.symbols['wPokedexInfoGFX'][1] + 15 * 16, 64), expected)

    def test_every_evolution_line_matches_without_stored_glyphs(self):
        for text, tiles in self.data['lines']:
            if not text:
                continue
            with self.subTest(text=text):
                cpu = self.cpu()
                encoded = bytes(self.code(glyph) for glyph in re.findall(r'<LV>|.', text)) + b'\x50'
                cpu.block(self.repo.symbols['wPokedexRuntimeTextBuffer'][1], encoded)
                cpu.field('wPokedexInfoMapCursor', self.repo.symbols['wPokedexOwnerTilemapBuffer'][1] + 11 * 32 + 4, 2)
                cpu.field('wPokedexInfoAttrCursor', self.repo.symbols['wPokedexOwnerAttrmapBuffer'][1] + 11 * 32 + 4, 2)
                cpu.field('wPokedexInfoAtlasBuffer', 1)
                cpu.field('wPokedexInfoPalette', 1)
                cpu.run('PokedexRuntime_StartText')
                for _ in range(32):
                    if self.block(cpu, 'wPokedexRuntimeTextState', 1) == b'\x03':
                        break
                    cpu.run('PokedexRuntime_TextGlyphStep')
                else:
                    self.fail('Text preparation did not finish')
                actual = []
                count = self.block(cpu, 'wPokedexRuntimeTextTiles', 1)[0]
                for _ in range(count):
                    cpu.run('PokedexRuntime_TextTileStep')
                ids = cpu.data(self.repo.symbols['wPokedexOwnerTilemapBuffer'][1] + 11 * 32 + 4, count)
                for index in ids:
                    actual.append(cpu.data(self.repo.symbols['wPokedexInfoGFX'][1] + index * 16, 16))
                self.assertEqual(actual, [self.compiler.pool[tile] for tile in tiles])

    def test_all_species_walk_native_evolutions_in_the_same_order(self):
        graph = evolution_graph(ROOT)
        values = constants(ROOT / 'constants/item_constants.asm')
        methods = {'EVOLVE_LEVEL': 1, 'EVOLVE_ITEM': 2, 'EVOLVE_TRADE': 3,
                   'EVOLVE_HAPPINESS': 4, 'EVOLVE_STAT': 5}
        values.update({'TR_ANYTIME': 1, 'TR_MORNDAY': 2, 'TR_EVENITE': 3,
                       'ATK_GT_DEF': 1, 'ATK_LT_DEF': 2, 'ATK_EQ_DEF': 3})
        number = lambda token: int(token) & 255 if token.lstrip('-').isdigit() else values[token]
        for index, name in enumerate(self.data['names'], 1):
            with self.subTest(species=name):
                cpu = self.cpu()
                cpu.field('wPrevDexEntry', index, 2)
                cpu.run('PokedexRuntime_PrepareData')
                expected = []
                for target, method in future_stages(graph, name):
                    expected += [(self.data['names'].index(target) + 1).to_bytes(2, 'little') +
                                 bytes((methods[method[0]], number(method[1]), number(method[2]) if len(method) > 2 else 0))]
                count = self.block(cpu, 'wPokedexRuntimeEvoCount', 1)[0]
                self.assertEqual(count, len(expected))
                if 'PokedexInfoSemanticSpecies' in self.repo.symbols:
                    table = self.repo.symbols['PokedexInfoSemanticSpecies']
                    at = table[0] * 0x4000 + table[1] - 0x4000 + (index - 1) * (6 if self.ancestors else 3)
                    address = int.from_bytes(self.repo.rom[at + 1:at + 3], 'little')
                    at = table[0] * 0x4000 + address - 0x4000
                    self.assertEqual(self.repo.rom[at:at + count * 5], b''.join(expected))
                else:
                    self.assertEqual(self.block(cpu, 'wPokedexRuntimeEvoRecords', count * 5), b''.join(expected))

    def test_generated_info_graphics_and_indexes_are_not_linked(self):
        for label in ('PokedexInfoTileGFX', 'PokedexInfoTitleGFX', 'PokedexInfoNumbers', 'PokedexInfoSpecies',
                      *(() if 'PokedexInfoSemanticSpecies' in self.repo.symbols else
                        ('PokedexMovesSpecies', 'PokedexMovesMachineMoves'))):
            self.assertNotIn(label, self.repo.symbols)

    def test_ancestor_order_requirements_page_boundaries_and_native_selection(self):
        if not self.ancestors:
            self.skipTest('Ancestor pages are not enabled in this build')
        graph = evolution_graph(ROOT)
        parent = {child: (source, method) for source, edges in graph.items() for child, method in edges}
        for index, name in enumerate(self.data['names'], 1):
            chain, node = [], name
            while node in parent:
                node, method = parent[node]
                chain.insert(0, (node, tuple(method)))
            groups = [future_stages(graph, name), chain]
            pages = [(kind, group[first:first + 2]) for kind, group in enumerate(groups)
                     for first in range(0, len(group), 2)]
            cpu = self.cpu()
            cpu.field('wPrevDexEntry', index, 2)
            cpu.run('PokedexAncestors_PageCount')
            self.assertEqual(self.block(cpu, 'wPokedexInfoPageCount', 1)[0], 1 + len(pages))
            bank, header = self.repo.symbols['PokedexInfoSemanticSpecies']
            header = bank * 0x4000 + header - 0x4000 + (index - 1) * 6
            for page, (kind, entries) in enumerate(pages, 1):
                with self.subTest(species=name, page=page):
                    cpu.field('wPokedexInfoPage', page)
                    cpu.run('PokedexAncestors_SelectPage')
                    self.assertEqual(self.block(cpu, 'wPokedexRuntimeEvoCount', 1)[0], len(entries))
                    address = int.from_bytes(self.repo.rom[header + kind * 3 + 1:header + kind * 3 + 3], 'little')
                    relative = page - 1 - (0 if kind == 0 else (len(groups[0]) + 1) // 2)
                    self.assertEqual(cpu.pair(2), address + relative * 10)
                    at = bank * 0x4000 + cpu.pair(2) - 0x4000
                    targets = [int.from_bytes(self.repo.rom[at + row * 5:at + row * 5 + 2], 'little') for row in range(len(entries))]
                    self.assertEqual(targets, [self.data['names'].index(target) + 1 for target, _ in entries])
                    cpu.run('PokedexAncestors_DrawTitle')
                    title = self.data['titles'][self.data['headings'][name][page]]
                    self.assertEqual(self.block(cpu, 'wPokedexOwnerTilemapBuffer', 512)[9 * 32 + 4:9 * 32 + 4 + len(title['cells'])], bytes(title['cells']))
                    self.assertEqual(self.block(cpu, 'wPokedexOwnerAttrmapBuffer', 512)[9 * 32 + 4:9 * 32 + 4 + len(title['cells'])], bytes([title.get('bank', 0) * 8] * len(title['cells'])))

    def test_ancestor_title_preserves_listing_art_and_joined_borders(self):
        if not self.ancestors:
            self.skipTest('Ancestor pages are not enabled in this build')
        cpu = self.cpu()
        cpu.vram[0][0xba0:0xca0] = bytes([0x75] * 256)
        cpu.vram[1][0xd00:0xd20] = bytes([0x69] * 32)
        cpu.vram[1][0xd20:0xfa0] = bytes([0x63] * 640)
        cpu.run('PokedexRuntime_LoadTitles')
        cpu.run('PokedexRuntime_LoadAncestorTitle')
        self.assertEqual(bytes(cpu.vram[0][0xba0:0xca0]), bytes([0x75] * 256))
        self.assertEqual(bytes(cpu.vram[1][0xd00:0xd20]), bytes([0x69] * 32))
        self.assertEqual(bytes(cpu.vram[1][0xd20:0xfa0]), bytes([0x63] * 640))

    def test_runtime_memory_bounds_and_title_bank_restoration(self):
        self.assertLessEqual(self.repo.symbols['wPokedexInfoWorkspaceEnd'][1], 0xdc40)
        if 'PokedexInfoSemanticSpecies' not in self.repo.symbols:
            self.assertEqual(self.repo.symbols['wPokedexRuntimeEvoRecords'], (5, 0xd950))
        else:
            self.assertNotIn('wPokedexRuntimeEvoRecords', self.repo.symbols)
            self.assertNotIn('wPokedexRuntimeParents', self.repo.symbols)
        self.assertLessEqual(self.repo.symbols['wPokedexRuntimeCacheEnd'][1], 0xe000)
        loaders = ['PokedexRuntime_LoadTitles'] + (['PokedexRuntime_LoadAncestorTitle'] if self.ancestors else [])
        for loader in loaders:
            for bank in (1, 2, 3, 5, 6):
                for lcdc in (0, 128):
                    with self.subTest(loader=loader, bank=bank, lcdc=lcdc):
                        cpu = self.cpu()
                        cpu.ram[0xff70] = bank
                        cpu.ram[0xff4f] = 1
                        cpu.ram[0xff40] = lcdc
                        cpu.run(loader)
                        self.assertEqual(cpu.ram[0xff70], bank)
                        self.assertEqual(cpu.ram[0xff4f], 1)

    def test_native_move_validation_emits_no_display_tables(self):
        from pokedex_moves_assets import compile
        with patch.object(Path, 'write_text', side_effect=AssertionError('Unexpected display table write')):
            with patch.object(Path, 'write_bytes', side_effect=AssertionError('Unexpected graphics write')):
                rows = compile(ROOT, validate_only=True)
        self.assertEqual(len(rows), 373)
        self.assertLessEqual(max(len(row['pages']) for row in rows.values()), 19)

    def test_runtime_moves_streams_match_all_authoritative_sources(self):
        manifest = json.loads((ROOT / 'build/dex-moves-assets/manifest.json').read_text())
        ids = constants(ROOT / 'constants/move_constants.asm')
        cpu = self.cpu()
        semantic = 'PokedexInfoSemanticSpecies' in self.repo.symbols
        if not semantic:
            cpu.run('PokedexRuntime_BuildParents')
        for index, name in enumerate(self.data['names'], 1):
            with self.subTest(species=name):
                data = manifest[name]
                stem = {'PORYGON_Z': 'porygonz'}.get(name, name.lower())
                base = (ROOT / f'data/pokemon/base_stats/{stem}.asm').read_text()
                line = re.search(r'^\s*tmhm\s*(.*?)$', base, re.M)[1].split(';')[0]
                eligible = {s.strip() for s in line.split(',') if s.strip()}
                machine = re.findall(r'^\s*add_(tm|hm|mt)\s+(\w+)',
                                     (ROOT / 'constants/item_constants.asm').read_text(), re.M)
                flags = sum(1 << i for i, (_, move) in enumerate(machine) if move in eligible)
                cpu.field('wBaseTMHM', flags, 8)
                cpu.field('wPrevDexEntry', index, 2)
                cpu.run('PokedexRuntime_PrepareData')
                if semantic:
                    bank, address = self.repo.symbols['PokedexMovesSpecies']
                    at = bank * 0x4000 + address - 0x4000 + (index - 1) * 17
                    self.assertEqual(self.repo.rom[at], max(1, len(data['pages'])))
                    headers = self.repo.rom[at + 1:at + 17]
                else:
                    headers = self.block(cpu, 'wPokedexRuntimeMovesStreams', 16)
                    self.assertEqual(self.block(cpu, 'wPokedexRuntimeMovesPages', 1)[0], max(1, len(data['pages'])))
                for kind in range(4):
                    count, bank, lo, hi = headers[kind * 4:kind * 4 + 4]
                    self.assertEqual(count, len(data['streams'][kind]))
                    address = lo | hi << 8
                    if kind in (1, 2):
                        if semantic:
                            at = bank * 0x4000 + address - 0x4000
                            actual = self.repo.rom[at:at + count]
                        else:
                            previous = cpu.ram[0xff70]
                            cpu.ram[0xff70] = bank
                            actual = cpu.data(address, count)
                            cpu.ram[0xff70] = previous
                        self.assertEqual(list(actual), data['machines' if kind == 1 else 'tutors'])
                    else:
                        at = bank * 0x4000 + address - 0x4000
                        expected = (b''.join(bytes((level,)) + ids[move].to_bytes(2, 'little')
                                           for level, move in data['streams'][0]) + b'\0' if kind == 0 else
                                    b''.join(ids[move].to_bytes(2, 'little') for _, move in data['streams'][3]) + b'\xff\xff')
                        self.assertEqual(self.repo.rom[at:at + len(expected)], expected)

    def test_all_native_requirements_have_exact_wording(self):
        cpu = self.cpu()
        graph = evolution_graph(ROOT)
        values = constants(ROOT / 'constants/item_constants.asm')
        values.update({'TR_ANYTIME': 1, 'TR_MORNDAY': 2, 'TR_EVENITE': 3,
                       'ATK_GT_DEF': 1, 'ATK_LT_DEF': 2, 'ATK_EQ_DEF': 3})
        method_id = {'EVOLVE_LEVEL': 1, 'EVOLVE_ITEM': 2, 'EVOLVE_TRADE': 3,
                     'EVOLVE_HAPPINESS': 4, 'EVOLVE_STAT': 5}
        number = lambda value: int(value) & 255 if value.lstrip('-').isdigit() else values[value]
        for name in self.data['names']:
            for index, ((target, method), record) in enumerate(zip(future_stages(graph, name), self.data['roots'][name])):
                with self.subTest(species=name, target=target):
                    if 'PokedexInfoSemanticSpecies' in self.repo.symbols:
                        bank, at = self.repo.symbols['PokedexInfoSemanticSpecies']
                        at = bank * 0x4000 + at - 0x4000 + self.data['names'].index(name) * (6 if self.ancestors else 3)
                        address = int.from_bytes(self.repo.rom[at + 1:at + 3], 'little') + index * 5 + 2
                    else:
                        address = self.repo.symbols['wPokedexRuntimeEvoRecords'][1]
                        cpu.ram[0xff70] = 5
                        cpu.block(address, bytes((method_id[method[0]], number(method[1]), number(method[2]) if len(method) > 2 else 0)))
                        cpu.ram[0xff70] = 3
                    cpu.field('wPokedexInfoEvolutionRecord', address, 2)
                    cpu.run('PokedexRuntime_RequirementText')
                    for _ in range(128):
                        if self.block(cpu, 'wPokedexRuntimeTextState', 1) != b'\x01':
                            break
                        cpu.run('PokedexRuntime_ItemTextStep')
                    else:
                        self.fail('Item search did not finish')
                    text = self.data['records'][record][2][1]
                    encoded = bytes(self.code(glyph) for glyph in re.findall(r'<LV>|.', text)) + b'\x50'
                    self.assertEqual(self.block(cpu, 'wPokedexRuntimeTextBuffer', len(encoded)), encoded)

    def test_decimal_formatting_includes_zero_digits(self):
        for value in range(256):
            with self.subTest(value=value):
                cpu = self.cpu()
                cpu.r[7] = value
                cpu.set_pair(1, self.repo.symbols['wPokedexRuntimeTextBuffer'][1])
                cpu.run('PokedexRuntime_AppendDecimal')
                expected = bytes(self.compiler.chars[c] for c in str(value))
                self.assertEqual(self.block(cpu, 'wPokedexRuntimeTextBuffer', len(expected)), expected)

    def test_vram_restoration_reads_exactly_the_committed_atlas(self):
        if 'PokedexRuntime_CopyTiles.pair' not in self.repo.symbols:
            self.skipTest('Only the buffer-free VRAM architecture uses readback')
        for count in range(1, 41):
            for prior_vbk in (0, 1):
                with self.subTest(count=count, vbk=prior_vbk):
                    cpu = self.cpu()
                    expected = bytes((i * 37 + count) & 255 for i in range(count * 16))
                    cpu.vram[1][0x1000:0x1000 + len(expected)] = expected
                    cpu.ram[0xff4f] = prior_vbk
                    cpu.field('wPokedexRuntimeReturnRepair', 1)
                    cpu.field('wPokedexInfoTileCount', count)
                    for _ in range(6):
                        cpu.run('PokedexRuntime_CopyTiles')
                        if self.block(cpu, 'wPokedexInfoCopyTile', 1)[0] == count:
                            break
                    self.assertEqual(self.block(cpu, 'wPokedexInfoGFX', len(expected)), expected)
                    self.assertEqual(cpu.ram[0xff4f], prior_vbk)
                    self.assertEqual(cpu.ram[0xff70], 3)

    def test_rom_restoration_matches_every_stats_and_evolution_atlas(self):
        if 'PokedexRuntime_CopyROMTiles' not in self.repo.symbols:
            self.skipTest('Only the ROM recovery architecture has a recovery atlas')
        for index, name in enumerate(self.data['names'], 1):
            pages = [self.data['shared'] + [tile for value in self.data['stats'][name]
                                          for tile in self.data['numbers'][value]]]
            for records in self.data['pages'][name]:
                tiles = []
                for record in records:
                    for line in self.data['records'][record][1]:
                        for tile in self.data['lines'][line][1]:
                            if tile not in tiles:
                                tiles.append(tile)
                pages.append(tiles)
            for page, tiles in enumerate(pages):
                with self.subTest(species=name, page=page):
                    cpu = self.cpu()
                    cpu.field('wPrevDexEntry', index, 2)
                    cpu.field('wPokedexInfoPage', page)
                    cpu.field('wPokedexInfoTileCount', len(tiles))
                    cpu.field('wPokedexInfoAtlasBuffer', 1)
                    cpu.run('PokedexInfo_BeginRecord')
                    for _ in range(6):
                        cpu.run('PokedexInfo_RecordPage')
                    # Replace the work key as a canceled preparation can do.
                    cpu.field('wPrevDexEntry', 1 if index != 1 else 373, 2)
                    cpu.field('wPokedexInfoPage', 18)
                    key = self.block(cpu, 'wPokedexInfoReturnRecordB', 7 * 32 + 3)[7 * 32:]
                    cpu.block(self.repo.symbols['wPokedexInfoTileSources'][1], key)
                    cpu.field('wPokedexRuntimeReturnRepair', 1)
                    for _ in range(6):
                        cpu.run('PokedexRuntime_CopyROMTiles')
                        if self.block(cpu, 'wPokedexInfoCopyTile', 1)[0] == len(tiles):
                            break
                    expected = b''.join(self.compiler.pool[tile] for tile in tiles)
                    self.assertEqual(self.block(cpu, 'wPokedexInfoGFX', len(expected)), expected)
                    self.assertEqual(cpu.ram[0xff70], 3)


if __name__ == '__main__':
    unittest.main()
