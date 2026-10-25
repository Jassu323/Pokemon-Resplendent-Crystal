"""Verify the retained persistence trial and assemble its qualification record."""
import argparse
import json
import os
from pathlib import Path
import unittest

from .assets import sha256
from .cold_listing import ROOT


def qualify(output):
    manifest = json.loads((output / 'moves-mode-manifest.json').read_text())
    digest = sha256((output / 'pokecrystal-dex-moves-persistence.gbc').read_bytes())
    if manifest['rom_sha256'] != digest:
        raise AssertionError('Review ROM changed after its build manifest')
    reports = {}
    for name in ('persistence-qualification.json', 'persistence-ui-qualification.json',
                 'persistence-visual-parity.json', 'moves-mode-qualification/summary.json',
                 'regression-modern/summary.json', 'regression-legacy/summary.json',
                 'integration/summary.json', 'modal-qualification/summary.json',
                 'search-qualification/summary.json', 'search-listing-returns/summary.json',
                 'search-default-empty/summary.json', 'mode-transitions/summary.json'):
        data = (output / name).read_bytes()
        record = json.loads(data)
        if record.get('failures') or record.get('issues'):
            raise AssertionError(f'Failed qualification: {name}')
        if record.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Wrong link qualified: {name}')
        if any(row['failures'] for row in record.get('summary', {}).values()):
            raise AssertionError(f'Failed regression: {name}')
        reports[name] = dict(sha256=sha256(data), summary={
            key: value for key, value in record.items()
            if key in ('cases', 'page_cases', 'interface_cases', 'interface_checks',
                       'transitions', 'helper_cases', 'snapshot_cases', 'cold_boot_cases',
                       'lifecycle_cases', 'interrupted_write_cases', 'interrupted_repair_cases',
                       'summary', 'failures', 'issues')})
    for style in ('modern', 'legacy'):
        config = json.loads((output / style / 'config.json').read_text())
        if config['hashes']['rom_sha256'] != digest:
            raise AssertionError('Regression checkpoints belong to another link')
    for path, expected in manifest['protected_inputs'].items():
        if sha256(Path(path).read_bytes()) != expected:
            raise AssertionError(f'Protected input changed: {path}')
    for name in ('MOVE_DISCOVERY_BUILD', 'DEX_MOVES_MODE_BUILD', 'DEX_OPTIONS_BUILD', 'DEX_SEARCH_BUILD'):
        os.environ[name] = str(output)
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'tools.test_move_discovery', 'tools.test_pokedex_moves_mode', 'tools.test_pokedex_moves',
        'tools.test_pokedex_sort', 'tools.test_pokedex_search_results'])
    host = unittest.TextTestRunner().run(suite)
    if not host.wasSuccessful():
        raise AssertionError('Final host tests failed')
    result = dict(rom_sha256=digest, review_seen=len(manifest['review_seen']),
                  save_sha256=sha256((output / 'pokecrystal-dex-moves-persistence.sav').read_bytes()),
                  host_tests=host.testsRun, reports=reports, rollback=manifest['rollback'],
                  production_unchanged=True, gameplay_hooks=False, egg_policy='at hatch', issues=[])
    (output / 'final-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'reports'}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use the private build directory')
    qualify(output)


if __name__ == '__main__':
    main()
