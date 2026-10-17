"""Focused special-caller registration tests; never edits a ROM or main save.

Native script/capture input is distinguished from declared RAM-data fixtures
and the optional direct ForceGarbageCollection call. No broad timing campaign.
Run with PYTHONPATH=tools; outputs must be fresh directories under build/.

Example:
  PYTHONPATH=tools python3 -m tools.dex_timing.interactive_registration_returns \
    --candidate build/interactive-registration-dev07-20261015/candidate \
    --output build/interactive-registration-special-returns
"""
import argparse
import gzip
import json
from pathlib import Path
import re
import struct
import subprocess
import traceback
import wave

from . import gotcha_boundary as catch, performance_audio as audio
from . import shared_menu_regression as menu
from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, FRAME, KEY, POINTS
from .cry_ownership import validate_output
from .interactive_registration_regression import cursor, run, tap, SEED
from .new_entry import CORE_FILES
from .shared_menu_fixtures import make_fixture

CASES = ('contest', 'celebi', 'transformed', 'goldenrod', 'celadon')
SAMEBOY = Path.home() / 'Documents/GitHub/SameBoy'
HISTORY = {'wPrevDexEntry': bytes((0x53, 1)), 'wPrevDexEntryBackup': bytes((0x44, 1)),
    'wLastMovesDexSort': bytes((0xa1,)), 'wMovesDexBookmarkTag': bytes((0xa1, 85, 0, 3)),
    'wPokemonDexBookmarkTag': bytes((0xa0, 25, 0, 4))}
PRESERVE = dict(wPartyMon1=48, wPartyCount=1, wMoveDiscoverySeen=64,
    wPokedexOrder=748, wDexListingScrollOffsetBackup=2, wDexListingCursorBackup=1,
    wPrevDexEntry=2, wPrevDexEntryBackup=2, wPrevDexEntryJumptableIndex=1,
    wLastDexMode=1, wLastDexPresentation=1, wCurDexMode=1, wLastMovesDexSort=1,
    wMovesDexBookmarkTag=4, wPokemonDexBookmarkTag=4,
    wCurPartySpecies=1, wCurSpecies=1, wTempSpecies=1, wUnownLetter=1,
    wOptions=1, wStateFlags=1, wVolume=1, wLastVolume=1, wScriptVar=1,
    wMenuCursorY=1, wJumptableIndex=1, wPokedexStatus=1,
    wDexArrowCursorPosIndex=1, wDexArrowCursorDelayCounter=1, wDexArrowCursorBlinkCounter=1)
PORTS = ('hMapAnims', 'hSCX', 'hSCY', 'hWX', 'hWY', 'hVBlank', 'hOAMUpdate',
         'hBGMapMode', 'hLCDCPointer', 'hInMenu', 'hMapObjectIndex', 'hObjectStructIndex',
         'rVBK', 'rSVBK')
JOBS = ('wPokedexOwnerTransition', 'wPokedexDescriptionTextState', 'wPokedexInfoState',
        'wPokedexInfoPendingPage', 'wPokedexMovesState', 'wPokedexAnimFlags',
        'wPokedexAnimPlaybackState', 'wPokedexAnimSchedulerControl', 'hSampledCryTimer',
        'hDMATransfer', 'wRequested1bppSize', 'wRequested2bppSize')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def compile_fixture(repo, folder, sameboy):
    folder.mkdir(parents=True)
    lines = []
    for short, label in dict(ENCOUNTER='LoadEnemyMon', OVERWORLD='HandleMapTimeAndJoypad',
            INPUT='NewDexRegistration_Input', ALLOCATE='GetPokemonIDFromIndex',
            LOCK='LockPokemonID', GC='ForceGarbageCollection', FARCALL='FarCall_hl',
            VISIBLE='InitializeVisibleSprites').items():
        bank, pc = repo.symbols[label]
        lines += [f'#define B_{short} {bank}', f'#define P_{short} {pc}']
    locks = re.findall(r'^\s*const\s+(\w+)',
        (repo.root / 'constants/16_bit_locking_constants.asm').read_text(), re.M)
    lines.append(f'#define LOCK_POSITION {locks.index("LOCKED_MON_ID_DEX_SELECTED")}')
    header = folder / 'symbols.h'
    header.write_text('\n'.join(lines) + '\n')
    binary = folder / 'returns-fixture'
    subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(sameboy), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="returns-fixture"',
        f'-DRETURNS_FIXTURE_SYMBOLS="{header}"',
        str(ROOT / 'tools/dex_timing/probes/interactive_registration_returns_fixture.c'),
        *(str(sameboy / 'Core' / (f+'.c')) for f in CORE_FILES), '-o', str(binary)], check=True)
    return binary, locks.index('LOCKED_MON_ID_DEX_SELECTED')


