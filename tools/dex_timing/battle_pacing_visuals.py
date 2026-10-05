"""Compare native logical states, physical OAM and rendered animation frames."""
from collections import Counter
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import itertools
import json
import hashlib
from pathlib import Path
import subprocess
import tarfile

from PIL import Image, ImageDraw

from .battle_pacing import OUTPUT, TARGETS
from .cold_listing import FRAME
from .performance_archive import compress

FPS = 4194304 / FRAME


def runs(values):
    return [(key, len(list(group))) for key, group in itertools.groupby(values)]


def signature(states):
    return [(s['delay'], s['param'], s['shadow']) for s in states]


def events(folder):
    with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
        return [json.loads(line) for line in stream]


def archive_frames(folder):
    paths = sorted(folder.glob('frame-*.ppm'))
    if not paths:
        return 0
    expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    target = folder / 'rendered-frames.tar.gz'
    before = sum(p.stat().st_size for p in paths)
    with tarfile.open(target, 'w:gz', compresslevel=6) as archive:
        for path in paths:
            archive.add(path, arcname=path.name, recursive=False)
    with tarfile.open(target, 'r:gz') as archive:
        actual = {member.name: hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                  for member in archive.getmembers()}
    if actual != expected or any(hashlib.sha256(p.read_bytes()).hexdigest() != expected[p.name] for p in paths):
        raise RuntimeError(f'Frame archive validation failed: {folder}')
    for path in paths:
        path.unlink()
    if (folder / 'audio.raw').exists():
        before += compress(folder / 'audio.raw')
    return before - target.stat().st_size


