"""Run established full campaigns on an immutable Type Matchups prototype."""
import argparse
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import unittest

from .assets import sha256
from .cold_listing import ROOT

STEMS = ('pokecrystal-dex-moves-search', 'pokecrystal-dex-moves-mode',
         'pokecrystal-dex-moves-persistence', 'pokecrystal-dex-moves-battle-use',
         'pokecrystal-dex-moves-sort-memory', 'pokecrystal-dex-unown-fix',
         'pokecrystal-dex-no-warming')


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare(source, output, baseline_source=None):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private build directory')
    output.mkdir(parents=True)
    reference = ROOT / 'build/dex-moves-search-final-review-20261011'
    production = {str(ROOT / f'pokecrystal.{ext}'): sha256((ROOT / f'pokecrystal.{ext}').read_bytes())
                  for ext in ('gbc', 'sym', 'map')}
    baseline_files = baseline_source or ROOT
    (output / 'candidate').symlink_to(source / 'candidate', target_is_directory=True)
    baseline = output / 'baseline'
    baseline.mkdir()
    with tarfile.open(source / 'rollback-source.tar') as archive:
        archive.extractall(baseline / 'candidate', filter='data')
    # Linked host tests read conventional names inside the source directory.
    for ext in ('gbc','sym','map'):
        shutil.copy2(baseline_files / f'pokecrystal.{ext}', baseline / f'candidate/pokecrystal.{ext}')
    for folder, original in ((output, source / 'pokecrystal-dex-types'),
                             (baseline, baseline_files / 'pokecrystal')):
        for stem in STEMS:
            for ext in ('gbc', 'sym', 'map'):
                shutil.copy2(original.with_suffix('.' + ext), folder / f'{stem}.{ext}')
            shutil.copy2(source / 'pokecrystal-dex-types.sav', folder / f'{stem}.sav')
        for name in ('all-seen-tests.sav', 'legacy-input.sav', 'sort-manifest.json',
                     'moves-mode-manifest.json'):
            shutil.copy2(reference / name, folder / name)
        (folder / 'battle-review').mkdir()
        old = json.loads((folder / 'moves-mode-manifest.json').read_text())
        old.update(rom_sha256=sha256((folder / 'pokecrystal-dex-moves-search.gbc').read_bytes()),
                   end_cursor_rollback=str(baseline))
        write(folder / 'moves-mode-manifest.json',old)
        battle = Path(old['sort_memory_source']) / 'battle-review'
        source_stem = json.loads((battle.parent / 'moves-mode-manifest.json').read_text())['stem']
        shutil.copy2(battle / f'{source_stem}.sav',
                     folder / 'battle-review/pokecrystal-dex-moves-sort-memory.sav')
        unown = json.loads((ROOT / 'build/dex-unown-black-20261011/unown-manifest.json').read_text())
        write(folder / 'unown-manifest.json', {key: unown[key] for key in
              ('red_background', 'black_panels', 'base', 'original_defect_base', 'background_defect_base')})
    write(output / 'campaign-manifest.json', dict(source=str(source),
          rom_sha256=sha256((source / 'pokecrystal-dex-types.gbc').read_bytes()),
          baseline_sha256=sha256((baseline_files / 'pokecrystal.gbc').read_bytes()),
          baseline_source=str(baseline_files),
          protected_inputs=production, fixture_definitions=str(reference),
          historical_manifests_are_fixture_definitions_only=True))


