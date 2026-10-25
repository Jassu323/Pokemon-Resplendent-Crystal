"""Replay unresolved Dex reports on the current, unchanged production link."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from . import performance, listing_restoration, backlog_revalidation
from .assets import Repository, sha256
from .cold_listing import ROOT, Driver, move, predecessor, audit as playback_audit
from .cry_ownership import validate_output
from .description_paging import description_pages
from .description_ui import audit as description_audit, settle, settle_description_text
from .info_ui import BOOT, press
from .listing_options import configuration
from .selected_runtime import stress_case


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def tab_case(task):
    config, source, target, age, phase = task
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    label = f'{source}-{target}-age{age}-q{phase}-{config["listing_style"]}'
    folder = Path(config['output']) / label
    folder.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], folder / 'core.log')
    row = dict(source=source, target=target, age=age, phase=phase,
               style=config['listing_style'], source_view=config.get('source_view', 1), issues=[])
    try:
        index = config['names'].index(source)
        prior, direction = predecessor(index)
        if config['listing_style'] == 'legacy':
            prior, direction = (index - 1) % len(config['names']), 'down'
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.command('audit 1')
        driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        settle(driver)
        performance.view(driver, repo, source, config.get('source_view', 1))
        driver.run(frames=2)
        driver.events.clear()
        incoming = driver.run(('change_species',), key='down')
        row['incoming_accepted'] = incoming
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        if incoming['selected_index'] not in (index, config['names'].index(target)):
            row['issues'].append('unexpected_source')
        if driver.command('peek')['selected_index'] != config['names'].index(target):
            raise RuntimeError('Internal paging did not reach the declared target')
        if age == 'settled':
            settle(driver)
        else:
            driver.run(('animation_miss', 'audio_miss'), frames=int(age))
        for _ in range(config.get('source_view', 1)):
            press(driver, 'left')
        if phase:
            performance.cycles(driver, phase)
        row['playback_at_request'] = driver.command('peek')
        driver.command(f'image {folder / "before.ppm"}')
        initial = driver.command('perf 1')
        playback_prefix = list(driver.events)
        driver.events.clear()
        accepted = driver.run(('footer_accept', 'animation_miss', 'audio_miss'), key='a')
        if accepted['hit'] != 'footer_accept':
            raise RuntimeError('Description activation was not accepted')
        driver.run(('animation_miss', 'audio_miss'), frames=1)
        if config.get('uncaught'):
            for _ in range(600):
                ui = driver.command('ui')
                if ui['view'] == 0 and not ui['owner_transition'] and not ui.get('description_state', 0):
                    break
                driver.run(('animation_miss', 'audio_miss'), frames=1)
            else:
                raise RuntimeError('Uncaught Description did not publish')
            if ui['caught']:
                row['issues'].append('uncaught_fixture_lost')
        else:
            settle_description_text(driver, description_pages(repo, target)[0])
        row['playback_at_ready'] = driver.command('peek')
        ui = driver.command('ui')
        row['issues'] += description_audit(repo, ui)
        if ui['view'] != 0:
            row['issues'].append('description_owner')
        driver.run(('animation_miss', 'audio_miss'), frames=2)
        # VRAM readiness can precede the next visible frame. Capture after scanout.
        driver.command(f'image {folder / "after.ppm"}')
        trace = list(driver.events)
        final = driver.command('perf 0')
        row.update(performance.result_timing(trace, initial, final, 'lower', initial['t'], accepted['t']))
        row['request_accept_ms'] = (accepted['t'] - initial['t']) * 1000 / 4194304
        row['request_accept_frames'] = (accepted['t'] - initial['t']) / 70224
        write(folder / 'trace.json', trace)
        finished = settle(driver)
        row['playback_final'] = finished
        playback_events = playback_prefix + driver.events
        row['audio_stops'] = [e for e in playback_events if e['event'] == 'audio_stop']
        if config.get('exact_playback'):
            row['playback_audit'] = playback_audit(repo.load([target])[0], incoming,
                playback_events, finished, cold=False, expected_double_speed=1)
            row['issues'] += row['playback_audit']['issues']
        row['issues'] += [e['event'] for e in driver.events
                          if e['event'] in ('animation_miss', 'audio_miss')]
    except Exception as error:
        row['issues'].append(str(error))
        driver.evidence(folder / 'failure')
    finally:
        driver.close()
    write(folder / 'report.json', row)
    return row


def return_case(task):
    config, case = task
    folder = Path(config['output']) / case['label']
    folder.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], folder / 'core.log')
    reference = Driver(config['core'], config['rom'], BOOT, config['battery'], folder / 'reference.log')
    try:
        result = listing_restoration.run_case(driver, Path(config['states']).parent,
                                             Path(config['output']), case, config['names'], False)
        trace = backlog_revalidation.events(folder / 'trace')
        expected = backlog_revalidation.exact_listing_reference(reference, Path(config['states']).parent,
            trace[-1], len(config['names']), folder / 'independent')
        result['historical_reports'] = backlog_revalidation.check_return_frames(repo, trace, expected)
        result['follow_up'] = listing_restoration.follow_up(driver, reference,
            Path(config['states']).parent, folder / 'follow-up', len(config['names']),
            require_lookahead=False)
        result['issues'] = (result['restoration_failures'] + result['historical_reports']['issues']
                            + result['follow_up']['issues'])
        row = dict(case=case, issues=result['issues'],
                   historical_reports=result['historical_reports'],
                   blocked_writes=result['follow_up']['blocked_navigation_palette_writes'])
        write(folder / 'report.json', result)
    except Exception as error:
        row = dict(case=case, issues=[str(error)])
        driver.evidence(folder / 'failure')
    finally:
        driver.close()
        reference.close()
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('badges', 'tabs', 'returns'))
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    args.output = validate_output(args.output, [args.source, ROOT / 'pokecrystal.gbc',
                                               ROOT / 'pokecrystal.sym'])
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / 'summary.json').exists():
        raise ValueError('Use a fresh output directory; preserve prior attempts')
    configs = {style: configuration(args.source / 'focused', style) for style in ('modern', 'legacy')}
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    protected = [ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map',
                 Path('/Applications/SameBoy/Games/pokecrystal.sav')]
    before = {str(path): sha256(path.read_bytes()) for path in protected}
    for style, config in configs.items():
        linked = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        if linked.hashes != config['hashes'] or linked.hashes != repo.hashes:
            raise ValueError('Checkpoint provenance does not match current production')
        config['output'] = str(args.output)
    if args.phase == 'badges':
        config = configs['modern']
        ages = (*map(str, range(13)), '16', '24', '32', 'settled')
        tasks = [(config, config['names'].index(name), name, age, 'description')
                 for name in ('rhyperior', 'dusknoir', 'weavile', 'chikorita', 'eevee', 'tyrogue')
                 for age in ages]
        worker = stress_case
    elif args.phase == 'tabs':
        tasks = [(config, source, target, age, phase)
                 for config in configs.values()
                 for source, target in (('dusclops', 'dusknoir'), ('abomasnow', 'weavile'),
                                        ('grovyle', 'sceptile'), ('bayleef', 'meganium'))
                 for age in ('0', '8', '32', 'settled')
                 for phase in (0, 17556, 35112, 52668)]
        worker = tab_case
    else:
        target = args.output / 'restore-core'
        target.mkdir(exist_ok=True)
        config = dict(configs['modern'], core=str(listing_restoration.compile_observer(
            repo, Path.home() / 'Documents/GitHub/SameBoy', target,
            extra_fields=('wPokedexRenderedSelectionKey',),
            extra_flags=('-DDEX_BACKLOG_REVALIDATION_TRACE',))))
        cases = listing_restoration.cases(config['names'])
        tasks = [(config, dict(case, label=case['label'] + f'-repeat{repeat}'))
                 for case in cases for repeat in range(3)]
        worker = return_case
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(worker, tasks):
            rows.append(row)
            if row['issues'] or len(rows) % 20 == 0:
                print(json.dumps(dict(phase=args.phase, done=len(rows), issues=row['issues'])), flush=True)
    after = {str(path): sha256(path.read_bytes()) for path in protected}
    result = dict(phase=args.phase, cases=len(rows), failures=sum(bool(r['issues']) for r in rows),
                  hashes=repo.hashes, protected_inputs_unchanged=before == after, rows=rows)
    write(args.output / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2), flush=True)
    return int(bool(result['failures']) or before != after)


if __name__ == '__main__':
    raise SystemExit(main())
