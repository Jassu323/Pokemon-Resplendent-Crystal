"""Host-only per-object production reference and targeted-motion qualification."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import statistics
import subprocess

from tools.pokedex_info_assets import constants
from .assets import Repository, sha256
from .cold_listing import ROOT, FRAME
from . import global_speed as speed, global_animation_timing as timing
from . import performance, shared_menu_regression as menu

OUTPUT = ROOT / 'build/battle-motion-reference-20261004'
PROTOTYPE = OUTPUT / 'prototype'
TARGETS = 'SURF WATER_PULSE DRAGON_DANCE CAUSTIC SOLARBEAM DAZZLING_GLEAM SUPERPOWER'.split()
CONTROLS = 'THUNDERBOLT PETAL_DANCE THUNDERSHOCK SHOCK_WAVE WILD_CHARGE VOLT_TACKLE ENERGY_BALL SHADOW_BALL'.split()


def configuration(variant):
    if variant in ('targeted', 'surf-production', 'surf-intro', 'surf-cleanup') or variant.startswith('expanded'):
        folder = PROTOTYPE if variant == 'targeted' else OUTPUT / ('prototype-'+variant)
        cfg = dict(root=str(folder / 'candidate'), rom=str(folder / 'pokecrystal-targeted-motion.gbc'),
                   sym=str(folder / 'pokecrystal-targeted-motion.sym'), expected_double_speed=1)
    else:
        cfg = speed.configuration(variant)
        if variant == 'battle-normal':
            cfg['expected_double_speed'] = cfg['expected_battle_speed']
    return dict(cfg, variant=variant, output_root=str(OUTPUT / 'replays'),
                capture_images=True, capture_moves=TARGETS + ['THUNDERBOLT'])


def prepare(variant, moves, purpose='standard', coherent=False):
    cfg = configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    parent = OUTPUT / 'setup' / variant
    fixture_key = sha256(json.dumps(sorted(moves)).encode())[:10]
    folder = parent / (sha256(repo.rom)[:12]+'-'+purpose+'-'+fixture_key)
    points = dict(timing.POINTS, sound=('PlaySFX', False), stereo_sound=('PlayStereoSFX', False))
    performance.core(repo, folder, points)
    header = folder / 'performance-symbols.h'
    with header.open('a') as out:
        for label in ('wBattleAnimAddress', 'wBattleAnimDelay', 'wBattleAnimParam',
                      'wActiveAnimObjects', 'wBGEffect1', 'hLCDCPointer'):
            out.write(f'#define S_{label} {repo.symbols[label][1]}\n')
    cfg['core'] = str(menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', folder,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_TIMING_TRACE',
         '-DDEX_ANIMATION_REFERENCE_TRACE', f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"')))
    if variant == 'battle-normal' or variant in ('targeted', 'surf-production', 'surf-intro', 'surf-cleanup') or variant.startswith('expanded'):
        from .shared_menu_fixtures import make_fixture
        cfg['battery'] = str(folder / 'private.sav')
        make_fixture(repo, speed.BATTERY, Path(cfg['battery']), ('ROUTE_30', 13, 49))
        stamp = folder/'checkpoint-rom.sha256'
        identity = sha256(repo.rom)
        if not (folder / 'battle-main.s0').exists() or not stamp.exists() or stamp.read_text().strip()!=identity:
            menu.location_menu_states(folder, repo, cfg['core'], Path(cfg['battery']), 'battle')
            stamp.write_text(identity+'\n')
        donor = folder / 'battle-main.s0'
    else:
        cfg['battery'] = str(speed.BASE / 'menus' / variant / 'battle/private.sav')
        donor = speed.BASE / 'menus' / variant / 'battle/battle-main.s0'
    factory = speed.compile_factory(repo, folder)
    values = constants(ROOT / 'constants/move_constants.asm')
    cfg['fixtures'] = {}
    for move in moves:
        cfg['fixtures'][move] = {}
        for side in ('player', 'foe'):
            state = folder / f'{move.lower()}-{side}.s0'
            subprocess.run([str(factory), cfg['rom'], str(donor), str(values[move]), side, str(state)]
                           + (['coherent'] if coherent else []),
                           capture_output=True, check=True)
            cfg['fixtures'][move][side] = str(state)
    (folder / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')
    if purpose=='regression' or not (parent/'config.json').exists():
        (parent/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    return cfg


def events(folder):
    with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
        return [json.loads(line) for line in stream]


def summarize(path):
    result = json.loads(path.read_text())
    source = events(path.parent)
    invocations = []
    for invocation in result['requested_animations']:
        if invocation['elapsed_t'] is None:
            continue
        start, end = invocation['start']['t'], invocation['start']['t'] + invocation['elapsed_t']
        selected = [e for e in source if start <= e['t'] < end]
        spans = sorted((e for e in selected if e['event'] == 'perf_cost' and e['name'] == 'battle_script'), key=lambda e:e['t'])
        scripts = []
        for span in spans:
            a, b = span['t'], span['t'] + span['elapsed']
            local = [e for e in selected if a <= e['t'] < b]
            objects = [e for e in local if e['event'] == 'anim_objects']
            states = [e for e in local if e['event'] == 'anim_state']
            histories = []
            active = {}
            for event in objects:
                data = bytes.fromhex(event['bytes'])
                for slot in range(14):
                    obj = list(data[slot*20:slot*20+20])
                    # INDEX zero is an empty object; slots are reused during scripts.
                    if obj[0] == 0 or (slot in active and active[slot]['index'] != obj[0]):
                        if slot in active:
                            history = active.pop(slot)
                            history['end_t'] = event['t']
                            histories.append(history)
                    if obj[0] == 0:
                        continue
                    if slot not in active:
                        active[slot] = dict(slot=slot, index=obj[0], function=obj[5], frameset=obj[3] + 256*obj[4],
                                            start_t=event['t'], samples=[])
                    active[slot]['samples'].append(dict(t=event['t'], data=obj))
            for history in active.values():
                history['end_t'] = b
                histories.append(history)
            for h in histories:
                h['lifetime'] = (h['end_t'] - h['start_t']) / FRAME
                phases = defaultdict(list)
                for sample in h['samples']:
                    phases[sample['data'][15]].append(sample['t'])
                h['phases'] = {str(k):dict(start=(v[0]-a)/FRAME, last=(v[-1]-a)/FRAME, samples=len(v)) for k,v in phases.items()}
            scripts.append(dict(start=a, elapsed=span['elapsed']/FRAME, states=states, objects=histories,
                sounds=[dict(t=(e['t']-a)/FRAME, sound=e['de'], name=e['name']) for e in local
                        if e['event']=='perf_phase' and e['name'] in ('sound','stereo_sound')],
                background=[e for e in local if e['event']=='anim_background']))
        invocations.append(dict(start=start, elapsed=invocation['elapsed_t']/FRAME, scripts=scripts))
    return dict(variant=result['variant'], move=result['move'], side=result['side'], quarter=result['quarter'],
                issues=result['issues'], invocations=invocations)


def report():
    paths = sorted((OUTPUT / 'replays').glob('*/*/result.json'))
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(summarize, paths))
    summary = []
    for move in TARGETS + CONTROLS:
        for side in ('player','foe'):
            row = dict(move=move, side=side)
            for variant in ('production','final','targeted','surf-production','surf-intro'):
                group = [r for r in rows if (r['move'],r['side'],r['variant'])==(move,side,variant) and r['invocations']]
                if group:
                    row[variant] = dict(primary=statistics.median(r['invocations'][0]['scripts'][0]['elapsed'] for r in group),
                                        wrapper=statistics.median(r['invocations'][0]['elapsed'] for r in group))
            summary.append(row)
    (OUTPUT / 'reference.json').write_text(json.dumps(dict(rows=rows, summary=summary), indent=2)+'\n')
    print(json.dumps(dict(cases=len(rows), failures=[dict(move=r['move'],side=r['side'],variant=r['variant'],issues=r['issues'])
                                                for r in rows if r['issues']],summary=summary)),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variants', nargs='+', default=['production','final'])
    parser.add_argument('--moves', nargs='+', default=TARGETS+CONTROLS)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--report-only', action='store_true')
    parser.add_argument('--regression', action='store_true')
    parser.add_argument('--coherent-fixture', action='store_true',
                        help='Keep critical-hit and party stat caches consistent with battle stats')
    parser.add_argument('--capture-all', action='store_true', help='Render all requested moves at phase zero')
    parser.add_argument('--phases', nargs='+', type=int, default=[0,17556,35112,52668])
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.report_only:
        if args.regression:
            args.moves = list(dict.fromkeys(speed.REQUESTED+speed.ADDED_NEW+speed.ADDED_OLD+['DRAGON_DANCE']))
        values = constants(ROOT / 'constants/move_constants.asm')
        purpose = ('regression' if args.regression else 'rendered') + ('-coherent' if args.coherent_fixture else '')
        configs = [prepare(v,args.moves,purpose,coherent=args.coherent_fixture) for v in args.variants]
        if args.capture_all:
            for cfg in configs:
                cfg['capture_moves'] = args.moves
        if args.regression:
            for cfg in configs:
                cfg.update(capture_images=False,output_root=str(OUTPUT/('regression-coherent' if args.coherent_fixture else 'regression')))
        tasks = [(cfg,move,values[move],side,q) for cfg in configs for move in args.moves
                 for side in ('player','foe') for q in args.phases]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for n,row in enumerate(pool.map(speed.move_job,tasks),1):
                if n%20==0 or row['issues']:
                    print(json.dumps(dict(done=n,total=len(tasks),move=row['move'],issues=row['issues'])),flush=True)
    if not args.regression and not args.capture_all:
        report()


if __name__ == '__main__':
    main()
