"""Paired New Entry input sweeps for the isolated shared-input diagnostic.

Donors must be fresh, matching-link registration checkpoints. All tested species
are explicitly generated contexts, not claims of twenty authentic catches.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import subprocess

from .assets import Repository, offset, sha256
from .cold_listing import expected_picture
from .cry_ownership import validate_output
from .new_entry import (compile_core, audit_publication, audit_resident_layout,
                        audit_description_publication)
from .new_entry_sweep import ORIGINAL, ADDITIONAL, cases, run_case


def prepare(root, donor, output, sameboy):
    output.mkdir(parents=True, exist_ok=True)
    repo = Repository(root, root / 'pokecrystal.gbc', root / 'pokecrystal.sym')
    names = list(ORIGINAL + ADDITIONAL)
    assets = {asset.name: asset for asset in repo.load(names)}
    trace = compile_core(repo, sameboy, output, 'trace')
    factory = compile_core(repo, sameboy, output, 'fixture')
    order = re.findall(r'^\s*dw (\w+)\s*$',
                       (root / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    start = offset(repo.symbols['NewPokedexOrder'])
    indices = {aliases.get(name, name.lower()):
               int.from_bytes(repo.rom[start + 2 * i:start + 2 * i + 2], 'little')
               for i, name in enumerate(order)}
    config = dict(rom=str(root / 'pokecrystal.gbc'), binary=str(trace),
                  output=str(output), states={}, references={})
    report = dict(**repo.hashes, structural=audit_resident_layout(repo),
                  publication=audit_publication(repo),
                  description_publication=audit_description_publication(repo),
                  donor=str(donor), donor_sha256=sha256(donor.read_bytes()),
                  fixture_kind='generated entry contexts from a freshly captured native catch',
                  fixtures={}, baselines=[], runs=[])
    for name, asset in assets.items():
        state = output / (name + '-generated.s0')
        generated = subprocess.run([str(factory), config['rom'], str(donor),
                                    str(indices[name]), str(state)],
                                   check=True, capture_output=True, text=True)
        references = output / (name + '.references')
        references.write_bytes(bytes([len(asset.plans)]) + b''.join(
            expected_picture(asset, i) for i in range(len(asset.plans))))
        config['states'][name], config['references'][name] = str(state), str(references)
        report['fixtures'][name] = dict(preparation=json.loads(generated.stdout),
                                       state_sha256=sha256(state.read_bytes()))
    return config, assets, report


def execute(job):
    variant, config, asset, case = job
    return variant, run_case((config, asset, case))


def sweep(inputs, output, sameboy, jobs):
    configs, assets, reports = {}, {}, {}
    for variant, (root, donor) in inputs.items():
        configs[variant], assets[variant], reports[variant] = prepare(
            root, donor, output / variant, sameboy)

    def save_reports():
        for variant, report in reports.items():
            (output / variant / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        starts = [(v, configs[v], asset, cases(0, 0)[0])
                  for v in configs for asset in assets[v].values()]
        for future in as_completed([pool.submit(execute, job) for job in starts]):
            variant, result = future.result()
            reports[variant]['baselines'].append(result)
            print(json.dumps(dict(variant=variant, species=result['species'],
                                  status=result['status'], errors=result['errors'][:1])), flush=True)
        save_reports()
        if any(row['status'] != 'pass' for r in reports.values() for row in r['baselines']):
            raise RuntimeError('Inspect baseline failures before sweeping input')
        work = [(v, configs[v], assets[v][r['species']], case)
                for v in configs for r in reports[v]['baselines']
                for case in cases(r['authored_intervals'], r['first_publication'])
                if case['family'] != 'baseline']
        print(json.dumps(dict(scheduled=len(work), variants=2, species=len(ORIGINAL + ADDITIONAL))), flush=True)
        failures = 0
        for i, future in enumerate(as_completed([pool.submit(execute, job) for job in work]), 1):
            variant, result = future.result()
            reports[variant]['runs'].append(result)
            failures += result['status'] != 'pass'
            if i % 250 == 0 or result['status'] != 'pass' or i == len(work):
                print(json.dumps(dict(done=i, total=len(work), failures=failures,
                                      latest=dict(variant=variant, species=result['species'],
                                                  case=result['case'], errors=result['errors'][:1]))), flush=True)
    for variant, report in reports.items():
        runs = report['baselines'] + report['runs']
        report['summary'] = dict(species=len(ORIGINAL + ADDITIONAL), cases=len(runs),
                                failures=sum(r['status'] != 'pass' for r in runs),
                                checked_displays=sum(r['checked_displays'] for r in runs))
        print(variant, report['summary'], flush=True)
    save_reports()
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'candidate', 'baseline-donor', 'candidate-donor', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--jobs', type=int, default=12)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('Worker count must be positive')
    inputs = {v: (getattr(args, v).resolve(), getattr(args, v + '_donor').resolve())
              for v in ('baseline', 'candidate')}
    protected = [path for root, donor in inputs.values()
                 for path in (root / 'pokecrystal.gbc', root / 'pokecrystal.sym', donor)]
    output = validate_output(args.output, protected)
    before = {path: sha256(path.read_bytes()) for path in protected}
    reports = sweep(inputs, output, args.sameboy.resolve(), args.jobs)
    if any(sha256(path.read_bytes()) != value for path, value in before.items()):
        raise RuntimeError('A source ROM, symbol file or donor changed')
    if any(r['summary']['failures'] for r in reports.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
