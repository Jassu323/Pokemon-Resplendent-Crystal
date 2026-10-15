"""Run the standard/supplementary campaign on the shared Moves bookmark link."""
import argparse
import json
from pathlib import Path
import shutil

from .cold_listing import ROOT
from . import dex_cleanup_campaign as campaign

BASE = ROOT / 'build/dex-moves-position-20261014'


def prepare():
    campaign.BASE = BASE
    campaign.prepare()


def repair_timing():
    folder = BASE / 'runtime-regression'
    retry = json.loads((folder / 'timing-fixture-retry.json').read_text())
    assert retry['exit_code'] == 0
    path = folder / 'campaign-logs/timing.json'
    record = json.loads(path.read_text())
    assert record['results'][0]['command'][0] == 'acquisition_performance'
    assert record['results'][0]['exit_code'] == 1
    assert all(row['exit_code'] == 0 for row in record['results'][1:])
    fresh = json.loads((folder / 'acquisition-performance.json').read_text())
    manifest = json.loads((BASE / 'position-manifest.json').read_text())
    assert fresh['rom_sha256'] == manifest['candidate_sha256'] and not fresh['issues']
    initial = path.with_name('timing-initial-fixture-order-failure.json')
    assert not initial.exists()
    shutil.copy2(path, initial)
    prior = dict(record['results'][0])
    record['results'][0].update(exit_code=0, log=retry['log'], previous_attempts=[prior],
                                seconds=None, retry_cause=retry['cause'])
    record['issues'] = []
    path.write_text(json.dumps(record, indent=2) + '\n')
    phases_path = folder / 'phase-results.json'
    phases = json.loads(phases_path.read_text())
    phase = next(row for row in phases if row['phase'] == 'timing')
    assert phase['exit_code'] == 1
    phase.update(previous_attempts=[dict(phase)], exit_code=0,
                 retry_evidence=str(folder / 'timing-fixture-retry.json'),
                 note='Only failed timing subcommand repeated after missing fixture became available; other completed subcommands retained')
    phases_path.write_text(json.dumps(phases, indent=2) + '\n')
    print('Timing retry accepted; original failure and every completed subcommand retained', flush=True)


