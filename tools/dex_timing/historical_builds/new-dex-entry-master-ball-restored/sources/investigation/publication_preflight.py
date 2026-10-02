"""Private diagnostic only: fixed-destination publication helpers in free ROMX."""
import json
from pathlib import Path
import subprocess

from tools.dex_timing.assets import Repository, offset, read_symbols, sha256
from tools.dex_timing.cpu import CounterCPU
from tools.dex_timing.new_entry import ROOT, audit_trace, compile_core, run
from tools.dex_timing.new_entry_sweep import ADDITIONAL, ORIGINAL

OUT = Path(__file__).resolve().parent
LIVE_ROM = Path('/Applications/SameBoy/Games/pokecrystal.gbc')
BASE_HASH = '546f053f8137bf7d1f780268762d431d00e1f0ae4c8edf0dec789e9aeb1a7a10'
repo = Repository(ROOT, LIVE_ROM, ROOT / 'pokecrystal.sym')
assert sha256(repo.rom) == BASE_HASH
source = OUT / 'publication-preflight.asm'
subprocess.run(['rgbasm', '-o', str(OUT / 'publication.o'), str(source)], check=True)
subprocess.run(['rgblink', '-p', '255', '-o', str(OUT / 'publication.bin'),
                '-n', str(OUT / 'publication.sym'), str(OUT / 'publication.o')], check=True)
private = read_symbols(OUT / 'publication.sym')
start = offset(private['PrivateCopyMap'])
end = offset(private['PrivateFillAttrsEnd'])
assert repo.rom[start:end] == bytes(end - start)
image = bytearray(repo.rom)
image[start:end] = (OUT / 'publication.bin').read_bytes()[start:end]
symbols = dict(repo.symbols)
changes = [(start, end), (0x14d, 0x150)]
copy = offset(symbols['NewDexEntry_PublishAnimation.copy'])
published = offset(symbols['NewDexEntry_PublishAnimation.published'])
for original, replacement in [('NewDexEntry_CopyVRAMMap', 'PrivateCopyMap'),
                               ('NewDexEntry_FillVRAMAttrs', 'PrivateFillAttrs')]:
    old = symbols[original][1]
    target = private[replacement]
    call = bytes((0xcd, old & 255, old >> 8))
    assert image[copy:published].count(call) == 1
    at = image.index(call, copy, published)
    image[at + 1:at + 3] = target[1].to_bytes(2, 'little')
    changes.append((at + 1, at + 3))
    symbols[original] = target
cutoff = offset(symbols['NewDexEntry_PublishAnimation.cutoff'])
assert image[cutoff - 2:cutoff] == bytes((6, 148))
image[cutoff - 1] = 150
changes.append((cutoff - 1, cutoff))
rom = OUT / 'private-publication-preflight.gbc'
sym = rom.with_suffix('.sym')
rom.write_bytes(image)
subprocess.run(['rgbfix', '-v', str(rom)], check=True)
sym.write_text('\n'.join(f'{bank:02x}:{address:04x} {name}'
                         for name, (bank, address) in symbols.items()) + '\n')
candidate = Repository(ROOT, rom, sym)
assert all(any(lo <= i < hi for lo, hi in changes)
           for i, (a, b) in enumerate(zip(repo.rom, candidate.rom)) if a != b)

# Unit instruction cost, including exactly the same caller path as the game.
costs = {}
for name, flags in [('map', 3), ('first', 11), ('finish', 7)]:
    cpu = CounterCPU(candidate.rom, candidate.symbols)
    cpu.allowed_io.add(0xff44)
    cpu.ram[0xff44], cpu.ram[0xff70], cpu.ram[0xff4f] = 149, 6, 1
    for field, value in [('wNewDexEntryAnimFlags', flags), ('wNewDexEntryAnimDuration', 5),
                         ('wNewDexEntryAnimDeadline', 0xfe), ('hVBlankCounter', 0xfe)]:
        cpu.field(field, value)
    cpu.record_writes = True
    cpu.run('NewDexEntry_PublishAnimation')
    sample = [t for t, at, _ in cpu.io_reads if at == 0xff44][-1]
    writes = [(t, at, v) for t, at, v in cpu.writes if 0x9821 <= at < 0x9900]
    assert len(writes) == (49 if name == 'map' else 98)
    expected = [0x9821 + y * 32 + x for y in range(7) for x in range(7)]
    assert [at for _, at, _ in writes] == expected * (1 if name == 'map' else 2)
    if name != 'map':
        assert all(v == (9 if name == 'first' else 1) for _, _, v in writes[49:])
    last_write = writes[-1][0] + 8 - sample
    assert last_write < 1824
    assert (cpu.ram[0xff70], cpu.ram[0xff4f]) == (6, 1)
    costs[name] = dict(last_write_t=last_write, conservative_available_t=1824,
                       write_margin_t=1824 - last_write, post_sample_t=cpu.cycles - sample)

binary = compile_core(candidate, Path.home() / 'Documents/GitHub/SameBoy', OUT, 'trace')
rows = []
for species in ORIGINAL + ADDITIONAL:
    if species in ORIGINAL:
        directory = ROOT / 'build/new-dex-entry-master-ball-restored'
        if not (directory / f'{species}-registration.s0').exists():
            directory = ROOT / 'build/new-dex-entry-master-ball-restored-expanded'
        state = directory / f'{species}-registration.s0'
        refs = ROOT / 'build/new-dex-entry-page2-integration/catches' / f'{species}.references'
    else:
        directory = ROOT / 'build/new-dex-entry-page2-integration/full'
        state = directory / f'{species}-generated.s0'
        refs = directory / f'{species}.references'
    asset = candidate.load([species])[0]
    for mode in (0, 1, 2):
        trace = run(binary, [rom, state, refs, mode], OUT / f'private-{species}-{mode}')
        row = audit_trace(asset, trace, mode)
        row.update(state=str(state), state_sha256=sha256(state.read_bytes()))
        rows.append(row)
        print(json.dumps(row), flush=True)

# The older, passing Dusknoir entry has a different PPU/audio phase.
directory = ROOT / 'build/new-dex-entry-page2-integration/catches'
for mode in (0, 1, 2):
    trace = run(binary, [rom, directory / 'dusknoir-registration.s0',
                        directory / 'dusknoir.references', mode], OUT / f'private-dusknoir-prior-{mode}')
    row = audit_trace(candidate.load(['dusknoir'])[0], trace, mode)
    row['state'] = str(directory / 'dusknoir-registration.s0')
    row['state_sha256'] = sha256((directory / 'dusknoir-registration.s0').read_bytes())
    rows.append(row)

report = dict(base_rom_sha256=BASE_HASH, private_rom_sha256=sha256(candidate.rom),
              source_sha256=sha256(source.read_bytes()), builder_sha256=sha256(Path(__file__).read_bytes()),
              helper_payload_bytes=end - start, replacement_growth_bytes=end - start - 34 - 29,
              costs=costs, changes=changes, cases=rows)
(OUT / 'private-preflight-report.json').write_text(json.dumps(report, indent=2) + '\n')
assert sha256(LIVE_ROM.read_bytes()) == BASE_HASH
print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
