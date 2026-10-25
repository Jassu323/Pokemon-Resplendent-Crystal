"""Host runner controls for the focused Description latency investigation."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools.dex_timing import backlog_reconciliation as replay
from tools.dex_timing.description_latency import cases
from tools.dex_timing.cold_listing import ROOT
from tools.dex_timing.description_latency_integration import response_violations


class AtomicPortraitContractTests(unittest.TestCase):
    def test_dispatcher_checks_pending_before_full_restore(self):
        text = (ROOT / 'engine/pokedex/pokedex_3.asm').read_text()
        owner = text.split('\n.owner\n\tcall Pokedex_VBlankAnimationFrontpicMap\n', 1)[1]
        owner = owner.split('\n.no_portrait\n', 1)[0]
        self.assertIn('jr z, .description_text', owner)
        self.assertIn('bit POKEDEX_ANIM_MAP_PENDING_F, a\n\tjr z, .description_done', owner)
        self.assertLess(owner.index('bit POKEDEX_ANIM_MAP_PENDING_F, a'),
                        owner.index('call Pokedex_VBlankDescriptionText'))
        self.assertIn('pokedex_info_description_latency_investigation.md#atomic-portrait-contract', owner)

    def test_atomic_publisher_clears_pending_after_both_banks(self):
        text = (ROOT / 'engine/pokedex/pokedex_3.asm').read_text()
        publisher = text.split('\nPokedex_VBlankAnimationFrontpicMap:\n', 1)[1]
        publication, deferred = publisher.split('\n.defer\n', 1)
        self.assertEqual(publication.count('call .TransferRows'), 2)
        self.assertEqual(publication.count('res POKEDEX_ANIM_MAP_PENDING_F, [hl]'), 1)
        self.assertGreater(publication.index('res POKEDEX_ANIM_MAP_PENDING_F, [hl]'),
                           publication.rindex('call .TransferRows'))
        self.assertTrue(deferred.startswith('\tscf\n\tret\n'))


class DescriptionLatencyRunnerTests(unittest.TestCase):
    def test_response_budget_rejects_starvation_and_missing_visible_completion(self):
        fast = dict(complete_visible=dict(frames=5.62))
        delayed = dict(complete_visible=dict(frames=121.18))
        missing = dict(complete_visible=None)
        self.assertEqual(response_violations([fast, delayed, missing]), [delayed, missing])

    def test_targeted_matrix_has_unique_case_keys(self):
        rows = cases(dict(names=['source', 'target']), 'private')
        self.assertEqual(len(rows), 64)
        self.assertEqual(len({row[1:] for row in rows}), 64)
        self.assertIn(('grovyle', 'sceptile', '8', 0, 'private'), [row[1:] for row in rows])

    def test_all_species_matrix_wraps_the_authored_order(self):
        rows = cases(dict(names=['first', 'middle', 'last']), 'private', True)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0][1:5], ('last', 'first', '0', 0))

    def test_incoming_metadata_is_recorded_after_native_paging(self):
        incoming = dict(hit='change_species', selected_index=1, t=100, double_speed=1)
        finished = dict(t=400, playback=3, audio=0, sfx=0)
        driver = Mock()
        driver.events = []
        driver.run.side_effect = lambda points=(), **kw: (
            incoming if 'change_species' in points else
            dict(hit='footer_accept', t=300) if 'footer_accept' in points else dict(t=150))
        def command(text):
            if text == 'peek':
                return dict(selected_index=1, t=250, playback=2)
            if text == 'ui':
                return dict(view=0)
            return dict(t=200 if text == 'perf 1' else 400)
        driver.command.side_effect = command
        with tempfile.TemporaryDirectory() as temporary:
            config = dict(names=['source', 'target'], rom='private.gbc', sym='private.sym',
                          core='private-core', battery='private.sav', listing_style='modern',
                          states=temporary, output=temporary)
            with patch.object(replay, 'Driver', return_value=driver), \
                 patch.object(replay, 'Repository'), \
                 patch.object(replay, 'move'), \
                 patch.object(replay, 'press'), \
                 patch.object(replay, 'settle', return_value=finished), \
                 patch.object(replay, 'settle_description_text'), \
                 patch.object(replay, 'description_pages', return_value=[b'expected']), \
                 patch.object(replay, 'description_audit', return_value=[]), \
                 patch.object(replay.performance, 'view'), \
                 patch.object(replay.performance, 'result_timing', return_value={}):
                result = replay.tab_case((config, 'source', 'target', '8', 0))
            self.assertEqual(result['issues'], [])
            self.assertEqual(result['incoming_accepted'], incoming)
            self.assertTrue((Path(temporary) / 'source-target-age8-q0-modern/report.json').is_file())
            calls = driver.mock_calls
            capture = next(i for i, call in enumerate(calls)
                           if call[0] == 'command' and str(call[1][0]).endswith('/after.ppm'))
            self.assertEqual(calls[capture - 1][0], 'run')
            self.assertEqual(calls[capture - 1][2]['frames'], 2)


if __name__ == '__main__':
    unittest.main()
