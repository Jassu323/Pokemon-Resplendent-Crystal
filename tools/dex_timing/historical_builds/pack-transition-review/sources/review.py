"""Read-only Pack pouch capture using the existing isolated SameBoy driver."""
import json
from pathlib import Path
import shutil

from tools.dex_timing import cold_listing as cold
from tools.dex_timing.assets import Repository, offset, sha256
from tools.dex_timing.listing_restoration import FIELDS

ROOT = cold.ROOT
OUT = ROOT / 'build/pack-transition-review'
OUT.mkdir(parents=True, exist_ok=True)
ROM = ROOT / 'build/dex-internal-transitions-integrated/cold/input-copy.gbc'
repo = Repository(ROOT, ROM, ROOT / 'pokecrystal.sym')
ROM_HASH = sha256(repo.rom)
BATTERY = ROOT / 'build/dex-internal-transitions-integrated/cold/input-copy.sav'
shutil.copy2(BATTERY, OUT / 'input-copy.sav')
BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
SOURCE = Path('/Users/jakeadams/Documents/GitHub/SameBoy')

start = repo.symbols['Pack_RedrawCurrentPocketShell']
end = repo.symbols['Pack_ShellPocketMenu']
code = repo.rom[offset(start):offset(end)]
target = repo.symbols['Pack_LoadAdjacentItemIconRows'][1]
call = bytes((0xcd, target & 255, target >> 8))
assert code.count(call) == 1
repo.symbols['HostPackRedrawDone'] = start[0], start[1] + code.index(call) + 3
cold.POINTS.update(pack_loop='Pack.loop', pack_ready='HostPackRedrawDone',
                   pack_switch='Pack_ShellPocketMenu.switch_pocket')
phases = dict(switch='Pack_ShellPocketMenu.switch_pocket',
              redraw='Pack_RedrawCurrentPocketShell',
              name_upload='Pack_LoadCurrentPocketNameGFX',
              shell='Pack_DrawShellNoCursor_BlankIcons',
              pack_upload='DrawPackGFX', maps='Pack_TransferTilemapAndAttrmap',
              icons='Pack_DrawVisibleItemIconsDeferredOAM',
              palette='Pack_ApplyVisibleItemIconPalettes',
              text='Pack_PrintSelectedItemText',
              adjacent='Pack_LoadAdjacentItemIconRows', ready='HostPackRedrawDone')
header = OUT / 'observer-symbols.h'
lines = [f'#define R_{name} 0x{repo.symbols[name][1]:04x}' for name in FIELDS]
lines += [f'#define R_wPokedexGridCells 0x{repo.symbols["wPokedexGridOccupied"][1]:04x}',
          '#define R_GRID_USES_PRESENCE 1',
          'static const struct { unsigned bank, pc; const char *name; } restoration_points[] = {']
for name, label in phases.items():
    bank, pc = repo.symbols[label]
    lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
lines.append('};')
header.write_text('\n'.join(lines) + '\n')
core = cold.build_core(repo, SOURCE, OUT,
    ('-DDEX_LISTING_RESTORE_TRACE', '-DDEX_INTERNAL_TRANSITION_TRACE',
     f'-DDEX_LISTING_RESTORE_SYMBOLS="{header}"'))
driver = cold.Driver(core, ROM, BOOT, OUT / 'input-copy.sav', OUT / 'runner.log')
results = []
try:
    for _ in range(180):
        state = driver.run(('overworld', 'new_game'), 20, 'a')
        if state['hit'] == 'new_game':
            raise RuntimeError('Refusing to start a new game')
        if state['hit'] == 'overworld':
            break
        driver.run(frames=10)
    else:
        raise RuntimeError('No overworld')
    driver.run(('start_menu',), 180, 'start')
    for _ in range(12):
        state = driver.run(('start_menu',), 60)
        if state['menu'] == 3:
            break
        driver.run(('start_menu',), frames=60, key='down')
    else:
        raise RuntimeError('No Pack selection: ' + str(state))
    state = driver.run(('pack_loop',), 600, 'a')
    assert state['hit'] == 'pack_loop', state
    driver.command('rawcolor')
    driver.run(('pack_ready',), 600)
    driver.run(('pack_loop',), 120)
    for direction in ('left', 'right'):
        for number in range(5):
            name = f'{direction}-{number}'
            prefix = OUT / name
            driver.command(f'restoretrace {prefix} 1')
            driver.command(f'image {prefix}-before.ppm')
            state = driver.run(('pack_switch',), 180, direction)
            assert state['hit'] == 'pack_switch', state
            state = driver.run(('pack_ready',), 600)
            assert state['hit'] == 'pack_ready', state
            driver.run(('pack_loop',), 120)
            driver.run(frames=3)
            driver.command('restorestop')
            driver.command(f'image {prefix}-after.ppm')
            trace = [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]
            phases_seen = [e for e in trace if e['event'] == 'phase']
            accepted = next(e for e in phases_seen if e['phase'] == 'switch')
            ready = next(e for e in phases_seen if e['phase'] == 'ready')
            writes = [e for e in trace if e['event'] == 'write']
            frames = [e for e in trace if e['event'] == 'frame']
            result = dict(case=name,
                accepted_to_ready_intervals=(ready['t'] - accepted['t']) / cold.FRAME,
                black_frames=sum(e['black'] for e in frames),
                white_frames=sum(e['white'] for e in frames),
                lcd_writes=[e for e in writes if e['address'] == 0xff40],
                phases=[dict(name=e['phase'], t=e['t'], ly=e['ly']) for e in phases_seen],
                dma_transfers=sum(e['address'] == 0xff55 and e['value'] & 128 != 0 for e in writes),
                blocked_palette_writes=sum(e['pal_blocked'] and e['address'] in (0xff69, 0xff6b) for e in writes))
            results.append(result)
            print(json.dumps({k: v for k, v in result.items() if k != 'phases'}), flush=True)
finally:
    driver.close()
report = dict(rom_sha256=ROM_HASH, rom_unchanged=sha256(ROM.read_bytes()) == ROM_HASH,
              cases=results, note='Reused observer Dex-specific state fields are irrelevant to Pack captures.')
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
