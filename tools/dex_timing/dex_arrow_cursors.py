"""Shared blink contract and normal-input visual coverage for every Dex arrow."""
import argparse
import json
import shutil
from pathlib import Path

from .assets import Repository, offset
from .cold_listing import Driver, ROOT, bootstrap
from .performance import core as performance_core
from .type_matchups import BOOT, reach, press, capture, memory, enter_types
from .legacy_listing import private_battery
from .listing_options import modal_audit
from .moves_mode import enter, open_sort
from .moves_search import WORK, open_search, row, search, finish_text, keyboard_audit
from .description_ui import settle


def helpers(repo, output, battery):
    from .move_persistence import core, boot, call
    executable = core(output.parent, stem='pokecrystal-dex-types', target_root=output)
    driver = boot(dict(core=str(executable), rom=str(repo.rom_path), symbols=repo.symbols),
                  battery, output / 'helpers.log')
    bank, address = repo.symbols['wDexArrowCursorBlinkCounter']
    count = 0
    try:
        for wram in range(1,8):
            driver.command(f'io 65392 {wram}')
            for initial in range(256):
                driver.command(f'fixture {bank} {address} {initial:02x}')
                result = call(driver, repo.symbols, 'Pokedex_AdvanceArrowCursorBlink', index=0x55aa)
                actual = bytes.fromhex(driver.command(f'read {bank} {address} 1')['bytes'])[0]
                assert actual == (initial+1)&255
                assert bool(result['af']&0x80) == (not initial&8)
                assert (result['bc'],result['de'],result['svbk']&7) == (0xa55a,0x55aa,wram)
                call(driver, repo.symbols, 'Pokedex_ResetArrowCursorBlink')
                assert bytes.fromhex(driver.command(f'read {bank} {address} 1')['bytes']) == b'\0'
                count += 1
    finally:
        driver.close()
    return dict(counter_bank_cases=count, counter_wrap=True, reset_visible=True,
                bc_de_wram_preserved=True)


