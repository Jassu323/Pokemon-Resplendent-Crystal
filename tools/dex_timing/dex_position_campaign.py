"""Full qualification of the private Pokemon/Moves session bookmark link."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import unittest

from .cold_listing import ROOT
from .assets import sha256
from . import dex_cleanup_campaign as campaign

BASE = ROOT / 'build/dex-position-memory-20261014'


def write(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2) + '\n')


def moves_focus():
    from . import moves_position as moves
    from . import moves_position_session as session
    moves.BASE = BASE
    for action in ('prepare', 'helpers', 'ui', 'owners', 'search_edges'):
        getattr(moves, action)()
    session.BASE = BASE
    session.run(publish=False, previous=ROOT / 'build/dex-moves-position-session-20261014/candidate')


def description(jobs):
    from . import description_latency as latency
    latency.BASE = BASE
    latency.RUN_TAG = 'position-memory'
    for action in ('test', 'moves', 'visibility'):
        assert getattr(latency, action)('runtime', jobs) == 0
    assert latency.test('runtime', jobs, all_species=True) == 0
    record = json.loads((BASE / 'runtime/all-species-position-memory/summary.json').read_text())
    violations = [row for row in record['rows'] if not row.get('complete_visible') or row['complete_visible']['frames'] > 8]
    assert record['cases'] == 1492 and not record['failures'] and not violations
    write('description-response-budget.json', dict(cases=1492, failures=0,
        maximum_frames=max(row['complete_visible']['frames'] for row in record['rows']),
        limit_frames=8, rom_sha256=json.loads((BASE / 'position-memory-manifest.json').read_text())['candidate_sha256']))


def models(jobs):
    from . import description_latency_integration
    description_latency_integration.BASE = BASE
    description_latency_integration.models(jobs)


def contracts():
    from . import unown_transition_campaign
    unown_transition_campaign.BASE = BASE
    unown_transition_campaign.contracts()


def bookmark_contracts():
    suite = unittest.defaultTestLoader.loadTestsFromName('tools.test_dex_position')
    with (BASE / 'bookmark-contracts.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    record = dict(cases=result.testsRun, failures=len(result.failures),
                  errors=len(result.errors), skipped=len(result.skipped))
    write('bookmark-contracts.json', record)
    assert result.wasSuccessful() and not result.skipped, record
    print(json.dumps(record, indent=2))


def review():
    from .assets import Repository
    from .cold_listing import Driver, bootstrap
    from .info_ui import BOOT
    from .pokemon_position import audit, listing
    from .moves_mode import enter, state, capture
    from .listing_options import memory
    data = json.loads((BASE / 'position-memory-manifest.json').read_text())
    assert data['full_regression_passed'] and data['review_files']
    folder = BASE / 'review-validation'
    folder.mkdir(exist_ok=False)
    stem = BASE / 'review/pokecrystal-dex-position-memory'
    repo = Repository(BASE / 'candidate', stem.with_suffix('.gbc'), stem.with_suffix('.sym'))
    cfg = json.loads((BASE / 'pokemon-position-tests/config.json').read_text())
    battery = stem.with_suffix('.sav')
    before = sha256(battery.read_bytes())
    driver = Driver(cfg['core'], repo.rom_path, BOOT, battery, folder / 'boot.log')
    try:
        bootstrap(driver)
        pokemon = listing(driver)
        assert pokemon['index'] == 0
        audit(driver, repo)
        assert memory(driver, 1, repo.symbols['wMovesDexBookmarkTag'][1], 8) == bytes(8)
        bitmap = memory(driver, *repo.symbols['wMoveDiscoverySeen'], 64)
        assert sum(value.bit_count() for value in bitmap) == 333
        capture(driver, folder / 'pokemon-cold.png')
        enter(driver, repo)
        moves = state(driver, repo)
        assert moves['sort'] == 1 and moves['scroll'] == moves['cursor'] == 0
        capture(driver, folder / 'moves-cold.png')
    finally:
        driver.close()
    assert sha256(battery.read_bytes()) == before
    record = dict(cases=2, pokemon=pokemon, moves=moves, all_moves_seen=333,
                  review_save_unchanged=True, rom_sha256=sha256(repo.rom), issues=[])
    write('review-validation/results.json', record)
    data['review_validation'] = record
    write('position-memory-manifest.json', data)
    print(json.dumps(record, indent=2))


def boundary():
    from . import moves_position_campaign
    moves_position_campaign.BASE = BASE
    moves_position_campaign.new_entry_boundary_union()


def lifecycle_bundle():
    for action in ('lifecycle', 'lifecycle_audit', 'routes', 'exit_matrix', 'audio_registers', 'audio'):
        campaign.extras(action)


def audio_proof():
    target = BASE / 'lifecycle/audio.json'
    rejected = target.with_name('audio-global-assumption-rejection.json')
    if not rejected.exists():
        shutil.copy2(target, rejected)
    rows = []
    for style in (0, 1):
        for order in range(3):
            for direction in ('entry', 'exit'):
                records = {}
                for variant in ('baseline', 'integrated'):
                    path = BASE / 'lifecycle/audio-registers' / variant / variant / f'style-{style}-order-{order}-q0' / f'{direction}-0-events.json.gz'
                    with gzip.open(path, 'rt') as stream:
                        events = json.load(stream)
                    gate = next(e['t'] for e in events if e['event'] == 'perf_phase' and
                        e['name'] == ('cleanup' if direction == 'exit' else 'menu_accept'))
                    sounds = [e for e in events if e['event'] == 'life_sfx']
                    prior = [e for e in sounds if e['t'] <= gate]
                    first = prior[-1] if prior and prior[-1]['mask'] else next(e for e in sounds if e['t'] >= gate and e['mask'])
                    end = next(e['t'] for e in sounds if e['t'] > first['t'] and not e['mask'])
                    writes, costs = [], {}
                    for event in events:
                        if event['event'] == 'perf_cost':
                            costs[event['name']] = costs.get(event['name'], 0) + event['elapsed']
                        if event['event'] != 'life_apu' or not first['t'] <= event['t'] <= end:
                            continue
                        at = event['address']
                        channel = 0 if at <= 0xff14 else 1 if 0xff16 <= at <= 0xff19 else 2 if 0xff1a <= at <= 0xff1e else 3 if 0xff20 <= at <= 0xff23 else None
                        if channel is not None and first['mask'] & (1 << channel):
                            writes.append(event)
                    assert writes
                    records[variant] = dict(signature=[(e['address'], e['value']) for e in writes],
                        relative_times=[e['t'] - writes[0]['t'] for e in writes],
                        onset=writes[0]['t'] - first['t'], tail=end - writes[-1]['t'],
                        flag_duration=end - first['t'], costs=costs)
                before, after = records['baseline'], records['integrated']
                delta = {key: after[key] - before[key] for key in ('onset', 'tail', 'flag_duration')}
                expected_onset = after['costs'].get('fade_to_menu', 0) - before['costs'].get('fade_to_menu', 0) if direction == 'entry' else 0
                expected_tail = after['costs'].get('init_dex', 0) - before['costs'].get('init_dex', 0) if direction == 'entry' else 0
                matched = before['signature'] == after['signature'] and before['relative_times'] == after['relative_times']
                qualified = matched and delta['onset'] == expected_onset and delta['tail'] == expected_tail and delta['flag_duration'] == expected_onset + expected_tail
                rows.append(dict(style=style, order=order, direction=direction,
                    identical_registers_and_relative_hardware_timing=matched,
                    delta_t=delta, expected_onset_t=expected_onset, expected_tail_t=expected_tail,
                    flag_delta_ms=delta['flag_duration'] * 1000 / 4194304,
                    flag_delta_frames=delta['flag_duration'] / 70224, qualified=qualified,
                    records=records))
    record = dict(cases=len(rows), mismatches=sum(not row['qualified'] for row in rows), rows=rows,
        scope='Exact sound-register values and relative physical write times. Entry onset/tail flag deltas must equal the same-case nonoverlapping fade/init procedure deltas, not a global entry median. Exit matches exactly.')
    write('lifecycle/audio-hardware-proof.json', record)
    assert not record['mismatches'], record
    write('lifecycle/audio.json', record)
    print(json.dumps(dict(cases=len(rows), mismatches=record['mismatches'],
        flag_delta_ms=sorted({row['flag_delta_ms'] for row in rows})), indent=2))


def finalize():
    from .type_mode7_campaign import PHASES
    data = json.loads((BASE / 'position-memory-manifest.json').read_text())
    def report(name):
        return json.loads((BASE / name).read_text())
    phases = report('runtime-regression/phase-results.json')
    assert {row['phase'] for row in phases} == set(PHASES) | {'arrows', 'report'}
    assert all(row['exit_code'] == 0 for row in phases), phases
    standard = report('runtime-regression/full-regression.json')
    assert standard['merge_ready'] and not standard['issues']
    assert standard['rom_sha256'] == data['candidate_sha256']
    assert standard['baseline_sha256'] == data['baseline_sha256']
    assert sha256((BASE / 'candidate/pokecrystal.gbc').read_bytes()) == data['candidate_sha256']
    for path, digest in data['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    expected = {
        'pokemon-position-tests/helpers.json': 16176,
        'pokemon-position-tests/ui.json': 48,
        'pokemon-position-tests/integration.json': 6,
        'pokemon-position-tests/lifecycle.json': 13,
        'pokemon-position-tests/sparse.json': 6,
        'pokemon-position-tests/warm-timing.json': 144,
        'bookmark-contracts.json': 11,
        'position-tests/helpers.json': 12641,
        'position-tests/ui.json': 32,
        'position-tests/owners.json': 16,
        'position-tests/search-edges.json': 4,
        'moves-session-validation.json': 4,
        'runtime/focused/info-all-double-speed/summary.json': 746,
        'runtime/focused/moves-all-double-speed/summary.json': 746,
        'runtime/focused/info-stress/summary.json': 400,
        'runtime/feature-timing/summary.json': 1056,
        'runtime/return-pixels/summary.json': 115,
        'runtime/all-species-position-memory/summary.json': 1492,
        'runtime/timing-position-memory/summary.json': 128,
        'runtime/moves-returns/summary.json': 128,
        'runtime/visibility-position-memory/summary.json': 128,
        'description-models/summary.json': 1536,
        'all-species/summary.json': 746,
        'visual/summary.json': 60,
        'sweep/summary.json': 8270,
        'lifecycle/summary.json': 336,
        'lifecycle/routes.json': 36,
        'lifecycle/exit-matrix/summary.json': 88,
        'runtime/unown-decoder/summary.json': 156,
    }
    for name, count in expected.items():
        value = report(name)
        assert value['cases'] == count and not value.get('failures') and not value.get('issues') and not value.get('errors'), name
    for model in ('0', 'A', 'B', 'C', 'D', 'E'):
        value = report(f'runtime/unown-model-{model}/summary.json')
        assert value['cases'] == 112 and value['rom_sha256'] == data['candidate_sha256']
        assert value['game_files_unchanged'] and value['donor_unchanged']
        assert all(all(row[key] for key in ('letter_restored', 'return_position',
            'return_presentation', 'battery_unchanged')) for row in value['checks'])
    for name in ('lifecycle/audio.json', 'lifecycle/audio-registers.json'):
        value = report(name)
        assert value['cases'] == 12 and not value['mismatches'], name
    for name in ('returns-summary.json', 'nicknames-summary.json'):
        value = report(name)
        assert value['cases'] == 4 and all(not row['issues'] for row in value['results'])
    contracts = report('additional-contracts.json')
    assert len(contracts) == 2 and all(row['tests'] == 22 and not any(
        row[key] for key in ('failures', 'errors', 'skipped')) for row in contracts)
    boundary = report('new-entry-boundary-union.json')
    assert boundary['cases'] == 4 and not boundary['failures']
    from .new_entry_sweep import cases
    sweep = report('sweep/summary.json')['results']
    generated = {(row['species'], case['name']) for row in sweep if row['family'] == 'baseline'
        for case in cases(row['authored_intervals'], row['first_publication'])}
    actual = {(row['species'], row['case']) for row in sweep}
    assert len(actual) == len(sweep) and actual == generated
    retained = actual | {(row['species'], row['case']) for row in boundary['rows'] if row['variant'] == 'candidate'}
    prior = json.loads((ROOT / 'build/dex-unown-transition-regression-20261014/sweep/summary.json').read_text())['results']
    assert retained == {(row['species'], row['case']) for row in prior}
    data.update(full_regression_passed=True, production_integrated=False,
                status='Qualified private prototype; manual review pending',
                standard_phases=phases, required_reports=expected)
    write('position-memory-manifest.json', data)
    print(json.dumps({key: data[key] for key in ('status', 'candidate_sha256', 'delta', 'pokemon_delta')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('moves-focus', 'description', 'models', 'contracts',
        'boundary', 'finalize', 'standard', 'report', 'animations', 'selected', 'displays',
        'registration', 'lifecycle', 'lifecycle_audit', 'routes', 'exit_matrix', 'audio', 'audio_registers',
        'lifecycle-bundle', 'audio-proof', 'bookmark-contracts', 'review'))
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    BASE = args.base.resolve()
    campaign.BASE = BASE
    if args.action in ('description', 'models'):
        globals()[args.action](args.jobs)
    elif args.action in ('moves-focus', 'contracts', 'boundary', 'finalize', 'lifecycle-bundle', 'audio-proof', 'bookmark-contracts', 'review'):
        globals()[args.action.replace('-', '_')]()
    elif args.action in ('standard', 'report'):
        raise SystemExit(campaign.standard(['report'] if args.action == 'report' else args.phases))
    else:
        campaign.extras(args.action)
