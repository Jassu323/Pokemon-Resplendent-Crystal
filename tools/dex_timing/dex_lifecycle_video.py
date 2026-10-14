"""Record native lifecycle frames and align a side-by-side timing video."""
import argparse
from bisect import bisect_right
import gzip
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .assets import Repository, sha256
from .cold_listing import Driver, ROOT, FRAME
from .dex_lifecycle_budget import BASE, FRAME_MS
from . import dex_lifecycle_review as life
from .info_ui import BOOT
from .performance import HZ
from .performance_lifecycle import open_menu

VIDEO = BASE / 'video'
FPS = HZ / FRAME


def record(variants=('baseline', 'music-best')):
    cfg = json.loads((BASE / 'config.json').read_text())
    rows = []
    for style in (0, 1):
        for variant in variants:
            resource = cfg['variants'][variant]
            folder = VIDEO / variant / str(style)
            folder.mkdir(parents=True, exist_ok=True)
            repo = Repository(ROOT, Path(resource['rom']), Path(cfg['sym']))
            driver = Driver(cfg['core'], repo.rom_path, BOOT, cfg['fixtures'][f'{style}-0'],
                            folder / 'driver.log')
            try:
                driver.command('rawcolor')
                open_menu(driver)
                for direction, label, key in (('entry', 'Pokedex_UpdateMainScreen', 'a'),
                                              ('exit', 'StartMenu.loop', 'b')):
                    initial = driver.command('perf 1')
                    driver.events.clear()
                    driver.command(f'perfimages {folder}/{direction}')
                    ready = life.reach(driver, repo, label, key)
                    driver.run(frames=120)
                    driver.command('perf 0')
                    driver.command('perfimages -')
                    events = list(driver.events)
                    with gzip.open(folder / (direction + '-events.json.gz'), 'wt') as stream:
                        json.dump(events, stream)
                    ms = (ready['t'] - initial['t']) * 1000 / HZ
                    rows.append(dict(variant=variant, style=style, direction=direction,
                        source_rom=str(repo.rom_path), rom_sha256=sha256(repo.rom),
                        input_t=initial['t'], ready_t=ready['t'], ready_ms=ms,
                        ready_frames=ms / FRAME_MS, folder=str(folder)))
            finally:
                driver.close()
    life.write(VIDEO / 'recordings.json', dict(rows=rows, host_only_observer=True,
                                              frame_ms=FRAME_MS, fps=FPS))
    print(json.dumps([{k:v for k,v in row.items() if k in
                      ('variant','style','direction','ready_ms','ready_frames')} for row in rows], indent=2))


class Clip:
    def __init__(self, row):
        self.row = row
        folder = Path(row['folder'])
        with gzip.open(folder / (row['direction'] + '-events.json.gz'), 'rt') as stream:
            events = json.load(stream)
        frames = {e['display']:e for e in events if e['event']=='perf_frame'}
        self.times, self.pictures = [], []
        for path in sorted(folder.glob(row['direction'] + '-*.ppm')):
            frame = frames[int(path.stem.rsplit('-', 1)[1])]
            self.times.append((frame['boundary_t'] - row['input_t']) / HZ)
            with Image.open(path) as picture:
                self.pictures.append(picture.convert('RGB').resize((480,432), Image.Resampling.NEAREST))

    def at(self, elapsed):
        return self.pictures[max(0, bisect_right(self.times, elapsed)-1)]


