"""Freeze matching links and run the standard registration-support campaigns.

This does not implement the separately owned all-species registration runner.
Use inventory before preparation; only prepare after the parent freezes a link.
"""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import unittest

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from .type_mode7_campaign import PHASES

TABLES = ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
          'dex-moves-mode-assets', 'dex-sort-assets')
STEMS = ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime',
         'pokecrystal-dex-unown-fast')
DEFAULT_BASELINE = ROOT / 'build/dex-position-memory-20261014/candidate'
DEFAULT_BATTERY = ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'
STANDARD = tuple('standard:' + phase for phase in PHASES + ('arrows',))
EXTRAS = ('animations', 'displays', 'selected', 'description', 'models', 'contracts', 'numbers',
          'lifecycle', 'lifecycle-audit', 'routes', 'exit-matrix', 'audio-registers', 'audio-proof',
          'baseline-host')
CAPTURE = ('capture-setup', 'capture', 'capture-supplement')
ALL = STANDARD + EXTRAS + CAPTURE + ('tower-prepare', 'tower', 'standard:report')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text())


def private(path):
    path = path.resolve()
    if path == ROOT / 'build' or not path.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private subdirectory under build/')
    return path


def module(name, *args):
    return [sys.executable, '-B', '-m', 'tools.dex_timing.' + name, *map(str, args)]


def command(base, action, jobs):
    if action.startswith('standard:'):
        return module('type_mode7_campaign', '--base', base, '--variant', 'runtime',
                      '--phases', action.split(':')[1])
    if action in ('animations', 'displays', 'selected', 'lifecycle', 'lifecycle-audit',
                  'routes', 'exit-matrix', 'audio-registers'):
        return module('dex_cleanup_campaign', action, '--base', base)
    if action == 'tower-prepare':
        return module('battle_tower', 'prepare', '--output', base / 'battle-tower',
            '--baseline-source', base / 'baseline-source', '--candidate-source', base / 'candidate',
            '--battery', base / 'pokecrystal-dex-types.sav')
    if action == 'tower':
        return module('battle_tower', 'all', '--output', base / 'battle-tower')
    if action in CAPTURE + ('capture-smoke',):
        phase = {'capture-setup': 'setup', 'capture': 'campaign',
                 'capture-supplement': 'supplement', 'capture-smoke': 'smoke'}[action]
        return module('gotcha_boundary', phase, '--output', base, '--jobs', jobs,
                      '--baseline-source', base / 'baseline-source')
    return module('interactive_full_regression', 'worker', '--base', base,
                  '--actions', action, '--jobs', jobs)


def versions():
    result = dict(python=sys.version)
    for name, args in (('rgbasm', ['rgbasm', '--version']), ('clang', ['clang', '--version']),
        ('sameboy', ['git', '-C', str(Path.home() / 'Documents/GitHub/SameBoy'), 'rev-parse', 'HEAD']),
        ('sameboy_dirty', ['git', '-C', str(Path.home() / 'Documents/GitHub/SameBoy'), 'status', '--short']),
        ('source_commit', ['git', 'rev-parse', 'HEAD'])):
        result[name] = subprocess.check_output(args, cwd=ROOT, text=True).strip()
    return result


