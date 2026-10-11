"""Run existing Pokemon Dex suites against the current Moves Search link."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil

from . import performance, listing_options, legacy_listing
from .assets import Repository, sha256


def prepare(output):
    target = output / 'dex-regression'
    target.mkdir(exist_ok=True)
    stem = output / 'pokecrystal-dex-moves-search'
    config = performance.prepare(stem.with_suffix('.gbc'), stem.with_suffix('.sym'),
                                 output / 'all-seen-tests.sav', target / 'modern')
    repo = Repository(output / 'candidate', Path(config['rom']), Path(config['sym']))
    config['core'] = str(performance.core(repo, target / 'popover-core', listing_options.POINTS).resolve())
    (target / 'modern/config.json').write_text(json.dumps(config, indent=2) + '\n')
    legacy_listing.prepare_legacy(target / 'legacy', config)
    shutil.copy2(output / 'sort-manifest.json', target / 'sort-manifest.json')
    return dict(rom_sha256=sha256(repo.rom), species=len(config['names']),
                checkpoints='fresh normal-input states for this link', issues=[])


def selected(output, jobs):
    target = output / 'dex-regression/selected'
    target.mkdir(exist_ok=True)
    tasks = []
    for style in ('modern', 'legacy'):
        config = listing_options.configuration(output / 'dex-regression', style)
        local = target / style
        local.mkdir(exist_ok=True)
        config['output'] = str(local)
        for name in config['names']:
            tasks.append((config, name, 'cycle', 'settled', 0, 0))
        for name in ('chikorita', 'weavile', 'dusknoir', 'eevee', 'unown_a', 'porygonz'):
            for action in ('description-info', 'moves-info', 'description-area',
                           'moves-area', 'info-area', 'info-area-return', 'listing',
                           'rapid', 'species'):
                tasks.extend((config, name, action, phase, 0, q)
                             for phase in ('0', 'settled') for q in (0, 3))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(performance.run_case, tasks))
    result = dict(cases=len(rows), failures=sum(r['status'] != 'pass' for r in rows),
                  workers=jobs, results=rows)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return {k: v for k, v in result.items() if k != 'results'}


def qualify(output):
    target = output / 'dex-regression'
    digest = sha256((output / 'pokecrystal-dex-moves-search.gbc').read_bytes())
    for style in ('modern', 'legacy'):
        config = listing_options.configuration(target, style)
        if config['hashes']['rom_sha256'] != digest:
            raise AssertionError('Pokemon Dex checkpoints belong to a different ROM')
    suites = {}
    for name in ('popover-qualification', 'integration', 'modal-qualification',
                 'visual-qualification', 'edges', 'edges-legacy', 'navigation',
                 'selected', 'search-qualification', 'search-listing-returns',
                 'search-default-empty', 'mode-transitions'):
        data = json.loads((target / name / 'summary.json').read_text())
        if isinstance(data, list):
            summary = dict(cases=len(data), failures=sum(bool(r['issues']) for r in data))
        else:
            summary = {k: v for k, v in data.items() if k in ('cases', 'failures', 'transitions')}
        suites[name] = summary
    result = dict(rom_sha256=digest, workers=6, suites=suites,
                  cases=sum(r['cases'] for r in suites.values()),
                  failures=sum(r['failures'] for r in suites.values()))
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if result['failures']:
        raise AssertionError('Pokemon Dex regression has unresolved failures')
    return result


def run(output, action, jobs):
    target = output / 'dex-regression'
    if action == 'prepare':
        return prepare(output)
    if action == 'listings':
        return dict(failures=listing_options.qualify(target, jobs), workers=jobs)
    if action == 'interfaces':
        failures = listing_options.integration(target, jobs)
        failures += listing_options.modal_tests(target, jobs)
        failures += listing_options.visuals(target, jobs)
        failures += sum(listing_options.edges(target, presentation) for presentation in (0, 1))
        failures += legacy_listing.navigation_tests(target, jobs)
        return dict(failures=failures, workers=jobs)
    if action == 'selected':
        return selected(output, jobs)
    if action == 'qualify':
        return qualify(output)
    raise ValueError(action)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'listings', 'interfaces', 'selected', 'qualify'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    result = run(args.output.resolve(), args.action, min(args.jobs, 6))
    print(json.dumps(result), flush=True)
    raise SystemExit(int(bool(result.get('failures') or result.get('issues'))))
