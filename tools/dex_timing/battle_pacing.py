"""Native phase-pacing A/B timing, state and rendered-frame investigation."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import statistics
import subprocess
import shutil
from functools import partial

from tools.pokedex_info_assets import constants
from .assets import Repository
from .cold_listing import ROOT, FRAME
from . import global_speed as speed, global_animation_timing as timing
from . import performance, shared_menu_regression as menu, performance_audio as audio, global_review_save as review_save
from .shared_menu_fixtures import make_fixture

OUTPUT = ROOT / 'build/battle-pacing-20261004'
PROTOTYPE = OUTPUT / 'prototype-v1'
TARGETS = '''SURF WATER_PULSE DRAGON_DANCE THUNDERBOLT CAUSTIC SOLARBEAM
DAZZLING_GLEAM SUPERPOWER SHOCK_WAVE WILD_CHARGE VOLT_TACKLE ENERGY_BALL SHADOW_BALL'''.split()
CONTROLS = ['PETAL_DANCE', 'THUNDERSHOCK']


def prepare_audio(quarter):
    cfg = configuration('paced')
    cfg['battery'] = str(speed.BATTERY)
    return audio.prepare(cfg, OUTPUT / 'audio' / f'q{quarter}', 0, quarter)


def audio_regression(jobs):
    with ProcessPoolExecutor(max_workers=4) as pool:
        configs = list(pool.map(prepare_audio, (0, 17556, 35112, 52668)))
    tasks = []
    for cfg in configs:
        output = Path(cfg['output'])
        repo = Repository(ROOT, Path(cfg['rom']), Path(cfg['sym']))
        factory = audio.factory(repo, output)
        order_at = repo.symbols['NewPokedexOrder']
        from .assets import offset
        for name in audio.SPECIES:
            n = performance.names().index(name)
            index = int.from_bytes(repo.rom[offset(order_at) + n * 2:offset(order_at) + n * 2 + 2], 'little')
            for context in ('player', 'blocking', 'stereo'):
                donor = cfg['states']['caterpie']['encounter'] if context == 'player' else str(output / 'party.s0')
                state = output / f'{name}-{context}.s0'
                subprocess.run([str(factory), cfg['rom'], donor, str(index), context, str(state)],
                               capture_output=True, check=True)
                cfg['states'][name][context] = str(state)
            tasks.extend((cfg, name, context) for context in ('stats', 'catch', 'faint', 'player', 'blocking', 'stereo'))
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(audio.execute, tasks):
            results.append(row)
            if len(results) % 40 == 0 or row['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), species=row['species'],
                                      context=row['context'], issues=row['issues'])), flush=True)
    (OUTPUT / 'audio/report.json').write_text(json.dumps(dict(configurations=configs, results=results), indent=2) + '\n')
    compare_audio(results)
    print(json.dumps(dict(cases=len(results), failures=sum(bool(r['issues']) for r in results))), flush=True)


def playback_signature(row):
    return [(s['expected_blocks'], s['blocks'], s['wave_sha256'], tuple(s['frequencies']),
             tuple(tuple(t) for t in s['timer_configs'])) for s in row['segments']]


def compare_audio(results):
    previous = json.loads((speed.BASE / 'audio/report-final.json').read_text())
    reference = {(r['species'], r['context'], r['quarter']): r for r in previous['results'] if r['visits'] == 0}
    changed = [dict(species=r['species'], context=r['context'], quarter=r['quarter']) for r in results
               if playback_signature(r) != playback_signature(reference[r['species'], r['context'], r['quarter']])]
    (OUTPUT / 'audio/comparison.json').write_text(json.dumps(dict(cases=len(results), changes=changed,
        known_misses=sum(len(r['known_misses']) for r in results)), indent=2) + '\n')


def manual_review():
    output = OUTPUT / 'manual-review'
    output.mkdir(exist_ok=True)
    party = (
        ('KYOGRE', 'WATER', ('SURF', 'WATER_PULSE', 'CAUSTIC', 'THUNDERBOLT')),
        ('GARCHOMP', 'PACE', ('DRAGON_DANCE', 'SUPERPOWER', 'SOLARBEAM', 'DAZZLING_GLEAM')),
        ('RAYQUAZA', 'CHARGE', ('SHOCK_WAVE', 'WILD_CHARGE', 'VOLT_TACKLE', 'ENERGY_BALL')),
        ('DUSKNOIR', 'CONTROL', ('SHADOW_BALL', 'PETAL_DANCE', 'THUNDERSHOCK', 'FIRE_BLAST')),
        ('MEGANIUM', 'LEAVES', ('RAZOR_LEAF', 'MAGICAL_LEAF', 'SEISMIC_TOSS', 'EARTHQUAKE')),
        ('METAGROSS', 'HEAVY', ('HYDRO_PUMP', 'OVERHEAT', 'METEOR_DIVE', 'AERIAL_CRASH')),
    )
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    report = review_save.create(repo, speed.BATTERY, output / 'animation-review.sav', party, TARGETS)
    for mode, source in (('normal', ROOT / 'pokecrystal'),
                         ('double', speed.BASE / 'final/pokecrystal-global-double-speed'),
                         ('paced', PROTOTYPE / 'pokecrystal-battle-paced')):
        folder = output / mode
        folder.mkdir(exist_ok=True)
        target = folder / ('pokecrystal-animation-' + mode)
        for suffix in ('.gbc', '.sym', '.map'):
            shutil.copy2(source.with_suffix(suffix), target.with_suffix(suffix))
        shutil.copy2(output / 'animation-review.sav', target.with_suffix('.sav'))
    (output / 'animation-review.json').write_text(json.dumps(report, indent=2) + '\n')
    with ProcessPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(partial(review_save.verify, review=output), ('normal', 'double', 'paced')))
    (output / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(dict(pokemon=report['pokemon'], moves=report['moves'], verified_arms=len(results))), flush=True)


def menu_regression(jobs):
    cfg = configuration('paced')
    cfg.update(battery=str(speed.BATTERY), menu_output=str(OUTPUT / 'menus'))
    with ProcessPoolExecutor(max_workers=min(5, jobs)) as pool:
        results = list(pool.map(speed.menu_job, [(cfg, location) for location in
            ('standard', 'battle', 'mart', 'puzzle', 'game-corner')]))
    (OUTPUT / 'menus/report.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results), flush=True)


def configuration(variant):
    if variant != 'paced':
        cfg = speed.configuration(variant)
    else:
        cfg = dict(root=str(PROTOTYPE / 'candidate'), rom=str(PROTOTYPE / 'pokecrystal-battle-paced.gbc'),
                   sym=str(PROTOTYPE / 'pokecrystal-battle-paced.sym'), expected_double_speed=1)
    cfg.update(variant=variant, output_root=str(OUTPUT / 'replays'),
               capture_images=True, capture_moves=TARGETS)
    return cfg


def prepare(variant, moves):
    cfg = configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = OUTPUT / 'setup' / variant
    output.mkdir(parents=True, exist_ok=True)
    points = dict(speed.EXTRA, anim_tick=('RunBattleAnimScript.playframe', False),
                  anim_ready=('RunBattleAnimScript.not_rollout', False))
    if variant == 'paced':
        points.update(pace_phase=('BattleAnimPacing_SetPhase', True),
                      pace_hold=('BattleAnimPacing_Hold', False), pace_late=('BattleAnimPacing_Late', False))
    performance.core(repo, output, points)
    header = output / 'performance-symbols.h'
    with header.open('a') as out:
        for label in ('wBattleAnimAddress', 'wBattleAnimDelay', 'wBattleAnimParam') + (
                ('wBattleAnimPaceExtra',) if variant == 'paced' else ()):
            out.write(f'#define S_{label} {repo.symbols[label][1]}\n')
    flags = ['-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_TIMING_TRACE',
             f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"']
    if variant == 'paced':
        flags.append('-DDEX_BATTLE_PACING_TRACE')
    cfg['core'] = str(menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output, tuple(flags)))
    if variant == 'paced':
        cfg['battery'] = str(output / 'private.sav')
        make_fixture(repo, speed.BATTERY, Path(cfg['battery']), ('ROUTE_30', 13, 49))
        if not (output / 'battle-main.s0').exists():
            menu.location_menu_states(output, repo, cfg['core'], Path(cfg['battery']), 'battle')
        donor = output / 'battle-main.s0'
    else:
        cfg['battery'] = str(speed.BASE / 'menus' / variant / 'battle/private.sav')
        donor = speed.BASE / 'menus' / variant / 'battle/battle-main.s0'
    factory = speed.compile_factory(repo, output)
    values = constants(repo.root / 'constants/move_constants.asm')
    fixtures = {}
    for move in moves:
        fixtures[move] = {}
        for side in ('player', 'foe'):
            path = output / f'{move.lower()}-{side}.s0'
            subprocess.run([str(factory), cfg['rom'], str(donor), str(values[move]), side, str(path)],
                           capture_output=True, check=True)
            fixtures[move][side] = str(path)
    cfg['fixtures'] = fixtures
    (output / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')
    return cfg


def summarize(path):
    result = json.loads(path.read_text())
    with gzip.open(path.parent / 'events.jsonl.gz', 'rt') as stream:
        events = [json.loads(line) for line in stream]
    invocations = []
    for invocation in result.get('requested_animations', ()):
        if invocation['elapsed_t'] is None:
            continue
        start = invocation['start']['t']
        end = start + invocation['elapsed_t']
        selected = [e for e in events if start <= e['t'] < end]
        scripts = sorted((e for e in selected if e['event'] == 'perf_cost' and e['name'] == 'battle_script'),
                         key=lambda e: e['t'])
        states = [e for e in selected if e['event'] == 'anim_state']
        script_rows = []
        for script in scripts:
            ss = [e for e in states if script['t'] <= e['t'] < script['t'] + script['elapsed']]
            ticks = [e for e in selected if e['event'] == 'perf_phase' and e['name'] == 'anim_tick'
                     and script['t'] <= e['t'] < script['t'] + script['elapsed']]
            intervals = [(b['t'] - a['t']) / FRAME for a, b in zip(ticks, ticks[1:])]
            script_rows.append(dict(elapsed=script['elapsed'] / FRAME, states=ss, intervals=intervals,
                                    ticks=len(ticks)))
        pace = [e for e in selected if e['event'] == 'pace_state']
        invocations.append(dict(elapsed=invocation['elapsed_t'] / FRAME, scripts=script_rows,
            states=states, holds=sum(e['event'] == 'perf_phase' and e['name'] == 'pace_hold' for e in selected),
            late=sum(e['event'] == 'perf_phase' and e['name'] == 'pace_late' for e in selected), pace=pace,
            start=start, end=end))
    return dict(variant=result['variant'], move=result['move'], side=result['side'], quarter=result['quarter'],
                issues=result['issues'], invocations=invocations)


def report():
    audio_report = OUTPUT / 'audio/report.json'
    if audio_report.exists():
        compare_audio(json.loads(audio_report.read_text())['results'])
    unique = {(p.parent.parent.name, p.parent.name): p for folder in ('replays-regression', 'replays')
              for p in (OUTPUT / folder).glob('*/*/result.json')}
    paths = sorted(unique.values())
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(summarize, paths))
    summary = []
    for move in TARGETS + CONTROLS:
        for side in ('player', 'foe'):
            entry = dict(move=move, side=side)
            for variant in ('production', 'final', 'paced'):
                group = [r for r in rows if (r['move'], r['side'], r['variant']) == (move, side, variant)
                         and r['invocations'] and r['invocations'][0]['scripts']]
                if group:
                    entries = [r['invocations'][0] for r in group]
                    entry[variant] = dict(cases=len(group), elapsed=statistics.median(e['elapsed'] for e in entries),
                        primary=statistics.median(e['scripts'][0]['elapsed'] for e in entries),
                        holds=statistics.median(e['holds'] for e in entries), late_max=max(e['late'] for e in entries))
            summary.append(entry)
    data = dict(cases=len(rows), failures=[r for r in rows if r['issues']], summary=summary, rows=rows)
    (OUTPUT / 'timing.json').write_text(json.dumps(data, indent=2) + '\n')
    paired, mismatches, timing_changes = 0, [], []
    signature = lambda states: [(s['delay'], s['param'], s['shadow']) for s in states]
    for move in sorted({r['move'] for r in rows}):
        for side in ('player', 'foe'):
            group = {v: [r for r in rows if (r['move'], r['side'], r['variant']) == (move, side, v)]
                     for v in ('final', 'paced')}
            if not all(group.values()):
                continue
            for quarter in (0, 17556, 35112, 52668):
                local = {v: next((r for r in rr if r['quarter'] == quarter), None) for v, rr in group.items()}
                if not all(local.values()) or any(not r['invocations'] for r in local.values()):
                    continue
                states = {v: r['invocations'][0]['scripts'][0]['states'] for v, r in local.items()}
                paired += 1
                if signature(states['final']) != signature(states['paced']):
                    mismatches.append(dict(move=move, side=side, quarter=quarter))
            if move not in TARGETS:
                elapsed = {v: statistics.median(r['invocations'][0]['scripts'][0]['elapsed'] for r in rr)
                           for v, rr in group.items()}
                delta = elapsed['paced'] - elapsed['final']
                if abs(delta) > 0.1:
                    timing_changes.append(dict(move=move, side=side, delta=delta, elapsed=elapsed))
    (OUTPUT / 'state-comparison.json').write_text(json.dumps(dict(paired_cases=paired,
        logical_signature_mismatches=mismatches, unselected_changes_over_tenth_interval=timing_changes), indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), failures=len(data['failures']), summary=summary)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--variants', nargs='+', default=['production', 'final', 'paced'])
    parser.add_argument('--moves', nargs='+', default=TARGETS + CONTROLS)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--report-only', action='store_true')
    parser.add_argument('--regression', action='store_true')
    parser.add_argument('--audio-regression', action='store_true')
    parser.add_argument('--manual-review', action='store_true')
    parser.add_argument('--menu-regression', action='store_true')
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    if args.audio_regression:
        return audio_regression(args.jobs)
    if args.manual_review:
        return manual_review()
    if args.menu_regression:
        return menu_regression(args.jobs)
    if not args.report_only:
        moves = list(dict.fromkeys((speed.REQUESTED + speed.ADDED_NEW + speed.ADDED_OLD + ['DRAGON_DANCE']
                                    + TARGETS) if args.regression else args.moves))
        with ProcessPoolExecutor(max_workers=min(3, args.jobs)) as pool:
            configs = list(pool.map(prepare, args.variants, [moves] * len(args.variants)))
        if args.regression:
            for config in configs:
                config['capture_images'] = False
                config['output_root'] = str(OUTPUT / 'replays-regression')
        values = constants(ROOT / 'constants/move_constants.asm')
        tasks = [(cfg, move, values[move], side, quarter) for cfg in configs for move in moves
                 for side in ('player', 'foe')
                 for quarter in ((0,) if args.smoke else (0, 17556, 35112, 52668))]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            results = []
            for row in pool.map(speed.move_job, tasks):
                results.append(row)
                if len(results) % 32 == 0 or row['issues']:
                    print(json.dumps(dict(done=len(results), total=len(tasks), variant=row['variant'],
                                          move=row['move'], side=row['side'], issues=row['issues'])), flush=True)
        filename = 'regression-' + '-'.join(args.variants) + '.json' if args.regression else 'suite.json'
        (OUTPUT / filename).write_text(
            json.dumps(dict(moves=moves, cases=len(results), results=results), indent=2) + '\n')
    report()


if __name__ == '__main__':
    main()
