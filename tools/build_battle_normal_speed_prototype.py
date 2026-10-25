"""Private double-speed game with a normal-speed battle ownership envelope."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

# Existing build helpers support direct-script imports from the tools root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dex_performance_prototype import ROOT, replace
from dex_timing.assets import sha256

TEMPLATE = ROOT / 'build/global-speed-20261004/final/candidate'
OUTPUT = ROOT / 'build/battle-normal-speed-20261004/prototype'
BASE_SHA = '5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90'

ENTRY = '''
; PRIVATE BATTLE-SPEED PROTOTYPE: the transition has already made the BG
; black. Nested battle menus, catching and registration inherit normal speed.
BattleSpeed_EnterNormal::
\tldh a, [hCGB]
\tand a
\tret z
\tldh a, [rKEY1]
\tbit 7, a
\tret z
\tcall WaitSFX
\tcall DisableLCD
\tdi
\tldh a, [rIE]
\tpush af
\tldh a, [hSampledCryTimer]
\tand a
\tcall nz, StopSampledCryAsync_NoInterruptControl
\txor a
\tldh [rNR52], a
\tcall NormalSpeed
\tcall InitSound
\tpop af
\tldh [rIE], a
\tcall EnableLCD
\tei
; The pre-wipe battle track is deliberately restarted at this hidden handoff.
\tjp PlayBattleMusic

; Called only by map setup after its existing DisableLCD. Leave the LCD off
; for the original graphics reload. No switch occurs on a visible battlefield.
BattleSpeed_LeaveNormal::
\tldh a, [hCGB]
\tand a
\tret z
\tldh a, [rKEY1]
\tbit 7, a
\tret nz
\tdi
\tldh a, [rIE]
\tpush af
\tldh a, [hSampledCryTimer]
\tand a
\tcall nz, StopSampledCryAsync_NoInterruptControl
\txor a
\tldh [rNR52], a
\tcall DoubleSpeed
\tcall InitSound
\tpop af
\tldh [rIE], a
\tei
\tret
'''


def install_dispatch(checkout):
    timer = checkout / 'home/sampled_cry_player.asm'
    old = '.has_decoded_block\n\tcall SampledCry_AlternateBlockTimer\n'
    if old in timer.read_text():
        replace(timer, old, '.has_decoded_block\n')
    mobile = checkout / 'home/mobile.asm'
    replace(mobile, '\tand a\n\tjr nz, .sampled_cry_timer\n\tpop af\n\treti\n', '''; Active value 1 takes the original normal/even-period IRQ budget.
\tdec a
\tjr z, .sampled_cry_timer
\tinc a
\tjr z, .inactive
\tpush bc
\tpush de
\tpush hl
\tcall SampledCry_AsyncTimerTickAlternating
\tjr .restore
.inactive
\tpop af
\treti
''')
    replace(mobile, '\tcall SampledCry_AsyncTimerTick\n\n\tpop hl',
            '\tcall SampledCry_AsyncTimerTick\n\n.restore\n\tpop hl')
    replace(timer, '\nSampledCry_AsyncTimerTick::', '''
; Only double-speed odd-period cries need the extra timer reload work.
SampledCry_AsyncTimerTickAlternating::
\tldh a, [rSVBK]
\tpush af
\tld a, BANK(wSampledCryCacheCount)
\tldh [rSVBK], a
\tcall SampledCry_AlternateBlockTimer
\tpop af
\tldh [rSVBK], a
\tjp SampledCry_AsyncTimerTick

SampledCry_AsyncTimerTick::''')
    indexed = checkout / 'engine/pokedex/performance_indexed.asm'
    replace(indexed, '\tld [wSampledCryTimerStep], a\n\txor a\n\tsub c\n',
            '\tld [wSampledCryTimerStep], a\n\tinc a\n\tldh [hSampledCryTimer], a\n\txor a\n\tsub c\n')


def build(output=OUTPUT, jobs=24, relink=False):
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Private output must be under build/')
    checkout = output / 'candidate'
    production = sha256((ROOT / 'pokecrystal.gbc').read_bytes())
    if not relink:
        if checkout.exists():
            raise ValueError('Use a fresh output directory or --relink')
        if sha256((TEMPLATE / 'pokecrystal.gbc').read_bytes()) != BASE_SHA:
            raise ValueError('Accepted unretimed baseline changed')
        shutil.copytree(TEMPLATE, checkout, ignore=shutil.ignore_patterns('.git', 'build'))
        shutil.copytree(TEMPLATE / 'build/dex-performance-assets', checkout / 'build/dex-performance-assets')
        start = checkout / 'engine/battle/start_battle.asm'
        replace(start, '\tpredef DoBattleTransition\n',
                '\tpredef DoBattleTransition\n\tcall BattleSpeed_EnterNormal\n')
        start.write_text(start.read_text() + ENTRY)
        commands = checkout / 'data/maps/setup_script_pointers.asm'
        replace(commands, '\tadd_mapsetup DisableLCD ; 01\n',
                'DisableLCD_MapSetupCmd:\n\tdba BattleSpeed_MapDisableLCD ; 01: same command ID\n')
        setup = checkout / 'engine/overworld/map_setup.asm'
        setup.write_text(setup.read_text() + '''
; PRIVATE BATTLE-SPEED PROTOTYPE: all post-battle reload/whiteout paths use
; map setup. Ordinary map transitions already run double speed and return fast.
BattleSpeed_MapDisableLCD::
\tcall DisableLCD
\tld a, [wBattleMode]
\tand a
\tret nz
\tfarcall BattleSpeed_LeaveNormal
\tret
''')
        # Normal-speed playback keeps the production active-IRQ budget. The
        # extra floor/ceil reload work belongs only to double-speed odd periods.
        timer = checkout / 'home/sampled_cry_player.asm'
        replace(timer, '.has_decoded_block\n\tcall SampledCry_AlternateBlockTimer\n',
                '.has_decoded_block\n')
        install_dispatch(checkout)
    elif 'SampledCry_AsyncTimerTickAlternating::' not in (checkout / 'home/sampled_cry_player.asm').read_text():
        install_dispatch(checkout)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j' + str(jobs), 'pokecrystal.gbc'], cwd=checkout,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(checkout / ('pokecrystal.' + ext),
                     output / ('pokecrystal-battle-normal-speed.' + ext))
    if sha256((ROOT / 'pokecrystal.gbc').read_bytes()) != production:
        raise RuntimeError('Production ROM changed')
    record = dict(template=str(TEMPLATE), template_sha256=BASE_SHA, output=str(output),
        rom=str(output / 'pokecrystal-battle-normal-speed.gbc'),
        sym=str(output / 'pokecrystal-battle-normal-speed.sym'),
        root=str(checkout), rom_sha256=sha256((checkout / 'pokecrystal.gbc').read_bytes()),
        production_sha256=production, production_unchanged=True,
        boundary='normal after black battle wipe; double during map-setup LCD-off reload',
        retiming=False, normal_sample_irq='original active-path instruction budget',
        sampled_active_values='0 inactive; 1 normal/even; 2 double-speed alternating')
    (output / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--relink', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.jobs, args.relink), indent=2))


if __name__ == '__main__':
    main()
