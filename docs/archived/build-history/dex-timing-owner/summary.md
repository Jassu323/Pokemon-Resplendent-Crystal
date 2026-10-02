# Selected Dex Timing Experiment

**Status: UNCALIBRATED. Not a timing certification.**

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

Validated 2 linked asset sets; ran 96 bounded scenarios.
Model animation misses: 87. Model audio underruns: 0.
Scenarios with late publication: 0 (can overlap the miss counts).
These counts describe the configured model, not observations of this ROM in SameBoy.

## Measured Instruction Paths

T-cycles below exclude interruptions unless stated. Normal speed: 4,194,304 T/s; 70,224 T/display interval.

- Eight-block audio refill: 17,096 T (cache-wrap fixture).
- 32-block prefill body: 68,136 T; excludes cry setup/arming.
- Sample timer interrupt: 1,480 T including vector JP and hardware entry.
- Short LCD STAT interrupt: 108 T including vector JP and hardware entry.
- Idle sampled-playback VBlank fixture: 2,764 T including OAM wait and housekeeping.
- Inner map publication: 1,124 CPU T + 896 GDMA T.

## Per-Species Summary

Startup is only the measured animation CPU component, NOT selection/paging latency. Warm means the first-event dictionary target and first stage are prepared, not necessarily the full dictionary.

| Species | Tiles (base + tail) | Max 6-tile decode service T | Max new-stage T | Cold startup CPU intervals | Misses / cases |
|---|---:|---:|---:|---:|---:|
| luxray | 49 + 85 | 13,464 | 32,912 | 3.43 | 39 / 48 |
| weavile | 49 + 79 | 9,928 | 21,636 | 3.29 | 48 / 48 |

## Model Boundaries

The current compact schedule advances by producer calls; deadlines advance by display intervals. That mismatch is modeled, not corrected.
CPU decoding and gathering run during visible scanout too. Only VRAM access/publication is constrained by the modeled display windows.
Audio cache count increases after each decoded block, not after an imaginary instantaneous refill.
HDMA advances while interrupts execute; interrupt time is not blindly added to the whole transfer train.
LCD mode-0 requests continue while interrupts are masked, coalesce in IF, and use VBlank > LCD > timer priority.
A late publication is recorded separately; the underrun breakpoint is the mainline unfinished-stage check.
Stops at the first missed animation deadline. Audio behavior after that miss is not simulated.
Time-accounting wait entries are elapsed intervals that INCLUDE interrupt and DMA time; they must not be summed with CPU totals.

Historical Weavile/Luxray captures are retained with their original bytes. Their ROM hash is unknown, so they are observations, not calibration. A phase sweep matching an observed frame does not establish the actual phase or explain missing CPU time.

## Still Required Before Runtime Changes

- owner input/blink state and actual per-line PPU mode lengths beyond the no-input fixtures.
- VBlank state-dependent transfers, timer rollover and active synth sound beyond the idle fixture.
- producer non-idle branch/wrapper beyond the idle and schedule-reader fixtures.
- audio source-borrow/cache-boundary branches beyond refill fixtures.
- sample timer phase and blocks already consumed at first publication unless captured.
- HDMA polling alignment and interrupt-entry instruction granularity.
- cold/warm/paging UI preparation and reveal outside animation priming.
- Match component timings and first-miss events against build-bound SameBoy captures.
- Reconcile any model/measurement discrepancy before treating a no-miss scenario as evidence.
- Expand the phase/loop sweep as needed; finite sampling is not a universal deadline proof.
