"""Build an isolated, faded successful-capture clock handoff."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess

from dex_timing.assets import read_symbols, sha256
from build_dex_unown_prototype import resources

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'build/gotcha-boundary-final-20261015'
TEMPLATE = ROOT / 'build/dex-position-memory-20261014/candidate'


def build(output, jobs):
    if not output.is_relative_to(ROOT / 'build') or output.exists():
        raise ValueError('Use a fresh prototype directory under build/')
    protected = {str(p): sha256(p.read_bytes()) for p in
        (*(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')),
         *ROOT.glob('*.sav'))}
    assert protected[str(ROOT / 'pokecrystal.gbc')] == sha256((TEMPLATE / 'pokecrystal.gbc').read_bytes())
    output.mkdir(parents=True)
    candidate = output / 'candidate'
    shutil.copytree(TEMPLATE, candidate)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, tracked):
        source, target = ROOT / name, candidate / name
        if source.is_file() and (not target.exists() or source.read_bytes() != target.read_bytes()):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    changes = {}
    item = candidate / 'engine/items/item_effects.asm'
    old = item.read_text()
    anchor = '\tld de, MUSIC_NONE\n\tcall PlayMusic\n\tcall DelayFrame\n\tld de, MUSIC_CAPTURE\n'
    assert old.count(anchor) == 1
    new = old.replace(anchor, '\tld de, MUSIC_NONE\n\tcall PlayMusic\n'
        '\tfarcall BattleSpeed_CaptureHandoff\n\tcall DelayFrame\n\tld de, MUSIC_CAPTURE\n')
    item.write_text(new)
    changes['engine/items/item_effects.asm'] = (old, new)
    start = candidate / 'engine/battle/start_battle.asm'
    old = start.read_text()
    new = old + '\nINCLUDE "engine/battle/capture_speed.asm"\n'
    start.write_text(new)
    changes['engine/battle/start_battle.asm'] = (old, new)
    helper = (ROOT / 'tools/dex_timing/probes/gotcha_boundary.asm').read_text()
    (candidate / 'engine/battle/capture_speed.asm').write_text(helper)
    changes['engine/battle/capture_speed.asm'] = ('', helper)
    (output / 'candidate.diff').write_text(''.join(''.join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), fromfile='a/'+name if old else '/dev/null',
        tofile='b/'+name)) for name, (old, new) in changes.items()))
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    before, after = resources(ROOT / 'pokecrystal.map'), resources(candidate / 'pokecrystal.map')
    delta = {name: after[name] - before[name] for name in before}
    assert not any(value for key, value in delta.items() if key != 'ROMX'), delta
    old_symbols = read_symbols(ROOT / 'pokecrystal.sym')
    new_symbols = read_symbols(candidate / 'pokecrystal.sym')
    assert not [(n, v, new_symbols.get(n)) for n, v in old_symbols.items()
                if v[1] >= 0xa000 and n in new_symbols and new_symbols[n] != v]
    for path, expected in protected.items():
        assert sha256(Path(path).read_bytes()) == expected, path
    record = dict(protected=protected, delta=delta, changed_owners=list(changes),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        rom_sha256=sha256((candidate / 'pokecrystal.gbc').read_bytes()),
        production_unchanged=True, interactive_registration=False,
        policy='normal battle; double after successful-capture sound reset; tutorial unchanged')
    (output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs)
