"""Normal production versus normal-battle trial; native frames, no retiming."""
from concurrent.futures import ProcessPoolExecutor
import json
import subprocess

from PIL import Image, ImageDraw

from .battle_normal_speed import BASE, CAPTURE
from . import animation_reference_visuals as visual, battle_pacing_visuals as old

FPS = 4194304/70224


def encode(task):
    old.OUTPUT = BASE
    return old.encode(task)


def comparison(task):
    move, side = task
    visual.OUTPUT = BASE
    windows = [visual.window(move,side,v) for v in ('production','battle-normal')]
    target = BASE/'visuals'/f'{move.lower()}-{side}-comparison.mp4'
    count = max(last-first+1 for _,first,last in windows)+16
    command = ['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
        '-video_size','640x328','-framerate',str(FPS),'-i','-','-an','-c:v','libx264',
        '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    process = subprocess.Popen(command,stdin=subprocess.PIPE)
    for n in range(count):
        canvas = Image.new('RGB',(640,328),(30,30,30))
        draw = ImageDraw.Draw(canvas)
        for col,(variant,(folder,first,last)) in enumerate(zip(('production','battle-normal'),windows)):
            frame = min(first+n,last)
            image = Image.open(folder/f'frame-{frame:03d}.ppm').convert('RGB')
            canvas.paste(image.resize((320,288),Image.Resampling.NEAREST),(col*320,40))
            draw.text((col*320+8,5),f'{variant} | {move} | {side}',fill='white')
            draw.text((col*320+8,22),f'interval {n}'+(' | FINISHED (padded)' if frame==last else ''),fill='white')
        process.stdin.write(canvas.tobytes())
    process.stdin.close()
    if process.wait():
        raise RuntimeError(target)
    return dict(move=move,side=side,path=str(target),frames=count,silent=True)


def reel(side):
    paths = [BASE/'visuals'/f'{m.lower()}-{side}-comparison.mp4' for m in CAPTURE]
    listing = BASE/'visuals'/f'{side}-concat.txt'
    listing.write_text(''.join(f"file '{p}'\n" for p in paths))
    target = BASE/'visuals'/f'{side}-comparison-reel.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0',
                    '-i',str(listing),'-c','copy','-movflags','+faststart',str(target)],check=True)
    return str(target)


def main():
    destination = BASE/'visuals'
    destination.mkdir(exist_ok=True)
    link = BASE/'replays'
    if not link.exists():
        link.symlink_to(BASE/'moves',target_is_directory=True)
    with ProcessPoolExecutor(max_workers=8) as pool:
        individuals = list(pool.map(encode,[(m,s,v) for m in CAPTURE for s in ('player','foe')
                                           for v in ('production','battle-normal')]))
        comparisons = list(pool.map(comparison,[(m,s) for m in CAPTURE for s in ('player','foe')]))
        reels = list(pool.map(reel,('player','foe')))
        reclaimed = sum(pool.map(old.archive_frames,[p for v in ('production','battle-normal')
            for p in (BASE/'moves'/v).iterdir() if p.is_dir() and any(p.glob('frame-*.ppm'))]))
    (destination/'videos.json').write_text(json.dumps(dict(individual=individuals,comparisons=comparisons,
        reels=reels,reclaimed_gib=reclaimed/1024**3),indent=2)+'\n')
    print(json.dumps(dict(individual=len(individuals),comparisons=len(comparisons),reels=reels,
                         reclaimed_gib=reclaimed/1024**3)))


if __name__=='__main__':main()
