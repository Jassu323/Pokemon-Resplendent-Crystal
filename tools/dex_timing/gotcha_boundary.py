"""Paired native capture-tail and subsequent battle qualification.

Every ROM boots its own private battery. Explicit species/party/EXP fixtures
are applied before the native enemy initializer, never across different links.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import struct
import subprocess
import traceback
import wave

from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, KEY, FRAME
from . import performance, performance_audio as audio, shared_menu_regression as menu
from . import global_review_save as review, global_speed as speed
from .shared_menu_fixtures import make_fixture
from .new_entry import CORE_FILES
from pokedex_info_assets import constants

BASE = ROOT / 'build/gotcha-boundary-final-20261015'
SEED = ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'
SCENARIOS = ('party', 'party-name', 'pc', 'pc-name', 'repeat', 'no-dex',
             'learn-empty', 'learn-replace', 'learn-decline', 'exp-share',
             'multi-level', 'evolve', 'evolve-cancel')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def repo_for(config):
    repo = Repository(Path(config.get('root', ROOT)), Path(config['rom']), Path(config['sym']))
    bank, pc = repo.symbols['SampledCry_RestartCH3']
    assert repo.rom[offset((bank, pc)) + 23] == 0xc9
    repo.symbols['@wave_committed'] = bank, pc + 23
    bank, pc = repo.symbols['Text_GotchaMonWasCaught']
    assert repo.rom[offset((bank, pc))] == 0x16
    assert repo.rom[offset((bank, pc)) + 4] == 8
    repo.symbols['@gotcha'] = bank, pc + 5
    bank, pc = repo.symbols['xor_a']
    assert repo.rom[offset((bank, pc)) - 3:offset((bank, pc))] == bytes((0x79, 0xa7, 0xc9))
    repo.symbols['@dex_check_return'] = bank, pc - 1
    return repo


def compiler(repo, output):
    points = dict(speed.EXTRA, switch=('SwitchSpeed', True),
        handoff=('BattleSpeed_CaptureHandoff', True), gotcha=('@gotcha', False),
        palette_build=('BattleSpeed_CaptureHandoff.prepare_palettes', True),
        capture_stop=('BattleSpeed_CaptureHandoff.SwitchNow', False),
        exp=('ApplyExperienceAfterEnemyCaught', True), learning=('LearnMove', True),
        learned=('LearnMove.learned', False), declined=('LearnMove.cancel', False),
        naming=('NamingScreen', True), capture_return=('PokeBallEffect.return_from_capture', False),
        registration_return=('PokeBallEffect.skip_pokedex', False),
        cleanup=('CleanUpBattleRAM', True), map_disable=('BattleSpeed_MapDisableLCD', True),
        music=('_PlayMusic', False), sfx=('_PlaySFX', False))
    performance.core(repo, output, points)
    header = output / 'performance-symbols.h'
    with header.open('a') as stream:
        stream.write(f'#define S_wBattleMode {repo.symbols["wBattleMode"][1]}\n')
    return menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_SPEED_TRACE',
         f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"'))


def setup(baseline_source=ROOT):
    audio.SPECIES = ('caterpie', 'dusknoir')
    configs = {}
    party = (
        ('BULBASAUR', 'LEARN', ('BODY_SLAM', 'THUNDERBOLT', 'WATER_PULSE', 'POISON_GAS')),
        ('CATERPIE', 'EVOLVE', ('TACKLE', 'STRING_SHOT', 'BODY_SLAM', 'POISON_GAS')),
        *review.PARTY[2:])
    for variant, source in (('production', baseline_source), ('candidate', BASE / 'candidate')):
        folder = BASE / 'setup' / variant
        folder.mkdir(parents=True, exist_ok=False)
        config = dict(variant=variant, root=str(source), rom=str(source / 'pokecrystal.gbc'),
            sym=str(source / 'pokecrystal.sym'), expected_double_speed=1)
        repo = repo_for(config)
        seed = folder / 'party.sav'
        review.create(repo, SEED, seed, party, level=6)
        config['battery'] = str(seed)
        config = audio.prepare(config, folder / 'native', 0, 0)
        config['core'] = str(compiler(repo, folder / 'observer'))
        header = folder / 'fixture-symbols.h'
        bank, pc = repo.symbols['LoadEnemyMon']
        header.write_text(f'#define B_ENCOUNTER {bank}\n#define P_ENCOUNTER {pc}\n')
        factory = folder / 'fixture'
        sameboy = Path.home() / 'Documents/GitHub/SameBoy'
        subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
            '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
            '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="gotcha-fixture"',
            f'-DGOTCHA_FIXTURE_SYMBOLS="{header}"', str(ROOT / 'tools/dex_timing/probes/gotcha_fixture.c'),
            *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(factory)], check=True)
        config['factory'] = str(factory)
        configs[variant] = config
        print(json.dumps(dict(prepared=variant)), flush=True)
    write(BASE / 'config.json', configs)


def ram(driver, repo, name, size=1):
    bank, at = repo.symbols[name]
    return bytes.fromhex(driver.command(f'perfram {bank} {at} {size}')['bytes'])


def number(driver, repo, name, size=1):
    return int.from_bytes(ram(driver, repo, name, size), 'little')


def permanent(driver, repo, ids, kind):
    table = ram(driver, repo, f'w{kind}IndexTableEntries', 508)
    return [int.from_bytes(table[2*(n-1):2*n], 'little') if 0 < n < 0xfd else n for n in ids]


def snapshot(driver, repo):
    count = number(driver, repo, 'wPartyCount')
    mons = []
    for n in range(1, count + 1):
        data = ram(driver, repo, f'wPartyMon{n}', 48)
        mons.append(dict(species=permanent(driver, repo, data[:1], 'Pokemon')[0],
            moves=permanent(driver, repo, data[2:6], 'Move'), level=data[31],
            exp=int.from_bytes(data[8:11], 'big'), stats=data[34:48].hex(),
            dvs=data[21:23].hex(), pp=data[23:27].hex(), nickname=ram(driver, repo, f'wPartyMon{n}Nickname', 11).hex()))
    flags = ram(driver, repo, 'wMoveDiscoverySeen', 64)
    seen = [n for n in range(1, 334) if flags[(n-1)//8] & 1 << ((n-1)%8)]
    box_count = number(driver, repo, 'sBoxCount')
    boxed = ram(driver, repo, 'sBoxMon1', 32) if box_count else None
    box = dict(count=box_count)
    if boxed:
        box.update(species=permanent(driver, repo, boxed[:1], 'Pokemon')[0],
            moves=permanent(driver, repo, boxed[2:6], 'Move'),
            exp=int.from_bytes(boxed[8:11], 'big'), dvs=boxed[21:23].hex(),
            pp=boxed[23:27].hex(), nickname=ram(driver, repo, 'sBoxMonNicknames', 11).hex())
    return dict(party_count=count, mons=mons, seen=seen, box=box,
                balance=int.from_bytes(ram(driver, repo, 'wMoney', 3), 'big'),
                payday=int.from_bytes(ram(driver, repo, 'wPayDayMoney', 3), 'big'),
                battle_mode=number(driver, repo, 'wBattleMode'),
                world=driver.command('m'))


def validate_speed_changes(repo, events):
    changes = [e for e in events if e['event'] == 'speed_change' and not e['initial']]
    assert [e['speed'] for e in changes] == [1, 0, 1], changes
    assert all(not e['nr52'] & 128 and not e['sampled_active'] for e in changes)
    live = [e for e in changes if e['lcdc'] & 128]
    stops = [e for e in events if e['event'] == 'perf_phase' and e['name'] == 'capture_stop']
    if 'BattleSpeed_CaptureHandoff.Resumed' not in repo.symbols:
        assert not live and not stops, 'Unexpected visible speed switch'
    else:
        stop = repo.symbols['BattleSpeed_CaptureHandoff.SwitchNow']
        resumed = repo.symbols['BattleSpeed_CaptureHandoff.Resumed']
        assert resumed == (stop[0], stop[1] + 2)
        assert repo.rom[offset(stop):offset(stop)+2] == b'\x10\x00'
        assert len(stops) == len(live) and live, 'Missing synchronized capture handoff'
        for before, after in zip(stops, live):
            assert before['t'] < after['t']
            assert before['stat'] & 3 == 3 and before['lcdc'] & 128
            assert before['speed'] == 0 and not before['nr52'] & 128 and not before['ie']
            assert after['speed'] == 1 and (after['bank'], after['pc']) == resumed
    return dict(transitions=len(changes), live_capture_switches=len(live),
                mode3_stops=len(stops), sound_inactive=True, other_switches_lcd_off=True)


def fixture(driver, repo, config, folder, scenario):
    edits = []
    def put(label, data):
        bank, at = repo.symbols[label]
        data = bytes(data)
        edits.append((label, bank, at, data))
    put('wMoveDiscoverySeen', bytes(64))
    count = 6 if scenario.startswith('pc') else 4
    put('wPartyCount', (count,))
    species = bytearray(ram(driver, repo, 'wPartySpecies', 7))
    species[count] = 255
    if scenario.startswith('evolve'):
        first, second = ram(driver, repo, 'wPartyMon1', 48), ram(driver, repo, 'wPartyMon2', 48)
        put('wPartyMon1', second)
        put('wPartyMon2', first)
        species[0], species[1] = species[1], species[0]
        for suffix in ('Nickname', 'OT'):
            a, b = ram(driver, repo, 'wPartyMon1'+suffix, 11), ram(driver, repo, 'wPartyMon2'+suffix, 11)
            put('wPartyMon1'+suffix, b)
            put('wPartyMon2'+suffix, a)
        put('wPartyMon1Exp', (342).to_bytes(3, 'big'))
        moves = bytearray(second[2:6]); moves[3] = 0
        pp = bytearray(second[23:27]); pp[3] = 0
        put('wPartyMon1Moves', moves)
        put('wPartyMon1PP', pp)
    elif scenario.startswith('learn') or scenario in ('exp-share', 'multi-level'):
        put('wPartyMon1Exp', (235).to_bytes(3, 'big'))
        if scenario in ('learn-empty', 'exp-share', 'multi-level'):
            moves = bytearray(ram(driver, repo, 'wPartyMon1Moves', 4)); moves[3] = 0
            pp = bytearray(ram(driver, repo, 'wPartyMon1PP', 4)); pp[3] = 0
            put('wPartyMon1Moves', moves); put('wPartyMon1PP', pp)
        if scenario == 'exp-share':
            put('wPartyMon2Item', (0x39,))
            put('wPartyMon2Exp', (342).to_bytes(3, 'big'))
        if scenario == 'multi-level':
            put('wCurPartyLevel', (60,))
    put('wPartySpecies', species)
    if scenario == 'repeat':
        index = permanent(driver, repo, ram(driver, repo, 'wWildMon'), 'Pokemon')[0]
        flags = bytearray(ram(driver, repo, 'wPokedexCaught', 47))
        flags[(index-1)//8] |= 1 << ((index-1)%8)
        put('wPokedexCaught', flags)
    elif scenario == 'no-dex':
        bit = constants(repo.root / 'constants/ram_constants.asm')['STATUSFLAGS_POKEDEX_F']
        put('wStatusFlags', (number(driver, repo, 'wStatusFlags') & ~(1 << bit),))
    patch = folder / 'fixture.bin'
    patch.write_bytes(b''.join(struct.pack('<BHH', bank, at, len(data)) + data for _, bank, at, data in edits))
    donor, state = folder / 'donor.s0', folder / 'fixture.s0'
    driver.command(f'save {donor}')
    subprocess.run([config['factory'], config['rom'], str(donor), str(patch), str(state)],
                   check=True, capture_output=True)
    write(folder / 'fixture.json', dict(fields=[dict(name=n, bank=b, address=a, bytes=d.hex()) for n,b,a,d in edits],
        donor_sha256=sha256(donor.read_bytes()), state_sha256=sha256(state.read_bytes())))
    driver.command(f'load {state}')


def world(driver, repo, key='b'):
    audio.until(driver, repo, 'HandleMapTimeAndJoypad', key=key, attempts=300)
    menu.run(driver, repo, frames=32)
    state = driver.command('m')
    assert state['double_speed'] == 1 and state['wBattleMode'] == 0
    assert not state['hInMenu'] and not state['wScriptRunning']
    return state


def next_battle(driver, repo, action='run', capture_evidence=None):
    before = driver.command('m')
    for n in range(400):
        state = menu.run(driver, repo, 'LoadEnemyMon', 12, KEY['up' if n//20%2 == 0 else 'down'])
        if audio.at(state, repo, 'LoadEnemyMon'):
            break
    else:
        raise AssertionError('No following native encounter')
    audio.until(driver, repo, 'BattleMenu.loop')
    assert driver.command('m')['double_speed'] == 0
    menu.run(driver, repo, frames=20)
    if action == 'fight':
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        menu.run(driver, repo, frames=8)
        for _ in range(8):
            if number(driver, repo, 'wMenuCursorY') == 2: break
            menu.tap(driver, repo, 'down', released=12)
        assert number(driver, repo, 'wMenuCursorY') == 2
        assert permanent(driver, repo, ram(driver, repo, 'wBattleMonMoves', 4), 'Move')[1] == 85
        returned = world(driver, repo, 'a')
    elif action == 'catch':
        evidence = capture_evidence if capture_evidence is not None else {}
        evidence['before'] = snapshot(driver, repo)
        index = permanent(driver, repo, ram(driver, repo, 'wEnemyMonSpecies'), 'Pokemon')[0]
        assert 1 <= index <= 373, index
        caught = ram(driver, repo, 'wPokedexCaught', 47)
        bit = constants(repo.root / 'constants/ram_constants.asm')['STATUSFLAGS_POKEDEX_F']
        was_caught = bool(caught[(index-1)//8] & 1 << ((index-1)%8))
        has_dex = bool(number(driver, repo, 'wStatusFlags') & (1 << bit))
        evidence.update(species=index, previously_caught=was_caught, received_dex=has_dex,
                        registration_expected=has_dex and not was_caught)
        event_start = len(driver.events)
        menu.tap(driver, repo, 'down')
        audio.until(driver, repo, 'BattlePack.loop')
        for _ in range(10):
            if number(driver, repo, 'wCurPocket') == 1: break
            menu.tap(driver, repo, 'right', released=30)
        audio.until(driver, repo, 'ApplyExperienceAfterEnemyCaught')
        assert driver.command('m')['double_speed'] == int('BattleSpeed_CaptureHandoff' in repo.symbols)
        if evidence['registration_expected']:
            audio.until(driver, repo, 'NewPokedexEntry')
            interactive = 'NewDexRegistration_Loop' in repo.symbols
            evidence['registration_owner'] = 'streaming' if interactive else 'resident'
            entry_loop = ('NewDexRegistration_Loop' if interactive else
                          'NewPokedexEntry.WaitPressAorB_AnimateFrontpic')
            return_label = ('NewPokedexEntry_ReturnFromDexRegistration' if interactive else
                            'NewPokedexEntry.ReturnFromDexRegistration')
            audio.until(driver, repo, entry_loop, key=None)
            menu.run(driver, repo, frames=240)
            audio.until(driver, repo, return_label, key='b')
            evidence['registration_return_reached'] = True
            audio.until(driver, repo, 'PokeBallEffect.skip_pokedex', key=None)
        else:
            audio.until(driver, repo, 'PokeBallEffect.skip_pokedex')
        entries = [e for e in driver.events[event_start:]
                   if e['event'] == 'perf_phase' and e['name'] == 'entry']
        evidence['registration_entries'] = len(entries)
        assert len(entries) == int(evidence['registration_expected']), evidence
        caught = ram(driver, repo, 'wPokedexCaught', 47)
        evidence['caught_after'] = bool(caught[(index-1)//8] & 1 << ((index-1)%8))
        assert evidence['caught_after'], evidence
        audio.until(driver, repo, 'PokeBallEffect.return_from_capture', key='b')
        evidence['after_delivery'] = snapshot(driver, repo)
        before_delivery, delivered = evidence['before'], evidence['after_delivery']
        to_pc = before_delivery['party_count'] == 6
        assert delivered['party_count'] == before_delivery['party_count'] + int(not to_pc)
        assert delivered['box']['count'] == before_delivery['box']['count'] + int(to_pc)
        mon = delivered['box'] if to_pc else delivered['mons'][-1]
        assert mon['species'] == index, evidence
        assert set(mon['moves']) - {0} <= set(delivered['seen']), evidence
        evidence['delivery_verified'] = True
        returned = world(driver, repo)
    else:
        position = number(driver, repo, 'wBattleMenuCursorPosition')
        if position <= 2:
            menu.tap(driver, repo, 'down')
        if number(driver, repo, 'wBattleMenuCursorPosition') % 2:
            menu.tap(driver, repo, 'right')
        audio.until(driver, repo, 'BattleMenu_Run')
        returned = world(driver, repo, 'a')
    # A grass encounter may return to the initial coordinate after a round trip.
    # Reaching it through native directional input proves step dispatch resumed.
    audio.until(driver, repo, 'StartMenu.loop', key='start')
    menu.run(driver, repo, frames=8)
    audio.until(driver, repo, 'HandleMapTimeAndJoypad', key='b')
    return returned


def execute(task):
    config, scenario, species, phase = task
    repo = repo_for(config)
    base = Path(config.get('campaign_base', BASE))
    folder = base / config.get('run_folder', 'runs') / config['variant'] / f'{scenario}-{species}-q{phase}'
    folder.mkdir(parents=True, exist_ok=False)
    driver = Driver(config['core'], config['rom'], menu.BOOT, config['battery'], folder / 'native.log')
    row = dict(variant=config['variant'], scenario=scenario, species=species, phase=phase,
               following_action=config.get('next_action', 'run'), issues=[])
    capture = phase == 0 and scenario in ('party-name', 'evolve')
    raw = folder / 'audio.pcm'
    try:
        driver.command(f'load {config["states"][species]["encounter"]}')
        fixture(driver, repo, config, folder, scenario)
        driver.command('perf 1'); driver.command('audit 1'); driver.events.clear()
        if capture:
            driver.command(f'perfaudio {raw}')
        row['before'] = snapshot(driver, repo)
        row['caught_species'] = permanent(driver, repo, ram(driver, repo, 'wWildMon'), 'Pokemon')[0]
        audio.until(driver, repo, 'BattleMenu.loop')
        assert driver.command('m')['double_speed'] == 0
        menu.run(driver, repo, frames=24 + phase/4)
        menu.tap(driver, repo, 'down')
        audio.until(driver, repo, 'BattlePack.loop')
        for _ in range(10):
            if number(driver, repo, 'wCurPocket') == 1: break
            menu.tap(driver, repo, 'right', released=30)
        audio.until(driver, repo, '@gotcha')
        if capture:
            row['video_start_t'] = driver.command('m')['t']
            driver.command(f'perfimages {folder / "frame"}')
        audio.until(driver, repo, 'ApplyExperienceAfterEnemyCaught')
        row['exp_speed'] = driver.command('m')['double_speed']
        assert row['exp_speed'] == int('BattleSpeed_CaptureHandoff' in repo.symbols)
        if scenario == 'learn-decline':
            audio.until(driver, repo, 'LearnMove')
            audio.until(driver, repo, 'LearnMove.cancel', key='b')
        has_registration = scenario not in ('repeat', 'no-dex')
        if has_registration:
            audio.until(driver, repo, 'NewPokedexEntry')
            driver.command(f'save {folder / "registration.s0"}')
            row['after_exp'] = snapshot(driver, repo)
            interactive = 'NewDexRegistration_Loop' in repo.symbols
            entry_loop = ('NewDexRegistration_Loop' if interactive else
                          'NewPokedexEntry.WaitPressAorB_AnimateFrontpic')
            return_label = ('NewPokedexEntry_ReturnFromDexRegistration' if interactive else
                            'NewPokedexEntry.ReturnFromDexRegistration')
            row['registration_owner'] = 'streaming' if interactive else 'resident'
            audio.until(driver, repo, entry_loop, key=None)
            menu.run(driver, repo, frames=240)
            audio.until(driver, repo, return_label, key='b')
        else:
            if scenario == 'no-dex':
                bit = constants(repo.root / 'constants/ram_constants.asm')['STATUSFLAGS_POKEDEX_F']
                flags = number(driver, repo, 'wStatusFlags')
                assert not flags & (1 << bit), 'No-Dex fixture still owns the Pokedex'
                audio.until(driver, repo, '@dex_check_return')
                driver.command('instructions 1')
                returned = next(e for e in reversed(driver.events) if e['event'] == 'instruction')
                row['no_dex_check'] = dict(flag_bit=bit, status_flags=flags, native_return=returned)
                assert returned['af'] >> 8 == 0 and returned['af'] & 0x80, returned
            audio.until(driver, repo, 'PokeBallEffect.skip_pokedex',
                        key=None if scenario == 'no-dex' else 'a')
            entries = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'entry']
            row['skipped_registration_entries'] = len(entries)
            if scenario == 'no-dex':
                row['no_dex_check']['registration_entries'] = len(entries)
            assert not entries, 'Registration ran on a skipped capture: ' + str(entries)
            row['after_exp'] = snapshot(driver, repo)
        if scenario.endswith('name'):
            audio.until(driver, repo, 'NamingScreen.loop')
            menu.run(driver, repo, frames=4)
            menu.tap(driver, repo, 'a')
            assert number(driver, repo, 'wNamingScreenCurNameLength') == 1
            menu.tap(driver, repo, 'start')
            menu.tap(driver, repo, 'a')
            audio.until(driver, repo, 'PokeBallEffect.return_from_capture')
        else:
            audio.until(driver, repo, 'PokeBallEffect.return_from_capture', key='b')
        row['after_delivery'] = snapshot(driver, repo)
        if scenario.startswith('evolve') or scenario == 'exp-share':
            audio.until(driver, repo, 'EvolutionAnimation', key='b')
            row['evolution_speed'] = driver.command('m')['double_speed']
            if scenario == 'evolve-cancel':
                audio.until(driver, repo, 'CancelEvolution', key='b')
            row['first_world'] = world(driver, repo, 'a')
        else:
            row['first_world'] = world(driver, repo)
        row['after'] = snapshot(driver, repo)
        # These no-attack Master Ball fixtures never legitimately earn Pay Day.
        assert row['after']['balance'] == row['before']['balance'], 'Unexpected capture payout'
        lead = row['after']['mons'][0]
        if scenario.startswith('learn') or scenario in ('exp-share','multi-level'):
            assert lead['level'] >= 7
            assert (73 in lead['moves']) == (scenario != 'learn-decline')
            assert (73 in row['after']['seen']) == (scenario != 'learn-decline')
        if scenario.startswith('evolve'):
            assert lead['species'] == (10 if scenario == 'evolve-cancel' else 11)
        if scenario.endswith('name') and not scenario.startswith('pc'):
            assert row['after']['mons'][-1]['nickname'].startswith('8050')
        if scenario.startswith('pc'):
            box = row['after']['box']
            assert box['count'] == row['before']['box']['count'] + 1
            assert box['species'] == row['caught_species']
            assert set(box['moves']) - {0} <= set(row['after']['seen'])
            if scenario.endswith('name'):
                assert box['nickname'].startswith('8050')
        assert row['after']['party_count'] == row['before']['party_count'] + int(not scenario.startswith('pc'))
        if capture:
            driver.command('perfimages -'); driver.command('perfaudio -')
            with wave.open(str(folder / 'audio.wav'), 'wb') as wav:
                wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
                wav.writeframes(raw.read_bytes())
        if config.get('next_action') == 'catch':
            row['following_capture'] = {}
        row['following_world'] = next_battle(driver, repo, config.get('next_action', 'run'),
                                            row.get('following_capture'))
        row['following_balance'] = int.from_bytes(ram(driver, repo, 'wMoney', 3), 'big')
        assert row['following_balance'] == row['before']['balance'], 'Unexpected following-battle payout'
        row['segments'] = audio.audio_segments(driver.events)
        row['speed_changes'] = [e for e in driver.events if e['event'] == 'speed_change']
        row['speed_contract'] = validate_speed_changes(repo, driver.events)
        assert all(e['speed'] == 0 for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'battle_anim')
        row['milestones'] = [e for e in driver.events if e['event'] in ('perf_phase','perf_cost') and
            e['name'] in ('gotcha','handoff','switch','exp','learning','learned','declined','naming','evolution','cleanup','music','sfx','palette_build')]
        row['misses'] = [e for e in driver.events if e['event'] in ('audio_miss','animation_miss','illegal')]
    except Exception as error:
        row['issues'].append(f'{type(error).__name__}: {error}')
        row['traceback'] = traceback.format_exc()
    finally:
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as log:
            log.write(''.join(json.dumps(e)+'\n' for e in driver.events))
        driver.close()
    if raw.exists() and (folder / 'audio.wav').exists(): raw.unlink()
    row['native_warnings'] = (folder / 'native.log').read_text()
    write(folder / 'result.json', row)
    print(json.dumps({k: row.get(k) for k in ('variant','scenario','species','phase','issues','native_warnings')}), flush=True)
    return row


def campaign(jobs, smoke=False):
    configs = json.loads((BASE / 'config.json').read_text())
    for cfg in configs.values():
        cfg['campaign_base'] = str(BASE)
    if smoke:
        for cfg in configs.values():
            cfg['run_folder'] = 'smoke-runs'
    work = [(cfg, name, 'dusknoir' if name.startswith(('pc','party')) else 'caterpie', phase)
            for cfg in configs.values() for name in (('party','learn-replace','evolve') if smoke else SCENARIOS)
            for phase in ((0,) if smoke else (0,1,2,3))]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(execute, work))
    write(BASE / ('smoke.json' if smoke else 'report.json'), dict(cases=len(rows), results=rows))
    print(json.dumps(dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows))), flush=True)


def supplement(jobs):
    configs = json.loads((BASE / 'config.json').read_text())
    for cfg in configs.values(): cfg['campaign_base'] = str(BASE)
    work = [(dict(cfg, run_folder='supplement', next_action=action), name, 'dusknoir', phase)
            for cfg in configs.values() for action in ('fight','catch')
            for name, phase in (('party', 0), ('pc-name', 1))]
    # Distinguish the two follow-up actions without replacing earlier evidence.
    for config, _, _, _ in work:
        config['run_folder'] += '/' + config['next_action']
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(execute, work))
    write(BASE / 'supplement.json', dict(cases=len(rows), results=rows))
    print(json.dumps(dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows))), flush=True)


def retry(jobs):
    prior=json.loads((BASE/'supplement.json').read_text())
    (BASE/'supplement.json').rename(BASE/'supplement-initial-status-move-driver.json')
    configs=json.loads((BASE/'config.json').read_text())
    for cfg in configs.values(): cfg['campaign_base']=str(BASE)
    positions=[n for n,r in enumerate(prior['results']) if r['issues']]
    work=[(dict(configs[prior['results'][n]['variant']], run_folder='supplement-fight-retry', next_action='fight'),
           prior['results'][n]['scenario'],prior['results'][n]['species'],prior['results'][n]['phase']) for n in positions]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows=list(pool.map(execute,work))
    for n,row in zip(positions,rows): prior['results'][n]=row
    prior['harness_retry']='Explicitly select Thunderbolt: newly learned Leech Seed had replaced slot one.'
    write(BASE/'supplement.json',prior)
    print(json.dumps(dict(cases=len(prior['results']),failures=sum(bool(r['issues']) for r in prior['results']))))


def registration(jobs):
    from .shared_new_entry_regression import prepare
    from .new_entry_sweep import run_case, cases
    configs=json.loads((BASE/'config.json').read_text())
    work=[]
    reports={}
    for variant,config in configs.items():
        folder=BASE/'registration'/variant
        donor=BASE/'runs'/variant/'party-dusknoir-q0/registration.s0'
        cfg,assets,report=prepare(Path(config['root']),donor,folder,
            Path.home()/'Documents/GitHub/SameBoy',expected_speed=int(variant=='candidate'))
        reports[variant]=report
        for asset in assets.values():
            for case in (cases(0,0)[0],
                dict(name='page-and-return',family='exit',windows=[(1,5,2,16),(2,8,2,32)]),
                dict(name='held-a',family='stress',windows=[(0,0,600,16)]),
                dict(name='held-b',family='stress',windows=[(0,0,600,32)]),
                dict(name='held-ab',family='stress',windows=[(0,0,600,48)]),
                dict(name='rapid-ab',family='stress',windows=[(1,n,2,16 if n%8==0 else 32) for n in range(0,240,4)])):
                work.append((cfg,asset,case))
        write(folder/'config.json',cfg)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows=list(pool.map(run_case,work))
    report=dict(cases=len(rows),failures=sum(r['status']!='pass' for r in rows),
                results=rows,structural={v:{k:r[k] for k in ('structural','publication','description_publication')} for v,r in reports.items()})
    write(BASE/'registration.json',report)
    print(json.dumps(dict(cases=len(rows),failures=report['failures'])),flush=True)


def contracts(baseline_source=ROOT):
    import unittest
    import tools.test_new_dex_entry as tests
    previous=tests.ROOT
    rows=[]
    try:
        for variant,root in (('production',baseline_source),('candidate',BASE/'candidate')):
            tests.ROOT=root
            with (BASE/(variant+'-contracts.log')).open('w') as log:
                result=unittest.TextTestRunner(stream=log,verbosity=2).run(
                    unittest.defaultTestLoader.loadTestsFromModule(tests))
            rows.append(dict(variant=variant,cases=result.testsRun,failures=len(result.failures),
                             errors=len(result.errors),skips=len(result.skipped)))
    finally:
        tests.ROOT=previous
    write(BASE/'contracts.json',rows)
    assert all(not r['failures'] and not r['errors'] and not r['skips'] for r in rows)
    print(json.dumps(rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('setup','smoke','campaign','supplement','retry','registration','contracts'))
    parser.add_argument('--output', type=Path, default=BASE)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--baseline-source', type=Path, default=ROOT)
    args = parser.parse_args()
    BASE = args.output.resolve()
    if args.action == 'setup': setup(args.baseline_source.resolve())
    elif args.action == 'supplement': supplement(args.jobs)
    elif args.action == 'retry': retry(args.jobs)
    elif args.action == 'registration': registration(args.jobs)
    elif args.action == 'contracts': contracts(args.baseline_source.resolve())
    else: campaign(args.jobs, args.action == 'smoke')
