"""Private icon-buffer cost/timing preflight, with no production source edits."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

import numpy as np
from PIL import Image

from tools.dex_timing import cold_listing as cold
from tools.dex_timing import internal_transitions as transitions
from tools.dex_timing.assets import Repository, offset, read_symbols, sha256
from tools.dex_timing.description_ui import audit as audit_ui, settle

ROOT = cold.ROOT
OUT = ROOT / 'build/dex-icon-buffer-preflight'
ORIGIN = ROOT / 'build/dex-internal-transitions-integrated'
CHECKPOINTS = ORIGIN / 'cold'
SOURCE = Path('/Users/jakeadams/Documents/GitHub/SameBoy')
BOOT = transitions.BOOT
SYMBOLS = ROOT / 'pokecrystal.sym'
WORK = None


def make_builds():
    repo = Repository(ROOT, CHECKPOINTS / 'input-copy.gbc', SYMBOLS)
    provenance = json.loads((CHECKPOINTS / 'provenance.json').read_text())
    assert all(provenance[k] == v for k, v in repo.hashes.items())
    control = ROOT / 'build/dex-background-mask-ab/pokecrystal-dex-background-mask.gbc'
    labels = '''wPokedexSelectedState wBGPals1 Pokedex_BlackOutBG FarCall
        wPokedexWRAM0Scratch wPokedexWRAM0ScratchEnd hCGB wCurPartySpecies
        wPokedexResidentFootprintSpecies wTilemap LowVolume PokedexSelectedMon_BeginWarmTransition
        Pokedex_DrawResidentFootprint wBaseType1 wBaseType2 Pokedex_LoadDescriptionTypeGFX.PlaceType
        wPokedexSelectedSpecies Pokedex_LoadCurrentFootprint'''.split()
    definitions = ['DEF rSVBK EQU $ff70']
    for name in labels:
        bank, pc = repo.symbols[name]
        alias = name.replace('.', '_')
        definitions += [f'DEF {alias} EQU ${pc:04x}', f'DEF B_{alias} EQU ${bank:02x}']
    source = OUT / 'private-overlay.asm'
    source.write_text('\n'.join(definitions) + '\nINCLUDE "' + str(OUT / 'icon-buffer.asm') + '"\n')
    obj, binary, sym = [OUT / f'private-overlay.{ext}' for ext in ('o', 'bin', 'sym')]
    subprocess.run(['rgbasm', '-o', str(obj), str(source)], check=True)
    subprocess.run(['rgblink', '-o', str(binary), '-n', str(sym), str(obj)], check=True)
    new_symbols = {k: v for k, v in read_symbols(sym).items() if k.startswith('Prototype')}
    private = bytearray(repo.rom)
    allowed, sizes, patches = set((0x14e, 0x14f)), {}, []
    for first, last in (('PrototypeIconBank77Start', 'PrototypeIconBank77End'),
                        ('PrototypeIconBankA0Start', 'PrototypeIconBankA0End')):
        start, end = offset(new_symbols[first]), offset(new_symbols[last])
        assert len(set(repo.rom[start:end])) == 1 and repo.rom[start] in (0, 255)
        private[start:end] = binary.read_bytes()[start:end]
        allowed.update(range(start, end))
        sizes[first] = end - start

    def patch(first, last, old, new, expected=1):
        a, b = offset(repo.symbols[first]), offset(repo.symbols[last])
        code = bytes(private[a:b])
        assert code.count(old) == expected, (first, old.hex(), code.count(old))
        cursor = 0
        for _ in range(expected):
            at = a + code.index(old, cursor)
            cursor = at - a + len(old)
            assert len(old) == len(new)
            private[at:at + len(old)] = new
            allowed.update(range(at, at + len(old)))
            patches.append(dict(function=first, offset=at, before=old.hex(), after=new.hex()))

    def instruction(name, far=False, new=False):
        bank, pc = (new_symbols if new else repo.symbols)[name]
        return bytes((0x3e, bank, 0x21, pc & 255, pc >> 8, 0xcf)) if far else bytes((0xcd, pc & 255, pc >> 8))

    patch('Pokedex_BlackOutSelectedMonBG', 'Pokedex_VBlankDispatch',
          instruction('Pokedex_BlackOutBG', True), instruction('PrototypeSelectiveMask', True, True))
    patch('PokedexSelectedMon_Enter', 'PokedexSelectedMon_Update',
          instruction('LowVolume'), instruction('PrototypeInitializeIcons', new=True))
    patch('PokedexSelectedMon_ChangeSpecies', 'PokedexSelectedMon_Leave',
          instruction('PokedexSelectedMon_BeginWarmTransition'), instruction('PrototypeBeginInternalIcons', new=True))
    patch('Pokedex_CommitPreparedSelectedMonGFX', 'Pokedex_PrepareAndCommitSelectedMonGFX',
          bytes((0x11, 0x10, 0x8b)), instruction('PrototypeFootprintDestination', new=True), 2)
    address = repo.symbols['wCurPartySpecies'][1]
    patch('Pokedex_CommitPreparedSelectedMonGFX.footprint_ready', 'Pokedex_CommitPreparedSelectedMonGFX.done',
          bytes((0xfa, address & 255, address >> 8)), instruction('PrototypeFootprintResidentSpecies', new=True))
    patch('PokedexSelectedMon_StageDescription', 'PokedexSelectedMon_BeginHiddenTransition',
          instruction('Pokedex_DrawResidentFootprint', True), instruction('PrototypeDrawDescriptionFootprint', True, True))
    patch('Pokedex_LoadDescriptionTypeGFX.upload', 'Pokedex_LoadDescriptionTypeGFX.PlaceType',
          bytes((0x11, 0x40, 0x96)), instruction('PrototypeTypeDestination', new=True))
    pc = new_symbols['PrototypePlaceTypes'][1]
    place = repo.symbols['wTilemap'][1] + 7 * 20 + 9
    patch('Pokedex_LoadDescriptionTypeGFX.upload', 'Pokedex_LoadDescriptionTypeGFX.PlaceType',
          bytes((0x3e, 0x64, 0x21, place & 255, place >> 8)), bytes((0xc3, pc & 255, pc >> 8, 0, 0)))
    rom = OUT / 'private-icon-buffer-preflight.gbc'
    rom.write_bytes(private)
    subprocess.run(['rgbfix', '-v', str(rom)], check=True)
    symbols = rom.with_suffix('.sym')
    symbols.write_text(SYMBOLS.read_text() + '\n' + '\n'.join(
        f'{bank:02x}:{pc:04x} {name}' for name, (bank, pc) in new_symbols.items()) + '\n')
    differences = [i for i, pair in enumerate(zip(repo.rom, rom.read_bytes())) if pair[0] != pair[1]]
    assert all(i in allowed for i in differences)
    configs = {}
    for variant, image, symbol_file in (('blackout', control, control.with_suffix('.sym')),
                                       ('selective', rom, symbols)):
        folder = OUT / variant
        folder.mkdir(exist_ok=True)
        linked = Repository(ROOT, image, symbol_file)
        core = transitions.compile_observer(linked, SOURCE, folder)
        configs[variant] = dict(rom=str(image), sym=str(symbol_file), core=str(core))
    metadata = dict(accepted_sha256=sha256(repo.rom), prototype_sha256=sha256(rom.read_bytes()),
                    background_control_sha256=sha256(control.read_bytes()), helper_bytes=sum(sizes.values()),
                    helper_sizes=sizes, patches=patches, changed_byte_offsets=differences,
                    existing_scratch_byte=repo.symbols['wPokedexWRAM0ScratchEnd'][1] - 1,
                    additional_vram_tiles=12, additional_vram_bytes=192,
                    no_new_rom0_wram0_wramx_hram_allocations=True, configs=configs)
    (OUT / 'builds.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


def initialize(configs):
    global WORK
    WORK = {}
    for variant, config in configs.items():
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        WORK[variant] = dict(config, repo=repo, assets={a.name: a for a in repo.load()})


def palette_mask(snapshot, palettes):
    vram = bytes.fromhex(snapshot['vram'])
    sx, sy, wx, wy = snapshot['scroll']
    assert sx == 5 and sy == 0 and wx >= 167, snapshot['scroll']
    return np.array([[(vram[0x3800 + ((y + sy) // 8) * 32 + (x + sx) // 8] & 7)
                      in palettes for x in range(160)] for y in range(144)])


def white_mask(snapshot):
    return palette_mask(snapshot, (1, 2, 6, 7))


def has_selective_mask(picture, portrait, badges, variant):
    return np.all(picture[portrait] == 255) and (variant == 'selective' or np.all(picture[badges] == 41))


def normalize_buffered_ui(ui, vram):
    # The stock UI observer reads the original type allocation. Resolve actual
    # visible tiles first, then compare semantics without treating bank choice
    # as an image difference. Raw snapshots remain alongside this audit copy.
    tilemap = bytearray.fromhex(ui['map'])
    base = tilemap[7 * 21 + 9]
    assert base in (0x64, 0x70), base
    ui['type_gfx'] = vram[0x3000 + base * 16:0x3000 + base * 16 + 128].hex()
    for slot in range(2 if ui['types'][0] != ui['types'][1] else 1):
        first = 7 * 21 + 9 + 5 * slot
        assert tilemap[first:first + 4] == bytes(range(base + 4 * slot, base + 4 * slot + 4))
        tilemap[first:first + 4] = bytes(range(0x64 + 4 * slot, 0x68 + 4 * slot))
    foot = tilemap[21 + 18]
    assert foot in (0xb1, 0x6c), foot
    for cell, delta in ((21 + 18, 0), (21 + 19, 1), (42 + 18, 2), (42 + 19, 3)):
        assert tilemap[cell] == foot + delta
        tilemap[cell] = 0xb1 + delta
    ui['map'] = tilemap.hex()


def audit_footprint(repo, name, snapshot):
    names = re.findall(r'^\s*const\s+(\w+)', (ROOT / 'constants/pokemon_constants.asm').read_text(), re.M)[:373]
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in names]
    start = offset(repo.symbols['Footprints']) + names.index(name) * 32
    expected = bytes(value for byte in repo.rom[start:start + 32] for value in (byte, byte))
    vram = bytes.fromhex(snapshot['vram'])
    first = vram[0x1800 + 32 + 18]
    signed = first if first < 128 else first - 256
    at = 0x3000 + signed * 16
    return [] if vram[at:at + 64] == expected else ['incoming_footprint_graphics']


def render_background(snapshot):
    vram, pals = bytes.fromhex(snapshot['vram']), bytes.fromhex(snapshot['bg_pal'])
    sx, sy, wx, wy = snapshot['scroll']
    assert sx == 5 and sy == 0 and wx >= 167
    result = np.zeros((144, 160, 3), dtype=np.uint8)
    for y in range(144):
        for x in range(160):
            cell = 0x1800 + ((y + sy) // 8) * 32 + (x + sx) // 8
            tile, attr = vram[cell], vram[cell + 0x2000]
            tx, ty = (x + sx) & 7, (y + sy) & 7
            if attr & 32:
                tx = 7 - tx
            if attr & 64:
                ty = 7 - ty
            address = 0x1000 + (tile if tile < 128 else tile - 256) * 16 + 2 * ty
            if attr & 8:
                address += 0x2000
            color = ((vram[address] >> (7 - tx)) & 1) | (((vram[address + 1] >> (7 - tx)) & 1) << 1)
            value = int.from_bytes(pals[(attr & 7) * 8 + color * 2:(attr & 7) * 8 + color * 2 + 2], 'little')
            channels = [(value >> shift) & 31 for shift in (0, 5, 10)]
            result[y, x] = [(channel << 3) | (channel >> 2) for channel in channels]
    return result


def analyze(folder, variant, input_t, changed, final, events, repo, asset):
    trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
    phases = [e for e in trace if e['event'] == 'phase']
    start = next(e for e in phases if e['phase'] == 'trace_start')
    hidden = next(e for e in phases if e['phase'] == 'hidden')
    reveal = next(e for e in phases if e['phase'] == 'reveal')
    revealed = next(e for e in phases if e['phase'] == 'revealed')
    frames = [e for e in trace if e['event'] == 'frame']
    mask = palette_mask(start, (1,)) if variant == 'selective' else white_mask(start)
    portrait = palette_mask(start, (1,))
    badges = palette_mask(start, (2, 6, 7))
    pictures = {frame['display']: np.asarray(Image.open(folder / f'trace-{frame["display"]:03}.ppm')) for frame in frames}
    stage_candidates = [frame for frame in frames if hidden['t'] < frame['t'] < reveal['t'] and
        has_selective_mask(pictures[frame['display']], portrait, badges, variant)]
    # Input polling can update the ordinary blinking footer cursor before the
    # warm transition freezes the outgoing backing. Preserve that final owner.
    old_frame = next(frame for frame in reversed(frames) if frame['t'] < stage_candidates[0]['t'])
    before = pictures[old_frame['display']]
    first_change, first_complete = None, None
    issues, staging_frames = [], []
    for frame in frames:
        path = folder / f'trace-{frame["display"]:03}.ppm'
        picture = np.asarray(Image.open(path))
        if frame['t'] > hidden['t'] and frame['t'] < reveal['t']:
            if has_selective_mask(picture, portrait, badges, variant):
                staging_frames.append(frame['display'])
                first_change = first_change or frame
                if not np.array_equal(picture[~mask], before[~mask]):
                    issues.append(f'outside_mask_pixels_changed_{frame["display"]}')
                expected_pals = bytearray.fromhex(start['bg_pal'])
                expected_pals[8:16] = bytes((255, 127)) * 4
                if variant == 'blackout':
                    for palette in (2, 6, 7):
                        expected_pals[palette * 8:(palette + 1) * 8] = bytes((165, 20)) * 4
                if bytes.fromhex(frame['bg_pal']) != expected_pals:
                    issues.append(f'wrong_mask_palette_{frame["display"]}')
        if frame['t'] > reveal['t'] and first_complete is None:
            first_complete = frame
            # The owner commit before this scan must have published the incoming
            # backing and every used palette; frame capture ends the full scan.
            target = bytes.fromhex(reveal['target_bg'])
            actual = bytes.fromhex(reveal['bg_pal'])
            if any(actual[i] != target[i] for i in (*range(24), *range(48, 64))):
                issues.append('incoming_palette_mismatch')
            expected_picture = render_background(reveal)
            # The live footer blink is deliberately resumed before the first
            # complete incoming display. Check its actual current tile too.
            expected_picture[136:144, 3:11] = render_background(frame)[136:144, 3:11]
            if not np.array_equal(picture, expected_picture):
                issues.append('incoming_reveal_pixels')
        Image.open(path).save(path.with_suffix('.png'))
        path.unlink()
    if not first_change or not first_complete:
        issues.append('missing_transition_display')
    writes = [e for e in trace if e['event'] == 'write']
    if any(e['pal_blocked'] for e in writes if e['address'] in (0xff69, 0xff6b)):
        issues.append('blocked_palette_write')
    if any(e['address'] == 0xff40 for e in writes):
        issues.append('lcd_toggle')
    if variant == 'selective' and any(e['white'] or e['black'] for e in frames):
        issues.append('full_screen_flash')
    incoming_events = [e for e in events if e['t'] >= revealed['t']]
    animation = cold.audit(asset, changed, incoming_events, final, cold=False)
    issues += animation['issues']
    ui = json.loads((folder / 'ui.json').read_text())
    if variant == 'selective':
        normalize_buffered_ui(ui, bytes.fromhex(reveal['vram']))
        (folder / 'normalized-ui.json').write_text(json.dumps(ui, indent=2) + '\n')
    issues += audit_ui(repo, ui)
    issues += audit_footprint(repo, asset.name, reveal)
    returned = next((e['t'] for e in phases if e['phase'] == 'owner_returned' and e['t'] > reveal['t']), None)
    boundary = next(e['boundary_t'] for e in reversed(trace) if e['event'] == 'line'
                    and e['physical_line'] == 144 and e['boundary_t'] <= reveal['t'])
    metrics = dict(input_to_accept_cycles=changed['t'] - input_t,
        input_to_visible_start_cycles=first_change['t'] - input_t if first_change else None,
        input_to_visible_complete_cycles=first_complete['t'] - input_t if first_complete else None,
        input_to_revealed_cycles=revealed['t'] - input_t,
        accepted_to_revealed_cycles=revealed['t'] - changed['t'],
        masked_display_frames=len(staging_frames),
        full_black_frames=sum(e['black'] for e in frames), full_white_frames=sum(e['white'] for e in frames),
        owner_return_margin=boundary + 4560 - returned if returned else None,
        displayed_frames=len(frames), animation=animation,
        first_mask_frame=first_change['display'] if first_change else None,
        first_complete_frame=first_complete['display'] if first_complete else None,
        issues=sorted(set(issues)))
    if first_change and first_complete:
        for number in range(first_change['display'], first_complete['display']):
            picture = np.asarray(Image.open(folder / f'trace-{number:03}.png'))
            if not has_selective_mask(picture, portrait, badges, variant) or not np.array_equal(picture[~mask], before[~mask]):
                metrics['issues'].append(f'continuous_mask_{number}')
    (folder / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics


def run_pair(job):
    label, fixture, source, target, key, phase, admission = job
    result = dict(label=label, source=source, target=target, key=key, phase=phase, admission=admission)
    for variant in ('blackout', 'selective'):
        config = WORK[variant]
        folder = OUT / 'cases' / label / variant
        folder.mkdir(parents=True, exist_ok=True)
        driver = cold.Driver(config['core'], config['rom'], BOOT, CHECKPOINTS / 'input-copy.sav', folder / 'core.log')
        try:
            driver.command(f'load {fixture}')
            driver.command('rawcolor')
            # Rebuild the host's pixel buffer after loading the device state.
            driver.run(frames=1 + phase / cold.FRAME)
            driver.command(f'image {folder / "before.ppm"}')
            input_state = driver.command('peek')
            driver.command('audit 1')
            driver.events.clear()
            driver.command(f'restoretrace {folder / "trace"} 1')
            if admission is not None:
                driver.command(f'restoreadmission {admission}')
            changed = driver.run(('change_species', 'animation_miss', 'audio_miss'), 180, key)
            assert changed['hit'] == 'change_species', changed
            incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
            assert incoming['hit'] == 'selected' and incoming['selected_index'] == transitions.names_in_order().index(target), incoming
            driver.run(frames=3)
            driver.command('restorestop')
            final = settle(driver)
            events = list(driver.events)
            ui = driver.command('ui')
            (folder / 'ui.json').write_text(json.dumps(ui, indent=2) + '\n')
            driver.command(f'image {folder / "after.ppm"}')
            driver.command('audit 0')
            returned = driver.run(('listing',), 600, 'b')
            assert returned['hit'] == 'listing' and returned['index'] == transitions.names_in_order().index(target), returned
            metrics = analyze(folder, variant, input_state['t'], changed, final, events,
                              config['repo'], config['assets'][target])
            result[variant] = dict(metrics, input=input_state, accepted=changed, incoming=incoming, final=final, returned=returned)
            (folder / 'events.json').write_text(json.dumps(events, indent=2) + '\n')
        except Exception as error:
            result[variant] = dict(issues=['runner_exception'], error=repr(error))
        finally:
            driver.close()
    if 'input' in result['blackout'] and 'input' in result['selective']:
        assert result['blackout']['input'] == result['selective']['input'], 'Input phases did not match'
        assert result['blackout']['accepted'] == result['selective']['accepted'], 'Acceptance changed before the overlay'
        result['differences'] = {k: result['selective'][k] - result['blackout'][k] for k in (
            'input_to_visible_start_cycles', 'input_to_visible_complete_cycles', 'accepted_to_revealed_cycles')}
        ui = [json.loads((OUT / 'cases' / label / v / ('normalized-ui.json' if v == 'selective' else 'ui.json')).read_text()) for v in ('blackout', 'selective')]
        for state in ui:
            pals = bytes.fromhex(state['palettes'])
            state['palettes'] = (pals[:24] + pals[48:]).hex()
            if state['types'][0] == state['types'][1]:
                state['type_gfx'] = state['type_gfx'][:128]
        result['final_ui_equal'] = ui[0] == ui[1]
        result['final_pixels_equal'] = (OUT / 'cases' / label / 'blackout/after.ppm').read_bytes() == (OUT / 'cases' / label / 'selective/after.ppm').read_bytes()
    (OUT / 'cases' / label / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def jobs_for(suite):
    names = transitions.names_in_order()
    jobs = []
    sources = names if suite == 'all' else ['chikorita', 'bayleef', 'dusclops', 'metang', 'luxio', 'abomasnow', 'gabite', 'gengar', 'zangoose', 'regigigas']
    for source in sources:
        index = names.index(source)
        target = names[(index + 1) % len(names)]
        label = f'{source}-to-{target}-settled'
        fixture = ORIGIN / 'all-species' / label / 'before.s0'
        assert fixture.exists(), fixture
        jobs.append((label, str(fixture), source, target, 'down', 0, None))
    if suite in ('active', 'all'):
        for folder in sorted((ORIGIN / 'active').glob('*-active*/before.s0')):
            source, remainder = folder.parent.name.split('-to-')
            target = remainder.split('-active')[0]
            jobs.append((folder.parent.name, str(folder), source, target, 'down', 0, None))
    if suite in ('phase', 'all'):
        for source in ('bayleef', 'dusclops', 'metang', 'luxio', 'abomasnow', 'regigigas'):
            index = names.index(source)
            base = ORIGIN / 'all-species' / f'{source}-to-{names[(index + 1) % len(names)]}-settled/before.s0'
            for key, target in (('down', names[(index + 1) % len(names)]), ('up', names[(index - 1) % len(names)])):
                for phase in range(0, cold.FRAME, 4388):
                    jobs.append((f'{source}-{key}-phase{phase}', str(base), source, target, key, phase, None))
    if suite in ('admission', 'all'):
        base = ORIGIN / 'all-species/bayleef-to-meganium-settled/before.s0'
        for admission in (*range(0, 164, 4), 256, 456):
            jobs.append((f'bayleef-admission{admission}', str(base), 'bayleef', 'meganium', 'down', 0, admission))
    return jobs


def aggregate(rows):
    def distribution(values):
        return dict(min=min(values), mean=statistics.mean(values), median=statistics.median(values), max=max(values))
    return dict(cases=len(rows), failures=[dict(label=r['label'], variant=v, issues=r[v]['issues'], error=r[v].get('error'))
               for r in rows for v in ('blackout', 'selective') if r[v]['issues']],
        final_ui_mismatches=[r['label'] for r in rows if r.get('final_ui_equal') is False],
        final_pixel_mismatches=[r['label'] for r in rows if r.get('final_pixels_equal') is False],
        timings={v: {k: distribution([r[v][k] / (cold.FRAME if k.endswith('_cycles') else 1) for r in rows if k in r[v]]) for k in (
            'input_to_accept_cycles', 'input_to_visible_start_cycles', 'input_to_visible_complete_cycles',
            'accepted_to_revealed_cycles', 'masked_display_frames', 'owner_return_margin')}
                 for v in ('blackout', 'selective')},
        completion_delta_cycles=distribution([r['differences']['input_to_visible_complete_cycles'] for r in rows if 'differences' in r]),
        black_frames={v: sum(r[v].get('full_black_frames', 0) for r in rows) for v in ('blackout', 'selective')})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', choices=('pilot', 'active', 'phase', 'admission', 'all'), default='pilot')
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--reuse-builds', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    metadata = json.loads((OUT / 'builds.json').read_text()) if args.reuse_builds else make_builds()
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs, initializer=initialize, initargs=(metadata['configs'],)) as pool:
        for row in pool.map(run_pair, jobs_for(args.suite)):
            results.append(row)
            print(json.dumps(dict(case=row['label'], issues={v: row[v]['issues'] for v in ('blackout', 'selective')},
                                  differences=row.get('differences'))), flush=True)
    summary = aggregate(results)
    (OUT / f'{args.suite}-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)
    return int(bool(summary['failures'] or summary['final_ui_mismatches'] or summary['final_pixel_mismatches']))


if __name__ == '__main__':
    raise SystemExit(main())
