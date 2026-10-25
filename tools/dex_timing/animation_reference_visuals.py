"""Native-frame motion reviews, with explicit completion padding in comparisons."""
from concurrent.futures import ProcessPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

from .animation_reference import OUTPUT, TARGETS, FRAME, events
from . import battle_pacing_visuals as old

FPS=4194304/FRAME


def encode(task):
    old.OUTPUT=OUTPUT
    return old.encode(task)


def window(move,side,variant):
    folder=OUTPUT/'replays'/variant/f'{move.lower()}-{side}-q0'
    result=json.loads((folder/'result.json').read_text())
    rows=events(folder)
    call=result['requested_animations'][0]
    script=next(e for e in rows if e['event']=='perf_cost' and e['name']=='battle_script' and
                call['start']['t']<=e['t']<call['start']['t']+call['elapsed_t'])
    frames=[e for e in rows if e['event']=='perf_frame']
    first=next(e['display'] for e in frames if e['boundary_t']>=script['t'])
    end=next(e['display'] for e in frames if e['boundary_t']>=script['t']+script['elapsed'])
    return folder,first,end


def compare(task):
    move,side=task
    variants=('production','final','targeted')
    windows=[window(move,side,v) for v in variants]
    count=max(b-a for _,a,b in windows)+20
    target=OUTPUT/'visuals'/f'{move.lower()}-{side}-comparison.mp4'
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size','960x328','-framerate',str(FPS),'-i','-','-an','-c:v','libx264',
             '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    for n in range(count):
        canvas=Image.new('RGB',(960,328),(30,30,30)); draw=ImageDraw.Draw(canvas)
        for column,(variant,(folder,first,end)) in enumerate(zip(variants,windows)):
            frame=min(first+n,end)
            native=Image.open(folder/f'frame-{frame:03d}.ppm').convert('RGB')
            canvas.paste(native.resize((320,288),Image.Resampling.NEAREST),(column*320,40))
            draw.text((column*320+8,5),f'{variant} | {move} | {side}',fill='white')
            draw.text((column*320+8,22),f'interval {n}' + (' | FINISHED (padded)' if frame==end else ''),fill='white')
        process.stdin.write(canvas.tobytes())
    process.stdin.close()
    if process.wait(): raise RuntimeError(target)
    return dict(move=move,side=side,path=str(target),frames=count,silent=True)


def sheets():
    for move in TARGETS:
        samples=(16,40,64,96,128,160)
        sheet=Image.new('RGB',(960,6*308+30),'white');draw=ImageDraw.Draw(sheet)
        for column,variant in enumerate(('production','final','targeted')):
            folder,first,end=window(move,'player',variant)
            draw.text((column*320+8,5),variant+' | '+move,fill='black')
            for row,n in enumerate(samples):
                frame=min(first+n,end)
                native=Image.open(folder/f'frame-{frame:03d}.ppm').convert('RGB')
                y=30+row*308
                draw.text((column*320+8,y),f'interval {n}'+(' FINISHED' if frame==end else ''),fill='black')
                sheet.paste(native.resize((320,288),Image.Resampling.NEAREST),(column*320,y+20))
        sheet.save(OUTPUT/'visuals'/f'{move.lower()}-contact.png')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-frames',action='store_true',
                        help='Verify lossless archives of generated raw frames before reclaiming their loose copies')
    args=parser.parse_args()
    if args.archive_frames:
        folders=[p for p in (OUTPUT/'replays').glob('*/*') if p.is_dir() and not p.is_symlink()]
        with ProcessPoolExecutor(max_workers=12) as pool:
            reclaimed=sum(pool.map(old.archive_frames,folders))
        (OUTPUT/'visuals/archive.json').write_text(json.dumps(dict(
            folders=len(folders),reclaimed_gib=reclaimed/1024**3),indent=2)+'\n')
        print(json.dumps(dict(reclaimed_gib=reclaimed/1024**3,folders=len(folders))),flush=True)
        return
    (OUTPUT/'visuals').mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=8) as pool:
        individual=list(pool.map(encode,[(m,s,v) for m in TARGETS for s in ('player','foe')
                                        for v in ('production','final','targeted')]))
        comparisons=list(pool.map(compare,[(m,s) for m in TARGETS for s in ('player','foe')]))
    sheets()
    (OUTPUT/'visuals/videos.json').write_text(json.dumps(dict(individual=individual,comparisons=comparisons),indent=2)+'\n')
    print(json.dumps(dict(individual=len(individual),comparisons=len(comparisons))),flush=True)


if __name__=='__main__':main()
