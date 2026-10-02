# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: rayquaza; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

## Capture-Seeded Linked Replay

**CAPTURE_CONSISTENT**

Joint state/timer matches: 2/64 sampled initial states.
Also matching all captured trace bytes: 2/64.
Initial owner state: captured.
This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 36992 | 36976 | -16 |
| Stage Entry -> Producer Entry | 24960 | 25012 | +52 |
| Producer Entry -> Frame Wait | 5376 | 5348 | -28 |
| Frame Wait -> First Miss | 673600 | 673580 | -20 |

All four differences fall within the timer's +/-63 T observation uncertainty.
One initial phase matches every DIV/TIMA pair: True.
Example initial phase: 644 T; owner variant 0; initial DIV low byte: 24.
Only the initial decoded dictionary prefix is seeded: 115 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780, 4316], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 0 differing byte observations across all five stops.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 0 | publication | 0 | 145 | 0 / 0 |
| 2 | 1 | stage prepared | 0 | 124 | 0 / 15 |
| 2 | 1 | upload helper entry | 5 | 116 | 0 / 15 |
| 2 | 1 | upload armed | 6 | 0 | 0 / 15 |
| 2 | 1 | map queued | 6 | 60 | 15 / 15 |
| 2 | 1 | publication | 7 | 145 | 15 / 15 |
| 3 | 2 | stage prepared | 7 | 133 | 0 / 20 |
| 3 | 2 | deadline miss | 10 | 73 | 0 / 20 |

This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
