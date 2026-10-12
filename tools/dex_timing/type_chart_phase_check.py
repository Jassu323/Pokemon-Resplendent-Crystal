"""Separate native battle start-phase changes from Type display overhead."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from . import animation_reference as motion, global_speed as speed
from .assets import sha256
from .cold_listing import FRAME, ROOT
from tools.pokedex_info_assets import constants


def run(base, jobs, campaign=None):
    source = base / 'all-animations'
    configurations = json.loads((source / 'configurations.json').read_text())
    original = json.loads((source / 'native.json').read_text()) if campaign is None else json.loads(
        (campaign / 'acquisition-moves-regression.json').read_text())['results']
    original = [dict(r, variant={'baseline':'production','acquisition':'runtime'}.get(r['variant'],r['variant']))
                for r in original]
    by = {(r['variant'], r['move'], r['side'], r['quarter']): r for r in original}
    selected = []
    for row in original:
        if row['variant'] != 'runtime' or row['issues']:
            continue
        old = by['production', row['move'], row['side'], row['quarter']]
        if row['requested_animations'][0]['elapsed_t'] != old['requested_animations'][0]['elapsed_t']:
            selected.append((row['move'], row['side'], row['quarter']))
    selected = sorted(set(selected + [('SWIFT', 'player', 0), ('WATERFALL', 'foe', 0)]))
    target = base / ('chart-phase-check' if campaign is None else 'chart-phase-check-100')
    target.mkdir(exist_ok=True)
    diagnostic = base / 'diagnostic-original-chart/candidate'
    production = next(c for c in configurations if c['variant'] == 'production')
    assert (diagnostic / 'data/types/type_matchups.asm').read_text().split('TypeMatchupsEnd::')[0] == (
        Path(production['root']) / 'data/types/type_matchups.asm').read_text()
    runtime_sha = next(c['rom_sha256'] for c in configurations if c['variant']=='runtime')
    assert sha256((diagnostic / 'pokecrystal.gbc').read_bytes()) != runtime_sha, 'Rebuild the chart ablation first'
    cfg = dict(production, variant='original-chart', root=str(diagnostic),
               rom=str(diagnostic / 'pokecrystal.gbc'), sym=str(diagnostic / 'pokecrystal.sym'))
    motion.OUTPUT = target
    motion.configuration = lambda _: cfg
    cfg = motion.prepare('original-chart', sorted({move for move, side, quarter in selected}),
                         'chart-ablation', coherent=True)
    cfg.update(output_root=str(target / 'native'), capture_images=False, post_menu_frames=32)
    values = constants(ROOT / 'constants/move_constants.asm')
    tasks = [(cfg, move, values[move], side, quarter) for move, side, quarter in selected]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(speed.move_job, tasks))
    comparisons = []
    for row in rows:
        old = by['production', row['move'], row['side'], row['quarter']]
        runtime = by['runtime', row['move'], row['side'], row['quarter']]
        before = old['requested_animations'][0]['elapsed_t']
        comparisons.append(dict(move=row['move'], side=row['side'], quarter=row['quarter'], issues=row['issues'],
            changed_chart_delta_t=runtime['requested_animations'][0]['elapsed_t']-before,
            original_chart_delta_t=row['requested_animations'][0]['elapsed_t']-before,
            changed_chart_delta_frames=(runtime['requested_animations'][0]['elapsed_t']-before)/FRAME))
    result = dict(diagnostic_rom_sha256=sha256((diagnostic / 'pokecrystal.gbc').read_bytes()),
                  production_rom_sha256=production['rom_sha256'],
                  candidate_rom_sha256=next(c['rom_sha256'] for c in configurations if c['variant']=='runtime'),
                  candidate_rom_sha256s={c['variant']:c['rom_sha256'] for c in configurations if c['variant']!='production'},
                  cases=len(rows), comparisons=comparisons,
                  all_original_chart_durations_exact=all(not r['issues'] and r['original_chart_delta_t']==0
                                                         for r in comparisons))
    (target / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
    return int(not result['all_original_chart_durations_exact'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--campaign', type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.base.resolve(), args.jobs, args.campaign.resolve() if args.campaign else None))