def commands(output, phase):
    out, base = str(output), str(output / 'baseline')
    dex = str(output / 'dex-regression')
    if phase == 'setup':
        return [('moves_search', 'prepare', '--output', out),
                ('moves_search_dex_regression', 'prepare', '--output', out),
                ('moves_search_dex_regression', 'prepare', '--output', base),
                ('moves_sort_memory', 'prepare', '--output', out)]
    if phase == 'dex':
        return [('moves_search_dex_regression', action, '--output', out, '--jobs', '6')
                for action in ('listings', 'interfaces', 'selected')] + [
                ('search_qualification', '--source', dex, '--jobs', '6', *flags)
                for flags in ((), ('--returns',), ('--defaults',))] + [
                ('mode_transitions', '--output', dex, '--jobs', '6', '--indices', '0,8,255,372', '--phases', '4'),
                ('mode_transitions', '--output', dex, '--jobs', '6', '--indices', '0,8', '--phases', '2',
                 '--prior-view', 'info', '--tag', 'unown-prior-info'),
                ('mode_transitions', '--output', dex, '--jobs', '6', '--indices', '0,8', '--phases', '2',
                 '--prior-view', 'moves', '--tag', 'unown-prior-moves'),
                ('moves_search_dex_regression', 'qualify', '--output', out),
                ('unown_regression', '--output', out, '--jobs', '6')]
    if phase == 'moves':
        return [('moves_search', action, '--output', out) for action in
                ('filter', 'ui', 'visual', 'navigation', 'transitions', 'surrounding', 'polish', 'cursor')] + [
                ('moves_sort_memory', action, '--output', out) for action in ('helpers', 'ui', 'saves')]
    if phase == 'persistence':
        return [('move_persistence', '--output', out, '--baseline', base, '--jobs', '6'),
                ('move_acquisition', '--output', out, '--jobs', '6', '--migration'),
                ('move_acquisition', '--output', out, '--jobs', '6', '--interruptions')]
    if phase == 'discovery':
        return [('moves_search', 'tracking', '--output', out)]
    if phase == 'gameplay':
        return [('acquisition_regression', action, '--output', out, '--baseline', base, '--jobs', '6')
                for action in ('menus', 'audio', 'gameplay', 'custom', 'transitions', 'moves')]
    if phase == 'battle-discovery':
        return [('move_battle_use', '--output', out, '--jobs', '6', '--only', 'contract'),
                ('move_battle_use', '--output', out, '--jobs', '6', '--only', 'semantic'),
                ('move_battle_use', '--output', out, '--jobs', '6', '--only', 'semantic', '--kinds', 'bide')]
    if phase == 'timing':
        return [('acquisition_performance', '--output', out, '--baseline', base),
                ('listing_warming', 'idle', '--output', out, '--jobs', '6'),
                ('listing_warming', 'timing', '--output', out, '--jobs', '6')] + [
                ('performance_regression', '--config', str(output / f'dex-regression/{style}/config.json'),
                 '--output', str(output / f'playback-{style}'), '--suites', 'cold', 'paging', 'warm',
                 '--expected-double-speed', '--jobs', '6') for style in ('modern', 'legacy')]
    if phase == 'readiness':
        return [('acquisition_report', 'readiness', '--output', out, '--baseline', base)]
    raise ValueError(phase)


def run(output, phase):
    logs = output / 'campaign-logs'
    logs.mkdir(exist_ok=True)
    if phase == 'gameplay':
        prerequisite = logs / 'discovery.json'
        if not prerequisite.exists() or json.loads(prerequisite.read_text())['issues']:
            raise ValueError('Finish discovery before gameplay recreates its battle fixtures')
    if phase == 'timing':
        required = ('acquisition-qualification/legacy-full-current-1.sav',
                    'persistence-qualification/repair-source.sav')
        if any(not (output / name).is_file() for name in required):
            raise ValueError('Finish persistence/migration fixture generation before timing')
    if phase == 'battle-discovery' and not (output / 'runtime/menus/acquisition/battle/battle-main.s0').is_file():
        raise ValueError('Finish gameplay menu/battle fixture generation before battle discovery')
    results = []
    env = dict(os.environ, PYTHONPATH='tools:.')
    for number, command in enumerate(commands(output, phase)):
        path = logs / f'{phase}-{number:02}-{command[0]}.log'
        started = time.monotonic()
        print(json.dumps(dict(start=command, log=str(path))), flush=True)
        with path.open('w') as log:
            result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + command[0], *command[1:]],
                                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        row = dict(command=command, exit_code=result.returncode,
                   seconds=round(time.monotonic() - started, 2), log=str(path))
        results.append(row)
        write(logs / f'{phase}.json', dict(results=results, issues=[r for r in results if r['exit_code']]))
        print(json.dumps(row), flush=True)
        if result.returncode:
            print(path.read_text()[-6000:], flush=True)
    manifest = json.loads((output / 'campaign-manifest.json').read_text())
    for path, digest in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError('Production changed during regression: ' + path)
    return int(any(r['exit_code'] for r in results))


