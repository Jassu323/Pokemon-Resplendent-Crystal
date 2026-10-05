"""New Entry regressions following native Dex speed roundtrips.

Registration donors come from performance_audio's controller-driven catches.
Only Unown's letter is normalized in an explicitly generated form-A context.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from .assets import Repository
from .cold_listing import ROOT, expected_picture
from .new_entry import compile_core, audit_resident_layout, audit_publication
from .new_entry_sweep import cases, run_case
from .performance_audio import SPECIES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--audio-report', default='report.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=24)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--input-variant', default='candidate-post-dex')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    source = json.loads((args.audio / args.audio_report).read_text())
    binaries, factories, assets, references, configurations = {}, {}, {}, {}, {}
    structural = {}
    for old in source['configurations']:
        rom = old['rom']
        repo = Repository(ROOT, Path(rom), Path(old['sym']))
        if rom not in binaries:
            folder = args.output / (old['variant'] + '-core')
            folder.mkdir(exist_ok=True)
            sameboy = Path.home() / 'Documents/GitHub/SameBoy'
            binaries[rom] = str(compile_core(repo, sameboy, folder, 'trace', expected_speed=old.get('expected_double_speed', 0)))
            factories[rom] = str(compile_core(repo, sameboy, folder, 'fixture', expected_speed=old.get('expected_double_speed', 0)))
            assets[rom] = {a.name: a for a in repo.load(SPECIES)}
            references[rom] = {}
            for name, asset in assets[rom].items():
                target = folder / (name + '.references')
                target.write_bytes(bytes([len(asset.plans)]) + b''.join(
                    expected_picture(asset, i) for i in range(len(asset.plans))))
                references[rom][name] = str(target)
            structural[rom] = dict(layout=audit_resident_layout(repo), publication=audit_publication(repo))
        folder = args.output / (old['variant'] + '-q' + str(old['quarter']))
        folder.mkdir(exist_ok=True)
        states = {}
        for name in SPECIES:
            donor_folder = Path(old['output']) / (name + '-catch')
            if not (donor_folder / 'registration.s0').exists():
                donor_folder = Path(old['output']) / 'retested' / (name + '-catch')
            donor = donor_folder / 'registration.s0'
            if name == 'unown_a':
                target = folder / 'unown-a-generated.s0'
                subprocess.run([factories[rom], rom, str(donor), '201', str(target)],
                               check=True, capture_output=True, text=True)
                states[name] = str(target)
            else:
                states[name] = str(donor)
        configurations[old['variant'], old['quarter']] = dict(
            rom=rom, binary=binaries[rom], output=str(folder), states=states,
            references=references[rom], variant=old['variant'], quarter=old['quarter'])
    work = [(config, assets[config['rom']][name], cases(0, 0)[0])
            for config in configurations.values() for name in SPECIES]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for i, result in enumerate(pool.map(run_case, work), 1):
            config = work[i-1][0]
            result.update(variant=config['variant'], quarter=config['quarter'])
            results.append(result)
            if i % 40 == 0 or result['status'] != 'pass':
                print(json.dumps(dict(done=i, total=len(work), errors=result['errors'][:1])), flush=True)
        if not args.smoke and all(r['status'] == 'pass' for r in results):
            config = configurations[args.input_variant, 0]
            inputs = [(config, assets[config['rom']][r['species']], case)
                      for r in results if r['variant'] == config['variant'] and r['quarter'] == 0
                      for case in cases(r['authored_intervals'], r['first_publication'])
                      if case['family'] != 'baseline']
            for i, result in enumerate(pool.map(run_case, inputs), 1):
                result.update(variant=config['variant'], quarter=0)
                results.append(result)
                if i % 100 == 0 or result['status'] != 'pass':
                    print(json.dumps(dict(input_done=i, total=len(inputs), errors=[e['reason'] for e in result['errors'][:1]])), flush=True)
    report = dict(structural=structural, results=results, cases=len(results),
                  failures=sum(r['status'] != 'pass' for r in results))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(results), failures=report['failures'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
