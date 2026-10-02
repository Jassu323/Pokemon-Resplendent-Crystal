"""Isolation and analysis contracts for the host-only DEX-DESC-01 probe."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dex_timing.assets import Repository, offset, sha256
from dex_timing.cold_listing import ROOT
from dex_timing.cpu import CounterCPU
from dex_timing.description_text_regression import compare_controls
from dex_timing.description_paging import (
    caught_fixture, description_pages, isolation_rom, picture_hash, run_to, summarize_trace, validate_starts,
)


class DescriptionPagingTests(unittest.TestCase):
    def test_fixture_refuses_to_replace_the_source(self):
        source = Path('/private/tmp/description-paging-source.sav')
        with self.assertRaisesRegex(ValueError, 'must not replace'):
            caught_fixture(None, source, source)

    def fixture_repo(self, root):
        order = root / 'data/pokemon/dex_order_new.asm'
        order.parent.mkdir(parents=True)
        order.write_text('dw CHIKORITA\ndw BAYLEEF\ndw MEGANIUM\n')
        symbols = {f'{prefix}{name}': (bank, address)
            for prefix, bank in (('s', 0), ('sBackup', 1))
            for name, address in (('SaveData', 0xa000), ('SaveDataEnd', 0xa100),
                                  ('Checksum', 0xa100), ('PokemonData', 0xa020))}
        symbols.update(wPokemonData=(1, 0xd000), wPokedexCaught=(1, 0xd008),
                       wEndPokedexCaught=(1, 0xd00a))
        return SimpleNamespace(root=root, symbols=symbols)

    def test_fixture_changes_only_caught_flags_and_both_checksums(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / 'source.sav', root / 'fixture.sav'
            original = bytearray(0x8040)
            original[0x8000:] = bytes(range(64))
            for bank in (0, 1):
                at = bank * 8192
                original[at + 0x2a] = 0x55
                original[at + 0x100:at + 0x102] = bytes((0x55, 0))
            source.write_bytes(original)
            provenance = caught_fixture(self.fixture_repo(root), source, target)
            changed = target.read_bytes()
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(changed[0x8000:], original[0x8000:])
            for bank in (0, 1):
                at = bank * 8192
                self.assertEqual(changed[at + 0x28:at + 0x2a], b'\x07\x00')
                self.assertEqual(changed[at + 0x2a], 0x55)
                self.assertEqual(sum(changed[at:at + 0x100]) & 65535,
                    int.from_bytes(changed[at + 0x100:at + 0x102], 'little'))
            self.assertTrue(provenance['caught_only'])
            self.assertTrue(provenance['rtc_unchanged'])

    def test_fixture_rejects_a_bad_source_checksum(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sav'
            data = bytearray(0x8040)
            data[1] = 1
            source.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'checksum invalid'):
                caught_fixture(self.fixture_repo(root), source, root / 'fixture.sav')
            self.assertFalse((root / 'fixture.sav').exists())

    def isolation_repo(self):
        data = bytearray(0x8000)
        data[0x4000:0x4003] = b'\xcd\x67\x45'
        data[0x400b:0x4011] = b'\x3e\x02\x21\x78\x56\xcf'
        return SimpleNamespace(rom=bytes(data), symbols={
            'PokedexSelectedMon_ToggleDescriptionPage': (1, 0x4000),
            'PokedexSelectedMon_ChangeSpecies': (1, 0x4020),
            'Pokedex_ReleaseQuietAnimationOwner': (1, 0x4567),
            'Pokedex_CopyBackingToBG': (2, 0x5678)})

    def test_counterfactuals_patch_only_the_verified_calls_and_checksum(self):
        with TemporaryDirectory() as directory:
            repo = self.isolation_repo()
            before = repo.rom
            target = Path(directory) / 'diagnostic.gbc'
            report = isolation_rom(repo, target, 'keep-owner-skip-copy')
            patched = target.read_bytes()
            allowed = set(range(0x4000, 0x4003)) | set(range(0x400b, 0x4011)) | {0x14e, 0x14f}
            changes = {i for i, (a, b) in enumerate(zip(before, patched)) if a != b}
            self.assertLessEqual(changes, allowed)
            self.assertEqual(repo.rom, before)
            self.assertEqual(len(report['patches']), 2)
            self.assertEqual(int.from_bytes(patched[0x14e:0x150], 'big'),
                             (sum(patched[:0x14e]) + sum(patched[0x150:])) & 65535)

    def test_unmodified_variant_does_not_rewrite_the_rom(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / 'diagnostic.gbc'
            report = isolation_rom(self.isolation_repo(), target, 'original')
            self.assertEqual(report['patches'], [])
            self.assertEqual(report['original_rom_sha256'], report['diagnostic_rom_sha256'])
            self.assertFalse(target.exists())

    def test_counterfactual_rejects_an_unexpected_call_site(self):
        repo = self.isolation_repo()
        repo.rom = bytes(len(repo.rom))
        with self.assertRaisesRegex(ValueError, 'call changed'):
            isolation_rom(repo, Path('/private/tmp/unused-desc.gbc'), 'keep-owner')

    def trace(self):
        picture = bytes(49 * 16)
        palette = [0xabcdef, 0x112233, 0x334455, 0x778899]
        valid = picture_hash(picture, palette)
        return picture, [dict(event='frame', display=i, picture=picture.hex(),
            portrait_rgb=palette, portrait_hash=valid if i > 1 else 0,
            header_hash=100 if i > 1 else 99) for i in range(1, 5)]

    def analyze(self, trace, picture):
        with patch('dex_timing.description_paging.expected_picture', return_value=picture):
            return summarize_trace(trace, SimpleNamespace(plans=[None]))

    def test_load_framebuffer_artifacts_are_not_reported_as_corruption(self):
        picture, trace = self.trace()
        report = self.analyze(trace, picture)
        self.assertEqual(report['invalid_rendered_portrait_frames'], [])
        self.assertEqual(report['changed_header_frames'], [])
        self.assertTrue(report['rendered_checks_available'])

    def test_post_load_corruption_is_detected_in_pixels_and_tile_data(self):
        picture, trace = self.trace()
        trace[2].update(portrait_hash=0, header_hash=200, picture=bytes([1] * len(picture)).hex())
        report = self.analyze(trace, picture)
        self.assertEqual(report['invalid_rendered_portrait_frames'], [3])
        self.assertEqual(report['invalid_vram_portrait_frames'], [3])
        self.assertEqual(report['changed_header_frames'], [3])

    def test_audio_interval_is_measured_independently_of_cache_empty(self):
        picture, trace = self.trace()
        trace += [dict(event='audio_tick', t=t) for t in (10, 12810, 98066)]
        self.assertEqual(self.analyze(trace, picture)['longest_audio_block_interval'], 85256)

    def test_reused_checkpoints_require_matching_rom_and_symbols(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            rom, symbols = b'test cartridge', b'test symbols'
            (root / 'pokecrystal-desc-diagnostic.gbc').write_bytes(rom)
            (root / 'pokecrystal-desc-diagnostic.sym').write_bytes(symbols)
            (root / 'provenance.json').write_text(json.dumps(dict(
                rom_sha256=sha256(rom), sym_sha256=sha256(symbols))))
            isolation = dict(original_rom_sha256=sha256(rom))
            validate_starts(root, isolation, sha256(symbols))
            with self.assertRaisesRegex(ValueError, 'do not match'):
                validate_starts(root, isolation, 'wrong symbols')
            (root / 'pokecrystal-desc-diagnostic.gbc').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'do not match'):
                validate_starts(root, isolation, sha256(symbols))

    def test_missing_input_checkpoint_fails_instead_of_silently_continuing(self):
        repo = SimpleNamespace(symbols={'toggle': (1, 0x4567)})
        driver = SimpleNamespace(command=lambda _: dict(pc=0x1234, bank=0))
        with self.assertRaisesRegex(RuntimeError, 'Checkpoint timed out'):
            run_to(driver, repo, 'toggle')

    def test_matched_control_comparison_checks_deadlines_and_content(self):
        with TemporaryDirectory() as directory:
            changed, control = Path(directory) / 'changed', Path(directory) / 'control'
            changed.mkdir()
            control.mkdir()
            (changed / 'report.json').write_text(json.dumps([
                dict(species='test', offset=0, physical_pages=[0, 1])]))
            events = [dict(event='publish', tick=7, frame=2, map='00', picture='00'),
                      dict(event='audio_stop', t=100, remaining=0)]
            for path in (changed, control):
                (path / 'test-0-audit.json').write_text(json.dumps(events))
            self.assertTrue(compare_controls(changed, control)[0]['exact_publication_deadlines'])
            for field, value in (('tick', 8), ('picture', 'ff')):
                altered = [dict(events[0], **{field: value}), events[1]]
                (control / 'test-0-audit.json').write_text(json.dumps(altered))
                self.assertFalse(compare_controls(changed, control)[0]['exact_publication_deadlines'])


@unittest.skipUnless((ROOT / 'pokecrystal.gbc').exists(), 'current linked ROM required')
class LinkedDescriptionTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
        if 'PokedexSelectedMon_ServiceDescriptionText' not in cls.repo.symbols:
            raise unittest.SkipTest('rebuild the queued Description renderer')
        import re
        names = re.findall(r'^\s*const\s+(\w+)',
                           (ROOT / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
        aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
        cls.names = [aliases.get(n, n.lower()) for n in names]

    def cpu(self, index, page):
        repo = self.repo
        cpu = CounterCPU(repo.rom, repo.symbols)
        cpu.ram[0xff70] = 3
        cpu.allowed_io.add(0xff44)
        cpu.field('hCGB', 1)
        cpu.field('wPokemonIndexTableEntries', index + 1, 2)
        cpu.field('wPokedexSelectedSpecies', 1)
        cpu.field('wPokedexDescriptionPage', page)
        cpu.field('wPokedexDescriptionTextState', 1)
        cpu.field('wPokedexAnimPlaybackState', 2)
        start = offset(repo.symbols['PokedexDescriptionTilemap'])
        shell = repo.rom[start:start + 360]
        cpu.block(repo.symbols['wTilemap'][1], shell)
        padded = b''.join(shell[y * 20:(y + 1) * 20] + bytes([0x32] * 12) for y in range(18))
        cpu.block(repo.symbols['wPokedexOwnerTilemapBuffer'][1], padded)
        cpu.block(repo.symbols['wPokedexOwnerAttrmapBuffer'][1], bytes([0x09] * 576))
        return cpu

    def lower(self, cpu, padded=False):
        base = self.repo.symbols['wPokedexOwnerTilemapBuffer' if padded else 'wTilemap'][1]
        stride = 32 if padded else 20
        return b''.join(cpu.data(base + y * stride, 20) for y in range(8, 15))

    def test_all_species_both_pages_match_the_independent_renderer(self):
        maximum = 0
        slowest = None
        for index, name in enumerate(self.names):
            for page, expected in enumerate(description_pages(self.repo, name)):
                with self.subTest(species=name, page=page):
                    cpu = self.cpu(index, page)
                    main = self.repo.symbols['wTilemap'][1]
                    owner = self.repo.symbols['wPokedexOwnerTilemapBuffer'][1]
                    upper, footer = cpu.data(main, 160), cpu.data(main + 300, 60)
                    owner_upper, owner_footer = cpu.data(owner, 256), cpu.data(owner + 480, 96)
                    cycles = cpu.run('PokedexSelectedMon_InitializeDescriptionText')
                    if cycles > maximum:
                        maximum, slowest = cycles, (name, page, 'initialize')
                    for _ in range(32):
                        cycles = cpu.run('PokedexSelectedMon_RenderDescriptionTextChunk')
                        if cycles > maximum:
                            maximum, slowest = cycles, (name, page, 'chunk')
                        if cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]) == 4:
                            break
                    else:
                        self.fail(f'Text renderer did not finish: {name}')
                    self.assertEqual(self.lower(cpu), expected)
                    self.assertEqual(self.lower(cpu, True), expected)
                    self.assertEqual(cpu.data(main, 160), upper)
                    self.assertEqual(cpu.data(main + 300, 60), footer)
                    self.assertEqual(cpu.data(owner, 256), owner_upper)
                    self.assertEqual(cpu.data(owner + 480, 96), owner_footer)
                    self.assertEqual(cpu.data(self.repo.symbols['wPokedexOwnerAttrmapBuffer'][1], 576),
                                     bytes([0x09] * 576))
        self.assertLessEqual(maximum, 6144)
        print(f'Description text: largest isolated slice {maximum} T ({slowest}); limit 6144 T')

    def test_active_late_slice_defers_but_completed_animation_does_not_starve(self):
        cpu = self.cpu(self.names.index('dusknoir'), 1)
        cpu.ram[0xff44] = 130
        cpu.run('PokedexSelectedMon_ServiceDescriptionText')
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexDescriptionTextState'][1]), 1)
        cpu.field('wPokedexAnimPlaybackState', 3)
        cpu.run('PokedexSelectedMon_ServiceDescriptionText')
        self.assertNotEqual(cpu.read(self.repo.symbols['wPokedexDescriptionTextState'][1]), 1)

    def test_request_is_immutable_and_cancellation_preserves_unrelated_handoffs(self):
        cpu = self.cpu(self.names.index('mewtwo'), 1)
        cpu.field('wPokedexOwnerTransition', 4)
        before = bytes(cpu.wram[3])
        cpu.run('PokedexSelectedMon_ServiceDescriptionText')
        self.assertEqual(bytes(cpu.wram[3]), before)
        cpu.run('PokedexSelectedMon_CancelDescriptionText')
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]), 0)
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexDescriptionTextState'][1]), 0)
        cpu.field('wPokedexOwnerTransition', 2)
        cpu.run('PokedexSelectedMon_CancelDescriptionText')
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]), 2)

    def test_text_publication_window_priority_and_bank_restore(self):
        for ly in (0, 96, 143, 144, 145, 147, 148, 153):
            for portrait_pending in (False, True):
                cpu = self.cpu(0, 1)
                cpu.allowed_io.update(range(0xff51, 0xff56))
                cpu.ram[0xff44] = ly
                cpu.ram[0xff70] = 6
                cpu.ram[0xff4f] = 1
                cpu.field('wPokedexOwnerTransition', 4)
                cpu.field('wPokedexAnimFlags', 0x23 if portrait_pending else 3)
                cpu.field('hVBlank', 0x87)
                cpu.record_writes = True
                cycles = cpu.run('Pokedex_VBlankDescriptionText')
                accepted = 144 <= ly < 148
                self.assertEqual(cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]), 0 if accepted else 4)
                self.assertEqual(cpu.ram[0xff70], 6)
                self.assertEqual(cpu.ram[0xff4f], 1)
                dmas = [value for _, address, value in cpu.writes if address == 0xff55]
                self.assertEqual(dmas, [13] if accepted else [])
                if accepted:
                    self.assertEqual(cpu.read(self.repo.symbols['hVBlank'][1]), 0x87 if portrait_pending else 0x80)
                    self.assertLess(cycles + 14 * 32 + 4, (154 - 147) * 456 - 455)
                self.assertFalse(any(address in (0xff68, 0xff69, 0xff6a, 0xff6b) for _, address, _ in cpu.writes))

    def test_competing_map_or_dma_defers_text_publication(self):
        for competing in ('hBGMapUpdate', 'hDMATransfer'):
            cpu = self.cpu(0, 1)
            cpu.ram[0xff44] = 144
            cpu.field('wPokedexOwnerTransition', 4)
            cpu.field(competing, 1)
            cpu.run('Pokedex_VBlankDescriptionText')
            self.assertEqual(cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]), 4)

    def test_uncaught_toggle_keeps_the_existing_blank_page_contract(self):
        cpu = self.cpu(0, 0)
        main = self.repo.symbols['wTilemap'][1]
        before = cpu.data(main, 360)
        owner_before = bytes(cpu.wram[3])
        cpu.ram[0xff70] = 1
        cpu.run('PokedexSelectedMon_ToggleDescriptionPage')
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexDescriptionPage'][1]), 1)
        self.assertEqual(cpu.read(self.repo.symbols['wPokedexOwnerTransition'][1]), 0)
        self.assertEqual(cpu.data(main, 360), before)
        state = self.repo.symbols['wPokedexDescriptionTextState'][1] - 0xd000
        self.assertEqual(cpu.wram[3][state], 0)
        self.assertEqual(bytes(cpu.wram[3][:state]), owner_before[:state])


if __name__ == '__main__':
    unittest.main()
