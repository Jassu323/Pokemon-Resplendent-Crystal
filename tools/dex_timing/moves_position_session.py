"""Focused session-reset checks; deliberately not the full Dex campaign."""
import difflib
import json
from pathlib import Path
import shutil

from .assets import Repository, read_symbols, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press
from .area_ui import reach
from .legacy_listing import private_battery
from .listing_options import memory
from .moves_mode import enter, sort, state, capture
from .moves_position import bookmark, visual_audit
from .moves_search import open_search, search
from .moves_sort_memory import close_dex, save_visual
from .performance import core
from build_dex_unown_prototype import resources

BASE = ROOT / 'build/dex-moves-position-session-20261014'
PRIOR = ROOT / 'build/dex-moves-position-20261014'
STEM = 'pokecrystal-dex-moves-position'


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def first(driver, repo, manifest, order):
    actual = state(driver, repo)
    expected = dict(sort=order, cursor=0, scroll=0,
                    selected=manifest['orders'][order][0])
    assert actual == expected, (actual, expected)
    visual_audit(driver, repo, manifest)
    return actual


def reopen_after_save(driver, repo):
    # Save leaves a different start-menu row remembered; allow a full key poll.
    reach(driver, repo, 'StartMenu.loop', key=128)
    driver.run(frames=8)
    bank, at = repo.symbols['wMenuCursorY']
    observed = []
    for _ in range(12):
        cursor = memory(driver, bank, at, 1)[0]
        observed.append(cursor)
        if cursor == 1:
            break
        driver.run(frames=4, key='up')
        driver.run(frames=8)
    else:
        raise AssertionError(f'Could not navigate from Save back to the Dex: {observed}')
    reach(driver, repo, 'Pokedex_UpdateMainScreen', key=16)
    driver.run(('end_loop',))
    driver.run(('end_loop',))


