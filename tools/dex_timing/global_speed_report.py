"""Consolidate private speed qualification without discarding retest evidence."""
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import statistics

from .cold_listing import FRAME
from .global_speed import BASE, REQUESTED, ADDED_NEW, ADDED_OLD

HZ = 4194304


def read(path):
    return json.loads(path.read_text())


def script_steps(job):
    variant, move, side, start, duration = job
    path = BASE / 'moves' / variant / f'{move.lower()}-{side}-q0/events.jsonl.gz'
    count = 0
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            event = json.loads(line)
            if (event['event'] == 'perf_phase' and event['name'] == 'battle_step'
                    and start <= event['t'] < start + duration):
                count += 1
    return dict(variant=variant, move=move, side=side, steps=count)


def moves(output):
    results = []
    ordered = REQUESTED + ADDED_NEW + ADDED_OLD
    for variant in ('production', 'full', 'final'):
        for path in sorted((BASE / 'moves' / variant).glob('*/result.json')):
            row = read(path)
            if row['move'] not in ordered:
                continue
            row.pop('frames', None)
            results.append(row)
    by = {(r['variant'], r['move'], r['side'], r['quarter']): r for r in results}
    assert len(by) == 79 * 2 * 4 * 3
    assert not any(r['issues'] or r['misses'] for r in results)
    summary = []
    for move in ordered:
        for side in ('player', 'foe'):
            a = [by['production', move, side, q] for q in (0, 17556, 35112, 52668)]
            b = [by['final', move, side, q] for q in (0, 17556, 35112, 52668)]
            normal = [r['requested_animations'][0]['elapsed_t'] / FRAME for r in a]
            double = [r['requested_animations'][0]['elapsed_t'] / FRAME for r in b]
            differences = [y - x for x, y in zip(normal, double)]
            summary.append(dict(move=move, side=side, normal=statistics.median(normal),
                double=statistics.median(double), delta=statistics.median(differences),
                delta_min=min(differences), delta_max=max(differences),
                normal_counts=[len(r['requested_animations']) for r in a],
                double_counts=[len(r['requested_animations']) for r in b]))
    jobs = []
    for move in ordered:
        for side in ('player', 'foe'):
            for variant in ('production', 'final'):
                first = by[variant, move, side, 0]['requested_animations'][0]
                jobs.append((variant, move, side, first['start']['t'], first['elapsed_t']))
    with ProcessPoolExecutor(max_workers=16) as pool:
        counts = list(pool.map(script_steps, jobs))
    steps = {(r['variant'], r['move'], r['side']): r['steps'] for r in counts}
    step_changes = [dict(move=m, side=s, normal=steps['production', m, s],
                        double=steps['final', m, s]) for m in ordered for s in ('player', 'foe')
                    if steps['production', m, s] != steps['final', m, s]]
    report = dict(cases=len(results), failures=0, results=results, summary=summary,
                  script_step_changes=step_changes, script_steps=counts)
    (output / 'moves-qualified.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Whole game double speed move animation measurements', '',
        '2026-10-04. Generated from matching-link native battle replays, four input',
        'phases per move and side. No animation scripts, waits, motion functions or',
        'graphical assets were changed. This table is an observation, not a retiming.', '',
        'Each cell is **physical display intervals / milliseconds**. Values are medians.',
        'The difference is the median of paired differences; it need not equal the',
        'difference of the two marginal medians. One interval is 16.742706ms.', '',
        'The main table measures the **first requested `_PlayBattleAnim` invocation**',
        'through its actual return, including interrupts and waits. It is not whole',
        'turn duration or the sum of a multi-hit/rampage move. Every subsequent',
        'invocation and all four phase-specific durations remain in the qualified',
        'JSON under `build/global-speed-20261004/qualification/`.', '',
        'CPU/DIV-dependent RNG changes the number of hits and battle follow-through',
        'in some fixtures. Do not attribute those different counts to animation',
        'retiming. Fly/Dig/Solarbeam include charge and attack invocations; see the',
        'additional-invocation table below rather than using the first as the attack.', '']
    cell = lambda value: f'{value:.3f} / {value * FRAME * 1000 / HZ:.2f}'
    for side in ('player', 'foe'):
        lines += [f'## {side.title()} timing', '', '| Move | Normal | Double | Paired difference | Difference range in intervals |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for row in summary:
            if row['side'] == side:
                lines.append(f'| `{row["move"]}` | {cell(row["normal"])} | {cell(row["double"])} | {cell(row["delta"])} | {row["delta_min"]:.3f} to {row["delta_max"]:.3f} |')
        lines.append('')
    lines += ['## Subsequent requested invocations', '',
        'Each row is the chronological invocation position, not a universal named',
        'animation stage. Medians use whichever of the four runs reached that',
        'position. Unequal run counts/RNG make these descriptive, not perfectly',
        'matched causal comparisons. An invocation still running when the replay',
        'ended has no duration; it is excluded rather than counted as zero.', '',
        '| Move | Side | Invocation | Normal intervals / ms | Double intervals / ms | Normal / double runs |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for move in ordered:
        for side in ('player', 'foe'):
            a = [by['production', move, side, q]['requested_animations'] for q in (0, 17556, 35112, 52668)]
            b = [by['final', move, side, q]['requested_animations'] for q in (0, 17556, 35112, 52668)]
            for n in range(1, max(map(len, a + b))):
                av = [r[n]['elapsed_t'] / FRAME for r in a if len(r) > n and r[n]['elapsed_t'] is not None]
                bv = [r[n]['elapsed_t'] / FRAME for r in b if len(r) > n and r[n]['elapsed_t'] is not None]
                lines.append(f'| `{move}` | {side} | {n + 1} | {cell(statistics.median(av)) if av else "not reached"} | {cell(statistics.median(bv)) if bv else "not reached"} | {len(av)} / {len(bv)} |')
    lines += ['', '## Script progression audit', '',
              f'First-invocation command-dispatch counts were compared for all 158 move/side pairs at phase zero. Differences: **{len(step_changes)}**.', '']
    for row in step_changes:
        lines.append(f'- `{row["move"]}`, {row["side"]}: {row["normal"]} normal, {row["double"]} double command dispatches.')
    (output / 'move-animation-measurements.md').write_text('\n'.join(lines) + '\n')
    return dict(cases=len(results), failures=0, script_step_changes=step_changes)


def audio(output):
    old = [r for r in read(BASE / 'audio/report.json')['results'] if r['variant'] == 'production']
    new = read(BASE / 'audio/report-final.json')['results']
    by = {(r['species'], r['context'], r['quarter']): r for r in old}
    errors, segments = [], 0
    for row in new:
        baseline = by[row['species'], row['context'], row['quarter']]
        if row['issues'] or row['known_misses'] or len(row['segments']) != len(baseline['segments']):
            errors.append(dict(species=row['species'], context=row['context'], reason='setup, miss or segment count'))
        for a, b in zip(baseline['segments'], row['segments']):
            segments += 1
            if (a['expected_blocks'] != b['expected_blocks'] or a['frequencies'] != b['frequencies']
                    or a['wave_blocks'] != b['wave_blocks'][:a['blocks']]
                    or b['blocks'] != b['expected_blocks'] or b['speed_values'] != [1]):
                errors.append(dict(species=row['species'], context=row['context'], reason='sample or physical settings'))
    result = dict(cases=len(new), segments=segments, issues=errors,
                  production_misses=sum(bool(r['known_misses']) for r in old))
    (output / 'audio-qualified.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    output = BASE / 'qualification'
    output.mkdir(exist_ok=True)
    result = dict(moves=moves(output), audio=audio(output))
    gameplay = [read(p) for variant in ('production', 'final')
                for p in sorted((BASE / 'gameplay' / variant).glob('*/result.json'))]
    result['gameplay'] = dict(cases=len(gameplay), failures=sum(bool(r['issues']) for r in gameplay))
    (output / 'gameplay-qualified.json').write_text(json.dumps(gameplay, indent=2) + '\n')
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
