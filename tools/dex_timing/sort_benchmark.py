"""A/B compact versus record orders using ordinary inputs and copied saves."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import random
import statistics
import tempfile

from . import performance
from .assets import Repository
from .cold_listing import ROOT, Driver, bootstrap, move
from .info_ui import BOOT, press
from .legacy_listing import private_battery
from .listing_options import LABELS, POINTS, grid_audit, memory, order_audit, popup, title_audit
from pokedex_info_assets import species

COUNTS = (5, 50, 100, 150, 200, 250, 300, 350, 373)


def setup(build, output, battery):
    repo = Repository(ROOT, build / 'pokecrystal-dex-options.gbc',
                      build / 'pokecrystal-dex-options.sym')
    compiled = performance.core(repo, output / 'core', POINTS)
    return dict(core=str(compiled), rom=str(repo.rom_path), sym=str(build / 'pokecrystal-dex-options.sym'),
                battery=str(battery), output=str(output),
                manifest=json.loads((build / 'sort-manifest.json').read_text()))


def distribution(count, kind):
    if kind == 'early':
        return tuple(range(count))
    sequence = list(range(373))
    random.Random(20261006).shuffle(sequence)
    return tuple(sorted(sequence[:count]))


def scenario(task):
    from PIL import Image
    config, count, kind, initial, target, phase = task
    label = f'{count:03}-{kind}-{initial}-{target}-q{phase}'
    output = Path(config['output'])
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    constants = species()
    seen = distribution(count, kind)
    unseen = tuple(i for i in range(373) if i not in seen)
    family = config['manifest']['orders'][LABELS[0]]
    excluded = {constants.index(family[i]) + 1 for i in unseen}
    battery = output / (label + '.sav')
    private_battery(config, battery, presentation=0, unseen=unseen, order_mode=initial)
    driver = Driver(config['core'], config['rom'], BOOT, battery, output / (label + '.log'))
    result = dict(count=count, distribution=kind, initial=initial, target=target,
                  phase=phase, issues=[])
    try:
        driver.command('rawcolor')
        driver.command('audit 1')
        driver.command('perf 1')
        bootstrap(driver, expected_mode=initial)
        costs = [e['elapsed'] for e in driver.events
                 if e['event'] == 'perf_cost' and e['name'] == 'order']
        if len(costs) != 1:
            raise RuntimeError(f'Expected one boot order span, got {costs}')
        result['boot_cycles'] = costs[0]
        grid_audit(driver, repo, order_audit(
            driver, repo, config['manifest']['orders'][LABELS[initial]], excluded), excluded)
        driver.command('perf 0')
        # Start away from entry zero, including a scrolled viewport on long lists.
        for _ in range(4):
            move(driver, 'down')
            driver.run(('end_loop',))
            driver.run(('end_loop',))
        result['original_index'] = driver.command('peek')['index']
        press(driver, 'start')
        popup(driver, 0, 0)
        press(driver, 'a')
        popup(driver, 1, initial)
        for _ in range(abs(target - initial)):
            press(driver, 'down' if target > initial else 'up')
        driver.run(frames=2 + phase / 8)
        with tempfile.TemporaryDirectory(prefix='dex-sort-benchmark-') as directory:
            temporary = Path(directory)
            driver.command(f'image {temporary}/old.ppm')
            original = Image.open(temporary / 'old.ppm').convert('RGB').tobytes()
            driver.events.clear()
            asserted = driver.command('perf 1')
            driver.command(f'perfimages {temporary}/display')
            driver.run(('animation_miss', 'audio_miss'), frames=2, key='a')
            driver.run(('animation_miss', 'audio_miss'), frames=64)
            driver.command('perfimages -')
            driver.command('perf 0')
            state = driver.command('peek')
            if state['jumptable'] != 1 or state['mode'] != target:
                raise RuntimeError(f'Sort did not finish in Listing: {state}')
            if state['index'] or state['cursor'] or state['scroll']:
                raise RuntimeError(f'Changed sort retained a cursor/viewport: {state}')
            order = order_audit(driver, repo, config['manifest']['orders'][LABELS[target]], excluded)
            grid_audit(driver, repo, order, excluded)
            # Unseen first entries intentionally display their unknown marker.
            if order[0] not in excluded:
                title_audit(driver, repo, order[0])
            result['first_species'] = constants[order[0] - 1]
            flags = memory(driver, 0, repo.symbols['wPokedexWRAM0Scratch'][1] + 0x4d0, 47)
            result['first_seen'] = bool(flags[0] & 1)
            frames = [e for e in driver.events if e['event'] == 'perf_frame']
            paths = sorted(temporary.glob('display-*.ppm'))
            images = [Image.open(path).convert('RGB').tobytes() for path in paths]
            if len(images) != len(frames):
                raise RuntimeError('Display captures and timestamps disagree')
            references = set(images[-32:])
            first = next(i for i, pixels in enumerate(images) if pixels != original)
            complete = next(i for i, pixels in enumerate(images) if pixels in references)
            for key, index in (('first', first), ('complete', complete)):
                cycles = frames[index]['boundary_t'] - asserted['t']
                result[key + '_cycles'] = cycles
                result[key + '_ms'] = cycles * 1000 / performance.HZ
                result[key + '_frames'] = cycles / performance.T
            # Accept old popup, a deliberate fully black owner mask, and the
            # final grid's normal animation phases. Never a partially built page.
            kinds = []
            for index, pixels in enumerate(images):
                kind_at = ('old' if pixels == original else 'new' if pixels in references
                           else 'mask' if not any(pixels) else 'mixed')
                kinds.append(kind_at)
                if kind_at == 'mixed':
                    result['issues'].append('partial_display')
                    Image.open(paths[index]).save(output / f'{label}-mixed-{index}.png')
            result['display_states'] = kinds
            if 'new' not in kinds or any(k != 'new' for k in kinds[kinds.index('new'):]):
                result['issues'].append('non_atomic_reveal')
            costs = [e['elapsed'] for e in driver.events
                     if e['event'] == 'perf_cost' and e['name'] == 'order']
            if len(costs) != 1:
                raise RuntimeError(f'Expected one changed-sort order span: {costs}')
            result['sort_cycles'] = costs[0]
            result['events'] = [e for e in driver.events if e['event'] != 'perf_frame']
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            result['issues'].append('playback_miss')
    except (RuntimeError, ValueError, StopIteration) as error:
        result['issues'].append(str(error) or type(error).__name__)
        driver.evidence(output / (label + '-error'))
    finally:
        driver.close()
    return result


def summarize(results):
    aggregates, boot = [], []
    counts = sorted({r['count'] for r in results})
    for variant in ('records', 'compact'):
        for count in counts:
            for mode in range(3):
                rows = [r for r in results if r['variant'] == variant and r['count'] == count
                        and r['target'] == mode and not r['issues']]
                aggregate = dict(variant=variant, count=count, target=mode, cases=len(rows))
                for key in ('sort_cycles', 'first_ms', 'first_frames', 'complete_ms', 'complete_frames'):
                    values = [r[key] for r in rows]
                    if values:
                        aggregate[key] = dict(min=min(values), median=statistics.median(values), max=max(values))
                aggregates.append(aggregate)
                values = [r['boot_cycles'] for r in results if r['variant'] == variant
                          and r['count'] == count and r['initial'] == mode and not r['issues']]
                if values:
                    boot.append(dict(variant=variant, count=count, mode=mode,
                                     min=min(values), median=statistics.median(values), max=max(values)))
    key = lambda r: (r['count'], r['distribution'], r['initial'], r['target'], r['phase'])
    arms = {variant: {key(r): r for r in results if r['variant'] == variant and not r['issues']}
            for variant in ('records', 'compact')}
    comparisons = []
    for count in counts:
        keys = [k for k in arms['records'].keys() & arms['compact'].keys() if k[0] == count]
        row = dict(count=count, pairs=len(keys))
        for metric in ('first_frames', 'complete_frames'):
            values = [arms['compact'][k][metric] - arms['records'][k][metric] for k in keys]
            if values:
                row[metric] = dict(min=min(values), median=statistics.median(values), max=max(values),
                                   extra_interval_cases=sum(value > 0.5 for value in values))
        comparisons.append(row)
    return dict(cases=len(results), failures=sum(bool(r['issues']) for r in results),
                aggregates=aggregates, boot_aggregates=boot, comparisons=comparisons, results=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--compact', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=12)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    output.mkdir(parents=True, exist_ok=True)
    configs = []
    for name in ('records', 'compact'):
        if getattr(args, name) is None:
            continue
        target = output / name
        target.mkdir(exist_ok=True)
        config = setup(getattr(args, name).resolve(), target, args.battery.resolve())
        configs.append((name, config))
    tasks = [(config, count, kind, initial, target, phase)
             for _, config in configs for count in ((5, 373) if args.quick else COUNTS)
             for kind in ('early', 'scattered') for initial in range(3)
             for target in range(3) if target != initial
             for phase in ((0,) if args.quick else range(8))]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result, task in zip(pool.map(scenario, tasks), tasks):
            result['variant'] = 'records' if task[0]['manifest']['records'] else 'compact'
            results.append(result)
            if len(results) % 50 == 0 or result['issues']:
                print(json.dumps(dict(done=len(results), total=len(tasks), result={
                    k: v for k, v in result.items() if k not in ('events', 'display_states')})), flush=True)
    summary = summarize(results)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(dict(cases=summary['cases'], failures=summary['failures'])))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
