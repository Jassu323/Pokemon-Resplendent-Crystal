import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from dex_timing.assets import Repository, offset
from dex_timing.cold_listing import ROOT
from dex_timing.costs import machine
from pokedex_info_assets import species, constants
from pokedex_moves_assets import compile as compile_moves

class MovesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        cls.manifest = json.loads((ROOT / 'build/dex-moves-assets/manifest.json').read_text())

    def read(self, bank, at, length):
        start = offset((bank, at))
        return self.repo.rom[start:start + length]

    def test_index_matches_linked_learnsets_and_actual_machine_bits(self):
        repo = self.repo
        names = species()
        ids = constants(ROOT / 'constants/move_constants.asm')
        at = offset(repo.symbols['PokedexMovesSpecies'])
        split = names.index('HARIYAMA') + 1
        total = 0
        for i, name in enumerate(names):
            with self.subTest(species=name):
                data = self.manifest[name]
                record = repo.rom[at + i*17:at + (i+1)*17]
                self.assertEqual(record[0], max(1, len(data['pages'])))
                self.assertLessEqual(record[0], 19)
                first = offset(repo.symbols['BaseData1' if i < split else 'BaseData2'])
                stats = repo.rom[first + (i if i < split else i - split)*32:first + (i if i < split else i - split)*32 + 32]
                flags = int.from_bytes(stats[24:32], 'little')
                eligible = [[n+1 for n in range(57) if flags & (1 << n)],
                            [n+1 for n in range(3) if flags & (1 << (n+57))]]
                for kind in range(4):
                    count, bank, lo, hi = record[1 + kind*4:5 + kind*4]
                    address = lo | hi << 8
                    rows = data['streams'][kind]
                    self.assertEqual(count, len(rows))
                    if kind == 0:
                        actual = self.read(bank, address, count*3 + 1)
                        self.assertEqual(actual, b''.join(bytes((level,)) + ids[move].to_bytes(2, 'little') for level, move in rows) + b'\0')
                    elif kind == 3:
                        self.assertEqual((bank, address), repo.symbols[data['egg_pointer']])
                        self.assertEqual(self.read(bank, address, count*2 + 2),
                                         b''.join(ids[move].to_bytes(2, 'little') for _, move in rows) + b'\xff\xff')
                    else:
                        self.assertEqual(list(self.read(bank, address, count)), eligible[kind - 1])
                total += len(data['pages'])
        self.assertEqual(total, 2576)

    def test_every_badge_from_1_through_19_preserves_the_visible_buffer(self):
        repo = self.repo
        for active in (0, 1):
            for page in range(1, 20):
                with self.subTest(active=active, page=page):
                    cpu = machine(repo)
                    cpu.write(0xff70, 3)
                    cpu.field('wPokedexBadgeActive', active)
                    cpu.vram[0][:] = bytes([0x5a]) * 8192
                    cpu.r[1] = page
                    cycles = cpu.run('PokedexBadge_Prepare')
                    pending = 1 - active
                    upper, lower = (0x73, 0x78) if pending == 0 else (0x79, 0x7a)
                    source = 'PokedexBadgeSingleGFX' if page < 10 else 'PokedexBadgeDoubleGFX'
                    column = page if page < 10 else (1 if page == 10 else page - 8)
                    at = offset(repo.symbols[source]) + column*32
                    self.assertEqual(bytes(cpu.vram[0][0x1000+upper*16:0x1010+upper*16]), repo.rom[at:at+16])
                    self.assertEqual(bytes(cpu.vram[0][0x1000+lower*16:0x1010+lower*16]), repo.rom[at+16:at+32])
                    for tile in ((0x73, 0x78) if active == 0 else (0x79, 0x7a)):
                        self.assertEqual(bytes(cpu.vram[0][0x1000+tile*16:0x1010+tile*16]), bytes([0x5a])*16)
                    self.assertEqual(cpu.wram[3][repo.symbols['wPokedexBadgeActive'][1] & 4095], active)
                    self.assertLessEqual(cycles, 6144)

    def test_workspace_uses_existing_overlay_and_no_premium_ram(self):
        repo = self.repo
        self.assertEqual(repo.symbols['wPokedexMovesState'][0], 3)
        self.assertLessEqual(repo.symbols['wPokedexInfoWorkspaceEnd'][1], 0xdc00)
        self.assertEqual(repo.symbols['wPokedexInfoWorkspaceEnd'][1] - repo.symbols['wPokedexMovesState'][1], 45)

    def test_deferred_evolution_links_are_not_invented(self):
        for name in ('WEAVILE', 'LEAFEON', 'GLACEON'):
            self.assertEqual(self.manifest[name]['streams'][3], [])
            self.assertEqual(self.manifest[name]['egg_source'], name)

    def test_existing_chains_branches_and_babies_share_egg_sources(self):
        families = {
            'CHIKORITA': ('CHIKORITA', 'BAYLEEF', 'MEGANIUM'),
            'EEVEE': ('EEVEE', 'VAPOREON', 'JOLTEON', 'FLAREON', 'ESPEON', 'UMBREON'),
            'PICHU': ('PICHU', 'PIKACHU', 'RAICHU'),
            'TYROGUE': ('TYROGUE', 'HITMONLEE', 'HITMONCHAN', 'HITMONTOP'),
        }
        for source, members in families.items():
            for name in members:
                with self.subTest(species=name):
                    self.assertEqual(self.manifest[name]['egg_source'], source)
                    self.assertEqual(self.manifest[name]['streams'][3], self.manifest[source]['streams'][3])
                    self.assertEqual(self.manifest[name]['egg_pointer'], self.manifest[source]['egg_pointer'])
        for name in ('CATERPIE', 'METAPOD', 'BUTTERFREE'):
            self.assertEqual(self.manifest[name]['streams'][3], [])

    def test_indexes_regenerate_after_learnset_and_compatibility_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for directory in ('constants', 'data/pokemon', 'data/moves', 'gfx/font'):
                shutil.copytree(ROOT / directory, root / directory)
            before = compile_moves(root)
            source = root / 'data/pokemon/evos_attacks_johto.asm'
            text = source.read_text()
            start = text.index('ChikoritaEvosAttacks:')
            end = text.index('BayleefEvosAttacks:', start)
            block = re.sub(r'^(\s*db 0[^\n]*\n)', r'\1\tdbw 99, LEEK_SLAP\n', text[start:end], count=1, flags=re.M)
            source.write_text(text[:start] + block + text[end:])
            source = root / 'data/pokemon/base_stats/chikorita.asm'
            source.write_text(re.sub(r'^\s*tmhm[^\n]*', '\ttmhm FLAMETHROWER', source.read_text(), flags=re.M))
            source = root / 'data/pokemon/egg_moves_johto.asm'
            source.write_text(source.read_text().replace('ChikoritaEggMoves:\n', 'ChikoritaEggMoves:\n\tdw LEEK_SLAP\n', 1))
            after = compile_moves(root)
            self.assertEqual(after['CHIKORITA']['streams'][0], [(99, 'LEEK_SLAP')] + before['CHIKORITA']['streams'][0])
            self.assertEqual(after['CHIKORITA']['machines'], [])
            self.assertEqual(after['CHIKORITA']['streams'][2], [(1, 'FLAMETHROWER')])
            self.assertEqual(after['CHIKORITA']['streams'][3], [(0, 'LEEK_SLAP')] + before['CHIKORITA']['streams'][3])
            for name in ('BAYLEEF', 'MEGANIUM'):
                self.assertEqual(after[name]['streams'][3], after['CHIKORITA']['streams'][3])
            source = root / 'data/pokemon/evos_attacks_johto.asm'
            source.write_text(source.read_text().replace('\tdbw 99, LEEK_SLAP\n', '\tdbw 99, LEEK_SLAP\n' * 100, 1))
            with self.assertRaisesRegex(ValueError, r'CHIKORITA needs .* Moves pages; limit is 19'):
                compile_moves(root)

    def test_new_species_and_new_family_link_regenerate_without_a_dex_index_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for directory in ('constants', 'data/pokemon', 'data/moves', 'gfx/font'):
                shutil.copytree(ROOT / directory, root / directory)
            source = root / 'constants/pokemon_constants.asm'
            source.write_text(source.read_text().replace('DEF NUM_POKEMON EQU', '\tconst DEX_TEST\nDEF NUM_POKEMON EQU', 1))
            source = root / 'data/pokemon/evos_attacks_custom.asm'
            source.write_text(source.read_text().replace('\n.IndirectEnd\n', '\n\tdw DexTestEvosAttacks\n.IndirectEnd\n', 1) +
                              '\nDexTestEvosAttacks:\n\tdb 0\n\tdbw 1, TACKLE\n\tdb 0\n')
            source = root / 'data/pokemon/egg_moves_custom.asm'
            source.write_text(source.read_text().replace('\n.IndirectEnd::\n', '\n\tdw NoEggMoves3 ; DEX_TEST\n.IndirectEnd::\n', 1))
            shutil.copyfile(root / 'data/pokemon/base_stats/chikorita.asm', root / 'data/pokemon/base_stats/dex_test.asm')
            data = compile_moves(root)
            self.assertEqual(len(data), len(self.manifest) + 1)
            self.assertEqual(data['DEX_TEST']['streams'][0], [(1, 'TACKLE')])
            self.assertEqual(data['DEX_TEST']['streams'][3], [])
            source = root / 'data/pokemon/evos_attacks_johto.asm'
            source.write_text(source.read_text().replace('MeganiumEvosAttacks:\n',
                              'MeganiumEvosAttacks:\n\tdbbw EVOLVE_LEVEL, 50, DEX_TEST\n', 1))
            data = compile_moves(root)
            self.assertEqual(data['DEX_TEST']['egg_source'], 'CHIKORITA')
            self.assertEqual(data['DEX_TEST']['streams'][3], data['CHIKORITA']['streams'][3])
            self.assertEqual(data['DEX_TEST']['egg_pointer'], 'ChikoritaEggMoves')

    def test_conflicting_family_lists_fail_but_identical_lists_share_one_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for directory in ('constants', 'data/pokemon', 'data/moves', 'gfx/font'):
                shutil.copytree(ROOT / directory, root / directory)
            source = root / 'data/pokemon/egg_moves_johto.asm'
            text = source.read_text().replace('\tdw ChikoritaEggMoves\n\tdw NoEggMoves2\n',
                                             '\tdw ChikoritaEggMoves\n\tdw BayleefEggMoves\n', 1)
            self.assertIn('\tdw BayleefEggMoves\n', text)
            source.write_text(text + '\nBayleefEggMoves:\n\tdw LEEK_SLAP\n\tdw -1\n')
            with self.assertRaisesRegex(ValueError, 'Conflicting egg-move lists.*CHIKORITA.*BAYLEEF.*MEGANIUM'):
                compile_moves(root)
            rows = ''.join(f'\tdw {move}\n' for _, move in self.manifest['CHIKORITA']['streams'][3])
            source.write_text(text + '\nBayleefEggMoves:\n' + rows + '\tdw -1\n')
            data = compile_moves(root)
            self.assertEqual(data['BAYLEEF']['egg_pointer'], 'ChikoritaEggMoves')
            self.assertEqual(data['MEGANIUM']['streams'][3],
                             [tuple(row) for row in self.manifest['CHIKORITA']['streams'][3]])

if __name__ == '__main__':
    unittest.main()
