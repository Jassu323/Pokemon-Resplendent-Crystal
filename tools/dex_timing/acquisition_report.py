"""Retain stage-two review files and verify the completed native qualification."""
import argparse
import importlib
import json
import os
from pathlib import Path
import statistics
import unittest

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, bootstrap
from . import shared_menu_regression as menu
from .acquisition_regression import configurations
from .global_custom_menus import metric
from .move_persistence import boot, call, core, read
from .move_acquisition import expected_migration, owned_indices
from .shared_menu_fixtures import make_fixture
from move_discovery_assets import decode_record


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def popup_readiness(output, baseline):
    records = []
    for config in configurations(output, baseline):
        name = config['variant']
        repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
        source = output / 'runtime/menus' / name / 'standard'
        custom = output / 'runtime/custom-menus' / name
        driver = Driver(custom / 'cold-listing-core', config['rom'], menu.BOOT,
                        source / 'private.sav', custom / 'readiness.log')
        rows = []
        try:
            tasks = [(source / f'pack-pocket-{n}.s0', key, f'pack-{n}-{key}')
                     for n in range(5) for key in ('a', 'start')]
            tasks += [(custom / f'apricorn-{n}.s0', 'a', f'apricorn-{n}-a') for n in range(7)]
            tasks += [(custom / f'tmhm-{n}.s0', 'a', f'tmhm-{n}-a') for n in range(57)]
            for checkpoint, key, label in tasks:
                driver.command(f'load {checkpoint}')
                menu.run(driver, repo, frames=4)
                start = driver.command('m')['t']
                final = menu.run(driver, repo, 'StaticMenuJoypad', 96, menu.KEY[key])
                if not menu.at(final, repo, 'StaticMenuJoypad'):
                    raise AssertionError(f'Popup input owner not reached: {name}/{label}')
                rows.append(dict(label=label, ready=metric(final['t'], start), final=final))
        finally:
            driver.close()
        records.append(dict(variant=name, rows=rows))
    previous = {row['label']: row for row in records[0]['rows']}
    differences = [dict(label=row['label'],
                        delta_frames=row['ready']['frames'] - previous[row['label']]['ready']['frames'],
                        delta_ms=row['ready']['ms'] - previous[row['label']]['ready']['ms'])
                   for row in records[1]['rows']]
    result = dict(cases=sum(len(r['rows']) for r in records), records=records,
                  differences=differences,
                  summary={field: dict(min=min(r[field] for r in differences),
                                       median=statistics.median(r[field] for r in differences),
                                       max=max(r[field] for r in differences))
                           for field in ('delta_frames', 'delta_ms')},
                  definition='Press to StaticMenuJoypad after popup construction/publication, not a late pixel-hash set.',
                  issues=[])
    write_json(output / 'acquisition-popup-readiness.json', result)
    return result


def review_save(output):
    stem = json.loads((output / 'moves-mode-manifest.json').read_text())['stem']
    repo = Repository(output / 'candidate', output / f'{stem}.gbc', output / f'{stem}.sym')
    target = output / 'manual-review'
    target.mkdir(exist_ok=True)
    source = target / 'legacy-convenience.sav'
    make_fixture(repo, output / 'legacy-input.sav', source)
    expected = expected_migration(source.read_bytes(), repo.symbols)
    config = dict(rom=str(repo.rom_path), symbols=repo.symbols, core=str(core(output, target_root=target)))
    driver = boot(config, source, target / 'migration-and-save.log')
    battery = output / f'{stem}.sav'
    try:
        if read(driver, repo.symbols)[:64] != expected:
            raise AssertionError('Manual save migration did not match independent owned-move decoder')
        call(driver, repo.symbols, 'SaveGameData')
        if driver.command(f'battery {battery}')['error']:
            raise AssertionError('Could not export the native saved battery')
    finally:
        driver.close()
    for prefix in ('s', 'sBackup'):
        if decode_record(battery.read_bytes(), repo.symbols, prefix) != dict(status='valid', bitmap=expected):
            raise AssertionError(f'Manual review {prefix} extension invalid')
    driver = boot(config, battery, target / 'cold-reload.log')
    try:
        if read(driver, repo.symbols)[:64] != expected:
            raise AssertionError('Manual review discoveries changed after cold reload')
    finally:
        driver.close()
    indices = owned_indices(source.read_bytes(), repo.symbols)
    result = dict(rom_sha256=sha256(repo.rom_path.read_bytes()),
                  save=str(battery), save_sha256=sha256(battery.read_bytes()),
                  naturally_discovered=indices, all_tms_hms=True,
                  apricorns_each=10, rare_candies=76, unown_unlocked=True,
                  seeded_discovery_bits=False, issues=[])
    write_json(output / 'manual-review.json', result)
    manifest_path = output / 'moves-mode-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update(manual_review_seen=indices, manual_review_save_sha256=result['save_sha256'])
    write_json(manifest_path, manifest)
    from .moves_mode import enter, state, audit, capture
    from .info_ui import press
    cfg = json.loads((output / 'modern/config.json').read_text())
    driver = Driver(cfg['core'], cfg['rom'], menu.BOOT, battery, target / 'moves-ui.log')
    try:
        bootstrap(driver)
        enter(driver, repo)
        fixture = dict(manifest, fixture='mixed', unknown=[n for n in range(1, 334) if n not in indices])
        audit(driver, repo, fixture)
        capture(driver, target / 'unseen-entry.png')
        selected = next(n for n in manifest['orders'][0] if n in indices)
        for _ in range(333):
            if state(driver, repo)['selected'] == selected:
                break
            press(driver, 'down')
        else:
            raise AssertionError('Manual review could not navigate to a known move')
        audit(driver, repo, fixture)
        capture(driver, target / 'known-entry.png')
    finally:
        driver.close()
    return result


