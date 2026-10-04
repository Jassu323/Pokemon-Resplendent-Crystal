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
    wPokedexGridFlags wPokedexGridIconPalettes
    wBGPals2 wOBPals2 wShadowOAM wPokemonIndexTableEntries'''.split()
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
OPTIONAL_PHASES = dict(
    cache_repair='Pokedex_RepairGridCache',
    prepare_cache_row='Pokedex_PrepareGridCacheRow',
    cache_row_uploaded='Pokedex_UploadPendingGridCacheRow.publish',
    listing_bg_pal_commit='Pokedex_VBlankOwnerTransition.CommitListingBGPals',
    listing_obj_pal_commit='Pokedex_VBlankOwnerTransition.CommitListingOBPals',
    info_return_preserve='PokedexInfo_PreserveReturnPanel',
    info_return_relocate='PokedexInfo_PreserveReturnPanel.relocate',
    info_return_remap='PokedexInfo_PreserveReturnPanel.remap',
    info_return_published='Pokedex_VBlankInfoReturn.published',
)


def compile_observer(repo, source, output, *, extra_points=None, extra_fields=(), extra_flags=()):
    header = (output / 'listing-restore-symbols.h').resolve()
    lines = [f'#define R_{name} 0x{repo.symbols[name][1]:04x}' for name in (*FIELDS, *extra_fields)]
    presence = 'wPokedexGridOccupied' in repo.symbols
    grid = 'wPokedexGridOccupied' if presence else 'wPokedexGridSpecies'
    lines += [f'#define R_wPokedexGridCells 0x{repo.symbols[grid][1]:04x}',
              f'#define R_GRID_USES_PRESENCE {int(presence)}']
    lines += ['static const struct { unsigned bank, pc; const char *name; } restoration_points[] = {']
    labels = dict(PHASES, **{name: label for name, label in OPTIONAL_PHASES.items()
                           if label in repo.symbols})
    labels.update(extra_points or {})
    for name, label in labels.items():
        bank, pc = repo.symbols[label]
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    bank, pc = repo.symbols.get('Pokedex_VBlankOwnerTransition.committed',
        (repo.symbols['Pokedex_VBlankOwnerTransition.CommitDirtyBGPals'][0],
         repo.symbols['Pokedex_VBlankOwnerTransition.CommitDirtyBGPals'][1] - 2))
    at = offset((bank, pc))
    if repo.rom[at:at + 2] != bytes((0x37, 0xc9)):
        raise ValueError('Owner-transition success return changed; update the trace point')
    lines.append(f'{{{bank}, 0x{pc:04x}, "owner_done"}},')
    dispatch_bank, dispatch_pc = repo.symbols['Pokedex_VBlankDispatch']
    owner_bank, owner_pc = repo.symbols['Pokedex_VBlankOwnerTransition']
    dispatch = offset((dispatch_bank, dispatch_pc))
    instruction = bytes((0xcd, owner_pc & 255, owner_pc >> 8))
    body = repo.rom[dispatch:offset((dispatch_bank, owner_pc))]
    if body.count(instruction) != 1:
        raise ValueError('Owner-transition caller changed; update the return trace point')
    lines.append(f'{{{dispatch_bank}, 0x{dispatch_pc + body.index(instruction) + 3:04x}, "owner_returned"}},')
    oam_pc = repo.symbols['hTransferShadowOAM'][1]
    body = repo.rom[offset((owner_bank, owner_pc)):at]
    oam_calls = [m.start() for m in re.finditer(re.escape(bytes((0xcd, oam_pc & 255, oam_pc >> 8))), body)]
    if len(oam_calls) != 1:
        raise ValueError('Owner-transition OAM call changed; update the trace points')
    oam_call = owner_pc + oam_calls[0]
    for name, address in (('owner_oam_call', oam_call), ('owner_oam_return', oam_call + 3),
                          ('owner_oam_entry', oam_pc)):
        lines.append(f'{{{owner_bank}, 0x{address:04x}, "{name}"}},')
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DDEX_LISTING_RESTORE_TRACE', f'-DDEX_LISTING_RESTORE_SYMBOLS="{header}"',
        *extra_flags))


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


def physical_vblank_bounds(trace, commit_t):
    lines = [e for e in trace if e['event'] == 'line']
    start = next(e for e in reversed(lines) if e['physical_line'] == 144 and e['boundary_t'] <= commit_t)
    end = next(e for e in lines if e['physical_line'] == 0 and e['boundary_t'] > start['boundary_t'])
    if end['boundary_t'] - start['boundary_t'] != 4560:
        raise ValueError('Physical VBlank boundaries differ from ten 456-cycle lines')
    return start['boundary_t'], end['boundary_t']


def summarize(trace, reference):
    phases = [e for e in trace if e['event'] == 'phase']
    frames = [e for e in trace if e['event'] == 'frame']
    writes = [e for e in trace if e['event'] == 'write']
    leave = next(e for e in phases if e['phase'] == 'leave')
    reveal = next(e for e in phases if e['phase'] == 'listing_revealed')
    wx = next(e for e in phases if e['phase'] == 'owner_wx')
    commit = next(e for e in reversed(phases) if e['phase'] == 'owner_dispatch' and e['t'] < wx['t'])
    done = next(e for e in phases if e['phase'] == 'owner_done')
    returned = next(e for e in phases if e['phase'] == 'owner_returned' and e['t'] > done['t'])
    start_t, end_t = physical_vblank_bounds(trace, commit['t'])
    final = phases[-1]
    palette_entry = next(e for e in phases if e['t'] > commit['t'] and
                         e['phase'] in ('bg_pal_commit', 'listing_bg_pal_commit'))
    oam_return = next(e for e in phases if e['phase'] == 'owner_oam_return')
    owner_palette_writes = [e for e in writes if commit['t'] <= e['t'] < returned['t']
                            and e['address'] in (0xff69, 0xff6b)]
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
        commit_return_cycles=returned['t'] - commit['t'],
        commit_return_physical_line=returned['physical_line'],
        vblank_start_t=start_t, visible_start_t=end_t,
        entry_offset_in_vblank=commit['t'] - start_t,
        available_vblank_cycles=end_t - commit['t'],
        return_vblank_margin=end_t - returned['t'],
        maps_vblank_margin=end_t - palette_entry['t'],
        bg_palette_first_use_margin=end_t + 40 * 456 -
            max((e['t'] for e in owner_palette_writes if e['address'] == 0xff69), default=commit['t']),
        obj_palette_first_use_margin=end_t + 34 * 456 -
            max((e['t'] for e in owner_palette_writes if e['address'] == 0xff6b), default=commit['t']),
        oam_first_use_margin=end_t + 34 * 456 - oam_return['t'],
        palette_write_count=len(owner_palette_writes),
        cache_rows_prepared=sum(e['phase'] == 'prepare_cache_row' for e in phases),
        cache_rows_uploaded=sum(e['phase'] == 'cache_row_uploaded' for e in phases),
        cache_repaired=any(e['phase'] == 'cache_repair' for e in phases),
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
                           physical_line=e['physical_line'],
                           display=e['display'], bg_dirty=e['bg_dirty'], obj_dirty=e['obj_dirty'])
                      for e in phases if e['phase'] != 'owner_dispatch' or e['owner_transition']],
    )


def restoration_failures(summary):
    """Listing publication checks; outgoing canceled-cry events are reported separately."""
    failures = []
    if summary['blocked_palette_writes']:
        failures.append('blocked_palette_write')
    if any(summary['visible_palette_mismatch_bytes'].values()):
        failures.append('visible_palette_mismatch')
    if summary['white_frames']:
        failures.append('white_frame')
    if summary['lcd_changes']:
        failures.append('lcd_toggled')
    if summary['palette_write_count'] != 96:
        failures.append('palette_write_count')
    for name in ('maps_vblank_margin', 'bg_palette_first_use_margin',
                 'obj_palette_first_use_margin', 'oam_first_use_margin'):
        if summary[name] <= 0:
            failures.append(name)
    return failures


def listing_snapshot(driver, prefix):
    driver.command(f'restoretrace {prefix} 0')
    driver.command('restorestop')
    return json.loads(prefix.with_suffix('.jsonl').read_text().splitlines()[0])


def cache_rows(snapshot):
    tags = bytes.fromhex(snapshot['grid_tags'])
    vram = bytes.fromhex(snapshot['vram'])
    return {int.from_bytes(tags[2 * row:2 * row + 2], 'little'):
            b''.join(vram[start + row * 128:start + (row + 1) * 128]
                     for start in (0x2000, 0x3000, 0x2d20)) for row in range(5)}


def check_listing_snapshot(actual, expected, count, all_rows=True):
    """Compare cache bytes by absolute row tag, not by changing ring positions."""
    problems = []
    tags = bytes.fromhex(actual['grid_tags'])
    scroll, top = actual['listing_scroll'], actual['grid_top']
    presence = bytes.fromhex(actual['grid_presence'])
    if any(value not in (0, 1) for value in presence):
        problems.append('grid_presence_not_boolean')
    if presence != bytes(int(scroll + i < count) for i in range(9)):
        problems.append('grid_presence')
    if actual['grid_presence'] != expected['grid_presence']:
        problems.append('grid_presence_reference')
    rows, expected_rows = cache_rows(actual), cache_rows(expected)
    for delta in range(-1, 4) if all_rows else range(3):
        slot = (top + delta) % 5
        tag = max(-1, scroll + delta * 3) & 65535
        if not all_rows and tag >= count:
            continue
        if int.from_bytes(tags[2 * slot:2 * slot + 2], 'little') != tag:
            problems.append(f'cache_tag_{slot}')
        if tag == 65535:
            continue  # The unused look-behind slot is not a visible blank-tile owner.
        want = expected_rows.get(tag)
        if want is None and (tag == 65535 or tag >= count):
            want = bytes(3 * 128)
        if want is None:
            problems.append(f'reference_missing_row_{tag}')
        elif rows.get(tag) != want:
            problems.append(f'cache_tiles_{tag}')
    for key in ('grid_flags', 'grid_palettes'):
        if actual[key] != expected[key]:
            problems.append(key)
    if bytes.fromhex(actual['bg_pal'])[16:] != bytes.fromhex(expected['target_bg'])[16:]:
        problems.append('bg_palette_reference')
    if bytes.fromhex(actual['obj_pal'])[:48] != bytes.fromhex(expected['target_obj'])[:48]:
        problems.append('obj_palette_reference')
    return problems


def follow_up(driver, reference_driver, checkpoints, output, count):
    """Normal-input cache, scroll/wrap and re-entry checks after a B return."""
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(label):
        actual = listing_snapshot(driver, output / label)
        index = min(actual['listing_scroll'] + 6, count - 1)
        reference_driver.command(f'load {checkpoints / "listing-states" / f"listing-{index:03}.s0"}')
        expected = listing_snapshot(reference_driver, output / f'{label}-reference')
        if actual['listing_scroll'] != expected['listing_scroll']:
            raise ValueError(f'Listing reference viewport differs: {label}')
        checks.append(dict(step=label, index=actual['index'], scroll=actual['listing_scroll'],
                           metadata_warnings=['grid_indices'] if actual.get('grid_indices') != expected.get('grid_indices') else [],
                           issues=check_listing_snapshot(actual, expected, count,
                                all_rows=label in ('returned', 'reopened-and-returned'))))
    check('returned')
    driver.command(f'restoretrace {output / "navigation"} 0')
    for n, direction in enumerate(('up', 'down', 'down', 'down', 'down', 'up', 'up', 'up', 'left', 'right')):
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        state = driver.command('peek')
        if direction == 'left' and state['index'] % 3 == 0:
            continue
        if direction == 'right' and (state['index'] % 3 == 2 or state['index'] + 1 == count):
            continue
        move(driver, direction)
        driver.run(('end_loop',))
        driver.run(('end_loop',))
        driver.command('restorestop')
        (output / 'navigation.jsonl').rename(output / f'navigation-{n}.jsonl')
        check(f'navigate-{n}-{direction}')
        driver.command(f'restoretrace {output / "navigation"} 0')
    driver.command('restorestop')
    navigation = [json.loads(line) for p in output.glob('navigation*.jsonl') for line in p.read_text().splitlines()]
    rejected = [e for e in navigation if e['event'] == 'write' and e['address'] in (0xff69, 0xff6b) and e['pal_blocked']]
    current = listing_snapshot(driver, output / 'before-reentry')
    seen = bytes.fromhex(current['grid_flags'])[current['cursor']] & 1
    driver.run(('accept',), key='a')
    if seen:
        settle(driver)
        driver.run(('leave',), key='b')
    returned = driver.run(('listing',), 600)
    if returned['hit'] != 'listing':
        raise RuntimeError('Post-repair re-entry did not return to Listing')
    driver.run(frames=5)
    check('reopened-and-returned' if seen else 'unseen-selection-ignored')
    result = dict(checks=checks, blocked_navigation_palette_writes=rejected,
                  reentry='selected_and_returned' if seen else 'unseen_selection_ignored',
                  metadata_warnings=[f'{c["step"]}:{warning}' for c in checks for warning in c['metadata_warnings']],
                  issues=([f'{c["step"]}:{issue}' for c in checks for issue in c['issues']]
                          + (['blocked_navigation_palette_write'] if rejected else [])))
    (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


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
    if 'moves_page' in case:
        # The frozen baseline has no Moves tab; compare its Description return.
        if case.get('moves_supported', True):
            from .info_ui import press
            from .moves_ui import ready
            for _ in range(2):
                press(driver, 'right')
            press(driver, 'a')
            ready(driver, 0)
            for page in range(1, case['moves_page'] + 1):
                press(driver, 'a')
                ready(driver, page)
            for _ in range(case.get('moves_internal_pages', 0)):
                driver.run(frames=2)
                driver.run(('change_species',), key='down')
                driver.run(('selected', 'animation_miss', 'audio_miss'))
                ready(driver, 0)
                settle(driver)
            if 'moves_cancel_frames' in case:
                driver.run(frames=1, key='a')
                driver.run(frames=case['moves_cancel_frames'])
    if 'info_page' in case:
        from .info_ui import press, ready
        press(driver, 'right')
        press(driver, 'a')
        ready(driver, 0)
        for page in range(1, case['info_page'] + 1):
            press(driver, 'a')
            ready(driver, page)
        ui = driver.command('ui')
        if ui['view'] != 1 or ui['info_page'] != case['info_page'] or ui['info_state']:
            raise RuntimeError(f'Return probe is not on the requested Info page: {case}: {ui}')
        for _ in range(case.get('info_internal_pages', 0)):
            driver.run(frames=2)
            changed = driver.run(('change_species',), key='down')
            if changed['hit'] != 'change_species':
                raise RuntimeError(f'Info internal paging was not accepted: {case}: {changed}')
            driver.run(('selected', 'animation_miss', 'audio_miss'))
            ready(driver, 0)
            settle(driver)
        if 'info_cancel_frames' in case:
            driver.run(frames=1, key='a')
            driver.run(frames=case['info_cancel_frames'])
        if 'description_cancel_frames' in case:
            press(driver, 'left')
            driver.run(frames=1, key='a')
            driver.run(frames=case['description_cancel_frames'])
    selected = driver.command('peek')
    driver.command(f'image {directory / "selected-before.ppm"}')
    driver.command(f'save {directory / "selected-before.s0"}')
    driver.command(f'restoretrace {directory / "trace"} {int(images)}')
    driver.command(f'restoreadmission {case.get("admission_delay", 0)}')
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
    report['restoration_failures'] = restoration_failures(report['summary'])
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
    for pages, info in ((0, None), (1, None), (9, None), (0, 0), (0, 1)):
        samples = []
        for tracing, core in ((False, control_core), (True, observed_core)):
            driver = Driver(core, checkpoints / 'input-copy.gbc',
                Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
                checkpoints / 'input-copy.sav', control / f'core-{pages}-{info}-{tracing}.log')
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
                if info is not None:
                    from .info_ui import press, ready
                    press(driver, 'right')
                    press(driver, 'a')
                    ready(driver, 0)
                    for page in range(1, info + 1):
                        press(driver, 'a')
                        ready(driver, page)
                if tracing:
                    driver.command(f'restoretrace {control / f"observed-{pages}-{info}"} 1')
                left = driver.run(('leave',), key='b')
                returned = driver.run(('listing',), 600)
                final = driver.run(frames=5)
                ui = driver.command('ui')
                image = control / f'final-{pages}-{info}-{tracing}.ppm'
                driver.command(f'image {image}')
                if tracing:
                    driver.command('restorestop')
                samples.append(dict(left=left, returned=returned, final=final,
                                    ui=ui, pixels=image.read_bytes()))
            finally:
                driver.close()
        same = samples[0] == samples[1]
        results.append(dict(pages=pages, info_page=info, cycles_state_palettes_maps_pixels_equal=same))
        if not same:
            raise RuntimeError(f'Host instrumentation changed replay output: {pages}:{info}')
    (output / 'observer-control.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym', help='Matching symbols, including explicit baseline comparisons')
    parser.add_argument('--case', action='append', help='Run only these case labels')
    parser.add_argument('--no-images', action='store_true')
    parser.add_argument('--sparse', action='store_true', help='Boot a separate sparse-seen battery fixture')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--verify-observer', action='store_true')
    parser.add_argument('--expect-fixed', action='store_true', help='Fail if any Listing publication check fails')
    parser.add_argument('--follow-up', action='store_true', help='Audit cache bytes, scrolling/wrapping and re-entry after every return')
    parser.add_argument('--admission-sweep', action='store_true', help='Separate synthetic pre-publication CPU-stall timing stress')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.checkpoints / 'input-copy.gbc', args.sym)
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
    suite = cases(names)
    if 'PokedexInfo_Service' in repo.symbols:
        suite += [dict(label=f'{name}-info{page + 1}', start=name, pages=0,
                       wait=wait, description_page=False, info_page=page)
                  for name, page, wait in (
                      ('chikorita', 0, None), ('chikorita', 1, None),
                      ('tyrogue', 2, None), ('eevee', 3, None),
                      ('chansey', 0, None), ('blissey', 0, None),
                      ('skitty', 1, None), ('dusknoir', 0, 8), ('kyogre', 0, 0))]
        suite += [dict(label=f'chikorita-info-down{n}', start='chikorita', pages=0,
                       wait=None, description_page=False, info_page=0,
                       info_internal_pages=n) for n in (1, 2)]
    suite = [c for c in suite if args.case is None or c['label'] in args.case]
    if args.follow_up and args.case is None:
        suite.append(dict(label='regigigas', start='regigigas', pages=0, wait=None, description_page=False))
    if args.admission_sweep:
        base = next(c for c in cases(names) if c['label'] == 'chikorita-down1')
        suite = [dict(base, label=f'admission-{delay}', admission_delay=delay)
                 for delay in (*range(0, 164, 4), 256, 456)]
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
    reference_driver = Driver(core, rom,
        Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
        battery, args.output / 'reference-core.log') if args.follow_up else None
    try:
        if sparse:
            bootstrap(driver)
            prepare_states(driver, checkpoints / 'listing-states', len(names) if args.follow_up else 3)
        for case in suite:
            report = run_case(driver, checkpoints, args.output, case, names, not args.no_images)
            if reference_driver:
                report['follow_up'] = follow_up(driver, reference_driver, checkpoints,
                    args.output / case['label'] / 'follow-up', len(names))
                (args.output / case['label'] / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            results.append(report)
            summary = report['summary']
            print(json.dumps(dict(case=case['label'], intervals=summary['return_intervals'],
                rebuilt=summary['cache_rebuilt'], blocked=len(summary['blocked_palette_writes']),
                mismatches=summary['palette_mismatch_bytes'])), flush=True)
    finally:
        driver.close()
        if reference_driver:
            reference_driver.close()
    (args.output / 'report.json').write_text(json.dumps(dict(
        provenance=repo.hashes, rom_unchanged=True, host_only_instrumentation=True,
        sparse_fixture=sparse, results=results), indent=2) + '\n')
    return int(args.expect_fixed and any(r['restoration_failures'] or r.get('follow_up', {}).get('issues') for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