def encode(task):
    move, side, variant = task
    folder = OUTPUT / 'replays' / variant / f'{move.lower()}-{side}-q0'
    result = json.loads((folder / 'result.json').read_text())
    rows = events(folder)
    invocation = result['requested_animations'][0]
    start = invocation['start']['t']
    script = next(e for e in rows if e['event'] == 'perf_cost' and e['name'] == 'battle_script'
                  and start <= e['t'] < start + invocation['elapsed_t'])
    frames = [e for e in rows if e['event'] == 'perf_frame']
    first = next(e['display'] for e in frames if e['boundary_t'] >= script['t'])
    last = next(e['display'] for e in frames if e['boundary_t'] >= script['t'] + script['elapsed'])
    first = max(frames[0]['display'], first - 4)
    last = min(frames[-1]['display'], last + 16)
    first_t = next(e['boundary_t'] for e in frames if e['display'] == first) - FRAME
    audio_offset = max(0, (first_t - result['capture_start_t']) / 4194304)
    target = OUTPUT / 'visuals' / f'{move.lower()}-{side}-{variant}.mp4'
    target.parent.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-framerate', str(FPS), '-start_number', str(first), '-i', str(folder / 'frame-%03d.ppm'),
        '-f', 's16le', '-ar', '44100', '-ac', '2', '-ss', str(audio_offset), '-i', str(folder / 'audio.raw'),
        '-frames:v', str(last - first + 1), '-vf', 'scale=640:576:flags=neighbor',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(target)], check=True)
    return dict(move=move, side=side, variant=variant, path=str(target), frames=last - first + 1,
                first=first, last=last)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-frames', action='store_true',
                        help='Losslessly archive only generated frames, preserving verified copies')
    args = parser.parse_args()
    if args.archive_frames:
        folders = [p for p in (OUTPUT / 'replays').glob('*/*') if p.is_dir() and not p.is_symlink()]
        with ProcessPoolExecutor(max_workers=12) as pool:
            reclaimed = sum(pool.map(archive_frames, folders))
        print(json.dumps(dict(reclaimed_gib=reclaimed / 1024**3, folders=len(folders))), flush=True)
        return
    data = json.loads((OUTPUT / 'timing.json').read_text())
    rows = data['rows']
    comparisons = []
    for move in TARGETS:
        for side in ('player', 'foe'):
            for quarter in (0, 17556, 35112, 52668):
                group = {r['variant']: r for r in rows if (r['move'], r['side'], r['quarter']) == (move, side, quarter)}
                states = {v: r['invocations'][0]['scripts'][0]['states'] for v, r in group.items()}
                pace = group['paced']['invocations'][0]['pace']
                phase_by_t = {e['t']: bytes.fromhex(e['data'])[5] for e in pace}
                gaps = [(b['display'] - a['display'], phase_by_t.get(a['t'], 0))
                        for a, b in zip(states['paced'], states['paced'][1:])]
                comparisons.append(dict(move=move, side=side, quarter=quarter,
                    logical_counts={v: len(s) for v, s in states.items()},
                    logical_matches_double=signature(states['final']) == signature(states['paced']),
                    logical_matches_normal=signature(states['production']) == signature(states['paced']),
                    paced_gap_counts=dict(Counter(g for g, p in gaps if p)),
                    max_active_gap=max((g for g, p in gaps if p), default=0),
                    max_unchanged_oam_logical={v: max((n for _, n in runs([s['shadow'] for s in ss])), default=0)
                                               for v, ss in states.items()},
                    crowded_logical={v: sum(s['peak'] > 10 for s in ss) for v, ss in states.items()},
                    peak_logical={v: max(s['peak'] for s in ss) for v, ss in states.items()}))
    result = dict(comparisons=comparisons, mismatches=[r for r in comparisons if not r['logical_matches_double']])
    output = OUTPUT / 'visuals'
    output.mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=12) as pool:
        videos = list(pool.map(encode, [(m, s, v) for m in TARGETS for s in ('player', 'foe')
                                       for v in ('production', 'final', 'paced')]))
    result['videos'] = videos
    physical = []
    for move in TARGETS:
        for side in ('player', 'foe'):
            row = dict(move=move, side=side)
            for variant in ('production', 'final', 'paced'):
                folder = OUTPUT / 'replays' / variant / f'{move.lower()}-{side}-q0'
                captured = events(folder)
                invocation = next(r for r in rows if (r['move'], r['side'], r['quarter'], r['variant']) ==
                                  (move, side, 0, variant))['invocations'][0]
                script = next(e for e in captured if e['event'] == 'perf_cost' and e['name'] == 'battle_script'
                              and invocation['start'] <= e['t'] < invocation['end'])
                frames = [e for e in captured if e['event'] == 'perf_frame'
                          and script['t'] <= e['boundary_t'] < script['t'] + script['elapsed']]
                row[variant] = dict(max_identical_rendered_run=max(n for _, n in runs([e['full'] for e in frames])),
                                    max_identical_hardware_oam_run=max(n for _, n in runs([e['oam'] for e in frames])))
            physical.append(row)
    result['physical'] = physical
    # Match logical states, not wall time, for the bubble-pop comparison.
    for side in ('player', 'foe'):
        selected = {r['variant']: r for r in rows if r['move'] == 'CAUSTIC' and r['side'] == side and r['quarter'] == 0}
        states = {v: r['invocations'][0]['scripts'][0]['states'] for v, r in selected.items()}
        busy = [i for i, s in enumerate(states['paced']) if s['peak'] > 10]
        indexes = sorted(set(i + shift for i in busy[::max(1, len(busy) // 5)] for shift in (-1, 0, 1)
                             if 0 <= i + shift < len(states['paced'])))[:12]
        sheet = Image.new('RGB', (3 * 320, len(indexes) * 308 + 24), 'white')
        draw = ImageDraw.Draw(sheet)
        for column, variant in enumerate(('production', 'final', 'paced')):
            draw.text((column * 320 + 8, 5), variant, fill='black')
            folder = OUTPUT / 'replays' / variant / f'caustic-{side}-q0'
            hardware = [e for e in events(folder) if e['event'] == 'hardware_oam']
            for row, index in enumerate(indexes):
                state = states[variant][index]
                choices = [e for e in hardware if e['t'] >= state['t'] and e['bytes'] == state['shadow']]
                frame = (choices[0] if choices else next(e for e in hardware if e['t'] >= state['t']))['display']
                image = Image.open(folder / f'frame-{frame:03d}.ppm').resize((320, 288), Image.Resampling.NEAREST)
                y = 24 + row * 308
                sheet.paste(image, (column * 320, y))
                draw.text((column * 320 + 4, y + 290), f'Logical {index}, peak {state["peak"]}, display {frame}', fill='black')
        sheet.save(output / f'caustic-{side}-matched-states.png')
    for move in ('SURF', 'WATER_PULSE', 'DRAGON_DANCE', 'SOLARBEAM', 'SUPERPOWER', 'THUNDERBOLT'):
        side = 'player'
        selected = {r['variant']: r for r in rows if r['move'] == move and r['side'] == side and r['quarter'] == 0}
        states = {v: r['invocations'][0]['scripts'][0]['states'] for v, r in selected.items()}
        count = len(states['paced'])
        indexes = list(dict.fromkeys([0, 15, 30, 45, 60, 70, 79, 80, 81, 85, 95, 104, 120, count - 1]))
        indexes = [i for i in indexes if i < count]
        sheet = Image.new('RGB', (3 * 320, len(indexes) * 308 + 24), 'white')
        draw = ImageDraw.Draw(sheet)
        for column, variant in enumerate(('production', 'final', 'paced')):
            draw.text((column * 320 + 8, 5), variant, fill='black')
            folder = OUTPUT / 'replays' / variant / f'{move.lower()}-{side}-q0'
            captured = events(folder)
            hardware = [e for e in captured if e['event'] == 'hardware_oam']
            for row, index in enumerate(indexes):
                state = states[variant][index]
                choices = [e for e in hardware if e['t'] >= state['t'] and e['bytes'] == state['shadow']]
                frame = (choices[0] if choices else next(e for e in hardware if e['t'] >= state['t']))['display']
                image = Image.open(folder / f'frame-{frame:03d}.ppm').resize((320, 288), Image.Resampling.NEAREST)
                y = 24 + row * 308
                sheet.paste(image, (column * 320, y))
                draw.text((column * 320 + 4, y + 290), f'Logical {index}, display {frame}', fill='black')
        sheet.save(output / f'{move.lower()}-{side}-matched-states.png')
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(comparisons=len(comparisons), mismatches=len(result['mismatches']), videos=len(videos),
                         maximum_active_gap=max(r['max_active_gap'] for r in comparisons))), flush=True)


if __name__ == '__main__':
    main()
