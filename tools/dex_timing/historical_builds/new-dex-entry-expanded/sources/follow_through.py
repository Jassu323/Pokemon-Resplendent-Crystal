"""Private replay through registration, nickname decline and catch storage."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'build/new-dex-entry-catches'
SAMEBOY = Path.home() / 'Documents/GitHub/SameBoy'
sys.path.insert(0, str(ROOT))
from tools.dex_timing.assets import read_symbols, sha256

symbols = read_symbols(OUT / 'fixture.sym')
draft = read_symbols(OUT / 'draft.sym')
fixtures = json.loads((OUT / 'manifest.json').read_text())['fixtures']
fields = '''wPokeAnimSceneIndex wPokeAnimIdleFlag wPokeAnimCommand wPokeAnimParameter
wPokeAnimWaitCounter hSampledCryTimer hSampledCryBlocks wFrameCounter wWildMon
wPokemonIndexTableEntries wCurItem wTempEnemyMonSpecies wEnemyMonSpecies
wPartyCount wPokedexSeen wPokedexCaught wPartySpecies sBoxCount sBoxSpecies
hVBlank hMapAnims hSCX'''.split()
files = ('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
         'sm83_cpu timing workboy').split()
report = []
for variant in ('baseline', 'resident', 'resident-bulk'):
    rom = OUT / ('fixture.gbc' if variant == 'baseline' else variant + '-private.gbc')
    points = [
        ('caught', symbols['PokeBallEffect.caught']),
        ('experience', symbols['ApplyExperienceAfterEnemyCaught']),
        ('level_up', symbols['LevelUpHappinessMod']),
        ('entry', symbols['NewPokedexEntry']),
        ('animation_finished', symbols['PokeAnim_Finish'] if variant == 'baseline' else draft['ProtoCompleted']),
        ('registration_return', symbols['PokeBallEffect.skip_pokedex']),
        ('send_to_pc', symbols['PokeBallEffect.SendToPC']),
        ('catch_return', symbols['PokeBallEffect.return_from_capture']),
    ]
    header = OUT / 'flow_symbols.h'
    lines = ['#define FOLLOW_THROUGH_AUDIT 1']
    lines += [f'#define S_{name} 0x{symbols[name][1]:04x}' for name in fields]
    bank, pc = symbols['NewPokedexEntry']
    lines += [f'#define B_ENTRY {bank}', f'#define P_ENTRY 0x{pc:04x}',
              f'#define B_sBoxCount {symbols["sBoxCount"][0]}',
              'static const struct { const char *name; unsigned bank, pc, owner_only; } points[] = {']
    lines += [f'{{"{name}", {bank}, 0x{pc:04x}, 0}},' for name, (bank, pc) in points]
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    binary = OUT / (variant + '-flow')
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(SAMEBOY), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING',
                    '-DGB_VERSION="registration-flow"', '-include', str(header),
                    str(SOURCE / 'capture_probe.c'),
                    *(str(SAMEBOY / 'Core' / (name + '.c')) for name in files),
                    '-o', str(binary)], check=True)
    for fixture in fixtures:
        name, slot = fixture['species'].lower(), fixture['slot']
        prefix = OUT / f'{name}-{variant}-flow'
        with prefix.with_suffix('.jsonl').open('w') as output, prefix.with_suffix('.stderr').open('w') as error:
            process = subprocess.run([str(binary), str(rom), str(OUT / f'{name}-catch.s{slot}'),
                                      str(prefix.with_suffix('.s0')), str(prefix.with_suffix('.ppm')),
                                      'follow-through'], stdout=output, stderr=error, timeout=120)
        records = [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]
        assert process.returncode == 0, (variant, name, records[-3:])
        result = next(e for e in records if e['event'] == 'catch_result')
        initial_party = fixture['initial']['party']
        pc_branch = initial_party == 6
        assert result['returned'] and result['caught']
        assert result['party'] == min(initial_party + 1, 6)
        assert result['first_box_species' if pc_branch else 'last_party_species'] == fixture['index']
        assert any(e['event'] == 'send_to_pc' for e in records) == pc_branch
        assert any(e['event'] == 'level_up' for e in records) == (name in ('garchomp', 'exeggcute'))
        assert result['hvblank'] != 0x88 and result['frame_counter'] == 0
        item = dict(species=name, variant=variant, rom_sha256=sha256(rom.read_bytes()),
                    result=result, level_up=any(e['event'] == 'level_up' for e in records),
                    pc_branch=pc_branch)
        report.append(item)
        print(name, variant, result, flush=True)

for species in {r['species'] for r in report}:
    outcomes = [r['result'] for r in report if r['species'] == species]
    assert all(outcome == outcomes[0] for outcome in outcomes), (species, outcomes)
(OUT / 'follow-through-audit.json').write_text(json.dumps(report, indent=2) + '\n')
