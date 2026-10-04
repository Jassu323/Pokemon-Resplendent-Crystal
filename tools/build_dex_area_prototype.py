"""Rebuild the isolated Area prototype from its pinned, unmodified Git baseline.

Never edits the caller's checkout, production ROM, live battery or Git state.
Outputs must use a fresh directory under the ignored root build directory.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '96e5a8c17'
PATCH = ROOT / 'tools/dex_timing/probes/area_integration.patch'
EXPECTED = '43bba18a8541e9d0931dc488ae0561ceb32162da120a9b7f0436bdb820029239'
STATIC_PATCH = ROOT / 'tools/dex_timing/probes/area_static_return.patch'
STATIC_EXPECTED = '7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=12)
    parser.add_argument('--variant', choices=('original', 'static-return'), default='static-return')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build') or output == ROOT / 'build':
        parser.error('Use a fresh subdirectory under the ignored build directory')
    if output.exists():
        parser.error('Output already exists; choose another directory')
    if args.jobs < 1:
        parser.error('Worker count must be positive')
    ref = subprocess.run(['git', 'rev-parse', BASE], cwd=ROOT, check=True,
                         text=True, capture_output=True).stdout.strip()
    archive = subprocess.run(['git', 'archive', ref], cwd=ROOT, check=True,
                             capture_output=True).stdout
    checkout = output / 'candidate'
    checkout.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as data:
        data.extractall(checkout, filter='data')
    with (output / 'patch.log').open('w') as log:
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(PATCH)],
                       cwd=checkout, check=True, stdout=log, stderr=subprocess.STDOUT)
        if args.variant == 'static-return':
            subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(STATIC_PATCH)],
                           cwd=checkout, check=True, stdout=log, stderr=subprocess.STDOUT)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-j' + str(args.jobs), 'pokecrystal.gbc'], cwd=checkout,
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    hashes = {}
    for suffix in ('gbc', 'sym', 'map'):
        source = checkout / ('pokecrystal.' + suffix)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        expected = STATIC_EXPECTED if args.variant == 'static-return' else EXPECTED
        if suffix == 'gbc' and digest != expected:
            raise RuntimeError('Rebuilt cartridge does not match the reviewed prototype')
        target = output / ('pokecrystal-dex-area-prototype.' + suffix)
        shutil.copy2(source, target)
        hashes[target.name] = digest
    report = dict(baseline_commit=ref, hashes=hashes, expected_rom_matches=True,
                  private_only=True, variant=args.variant,
                  patch_sha256=hashlib.sha256(PATCH.read_bytes()).hexdigest())
    if args.variant == 'static-return':
        report['static_patch_sha256'] = hashlib.sha256(STATIC_PATCH.read_bytes()).hexdigest()
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
