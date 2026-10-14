"""Native, normal-input qualification of the private Type Matchups prototype."""
import argparse
import json
from pathlib import Path
import shutil

from PIL import Image

from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, bootstrap, audit as playback_audit
from .performance import core as performance_core
from .dex_modes import audit_menu
from .legacy_listing import private_battery
from .listing_options import listing_audit
from pokedex_info_assets import constants, species
from .description_ui import settle, audit as description_audit

OUTPUT = ROOT / 'build/dex-types-cursors-20261011'
BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')


def reach(driver, repo, label, key=None, frames=600):
    bank, pc = repo.symbols[label]
    result = driver.command(f'restorerun {bank} {pc} {frames * 70224} '
                            f'{dict(a=16,b=32,select=64,start=128).get(key,0)}')
    assert result['hit'] == 0, (label, result)
    return result


def press(driver, key):
    driver.run(frames=4, key=key)
    return driver.run(frames=4)


def capture(driver, path):
    ppm = path.with_suffix('.ppm')
    driver.command(f'image {ppm}')
    with Image.open(ppm) as image:
        result = image.convert('RGB').copy()
        result.save(path)
    ppm.unlink()
    return result


def memory(driver, repo, label, count, delta=0):
    bank, at = repo.symbols[label]
    return bytes.fromhex(driver.command(f'perfram {bank} {at + delta} {count}')['bytes'])


def rgb555(word):
    return tuple(((word >> shift & 31) << 3) | (word >> shift & 31) >> 2
                 for shift in (0, 5, 10))


