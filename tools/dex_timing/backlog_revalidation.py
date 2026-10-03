"""Host-only validation of historical Dex return, marker and exit reports.

The runner observes normal input in a private copy of the accepted ROM. The
optional exit counterfactual patches only verified unused ROMX and the exit-state
entry point in that private copy; production files, saves and checkpoints stay intact.
"""
import argparse
import atexit
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil

from .assets import Repository, offset, sha256
from .cold_listing import Driver, KEY, ROOT, audit as audit_animation, bootstrap, move, prepare_states
from .cry_ownership import validate_output
from .description_paging import caught_fixture
from .description_ui import settle
from .listing_restoration import compile_observer, listing_snapshot, verify_observer

FRAME = 70224
EXIT_POINTS = dict(
    dex_exit='Pokedex_Exit', dex_cleanup='Pokedex.exit', unlock_ids='Pokedex_ClearLockedIDs',
    restore_map='ReturnToMapFromSubmenu', map_setup='RunMapSetupScript',
    load_blocks='LoadBlockData', load_connections='LoadConnectionBlockData',
    close_submenu='CloseSubmenu', clear_bg='ClearBGPalettes', clear_palettes='ClearPalettes',
    reload_tiles='ReloadTilesetAndPalettes', finish_exit='FinishExitMenu',
    start_reopen='StartMenu.Reopen', start_input='StartMenu.loop',
)


def order_names():
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    return [aliases.get(n, n.lower()) for n in re.findall(
        r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)]


def run_to(driver, repo, label, frames=600, key=None):
    bank, pc = repo.symbols[label]
    state = driver.command(f'restorerun {bank} {pc} {int(frames * FRAME)} {KEY.get(key, 0)}')
    if state['pc'] != pc or (pc >= 0x4000 and state['bank'] != bank):
        raise RuntimeError(f'Timed out reaching {label}: {state}')
    return state


def events(prefix):
    return [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]


def linked(repo, name, size):
    start = offset(repo.symbols[name])
    return repo.rom[start:start + size]


