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
