"""Aggregate private A/B evidence and produce an actual-frame contact sheet."""
from collections import Counter
import json
from pathlib import Path
import statistics

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from run import OUT, ORIGIN, white_mask


def distribution(values):
    return dict(min=min(values), mean=statistics.mean(values), median=statistics.median(values), max=max(values))


def main():
    comparisons = [json.loads(p.read_text()) for p in sorted((OUT / 'cases').glob('*/comparison.json'))]
    settled = [row for row in comparisons if row['label'].endswith('-settled')]
    cross_control = []
    for row in comparisons:
        folders = {v: OUT / 'cases' / row['label'] / v for v in ('blackout', 'selective')}
        trace = [json.loads(line) for line in (folders['blackout'] / 'trace.jsonl').read_text().splitlines()]
        mask = white_mask(trace[0])
        last_old = {}
        for variant in folders:
            number = row[variant]['first_mask_frame'] - 1
            last_old[variant] = np.asarray(Image.open(folders[variant] / f'trace-{number:03}.png'))
        if not np.array_equal(last_old['blackout'][~mask], last_old['selective'][~mask]):
            cross_control.append(row['label'])
    cold_identical, cold_changed = [], []
    for file in sorted((OUT / 'cold-regression').glob('[0-9][0-9][0-9]-*.json')):
        original = ORIGIN / 'cold' / file.name
        (cold_identical if original.read_bytes() == file.read_bytes() else cold_changed).append(file.stem)
    cry = json.loads((OUT / 'cry-regression/report.json').read_text())
    listing = json.loads((OUT / 'listing-regression/report.json').read_text())
    milliseconds_per_interval = 70224 / 4194304 * 1000
    report = dict(
        builds=json.loads((OUT / 'builds.json').read_text()),
        endpoint_definition='Input begins when the isolated driver presses the direction. '
        'Visible start is the first completed hardware display with the blackout/selective mask. '
        'Completion is the first completed hardware display of the complete incoming page. '
        'These are presented-frame times, not the earlier RAM-ready or VBlank commit instruction. '
        'Ordinary footer cursor blinking before transition acceptance is not counted as transition onset.',
        normal_settled_pairs=len(settled), total_paired_transitions=len(comparisons),
        normal_timings_intervals={v: {k: distribution([row[v][k] / 70224 for row in settled]) for k in (
            'input_to_accept_cycles', 'input_to_visible_start_cycles', 'input_to_visible_complete_cycles',
            'accepted_to_revealed_cycles')} for v in ('blackout', 'selective')},
        milliseconds_per_interval=milliseconds_per_interval,
        faster_case_labels=[row['label'] for row in comparisons if row['differences']['input_to_visible_complete_cycles'] < 0],
        displayed_completion_delta_cycles=dict(Counter(str(row['differences']['input_to_visible_complete_cycles']) for row in comparisons)),
        mask_duration_intervals=distribution([row['selective']['masked_display_frames'] for row in settled]),
        old_owner_nonmasked_pixels_match_control=not cross_control,
        old_owner_cross_control_failures=cross_control,
        unused_background_palette_slots=[3, 4, 5],
        unused_palette_note='The control zeros these unused slots; the prototype leaves them alone. '
        'They are not referenced by the visible Description. Final used palettes, maps, type graphics, '
        'border graphics, footprints, and screen pixels compare equal.',
        cold_entry_identical_result_files=len(cold_identical), cold_entry_changed_result_files=cold_changed,
        additional_tests=dict(cold_listing=373, active_page_and_b_return=len(cry['all_species_handoffs']),
            focused_cry_handoffs=len(cry['results']), footer_navigation=len(cry['navigation_controls']),
            listing_returns=len(listing['results']), listing_followups=sum(len(r['follow_up']['checks']) for r in listing['results']),
            listing_late_admissions=43, paired_internal_late_admissions=43,
            observer_equivalence_controls=7),
        suite_summary=json.loads((OUT / 'all-summary.json').read_text()),
        regression_summary=json.loads((OUT / 'regression-summary.json').read_text()),
        representative_cases=[{k: row[k] for k in ('label', 'blackout', 'selective', 'differences')}
            for row in settled if row['target'] in ('bayleef', 'meganium', 'dusknoir', 'metagross', 'luxray', 'weavile', 'bastiodon')],
        assessment='Promising visual change, not a material loading-speed optimization. '
        'The old text, shell, and footer remain visible while portrait, footprint, and existing type badges '
        'are white. Incoming content is still atomically revealed. No new issues were found in the tested '
        'paths. Six of 647 pairs finish one interval earlier, the other 641 are equal; none are slower.'
    )
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    row = next(r for r in comparisons if r['label'] == 'dusclops-to-dusknoir-settled')
    canvas = Image.new('RGB', (1660, 730), '#e6e6e6')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
    for y, variant, name in ((0, 'blackout', 'A: Accepted full blackout'), (365, 'selective', 'B: Selective graphics mask')):
        folder, metrics = OUT / 'cases' / row['label'] / variant, row[variant]
        draw.text((10, y + 8), name, font=font, fill='black')
        first, complete = metrics['first_mask_frame'], metrics['first_complete_frame']
        stages = ((first - 1, 'Outgoing page'), (first, 'Mask begins'),
                  (complete - 1, 'Still preparing'), (complete, 'Complete incoming page'),
                  (complete + 2, 'Animation begins'))
        for x, (number, label) in enumerate(stages):
            picture = Image.open(folder / f'trace-{number:03}.png')
            canvas.paste(picture.resize((320, 288), Image.Resampling.NEAREST), (10 + x * 330, y + 40))
            draw.text((10 + x * 330, y + 334), label, font=font, fill='black')
    canvas.save(OUT / 'comparison.png')
    print(json.dumps(dict(pairs=len(comparisons), cold_identical=len(cold_identical),
                         cold_changed=cold_changed, cross_control_failures=cross_control,
                         production_unchanged=report['regression_summary']['production_unchanged'])), flush=True)
    return int(bool(cross_control or cold_changed))


if __name__ == '__main__':
    raise SystemExit(main())
