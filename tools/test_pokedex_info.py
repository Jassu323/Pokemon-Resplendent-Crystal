import unittest

from pokedex_info_assets import Compiler, TITLE_CELLS, evolution_graph, future_stages, pack, unpack, width
from dex_timing.assets import Repository, offset
from dex_timing.cold_listing import ROOT
from dex_timing.costs import machine


class InfoAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = Compiler()
        cls.data = cls.compiler.compile()

    def test_quantization_and_endpoint_cap(self):
        self.assertEqual([width(v) for v in (4, 5, 10, 45, 249, 250, 255)],
                         [0, 2, 4, 18, 98, 100, 101])

    def test_skitty_uses_the_game_moon_stone_link(self):
        self.assertEqual(evolution_graph()['SKITTY'],
                         [('DELCATTY', ['EVOLVE_ITEM', 'MOON_STONE'])])
        records = self.data['roots']['SKITTY']
        self.assertEqual([self.data['records'][r][2] for r in records],
                         [('Delcatty', 'Moon Stone', '')])
        self.assertEqual(self.data['roots']['DELCATTY'], [])

    def test_all_future_stages_not_only_the_next_stage(self):
        targets = [target for target, _ in future_stages(evolution_graph(), 'CHIKORITA')]
        self.assertEqual(targets, ['BAYLEEF', 'MEGANIUM'])
        self.assertEqual(self.data['stats']['CHIKORITA'], [45, 49, 65, 49, 65, 45])

    def test_branching_methods_and_empty_third_lines(self):
        graph = evolution_graph()
        for name in ('EEVEE', 'TYROGUE', 'POLIWAG', 'ODDISH'):
            self.assertEqual(len(self.data['roots'][name]), len(future_stages(graph, name)))
        texts = [r[2] for r in self.data['records']]
        self.assertTrue(any(t[1] == 'friendship' for t in texts))
        self.assertTrue(all(not t[2] for t in texts))
        tyrogue = {self.data['records'][r][0]: self.data['records'][r][2][1]
                   for r in self.data['roots']['TYROGUE']}
        self.assertEqual(tyrogue, {'HITMONLEE': '<LV>20 Atk > Def',
                                  'HITMONCHAN': '<LV>20 Atk < Def',
                                  'HITMONTOP': '<LV>20 Atk = Def'})
        self.assertTrue(any(t[1].startswith('Trade') for t in texts))
        self.assertEqual([method[1] for _, method in graph['EEVEE']
                          if method[0] == 'EVOLVE_HAPPINESS'], ['TR_MORNDAY', 'TR_EVENITE'])

    def test_level_marker_uses_the_dedicated_battle_glyph(self):
        tile = (ROOT / 'gfx/font/font_battle_extra.2bpp').read_bytes()[14 * 16:15 * 16]
        expected = bytes(tile[y] | tile[y + 1] for y in range(0, 16, 2))
        self.assertEqual(self.compiler.glyph('<LV>'), expected)
        self.assertNotEqual(expected, self.compiler.glyph('L'))
        pixels = self.compiler.text('<LV>20 Atk < Def', 5)
        self.assertEqual(len(pixels[0]), 14 * 8)
        for y, glyph in enumerate(expected):
            self.assertEqual(pixels[y][5:13],
                             [0 if glyph & (128 >> x) else 2 for x in range(8)])

    def test_shifted_titles_share_only_identical_unused_font_cells(self):
        resident = {}
        for text, title in self.data['titles'].items():
            pixels = self.compiler.text(text, 5)
            expected = [pack([row[x:x + 8] for row in pixels])
                        for x in range(0, len(pixels[0]), 8)]
            self.assertEqual(title['tiles'], expected)
            self.assertEqual(tuple(title['cells']), TITLE_CELLS[text])
            for cell, tile in zip(title['cells'], title['tiles']):
                self.assertFalse(any(self.compiler.font[(cell - 128) * 8:(cell - 127) * 8]))
                if cell in resident:
                    self.assertEqual(resident[cell], tile)
                resident[cell] = tile
        self.assertEqual(len(resident), 16)
        self.assertEqual(self.data['titles']['Stats']['cells'][-1],
                         self.data['titles']['Evolutions']['cells'][-1])

    def test_every_species_fits_the_double_buffered_atlas(self):
        data = self.data
        self.assertEqual(len(data['names']), 373)
        for name in data['names']:
            with self.subTest(species=name):
                used = set(data['shared'])
                used.update(t for stat in data['stats'][name] for t in data['numbers'][stat])
                self.assertLessEqual(len(used), 40)
                records = data['roots'][name]
                self.assertLessEqual(1 + (len(records) + 1) // 2, 4)
                for first in range(0, len(records), 2):
                    used = {t for i in records[first:first + 2]
                            for line in data['records'][i][1] for t in data['lines'][line][1]}
                    self.assertLessEqual(len(used), 40)

    def test_bar_segments_come_from_the_editable_source_sheet(self):
        compiler = self.compiler
        for i, terminal in enumerate((1, 3, 5, 7, 8)):
            source = compiler.bars[8 if terminal == 8 else 4 + terminal // 2]
            expected = [r[:] if terminal == 8 else r[1:terminal + 1] + [3] * (8 - terminal)
                        for r in source]
            self.assertEqual(compiler.pool[self.data['shared'][10 + i]], pack(expected))

    def test_packed_glyphs_round_trip_and_numbers_keep_the_prefix(self):
        for tile in self.compiler.pool:
            self.assertEqual(pack(unpack(tile)), tile)
        for value in range(256):
            final = unpack(self.compiler.pool[self.data['numbers'][value][3]])
            for y in range(8):
                source = self.compiler.bars[0 if width(value) == 2 else 9][y]
                for x in range(min(3, width(value))):
                    self.assertEqual(final[y][5 + x], source[x])


@unittest.skipUnless((ROOT / 'pokecrystal.gbc').exists(), 'linked production ROM required')
class InfoLinkedTests(unittest.TestCase):
    def test_committed_records_copy_all_six_slices_without_touching_active_page(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for inactive in (0, 1):
            with self.subTest(inactive_atlas=inactive):
                cpu = machine(repo)
                cpu.write(0xff70, 3)
                cpu.field('wPokedexInfoAtlasBuffer', inactive)
                cpu.field('wPokedexInfoActiveAtlasBuffer', 1 - inactive)
                cpu.field('wPokedexInfoVisible', 1)
                cpu.field('wPokedexInfoTileCount', 39)
                tilemap = bytes((i * 7) & 255 for i in range(224))
                sources = bytes((i * 3) & 255 for i in range(80))
                cpu.block(repo.symbols['wPokedexOwnerTilemapBuffer'][1] + 9 * 32, tilemap)
                cpu.block(repo.symbols['wPokedexInfoTileSources'][1], sources)
                record = repo.symbols['wPokedexInfoReturnRecord' + 'AB'[inactive]][1]
                active = repo.symbols['wPokedexInfoReturnRecord' + 'AB'[1 - inactive]][1]
                cpu.block(active, b'\x5a' * 305)
                cpu.run('PokedexInfo_BeginRecord')
                for step in range(6):
                    cpu.run('PokedexInfo_Step')
                    self.assertEqual(cpu.read(repo.symbols['wPokedexInfoState'][1]), 5 if step == 5 else 8)
                    self.assertEqual(cpu.data(active, 305), b'\x5a' * 305)
                    self.assertEqual(cpu.read(repo.symbols['wPokedexInfoActiveAtlasBuffer'][1]), 1 - inactive)
                    self.assertEqual(cpu.read(repo.symbols['wPokedexInfoVisible'][1]), 1)
                self.assertEqual(cpu.data(record, 305), tilemap + sources + bytes((39,)))

    def test_cancel_preserves_actually_visible_record_and_restores_wram_bank(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        cpu = machine(repo)
        cpu.field('wPokedexInfoState', 8)
        cpu.field('wPokedexOwnerTransition', 5)
        cpu.field('wPokedexInfoVisible', 1)
        cpu.field('wPokedexInfoActiveAtlasBuffer', 1)
        cpu.write(0xff70, 3)
        record = repo.symbols['wPokedexInfoReturnRecordB'][1]
        cpu.block(record, b'\x5a' * 305)
        cpu.write(0xff70, 1)
        cpu.run('PokedexInfo_Cancel')
        self.assertEqual(cpu.ram[0xff70], 1)
        self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), 0)
        cpu.write(0xff70, 3)
        self.assertEqual(cpu.read(repo.symbols['wPokedexInfoState'][1]), 0)
        self.assertEqual(cpu.read(repo.symbols['wPokedexInfoVisible'][1]), 1)
        self.assertEqual(cpu.read(repo.symbols['wPokedexInfoActiveAtlasBuffer'][1]), 1)
        self.assertEqual(cpu.data(record, 305), b'\x5a' * 305)

    def test_visible_info_ownership_changes_only_at_publication(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for state, view, visible in ((5, 1, 1), (8, 1, 0), (5, 0, 0)):
            with self.subTest(state=state, view=view):
                cpu = machine(repo)
                cpu.write(0xff70, 3)
                cpu.field('wPokedexInfoState', state)
                cpu.field('wPokedexSelectedView', view)
                cpu.field('wPokedexInfoVisible', 1 - visible)
                cpu.run('Pokedex_VBlankInfoAssets')
                self.assertEqual(cpu.read(repo.symbols['wPokedexInfoVisible'][1]), visible)

    def test_uncaught_info_return_keeps_its_new_blank_publication(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        cpu = machine(repo)
        cpu.field('wPokedexInfoCaught', 0)
        cpu.field('wPokedexInfoPage', 1)
        cpu.field('wPokedexSelectedView', 1)
        cpu.field('wPokedexSelectedSpecies', 1)
        cpu.field('wPokemonIndexTableEntries', 152, 2)
        cpu.field('wPokedexOwnerTransition', 4)
        cpu.write(0xff70, 1)
        cpu.write(repo.symbols['hVBlank'][1], 0x80)
        cpu.run('PokedexSelectedMon_ToggleDescriptionPage')
        self.assertEqual(cpu.read(repo.symbols['wPokedexSelectedView'][1]), 0)
        self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), 4)
        self.assertEqual(cpu.read(repo.symbols['hVBlank'][1]), 0x87)
        self.assertEqual(cpu.ram[0xff70], 1)
        base = repo.symbols['wPokedexOwnerTilemapBuffer'][1] - 0xd000
        self.assertEqual(cpu.wram[3][base + 8 * 32 + 2], 0x79)
        self.assertEqual(cpu.wram[3][base + 9 * 32 + 2], 0x7a)

    def test_description_restore_rearms_publication_without_losing_quiet_mode(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        cpu = machine(repo)
        cpu.field('wPokedexOwnerTransition', 4)
        cpu.write(repo.symbols['hVBlank'][1], 0x80)
        cpu.run('PokedexSelectedMon_ServiceDescriptionText')
        self.assertEqual(cpu.read(repo.symbols['hVBlank'][1]), 0x87)
        self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), 4)

    def test_description_restore_clears_info_gutter_and_publishes_uncaught_badge(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for caught in (0, 1):
            with self.subTest(caught=caught):
                cpu = machine(repo)
                cpu.field('wPokedexInfoCaught', caught)
                cpu.field('wPokedexInfoPage', 3)
                cpu.field('wPokedexSelectedView', 1)
                base = repo.symbols['wPokedexOwnerTilemapBuffer'][1]
                cpu.write(0xff70, 3)
                for row in range(10, 15):
                    cpu.write(base + row * 32 + 1, 0x42)
                cpu.write(repo.symbols['hVBlank'][1], 0x80)
                cpu.run('PokedexInfo_ReturnDescription')
                self.assertEqual(cpu.read(repo.symbols['wPokedexSelectedView'][1]), 0)
                for row in range(10, 15):
                    self.assertEqual(cpu.read(base + row * 32 + 1), 0x32)
                if not caught:
                    self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), 4)
                    self.assertEqual(cpu.read(repo.symbols['hVBlank'][1]), 0x87)
                    self.assertEqual(cpu.read(base + 8 * 32 + 2), 0x79)
                    self.assertEqual(cpu.read(base + 9 * 32 + 2), 0x7a)

    def test_ready_handoff_obeys_the_active_playback_budget(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for line, expected in ((63, 5), (64, 0)):
            with self.subTest(line=line):
                cpu = machine(repo)
                cpu.field('wPokedexSelectedView', 1)
                cpu.field('wPokedexInfoState', 5)
                cpu.field('wPokedexAnimPlaybackState', 2)
                cpu.write(0xff44, line)
                cpu.run('PokedexInfo_Service')
                self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), expected)

    def test_stats_slice_cpu_cost_is_bounded_for_all_values(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for row in range(6):
            for value in range(256):
                cpu = machine(repo)
                cpu.write(0xff70, 3)
                cpu.field('wPokedexInfoState', 2)
                cpu.field('wPokedexInfoCaught', 1)
                cpu.field('wPokedexInfoRow', row)
                cpu.field('wPokedexInfoTileCount', 15 + row * 4)
                cpu.field('wPokedexInfoStats', value << (row * 8), 6)
                cpu.run('PokedexInfo_Step')
                self.assertLessEqual(cpu.cycles, 14000, (row, value))

    def test_atlas_avoids_portrait_slots_and_icon_buffers(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        start = offset(repo.symbols['PokedexInfoAtlasCells'])
        cells = repo.rom[start:start + 80]
        expected = list(range(0xfa, 0x100)) + list(range(0x28, 0x32)) + list(range(0x78, 0x80)) + list(range(0x64, 0x6c)) + list(range(0x70, 0x78))
        self.assertEqual(list(cells[::2]), expected)
        self.assertEqual(list(cells[1::2]), [8] * 40)
        self.assertFalse(set(expected) & set(range(0x33, 0x64)))
        self.assertFalse(set(expected) & set(range(0xb1, 0xb5)))
        self.assertLessEqual(repo.symbols['wPokedexInfoWorkspaceEnd'][1], 0xe000)

    def test_lower_publication_cannot_reprogram_a_waiting_portrait_upload(self):
        repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        for label, owner in (('Pokedex_VBlankInfo', 5), ('Pokedex_VBlankDescriptionText', 4)):
            with self.subTest(publisher=label):
                cpu = machine(repo)
                cpu.allowed_io.update((0xff4f, 0xff70))
                cpu.field('wPokedexSelectedView', 1)
                cpu.field('wPokedexSelectedState', 1)
                cpu.field('wPokedexOwnerTransition', owner)
                cpu.field('wPokedexAnimSchedulerControl', 4)
                cpu.record_writes = True
                cpu.run(label)
                self.assertEqual(cpu.read(repo.symbols['wPokedexOwnerTransition'][1]), owner)
                self.assertFalse(any(0xff51 <= at <= 0xff55 for _, at, _ in cpu.writes))

        start = offset(repo.symbols['Pokedex_ServiceAnimationUploadChunk.transfer'])
        end = offset(repo.symbols['Pokedex_ServiceAnimationUploadChunk.copy_lcd_off'])
        field = repo.symbols['wPokedexAnimSchedulerControl'][1].to_bytes(2, 'little')
        claim = b'\xfa' + field + b'\xf6\x04\xea' + field
        release = b'\x21' + field + b'\xcb\x96'
        body = repo.rom[start:end]
        self.assertTrue(body.startswith(claim))
        self.assertIn(release, body)


if __name__ == '__main__':
    unittest.main()
