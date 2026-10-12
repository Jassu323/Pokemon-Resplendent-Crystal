"""Native base-only decode coverage, including stale 5/6/7-tile metadata."""
import argparse
import json
from pathlib import Path

from .assets import Repository, sha256
from .move_acquisition import fixture, direct
from .move_persistence import core, boot, call
from .unown_regression import expected_picture
from tools.pokedex_info_assets import constants

STEM = 'pokecrystal-dex-unown-fast'


def test(source, target):
    target.mkdir(parents=True, exist_ok=True)
    repo = Repository(source / 'candidate', source / f'{STEM}.gbc', source / f'{STEM}.sym')
    symbols = repo.symbols
    config = dict(core=str(core(source, STEM, target)), rom=str(repo.rom_path), symbols=symbols)
    driver = boot(config, source / f'{STEM}.sav', target / 'native.log')
    values = constants(source / 'candidate/constants/pokemon_constants.asm')
    rows = []
    try:
        for previous in ('CHIKORITA', 'CHARMELEON', 'TYRANITAR'):
            identifier = direct(driver, symbols, 'GetPokemonIDFromIndex', hl=values[previous])['af'] >> 8
            for form in range(1, 27):
                asset = repo.load(['unown_' + chr(96 + form)])[0]
                for original_letter in (1, 26):
                    driver.command('io 65392 1')
                    fixture(driver, symbols, 'wCurSpecies', [identifier])
                    call(driver, symbols, 'GetBaseData')
                    fixture(driver, symbols, 'wUnownLetter', [original_letter])
                    fixture(driver, symbols, 'wUnownDex', [form] + [0] * 25)
                    fixture(driver, symbols, 'wDexCurUnownIndex', [0])
                    initial = driver.command('run 0 0')
                    result = call(driver, symbols, 'Pokedex_LoadUnownFrontpicTiles')
                    scratch = symbols['wPokedexWRAM0Scratch'][1]
                    picture = bytes.fromhex(driver.command(f'read 0 {scratch} 784')['bytes'])
                    letter_bank, letter = symbols['wUnownLetter']
                    restored = driver.command(f'read {letter_bank} {letter} 1')['bytes'] == f'{original_letter:02x}'
                    bank_ok = all(initial[k] == result[k] for k in ('sp', 'bank', 'svbk', 'sram_enabled', 'sram_bank'))
                    rows.append(dict(previous=previous, form=form, original_letter=original_letter,
                                     correct=picture == expected_picture(asset), restored=restored,
                                     bank_stack_sram_ok=bank_ok))
    finally:
        driver.close()
    result = dict(rom_sha256=sha256(repo.rom), cases=len(rows),
                  failures=sum(not all(r[k] for k in ('correct', 'restored', 'bank_stack_sram_ok'))
                               for r in rows), rows=rows)
    (target / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
    return result


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--negative', action='store_true')
    args = cli.parse_args()
    result = test(args.source.resolve(), args.output.resolve())
    if args.negative:
        assert result['failures'] == 104, result['failures']
    else:
        assert not result['failures'], result['failures']
