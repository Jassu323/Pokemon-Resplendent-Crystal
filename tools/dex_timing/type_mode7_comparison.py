"""Compare private mode-7 Type owners using native buttons and pixel evidence."""
import argparse
import json
from pathlib import Path
import statistics
from collections import defaultdict

from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, bootstrap, FRAME
from .performance import core
from .type_matchups import BOOT, enter_types, memory, press, reach, capture, Oracle, trace_audit, display_hash, atomic_audit
from tools.pokedex_info_assets import constants

BASE = ROOT / 'build/dex-types-mode7-20261012'


def diagnose(variant):
    output = BASE / variant
    target = output / 'mode7-diagnostic'
    repo = Repository(ROOT, output / 'pokecrystal-dex-types.gbc',
                      output / 'pokecrystal-dex-types.sym')
    executable = core(repo, target, {
        'type_vblank': ('PokedexTypes_VBlank', True),
        'type_draw': ('PokedexTypes_DrawSelection', True),
        'type_yield': ('PokedexTypes_Yield', True),
        'sound': ('_UpdateSound', True)})
    driver = Driver(executable, repo.rom_path, BOOT, output / 'pokecrystal-dex-types.sav', target / 'trace.log')
    try:
        bootstrap(driver)
        driver.command('perf 1')
        enter_types(driver, repo, True)
        report = dict(state=memory(driver, repo, 'wPokedexWRAM0Scratch', 224).hex(),
                      private=memory(driver, repo, 'wPokedexWRAM0Scratch', 9, 0x180).hex(),
                      page=memory(driver, repo, 'wPokedexWRAM0Scratch', 96, 0x200).hex(),
                      accents=memory(driver, repo, 'wPokedexWRAM0Scratch', 36, 0x1a0).hex(),
                      owners={k: memory(driver, repo, k, 1).hex()
                              for k in ('hVBlank', 'hLCDCPointer', 'hLYOverrideStart')},
                      cpu=driver.command('peek'),
                      interrupts=driver.command('perfram 0 65535 1'),
                      events=driver.events)
        (target / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'events'}, indent=2))
    finally:
        driver.close()


def points(repo=None):
    return {'type_prepare': ('PokedexTypes_PrepareLower', True),
            'type_draw': ('PokedexTypes_DrawSelection', True),
            'type_load': ('PokedexTypes_LoadRecord', True),
            'type_accept': ('PokedexTypes_Update.move', False),
            'type_publish': ('PokedexTypes_CommitLower', True),
            'type_vblank': ('VBlank', True),
            'sound': ('PokedexTypes_AudioUpdate' if repo and 'PokedexTypes_AudioUpdate' in repo.symbols else '_UpdateSound', True),
            'type_enter': ('PokedexTypes_Initialize', False)}


def costs(events):
    groups = defaultdict(list)
    for row in events:
        if row['event'] == 'perf_cost':
            groups[row['name']].append(row['elapsed'])
    return {name: dict(calls=len(rows), min_ms=min(rows)*1000/4194304,
                       median_ms=statistics.median(rows)*1000/4194304,
                       max_ms=max(rows)*1000/4194304) for name, rows in groups.items()}


def bug_hashes(repo, image, index=0):
    x,y = 8+index%3*48,8+index//3*14
    hidden = image.copy()
    hidden.paste((41,41,41),(x,y,x+8,y+8))
    visible = hidden.copy()
    font = offset(repo.symbols['Font']) + (0xed-0x80)*8
    for dy,bits in enumerate(repo.rom[font:font+8]):
        for dx in range(8):
            if bits & (0x80 >> dx):
                visible.putpixel((x+dx,y+dy),(255,255,255))
    return {display_hash(view.tobytes()) for view in (hidden,visible)}


