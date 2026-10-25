"""Exhaustive linked JoyTextDelay contract comparisons; not a hardware/UI model."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

from .assets import Repository, sha256
from .cpu import CounterCPU
from .cry_ownership import validate_output

FIELDS = '''hJoyLast hJoyPressed hJoyReleased hJoyDown hJoypadDown hInMenu
    wTextDelayFrames wInputType wAutoInputBank wAutoInputAddress wAutoInputLength'''.split()
_repos = None


def initialize(baseline, candidate):
    global _repos
    _repos = [Repository(Path(root), Path(root) / 'pokecrystal.gbc', Path(root) / 'pokecrystal.sym')
              for root in (baseline, candidate)]


def value(cpu, name):
    address = cpu.symbols[name][1]
    size = 2 if name == 'wAutoInputAddress' else 1
    return sum(cpu.read(address + n) << (8 * n) for n in range(size))


def execute(cpu, old, new, menu, delay, auto=None):
    cpu.r = [0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0, 0xde]
    cpu.f, cpu.sp, cpu.bank = 0x10, 0xc0f0, 1
    for name, number in (('hInMenu', menu), ('hJoyDown', old), ('hJoypadDown', new),
                         ('hJoyPressed', 0), ('hJoyReleased', 0), ('wInputType', 0),
                         ('wTextDelayFrames', delay), ('wAutoInputBank', 0),
                         ('wAutoInputAddress', 0), ('wAutoInputLength', 0)):
        cpu.field(name, number)
    if auto is not None:
        cpu.field('wInputType', 255)
        cpu.field('wAutoInputBank', 250)
        cpu.field('wAutoInputAddress', 0x4000, 2)
        cpu.field('wAutoInputLength', auto)
        cpu.field('hJoyPressed', old)
    cycles = cpu.run('JoyTextDelay', max_steps=1000)
    return dict(t=cycles, registers=list(cpu.r), flags=cpu.f, sp=cpu.sp, bank=cpu.bank,
                fields={name: value(cpu, name) for name in FIELDS})


def compare(samples, menu, context):
    baseline, candidate = samples
    expected = dict(baseline['fields'])
    fresh = expected['hJoyPressed'] & 0xf0
    if menu and fresh:
        expected['hJoyLast'] = (expected['hJoyDown'] & 15) | fresh
    if candidate['fields'] != expected or any(candidate[key] != baseline[key]
            for key in ('registers', 'flags', 'sp', 'bank')):
        raise RuntimeError(f'Linked input contract changed unexpectedly: {context}: {samples}')
    return ('non_menu' if not menu else 'fresh_direction' if fresh else 'other_menu_input',
            candidate['t'] - baseline['t'])


def group(index):
    cpus = [CounterCPU(repo.rom, repo.symbols) for repo in _repos]
    count, deltas = 0, {}
    for old in range(index * 32, (index + 1) * 32):
        for new in range(256):
            for menu in (0, 1):
                for delay in (0, 1, 10):
                    samples = [execute(cpu, old, new, menu, delay) for cpu in cpus]
                    key, delta = compare(samples, menu, (old, new, menu, delay))
                    deltas.setdefault(key, set()).add(delta)
                    count += 1
    return dict(cases=count, extra_t={key: sorted(values) for key, values in deltas.items()})


def auto_contracts():
    rows = []
    for current in range(256):
        for duration in (0, 1, 255):
            for menu in (0, 1):
                cpus = []
                for repo in _repos:
                    image = bytearray(repo.rom)
                    at = 250 * 16384
                    image[at:at + 3] = bytes((current, 4, 255))
                    cpus.append(CounterCPU(bytes(image), repo.symbols))
                samples = [execute(cpu, 0x40, 0xa5, menu, 0, auto=duration) for cpu in cpus]
                key, delta = compare(samples, menu, ('auto', current, duration, menu))
                rows.append(dict(input=current, duration=duration, menu=menu, path=key, extra_t=delta))
    return rows


def callers(root):
    result = []
    for directory in ('home', 'engine', 'mobile'):
        for path in sorted((root / directory).rglob('*.asm')):
            global_label, local = None, None
            for number, line in enumerate(path.read_text().splitlines(), 1):
                label = re.match(r'^([A-Za-z_][\w]*|\.[\w]+)(?:::|:|$)', line)
                if label:
                    name = label[1]
                    if name.startswith('.'):
                        local = name
                    else:
                        global_label, local = name, None
                if re.search(r'\b(?:call|jp)\s+JoyTextDelay\b', line.split(';')[0]):
                    result.append(dict(path=str(path.relative_to(root)), line=number,
                                       owner=(global_label or '?') + (local or '')))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
    output = validate_output(args.output, (baseline / 'pokecrystal.gbc', candidate / 'pokecrystal.gbc'))
    with ProcessPoolExecutor(max_workers=args.jobs, initializer=initialize,
                             initargs=(str(baseline), str(candidate))) as pool:
        groups = list(pool.map(group, range(8)))
    initialize(str(baseline), str(candidate))
    auto = auto_contracts()
    deltas = {}
    for row in groups:
        for key, values in row['extra_t'].items():
            deltas.setdefault(key, set()).update(values)
    result = dict(normal_cases=sum(row['cases'] for row in groups), auto_cases=len(auto),
                  extra_t={key: sorted(values) for key, values in deltas.items()},
                  callers=callers(candidate), auto_controls=auto, groups=groups,
                  rom_hashes=[sha256(repo.rom) for repo in _repos], all_passed=True,
                  note='Instruction-only fixtures preserve input mirrors, repeat timers, registers, flags, bank and stack. Menu-level hardware coverage is separate.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('normal_cases', 'auto_cases', 'extra_t', 'all_passed')}))


if __name__ == '__main__':
    main()
