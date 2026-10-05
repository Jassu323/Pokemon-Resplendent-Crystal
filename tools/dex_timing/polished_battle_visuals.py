"""Compare native Polished and Resplendent motion, without cartridge retiming."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import argparse
import json
import statistics
import subprocess

from PIL import Image, ImageDraw

from .animation_reference import OUTPUT as RESPLENDENT, FRAME, events
from .battle_motion_revision_visuals import frames
from .polished_battle_reference import OUTPUT, MOVES
from .battle_pacing_visuals import archive_frames

FPS = 4194304 / FRAME
VARIANTS = ('production', 'final', 'polished')
LABELS = ('Resplendent normal', 'Resplendent double (raw)', 'Polished double (native)')


def folder(variant, move, side, quarter=0):
    root = OUTPUT if variant == 'polished' else RESPLENDENT
    return root / 'replays' / variant / f'{move.lower()}-{side}-q{quarter}'


def analyze(task):
    variant, move, side, quarter = task
    path = folder(*task)
    result = json.loads((path/'result.json').read_text())
    if result['issues']:
        raise RuntimeError((path, result['issues']))
    rows = events(path)
    call = result['requested_animations'][0]
    begin = call['start']['t']
    end = begin + call['elapsed_t']
    script = min((e for e in rows if e['event'] == 'perf_cost' and e['name'] == 'battle_script'
                  and begin <= e['t'] < end), key=lambda e: e['t'])
    a, b = script['t'], script['t'] + script['elapsed']
    local = [e for e in rows if a <= e['t'] < b]
    ticks = [e for e in local if e['event'] == 'perf_phase' and e['name'] == 'anim_tick']
    states = [e for e in local if e['event'] == 'anim_state']
    if len(ticks) != len(states):
        raise RuntimeError(('Missing logical trace', path, len(ticks), len(states)))
    display = [e for e in rows if e['event'] == 'perf_frame']
    first = next(e['display'] for e in display if e['boundary_t'] >= a)
    last = next(e['display'] for e in display if e['boundary_t'] >= b)
    stride, count, state_offset = (24, 10, 14) if variant == 'polished' else (20, 14, 15)
    histories, active = [], {}
    for event in (e for e in local if e['event'] == 'anim_objects'):
        data = bytes.fromhex(event['bytes'])
        if len(data) != stride*count:
            raise RuntimeError(('Object layout mismatch', path, len(data)))
        for slot in range(count):
            obj = list(data[slot*stride:(slot+1)*stride])
            if not obj[0] or (slot in active and obj[0] != active[slot]['index']):
                if slot in active:
                    old = active.pop(slot)
                    old['end'] = (event['t']-a)/FRAME
                    histories.append(old)
            if not obj[0]: continue
            if slot not in active:
                active[slot] = dict(slot=slot, index=obj[0], start=(event['t']-a)/FRAME, samples=[])
            active[slot]['samples'].append(dict(t=(event['t']-a)/FRAME,
                state=obj[state_offset], x=obj[7 if variant=='polished' else 8],
                y=obj[8 if variant=='polished' else 9]))
    for old in active.values():
        old['end'] = script['elapsed']/FRAME
        histories.append(old)
    costs = {}
    for name in ('anim_command','anim_bg','anim_oam','anim_ly','anim_pals','anim_wait'):
        spans = [e['elapsed']/FRAME for e in local if e['event']=='perf_cost' and e['name']==name]
        costs[name] = dict(calls=len(spans), total=sum(spans), maximum=max(spans,default=0))
    return dict(variant=variant, move=move, side=side, quarter=quarter,
        primary=script['elapsed']/FRAME, primary_ms=script['elapsed']/4194.304,
        wrapper=call['elapsed_t']/FRAME, wrapper_ms=call['elapsed_t']/4194.304,
        ticks=len(ticks), step_gaps=dict(Counter(round((y['t']-x['t'])/FRAME)
                                               for x,y in zip(ticks,ticks[1:]))),
        work_median=statistics.median((y['t']-x['t'])/FRAME for x,y in zip(ticks,states)),
        work_max=max((y['t']-x['t'])/FRAME for x,y in zip(ticks,states)),
        first=first,last=last, primary_start=a, primary_end=b,
        sounds=[dict(t=(e['t']-a)/FRAME,id=e['de']) for e in local
                if e['event']=='perf_phase' and e['name'] in ('sound','stereo_sound')],
        objects=histories,costs=costs)


def individual(task):
    variant, move, side = task
    path = folder(variant,move,side)
    row = analyze((variant,move,side,0))
    result = json.loads((path/'result.json').read_text())
    display = [e for e in events(path) if e['event']=='perf_frame']
    call=result['requested_animations'][0]
    first=next(e['display'] for e in display if e['boundary_t']>=call['start']['t'])
    last=next(e['display'] for e in display if e['boundary_t']>=call['start']['t']+call['elapsed_t'])
    first=max(display[0]['display'],first-4)
    last=min(display[-1]['display'],last+16)
    boundary=next(e['boundary_t'] for e in display if e['display']==first)-FRAME
    offset=max(0,(boundary-result['capture_start_t'])/4194304)
    video=OUTPUT/'visuals'/f'{move.lower()}-{side}-{variant}.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-framerate',str(FPS),'-start_number',str(first),'-i',str(path/'frame-%03d.ppm'),
        '-f','s16le','-ar','44100','-ac','2','-ss',str(offset),'-i',str(path/'audio.raw'),
        '-frames:v',str(last-first+1),'-vf','scale=640:576:flags=neighbor',
        '-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(video)],check=True)
    return dict(variant=variant,move=move,side=side,path=str(video))


def reel(side):
    directory=OUTPUT/'visuals'
    playlist=directory/(side+'-playlist.txt')
    playlist.write_text(''.join(f"file '{m.lower()}-{side}-comparison.mp4'\n" for m in MOVES))
    target=directory/(side+'-all-moves-comparison.mp4')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat',
        '-safe','0','-i',str(playlist),'-c','copy','-movflags','+faststart',str(target)],check=True)
    return dict(side=side,path=str(target),silent=True)


def review_index():
    manifest=json.loads((OUTPUT/'visuals/videos.json').read_text())
    lines=['# Polished battle animation review videos','',
        'Comparison columns: Resplendent production normal, unretimed Resplendent double, native Polished double.',
        'Comparisons are silent and aligned at primary-script entry. SCRIPT END indicates explicit padding.',
        'Individual clips have native audio and cover the full animation wrapper, including sound waits.','']
    for row in manifest['reels']:
        lines.append(f'[{row["side"].title()} complete comparison]({row["path"]})')
    lines.extend(('', '| Move | Player comparison | Opponent comparison |', '| --- | --- | --- |'))
    for m in MOVES:
        paths=[next(r['path'] for r in manifest['comparisons'] if r['move']==m and r['side']==s) for s in ('player','foe')]
        lines.append(f'| {m} | [Player]({paths[0]}) | [Opponent]({paths[1]}) |')
    lines.extend(('', '## Individual clips with audio','',
        '| Move and side | Production normal | Resplendent raw double | Polished native double |',
        '| --- | --- | --- | --- |'))
    for m in MOVES:
        for s in ('player','foe'):
            paths=[next(r['path'] for r in manifest['individual'] if (r['move'],r['side'],r['variant'])==(m,s,v)) for v in VARIANTS]
            lines.append('| '+m+' '+s+' | '+' | '.join(f'[Play]({p})' for p in paths)+' |')
    (OUTPUT/'visuals/README.md').write_text('\n'.join(lines)+'\n')


def verify_video(row):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format',
        '-of','json',row['path']],text=True))
    videos=[s for s in data['streams'] if s['codec_type']=='video']
    audio=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or float(data['format']['duration'])<=0 or (not row.get('silent') and not audio):
        raise RuntimeError(('Invalid media',row))
    n,d=map(int,videos[0]['r_frame_rate'].split('/'))
    if abs(n/d-FPS)>.0001: raise RuntimeError(('Non-native cadence',row))
    return dict(path=row['path'],frames=int(videos[0]['nb_frames']),audio=bool(audio))


def comparison(task):
    move,side=task
    rows=[analyze((v,move,side,0)) for v in VARIANTS]
    sources=[frames(folder(v,move,side)) for v in VARIANTS]
    length=max(r['last']-r['first']+1 for r in rows)+16
    video=OUTPUT/'visuals'/f'{move.lower()}-{side}-comparison.mp4'
    process=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pixel_format','rgb24','-video_size','960x328',
        '-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast',
        '-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
    sheet=Image.new('RGB',(960,6*308+28),'white')
    draw_sheet=ImageDraw.Draw(sheet)
    samples=sorted({round(n*(length-17)/5) for n in range(6)})
    for n in range(length):
        canvas=Image.new('RGB',(960,328),(30,30,30))
        draw=ImageDraw.Draw(canvas)
        for column,(label,row,source) in enumerate(zip(LABELS,rows,sources)):
            index=min(row['first']+n,row['last'])
            native=source[index].resize((320,288),Image.Resampling.NEAREST)
            canvas.paste(native,(column*320,40))
            draw.text((column*320+5,5),label+' | '+move,fill='white')
            draw.text((column*320+5,22),f'{side} | interval {n}'+
                (' | SCRIPT END (padded)' if index==row['last'] else ''),fill='white')
            if n in samples:
                k=samples.index(n)
                draw_sheet.text((column*320+5,5),label,fill='black')
                draw_sheet.text((column*320+5,28+k*308),f'interval {n}',fill='black')
                sheet.paste(native,(column*320,48+k*308))
        process.stdin.write(canvas.tobytes())
    process.stdin.close()
    if process.wait(): raise RuntimeError(video)
    sheet.save(video.with_name(video.stem.replace('comparison','contact')+'.png'))
    return dict(move=move,side=side,path=str(video),silent=True,frames=length)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-only',action='store_true')
    parser.add_argument('--archive-frames',action='store_true')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    (OUTPUT/'visuals').mkdir(exist_ok=True)
    if args.verify_only:
        review_index()
        manifest=json.loads((OUTPUT/'visuals/videos.json').read_text())
        with ProcessPoolExecutor(max_workers=12) as pool:
            checked=list(pool.map(verify_video,manifest['individual']+manifest['comparisons']+manifest['reels']))
        (OUTPUT/'visuals/verified.json').write_text(json.dumps(checked,indent=2)+'\n')
        print(json.dumps(dict(videos=len(checked),with_audio=sum(r['audio'] for r in checked))),flush=True)
        return
    if args.archive_frames:
        targets=[folder(v,m,s) for v in VARIANTS for m in MOVES for s in ('player','foe')]
        with ProcessPoolExecutor(max_workers=12) as pool:
            reclaimed=sum(pool.map(archive_frames,targets))
        (OUTPUT/'archive.json').write_text(json.dumps(dict(folders=len(targets),reclaimed_gib=reclaimed/1024**3),indent=2)+'\n')
        print(json.dumps(dict(folders=len(targets),reclaimed_gib=reclaimed/1024**3)),flush=True)
        return
    tasks=[(v,m,s,q) for v in VARIANTS for m in MOVES for s in ('player','foe') for q in (0,17556,35112,52668)]
    with ProcessPoolExecutor(max_workers=12) as pool:
        rows=list(pool.map(analyze,tasks))
        if not args.report_only:
            individual_rows=list(pool.map(individual,[(v,m,s) for v in VARIANTS for m in MOVES for s in ('player','foe')]))
            comparisons=list(pool.map(comparison,[(m,s) for m in MOVES for s in ('player','foe')]))
            reels=list(pool.map(reel,('player','foe')))
            (OUTPUT/'visuals/videos.json').write_text(json.dumps(dict(individual=individual_rows,comparisons=comparisons,reels=reels),indent=2)+'\n')
            review_index()
    summary=[]
    for m in MOVES:
        for s in ('player','foe'):
            line=dict(move=m,side=s)
            for v in VARIANTS:
                group=[r for r in rows if (r['variant'],r['move'],r['side'])==(v,m,s)]
                line[v]={key:statistics.median(r[key] for r in group) for key in ('primary','primary_ms','wrapper','wrapper_ms','ticks','work_max')}
                line[v]['range']=[min(r['primary'] for r in group),max(r['primary'] for r in group)]
                line[v]['gaps']=group[0]['step_gaps']
            summary.append(line)
    (OUTPUT/'measurements.json').write_text(json.dumps(dict(summary=summary,rows=rows),indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__': main()
