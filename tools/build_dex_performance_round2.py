"""Private second-round experiments; preserve round-one ROMs and production."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_dex_performance_prototype import ROOT, build, replace
from dex_timing.assets import sha256


def speed(checkout):
    dex = checkout / 'engine/pokedex/pokedex.asm'
    replace(dex, '\nPokedex:\n', '\nPokedex:\n\tldh a, [rKEY1]\n\tpush af\n')
    replace(dex, '\tpop hl\n\tld a, l\n\tldh [hWX], a\n\tld a, h\n\tldh [hWY], a\n\tret',
            '\tpop hl\n\tld a, l\n\tldh [hWX], a\n\tld a, h\n\tldh [hWY], a\n'
            '\tpop af\n\tbit 7, a\n\tret nz\n\tcall DisableLCD\n'
            '\tcall PokedexPerf_NormalSpeed\n\tjp EnableLCD')
    replace(dex, '\tcall ClearTilemap\n\tcall Pokedex_LoadGFX',
            '\tcall ClearTilemap\n\tcall DisableLCD\n\tcall PokedexPerf_DoubleSpeed\n\tcall Pokedex_LoadGFX')
    with dex.open('a') as file:
        file.write('''
; PRIVATE PROTOTYPE: switch only while the LCD is disabled. SwitchSpeed
; clears IE, so restore it before the ordinary owner resumes. No new RAM.
PokedexPerf_DoubleSpeed:
    ldh a, [rIE]
    push af
    call DoubleSpeed
    pop af
    ldh [rIE], a
    ret
PokedexPerf_NormalSpeed:
    ldh a, [rIE]
    push af
    call NormalSpeed
    pop af
    ldh [rIE], a
    ret
''')
    timer = checkout / 'home/sampled_cry_player.asm'
    replace(timer, '\tld a, [wSampledCryBlockPeriod]\n\tld c, a\n\txor a\n\tsub c\n\tldh [rTMA], a',
            '\tld a, [wSampledCryBlockPeriod]\n\tld c, a\n\tldh a, [rKEY1]\n\tbit 7, a\n'
            '\tjr z, .normal_period\n\tsrl c\n\tjr nc, .normal_period\n\tinc c\n.normal_period\n'
            '\txor a\n\tsub c\n\tldh [rTMA], a')
    replace(timer, '\tld a, TAC_START | TAC_65KHZ\n\tldh [rTAC], a\n\tret',
            '\tldh a, [rKEY1]\n\tbit 7, a\n\tld a, TAC_START | TAC_65KHZ\n'
            '\tjr z, .timer_ready\n\tld a, TAC_START | TAC_16KHZ\n.timer_ready\n\tldh [rTAC], a\n\tret')
    text = timer.read_text()
    start = text.index('SampledCry_StartBlockTimer::')
    end = text.index('SampledCry_ClearTimerFlag::', start)
    helper = text[start:end].replace('SampledCry_StartBlockTimer::', 'PokedexPerf_StartBlockTimer::')
    timer.write_text(text[:start] + 'SampledCry_StartBlockTimer::\n\tfarcall PokedexPerf_StartBlockTimer\n\tret\n\n' + text[end:])
    with (checkout / 'engine/pokedex/performance_indexed.asm').open('a') as file:
        file.write('\n' + helper)
    policy = checkout / 'engine/pokedex/pokedex_animation_policy.asm'
    replace(policy, '\tldh a, [rKEY1]\n\tbit 7, a\n\tjr nz, .reject\n', '')
    replace(policy, '\tcp 6\n\tjr z, .fast_timer', '\tcp 7\n\tjr z, .double_timer\n\tcp 6\n\tjr z, .fast_timer')
    replace(policy, '\n.fast_timer\n', '''
.double_timer
    ldh a, [rKEY1]
    bit 7, a
    jr z, .reject
    ldh a, [rTMA]
    cp 156
    jr nz, .reject
    ldh a, [hSampledCryTimer]
    and a
    ld e, 20
    jr z, .time_gate
    call Pokedex_CheckAnimationAudioRunway
    jr nc, .reject
    ld e, 40
    jr .time_gate
.fast_timer
''')
    # Retain the old normal-speed finish bounds as conservative prototype gates.
    # DMA/waits do not speed up. Broader speed-specific bounds are not assumed.
    policy.write_text(policy.read_text().replace('jr nz, .reject', 'jp nz, .reject').replace('jr z, .reject', 'jp z, .reject'))


def retained(checkout):
    shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_retained.asm',
                 checkout / 'engine/pokedex/performance_retained.asm')
    replace(checkout / 'main.asm', 'INCLUDE "engine/pokedex/performance_queue.asm"',
            'INCLUDE "engine/pokedex/performance_queue.asm"\nINCLUDE "engine/pokedex/performance_retained.asm"')
    replace(checkout / 'ram/wram.asm', 'wPokedexInfoWorkspaceEnd::',
            'wPokedexPerfRetainedInfo:: db\nwPokedexInfoWorkspaceEnd::')
    replace(checkout / 'engine/pokedex/pokedex_detail.asm', 'PokedexSelectedMon_Area:\n',
            'PokedexSelectedMon_Area:\n\tfarcall PokedexPerf_CacheInfoAcrossArea\n')
    replace(checkout / 'engine/pokedex/pokedex_info.asm', '\tcall PokedexInfo_Initialize\n.build',
            '\tcall PokedexPerf_RestoreInfoAcrossArea\n\tjr c, .restored\n\tcall PokedexInfo_Initialize\n.build')
    replace(checkout / 'engine/pokedex/pokedex_info.asm', '\tcall PokedexInfo_StageOAM\n\tpop af\n\tldh [rSVBK], a\n\tret',
            '\tcall PokedexInfo_StageOAM\n.restored\n\tpop af\n\tldh [rSVBK], a\n\tret')


def admission(checkout):
    shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_admission.asm',
                 checkout / 'engine/pokedex/performance_admission.asm')
    replace(checkout / 'main.asm', 'INCLUDE "engine/pokedex/performance_queue.asm"',
            'INCLUDE "engine/pokedex/performance_queue.asm"\nINCLUDE "engine/pokedex/performance_admission.asm"')
    info = checkout / 'engine/pokedex/pokedex_info.asm'
    replace(info, '\tcall PokedexPerf_CanBatch\n\tld b, POKEDEX_INFO_SERVICE_SLICES\n\tjr nc, .slice\n\tld b, 6\n.slice',
            '\tld b, 12\n.slice')
    replace(info, '\tldh a, [hVBlankCounter]\n\tld hl, wPokedexAnimLoopTick\n\tcp [hl]\n\tjr nz, .done\n\tldh a, [rLY]\n\tcp POKEDEX_INFO_LATEST_LY\n\tjr nc, .done',
            '\tpush bc\n\tcall PokedexPerf_AdmitInfo\n\tpop bc\n\tjr nc, .done')
    # Bound quiet jobs too: otherwise 12 slices can chase HDMA into another
    # display interval. The same physical guard avoids wasted late uploads.
    replace(info, '\tjr nz, .admit\n\tpush bc\n\tcall PokedexPerf_AdmitInfo',
            '\tjr nz, .quiet_gate\n\tpush bc\n\tcall PokedexPerf_AdmitInfo')
    replace(info, '\tjr nc, .done\n.admit\n',
            '\tjr nc, .done\n\tjr .admit\n.quiet_gate\n\tldh a, [rLY]\n\tcp 96\n\tjr nc, .done\n.admit\n')


def no_lookahead(checkout):
    shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_no_lookahead.asm',
                 checkout / 'engine/pokedex/performance_no_lookahead.asm')
    replace(checkout / 'main.asm', 'INCLUDE "engine/pokedex/pokedex_3.asm"',
            'INCLUDE "engine/pokedex/pokedex_3.asm"\nINCLUDE "engine/pokedex/performance_no_lookahead.asm"')
    path = checkout / 'engine/pokedex/pokedex_3.asm'
    text = path.read_text()
    begin = text.index('\t; Validate the row above the viewport.')
    end = text.index('\t; Validate the top row and the three rows after it.', begin)
    text = text[:begin] + text[end:]
    text = text.replace('\tld c, 4\n.check_forward', '\tld c, POKEDEX_GRID_HEIGHT\n.check_forward')
    begin = text.index('Pokedex_RepairGridCache:')
    end = text.index('\tld hl, wDexListingScrollOffset', text.index('.ensure_previous', begin))
    text = text[:begin] + 'Pokedex_RepairGridCache:\n' + text[end:]
    text = text.replace('\tld c, POKEDEX_GRID_CACHE_ROWS - 1\n.ensure_forward', '\tld c, POKEDEX_GRID_HEIGHT\n.ensure_forward')
    begin = text.index('.prime\n', text.index('Pokedex_PrimeGridCache:'))
    # Select the actual label, not the initial conditional branch.
    begin = text.index('\n.prime\n', begin)
    end = text.index('\nPokedex_CacheGridIconPalette:', begin)
    text = text[:begin] + '''
.prime
    ld hl, wPokedexGridCacheRowOffsets
    ld bc, POKEDEX_GRID_CACHE_ROWS * 2
    ld a, $ff
    call ByteFill
    ld a, 1
    ld [wPokedexGridTopPhysicalRow], a
    jp Pokedex_RepairGridCache
''' + text[end:]
    text = text.replace('Pokedex_FinalizeWrappedGridCache:\n', 'Pokedex_FinalizeWrappedGridCache:\n\tret\nPokedexPerf_LegacyFinalizeWrappedGridCache:\n')
    path.write_text(text)
    path = checkout / 'engine/pokedex/pokedex_animation.asm'
    replace(path, '\tfarcall Pokedex_PrepareGridCacheRefill\n\tfarcall Pokedex_UploadPendingGridCacheRow\n', '')
    replace(path, '\t; Finish every WRAM and shadow-state update before streaming the selection.',
            '\tfarcall PokedexPerf_PrepareIncomingGridRow\n\t; Finish every WRAM and shadow-state update before streaming the selection.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=('control', 'speed', 'retained', 'speed-retained', 'admission', 'speed-admission', 'no-lookahead', 'combined', 'combined-no-lookahead'), required=True)
    parser.add_argument('--jobs', type=int, default=12)
    parser.add_argument('--relink', action='store_true', help='Rebuild an already patched private checkout')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        parser.error('Private outputs must be under build/')
    output.mkdir(parents=True, exist_ok=True)
    if not args.relink:
        build(output, 'batch', args.jobs)
    checkout = output / 'candidate'
    if not args.relink and ('speed' in args.variant or args.variant.startswith('combined')):
        speed(checkout)
    if not args.relink and ('retained' in args.variant or args.variant.startswith('combined')):
        retained(checkout)
    if not args.relink and ('admission' in args.variant or args.variant.startswith('combined')):
        admission(checkout)
    if not args.relink and 'no-lookahead' in args.variant:
        no_lookahead(checkout)
    with (output / 'round2-build.log').open('w') as log:
        subprocess.run(['make', '-s', '-W', 'main.asm', '-W', 'home.asm', '-W', 'ram.asm',
                        '-j' + str(args.jobs), 'main.o', 'home.o', 'ram.o'], cwd=checkout,
                       check=True, stdout=log, stderr=subprocess.STDOUT)
        subprocess.run(['make', '-s', '-W', 'main.o', '-W', 'home.o', '-W', 'ram.o',
                        '-j' + str(args.jobs), 'pokecrystal.gbc'], cwd=checkout,
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    for extension in ('gbc', 'sym', 'map'):
        shutil.copy2(checkout / ('pokecrystal.' + extension),
                     output / (f'pokecrystal-dex-round2-{args.variant}.' + extension))
    provenance = json.loads((output / 'provenance.json').read_text())
    provenance.update(variant=args.variant, round=2,
                      rom_sha256=sha256((checkout / 'pokecrystal.gbc').read_bytes()))
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance))


if __name__ == '__main__':
    main()
