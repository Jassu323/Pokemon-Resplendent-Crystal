"""Private prototype regression pass using existing read-only SameBoy suites."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys

from tools.dex_timing import cold_listing as cold
from tools.dex_timing import cry_ownership as cries
from tools.dex_timing import internal_transitions as transitions
from tools.dex_timing import listing_restoration as listing
from tools.dex_timing.assets import Repository, sha256

ROOT = cold.ROOT
OUT = ROOT / 'build/dex-background-mask-ab'
ORIGINAL = ROOT / 'build/dex-internal-transitions-integrated/cold'
ROM = OUT / 'pokecrystal-dex-background-mask.gbc'
SYM = ROM.with_suffix('.sym')
SOURCE = Path('/Users/jakeadams/Documents/GitHub/SameBoy')


def protected():
    paths = [ROOT / 'pokecrystal.sym', ROOT / 'pokecrystal.map',
             ORIGINAL / 'input-copy.gbc', ORIGINAL / 'input-copy.sav']
    return dict(status=subprocess.check_output(['git', 'status', '--short'], text=True),
                diff_sha256=sha256(subprocess.check_output(['git', 'diff', '--binary'])),
                files={str(p): sha256(p.read_bytes()) for p in paths},
                root_rom_exists=(ROOT / 'pokecrystal.gbc').exists())


def main():
    before = protected()
    repo = Repository(ROOT, ROM, SYM)
    fixtures = OUT / 'compatible-checkpoints'
    fixtures.mkdir(exist_ok=True)
    shutil.copy2(ROM, fixtures / 'input-copy.gbc')
    shutil.copy2(ORIGINAL / 'input-copy.sav', fixtures / 'input-copy.sav')
    provenance = json.loads((ORIGINAL / 'provenance.json').read_text())
    provenance.update(repo.hashes)
    (fixtures / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (fixtures / 'compatibility.json').write_text(json.dumps(dict(
        original_provenance=json.loads((ORIGINAL / 'provenance.json').read_text()),
        reused_states=str(ORIGINAL / 'listing-states'),
        justification='The overlay is reached only when the existing Selected hide helper runs. '
        'Normal boot, Listing navigation, and cold-entry checkpoints precede that code and are compatible. '
        'The state files and original provenance are read-only; this manifest identifies the private ROM.'), indent=2) + '\n')
    states = fixtures / 'listing-states'
    if not states.exists():
        states.symlink_to(ORIGINAL / 'listing-states', target_is_directory=True)
    report = dict(private_only=True)
    observer = OUT / 'observer-control'
    observer.mkdir(exist_ok=True)
    report['observer_controls'] = transitions.verify_observer(repo, SOURCE,
        OUT / 'selective/cold-listing-core', ROM, fixtures, observer)
    cold_out = OUT / 'cold-regression'
    cold_out.mkdir(exist_ok=True)
    if not (cold_out / 'listing-states').exists():
        (cold_out / 'listing-states').symlink_to(states, target_is_directory=True)
    assets = {a.name: a for a in repo.load()}
    names = transitions.names_in_order()
    config = dict(output=str(cold_out), core=str(OUT / 'selective/cold-listing-core'),
                  rom=str(ROM), boot=str(transitions.BOOT), battery=str(fixtures / 'input-copy.sav'))
    with ProcessPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(cold.run_case, [(config, i, assets[name]) for i, name in enumerate(names)]))
    report['cold_listing'] = dict(cases=len(rows), failures=[r for r in rows if
        r['status'] != 'pass' or r.get('return_to_listing') != 'pass'])
    (cold_out / 'report.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(dict(cold_listing=report['cold_listing'])), flush=True)
    sys.argv = ['cry_ownership', '--checkpoints', str(fixtures), '--rom', str(ROM), '--sym', str(SYM),
                '--output', str(OUT / 'cry-regression'), '--jobs', '8',
                '--navigation-controls', '--all-species-handoffs', '--observer-control']
    report['cry_regression_exit'] = cries.main()
    sys.argv = ['listing_restoration', '--checkpoints', str(fixtures), '--sym', str(SYM),
                '--output', str(OUT / 'listing-regression'), '--no-images', '--expect-fixed', '--follow-up']
    report['listing_regression_exit'] = listing.main()
    sys.argv = ['listing_restoration', '--checkpoints', str(fixtures), '--sym', str(SYM),
                '--output', str(OUT / 'listing-admission'), '--no-images', '--expect-fixed', '--admission-sweep']
    report['listing_admission_exit'] = listing.main()
    report['protected_before'], report['protected_after'] = before, protected()
    report['production_unchanged'] = report['protected_before'] == report['protected_after']
    (OUT / 'regression-summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return int(not report['production_unchanged'] or report['cold_listing']['failures'] or
               any(report[k] for k in ('cry_regression_exit', 'listing_regression_exit', 'listing_admission_exit')))


if __name__ == '__main__':
    raise SystemExit(main())
