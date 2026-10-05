"""Paired normal-speed audio contexts, with and without a double-speed Dex visit.

Species contexts are explicitly generated on native, matching-link checkpoints.
Sound/PPU state survives the real Dex entry/exit; no sound reset or timer repair
is injected. Party Stats and wild encounter/catch use normal controls thereafter.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import wave

from .assets import Repository, offset
from .cold_listing import Driver, ROOT, KEY
from .info_ui import BOOT
from .new_entry import CORE_FILES
from .new_entry_sweep import ORIGINAL, ADDITIONAL
from .performance import core, T, names
from .performance_lifecycle import open_menu
from .shared_menu_fixtures import make_fixture

SPECIES = ORIGINAL + ADDITIONAL
EXTRA = dict(timer_block=('SampledCry_AsyncTimerTick', False),
             wave_block=('@wave_committed', False),
             audio_arm=('SampledCry_ArmCachedPlayback', False),
             faint=('PlayFaintingCry', False),
             entry=('NewPokedexEntry', False),
             entry_finished=('NewDexEntry_AnimationCompleted', False))


def run(driver, repo, label=None, frames=1, key=None):
    bank, pc = repo.symbols[label] if label else (0, 0xffff)
    state = driver.command(f'restorerun {bank} {pc} {int(frames * T)} {KEY.get(key, 0)}')
    if label and not at(state, repo, label):
        raise RuntimeError(f'Did not reach {label}: {state}')
    return state


def at(state, repo, label):
    bank, pc = repo.symbols[label]
    return state['pc'] == pc and (pc < 0x4000 or state['bank'] == bank)


def value(driver, repo, label, size=1):
    bank, address = repo.symbols[label]
    return int.from_bytes(bytes.fromhex(driver.command(f'perfram {bank} {address} {size}')['bytes']), 'little')


def tap(driver, repo, key, held=4, released=4):
    run(driver, repo, frames=held, key=key)
    return run(driver, repo, frames=released)


def until(driver, repo, label, key='a', attempts=160):
    bank, pc = repo.symbols[label]
    for _ in range(attempts):
        for button in (key, None):
            state = driver.command(f'restorerun {bank} {pc} {8*T} {KEY.get(button, 0)}')
            if at(state, repo, label):
                return state
    raise RuntimeError(f'Input did not reach {label}: {state}')


def factory(repo, output):
    header = output / 'fixture-symbols.h'
    lines = []
    for short, label in dict(PARTY='PartyMenuSelect', ENEMY='LoadEnemyMon',
                             ALLOCATE='GetPokemonIDFromIndex', CRY='PlayMonCry',
                             STEREO='PlayStereoCry', LOAD='LoadCry',
                             PERIOD='PlayLoadedSampledCryWithPeriod', WAIT='WaitCrySFX').items():
        bank, pc = repo.symbols[label]
        lines += [f'#define B_{short} {bank}', f'#define P_{short} {pc}']
    for label in ('wPartySpecies', 'wPartyMon1Species', 'wTempEnemyMonSpecies', 'wWildMon',
                  'wPokedexCaught', 'wPokedexSeen', 'wPokemonIndexTableEntries'):
        bank, pc = repo.symbols[label]
        lines += [f'#define B_{label} {bank}', f'#define S_{label} {pc}']
    bank, pc = repo.symbols['wUnlockedUnowns']
    lines += [f'#define B_wUnlockedUnowns {bank}', f'#define S_wUnlockedUnowns {pc}']
    header.write_text('\n'.join(lines) + '\n')
    sameboy = Path.home() / 'Documents/GitHub/SameBoy'
    binary = output / 'audio-fixture'
    subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="audio-fixture"',
                    f'-DPERF_AUDIO_FIXTURE_SYMBOLS="{header}"',
                    str(ROOT / 'tools/dex_timing/probes/performance_audio_fixture.c'),
                    *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(binary)], check=True)
    return binary


def prepare(config, output, visit, quarter):
    output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    bank, pc = repo.symbols['SampledCry_RestartCH3']
    if repo.rom[offset((bank, pc)) + 23] != 0xc9:
        raise RuntimeError('Linked CH3 restart body changed')
    repo.symbols['@wave_committed'] = bank, pc + 23
    binary = core(repo, output, EXTRA)
    battery = output / 'capture-copy.sav'
    make_fixture(repo, Path(config['battery']), battery, ('ROUTE_30', 13, 49), capture=True)
    driver = Driver(binary, config['rom'], BOOT, battery, output / 'setup.log')
    try:
        open_menu(driver)
        driver.command(f'run 0 {quarter} 0')
        for _ in range(visit):
            driver.run(('listing',), 600, 'a')
            driver.run(frames=5)
            returned = driver.run(('start_menu',), 600, 'b')
            if returned['double_speed'] != config.get('expected_double_speed', 0):
                raise RuntimeError('Unexpected speed after the Dex')
            driver.run(('start_menu',), 60)
            driver.run(frames=4)
        # Save the normal-speed, post-switch menu with its APU state intact.
        driver.command(f'save {output / "menu.s0"}')
        tap(driver, repo, 'down')
        until(driver, repo, 'PartyMenuSelect')
        driver.command(f'save {output / "party.s0"}')
        driver.command(f'load {output / "menu.s0"}')
        driver.run(('overworld',), 600, 'b')
        driver.run(frames=120)
        # The saved location is a grass corridor; walk up/down naturally until
        # the enemy initializer, before any enemy cry or picture preparation.
        bank, pc = repo.symbols['LoadEnemyMon']
        for step in range(300):
            key = 'up' if (step // 20) % 2 == 0 else 'down'
            state = driver.command(f'restorerun {bank} {pc} {12*T} {KEY[key]}')
            if at(state, repo, 'LoadEnemyMon'):
                break
        else:
            raise RuntimeError('No native grass encounter')
        driver.command(f'save {output / "encounter.s0"}')
    finally:
        driver.close()
    compiled = factory(repo, output)
    ordered = names()
    order_at = offset(repo.symbols['NewPokedexOrder'])
    states = {}
    for name in SPECIES:
        ordinal = ordered.index(name)
        index = int.from_bytes(repo.rom[order_at+2*ordinal:order_at+2*ordinal+2], 'little')
        states[name] = {}
        for context in ('party', 'encounter'):
            destination = output / f'{name}-{context}.s0'
            result = subprocess.run([str(compiled), config['rom'], str(output / (context+'.s0')),
                                     str(index), context, str(destination)], capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f'Fixture failed {context}/{name}: {result.returncode} {result.stderr}')
            states[name][context] = str(destination)
    local = dict(config, core=str(binary), battery=str(battery), output=str(output),
                 states=states, visits=visit, quarter=quarter)
    (output / 'config.json').write_text(json.dumps(local, indent=2) + '\n')
    return local


def audio_segments(events):
    starts = [i for i, event in enumerate(events)
              if event['event'] == 'perf_phase' and event['name'] == 'audio_arm']
    result = []
    for n, begin in enumerate(starts):
        end = starts[n+1] if n+1 < len(starts) else len(events)
        row = events[begin:end]
        blocks = [e for e in row if e['event'] == 'wave_block']
        ticks = [e for e in row if e['event'] == 'perf_phase' and e['name'] == 'timer_block']
        periods = [b['t'] - a['t'] for a, b in zip(ticks, ticks[1:])]
        stops = [e for e in row if e['event'] in ('audio_stop', 'audio_miss')]
        digest = hashlib.sha256(b''.join(bytes.fromhex(e['wave']) for e in blocks)).hexdigest()
        result.append(dict(start_t=events[begin]['t'], expected_blocks=events[begin]['remaining'],
                           blocks=len(blocks), wave_sha256=digest,
                           wave_blocks=[e['wave'] for e in blocks],
                           timer_configs=sorted(set((e['tac'] & 7, e['tma']) for e in ticks)),
                           frequencies=sorted(set(e['frequency'] for e in blocks)),
                           speed_values=sorted(set(e['speed'] for e in blocks)),
                           median_period=statistics.median(periods) if periods else None,
                           elapsed_t=ticks[-1]['t']-ticks[0]['t'] if ticks else None, stops=stops))
    return result


def compare_playback(baseline, candidate):
    """Compare sample content and hardware settings, not IRQ-entry jitter."""
    issues = []
    if baseline['issues'] or candidate['issues']:
        return ['test setup rejected']
    if len(baseline['segments']) != len(candidate['segments']):
        return ['sampled segment count changed']
    for index, (a, b) in enumerate(zip(baseline['segments'], candidate['segments'])):
        for key in ('expected_blocks', 'blocks', 'wave_sha256', 'timer_configs', 'frequencies', 'speed_values'):
            if a[key] != b[key]:
                issues.append(f'segment {index}: {key} changed')
        stop = lambda row: [(e['event'], e.get('remaining')) for e in row['stops']]
        if stop(a) != stop(b):
            issues.append(f'segment {index}: exhaustion/completion changed')
    return issues


def compare_reports(paths, output):
    rows = [row for path in paths for row in json.loads((path / 'report.json').read_text())['results']]
    baseline = {(r['species'], r['context'], r['quarter']): r for r in rows if r['variant'] == 'baseline'}
    comparisons = []
    for row in rows:
        if row['variant'] == 'baseline':
            continue
        reference = baseline[row['species'], row['context'], row['quarter']]
        comparisons.append(dict(species=row['species'], context=row['context'], quarter=row['quarter'],
                                variant=row['variant'], issues=compare_playback(reference, row)))
    result = dict(cases=len(rows), sampled_segments=sum(len(r['segments']) for r in rows),
                  comparisons=comparisons, differences=sum(bool(c['issues']) for c in comparisons),
                  setup_failures=sum(bool(r['issues']) for r in rows))
    (output / 'audio-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'comparisons'}))
    return bool(result['differences'] or result['setup_failures'])


def execute(job):
    config, name, context = job
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    output = Path(config['output']) / f'{name}-{context}'
    output.mkdir(exist_ok=True)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / 'run.log')
    result = dict(species=name, context=context, visits=config['visits'], quarter=config['quarter'], issues=[])
    raw = output / 'audio.pcm'
    try:
        state_kind = 'party' if context == 'stats' else (
            context if context in ('player', 'blocking', 'stereo', 'altered') else 'encounter')
        driver.command(f'load {config["states"][name][state_kind]}')
        driver.command('audit 1')
        driver.command('perf 1')
        driver.command(f'perfaudio {raw}')
        driver.events.clear()
        if context in ('blocking', 'stereo', 'altered'):
            run(driver, repo, 'PartyMenuSelect', frames=600)
        elif context == 'player':
            until(driver, repo, 'BattleMenu.loop')
            run(driver, repo, frames=240)
        elif context == 'stats':
            until(driver, repo, 'MonMenuLoop')
            until(driver, repo, 'StatsScreenMain.loop')
            run(driver, repo, frames=240)
        else:
            until(driver, repo, 'BattleMenu.loop')
            driver.command(f'save {output / "battle-menu.s0"}')
            run(driver, repo, frames=60)
            if context == 'faint':
                # Native battle commands: first move, then dismiss text. The
                # fixture's lead is the original high-level party Pokemon.
                until(driver, repo, 'MoveSelectionScreen.menu_loop')
                run(driver, repo, frames=40)
                # This copied party's third move is Razor Leaf, rather than
                # its Ghost-immune first move, Body Slam. Verify the index.
                moves = value(driver, repo, 'wBattleMonMoves', 4).to_bytes(4, 'little')
                table_bank, table_address = repo.symbols['wMoveIndexTableEntries']
                move_index = int.from_bytes(bytes.fromhex(driver.command(
                    f'perfram {table_bank} {table_address+2*(moves[2]-1)} 2')['bytes']), 'little')
                if move_index != 75:
                    raise RuntimeError('Fixture lead no longer has Razor Leaf in slot three')
                for _ in range(12):
                    if value(driver, repo, 'wMenuCursorY') == 3:
                        break
                    tap(driver, repo, 'down', 12, 16)
                else:
                    raise RuntimeError('Move cursor did not reach Razor Leaf')
                until(driver, repo, 'FaintEnemyPokemon')
                run(driver, repo, frames=240)
            else:
                tap(driver, repo, 'down')
                until(driver, repo, 'BattlePack.loop')
                for _ in range(10):
                    if value(driver, repo, 'wCurPocket') == 1:
                        break
                    tap(driver, repo, 'right', 4, 30)
                else:
                    raise RuntimeError('Balls pouch not reached')
                until(driver, repo, 'NewPokedexEntry')
                driver.command(f'save {output / "registration.s0"}')
                until(driver, repo, 'NewPokedexEntry.WaitPressAorB_AnimateFrontpic', key=None)
                run(driver, repo, frames=240)
        driver.command('perfaudio -')
        result['speed_after'] = driver.command('peek')['double_speed']
        result['segments'] = audio_segments(driver.events)
        result['known_misses'] = [e for e in driver.events if e['event'] == 'audio_miss']
        expected_speed = config.get('expected_double_speed', 0)
        if result['speed_after'] != expected_speed or any(s['speed_values'] != [expected_speed] for s in result['segments']):
            result['issues'].append('audio context changed the expected CPU speed')
        if repo.load([name])[0].sample_blocks and not result['segments']:
            result['issues'].append('expected sampled cry never started')
        with wave.open(str(output / 'audio.wav'), 'wb') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(raw.read_bytes())
    except Exception as error:
        result['issues'].append(str(error))
    finally:
        if raw.exists():
            raw.unlink()
        with gzip.open(output / 'events.jsonl.gz', 'wt') as log:
            log.write(''.join(json.dumps(e) + '\n' for e in driver.events))
        driver.close()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def retest(output, jobs):
    """Preserve failed harness evidence and retry only rejected setup cases."""
    report = json.loads((output / 'report.json').read_text())
    with gzip.open(output / 'initial-harness-report.json.gz', 'wt') as archive:
        archive.write(json.dumps(report))
    by_key = {(c['variant'], c['quarter']): c for c in report['configurations']}
    binaries = {}
    work, positions = [], []
    for position, row in enumerate(report['results']):
        if not row['issues']:
            continue
        config = by_key[row['variant'], row['quarter']]
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        if row['species'] == 'unown_a':
            if config['rom'] not in binaries:
                binaries[config['rom']] = factory(repo, Path(config['output']))
            for context in ('party', 'encounter'):
                state = config['states']['unown_a'][context]
                subprocess.run([str(binaries[config['rom']]), config['rom'],
                                str(Path(config['output']) / (context+'.s0')), '201', context, state], check=True,
                               capture_output=True, text=True)
        local = dict(config, output=str(Path(config['output']) / 'retested'))
        Path(local['output']).mkdir(exist_ok=True)
        work.append((local, row['species'], row['context']))
        positions.append(position)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for position, result in zip(positions, pool.map(execute, work)):
            result['variant'] = report['results'][position]['variant']
            report['results'][position] = result
            if result['issues']:
                print(json.dumps(result['issues']), flush=True)
    report['retested_harness_cases'] = len(work)
    report['setup_failures'] = sum(bool(r['issues']) for r in report['results'])
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=report['cases'], retested=len(work), setup_failures=report['setup_failures'])))
    return bool(report['setup_failures'])


def shared_paths(source, output, jobs):
    prior = json.loads((source / 'report.json').read_text())
    configurations, work = [], []
    binaries = {}
    for old in prior['configurations']:
        folder = output / (old['variant'] + '-q' + str(old['quarter']))
        folder.mkdir(parents=True, exist_ok=True)
        repo = Repository(ROOT, Path(old['rom']), Path(old['sym']))
        if old['rom'] not in binaries:
            binaries[old['rom']] = factory(repo, folder)
        config = dict(old, output=str(folder), states={name: dict(states) for name, states in old['states'].items()})
        order_at = offset(repo.symbols['NewPokedexOrder'])
        for name in SPECIES:
            ordinal = names().index(name)
            index = int.from_bytes(repo.rom[order_at+2*ordinal:order_at+2*ordinal+2], 'little')
            for context in ('player', 'blocking', 'stereo'):
                donor = old['states']['caterpie']['encounter'] if context == 'player' else str(Path(old['output']) / 'party.s0')
                state = folder / f'{name}-{context}.s0'
                subprocess.run([str(binaries[old['rom']]), old['rom'], donor, str(index), context, str(state)],
                               check=True, capture_output=True, text=True)
                config['states'][name][context] = str(state)
                work.append((config, name, context))
        configurations.append(config)
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for i, result in enumerate(pool.map(execute, work), 1):
            result['variant'] = work[i-1][0]['variant']
            results.append(result)
            if i % 40 == 0 or result['issues']:
                print(json.dumps(dict(done=i, total=len(work), issues=result['issues'])), flush=True)
    report = dict(configurations=configurations, results=results, cases=len(results),
                  setup_failures=sum(bool(r['issues']) for r in results))
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), setup_failures=report['setup_failures'])))
    return bool(report['setup_failures'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--reuse', action='store_true')
    parser.add_argument('--retest-harness', action='store_true')
    parser.add_argument('--shared-from', type=Path)
    parser.add_argument('--compare', type=Path, nargs='+')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.compare:
        return int(compare_reports(args.compare, args.output))
    if args.shared_from:
        return int(shared_paths(args.shared_from.resolve(), args.output, args.jobs))
    if args.retest_harness:
        return int(retest(args.output, args.jobs))
    jobs = []
    configurations = []
    preparations = []
    for variant, source, visits in (('baseline', args.baseline, 1), ('candidate-direct', args.candidate, 0),
                                    ('candidate-post-dex', args.candidate, 1), ('candidate-repeat', args.candidate, 4)):
        base = json.loads(source.read_text())
        for q in ((0,) if args.smoke else (0, 17556, 35112, 52668)):
            output = args.output / f'{variant}-q{q}'
            preparations.append((variant, base, output, visits, q))
    if args.reuse:
        prepared = [json.loads((item[2] / 'config.json').read_text()) for item in preparations]
    else:
        with ProcessPoolExecutor(max_workers=min(8, args.jobs)) as pool:
            prepared = list(pool.map(prepare_job, preparations))
    for preparation, config in zip(preparations, prepared):
        variant = preparation[0]
        config['variant'] = variant
        configurations.append(config)
        for name in (('dusknoir', 'caterpie') if args.smoke else SPECIES):
            for context in ('stats', 'catch', 'faint'):
                jobs.append((config, name, context))
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for i, result in enumerate(pool.map(execute, jobs), 1):
            result['variant'] = jobs[i-1][0]['variant']
            results.append(result)
            if i % 20 == 0 or result['issues']:
                print(json.dumps(dict(done=i, total=len(jobs), variant=result['variant'], species=result['species'],
                                      context=result['context'], issues=result['issues'])), flush=True)
    report = dict(configurations=configurations, results=results, cases=len(results),
                  setup_failures=sum(bool(r['issues']) for r in results))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), setup_failures=report['setup_failures'])))
    return int(bool(report['setup_failures']))


def prepare_job(item):
    variant, base, output, visits, q = item
    result = prepare(base, output, visits, q)
    print(json.dumps(dict(prepared=variant, quarter=q)), flush=True)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