def inventory(base, jobs):
    from .type_full_regression import commands
    rows = {}
    for name in ('dex-position-memory-20261014', 'dex-unown-transition-regression-20261014',
                 'dex-description-fix-integration-20261014'):
        path = ROOT / 'build' / name / 'runtime-regression/phase-results.json'
        if path.is_file():
            phases = read(path)
            rows[name] = dict(serial_phase_minutes=sum(p['seconds'] for p in phases) / 60,
                phases=[dict(phase=p['phase'], seconds=p['seconds'], exit_code=p['exit_code']) for p in phases],
                scope='Historical costs, not acceptance evidence for a new link; excludes supplementary campaigns')
    expanded = {phase: commands(base / 'runtime-regression', phase)
                for phase in PHASES if phase not in ('host', 'historical-host', 'gift', 'chart', 'diagnose-types')}
    record = dict(production_sha256=sha256((ROOT / 'pokecrystal.gbc').read_bytes()),
        default_baseline=str(DEFAULT_BASELINE),
        baseline_matches_production=sha256((DEFAULT_BASELINE / 'pokecrystal.gbc').read_bytes()) ==
                                    sha256((ROOT / 'pokecrystal.gbc').read_bytes()),
        environment=versions(), historical_costs=rows, free_bytes=shutil.disk_usage(ROOT).free,
        retained_campaign_size_gb=[8.3, 17], requested_workers=jobs,
        effective_workers='Established standard/supplementary modules cap or fix workers at six; capture uses --jobs',
        preparation=module('interactive_full_regression', 'prepare', '--base', base,
            '--baseline-source', DEFAULT_BASELINE, '--candidate-source', '<parent-final-source>',
            '--battery', DEFAULT_BATTERY, '--jobs', jobs),
        ordered_actions=[dict(action=a, command=command(base, a, jobs)) for a in ALL],
        expanded_standard_commands=expanded,
        fixture_requirements=[str(ROOT / 'build/dex-moves-search-final-review-20261011' / name)
            for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json', 'moves-mode-manifest.json')],
        invariants=['Fresh ROM-specific native checkpoints; no cross-ROM CPU-state reuse',
            'Explicit Modern/Evolves fixture seed, frozen per-link generated tables and source',
            'Discovery before gameplay; persistence before timing; gameplay before readiness/battle-discovery',
            'No changed baseline exception identities; current host group has no allowed LY64 failure',
            'Tower report may be non-clean only with complete coverage and no new failures',
            'All-species registration/twenty-species tab timings and evolution audit are separately owned',
            'Old resident New Entry helpers remain tested but are not streaming-owner acceptance'],
        timing_units=dict(hz=4194304, ticks_per_display_frame=70224, ms_per_display_frame=70224/4194304*1000))
    write(base / 'orchestration/inventory.json', record)
    return record


def snapshot(source, target):
    ignore = shutil.ignore_patterns('.git', '.agents', '.codex', '.aws', 'build', '__pycache__',
                                   '*.o', '*.d', '*.pyc', '*.sav', '*.s0')
    shutil.copytree(source, target, ignore=ignore)
    for name in TABLES:
        shutil.copytree(source / 'build' / name, target / 'build' / name,
                        ignore=shutil.ignore_patterns('*.o', '*.d'))
    # Preserve the link's build generators; overlay only current test harnesses.
    shutil.copytree(ROOT / 'tools/dex_timing', target / 'tools/dex_timing', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in (ROOT / 'tools').glob('test_*.py'):
        shutil.copy2(path, target / 'tools' / path.name)


def protected_inputs(baseline, candidate, battery):
    paths = {battery, *ROOT.glob('*.sav')}
    main_save = Path('/Applications/SameBoy/Games/pokecrystal.sav')
    if main_save.is_file():
        paths.add(main_save)
    paths.update(source / f'pokecrystal.{ext}' for source in (ROOT, baseline, candidate)
                 for ext in ('gbc', 'sym', 'map'))
    return {str(path.resolve()): sha256(path.read_bytes()) for path in sorted(paths)}


def check_inputs(base):
    data = read(base / 'orchestration/inputs.json')
    changed = [name for name, digest in data['protected'].items()
               if not Path(name).is_file() or sha256(Path(name).read_bytes()) != digest]
    if changed:
        raise AssertionError('Protected/frozen inputs changed: ' + ', '.join(changed))
    return data


def prepare(base, baseline, candidate, battery, jobs):
    if base.exists():
        raise ValueError('Preparation requires a fresh campaign directory')
    if base.is_relative_to(baseline) or base.is_relative_to(candidate):
        raise ValueError('Do not nest evidence inside an input source tree')
    hashes = protected_inputs(baseline, candidate, battery)
    if hashes[str((baseline / 'pokecrystal.gbc').resolve())] != hashes[str(ROOT / 'pokecrystal.gbc')]:
        raise ValueError('The baseline must match protected production exactly')
    base.mkdir(parents=True)
    data = dict(protected=hashes, baseline_source=str(baseline), candidate_source=str(candidate),
                battery=str(battery), environment=versions(), preparation_complete=False)
    write(base / 'orchestration/inputs.json', data)
    for label, source in (('baseline-source', baseline), ('candidate', candidate)):
        target = base / label
        snapshot(source, target)
        expected = sha256((source / 'pokecrystal.gbc').read_bytes())
        with (base / 'orchestration' / (label + '-rebuild.log')).open('w') as log:
            subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=target,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        if sha256((target / 'pokecrystal.gbc').read_bytes()) != expected:
            raise AssertionError(label + ' source does not exactly reproduce the input ROM')
        for ext in ('gbc', 'sym', 'map'):
            path = target / ('pokecrystal.' + ext)
            data['protected'][str(path)] = sha256(path.read_bytes())
    rollback = base / 'rollback'
    rollback.mkdir()
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(base / 'baseline-source' / ('pokecrystal.' + ext), rollback / ('pokecrystal.' + ext))
    with tarfile.open(base / 'rollback-source.tar', 'w') as archive:
        for path in (base / 'baseline-source').iterdir():
            archive.add(path, arcname=path.name)
    for stem in STEMS:
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(base / 'candidate' / ('pokecrystal.' + ext), base / (stem + '.' + ext))
        shutil.copy2(battery, base / (stem + '.sav'))
    source = base / 'runtime'
    source.mkdir()
    for name in ('candidate', 'rollback'):
        (source / name).symlink_to(base / name, target_is_directory=True)
    (source / 'rollback-source.tar').symlink_to(base / 'rollback-source.tar')
    for stem in STEMS:
        for ext in ('gbc', 'sym', 'map', 'sav'):
            (source / (stem + '.' + ext)).symlink_to(base / (stem + '.' + ext))
    from .type_full_regression import prepare as campaign_prepare
    campaign_prepare(source, base / 'runtime-regression', rollback)
    for path in [*rollback.glob('pokecrystal.*'), *(base / (stem + '.' + ext)
            for stem in STEMS for ext in ('gbc', 'sym', 'map', 'sav'))]:
        data['protected'][str(path)] = sha256(path.read_bytes())
    data.update(preparation_complete=True,
        baseline_sha256=sha256((rollback / 'pokecrystal.gbc').read_bytes()),
        candidate_sha256=sha256((base / 'candidate/pokecrystal.gbc').read_bytes()))
    from tools.build_dex_unown_prototype import resources
    before = resources(rollback / 'pokecrystal.map')
    after = resources(base / 'candidate/pokecrystal.map')
    data['resource_delta'] = {name: after[name] - value for name, value in before.items()}
    old = read_symbols(rollback / 'pokecrystal.sym')
    new = read_symbols(base / 'candidate/pokecrystal.sym')
    data['moved_ram_labels'] = [name for name, pair in old.items()
                              if pair[1] >= 0xa000 and name in new and new[name] != pair]
    if data['moved_ram_labels'] or any(data['resource_delta'][name]
            for name in ('SRAM', 'WRAM0', 'WRAMX', 'HRAM')):
        raise AssertionError('Unexpected allocated/moved RAM in the registration prototype')
    write(base / 'orchestration/inputs.json', data)
    check_inputs(base)
    inventory(base, jobs)
    print(json.dumps({k: data[k] for k in ('preparation_complete', 'baseline_sha256', 'candidate_sha256')}), flush=True)


def worker(base, action, jobs):
    if action == 'description':
        from . import description_latency as latency
        latency.BASE, latency.RUN_TAG = base, 'interactive'
        for name in ('test', 'moves', 'visibility'):
            if getattr(latency, name)('runtime', jobs):
                raise AssertionError('Description return failure: ' + name)
        if latency.test('runtime', jobs, all_species=True):
            raise AssertionError('All-species Description return failure')
        report = read(base / 'runtime/all-species-interactive/summary.json')
        if report['cases'] != 1492 or any(not r.get('complete_visible') or
                r['complete_visible']['frames'] > 8 for r in report['rows']):
            raise AssertionError('Active Description response matrix/budget failed')
    elif action == 'models':
        from . import description_latency_integration as integration
        integration.BASE = base
        integration.models(jobs)
    elif action == 'contracts':
        from . import unown_transition_campaign as contracts, gotcha_boundary
        contracts.BASE = gotcha_boundary.BASE = base
        contracts.contracts()
        gotcha_boundary.contracts(base / 'baseline-source')
        symbols = read_symbols(base / 'candidate/pokecrystal.sym')
        if 'NewDexRegistration_Loop' in symbols:
            subprocess.run([sys.executable, '-B', 'tools/test_interactive_registration.py',
                '--root', str(base / 'candidate'), '--report', str(base / 'context-contracts.json')],
                cwd=ROOT, check=True)
    elif action == 'audio-proof':
        from . import dex_cleanup_campaign, dex_position_campaign
        dex_cleanup_campaign.BASE = dex_position_campaign.BASE = base
        dex_cleanup_campaign.audio()
        dex_position_campaign.audio_proof()
    elif action == 'numbers':
        numbers(base)
    elif action == 'baseline-host':
        from .type_full_regression import host
        target=base/'orchestration/full-baseline-host'
        target.mkdir()
        (target/'campaign-logs').mkdir()
        (target/'candidate').symlink_to(base/'baseline-source',target_is_directory=True)
        (target/'baseline').mkdir()
        (target/'baseline/candidate').symlink_to(base/'baseline-source',target_is_directory=True)
        if host(target):raise AssertionError('Full baseline host checks failed')
        report=read(target/'campaign-logs/host.json')
        if report['cases']!=87 or report['failures'] or report['errors'] or report['skipped']:
            raise AssertionError('Incomplete full baseline host checks')
        write(target/'receipt.json',dict(rom_sha256=check_inputs(base)['baseline_sha256'],
            cases=report['cases'],scope='Explicit full production host group, not only candidate-failure replays'))
    else:
        raise ValueError(action)


def numbers(base):
    from .assets import Repository, offset
    from .costs import machine
    from pokedex_info_assets import Compiler
    results = []
    for variant, source in (('baseline', base / 'baseline-source'), ('candidate', base / 'candidate')):
        repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
        data = Compiler(source).compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
        glyphs = repo.symbols['PokedexInfoTileGFX'][1]
        number_bank, number_pc = repo.symbols['PokedexInfoNumbers']
        table = offset((number_bank, number_pc))
        planner_bank = repo.symbols['PokedexInfo_PlanStats'][0]
        cases = 0
        for value in range(256):
            expected = b''.join((glyphs + tile * 16).to_bytes(2, 'little') for tile in data['numbers'][value])
            if repo.rom[table + value*8:table + value*8+8] != expected:
                raise AssertionError(f'{variant}: numeric source/linked row mismatch at {value}')
            for row in range(6):
                cpu = machine(repo)
                cpu.write(0xff70, 3)
                cpu.field('wPokedexInfoRow', row)
                cpu.field('wPokedexInfoTileCount', 15 + row*4)
                cpu.block(repo.symbols['wPokedexInfoStats'][1], bytes([value]*6))
                staging = repo.symbols['wPokedexInfoMiniGFX'][1]
                cpu.block(staging, b'\xa6'*32)
                cpu.run('PokedexInfo_PlanStats')
                actual = cpu.data(repo.symbols['wPokedexInfoTileSources'][1] + 30 + row*8, 8)
                if actual != expected or cpu.bank != planner_bank or cpu.ram[0xff70] != 3:
                    raise AssertionError(f'{variant}: numeric transport/bank failure at {value}, row {row}')
                if cpu.data(staging + 8, 24) != b'\xa6'*24:
                    raise AssertionError(f'{variant}: numeric staging overran eight bytes')
                cases += 1
        results.append(dict(variant=variant, cases=cases, rom_sha256=sha256(repo.rom),
            number_bank=number_bank, planner_bank=planner_bank, failures=0))
    write(base / 'numeric-contracts.json', dict(cases=sum(r['cases'] for r in results), failures=0,
        results=results, scope='Linked numeric pointers and real planner execution; 256 values x six rows per ROM. Native displayed pixels remain separate.'))
    print(json.dumps(results, indent=2), flush=True)


def result_gate(base, action, exit_code):
    if action == 'tower':
        report = read(base / 'battle-tower/report.json')
        data = check_inputs(base)
        ok = (exit_code in (0, 1) and report['coverage_complete'] and report['no_new_failures'] and
              report['protected_inputs_unchanged'] and report['rom_hashes'] ==
              dict(baseline=data['baseline_sha256'], candidate=data['candidate_sha256']))
        return ok, dict(clean=report['clean'], no_new_failures=report['no_new_failures'],
                        coverage_complete=report['coverage_complete'])
    if action in ('capture', 'capture-smoke', 'capture-supplement'):
        filename, expected = {'capture': ('report.json', 104), 'capture-smoke': ('smoke.json', 6),
                              'capture-supplement': ('supplement.json', 8)}[action]
        report = read(base / filename)
        return capture_gate(report, expected, exit_code)
    return exit_code == 0, {}


def capture_gate(report, expected, exit_code):
    rows = report['results']
    key = lambda r: (r['scenario'], r['species'], r['phase'], r.get('following_action', 'run'))
    pairs = {v: {key(r): r for r in rows if r['variant'] == v} for v in ('production', 'candidate')}
    unique = sum(len(p) for p in pairs.values()) == len(rows)
    complete = (report['cases'] == len(rows) == expected and unique and
                pairs['production'].keys() == pairs['candidate'].keys())
    no_dex = [row for row in rows if row['scenario'] == 'no-dex']
    repeats = [row for row in rows if row['scenario'] == 'repeat']
    if expected == 104:
        complete &= len(no_dex) == 8
        complete &= len(repeats) == 8
    invalid_no_dex = [list(key(row)) for row in no_dex if not no_dex_proof(row)]
    invalid_repeats = [list(key(row)) for row in repeats if row.get('skipped_registration_entries') != 0]
    following_catches = [row for row in rows if row.get('following_action') == 'catch']
    if expected == 8:
        complete &= len(following_catches) == 4
    invalid_following = [list(key(row)) for row in following_catches if not following_capture_proof(row)]
    misses = lambda r: sorted(json.dumps({k: v for k, v in e.items() if k != 't'}, sort_keys=True)
                              for e in r.get('misses', []))
    differences = [list(k) for k in pairs['production'].keys() & pairs['candidate'].keys()
                   if misses(pairs['production'][k]) != misses(pairs['candidate'][k])]
    failures = sum(bool(r['issues'] or r.get('native_warnings')) for r in rows)
    invalid_money = [list(key(r)) for r in rows if
        'balance' not in r.get('before', {}) or
        r.get('after', {}).get('balance') != r['before']['balance'] or
        r.get('following_balance') != r['before']['balance']]
    ok = (exit_code == 0 and complete and not failures and not differences and
          not invalid_no_dex and not invalid_following and not invalid_repeats and not invalid_money)
    return ok, dict(cases=len(rows), failures=failures, case_matrix_complete=complete,
                    changed_miss_identities=differences, invalid_no_dex_proofs=invalid_no_dex,
                    invalid_following_capture_proofs=invalid_following,
                    invalid_repeat_proofs=invalid_repeats, invalid_money_proofs=invalid_money)


def following_capture_proof(row):
    proof = row.get('following_capture', {})
    expected = proof.get('received_dex', False) and not proof.get('previously_caught', True)
    return (proof.get('registration_expected') == expected and
            proof.get('registration_entries') == int(expected) and
            (not expected or proof.get('registration_return_reached') is True) and
            proof.get('caught_after') is True and proof.get('delivery_verified') is True)


def no_dex_proof(row):
    proof = row.get('no_dex_check', {})
    bit = proof.get('flag_bit', -1)
    native = proof.get('native_return', {})
    af = native.get('af', 0x100)
    return (0 <= bit < 8 and not proof.get('status_flags', 1 << bit) & (1 << bit) and
            af >> 8 == 0 and bool(af & 0x80) and native.get('opcode') == 0xc9 and
            native.get('bank') == 0 and proof.get('registration_entries') == 0)


def run(base, actions, jobs):
    check_inputs(base)
    ledger = base / 'orchestration/actions.json'
    rows = read(ledger) if ledger.exists() else []
    lock = (base / 'orchestration/runner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        for action in actions:
            prior = next((r for r in rows if r['action'] == action), None)
            if prior:
                if prior.get('passed'):
                    continue
                raise ValueError('Preserve the failed campaign; use a new base for retries: ' + action)
            check_inputs(base)
            path = base / 'orchestration' / (action.replace(':', '-') + '.log')
            if path.exists():
                raise ValueError('Preserve interrupted evidence: ' + str(path))
            args = command(base, action, jobs)
            print(json.dumps(dict(action=action, command=args, log=str(path))), flush=True)
            started = time.monotonic()
            with path.open('w') as log:
                env = dict(os.environ, PYTHONPATH='tools:.', PYTHONDONTWRITEBYTECODE='1',
                           DEX_COMPRESS_TRACE_ROOT=str(base))
                result = subprocess.run(args, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                passed, gate = result_gate(base, action, result.returncode)
            except Exception as error:
                passed, gate = False, dict(report_error=f'{type(error).__name__}: {error}')
            row = dict(action=action, exit_code=result.returncode, passed=passed,
                       seconds=round(time.monotonic()-started, 3), command=args, log=str(path), gate=gate)
            rows.append(row)
            write(ledger, rows)
            check_inputs(base)
            print(json.dumps(row), flush=True)
            if not passed:
                print(path.read_text()[-5000:], flush=True)
                return 1
    finally:
        lock.close()
    return 0


def audit(base):
    inputs = check_inputs(base)
    rows = read(base / 'orchestration/actions.json')
    completed = {r['action'] for r in rows if r['passed']}
    missing = sorted(set(ALL) - completed)
    groups = dict(standard=STANDARD + ('standard:report',), supplementary=EXTRAS,
                  capture=CAPTURE, tower=('tower-prepare', 'tower'))
    record = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        protected_inputs_unchanged=True, support_campaign_complete=not missing, missing_actions=missing,
        action_counts={name: dict(expected=len(actions), completed=sum(a in completed for a in actions))
                       for name, actions in groups.items()},
        no_new_failures=None if missing else True,
        action_results=rows, full_qualification=False,
        scope='This support campaign only; parent adjudicates separately owned evidence and manual review',
        parent_owned=['All-species interactive tabs and twenty-species matched timing',
                      'Evolution-data audit', 'Manual audio/visual review and packaging'],
        failure_preservation={name: str(base / 'orchestration' / name / 'receipt.json')
            for name in ('dex-source-root-repair', 'host-contract-repair', 'no-dex-fixture-repair',
                         'following-capture-repair', 'tower-victory-input-repair')
            if (base / 'orchestration' / name / 'receipt.json').exists()},
        compatibility_receipts=[str(path) for path in
            (base / 'orchestration/repeat-compatibility/receipt.json',) if path.exists()])
    if not missing:
        tower = read(base / 'battle-tower/report.json')
        animations = read(base / 'all-animations/report.json')
        history = read(base / 'runtime-regression/historical-host-comparison.json')
        record['baseline_exceptions'] = dict(
            tower=dict(clean=tower['clean'], no_new_failures=tower['no_new_failures'],
                       coverage_complete=tower['coverage_complete'],
                       evidence=str(base / 'battle-tower/report.json')),
            native_animations=animations['native']['summary'],
            historical_host=dict(identical=history['same_failure_error_skip_identities'],
                records={v: {k: len(r[k]) if isinstance(r[k], list) else r[k]
                             for k in ('cases', 'failures', 'errors', 'skipped')}
                         for v, r in history['records'].items()}))
        record['tower_timeout_audit'] = str(base / 'battle-tower/timeout-audit.json')
        if (base / 'orchestration/tower-context/receipt.json').exists():
            record['tower_timeout_context'] = str(base / 'orchestration/tower-context/receipt.json')
        cadence_path = base / 'orchestration/tower-original-cadence/receipt.json'
        if cadence_path.exists():
            cadence = read(cadence_path)
            record['original_cadence_diagnostic'] = dict(evidence=str(cadence_path),
                scope=cadence['scope'],
                results=[{key: row[key] for key in ('variant', 'phase', 'returned', 'additional_frames',
                                                   'total_frames', 'issues', 'watch_counts')}
                         for row in cadence['results']])
            diagnostics = {row['checkpoint']: row for row in cadence['results']}
            classifications = []
            for observation in read(base / 'battle-tower/timeout-audit.json')['results']:
                phase = read(base / 'battle-tower' / observation['variant'] / observation['phase'] / 'summary.json')
                recovered = next(row for row in phase['results'] if row['case'] == observation['case'])
                original_cadence = diagnostics.get(observation['checkpoint'])
                classifications.append(dict(variant=observation['variant'], phase=observation['phase'],
                    case=observation['case'], recovered=recovered.get('recovered', False),
                    completed=not recovered['issues'] and not recovered.get('timeout'),
                    fresh_native_replay=recovered.get('fresh_native_replay', False),
                    recovery_frames=recovered.get('recovery_frames'), total_frames=recovered.get('elapsed_frames'),
                    issues=recovered['issues'], native_audit_watch_counts=observation['watch_counts'],
                    native_audit_hp_changed=observation['hp_changed'],
                    classification=('Stale post-battle party flag steered at victory text; corrected fresh native replay completed'
                        if recovered.get('input_driver_correction') else
                        'First-budget overrun; original cadence also completed'
                        if original_cadence and original_cadence['returned'] else
                        'Original-cadence sensitivity; bounded seven-frame recovery completed'
                        if original_cadence and recovered.get('recovered') else
                        'See preserved native audit and recovery evidence'),
                    original_cadence_additional_frames=original_cadence.get('additional_frames')
                        if original_cadence else None))
            record['tower_timeout_classifications'] = classifications
        record['capture_gates'] = {name: result_gate(base, name, 0)[1]
                                  for name in ('capture', 'capture-supplement')}
        campaign = base / 'runtime-regression'
        playback = [read(campaign / f'playback-{style}/summary.json')['summary']
                    for style in ('modern', 'legacy')]
        persistence = read(campaign / 'persistence-qualification.json')
        record['coverage_summary'] = dict(
            scope='Overlapping checks with different fixture scopes; do not sum into end-to-end scenarios',
            standard_dex_cases=read(campaign / 'dex-regression/summary.json')['cases'],
            current_host_cases={name: read(path / 'campaign-logs/host.json')['cases']
                for name, path in (('baseline', base/'orchestration/full-baseline-host'),
                                   ('candidate', campaign))},
            persistence={key: value for key, value in persistence.items() if key.endswith('_cases')},
            selected_playback_cases=sum(row['cases'] for group in playback for row in group.values()),
            selected_entry_timing_cases=read(campaign / 'entry-timing/summary.json')['cases'],
            sampled_audio_cases=read(campaign / 'acquisition-audio-regression.json')['cases'],
            battle_move_cases=read(campaign / 'acquisition-moves-regression.json')['cases'],
            all_move_renderer_calls=animations['renderer_calls'],
            all_move_native_cases=animations['native']['cases'],
            all_move_native_pairs=animations['native']['summary'],
            interactive_host_contracts=read(base / 'context-contracts.json')['cases']
                if (base / 'context-contracts.json').exists() else None,
            linked_numeric_planner_cases=read(base / 'numeric-contracts.json')['cases'],
            active_description_return_cases=read(base / 'runtime/all-species-interactive/summary.json')['cases'],
            six_model_description_cases=read(base / 'description-models/summary.json')['cases'],
            lifecycle_cases=read(base / 'lifecycle/summary.json')['cases'],
            lifecycle_route_cases=read(base / 'lifecycle/routes.json')['cases'],
            exit_matrix_cases=read(base / 'lifecycle/exit-matrix/summary.json')['cases'],
            capture_cases=read(base / 'report.json')['cases'],
            capture_supplement_cases=read(base / 'supplement.json')['cases'],
            tower_cases=sum(sum(phase['cases'].values()) for phase in tower['phases'].values()))
        if (not tower['coverage_complete'] or not tower['no_new_failures'] or
                not history['same_failure_error_skip_identities'] or
                animations['native']['summary']['differing_issue_pairs'] or
                not all(result_gate(base, name, 0)[0] for name in ('capture', 'capture-supplement'))):
            raise AssertionError('Final support audit rejected underlying comparison evidence')
        record['final_harness'] = freeze_harness(base)
    write(base / 'orchestration/audit.json', record)
    print(json.dumps({k: v for k, v in record.items() if k != 'action_results'}), flush=True)
    return int(bool(missing))


def freeze_harness(base):
    folder = base / 'orchestration/harness-final'
    manifest_path = folder / 'manifest.json'
    if manifest_path.exists():
        manifest = read(manifest_path)
        if any(sha256((folder / name).read_bytes()) != digest for name, digest in manifest['files'].items()):
            raise AssertionError('Retained final harness changed')
        return str(manifest_path)
    folder.mkdir()
    target = folder / 'tools'
    target.mkdir()
    shutil.copytree(ROOT / 'tools/dex_timing', target / 'dex_timing',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in (ROOT / 'tools').glob('*.py'):
        shutil.copy2(path, target / path.name)
    files = {str(path.relative_to(folder)): sha256(path.read_bytes())
             for path in folder.rglob('*') if path.is_file()}
    write(manifest_path, dict(files=files,
        scope='Final corrected harness; preserved original failures and repair receipts identify earlier attempts'))
    return str(manifest_path)


def repair_dex(base, jobs):
    inputs = check_inputs(base)
    campaign = base / 'runtime-regression'
    path = base / 'orchestration/dex-source-root-repair'
    path.mkdir()
    ledger_path = base / 'orchestration/actions.json'
    ledger = read(ledger_path)
    action = next(r for r in ledger if r['action'] == 'standard:dex')
    if action['passed']:
        raise ValueError('Do not repair a passing phase')
    phase_path = campaign / 'campaign-logs/dex.json'
    phase = read(phase_path)
    if {r['command'][0] for r in phase['issues']} != {'mode_transitions', 'moves_search_dex_regression'}:
        raise ValueError('This repair only covers the diagnosed mode-transition oracle failure')
    write(path / 'original-action.json', action)
    write(path / 'original-phase.json', phase)
    phase_ledger_path = campaign / 'phase-results.json'
    write(path / 'original-phase-results.json', read(phase_ledger_path))
    for original in (campaign / 'dex-run.log', * (campaign / 'campaign-logs').glob('dex-*.log')):
        shutil.copy2(original, path / original.name)
    commands = [r for r in phase['results'] if r['command'][0] == 'mode_transitions']
    attempts = []
    started = time.monotonic()
    for role, output in (('baseline', campaign / 'baseline/dex-regression'),
                         ('candidate', campaign / 'dex-regression')):
        for number, original in enumerate(commands):
            args = list(original['command'])
            args[args.index('--output') + 1] = str(output)
            args[args.index('--jobs') + 1] = str(jobs)
            tag = args[args.index('--tag') + 1] if '--tag' in args else 'mode-transitions'
            if role == 'candidate':
                (output / tag).rename(path / ('original-' + tag))
            else:
                tag += '-source-root-confirmation'
                if '--tag' in args:
                    args[args.index('--tag') + 1] = tag
                else:
                    args += ['--tag', tag]
            log_path = path / f'{role}-{number}-mode-transitions.log'
            call = module(args[0], *args[1:])
            tick = time.monotonic()
            with log_path.open('w') as log:
                result = subprocess.run(call, cwd=ROOT, env=dict(os.environ, PYTHONPATH='tools:.'),
                                        stdout=log, stderr=subprocess.STDOUT)
            record = dict(role=role, command=args, exit_code=result.returncode,
                          seconds=round(time.monotonic()-tick, 3), log=str(log_path))
            attempts.append(record)
            write(path / 'replay-results.json', attempts)
            print(json.dumps(record), flush=True)
            if result.returncode:
                raise AssertionError('Source-root transition replay failed; original evidence retained')
            summary = read(output / tag / 'summary.json')
            if summary['cases'] != (32 if number == 0 else 8) or summary['failures']:
                raise AssertionError('Incomplete transition replay')
            if role == 'candidate':
                original.update(previous_attempts=[copy.deepcopy(original)], **record)
    qualification = next(r for r in phase['results']
                         if r['command'][:2] == ['moves_search_dex_regression', 'qualify'])
    call = module(qualification['command'][0], *qualification['command'][1:])
    with (path / 'qualify.log').open('w') as log:
        result = subprocess.run(call, cwd=ROOT, env=dict(os.environ, PYTHONPATH='tools:.'),
                                stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise AssertionError('Dex qualification still fails; original evidence retained')
    summary = read(campaign / 'dex-regression/summary.json')
    if summary['cases'] != 4479 or summary['failures']:
        raise AssertionError('Incomplete standard Dex case set after replay')
    qualification.update(previous_attempts=[copy.deepcopy(qualification)], exit_code=0,
                         log=str(path / 'qualify.log'))
    phase['issues'] = [r for r in phase['results'] if r['exit_code']]
    if phase['issues']:
        raise AssertionError('Other Dex failures remain')
    write(phase_path, phase)
    receipt = dict(rom_sha256=inputs['candidate_sha256'], baseline_sha256=inputs['baseline_sha256'],
        correction='Use the configured source for Repository and Compiler in mode_transitions.case',
        native_replays=attempts, standard_dex_cases=summary['cases'], failures=0,
        original_failure_retained=True, game_and_expectations_unchanged=True,
        seconds=round(time.monotonic()-started, 3))
    write(path / 'receipt.json', receipt)
    phases = read(phase_ledger_path)
    row = next(r for r in phases if r['phase'] == 'dex')
    old = {k: v for k, v in row.items() if k != 'previous_attempts'}
    row.update(exit_code=0, log=str(path / 'receipt.json'), seconds=receipt['seconds'],
               previous_attempts=row.get('previous_attempts', []) + [old])
    write(phase_ledger_path, phases)
    old = {k: v for k, v in action.items() if k != 'previous_attempts'}
    action.update(exit_code=0, passed=True, seconds=receipt['seconds'],
        previous_attempts=action.get('previous_attempts', []) + [old], log=str(path / 'receipt.json'),
        gate=dict(native_transition_cases_per_link=48, standard_dex_cases=4479, failures=0))
    write(ledger_path, ledger)
    check_inputs(base)
    print(json.dumps(receipt, indent=2), flush=True)


def repair_host(base):
    inputs = check_inputs(base)
    campaign = base / 'runtime-regression'
    folder = base / 'orchestration/host-contract-repair'
    folder.mkdir()
    ledger_path = base / 'orchestration/actions.json'
    ledger = read(ledger_path)
    action = next(row for row in ledger if row['action'] == 'standard:host')
    if action['passed']:
        raise ValueError('Do not repair a passing host phase')
    write(folder / 'original-action.json', action)
    for path in (campaign / 'host-run.log', campaign / 'phase-results.json',
                 * (campaign / 'campaign-logs').glob('host*')):
        shutil.copy2(path, folder / path.name)
    attempts = []
    started = time.monotonic()
    for role, output in (('baseline', campaign / 'baseline'), ('candidate', campaign)):
        (output / 'campaign-logs').mkdir(exist_ok=True)
        args = (module('type_full_regression', 'host', '--output', output) if role == 'baseline'
                else command(base, 'standard:host', 6))
        log_path = folder / (role + '-replay.log')
        with log_path.open('w') as log:
            result = subprocess.run(args, cwd=ROOT, env=dict(os.environ, PYTHONPATH='tools:.'),
                                    stdout=log, stderr=subprocess.STDOUT)
        report = read(output / 'campaign-logs/host.json')
        attempts.append(dict(role=role, command=args, exit_code=result.returncode,
                             log=str(log_path), report=report))
        write(folder / 'replay-results.json', attempts)
        print(json.dumps(attempts[-1]), flush=True)
        if (result.returncode or report['cases'] != 87 or report['skipped'] or
                report['failures'] or report['errors'] or not report['no_new_failures']):
            raise AssertionError('Host contract replay failed; initial evidence retained')
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        corrections=['Independent raw-family breeding/page oracle with old-graph expectations retained',
            'Matching-source Info compiler and graph-derived page checks',
            'Original 14000-T bound retained on baseline; banked rows require exact +672 T and unchanged admission gate'],
        replays=attempts, original_failure_retained=True, runtime_unchanged=True,
        seconds=round(time.monotonic()-started, 3))
    write(folder / 'receipt.json', receipt)
    old = {key: value for key, value in action.items() if key != 'previous_attempts'}
    action.update(exit_code=0, passed=True, seconds=receipt['seconds'], log=str(folder / 'receipt.json'),
        previous_attempts=action.get('previous_attempts', []) + [old],
        gate=dict(host_cases_per_link=87, failures=0, errors=0, skipped=0))
    write(ledger_path, ledger)
    check_inputs(base)


def repair_capture(base, jobs):
    from concurrent.futures import ProcessPoolExecutor
    from . import gotcha_boundary
    import gzip
    inputs = check_inputs(base)
    folder = base / 'orchestration/no-dex-fixture-repair'
    folder.mkdir(exist_ok=True)
    ledger_path = base / 'orchestration/actions.json'
    ledger = read(ledger_path)
    action = next(row for row in ledger if row['action'] == 'capture')
    report = read(base / 'report.json')
    if action['passed'] or {row['scenario'] for row in report['results'] if row['issues']} != {'no-dex'}:
        raise ValueError('Repair is restricted to the diagnosed No-Dex fixture')
    initial = not (folder / 'original-report.json').exists()
    if (folder / 'receipt.json').exists():
        raise ValueError('No-Dex repair already qualified')
    if initial:
        write(folder / 'original-action.json', action)
        write(folder / 'original-report.json', report)
        shutil.copy2(base / 'orchestration/capture.log', folder / 'original-capture.log')
    else:
        report = read(folder / 'original-report.json')
    rejected = None
    if not initial:
        rejected = folder / f'rejected-replay-{1 + len(list(folder.glob("rejected-replay-*")))}'
        rejected.mkdir()
        (folder / 'replay-results.json').rename(rejected / 'replay-results.json')
    configurations = read(base / 'config.json')
    tasks = []
    original_entries = [] if initial else read(folder / 'original-entry-observations.json')
    for variant, config in configurations.items():
        target = (folder / 'original-no-dex' if initial else rejected) / variant
        target.mkdir(parents=True)
        for phase in range(4):
            source = base / 'runs' / variant / f'no-dex-caterpie-q{phase}'
            if initial:
                with gzip.open(source / 'events.jsonl.gz', 'rt') as stream:
                    entries = sum(event.get('event') == 'perf_phase' and event.get('name') == 'entry'
                                  for event in map(json.loads, stream))
                original_entries.append(dict(variant=variant, phase=phase, registration_entries=entries))
            source.rename(target / source.name)
            tasks.append((dict(config, campaign_base=str(base)), 'no-dex', 'caterpie', phase))
    if any(row['registration_entries'] != 1 for row in original_entries):
        raise AssertionError('Initial false-positive diagnosis does not match retained traces')
    write(folder / 'original-entry-observations.json', original_entries)
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(gotcha_boundary.execute, tasks))
    write(folder / 'replay-results.json', results)
    for row in results:
        if row['issues'] or row['native_warnings'] or not no_dex_proof(row):
            raise AssertionError('Corrected No-Dex fixture failed; initial evidence retained')
    replacements = {(row['variant'], row['phase']): row for row in results}
    report['results'] = [replacements[row['variant'], row['phase']] if row['scenario'] == 'no-dex'
                         else row for row in report['results']]
    passed, gate = capture_gate(report, 104, 0)
    if not passed:
        raise AssertionError('Full capture gate still rejects the combined evidence: ' + str(gate))
    report['fixture_correction'] = dict(original_report=str(folder / 'original-report.json'),
        reason='Old mask cleared Unown bit 1; A-button pumping falsely dismissed resident registration',
        corrected='Clear source-defined Pokedex bit; require native zero/Z return and zero registration entries')
    write(base / 'report.json', report)
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        native_replays=8, prior_false_positive_observations=original_entries, gate=gate,
        original_failure_retained=True, runtime_unchanged=True,
        seconds=round(time.monotonic()-started, 3))
    write(folder / 'receipt.json', receipt)
    old = {key: value for key, value in action.items() if key != 'previous_attempts'}
    action.update(exit_code=0, passed=True, seconds=receipt['seconds'], log=str(folder / 'receipt.json'),
        previous_attempts=action.get('previous_attempts', []) + [old], gate=gate)
    write(ledger_path, ledger)
    check_inputs(base)
    print(json.dumps(receipt, indent=2), flush=True)


def repair_capture_supplement(base, jobs):
    from concurrent.futures import ProcessPoolExecutor
    from . import gotcha_boundary
    import gzip
    inputs = check_inputs(base)
    folder = base / 'orchestration/following-capture-repair'
    folder.mkdir(exist_ok=True)
    ledger_path = base / 'orchestration/actions.json'
    ledger = read(ledger_path)
    action = next(row for row in ledger if row['action'] == 'capture-supplement')
    report = read(base / 'supplement.json')
    failures = [row for row in report['results'] if row['issues']]
    if (action['passed'] or len(report['results']) != 8 or len(failures) != 2 or
            any(row['following_action'] != 'catch' or row['variant'] != 'candidate' for row in failures)):
        raise ValueError('Repair is restricted to the diagnosed following-capture driver')
    initial = not (folder / 'original-report.json').exists()
    if initial:
        write(folder / 'original-action.json', action)
        write(folder / 'original-report.json', report)
        shutil.copy2(base / 'orchestration/capture-supplement.log', folder / 'original-capture-supplement.log')
    else:
        report = read(folder / 'original-report.json')
    rejected = None
    if not initial:
        rejected = folder / f'rejected-replay-{1 + len(list(folder.glob("rejected-replay-*")))}'
        rejected.mkdir()
        (folder / 'replay-results.json').rename(rejected / 'replay-results.json')
    configs = read(base / 'config.json')
    tasks = []
    observations = [] if initial else read(folder / 'original-entry-observations.json')
    for row in report['results']:
        if row['following_action'] != 'catch':
            continue
        source = (base / 'supplement/catch' / row['variant'] /
                  f'{row["scenario"]}-{row["species"]}-q{row["phase"]}')
        target = (folder / 'original-catch' if initial else rejected) / row['variant'] / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if initial:
            with gzip.open(source / 'events.jsonl.gz', 'rt') as stream:
                events = list(map(json.loads, stream))
            observations.append(dict(variant=row['variant'], scenario=row['scenario'], phase=row['phase'],
                registration_entries=sum(e.get('event') == 'perf_phase' and e.get('name') == 'entry' for e in events),
                original_issues=row['issues'],
                misses=[e for e in events if e.get('event') in ('audio_miss', 'animation_miss', 'illegal')]))
        source.rename(target)
        config = dict(configs[row['variant']], campaign_base=str(base),
                      run_folder='supplement/catch', next_action='catch')
        tasks.append((config, row['scenario'], row['species'], row['phase']))
    if len(tasks) != 4 or any(row['registration_entries'] != 2 for row in observations):
        raise AssertionError('Following-capture diagnosis does not match original native entries')
    write(folder / 'original-entry-observations.json', observations)
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(gotcha_boundary.execute, tasks))
    write(folder / 'replay-results.json', results)
    replacements = {(row['variant'], row['scenario'], row['phase']): row for row in results}
    report['results'] = [replacements[row['variant'], row['scenario'], row['phase']]
                         if row['following_action'] == 'catch' else row for row in report['results']]
    passed, gate = capture_gate(report, 8, 0)
    if not passed:
        raise AssertionError('Following-capture replay failed; original evidence retained: ' + str(gate))
    report['driver_correction'] = dict(original_report=str(folder / 'original-report.json'),
        reason='Following native encounter can be a new species; held A did not exit the streaming owner',
        corrected='Derive registration from native caught/Dex flags, exit the proper owner with B, assert delivery')
    write(base / 'supplement.json', report)
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        native_replays=4, retained_fight_cases=4, original_entry_observations=observations, gate=gate,
        original_failure_retained=True, runtime_unchanged=True, initial_review_media_unchanged=True,
        seconds=round(time.monotonic()-started, 3))
    write(folder / 'receipt.json', receipt)
    old = {key: value for key, value in action.items() if key != 'previous_attempts'}
    action.update(exit_code=0, passed=True, seconds=receipt['seconds'], log=str(folder / 'receipt.json'),
        previous_attempts=action.get('previous_attempts', []) + [old], gate=gate)
    write(ledger_path, ledger)
    check_inputs(base)
    print(json.dumps(receipt, indent=2), flush=True)


