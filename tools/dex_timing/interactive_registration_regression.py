"""Native fixed-species registration qualification and matched Selected timing.

All batteries, generated contexts, checkpoints, recordings and reports belong
under build/. Checkpoints are never transported across links. Generated species
contexts are explicitly distinguished from the authentic native donor catch.

Example (PYTHONPATH=tools):
  python3 -m tools.dex_timing.interactive_registration_regression smoke \
    --candidate build/interactive-registration-dev07-20261015/candidate \
    --output build/interactive-registration-smoke-FRESH
"""
import argparse
import copy
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import traceback
import wave

from . import performance, performance_audio as audio, shared_menu_regression as menu
from . import cry_ownership
from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, FRAME, KEY, bootstrap, prepare_states, move
from .cold_listing import expected_picture
from .description_paging import description_pages
from .info_ui import info_audit, type_audit
from .moves_ui import content_audit
from .new_entry import CORE_FILES
from .gotcha_boundary import number, ram
from pokedex_info_assets import Compiler, species as species_constants
from pokedex_moves_assets import compile as moves_metadata

HZ = 4194304
STRESS_FAMILIES = ('rapid-tabs', 'rapid-info', 'held-a', 'directions',
                   'finish-boundary', 'after-finish', 'early-b', 'early-end')
SEED = ROOT / 'build/dex-moves-search-final-review-20261011/legacy-input.sav'
SAMEBOY = Path.home() / 'Documents/GitHub/SameBoy'
REPRESENTATIVE = ('caterpie', 'exeggcute', 'mewtwo', 'eevee', 'tyrogue',
    'slowpoke', 'poliwhirl', 'gloom', 'magnemite', 'swinub', 'treecko', 'torchic',
    'mudkip', 'dusknoir', 'bastiodon', 'groudon', 'spheal', 'weavile',
    'luxray', 'metagross')
LABELS = {
    'entry': 'NewPokedexEntry', 'reveal': 'NewDexRegistration_Revealed',
    'loop': 'NewDexRegistration_Loop', 'input': 'NewDexRegistration_Input',
    'leave': 'NewDexRegistration_Leave', 'returned': 'NewDexRegistration_Returned',
    'desc_request': 'PokedexSelectedMon_ToggleDescriptionPage',
    'info_request': 'PokedexInfo_Activate', 'moves_request': 'PokedexMoves_Activate',
    'desc_published': 'Pokedex_VBlankDescriptionText.committed',
    'begin': 'Pokedex_BeginPreparedDescriptionAnimation',
}
FIELDS = {
    'view': ('wPokedexSelectedView', 1), 'desc': ('wPokedexDescriptionPage', 1),
    'info_page': ('wPokedexInfoPage', 1), 'info_state': ('wPokedexInfoState', 1),
    'info_pending': ('wPokedexInfoPendingPage', 1),
    'moves_page': ('wPokedexMovesPage', 1), 'moves_state': ('wPokedexMovesState', 1),
    'transition': ('wPokedexOwnerTransition', 1),
    'desc_state': ('wPokedexDescriptionTextState', 1),
    'playback': ('wPokedexAnimPlaybackState', 1), 'owner': ('wPokedexAnimOwner', 1),
    'identity': ('wPrevDexEntry', 2), 'live_species': ('wPokedexSelectedSpecies', 1),
    'pressed': ('hJoyPressed', 1), 'footer': ('wDexArrowCursorPosIndex', 1),
    'scheduler': ('wPokedexAnimSchedulerControl', 1), 'anim_flags': ('wPokedexAnimFlags', 1),
    'deadline': ('wPokedexAnimDeadline', 1), 'loop_tick': ('wPokedexAnimLoopTick', 1),
    'work_tick': ('wPokedexAnimWorkTick', 1), 'display_tick': ('hVBlankCounter', 1),
}
PRESERVE = {
    'wMoveDiscoverySeen': 64, 'wLastDexMode': 1, 'wLastDexPresentation': 1,
    'wLastMovesDexSort': 1, 'wMovesDexBookmarkTag': 5,
    'wPokemonDexBookmarkTag': 5, 'wEnemyMon': 40,
    'wPartyMon1': 48, 'wPartyCount': 1, 'wOptions': 1,
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def labels_for(repo, overrides=None, require=True):
    labels = dict(LABELS, **(overrides or {}))
    # Observe the lower-assets ACK RET; complete scanout is measured separately.
    for name, following in (('info_published', 'Pokedex_VBlankInfoAssets.not_info'),
                            ('moves_published', 'Pokedex_VBlankInfoAssets.info')):
        bank, pc = repo.symbols[following]
        if repo.rom[offset((bank, pc - 1))] != 0xc9:
            raise ValueError(f'{following}: publication RET changed; supply an explicit label')
        synthetic = '@interactive_' + name
        repo.symbols[synthetic] = bank, pc - 1
        labels.setdefault(name, synthetic)
    missing = {k: v for k, v in labels.items() if v not in repo.symbols}
    if require and missing:
        raise ValueError(f'Missing registration observability labels: {missing}')
    return {k: v for k, v in labels.items() if v in repo.symbols}, missing


def compile_observer(repo, output, labels, sameboy=SAMEBOY):
    output.mkdir(parents=True, exist_ok=True)
    header = (output / 'performance-symbols.h').resolve()
    points = dict(performance.POINTS,
        prepare_front=('Pokedex_PrepareFrontpicBase', False),
        prime=('Pokedex_PrimeDescriptionAnimation', False),
        sample_start=('StartSampledCryAsync', False), synth_start=('_PlayCry', False))
    bank, pc = repo.symbols['SampledCry_RestartCH3']
    if repo.rom[offset((bank, pc)) + 23] != 0xc9:
        raise ValueError('Sampled CH3 commit observer changed')
    repo.symbols['@interactive_wave'] = bank, pc + 23
    points['wave_block'] = ('@interactive_wave', False)
    points.update({k: (v, False) for k, v in labels.items()})
    lines = ['static const struct { unsigned bank,pc; const char *name; bool span; } perf_points[] = {']
    for name, (label, span) in points.items():
        if label in repo.symbols:
            bank, pc = repo.symbols[label]
            lines.append(f'{{{bank},{pc},"{name}",{str(span).lower()}}},')
    header.write_text('\n'.join(lines + ['};']) + '\n')
    ih = (output / 'interactive-symbols.h').resolve()
    lines = ['static const struct { const char *name; unsigned bank,address,size; } interactive_fields[] = {']
    for name, (label, size) in FIELDS.items():
        bank, at = repo.symbols[label]
        lines.append(f'{{"{name}",{bank},{at},{size}}},')
    lines += ['};', 'static const struct { const char *name; unsigned bank,pc; } interactive_points[] = {']
    for name, label in labels.items():
        bank, pc = repo.symbols[label]
        lines.append(f'{{"{name}",{bank},{pc}}},')
    ih.write_text('\n'.join(lines + ['};']) + '\n')
    flags = ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE',
             f'-DDEX_PERFORMANCE_SYMBOLS="{header}"',
             *cry_ownership.observer_flags(repo, output))
    menu.compile_observer(repo, sameboy, output, flags)
    binary = output / 'interactive-registration-core'
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(sameboy), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING',
        '-DGB_VERSION="interactive-registration"', '-include', str(output / 'linked-symbols.h'),
        '-DSHARED_MENU_INPUT_TRACE',
        f'-DSHARED_MENU_INPUT_SYMBOLS="{(output / "shared-menu-symbols.h").resolve()}"',
        f'-DINTERACTIVE_SYMBOLS="{ih}"', *flags,
        str(ROOT / 'tools/dex_timing/probes/interactive_registration.c'),
        *(str(sameboy / 'Core' / (f + '.c')) for f in CORE_FILES), '-o', str(binary)],
        check=True, capture_output=True, text=True)
    return binary


def run(driver, frames=1, key=None):
    return driver.command(f'run 0 {int(frames * FRAME)} {KEY.get(key, key or 0)}')


def tap(driver, key, held=2, released=2):
    state = run(driver, held, key)
    return run(driver, released) if released else state


def cursor(driver, target):
    for _ in range(8):
        current = driver.command('ui')['footer_cursor']
        if current == target:
            return
        tap(driver, 'right' if current < target else 'left')
    raise AssertionError(f'Footer did not reach {target}')


def ready(driver, view, page=None, limit=360):
    for _ in range(limit):
        ui = driver.command('ui')
        actual = ui['page'] if view == 0 else ui['info_page' if view == 1 else 'moves_page']
        busy = ui['description_state'] if view == 0 else ui['info_state' if view == 1 else 'moves_state']
        if ui['view'] == view and (page is None or actual == page) and not busy and not ui['owner_transition'] and not (view == 1 and ui.get('info_pending_page', 0)):
            run(driver, 2)
            return driver.command('ui')
        run(driver)
    state = {k: ui[k] for k in ('view', 'page', 'info_page', 'info_pages', 'moves_page',
                               'moves_pages', 'info_state', 'moves_state', 'owner_transition')}
    raise AssertionError(f'Page did not publish: view={view}, page={page}, last={state}')


def preserved(driver, repo):
    return {name: ram(driver, repo, name, size).hex() for name, size in PRESERVE.items()
            if name in repo.symbols}


def native_donor(config, repo, output):
    # Boot and encounter checkpoints are rebuilt from a battery, not relocated.
    before_species = audio.SPECIES
    try:
        audio.SPECIES = ('dusknoir',)
        native = audio.prepare(config, output / 'native', 0, 0)
    finally:
        audio.SPECIES = before_species
    driver = Driver(config['core'], config['rom'], menu.BOOT, native['battery'], output / 'catch.log')
    try:
        driver.command(f'load {native["states"]["dusknoir"]["encounter"]}')
        audio.until(driver, repo, 'BattleMenu.loop')
        run(driver, 24)
        tap(driver, 'down')
        audio.until(driver, repo, 'BattlePack.loop')
        for _ in range(10):
            if number(driver, repo, 'wCurPocket') == 1:
                break
            tap(driver, 'right', released=30)
        audio.until(driver, repo, 'NewPokedexEntry')
        state = driver.command('peek')
        if state['double_speed'] != 1:
            raise AssertionError('Gotcha boundary did not enter registration at double speed')
        donor = output / 'native-registration.s0'
        driver.command(f'save {donor}')
        write(output / 'native-donor.json', dict(**repo.hashes, state=state,
            state_sha256=sha256(donor.read_bytes()), authentic_native_catch='dusknoir'))
    finally:
        driver.close()
    return donor, native['battery']


