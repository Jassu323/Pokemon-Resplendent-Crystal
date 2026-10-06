"""Frame-by-frame, real-input Modes/Unown transition qualification."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from PIL import Image

from .assets import Repository
from .cold_listing import Driver, ROOT, audit, bootstrap, move
from .description_ui import settle
from .dex_modes import audit_menu
from .info_ui import BOOT, press, ready as info_ready
from .moves_ui import ready as moves_ready
from .legacy_listing import open_mode_screen, private_battery
from .area_ui import reach


def capture(driver, output, name, key, finish):
    folder = output / name
    folder.mkdir(exist_ok=True)
    before = []
    for at in range(16):
        driver.run(frames=1)
        path = folder / f'before-{at:02}.ppm'
        driver.command(f'image {path}')
        with Image.open(path) as image:
            before.append(image.convert('RGB').tobytes())
        path.unlink()
    start = driver.command('peek')['t']
    driver.events.clear()
    driver.command(f'perfimages {folder}/display')
    driver.command('perf 1')
    press(driver, key)
    finish()
    driver.run(frames=3)
    end = driver.command('peek')['t']
    driver.command('perfimages -')
    driver.command('perf 0')
    events = [e for e in driver.events if e['event'] == 'perf_frame']
    after = []
    for at in range(16):
        driver.run(frames=1)
        path = folder / f'after-{at:02}.ppm'
        driver.command(f'image {path}')
        with Image.open(path) as image:
            after.append(image.convert('RGB').tobytes())
        path.unlink()
    # Ignore only pixels that actually animate/blink on the settled owners.
    # The remaining pixels must be wholly old, wholly new, or a black mask.
    stable = [i for i in range(160 * 144) if all(
        sample[i*3:i*3+3] == before[0][i*3:i*3+3] for sample in before)
        and all(sample[i*3:i*3+3] == after[0][i*3:i*3+3] for sample in after)]
    old = bytes(v for i in stable for v in before[0][i*3:i*3+3])
    new = bytes(v for i in stable for v in after[0][i*3:i*3+3])
    observations = []
    for path in sorted(folder.glob('display-*.ppm')):
        with Image.open(path) as image:
            pixels = image.convert('RGB').tobytes()
            masked = bytes(v for i in stable for v in pixels[i*3:i*3+3])
            kind = 'black' if not any(pixels) else 'old' if masked == old else 'new' if masked == new else 'mixed'
            observations.append(kind)
            image.save(path.with_suffix('.png'))
        path.unlink()
    issues = []
    if 'mixed' in observations:
        issues.append('mixed_display_frame')
    if 'new' not in observations:
        issues.append('destination_not_displayed')
    ranks = dict(old=0, black=1, new=2, mixed=1)
    if any(ranks[a] > ranks[b] for a, b in zip(observations, observations[1:])):
        issues.append('reveal_reverted')
    if any(e['white'] == 160 * 144 for e in events):
        issues.append('white_flash')
    if any(not e['lcdc'] & 0x80 for e in events):
        issues.append('lcd_disabled')
    first = next((i for i, k in enumerate(observations) if k != 'old'), None)
    complete = next((i for i, k in enumerate(observations) if k == 'new'), None)
    def intervals(at):
        return (events[at]['boundary_t'] - start) / 70224 if at is not None else None
    first_frames, complete_frames = intervals(first), intervals(complete)
    return dict(issues=issues, displayed=observations, stable_pixels=len(stable),
                key=key,
                first_display_index=first + 1 if first is not None else None,
                complete_display_index=complete + 1 if complete is not None else None,
                first_frames=first_frames, complete_frames=complete_frames,
                first_ms=first_frames * 70224 / 4194304 * 1000 if first_frames is not None else None,
                complete_ms=complete_frames * 70224 / 4194304 * 1000 if complete_frames is not None else None,
                start_t=start, end_t=end, events=events)


def case(task):
    config, fixture, presentation, index, phase, output = task
    output = Path(output) / f'{presentation}-{index:03}-{phase}'
    output.mkdir(exist_ok=True)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, fixture, output / 'trace.log')
    records, issues, playback = {}, [], None
    try:
        bootstrap(driver)
        for _ in range(index if presentation else index // 3):
            move(driver, 'down')
        if not presentation:
            for _ in range(index % 3):
                move(driver, 'right')
        driver.run(('end_loop',))
        if driver.command('peek')['index'] != index:
            raise RuntimeError('Starting navigation selected the wrong species')
        prior = config.get('prior_view')
        if prior:
            driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
            settle(driver)
            press(driver, 'right')
            if prior == 'moves':
                press(driver, 'right')
            press(driver, 'a')
            if prior == 'info':
                ui = info_ready(driver, 0)
                if ui['info_pages'] > 1:
                    press(driver, 'a')
                    info_ready(driver, 1)
            else:
                moves_ready(driver)
            press(driver, 'b')
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(('end_loop',))
        driver.command('rawcolor')
        driver.run(frames=2 + phase / 8)
        def menu_ready():
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
        def listing_ready():
            driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        def unown_ready():
            reach(driver, repo, 'Pokedex_UpdateUnownMode')
        records['listing-to-modes'] = capture(driver, output, 'listing-to-modes', 'select', menu_ready)
        issues += audit_menu(driver.command('ui'), True, presentation)
        records['modes-cancel'] = capture(driver, output, 'modes-cancel',
                                         'select' if phase & 1 else 'b', listing_ready)
        open_mode_screen(driver)
        target = 1 - presentation
        press(driver, 'down' if target else 'up')
        records['modes-switch'] = capture(driver, output, 'modes-switch', 'a', listing_ready)
        open_mode_screen(driver)
        for _ in range(2 - target):
            press(driver, 'down')
        records['modes-to-unown'] = capture(driver, output, 'modes-to-unown', 'a', unown_ready)
        press(driver, 'right')
        press(driver, 'left')
        records['unown-to-modes'] = capture(driver, output, 'unown-to-modes',
                                           'a' if phase & 1 else 'b', menu_ready)
        issues += audit_menu(driver.command('ui'), True, 2)
        records['unown-modes-to-listing'] = capture(driver, output, 'unown-modes-to-listing', 'b', listing_ready)
        state = driver.command('peek')
        if state['index'] != index or state['presentation'] != target:
            issues.append('selection_or_presentation_changed')
        for name, record in records.items():
            issues.extend(f'{name}:{issue}' for issue in record['issues'])
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept', 'animation_miss', 'audio_miss'), key='a')
        final = settle(driver)
        asset = repo.load([config['names'][index]])[0]
        playback = audit(asset, accepted, driver.events, final, cold=False, expected_double_speed=1)
        issues.extend('post_menu:' + issue for issue in playback['issues'])
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / 'failure')
    finally:
        driver.close()
    result = dict(presentation=presentation, index=index, phase=phase, issues=issues,
                  transitions=records, playback=playback)
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--indices', default='0')
    parser.add_argument('--phases', type=int, default=4)
    parser.add_argument('--tag', default='mode-transitions')
    parser.add_argument('--prior-view', choices=('info', 'moves'))
    args = parser.parse_args()
    output = args.output.resolve()
    config = json.loads((output / 'legacy/config.json').read_text())
    config['prior_view'] = args.prior_view
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    if args.phases not in range(1, 9) or Path(args.tag).name != args.tag:
        raise ValueError('Use 1-8 input phases and a single directory name')
    target = output / args.tag
    target.mkdir(exist_ok=True)
    tasks = []
    for presentation in (0, 1):
        fixture = target / f'fixture-{presentation}.sav'
        private_battery(config, fixture, presentation=presentation, unown_unlocked=True)
        tasks.extend((config, str(fixture), presentation, int(index), phase, str(target))
                     for index in args.indices.split(',') for phase in range(args.phases))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(case, tasks))
    summary = dict(cases=len(results), transitions=sum(len(r['transitions']) for r in results),
                   failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}), flush=True)
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
