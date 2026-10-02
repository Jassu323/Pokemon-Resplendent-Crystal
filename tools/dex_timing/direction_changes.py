"""Reproduce Dex axis changes using real keys and a read-only SameBoy observer.

The ROM and source battery stay unchanged. Controls distinguish clean releases,
brief key overlap, repeat-driven input and multiple fresh simultaneous presses.
"""
import argparse
import json
from pathlib import Path
import subprocess

from .assets import Repository, read_symbols, sha256
from .cold_listing import Driver, FRAME, KEY, POINTS, ROOT, build_core
from .costs import machine
from .cry_ownership import state_without_wall_clock, validate_output

BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
FIELDS = '''hJoypadDown hJoypadPressed hJoypadReleased hJoyPressed hJoyReleased
    hJoyLast hInMenu wTextDelayFrames wDexArrowCursorPosIndex
    wDexArrowCursorDelayCounter wPokedexSelectedPendingIndex'''.split()
PHASES = {
    'mirror': 'GetJoypad.quit', 'listing': 'Pokedex_UpdateMainScreen',
    'grid': 'Pokedex_GridHandleDPadInput', 'grid_up': 'Pokedex_GridHandleDPadInput.up',
    'grid_down': 'Pokedex_GridHandleDPadInput.down',
    'grid_left': 'Pokedex_GridHandleDPadInput.left',
    'grid_right': 'Pokedex_GridHandleDPadInput.right',
    'grid_changed': 'Pokedex_UpdateMainScreen.selection_changed',
    'selected': 'PokedexSelectedMon_Update',
    'next_seen': 'PokedexSelectedMon_FindNextSeen',
    'previous': 'PokedexSelectedMon_FindNextSeen.previous',
    'found': 'PokedexSelectedMon_FindNextSeen.found',
    'page': 'PokedexSelectedMon_ChangeSpecies',
    'footer_changed': 'Pokedex_MoveArrowCursor.update_cursor_pos',
    'end_loop': 'Pokedex_EndOwnerLoop',
}
ORDERS = tuple((a, b) for first, second in ((('up', 'down'), ('left', 'right')),
                                           (('left', 'right'), ('up', 'down')))
               for a in first for b in second)


def compile_observer(repo, sameboy, output):
    header = (output / 'direction-symbols.h').resolve()
    lines = [f'#define N_{name} 0x{repo.symbols[name][1]:04x}' for name in FIELDS]
    lines.append('static const struct { unsigned bank, pc; const char *name; } direction_points[] = {')
    for name, label in PHASES.items():
        bank, pc = repo.symbols[label]
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    lines.append('};')
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, sameboy, output, (
        '-DDEX_DIRECTION_CHANGE_TRACE', f'-DDEX_DIRECTION_SYMBOLS="{header}"'))


def run_keys(driver, keys=0, frames=1, points=()):
    mask = sum(1 << list(POINTS).index(point) for point in points)
    state = driver.command(f'run {mask} {int(frames * FRAME)} {keys}')
    state['hit'] = list(POINTS)[state['hit']] if state['hit'] >= 0 else None
    return state


def actions(trace, owner):
    phases = ('grid_up', 'grid_down', 'grid_left', 'grid_right') if owner == 'listing' else ('page', 'footer_changed')
    return [event for event in trace if event['event'] == 'phase' and event['phase'] in phases]


def old_vertical_on_new_horizontal(trace, owner):
    phases = ('grid_up', 'grid_down') if owner == 'listing' else ('page',)
    return [event for event in trace if event['event'] == 'phase'
            and event['phase'] in phases and event['pressed'] & 0x30
            and not event['pressed'] & 0xc0 and event['last'] & 0xc0]


def old_horizontal_on_new_vertical(trace):
    return [event for event in trace if event['event'] == 'phase'
            and event['phase'] == 'footer_changed' and event['pressed'] & 0xc0
            and not event['pressed'] & 0x30 and event['last'] & 0x30]


def summarize(rows):
    result = {}
    for owner in ('listing', 'selected'):
        groups = {}
        for mode in ('released', 'overlap'):
            cases = [row for row in rows if row['owner'] == owner and row['mode'] == mode]
            vertical = [row for row in cases if row['first'] in ('up', 'down')]
            horizontal = [row for row in cases if row['first'] in ('left', 'right')]
            groups[mode] = dict(cases=len(cases), vertical_first_cases=len(vertical),
                wrong_vertical_first_cases=sum(bool(row['wrong_vertical_edges']) for row in vertical),
                horizontal_first_cases=len(horizontal),
                wrong_horizontal_first_cases=sum(bool(row['wrong_horizontal_edges']) for row in horizontal))
        result[owner] = groups
    return result


