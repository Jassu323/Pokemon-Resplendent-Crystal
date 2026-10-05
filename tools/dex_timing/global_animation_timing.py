"""Read-only battle tick/cost/OAM profiling of the accepted speed baseline.

This is host instrumentation, not cartridge pacing. Every replay runs the
unmodified normal or double-speed ROM with native battle input.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import re
import statistics
import subprocess

from tools.pokedex_info_assets import constants
from .assets import Repository
from .cold_listing import ROOT, FRAME
from . import global_speed as speed, performance, shared_menu_regression as menu

OUTPUT = ROOT / 'build/global-animation-timing-20261004'
MOVES = '''SURF WATER_PULSE THUNDERSHOCK THUNDERBOLT CAUSTIC DRAGON_DANCE
PETAL_DANCE SOLARBEAM DAZZLING_GLEAM POISON_GAS'''.split()
POINTS = dict(speed.EXTRA,
    anim_tick=('RunBattleAnimScript.playframe', False),
    anim_ready=('RunBattleAnimScript.not_rollout', False),
    anim_command=('RunBattleAnimCommand', True),
    anim_bg=('_ExecuteBGEffects', True),
    anim_oam=('BattleAnim_UpdateOAM_All', True),
    anim_functions=('BattleAnim_UpdateFunctions_All', True),
    anim_object=('DoBattleAnimFrame', True),
    anim_frame=('GetBattleAnimFrame', True),
    anim_sine=('BattleAnim_Sine', True),
    anim_ly=('PushLYOverrides', True),
    anim_pals=('BattleAnimRequestPals', True),
    anim_wait=('BattleAnimDelayFrame', True),
    anim_gfx=('LoadBattleAnimGFX', True),
    anim_sound_wait=('WaitSFX', True))

CUSTOM = '''Bug Bite,Drain Life,Signal Beam,Silver Wind,Twineedle,Vampirism,X-Scissor,
Night Slash,Sucker Punch,Taunt,Dragon Claw,Dragon Dance,Dragon Rage,DragonBreath,
Outrage,Shock Wave,Spark,Thunder,Thunder Fang,Thunderbolt,ThunderPunch,Thundershock,
Volt Tackle,Wild Charge,Dazzling Gleam,Disarming Voice,Fairy Wind,Moonblast,Wish,
Arm Thrust,Brick Break,Bulk Up,Drain Punch,Focus Punch,Force Palm,Meteor Dive,
Seismic Toss,Sky Uppercut,Superpower,Blaze Kick,Ember,Fire Blast,Fire Fang,Fire Punch,
Fire Spin,Flame Wheel,Flamethrower,Heat Wave,Lava Plume,Overheat,Sacred Fire,Aerial Ace,
Aerial Crash,Air Cutter,Dive Bomb,Pluck,Hex,Shadow Ball,Shadow Claw,Shadow Punch,
Will-O-Wisp,Aromatherapy,Bullet Seed,Energy Ball,Giga Drain,Ingrain,Leaf Blade,
Magical Leaf,Mega Drain,Petal Dance,Razor Leaf,Sleep Powder,Solar Beam,Spore,Stun Spore,
Vine Whip,Drill Run,Mud Bomb,Mud Shot,Sand Tomb,Aurora Beam,Blizzard,Glacial Slam,Hail,
Ice Ball,Ice Fang,Icicle Crash,Icy Wind,Block,Crush Claw,Fake Out,Howl,Hyper Fang,Yawn,
Acid,Caustic,Corrosion,Poison Fang,Poison Gas,Poison Jab,Poison Sting,Poison Tail,
PoisonPowder,Sludge,Sludge Bomb,Sludge Wave,Toxic,Calm Mind,Extrasensory,Rock Blast,
Rock Tomb,Stone Edge,Bullet Punch,Heavy Slam,Iron Defense,Meteor Mash,Hydro Pump,
Water Pulse,Waterfall'''


def polished_audit():
    normalize = lambda s: ''.join(c for c in s.upper() if c.isalpha())
    custom = {normalize(n) for n in CUSTOM.split(',')}
    qualified = json.loads((speed.BASE / 'qualification/moves-qualified.json').read_text())
    affected = [dict(r, faster_percent=100 * (r['normal'] - r['double']) / r['normal'])
                for r in qualified['summary'] if normalize(r['move']) not in custom
                and (r['normal'] - r['double']) / r['normal'] >= .1]
    roots = dict(project=ROOT, polished=Path.home() / 'Documents/GitHub/polishedcrystal',
                 pret=Path.home() / 'Documents/GitHub/pokecrystal')
    wanted = sorted({r['move'] for r in affected} | {'POISON_GAS'})
    sources = {}
    for name, root in roots.items():
        source = root / 'data/moves/animations.asm'
        text = source.read_text()
        blocks = {}
        for match in re.finditer(r'^BattleAnim_(\w+):\s*\n(.*?)(?=^\w+::?|\Z)', text, re.M | re.S):
            key = normalize(match[1])
            blocks[key] = dict(label=match[1], line=text.count('\n', 0, match.start()) + 1,
                              body=match[2], waits=re.findall(r'^\s*anim_wait\s+([^;\n]+)', match[2], re.M),
                              loops=re.findall(r'^\s*anim_loop\s+([^;\n]+)', match[2], re.M))
        sources[name] = dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
            file=str(source), moves={m: blocks.get(normalize(m)) for m in wanted})
    (OUTPUT / 'polished-audit.json').write_text(json.dumps(dict(affected=affected, sources=sources), indent=2) + '\n')


def prepare(variant):
    cfg = speed.configuration(variant)
    cfg.update(variant=variant, output_root=str(OUTPUT / 'replays'))
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    folder = OUTPUT / 'observers' / variant
    performance.core(repo, folder, POINTS)
    header = folder / 'performance-symbols.h'
    with header.open('a') as out:
        for label in ('wBattleAnimAddress', 'wBattleAnimDelay', 'wBattleAnimParam'):
            out.write(f'#define S_{label} {repo.symbols[label][1]}\n')
    cfg['core'] = str(menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', folder,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_TIMING_TRACE',
         f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"')))
    cfg['battery'] = str(speed.BASE / 'menus' / variant / 'battle/private.sav')
    cfg['fixtures'] = {move: {side: str(speed.BASE / 'moves' / variant / f'{move.lower()}-{side}.s0')
                              for side in ('player', 'foe')} for move in MOVES}
    assert all(Path(path).exists() for row in cfg['fixtures'].values() for path in row.values())
    return cfg


def summarize(path):
    row = json.loads(path.read_text())
    baseline = json.loads((speed.BASE / 'moves' / row['variant'] / path.parent.name / 'result.json').read_text())
    assert row['requested_animations'] == baseline['requested_animations'], path
    with gzip.open(path.parent / 'events.jsonl.gz', 'rt') as stream:
        events = [json.loads(line) for line in stream]
    result = dict(variant=row['variant'], move=row['move'], side=row['side'], quarter=row['quarter'],
                  issues=row['issues'], observer_timing_parity=True, invocations=[])
    for anim in row['requested_animations']:
        if anim['elapsed_t'] is None:
            continue
        start, end = anim['start']['t'], anim['start']['t'] + anim['elapsed_t']
        captured = [e for e in events if start <= e['t'] < end]
        ticks = [e for e in captured if e['event'] == 'perf_phase' and e['name'] == 'anim_tick']
        ready = [e for e in captured if e['event'] == 'anim_state']
        if len(ticks) != len(ready):
            raise ValueError((path, len(ticks), len(ready)))
        work = [(r['t'] - t['t']) / FRAME for t, r in zip(ticks, ready)]
        intervals = [(b['t'] - a['t']) / FRAME for a, b in zip(ticks, ticks[1:])]
        costs = defaultdict(list)
        for e in captured:
            if e['event'] == 'perf_cost':
                costs[e['name']].append(e['elapsed'] / FRAME)
        script_spans = [e for e in captured if e['event'] == 'perf_cost' and e['name'] == 'battle_script']
        scripts = []
        for script in script_spans:
            a, b = script['t'], script['t'] + script['elapsed']
            ts = [e for e in ticks if a <= e['t'] < b]
            rs = [e for e in ready if a <= e['t'] < b]
            ds = [(y['t'] - x['t']) / FRAME for x, y in zip(ts, ts[1:])]
            scripts.append(dict(start=a, elapsed=script['elapsed'] / FRAME, ticks=len(ts),
                step_intervals=dict(Counter(round(x) for x in ds)),
                states=rs, intervals=ds))
        scripts.sort(key=lambda s: s['start'])
        result['invocations'].append(dict(
            elapsed=anim['elapsed_t'] / FRAME, ticks=len(ticks),
            work_median=statistics.median(work), work_max=max(work),
            work_total=sum(work), step_intervals=dict(Counter(round(x) for x in intervals)),
            intervals=intervals, work=work, states=ready, scripts=scripts,
            script_duration=sum(e['elapsed'] for e in script_spans) / FRAME,
            costs={n: dict(calls=len(v), total=sum(v), median=statistics.median(v), maximum=max(v))
                   for n, v in costs.items()},
            oam_peak=max(r['peak'] for r in ready), oam_over_ticks=sum(r['over_lines'] > 0 for r in ready)))
    return result


def report():
    paths = sorted((OUTPUT / 'replays').glob('*/*/result.json'))
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(summarize, paths))
    comparisons = []
    by = {(r['variant'], r['move'], r['side'], r['quarter']): r for r in rows}
    for move in MOVES:
        for side in ('player', 'foe'):
            a = by['production', move, side, 0]['invocations'][0]
            b = by['final', move, side, 0]['invocations'][0]
            states_match = len(a['states']) == len(b['states']) and all(
                (x['script'], x['delay'], x['param'], x['shadow']) ==
                (y['script'], y['delay'], y['param'], y['shadow'])
                for x, y in zip(a['states'], b['states']))
            comparisons.append(dict(move=move, side=side, normal=a['elapsed'], double=b['elapsed'],
                normal_ticks=a['ticks'], double_ticks=b['ticks'],
                normal_intervals=a['step_intervals'], double_intervals=b['step_intervals'],
                normal_work=a['work_total'], double_work=b['work_total'],
                normal_work_max=a['work_max'], double_work_max=b['work_max'],
                normal_oam_peak=a['oam_peak'], double_oam_peak=b['oam_peak'],
                normal_over_ticks=a['oam_over_ticks'], double_over_ticks=b['oam_over_ticks'],
                exact_logical_states_match=states_match))
    data = dict(cases=len(rows), issues=[r for r in rows if r['issues']],
                rows=rows, phase_zero=comparisons)
    (OUTPUT / 'profile.json').write_text(json.dumps(data, indent=2) + '\n')
    polished_audit()
    print(json.dumps(dict(cases=len(rows), issues=len(data['issues']), comparisons=comparisons)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.report_only:
        values = constants(ROOT / 'constants/move_constants.asm')
        configs = [prepare(v) for v in ('production', 'final')]
        tasks = [(cfg, move, values[move], side, phase)
                 for cfg in configs for move in MOVES for side in ('player', 'foe')
                 for phase in (0, 17556, 35112, 52668)]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for i, row in enumerate(pool.map(speed.move_job, tasks), 1):
                if row['issues'] or i % 20 == 0:
                    print(json.dumps(dict(done=i, total=len(tasks), move=row['move'], issues=row['issues'])), flush=True)
    report()


if __name__ == '__main__':
    main()
