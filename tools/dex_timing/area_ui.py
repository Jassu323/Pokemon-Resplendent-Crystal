"""Read-only normal-input Area integration checks in isolated SameBoy.

Cartridge graphics/encounters are compared to independent linked-data oracles.
Only private battery copies are edited; test cores never patch live game RAM.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re

from .assets import Repository, offset, decompress, sha256
from .cold_listing import ROOT, Driver, bootstrap, prepare_states, move, predecessor, audit, expected_picture
from .description_ui import audit as description_audit, settle, settle_description_text
from .info_ui import BOOT, fixture, press, ready as info_ready, info_audit, type_audit
from .moves_ui import ready as moves_ready, content_audit
from .description_paging import description_pages
from pokedex_info_assets import Compiler
from .listing_restoration import compile_observer, listing_snapshot, summarize, restoration_failures
from .shared_menu_fixtures import make_fixture

T = 70224
ALIASES = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}


@lru_cache(maxsize=1)
def info_data():
    compiler = Compiler()
    return compiler, compiler.compile(), json.loads((ROOT / 'build/dex-moves-assets/manifest.json').read_text())


@lru_cache(maxsize=4)
def repository(rom, sym):
    return Repository(ROOT, Path(rom), Path(sym))


@lru_cache(maxsize=512)
def asset(rom, sym, name):
    return repository(rom, sym).load([name])[0]


def shell_audit(ui):
    issues = []
    actual, attrs, staged, staged_attrs = (bytes.fromhex(ui[k]) for k in ('map', 'attrs', 'staged_map', 'staged_attrs'))
    for row in (0, 16, 17):
        for col in range(21):
            at, target = row * 21 + col, row * 32 + col
            # The footer cursor is redrawn by the subsequent input poll.
            arrow = (row == 17 and col in (1, 6, 11, 15)
                     and actual[at] in (0x7f, 0xed) and staged[target] in (0x7f, 0xed))
            if (not arrow and actual[at] != staged[target]) or attrs[at] != staged_attrs[target]:
                issues.append(f'shell_restore_{row}_{col}')
    if (ui['scx'], ui['scy'], ui['wx'], ui['wy']) != (5, 0, 167, 0):
        issues.append('selected_viewport')
    return issues


def lower_audit(driver, repo, name, view, page):
    if view == 0:
        if driver.command('ui')['caught']:
            settle_description_text(driver, description_pages(repo, name)[page])
        return description_audit(repo, driver.command('ui')) + type_audit(repo, name, driver.command('ui'))
    compiler, data, manifest = info_data()
    ui = driver.command('ui')
    if view == 1:
        return info_audit(compiler, data, name, page, ui, repo) + type_audit(repo, name, ui)
    return content_audit(repo, name, page, ui, manifest)


def static_audit(driver, repo, name, config):
    issues, phases = [], set()
    expected = expected_picture(asset(config['rom'], config['sym'], name), 0).hex()
    first = driver.command('peek')
    for _ in range(30):
        stopped = driver.run(('animation_miss', 'audio_miss'), frames=4)
        if stopped['hit']:
            raise RuntimeError(f'Playback miss after static return: {stopped}')
        ui, state = driver.command('ui'), driver.command('peek')
        if ui['picture'] != expected:
            issues.append('static_base_portrait')
        if state['playback'] or state['animation_flags'] or state['audio'] or state['sfx']:
            issues.append('static_owner_playback_active')
        if (state['dictionary_services'], state['upload_services']) != (first['dictionary_services'], first['upload_services']):
            issues.append('static_owner_producer_work')
        if ui['info_minis'] and ui['view'] == 1 and ui['info_page']:
            phases.add(bytes.fromhex(ui['oam'])[34])
    if phases and len(phases) != 2:
        issues.append('evolution_minis_not_animated')
    if any(e['event'] == 'publish' for e in driver.events):
        issues.append('static_frontpic_publication')
    return sorted(set(issues)), sorted(phases)


def location(repo, group, number):
    bank, pc = repo.symbols['MapGroupPointers']
    at = offset((bank, pc + (group - 1) * 2))
    base = int.from_bytes(repo.rom[at:at + 2], 'little')
    return repo.rom[offset((bank, base + (number - 1) * 9 + 5))]


def nests(repo, species_index, region):
    result = []
    for kind, slots in (('Grass', 21), ('Water', 3)):
        at = offset(repo.symbols[('Kanto' if region else 'Johto') + kind + 'WildMons'])
        while repo.rom[at] != 255:
            group, number = repo.rom[at:at + 2]
            first = at + (5 if kind == 'Grass' else 3)
            found = any(int.from_bytes(repo.rom[first + 5 * i + 1:first + 5 * i + 3], 'little')
                        == species_index for i in range(slots))
            if found:
                landmark = location(repo, group, number)
                if landmark not in result:
                    result.append(landmark)
            at = first + slots * 5
    return result


def marker_bytes(repo, locations):
    at = offset(repo.symbols['Landmarks'])
    return b''.join(bytes((repo.rom[at + n * 4 + 1] - 4,
                           repo.rom[at + n * 4] - 4, 127, 0)) for n in locations)


def map_audit(repo, index, area, ui):
    issues = []
    species_index = int.from_bytes(repo.rom[offset(repo.symbols['NewPokedexOrder']) + index * 2:
                                           offset(repo.symbols['NewPokedexOrder']) + index * 2 + 2], 'little')
    expected = nests(repo, species_index, area['region'])
    # Vanilla adds the two tracked Johto roamers after static encounter data.
    if not area['region']:
        for species_id, group, number in area['roam']:
            if species_id and species_id == area['named'] and group and number:
                landmark = location(repo, group, number)
                if landmark not in expected:
                    expected.append(landmark)
    actual = bytes.fromhex(area['nests'])
    count = len(expected) * 4
    if actual[:count] != marker_bytes(repo, expected) or any(actual[count:]):
        issues.append('nest_locations')
    if len(expected) > 40:
        issues.append('nest_oam_capacity')
    for region in range(2):
        tiles = repo.rom[offset(repo.symbols['KantoMap' if region else 'JohtoMap']):]
        loaded = bytes.fromhex(area[f'map{region}'])
        at = offset(repo.symbols['PokemonNames']) + (species_index - 1) * 10
        name = repo.rom[at:at + 10].split(b'\x50')[0]
        at = offset(repo.symbols['Pokedex_GetArea.String_SNest'])
        suffix = repo.rom[at:at + 16].split(b'\x50')[0]
        heading = bytearray(bytes((127,)) * 20)
        heading[2:2 + len(name + suffix)] = name + suffix
        if loaded[:20] != heading or loaded[32:52] != bytes((6,)) + bytes((7,)) * 18 + bytes((23,)):
            issues.append(f'map_{region}_heading')
        for y in range(2, 18):
            if loaded[y * 32:y * 32 + 20] != tiles[y * 20:y * 20 + 20]:
                issues.append(f'map_{region}_{y}')
        attrs = bytes.fromhex(area[f'attrs{region}'])
        at = offset(repo.symbols['TownMapPals.PalMap'])
        for y in range(18):
            for x in range(20):
                tile = loaded[y * 32 + x]
                color = ((repo.rom[at + tile // 2] >> ((tile & 1) * 4)) & 7) if tile < 96 else 0
                if attrs[y * 32 + x] != color:
                    issues.append(f'map_{region}_attr_{y}_{x}')
    start = offset(repo.symbols['TownMapGFX'])
    expected_tiles = decompress(repo.rom, start, 768).output
    if bytes.fromhex(area['town_tiles']) != expected_tiles:
        issues.append('town_graphics')
    start = offset(repo.symbols['PokedexNestIconGFX'])
    if bytes.fromhex(area['icons'])[-16:] != repo.rom[start:start + 16]:
        issues.append('nest_graphics')
    label = 'FastShipGFX' if area['player'] == 95 else ('KrisSpriteGFX' if area['gender'] & 1 else 'ChrisSpriteGFX')
    start = offset(repo.symbols[label])
    if bytes.fromhex(area['icons'])[:64] != repo.rom[start:start + 64]:
        issues.append('player_graphics')
    start = offset(repo.symbols['FemalePokegearPals' if area['gender'] & 1 else 'MalePokegearPals'])
    if bytes.fromhex(ui['palettes'])[:48] != repo.rom[start:start + 48]:
        issues.append('town_palettes')
    if area['request'] or area['bg_mode'] or area['pal_update'] or area['oam_hold']:
        issues.append('unfinished_area_request')
    if area['vblank'] != 0:
        issues.append('area_vblank_owner')
    if ui['scx'] or ui['scy'] or ui['wx'] != 7 or ui['wy'] != (0 if area['region'] else 144):
        issues.append('area_viewport')
    return issues, expected


def player_audit(driver, repo):
    reach(driver, repo, 'Pokedex_GetArea.HideNestsShowPlayer', 64)
    reach(driver, repo, 'Pokedex_GetArea.next', 64)
    player, ui = driver.command('area'), driver.command('ui')
    expected = bytearray(160)
    player_region = int(player['player'] >= 47 and player['player'] != 95)
    if player_region == player['region']:
        at = offset(repo.symbols['Landmarks']) + player['player'] * 4
        x, y = repo.rom[at:at + 2]
        palette = player['gender'] & 1
        expected[:16] = bytes((y - 8, x - 8, 120, palette, y - 8, x, 121, palette,
                               y, x - 8, 122, palette, y, x, 123, palette))
    issues = []
    if bytes.fromhex(player['shadow_oam']) != expected:
        issues.append('player_shadow_oam')
    at = offset(repo.symbols['MapObjectPals']) + (player['time'] & 3) * 64
    if bytes.fromhex(ui['obj_palettes'])[:16] != repo.rom[at:at + 16]:
        issues.append('player_palettes')
    driver.run(frames=2, key='select')
    if bytes.fromhex(driver.command('ui')['oam']) != expected:
        issues.append('player_hardware_oam')
    return issues


def reach(driver, repo, label, key=0, frames=600):
    bank, pc = repo.symbols[label]
    result = driver.command(f'restorerun {bank} {pc} {frames * T} {key}')
    if result['hit'] < 0:
        raise RuntimeError(f'{label} timed out: {result}')
    return result


def run_case(job):
    config, name, view, phase, exit_key, page = job
    repo = repository(config['rom'], config['sym'])
    index = config['names'].index(name)
    label = f'{name}-{view}-p{page}-{phase}-{exit_key}'
    out = Path(config['output'])
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], out / (label + '.log'))
    result = dict(species=name, view=view, page=page, phase=phase, exit=exit_key, issues=[])
    try:
        prior, direction = predecessor(index)
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        reference = listing_snapshot(driver, out / (label + '-listing-reference')) if config.get('direct_listing') else None
        driver.command('audit 1')
        initial = driver.run(('accept',), key='a')
        driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        if phase == 'settled':
            settle(driver)
        else:
            driver.run(('animation_miss', 'audio_miss'), frames=int(phase))
        if view in ('info', 'evo'):
            press(driver, 'right')
            press(driver, 'a')
            if phase == 'settled':
                info_ready(driver, 0)
            if view == 'evo':
                info_ready(driver, 0)
                press(driver, 'a')
                info_ready(driver, None)
        elif view == 'moves':
            press(driver, 'right')
            press(driver, 'right')
            press(driver, 'a')
            if phase == 'settled':
                moves_ready(driver, 0)
        elif view == 'page2':
            press(driver, 'a')
            if phase == 'settled':
                settle_description_text(driver, description_pages(repo, name)[1])
        current_view = driver.command('ui')['view']
        field = ('page', 'info_page', 'moves_page')[current_view]
        first_page = int(view in ('page2', 'evo'))
        for _ in range(page - first_page):
            if current_view == 1:
                info_ready(driver, None)
            elif current_view == 2:
                moves_ready(driver)
            else:
                settle_description_text(driver, description_pages(repo, name)[driver.command('ui')['page']])
            press(driver, 'a')
        if phase == 'settled':
            if current_view == 1:
                info_ready(driver, page)
            elif current_view == 2:
                moves_ready(driver, page)
            elif driver.command('ui')['caught']:
                settle_description_text(driver, description_pages(repo, name)[page])
        # Move to Area without waiting for a pending lower-panel job to finish.
        for _ in range(3 - driver.command('ui')['footer_cursor']):
            press(driver, 'right')
        before = driver.command('area')
        prior_ui = driver.command('ui')
        result['prior_ui'] = {k: prior_ui[k] for k in ('view', 'page', 'info_page', 'moves_page',
                                                       'description_state', 'info_state', 'moves_state')}
        if config.get('images'):
            driver.command(f'restoretrace {out / label} 1')
        driver.events.clear()
        pressed = driver.command('peek')['t']
        accepted = driver.run(('footer_accept',), key='a', frames=600)
        ready = reach(driver, repo, 'Pokedex_GetArea.loop')
        result.update(pressed_t=pressed, accepted_t=accepted['t'], ready_t=ready['t'],
                      entry_frames=(ready['t'] - accepted['t']) / T)
        driver.run(frames=2)
        area, ui = driver.command('area'), driver.command('ui')
        result['issues'], result['nests'] = map_audit(repo, index, area, ui)
        result['context'] = {k: area[k] for k in ('player', 'gender', 'status', 'time')}
        state = driver.command('peek')
        if state['audio'] or state['sfx']:
            result['issues'].append('area_outgoing_audio')
        if config.get('images') or name in ('dusknoir', 'rattata', 'magikarp', 'mewtwo'):
            driver.command(f'image {out / (label + "-johto.ppm")}')
        # Test the vanilla right-lock, or both region directions when unlocked.
        press(driver, 'right')
        reach(driver, repo, 'Pokedex_GetArea.loop')
        driver.run(frames=1)
        area, ui = driver.command('area'), driver.command('ui')
        unlocked = bool(area['status'] & 64)
        if area['region'] != int(unlocked):
            result['issues'].append('kanto_unlock')
        issues, result['kanto_nests'] = map_audit(repo, index, area, ui)
        result['issues'] += issues
        if config.get('images'):
            driver.command(f'image {out / (label + "-kanto.ppm")}')
        result['issues'] += ['kanto:' + s for s in player_audit(driver, repo)]
        if config.get('images'):
            driver.command(f'image {out / (label + "-kanto-player.ppm")}')
        press(driver, 'left')
        reach(driver, repo, 'Pokedex_GetArea.loop')
        driver.run(frames=1)
        if driver.command('area')['region']:
            result['issues'].append('johto_return')
        # Select must place the player only in the displayed region.
        result['issues'] += ['johto:' + s for s in player_audit(driver, repo)]
        if config.get('images'):
            driver.command(f'image {out / (label + "-johto-player.ppm")}')
        driver.run(frames=2)
        # Several blink boundaries must copy the prepared nests, not old types.
        observed = set()
        expected_oam = marker_bytes(repo, result['nests']).ljust(160, b'\0')
        for _ in range(40):
            driver.run(frames=1)
            oam = bytes.fromhex(driver.command('ui')['oam'])
            if oam == bytes(160):
                observed.add('off')
            elif oam == expected_oam:
                observed.add('on')
        if result['nests'] and observed != {'off', 'on'}:
            result['issues'].append('nest_blink')
        result['blink'] = sorted(observed)
        driver.events.clear()
        pressed = driver.command('peek')['t']
        # Release during restoration: held B must not leak into Listing.
        handoff = reach(driver, repo, 'PokedexSelectedMon_Area.map_returned',
                        16 if exit_key == 'a' else 32)
        after = driver.command('area')
        if after['player'] != before['player'] or after['region'] != before['region']:
            result['issues'].append('map_state_not_restored')
        restored = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
        result.update(return_frames=(restored['t'] - pressed) / T, restored=restored)
        if restored['hit'] != 'selected' or restored['state'] != 1:
            raise RuntimeError('Selected owner was not restored')
        driver.run(('animation_miss', 'audio_miss'), frames=1)
        ui = driver.command('ui')
        result['issues'] += shell_audit(ui)
        static = 'PokedexSelectedMon_Area.restored' in repo.symbols
        if static:
            if ui['view'] != current_view or ui[field] != page or ui['footer_cursor'] != current_view:
                result['issues'].append('return_tab_page_cursor')
            result['issues'] += ['return:' + s for s in lower_audit(driver, repo, name, current_view, page)]
            issues, result['mini_phases'] = static_audit(driver, repo, name, config)
            result['issues'] += issues
            result['playback'] = dict(mode='static', final=driver.command('peek'))
        else:
            result['issues'] += ['return:' + s for s in description_audit(repo, ui)]
            if ui['view'] or ui['page'] != prior_ui['page'] or ui['footer_cursor']:
                result['issues'].append('return_description_state')
            final = settle(driver)
            playback = audit(repo.load([name])[0], accepted, driver.events, final, cold=False)
            result['playback'] = playback
            result['issues'] += ['playback:' + s for s in playback['issues']]
        if config.get('images'):
            driver.command(f'image {out / (label + "-returned.ppm")}')
            driver.command('restorestop')
        if static and config.get('repeat_area'):
            for _ in range(3 - current_view):
                press(driver, 'right')
            driver.run(('footer_accept', 'animation_miss', 'audio_miss'), frames=600, key='a')
            reach(driver, repo, 'Pokedex_GetArea.loop')
            driver.run(frames=2)
            reach(driver, repo, 'PokedexSelectedMon_Area.map_returned', 32)
            again = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            driver.run(frames=1)
            ui = driver.command('ui')
            result['issues'] += ['repeat_area:' + s for s in shell_audit(ui)]
            if again['hit'] != 'selected' or ui['view'] != current_view or ui[field] != page or ui['footer_cursor'] != current_view:
                result['issues'].append('repeat_area_state')
            result['issues'] += ['repeat_area:' + s for s in lower_audit(driver, repo, name, current_view, page)]
        # Direct Listing return also exercises Info's borrowed-panel transaction.
        if config.get('direct_listing'):
            driver.command(f'restoretrace {out / (label + "-listing")} 0')
        else:
            cursor = driver.command('ui')['footer_cursor']
            for _ in range(abs(1 - cursor)):
                press(driver, 'left' if cursor > 1 else 'right')
            press(driver, 'a')
            info_ready(driver, None)
            press(driver, 'right')
            press(driver, 'a')
            moves_ready(driver)
        if static and config.get('follow_up'):
            # Species paging must still start the ordinary exact-timeline owner.
            driver.events.clear()
            switched = driver.run(('change_species', 'animation_miss', 'audio_miss'), frames=600, key='down')
            if switched['hit'] != 'change_species':
                raise RuntimeError('Internal paging did not start')
            next_state = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            next_index = next_state['selected_index']
            final = settle(driver)
            check = audit(repo.load([config['names'][next_index]])[0], switched, driver.events, final, cold=False)
            result['follow_up_playback'] = check
            result['issues'] += ['following_species:' + s for s in check['issues']]
            index = next_index
        driver.run(('leave', 'animation_miss', 'audio_miss'), frames=600, key='b')
        listing = driver.run(('listing', 'animation_miss', 'audio_miss'), frames=600)
        if listing['hit'] != 'listing' or listing['index'] != index:
            result['issues'].append('listing_return')
        if config.get('direct_listing'):
            driver.run(frames=5)
            driver.command('restorestop')
            trace = [json.loads(line) for line in (out / (label + '-listing.jsonl')).read_text().splitlines()]
            result['listing_summary'] = summarize(trace, reference)
            result['issues'] += ['listing:' + s for s in restoration_failures(result['listing_summary'])]
        result['status'] = 'pass' if not result['issues'] else 'fail'
    except Exception as error:
        result.update(status='error', error=str(error))
        try:
            result['failure'] = driver.evidence(out / (label + '-failure'))
        except Exception:
            pass
    finally:
        driver.close()
    (out / (label + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--sym', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--checkpoints', type=Path)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--views', nargs='+', default=['description', 'info', 'moves'])
    parser.add_argument('--phases', nargs='+', default=['0', 'settled'])
    parser.add_argument('--exit-keys', nargs='+', default=['b'])
    parser.add_argument('--uncaught', action='store_true')
    parser.add_argument('--images', action='store_true')
    parser.add_argument('--all-pages', action='store_true')
    parser.add_argument('--follow-up', action='store_true')
    parser.add_argument('--repeat-area', action='store_true')
    parser.add_argument('--direct-listing', action='store_true')
    parser.add_argument('--female', action='store_true')
    regions = parser.add_mutually_exclusive_group()
    regions.add_argument('--lock-kanto', action='store_true')
    regions.add_argument('--unlock-kanto', action='store_true')
    parser.add_argument('--player-map', nargs=3, metavar=('MAP', 'X', 'Y'))
    parser.add_argument('--hour-offset', type=int, choices=range(24))
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.rom, args.sym)
    names = [ALIASES.get(n, n.lower()) for n in re.findall(r'^\s*dw (\w+)\s*$',
              (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)]
    battery = args.output / 'private.sav'
    fixture(args.battery, battery, caught=not args.uncaught)
    if args.player_map:
        located = args.output / 'located.sav'
        make_fixture(repo, battery, located,
                     (args.player_map[0], int(args.player_map[1]), int(args.player_map[2])))
        battery = located
    if args.female or args.lock_kanto or args.unlock_kanto or args.hour_offset is not None:
        data = bytearray(battery.read_bytes())
        original = bytes(data)
        edits, allowed = {}, set()
        def saved(name):
            bank, pc = repo.symbols[name]
            return bank * 8192 + pc - 0xa000
        if args.female:
            at = saved('sCrystalData')
            data[at] |= 1
            allowed.add(at)
            edits['female'] = True
        for prefix in ('s', 'sBackup'):
            start, end = saved(prefix + 'SaveData'), saved(prefix + 'SaveDataEnd')
            checksum = saved(prefix + 'Checksum')
            if sum(original[start:end]) & 65535 != int.from_bytes(original[checksum:checksum + 2], 'little'):
                raise ValueError('Source fixture checksum invalid')
            if args.lock_kanto or args.unlock_kanto:
                at = saved(prefix + 'PlayerData') + repo.symbols['wStatusFlags'][1] - repo.symbols['wPlayerData'][1]
                data[at] = (data[at] & ~64) if args.lock_kanto else (data[at] | 64)
                allowed.add(at)
                edits['kanto_unlocked'] = args.unlock_kanto
            if args.hour_offset is not None:
                at = saved(prefix + 'PlayerData') + repo.symbols['wStartHour'][1] - repo.symbols['wPlayerData'][1]
                data[at] = (data[at] + args.hour_offset) % 24
                allowed.add(at)
                edits['hour_offset'] = args.hour_offset
            data[checksum:checksum + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')
            allowed.update((checksum, checksum + 1))
        if not {i for i, (a, b) in enumerate(zip(original, data)) if a != b} <= allowed:
            raise ValueError('Fixture changed an undeclared field')
        battery = args.output / 'variant.sav'
        battery.write_bytes(data)
        battery.with_suffix('.json').write_text(json.dumps(dict(edits=edits, original_sha256=sha256(original),
            variant_sha256=sha256(data), checksums_valid=True), indent=2))
    core = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', args.output,
        extra_points={'area_start': 'Pokedex_GetArea', 'area_loop': 'Pokedex_GetArea.loop'},
        extra_fields=('wPokedexRenderedSelectionKey',), extra_flags=('-DDEX_BACKLOG_REVALIDATION_TRACE',))
    provenance = dict(**repo.hashes, battery_sha256=sha256(battery.read_bytes()))
    if args.checkpoints:
        states = args.checkpoints / 'listing-states'
        old = json.loads((args.checkpoints / 'provenance.json').read_text())
        if old != provenance:
            raise ValueError('Area checkpoints do not match ROM, symbols and battery')
    else:
        states = args.output / 'listing-states'
        states.mkdir(exist_ok=True)
        driver = Driver(core, args.rom, BOOT, battery, args.output / 'bootstrap.log')
        try:
            bootstrap(driver)
            prepare_states(driver, states, len(names))
        finally:
            driver.close()
        (args.output / 'provenance.json').write_text(json.dumps(provenance, indent=2))
    config = dict(core=str(core), rom=str(args.rom), sym=str(args.sym), battery=str(battery),
                  states=str(states), names=names, output=str(args.output), images=args.images,
                  follow_up=args.follow_up, repeat_area=args.repeat_area, direct_listing=args.direct_listing)
    _, data, manifest = info_data()
    tasks = []
    for n in (args.species or names):
        constant = {'unown_a': 'UNOWN', 'porygonz': 'PORYGON_Z'}.get(n, n.upper())
        for v in args.views:
            if v == 'evo' and (args.uncaught or not data['roots'][constant]):
                continue
            count = (2 if v == 'description' else 1 + (len(data['roots'][constant]) + 1) // 2
                     if v == 'info' else max(1, len(manifest[constant]['pages'])) if v == 'moves' else 1)
            pages = range(count) if args.all_pages and not args.uncaught else (int(v in ('page2', 'evo')),)
            tasks += [(config, n, v, p, k, page) for page in pages for p in args.phases for k in args.exit_keys]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        runs = list(pool.map(run_case, tasks))
    report = dict(**provenance, cases=len(runs), failures=[r for r in runs if r['status'] != 'pass'],
                  runs=runs)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=report['cases'], failures=len(report['failures']))))
    raise SystemExit(bool(report['failures']))


if __name__ == '__main__':
    main()
