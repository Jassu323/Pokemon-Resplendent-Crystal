"""Capture vanilla, production and trial Unown screens using normal controls."""
import argparse
import json
from pathlib import Path

from PIL import Image

from .assets import offset, read_symbols, sha256
from .cold_listing import Driver, bootstrap
from .info_ui import BOOT
from .vanilla_performance import compile_core


def battery(source, symbols, target, forms, modern, *, caught_order=None, presentation=0):
    before = source.read_bytes()
    data = bytearray(before)
    ram = lambda label: symbols[label][1]
    def address(label):
        bank, at = symbols[label]
        return bank * 8192 + at - 0xa000
    for prefix in ('s', 'sBackup'):
        player = address(prefix + 'PlayerData')
        pokemon = address(prefix + 'PokemonData')
        at = player + ram('wStatusFlags') - ram('wPlayerData')
        data[at] |= 2
        at = player + ram('wLastDexMode') - ram('wPlayerData')
        data[at] = 0
        if modern:
            at = player + ram('wLastDexPresentation') - ram('wPlayerData')
            data[at] = presentation
        at = pokemon + ram('wUnownDex') - ram('wPokemonData')
        order = list(range(1, forms + 1)) if caught_order is None else list(caught_order)
        if len(order) > 26 or len(set(order)) != len(order) or any(n not in range(1, 27) for n in order):
            raise ValueError('Use at most 26 distinct Unown IDs in the range 1-26')
        data[at:at + 26] = bytes(order) + bytes(26 - len(order))
        at = pokemon + ram('wFirstUnownSeen') - ram('wPokemonData')
        data[at] = 1
        section = 'SaveData' if prefix + 'SaveData' in symbols else 'GameData'
        start, end = address(prefix + section), address(prefix + section + 'End')
        at = address(prefix + 'Checksum')
        data[at:at + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')
    if modern:
        from move_discovery_assets import rebind_fixture
        data = rebind_fixture(before, data, symbols)
    target.write_bytes(data)


def capture(config, output, forms, vanilla):
    symbols = read_symbols(Path(config['sym']))
    fixture = output / f'{forms}-forms.sav'
    battery(Path(config['battery']), symbols, fixture, forms, not vanilla)
    driver = Driver(config['core'], config['rom'], BOOT, fixture,
                    output / f'{forms}-forms.log')
    def reach(label):
        bank, pc = symbols[label]
        result = driver.command(f'restorerun {bank} {pc} {600 * 70224} 0')
        if result['hit'] < 0:
            raise RuntimeError(f'Timed out reaching {label}')
    def press(key):
        driver.run(frames=2, key=key)
        driver.run(frames=2)
    def memory(label, size=1):
        bank, address = symbols[label]
        return bytes.fromhex(driver.command(f'perfram {bank} {address} {size}')['bytes'])
    records = []
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        press('select')
        reach('Pokedex_UpdateOptionScreen')
        for _ in range(3 if vanilla else 2):
            press('down')
        press('a')
        reach('Pokedex_UpdateUnownMode')
        driver.run(frames=4)
        for step in range(min(forms, 3)):
            name = f'{forms}-forms-{step}'
            path = output / f'{name}.ppm'
            driver.command(f'image {path}')
            with Image.open(path) as image:
                image.save(path.with_suffix('.png'))
            record = dict(requested_step=step, path=str(path.with_suffix('.png')),
                          pixels_sha256=sha256(path.read_bytes()),
                          caught_form_ids=list(memory('wUnownDex', 26)),
                          actual_index=memory('wDexCurUnownIndex')[0],
                          displayed_count=memory('wDexUnownCount')[0])
            if not vanilla:
                ui = driver.command('ui')
                for bank in (0, 1):
                    record[f'bank{bank}_space_tile'] = driver.command(
                        f'inspectvram {bank} 38896 16')['bytes']
                resident = bytes.fromhex(driver.command('inspectvram 1 35664 432')['bytes'])
                start = offset(symbols['UnownFont'])
                original = Path(config['rom']).read_bytes()[start:start + 432]
                record['resident_font_matches'] = resident == bytes(value ^ 255 for value in original)
                (output / f'{name}.json').write_text(json.dumps(ui, indent=2) + '\n')
            records.append(record)
            if step + 1 < min(forms, 3):
                press('right')
                reach('Pokedex_UpdateUnownMode')
                driver.run(frames=4)
    finally:
        driver.close()
    return records


def run(source, output, vanilla_source):
    if not output.is_relative_to(source):
        raise ValueError('Keep comparison fixtures under the private trial directory')
    output.mkdir(parents=True, exist_ok=True)
    configs = {}
    for variant, path in (('production', source / 'baseline'), ('prototype', source)):
        configs[variant] = json.loads((path / 'dex-regression/modern/config.json').read_text())
    folder = output / 'vanilla'
    folder.mkdir(exist_ok=True)
    configs['vanilla'] = dict(core=str(compile_core(vanilla_source, folder)),
                             rom=str(vanilla_source / 'pokecrystal.gbc'),
                             sym=str(vanilla_source / 'pokecrystal.sym'),
                             battery='/Applications/SameBoy/Games/pokecrystal-original.sav')
    records = {}
    for variant, config in configs.items():
        folder = output / variant
        folder.mkdir(exist_ok=True)
        records[variant] = dict(rom_sha256=sha256(Path(config['rom']).read_bytes()),
                               captures={forms: capture(config, folder, forms, variant == 'vanilla')
                                         for forms in (1, 26)})
        print(variant, records[variant]['rom_sha256'], flush=True)
    (output / 'comparison.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--vanilla-source', type=Path, required=True)
    args = parser.parse_args()
    run(args.source.resolve(), args.output.resolve(), args.vanilla_source.resolve())
