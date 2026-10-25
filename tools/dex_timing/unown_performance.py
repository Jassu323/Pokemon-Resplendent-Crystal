"""Measure current Unown selection updates without changing the game ROM.

Use normal input on private batteries, all forms in both Listing origins, and
native frame captures for the first change. No cartridge RAM is patched live.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from PIL import Image

from .assets import Repository, sha256
from .cold_listing import ROOT, Driver, KEY, bootstrap
from .info_ui import BOOT
from .performance import HZ, T, core, result_timing
from .unown_comparison import battery
from .unown_regression import memory, press


POINTS = {
    'unown_update': ('Pokedex_UnownModeHandleDPadInput.update', True),
    'unown_picture': ('Pokedex_LoadUnownFrontpicTiles', True),
    'generic_picture': ('GetMonFrontpic', True),
    'prepare_all_frames': ('_PrepareFrontpic', True),
    'decompress': ('FarDecompress', True),
    'pad': ('PadFrontpic', True),
    'get_2bpp': ('Get2bpp', True),
    'request_2bpp': ('Request2bpp', True),
    'word': ('PrintUnownWord', True),
    'delay_frame': ('DelayFrame', True),
    'static_prepare': ('PokedexUnown_PreparePicture', True),
    'static_publish': ('PokedexUnown_Publish', True),
    'static_commit': ('PokedexUnown_Publish.commit', False),
    'static_committed': ('PokedexUnown_Publish.committed', False),
}


def reach(driver, symbols, label, key=0):
    bank, pc = symbols[label]
    result = driver.command(f'restorerun {bank} {pc} {600 * T} {key}')
    if result['hit'] < 0:
        raise RuntimeError('Could not reach ' + label)
    return result


def image(driver, path):
    driver.command(f'image {path.with_suffix(".ppm")}')
    with Image.open(path.with_suffix('.ppm')) as capture:
        capture.save(path.with_suffix('.png'))
        pixels = capture.convert('RGB')
        picture = pixels.crop((48, 40, 104, 96)).tobytes(), pixels.tobytes()
    path.with_suffix('.ppm').unlink()
    return picture


def change(driver, repo, output, direction, previous, phase=0, capture=False):
    folder = output / f'{direction}-{previous:02}-q{phase}'
    folder.mkdir()
    if phase:
        driver.command(f'run 0 {phase} 0')
    old_picture, old_full = image(driver, folder / 'before') if capture else (None, None)
    if capture:
        driver.command(f'perfimages {folder}/frame')
    initial = driver.command('perf 1')
    driver.events.clear()
    accepted = reach(driver, repo.symbols,
                     'Pokedex_UnownModeHandleDPadInput.update', KEY[direction])
    ready = reach(driver, repo.symbols, 'Pokedex_UpdateUnownMode')
    driver.run(frames=4)
    final = driver.command('perf 0')
    driver.command('perfimages -')
    events = list(driver.events)
    index = memory(driver, repo.symbols, 'wDexCurUnownIndex')[0]
    expected = previous + (1 if direction == 'right' else -1)
    if index != expected:
        raise RuntimeError(f'Unexpected selection {index}, expected {expected}')
    timing = result_timing(events, initial, final, 'full', initial['t'], accepted['t'])
    if not timing['complete_visible']:
        raise RuntimeError('No complete stable display observed')
    record = dict(direction=direction, previous=previous, selected=index,
                  phase=phase, accepted_ms=(accepted['t'] - initial['t']) * 1000 / HZ,
                  next_input_loop_ms=(ready['t'] - initial['t']) * 1000 / HZ,
                  timing=timing)
    commits = [e for e in events if e['event'] == 'perf_phase' and e['name'] == 'static_commit']
    finished = [e for e in events if e['event'] == 'perf_phase' and e['name'] == 'static_committed']
    if 'PokedexUnown_Publish' in repo.symbols:
        if len(commits) != 1 or len(finished) != 1 or not 144 <= commits[0]['ly'] <= 145 or not 144 <= finished[0]['ly'] <= 152:
            raise RuntimeError('Static publication exceeded VBlank: ' + str(commits + finished))
        record['commit'] = dict(start_ly=commits[0]['ly'], end_ly=finished[0]['ly'],
                              ms=(finished[0]['t'] - commits[0]['t']) * 1000 / HZ)
        frames = [e for e in events if e['event'] == 'perf_frame']
        unexpected = [e for e in frames if e['full'] not in (initial['full'], final['full'])]
        if unexpected:
            raise RuntimeError('Mixed whole-screen frames: ' + str(unexpected))
        record['whole_frame_checks'] = len(frames)
    if capture:
        new_picture, new_full = image(driver, folder / 'after')
        frames = []
        for event in events:
            if event['event'] != 'perf_frame':
                continue
            path = folder / f'frame-{event["display"]:03}.ppm'
            with Image.open(path) as screenshot:
                pixels = screenshot.convert('RGB')
                picture = pixels.crop((48, 40, 104, 96)).tobytes()
                state = 'old' if picture == old_picture else 'new' if picture == new_picture else 'partial'
                whole = pixels.tobytes()
                full_state = 'old' if whole == old_full else 'new' if whole == new_full else 'partial'
                if state == 'partial' or event['display'] == 1:
                    pixels.save(path.with_suffix('.png'))
            path.unlink()
            frames.append(dict(display=event['display'], state=state, full_state=full_state,
                               ms=(event['t'] - initial['t']) * 1000 / HZ))
        record['portrait_frames'] = frames
        record['partial_portrait_frames'] = sum(v['state'] == 'partial' for v in frames)
        record['partial_full_frames'] = sum(v['full_state'] == 'partial' for v in frames)
        if 'PokedexUnown_Publish' in repo.symbols and record['partial_full_frames']:
            raise RuntimeError('Non-atomic Unown frame: ' + str(frames))
    (folder / 'events.json').write_text(json.dumps(events, separators=(',', ':')) + '\n')
    (folder / 'summary.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def run(output, donor, source=ROOT, rom=None, sym=None, model='E'):
    output.mkdir(parents=True, exist_ok=False)
    rom = rom or source / 'pokecrystal.gbc'
    sym = sym or source / 'pokecrystal.sym'
    repo = Repository(source, rom, sym)
    hashes = dict(repo.hashes)
    donor_hash = sha256(donor.read_bytes())
    compiled = core(repo, output / 'core', extra_points=POINTS,
                    extra_flags=(f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}',))
    records, checks = [], []
    for presentation in (0, 1):
        for phase in (0, 17556, 35112, 52668):
            folder = output / f'presentation-{presentation}-q{phase}'
            folder.mkdir()
            fixture = folder / 'private.sav'
            battery(donor, repo.symbols, fixture, 26, True, presentation=presentation)
            fixture_hash = sha256(fixture.read_bytes())
            driver = Driver(compiled, repo.rom_path, BOOT, fixture, folder / 'driver.log')
            try:
                driver.command('rawcolor')
                bootstrap(driver)
                original = driver.command('peek')
                original_letter = memory(driver, repo.symbols, 'wUnownLetter')
                press(driver, 'select')
                reach(driver, repo.symbols, 'Pokedex_UpdateOptionScreen')
                for _ in range(2 - presentation):
                    press(driver, 'down')
                press(driver, 'a')
                reach(driver, repo.symbols, 'Pokedex_UpdateUnownMode')
                driver.run(frames=4)
                if memory(driver, repo.symbols, 'wDexUnownCount')[0] != 26:
                    raise RuntimeError('Not all forms were available')
                steps = 25 if phase == 0 else 1
                for previous in range(steps):
                    row = change(driver, repo, folder, 'right', previous,
                                 phase if previous == 0 else 0, capture=previous == 0)
                    row['presentation'] = presentation
                    records.append(row)
                for previous in range(steps, 0, -1):
                    row = change(driver, repo, folder, 'left', previous)
                    row['presentation'] = presentation
                    records.append(row)
                letter_ok = memory(driver, repo.symbols, 'wUnownLetter') == original_letter
                driver.run(frames=60, key='right')
                held_index = memory(driver, repo.symbols, 'wDexCurUnownIndex')[0]
                driver.run(frames=20)
                press(driver, 'b')
                reach(driver, repo.symbols, 'Pokedex_UpdateOptionScreen')
                press(driver, 'b')
                driver.run(('listing',), frames=600)
                driver.run(('end_loop',))
                returned = driver.command('peek')
                check = dict(presentation=presentation, phase=phase, letter_restored=letter_ok,
                             held_60_frames_index=held_index,
                             return_position=returned['index'] == original['index'],
                             return_presentation=returned['presentation'] == presentation,
                             battery_unchanged=sha256(fixture.read_bytes()) == fixture_hash)
                if not all(check[k] for k in ('letter_restored', 'return_position',
                                              'return_presentation', 'battery_unchanged')):
                    raise RuntimeError('Restoration failed: ' + str(check))
                checks.append(check)
                print(json.dumps(dict(presentation=presentation, phase=phase,
                                      selections=steps * 2, restoration_passed=True)), flush=True)
            finally:
                driver.close()
    metrics = defaultdict(list)
    costs = defaultdict(list)
    for row in records:
        metrics['input_accept_ms'].append(row['accepted_ms'])
        metrics['next_input_loop_ms'].append(row['next_input_loop_ms'])
        for key in ('first_visible', 'complete_visible'):
            metrics[key + '_ms'].append(row['timing'][key]['ms'])
        for name, values in row['timing']['costs'].items():
            costs[name].append(values['ms'])
    stats = lambda values: dict(minimum=min(values), median=statistics.median(values), maximum=max(values))
    forms = [repo.load(['unown_' + chr(97 + n)])[0] for n in range(26)]
    result = dict(rom_sha256=hashes['rom_sha256'], cases=len(records), models=['CGB ' + model],
                  input_phases=[0, 17556, 35112, 52668], records=records, checks=checks,
                  metrics={k: stats(v) for k, v in metrics.items()},
                  costs={k: stats(v) for k, v in costs.items()},
                  forms=[dict(form=n + 1, width=a.width, dictionary_tiles=len(a.dictionary) // 16)
                         for n, a in enumerate(forms)],
                  game_files_unchanged=Repository(source, repo.rom_path, sym).hashes == hashes,
                  donor_unchanged=sha256(donor.read_bytes()) == donor_hash)
    assert result['game_files_unchanged'] and result['donor_unchanged']
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('rom_sha256', 'cases', 'metrics', 'costs',
                                          'game_files_unchanged', 'donor_unchanged')}, indent=2))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--battery', type=Path, default=ROOT /
                     'build/dex-moves-search-final-review-20261011/legacy-input.sav')
    cli.add_argument('--source', type=Path, default=ROOT)
    cli.add_argument('--rom', type=Path)
    cli.add_argument('--sym', type=Path)
    cli.add_argument('--model', choices=('0', 'A', 'B', 'C', 'D', 'E'), default='E')
    args = cli.parse_args()
    run(args.output.resolve(), args.battery.resolve(), args.source.resolve(), args.rom, args.sym, args.model)
