# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: rampardos; HBlank start: dot 257.
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

No jointly timer/interval-compatible candidate was found. The following is the nearest elapsed-time diagnostic candidate, NOT a passing replay.
- Producer Entry, mode: captured 2, modeled 3.
- First Miss, mode: captured 3, modeled 2.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37440 | 37444 | +4 |
| Stage Entry -> Producer Entry | 48576 | 48708 | +132 |
| Producer Entry -> Frame Wait | 5120 | 5132 | +12 |
| Frame Wait -> First Miss | 208448 | 208204 | -244 |

One or more intervals exceed the timer's +/-63 T observation uncertainty; these differences remain unexplained.
One initial phase matches every DIV/TIMA pair: False.
Example initial phase: 408 T; owner variant 0; initial DIV low byte: 4.
Only the initial decoded dictionary prefix is seeded: 145 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780], 'lcd': [108], 'timer': [1452, 1472]}.

Additional 139-byte trace comparison: 46 differing byte observations across all five stops.
Trace equality is an additional check beyond the core-state/timer verdict; do not call this byte-identical replay.
- Producer Entry (captured -> modeled): $c779: $16 -> $17, $c77b: $16 -> $17, $c77d: $16 -> $17, $c77f: $16 -> $17, $c781: $16 -> $17, $c783: $4a -> $49, $c7c1: $4a -> $49, $c7c3: $16 -> $17, $c7c5: $16 -> $17, $c7c7: $16 -> $17, $c7c9: $16 -> $17, $c7cb: $16 -> $17.
- Frame Wait (captured -> modeled): $c773: $1a -> $1b, $c779: $1a -> $1b, $c77b: $1a -> $1b, $c77d: $1a -> $1b, $c77f: $1a -> $1b, $c781: $1a -> $1b, $c783: $4a -> $49, $c7c1: $4a -> $49, $c7c3: $16 -> $17, $c7c5: $16 -> $17, $c7c7: $16 -> $17, $c7c9: $16 -> $17, $c7cb: $16 -> $17, $c7d3: $1a -> $1b, $c7d5: $1a -> $1b, $c7d7: $1a -> $1b, $c7d9: $1a -> $1b, $c7db: $1a -> $1b, $c7dd: $1a -> $1b.
- First Miss (captured -> modeled): $c783: $4a -> $49, $c7a3: $84 -> $85, $c7af: $1d -> $1c, $c7c1: $4a -> $49, $c7c3: $16 -> $17, $c7c5: $16 -> $17, $c7c7: $16 -> $17, $c7c9: $16 -> $17, $c7cb: $16 -> $17, $c7d3: $1a -> $1b, $c7d5: $1a -> $1b, $c7d7: $1a -> $1b, $c7d9: $1a -> $1b, $c7db: $1a -> $1b, $c7dd: $1a -> $1b.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 1 | publication | 0 | 145 | 33 / 33 |
| 2 | 2 | stage prepared | 1 | 23 | 0 / 38 |
| 2 | 2 | upload helper entry | 3 | 135 | 0 / 38 |
| 2 | 2 | upload armed | 4 | 0 | 0 / 38 |
| 2 | 2 | deadline miss | 4 | 29 | 20 / 38 |

Residuals remain: this comparison does not certify capture agreement, exact hardware timing, or deadlines.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
