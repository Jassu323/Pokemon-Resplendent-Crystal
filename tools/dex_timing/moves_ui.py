"""Normal-input Moves correctness, playback and cancellation suite."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
from .assets import Repository, offset
from .cold_listing import ROOT, KEY, Driver, bootstrap, prepare_states, build_core, move, predecessor, audit
from .info_ui import BOOT, fixture, press, type_audit, ready as info_ready, info_audit
from .description_ui import settle, audit as description_audit, settle_description_text
from .description_paging import description_pages
from pokedex_info_assets import Compiler, species

def badge_audit(repo, ui, page):
    raw = bytes.fromhex(ui['lower_tiles'])
    def tile(row, col):
        at = ((row - 8) * 21 + col) * 16
        return raw[at:at + 16]
    label = 'PokedexBadgeSingleGFX' if page < 10 else 'PokedexBadgeDoubleGFX'
    column = page if page < 10 else (1 if page == 10 else page - 8)
    at = offset(repo.symbols[label]) + column * 32
    issues = []
    if tile(8, 2) + tile(9, 2) != repo.rom[at:at + 32]:
        issues.append('badge_pixels')
    if page >= 10:
        at = offset(repo.symbols['PokedexBadgePermanentGFX'])
        if tile(8, 3) + tile(9, 3) != repo.rom[at:at + 32]:
            issues.append('double_badge_closing_pixels')
    elif bytes.fromhex(ui['map'])[9 * 21 + 3] != 0x32:
        issues.append('stale_double_badge')
    return issues

def ready(driver, page=None):
    for _ in range(300):
        ui = driver.command('ui')
        if ui['view'] == 2 and not ui['moves_state'] and not ui['owner_transition'] and (page is None or ui['moves_page'] == page):
            driver.run(('animation_miss', 'audio_miss'), frames=1)
            return driver.command('ui')
        result = driver.run(('animation_miss', 'audio_miss'), frames=1)
        if result['hit']:
            raise RuntimeError('Playback miss while rendering Moves')
    raise RuntimeError('Moves page did not publish')

def content_audit(repo, name, page, ui, manifest):
    constant = {'unown_a': 'UNOWN', 'porygonz': 'PORYGON_Z'}.get(name, name.upper())
    data = manifest[constant]
    issues = badge_audit(repo, ui, page + 1) + type_audit(repo, name, ui)
    if ui['moves_pages'] != (max(1, len(data['pages'])) if ui['caught'] else 1):
        issues.append('move_page_count')
    if any(bytes.fromhex(ui['oam'])[32:64]):
        issues.append('stale_lower_oam')
    rows = [bytearray([0x32] * 32) for _ in range(7)]
    chars = Compiler().chars
    encode = lambda text: bytes(0x7f if c == ' ' else chars[c] for c in text)
    if ui['caught'] and data['pages']:
        kind, moves = data['pages'][page]
        heading = encode(('Level Up', 'TM/HM', 'Move Tutor', 'Breeding')[kind])
        rows[0][7:7 + len(heading)] = heading
        ids = __import__('pokedex_info_assets').constants(ROOT / 'constants/move_constants.asm')
        texts = re.findall(r'^\s*li "([^"]+)"', (ROOT / 'data/moves/names.asm').read_text(), re.M)
        for i, (value, move_name) in enumerate(moves):
            prefix = (bytes((0x7d,)) + encode(f'{value:02}') if kind == 0 else
                      encode(f'TM{value:02}' if value <= 50 else f'HM{value - 50:02}') if kind == 1 else
                      encode('Tut') if kind == 2 else encode('Egg'))
            rows[i + 2][2:2 + len(prefix)] = prefix
            move_text = encode(texts[ids[move_name] - 1])
            rows[i + 2][7:7 + len(move_text)] = move_text
    tilemap, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    for row in range(9, 16):
        for col in range(1, 20):
            if row == 9 and col in (1, 2, 3):
                continue
            if tilemap[row * 21 + col] != rows[row - 9][col] or attrs[row * 21 + col]:
                issues.append(f'content_{row}_{col}')
    level = (ROOT / 'build/dex-moves-assets/level.2bpp').read_bytes()
    if ui['caught'] and data['pages'] and data['pages'][page][0] == 0:
        raw = bytes.fromhex(ui['lower_tiles'])
        at = (3 * 21 + 2) * 16
        if raw[at:at + 16] != level:
            issues.append('level_glyph_pixels')
    return issues

def run_case(task):
    config, index, name, phase = task
    rom = Path(config.get('rom', ROOT / 'pokecrystal.gbc'))
    repo = Repository(ROOT, rom, Path(config.get('sym', ROOT / 'pokecrystal.sym')))
    manifest = json.loads((ROOT / 'build/dex-moves-assets/manifest.json').read_text())
    out = Path(config['output'])
    driver = Driver(config['core'], rom, BOOT, config['battery'], out / f'{name}-{phase}.log')
    issues, timings, pages, playback = [], [], [], []
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        if phase == 'settled':
            settle(driver)
        else:
            driver.run(('animation_miss', 'audio_miss'), frames=int(phase))
        press(driver, 'right')
        press(driver, 'right')
        start = driver.command('peek')['t']
        press(driver, 'a')
        ui = ready(driver, 0)
        timings.append((driver.command('peek')['t'] - start) / 70224)
        count = ui['moves_pages']
        for page in range(count):
            if page:
                start = driver.command('peek')['t']
                press(driver, 'a')
                ui = ready(driver, page)
                timings.append((driver.command('peek')['t'] - start) / 70224)
            issues += content_audit(repo, name, page, ui, manifest)
            pages.append(dict(page=page + 1, issues=issues[-20:]))
            if name in ('chikorita', 'mew', 'dusknoir') and page in (0, 8, 9, 10, count - 1):
                driver.command(f'image {out / f"{name}-{phase}-p{page + 1:02}.ppm"}')
        press(driver, 'a')
        ui = ready(driver, 0)
        wrap_issues = content_audit(repo, name, 0, ui, manifest)
        issues += ['wrap:' + issue for issue in wrap_issues]
        if wrap_issues:
            (out / f'{name}-{phase}-wrap.json').write_text(json.dumps(ui, indent=2))
        final = settle(driver)
        playback += audit(repo.load([name])[0], accepted, driver.events, final)['issues']
        target = index + 1 if index < 372 else index - 1
        driver.events.clear()
        accepted = driver.run(('change_species',), key='down' if target > index else 'up')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        ui = ready(driver, 0)
        target_name = config['names'][target]
        incoming_issues = content_audit(repo, target_name, 0, ui, manifest)
        issues += ['incoming:' + issue for issue in incoming_issues]
        if incoming_issues:
            (out / f'{name}-{phase}-incoming.json').write_text(json.dumps(ui, indent=2))
        if ui['footer_cursor'] != 2:
            issues.append('internal_footer')
        final = settle(driver)
        reveal = next(e['t'] for e in driver.events if e['event'] == 'reveal')
        playback += audit(repo.load([target_name])[0], accepted,
                          [e for e in driver.events if e['t'] >= reveal], final, cold=False)['issues']
        press(driver, 'left')
        press(driver, 'a')
        ui = info_ready(driver, 0)
        compiler = Compiler()
        info_issues = info_audit(compiler, compiler.compile(), target_name, 0, ui, repo)
        issues += ['info:' + issue for issue in info_issues]
        if info_issues:
            (out / f'{name}-{phase}-info.json').write_text(json.dumps(ui, indent=2))
        press(driver, 'left')
        press(driver, 'a')
        if ui['caught']:
            settle_description_text(driver, description_pages(repo, target_name)[0])
        else:
            driver.run(frames=60)
        description_ui = driver.command('ui')
        description_issues = description_audit(repo, description_ui)
        issues += description_issues
        if description_issues:
            (out / f'{name}-{phase}-description.json').write_text(json.dumps(description_ui, indent=2))
            driver.evidence(out / f'{name}-{phase}-description')
        driver.run(('leave',), key='b')
        result = driver.run(('listing',), frames=1200)
        if result['hit'] != 'listing':
            issues.append('listing_return')
        (out / f'{name}-{phase}.json').write_text(json.dumps(dict(issues=issues, pages=pages, playback=playback,
                timings=timings, events=driver.events), indent=2))
    except Exception as error:
        issues.append(str(error))
        driver.evidence(out / f'{name}-{phase}-failure')
    finally:
        driver.close()
    return dict(species=name, phase=phase, pages=len(pages), issues=sorted(set(issues + playback)), ready_frames=timings)

def run_stress(task):
    config, index, name, age, family = task
    rom = Path(config.get('rom', ROOT / 'pokecrystal.gbc'))
    repo = Repository(ROOT, rom, Path(config.get('sym', ROOT / 'pokecrystal.sym')))
    manifest = json.loads((ROOT / 'build/dex-moves-assets/manifest.json').read_text())
    out = Path(config['output'])
    label = f'{name}-{age}-{family}'
    driver = Driver(config['core'], rom, BOOT, config['battery'], out / f'{label}.log')
    issues, return_frames = [], None
    def select_footer(target):
        for _ in range(12):
            cursor = driver.command('ui')['footer_cursor']
            if cursor == target:
                driver.run(('selected', 'animation_miss', 'audio_miss'))
                return
            press(driver, 'right' if cursor < target else 'left')
            for _ in range(2):
                result = driver.run(('selected', 'animation_miss', 'audio_miss'))
                if result['hit'] != 'selected':
                    raise RuntimeError('Miss while selecting footer')
        raise RuntimeError('Footer selection was not accepted')
    def activate_footer():
        result = driver.run(('footer_accept', 'animation_miss', 'audio_miss'), key='a')
        if result['hit'] != 'footer_accept':
            raise RuntimeError('Footer activation was not accepted')
        result = driver.run(('selected', 'animation_miss', 'audio_miss'))
        if result['hit'] != 'selected':
            raise RuntimeError('Miss after footer activation')
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        move(driver, direction, index)
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'))
        select_footer(2)
        activate_footer()
        if age == 'settled':
            settle(driver)
        elif int(age):
            result = driver.run(('animation_miss', 'audio_miss'), frames=int(age))
            if result['hit']:
                raise RuntimeError('Playback miss before rapid input')
        if family == 'mash-a':
            for _ in range(12):
                press(driver, 'a')
        elif family == 'hold-a':
            result = driver.run(('animation_miss', 'audio_miss'), frames=60, key='a')
            if result['hit']:
                raise RuntimeError('Playback miss with held A')
            driver.run(frames=4)
        elif family in ('listing', 'a-b'):
            KEY['a-b'] = KEY['a'] | KEY['b']
            start = driver.command('peek')['t']
            left = driver.run(('leave',), key='b' if family == 'listing' else 'a-b')
            if left['hit'] != 'leave':
                raise RuntimeError('B did not cancel Moves')
            result = driver.run(('listing',), frames=1200)
            return_frames = (result['t'] - start) / 70224
            if result['hit'] != 'listing':
                issues.append('listing_cancel')
        elif family == 'description':
            select_footer(0)
            activate_footer()
            settle_description_text(driver, description_pages(repo, name)[0])
            ui = driver.command('ui')
            issues += description_audit(repo, ui) + type_audit(repo, name, ui)
            if ui['view'] or ui['moves_state'] or any(bytes.fromhex(ui['oam'])[32:64]):
                issues.append('description_cancel_owner')
            final = settle(driver)
            issues += audit(repo.load([name])[0], accepted, driver.events, final)['issues']
        elif family == 'info':
            select_footer(1)
            activate_footer()
            ui = info_ready(driver, 0)
            compiler = Compiler()
            issues += info_audit(compiler, compiler.compile(), name, 0, ui, repo) + type_audit(repo, name, ui)
            if ui['moves_state']:
                issues.append('moves_job_survived_info')
            final = settle(driver)
            issues += audit(repo.load([name])[0], accepted, driver.events, final)['issues']
        elif family == 'species':
            target = index + 1 if index < 372 else index - 1
            driver.events.clear()
            accepted = driver.run(('change_species',), key='down' if target > index else 'up')
            driver.run(('selected', 'animation_miss', 'audio_miss'))
            ui = ready(driver, 0)
            target_name = config['names'][target]
            issues += content_audit(repo, target_name, 0, ui, manifest)
            if ui['footer_cursor'] != 2:
                issues.append('species_cancel_cursor')
            final = settle(driver)
            reveal = next(e['t'] for e in driver.events if e['event'] == 'reveal')
            issues += audit(repo.load([target_name])[0], accepted,
                            [e for e in driver.events if e['t'] >= reveal], final, cold=False)['issues']
        else:
            raise ValueError(family)
        if family in ('mash-a', 'hold-a'):
            ui = ready(driver, None)
            issues += content_audit(repo, name, ui['moves_page'], ui, manifest)
            final = settle(driver)
            issues += audit(repo.load([name])[0], accepted, driver.events, final)['issues']
        if any(e['event'] in ('animation_miss', 'audio_miss') for e in driver.events):
            issues.append('playback_miss')
        (out / f'{label}.json').write_text(json.dumps(dict(issues=issues, events=driver.events, return_frames=return_frames), indent=2))
    except Exception as error:
        issues.append(str(error))
        driver.evidence(out / f'{label}-failure')
    finally:
        driver.close()
    return dict(species=name, phase=age, family=family, issues=sorted(set(issues)), return_frames=return_frames)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--phases', nargs='+', default=['0'])
    parser.add_argument('--reuse', action='store_true')
    parser.add_argument('--uncaught', action='store_true')
    parser.add_argument('--checkpoints', type=Path, help='Reuse matching caught/uncaught normal-input checkpoints')
    parser.add_argument('--stress', action='store_true')
    parser.add_argument('--families', nargs='+', default=['mash-a', 'hold-a', 'listing', 'a-b', 'description', 'info', 'species'])
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    battery = out / 'fixture.sav'
    fixture(Path('/Applications/SameBoy/Games/pokecrystal.sav'), battery, not args.uncaught)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    core = build_core(repo, Path.home() / 'Documents/GitHub/SameBoy', out)
    states = out / 'listing-states'
    states.mkdir(exist_ok=True)
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    names = [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower()) for n in names]
    provenance = dict(repo.hashes)
    if args.checkpoints:
        checkpoint = args.checkpoints.resolve()
        if any(json.loads((checkpoint / 'provenance.json').read_text())[key] != value for key, value in provenance.items()):
            raise ValueError('Checkpoint ROM changed')
        if (checkpoint / 'fixture.sav').read_bytes() != battery.read_bytes():
            raise ValueError('Checkpoint caught flags differ from this fixture')
        states = checkpoint / 'listing-states'
    elif args.reuse:
        if json.loads((out / 'provenance.json').read_text()) != provenance:
            raise ValueError('ROM changed; regenerate listing checkpoints')
    else:
        driver = Driver(core, ROOT / 'pokecrystal.gbc', BOOT, battery, out / 'bootstrap.log')
        try:
            bootstrap(driver)
            prepare_states(driver, states, len(names))
        finally:
            driver.close()
        (out / 'provenance.json').write_text(json.dumps(provenance))
    config = dict(core=str(core), output=str(out), battery=str(battery), states=str(states), names=names)
    tasks = [(config, i, name, phase) for i, name in enumerate(names)
             if not args.species or name in args.species for phase in args.phases]
    runner = run_case
    if args.stress:
        runner = run_stress
        tasks = [(*task, family) for task in tasks for family in args.families]
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(runner, tasks):
            rows.append(row)
            print(json.dumps(row), flush=True)
            (out / 'report.json').write_text(json.dumps(rows, indent=2))
    totals = dict(tested=len(rows), passed=sum(not r['issues'] for r in rows), pages=sum(r.get('pages', 0) for r in rows))
    (out / 'totals.json').write_text(json.dumps(totals, indent=2))
    print(json.dumps(totals), flush=True)
    return int(totals['tested'] != totals['passed'])

if __name__ == '__main__':
    raise SystemExit(main())
