"""Host-only frame/write tracing of normal-input Selected-to-Listing returns.

The optional C observer runs the unchanged accepted ROM from copied checkpoints.
All diagnostic executables, logs and displayed frames have a distinct build path.
"""
import argparse
import json
from pathlib import Path
import re
import shutil

from .assets import Repository, offset
from .cold_listing import Driver, ROOT, bootstrap, build_core, move, predecessor, prepare_states
from .description_ui import settle

FIELDS = '''hSCX hSCY hWX hWY hVBlank hBGMapMode hCGBPalUpdate hOAMUpdate
    wPokedexOwnerTransition wPokedexSelectedBGPaletteDirty wPokedexSelectedOBJPaletteDirty
    wPokedexGridTopPhysicalRow wPokedexGridIconAnimFrame wPokedexGridCacheRowOffsets
    wPokedexGridSpecies wPokedexGridFlags wPokedexGridIconPalettes
    wBGPals2 wOBPals2 wShadowOAM'''.split()
PHASES = dict(
    leave='PokedexSelectedMon_Leave',
    init_main='Pokedex_InitMainScreen',
    stage_listing='Pokedex_InitMainScreen.stage_listing',
    cache_ready='Pokedex_InitMainScreen.cache_ready',
    window_staged='Pokedex_InitMainScreen.window_staged',
    layout_ready='Pokedex_InitMainScreen.layout_ready',
    bg_staged='Pokedex_InitMainScreen.bg_staged',
    listing_revealed='Pokedex_InitMainScreen.revealed',
    ensure_cache='Pokedex_EnsureGridCache',
    prime_cache='Pokedex_PrimeGridCache',
    prime_lcd_off='Pokedex_PrimeGridCache.prime',
    copy_window='Pokedex_CopyBackingToWindow',
    list_layout='CGB_PokedexBuildListLayout',
    stage_maps='Pokedex_StageOwnerTransitionMaps',
    stage_maps_done='Pokedex_StageOwnerTransitionMaps.maps_ready',
    queue_owner='Pokedex_QueueOwnerTransition',
    owner_dispatch='Pokedex_VBlankOwnerTransition',
    owner_wx='Pokedex_VBlankOwnerTransition.got_wx',
    bg_pal_commit='Pokedex_VBlankOwnerTransition.CommitDirtyBGPals',
    obj_pal_commit='Pokedex_VBlankOwnerTransition.CommitDirtyOBPals',
    transfer_map='Pokedex_VBlankOwnerTransition.TransferMap',
    update_oam='Pokedex_UpdateGridOAM',
)


def compile_observer(repo, source, output):
    header = (output / 'listing-restore-symbols.h').resolve()
    lines = [f'#define R_{name} 0x{repo.symbols[name][1]:04x}' for name in FIELDS]
    lines += ['static const struct { unsigned bank, pc; const char *name; } restoration_points[] = {']
    for name, label in PHASES.items():
        bank, pc = repo.symbols[label]
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    bank, pc = repo.symbols['Pokedex_VBlankOwnerTransition.CommitDirtyBGPals']
    at = offset((bank, pc - 2))
    if repo.rom[at:at + 2] != bytes((0x37, 0xc9)):
        raise ValueError('Owner-transition success return changed; update the trace point')
    lines.append(f'{{{bank}, 0x{pc - 2:04x}, "owner_done"}},')
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DDEX_LISTING_RESTORE_TRACE', f'-DDEX_LISTING_RESTORE_SYMBOLS="{header}"'))


def cases(names):
    # Local-cache, viewport-boundary, rebuilt-cache, active-cancel and text-page paths.
    result = [dict(label=name, start=name, pages=0, wait=None, description_page=False)
              for name in ('chikorita', 'meganium', 'togetic', 'dusknoir', 'luxray', 'weavile')]
    result += [dict(label=f'chikorita-down{n}', start='chikorita', pages=n,
                    wait=None, description_page=False) for n in (1, 8, 9, 12)]
    result += [dict(label=f'{name}-active{n}', start=name, pages=0,
                    wait=n, description_page=False)
               for name in ('dusknoir', 'weavile') for n in (0, 4, 16, 40)]
    result += [dict(label=f'{name}-page2', start=name, pages=0,
                    wait=None, description_page=True) for name in ('chikorita', 'dusknoir')]
    return result