class Oracle:
    def __init__(self, repo):
        self.repo = repo
        self.workbook = json.loads((ROOT / 'tools/dex_timing/probes/type_matchups_workbook.json').read_text())
        self.names, self.matrix = self.workbook['names'], self.workbook['matrix']
        const = constants(ROOT / 'constants/type_constants.asm')
        self.ids = [const['PSYCHIC_TYPE' if name == 'Psychic' else name.upper()] for name in self.names]
        self.icons = []
        for id_ in self.ids:
            at = offset(repo.symbols['CompactTypeIconGFXPointers']) + id_ * 3
            bank, lo, hi = repo.rom[at:at + 3]
            at = offset((bank, lo | hi << 8))
            raw = repo.rom[at:at + 64]
            at = offset(repo.symbols['TypeIconPalettePointers']) + id_ * 2
            pointer = int.from_bytes(repo.rom[at:at + 2], 'little')
            at = offset((repo.symbols['TypeIconPalettePointers'][0], pointer))
            accent = int.from_bytes(repo.rom[at + 4:at + 6], 'little')
            colors = [(255,255,255), (41,41,41), rgb555(accent), (0,0,0)]
            pixels = []
            for y in range(8):
                for x in range(32):
                    tile, bit = x // 8, 7 - x % 8
                    i = tile * 16 + y * 2
                    color = (raw[i] >> bit & 1) | (raw[i + 1] >> bit & 1) << 1
                    if (x,y) in ((0,0),(0,7),(31,0),(31,7)):
                        color = 1
                    pixels.append(colors[color])
            icon = Image.new('RGB', (32,8))
            icon.putdata(pixels)
            self.icons.append(icon)
        at = offset(repo.symbols['TypeMatchups'])
        linked = [[1 for _ in self.ids] for _ in self.ids]
        records = 0
        while repo.rom[at] != 255:
            if repo.rom[at] == 254:
                at += 1
                continue
            attack, defense, factor = repo.rom[at:at + 3]
            linked[self.ids.index(attack)][self.ids.index(defense)] = factor / 10
            at += 3
            records += 1
        assert linked == self.matrix, 'Linked battle chart differs from workbook'
        self.records = records

    def lists(self, selection):
        weak = [i for i in range(18) if self.matrix[i][selection] == 2]
        steel = self.names[selection] == 'Steel'
        resist = [i for i in range(18) if self.matrix[i][selection] == 0.5
                  or steel and self.matrix[i][selection] == 0]
        immune = [] if steel else [i for i in range(18) if self.matrix[i][selection] == 0]
        return weak, resist, immune

    def label(self, text):
        font = offset(self.repo.symbols['Font'])
        codes = {'I':0x88, 'R':0x91, 'W':0x96, ':':0x9c}
        result = Image.new('RGB', (16,8), (41,41,41))
        for column, letter in enumerate(text):
            start = font + (codes[letter] - 0x80) * 8
            for y, bits in enumerate(self.repo.rom[start:start+8]):
                for x in range(8):
                    if bits & (0x80 >> x):
                        result.putpixel((column*8+x,y), (255,255,255))
        return result

    def audit(self, driver, selection, image):
        state = memory(driver, self.repo, 'wPokedexWRAM0Scratch', 48)
        assert state[0] == selection, (selection, state[0])
        weak, resist, immune = self.lists(selection)
        assert (state[8],state[9],state[7]) == (len(weak),len(resist),len(immune))
        assert list(state[11:11+len(weak)]) == weak
        assert list(state[29:29+len(resist)]) == resist
        assert list(memory(driver, self.repo, 'wPokedexWRAM0Scratch', 18,
                           delta=0x2a0)[:len(immune)]) == immune
        rrow = 15 if len(weak) > 4 else 14
        assert state[10] == rrow
        boxes = []
        for i in range(18):
            boxes.append((i, 16+(i%3)*48, 8+(i//3)*14))
        for ids, y in ((weak,96),(resist,rrow*8),(immune,128)):
            for i, type_ in enumerate(ids):
                boxes.append((type_,24+(i%4)*32,y+(i//4)*8))
        for type_, x, y in boxes:
            actual = image.crop((x,y,x+32,y+8)).tobytes()
            expected = self.icons[type_].tobytes()
            if actual != expected:
                failure = Path(driver.log.name).parent / 'badge-failure'
                driver.command(f'save {failure}.s0')
                failure.with_suffix('.json').write_text(json.dumps(driver.command('ui'),indent=2)+'\n')
            assert actual == expected, (self.names[selection],
                'badge_pixels', self.names[type_], x, y,
                [(n//3%32,n//96,tuple(actual[n:n+3]),tuple(expected[n:n+3]))
                 for n in range(0,len(actual),3) if actual[n:n+3] != expected[n:n+3]][:16])
        ui = driver.command('ui')
        assert (ui['scx'],ui['wx'],ui['wy']) == (0,167,0)
        oam = bytes.fromhex(ui['oam'])
        assert oam[0] in (0,24+(selection//3)*14)
        assert oam[1:4] == bytes((16+(selection%3)*48,90,8))
        assert not any(oam[4:]), 'Unexpected objects can exhaust the scanline limit'
        expected_lower = Image.new('RGB', (144,40), (41,41,41))
        for label, y in (('W:',96),('R:',rrow*8)) + ((('I:',128),) if immune else ()):
            expected_lower.paste(self.label(label), (0,y-96))
        for ids, y in ((weak,96),(resist,rrow*8),(immune,128)):
            for i, type_ in enumerate(ids):
                expected_lower.paste(self.icons[type_], (16+(i%4)*32,y-96+(i//4)*8))
        assert image.crop((8,96,152,136)).tobytes() == expected_lower.tobytes(), (selection,'lower_panel')
        for y in list(range(6,90)) + list(range(94,138)):
            assert image.getpixel((1,y)) == (255,255,255)
            assert image.getpixel((158,y)) == (255,255,255)
        red = rgb555(int.from_bytes(
            self.repo.rom[offset(self.repo.symbols['PokedexUIPalette'])+2:
                          offset(self.repo.symbols['PokedexUIPalette'])+4], 'little'))
        assert all(image.getpixel((x,92)) == red for x in range(2,158))
        for y in list(range(5)) + list(range(139,144)):
            assert all(image.getpixel((x,y)) == red for x in range(160)), ('outer_margin',selection,y)
        for y in (5,138):
            assert all(image.getpixel((x,y)) == (255,255,255) for x in range(1,159)), ('frame',selection,y)
        return len(boxes) * 256


def enter_types(driver, repo, unlocked):
    press(driver, 'select')
    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
    current = driver.command('ui')['footer_cursor']
    row = 4 if unlocked else 3
    for _ in range(abs(row-current)):
        press(driver, 'down' if row > current else 'up')
    press(driver, 'a')
    reach(driver, repo, 'PokedexTypes_Update')
    driver.run(frames=4)


def trace_audit(events):
    frames = [e for e in events if e['event'] == 'types_frame']
    assert frames, 'No native raster evidence'
    assert not any(e[k] for e in frames for k in ('bad_modes','bad_indexes','bad_registers'))
    assert all(e['writes'] == 88 for e in frames[2:]), 'Missed or extra raster writes'
    if frames[-1].get('mode7'):
        assert all(e[k] == 1 for e in frames[2:]
                   for k in ('irq_count','sound_updates','input_updates','clock_updates')), 'Frame work duplicated or missed'
    return dict(frames=len(frames), palette_bytes_per_frame=88,
                max_irq_dots=max(e['max_irq_dots'] for e in frames),
                bad_mode_writes=0, bad_palette_indexes=0, register_or_bank_errors=0)


def open_owner(driver, repo, owner, unlocked):
    reach(driver, repo, 'Pokedex_UpdateOptionScreen')
    row = owner if unlocked or owner < 2 else owner - 1
    current = driver.command('ui')['footer_cursor']
    for _ in range(abs(row-current)):
        press(driver, 'down' if row > current else 'up')
    press(driver, 'a')
    label = {0:'Pokedex_UpdateMainScreen',1:'Pokedex_UpdateMainScreen',
             2:'Pokedex_UpdateUnownMode',3:'PokedexMovesMode_Update'}[owner]
    reach(driver, repo, label)
    driver.run(frames=5)


def owner_signature(driver, owner):
    ui = driver.command('ui')
    keys = ['map','attrs','scx','scy','wx','wy']
    if ui['wx'] < 167:
        keys += ['window','window_attrs']
    if owner in (0,1):
        keys += ['picture','legacy_gfx']
    if owner == 2:
        keys += ['picture']
    # Compare only palette slots actually assigned to visible background cells.
    attrs = bytes.fromhex(ui['attrs'])
    if ui['wx'] < 167:
        attrs += bytes.fromhex(ui['window_attrs'])
    palettes = bytes.fromhex(ui['palettes'])
    result = {key:ui[key] for key in keys}
    if owner == 2:
        # The generic UI picture samples x=1,y=1. Unown is at x=6,y=5;
        # its 49 base tiles are bank 0 $9000, not that unrelated corner crop.
        result['picture'] = driver.command('inspectvram 0 36864 784')['bytes']
        result['unown_font'] = driver.command('inspectvram 1 35664 432')['bytes']
        result['unown_blank'] = driver.command('inspectvram 1 37664 16')['bytes']
    if owner == 3:
        tiles = bytearray.fromhex(result['map'])
        for row in range(1,9):
            tiles[row*21+6] = 0
        result['map'] = tiles.hex()
    if owner == 0:
        window = bytearray.fromhex(result['window'])
        for y in (5,6,9,10,13,14):
            for x in (1,2,9,10):
                window[y*20+x] = 0
        result['window'] = window.hex()
    result['used_bg_palettes'] = [palettes[p*8:p*8+8].hex() for p in sorted({a&7 for a in attrs})]
    return result


def returns(repo, core, output):
    records = []
    playback = []
    assets = {}
    config = dict(rom=str(repo.rom_path),sym=str(repo.rom_path.with_suffix('.sym')),
                  battery=str(output.parent / 'pokecrystal-dex-types.sav'))
    for unlocked in (False,True):
        for presentation in (0,1):
            for order in (0,1,2):
                tag = f'{int(unlocked)}-{presentation}-{order}'
                battery = output / f'return-{tag}.sav'
                private_battery(config,battery,presentation=presentation,
                                order_mode=order,unown_unlocked=unlocked)
                driver = Driver(core,repo.rom_path,BOOT,battery,output / f'return-{tag}.log')
                try:
                    driver.command('rawcolor')
                    bootstrap(driver,expected_mode=order)
                    seen = memory(driver,repo,'wMoveDiscoverySeen',64)
                    for owner in ((0,1,2,3) if unlocked else (0,1,3)):
                        press(driver,'select')
                        open_owner(driver,repo,owner,unlocked)
                        before = owner_signature(driver,owner)
                        if owner in (0,1):
                            raw = memory(driver,repo,'wPokedexOrder',746)
                            active_order = [int.from_bytes(raw[i:i+2],'little') for i in range(0,746,2)]
                        # Return through the ordinary Mode menu to enter Matchups.
                        press(driver,'select' if owner in (0,1,3) else 'b')
                        reach(driver,repo,'Pokedex_UpdateOptionScreen')
                        row = 4 if unlocked else 3
                        current = driver.command('ui')['footer_cursor']
                        for _ in range(abs(row-current)):
                            press(driver,'down' if row > current else 'up')
                        press(driver,'a')
                        reach(driver,repo,'PokedexTypes_Update')
                        driver.run(frames=5)
                        press(driver,'left')
                        press(driver,'up')
                        press(driver,'select' if owner & 1 else 'b')
                        reach(driver,repo,'Pokedex_UpdateOptionScreen')
                        driver.run(frames=5)
                        assert not audit_menu(driver.command('ui'),unlocked,row)
                        assert memory(driver,repo,'hLCDCPointer',1) == b'\0'
                        open_owner(driver,repo,owner,unlocked)
                        after = owner_signature(driver,owner)
                        (output / 'return-owner-compare.json').write_text(json.dumps(dict(before=before,after=after),indent=2)+'\n')
                        assert before == after, (tag,owner,[k for k in before if before[k]!=after[k]])
                        if owner in (0,1):
                            assert memory(driver,repo,'wPokedexOrder',746) == raw
                            listing_audit(driver,repo,active_order)
                            index = driver.command('peek')['index']
                            name = species()[active_order[index]-1].lower()
                            if name not in assets:
                                assets[name] = repo.load([name])[0]
                            driver.events.clear()
                            driver.command('audit 1')
                            accepted = driver.run(('accept',),frames=180,key='a')
                            assert accepted['hit'] == 'accept'
                            final = settle(driver)
                            result = playback_audit(assets[name],accepted,driver.events,final,
                                                    cold=False,expected_double_speed=1)
                            assert not result['issues'], (tag,owner,result)
                            assert not description_audit(repo,driver.command('ui'))
                            driver.command('audit 0')
                            press(driver,'b')
                            reach(driver,repo,'Pokedex_UpdateMainScreen')
                            driver.run(frames=5)
                            playback.append(dict(tag=tag,owner=owner,species=name,passed=True))
                        assert memory(driver,repo,'wMoveDiscoverySeen',64) == seen
                        capture(driver,output / f'return-{tag}-owner-{owner}.png')
                        records.append(dict(unlocked=unlocked,presentation=presentation,
                                            order=order,owner=owner,graphics_identical=True))
                        (output / 'return-paths.json').write_text(json.dumps(records,indent=2)+'\n')
                        if owner in (2,3):
                            press(driver,'b')
                            reach(driver,repo,'Pokedex_UpdateOptionScreen')
                            press(driver,'b')
                            reach(driver,repo,'Pokedex_UpdateMainScreen')
                            driver.run(frames=5)
                    # Cancel the Mode menu back to each listing, then close and reopen.
                    enter_types(driver,repo,unlocked)
                    press(driver,'b')
                    reach(driver,repo,'Pokedex_UpdateOptionScreen')
                    press(driver,'b')
                    reach(driver,repo,'Pokedex_UpdateMainScreen')
                    driver.run(frames=5)
                    current = driver.command('peek')
                    assert current['mode'] == order
                    press(driver,'b')
                    reach(driver,repo,'StartMenu.loop')
                    driver.run(frames=5)
                    # Close the Start menu too, then reopen it through fresh input.
                    driver.run(frames=12,key='b')
                    driver.run(frames=8)
                    reach(driver,repo,'HandleMapTimeAndJoypad')
                    driver.run(frames=8)
                    driver.run(('start_menu',),frames=180,key='start')
                    driver.run(frames=5)
                    assert driver.command('peek')['menu'] == 1
                    driver.run(frames=12,key='a')
                    driver.run(frames=8)
                    reach(driver,repo,'Pokedex_UpdateMainScreen')
                    driver.run(frames=5)
                    assert driver.command('peek')['mode'] == order
                except Exception:
                    driver.command(f'save {output}/return-failure.s0')
                    capture(driver,output / 'return-failure.png')
                    (output / 'return-failure-events.json').write_text(json.dumps(driver.events,indent=2)+'\n')
                    raise
                finally:
                    driver.close()
    (output / 'return-paths.json').write_text(json.dumps(records,indent=2)+'\n')
    (output / 'return-playback.json').write_text(json.dumps(playback,indent=2)+'\n')
    return dict(owner_reentries=len(records),close_and_reopen=12,locked_unlocked=True,
                modern_legacy=True,all_pokemon_sort_orders=True,selected_playbacks=len(playback))


def battle_chart(repo, oracle, output):
    from .move_persistence import core as unit_core, boot as unit_boot, call
    core = unit_core(output.parent,stem='pokecrystal-dex-types',target_root=output)
    config = dict(core=str(core),rom=str(repo.rom_path),symbols=repo.symbols)
    battery = output / 'battle-chart.sav'
    shutil.copy2(output.parent / 'pokecrystal-dex-types.sav',battery)
    driver = unit_boot(config,battery,output / 'battle-chart.log')
    records = []
    def fixture(label, raw, delta=0):
        bank, address = repo.symbols[label]
        driver.command(f'fixture {bank} {address+delta} {raw.hex()}')
    try:
        fixture('wEnemySubStatus1',bytes(5))
        fixture('wPlayerSubStatus1',bytes(5))
        fixture('wPlayerMoveStruct',bytes(8))
        fixture('wEnemyMoveStruct',bytes(8))
        fixture('wPlayerAbility',bytes(2))
        for turn in (0,1):
            driver.command(f'hram {repo.symbols["hBattleTurn"][1]} {turn}')
            for attack, id_ in enumerate(oracle.ids):
                fixture('wEnemyMoveStruct' if turn else 'wPlayerMoveStruct',bytes([id_]),3)
                for defense, target in enumerate(oracle.ids):
                    fixture('wBattleMonType1' if turn else 'wEnemyMonType1',bytes([target,target]))
                    result = call(driver,repo.symbols,'BattleCheckTypeMatchup')
                    bank, at = repo.symbols['wTypeMatchup']
                    factor = bytes.fromhex(driver.command(f'read {bank} {at} 1')['bytes'])[0]
                    assert factor == oracle.matrix[attack][defense]*10, (turn,attack,defense,factor)
                    records.append(dict(turn=turn,attack=attack,defense=defense,factor=factor))
        # Every unordered dual-type combination: check the game's integer
        # multiplier semantics against the independent workbook oracle.
        driver.command(f'hram {repo.symbols["hBattleTurn"][1]} 0')
        for attack,id_ in enumerate(oracle.ids):
            fixture('wPlayerMoveStruct',bytes([id_]),3)
            for first in range(18):
                for second in range(first+1,18):
                    fixture('wEnemyMonType1',bytes([oracle.ids[first],oracle.ids[second]]))
                    call(driver,repo.symbols,'BattleCheckTypeMatchup')
                    bank,at = repo.symbols['wTypeMatchup']
                    actual = bytes.fromhex(driver.command(f'read {bank} {at} 1')['bytes'])[0]
                    expected = int(oracle.matrix[attack][first]*oracle.matrix[attack][second]*10)
                    assert actual == expected, (attack,first,second,actual,expected)
        # Identified targets bypass only the original Normal/Fighting-to-Ghost
        # entries; the new Ground immunity and Electric self-immunity remain.
        fixture('wEnemySubStatus1',bytes([8]))
        for attacker,defender,expected in (('Normal','Ghost',10),('Fighting','Ghost',10),
                                          ('Ground','Ghost',0),('Electric','Electric',0)):
            attack,defense = oracle.names.index(attacker),oracle.names.index(defender)
            fixture('wPlayerMoveStruct',bytes([oracle.ids[attack]]),3)
            fixture('wEnemyMonType1',bytes([oracle.ids[defense]])*2)
            call(driver,repo.symbols,'BattleCheckTypeMatchup')
            bank,at=repo.symbols['wTypeMatchup']
            assert bytes.fromhex(driver.command(f'read {bank} {at} 1')['bytes'])[0] == expected
    finally:
        driver.close()
    (output / 'battle-chart-cells.json').write_text(json.dumps(records,indent=2)+'\n')
    return dict(single_type_calls=648,dual_type_calls=2754,identified_target_cases=4)


def transitions(repo,core,output):
    target = output / 'transitions'
    target.mkdir(exist_ok=True)
    driver = Driver(core,repo.rom_path,BOOT,output / 'battery.sav',target / 'trace.log')
    rows = []
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        press(driver,'select')
        reach(driver,repo,'Pokedex_UpdateOptionScreen')
        for _ in range(4):
            press(driver,'down')
        driver.command(f'save {target}/menu.s0')
        driver.command(f'perfpixels save {target}/menu.pixels')
        for phase in range(8):
            driver.command(f'load {target}/menu.s0')
            driver.command(f'perfpixels load {target}/menu.pixels')
            driver.run(frames=phase/8)
            driver.events.clear()
            driver.command('perf 1')
            driver.command(f'perfimages {target}/entry-{phase}')
            press(driver,'a')
            reach(driver,repo,'PokedexTypes_Update')
            driver.run(frames=4)
            driver.command('perfimages -')
            frames = [e for e in driver.events if e['event']=='perf_frame']
            assert not any(e['white']==23040 for e in frames), ('entry_white_flash',phase)
            assert all(e['lcdc']&128 for e in frames), ('entry_lcd_disabled',phase)
            rows.append(dict(direction='entry',phase=phase,frames=len(frames),white_flash=False))
            driver.events.clear()
            driver.command(f'perfimages {target}/exit-{phase}')
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateOptionScreen')
            driver.run(frames=4)
            driver.command('perfimages -')
            frames = [e for e in driver.events if e['event']=='perf_frame']
            assert not any(e['white']==23040 for e in frames), ('exit_white_flash',phase)
            assert all(e['lcdc']&128 for e in frames), ('exit_lcd_disabled',phase)
            rows.append(dict(direction='exit',phase=phase,frames=len(frames),white_flash=False))
    finally:
        driver.close()
    for path in target.glob('*.ppm'):
        with Image.open(path) as image:
            image.save(path.with_suffix('.png'))
        path.unlink()
    (target / 'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    return dict(entry_phases=8,exit_phases=8,white_flashes=0)


def display_hash(raw):
    hash_ = 2166136261
    for at in range(0,len(raw),3):
        for value in (raw[at+2],raw[at+1],raw[at]):
            hash_ = ((hash_ ^ value) * 16777619) & 0xffffffff
    return hash_


def atomic_audit(events,legal):
    frames = [e for e in events if e['event']=='perf_frame']
    assert frames and all(e['full'] in legal for e in frames), 'Mixed or malformed display frame'
    return len(frames)


def run(output, smoke, model):
    target = output / 'type-tests'
    if model != 'E':
        target = target / f'cgb-{model}'
    target.mkdir(parents=True,exist_ok=True)
    repo = Repository(ROOT, output / 'pokecrystal-dex-types.gbc',
                      output / 'pokecrystal-dex-types.sym')
    flags = ['-DDEX_TYPES_TRACE',f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}',
             f'-DS_wPokedexWRAM0Scratch={repo.symbols["wPokedexWRAM0Scratch"][1]}',
             f'-DS_hLCDCPointer={repo.symbols["hLCDCPointer"][1]}',
             f'-DP_LCD_DONE={repo.symbols["LCD.done"][1]}']
    if 'PokedexTypes_VBlank' in repo.symbols:
        sound = 'PokedexTypes_AudioUpdate' if 'PokedexTypes_AudioUpdate' in repo.symbols else '_UpdateSound'
        flags += ['-DDEX_TYPES_MODE7_TRACE',
                  f'-DP_TYPES_FRAME_ENTRY={repo.symbols["VBlank"][1]}',
                  f'-DP_TYPES_FRAME_RETURN={repo.symbols["VBlank.return"][1]}',
                  f'-DP_TYPES_SOUND={repo.symbols[sound][1]}',
                  f'-DP_TYPES_SOUND_BANK={repo.symbols[sound][0]}',
                  f'-DP_TYPES_JOYPAD={repo.symbols["UpdateJoypad"][1]}',
                  f'-DP_TYPES_CLOCK={repo.symbols["GameTimer"][1]}']
    else:
        flags += [f'-DP_TYPES_LCD={repo.symbols["PokedexTypes_LCD"][1]}']
    # The generic performance include supplies read-only bank/VRAM inspectors.
    core = performance_core(repo, target, {'types_commit':('PokedexTypes_CommitLower',True),
                                         'types_vblank':('VBlank',True),
                                         'types_clock':('GameTimer',True)},extra_flags=flags)
    battery = target / 'battery.sav'
    private_battery(dict(rom=str(repo.rom_path), sym=str(output / 'pokecrystal-dex-types.sym'),
                         battery=str(output / 'pokecrystal-dex-types.sav')),
                    battery, presentation=0, order_mode=0, unown_unlocked=True)
    driver = Driver(core, output / 'pokecrystal-dex-types.gbc', BOOT, battery, target / 'trace.log')
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        enter_types(driver, repo, True)
        oracle = Oracle(repo)
        pixels = oracle.audit(driver, 0, capture(driver, target / 'bug.png'))
        if not smoke:
            driver.events.clear()
            driver.command('perf 1')
            checkpoints = []
            for i in range(18):
                driver.command(f'save {target}/type-{i}.s0')
                driver.command(f'perfpixels save {target}/type-{i}.pixels')
                image = capture(driver, target / f'{oracle.names[i].lower()}.png')
                pixels += oracle.audit(driver, i, image)
                checkpoints.append(image.tobytes())
                # Both phases are legal; only the single OBJ arrow disappears.
                hidden = image.copy()
                x, y = 8+(i%3)*48, 8+(i//3)*14
                hidden.paste((41,41,41),(x,y,x+8,y+8))
                checkpoints.append(hidden.tobytes())
                visible = hidden.copy()
                font = offset(repo.symbols['Font']) + (0xed-0x80)*8
                for dy,bits in enumerate(repo.rom[font:font+8]):
                    for dx in range(8):
                        if bits & (0x80 >> dx):
                            visible.putpixel((x+dx,y+dy),(255,255,255))
                checkpoints.append(visible.tobytes())
                if i < 17:
                    press(driver, 'down' if i % 3 == 2 else 'right')
                    # Down preserves columns; start the following row at its left edge.
                    if i % 3 == 2:
                        press(driver, 'right')
            (target / 'selection-events.json').write_text(json.dumps(driver.events,indent=2)+'\n')
            raster = trace_audit(driver.events)
            legal = {display_hash(raw) for raw in checkpoints}
            atomic_frames = atomic_audit(driver.events,legal)
            navigation = 0
            driver.events.clear()
            for i in range(18):
                for direction in ('up','down','left','right'):
                    driver.command(f'load {target}/type-{i}.s0')
                    driver.command(f'perfpixels load {target}/type-{i}.pixels')
                    row, col = divmod(i,3)
                    dest = {'up':((row-1)%6)*3+col, 'down':((row+1)%6)*3+col,
                            'left':row*3+(col-1)%3, 'right':row*3+(col+1)%3}[direction]
                    press(driver, direction)
                    pixels += oracle.audit(driver, dest, capture(driver, target / 'navigation.png'))
                    navigation += 1
            atomic_frames += atomic_audit(driver.events,legal)
            driver.events.clear()
            for phase in range(8):
                for direction,dest in (('right',1),('left',2),('up',15),('down',3)):
                    driver.command(f'load {target}/type-0.s0')
                    driver.command(f'perfpixels load {target}/type-0.pixels')
                    driver.run(frames=phase/8)
                    press(driver,direction)
                    pixels += oracle.audit(driver,dest,capture(driver,target / 'phase.png'))
            atomic_frames += atomic_audit(driver.events,legal)
            for direction in ('up','down','left','right'):
                driver.events.clear()
                driver.run(frames=180,key=direction)
                driver.run(frames=4)
                atomic_frames += atomic_audit(driver.events,legal)
                trace_audit(driver.events)
            driver.command(f'load {target}/type-0.s0')
            driver.command(f'perfpixels load {target}/type-0.pixels')
            press(driver, 'a')
            press(driver, 'start')
            assert driver.command('peek')['jumptable'] == 22
            oracle.audit(driver, 0, capture(driver, target / 'ignored-confirm.png'))
            driver.events.clear()
            driver.run(frames=1800 if model=='E' else 180)
            idle = trace_audit(driver.events)
            atomic_frames += atomic_audit(driver.events,legal)
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateOptionScreen')
            driver.run(frames=4)
            assert not audit_menu(driver.command('ui'), True, 4)
            capture(driver, target / 'return-mode-menu.png')
            press(driver, 'b')
            reach(driver, repo, 'Pokedex_UpdateMainScreen')
            driver.run(frames=5)
            order = [int.from_bytes(repo.rom[offset(repo.symbols['NewPokedexOrder'])+i*2:
                                           offset(repo.symbols['NewPokedexOrder'])+i*2+2], 'little')
                     for i in range(373)]
            listing_audit(driver, repo, order)
            capture(driver, target / 'return-modern.png')
            summary = dict(model=model,rom_sha256=sha256(repo.rom),chart_cells=324,chart_records=oracle.records,selections=18,
                           navigation_cases=navigation,badge_pixels_checked=pixels,
                           raster=raster,idle=idle,return_modern=True,input_phases=32,
                           legal_display_frames=atomic_frames,held_direction_frames=720)
            summary['immunity_sections'] = [name for i,name in enumerate(oracle.names)
                                           if oracle.lists(i)[2]]
            summary['steel_combined_resistances'] = len(oracle.lists(16)[1])
            summary['outer_frame_matches_mockup'] = True
            if model == 'E':
                summary['transitions'] = transitions(repo,core,target)
                summary['return_paths'] = returns(repo,core,target)
                summary['battle_chart'] = battle_chart(repo,oracle,target)
            (target / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            print(json.dumps(summary,indent=2),flush=True)
    finally:
        driver.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--model',choices=('0','A','B','C','D','E'),default='E')
    parser.add_argument('--all-models',action='store_true')
    args = parser.parse_args()
    for model in (('0','A','B','C','D','E') if args.all_models else (args.model,)):
        run(args.output,args.smoke,model)
