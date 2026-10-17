"""Build and inspect every Selected footprint without modifying production."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageChops, ImageDraw

from .assets import Repository, offset, sha256
from .cold_listing import ROOT, Driver, move, predecessor, audit
from .description_ui import audit as shell_audit, settle, settle_description_text, audit_type_sprites
from .description_paging import description_pages
from .info_ui import BOOT, press
from . import performance, legacy_listing
from tools.pokedex_footprint_assets import import_assets
from tools.build_dex_unown_prototype import resources

DEFAULT = ROOT / 'build/dex-footprints-20261016'
SOURCES = ROOT / 'build/footprint-source-review-20261016/manifest.json'
SEED = ROOT / 'build/interactive-registration-review-20261016/regular-dex-comparison/pokecrystal-interactive-registration.sav'
TABLES = ('dex-info-assets', 'dex-moves-assets', 'dex-sort-assets', 'dex-area-assets', 'dex-moves-mode-assets')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def protected():
    paths = [*(ROOT / f'pokecrystal.{ext}' for ext in ('gbc', 'sym', 'map')),
             *ROOT.glob('*.sav'), Path('/Applications/SameBoy/Games/pokecrystal.sav')]
    return {str(p): sha256(p.read_bytes()) for p in paths if p.is_file()}


def verify_protected(output):
    record = json.loads((output / 'build.json').read_text())
    for name, expected in record['protected'].items():
        if sha256(Path(name).read_bytes()) != expected:
            raise AssertionError('Protected production input changed: ' + name)


def build(output, jobs):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh private build folder')
    output.mkdir(parents=True)
    saved = protected()
    candidate = output / 'candidate'
    candidate.mkdir()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, tracked):
        if Path(name).parts[0] in ('gfx', 'tools', 'docs', '.github'):
            continue
        source, target = ROOT / name, candidate / name
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in ('gfx', 'tools'):
        shutil.copytree(ROOT / name, candidate / name,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.o', '*.d'))
    for name in TABLES:
        shutil.copytree(ROOT / 'build' / name, candidate / 'build' / name)
    imported = import_assets(SOURCES, candidate)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', f'-j{jobs}', 'pokecrystal.gbc'], cwd=candidate,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    before = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    after = Repository(candidate, candidate / 'pokecrystal.gbc', candidate / 'pokecrystal.sym')
    assert before.symbols == after.symbols, 'Asset-only change moved symbols'
    delta = {k: resources(candidate / 'pokecrystal.map')[k] - v
             for k, v in resources(ROOT / 'pokecrystal.map').items()}
    assert not any(delta.values()), delta
    start = offset(before.symbols['Footprints'])
    allowed = set(range(start + 251 * 32, start + 373 * 32)) | {0x14e, 0x14f}
    changed = [i for i, (a, b) in enumerate(zip(before.rom, after.rom)) if a != b]
    assert all(i in allowed for i in changed), 'Non-footprint executable bytes changed'
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(candidate / f'pokecrystal.{ext}', output / f'pokecrystal-dex-footprints.{ext}')
    write(output / 'build.json', dict(protected=saved, candidate_sha256=sha256(after.rom),
        baseline_sha256=sha256(before.rom), changed_bytes=len(changed), delta=delta,
        source_manifest=str(SOURCES), imported=imported['species'], blank=imported['blank'],
        executable_and_vanilla_footprints_unchanged=True, symbol_addresses_unchanged=True))
    verify_protected(output)
    print(json.dumps(dict(built=str(output), delta=delta, changed_bytes=len(changed))), flush=True)


def qualify(output):
    verify_protected(output)
    host_record = json.loads((output/'host/campaign-logs/host.json').read_text())
    assert host_record['cases'] == 87 and not any(host_record[k] for k in ('failures','errors','skipped'))
    native = json.loads((output/'native-summary.json').read_text())
    assert not native['smoke'] and native['failures'] == 0
    assert len(native['suites']) == 4 and all(r['species'] == 373 and r['screens'] == 2984 for r in native['suites'])
    comparisons, clocks = [], []
    for style in ('modern', 'legacy'):
        before = json.loads((output/f'checks/production/{style}/summary.json').read_text())
        after = json.loads((output/f'checks/candidate/{style}/summary.json').read_text())
        for old, new in zip(before['results'], after['results']):
            assert old['species'] == new['species'] and len(old['screens']) == len(new['screens']) == 8
            for original, candidate in zip(old['screens'], new['screens']):
                assert original['label'] == candidate['label'] and original['box'] == candidate['box']
                with Image.open(original['image']) as a, Image.open(candidate['image']) as b:
                    difference = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
                    difference.paste((0, 0, 0), original['box'])
                    if difference.getbbox():
                        comparisons.append(dict(style=style, species=new['species'],
                            operation=candidate['label'], unexpected_box=difference.getbbox()))
                clocks.append(candidate['t'] - original['t'])
    assert not comparisons, comparisons[:10]
    assert not any(clocks), 'Matched native observation times changed'

    media = output/'review'
    media.mkdir()
    config = json.loads((output/'checks/candidate/modern/config.json').read_text())
    names = config['names']
    paths = [output/f'checks/candidate/modern/screens/{i:03}-{name}/description-1.png'
             for i,name in enumerate(names)]
    for page in range(6):
        sheet = Image.new('RGB', (8*160, 32+8*162), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        draw.text((8,8), f'Prototype Selected screens {page*64+1}-{min(373,(page+1)*64)}', fill='black')
        for slot in range(64):
            i = page*64+slot
            if i >= 373:
                break
            x,y = slot%8*160, 32+slot//8*162
            draw.text((x+2,y), names[i], fill='black')
            with Image.open(paths[i]) as frame:
                sheet.paste(frame, (x,y+16))
        sheet.save(media/f'all-selected-{page+1}.png')
    for page in range(4):
        sheet = Image.new('RGB',(8*136,32+12*88),'#eeeeee')
        draw = ImageDraw.Draw(sheet)
        draw.text((8,8), f'Actual in-game footprints {page*96+1}-{min(373,(page+1)*96)}; 4x', fill='black')
        for slot in range(96):
            i = page*96+slot
            if i >= 373:
                break
            x,y = slot%8*136, 32+slot//8*88
            draw.text((x+2,y), names[i], fill='black')
            with Image.open(paths[i]) as frame:
                sheet.paste(frame.crop((141,8,157,24)).resize((64,64),Image.Resampling.NEAREST),(x+2,y+16))
        sheet.save(media/f'all-footprints-{page+1}.png')
    selected = ('treecko','gallade','magnezone','porygonz','regigigas','chikorita')
    comparison = Image.new('RGB',(160*4,32+len(selected)*310),'#eeeeee')
    draw = ImageDraw.Draw(comparison)
    draw.text((8,8),'Production (left) / footprint prototype (right), 2x native pixels',fill='black')
    for row,name in enumerate(selected):
        i = names.index(name)
        draw.text((8,32+row*310), name, fill='black')
        for column,link in enumerate(('production','candidate')):
            with Image.open(output/f'checks/{link}/modern/screens/{i:03}-{name}/description-1.png') as frame:
                comparison.paste(frame.resize((320,288),Image.Resampling.NEAREST),(column*320,50+row*310))
    comparison.save(media/'production-vs-prototype.png')
    shutil.copy2(output/'checks/candidate/modern/private.sav',output/'pokecrystal-dex-footprints.sav')
    result = dict(qualified=True, candidate_sha256=sha256((output/'pokecrystal-dex-footprints.gbc').read_bytes()),
        candidate_species=373, presentations=2, candidate_screen_checks=5968,
        production_screen_controls=5968, matched_comparisons=len(clocks),
        unexpected_pixel_changes=comparisons, observation_timing_delta_ms=0,
        observation_timing_delta_display_frames=0, playback_sequences_per_link=2238,
        current_host_cases=87,
        source_and_linked_masks_checked_per_link=373, protected_inputs_unchanged=True,
        qualification='Focused footprint/Selected suite, not a new full battle/Tower campaign',
        manual_review='User review pending; automated physical-pixel and native playback checks pass')
    write(output/'qualification.json',result)
    print(json.dumps(result,indent=2),flush=True)


@lru_cache(maxsize=8)
def context(root, rom, sym):
    if not SOURCES.is_file():
        from .regression_fixtures import require
        require(SOURCES.relative_to(ROOT))
    repo = Repository(Path(root), Path(rom), Path(sym))
    assets = {a.name: a for a in repo.load()}
    table = re.findall(r'INCBIN "([^"]+[.]1bpp)"', (repo.root / 'gfx/footprints.asm').read_text())
    constants = re.findall(r'^\s*const\s+(\w+)', (repo.root / 'constants/pokemon_constants.asm').read_text(), re.M)[:373]
    names = [{'UNOWN': 'unown_a', 'PORYGON_Z': 'porygonz'}.get(n, n.lower()) for n in constants]
    originals = json.loads(SOURCES.read_text())
    sources = {r['species'].replace('porygon-z', 'porygonz'): r for r in originals['records']}
    masks = {}
    for index, name in enumerate(names):
        if name in sources and repo.root != ROOT:
            record = sources[name]
            source = SOURCES.parent / record['file']
            assert sha256(source.read_bytes()) == record['sha256']
            with Image.open(source) as image:
                image = image.convert('RGB')
                mask = [image.getpixel((x, y)) != (255, 255, 255) for y in range(16) for x in range(16)]
        else:
            with Image.open((repo.root / table[index]).with_suffix('.png')) as image:
                image = image.convert('RGB')
                mask = [image.getpixel((x, y)) == (255, 255, 255) for y in range(16) for x in range(16)]
        # Independent row-major tile encoder; renderer color 3 is background.
        encoded = bytes(sum((not mask[(ty+y)*16+tx+x]) << (7-x) for x in range(8))
                        for ty in (0, 8) for tx in (0, 8) for y in range(8))
        at = offset(repo.symbols['Footprints']) + index * 32
        assert repo.rom[at:at+32] == encoded, 'Source/linked footprint mismatch: ' + name
        assert (repo.root / table[index]).read_bytes() == encoded, name
        masks[name] = (mask, encoded)
    return repo, assets, masks


def pixel_issues(image, mask, x, y):
    return sum(image.getpixel((x+col, y+row)) != ((255, 255, 255) if mask[row*16+col] else (41, 41, 41))
               for row in range(16) for col in range(16))


def capture(driver, repo, masks, name, label, folder):
    state = driver.run(('animation_miss', 'audio_miss'), frames=2)
    if state['hit']:
        raise AssertionError('Playback miss before screenshot')
    ui = driver.command('ui')
    mask, encoded = masks[name]
    issues = audit_type_sprites(repo, ui)
    if bytes.fromhex(ui['footprint_gfx']) != bytes(v for b in encoded for v in (b, b)):
        issues.append('wrong_hardware_footprint')
    cells = (21+18, 21+19, 42+18, 42+19)
    tiles, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    if [tiles[i] for i in cells] not in ([0xb1, 0xb2, 0xb3, 0xb4], [0x6c, 0x6d, 0x6e, 0x6f]):
        issues.append('footprint_tile_order')
    if any(attrs[i] != 10 for i in cells):
        issues.append('footprint_attributes')
    if ui['view'] == 0:
        issues += shell_audit(repo, ui)
    ppm = folder / (label + '.ppm')
    driver.command(f'image {ppm}')
    with Image.open(ppm) as source:
        frame = source.convert('RGB')
    x, y = 144 - ui['scx'], 8 - ui['scy']
    if not (0 <= x <= 144 and 0 <= y <= 128):
        raise AssertionError('Footprint unexpectedly scrolled outside screen')
    bad = pixel_issues(frame, mask, x, y)
    if bad:
        issues.append('visible_footprint_pixels:' + str(bad))
    png = ppm.with_suffix('.png')
    frame.save(png)
    ppm.unlink()
    return dict(label=label, species=name, view=ui['view'], buffer=tiles[cells[0]],
        box=[x, y, x+16, y+16], image=str(png), issues=issues,
        t=driver.command('peek')['t'], foreground_pixels=sum(mask))


def case(task):
    config, index = task
    repo, assets, masks = context(config['root'], config['rom'], config['sym'])
    name = config['names'][index]
    folder = Path(config['output']) / 'screens' / f'{index:03}-{name}'
    folder.mkdir(parents=True, exist_ok=False)
    driver = Driver(config['core'], config['rom'], BOOT, config['battery'], folder / 'native.log')
    result = dict(species=name, index=index, screens=[], playback=[], issues=[])
    try:
        prior, direction = predecessor(index) if config['style'] == 'modern' else ((index-1) % len(config['names']), 'down')
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver, direction, index)
        driver.events.clear()
        driver.command('audit 1')
        accepted = driver.run(('accept',), key='a')
        final = settle(driver)
        result['playback'].append(audit(assets[name], accepted, driver.events, final, expected_double_speed=1))
        def snap(current, label):
            result['screens'].append(capture(driver, repo, masks, current, label, folder))
        snap(name, 'description-1')
        press(driver, 'a')
        settle_description_text(driver, description_pages(repo, name)[1])
        snap(name, 'description-2')
        performance.view(driver, repo, name, 1)
        snap(name, 'info')
        performance.view(driver, repo, name, 2)
        snap(name, 'moves')
        performance.view(driver, repo, name, 0)
        snap(name, 'description-return')
        target = index+1 if index+1 < len(config['names']) else index-1
        for destination, key, label in ((target, 'down' if target > index else 'up', 'internal-next'),
                                        (index, 'up' if target > index else 'down', 'internal-back')):
            driver.events.clear()
            accepted = driver.run(('change_species', 'animation_miss', 'audio_miss'), key=key)
            if accepted['hit'] != 'change_species':
                raise AssertionError('Internal paging not accepted')
            final = settle(driver)
            current = config['names'][destination]
            if final['selected_index'] != destination:
                raise AssertionError('Wrong internal-paging destination')
            result['playback'].append(audit(assets[current], accepted, driver.events, final,
                                           cold=False, expected_double_speed=1))
            snap(current, label)
        left = driver.run(('leave', 'animation_miss', 'audio_miss'), key='b')
        if left['hit'] != 'leave':
            raise AssertionError('Selected B-return not accepted')
        returned = driver.run(('listing',), frames=600)
        if returned['hit'] != 'listing' or returned['index'] != index:
            raise AssertionError('Wrong return selection')
        driver.run(frames=2)
        driver.run(('accept',), key='a')
        settle(driver)
        snap(name, 'reentry')
        result['issues'] += [s for s in result['screens'] if s['issues']]
        result['issues'] += [p for p in result['playback'] if p['issues']]
    except Exception as error:
        result['issues'].append(dict(error=str(error)))
        driver.evidence(folder / 'failure')
    finally:
        driver.close()
    write(folder / 'result.json', result)
    return result


def prepare(output):
    verify_protected(output)
    for link, root, rom, sym in (('production', ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym'),
                               ('candidate', output/'candidate', output/'pokecrystal-dex-footprints.gbc', output/'pokecrystal-dex-footprints.sym')):
        target = output / 'checks' / link
        modern = performance.prepare(rom, sym, SEED, target/'modern', root=root)
        modern['style'] = 'modern'
        write(target/'modern/config.json', modern)
        legacy = legacy_listing.prepare_legacy(target/'legacy', modern)
        legacy['style'] = 'legacy'
        write(target/'legacy/config.json', legacy)


def host(output):
    from .type_full_regression import host as current_host
    target = output / 'host'
    (target / 'campaign-logs').mkdir(parents=True)
    (target / 'candidate').symlink_to(output / 'candidate', target_is_directory=True)
    (target / 'baseline').mkdir()
    # The numeric-copy test measures +672 cycles against its pre-relocation
    # reference, not against today's already-banked production layout.
    reference = ROOT / 'build/interactive-registration-fixed-full-20261016/baseline-source'
    (target / 'baseline/candidate').symlink_to(reference, target_is_directory=True)
    assert current_host(target) == 0
    record = json.loads((target / 'campaign-logs/host.json').read_text())
    assert record['cases'] == 87 and not record['skipped'] and not record['errors'] and not record['failures']


def run(output, jobs, limit=None):
    rows = []
    for link in ('production', 'candidate'):
        for style in ('modern', 'legacy'):
            target = output / 'checks' / link / style
            config = json.loads((target/'config.json').read_text())
            indices = list(range(373))
            if limit:
                config['output'] = str(target / 'smoke')
                indices = sorted(set(list(range(limit)) + [config['names'].index(n)
                    for n in ('treecko', 'gallade', 'magnezone', 'porygonz')]))
            with ProcessPoolExecutor(max_workers=jobs) as pool:
                cases = list(pool.map(case, [(config, i) for i in indices]))
            summary = dict(link=link, style=style, species=len(cases),
                screens=sum(len(c['screens']) for c in cases),
                failures=sum(bool(c['issues']) for c in cases), results=cases)
            write(target/('smoke-summary.json' if limit else 'summary.json'), summary)
            print(json.dumps({k:v for k,v in summary.items() if k != 'results'}), flush=True)
            rows.append(summary)
    write(output/('native-smoke-summary.json' if limit else 'native-summary.json'), dict(suites=[{k:v for k,v in r.items() if k != 'results'} for r in rows],
        failures=sum(r['failures'] for r in rows), smoke=bool(limit)))
    verify_protected(output)
    if any(r['failures'] for r in rows):
        raise AssertionError('Native footprint review has failures; inspect retained results')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'prepare', 'run', 'qualify', 'host'))
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.action == 'build':
        build(args.output.resolve(), args.jobs)
    elif args.action == 'prepare':
        prepare(args.output.resolve())
    elif args.action == 'qualify':
        qualify(args.output.resolve())
    elif args.action == 'host':
        host(args.output.resolve())
    else:
        run(args.output.resolve(), args.jobs, args.limit)