def run(output):
    target = output / 'arrow-tests'
    target.mkdir(parents=True,exist_ok=True)
    repo = Repository(ROOT, output / 'pokecrystal-dex-types.gbc', output / 'pokecrystal-dex-types.sym')
    executable = performance_core(repo,target,{})
    seed = target / 'battery.sav'
    shutil.copy2(output / 'pokecrystal-dex-types.sav',seed)
    from move_discovery_assets import seed_records, move_bitmap
    seed.write_bytes(seed_records(seed.read_bytes(), repo.symbols, move_bitmap(range(1, 334))))
    unit = helpers(repo,target,seed)
    records = []
    font = offset(repo.symbols['Font']) + (0xed-0x80)*8
    glyph = {(x,y) for y,bits in enumerate(repo.rom[font:font+8])
             for x in range(8) if bits&(0x80>>x)}

    def observe(driver,name,rect,shift=0,audit=None):
        states = {}
        phases = []
        counters = []
        for frame in range(64):
            driver.run(frames=1)
            image = capture(driver,target / 'frame.png')
            crop = image.crop(rect)
            key = crop.tobytes()
            if key not in states:
                states[key] = image.copy()
            phases.append(key)
            counters.append(memory(driver,repo,'wDexArrowCursorBlinkCounter',1)[0])
            if audit:
                audit()
        if len(states) != 2:
            for index, image in enumerate(states.values()):
                image.save(target / f'{name}-unexpected-{index}.png')
            (target / f'{name}-unexpected.json').write_text(json.dumps(dict(rect=rect,
                counters=counters, ui=driver.command('ui')), indent=2) + '\n')
        assert len(states) == 2, (name,'cursor_phases',len(states),counters)
        images = sorted(states.values(),key=lambda im:sum(c==(255,255,255) for c in im.crop(rect).get_flattened_data()))
        off,on = images
        off_crop,on_crop = off.crop(rect),on.crop(rect)
        changed = {(x,y) for y in range(on_crop.height) for x in range(on_crop.width)
                   if on_crop.getpixel((x,y)) != off_crop.getpixel((x,y))}
        assert changed == {(x+shift,y) for x,y in glyph}, (name,'arrow_shape',changed,glyph,rect)
        assert all(on_crop.getpixel((x,y))==(255,255,255) for x,y in changed)
        # Instruction-bounded frame budgets can straddle an extra owner loop.
        ticks = [(b-a)&255 for a,b in zip(counters,counters[1:])]
        assert max(ticks) <= 2 and 60 <= sum(ticks) <= 68, (name,'idle_tick',counters)
        on.save(target / f'{name}-on.png')
        off.save(target / f'{name}-off.png')
        transitions = sum(a!=b for a,b in zip(phases,phases[1:]))
        assert transitions >= 6, (name,transitions)
        records.append(dict(location=name,frames=64,phases=2,shared_tick=True,
                            arrow_pixels=len(changed),static_surroundings=True))
        (target / 'locations.json').write_text(json.dumps(records,indent=2)+'\n')

    config = dict(rom=str(repo.rom_path),sym=str(repo.rom_path.with_suffix('.sym')),battery=str(seed))
    for presentation in (0,1):
        battery = target / f'listing-{presentation}.sav'
        private_battery(config,battery,presentation=presentation,order_mode=0,unown_unlocked=True)
        driver = Driver(executable,repo.rom_path,BOOT,battery,target / f'listing-{presentation}.log')
        try:
            driver.command('rawcolor')
            bootstrap(driver)
            press(driver,'start')
            reach(driver,repo,'PokedexPopover_Update')
            x = driver.command('ui')['wx']-7+16
            y = (8-presentation)*8
            observe(driver,f'{("modern","legacy")[presentation]}-options',(x,y,x+8,y+8),
                    audit=lambda:modal_audit(driver,0,repo))
            press(driver,'down')
            observe(driver,f'{("modern","legacy")[presentation]}-options-moved',(x,y+16,x+8,y+24),
                    audit=lambda:modal_audit(driver,0,repo))
            press(driver,'up')
            press(driver,'a')
            x = driver.command('ui')['wx']-7+8
            y = (7-presentation)*8
            observe(driver,f'{("modern","legacy")[presentation]}-sort',(x,y,x+(16 if not presentation else 8),y+8),
                    shift=3 if not presentation else 0,audit=lambda:modal_audit(driver,1,repo))
            press(driver,'down')
            observe(driver,f'{("modern","legacy")[presentation]}-sort-moved',
                    (x,y+16,x+(16 if not presentation else 8),y+24),shift=3 if not presentation else 0,
                    audit=lambda:modal_audit(driver,1,repo))
            press(driver,'b')
            press(driver,'down')
            press(driver,'a')
            reach(driver,repo,'Pokedex_UpdateSearchScreen')
            observe(driver,f'pokemon-search-{presentation}',(8,32,16,40))
            for option,(x,y) in enumerate(((8,48),(16,104),(16,120)),1):
                press(driver,'down')
                observe(driver,f'pokemon-search-row-{option}-{presentation}',(x,y,x+8,y+8))
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateMainScreen')
            press(driver,'select')
            reach(driver,repo,'Pokedex_UpdateOptionScreen')
            observe(driver,f'modes-{presentation}',(16,24+presentation*16,24,32+presentation*16))
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateMainScreen')
            press(driver,'a')
            reach(driver,repo,'PokedexSelectedMon_Update')
            settle(driver)
            driver.run(frames=120)
            observe(driver,f'detail-footer-{presentation}',(3,136,11,144))
            for option,x in enumerate((43,83,115),1):
                press(driver,'right')
                observe(driver,f'detail-footer-{option}-{presentation}',(x,136,x+8,144))
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateMainScreen')
            enter_types(driver,repo,True)
            observe(driver,f'types-{presentation}',(8,8,16,16))
            press(driver,'right')
            observe(driver,f'types-moved-{presentation}',(56,8,64,16))
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateOptionScreen')
            press(driver,'b')
            reach(driver,repo,'Pokedex_UpdateMainScreen')
            enter(driver,repo,True)
            observe(driver,f'moves-list-{presentation}',(43,8,51,16))
            press(driver,'down')
            observe(driver,f'moves-list-moved-{presentation}',(43,16,51,24))
            press(driver,'start')
            reach(driver,repo,'PokedexMovesSearch_OptionsUpdate')
            observe(driver,f'moves-options-{presentation}',(51,24,59,32))
            press(driver,'down')
            observe(driver,f'moves-options-moved-{presentation}',(51,40,59,48))
            press(driver,'up')
            press(driver,'a')
            reach(driver,repo,'PokedexMovesMode_SortUpdate')
            y = 24+driver.command('ui')['footer_cursor']*16
            observe(driver,f'moves-sort-{presentation}',(51,y,59,y+8))
            press(driver,'down')
            y = 24+driver.command('ui')['footer_cursor']*16
            observe(driver,f'moves-sort-moved-{presentation}',(51,y,59,y+8))
            press(driver,'b')
            reach(driver,repo,'PokedexMovesMode_Update')
            open_search(driver,repo)
            observe(driver,f'moves-search-{presentation}',(8,32,16,40))
            for option,(x,y) in enumerate(((8,48),(16,104),(16,120)),1):
                row(driver,repo,option)
                observe(driver,f'moves-search-row-{option}-{presentation}',(x,y,x+8,y+8))
            row(driver,repo,1)
            press(driver,'a')
            reach(driver,repo,'PokedexMovesSearch_TextUpdate')
            driver.run(frames=20)
            keyboard_audit(driver,repo)
            finish_text(driver,repo)
            search(driver,repo)
            count = int.from_bytes(memory(driver, repo, 'wPokedexInfoGFX', 2,
                delta=WORK + 1 - repo.symbols['wPokedexInfoGFX'][1]), 'little')
            assert count, 'No seen Bug moves in the declared all-seen fixture'
            observe(driver,f'moves-results-{presentation}',(43,8,51,16))
        finally:
            driver.close()
    summary = dict(helpers=unit,locations=len(records),idle_frames=sum(r['frames'] for r in records),
                   modern_and_legacy=True,keyboard_box_unchanged=True,results=records)
    (target / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT / 'build/dex-types-cursors-20261011')
    run(parser.parse_args().output)
