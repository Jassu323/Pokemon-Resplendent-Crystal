"""Fresh production qualification of the accepted world/battle clock policy.

Historical runners are bound to isolated outputs and matching-link fixtures;
only host configuration is rebound. No timing repair is injected into the game.
Pools run sequentially, with at most 12 workers, preserving CPU headroom.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from . import global_speed as speed, battle_normal_speed as battle
from . import animation_reference as motion, global_gameplay as gameplay
from . import global_custom_menus as custom, battle_speed_transitions as transitions
from . import battle_intro_reference as intro, battle_normal_speed_report as audit
from . import performance
from .assets import sha256
from .assets import Repository
from .cold_listing import Driver, FRAME, ROOT
from . import performance_audio as audio, shared_menu_regression as menu

BASE = ROOT / 'build/production-speed-integration-20261005'
SEED = BASE / 'seed.sav'
MAX_WORKERS = 12


def configuration(variant):
    if variant == 'production':
        folder, stem, root, outside = BASE / 'baseline', 'pokecrystal', ROOT, 0
    elif variant == 'battle-normal':
        folder, stem, root, outside = ROOT, 'pokecrystal', ROOT, 1
    elif variant == 'final':
        folder = ROOT / 'build/global-speed-20261004/final'
        stem, root, outside = 'pokecrystal-global-double-speed', folder / 'candidate', 1
    else:
        raise ValueError(f'Unqualified arm: {variant}')
    return dict(root=str(root), rom=str(folder / (stem + '.gbc')),
                sym=str(folder / (stem + '.sym')), battery=str(SEED),
                expected_double_speed=outside, expected_battle_speed=0,
                audio_fixture_dir=str(BASE / 'audio' / variant / 'q0'))


def pool(max_workers=None, **kwargs):
    return ProcessPoolExecutor(max_workers=min(MAX_WORKERS, max_workers or MAX_WORKERS),
                               initializer=bind, **kwargs)


def bind():
    # Imported-by-value helper settings must also follow the fresh output root.
    speed.BASE = battle.BASE = gameplay.BASE = custom.BASE = transitions.BASE = BASE
    speed.BATTERY = SEED
    speed.configuration = gameplay.configuration = custom.configuration = configuration
    transitions.cfg = battle.cfg
    motion.OUTPUT = BASE / 'motion'
    intro.OUTPUT = BASE / 'intros'
    audit.BASE = BASE
    battle.ProcessPoolExecutor = pool


def write(name, value):
    path = BASE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def reset_job(quarter):
    local = configuration('battle-normal')
    repo = Repository(ROOT, Path(local['rom']), Path(local['sym']))
    output = BASE / 'battle-reset' / f'q{quarter}'
    output.mkdir(parents=True, exist_ok=True)
    core = transitions.compiler(repo, output)
    source = BASE / 'menus/battle-normal/battle'
    driver = Driver(core, local['rom'], menu.BOOT, source / 'private.sav', output / 'run.log')
    row = dict(quarter=quarter, issues=[])
    try:
        driver.command(f'load {source / "battle-main.s0"}')
        menu.run(driver, repo, frames=quarter/FRAME)
        row['battle'] = driver.command('m')
        if row['battle']['double_speed'] != 0:
            raise RuntimeError('Reset fixture is not a normal-speed battle')
        driver.command('perf 1')
        driver.command('audit 1')
        driver.events.clear()
        reset = menu.run(driver, repo, 'Reset', 180, 0xf0)
        if not audio.at(reset, repo, 'Reset'):
            raise RuntimeError('Native battle soft reset not dispatched')
        menu.run(driver, repo, frames=40)
        row['returned'] = menu.boot_overworld(driver, repo)
        if row['returned']['double_speed'] != 1:
            raise RuntimeError('Reset did not restore ordinary double speed')
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        row['changes'] = [e for e in driver.events if e['event'] == 'speed_change']
        row['misses'] = [e for e in driver.events if e['event'] in ('audio_miss', 'animation_miss', 'illegal')]
        speed.save_events(output / 'events.jsonl.gz', driver.events)
        driver.close()
    if row['misses'] or 'odd mode' in (output / 'run.log').read_text():
        row['issues'].append('Playback failure or SameBoy odd-mode warning during reset')
    write(f'battle-reset/q{quarter}/result.json', row)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=('menus', 'custom', 'moves', 'audio', 'odd-timer',
                                         'registration', 'dex', 'new-entry', 'gameplay', 'transitions',
                                         'intros', 'trainer-intros', 'battle-reset', 'audit'))
    args = parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    bind()
    if args.suite == 'menus':
        tasks = [(v, place) for v in ('production', 'battle-normal')
                 for place in ('standard', 'battle', 'mart', 'puzzle', 'game-corner')]
        with pool(max_workers=8) as workers:
            rows = list(workers.map(speed.menu_job, tasks))
        write('menus/report.json', rows)
    elif args.suite == 'custom':
        with pool(max_workers=2) as workers:
            rows = list(workers.map(custom.execute, ('production', 'battle-normal')))
        write('custom-menus/report.json', rows)
    elif args.suite == 'moves':
        from tools.pokedex_info_assets import constants
        values = constants(ROOT / 'constants/move_constants.asm')
        configurations = []
        for variant in ('production', 'battle-normal'):
            local = motion.prepare(variant, battle.MOVES, 'production-integration', coherent=True)
            local.update(output_root=str(BASE / 'moves'), capture_images=False, post_menu_frames=32)
            configurations.append(local)
        tasks = [(c, m, values[m], s, q) for c in configurations for m in battle.MOVES
                 for s in ('player', 'foe') for q in battle.PHASES]
        rows = []
        with pool() as workers:
            for n, row in enumerate(workers.map(speed.move_job, tasks), 1):
                rows.append(row)
                if n % 40 == 0 or row['issues']:
                    print(json.dumps(dict(done=n, total=len(tasks), move=row['move'], issues=row['issues'])), flush=True)
        write('moves/report.json', dict(cases=len(rows), configurations=configurations, results=rows))
    elif args.suite == 'audio':
        return battle.audio_suite(MAX_WORKERS)
    elif args.suite == 'odd-timer':
        return battle.odd_timer(MAX_WORKERS)
    elif args.suite == 'registration':
        return battle.registration()
    elif args.suite == 'dex':
        # A clean ROM may reuse its compiled Info payload without rebuilding
        # these raw glyph inputs, which the independent content auditor reads.
        subprocess.run(['make', '-j12', 'gfx/font/font.1bpp',
                        'gfx/font/font_battle_extra.2bpp', 'gfx/pokedex/dex_stat_bar.2bpp'], check=True)
        config = performance.prepare(ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', SEED, BASE / 'dex-setup')
        return subprocess.run([sys.executable, '-B', '-m', 'tools.dex_timing.performance_regression',
            '--config', str(BASE / 'dex-setup/config.json'), '--output', str(BASE / 'dex'),
            '--expected-double-speed', '--jobs', str(MAX_WORKERS)], check=True)
    elif args.suite == 'new-entry':
        return subprocess.run([sys.executable, '-B', '-m', 'tools.dex_timing.new_entry_sweep',
            '--rom', str(ROOT / 'pokecrystal.gbc'), '--sym', str(ROOT / 'pokecrystal.sym'),
            '--registration', str(BASE / 'registration'), '--output', str(BASE / 'new-entry'),
            '--jobs', str(MAX_WORKERS)], check=True)
    elif args.suite == 'gameplay':
        tasks = [('battle-normal', kind) for kind in ('navigation', 'purchase', 'puzzle', 'fishing',
            'trainer', 'phone', 'level', 'egg', 'pc-catch', 'heal-save')]
        with pool(max_workers=8) as workers:
            rows = list(workers.map(gameplay.scenario, tasks))
        write('gameplay/report.json', rows)
    elif args.suite == 'transitions':
        tasks = [('repeat', q, 16) for q in battle.PHASES]
        tasks += [(kind, q, 0) for kind in ('loss', 'level') for q in battle.PHASES]
        with pool(max_workers=8) as workers:
            rows = list(workers.map(transitions.job, tasks))
        write('transitions/report.json', rows)
    elif args.suite == 'battle-reset':
        with pool(max_workers=4) as workers:
            rows = list(workers.map(reset_job, battle.PHASES))
        write('battle-reset/report.json', rows)
    elif args.suite in ('intros', 'trainer-intros'):
        if args.suite == 'intros':
            configurations = [intro.prepare(v) for v in ('production', 'battle-normal')]
            tasks = [(c, n, q) for c in configurations for n in intro.SPECIES for q in battle.PHASES]
            with pool() as workers:
                rows = list(workers.map(intro.job, tasks))
            write('intros/wild-report.json', rows)
        else:
            configurations = [json.loads((BASE / 'intros/setup' / v / 'config.json').read_text())
                              for v in ('production', 'battle-normal')]
            rows = []
        tasks = [(intro.prepare_trainer(dict(c, trainer_seed=str(
            BASE / 'gameplay/battle-normal/trainer/private.sav')), q), 'joey', q)
            for c in configurations for q in battle.PHASES]
        with pool(max_workers=8) as workers:
            trainers = list(workers.map(intro.job, tasks))
        write('intros/trainer-report.json', trainers)
        rows += trainers
    else:
        tasks = [(m, s, q) for m in battle.MOVES for s in ('player', 'foe') for q in battle.PHASES]
        with pool() as workers:
            rows = list(workers.map(audit.compare, tasks))
        write('comparison.json', dict(paired_cases=len(rows), rows=rows,
            logical_differences=sum(not r['logical_equal'] for r in rows),
            object_differences=sum(not r['objects_equal'] for r in rows),
            background_differences=sum(not r['backgrounds_equal'] for r in rows),
            sound_differences=sum(not r['sound_sequence_equal'] for r in rows),
            maximum_primary_delta=max(abs(r['delta']) for r in rows), audio=audit.audio_audit()))
    print(json.dumps(dict(suite=args.suite, cases=len(rows),
                          failures=sum(bool(row.get('issues')) for row in rows))), flush=True)


if __name__ == '__main__':
    main()