def smoke(args):
    root, out = args.candidate.resolve(), args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh output directory under build/')
    out.mkdir(parents=True)
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    labels, missing = labels_for(repo)
    core = compile_observer(repo, out / 'observer', labels, args.sameboy)
    config = dict(root=str(root), rom=str(repo.rom_path), sym=str(root / 'pokecrystal.sym'),
        core=str(core), battery=str(args.battery), expected_double_speed=1)
    donor, battery = native_donor(config, repo, out)
    config.update(battery=str(battery), donor=str(donor), labels=labels, hashes=repo.hashes)
    write(out / 'config.json', config)
    driver = Driver(core, repo.rom_path, menu.BOOT, battery, out / 'smoke.log')
    row = dict(issues=[], **repo.hashes, automated=True, visual_approval=False, listening_approval=False)
    try:
        driver.command(f'load {donor}')
        driver.command('rawcolor'); driver.command('perf 1'); driver.command('audit 1')
        driver.command(f'crytrace {out / "cry.jsonl"}')
        driver.command(f'perfaudio {out / "audio.pcm"}')
        before = preserved(driver, repo)
        entered = menu.run(driver, repo, labels['loop'], 600)
        if not menu.at(entered, repo, labels['loop']):
            raise AssertionError(f'Registration startup did not reach its loop: {entered}')
        run(driver, 4)
        configured = next(r for r in catalog(repo, False) if r['species'] == 'dusknoir')
        pages = ((0, 0), (0, 1), (1, 0), (1, 1 % configured['info_pages']),
                 (2, 0), (2, 1 % configured['moves_pages']), (0, 0))
        for n, (view, page) in enumerate(pages):
            if n:
                cursor(driver, view); tap(driver, 'a')
            ui = ready(driver, view, page)
            driver.command(f'image {out / f"{n:02}-view{view}-page{page}.ppm"}')
            write(out / f'{n:02}-ui.json', ui)
            print(json.dumps(dict(smoke='page', view=view, page=page,
                playback=driver.command('peek')['playback'])), flush=True)
        run(driver, 240)
        audio.until(driver, repo, labels['returned'], key='b')
        after = preserved(driver, repo)
        row['preserved'] = {name: value == after[name] for name, value in before.items()}
        row['issues'] += [f'changed_{name}' for name, same in row['preserved'].items() if not same]
        row['issues'] += [e['event'] for e in driver.events if e['event'] in ('animation_miss', 'audio_miss')]
        row['final'] = driver.command('peek')
    except Exception as error:
        row['issues'].append(f'{type(error).__name__}: {error}')
        row['traceback'] = traceback.format_exc()
    finally:
        driver.command('crystop'); driver.command('perfaudio -')
        with gzip.open(out / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e) + '\n' for e in driver.events))
        driver.close()
    with wave.open(str(out / 'audio.wav'), 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
        wav.writeframes((out / 'audio.pcm').read_bytes())
    write(out / 'smoke.json', row)
    print(json.dumps(row), flush=True)
    return int(bool(row['issues']))


def catalog(repo, include_forms=True):
    constants = species_constants(repo.root)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    order = re.findall(r'^\s*dw (\w+)\s*$',
        (repo.root / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    compiler = Compiler(repo.root)
    info = compiler.compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
    moves = moves_metadata(repo.root, validate_only=True)
    assets = {a.name: a for a in repo.load()}
    rows = []
    for index, constant in enumerate(constants, 1):
        name = aliases.get(constant, constant.lower())
        forms = [name]
        if include_forms and constant == 'UNOWN':
            forms = ['unown_' + chr(97 + n) for n in range(26)]
        for form in forms:
            asset = assets[form]
            rows.append(dict(species=form, base=name, constant=constant, index=index,
                form=ord(form[-1]) - 96 if constant == 'UNOWN' else 0,
                listing_index=order.index(constant), info_pages=1 + len(info['pages'][constant]),
                info_headings=info['headings'][constant],
                moves_pages=max(1, len(moves[constant]['pages'])),
                move_categories=sorted({page[0] for page in moves[constant]['pages']}),
                cry='sampled' if asset.sample_blocks else 'synthesized',
                authored_frames=sum(e.duration for e in asset.events)))
    return rows


def operations(row):
    # Every page, wraps, Description 2, and all six directed tab-return pairs.
    result = [dict(name='desc-2', view=0, page=1), dict(name='desc-1', view=0, page=0)]
    for view, key in ((1, 'info_pages'), (2, 'moves_pages')):
        result += [dict(name=f'view{view}-page{p}', view=view, page=p)
                   for p in range(row[key])]
        result.append(dict(name=f'view{view}-wrap', view=view, page=0))
    for source in range(3):
        for target in range(3):
            if source != target:
                result.append(dict(name=f'tab-{source}-{target}', source=source, view=target, page=0))
    return result


def compile_factory(repo, output, sameboy=SAMEBOY):
    header = (output / 'fixture-symbols.h').resolve()
    fields = ('wCurSpecies', 'wCurPartySpecies', 'wTempSpecies', 'wNamedObjectIndex',
              'wTempEnemyMonSpecies', 'wEnemyMonSpecies', 'wWildMon')
    lines = []
    for name in ('wPokemonIndexTableEntries', 'wPokedexSeen', 'wPokedexCaught',
                 'wUnownLetter', 'wEnemyMonDVs'):
        bank, at = repo.symbols[name]
        lines += [f'#define B_{name} {bank}', f'#define S_{name} {at}']
    bank, at = repo.symbols['NewPokedexEntry']
    lines += [f'#define B_ENTRY {bank}', f'#define P_ENTRY {at}',
              f'#define P_ALLOCATE {repo.symbols["GetPokemonIDFromIndex"][1]}',
              'static const struct { unsigned bank,address; } identity_fields[] = {']
    lines += [f'{{{repo.symbols[n][0]},{repo.symbols[n][1]}}},' for n in fields]
    header.write_text('\n'.join(lines + ['};']) + '\n')
    binary = output / 'interactive-registration-fixture'
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(sameboy), '-DGB_INTERNAL',
        '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
        '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING',
        '-DGB_VERSION="interactive-fixture"', f'-DINTERACTIVE_FIXTURE_SYMBOLS="{header}"',
        str(ROOT / 'tools/dex_timing/probes/interactive_registration_fixture.c'),
        *(str(sameboy / 'Core' / (f + '.c')) for f in CORE_FILES), '-o', str(binary)],
        check=True, capture_output=True, text=True)
    return binary


def selected_battery(repo, source, destination):
    from move_discovery_assets import rebind_fixture
    original = source.read_bytes()
    data = bytearray(original)
    def saved(label):
        bank, address = repo.symbols[label]
        return bank * 8192 + address - 0xa000
    for prefix in ('s', 'sBackup'):
        for label, value in (('wLastDexMode', 0), ('wLastDexPresentation', 0)):
            at = saved(prefix + 'PlayerData') + repo.symbols[label][1] - repo.symbols['wPlayerData'][1]
            data[at] = value
        for field in ('Seen', 'Caught'):
            at = saved(prefix + 'PokemonData') + repo.symbols['wPokedex' + field][1] - repo.symbols['wPokemonData'][1]
            for index in range(373):
                data[at + index // 8] |= 1 << (index % 8)
        for label, value in (('wFirstUnownSeen', b'\x01'),
                             ('wUnownDex', bytes(range(1, 27)))):
            at = saved(prefix + 'PokemonData') + repo.symbols[label][1] - repo.symbols['wPokemonData'][1]
            data[at:at + len(value)] = value
        start, end = saved(prefix + 'SaveData'), saved(prefix + 'SaveDataEnd')
        at = saved(prefix + 'Checksum')
        data[at:at + 2] = (sum(data[start:end]) & 65535).to_bytes(2, 'little')
    destination.write_bytes(rebind_fixture(original, data, repo.symbols))
    if source.read_bytes() != original:
        raise AssertionError('Battery source changed')


def prepare(args):
    root, out = args.candidate.resolve(), args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh output directory under build/')
    out.mkdir(parents=True)
    for suffix in ('gbc', 'sym'):
        shutil.copy2(root / f'pokecrystal.{suffix}', out / f'input.{suffix}')
    repo = Repository(root, out / 'input.gbc', out / 'input.sym')
    labels, _ = labels_for(repo)
    rows = catalog(repo, not args.no_forms)
    if args.species:
        rows = [r for r in rows if r['species'] in args.species or r['base'] in args.species]
    core = compile_observer(repo, out / 'observer', labels, args.sameboy)
    config = dict(root=str(root), rom=str(repo.rom_path), sym=str(out / 'input.sym'),
        source_rom=str(root / 'pokecrystal.gbc'), source_sym=str(root / 'pokecrystal.sym'),
        core=str(core), battery=str(args.battery.resolve()), expected_double_speed=1,
        output=str(out), labels=labels, hashes=repo.hashes, catalog=rows,
        final_link=bool(args.final_link), latency_slack_frames=2,
        generated_fixture_kind='generated species context on fresh native catch',
        manual_visual_approval=False, manual_listening_approval=False)
    donor, battery = native_donor(config, repo, out)
    config['battery'] = str(battery)
    factory = compile_factory(repo, out / 'observer', args.sameboy)
    states = out / 'registration-fixtures'
    states.mkdir()
    fixtures = {}
    for row in rows:
        path = states / (row['species'] + '.s0')
        result = subprocess.run([str(factory), config['rom'], str(donor),
            str(row['index']), str(row['form']), str(path)], check=True,
            capture_output=True, text=True)
        fixtures[row['species']] = dict(path=str(path), sha256=sha256(path.read_bytes()),
            preparation=json.loads(result.stdout), rom_sha256=repo.hashes['rom_sha256'])
    config['fixtures'] = fixtures
    config['references'] = {}
    for name in sorted({r['species'] for r in rows} | {r['base'] for r in rows}):
        asset = repo.load([name])[0]
        path = states / (name + '.references')
        path.write_bytes(bytes((len(asset.plans),)) + b''.join(
            expected_picture(asset, n) for n in range(len(asset.plans))))
        config['references'][name] = dict(path=str(path), sha256=sha256(path.read_bytes()))
    selected = out / 'selected.sav'
    selected_battery(repo, args.battery, selected)
    config['selected_battery'] = str(selected)
    states = out / 'listing-states'
    states.mkdir()
    driver = Driver(core, config['rom'], menu.BOOT, selected, out / 'listing-bootstrap.log')
    try:
        bootstrap(driver)
        prepare_states(driver, states, 373)
    finally:
        driver.close()
    config['listing_states'] = str(states)
    config['listing_hashes'] = {p.name: sha256(p.read_bytes()) for p in states.glob('*.s0')}
    write(out / 'config.json', config)
    validate_config(config)
    print(json.dumps(dict(prepared=len(rows), base_species=len({r['base'] for r in rows}),
        forms=sum(r['form'] > 1 for r in rows), final_link=config['final_link'])), flush=True)
    return config


def validate_config(config):
    for key, source in (('rom_sha256', 'source_rom'), ('sym_sha256', 'source_sym')):
        if sha256(Path(config[source]).read_bytes()) != config['hashes'][key]:
            raise ValueError('Candidate relinked: regenerate all fixtures in a fresh output directory')
    for key, field in (('rom_sha256', 'rom'), ('sym_sha256', 'sym')):
        if sha256(Path(config[field]).read_bytes()) != config['hashes'][key]:
            raise ValueError('Frozen input changed')
    for fixture in config['fixtures'].values():
        if sha256(Path(fixture['path']).read_bytes()) != fixture['sha256']:
            raise ValueError('Generated fixture changed')
    for reference in config.get('references', {}).values():
        if sha256(Path(reference['path']).read_bytes()) != reference['sha256']:
            raise ValueError('Authored picture reference changed')
    for name, expected in config['listing_hashes'].items():
        if sha256((Path(config['listing_states']) / name).read_bytes()) != expected:
            raise ValueError('Selected fixture changed')


@lru_cache(maxsize=2)
def content(config_json):
    config = json.loads(config_json)
    repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
    compiler = Compiler(repo.root)
    info = compiler.compile(ancestors='PokedexInfoEvolvesFromTitle' in repo.symbols)
    return repo, compiler, info, moves_metadata(repo.root, validate_only=True)


def semantic(driver, repo, compiler, info, moves, row, view, page):
    ui = driver.command('ui')
    name = row['base']
    if view == 1:
        issues = info_audit(compiler, info, name, page, ui, repo) + type_audit(repo, name, ui)
    elif view == 2:
        issues = content_audit(repo, name, page, ui, moves)
    else:
        from .description_ui import audit as description_audit
        issues = description_audit(repo, ui) + type_audit(repo, name, ui)
        expected = description_pages(repo, name)[page]
        actual = bytearray(b''.join(bytes.fromhex(ui['map'])[y * 21:y * 21 + 20] for y in range(8, 15)))
        actual[2], actual[22] = expected[2], expected[22]
        if actual != expected:
            issues.append('description_text')
    return issues


def frame_matches(frame, view, page):
    return (frame.get('view') == view and frame.get(('desc', 'info_page', 'moves_page')[view]) == page
            and not frame.get(('desc_state', 'info_state', 'moves_state')[view])
            and not frame.get('transition') and not (view == 1 and frame.get('info_pending')))


def timing(events, pressed, view, page, expected=None):
    point = ('desc_request', 'info_request', 'moves_request')[view]
    accepted = next((e for e in events if e['event'] == 'interactive_phase' and
                     e['point'] == point and e['t'] >= pressed), None)
    frames = [e for e in events if e['event'] == 'interactive_frame' and frame_matches(e, view, page)]
    final = frames[-1] if frames else None
    target = expected or final
    publication = next((e for e in events if e['event'] == 'interactive_phase' and
        accepted and e['t'] >= accepted['t'] and
        e['point'] == ('desc_published', 'info_published', 'moves_published')[view] and
        e.get('view') == view and e.get(('desc', 'info_page', 'moves_page')[view]) == page), None)
    # A VBlank callback reports the completed display. Identical wrap content
    # can already match before acceptance, or while its new job is still queued.
    complete = next((e for e in frames if target and publication and
        e['t'] > publication['t'] and e['t'] >= accepted['t'] and
        e.get('display', 0) > publication.get('display', -1) and
        e['upper'] == target['upper'] and e['panel'] == target['panel']), None)
    def interval(event, start):
        if not event or start is None:
            return None
        cycles = event['t'] - start
        return dict(t_cycles=cycles, ms=cycles * 1000 / HZ, display_frames=cycles / FRAME,
                    display_ordinal=event.get('display'))
    return dict(pressed_t=pressed, accepted_t=accepted['t'] if accepted else None,
        published_t=publication['t'] if publication else None,
        input_to_accept=interval(accepted, pressed),
        request_to_published=interval(publication, accepted['t'] if accepted else None),
        request_to_displayed=interval(complete, accepted['t'] if accepted else None),
        input_to_displayed=interval(complete, pressed),
        pixel_signature={key: final[key] for key in ('upper', 'panel')} if final else None,
        pixel_parity=bool(complete), complete_visible_t=complete['t'] if complete else None)


def playback_audit(asset, events, complete=True):
    issues = []
    misses = [e for e in events if e['event'] in ('animation_miss', 'audio_miss')]
    issues += [e['event'] for e in misses if e['event'] != 'audio_miss' or e.get('remaining')]
    if complete and any(e['event'] == 'audio_stop' and e.get('remaining') for e in events):
        issues.append('sampled_cry_interrupted')
    waves = [e for e in events if e['event'] == 'wave_block']
    if complete and len(waves) != asset.sample_blocks:
        issues.append(f'wave_blocks_{len(waves)}_expected_{asset.sample_blocks}')
    pubs = [e for e in events if e['event'] == 'publish']
    expected = [(e.frame, e.duration) for e in asset.events] + [(0, 0)]
    if complete and len(pubs) != len(expected):
        issues.append(f'animation_publications_{len(pubs)}_expected_{len(expected)}')
    elapsed = 0
    for i, (pub, (frame, duration)) in enumerate(zip(pubs, expected)):
        if pub['frame'] != frame or bytes.fromhex(pub['picture']) != expected_picture(asset, frame):
            issues.append(f'animation_content_{i}')
        if round((pub['t'] - pubs[0]['t']) / FRAME) != elapsed:
            issues.append(f'animation_deadline_{i}')
        if not 144 <= pub['ly'] <= 153:
            issues.append(f'animation_outside_vblank_{i}')
        elapsed += duration
    for point in ('prepare_front', 'prime', 'sample_start', 'synth_start'):
        count = sum(e['event'] == 'perf_phase' and e['name'] == point for e in events)
        if count > 1:
            issues.append(f'restarted_{point}_{count}')
    valid = {fnv(expected_picture(asset, n)) for n in range(len(asset.plans))}
    first = pubs[0]['t'] if pubs else float('inf')
    frames = [e for e in events if e['event'] == 'interactive_frame' and e['t'] > first]
    if any(e['picture'] not in valid for e in frames):
        issues.append('displayed_portrait_corruption')
    rendered = [e for e in events if e['event'] == 'interactive_pixels' and e['t'] > first]
    if not rendered and complete:
        issues.append('rendered_portrait_not_observed')
    elif any(not e['references'] or not e['valid'] for e in rendered):
        issues.append('rendered_portrait_pixel_corruption')
    if any(e['speed'] != 1 for e in frames):
        issues.append('not_double_speed')
    return list(dict.fromkeys(issues))


def fnv(data):
    result = 2166136261
    for value in data:
        result = ((result ^ value) * 16777619) & 0xffffffff
    return result


def audio_signature(events, cry_path):
    waves = [e for e in events if e['event'] == 'wave_block']
    cry = [json.loads(line) for line in cry_path.read_text().splitlines()]
    notes = []
    for event in cry:
        channel = event.get('cur_channel', 0) - 4
        if (event['phase'] == 'synth_note' and 0 <= channel < 4
                and event['sfx_flags'][channel] & 0x20):
            notes.append((event['cur_channel'], event['sfx_address'][channel],
                          event['sfx_duration'][channel]))
    return dict(wave_blocks=len(waves),
        wave_sha256=sha256(b''.join(bytes.fromhex(e['wave']) for e in waves)),
        wave_frequencies=sorted({e['frequency'] for e in waves}),
        wave_speeds=sorted({e['speed'] for e in waves}),
        synth_notes=len(notes), synth_sha256=sha256(json.dumps(notes).encode()),
        sampled_starts=sum(e['phase'] == 'sample_start' for e in cry),
        synth_starts=sum(e['phase'] == 'synth_start' for e in cry))


def save_pngs(folder):
    from PIL import Image
    for path in folder.glob('*.ppm'):
        if not path.name.startswith('frame-'):
            with Image.open(path) as picture:
                picture.save(path.with_suffix('.png'))


def display_signature(driver, folder, view, page):
    from PIL import Image
    path = folder / 'last-display.ppm'
    driver.command(f'image {path}')
    with Image.open(path) as picture:
        raw = picture.convert('RGB').tobytes()
    upper, panel = bytearray(), bytearray()
    for y in range(132):
        for x in range(160):
            if 3 <= x < 59 and 8 <= y < 64:
                continue
            if view == 1 and page and y >= 69 and x < 32 and 88 <= y < 128:
                continue
            at = (y * 160 + x) * 3
            (upper if y < 69 else panel).extend(raw[at:at + 3])
    return dict(upper_sha256=sha256(upper), panel_sha256=sha256(panel))


def enter(driver, repo, config, row, mode):
    reference = config['references'][row['species'] if mode == 'registration' else row['base']]
    driver.command(f'interactive_refs {reference["path"]}')
    if mode == 'registration':
        driver.command(f'load {config["fixtures"][row["species"]]["path"]}')
    else:
        driver.command(f'load {config["listing_states"]}/listing-{row["listing_index"]:03}.s0')
    driver.command('rawcolor'); driver.command('perf 1'); driver.command('audit 1')
    driver.events.clear()
    before = preserved(driver, repo)
    if mode == 'registration':
        state = menu.run(driver, repo, config['labels']['loop'], 600)
        if not menu.at(state, repo, config['labels']['loop']):
            raise AssertionError(f'Registration startup failed: {state}')
    else:
        state = driver.run(('selected',), 600, 'a')
        if state['hit'] != 'selected':
            raise AssertionError(f'Selected startup failed: {state}')
    run(driver, 4)
    ready(driver, 0, 0)
    return before


def finish_playback(driver, limit=1800):
    for _ in range(limit // 4):
        state = driver.command('peek')
        if state['playback'] == 3 and not state['audio'] and not state['sfx']:
            return state
        run(driver, 4)
    raise AssertionError('Authored animation/cry did not finish naturally')


def exit_case(driver, repo, config, checkpoint, original, end, fast=False):
    driver.command(f'load {checkpoint}')
    driver.command('perf 1')
    driver.events.clear()
    checkpoint_ui = driver.command('ui')
    if end and fast:
        for _ in range(4):
            current = driver.command('ui')['footer_cursor']
            if current >= 2:
                break
            tap(driver, 'right', held=1, released=1)
        if driver.command('ui')['footer_cursor'] != 2:
            raise AssertionError('Fast End did not reach the adjacent footer column')
    elif end:
        cursor(driver, 3)
    before = driver.command('ui')
    pressed = driver.command('peek')['t']
    state = menu.run(driver, repo, config['labels']['returned'], 600,
                     KEY['a'] | KEY['right'] if end and fast else KEY['a' if end else 'b'])
    if not menu.at(state, repo, config['labels']['returned']):
        raise AssertionError(f'{"End" if end else "B"} did not return to native caller: {state}')
    after = preserved(driver, repo)
    issues = ['return_changed_' + name for name, value in original.items() if value != after[name]]
    ui = driver.command('ui')
    if ui['description_state'] or ui['info_state'] or ui['moves_state'] or ui['owner_transition']:
        issues.append('exit_retained_pending_job')
    run(driver, 8)
    returns = [e for e in driver.events if e['event'] == 'interactive_phase' and e['point'] == 'returned']
    leaves = [e for e in driver.events if e['event'] == 'interactive_phase' and e['point'] == 'leave']
    if len(leaves) != 1:
        issues.append('leave_count')
    leave = leaves[0] if leaves else None
    if end and leave and leave['footer'] != 3:
        issues.append('End_did_not_use_End_footer')
    if len(returns) != 1:
        issues.append('continuation_return_count')
    returned_t = returns[0]['t'] if returns else state['t']
    if any(e['event'] == 'interactive_phase' and e['point'].endswith('_published')
           and e['t'] > returned_t for e in driver.events):
        issues.append('stale_publication_after_return')
    return dict(exit='End' if end else 'B', before={k: before[k] for k in
        ('view', 'page', 'info_page', 'moves_page', 'description_state', 'info_state', 'moves_state')},
        pending_at_input=bool(before['description_state'] or before['info_state'] or before['moves_state']),
        pending_at_checkpoint=bool(checkpoint_ui['description_state'] or checkpoint_ui['info_state'] or checkpoint_ui['moves_state']),
        pending_at_leave=bool(leave and any(leave[k] for k in ('desc_state', 'info_state', 'moves_state', 'transition'))),
        leave=leave,
        ms=(state['t'] - pressed) * 1000 / HZ,
        display_frames=(state['t'] - pressed) / FRAME, issues=issues)


def pending_exit_species(task):
    config, row = task
    folder = Path(config['output']) / 'pending-exits' / row['species']
    if (folder / 'result.json').exists():
        return json.loads((folder / 'result.json').read_text())
    folder.mkdir(parents=True, exist_ok=True)
    repo, _, _, _ = content(json.dumps(config, sort_keys=True))
    driver = Driver(config['core'], config['rom'], menu.BOOT, config['battery'], folder / 'native.log')
    report = dict(species=row['species'], issues=[], exits=[], **config['hashes'])
    try:
        original = enter(driver, repo, config, row, 'registration')
        checkpoints = sorted((Path(config['output']) / 'runs/registration-exits' / row['species']).glob('pending-*.s0'))
        for checkpoint in checkpoints:
            for end in (False, True):
                result = exit_case(driver, repo, config, checkpoint, original, end, fast=end)
                report['exits'].append(dict(operation=checkpoint.stem.removeprefix('pending-'), **result))
                report['issues'] += result['issues']
        report['checkpoint_count'] = len(checkpoints)
    except Exception as error:
        report['issues'].append(f'{type(error).__name__}: {error}')
        report['traceback'] = traceback.format_exc()
    finally:
        driver.close()
    write(folder / 'result.json', report)
    return report


def pending_exits(config, jobs, names=None):
    validate_config(config)
    rows = [r for r in config['catalog'] if not names or r['base'] in names]
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for future in as_completed([pool.submit(pending_exit_species, (config, row)) for row in rows]):
            results.append(future.result())
            if len(results) % 25 == 0 or len(results) == len(rows):
                print(json.dumps(dict(pending_exit_species=len(results), total=len(rows),
                    failures=sum(bool(r['issues']) for r in results))), flush=True)
    counts = {view: dict(B=0, End=0) for view in range(3)}
    for row in results:
        for item in row['exits']:
            if item['pending_at_leave']:
                counts[item['leave']['view']][item['exit']] += 1
    report = dict(**config['hashes'], species=len(results),
        checkpoints=sum(r.get('checkpoint_count', 0) for r in results),
        exits=sum(len(r['exits']) for r in results),
        failures=sum(bool(r['issues']) for r in results), pending_at_leave_by_view=counts,
        policy='Native physical buttons only; one-frame footer taps then Right+A together from Mov to select and activate End in one poll. Job state observed at NewDexRegistration_Leave, before cancellation.',
        results=results)
    write(Path(config['output']) / 'pending-exits.json', report)
    return report


def run_species(task):
    config, row, mode, exits, record = task
    repo, compiler, info, moves = content(json.dumps(config, sort_keys=True))
    folder = Path(config['output']) / 'runs' / (mode + '-exits' if exits else mode) / row['species']
    folder.mkdir(parents=True, exist_ok=False)
    battery = config['battery' if mode == 'registration' else 'selected_battery']
    driver = Driver(config['core'], config['rom'], menu.BOOT, battery, folder / 'native.log')
    report = dict(species=row['species'], mode=mode, issues=[], warnings=[], operations=[], exits=[],
                  **config['hashes'], final_link=config['final_link'])
    full_events = []
    reference_report = None
    try:
        driver.command(f'crytrace {folder / "cry.jsonl"}')
        if record:
            driver.command(f'perfaudio {folder / "audio.pcm"}')
            driver.command(f'perfimages {folder / "frame"}')
        original = enter(driver, repo, config, row, mode)
        references = {}
        if mode == 'registration':
            path = Path(config['output']) / 'runs/selected' / row['base'] / 'result.json'
            if not path.exists():
                raise AssertionError('Run ordinary Selected references before registration parity')
            reference_report = json.loads(path.read_text())
            references = reference_report['references']
        if mode == 'registration':
            fixed = number(driver, repo, 'wPrevDexEntry', 2)
            if fixed != row['index']:
                report['issues'].append('wrong_fixed_species')
        checkpoints = {}
        signatures = {}
        for operation in operations(row):
            if 'source' in operation:
                source = operation['source']
                if driver.command('ui')['view'] != source:
                    cursor(driver, source); tap(driver, 'a'); ready(driver, source, 0)
            view, page = operation['view'], operation['page']
            cursor(driver, view)
            pressed = driver.command('peek')['t']
            start = len(driver.events)
            tap(driver, 'a')
            pending = driver.command('ui')
            pending_path = None
            if exits and mode == 'registration' and (pending['description_state'] or pending['info_state'] or pending['moves_state']):
                pending_path = folder / f'pending-{operation["name"]}.s0'
                driver.command(f'save {pending_path}')
            ui = ready(driver, view, page)
            measured = timing(driver.events[start:], pressed, view, page,
                              references.get(f'{view}-{page}'))
            exact = display_signature(driver, folder, view, page)
            if measured['pixel_signature']:
                measured['pixel_signature'].update(exact)
            issues = semantic(driver, repo, compiler, info, moves, row, view, page)
            if references and any(exact[k] != references[f'{view}-{page}'].get(k) for k in exact):
                issues.append('exact_RGB_pixel_parity')
            if not measured['pixel_parity']:
                issues.append('displayed_pixel_parity')
            if measured['request_to_published'] is None:
                issues.append('publication_not_observed')
            if reference_report:
                baseline = next(o for o in reference_report['operations'] if o['name'] == operation['name'])
                for metric in ('request_to_published', 'request_to_displayed'):
                    actual, normal = measured[metric], baseline[metric]
                    if (row['species'] == row['base'] and actual and normal and
                            actual['display_frames'] > normal['display_frames'] + config.get('latency_slack_frames', 2)):
                        report['warnings'].append(operation['name'] + ':latency_alert_' + metric)
            if mode == 'registration' and number(driver, repo, 'wPrevDexEntry', 2) != row['index']:
                issues.append('species_changed')
            report['operations'].append(dict(operation, **measured, issues=issues))
            signatures[f'{view}-{page}'] = measured['pixel_signature']
            if record:
                driver.command(f'image {folder / (operation["name"] + ".ppm")}')
            if exits and mode == 'registration':
                complete_path = folder / f'committed-{view}-{page}.s0'
                driver.command(f'save {complete_path}')
                checkpoints[f'{view}-{page}'] = complete_path
                full_events += driver.events
                driver.events.clear()
                for path, state_kind in ((pending_path, 'pending'), (complete_path, 'committed')):
                    if path:
                        for end in (False, True):
                            result = exit_case(driver, repo, config, path, original, end)
                            report['exits'].append(dict(operation=operation['name'], state=state_kind, **result))
                driver.command(f'load {complete_path}')
                driver.command('perf 1')
                driver.events.clear()
        if not exits:
            finish_playback(driver)
            asset = repo.load([row['species'] if mode == 'registration' else row['base']])[0]
            report['issues'] += playback_audit(asset, driver.events)
        report['references'] = signatures
        report['issues'] += [f'{op["name"]}:{issue}' for op in report['operations'] for issue in op['issues']]
        report['issues'] += [f'{r["operation"]}:{r["state"]}:{r["exit"]}:{issue}' for r in report['exits'] for issue in r['issues']]
        if record:
            driver.command('perfimages -'); driver.command('perfaudio -')
    except Exception as error:
        report['issues'].append(f'{type(error).__name__}: {error}')
        report['traceback'] = traceback.format_exc()
    finally:
        full_events += driver.events
        driver.command('crystop'); driver.command('perfaudio -')
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e) + '\n' for e in full_events))
        driver.close()
    pcm = folder / 'audio.pcm'
    if pcm.exists():
        with wave.open(str(folder / 'audio.wav'), 'wb') as wav:
            wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
            wav.writeframes(pcm.read_bytes())
    if not exits:
        report['audio_signature'] = audio_signature(full_events, folder / 'cry.jsonl')
        if reference_report and report['audio_signature'] != reference_report.get('audio_signature'):
            report['issues'].append('cry_content_differs_from_Selected')
    if record:
        save_pngs(folder)
    report['status'] = 'fail' if report['issues'] else 'pass'
    write(folder / 'result.json', report)
    print(json.dumps(dict(species=row['species'], mode=mode, status=report['status'],
        operations=len(report['operations']), exits=len(report['exits']), issues=report['issues'][:3])), flush=True)
    return report


