"""Read-only cry handoff investigation and regression tests in isolated SameBoy.

The optional observer runs the unmodified ROM through normal key input. A
checksum-verified local sparse-seen battery reproduces the original paging
neighbors; it never replaces the user's battery or injects in-game memory.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re
import struct
import subprocess

from .assets import Repository, offset, sha256
from .cold_listing import Driver, ROOT, FRAME, audit as audit_animation, bootstrap, build_core, move, predecessor, prepare_states
from .description_ui import audit as audit_ui

FIELDS = '''wPokedexSelectedPendingIndex hSampledCryBank hSampledCryAddress
    wSampledCryCacheCount wSampledCryCompressedBlocks wVolume wLastVolume
    wSFXPriority wMusicPlaying wCurChannel wPitchSweep'''.split()
PHASES = {
    'change': 'PokedexSelectedMon_ChangeSpecies', 'leave': 'PokedexSelectedMon_Leave',
    'area': 'PokedexSelectedMon_Area', 'description_toggle': 'PokedexSelectedMon_ToggleDescriptionPage',
    'hidden': 'PokedexSelectedMon_BeginHiddenTransition', 'stage': 'PokedexSelectedMon_StageDescription',
    'begin': 'Pokedex_BeginDescriptionAnimation', 'play_mon': 'PlayMonCry2',
    'play_cry': 'PlayCry', 'synth_start': '_PlayCry',
    'sample_metadata': 'TryLoadSampledCryBySpeciesIndex.found',
    'loaded_sampled': 'PlayLoadedSampledCryWithPeriod',
    'timer_copy': 'SampledCry_CopyNextCachedBlock',
    'sample_start': 'StartSampledCryAsync', 'sample_arm': 'SampledCry_ArmCachedPlayback',
    'sample_stop': 'StopSampledCryAsync_NoInterruptControl',
    'sample_empty': '@audio_empty', 'sound_update': '_UpdateSound',
    'synth_note': 'ParseSFXOrCry', 'sound_ret': 'ParseMusic.sound_ret',
    'restore_volume': 'RestoreVolume', 'listing': 'Pokedex_UpdateMainScreen',
    'sfx_off': 'SFXChannelsOff',
}
TARGETS = ('chikorita', 'bayleef', 'caterpie', 'exeggcute', 'mewtwo', 'dusknoir',
           'metagross', 'luxray', 'bastiodon', 'garchomp', 'weavile', 'regigigas')


def cancellation_prototype(repo, output):
    """Overlay only a private ROM; no production assembler files are edited."""
    fields = ['wPokedexSelectedState', 'hSampledCryTimer', 'StopSampledCryAsync_NoInterruptControl',
              'wVolume', 'wLastVolume', 'wSFXPriority', 'wPitchSweep',
              'wChannel6PitchOffset', 'wChannel8PitchOffset']
    fields += [f'wChannel{i}Flags1' for i in range(5, 9)]
    source = output / 'cancellation.asm'
    definitions = '\n'.join(f'DEF {name} EQU ${repo.symbols[name][1]:04x}' for name in fields)
    source.write_text(definitions + '\n' +
        (ROOT / 'tools/dex_timing/probes/cry_ownership_cancel.asm').read_text())
    obj, linked, symbols = (output / name for name in ('cancellation.o', 'cancellation.bin', 'cancellation.sym'))
    subprocess.run(['rgbasm', '-o', str(obj), str(source)], check=True)
    subprocess.run(['rgblink', '-o', str(linked), '-n', str(symbols), str(obj)], check=True)
    labels = {name: (int(bank, 16), int(address, 16)) for bank, address, name in re.findall(
        r'^(\w+):(\w+) (\S+)$', symbols.read_text(), re.M)}
    start, end = offset(labels['PrototypeChange']), offset(labels['PrototypeEnd'])
    bank_map = (ROOT / 'pokecrystal.map').read_text().split('ROMX bank #160:')[1].split('ROMX bank #161:')[0]
    if ('EMPTY: $7666-$7fff ($099a bytes)' not in bank_map or end > offset((0xa1, 0x4000))
            or len(set(repo.rom[start:end])) != 1 or repo.rom[start] not in (0, 255)):
        raise ValueError('Prototype is not confined to unused ROMX bytes')
    private = bytearray(repo.rom)
    private[start:end] = linked.read_bytes()[start:end]
    entries = [('ChangeSpecies', 'PrototypeChange', 2), ('Leave', 'PrototypeLeave', 5),
               ('Area', 'PrototypeArea', 3)]
    for routine, stub, state in entries:
        entry = offset(repo.symbols['PokedexSelectedMon_' + routine])
        expected = bytes((0x3e, state, 0xea)) + repo.symbols['wPokedexSelectedState'][1].to_bytes(2, 'little')
        if repo.rom[entry:entry + 5] != expected:
            raise ValueError('Owner boundary prefix changed: ' + routine)
        target = labels[stub][1]
        private[entry:entry + 5] = bytes((0xcd, target & 255, target >> 8, 0, 0))
    (output / 'cancellation-prototype.gbc').write_bytes(private)
    points = dict(cancel_entry=labels['PrototypeCancelCry'],
                  cancel_return=labels['PrototypeCancelCryReturn'])
    return private, points, dict(
        rom_sha256=sha256(private), private_only=True,
        helper_bytes=labels['PrototypeEnd'][1] - labels['PrototypeCancelCry'][1],
        proposed_call_site_bytes=3 * len(entries), overlay_bytes=end - start,
        helper_bank=labels['PrototypeCancelCry'][0], helper_address=labels['PrototypeCancelCry'][1],
        remaining_dex_bank_bytes=0x8000 - labels['PrototypeEnd'][1])


def compile_observer(repo, source, output, extra_points=None):
    header = (output / 'cry-owner-symbols.h').resolve()
    lines = [f'#define C_{name} 0x{repo.symbols[name][1]:04x}' for name in FIELDS]
    for array, stem, channels in (
        ('cry_flags', 'Flags1', range(5, 9)), ('cry_addresses', 'MusicAddress', range(5, 9)),
        ('cry_durations', 'NoteDuration', range(5, 9)), ('cry_banks', 'MusicBank', range(5, 9)),
        ('cry_music_addresses', 'MusicAddress', range(1, 5)),
    ):
        values = ', '.join(f'0x{repo.symbols[f"wChannel{i}{stem}"][1]:04x}' for i in channels)
        lines.append(f'static const unsigned {array}[] = {{{values}}};')
    lines += ['static const struct { unsigned bank, pc; const char *name; } cry_owner_points[] = {']
    for name, label in PHASES.items():
        bank, pc = repo.symbols['SampledCry_AsyncTimerTick.has_decoded_block'] if label == '@audio_empty' else repo.symbols[label]
        if label == '@audio_empty':
            pc -= 6
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    if 'StopSampledCryAsync_FromTimer' in repo.symbols:
        bank, pc = repo.symbols['StopSampledCryAsync_FromTimer']
        lines.append(f'{{{bank}, 0x{pc:04x}, "sample_stop"}},')
    for name, (bank, pc) in (extra_points or {}).items():
        lines.append(f'{{{bank}, 0x{pc:04x}, "{name}"}},')
    lines += ['};']
    header.write_text('\n'.join(lines) + '\n')
    return build_core(repo, source, output, (
        '-DDEX_CRY_OWNER_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE',
        f'-DDEX_CRY_OWNER_SYMBOLS="{header}"'))


def sparse_fixture(repo, source, destination, names=TARGETS):
    if source.resolve() == destination.resolve():
        raise ValueError('A diagnostic fixture must not replace its source battery')
    original = source.read_bytes()
    changed = bytearray(original)
    constants = re.findall(r'^\s*const\s+(\w+)',
        (repo.root / 'constants/pokemon_constants.asm').read_text().split('DEF NUM_POKEMON')[0], re.M)
    flags_size = repo.symbols['wEndPokedexSeen'][1] - repo.symbols['wPokedexSeen'][1]
    seen_flags = bytearray(flags_size)
    for name in names:
        index = constants.index(name.upper())
        seen_flags[index // 8] |= 1 << (index % 8)
    allowed = set()
    def sram(label):
        bank, address = repo.symbols[label]
        return bank * 8192 + address - 0xa000
    for prefix in ('s', 'sBackup'):
        start, end, checksum = (sram(prefix + suffix) for suffix in ('SaveData', 'SaveDataEnd', 'Checksum'))
        if sum(original[start:end]) & 65535 != int.from_bytes(original[checksum:checksum + 2], 'little'):
            raise ValueError('Invalid source battery checksum')
        pokemon = sram(prefix + 'PokemonData')
        for field in ('wPokedexSeen', 'wPokedexCaught'):
            address = pokemon + repo.symbols[field][1] - repo.symbols['wPokemonData'][1]
            changed[address:address + flags_size] = (seen_flags if field == 'wPokedexSeen' else
                bytes(a & b for a, b in zip(original[address:address + flags_size], seen_flags)))
            allowed.update(range(address, address + flags_size))
        changed[checksum:checksum + 2] = (sum(changed[start:end]) & 65535).to_bytes(2, 'little')
        allowed.update((checksum, checksum + 1))
    changes = {i for i, (a, b) in enumerate(zip(original, changed)) if a != b}
    if not changes <= allowed or original[0x8000:] != changed[0x8000:]:
        raise ValueError('Unrelated save bytes changed in local fixture')
    destination.write_bytes(changed)
    return dict(seen_species=list(names), source_sha256=sha256(original), fixture_sha256=sha256(changed),
                changed_offsets=sorted(changes), local_only=True)


def cases(offsets):
    pairs = [('mewtwo', 'dusknoir', 'down'), ('garchomp', 'bastiodon', 'up'),
             ('dusknoir', 'mewtwo', 'up'), ('metagross', 'luxray', 'down'),
             ('chikorita', 'bayleef', 'down')]
    result = [dict(source=a, target=b, key=k, delay=n, action='page')
              for a, b, k in pairs for n in (*offsets, None)]
    result += [dict(source=a, target=None, key='b', delay=n, action='leave')
               for a in ('mewtwo', 'dusknoir', 'weavile') for n in (*offsets, None)]
    return result


def validate_output(output, inputs, root=ROOT):
    output, build = output.resolve(), (root / 'build').resolve()
    if output == build or not output.is_relative_to(build):
        raise ValueError('Diagnostic output must be a subdirectory of the ignored build directory')
    if any(path.resolve().is_relative_to(output) for path in inputs):
        raise ValueError('Diagnostic output must not contain its input ROM, symbols or checkpoints')
    return output


def cancellation_issues(result):
    summary = result.get('summary', {})
    issues = []
    if summary.get('sample_empty_count'):
        issues.append('sample_empty')
    if summary.get('synthesized_notes_after_incoming_sample'):
        issues.append('resumed_synth')
    if result.get('animation_misses'):
        issues.append('animation_miss')
    for before, after in result.get('cancellations', []):
        if after['audio'] or any(flags & 0x21 == 0x21 for flags in after['sfx_flags']):
            issues.append('outgoing_cry_not_canceled')
        if any(before[field] != after[field] for field in ('af', 'bc', 'de', 'hl')):
            issues.append('cancellation_clobbered_registers')
        if before['sp'] != after['sp'] or not after['ime']:
            issues.append('cancellation_broke_call_contract')
    return issues


def cancellation_pairs(trace):
    pairs, pending = [], None
    for event in trace:
        if event['phase'] == 'cancel_entry':
            pending = event
        elif event['phase'] == 'cancel_return':
            if pending is None:
                raise ValueError('Cancellation return has no matching entry')
            pairs.append((pending, event))
            pending = None
    if pending is not None:
        raise ValueError('Cancellation helper did not return')
    return pairs


def settle(driver, listing=False):
    for _ in range(2400):
        state = driver.run(('listing' if listing else 'selected',), frames=600)
        if state['hit'] is None:
            raise RuntimeError('Owner stopped returning to its input loop')
        if not state['audio'] and not state['sfx'] and (listing or state['playback'] == 3):
            return state
    raise RuntimeError('Playback did not finish')


def summarize(trace, handoff_t, incoming_index):
    after = [e for e in trace if e['t'] >= handoff_t]
    empty = [e for e in after if e['phase'] == 'sample_empty' and e['remaining']]
    stops = [e for e in after if e['phase'] == 'sample_stop' and e['audio']]
    arms = [e for e in after if e['phase'] == 'sample_arm']
    incoming_arm = arms[0]['t'] if arms else None
    outgoing_empty = [e for e in empty if incoming_arm is None or e['t'] < incoming_arm]
    resumed = [e for e in after if e['phase'] == 'synth_note' and e['cur_channel'] >= 4
               and e['sfx_flags'][e['cur_channel'] - 4] & 0x20
               and not e['audio'] and (incoming_arm is not None and e['t'] > incoming_arm)]
    return dict(outgoing_cache_empty=outgoing_empty, sampled_stops=stops,
                synthesized_notes_after_incoming_sample=resumed,
                incoming_sample_arm=incoming_arm,
                final_selected=trace[-1]['selected'], incoming_index=incoming_index,
                sample_empty_count=len(empty))


def check_incoming_header(trace, handoff_t, header, blocks):
    starts = [e for e in trace if e['t'] >= handoff_t and e['phase'] == 'sample_start']
    arms = [e for e in trace if e['t'] >= handoff_t and e['phase'] == 'sample_arm']
    if not blocks:
        return dict(issues=['unexpected_sample'] if starts or arms else [])
    issues = []
    if len(starts) != 1 or (starts[0]['sample_bank'], starts[0]['de']) != header:
        issues.append('incoming_header')
    if len(arms) != 1 or arms[0]['remaining'] != blocks:
        issues.append('incoming_block_count')
    return dict(issues=issues, expected_header=header, expected_blocks=blocks,
                actual_header=(starts[0]['sample_bank'], starts[0]['de']) if starts else None,
                actual_blocks=arms[0]['remaining'] if arms else None)


def state_without_wall_clock(payload):
    """Compare every emulated byte except native/BESS host-synchronized RTC.

    RTC cycle accumulation remains part of the comparison. No saved state is
    modified or reloaded; normalization applies only to comparison copies.
    """
    if payload[:4] != b'EMAS' or payload[-4:] != b'BESS':
        raise ValueError('Expected little-endian native SameBoy state with BESS footer')
    normalized = bytearray(payload)
    cursor = 8
    for name in ('core', 'dma', 'mbc', 'hram', 'timing', 'apu', 'rtc', 'video', 'accessory'):
        size = struct.unpack_from('<I', payload, cursor)[0]
        cursor += 4
        if cursor + size > len(payload):
            raise ValueError('Truncated native SameBoy state')
        if name == 'rtc':
            if size != 32:
                raise ValueError('Unexpected native RTC layout')
            normalized[cursor:cursor + 10] = bytes(10)
            normalized[cursor + 16:cursor + 24] = bytes(8)
        cursor += size
    cursor = struct.unpack_from('<I', payload, len(payload) - 8)[0]
    rtc_blocks = 0
    while cursor < len(payload) - 8:
        tag = payload[cursor:cursor + 4]
        size = struct.unpack_from('<I', payload, cursor + 4)[0]
        cursor += 8
        if cursor + size > len(payload) - 8:
            raise ValueError('Truncated BESS block')
        if tag == b'RTC ':
            if size != 48:
                raise ValueError('Unexpected BESS RTC layout')
            normalized[cursor:cursor + size] = bytes(size)
            rtc_blocks += 1
        cursor += size
    if rtc_blocks != 1:
        raise ValueError('Expected exactly one MBC3 BESS RTC block')
    return bytes(normalized)


def observer_control(config, repo, source):
    """Replay identical inputs with the observer compiled out versus enabled."""
    output = Path(config['output']) / 'observer-control'
    output.mkdir(exist_ok=True)
    plain_core = build_core(repo, source, output)
    chosen = [c for c in cases([0, 16]) if (c['source'], c['action'], c['delay']) in {
        ('mewtwo', 'page', 0), ('metagross', 'page', 16),
        ('dusknoir', 'leave', 0), ('chikorita', 'page', None)}]
    results = []
    for case in chosen:
        runs = []
        for observe in (False, True):
            prefix = output / f'{case["source"]}-{case["action"]}-{int(observe)}'
            driver = Driver(config['core'] if observe else plain_core, config['rom'],
                            config['boot'], config['battery'], prefix.with_suffix('.log'))
            checkpoints = []
            try:
                index = config['names'].index(case['source'])
                prior, direction = predecessor(index)
                states = Path(config.get('states', Path(config['output']) / 'listing-states'))
                driver.command(f'load {states / f"listing-{prior:03}.s0"}')
                move(driver, direction, index)
                driver.command('audit 1')
                if observe:
                    driver.command(f'crytrace {prefix}.jsonl')
                checkpoints.append(driver.run(('accept',), key='a'))
                checkpoints.append(driver.run(('selected',), frames=600))
                if case['delay'] is None:
                    settle(driver)
                else:
                    for _ in range(case['delay']):
                        driver.run(('selected',), frames=600)
                checkpoints.append(driver.run(('change_species' if case['action'] == 'page' else 'leave',),
                                               frames=600, key=case['key']))
                checkpoints.append(driver.run(('selected' if case['action'] == 'page' else 'listing',), frames=600))
                checkpoints.append(driver.run(frames=180))
                ui = driver.command('ui')
                driver.command(f'save {prefix}.s0')
                driver.command(f'image {prefix}.ppm')
                runs.append(dict(checkpoints=checkpoints, events=driver.events, ui=ui,
                    state_sha256=sha256(state_without_wall_clock(prefix.with_suffix('.s0').read_bytes())),
                    image_sha256=sha256(prefix.with_suffix('.ppm').read_bytes())))
            finally:
                driver.close()
        results.append(dict(case=case, equal=runs[0] == runs[1],
            equal_checkpoints=runs[0]['checkpoints'] == runs[1]['checkpoints'],
            equal_events=runs[0]['events'] == runs[1]['events'], equal_ui=runs[0]['ui'] == runs[1]['ui'],
            equal_states=runs[0]['state_sha256'] == runs[1]['state_sha256'],
            equal_pixels=runs[0]['image_sha256'] == runs[1]['image_sha256']))
    (output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def view_control(config, species, action):
    """Keep text paging with the same owner; relinquish audio for Area."""
    output = Path(config['output'])
    prefix = output / f'{species}-{action}'
    driver = Driver(config['core'], config['rom'], config['boot'], config['battery'], prefix.with_suffix('.log'))
    result = dict(species=species, action=action)
    try:
        index = config['names'].index(species)
        prior, direction = predecessor(index)
        driver.command(f'load {Path(config["states"]) / f"listing-{prior:03}.s0"}')
        move(driver, direction, index)
        driver.command(f'crytrace {prefix}.jsonl')
        driver.command('audit 1')
        driver.run(('accept',), key='a')
        driver.run(('selected',), frames=600)
        area = action in ('area', 'area-return')
        if area:
            for _ in range(3):
                driver.run(('selected',), key='right')
                driver.run(('selected',))
                driver.run(('selected',))
            entered = driver.run(frames=30, key='a')
            result['area_state'] = entered
            if entered['state'] != 4:
                raise RuntimeError('Area navigation did not reach Area owner')
            result['area_audio'] = driver.command('cry')
            if action == 'area-return':
                # Area setup can exceed 32 intervals. Wait for its real input
                # loop so a short B tap is not lost during map preparation.
                repository = Repository(ROOT, config['rom'], config['sym'])
                bank, pc = repository.symbols['Pokedex_GetArea.loop']
                ready = driver.command(f'restorerun {bank} {pc} {600 * FRAME} 0')
                if ready['hit'] < 0:
                    raise RuntimeError(f'Area setup did not reach its input loop: {ready}')
                driver.run(frames=2)
                # Release B during preparation, not after a held key has
                # already reached the Description page's input poll.
                driver.run(frames=1, key='b')
                restored = driver.run(('selected',), frames=600)
                result['restored'] = restored
                if restored['hit'] != 'selected' or restored['state'] != 1:
                    raise RuntimeError(f'Area return did not restore the Description owner: {restored}')
                result['ui_issues'] = audit_ui(repository, driver.command('ui'))
                static_return = 'PokedexSelectedMon_Area.restored' in repository.symbols
                if static_return:
                    driver.events.clear()
                    final = driver.run(('animation_miss', 'audio_miss'), frames=120)
                    if final['hit'] or final['playback'] or final['animation_flags'] or final['audio'] or final['sfx']:
                        raise RuntimeError(f'Static Area return started playback: {final}')
                else:
                    final = settle(driver)
                result['return_publications'] = [e for e in driver.events if e['event'] == 'publish']
            else:
                final = entered
        else:
            driver.run(('selected',), frames=600, key='a')
            final = settle(driver)
        driver.command('crystop')
        trace = [json.loads(s) for s in prefix.with_suffix('.jsonl').read_text().splitlines()]
        arms = [r for r in trace if r['phase'] == 'sample_arm']
        synths = [r for r in trace if r['phase'] == 'synth_start']
        cancellations = [r for r in trace if r['phase'] == 'cancel_entry']
        natural = [r for r in trace if r['phase'] == 'sample_stop' and r['audio'] and not r['remaining']]
        issues = []
        replay = action == 'area-return' and not static_return
        expected_starts = 2 if replay else 1
        if len(arms if species == 'dusknoir' else synths) != expected_starts:
            issues.append('unexpected_restart_count')
        if len(cancellations) != int(area):
            issues.append('wrong_cancellation_scope')
        if any(r['phase'] == 'sample_empty' for r in trace):
            issues.append('sample_empty')
        if species == 'dusknoir' and len(natural) != int(not area or replay):
            issues.append('missing_natural_completion')
        if area and (result['area_audio']['audio'] or
                any(flags & 0x21 == 0x21 for flags in result['area_audio']['sfx_flags'])):
            issues.append('area_retained_outgoing_cry')
        result.update(final=final, issues=issues, status='complete')
    except (RuntimeError, ValueError) as error:
        result.update(status='error', error=str(error))
        result['failure_state'] = driver.evidence(f'{prefix}-failure')
    finally:
        driver.close()
    prefix.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run_case(job):
    config, case = job
    output, names = Path(config['output']), config['names']
    label = f'{case["source"]}-{case["action"]}-{case["target"] or "listing"}-{case["delay"] if case["delay"] is not None else "settled"}'
    trace_path = output / f'{label}.jsonl'
    driver = Driver(config['core'], config['rom'], config['boot'], config['battery'], output / f'{label}.log')
    result = dict(case=case, label=label)
    try:
        index = names.index(case['source'])
        prior, direction = predecessor(index)
        driver.command(f'load {Path(config.get("states", output / "listing-states")) / f"listing-{prior:03}.s0"}')
        move(driver, direction, index)
        driver.command('audit 1')
        driver.command(f'crytrace {trace_path}')
        accepted = driver.run(('accept',), key='a')
        first = driver.run(('selected',), frames=600)
        if case['delay'] is None:
            settle(driver)
        else:
            for _ in range(case['delay']):
                driver.run(('selected',), frames=600)
        before = driver.command('cry')
        result.update(accepted=accepted, first=first, before=before)
        handoff = driver.run(('change_species' if case['action'] == 'page' else 'leave',),
                             frames=600, key=case['key'])
        if handoff['hit'] != ('change_species' if case['action'] == 'page' else 'leave'):
            raise RuntimeError(f'Handoff was not accepted: {handoff}')
        handoff_audio = driver.command('cry')
        result.update(handoff=handoff, handoff_audio=handoff_audio)
        if case['action'] == 'page':
            incoming = driver.run(('selected',), frames=600)
            if incoming['selected_index'] != names.index(case['target']):
                raise RuntimeError(f'Wrong paging target: {incoming}')
            result['incoming'] = incoming
            repository = Repository(ROOT, config['rom'], config['sym'])
            result['ui_issues'] = audit_ui(repository, driver.command('ui'))
            final = settle(driver)
        else:
            incoming = driver.run(('listing',), frames=600)
            result['incoming'] = incoming
            final = settle(driver, listing=True)
        final_audio = driver.command('cry')
        driver.command('crystop')
        trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
        result['cancellations'] = cancellation_pairs(trace)
        summary = summarize(trace, handoff['t'], names.index(case['target']) if case['target'] else None)
        if case['action'] == 'page':
            asset = repository.load([case['target']])[0]
            sample = repository.symbols[asset.labels['sample']] if asset.sample_blocks else None
            result['header_audit'] = check_incoming_header(trace, handoff['t'], sample, asset.sample_blocks)
            incoming_events = [e for e in driver.events if e['t'] >= handoff['t'] and
                (e['event'] not in ('audio_stop', 'audio_miss') or
                 (summary['incoming_sample_arm'] is not None and e['t'] >= summary['incoming_sample_arm']))]
            result['animation_audit'] = audit_animation(asset, handoff, incoming_events, final, cold=False)
        result.update(status='complete', accepted=accepted, first=first, before=before,
                      handoff=handoff, handoff_audio=handoff_audio, incoming=incoming, final=final,
                      final_audio=final_audio, summary=summary,
                      animation_misses=sum(e['event'] == 'animation_miss' for e in driver.events))
    except Exception as error:
        result.update(status='error', error=str(error))
        try:
            result['failed_audio'] = driver.command('cry')
            driver.command('crystop')
        except (RuntimeError, BrokenPipeError) as capture_error:
            result['capture_error'] = str(capture_error)
        if 'handoff' in result:
            trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
            result['summary'] = summarize(trace, result['handoff']['t'],
                names.index(case['target']) if case['target'] else None)
    finally:
        driver.close()
    (output / f'{label}.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rom', type=Path, help='Matching ROM; defaults to root ROM or checkpoint copy')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--sameboy', type=Path, default=Path.home() / 'Documents/GitHub/SameBoy')
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--offsets', type=int, nargs='+', default=[0, 4, 16, 40])
    parser.add_argument('--reuse-states', action='store_true')
    parser.add_argument('--states-from', type=Path, help='Use matching sparse diagnostic checkpoints')
    parser.add_argument('--prototype', action='store_true', help='Test cancellation in a private ROM overlay only')
    parser.add_argument('--observer-control', action='store_true', help='Check observer-on/off state and pixel equivalence')
    parser.add_argument('--navigation-controls', action='store_true', help='Broaden cancellation tests to all-seen neighbors and footer views')
    parser.add_argument('--all-species-handoffs', action='store_true', help='Page and B-return from every species while playback is active')
    parser.add_argument('--area-roundtrips', action='store_true', help='Also diagnose the deferred Area screen round-trip behavior')
    args = parser.parse_args()
    if args.area_roundtrips and not args.navigation_controls:
        parser.error('Area round trips require navigation controls')
    if args.jobs < 1 or any(n < 0 for n in args.offsets):
        parser.error('Use positive worker counts and nonnegative input offsets')
    production = ROOT / 'pokecrystal.gbc'
    production_before = production.read_bytes() if production.exists() else None
    source_rom = args.rom or (production if production.exists() else args.checkpoints / 'input-copy.gbc')
    args.output = validate_output(args.output,
        [source_rom, args.sym, args.checkpoints])
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, source_rom, args.sym)
    origin = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(origin[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Checkpoints do not match the current ROM and symbols')
    aliases = {'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}
    names = [aliases.get(n, n.lower()) for n in re.findall(r'^\s*dw (\w+)\s*$',
        (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)]
    rom = args.output / 'diagnostic-input.gbc'
    rom.write_bytes(repo.rom)
    symbols = args.output / 'diagnostic-input.sym'
    symbols.write_bytes(args.sym.read_bytes())
    battery = args.output / 'sparse-input.sav'
    fixture = sparse_fixture(repo, args.checkpoints / 'input-copy.sav', battery)
    extra_points, experiment = {}, None
    if args.prototype:
        private, extra_points, experiment = cancellation_prototype(repo, args.output)
        rom = args.output / 'cancellation-prototype.gbc'
    elif 'PokedexSelectedMon_CancelCry' in repo.symbols:
        extra_points = dict(cancel_entry=repo.symbols['PokedexSelectedMon_CancelCry'],
                            cancel_return=repo.symbols['PokedexSelectedMon_CancelCry.return'])
    cancellation_expected = bool(extra_points)
    if (args.navigation_controls or args.all_species_handoffs) and not cancellation_expected:
        parser.error('Cancellation regression controls require the integrated helper or prototype')
    core = compile_observer(repo, args.sameboy, args.output, extra_points)
    boot = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
    config = dict(output=str(args.output), names=names, core=str(core), rom=str(rom),
                  boot=str(boot), battery=str(battery), sym=str(symbols))
    provenance = dict(**repo.hashes, fixture=fixture, sameboy_commit=subprocess.check_output(
        ['git', '-C', str(args.sameboy), 'rev-parse', 'HEAD'], text=True).strip())
    provenance_path = args.output / 'provenance.json'
    if args.reuse_states and json.loads(provenance_path.read_text()) != provenance:
        raise ValueError('Sparse checkpoints do not match the diagnostic inputs')
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
    if args.states_from:
        if json.loads((args.states_from / 'provenance.json').read_text()) != provenance:
            raise ValueError('Reused checkpoint ROM, symbols, battery or SameBoy version differs')
        config['states'] = str((args.states_from / 'listing-states').resolve())
    elif not args.reuse_states:
        (args.output / 'listing-states').mkdir(exist_ok=True)
        driver = Driver(core, rom, boot, battery, args.output / 'bootstrap.log')
        try:
            bootstrap(driver)
            prepare_states(driver, args.output / 'listing-states', len(names))
        finally:
            driver.close()
    results = []
    controls = observer_control(config, repo, args.sameboy) if args.observer_control else []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(run_case, [(config, case) for case in cases(args.offsets)]):
            results.append(result)
            s = result.get('summary', {})
            print(json.dumps(dict(label=result['label'], status=result['status'], error=result.get('error'),
                outgoing_empty=len(s.get('outgoing_cache_empty', [])),
                resumed_notes=len(s.get('synthesized_notes_after_incoming_sample', [])))), flush=True)
    navigation = []
    if args.navigation_controls:
        normal_output = args.output / 'all-seen-controls'
        normal_output.mkdir(exist_ok=True)
        normal = dict(config, output=str(normal_output),
                      states=str((args.checkpoints / 'listing-states').resolve()))
        normal_cases = [dict(source=a, target=b, key='down', delay=n, action='page')
            for a, b, ns in (('celebi', 'treecko', (0, 4, 16, None)),
                             ('garchomp', 'riolu', (0, 16)), ('metagross', 'regirock', (0, 16))) for n in ns]
        normal_cases += [dict(source=a, target=None, key='b', delay=0, action='leave')
                        for a in ('mewtwo', 'dusknoir')]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            navigation = list(pool.map(run_case, [(normal, case) for case in normal_cases]))
        navigation += [view_control(normal, species, action)
                       for species in ('mewtwo', 'dusknoir')
                       for action in ('description', 'area', *(['area-return'] if args.area_roundtrips else []))]
    all_species = []
    if args.all_species_handoffs:
        all_output = args.output / 'all-species-handoffs'
        all_output.mkdir(exist_ok=True)
        normal = dict(config, output=str(all_output),
                      states=str((args.checkpoints / 'listing-states').resolve()))
        broad_cases = [dict(source=name, target=names[(index + 1) % len(names)] if action == 'page' else None,
                            key='down' if action == 'page' else 'b', delay=delay, action=action)
                       for index, name in enumerate(names) for delay in (0, 16) for action in ('page', 'leave')]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for result in pool.map(run_case, [(normal, case) for case in broad_cases]):
                all_species.append(result)
                print(json.dumps(dict(label=result['label'], status=result['status'],
                                      issues=cancellation_issues(result), error=result.get('error'))), flush=True)
    unchanged = production_before == (production.read_bytes() if production.exists() else None)
    report = dict(provenance=provenance, experiment=experiment, observer_controls=controls,
                  navigation_controls=navigation,
                  all_species_handoffs=all_species, cancellation_expected=cancellation_expected,
                  production_rom_unchanged=unchanged, results=results)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return int(not unchanged or any(r['status'] != 'complete' for r in results)
               or any(not c['equal'] for c in controls)
               or any(r.get('ui_issues') or r.get('header_audit', {}).get('issues')
                      or r.get('animation_audit', {}).get('issues') for r in results)
               or (cancellation_expected and any(cancellation_issues(r) for r in results + navigation + all_species))
               or any(r['status'] != 'complete' or r.get('issues') or r.get('ui_issues')
                      or r.get('header_audit', {}).get('issues')
                      or r.get('animation_audit', {}).get('issues') for r in navigation + all_species))


if __name__ == '__main__':
    raise SystemExit(main())