def measure(variant):
    output = BASE / variant
    target = output / 'comparison'
    repo = Repository(output / 'candidate', output / 'pokecrystal-dex-types.gbc',
                      output / 'pokecrystal-dex-types.sym')
    executable = core(repo, target, points(repo))
    driver = Driver(executable, repo.rom_path, BOOT, output / 'pokecrystal-dex-types.sav', target / 'trace.log')
    rows, entries = [], []
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        press(driver, 'select')
        reach(driver, repo, 'Pokedex_UpdateOptionScreen')
        while driver.command('ui')['footer_cursor'] != 4:
            press(driver, 'down')
        driver.command(f'save {target}/menu.s0')
        driver.command(f'perfpixels save {target}/menu.pixels')
        for phase in range(8):
            driver.command(f'load {target}/menu.s0')
            driver.command(f'perfpixels load {target}/menu.pixels')
            driver.run(frames=phase/8)
            driver.events.clear()
            start = driver.command('perf 1')['t']
            driver.run(frames=30, key='a')
            driver.run(frames=4)
            final = driver.command('perf 0')
            image = capture(driver, target / 'entry.png')
            Oracle(repo).audit(driver, 0, image)
            legal = bug_hashes(repo,image)
            frames = [e for e in driver.events if e['event'] == 'perf_frame' and e['full'] in legal]
            assert frames
            entries.append(dict(phase=phase, complete_ms=(frames[0]['t']-start)*1000/4194304,
                                costs=costs(driver.events)))
        for index in range(18):
            for direction in ('up','down','left','right'):
                row, col = divmod(index, 3)
                dest = {'up':((row-1)%6)*3+col, 'down':((row+1)%6)*3+col,
                        'left':row*3+(col-1)%3, 'right':row*3+(col+1)%3}[direction]
                for phase in range(8):
                    driver.command(f'load {output}/type-tests/type-{index}.s0')
                    driver.command(f'perfpixels load {output}/type-tests/type-{index}.pixels')
                    driver.run(frames=phase/8)
                    driver.events.clear()
                    start = driver.command('perf 1')['t']
                    press(driver, direction)
                    final = driver.command('perf 0')
                    Oracle(repo).audit(driver, dest, capture(driver, target / 'selection.png'))
                    accepted = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'type_accept']
                    published = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'type_publish']
                    frames = [e for e in driver.events if e['event'] == 'perf_frame' and e['lower'] == final['lower']]
                    assert len(accepted) == len(published) == 1 and frames
                    rows.append(dict(index=index,direction=direction,phase=phase,
                        accept_ms=(accepted[0]['t']-start)*1000/4194304,
                        publish_ms=(published[0]['t']-start)*1000/4194304,
                        complete_ms=(next(e for e in frames if e['t'] >= published[0]['t'])['t']-start)*1000/4194304,
                        costs=costs(driver.events)))
    finally:
        driver.close()
    def summary(records, key):
        values = [r[key] for r in records]
        return dict(min_ms=min(values),median_ms=statistics.median(values),max_ms=max(values))
    record = dict(variant=variant,selection_cases=len(rows),entry_cases=len(entries),
                  entry=summary(entries,'complete_ms'),
                  selection={key:summary(rows,key) for key in ('accept_ms','publish_ms','complete_ms')},
                  rows=rows,entries=entries)
    (target / 'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('rows','entries')},indent=2))


def audio(variant, navigation=False):
    output = BASE / variant
    target = output / ('audio-navigation' if navigation else 'audio-stress')
    repo = Repository(output / 'candidate', output / 'pokecrystal-dex-types.gbc',
                      output / 'pokecrystal-dex-types.sym')
    sound = 'PokedexTypes_AudioUpdate' if 'PokedexTypes_AudioUpdate' in repo.symbols else '_UpdateSound'
    flags = ['-DDEX_TYPES_TRACE','-DDEX_TYPES_MODE7_TRACE','-DDEX_TYPES_AUDIO_FIXTURE',
             f'-DP_TYPES_OWNER={repo.symbols["PokedexTypes_Update.owner_loop"][1]}',
             f'-DP_TYPES_OWNER_BANK={repo.symbols["PokedexTypes_Update.owner_loop"][0]}',
             f'-DS_wPokedexWRAM0Scratch={repo.symbols["wPokedexWRAM0Scratch"][1]}',
             f'-DS_hLCDCPointer={repo.symbols["hLCDCPointer"][1]}',
             f'-DP_TYPES_FRAME_ENTRY={repo.symbols["VBlank"][1]}',
             f'-DP_TYPES_FRAME_RETURN={repo.symbols["VBlank.return"][1]}',
             f'-DP_TYPES_SOUND={repo.symbols[sound][1]}',
             f'-DP_TYPES_SOUND_BANK={repo.symbols[sound][0]}',
             f'-DP_TYPES_JOYPAD={repo.symbols["UpdateJoypad"][1]}',
             f'-DP_TYPES_CLOCK={repo.symbols["GameTimer"][1]}']
    executable = core(repo,target,points(repo),extra_flags=flags)
    driver = Driver(executable,repo.rom_path,BOOT,output / 'pokecrystal-dex-types.sav',target / 'trace.log')
    rows = []
    name, index = None, None
    try:
        driver.command('rawcolor')
        bootstrap(driver)
        enter_types(driver,repo,True)
        oracle = Oracle(repo)
        legal = set()
        if navigation:
            for selected in range(18):
                image = capture(driver,target / f'legal-{selected}.png')
                oracle.audit(driver,selected,image)
                legal.update(bug_hashes(repo,image,selected))
                press(driver,'down' if selected%3==2 else 'right')
                if selected%3==2:
                    press(driver,'right')
        music = constants(ROOT / 'constants/music_constants.asm')
        # constants() returns actual const entries, not the map-music sentinels.
        songs = {k:v for k,v in music.items() if k.startswith('MUSIC_')}
        effects = constants(ROOT / 'constants/sfx_constants.asm')
        for name, index in songs.items():
            reach(driver,repo,'PokedexTypes_Update.owner_loop')
            driver.command(f'typesaudio {repo.symbols["PlayMusic"][1]} {index}')
            driver.run(frames=4)
            driver.events.clear()
            driver.command('perf 1')
            driver.run(frames=360 if navigation else 1800)
            trace = trace_audit(driver.events)
            cost = costs(driver.events)
            oracle.audit(driver,0,capture(driver,target / 'last.png'))
            for effect in ('SFX_MENU','SFX_READ_TEXT_2','SFX_CHANGE_DEX_MODE'):
                reach(driver,repo,'PokedexTypes_Update.owner_loop')
                if navigation:
                    driver.events.clear()
                driver.command(f'typesaudio {repo.symbols["PlaySFX"][1]} {effects[effect]}')
                if not navigation:
                    driver.run(frames=4)
                    driver.events.clear()
                driver.run(frames=90,key='down' if navigation else None)
                driver.run(frames=4)
                trace_audit(driver.events)
                selected = memory(driver,repo,'wPokedexWRAM0Scratch',1)[0]
                oracle.audit(driver,selected,capture(driver,target / 'last.png'))
                if navigation:
                    atomic_audit(driver.events,legal)
            if navigation:
                for _ in range(6):
                    if memory(driver,repo,'wPokedexWRAM0Scratch',1)[0] == 0:
                        break
                    press(driver,'up')
                assert memory(driver,repo,'wPokedexWRAM0Scratch',1)[0] == 0
            rows.append(dict(song=name,index=index,frames=360 if navigation else 1800,
                             menu_sfx=3,held_input=navigation,trace=trace,costs=cost))
            (target / 'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
            if len(rows)%20 == 0:
                print(json.dumps(dict(songs=len(rows),total=len(songs))),flush=True)
        press(driver,'b')
        reach(driver,repo,'Pokedex_UpdateOptionScreen')
        driver.command('perf 0')
    except Exception:
        (target / 'failure-events.json').write_text(json.dumps(dict(song=name,index=index,events=driver.events),indent=2)+'\n')
        raise
    finally:
        driver.close()
    record = dict(variant=variant,rom_sha256=sha256(repo.rom),songs=len(rows),
                  frames_per_song=360 if navigation else 1800,sfx_per_song=3,held_input=navigation,
                  normal_input=False,fixture='Real PlayMusic/PlaySFX calls on live Type owner; no PPU/IME patch',
                  max_vblank_ms=max(r['costs']['type_vblank']['max_ms'] for r in rows),
                  max_sound_ms=max(r['costs']['sound']['max_ms'] for r in rows),rows=rows,issues=[])
    (target / 'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='rows'},indent=2))


def audio_navigation(variant):
    audio(variant,navigation=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('diagnose','measure','audio','audio_navigation'),nargs='?',default='diagnose')
    parser.add_argument('--variant', choices=('runtime', 'precomputed'), default='runtime')
    parser.add_argument('--base',type=Path,default=BASE)
    args = parser.parse_args()
    BASE = args.base.resolve()
    globals()[args.action](args.variant)