def summarize(trace, reference):
    phases = [e for e in trace if e['event'] == 'phase']
    frames = [e for e in trace if e['event'] == 'frame']
    writes = [e for e in trace if e['event'] == 'write']
    leave = next(e for e in phases if e['phase'] == 'leave')
    reveal = next(e for e in phases if e['phase'] == 'listing_revealed')
    commit = next(e for e in phases if e['phase'] == 'owner_dispatch' and e['owner_transition'])
    done = next(e for e in phases if e['phase'] == 'owner_done')
    final = phases[-1]
    mismatches = {}
    for kind in ('bg', 'obj'):
        actual, target = bytes.fromhex(final[f'{kind}_pal']), bytes.fromhex(final[f'target_{kind}'])
        mismatches[kind] = [i for i, pair in enumerate(zip(actual, target)) if pair[0] != pair[1]]
    before_vram, after_vram = bytes.fromhex(reference['vram']), bytes.fromhex(final['vram'])
    cache_regions = dict(center=(0x2000, 0x2280), side0=(0x3000, 0x3280), side1=(0x2d20, 0x2fa0))
    return dict(
        leave_t=leave['t'], reveal_t=reveal['t'], return_cycles=reveal['t'] - leave['t'],
        return_intervals=(reveal['t'] - leave['t']) / 70224,
        commit_cycles=done['t'] - commit['t'], commit_done_ly=done['ly'],
        cache_rebuilt=any(e['phase'] == 'prime_cache' for e in phases),
        lcd_changes=[e for e in writes if e['address'] == 0xff40],
        blocked_palette_writes=[e for e in writes if e['address'] in (0xff69, 0xff6b) and e['pal_blocked']],
        palette_mismatch_bytes=mismatches,
        visible_palette_mismatch_bytes=dict(bg=[i for i in mismatches['bg']],
                                            obj=[i for i in mismatches['obj'] if i < 48]),
        white_frames=sum(e['white'] for e in frames),
        cache_changed_bytes={name: sum(a != b for a, b in zip(before_vram[start:end], after_vram[start:end]))
                             for name, (start, end) in cache_regions.items()},
        frames=[dict(display=e['display'], t=e['t'], type=int(e['phase']),
                     state=e['state'], white=bool(e['white']), scroll=e['scroll'],
                     mirrors=e['mirrors']) for e in frames],
        phase_timing=[dict(phase=e['phase'], t=e['t'], ly=e['ly'], stat=e['stat'],
                           display=e['display'], bg_dirty=e['bg_dirty'], obj_dirty=e['obj_dirty'])
                      for e in phases if e['phase'] != 'owner_dispatch' or e['owner_transition']],
    )


