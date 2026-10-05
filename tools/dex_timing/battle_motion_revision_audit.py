"""Audit the Surf/intro revision without replacing the original trial evidence."""
from concurrent.futures import ProcessPoolExecutor
import json
import re
import statistics

from .animation_reference import OUTPUT, FRAME
from .animation_reference_audit import primary


def compare(path):
    row, span, current = primary(path.parent)
    _, old_span, old = primary(OUTPUT/'regression/targeted'/path.parent.name)
    signature = lambda r: (r['delay'],r['param'],r['shadow'])
    equal = [signature(r) for r in current] == [signature(r) for r in old]
    return dict(move=row['move'],side=row['side'],quarter=row['quarter'],issues=row['issues'],
        logical_equal=equal,old_intervals=old_span['elapsed']/FRAME,
        revised_intervals=span['elapsed']/FRAME)


def sections(path):
    return {m[2]:int(m[1],16) for m in re.finditer(
        r'SECTION: \$[0-9a-f]+(?:-\$[0-9a-f]+)? \(\$([0-9a-f]+) bytes?\) \["([^\"]+)"\]',
        path.read_text())}


def main():
    with ProcessPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(compare,sorted((OUTPUT/'regression/surf-intro').glob('*/result.json'))))
    unchanged = [r for r in rows if r['move']!='SURF']
    report = dict(cases=len(rows),failures=[r for r in rows if r['issues']],
        unchanged_cases=len(unchanged),changed_logical_states=[r for r in unchanged if not r['logical_equal']],rows=rows)
    old,new = [sections(OUTPUT/p/'pokecrystal-targeted-motion.map')
               for p in ('prototype','prototype-surf-intro')]
    report['section_changes']={n:new.get(n,0)-old.get(n,0) for n in old.keys()|new.keys()
                               if old.get(n,0)!=new.get(n,0)}
    report['net_bytes']=sum(report['section_changes'].values())
    reference=json.loads((OUTPUT/'reference.json').read_text())
    surf=[]
    for variant in ('production','targeted','surf-intro'):
        for side in ('player','foe'):
            group=[r for r in reference['rows'] if (r['variant'],r['move'],r['side'])==(variant,'SURF',side)]
            scripts=[r['invocations'][0]['scripts'][0] for r in group]
            surf.append(dict(variant=variant,side=side,
                primary_intervals=statistics.median(s['elapsed'] for s in scripts),
                phase_lengths={str(p):statistics.median(next(o for o in s['objects'] if o['function']==13)
                    ['phases'][str(p)]['last']-next(o for o in s['objects'] if o['function']==13)
                    ['phases'][str(p)]['start'] for s in scripts) for p in (1,2,3)},
                sound_spacing=[statistics.median(s['sounds'][i+1]['t']-s['sounds'][i]['t'] for s in scripts)
                               for i in range(3)]))
    report['surf']=surf
    (OUTPUT/'surf-intro-qualification/motion-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:len(v) if isinstance(v,list) and k!='surf' else v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':main()
