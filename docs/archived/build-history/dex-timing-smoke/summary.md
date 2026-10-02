# Selected Dex Timing Experiment

**Status: UNCALIBRATED. Not a timing certification.**

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Validated 4 linked asset sets; ran 72 bounded scenarios.
Model animation misses: 33. Model audio underruns: 0.
These counts describe the configured model, not observations of this ROM in SameBoy.

## Measured Instruction Paths

T-cycles below exclude interruptions unless stated. Normal speed: 4,194,304 T/s; 70,224 T/display interval.

- Eight-block audio refill: 17,096 T (cache-wrap fixture).
- 32-block prefill body: 68,136 T; excludes cry setup/arming.
- Sample timer interrupt: 1,464 T including hardware entry.
- Map publication: 1,124 CPU T + 896 GDMA T; outer VBlank work excluded.

## Per-Species Summary

Startup is only the measured animation CPU component, NOT selection/paging latency. Warm means a fully prepared dictionary and first stage.

| Species | Tiles (base + tail) | Max 6-tile decode service T | Max new-stage T | Cold startup CPU intervals | Misses / cases |
|---|---:|---:|---:|---:|---:|
| dusknoir | 49 + 198 | 15,724 | 25,556 | 3.89 | 9 / 18 |
| luxray | 49 + 85 | 13,464 | 32,912 | 3.43 | 9 / 18 |
| metagross | 49 + 48 | 10,456 | 15,340 | 2.12 | 3 / 18 |
| weavile | 49 + 79 | 9,928 | 21,636 | 3.29 | 12 / 18 |

## Model Boundaries

The current compact schedule advances by producer calls; deadlines advance by display intervals. That mismatch is modeled, not corrected.
CPU decoding and gathering run during visible scanout too. Only VRAM access/publication is constrained by the modeled display windows.
Audio cache count increases after each decoded block, not after an imaginary instantaneous refill.
HDMA advances while interrupts execute; interrupt time is not blindly added to the whole transfer train.
Stops at the first missed animation deadline. Audio behavior after that miss is not simulated.
Time-accounting wait entries are elapsed intervals that INCLUDE interrupt and DMA time; they must not be summed with CPU totals.

## Still Required Before Runtime Changes

- owner-loop/input work outside the measured routines.
- outer VBlank dispatch, OAM DMA and sound workload.
- producer non-idle branch/wrapper and schedule-loop overhead.
- audio service wrapper and source-borrow/cache-boundary branches.
- sample timer phase at first publication.
- HDMA polling alignment and interrupt-entry instruction granularity.
- cold/warm/paging UI preparation and reveal outside animation priming.
- Match component timings and first-miss events against build-bound SameBoy captures.
- Reconcile any model/measurement discrepancy before treating a no-miss scenario as evidence.
- Expand the phase/loop sweep as needed; finite sampling is not a universal deadline proof.
