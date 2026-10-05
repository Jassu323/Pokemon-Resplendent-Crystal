"""Retained baseline versus Surf/intro revision, using native LCD frames."""
from concurrent.futures import ProcessPoolExecutor
import argparse
from io import BytesIO
import json
import subprocess
import tarfile

from PIL import Image, ImageDraw

from .animation_reference import OUTPUT, FRAME, events
from .animation_reference_visuals import window
from . import battle_pacing_visuals as old

FPS = 4194304 / FRAME
DESTINATION = OUTPUT / 'surf-intro-qualification/visuals'


def frames(folder):
    paths=list(folder.glob('frame-*.ppm'))
    if paths:
        return {int(p.stem.split('-')[1]):Image.open(p).convert('RGB') for p in paths}
    if (folder/'rendered-frames.tar.gz').exists():
        with tarfile.open(folder/'rendered-frames.tar.gz') as archive:
            return {int(m.name.split('-')[1].split('.')[0]):
                    Image.open(BytesIO(archive.extractfile(m).read())).convert('RGB')
                    for m in archive.getmembers()}
    raise FileNotFoundError(f'No native frames in {folder}')


def comparison(kind):
    variants = ('production','targeted','surf-intro') if kind.startswith('surf') else (
        'production','surf-production','surf-intro')
    windows=[]
    if kind.startswith('surf'):
        side=kind.split('-')[1]
        windows=[window('SURF',side,v) for v in variants]
    else:
        species='dusknoir' if kind=='wild-intro' else 'joey'
        for variant in variants:
            folder=OUTPUT/'wild-intro'/variant/(species+'-q0')
            rows=events(folder)
            span=next(e for e in rows if e['event']=='perf_cost' and e['name']=='intro')
            shown=[e['display'] for e in rows if e['event']=='perf_frame' and
                   span['t']<=e['t']<span['t']+span['elapsed']]
            windows.append((folder,shown[0],shown[-1]))
    images=[frames(folder) for folder,_,_ in windows]
    count=max(b-a+1 for _,a,b in windows)+20
    destination=DESTINATION/(kind+'-comparison.mp4')
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
        '-video_size','960x328','-framerate',str(FPS),'-i','-','-an','-c:v','libx264',
        '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    for n in range(count):
        canvas=Image.new('RGB',(960,328),(30,30,30))
        draw=ImageDraw.Draw(canvas)
        for column,(variant,(_,first,last),source) in enumerate(zip(variants,windows,images)):
            frame=min(first+n,last)
            canvas.paste(source[frame].resize((320,288),Image.Resampling.NEAREST),(column*320,40))
            draw.text((column*320+8,5),f'{variant} | {kind}',fill='white')
            draw.text((column*320+8,22),f'interval {n}'+(' | FINISHED (padded)' if frame==last else ''),fill='white')
        process.stdin.write(canvas.tobytes())
    process.stdin.close()
    if process.wait():
        raise RuntimeError(destination)
    return dict(kind=kind,path=str(destination),frames=count,silent=True)


def encode(task):
    old.OUTPUT=OUTPUT
    return old.encode(task)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparisons-only',action='store_true')
    args=parser.parse_args()
    DESTINATION.mkdir(parents=True,exist_ok=True)
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(comparison,('surf-player','surf-foe','wild-intro','trainer-intro')))
        if args.comparisons_only:
            previous=DESTINATION/'videos.json'
            individual=json.loads(previous.read_text())['individual'] if previous.exists() else []
        else:
            individual=list(pool.map(encode,[('SURF',side,'surf-intro') for side in ('player','foe')]))
    (DESTINATION/'videos.json').write_text(json.dumps(dict(comparisons=rows,individual=individual),indent=2)+'\n')
    print(json.dumps(dict(comparisons=len(rows),individual=len(individual))))


if __name__=='__main__':main()