def qualify(output):
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    digest = sha256((output / (manifest['stem'] + '.gbc')).read_bytes())
    if digest != manifest['rom_sha256']:
        raise AssertionError('Review ROM differs from the qualified link')
    if sha256((output / (manifest['stem'] + '.sav')).read_bytes()) != manifest['manual_review_save_sha256']:
        raise AssertionError('Natural review save differs from its qualified hash')
    names = ['persistence-qualification.json', 'acquisition-qualification.json',
             'acquisition-sources.json', 'acquisition-migration.json',
             'acquisition-migration-interruptions.json', 'acquisition-performance.json',
             'acquisition-popup-readiness.json', 'manual-review.json',
             'moves-mode-qualification/summary.json', 'scrollbar-visual/summary.json',
             'scrollbar-mixed/summary.json', 'regression-modern/summary.json',
             'regression-modern-warm/summary.json', 'regression-legacy/summary.json',
             'integration/summary.json', 'modal-qualification/summary.json',
             'search-qualification/summary.json', 'search-stress/summary.json',
             'search-sparse/summary.json', 'search-default-empty/summary.json',
             'search-results-qualification/summary.json', 'search-results-badges/summary.json',
             'search-listing-returns/summary.json', 'mode-transitions/summary.json']
    names += [f'acquisition-{name}-regression.json' for name in
              ('menus', 'gameplay', 'moves', 'audio', 'transitions', 'custom')]
    if manifest['persistence_stage'] == 3:
        names += ['battle-use-qualification.json', 'battle-use/supplemental-bide.json',
                  'battle-review/review.json']
    reports = {}
    records = {}
    for name in names:
        path = output / name
        data = path.read_bytes()
        record = json.loads(data)
        if record.get('issues') or record.get('failures'):
            raise AssertionError(f'Qualification failed: {name}')
        if record.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Qualification used a different ROM: {name}')
        if any(r['failures'] for r in record.get('summary', {}).values()
               if isinstance(r, dict) and 'failures' in r):
            raise AssertionError(f'Suite failure: {name}')
        records[name] = record
        fields = ('cases', 'page_cases', 'interface_cases', 'interface_checks', 'transitions',
                  'helper_cases', 'snapshot_cases', 'cold_boot_cases', 'lifecycle_cases',
                  'interrupted_write_cases', 'interrupted_repair_cases', 'failures', 'issues')
        reports[name] = dict(sha256=sha256(data), summary={k: record[k] for k in fields if k in record})
    for path, expected in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != expected:
            raise AssertionError(f'Protected production/rollback artifact changed: {path}')
    for style in ('modern', 'legacy'):
        cfg = json.loads((output / style / 'config.json').read_text())
        if cfg['hashes']['rom_sha256'] != digest:
            raise AssertionError('Dex checkpoints do not match the final link')
    for name in ('MOVE_DISCOVERY_BUILD', 'DEX_MOVES_MODE_BUILD', 'DEX_OPTIONS_BUILD', 'DEX_SEARCH_BUILD'):
        os.environ[name] = str(output)
    test_names = [
        'tools.test_move_discovery', 'tools.test_move_acquisition', 'tools.test_pokedex_moves_mode',
        'tools.test_pokedex_moves', 'tools.test_pokedex_sort', 'tools.test_pokedex_search_results']
    if manifest['persistence_stage'] == 3:
        test_names += ['tools.test_move_battle_use', 'tools.test_dex_scheduler',
                       'tools.test_dex_cold_listing', 'tools.test_dex_target_regression',
                       'tools.test_new_dex_entry']
    relocated = []
    if manifest['persistence_stage'] == 3:
        for name in ('tools.test_dex_scheduler', 'tools.test_new_dex_entry'):
            module = importlib.import_module(name)
            relocated.append((module, module.ROOT))
            module.ROOT = output / 'candidate'
    try:
        suite = unittest.defaultTestLoader.loadTestsFromNames(test_names)
        host = unittest.TextTestRunner().run(suite)
    finally:
        for module, original in relocated:
            module.ROOT = original
    if not host.wasSuccessful():
        raise AssertionError('Final host tests failed')
    from .moves_scrollbar import pixel_audit
    pixels = pixel_audit(output, Repository(ROOT, output / (manifest['stem'] + '.gbc'),
                                           output / (manifest['stem'] + '.sym')))
    current = records['moves-mode-qualification/summary.json']
    baseline = Path(manifest['source'])
    old = json.loads((baseline / 'moves-mode-qualification/summary.json').read_text())
    previous = {(r['presentation'], r['phase']): r['transitions'] for r in old['interfaces']}
    latency = {}
    for name in current['interfaces'][0]['transitions']:
        latency[name] = {}
        for field in ('first_frames', 'complete_frames'):
            values = [r['transitions'][name][field] - previous[r['presentation'], r['phase']][name][field]
                      for r in current['interfaces']]
            latency[name][field] = dict(min=min(values), median=statistics.median(values), max=max(values))
    audio = records['acquisition-audio-regression.json']['results']
    def known(rows):
        return sorted((r['species'], r['context'], r['quarter'], m['remaining'])
                      for r in rows for m in r['known_misses'])
    before, after = known(audio[:len(audio) // 2]), known(audio[len(audio) // 2:])
    if before != after:
        raise AssertionError('Sampled cry known misses differ from the accepted baseline')
    moves = records['acquisition-moves-regression.json']['results']
    motion = {(r['move'], r['side'], r['quarter']): r for r in moves if r['variant'] == 'baseline'}
    differences = [(r['requested_animations'][0]['elapsed_t'] -
                    motion[r['move'], r['side'], r['quarter']]['requested_animations'][0]['elapsed_t']) / 70224
                   for r in moves if r['variant'] == 'acquisition']
    custom = records['acquisition-custom-regression.json']['results']
    old_custom = {r['label']: r for r in custom[0]['rows']}
    custom_delta = {}
    for field in ('first', 'complete'):
        values = [r[field]['frames'] - old_custom[r['label']][field]['frames']
                  for r in custom[1]['rows'] if r[field] and old_custom[r['label']][field]]
        custom_delta[field] = dict(min=min(values), median=statistics.median(values), max=max(values))
    result = dict(rom_sha256=digest, save_sha256=manifest['manual_review_save_sha256'],
                  reports=reports, host_tests=host.testsRun, host_skipped=len(host.skipped),
                  scrollbar_pixel_audit=pixels, latency_delta_display_intervals=latency,
                  acquisition_hooks=True, battle_use_hooks=manifest['battle_use_hooks'], legacy_bootstrap=True,
                  sampled_cry_known_misses=dict(baseline=len(before), acquisition=len(after), same=True),
                  first_requested_animation_delta_intervals=dict(min=min(differences),
                      median=statistics.median(differences), max=max(differences)),
                  custom_menu_pixel_metric_delta_intervals=custom_delta,
                  production_unchanged=True, protected_inputs_checked=len(manifest['protected_inputs']),
                  issues=[])
    write_json(output / 'final-qualification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('readiness', 'review', 'final'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build output')
    if args.action == 'readiness':
        result = popup_readiness(output, args.baseline.resolve())
    elif args.action == 'review':
        result = review_save(output)
    else:
        result = qualify(output)
    print(json.dumps({k: v for k, v in result.items() if k not in ('reports', 'records', 'differences')}))


if __name__ == '__main__':
    main()
