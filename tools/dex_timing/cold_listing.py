"""Real-input cold Listing regression using the local SameBoy core.

Unlike relocated playback replays, this boots an isolated battery copy and
creates every starting state through normal controls. The ROM, cartridge RAM,
animation owners, and producer counters are never patched by the driver.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import subprocess

from .assets import Repository, offset, sha256
from .recovery_experiment import initial_asset_maps

ROOT = Path(__file__).resolve().parents[2]
FRAME = 70224
KEY = dict(right=1, left=2, up=4, down=8, a=16, b=32, start=128)
POINTS = {
    'title': 'TitleScreenMain', 'continue': 'MainMenu_Continue',
    'new_game': 'MainMenu_NewGame', 'overworld': 'HandleMapTimeAndJoypad',
    'start_menu': 'StartMenu.loop', 'listing': 'Pokedex_UpdateMainScreen',
    'accept': 'Pokedex_UpdateMainScreen.a', 'selected': 'PokedexSelectedMon_Update',
    'end_loop': 'Pokedex_EndOwnerLoop', 'leave': 'PokedexSelectedMon_Leave',
    'animation_miss': 'Pokedex_CountAnimationUnderflow',
    'audio_miss': '@audio_empty',
}
FIELDS = '''wDexListingScrollOffset wDexListingCursor wDexListingEnd wCurDexMode
    wMenuCursorPosition wJumptableIndex wPokedexSelectedState wPokedexAnimOwner
    wPokedexAnimDictionaryDestination wPokedexAnimUploadOffset
    wPokedexAnimDebugDictionaryServices wPokedexAnimDebugUploadServices
    wPokedexAnimPlaybackState hSampledCryTimer hSampledCryBlocks hVBlankCounter
    hJoyDown wPokedexAnimDebug wPokedexAnimDebugEnd wPokedexAnimStageFrameID
    wPokedexAnimStageSlot wPokedexAnimDebugEventReads
    wChannel5Flags1 wChannel6Flags1 wChannel7Flags1 wChannel8Flags1'''.split()


def build_core(repo, source, output):
    symbols = repo.symbols
    pairs = dict(PUBLISH=symbols['Pokedex_VBlankAnimationFrontpicMap.display_recorded'],
                 REVEAL=symbols['PokedexSelectedMon_Enter.revealed'],
                 ANIMATION_MISS=symbols['Pokedex_CountAnimationUnderflow'],
                 AUDIO_STOP=symbols['StopSampledCryAsync_NoInterruptControl'])
    # Derive the cache-empty branch from the linked labels and verify its bytes.
    bank, decoded = symbols['SampledCry_AsyncTimerTick.has_decoded_block']
    empty = decoded - 6
    stop = pairs['AUDIO_STOP'][1]
    if repo.rom[empty:decoded] != bytes((0xf1, 0xe0, 0x70, 0xc3, stop & 255, stop >> 8)):
        raise ValueError('Sampled-cry empty branch changed; update the host checkpoint')
    pairs['AUDIO_EMPTY'] = bank, empty
    lines = [f'#define S_{name} 0x{symbols[name][1]:04x}' for name in FIELDS]
    for name, (bank, pc) in pairs.items():
        lines += [f'#define B_{name} {bank}', f'#define P_{name} 0x{pc:04x}']
    lines += ['static const struct { unsigned bank, pc; } points[] = {']
    for name in POINTS.values():
        bank, pc = pairs['AUDIO_EMPTY'] if name == '@audio_empty' else symbols[name]
        lines.append(f'{{{bank}, 0x{pc:04x}}},')
    lines += ['};']
    header = output / 'linked-symbols.h'
    header.write_text('\n'.join(lines) + '\n')
    core = output / 'cold-listing-core'
    files = ('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
             'sm83_cpu timing workboy').split()
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(source), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="dex-cold-listing"',
        '-include', str(header), str(ROOT / 'tools/dex_timing/probes/cold_listing.c'),
        *(str(source / 'Core' / f'{f}.c') for f in files), '-o', str(core)], check=True)
    return core


class Driver:
    def __init__(self, core, rom, boot, battery, log):
        self.log = open(log, 'w')
        self.process = subprocess.Popen([str(core), str(rom), str(boot), str(battery)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, text=True, bufsize=1)
        self.events = []

    def command(self, text):
        self.process.stdin.write(text + '\n')
        self.process.stdin.flush()
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError(f'Headless core exited: {self.process.poll()}')
            event = json.loads(line)
            if event['event'] in ('stop', 'ok'):
                if event.get('error'):
                    raise RuntimeError(f'Headless command failed: {text}: {event}')
                return event
            self.events.append(event)

    def run(self, points=(), frames=180, key=None):
        mask = sum(1 << list(POINTS).index(p) for p in points)
        result = self.command(f'run {mask} {int(frames * FRAME)} {KEY.get(key, 0)}')
        result['hit'] = list(POINTS)[result['hit']] if result['hit'] >= 0 else None
        return result

    def close(self):
        if self.process.poll() is None:
            try:
                self.process.stdin.write('quit\n')
                self.process.stdin.flush()
                self.process.wait(timeout=15)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()
        self.log.close()

    def evidence(self, prefix):
        self.command(f'save {prefix}.s0')
        self.command(f'image {prefix}.ppm')
        return self.command('peek')


def bootstrap(driver):
    """Continue the copy, open the start menu, and select its first (Dex) item."""
    stages = []
    for _ in range(180):
        state = driver.run(('continue', 'new_game', 'overworld'), 20, 'a')
        stages.append(state)
        if state['hit'] == 'new_game':
            raise RuntimeError('Continue was unavailable; refusing to start a new game')
        if state['hit'] == 'overworld':
            break
        driver.run(frames=10)
    else:
        raise RuntimeError('Could not reach the overworld from the copied battery save')
    state = driver.run(('start_menu',), 180, 'start')
    if state['hit'] != 'start_menu':
        raise RuntimeError('Could not open the start menu')
    for _ in range(12):
        state = driver.run(('start_menu',), 60)
        if state['menu'] == 1:
            break
        driver.run(frames=2, key='up')
    else:
        raise RuntimeError('Could not select the Dex menu item')
    state = driver.run(('listing',), 600, 'a')
    if state['hit'] != 'listing' or state['mode'] != 0:
        raise RuntimeError(f'Expected New Dex Listing, got {state}')
    driver.run(('end_loop',), key=None)
    driver.run(('end_loop',), key=None)
    return stages, driver.command('peek')


def move(driver, direction, expected=None):
    previous = driver.command('peek')['index']
    for _ in range(40):
        state = driver.run(('end_loop',), frames=180, key=direction)
        if state['hit'] != 'end_loop':
            raise RuntimeError('Listing navigation timed out')
        if state['index'] != previous:
            if expected is not None and state['index'] != expected:
                raise RuntimeError(f'Navigation reached {state["index"]}, expected {expected}')
            return state
    raise RuntimeError(f'Listing did not move {direction} from {previous}')


def prepare_states(driver, output, count):
    # Get to the top left without editing the saved cursor, including row wraps.
    state = driver.command('peek')
    for _ in range(150):
        if state['index'] < 3:
            break
        state = move(driver, 'up')
        driver.run(('end_loop',), key=None)
        driver.run(('end_loop',), key=None)
    else:
        raise RuntimeError('Could not navigate to the first Listing row')
    while state['index']:
        state = move(driver, 'left')
        driver.run(('end_loop',), key=None)
        driver.run(('end_loop',), key=None)
    route = []
    for row in range((count + 2) // 3):
        columns = list(range(min(3, count - row * 3)))
        if row & 1:
            columns.reverse()
        route += [row * 3 + col for col in columns]
    for number, target in enumerate(route):
        current = driver.command('peek')['index']
        if current != target:
            direction = 'down' if target // 3 != current // 3 else ('right' if target > current else 'left')
            move(driver, direction, target)
        driver.run(('end_loop',), key=None)
        state = driver.run(('end_loop',), key=None)
        if state['index'] != target or state['joy']:
            raise RuntimeError('Starting Listing state has pending directional input')
        driver.command(f'save {output / f"listing-{target:03}.s0"}')
        if number % 30 == 0:
            print(f'Listing checkpoints: {number + 1}/{count}', flush=True)


def predecessor(index):
    if not index:
        return 1, 'left'
    if index % 3:
        return index - 1, 'right'
    return index - 3, 'down'


def expected_picture(asset, frame):
    base = [bytes(16) for _ in range(49)]
    width, col = asset.width, int(asset.width != 7)
    for x in range(width):
        for y in range(width):
            source = x * width + y
            base[(x + col) * 7 + y + 7 - width] = asset.dictionary[source * 16:(source + 1) * 16]
    result = [base[x * 7 + y] for y in range(7) for x in range(7)]
    for pos, source in asset.plans[frame].pairs:
        result[pos & 127] = base[source] if pos & 128 else asset.dictionary[source * 16:(source + 1) * 16]
    return b''.join(result)


def audit(asset, accepted, events, final):
    issues = []
    if (accepted['loaded'] != asset.width ** 2 or accepted['dictionary_services']
            or accepted['upload_services'] or accepted.get('upload', 0)):
        issues.append('not_cold')
    if accepted.get('double_speed') or final.get('double_speed'):
        issues.append('unexpected_double_speed')
    reveals = [e for e in events if e['event'] == 'reveal']
    if len(reveals) != 1:
        issues.append('static_reveal_count')
    elif (bytes.fromhex(reveals[0]['map']) != b''.join(initial_asset_maps(asset, 0, 0))
            or bytes.fromhex(reveals[0]['picture']) != expected_picture(asset, 0)):
        issues.append('static_reveal_tiles')
    if any(e['event'] == 'animation_miss' for e in events):
        issues.append('animation_miss')
    if any(e['event'] == 'audio_miss' for e in events):
        issues.append('audio_miss')
    stops = [e for e in events if e['event'] == 'audio_stop']
    if asset.sample_blocks and (not stops or any(e['remaining'] for e in stops)):
        issues.append('sampled_cry_incomplete')
    pubs = [e for e in events if e['event'] == 'publish']
    expected = [(e.frame, e.duration) for e in asset.events] + [(0, 0)]
    if len(pubs) != len(expected):
        issues.append('publication_count')
    elapsed, actual_elapsed, last_tick = 0, 0, pubs[0]['tick'] if pubs else 0
    for i, (pub, (frame, duration)) in enumerate(zip(pubs, expected)):
        actual_elapsed += (pub['tick'] - last_tick) & 255
        last_tick = pub['tick']
        if (pub['frame'], pub['ordinal'], actual_elapsed) != (frame, i + 1, elapsed):
            issues.append(f'timeline_event_{i + 1}')
        # The byte-sized game clock is not enough: a 256-frame stall could
        # alias it. Independent core cycles must identify the same interval.
        if (pub['t'] - pubs[0]['t'] + FRAME // 2) // FRAME != elapsed:
            issues.append(f'hardware_interval_event_{i + 1}')
        if bytes.fromhex(pub['map']) != b''.join(initial_asset_maps(asset, frame, pub['slot'])):
            issues.append(f'tilemap_event_{i + 1}')
        if bytes.fromhex(pub['picture']) != expected_picture(asset, frame):
            issues.append(f'tile_pixels_event_{i + 1}')
        if not 144 <= pub['ly'] <= 153:
            issues.append(f'publication_outside_vblank_{i + 1}')
        elapsed += duration
    if final['playback'] != 3 or final['audio'] or final['sfx']:
        issues.append('playback_not_finished')
    return dict(issues=issues, cold=not ('not_cold' in issues), publications=len(pubs),
        expected_intervals=sum(e.duration for e in asset.events), actual_intervals=actual_elapsed,
        static_reveal_frames=(reveals[0]['t'] - accepted['t']) / FRAME if reveals else None,
        first_publication_frames=(pubs[0]['t'] - accepted['t']) / FRAME if pubs else None,
        sampled_blocks=asset.sample_blocks)


def run_case(job):
    config, index, asset = job
    output = Path(config['output'])
    prefix = output / f'{index:03}-{asset.name}'
    driver = Driver(config['core'], config['rom'], config['boot'], config['battery'], f'{prefix}.log')
    row = dict(index=index, species=asset.name, status='error')
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {output / "listing-states" / f"listing-{prior:03}.s0"}')
        moved = move(driver, direction, index)
        driver.command('audit 1')
        accepted = driver.run(('accept',), frames=120, key='a')
        if accepted['hit'] != 'accept' or accepted['index'] != index:
            raise RuntimeError('A was not accepted on the intended new selection')
        # No further input until both animation and cry have fully ended.
        first = None
        for _ in range(2400):
            final = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=120)
            if final['hit'] in ('animation_miss', 'audio_miss') and first is None:
                first = driver.evidence(f'{prefix}-first-miss')
            if final['hit'] is None:
                raise RuntimeError('Selected-page entry/playback stopped returning to its input loop')
            if final['playback'] == 3 and not final['audio'] and not final['sfx']:
                break
        else:
            raise RuntimeError('Animation or cry did not finish within the bounded test')
        result = audit(asset, accepted, driver.events, final)
        row.update(result, status='fail' if result['issues'] else 'pass',
                   moved=moved, accepted=accepted, final=final, first_miss=first)
        if result['issues']:
            driver.evidence(f'{prefix}-failure')
        # Exit behavior is a separate result, never used to seed the next case.
        driver.command('audit 0')
        returned = driver.run(('listing',), frames=600, key='b')
        row['return_to_listing'] = 'pass' if returned['hit'] == 'listing' and returned['index'] == index else 'fail'
        row['return_state'] = returned
        if row['return_to_listing'] != 'pass':
            driver.evidence(f'{prefix}-return-failure')
    except (RuntimeError, ValueError) as error:
        row['error'] = str(error)
        try:
            row['failure_state'] = driver.evidence(f'{prefix}-error')
        except (RuntimeError, BrokenPipeError) as capture_error:
            row['capture_error'] = str(capture_error)
    finally:
        row['events'] = driver.events
        driver.close()
    prefix.with_suffix('.json').write_text(json.dumps(row, indent=2) + '\n')
    return {k: v for k, v in row.items() if k not in ('events', 'moved', 'accepted', 'final', 'first_miss', 'return_state')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--rom', type=Path, help='Defaults to ROOT/pokecrystal.gbc; must match ROOT/pokecrystal.sym and assets')
    parser.add_argument('--sameboy-source', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--boot', type=Path, default=Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', nargs='+', help='Optional smoke-test subset; default is every New Dex entry')
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--reuse-listing-states', action='store_true', help='Requires matching ROM/save/source provenance')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    args.rom = args.rom or args.root / 'pokecrystal.gbc'
    repo = Repository(args.root, args.rom, args.root / 'pokecrystal.sym')
    assets = {a.name: a for a in repo.load()}
    names = re.findall(r'^\s*dw (\w+)\s*$', (args.root / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in names]
    if len(set(names)) != len(names) or any(n not in assets for n in names):
        raise ValueError('New Dex order does not map one-to-one to linked animation assets')
    order_at = offset(repo.symbols['NewPokedexOrder'])
    pics_at = offset(repo.symbols['PokemonPicPointers'])
    for i, name in enumerate(names):
        species = int.from_bytes(repo.rom[order_at + 2*i:order_at + 2*i + 2], 'little')
        pointer = offset(repo.symbols['UnownPicPointers']) if name == 'unown_a' else pics_at + 6*species
        bank, address = repo.symbols[assets[name].labels['front']]
        if repo.rom[pointer:pointer + 3] != bytes((bank, address & 255, address >> 8)):
            raise ValueError(f'Source New Dex order does not match linked portrait pointer: {name}')
    original_save = args.battery.read_bytes()
    provenance = {**repo.hashes, 'battery_sha256': sha256(original_save),
        'boot_sha256': sha256(args.boot.read_bytes()), 'species_count': len(names),
        'sameboy_commit': subprocess.check_output(['git', '-C', str(args.sameboy_source), 'rev-parse', 'HEAD'], text=True).strip(),
        'sameboy_core_sha256': {p.name: sha256(p.read_bytes()) for p in sorted((args.sameboy_source / 'Core').glob('*.[ch]'))},
        'driver_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in
            (Path(__file__).resolve(), ROOT / 'tools/dex_timing/probes/cold_listing.c',
             ROOT / 'tools/dex_timing/assets.py', ROOT / 'tools/dex_timing/recovery_experiment.py')},
        'new_dex_order_sha256': sha256((args.root / 'data/pokemon/dex_order_new.asm').read_bytes())}
    provenance_file = args.output / 'provenance.json'
    if args.reuse_listing_states and json.loads(provenance_file.read_text()) != provenance:
        raise ValueError('Listing states belong to different inputs or host code; regenerate them')
    provenance_file.write_text(json.dumps(provenance, indent=2) + '\n')
    battery = args.output / 'input-copy.sav'
    battery.write_bytes(original_save)
    rom = args.output / 'input-copy.gbc'
    rom.write_bytes(repo.rom)
    core = build_core(repo, args.sameboy_source, args.output)
    states = args.output / 'listing-states'
    states.mkdir(exist_ok=True)
    if not args.reuse_listing_states:
        driver = Driver(core, rom, args.boot, battery, args.output / 'bootstrap.log')
        try:
            boot, state = bootstrap(driver)
            (args.output / 'bootstrap.json').write_text(json.dumps(boot + [state], indent=2) + '\n')
            if state['end'] != len(names):
                raise ValueError(f'Expected all {len(names)} entries accessible, got {state["end"]}')
            prepare_states(driver, states, len(names))
        except Exception:
            driver.evidence(args.output / 'bootstrap-failure')
            raise
        finally:
            driver.close()
    config = dict(output=str(args.output), core=str(core), rom=str(rom), boot=str(args.boot), battery=str(battery))
    selected = set(args.species or names)
    if selected - set(names):
        raise ValueError(f'Unknown test species: {selected - set(names)}')
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(run_case, [(config, i, assets[n]) for i, n in enumerate(names) if n in selected]):
            rows.append(row)
            print(json.dumps(row), flush=True)
            (args.output / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
    unchanged = args.battery.read_bytes() == original_save and args.rom.read_bytes() == repo.rom
    totals = dict(tested=len(rows), passed=sum(r['status'] == 'pass' for r in rows),
        returns_passed=sum(r.get('return_to_listing') == 'pass' for r in rows), originals_unchanged=unchanged)
    (args.output / 'totals.json').write_text(json.dumps(totals, indent=2) + '\n')
    print(json.dumps(totals))
    return int(not unchanged or any(r['status'] != 'pass' or r.get('return_to_listing') != 'pass' for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
