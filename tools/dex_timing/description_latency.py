"""Private attribution and small local experiments for Info-to-Description delay."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from .assets import Repository, sha256, read_symbols, offset
from .cold_listing import ROOT, Driver, bootstrap, move, predecessor
from .backlog_reconciliation import tab_case
from .listing_options import configuration
from . import performance
from .cry_ownership import validate_output
from tools.build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-description-latency-20261014'
CURRENT = ROOT / 'build/dex-cleanup-20261014/runtime'
RUN_TAG = ''
HISTORY = {
    'pre-cleanup': ROOT / 'build/dex-cleanup-20261014/runtime-regression/baseline/dex-regression',
    'pre-stage': ROOT / 'build/dex-selected-ancestors-integration-20261013/precomputed/focused',
    'pre-ancestors': ROOT / 'build/dex-selected-ancestors-integration-20261013/precomputed-regression/baseline/dex-regression',
    'current': CURRENT / 'focused',
}
POINTS = {
    'text_service': ('PokedexSelectedMon_ServiceDescriptionText', True),
    'text_slice': ('PokedexSelectedMon_ServiceDescriptionText.slice', False),
    'text_admitted': ('PokedexSelectedMon_ServiceDescriptionText.admitted', False),
    'text_done': ('PokedexSelectedMon_ServiceDescriptionText.done', False),
    'text_initialize': ('PokedexSelectedMon_InitializeDescriptionText', True),
    'text_badge': ('PokedexSelectedMon_PrepareDescriptionBadge', True),
    'text_chunk': ('PokedexSelectedMon_RenderDescriptionTextChunk', True),
    'text_ready': ('PokedexSelectedMon_RenderDescriptionTextChunk.ready', False),
    'text_publish': ('Pokedex_VBlankDescriptionText', True),
    'text_committed': ('Pokedex_VBlankDescriptionText.committed', False),
    'portrait_entry': ('Pokedex_VBlankAnimationFrontpicMap', False),
    'portrait_defer': ('Pokedex_VBlankAnimationFrontpicMap.defer', False),
    'portrait_displayed': ('Pokedex_VBlankAnimationFrontpicMap.display_recorded', False),
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def protected():
    return {str(path): sha256(path.read_bytes()) for path in (
        ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map')}


def cases(config, variant, all_species=False):
    pairs = (('dusclops', 'dusknoir'), ('abomasnow', 'weavile'),
             ('grovyle', 'sceptile'), ('bayleef', 'meganium'))
    if all_species:
        pairs = tuple((config['names'][(i - 1) % len(config['names'])], name)
                      for i, name in enumerate(config['names']))
    ages = ('0', '8') if all_species else ('0', '8', '32', 'settled')
    phases = (0,) if all_species else (0, 17556, 35112, 52668)
    return [(config, source, target, age, phase, variant)
            for source, target in pairs for age in ages for phase in phases]


def run_case(task):
    row = tab_case(task[:5])
    return dict(row, variant=task[5])


def run(folder, tasks, jobs):
    before = protected()
    private_inputs = {config[field] for config, *_ in tasks for field in ('rom', 'sym', 'battery')}
    private_before = {path: sha256(Path(path).read_bytes()) for path in private_inputs}
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(run_case, tasks):
            rows.append(row)
            if row['issues'] or len(rows) % 50 == 0:
                print(json.dumps(dict(done=len(rows), variant=row['variant'], issues=row['issues'])), flush=True)
    result = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows),
                  protected_inputs_unchanged=before == protected(),
                  private_inputs_unchanged=private_before == {
                      path: sha256(Path(path).read_bytes()) for path in private_inputs},
                  protected_hashes_before=before, protected_hashes_after=protected(), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2), flush=True)
    return int(result['failures'] > 0 or not result['protected_inputs_unchanged']
               or not result['private_inputs_unchanged'])


def history(jobs):
    folder = BASE / 'history'
    if folder.exists():
        raise ValueError('Preserve the prior history run')
    folder.mkdir(parents=True)
    tasks, provenance = [], {}
    for variant, source in HISTORY.items():
        for style in ('modern', 'legacy'):
            config = configuration(source, style)
            repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
            if repo.hashes != config['hashes']:
                raise ValueError('Historical checkpoint provenance mismatch')
            target = folder / variant / style
            target.mkdir(parents=True)
            config['output'] = str(target)
            provenance[variant] = repo.hashes
            tasks.extend(cases(config, variant))
    write(folder / 'provenance.json', provenance)
    return run(folder, tasks, jobs)


def prepare(variant, jobs):
    folder = BASE / variant
    if folder.exists():
        raise ValueError('Use a new private variant name')
    before = protected()
    candidate = folder / 'candidate'
    shutil.copytree(CURRENT / 'candidate', candidate,
        ignore=shutil.ignore_patterns('*.o', '*.d', '__pycache__', '*.pyc'))
    # Source changes are applied separately with apply_patch before finish.
    write(folder / 'manifest.json', dict(variant=variant, protected=before,
          original=resources(ROOT / 'pokecrystal.map'), state='prepared'))
    print(json.dumps(dict(prepared=str(candidate))), flush=True)
    return 0


def finish(variant, jobs):
    folder = BASE / variant
    candidate = folder / 'candidate'
    manifest = json.loads((folder / 'manifest.json').read_text())
    game_before = {path: digest for path, digest in manifest['protected'].items()
                   if Path(path).suffix != '.sav'}
    if game_before != protected():
        raise ValueError('Production changed during private preparation')
    with (folder / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', '-W', 'main.asm', 'pokecrystal.gbc'],
                       cwd=candidate, stdout=log, stderr=subprocess.STDOUT, check=True)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(candidate / f'pokecrystal.{ext}', folder / f'pokecrystal-dex-selected-runtime.{ext}')
    shutil.copy2(CURRENT / 'pokecrystal-dex-selected-runtime.sav',
                 folder / 'pokecrystal-dex-selected-runtime.sav')
    from .selected_architecture import prepare as fixtures
    fixtures(folder)
    new = resources(candidate / 'pokecrystal.map')
    manifest.update(state='built', delta={k: new[k] - old for k, old in manifest['original'].items()},
                    rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
                    protected_inputs_unchanged=game_before == protected())
    write(folder / 'manifest.json', manifest)
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


def test(variant, jobs, all_species=False):
    source = CURRENT if variant == 'current' else BASE / variant
    name = 'all-species' if all_species else 'timing'
    folder = BASE / variant / (name + ('-' + RUN_TAG if RUN_TAG else ''))
    if folder.exists():
        raise ValueError('Preserve prior tests')
    tasks = []
    for style in ('modern', 'legacy'):
        config = configuration(source / 'focused', style)
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        if repo.hashes != config['hashes']:
            raise ValueError('Private checkpoint mismatch')
        target = folder / style
        target.mkdir(parents=True)
        config['output'] = str(target)
        config['exact_playback'] = True
        tasks.extend(cases(config, variant, all_species))
    return run(folder, tasks, jobs)


def trace(variant, jobs):
    source = CURRENT if variant == 'current' else BASE / variant
    folder = BASE / variant / ('trace' + ('-' + RUN_TAG if RUN_TAG else ''))
    if folder.exists():
        raise ValueError('Preserve prior trace')
    folder.mkdir(parents=True)
    tasks = []
    for style in ('modern',):
        config = configuration(source / 'focused', style)
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        target = folder / style
        target.mkdir()
        header = target / 'description-symbols.h'
        header.write_text('\n'.join(
            f'#define D_{name}_bank {repo.symbols[name][0]}\n#define D_{name} {repo.symbols[name][1]}'
            for name in ('wPokedexDescriptionTextState', 'wPokedexOwnerTransition',
                         'wPokedexAnimPlaybackState', 'wPokedexAnimFlags', 'wPokedexAnimDeadline',
                         'wPokedexDescriptionTextSource', 'wPokedexDescriptionTextRow',
                         'wPokedexAnimSchedulerControl', 'wPokedexInfoRestoreDescription')) + '\n')
        config['core'] = str(performance.core(repo, target, POINTS,
            ('-DDEX_DESCRIPTION_LATENCY_TRACE', f'-DDEX_DESCRIPTION_LATENCY_SYMBOLS="{header.resolve()}"')))
        config['output'] = str(target)
        tasks.extend((config, src, dst, age, 0, variant)
                     for src, dst in (('grovyle', 'sceptile'), ('bayleef', 'meganium'),
                                      ('dusclops', 'dusknoir')) for age in ('8', 'settled'))
    return run(folder, tasks, jobs)


def visibility(variant, jobs):
    from .info_ui import fixture, BOOT
    from .legacy_listing import select_presentation
    source = BASE / variant
    folder = source / ('visibility' + ('-' + RUN_TAG if RUN_TAG else ''))
    if folder.exists():
        raise ValueError('Preserve prior visibility tests')
    tasks = []
    for style in ('modern', 'legacy'):
        config = configuration(source / 'focused', style)
        target = folder / style
        target.mkdir(parents=True)
        battery = target / 'uncaught.sav'
        fixture(Path(config['battery']), battery, caught=False)
        states = target / 'listing-states'
        states.mkdir()
        config.update(output=str(target), battery=str(battery), states=str(states),
                      uncaught=True, exact_playback=True)
        batch = cases(config, variant)
        needed = sorted({(config['names'].index(src) - 1) % len(config['names']) if style == 'legacy'
                         else predecessor(config['names'].index(src))[0] for _, src, *_ in batch})
        driver = Driver(config['core'], config['rom'], BOOT, battery, target / 'bootstrap.log')
        try:
            bootstrap(driver)
            if driver.command('peek')['presentation'] != int(style == 'legacy'):
                select_presentation(driver, int(style == 'legacy'))
            for index in needed:
                state = driver.command('peek')
                if style == 'modern':
                    while state['index'] % 3 != index % 3:
                        state = move(driver, 'right' if state['index'] % 3 < index % 3 else 'left')
                for _ in range(len(config['names'])):
                    if state['index'] == index:
                        break
                    state = move(driver, 'down' if state['index'] < index else 'up')
                else:
                    raise RuntimeError('Normal navigation did not reach fixture index')
                driver.run(('end_loop',))
                driver.command(f'save {states / f"listing-{index:03}.s0"}')
        finally:
            driver.close()
        tasks.extend(batch)
    return run(folder, tasks, jobs)


def moves(variant, jobs):
    source = BASE / variant
    folder = source / 'moves-returns'
    if folder.exists():
        raise ValueError('Preserve prior Moves-return tests')
    tasks = []
    for style in ('modern', 'legacy'):
        config = configuration(source / 'focused', style)
        target = folder / style
        target.mkdir(parents=True)
        config.update(output=str(target), source_view=2, exact_playback=True)
        tasks.extend(cases(config, variant))
    return run(folder, tasks, jobs)


def report(variant, jobs):
    import statistics
    key = lambda r: tuple(r[name] for name in ('source', 'target', 'style', 'age', 'phase'))
    history = json.loads((BASE / 'history-retry/history/summary.json').read_text())
    baseline = json.loads((BASE / 'current/all-species-audio/summary.json').read_text())
    reference = {key(row): row for row in baseline['rows']}
    summaries = {}
    for name in ('current', 'pending-aware', 'deadline-aware', 'combined'):
        folder = BASE / name / ('all-species' if name == 'combined' else 'all-species-audio')
        data = json.loads((folder / 'summary.json').read_text())
        values = [row['complete_visible']['ms'] for row in data['rows'] if not row['issues']]
        differences, audio = [], []
        if {key(row) for row in data['rows']} != set(reference):
            raise ValueError('Paired catalog is incomplete')
        for row in data['rows']:
            other = reference[key(row)]
            if row['issues'] or other['issues']:
                continue
            differences.append(row['complete_visible']['ms'] - other['complete_visible']['ms'])
            if row.get('audio_stops'):
                def elapsed(value):
                    first = value['incoming_accepted']['t'] + value['playback_audit']['first_publication_frames'] * 70224
                    return value['audio_stops'][-1]['t'] - first
                delta = (elapsed(row) - elapsed(other)) * 1000 / 4194304
                audio.append(dict(case=key(row), delta_ms=delta, delta_frames=delta / (70224 * 1000 / 4194304)))
        manifest = None if name == 'current' else json.loads((BASE / name / 'manifest.json').read_text())
        moved = []
        interrupts = {}
        if manifest:
            old = read_symbols(ROOT / 'pokecrystal.sym')
            new = read_symbols(BASE / name / 'candidate/pokecrystal.sym')
            moved = [label for label, pair in old.items() if pair[1] >= 0xa000 and label in new and new[label] != pair]
            current = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
            candidate = Repository(ROOT, BASE / name / 'candidate/pokecrystal.gbc',
                                   BASE / name / 'candidate/pokecrystal.sym')
            for start, end in (('LCD', 'DisableLCD'), ('VBlank_Normal', 'VBlank_SoundOnly'),
                               ('VBlank_Cutscene', 'UpdatePals'), ('VBlank_CutsceneCGB', 'VBlank_Serial')):
                a = current.rom[offset(current.symbols[start]):offset(current.symbols[end])]
                b = candidate.rom[offset(candidate.symbols[start]):offset(candidate.symbols[end])]
                interrupts[start] = a == b
        summaries[name] = dict(cases=data['cases'], failures=data['failures'],
            protected_inputs_unchanged=data['protected_inputs_unchanged'], private_inputs_unchanged=data['private_inputs_unchanged'],
            median_ms=statistics.median(values), minimum_ms=min(values), maximum_ms=max(values),
            median_frames=statistics.median(values) / (70224 * 1000 / 4194304),
            maximum_frames=max(values) / (70224 * 1000 / 4194304),
            paired_median_delta_ms=statistics.median(differences),
            paired_median_delta_frames=statistics.median(differences) / (70224 * 1000 / 4194304),
            paired_delta_range_ms=[min(differences), max(differences)],
            slower_over_one_frame=sum(delta > 70224 * 1000 / 4194304 for delta in differences),
            delta=None if not manifest else manifest['delta'], moved_ram_labels=moved,
            ordinary_interrupt_code_identical=interrupts,
            cry_cases=len(audio), cry_delta_range_ms=[min((r['delta_ms'] for r in audio), default=0),
                                                    max((r['delta_ms'] for r in audio), default=0)],
            audio=audio)
    current_history = {key(row): row for row in history['rows'] if row['variant'] == 'current'}
    paired_history = {}
    for name in HISTORY:
        deltas = [row['complete_visible']['ms'] - current_history[key(row)]['complete_visible']['ms']
                  for row in history['rows'] if row['variant'] == name]
        paired_history[name] = dict(cases=len(deltas), minimum_ms=min(deltas), maximum_ms=max(deltas),
                                   median_ms=statistics.median(deltas))
    result = dict(history=paired_history, variants=summaries)
    write(BASE / 'comparison.json', result)
    print(json.dumps(dict(history=paired_history,
        variants={name: {k: v for k, v in value.items() if k != 'audio'} for name, value in summaries.items()}), indent=2))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('history', 'prepare', 'finish', 'test', 'all-species', 'trace', 'report', 'visibility', 'moves'))
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--variant', default='current')
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--tag', default='')
    args = parser.parse_args()
    BASE = validate_output(args.base, [CURRENT])
    RUN_TAG = args.tag
    if args.jobs < 1 or not args.variant.replace('-', '').isalnum() or (
            args.tag and not args.tag.replace('-', '').isalnum()):
        parser.error('Use a positive worker count and a simple variant name')
    if args.action == 'history':
        code = history(args.jobs)
    elif args.action == 'all-species':
        code = test(args.variant, args.jobs, True)
    else:
        code = globals()[args.action](args.variant, args.jobs)
    raise SystemExit(code)
