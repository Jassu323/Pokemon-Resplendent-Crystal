"""Freeze and fully qualify the private 51-byte Unown transition candidate."""
import argparse
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import unittest

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from . import dex_cleanup_campaign as campaign
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-unown-transition-regression-20261014'
APPROVED = ROOT / 'build/dex-unown-transitions-20261014/staged'
PRODUCTION = '12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d'
CANDIDATE = '942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc'
TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare(jobs):
    assert not BASE.exists(), 'Use a fresh private campaign directory'
    assert sha256((ROOT / 'pokecrystal.gbc').read_bytes()) == PRODUCTION
    assert sha256((APPROVED / 'candidate/pokecrystal.gbc').read_bytes()) == CANDIDATE
    BASE.mkdir(parents=True)
    protected = {str(path): sha256(path.read_bytes()) for path in
                 (ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map')}
    candidate = BASE / 'candidate'
    shutil.copytree(APPROVED / 'candidate', candidate,
        ignore=shutil.ignore_patterns('*.o', '*.d', '__pycache__', '*.pyc'))
    baseline = BASE / 'baseline-source'
    baseline.mkdir()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in tracked:
        source = ROOT / name
        if name and source.is_file():
            target = baseline / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    shutil.copytree(ROOT / 'gfx', baseline / 'gfx', dirs_exist_ok=True)
    for name in TABLES:
        shutil.copytree(ROOT / 'build' / name, baseline / 'build' / name, dirs_exist_ok=True)
    for source in (candidate, baseline):
        shutil.copytree(ROOT / 'tools', source / 'tools', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for label, source, expected in (('baseline', baseline, PRODUCTION),
                                     ('candidate', candidate, CANDIDATE)):
        with (BASE / f'{label}-build.log').open('w') as log:
            subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=source,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        assert sha256((source / 'pokecrystal.gbc').read_bytes()) == expected, label
    delta = {key: value - resources(baseline / 'pokecrystal.map')[key]
             for key, value in resources(candidate / 'pokecrystal.map').items()}
    assert delta == dict(ROM0=0, ROMX=51, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0), delta
    old, new = read_symbols(baseline / 'pokecrystal.sym'), read_symbols(candidate / 'pokecrystal.sym')
    moved = [name for name, pair in old.items() if pair[1] >= 0xa000 and name in new and pair != new[name]]
    assert not moved, moved
    rollback = BASE / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(baseline / f'pokecrystal.{ext}', rollback / f'pokecrystal.{ext}')
    with tarfile.open(BASE / 'rollback-source.tar', 'w') as archive:
        def retained(member):
            return None if member.name.endswith(('.o', '.d', '.pyc')) else member
        for path in baseline.iterdir():
            archive.add(path, arcname=path.name, filter=retained)
    for stem in ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime', 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(candidate / f'pokecrystal.{ext}', BASE / f'{stem}.{ext}')
        shutil.copy2(APPROVED / 'pokecrystal-dex-unown-staged.sav', BASE / f'{stem}.sav')
    shutil.copy2(APPROVED / 'candidate.diff', BASE / 'candidate.diff')
    environment = dict(python=sys.version)
    for name, command in (('rgbasm', ['rgbasm', '--version']), ('clang', ['clang', '--version']),
                          ('sameboy', ['git', '-C', str(Path.home() / 'Documents/GitHub/SameBoy'), 'rev-parse', 'HEAD']),
                          ('source_commit', ['git', 'rev-parse', 'HEAD'])):
        environment[name] = subprocess.check_output(command, cwd=ROOT, text=True).strip()
    manifest = dict(production_sha256=PRODUCTION, candidate_sha256=CANDIDATE,
        approved_candidate_rebuilt_exactly=True, production_rebuilt_exactly=True,
        delta=delta, moved_ram_labels=moved, protected=protected, environment=environment,
        status='Fresh full qualification pending; no production integration authorized')
    write(BASE / 'qualification.json', manifest)
    campaign.BASE = BASE
    campaign.prepare()
    print(json.dumps(manifest, indent=2), flush=True)


def description(jobs):
    from . import description_latency as latency
    latency.BASE = BASE
    latency.RUN_TAG = 'unown-transition'
    for action in ('test', 'moves', 'visibility'):
        if getattr(latency, action)('runtime', jobs):
            raise RuntimeError('Active Description return failed: ' + action)
    if latency.test('runtime', jobs, all_species=True):
        raise RuntimeError('All-species active Description return failed')
    path = BASE / 'runtime/all-species-unown-transition/summary.json'
    record = json.loads(path.read_text())
    missed = [row for row in record['rows'] if not row.get('complete_visible') or row['complete_visible']['frames'] > 8]
    assert record['cases'] == 1492 and not record['failures'] and not missed
    write(BASE / 'description-response-budget.json', dict(cases=record['cases'], failures=0,
        maximum_frames=max(row['complete_visible']['frames'] for row in record['rows']),
        limit_frames=8, limit_ms=8 * 70224 * 1000 / 4194304,
        rom_sha256=CANDIDATE))


def models(jobs):
    from . import description_latency_integration as latency
    latency.BASE = BASE
    latency.models(jobs)


def contracts():
    rows = []
    for label, source in (('production', BASE / 'baseline-source'), ('candidate', BASE / 'candidate')):
        retained = Path('build/dex-selected-ancestors-vram-20261012-v6/rollback/pokecrystal.sym')
        target = source / retained
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / retained, target)
        modules = []
        for name in ('test_dex_description_latency', 'test_dex_backlog_revalidation', 'test_pokedex_ancestors'):
            module = importlib.import_module('tools.' + name)
            module.__file__ = str(source / 'tools' / (name + '.py'))
            if hasattr(module, 'ROOT'):
                module.ROOT = source
            modules.append(module)
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules)
        with (BASE / f'{label}-additional-contracts.log').open('w') as log:
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        row = dict(variant=label, tests=result.testsRun, skipped=len(result.skipped),
                   failures=len(result.failures), errors=len(result.errors))
        rows.append(row)
        assert result.wasSuccessful() and not result.skipped, row
    write(BASE / 'additional-contracts.json', rows)
    print(json.dumps(rows, indent=2), flush=True)


def finalize():
    from .type_mode7_campaign import PHASES
    def read(relative):
        return json.loads((BASE / relative).read_text())
    manifest = read('qualification.json')
    standard = read('runtime-regression/full-regression.json')
    phases = read('runtime-regression/phase-results.json')
    assert {row['phase'] for row in phases} == set(PHASES) | {'arrows', 'report'}
    assert all(row['exit_code'] == 0 for row in phases), phases
    assert standard['merge_ready'] and not standard['issues'], standard['issues']
    assert standard['rom_sha256'] == CANDIDATE and standard['baseline_sha256'] == PRODUCTION
    checks = {}
    specifications = {
        'selected_info': ('runtime/focused/info-all-double-speed/summary.json', 746),
        'selected_moves': ('runtime/focused/moves-all-double-speed/summary.json', 746),
        'selected_stress': ('runtime/focused/info-stress/summary.json', 400),
        'selected_features': ('runtime/feature-timing/summary.json', 1056),
        'selected_returns': ('runtime/return-pixels/summary.json', 115),
        'unown_font_reuse': ('runtime/focused/ancestor-font-reuse/summary.json', 16),
        'description_all_species': ('runtime/all-species-unown-transition/summary.json', 1492),
        'description_phases': ('runtime/timing-unown-transition/summary.json', 128),
        'moves_description_returns': ('runtime/moves-returns/summary.json', 128),
        'uncaught_description_returns': ('runtime/visibility-unown-transition/summary.json', 128),
        'description_models': ('description-models/summary.json', 1536),
        'new_entry_species': ('all-species/summary.json', 746),
        'new_entry_visuals': ('visual/summary.json', 60),
        'new_entry_input_sweep': ('sweep/summary.json', 8272),
        'lifecycle': ('lifecycle/summary.json', 336),
        'secondary_routes': ('lifecycle/routes.json', 36),
        'exit_publication': ('lifecycle/exit-matrix/summary.json', 88),
        'unown_decoder': ('runtime/unown-decoder/summary.json', 156),
    }
    for name, (path, count) in specifications.items():
        record = read(path)
        assert record['cases'] == count and record['failures'] == 0, (name, record.get('cases'), record.get('failures'))
        if 'rom_sha256' in record:
            assert record['rom_sha256'] == CANDIDATE, name
        checks[name] = dict(cases=count, failures=0, evidence=path)
    for model in ('0', 'A', 'B', 'C', 'D', 'E'):
        record = read(f'runtime/unown-model-{model}/summary.json')
        assert record['cases'] == 112 and record['rom_sha256'] == CANDIDATE
        assert record['game_files_unchanged'] and record['donor_unchanged']
        assert all(all(row[key] for key in ('letter_restored', 'return_position',
                   'return_presentation', 'battery_unchanged')) for row in record['checks'])
        checks['unown_model_' + model] = dict(cases=112, failures=0)
    for path in ('lifecycle/audio.json', 'lifecycle/audio-registers.json'):
        record = read(path)
        assert record['cases'] == 12 and not record['mismatches'], path
    for path in ('returns-summary.json', 'nicknames-summary.json'):
        record = read(path)
        assert record['cases'] == 4 and all(not row['issues'] for row in record['results']), path
        checks[path] = dict(cases=4, failures=0)
    capture_returns = read('returns-summary.json')['results']
    early_audio = {row['scenario']: row.get('playback_misses', []) for row in capture_returns
                   if row['variant'] == 'baseline'}
    for row in capture_returns:
        if row['variant'] == 'candidate':
            assert row.get('playback_misses', []) == early_audio[row['scenario']]
    assert read('description-response-budget.json')['maximum_frames'] <= 8
    negative = read('stale-decoder-control/decoder/summary.json')
    assert negative['cases'] == 156 and negative['failures'] == 104
    assert negative['rom_sha256'] != CANDIDATE
    assert all(row['correct'] == (row['previous'] == 'CHIKORITA') and row['restored']
               and row['bank_stack_sram_ok'] for row in negative['rows'])
    checks['stale_decoder_negative_control'] = dict(cases=156, expected_rejections=104,
        observed_rejections=104, only_stale_six_and_seven_tile_cases_rejected=True,
        evidence='stale-decoder-control/decoder/summary.json')
    assert not read('lifecycle/summary.json')['completed_screen_issues']
    assert not read('lifecycle/summary.json')['nonwhite_before_fade_issues']
    additional = read('additional-contracts.json')
    assert len(additional) == 2 and all(row['tests'] == 22 and not any(
        row[key] for key in ('failures', 'errors', 'skipped')) for row in additional)
    for path, digest in manifest['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, path
    for path in (BASE / 'candidate/pokecrystal.gbc', BASE / 'pokecrystal-dex-types.gbc',
                 APPROVED / 'pokecrystal-dex-unown-staged.gbc'):
        assert sha256(path.read_bytes()) == CANDIDATE, path
    changed = []
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '*.asm', '*.inc'], cwd=ROOT).decode().split('\0')
    for name in tracked:
        before, after = BASE / 'baseline-source' / name, BASE / 'candidate' / name
        if name and before.is_file() and after.is_file() and before.read_bytes() != after.read_bytes():
            changed.append(name)
    assert set(changed) == {'engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm', 'engine/gfx/cgb_layouts.asm'}, changed
    artwork = 0
    for path in (BASE / 'baseline-source/gfx').rglob('*'):
        # Compiled objects contain relocations/debug paths, not artwork bytes.
        if path.is_file() and path.suffix not in ('.o', '.d'):
            other = BASE / 'candidate/gfx' / path.relative_to(BASE / 'baseline-source/gfx')
            assert other.is_file() and sha256(other.read_bytes()) == sha256(path.read_bytes()), path
            artwork += 1
    for ext in ('gbc', 'sym', 'map', 'sav'):
        shutil.copy2(BASE / f'pokecrystal-dex-types.{ext}', BASE / f'pokecrystal-dex-unown-transitions.{ext}')
    manifest.update(status='Full standard and supplementary regression passed; production unchanged',
        full_regression_passed=True, production_integrated=False, standard_phases=phases,
        standard_report='runtime-regression/full-regression.json', supplementary=checks,
        changed_assembly_owners=changed, unchanged_artwork_files=artwork,
        artwork_audit_excludes_compiled_sidecars=['.o', '.d'],
        additional_contracts=additional,
        unchanged_preexisting_capture_startup_audio_events=early_audio,
        limits=['Native battle fixture exceptions are compared with production, not erased',
                'Historical host failures are retained with matching production identities',
                'Physical hardware and manual auditory acceptance are not certified',
                'Independent Battle Tower addendum is not part of the standard campaign'])
    write(BASE / 'qualification.json', manifest)
    print(json.dumps({key: manifest[key] for key in ('status', 'candidate_sha256',
        'production_sha256', 'delta', 'full_regression_passed', 'production_integrated')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'standard', 'animations', 'selected', 'displays',
        'registration', 'lifecycle', 'lifecycle_audit', 'routes', 'exit_matrix', 'audio', 'audio_registers',
        'description', 'models', 'contracts', 'finalize', 'report'))
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    campaign.BASE = BASE
    if args.action == 'prepare':
        prepare(args.jobs)
    elif args.action in ('contracts', 'finalize'):
        globals()[args.action]()
    elif args.action in ('description', 'models'):
        globals()[args.action](args.jobs)
    elif args.action == 'standard':
        raise SystemExit(campaign.standard(args.phases))
    elif args.action == 'report':
        raise SystemExit(campaign.standard(['report']))
    else:
        campaign.extras(args.action)
