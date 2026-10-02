"""Build an isolated, fully relinked shared-menu input diagnostic cartridge."""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from .assets import sha256
from .cold_listing import ROOT
from .cry_ownership import validate_output


def build(output, accepted_rom, battery, jobs=8):
    output = validate_output(output, (accepted_rom, battery, ROOT / 'pokecrystal.sym'))
    output.mkdir(parents=True, exist_ok=True)
    baseline, candidate = (output / name for name in ('baseline', 'candidate'))
    if baseline.exists() or candidate.exists():
        raise ValueError('Build output already contains a checkout; use a fresh output')
    inputs = {str(path): sha256(path.read_bytes()) for path in (accepted_rom, battery, ROOT / 'pokecrystal.sym')}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    baseline.mkdir()
    archive = subprocess.check_output(['git', 'archive', commit], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(baseline, filter='data')
    # Reuse local generated assets, then verify the complete baseline ROM hash.
    shutil.copytree(ROOT / 'gfx', baseline / 'gfx', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'tools', baseline / 'tools', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    with (output / 'baseline-build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=baseline,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    if sha256((baseline / 'pokecrystal.gbc').read_bytes()) != inputs[str(accepted_rom)]:
        raise ValueError('Rebuilt baseline does not match the accepted cartridge')
    shutil.copytree(baseline, candidate)
    joypad = candidate / 'home/joypad.asm'
    original = joypad.read_text()
    start, end = (original.index(label) for label in ('JoyTextDelay::', 'WaitPressAorB_BlinkCursor::'))
    replacement = (ROOT / 'tools/dex_timing/probes/shared_menu_joypad.asm').read_text()
    replacement = replacement[replacement.index('JoyTextDelay::'):]
    joypad.write_text(original[:start] + replacement + '\n' + original[end:])
    with (output / 'candidate-build.log').open('w') as log:
        subprocess.run(['make', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    diagnostic = output / 'pokecrystal-shared-input-diagnostic.gbc'
    for suffix in ('.gbc', '.sym', '.map'):
        shutil.copyfile(candidate / ('pokecrystal' + suffix), diagnostic.with_suffix(suffix))
    copied_battery = output / 'input-copy.sav'
    shutil.copyfile(battery, copied_battery)
    diagnostic_battery = diagnostic.with_suffix('.sav')
    shutil.copyfile(copied_battery, diagnostic_battery)
    if any(sha256(Path(path).read_bytes()) != value for path, value in inputs.items()):
        raise RuntimeError('An original input changed during the diagnostic build')
    result = dict(source_commit=commit, original_inputs=inputs, originals_unchanged=True,
                  baseline=str(baseline), candidate=str(candidate), diagnostic=str(diagnostic),
                  diagnostic_sha256=sha256(diagnostic.read_bytes()), battery=str(copied_battery),
                  diagnostic_battery=str(diagnostic_battery),
                  patch_source='tools/dex_timing/probes/shared_menu_joypad.asm',
                  production_source_changed=False)
    (output / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--accepted-rom', type=Path, required=True)
    parser.add_argument('--battery', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('Worker count must be positive')
    build(args.output.resolve(), args.accepted_rom.resolve(), args.battery.resolve(), args.jobs)


if __name__ == '__main__':
    main()
