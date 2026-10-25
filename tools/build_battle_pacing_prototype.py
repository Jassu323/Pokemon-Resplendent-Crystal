"""Build a private phase-paced ROM from the accepted whole-game speed snapshot."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_performance_prototype import ROOT, replace
from dex_timing.assets import sha256

BASE = ROOT / 'build/global-speed-20261004/final'
DEFAULT = ROOT / 'build/battle-pacing-20261004/prototype-v1'
CHARGES = ('Solarbeam', 'DazzlingGleam', 'Superpower', 'ShockWave',
           'WildCharge', 'VoltTackle', 'EnergyBall', 'ShadowBall')


def record(phase, extra, denominator, limit=0):
    assert 0 <= extra <= denominator <= 127 and 0 <= limit <= 255
    return f'\tanim_pace {extra}, {denominator}, {limit}, {phase}\n'


def patch(checkout):
    vblank = checkout / 'home/vblank.asm'
    for label in ('VBlank_Cutscene::', 'VBlank_CutsceneCGB::'):
        replace(vblank, label + '\n', label + '''
; PRIVATE PACING PROTOTYPE: share the physical VBlank clock with battle updates.
\tld hl, hVBlankCounter
\tinc [hl]
''')
    ram = checkout / 'ram/wram.asm'
    replace(ram, 'wBattleAnimUpdatedObjects:: ds NUM_BATTLE_ANIM_STRUCTS * 2\n', '''wBattleAnimUpdatedObjects:: ds NUM_BATTLE_ANIM_STRUCTS * 2

; PRIVATE PACING PROTOTYPE: dedicated persistent state, never the Surf union.
wBattleAnimPaceExtra:: db
wBattleAnimPaceDenominator:: db
wBattleAnimPaceError:: db
wBattleAnimPaceDeadline:: db
wBattleAnimPaceRemaining:: db
; INSTRUMENTATION: phase tag for the read-only host observer, not the delay gate.
wBattleAnimPacePhase:: db
; INSTRUMENTATION: cumulative counts reset at each animation script entry.
wBattleAnimPaceHolds:: dw
wBattleAnimPaceLate:: dw
wBattleAnimPaceEnd::
''')
    commands = checkout / 'engine/battle_anims/anim_commands.asm'
    replace(commands, 'RunBattleAnimScript:\n\tcall ClearBattleAnims\n',
            'RunBattleAnimScript:\n\tcall ClearBattleAnims\n\tcall BattleAnimPacing_Reset\n')
    replace(commands, '.not_rollout\n\tcall BattleAnimDelayFrame\n',
            '.not_rollout\n\tcall BattleAnimPacing_DelayFrame\n')
    replace(commands, '\tdw BattleAnimCmd_EA ; dummy\n', '\tdw BattleAnimPacing_SetPhase ; PRIVATE prototype\n')
    with commands.open('a') as out:
        out.write('\nINCLUDE "engine/battle_anims/pacing_prototype.asm"\n')
    shutil.copy2(ROOT / 'tools/dex_timing/probes/battle_pacing.asm',
                 checkout / 'engine/battle_anims/pacing_prototype.asm')
    macros = checkout / 'macros/scripts/battle_anims.asm'
    with macros.open('a') as out:
        out.write('''
; PRIVATE PACING PROTOTYPE: reuse a dummy opcode only in this test ROM.
MACRO anim_pace
\tassert 0 <= \\1 && \\1 <= \\2 && \\2 <= 127
\tassert 0 <= \\3 && \\3 <= 255
\tdb anim_0xea_command, \\1, \\2, \\3, \\4
ENDM
''')
    scripts = checkout / 'data/moves/animations.asm'
    original = scripts.read_text()
    assert '\tanim_0xea' not in original
    phases = []

    def edit(name, changes):
        nonlocal original
        start = original.index(f'BattleAnim_{name}:\n')
        end = original.find('\nBattleAnim_', start + 1)
        if end == -1:
            end = len(original)
        block = original[start:end]
        for anchor, phase, extra, denominator, limit in changes:
            expected = 3 if name == 'WaterPulse' and phase == 4 else 1
            assert block.count(anchor) == expected, (name, anchor)
            block = block.replace(anchor, record(phase, extra, denominator, limit) + anchor, 1)
            phases.append(dict(move=name, phase=phase, extra=extra, denominator=denominator, limit=limit,
                               anchor=anchor.strip()))
        original = original[:start] + block + original[end:]

    edit('Surf', [('\tanim_bgeffect BATTLE_BG_EFFECT_SURF', 1, 2, 3, 0),
                  ('\tanim_incobj 1\n', 2, 2, 3, 0), ('\tanim_ret\n', 0, 0, 1, 0)])
    edit('WaterPulse', [('\tanim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL', 3, 1, 3, 0),
                        ('\tanim_sound 0, 1, SFX_BUBBLEBEAM\n\tanim_obj BATTLE_ANIM_OBJ_WATER_PULSE_RING', 4, 6, 7, 0),
                        ('\tanim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL\n', 0, 0, 1, 0)])
    edit('DragonDance', [('\tanim_sound 0, 0, SFX_SWORDS_DANCE\n', 5, 10, 81, 81)])
    edit('Thunderbolt', [('\tanim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2\n\tanim_sound',
                         6, 12, 77, 77)])
    edit('Caustic', [('.loop\n\tanim_sound 16, 2, SFX_BUBBLEBEAM\n', 7, 1, 15, 0),
                     ('\tanim_clearobjs\n', 0, 0, 1, 0)])
    for name in CHARGES:
        edit(name, [('\tanim_sound 0, 0, SFX_CHARGE\n', 8, 34, 81, 81)])
    scripts.write_text(original)
    return phases


def build(output, jobs, relink=False):
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Prototype must remain under ignored build/')
    checkout = output / 'candidate'
    before = {str(p): sha256(p.read_bytes()) for p in
              (ROOT / 'pokecrystal.gbc', BASE / 'pokecrystal-global-double-speed.gbc')}
    if not relink:
        if checkout.exists():
            raise ValueError('Use a fresh output or --relink')
        shutil.copytree(BASE / 'candidate', checkout,
                        ignore=shutil.ignore_patterns('.git', 'build', '*.o', 'pokecrystal.gbc',
                                                      'pokecrystal.sym', 'pokecrystal.map'))
        shutil.copytree(BASE / 'candidate/build/dex-performance-assets', checkout / 'build/dex-performance-assets')
        phases = patch(checkout)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'phases.json').write_text(json.dumps(phases, indent=2) + '\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j' + str(jobs), 'pokecrystal.gbc'], cwd=checkout,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(checkout / ('pokecrystal.' + ext), output / ('pokecrystal-battle-paced.' + ext))
    assert before == {p: sha256(Path(p).read_bytes()) for p in before}
    report = dict(baseline=str(BASE), output=str(output), rom=str(output / 'pokecrystal-battle-paced.gbc'),
                  rom_sha256=sha256((checkout / 'pokecrystal.gbc').read_bytes()),
                  unchanged_inputs=before, source=str(checkout))
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--relink', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.jobs, args.relink)))


if __name__ == '__main__':
    main()
