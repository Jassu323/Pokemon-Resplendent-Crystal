# Owner-Loop Follow-Up

**PARTIAL_NOT_CALIBRATED**

Species: weavile; HBlank start: dot 257.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings.

| Interval | Captured ms (+/- 0.015 ms) | Predicted range ms |
|---|---:|---:|
| Publication -> Stage Entry | 8.942 | 8.810-8.925 |
| Stage Entry -> Producer Entry | 7.187 | 7.132-7.235 |
| Producer Entry -> Frame Wait | 1.450 | 1.445-1.496 |
| Frame Wait -> First Miss | 25.131 | 25.112-25.796 |

Matching first-miss states: 768/768.
Single replays inside all four timer bounds: 0/768.
These are finite phase/owner-state samples, not probabilities or a proof.

## Limits

- Captured timer phase is bounded, not measured to a CPU cycle.
- All eight no-input owner states are swept; their exact state was not captured.
- Constant HBlank profile is not a reconstruction of per-line PPU behavior.
- Timer/refill use conservative fixtures, not exact cache-address paths.
- Stage/producer instructions still use aggregate IRQ timing.
- The first undelayed publication origin is a fixture, not a measured IRQ-entry timestamp.
- Agreement of separate leg ranges does not imply one jointly matching replay.

## Capture-Seeded Linked Replay

**CAPTURE_CONSISTENT**

Joint state/timer matches: 1/512 sampled initial states.
This supplementary replay executes the actual linked owner, stage, idle-producer, refill and interrupt instructions.
It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.
The captured later states do not drive the replay. One initial state runs through all five stops.

| Interval | Captured nominal T | Linked replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37504 | 37468 | -36 |
| Stage Entry -> Producer Entry | 30144 | 30144 | +0 |
| Producer Entry -> Frame Wait | 6080 | 6128 | +48 |
| Frame Wait -> First Miss | 105408 | 105380 | -28 |

All four differences fall within the timer's +/-63 T observation uncertainty.
Example initial phase: 696 T; owner variant 0; initial DIV low byte: 36.
Executed interrupt costs, T (including entry/vector): {'vblank': [2780], 'lcd': [108], 'timer': [1452, 1472]}.

This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee.

- Weavile first publication through first miss only, not full animation coverage.
- One capture-seeded memory state; later stops are comparisons, not re-seeding points.
- No-input owner fixture and fixed HBlank profile, not captured per-line pixels.
- Linked CPU and IRQ execution share the instruction counter, not an independent emulator.
- Unknown DIV low byte and timer/owner phase are swept, not measured.
- The bulk all-species model retains conservative/aggregate component fixtures.
