"""Qualify Struggle's Pokedex-award hook without replacing the accepted link."""
import argparse
import json
from pathlib import Path
import shutil

from .assets import Repository, read_symbols, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .info_ui import BOOT, press
from .move_acquisition import fixture, ram
from .move_battle_use import reach
from .move_persistence import boot, call, core, read, checksum, lifecycle
from .moves_mode import enter, audit, capture, state
from .performance import core as visual_core
from move_discovery_assets import address, decode_record, move_bitmap, seed_records
from tools.pokedex_info_assets import constants

STEM = 'pokecrystal-dex-moves-battle-use'


def award(driver, symbols, expected, struggle):
    """Run the actual award's setflag/callasm through the ROM script dispatcher."""
    old_bank = ram(driver, symbols, 'wScriptBank')
    old_pos = ram(driver, symbols, 'wScriptPos', 2)
    bank, pc = symbols['MrPokemonsHouse_OakScript.ReceivePokedex']
    try:
        fixture(driver, symbols, 'wScriptBank', [bank])
        fixture(driver, symbols, 'wScriptPos', pc.to_bytes(2, 'little'))
        call(driver, symbols, 'RunScriptCommand')
        if read(driver, symbols)[:64] != expected:
            raise AssertionError('The setflag command unexpectedly discovered a move')
        if not ram(driver, symbols, 'wStatusFlags')[0] & 1:
            raise AssertionError('The actual award did not enable the Pokedex')
        result = call(driver, symbols, 'RunScriptCommand')
        expected = bytes(a | b for a, b in zip(expected, move_bitmap([struggle])))
        if read(driver, symbols)[:64] != expected:
            raise AssertionError('The award did not add exactly Struggle')
        after = int.from_bytes(ram(driver, symbols, 'wScriptPos', 2), 'little')
        if (ram(driver, symbols, 'wScriptBank')[0], after) != symbols['MrPokemonsHouse_OakScript.PokedexRecorded']:
            raise AssertionError('The gift hook lost its script continuation')
        return result
    finally:
        fixture(driver, symbols, 'wScriptBank', old_bank)
        fixture(driver, symbols, 'wScriptPos', old_pos)


def normal_save(driver, symbols, path):
    bank, pc = symbols['StartMenu.loop']
    if not driver.command(f'until {bank} {pc} 400 128')['hit']:
        raise AssertionError('Could not open the normal Save menu')
    driver.command('run 4 0')
    menu = ram(driver, symbols, 'wMenuItemsList', 16)
    row = list(menu[1:menu[0] + 1]).index(4) + 1
    for _ in range(12):
        if ram(driver, symbols, 'wMenuCursorPosition')[0] == row:
            break
        driver.command('run 4 8')
        driver.command('run 4 0')
    else:
        raise AssertionError('Could not select Save')
    reach(driver, symbols, 'SaveGameData')
    reach(driver, symbols, 'ResumeGameLogic')
    bank, pc = symbols['HandleMapTimeAndJoypad']
    if not driver.command(f'until {bank} {pc} 400 0')['hit']:
        raise AssertionError('Save did not return to the map')
    driver.command(f'battery {path}')