def run_case(driver, checkpoints, output, case, names, images):
    directory = output / case['label']
    directory.mkdir(parents=True, exist_ok=True)
    index = names.index(case['start'])
    prior, direction = predecessor(index)
    driver.command(f'load {checkpoints / "listing-states" / f"listing-{prior:03}.s0"}')
    driver.command('rawcolor')
    move(driver, direction, index)
    driver.run(('end_loop',))
    driver.run(('end_loop',))
    driver.command(f'image {directory / "listing-before.ppm"}')
    driver.command(f'restoretrace {directory / "reference"} 0')
    driver.command('restorestop')
    driver.run(('accept',), key='a')
    driver.run(('selected', 'animation_miss', 'audio_miss'))
    if case['wait'] is not None:
        if case['wait']:
            driver.run(frames=case['wait'])
    else:
        settle(driver)
    for _ in range(case['pages']):
        driver.run(frames=2)
        driver.run(('change_species',), key='down')
        settle(driver)
    if case['description_page']:
        driver.run(frames=2)
        driver.run(frames=2, key='a')
        driver.run(frames=2)
    selected = driver.command('peek')
    driver.command(f'image {directory / "selected-before.ppm"}')
    driver.command(f'save {directory / "selected-before.s0"}')
    driver.command(f'restoretrace {directory / "trace"} {int(images)}')
    driver.command('audit 1')
    driver.events.clear()
    before = driver.command('peek')
    left = driver.run(('leave',), 180, 'b')
    if left['hit'] != 'leave':
        raise RuntimeError(f'B did not enter Leave: {case}: {left}')
    returned = driver.run(('listing',), 600)
    if returned['hit'] != 'listing':
        raise RuntimeError(f'Return did not reach Listing: {case}: {returned}')
    driver.run(frames=5)
    final = driver.command('peek')
    driver.command('restorestop')
    driver.command('audit 0')
    driver.command(f'image {directory / "listing-after.ppm"}')
    trace = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
    reference = json.loads((directory / 'reference.jsonl').read_text().splitlines()[0])
    report = dict(case=case, selected=selected, before=before, left=left,
                  returned=returned, final=final, runtime_events=list(driver.events),
                  summary=summarize(trace, reference))
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def sparse_battery(repo, source, destination):
    """Make a separate, checksum-verified sparse-seen fixture; never edit the user's save."""
    symbols = repo.symbols
    original = source.read_bytes()
    changed = bytearray(original)
    flag_bytes = symbols['wEndPokedexSeen'][1] - symbols['wPokedexSeen'][1]
    last_species = len(re.findall(r'^\s*dw \w+\s*$',
        (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M))
    # The last New Dex entry remains seen so unseen holes remain navigable in Listing.
    last_name = re.findall(r'^\s*dw (\w+)\s*$',
        (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)[-1]
    constants = re.findall(r'^\s*const\s+(\w+)',
        (ROOT / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
    last_index = constants.index(last_name) + 1
    allowed = set()
    def sram(label):
        bank, address = symbols[label]
        return bank * 8192 + address - 0xa000
    for prefix in ('s', 'sBackup'):
        start, end, checksum = (sram(prefix + suffix) for suffix in ('SaveData', 'SaveDataEnd', 'Checksum'))
        if sum(original[start:end]) & 65535 != int.from_bytes(original[checksum:checksum + 2], 'little'):
            raise ValueError('Sparse fixture source checksum is invalid')
        pokemon = sram(prefix + 'PokemonData')
        caught = pokemon + symbols['wPokedexCaught'][1] - symbols['wPokemonData'][1]
        seen = pokemon + symbols['wPokedexSeen'][1] - symbols['wPokemonData'][1]
        changed[seen:seen + flag_bytes] = original[caught:caught + flag_bytes]
        changed[seen + (last_index - 1) // 8] |= 1 << ((last_index - 1) % 8)
        changed[checksum:checksum + 2] = (sum(changed[start:end]) & 65535).to_bytes(2, 'little')
        allowed.update(range(seen, seen + flag_bytes))
        allowed.update((checksum, checksum + 1))
    actual_changes = {i for i, (a, b) in enumerate(zip(original, changed)) if a != b}
    if not actual_changes <= allowed or original[0x8000:] != changed[0x8000:]:
        raise ValueError('Sparse fixture modified unrelated save data')
    destination.write_bytes(changed)
    return dict(source=str(source), destination=str(destination), total_order=last_species,
                caught_unchanged=True, checksums_valid=True, rtc_unchanged=True,
                changed_offsets=sorted(actual_changes))


def verify_observer(repo, source, observed_core, checkpoints, output):
    """Check that enabled host tracing changes neither emulated cycles nor final display data."""
    control = output / 'control'
    control.mkdir(exist_ok=True)
    control_core = build_core(repo, source, control)
    results = []
    for pages in (0, 1, 9):
        samples = []
        for tracing, core in ((False, control_core), (True, observed_core)):
            driver = Driver(core, checkpoints / 'input-copy.gbc',
                Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
                checkpoints / 'input-copy.sav', control / f'core-{pages}-{tracing}.log')
            try:
                driver.command(f'load {checkpoints / "listing-states/listing-001.s0"}')
                driver.command('rawcolor')
                move(driver, 'left', 0)
                driver.run(('end_loop',))
                driver.run(('end_loop',))
                driver.run(('accept',), key='a')
                driver.run(('selected',))
                settle(driver)
                for _ in range(pages):
                    driver.run(frames=2)
                    driver.run(('change_species',), key='down')
                    settle(driver)
                if tracing:
                    driver.command(f'restoretrace {control / f"observed-{pages}"} 1')
                left = driver.run(('leave',), key='b')
                returned = driver.run(('listing',), 600)
                final = driver.run(frames=5)
                ui = driver.command('ui')
                image = control / f'final-{pages}-{tracing}.ppm'
                driver.command(f'image {image}')
                if tracing:
                    driver.command('restorestop')
                samples.append(dict(left=left, returned=returned, final=final,
                                    ui=ui, pixels=image.read_bytes()))
            finally:
                driver.close()
        same = samples[0] == samples[1]
        results.append(dict(pages=pages, cycles_state_palettes_maps_pixels_equal=same))
        if not same:
            raise RuntimeError(f'Host instrumentation changed replay output: {pages}')
    (output / 'observer-control.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--case', action='append', help='Run only these case labels')
    parser.add_argument('--no-images', action='store_true')
    parser.add_argument('--sparse', action='store_true', help='Boot a separate sparse-seen battery fixture')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--verify-observer', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.checkpoints / 'input-copy.gbc', ROOT / 'pokecrystal.sym')
    origin = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(origin[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Checkpoint ROM or linked symbols differ from the accepted build')
    rom = args.output / 'diagnostic-input.gbc'
    shutil.copy2(args.checkpoints / 'input-copy.gbc', rom)
    core = compile_observer(repo, args.sameboy, args.output)
    if args.verify_observer:
        print(json.dumps(dict(observer_control=verify_observer(repo, args.sameboy, core,
            args.checkpoints, args.output))), flush=True)
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in names]
    suite = [c for c in cases(names) if args.case is None or c['label'] in args.case]
    battery = args.checkpoints / 'input-copy.sav'
    checkpoints = args.checkpoints
    sparse = None
    if args.sparse:
        battery = args.output / 'sparse-input.sav'
        sparse = sparse_battery(repo, args.checkpoints / 'input-copy.sav', battery)
        checkpoints = args.output
        (checkpoints / 'listing-states').mkdir(exist_ok=True)
        suite = [dict(label=f'sparse-chikorita-down{n}', start='chikorita', pages=n,
                      wait=None, description_page=False) for n in (0, 1, 3, 4)]
    suite = [dict(case, label=case['label'] if repetition == 0 else
                  f'{case["label"]}-repeat{repetition + 1}', repetition=repetition + 1)
             for case in suite for repetition in range(args.repeat)]
    driver = Driver(core, rom,
        Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
        battery, args.output / 'core.log')
    results = []
    try:
        if sparse:
            bootstrap(driver)
            prepare_states(driver, checkpoints / 'listing-states', 3)
        for case in suite:
            report = run_case(driver, checkpoints, args.output, case, names, not args.no_images)
            results.append(report)
            summary = report['summary']
            print(json.dumps(dict(case=case['label'], intervals=summary['return_intervals'],
                rebuilt=summary['cache_rebuilt'], blocked=len(summary['blocked_palette_writes']),
                mismatches=summary['palette_mismatch_bytes'])), flush=True)
    finally:
        driver.close()
    (args.output / 'report.json').write_text(json.dumps(dict(
        provenance=repo.hashes, rom_unchanged=True, host_only_instrumentation=True,
        sparse_fixture=sparse, results=results), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
