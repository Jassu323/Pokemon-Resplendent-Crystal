"""Create a declared unseen-party fixture for manual first-use policy review."""
import argparse
import json
from pathlib import Path

from .assets import Repository, sha256
from .cold_listing import ROOT
from .global_review_save import create
from .move_persistence import boot, call, core, read
from .move_acquisition import ram, live_indices
from move_discovery_assets import move_bitmap, seed_records, decode_record
from build_move_discovery_prototype import publish_copy

STEM = 'pokecrystal-dex-moves-battle-use'
PARTY = (
    ('SMEARGLE', 'CALL', ('SKETCH', 'METRONOME', 'MIRROR_MOVE', 'TRANSFORM')),
    ('SNORLAX', 'FOCUS', ('FOCUS_PUNCH', 'SLEEP_TALK', 'REST', 'BODY_SLAM')),
    ('CHARIZARD', 'CHARGE', ('FLY', 'SOLARBEAM', 'SKULL_BASH', 'RAZOR_WIND')),
    ('DIGLETT', 'FIRSTUSE', ('DIG', 'SKY_ATTACK', 'POUND', 'SURF')),
    ('LUXRAY', 'REGULAR', ('THUNDERBOLT', 'CAUSTIC', 'DRAGON_DANCE', 'WATER_PULSE')),
    ('MEGANIUM', 'COPY', ('MIMIC', 'POISONPOWDER', 'TACKLE', 'REFLECT')),
)


def run(output):
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    repo = Repository(output / 'candidate', output / f'{STEM}.gbc', output / f'{STEM}.sym')
    target = output / 'battle-review'
    target.mkdir(exist_ok=True)
    report = create(repo, output / f'{STEM}.sav', target / f'{STEM}.sav', PARTY,
                    extra_moves=tuple(m for _, _, moves in PARTY for m in moves))
    save = target / f'{STEM}.sav'
    save.write_bytes(seed_records(save.read_bytes(), repo.symbols, move_bitmap([])))
    publish_copy(output / f'{STEM}.gbc', target / f'{STEM}.gbc')
    config = dict(rom=str(repo.rom_path), symbols=repo.symbols, core=str(core(output, target_root=target)))
    driver = boot(config, save, target / 'cold-verify.log')
    try:
        if read(driver, repo.symbols)[:64] != bytes(64):
            raise AssertionError('Unseen-party review fixture did not load empty')
        actual = [live_indices(driver, repo.symbols, ram(driver, repo.symbols, f'wPartyMon{n}Moves', 4))
                  for n in range(1, 7)]
        from tools.pokedex_info_assets import constants
        values = constants(ROOT / 'constants/move_constants.asm')
        if actual != [[values[n] for n in moves] for _, _, moves in PARTY]:
            raise AssertionError('Manual battle review party differs')
        call(driver, repo.symbols, 'SaveGameData')
        driver.command(f'battery {save}')
    finally:
        driver.close()
    for prefix in ('s', 'sBackup'):
        if decode_record(save.read_bytes(), repo.symbols, prefix) != dict(status='valid', bitmap=bytes(64)):
            raise AssertionError('Manual battle review did not preserve valid empty record')
    driver = boot(config, save, target / 'saved-cold-reload.log')
    try:
        if read(driver, repo.symbols)[:64] != bytes(64):
            raise AssertionError('Saved manual review fixture did not cold-reload empty')
        reloaded = [live_indices(driver, repo.symbols, ram(driver, repo.symbols, f'wPartyMon{n}Moves', 4))
                    for n in range(1, 7)]
        if reloaded != actual:
            raise AssertionError('Saved manual review party did not survive cold reload')
        snapshot = target / 'cold-loaded-box.sav'
        driver.command(f'battery {snapshot}')
        data = snapshot.read_bytes()

        def sram(label, size=1):
            bank, address = repo.symbols[label]
            at = bank * 8192 + address - 0xa000
            return data[at:at + size]

        boxed = report['records'][6:]
        if sram('sBoxCount')[0] != len(boxed):
            raise AssertionError('Cold-loaded manual PC count differs')
        for n, record in enumerate(boxed, 1):
            moves = live_indices(driver, repo.symbols, sram(f'sBoxMon{n}Moves', 4))
            if moves != [values[name] for name in record['moves']]:
                raise AssertionError(f'Cold-loaded manual PC moves differ: {n}')
    finally:
        driver.close()
    report['configured_before_discovery_seed_sha256'] = report.pop('sha256')
    report.update(rom_sha256=manifest['rom_sha256'], save_sha256=sha256(save.read_bytes()),
                  fixture='Deliberately valid empty discovery records with a preconfigured party/PC. This is not natural acquisition.',
                  party_indices=actual, cold_reload_verified=True,
                  cold_reload_pc_pokemon_verified=len(boxed),
                  cold_reload_pc_moves_verified=sum(len(r['moves']) for r in boxed), issues=[])
    report['sha256'] = report['save_sha256']
    save.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    (target / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('rom_sha256', 'save_sha256', 'moves', 'pokemon', 'issues')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output.resolve())


if __name__ == '__main__':
    main()
