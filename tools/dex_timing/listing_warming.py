"""Normal-input idle-work checks and paired Selected-entry display timing."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import statistics
import unittest

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, FRAME, move, predecessor, audit
from .description_ui import settle
from .info_ui import BOOT
from .listing_options import configuration
from .performance import result_timing


SPECIES = ('chikorita', 'eevee', 'ditto', 'unown_a', 'mewtwo', 'celebi',
           'dusknoir', 'weavile', 'garchomp', 'bronzong', 'seviper', 'spheal',
           'groudon', 'kyogre', 'rayquaza', 'metagross')
HOVERS = (0, 4, 30, 120)
PHASES = (0, FRAME // 4, FRAME // 2, 3 * FRAME // 4)
WORK_FIELDS = ('loaded', 'dictionary_services', 'upload_services', 'upload')


def enter_selection(driver, config, index):
    prior, direction = predecessor(index)
    if config['listing_style'] == 'legacy':
        prior, direction = (index - 1) % len(config['names']), 'down'
    driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
    driver.command('rawcolor')
    move(driver, direction, index)


def idle_case(task):
    config, index, output = task
    name = config['names'][index]
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                    Path(output) / f'{config["listing_style"]}-{name}.log')
    result = dict(species=name, presentation=config['listing_style'], issues=[])
    try:
        enter_selection(driver, config, index)
        before = driver.command('peek')
        driver.run(frames=120)
        after = driver.command('peek')
        result.update(before={key: before[key] for key in WORK_FIELDS},
                      after={key: after[key] for key in WORK_FIELDS})
        if result['before'] != result['after']:
            result['issues'].append('idle_animation_work')
        asset = Repository(ROOT, Path(config['rom']), Path(config['sym'])).load([name])[0]
        if after['loaded'] != asset.width ** 2 or after['dictionary_services'] or after['upload_services']:
            result['issues'].append('not_base_only_after_hover')
        if after['index'] != index or after['double_speed'] != 1:
            result['issues'].append('idle_owner_changed')
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
    finally:
        driver.close()
    return result


def entry_case(task):
    config, name, hover, phase, variant, output = task
    prefix = Path(output) / f'{variant}-{config["listing_style"]}-{name}-h{hover}-q{phase}'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], prefix.with_suffix('.log'))
    result = dict(species=name, presentation=config['listing_style'], hover=hover,
                  phase=phase, variant=variant, issues=[])
    try:
        index = config['names'].index(name)
        enter_selection(driver, config, index)
        if hover:
            driver.run(frames=hover)
        driver.command(f'run 0 {phase} 0')
        before = driver.command('peek')
        driver.command('audit 1')
        initial = driver.command('perf 1')
        driver.events.clear()
        accepted = driver.run(('accept', 'animation_miss', 'audio_miss'), key='a')
        if accepted['hit'] != 'accept' or accepted['index'] != index:
            raise RuntimeError('A was not accepted on the intended species')
        final = settle(driver)
        driver.run(frames=3)
        rendered = driver.command('perf 0')
        events = list(driver.events)
        asset = Repository(ROOT, Path(config['rom']), Path(config['sym'])).load([name])[0]
        playback = audit(asset, accepted, events, final,
                         cold=variant == 'candidate', expected_double_speed=1)
        result['issues'] += playback['issues']
        result.update(playback=playback,
                      before={key: before[key] for key in WORK_FIELDS},
                      timing=result_timing(events, initial, rendered, 'stable',
                                           initial['t'], accepted['t'], first_key='lower'))
        for metric in ('first_visible', 'complete_visible'):
            if result['timing'][metric] is None:
                result['issues'].append('missing_' + metric)
        prefix.with_suffix('.events.json').write_text(json.dumps(events) + '\n')
        if variant == 'candidate' and hover == 120 and phase == 0 and name in ('chikorita', 'groudon'):
            driver.command(f'image {prefix}.ppm')
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
        driver.evidence(prefix.with_suffix('.failure'))
    finally:
        driver.close()
    return result


def summarize(rows):
    pairs = {}
    for row in rows:
        key = row['presentation'], row['species'], row['hover'], row['phase']
        pairs.setdefault(key, {})[row['variant']] = row
    summaries = []
    for presentation in ('modern', 'legacy'):
        for hover in HOVERS:
            matched = [value for key, value in pairs.items() if key[0] == presentation and key[2] == hover]
            summary = dict(presentation=presentation, hover=hover, pairs=len(matched), metrics={})
            for metric in ('first_visible', 'complete_visible'):
                baseline = [pair['baseline']['timing'][metric]['ms'] for pair in matched]
                candidate = [pair['candidate']['timing'][metric]['ms'] for pair in matched]
                deltas = [b - a for a, b in zip(baseline, candidate)]
                worst = max(zip(deltas, matched), key=lambda item: item[0])
                summary['metrics'][metric] = dict(baseline_median_ms=statistics.median(baseline),
                    candidate_median_ms=statistics.median(candidate), median_delta_ms=statistics.median(deltas),
                    maximum_delta_ms=worst[0], worst_species=worst[1]['candidate']['species'],
                    candidate_maximum_ms=max(candidate))
            summaries.append(summary)
    return summaries


def run(output, action, jobs):
    if action == 'qualify':
        return qualify(output)
    if action == 'host':
        return host_tests(output)
    target = output / ('entry-timing' if action == 'timing' else 'idle-proof')
    target.mkdir(exist_ok=True)
    configs = {variant: [configuration(path / 'dex-regression', style)
                         for style in ('modern', 'legacy')]
               for variant, path in (('baseline', output / 'baseline'), ('candidate', output))}
    if action == 'idle':
        tasks = [(config, index, str(target)) for config in configs['candidate']
                 for index in range(len(config['names']))]
        function = idle_case
    else:
        tasks = [(config, name, hover, phase, variant, str(target))
                 for variant, group in configs.items() for config in group
                 for name in SPECIES for hover in HOVERS for phase in PHASES]
        function = entry_case
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(function, tasks):
            rows.append(row)
            if len(rows) % 100 == 0 or row['issues']:
                print(json.dumps(dict(done=len(rows), total=len(tasks), issues=row['issues'])), flush=True)
    result = dict(action=action, cases=len(rows), failures=sum(bool(row['issues']) for row in rows), rows=rows,
                  rom_sha256=sha256((output / 'pokecrystal-dex-no-warming.gbc').read_bytes()))
    if action == 'timing' and not result['failures']:
        result['summary'] = summarize(rows)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}), flush=True)
    if result['failures']:
        raise AssertionError('Listing warming trial has unresolved failures')


def host_tests(output):
    from tools import test_dex_scheduler, test_listing_warming
    test_dex_scheduler.ROOT = output / 'candidate'
    test_listing_warming.OUTPUT = output
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)
                               for module in (test_dex_scheduler, test_listing_warming))
    with (output / 'current-host.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    if result.testsRun != 21 or not result.wasSuccessful():
        raise AssertionError('Current host contracts failed; see current-host.log')
    print(json.dumps(dict(cases=result.testsRun, failures=0)), flush=True)


def qualify(output):
    from .performance_audio import compare_playback
    manifest = json.loads((output / 'no-warming-manifest.json').read_text())
    digest = sha256((output / 'pokecrystal-dex-no-warming.gbc').read_bytes())
    if digest != manifest['rom_sha256']:
        raise AssertionError('Prototype ROM changed after build')
    expected_counts = {
        'dex-regression/summary.json': 4479,
        'idle-proof/summary.json': 746,
        'entry-timing/summary.json': 1024,
        'search-tests/filter.json': 1692,
        'search-tests/ui.json': 10,
        'search-tests/visual/summary.json': 1406,
        'search-tests/navigation/summary.json': 2686,
        'search-tests/transitions/summary.json': 11,
        'search-tests/surrounding/summary.json': 2,
        'search-tests/form-polish/summary.json': 1284,
        'search-tests/naming-cursor/summary.json': 3840,
        **{f'acquisition-{kind}-regression.json': count for kind, count in
           (('menus', 10), ('gameplay', 22), ('custom', 2),
            ('transitions', 24), ('moves', 1600), ('audio', 960))},
    }
    reports = {}
    for name in ('dex-regression/summary.json', 'playback-modern/summary.json',
                 'playback-legacy/summary.json', 'idle-proof/summary.json', 'entry-timing/summary.json',
                 'search-tests/filter.json', 'search-tests/ui.json', 'search-tests/visual/summary.json',
                 'search-tests/navigation/summary.json', 'search-tests/transitions/summary.json',
                 'search-tests/surrounding/summary.json', 'search-tests/form-polish/summary.json',
                 'search-tests/naming-cursor/summary.json',
                 *(f'acquisition-{kind}-regression.json' for kind in
                   ('menus', 'gameplay', 'custom', 'transitions', 'moves', 'audio'))):
        path = output / name
        record = json.loads(path.read_text())
        if name in expected_counts and record.get('cases') != expected_counts[name]:
            raise AssertionError(f'Incomplete suite: {name}')
        if record.get('failures') or record.get('issues'):
            raise AssertionError(f'Unresolved suite: {name}')
        summaries = record.get('summary')
        if isinstance(summaries, dict) and any(row.get('failures') for row in summaries.values()):
            raise AssertionError(f'Unresolved playback suite: {name}')
        if name.startswith('playback-') and summaries != {
            kind: dict(cases=373, failures=0) for kind in ('cold', 'paging', 'warm')
        }:
            raise AssertionError(f'Incomplete playback suite: {name}')
        if record.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Suite uses a different ROM: {name}')
        reports[name] = dict(sha256=sha256(path.read_bytes()), cases=record.get('cases'), issues=[])
    audio = json.loads((output / 'acquisition-audio-regression.json').read_text())['results']
    if len(audio) != 960:
        raise AssertionError('Incomplete sampled-cry campaign')
    before = {(row['species'], row['context'], row['quarter']): row for row in audio[:480]}
    for row in audio[480:]:
        if compare_playback(before[row['species'], row['context'], row['quarter']], row):
            raise AssertionError('Sampled playback differs from production')
    def misses(rows):
        return sorted((row['species'], row['context'], row['quarter'], miss['remaining'])
                      for row in rows for miss in row['known_misses'])
    if misses(audio[:480]) != misses(audio[480:]):
        raise AssertionError('Known sampled-cry warnings changed')
    battle = json.loads((output / 'acquisition-moves-regression.json').read_text())['results']
    before = {(row['move'], row['side'], row['quarter']): row for row in battle if row['variant'] == 'baseline'}
    deltas = [row['requested_animations'][0]['elapsed_t'] -
              before[row['move'], row['side'], row['quarter']]['requested_animations'][0]['elapsed_t']
              for row in battle if row['variant'] == 'acquisition']
    if len(deltas) != 800 or any(deltas):
        raise AssertionError('Battle animation timing changed')
    custom = json.loads((output / 'acquisition-custom-regression.json').read_text())['results']
    before = {row['label']: row for row in custom[0]['rows']}
    for row in custom[1]['rows']:
        for key in ('palette_set', 'pixel_set', 'oam_set'):
            if row[key] != before[row['label']][key]:
                raise AssertionError('Custom menu presentation changed')
    protected, status_notes = 0, []
    for name, expected in manifest['protected_inputs'].items():
        current = sha256(Path(name).read_bytes())
        if current != expected:
            if Path(name).relative_to(ROOT).as_posix() not in (
                'docs/index.md', 'docs/pokedex_selected_bug_backlog.md'
            ):
                raise AssertionError(f'Protected production input changed: {name}')
            status_notes.append(dict(path=name, before=expected, after=current))
        else:
            protected += 1
    def resources(path):
        return {name: int(value) for name, value in re.findall(
            r'^\s*(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used', path.read_text(), re.M)}
    previous = resources(output / 'baseline/pokecrystal-dex-no-warming.map')
    current = resources(output / 'pokecrystal-dex-no-warming.map')
    delta = {name: current[name] - previous[name] for name in current}
    if delta != dict(ROM0=0, ROMX=-58, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0):
        raise AssertionError('Unexpected resource change')
    timing = json.loads((output / 'entry-timing/summary.json').read_text())
    historical = json.loads((output / 'historical-host-comparison.json').read_text())
    if not historical['identical'] or historical['records']['baseline'] != historical['records']['candidate']:
        raise AssertionError('Missing host evidence')
    host = (output / 'current-host.log').read_text()
    if '\nOK\n' not in host or 'Ran 21 tests' not in host:
        raise AssertionError('Current host contracts failed')
    record = dict(rom_sha256=digest, baseline_sha256=manifest['baseline_rom_sha256'],
                  resources=current, delta=delta,
                  reports=reports, entry_timing=timing['summary'], protected_inputs=protected,
                  intentional_status_notes=status_notes, production_unchanged=True,
                  host_contracts=21, historical_host_comparison=historical,
                  historical_checks_not_current_acceptance=True,
                  paired_audio_captures=480, known_sampled_cry_warnings_per_build=len(misses(audio[:480])),
                  paired_battle_animations=len(deltas), battle_duration_delta_cycles=[min(deltas), max(deltas)],
                  custom_menu_visuals_unchanged=True, issues=[])
    (output / 'no-warming-qualification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ('reports', 'entry_timing', 'historical_host_comparison')}), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('idle', 'timing', 'host', 'qualify'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    run(args.output.resolve(), args.action, args.jobs)
