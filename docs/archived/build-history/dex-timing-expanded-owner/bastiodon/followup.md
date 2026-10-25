# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: bastiodon; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

## Capture-Seeded Linked Replay

**RESIDUAL_MISMATCH**

Joint state/timer matches: 0/64 sampled initial states.
Also matching all captured trace bytes: 0/64.
Initial owner state: captured.
This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

The following is the closest state comparison among timer-compatible candidates, NOT a passing replay.
- Producer Entry, mode: captured 0, modeled 3.
- Producer Entry, enabled_if: captured 2, modeled 0.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37440 | 37444 | +4 |
| Stage Entry -> Producer Entry | 47488 | 47480 | -8 |
| Producer Entry -> Frame Wait | 3776 | 3788 | +12 |
| Frame Wait -> First Miss | 279552 | 279548 | -4 |

All four differences fall within the timer's +/-63 T observation uncertainty.
Example initial phase: 340 T; owner variant 0; initial DIV low byte: 200.
Only the initial decoded dictionary prefix is seeded: 145 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 5 differing byte observations across all five stops.
Trace equality is an additional check beyond the core-state/timer verdict; do not call this byte-identical replay.
- Producer Entry (captured -> modeled): $c783: $4a -> $49, $c7c1: $4a -> $49.
- Frame Wait (captured -> modeled): $c783: $4a -> $49, $c7c1: $4a -> $49.
- First Miss (captured -> modeled): $c783: $4a -> $49.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 1 | publication | 0 | 145 | 35 / 35 |
| 2 | 2 | stage prepared | 1 | 20 | 0 / 37 |
| 2 | 2 | upload helper entry | 4 | 137 | 0 / 37 |
| 2 | 2 | upload armed | 5 | 0 | 0 / 37 |
| 2 | 2 | deadline miss | 5 | 26 | 20 / 37 |

Residuals remain: this comparison does not certify capture agreement, exact hardware timing, or deadlines.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
