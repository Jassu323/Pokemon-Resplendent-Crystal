# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: kyogre; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

## Capture-Seeded Linked Replay

**CAPTURE_CONSISTENT**

Joint state/timer matches: 12/64 sampled initial states.
Also matching all captured trace bytes: 8/64.
Initial owner state: captured.
This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37440 | 37428 | -12 |
| Stage Entry -> Producer Entry | 20992 | 21008 | +16 |
| Producer Entry -> Frame Wait | 3648 | 3672 | +24 |
| Frame Wait -> First Miss | 538816 | 538804 | -12 |

All four differences fall within the timer's +/-63 T observation uncertainty.
One initial phase matches every DIV/TIMA pair: True.
Example initial phase: 700 T; owner variant 0; initial DIV low byte: 32.
Only the initial decoded dictionary prefix is seeded: 124 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780, 4300], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 0 differing byte observations across all five stops.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 0 | publication | 0 | 145 | 0 / 0 |
| 2 | 5 | stage prepared | 0 | 116 | 0 / 10 |
| 2 | 5 | upload helper entry | 5 | 103 | 0 / 10 |
| 2 | 5 | upload armed | 5 | 104 | 0 / 10 |
| 2 | 5 | map queued | 6 | 10 | 10 / 10 |
| 2 | 5 | publication | 7 | 145 | 10 / 10 |
| 3 | 6 | stage prepared | 7 | 113 | 0 / 10 |
| 3 | 6 | deadline miss | 8 | 74 | 0 / 10 |

This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
