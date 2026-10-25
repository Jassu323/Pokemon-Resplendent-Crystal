"""Compare private Info-return prototypes using saved cycle/pixel regressions."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from .assets import read_symbols, sha256
from .cold_listing import ROOT
from .info_return_regression import preservation_audit


def timing(result):
    summary = result['summary']
    cycles = summary['reveal_t'] - result['before']['t']
    return dict(input_to_reveal_cycles=cycles, ms=cycles / 4194.304,
                display_intervals=cycles / 70224,
                observed_display_boundaries=sum(result['before']['t'] < f['t'] <= summary['reveal_t']
                                                for f in summary['frames']),
                leave_to_reveal_ms=summary['return_cycles'] / 4194.304,
                leave_to_reveal_intervals=summary['return_intervals'])


def summarize(build, previous):
    load = lambda p: json.loads(p.read_text())
    metadata = load(build / 'build.json')
    baseline = Path(metadata['baseline'])
    old_metadata = load(previous / 'build.json')
    pairs = load(build / 'paired-full/report.json')
    prior = {r['case']: r for r in load(previous / 'paired-full/report.json')}
    comparisons = []
    for row in pairs:
        if 'repeat' in row['case']:
            continue
        variants = dict(production=timing(row['baseline']),
                        readback=timing(prior[row['case']]['candidate']),
                        records=timing(row['candidate']))
        comparisons.append(dict(case=row['case'], **variants,
            added_ms=variants['records']['ms'] - variants['production']['ms'],
            added_intervals=variants['records']['display_intervals'] - variants['production']['display_intervals']))
    failures = []
    for suite in ('paired-full', 'cancel-sweep', 'cancel-record-phases'):
        for row in load(build / suite / 'report.json'):
            audit = preservation_audit(build / suite / 'candidate' / row['case'])
            if (row['candidate']['restoration_failures'] or row['candidate']['follow_up']['issues']
                    or audit['changed_outgoing_frames'] or audit['exposed_tile_replacements']
                    or audit['translation_issues']):
                failures.append(dict(suite=suite, case=row['case'], audit=audit))
    runtime = load(build / 'runtime/report.json')
    old_runtime = {r['species']: r for r in load(previous / 'runtime-v2/report.json')}
    preparation = [dict(species=r['species'],
        prior_intervals=old_runtime[r['species']]['stats_ready_frames'][0],
        records_intervals=r['stats_ready_frames'][0],
        added_intervals=r['stats_ready_frames'][0] - old_runtime[r['species']]['stats_ready_frames'][0],
        internal_reveal_added_intervals=r['playback'][1]['static_reveal_frames'] -
            old_runtime[r['species']]['playback'][1]['static_reveal_frames']) for r in runtime]
    stress_failures = [r for r in load(build / 'stress-runtime/report.json') if r['issues']]
    prior_failures = [r for r in load(previous / 'stress-runtime/report.json') if r['issues']]
    baseline_symbols = read_symbols(baseline / 'pokecrystal.sym')
    diagnostic = Path(metadata['diagnostic'])
    symbols = read_symbols(diagnostic.with_suffix('.sym'))
    def sections(path):
        return {name: int(size, 16) for size, name in re.findall(
            r'SECTION: \$[0-9a-f]+-\$[0-9a-f]+ \(\$([0-9a-f]+) bytes\) \["([^\"]+)"\]', path.read_text())}
    baseline_sections = sections(baseline / 'pokecrystal.map')
    candidate_sections = sections(diagnostic.with_suffix('.map'))
    deltas = {n: size - baseline_sections.get(n, 0) for n, size in candidate_sections.items()
              if size != baseline_sections.get(n, 0)}
    source_files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                          '--exclude-standard'], cwd=ROOT).decode().split('\0')
    game_sources = [p for p in dict.fromkeys(source_files) if not p.startswith(('tools/', 'docs/'))
                    and (p.endswith('.asm') or p in ('Makefile', 'layout.link'))
                    and (ROOT / p).is_file()]
    changed_sources = [p for p in game_sources if not (baseline / p).exists() or
                       (ROOT / p).read_bytes() != (baseline / p).read_bytes()]
    return dict(prototype_sha256=sha256(diagnostic.read_bytes()),
        previous_sha256=old_metadata['diagnostic_sha256'],
        production_unchanged=all(sha256(Path(p).read_bytes()) == h for p, h in metadata['production_hashes'].items()),
        production_promoted=all(sha256((ROOT / ('pokecrystal' + suffix)).read_bytes()) ==
                                sha256(diagnostic.with_suffix(suffix).read_bytes())
                                for suffix in ('.gbc', '.sym', '.map')),
        game_sources_checked=len(game_sources), changed_game_sources=changed_sources,
        costs=dict(section_deltas=deltas, romx_bytes=sum(deltas.values()),
            reused_overlay_bytes=symbols['wPokedexInfoWorkspaceEnd'][1] - baseline_symbols['wPokedexInfoWorkspaceEnd'][1],
            remaining_before_dc00=0xdc00 - symbols['wPokedexInfoWorkspaceEnd'][1],
            existing_ram_symbols_moved=[n for n in baseline_symbols if n.startswith(('w', 'h'))
                and n != 'wPokedexInfoWorkspaceEnd' and n in symbols and symbols[n] != baseline_symbols[n]]),
        comparisons=comparisons, preparation=preparation,
        preservation_failures=failures,
        baseline_corrupt_returns=sum(bool(r['baseline']['preservation']['changed_outgoing_frames']
            or r['baseline']['preservation']['exposed_tile_replacements']) for r in pairs),
        runtime=load(build / 'runtime/totals.json'), stress=load(build / 'stress-runtime/totals.json'),
        stress_failures=stress_failures, stress_failure_matches_previous=stress_failures == prior_failures,
        uncaught=load(build / 'uncaught-runtime/totals.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.build, args.previous)
    (args.build / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('comparisons', 'preparation')}, indent=2))
    unchanged = result['production_unchanged'] and not result['changed_game_sources']
    raise SystemExit(bool(result['preservation_failures'] or
                          not (unchanged or result['production_promoted']) or
                          not result['stress_failure_matches_previous']))
