"""Exact native-frame translation and atomic popup-transition A/B checks."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import tempfile

from PIL import Image

from .cold_listing import ROOT, Driver
from .info_ui import BOOT, press
from .listing_options import configuration, modal_audit, popup
from .assets import Repository
from . import performance


def transition(driver, key, name, directory):
    driver.command(f'image {directory}/before.ppm')
    before = Image.open(directory / 'before.ppm').convert('RGB')
    driver.events.clear()
    accepted = driver.command('perf 1')
    driver.command(f'perfimages {directory}/frame')
    driver.run(('animation_miss', 'audio_miss'), frames=2, key=key)
    driver.run(('animation_miss', 'audio_miss'), frames=46)
    driver.command('perfimages -')
    driver.command('perf 0')
    frames = [Image.open(path).convert('RGB') for path in sorted(directory.glob('frame-*.ppm'))]
    # Mini animation resumes on cancellation, so both ordinary final phases are
    # valid. Modal transitions themselves are static complete-frame references.
    rectangle = (64, 40, 160, 112)
    old = before.crop(rectangle).tobytes()
    references = {frame.crop(rectangle).tobytes() for frame in frames[-32:]}
    observations = ['old' if frame.crop(rectangle).tobytes() == old else
                    'new' if frame.crop(rectangle).tobytes() in references else 'mixed'
                    for frame in frames]
    issues = []
    if 'mixed' in observations or 'new' not in observations:
        issues.append(name + ': partial or missing publication')
    elif any(value != 'new' for value in observations[observations.index('new'):]):
        issues.append(name + ': outgoing frame returned after publication')
    costs = [event['elapsed'] for event in driver.events if event['event'] == 'perf_cost'
             and event['name'] == 'popover_commit' and event['elapsed'] > 100]
    if any(cost > 4300 for cost in costs):
        issues.append(name + ': VBlank budget')
    if any(event['event'] in ('animation_miss', 'audio_miss') for event in driver.events):
        issues.append(name + ': playback miss')
    display = [event for event in driver.events if event['event'] == 'perf_frame']
    first = observations.index('new') if 'new' in observations else len(display) - 1
    elapsed = (display[first]['boundary_t'] - accepted['t']) / performance.T
    return frames[-1], dict(name=name, intervals=elapsed,
                           milliseconds=elapsed * performance.T / performance.HZ * 1000,
                           costs=costs, issues=issues)


def run_arm(config, index, phase, output):
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output)
    captures, records = {}, []
    try:
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        driver.run(frames=2 + phase / 8)
        press(driver, 'start')
        driver.run(frames=4)
        popup(driver, 0, 0)
        modal_audit(driver, 0, repo)
        with tempfile.TemporaryDirectory(prefix='dex-shift-frames-') as temporary:
            root = Path(temporary)
            for name, key, kind, cursor in (
                ('sort-open', 'a', 1, 0), ('cursor-one', 'down', 1, 1),
                ('cursor-two', 'down', 1, 2), ('cursor-wrap', 'down', 1, 0),
                ('sort-back', 'b', 0, 0), ('sort-reopen', 'a', 1, 0),
                ('sort-back-again', 'b', 0, 0), ('options-close', 'b', None, None),
            ):
                directory = root / name
                directory.mkdir()
                captures[name], record = transition(driver, key, name, directory)
                records.append(record)
                if kind is not None:
                    popup(driver, kind, cursor)
                    modal_audit(driver, kind, repo)
                elif driver.command('peek')['jumptable'] != 1:
                    record['issues'].append('Cancellation did not return to Listing')
        return captures, records
    finally:
        driver.close()


def case(task):
    baseline, candidate, index, phase, output = task
    output = Path(output)
    style = candidate['listing_style']
    name = f'{style}-{index}-{phase}'
    result = dict(presentation=style, index=index, phase=phase, issues=[])
    try:
        old, old_records = run_arm(baseline, index, phase, output / (name + '-baseline.log'))
        new, new_records = run_arm(candidate, index, phase, output / (name + '-candidate.log'))
        result['baseline'] = old_records
        result['candidate'] = new_records
        result['issues'] += [issue for record in old_records + new_records for issue in record['issues']]
        for route in ('sort-open', 'cursor-one', 'cursor-two', 'cursor-wrap',
                      'sort-back', 'sort-reopen', 'sort-back-again'):
            is_sort = not route.startswith('sort-back')
            rectangle = (64, 48, 152, 104) if is_sort else (72, 56, 144, 96)
            if style == 'legacy':
                rectangle = (rectangle[0], rectangle[1] - 8, rectangle[2], rectangle[3] - 8)
            shifted = (rectangle[0] + 3, rectangle[1], rectangle[2] + 3, rectangle[3]) if style == 'modern' and is_sort else rectangle
            if old[route].crop(rectangle).tobytes() != new[route].crop(shifted).tobytes():
                result['issues'].append(route + ': native pixels do not match exact translation')
                old[route].save(output / (name + '-' + route + '-baseline.png'))
                new[route].save(output / (name + '-' + route + '-candidate.png'))
    except (RuntimeError, ValueError) as error:
        result['issues'].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build directory')
    target = output / 'shift-qualification'
    target.mkdir(exist_ok=True)
    modern = configuration(output)
    indices = [modern['names'].index(name) for name in ('chikorita', 'weavile', 'garchomp', 'kyogre')]
    tasks = [(configuration(args.baseline.resolve(), style), configuration(output, style),
              index, phase, str(target)) for style in ('modern', 'legacy')
             for index in indices for phase in range(8)]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(result['issues']) for result in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'results'}))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
