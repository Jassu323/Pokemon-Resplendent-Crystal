"""Paired return/pixel/cache regressions against a frozen preflight baseline."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

from PIL import Image, ImageChops

from .assets import Repository
from .cold_listing import Driver, ROOT
from .info_ui import BOOT
from .info_investigation import replaced_visible_tiles, visible_atlas_b_cells
from .listing_restoration import cases, compile_observer, follow_up, run_case


def preservation_audit(directory):
    trace = [json.loads(s) for s in (directory / 'trace.jsonl').read_text().splitlines()]
    phases = [e for e in trace if e['event'] == 'phase']
    leave = next(e for e in phases if e['phase'] == 'leave')
    before = bytes.fromhex(leave['vram'])
    frames = [e for e in trace if e['event'] == 'frame']
    held = [(i, e) for i, e in enumerate(frames, 1) if e['state'] == 5 and e['scroll'][2] == 167]
    changed = []
    if held:
        first = Image.open(directory / f'trace-{held[0][0]:03}.ppm').convert('RGB')
        for i, event in held:
            current = Image.open(directory / f'trace-{i:03}.ppm').convert('RGB')
            if ImageChops.difference(first, current).crop((0, 72, 160, 128)).getbbox():
                changed.append(i)
    before_copy = next((e for e in phases if e['phase'] == 'info_return_relocate'), None)
    after_copy = next((e for e in phases if e['phase'] == 'info_return_published'), None)
    translation_issues = []
    if after_copy:
        old, new = bytes.fromhex(before_copy['vram']), bytes.fromhex(after_copy['vram'])
        for row in range(9, 16):
            for col in range(1, 20):
                at = 0x1800 + row * 32 + col
                if not (old[at + 0x2000] & 8 and old[at] < 40) and old[at] != new[at]:
                    translation_issues.append(f'permanent_cell_{row}_{col}')
        for row, col, tile in visible_atlas_b_cells(old):
            at = 0x1800 + row * 32 + col
            target = 0x1000 + int.from_bytes(new[at:at + 1], 'little', signed=True) * 16 + 0x2000
            if old[0x3000 + tile * 16:0x3010 + tile * 16] != new[target:target + 16]:
                translation_issues.append(f'tile_{row}_{col}')
        for key in ('bg_pal', 'obj_pal', 'oam'):
            if before_copy[key] != after_copy[key]:
                translation_issues.append(key)
        if old[0x3800 + 9 * 32:0x3800 + 16 * 32] != new[0x3800 + 9 * 32:0x3800 + 16 * 32]:
            translation_issues.append('attributes')
        if visible_atlas_b_cells(new):
            translation_issues.append('borrowed_references_survived')
    exposed = max((len(replaced_visible_tiles(before, bytes.fromhex(e['vram'])))
                   for e in phases if e['state'] == 5 and e['scroll'][2] == 167), default=0)
    return dict(changed_outgoing_frames=changed, exposed_tile_replacements=exposed,
                relocated=bool(after_copy), translation_issues=translation_issues,
                relocation_cycles=after_copy['t'] - before_copy['t'] if after_copy else 0,
                borrowed_cells=len(visible_atlas_b_cells(before)))


def paired(task):
    configs, case, names = task
    rows = []
    for config in configs:
        output = Path(config['output'])
        driver = Driver(config['core'], config['rom'], BOOT, config['battery'],
                        output / (case['label'] + '-core.log'))
        reference = Driver(config['core'], config['rom'], BOOT, config['battery'],
                           output / (case['label'] + '-reference-core.log'))
        try:
            actual_case = dict(case, moves_supported=config['variant'] == 'candidate')
            result = run_case(driver, Path(config['checkpoints']), output, actual_case, names, True)
            result['follow_up'] = follow_up(driver, reference, Path(config['checkpoints']),
                output / case['label'] / 'follow-up', len(names))
            result['preservation'] = preservation_audit(output / case['label'])
            (output / case['label'] / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
            rows.append(result)
        finally:
            driver.close()
            reference.close()
    baseline, candidate = rows
    delta = candidate['summary']['return_cycles'] - baseline['summary']['return_cycles']
    return dict(case=case['label'], baseline=baseline, candidate=candidate,
                delta_cycles=delta, delta_intervals=delta / 70224, delta_ms=delta / 4194.304)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--baseline-checkpoints', type=Path, required=True)
    parser.add_argument('--candidate-rom', type=Path,
                        help='Override the preflight cartridge, e.g. the promoted production ROM')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', action='append')
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--cancel-sweep', action='store_true')
    parser.add_argument('--cancel-ages', type=int, nargs='+',
                        help='Additional explicit cancellation ages, in display intervals')
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    names = re.findall(r'^\s*dw (\w+)\s*$', (ROOT / 'data/pokemon/dex_order_new.asm').read_text(), re.M)
    names = [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower()) for n in names]
    suite = cases(names)
    suite += [dict(label=f'{name}-info{page + 1}', start=name, pages=0,
                   wait=wait, description_page=False, info_page=page)
              for name, page, wait in (
                  ('chikorita', 0, None), ('chikorita', 1, None), ('tyrogue', 2, None),
                  ('eevee', 3, None), ('chansey', 0, None), ('blissey', 0, None),
                  ('skitty', 1, None), ('dusknoir', 0, 8), ('kyogre', 0, 0))]
    suite += [dict(label=f'chikorita-info-down{n}', start='chikorita', pages=0,
                   wait=None, description_page=False, info_page=0, info_internal_pages=n) for n in (1, 2)]
    suite += [dict(label='regigigas', start='regigigas', pages=0, wait=None, description_page=False)]
    suite += [dict(label=f'{name}-moves{page + 1}-down{internal}', start=name, pages=0,
                   wait=wait, description_page=False, moves_page=page, moves_internal_pages=internal)
              for name, page, internal, wait in (
                  ('chikorita', 0, 0, None), ('chikorita', 8, 0, None),
                  ('mew', 9, 0, None), ('mew', 14, 0, None),
                  ('chansey', 0, 0, None), ('tyrogue', 0, 0, None),
                  ('dusknoir', 0, 0, 8), ('weavile', 0, 0, 8),
                  ('chikorita', 0, 1, None), ('chikorita', 0, 2, None))]
    if args.cancel_sweep:
        suite = [dict(label=f'{name}-{kind}-cancel{age}', start=name, pages=0, wait=None,
                      description_page=False, info_page=page, **{kind + '_cancel_frames': age})
                 for name, page in (('chikorita', 0), ('chansey', 0), ('tyrogue', 2),
                                    ('eevee', 3), ('dusknoir', 0))
                 for kind in ('info', 'description')
                 for age in (args.cancel_ages or (*range(13), 16, 24))]
    suite = [case for case in suite if not args.case or case['label'] in args.case]
    suite = [dict(case, label=case['label'] if repeat == 0 else f'{case["label"]}-repeat{repeat + 1}')
             for case in suite for repeat in range(args.repeat)]
    configs = []
    metadata = json.loads((args.build / 'build.json').read_text())
    baseline = Path(metadata['baseline'])
    diagnostic = args.candidate_rom or Path(metadata['diagnostic'])
    for variant, checkpoints, rom, sym in (
        ('baseline', args.baseline_checkpoints, baseline / 'pokecrystal.gbc', baseline / 'pokecrystal.sym'),
        ('candidate', args.checkpoints, diagnostic, diagnostic.with_suffix('.sym'))):
        output = args.output / variant
        output.mkdir(exist_ok=True)
        repo = Repository(ROOT, rom, sym)
        manifest = json.loads((checkpoints / 'provenance.json').read_text())
        if any(manifest[key] != value for key, value in repo.hashes.items()):
            raise ValueError(f'Checkpoints do not match {variant}')
        core = compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', output)
        configs.append(dict(variant=variant, core=str(core), rom=str(rom), sym=str(sym),
                            battery=str(checkpoints / 'fixture.sav'), checkpoints=str(checkpoints), output=str(output)))
    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(paired, [(configs, case, names) for case in suite]):
            rows.append(row)
            print(json.dumps(dict(case=row['case'], delta_ms=row['delta_ms'],
                preservation=row['candidate']['preservation'],
                failures=row['candidate']['restoration_failures'],
                follow_up=row['candidate']['follow_up']['issues'])), flush=True)
            (args.output / 'report.json').write_text(json.dumps(rows, indent=2) + '\n')
    failures = [row['case'] for row in rows if row['candidate']['restoration_failures']
                or row['candidate']['follow_up']['issues']
                or row['candidate']['preservation']['changed_outgoing_frames']
                or row['candidate']['preservation']['exposed_tile_replacements']
                or row['candidate']['preservation']['translation_issues']]
    print(json.dumps(dict(tested=len(rows), failed=failures)), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