def verify_repeat(base, jobs):
    from concurrent.futures import ProcessPoolExecutor
    from . import gotcha_boundary
    inputs = check_inputs(base)
    folder = base / 'orchestration/repeat-compatibility'
    if (folder / 'receipt.json').exists():
        canonicalize_repeat(base)
        passed, gate = capture_gate(read(base / 'report.json'), 104, 0)
        if not passed:
            raise AssertionError('Retained repeat compatibility evidence failed: ' + str(gate))
        check_inputs(base)
        print(json.dumps(read(folder / 'receipt.json'), indent=2), flush=True)
        return
    folder.mkdir()
    report = read(base / 'report.json')
    write(folder / 'original-report.json', report)
    tasks = [(dict(config, campaign_base=str(base),
                   run_folder='orchestration/repeat-compatibility/runs'), 'repeat', 'caterpie', phase)
             for config in read(base / 'config.json').values() for phase in range(4)]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(gotcha_boundary.execute, tasks))
    write(folder / 'replay-results.json', results)
    if (len(results) != 8 or any(row['issues'] or row['native_warnings'] or
                               row.get('skipped_registration_entries') != 0 for row in results)):
        raise AssertionError('Fresh repeat compatibility cases failed; earlier evidence retained')
    replacements = {(row['variant'], row['phase']): row for row in results}
    report['results'] = [replacements[row['variant'], row['phase']] if row['scenario'] == 'repeat'
                         else row for row in report['results']]
    passed, gate = capture_gate(report, 104, 0)
    if not passed:
        raise AssertionError('Repeat compatibility replay failed combined capture gate: ' + str(gate))
    report['repeat_compatibility'] = str(folder / 'receipt.json')
    write(base / 'report.json', report)
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        native_replays=8, registration_entries=0, gate=gate, original_rows_retained=True,
        runtime_unchanged=True, initial_review_media_unchanged=True,
        policy='Repeat advances ordinary EXP text with A and requires zero native registration entries',
        seconds=round(time.monotonic()-started, 3))
    write(folder / 'receipt.json', receipt)
    canonicalize_repeat(base)
    check_inputs(base)
    print(json.dumps(receipt, indent=2), flush=True)