def fixture(driver, repo, factory, folder, mode, edits, label):
    donor, state, patch = (folder / (mode + suffix) for suffix in ('.donor.s0', '.s0', '.bin'))
    driver.command(f'save {donor}')
    records = [(name, *repo.symbols[name], bytes(data)) for name, data in edits.items()]
    patch.write_bytes(b''.join(struct.pack('<BHH', b, at, len(data)) + data for _, b, at, data in records))
    b, pc = repo.symbols[label]
    result = subprocess.run([str(factory), str(repo.rom_path), str(donor), str(b), str(pc),
        mode, str(patch), str(state)], check=True, capture_output=True, text=True)
    declaration = dict(mode=mode, checkpoint=label,
        edits=[dict(name=n, bank=b, address=a, bytes=d.hex()) for n,b,a,d in records],
        routine=('allocate species 373 and set prior Selected lock' +
                 ('; direct InitializeVisibleSprites for saved map fixture' if label == 'HandleMapTimeAndJoypad' else '')) if mode == 'history' else
                'direct allocations 300..372 then ForceGarbageCollection, not native gameplay' if mode == 'gc' else None,
        **json.loads(result.stdout), donor_sha256=sha256(donor.read_bytes()),
        state_sha256=sha256(state.read_bytes()))
    write(folder / (mode + '.json'), declaration)
    driver.command(f'load {state}')
    return declaration


def snapshot(driver, repo, lock):
    fields = {name: catch.ram(driver, repo, name, size).hex() for name,size in PRESERVE.items()}
    fields.update({name: catch.number(driver, repo, name) for name in PORTS if name in repo.symbols})
    for name, address in (('rVBK', 0xff4f), ('rSVBK', 0xff70)):
        fields[name] = int(driver.command(f'perfram 0 {address} 1')['bytes'], 16)
    ids = catch.ram(driver, repo, 'wPokemonIndexTableLockedEntries', 32)
    fields['selected_lock_identity'] = catch.permanent(driver, repo, ids[lock:lock+1], 'Pokemon')[0]
    return dict(fields=fields, cpu=driver.command('m'))


def map_blocks(driver, repo):
    bank, address = repo.symbols['wOverworldMapBlocks']
    return b''.join(bytes.fromhex(driver.command(f'perfram {bank} {address+n} {min(512, 1300-n)}')['bytes'])
                    for n in range(0, 1300, 512))


def evidence(driver, folder, name):
    ppm = folder / (name + '.ppm')
    driver.command(f'image {ppm}')
    # Pillow preserves the native 160x144 frame without image editing.
    from PIL import Image
    Image.open(ppm).save(folder / (name + '.png'))


