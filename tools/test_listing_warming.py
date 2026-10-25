"""Scope and resource contracts for the private no-warming link."""
import json
import os
from pathlib import Path
import re
import unittest

from dex_timing.assets import read_symbols, sha256


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / os.environ.get('DEX_NO_WARMING_BUILD', 'build/dex-no-warming-20261011')


class ListingWarmingTests(unittest.TestCase):
    def test_only_four_assembly_owners_changed(self):
        baseline = OUTPUT / 'baseline/candidate'
        candidate = OUTPUT / 'candidate'
        changed = [str(path.relative_to(candidate)) for path in candidate.rglob('*.asm')
                   if path.read_bytes() != (baseline / path.relative_to(candidate)).read_bytes()]
        self.assertEqual(sorted(changed), sorted(('engine/pokedex/pokedex.asm',
            'engine/pokedex/pokedex_legacy.asm', 'engine/pokedex/pokedex_animation.asm',
            'engine/pokedex/pokedex_popover.asm')))

    def test_listing_has_no_producer_or_startup_calls(self):
        for name in ('pokedex.asm', 'pokedex_legacy.asm', 'pokedex_popover.asm'):
            source = (OUTPUT / 'candidate/engine/pokedex' / name).read_text()
            self.assertNotIn('farcall Pokedex_ServiceAnimationProducer', source)
            self.assertNotIn('farcall Pokedex_StartAnimationPrefetch', source)
        source = (OUTPUT / 'candidate/engine/pokedex/pokedex_animation.asm').read_text()
        prefix = source.split('Pokedex_CancelAnimationPrefetch:', 1)[0]
        self.assertNotIn('call Pokedex_StartAnimationPrefetch', prefix)

    def test_selected_startup_and_playback_are_unchanged(self):
        for name in ('engine/pokedex/pokedex_detail.asm', 'engine/gfx/load_pics.asm',
                     'engine/pokedex/pokedex_animation_policy.asm'):
            self.assertEqual((OUTPUT / 'candidate' / name).read_bytes(),
                             (OUTPUT / 'baseline/candidate' / name).read_bytes())
        name = 'engine/pokedex/pokedex_animation.asm'
        before = (OUTPUT / 'baseline/candidate' / name).read_text()
        after = (OUTPUT / 'candidate' / name).read_text()
        self.assertEqual(after.split('Pokedex_CancelAnimationPrefetch:', 1)[1],
                         before.split('Pokedex_CancelAnimationPrefetch:', 1)[1])

    def test_existing_memory_locations_are_preserved(self):
        before = read_symbols(OUTPUT / 'baseline/pokecrystal-dex-no-warming.sym')
        after = read_symbols(OUTPUT / 'pokecrystal-dex-no-warming.sym')
        for name, pair in before.items():
            if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in after:
                self.assertEqual(pair, after[name], name)

    def test_exact_resource_reduction(self):
        def resources(path):
            return {name: int(value) for name, value in re.findall(
                r'^\s*(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used',
                path.read_text(), re.M)}
        before = resources(OUTPUT / 'baseline/pokecrystal-dex-no-warming.map')
        after = resources(OUTPUT / 'pokecrystal-dex-no-warming.map')
        self.assertEqual({name: after[name] - before[name] for name in before},
                         {'ROM0': 0, 'ROMX': -58, 'SRAM': 0, 'WRAM0': 0, 'WRAMX': 0, 'HRAM': 0})

    def test_production_and_review_batteries_are_unchanged(self):
        manifest = json.loads((OUTPUT / 'no-warming-manifest.json').read_text())
        promoted = ROOT / 'build/dex-production-integration-20261011/integration.json'
        overrides = {}
        if promoted.exists():
            integration = json.loads(promoted.read_text())
            if sha256((ROOT / 'pokecrystal.gbc').read_bytes()) == integration['rom_sha256']:
                self.assertFalse(integration['issues'])
                self.assertTrue(integration['byte_identical_to_accepted_rom'])
                review = Path(integration['qualification']).parent
                qualification = json.loads(Path(integration['qualification']).read_text())
                self.assertFalse(qualification['issues'])
                self.assertEqual(qualification['rom_sha256'], integration['rom_sha256'])
                for name in integration['changed_sources']:
                    overrides[str(ROOT / name)] = sha256((review / 'candidate' / name).read_bytes())
                for suffix in ('gbc', 'sym', 'map'):
                    overrides[str(ROOT / f'pokecrystal.{suffix}')] = sha256(
                        (review / f'pokecrystal-dex-unown-fix.{suffix}').read_bytes())
        for path, expected in manifest['protected_inputs'].items():
            if Path(path).relative_to(ROOT).as_posix() in (
                'docs/index.md', 'docs/pokedex_selected_bug_backlog.md'
            ):
                continue
            self.assertEqual(sha256(Path(path).read_bytes()), overrides.get(path, expected), path)
        self.assertEqual((OUTPUT / 'pokecrystal-dex-no-warming.sav').read_bytes(),
                         (OUTPUT / 'baseline/pokecrystal-dex-no-warming.sav').read_bytes())


if __name__ == '__main__':
    unittest.main()
