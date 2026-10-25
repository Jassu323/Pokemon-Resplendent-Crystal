"""Read-only Type-page costs for isolated frame-owner scoping."""
from collections import defaultdict
import gzip
import json
import shutil
import statistics

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, bootstrap
from .performance import core
from .type_matchups import BOOT, OUTPUT as SOURCE, enter_types, press

OUTPUT = ROOT / 'build/dex-types-isolation-scope-20261012'
POINTS = {
    'types_draw': ('PokedexTypes_DrawSelection', True),
    'types_matchups': ('PokedexTypes_BuildMatchups', True),
    'types_colours': ('PokedexTypes_StageColours', True),
    'types_stage': ('Pokedex_StageOwnerTransitionMaps', True),
    'types_commit': ('PokedexTypes_CommitLower', True),
    'sound': ('_UpdateSound', True),
    'joypad': ('UpdateJoypad', True),
    'clock': ('GameTimer', True),
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, SOURCE / 'pokecrystal-dex-types.gbc', SOURCE / 'pokecrystal-dex-types.sym')
    executable = core(repo, OUTPUT, POINTS)
    battery = OUTPUT / 'private.sav'
    shutil.copy2(SOURCE / 'pokecrystal-dex-types.sav', battery)
    driver = Driver(executable, repo.rom_path, BOOT, battery, OUTPUT / 'run.log')
    try:
        bootstrap(driver)
        enter_types(driver, repo, True)
        driver.events.clear()
        driver.command('perf 1')
        for i in range(36):
            press(driver, 'down' if i % 3 == 2 else 'right')
            if i % 3 == 2:
                press(driver, 'right')
        press(driver, 'b')
        events = list(driver.events)
    finally:
        driver.close()
    with gzip.open(OUTPUT / 'events.jsonl.gz', 'wt') as stream:
        for event in events:
            stream.write(json.dumps(event) + '\n')
    groups = defaultdict(list)
    for event in events:
        if event['event'] == 'perf_cost' and event['name'] in POINTS:
            groups[event['name']].append(event['elapsed'] * 1000 / 4194304)
    result = dict(rom_sha256=sha256(repo.rom), costs_ms={name: dict(samples=len(values),
        minimum=min(values), median=statistics.median(values), maximum=max(values))
        for name, values in groups.items()}, observed_only=True,
        note='Wall-clock spans include interrupts. This is not a frame-loop implementation or all-music worst-case qualification.')
    (OUTPUT / 'costs.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
