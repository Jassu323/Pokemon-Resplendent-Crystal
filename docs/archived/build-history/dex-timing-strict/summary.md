# Selected Dex Timing Experiment

**Status: UNCALIBRATED. Not a timing certification.**

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Validated 1 linked asset sets; ran 1 bounded scenarios.
Model animation misses: 0. Model audio underruns: 0.
These counts describe the configured model, not observations of this ROM in SameBoy.

## Measured Instruction Paths

T-cycles below exclude interruptions unless stated. Normal speed: 4,194,304 T/s; 70,224 T/display interval.

- Eight-block audio refill: 17,096 T (cache-wrap fixture).
- 32-block prefill body: 68,136 T; excludes cry setup/arming.
- Sample timer interrupt: 1,464 T including hardware entry.
- Map publication: 1,124 CPU T + 896 GDMA T; outer VBlank work excluded.

## Per-Species Summary

Startup is only the measured animation CPU component, NOT selection/paging latency. Warm means the first-event dictionary target and first stage are prepared, not necessarily the full dictionary.

| Species | Tiles (base + tail) | Max 6-tile decode service T | Max new-stage T | Cold startup CPU intervals | Misses / cases |
|---|---:|---:|---:|---:|---:|
| chikorita | 25 + 24 | 9,088 | 11,904 | 1.29 | 0 / 1 |

## Model Boundaries

The current compact schedule advances by producer calls; deadlines advance by display intervals. That mismatch is modeled, not corrected.
CPU decoding and gathering run during visible scanout too. Only VRAM access/publication is constrained by the modeled display windows.
Audio cache count increases after each decoded block, not after an imaginary instantaneous refill.
HDMA advances while interrupts execute; interrupt time is not blindly added to the whole transfer train.
Stops at the first missed animation deadline. Audio behavior after that miss is not simulated.
Time-accounting wait entries are elapsed intervals that INCLUDE interrupt and DMA time; they must not be summed with CPU totals.

Historical Weavile/Luxray captures are retained with their original bytes. Their ROM hash is unknown, so they are observations, not calibration. A phase sweep matching an observed frame does not establish the actual phase or explain missing CPU time.

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
