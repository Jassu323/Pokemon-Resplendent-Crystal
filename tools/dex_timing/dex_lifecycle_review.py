"""Private normal-input Dex lifecycle profiling and address-stable ablations."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import shutil
import statistics
import re
import subprocess

from .assets import Repository, offset, sha256, read_symbols
from .cold_listing import ROOT, Driver, KEY, FRAME
from .info_ui import BOOT
from .performance import core, HZ
from .performance_lifecycle import open_menu
from .legacy_listing import private_battery
from .backlog_revalidation import exit_counterfactual
from pokedex_info_assets import constants

BASE = ROOT / 'build/dex-entry-exit-review-20261013'
PROFILE = {
    'menu_accept': ('StartMenu_Pokedex', True),
    'fade_to_menu': ('FadeToMenu', True),
    'fade_out': ('FadeOutToWhite', True),
    'dex_start': ('Pokedex', True),
    'init_dex': ('InitPokedex', True),
    'clear_bg': ('ClearBGPalettes', True),
    'clear_tilemap': ('ClearTilemap', True),
    'wait_bg': ('WaitBGMap', True),
    'wait_bg2': ('WaitBGMap2', True),
    'disable_lcd': ('DisableLCD', True),
    'enable_lcd': ('EnableLCD', True),
    'dex_gfx': ('Pokedex_LoadGFX', True),
    'font': ('Pokedex_LoadInvertedFont', True),
    'extra_font': ('LoadFontsExtra', True),
    'static_gfx': ('Pokedex_LoadListStaticGFX', True),
    'right_edge': ('DrawDexEntryScreenRightEdge', True),
    'resident_gfx': ('Pokedex_LoadPermanentCGBGFX', True),
    'unown_font': ('Pokedex_LoadUnownFont', True),
    'order': ('Pokedex_OrderMonsByMode', True),
    'presentation': ('Pokedex_InitListingPresentation', True),
    'grid_cache': ('Pokedex_EnsureGridCache', True),
    'modern_init': ('Pokedex_InitMainScreen', True),
    'legacy_init': ('PokedexLegacy_InitMainScreen', True),
    'window': ('Pokedex_CopyBackingToWindow', True),
    'static_picture': ('Pokedex_PrepareAndCommitSelectedMonGFX', True),
    'list_reveal': ('Pokedex_InitMainScreen.revealed', False),
    'exit_accept': ('Pokedex_Exit', False),
    'cleanup': ('Pokedex.exit', True),
    'exit_wait_sfx': ('WaitSFX', True),
    'clear_sprites': ('ClearSprites', True),
    'clear_ids': ('Pokedex_ClearLockedIDs', True),
    'return_map': ('ReturnToMapFromSubmenu', True),
    'map_script': ('RunMapSetupScript', True),
    'map_blocks': ('LoadBlockData', True),
    'connections': ('LoadConnectionBlockData', True),
    'close_submenu': ('CloseSubmenu', True),
    'reload_tiles': ('ReloadTilesetAndPalettes', True),
    'metatiles': ('LoadOverworldTilemapAndAttrmapPals', True),
    'tileset': ('LoadTilesetGFX', True),
    'update_sprites': ('UpdateSprites', True),
    'exit_menu': ('ExitMenu', True),
    'finish_exit': ('FinishExitMenu', True),
    'fade_in': ('FadeInFromWhite', True),
    'reopen_menu': ('StartMenu.Reopen', False),
    'menu_draw': ('StartMenu.OpenMenu', True),
    'menu_input': ('StartMenu.loop', False),
    'skip_music': ('SkipMusic', True),
}


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def call(repo, label):
    pc = repo.symbols[label][1]
    return bytes((0xcd, pc & 255, pc >> 8))


def farcall(repo, bank, pc):
    return bytes((0x3e, bank, 0x21, pc & 255, pc >> 8, 0xc7 + repo.symbols['FarCall'][1]))


def add_helper(repo, data, folder, name, definitions, bank=None):
    if bank is None:
        bank = repo.symbols['Pokedex_CopyDescriptionRightEdge'][0]
    mapping = (BASE / 'baseline/pokecrystal.map').read_text().split(f'ROMX bank #{bank}:')[1].split('ROMX bank #')[0]
    free = re.findall(r'EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+)', mapping)
    for start, finish in free:
        for pc in range(int(start, 16), int(finish, 16) - 95):
            at = offset((bank, pc))
            if bytes(data[at:at+96]) in (bytes(96), bytes([255])*96):
                break
        else:
            continue
        break
    else:
        raise ValueError('No verified private helper space')
    source = ROOT / 'tools/dex_timing/probes' / (name + '.asm')
    obj, rom, sym = (folder / (name + suffix) for suffix in ('.o', '.gbc', '.sym'))
    arguments = dict(PROBE_BANK=bank, PROBE_PC=pc, **definitions)
    subprocess.run(['rgbasm', *(f'-D{key}={value}' for key, value in arguments.items()),
                    '-o', str(obj), str(source)], check=True)
    subprocess.run(['rgblink', '-o', str(rom), '-n', str(sym), str(obj)], check=True)
    labels = read_symbols(sym)
    finish = next(value for label, value in labels.items() if label.endswith('End'))
    payload = rom.read_bytes()[at:offset(finish)]
    if not payload or len(payload) > 96:
        raise ValueError('Unexpected helper size')
    data[at:at+len(payload)] = payload
    return bank, pc, len(payload)


def extra_variants():
    config = json.loads((BASE / 'config.json').read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    entry = offset(repo.symbols['InitPokedex'])
    body = repo.rom[entry:offset(repo.symbols['Pokedex_ClearLockedIDs'])]
    enable = call(repo, 'EnableLCD')
    edge = farcall(repo, *repo.symbols['DrawDexEntryScreenRightEdge'])
    if body.count(enable) != 1 or body.count(edge) != 1:
        raise ValueError('Cold entry changed; re-review helper')
    names = ('entry-edge','exit-local','local-combined','exit-local-guarded','local-guarded',
             'exit-late-guarded','local-late-guarded')
    for name in names:
        folder = BASE / name
        folder.mkdir(exist_ok=True)
        data = bytearray(repo.rom)
        cost = 0
        if name != 'entry-edge':
            if 'late' in name:
                bank, pc, size = add_helper(repo,data,folder,'dex_exit_mask_late',
                    dict(CLEAR_SPRITES=repo.symbols['ClearSprites'][1],
                         CLEAR_PALETTES=repo.symbols['ClearPalettes'][1]),
                    bank=repo.symbols['Pokedex.exit'][0])
                start = offset(repo.symbols['Pokedex.exit'])
                finish = offset(repo.symbols['InitPokedex'])
                body_exit = bytes(data[start:finish])
                original = call(repo,'ClearSprites')
                if body_exit.count(original) != 1:
                    raise ValueError('Post-SFX sprite cleanup changed')
                at = start + body_exit.index(original)
                data[at:at+3] = bytes((0xcd,pc&255,pc>>8))
                cost += size
            else:
                overlay = exit_counterfactual(repo, folder / 'initial-mask.gbc')
                data = bytearray((folder / 'initial-mask.gbc').read_bytes())
                cost += overlay['proposed_romx_bytes']
        if not name.startswith('exit-'):
            data[entry:entry+12] = b''.join(call(repo, label) for label in
                ('ClearPalettes', 'ClearSprites', 'Pokedex_LoadGFX', 'ClearTilemap'))
            defs = dict(H_CGB=repo.symbols['hCGB'][1], COPY_EDGE=repo.symbols['Pokedex_CopyDescriptionRightEdge'][1],
                        ENABLE_LCD=repo.symbols['EnableLCD'][1], OLD_EDGE_BANK=repo.symbols['DrawDexEntryScreenRightEdge'][0],
                        OLD_EDGE=repo.symbols['DrawDexEntryScreenRightEdge'][1], FAR_CALL=repo.symbols['FarCall'][1])
            bank, pc, size = add_helper(repo, data, folder, 'dex_entry_edge', defs)
            at = entry + body.index(enable)
            data[at:at+3] = bytes(3)
            at = entry + body.index(edge)
            data[at:at+6] = farcall(repo, bank, pc)
            cost += size - 3
        if name != 'entry-edge':
            defs = dict(H_CGB=repo.symbols['hCGB'][1], CLOSE_SUBMENU=repo.symbols['CloseSubmenu'][1],
                        CLEAR_PALETTES=repo.symbols['ClearPalettes'][1], RELOAD_TILES=repo.symbols['ReloadTilesetAndPalettes'][1],
                        UPDATE_SPRITES=repo.symbols['UpdateSprites'][1], EXIT_MENU=repo.symbols['ExitMenu'][1],
                        MAP_PALS=constants(ROOT / 'constants/scgb_constants.asm')['SCGB_MAPPALS'],
                        GET_LAYOUT=repo.symbols['GetSGBLayout'][1], OW_PAL_BANK=repo.symbols['LoadOW_BGPal7'][0],
                        OW_PAL=repo.symbols['LoadOW_BGPal7'][1], FAR_CALL=repo.symbols['FarCall'][1],
                        COPY_MAP=repo.symbols['CGBOnly_CopyTilemapAtOnce'][1], H_BG_MODE=repo.symbols['hBGMapMode'][1],
                        FADE_BANK=repo.symbols['FadeInFromWhite'][0], FADE_IN=repo.symbols['FadeInFromWhite'][1],
                        ENABLE_SPRITES=repo.symbols['EnableSpriteUpdates'][1])
            if 'guarded' in name:
                defs.update(PAL_GUARD=1,H_PAL_UPDATE=repo.symbols['hCGBPalUpdate'][1],
                            DELAY_FRAME=repo.symbols['DelayFrame'][1])
            bank, pc, size = add_helper(repo, data, folder, 'dex_exit_local', defs)
            start = offset(repo.symbols['StartMenu_Pokedex'])
            end = offset(repo.symbols['StartMenu_Pokedex.empty'])
            original = repo.rom[start:end]
            close = call(repo, 'CloseSubmenu')
            if original.count(close) != 1 or original[-3:] != close:
                raise ValueError('Dex caller cleanup changed')
            at = start + original.index(close)
            data[at:at+3] = bytes((0xc3, pc & 255, pc >> 8))
            # A JP in bank 4 must target a bank-4 helper; a farcall cannot fit.
            # Reserve a small local trampoline from its own verified free space.
            caller_bank = repo.symbols['StartMenu_Pokedex'][0]
            caller_map = (BASE / 'baseline/pokecrystal.map').read_text().split(f'ROMX bank #{caller_bank}:')[1].split('ROMX bank #')[0]
            ranges = re.findall(r'EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+)', caller_map)
            trampoline = next(int(a,16) for a,b in ranges if int(b,16)-int(a,16)+1 >= 9)
            at_stub = offset((caller_bank, trampoline))
            if bytes(data[at_stub:at_stub+9]) not in (bytes(9), bytes([255])*9):
                raise ValueError('Caller trampoline is not unused')
            empty = repo.symbols['StartMenu_Pokedex.empty'][1]
            stub = farcall(repo, bank, pc) + bytes((0x18, 0))
            jump = empty - (trampoline + 8)
            if not -128 <= jump <= 127:
                stub = farcall(repo, bank, pc) + bytes((0xc3, empty & 255, empty >> 8))
            else:
                stub = stub[:-1] + bytes((jump & 255,))
            data[at_stub:at_stub+len(stub)] = stub
            at = start + original.index(close)
            data[at:at+3] = bytes((0xc3, trampoline & 255, trampoline >> 8))
            cost += size + len(stub)
        data[0x14e:0x150] = bytes(2)
        data[0x14e:0x150] = (sum(data) & 65535).to_bytes(2, 'big')
        path = folder / 'pokecrystal-diagnostic.gbc'
        path.write_bytes(data)
        config['variants'][name] = dict(rom=str(path), sha256=sha256(data), proposed_romx_delta=cost,
                                        wram_delta=0, address_stable_binary_ablation=True)
    write(BASE / 'config.json', config)
    print(json.dumps({k:v for k,v in config['variants'].items() if k in names}, indent=2))


def observer(repo):
    folder = BASE / 'observer-v2'
    folder.mkdir(exist_ok=True)
    header = folder / 'lifecycle-symbols.h'
    header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n' +
                      '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}'
                                for name in ('hSCX', 'hWX', 'hWY')) + '\n')
    return core(repo, folder, PROFILE, ('-DDEX_LIFECYCLE_TRACE',
                                       f'-DDEX_LIFECYCLE_SYMBOLS="{header.resolve()}"'))


def prepare(battery):
    BASE.mkdir(parents=True, exist_ok=True)
    target = BASE / 'baseline'
    target.mkdir(exist_ok=False)
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / ('pokecrystal.' + suffix), target / ('pokecrystal.' + suffix))
    shutil.copy2(battery, target / 'private.sav')
    repo = Repository(ROOT, target / 'pokecrystal.gbc', target / 'pokecrystal.sym')
    binary = observer(repo)
    cfg = dict(core=str(binary), rom=str(repo.rom_path), sym=str(target / 'pokecrystal.sym'),
               battery=str(target / 'private.sav'))
    fixtures = {}
    for style in (0, 1):
        for order in (0, 1, 2):
            path = target / f'style-{style}-order-{order}.sav'
            private_battery(cfg, path, presentation=style, order_mode=order)
            fixtures[f'{style}-{order}'] = str(path)
    original = repo.rom
    entry = offset(repo.symbols['InitPokedex'])
    expected = b''.join(call(repo, name) for name in
                       ('ClearBGPalettes', 'ClearSprites', 'ClearTilemap', 'Pokedex_LoadGFX'))
    if original[entry:entry+12] != expected:
        raise ValueError('Init ordering changed; re-review ablation')
    variants = {'baseline': dict(rom=str(repo.rom_path), proposed_romx_delta=0)}
    for name in ('entry-reorder', 'exit-mask', 'exit-async', 'combined'):
        folder = BASE / name
        folder.mkdir()
        rom = folder / 'pokecrystal-diagnostic.gbc'
        if name in ('exit-mask', 'exit-async', 'combined'):
            overlay = exit_counterfactual(repo, rom)
            data = bytearray(rom.read_bytes())
            cost = overlay['proposed_romx_bytes']
        else:
            data = bytearray(original)
            cost = 0
        if name in ('entry-reorder', 'combined'):
            data[entry:entry+12] = b''.join(call(repo, label) for label in
                ('ClearPalettes', 'ClearSprites', 'Pokedex_LoadGFX', 'ClearTilemap'))
        if name == 'exit-async':
            start = offset(repo.symbols['Pokedex.exit'])
            end = offset(repo.symbols['InitPokedex'])
            body = bytes(data[start:end])
            instruction = call(repo, 'WaitSFX')
            if body.count(instruction) != 1:
                raise ValueError('Exit WaitSFX changed; re-review ablation')
            at = start + body.index(instruction)
            data[at:at+3] = bytes(3)
            cost -= 3
        data[0x14e:0x150] = bytes(2)
        data[0x14e:0x150] = (sum(data) & 65535).to_bytes(2, 'big')
        rom.write_bytes(data)
        variants[name] = dict(rom=str(rom), sha256=sha256(data), proposed_romx_delta=cost,
                              wram_delta=0, address_stable_binary_ablation=True)
    config = dict(**cfg, fixtures=fixtures, variants=variants, baseline_hashes=repo.hashes,
                  live_save_used_only_as_copied_donor=True)
    write(BASE / 'config.json', config)
    print(json.dumps(dict(prepared=list(variants), hashes=repo.hashes)), flush=True)


def reach(driver, repo, label, key=None):
    bank, pc = repo.symbols[label]
    result = driver.command(f'restorerun {bank} {pc} {600 * FRAME} {KEY.get(key, 0)}')
    if result['hit'] < 0:
        raise RuntimeError('Timed out at ' + label)
    return result


def measured(driver, repo, label, key, folder, name, capture):
    initial = driver.command('perf 1')
    driver.events.clear()
    if capture:
        driver.command(f'perfimages {folder}/{name}')
        driver.command(f'perfaudio {folder}/{name}.pcm')
    ready = reach(driver, repo, label, key)
    driver.run(frames=4)
    final = driver.command('perf 0')
    driver.command('perfimages -')
    driver.command('perfaudio -')
    events = list(driver.events)
    frames = [e for e in events if e['event'] == 'perf_frame' and e['type'] == 0]
    good = {e['full'] for e in frames if e['t'] >= ready['t'] and e['white'] < 23040}
    complete = next((e for e in frames if e['full'] in good), None)
    changed = next((e for e in frames if e['full'] != initial['full']), None)
    white = next((e for e in frames if e['white'] == 23040), None)
    costs = defaultdict(list)
    for event in events:
        if event['event'] == 'perf_cost':
            costs[event['name']].append(event['elapsed'] * 1000 / HZ)
    origin = initial['t']
    metric = lambda event: None if event is None else (event['t'] - origin) * 1000 / HZ
    result = dict(input_to_ready_ms=(ready['t']-origin)*1000/HZ,
                  first_change_ms=metric(changed), complete_screen_ms=metric(complete),
                  first_white_ms=metric(white), white_frames=sum(e['white']==23040 for e in frames),
                  ready=ready, final=final, costs={k:dict(calls=len(v), total_ms=sum(v),
                    max_ms=max(v)) for k,v in costs.items()},
                  phases=[e for e in events if e['event']=='perf_phase' and e['name'] in PROFILE])
    with gzip.open(folder / (name + '-events.json.gz'), 'wt') as stream:
        json.dump(events, stream)
    return result, driver.command('ui')


def case(task):
    base, variant, style, order, phase = task
    base = Path(base)
    config = json.loads((base / 'config.json').read_text())
    repo = Repository(Path(config.get('root', ROOT)), Path(config['variants'][variant]['rom']), Path(config['sym']))
    folder = base / variant / f'style-{style}-order-{order}-q{phase}'
    folder.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['core'], repo.rom_path, BOOT, config['fixtures'][f'{style}-{order}'],
                    folder / 'driver.log')
    rows = []
    try:
        driver.command('rawcolor')
        open_menu(driver)
        driver.command(f'run 0 {phase} 0')
        loop = 'Pokedex_UpdateMainScreen'
        for iteration in range(2):
            entry, listing = measured(driver, repo, loop, 'a', folder, f'entry-{iteration}',
                                      phase==0 and iteration==0)
            leave, menu = measured(driver, repo, 'StartMenu.loop', 'b', folder, f'exit-{iteration}',
                                   phase==0 and iteration==0)
            if not entry['ready']['double_speed'] or not leave['ready']['double_speed']:
                raise AssertionError('Global clock policy changed')
            rows.append(dict(variant=variant, style=style, order=order, phase=phase,
                             iteration=iteration, entry=entry, exit=leave,
                             listing=listing, menu=menu, issues=[]))
        driver.run(('overworld',), frames=600, key='b')
        if not driver.command('peek')['double_speed']:
            raise AssertionError('Global overworld clock policy changed')
    finally:
        driver.close()
    write(folder / 'summary.json', rows)
    return rows


def profile(variants, jobs):
    tasks = [(str(BASE), v, style, order, phase) for v in variants for style in (0, 1)
             for order in (0, 1, 2) for phase in (0, 17556, 35112, 52668)]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for batch in pool.map(case, tasks):
            rows.extend(batch)
            if len(rows) % 16 == 0:
                print(json.dumps(dict(cases=len(rows), variants=variants)), flush=True)
    target = BASE / ('profile-' + '-'.join(variants) + '.json')
    write(target, dict(cases=len(rows), rows=rows))
    summaries = {}
    for variant in variants:
        summaries[variant] = {}
        for direction in ('entry', 'exit'):
            records = [r[direction] for r in rows if r['variant']==variant]
            values = [r['input_to_ready_ms'] for r in records]
            summaries[variant][direction] = dict(min_ms=min(values), median_ms=statistics.median(values),
                                                max_ms=max(values))
    print(json.dumps(summaries, indent=2), flush=True)


def visible_ui_differences(old, new, style, surface):
    """Normalize only known icon-frame pairs and strictly off-screen cells."""
    differences, allowances = [], []
    fields = ('map','attrs','picture','palettes','obj_palettes','window','window_attrs',
              'oam','lcdc','scx','scy','wx','wy')
    for field in fields:
        if old[field] == new[field]:
            continue
        if field in ('window', 'window_attrs'):
            a, b = bytearray.fromhex(old[field]), bytearray.fromhex(new[field])
            changed = [i for i, pair in enumerate(zip(a, b)) if pair[0] != pair[1]]
            if len(a) != len(b) or len(a) != 360:
                differences.append(field)
                continue
            # The returned menu hides the whole window below the LCD.
            if old['wy'] >= 144 and new['wy'] >= 144:
                allowances.append(field + ':hidden_window')
                continue
            allowed = []
            for at in changed:
                row, column = divmod(at, 20)
                x, y = old['wx'] - 7 + column * 8, old['wy'] + row * 8
                if x >= 160 or y >= 144:
                    allowed.append('offscreen_column')
                elif field == 'window' and style == 0 and row in (5,6,9,10,13,14) and column in (1,2,9,10):
                    icon_row = (row - 5) // 4
                    cell = (column - 1) % 8 + (4 if column >= 9 else 0) + (2 if row % 4 == 2 else 0)
                    first = (icon_row + 1) * 8 + cell
                    if {a[at], b[at]} == {first, (first + 0xd2) & 255}:
                        allowed.append('side_icon_animation_phase')
                    else:
                        differences.append(field + ':' + str(at))
                else:
                    differences.append(field + ':' + str(at))
            allowances.extend(field + ':' + name for name in sorted(set(allowed)))
        elif field == 'oam' and style == 0 and surface == 'listing':
            a, b = bytes.fromhex(old[field]), bytes.fromhex(new[field])
            changed = [i for i, pair in enumerate(zip(a,b)) if pair[0] != pair[1]]
            legal = all(at < 48 and at % 4 == 2 and
                        {a[at],b[at]} == {(at // 16 + 1) * 8 + (at // 4) % 4,
                                         (at // 16 + 1) * 8 + (at // 4) % 4 + 4}
                        for at in changed)
            if len(a) == len(b) == 160 and legal:
                allowances.append('oam:center_icon_animation_phase')
            else:
                differences.append(field)
        else:
            differences.append(field)
    return dict(issues=differences, allowances=allowances)


def exit_matrix(variants):
    from .backlog_revalidation import EXIT_POINTS, exit_case
    from .listing_restoration import compile_observer
    config = json.loads((BASE / 'config.json').read_text())
    fixture = ROOT / 'build/dex-selected-ancestors-integration-20261013/precomputed/focused/modern'
    origin = json.loads((fixture / 'config.json').read_text())
    if sha256(Path(origin['rom']).read_bytes()) != config['baseline_hashes']['rom_sha256']:
        raise ValueError('Historical fixture must match the lifecycle baseline')
    for variant in variants:
        folder = BASE / 'exit-matrix' / variant
        checkpoints = folder / 'checkpoints'
        checkpoints.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config['variants'][variant]['rom'], checkpoints / 'input-copy.gbc')
        shutil.copy2(fixture / 'private.sav', checkpoints / 'input-copy.sav')
        states = checkpoints / 'listing-states'
        if not states.exists():
            states.symlink_to(fixture / 'listing-states', target_is_directory=True)
        repo = Repository(ROOT, checkpoints / 'input-copy.gbc', Path(config['sym']))
        write(checkpoints / 'provenance.json', repo.hashes)
        output = folder / 'results'
        output.mkdir(exist_ok=True)
        previous = output / 'report.json'
        if previous.exists() and json.loads(previous.read_text())['provenance'] == repo.hashes:
            print(json.dumps(dict(variant=variant,reused_completed_matrix=True)),flush=True)
            continue
        overrides = {}
        if config['variants'][variant].get('close_probe'):
            helper = tuple(config['variants'][variant]['close_probe'])
            repo.symbols['CloseSubmenu'] = helper
            overrides['close_submenu'] = list(helper)
        elif variant in ('exit-local','local-combined','exit-local-guarded','local-guarded',
                       'exit-late-guarded','local-late-guarded'):
            helper = read_symbols(BASE / variant / 'dex_exit_local.sym')['ProbeExitLocal']
            repo.symbols['CloseSubmenu'] = helper
            overrides['close_submenu'] = list(helper)
        binary = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output,
            extra_points={k:v for k,v in EXIT_POINTS.items() if v in repo.symbols},
            extra_fields=('wPokedexRenderedSelectionKey',),
            extra_flags=('-DDEX_BACKLOG_REVALIDATION_TRACE',))
        driver = Driver(binary, repo.rom_path, BOOT, checkpoints / 'input-copy.sav', output / 'core.log')
        results = []
        try:
            for name in ('chikorita','dusknoir','weavile','regigigas'):
                for pages in (-1,0,9) if name != 'regigigas' else (-1,0):
                    for idle in range(8):
                        results.append(exit_case(driver,repo,checkpoints,output,name,pages,idle,False))
            write(previous, dict(provenance=repo.hashes,mode='exit',host_only_instrumentation=True,
                                 diagnostic_observer_address_overrides=overrides,results=results))
        finally:
            driver.close()
        print(json.dumps(dict(variant=variant,cases=len(results),
                              shifted=sum(bool(r['shifted_frames']) for r in results))),flush=True)


def route_case(task):
    from .info_ui import press, ready as info_ready
    from .description_ui import settle
    from .legacy_listing import open_mode_screen
    from .moves_mode import enter as enter_moves
    from .moves_search import open_search, row as search_row, search
    from .type_matchups import enter_types
    base, variant, style, route, battery = task
    base = Path(base)
    config = json.loads((base / 'config.json').read_text())
    repo = Repository(Path(config.get('root', ROOT)), Path(config['variants'][variant]['rom']), Path(config['sym']))
    folder = base / 'routes' / variant / f'{style}-{route}'
    folder.mkdir(parents=True, exist_ok=True)
    driver = Driver(config['core'], repo.rom_path, BOOT, battery, folder / 'driver.log')
    try:
        driver.command('rawcolor')
        open_menu(driver)
        reach(driver, repo, 'Pokedex_UpdateMainScreen', 'a')
        driver.run(frames=4)
        if route == 'modes-cancel':
            open_mode_screen(driver)
            press(driver, 'b')
        elif route == 'pokemon-search':
            press(driver, 'start')
            press(driver, 'down')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            press(driver, 'down')
            press(driver, 'down')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateSearchResultsScreen')
            press(driver, 'down')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateSearchScreen')
            press(driver, 'b')
        elif route in ('description','info-ancestors','selected-moves','area'):
            if route == 'info-ancestors':
                press(driver, 'down' if style else 'right')
            reach(driver, repo, 'PokedexSelectedMon_Update', 'a')
            settle(driver)
            tabs = {'description':0,'info-ancestors':1,'selected-moves':2,'area':3}[route]
            for _ in range(tabs):
                press(driver, 'right')
            if tabs:
                press(driver, 'a')
                if route == 'info-ancestors':
                    ui = info_ready(driver, 0)
                    if ui['info_pages'] < 3:
                        raise AssertionError('Bayleef forward/ancestor pages were not reached')
                    for page in range(1, ui['info_pages']):
                        press(driver, 'a')
                        info_ready(driver, page)
                else:
                    driver.run(frames=120)
                    expected = 2 if route == 'selected-moves' else 3
                    if driver.command('ui')['view'] != expected:
                        raise AssertionError('Selected tab was not reached')
            press(driver, 'b')
            if route == 'area':
                reach(driver, repo, 'PokedexSelectedMon_Update')
                driver.run(frames=2)
                press(driver, 'b')
        elif route == 'unown':
            open_mode_screen(driver)
            current = driver.command('ui')['footer_cursor']
            for _ in range(abs(2-current)):
                press(driver, 'down' if current < 2 else 'up')
            press(driver, 'a')
            reach(driver, repo, 'Pokedex_UpdateUnownMode')
            press(driver, 'right')
            press(driver, 'left')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            press(driver, 'b')
        elif route == 'types':
            enter_types(driver, repo, True)
            press(driver, 'down')
            press(driver, 'right')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            press(driver, 'b')
        elif route == 'moves-search':
            enter_moves(driver, repo, True)
            open_search(driver, repo)
            search_row(driver, repo, 1)
            press(driver, 'a')
            reach(driver, repo, 'PokedexMovesSearch_TextUpdate')
            press(driver, 'a')
            press(driver, 'b')
            press(driver, 'start')
            press(driver, 'a')
            reach(driver, repo, 'PokedexMovesSearch_Update')
            search(driver, repo)
            press(driver, 'right')
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesSearch_Update')
            press(driver, 'b')
            reach(driver, repo, 'PokedexMovesMode_Update')
            press(driver, 'select')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            press(driver, 'b')
        else:
            raise ValueError(route)
        reach(driver, repo, 'Pokedex_UpdateMainScreen')
        driver.run(frames=4)
        leave, menu = measured(driver, repo, 'StartMenu.loop', 'b', folder, 'exit', False)
        driver.run(('overworld',), frames=600, key='b')
        driver.run(frames=30, key='right')
        driver.run(frames=30)
        driver.command(f'image {folder}/overworld.ppm')
        speed = driver.command('peek')['double_speed']
        if speed != 1:
            raise AssertionError('Global clock policy changed')
        result = dict(variant=variant,style=style,route=route,exit=leave,menu=menu,
                      overworld_double_speed=speed,issues=[])
    except (RuntimeError,AssertionError,ValueError) as error:
        result = dict(variant=variant,style=style,route=route,issues=[str(error)])
        driver.evidence(folder / 'failure')
    finally:
        driver.close()
    write(folder / 'summary.json', result)
    return result


def routes(variants, jobs):
    config = json.loads((BASE / 'config.json').read_text())
    fixtures = {}
    for style in (0,1):
        path = BASE / f'route-style-{style}.sav'
        private_battery(config, path, presentation=style, order_mode=0, unown_unlocked=True)
        fixtures[style] = str(path)
    names = ('modes-cancel','pokemon-search','description','info-ancestors','selected-moves',
             'area','unown','types','moves-search')
    tasks = [(str(BASE),v,s,name,fixtures[s]) for v in variants for s in (0,1) for name in names]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(route_case, tasks))
    baseline = {(r['style'],r['route']):r for r in rows if r['variant']=='baseline'}
    for row in rows:
        old = baseline.get((row['style'],row['route']))
        if old and 'menu' in old and 'menu' in row:
            row['menu_comparison'] = visible_ui_differences(old['menu'],row['menu'],row['style'],'menu')
            row['issues'] += row['menu_comparison']['issues']
    result = dict(cases=len(rows),failures=sum(bool(r['issues']) for r in rows),rows=rows)
    write(BASE / 'routes-summary.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)


def capture_audit():
    from PIL import Image
    rows = [dict(row,campaign=path.parent.name) for version in ('v2','v3','v4')
            for path in (BASE / version).glob('profile-*.json')
            for row in json.loads(path.read_text())['rows'] if row['phase']==0 and row['iteration']==0]
    references, results = {}, []
    def pixels(path, style, direction):
        with Image.open(path) as source:
            picture = source.convert('RGB')
            if style == 0 and direction == 'entry':
                for y in (40,72,104):
                    for x in (72,104,136):
                        picture.paste((0,0,0),(x,y,x+16,y+16))
            elif direction == 'exit':
                picture.paste((0,0,0),(88,16,96,24))
            return picture.tobytes()
    for row in sorted(rows,key=lambda r:r['variant']!='baseline'):
        folder = BASE / row['campaign'] / row['variant'] / f'style-{row["style"]}-order-{row["order"]}-q0'
        for direction in ('entry','exit'):
            paths = sorted(folder.glob(direction+'-0-*.ppm'))
            final = pixels(paths[-1],row['style'],direction)
            key = row['style'],row['order'],direction
            if row['variant']=='baseline':
                references[key] = final
            with gzip.open(folder / (direction+'-0-events.json.gz'),'rt') as stream:
                events = json.load(stream)
            frames = {e['display']:e for e in events if e['event']=='perf_frame'}
            origin = row[direction]['ready']['t'] - row[direction]['input_to_ready_ms']*HZ/1000
            signature = [pixels(path,row['style'],direction)==final for path in paths]
            first = next(i for i,value in enumerate(signature) if value)
            frame = int(paths[first].stem.rsplit('-',1)[1])
            record = dict(variant=row['variant'],style=row['style'],order=row['order'],direction=direction,
                          static_destination_ms=(frames[frame]['boundary_t']-origin)*1000/HZ,
                          frames=len(paths),same_static_pixels_as_baseline=final==references[key],
                          reverted_after_destination=not all(signature[first:]),
                          ignored_regions=('Only the nine 16x16 animated grid icons' if direction=='entry'
                                           and row['style']==0 else 'Only the 8x8 blinking Start-menu arrow'
                                           if direction=='exit' else 'None'))
            results.append(record)
    summary = dict(cases=len(results),failures=sum(not r['same_static_pixels_as_baseline'] or
                    r['reverted_after_destination'] for r in results),rows=results)
    write(BASE / 'capture-audit.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)


def report():
    config = json.loads((BASE / 'config.json').read_text())
    rows = [dict(row,campaign=path.parent.name) for version in ('v2','v3','v4')
            for path in (BASE / version).glob('profile-*.json')
            for row in json.loads(path.read_text())['rows']]
    def key(row):
        return tuple(row[name] for name in ('style','order','phase','iteration'))
    baseline = {key(row): row for row in rows if row['variant']=='baseline'}
    results = {}
    ui_fields = ('map','attrs','picture','palettes','obj_palettes','window','window_attrs',
                 'oam','lcdc','scx','scy','wx','wy')
    def stats(values):
        return dict(cases=len(values), min=min(values), median=statistics.median(values), max=max(values))
    for variant in config['variants']:
        group = [r for r in rows if r['variant']==variant]
        if not group:
            continue
        comparisons, sound, shifted = [], [], []
        for row in group:
            old = baseline[key(row)]
            differences = {surface:[field for field in ui_fields if row[surface][field] != old[surface][field]]
                           for surface in ('listing','menu')}
            visible = {surface:visible_ui_differences(old[surface],row[surface],row['style'],surface)
                       for surface in ('listing','menu')}
            comparisons.append(dict(case=key(row), differences=differences, visible_audit=visible))
            folder = BASE / row['campaign'] / variant / f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
            with gzip.open(folder / f'exit-{row["iteration"]}-events.json.gz', 'rt') as stream:
                events = json.load(stream)
            sounds = [e for e in events if e['event']=='life_sfx']
            start = next((e for e in sounds if e['mask']), None)
            stop = next((e for e in sounds if start and e['t']>start['t'] and not e['mask']), None)
            if start and stop:
                sound.append((stop['t']-start['t'])*1000/HZ)
            frames = {e['display']:e for e in events if e['event']=='perf_frame'}
            cleanup = next(e['t'] for e in events if e['event']=='perf_phase' and e['name']=='cleanup')
            white = next((e['t'] for e in events if e['event']=='perf_frame' and e['white']==23040), float('inf'))
            bad = [e for e in events if e['event']=='life_frame' and cleanup<e['t']<white and
                   (e['scx'],e['wx'],e['wy']) != (5,71,0) and frames[e['display']]['white']<23040]
            shifted.append(len(bad))
        record = dict(cases=len(group), resources=config['variants'][variant],
                      sfx_active_ms=stats(sound), shifted_colored_exit_cases=sum(bool(n) for n in shifted),
                      final_ui_difference_cases=sum(any(c['differences'].values()) for c in comparisons),
                      visible_ui_issue_cases=sum(any(v['issues'] for v in c['visible_audit'].values())
                                                 for c in comparisons),
                      final_ui_comparisons=comparisons)
        for direction in ('entry','exit'):
            record[direction] = dict(ready_ms=stats([r[direction]['input_to_ready_ms'] for r in group]),
                paired_delta_ms=stats([r[direction]['input_to_ready_ms']-baseline[key(r)][direction]['input_to_ready_ms']
                                      for r in group]),
                complete_screen_ms=stats([r[direction]['complete_screen_ms'] for r in group
                                         if r[direction]['complete_screen_ms'] is not None]),
                first_white_ms=stats([r[direction]['first_white_ms'] for r in group
                                     if r[direction]['first_white_ms'] is not None]))
        results[variant] = record
    record = dict(baseline_hashes=config['baseline_hashes'], cases=len(rows), variants=results,
                  measurements='Physical emulated LCD time; normal inputs, private batteries, read-only host observer',
                  production_unchanged=Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym').hashes==config['baseline_hashes'])
    write(BASE / 'comparison.json', record)
    print(json.dumps({name:dict(cases=r['cases'],visible_issues=r['visible_ui_issue_cases'],
                      entry_ms=r['entry']['ready_ms']['median'],exit_ms=r['exit']['ready_ms']['median'],
                      entry_delta_ms=r['entry']['paired_delta_ms']['median'],
                      exit_delta_ms=r['exit']['paired_delta_ms']['median'])
                      for name,r in results.items()},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','observer','variants','profile','exit-matrix','routes','capture-audit','report'))
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--battery', type=Path)
    parser.add_argument('--variants', nargs='+', default=['baseline'])
    parser.add_argument('--jobs', type=int, default=6)
    args = parser.parse_args()
    BASE = args.base.resolve()
    if args.action == 'prepare':
        prepare(args.battery.resolve())
    elif args.action == 'observer':
        config = json.loads((BASE / 'config.json').read_text())
        repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
        config['core'] = str(observer(repo))
        write(BASE / 'config.json', config)
    elif args.action == 'variants':
        extra_variants()
    elif args.action == 'report':
        report()
    elif args.action == 'exit-matrix':
        exit_matrix(args.variants)
    elif args.action == 'routes':
        routes(args.variants, args.jobs)
    elif args.action == 'capture-audit':
        capture_audit()
    else:
        profile(args.variants, args.jobs)
