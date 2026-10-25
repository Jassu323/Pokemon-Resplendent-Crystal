"""Run adjacent Dex suites and qualify the isolated Unown repair."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image

from . import moves_search
from .assets import read_symbols, sha256
from .unown_comparison import battery
from .unown_regression import case, OUTER_CELLS, PORTRAIT_CELLS
from build_dex_unown_prototype import resources, ROOT, STEM, BASE_STEM


def remaining_dex(output):
    commands = [
        ('moves_search_dex_regression', 'selected', '--output', str(output), '--jobs', '6'),
        ('search_qualification', '--source', str(output / 'dex-regression'), '--jobs', '6'),
        ('search_qualification', '--source', str(output / 'dex-regression'), '--jobs', '6', '--returns'),
        ('search_qualification', '--source', str(output / 'dex-regression'), '--jobs', '6', '--defaults'),
        ('mode_transitions', '--output', str(output / 'dex-regression'), '--jobs', '6',
         '--indices', '0,8,255,372', '--phases', '4'),
        ('mode_transitions', '--output', str(output / 'dex-regression'), '--jobs', '6',
         '--indices', '0,8', '--phases', '2', '--prior-view', 'info', '--tag', 'unown-prior-info'),
        ('mode_transitions', '--output', str(output / 'dex-regression'), '--jobs', '6',
         '--indices', '0,8', '--phases', '2', '--prior-view', 'moves', '--tag', 'unown-prior-moves'),
        ('moves_search_dex_regression', 'qualify', '--output', str(output)),
    ]
    for module, *arguments in commands:
        print('Running', module, *arguments, flush=True)
        subprocess.run([sys.executable, '-m', 'tools.dex_timing.' + module, *arguments],
                       cwd=ROOT, check=True)


def moves(output):
    for action, function in (
        ('filter', moves_search.filter_tests), ('ui', moves_search.ui_tests),
        ('visual', moves_search.visual_tests), ('navigation', moves_search.navigation_tests),
        ('transitions', moves_search.transition_tests), ('surrounding', moves_search.surrounding_tests),
        ('polish', moves_search.form_polish_tests), ('cursor', moves_search.naming_cursor_tests),
    ):
        result = function(output)
        print(json.dumps(dict(action=action, result=result)), flush=True)
        if result.get('issues') or result.get('failures'):
            raise AssertionError(f'Moves suite failed: {action}')


def compare_backdrop(output, base, original_base, black_panels=False):
    vanilla = original_base / 'unown-investigation/vanilla/1-forms-0.png'
    with Image.open(vanilla) as image:
        reference = image.convert('RGB').tobytes()
    outer = {(y * 8 + py) * 160 + x * 8 + px for x, y in OUTER_CELLS
             for py in range(8) for px in range(8)}
    portrait = {(y * 8 + py) * 160 + x * 8 + px for x, y in PORTRAIT_CELLS
                for py in range(8) for px in range(8)}
    records = []
    for name, form in (('single-01', 0), ('ascending-26', 0), ('ascending-26', 25)):
        for presentation in (0, 1):
            relative = Path('unown-tests') / f'{name}-p{presentation}-q0' / f'form-{form:02}.png'
            with Image.open(base / relative) as image:
                before = image.convert('RGB').tobytes()
            with Image.open(output / relative) as image:
                after = image.convert('RGB').tobytes()
            if black_panels:
                unchanged_colors = {bytes((255, 255, 255)), bytes((214, 82, 49)), bytes(3)}
                inside_unchanged = all(after[n * 3:n * 3 + 3] == (
                    before[n * 3:n * 3 + 3] if before[n * 3:n * 3 + 3] in unchanged_colors else bytes(3))
                    for n in range(160 * 144) if n not in outer and n not in portrait)
            else:
                inside_unchanged = all(after[n * 3:n * 3 + 3] == before[n * 3:n * 3 + 3]
                                      for n in range(160 * 144) if n not in outer)
            outside_matches = all(after[n * 3:n * 3 + 3] == reference[n * 3:n * 3 + 3] for n in outer)
            if not inside_unchanged or not outside_matches:
                raise AssertionError(f'Unexpected backdrop/panel pixels: {relative}')
            records.append(dict(path=str(relative), inside_unchanged=inside_unchanged if not black_panels else None,
                                inside_matches_requested_conversion=inside_unchanged if black_panels else None,
                                inside_pixels=160 * 144 - len(outer) - (len(portrait) if black_panels else 0),
                                black_panel_conversion=black_panels, outside_matches_vanilla=outside_matches,
                                outside_pixels=len(outer)))
    result = dict(cases=len(records), failures=0, vanilla_reference=str(vanilla),
                  palette='RGB 26,10,6; raw native RGB 214,82,49', results=records)
    (output / 'unown-backdrop-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def qualify(output):
    manifest = json.loads((output / 'unown-manifest.json').read_text())
    base = Path(manifest['base'])
    base_stem = manifest.get('base_stem', BASE_STEM)
    red_background = manifest.get('red_background', False)
    black_panels = manifest.get('black_panels', False)
    digest = sha256((output / f'{STEM}.gbc').read_bytes())
    if digest != manifest['rom_sha256']:
        raise AssertionError('Candidate ROM changed')
    owner = 'engine/gfx/cgb_layouts.asm' if black_panels else 'engine/pokedex/pokedex.asm'
    begin, end = ('_CGB_PokedexUnownMode:', '_CGB_SlotMachine:') if black_panels else (
        'Pokedex_DrawUnownModeBG:', 'UnownModeLetterAndCursorCoords:')
    before = (base / 'candidate' / owner).read_text()
    after = (output / 'candidate' / owner).read_text()
    for content in (before.split(begin, 1)[0], before.split(end, 1)[1]):
        if content not in after:
            raise AssertionError('Changes extend outside the Unown drawing routine')
    for name in manifest['protected_inputs']:
        if sha256(Path(name).read_bytes()) != manifest['protected_inputs'][name]:
            raise AssertionError(f'Production/rollback file changed: {name}')
    original = json.loads(Path(manifest.get('production_manifest', base / 'no-warming-manifest.json')).read_text())
    protected = 0
    for name, expected in original['protected_inputs'].items():
        if Path(name).relative_to(ROOT).as_posix() in (
                'docs/index.md', 'docs/pokedex_selected_bug_backlog.md'):
            continue
        if sha256(Path(name).read_bytes()) != expected:
            raise AssertionError(f'Production source changed: {name}')
        protected += 1
    for path in (output / 'candidate').rglob('*.asm'):
        name = path.relative_to(output / 'candidate')
        if str(name) != owner and path.read_bytes() != (base / 'candidate' / name).read_bytes():
            raise AssertionError(f'Another assembly owner changed: {name}')
    for path in (base / 'candidate/gfx').rglob('*'):
        if path.is_file() and path.read_bytes() != (output / 'candidate/gfx' / path.relative_to(base / 'candidate/gfx')).read_bytes():
            raise AssertionError(f'Artwork changed: {path}')
    previous = read_symbols(base / f'{base_stem}.sym')
    current = read_symbols(output / f'{STEM}.sym')
    for name, pair in previous.items():
        if name.startswith(('s', 'w', 'h')) and pair[1] >= 0xa000 and name in current and pair != current[name]:
            raise AssertionError(f'Memory address moved: {name}')
    delta = {name: resources(output / f'{STEM}.map')[name] - value
             for name, value in resources(base / f'{base_stem}.map').items()}
    if delta != dict(ROM0=0, ROMX=8 if black_panels else 15 if red_background else 23,
                     SRAM=0, WRAM0=0, WRAMX=0, HRAM=0):
        raise AssertionError(f'Unexpected resource change: {delta}')
    counts = {
        'unown-tests/summary.json': 136,
        'dex-regression/summary.json': 4479,
        'dex-regression/unown-prior-info/summary.json': 8,
        'dex-regression/unown-prior-moves/summary.json': 8,
        'search-tests/filter.json': 1692,
        'search-tests/ui.json': 10,
        'search-tests/visual/summary.json': 1406,
        'search-tests/navigation/summary.json': 2686,
        'search-tests/transitions/summary.json': 11,
        'search-tests/surrounding/summary.json': 2,
        'search-tests/form-polish/summary.json': 1284,
        'search-tests/naming-cursor/summary.json': 3840,
    }
    reports = {}
    for name, count in counts.items():
        path = output / name
        data = json.loads(path.read_text())
        if data.get('cases') != count or data.get('failures') or data.get('issues'):
            raise AssertionError(f'Incomplete or failing report: {name}')
        if data.get('rom_sha256', digest) != digest:
            raise AssertionError(f'Wrong ROM in report: {name}')
        reports[name] = dict(cases=count, sha256=sha256(path.read_bytes()))
    unown = json.loads((output / 'unown-tests/summary.json').read_text())
    if unown['draw_unit_cases'] != 126 or len(unown['negative_controls']) != (
            4 if black_panels else 3 if red_background else 2) or not all(
            row['original_failure_detected'] for row in unown['negative_controls']):
        raise AssertionError('Unown content oracle is incomplete or misses the original faults')
    if red_background and unown['background_cells'] != 298620:
        raise AssertionError('Outer-background pixel checks are incomplete')
    if black_panels and (unown['portrait_palette_cells'] != 2212 * 49 or not unown['black_panel_cells']):
        raise AssertionError('Black panel/portrait pixel checks are incomplete')
    comparison = compare_backdrop(output, base, Path(manifest['original_defect_base']), black_panels) if red_background else None
    if (output / f'{STEM}.sav').read_bytes() != (base / f'{base_stem}.sav').read_bytes():
        raise AssertionError('Ordinary review save changed')
    review = output / 'all-unown-review'
    review.mkdir(exist_ok=True)
    shutil.copy2(output / f'{STEM}.gbc', review / f'{STEM}.gbc')
    battery(output / f'{STEM}.sav', current, review / f'{STEM}.sav', 26, True)
    confirmation = output / 'review-confirmation'
    confirmation.mkdir(exist_ok=True)
    config = json.loads((output / 'dex-regression/modern/config.json').read_text())
    config['battery'] = str(review / f'{STEM}.sav')
    config['red_background'] = red_background
    config['black_panels'] = black_panels
    review_result = case((config, str(output / 'candidate'), str(confirmation),
                          'all-26-review', list(range(1, 27)), 0, 0))
    if review_result['issues'] or (confirmation / 'all-26-review-p0-q0/input.sav').read_bytes() != (
            review / f'{STEM}.sav').read_bytes():
        raise AssertionError('Published all-Unown review battery failed native confirmation')
    result = dict(rom_sha256=digest, rollback_rom_sha256=manifest['rollback_rom_sha256'],
                  delta=delta, protected_inputs=protected, reports=reports,
                  unown_cases=unown['cases'], form_selections=unown['form_selections'],
                  overlay_cells=unown['overlay_cells'], draw_unit_cases=unown['draw_unit_cases'],
                  red_background=red_background, background_cells=unown.get('background_cells', 0),
                  black_panels=black_panels, black_panel_cells=unown.get('black_panel_cells', 0),
                  portrait_palette_cells=unown.get('portrait_palette_cells', 0),
                  backdrop_comparison=comparison,
                  original_defects_detected=True, production_unchanged=True, rollback_unchanged=True,
                  assets_unchanged=True, memory_addresses_unchanged=True,
                  all_unown_review_native_confirmed=True, issues=[])
    (output / 'unown-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('dex', 'moves', 'qualify'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    {'dex': remaining_dex, 'moves': moves, 'qualify': qualify}[args.action](args.output.resolve())