def run_campaign(config, jobs, names=None, exits=False, record=False):
    validate_config(config)
    selected = {row['base']: dict(row, species=row['base'], form=1 if row['form'] else 0)
                for row in config['catalog'] if not names or row['base'] in names}
    tasks, results = [], []
    for row in selected.values():
        path = Path(config['output']) / 'runs/selected' / row['base'] / 'result.json'
        if path.exists():
            prior = json.loads(path.read_text())
            if any(prior[k] != v for k, v in config['hashes'].items()):
                raise AssertionError('Selected reference belongs to a different link')
            results.append(prior)
        else:
            tasks.append((config, row, 'selected', False, record and row['base'] in
                          ('dusknoir', 'metagross', 'exeggcute', 'eevee')))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for future in as_completed([pool.submit(run_species, task) for task in tasks]):
            results.append(future.result())
    failed = [r for r in results if r['status'] != 'pass']
    write(Path(config['output']) / 'selected-summary.json', results)
    if failed:
        raise AssertionError('Ordinary Selected reference failed; inspect selected-summary.json')
    rows = [row for row in config['catalog'] if not names or row['base'] in names]
    tasks = [(config, row, 'registration', exits, record and row['species'] in
             ('dusknoir', 'metagross', 'exeggcute', 'eevee')) for row in rows]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for future in as_completed([pool.submit(run_species, task) for task in tasks]):
            results.append(future.result())
    validate_config(config)
    write(Path(config['output']) / ('exits-campaign.json' if exits else 'campaign.json'), results)
    return results


