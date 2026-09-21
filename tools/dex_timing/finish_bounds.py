"""Recompute the shipped finishing gates from linked instruction costs.

This checks conservative inequalities, not complete-sequence feasibility.
Run integrated_replay separately. No cartridge or asset is written here.
"""
import argparse
import json
import math
from pathlib import Path

from .assets import Repository, offset
from .cpu import ModelError
from .finish_experiment import finish_admission, finishing_costs


def finish_tables(costs, reserve=8192):
    """Encode the response-time inequalities as strict, exclusive LY limits."""
    rows = []
    for suffix in ('_no_timer_t', '_inactive_timer_t', '_t'):
        row = []
        for count in range(1, 21):
            c = costs[count]
            bound, launch = c['chain_bound'+suffix], c['launch_bound'+suffix]
            limit = min(144-math.ceil((bound+reserve)/456),
                        127-count-math.ceil(launch/456))
            row.append(max(0, min(144, limit)))
        rows.append(row)
    audio = [1+math.ceil((costs[n]['chain_bound_t']+2*70224)/12800)
             for n in range(1, 21)]
    return rows, audio


def verify_tables(costs, limits, audio):
    cases = 0
    for cls in range(3):
        active, enabled = cls == 2, cls != 0
        for n in range(1, 21):
            for ly in range(144):
                for delta in (0, 1, 127, 128, 255):
                    for remaining, cache in ((557, 0), (557, audio[n-1]-1),
                                             (557, audio[n-1]), (3, 3), (0, 0)):
                        state = dict(deadline=(11+delta)&255, counter=10, ly=ly)
                        expected = finish_admission(state, n, costs[n], active, cache,
                                                    200, remaining, enabled, 8192)['admitted']
                        got = delta < 128 and ly < limits[cls][n-1] and (
                            not active or cache >= min(remaining, audio[n-1]))
                        if got != expected:
                            raise ModelError('Compact thresholds changed the host admission inequality')
                        cases += 1
    return cases


def check(repo):
    costs = finishing_costs(repo)
    limits, audio = finish_tables(costs)
    wanted = bytes(sum(limits, []) + audio)
    at = offset(repo.symbols['Pokedex_AnimationFinishLatestLY'])
    actual = repo.rom[at:at + 80]
    return dict(costs=costs, latest_ly_exclusive=limits, audio_minimum=audio,
                matches=actual == wanted, expected_hex=wanted.hex(),
                inequality_cases=verify_tables(costs, limits, audio), **repo.hashes)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    report = check(Repository(a.root, a.root/'pokecrystal.gbc', a.root/'pokecrystal.sym'))
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'costs'}, indent=2))
    return 0 if report['matches'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
