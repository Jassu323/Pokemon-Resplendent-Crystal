"""Read-only Dex speed-switch, audio-period and entry/exit tests."""
import argparse
import json
from pathlib import Path
import statistics
import wave

from .assets import Repository
from .cold_listing import Driver, ROOT, move, predecessor
from .info_ui import BOOT
from .description_ui import settle
from .performance import core, T, HZ, result_timing


def open_menu(driver):
    for _ in range(180):
        state = driver.run(('continue', 'new_game', 'overworld'), 20, 'a')
        if state['hit'] == 'new_game':
            raise RuntimeError('Private battery could not Continue')
        if state['hit'] == 'overworld':
            break
        driver.run(frames=10)
    else:
        raise RuntimeError('Overworld not reached')
    driver.run(('start_menu',), key='start')
    for _ in range(12):
        state = driver.run(('start_menu',), 60)
        if state['menu'] == 1:
            return
        driver.run(frames=2, key='up')
    raise RuntimeError('Dex menu item not reached')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text())
    repo = Repository(ROOT, Path(config['rom']), Path(config['sym']))
    binary = core(repo, args.output, dict(speed_enter=('PokedexPerf_DoubleSpeed', True),
        speed_exit=('PokedexPerf_NormalSpeed', True), switch_speed=('SwitchSpeed', True),
        timer_block=('SampledCry_AsyncTimerTick', False)))
    expected_speed = int('PokedexPerf_DoubleSpeed' in repo.symbols)
    rows = []
    for q in (0, 17556, 35112, 52668):
        driver = Driver(binary, config['rom'], BOOT, config['battery'], args.output / f'life-{q}.log')
        try:
            driver.command('rawcolor')
            open_menu(driver)
            driver.command(f'run 0 {q} 0')
            for iteration in range(2):
                initial = driver.command('perf 1')
                driver.events.clear()
                if q == 0 and iteration == 0:
                    driver.command(f'perfimages {args.output / "entry"}')
                listed = driver.run(('listing',), 600, 'a')
                driver.run(frames=3)
                final = driver.command('perf 0')
                driver.command('perfimages -')
                events = list(driver.events)
                entry = result_timing(events, initial, final, 'full', initial['t'], initial['t'])
                if listed['double_speed'] != expected_speed:
                    raise RuntimeError('Wrong Dex clock')
                initial = driver.command('perf 1')
                driver.events.clear()
                if q == 0 and iteration == 0:
                    driver.command(f'perfimages {args.output / "exit"}')
                returned = driver.run(('start_menu',), 600, 'b')
                driver.run(frames=3)
                final = driver.command('perf 0')
                driver.command('perfimages -')
                exits = list(driver.events)
                leave = result_timing(exits, initial, final, 'full', initial['t'], initial['t'])
                if returned['double_speed'] != 0:
                    raise RuntimeError('Double speed leaked outside Dex')
                rows.append(dict(q=q, iteration=iteration, entry=entry, exit=leave,
                                 switches=[e for e in events + exits if e['event'] == 'perf_cost' and e['name'].startswith(('speed_', 'switch_'))],
                                 switch_states=[e for e in events + exits if e['event'] == 'perf_phase' and e['name'] == 'switch_speed']))
                driver.run(('start_menu',), 60)
                driver.run(frames=3)
            driver.run(('overworld',), key='b')
            driver.run(('overworld',), frames=300)
            if driver.command('peek')['double_speed']:
                raise RuntimeError('Overworld clock not normal')
        finally:
            (args.output / f'life-{q}-events.json').write_text(json.dumps(driver.events, indent=2) + '\n')
            driver.close()
    audio = []
    for name in ('chikorita', 'mewtwo', 'dusknoir', 'garchomp', 'weavile', 'metagross'):
        driver = Driver(binary, config['rom'], BOOT, config['battery'], args.output / f'audio-{name}.log')
        try:
            index = config['names'].index(name)
            prior, direction = predecessor(index)
            driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
            move(driver, direction, index)
            driver.command('audit 1')
            raw = args.output / f'{name}.pcm'
            driver.command(f'perfaudio {raw}')
            driver.command('perf 1')
            driver.events.clear()
            driver.run(('accept',), key='a')
            driver.run(('selected',), frames=600)
            settle(driver)
            driver.command('perfaudio -')
            driver.command('perf 0')
            ticks = [e for e in driver.events if e['event'] == 'perf_phase' and e['name'] == 'timer_block']
            periods = [b['t'] - a['t'] for a, b in zip(ticks, ticks[1:])]
            stops = [e for e in driver.events if e['event'] in ('audio_stop', 'audio_miss', 'animation_miss')]
            if any(e['event'] != 'audio_stop' or e.get('remaining') for e in stops):
                raise RuntimeError(f'Playback miss: {name}')
            if ticks and any((e['tac'] & 7, e['tma']) != ((7, 156) if expected_speed else (6, 56)) for e in ticks):
                raise RuntimeError('Unexpected timer configuration')
            with wave.open(str(args.output / f'{name}.wav'), 'wb') as output:
                output.setnchannels(2)
                output.setsampwidth(2)
                output.setframerate(44100)
                output.writeframes(raw.read_bytes())
            raw.unlink()
            audio.append(dict(species=name, blocks=len(ticks), minimum_period=min(periods) if periods else None,
                              maximum_period=max(periods) if periods else None,
                              median_period=statistics.median(periods) if periods else None, stops=stops,
                              total_t=ticks[-1]['t']-ticks[0]['t'] if ticks else None))
        finally:
            driver.close()
    report = dict(lifecycle=rows, audio=audio, expected_speed=expected_speed, frame_ms=1000*T/HZ)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
