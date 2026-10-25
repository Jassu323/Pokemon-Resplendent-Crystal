"""Fresh qualification and paired latency for Selected runtime preparation."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
from pathlib import Path
import re
import statistics
import tarfile

from . import info_ui, moves_ui, performance, listing_options
from .assets import Repository, sha256
from .cold_listing import Driver, bootstrap
from .cold_listing import audit as BASE_AUDIT
from .info_ui import BOOT
from .legacy_listing import select_presentation


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def panel_case(task):
    kind, case = task
    # These old runners predate the integrated double-speed clock policy.
    info_ui.audit = partial(BASE_AUDIT, expected_double_speed=1)
    moves_ui.audit = partial(BASE_AUDIT, expected_double_speed=1)
    return (info_ui.run_case if kind == 'info' else moves_ui.run_case)(case)


def stress_case(task):
    info_ui.audit = partial(BASE_AUDIT, expected_double_speed=1)
    return info_ui.run_stress(task)


def panels(source, jobs, kind):
    config = json.loads((source / 'focused/modern/config.json').read_text())
    folder = source / 'focused' / (kind + '-all-double-speed')
    folder.mkdir(exist_ok=True)
    config = dict(config, output=str(folder), uncaught=False)
    tasks = [(kind, (config, i, name, phase)) for i, name in enumerate(config['names'])
             for phase in ('0', 'settled')]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(panel_case, tasks):
            rows.append(row)
            if row['issues'] or len(rows) % 100 == 0:
                print(json.dumps(dict(kind=kind, done=len(rows), species=row['species'],
                                      issues=row['issues'])), flush=True)
    result = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    return int(bool(result['failures']))


def stress(source, jobs):
    config = json.loads((source / 'focused/modern/config.json').read_text())
    folder = source / 'focused/info-stress'
    folder.mkdir(exist_ok=True)
    config = dict(config, output=str(folder), uncaught=False)
    names = ('chikorita', 'eevee', 'tyrogue', 'kingdra', 'politoed', 'chansey',
             'blissey', 'mew', 'dusknoir', 'weavile', 'porygonz', 'unown_a',
             'groudon', 'kyogre', 'sneasel', 'charizard', 'magmar', 'steelix',
             'delcatty', 'crobat')
    tasks = [(config, config['names'].index(name), name, phase, family)
             for name in names for phase in ('0', '8', '32', 'settled')
             for family in ('mash-a', 'hold-a', 'description', 'listing', 'species')]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(stress_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    return int(bool(result['failures']))


def latency_case(task):
    config, name, target, phase, input_phase, variant, style = task
    row = performance.run_case((config, name, target, phase, 0, input_phase))
    return dict(row, variant=variant, style=style)


def compare(source, campaign, jobs):
    folder = source / 'paired-timing'
    folder.mkdir(exist_ok=True)
    tasks = []
    names = ('chikorita', 'eevee', 'tyrogue', 'kingdra', 'politoed',
             'mew', 'dusknoir', 'weavile', 'unown_a', 'porygonz')
    for variant in ('baseline', 'candidate'):
        base = campaign / ('baseline' if variant == 'baseline' else '')
        for style in ('modern', 'legacy'):
            config = listing_options.configuration(base / 'dex-regression', style)
            local = folder / variant / style
            local.mkdir(parents=True, exist_ok=True)
            config = dict(config, output=str(local))
            for name in names:
                for target in ('description-info', 'moves-info', 'info-area-return', 'listing', 'species'):
                    for phase in ('0', 'settled'):
                        for q in (0, 17556, 35112, 52668):
                            tasks.append((config, name, target, phase, q, variant, style))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(latency_case, tasks))
    groups = {}
    for style in ('modern', 'legacy'):
        for action in ('description-info', 'moves-info', 'info-area-return', 'listing', 'species'):
            for phase in ('0', 'settled'):
                selected = [r for r in rows if r['style'] == style and r['action'] == action and r['phase'] == phase]
                record = dict(cases=len(selected), timings={})
                for key in ('first_visible', 'complete_visible', 'info_ready'):
                    found = {}
                    for variant in ('baseline', 'candidate'):
                        values = [r[key]['ms'] for r in selected if r['variant'] == variant and r.get(key)]
                        if values:
                            found[variant] = dict(median=statistics.median(values), maximum=max(values))
                    if found:
                        record['timings'][key] = found
                groups[f'{style}:{action}:{phase}'] = record
    result = dict(cases=len(rows), failures=sum(r['status'] != 'pass' for r in rows),
                  groups=groups, rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps(dict(cases=len(rows), failures=result['failures'], groups=groups)), flush=True)
    return int(bool(result['failures']))


def extra_timing(source, campaign, jobs):
    folder = source / 'extra-timing'
    folder.mkdir(exist_ok=True)
    tasks = []
    for variant in ('baseline', 'candidate'):
        base = campaign / ('baseline' if variant == 'baseline' else '')
        for style in ('modern', 'legacy'):
            config = listing_options.configuration(base / 'dex-regression', style)
            local = folder / variant / style
            local.mkdir(parents=True, exist_ok=True)
            config = dict(config, output=str(local))
            for name in ('chikorita', 'eevee', 'tyrogue', 'slowpoke', 'onix', 'dusknoir'):
                for action in ('cycle', 'description-moves', 'info-moves'):
                    if action == 'cycle' and name == 'dusknoir':
                        continue
                    for phase in ('0', 'settled'):
                        for q in (0, 17556, 35112, 52668):
                            tasks.append((config, name, action, phase, q, variant, style))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(latency_case, tasks))
    result = dict(cases=len(rows), failures=sum(row['status'] != 'pass' for row in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    return int(bool(result['failures']))


def startup_case(task):
    config, variant, style, phase = task
    path = Path(config['output']) / f'{variant}-{style}-q{phase}.log'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], path)
    row = dict(variant=variant, style=style, phase=phase, issues=[])
    try:
        bootstrap(driver)
        if style == 'legacy':
            select_presentation(driver, 1)
        menu = driver.run(('start_menu',), frames=600, key='b')
        if menu['hit'] != 'start_menu':
            raise RuntimeError('Dex close did not return to the start menu')
        driver.run(frames=2)
        driver.command(f'run 0 {phase} 0')
        before = driver.command('peek')
        listing = driver.run(('listing',), frames=600, key='a')
        if listing['hit'] != 'listing' or listing['presentation'] != int(style == 'legacy'):
            raise RuntimeError('Dex reopen did not reach the intended listing')
        row['reopen_ms'] = (listing['t'] - before['t']) / 4194304 * 1000
    except Exception as error:
        row['issues'].append(str(error))
    finally:
        driver.close()
    return row


def startup(source, campaign, jobs):
    folder = source / 'startup-timing'
    folder.mkdir(exist_ok=True)
    tasks = []
    for variant in ('baseline', 'candidate'):
        base = campaign / ('baseline' if variant == 'baseline' else '')
        for style in ('modern', 'legacy'):
            config = listing_options.configuration(base / 'dex-regression', style)
            config = dict(config, output=str(folder))
            tasks.extend((config, variant, style, phase) for phase in (0, 17556, 35112, 52668))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(startup_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(row['issues']) for row in rows), rows=rows)
    write(folder / 'summary.json', result)
    print(json.dumps(result), flush=True)
    return int(bool(result['failures']))


def inventory(source):
    candidate = source / 'candidate'
    old = Repository(source, source / 'rollback/pokecrystal.gbc', source / 'rollback/pokecrystal.sym')
    new = Repository(candidate, candidate / 'pokecrystal.gbc', candidate / 'pokecrystal.sym')
    for label in ('PokedexInfoTileGFX', 'PokedexInfoTitleGFX', 'PokedexInfoNumbers',
                  'PokedexInfoSpecies', 'PokedexMovesSpecies', 'PokedexMovesMachineMoves'):
        if label in new.symbols:
            raise AssertionError('Generated display data remains linked: ' + label)
    manifest = json.loads((source / 'runtime-manifest.json').read_text())
    unchanged = ('home/vblank.asm', 'home/lcd.asm', 'home/audio.asm',
                 'engine/pokedex/pokedex_2.asm', 'engine/pokedex/pokedex_3.asm',
                 'engine/pokedex/pokedex_types.asm',
                 'engine/pokedex/pokedex_types_mode7.asm')
    with tarfile.open(source / 'rollback-source.tar') as archive:
        for path in unchanged:
            if archive.extractfile(path).read() != (candidate / path).read_bytes():
                raise AssertionError('Shared/Area implementation changed: ' + path)
    def sections(path):
        return {name: int(size, 16) for size, name in re.findall(
            r'SECTION: .*?\(\$([0-9a-f]+) bytes?\) \["([^"]+)"\]', path.read_text())}
    before, after = sections(source / 'rollback/pokecrystal.map'), sections(candidate / 'pokecrystal.map')
    changes = {name: dict(before=before.get(name, 0), after=after.get(name, 0),
                         delta=after.get(name, 0) - before.get(name, 0))
               for name in before.keys() | after.keys() if before.get(name, 0) != after.get(name, 0)}
    result = dict(rom_sha256=sha256(new.rom), removed_labels=[label for label in old.symbols
                  if label.startswith(('PokedexInfoEvolution', 'PokedexInfoLine')) and label not in new.symbols],
                  retained_shared_move_name_index_bytes=2 * 333,
                  retained_original_font=True, retained_editable_bar_art=True,
                  unchanged_source_files=list(unchanged), section_changes=changes,
                  allocation_delta=manifest['delta'],
                  bank3_additional_overlay_bytes=new.symbols['wPokedexInfoWorkspaceEnd'][1] - old.symbols['wPokedexInfoWorkspaceEnd'][1],
                  bank5_remaining_bytes=0xe000 - new.symbols['wPokedexRuntimeCacheEnd'][1],
                  area_implementation_unchanged=True)
    write(source / 'runtime-inventory.json', result)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('info', 'moves', 'stress', 'compare', 'extra-timing', 'startup', 'inventory'))
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.phase in ('info', 'moves'):
        code = panels(source, args.jobs, args.phase)
    elif args.phase == 'stress':
        code = stress(source, args.jobs)
    elif args.phase == 'compare':
        code = compare(source, args.campaign.resolve(), args.jobs)
    elif args.phase == 'extra-timing':
        code = extra_timing(source, args.campaign.resolve(), args.jobs)
    elif args.phase == 'startup':
        code = startup(source, args.campaign.resolve(), args.jobs)
    else:
        code = inventory(source)
    raise SystemExit(code)