def canonicalize_repeat(base):
    folder = base / 'orchestration/repeat-compatibility'
    for row in read(folder / 'replay-results.json'):
        name = Path(row['variant']) / f'repeat-caterpie-q{row["phase"]}'
        fresh, canonical, original = folder / 'runs' / name, base / 'runs' / name, folder / 'original-runs' / name
        if fresh.exists():
            if original.exists():
                raise ValueError('Do not overwrite an archived repeat trace: ' + str(original))
            original.parent.mkdir(parents=True, exist_ok=True)
            canonical.rename(original)
            fresh.rename(canonical)
        elif not original.exists() or not canonical.exists():
            raise ValueError('Incomplete repeat evidence relocation: ' + str(name))
    receipt_path = folder / 'receipt.json'
    receipt = read(receipt_path)
    if 'original_trace_directory' not in receipt:
        shutil.copy2(receipt_path, folder / 'initial-receipt.json')
        receipt.update(original_trace_directory=str(folder / 'original-runs'),
                       qualified_trace_directory=str(base / 'runs'))
        write(receipt_path, receipt)


def tower_context(base):
    from . import battle_tower
    from .assets import Repository, offset
    from .costs import machine
    from .cold_listing import Driver
    from .info_ui import BOOT
    from tools.pokedex_info_assets import species, evolution_graph, constants
    from tools.test_pokedex_moves import raw_move_sources
    import re
    inputs = check_inputs(base)
    folder = base / 'orchestration/tower-context'
    folder.mkdir(exist_ok=True)
    if (folder / 'receipt.json').exists():
        previous = folder / f'previous-attempt-{1 + len(list(folder.glob("previous-attempt-*")))}'
        previous.mkdir()
        for path in (folder / 'receipt.json', *folder.glob('*.log')):
            path.rename(previous / path.name)
    repositories = {name: Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
                    for name, source in (('baseline', base / 'baseline-source'), ('candidate', base / 'candidate'))}
    names = species(repositories['baseline'].root)
    assert species(repositories['candidate'].root) == names
    old_levels = raw_move_sources(repositories['baseline'].root)[0]
    new_levels = raw_move_sources(repositories['candidate'].root)[0]
    assert old_levels == new_levels
    costs, helpers = {}, {}
    for variant, repo in repositories.items():
        labels = []
        for suffix in ('kanto', 'johto', 'custom'):
            text = (repo.root / f'data/pokemon/evos_attacks_{suffix}.asm').read_text().split('.IndirectEnd', 1)[0]
            labels.extend(re.findall(r'^\s*dw (\w+)\s*(?:;[^\n]*)?$', text, re.M))
        assert len(labels) == len(names) == 373
        graph = evolution_graph(repo.root)
        rows = {}
        for name, label in zip(names, labels):
            bank, pc = repo.symbols[label]
            cpu = machine(repo)
            cpu.r[0] = bank
            cpu.set_pair(2, pc)
            cycles = cpu.run('SkipEvolutions')
            rows[name] = dict(cpu_t=cycles, evolution_rows=len(graph.get(name, [])),
                              skipped_bytes=cpu.pair(2)-pc)
        costs[variant] = rows
        start, end = (offset(repo.symbols[label]) for label in ('SkipEvolutions', 'DetermineEvolutionItemResults'))
        helpers[variant] = repo.rom[start:end]
    assert helpers['baseline'] == helpers['candidate']
    deltas = [dict(species=name, baseline=costs['baseline'][name], candidate=costs['candidate'][name],
                   delta_cpu_t=costs['candidate'][name]['cpu_t']-costs['baseline'][name]['cpu_t'])
              for name in names if costs['baseline'][name] != costs['candidate'][name]]
    assert sum(row['candidate']['evolution_rows']-row['baseline']['evolution_rows'] for row in deltas) == 67
    assert all(row['delta_cpu_t'] == 336 * (row['candidate']['evolution_rows']-
                                         row['baseline']['evolution_rows']) for row in deltas)
    catalog_names = {names[row[0]-1] for row in battle_tower.catalog(repositories['candidate'])}
    snapshots = []
    for variant, cfg in battle_tower.configs(base / 'battle-tower').items():
        symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
        move_source = Path(cfg['root']) / 'constants/move_constants.asm'
        move_ids = constants(move_source)
        move_names = {move_ids[name]: name for name in re.findall(r'^\s*const\s+(\w+)',
                      move_source.read_text().split('DEF NUM_ATTACKS', 1)[0], re.M)}
        item_ids = constants(Path(cfg['root']) / 'constants/item_constants.asm')
        item_names = {value: name for name, value in item_ids.items() if name not in ('NUM_ITEMS',)}
        for checkpoint in (base / 'battle-tower' / variant).glob('*/timeout-*.s0'):
            driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], folder / f'{variant}-{checkpoint.parent.name}-{checkpoint.stem}.log')
            try:
                driver.command(f'load {checkpoint}')
                pokemon = battle_tower.get(driver, symbols, 'wPokemonIndexTableEntries', 508)
                moves = battle_tower.get(driver, symbols, 'wMoveIndexTableEntries', 508)
                def permanent(table, value):
                    return int.from_bytes(table[2*(value-1):2*value], 'little') if 0 < value < 0xfd else value
                combatants = {}
                for label in ('wBattleMon', 'wEnemyMon'):
                    index = permanent(pokemon, battle_tower.byte(driver, symbols, label+'Species'))
                    attacks = [permanent(moves, value) for value in battle_tower.get(driver, symbols, label+'Moves', 4)]
                    combatants[label] = dict(species_index=index, species=names[index-1],
                        hp=int.from_bytes(battle_tower.get(driver, symbols, label+'HP', 2), 'big'),
                        move_indices=attacks, moves=[move_names.get(value, str(value)) for value in attacks],
                        pp=list(battle_tower.get(driver, symbols, label+'PP', 4)),
                        item=battle_tower.byte(driver, symbols, label+'Item'))
                    combatants[label]['item_name'] = item_names.get(combatants[label]['item'],
                                                                  str(combatants[label]['item']))
                state = driver.command('peek')
                nearest = max((address, name) for name, (bank, address) in symbols.items()
                              if bank == state['bank'] and address <= state['pc'])
                joy = {name: battle_tower.byte(driver, symbols, name) for name in
                       ('hJoypadDown', 'hJoyPressed', 'hJoyReleased', 'hJoyDown', 'hJoyLast',
                        'wMenuJoypad', 'wMenuCursorY', 'hRandomAdd', 'hRandomSub',
                        'wBattleEnded', 'wPartyMenuActionText', 'wPartyMenuCursor', 'hROMBank') if name in symbols}
                party_hp = [int.from_bytes(battle_tower.get(driver, symbols, f'wPartyMon{slot}HP', 2), 'big')
                            for slot in range(1, 4)]
                stack = bytes.fromhex(driver.command(f'read 0 {state["sp"]} 32')['bytes'])
                returns = []
                repo = repositories[variant]
                for slot in range(0, len(stack), 2):
                    address = int.from_bytes(stack[slot:slot+2], 'little')
                    bank = 0 if address < 0x4000 else joy['hROMBank']
                    if 3 <= address < 0x8000:
                        at = offset((bank, address))
                        if repo.rom[at-3] == 0xcd:
                            target = int.from_bytes(repo.rom[at-2:at], 'little')
                            target_bank = 0 if target < 0x4000 else bank
                            caller = max((pc, name) for name, (b, pc) in symbols.items()
                                         if b == bank and pc <= address)
                            returns.append(dict(stack_offset=slot, return_pc=address, bank=bank,
                                return_symbol=caller[1], return_symbol_offset=address-caller[0],
                                call_target=target, call_target_symbols=[name for name, pair in symbols.items()
                                                                         if pair == (target_bank, target)]))
                snapshots.append(dict(variant=variant, phase=checkpoint.parent.name, checkpoint=str(checkpoint),
                    cpu=state, pc_symbol=nearest[1], pc_symbol_offset=state['pc']-nearest[0],
                    joy_fields=joy, party_hp=party_hp, stack_bytes=stack.hex(),
                    call_return_candidates=returns, combatants=combatants))
            finally:
                driver.close()
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        raw_level_learnsets_identical=373, skip_helper_byte_identical=True, added_evolution_rows=67,
        changed_species=len(deltas), skip_cost_scope='Controlled linked CPU helper, not native end-to-end timing',
        cycles_per_added_evolution_row=336, changed_skip_costs=deltas,
        input_cadence=dict(initial_battle_chunk_frames=16, initial_budget_frames=60000,
                           key_policy='Alternating release and interactive A/party-selection directions',
                           diagnostic_chunk_frames=64,
                           single_recovery_chunk_frames=7, additional_recovery_budget_frames=60000),
        affected_tower_catalog_species=[row['species'] for row in deltas if row['species'] in catalog_names],
        timeout_snapshots=snapshots,
        interpretation='Extra evolution rows add controlled SkipEvolutions helper cycles with unchanged learnsets/helper code. '
            'This does not establish that FillMoves ran in a particular Tower setup or caused RNG divergence. '
            'No ordinary-battle startup reset or ISR-regression cause is asserted. '
            'Native audit and the original single bounded continuation remain mandatory.')
    write(folder / 'receipt.json', receipt)
    check_inputs(base)
    print(json.dumps({k: value for k, value in receipt.items() if k != 'changed_skip_costs'}, indent=2), flush=True)