def stress_species(task):
    config, row, phase, family, record = task
    if family in ('early-b', 'early-end'):
        return early_exit_stress(task)
    repo, compiler, info, moves = content(json.dumps(config, sort_keys=True))
    folder = Path(config['output']) / 'stress' / row['species'] / f'{family}-q{phase}'
    folder.mkdir(parents=True, exist_ok=False)
    driver = Driver(config['core'], config['rom'], menu.BOOT, config['battery'], folder / 'native.log')
    report = dict(species=row['species'], family=family, input_phase_t=phase,
                  issues=[], anchors=[], **config['hashes'])
    try:
        driver.command(f'crytrace {folder / "cry.jsonl"}')
        if record:
            driver.command(f'perfaudio {folder / "audio.pcm"}')
            driver.command(f'perfimages {folder / "frame"}')
        original = enter(driver, repo, config, row, 'registration')
        run(driver, phase / FRAME)
        def anchor(action):
            state = driver.command('peek')
            report['anchors'].append(dict(action=action, t=state['t'],
                ms=state['t'] * 1000 / HZ, display_frames=state['t'] / FRAME,
                playback=state['playback'], audio=state['audio']))
        if family == 'rapid-tabs':
            for view in (1, 2, 0, 2, 1, 0):
                cursor(driver, view); anchor(f'request-view{view}'); tap(driver, 'a')
            ready(driver, 0, 0)
        elif family == 'rapid-info':
            cursor(driver, 1)
            for _ in range(16):
                anchor('Info-A'); tap(driver, 'a', 1, 1)
            ready(driver, 1)
        elif family == 'held-a':
            anchor('hold-A-120'); run(driver, 120, 'a'); run(driver, 4)
            ready(driver, 0, 1)
        elif family == 'directions':
            for key in ('up', 'down', 'up', 'down', 'right', 'left'):
                anchor('hold-' + key); run(driver, 20, key); run(driver, 2)
            if number(driver, repo, 'wPrevDexEntry', 2) != row['index']:
                report['issues'].append('direction_changed_fixed_species')
        elif family in ('finish-boundary', 'after-finish'):
            cursor(driver, 1)
            first = next((e for e in driver.events if e['event'] == 'publish'), None)
            if first is None:
                for _ in range(60):
                    run(driver)
                    first = next((e for e in driver.events if e['event'] == 'publish'), None)
                    if first:
                        break
            if not first:
                raise AssertionError('No first animation publication')
            target = first['t'] + (row['authored_frames'] + (-1 if family == 'finish-boundary' else 4)) * FRAME
            run(driver, max(0, target - driver.command('peek')['t']) / FRAME)
            anchor(family + '-Info'); tap(driver, 'a'); ready(driver, 1, 0)
            cursor(driver, 2); anchor(family + '-Mov'); tap(driver, 'a'); ready(driver, 2, 0)
        else:
            raise ValueError(family)
        final_ui = driver.command('ui')
        view = final_ui['view']
        page = final_ui[('page', 'info_page', 'moves_page')[view]]
        report['issues'] += semantic(driver, repo, compiler, info, moves, row, view, page)
        finish_playback(driver)
        report['issues'] += playback_audit(repo.load([row['species']])[0], driver.events)
        # Read-only browsing cannot discover moves or update ordinary bookmarks.
        now = preserved(driver, repo)
        for name in ('wMoveDiscoverySeen', 'wLastDexMode', 'wLastDexPresentation',
                     'wLastMovesDexSort', 'wMovesDexBookmarkTag', 'wPokemonDexBookmarkTag'):
            if now.get(name) != original.get(name):
                report['issues'].append('browsing_changed_' + name)
        if record:
            driver.command(f'image {folder / "final.ppm"}')
    except Exception as error:
        report['issues'].append(f'{type(error).__name__}: {error}')
        report['traceback'] = traceback.format_exc()
    finally:
        driver.command('perfimages -'); driver.command('perfaudio -'); driver.command('crystop')
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e) + '\n' for e in driver.events))
        driver.close()
    pcm = folder / 'audio.pcm'
    if pcm.exists():
        with wave.open(str(folder / 'audio.wav'), 'wb') as wav:
            wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
            wav.writeframes(pcm.read_bytes())
    if record:
        save_pngs(folder)
    report['status'] = 'fail' if report['issues'] else 'pass'
    write(folder / 'result.json', report)
    if report['issues']:
        print(json.dumps(dict(species=row['species'], family=family, phase=phase,
            status=report['status'], issues=report['issues'][:2])), flush=True)
    return report


def early_exit_stress(task):
    config, row, phase, family, record = task
    repo, _, _, _ = content(json.dumps(config, sort_keys=True))
    folder = Path(config['output']) / 'stress' / row['species'] / f'{family}-q{phase}'
    folder.mkdir(parents=True, exist_ok=False)
    driver = Driver(config['core'], config['rom'], menu.BOOT, config['battery'], folder / 'native.log')
    report = dict(species=row['species'], family=family, input_phase_t=phase,
                  issues=[], **config['hashes'])
    try:
        driver.command(f'interactive_refs {config["references"][row["species"]]["path"]}')
        driver.command(f'load {config["fixtures"][row["species"]]["path"]}')
        driver.command('rawcolor'); driver.command('perf 1'); driver.command('audit 1')
        driver.command(f'crytrace {folder / "cry.jsonl"}')
        original = preserved(driver, repo)
        if family == 'early-end':
            state = menu.run(driver, repo, config['labels']['loop'], 600)
            if not menu.at(state, repo, config['labels']['loop']):
                raise AssertionError('Early End did not reach registration loop')
            run(driver, 1)
            cursor(driver, 3)
        run(driver, phase / FRAME)
        report['before_exit'] = driver.command('peek')
        state = menu.run(driver, repo, config['labels']['returned'], 600,
                         KEY['b' if family == 'early-b' else 'a'])
        if not menu.at(state, repo, config['labels']['returned']):
            raise AssertionError(f'Early exit did not return: {state}')
        after = preserved(driver, repo)
        report['issues'] += ['return_changed_' + name for name, value in original.items() if after[name] != value]
        leave = next((e for e in driver.events if e['event'] == 'interactive_phase' and e['point'] == 'leave'), None)
        if not leave:
            raise AssertionError('Early exit did not execute local Leave')
        active = [e for e in driver.events if e['t'] <= leave['t']]
        report['issues'] += playback_audit(repo.load([row['species']])[0], active, complete=False)
        run(driver, 8)
        returned = [e for e in driver.events if e['event'] == 'interactive_phase' and e['point'] == 'returned']
        if len(returned) != 1:
            report['issues'].append('continuation_return_count')
    except Exception as error:
        report['issues'].append(f'{type(error).__name__}: {error}')
        report['traceback'] = traceback.format_exc()
    finally:
        driver.command('crystop')
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e) + '\n' for e in driver.events))
        driver.close()
    report['status'] = 'fail' if report['issues'] else 'pass'
    write(folder / 'result.json', report)
    if report['issues']:
        print(json.dumps(dict(species=row['species'], family=family, phase=phase,
            status=report['status'], issues=report['issues'][:2])), flush=True)
    return report


