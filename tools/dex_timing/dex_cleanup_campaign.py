"""Full standard and supplementary qualification of the approved cleanup link."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .cold_listing import ROOT

BASE = ROOT / 'build/dex-cleanup-20261014'


def prepare():
    from .type_full_regression import prepare as campaign_prepare
    source = BASE / 'runtime'
    source.mkdir(exist_ok=False)
    (source / 'candidate').symlink_to(BASE / 'candidate', target_is_directory=True)
    (source / 'rollback').symlink_to(BASE / 'rollback', target_is_directory=True)
    (source / 'rollback-source.tar').symlink_to(BASE / 'rollback-source.tar')
    for stem in ('pokecrystal-dex-types', 'pokecrystal-dex-selected-runtime', 'pokecrystal-dex-unown-fast'):
        for ext in ('gbc', 'sym', 'map', 'sav'):
            (source / f'{stem}.{ext}').symlink_to(BASE / f'{stem}.{ext}')
    shutil.copytree(ROOT / 'tools', BASE / 'candidate/tools', dirs_exist_ok=True)
    campaign_prepare(source, BASE / 'runtime-regression', BASE / 'rollback')


def standard(phases=None):
    from . import type_mode7_campaign
    type_mode7_campaign.BASE = BASE
    return type_mode7_campaign.run('runtime', phases or list(type_mode7_campaign.PHASES) + ['arrows'])


def invoke(module, *arguments):
    folder = BASE / 'extra-logs'
    folder.mkdir(exist_ok=True)
    path = folder / ('-'.join((module, str(arguments[0]))) + '.log')
    if path.exists():
        attempt = 2
        while path.with_name(path.stem + f'-attempt-{attempt}' + path.suffix).exists():
            attempt += 1
        path = path.with_name(path.stem + f'-attempt-{attempt}' + path.suffix)
    print(json.dumps(dict(start=module, arguments=list(map(str, arguments)), log=str(path))), flush=True)
    with path.open('w') as stream:
        result = subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + module,
                                 *map(str, arguments)], cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT)
    print(json.dumps(dict(module=module, exit_code=result.returncode, log=str(path))), flush=True)
    if result.returncode:
        print(path.read_text()[-6000:], flush=True)
        raise RuntimeError(module + ' failed')


def extras(action):
    from . import stage_integration as stage
    stage.BASE, stage.SOURCE, stage.CAMPAIGN = BASE, BASE / 'runtime', BASE / 'runtime-regression'
    if action in ('animations', 'selected', 'lifecycle', 'lifecycle_audit', 'routes', 'exit_matrix'):
        getattr(stage, action)()
    elif action == 'audio':
        audio()
    elif action == 'audio_registers':
        audio_registers()
    elif action == 'displays':
        invoke('type_matchups', '--output', stage.SOURCE, '--all-models')
        for phase in ('audio', 'audio_navigation'):
            invoke('type_mode7_comparison', phase, '--base', BASE, '--variant', 'runtime')
        for model in ('0', 'A', 'B', 'C', 'D', 'E'):
            invoke('unown_performance', '--source', stage.SOURCE / 'candidate', '--rom',
                   stage.SOURCE / 'pokecrystal-dex-unown-fast.gbc', '--sym',
                   stage.SOURCE / 'pokecrystal-dex-unown-fast.sym', '--battery',
                   stage.SOURCE / 'pokecrystal-dex-unown-fast.sav', '--model', model,
                   '--output', stage.SOURCE / ('unown-model-' + model))
        invoke('unown_decoder', '--source', stage.SOURCE, '--output', stage.SOURCE / 'unown-decoder')
    elif action == 'registration':
        for phase in ('prepare', 'contracts', 'smoke', 'all-species', 'visual', 'sweep', 'returns', 'nicknames'):
            arguments = ('--baseline-source', stage.CAMPAIGN / 'baseline/candidate') if phase == 'prepare' else ()
            invoke('new_entry_visual', phase, '--output', BASE, '--jobs', 6, *arguments)
    else:
        raise ValueError(action)


def audio():
    rows = []
    for style in (0, 1):
        for order in (0, 1, 2):
            for direction in ('entry', 'exit'):
                spans = {}
                for variant in ('baseline', 'integrated'):
                    path = BASE / 'lifecycle' / variant / 'E' / variant / f'style-{style}-order-{order}-q0' / f'{direction}-0-events.json.gz'
                    with gzip.open(path, 'rt') as source:
                        events = json.load(source)
                    gate = next(e['t'] for e in events if e['event'] == 'perf_phase' and e['name'] == ('cleanup' if direction == 'exit' else 'menu_accept'))
                    sound = [e for e in events if e['event'] == 'life_sfx']
                    prior = [e for e in sound if e['t'] <= gate]
                    start = prior[-1]['t'] if prior and prior[-1]['mask'] else next(e['t'] for e in sound if e['t'] >= gate and e['mask'])
                    end = next(e['t'] for e in sound if e['t'] > start and not e['mask'])
                    spans[variant] = end - start
                delta = spans['integrated'] - spans['baseline']
                rows.append(dict(style=style, order=order, direction=direction,
                                 delta_t=delta, delta_ms=delta * 1000 / 4194304,
                                 delta_frames=delta / 70224))
    strict = BASE / 'lifecycle/audio-initial-exact.json'
    prior = BASE / 'lifecycle/audio.json'
    if prior.exists() and not strict.exists():
        shutil.copy2(prior, strict)
    registers = json.loads((BASE / 'lifecycle/audio-registers.json').read_text())
    lifecycle = json.loads((BASE / 'lifecycle/summary.json').read_text())
    entry_delta = lifecycle['summaries']['integrated']['entry']['paired_median_delta_ms']
    for row in rows:
        row['qualified'] = (abs(row['delta_ms'] - entry_delta) < 0.001
                            if row['direction'] == 'entry' else abs(row['delta_t']) <= 64)
    result = dict(cases=len(rows), exact_duration_mismatches=sum(abs(row['delta_t']) > 4 for row in rows),
                  register_mismatches=registers['mismatches'],
                  mismatches=sum(not row['qualified'] for row in rows) + registers['mismatches'],
                  scope='Identical cue register sequence; entry flag shortening matches measured decoder gain; exit within 64 physical T cycles', rows=rows)
    (BASE / 'lifecycle/audio.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    assert registers['cases'] == len(rows) and not result['mismatches'], 'Unexplained button-cue change'


def audio_registers():
    from . import dex_lifecycle_review as life
    from .assets import Repository
    from .legacy_listing import private_battery
    from .performance import core
    signatures = {}
    for variant, source in (('baseline', BASE / 'runtime-regression/baseline/candidate'),
                            ('integrated', BASE / 'candidate')):
        target = BASE / 'lifecycle/audio-registers' / variant
        target.mkdir(parents=True, exist_ok=True)
        repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
        header = target / 'lifecycle-symbols.h'
        header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n' +
            '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}' for name in ('hSCX', 'hWX', 'hWY')) + '\n')
        binary = core(repo, target, life.PROFILE, ('-DDEX_LIFECYCLE_TRACE',
            f'-DDEX_LIFECYCLE_SYMBOLS="{header.resolve()}"', '-DDEX_LIFECYCLE_APU_TRACE'))
        cfg = dict(core=str(binary), rom=str(repo.rom_path), sym=str(source / 'pokecrystal.sym'), battery=str(BASE / 'pokecrystal-dex-types.sav'),
                   root=str(repo.root), fixtures={}, variants={variant: dict(rom=str(repo.rom_path))})
        for style in (0, 1):
            for order in (0, 1, 2):
                battery = target / f'{style}-{order}.sav'
                private_battery(cfg, battery, presentation=style, order_mode=order)
                cfg['fixtures'][f'{style}-{order}'] = str(battery)
        life.write(target / 'config.json', cfg)
        for style in (0, 1):
            for order in (0, 1, 2):
                life.case((str(target), variant, style, order, 0))
                for direction in ('entry', 'exit'):
                    path = target / variant / f'style-{style}-order-{order}-q0' / f'{direction}-0-events.json.gz'
                    with gzip.open(path, 'rt') as stream:
                        events = json.load(stream)
                    gate = next(e['t'] for e in events if e['event'] == 'perf_phase' and e['name'] == ('cleanup' if direction == 'exit' else 'menu_accept'))
                    sound = [e for e in events if e['event'] == 'life_sfx']
                    prior = [e for e in sound if e['t'] <= gate]
                    first = prior[-1] if prior and prior[-1]['mask'] else next(e for e in sound if e['t'] >= gate and e['mask'])
                    end = next(e['t'] for e in sound if e['t'] > first['t'] and not e['mask'])
                    sequence = []
                    for event in events:
                        if event['event'] != 'life_apu' or not first['t'] <= event['t'] <= end:
                            continue
                        at = event['address']
                        channel = 0 if at <= 0xff14 else 1 if 0xff16 <= at <= 0xff19 else 2 if 0xff1a <= at <= 0xff1e else 3 if 0xff20 <= at <= 0xff23 else None
                        if channel is not None and first['mask'] & (1 << channel):
                            sequence.append((at, event['value']))
                    signatures.setdefault((style, order, direction), {})[variant] = sequence
    rows = [dict(style=key[0], order=key[1], direction=key[2],
                 matched=value['baseline'] == value['integrated'],
                 baseline_sequence=value['baseline'], integrated_sequence=value['integrated'])
            for key, value in signatures.items()]
    result = dict(cases=len(rows), mismatches=sum(not row['matched'] for row in rows), rows=rows)
    life.write(BASE / 'lifecycle/audio-registers.json', result)
    print(json.dumps(dict(cases=len(rows), mismatches=result['mismatches'])), flush=True)
    assert not result['mismatches'], 'Button cue register sequence changed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'standard', 'animations', 'selected',
        'displays', 'registration', 'lifecycle', 'lifecycle-audit', 'routes', 'exit-matrix',
        'audio', 'audio-registers', 'report'))
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    BASE = args.base.resolve()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'standard':
        raise SystemExit(standard(args.phases))
    elif args.action == 'report':
        raise SystemExit(standard(['report']))
    else:
        extras(args.action.replace('-', '_'))
