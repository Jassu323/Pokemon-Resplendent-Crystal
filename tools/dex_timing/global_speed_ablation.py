"""Private double-speed ablations; matching native checkpoints for every link."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

from .cold_listing import ROOT


def execute(item):
    output, disabled, jobs = item
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'workflow.log').open('w') as log:
        subprocess.run(['python3', 'tools/build_global_speed_prototype.py', '--output', str(output),
                        '--jobs', '4', '--disable', disabled], cwd=ROOT, stdout=log, stderr=log, check=True)
        subprocess.run(['python3', '-m', 'tools.dex_timing.performance', '--prepare',
                        '--rom', str(output / 'pokecrystal-global-double-speed.gbc'),
                        '--sym', str(output / 'pokecrystal-global-double-speed.sym'),
                        '--battery', str(ROOT / 'build/global-speed-20261004/full/measurements/private.sav'),
                        '--output', str(output / 'measurements'), '--species',
                        'chikorita', 'dusknoir', 'weavile', 'garchomp', 'eevee', 'tyrogue',
                        '--input-phases', '0', '17556', '35112', '52668', '--all-info-pages',
                        '--actions', 'description-info', 'moves-info', 'description-area', 'info-area',
                        'moves-area', 'info-area-return', 'listing', 'cycle', 'rapid',
                        'description-listing', 'moves-listing', 'info-description-listing', 'info-moves-listing',
                        '--jobs', str(jobs)], cwd=ROOT, stdout=log, stderr=log, check=True)
    return dict(disabled=disabled, output=str(output), complete=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--disable', nargs='+', default=['retained', 'admission', 'glyph', 'town', 'nests', 'queue', 'lookahead'])
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=7) as pool:
        for result in pool.map(execute, [(args.output.resolve() / name, name, 4) for name in args.disable]):
            print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
