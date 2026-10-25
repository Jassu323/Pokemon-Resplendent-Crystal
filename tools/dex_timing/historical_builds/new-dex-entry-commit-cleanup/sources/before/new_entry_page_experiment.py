"""HOST-ONLY page-two redraw prototype, never an in-place game patch.

Assemble real instructions into verified empty ROMX of a private image and
redirect only NewPokedexEntry's page-two farcall. Existing code/data/state
addresses are unchanged, so authentic catch fixtures can be replayed normally.
"""
import argparse
import json
from pathlib import Path
import subprocess

from .assets import Repository, offset, read_symbols, sha256
from .new_entry import ROOT, FRAME, compile_core, run
from .new_entry_sweep import ADDITIONAL, ORIGINAL, audit

BASE_ROM = '13e85ecf5d6986fbb38e62af0b3e0ea9f3a191fdc38e5c249a57e5eeba3e7a3a'


def compare(output, rom, sym, sameboy, base_rom=None, base_sym=None):
    """Full profiling of paired failures and successful sampled-cry controls.

    The recorded pre-entry states also support the integrated page-two build:
    its changed owner code has not run yet, and live stack/data bindings remain
    compatible. Explicit baseline paths keep a frozen old link separate from
    a newly integrated candidate; catch replay verifies compatibility first.
    """
    base_rom = base_rom or ROOT / 'pokecrystal.gbc'
    base_sym = base_sym or ROOT / 'pokecrystal.sym'
    base = Repository(ROOT, base_rom, base_sym)
    candidate = Repository(ROOT, rom, sym)
    checks = [('mewtwo', n) for n in (11, 30, 35, 36)] + [
        ('exeggcute', 23), ('exeggcute', 24), ('dusknoir', 18)] + [(n, 5) for n in ORIGINAL + ADDITIONAL]
    diagnostic = output / 'diagnostic'
    diagnostic.mkdir(exist_ok=True)
    results = []
    for label, repo, cartridge in (('baseline', base, base_rom),
                                   ('prototype', candidate, rom)):
        directory = diagnostic / label
        directory.mkdir(exist_ok=True)
        binary = compile_core(repo, sameboy, directory, 'trace')
        for species, tick in checks:
            asset = repo.load([species])[0]
            prefix = directory / f'{species}-{tick:03}'
            plan = prefix.with_suffix('.inputs')
            plan.write_text(f'1 {tick} 2 16\n')
            registration = ROOT / 'build/new-dex-entry-integration/results'
            state = registration / f'{species}-registration.s0'
            refs = registration / f'{species}.references'
            if species not in ORIGINAL:
                registration = ROOT / 'build/new-dex-entry-sweep-verified'
                state = registration / f'{species}-generated.s0'
                refs = registration / f'{species}.references'
            trace = run(binary, [cartridge, state, refs, 'plan', plan], prefix, screens=True)
            row = audit(asset, trace, dict(name=f'page-{tick:03}', family='page'))
            desc = next(e for e in trace if e['event'] == 'description' and e['dex_status'] == 1)
            spans = [e for e in trace if e['event'] == 'span']
            span = next(e for e in spans if e['name'] in ('DisplayDexEntry', 'NewDexEntry_DisplayPage2')
                        and e['start'] == desc['t'])
            wait = next(e for e in trace if e['event'] == 'wait_entry' and e['dex_status'] == 1)
            press = next(e for e in trace if e['event'] == 'input' and e['keys'] == 16)
            services = sorted(e['start'] for e in spans if e['name'] == 'NewDexEntry_ServiceAnimation')
            gaps = [b - a for a, b in zip(services, services[1:]) if a <= wait['t'] and b >= desc['t']]
            row.update(build=label, redraw_t=span['end'] - span['start'],
                       redraw_intervals=(span['end'] - span['start']) / FRAME,
                       max_service_gap_t=max(gaps, default=0),
                       input_to_second_wait_t=wait['t'] - press['t'],
                       first_publication_t=next(e['t'] for e in trace if e['event'] == 'published'),
                       ui_snapshots=[e for e in trace if e['event'] == 'ui_snapshot'])
            # Compare rendered text against a settled reference, not just
            # matching copies of an incorrectly constructed software map.
            if label == 'prototype':
                old = diagnostic / 'baseline' / f'{species}-{tick:03}-settled.ppm'
                new = prefix.with_name(prefix.name + '-page2').with_suffix('.ppm')
                a = old.read_bytes().split(b'\n', 3)[3]
                b = new.read_bytes().split(b'\n', 3)[3]
                row['description_pixels_equal'] = a[72 * 160 * 3:120 * 160 * 3] == b[72 * 160 * 3:120 * 160 * 3]
                assert row['description_pixels_equal'], (species, tick, 'Description content changed')
            results.append(row)
    (diagnostic / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(json.dumps({k: row[k] for k in ('build', 'species', 'case', 'status', 'redraw_t',
                                              'max_service_gap_t', 'input_to_second_wait_t')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--audio-points', choices=('all', 'start', 'none'), default='all')
    parser.add_argument('--ack-guard', action='store_true', help='Recheck publication ACK before map construction')
    parser.add_argument('--compare', action='store_true', help='Run paired diagnostic replays after building')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    args = parser.parse_args()
    directory = {'all': 'redraw', 'start': 'start-audio', 'none': 'animation-only'}[args.audio_points]
    if args.ack_guard:
        directory += '-ack-guard'
    output = (args.output or ROOT / 'build/new-entry-page-experiment' / directory).resolve()
    if not output.is_relative_to(ROOT / 'build'):
        parser.error('Private experimental output must stay in ignored build/')
    output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    assert sha256(repo.rom) == BASE_ROM, 'Re-audit code/free-space bindings for this ROM'
    source = ROOT / 'tools/dex_timing/preflight/new_entry_page2.asm'
    names = ('NewDexEntry_ServiceAfterDelayFrame hBGMapMode wTempSpecies '
             'GetDexEntryPointer FarCall GetFarByte wTilemap ClearBox PlaceFarString '
             'ServiceSampledCryAsync hVBlank NewDexEntry_ServiceAnimation wNewDexEntryAnimFlags').split()
    bindings = [f'DEF EXPERIMENT_AUDIO_POINTS EQU {dict(all=3, start=1, none=0)[args.audio_points]}',
                f'DEF EXPERIMENT_ACK_GUARD EQU {int(args.ack_guard)}']
    for name in names:
        bank, address = repo.symbols[name]
        bindings += [f'DEF {name} EQU ${address:04x}', f'DEF B_{name} EQU ${bank:x}']
    service = offset(repo.symbols['NewDexEntry_ServiceAnimation'])
    build = offset(repo.symbols['NewDexEntry_ServiceAnimation.build'])
    flag = repo.symbols['wNewDexEntryAnimFlags'][1]
    assert repo.rom[service + 10:service + 14] == bytes.fromhex('cb 66 28 2c')
    assert repo.rom[build:build + 5] == bytes((0xfa, flag & 255, flag >> 8, 0xcb, 0x4f))
    bindings += [f'DEF OriginalServiceAck EQU ${repo.symbols["NewDexEntry_ServiceAnimation"][1] + 14:04x}',
                 f'DEF OriginalServiceBuild EQU ${repo.symbols["NewDexEntry_ServiceAnimation.build"][1]:04x}']
    (output / 'page2-bindings.asm').write_text('\n'.join(bindings) + '\n')
    subprocess.run(['rgbasm', '-I', str(output) + '/', '-o', str(output / 'page2.o'), str(source)], check=True)
    subprocess.run(['rgblink', '-p', '255', '-o', str(output / 'page2.bin'),
                    '-n', str(output / 'page2.sym'), str(output / 'page2.o')], check=True)
    symbols = read_symbols(output / 'page2.sym')
    begin = offset(symbols['NewDexEntry_DisplayPage2'])
    end = offset(symbols['NewDexEntry_PageExperimentEnd'])
    assert begin < end <= 0x78 * 0x4000
    assert repo.rom[begin:end] == bytes(end - begin), 'Prototype space is not free'
    image = bytearray(repo.rom)
    image[begin:end] = (output / 'page2.bin').read_bytes()[begin:end]
    changed_regions = [(begin, end)]
    guard_bytes = 0
    if args.ack_guard:
        guard_begin = offset(symbols['NewDexEntry_PageACKGuard'])
        guard_end = offset(symbols['NewDexEntry_PageACKGuardEnd'])
        assert repo.rom[guard_begin:guard_end] == bytes(guard_end - guard_begin), 'ACK guard space is not free'
        image[guard_begin:guard_end] = (output / 'page2.bin').read_bytes()[guard_begin:guard_end]
        address = symbols['NewDexEntry_PageACKGuard'][1]
        image[build:build + 3] = bytes((0xc3, address & 255, address >> 8))
        changed_regions += [(guard_begin, guard_end), (build, build + 3)]
        guard_bytes = guard_end - guard_begin
    old_bank, old_address = repo.symbols['DisplayDexEntry']
    old_call = bytes([0x3e, old_bank, 0x21, old_address & 255, old_address >> 8, 0xcf])
    at = offset(repo.symbols['NewPokedexEntry'])
    limit = offset(repo.symbols['NewPokedexEntry.ReturnFromDexRegistration'])
    assert image[at:limit].count(old_call) == 1
    call_at = image.index(old_call, at, limit)
    bank, address = symbols['NewDexEntry_DisplayPage2']
    image[call_at:call_at + 6] = bytes([0x3e, bank, 0x21, address & 255, address >> 8, 0xcf])
    changed_regions += [(call_at, call_at + 6), (0x14d, 0x150)]
    rom = output / 'pokecrystal-page2-experiment.gbc'
    sym = rom.with_suffix('.sym')
    temporary = rom.with_suffix('.tmp.gbc')
    temporary.write_bytes(image)
    subprocess.run(['rgbfix', '-v', str(temporary)], check=True)
    final = temporary.read_bytes()
    assert len(final) == len(repo.rom)
    assert all(any(lo <= i < hi for lo, hi in changed_regions)
               for i, (old, new) in enumerate(zip(repo.rom, final)) if old != new), 'Unexpected ROM edit'
    temporary.replace(rom)
    sym.write_text((ROOT / 'pokecrystal.sym').read_text() + '\n' + (output / 'page2.sym').read_text())
    manifest = dict(base_rom_sha256=BASE_ROM, private_rom_sha256=sha256(rom.read_bytes()),
                    private_sym_sha256=sha256(sym.read_bytes()), source_sha256=sha256(source.read_bytes()),
                    builder_sha256=sha256(Path(__file__).read_bytes()), audio_points=args.audio_points,
                    ack_guard=args.ack_guard, helper_bank=bank, helper_address=address,
                    helper_bytes=end - begin, guard_bytes=guard_bytes,
                    total_added_bytes=end - begin + guard_bytes, changed_regions=changed_regions,
                    call_file_offset=call_at, rom=str(rom), sym=str(sym))
    (output / 'prototype.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))
    if args.compare:
        compare(output, rom, sym, args.sameboy)


if __name__ == '__main__':
    main()