def tower_cadence(base):
    from . import battle_tower
    from .cold_listing import Driver
    from .info_ui import BOOT
    inputs = check_inputs(base)
    folder = base / 'orchestration/tower-original-cadence'
    folder.mkdir(exist_ok=True)
    if (folder / 'receipt.json').exists():
        shutil.copy2(folder / 'receipt.json', folder / f'receipt-attempt-{1 + len(list(folder.glob("receipt-attempt-*")))}.json')
    rows = []
    for variant, cfg in battle_tower.configs(base / 'battle-tower').items():
        symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
        for checkpoint in (base / 'battle-tower' / variant).glob('*/timeout-*.s0'):
            result_path = folder / f'{variant}-{checkpoint.parent.name}-{checkpoint.stem}.json'
            if result_path.exists():
                prior = read(result_path)
                if prior['checkpoint_sha256'] != sha256(checkpoint.read_bytes()):
                    raise AssertionError('Do not reuse cadence diagnostics for a changed checkpoint')
                rows.append(prior)
                continue
            diagnostic = read(checkpoint.with_suffix('.json'))
            owner = diagnostic['owner']
            driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'],
                            folder / f'{variant}-{checkpoint.parent.name}-{checkpoint.stem}.log')
            row = dict(variant=variant, phase=checkpoint.parent.name, checkpoint=str(checkpoint),
                       checkpoint_sha256=sha256(checkpoint.read_bytes()), issues=[])
            try:
                driver.command(f'load {checkpoint.parent / "prepared.s0"}')
                options = battle_tower.byte(driver, symbols, 'wOptions')
                original_flag = battle_tower.byte(driver, symbols, 'wInBattleTowerBattle')
                driver.command(f'load {checkpoint}')
                row['start'] = driver.command('peek')
                labels = [name for name in ('BattleTurn', 'BattleAnim_UpdateOAM_All',
                          'BattleMoveInfo_UpdateTilemapAndAttrmap.wait') if name in symbols]
                for name in labels:
                    driver.command(f'watch {symbols[name][0]} {symbols[name][1]}')
                elapsed, returned = 0, False
                for step in range(60000 // 16):
                    state = driver.command(f'until {owner["bank"]} {owner["pc"]} 16 '
                                           f'{battle_tower.interactive_key(driver, symbols, 3750 + step)}')
                    elapsed += state['frames']
                    if state['hit'] and state['sp'] == owner['sp']:
                        returned = True
                        break
                row.update(returned=returned, additional_frames=elapsed,
                           total_frames=diagnostic['elapsed_frames'] + elapsed, final=state,
                           watch_counts=dict(zip(labels, driver.command('watchcounts')['hits'])))
                if returned:
                    battle_tower.battle_contract(row, driver, symbols, state, options, original_flag,
                                                int(checkpoint.stem.split('-')[-1]))
                else:
                    row['issues'].append('Original-cadence diagnostic did not return within its fixed continuation budget')
                write(result_path, row)
                rows.append(row)
                print(json.dumps(row), flush=True)
            finally:
                driver.close()
    write(folder / 'receipt.json', dict(baseline_sha256=inputs['baseline_sha256'],
        candidate_sha256=inputs['candidate_sha256'], cases=len(rows), results=rows,
        chunk_frames=16, additional_budget_frames=60000,
        scope='Independent diagnostic from the original matching-ROM timeout checkpoint. '
              'Does not alter the suite summaries, timeout limit, or mandatory seven-frame continuation.'))
    check_inputs(base)


def tower_case(task):
    from . import battle_tower as tower
    from .cold_listing import Driver
    from .info_ui import BOOT
    from .cold_listing import KEY
    cfg, checkpoint, output, group, position = task
    output.mkdir(parents=True)
    symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
    driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], output / 'native.log')
    row = dict(case=f'battle-{group}-{position}', variant=cfg['variant'], issues=[], fresh_native_replay=True)
    original_key = tower.interactive_key
    events = []
    def recorded_key(driver, symbols, step):
        key = original_key(driver, symbols, step)
        if step % 2 and tower.byte(driver, symbols, 'wBattleEnded'):
            active = any(tower.get(driver, symbols, 'wBattleMonHP', 2))
            action = tower.byte(driver, symbols, 'wPartyMenuActionText')
            if not active and action == 2:
                hp = [int.from_bytes(tower.get(driver, symbols, f'wPartyMon{slot}HP', 2), 'big') for slot in range(1, 4)]
                cursor = tower.byte(driver, symbols, 'wMenuCursorY')
                alive = [slot for slot, value in enumerate(hp, 1) if value]
                old = KEY['down' if cursor < alive[0] else 'up'] if alive and cursor != alive[0] else KEY['a']
                events.append(dict(step=step, battle_ended=1, party_action=action, party_hp=hp,
                                   cursor=cursor, old_key=old, corrected_key=key, cpu=driver.command('peek')))
        return key
    tower.interactive_key = recorded_key
    try:
        driver.command(f'load {checkpoint}')
        live = list(tower.get(driver, symbols, 'wPartySpecies', 3))
        tower.fighters(driver, symbols, live, level=group * 10)
        tower.call(driver, symbols, 'SaveGameData')
        tower.fixture(driver, symbols, 'wBTChoiceOfLvlGroup', [group])
        tower.fixture(driver, symbols, 'sBTMonOfTrainers', bytes(12))
        tower.call(driver, symbols, 'ResetBattleTowerTrainersSRAM')
        for prior in range(position + 1):
            tower.call(driver, symbols, 'LoadOpponentTrainerAndPokemon')
            if prior < position:
                tower.call(driver, symbols, 'CopyBTTrainer_FromBT_OT_TowBT_OTTemp')
        options = tower.byte(driver, symbols, 'wOptions')
        original_flag = tower.byte(driver, symbols, 'wInBattleTowerBattle')
        try:
            ended = tower.invoke(driver, symbols, 'BattleTowerBattle', frames=60000,
                                 diagnostic=output / 'timeout')
            row['elapsed_frames'] = ended['frames']
        except AssertionError:
            diagnostic = read(output / 'timeout.json')
            owner = diagnostic['owner']
            driver.command(f'load {output / "timeout.s0"}')
            elapsed = 0
            for step in range(60000 // 7):
                ended = driver.command(f'until {owner["bank"]} {owner["pc"]} 7 {recorded_key(driver, symbols, step)}')
                elapsed += ended['frames']
                if ended['hit'] and ended['sp'] == owner['sp']:
                    break
            else:
                raise AssertionError('Corrected native case exceeded the unchanged two-budget limit')
            row.update(initial_timeout_frames=diagnostic['elapsed_frames'], recovery_frames=elapsed,
                       elapsed_frames=diagnostic['elapsed_frames'] + elapsed, recovered=True)
        tower.battle_contract(row, driver, symbols, ended, options, original_flag, position)
        driver.command(f'image {output / "returned.ppm"}')
    except Exception as error:
        row['issues'].append(f'{type(error).__name__}: {error}')
    finally:
        tower.interactive_key = original_key
        driver.close()
    row['victory_input_events'] = events
    row['native_warnings'] = (output / 'native.log').read_text()
    write(output / 'result.json', row)
    print(json.dumps({key: row.get(key) for key in ('variant', 'case', 'issues', 'elapsed_frames')}), flush=True)
    return row


def repair_tower(base, jobs):
    from concurrent.futures import ProcessPoolExecutor
    from . import battle_tower as tower
    from .cold_listing import Driver, KEY
    from .info_ui import BOOT
    inputs = check_inputs(base)
    folder = base / 'orchestration/tower-victory-input-repair'
    folder.mkdir()
    output = base / 'battle-tower'
    ledger_path = base / 'orchestration/actions.json'
    ledger = read(ledger_path)
    action = next(row for row in ledger if row['action'] == 'tower')
    if action['passed']:
        raise ValueError('Do not repair a passing Tower campaign')
    write(folder / 'original-action.json', action)
    for path in (output / 'report.json', output / 'battles-comparison.json', output / 'timeout-audit.json',
                 base / 'orchestration/tower.log'):
        shutil.copy2(path, folder / path.name)
    shutil.copy2(base / 'candidate/tools/dex_timing/battle_tower.py', folder / 'original-battle_tower.py')
    configs = tower.configs(output)
    started = time.monotonic()
    proofs, tasks = [], []
    for variant, cfg in configs.items():
        symbols = {name: tuple(pair) for name, pair in cfg['symbols'].items()}
        source = output / variant / 'battles'
        target = folder / variant
        target.mkdir()
        for name in ('summary.json', 'summary-before-recovery.json'):
            shutil.copy2(source / name, target / name)
        summary = read(source / 'summary.json')
        failed = [row for row in summary['results'] if row.get('timeout')]
        expected = 'battle-10-6' if variant == 'baseline' else 'battle-10-3'
        if len(failed) != 1 or failed[0]['case'] != expected or not failed[0].get('recovery_failed'):
            raise AssertionError('Unexpected Tower failure outside the diagnosed victory-input branch')
        position = int(expected.split('-')[-1])
        checkpoint = source / f'timeout-10-{position}.s0'
        diagnostic = read(checkpoint.with_suffix('.json'))
        owner = diagnostic['owner']
        driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], target / 'checkpoint-replay.log')
        try:
            driver.command(f'load {source / "prepared.s0"}')
            options = tower.byte(driver, symbols, 'wOptions')
            flag = tower.byte(driver, symbols, 'wInBattleTowerBattle')
            driver.command(f'load {checkpoint}')
            proof = dict(variant=variant, case=expected,
                battle_ended=tower.byte(driver, symbols, 'wBattleEnded'),
                party_action=tower.byte(driver, symbols, 'wPartyMenuActionText'),
                cursor=tower.byte(driver, symbols, 'wMenuCursorY'),
                party_hp=[int.from_bytes(tower.get(driver, symbols, f'wPartyMon{slot}HP', 2), 'big')
                          for slot in range(1, 4)])
            assert (proof['battle_ended'], proof['party_action'], proof['cursor'], proof['party_hp']) == (1, 2, 2, [0, 0, 999])
            assert tower.interactive_key(driver, symbols, 1) == KEY['a']
            elapsed = 0
            for step in range(60000 // 7):
                state = driver.command(f'until {owner["bank"]} {owner["pc"]} 7 {tower.interactive_key(driver, symbols, step)}')
                elapsed += state['frames']
                if state['hit'] and state['sp'] == owner['sp']:
                    break
            else:
                raise AssertionError('Corrected checkpoint replay exceeded the original continuation budget')
            proof.update(issues=[], additional_frames=elapsed)
            tower.battle_contract(proof, driver, symbols, state, options, flag, position)
            assert not proof['issues'], proof
            proofs.append(proof)
        finally:
            driver.close()
        for case_position in (3, 6):
            tasks.append((dict(cfg, variant=variant), source / 'prepared.s0',
                          target / f'fresh-battle-10-{case_position}', 10, case_position))
    write(folder / 'checkpoint-proofs.json', proofs)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(tower_case, tasks))
    write(folder / 'fresh-replays.json', results)
    if len(results) != 4 or any(row['issues'] or row['native_warnings'] for row in results):
        raise AssertionError('Fresh matched Tower cases failed; original evidence retained')
    for row in results:
        if (row['variant'], row['case']) in (('baseline', 'battle-10-6'), ('candidate', 'battle-10-3')):
            if not any(event['old_key'] == KEY['down'] and event['corrected_key'] == KEY['a']
                       for event in row['victory_input_events']):
                raise AssertionError('Fresh case did not reproduce the diagnosed stale input predicate')
    for variant in configs:
        path = output / variant / 'battles/summary.json'
        summary = read(path)
        replacements = {row['case']: row for row in results if row['variant'] == variant}
        summary['results'] = [dict(replacements[row['case']], timeout=False,
                                   input_driver_correction=True, previous_attempts=[row])
                              if row['case'] in replacements else row for row in summary['results']]
        summary['failures'] = sum(bool(row['issues']) for row in summary['results'])
        write(path, summary)
    failures = {variant: sorted((row['case'], tuple(row['issues'])) for row in
                read(output / variant / 'battles/summary.json')['results'] if row['issues']) for variant in configs}
    write(output / 'battles-comparison.json', dict(phase='battles', no_new_failures=not any(failures.values()),
        baseline_failures=failures['baseline'], candidate_failures=failures['candidate'],
        harness_correction=str(folder / 'receipt.json')))
    raw_exit = tower.report(output)
    passed, gate = result_gate(base, 'tower', raw_exit)
    if not passed:
        raise AssertionError('Tower gate still rejects the repaired native evidence')
    receipt = dict(baseline_sha256=inputs['baseline_sha256'], candidate_sha256=inputs['candidate_sha256'],
        correction='Do not steer toward a live party member after wBattleEnded; native victory text needs A',
        matching_checkpoint_proofs=proofs, fresh_matched_cases=4, gate=gate,
        original_failures_and_recovery_retained=True, runtime_unchanged=True, budgets_unchanged=True,
        seconds=round(time.monotonic()-started, 3))
    write(folder / 'receipt.json', receipt)
    old = {key: value for key, value in action.items() if key != 'previous_attempts'}
    action.update(exit_code=raw_exit, passed=True, seconds=receipt['seconds'], gate=gate,
                  log=str(folder / 'receipt.json'), previous_attempts=action.get('previous_attempts', [])+[old])
    write(ledger_path, ledger)
    check_inputs(base)
    print(json.dumps(receipt, indent=2), flush=True)