def host(output):
    target = output / 'campaign-logs'
    modules = []
    candidate = output / 'candidate'
    for name in ('test_moves_dex_production', 'test_dex_scheduler', 'test_pokedex_info',
                 'test_pokedex_moves', 'test_pokedex_area_assets', 'test_description_paging',
                 'test_sampled_cry_shutdown', 'test_battle_motion'):
        module = importlib.import_module('tools.' + name)
        module.__file__ = str(candidate / 'tools' / (name + '.py'))
        if hasattr(module, 'ROOT'):
            module.ROOT = candidate
        modules.append(module)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules)
    with (target / 'host.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    record = dict(cases=result.testsRun, skipped=len(result.skipped),
                  failures=[dict(test=str(test), detail=detail) for test, detail in result.failures],
                  errors=[dict(test=str(test), detail=detail) for test, detail in result.errors])
    baseline_cases = []
    for test, _ in result.failures + result.errors:
        case = getattr(test, 'test_case', test)
        baseline_cases.append(case.id())
    for module in modules:
        module.__file__ = str(output / 'baseline/candidate/tools' / Path(module.__file__).name)
        if hasattr(module, 'ROOT'):
            module.ROOT = output / 'baseline/candidate'
    with (target / 'host-baseline-failures.log').open('w') as log:
        baseline = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromNames(sorted(set(baseline_cases))))
    record['baseline_failures'] = [dict(test=str(test), detail=detail) for test, detail in baseline.failures]
    record['baseline_errors'] = [dict(test=str(test), detail=detail) for test, detail in baseline.errors]
    record['no_new_failures'] = (record['failures'] == record['baseline_failures'] and
                                 record['errors'] == record['baseline_errors'])
    write(target / 'host.json', record)
    print(json.dumps(record), flush=True)
    return int(not record['no_new_failures'])


def diagnose_types(output):
    from .assets import Repository
    from .cold_listing import Driver, bootstrap
    from .performance import core
    from .type_matchups import BOOT, Oracle, enter_types, capture
    source = Path(json.loads((output / 'campaign-manifest.json').read_text())['source'])
    target = output / 'type-diagnostic'
    target.mkdir(exist_ok=True)
    repo = Repository(source / 'candidate', source / 'pokecrystal-dex-types.gbc',
                      source / 'pokecrystal-dex-types.sym')
    executable = core(repo, target, {})
    driver = Driver(executable, repo.rom_path, BOOT, source / 'pokecrystal-dex-types.sav', target / 'trace.log')
    rows = []
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        enter_types(driver, repo, True)
        oracle = Oracle(repo)
        for frame in range(16):
            image = capture(driver, target / f'frame-{frame:02}.png')
            differences = []
            for index, name in enumerate(oracle.names):
                x, y = 16 + index % 3 * 48, 8 + index // 3 * 14
                actual = image.crop((x,y,x+32,y+8))
                wanted = oracle.icons[index]
                for dy in range(8):
                    for dx in range(32):
                        if actual.getpixel((dx,dy)) != wanted.getpixel((dx,dy)):
                            differences.append(dict(type=name,x=x+dx,y=y+dy,
                                actual=actual.getpixel((dx,dy)),expected=wanted.getpixel((dx,dy))))
            rows.append(dict(frame=frame,differences=differences))
            driver.run(frames=1)
        write(target / 'ui.json', driver.command('ui'))
        write(target / 'ice-tile.json', driver.command('inspectvram 1 36896 16'))
        driver.command(f'save {target}/state.s0')
    finally:
        driver.close()
    record = dict(rom_sha256=sha256(repo.rom), no_type_trace_instrumentation=True,
                  frames=rows, failures=sum(bool(r['differences']) for r in rows))
    write(target / 'summary.json', record)
    print(json.dumps(record),flush=True)
    return int(bool(record['failures']))


