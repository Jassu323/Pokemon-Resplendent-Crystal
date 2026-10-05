"""Saved native replay checks; do not reclassify timing parity as visual approval."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import statistics

from .animation_reference import OUTPUT, TARGETS, FRAME, events
from . import battle_pacing, global_speed as speed


def primary(folder):
    result = json.loads((folder / 'result.json').read_text())
    source = events(folder)
    invocation = result['requested_animations'][0]
    begin = invocation['start']['t']
    finish = begin + invocation['elapsed_t']
    spans = [e for e in source if e['event'] == 'perf_cost' and e['name'] == 'battle_script'
             and begin <= e['t'] < finish]
    span = min(spans, key=lambda e: e['t'])
    states = [e for e in source if e['event'] == 'anim_state' and
              span['t'] <= e['t'] < span['t'] + span['elapsed']]
    return result, span, states


def compare_case(path):
    old = Path('build/battle-pacing-20261004/replays-regression/final') / path.parent.name
    candidate, b, bs = primary(path.parent)
    reference, a, states = primary(old)
    signature = lambda s: (s['delay'], s['param'], s['shadow'])
    equal = len(states) == len(bs) and all(signature(x) == signature(y) for x, y in zip(states, bs))
    # Relocated script PCs are deliberately excluded; generated OAM and script
    # counters must still match for unmodified moves at every completed update.
    return dict(move=candidate['move'], side=candidate['side'], quarter=candidate['quarter'],
                issues=candidate['issues'], intentionally_retimed=candidate['move'] in TARGETS,
                logical_states_equal=equal, old_ticks=len(states), new_ticks=len(bs),
                old_primary=a['elapsed']/FRAME, new_primary=b['elapsed']/FRAME,
                delta_intervals=(b['elapsed']-a['elapsed'])/FRAME)


def regressions():
    paths = sorted((OUTPUT / 'regression/targeted').glob('*/result.json'))
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(compare_case, paths))
    unchanged = [r for r in rows if not r['intentionally_retimed']]
    report = dict(cases=len(rows), issues=[r for r in rows if r['issues']], rows=rows,
                  unchanged_cases=len(unchanged),
                  logical_differences=[r for r in unchanged if not r['logical_states_equal']],
                  primary_delta_min=min(r['delta_intervals'] for r in unchanged),
                  primary_delta_max=max(r['delta_intervals'] for r in unchanged))
    (OUTPUT / 'regression/comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    return {k: len(v) if isinstance(v, list) else v for k, v in report.items() if k != 'rows'}


def caustic(row):
    script = row['invocations'][0]['scripts'][0]
    begin = script['start']
    bubbles = sorted((o for o in script['objects'] if o['function'] == 140), key=lambda o: o['start_t'])
    # Native SFX_BUBBLEBEAM dispatch accompanies each script spawn. SFX_TOXIC
    # stays inside that individual bubble's transition to its pop state.
    launches = [e['t'] for e in script['sounds'] if e['sound'] == 81]
    pops = [e['t'] for e in script['sounds'] if e['sound'] == 127]
    onset = [(o['start_t']-begin)/FRAME for o in bubbles]
    impact = sorted(o['phases']['3']['start'] for o in bubbles if '3' in o['phases'])
    folder=OUTPUT/'replays'/row['variant']/f'caustic-{row["side"]}-q{row["quarter"]}'
    hardware=[e for e in events(folder) if e['event']=='hardware_oam']
    states={s['t']:s for s in script['states']}

    def publication(sound_times,ready_times):
        delays=[]
        for sound,ready in zip(sound_times,ready_times):
            t=round(begin+ready*FRAME)
            state=states[t]
            match=next((e for e in hardware if t <= e['t'] < t+4*FRAME and
                        e['bytes']==state['shadow']),None)
            delays.append((match['t']-begin)/FRAME-sound if match else None)
        return delays
    return dict(launch_sounds=launches, pop_sounds=pops, bubble_onsets=onset, pop_states=impact,
                launch_count=len(launches), pop_count=len(pops), bubbles=len(bubbles),
                launch_to_ready=[b-a for a,b in zip(launches,onset)],
                pop_to_ready=[b-a for a,b in zip(pops,impact)],
                launch_to_hardware=publication(launches,onset),
                pop_to_hardware=publication(pops,impact))


def phases():
    reference = json.loads((OUTPUT / 'reference.json').read_text())
    rows = []
    for row in reference['rows']:
        if row['move'] not in TARGETS or not row['invocations']:
            continue
        script = row['invocations'][0]['scripts'][0]
        states = script['states']
        gaps = [b['display']-a['display'] for a,b in zip(states,states[1:])]
        counts = {}
        for obj in script['objects']:
            counts[obj['function']] = counts.get(obj['function'],0)+1
        point = dict(variant=row['variant'], move=row['move'], side=row['side'], quarter=row['quarter'],
                     objects=len(script['objects']), functions=counts,
                     physical_gap_max=max(gaps,default=0),
                     peak_scanline=max(s['peak'] for s in states),
                     crowded_updates=sum(s['over_lines'] > 0 for s in states),
                     sounds=script['sounds'])
        point['object_lifetimes'] = {str(f):dict(
            count=sum(o['function']==f for o in script['objects']),
            minimum=min(o['lifetime'] for o in script['objects'] if o['function']==f),
            maximum=max(o['lifetime'] for o in script['objects'] if o['function']==f)) for f in counts}
        if row['move'] == 'CAUSTIC':
            point['caustic'] = caustic(row)
        rows.append(point)
    (OUTPUT / 'phase-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows


def work():
    rows=[]
    for variant in ('production','final','targeted'):
        for move in TARGETS:
            for side in ('player','foe'):
                folder=OUTPUT/'replays'/variant/f'{move.lower()}-{side}-q0'
                result,span,states=primary(folder)
                local=[e for e in events(folder) if span['t'] <= e['t'] < span['t']+span['elapsed']]
                costs={}
                for name in ('anim_command','anim_bg','anim_oam','anim_sine','anim_gfx','anim_wait'):
                    values=[e['elapsed']/FRAME for e in local if e['event']=='perf_cost' and e['name']==name]
                    if values:
                        costs[name]=dict(calls=len(values),median=statistics.median(values),
                                         maximum=max(values),total=sum(values))
                rows.append(dict(move=move,side=side,variant=variant,costs=costs))
    (OUTPUT/'work-audit.json').write_text(json.dumps(rows,indent=2)+'\n')


def costs():
    maps = {}
    for name,path in (('final',speed.BASE/'final/pokecrystal-global-double-speed.map'),
                      ('targeted',OUTPUT/'prototype/pokecrystal-targeted-motion.map')):
        sections = {}
        for m in re.finditer(r'SECTION: \$[0-9a-f]+(?:-\$[0-9a-f]+)? \(\$([0-9a-f]+) bytes?\) \["([^"]+)"\]',path.read_text()):
            sections[m[2]] = int(m[1],16)
        maps[name] = sections
    changes = {n:maps['targeted'].get(n,0)-maps['final'].get(n,0)
               for n in maps['final'].keys() | maps['targeted'].keys()
               if maps['targeted'].get(n,0)!=maps['final'].get(n,0)}
    old=(speed.BASE/'final/pokecrystal-global-double-speed.gbc').read_bytes()
    new=(OUTPUT/'prototype/pokecrystal-targeted-motion.gbc').read_bytes()
    rom0_changed=[i for i in range(0x4000) if old[i]!=new[i]]
    data=dict(section_changes=changes,total=sum(changes.values()),rom0_changed_offsets=rom0_changed,
              only_rom0_header_checksum_changed=rom0_changed==[0x14e,0x14f])
    (OUTPUT/'costs.json').write_text(json.dumps(data,indent=2)+'\n')
    return data


def main():
    battle_pacing.OUTPUT=OUTPUT
    audio=json.loads((OUTPUT/'audio/report.json').read_text())
    battle_pacing.compare_audio(audio['results'])
    audio_comparison=json.loads((OUTPUT/'audio/comparison.json').read_text())
    phases()
    work()
    report=dict(regression=regressions(),costs=costs(),
                audio={k:len(v) if isinstance(v,list) else v for k,v in audio_comparison.items()})
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
