"""Rendered transition frames for diagnosing latency tradeoffs, never live saves."""
import argparse
import json
from pathlib import Path

from .assets import Repository
from .cold_listing import Driver, move, predecessor, ROOT
from .description_ui import settle
from .info_ui import BOOT, ready
from .performance import core, view


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', default='chikorita')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    binary = core(repo, args.output)
    index = config['names'].index(args.species)
    for action in ('species', 'listing'):
        driver = Driver(binary, config['rom'], BOOT, config['battery'], args.output / (action + '.log'))
        try:
            prior, direction = predecessor(index)
            driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
            driver.command('rawcolor')
            move(driver, direction, index)
            driver.run(('accept',), key='a')
            driver.run(('selected',), frames=600)
            settle(driver)
            view(driver, repo, args.species, 1)
            driver.command(f'image {args.output / (action + "-000.ppm")}')
            driver.command(f'perfimages {args.output / action}')
            driver.command('perf 1')
            driver.run(('leave' if action == 'listing' else 'change_species',),
                       key='b' if action == 'listing' else 'down')
            driver.run(('listing' if action == 'listing' else 'selected',), frames=600)
            if action != 'listing':
                ready(driver, 0)
            driver.run(frames=3)
        finally:
            driver.close()


if __name__ == '__main__':
    main()