def self_test():
    from .performance_audio import compare_playback
    from tools.test_dex_performance import AudioComparisonTests
    from . import battle_tower
    from .cold_listing import KEY
    from unittest.mock import patch
    fields = dict(wBattleEnded=1, wPartyMenuActionText=2, wMenuCursorY=2)
    def fixture_get(driver, symbols, name, size):
        return b'\0\x01' if name == 'wPartyMon3HP' else b'\0\0'
    with patch.object(battle_tower, 'byte', side_effect=lambda driver, symbols, name: fields[name]), \
            patch.object(battle_tower, 'get', side_effect=fixture_get):
        assert battle_tower.interactive_key(None, {}, 1) == KEY['a']
        assert battle_tower.interactive_key(None, {}, 0) == 0
        fields['wBattleEnded'] = 0
        assert battle_tower.interactive_key(None, {}, 1) == KEY['down']
        fields['wMenuCursorY'] = 3
        assert battle_tower.interactive_key(None, {}, 1) == KEY['a']
    case = AudioComparisonTests()
    original = case.row()
    original.update(context='catch', registration_owner='resident', registration_t=0)
    candidate = copy.deepcopy(original)
    candidate['registration_owner'] = 'streaming'
    candidate['segments'][0].update(speed_values=[1], timer_configs=[(7, 156)])
    assert compare_playback(original, candidate) == []
    for field, value in (('speed_values', [0]), ('timer_configs', [(7, 155)]), ('wave_sha256', 'bad')):
        bad = copy.deepcopy(candidate)
        bad['segments'][0][field] = value
        assert compare_playback(original, bad), field
    odd = copy.deepcopy(original)
    odd['segments'][0]['timer_configs'] = [(6, 55)]
    candidate['segments'][0]['timer_configs'] = [(7, 155), (7, 156)]
    assert compare_playback(odd, candidate) == []
    candidate['context'] = 'stats'
    assert compare_playback(odd, candidate)
    rows = [dict(variant=v, scenario='party', species='dusknoir', phase=0, issues=[],
                 before=dict(balance=2137), after=dict(balance=2137), following_balance=2137,
                 misses=[dict(event='audio_miss', t=n, remaining=45)])
            for n, v in enumerate(('production', 'candidate'))]
    report = dict(cases=2, results=rows)
    assert capture_gate(report, 2, 0)[0]
    assert not capture_gate(report, 4, 0)[0]
    assert not capture_gate(report, 2, 1)[0]
    for change in ('issues', 'misses', 'duplicate', 'money', 'missing_money', 'following_money'):
        bad = copy.deepcopy(report)
        if change == 'issues':
            bad['results'][1]['issues'] = ['owner did not return']
        elif change == 'misses':
            bad['results'][1]['misses'][0]['remaining'] = 44
        elif change == 'money':
            bad['results'][1]['after']['balance'] += 65536
        elif change == 'missing_money':
            del bad['results'][1]['before']['balance']
        elif change == 'following_money':
            bad['results'][1]['following_balance'] += 65536
        else:
            bad['results'] = [bad['results'][0], bad['results'][0]]
        assert not capture_gate(bad, 2, 0)[0], change
    no_dex = copy.deepcopy(report)
    for row in no_dex['results']:
        row.update(scenario='no-dex', no_dex_check=dict(flag_bit=0, status_flags=2,
            registration_entries=0, native_return=dict(af=0x80, opcode=0xc9, bank=0)))
    assert capture_gate(no_dex, 2, 0)[0]
    for field, value in (('status_flags', 1), ('registration_entries', 1),
                         ('native_return', dict(af=0, opcode=0xc9, bank=0))):
        bad = copy.deepcopy(no_dex)
        bad['results'][1]['no_dex_check'][field] = value
        assert not capture_gate(bad, 2, 0)[0], field
    repeat = copy.deepcopy(report)
    for row in repeat['results']:
        row.update(scenario='repeat', skipped_registration_entries=0)
    assert capture_gate(repeat, 2, 0)[0]
    repeat['results'][1]['skipped_registration_entries'] = 1
    assert not capture_gate(repeat, 2, 0)[0]
    following = copy.deepcopy(report)
    for row in following['results']:
        row.update(following_action='catch', following_capture=dict(received_dex=True,
            previously_caught=False, registration_expected=True, registration_entries=1,
            registration_return_reached=True, caught_after=True, delivery_verified=True))
    assert capture_gate(following, 2, 0)[0]
    for field, value in (('previously_caught', True), ('registration_entries', 0),
                         ('registration_return_reached', False), ('delivery_verified', False)):
        bad = copy.deepcopy(following)
        bad['results'][1]['following_capture'][field] = value
        assert not capture_gate(bad, 2, 0)[0], field
    for forbidden in (ROOT, ROOT / 'build', ROOT / 'build/../pokecrystal.gbc'):
        try:
            private(forbidden)
        except ValueError:
            pass
        else:
            raise AssertionError('Output confinement failed')
    suite = unittest.defaultTestLoader.loadTestsFromName('tools.test_dex_performance')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and not result.skipped
    print('Registration clock-policy and output-confinement controls passed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'prepare', 'run', 'worker', 'audit', 'self-test', 'repair-dex', 'repair-host', 'repair-capture', 'repair-capture-supplement', 'verify-repeat', 'tower-context', 'tower-cadence', 'repair-tower'))
    parser.add_argument('--base', type=Path, default=ROOT / 'build/interactive-full-regression-20261015')
    parser.add_argument('--baseline-source', type=Path, default=DEFAULT_BASELINE)
    parser.add_argument('--candidate-source', type=Path)
    parser.add_argument('--battery', type=Path, default=DEFAULT_BATTERY)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--actions', nargs='+', choices=ALL + ('capture-smoke',))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    base = private(args.base)
    if args.action == 'self-test':
        self_test()
    elif args.action == 'inventory':
        inventory(base, args.jobs)
        print(base / 'orchestration/inventory.json')
    elif args.action == 'prepare':
        if not args.candidate_source:
            parser.error('Provide the parent-confirmed --candidate-source')
        prepare(base, args.baseline_source.resolve(), args.candidate_source.resolve(), args.battery.resolve(), args.jobs)
    elif args.action == 'run':
        return run(base, args.actions or ALL, args.jobs)
    elif args.action == 'worker':
        if not args.actions or len(args.actions) != 1:
            parser.error('worker requires one --actions value')
        worker(base, args.actions[0], args.jobs)
    elif args.action == 'repair-dex':
        repair_dex(base, args.jobs)
    elif args.action == 'repair-host':
        repair_host(base)
    elif args.action == 'repair-capture':
        repair_capture(base, args.jobs)
    elif args.action == 'repair-capture-supplement':
        repair_capture_supplement(base, args.jobs)
    elif args.action == 'verify-repeat':
        verify_repeat(base, args.jobs)
    elif args.action == 'tower-context':
        tower_context(base)
    elif args.action == 'tower-cadence':
        tower_cadence(base)
    elif args.action == 'repair-tower':
        repair_tower(base, args.jobs)
    else:
        return audit(base)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
