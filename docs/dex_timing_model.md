# Selected Dex Host Timing Tools

Maintained guide, updated 2026-09-21. Runtime behavior is defined in the
[Selected scheduler reference](pokedex_animation_scheduler.md), and accepted
build hashes/results are in the [validation guide](dex_scheduler_validation.md).
The [pre-consolidation model history](archived/dex-scheduler/dex_timing_model_history.md)
retains the original measurements, calibration progression and old commands.

## Choose The Right Tool

| Tool | Purpose | Required inputs / limits |
| --- | --- | --- |
| `tools/test_dex_scheduler.py` | Execute current linked scheduling/ownership contracts and verify finishing tables | Current root ROM, symbols and generated assets; hardware registers are frozen unit fixtures |
| `dex_timing.finish_bounds` | Check conservative admission inequalities against current tables | Current link; checks bounds, not an end-to-end animation |
| `tools/test_dex_cold_listing.py`, `tools/test_dex_target_regression.py` | Host audit/parser negative controls | Maintained host source; not game playback tests |
| `dex_timing.cold_listing` | Boot the real SameBoy core, navigate with normal inputs and audit cold entry through completion | SameBoy source, boot ROM, C compiler, matching game assets and prepared battery save |
| `tools/test_new_dex_entry.py` | Current-link resident mappings, publication bounds, diagnostics and owner/register contracts | Current ROM/symbols; frozen-register unit fixtures, not a hardware emulator |
| `dex_timing.new_entry` | SameBoy catch-through-registration, exact events, VRAM/pixels, description changes and early exit | Compatible frozen pre-catch fixtures with manifests; local SameBoy source and C compiler |
| `dex_timing.new_entry_sweep` | Twenty-species display-interval input matrix with real A/B events | Current-link authentic registration checkpoints and explicitly generated extra-species fixtures |
| `dex_timing.new_entry_phase_sweep` | Synthetic timer/VBlank phase stress, separate from real-input acceptance | Same checkpoints; changes only the first TIMA write in the headless core, not ROM or producer state |
| `OwnerReplay` / `IntegratedReplay` | Instruction-level continuation and component timing from a specified initial state | Matching ROM/symbols/assets and captured or explicitly constructed state; scope depends on that fixture |
| `full_replay`, policy/queue/finishing experiments | Reproduce the earlier failure chain and counterfactual controls | Frozen historical link and named local fixtures; not alternative game schedulers |
| `verify_dex_timing.py audit` / `model.py` | Original aggregate cost/scheduling explorer | Historical service-call scheduling assumptions; deliberately uncalibrated, not a current runtime acceptance gate |
| `tools/test_dex_timing.py` | Historical model/capture regressions | Some tests require the frozen reference link and local captured state |

The game no longer consumes a compact micro-schedule. It releases useful work
on the hardware display clock, tracks completion independently, and publishes
on authored deadlines. Descriptions of service-call-index scheduling in the
archive and aggregate explorer refer to the old implementation. Advancing a
display clock does not itself guarantee a task fits before publication.

## Current Checks

From the repository root:

```sh
make -j8 pokecrystal.gbc
make verify-dex-animations
python3 -B tools/test_dex_scheduler.py
python3 -B tools/test_dex_cold_listing.py
python3 -B tools/test_dex_target_regression.py
PYTHONPATH=tools python3 -B -m dex_timing.finish_bounds \
  --output build/dex-scheduler-integrated/finish-bounds.json
```

These checks do not require an ignored one-off integration script or the user's
save states. Building still requires the repository's normal toolchain.
The contract suite checks all 399 generated assets, first/later dictionary
targets, work-choice combinations, complete-ready finishing, counter wrap,
timer/audio limits, quiet ownership, cancellation and publication bounds.