def chart(output):
    from .assets import Repository
    from .type_matchups import Oracle, battle_chart
    source = Path(json.loads((output / 'campaign-manifest.json').read_text())['source'])
    repo = Repository(source / 'candidate', source / 'pokecrystal-dex-types.gbc',
                      source / 'pokecrystal-dex-types.sym')
    record = dict(rom_sha256=sha256(repo.rom), **battle_chart(repo,Oracle(repo),source / 'type-tests'), issues=[])
    write(output / 'type-chart.json',record)
    print(json.dumps(record),flush=True)


def historical_host(output):
    candidate = output / 'candidate'
    baseline = output / 'baseline/candidate'
    # A frozen baseline may use a different generated table format.
    # Populate missing dependencies only; never replace its matching assets.
    for name in ('dex-area-assets', 'dex-info-assets', 'dex-moves-assets',
                 'dex-moves-mode-assets', 'dex-sort-assets'):
        if not (baseline / 'build' / name).exists():
            shutil.copytree(candidate / 'build' / name, baseline / 'build' / name)
    if not (baseline / 'gfx').exists():
        shutil.copytree(candidate / 'gfx', baseline / 'gfx')
    records = {}
    for variant,root in (('baseline',baseline),('candidate',candidate)):
        os.environ['DEX_TIMING_REFERENCE_ROOT'] = str(root)
        module = importlib.import_module('tools.test_dex_timing')
        module = importlib.reload(module)
        with (output / f'campaign-logs/historical-{variant}.log').open('w') as log:
            result = unittest.TextTestRunner(stream=log,verbosity=2).run(
                unittest.defaultTestLoader.loadTestsFromModule(module))
        def detail(rows):
            return [dict(test=str(test),detail=text.replace(str(root),'<source>')) for test,text in rows]
        records[variant] = dict(cases=result.testsRun,failures=detail(result.failures),
                                errors=detail(result.errors),skipped=detail(result.skipped))
    identities = {variant:{key:[row['test'] for row in data[key]]
                           for key in ('failures','errors','skipped')}
                  for variant,data in records.items()}
    differences = [dict(kind=key,test=old['test'],baseline=old['detail'],candidate=new['detail'])
                   for key in ('failures','errors','skipped')
                   for old,new in zip(records['baseline'][key],records['candidate'][key]) if old!=new]
    record = dict(records=records,identical=records['baseline']==records['candidate'],
                  same_failure_error_skip_identities=identities['baseline']==identities['candidate'],
                  message_differences=differences)
    write(output / 'historical-host-comparison.json',record)
    print(json.dumps(dict(identical=record['identical'],summaries={k:dict(cases=v['cases'],
          failures=len(v['failures']),errors=len(v['errors']),skipped=len(v['skipped']))
          for k,v in records.items()})),flush=True)
    return int(not record['same_failure_error_skip_identities'])


def gift(output):
    from .assets import read_symbols
    from .move_persistence import boot,call,core,read,checksum
    from .pokedex_gift import award
    from move_discovery_assets import address,seed_records,move_bitmap
    from tools.pokedex_info_assets import constants
    target = output / 'pokedex-gift'
    target.mkdir(exist_ok=True)
    stem = 'pokecrystal-dex-moves-battle-use'
    symbols = read_symbols(output / f'{stem}.sym')
    config = dict(rom=str(output / f'{stem}.gbc'),symbols=symbols,
                  core=str(core(output,target_root=target)))
    data = bytearray((output / 'legacy-input.sav').read_bytes())
    for prefix in ('s','sBackup'):
        at = address(symbols,prefix+'PlayerData') + symbols['wStatusFlags'][1] - symbols['wPlayerData'][1]
        data[at] &= ~1
        checksum(data,symbols,prefix)
    battery = target / 'pre-dex.sav'
    battery.write_bytes(seed_records(data,symbols,bytes(64)))
    struggle = constants(ROOT / 'constants/move_constants.asm')['STRUGGLE']
    driver = boot(config,battery,target / 'award.log')
    rows = []
    try:
        assert read(driver,symbols)[:64] == bytes(64)
        driver.command(f'trace {target}/award-sram.csv')
        for phase in range(4):
            for seen in ([],[1,85,333],[struggle],list(range(1,334))):
                call(driver,symbols,'MoveDiscovery_Clear')
                for index in seen:
                    call(driver,symbols,'MoveDiscovery_MarkIndex',index)
                driver.command(f'cycles {phase*35112} 0')
                award(driver,symbols,move_bitmap(seen),struggle)
                after = read(driver,symbols)
                award(driver,symbols,after[:64],struggle)
                assert read(driver,symbols) == after
                rows.append(dict(phase=phase,previous_count=len(seen)))
        driver.command('trace off')
        assert not (target / 'award-sram.csv').read_bytes()
        call(driver,symbols,'SaveGameData')
        driver.command(f'battery {target}/saved.sav')
    finally:
        driver.close()
    driver = boot(config,target / 'saved.sav',target / 'cold-reload.log')
    try:
        assert read(driver,symbols)[:64] == move_bitmap(range(1,334))
    finally:
        driver.close()
    record = dict(rom_sha256=sha256(Path(config['rom']).read_bytes()),award_cases=len(rows),
                  repeated_awards=len(rows),cold_save_reload=True,no_immediate_sram_write=True,issues=[])
    write(output / 'pokedex-gift-regression.json',record)
    print(json.dumps(record),flush=True)


