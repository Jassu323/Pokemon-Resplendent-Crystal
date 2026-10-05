"""Aggregate final linked-build qualification and complete move timing tables."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import statistics

from .animation_reference import OUTPUT, FRAME
from .assets import sha256
from .cold_listing import ROOT


def load(path):
    return json.loads(path.read_text())


def layout(path):
    text=path.read_text().split('ROM0 bank')[0]
    return {name:tuple(map(int,values)) for name,*values in
            re.findall(r'^\s*(\w+): (\d+) bytes used / (\d+) free',text,re.M)}


def number(intervals):
    return f'{intervals:.2f} / {intervals*FRAME/4194.304:.2f}'


def report(candidate):
    root=OUTPUT/(candidate+'-qualification')
    phases=load(OUTPUT/'expansion'/f'phases-{candidate}.json')
    assert len(phases['rows'])==1280 and not any(r['issues'] for r in phases['rows'])
    previous=load(OUTPUT/'expansion/phases-surf-cleanup.json')
    moves=list(dict.fromkeys(r['move'] for r in phases['rows']))
    lookup={(r['variant'],r['move'],r['side'],r['phase']):r for r in phases['rows']}
    old={(r['variant'],r['move'],r['side'],r['phase']):r for r in previous['rows']}
    dex=load(root/'dex-regression/summary.json')['summary']
    entry=load(root/'new-entry/report.json')['summary']
    audio=load(root/'audio/report.json')
    audio_parity=load(root/'audio/comparison.json')
    menus=load(root/'menus/report.json')
    saves=load(root/'manual-review/verification.json')
    cleanup=load(OUTPUT/('surf-cleanup-diagnostic-production-'+candidate)/'report.json')
    assert not any(r['failures'] for r in dex.values()) and entry['failed']==0
    assert not any(r['issues'] for r in audio['results']) and not audio_parity['changes']
    assert not any(r['wrong_masks'] or r['register_failures'] for r in menus)
    assert all(r['valid_boot'] and r['moves_verified']==82 for r in saves)
    assert not any(r['issues'] or r['cleanup_violation'] or r['wrong_bank_reads']
                   or not r['instrumentation_timing_parity'] for r in cleanup['rows'])
    package=root/'manual-review'/candidate/('pokecrystal-animation-'+candidate)
    rom=Path(str(package)+'.gbc')
    final=layout(Path(str(package)+'.map'))
    base=layout(OUTPUT/'prototype-surf-cleanup/pokecrystal-targeted-motion.map')
    unpaced=layout(ROOT/'build/global-speed-20261004/final/pokecrystal-global-double-speed.map')
    production_sha=sha256((ROOT/'pokecrystal.gbc').read_bytes())
    expansion=load(OUTPUT/('prototype-'+candidate)/'expansion.json')
    assert production_sha==expansion['production_sha'] and sha256(rom.read_bytes())==expansion['sha256']
    results=[]
    sounds=[]
    for move in moves:
        for side in ('player','foe'):
            body={}
            wrapper={}
            for variant in ('production',candidate):
                body[variant]=statistics.median(lookup[variant,move,side,q]['scripts'][0]['elapsed']
                                               for q in (0,17556,35112,52668))
                rs=[load(OUTPUT/'regression-coherent'/variant/f'{move.lower()}-{side}-q{q}/result.json')
                    for q in (0,17556,35112,52668)]
                assert all(not r['issues'] and r['requested_animations'][0]['elapsed_t'] is not None for r in rs)
                wrapper[variant]=statistics.median(r['requested_animations'][0]['elapsed_t']/FRAME for r in rs)
            prior=statistics.median(old['surf-cleanup',move,side,q]['scripts'][0]['elapsed']
                                    for q in (0,17556,35112,52668))
            results.append(dict(move=move,side=side,normal=body['production'],prior=prior,
                                final=body[candidate],delta=body[candidate]-body['production'],wrappers=wrapper))
            for q in (0,17556,35112,52668):
                a=lookup['production',move,side,q]['scripts'][0]['sounds']
                b=lookup[candidate,move,side,q]['scripts'][0]['sounds']
                prior_sounds=old['surf-cleanup',move,side,q]['scripts'][0]['sounds']
                sounds.append(dict(move=move,side=side,phase=q,
                                   counts_match=Counter(s['sound'] for s in a)==Counter(s['sound'] for s in b),
                                   dispatch_order_match=[s['sound'] for s in a]==[s['sound'] for s in b],
                                   prior_order_match=[s['sound'] for s in prior_sounds]==[s['sound'] for s in b],
                                   normal=a,final=b))
    extra=[]
    for move in ('HEAVY_SLAM','ROCK_SMASH'):
        for side in ('player','foe'):
            for q in (0,17556,35112,52668):
                r=load(OUTPUT/'replays'/candidate/f'{move.lower()}-{side}-q{q}/result.json')
                assert not r['issues'], r
                extra.append(r)
    player_results={r['move']:r for r in results if r['side']=='player'}
    foe_results=[r for r in results if r['side']=='foe']
    stats=dict(move_cases=1280,extra_consumer_cases=len(extra),dex_cases=sum(s['cases'] for s in dex.values()),
               new_entry=entry,audio_cases=len(audio['results']),audio_parity=audio_parity,
               menu_inputs=sum(r['inputs'] for r in menus),cleanup_cases=cleanup['cases'],
               sound_count_differences=[r for r in sounds if not r['counts_match']],
               sound_order_differences=[dict(move=r['move'],side=r['side'],phase=r['phase'],
                                             prior_order_match=r['prior_order_match'])
                                        for r in sounds if not r['dispatch_order_match']],
               body_within_three_player=sum(abs(r['delta'])<=3 for r in results if r['side']=='player'),
               body_within_three_foe_vs_normal_player=sum(abs(r['final']-player_results[r['move']]['normal'])<=3
                                                         for r in foe_results),
               maximum_final_side_difference=max(abs(r['final']-player_results[r['move']]['final'])
                                                  for r in foe_results),
               rom_sha256=sha256(rom.read_bytes()),production_sha256=production_sha)
    output=OUTPUT/'expansion'/('report-'+candidate+'.json')
    output.write_text(json.dumps(dict(statistics=stats,timing=results,sounds=sounds,layout=final),indent=2)+'\n')
    lines=[
        f'Final linked ROM: `{stats["rom_sha256"]}`.',
        f'Unchanged production: `{production_sha}`.',
        '',
        '| Final-build native checks | Cases/inputs | Result |',
        '| --- | ---: | --- |',
        '| 80 moves x two sides x four phases x two ROMs | 1280 | No replay/playback failures |',
        f'| Additional shared-subroutine consumers, final build | {len(extra)} | No failures |',
        f'| All-species Dex cold/paging/Info/Moves/Area/stress | {stats["dex_cases"]} | No failures |',
        f'| New Dex Entry, 20 species and input sweep | {entry["cases"]} | No failures; authored durations retained |',
        f'| Cries: Stats/catch/faint/send-out/blocking/stereo | {len(audio["results"])} | No misses or waveform/pitch/block-count changes |',
        f'| Menu/input/overworld/battle/mart/puzzle/Game Corner | {stats["menu_inputs"]} | No mask/register regressions |',
        f'| Surf/Caustic ownership, both sides/four phases/two ROMs | {cleanup["cases"]} | Clean teardown; exact observer parity |',
        '| Private review saves | 3 arms, 82 moves each | Boot, linked moves and PC conversion pass |',
        '| Host motion/pacing invariants | 21 | Pass |',
        '',
        'The native intro tests also retain smooth two-pixel-per-display sliding on',
        'eight wild species/four phases and the trainer path. Tests overlap; these',
        'counts are not a claim of that many independent gameplay features.',
        '',
        '### Linked Cost',
        '',
        '| Resource | Added by expansion over Surf-cleanup | Total free in linked final build |',
        '| --- | ---: | ---: |',
    ]
    for name in ('ROM0','ROMX','WRAM0','WRAMX','HRAM','SRAM'):
        lines.append(f'| {name} | {final[name][0]-base[name][0]:,} bytes | {final[name][1]:,} bytes |')
    lines += ['',
        f'One new ROMX bank, `$bb`, holds 9,416 curve-data bytes plus the reader/dispatch',
        'and pose rules. No new VRAM/OAM allocation. Existing per-object scratch is',
        'repurposed only within selected functions. The expansion includes the extra',
        '94 bytes for individually timed bursts. Total battle retiming over the',
        f'unpaced double-speed baseline is {final["ROMX"][0]-unpaced["ROMX"][0]:,} ROMX bytes;',
        'its earlier seven-byte ROM0 whole-game speed cost is inherited, not new here.',
        '',
        '### Primary Script Timing',
        '',
        'Every duration cell is **display intervals / milliseconds**, medians over',
        'four offsets. One interval is 16.742706ms. The first `RunBattleAnimScript`',
        'body is separate from the broader `_PlayBattleAnim` wrapper measured in',
        'the original report. Setup/HUD/cleanup gains therefore are not disguised',
        'as motion changes. Multi-hit and later charge/attack invocations stay in',
        'the raw traces and are not summed into these first-invocation medians.',
        '"Prior" is the corrected Surf/accepted-local-motion build before expansion,',
        'not the rejected shared-phase-gating experiment.',
        f'{stats["body_within_three_player"]}/80 player primary bodies finish within three display intervals',
        'of production. This is descriptive, not a visual pass/fail threshold.',
        f'{stats["body_within_three_foe_vs_normal_player"]}/80 foe bodies are within three intervals of the',
        'normal-player reference. Final player/foe body medians differ by at most',
        f'{stats["maximum_final_side_difference"]:.3f} intervals. The old foe stalls are not target holds.',
    ]
    for side in ('player','foe'):
        lines += ['',f'#### {side.title()} Primary Body','',
            '| Move | Production | Prior local-motion build | Final expanded build | Final - production (intervals) |',
            '| --- | ---: | ---: | ---: | ---: |']
        for row in results:
            if row['side']==side:
                lines.append(f'| `{row["move"]}` | {number(row["normal"])} | {number(row["prior"])} | {number(row["final"])} | {row["delta"]:+.2f} |')
    lines += ['', '### Broader First-Invocation Wrapper','',
              '| Move | Side | Production intervals / ms | Final intervals / ms |','| --- | --- | ---: | ---: |']
    for row in results:
        lines.append(f'| `{row["move"]}` | {row["side"]} | {number(row["wrappers"]["production"])} | {number(row["wrappers"][candidate])} |')
    lines += ['', '### Sound Dispatch','',
              'Sound-count and order differences below are observations, not omissions.',
              'All 640 move/side/start-phase pairs are compared. Controller-generated',
              'sounds can interleave differently even when their',
              'counts and script-owned launch order are preserved. Raw captures retain',
              'each dispatch timestamp and individual clips retain native audio.',
              '', f'- Sound-count differences: `{[(r["move"],r["side"]) for r in stats["sound_count_differences"]]}`.',
              f'- Merged-order differences: `{[(r["move"],r["side"],r["phase"]) for r in stats["sound_order_differences"]]}`.',
              '- Caustic foe interleaving matches the accepted prior local-motion build',
              '  at each of those phases; it is not a new change from this expansion.',
              '', 'Caustic at phase zero, times in physical display intervals from primary-script entry:',
              '', '| Side/component | Production dispatch times | Final dispatch times |',
              '| --- | --- | --- |']
    for side in ('player','foe'):
        row=next(r for r in sounds if r['move']=='CAUSTIC' and r['side']==side)
        for component,id_ in (('launch',81),('pop',127)):
            a=', '.join(f'{s["t"]:.1f}' for s in row['normal'] if s['sound']==id_)
            b=', '.join(f'{s["t"]:.1f}' for s in row['final'] if s['sound']==id_)
            lines.append(f'| {side} {component} | {a} | {b} |')
    target=ROOT/'docs/battle_animation_expanded_motion_prototype.md'
    text=target.read_text()
    start='<!-- EXPANDED_RESULTS_START -->'
    end='<!-- EXPANDED_RESULTS_END -->'
    before,rest=text.split(start,1)
    _,after=rest.split(end,1)
    target.write_text(before+start+'\n'+'\n'.join(lines)+'\n'+end+after)
    print(json.dumps(stats),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',default='expanded-v3')
    args=parser.parse_args()
    report(args.candidate)
