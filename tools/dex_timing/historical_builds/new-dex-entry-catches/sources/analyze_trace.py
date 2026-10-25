"""Host-only audit of the four frozen registration baseline replays."""

import json
import os
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get('REGISTRATION_OUT', Path(__file__).resolve().parent))
SPECIES = os.environ.get('REGISTRATION_SPECIES', 'caterpie,luxray,metagross,dusknoir').split(',')
sys.path.insert(0, str(ROOT))
from tools.dex_timing.assets import Repository

INTERVAL = 70224
HZ = 4194304


def read(name):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines()]


def coalesce(events):
    result = []
    for frame, duration in events:
        if result and result[-1][0] == frame:
            result[-1][1] += duration
        else:
            result.append([frame, duration])
    return result


def stats(spans):
    values = [s['end'] - s['start'] for s in spans]
    return dict(count=len(values), total_t=sum(values), min_t=min(values),
                median_t=median(values), max_t=max(values)) if values else {}


repo = Repository(ROOT, OUT / 'fixture.gbc', OUT / 'fixture.sym')
report = {}
for asset in repo.load(SPECIES):
    trace = read(f'{asset.name}-trace.jsonl')
    old = read(f'{asset.name}.jsonl')
    origin = next(e['t'] for e in old if e['event'] == 'entry')
    boundaries = ('wait_entry', 'script_frame', 'script_end', 'animation_finished',
                  'audio_empty', 'audio_stop')
    for label in boundaries:
        before = [e['t'] - origin for e in old if e['event'] == label and e['t'] >= origin]
        after = [e['t'] for e in trace if e['event'] == label]
        assert before == after, (asset.name, label, before, after)

    commands = [e for e in trace if e['event'] in ('script_frame', 'script_end')]
    command_by_serial = {e['serial']: e for e in commands}
    displays = [e for e in trace if e['event'] == 'display' and e['phase'] == 1 and e['type'] == 0]
    first_display = {}
    for display in displays:
        assert display['map_mask'] and display['pixel_mask'], (asset.name, display)
        if not display['serial']:
            continue
        command = command_by_serial[display['serial']]
        frame = command['command'] if command['event'] == 'script_frame' else 0
        assert display['map_mask'] & display['pixel_mask'] & (1 << frame), (asset.name, display, frame)
        first_display.setdefault(display['serial'], display)
    assert set(first_display) == set(command_by_serial)
    assert all(b['number'] == a['number'] + 1 for a, b in zip(displays, displays[1:]))
    # SameBoy can deliver the callback at the end of a four-T CPU step.
    # Publication durations use counted display intervals, not callback jitter.
    assert all(abs(d['t'] - displays[0]['t'] -
                   (d['number'] - displays[0]['number'])*INTERVAL) <= 4 for d in displays)

    publications = []
    for command, following in zip(commands, commands[1:]):
        frame = command['command'] if command['event'] == 'script_frame' else 0
        start = first_display[command['serial']]['number']
        end = first_display[following['serial']]['number']
        publications.append(dict(serial=command['serial'], frame=frame, display=start,
                                 duration=end-start, idle=command['idle']))
    actual = coalesce((p['frame'], p['duration']) for p in publications)
    expected = coalesce((e.frame, e.duration) for e in asset.events)
    assert [e[0] for e in actual] == [e[0] for e in expected], (asset.name, actual, expected)
    assert all(a[1] >= e[1] for a, e in zip(actual, expected)), (asset.name, actual, expected)
    wanted = sum(e.duration for e in asset.events)
    measured = sum(p['duration'] for p in publications)

    finish = next(e['t'] for e in trace if e['event'] == 'animation_finished')
    spans = [e for e in trace if e['event'] == 'span']
    names = ('PokeAnim_GetFrame', 'PokeAnim_PlaceGraphic', 'PokeAnim_CountBitmaskTiles',
             'PokeAnim_ConvertAndApplyBitmask', 'PadTilemapForHDMATransfer',
             'HDMATransferTilemapToWRAMBank3', 'WaitDMATransfer')
    profile = {name: stats([s for s in spans if s['name'] == name and
                           s['phase'] == 1 and s['end'] <= finish]) for name in names}
    dma = [s for s in spans if s['name'] == 'DMATransfer' and s['phase'] == 1 and
           s['end'] <= finish and s['end'] - s['start'] > 36]
    assert all(s['end'] - s['start'] == 1228 for s in dma)
    profile['actual_map_dma'] = stats(dma)

    startup = next(s for s in spans if s['name'] == 'GetAnimatedFrontpic')
    startup_parts = {name: stats([s for s in spans if s['name'] == name and
                                 s['start'] >= startup['start'] and s['end'] <= startup['end']])
                     for name in ('Decompress', 'Request2bpp', 'DelayFrame')}

    audio = None
    start = next((e for e in trace if e['event'] == 'audio_start'), None)
    if start:
        stop = next(e for e in trace if e['event'] == 'audio_stop' and e['t'] > start['t'])
        empty = [e for e in trace if e['event'] == 'audio_empty' and start['t'] < e['t'] < stop['t']]
        fills = [s for s in spans if s['name'] == 'SampledCry_FillRollingCache' and
                 start['t'] < s['start'] < s['end'] <= stop['t']]
        produced = sum(s['cache_end'] - s['cache_start'] +
                       s['remaining_start'] - s['remaining_end'] for s in fills)
        services = [s for s in spans if s['name'] == 'ServiceSampledCryAsync' and
                    start['t'] < s['start'] < stop['t']]
        gaps = [b['start'] - a['start'] for a, b in zip(services, services[1:])]
        elapsed = stop['t'] - start['t']
        audio = dict(total_blocks=start['remaining'], startup_blocks=start['cache'],
                     completed_refills=len(fills), completed_refill_blocks=produced,
                     service_calls_started=len(services), elapsed_t=elapsed,
                     elapsed_intervals=elapsed/INTERVAL, max_service_start_gap_t=max(gaps),
                     max_service_start_gap_intervals=max(gaps)/INTERVAL,
                     runtime_blocks_per_interval=produced/(elapsed/INTERVAL),
                     underrun_remaining=empty[0]['remaining'] if empty else 0,
                     halt_idle_t=stop['idle_t'] - start['idle_t'],
                     halt_idle_fraction=(stop['idle_t'] - start['idle_t'])/elapsed,
                     refill_wall_cost=stats(fills))
        assert start['cache'] + produced + audio['underrun_remaining'] == start['remaining']

    report[asset.name] = dict(
        common_boundaries_unchanged=True, checked_display_intervals=len(displays),
        bad_picture_intervals=0, authored_intervals=wanted, actual_intervals=measured,
        extra_intervals=measured-wanted, authored_seconds=wanted*INTERVAL/HZ,
        actual_seconds=measured*INTERVAL/HZ, publications=publications,
        normalized_events=[dict(frame=e[0], wanted=e[1], actual=a[1]) for e,a in zip(expected,actual)],
        profile=profile, get_animated_frontpic=stats([startup]),
        startup_components=startup_parts, audio=audio,
    )

(OUT / 'registration-baseline-audit.json').write_text(json.dumps(report, indent=2) + '\n')
for species, item in report.items():
    print(species, f"{item['authored_intervals']} -> {item['actual_intervals']} intervals",
          f"{item['checked_display_intervals']} rendered frames checked",
          'audio=' + str(item['audio']['underrun_remaining'] if item['audio'] else 'synth'))