def registration(driver, repo, folder, button, lock, row, factory, gc, panel):
    row['entry'] = before = snapshot(driver, repo, lock)
    start = before['cpu']['t']
    event_offset = len(driver.events)
    row['registration_event_offset'] = event_offset
    driver.command(f'perfaudio {folder / "registration.pcm"}')
    audio.until(driver, repo, 'NewDexRegistration_Input', key=None)
    row['reveal_t'] = driver.command('m')['t']
    context_size = (repo.symbols['NewDexRegistration_Fields.end'][1] -
                    repo.symbols['NewDexRegistration_Fields'][1]) // 2 + 36
    context = catch.ram(driver, repo, 'wTempTilemap', context_size)
    row['saved_context_bytes'] = context.hex()
    row['saved_context_size'] = context_size
    run(driver, 2)
    row['evidence_capture_wait_frames'] = 2
    evidence(driver, folder, 'candidate-registration')
    if gc:
        run(driver, 360)
        audio.until(driver, repo, 'NewDexRegistration_Input', key=None)
        row['gc_fixture'] = fixture(driver, repo, factory, folder, 'gc', {}, 'NewDexRegistration_Input')
        row['gc_note'] = 'Direct GC after playback settles; not an audio/timing qualification.'
        size = repo.symbols['wPokemonIndexTableEntriesEnd'][1] - repo.symbols['wPokemonIndexTableEntries'][1]
        table = catch.ram(driver, repo, 'wPokemonIndexTableEntries', size)
        row['prior_lock_evicted'] = 373 not in struct.unpack(f'<{size//2}H', table)
        assert row['prior_lock_evicted'], 'GC fixture did not evict prior lock identity'
    # Exercise cancellation of a lower-panel job, not just idle-screen exit.
    panel = panel or ('info' if button == 'b' else 'moves')
    row['panel'] = panel
    cursor(driver, {'description': 0, 'info': 1, 'moves': 2}[panel])
    audio.until(driver, repo, {'description': 'PokedexSelectedMon_ToggleDescriptionPage',
        'info': 'PokedexInfo_Activate', 'moves': 'PokedexMoves_Activate'}[panel])
    audio.until(driver, repo, 'NewDexRegistration_Input', key=None)
    row['queued_before_exit'] = {n: catch.number(driver, repo, n) for n in JOBS}
    if button == 'end':
        cursor(driver, 3)
        assert driver.command('ui')['footer_cursor'] == 3
    audio.until(driver, repo, 'NewDexRegistration_Leave', key='b' if button == 'b' else 'a')
    row['leave_jobs'] = {n: catch.number(driver, repo, n) for n in JOBS}
    evidence(driver, folder, 'candidate-before-exit')
    audio.until(driver, repo, 'NewDexRegistration_Returned', key=None)
    row['returned'] = after = snapshot(driver, repo, lock)
    row['context_buffer_intact'] = catch.ram(driver, repo, 'wTempTilemap', context_size) == context
    assert row['context_buffer_intact'], 'Registration context was overwritten'
    row['restored'] = {n: v == after['fields'][n] for n,v in before['fields'].items()}
    # The legacy continuation deliberately requests the rebuilt BG tilemap.
    row['continuation_bgmap_mode'] = dict(before=before['fields']['hBGMapMode'],
                                         after=after['fields']['hBGMapMode'], expected=1)
    row['restored']['hBGMapMode'] = after['fields']['hBGMapMode'] == 1
    row['issues'] += ['changed_' + n for n,ok in row['restored'].items() if not ok]
    assert before['cpu']['sp'] == after['cpu']['sp'], 'registration stack mismatch'
    assert before['cpu']['bank'] == after['cpu']['bank'], 'registration ROM bank mismatch'
    assert after['cpu']['ime'] and after['cpu']['double_speed'] == 1
    row['cancelled'] = {n: catch.number(driver, repo, n) for n in JOBS}
    row['issues'] += ['live_after_return_' + n for n,v in row['cancelled'].items() if v]
    end = after['cpu']['t']
    row['timing'] = dict(total_ms=(end-start)*1000/4194304 if not gc else None,
        total_frame_equivalents=(end-start)/FRAME if not gc else None,
        display_frames=sum(e['event'] == 'perf_frame' and start <= e.get('t', -1) <= end for e in driver.events[event_offset:]) if not gc else None,
        reveal_ms=(row['reveal_t']-start)*1000/4194304,
        reveal_frame_equivalents=(row['reveal_t']-start)/FRAME,
        reveal_display_frames=sum(e['event'] == 'perf_frame' and start <= e.get('t', -1) <= row['reveal_t'] for e in driver.events[event_offset:]),
        total_unavailable_reason='fixture reload resets host clock' if gc else None)
    driver.command('perfaudio -')
    with wave.open(str(folder / 'registration.wav'), 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
        wav.writeframes((folder / 'registration.pcm').read_bytes())


def begin_capture(driver, repo, config, folder, scenario, factory):
    state = Path(config['states']['caterpie']['encounter'])
    driver.command(f'load {state}')
    species_context = None
    if scenario in ('celebi', 'transformed'):
        index = 251 if scenario == 'celebi' else 132
        state = folder / 'species.s0'
        generated = subprocess.run([str(Path(config['output']) / 'audio-fixture'), config['rom'],
            config['states']['caterpie']['encounter'], str(index), 'encounter', str(state)],
            check=True, capture_output=True, text=True)
        species_context = dict(**json.loads(generated.stdout),
            checkpoint='LoadEnemyMon', declared_fields=['wTempEnemyMonSpecies', 'wWildMon',
                'species allocator table', 'matching caught/seen flag bit'],
            state_sha256=sha256(state.read_bytes()))
        write(folder / 'species-fixture.json', species_context)
        driver.command(f'load {state}')
    edits = dict(HISTORY, wPartyCount=bytes((4,)))
    species = bytearray(catch.ram(driver, repo, 'wPartySpecies', 7)); species[4] = 255
    edits['wPartySpecies'] = species
    if scenario == 'contest':
        edits.update(wBattleType=bytes((6,)), wParkBallsRemaining=bytes((99,)),
                     wContestMon=bytes(48))
    elif scenario == 'celebi':
        edits['wBattleType'] = bytes((11,))
    else:
        edits['wCurPartyLevel'] = bytes((20,))
    declaration = fixture(driver, repo, factory, folder, 'history', edits, 'LoadEnemyMon')
    declaration['species_context'] = species_context
    audio.until(driver, repo, 'BattleMenu.loop')
    run(driver, 24)
    if scenario == 'transformed':
        audio.until(driver, repo, 'MoveSelectionScreen.menu_loop')
        run(driver, 8)
        for _ in range(8):
            if catch.number(driver, repo, 'wMenuCursorY') == 4: break
            menu.tap(driver, repo, 'down', released=12)
        assert catch.number(driver, repo, 'wMenuCursorY') == 4
        audio.until(driver, repo, 'BattleCommand_Transform')
        audio.until(driver, repo, 'BattleMenu.loop', key='a')
        assert catch.number(driver, repo, 'wEnemySubStatus5') & 8, 'Ditto did not Transform'
        declaration['native_transform_observed'] = True
        declaration['backup_dvs'] = catch.ram(driver, repo, 'wEnemyBackupDVs', 2).hex()
        evidence(driver, folder, 'candidate-transformed-battle')
        run(driver, 16)
    menu.tap(driver, repo, 'down')
    if scenario != 'contest':
        audio.until(driver, repo, 'BattlePack.loop')
        for _ in range(10):
            if catch.number(driver, repo, 'wCurPocket') == 1: break
            menu.tap(driver, repo, 'right', released=30)
    if scenario == 'contest':
        for attempt in range(12):
            for _ in range(400):
                state = driver.run(('returns_entry', 'returns_battle_menu'), frames=8, key='a')
                if state['hit'] is not None: break
                state = driver.run(('returns_entry', 'returns_battle_menu'), frames=8)
                if state['hit'] is not None: break
            else:
                raise AssertionError('Contest throw did not return to battle menu or registration')
            if state['hit'] == 'returns_entry':
                declaration['native_park_ball_attempts'] = attempt+1
                break
            run(driver, 24)
            position = catch.number(driver, repo, 'wBattleMenuCursorPosition')
            if position <= 2: menu.tap(driver, repo, 'down')
            if catch.number(driver, repo, 'wBattleMenuCursorPosition') == 4: menu.tap(driver, repo, 'left')
        else:
            raise AssertionError('Twelve native Park Balls did not catch the fixture')
    else:
        audio.until(driver, repo, 'NewPokedexEntry', attempts=240)
    return declaration


def saved_bytes(repo, source, name, size):
    bank, address = repo.symbols[name]
    data = source.read_bytes()
    for block in ('PlayerData', 'CurMapData', 'PokemonData'):
        b, start = repo.symbols['w'+block]
        if bank == b and start <= address and address+size <= repo.symbols['w'+block+'End'][1]:
            sb, at = repo.symbols['s'+block]
            offset = sb*8192 + at-0xa000 + address-start
            return data[offset:offset+size]
    raise ValueError(name)


def begin_prize(driver, repo, config, folder, scenario, factory):
    menu.boot_overworld(driver, repo)
    menu.settle_map_input(driver, repo)
    audio.until(driver, repo, 'HandleMapTimeAndJoypad', key=None)
    fixture(driver, repo, factory, folder, 'history', HISTORY, 'HandleMapTimeAndJoypad')
    tap(driver, 'up', held=8, released=16)
    # The actual NPC/background event starts the map's vendor bytecode.
    audio.until(driver, repo, 'GameCornerPrizeMonCheckDex')
    before_map = map_blocks(driver, repo)
    before = dict(party=catch.number(driver, repo, 'wPartyCount'),
                  coins=int.from_bytes(catch.ram(driver, repo, 'wCoins', 2), 'big'),
                  script_bank=catch.number(driver, repo, 'wScriptBank'),
                  script_pos=catch.number(driver, repo, 'wScriptPos', 2),
                  map_sha256=sha256(before_map))
    audio.until(driver, repo, 'NewPokedexEntry', key=None)
    return before, before_map


def execute(config, scenario, button, out, factory, lock, gc=False, panel=None):
    folder = out / f'{scenario}-{button}'; folder.mkdir()
    repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
    local = dict(config)
    if scenario in ('goldenrod', 'celadon'):
        source = Path(config['battery'])
        party = bytearray(saved_bytes(repo, source, 'wPartySpecies', 7)); party[4] = 255
        location = ('GOLDENROD_GAME_CORNER', 18, 4) if scenario == 'goldenrod' else ('CELADON_GAME_CORNER_PRIZE_ROOM', 4, 2)
        battery = folder / 'map-fixture.sav'
        make_fixture(repo, source, battery, location, capture=True,
            extra_fields={'wPartyCount': bytes((4,)), 'wPartySpecies': party,
                          'wCoins': (9999).to_bytes(2, 'big'), 'wPlayerDirection': bytes((0,))})
        local['battery'] = str(battery)
    driver = Driver(config['core'], config['rom'], menu.BOOT, local['battery'], folder / 'native.log')
    row = dict(scenario=scenario, exit=button, issues=[], coverage='native-controller-path-with-declared-data-fixture',
               automated=True, visual_approval=False, listening_approval=False, **repo.hashes)
    row['scope_note'] = {
        'contest': 'Route 30 encounter with declared contest-type fixture; no contest entry/scoring script claim.',
        'celebi': 'Route 30 encounter with declared Celebi species/type fixture; no Ilex event script claim.',
        'transformed': 'Declared Ditto species fixture; real enemy Transform and capture inputs.',
        'goldenrod': 'Actual vendor bytecode, givepoke, takecoins and menu return.',
        'celadon': 'Actual vendor bytecode, givepoke, takecoins and menu return.',
    }[scenario]
    if scenario in ('goldenrod', 'celadon'):
        row['coverage'] = 'actual-map-script-controller-path; direct visible-object initialization for saved map fixture'
    try:
        driver.command('audit 1'); driver.command('perf 1')
        if scenario in ('goldenrod', 'celadon'):
            row['prize_before'], map_before = begin_prize(driver, repo, local, folder, scenario, factory)
        else:
            row['fixture'] = begin_capture(driver, repo, config, folder, scenario, factory)
        registration(driver, repo, folder, button, lock, row, factory, gc, panel)
        if scenario in ('goldenrod', 'celadon'):
            audio.until(driver, repo, 'ReturnToMapFromSubmenu', key=None)
            audio.until(driver, repo, 'ExitAllMenus', key=None)
            row['map_rebuilt'] = map_blocks(driver, repo) == map_before
            assert row['map_rebuilt'], 'map blocks were not rebuilt'
            audio.until(driver, repo, 'Script_givepoke', key=None)
            audio.until(driver, repo, 'Script_takecoins', key='b')
            assert catch.number(driver, repo, 'wPartyCount') == row['prize_before']['party']+1
            audio.until(driver, repo, 'Script_verticalmenu', key='b')
            row['prize_after'] = dict(party=catch.number(driver, repo, 'wPartyCount'),
                coins=int.from_bytes(catch.ram(driver, repo, 'wCoins', 2), 'big'),
                species=catch.permanent(driver, repo, catch.ram(driver, repo, 'wPartyMon5Species'), 'Pokemon')[0],
                level=catch.number(driver, repo, 'wPartyMon5Level'))
            assert row['prize_after']['species'] == (63 if scenario == 'goldenrod' else 25)
            assert row['prize_before']['coins']-row['prize_after']['coins'] == (100 if scenario == 'goldenrod' else 2222)
            audio.until(driver, repo, 'HandleMapTimeAndJoypad', key='b')
            run(driver, 32)
        else:
            audio.until(driver, repo, 'PokeBallEffect.return_from_capture', key='b')
            row['battle_result'] = catch.number(driver, repo, 'wBattleResult')
            if scenario == 'contest':
                assert catch.number(driver, repo, 'wPartyCount') == 4
                row['contest_species'] = catch.permanent(driver, repo, catch.ram(driver, repo, 'wContestMonSpecies'), 'Pokemon')[0]
                assert row['contest_species'] == 10
                # This checkpoint precedes .used_park_ball; qualify consumption after return.
                row['park_balls_before_consumption'] = catch.number(driver, repo, 'wParkBallsRemaining')
            else:
                assert catch.number(driver, repo, 'wPartyCount') == 5
                row['caught_species'] = catch.permanent(driver, repo, catch.ram(driver, repo, 'wPartyMon5Species'), 'Pokemon')[0]
                assert row['caught_species'] == (251 if scenario == 'celebi' else 132)
                if scenario == 'celebi': assert row['battle_result'] & 64
                if scenario == 'transformed':
                    assert catch.ram(driver, repo, 'wPartyMon5DVs', 2).hex() == row['fixture']['backup_dvs']
            catch.world(driver, repo)
            if scenario == 'contest':
                row['park_balls_after_consumption'] = catch.number(driver, repo, 'wParkBallsRemaining')
                assert row['park_balls_after_consumption'] == 99 - row['fixture']['native_park_ball_attempts']
        row['world'] = driver.command('m')
        assert row['world']['wBattleMode'] == 0 and not row['world']['hInMenu'] and not row['world']['wScriptRunning']
        evidence(driver, folder, 'candidate-returned-world')
        row['misses'] = [e for e in driver.events if e['event'] in ('animation_miss', 'audio_miss', 'illegal')]
        row['issues'] += [e['event'] for e in row['misses']]
    except Exception as error:
        row['issues'].append(f'{type(error).__name__}: {error}')
        row['traceback'] = traceback.format_exc()
        if driver.process.poll() is None:
            driver.command(f'save {folder / "failure.s0"}')
            evidence(driver, folder, 'failure')
    finally:
        if driver.process.poll() is None:
            driver.command('perfaudio -')
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e)+'\n' for e in driver.events))
        try:
            driver.close()
        except BrokenPipeError:
            pass
    write(folder / 'result.json', row)
    print(json.dumps(dict(scenario=scenario, exit=button, issues=row['issues'])), flush=True)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config', type=Path, help='Matching-link Gotcha setup config.json')
    source.add_argument('--candidate', type=Path, help='Fresh matching native setup for this candidate')
    parser.add_argument('--battery', type=Path, default=SEED)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', choices=CASES, default=CASES)
    parser.add_argument('--exits', nargs='+', choices=('b', 'end'), default=('b', 'end'))
    parser.add_argument('--gc', action='store_true', help='Also invoke direct GC after playback settles')
    parser.add_argument('--panel', choices=('description', 'info', 'moves'), help='Override lower-panel cancellation target')
    parser.add_argument('--sameboy', type=Path, default=SAMEBOY)
    args = parser.parse_args()
    if args.config:
        configs = json.loads(args.config.read_text()); config = configs.get('candidate', configs)
    else:
        root = args.candidate.resolve()
        config = dict(root=str(root), rom=str(root / 'pokecrystal.gbc'),
                      sym=str(root / 'pokecrystal.sym'), battery=str(args.battery.resolve()),
                      expected_double_speed=1)
    out = validate_output(args.output, (Path(config['rom']), Path(config['sym']), Path(config['battery'])))
    out.mkdir(parents=True, exist_ok=False)
    repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
    protected = {str(p): sha256(p.read_bytes()) for p in
        (ROOT / 'pokecrystal.gbc', *ROOT.glob('*.sav'), Path(config['rom']), Path(config['battery']))}
    # Recompile a matching host observer, never the candidate ROM.
    POINTS.update(returns_entry='NewPokedexEntry', returns_battle_menu='BattleMenu.loop')
    config = dict(config, core=str(catch.compiler(repo, out / 'observer')))
    if args.candidate:
        original_species = audio.SPECIES
        try:
            audio.SPECIES = ('caterpie',)
            native = audio.prepare(config, out / 'native', 0, 0)
        finally:
            audio.SPECIES = original_species
        config.update({key: native[key] for key in ('battery', 'states', 'output')})
    write(out / 'config.json', config)
    factory, lock = compile_fixture(repo, out / 'fixture', args.sameboy)
    rows = [execute(config, name, button, out, factory, lock, args.gc, args.panel)
            for name in args.cases for button in args.exits]
    assert all(sha256(Path(p).read_bytes()) == digest for p,digest in protected.items())
    write(out / 'report.json', dict(cases=len(rows), failures=sum(bool(r['issues']) for r in rows),
        results=rows, protected=protected, production_and_main_saves_unchanged=True,
        automated=True, visual_approval=False, listening_approval=False))
    return int(any(r['issues'] for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
