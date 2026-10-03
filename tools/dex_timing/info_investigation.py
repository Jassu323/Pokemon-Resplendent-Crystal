"""Read-only evidence checks for Info returns and missing evolution content.

The linked gameplay graph is decoded independently of the Info generator.
Optional return reports inspect every outgoing lower-panel display image, not
just the correctly restored final Listing. All output belongs under build/.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

from .assets import Repository, offset
from .cold_listing import ROOT
from pokedex_info_assets import Compiler, constants, evolution_graph, future_stages, species


def linked_evolutions(repo, names):
    result, index = {}, 0
    for label, count in (('EvosAttacksPointers1', 151),
                         ('EvosAttacksPointers2', 100),
                         ('EvosAttacksPointers3', len(names) - 251)):
        bank, address = repo.symbols[label]
        table = offset((bank, address))
        for row in range(count):
            pointer = int.from_bytes(repo.rom[table + row * 2:table + row * 2 + 2], 'little')
            if not 0x4000 <= pointer < 0x8000:
                raise ValueError(f'Invalid evolution pointer: {label}:{row}')
            at = offset((bank, pointer))
            edges = []
            while repo.rom[at]:
                kind = repo.rom[at]
                if kind not in range(1, 6):
                    raise ValueError(f'Unknown linked evolution method: {kind}')
                length = 5 if kind == 5 else 4
                target = int.from_bytes(repo.rom[at + length - 2:at + length], 'little')
                if not 1 <= target <= len(names):
                    raise ValueError(f'Invalid evolution target: {target}')
                edges.append((names[target - 1], tuple(repo.rom[at:at + length - 2])))
                at += length
                if at >= (bank + 1) * 0x4000:
                    raise ValueError('Evolution data crossed its ROM bank')
            result[names[index]] = edges
            index += 1
    return result


def visible_atlas_b_cells(vram):
    """Screen BG-map cells which still reference the borrowed frame-0 atlas."""
    return [(row, col, vram[0x1800 + row * 32 + col])
            for row in range(9, 16) for col in range(1, 20)
            if vram[0x3800 + row * 32 + col] & 8
            and vram[0x1800 + row * 32 + col] < 40]


def replaced_visible_tiles(before, after):
    return [(row, col, tile) for row, col, tile in visible_atlas_b_cells(before)
            if after[0x1800 + row * 32 + col] == tile
            and after[0x3800 + row * 32 + col] == before[0x3800 + row * 32 + col]
            and before[0x3000 + tile * 16:0x3010 + tile * 16]
            != after[0x3000 + tile * 16:0x3010 + tile * 16]]


def graph_audit(repo):
    names = species()
    source, linked = evolution_graph(), linked_evolutions(repo, names)
    ids = constants(ROOT / 'constants/pokemon_data_constants.asm')
    ids.update(constants(ROOT / 'constants/item_constants.asm'))
    def number(value):
        return ids[value] if value in ids else int(value)
    mismatch = []
    for name in names:
        expected = [(target, tuple(number(value) & 255 for value in method))
                    for target, method in source[name]]
        if expected != linked[name]:
            mismatch.append(name)
    compiler = Compiler()
    data = compiler.compile()
    future_mismatches = []
    # Compare emitted target lists to the independently decoded runtime graph.
    table = offset(repo.symbols['PokedexInfoSpecies'])
    roots_bank = repo.symbols['PokedexInfoSpecies'][0]
    for index, name in enumerate(names):
        entry = repo.rom[table + index * 3:table + index * 3 + 3]
        count, address = entry[0], int.from_bytes(entry[1:], 'little')
        at = offset((roots_bank, address))
        targets = []
        for i in range(count):
            record = int.from_bytes(repo.rom[at + i * 2:at + i * 2 + 2], 'little')
            # Root entries are ROM addresses, not indices into the host records.
            if not 0x4000 <= record < 0x8000:
                raise ValueError(f'Invalid Info evolution pointer: {name}:{record}')
            record_at = offset((roots_bank, record))
            target = int.from_bytes(repo.rom[record_at:record_at + 2], 'little')
            if not 1 <= target <= len(names):
                raise ValueError(f'Invalid Info evolution target: {name}:{target}')
            targets.append(names[target - 1])
        expected = [target for target, _ in future_stages(linked, name)]
        if targets != expected:
            future_mismatches.append(name)
    badge = (ROOT / 'gfx/pokedex/pokedex_page_numbers.2bpp').read_bytes()
    page5_upper = badge[10 * 16:11 * 16]
    matches = [p for p in range(1, 5) if badge[p * 32:p * 32 + 16] == page5_upper]
    examples = {}
    for name in ('CHIKORITA', 'EEVEE', 'TREECKO', 'TORCHIC', 'MUDKIP', 'SHINX',
                 'RHYHORN', 'DUSKULL', 'SKITTY', 'DELCATTY'):
        edges = future_stages(linked, name)
        examples[name] = dict(direct=linked[name], future=[t for t, _ in edges],
                              info_pages=1 + (len(edges) + 1) // 2)
    lowest = re.findall(r'^\s*dw (\w+)', (ROOT / 'data/pokemon/first_stages.asm').read_text(), re.M)
    if len(lowest) != len(names):
        raise ValueError('First-stage family table and species constants disagree')
    lowest = dict(zip(names, lowest))
    unreachable = [(name, lowest[name]) for name in names if lowest[name] != name
                   and name not in {t for t, _ in future_stages(linked, lowest[name])}]
    inconsistent = [(name, target, lowest[name], lowest[target])
                    for name in names for target, _ in linked[name] if lowest[name] != lowest[target]]
    return dict(provenance=repo.hashes, species=len(names),
                direct_edges=sum(map(len, linked.values())),
                custom_species_with_edges=[n for n in names[251:] if linked[n]],
                source_linked_mismatches=mismatch,
                linked_info_future_mismatches=future_mismatches,
                generated_records=len(data['records']), examples=examples,
                first_stage_members_unreachable=unreachable,
                first_stage_link_inconsistencies=inconsistent,
                page5_upper_matches_existing_pages=matches,
                page5_lower_is_new=all(badge[11 * 16:12 * 16] != badge[(p * 2 + 1) * 16:(p * 2 + 2) * 16]
                                       for p in range(1, 5)))


def return_audit(directory):
    from PIL import Image, ImageChops
    report = json.loads((directory / 'report.json').read_text())
    result = []
    for case in report['results']:
        folder = directory / case['case']['label']
        trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
        frames = [e for e in trace if e['event'] == 'frame']
        leave = next(e for e in trace if e['event'] == 'phase' and e['phase'] == 'leave')
        before = bytes.fromhex(leave['vram'])
        corrupt_tiles = [len(replaced_visible_tiles(before, bytes.fromhex(e['vram'])))
                         for e in trace if e['event'] == 'phase' and 'vram' in e
                         and e['state'] == 5 and e['scroll'][2] == 167]
        # A stable canceled Info panel must not mutate its visible body while
        # its owner is still displayed. Compare to its first complete frame.
        held = [(i, e) for i, e in enumerate(frames, 1) if e['state'] == 5 and e['scroll'][2] == 167]
        changed = []
        if held:
            baseline = Image.open(folder / f'trace-{held[0][0]:03}.ppm').convert('RGB').crop((0, 80, 160, 128))
            for i, frame in held:
                image = Image.open(folder / f'trace-{i:03}.ppm').convert('RGB').crop((0, 80, 160, 128))
                if ImageChops.difference(baseline, image).getbbox():
                    changed.append(dict(frame=i, display=frame['display']))
        result.append(dict(case=case['case']['label'],
                           borrowed_cells_visible=len(visible_atlas_b_cells(before)),
                           max_visible_tiles_overwritten=max(corrupt_tiles, default=0),
                           changed_outgoing_body_frames=changed,
                           return_intervals=case['summary']['return_intervals'],
                           final_failures=case['restoration_failures'],
                           follow_up_issues=case.get('follow_up', {}).get('issues', [])))
    return dict(provenance=report['provenance'],
                cases=len(result), visibly_changed_cases=sum(bool(c['changed_outgoing_body_frames']) for c in result),
                results=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--returns', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, help='Run all species from these matching normal-input checkpoints')
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    report = dict(graph=graph_audit(repo), returns=[return_audit(p) for p in args.returns])
    if args.runtime:
        from .info_ui import run_case
        manifest = json.loads((args.runtime / 'provenance.json').read_text())
        if any(manifest[key] != value for key, value in repo.hashes.items()):
            raise ValueError('Runtime checkpoints do not match the production ROM')
        names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
        names = [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower()) for n in names]
        runtime_output = args.output / 'runtime'
        runtime_output.mkdir(exist_ok=True)
        config = dict(core=str(args.runtime / 'cold-listing-core'), rom=str(ROOT / 'pokecrystal.gbc'),
                      battery=str(args.runtime / 'fixture.sav'),
                      states=str(args.runtime / 'listing-states'), output=str(runtime_output),
                      names=names, uncaught=False)
        tasks = [(config, index, name, 'settled') for index, name in enumerate(names)]
        rows = []
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for row in pool.map(run_case, tasks):
                rows.append(row)
                if len(rows) % 50 == 0 or row['issues']:
                    print(json.dumps(dict(completed=len(rows), species=row['species'], issues=row['issues'])), flush=True)
        report['runtime'] = dict(tested=len(rows), passed=sum(not r['issues'] for r in rows), results=rows)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(species=report['graph']['species'], edges=report['graph']['direct_edges'],
        graph_mismatches=report['graph']['source_linked_mismatches'],
        info_mismatches=report['graph']['linked_info_future_mismatches'],
        returns=[dict(cases=r['cases'], changed=r['visibly_changed_cases']) for r in report['returns']],
        runtime={key: value for key, value in report.get('runtime', {}).items() if key != 'results'})))
    return int(bool(report['graph']['source_linked_mismatches'] or report['graph']['linked_info_future_mismatches']
                    or any(r['issues'] for r in report.get('runtime', {}).get('results', []))))


if __name__ == '__main__':
    raise SystemExit(main())
