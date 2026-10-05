"""Physical-frame A/B checks for every custom inventory selection."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import statistics

from .assets import Repository
from .cold_listing import Driver, FRAME, KEY
from .global_speed import BASE, configuration, compile_core
from . import shared_menu_regression as menu


def metric(t, pressed):
    return dict(frames=(t - pressed) / FRAME, ms=(t - pressed) * 1000 / 4194304)


def measure(driver, repo, checkpoint, key, output, label):
    # A matched no-input replay excludes autonomous disc/icon animation from
    # the first-response measurement. The emulator does not serialize pixels.
    driver.command(f'load {checkpoint}')
    menu.run(driver, repo, frames=4)
    driver.command(f'save {output / "measurement.s0"}')
    driver.command(f'perfpixels save {output / "measurement.pixels"}')
    driver.command('perf 1')
    driver.events.clear()
    menu.run(driver, repo, frames=96)
    idle = [e for e in driver.events if e['event'] == 'perf_frame']
    driver.command(f'load {output / "measurement.s0"}')
    driver.command(f'perfpixels load {output / "measurement.pixels"}')
    initial = driver.command('perf 1')
    driver.events.clear()
    menu.run(driver, repo, frames=4, keys=KEY[key])
    menu.run(driver, repo, frames=92)
    frames = [e for e in driver.events if e['event'] == 'perf_frame']
    changes = [a for a, b in zip(frames, idle) if a['full'] != b['full']]
    targets = {e['full'] for e in frames[-32:]}
    complete = [e for e in frames if e['full'] in targets]
    state = driver.command('m')
    driver.command(f'image {output / (label + ".ppm")}')
    return dict(label=label, key=key,
                first=metric(changes[0]['t'], initial['t']) if changes else None,
                complete=metric(complete[0]['t'], initial['t']) if changes and complete else None,
                palette_set=sorted({(e['bgpals'], e['objpals']) for e in frames[-32:]}),
                oam_set=sorted({e['oam'] for e in frames[-32:]}),
                pixel_set=sorted(targets), final=state,
                animation_states=len({e['oam'] for e in frames[-64:]}))


def execute(variant):
    cfg = configuration(variant)
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    output = BASE / 'custom-menus' / variant
    output.mkdir(parents=True, exist_ok=True)
    core = compile_core(repo, output)
    source = BASE / 'menus' / variant / 'standard'
    driver = Driver(core, cfg['rom'], menu.BOOT, source / 'private.sav', output / 'run.log')
    rows, issues = [], []
    try:
        for pocket in range(5):
            state = source / f'pack-pocket-{pocket}.s0'
            for key in ('left', 'right', 'up', 'down', 'a', 'start', 'select', 'b'):
                rows.append(measure(driver, repo, state, key, output, f'pack-{pocket}-{key}'))
        for color in range(7):
            driver.command(f'load {source / "apricorn.s0"}')
            for _ in range(color):
                menu.tap(driver, repo, 'right', released=40)
            if driver.command('m')['wMenuCursorPosition'] != color:
                issues.append(f'Apricorn selection {color}')
            state = output / f'apricorn-{color}.s0'
            driver.command(f'save {state}')
            for key in ('right', 'left', 'a'):
                rows.append(measure(driver, repo, state, key, output, f'apricorn-{color}-{key}'))
        for index in range(57):
            page, slot = divmod(index, 8) if index < 50 else (7, index - 50)
            driver.command(f'load {source / "tmhm.s0"}')
            for _ in range(min(page, 6) * 4 + (2 if page == 7 else 0)):
                menu.tap(driver, repo, 'right', released=40)
            if slot >= 4:
                menu.tap(driver, repo, 'down', released=40)
            for _ in range(slot % 4):
                menu.tap(driver, repo, 'right', released=40)
            selected = driver.command('m')
            if (selected['wMenuScrollPosition'], selected['wMenuCursorPosition']) != (page, slot):
                issues.append(f'TM/HM selection {index}: {selected["wMenuScrollPosition"]}/{selected["wMenuCursorPosition"]}')
            state = output / f'tmhm-{index}.s0'
            driver.command(f'save {state}')
            for key in ('right', 'select', 'a'):
                rows.append(measure(driver, repo, state, key, output, f'tmhm-{index}-{key}'))
        for row in rows:
            if row['final']['double_speed'] != cfg['expected_double_speed']:
                issues.append(f'CPU speed changed: {row["label"]}')
    finally:
        driver.close()
    result = dict(variant=variant, cases=len(rows), issues=issues, rows=rows)
    (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    with ProcessPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(execute, ('production', 'full', 'final')))
    base = {r['label']: r for r in results[0]['rows']}
    comparisons = []
    for result in results[1:]:
        for row in result['rows']:
            old = base[row['label']]
            comparisons.append(dict(variant=result['variant'], label=row['label'],
                first_change=(row['first']['frames'] - old['first']['frames']) if row['first'] and old['first'] else None,
                complete_change=(row['complete']['frames'] - old['complete']['frames']) if row['complete'] and old['complete'] else None,
                same_palettes=row['palette_set'] == old['palette_set'],
                same_pixels=row['pixel_set'] == old['pixel_set'],
                same_disc_motion=row['oam_set'] == old['oam_set'] if row['label'].startswith('tmhm') else None))
    report = dict(results=results, comparisons=comparisons)
    (BASE / 'custom-menus/report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(variant=r['variant'], cases=r['cases'], issues=r['issues']) for r in results]))


if __name__ == '__main__':
    main()
