"""Native phase/reference analysis for the complete double-speed move suite."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import json
import statistics

from tools.pokedex_info_assets import constants
from .assets import Repository
from .cold_listing import ROOT, FRAME
from . import animation_reference as reference

OUTPUT = reference.OUTPUT / 'expansion'


def profile(task):
    variant, move, side, phase = task[:4]
    folder_name = task[4] if len(task)>4 else 'regression'
    folder = reference.OUTPUT / folder_name / variant / f'{move.lower()}-{side}-q{phase}'
    data = reference.summarize(folder / 'result.json')
    if not data['invocations']:
        raise RuntimeError(f'Missing animation: {folder}')
    result = dict(variant=variant, move=move, side=side, phase=phase, issues=data['issues'], scripts=[])
    for invocation in data['invocations']:
        for script in invocation['scripts']:
            states = script['states']
            groups = []
            for state in states:
                if not groups or state['script'] != groups[-1][-1]['script'] or state['delay'] > groups[-1][-1]['delay']:
                    groups.append([])
                groups[-1].append(state)
            stages = [dict(pc=group[0]['script'], wait=group[0]['delay'], ticks=len(group),
                           start=(group[0]['t']-script['start'])/FRAME,
                           elapsed=((groups[i+1][0]['t'] if i+1<len(groups) else script['start']+script['elapsed']*FRAME)
                                    - group[0]['t'])/FRAME)
                      for i,group in enumerate(groups)]
            objects = [dict(function=o['function'], param=o['samples'][0]['data'][12],
                            lifetime=o['lifetime'], ticks=len(o['samples']),
                            start=(o['start_t']-script['start'])/FRAME,
                            state_phases=o['phases']) for o in script['objects']]
            result['scripts'].append(dict(elapsed=script['elapsed'], stages=stages, objects=objects,
                                          sounds=script['sounds']))
    return result


def analyze(candidate='surf-intro', folder_name='regression'):
    moves = list(dict.fromkeys(reference.speed.REQUESTED+reference.speed.ADDED_NEW+reference.speed.ADDED_OLD+['DRAGON_DANCE']))
    tasks = [(variant,move,side,phase,folder_name) for variant in ('production',candidate) for move in moves
             for side in ('player','foe') for phase in (0,17556,35112,52668)]
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(profile,tasks))
    by = {(r['variant'],r['move'],r['side'],r['phase']):r for r in rows}
    names = {v:k for k,v in constants(ROOT/'constants/battle_anim_constants.asm').items()
             if k.startswith('BATTLE_ANIM_FUNC_')}
    summary = []
    for move in moves:
        for side in ('player','foe'):
            a = by['production',move,side,0]['scripts'][0]
            b = by[candidate,move,side,0]['scripts'][0]
            functions = []
            for f in sorted({o['function'] for o in a['objects']}):
                ao = [o for o in a['objects'] if o['function']==f]
                bo = [o for o in b['objects'] if o['function']==f]
                functions.append(dict(id=f,name=names.get(f,str(f)),normal=len(ao),double=len(bo),
                    normal_life=statistics.median(o['lifetime'] for o in ao),
                    double_life=statistics.median(o['lifetime'] for o in bo) if bo else None))
            summary.append(dict(move=move,side=side,normal_primary=a['elapsed'],double_primary=b['elapsed'],
                                delta=b['elapsed']-a['elapsed'],stage_counts=[len(a['stages']),len(b['stages'])],
                                functions=functions))
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/f'phases-{candidate}.json').write_text(json.dumps(dict(rows=rows,summary=summary),indent=2)+'\n')
    for move in moves:
        rs=[r for r in summary if r['move']==move]
        print(json.dumps(dict(move=move,delta=[round(r['delta'],2) for r in rs],
                             slower_functions=[(f['name'],round(f['normal_life'],1),round(f['double_life'],1))
                                               for f in rs[0]['functions'] if f['double_life'] is not None
                                               and f['normal_life']-f['double_life']>=5])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',default='surf-intro')
    parser.add_argument('--folder',default='regression')
    args=parser.parse_args()
    analyze(args.candidate,args.folder)