def report(output):
    from .moves_search import full_regression_report
    import statistics
    manifest = json.loads((output / 'campaign-manifest.json').read_text())
    fixture_path = output / 'moves-mode-manifest.json'
    fixture_manifest = json.loads(fixture_path.read_text())
    fixture_manifest['end_cursor_rollback'] = str(output / 'baseline')
    write(fixture_path,fixture_manifest)
    paired = full_regression_report(output)
    def read_json(relative):
        return json.loads((output / relative).read_text())
    dex = read_json('dex-regression/summary.json')
    assert dex['failures'] == 0
    ui = {name:read_json('search-tests/'+name+'/summary.json') for name in
          ('visual','navigation','transitions','surrounding','form-polish','naming-cursor')}
    ui.update(filter=read_json('search-tests/filter.json'),ui=read_json('search-tests/ui.json'))
    assert all(not row.get('issues') for row in ui.values())
    sort = {name:read_json('sort-memory/'+path) for name,path in
            (('helpers','helpers.json'),('ui','ui/summary.json'),('saves','saves/summary.json'))}
    assert all(not row.get('issues') for row in sort.values())
    host_record = read_json('campaign-logs/host.json')
    assert host_record['no_new_failures']
    history = read_json('historical-host-comparison.json')
    assert history['same_failure_error_skip_identities']
    unown = read_json('unown-tests/summary.json')
    assert not unown['failures']
    playback = {style:read_json('playback-'+style+'/summary.json')['summary'] for style in ('modern','legacy')}
    assert all(not row['failures'] for group in playback.values() for row in group.values())
    entries = read_json('entry-timing/summary.json')
    assert not entries['failures']
    reveal = {}
    for row in entries['rows']:
        events = read_json('entry-timing/'+f'{row["variant"]}-{row["presentation"]}-{row["species"]}-h{row["hover"]}-q{row["phase"]}.events.json')
        frames = [e for e in events if e['event']=='perf_frame']
        key = row['species'],row['hover'],row['phase']
        shown = next(e for e in frames if e['wx']==167)
        # Recover the input origin from the recorded first-change event.
        first = next(e for e in frames if e['display']==row['timing']['first_visible']['displayed_frames'])
        origin = first['t'] - row['timing']['first_visible']['cycles']
        reveal.setdefault(row['presentation'],{}).setdefault(key,{})[row['variant']] = (shown['t']-origin)*1000/4194304
    owner_reveal = {}
    for style,group in reveal.items():
        differences = [v['candidate']-v['baseline'] for v in group.values()]
        owner_reveal[style] = dict(pairs=len(differences),min_delta_ms=min(differences),
            median_delta_ms=statistics.median(differences),max_delta_ms=max(differences))
    source = Path(manifest['source'])
    type_models = {}
    for model in ('0','A','B','C','D','E'):
        model_path = source / 'type-tests' / ('' if model=='E' else 'cgb-'+model) / 'summary.json'
        if model_path.exists():
            type_models[model] = json.loads(model_path.read_text())
    arrows = json.loads((source / 'arrow-tests/summary.json').read_text())
    defect = read_json('type-diagnostic/summary.json')
    motion = read_json('acquisition-moves-regression.json')['results']
    before = {(row['move'],row['side'],row['quarter']):row for row in motion if row['variant']=='baseline'}
    timing_rows = []
    for row in motion:
        if row['variant'] != 'acquisition':
            continue
        old = before[row['move'],row['side'],row['quarter']]
        delta = row['requested_animations'][0]['elapsed_t'] - old['requested_animations'][0]['elapsed_t']
        timing_rows.append(dict(move=row['move'],side=row['side'],phase=row['quarter'],
                                delta_t=delta,delta_frames=delta/70224,delta_ms=delta*1000/4194304))
    largest = max(timing_rows,key=lambda row:row['delta_frames'])
    timing_issue = any(abs(row['delta_frames'])>1 for row in timing_rows)
    issues = ([dict(issue='Ice badge has six black pixels at x114..119, y56',
                    evidence='type-diagnostic/summary.json',pixel_frames=defect['failures'])]
              if defect['failures'] else [])
    chart_phase_path = source.parent / 'chart-phase-check-100/summary.json'
    chart_phase = json.loads(chart_phase_path.read_text()) if chart_phase_path.exists() else None
    chart_proven = bool(chart_phase and chart_phase['all_original_chart_durations_exact'] and
                       manifest['rom_sha256'] in chart_phase.get('candidate_rom_sha256s',{}).values() and
                       chart_phase['production_rom_sha256']==manifest['baseline_sha256'])
    if chart_proven:
        evidence = {(r['move'],r['side'],r['quarter']):r for r in chart_phase['comparisons']}
        chart_proven = all((r['move'],r['side'],r['phase']) in evidence and
            evidence[r['move'],r['side'],r['phase']]['original_chart_delta_t']==0 and
            evidence[r['move'],r['side'],r['phase']]['changed_chart_delta_t']==r['delta_t']
            for r in timing_rows if r['delta_t'])
    if timing_issue and not chart_proven:
        issues.append(dict(issue='Paired battle animation duration changes are not yet explained',
                           evidence='acquisition-moves-regression.json',largest_increase=largest))
    from .assets import read_symbols
    mode7_audio, mode7_audio_navigation, all_animations = None, None, None
    if 'PokedexTypes_VBlank' in read_symbols(source / 'pokecrystal-dex-types.sym'):
        audio_path = source / 'audio-stress/summary.json'
        navigation_path = source / 'audio-navigation/summary.json'
        animation_path = source.parent / 'all-animations/report.json'
        if audio_path.exists():
            mode7_audio = json.loads(audio_path.read_text())
        if not mode7_audio or mode7_audio.get('rom_sha256') != manifest['rom_sha256'] or mode7_audio['issues'] or mode7_audio.get('songs') != 122:
            issues.append(dict(issue='Fresh private-owner all-music/SFX stress acceptance is missing or failed',evidence=str(audio_path)))
        if navigation_path.exists():
            mode7_audio_navigation = json.loads(navigation_path.read_text())
        if not mode7_audio_navigation or mode7_audio_navigation.get('rom_sha256') != manifest['rom_sha256'] or mode7_audio_navigation['issues'] or mode7_audio_navigation.get('songs') != 122 or not mode7_audio_navigation.get('held_input'):
            issues.append(dict(issue='Fresh private-owner music/SFX/navigation acceptance is missing or failed',evidence=str(navigation_path)))
        if animation_path.exists():
            all_animations = json.loads(animation_path.read_text())
        required = ('complete_coverage', 'restoration_passed', 'logical_sequence_passed',
                    'all_variant_timing_exact', 'visual_sequence_passed',
                    'native_coverage_passed', 'native_issue_identities_match')
        if not all_animations or manifest['rom_sha256'] not in all_animations.get('rom_sha256s',{}).values() or not all(all_animations.get('qualification',{}).get(key) for key in required):
            issues.append(dict(issue='Fresh exhaustive battle-animation timing/visual acceptance is missing or failed',evidence=str(animation_path)))
        if len(type_models) != 6:
            issues.append(dict(issue='Fresh six-model Type visual qualification is incomplete'))
        elif any(row.get('rom_sha256') != manifest['rom_sha256'] for row in type_models.values()):
            issues.append(dict(issue='Six-model Type qualification ROM hashes do not match the candidate'))
    for path,digest in manifest['protected_inputs'].items():
        assert sha256(Path(path).read_bytes()) == digest
    for suffix in ('gbc','sav'):
        assert sha256((source / f'pokecrystal-dex-types.{suffix}').read_bytes()) == sha256(
            (output / f'pokecrystal-dex-moves-search.{suffix}').read_bytes())
    record = dict(rom_sha256=manifest['rom_sha256'],baseline_sha256=manifest['baseline_sha256'],
                  production_unchanged=True,rom_unchanged=True,merge_ready=not issues,issues=issues,
                  dex=dex,move_search={k:dict(cases=v['cases'],issues=v['issues']) for k,v in ui.items()},
                  sort_memory=sort,paired_campaigns=paired,playback=playback,
                  unown={k:unown[k] for k in ('cases','form_selections','draw_unit_cases','failures')},
                  arrows=arrows,type_chart=read_json('type-chart.json'),gift=read_json('pokedex-gift-regression.json'),
                  acquisitions={name:read_json(name+'.json') for name in
                                ('acquisition-qualification','acquisition-sources')},
                  host=host_record,historical_host=history,
                  entry_timing=entries['summary'],modern_owner_reveal=owner_reveal['modern'],
                  legacy_owner_reveal=owner_reveal['legacy'],
                  battle_duration_comparison=dict(pairs=len(timing_rows),
                      over_one_frame=sum(abs(row['delta_frames'])>1 for row in timing_rows),
                      largest_increase=largest,rows=timing_rows,
                      changed_start_phase_from_requested_chart=chart_proven,
                      chart_ablation=chart_phase),
                  test_harness_updates=['Valid blinking phases accepted in Moves Sort',
                      'Type Matchups placeholder test replaced with real owner entry/return',
                      'Popup readiness rerun after required custom-menu fixture setup'],
                  type_models=type_models,
                  mode7_audio=mode7_audio,mode7_audio_navigation=mode7_audio_navigation,
                  all_animations=(None if not all_animations else
                      {k:all_animations[k] for k in ('rom_sha256s','moves','renderer_calls','coverage','qualification','summaries')}),
                  gaps=([] if len(type_models)==6 and not defect['failures'] else
                        ['Fresh six-model Type visual qualification incomplete']) +
                       ['Real Game Boy hardware not tested',
                        'Historical host assertions with matching production failures remain outside native acceptance'])
    write(output / 'full-regression.json',record)
    print(json.dumps({k:record[k] for k in ('rom_sha256','merge_ready','issues','modern_owner_reveal','legacy_owner_reveal','gaps')}),flush=True)
    return int(bool(issues))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'setup', 'dex', 'moves', 'persistence', 'discovery', 'host', 'diagnose-types', 'chart', 'historical-host', 'gift', 'report',
                                         'gameplay', 'battle-discovery', 'timing', 'readiness'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--baseline-source', type=Path,
                        help='Frozen pre-integration ROM/symbol/map folder; current production remains protected')
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare(args.source.resolve(), args.output.resolve(),
                args.baseline_source.resolve() if args.baseline_source else None)
    elif args.phase == 'host':
        raise SystemExit(host(args.output.resolve()))
    elif args.phase == 'diagnose-types':
        raise SystemExit(diagnose_types(args.output.resolve()))
    elif args.phase == 'chart':
        chart(args.output.resolve())
    elif args.phase == 'historical-host':
        raise SystemExit(historical_host(args.output.resolve()))
    elif args.phase == 'gift':
        gift(args.output.resolve())
    elif args.phase == 'report':
        raise SystemExit(report(args.output.resolve()))
    else:
        raise SystemExit(run(args.output.resolve(), args.phase))
