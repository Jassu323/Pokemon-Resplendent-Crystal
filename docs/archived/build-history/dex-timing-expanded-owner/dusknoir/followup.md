# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: dusknoir; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

## Capture-Seeded Linked Replay

**CAPTURE_CONSISTENT**

Joint state/timer matches: 9/64 sampled initial states.
Also matching all captured trace bytes: 3/64.
Initial owner state: captured.
This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37184 | 37208 | +24 |
| Stage Entry -> Producer Entry | 43968 | 43968 | +0 |
| Producer Entry -> Frame Wait | 3712 | 3696 | -16 |
| Frame Wait -> First Miss | 423872 | 423848 | -24 |

All four differences fall within the timer's +/-63 T observation uncertainty.
Example initial phase: 10180 T; owner variant 0; initial DIV low byte: 152.
Only the initial decoded dictionary prefix is seeded: 145 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 0 differing byte observations across all five stops.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 1 | publication | 0 | 145 | 30 / 30 |
| 2 | 2 | stage prepared | 1 | 12 | 0 / 32 |
| 2 | 2 | upload helper entry | 6 | 135 | 0 / 32 |
| 2 | 2 | upload armed | 7 | 0 | 0 / 32 |
| 2 | 2 | deadline miss | 7 | 26 | 20 / 32 |

This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