def new_entry_boundary_union():
    from .assets import Repository, sha256
    from .new_entry_sweep import run_case, A, B
    rows = []
    for variant in ('baseline', 'candidate'):
        config = json.loads((BASE / f'smoke/{variant}/config.json').read_text())
        source = BASE / ('baseline-source' if variant == 'baseline' else 'candidate')
        repo = Repository(source, Path(config['rom']), source / 'pokecrystal.sym')
        assets = repo.load(['groudon'])
        target = BASE / 'new-entry-boundary-union' / variant
        target.mkdir(parents=True, exist_ok=False)
        config['output'] = str(target)
        for key, label in ((A, 'a'), (B, 'b')):
            case = dict(name=f'startup-{label}-048', family='startup', windows=[(0, 48, 2, key)])
            result = run_case((config, assets[0], case))
            assert result['status'] == 'pass' and not result['errors'], result
            rows.append(dict(variant=variant, rom_sha256=sha256(repo.rom), **result))
    record = dict(cases=len(rows), failures=0, rows=rows,
                  reason='Fresh production and candidate Groudon startup is 48 intervals, versus 49 in the prior campaign; retain both historical boundary inputs explicitly')
    (BASE / 'new-entry-boundary-union.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), failures=0)), flush=True)


def finalize():
    from .assets import sha256
    from .type_mode7_campaign import PHASES
    data = json.loads((BASE / 'position-manifest.json').read_text())
    phases = json.loads((BASE / 'runtime-regression/phase-results.json').read_text())
    assert {row['phase'] for row in phases} == set(PHASES) | {'arrows', 'report'}
    assert all(row['exit_code'] == 0 for row in phases), phases
    standard = json.loads((BASE / 'runtime-regression/full-regression.json').read_text())
    assert standard['merge_ready'] and not standard['issues'], standard['issues']
    assert standard['rom_sha256'] == data['candidate_sha256']
    assert standard['baseline_sha256'] == data['baseline_sha256']
    for path, digest in data['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    for name in ('helpers', 'ui', 'saves', 'timing', 'save-edges', 'owners', 'search-edges'):
        result = json.loads((BASE / 'position-tests' / (name + '.json')).read_text())
        assert not result.get('issues') and not result.get('failures'), (name, result)
    expected = {
        'runtime/focused/info-all-double-speed/summary.json': 746,
        'runtime/focused/moves-all-double-speed/summary.json': 746,
        'runtime/focused/info-stress/summary.json': 400,
        'runtime/feature-timing/summary.json': 1056,
        'runtime/return-pixels/summary.json': 115,
        'runtime/all-species-moves-position/summary.json': 1492,
        'runtime/timing-moves-position/summary.json': 128,
        'runtime/moves-returns/summary.json': 128,
        'runtime/visibility-moves-position/summary.json': 128,
        'description-models/summary.json': 1536,
        'all-species/summary.json': 746,
        'visual/summary.json': 60,
        'sweep/summary.json': 8270,
        'lifecycle/summary.json': 336,
        'lifecycle/routes.json': 36,
        'lifecycle/exit-matrix/summary.json': 88,
        'runtime/unown-decoder/summary.json': 156,
    }
    for path, count in expected.items():
        record = json.loads((BASE / path).read_text())
        assert record['cases'] == count and record['failures'] == 0, path
    boundary = json.loads((BASE / 'new-entry-boundary-union.json').read_text())
    assert boundary['cases'] == 4 and not boundary['failures']
    assert {(row['variant'], row['case']) for row in boundary['rows']} == {
        (variant, case) for variant in ('baseline', 'candidate') for case in ('startup-a-048', 'startup-b-048')}
    from .new_entry_sweep import cases
    sweep = json.loads((BASE / 'sweep/summary.json').read_text())['results']
    generated = {(row['species'], case['name']) for row in sweep if row['family'] == 'baseline'
                 for case in cases(row['authored_intervals'], row['first_publication'])}
    actual = {(row['species'], row['case']) for row in sweep}
    assert len(actual) == len(sweep) and actual == generated
    previous = json.loads((ROOT / 'build/dex-unown-transition-regression-20261014/sweep/summary.json').read_text())['results']
    retained = actual | {(row['species'], row['case']) for row in boundary['rows'] if row['variant'] == 'candidate'}
    assert retained == {(row['species'], row['case']) for row in previous}
    active = json.loads((BASE / 'runtime/all-species-moves-position/summary.json').read_text())
    assert all(row.get('complete_visible') and row['complete_visible']['frames'] <= 8 for row in active['rows'])
    for model in ('0', 'A', 'B', 'C', 'D', 'E'):
        record = json.loads((BASE / f'runtime/unown-model-{model}/summary.json').read_text())
        assert record['cases'] == 112 and record['rom_sha256'] == data['candidate_sha256']
        assert record['game_files_unchanged'] and record['donor_unchanged']
        assert all(all(row[key] for key in ('letter_restored', 'return_position', 'return_presentation',
                       'battery_unchanged')) for row in record['checks'])
    for path in ('lifecycle/audio.json', 'lifecycle/audio-registers.json'):
        record = json.loads((BASE / path).read_text())
        assert record['cases'] == 12 and not record['mismatches'], path
    for path in ('returns-summary.json', 'nicknames-summary.json'):
        record = json.loads((BASE / path).read_text())
        assert record['cases'] == 4 and all(not row['issues'] for row in record['results']), path
    capture_returns = json.loads((BASE / 'returns-summary.json').read_text())['results']
    prior_audio = {row['scenario']: row.get('playback_misses', []) for row in capture_returns
                   if row['variant'] == 'baseline'}
    assert all(row.get('playback_misses', []) == prior_audio[row['scenario']]
               for row in capture_returns if row['variant'] == 'candidate')
    lifecycle = json.loads((BASE / 'lifecycle/summary.json').read_text())
    assert not lifecycle['completed_screen_issues'] and not lifecycle['nonwhite_before_fade_issues']
    contracts = json.loads((BASE / 'additional-contracts.json').read_text())
    assert len(contracts) == 2 and all(row['tests'] == 22 and not any(
        row[key] for key in ('failures', 'errors', 'skipped')) for row in contracts)
    from .assets import read_symbols
    old, new = read_symbols(BASE / 'rollback/pokecrystal.sym'), read_symbols(BASE / 'candidate/pokecrystal.sym')
    assert all(new.get(name) == pair for name, pair in old.items() if pair[1] >= 0xa000)
    changed = [str(path.relative_to(BASE / 'baseline-source')) for path in
               (BASE / 'baseline-source').rglob('*.asm') if path.read_bytes() !=
               (BASE / 'candidate' / path.relative_to(BASE / 'baseline-source')).read_bytes()]
    assert set(changed) == {'engine/pokedex/pokedex_moves_mode.asm', 'ram/wram.asm'}, changed
    data['changed_assembly_owners_verified'] = changed
    data['supplementary_checked'] = expected
    data.update(full_regression_passed=True, production_integrated=False,
                status='Qualified private prototype; manual review pending', standard_phases=phases)
    (BASE / 'position-manifest.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({k: data[k] for k in ('status', 'delta', 'candidate_sha256')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'standard', 'report', 'animations', 'selected',
        'displays', 'registration', 'lifecycle', 'lifecycle_audit', 'routes', 'exit_matrix',
        'audio', 'audio_registers', 'repair_timing', 'new_entry_boundary_union', 'finalize'))
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    campaign.BASE = BASE
    if args.action in ('prepare', 'repair_timing', 'new_entry_boundary_union', 'finalize'):
        globals()[args.action]()
    elif args.action in ('standard', 'report'):
        raise SystemExit(campaign.standard(['report'] if args.action == 'report' else args.phases))
    else:
        campaign.extras(args.action)