The normal-input cold runner is the maintained way to reproduce current entry
and full-animation acceptance. See [setup and invocation](dex_cold_listing_results.md#reproduce).
It copies inputs into its output directory, uses real D-pad/A/B events and does
not inject producer RAM or alter the source save. The all-species run intentionally
fails Drapion's static-reveal check while its animation/audio checks pass.
Preserve that distinction in reports.

New Dex Entry uses its own adapter rather than a second bespoke hardware model.
The linked instruction counter checks publication costs/fault fixtures; the
real SameBoy core checks full owner execution, PPU timing and audio. Commands,
fixtures and miss breakpoints are in [the registration test guide](dex_new_entry_testing.md#current-implementation-test).
Its ordinary probes do not replace runtime production with a host policy or inject
owner state. Original fixture saves remain read-only; generated reports and
screenshots are ignored build products.

For a bounded registration instruction trace, set both
`REGISTRATION_INSTRUCTION_FROM_T` and `REGISTRATION_INSTRUCTION_TO_T` when
running the compiled `new-entry-trace` probe. Values are decimal T-cycles from
the loaded entry state; the start is inclusive and end exclusive. For example,
4,084,000 through 4,092,000 captures the restored Master Ball Dusknoir collision.
The optional `instruction` records include PC/bank/opcode, registers, IME,
IE/IF, LY/STAT, DIV/TIMA/TMA/TAC, owner, flags and audio counts. This is strictly
host instrumentation: physical-memory observations do not advance the emulated
clock or change game state. Leave both variables unset for ordinary runs.
See the [timer collision diagnosis](new_dex_entry_regression_results.md#timer-collision-diagnosis)
for a verified trace-on/trace-off comparison and why fixed entry-state input
sweeps do not exhaust possible interrupt phases.

The separate phase sweep requests `REGISTRATION_TIMER_FIRST_CLOCKS=1..200` on
the compiled trace probe. At audio startup it replaces only the first TIMA write
while TAC is disabled; it validates the expected TMA reload and leaves subsequent
timer periods untouched. This is explicitly synthetic input to the hardware core,
not read-only instrumentation and not an actual captured phase. The 200-clock
no-op reproduces the ordinary trace, excluding its one injection record. The
64-T grid does not exhaust 4-T instruction phases or all entry CPU/PPU states.
Leave that variable unset for ordinary replays. The driver records the ROM,
source/core, checkpoint and injection identities separately from the input suite.
`--all-input-modes` additionally tests description advance and early exit for
every sampled species, rather than only Dusknoir (9,600 rather than 3,600 runs
for the current sixteen sampled fixtures).

Publication auditing accepts LY=0 only when STAT still reports VBlank mode 1:
SameBoy models the LY reset during physical line 153. It rejects modes 0/2/3 at
LY=0. Frozen-LY bounds separately check every VRAM destination and last-store
cost, while full-core pixel/map checks verify the actual displayed result.

New Entry's description audit snapshots the old VRAM rectangle and complete
new backing rectangle without bus reads, then compares all 91 cells and their
rendered pixels on every display. Only wholly old or wholly new is accepted;
partial presentation and later reversion fail. Latency is anchored to the A
input, not return from the rendering/wait routine. Historical ROMs without the
new ready label use the instruction immediately after the page-render farcall
as that observation point. No game code is patched by the observer.

Display events retain raw CPU callback time in `t` and record exact PPU boundary
time in `ppu_t`. SameBoy's `GB_advance_cycles` advances the CPU clock through a
whole batch before its display state machine consumes it. At the normal-frame
callback, `display_cycles` is the remainder in 8 MHz units; subtracting it from
the callback clock gives the actual boundary. The current audit requires exact
70,224-T spacing on that field, not a widened CPU-clock jitter tolerance.
Two Yanmega synthetic phase-182 description cases exposed a six-T callback
variation; all previous execution events remain identical after adding the
read-only PPU observation. See the current New Entry regression report.

## What The Models Measure

`cpu.py` executes supported linked SM83 instructions against controlled memory
and counts T-cycles. It checks output as well as cost and fails on unsupported
instructions or hardware access. Alone it is not a Game Boy emulator: it does
not supply an LCD, interrupt controller or complete audio device.

`OwnerReplay` adds the explicitly modeled hardware paths required for Selected
playback: instruction-boundary interrupt delivery, timer overflow/reload,
HALT/wait behavior, scanline/STAT reads, DMA waits and publication auditing.
`IntegratedReplay` executes the linked scheduler rather than substituting a
hypothetical policy. Independent SameBoy comparisons validate specific complete
continuations; they do not certify every possible initial state or bus behavior.

Relevant costs include linked decoder paths, taken branches, bank switches,
stage construction, gathering, backing/owner map copies, queueing, timer/LCD/
VBlank interrupts, and the return through the owner wait/audio loop.
CPU instruction cost and elapsed wall time are different: a transfer wait can
already include IRQ service and must not be charged again as an independent
sum. A transfer completing is also not the same as a map being publication-ready.

The model's validated Selected scope is normal-speed CGB. The current game uses
six-tile independent dictionary streams, up to 20 gathered tiles per regular
upload, a 96-tail-tile startup lead, two independently resident slots, 32 audio
prefill blocks and eight-block refills. The runtime's conservative finishing
contract includes a separate 8,192-T reserve. Read its full conditions in the
[scheduler cost model](pokedex_animation_scheduler.md#finishing-cost-model);
none of these quotas alone proves deadline feasibility.

Synthesized-audio replay models the CPU-visible registers, DAC controls and
triggers needed by its captured paths, not a full APU waveform. Unsupported
sound behavior fails closed. The normal-input SameBoy runner uses the actual
core, but its acceptance checks still are not subjective listening tests.

## Linked Replay And Fixture Discipline

A replay starts from one specified state and continues without replacing it
with later captures. Later dumps are observations to compare, not checkpoints
used to force agreement. Preserve input hashes, capture provenance, timer/PPU
phase assumptions, actual versus synthetic memory and all residual mismatches.

The integrated replay can relocate a settled initial state by executing the
new link to build its own call/interrupt stack, while retaining captured
asset/audio/viewport data. Its guards reject moved RAM, incompatible asset
content or relocated data pointers. This does not measure cold startup or
input-to-reveal latency. Do not weaken a guard merely to reuse an old state.

In particular, the old `integrated_replay --reference` unchanged-target recipe
rejects the later dictionary-target correction as an asset mismatch. The
recorded target-integration run used already-relocated current-link starts and
actual save-state fixtures instead. Its local
`build/dex-target-integration-20260920/verify_integration.py` was a one-off
driver, not a checked-in fresh-checkout entry point. Retain its written results,
not a promise that the ignored script is available to every contributor.
For a future linked replay, capture matching starts and explicitly adapt the
host fixture/driver if needed; current normal-input testing does not need those
old private starts.

Current linked-contract and normal-input suites are complemented by historical
evidence, not replaced by it. The 18-species target matrix and earlier
instruction-exact comparisons are recorded under
[compiled target regression](archived/dex-scheduler/dex_target_regression_results.md#compiled-integration)
and the [archive index](archived/dex-scheduler/README.md).

## Historical Reproduction

The original failure-model link has ROM SHA-256
`7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`.
A local frozen checkout, ROM, symbols, map and generated assets were preserved
under `build/dex-scheduler-reference-20260920/`. This directory is ignored and
not distributed. Actual-state/core comparisons additionally require their
documented memory exports/save states and a matching SameBoy source/core.

Only when those prerequisites are present:

```sh
PYTHONPATH=tools DEX_TIMING_REFERENCE_ROOT=build/dex-scheduler-reference-20260920 \
  python3 -B tools/test_dex_timing.py
```

The recorded historical suite passed 197 tests. That environment variable is
the test module's reference-root selector, not a universal switch for every
experimental tool. Follow each archived report's own build/fixture instructions.
Do not run historical commands against the newest link and interpret their
result as a current scheduler verdict.

The old `make test-dex-timing` and `make verify-dex-timing` targets remain
legacy diagnostic entry points. Prefer the explicit current checks above.
The aggregate audit labels reports **UNCALIBRATED**, with `MODEL_MISS` or
`UNVALIDATED_NO_MISS`, never a calibrated pass. Normal audit exit 0 means the
diagnostic ran, not that animation passed; strict mode rejects an uncalibrated
verdict. Its old compact-schedule assumptions are not the current runtime.

## Captures And Reporting

Use the [current debugger guide](dex_scheduler_validation.md#sameboy-debugging),
not the archive's numeric breakpoints. Verify the ROM/symbol hash before a
capture; re-resolve labels after relinking, especially instrumentation removal.

For a new failure, retain species, entry route, input context, the first-publication
state when requested, each numbered miss, final state and the matching ROM/
symbol/core identity. `ticks` resets SameBoy's cycle counter; `ticks keep`
reads it without resetting. Record `lcd` state because LY alone does not fully
specify PPU phase. Video for visual durations must be uninterrupted and separate
from debugger pauses.

A useful result distinguishes:
- Structural correctness and decoded output from time-budget feasibility.
- Authored hardware intervals from startup and cleanup elapsed time.
- Actual-state core agreement from phase/cost counterfactuals.
- Natural cry completion from cache exhaustion or intentional cancellation.
- Logical UI return from palette/text/transition presentation correctness.

## Artifact Policy And Limits

Keep reusable source, tests, small reference fixtures and curated Markdown
findings in the repository. Keep copied ROMs/saves, volatile state exports,
compiled host cores, screenshots, traces and generated reports under ignored
`build/`. Historical local paths are provenance, not portable dependencies.

Finite replay coverage is not a universal proof for every future species,
input sequence or hardware phase. New data still needs structural and timed
checks. Double speed, New Dex Entry, Party Stats and battle owners need their
own workload/ownership analysis. The next owner audit is
[New Dex Entry](dex_new_entry_testing.md); Selected telemetry is not valid
simply because a different owner reuses its RAM addresses.

## Hardware References

Instruction timing and modeled hardware behavior are grounded in
[Pan Docs rendering](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md),
[CGB DMA](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md),
[interrupts](https://github.com/gbdev/pandocs/blob/master/src/Interrupts.md),
[timer overflow/reload](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md),
the [SM83 opcode tables](https://github.com/gbdev/gb-opcodes), and the
[SameBoy CPU implementation](https://github.com/LIJI32/SameBoy/blob/master/Core/sm83_cpu.c).
Project operation costs come from this project's linked instructions, not
another game's implementation. Historical comparisons pin the SameBoy commit
in their provenance rather than assuming a moving master branch is identical.
