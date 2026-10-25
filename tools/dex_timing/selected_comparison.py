"""Summarize the six frozen Selected display trials without mismatching pages."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from .cold_listing import ROOT
from pokedex_info_assets import Compiler


SOURCES = {
    'ram': ('dex-selected-semantic-ram-20261012-v5', 'dex-selected-ancestors-ram-20261012-v8'),
    'vram': ('dex-selected-semantic-vram-20261012-v1', 'dex-selected-ancestors-vram-20261012-v6'),
    'rom': ('dex-selected-semantic-rom-20261012-v2', 'dex-selected-ancestors-rom-20261012-v7'),
}
CONTROL = 'dex-selected-production-control-20261012-v1'


def read(source, relative):
    return json.loads((ROOT / 'build' / source / relative).read_text())


def key(row):
    return tuple(row[name] for name in ('species', 'style', 'action', 'phase', 'page', 'input_phase'))


def distribution(values):
    if not values:
        return None
    return dict(count=len(values), min=min(values), median=statistics.median(values), max=max(values),
                slower_display_frame=sum(value > 8 for value in values),
                faster_display_frame=sum(value < -8 for value in values))


def constant(name):
    return {'porygonz': 'PORYGON_Z', 'unown_a': 'UNOWN'}.get(name, name.upper())


def page_signature(data, species, page):
    if not page:
        return ('Stats',)
    name = constant(species)
    if page > len(data['pages'][name]):
        return None
    return (data['headings'][name][page], tuple(
        (data['records'][record][0], tuple(data['lines'][line][0]
         for line in data['records'][record][1])) for record in data['pages'][name][page - 1]))


def same_transition(row, left, right):
    if row['action'] != 'cycle' and row['action'] != 'listing' and row['action'] != 'info-area-return':
        return True
    if page_signature(left, row['species'], row['page']) != page_signature(right, row['species'], row['page']):
        return False
    if row['action'] != 'cycle':
        return True
    name = constant(row['species'])
    lp = (row['page'] + 1) % (1 + len(left['pages'][name]))
    rp = (row['page'] + 1) % (1 + len(right['pages'][name]))
    return page_signature(left, row['species'], lp) == page_signature(right, row['species'], rp)


def paired(before, after, left=None, right=None):
    baseline = {key(row): row for row in before}
    groups = defaultdict(lambda: defaultdict(list))
    excluded = 0
    for row in after:
        prior = baseline.get(key(row))
        if prior is None:
            continue
        if left is not None and not same_transition(row, left, right):
            excluded += 1
            continue
        group = (row['style'], row['action'], row['phase'])
        for metric in ('first_visible', 'complete_visible'):
            if row.get(metric) and prior.get(metric):
                groups[group][metric].append(row[metric]['ms'] - prior[metric]['ms'])
        if row.get('ready_t') and prior.get('ready_t'):
            elapsed = row['ready_t'] - row['initial_hashes']['t']
            old_elapsed = prior['ready_t'] - prior['initial_hashes']['t']
            groups[group]['owner_ready_ms'].append((elapsed - old_elapsed) * 1000 / 4194304)
    return dict(excluded_different_page_transitions=excluded, groups=[
        dict(style=group[0], action=group[1], phase=group[2],
             **{metric: distribution(values) for metric, values in metrics.items()})
        for group, metrics in sorted(groups.items())])


def startup(before, after):
    lookup = {(row['style'], row['phase']): row for row in before}
    return {style: distribution([row['reopen_ms'] - lookup[(style, row['phase'])]['reopen_ms']
                                for row in after if row['style'] == style])
            for style in ('modern', 'legacy')}


def ancestor_latencies(rows, data):
    groups = defaultdict(list)
    species_groups = defaultdict(list)
    for row in rows:
        if row['action'] != 'cycle':
            continue
        name = constant(row['species'])
        page = (row['page'] + 1) % (1 + len(data['pages'][name]))
        if not page or data['headings'][name][page] != 'Evolves from':
            continue
        if row.get('complete_visible'):
            value = row['complete_visible']['ms']
            groups[(row['style'], row['phase'])].append(value)
            species_groups[(row['species'], row['style'], row['phase'])].append(value)
    return dict(groups=[dict(style=k[0], phase=k[1], complete_ms=distribution(v)) for k, v in sorted(groups.items())],
                species=[dict(species=k[0], style=k[1], phase=k[2], complete_ms=distribution(v))
                         for k, v in sorted(species_groups.items())])


def mode_delta(before, after):
    lookup = {(r['presentation'], r['index'], r['phase']): r for r in before['results']}
    groups = defaultdict(list)
    for row in after['results']:
        prior = lookup[(row['presentation'], row['index'], row['phase'])]
        for transition, value in row['transitions'].items():
            groups[transition].append(value['complete_ms'] - prior['transitions'][transition]['complete_ms'])
    return {name: distribution(values) for name, values in groups.items()}


def entry_delta(before, after):
    entry_key = lambda row: tuple(row[k] for k in ('species', 'presentation', 'hover', 'phase'))
    lookup = {entry_key(row): row for row in before}
    groups = defaultdict(lambda: defaultdict(list))
    for row in after:
        prior = lookup[entry_key(row)]
        group = (row['presentation'], row['hover'])
        for metric in ('first_visible', 'complete_visible'):
            groups[group][metric].append(row['timing'][metric]['ms'] - prior['timing'][metric]['ms'])
        reveal = row['timing']['input_accept_ms'] + row['playback']['static_reveal_frames'] * 70224 / 4194.304
        old_reveal = prior['timing']['input_accept_ms'] + prior['playback']['static_reveal_frames'] * 70224 / 4194.304
        groups[group]['static_reveal_ms'].append(reveal - old_reveal)
    return [dict(style=k[0], hover=k[1], **{m: distribution(v) for m, v in metrics.items()})
            for k, metrics in sorted(groups.items())]


def summarize():
    compiler = Compiler()
    old_data, new_data = compiler.compile(), compiler.compile(ancestors=True)
    control_main = read(CONTROL, 'architecture-timing/summary.json')['rows']
    control_start = read(CONTROL, 'startup-timing/summary.json')['rows']
    control_modes = read(CONTROL, 'focused/ancestor-font-reuse/summary.json')
    control_entry = read(CONTROL, 'entry-timing/summary.json')['rows']
    result = dict(control=CONTROL, old_pages=sum(map(len, old_data['pages'].values())),
                  new_pages=sum(map(len, new_data['pages'].values())), architectures={})
    for architecture, (old, new) in SOURCES.items():
        variants = []
        for source, data in ((old, old_data), (new, new_data)):
            manifest = read(source, 'runtime-manifest.json')
            main = read(source, 'architecture-timing/summary.json')
            feature = read(source, 'feature-timing/summary.json')
            starts = read(source, 'startup-timing/summary.json')
            enters = read(source, 'entry-timing/summary.json')
            variants.append(dict(source=source, rom_sha256=manifest['rom_sha256'], delta=manifest['delta'],
                                 performance_cases=main['cases'], performance_failures=main['failures'],
                                 feature_cases=feature['cases'], feature_failures=feature['failures'],
                                 vs_production=paired(control_main, main['rows'], old_data, data),
                                 startup_vs_production=startup(control_start, starts['rows']),
                                 entry_cases=enters['cases'], entry_failures=enters['failures'],
                                 entry_vs_production=entry_delta(control_entry, enters['rows']),
                                 ancestor_latency=ancestor_latencies(feature['rows'], data)))
        result['architectures'][architecture] = dict(variants=variants,
            incremental_feature_bytes={region: variants[1]['delta'][region] - variants[0]['delta'][region]
                                       for region in variants[0]['delta']},
            feature_main_delta=paired(read(old, 'architecture-timing/summary.json')['rows'],
                                      read(new, 'architecture-timing/summary.json')['rows'], old_data, new_data),
            feature_existing_pages_delta=paired(read(old, 'feature-timing/summary.json')['rows'],
                                                read(new, 'feature-timing/summary.json')['rows'], old_data, new_data),
            feature_startup_delta=startup(read(old, 'startup-timing/summary.json')['rows'],
                                          read(new, 'startup-timing/summary.json')['rows']),
            feature_modes_delta=mode_delta(read(old, 'focused/ancestor-font-reuse/summary.json'),
                                           read(new, 'focused/ancestor-font-reuse/summary.json')),
            feature_entry_delta=entry_delta(read(old, 'entry-timing/summary.json')['rows'],
                                            read(new, 'entry-timing/summary.json')['rows']))
    for index, label in ((0, 'without_ancestors'), (1, 'with_ancestors')):
        ram, vram, rom = (SOURCES[a][index] for a in ('ram', 'vram', 'rom'))
        result[label] = dict(
            vram_vs_ram=paired(read(ram, 'architecture-timing/summary.json')['rows'],
                               read(vram, 'architecture-timing/summary.json')['rows']),
            rom_vs_vram=paired(read(vram, 'architecture-timing/summary.json')['rows'],
                               read(rom, 'architecture-timing/summary.json')['rows']),
            vram_vs_ram_all_pages=paired(read(ram, 'feature-timing/summary.json')['rows'],
                                         read(vram, 'feature-timing/summary.json')['rows']),
            rom_vs_vram_all_pages=paired(read(vram, 'feature-timing/summary.json')['rows'],
                                         read(rom, 'feature-timing/summary.json')['rows']))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value['incremental_feature_bytes'] for key, value in report['architectures'].items()}))
