"""Matched timing captures for five configured evolution lines, not regression."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics

from . import performance, cry_ownership, legacy_listing, listing_warming
from .assets import Repository
from .cold_listing import ROOT, Driver, bootstrap, move
from .description_ui import settle
from .info_ui import BOOT, ready, press, info_audit
from .selected_comparison import same_transition
from pokedex_info_assets import Compiler

LINES = {
    'Treecko': ('treecko', 'grovyle', 'sceptile'),
    'Torchic': ('torchic', 'combusken', 'blaziken'),
    'Mudkip': ('mudkip', 'marshtomp', 'swampert'),
    'Magnemite': ('magnemite', 'magneton', 'magnezone'),
    'Swinub': ('swinub', 'piloswine', 'mamoswine'),
}
SOURCES = {
    'production': ROOT / 'build/dex-selected-sampled-production-20261013-v1',
    'vram': ROOT / 'build/dex-selected-sampled-vram-20261013-v2',
}
PHASES = (0, 17556, 35112, 52668)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def config(source, style):
    value = json.loads((source / 'focused' / style / 'config.json').read_text())
    return dict(value, root=str(source / 'candidate'), cry_trace=True, listing_style=style)


def prepare(source):
    repo = Repository(source / 'candidate', source / 'pokecrystal-dex-selected-runtime.gbc',
                      source / 'pokecrystal-dex-selected-runtime.sym')
    out = source / 'focused/cry-timing-core'
    out.mkdir(parents=True, exist_ok=True)
    flags = cry_ownership.observer_flags(repo, out, {
        'info_request': repo.symbols['PokedexInfo_Activate'],
        'moves_request': repo.symbols['PokedexMoves_Activate'],
    })
    core = performance.core(repo, out, extra_flags=flags).resolve()
    for style in ('modern', 'legacy'):
        value = config(source, style)
        value['core'] = str(core)
        write(source / 'focused' / style / 'config.json', value)
    # Three-member batteries permit direct mixed-cry handoffs by normal Up/Down.
    for line, members in LINES.items():
        for style in ('modern', 'legacy'):
            folder = source / 'line-checkpoints' / line / style
            folder.mkdir(parents=True, exist_ok=True)
            value = config(source, style)
            battery = folder / 'private.sav'
            cry_ownership.sparse_fixture(repo, Path(value['battery']), battery, members)
            driver = Driver(core, value['rom'], BOOT, battery, folder / 'prepare.log')
            try:
                bootstrap(driver)
                if style == 'legacy':
                    legacy_listing.select_presentation(driver, 1)
                first = min(members, key=value['names'].index)
                target = value['names'].index(first)
                while driver.command('peek')['index'] != target:
                    current = driver.command('peek')['index']
                    if style == 'legacy':
                        direction = 'down' if current < target else 'up'
                    elif current // 3 != target // 3:
                        direction = 'down' if current // 3 < target // 3 else 'up'
                    else:
                        direction = 'right' if current < target else 'left'
                    move(driver, direction)
                    driver.run(('end_loop',))
                    driver.run(('end_loop',))
                driver.run(('accept',), key='a')
                driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
                press(driver, 'right')
                press(driver, 'a')
                for name in sorted(members, key=value['names'].index):
                    if driver.command('peek')['selected_index'] != value['names'].index(name):
                        driver.run(('change_species',), key='down')
                        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
                    ready(driver, 0)
                    settle(driver)
                    driver.run(frames=2)
                    if driver.command('peek')['selected_index'] != value['names'].index(name):
                        raise RuntimeError('Line fixture did not select the expected species')
                    driver.command(f'save {folder / (name + ".s0")}')
            finally:
                driver.close()
            write(folder / 'config.json', dict(value, battery=str(battery), line=line,
                                               members=sorted(members, key=value['names'].index),
                                               selected_states=str(folder)))
            print(json.dumps(dict(prepared_line=line, style=style, source=source.name)), flush=True)


def cry_kind(snapshot):
    if snapshot['audio'] and snapshot['remaining']:
        return 'sampled'
    if any(flags & 0x21 == 0x21 for flags in snapshot['sfx_flags']):
        return 'synthesized'
    return 'inactive'


def cry_summary(path, pressed):
    trace = [json.loads(line) for line in path.read_text().splitlines()]
    request = next((row for row in trace if row['t'] >= pressed and
                    row['phase'] in ('info_request', 'moves_request', 'change', 'leave')), None)
    durations = []
    for start in (row for row in trace if row['phase'] == 'sample_arm'):
        stop = next((row for row in trace if row['t'] > start['t'] and row['phase'] == 'sample_stop'
                     and row['audio']), None)
        if stop:
            durations.append(dict(ms=(stop['t'] - start['t']) * 1000 / 4194304,
                                  natural=not stop['remaining'], blocks=start['remaining'],
                                  bank=start['sample_bank']))
    synthesized = []
    for start in (row for row in trace if row['phase'] == 'synth_start'):
        active = next((row for row in trace if row['t'] > start['t'] and
                       cry_kind(row) == 'synthesized'), None)
        stop = next((row for row in trace if active and row['t'] > active['t'] and
                     cry_kind(row) != 'synthesized'), None)
        if stop:
            canceled = any(row['phase'] in ('change', 'leave', 'area') and
                           start['t'] < row['t'] <= stop['t'] for row in trace)
            synthesized.append(dict(ms=(stop['t'] - start['t']) * 1000 / 4194304,
                                    natural=not canceled))
    return dict(active_at_request=cry_kind(request) if request else None,
                request=request, sampled_playbacks=durations,
                synthesized_playbacks=synthesized,
                starvation_events=sum(row['phase'] == 'sample_empty' and bool(row['remaining'])
                                      for row in trace))


def page_case(task):
    variant, line, job = task
    cfg, name, action, phase, page, q = job
    row = dict(performance.run_case(job), variant=variant, line=line, style=cfg['listing_style'])
    repo, _, data = performance.data(cfg['rom'], cfg['sym'], cfg['root'])
    row['cry_kind'] = 'sampled' if repo.load([name])[0].sample_blocks else 'synthesized'
    label = f'{name}-{action}-{phase}-p{page}-q{q}'
    trace = Path(cfg['output']) / 'measurements' / (label + '-cry.jsonl')
    if row.get('initial_hashes') and trace.exists():
        row['cry_capture'] = cry_summary(trace, row['initial_hashes']['t'])
    if action == 'cycle':
        destination = (page + 1) % (1 + len(data['pages'][name.upper()]))
        row['destination_page'] = destination
        row['destination_heading'] = data['headings'][name.upper()][destination]
    return row


def transition_case(task):
    variant, cfg, source, target, phase, q = task
    folder = Path(cfg['output'])
    label = f'{source}-{target}-{phase}-q{q}'
    driver = Driver(cfg['core'], cfg['rom'], BOOT, cfg['battery'], folder / (label + '.log'))
    row = dict(variant=variant, style=cfg['listing_style'], line=cfg['line'], species=source,
               target=target, action='line-species', phase=phase, page=0, input_phase=q, issues=[])
    repo, compiler, data = performance.data(cfg['rom'], cfg['sym'], cfg['root'])
    try:
        members = cfg['members']
        predecessor = members[(members.index(source) - 1) % len(members)]
        driver.command(f'load {cfg["selected_states"]}/{predecessor}.s0')
        driver.command('rawcolor')
        driver.command('audit 1')
        cry_path = folder / (label + '-cry.jsonl')
        driver.command(f'crytrace {cry_path}')
        driver.run(('change_species',), key='down')
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        ready(driver, 0)
        if phase == 'settled':
            settle(driver)
        performance.cycles(driver, q)
        row['cry_at_input'] = driver.command('cry')
        initial = driver.command('perf 1')
        row['initial_hashes'] = initial
        driver.events.clear()
        key = 'down' if members.index(target) > members.index(source) else 'up'
        accepted = driver.run(('change_species', 'animation_miss', 'audio_miss'), key=key)
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        ready(driver, 0)
        row['ready_t'] = driver.command('peek')['t']
        if driver.command('peek')['selected_index'] != cfg['names'].index(target):
            raise RuntimeError('Line transition selected the wrong target')
        row['issues'] += info_audit(compiler, data, target, 0, driver.command('ui'), repo)
        driver.run(frames=2)
        events = list(driver.events)
        final = driver.command('perf 0')
        row.update(performance.result_timing(events, initial, final, 'stable', initial['t'],
                                             accepted['t'], first_key='full'))
        reveal = next((event for event in events if event['event'] == 'reveal'), None)
        row['static_reveal_ms'] = (reveal['t'] - initial['t']) * 1000 / 4194304 if reveal else None
        settle(driver)
        row['issues'] += [event['event'] for event in driver.events
                          if event['event'] in ('audio_miss', 'animation_miss')]
        driver.command('crystop')
        row['cry_capture'] = cry_summary(cry_path, initial['t'])
        row['status'] = 'pass' if not row['issues'] else 'fail'
        write(folder / (label + '-events.json'), driver.events)
    except Exception as error:
        row.update(status='error', error=str(error))
    finally:
        driver.close()
    row['cry_kind'] = 'sampled' if repo.load([source])[0].sample_blocks else 'synthesized'
    row['target_cry_kind'] = 'sampled' if repo.load([target])[0].sample_blocks else 'synthesized'
    write(folder / (label + '.json'), row)
    return row


def timings(variant, jobs, limit=None):
    source = SOURCES[variant]
    tasks = []
    for style in ('modern', 'legacy'):
        cfg = config(source, style)
        folder = source / 'sampled-timing' / style
        folder.mkdir(parents=True, exist_ok=True)
        cfg['output'] = str(folder)
        repo, _, data = performance.data(cfg['rom'], cfg['sym'], cfg['root'])
        for line, names in LINES.items():
            for name in names:
                count = 1 + len(data['pages'][name.upper()])
                actions = [('description-info', 0)]
                actions += [('cycle', page) for page in range(count)
                            if (page + 1) % count != 0]
                actions += [('listing', page) for page in range(count)
                            if data['headings'][name.upper()][page] != 'Evolves from']
                for action, page in actions:
                    tasks.extend((variant, line, (cfg, name, action, phase, page, q))
                                 for phase in ('0', 'settled') for q in PHASES)
    if limit:
        tasks = tasks[:limit]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(page_case, tasks):
            rows.append(row)
            if len(rows) % 80 == 0 or row['status'] != 'pass':
                print(json.dumps(dict(done=len(rows), cases=len(tasks), variant=variant,
                                      errors=sum(r['status'] != 'pass' for r in rows))), flush=True)
    write(source / 'sampled-timing/summary.json', dict(cases=len(rows), rows=rows))
    print(json.dumps(dict(cases=len(rows), errors=sum(r['status'] != 'pass' for r in rows))), flush=True)


def transitions(variant, jobs):
    source = SOURCES[variant]
    tasks = []
    for style in ('modern', 'legacy'):
        for line in LINES:
            cfg = json.loads((source / 'line-checkpoints' / line / style / 'config.json').read_text())
            folder = source / 'line-timing' / line / style
            folder.mkdir(parents=True, exist_ok=True)
            cfg['output'] = str(folder)
            for a, b in zip(cfg['members'], cfg['members'][1:]):
                tasks.extend((variant, cfg, first, second, phase, q)
                             for first, second in ((a, b), (b, a))
                             for phase in ('0', 'settled') for q in PHASES)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(transition_case, tasks))
    write(source / 'line-timing/summary.json', dict(cases=len(rows), rows=rows))
    print(json.dumps(dict(cases=len(rows), errors=sum(r['status'] != 'pass' for r in rows))), flush=True)


def distribution(values):
    return dict(cases=len(values), median=statistics.median(values),
                minimum=min(values), maximum=max(values)) if values else None


def comparison():
    rows = {}
    data = {}
    for variant, source in SOURCES.items():
        rows[variant] = []
        for folder in ('sampled-timing', 'line-timing'):
            found = json.loads((source / folder / 'summary.json').read_text())['rows']
            # Recompute trace summaries so capture analysis can improve without rerunning.
            for row in found:
                style, line = row['style'], row['line']
                if folder == 'sampled-timing':
                    label = f'{row["species"]}-{row["action"]}-{row["phase"]}-p{row["page"]}-q{row["input_phase"]}'
                    path = source / folder / style / 'measurements' / (label + '-cry.jsonl')
                else:
                    label = f'{row["species"]}-{row["target"]}-{row["phase"]}-q{row["input_phase"]}'
                    path = source / folder / line / style / (label + '-cry.jsonl')
                if row.get('initial_hashes') and path.exists():
                    row['cry_capture'] = cry_summary(path, row['initial_hashes']['t'])
            rows[variant].extend(found)
        repo, compiler, data[variant] = performance.data(
            str(source / 'pokecrystal-dex-selected-runtime.gbc'),
            str(source / 'pokecrystal-dex-selected-runtime.sym'), str(source / 'candidate'))
    key = lambda row: tuple(row.get(k) for k in
                           ('style', 'species', 'target', 'action', 'phase', 'page', 'input_phase'))
    baseline = {key(row): row for row in rows['production']}
    paired, extra, failed = [], [], []
    for row in rows['vram']:
        old = baseline.get(key(row))
        if row['status'] != 'pass' or old and old['status'] != 'pass':
            failed.append(dict(candidate=row, baseline=old))
            continue
        if old is None or not same_transition(row, data['production'], data['vram']):
            extra.append(row)
            continue
        first = old['cry_capture']['active_at_request']
        second = row['cry_capture']['active_at_request']
        record = dict(style=row['style'], species=row['species'], target=row.get('target'),
                      line=row['line'], action=row['action'], page=row['page'], phase=row['phase'],
                      input_phase=row['input_phase'], cry_kind=row['cry_kind'],
                      target_cry_kind=row.get('target_cry_kind'),
                      production_cry_at_request=first, vram_cry_at_request=second,
                      matched_cry_state=first == second, timings={}, cry_duration_delta={})
        for metric in ('first_visible', 'complete_visible'):
            if old.get(metric) and row.get(metric):
                record['timings'][metric] = dict(production_ms=old[metric]['ms'],
                    vram_ms=row[metric]['ms'], delta_ms=row[metric]['ms'] - old[metric]['ms'])
        if old.get('ready_t') and row.get('ready_t'):
            previous = (old['ready_t'] - old['initial_hashes']['t']) * 1000 / 4194304
            current = (row['ready_t'] - row['initial_hashes']['t']) * 1000 / 4194304
            record['timings']['owner_ready'] = dict(production_ms=previous, vram_ms=current,
                                                   delta_ms=current - previous)
        if old.get('static_reveal_ms') is not None and row.get('static_reveal_ms') is not None:
            record['timings']['static_reveal'] = dict(production_ms=old['static_reveal_ms'],
                vram_ms=row['static_reveal_ms'], delta_ms=row['static_reveal_ms'] - old['static_reveal_ms'])
        for kind in ('sampled', 'synthesized'):
            before = [p for p in old['cry_capture'][kind + '_playbacks'] if p['natural']]
            after = [p for p in row['cry_capture'][kind + '_playbacks'] if p['natural']]
            if len(before) == len(after):
                record['cry_duration_delta'][kind] = [b['ms'] - a['ms'] for a, b in zip(before, after)]
        paired.append(record)
    def groups(fields):
        grouped = defaultdict(list)
        for row in paired:
            if not row['matched_cry_state']:
                continue
            grouped[tuple(row[k] for k in fields)].append(row)
        result = []
        for group, found in sorted(grouped.items(), key=lambda pair: str(pair[0])):
            metrics = defaultdict(list)
            for row in found:
                for metric, values in row['timings'].items():
                    for name, value in values.items():
                        metrics[metric + '_' + name].append(value)
            result.append(dict(zip(fields, group), cases=len(found),
                               **{name: distribution(values) for name, values in metrics.items()}))
        return result
    report = dict(sources={variant: str(source) for variant, source in SOURCES.items()},
        cases={variant: len(found) for variant, found in rows.items()},
        capture_errors={variant: [row for row in found if row['status'] != 'pass']
                        for variant, found in rows.items()},
        paired_cases=len(paired), extra_feature_cases=len(extra), failed_pairs=failed,
        cry_state_mismatches=[row for row in paired if not row['matched_cry_state']],
        starvation_events={variant: sum(row.get('cry_capture', {}).get('starvation_events', 0)
                                        for row in found) for variant, found in rows.items()},
        groups=groups(('style', 'action', 'phase', 'cry_kind')),
        lines=groups(('style', 'line', 'action', 'phase')),
        species=groups(('style', 'species', 'action', 'phase')),
        transitions=groups(('style', 'species', 'target', 'action', 'phase')),
        cry_duration_delta={kind: distribution([value for row in paired
                            for value in row['cry_duration_delta'].get(kind, [])])
                            for kind in ('sampled', 'synthesized')},
        paired=paired, ancestors=[dict(species=row['species'], style=row['style'], phase=row['phase'],
                                     input_phase=row['input_phase'], complete_visible=row['complete_visible'],
                                     active_at_request=row['cry_capture']['active_at_request'])
                                 for row in extra],
        limits='Timing captures only; no regression campaign; CGB-E; production has no ancestor counterpart')
    write(ROOT / 'build/dex-selected-sampled-comparison-20261013/summary.json', report)
    print(json.dumps({k: report[k] for k in ('cases', 'paired_cases', 'extra_feature_cases',
                                           'starvation_events', 'cry_duration_delta')}), flush=True)
    print('Cry-state mismatches:', len(report['cry_state_mismatches']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'timings', 'transitions', 'compare'))
    parser.add_argument('--variant', choices=tuple(SOURCES))
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.action == 'compare':
        comparison()
    elif args.variant is None:
        parser.error('--variant is required for captures')
    elif args.action == 'prepare':
        prepare(SOURCES[args.variant])
    elif args.action == 'timings':
        timings(args.variant, args.jobs, args.limit)
    else:
        transitions(args.variant, args.jobs)
