"""Normal-input Area latency comparison against a freshly linked vanilla ROM."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import subprocess

from .assets import read_symbols, offset, sha256
from .cold_listing import ROOT, POINTS, Driver, bootstrap, KEY
from .info_ui import BOOT
from .performance import result_timing, summarize, T


def compile_core(source, output):
    symbols = read_symbols(source / 'pokecrystal.sym')
    aliases = {'selected': 'Pokedex_UpdateDexEntryScreen', 'end_loop': 'Pokedex.main',
               'footer_accept': 'Pokedex_UpdateDexEntryScreen.do_menu_action'}
    header = output / 'symbols.h'
    lines = [f'#define S_{name} {symbols[name][1]}' for name in
             ('wDexListingScrollOffset', 'wDexListingCursor', 'wCurDexMode',
              'wMenuCursorPosition', 'wDexArrowCursorPosIndex', 'wCurPartySpecies')]
    lines += ['static const struct { unsigned bank, pc; } points[] = {']
    for name, label in POINTS.items():
        bank, pc = symbols.get(aliases.get(name, label), (0, 65535))
        lines.append(f'{{{bank}, {pc}}},')
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    profile = output / 'profile.h'
    labels = {'town_maps': 'TownMapBGUpdate', 'town_gfx': 'LoadTownMapGFX',
              'town_pals': 'TownMapPals', 'find_nests': 'FindNest'}
    profile.write_text('static const struct { unsigned bank, pc; const char *name; bool span; } perf_points[] = {\n' +
        '\n'.join(f'{{{symbols[label][0]}, {symbols[label][1]}, "{name}", true}},' for name, label in labels.items()) + '\n};\n')
    sameboy = Path.home() / 'Documents/GitHub/SameBoy'
    core = output / 'vanilla-core'
    files = 'apu camera display gb joypad mbc memory printer random rumble save_state sgb sm83_cpu timing workboy'.split()
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(sameboy), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="vanilla-perf"',
        f'-DVANILLA_SYMBOLS="{header.resolve()}"', f'-DDEX_PERFORMANCE_SYMBOLS="{profile.resolve()}"',
        str(ROOT / 'tools/dex_timing/probes/vanilla_performance.c'),
        *(str(sameboy / 'Core' / (f + '.c')) for f in files), '-o', str(core)], check=True)
    return core


def prepare(source, output, battery):
    output.mkdir(parents=True, exist_ok=True)
    symbols = read_symbols(source / 'pokecrystal.sym')
    rom = source / 'pokecrystal.gbc'
    core = compile_core(source, output)
    contents = bytearray(battery.read_bytes())
    address = lambda label: symbols[label][0] * 8192 + symbols[label][1] - 0xa000
    for prefix in ('s', 'sBackup'):
        for field in ('Caught', 'Seen'):
            at = address(prefix + 'PokemonData') + symbols['wPokedex' + field][1] - symbols['wPokemonData'][1]
            for i in range(251):
                contents[at + i // 8] |= 1 << (i & 7)
        for field in ('wFirstUnownSeen', 'wUnownDex'):
            at = address(prefix + 'PokemonData') + symbols[field][1] - symbols['wPokemonData'][1]
            if not contents[at]:
                contents[at] = 1
        start, end = address(prefix + 'GameData'), address(prefix + 'GameDataEnd')
        at = address(prefix + 'Checksum')
        contents[at:at+2] = (sum(contents[start:end]) & 65535).to_bytes(2, 'little')
    private = output / 'all-caught.sav'
    private.write_bytes(contents)
    constants = re.findall(r'^\s*const (\w+)\s*;', (source / 'constants/pokemon_constants.asm').read_text(), re.M)
    order = rom.read_bytes()[offset(symbols['NewPokedexOrder']):offset(symbols['NewPokedexOrder'])+251]
    names = [constants[value-1].lower() for value in order]
    driver = Driver(core, rom, BOOT, private, output / 'bootstrap.log')
    states = output / 'states'
    states.mkdir(exist_ok=True)
    try:
        bootstrap(driver)
        def navigate(key, target):
            for _ in range(50):
                driver.run(('listing',), key=key)
                driver.run(('end_loop',))
                if driver.command('peek')['index'] == target:
                    driver.run(('listing',))
                    return
                driver.run(('listing',))
            raise RuntimeError(f'Vanilla navigation did not reach {target}')
        for _ in range(300):
            current = driver.command('peek')['index']
            if current == 0:
                break
            navigate('up', current - 1)
        for i in range(251):
            if driver.command('peek')['index'] != i:
                raise RuntimeError(f'Vanilla navigation expected {i}: {driver.command("peek")}')
            driver.command(f'save {states}/listing-{i:03}.s0')
            if i < 250:
                navigate('down', i + 1)
    finally:
        driver.close()
    config = dict(core=str(core.resolve()), rom=str(rom.resolve()), sym=str((source / 'pokecrystal.sym').resolve()),
        battery=str(private.resolve()), output=str(output.resolve()), states=str(states.resolve()), names=names,
        rom_sha256=sha256(rom.read_bytes()), original_save_sha256=sha256(battery.read_bytes()))
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    return config


def run_case(job):
    config, name, action, q = job
    output = Path(config['output'])
    label = f'{name}-{action}-{q}'
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], output / (label + '.log'))
    symbols = read_symbols(config['sym'])
    result = dict(species=name, action=action, phase='settled', input_phase=q, issues=[])
    def reach(label, key=0):
        bank, pc = symbols[label]
        value = driver.command(f'restorerun {bank} {pc} {600*T} {key}')
        if value['hit'] < 0:
            raise RuntimeError(f'Timed out: {label}: {value}')
        return value
    try:
        index = config['names'].index(name)
        driver.command(f'load {config["states"]}/listing-{index:03}.s0')
        driver.command('rawcolor')
        driver.run(('accept',), key='a')
        driver.run(('selected',), frames=600)
        driver.run(frames=180)
        driver.run(frames=2, key='right')
        driver.run(frames=2)
        if driver.command('peek')['cursor'] != 1:
            raise RuntimeError('Vanilla Area cursor was not selected')
        if action == 'area-return':
            reach('Pokedex_GetArea.loop', 16)
            driver.run(frames=3)
        if q:
            driver.command(f'run 0 {q} 0')
        initial = driver.command('perf 1')
        driver.events.clear()
        if action == 'area':
            accepted = driver.run(('footer_accept',), key='a')
            reached = reach('Pokedex_GetArea.loop')
        else:
            accepted = reach('Pokedex_GetArea.a_b', 32)
            reached = driver.run(('selected',), frames=600)
        driver.run(frames=4)
        result['ready_t'] = reached['t']
        events = list(driver.events)
        final = driver.command('perf 0')
        result.update(result_timing(events, initial, final, 'full', initial['t'], accepted['t']))
        (output / (label + '-trace.json')).write_text(json.dumps(events, separators=(',', ':')))
        result['status'] = 'pass'
    except Exception as error:
        result.update(status='error', error=str(error))
        driver.evidence(output / (label + '-failure'))
    finally:
        driver.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--jobs', type=int, default=12)
    args = parser.parse_args()
    config = prepare(args.source.resolve(), args.output.resolve(), args.battery.resolve()) if args.prepare else json.loads((args.output / 'config.json').read_text())
    tasks = [(config, name, action, q) for name in ['chikorita', 'eevee', 'mewtwo', 'exeggcute', 'snorlax', 'chansey', 'rattata', 'magikarp']
             for action in ('area', 'area-return') for q in (0, T//4, T//2, T*3//4)]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(run_case, tasks))
    report = dict(provenance=config, cases=len(results), failures=sum(r['status'] != 'pass' for r in results),
                  summary=summarize(results), results=results)
    (args.output / 'performance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))
    for r in results:
        if r['status'] != 'pass':
            print(json.dumps(r))
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
