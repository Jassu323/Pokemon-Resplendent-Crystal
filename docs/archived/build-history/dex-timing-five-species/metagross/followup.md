# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: metagross; HBlank start: dot 257.
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
- Stage Entry, ly: captured 72, modeled 73.
- Producer Entry, ly: captured 107, modeled 108.
- Frame Wait, ly: captured 115, modeled 116.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 36928 | 37428 | +500 |
| Stage Entry -> Producer Entry | 15808 | 15824 | +16 |
| Producer Entry -> Frame Wait | 3712 | 3672 | -40 |
| Frame Wait -> First Miss | 3002304 | 3001832 | -472 |

One or more intervals exceed the timer's +/-63 T observation uncertainty; these differences remain unexplained.
One initial phase matches every DIV/TIMA pair: False.
Example initial phase: 532 T; owner variant 0; initial DIV low byte: 8.
Only the initial decoded dictionary prefix is seeded: 97 tiles.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780, 3252, 3320, 4184, 4316], 'lcd': [108], 'timer': [1452, 1472, 1480]}.

Additional 139-byte trace comparison: 33 differing byte observations across all five stops.
Trace equality is an additional check beyond the core-state/timer verdict; do not call this byte-identical replay.
- Producer Entry (captured -> modeled): $c779: $64 -> $65, $c77b: $64 -> $65, $c77d: $64 -> $65, $c77f: $64 -> $65, $c781: $64 -> $65, $c783: $48 -> $49, $c785: $64 -> $65, $c78b: $48 -> $49, $c78d: $64 -> $65, $c78f: $64 -> $65, $c791: $64 -> $65, $c793: $64 -> $65, $c795: $64 -> $65.
- Frame Wait (captured -> modeled): $c773: $6b -> $6c, $c779: $6b -> $6c, $c77b: $6b -> $6c, $c77d: $6b -> $6c, $c77f: $6b -> $6c, $c781: $6b -> $6c, $c783: $48 -> $49, $c785: $64 -> $65, $c78b: $48 -> $49, $c78d: $64 -> $65, $c78f: $64 -> $65, $c791: $64 -> $65, $c793: $64 -> $65, $c795: $64 -> $65, $c79d: $6b -> $6c, $c79f: $6b -> $6c, $c7a1: $6b -> $6c, $c7a3: $6b -> $6c, $c7a5: $6b -> $6c, $c7a7: $6b -> $6c.

## Modeled Work Sequence

Intervening events below are predictions from the selected replay, not additional captured breakpoints.
Interval zero is the first publication VBlank. Queueing and actual publication are distinct.

| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |
|---|---:|---|---:|---:|---:|
| 1 | 0 | publication | 0 | 145 | 0 / 0 |
| 2 | 1 | stage prepared | 0 | 101 | 0 / 3 |
| 2 | 1 | upload helper entry | 3 | 80 | 0 / 3 |
| 2 | 1 | upload armed | 3 | 81 | 0 / 3 |
| 2 | 1 | map queued | 3 | 129 | 3 / 3 |
| 2 | 1 | publication | 4 | 145 | 3 / 3 |
| 3 | 2 | stage prepared | 4 | 102 | 0 / 3 |
| 3 | 2 | upload helper entry | 7 | 82 | 0 / 3 |
| 3 | 2 | upload armed | 7 | 82 | 0 / 3 |
| 3 | 2 | map queued | 7 | 130 | 3 / 3 |
| 3 | 2 | publication | 8 | 145 | 3 / 3 |
| 4 | 1 | stage prepared | 8 | 77 | 0 / 0 |
| 4 | 1 | map queued | 8 | 127 | 0 / 0 |
| 4 | 1 | publication | 12 | 145 | 0 / 0 |
| 5 | 2 | stage prepared | 12 | 78 | 0 / 0 |
| 5 | 2 | map queued | 12 | 127 | 0 / 0 |
| 5 | 2 | publication | 16 | 145 | 0 / 0 |
| 6 | 1 | stage prepared | 16 | 77 | 0 / 0 |
| 6 | 1 | map queued | 16 | 126 | 0 / 0 |
| 6 | 1 | publication | 20 | 145 | 0 / 0 |
| 7 | 2 | stage prepared | 20 | 78 | 0 / 0 |
| 7 | 2 | map queued | 20 | 127 | 0 / 0 |
| 7 | 2 | publication | 24 | 145 | 0 / 0 |
| 8 | 1 | stage prepared | 24 | 77 | 0 / 0 |
| 8 | 1 | map queued | 24 | 126 | 0 / 0 |
| 8 | 1 | publication | 28 | 145 | 0 / 0 |
| 9 | 2 | stage prepared | 28 | 78 | 0 / 0 |
| 9 | 2 | map queued | 28 | 127 | 0 / 0 |
| 9 | 2 | publication | 32 | 145 | 0 / 0 |
| 10 | 3 | stage prepared | 32 | 126 | 0 / 17 |
| 10 | 3 | upload helper entry | 36 | 126 | 0 / 17 |
| 10 | 3 | upload armed | 37 | 0 | 0 / 17 |
| 10 | 3 | map queued | 37 | 61 | 17 / 17 |
| 10 | 3 | publication | 38 | 145 | 17 / 17 |
| 11 | 4 | stage prepared | 38 | 129 | 0 / 17 |
| 11 | 4 | deadline miss | 43 | 74 | 0 / 17 |

Residuals remain: this comparison does not certify capture agreement, exact hardware timing, or deadlines.

- Supported first-publication through first-miss cases only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated.
- Map and tile pixel contents at initial publication are not captured or certified.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
