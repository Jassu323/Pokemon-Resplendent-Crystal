"""Species x display-interval input sweep through the real SameBoy core.

Run new_entry's authentic catch audit first. Its build-bound registration
checkpoints seed this suite. Additional species use explicitly generated entry
fixtures, not fabricated claims of successful catches. All writes stay in build/.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import time

from .assets import Repository, offset, sha256
from .cold_listing import expected_picture
from .new_entry import ROOT, compile_core, audit_description, audit_resident_layout, audit_publication, display_clock_matches

ORIGINAL = ('luxray', 'caterpie', 'metagross', 'dusknoir', 'garchomp',
            'exeggcute', 'vibrava', 'mewtwo')
ADDITIONAL = ('groudon', 'weavile', 'bastiodon', 'unown_a', 'seviper',
              'rampardos', 'kyogre', 'rayquaza', 'spheal', 'milotic', 'yanmega', 'rhyperior')
A, B = 16, 32


def cases(duration, startup):
    """Two-interval taps shifted by ONE display interval, plus sustained input.

    Anchors: 0=registration entry, 1=first publication, 2=page-two wait entry.
    Two-interval taps avoid relying on sub-instruction alignment of input polls.
    This is not an exhaustive Cartesian product of arbitrary button sequences.
    """
    result = [dict(name='baseline', family='baseline', windows=[])]
    for tick in range(duration + 3):
        result.append(dict(name=f'page-{tick:03}', family='page', windows=[(1, tick, 2, A)]))
        result.append(dict(name=f'exit-{tick:03}', family='exit',
                           windows=[(1, 5, 2, A), (2, tick, 2, B)]))
    for tick in range(startup):
        for key, label in ((A, 'a'), (B, 'b')):
            result.append(dict(name=f'startup-{label}-{tick:03}', family='startup',
                               windows=[(0, tick, 2, key)]))
    for anchor in (0, 1):
        for key, label in ((A, 'a'), (B, 'b'), (A | B, 'ab')):
            result.append(dict(name=f'held-{label}-{anchor}', family='stress',
                               windows=[(anchor, 0, startup + duration + 20, key)]))
        for alternating in (False, True):
            windows = [(anchor, tick, 2, B if alternating and tick % 8 else A)
                       for tick in range(0, startup + duration + 20, 4)]
            result.append(dict(name=f'mash-{"ab" if alternating else "a"}-{anchor}',
                               family='stress', windows=windows))
    # Closely spaced cross-button transitions, including a press during redraw.
    for tick in sorted({0, duration // 2, max(0, duration - 1)}):
        for gap in (1, 2, 3, 4):
            result.append(dict(name=f'quick-ab-{tick:03}-{gap}', family='stress',
                               windows=[(1, tick, 2, A), (1, tick + gap, 2, B)]))
    return result


def audit(asset, trace, case):
    errors = []

    def check(condition, reason, detail=None):
        if not condition and len(errors) < 12:
            errors.append(dict(reason=reason, detail=detail))

    expected = [(e.frame, e.duration) for e in asset.events] + [(0, 0)]
    commands = [e for e in trace if e['event'] == 'script_frame']
    publications = [e for e in trace if e['event'] == 'published']
    observed = [(e['command'], e['duration']) for e in commands]
    check(observed == expected[:len(observed)], 'script differs from authored timeline', observed)
    misses = [e for e in trace if e['event'] in ('animation_miss', 'audio_empty')]
    check(not misses, 'animation/audio miss breakpoint', misses)
    check(bool(publications), 'no first publication')
    if publications:
        deadline = publications[0]['display']
        for i, event in enumerate(publications):
            check(i < len(expected) and event['serial'] == i + 1 and event['display'] == deadline,
                  'publication deadline or order', event)
            # LY resets to zero during the final VBlank line, before mode 1
            # ends. Publication bookkeeping can reach that point safely.
            check(event['mode'] == 1 and (event['ly'] == 0 or 144 <= event['ly'] <= 153),
                  'publication outside VBlank', event)
            if i < len(expected):
                deadline += expected[i][1]
        check(not any(e['misses'] for e in publications), 'nonzero animation miss counter',
              max(e['misses'] for e in publications))
    by_serial = {e['serial']: e['command'] for e in commands}
    checked = [e for e in trace if e['event'] == 'display' and e['type'] == 0
               and e['phase'] == 1 and e['serial']]
    for event in checked:
        frame = by_serial.get(event['serial'])
        check(frame is not None and bool(event['map_mask'] & event['pixel_mask'] & (1 << frame)),
              'rendered picture or VRAM mismatch', event)
    check(all(b['number'] == a['number'] + 1 for a, b in zip(checked, checked[1:])),
          'missing display observations')
    check(display_clock_matches(checked), 'display clock drift')
    finish = [e for e in trace if e['event'] == 'animation_finished']
    returned = [e for e in trace if e['event'] == 'registration_return']
    check(bool(finish or returned), 'neither completed nor returned')
    if not returned or finish:
        check(observed == expected and len(publications) == len(expected), 'incomplete natural animation')
    for event in finish + returned:
        check(event['hvblank'] != 0x88 and event['frame_counter'] == 0, 'owner not released', event)
    entry = next((e for e in trace if e['event'] == 'entry'), None)
    if entry:
        for event in returned:
            check(all(event[k] == entry[k] for k in ('hvblank', 'oam_lock', 'map_anims', 'scx', 'dex_status')),
                  'return did not restore caller state', event)
    pages = [e for e in trace if e['event'] == 'description' and e['dex_status'] == 1]
    # The authentic catches enter with hJoyDown=A from the catch prompt. A
    # pressed before the first released poll is not a NEW press. Record it,
    # but do not misclassify that existing edge semantics as a scheduler miss.
    inherited_a = case['name'] == 'page-000' and not pages
    if inherited_a:
        polls = [e for e in trace if e['event'] == 'input_poll']
        check(bool(polls) and polls[0]['joy_down'] == 1 and polls[0]['joy_last'] == 0,
              'unexplained initial A suppression', polls[:1])
    if case['family'] in ('page', 'exit') and not inherited_a:
        check(len(pages) == 1, 'page-advance tap not accepted', len(pages))
    if case['family'] == 'exit':
        check(len(returned) == 1, 'exit tap not accepted', len(returned))
    snapshots = [e for e in trace if e['event'] == 'ui_snapshot' and e['name'] != 'returned']
    check(all(not e['mismatches'] for e in snapshots), 'UI tilemap/backing mismatch', snapshots)
    description_errors, description = audit_description(trace)
    errors.extend(description_errors)
    starts = [e for e in trace if e['event'] == 'audio_start']
    check(len(starts) == int(bool(asset.sample_blocks)), 'wrong cry path', starts)
    audio = None
    if starts:
        start = starts[0]
        stops = [e for e in trace if e['event'] == 'audio_stop' and e['t'] > start['t']]
        check(bool(stops), 'sampled cry never completed')
        if stops:
            stop = stops[0]
            fills = [e for e in trace if e['event'] == 'span' and e['name'] == 'SampledCry_FillRollingCache'
                     and start['t'] < e['start'] < e['end'] <= stop['t']]
            produced = sum(e['cache_end'] - e['cache_start'] + e['remaining_start'] - e['remaining_end']
                           for e in fills)
            check(stop['remaining'] == 0 and start['cache'] == 32 and
                  start['remaining'] == asset.sample_blocks and produced + 32 == asset.sample_blocks,
                  'sampled cry accounting', dict(start=start, stop=stop, produced=produced))
            audio = dict(blocks=start['remaining'], refilled=produced, remaining=stop['remaining'])
    return dict(species=asset.name, case=case['name'], family=case['family'],
                status='fail' if errors else 'pass', errors=errors,
                authored_intervals=sum(e.duration for e in asset.events),
                observed_intervals=(publications[-1]['display'] - publications[0]['display']) if publications else None,
                first_publication=publications[0]['display'] if publications else None,
                publications=len(publications), checked_displays=len(checked),
                completed=bool(finish), returned=bool(returned), page2=bool(pages),
                inherited_a_suppressed=inherited_a,
                snapshots=len(snapshots), audio=audio, description=description,
                latest_publication_ly=max((e['ly'] for e in publications), default=None))


def run_case(job):
    config, asset, case = job
    output = Path(config['output']) / asset.name
    output.mkdir(exist_ok=True)
    prefix = output / case['name']
    plan = prefix.with_suffix('.inputs')
    plan.write_text(''.join(' '.join(map(str, w)) + '\n' for w in case['windows']))
    command = [config['binary'], config['rom'], config['states'][asset.name],
               config['references'][asset.name], 'plan', str(plan)]
    started = time.monotonic()
    process = subprocess.run(command, capture_output=True, text=True, timeout=180,
                             env={**os.environ, 'REGISTRATION_COMPACT': '1'})
    trace = [json.loads(line) for line in process.stdout.splitlines()]
    result = audit(asset, trace, case)
    if process.returncode:
        result['status'] = 'fail'
        result['errors'].append(dict(reason='runner failed or timed out', code=process.returncode,
                                     stderr=process.stderr[-3000:]))
    result['wall_seconds'] = round(time.monotonic() - started, 3)
    if result['status'] == 'fail' or case['name'] in ('baseline', 'page-000', 'exit-000', 'held-a-0'):
        with gzip.open(prefix.with_suffix('.jsonl.gz'), 'wt') as out:
            out.write(process.stdout)
        prefix.with_suffix('.stderr').write_text(process.stderr)
        result['trace'] = str(prefix.with_suffix('.jsonl.gz'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--registration', type=Path, default=ROOT / 'build/new-dex-entry-integration/results')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/new-dex-entry-sweep')
    parser.add_argument('--species', nargs='+')
    parser.add_argument('--smoke', action='store_true', help='Only baseline and representative inputs')
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.rom, args.sym)
    prior = json.loads((args.registration / 'report.json').read_text())
    assert all(prior[k] == v for k, v in repo.hashes.items()), 'Regenerate authentic checkpoints for this link'
    for catch in prior['catches']:
        state = args.registration / f'{catch["species"]}-registration.s0'
        assert sha256(state.read_bytes()) == catch['registration_sha256'], 'Registration checkpoint changed'
    names = args.species or list(ORIGINAL + ADDITIONAL)
    assert len(set(names)) == len(names) and set(names) <= set(ORIGINAL + ADDITIONAL)
    assets = {a.name: a for a in repo.load(names)}
    order_names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    order_at = offset(repo.symbols['NewPokedexOrder'])
    indices = {aliases.get(n, n.lower()): int.from_bytes(repo.rom[order_at + 2*i:order_at + 2*i + 2], 'little')
               for i, n in enumerate(order_names)}
    report = dict(**repo.hashes, structural=audit_resident_layout(repo), publication=audit_publication(repo),
                  authentic_catches=prior['catches'], fixtures={}, runs=[], baseline=[])
    trace = compile_core(repo, args.sameboy, args.output, 'trace')
    factory = compile_core(repo, args.sameboy, args.output, 'fixture')
    config = dict(rom=str(args.rom), binary=str(trace), output=str(args.output), states={}, references={})
    for name in names:
        asset = assets[name]
        if name in ORIGINAL:
            state = args.registration / f'{name}-registration.s0'
            provenance = dict(kind='authentic catch registration checkpoint')
        else:
            donor = args.registration / 'caterpie-registration.s0'
            state = args.output / f'{name}-generated.s0'
            generated = subprocess.run([str(factory), str(args.rom), str(donor), str(indices[name]), str(state)],
                                       capture_output=True, text=True, check=True)
            provenance = dict(kind='generated registration-entry fixture', donor_sha256=sha256(donor.read_bytes()),
                              preparation=json.loads(generated.stdout))
        provenance['state_sha256'] = sha256(state.read_bytes())
        provenance['index'] = indices[name]
        report['fixtures'][name] = provenance
        config['states'][name] = str(state)
        refs = args.output / f'{name}.references'
        refs.write_bytes(bytes([len(asset.plans)]) + b''.join(expected_picture(asset, i) for i in range(len(asset.plans))))
        config['references'][name] = str(refs)
    host_files = [Path(__file__), ROOT / 'tools/dex_timing/new_entry.py', ROOT / 'tools/dex_timing/assets.py',
                  ROOT / 'tools/dex_timing/cold_listing.py', ROOT / 'tools/dex_timing/probes/new_entry_trace.c',
                  ROOT / 'tools/dex_timing/probes/new_entry_fixture.c']
    report['provenance'] = dict(sameboy_commit=subprocess.check_output(
        ['git', '-C', str(args.sameboy), 'rev-parse', 'HEAD'], text=True).strip(),
        sameboy_core_sha256=sha256(b''.join(str(p.relative_to(args.sameboy)).encode() + b'\0' + p.read_bytes()
            for p in sorted((args.sameboy / 'Core').rglob('*')) if p.suffix in ('.h', '.c'))),
        host_sources={str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in host_files},
        binaries={p.name: sha256(p.read_bytes()) for p in (trace, factory)})
    jobs = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case, (config, assets[n], cases(0, 0)[0])): n for n in names}
        for future in as_completed(futures):
            baseline = future.result()
            report['baseline'].append(baseline)
            print(json.dumps(baseline), flush=True)
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        if any(r['status'] != 'pass' for r in report['baseline']):
            raise SystemExit('Baseline failures retained; inspect before sweeping input')
        for row in report['baseline']:
            name = row['species']
            generated_cases = cases(row['authored_intervals'], row['first_publication'])
            if args.smoke:
                selected = {'page-000', 'exit-000', 'held-a-0', 'held-b-0', 'mash-ab-0',
                            'quick-ab-000-1', 'quick-ab-000-2', 'quick-ab-000-3', 'quick-ab-000-4'}
                generated_cases = [c for c in generated_cases if c['name'] in selected]
            jobs.extend((config, assets[name], case) for case in generated_cases if case['family'] != 'baseline')
        print(json.dumps(dict(scheduled=len(jobs), species=len(names), workers=args.jobs)), flush=True)
        futures = [pool.submit(run_case, job) for job in jobs]
        failures = 0
        with (args.output / 'results.jsonl').open('w') as output:
            for i, future in enumerate(as_completed(futures), 1):
                row = future.result()
                report['runs'].append(row)
                output.write(json.dumps(row) + '\n')
                output.flush()
                failures += row['status'] != 'pass'
                if row['status'] != 'pass' or i % 100 == 0 or i == len(jobs):
                    print(json.dumps(dict(done=i, total=len(jobs), failures=failures,
                                          latest=dict(species=row['species'], case=row['case'],
                                                      reasons=[e['reason'] for e in row['errors'][:2]]))), flush=True)
    all_runs = report['baseline'] + report['runs']
    report['summary'] = dict(species=len(names), cases=len(all_runs), failed=sum(r['status'] != 'pass' for r in all_runs),
                             checked_displays=sum(r['checked_displays'] for r in all_runs),
                             completed=sum(r['completed'] for r in all_runs), returned=sum(r['returned'] for r in all_runs))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']), flush=True)
    if report['summary']['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
