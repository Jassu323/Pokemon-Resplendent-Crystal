"""Fresh normal-input catches and generated-species qualification of registration."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from . import performance_audio as audio
from .assets import Repository
from .cold_listing import ROOT, expected_picture
from .new_entry import compile_core, run, audit_publication, audit_resident_layout, audit_description_publication
from .new_entry_sweep import cases, run_case, audit
from .shared_new_entry_regression import prepare as prepare_sweep


def prepare(output, baseline_source=ROOT):
    configs = {}
    prior = audio.SPECIES
    audio.SPECIES = ('caterpie', 'dusknoir')
    try:
        for variant, root in (('baseline', baseline_source), ('candidate', output / 'candidate')):
            folder = output / 'native' / variant
            config = dict(variant=variant, root=str(root), rom=str(root / 'pokecrystal.gbc'),
                          sym=str(root / 'pokecrystal.sym'), expected_double_speed=0,
                          battery=str(ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'))
            local = audio.prepare(config, folder, 0, 0)
            catches = [audio.execute((local, name, 'catch')) for name in audio.SPECIES]
            assert not any(r['issues'] for r in catches), catches
            configs[variant] = dict(root=str(root), donor=str(folder / 'caterpie-catch/registration.s0'),
                                    catches=catches)
            print(json.dumps(dict(variant=variant, native_catches=len(catches))), flush=True)
    finally:
        audio.SPECIES = prior
    (output / 'native-config.json').write_text(json.dumps(configs, indent=2) + '\n')


def smoke(output):
    configs = json.loads((output / 'native-config.json').read_text())
    rows = []
    for variant, old in configs.items():
        root, donor = Path(old['root']), Path(old['donor'])
        target = output / 'smoke' / variant
        config, assets, report = prepare_sweep(root, donor, target, Path.home() / 'Documents/GitHub/SameBoy')
        for name in sorted(assets, key=lambda n: (n not in ('caterpie', 'dusknoir'), n)):
            asset = assets[name]
            for mode in (0, 1, 2):
                prefix = target / f'{name}-{mode}'
                trace = run(Path(config['binary']), [config['rom'], config['states'][name],
                    config['references'][name], mode], prefix, screens=name in ('caterpie', 'dusknoir'))
                row = dict(variant=variant, mode=mode, **audit(asset, trace,
                    dict(name='smoke-' + str(mode), family='smoke')))
                assert row['status'] == 'pass', row
                rows.append(row)
                print(json.dumps(dict(variant=variant, species=name, mode=mode, status='pass')), flush=True)
        (target / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    (output / 'smoke-summary.json').write_text(json.dumps(dict(cases=len(rows), results=rows), indent=2) + '\n')


def sweep(output, jobs):
    configs = json.loads((output / 'native-config.json').read_text())
    old = configs['candidate']
    target = output / 'sweep'
    config, assets, report = prepare_sweep(Path(old['root']), Path(old['donor']), target,
                                         Path.home() / 'Documents/GitHub/SameBoy')
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        starts = [(config, asset, cases(0, 0)[0]) for asset in assets.values()]
        baselines = list(pool.map(run_case, starts))
        assert all(r['status'] == 'pass' for r in baselines), baselines
        rows.extend(baselines)
        work = [(config, assets[row['species']], case) for row in baselines
                for case in cases(row['authored_intervals'], row['first_publication'])
                if case['family'] != 'baseline']
        for i, row in enumerate(pool.map(run_case, work), 1):
            rows.append(row)
            if i % 250 == 0 or row['status'] != 'pass':
                print(json.dumps(dict(done=i, total=len(work), errors=row['errors'][:1])), flush=True)
    record = dict(cases=len(rows), failures=sum(r['status'] != 'pass' for r in rows), results=rows)
    (target / 'summary.json').write_text(json.dumps(record, indent=2) + '\n')
    assert not record['failures'], record['failures']
    print(json.dumps(dict(cases=len(rows), failures=0)), flush=True)


def all_species(output, jobs):
    old = json.loads((output / 'native-config.json').read_text())['candidate']
    root = Path(old['root'])
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    target = output / 'all-species'
    target.mkdir(exist_ok=True)
    binary = compile_core(repo, Path.home() / 'Documents/GitHub/SameBoy', target, 'trace')
    factory = compile_core(repo, Path.home() / 'Documents/GitHub/SameBoy', target, 'fixture')
    assets = repo.load()
    # Form A covers Unown's entry path; other forms are covered by structural frame mapping.
    from .performance import names
    order = names()
    assets = [a for a in assets if a.name in order]
    assert len(assets) == len(order) == 373, (len(assets), len(order))
    from .assets import offset
    at = offset(repo.symbols['NewPokedexOrder'])
    config = dict(rom=str(repo.rom_path), sym=str(root / 'pokecrystal.sym'), root=str(root),
                  binary=str(binary), output=str(target), states={}, references={}, registration_visual=True)
    for asset in assets:
        n = order.index(asset.name)
        index = int.from_bytes(repo.rom[at+2*n:at+2*n+2], 'little')
        state, refs = target / (asset.name + '.s0'), target / (asset.name + '.references')
        subprocess.run([str(factory), str(repo.rom_path), old['donor'], str(index), str(state)],
                       check=True, capture_output=True)
        refs.write_bytes(bytes([len(asset.plans)]) + b''.join(expected_picture(asset, n) for n in range(len(asset.plans))))
        config['states'][asset.name], config['references'][asset.name] = str(state), str(refs)
    work = [(config, asset, case) for asset in assets for case in
            (cases(0, 0)[0], dict(name='page-and-return', family='exit', windows=[(1, 5, 2, 16), (2, 8, 2, 32)]))]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(run_case, work))
    record = dict(cases=len(rows), species=len(assets), failures=sum(r['status'] != 'pass' for r in rows),
                  structural=audit_resident_layout(repo), publication=audit_publication(repo),
                  description_publication=audit_description_publication(repo),
                  visual_snapshots=sum(r.get('visual_snapshots', 0) for r in rows), results=rows)
    (target / 'summary.json').write_text(json.dumps(record, indent=2) + '\n')
    assert not record['failures'], [r for r in rows if r['status'] != 'pass'][:3]
    print(json.dumps({k:v for k,v in record.items() if k != 'results'}), flush=True)


def audit_visual_snapshot(repo, name, ui):
    from .description_ui import linked, expected_types, audit_type_sprites, audit_footprint
    issues = audit_type_sprites(repo, ui) + audit_footprint(repo, name, ui)
    if ui['types'] != expected_types(repo, name):
        issues.append('wrong_types')
    tilemap, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    shell, edge = linked(repo, 'PokedexDescriptionTilemap', 360), linked(repo, 'PokedexDescriptionRightEdge', 18)
    red_footer = 'NewDexEntry_RedFooterPalette' in repo.symbols
    for y in range(18):
        for x in range(21):
            if red_footer and y == 17:
                expected = (0x31, 0xee) if x == 18 else (0x31,)
                if tilemap[y * 21 + x] not in expected or attrs[y * 21 + x] != (3 if x == 18 else 0):
                    issues.append(f'red_footer_{x}')
                continue
            if not (y in (0, 8, 16) or x in (0, 20) or x == 8 and 1 <= y <= 7):
                continue
            value = edge[y] if x == 20 else shell[y * 20 + x]
            if (x, y) == (2, 8) and ui['page']:
                value = 0x79
            if tilemap[y * 21 + x] != value or attrs[y * 21 + x]:
                issues.append(f'shell_{x}_{y}')
    for x, y, d in ((18, 1, 0), (19, 1, 1), (18, 2, 2), (19, 2, 3)):
        if tilemap[y * 21 + x] != 0x62 + d or attrs[y * 21 + x] != 2:
            issues.append('footprint_storage')
    pals = bytes.fromhex(ui['palettes'])
    if pals[16:18] != bytes((255, 127)) or pals[22:24] != bytes((165, 20)):
        issues.append('footprint_palette')
    if red_footer:
        expected_palette = bytearray(linked(repo, 'PokedexUIPalette', 8))
        expected_palette[6:8] = expected_palette[2:4]
        if pals[24:32] != expected_palette:
            issues.append('red_footer_palette')
    return issues


def visual(output, jobs):
    old = json.loads((output / 'native-config.json').read_text())['candidate']
    root = Path(old['root'])
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    target = output / 'visual'
    config, assets, _ = prepare_sweep(root, Path(old['donor']), target,
                                    Path.home() / 'Documents/GitHub/SameBoy')
    record = []
    for name, asset in assets.items():
        prefix = target / name
        trace = run(Path(config['binary']), [config['rom'], config['states'][name],
                    config['references'][name], 1], prefix, screens=True)
        for ui in (e for e in trace if e['event'] == 'visual_snapshot'):
            issues = audit_visual_snapshot(repo, name, ui)
            if 'NewDexEntry_RedFooterPalette' in repo.symbols:
                from PIL import Image
                from .description_ui import linked
                from .type_matchups import rgb555
                red = rgb555(int.from_bytes(linked(repo, 'PokedexUIPalette', 8)[2:4], 'little'))
                with Image.open(target / f'{name}-{ui["name"]}.ppm') as image:
                    for y in range(136, 144):
                        for x in range(160):
                            allowed = (red, (255, 255, 255)) if 139 <= x < 147 else (red,)
                            if image.getpixel((x, y)) not in allowed:
                                issues.append(f'footer_pixel_{x}_{y}')
                record.append(dict(species=name, frame=ui['name'], page=ui['page'], issues=issues))
                continue
            record.append(dict(species=name, frame=ui['name'], page=ui['page'], issues=issues))
    result = dict(cases=len(record), failures=sum(bool(r['issues']) for r in record), results=record)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    assert not result['failures'], [r for r in record if r['issues']][:3]
    print(json.dumps(dict(cases=len(record),failures=0)),flush=True)


def returns(output):
    from . import global_gameplay as gameplay
    rows=[]
    for variant, root in (('baseline', ROOT), ('candidate', output / 'candidate')):
        config=dict(root=str(root), rom=str(root/'pokecrystal.gbc'), sym=str(root/'pokecrystal.sym'),
            battery=str(ROOT/'build/dex-moves-search-final-review-20261011/legacy-input.sav'),
            expected_double_speed=1, expected_battle_speed=0, audio_fixture_dir=str(output/'native'/variant))
        gameplay.BASE=output/'returns'
        gameplay.configuration=lambda v: config
        for kind in ('party-catch','pc-catch'):
            row=gameplay.scenario((variant,kind))
            rows.append(row)
            print(json.dumps(dict(variant=variant,scenario=kind,issues=row['issues'])),flush=True)
    (output/'returns-summary.json').write_text(json.dumps(dict(cases=len(rows),results=rows),indent=2)+'\n')
    assert not any(r['issues'] for r in rows),rows


def contracts(output):
    from tools import test_new_dex_entry
    rows = []
    for variant, root in (('baseline', ROOT), ('candidate', output / 'candidate')):
        test_new_dex_entry.ROOT = root
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_new_dex_entry)
        with (output / f'contracts-{variant}.log').open('w') as log:
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        row = dict(variant=variant, cases=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skipped=len(result.skipped))
        if variant == 'candidate' and 'NewDexEntry_RedFooterPalette' in test_new_dex_entry.RegistrationTests.repo.symbols:
            from .cpu import CounterCPU
            repo = test_new_dex_entry.RegistrationTests.repo
            bank, at = repo.symbols['wBGPals1']
            source = bytes(range(64))
            expected = bytearray(source)
            expected[24:32] = source[:8]
            expected[30:32] = source[2:4]
            for incoming in range(1, 8):
                cpu = CounterCPU(repo.rom, repo.symbols)
                cpu.field('wBGPals1', int.from_bytes(source, 'little'), len(source))
                cpu.write(0xff70, incoming)
                cpu.run('NewDexEntry_RedFooterPalette')
                assert cpu.ram[0xff70] == incoming
                assert cpu.wram[bank][at - 0xd000:at - 0xd000 + 64] == expected
            row['footer_palette_bank_cases'] = 7
        rows.append(row)
        assert result.wasSuccessful(), row
    (output / 'contracts-summary.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(rows), flush=True)


def nicknames(output):
    from . import global_gameplay as gameplay
    from . import shared_menu_regression as menu
    rows = []
    gameplay.BASE = output / 'nicknames'
    for variant, root in (('baseline', ROOT), ('candidate', output / 'candidate')):
        config = dict(root=str(root), rom=str(root / 'pokecrystal.gbc'), sym=str(root / 'pokecrystal.sym'),
                      battery=str(ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'))
        gameplay.configuration = lambda v: config
        for full_party in (False, True):
            kind = 'pc-nickname' if full_party else 'party-nickname'
            _, repo, folder, driver = gameplay.new_driver(variant, kind, ('ROUTE_30', 13, 49))
            try:
                driver.command(f'load {output / "native" / variant / "dusknoir-encounter.s0"}')
                gameplay.generated(driver, repo, folder, 'full-party' if full_party else 'discovery-empty')
                count = audio.value(driver, repo, 'wPartyCount')
                audio.until(driver, repo, 'BattleMenu.loop')
                menu.run(driver, repo, frames=40)
                menu.tap(driver, repo, 'down')
                audio.until(driver, repo, 'BattlePack.loop')
                for _ in range(10):
                    if audio.value(driver, repo, 'wCurPocket') == 1:
                        break
                    menu.tap(driver, repo, 'right', released=30)
                audio.until(driver, repo, 'NewPokedexEntry')
                audio.until(driver, repo, 'NewPokedexEntry.WaitPressAorB_AnimateFrontpic', key=None)
                menu.run(driver, repo, frames=240)
                audio.until(driver, repo, 'NewPokedexEntry.ReturnFromDexRegistration')
                audio.until(driver, repo, 'NamingScreen.loop')
                menu.run(driver, repo, frames=4)
                menu.tap(driver, repo, 'a')
                assert audio.value(driver, repo, 'wNamingScreenCurNameLength') == 1
                menu.tap(driver, repo, 'start')
                menu.tap(driver, repo, 'a')
                audio.until(driver, repo, 'PokeBallEffect.return_from_capture')
                label = 'wMonOrItemNameBuffer' if full_party else f'wPartyMon{count + 1}Nickname'
                name = audio.value(driver, repo, label, 2)
                assert name == 0x5080, (variant, kind, name)
                for _ in range(80):
                    menu.tap(driver, repo, 'b', released=40)
                    if not audio.value(driver, repo, 'wBattleMode'):
                        break
                assert audio.value(driver, repo, 'wBattleMode') == 0
                rows.append(dict(variant=variant, scenario=kind, nickname='A', issues=[]))
                print(json.dumps(rows[-1]), flush=True)
            finally:
                driver.close()
    (output / 'nicknames-summary.json').write_text(json.dumps(dict(cases=len(rows), results=rows), indent=2) + '\n')


def dex_prepare(output):
    from .type_full_regression import prepare as prepare_campaign
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(output / f'pokecrystal-dex-new-entry-visual.{ext}', output / f'pokecrystal-dex-types.{ext}')
    # Conventional aliases are private campaign inputs, not another game build.
    type_prepare(output)
    prepare_campaign(output, output / 'dex-campaign')
    print(json.dumps(dict(campaign=str(output / 'dex-campaign'))), flush=True)


def type_prepare(output):
    from .legacy_listing import private_battery
    stem = output / 'pokecrystal-dex-types'
    config = dict(rom=str(stem.with_suffix('.gbc')), sym=str(stem.with_suffix('.sym')),
                  battery=str(ROOT / 'build/dex-moves-search-final-review-20261011/all-seen-tests.sav'))
    private_battery(config, stem.with_suffix('.sav'), presentation=0, order_mode=0, unown_unlocked=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'smoke', 'sweep', 'all-species', 'visual', 'returns',
                                         'contracts', 'dex-prepare', 'nicknames', 'type-prepare'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--baseline-source', type=Path, default=ROOT)
    args = parser.parse_args()
    folder = args.output.resolve()
    if args.action == 'prepare':
        prepare(folder, args.baseline_source.resolve())
    elif args.action in ('sweep', 'all-species', 'visual'):
        globals()[args.action.replace('-', '_')](folder, args.jobs)
    else:
        globals()[args.action.replace('-', '_')](folder)
