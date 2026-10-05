"""Qualification of the private normal-battle/double-world clock policy."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from tools.pokedex_info_assets import constants
from . import global_speed as speed, animation_reference as motion
from . import performance, performance_audio as audio, shared_menu_regression as menu
from . import global_review_save as review
from .assets import Repository, offset, sha256
from .cold_listing import ROOT
from .new_entry_sweep import ORIGINAL

BASE = ROOT / 'build/battle-normal-speed-20261004'
ADDED = '''DRAGON_DANCE ROCK_SLIDE VOLT_TACKLE ENERGY_BALL GLACIAL_SLAM ICICLE_CRASH
FIRE_SPIN FLAME_WHEEL LAVA_PLUME DRAGON_RAGE DRAGONBREATH NIGHT_SLASH X_SCISSOR
GIGA_DRAIN SACRED_FIRE HYPER_FANG BLAZE_KICK HEAVY_SLAM ROCK_BLAST POISON_JAB IRON_TAIL'''.split()
MOVES = speed.REQUESTED + speed.ADDED_NEW + speed.ADDED_OLD + ADDED
assert len(MOVES) == len(set(MOVES)) == 100
PHASES = (0, 17556, 35112, 52668)
CAPTURE = '''SURF WATER_PULSE DRAGON_DANCE THUNDERBOLT CAUSTIC SOLARBEAM DAZZLING_GLEAM
SUPERPOWER WATERFALL LEAF_BLADE RAZOR_LEAF MAGICAL_LEAF GUST WHIRLPOOL PILEDRIVER PETAL_DANCE'''.split()


def cfg(variant='battle-normal'):
    return dict(speed.configuration(variant), variant=variant)


def moves(jobs):
    configurations = []
    for variant in ('production', 'battle-normal'):
        local = motion.prepare(variant, MOVES, 'normal-battle-100', coherent=True)
        local.update(output_root=str(BASE / 'moves'), capture_images=True, capture_moves=CAPTURE,
                     post_menu_frames=32)
        configurations.append(local)
    indexes = constants(ROOT / 'constants/move_constants.asm')
    tasks = [(c, m, indexes[m], s, q) for c in configurations for m in MOVES
             for s in ('player', 'foe') for q in PHASES]
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(speed.move_job, tasks):
            results.append(row)
            if len(results) % 40 == 0 or row['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), move=row['move'],
                                     side=row['side'], issues=row['issues'])), flush=True)
    report = dict(moves=MOVES, configurations=configurations, cases=len(results), results=results)
    (BASE / 'moves/report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), failures=sum(bool(r['issues']) for r in results))))


def audio_setup(task):
    variant, q = task
    return audio.prepare(cfg(variant), BASE / 'audio' / variant / f'q{q}', 1, q)


def audio_suite(jobs):
    with ProcessPoolExecutor(max_workers=8) as pool:
        configurations = list(pool.map(audio_setup, [(v, q) for v in ('production', 'battle-normal') for q in PHASES]))
    tasks = []
    for local in configurations:
        folder = Path(local['output'])
        repo = Repository(ROOT, Path(local['rom']), Path(local['sym']))
        factory = audio.factory(repo, folder)
        order = offset(repo.symbols['NewPokedexOrder'])
        for name in audio.SPECIES:
            n = performance.names().index(name)
            index = int.from_bytes(repo.rom[order + n*2:order + n*2 + 2], 'little')
            for context in ('player', 'blocking', 'stereo'):
                donor = local['states']['caterpie']['encounter'] if context == 'player' else str(folder / 'party.s0')
                state = folder / f'{name}-{context}.s0'
                subprocess.run([str(factory), local['rom'], donor, str(index), context, str(state)], check=True, capture_output=True)
                local['states'][name][context] = str(state)
            for context in ('stats', 'catch', 'faint', 'player', 'blocking', 'stereo'):
                speed_expected = int(local['variant'] == 'battle-normal' and context in ('stats', 'blocking', 'stereo'))
                tasks.append((dict(local, expected_double_speed=speed_expected), name, context))
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for i, row in enumerate(pool.map(audio.execute, tasks)):
            row['variant'] = tasks[i][0]['variant']
            results.append(row)
            if len(results) % 40 == 0 or row['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), species=row['species'],
                                     context=row['context'], issues=row['issues'])), flush=True)
    record = dict(configurations=configurations, results=results, cases=len(results))
    (BASE / 'audio/report.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), failures=sum(bool(r['issues']) for r in results))))


def registration():
    local = cfg()
    repo = Repository(ROOT, Path(local['rom']), Path(local['sym']))
    output = BASE / 'registration'
    output.mkdir(exist_ok=True)
    catches = []
    for species in ORIGINAL:
        source = BASE / 'audio/battle-normal/q0' / f'{species}-catch'
        result = json.loads((source / 'result.json').read_text())
        if result['issues']:
            raise RuntimeError(result)
        state = output / f'{species}-registration.s0'
        shutil.copy2(source / 'registration.s0', state)
        catches.append(dict(species=species, registration_sha256=sha256(state.read_bytes()),
                            source=str(source), result=result))
    (output / 'report.json').write_text(json.dumps(dict(**repo.hashes, catches=catches), indent=2) + '\n')
    print(json.dumps(dict(catches=len(catches), registration=str(output))))


def odd_setup(task):
    variant, quarter = task
    return audio.prepare(cfg(variant), BASE / 'odd-timer' / variant / f'q{quarter}', 1, quarter)


def odd_timer(jobs):
    # Odd-period compatibility is shared-routine coverage. Native fainting
    # itself is normal-speed in this prototype and is covered by audio_suite.
    with ProcessPoolExecutor(max_workers=8) as pool:
        configurations = list(pool.map(odd_setup, [(v, q) for v in ('final', 'battle-normal') for q in PHASES]))
    tasks = []
    for local in configurations:
        output = Path(local['output'])
        repo = Repository(ROOT, Path(local['rom']), Path(local['sym']))
        factory = audio.factory(repo, output)
        order = offset(repo.symbols['NewPokedexOrder'])
        for name in audio.SPECIES:
            if not repo.load([name])[0].sample_blocks:
                continue
            ordinal = performance.names().index(name)
            index = int.from_bytes(repo.rom[order + 2*ordinal:order + 2*ordinal + 2], 'little')
            state = output / f'{name}-altered.s0'
            subprocess.run([str(factory), local['rom'], str(output / 'party.s0'), str(index),
                            'altered', str(state)], check=True, capture_output=True)
            local['states'][name]['altered'] = str(state)
            tasks.append((dict(local, expected_double_speed=1), name, 'altered'))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(audio.execute, tasks))
    for task, row in zip(tasks, rows):
        row['variant'] = task[0]['variant']
    baseline = {(r['species'], r['quarter']): r for r in rows if r['variant'] == 'final'}
    comparisons = [dict(species=r['species'], quarter=r['quarter'],
        issues=audio.compare_playback(baseline[r['species'], r['quarter']], r))
        for r in rows if r['variant'] == 'battle-normal']
    report = dict(cases=len(rows), configurations=configurations, results=rows, comparisons=comparisons)
    (BASE / 'odd-timer/report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), setup_failures=sum(bool(r['issues']) for r in rows),
        misses=sum(bool(r['known_misses']) for r in rows),
        differences=sum(bool(r['issues']) for r in comparisons))))


def manual():
    output = BASE / 'manual-review'
    output.mkdir(exist_ok=True)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    report = review.create(repo, speed.BATTERY, output / 'animation-review.sav', review.PARTY, ADDED)
    (output / 'animation-review.json').write_text(json.dumps(report, indent=2) + '\n')
    for variant, arm in (('production', 'normal'), ('battle-normal', 'battle-normal')):
        target = output / arm / ('pokecrystal-animation-' + arm)
        target.parent.mkdir(exist_ok=True)
        source = Path(cfg(variant)['rom'])
        for ext in ('.gbc', '.sym', '.map'):
            shutil.copy2(source.with_suffix(ext), target.with_suffix(ext))
        shutil.copy2(output / 'animation-review.sav', target.with_suffix('.sav'))
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(review_job, [('normal', output), ('battle-normal', output)]))
    (output / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(dict(moves=report['moves'], verified=len(results))))


def review_job(task):
    return review.verify(task[0], review=task[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=('moves', 'audio', 'odd-timer', 'registration', 'dex-prepare', 'custom', 'manual'))
    parser.add_argument('--jobs', type=int, default=24)
    args = parser.parse_args()
    BASE.mkdir(exist_ok=True)
    if args.suite == 'moves':
        return moves(args.jobs)
    if args.suite == 'audio':
        return audio_suite(args.jobs)
    if args.suite == 'odd-timer':
        return odd_timer(args.jobs)
    if args.suite == 'registration':
        return registration()
    if args.suite == 'manual':
        return manual()
    if args.suite == 'custom':
        from .global_custom_menus import execute
        result = execute('battle-normal')
        (BASE / 'custom-menus.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(cases=result['cases'], issues=result['issues'])))
        return
    local = cfg()
    performance.prepare(Path(local['rom']), Path(local['sym']), speed.BATTERY, BASE / 'dex-setup')
    print(json.dumps(dict(config=str(BASE / 'dex-setup/config.json'))))


if __name__ == '__main__':
    main()
