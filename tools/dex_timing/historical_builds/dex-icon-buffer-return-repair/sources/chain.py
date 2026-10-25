"""Private continuous paging, buffer alternation and return/re-entry checks."""
import json
from pathlib import Path
import subprocess

from run import (OUT, ORIGIN, CHECKPOINTS, BOOT, ROOT, initialize, normalize_buffered_ui,
                 audit_footprint, audit_ui, settle, cold, transitions, sha256)
import run


def protected():
    return dict(status=subprocess.check_output(['git', 'status', '--short'], text=True),
                diff=sha256(subprocess.check_output(['git', 'diff', '--binary'])),
                rom=sha256((CHECKPOINTS / 'input-copy.gbc').read_bytes()),
                battery=sha256((CHECKPOINTS / 'input-copy.sav').read_bytes()),
                symbols=sha256((ROOT / 'pokecrystal.sym').read_bytes()),
                root_rom_exists=(ROOT / 'pokecrystal.gbc').exists())


def snapshot(driver, label):
    prefix = OUT / 'chain' / label
    driver.command(f'restoretrace {prefix} 0')
    driver.command('restorestop')
    rows = [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]
    return rows[0]


def check_ui(driver, config, name, label):
    state = snapshot(driver, label)
    ui = driver.command('ui')
    foot = bytes.fromhex(ui['map'])[21 + 18]
    raw = dict(ui)
    normalize_buffered_ui(ui, bytes.fromhex(state['vram']))
    issues = audit_ui(config['repo'], ui) + audit_footprint(config['repo'], name, state)
    assert not issues, (label, issues)
    return dict(footprint_tile=foot, type_tile=bytes.fromhex(raw['map'])[7 * 21 + 9], issues=issues)


def page(driver, config, source, target, key, label):
    driver.command('audit 1')
    driver.events.clear()
    changed = driver.run(('change_species', 'animation_miss', 'audio_miss'), 180, key)
    assert changed['hit'] == 'change_species', changed
    incoming = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
    assert incoming['hit'] == 'selected' and incoming['selected_index'] == transitions.names_in_order().index(target), incoming
    final = settle(driver)
    animation = cold.audit(config['assets'][target], changed, list(driver.events), final, cold=False)
    assert not animation['issues'], (label, animation)
    driver.command('audit 0')
    result = dict(label=label, source=source, target=target, animation=animation,
                  ui=check_ui(driver, config, target, label))
    print(json.dumps(dict(label=label, footprint_tile=result['ui']['footprint_tile'], issues=[])), flush=True)
    return result


def return_and_reenter(driver, config, name, label):
    returned = driver.run(('listing',), 600, 'b')
    assert returned['hit'] == 'listing' and returned['index'] == transitions.names_in_order().index(name), returned
    driver.run(('end_loop',), 600)
    accepted = driver.run(('accept',), 600, 'a')
    assert accepted['hit'] == 'accept', accepted
    selected = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
    assert selected['hit'] == 'selected', selected
    settle(driver)
    ui = check_ui(driver, config, name, label)
    assert ui['footprint_tile'] == 0xb1 and ui['type_tile'] == 0x64, ui
    return dict(label=label, ui=ui)


def main():
    before = protected()
    initialize(json.loads((OUT / 'builds.json').read_text())['configs'])
    config, names = run.WORK['selective'], transitions.names_in_order()
    folder = OUT / 'chain'
    folder.mkdir(exist_ok=True)
    driver = cold.Driver(config['core'], config['rom'], BOOT, CHECKPOINTS / 'input-copy.sav', folder / 'core.log')
    result = dict(private_only=True, continuous=[], roundtrips=[], returns=[])
    try:
        driver.command(f'load {ORIGIN / "all-species/regigigas-to-chikorita-settled/before.s0"}')
        driver.command('rawcolor')
        source = 'regigigas'
        for index, target in enumerate(names):
            row = page(driver, config, source, target, 'down', f'continuous-{index:03}-{target}')
            assert row['ui']['footprint_tile'] == (0x6c if index % 2 == 0 else 0xb1), row
            result['continuous'].append(row)
            source = target
        result['returns'].append(return_and_reenter(driver, config, source, 'continuous-return-reentry'))
        for source in ('chikorita', 'bayleef', 'dusclops', 'metang', 'luxio', 'abomasnow',
                       'gabite', 'heracross', 'crawdaunt', 'gengar', 'zangoose', 'regigigas'):
            index = names.index(source)
            target = names[(index + 1) % len(names)]
            fixture = ORIGIN / 'all-species' / f'{source}-to-{target}-settled/before.s0'
            driver.command(f'load {fixture}')
            driver.run(frames=1)
            for key, start, end, suffix in (('down', source, target, 'B'), ('up', target, source, 'A'),
                                           ('down', source, target, 'B-again')):
                result['roundtrips'].append(page(driver, config, start, end, key, f'{source}-roundtrip-{suffix}'))
            result['returns'].append(return_and_reenter(driver, config, target, f'{source}-return-reentry'))
    finally:
        driver.close()
    result['production_unchanged'] = protected() == before
    assert result['production_unchanged']
    (OUT / 'chain-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(continuous=len(result['continuous']), roundtrip_pages=len(result['roundtrips']),
                         returns_and_reentries=len(result['returns']), production_unchanged=result['production_unchanged'])), flush=True)


if __name__ == '__main__':
    main()
