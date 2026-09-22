"""Headless regression of the linked New Dex Entry owner and catch return.

Accepts frozen, build-bound pre-catch fixture directories. Original states and
battery saves are read-only; registration checkpoints and reports go to build/.
This is SameBoy execution, not the Selected Description timing model.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from .assets import Repository, sha256
from .cold_listing import expected_picture
from .cpu import CounterCPU

ROOT = Path(__file__).resolve().parents[2]
FRAME = 70224
CORE_FILES = ('apu camera display gb joypad mbc memory printer random rumble '
              'save_state sgb sm83_cpu timing workboy').split()
FIELDS = '''wPokeAnimSceneIndex wPokeAnimIdleFlag wPokeAnimCommand wPokeAnimParameter
    wPokeAnimWaitCounter hSampledCryTimer hSampledCryBlocks hDMATransfer
    wPokeAnimJumptableIndex hVBlank wFrameCounter wPokedexStatus wTilemap wWildMon
    wPokemonIndexTableEntries wCurItem wTempEnemyMonSpecies wEnemyMonSpecies
    wPartyCount wPokedexSeen wPokedexCaught wPartySpecies sBoxCount sBoxSpecies
    hMapAnims hSCX hOAMUpdate wCurSpecies wCurPartySpecies wTempSpecies
    wNamedObjectIndex wEnemyMonDVs wUnownLetter hJoyDown hJoyLast hJoypadDown
    wNewDexEntryAnimMissReason'''.split()


def audio_empty(repo):
    bank, decoded = repo.symbols['SampledCry_AsyncTimerTick.has_decoded_block']
    stop = repo.symbols['StopSampledCryAsync_NoInterruptControl'][1]
    assert bank == 0
    assert repo.rom[decoded - 6:decoded] == bytes((0xf1, 0xe0, 0x70, 0xc3,
                                                stop & 255, stop >> 8))
    return bank, decoded - 6


def compile_core(repo, sameboy, output, kind, start=(3, 0x6a8c)):
    symbols = {**repo.symbols, '@audio_empty': audio_empty(repo)}
    lines = [f'#define S_{name} 0x{symbols[name][1]:04x}' for name in FIELDS]
    lines += [f'#define B_{name} {symbols[name][0]}' for name in FIELDS]
    bank, pc = symbols['NewPokedexEntry']
    lines += [f'#define B_ENTRY {bank}', f'#define P_ENTRY 0x{pc:04x}']
    if kind == 'fixture':
        bank, pc = symbols['GetPokemonIDFromIndex']
        assert bank == 0
        lines += [f'#define P_ALLOCATE 0x{pc:04x}']
    elif kind == 'catch':
        points = {
            'caught': 'PokeBallEffect.caught',
            'experience': 'ApplyExperienceAfterEnemyCaught',
            'level_up': 'LevelUpHappinessMod', 'entry': 'NewPokedexEntry',
            'animation_finished': 'NewDexEntry_AnimationCompleted',
            'animation_miss': 'NewDexEntryAnimationMiss', 'audio_empty': '@audio_empty',
            'registration_return': 'PokeBallEffect.skip_pokedex',
            'send_to_pc': 'PokeBallEffect.SendToPC',
            'catch_return': 'PokeBallEffect.return_from_capture',
        }
        lines += ['#define FOLLOW_THROUGH_AUDIT 1',
                  f'#define B_START {start[0]}', f'#define P_START 0x{start[1]:04x}',
                  f'#define B_sBoxCount {symbols["sBoxCount"][0]}',
                  'static const struct { const char *name; unsigned bank,pc,owner_only; } points[] = {']
        for name, label in points.items():
            bank, pc = symbols[label]
            owner_only = name in ('animation_miss', 'audio_empty')
            lines.append(f'{{"{name}",{bank},0x{pc:04x},{int(owner_only)}}},')
        lines.append('};')
    else:
        bank, at = symbols['NewPokedexEntry.frame_done']
        start = bank * 0x4000 + at - 0x4000
        call = bytes((0xcd, symbols['JoyTextDelay'][1] & 255, symbols['JoyTextDelay'][1] >> 8))
        poll = repo.rom.index(call, start, start + 32) + 3
        symbols['@registration_poll'] = bank, poll - bank * 0x4000 + 0x4000
        events = {
            'entry': ('NewPokedexEntry', 0),
            'wait_entry': ('NewPokedexEntry.WaitPressAorB_AnimateFrontpic', 1),
            'script_frame': ('NewDexEntry_AnimationPrepared', 2),
            'animation_finished': ('NewDexEntry_AnimationCompleted', 4),
            'published': ('NewDexEntry_AnimationPublished', 5),
            'cancel_begin': ('NewDexEntry_CancelAnimation', 6),
            'description': ('DisplayDexEntry', 0),
            'animation_miss': ('NewDexEntryAnimationMiss', 0),
            'audio_start': ('SampledCry_ArmCachedPlayback', 7),
            'audio_stop': ('StopSampledCryAsync_NoInterruptControl', 0),
            'audio_empty': ('@audio_empty', 0),
            'input_poll': ('@registration_poll', 0),
        }
        functions = '''NewDexEntry_InitializeAnimation NewDexEntry_BuildAnimationMap
            NewDexEntry_ServiceAnimation NewDexEntry_PublishAnimation
            NewDexEntry_CopyBackingMap NewDexEntry_CopyVRAMMap
            NewDexEntry_FillBackingAttrs NewDexEntry_FillVRAMAttrs
            NewDexEntry_UploadTiles NewDexEntry_LoadAnimatedFrontpic
            _NewPokedexEntry UpdateBGMap DelayFrame WaitDMATransfer ServiceSampledCryAsync
            SampledCry_FillRollingCache SampledCry_DecodePairBatch
            Decompress Request2bpp Pokedex_LoadGFX StartSampledCryAsync DisplayDexEntry'''.split()
        additional_events = []
        if 'NewDexEntry_DisplayPage2' in symbols:
            additional_events.append(('description', ('NewDexEntry_DisplayPage2', 8)))
            functions.append('NewDexEntry_DisplayPage2')
        if 'NewDexEntry_DescriptionPublished' in symbols:
            additional_events += [
                ('description_ready', ('NewDexEntry_DisplayPage2.description_ready', 9)),
                ('description_published', ('NewDexEntry_DescriptionPublished', 0))]
            functions.append('NewDexEntry_TryPublishDescription')
        elif 'NewDexEntry_DisplayPage2' in symbols:
            # Historical baseline returns immediately after drawing, before
            # WaitBGMap. Observe that boundary without changing its ROM.
            bank, at = symbols['NewPokedexEntry']
            call_bank, call_at = symbols['NewDexEntry_DisplayPage2']
            start = bank * 0x4000 + at - 0x4000
            call = bytes((0x3e, call_bank, 0x21, call_at & 255, call_at >> 8, 0xcf))
            after = repo.rom.index(call, start, start + 128) + len(call)
            symbols['@description_ready'] = bank, after - bank * 0x4000 + 0x4000
            additional_events.append(('description_ready', ('@description_ready', 9)))
        lines += ['enum { E_WAIT=1, E_FRAME=2, E_END=3, E_FINISH=4, E_PUBLISH=5, E_EXIT=6, E_AUDIO=7, E_DESCRIPTION=8, E_DESCRIPTION_READY=9, F_DMA=1 };',
                  'static const struct { const char *name; unsigned bank,pc,kind; } events[] = {']
        for name, (label, kind_id) in list(events.items()) + additional_events:
            bank, pc = symbols[label]
            lines.append(f'{{"{name}",{bank},0x{pc:04x},{kind_id}}},')
        lines += ['};', 'static const struct { const char *name; unsigned bank,pc,log,kind; } functions[] = {']
        for label in functions + ['VBlank', 'LCD', 'SampledCryTimer', 'DMATransfer']:
            bank, pc = symbols[label]
            lines.append(f'{{"{label}",{bank},0x{pc:04x},{int(label in functions)},{int(label == "DMATransfer")}}},')
        lines.append('};')
    header = output / f'{kind}-symbols.h'
    header.write_text('\n'.join(lines) + '\n')
    binary = output / f'new-entry-{kind}'
    subprocess.run(['clang', '-O2', '-std=c11', '-I' + str(sameboy), '-DGB_INTERNAL',
                    '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
                    '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING',
                    '-DGB_VERSION="new-entry-audit"', '-include', str(header),
                    str(ROOT / f'tools/dex_timing/probes/new_entry_{kind}.c'),
                    *(str(sameboy / 'Core' / f'{name}.c') for name in CORE_FILES),
                    '-o', str(binary)], check=True)
    return binary


def validate_fixture(repo, directory, fixture):
    """Reject arbitrary cross-build states, rather than guessing pointer fixes."""
    manifest = json.loads((directory / 'manifest.json').read_text())
    prior = Repository(ROOT, directory / 'fixture.gbc', directory / 'fixture.sym')
    assert sha256(prior.rom) == manifest['rom_sha256']
    state = directory / f'{fixture["species"].lower()}-catch.s{fixture["slot"]}'
    assert sha256(state.read_bytes()) == fixture['state_sha256']
    for name, location in prior.symbols.items():
        if name in repo.symbols and (location[0] == 0 or location[1] >= 0x8000):
            assert repo.symbols[name] == location, ('Fixture address moved', name)
    # Captured catch call chains and sound/animation pointers are still live.
    # Bank $10/$3e registration code is entered afresh, not on the old stack.
    relocations = {(at, repo.symbols[name][1]) for name, (bank, at) in prior.symbols.items()
                   if 0x4000 <= at < 0x8000 and name in repo.symbols
                   and repo.symbols[name][0] == bank and repo.symbols[name][1] != at}
    for bank in (1, 3, 9, 0x0f, 0x11, 0x12, 0x13, 0x25, 0x34):
        begin, end = bank * 0x4000, (bank + 1) * 0x4000
        for name, location in prior.symbols.items():
            if location[0] == bank and name in repo.symbols and not re.search(r'_u\d+$', name):
                assert repo.symbols[name] == location, ('Live catch code moved', name)
        for at in range(begin, end):
            if prior.rom[at] == repo.rom[at]:
                continue
            # Re-linked address operands may target code outside the captured
            # stack (e.g. the new Unown routine position after registration).
            assert any((int.from_bytes(prior.rom[p:p + 2], 'little'),
                        int.from_bytes(repo.rom[p:p + 2], 'little')) in relocations
                       for p in (at - 1, at)), ('Catch fixture code changed', bank, at)
    for name, location in prior.symbols.items():
        if name.startswith(('Music_', 'Cry_', 'Sfx_')) and name in repo.symbols:
            assert repo.symbols[name] == location, ('Sound pointer moved', name)
    asset = repo.load([fixture['species'].lower()])[0]
    old_asset = prior.load([asset.name])[0]
    assert (asset.dictionary, asset.plans, asset.events) == (
        old_asset.dictionary, old_asset.plans, old_asset.events)
    return state, asset


def run(binary, args, prefix, screens=False):
    env = dict(os.environ)
    if screens:
        env['REGISTRATION_FRAMES'] = str(prefix)
    with prefix.with_suffix('.jsonl').open('w') as output, prefix.with_suffix('.stderr').open('w') as errors:
        result = subprocess.run([str(binary), *map(str, args)], stdout=output, stderr=errors, env=env, timeout=180)
    records = [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]
    assert result.returncode == 0, (prefix, result.returncode, records[-3:])
    return records


def audit_description(trace):
    """Input-anchored visibility and atomicity, independent of the wait loop."""
    starts = [e for e in trace if e['event'] == 'description' and e['dex_status'] == 1]
    if not starts:
        return [], None
    frames = [e for e in trace if e['event'] == 'description_display']
    ready = [e for e in trace if e['event'] == 'description_ready']
    errors = []
    if len(ready) != 1 or not frames:
        errors.append(dict(reason='missing description presentation observations'))
    mixed = [e['display'] for e in frames if not ((e['old_map'] and e['old_pixels']) or
                                                 (e['new_map'] and e['new_pixels']))]
    if mixed:
        errors.append(dict(reason='mixed old/new description on display', detail=mixed))
    visible = next((e for e in frames if e['new_map'] and e['new_pixels']), None)
    if not visible:
        errors.append(dict(reason='complete new description never displayed'))
    elif any(not (e['new_map'] and e['new_pixels']) for e in frames if e['display'] >= visible['display']):
        errors.append(dict(reason='description reverted after publication'))
    press = next((e for e in reversed(trace) if e['event'] == 'input' and e['keys'] and e['t'] <= starts[0]['t']), None)
    return errors, dict(checked_displays=len(frames), mixed_displays=mixed,
                        ready_display=ready[0]['display'] if ready else None,
                        visible_display=visible['display'] if visible else None,
                        input_to_visible_intervals=visible['display']-press['display'] if visible and press else None,
                        input_to_visible_t=visible['t']-press['t'] if visible and press else None,
                        ready_to_visible_intervals=visible['display']-ready[0]['display'] if visible and ready else None)


def display_clock_matches(frames):
    """Use exact PPU boundaries; historical traces only sampled the CPU clock."""
    if not frames:
        return False
    precise = all('ppu_t' in e for e in frames)
    clock, tolerance = ('ppu_t', 0) if precise else ('t', 4)
    return all(abs(e[clock] - frames[0][clock] -
                   (e['number'] - frames[0]['number']) * FRAME) <= tolerance for e in frames)


def audit_trace(asset, trace, mode):
    commands = [e for e in trace if e['event'] == 'script_frame']
    publications = [e for e in trace if e['event'] == 'published']
    expected = [(e.frame, e.duration) for e in asset.events] + [(0, 0)]
    observed = [(e['command'], e['duration']) for e in commands]
    assert observed == expected[:len(observed)], (asset.name, observed, expected)
    assert not any(e['event'] in ('animation_miss', 'audio_empty') for e in trace)
    if mode != 2:
        assert observed == expected and len(publications) == len(expected)
    assert publications and all(e['misses'] == 0 for e in publications)
    deadline = publications[0]['display']
    for i, event in enumerate(publications):
        assert event['serial'] == i + 1 and event['display'] == deadline, (asset.name, event, deadline)
        # LY reads zero during the tail of line 153 while mode 1 is still active.
        assert event['mode'] == 1 and (event['ly'] == 0 or 144 <= event['ly'] <= 153), event
        deadline += expected[i][1]
    command_by_serial = {e['serial']: e for e in commands}
    displays = [e for e in trace if e['event'] == 'display' and e['type'] == 0]
    checked = [e for e in displays if e['phase'] == 1 and e['serial']]
    for event in checked:
        frame = command_by_serial[event['serial']]['command']
        assert event['map_mask'] & event['pixel_mask'] & (1 << frame), (asset.name, mode, frame, event)
    assert all(b['number'] == a['number'] + 1 for a, b in zip(checked, checked[1:]))
    assert display_clock_matches(checked)
    finish = [e for e in trace if e['event'] == 'animation_finished']
    returned = [e for e in trace if e['event'] == 'registration_return']
    if mode == 2:
        assert len(returned) == 1 and not finish
        assert returned[0]['hvblank'] != 0x88 and returned[0]['frame_counter'] == 0
    else:
        assert len(finish) == 1 and finish[0]['hvblank'] != 0x88
        assert finish[0]['frame_counter'] == 0
    pages = [e for e in trace if e['event'] == 'description' and e['dex_status'] == 1]
    if mode:
        assert len(pages) == 1
    snapshots = [e for e in trace if e['event'] == 'ui_snapshot' and e['name'] != 'returned']
    assert snapshots and all(e['mismatches'] == 0 for e in snapshots), snapshots
    if mode == 1:
        assert any(e['name'] == 'page2' and e['status'] == 1 for e in snapshots)
    description_errors, description = audit_description(trace)
    assert not description_errors, (asset.name, description_errors)
    starts = [e for e in trace if e['event'] == 'audio_start']
    audio = None
    if starts:
        start = starts[0]
        stop = next(e for e in trace if e['event'] == 'audio_stop' and e['t'] > start['t'])
        assert stop['remaining'] == 0 and start['cache'] == 32
        fills = [e for e in trace if e['event'] == 'span' and e['name'] == 'SampledCry_FillRollingCache'
                 and start['t'] < e['start'] < e['end'] <= stop['t']]
        produced = sum(e['cache_end'] - e['cache_start'] + e['remaining_start'] - e['remaining_end']
                       for e in fills)
        assert produced + 32 == start['remaining']
        audio = dict(total=start['remaining'], startup=32, refilled=produced, remaining=0)
    return dict(species=asset.name, input=('none', 'description', 'exit')[mode],
                authored_intervals=sum(e.duration for e in asset.events),
                observed_intervals=publications[-1]['display'] - publications[0]['display'],
                publications=len(publications), checked_displays=len(checked),
                latest_publication_ly=max(e['ly'] for e in publications), audio=audio,
                description=description)


def audit_publication(repo):
    """Count linked instructions with frozen LY; SameBoy checks live timing.

    Also exercise late/not-ready/window failures and the unpublished-backing
    barrier. These are fault fixtures, never edits to a gameplay save.
    """
    def fixture(flags, ly, deadline=0xfe):
        cpu = CounterCPU(repo.rom, repo.symbols)
        cpu.allowed_io.add(0xff44)
        cpu.ram[0xff44], cpu.ram[0xff70], cpu.ram[0xff4f] = ly, 6, 1
        for name, value in [('wNewDexEntryAnimFlags', flags),
                            ('wNewDexEntryAnimDuration', 5),
                            ('wNewDexEntryAnimDeadline', deadline),
                            ('hVBlankCounter', 0xfe)]:
            cpu.field(name, value)
        bank, at = repo.symbols['wNewDexEntryAnimMap']
        cpu.wram[bank][at & 4095:(at & 4095) + 49] = bytes(range(1, 50))
        cpu.record_writes = True
        cpu.run('NewDexEntry_PublishAnimation')
        assert (cpu.ram[0xff70], cpu.ram[0xff4f]) == (6, 1)
        return cpu

    def state(cpu, name):
        bank, at = repo.symbols[name]
        return cpu.wram[bank][at & 4095]

    costs = {}
    rectangle = [0x9821 + row * 32 + column for row in range(7) for column in range(7)]
    for name, flags, line, cells in [('map', 3, 149, 49), ('first', 11, 149, 98),
                                    ('finish', 7, 149, 98)]:
        cpu = fixture(flags, line)
        sample = [t for t, at, _ in cpu.io_reads if at == 0xff44][-1]
        stores = [(t, at, value) for t, at, value in cpu.writes if 0x8000 <= at < 0xa000]
        assert [(at, value) for _, at, value in stores[:1]] == [(0x9a32, 0)]  # menu arrow
        stores = stores[1:]
        assert [at for _, at, _ in stores] == rectangle * (cells // 49)
        assert [value for _, _, value in stores[:49]] == list(range(1, 50))
        if cells == 98:
            assert [value for _, _, value in stores[49:]] == [9 if name == 'first' else 1] * 49
        writes = [t for t, _, _ in stores]
        assert len(writes) == cells
        assert state(cpu, 'wNewDexEntryAnimMisses') == 0
        assert state(cpu, 'wNewDexEntryAnimDeadline') == 3  # eight-bit wrap
        # Recorder stamps the instruction start; the store finishes 8 T later.
        last_write = writes[-1] + 8 - sample
        available = (153 - line) * 456
        assert last_write < available
        costs[name] = dict(post_sample_t=cpu.cycles - sample,
                           last_write_t=last_write, minimum_available_t=available,
                           write_margin_t=available - last_write)
    for flags, line, deadline, reason in [(1, 145, 0xfe, 1), (1, 145, 0xfd, 2),
                                         (11, 150, 0xfe, 3), (7, 150, 0xfe, 3),
                                         (3, 150, 0xfe, 3),
                                         (3, 143, 0xfe, 3)]:
        cpu = fixture(flags, line, deadline)
        assert state(cpu, 'wNewDexEntryAnimMisses') == 1
        assert state(cpu, 'wNewDexEntryAnimMissReason') == reason
        assert not any(0x9821 <= a < 0x9900 for _, a, _ in cpu.writes)
        cpu.run('NewDexEntry_PublishAnimation')
        assert state(cpu, 'wNewDexEntryAnimMisses') == 1  # latched, not per poll
    for flags, owned in [(17, True), (3, False), (21, True)]:
        cpu = fixture(flags, 145, 0xff)
        assert bool(cpu.r[7]) == owned  # block stale background while ACK is set
        assert state(cpu, 'wNewDexEntryAnimMisses') == 0
    return costs


def audit_description_publication(repo):
    """Bound the disjoint text copy; never count a rejected window as work."""
    cells = [0x9800 + y * 32 + x for y in range(10, 15) for x in range(2, 20)] + [0x9922]
    values = list(range(1, 91)) + [0x58]
    last_write = 0
    for line in range(154):
        cpu = CounterCPU(repo.rom, repo.symbols)
        cpu.allowed_io.add(0xff44)
        cpu.ram[0xff44], cpu.ram[0xff70], cpu.ram[0xff4f] = line, 2, 1
        cpu.field('wNewDexEntryAnimFlags', 0x40)
        base = repo.symbols['wTilemap'][1]
        for y in range(10, 15):
            cpu.ram[base + y * 20 + 2:base + (y + 1) * 20] = bytes(values[(y-10)*18:(y-9)*18])
        cpu.ram[base + 9 * 20 + 2] = 0x58
        cpu.record_writes = True
        cpu.run('NewDexEntry_TryPublishDescription')
        stores = [(t, at, value) for t, at, value in cpu.writes if 0x8000 <= at < 0xa000]
        flag_bank, flag_at = repo.symbols['wNewDexEntryAnimFlags']
        flags = cpu.wram[flag_bank][flag_at & 4095]
        if 144 <= line < 149:
            assert [(at, value) for _, at, value in stores] == list(zip(cells, values))
            assert flags == 0 and cpu.r[7] == 1
            sample = next(t for t, at, _ in cpu.io_reads if at == 0xff44)
            last_write = stores[-1][0] + 16 - sample  # LD [a16], A, instruction-start stamp
            assert last_write < (153 - line) * 456
        else:
            assert not stores and flags == 0x40 and cpu.r[7] == 0
    return dict(cells=len(cells), last_write_t=last_write,
                minimum_available_t=5 * 456, write_margin_t=5 * 456 - last_write)


def audit_resident_layout(repo):
    result = dict(assets=0, pictures=0, max_pairs=0, max_duration=0, max_tile=0)
    for asset in repo.load():
        width, base = asset.width, asset.width ** 2
        resident = {i: bytes(16) for i in range(49)}
        for x in range(width):
            for y in range(width):
                source = x * width + y
                target = (x + int(width != 7)) * 7 + y + 7 - width
                resident[target] = asset.dictionary[source * 16:(source + 1) * 16]
        for source in range(base, asset.total):
            target = source - base + 49
            target += int(target >= 127)
            assert target < 256
            resident[target] = asset.dictionary[source * 16:(source + 1) * 16]
            result['max_tile'] = max(result['max_tile'], target)
        for frame in range(len(asset.plans)):
            tilemap = [x * 7 + y for y in range(7) for x in range(7)]
            if frame:
                plan = asset.plans[frame]
                result['max_pairs'] = max(result['max_pairs'], len(plan.pairs))
                for position, source in plan.pairs:
                    target = source if position & 128 else source - base + 49
                    if not position & 128 and target >= 127:
                        target += 1
                    tilemap[position & 127] = target
            assert b''.join(resident[i] for i in tilemap) == expected_picture(asset, frame), (asset.name, frame)
            result['pictures'] += 1
        assert all(0 < e.duration < 128 for e in asset.events)
        result['max_duration'] = max(result['max_duration'], *(e.duration for e in asset.events))
        result['assets'] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--fixtures', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/new-dex-entry-integration/results')
    parser.add_argument('--species', nargs='+')
    args = parser.parse_args()
    args.output = args.output.resolve()
    for directory in args.fixtures:
        directory = directory.resolve()
        if directory.is_relative_to(args.output) or args.output.is_relative_to(directory):
            parser.error('Keep generated output separate from frozen catch fixtures')
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, args.rom, args.sym)
    report = dict(**repo.hashes, structural=audit_resident_layout(repo),
                  publication=audit_publication(repo), catches=[], runs=[])
    if 'NewDexEntry_TryPublishDescription' in repo.symbols:
        report['description_publication'] = audit_description_publication(repo)
    catch = compile_core(repo, args.sameboy, args.output, 'catch')
    trace = compile_core(repo, args.sameboy, args.output, 'trace')
    source_files = sorted(p for p in (args.sameboy / 'Core').rglob('*')
                          if p.suffix in ('.h', '.c'))
    host_files = [Path(__file__), ROOT / 'tools/dex_timing/cold_listing.py',
                  ROOT / 'tools/dex_timing/probes/new_entry_catch.c',
                  ROOT / 'tools/dex_timing/probes/new_entry_trace.c']
    report['provenance'] = dict(
        sameboy_commit=subprocess.check_output(
            ['git', '-C', str(args.sameboy), 'rev-parse', 'HEAD'], text=True).strip(),
        sameboy_core_sha256=sha256(b''.join(
            str(p.relative_to(args.sameboy)).encode() + b'\0' + p.read_bytes()
            for p in source_files)),
        host_sources={str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in host_files},
        binaries={p.name: sha256(p.read_bytes()) for p in (catch, trace)})
    for directory in args.fixtures:
        manifest = json.loads((directory / 'manifest.json').read_text())
        for fixture in manifest['fixtures']:
            name = fixture['species'].lower()
            if args.species and name not in args.species:
                continue
            state, asset = validate_fixture(repo, directory, fixture)
            prefix = args.output / f'{name}-catch'
            entry = args.output / f'{name}-registration.s0'
            records = run(catch, [args.rom, state, entry, prefix.with_suffix('.ppm'), 'follow-through'], prefix)
            assert not any(e['event'] in ('animation_miss', 'audio_empty') for e in records)
            outcome = next(e for e in records if e['event'] == 'catch_result')
            party = fixture['initial']['party']
            assert outcome['returned'] and outcome['caught']
            assert outcome['party'] == min(party + 1, 6)
            assert outcome['first_box_species' if party == 6 else 'last_party_species'] == fixture['index']
            assert any(e['event'] == 'send_to_pc' for e in records) == (party == 6)
            assert any(e['event'] == 'level_up' for e in records) == any(
                e['event'] == 'level_up' for e in fixture['events'])
            assert outcome['hvblank'] != 0x88 and outcome['frame_counter'] == 0
            report['catches'].append(dict(species=name, state_sha256=fixture['state_sha256'],
                                         registration_sha256=sha256(entry.read_bytes()), result=outcome))
            refs = args.output / f'{name}.references'
            refs.write_bytes(bytes([len(asset.plans)]) + b''.join(
                expected_picture(asset, i) for i in range(len(asset.plans))))
            for mode in range(3):
                prefix = args.output / f'{name}-{mode}'
                events = run(trace, [args.rom, entry, refs, mode], prefix, screens=True)
                result = audit_trace(asset, events, mode)
                report['runs'].append(result)
                print(json.dumps(result), flush=True)
            (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['runs'], 'No cases selected'
    print(json.dumps(dict(catches=len(report['catches']), runs=len(report['runs']),
                         checked_displays=sum(r['checked_displays'] for r in report['runs']),
                         structural=report['structural'])), flush=True)


if __name__ == '__main__':
    main()