def marker_issues(repo, snapshot):
    """Audit the actual OAM owner, tile pixels and hardware OBJ palette, not targets alone."""
    problems = []
    palette = linked(repo, 'PokedexListCaughtBallPalette', 8)
    if bytes.fromhex(snapshot['obj_pal'])[8:16] != palette:
        problems.append('caught_ball_hardware_palette')
    if bytes.fromhex(snapshot['target_obj'])[8:16] != palette:
        problems.append('caught_ball_target_palette')
    vram = bytes.fromhex(snapshot['vram'])
    if vram[0x410:0x420] != linked(repo, 'PokedexCaughtBallGFX', 16):
        problems.append('caught_ball_graphics')
    flags, oam = bytes.fromhex(snapshot['grid_flags']), bytes.fromhex(snapshot['oam'])
    for i, flag in enumerate(flags):
        actual = oam[(12 + i) * 4:(13 + i) * 4]
        expected = bytes((60 + 32 * (i // 3), 72 + 32 * (i % 3), 0x41, 1)) if flag & 2 else bytes(4)
        if actual != expected:
            problems.append(f'caught_ball_oam_{i}')
    cursor = snapshot['cursor']
    y, x = 50 + 32 * (cursor // 3), 74 + 32 * (cursor % 3)
    corners = b''.join(bytes((y + dy, x + dx, 0x40, attr)) for dy, dx, attr in (
        (0, 0, 0), (0, 20, 32), (20, 0, 64), (20, 20, 96)))
    if oam[84:100] != corners:
        problems.append('cursor_geometry')
    return problems


def window_pixels(snapshot):
    """Resolve equivalent dynamic digit-tile allocations before comparing the window."""
    vram, palette = bytes.fromhex(snapshot['vram']), bytes.fromhex(snapshot['bg_pal'])
    result = bytearray()
    # Only the selection header. Grid icons legitimately alternate frame tiles.
    for row in range(3):
        for x in range(11):
            cell = row * 32 + x
            tile, attr = vram[0x1c00 + cell], vram[0x3c00 + cell]
            if snapshot['lcd'] & 16:
                address = tile * 16
            else:
                address = 0x1000 + (tile if tile < 128 else tile - 256) * 16
            address += 0x2000 if attr & 8 else 0
            for y in range(8):
                lo, hi = vram[address + (7 - y if attr & 64 else y) * 2:][:2]
                for column in range(8):
                    bit = column if attr & 32 else 7 - column
                    color = ((lo >> bit) & 1) | ((hi >> bit) & 1) << 1
                    start = (attr & 7) * 8 + color * 2
                    result += palette[start:start + 2]
    return bytes(result)


def front_bytes(snapshot):
    return bytes.fromhex(snapshot['vram'])[0x1000:0x1310]


def exact_listing_reference(driver, checkpoints, actual, count, prefix):
    # Independent viewport reached by ordinary Listing input, with the same cursor.
    index = min(actual['listing_scroll'] + 6, count - 1)
    driver.command(f'load {checkpoints / "listing-states" / f"listing-{index:03}.s0"}')
    driver.command('rawcolor')
    for _ in range(8):
        state = driver.command('peek')
        if state['index'] == actual['index']:
            break
        current = state['index'] - state['scroll']
        target = actual['index'] - actual['listing_scroll']
        direction = ('up' if target // 3 < current // 3 else 'down') if target // 3 != current // 3 else (
            'left' if target % 3 < current % 3 else 'right')
        move(driver, direction)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
    else:
        raise RuntimeError('Reference cursor did not converge')
    driver.run(frames=3)
    result = listing_snapshot(driver, prefix)
    if (result['listing_scroll'], result['index']) != (actual['listing_scroll'], actual['index']):
        raise RuntimeError('Independent reference is not the same Listing selection/viewport')
    return result


def check_return_frames(repo, trace, expected):
    frames = [e for e in trace if e['event'] == 'frame' and e['phase'] == '0']
    issues, listing_count, selected_count = [], 0, 0
    for frame in frames:
        if frame['scroll'][1] or frame['mirrors'][1]:
            issues.append(f'vertical_displacement:{frame["display"]}')
        if frame['scroll'][2] == 71:
            listing_count += 1
            if window_pixels(frame) != window_pixels(expected):
                issues.append(f'placeholder_window:{frame["display"]}')
            if front_bytes(frame) != front_bytes(expected):
                issues.append(f'placeholder_portrait:{frame["display"]}')
            if frame['index'] != expected['index'] or frame['cursor'] != expected['cursor']:
                issues.append(f'intermediate_selection:{frame["display"]}')
            issues += [f'{problem}:{frame["display"]}' for problem in marker_issues(repo, frame)]
        elif frame['scroll'][2] == 167:
            selected_count += 1
    if not listing_count or not selected_count:
        issues.append('missing_visible_owner_coverage')
    return dict(outgoing_frames=selected_count, listing_frames=listing_count, issues=issues)


def audit_returns(driver, repo, directories, checkpoints, output):
    results = []
    for source in directories:
        suite = json.loads((source / 'report.json').read_text())
        fixture_checkpoints = source if suite['sparse_fixture'] else checkpoints
        for result in suite['results']:
            label = result['case']['label']
            directory = output / source.name / label
            directory.mkdir(parents=True, exist_ok=True)
            trace = events(source / label / 'trace')
            expected = exact_listing_reference(driver, fixture_checkpoints, trace[-1],
                len(order_names()), directory / 'independent-listing')
            results.append(dict(case=label, source=str(source), **check_return_frames(repo, trace, expected)))
    return results


def return_worker_init(config):
    global _return_worker
    output = Path(config['output'])
    checkpoints = Path(config['checkpoints'])
    repo = Repository(ROOT, checkpoints / 'input-copy.gbc', ROOT / 'pokecrystal.sym')
    drivers = [Driver(config['core'], config['rom'], config['boot'], config['battery'],
                      output / f'worker-{os.getpid()}-{i}.log') for i in range(2)]
    atexit.register(lambda: [driver.close() for driver in drivers])
    _return_worker = dict(config=config, repo=repo, drivers=drivers,
                          assets={a.name: a for a in repo.load()})


def return_worker(job):
    index, name = job
    config, repo = _return_worker['config'], _return_worker['repo']
    driver, reference_driver = _return_worker['drivers']
    checkpoints = Path(config['checkpoints'])
    directory = Path(config['output']) / f'{index:03}-{name}'
    directory.mkdir(parents=True, exist_ok=True)
    driver.command(f'load {checkpoints / "listing-states" / f"listing-{index:03}.s0"}')
    driver.command('rawcolor')
    driver.run(frames=3)
    driver.events.clear()
    driver.command('audit 1')
    accepted = driver.run(('accept',), key='a')
    finished = settle(driver)
    animation = audit_animation(_return_worker['assets'][name], accepted, driver.events, finished, cold=False)
    driver.command('audit 0')
    driver.command(f'restoretrace {directory / "trace"} 0')
    driver.run(('leave',), key='b')
    driver.run(('listing',), frames=600)
    driver.run(frames=5)
    driver.command('restorestop')
    trace = events(directory / 'trace')
    expected = exact_listing_reference(reference_driver, checkpoints, trace[-1], len(order_names()),
                                       directory / 'independent-listing')
    row = dict(index=index, species=name, animation=animation, **check_return_frames(repo, trace, expected))
    (directory / 'report.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def marker_sweep(driver, repo, checkpoints, output, caught_all=False, fixture=None):
    if caught_all:
        bootstrap(driver)
        prepare_states(driver, output / 'listing-states', len(order_names()))
        checkpoints = output
    results = []
    for index, name in enumerate(order_names()):
        driver.command(f'load {checkpoints / "listing-states" / f"listing-{index:03}.s0"}')
        driver.command('rawcolor')
        driver.run(frames=3)
        snap = listing_snapshot(driver, output / f'marker-{index:03}')
        issues = marker_issues(repo, snap)
        row = dict(index=index, species=name, caught_slots=sum(bool(v & 2) for v in bytes.fromhex(snap['grid_flags'])),
                   issues=issues)
        results.append(row)
        if index % 30 == 0:
            print(json.dumps(dict(marker=index, issues=issues)), flush=True)
    return dict(fixture=fixture, results=results)


def exit_counterfactual(repo, destination):
    """Request the existing white exit mask before cleanup/map reconstruction."""
    bank, entry = repo.symbols['Pokedex_Exit']
    body = linked(repo, 'Pokedex_Exit', repo.symbols['Pokedex_InitMainScreen'][1] - entry)
    if len(body) != 9 or body[0] != 0xaf or body[-1] != 0xc9:
        raise ValueError('Exit state routine changed; re-review the overlay')
    helper_bank = repo.symbols['Pokedex_BeginOwnerLoop'][0]
    bank_map = (ROOT / 'pokecrystal.map').read_text().split(f'ROMX bank #{helper_bank}:')[1].split('ROMX bank #')[0]
    free = re.findall(r'EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+)', bank_map)
    clear = repo.symbols['ClearPalettes'][1]
    payload = body[:-1] + bytes((0xc3, clear & 255, clear >> 8))
    stub = next(int(start, 16) for start, finish in free if int(finish, 16) - int(start, 16) + 1 >= len(payload))
    at = offset((helper_bank, stub))
    if len(set(repo.rom[at:at + len(payload)])) != 1 or repo.rom[at] not in (0, 255):
        raise ValueError('Overlay helper is not wholly within unused ROMX')
    private = bytearray(repo.rom)
    private[at:at + len(payload)] = payload
    call = offset((bank, entry))
    farcall = repo.symbols['FarCall'][1]
    if farcall not in range(0, 0x40, 8):
        raise ValueError('FarCall is not an RST vector')
    private[call:call + 9] = bytes((0x3e, helper_bank, 0x21, stub & 255, stub >> 8,
                                   0xc7 + farcall, 0xc9, 0, 0))
    private[0x14e:0x150] = bytes(2)
    private[0x14e:0x150] = (sum(private) & 65535).to_bytes(2, 'big')
    destination.write_bytes(private)
    return dict(call_address=f'{bank:02x}:{entry:04x}', stub=f'{helper_bank:02x}:{stub:04x}',
        helper_bytes=len(payload), proposed_romx_bytes=9, crowded_bank_bytes_freed=2, no_new_ram=True,
        production_unchanged=True, sha256=sha256(private))


def exit_case(driver, repo, checkpoints, output, name, pages, idle, images):
    directory = output / f'{name}-pages{pages}-phase{idle}'
    directory.mkdir(parents=True, exist_ok=True)
    index = order_names().index(name)
    driver.command(f'load {checkpoints / "listing-states" / f"listing-{index:03}.s0"}')
    driver.command('rawcolor')
    if pages >= 0:
        driver.run(('accept',), key='a')
        settle(driver)
        for _ in range(pages):
            driver.run(frames=2)
            driver.run(('change_species',), key='down')
            settle(driver)
        driver.run(('leave',), key='b')
        driver.run(('listing',), frames=600)
    driver.run(frames=3 + idle)
    driver.command(f'image {directory / "before.ppm"}')
    driver.command(f'restoretrace {directory / "trace"} {int(images)}')
    requested = run_to(driver, repo, 'Pokedex_Exit', key='b')
    stopped = run_to(driver, repo, 'StartMenu.loop', frames=600)
    driver.run(frames=5)
    driver.command('restorestop')
    driver.command(f'image {directory / "after.ppm"}')
    trace = events(directory / 'trace')
    phases = [e for e in trace if e['event'] == 'phase']
    frames = [e for e in trace if e['event'] == 'frame' and e['phase'] == '0']
    cleanup = next(e for e in phases if e['phase'] == 'dex_cleanup')
    map_start = next(e for e in phases if e['phase'] == 'restore_map')
    close = next(e for e in phases if e['phase'] == 'close_submenu')
    white = next((e for e in frames if e['t'] >= cleanup['t'] and e['white']), None)
    shifted = [e for e in frames if cleanup['t'] < e['t'] < (white['t'] if white else stopped['t']) and not e['white'] and
               (e['scroll'] != cleanup['scroll'])]
    report = dict(species=name, pages=pages, idle_intervals=idle, requested=requested,
        menu_ready=stopped, exit_cycles=stopped['t'] - requested['t'],
        first_white_cycles=white['t'] - requested['t'] if white else None,
        map_rebuild_cycles=close['t'] - map_start['t'],
        shifted_frames=[dict(display=e['display'], t=e['t'], scroll=e['scroll'], mirrors=e['mirrors']) for e in shifted],
        white_frames=sum(bool(e['white']) for e in frames),
        blocked_palette_writes=sum(e['event'] == 'write' and e['address'] in (0xff69, 0xff6b)
                                  and e['pal_blocked'] for e in trace),
        phases=[dict(phase=e['phase'], t=e['t'], scroll=e['scroll'], mirrors=e['mirrors'])
                for e in phases if e['phase'] in EXIT_POINTS or e['phase'] in ('trace_start', 'trace_end')])
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('returns', 'return-sweep', 'markers', 'exit'), required=True)
    parser.add_argument('--return-suite', type=Path, action='append', default=[])
    parser.add_argument('--prototype', action='store_true')
    parser.add_argument('--caught-all', action='store_true')
    parser.add_argument('--phases', type=int, default=8)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--no-images', action='store_true')
    parser.add_argument('--verify-observer', action='store_true')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    args = parser.parse_args()
    if args.prototype and args.mode != 'exit':
        parser.error('--prototype applies only to --mode exit')
    if args.caught_all and args.mode != 'markers':
        parser.error('--caught-all applies only to --mode markers')
    if args.mode == 'returns' and not args.return_suite:
        parser.error('--mode returns requires at least one --return-suite')
    if args.phases < 1 or args.jobs < 1:
        parser.error('--phases and --jobs must be positive')
    args.output = validate_output(args.output, [args.checkpoints, ROOT / 'pokecrystal.sym'])
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.checkpoints / 'input-copy.gbc', ROOT / 'pokecrystal.sym')
    origin = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(origin[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Checkpoints do not match current accepted symbols/ROM')
    rom = args.output / 'diagnostic-input.gbc'
    overlay = exit_counterfactual(repo, rom) if args.prototype else None
    if not args.prototype:
        shutil.copy2(args.checkpoints / 'input-copy.gbc', rom)
    core = compile_observer(repo, args.sameboy, args.output,
        extra_points={k: v for k, v in EXIT_POINTS.items() if v in repo.symbols},
        extra_fields=('wPokedexRenderedSelectionKey',),
        extra_flags=('-DDEX_BACKLOG_REVALIDATION_TRACE',))
    controls = verify_observer(repo, args.sameboy, core, args.checkpoints, args.output) if args.verify_observer else None
    battery = args.checkpoints / 'input-copy.sav'
    fixture = None
    if args.caught_all:
        battery = args.output / 'all-caught.sav'
        fixture = caught_fixture(repo, args.checkpoints / 'input-copy.sav', battery)
        (args.output / 'listing-states').mkdir(exist_ok=True)
    driver = Driver(core, rom, Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
                    battery, args.output / 'core.log')
    try:
        if args.mode == 'returns':
            results = audit_returns(driver, repo, args.return_suite, args.checkpoints, args.output)
        elif args.mode == 'return-sweep':
            config = dict(core=str(core), rom=str(rom), battery=str(battery), output=str(args.output),
                checkpoints=str(args.checkpoints),
                boot='/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
            names = order_names()
            jobs = [(i, name) for i, name in enumerate(names) if not args.species or name in args.species]
            with ProcessPoolExecutor(max_workers=args.jobs, initializer=return_worker_init, initargs=(config,)) as pool:
                results = []
                for row in pool.map(return_worker, jobs):
                    results.append(row)
                    if row['index'] % 30 == 0 or row['issues'] or row['animation']['issues']:
                        print(json.dumps(dict(species=row['species'], issues=row['issues'],
                                              animation=row['animation']['issues'])), flush=True)
        elif args.mode == 'markers':
            results = marker_sweep(driver, repo, args.checkpoints, args.output, args.caught_all, fixture)
        else:
            results = []
            for name in args.species or ['chikorita', 'dusknoir', 'weavile', 'regigigas']:
                for pages in (-1, 0, 9) if name != 'regigigas' else (-1, 0):
                    for idle in range(args.phases):
                        row = exit_case(driver, repo, args.checkpoints, args.output, name, pages,
                                        idle, not args.no_images)
                        results.append(row)
                        print(json.dumps(dict(species=name, pages=pages, phase=idle,
                            shifted=len(row['shifted_frames']), exit_intervals=row['exit_cycles'] / FRAME)), flush=True)
    finally:
        driver.close()
    report = dict(provenance=repo.hashes, mode=args.mode, host_only_instrumentation=True,
        overlay=overlay, observer_controls=controls, production_unchanged=True, results=results)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