def qualify(output, baseline):
    manifest_path = output / 'moves-mode-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if not manifest.get('struggle_at_pokedex'):
        raise ValueError('Build with --grant-struggle first')
    target = output / 'pokedex-gift'
    target.mkdir(exist_ok=True)
    symbols = read_symbols(output / f'{STEM}.sym')
    struggle = constants(ROOT / 'constants/move_constants.asm')['STRUGGLE']
    old_root, new_root = baseline / 'candidate', output / 'candidate'
    changed = {p.relative_to(new_root).as_posix() for p in new_root.rglob('*.asm')
               if not (old_root / p.relative_to(new_root)).exists()
               or p.read_bytes() != (old_root / p.relative_to(new_root)).read_bytes()}
    if changed != {'main.asm', 'maps/MrPokemonsHouse.asm', 'engine/pokedex/move_pokedex_gift.asm'}:
        raise AssertionError(f'Unexpected source delta from accepted battle prototype: {changed}')
    old_symbols = read_symbols(baseline / f'{STEM}.sym')
    for name, pair in old_symbols.items():
        if name.startswith(('w', 's', 'h')) and pair[1] >= 0xa000 and name in symbols and symbols[name] != pair:
            raise AssertionError(f'Existing memory address moved: {name}')
    protected = dict(manifest['protected_inputs'])
    for path in [*(baseline / f'{STEM}.{suffix}' for suffix in ('gbc', 'sym', 'map', 'sav')),
                 baseline / 'final-qualification.json',
                 baseline / 'battle-review' / f'{STEM}.sav']:
        protected[str(path)] = sha256(path.read_bytes())
    config = dict(rom=str(output / f'{STEM}.gbc'), symbols=symbols,
                  core=str(core(output, target_root=target)))
    data = bytearray((baseline / f'{STEM}.sav').read_bytes())
    flag_offset = symbols['wStatusFlags'][1] - symbols['wPlayerData'][1]
    for prefix in ('s', 'sBackup'):
        at = address(symbols, prefix + 'PlayerData') + flag_offset
        data[at] &= ~1
        checksum(data, symbols, prefix)
    pre_dex = target / 'pre-dex.sav'
    pre_dex.write_bytes(seed_records(data, symbols, bytes(64)))
    driver = boot(config, pre_dex, target / 'award.log')
    rows, contracts = [], []
    try:
        if read(driver, symbols)[:64] != bytes(64) or ram(driver, symbols, 'wStatusFlags')[0] & 1:
            raise AssertionError('Cold pre-Dex fixture was already awarded/discovered')
        driver.command(f'trace {target / "award-sram.csv"}')
        for phase in range(4):
            for indices in ([], [1, 85, 333], [struggle], list(range(1, 334))):
                call(driver, symbols, 'MoveDiscovery_Clear')
                for index in indices:
                    call(driver, symbols, 'MoveDiscovery_MarkIndex', index)
                expected = move_bitmap(indices)
                fixture(driver, symbols, 'wStatusFlags', [ram(driver, symbols, 'wStatusFlags')[0] & ~1])
                driver.command(f'cycles {phase * 35112} 0')
                result = award(driver, symbols, expected, struggle)
                after = read(driver, symbols)
                award(driver, symbols, after[:64], struggle)
                if read(driver, symbols) != after:
                    raise AssertionError('Repeated award changed flags or status')
                rows.append(dict(phase=phase, prior=indices, ms=result['ms'], intervals=result['intervals']))
        for bank in range(8):
            for flags in (0, 0xf0):
                call(driver, symbols, 'MoveDiscovery_Clear')
                call(driver, symbols, 'MoveDiscovery_MarkIndex', 85)
                driver.command(f'io 65392 {bank}')
                b, pc = symbols['MoveDiscovery_PokedexGift']
                owner = driver.command('peek')
                driver.command(f'begin {b} {pc} 42330 23205')
                if not driver.command(f'until {b} {pc} 4 0')['hit']:
                    raise AssertionError('Gift helper entry was not reached')
                driver.command(f'regs {0x6900 | flags} 42330 23205 4660')
                before = driver.command('peek')
                driver.command('follow')
                after = driver.command('resume 8 0')
                if not after['hit'] or any(before[n] != after[n] for n in (
                        'af', 'bc', 'de', 'hl', 'svbk', 'sram_bank', 'sram_enabled', 'double_speed')):
                    raise AssertionError(f'Gift helper lost its register/bank contract: {before}: {after}')
                if read(driver, symbols)[:64] != move_bitmap([85, struggle]):
                    raise AssertionError('Gift helper used a transient ID or changed another bit')
                if not driver.command(f'until {owner["bank"]} {owner["pc"]} 8 0')['hit']:
                    raise AssertionError('Gift helper observer did not unwind')
                contracts.append(dict(bank=bank, flags=flags))
        driver.command('trace off')
        if (target / 'award-sram.csv').read_bytes():
            raise AssertionError('Receiving the Dex wrote SRAM immediately')
    finally:
        driver.close()
    review = []
    for label, source, destination in (
            ('natural', baseline / f'{STEM}.sav', output / f'{STEM}.sav'),
            ('battle', baseline / 'battle-review' / f'{STEM}.sav', output / 'battle-review' / f'{STEM}.sav')):
        destination.parent.mkdir(exist_ok=True)
        driver = boot(config, source, target / (label + '-save.log'))
        try:
            before = read(driver, symbols)[:64]
            award(driver, symbols, before, struggle)
            expected = read(driver, symbols)[:64]
            normal_save(driver, symbols, destination)
        finally:
            driver.close()
        for prefix in ('s', 'sBackup'):
            if decode_record(destination.read_bytes(), symbols, prefix) != dict(status='valid', bitmap=expected):
                raise AssertionError('Normal Save did not commit the gift in both copies')
        driver = boot(config, destination, target / (label + '-cold-reload.log'))
        try:
            if read(driver, symbols)[:64] != expected:
                raise AssertionError('Cold Continue lost the gift')
        finally:
            driver.close()
        review.append(dict(fixture=label, save=str(destination), save_sha256=sha256(destination.read_bytes()),
                           discovered=[n for n in range(1, 334) if expected[(n - 1) // 8] & 1 << ((n - 1) % 8)],
                           normal_save=True, cold_reload=True))
    shutil.copy2(output / f'{STEM}.gbc', output / 'battle-review' / f'{STEM}.gbc')
    shutil.copy2(output / f'{STEM}.sav', target / 'save-4.sav')
    lifecycle_cases = lifecycle(config, target)
    repo = Repository(new_root, output / f'{STEM}.gbc', output / f'{STEM}.sym')
    executable = visual_core(repo, target)
    driver = Driver(executable, repo.rom_path, BOOT, output / f'{STEM}.sav', target / 'dex.log')
    try:
        bootstrap(driver)
        enter(driver, repo)
        known = set(review[0]['discovered'])
        fixture_manifest = dict(manifest, fixture='mixed', unknown=[n for n in range(1, 334) if n not in known])
        audit(driver, repo, fixture_manifest)
        ordinal = manifest['orders'][state(driver, repo)['sort']].index(struggle)
        for _ in range(42):
            current = state(driver, repo)
            if ordinal - current['scroll'] - current['cursor'] < 8:
                break
            press(driver, 'right')
        for _ in range(8):
            if state(driver, repo)['selected'] == struggle:
                break
            press(driver, 'down')
        if state(driver, repo)['selected'] != struggle:
            raise AssertionError('Could not navigate to Struggle')
        audit(driver, repo, fixture_manifest)
        capture(driver, target / 'struggle-seen.png')
    finally:
        driver.close()
    for path, digest in protected.items():
        if sha256(Path(path).read_bytes()) != digest:
            raise AssertionError(f'Protected artifact changed: {path}')
    manifest.update(protected_inputs=protected, prior_battle_baseline=str(baseline),
                    manual_review_seen=review[0]['discovered'], manual_review_save_sha256=review[0]['save_sha256'])
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    result = dict(rom_sha256=sha256(repo.rom), struggle_index=struggle, award_cases=len(rows),
                  repeated_awards=len(rows), contracts=len(contracts), lifecycle_cases=lifecycle_cases,
                  script_cases=rows, register_cases=contracts, review=review,
                  changed_sources=sorted(changed), protected_inputs=len(protected), no_immediate_sram_write=True,
                  visible_known_entry=struggle, issues=[],
                  baseline_qualification=str(baseline / 'final-qualification.json'),
                  scope='Focused new-link qualification; prior full battle regression was not rerun.')
    (output / 'pokedex-gift-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('script_cases', 'register_cases')}, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    output, baseline = args.output.resolve(), args.baseline.resolve()
    if not all(path.is_relative_to(ROOT / 'build') for path in (output, baseline)):
        raise ValueError('Use private build paths')
    qualify(output, baseline)


if __name__ == '__main__':
    main()