def load_trace(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def react(driver, keys, owner, limit=60):
    before = driver.command('dir')
    for _ in range(limit):
        state = run_keys(driver, keys, 180, ('end_loop',))
        after = driver.command('dir')
        if state['hit'] != 'end_loop':
            raise RuntimeError('Input owner did not return to its loop')
        if (after['index'] != before['index'] if owner == 'listing' else
                after['selected'] != before['selected'] or after['footer'] != before['footer']):
            return after
    raise RuntimeError('No navigation response')


def consume_press(driver, keys, limit=60):
    # A direction at a grid/footer edge is still a valid consumed input.
    pressed_mask = (keys & 15) << 4
    for _ in range(limit):
        state = run_keys(driver, keys, 180, ('end_loop',))
        after = driver.command('dir')
        if state['hit'] != 'end_loop':
            raise RuntimeError('Input owner did not return to its loop')
        if after['pressed'] & pressed_mask:
            return after
    raise RuntimeError('No new directional press observed')


def case(driver, states, output, owner, first, second, mode, gap=0, hold=0):
    # Grid's first vertical movement ends at the middle-row/middle-column cell.
    index = 7 if first == 'up' else 1 if first == 'down' else 4
    driver.command(f'load {states / f"{owner}-{index:03}.s0"}')
    run_keys(driver, frames=2)
    before = driver.command('dir')
    name = f'{owner}-{first}-{second}-{mode}-{gap}-{hold}'
    trace_path = output / (name + '.jsonl')
    driver.command(f'dirtrace {trace_path}')
    first_state = react(driver, KEY[first], owner)
    if gap:
        run_keys(driver, frames=gap)
    second_start = driver.command('dir')
    if mode == 'overlap':
        run_keys(driver, KEY[first] | KEY[second], hold)
        run_keys(driver, frames=3)
    elif mode == 'released':
        consume_press(driver, KEY[second])
        run_keys(driver, frames=3)
    else:
        raise ValueError(mode)
    final = driver.command('dir')
    driver.command('dirstop')
    trace = load_trace(trace_path)
    row = dict(name=name, owner=owner, first=first, second=second, mode=mode,
               gap=gap, hold=hold, before=before, first_state=first_state,
               second_start=second_start, final=final,
               actions=actions(trace, owner),
               wrong_vertical_edges=old_vertical_on_new_horizontal(trace, owner),
               wrong_horizontal_edges=old_horizontal_on_new_vertical(trace),
               trace=str(trace_path))
    (output / (name + '.json')).write_text(json.dumps(row, indent=2) + '\n')
    return row


def fixed_case(driver, states, output, owner, name, sequence, index=4, offset=0):
    """Change real key pins on a display-time budget, including while UI is busy."""
    driver.command(f'load {states / f"{owner}-{index:03}.s0"}')
    run_keys(driver, frames=2 + offset)
    prefix = output / f'{owner}-{name}'
    driver.command(f'dirtrace {prefix}.jsonl')
    before = driver.command('dir')
    driver.command('audit 1')
    driver.events.clear()
    checkpoints = [run_keys(driver, keys, frames) for keys, frames in sequence]
    run_keys(driver, frames=40)
    final = driver.command('dir')
    driver.command('dirstop')
    driver.command('audit 0')
    trace = load_trace(prefix.with_suffix('.jsonl'))
    row = dict(name=prefix.name, owner=owner, offset=offset, sequence=sequence,
               before=before, checkpoints=checkpoints, final=final,
               actions=actions(trace, owner),
               wrong_vertical_edges=old_vertical_on_new_horizontal(trace, owner),
               wrong_horizontal_edges=old_horizontal_on_new_vertical(trace),
               misses=[event for event in driver.events
                       if event['event'] in ('animation_miss', 'audio_miss')],
               mirrors=[event for event in trace if event['phase'] == 'mirror'],
               trace=str(prefix.with_suffix('.jsonl')))
    prefix.with_suffix('.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def verify_observer(repo, source, core, rom, battery, states, output):
    folder = output / 'observer-control'
    folder.mkdir(exist_ok=True)
    plain = build_core(repo, source, folder)
    results = []
    for owner in ('listing', 'selected'):
        for first, second in (('up', 'right'), ('right', 'down')):
            samples = []
            for traced, executable in ((False, plain), (True, core)):
                prefix = folder / f'{owner}-{first}-{second}-{int(traced)}'
                driver = Driver(executable, rom, BOOT, battery, prefix.with_suffix('.log'))
                try:
                    driver.command(f'load {states / f"{owner}-004.s0"}')
                    if traced:
                        driver.command(f'dirtrace {prefix}.jsonl')
                    driver.command('audit 1')
                    checkpoints = [run_keys(driver, keys, frames) for keys, frames in (
                        (0, 2), (KEY[first], 8), (KEY[first] | KEY[second], 2),
                        (KEY[second], 6), (0, 240))]
                    samples.append(dict(checkpoints=checkpoints, events=list(driver.events),
                        ui=driver.command('ui'), final=driver.evidence(prefix)))
                    samples[-1]['state_hash'] = sha256(state_without_wall_clock(
                        prefix.with_suffix('.s0').read_bytes()))
                    samples[-1]['pixels_hash'] = sha256(prefix.with_suffix('.ppm').read_bytes())
                finally:
                    driver.close()
            equal = samples[0] == samples[1]
            results.append(dict(owner=owner, first=first, second=second, equal=equal))
            if not equal:
                raise RuntimeError('Direction observer changed emulated execution')
    (folder / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def global_input_costs(repo, symbols, image):
    """Pre-flight shared-menu policy; not an integrated game regression test."""
    deltas, count = {}, 0
    image = bytes(image)
    peak_stack_deltas = set()
    start = symbols['DirectionCostGlobalBaseline'][1]
    size = symbols['DirectionCostGlobalBaselineEnd'][1] - start
    original = repo.symbols['JoyTextDelay'][1]
    if image[start:start + size] != repo.rom[original:original + size]:
        raise RuntimeError('Global baseline copy differs from the linked JoyTextDelay routine')
    buttons = ((0, 0), (1, 1), (0, 1), (15, 15),
               (0, 15), (5, 10), (8, 9), (15, 0))
    for in_menu in (0, 1):
        for old_dpad in range(16):
            for new_dpad in range(16):
                for old_buttons, new_buttons in buttons:
                    held = old_dpad << 4 | old_buttons
                    current = new_dpad << 4 | new_buttons
                    for delay in (0, 1, 10):
                        samples = {}
                        for name in ('GlobalBaseline', 'Global'):
                            cpu = machine(repo)
                            cpu.rom = image
                            cpu.symbols = dict(repo.symbols, **symbols)
                            cpu.r = [0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0, 0xde]
                            cpu.f = 0x10
                            for field, value in (('hInMenu', in_menu), ('hJoyDown', held),
                                                 ('hJoypadDown', current),
                                                 ('wTextDelayFrames', delay)):
                                cpu.field(field, value)
                            initial_sp = cpu.sp
                            cpu.record_writes = True
                            cycles = cpu.run('DirectionCost' + name)
                            samples[name] = dict(t=cycles, registers=list(cpu.r), flags=cpu.f,
                                sp=cpu.sp, peak_stack_bytes=initial_sp - min(address
                                    for _, address, _ in cpu.writes if initial_sp - 32 <= address < initial_sp),
                                fields={field: cpu.read(repo.symbols[field][1])
                                    for field in ('hJoyLast', 'hJoyPressed', 'hJoyReleased',
                                                  'hJoyDown', 'hInMenu', 'wTextDelayFrames')})
                        baseline, candidate = samples['GlobalBaseline'], samples['Global']
                        fresh_dpad = baseline['fields']['hJoyPressed'] & 0xf0
                        expected = dict(baseline['fields'])
                        if in_menu and fresh_dpad:
                            expected['hJoyLast'] = baseline['fields']['hJoyLast'] & 15 | fresh_dpad
                        if (candidate['fields'] != expected or
                                any(candidate[field] != baseline[field]
                                    for field in ('registers', 'flags', 'sp'))):
                            raise RuntimeError('Global cost specification changed an unintended contract')
                        key = 'non_menu' if not in_menu else 'new_direction' if fresh_dpad else 'other_menu_input'
                        deltas.setdefault(key, set()).add(candidate['t'] - baseline['t'])
                        peak_stack_deltas.add(candidate['peak_stack_bytes'] - baseline['peak_stack_bytes'])
                        count += 1
    size = lambda name: symbols['DirectionCost' + name + 'End'][1] - symbols['DirectionCost' + name][1]
    return dict(host_only=True, fixtures=count, added_rom0_bytes=size('Global') - size('GlobalBaseline'),
                bytes=dict(baseline=size('GlobalBaseline'), candidate=size('Global')),
                extra_t={key: sorted(values) for key, values in deltas.items()},
                preserves='BC/DE/HL, return A/flags, stack depth, mirror input and repeat timer',
                temporary_register_save_bytes=2,
                added_peak_stack_bytes=sorted(peak_stack_deltas), added_persistent_ram_bytes=0)


def input_costs(repo, output):
    """Count isolated candidate instructions, without making a playable patch."""
    folder = output / 'cost-specification'
    folder.mkdir(exist_ok=True)
    labels = ('JoyTextDelay', 'GetJoypad', 'hJoyPressed', 'hJoyLast', 'hJoyDown',
              'hInMenu', 'wTextDelayFrames', 'wJumptableIndex')
    (folder / 'direction-cost-symbols.asm').write_text('\n'.join(
        f'DEF {label} EQU ${repo.symbols[label][1]:04x}' for label in labels) + '\n')
    subprocess.run(['rgbasm', '-I', str(folder) + '/', '-o', str(folder / 'cost.o'),
                    str(ROOT / 'tools/dex_timing/probes/direction_change_cost.asm')], check=True)
    subprocess.run(['rgblink', '-o', str(folder / 'cost.bin'), '-n', str(folder / 'cost.sym'),
                    str(folder / 'cost.o')], check=True)
    symbols = read_symbols(folder / 'cost.sym')
    image = bytearray(repo.rom)
    image[0x4000:0x8000] = (folder / 'cost.bin').read_bytes()[0x4000:0x8000]
    rows = []
    for state in range(14):
        for held, current, delay in ((0x40, 0x50, 10), (0x80, 0xa0, 10),
                                     (0x40, 0x40, 1), (0x40, 0x40, 0),
                                     (0, 0, 0), (0x41, 0x51, 10)):
            samples = {}
            for name in ('Baseline', 'AllDex', 'Scoped'):
                cpu = machine(repo)
                cpu.rom = bytes(image)
                cpu.symbols = dict(repo.symbols, **symbols)
                for field, value in (('hInMenu', 1), ('hJoyDown', held),
                                     ('hJoypadDown', current), ('wTextDelayFrames', delay),
                                     ('wJumptableIndex', state)):
                    cpu.field(field, value)
                cycles = cpu.run('DirectionCost' + name)
                samples[name] = dict(t=cycles, last=cpu.read(repo.symbols['hJoyLast'][1]),
                    pressed=cpu.read(repo.symbols['hJoyPressed'][1]),
                    delay=cpu.read(repo.symbols['wTextDelayFrames'][1]))
            baseline = samples['Baseline']
            fresh = baseline['pressed'] & 0xf0
            filtered = (baseline['last'] & 15) | fresh if fresh else baseline['last']
            for name, active in (('AllDex', True), ('Scoped', state in (1, 3, 4))):
                expected = filtered if active else baseline['last']
                if (samples[name]['last'] != expected or
                        any(samples[name][field] != baseline[field] for field in ('pressed', 'delay'))):
                    raise RuntimeError('Cost specification changed the input contract')
            rows.append(dict(state=state, held=held, current=current, delay=delay, samples=samples,
                scoped_extra_t=samples['Scoped']['t'] - samples['Baseline']['t'],
                all_dex_extra_t=samples['AllDex']['t'] - samples['Baseline']['t']))
    sizes = {name: symbols['DirectionCost' + name + 'End'][1] -
             symbols['DirectionCost' + name][1] for name in ('Baseline', 'AllDex', 'Scoped')}
    result = dict(host_only=True, bytes=sizes, cases=rows,
                  scoped_added_bytes=sizes['Scoped'] - sizes['Baseline'],
                  all_dex_added_bytes=sizes['AllDex'] - sizes['Baseline'],
                  global_menu=global_input_costs(repo, symbols, image))
    (folder / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def prepare_selected(driver, checkpoints, states):
    for index in (1, 4, 7):
        driver.command(f'load {checkpoints / f"listing-{index:03}.s0"}')
        entered = run_keys(driver, KEY['a'], 180, ('accept',))
        if entered['hit'] != 'accept':
            raise RuntimeError('Selected entry did not accept A')
        run_keys(driver, frames=240)
        # Put the footer in the middle so both horizontal directions can move it.
        react(driver, KEY['right'], 'selected')
        run_keys(driver, frames=20)
        state = driver.command('dir')
        if state['selected'] != index or state['footer'] != 1 or state['down']:
            raise RuntimeError('Selected start has unexpected selection/input')
        driver.command(f'save {states / f"selected-{index:03}.s0"}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--skip-costs', action='store_true',
                        help='Use for a relinked candidate; old isolated baseline costs were measured separately')
    args = parser.parse_args()
    args.checkpoints = args.checkpoints.resolve()
    rom, battery = [args.checkpoints / ('input-copy.' + suffix) for suffix in ('gbc', 'sav')]
    args.output = validate_output(args.output, (rom, battery, args.sym, args.checkpoints))
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, rom, args.sym)
    before_hashes = {str(path): sha256(path.read_bytes()) for path in (rom, battery, args.sym)}
    if json.loads((args.checkpoints / 'provenance.json').read_text())['rom_sha256'] != repo.hashes['rom_sha256']:
        raise ValueError('Checkpoint ROM identity does not match')
    core = compile_observer(repo, args.sameboy, args.output)
    states = args.output / 'starts'
    states.mkdir(exist_ok=True)
    for index in (1, 4, 7):
        (states / f'listing-{index:03}.s0').write_bytes(
            (args.checkpoints / 'listing-states' / f'listing-{index:03}.s0').read_bytes())
    driver = Driver(core, rom, BOOT, battery, args.output / 'core.log')
    rows, timed, repeats, simultaneous, reverse = [], [], [], [], []
    try:
        prepare_selected(driver, args.checkpoints / 'listing-states', states)
        for owner in ('listing', 'selected'):
            for first, second in ORDERS:
                for gap in (0, 1, 2, 4, 8):
                    rows.append(case(driver, states, args.output, owner, first, second, 'released', gap=gap))
                for hold in (1, 2, 4):
                    rows.append(case(driver, states, args.output, owner, first, second, 'overlap', hold=hold))
            print(f'{owner}: {sum(row["owner"] == owner for row in rows)} input cases', flush=True)
            for first, second in ORDERS[:4]:
                index = 7 if first == 'up' else 1
                for offset in (0, .25, .5, .75):
                    for overlap in (False, True):
                        sequence = [(KEY[first], 2)]
                        if overlap:
                            sequence.append((KEY[first] | KEY[second], 1))
                        sequence.append((KEY[second], 8))
                        timed.append(fixed_case(driver, states, args.output, owner,
                            f'timed-{first}-{second}-q{int(offset * 4)}-{int(overlap)}',
                            sequence, index=index, offset=offset))
            for key in ('up', 'down', 'left', 'right'):
                repeats.append(fixed_case(driver, states, args.output, owner,
                    f'repeat-{key}', [(KEY[key], 40)]))
            for first, second in ORDERS[:4]:
                simultaneous.append(fixed_case(driver, states, args.output, owner,
                    f'simultaneous-{first}-{second}', [(KEY[first] | KEY[second], 3)]))
            if owner == 'selected':
                for direction in ('up', 'down'):
                    for hold in (10, 11, 12, 13, 14):
                        reverse.append(fixed_case(driver, states, args.output, owner,
                            f'reverse-{direction}-{hold}', [(KEY['right'], hold),
                            (KEY['right'] | KEY[direction], 1), (KEY[direction], 1)]))
    finally:
        driver.close()
    controls = verify_observer(repo, args.sameboy, core, rom, battery, states, args.output)
    costs = None if args.skip_costs else input_costs(repo, args.output)
    unchanged = all(sha256(Path(path).read_bytes()) == value for path, value in before_hashes.items())
    report = dict(provenance=repo.hashes, unchanged_inputs=unchanged, cases=rows,
                  summary=summarize(rows), timed_cases=timed, repeat_controls=repeats,
                  simultaneous_controls=simultaneous, observer_controls=controls, costs=costs,
                  reverse_timing_controls=reverse,
                  host_only_instrumentation=True)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), timed_cases=len(timed),
                          repeat_controls=len(repeats), simultaneous_controls=len(simultaneous),
                          reverse_timing_controls=len(reverse),
                          observer_controls=controls, summary=report['summary'],
                          unchanged_inputs=unchanged)))
    return int(not unchanged)


if __name__ == '__main__':
    raise SystemExit(main())
