import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from dex_timing.assets import Repository, offset, sha256
from dex_timing.cold_listing import ROOT
from dex_timing.costs import machine, run_to
from dex_timing.moves_mode import description, shifted_glyph, sort_right_gfx, sort_border_gfx, font_glyph
from pokedex_moves_mode_assets import compile_tables, TYPES


class MovesModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / os.environ.get('DEX_MOVES_MODE_BUILD', 'build/dex-moves-mode-20261007b')
        cls.repo = Repository(ROOT, cls.output / 'pokecrystal-dex-moves-mode.gbc',
                              cls.output / 'pokecrystal-dex-moves-mode.sym')
        cls.tables, cls.manifest = compile_tables(cls.output / 'candidate')

    def test_both_orders_cover_each_permanent_identity_once(self):
        expected = list(range(1, len(self.manifest['moves']) + 1))
        for order in self.manifest['orders']:
            self.assertEqual(sorted(order), expected)

    def test_types_are_alphabetical_and_keep_gameplay_type_ids(self):
        self.assertEqual(list(TYPES), sorted(TYPES))
        self.assertEqual(TYPES[0], 'BUG')
        self.assertEqual(TYPES[-1], 'WATER')
        order = [self.manifest['moves'][i - 1] for i in self.manifest['orders'][0]]
        self.assertEqual([TYPES.index(m['type']) for m in order],
                         sorted(TYPES.index(m['type']) for m in order))

    def test_names_are_alphabetical_within_each_type_and_across_all_moves(self):
        import re
        key = lambda move: (re.sub(r'[^a-z0-9]', '', move['name'].lower()), move['index'])
        moves = self.manifest['moves']
        for type_ in TYPES:
            actual = [i for i in self.manifest['orders'][0] if moves[i - 1]['type'] == type_]
            self.assertEqual(actual, [m['index'] for m in sorted(
                (m for m in moves if m['type'] == type_), key=key)])
        self.assertEqual(self.manifest['orders'][1], [m['index'] for m in sorted(moves, key=key)])

    def test_compiled_order_words_match_generated_tables_including_extended_ids(self):
        for label, expected in zip(('PokedexMovesModeTypeOrder', 'PokedexMovesModeNameOrder'),
                                   self.manifest['orders']):
            at = offset(self.repo.symbols[label])
            words = [int.from_bytes(self.repo.rom[at + i * 2:at + i * 2 + 2], 'little')
                     for i in range(len(expected) + 1)]
            self.assertEqual(words, expected + [0])
            self.assertTrue(any(i > 255 for i in words))
        self.assertEqual(self.manifest['sort_bytes'], 1336)

    def test_existing_names_and_descriptions_fit_bounded_panels(self):
        for move in self.manifest['moves']:
            self.assertLessEqual(len(move['name']), 12)
            lines = description(self.repo, move['index'])
            self.assertLessEqual(len(lines), 6, move['symbol'])
            self.assertTrue(all(len(line) <= 19 for line in lines), move['symbol'])

    def test_move_symbols_are_not_inferred_from_record_comments(self):
        psychic = next(m for m in self.manifest['moves'] if m['name'] == 'Psychic')
        self.assertEqual(psychic['symbol'], 'PSYCHIC_M')

    def test_save_layout_and_production_outputs_are_untouched(self):
        manifest = json.loads((self.output / 'moves-mode-manifest.json').read_text())
        source = Path(manifest['source']) / 'candidate'
        if manifest.get('persistence_stage') in (1, 2, 3):
            from dex_timing.assets import read_symbols
            old = read_symbols(Path(manifest['source']) / 'pokecrystal-dex-moves-mode.sym')
            for name, pair in old.items():
                if name.startswith(('s', 'w')) and pair[1] >= 0xa000 and name in self.repo.symbols:
                    self.assertEqual(self.repo.symbols[name], pair, name)
            for path, expected in manifest['protected_inputs'].items():
                self.assertEqual(sha256(Path(path).read_bytes()), expected)
            self.assertEqual((self.output / 'candidate/ram/hram.asm').read_bytes(),
                             (source / 'ram/hram.asm').read_bytes())
            return
        for name in ('ram/sram.asm', 'ram/wram.asm', 'ram/hram.asm'):
            self.assertEqual((self.output / 'candidate' / name).read_bytes(),
                             (source / name).read_bytes())
        for suffix, expected in manifest['production_hashes'].items():
            self.assertEqual(sha256((ROOT / f'pokecrystal.{suffix}').read_bytes()), expected)
        self.assertEqual((self.output / 'pokecrystal-dex-moves-mode.sav').read_bytes(),
                         (Path(manifest['source']) / 'pokecrystal-dex-search.sav').read_bytes())

    def test_renderer_has_no_persistent_discovery_or_save_writes(self):
        source = (ROOT / 'tools/dex_timing/probes/pokedex_moves_mode.asm').read_text()
        for forbidden in ('OpenSRAM', 'CloseSRAM', 'sMove', 'SaveGame'):
            self.assertNotIn(forbidden, source)
        self.assertIn('IF DEF(DEX_MOVES_MODE_UNKNOWN)', source)
        self.assertIn('DEF wMovesModeSort       EQUS "wPokedexInfoGFX"', source)
        if 'wMoveDiscoverySeen' in self.repo.symbols:
            candidate = (self.output / 'candidate/engine/pokedex/pokedex_moves_mode.asm').read_text()
            self.assertIn('call PokedexMovesMode_SnapshotSeen', candidate)
            self.assertIn('ld de, wMovesModeSeenSnapshot', candidate)
            self.assertNotIn('farcall MoveDiscovery_CheckIndex', candidate)
            for forbidden in ('OpenSRAM', 'SaveGame', 'MoveDiscovery_MarkIndex'):
                self.assertNotIn(forbidden, candidate)

    def test_page_jumps_keep_cursor_and_clamp_every_scroll_position(self):
        cpu = machine(self.repo)
        cpu.write(0xff70, 3)
        start = self.repo.symbols['wPokedexInfoGFX'][1]
        last_page = len(self.manifest['moves']) - 8
        for scroll in range(last_page + 1):
            for label, step in (('PokedexMovesMode_PageLeft', -8), ('PokedexMovesMode_PageRight', 8)):
                with self.subTest(scroll=scroll, label=label):
                    cpu.block(start, b'\x01\x07' + scroll.to_bytes(2, 'little') + b'\xaa\xbb')
                    cpu.run(label)
                    expected = max(0, min(last_page, scroll + step))
                    self.assertEqual(cpu.data(start, 6), b'\x01\x07' + expected.to_bytes(2, 'little') + b'\xaa\xbb')
                    self.assertEqual(bool(cpu.f & cpu.C), expected != scroll)

    def sort_font_machine(self):
        cpu = machine(self.repo)
        cpu.write(0xff70, 3)
        at = offset(self.repo.symbols['Font'])
        cpu.block(0xdc00, self.repo.rom[at:at + 1024])
        cpu.block(self.repo.symbols['wPokedexInfoGFX'][1] + 40, bytes(8))
        return cpu

    def test_every_font_glyph_shifts_without_changing_the_font(self):
        if 'PokedexMovesMode_ShiftGlyph' not in self.repo.symbols:
            self.skipTest('Tile-aligned popup uses the native font directly')
        cpu = self.sort_font_machine()
        destination = self.repo.symbols['wPokedexInfoGFX'][1] + 48
        for code in range(0x80, 0x100):
            for previous in (0x7f, 0x80, 0xed, 0xff):
                cpu.r[7], cpu.r[0], cpu.r[1] = code, previous, 0xab
                cpu.set_pair(1, destination)
                cpu.run('PokedexMovesMode_ShiftGlyph')
                self.assertEqual(cpu.data(destination, 16), shifted_glyph(self.repo, code, previous))
                self.assertEqual((cpu.r[0], cpu.r[1]), (previous, 0xab))
                self.assertEqual(cpu.pair(1), destination + 16)

    def test_partial_right_border_preserves_the_underlying_glyph_pixels(self):
        if 'PokedexMovesMode_PrepareSortRightEdge' not in self.repo.symbols:
            self.skipTest('Popup no longer uses per-open right-edge packing')
        cpu = self.sort_font_machine()
        start = self.repo.symbols['wTilemap'][1]
        destination = self.repo.symbols['wPokedexInfoGFX'][1] + 48
        for code in range(0x7f, 0x100):
            cpu.sp = 0xc0f0
            chars = bytes((code,)) * 5
            for row in range(3, 8):
                cpu.block(start + row * 20 + 19, bytes((code,)))
            run_to(cpu, 'PokedexMovesMode_PrepareSortRightEdge', 'PokedexMovesMode_UploadSortRightEdge')
            self.assertEqual(cpu.data(destination, 80), b''.join(sort_right_gfx(self.repo, chars)))

    def test_shifted_border_preserves_the_scrollbar_and_uncovered_left_pixel(self):
        if 'PokedexMovesMode_ShiftSortBorder' not in self.repo.symbols:
            self.skipTest('Earlier popup alignment')
        cpu = self.sort_font_machine()
        destination = self.repo.symbols['wPokedexInfoGFX'][1] + 48
        run_to(cpu, 'PokedexMovesMode_LoadSortBorder', 'PokedexMovesMode_UploadSortBorder')
        self.assertEqual(cpu.data(destination, 144), b''.join(sort_border_gfx(self.repo)))
        self.assertTrue(all(not (row & 128) for row in font_glyph(self.repo, 0xed)))
        self.assertEqual(font_glyph(self.repo, 0x32), bytes(8))

    def test_tile_aligned_border_uses_the_original_eight_tiles_unchanged(self):
        if 'PokedexMovesMode_PrepareSortText' in self.repo.symbols:
            self.skipTest('Earlier sub-tile popup alignment')
        cpu = machine(self.repo)
        cpu.write(0xff70, 3)
        destination = self.repo.symbols['wPokedexInfoGFX'][1] + 48
        cpu.block(destination, b'\xaa' * 144)
        run_to(cpu, 'PokedexMovesMode_LoadSortBorder', 'PokedexMovesMode_UploadSortBorder')
        self.assertEqual(cpu.data(destination, 144), b''.join(sort_border_gfx(self.repo)) + b'\xaa' * 16)

    def test_short_presses_survive_redraws_without_repeating_or_overriding_auto_input(self):
        if 'PokedexMovesMode_ReadInput' not in self.repo.symbols:
            self.skipTest('Earlier unlatched input owner')
        cpu = machine(self.repo)
        cpu.field('wInputType', 0)
        cpu.field('hInMenu', 1)
        cpu.field('hJoypadSum', 0x20)
        cpu.field('hJoypadDown', 0)
        cpu.field('hJoyDown', 0)
        cpu.field('hJoyPressed', 0)
        cpu.field('hJoyLast', 0x40)
        cpu.field('wTextDelayFrames', 7)
        cpu.run('PokedexMovesMode_ReadInput')
        for field, value in (('hJoypadSum', 0), ('hJoyDown', 0), ('hJoyPressed', 0x20),
                             ('hJoyLast', 0x20), ('wTextDelayFrames', 15)):
            self.assertEqual(cpu.read(self.repo.symbols[field][1]), value, field)
        cpu.field('hJoypadSum', 0x80)
        cpu.field('hJoypadDown', 0x80)
        cpu.field('hJoyDown', 0)
        cpu.field('hJoyPressed', 0)
        cpu.run('PokedexMovesMode_ReadInput')
        self.assertEqual(cpu.read(self.repo.symbols['hJoyDown'][1]), 0x80)
        cpu.run('JoyTextDelay')
        cpu.run('PokedexMovesMode_ReadInput')
        self.assertEqual(cpu.read(self.repo.symbols['hJoyPressed'][1]), 0)
        self.assertEqual(cpu.read(self.repo.symbols['hJoyLast'][1]), 0)
        self.assertIn('DEF AUTO_INPUT EQU $ff', (ROOT / 'constants/ram_constants.asm').read_text())
        cpu.field('wInputType', 0xff)
        cpu.field('hJoypadSum', 0x20)
        cpu.field('hJoyDown', 0x80)
        cpu.run('PokedexMovesMode_ReadInput')
        self.assertEqual(cpu.read(self.repo.symbols['hJoypadSum'][1]), 0x20)
        self.assertEqual(cpu.read(self.repo.symbols['hJoyDown'][1]), 0x80)

    def test_scrollbar_art_matches_the_user_sheet_and_precise_pixel_contract(self):
        if 'PokedexMovesModeScrollbarGFX' not in self.repo.symbols:
            self.skipTest('Accepted pre-scrollbar fixture')
        from PIL import Image
        rows = ['OOOOOOOOOOOOOOOO'] * 5 + ['WWWWOOWWWWWOOOOO'] + ['DDDWOOWDDDWOOOOO'] * 12
        rows += ['WWWWOOWWWWWOOOOO'] + ['OOOOOOOOOOOOOOOO'] * 2
        rows += ['WWWWWWWWWWWWOOOO'] + ['DDDDDDDDDDDWOOOO'] * 2
        colors = {'W': (255, 255, 255, 255), 'O': (170, 170, 170, 255), 'D': (85, 85, 85, 255)}
        path = self.output / 'candidate/gfx/pokedex/pokedex_moves_scroll_bar_and_borders.png'
        with Image.open(path) as image:
            self.assertEqual(image.size, (16, 24))
            image = image.convert('RGBA')
            self.assertEqual([image.getpixel((x, y)) for y in range(24) for x in range(16)],
                             [colors[c] for row in rows for c in row])
        expected = path.with_suffix('.2bpp').read_bytes()
        at = offset(self.repo.symbols['PokedexMovesModeScrollbarGFX'])
        self.assertEqual(len(expected), 96)
        self.assertEqual(self.repo.rom[at:at + 96], expected)

    def test_scrollbar_scales_every_16_bit_scroll_offset_without_changing_state(self):
        if 'PokedexMovesMode_DrawScrollbar' not in self.repo.symbols:
            self.skipTest('Accepted pre-scrollbar fixture')
        cpu = machine(self.repo)
        cpu.write(0xff70, 3)
        start = self.repo.symbols['wPokedexInfoGFX'][1]
        oam = self.repo.symbols['wShadowOAM'][1]
        maximum = len(self.manifest['moves']) - 8
        for scroll in range(maximum + 1):
            before = b'\x01\x07' + scroll.to_bytes(2, 'little') + b'\xaa' * 14
            cpu.block(start, before)
            cpu.block(oam, b'\xbb' * 160)
            cpu.run('PokedexMovesMode_DrawScrollbar')
            y = 20 + (scroll * 65 + maximum // 2) // maximum
            self.assertEqual(cpu.data(start, 18), before)
            self.assertEqual(cpu.data(oam, 160), b'\xbb' * 24 + bytes((y, 160, 15, 3)) + b'\xbb' * 132)

    def test_new_moves_names_and_types_regenerate_both_orders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ('constants/move_constants.asm', 'data/moves/names.asm', 'data/moves/moves.asm'):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / path, target)
            path = root / 'constants/move_constants.asm'
            path.write_text(path.read_text().replace('DEF NUM_ATTACKS',
                            '\tconst MOVES_MODE_TEST\nDEF NUM_ATTACKS', 1))
            path = root / 'data/moves/names.asm'
            path.write_text(path.read_text().replace('\tassert_list_length',
                            '\tli "AAA Test"\n\tassert_list_length', 1))
            path = root / 'data/moves/moves.asm'
            path.write_text(path.read_text().replace('.IndirectEnd::',
                            '\tmove EFFECT_NORMAL_HIT, 50, BUG, 100, 10, 0 ; TEST\n.IndirectEnd::', 1))
            _, manifest = compile_tables(root)
            self.assertEqual(manifest['orders'][0][0], 334)
            self.assertEqual(manifest['orders'][1][0], 334)
            self.assertEqual(manifest['sort_bytes'], 1340)
            path.write_text(path.read_text().replace('50, BUG, 100', '50, WATER, 100'))
            _, manifest = compile_tables(root)
            self.assertGreater(manifest['orders'][0].index(334), 0)
            self.assertEqual(manifest['orders'][1][0], 334)
            path.write_text(path.read_text().replace(' ; TEST', ''))
            self.assertEqual(compile_tables(root)[1], manifest)

    def render_text(self, payload):
        cpu = machine(self.repo)
        cpu.write(0xff70, 3)
        cpu.write(self.repo.symbols['wPokedexInfoGFX'][1] + 15, 1)
        cpu.block(0xc800, payload)
        start = self.repo.symbols['wTilemap'][1]
        cpu.block(start, b'\x32' * 360)
        cpu.set_pair(2, 0xc800)
        cpu.run('PokedexMovesMode_DrawDescription')
        return [cpu.data(start + i * 20, 20) for i in range(18)]

    def test_six_full_lines_use_consecutive_rows_and_stay_inside_the_panel(self):
        lines = [bytes((0x80 + i,)) * 19 for i in range(6)]
        for separator in (0x4f, 0x4e, 0x22):
            with self.subTest(separator=separator):
                rows = self.render_text(bytes((separator,)).join(lines) + b'\x50')
                for i, line in enumerate(lines):
                    self.assertEqual(rows[10 + i], b'\x32' + line)
                self.assertTrue(all(row == b'\x32' * 20 for row in rows[:10] + rows[16:]))

    def test_oversized_text_cannot_write_into_borders_or_footer(self):
        for payload in (b'\x80' * 20 + b'\x50', b'\x4f'.join([b'\x80' * 19] * 7) + b'\x50'):
            rows = self.render_text(payload)
            self.assertTrue(all(row[0] == 0x32 for row in rows))
            self.assertTrue(all(row == b'\x32' * 20 for row in rows[:10] + rows[16:]))


if __name__ == '__main__':
    unittest.main()
