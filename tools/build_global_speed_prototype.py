"""Reproducible private whole-game double-speed and Dex ablation builds."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_performance_prototype import ROOT, replace
from dex_timing.assets import sha256

TEMPLATE = ROOT / 'build/dex-performance-20261004/combined-no-lookahead/candidate'


def global_speed(checkout):
    init = checkout / 'home/init.asm'
    replace(init, '\tldh a, [hCGB]\n\tand a\n\tjr z, .no_double_speed\n\tcall NormalSpeed\n.no_double_speed\n', '')
    replace(init, '\tcall ClearWRAM\n', '''; PRIVATE GLOBAL-SPEED PROTOTYPE: stack and hardware flags are now valid,
; interrupts and LCD are off, and ordinary audio has not initialized yet.
\tldh a, [hCGB]
\tand a
\tjr z, .cpu_speed_ready
\tcall DoubleSpeed
.cpu_speed_ready
\tcall ClearWRAM
''')
    dex = checkout / 'engine/pokedex/pokedex.asm'
    replace(dex, 'Pokedex:\n\tldh a, [rKEY1]\n\tpush af\n', 'Pokedex:\n')
    replace(dex, '\tpop af\n\tbit 7, a\n\tret nz\n\tcall DisableLCD\n\tcall PokedexPerf_NormalSpeed\n\tjp EnableLCD', '\tret')
    replace(dex, '\tcall DisableLCD\n\tcall PokedexPerf_DoubleSpeed\n\tcall Pokedex_LoadGFX', '\tcall Pokedex_LoadGFX')
    text = dex.read_text()
    text = text[:text.index('\n; PRIVATE PROTOTYPE: switch only while the LCD is disabled.')]
    dex.write_text(text)
    # Multiplayer is outside the project. Defensive cleanup must not undo
    # the global clock policy if an old mobile routine is reached indirectly.
    for name in ('mobile/mobile_40.asm', 'mobile/mobile_46.asm'):
        path = checkout / name
        replace(path, '\tcall NormalSpeed\n', '\tcall DoubleSpeed\n')
    ram = checkout / 'ram/wram.asm'
    replace(ram, 'wSampledCryBlockPeriod:: db\n', '''wSampledCryBlockPeriod:: db
; PRIVATE GLOBAL-SPEED PROTOTYPE: reuse bank-4 tail padding, not extra RAM.
wSampledCryTimerStep:: db
''')
    timer = checkout / 'home/sampled_cry_player.asm'
    replace(timer, '\tfarcall PokedexPerf_StartBlockTimer\n', '\tfarcall SampledCry_StartBlockTimerROMX\n')
    replace(timer, '.has_decoded_block\n\tcall SampledCry_CopyNextCachedBlock', '.has_decoded_block\n\tcall SampledCry_AlternateBlockTimer\n\tcall SampledCry_CopyNextCachedBlock')
    replace(timer, '\nSampledCry_ClearTimerFlag::', '''
; Odd periods alternate floor/ceil reloads. TIMA already loaded the previous
; TMA at IRQ entry, so this write selects the following interval's reload.
; Standard cries take only the zero-step path; no ROMX call occurs in the IRQ.
SampledCry_AlternateBlockTimer:
\tld a, [wSampledCryTimerStep]
\tand a
\tret z
\tld c, a
\tldh a, [rTMA]
\tadd c
\tldh [rTMA], a
\tld a, c
\tcpl
\tinc a
\tld [wSampledCryTimerStep], a
\tret

SampledCry_ClearTimerFlag::''')
    indexed = checkout / 'engine/pokedex/performance_indexed.asm'
    text = indexed.read_text()
    start = text.index('PokedexPerf_StartBlockTimer::')
    text = text[:start] + '''; PRIVATE GLOBAL-SPEED PROTOTYPE: physical sample cadence is independent
; of CPU speed. Odd periods retain exact average timing rather than rounding.
SampledCry_StartBlockTimerROMX::
\txor a
\tldh [rTAC], a
\tld [wSampledCryTimerStep], a
\tld a, [wSampledCryBlockPeriod]
\tld c, a
\tldh a, [rKEY1]
\tbit 7, a
\tjr z, .normal
\tsrl c
\tjr nc, .normal
\tld a, 1
\tld [wSampledCryTimerStep], a
\txor a
\tsub c
\tldh [rTIMA], a
\tdec a
\tldh [rTMA], a
\tjr .start
.normal
\txor a
\tsub c
\tldh [rTMA], a
\tldh [rTIMA], a
.start
\tcall SampledCry_ClearTimerFlag
\tldh a, [rKEY1]
\tbit 7, a
\tld a, TAC_START | TAC_65KHZ
\tjr z, .timer_ready
\tld a, TAC_START | TAC_16KHZ
.timer_ready
\tldh [rTAC], a
\tret
'''
    indexed.write_text(text)
    entry = checkout / 'engine/pokedex/new_pokedex_entry.asm'
    replace(entry, '\tfarcall NewDexEntry_CancelAnimation\n', '''\tfarcall NewDexEntry_CancelAnimation
; The page owns its nonblocking sampled cry. A faster post-catch return can
; reach naming/other waits before it ends, so cancel it at this handoff.
\tdi
\tldh a, [hSampledCryTimer]
\tand a
\tcall nz, StopSampledCryAsync_NoInterruptControl
\tei
''')


def ablate(checkout, disabled):
    if 'retained' in disabled:
        detail = checkout / 'engine/pokedex/pokedex_detail.asm'
        replace(detail, '\tfarcall PokedexPerf_CacheInfoAcrossArea\n', '')
        info = checkout / 'engine/pokedex/pokedex_info.asm'
        replace(info, '\tcall PokedexPerf_RestoreInfoAcrossArea\n\tjr c, .restored\n', '')
    if 'admission' in disabled:
        base = ROOT / 'build/dex-performance-20261004/speed-v3/candidate/engine/pokedex/pokedex_info.asm'
        original, path = base.read_text(), checkout / 'engine/pokedex/pokedex_info.asm'
        text = path.read_text()
        begin, end = text.index('PokedexInfo_Service:'), text.index('\nPokedexInfo_Initialize:')
        a, b = original.index('PokedexInfo_Service:'), original.index('\nPokedexInfo_Initialize:')
        path.write_text(text[:begin] + original[a:b] + text[end:])
    if 'glyph' in disabled:
        path = checkout / 'engine/pokedex/pokedex_info.asm'
        replace(path, '\tfarcall PokedexPerf_FastCopyTiles\n\tret\nPokedexInfo_CopyTiles_Legacy:\n', '')
    if 'town' in disabled:
        path = checkout / 'engine/pokegear/pokegear.asm'
        replace(path, '\tfarcall PokedexPerf_FastTownGFX\n', '\tcall LoadTownMapGFX\n')
        text = path.read_text()
        for before, after in (('\tfarcall PokedexPerf_FastTownPals\n', '\tcall TownMapPals\n'),
                              ('\tfarcall PokedexPerf_FastTownMap\n', '\tcall TownMapBGUpdate\n')):
            if text.count(before) != 2:
                raise ValueError('Town-map ablation anchor changed')
            text = text.replace(before, after)
        path.write_text(text)
    if 'nests' in disabled:
        path = checkout / 'engine/pokegear/pokegear.asm'
        replace(path, '\tfarcall PokedexPerf_FastNests ; generated landmarks + live roamers\n', '\tfarcall FindNest\n')
    if 'queue' in disabled:
        path = checkout / 'engine/pokedex/pokedex_info.asm'
        replace(path, '\tcall PokedexPerf_QueueInfo\n\tret c\n', '')
    if 'lookahead' in disabled:
        base = ROOT / 'build/dex-performance-20261004/combined/candidate'
        for name in ('engine/pokedex/pokedex_3.asm', 'engine/pokedex/pokedex_animation.asm'):
            shutil.copy2(base / name, checkout / name)


def build(output, disabled, jobs, relink=False):
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Private prototype output must be under build/')
    checkout = output / 'candidate'
    if not relink:
        if checkout.exists():
            raise ValueError('Use a fresh output directory or --relink')
        shutil.copytree(TEMPLATE, checkout, ignore=shutil.ignore_patterns('.git', 'build'))
        shutil.copytree(TEMPLATE / 'build/dex-performance-assets', checkout / 'build/dex-performance-assets')
        global_speed(checkout)
        ablate(checkout, disabled)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j' + str(jobs), 'pokecrystal.gbc'], cwd=checkout,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(checkout / ('pokecrystal.' + ext), output / ('pokecrystal-global-double-speed.' + ext))
    result = dict(template=str(TEMPLATE), disabled=sorted(disabled), output=str(output),
                  rom=str(output / 'pokecrystal-global-double-speed.gbc'),
                  sym=str(output / 'pokecrystal-global-double-speed.sym'),
                  rom_sha256=sha256((checkout / 'pokecrystal.gbc').read_bytes()),
                  production_unchanged=True)
    (output / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--disable', nargs='*', choices=('retained', 'admission', 'glyph', 'town', 'nests', 'queue', 'lookahead'), default=[])
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--relink', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.output, set(args.disable), args.jobs, args.relink)))


if __name__ == '__main__':
    main()
