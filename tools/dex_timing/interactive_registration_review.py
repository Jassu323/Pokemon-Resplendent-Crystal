"""Publish private interactive-registration ROM, save and manual-review media."""
import argparse
import gzip
import io
import json
from pathlib import Path
import shutil
import unittest
import wave

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT
from .shared_menu_regression import BOOT
from .shared_menu_fixtures import make_fixture

HZ = 4194304


def qualification(source, campaign, output, manifest, required, evidence=None):
    from .interactive_full_regression import check_inputs
    support_root = ROOT / 'build/interactive-registration-fixed-full-20261016'
    paths = dict(support=support_root / 'orchestration/audit.json',
        tabs=campaign / 'summary.json',
        evolution=ROOT / 'build/interactive-registration-fixed-evolution-20261016/report.json',
        contracts=source.parent / 'context-contracts.json',
        returns=ROOT / 'build/interactive-registration-fixed-returns-20261016/report.json',
        gc=ROOT / 'build/interactive-registration-fixed-returns-gc-20261016/report.json',
        payday=ROOT / 'build/interactive-registration-fixed-payday-v2-20261016/report.json',
        capture_delivery=support_root / 'delivery-proof.json',
        capture_comparison=support_root / 'comparison.json',
        capture_visual=support_root / 'visual-audit.json')
    paths.update(evidence or {})
    support_root = paths['support'].parent.parent
    reports = {key: json.loads(path.read_text()) for key, path in paths.items()}
    support, tabs, evolution, contracts = (reports[key] for key in ('support', 'tabs', 'evolution', 'contracts'))
    expected = manifest['rom_sha256']
    identities = [support['candidate_sha256'], tabs['rom_sha256'],
                  evolution['linked']['rom_sha256'], contracts['rom_sha256']]
    for key in ('returns', 'gc'):
        identities.extend(row['rom_sha256'] for row in reports[key]['results'])
    if set(identities) != {expected}:
        raise AssertionError('Qualification reports refer to different candidates')
    check_inputs(support_root)
    checks = dict(support=support['support_campaign_complete'] and support['no_new_failures'],
        tabs=tabs['complete'] and tabs['automated_suite_pass'] and tabs['displayed_completion_checks']['pass'],
        evolution=evolution['validation_pass'] and evolution['complete'] and
            evolution['linked']['passed'] and evolution['self_tests']['passed'],
        contracts=contracts['cases'] == manifest.get('context_contract_cases', 9) and
            not any(contracts[k] for k in ('failures', 'errors', 'skips')),
        returns=reports['returns']['cases'] == 10 and not reports['returns']['failures'],
        gc=reports['gc']['cases'] == 1 and not reports['gc']['failures'],
        resource_delta=manifest['delta'] == check_inputs(support_root)['resource_delta'])
    if 'payday' in reports:
        payday=reports['payday']
        expected_cases={(variant,coin,cap) for variant in ('production','candidate') for coin in (0,1) for cap in (0,1)}
        checks['payday'] = payday['cases'] == len(payday['results']) == 8 and not payday['failures'] and (
            {(row['variant'],row['coin'],row['capped']) for row in payday['results']} == expected_cases) and all(
            row.get('rom_sha256') == (expected if row['variant']=='candidate' else support['baseline_sha256'])
            for row in payday['results'])
    delivery=reports['capture_delivery']
    checks['capture_delivery']=(delivery['cases']==len(delivery['results'])==104 and
        not delivery['failures'] and all(row['passed'] and row['checks'] and all(row['checks'].values()) and
            row['rom_sha256']==(expected if row['variant']=='candidate' else support['baseline_sha256'])
            for row in delivery['results']))
    comparison=reports['capture_comparison']
    checks['capture_comparison']=(comparison['pairs']==52 and not comparison['mismatches'] and
        comparison['rom_hashes']==dict(production=support['baseline_sha256'],candidate=expected))
    visual=reports['capture_visual']
    checks['capture_visual']=(visual['rom_sha256']==expected and visual['cases']==2 and
        len(visual['results'])==2 and all(row['no_blank_scanout'] and row['mode3_stops']
                                       for row in visual['results']))
    import tools.test_capture_handoff as capture_tests
    capture_tests.SOURCE = source
    log = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromNames((
        'tools.test_battle_tower_suite', 'tools.test_interactive_registration_regression',
        'tools.test_capture_handoff'))
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (output / 'additional-host-tests.txt').write_text(log.getvalue())
    checks['harness_unit_tests'] = tests.testsRun == 36 and tests.wasSuccessful() and not tests.skipped
    passed = all(checks.values())
    if required and not passed:
        raise AssertionError('Incomplete automated qualification: ' + str(checks))
    record = dict(rom_sha256=expected, automated_qualification_pass=passed, checks=checks,
        reports={key: str(path) for key, path in paths.items()},
        additional_host_tests=tests.testsRun,
        protected_inputs_unchanged=True, production_integration=False,
        manual_visual_approval=False, manual_listening_approval=False, responsiveness_approval=False,
        responsiveness_alerts=tabs['responsiveness_alerts'], temporary_evolution_requirements=20,
        baseline_exceptions=support['baseline_exceptions'])
    (output / 'qualification.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def publish(source, campaign, output, required=False, evidence=None):
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Review artifacts must remain under build/')
    manifest = json.loads((source.parent / 'manifest.json').read_text())
    for name, expected in manifest['protected'].items():
        if sha256(Path(name).read_bytes()) != expected:
            raise AssertionError('Protected input changed: ' + name)
    if sha256((source / 'pokecrystal.gbc').read_bytes()) != manifest['rom_sha256']:
        raise AssertionError('Candidate no longer matches its build manifest')
    config = json.loads((campaign / 'config.json').read_text())
    for name, extension in (('rom_sha256', 'gbc'), ('sym_sha256', 'sym')):
        if config['hashes'][name] != sha256((source / ('pokecrystal.' + extension)).read_bytes()):
            raise AssertionError('Review evidence belongs to a different candidate: ' + name)
    output.mkdir(parents=True, exist_ok=True)
    stem = 'pokecrystal-interactive-registration'
    for extension in ('gbc', 'sym', 'map'):
        shutil.copy2(source / ('pokecrystal.' + extension), output / (stem + '.' + extension))
    comparison = output / 'regular-dex-comparison'
    comparison.mkdir(exist_ok=True)
    for extension in ('gbc', 'sym'):
        shutil.copy2(source / ('pokecrystal.' + extension), comparison / (stem + '.' + extension))
    shutil.copy2(campaign / 'selected.sav', comparison / (stem + '.sav'))
    repo = Repository(source, source / 'pokecrystal.gbc', source / 'pokecrystal.sym')
    # The seed's first four transient IDs are fixed by the qualified donor save.
    seed = ROOT / 'build/gotcha-boundary-final-20261015/review/pokecrystal-gotcha-boundary.sav'
    make_fixture(repo, seed, output / (stem + '.sav'), ('ROUTE_30', 13, 49), capture=True,
        extra_fields={'wPartyCount': bytes((4,)),
            'wPartySpecies': bytes((1, 2, 3, 4, 255, 6, 255)),
            'wPartyMon1Exp': (235).to_bytes(3, 'big'),
            'wPartyMon2Exp': (342).to_bytes(3, 'big'), 'wPartyMon2Item': bytes((0x39,))})
    battery_hash = sha256((output / (stem + '.sav')).read_bytes())
    driver = Driver(config['core'], output / (stem + '.gbc'), BOOT,
                    output / (stem + '.sav'), output / 'continue-check.log')
    try:
        for _ in range(180):
            state = driver.run(('continue', 'new_game', 'overworld'), 20, 'a')
            if state['hit'] == 'new_game':
                raise AssertionError('Review battery did not offer Continue')
            if state['hit'] == 'overworld':
                break
            driver.run(frames=10)
        else:
            raise AssertionError('Review battery did not reach the overworld')
        (output / 'continue-check.json').write_text(json.dumps(dict(
            reached_overworld=True, input='Normal Continue controls', state=state), indent=2) + '\n')
    finally:
        driver.close()
    assert sha256((output / (stem + '.sav')).read_bytes()) == battery_hash
    media = []
    for species in ('dusknoir', 'eevee', 'exeggcute', 'metagross'):
        video = campaign / 'manual-review' / (species + '-selected-v-registration.mp4')
        if video.is_file():
            target = output / video.name
            shutil.copy2(video, target)
            media.append(dict(path=str(target), kind='silent video',
                left='Regular Selected screen, same candidate ROM',
                right='New Entry registration, same candidate ROM',
                alignment='First complete Description; later actions auto-advance when each page is ready'))
        chunks, cues, parameters = [], [], None
        for owner in ('selected', 'registration'):
            folder = campaign / 'runs' / owner / species
            with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
                marks = [json.loads(line) for line in stream]
            cue = next((e['t'] for e in marks if e['event'] == 'perf_phase'
                        and e['name'] == 'sample_start'), None)
            if cue is None:
                cue = next(e['t'] for e in marks if e['event'] == 'interactive_phase'
                           and e['point'] == 'begin')
            with wave.open(str(folder / 'audio.wav'), 'rb') as sound:
                current = sound.getparams()[:3]
                if parameters is not None and parameters != current:
                    raise ValueError('A/B audio format mismatch')
                parameters = current
                start = max(0, round((cue / HZ - .08) * sound.getframerate()))
                sound.setpos(start)
                chunks.append(sound.readframes(round(3.2 * sound.getframerate())))
                cues.append(dict(owner=owner, event_t=cue, start_sample=start))
        path = output / (species + '-audio-selected-then-registration.wav')
        channels, width, rate = parameters
        with wave.open(str(path), 'wb') as sound:
            sound.setnchannels(channels)
            sound.setsampwidth(width)
            sound.setframerate(rate)
            sound.writeframes(chunks[0] + bytes(round(.7 * rate) * channels * width) + chunks[1])
        media.append(dict(path=str(path), kind='native stereo audio',
            order='Regular Selected, 0.7-second silence, registration', cues=cues,
            retimed=False, listening_approval=False))
    from PIL import Image, ImageDraw, ImageFont
    samples = (('eevee', 'desc-1', 'Description'), ('eevee', 'view1-page0', 'Stats'),
               ('eevee', 'view1-page1', 'Evolutions'),
               ('dusknoir', 'view1-page1', 'Evolves from'),
               ('metagross', 'tab-0-2', 'Moves'))
    sheet = Image.new('RGB', (1600, 704), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 16)
    for row, owner in enumerate(('selected', 'registration')):
        top = row * 352
        draw.text((8, top + 5), 'REGULAR SELECTED' if row == 0 else 'NEW REGISTRATION',
                  font=font, fill='white')
        for column, (species, page, label) in enumerate(samples):
            left = column * 320
            draw.text((left + 8, top + 31), species.title() + ': ' + label,
                      font=font, fill='white')
            with Image.open(campaign / 'runs' / owner / species / (page + '.png')) as picture:
                sheet.paste(picture.convert('RGB').resize((320, 288), Image.Resampling.NEAREST),
                            (left, top + 56))
    sheet_path = output / 'selected-versus-registration-panels.png'
    sheet.save(sheet_path)
    media.append(dict(path=str(sheet_path), kind='paired native screenshots',
                      source='Same candidate ROM; top regular Selected, bottom registration'))
    frames = sorted((campaign / 'runs/registration/dusknoir').glob('frame-*.ppm'))[:25]
    startup = Image.new('RGB', (1600, 5 * 320), (24, 24, 24))
    draw = ImageDraw.Draw(startup)
    for n, path in enumerate(frames):
        left, top = (n % 5) * 320, (n // 5) * 320
        draw.text((left + 6, top + 4), 'Native display ' + path.stem.rsplit('-', 1)[1],
                  font=font, fill='white')
        with Image.open(path) as picture:
            startup.paste(picture.convert('RGB').resize((320, 288), Image.Resampling.NEAREST),
                          (left, top + 28))
    startup_path = output / 'dusknoir-startup-first-25-displays.png'
    startup.save(startup_path)
    media.append(dict(path=str(startup_path), kind='native startup frame contact sheet',
                      source='Generated Dusknoir registration context, before first complete Description alignment'))
    for name in ('timing-tables.md', 'timing-tables.json', 'timing-tables.csv', 'summary.json'):
        shutil.copy2(campaign / name, output / name)
    support = (evidence or {}).get('support', ROOT / 'build/interactive-registration-fixed-full-20261016/orchestration/audit.json')
    if support.is_file():
        record = json.loads(support.read_text())
        if record['candidate_sha256'] != manifest['rom_sha256']:
            raise AssertionError('Support regression belongs to another candidate')
        shutil.copy2(support, output / 'support-regression-audit.json')
    capture = support.parent.parent / 'review'
    for name in ('party-name-production-vs-prototype.mp4',
                 'evolve-production-vs-prototype.mp4',
                 'capture-audio-production-then-prototype.wav',
                 'gotcha-first-12-frames.png',
                 'gotcha-fade-first-12-frames.png'):
        path = capture / name
        if path.is_file():
            target = output / name
            shutil.copy2(path, target)
            media.append(dict(path=str(target), kind='current production versus interactive capture evidence',
                alignment='Same executable Gotcha callback origin; real physical time',
                audio_order='Production, 0.7-second silence, prototype' if name.endswith('.wav') else None))
    qualified = qualification(source, campaign, output, manifest, required, evidence)
    receipt = dict(rom=str(output / (stem + '.gbc')), rom_sha256=manifest['rom_sha256'],
        source=str(source), campaign=str(campaign), delta=manifest['delta'],
        production_and_main_saves_unchanged=True,
        automated_qualification_pass=qualified['automated_qualification_pass'],
        qualification='qualification.json combines independent campaign gates; human approval remains pending',
        save='Private Route 30 copy; four Pokemon, 99 Master Balls; caught flags clear. '
             'Bulbasaur and Exp Share Caterpie are one EXP below level 7. Not the main save.',
        regular_dex_comparison=str(comparison / (stem + '.gbc')),
        comparison_save='Separate private all-373-seen/caught and all-Unown save from the native Selected controls.',
        media=media)
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'media'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
        default=ROOT / 'build/interactive-registration-fixed-full-20261016/candidate')
    parser.add_argument('--campaign', type=Path,
        default=ROOT / 'build/interactive-registration-fixed-tabs-20261016')
    parser.add_argument('--output', type=Path,
        default=ROOT / 'build/interactive-registration-review-20261016')
    parser.add_argument('--require-qualified', action='store_true')
    names=('support', 'evolution', 'contracts', 'returns', 'gc', 'payday',
           'capture_delivery', 'capture_comparison', 'capture_visual')
    for name in names:
        parser.add_argument('--'+name.replace('_','-')+'-report', type=Path)
    args = parser.parse_args()
    evidence={name:getattr(args,name+'_report').resolve() for name in names if getattr(args,name+'_report')}
    publish(args.source.resolve(), args.campaign.resolve(), args.output.resolve(), args.require_qualified, evidence)