def run(publish=True, previous=None):
    protected = {str(path): sha256(path.read_bytes()) for path in (
        *(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')),
        *ROOT.glob('pokecrystal*.sav'))}
    repo = Repository(BASE / 'candidate', BASE / 'candidate/pokecrystal.gbc',
                      BASE / 'candidate/pokecrystal.sym')
    before = read_symbols(PRIOR / 'rollback/pokecrystal.sym')
    moved = [name for name, pair in before.items()
             if pair[1] >= 0xa000 and name in repo.symbols and pair != repo.symbols[name]]
    assert not moved, moved
    output = BASE / 'focused-tests'
    attempt = 1
    while output.exists():
        attempt += 1
        output = BASE / f'focused-tests-attempt-{attempt}'
    output.mkdir(exist_ok=False)
    executable = core(repo, output / 'observer')
    config = dict(rom=str(repo.rom_path), sym=str(BASE / 'candidate/pokecrystal.sym'), core=str(executable),
                  battery=str(PRIOR / 'review-all-moves.sav'))
    write(output / 'config.json', config)
    manifest = json.loads((PRIOR / 'runtime-regression/moves-mode-manifest.json').read_text())
    rows = []
    for style in (0, 1):
        for order in (0, 1):
            directory = output / f'{style}-{order}'
            directory.mkdir()
            battery = directory / 'input.sav'
            private_battery(config, battery, presentation=style, order_mode=0,
                            unown_unlocked=True)
            driver = Driver(executable, repo.rom_path, BOOT, battery, directory / 'session.log')
            try:
                bootstrap(driver)
                assert bookmark(driver, repo) == bytes(4), 'Continue kept a saved bookmark'
                enter(driver, repo)
                first(driver, repo, manifest, 1)
                sort(driver, repo, 1 - order)
                sort(driver, repo, order)
                for _ in range(3):
                    press(driver, 'right')
                for _ in range(5):
                    press(driver, 'down')
                current = state(driver, repo)
                assert current['scroll'] == 24 and current['cursor'] == 5
                expected = bookmark(driver, repo)
                close_dex(driver, repo)
                bootstrap(driver)
                enter(driver, repo)
                assert state(driver, repo) == current, 'Closing the Dex lost the session bookmark'
                visual_audit(driver, repo, manifest)
                open_search(driver, repo)
                search(driver, repo)
                press(driver, 'down')
                assert bookmark(driver, repo) == expected
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesSearch_Update')
                press(driver, 'b')
                reach(driver, repo, 'PokedexMovesMode_Update')
                assert state(driver, repo) == current, 'Search changed the ordinary-list bookmark'
                close_dex(driver, repo)
                saved = directory / 'normally-saved.sav'
                save_visual(driver, repo, saved)
                assert bookmark(driver, repo) == expected, 'Saving cleared the live bookmark'
                reopen_after_save(driver, repo)
                enter(driver, repo)
                assert state(driver, repo) == current, 'Saving prevented session restoration'
                capture(driver, directory / 'same-session.png')
                close_dex(driver, repo)
                # Real A+B+SELECT+START, not a state load or direct Reset call.
                reach(driver, repo, 'Reset', key=240)
                driver.run(frames=90)
                bootstrap(driver)
                assert bookmark(driver, repo) == bytes(4), 'Soft reset kept the bookmark'
                enter(driver, repo)
                after_reset = first(driver, repo, manifest, order)
                capture(driver, directory / 'soft-reset.png')
                press(driver, 'right')
                current_session = state(driver, repo)
                close_dex(driver, repo)
                bootstrap(driver)
                enter(driver, repo)
                assert state(driver, repo) == current_session
            finally:
                driver.close()
            driver = Driver(executable, repo.rom_path, BOOT, saved, directory / 'cold.log')
            try:
                bootstrap(driver)
                assert bookmark(driver, repo) == bytes(4), 'Cold Continue kept the bookmark'
                bank, at = repo.symbols['wLastMovesDexSort']
                assert memory(driver, bank, at, 1) == bytes([0xa0 | order])
                enter(driver, repo)
                after_cold = first(driver, repo, manifest, order)
                capture(driver, directory / 'cold-continue.png')
            finally:
                driver.close()
            rows.append(dict(presentation=style, sort=order, live=current,
                             soft_reset=after_reset, cold_continue=after_cold, issues=[]))
            print(json.dumps(rows[-1]), flush=True)
    owners = ('engine/pokedex/pokedex_moves_mode.asm', 'ram/wram.asm',
              'engine/menus/intro_menu.asm')
    patch = ''
    for name in owners:
        a, b = PRIOR / 'baseline-source' / name, BASE / 'candidate' / name
        patch += ''.join(difflib.unified_diff(a.read_text().splitlines(True),
            b.read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    (BASE / 'candidate.diff').write_text(patch)
    old = resources(PRIOR / 'rollback/pokecrystal.map')
    previous = resources((previous or PRIOR / 'candidate') / 'pokecrystal.map')
    new = resources(BASE / 'candidate/pokecrystal.map')
    delta = {key: new[key] - old[key] for key in old}
    revision = {key: new[key] - previous[key] for key in old}
    assert all(value == 0 for key, value in delta.items() if key != 'ROMX')
    for path, digest in protected.items():
        assert sha256(Path(path).read_bytes()) == digest, path
    report = dict(candidate_sha256=sha256(repo.rom), production_sha256=protected[str(ROOT / 'pokecrystal.gbc')],
                  cases=len(rows), rows=rows, issues=[], delta=delta, revision_delta=revision,
                  session_only=True, full_regression_rerun=False, production_integrated=False,
                  moved_ram_labels=moved, protected=protected, changed_owners=list(owners))
    write(output / 'results.json', report)
    if not publish:
        report['evidence'] = str(output)
        write(BASE / 'moves-session-validation.json', report)
        return report
    review = BASE / 'review'
    review.mkdir(exist_ok=False)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(BASE / 'candidate' / f'pokecrystal.{ext}', review / f'{STEM}.{ext}')
    shutil.copy2(PRIOR / 'review-all-moves.sav', review / f'{STEM}.sav')
    # Preserve any manual-review battery changes when relocating the old bundle.
    archive = PRIOR / 'root-review-archive'
    archive.mkdir(exist_ok=True)
    relocated = {}
    for ext in ('gbc', 'sym', 'map', 'sav'):
        source = ROOT / f'{STEM}.{ext}'
        if source.exists():
            destination = archive / source.name
            if destination.exists():
                raise ValueError('Refusing to replace earlier archive: ' + str(destination))
            relocated[str(destination)] = sha256(source.read_bytes())
            shutil.move(source, destination)
    report['prior_review_relocated'] = relocated
    report['review_files'] = {str(path): sha256(path.read_bytes()) for path in review.iterdir()}
    write(BASE / 'session-manifest.json', report)
    print(json.dumps({key: report[key] for key in ('candidate_sha256', 'delta', 'revision_delta', 'cases')}, indent=2))


if __name__ == '__main__':
    run()
