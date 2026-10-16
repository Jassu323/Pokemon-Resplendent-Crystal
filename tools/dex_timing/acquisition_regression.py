"""Run the established gameplay, menu, animation, and audio suites on fresh links."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from tools.pokedex_info_assets import constants
from . import global_speed as speed, global_gameplay as gameplay
from . import animation_reference as motion, performance_audio as audio
from . import performance
from . import battle_speed_transitions as transitions
from . import global_custom_menus as custom
from .assets import Repository, offset, sha256
from .battle_normal_speed import MOVES, PHASES
from .cold_listing import ROOT


def configurations(output, baseline):
    return [dict(variant=name, root=str(path / 'candidate'),
                 rom=str(path / 'pokecrystal-dex-moves-mode.gbc'),
                 sym=str(path / 'pokecrystal-dex-moves-mode.sym'),
                 battery=str(path / 'legacy-input.sav'), expected_double_speed=1,
                 expected_battle_speed=0, fresh_battle_fixture=True,
                 audio_fixture_dir=str(output / 'runtime/audio' / name / 'q0'),
                 menu_output=str(output / 'runtime/menus'))
            for name, path in (('baseline', baseline), ('acquisition', output))]


def gameplay_job(task):
    config, kind, output = task
    gameplay.BASE = Path(output) / 'runtime'
    gameplay.configuration = lambda variant: config
    return gameplay.scenario((config['variant'], kind))


def move_setup(task):
    config, output = task
    motion.OUTPUT = Path(output) / 'runtime/animation'
    motion.configuration = lambda variant: dict(config, expected_double_speed=0)
    local = motion.prepare(config['variant'], MOVES, 'acquisition-100', coherent=True)
    local.update(output_root=str(Path(output) / 'runtime/moves'),
                 capture_images=False, post_menu_frames=32)
    return local


def audio_setup(task):
    config, quarter, output = task
    return audio.prepare(config, Path(output) / 'runtime/audio' / config['variant'] / f'q{quarter}', 1, quarter)


def transition_job(task):
    config, kind, quarter, output = task
    transitions.BASE = Path(output) / 'runtime/clock' / config['variant']
    local = dict(config, learning_species='BULBASAUR',
                 battle_menu_fixture=str(Path(config['menu_output']) / config['variant'] / 'battle'))
    transitions.cfg = lambda: local
    speed.BATTERY = Path(config['battery'])
    if kind == 'repeat':
        return dict(variant=config['variant'], **transitions.repeat(quarter, 8))
    if kind == 'learning':
        return dict(variant=config['variant'], **transitions.level(quarter))
    return dict(variant=config['variant'], **transitions.loss(quarter))


def custom_job(task):
    config, output = task
    custom.BASE = Path(output) / 'runtime'
    custom.configuration = lambda variant: config
    return custom.execute(config['variant'])


def run(output, baseline, action, jobs):
    configs = configurations(output, baseline)
    jobs = min(jobs, 6)
    if action == 'menus':
        tasks = [(cfg, place) for cfg in configs for place in ('standard', 'battle', 'mart', 'puzzle', 'game-corner')]
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            records = list(pool.map(speed.menu_job, tasks))
        if any(r['wrong_masks'] or r['register_failures'] for r in records):
            raise AssertionError('Custom menu input/register regression')
    elif action == 'gameplay':
        tasks = [(cfg, kind, str(output)) for cfg in configs for kind in
                 ('navigation', 'purchase', 'puzzle', 'fishing', 'trainer', 'phone', 'level', 'egg', 'pc-catch', 'party-catch', 'heal-save')]
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            records = list(pool.map(gameplay_job, tasks))
        if any(r['issues'] for r in records):
            raise AssertionError(json.dumps([r for r in records if r['issues']]))
    elif action == 'custom':
        with ProcessPoolExecutor(max_workers=min(jobs, 2)) as pool:
            records = list(pool.map(custom_job, [(cfg, str(output)) for cfg in configs]))
    elif action == 'transitions':
        tasks = [(cfg, kind, q, str(output)) for cfg in configs
                 for kind in ('repeat', 'learning', 'loss') for q in PHASES]
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            records = list(pool.map(transition_job, tasks))
    elif action == 'moves':
        with ProcessPoolExecutor(max_workers=min(jobs, 2)) as pool:
            prepared = list(pool.map(move_setup, [(cfg, str(output)) for cfg in configs]))
        values = constants(ROOT / 'constants/move_constants.asm')
        tasks = [(cfg, move, values[move], side, q) for cfg in prepared for move in MOVES
                 for side in ('player', 'foe') for q in PHASES]
        records = []
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            for row in pool.map(speed.move_job, tasks):
                records.append(row)
                if len(records) % 100 == 0 or row['issues']:
                    print(json.dumps(dict(done=len(records), total=len(tasks), move=row['move'],
                                          side=row['side'], issues=row['issues'])), flush=True)
    elif action == 'audio':
        with ProcessPoolExecutor(max_workers=min(jobs, 2)) as pool:
            prepared = list(pool.map(audio_setup, [(cfg, q, str(output)) for cfg in configs for q in PHASES]))
        tasks = []
        for local in prepared:
            folder = Path(local['output'])
            repo = Repository(Path(local['root']), Path(local['rom']), Path(local['sym']))
            factory = audio.factory(repo, folder)
            table = offset(repo.symbols['NewPokedexOrder'])
            for name in audio.SPECIES:
                n = performance.names().index(name)
                index = int.from_bytes(repo.rom[table + n * 2:table + n * 2 + 2], 'little')
                for context in ('player', 'blocking', 'stereo'):
                    donor = local['states']['caterpie']['encounter'] if context == 'player' else str(folder / 'party.s0')
                    state = folder / f'{name}-{context}.s0'
                    subprocess.run([str(factory), local['rom'], donor, str(index), context, str(state)],
                                   check=True, capture_output=True)
                    local['states'][name][context] = str(state)
                for context in ('stats', 'catch', 'faint', 'player', 'blocking', 'stereo'):
                    tasks.append((dict(local, expected_double_speed=int(context in ('stats', 'blocking', 'stereo'))), name, context))
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            records = list(pool.map(audio.execute, tasks))
    else:
        raise ValueError(action)
    result = dict(action=action, cases=len(records), workers=jobs, results=records,
                  rom_sha256=sha256(Path(configs[1]['rom']).read_bytes()),
                  baseline_sha256=sha256(Path(configs[0]['rom']).read_bytes()),
                  issues=[r for r in records if r.get('issues')])
    (output / f'acquisition-{action}-regression.json').write_text(json.dumps(result, indent=2) + '\n')
    if result['issues']:
        raise AssertionError(f'{action}: {len(result["issues"])} failing cases')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('menus', 'gameplay', 'moves', 'audio', 'transitions', 'custom'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    run(args.output.resolve(), args.baseline.resolve(), args.action, args.jobs)


if __name__ == '__main__':
    main()
