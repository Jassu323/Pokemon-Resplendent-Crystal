"""Freeze and qualify the source-linked Stage lifecycle production integration."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tarfile

from .assets import Repository, read_symbols, sha256
from .cold_listing import ROOT

BASE = ROOT / 'build/dex-stage-production-integration-20261013'
SOURCE = BASE / 'precomputed'
CAMPAIGN = BASE / 'precomputed-regression'
FILES = ('engine/pokedex/pokedex.asm', 'engine/pokedex/pokedex_legacy.asm',
         'engine/pokedex/pokedex_description.asm', 'engine/menus/start_menu.asm')


def freeze():
    from tools.build_selected_runtime_prototype import prepare
    prepare(SOURCE)
    # Baseline host tests need their own matching converted and generated assets.
    with tarfile.open(SOURCE / 'rollback-source.tar', 'a') as archive:
        archive.add(ROOT / 'gfx', arcname='gfx')
        for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                     'dex-moves-mode-assets', 'dex-sort-assets'):
            archive.add(ROOT / 'build' / name, arcname='build/' + name)


def prepare():
    from tools.build_dex_unown_prototype import resources
    from .type_full_regression import prepare as campaign_prepare
    for name in FILES:
        shutil.copy2(ROOT / name, SOURCE / 'candidate' / name)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{ext}', SOURCE / f'candidate/pokecrystal.{ext}')
    donor = ROOT / 'build/dex-entry-exit-review-20261013/baseline/private.sav'
    for stem in ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime',
                 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map'):
            shutil.copy2(ROOT / f'pokecrystal.{ext}', SOURCE / f'{stem}.{ext}')
        shutil.copy2(donor, SOURCE / f'{stem}.sav')
    old = resources(SOURCE / 'rollback/pokecrystal.map')
    new = resources(ROOT / 'pokecrystal.map')
    old_symbols = read_symbols(SOURCE / 'rollback/pokecrystal.sym')
    symbols = read_symbols(ROOT / 'pokecrystal.sym')
    old_rom = (SOURCE / 'rollback/pokecrystal.gbc').read_bytes()
    rom = (ROOT / 'pokecrystal.gbc').read_bytes()
    result = dict(rom_sha256=sha256(rom), baseline_sha256=sha256(old_rom),
                  delta={k: new[k] - old[k] for k in old},
                  fixed_bank_code_identical=(old_rom[:0x14e] == rom[:0x14e] and
                                             old_rom[0x150:0x4000] == rom[0x150:0x4000]),
                  changed_ram_labels=[name for name, pair in old_symbols.items()
                                      if pair[1] >= 0xa000 and name in symbols
                                      and pair != symbols[name]])
    (BASE / 'integration.json').write_text(json.dumps(result, indent=2) + '\n')
    campaign_prepare(SOURCE, CAMPAIGN, SOURCE / 'rollback')
    print(json.dumps(result, indent=2), flush=True)


def run_command(module, *arguments):
    folder = BASE / 'extra-logs'
    folder.mkdir(exist_ok=True)
    name = '-'.join((module, *(str(a) for a in arguments[:1])))
    path = folder / (name + '.log')
    attempt = 1
    while path.exists():
        attempt += 1
        path = folder / (name + f'-attempt-{attempt}.log')
    with path.open('w') as log:
        subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + module,
                        *(str(a) for a in arguments)], cwd=ROOT, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    print(json.dumps(dict(completed=module, action=str(arguments[0]))), flush=True)


def animations():
    configurations = []
    for variant, folder, stem in (
            ('production', CAMPAIGN / 'baseline', 'pokecrystal-dex-moves-mode'),
            ('integrated', SOURCE, 'pokecrystal-dex-types')):
        configurations.append(dict(variant=variant, root=str(folder / 'candidate'),
            rom=str(folder / (stem + '.gbc')), sym=str(folder / (stem + '.sym')),
            battery=str(CAMPAIGN / 'legacy-input.sav'), expected_double_speed=0,
            expected_battle_speed=0, fresh_battle_fixture=True))
    path = BASE / 'animation-configurations.json'
    path.write_text(json.dumps(configurations, indent=2) + '\n')
    for action in ('prepare', 'renderer', 'native', 'report'):
        run_command('all_battle_animations', action, '--configurations', path,
                    '--output', BASE / 'all-animations', '--jobs', 6)


def displays():
    run_command('type_matchups', '--output', SOURCE, '--all-models')
    for action in ('audio', 'audio_navigation'):
        run_command('type_mode7_comparison', action, '--base', BASE, '--variant', 'precomputed')
    for model in ('0', 'A', 'B', 'C', 'D', 'E'):
        run_command('unown_performance', '--source', SOURCE / 'candidate', '--rom',
                    SOURCE / 'pokecrystal-dex-unown-fast.gbc', '--sym',
                    SOURCE / 'pokecrystal-dex-unown-fast.sym', '--battery',
                    SOURCE / 'pokecrystal-dex-unown-fast.sav', '--model', model,
                    '--output', SOURCE / ('unown-model-' + model))
    run_command('unown_decoder', '--source', SOURCE, '--output', SOURCE / 'unown-decoder')


def selected():
    for phase in ('prepare', 'info', 'moves', 'stress', 'feature', 'returns', 'modes'):
        run_command('selected_architecture', phase, '--source', SOURCE, '--jobs', 6)


def lifecycle():
    from . import dex_lifecycle_review as life
    from .dex_lifecycle_return_repair import reveal_frames
    from .legacy_listing import private_battery
    from .performance import core
    tasks = []
    for variant in ('baseline', 'integrated'):
        models = ('E',) if variant == 'baseline' else ('0', 'A', 'B', 'C', 'D', 'E')
        folder = SOURCE / 'rollback' if variant == 'baseline' else SOURCE / 'candidate'
        repo = Repository(
            folder, folder / 'pokecrystal.gbc', folder / 'pokecrystal.sym')
        for model in models:
            target = BASE / 'lifecycle' / variant / model
            target.mkdir(parents=True, exist_ok=True)
            header = target / 'lifecycle-symbols.h'
            header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n' +
                '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}'
                          for name in ('hSCX', 'hWX', 'hWY')) + '\n')
            points = dict(life.PROFILE)
            if variant == 'integrated':
                points['close_submenu'] = ('Pokedex_CloseSubmenu', True)
                points['right_edge'] = ('Pokedex_InitListingRightEdge', True)
            binary = core(repo, target, points, ('-DDEX_LIFECYCLE_TRACE',
                f'-DDEX_LIFECYCLE_SYMBOLS="{header.resolve()}"',
                f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}'))
            config = dict(core=str(binary), rom=str(repo.rom_path),
                sym=str(folder / 'pokecrystal.sym'), battery=str(SOURCE / 'pokecrystal-dex-types.sav'),
                variants={variant: dict(rom=str(repo.rom_path))}, fixtures={})
            for style in (0, 1):
                for order in (0, 1, 2):
                    battery = target / f'{style}-{order}.sav'
                    private_battery(config, battery, presentation=style, order_mode=order)
                    config['fixtures'][f'{style}-{order}'] = str(battery)
                    tasks.extend((str(target), variant, style, order, phase)
                                 for phase in (0, 17556, 35112, 52668))
            life.write(target / 'config.json', config)
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        for task, batch in zip(tasks, pool.map(life.case, tasks)):
            for row in batch:
                target = Path(task[0]) / task[1] / f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
                with gzip.open(target / f'exit-{row["iteration"]}-events.json.gz', 'rt') as stream:
                    bad = reveal_frames(json.load(stream))
                rows.append(dict(row, model=Path(task[0]).name, premature_frames=len(bad)))
            if len(rows) % 48 == 0:
                print(json.dumps(dict(lifecycle_cases=len(rows))), flush=True)
    summaries = {}
    for variant in ('baseline', 'integrated'):
        group = [r for r in rows if r['variant'] == variant and r['model'] == 'E']
        summaries[variant] = {direction: dict(median_ms=statistics.median(
            r[direction]['input_to_ready_ms'] for r in group), median_frames=statistics.median(
            r[direction]['input_to_ready_ms'] for r in group) / (70224 * 1000 / 4194304))
            for direction in ('entry', 'exit')}
    failures = [r for r in rows if r['premature_frames'] or r['issues']]
    result = dict(cases=len(rows), failures=len(failures), summaries=summaries, rows=rows)
    life.write(BASE / 'lifecycle/summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2), flush=True)
    if failures:
        raise AssertionError('Source-linked lifecycle qualification failed')


def lifecycle_audit():
    from .dex_lifecycle_budget import visual_audit
    path = BASE / 'lifecycle/summary.json'
    result = json.loads(path.read_text())
    key = lambda r: tuple(r[k] for k in ('style', 'order', 'phase', 'iteration'))
    baseline = {key(r): r for r in result['rows'] if r['variant'] == 'baseline'}
    issues = []
    pre_fade_issues = []
    for row in result['rows']:
        target = BASE / 'lifecycle' / row['variant'] / row['model'] / row['variant'] / f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
        with gzip.open(target / f'exit-{row["iteration"]}-events.json.gz', 'rt') as stream:
            events = json.load(stream)
        enabled = [e['t'] for e in events if e['event'] == 'perf_phase' and e['name'] == 'enable_lcd'][-1]
        fade = next(e['t'] for e in events if e['event'] == 'perf_phase' and e['name'] == 'fade_in')
        bad = [e for e in events if e['event'] == 'perf_frame' and e['type'] == 0 and
               enabled <= e['boundary_t'] < fade and e['lcdc'] & 128 and e['white'] != 23040]
        if bad:
            pre_fade_issues.append(dict(variant=row['variant'], model=row['model'], case=key(row), frames=bad))
        if row['variant'] != 'integrated':
            continue
        for surface in ('listing', 'menu'):
            found = visual_audit(baseline[key(row)][surface], row[surface],
                                 row['style'], surface)['issues']
            if found:
                issues.append(dict(model=row['model'], case=key(row), surface=surface, issues=found))
    result['completed_screen_issues'] = issues
    result['nonwhite_before_fade_issues'] = pre_fade_issues
    for direction in ('entry', 'exit'):
        differences = [row[direction]['input_to_ready_ms'] - baseline[key(row)][direction]['input_to_ready_ms']
                       for row in result['rows'] if row['variant'] == 'integrated' and row['model'] == 'E']
        result['summaries']['integrated'][direction]['paired_median_delta_ms'] = statistics.median(differences)
        result['summaries']['integrated'][direction]['paired_median_delta_frames'] = statistics.median(differences) / (70224 * 1000 / 4194304)
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(completed_screen_issues=issues, nonwhite_before_fade_issues=pre_fade_issues,
                         summaries=result['summaries']), indent=2))
    if issues or pre_fade_issues:
        raise AssertionError('Completed lifecycle display differs')


def routes():
    from . import dex_lifecycle_review as life
    from .legacy_listing import private_battery
    tasks = []
    names = ('modes-cancel', 'pokemon-search', 'description', 'info-ancestors',
             'selected-moves', 'area', 'unown', 'types', 'moves-search')
    for variant in ('baseline', 'integrated'):
        target = BASE / 'lifecycle' / variant / 'E'
        config = json.loads((target / 'config.json').read_text())
        for style in (0, 1):
            battery = target / f'route-{style}.sav'
            private_battery(config, battery, presentation=style, order_mode=0, unown_unlocked=True)
            tasks.extend((str(target), variant, style, name, str(battery)) for name in names)
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(life.route_case, tasks))
    result = dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows), rows=rows)
    life.write(BASE / 'lifecycle/routes.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    if result['failures']:
        raise AssertionError('Linked secondary-route qualification failed')


def exit_matrix():
    from .backlog_revalidation import EXIT_POINTS, exit_case
    from .cold_listing import Driver
    from .info_ui import BOOT
    from .listing_restoration import compile_observer
    fixture = SOURCE / 'focused/modern'
    repo = Repository(SOURCE / 'candidate', SOURCE / 'pokecrystal-dex-types.gbc',
                      SOURCE / 'pokecrystal-dex-types.sym')
    repo.symbols['CloseSubmenu'] = repo.symbols['Pokedex_CloseSubmenu']
    output = BASE / 'lifecycle/exit-matrix'
    output.mkdir(parents=True, exist_ok=True)
    binary = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
        extra_points={k: v for k, v in EXIT_POINTS.items() if v in repo.symbols},
        extra_fields=('wPokedexRenderedSelectionKey',),
        extra_flags=('-DDEX_BACKLOG_REVALIDATION_TRACE',))
    driver = Driver(binary, repo.rom_path, BOOT, fixture / 'private.sav', output / 'core.log')
    try:
        rows = [exit_case(driver, repo, fixture, output, name, pages, idle, False)
                for name in ('chikorita', 'dusknoir', 'weavile', 'regigigas')
                for pages in ((-1, 0) if name == 'regigigas' else (-1, 0, 9))
                for idle in range(8)]
    finally:
        driver.close()
    result = dict(rom_sha256=sha256(repo.rom), cases=len(rows),
        failures=sum(bool(r['shifted_frames']) or bool(r['blocked_palette_writes']) for r in rows), rows=rows)
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    if result['failures']:
        raise AssertionError('Hardware publication audit failed')


def audio():
    result = json.loads((BASE / 'lifecycle/summary.json').read_text())
    reviewed = json.loads((BASE / 'lifecycle/reviewed/summary.json').read_text())
    rows = []
    for style in (0, 1):
        for order in (0, 1, 2):
            for direction in ('entry', 'exit'):
                spans = []
                for variant in ('baseline', 'reviewed', 'integrated'):
                    folder = (BASE / 'lifecycle/reviewed' if variant == 'reviewed' else
                              BASE / 'lifecycle' / variant / 'E') / variant / f'style-{style}-order-{order}-q0'
                    with gzip.open(folder / f'{direction}-0-events.json.gz', 'rt') as stream:
                        events = json.load(stream)
                    gate = next(e['t'] for e in events if e['event'] == 'perf_phase' and
                                e['name'] == ('cleanup' if direction == 'exit' else 'menu_accept'))
                    sound = [e for e in events if e['event'] == 'life_sfx']
                    prior = [e for e in sound if e['t'] <= gate]
                    start = (prior[-1]['t'] if prior and prior[-1]['mask'] else
                             next(e['t'] for e in sound if e['t'] >= gate and e['mask']))
                    end = next(e['t'] for e in sound if e['t'] > start and not e['mask'])
                    spans.append(dict(variant=variant, duration_ms=(end-start)*1000/4194304,
                                      duration_frames=(end-start)/70224))
                rows.append(dict(style=style, order=order, direction=direction, spans=spans,
                    delta_ms=spans[2]['duration_ms']-spans[1]['duration_ms'],
                    baseline_delta_ms=spans[2]['duration_ms']-spans[0]['duration_ms']))
    # Acceptance is parity with the manually approved fixed Stage, not the
    # deliberately slower original production entry's sound-service cadence.
    record = dict(cases=len(rows), duration_mismatches=sum(abs(r['delta_ms']) > .001 for r in rows),
                  reviewed_rom_sha256=reviewed['rom_sha256'],
                  integrated_rom_sha256=json.loads((BASE / 'integration.json').read_text())['rom_sha256'],
                  scope='Fresh native active cue durations versus approved Stage; baseline differences retained', rows=rows)
    (BASE / 'lifecycle/audio.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'rows'}))
    if record['duration_mismatches']:
        raise AssertionError('Button cue duration changed')


def audio_reference():
    from . import dex_lifecycle_review as life
    from .legacy_listing import private_battery
    from .performance import core
    original = ROOT / 'build/dex-lifecycle-budget-20261013/stage-return-repair'
    prior = json.loads((original / 'config.json').read_text())
    resource = prior['variants']['stage-mask-commit']
    repo = Repository(ROOT, Path(resource['rom']), Path(prior['sym']))
    assert sha256(repo.rom) == resource['sha256']
    repo.symbols['CloseSubmenu'] = tuple(resource['close_probe'])
    target = BASE / 'lifecycle/reviewed'
    target.mkdir(parents=True, exist_ok=True)
    header = target / 'lifecycle-symbols.h'
    header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n' +
        '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}' for name in ('hSCX', 'hWX', 'hWY')) + '\n')
    binary = core(repo, target, life.PROFILE, ('-DDEX_LIFECYCLE_TRACE',
        f'-DDEX_LIFECYCLE_SYMBOLS="{header.resolve()}"', '-DDEX_TEST_MODEL=GB_MODEL_CGB_E'))
    config = dict(core=str(binary), rom=str(repo.rom_path), sym=prior['sym'],
        battery=str(SOURCE / 'pokecrystal-dex-types.sav'), fixtures={},
        variants=dict(reviewed=dict(rom=str(repo.rom_path))))
    tasks = []
    for style in (0, 1):
        for order in (0, 1, 2):
            battery = target / f'{style}-{order}.sav'
            private_battery(config, battery, presentation=style, order_mode=order)
            config['fixtures'][f'{style}-{order}'] = str(battery)
            tasks.append((str(target), 'reviewed', style, order, 0))
    life.write(target / 'config.json', config)
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows = [r for batch in pool.map(life.case, tasks) for r in batch]
    life.write(target / 'summary.json', dict(rom_sha256=sha256(repo.rom), cases=len(rows), rows=rows))
    audio()


def resources():
    path = BASE / 'integration.json'
    result = json.loads(path.read_text())
    old = Repository(SOURCE / 'rollback', SOURCE / 'rollback/pokecrystal.gbc',
                     SOURCE / 'rollback/pokecrystal.sym')
    new = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    expected = bytearray(old.rom[:0x4000])
    fields = []
    for caller, target, opcode in (
            ('LoadCry', 'TryLoadSampledCryBySpeciesIndex', 0x21),
            ('PlayCry', 'TryLoadSampledCryBySpeciesIndex', 0x21),
            ('FarSkipEvolutions', 'SkipEvolutions', 0xcd),
            ('GetMoveAddress', 'Moves', 0x21)):
        start = old.symbols[caller][1]
        end = min(pair[1] for pair in old.symbols.values() if pair[0] == 0 and pair[1] > start)
        operand = old.symbols[target][1]
        needle = bytes((opcode,)) + operand.to_bytes(2, 'little')
        body = old.rom[start:end]
        assert body.count(needle) == 1, caller
        at = start + body.index(needle) + 1
        replacement = new.symbols[target][1].to_bytes(2, 'little')
        expected[at:at + 2] = replacement
        fields.append(dict(caller=caller, target=target, address=at,
                           original=operand, linked=int.from_bytes(replacement, 'little'), width=2))
    expected[0x14e:0x150] = new.rom[0x14e:0x150]
    assert bytes(expected) == new.rom[:0x4000], 'Unexpected fixed-bank change'
    assert result['rom_sha256'] == sha256(new.rom)
    assert result['delta'] == dict(ROM0=0, ROMX=96, SRAM=0, WRAM0=0, WRAMX=0, HRAM=0)
    assert not result['changed_ram_labels']
    result.update(fixed_bank_instruction_sequence_unchanged=True,
                  fixed_bank_changes_are_linker_operands_and_checksum_only=True,
                  fixed_bank_relocations=fields,
                  toolchain={name: subprocess.check_output(command, cwd=ROOT).decode().strip()
                             for name, command in (
                                 ('python', [sys.executable, '--version']),
                                 ('rgbds', ['rgbasm', '--version']),
                                 ('clang', ['clang', '--version']),
                                 ('sameboy_revision', ['git', '-C', str(Path.home() / 'Documents/GitHub/SameBoy'),
                                                      'rev-parse', 'HEAD']))})
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'prepare', 'animations', 'displays',
                                          'selected', 'lifecycle', 'lifecycle-audit',
                                          'routes', 'exit-matrix', 'audio', 'audio-reference', 'resources'))
    args = parser.parse_args()
    globals()[args.action.replace('-', '_')]()
