"""Assert executable registration preflight against independent asset pictures."""
import json
import os
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get('REGISTRATION_OUT', Path(__file__).resolve().parent))
SPECIES = os.environ.get('REGISTRATION_SPECIES', 'caterpie,dusknoir,luxray,metagross').split(',')
sys.path.insert(0, str(ROOT))
from tools.dex_timing.assets import Repository
from tools.dex_timing.cold_listing import expected_picture

INTERVAL = 70224


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def spans(trace, name, phase=None):
    return [e for e in trace if e['event'] == 'span' and e['name'] == name
            and (phase is None or e['phase'] == phase)]


def costs(items):
    values = [e['end'] - e['start'] for e in items]
    return dict(count=len(values), min_t=min(values), median_t=median(values),
                max_t=max(values), total_t=sum(values)) if values else {}


def audit(asset, variant, mode):
    suffix = '' if mode == 'none' else '-' + mode
    path = OUT / f'{asset.name}-{variant}{suffix}-trace.jsonl'
    trace = read(path)
    commands = [e for e in trace if e['event'] == 'script_frame']
    publications = [e for e in trace if e['event'] == 'published']
    displays = [e for e in trace if e['event'] == 'display' and e['type'] == 0]
    display_by_number = {e['number']: e for e in displays}
    commands_by_serial = {e['serial']: e for e in commands}
    expected = [(e.frame, e.duration) for e in asset.events] + [(0, 0)]
    observed = [(e['command'], e['duration']) for e in commands]
    assert observed == expected[:len(observed)], (asset.name, variant, mode, observed, expected)
    if mode != 'exit':
        assert observed == expected
        assert len(publications) == len(expected)
    assert publications and all(e['misses'] == 0 for e in publications)
    deadline = publications[0]['display']
    margins = []
    for i, publication in enumerate(publications):
        assert publication['serial'] == i + 1
        assert publication['display'] == deadline, (asset.name, mode, i, publication, deadline)
        assert publication['mode'] == 1, publication
        if i:
            built = commands_by_serial[publication['serial']]
            completed = next(s['end'] for s in spans(trace, 'ProtoBuild')
                             if s['start'] <= built['t'] < s['end'])
            margins.append(display_by_number[deadline]['t'] - completed)
        deadline += expected[i][1]
    checked = [e for e in displays if e['phase'] == 1 and e['serial']]
    for display in checked:
        frame = commands_by_serial[display['serial']]['command']
        assert display['map_mask'] & display['pixel_mask'] & (1 << frame), (
            asset.name, variant, mode, frame, display)
    assert all(b['number'] == a['number'] + 1 for a, b in zip(checked, checked[1:]))
    assert all(abs(e['t'] - checked[0]['t'] -
                   (e['number'] - checked[0]['number']) * INTERVAL) <= 4 for e in checked)
    finishes = [e for e in trace if e['event'] == 'animation_finished']
    if mode != 'exit':
        assert len(finishes) == 1 and finishes[0]['hvblank'] != 0x88
        assert finishes[0]['frame_counter'] == 0
    second_page = [e for e in trace if e['event'] == 'description' and e['dex_status'] == 1]
    if mode != 'none':
        assert len(second_page) == 1
    returned = [e for e in trace if e['event'] == 'registration_return']
    if mode == 'exit':
        assert len(returned) == 1 and returned[0]['hvblank'] != 0x88
        assert not finishes, 'Exit pulse failed to cancel before natural completion'
    snapshots = [e for e in trace if e['event'] == 'ui_snapshot']
    assert all(e['mismatches'] == 0 for e in snapshots)
    for snapshot in snapshots:
        if snapshot['name'] in ('page1', 'page2'):
            expected_page = 0 if snapshot['name'] == 'page1' else 1
            assert snapshot['status'] == expected_page
            assert snapshot['page_backing'] == snapshot['page_vram'] == 0x57 + expected_page
    wait_events = [e for e in trace if e['event'] == 'wait_entry']
    if mode != 'none':
        assert len(wait_events) == 2
        assert wait_events[1]['display'] < publications[0]['display'] + 15

    audio = None
    start = next((e for e in trace if e['event'] == 'audio_start'), None)
    if start:
        stop = next(e for e in trace if e['event'] == 'audio_stop' and e['t'] > start['t'])
        empties = [e for e in trace if e['event'] == 'audio_empty' and start['t'] < e['t'] < stop['t']]
        fills = [e for e in spans(trace, 'SampledCry_FillRollingCache')
                 if start['t'] < e['start'] < e['end'] <= stop['t']]
        produced = sum(e['cache_end'] - e['cache_start'] +
                       e['remaining_start'] - e['remaining_end'] for e in fills)
        service = [e for e in spans(trace, 'ServiceSampledCryAsync')
                   if start['t'] < e['start'] < stop['t']]
        gaps = [b['start'] - a['start'] for a, b in zip(service, service[1:])]
        audio = dict(total=start['remaining'], startup=start['cache'], remaining=stop['remaining'],
                     empty_branches=len(empties), completed_refill_blocks=produced,
                     max_service_gap_t=max(gaps),
                     refill_cost=costs(fills),
                     elapsed_intervals=(stop['t'] - start['t']) / INTERVAL,
                     halt_fraction=(stop['idle_t'] - start['idle_t']) / (stop['t'] - start['t']))
        assert not empties and stop['remaining'] == 0
        assert start['cache'] == 32 and start['cache'] + produced == start['remaining']
    startup = spans(trace, 'GetAnimatedFrontpic')[0]
    base = read(OUT / f'{asset.name}-trace.jsonl')
    old_wait = next(e['t'] for e in base if e['event'] == 'wait_entry')
    wait = wait_events[0]['t']
    return dict(variant=variant, input=mode, species=asset.name,
                publications=len(publications), checked_displays=len(checked), bad_pictures=0,
                authored_intervals=sum(e.duration for e in asset.events),
                published_intervals=publications[-1]['display'] - publications[0]['display'],
                min_prepared_lead_t=min(margins),
                max_publication_ly=max(e['ly'] for e in publications),
                owner_to_wait_t=wait, startup_saving_t=old_wait - wait,
                dictionary_load_t=startup['end'] - startup['start'],
                first_publication_t=publications[0]['t'],
                description_wait_intervals=wait_events[1]['display'] - second_page[0]['display']
                    if second_page else None,
                returned=bool(returned), audio=audio,
                costs={name: costs(spans(trace, name, 1)) for name in (
                    'ProtoBuild', 'ProtoService', 'ProtoPublish', 'ProtoCopyBacking',
                    'ProtoCopyVRAM', 'ProtoFillBacking', 'ProtoFillVRAM')})


