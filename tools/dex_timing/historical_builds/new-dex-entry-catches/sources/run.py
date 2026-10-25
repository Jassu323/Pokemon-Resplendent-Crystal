"""Temporary, read-only capture-fixture validation and baseline collection."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = Path(os.environ.get('REGISTRATION_OUT', SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
SAMEBOY = Path.home() / 'Documents/GitHub/SameBoy'
GAMES = Path('/Applications/SameBoy/Games')
EXPECTED_ROM = os.environ.get('REGISTRATION_ROM_SHA256', '407c4d29e08a47c5e5cce165eb4d171b62d4afbced665938950aa0a21b5d9fd3')
CASES = json.loads(os.environ.get('REGISTRATION_CASES', '[[1,"Luxray",338],[2,"Caterpie",10],[3,"Metagross",329],[4,"Dusknoir",316]]'))
sys.path.insert(0, str(ROOT))
from tools.dex_timing.assets import read_symbols

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

symbols = read_symbols(ROOT / 'pokecrystal.sym')

rom = OUT / 'fixture.gbc'
assert digest(GAMES / 'pokecrystal.gbc') == EXPECTED_ROM
shutil.copy2(GAMES / 'pokecrystal.gbc', rom)
shutil.copy2(ROOT / 'pokecrystal.sym', OUT / 'fixture.sym')
shutil.copy2(ROOT / 'pokecrystal.map', OUT / 'fixture.map')

fields = '''wPokeAnimSceneIndex wPokeAnimIdleFlag wPokeAnimCommand wPokeAnimParameter
wPokeAnimWaitCounter hSampledCryTimer hSampledCryBlocks wFrameCounter wWildMon
wPokemonIndexTableEntries wCurItem wTempEnemyMonSpecies wEnemyMonSpecies
wPartyCount wPokedexSeen wPokedexCaught'''.split()
events = {
    'caught': ('PokeBallEffect.caught', False),
    'experience': ('ApplyExperienceAfterEnemyCaught', False),
    'level_up': ('LevelUpHappinessMod', False),
    'entry': ('NewPokedexEntry', False),
    'setup': ('_NewPokedexEntry', True),
    'wait_entry': ('NewPokedexEntry.WaitPressAorB_AnimateFrontpic', True),
    'script_frame': ('PokeAnim_GetFrame', True),
    'script_end': ('PokeAnim_End', True),
    'animation_finished': ('PokeAnim_Finish', True),
    'audio_empty': ('@audio_empty', True),
    'audio_stop': ('StopSampledCryAsync_NoInterruptControl', True),
}
bank, decoded = symbols['SampledCry_AsyncTimerTick.has_decoded_block']
stop = symbols['StopSampledCryAsync_NoInterruptControl'][1]
assert rom.read_bytes()[decoded - 6:decoded] == bytes((0xf1, 0xe0, 0x70, 0xc3, stop & 255, stop >> 8))
symbols['@audio_empty'] = bank, decoded - 6
lines = [f'#define S_{name} 0x{symbols[name][1]:04x}' for name in fields]
entry_bank, entry = symbols['NewPokedexEntry']
lines += [f'#define B_ENTRY {entry_bank}', f'#define P_ENTRY 0x{entry:04x}',
          'static const struct { const char *name; unsigned bank, pc, owner_only; } points[] = {']
for event, (name, only) in events.items():
    bank, pc = symbols[name]
    lines += [f'{{"{event}", {bank}, 0x{pc:04x}, {int(only)}}},']
lines += ['};']
header = OUT / 'symbols.h'
header.write_text('\n'.join(lines) + '\n')
core = OUT / 'capture-probe'
files = ('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
         'sm83_cpu timing workboy').split()
subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(SAMEBOY), '-DGB_INTERNAL',
    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="dex-catch-baseline"',
    '-include', str(header), str(SOURCE / 'capture_probe.c'),
    *(str(SAMEBOY / 'Core' / f'{name}.c') for name in files), '-o', str(core)], check=True)

manifest = {'rom_sha256': digest(rom), 'sym_sha256': digest(OUT / 'fixture.sym'),
            'sameboy_commit': subprocess.check_output(['git', '-C', str(SAMEBOY), 'rev-parse', 'HEAD'], text=True).strip(),
            'fixtures': []}
for slot, name, index in CASES:
    state = OUT / f'{name.lower()}-catch.s{slot}'
    shutil.copy2(GAMES / f'pokecrystal.s{slot}', state)
    capture = OUT / f'{name} Catch.txt'
    shutil.copy2(Path.home() / 'Downloads' / capture.name, capture)
    logfile = OUT / f'{name.lower()}.jsonl'
    with logfile.open('w') as output, (OUT / f'{name.lower()}.stderr').open('w') as errors:
        result = subprocess.run([str(core), str(rom), str(state),
            str(OUT / f'{name.lower()}-registration.s0'), str(OUT / f'{name.lower()}.ppm')],
            stdout=output, stderr=errors, timeout=120)
    records = [json.loads(line) for line in logfile.read_text().splitlines()]
    assert records[0]['species'] == index, records[0]
    assert records[0]['caught'] == 0 and records[0]['seen'] == 1, records[0]
    assert records[0]['item'] == 1, records[0]
    info = {'species': name, 'index': index, 'slot': slot, 'state_sha256': digest(state),
            'capture_sha256': digest(capture), 'exit_code': result.returncode,
            'initial': records[0], 'events': [r for r in records[1:] if r['event'] != 'script_frame']}
    manifest['fixtures'].append(info)
    print(json.dumps(info), flush=True)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
assert all(f['exit_code'] == 0 for f in manifest['fixtures'])
