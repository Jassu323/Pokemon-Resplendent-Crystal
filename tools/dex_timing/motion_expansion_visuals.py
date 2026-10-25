"""Retain native-frame and audio comparisons for the expanded private ROM."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import subprocess

from PIL import Image, ImageDraw

from .animation_reference import OUTPUT, FRAME
from .animation_reference_visuals import window
from .battle_motion_revision_visuals import frames
from . import battle_pacing_visuals as encoding

MOVES = '''SURF CAUSTIC WATER_PULSE DRAGON_DANCE THUNDERBOLT HYDRO_PUMP
WATERFALL LEAF_BLADE RAZOR_LEAF MAGICAL_LEAF POISON_GAS WHIRLPOOL GUST
RECOVER SEISMIC_TOSS PSYCHIC_M WILD_CHARGE SHOCK_WAVE SHADOW_BALL FIRE_BLAST
SILVER_WIND AROMATHERAPY OVERHEAT BULLET_SEED'''.split()
FPS = 4194304 / FRAME


def render(task):
    move, side, candidate = task
    variants = ('production', candidate)
    spans = [window(move, side, variant) for variant in variants]
    sources = [frames(folder) for folder, _, _ in spans]
    count = max(b-a+1 for _, a, b in spans) + 16
    output = OUTPUT / (candidate+'-qualification/visuals')
    output.mkdir(parents=True, exist_ok=True)
    video = output / f'{move.lower()}-{side}-comparison.mp4'
    process = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '640x328',
        '-framerate', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)],
        stdin=subprocess.PIPE)
    samples = sorted(set(round(n*(count-17)/5) for n in range(6)))
    sheet = Image.new('RGB', (640, 6*308+28), 'white')
    draw_sheet = ImageDraw.Draw(sheet)
    for n in range(count):
        canvas = Image.new('RGB', (640,328), (30,30,30))
        draw = ImageDraw.Draw(canvas)
        for column, (variant, (_,first,last), source) in enumerate(zip(variants,spans,sources)):
            index = min(first+n,last)
            native = source[index].resize((320,288),Image.Resampling.NEAREST)
            canvas.paste(native,(column*320,40))
            draw.text((column*320+8,5),f'{variant} | {move} | {side}',fill='white')
            draw.text((column*320+8,22),f'interval {n}'+(' | SCRIPT END (padded)' if index==last else ''),fill='white')
            if n in samples:
                row=samples.index(n)
                draw_sheet.text((column*320+8,5),variant,fill='black')
                draw_sheet.text((column*320+8,28+row*308),f'interval {n}',fill='black')
                sheet.paste(native,(column*320,48+row*308))
        process.stdin.write(canvas.tobytes())
    process.stdin.close()
    if process.wait():
        raise RuntimeError(video)
    sheet.save(output/f'{move.lower()}-{side}-contact.png')
    encoding.OUTPUT=OUTPUT
    individual=[encoding.encode((move,side,v)) for v in variants]
    return dict(move=move,side=side,comparison=str(video),individual=individual,
                alignment='first primary-script display',padding='last primary-script display; not native idle time')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',default='expanded-v2')
    parser.add_argument('--moves',nargs='+',default=MOVES)
    parser.add_argument('--jobs',type=int,default=12)
    args=parser.parse_args()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        rows=list(pool.map(render,[(m,s,args.candidate) for m in args.moves for s in ('player','foe')]))
    target=OUTPUT/(args.candidate+'-qualification/visuals/videos.json')
    target.write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(dict(comparisons=len(rows),individual=len(rows)*2)),flush=True)


if __name__=='__main__':main()