def render():
    rows = json.loads((VIDEO / 'recordings.json').read_text())['rows']
    clips = {(r['variant'],r['style'],r['direction']):Clip(r) for r in rows}
    font = '/System/Library/Fonts/Menlo.ttc'
    fonts = {size:ImageFont.truetype(font, size) for size in (18,22,25,30)}
    target = VIDEO / 'production-vs-balanced-prototype.mp4'
    process = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo',
        '-pixel_format','rgb24','-video_size','1080x720','-framerate','262144/4389',
        '-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(target)], stdin=subprocess.PIPE)
    scenes = [(0,'entry',1),(0,'exit',1),(1,'entry',1),(1,'exit',1),
              (0,'entry',.5),(0,'exit',.5)]
    receipt = []
    output_frames = 0
    try:
        for style,direction,speed in scenes:
            left,right = (clips[v,style,direction] for v in ('baseline','music-best'))
            maximum = max(left.row['ready_ms'],right.row['ready_ms']) / 1000
            prelude, tail = .8, .8
            count = round((prelude + (maximum+tail) / speed) * FPS)
            receipt.append(dict(style=style,direction=direction,playback_speed=speed,
                output_start_s=output_frames/FPS,production_ms=left.row['ready_ms'],
                prototype_ms=right.row['ready_ms'],
                saving_ms=left.row['ready_ms']-right.row['ready_ms'],
                saving_frames=left.row['ready_frames']-right.row['ready_frames']))
            for index in range(count):
                elapsed = (index/FPS-prelude)*speed
                canvas = Image.new('RGB',(1080,720),(24,24,24))
                draw = ImageDraw.Draw(canvas)
                label = ('Modern' if style==0 else 'Legacy') + ' - ' + ('Enter Dex' if direction=='entry' else 'Exit Dex')
                draw.text((40,22),label,font=fonts[30],fill='white')
                draw.text((820,26),'1x real time' if speed==1 else '0.5x replay',font=fonts[22],fill=(200,200,200))
                draw.text((40,88),'PRODUCTION',font=fonts[25],fill='white')
                draw.text((560,88),'BALANCED PROTOTYPE',font=fonts[25],fill='white')
                for x,clip in ((40,left),(560,right)):
                    canvas.paste(clip.at(max(0,elapsed)),(x,140))
                    ready_ms = clip.row['ready_ms']
                    if elapsed<0:
                        text,color = 'Waiting for synchronized input',(190,190,190)
                    elif elapsed*1000<ready_ms:
                        text,color = 'Working... %.0f ms (%.1f f)'%(elapsed*1000,elapsed*1000/FRAME_MS),(235,235,235)
                    else:
                        text,color = 'READY: %.1f ms (%.2f f)'%(ready_ms,ready_ms/FRAME_MS),(122,219,159)
                    draw.text((x,596),text,font=fonts[22],fill=color)
                command = 'A: open Pokedex' if direction=='entry' else 'B: close Pokedex'
                draw.text((40,645),command + ' | Same save and requested input time',font=fonts[18],fill=(200,200,200))
                draw.text((40,675),'Current fades retained | +712 B ROMX, +5 B WRAMX | Timers show game time',
                          font=fonts[18],fill=(200,200,200))
                process.stdin.write(canvas.tobytes())
            output_frames += count
    finally:
        process.stdin.close()
        result = process.wait()
    if result:
        raise RuntimeError('Video encoding failed')
    life.write(VIDEO / 'video-receipt.json', dict(video=str(target),fps=FPS,
        output_frames=output_frames,duration_s=output_frames/FPS,scenes=receipt,
        silent=True,alignment='same normal input request; native display boundary timestamps',
        production_rom_unchanged=True))
    print(str(target))


def render_four():
    rows = json.loads((VIDEO / 'recordings.json').read_text())['rows']
    resources = json.loads((BASE / 'config.json').read_text())['variants']
    font = '/System/Library/Fonts/Menlo.ttc'
    fonts = {size:ImageFont.truetype(font, size) for size in (16,18,22,30)}
    target = VIDEO / 'production-reference-stage-hard-cuts.mp4'
    variants = ('baseline','reference','stage','hard-cuts')
    names = dict(baseline='PRODUCTION',reference='REFERENCE',stage='STAGE',
                 **{'hard-cuts':'HARD CUTS'})
    positions = ((40,108),(560,108),(40,674),(560,674))
    process = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo',
        '-pixel_format','rgb24','-video_size','1080x1240','-framerate','262144/4389',
        '-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(target)], stdin=subprocess.PIPE)
    scenes = [(0,'entry',1),(0,'exit',1),(1,'entry',1),(1,'exit',1),
              (0,'entry',.5),(0,'exit',.5)]
    receipt = []
    output_frames = 0
    try:
        for style,direction,speed in scenes:
            clips = [Clip(next(r for r in rows if (r['variant'],r['style'],r['direction']) ==
                               (variant,style,direction))) for variant in variants]
            maximum = max(clip.row['ready_ms'] for clip in clips) / 1000
            prelude, tail = .8, .8
            count = round((prelude + (maximum+tail) / speed) * FPS)
            receipt.append(dict(style=style,direction=direction,playback_speed=speed,
                output_start_s=output_frames/FPS,
                timings={c.row['variant']:dict(ms=c.row['ready_ms'],frames=c.row['ready_frames'])
                         for c in clips}))
            for index in range(count):
                elapsed = (index/FPS-prelude)*speed
                canvas = Image.new('RGB',(1080,1240),(24,24,24))
                draw = ImageDraw.Draw(canvas)
                label = ('Modern' if style==0 else 'Legacy') + ' - ' + ('Enter Dex' if direction=='entry' else 'Exit Dex')
                draw.text((40,22),label,font=fonts[30],fill='white')
                draw.text((820,26),'1x real time' if speed==1 else '0.5x replay',font=fonts[22],fill=(200,200,200))
                command = 'A: open Pokedex' if direction=='entry' else 'B: close Pokedex'
                draw.text((40,70),command + ' | Same save, sort and synchronized requested input',
                          font=fonts[18],fill=(200,200,200))
                for clip,(x,y) in zip(clips,positions):
                    variant = clip.row['variant']
                    cost = resources[variant]['proposed_romx_delta']
                    text = names[variant] + ((' (+%d B ROMX)'%cost) if cost else '')
                    draw.text((x,y),text,font=fonts[22],fill='white')
                    canvas.paste(clip.at(max(0,elapsed)),(x,y+40))
                    ready_ms = clip.row['ready_ms']
                    if elapsed<0:
                        text,color = 'Waiting for synchronized input',(190,190,190)
                    elif elapsed*1000<ready_ms:
                        text,color = 'Working... %.0f ms (%.1f f)'%(elapsed*1000,elapsed*1000/FRAME_MS),(235,235,235)
                    else:
                        text,color = 'READY: %.1f ms (%.2f f)'%(ready_ms,ready_ms/FRAME_MS),(122,219,159)
                    draw.text((x,y+490),text,font=fonts[22],fill=color)
                draw.text((40,1210),'Native display timing | Individual recording results, not pooled medians | Silent',
                          font=fonts[16],fill=(200,200,200))
                process.stdin.write(canvas.tobytes())
            output_frames += count
    finally:
        process.stdin.close()
        result = process.wait()
    if result:
        raise RuntimeError('Four-way video encoding failed')
    config = json.loads((BASE / 'config.json').read_text())
    unchanged = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym').hashes == config['baseline_hashes']
    life.write(VIDEO / 'video-receipt.json', dict(video=str(target),fps=FPS,
        output_frames=output_frames,duration_s=output_frames/FPS,scenes=receipt,
        silent=True,alignment='same normal input request; native display boundary timestamps',
        production_rom_unchanged=unchanged,
        variants={v:dict(rom=resources[v]['rom'],sha256=sha256(Path(resources[v]['rom']).read_bytes()))
                  for v in variants}))
    print(str(target))


