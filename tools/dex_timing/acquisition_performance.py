"""Measure stage-two save/load and real-source hook cost against the accepted ROM."""
import argparse
import json
from pathlib import Path
import statistics

from .assets import read_symbols, sha256
from .move_persistence import boot, call, core, STEM
from .move_persistence_integration import timing_case, save_menu_case
from .move_acquisition import fixture, direct


def qualify(output, baseline):
    target = output / 'acquisition-performance'
    target.mkdir(exist_ok=True)
    configs = {}
    for name, folder in (('baseline', baseline), ('acquisition', output)):
        (target / name).mkdir(exist_ok=True)
        configs[name] = dict(rom=str(folder / f'{STEM}.gbc'),
                             symbols=read_symbols(folder / f'{STEM}.sym'),
                             core=str(core(folder, target_root=target / name)))
    rows = {}
    for name, config in configs.items():
        rows[name] = {}
        for kind, source in (('valid', output / 'all-seen-tests.sav'),
                             ('legacy', output / 'legacy-input.sav'),
                             ('full_legacy', output / 'acquisition-qualification/legacy-full-current-1.sav'),
                             ('recovery', output / 'persistence-qualification/repair-source.sav')):
            rows[name][kind] = [timing_case(config, source, target / f'{name}-{kind}-{n}.log') for n in range(4)]
        driver = boot(config, output / 'persistence-qualification/empty.sav', target / f'{name}-save.log')
        try:
            rows[name]['save'] = [call(driver, config['symbols'], 'SaveGameData') for _ in range(4)]
        finally:
            driver.close()
    native = configs['acquisition']
    save_menus = [save_menu_case(native, target, value) for value in (False, True)]
    costs = {}
    driver = boot(native, output / 'persistence-qualification/empty.sav', target / 'receipt-costs.log')
    try:
        symbols = native['symbols']
        fixture(driver, symbols, 'wPartyCount', [1])
        fixture(driver, symbols, 'wCurPartyMon', [0])
        fixture(driver, symbols, 'wPartySpecies', [1, 255])
        ids = [direct(driver, symbols, 'GetMoveIDFromIndex', hl=n)['af'] >> 8 for n in (1, 255, 256, 333)]
        fixture(driver, symbols, 'wPartyMon1Moves', ids)
        fixture(driver, symbols, 'wPutativeTMHMMove', [ids[-1]])
        for name in ('Learned', 'LastParty', 'CurrentParty', 'BootstrapOwned'):
            costs[name] = [call(driver, symbols, 'MoveDiscovery_' + name) for _ in range(4)]
    finally:
        driver.close()
    summary = {}
    for kind in rows['acquisition']:
        record = {}
        for field in ('ms', 'intervals'):
            before = statistics.median(r[field] for r in rows['baseline'][kind])
            after = statistics.median(r[field] for r in rows['acquisition'][kind])
            record[field] = dict(baseline=before, acquisition=after, delta=after - before)
        summary[kind] = record
    result = dict(rom_sha256=sha256(Path(native['rom']).read_bytes()), rows=rows, summary=summary,
                  hook_costs=costs, normal_save_menus=save_menus,
                  note='Physical LCD intervals, not emulator speed; no save states used for loading.', issues=[])
    (output / 'acquisition-performance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    qualify(args.output.resolve(), args.baseline.resolve())


if __name__ == '__main__':
    main()