repo = Repository(ROOT, OUT/'fixture.gbc', OUT/'fixture.sym')
structural = dict(assets=0, pictures=0, max_duration=0, max_pairs=0, max_resident_id=0)
for asset in repo.load():
    width = asset.width
    base_count = width * width
    resident = {i: bytes(16) for i in range(49)}
    for x in range(width):
        for y in range(width):
            source = x * width + y
            padded = (x + int(width != 7)) * 7 + y + 7 - width
            resident[padded] = asset.dictionary[source*16:(source+1)*16]
    for source in range(base_count, asset.total):
        target = source - base_count + 49
        if target >= 127:
            target += 1
        assert target < 256, (asset.name, target)
        resident[target] = asset.dictionary[source*16:(source+1)*16]
        structural['max_resident_id'] = max(structural['max_resident_id'], target)
    for frame, plan in enumerate(asset.plans):
        tilemap = [x*7+y for y in range(7) for x in range(7)]
        for position, source in plan.pairs:
            target = source
            if not position & 128:
                target = source - base_count + 49
                if target >= 127:
                    target += 1
            tilemap[position & 127] = target
        actual = b''.join(resident[tile] for tile in tilemap)
        assert actual == expected_picture(asset, frame), (asset.name, frame)
        structural['pictures'] += 1
        structural['max_pairs'] = max(structural['max_pairs'], len(plan.pairs))
    structural['assets'] += 1
    structural['max_duration'] = max(structural['max_duration'], *(e.duration for e in asset.events))
assert structural['max_duration'] < 128
assert structural['max_pairs'] <= 49
(OUT/'resident-mapping-audit.json').write_text(json.dumps(structural, indent=2)+'\n')
print('structural', structural)
report = []
for variant in ['resident', 'resident-bulk']:
    for mode in ['none', 'description', 'exit']:
        for asset in repo.load(SPECIES):
            suffix = '' if mode == 'none' else '-' + mode
            if not (OUT/f'{asset.name}-{variant}{suffix}-trace.jsonl').exists():
                continue
            result = audit(asset, variant, mode)
            report.append(result)
            print(variant, mode, asset.name, result['published_intervals'],
                  'audio', result['audio'] and result['audio']['remaining'],
                  'pictures', result['checked_displays'])
(OUT/'registration-preflight-audit.json').write_text(json.dumps(report, indent=2)+'\n')
