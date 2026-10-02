"""Private normal-input checks for icon-buffer return, re-entry and footer paths."""
import json

from run import (OUT, ORIGIN, CHECKPOINTS, BOOT, initialize, cold, settle,
                 transitions, audit_footprint)
from chain import check_ui, protected
import run


def main():
    before = protected()
    initialize(json.loads((OUT / 'builds.json').read_text())['configs'])
    names = transitions.names_in_order()
    result = dict(private_only=True, returns=[], footer=[])
    sources = ('chikorita', 'bayleef', 'dusclops', 'metang', 'luxio', 'abomasnow',
               'gabite', 'heracross', 'crawdaunt', 'gengar', 'zangoose', 'regigigas')
    for source in sources:
        target = names[(names.index(source) + 1) % len(names)]
        fixture = ORIGIN / 'all-species' / f'{source}-to-{target}-settled/before.s0'
        comparison = dict(source=source, target=target)
        for variant, config in run.WORK.items():
            label = f'controls-{source}-{variant}'
            driver = cold.Driver(config['core'], config['rom'], BOOT,
                                 CHECKPOINTS / 'input-copy.sav', OUT / f'{label}.log')
            try:
                driver.command(f'load {fixture}')
                driver.command('rawcolor')
                driver.run(('change_species', 'animation_miss', 'audio_miss'), key='down')
                settle(driver)
                started = driver.command('peek')['t']
                listing = driver.run(('listing',), 600, 'b')
                driver.run(('end_loop',), 600)
                input_t = driver.command('peek')['t']
                accepted = driver.run(('accept',), 600, 'a')
                selected = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
                assert selected['hit'] == 'selected' and selected['selected_index'] == names.index(target), selected
                settle(driver)
                comparison[variant] = dict(return_cycles=listing['t'] - started,
                    reentry_cycles=selected['t'] - input_t,
                    accepted_to_selected_cycles=selected['t'] - accepted['t'],
                    ui=check_ui(driver, config, target, label))
                driver.run(frames=2)
                for page in (1, 0):
                    driver.run(frames=2, key='a')
                    driver.run(frames=8)
                    text_ui = driver.command('ui')
                    assert text_ui['page'] == page, (label, page, text_ui['page'], driver.command('peek'))
                    check_ui(driver, config, target, f'{label}-description{page}')
                result['footer'].append(dict(label=label, description_pages=2, issues=[]))
                if source in ('chikorita', 'dusclops', 'metang', 'luxio', 'gengar', 'regigigas'):
                    for _ in range(3):
                        driver.run(frames=2, key='right')
                        driver.run(frames=2)
                    area = driver.run(frames=30, key='a')
                    assert area['state'] == 4, area
                    driver.run(frames=120)
                    driver.run(frames=2, key='b')
                    restored = driver.run(('selected', 'animation_miss', 'audio_miss'), 600)
                    assert restored['hit'] == 'selected' and restored['state'] == 1, restored
                    settle(driver)
                    check_ui(driver, config, target, f'{label}-area-restored')
                    result['footer'].append(dict(label=label, area_roundtrip=True, issues=[]))
            finally:
                driver.close()
        comparison['differences'] = {k: comparison['selective'][k] - comparison['blackout'][k]
                                     for k in ('return_cycles', 'reentry_cycles', 'accepted_to_selected_cycles')}
        result['returns'].append(comparison)
        print(json.dumps(comparison), flush=True)
    result['production_unchanged'] = protected() == before
    assert result['production_unchanged']
    (OUT / 'return-controls-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(return_pairs=len(result['returns']), footer_cases=len(result['footer']),
                         production_unchanged=result['production_unchanged'])), flush=True)


if __name__ == '__main__':
    main()
