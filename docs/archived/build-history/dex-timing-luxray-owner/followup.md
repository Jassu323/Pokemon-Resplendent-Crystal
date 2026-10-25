# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: luxray; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

## Capture-Seeded Linked Replay

**CAPTURE_CONSISTENT**

Joint state/timer matches: 1/60 sampled initial states.
Initial owner state: captured.
This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37440 | 37428 | -12 |
| Stage Entry -> Producer Entry | 25792 | 25760 | -32 |
| Producer Entry -> Frame Wait | 5184 | 5232 | +48 |
| Frame Wait -> First Miss | 1936512 | 1936524 | +12 |

All four differences fall within the timer's +/-63 T observation uncertainty.
Example initial phase: 560 T; owner variant 0; initial DIV low byte: 236.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780, 3320, 4172, 4184, 4316], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 7 differing byte observations across all five stops.
These differences are not included in the joint core-state/timer match above; do not call this byte-identical replay.
- First Miss (captured -> modeled): $c783: $49 -> $4a, $c7af: $42 -> $43, $c7b1: $42 -> $43, $c7b3: $42 -> $43, $c7b5: $42 -> $43, $c7b7: $42 -> $43, $c7b9: $42 -> $43.

## Modeled Work Sequence

Intervening events below are predictions from the matching replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 0 | publication | 0 | 145 | 0 / 0 |
| 2 | 1 | stage prepared | 0 | 126 | 0 / 17 |
| 2 | 1 | upload helper entry | 9 | 126 | 0 / 17 |
| 2 | 1 | upload armed | 10 | 0 | 0 / 17 |
| 2 | 1 | map queued | 10 | 62 | 17 / 17 |
| 2 | 1 | publication | 11 | 145 | 17 / 17 |
| 3 | 0 | stage prepared | 11 | 87 | 0 / 0 |
| 3 | 0 | map queued | 11 | 137 | 0 / 0 |
| 3 | 0 | publication | 13 | 145 | 0 / 0 |
| 4 | 1 | stage prepared | 13 | 77 | 0 / 0 |
| 4 | 1 | map queued | 13 | 122 | 0 / 0 |
| 4 | 1 | publication | 16 | 145 | 0 / 0 |
| 5 | 0 | stage prepared | 16 | 90 | 0 / 0 |
| 5 | 0 | map queued | 16 | 135 | 0 / 0 |
| 5 | 0 | publication | 19 | 145 | 0 / 0 |
| 6 | 1 | stage prepared | 19 | 78 | 0 / 0 |
| 6 | 1 | map queued | 19 | 123 | 0 / 0 |
| 6 | 1 | publication | 22 | 145 | 0 / 0 |
| 7 | 2 | stage prepared | 22 | 138 | 0 / 21 |
| 7 | 2 | deadline miss | 28 | 73 | 0 / 21 |

This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
