"""Host-only diagnostics for Selected-to-Selected species transitions.

The baseline runs a byte-identical copy of the accepted ROM. Optional private
overlays test proposed fixes without changing the production sources. Tracing
records physical display frames, palette writes and preparation boundaries. A
checksum-verified sparse-seen battery supplies historical paging neighbors.
All executable and capture output belongs in the ignored build directory.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from .assets import Repository, offset, read_symbols, sha256
from .cold_listing import Driver, FRAME, ROOT, audit as audit_animation, bootstrap, build_core, move, predecessor, prepare_states
from .cry_ownership import sparse_fixture, validate_output
from .description_ui import audit as audit_ui, audit_footprint, settle
from .listing_restoration import FIELDS

BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
PHASES = dict(
    change='PokedexSelectedMon_ChangeSpecies', hidden='PokedexSelectedMon_BeginHiddenTransition',
    stage='PokedexSelectedMon_StageDescription',
    static_prepare='Pokedex_PrepareSelectedMonTiles',
    static_upload='Pokedex_CommitPreparedSelectedMonGFX',
    static_ready='PokedexSelectedMon_StageDescription.selected_tiles_ready',
    type_upload='Pokedex_LoadDescriptionTypeGFX',
    prime='Pokedex_PrimeDescriptionAnimation',
    layout='CGB_PokedexStageSelectedMonLayout', usual_pals='Pokedex_ApplyUsualPals',
    palette_flush='ForceUpdateCGBPals',
    stage_maps='Pokedex_StageOwnerTransitionMaps',
    stage_maps_done='Pokedex_StageOwnerTransitionMaps.maps_ready',
    copy_backing='Pokedex_CopyBackingToBG', copy_maps='CopyTilemapAtOnce',
    stack_map='CopyTilemapAtOnce.CopyBGMapViaStack',
    reveal='PokedexSelectedMon_Reveal', revealed='PokedexSelectedMon_ChangeSpecies.revealed',
    begin='Pokedex_BeginDescriptionAnimation',
    selected='PokedexSelectedMon_Update',
)
TARGETS = ('chikorita', 'bayleef', 'meganium', 'caterpie', 'exeggcute', 'mewtwo',
           'dusknoir', 'metagross', 'kyogre', 'rayquaza', 'luxray', 'rampardos',
           'bastiodon', 'garchomp', 'weavile', 'regigigas')
PAIRS = (('bayleef', 'meganium', 'down'), ('exeggcute', 'mewtwo', 'down'),
         ('metagross', 'dusknoir', 'up'), ('dusknoir', 'metagross', 'down'),
         ('kyogre', 'rayquaza', 'down'), ('rayquaza', 'luxray', 'down'),
         ('mewtwo', 'dusknoir', 'down'), ('luxray', 'rampardos', 'down'),
         ('garchomp', 'weavile', 'down'), ('weavile', 'garchomp', 'up'))


def prototype(repo, output, variant):
    """Assemble verified overlays solely into unused bytes of a copied image."""
    labels = '''CopyPals Pokedex_PrepareSelectedMonTiles Pokedex_CommitPreparedSelectedMonGFX
        PokedexSelectedMon_BeginHiddenTransition PokedexSelectedMon_Reveal Pokedex_CopyBackingToBG
        wOBPals1 wOBPals2 wBGPals2 wPokedexSelectedState wPokedexOwnerAttrmapBuffer
        wPokedexOwnerTilemapBuffer hCGB hCGBPalUpdate wPokedexSelectedBGPaletteDirty
        wPokedexSelectedOBJPaletteDirty FarCall'''.split()
    hardware = dict(rBGP=0xff47, rOBP0=0xff48, rSVBK=0xff70, rVBK=0xff4f,
                    rLY=0xff44, rBGPI=0xff68, rBGPD=0xff69,
                    rHDMA1=0xff51, rHDMA2=0xff52, rHDMA3=0xff53, rHDMA4=0xff54, rHDMA5=0xff55)
    definitions = [f'DEF {name} EQU ${value:04x}' for name, value in hardware.items()]
    for label in labels:
        bank, pc = repo.symbols[label]
        definitions += [f'DEF {label} EQU ${pc:04x}', f'DEF B_{label} EQU ${bank:02x}']
    source = output / 'private-overlay.asm'
    source.write_text('\n'.join(definitions) + '\nINCLUDE "' +
        str(ROOT / 'tools/dex_timing/probes/internal_transition_prototype.asm') + '"\n')
    obj, binary, sym = (output / name for name in ('private-overlay.o', 'private-overlay.bin', 'private-overlay.sym'))
    subprocess.run(['rgbasm', '-o', str(obj), str(source)], check=True)
    subprocess.run(['rgblink', '-o', str(binary), '-n', str(sym), str(obj)], check=True)
    overlay_symbols = {name: value for name, value in read_symbols(sym).items() if name.startswith('Prototype')}
    private, linked = bytearray(repo.rom), binary.read_bytes()
    sizes = {}
    for start, end in (('PrototypeStagePals', 'PrototypeStagingEnd'),
                       ('PrototypeCopyBacking', 'PrototypePublicationEnd')):
        a, b = offset(overlay_symbols[start]), offset(overlay_symbols[end])
        if len(set(repo.rom[a:b])) != 1 or repo.rom[a] not in (0, 255):
            raise ValueError('Overlay would overwrite used ROMX bytes')
        private[a:b] = linked[a:b]
        sizes[start] = b - a
    def replace_call(start, end, old, new, far=False):
        a, b = offset(repo.symbols[start]), offset(repo.symbols[end])
        old_bank, old_pc = repo.symbols[old]
        bank, pc = overlay_symbols[new]
        instruction = (bytes((0x3e, old_bank, 0x21, old_pc & 255, old_pc >> 8, 0xcf)) if far else
                       bytes((0xcd, old_pc & 255, old_pc >> 8)))
        code = bytes(private[a:b])
        if code.count(instruction) != 1:
            raise ValueError('Private call overlay no longer matches: ' + old)
        at = a + code.index(instruction)
        private[at:at + len(instruction)] = (bytes((0x3e, bank, 0x21, pc & 255, pc >> 8, 0xcf)) if far else
                                           bytes((0xcd, pc & 255, pc >> 8)))
    replace_call('PokedexSelectedMon_StageDescription', 'PokedexSelectedMon_BeginHiddenTransition',
                 'Pokedex_ApplyUsualPals', 'PrototypeStagePals', True)
    if variant != 'palette-only':
        replace_call('Pokedex_PublishOrStageDescriptionBacking.publish', 'Pokedex_PublishOrStageListingBacking',
                     'Pokedex_CopyBackingToBG', 'PrototypeCopyBacking')
        replace_call('PokedexSelectedMon_ChangeSpecies', 'PokedexSelectedMon_Leave',
                     'PokedexSelectedMon_Reveal', 'PrototypeAlreadyRevealed')
    if variant == 'late-hide':
        a, b = offset(repo.symbols['PokedexSelectedMon_ChangeSpecies']), offset(repo.symbols['PokedexSelectedMon_Leave'])
        pc = repo.symbols['PokedexSelectedMon_BeginHiddenTransition'][1]
        instruction = bytes((0xcd, pc & 255, pc >> 8))
        if bytes(private[a:b]).count(instruction) != 1:
            raise ValueError('Early hiding call changed')
        at = a + bytes(private[a:b]).index(instruction)
        private[at:at + 3] = bytes(3)
        replace_call('PokedexSelectedMon_StageDescription', 'PokedexSelectedMon_BeginHiddenTransition',
                     'Pokedex_PrepareAndCommitSelectedMonGFX', 'PrototypePrepareThenHide', True)
    repo.rom = bytes(private)
    repo.symbols.update(overlay_symbols)
    return dict(variant=variant, private_only=True, private_rom_sha256=sha256(private), overlay_sizes=sizes)


def compile_observer(repo, source, output, variant=None):
    header = (output / 'transition-symbols.h').resolve()
    lines = [f'#define R_{name} 0x{repo.symbols[name][1]:04x}' for name in FIELDS]
    lines += [f'#define R_wPokedexGridCells 0x{repo.symbols["wPokedexGridOccupied"][1]:04x}',
              '#define R_GRID_USES_PRESENCE 1']
    points = {name: repo.symbols[label] for name, label in PHASES.items()}
    integrated = 'PokedexSelectedMon_StageUsualPals' in repo.symbols
    static_target = ('Pokedex_CommitPreparedSelectedMonGFX' if integrated else
                     'Pokedex_PrepareAndCommitSelectedMonGFX')
    usual_target = ('PokedexSelectedMon_StageUsualPals' if integrated else
                    'Pokedex_ApplyUsualPals')
    start = repo.symbols['PokedexSelectedMon_StageDescription']
    end = repo.symbols['PokedexSelectedMon_BeginHiddenTransition']
    code = repo.rom[offset(start):offset(end)]
    for name, target, far in (
        ('static_committed', static_target, True),
        ('types_ready', 'Pokedex_LoadDescriptionTypeGFX', True),
        ('prime_done', 'Pokedex_PrimeDescriptionAnimation', False),
        ('layout_done', 'CGB_PokedexStageSelectedMonLayout', True),
        ('usual_done', usual_target, not integrated),
    ):
        replacements = {'Pokedex_ApplyUsualPals': 'PrototypeStagePals'} if variant else {}
        if variant == 'late-hide':
            replacements['Pokedex_PrepareAndCommitSelectedMonGFX'] = 'PrototypePrepareThenHide'
        bank, pc = repo.symbols[replacements.get(target, target)]
        instruction = (bytes((0x3e, bank, 0x21, pc & 255, pc >> 8,
                              0xc7 + repo.symbols['FarCall'][1])) if far else
                       bytes((0xcd, pc & 255, pc >> 8)))
        if code.count(instruction) != 1:
            raise ValueError('Linked staging call changed: ' + target)
        points[name] = start[0], start[1] + code.index(instruction) + len(instruction)
    wait = repo.symbols['CopyTilemapAtOnce.wait2']
    if repo.rom[offset(wait) + 6] != 0xfb:
        raise ValueError('Map-copy wait exit changed')
    points['maps_wait_done'] = wait[0], wait[1] + 6
    if variant:
        points['usual_pals'] = repo.symbols['PrototypeStagePals']
    if variant in ('fast-maps', 'late-hide'):
        points['copy_backing'] = repo.symbols['PrototypeCopyBacking']
        points['reveal'] = repo.symbols['PrototypeCommitted']
        points['fast_commit'] = repo.symbols['PrototypeCommit']
        points['fast_commit_done'] = repo.symbols['PrototypeCommitted']
    if integrated:
        points['usual_pals'] = repo.symbols[usual_target]
        points['copy_backing'] = repo.symbols['Pokedex_QueueOwnerTransition']
        points['reveal'] = repo.symbols['Pokedex_VBlankOwnerTransition.committed']
        points['fast_commit'] = repo.symbols['Pokedex_VBlankOwnerTransition']
        points['owner_dispatch'] = points['fast_commit']
        points['fast_commit_done'] = points['reveal']
        dispatch_bank, dispatch_pc = repo.symbols['Pokedex_VBlankDispatch']
        owner_pc = points['fast_commit'][1]
        at = offset((dispatch_bank, dispatch_pc))
        if repo.rom[at:at + 3] != bytes((0xcd, owner_pc & 255, owner_pc >> 8)):
            raise ValueError('Owner-transition caller changed')
        points['owner_returned'] = dispatch_bank, dispatch_pc + 3
    lines += ['static const struct { unsigned bank, pc; const char *name; } restoration_points[] = {']
    lines += [f'{{{bank}, 0x{pc:04x}, "{name}"}},' for name, (bank, pc) in points.items()]
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DDEX_LISTING_RESTORE_TRACE', '-DDEX_INTERNAL_TRANSITION_TRACE',
        f'-DDEX_LISTING_RESTORE_SYMBOLS="{header}"'))


def names_in_order():
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    return [aliases.get(name, name.lower()) for name in names]


def enter(driver, checkpoints, index):
    prior, direction = predecessor(index)
    driver.command(f'load {checkpoints / "listing-states" / f"listing-{prior:03}.s0"}')
    driver.command('rawcolor')
    move(driver, direction, index)
    driver.run(('end_loop',))
    driver.run(('end_loop',))
    driver.run(('accept',), key='a')
    state = driver.run(('selected', 'animation_miss', 'audio_miss'))
    if state['hit'] != 'selected':
        raise RuntimeError('Entry did not reach Selected: ' + str(state))
    return state


def summarize(trace, events):
    phases = [e for e in trace if e['event'] == 'phase']
    change = next(e for e in phases if e['phase'] == 'change')
    revealed = next(e for e in phases if e['phase'] == 'revealed')
    points = {e['phase']: e for e in phases if change['t'] <= e['t'] <= revealed['t']}
    writes = [e for e in trace if e['event'] == 'write' and change['t'] <= e['t'] <= revealed['t']]
    flushes = [e for e in phases if e['phase'] == 'palette_flush' and change['t'] <= e['t'] <= revealed['t']]
    after_layout = points['layout_done']['t']
    early = [e for e in flushes if after_layout < e['t'] < points['reveal']['t']]
    blocks = (
        ('hide_and_text', 'change', 'static_prepare'),
        ('static_prepare', 'static_prepare', 'static_upload'),
        ('static_commit', 'static_upload', 'static_ready'),
        ('types_and_footprint', 'static_ready', 'prime'),
        ('animation_startup', 'prime', 'prime_done'),
        ('palette_staging', 'prime_done', 'stage_maps'),
        ('row_padding', 'stage_maps', 'copy_backing'),
        ('backing_publication', 'copy_backing', 'reveal'),
        ('reveal_wait', 'reveal', 'revealed'),
    )
    pubs = [e for e in events if e['event'] == 'publish' and e['t'] >= revealed['t']]
    frames = [e for e in trace if e['event'] == 'frame']
    old_header = phases[0]['header_hash']
    new_header = phases[-1]['header_hash']
    black = [e for e in frames if e['black']]
    visible_incoming = [e for e in frames if not e['black'] and e['header_hash'] == new_header]
    mixed_header = [e for e in frames if not e['black'] and e['header_hash'] not in (old_header, new_header)]
    exposed = [e for e in frames if not e['black'] and points['static_ready']['t'] < e['t'] < points['reveal']['t']]
    vblank_start = next((e['boundary_t'] for e in reversed(trace)
        if e['event'] == 'line' and e['physical_line'] == 144 and
        e['boundary_t'] <= points['reveal']['t']), None)
    commit_return = next((e['t'] for e in phases if e['phase'] == 'owner_returned'
        and points['reveal']['t'] < e['t']), None)
    commit_writes = [e for e in writes if 'fast_commit' in points and
                    points['fast_commit']['t'] <= e['t'] <= points['reveal']['t']]
    return dict(
        accepted_to_revealed_cycles=revealed['t'] - change['t'],
        accepted_to_revealed_intervals=(revealed['t'] - change['t']) / FRAME,
        first_publication_t=pubs[0]['t'] if pubs else None,
        black_frames=len(black),
        first_incoming_display=visible_incoming[0]['display'] if visible_incoming else None,
        unexpected_visible_header_frames=[e['display'] for e in mixed_header],
        visible_staging_frames=[e['display'] for e in exposed],
        fast_commit_cycles=(points['fast_commit_done']['t'] - points['fast_commit']['t'])
            if 'fast_commit' in points else None,
        owner_return_vblank_margin=(vblank_start + 4560 - commit_return)
            if vblank_start is not None and commit_return is not None else None,
        publication_palette_bytes=sum(e['address'] == 0xff69 for e in commit_writes),
        publication_outside_vblank=[e for e in commit_writes if e['physical_line'] < 144],
        sections={name: points[b]['t'] - points[a]['t'] for name, a, b in blocks},
        early_palette_flushes=[dict(t=e['t'], ly=e['ly'], physical_line=e['physical_line']) for e in early],
        blocked_palette_writes=[e for e in writes if e['address'] in (0xff69, 0xff6b) and e['pal_blocked']],
        lcd_changes=[e for e in writes if e['address'] == 0xff40],
        phase_timing=[{k: e[k] for k in ('phase', 't', 'ly', 'physical_line', 'display', 'pal_update')}
                      for e in phases if change['t'] <= e['t'] <= revealed['t']],
        displayed_frames=[{k: e[k] for k in ('display', 't', 'pal_update', 'state',
                                            'black', 'header_hash', 'front_hash')}
                          for e in frames],
    )


def run_case(driver, checkpoints, output, names, source, target, key, delay, images, repo, assets,
             admission_delay=None):
    label = f'{source}-to-{target}-' + ('settled' if delay is None else f'active{delay}')
    if admission_delay is not None:
        label += f'-admission{admission_delay}'
    folder = output / label
    folder.mkdir(parents=True, exist_ok=True)
    enter(driver, checkpoints, names.index(source))
    if delay is None:
        settle(driver)
    elif delay:
        driver.run(frames=delay)
    driver.run(frames=2)
    driver.command(f'image {folder / "before.ppm"}')
    driver.command(f'save {folder / "before.s0"}')
    driver.command('audit 1')
    driver.events.clear()
    driver.command(f'restoretrace {folder / "trace"} {int(images)}')
    if admission_delay is not None:
        driver.command(f'restoreadmission {admission_delay}')
    changed = driver.run(('change_species',), 180, key)
    if changed['hit'] != 'change_species':
        raise RuntimeError('Direction did not accept a species change')
    incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
    if incoming['hit'] != 'selected' or incoming['selected_index'] != names.index(target):
        raise RuntimeError(f'Wrong incoming entry: {label}: {incoming}')
    driver.run(frames=3)
    driver.command('restorestop')
    final = settle(driver)
    driver.command(f'image {folder / "after.ppm"}')
    ui = driver.command('ui')
    events = list(driver.events)
    driver.command('audit 0')
    trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
    reveal_t = next(e['t'] for e in events if e['event'] == 'reveal')
    # Active-input fixtures can publish the outgoing animation while the next
    # input poll is pending, then intentionally stop its unfinished cry. Audit
    # only the incoming owner; keep the entire raw trace as handoff evidence.
    incoming_events = [e for e in events if e['t'] >= reveal_t]
    report = dict(label=label, source=source, target=target, delay=delay, incoming=incoming,
                  final=final, events=events, final_ui_issues=audit_ui(repo, ui) + audit_footprint(repo, target, ui),
                  animation_audit=audit_animation(assets[target], changed, incoming_events, final, cold=False),
                  summary=summarize(trace, events))
    if 'PokedexSelectedMon_BeginBufferedIconTransition' in repo.symbols and images:
        from .buffered_icons import audit_transition
        report['buffered_icon_audit'] = audit_transition(folder, trace)
    (folder / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def verify_observer(repo, source, observed_core, rom, checkpoints, output):
    """Compare traced and untraced cores at identical real-input checkpoints."""
    control = output / 'observer-control'
    control.mkdir(exist_ok=True)
    plain_core = build_core(repo, source, control)
    names = names_in_order()
    results = []
    for source_name in ('bayleef', 'heracross', 'dusclops'):
        samples = []
        for tracing, core in ((False, plain_core), (True, observed_core)):
            driver = Driver(core, rom, BOOT, checkpoints / 'input-copy.sav',
                            control / f'{source_name}-{tracing}.log')
            try:
                enter(driver, checkpoints, names.index(source_name))
                settle(driver)
                driver.run(frames=2)
                if tracing:
                    driver.command(f'restoretrace {control / source_name} 1')
                driver.command('audit 1')
                driver.events.clear()
                changed = driver.run(('change_species',), key='down')
                incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
                driver.run(frames=3)
                if tracing:
                    driver.command('restorestop')
                final = settle(driver)
                ui = driver.command('ui')
                image = control / f'{source_name}-{tracing}.ppm'
                driver.command(f'image {image}')
                samples.append(dict(changed=changed, incoming=incoming, final=final,
                                    events=list(driver.events), ui=ui, pixels=image.read_bytes()))
            finally:
                driver.close()
        same = samples[0] == samples[1]
        results.append(dict(source=source_name, cycles_state_events_maps_palettes_pixels_equal=same))
        if not same:
            raise RuntimeError('Host observer changed transition output: ' + source_name)
    (control / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--sym', type=Path, help='Matching symbols for baseline or production checkpoints')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--sparse', action='store_true')
    parser.add_argument('--reuse-states', action='store_true')
    parser.add_argument('--active', action='store_true')
    parser.add_argument('--all-species', action='store_true')
    parser.add_argument('--prototype', choices=('palette-only', 'fast-maps', 'late-hide'))
    parser.add_argument('--no-images', action='store_true')
    parser.add_argument('--verify-observer', action='store_true')
    parser.add_argument('--admission-sweep', action='store_true',
        help='Separate host-only CPU-stall stress at internal owner admission')
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    validate_output(args.output, [args.checkpoints])
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.checkpoints / 'input-copy.gbc', args.sym or ROOT / 'pokecrystal.sym')
    origin = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(origin[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Checkpoints do not match this ROM and symbols')
    rom = args.output / 'diagnostic-input.gbc'
    experiment = prototype(repo, args.output, args.prototype) if args.prototype else None
    if args.admission_sweep and (args.prototype or 'PokedexSelectedMon_StageUsualPals' not in repo.symbols):
        raise ValueError('Internal admission stress requires the integrated production profile')
    rom.write_bytes(repo.rom)
    core = compile_observer(repo, args.sameboy, args.output, args.prototype)
    if args.verify_observer:
        print(json.dumps(dict(observer_control=verify_observer(repo, args.sameboy, core, rom,
            args.checkpoints, args.output))), flush=True)
    assets = {asset.name: asset for asset in repo.load()}
    names = names_in_order()
    battery, checkpoints = args.checkpoints / 'input-copy.sav', args.checkpoints
    fixture = None
    if args.sparse:
        battery = args.output / 'sparse-input.sav'
        fixture = sparse_fixture(repo, args.checkpoints / 'input-copy.sav', battery, TARGETS)
        checkpoints = args.output
    driver = Driver(core, rom, BOOT, battery, args.output / 'core.log')
    results = []
    try:
        if args.sparse and not args.reuse_states:
            (checkpoints / 'listing-states').mkdir(exist_ok=True)
            bootstrap(driver)
            prepare_states(driver, checkpoints / 'listing-states', len(names))
        pairs = PAIRS if args.sparse else tuple(
            (name, names[names.index(name) + 1], 'down') for name in TARGETS if name != 'regigigas')
        if args.all_species:
            if args.sparse:
                raise ValueError('All-species coverage requires the all-seen fixture')
            pairs = tuple((name, names[(i + 1) % len(names)], 'down') for i, name in enumerate(names))
        for source, target, key in pairs:
            if args.case and source not in args.case:
                continue
            for delay in (None, 0, 4, 16) if args.active else (None,):
                stalls = (*range(0, 164, 4), 256, 456) if args.admission_sweep else (None,)
                for stall in stalls:
                    report = run_case(driver, checkpoints, args.output, names, source, target, key,
                                      delay, not args.no_images, repo, assets, stall)
                    results.append(report)
                    s = report['summary']
                    print(json.dumps(dict(case=report['label'],
                        intervals=s['accepted_to_revealed_intervals'], black_frames=s['black_frames'],
                        early_flushes=len(s['early_palette_flushes']),
                        mixed_header_frames=s['unexpected_visible_header_frames'],
                        visible_staging=s['visible_staging_frames'],
                        blocked_writes=len(s['blocked_palette_writes']),
                        buffered_icon_issues=report.get('buffered_icon_audit', {}).get('issues'),
                        animation_issues=report['animation_audit']['issues'])), flush=True)
    finally:
        driver.close()
    (args.output / 'report.json').write_text(json.dumps(dict(provenance=repo.hashes,
        copied_unchanged_rom=not args.prototype, private_experiment=experiment,
        fixture=fixture, cases=results), indent=2) + '\n')


if __name__ == '__main__':
    main()