def package_review():
    from set_move_discovery_fraction import catalogue, inspect
    from .assets import read_symbols
    cfg = json.loads((BASE / 'config.json').read_text())
    video = BASE / 'video-four-way/production-reference-stage-hard-cuts.mp4'
    if not video.is_file():
        raise ValueError('Finish the four-way video before packaging review ROMs')
    source_save = Path(cfg['fixtures']['0-0'])
    _, seen = inspect(source_save.read_bytes(), read_symbols(Path(cfg['sym'])), len(catalogue()))
    variants = ('reference','stage','hard-cuts')
    for variant in variants:
        row = cfg['variants'][variant]
        data = Path(row['rom']).read_bytes()
        if sha256(data) != row['sha256']:
            raise ValueError('Diagnostic ROM no longer matches its measured version: ' + variant)
        if data[0x14d] != (-sum(data[0x134:0x14d])-25)&255:
            raise ValueError('Invalid cartridge header checksum: ' + variant)
        if int.from_bytes(data[0x14e:0x150],'big') != (sum(data[:0x14e])+sum(data[0x150:]))&65535:
            raise ValueError('Invalid cartridge global checksum: ' + variant)
    folder = BASE / 'review-roms-four-way-20261013'
    # A later package must not overwrite saves the user has started testing.
    folder.mkdir(exist_ok=False)
    outputs = []
    for variant in variants:
        row = cfg['variants'][variant]
        rom = folder / ('pokecrystal-dex-entry-' + variant + '.gbc')
        save = rom.with_suffix('.sav')
        shutil.copy2(row['rom'],rom)
        shutil.copy2(source_save,save)
        outputs.append(dict(variant=variant,rom=str(rom),rom_sha256=sha256(rom.read_bytes()),
            source_rom=row['rom'],save=str(save),save_sha256=sha256(save.read_bytes()),
            seen_moves=len(seen),projected_romx_bytes=row['proposed_romx_delta'],
            wramx_bytes=row.get('wram_delta',0)))
    life.write(folder / 'manifest.json',dict(video=str(video),source_save=str(source_save),
        source_save_is_private_copy=True,main_save_not_modified=True,
        cartridge_checksums_valid=True,outputs=outputs))
    print(json.dumps(outputs,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('record','render','package'))
    parser.add_argument('--comparison', choices=('balanced','four'), default='balanced')
    args = parser.parse_args()
    if args.comparison=='four':
        VIDEO = BASE / 'video-four-way'
    if args.action=='package': package_review()
    elif args.action=='record':
        record(('baseline','reference','stage','hard-cuts') if args.comparison=='four' else
               ('baseline','music-best'))
    elif args.comparison=='four': render_four()
    else: render()
