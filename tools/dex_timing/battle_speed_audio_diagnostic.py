"""Private A/B controls for the inherited odd-period timer's normal-speed cost."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from .battle_normal_speed import BASE, cfg
from . import performance_audio as audio
from tools.build_battle_normal_speed_prototype import install_dispatch


def control(mode):
    local = cfg()
    initial = BASE / 'initial-revision/prototype'
    if initial.exists():
        local.update(root=str(initial / 'candidate'),
                     rom=str(initial / 'pokecrystal-battle-normal-speed.gbc'),
                     sym=str(initial / 'pokecrystal-battle-normal-speed.sym'))
    output = BASE / 'timer-controls' / mode
    checkout = output / 'candidate'
    output.mkdir(parents=True, exist_ok=True)
    if not checkout.exists():
        shutil.copytree(local['root'], checkout)
        path = checkout / 'home/sampled_cry_player.asm'
        source = path.read_text()
        old = '.has_decoded_block\n\tcall SampledCry_AlternateBlockTimer\n'
        if source.count(old) != 1:
            raise RuntimeError('Unexpected timer body')
        replacement = '.has_decoded_block\n'
        if mode == 'gated':
            replacement += '\tld a, [wSampledCryTimerStep]\n\tand a\n\tcall nz, SampledCry_AlternateBlockTimer\n'
        path.write_text(source.replace(old, replacement))
    if mode == 'dispatch' and 'AsyncTimerTickAlternating::' not in (checkout / 'home/sampled_cry_player.asm').read_text():
        install_dispatch(checkout)
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j24', 'pokecrystal.gbc'], cwd=checkout,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    local.update(root=str(checkout), rom=str(checkout / 'pokecrystal.gbc'),
                 sym=str(checkout / 'pokecrystal.sym'), variant=mode)
    prepared = audio.prepare(local, output / 'fixtures', 1, 0)
    prepared['expected_double_speed'] = 0
    (output / 'config.json').write_text(json.dumps(prepared, indent=2) + '\n')
    return prepared


def main():
    configurations = [control(mode) for mode in ('no-alternation-call', 'gated', 'dispatch')]
    tasks = [(c, name, context) for c in configurations for name in audio.SPECIES
             for context in ('catch', 'faint')]
    with ProcessPoolExecutor(max_workers=24) as pool:
        rows = list(pool.map(audio.execute, tasks))
    for task, row in zip(tasks, rows):
        row['variant'] = task[0]['variant']
    report = dict(configurations=configurations, results=rows)
    (BASE / 'timer-controls/report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(variant=r['variant'], species=r['species'], context=r['context'],
                          blocks=[s['blocks'] for s in r['segments']],
                          misses=len(r['known_misses']), issues=r['issues'])
                     for r in rows if r['species'] == 'vibrava' or r['issues']]))


if __name__ == '__main__':
    main()
