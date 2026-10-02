# Host-Model Capture Comparison

**Status: PARTIAL, NOT CALIBRATED.**

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

The game/ROM was not changed. These are host-only corrections and phase experiments.

## First Misses in SameBoy

| Capture | Event | Frame | Deadline | Uploaded |
|---|---:|---:|---:|---:|
| Weavile - Test 1.txt | 2 | 2 | +3 | 0 |
| Weavile - Test 2.txt | 2 | 2 | +3 | 0 |
| Weavile - Test 3.txt | 2 | 2 | +3 | 0 |
| Luxray - Test 1.txt | 7 | 2 | +29 | 0 |
| Luxray - Test 2.txt | 7 | 2 | +29 | 0 |
| Luxray - Test 3.txt | 7 | 2 | +29 | 0 |

## Component Comparison

Ranges are independently swept dot/timer/HBlank phases, not an exact replay or proof. Observations have +/- one scanline uncertainty (~0.109 ms).

| Species / operation | Samples | Observed ms | Before ms | Corrected ms | Overlap |
|---|---:|---:|---:|---:|---:|
| luxray gather 20 tiles | 6 | 6.958-7.284 | 6.876-7.534 | 6.876-7.534 | 6/6 |
| luxray hdma 20 tiles | 6 | 2.283-7.284 | 2.198-7.632 | 2.198-7.632 | 6/6 |
| luxray stage frame 3 | 5 | 12.394-12.829 | 12.010-13.236 | 12.010-13.236 | 5/5 |
| weavile gather 7 tiles | 3 | 2.718-2.718 | 2.335-2.915 | 2.335-2.915 | 3/3 |
| weavile gather 20 tiles | 9 | 7.067-7.502 | 6.773-7.534 | 6.773-7.534 | 9/9 |
| weavile hdma 7 tiles | 3 | 1.196-1.305 | 0.784-1.300 | 0.784-1.300 | 3/3 |
| weavile hdma 20 tiles | 9 | 2.283-2.718 | 2.198-2.713 | 2.198-2.713 | 9/9 |
| weavile stage frame 2 | 6 | 6.306-6.741 | 5.836-6.823 | 5.836-6.823 | 6/6 |
| weavile stage frame 3 | 3 | 8.806-8.806 | 8.367-8.992 | 8.367-8.992 | 3/3 |
| weavile stage frame 4 | 6 | 7.828-8.480 | 7.323-8.597 | 7.323-8.597 | 6/6 |

## Full-Replay First Misses

These remain phase experiments. Do not choose a phase just because it matches a failure.

| Species / model | Initial LY | First event | Frame | Uploaded / required | Deadline |
|---|---:|---:|---:|---:|---:|
| luxray before | 0 | 7 | 2 | 0/21 | +29 |
| luxray before | 64 | 2 | 1 | 0/17 | +10 |
| luxray before | 107 | 2 | 1 | 0/17 | +10 |
| luxray before | 108 | 2 | 1 | 0/17 | +10 |
| luxray before | 128 | 2 | 1 | 0/17 | +10 |
| luxray before | 143 | 2 | 1 | 0/17 | +10 |
| luxray before | 144 | 7 | 2 | 0/21 | +29 |
| luxray before | 153 | 7 | 2 | 0/21 | +29 |
| luxray after | 0 | 7 | 2 | 0/21 | +29 |
| luxray after | 64 | 2 | 1 | 0/17 | +10 |
| luxray after | 107 | 2 | 1 | 0/17 | +10 |
| luxray after | 108 | 2 | 1 | 0/17 | +10 |
| luxray after | 128 | 2 | 1 | 0/17 | +10 |
| luxray after | 143 | 2 | 1 | 0/17 | +10 |
| luxray after | 144 | 7 | 2 | 0/21 | +29 |
| luxray after | 153 | 7 | 2 | 0/21 | +29 |
| weavile before | 0 | 2 | 2 | 0/18 | +3 |
| weavile before | 64 | 2 | 2 | 0/18 | +3 |
| weavile before | 107 | 2 | 2 | 0/18 | +3 |
| weavile before | 108 | 2 | 2 | 0/18 | +3 |
| weavile before | 128 | 2 | 2 | 0/18 | +3 |
| weavile before | 143 | 2 | 2 | 0/18 | +3 |
| weavile before | 144 | 2 | 2 | 0/18 | +3 |
| weavile before | 153 | 2 | 2 | 0/18 | +3 |
| weavile after | 0 | 2 | 2 | 0/18 | +3 |
| weavile after | 64 | 2 | 2 | 0/18 | +3 |
| weavile after | 107 | 2 | 2 | 0/18 | +3 |
| weavile after | 108 | 2 | 2 | 0/18 | +3 |
| weavile after | 128 | 2 | 2 | 0/18 | +3 |
| weavile after | 143 | 2 | 2 | 0/18 | +3 |
| weavile after | 144 | 2 | 2 | 0/18 | +3 |
| weavile after | 153 | 2 | 2 | 0/18 | +3 |

Report profiles: before HBlank dot 257; after dot 257.
If these profiles differ, the report rows are not a single-change A/B. The explicit phase sweep below separates the PPU assumptions.

## Remaining Limits

- IE $0f, STAT mode-0 enabled, hLCDCPointer zero, normal CPU speed.
- new-stage construction; both slots swept, no resident fast path.
- complete dictionaries; gather schedule-run reload and continuation both swept.
- three dot positions and 200 timer phases, not an exhaustive continuous bound.
- HDMA component stops at helper return; small outer return path is unmodeled.
- idle VBlank fixture applies; no palette/tile requests or active synth music.
- component envelopes are independent, not one reconstructed IRQ history.
- end-to-end entry phase is not established by a late first-miss dump.

## Initial Timer Phase Sensitivity

Native cold path, initial LY 144; timer delays 64..12800 T in steps of 64, separately for each listed HBlank profile. No per-species workload is fitted. A matching state is not proof of the actual phase.

- luxray, HBlank dot 257: 200/200 sampled phases reproduce the event/frame/deadline/loaded/uploaded first-miss state.
- luxray, HBlank dot 369: 0/200 sampled phases reproduce the event/frame/deadline/loaded/uploaded first-miss state.
- weavile, HBlank dot 257: 176/200 sampled phases reproduce the event/frame/deadline/loaded/uploaded first-miss state.
- weavile, HBlank dot 369: 200/200 sampled phases reproduce the event/frame/deadline/loaded/uploaded first-miss state.
