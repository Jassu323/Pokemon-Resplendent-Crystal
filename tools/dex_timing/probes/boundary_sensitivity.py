"""Replay partial captures with the consolidated CGB-E timing model.

The earlier experimental class ladder has been retired. Historical report
files preserve those experiments; new runs use only the validated behavior.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from dex_timing.assets import Repository, sha256
from dex_timing.followup import read_stops, observed_legs, compare_linked_replay
from dex_timing.model import Profile
from dex_timing.replay import OwnerReplay, ReplayClock, matching_div_phases

# Compatibility names for old diagnostic commands. No alternate implementation.
DeferredClock = ReplayClock
DeferredReplay = PendingHaltReplay = OwnerReplay


def work(args):
    name, origin, capture = args
    repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    asset = repo.load([name])[0]
    path = Path(capture) if capture else ROOT/f'tools/dex_timing/fixtures/{name}_owner_followup.txt'
    stops = read_stops(path.read_text(), repo.symbols)
    phases = [p for p in range(origin % 4 or 4, 12801, 4)
              if matching_div_phases([{'t':origin}], stops[:1], p)]
    legs = observed_legs(stops)
    result = compare_linked_replay(repo, asset, stops,
        Profile(hblank_dot=257, audio_played_at_publication=4), origin, phases, legs)
    selected = result['example'] or result['closest'] or result['diagnostic']
    return {'species':name, 'origin':origin, 'status':result['status'],
            'matches':sum(t['joint_match'] for t in result['trials']),
            'trace_matches':sum(t['joint_trace_match'] for t in result['trials']),
            'trials':len(result['trials']), **repo.hashes,
            'capture_sha256':sha256(path.read_bytes()), 'observed_legs':legs,
            'scope':'CONSOLIDATED_MODEL_PARTIAL_CAPTURE',
            'best':{k:selected[k] for k in ('phase_t','owner_variant','initial_div_low','elapsed_t',
                                          'timer_match','intervals_match')},
            'state_diffs':result['state_differences'],
            'trace_diffs':sum(len(d['bytes']) for d in result['trace_differences'])}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--species', nargs='+', default=['weavile','luxray'])
    p.add_argument('--origins', type=int, nargs='+', default=[606])
    p.add_argument('--jobs', type=int, default=8)
    p.add_argument('--capture', help='Alternate five-stop capture; requires one species')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.capture and len(a.species) != 1:
        p.error('--capture requires exactly one species')
    with ProcessPoolExecutor(a.jobs) as pool:
        results = list(pool.map(work, [(n,o,a.capture) for n in a.species for o in a.origins]))
    if a.output:
        a.output.write_text(json.dumps(results, indent=2)+'\n')
    for result in results:
        print(json.dumps(result), flush=True)
