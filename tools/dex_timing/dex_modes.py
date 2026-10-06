"""Read-only native qualification for the locked/unlocked Dex Modes menu."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import shutil

from .assets import Repository
from .cold_listing import Driver, ROOT, bootstrap
from .description_ui import settle
from .info_ui import BOOT, press
from .legacy_listing import open_mode_screen, private_battery
from .area_ui import reach

LABELS = ('Modern Dex Mode', 'Legacy Dex Mode', 'Unown Dex Mode',
          'Moves Dex Mode', 'Type Matchups')
DESCRIPTIONS = (
    ('Displays <PK><MN> in a', 'visual grid.'),
    ('Displays <PK><MN> in the', 'classic text list.'),
    ('Displays all Unown', 'forms caught.'),
    ('Move descriptions', 'and stats.'),
    ('<PK><MN> Type weaknesses', 'and resistances.'),
)


def mode_ids(unlocked):
    return (0, 1, 2, 3, 4) if unlocked else (0, 1, 3, 4)


def encode(text):
    from pokedex_info_assets import Compiler
    chars = dict(Compiler().chars, **{'<PK>': 0xe1, '<MN>': 0xe2})
    return bytes(chars[token] for token in re.findall(r'<PK>|<MN>|.', text))


def audit_menu(ui, unlocked, row):
    issues = []
    tiles = bytes.fromhex(ui['map'])
    ids = mode_ids(unlocked)
    for at in range(5):
        expected = encode(LABELS[ids[at]]) if at < len(ids) else b''
        start = (3 + at * 2) * 21 + 3
        if tiles[start:start + 16] != expected.ljust(16, b'\x7f'):
            issues.append(f'row_{at}_label')
        cursor = tiles[(3 + at * 2) * 21 + 2]
        if cursor not in ((0x7f, 0xed) if at == row else (0x7f,)):
            issues.append(f'row_{at}_cursor')
    if ui['footer_cursor'] != row:
        issues.append('cursor_index')
    for y, line in zip((14, 16), DESCRIPTIONS[ids[row]]):
        expected = encode(line)
        if len(expected) > 18:
            raise ValueError('Description exceeds the 18-cell panel')
        start = y * 21 + 1
        if tiles[start:start + 18] != expected.ljust(18, b'\x7f'):
            issues.append(f'description_line_{y}')
        if tiles[y * 21] != 0x36 or tiles[y * 21 + 19] != 0x37:
            issues.append(f'description_border_{y}')
    if tiles[15 * 21 + 1:15 * 21 + 19] != b'\x7f' * 18:
        issues.append('description_line_gap')
    title = bytes((0x3b,)) + encode(' Modes ') + bytes((0x3c,))
    if tiles[21:21 + len(title)] != title:
        issues.append('title')
    if tiles[:20] != b'\x31' * 20 or tiles[21 + len(title):41] != b'\x31' * (20 - len(title)):
        issues.append('header_shell_background')
    if ui['scx'] or ui['wx'] != 0xa7:
        issues.append('menu_scroll_window')
    return issues


def row_case(task):
    from PIL import Image
    config, fixture, unlocked, presentation, order, row, output = task
    output = Path(output)
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    tag = f'{int(unlocked)}-{presentation}-{order}-{row}'
    driver = Driver(config['core'], config['rom'], BOOT, fixture, output / f'{tag}.log')
    issues = []
    try:
        bootstrap(driver, expected_mode=order)
        before = driver.command('peek')
        open_mode_screen(driver)
        cursor = driver.command('ui')['footer_cursor']
        for _ in range(abs(row - cursor)):
            press(driver, 'down' if row > cursor else 'up')
        driver.run(frames=3)
        issues += audit_menu(driver.command('ui'), unlocked, row)
        if order == 0:
            driver.command('rawcolor')
            driver.run(frames=2)
            path = output / f'modes-{tag}.ppm'
            driver.command(f'image {path}')
            with Image.open(path) as image:
                image.save(path.with_suffix('.png'))
                image.resize((640, 576), Image.Resampling.NEAREST).save(
                    path.with_name(path.stem + '-4x.png'))
        # Both menu boundaries remain bounded, including held input.
        if row in (0, len(mode_ids(unlocked)) - 1):
            driver.run(frames=40, key='up' if row == 0 else 'down')
            driver.run(frames=3)
            issues += audit_menu(driver.command('ui'), unlocked, row)
        mode = mode_ids(unlocked)[row]
        if mode in (3, 4):
            press(driver, 'a')
            driver.run(frames=20, key='a')
            driver.run(frames=3)
            state = driver.command('peek')
            if state['jumptable'] != 8 or state['presentation'] != presentation or state['mode'] != order:
                issues.append('placeholder_changed_owner_or_order')
            issues += audit_menu(driver.command('ui'), unlocked, row)
            press(driver, 'select' if row & 1 else 'b')
        elif mode == 2:
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateUnownMode')
            driver.run(frames=2)
            for _ in range(27):
                press(driver, 'right')
            for _ in range(27):
                press(driver, 'left')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            driver.run(frames=3)
            issues += audit_menu(driver.command('ui'), unlocked, 2)
            press(driver, 'b')
        else:
            press(driver, 'a')
        returned = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        state = driver.command('peek')
        expected = mode if mode in (0, 1) else presentation
        if returned['hit'] != 'listing' or state['index'] != before['index'] or state['mode'] != order:
            issues.append('return_changed_selection_or_order')
        if state['presentation'] != expected:
            issues.append('return_changed_presentation')
        driver.events.clear()
        driver.command('audit 1')
        driver.run(('selected', 'animation_miss', 'audio_miss'), key='a')
        settle(driver)
        press(driver, 'select')
        if driver.command('peek')['jumptable'] != 3:
            issues.append('selected_allowed_mode_entry')
        if any(event['event'] in ('animation_miss', 'audio_miss') for event in driver.events):
            issues.append('return_playback_miss')
        if issues:
            driver.evidence(output / f'{tag}-failure')
    except (RuntimeError, ValueError) as error:
        issues.append(str(error))
        driver.evidence(output / f'{tag}-error')
    finally:
        driver.close()
    return dict(unlocked=unlocked, presentation=presentation, order=order, row=row,
                mode=mode_ids(unlocked)[row], issues=issues)


def qualify(output, jobs):
    config = json.loads((output / 'legacy/config.json').read_text())
    target = output / 'modes-qualification'
    target.mkdir(exist_ok=True)
    tasks = []
    for unlocked in (False, True):
        for presentation in (0, 1):
            for order in (0, 1, 2):
                fixture = target / f'fixture-{int(unlocked)}-{presentation}-{order}.sav'
                private_battery(config, fixture, presentation=presentation,
                                order_mode=order, unown_unlocked=unlocked)
                tasks.extend((config, str(fixture), unlocked, presentation, order, row, str(target))
                             for row in range(len(mode_ids(unlocked))))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(row_case, tasks))
    summary = dict(cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for stem in ('pokecrystal-dex-modes', 'pokecrystal-dex-modes-locked'):
        for suffix in ('gbc', 'sym', 'map'):
            shutil.copy2(output / f'pokecrystal-dex-legacy.{suffix}', output / f'{stem}.{suffix}')
    private_battery(config, output / 'pokecrystal-dex-modes.sav', presentation=0, unown_unlocked=True)
    locked = dict(config, battery=str(output / 'pokecrystal-dex-modes.sav'))
    private_battery(locked, output / 'pokecrystal-dex-modes-locked.sav', presentation=0, unown_unlocked=False)
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}), flush=True)
    return int(bool(summary['failures']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=10)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a private build/ directory')
    return qualify(output, args.jobs)


if __name__ == '__main__':
    raise SystemExit(main())
