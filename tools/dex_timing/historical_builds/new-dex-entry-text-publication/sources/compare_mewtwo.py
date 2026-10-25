"""Read-only comparison of the eleven formerly failing Mewtwo input timings."""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from dex_timing.assets import Repository, sha256
from dex_timing.new_entry import compile_core, run
from dex_timing.new_entry_sweep import audit

base = ROOT / 'build/new-dex-entry-text-publication'
out = base / 'mewtwo-comparison'
out.mkdir(exist_ok=True)
report = dict(runs=[], provenance={})
for version, romdir, registration in (
        ('before', base / 'before', ROOT / 'build/new-dex-entry-commit-cleanup/catches'),
        ('after', ROOT, base / 'catches')):
    repo = Repository(ROOT, romdir / 'pokecrystal.gbc', romdir / 'pokecrystal.sym')
    checkpoint_report = json.loads((registration / 'report.json').read_text())
    assert all(checkpoint_report[k] == v for k, v in repo.hashes.items())
    state = registration / 'mewtwo-registration.s0'
    row = next(c for c in checkpoint_report['catches'] if c['species'] == 'mewtwo')
    assert sha256(state.read_bytes()) == row['registration_sha256']
    directory = out / version
    directory.mkdir(exist_ok=True)
    binary = compile_core(repo, Path.home() / 'Documents/GitHub/SameBoy', directory, 'trace')
    report['provenance'][version] = dict(**repo.hashes, state_sha256=sha256(state.read_bytes()),
                                        binary_sha256=sha256(binary.read_bytes()))
    asset = repo.load(['mewtwo'])[0]
    for tick in [*range(32, 42), 43]:
        prefix = directory / f'page-{tick:03}'
        plan = prefix.with_suffix('.inputs')
        plan.write_text(f'1 {tick} 2 16\n')
        trace = run(binary, [romdir / 'pokecrystal.gbc', state,
                             registration / 'mewtwo.references', 'plan', plan], prefix)
        result = audit(asset, trace, dict(name=f'page-{tick:03}', family='page'))
        with gzip.open(prefix.with_suffix('.jsonl.gz'), 'wt') as output:
            output.write(prefix.with_suffix('.jsonl').read_text())
        result.update(version=version, trace=str(prefix.with_suffix('.jsonl.gz')))
        report['runs'].append(result)
        print(json.dumps(dict(version=version, case=result['case'], status=result['status'],
                              description=result['description'])), flush=True)
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
assert all(r['status'] == 'pass' for r in report['runs'] if r['version'] == 'after')
assert all(r['status'] == 'fail' for r in report['runs'] if r['version'] == 'before')