def stress(config, jobs, names=None, record=False):
    validate_config(config)
    rows = [row for row in config['catalog'] if not names or row['base'] in names]
    tasks = [(config, row, phase, family, record and phase == 0 and family == 'rapid-tabs'
              and row['species'] in ('dusknoir', 'exeggcute', 'metagross', 'eevee'))
        for row in rows for phase in (0, FRAME // 4, FRAME // 2, 3 * FRAME // 4)
        for family in STRESS_FAMILIES]
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for future in as_completed([pool.submit(stress_species, task) for task in tasks]):
            results.append(future.result())
            if len(results) % 100 == 0 or len(results) == len(tasks):
                print(json.dumps(dict(stress_done=len(results), total=len(tasks),
                    failures=sum(bool(r['issues']) for r in results))), flush=True)
    validate_config(config)
    write(Path(config['output']) / 'stress.json', results)
    return results


def timing_comparison(config, reports):
    pairs = {}
    for report in reports:
        if report['species'] in REPRESENTATIVE:
            pairs.setdefault(report['species'], {})[report['mode']] = report
    if set(pairs) != set(REPRESENTATIVE):
        raise ValueError(f'Timing representatives missing: {set(REPRESENTATIVE) - set(pairs)}')
    rows = []
    for species, pair in pairs.items():
        if set(pair) != {'selected', 'registration'}:
            raise ValueError(f'Incomplete paired timing: {species}')
        baseline = {op['name']: op for op in pair['selected']['operations']}
        for operation in pair['registration']['operations']:
            other = baseline[operation['name']]
            values = {}
            for key in ('request_to_published', 'request_to_displayed', 'input_to_displayed'):
                a, b = other[key], operation[key]
                values[key] = dict(selected=a, registration=b,
                    delta_ms=b['ms'] - a['ms'] if a and b else None,
                    delta_display_frames=b['display_frames'] - a['display_frames'] if a and b else None)
            rows.append(dict(species=species, operation=operation['name'],
                             view=operation['view'], page=operation['page'],
                             group=operation_group(operation),
                             pixel_parity=operation['pixel_parity'], **values))
    summary = {}
    for key in ('request_to_published', 'request_to_displayed', 'input_to_displayed'):
        deltas = [row[key]['delta_ms'] for row in rows if row[key]['delta_ms'] is not None]
        summary[key] = dict(paired_operations=len(deltas),
            median_delta_ms=statistics.median(deltas) if deltas else None,
            maximum_delta_ms=max(deltas) if deltas else None,
            median_delta_display_frames=statistics.median(deltas) * HZ / 1000 / FRAME if deltas else None,
            maximum_delta_display_frames=max(deltas) * HZ / 1000 / FRAME if deltas else None)
    report = dict(**config['hashes'], final_link=config['final_link'],
        representatives=list(REPRESENTATIVE), species=len(pairs), operations=len(rows),
        units='elapsed physical display time at 4194304 T-cycles/s; 70224 T-cycles/display frame',
        automated=True, listening_approval=False, visual_approval=False,
        latency_slack_frames=config.get('latency_slack_frames', 2),
        summary=summary, rows=rows)
    write(Path(config['output']) / 'timing-comparison.json', report)
    timing_tables(config, reports, rows)
    return report


def operation_group(operation):
    names = ('Desc', 'Info', 'Mov')
    if 'source' in operation:
        return names[operation['source']] + ' -> ' + names[operation['view']]
    if operation['name'] == 'view1-page0':
        return 'Desc -> Info'
    if operation['name'] == 'view2-page0':
        return 'Info -> Mov'
    return names[operation['view']] + ' page/wrap'


def metric_stats(rows, metric):
    values = [r[metric] for r in rows]
    valid = [v for v in values if v['selected'] is not None and v['registration'] is not None]
    result = dict(operations=len(rows), complete_pairs=len(valid))
    for key in ('selected', 'registration'):
        ms = [v[key]['ms'] for v in valid]
        result[key] = dict(median_ms=statistics.median(ms) if ms else None,
                           maximum_ms=max(ms) if ms else None)
        result[key].update({k.replace('_ms', '_display_frames'): v * HZ / 1000 / FRAME
                            for k, v in list(result[key].items()) if v is not None})
    deltas = [v['delta_ms'] for v in valid]
    result['delta'] = dict(median_ms=statistics.median(deltas) if deltas else None,
                           maximum_ms=max(deltas) if deltas else None)
    result['delta'].update({k.replace('_ms', '_display_frames'): v * HZ / 1000 / FRAME
                           for k, v in list(result['delta'].items()) if v is not None})
    slowest = max(rows, key=lambda r: r[metric]['delta_ms'] if r[metric]['delta_ms'] is not None else -float('inf'))
    result['maximum_delta_case'] = {k: slowest[k] for k in ('species', 'operation')}
    return result


def timing_tables(config, reports, representative_rows):
    out = Path(config['output'])
    metrics = ('request_to_published', 'request_to_displayed', 'input_to_displayed')
    pairs = {}
    bases = {r['base'] for r in config['catalog']}
    for report in reports:
        if report['species'] in bases:
            pairs.setdefault(report['species'], {})[report['mode']] = report
    all_rows = []
    checks = dict(operations=0, missing_acceptance=0, missing_publication=0,
                  missing_completion=0, wrong_order=0, negative_intervals=0, pixel_parity_failures=0)
    for report in reports:
        for op in report['operations']:
            checks['operations'] += 1
            checks['missing_acceptance'] += op.get('accepted_t') is None
            checks['missing_publication'] += op.get('published_t') is None
            checks['missing_completion'] += op.get('complete_visible_t') is None
            times = [op.get(k) for k in ('pressed_t', 'accepted_t', 'published_t', 'complete_visible_t')]
            if all(t is not None for t in times):
                checks['wrong_order'] += not (times[0] <= times[1] <= times[2] < times[3])
            checks['negative_intervals'] += sum(op.get(k) is not None and op[k]['t_cycles'] < 0
                                               for k in metrics)
            checks['pixel_parity_failures'] += not op.get('pixel_parity', False)
    for species, pair in sorted(pairs.items()):
        if set(pair) != {'selected', 'registration'}:
            continue
        baseline = {o['name']: o for o in pair['selected']['operations']}
        for op in pair['registration']['operations']:
            values = {}
            for metric in metrics:
                a, b = baseline[op['name']][metric], op[metric]
                values[metric] = dict(selected=a, registration=b,
                    delta_ms=b['ms'] - a['ms'] if a and b else None,
                    delta_display_frames=b['display_frames'] - a['display_frames'] if a and b else None)
            all_rows.append(dict(species=species, operation=op['name'], group=operation_group(op), **values))
    grouped = []
    for scope, rows in (('20 representatives', representative_rows), (f'{len(pairs)} base species', all_rows)):
        for group in sorted({r['group'] for r in rows}):
            selected = [r for r in rows if r['group'] == group]
            grouped.append(dict(scope=scope, group=group,
                                **{m: metric_stats(selected, m) for m in metrics}))
    species_rows = [dict(species=name,
        **{m: metric_stats([r for r in representative_rows if r['species'] == name], m) for m in metrics})
        for name in REPRESENTATIVE]
    alerts = [dict(species=r['species'], operation=r['operation'],
                  **{m: r[m] for m in metrics}) for r in all_rows
              if any(r[m]['delta_display_frames'] is not None and
                     r[m]['delta_display_frames'] > config.get('latency_slack_frames', 2)
                     for m in ('request_to_published', 'request_to_displayed'))]
    checks['pass'] = not any(v for k, v in checks.items() if k not in ('operations', 'pass'))
    report = dict(**config['hashes'], grouped=grouped, per_species=species_rows,
        displayed_completion_checks=checks, alerts=alerts,
        alert_threshold_display_frames=config.get('latency_slack_frames', 2),
        publication_marker='Lower-assets ACK; complete displayed scanout is a separate, freshly qualified measurement',
        delta_policy='Registration minus ordinary Selected. Median of paired deltas, not difference of medians.',
        timing_policy='Physical 4194304 T-cycles/s and 70224 T-cycles/display frame; display must follow accepted request and its fresh publication',
        paired_base_species=len(pairs), paired_base_operations=len(all_rows))
    write(out / 'timing-tables.json', report)
    csv_rows = []
    for category, rows in (('tab group', grouped), ('species', species_rows)):
        for row in rows:
            for metric in metrics:
                stats = row[metric]
                csv_rows.append(dict(category=category, scope=row.get('scope', '20 representatives'),
                    name=row.get('species', row.get('group')), metric=metric, operations=stats['operations'],
                    **{side + '_' + key: value for side in ('selected', 'registration', 'delta')
                       for key, value in stats[side].items()},
                    maximum_delta_species=stats['maximum_delta_case']['species'],
                    maximum_delta_operation=stats['maximum_delta_case']['operation']))
    with (out / 'timing-tables.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    lines = ['# Corrected Registration Timing', '',
             'Delta is registration minus ordinary Selected; values are milliseconds / physical display frames.',
             'A matching display counts only after the accepted request and its fresh publication. Publication is the lower-assets ACK, not completed scanout.', '',
             '## Tab Groups', '',
             '| Scope | Operation | N | Publication delta median / max (ms) | Display delta median / max (ms) | Display delta median / max (frames) |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in grouped:
        pub, display = (row[m]['delta'] for m in metrics[:2])
        lines.append(f'| {row["scope"]} | {row["group"]} | {row[metrics[0]]["operations"]} | '
            f'{pub["median_ms"]:.3f} / {pub["maximum_ms"]:.3f} | '
            f'{display["median_ms"]:.3f} / {display["maximum_ms"]:.3f} | '
            f'{display["median_display_frames"]:.3f} / {display["maximum_display_frames"]:.3f} |')
    lines += ['', '## Twenty Species', '',
              '| Species | N | Publication delta median / max (ms) | Display delta median / max (ms) | Display delta median / max (frames) | Slowest display operation |',
              '| --- | ---: | ---: | ---: | ---: | --- |']
    for row in species_rows:
        pub, display = (row[m]['delta'] for m in metrics[:2])
        lines.append(f'| {row["species"]} | {row[metrics[0]]["operations"]} | '
            f'{pub["median_ms"]:.3f} / {pub["maximum_ms"]:.3f} | '
            f'{display["median_ms"]:.3f} / {display["maximum_ms"]:.3f} | '
            f'{display["median_display_frames"]:.3f} / {display["maximum_display_frames"]:.3f} | '
            f'{row[metrics[1]]["maximum_delta_case"]["operation"]} |')
    lines += ['', f'Fresh completion checks: {checks["operations"]} operations; '
              f'{checks["negative_intervals"]} negative intervals; {checks["missing_completion"]} missing completions; '
              f'{checks["wrong_order"]} ordering violations.', '',
              f'{len(alerts)} full-catalog operation alerts exceed the unchanged two-display-frame paired warning threshold. See latency-alert-analysis.json for causal replay evidence.']
    (out / 'timing-tables.md').write_text('\n'.join(lines) + '\n')
    return report


def retime(config):
    validate_config(config)
    out = Path(config['output'])
    changed, absent, negative_before, negative_after = 0, [], 0, 0
    reports = []
    for mode in ('selected', 'registration'):
        for path in sorted((out / 'runs' / mode).glob('*/result.json')):
            report = json.loads(path.read_text())
            with gzip.open(path.parent / 'events.jsonl.gz', 'rt') as stream:
                events = [json.loads(line) for line in stream]
            if mode == 'selected':
                references = report['references']
            else:
                base = next(r['base'] for r in config['catalog'] if r['species'] == report['species'])
                references = json.loads((out / 'runs/selected' / base / 'result.json').read_text())['references']
            for n, operation in enumerate(report['operations']):
                old = operation.get('request_to_displayed')
                negative_before += bool(old and old['t_cycles'] < 0)
                end = report['operations'][n + 1]['pressed_t'] if n + 1 < len(report['operations']) else float('inf')
                window = [e for e in events if operation['pressed_t'] <= e['t'] < end]
                measured = timing(window, operation['pressed_t'], operation['view'], operation['page'],
                                  references[f'{operation["view"]}-{operation["page"]}'])
                if not measured['request_to_displayed']:
                    absent.append(dict(mode=mode, species=report['species'], operation=operation['name']))
                if measured['pixel_signature']:
                    measured['pixel_signature'].update({k: v for k, v in operation['pixel_signature'].items() if k.endswith('_sha256')})
                operation.update(measured)
                new = operation.get('request_to_displayed')
                negative_after += bool(new and new['t_cycles'] < 0)
                changed += old != new
            report['timing_revision'] = 2
            report['visible_completion_policy'] = 'Matching displayed frame strictly after this request acceptance and its fresh publication'
            write(path, report)
            reports.append(report)
    write(out / 'campaign.json', reports)
    prior_path = out / 'timing-revision.json'
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    write(prior_path, dict(revision=2, changed_operations=changed,
        negative_before=negative_before, negative_after=negative_after, missing_completions=absent,
        stale_negative_corrected_total=prior.get('stale_negative_corrected_total', prior.get('negative_before', 0)) + negative_before,
        source='Retained native instruction/display traces from unchanged final ROM'))
    comparison = timing_comparison(config, reports)
    print(json.dumps(dict(retimed=changed, negative_before=negative_before,
                         negative_after=negative_after, missing=len(absent), summary=comparison['summary'])), flush=True)
    if absent or negative_after:
        raise AssertionError('Corrected visible qualification is incomplete')
    return reports


def latency_case(task):
    config, row, mode, operation_name, policy, phase = task
    repo, _, _, _ = content(json.dumps(config, sort_keys=True))
    folder = Path(config['output']) / config.get('latency_probe_root', 'latency-probes') / row['species'] / f'{operation_name}-{mode}-{policy}-q{phase}'
    folder.mkdir(parents=True, exist_ok=False)
    driver = Driver(config['core'], config['rom'], menu.BOOT,
                    config['battery' if mode == 'registration' else 'selected_battery'], folder / 'native.log')
    result = dict(species=row['species'], mode=mode, operation=operation_name,
                  policy=policy, phase_t=phase, issues=[], **config['hashes'])
    try:
        driver.command(f'crytrace {folder / "cry.jsonl"}')
        enter(driver, repo, config, row, mode)
        reference = json.loads((Path(config['output']) / 'runs/selected' / row['base'] / 'result.json').read_text())['references']
        first_display = next(e for e in driver.events if e['event'] == 'interactive_frame' and
            frame_matches(e, 0, 0) and all(e[k] == reference['0-0'][k] for k in ('upper', 'panel')))
        entry = next(e for e in driver.events if e['event'] == 'interactive_phase' and
                     e['point'] == ('entry' if mode == 'registration' else 'selected_entry'))
        if mode == 'registration':
            loop = next(e for e in driver.events if e['event'] == 'interactive_phase' and e['point'] == 'input')
        else:
            loop = next(e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'selected_loop')
        def interval(t):
            return dict(t_cycles=t, ms=t * 1000 / HZ, display_frames=t / FRAME)
        result['entry_metrics'] = dict(entry_t=entry['t'], first_complete_display_t=first_display['t'],
            first_input_dispatch_t=loop['t'],
            entry_to_complete_display=interval(first_display['t'] - entry['t']),
            entry_to_input_dispatch=interval(loop['t'] - entry['t']),
            visible_unresponsive_interval=interval(max(0, loop['t'] - first_display['t'])))
        for operation in operations(row):
            if 'source' in operation and driver.command('ui')['view'] != operation['source']:
                cursor(driver, operation['source']); tap(driver, 'a'); ready(driver, operation['source'], 0)
            view, page = operation['view'], operation['page']
            cursor(driver, view)
            target = operation['name'] == operation_name
            if target and policy == 'settled':
                finish_playback(driver)
            if target and phase:
                run(driver, phase / FRAME)
            pressed = driver.command('peek')['t']
            before = driver.command('peek')
            start = len(driver.events)
            tap(driver, 'a'); ready(driver, view, page)
            if target:
                window = driver.events[start:]
                measured = timing(window, pressed, view, page, reference[f'{view}-{page}'])
                result.update(measured, before=before)
                accepted = next(e for e in window if e['event'] == 'interactive_phase' and
                                e['point'] == ('desc_request', 'info_request', 'moves_request')[view])
                pub = measured['published_t']
                slices = [e for e in window if e['event'] == 'info_slice' and accepted['t'] <= e['t'] <= pub]
                costs = {}
                for event in window:
                    if event['event'] == 'perf_cost' and accepted['t'] <= event['t'] <= pub:
                        costs.setdefault(event['name'], []).append(event['elapsed'])
                result.update(request_snapshot=accepted, slices=slices,
                    costs={name: dict(calls=len(values), total_t=sum(values), maximum_t=max(values))
                           for name, values in costs.items()})
                if not measured['pixel_parity']:
                    result['issues'].append('fresh_display_not_observed')
                break
        else:
            raise AssertionError('Probe operation absent')
    except Exception as error:
        result['issues'].append(f'{type(error).__name__}: {error}')
        result['traceback'] = traceback.format_exc()
    finally:
        driver.command('crystop')
        with gzip.open(folder / 'events.jsonl.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(e) + '\n' for e in driver.events))
        driver.close()
    write(folder / 'result.json', result)
    return result


def latency_targets(config):
    table = json.loads((Path(config['output']) / 'timing-tables.json').read_text())
    return sorted({(row['species'], row['operation']) for row in table['alerts']})


def latency_probes(config, jobs, detailed=False):
    validate_config(config)
    controls = (('primeape', 'view1-wrap'), ('tyrogue', 'view1-page2'),
                ('beldum', 'tab-0-1'), ('toxicroak', 'tab-0-1'))
    controls = tuple(sorted(set(controls) | set(latency_targets(config))))
    catalog_by_name = {r['species']: r for r in config['catalog']}
    repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
    labels, _ = labels_for(repo)
    labels['selected_entry'] = 'PokedexSelectedMon_Enter'
    probe_root = 'latency-probes-detail' if detailed else 'latency-probes'
    if detailed:
        labels.update(info_admit='PokedexPerf_AdmitInfo',
            info_admit_clock='PokedexPerf_AdmitInfo.clock',
            info_admit_reject='PokedexPerf_AdmitInfo.reject',
            info_ready='PokedexInfo_Service.publish',
            info_gate='Pokedex_VBlankInfo.active',
            lower_transaction_done='Pokedex_VBlankInfo.done')
        controls += (('dusknoir', 'view1-page0'),)
    core = compile_observer(repo, Path(config['output']) / probe_root / 'observer', labels)
    diagnostic = dict(config, core=str(core), latency_probe_root=probe_root)
    tasks = [(diagnostic, catalog_by_name[name], mode, operation, policy, phase)
        for name, operation in controls for mode in ('selected', 'registration')
        for policy in ('continuous', 'settled') for phase in (0, FRAME // 4, FRAME // 2, 3 * FRAME // 4)]
    results, pending = [], []
    for task in tasks:
        _, row, mode, operation, policy, phase = task
        path = Path(config['output']) / probe_root / row['species'] / f'{operation}-{mode}-{policy}-q{phase}' / 'result.json'
        if path.exists():
            prior = json.loads(path.read_text())
            if prior['issues'] or any(prior.get(k) != v for k, v in config['hashes'].items()):
                raise AssertionError('Do not reuse failed or mismatched latency evidence: ' + str(path))
            results.append(prior)
        else:
            pending.append(task)
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for future in as_completed([pool.submit(latency_case, task) for task in pending]):
            results.append(future.result())
    write(Path(config['output']) / (probe_root + '.json'), dict(**config['hashes'],
          cases=len(results), failures=sum(bool(r['issues']) for r in results), results=results))
    print(json.dumps(dict(latency_probes=len(results), failures=sum(bool(r['issues']) for r in results))), flush=True)
    return results


def latency_analysis(config):
    out = Path(config['output'])
    repo = Repository(Path(config['root']), Path(config['rom']), Path(config['sym']))
    ready_cutoff = repo.rom[offset(repo.symbols['PokedexPerf_InfoLatestLY']) + 5]
    active = offset(repo.symbols['Pokedex_VBlankInfo.active'])
    gate = repo.rom[active:active+64]
    clock = gate.find(b'\xf0\x44\xfe\x90\x38')
    if clock < 0 or gate[clock+6] != 0xfe:
        raise AssertionError('Lower-publication LY guard changed; update diagnostic decoder')
    publication_cutoff = gate[clock+7]
    probe = json.loads((out / 'latency-probes-detail.json').read_text())
    result = dict(**config['hashes'], alerts=[], probe_cases=probe['cases'],
        probe_failures=probe['failures'], responsiveness_approval=False,
        publication_marker='Existing lower-assets ACK; first complete displayed frame is qualified separately after that fresh transaction',
        delta_source='Original continuous catalog scan, not diagnostic replays. delta_ms and delta_display_frames alias original request_to_displayed deltas.',
        conclusion='Real active-playback phase-dependent latency, not duplicated content work. Shared admission gates preserve portrait/audio deadlines; alerts remain visible for responsiveness review.')
    catalog = {row['species']: row for row in config['catalog']}
    for name, operation in latency_targets(config):
        alert = dict(species=name, operation=operation, original={}, phase_probes={}, gates={})
        for mode in ('selected', 'registration'):
            species = name if mode == 'registration' else catalog[name]['base']
            report = json.loads((out / 'runs' / mode / species / 'result.json').read_text())
            op = next(o for o in report['operations'] if o['name'] == operation)
            alert['original'][mode] = {k: op[k] for k in ('request_to_published', 'request_to_displayed')}
            for policy in ('continuous', 'settled'):
                rows = sorted([r for r in probe['results'] if r['species'] == name and r['operation'] == operation and r['mode'] == mode
                               and r['policy'] == policy], key=lambda r: r['phase_t'])
                alert['phase_probes'][mode + '-' + policy] = [dict(phase_t=r['phase_t'],
                    published=r['request_to_published'], displayed=r['request_to_displayed'],
                    playback_at_input=r['before']['playback'], slices=len(r['slices']),
                    admitted_slice_elapsed_t=sum(e['elapsed'] for e in r['slices'])) for r in rows]
            row = next(r for r in probe['results'] if r['species'] == name and r['operation'] == operation and r['mode'] == mode
                       and r['policy'] == 'continuous' and r['phase_t'] == 0)
            folder = out / 'latency-probes-detail' / name / f'{operation}-{mode}-continuous-q0'
            with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
                events = [json.loads(line) for line in stream]
            gates = [e for e in events if e['event'] == 'interactive_phase' and
                row['accepted_t'] <= e['t'] <= row['published_t'] and
                ((e['point'] == 'info_admit_clock' and e['info_state'] == 5) or
                 e['point'] == 'info_ready' or (e['point'] == 'info_gate' and e['transition'] == 5))]
            alert['gates'][mode] = [dict(point=e['point'], ly=e['ly'],
                after_request_frames=(e['t'] - row['accepted_t']) / FRAME,
                scheduler=e['scheduler'], info_state=e['info_state'], transition=e['transition']) for e in gates]
        alert['original_scan_deltas'] = {metric: dict(
            ms=alert['original']['registration'][metric]['ms'] - alert['original']['selected'][metric]['ms'],
            display_frames=alert['original']['registration'][metric]['display_frames'] - alert['original']['selected'][metric]['display_frames'])
            for metric in ('request_to_published', 'request_to_displayed')}
        alert['delta_ms'] = alert['original_scan_deltas']['request_to_displayed']['ms']
        alert['delta_display_frames'] = alert['original_scan_deltas']['request_to_displayed']['display_frames']
        alert['diagnostic_probe_deltas'] = [dict(policy=policy, phase_t=phase,
            **{metric: dict(ms=b[metric]['ms'] - a[metric]['ms'],
                           display_frames=b[metric]['display_frames'] - a[metric]['display_frames'])
               for metric in ('request_to_published', 'request_to_displayed')})
            for policy in ('continuous', 'settled') for phase in (0, FRAME // 4, FRAME // 2, 3 * FRAME // 4)
            for a in probe['results'] if a['species'] == name and a['operation'] == operation and a['mode'] == 'selected'
                and a['policy'] == policy and a['phase_t'] == phase
            for b in probe['results'] if b['species'] == name and b['operation'] == operation and b['mode'] == 'registration'
                and b['policy'] == policy and b['phase_t'] == phase]
        late_stage = any(e['point'] == 'info_admit_clock' and e['ly'] >= ready_cutoff
                         for e in alert['gates']['registration'])
        late_publish = any(e['point'] == 'info_gate' and e['ly'] >= publication_cutoff
                           for e in alert['gates']['registration'])
        alert['cause'] = ('READY staging encounters late foreground admission; the pending panel also encounters late VBlank publication admission.'
            if late_stage and late_publish else
            'The pending lower panel encounters late VBlank publication admission.' if late_publish else
            'Lower-panel producer/staging phase differs; see recorded admission and publication LY traces.')
        alert['late_stage_observed'] = late_stage
        alert['late_publication_observed'] = late_publish
        alert['linked_admission_cutoffs'] = dict(ready=ready_cutoff, publication=publication_cutoff)
        result['alerts'].append(alert)
    result['entry_metrics'] = {mode: next(r['entry_metrics'] for r in probe['results']
        if r['species'] == 'dusknoir' and r['mode'] == mode and r['policy'] == 'continuous' and r['phase_t'] == 0)
        for mode in ('selected', 'registration')}
    for mode, metrics in result['entry_metrics'].items():
        folder = out / 'latency-probes-detail/dusknoir' / f'view1-page0-{mode}-continuous-q0'
        with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
            events = [json.loads(line) for line in stream]
        begin = next(e for e in events if e['event'] == 'interactive_phase' and e['point'] == 'begin')
        loop = next(e for e in events if
                    (e['event'] == 'interactive_phase' and e['point'] == 'loop') or
                    (mode == 'selected' and e['event'] == 'perf_phase' and e['name'] == 'selected_loop'))
        reveal = next(e for e in events if
                      (mode == 'registration' and e['event'] == 'interactive_phase' and e['point'] == 'reveal') or
                      (mode == 'selected' and e['event'] == 'reveal'))
        def interval(t):
            return dict(t_cycles=t, ms=t * 1000 / HZ, display_frames=t / FRAME)
        metrics.update(prepared_animation_begin_t=begin['t'], first_controller_loop_t=loop['t'],
            reveal_observer_t=reveal['t'],
            reveal_observer='Before PokedexSelectedMon_Reveal call' if mode == 'registration' else 'PokedexSelectedMon_Enter.revealed, after reveal call',
            entry_to_controller_loop=interval(loop['t'] - metrics['entry_t']),
            prepared_animation_begin_to_input=interval(metrics['first_input_dispatch_t'] - begin['t']),
            reveal_observer_to_input=interval(metrics['first_input_dispatch_t'] - reveal['t']))
    result['entry_context'] = 'Measured routine boundaries on fresh matching-link wild-catch and ordinary Selected fixtures; input dispatch precedes the first complete visible Description on both paths.'
    result['entry_caveat'] = 'Registration has real pre-reveal setup cost. Reveal observers bracket opposite sides of the reveal call and are not directly comparable; use entry-to-display or the shared prepared-animation-begin boundary for matched timing.'
    write(out / 'latency-alert-analysis.json', result)
    return result


def media(config):
    from PIL import Image, ImageDraw, ImageFont
    out = Path(config['output'])
    destination = out / 'manual-review'
    destination.mkdir(exist_ok=True)
    title_path = destination / 'comparison-labels.png'
    title = Image.new('RGB', (960, 44), 'white')
    draw = ImageDraw.Draw(title)
    font_path = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    font = ImageFont.truetype(str(font_path), 16) if font_path.exists() else ImageFont.load_default()
    draw.text((8, 3), 'Regular Selected (candidate)', fill='black', font=font)
    draw.text((488, 3), 'Registration (candidate)', fill='black', font=font)
    small = ImageFont.truetype(str(font_path), 12) if font_path.exists() else ImageFont.load_default()
    draw.text((8, 26), 'Same operation sequence; inputs advance independently when each page is ready',
              fill='black', font=small)
    title.save(title_path)
    result = dict(**config['hashes'], final_link=config['final_link'],
                  visual_approval=False, listening_approval=False, pairs=[])
    for species in ('dusknoir', 'metagross', 'exeggcute', 'eevee'):
        folders = [out / 'runs' / mode / species for mode in ('selected', 'registration')]
        if not all((folder / 'audio.wav').exists() for folder in folders):
            continue
        starts, anchors = [], {}
        for mode, folder in zip(('selected', 'registration'), folders):
            save_pngs(folder)
            report = json.loads((folder / 'result.json').read_text())
            signature = report['references']['0-0']
            with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
                events = [json.loads(line) for line in stream]
            first = next(e for e in events if e['event'] == 'interactive_frame' and
                frame_matches(e, 0, 0) and all(e[k] == signature[k] for k in ('upper', 'panel')))
            starts.append(first['display'])
            displays = [e for e in events if e['event'] == 'perf_frame' and e['display'] >= first['display']]
            periods = [b['boundary_t'] - a['boundary_t'] for a, b in zip(displays, displays[1:])]
            anchors[mode] = dict(first_complete_description_t=first['t'],
                first_video_display=first['display'],
                frame_prefix=str(folder / 'frame'), audio=str(folder / 'audio.wav'),
                video_fps=HZ / FRAME, native_display_period_t=FRAME,
                observed_period_min_t=min(periods) if periods else None,
                observed_period_max_t=max(periods) if periods else None,
                operations=[{k: op.get(k) for k in ('name', 'pressed_t', 'accepted_t',
                    'published_t', 'complete_visible_t')} for op in report['operations']])
        video = destination / f'{species}-selected-v-registration.mp4'
        fps = HZ / FRAME
        filters = []
        for n in range(2):
            filters.append(f'[{n}:v]setpts=PTS-STARTPTS,scale=480:432:flags=neighbor,'
                f'tpad=stop_mode=clone:stop_duration=6[v{n}]')
        filters += ['[v0][v1]hstack=inputs=2,pad=960:476:0:44:color=white[stack]',
                    '[stack][2:v]overlay=0:0[v]']
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
        for folder, start in zip(folders, starts):
            command += ['-framerate', str(fps), '-start_number', str(start),
                        '-i', str(folder / 'frame-%03d.ppm')]
        command += ['-loop', '1', '-framerate', str(fps), '-i', str(title_path),
                    '-filter_complex', ';'.join(filters), '-map', '[v]', '-t', '6',
                    '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        result['pairs'].append(dict(species=species, video=str(video),
            audio_policy='Separate unmodified stereo WAV recordings; video is silent',
            alignment='Each side begins at its first complete Description display; matching operation sequence advances independently as each page is ready, not identical wall-clock key times',
            anchors=anchors))
    write(destination / 'evidence.json', result)
    print(json.dumps(dict(manual_review=str(destination), pairs=len(result['pairs']))), flush=True)
    return result


def coverage_plan(rows):
    return dict(base_species=len({r['base'] for r in rows}), species_and_forms=len(rows),
        description_pages=len(rows) * 2,
        info_pages=sum(r['info_pages'] for r in rows),
        moves_pages=sum(r['moves_pages'] for r in rows),
        directed_tab_pairs=len(rows) * 6,
        page_and_tab_requests=sum(len(operations(r)) for r in rows),
        committed_B_End_exits=2 * sum(2 + r['info_pages'] + r['moves_pages'] for r in rows),
        pending_exit_policy='B and End on each observed queued-page checkpoint; baseline pending_at_input is sampled before physical button signal, not at dispatch. Supplemental probe records actual leave-boundary state.',
        input_stress_cases=len(rows) * 4 * len(STRESS_FAMILIES),
        phases_t=[0, FRAME // 4, FRAME // 2, 3 * FRAME // 4],
        stress_families=list(STRESS_FAMILIES),
        excluded_assets=['egg (not a registered species)'],
        caller_scope='Generated fixed-species registration contexts; authentic capture/prize continuations are the separate Gotcha suite')


def negative_controls(config):
    validate_config(config)
    out = Path(config['output'])
    repo, _, _, _ = content(json.dumps(config, sort_keys=True))
    folder = out / 'negative-controls'
    folder.mkdir(exist_ok=True)
    source = out / 'runs/registration/dusknoir/events.jsonl.gz'
    with gzip.open(source, 'rt') as stream:
        original = [json.loads(line) for line in stream]
    asset = repo.load(['dusknoir'])[0]
    baseline = playback_audit(asset, original)
    if baseline:
        raise AssertionError(f'Negative-control baseline is not clean: {baseline}')
    results = []
    def rejected(name, changed):
        issues = playback_audit(asset, changed)
        results.append(dict(name=name, rejected=bool(issues), detected=issues))
    changed = copy.deepcopy(original)
    changed.remove(next(e for e in changed if e['event'] == 'publish'))
    rejected('missing_animation_publication', changed)
    changed = copy.deepcopy(original)
    event = next(e for e in changed if e['event'] == 'publish')
    event['picture'] = ('00' if event['picture'][:2] != '00' else '01') + event['picture'][2:]
    rejected('wrong_published_picture', changed)
    changed = copy.deepcopy(original)
    publications = [e for e in changed if e['event'] == 'publish']
    publications[1]['t'] += FRAME
    rejected('one_display_frame_late_publication', changed)
    changed = copy.deepcopy(original)
    first = next(e for e in changed if e['event'] == 'publish')['t']
    next(e for e in changed if e['event'] == 'interactive_pixels' and e['t'] > first)['valid'] = False
    rejected('rendered_only_portrait_corruption', changed)
    changed = copy.deepcopy(original)
    changed.append(dict(event='audio_miss', remaining=1, t=first))
    rejected('sampled_cache_starvation', changed)
    changed = copy.deepcopy(original)
    changed.append(copy.deepcopy(next(e for e in changed if e['event'] == 'perf_phase' and e['name'] == 'sample_start')))
    rejected('cry_restarted_on_tab', changed)
    changed = copy.deepcopy(original)
    changed.remove(next(e for e in changed if e['event'] == 'wave_block'))
    rejected('missing_CH3_wave_block', changed)
    reference = json.loads((out / 'runs/selected/dusknoir/result.json').read_text())['references']['0-1']
    measured = timing(original, 0, 0, 1, dict(reference, upper=-1))
    results.append(dict(name='wrong_complete_panel_pixels', rejected=not measured['pixel_parity']))
    for name, mutate in (
        ('relinked_ROM_manifest', lambda c: c['hashes'].__setitem__('rom_sha256', '0' * 64)),
        ('altered_fixture_manifest', lambda c: c['fixtures']['dusknoir'].__setitem__('sha256', '0' * 64))):
        changed = copy.deepcopy(config)
        mutate(changed)
        try:
            validate_config(changed)
            caught = False
        except ValueError:
            caught = True
        results.append(dict(name=name, rejected=caught))
    factory = out / 'observer/interactive-registration-fixture'
    for name, index, form, donor, code in (
        ('zero_species_fixture', 0, 0, out / 'native-registration.s0', 2),
        ('out_of_catalog_fixture', 374, 0, out / 'native-registration.s0', 2),
        ('invalid_Unown_form_fixture', 201, 27, out / 'native-registration.s0', 2),
        ('wrong_native_boundary_fixture', 1, 0, Path(config['listing_states']) / 'listing-000.s0', 4)):
        destination = folder / (name + '.s0')
        process = subprocess.run([str(factory), config['rom'], str(donor), str(index),
            str(form), str(destination)], capture_output=True, text=True)
        results.append(dict(name=name, rejected=process.returncode == code and not destination.exists(),
                            expected_exit=code, actual_exit=process.returncode))
    stale = [dict(event='interactive_frame', t=100, display=1, view=2, moves_page=0,
                  moves_state=0, transition=0, upper=11, panel=22),
             dict(event='interactive_phase', point='moves_request', t=1000),
             dict(event='interactive_frame', t=1100, display=2, view=2, moves_page=0,
                  moves_state=0, transition=0, upper=11, panel=22),
             dict(event='interactive_phase', point='moves_published', t=2000, display=3,
                  view=2, moves_page=0),
             dict(event='interactive_frame', t=3000, display=4, view=2, moves_page=0,
                  moves_state=0, transition=0, upper=11, panel=22)]
    measured = timing(stale, 0, 2, 0, dict(upper=11, panel=22))
    results.append(dict(name='stale_identical_wrap_frame',
                        rejected=measured['complete_visible_t'] == 3000 and
                                 measured['request_to_displayed']['t_cycles'] == 2000))
    report = dict(**config['hashes'], controls=len(results),
        failures=sum(not r['rejected'] for r in results), results=results,
        policy='Mutated host trace/manifest copies and invalid fixture requests only; no runtime/ROM/save mutations')
    write(out / 'negative-controls.json', report)
    validate_config(config)
    print(json.dumps(dict(negative_controls=report['controls'], failures=report['failures'])), flush=True)
    return report


def summarize(config):
    root = Path(config['output'])
    reports = [json.loads(p.read_text()) for p in (root / 'runs').glob('*/*/result.json')]
    stresses = [json.loads(p.read_text()) for p in (root / 'stress').glob('*/*/result.json')]
    control_path = root / 'negative-controls.json'
    controls = json.loads(control_path.read_text()) if control_path.exists() else None
    pending_path = root / 'pending-exits.json'
    pending_exits_report = json.loads(pending_path.read_text()) if pending_path.exists() else None
    tables_path = root / 'timing-tables.json'
    tables = json.loads(tables_path.read_text()) if tables_path.exists() else None
    failed = [dict(species=r['species'], mode=r.get('mode', r.get('family')), issues=r['issues'])
              for r in reports + stresses if r['issues']]
    failed += [dict(species=r['species'], mode='supplemental-pending-exits', issues=r['issues'])
               for r in (pending_exits_report or {}).get('results', []) if r['issues']]
    reg = [r for r in reports if r.get('mode') == 'registration' and not r.get('exits')]
    selected = [r for r in reports if r.get('mode') == 'selected' and not r.get('exits')]
    exits = [r for r in reports if r.get('exits')]
    actual = dict(registration_species=len(reg),
        selected_species=len(selected), continuous_runs=len(reg) + len(selected),
        continuous_operations=sum(len(r['operations']) for r in reg + selected),
        operations=sum(len(r.get('operations', [])) for r in reg),
        exit_species=len(exits), exits=sum(len(r['exits']) for r in exits),
        pending_B=sum(x['pending_at_input'] and x['exit'] == 'B' for r in exits for x in r['exits']),
        pending_End=sum(x['pending_at_input'] and x['exit'] == 'End' for r in exits for x in r['exits']),
        stress_cases=len(stresses), failures=len(failed))
    pages = {(r['species'], op['view'], op['page']) for r in reg for op in r['operations']}
    actual.update(description_pages=sum(v == 0 for _, v, _ in pages),
        info_pages=sum(v == 1 for _, v, _ in pages), moves_pages=sum(v == 2 for _, v, _ in pages),
        directed_tab_pairs=sum(len({op['name'] for op in r['operations'] if op['name'].startswith('tab-')}) for r in reg))
    committed = set()
    pending = {view: dict(B=0, End=0) for view in range(3)}
    for row in exits:
        for item in row['exits']:
            before = item['before']
            view = before['view']
            if item['state'] == 'committed':
                committed.add((row['species'], view, before[('page', 'info_page', 'moves_page')[view]], item['exit']))
            if item['pending_at_input']:
                pending[view][item['exit']] += 1
    actual.update(unique_committed_B_End_exits=len(committed), pending_at_input_by_view=pending)
    supplementary = pending_exits_report or {}
    actual.update(supplemental_exit_species=supplementary.get('species', 0),
        supplemental_exits=supplementary.get('exits', 0),
        total_exit_replays=actual['exits'] + supplementary.get('exits', 0),
        pending_at_leave_by_view=supplementary.get('pending_at_leave_by_view'))
    expected = coverage_plan(config['catalog'])
    complete = (len(selected) == expected['base_species']
                and len(reg) == len(config['catalog']) and len(exits) == len(config['catalog'])
                and len(stresses) == expected['input_stress_cases'] and controls is not None
                and not controls['failures'] and controls['controls'] == 15
                and len(committed) == expected['committed_B_End_exits']
                and actual['operations'] == expected['page_and_tab_requests']
                and all(actual[k] == expected[k] for k in ('description_pages', 'info_pages', 'moves_pages', 'directed_tab_pairs')))
    result = dict(**config['hashes'], final_link=config['final_link'],
        expected=expected, actual=actual, complete=complete,
        automated_suite_pass=bool(config['final_link'] and complete and not failed
                                  and expected['base_species'] == 373
                                  and expected['species_and_forms'] == 398
                                  and tables and tables['displayed_completion_checks']['pass']
                                  and not supplementary.get('failures', 0)),
        automated_only=True, visual_approval=False, listening_approval=False, failures=failed)
    result['negative_controls'] = controls
    result['responsiveness_alerts'] = [{k: r[k] for k in ('species', 'operation', 'delta_ms', 'delta_display_frames', 'original_scan_deltas', 'cause')}
        for r in json.loads((root / 'latency-alert-analysis.json').read_text())['alerts']] if (root / 'latency-alert-analysis.json').exists() else []
    result['responsiveness_approval'] = False
    result['displayed_completion_checks'] = tables['displayed_completion_checks'] if tables else None
    result['supplemental_pending_exits_complete'] = supplementary.get('species') == len(config['catalog'])
    result['pending_exit_caveat'] = 'Baseline pending_B/pending_End and pending_at_input_by_view sample state before physical signal. Only supplemental pending_at_leave_by_view proves cancellation of live work at dispatch; no equivalence is assumed.'
    result['limitations'] = [
        'Phase-dependent responsiveness alerts remain open for review; automated content/playback success does not approve latency.',
        'Manual visual and listening approval is outstanding.',
        'Videos use the same ready-paced operation sequence, not identical wall-clock key times.',
        'Authentic capture, prize and post-return gameplay continuations belong to the separate caller suite.']
    if supplementary.get('pending_at_leave_by_view'):
        pending_counts = supplementary['pending_at_leave_by_view']
        for view, name in enumerate(('Desc', 'Info', 'Mov')):
            missing = [key for key in ('B', 'End') if not pending_counts[str(view)][key]]
            if missing:
                result['limitations'].append(name + ' pending ' + '/'.join(missing) + ' cancellation was not observed at the leave boundary; work may complete before dispatch, including during footer travel.')
    result['exit_return_timings'] = {}
    for key in ('B', 'End'):
        values = [x['ms'] for r in exits for x in r['exits'] if x['exit'] == key]
        result['exit_return_timings'][key] = dict(cases=len(values), median_ms=statistics.median(values),
            maximum_ms=max(values), median_display_frames=statistics.median(values) * HZ / 1000 / FRAME,
            maximum_display_frames=max(values) * HZ / 1000 / FRAME,
            policy='Physical final button signal to native public return; preceding footer cursor travel excluded')
    validate_config(config)
    write(root / 'summary.json', result)
    print(json.dumps({k: result[k] for k in ('final_link', 'complete', 'automated_suite_pass', 'actual')}), flush=True)
    return result


def finalize(config):
    out = Path(config['output'])
    # Exit checkpoints are independent replay epochs. Their page-validation
    # records are not a continuous-session latency comparison.
    exits = []
    removed = 0
    for path in sorted((out / 'runs/registration-exits').glob('*/result.json')):
        row = json.loads(path.read_text())
        for operation in row['operations']:
            for key in ('pressed_t', 'accepted_t', 'published_t', 'input_to_accept',
                        'request_to_published', 'request_to_displayed', 'input_to_displayed', 'complete_visible_t'):
                if key in operation:
                    del operation[key]
                    removed += 1
        row['timing_policy'] = 'Independent checkpoint epochs; page/exit correctness only. Latency comparisons use the corrected continuous campaign.'
        write(path, row)
        exits.append(row)
    write(out / 'exits-campaign.json', exits)
    continuous = [json.loads(p.read_text()) for mode in ('selected', 'registration')
                  for p in sorted((out / 'runs' / mode).glob('*/result.json'))]
    write(out / 'campaign.json', continuous)
    timing_comparison(config, continuous)
    analysis = latency_analysis(config)
    result = summarize(config)
    result['excluded_exit_replay_timing_fields'] = removed
    write(out / 'summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('smoke', 'inspect', 'plan', 'prepare', 'run',
                                         'timings', 'exits', 'stress', 'all', 'summarize', 'media', 'negative',
                                         'retime', 'latency-probes', 'pending-exits', 'finalize'))
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path, default=SEED)
    parser.add_argument('--sameboy', type=Path, default=SAMEBOY)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--no-forms', action='store_true')
    parser.add_argument('--record', action='store_true')
    parser.add_argument('--detailed', action='store_true')
    parser.add_argument('--final-link', action='store_true',
                        help='Explicitly designate the supplied runtime/data link as final')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if args.action in ('smoke', 'inspect', 'plan', 'prepare', 'all') and not args.candidate:
        parser.error('This action requires --candidate')
    if args.action == 'smoke':
        return smoke(args)
    if args.action in ('inspect', 'plan'):
        repo = Repository(args.candidate, args.candidate / 'pokecrystal.gbc', args.candidate / 'pokecrystal.sym')
        labels, missing = labels_for(repo, require=False)
        result = dict(labels=labels, missing=missing, **repo.hashes)
        if args.action == 'plan':
            rows = catalog(repo, not args.no_forms)
            available = {r['base'] for r in rows}
            if len(REPRESENTATIVE) != 20 or not set(REPRESENTATIVE) <= available:
                raise AssertionError('Twenty representative species must be unique and present')
            result.update(coverage=coverage_plan(rows), representatives=list(REPRESENTATIVE))
        output = args.output.resolve()
        if not output.is_relative_to(ROOT / 'build'):
            raise ValueError('Keep generated observability/coverage reports under build/')
        write(output / 'observability.json', result)
        print(json.dumps(result, indent=2))
        return int(bool(missing))
    if args.action in ('prepare', 'all'):
        config = prepare(args)
        if args.action == 'prepare':
            return 0
    else:
        config = json.loads((args.output / 'config.json').read_text())
        validate_config(config)
    names = args.species
    if args.action == 'media':
        media(config)
        return 0
    if args.action == 'negative':
        return int(bool(negative_controls(config)['failures']))
    if args.action == 'retime':
        retime(config)
        return 0
    if args.action == 'latency-probes':
        return int(any(r['issues'] for r in latency_probes(config, args.jobs, args.detailed)))
    if args.action == 'pending-exits':
        return int(bool(pending_exits(config, args.jobs, names)['failures']))
    if args.action == 'finalize':
        return int(not finalize(config)['automated_suite_pass'])
    if args.action == 'all':
        if (not config['final_link'] or len({r['base'] for r in config['catalog']}) != 373
                or len(config['catalog']) != 398):
            raise ValueError('Full suite requires --final-link, all 373 species and 26 Unown forms; do not use development links')
        results = run_campaign(config, args.jobs, record=args.record)
        timing_comparison(config, results)
        negative_controls(config)
        run_campaign(config, args.jobs, exits=True)
        pending_exits(config, args.jobs)
        stress(config, args.jobs, record=args.record)
        if args.record:
            media(config)
        return int(not summarize(config)['automated_suite_pass'])
    if args.action in ('run', 'timings', 'exits'):
        if args.action == 'timings':
            names = list(REPRESENTATIVE)
        results = run_campaign(config, args.jobs, names, args.action == 'exits', args.record)
        if args.action == 'timings':
            timing_comparison(config, results)
        return int(any(r['issues'] for r in results))
    if args.action == 'stress':
        return int(any(r['issues'] for r in stress(config, args.jobs, names, args.record)))
    return int(bool(summarize(config)['actual']['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
