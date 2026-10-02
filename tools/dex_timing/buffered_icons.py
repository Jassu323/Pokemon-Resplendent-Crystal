"""Production-only icon-buffer, continuous paging and return/reentry audit.

Uses matching cold-listing checkpoints and real joypad input. The observer
does not modify the ROM or emulated memory. Generated evidence stays in build/.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import Repository
from .cold_listing import Driver, ROOT, audit as audit_animation
from .description_ui import audit, audit_footprint, expected_types, settle


def render(snapshot):
    vram, pals = bytes.fromhex(snapshot['vram']), bytes.fromhex(snapshot['bg_pal'])
    sx, sy, wx, wy = snapshot['scroll']
    if sx != 5 or sy or wx < 167:
        raise ValueError('Unexpected Description viewport')
    picture = np.zeros((144, 160, 3), dtype=np.uint8)
    portrait = np.zeros((144, 160), dtype=bool)
    for y in range(144):
        for x in range(160):
            cell = 0x1800 + ((y + sy) // 8) * 32 + (x + sx) // 8
            tile, attr = vram[cell], vram[cell + 0x2000]
            portrait[y, x] = (attr & 7) == 1
            tx, ty = (x + sx) & 7, (y + sy) & 7
            if attr & 32:
                tx = 7 - tx
            if attr & 64:
                ty = 7 - ty
            at = 0x1000 + (tile if tile < 128 else tile - 256) * 16 + 2 * ty
            if attr & 8:
                at += 0x2000
            color = ((vram[at] >> (7 - tx)) & 1) | (((vram[at + 1] >> (7 - tx)) & 1) << 1)
            at = (attr & 7) * 8 + color * 2
            value = int.from_bytes(pals[at:at + 2], 'little')
            channels = [(value >> shift) & 31 for shift in (0, 5, 10)]
            picture[y, x] = [(v << 3) | (v >> 2) for v in channels]
    return picture, portrait


def audit_transition(folder, trace):
    phases = [e for e in trace if e['event'] == 'phase']
    start = next(e for e in phases if e['phase'] == 'trace_start')
    hidden = next(e for e in phases if e['phase'] == 'hidden')
    reveal = next(e for e in phases if e['phase'] == 'reveal')
    frames = [e for e in trace if e['event'] == 'frame']
    _, portrait = render(start)
    pictures = {e['display']: np.asarray(Image.open(folder / f'trace-{e["display"]:03}.ppm'))
                for e in frames}
    masked = [e for e in frames if hidden['t'] < e['t'] < reveal['t'] and
              np.all(pictures[e['display']][portrait] == 255)]
    issues = []
    if not masked:
        return dict(issues=['missing_masked_display'], masked_frames=0)
    old = next((e for e in reversed(frames) if e['t'] < masked[0]['t']), None)
    before = pictures[old['display']] if old else np.asarray(Image.open(folder / 'before.ppm'))
    expected_pals = bytearray.fromhex(start['bg_pal'])
    expected_pals[8:16] = bytes((255, 127)) * 4
    for frame in frames:
        picture = pictures[frame['display']]
        if masked[0]['t'] <= frame['t'] < reveal['t']:
            if not np.all(picture[portrait] == 255):
                issues.append(f'portrait_mask_{frame["display"]}')
            if not np.array_equal(picture[~portrait], before[~portrait]):
                issues.append(f'outgoing_shell_or_icons_{frame["display"]}')
            if bytes.fromhex(frame['bg_pal']) != expected_pals:
                issues.append(f'outgoing_palette_{frame["display"]}')
        if frame['black'] or frame['white']:
            issues.append(f'full_screen_flash_{frame["display"]}')
    incoming = next((e for e in frames if e['t'] > reveal['t']), None)
    if incoming:
        expected, _ = render(reveal)
        actual_footer, _ = render(incoming)
        expected[136:144, 3:11] = actual_footer[136:144, 3:11]
        if not np.array_equal(pictures[incoming['display']], expected):
            issues.append('incoming_reveal_pixels')
    else:
        issues.append('missing_incoming_display')
    if any(e['pal_blocked'] for e in trace if e['event'] == 'write' and e['address'] in (0xff69, 0xff6b)):
        issues.append('blocked_palette_write')
    if any(e['address'] == 0xff40 for e in trace if e['event'] == 'write'):
        issues.append('lcd_toggle')
    return dict(issues=sorted(set(issues)), masked_frames=len(masked))


def check_ui(driver, repo, name):
    ui = driver.command('ui')
    issues = audit(repo, ui) + audit_footprint(repo, name, ui)
    if ui['types'] != expected_types(repo, name):
        issues.append('wrong_species_types')
    if issues:
        raise RuntimeError(f'{name}: {issues}')
    tilemap = bytes.fromhex(ui['map'])
    return dict(footprint_tile=tilemap[21 + 18], type_tile=tilemap[7 * 21 + 9], issues=[])


def main():
    from .internal_transitions import BOOT, enter, names_in_order
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoints', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    provenance = json.loads((args.checkpoints / 'provenance.json').read_text())
    if any(provenance[k] != v for k, v in repo.hashes.items()):
        raise ValueError('Checkpoints do not match the current production link')
    args.output.mkdir(parents=True, exist_ok=True)
    names, assets = names_in_order(), {a.name: a for a in repo.load()}
    driver = Driver(args.checkpoints / 'cold-listing-core', args.checkpoints / 'input-copy.gbc',
                    BOOT, args.checkpoints / 'input-copy.sav', args.output / 'core.log')
    results = dict(provenance=repo.hashes, continuous=[], roundtrips=[], returns=[], footer=[])

    def page(source, target, key):
        driver.command('audit 1')
        driver.events.clear()
        changed = driver.run(('change_species', 'animation_miss', 'audio_miss'), 180, key)
        if changed['hit'] != 'change_species':
            raise RuntimeError(f'Paging failed: {changed}')
        incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
        if incoming['hit'] != 'selected' or incoming['selected_index'] != names.index(target):
            raise RuntimeError(f'Wrong incoming entry: {incoming}')
        final = settle(driver)
        animation = audit_animation(assets[target], changed, list(driver.events), final, cold=False)
        if animation['issues']:
            raise RuntimeError(f'{target}: {animation["issues"]}')
        driver.command('audit 0')
        return dict(source=source, target=target, ui=check_ui(driver, repo, target), animation=animation)

    def reenter(name):
        listing = driver.run(('listing',), 600, 'b')
        if listing['hit'] != 'listing' or listing['index'] != names.index(name):
            raise RuntimeError(f'Return failed: {listing}')
        driver.run(('end_loop',), 600)
        driver.run(('accept',), 600, 'a')
        incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
        if incoming['hit'] != 'selected' or incoming['selected_index'] != names.index(name):
            raise RuntimeError(f'Reentry failed: {incoming}')
        settle(driver)
        ui = check_ui(driver, repo, name)
        if ui['footprint_tile'] != 0xb1 or ui['type_tile'] != 0x64:
            raise RuntimeError('Listing reentry failed to restore icon set A')
        return dict(species=name, ui=ui)

    try:
        enter(driver, args.checkpoints, len(names) - 1)
        settle(driver)
        source = names[-1]
        for i, target in enumerate(names):
            row = page(source, target, 'down')
            if row['ui']['footprint_tile'] != (0x6c if i % 2 == 0 else 0xb1):
                raise RuntimeError('Continuous paging did not alternate icon buffers')
            results['continuous'].append(row)
            source = target
        results['returns'].append(reenter(source))
        for source in ('chikorita', 'bayleef', 'dusclops', 'metang', 'luxio', 'abomasnow',
                       'gabite', 'heracross', 'crawdaunt', 'gengar', 'zangoose', 'regigigas'):
            target = names[(names.index(source) + 1) % len(names)]
            enter(driver, args.checkpoints, names.index(source))
            settle(driver)
            for first, last, key in ((source, target, 'down'), (target, source, 'up'), (source, target, 'down')):
                results['roundtrips'].append(page(first, last, key))
            results['returns'].append(reenter(target))
            for expected in (1, 0):
                driver.run(frames=2, key='a')
                driver.run(frames=8)
                ui = driver.command('ui')
                if ui['page'] != expected:
                    raise RuntimeError('Description page toggle did not complete')
                results['footer'].append(dict(species=target, page=expected, ui=check_ui(driver, repo, target)))
            if source in ('chikorita', 'dusclops', 'metang', 'luxio', 'gengar', 'regigigas'):
                for name in (target, source):
                    if name == source:
                        page(target, source, 'up')
                    for _ in range(3):
                        driver.run(frames=2, key='right')
                        driver.run(frames=2)
                    area = driver.run(frames=30, key='a')
                    if area['state'] != 4:
                        raise RuntimeError('Area overlay did not open')
                    driver.run(frames=120)
                    driver.run(frames=2, key='b')
                    incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
                    if incoming['hit'] != 'selected' or incoming['state'] != 1:
                        raise RuntimeError('Area return did not reach Description')
                    settle(driver)
                    results['footer'].append(dict(species=name, area_return=True, ui=check_ui(driver, repo, name)))
            print(json.dumps(dict(source=source, issues=[])), flush=True)
    finally:
        driver.close()
    (args.output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({name: len(results[name]) for name in ('continuous', 'roundtrips', 'returns', 'footer')}))


if __name__ == '__main__':
    main()
