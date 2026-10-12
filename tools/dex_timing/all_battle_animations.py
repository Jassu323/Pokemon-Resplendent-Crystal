"""Exhaustive private renderer comparisons plus normal battle-input coverage."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
import gzip
import json
from pathlib import Path
import re
import statistics
import subprocess

from .assets import Repository, sha256
from .cold_listing import ROOT, FRAME
from .new_entry import CORE_FILES
from . import animation_reference as motion, global_speed as speed
from tools.pokedex_info_assets import constants

SOURCE = ROOT / 'build/dex-types-cursors-20261011'
CAMPAIGN = ROOT / 'build/dex-types-full-regression-20261012'
INVESTIGATION = ROOT / 'build/dex-types-investigation-20261012'
OUTPUT = ROOT / 'build/dex-types-all-animations-20261012'
PHASES = (0, 17556, 35112, 52668)
CUSTOM_CONFIGURATIONS = None


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def moves():
    text = (ROOT / 'constants/move_constants.asm').read_text().split('DEF NUM_ATTACKS')[0]
    return [m for m in re.findall(r'^\s*const\s+(\w+)', text, re.M) if m != 'NO_MOVE']


def catalogue():
    text = (ROOT / 'data/moves/animation_pointers.asm').read_text()
    before, after = text.split('BattleAnimations::')
    negative = re.findall(r'^\s*dw\s+(\w+)', before, re.M)
    positive = re.findall(r'^\s*dw\s+(\w+)', after, re.M)
    script = (ROOT / 'data/moves/animations.asm').read_text()
    blocks = {m[1]: m[2] for m in re.finditer(r'^(BattleAnim_\w+):\s*\n(.*?)(?=^BattleAnim_\w+:|\Z)', script, re.M | re.S)}
    rows = []
    for index, label in [(i - len(negative), n) for i, n in enumerate(negative)] + list(enumerate(positive)):
        # Parameters include both charge/release branches, Substitute stages,
        # shiny send-out, and ball variants. Scripts run on the native renderer.
        body = blocks.get(label, '')
        params = {0}
        if 'anim_if_param' in body:
            params |= {1, 2, 3}
        rows.append(dict(id=index & 65535, label=label, name=(moves()[index-1] if 1 <= index <= len(moves()) else label),
                         kind='move' if 1 <= index <= len(moves()) else 'auxiliary', params=sorted(params)))
    assert len(positive) == len(moves()) + 3
    return rows


def configurations():
    if CUSTOM_CONFIGURATIONS:
        return json.loads(CUSTOM_CONFIGURATIONS.read_text())
    paths = [('production', CAMPAIGN / 'baseline', 'pokecrystal-dex-moves-mode'),
             ('prototype', SOURCE, 'pokecrystal-dex-types'),
             ('original-interrupts', INVESTIGATION / 'interrupts-original', 'pokecrystal')]
    return [dict(variant=name, root=str(path / 'candidate'), rom=str(path / f'{stem}.gbc'),
                 sym=str(path / f'{stem}.sym'), battery=str(CAMPAIGN / 'legacy-input.sav'),
                 expected_double_speed=0, expected_battle_speed=0, fresh_battle_fixture=True)
            for name, path, stem in paths]


def compile_sweep(repo, target):
    labels = '''wBattleMode wBattleAnimParam wBattleAfterAnim hBattleTurn hROMBank hVBlank
    wBattleAnimAddress wBattleAnimDelay wActiveAnimObjects wBGEffect1 wShadowOAM hLCDCPointer
    wThrownBallWobbleCount wFinalCatchRate wWildMon'''.split()
    lines = []
    for name in labels:
        bank, pc = repo.symbols[name]
        lines += [f'#define SW_{name} {pc}', f'#define SWB_{name} {bank}']
    for name in ('Call_PlayBattleAnim', 'RunBattleAnimScript.done', 'BattleAnimationScriptsStart', 'LCD', 'VBlank'):
        bank, pc = repo.symbols[name]
        key = name.replace('.', '_')
        lines += [f'#define SW_{key} {pc}', f'#define SW_{key}_bank {bank}']
    lines.append(f'#define SW_ThrowPokeBall_id {next(e["id"] for e in catalogue() if e["label"]=="BattleAnim_ThrowPokeBall")}')
    header = target / 'sweep-symbols.h'
    header.write_text('\n'.join(lines) + '\n')
    sameboy = Path.home() / 'Documents/GitHub/SameBoy'
    executable = target / 'animation-sweep'
    subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="animation-sweep"',
                    f'-DSWEEP_SYMBOLS="{header.resolve()}"',
                    str(ROOT / 'tools/dex_timing/probes/battle_animation_sweep.c'),
                    *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(executable)], check=True)
    return executable


def prepare():
    prepared = []
    for config in configurations():
        motion.OUTPUT = OUTPUT / 'runtime/animation'
        motion.configuration = lambda _: config
        cfg = motion.prepare(config['variant'], moves(), 'all-moves', coherent=True)
        cfg.update(output_root=str(OUTPUT / 'native'), capture_images=False, post_menu_frames=32)
        repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
        target = OUTPUT / config['variant']
        target.mkdir(exist_ok=True)
        cfg['sweep_core'] = str(compile_sweep(repo, target))
        cfg['rom_sha256'] = sha256(repo.rom)
        cfg['sweep_output'] = str(OUTPUT)
        prepared.append(cfg)
        print(json.dumps(dict(prepared=config['variant'], moves=len(moves()), sha256=cfg['rom_sha256'])), flush=True)
    write(OUTPUT / 'configurations.json', prepared)
    write(OUTPUT / 'catalogue.json', catalogue())


def renderer_job(task):
    config, entry, phase = task
    target = Path(config.get('sweep_output', OUTPUT)) / 'renderer' / config['variant']
    target.mkdir(parents=True, exist_ok=True)
    commands = [(side, param) for side in (0, 1) for param in entry['params']]
    inputs = ''.join(f'{config["fixtures"]["POUND"]["player"]} {entry["id"]} {side} {param} {phase}\n'
                     for side, param in commands)
    result = subprocess.run([config['sweep_core'], config['rom']], input=inputs,
                            text=True, capture_output=True, timeout=240)
    rows = [dict(json.loads(line), variant=config['variant'], name=entry['name'], label=entry['label'], kind=entry['kind'])
            for line in result.stdout.splitlines() if line.startswith('{')]
    assert result.returncode == 0 and len(rows) == len(commands), (entry, result.returncode, result.stderr[-2000:])
    write(target / f'{entry["id"]}-q{phase}.json', rows)
    return rows


def renderer(jobs, smoke):
    configs = json.loads((OUTPUT / 'configurations.json').read_text())
    entries = catalogue()
    if smoke:
        entries = [e for e in entries if e['name'] in ('POUND', 'WATERFALL', 'WATER_PULSE', 'SURF', 'FLY', 'FOCUS_PUNCH', 'MIRROR_COAT')]
    tasks = [(cfg, entry, phase) for cfg in configs for entry in entries for phase in PHASES]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for i, batch in enumerate(pool.map(renderer_job, tasks), 1):
            rows.extend(batch)
            if i % 100 == 0 or i == len(tasks):
                print(json.dumps(dict(done=i, total=len(tasks), calls=len(rows))), flush=True)
    write(OUTPUT / ('renderer-smoke.json' if smoke else 'renderer.json'), rows)
    failures = [r for r in rows if not all(r[n] for n in ('returned', 'wram_restored', 'speed_restored', 'vblank_restored', 'rom_restored'))]
    print(json.dumps(dict(cases=len(rows), restoration_failures=len(failures))), flush=True)
    if failures:
        write(OUTPUT / 'renderer-failures.json', failures)


def capture_rerun(jobs):
    configs=json.loads((OUTPUT / 'configurations.json').read_text())
    entry=next(e for e in catalogue() if e['label']=='BattleAnim_ThrowPokeBall')
    tasks=[(cfg,entry,phase) for cfg in configs for phase in PHASES]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        replacements=[r for batch in pool.map(renderer_job,tasks) for r in batch]
    original=json.loads((OUTPUT / 'renderer.json').read_text())
    write(OUTPUT / 'capture-uninitialized-fixture.json',[r for r in original if r['id']==entry['id']])
    write(OUTPUT / 'renderer.json',[r for r in original if r['id']!=entry['id']]+replacements)
    print(json.dumps(dict(capture_cases=len(replacements),corrected_catch_context=True)),flush=True)


def native(jobs):
    configs = json.loads((OUTPUT / 'configurations.json').read_text())
    if not CUSTOM_CONFIGURATIONS:
        configs = configs[:2]
    values = constants(ROOT / 'constants/move_constants.asm')
    tasks = [(cfg, move, values[move], side, 0) for cfg in configs for move in moves() for side in ('player', 'foe')]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for i, row in enumerate(pool.map(speed.move_job, tasks), 1):
            rows.append(row)
            if i % 100 == 0 or row['issues']:
                print(json.dumps(dict(done=i, total=len(tasks), variant=row['variant'], move=row['move'], side=row['side'], issues=row['issues'])), flush=True)
    write(OUTPUT / 'native.json', rows)
    print(json.dumps(dict(cases=len(rows), cases_with_issues=sum(bool(r['issues']) for r in rows))), flush=True)


def native_edges():
    rows=json.loads((OUTPUT / 'native.json').read_text())
    edges=[]
    for row in rows:
        if not row['issues']: continue
        path=OUTPUT / 'native' / row['variant'] / f'{row["move"].lower()}-{row["side"]}-q0' / 'events.jsonl.gz'
        with gzip.open(path,'rt') as stream:
            events=[json.loads(line) for line in stream]
        starts=[e for e in events if e['event']=='perf_phase' and e['name']=='battle_anim'
                and e['anim_id']==row['index'] and e['turn']==int(row['side']=='foe')]
        returns={e['t'] for e in events if e['event']=='perf_cost' and e['name']=='battle_anim'}
        edges.append(dict(variant=row['variant'],move=row['move'],side=row['side'],
            issues=[s.split(': {')[0] for s in row['issues']], starts=len(starts),
            returned=sum(e['t'] in returns for e in starts)))
    write(OUTPUT / 'native-edge-events.json',edges)
    print(json.dumps(edges,indent=2),flush=True)


def summarize_comparisons(rows):
    changed = {r['name'] for r in rows if abs(r['delta_frames']) > 1}
    return dict(cases=len(rows), over_one_frame=sum(abs(r['delta_frames']) > 1 for r in rows),
        affected_names=len(changed), affected_name_list=sorted(changed),
        slower_over_one_frame=sum(r['delta_frames'] > 1 for r in rows),
        faster_over_one_frame=sum(r['delta_frames'] < -1 for r in rows),
        minimum=min(r['delta_frames'] for r in rows), maximum=max(r['delta_frames'] for r in rows),
        median=statistics.median(r['delta_frames'] for r in rows),
        logical_differences=sum(not r['logical_equal'] for r in rows),
        update_count_differences=sum(r['old_updates'] != r['updates'] for r in rows),
        return_differences=sum(r['returned'] != r['old_returned'] for r in rows))


def report():
    rows = json.loads((OUTPUT / 'renderer.json').read_text())
    by = {(r['variant'], r['id'], r['side'], r['param'], r['phase']): r for r in rows}
    expected = {(cfg['variant'], e['id'], side, param, phase)
                for cfg in configurations() for e in catalogue()
                for side in (0, 1) for param in e['params'] for phase in PHASES}
    coverage = dict(expected_calls=len(expected), actual_calls=len(rows),
        missing_cases=len(expected - by.keys()), unexpected_cases=len(by.keys() - expected),
        duplicate_cases=len(rows) - len(by))
    restoration_failures = [r for r in rows if not all(r[n] for n in
        ('returned', 'wram_restored', 'speed_restored', 'vblank_restored', 'rom_restored'))]
    comparisons = []
    for r in rows:
        if r['variant'] == 'production':
            continue
        old = by['production', r['id'], r['side'], r['param'], r['phase']]
        comparisons.append(dict(variant=r['variant'], name=r['name'], kind=r['kind'], side=r['side'],
            param=r['param'], phase=r['phase'], delta_frames=(r['elapsed_t']-old['elapsed_t'])/FRAME,
            delta_ms=(r['elapsed_t']-old['elapsed_t'])*1000/4194304,
            old_frames=old['elapsed_t']/FRAME, frames=r['elapsed_t']/FRAME,
            old_updates=old['updates'], updates=r['updates'], logical_equal=r['logical_hash']==old['logical_hash'],
            pixels_equal=(r['pixel_hash']==old['pixel_hash'] and r['full_pixel_frames']==old['full_pixel_frames']
                          if 'pixel_hash' in r and 'pixel_hash' in old else None),
            old_intervals=old['intervals'], intervals=r['intervals'], lcd_active_updates=r['lcd_active_updates'],
            returned=r['returned'], old_returned=old['returned']))
    variants = tuple(cfg['variant'] for cfg in configurations() if cfg['variant'] != 'production')
    summaries = {v: summarize_comparisons([r for r in comparisons if r['variant'] == v]) for v in variants}
    move_summaries = {v: summarize_comparisons([r for r in comparisons if r['variant'] == v and r['kind'] == 'move'])
                      for v in variants}
    per_move = []
    for variant in variants if CUSTOM_CONFIGURATIONS else ('prototype',):
        for move in moves():
            selected = [r for r in comparisons if r['variant'] == variant and r['name'] == move and r['kind'] == 'move']
            peak = max(selected, key=lambda r: r['delta_frames'])
            per_move.append(dict(variant=variant,move=move, **summarize_comparisons(selected), worst_ms=peak['delta_ms'],
                                 worst_side=peak['side'], worst_phase=peak['phase']))
    result = dict(rom_sha256s={c['variant']:c['rom_sha256'] for c in json.loads((OUTPUT / 'configurations.json').read_text())},
        catalogue_entries=len(catalogue()), moves=len(moves()), renderer_calls=len(rows),
        coverage=coverage, restoration_failures=restoration_failures, summaries=summaries,
        move_summaries=move_summaries, per_move=per_move, comparisons=comparisons)
    native_path = OUTPUT / 'native.json'
    if native_path.exists():
        nrows = json.loads(native_path.read_text())
        nby = {(r['variant'],r['move'],r['side']):r for r in nrows}
        nexpected = {(cfg['variant'],move,side) for cfg in configurations()
                     for move in moves() for side in ('player','foe')
                     if CUSTOM_CONFIGURATIONS or cfg['variant'] in ('production','prototype')}
        ncoverage = dict(expected_cases=len(nexpected),actual_cases=len(nrows),
            missing_cases=len(nexpected-nby.keys()),unexpected_cases=len(nby.keys()-nexpected),
            duplicate_cases=len(nrows)-len(nby))
        ncomp = []
        for r in nrows:
            if r['variant'] == 'production': continue
            a=nby['production',r['move'],r['side']]
            ncomp.append(dict(variant=r['variant'],move=r['move'],side=r['side'],production_issues=a['issues'],prototype_issues=r['issues'],
                same_issue=[s.split(': {')[0] for s in a['issues']]==[s.split(': {')[0] for s in r['issues']],
                played=bool(r.get('requested_animations')) and bool(a.get('requested_animations')),
                delta_frames=((r['requested_animations'][0]['elapsed_t']-a['requested_animations'][0]['elapsed_t'])/FRAME
                    if r.get('requested_animations') and a.get('requested_animations') and
                    r['requested_animations'][0]['elapsed_t'] is not None and a['requested_animations'][0]['elapsed_t'] is not None else None)))
        result['native'] = dict(cases=len(nrows), coverage=ncoverage, comparisons=ncomp,
            failures=[r for r in ncomp if r['production_issues'] or r['prototype_issues']])
        result['native']['summary'] = dict(paired_cases=len(ncomp), clean_pairs=sum(not r['production_issues'] and
            not r['prototype_issues'] for r in ncomp), differing_issue_pairs=sum(not r['same_issue'] for r in ncomp))
    result['qualification'] = dict(complete_coverage=not any(coverage[k] for k in
        ('missing_cases', 'unexpected_cases', 'duplicate_cases')), restoration_passed=not restoration_failures,
        logical_sequence_passed=all(not s['logical_differences'] and not s['update_count_differences'] for s in summaries.values()),
        original_interrupt_timing_exact=(all(r['delta_frames'] == 0 for r in comparisons if r['variant'] == 'original-interrupts')
                                         if 'original-interrupts' in summaries else None),
        prototype_timing_unchanged=(not summaries['prototype']['over_one_frame'] if 'prototype' in summaries else None),
        all_variant_timing_exact=all(r['delta_frames'] == 0 for r in comparisons))
    result['qualification']['visual_sequence_passed'] = all(r['pixels_equal'] is True for r in comparisons)
    native_record = result.get('native',{})
    result['qualification']['native_coverage_passed'] = bool(native_record) and not any(
        native_record['coverage'][key] for key in ('missing_cases','unexpected_cases','duplicate_cases'))
    result['qualification']['native_issue_identities_match'] = bool(native_record) and native_record['summary']['differing_issue_pairs']==0
    write(OUTPUT / 'report.json', result)
    print(json.dumps(dict(coverage=coverage, qualification=result['qualification'],
        summaries={v:{k:x for k,x in s.items() if k != 'affected_name_list'} for v,s in summaries.items()},
        move_summaries={v:{k:x for k,x in s.items() if k != 'affected_name_list'} for v,s in move_summaries.items()},
        native_summary=result.get('native', {}).get('summary')),indent=2),flush=True)
    required = ['complete_coverage', 'restoration_passed', 'logical_sequence_passed',
                'all_variant_timing_exact' if CUSTOM_CONFIGURATIONS else 'original_interrupt_timing_exact']
    if CUSTOM_CONFIGURATIONS:
        required += ['visual_sequence_passed','native_coverage_passed','native_issue_identities_match']
    assert all(result['qualification'][k] for k in required), result['qualification']


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','compile','renderer','smoke','native','edges','capture','report'))
    parser.add_argument('--jobs',type=int,default=8)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--configurations',type=Path)
    args=parser.parse_args()
    OUTPUT = args.output.resolve()
    CUSTOM_CONFIGURATIONS = args.configurations.resolve() if args.configurations else None
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if args.action=='prepare': prepare()
    elif args.action=='compile':
        for config in json.loads((OUTPUT / 'configurations.json').read_text()):
            repo=Repository(Path(config['root']),Path(config['rom']),Path(config['sym']))
            compile_sweep(repo,OUTPUT / config['variant'])
    elif args.action in ('renderer','smoke'): renderer(args.jobs,args.action=='smoke')
    elif args.action=='native': native(args.jobs)
    elif args.action=='edges': native_edges()
    elif args.action=='capture': capture_rerun(args.jobs)
    else: report()
