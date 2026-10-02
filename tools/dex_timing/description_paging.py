"""Private, read-only headless diagnostics for Selected Description A paging."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from .assets import Repository, sha256, offset
from .cold_listing import Driver, ROOT, FRAME, KEY, bootstrap, build_core, move, expected_picture
from .cry_ownership import state_without_wall_clock, validate_output
from .description_ui import settle

FIELDS = '''wTilemap wAttrmap hVBlank hBGMapMode wPokedexAnimFlags
    wPokedexAnimDeadline wPokedexOwnerTransition wPokedexDescriptionTextState
    wDexArrowCursorPosIndex'''.split()
PHASES = dict(
    toggle='PokedexSelectedMon_ToggleDescriptionPage',
    toggle_done='PokedexSelectedMon_ToggleDescriptionPage',
    release='Pokedex_ReleaseQuietAnimationOwner',
    print_entry='Pokedex_DisplayDescriptionEntry',
    print_shared='DisplayDexEntry',
    copy_bg='Pokedex_CopyBackingToBG',
    copy_full='CopyTilemapAtOnce',
    copy_attrs='CopyTilemapAtOnce.CopyBGMapViaStack',
    copy_complete='CopyTilemapAtOnce.wait2',
    copy_full_done='CopyTilemapAtOnce.CopyBGMapViaStack',
    copy_edge='Pokedex_CopyDescriptionRightEdge',
    prepare='Pokedex_PrepareDescriptionAnimation',
    commit='Pokedex_CommitDescriptionAnimation',
    publish='Pokedex_VBlankAnimationFrontpicMap.deadline_reached',
    published='Pokedex_VBlankAnimationFrontpicMap.display_recorded',
    animation_miss='Pokedex_AnimationMiss',
    get_name='GetPokemonName',
    far_string='PlaceFarString',
    print_number='PrintNum',
    print_number_impl='_PrintNum',
    get_entry='GetDexEntryPointer',
    check_caught='CheckCaughtMon',
)
TEXT_PHASES = dict(
    text_initialize='PokedexSelectedMon_InitializeDescriptionText',
    text_chunk='PokedexSelectedMon_RenderDescriptionTextChunk',
    text_ready='PokedexSelectedMon_RenderDescriptionTextChunk.ready',
    text_publish='Pokedex_VBlankDescriptionText.pending',
    text_published='Pokedex_VBlankDescriptionText.committed',
)


def compile_observer(repo, source, output):
    header = (output / 'description-paging-symbols.h').resolve()
    lines = [f'#define D_{name} 0x{repo.symbols.get(name, (0, 0))[1]:04x}' for name in FIELDS]
    bank, pc = repo.symbols['SampledCry_AsyncTimerTick']
    lines += [f'#define D_TIMER_BANK {bank}', f'#define D_TIMER_PC 0x{pc:04x}']
    lines += ['static const struct { unsigned bank, pc; const char *name; } dp_points[] = {']
    points = {**PHASES, **{name: label for name, label in TEXT_PHASES.items() if label in repo.symbols}}
    for name, label in points.items():
        bank, pc = repo.symbols[label]
        if name == 'toggle_done':
            label = 'PokedexSelectedMon_ToggleDescriptionPage.queued'
            pc = repo.symbols[label][1] if label in repo.symbols else repo.symbols['PokedexSelectedMon_ChangeSpecies'][1] - 1
            if repo.rom[bank * 0x4000 + pc - 0x4000] != 0xc9:
                raise ValueError('Description toggle return changed')
        if name == 'copy_full_done':
            pc -= 1
            if repo.rom[pc] != 0xc9:
                raise ValueError('Full-map copy return changed')
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DDEX_DESCRIPTION_PAGING_TRACE', f'-DDEX_DESCRIPTION_PAGING_SYMBOLS="{header}"'))


def caught_fixture(repo, source, destination):
    """Set only caught flags in an isolated copy, preserving seen and RTC bytes."""
    if source.resolve() == destination.resolve():
        raise ValueError('Fixture must not replace the source battery')
    original = source.read_bytes()
    result = bytearray(original)
    size = repo.symbols['wEndPokedexCaught'][1] - repo.symbols['wPokedexCaught'][1]
    count = len(re.findall(r'^\s*dw (\w+)\s*$',
                          (repo.root / 'data/pokemon/dex_order_new.asm').read_text(), re.M))
    flags = ((1 << count) - 1).to_bytes(size, 'little')
    allowed = set()
    def sram(name):
        bank, address = repo.symbols[name]
        return bank * 8192 + address - 0xa000
    for prefix in ('s', 'sBackup'):
        start, end, checksum = (sram(prefix + field) for field in ('SaveData', 'SaveDataEnd', 'Checksum'))
        if sum(original[start:end]) & 65535 != int.from_bytes(original[checksum:checksum + 2], 'little'):
            raise ValueError('Source battery checksum invalid')
        at = sram(prefix + 'PokemonData') + repo.symbols['wPokedexCaught'][1] - repo.symbols['wPokemonData'][1]
        result[at:at + size] = flags
        allowed.update(range(at, at + size))
        result[checksum:checksum + 2] = (sum(result[start:end]) & 65535).to_bytes(2, 'little')
        allowed.update((checksum, checksum + 1))
        if sum(result[start:end]) & 65535 != int.from_bytes(result[checksum:checksum + 2], 'little'):
            raise ValueError('Fixture checksum invalid')
    changes = {i for i, (a, b) in enumerate(zip(original, result)) if a != b}
    if not changes <= allowed or original[0x8000:] != result[0x8000:]:
        raise ValueError('Unrelated fixture bytes changed')
    destination.write_bytes(result)
    return dict(source_sha256=sha256(original), fixture_sha256=sha256(result),
                caught_only=True, changed_offsets=sorted(changes), rtc_unchanged=True)


def run_to(driver, repo, label=None, frames=1, keys=0):
    bank, pc = repo.symbols[label] if label else (0, 0xffff)
    result = driver.command(f'dprun {bank} {pc} {int(frames * FRAME)} {keys}')
    if label and (result['pc'] != pc or (pc >= 0x4000 and result['bank'] != bank)):
        raise RuntimeError(f'Checkpoint timed out: {label}: {result}')
    return result


def isolation_rom(repo, destination, variant):
    """Generate diagnostic counterfactuals, never a production fix/build option."""
    data = bytearray(repo.rom)
    patches = []
    begin = offset(repo.symbols['PokedexSelectedMon_ToggleDescriptionPage'])
    end = offset(repo.symbols['PokedexSelectedMon_ChangeSpecies'])
    body = data[begin:end]
    if 'keep-owner' in variant:
        target = repo.symbols['Pokedex_ReleaseQuietAnimationOwner'][1]
        call = bytes((0xcd, target & 255, target >> 8))
        if body[:3] != call:
            raise ValueError('Quiet-release call changed')
        data[begin:begin + 3] = bytes(3)
        patches.append(dict(purpose='omit quiet-owner release', offset=begin, old=call.hex(), new='000000'))
    if 'skip-copy' in variant:
        bank, target = repo.symbols['Pokedex_CopyBackingToBG']
        farcall = bytes((0x3e, bank, 0x21, target & 255, target >> 8, 0xcf))
        if body.count(farcall) != 1:
            raise ValueError('Full-screen copy farcall changed')
        at = begin + body.index(farcall)
        data[at:at + len(farcall)] = bytes(len(farcall))
        patches.append(dict(purpose='omit full-screen copy', offset=at, old=farcall.hex(), new=bytes(len(farcall)).hex()))
    if patches:
        data[0x14e:0x150] = ((sum(data[:0x14e]) + sum(data[0x150:])) & 65535).to_bytes(2, 'big')
        destination.write_bytes(data)
    return dict(variant=variant, patches=patches, original_rom_sha256=sha256(repo.rom),
                diagnostic_rom_sha256=sha256(data))


def picture_hash(picture, palette):
    value = 2166136261
    for y in range(56):
        for x in range(56):
            at = ((y // 8) * 7 + x // 8) * 16 + (y % 8) * 2
            bit = 7 - x % 8
            color = ((picture[at] >> bit) & 1) | (((picture[at + 1] >> bit) & 1) << 1)
            pixel = palette[color]
            for shift in (0, 8, 16):
                value = ((value ^ ((pixel >> shift) & 255)) * 16777619) & 0xffffffff
    return value


def description_pages(repo, name):
    """Independent expected tile IDs, including the shared '#' expansion."""
    names = re.findall(r'^\s*const\s+(\w+)',
                       (repo.root / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in names]
    at = offset(repo.symbols['PokedexDataPointerTable']) + names.index(name) * 3
    pointer = repo.rom[at:at + 3]
    at = offset((pointer[0], int.from_bytes(pointer[1:], 'little')))
    at = repo.rom.index(0x50, at) + 5
    shell_at = offset(repo.symbols['PokedexDescriptionTilemap'])
    shell = repo.rom[shell_at:shell_at + 360]
    pokemon_at = offset(repo.symbols['PlacePOKeText'])
    pokemon = repo.rom[pokemon_at:pokemon_at + 4]
    result = []
    for page in (0, 1):
        end = repo.rom.index(0x50, at)
        text = repo.rom[at:end]
        if any(c < 0x60 and c not in (0x4e, 0x54) for c in text):
            raise ValueError(f'Unsupported Description control: {name}: {text.hex()}')
        tiles = bytearray(shell[8 * 20:15 * 20])
        for y in range(10, 15):
            tiles[(y - 8) * 20 + 2:(y - 8) * 20 + 20] = bytes([0x7f] * 18)
        tiles[2] = 0x79 if page else shell[8 * 20 + 2]
        tiles[21:23] = bytes((0x77, 0x7a if page else 0x78))
        row, col = 10, 2
        for c in text:
            if c == 0x4e:
                row, col = row + 2, 2
                continue
            for glyph in pokemon if c == 0x54 else (c,):
                if row > 14 or col >= 20:
                    raise ValueError(f'Description text exceeds its box: {name}: page {page + 1}')
                tiles[(row - 8) * 20 + col] = glyph
                col += 1
        result.append(bytes(tiles))
        at = end + 1
    return result


def summarize_trace(trace, asset, pages=None):
    phases = [e for e in trace if e['event'] == 'phase']
    entry = next((e for e in phases if e['phase'] == 'toggle'), None)
    done = next((e for e in phases if e['phase'] == 'toggle_done'), None)
    frames = [e for e in trace if e['event'] == 'frame']
    pictures = [expected_picture(asset, frame) for frame in range(len(asset.plans))]
    corrupt = [e['display'] for e in frames if bytes.fromhex(e['picture']) not in pictures]
    invalid_pixels = []
    if frames and 'portrait_rgb' in frames[0]:
        hashes = {picture_hash(p, frames[0]['portrait_rgb']) for p in pictures}
        # SameBoy states do not restore the host pixel buffer. The first callback
        # can contain pre-load pixels above the starting scanline; ignore it.
        invalid_pixels = [e['display'] for e in frames[1:] if e['portrait_hash'] not in hashes]
    # The same load artifact can affect the header. Compare completed post-load
    # frames, not the partially restored host framebuffer at the first callback.
    header_changes = [e['display'] for e in frames[2:]
                      if 'header_hash' in e and e['header_hash'] != frames[1]['header_hash']]
    copy = next((e for e in phases if e['phase'] == 'copy_full'), None)
    copy_done = next((e for e in phases if e['phase'] == 'copy_full_done'), None)
    half = [e for e in phases if e['phase'] == 'copy_attrs']
    audio = [e for e in trace if e['event'] == 'audio_tick']
    published = next((e for e in phases if e['phase'] == 'text_published'), None)
    text_errors = []
    physical_pages = []
    if pages:
        for e in frames:
            tilemap = bytes.fromhex(e['map'])
            text = b''.join(tilemap[y * 21:y * 21 + 20] for y in range(8, 15))
            if text not in pages:
                text_errors.append(e['display'])
            physical_pages.append(pages.index(text) if text in pages else None)
    pixel_text_errors = []
    if frames and 'text_hash' in frames[0] and pages:
        known = {frames[i]['text_hash'] for page in (0, 1)
                 for i in (next((i for i in reversed(range(1, len(frames)))
                               if physical_pages[i] == page), None),) if i is not None}
        pixel_text_errors = [e['display'] for e in frames[1:] if e['text_hash'] not in known]
    return dict(toggle_cycles=done['t'] - entry['t'] if entry and done else None,
        text_publication_cycles=published['t'] - entry['t'] if entry and published else None,
        invalid_text_frames=text_errors, invalid_rendered_text_frames=pixel_text_errors,
        physical_pages=physical_pages,
        print_and_setup_cycles=copy['t'] - entry['t'] if copy and entry else None,
        full_copy_cycles=copy_done['t'] - copy['t'] if copy and copy_done else None,
        half_copy_timing=[dict(t=e['t'], ly=e['ly'], tick=e['tick']) for e in half],
        rendered_checks_available=bool(frames and 'portrait_rgb' in frames[0]),
        invalid_vram_portrait_frames=corrupt, invalid_rendered_portrait_frames=invalid_pixels,
        changed_header_frames=header_changes,
        quiet_on_entry=bool(entry and entry['vblank'] & 128),
        quiet_on_exit=bool(done and done['vblank'] & 128),
        longest_audio_block_interval=max((b['t'] - a['t'] for a, b in zip(audio, audio[1:])), default=None),
        toggle_start_t=entry['t'] if entry else None, toggle_done_t=done['t'] if done else None)


def validate_starts(path, isolation, sym_hash):
    """Checkpoint reuse requires an exact base ROM and symbol match."""
    origin = json.loads((path / 'provenance.json').read_text())
    if (origin['rom_sha256'] != isolation['original_rom_sha256'] or
            sha256((path / 'pokecrystal-desc-diagnostic.gbc').read_bytes()) != origin['rom_sha256'] or
            sha256((path / 'pokecrystal-desc-diagnostic.sym').read_bytes()) != sym_hash or
            origin['sym_sha256'] != sym_hash):
        raise ValueError('Starting checkpoints do not match the unmodified base ROM')


def observer_equivalence(driver, repo, start, output, label, delay):
    results = []
    for enabled in (False, True):
        driver.command(f'load {start}')
        if delay:
            run_to(driver, repo, frames=delay)
        prefix = output / f'{label}-{delay}-observer-{int(enabled)}'
        if enabled:
            driver.command(f'dptrace {prefix} 0')
        driver.command('audit 1')
        driver.events.clear()
        run_to(driver, repo, 'PokedexSelectedMon_ToggleDescriptionPage', frames=4, keys=KEY['a'])
        run_to(driver, repo, 'PokedexSelectedMon_Update', frames=10)
        run_to(driver, repo, frames=180)
        if enabled:
            driver.command('dpstop')
        driver.command('audit 0')
        events = list(driver.events)
        results.append(dict(final=driver.evidence(prefix), ui=driver.command('ui'), events=events,
            state=state_without_wall_clock(Path(str(prefix) + '.s0').read_bytes()),
            pixels=Path(str(prefix) + '.ppm').read_bytes()))
    matches = {key: results[0][key] == results[1][key] for key in results[0]}
    if not all(matches.values()):
        raise ValueError(f'Observer changed emulated execution: {label}: {matches}')
    return dict(species=label, offset=delay, **matches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sameboy-source', type=Path, default=Path('/Users/jakeadams/Documents/GitHub/SameBoy'))
    parser.add_argument('--battery', type=Path, default=ROOT / 'build/shared-menu-input/cold/input-copy.sav')
    parser.add_argument('--species', nargs='+', default=['chikorita', 'meganium', 'dusknoir', 'luxray', 'weavile'])
    parser.add_argument('--all-species', action='store_true')
    parser.add_argument('--offsets', nargs='+', type=int, default=[0, 1, 2, 4, 8, 16, 32, 64])
    parser.add_argument('--images', action='store_true')
    parser.add_argument('--no-a', action='store_true', help='No-input playback control using the same checkpoints')
    parser.add_argument('--analyze-only', action='store_true')
    parser.add_argument('--observer-controls', action='store_true',
        help='Compare tracing on/off from reused starts instead of running the A sweep')
    parser.add_argument('--variant', choices=('original', 'keep-owner', 'skip-copy', 'keep-owner-skip-copy'), default='original')
    parser.add_argument('--reuse-starts', type=Path,
        help='Run counterfactuals from these exact normal-input checkpoints, avoiding fresh-boot phase differences')
    args = parser.parse_args()
    if args.observer_controls and not args.reuse_starts:
        parser.error('--observer-controls requires --reuse-starts')
    output = validate_output(args.output, (args.battery, ROOT / 'pokecrystal.gbc'))
    output.mkdir(parents=True, exist_ok=True)
    if args.analyze_only:
        repo = Repository(ROOT, output / 'pokecrystal-desc-diagnostic.gbc', output / 'pokecrystal-desc-diagnostic.sym')
        results = json.loads((output / 'report.json').read_text())
        assets = {a.name: a for a in repo.load({r['species'] for r in results})}
        for result in results:
            label = f'{result["species"]}-{result["offset"] if result["offset"] is not None else "done"}'
            trace = [json.loads(line) for line in (output / f'{label}.jsonl').read_text().splitlines()]
            result.update(summarize_trace(trace, assets[result['species']], description_pages(repo, result['species'])))
        (output / 'analysis.json').write_text(json.dumps(results, indent=2) + '\n')
        print(json.dumps(dict(cases=len(results),
            corrupt_cases=sum(bool(r['invalid_vram_portrait_frames']) for r in results),
            corrupt_rendered_cases=sum(bool(r['invalid_rendered_portrait_frames']) for r in results),
            changed_header_cases=sum(bool(r['changed_header_frames']) for r in results),
            animation_miss_cases=sum(bool(r['animation_misses']) for r in results),
            audio_miss_cases=sum(bool(r['audio_misses']) for r in results),
            blocked_map_writes=sum(len(r['blocked_map_writes']) for r in results)), indent=2))
        return
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / f'pokecrystal.{suffix}', output / f'pokecrystal-desc-diagnostic.{suffix}')
    repo = Repository(ROOT, output / 'pokecrystal-desc-diagnostic.gbc', output / 'pokecrystal-desc-diagnostic.sym')
    isolation = isolation_rom(repo, output / 'pokecrystal-desc-diagnostic.gbc', args.variant)
    repo = Repository(ROOT, output / 'pokecrystal-desc-diagnostic.gbc', output / 'pokecrystal-desc-diagnostic.sym')
    fixture = output / 'test-only-caught.sav'
    if args.reuse_starts:
        validate_starts(args.reuse_starts, isolation, repo.hashes['sym_sha256'])
    provenance = dict(repo.hashes, fixture=caught_fixture(repo, args.battery, fixture), isolation=isolation,
                      reused_starts=str(args.reuse_starts) if args.reuse_starts else None,
                      action='uninterrupted control' if args.no_a else 'A-button description page toggle',
                      sameboy_revision=subprocess.check_output(
                          ['git', '-C', str(args.sameboy_source), 'rev-parse', 'HEAD'], text=True).strip())
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    core = compile_observer(repo, args.sameboy_source, output)
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    names = [dict(UNOWN='unown_a', PORYGON_Z='porygonz').get(n, n.lower()) for n in names]
    if args.all_species:
        args.species = names
    driver = Driver(core, output / 'pokecrystal-desc-diagnostic.gbc',
        Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'), fixture, output / 'core.log')
    results = []
    try:
        if args.observer_controls:
            for name in args.species:
                for delay in args.offsets:
                    results.append(observer_equivalence(driver, repo,
                        args.reuse_starts / f'{name}-start.s0', output, name, delay))
            (output / 'observer-controls.json').write_text(json.dumps(results, indent=2) + '\n')
            print(json.dumps(results, indent=2), flush=True)
            return
        if not args.reuse_starts:
            bootstrap(driver)
        for name in sorted(args.species, key=names.index):
            target = names.index(name)
            if args.reuse_starts:
                for kind in ('listing', 'start', 'settled'):
                    shutil.copy2(args.reuse_starts / f'{name}-{kind}.s0', output / f'{name}-{kind}.s0')
                driver.command(f'load {output / f"{name}-listing.s0"}')
            for _ in range(500):
                index = driver.command('peek')['index']
                if index == target:
                    break
                if index // 3 != target // 3:
                    # Align before descending into a partially populated last
                    # row; an empty column can otherwise wrap past the target.
                    if target // 3 == (len(names) - 1) // 3 and index % 3 > target % 3:
                        move(driver, 'left')
                    else:
                        move(driver, 'down' if target > index else 'up')
                else:
                    move(driver, 'right' if target > index else 'left')
                driver.run(('end_loop',))
                driver.run(('end_loop',))
            else:
                raise RuntimeError(f'Listing navigation did not reach {name}')
            listing = output / f'{name}-listing.s0'
            start = output / f'{name}-start.s0'
            settled = output / f'{name}-settled.s0'
            if not args.reuse_starts:
                driver.command(f'save {listing}')
                driver.run(('accept',), key='a')
                state = driver.run(('selected', 'animation_miss', 'audio_miss'))
                if state['hit'] != 'selected':
                    raise RuntimeError(f'Selection failed: {state}')
                driver.run(('selected',))
                driver.command(f'save {start}')
                settle(driver)
                driver.command(f'save {settled}')
            for delay in (*args.offsets, None):
                driver.command(f'load {settled if delay is None else start}')
                if delay:
                    run_to(driver, repo, frames=delay)
                label = f'{name}-{delay if delay is not None else "done"}'
                driver.command(f'dptrace {output / label} {int(args.images)}')
                driver.command('audit 1')
                driver.events.clear()
                if not args.no_a:
                    run_to(driver, repo, 'PokedexSelectedMon_ToggleDescriptionPage', frames=4, keys=KEY['a'])
                    run_to(driver, repo, 'PokedexSelectedMon_Update', frames=10)
                run_to(driver, repo, frames=180)
                driver.command('dpstop')
                driver.command('audit 0')
                events = list(driver.events)
                (output / f'{label}-audit.json').write_text(json.dumps(events, indent=2) + '\n')
                trace = [json.loads(line) for line in (output / f'{label}.jsonl').read_text().splitlines()]
                phases = [e for e in trace if e['event'] == 'phase']
                entry = next((e for e in phases if e['phase'] == 'toggle'), None)
                done = next((e for e in phases if e['phase'] == 'toggle_done'), None)
                result = dict(species=name, offset=delay,
                    toggle_cycles=done['t'] - entry['t'] if entry and done else None,
                    animation_misses=[e for e in events if e['event'] == 'animation_miss'],
                    audio_misses=[e for e in events if e['event'] == 'audio_miss'],
                    blocked_map_writes=[e for e in trace if e['event'] == 'write' and
                        0x9800 <= e['address'] < 0x9a40 and e['vram_blocked']],
                    final=driver.command('peek'))
                result.update(summarize_trace(trace, next(a for a in repo.load({name})), description_pages(repo, name)))
                results.append(result)
                print(json.dumps({k: v for k, v in result.items() if k not in (
                    'final', 'blocked_map_writes', 'physical_pages')}), flush=True)
            (output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
            driver.command(f'load {listing}')
        (output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    finally:
        driver.close()


if __name__ == '__main__':
    main()
