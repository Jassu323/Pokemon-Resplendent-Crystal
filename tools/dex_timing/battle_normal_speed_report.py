"""Compact native motion, timer-content and resource audit for the clock trial."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import statistics

from .battle_normal_speed import BASE, MOVES, PHASES
from .animation_reference_audit import primary
from .animation_reference import events
from .battle_motion_revision_audit import sections
from . import global_speed as speed
from .cold_listing import FRAME, ROOT


def digest(values):
    return hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()


def compare(task):
    move, side, quarter = task
    name = f'{move.lower()}-{side}-q{quarter}'
    folders = [BASE / 'moves' / v / name for v in ('production', 'battle-normal')]
    captures = [primary(folder) for folder in folders]
    durations = [span['elapsed']/FRAME for _, span, _ in captures]
    signatures = [[(s['delay'], s['param'], s['shadow']) for s in states] for _, _, states in captures]
    details = []
    for folder, (_, span, states) in zip(folders, captures):
        selected = [e for e in events(folder) if span['t'] <= e['t'] < span['t']+span['elapsed']]
        sounds = [e for e in selected if e['event']=='perf_phase' and e['name'] in ('sound', 'stereo_sound')]
        details.append(dict(logical=digest(signatures[len(details)]), ticks=len(states),
            objects=digest([e['bytes'] for e in selected if e['event']=='anim_objects']),
            backgrounds=digest([e['bytes'] for e in selected if e['event']=='anim_background']),
            sounds=[dict(id=e['de'], kind=e['name'], interval=(e['t']-span['t'])/FRAME) for e in sounds],
            gaps=dict(Counter(b['display']-a['display'] for a,b in zip(states, states[1:]))),
            peak=max((s['peak'] for s in states), default=0),
            crowded_ticks=sum(bool(s['over_lines']) for s in states)))
    ids = lambda x: [(e['id'],e['kind']) for e in x['sounds']]
    sound_equal = ids(details[0]) == ids(details[1])
    return dict(move=move, side=side, quarter=quarter, normal=durations[0], candidate=durations[1],
        delta=durations[1]-durations[0], logical_equal=details[0]['logical']==details[1]['logical'],
        objects_equal=details[0]['objects']==details[1]['objects'],
        backgrounds_equal=details[0]['backgrounds']==details[1]['backgrounds'],
        sound_sequence_equal=sound_equal,
        sound_onset_max_delta=max((abs(b['interval']-a['interval']) for a,b in zip(details[0]['sounds'],details[1]['sounds'])),default=0) if sound_equal else None,
        details=details, issues=[r['issues'] for r,_,_ in captures if r['issues']])


def audio_audit():
    report = json.loads((BASE / 'audio/report.json').read_text())
    pairs = {}
    for row in report['results']:
        pairs.setdefault((row['species'],row['context'],row['quarter']),{})[row['variant']] = row
    comparisons = []
    for key, arms in pairs.items():
        a,b = arms['production'],arms['battle-normal']
        equal = len(a['segments']) == len(b['segments'])
        differences = []
        for i,(x,y) in enumerate(zip(a['segments'],b['segments'])):
            for name in ('expected_blocks','blocks','wave_sha256','frequencies'):
                if x[name] != y[name]:
                    differences.append(f'segment {i}: {name}')
            stopped = lambda row: [(e['event'],e.get('remaining')) for e in row['stops']]
            if stopped(x) != stopped(y):
                differences.append(f'segment {i}: completion/cancellation')
            if key[1] in ('player','catch','faint') and x['timer_configs'] != y['timer_configs']:
                differences.append(f'segment {i}: normal battle timer')
        if not equal:
            differences.append('segment count')
        comparisons.append(dict(species=key[0],context=key[1],quarter=key[2],differences=differences,
            normal_misses=a['known_misses'],candidate_misses=b['known_misses']))
    return dict(cases=report['cases'], paired=len(comparisons),
        differences=[r for r in comparisons if r['differences']],
        cases_with_misses=[r for r in comparisons if r['normal_misses'] or r['candidate_misses']],
        setup_failures=[r for r in report['results'] if r['issues']], comparisons=comparisons)


def main():
    tasks = [(m,s,q) for m in MOVES for s in ('player','foe') for q in PHASES]
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(compare,tasks))
    summaries = []
    for m in MOVES:
        for side in ('player','foe'):
            group = [r for r in rows if (r['move'],r['side'])==(m,side)]
            summaries.append(dict(move=m,side=side,
                normal=statistics.median(r['normal'] for r in group),
                candidate=statistics.median(r['candidate'] for r in group),
                delta=statistics.median(r['delta'] for r in group),
                largest_phase_delta=max(abs(r['delta']) for r in group)))
    old = sections(speed.BASE/'final/pokecrystal-global-double-speed.map')
    new = sections(BASE/'prototype/pokecrystal-battle-normal-speed.map')
    changes = {name:new.get(name,0)-old.get(name,0) for name in old.keys()|new.keys() if old.get(name,0)!=new.get(name,0)}
    source = BASE/'prototype/candidate'
    animation_files = ['data/moves/animations.asm'] + [str(p.relative_to(ROOT)) for p in (ROOT/'engine/battle_anims').glob('*.asm')]
    modified = [f for f in animation_files if (ROOT/f).read_bytes() != (source/f).read_bytes()]
    record = dict(paired_cases=len(rows), rows=rows, summary=summaries,
        logical_differences=[{k:v for k,v in r.items() if k!='details'} for r in rows if not r['logical_equal']],
        object_differences=sum(not r['objects_equal'] for r in rows),
        background_differences=sum(not r['backgrounds_equal'] for r in rows),
        sound_sequence_differences=sum(not r['sound_sequence_equal'] for r in rows),
        maximum_primary_delta=max(abs(r['delta']) for r in rows),
        modified_animation_sources=modified, section_changes=changes, net_bytes=sum(changes.values()),
        audio=audio_audit())
    (BASE/'comparison.json').write_text(json.dumps(record,indent=2)+'\n')
    with (BASE/'move-timings.csv').open('w', newline='') as stream:
        fields = ['move', 'side', 'production_intervals', 'prototype_intervals',
                  'production_ms', 'prototype_ms', 'delta_intervals', 'delta_ms',
                  'percent_change', 'maximum_offset_delta_intervals']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        ms = FRAME*1000/4194304
        for row in summaries:
            writer.writerow(dict(move=row['move'], side=row['side'],
                production_intervals=row['normal'], prototype_intervals=row['candidate'],
                production_ms=row['normal']*ms, prototype_ms=row['candidate']*ms,
                delta_intervals=row['delta'], delta_ms=row['delta']*ms,
                percent_change=row['delta']/row['normal']*100,
                maximum_offset_delta_intervals=row['largest_phase_delta']))
    print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in record.items() if k not in ('rows','summary','audio')}))
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in record['audio'].items() if k!='comparisons'}))


if __name__=='__main__':main()
