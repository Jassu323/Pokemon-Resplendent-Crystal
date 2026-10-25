"""Analyze and encode the native three-way Thunderbolt captures."""
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import subprocess
from PIL import Image, ImageDraw, ImageFont

from .thunderbolt import OUT, ROOT, EMERALD, symbols

FRAME = 70224
FPS = 4194304 / FRAME
GBA_FRAME = FRAME * 4


def events(folder):
    path = folder / 'events.jsonl'
    return [json.loads(line) for line in (path.open() if path.exists() else gzip.open(folder / 'events.jsonl.gz','rt'))]


def csv_write(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def groups(rows, signature):
    return [list(group) for _, group in itertools.groupby(rows, signature)]


def display_groups(rows, signature, clock):
    runs = []
    for row in rows:
        if (not runs or signature(runs[-1][-1]) != signature(row)
                or row[clock] != runs[-1][-1][clock] + 1):
            runs.append([])
        runs[-1].append(row)
    return runs


def crystal(folder):
    result = json.loads((folder / 'result.json').read_text())
    es = events(folder)
    invocation = result['requested_animations'][0]
    start = invocation['start']['t']
    scripts = [e for e in es if e['event']=='perf_cost' and e['name']=='battle_script'
               and start <= e['t'] < start + invocation['elapsed_t']]
    primary = scripts[0]
    a, b = primary['t'], primary['t']+primary['elapsed']
    states = [e for e in es if e['event']=='anim_state' and a<=e['t']<b]
    objects = {e['t']: bytes.fromhex(e['bytes']) for e in es if e['event']=='anim_objects'}
    ticks = [e for e in es if e['event']=='perf_phase' and e['name']=='anim_tick' and a<=e['t']<b]
    holds = []
    tracks = defaultdict(list)
    for state in states:
        raw = objects[state['t']]
        for slot in range(14):
            obj = raw[slot*20:slot*20+20]
            if not obj[0]: continue
            frameset = int.from_bytes(obj[3:5],'little')
            key = (slot, obj[0], frameset, obj[8], obj[9])
            tracks[key].append(dict(t=state['t'], pose=obj[18] if frameset>=256 else obj[14],
                invisible=frameset>=256 and obj[18] in (0xfd, 0xfc), frame_command=obj[14], duration=obj[13]))
    for key, track in tracks.items():
        for run in groups(track, lambda x:(x['pose'],x['invisible'])):
            next_t = next((r['t'] for r in states if r['t'] > run[-1]['t']), b)
            holds.append(dict(slot=key[0], object_id=key[1], frameset=key[2], x=key[3], y=key[4],
                pose=run[0]['pose'], invisible=run[0]['invisible'], logical_updates=len(run),
                start_intervals=(run[0]['t']-a)/FRAME, held_intervals=(next_t-run[0]['t'])/FRAME,
                held_ms=(next_t-run[0]['t'])/4194.304))
    csv_write(folder/'object-state-holds.csv', sorted(holds,key=lambda x:x['start_intervals']))
    intervals = [(y['t']-x['t'])/FRAME for x,y in zip(ticks,ticks[1:])]
    work = [(r['t']-t['t'])/FRAME for t,r in zip(ticks,states)]
    first_bolt = min(row['start_intervals'] for row in holds if row['frameset']==296)
    frames = [e for e in es if e['event']=='perf_frame']
    hardware = {e['display']: e['bytes'] for e in es if e['event']=='hardware_oam'}
    candidates = defaultdict(list)
    for state in states: candidates[state['shadow']].append(state)
    published = []
    for frame in frames:
        matching = [s for s in candidates.get(hardware.get(frame['display']),[]) if s['t']<=frame['t']]
        if not matching: continue
        state = matching[-1]; raw=objects[state['t']]
        if not a<=frame['boundary_t']<b: continue
        for slot in range(14):
            obj=raw[slot*20:slot*20+20]
            if obj[0] and int.from_bytes(obj[3:5],'little') in [277,296,278]:
                published.append(dict(display=frame['display'], slot=slot, object_id=obj[0],
                    frameset=int.from_bytes(obj[3:5],'little'), pose=obj[18], flags=obj[19],
                    publication_age_intervals=(frame['boundary_t']-state['t'])/FRAME))
    csv_write(folder/'published-state-per-frame.csv', published)
    publication_holds=[]
    by_object=defaultdict(list)
    for p in published: by_object[(p['slot'],p['object_id'],p['frameset'])].append(p)
    for key,track in by_object.items():
        for run in display_groups(track,lambda p:(p['pose'],p['flags']),'display'):
            publication_holds.append(dict(slot=key[0],object_id=key[1],frameset=key[2],pose=run[0]['pose'],
                start_display=run[0]['display'],held_frames=len(run),held_ms=len(run)*1000/FPS))
    csv_write(folder/'published-state-holds.csv',publication_holds)
    first_published = next(f for f in frames if any(p['display']==f['display'] and p['frameset']==296 for p in published))
    return dict(system=result['variant'], side=result['side'], quarter=result['quarter'],
        script_start=a, script_end=b, script_intervals=primary['elapsed']/FRAME,
        script_ms=primary['elapsed']/4194.304, wrapper_intervals=invocation['elapsed_t']/FRAME,
        wrapper_ms=invocation['elapsed_t']/4194.304, updates=len(ticks),
        update_intervals=dict(Counter(round(d) for d in intervals)),
        work_median_intervals=statistics.median(work), work_max_intervals=max(work),
        first_bolt_intervals=first_bolt, first_bolt_t=first_published['boundary_t'],
        first_bolt_visible_intervals=(first_published['boundary_t']-a)/FRAME,
        holds=holds, published=published, publication_holds=publication_holds, issues=result['issues'],
        capture_start=result.get('capture_start_t'), frames=frames, folder=str(folder))


def gba(folder):
    result=json.loads((folder/'result.json').read_text()); es=events(folder); sy=symbols()
    frames=[e for e in es if e['event']=='frame']
    starts=[e for e in es if e.get('name')=='DoMoveAnim' and e['r'][0]==85]
    assert len(starts)==1, starts
    start=starts[0]
    end=next(e for e in es if e.get('name')=='BattleMainCB2' and e['t']>start['t'] and not e['active'])
    end_cmd=next(e for e in es if e.get('name')=='BattleAnimEnd' and e['t']>start['t'])
    active=[e for e in frames if start['t']<=e['t']<end['t']]
    phase_states=[]; poses=defaultdict(list); sprite_tracks=defaultdict(list); affine=[]
    templates={sy['gElectricBoltSegmentSpriteTemplate']:'bolt', sy['gThunderboltOrbSpriteTemplate']:'orb',
               sy['gSparkElectricityFlashingSpriteTemplate']:'spark'}
    for frame in active:
        data=bytes.fromhex(frame['sprites']); per=defaultdict(list)
        for slot in range(64):
            raw=data[slot*68:slot*68+68]
            template=int.from_bytes(raw[20:24],'little')
            if not raw[62]&1 or template not in templates: continue
            name=templates[template]
            x=int.from_bytes(raw[32:34],'little',signed=True); y=int.from_bytes(raw[34:36],'little',signed=True)
            x2=int.from_bytes(raw[36:38],'little',signed=True); y2=int.from_bytes(raw[38:40],'little',signed=True)
            tile=int.from_bytes(raw[4:6],'little')&1023
            invisible=bool(raw[62]&4)
            center_x=int.from_bytes(raw[40:41],'little',signed=True)
            center_y=int.from_bytes(raw[41:42],'little',signed=True)
            row=dict(frame=frame['frame'], component=name, slot=slot, x=x,y=y,x2=x2,y2=y2,
                     center_x=center_x,center_y=center_y,
                     tile=tile, anim_command=raw[43], anim_delay=raw[44]&63, invisible=invisible,
                     data=raw[46:62].hex())
            phase_states.append(row); sprite_tracks[(name,slot)].append(row)
            if name=='orb':
                matrix=(int.from_bytes(raw[2:4],'little')>>9)&31
                oam=bytes.fromhex(frame['hardware_oam'])
                values=[int.from_bytes(oam[matrix*32+6+j*8:matrix*32+8+j*8],'little',signed=True) for j in range(4)]
                affine.append(dict(frame=frame['frame'],slot=slot,invisible=invisible,matrix=matrix,
                    pa=values[0],pb=values[1],pc=values[2],pd=values[3]))
            per[(name,x) if name=='bolt' else (name,0)].append((x+x2,y+y2,tile,invisible))
        for key, values in per.items(): poses[key].append(dict(frame=frame['frame'],pose=tuple(sorted(values))))
    csv_write(folder/'sprite-state-per-frame.csv',phase_states)
    csv_write(folder/'orb-affine-per-frame.csv',affine)
    holds=[]
    for (component,x), track in poses.items():
        for run in display_groups(track,lambda x:x['pose'],'frame'):
            holds.append(dict(component=component,x=x, start_intervals=run[0]['frame']-start['frame'],
                held_intervals=len(run),held_ms=len(run)*1000/FPS,pose=str(run[0]['pose'])))
    csv_write(folder/'component-state-holds.csv',sorted(holds,key=lambda x:x['start_intervals']))
    sprite_holds=[]
    for (name,slot),track in sprite_tracks.items():
        for run in display_groups(track,lambda x:(x['tile'],x['x2'],x['y2'],x['invisible']),'frame'):
            sprite_holds.append(dict(component=name,slot=slot,start=run[0]['frame']-start['frame'],
                held_frames=len(run),tile=run[0]['tile'],x2=run[0]['x2'],y2=run[0]['y2'],invisible=run[0]['invisible']))
    csv_write(folder/'individual-sprite-holds.csv',sprite_holds)
    # Associate actual hardware OAM by the bolt's dedicated tile range and
    # original column. Unlike Sprite RAM, this is the pose used for rendering.
    bolt_tiles={s['tile'] for s in phase_states if s['component']=='bolt'}
    bolt_x={s['x']+s['center_x']:s['x'] for s in phase_states if s['component']=='bolt'}
    hardware_poses=defaultdict(list)
    for f in active:
        oam=bytes.fromhex(f['hardware_oam']); per=defaultdict(list)
        for i in range(0,1024,8):
            attr0=int.from_bytes(oam[i:i+2],'little'); attr1=int.from_bytes(oam[i+2:i+4],'little')
            attr2=int.from_bytes(oam[i+4:i+6],'little'); x=attr1&511; tile=attr2&1023
            if (attr0>>8)&3==2 or tile not in bolt_tiles or x not in bolt_x: continue
            per[bolt_x[x]].append((attr0&255,tile,attr0>>14,attr1>>14))
        for x,pose in per.items(): hardware_poses[x].append(dict(frame=f['frame'],pose=tuple(sorted(pose))))
    publication_holds=[]
    for x,track in hardware_poses.items():
        for run in display_groups(track,lambda p:p['pose'],'frame'):
            publication_holds.append(dict(x=x,pose=str(run[0]['pose']),segments=len(run[0]['pose']),
                start_display=run[0]['frame'],held_frames=len(run),held_ms=len(run)*1000/FPS))
    csv_write(folder/'published-state-holds.csv',publication_holds)
    updates=[e for e in es if e.get('name')=='BattleMainCB2' and start['t']<=e['t']<end['t']]
    intervals=[(y['t']-x['t'])/GBA_FRAME for x,y in zip(updates,updates[1:])]
    def visible_bolt(frame):
        tiles={s['tile'] for s in phase_states if s['frame']==frame['frame'] and s['component']=='bolt'}
        oam=bytes.fromhex(frame['hardware_oam'])
        return any(int.from_bytes(oam[i+4:i+6],'little')&1023 in tiles and
                   not (oam[i+1]&3==2) for i in range(0,1024,8))
    first=next(e for e in active if visible_bolt(e))
    return dict(system='emerald',side=result['side'],phase=result['phase'],traced=True,
        script_start=start['t'],script_end=end['t'],script_intervals=(end['t']-start['t'])/GBA_FRAME,
        script_ms=(end['t']-start['t'])/16777.216, end_command_intervals=(end_cmd['t']-start['t'])/GBA_FRAME,
        updates=len(updates),update_intervals=dict(Counter(round(d) for d in intervals)),
        first_bolt_intervals=(first['t']-start['t'])/GBA_FRAME,first_bolt_t=first['t'],holds=holds,
        first_bolt_visible_intervals=(first['t']-start['t'])/GBA_FRAME,publication_holds=publication_holds,
        capture_start=result['capture_start']['t'],frames=frames,folder=str(folder),
        native_audio_rate=result['capture_start']['audio_rate'],
        affine_states=affine,
        sound_cues=[e for e in es if e.get('name','').startswith('PlaySE') and start['t']<=e['t']<end['t']])


def parity():
    rows=[]
    for side in ['player','foe']:
        for q in range(4):
            a=events(OUT/'gba'/f'{side}-q{q}-trace'); b=events(OUT/'gba'/f'{side}-q{q}-plain')
            a=[e for e in a if e['event']=='frame']; b=[e for e in b if e['event']=='frame']
            fields=['frame','pixels','script','active','sprites','tasks','shadow_oam','hardware_oam','palettes']
            differences=[i for i,(x,y) in enumerate(zip(a,b)) if any(x[k]!=y[k] for k in fields)]
            rows.append(dict(side=side,phase=q,frames=len(a),same_length=len(a)==len(b),differences=differences))
    return rows


def encode(row):
    folder=Path(row['folder']); emerald=row['system']=='emerald'
    frame_cycles=GBA_FRAME if emerald else FRAME; hz=16777216 if emerald else 4194304
    frames=row['frames']; boundary=lambda f:f['t'] if emerald else f['boundary_t']
    first=max(0,next(i for i,f in enumerate(frames) if boundary(f)>=row['script_start'])-4)
    last=min(len(frames)-1,next(i for i,f in enumerate(frames) if boundary(f)>=row['script_end'])+24)
    offset=max(0,(boundary(frames[first])-frame_cycles-row['capture_start'])/hz)
    target=OUT/'videos'/f'{row["system"]}-{row["side"]}.mp4'; target.parent.mkdir(exist_ok=True)
    if emerald:
        video=['-f','rawvideo','-pixel_format','rgb24','-video_size','240x160','-framerate',f'{4194304}/{FRAME}',
               '-skip_initial_bytes',str(first*240*160*3),'-i',str(folder/'video.rgb')]
        rate=str(row['native_audio_rate']); scale='scale=720:480:flags=neighbor'
    else:
        video=['-framerate',f'{4194304}/{FRAME}','-start_number',str(frames[first]['display']),'-i',str(folder/'frame-%03d.ppm')]
        rate='44100'; scale='scale=640:576:flags=neighbor'
    subprocess.run(['ffmpeg','-v','error','-y',*video,'-f','s16le','-ar',rate,'-ac','2',
        '-ss',str(offset),'-i',str(folder/'audio.raw'),'-frames:v',str(last-first+1),'-vf',scale,
        '-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
        '-movflags','+faststart',str(target)],check=True)
    row.update(video=str(target),video_first=first,video_last=last,
               video_first_t=boundary(frames[first])-frame_cycles,
               bolt_video_frame=next(i for i,f in enumerate(frames[first:last+1]) if boundary(f)>=row['first_bolt_t']))
    return row


def comparison(task):
    side,alignment,rows=task
    selected=[next(r for r in rows if r['system']==s and r['side']==side) for s in ['emerald','production','final']]
    anchors=[r['bolt_video_frame'] if alignment=='first-bolt' else
             round((r['script_start']-r['video_first_t'])/(GBA_FRAME if r['system']=='emerald' else FRAME)) for r in selected]
    anchor=max(anchors)+6
    length=max(r['video_last']-r['video_first']+1+anchor-a for r,a in zip(selected,anchors))
    labels=['Emerald / vanilla','Resplendent / production','Resplendent / double speed']
    target=OUT/'videos'/f'comparison-{side}-{alignment}.mp4'
    process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24',
        '-video_size','2160x544','-framerate',f'{4194304}/{FRAME}','-i','pipe:0','-an',
        '-c:v','libx264','-crf','16','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
    font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',22)
    small=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',18)
    gba_file=(Path(selected[0]['folder'])/'video.rgb').open('rb')
    try:
        for n in range(length):
            image=Image.new('RGB',(2160,544),(22,22,22)); draw=ImageDraw.Draw(image)
            for i,(r,a,label) in enumerate(zip(selected,anchors,labels)):
                index=min(r['video_last'],max(r['video_first'],r['video_first']+n-(anchor-a)))
                if r['system']=='emerald':
                    gba_file.seek(index*240*160*3)
                    frame=Image.frombytes('RGB',(240,160),gba_file.read(240*160*3))
                else:
                    frame=Image.open(Path(r['folder'])/f'frame-{r["frames"][index]["display"]:03d}.ppm').convert('RGB')
                frame=frame.resize((frame.width*3,frame.height*3),Image.Resampling.NEAREST)
                image.paste(frame,(i*720+(720-frame.width)//2,64))
                draw.text((i*720+16,10),label,font=font,fill='white')
                draw.text((i*720+16,38),f'Interval {n-anchor:+d} from {alignment}',font=small,fill='white')
            process.stdin.write(image.tobytes())
            if n==anchor+18: image.save(target.with_suffix('.png'))
    finally:
        gba_file.close(); process.stdin.close()
    if process.wait(): raise RuntimeError('Comparison encoding failed')
    return str(target)


def main():
    rows=[]
    for variant in ['production','final']:
        for side in ['player','foe']:
            for q in [0,17556,35112,52668]:
                rows.append(crystal(OUT/'crystal'/variant/f'thunderbolt-{side}-q{q}'))
    for side in ['player','foe']:
        for q in range(4): rows.append(gba(OUT/'gba'/f'{side}-q{q}-trace'))
    assert len(rows)==24 and all(r['script_intervals']>0 for r in rows)
    assert not any(r.get('issues') for r in rows)
    observer_parity=parity()
    assert all(r['same_length'] and not r['differences'] for r in observer_parity)
    previews=[r for r in rows if r.get('quarter',r.get('phase'))==0]
    with ProcessPoolExecutor(max_workers=6) as pool:
        previews=list(pool.map(encode,previews))
    with ProcessPoolExecutor(max_workers=4) as pool:
        comparisons=list(pool.map(comparison,[(s,a,previews) for s in ['player','foe'] for a in ['script','first-bolt']]))
    data=dict(refresh=FPS, rows=rows, previews=previews, comparisons=comparisons,gba_observer_parity=observer_parity)
    (OUT/'measurements.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(previews=[{k:v for k,v in r.items() if k in ['system','side','script_intervals','script_ms','wrapper_intervals','updates','update_intervals','first_bolt_intervals','video']} for r in previews],
                         gba_parity=data['gba_observer_parity']),indent=2))


if __name__=='__main__': main()
