# Selected Dex Host Timing Model

> Historical pre-consolidation record, preserved 2026-09-21.
> Build identities and dated measurements below remain evidence; old "current"
> statements and commands are not current checkout instructions. See the
> [archive index](README.md) and [maintained guide](../../dex_timing_model.md).

## Status and Scope

The dated [scheduler investigation and final-review record](dex_scheduler_investigation.md)
preserves the Weavile/Luxray measurements, evidence identities, failure chains,
proposed runtime fix direction, unresolved limitations, and acceptance checklist.
Use that record for the final decision review; this document describes the host
model and its current behavior. Neither document signs off a runtime fix.

The [boundary investigation](dex_timing_boundary_investigation.md) preserves the
history of source-supported IRQ, HALT, PPU and DMA corrections. As of September
20 they are consolidated into the normal linked `OwnerReplay`; the old boundary
probe is now a parameter-sweep wrapper, not a separate hardware implementation.

The [full-sequence results](dex_full_replay_results.md) and subsequent
[actual-state end-to-end validation](dex_end_to_end_capture_results.md) reproduce
nine complete Selected animation/cry continuations against the independent
SameBoy core, matching **5,400,595 non-HALT instruction starts** in time and
registers. Luxray, Weavile and Dusknoir use actual initial volatile-memory
fixtures. Weavile and Dusknoir additionally match all four user-measured stops
from publication through cry stop and stable completion, with zero T-cycle or
captured-state differences. The other six species retain documented synthetic
extensions of partial captures in that historical run, not live continuations.

The subsequent [Garchomp finishing investigation](dex_garchomp_finishing_results.md)
adds the user's six further sampled-species starting states and an independently
calibrated continuation for each. Those 4,092,809 new instruction comparisons
raise actual-initial-state coverage to all nine sampled species (5,608,137 matching
instruction starts including the existing three). Exeggcute's synth-start state
was preserved at that stage; the subsequent headroom/synth work below adds its
full calibrated continuation.
The explicit `--actual-states` finishing option selects the expanded set;
historical partial controls remain reproducible rather than being overwritten.

The older Luxray Pass 4 partial fixture retains its +8-T residual, and the older
Weavile partial fixture retains its boundary qualification. Their newer fully
specified runs are exact; they do not retroactively identify the missing detail
in those different old runs. The older aggregate `model.py` explorer and
ROM quota validator remain uncalibrated timing estimates; the linked replay's
stronger validation does not transfer automatically to them.

The [scheduler policy experiment record](dex_scheduler_policy_experiments.md)
adds a separate counterfactual runner over this linked baseline. Existing work
routines still execute, while hypothetical scheduling decisions carry explicit
CPU-time charges. Its candidate results are not instruction-exact predictions
of unimplemented runtime code. The record includes failed controls, dispatch
cost sensitivity, synthetic timer-phase sweeps, and remaining publication and
decode/upload admission problems. The game has not been changed or rebuilt.

The subsequent [publication-budget investigation](dex_publication_budget_results.md)
adds physical-VBlank critical-write/OAM audits, independent hardware-map checks,
quiet-OAM ownership controls, and linked branch/prefix bounds. Its best policy
passes 192 synthetic timer-phase continuations, but the report explicitly
retains a failing widened-window control and the late-publication branch that
prevents treating the candidate cutoff as a universal safe rule. These are
host-only feasibility experiments, not changes to the calibrated baseline.

The [steady-display recovery follow-up](dex_steady_publication_results.md) adds
`recovery_experiment.py`: a costed Selected viewport-ownership route, bounded
publication admission, deliberate late-entry controls, and broader partial-state
continuations. It closes the candidate's critical-write bound under that contract,
but deliberately retains a Garchomp 20/30-tile counterexample to the eight-tile
suffix heuristic. Successful timing does not excuse an incorrect fallback map.
Canonical initial graphics for incomplete captures are explicitly synthetic;
they do not replace actual-memory calibration or prove live runtime correctness.

`finish_experiment.py` extends that counterfactual with measured gather/queue
costs, a bounded ready-remainder upload, and early submission before retained
bookkeeping. All nine actual nominal runs pass, but one timer-phase control and
two high-overhead settings retain Garchomp misses. The linked timer's post-cry
104-T return path is costed separately from active playback. See the finishing
record for the entry contract, full-chain bounds, negative controls, and why this
is not yet a general scheduler signoff. No runtime source was changed.

`queue_experiment.py` adds a private instruction-image experiment on top of
`early-budget`, documented in the [queue-construction results](dex_queue_construction_results.md).
Only two fixed-row copy helpers and four CALL operands differ in that in-memory
image. Both backing and owner maps, publication, audio and diagnostics remain.
Actual counted queue cost falls from 12,596 to 9,380 T; the tested phase/cost
counterexamples close without changing a cartridge file. Patch manifests and
private-image hashes distinguish it from unchanged-ROM calibration. The
remaining hypothetical scheduler decision costs still require a concrete runtime
implementation and validation; the private helper proof does not validate them.

The [headroom/synth follow-up](dex_headroom_synth_results.md) adds
`gather_experiment.py` and the `tile-unrolled` queue-experiment mode. A private
replacement unrolls the fixed 16-byte tile copy, preserving tile readiness and
upload payloads. `--finish-margin-t` adds an explicit minimum conservative
finishing reserve without changing an operation's measured bound. Both the
4,096-T and 8,192-T matrices pass; 8,192 T is the recommended next pre-flight
setting. The document preserves the larger-reserve negative control and the
separate, unchanged publication-window bound.

`OwnerReplay` now accepts Exeggcute's captured slow timer configuration and
audits its active synthesized cry through completion. `sound_registers.py`
implements only the CPU-visible register masks, read-only status, DAC controls
and triggers required by that path, rejecting unsupported sweep, length-clock,
power-transition and active-wave-read behavior. It is not a waveform/APU model.
The unchanged-ROM baseline matches all 385,586 SameBoy instruction starts;
the actual-state calibration total is now 5,993,723. Candidate controls preserve
sound-engine cadence, ordered hardware writes and cry-channel completion frames.
This does not establish all synthesized cries or cancelled/paged audio behavior.

This is a **host-side diagnostic**, not a new game scheduler and not a hardware
timing certification. It does not add or change ROM code/data, WRAM, HRAM, VRAM,
runtime instrumentation, sampled-cry settings, animation scripts, or CPU speed.
The existing quota-based asset validators remain in place. They are structural
checks, not evidence of enough execution time; do not replace them with this
model's verdict until the model is calibrated against SameBoy.

The current model pins these contracts:

- Normal-speed CGB: 4,194,304 T-cycles/second, 456 dots/line, 154 lines/interval.
- Six dictionary tiles per independent compressed stream; up to 20 gathered tiles per upload.
- 96 **tail** tiles of startup lead, plus the dimension-dependent base tiles,
  bounded by the dictionary and raised when the first stage needs more.
- Two frame slots with independent residency. The displayed slot cannot be overwritten.
- Normal-pitch sampled cries: 200 timer ticks/block, 32-block prefill, eight-block refill.
- The current compact micro-schedule advances by **service calls**, not display time.
- Publication uses authored deadlines and a single VBlank transaction. The
  aggregate experiment stops at its first miss. The linked replay offers both
  first-miss and full animation/cry completion, without hiding underruns.

Double speed, battle, New Dex Entry and the party Stats Screen are out of scope.

## Running It

For the pinned full linked replay, without rebuilding the game, use the
[host-core build and replay commands](dex_full_replay_results.md#identity-and-reproduction).
The short command, after building that host executable, is:

```sh
env PYTHONPATH=tools python3 -B -m dex_timing.full_replay \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --output build/dex-full-replays --jobs 8
python3 -B tools/test_dex_timing.py
```

Full reports contain all later misses, authored/actual publication intervals,
cry-stop reason, per-call operation spans, core comparisons, and provenance.
"Full sequence" includes the main animation, base hold and idle animation;
cleanup elapsed time is reported separately, not used as animation duration.

The commands below instead run the broader, still-uncalibrated aggregate audit.

From the repository root:

```sh
make test-dex-timing
make verify-dex-timing
```

The verification target builds the existing normal ROM if necessary, then runs
the host audit using up to eight processes. The ordinary `make` target is unchanged.
There are no third-party Python dependencies.

For a smaller run:

```sh
python3 -B tools/verify_dex_timing.py audit \
  --species weavile luxray dusknoir metagross bastiodon rampardos \
  --jobs 8 --output build/dex-timing-stress
```

Default coverage is all linked species/forms, cold/warm/paging, native audio and
an audio-disabled comparison for sampled species, eight initial mainline LY
phases, and two traversals of looping timelines. It is a bounded sweep, **not**
an exhaustive search of every dot, timer phase, input sequence or infinite loop.

Generated files, ignored by Git:

- `build/dex-timing/summary.md`: readable costs, coverage and limitations.
- `build/dex-timing/report.json`: per-stream, per-stage, per-offset costs and simulation events.
- `build/dex-timing/manifest.json`: ROM, symbols, covered sources, tools and asset hashes.
- `build/dex-timing/sameboy_capture.md`: build-specific debugger addresses and capture directions.

Reports are always labeled **UNCALIBRATED**. Per-scenario statuses are `MODEL_MISS`
or `UNVALIDATED_NO_MISS`, never `PASS`. `--strict` exits 2 while uncalibrated;
the ordinary audit exits 0 when the diagnostic run succeeds, even if it predicts
misses. Invalid assets, unsupported instructions and inconsistent inputs exit 1.

`--reference-manifest PATH` rejects changes to a previously pinned input set.
Always rebuild before measuring a changed checkout. Hashes establish identity,
not proof that independently copied ROM/symbol/source files belong together.
Linked-byte and output checks provide additional mismatch detection.

## What Is Measured

`tools/dex_timing/cpu.py` is a small, fail-closed instruction-path counter for
isolated linked routines. It executes supported SM83 instructions against fixture
memory and counts their documented T-cycles. It is **not a Game Boy emulator**:
there is no LCD, sound, timer, interrupt controller, OAM or DMA emulation in it.
Hardware accesses other than explicitly permitted fixture registers fail.

This avoids assigning a single optimistic cost to every compressed chunk. The
actual opcode path accounts for compression commands, taken branches, farcalls,
copies, source order and the linked temporary trace instructions. The host
reference decoder and reconstructed maps independently check resulting bytes.

The measured catalogue includes:

- Every independent LZ stream, including base pictures, partial final chunks,
  repeats, bit reversals, reverse copies and overlapping references.
- Dictionary-service wrappers and bank switching.
- Every frame's new-stage construction in both slots, plus resident/base event paths.
- Tile gathering at every possible upload offset, checked against decoded data.
- Map backing/staging/queue work and the publication handler's software portion.
- Actual pair-lookup refill paths for one through eight and 32 blocks, including
  ring-buffer wrap, per-block cache publication, and independent output checking.
- The sample timer and short LCD STAT handlers, including their linked vector
  jumps and 20-T hardware entry costs: 1,452/1,480 T for sample playback and
  108 T for the `hLCDCPointer = 0` LCD path.
- The no-input owner-loop prefix, stage-turnover/return paths, schedule-run
  reloads, and audio-service wrapper. These are executed fixtures, not fitted
  per-species penalties.
- The owner's four footer STAT polls, retained as clock-dependent operations
  between real instruction boundaries. Eight no-input blink/text/cursor-state
  paths are counted; `owner_variant` selects one without fitting a new cost.
- The complete owner return through the unfinished-stage deadline check and
  trace, wait-flag store, `DelayFrame` HALT/NOP/flag-test loop, audio service,
  and return to the main loop. The wake branches cost 56 T after VBlank or
  36 T after another interrupt, before the separately counted service/loop.
- Selected-page VBlank fixtures with OAM enabled and sampled sound active:
  2,764 T idle, 3,304 T queued-but-not-due, and 4,212 T publishing. Publication's
  896-T GDMA cost is additional. The HRAM OAM wait is counted once, not added
  again as a separate CPU halt.

Trace comparisons timestamp the actual LY reads, not the later stores into the
debug buffer. Fixtures that write JOYP can explicitly retain released-button
read values; ordinary RAM writes do not model the JOYP input multiplexer.

The instruction counter has unit tests and checks actual routine output, but it
still requires independent timing calibration. Counting instructions correctly
does not establish how often a routine is called or what interrupts surround it.

## Asset Validation

Discovery follows the linked `INCBIN` lists, not a hard-coded species count.
All linked frontpic, frame-plan, timeline and schedule bytes must match generated
files. Each compressed dictionary must reproduce `front.animated.2bpp` exactly.
Each frame plan must reconstruct its padded 7x7 tilemap and contain valid, sorted
tail sources and the correct high-water mark. Timeline/schedule loops must point
to record boundaries. Unknown/reserved encodings fail instead of being skipped.

The existing sampled-cry verifier remains complementary:

```sh
make verify-sampled-cries
```

It checks all selector/header combinations and cry assets; the new microbench
additionally executes the linked decoder/refill instructions on controlled data.

## Display-Time Experiment

`model.py` keeps CPU work separate from wall time. VBlank, mode-0 LCD STAT, and
the sample timer can interrupt work. The observed `IE = $0f`, mode-0-enabled
STAT, and `hLCDCPointer = 0` require the short LCD interrupt even though it does
not modify the display. It requests service on visible scanlines, not VBlank
lines. Requests continue while IME is clear and coalesce in IF; pending service
priority is VBlank, LCD, then timer. This is not a flat 108-T charge added to
every scanline regardless of masking.

HDMA moves one block per eligible visible HBlank while the
mainline polls; interrupts can execute during the transfer train, and their time
is not blindly added to its entire elapsed duration. The modeled helper enforces
its real `LY < 128 - tile_count` launch test. A 20-tile request arriving too late
can therefore roll into the following display interval.
The final VBlank line's early `LY = 0` is distinguished from physical line zero:
STAT remains mode 1 there. HDMA may be armed during that interval but still
cannot transfer blocks until a visible HBlank.

The owner no longer jumps directly from a producer call to the next VBlank in
the model. It runs the return path and arms the real wait first. If VBlank has
already occurred before that store, the new wait requires the following one.
LCD/audio interrupts can wake HALT without satisfying the wait. Footer STAT
reads and deadline/flag reads occur at their instruction's data-read point;
interrupts do not split those instructions. Bulk stage and producer work still
uses aggregate interrupt timing, as noted below.

The event model tracks decoded prefixes, two-slot residency, upload offsets,
queued maps, authored publication deadlines, producer-call count, audio-cache
consumption and progressive refill publication. It preserves the current
call-clock/display-clock mismatch so a missed service opportunity is visible.
The mainline unfinished-stage underrun and a late VBlank publication are
distinct outcomes. A deferred, already-queued map does not itself execute the
underrun breakpoint. Both outcomes can make a scenario `MODEL_MISS`.

Cold and paging begin without dictionary warming. Warm means the **current first
event's target and first stage** are prepared; it does not assume every species'
whole dictionary is resident. Once the same initial state is reached, the modeled
animation pipeline is the same. This does **not** imply equal selection/paging UI
latency. Startup reports only measured animation CPU components, with omitted
transition, basepic transfer, cry-arm/prefill and wait time explicitly listed.

Measured owner, VBlank, and audio-wrapper fixtures are charged by default.
Additional unspecified external work is set to zero and listed as **unknown**,
not certified free. This isolates the measured paths without claiming their
fixtures cover every runtime branch.
It uses the long end of the documented HBlank-start envelope, 369 dots; this is
not a claim that every selected-screen scanline has that exact mode-3 duration.
Nor is that profile guaranteed to maximize every end-to-end delay: changing
phase can move a wait across VBlank or change the next producer opportunity.
For a source-derived Selected-page comparison, use
`--profile tools/dex_timing/fixtures/selected_no_input.json`. Its 257-dot HBlank
start is 80 mode-2 dots + 172 minimum mode-3 dots + the five discarded pixels
from `POKEDEX_SCX = 5`. The Selected transition clears OAM and hides the window
with `WX = $a7`; frontpic/footprint/caught-symbol tiles are BG. This is a
normal-layout assumption to validate, not a captured per-line PPU trace.
The hardware basis is [Pan Docs' rendering description](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md).
An exploratory profile can vary the assumed workload without changing the game:

```json
{
  "hblank_dot": 252,
  "lcd_stat_enabled": true,
  "audio_phase_t": 12800,
  "outer_loop_t": 0,
  "vblank_other_t": 0,
  "vblank_dispatch_t": 0,
  "service_extra_t": 0,
  "refill_wrapper_t": 0
}
```

Pass that file with `--profile`. Workload zeroes mean no *additional* cost beyond
the measured fixtures, not conservative upper bounds. `audio_phase_t` is the
time from first publication's modeled VBlank start to the next timer request;
its default full-period value is unmeasured. The actual cry arms before the
first map publication. `audio_played_at_publication` explicitly accounts for
blocks already consumed then; the five-stop Weavile capture establishes four,
instead of the older default assumption of one. Do not fit these numbers solely to make a recorded
miss appear. Measure or derive the omitted paths, then explain any residual.
Profiles cannot remove uncertainty warnings or enable a calibrated verdict.

Important current limitations:

- Owner input and changes of blink/text/cursor state, state-dependent VBlank
  transfers/synth sound, non-idle producer bookkeeping and uncommon audio/loop
  branches are not fully bounded. The measured no-input/idle fixtures are not
  universal upper bounds. In particular, timer/cache-wrap costs are not a
  reconstruction of each captured read/write address.
- Initial mainline and audio-timer phase are not inferred from the screenshot.
- Instruction boundaries, polling alignment and real PPU mode timing are modeled
  approximately in the clock layer, not at emulator fidelity.
- An audio result ends at the first animation miss, since the real underflow-map
  path would alter subsequent execution. It is not a full-cry pass in that case.
- The final timeline stop/base-map cleanup and external entry transition are not
  part of the modeled visual-event budget.
- Counter-clock comparisons assume events remain inside the runtime's signed
  8-bit deadline horizon. Newly generated events outside it must be rejected.
- Wait totals already include time spent servicing interrupts and DMA; they must
  not be summed with CPU-only category totals as though disjoint.

## SameBoy Calibration

Use the generated `sameboy_capture.md`, not breakpoint addresses from an old
reply. It starts with Weavile/Luxray first-miss captures, then warm/paging and
Dusknoir/Metagross/synth controls. It reuses version-6 instrumentation already in
the ROM. No new runtime instrumentation has been added by this host tool.

`trace` imports the 139-byte debugger dumps, orders the ring, handles counter
wrap, and reports per-phase elapsed intervals with +/-455-T scanline uncertainty.
Those are elapsed times including IRQs/waits, not pure instruction counts.
`--rom-sha256` together with `--report` binds the observation to the measured ROM
and rejects mismatches. Without that explicit association, it remains unbound.

The checked-in Weavile/Luxray fixtures preserve the user-supplied raw bytes and
the observed producer-gap/idle-run failures. Their original ROM hash was not
recorded. They are regression fixtures for trace interpretation, **not calibration
of the current image**. Predicting some miss, or matching one phase in a sweep,
is not equivalent to explaining the observed first miss.

For the six newer, build-bound captures, retain the original report and write
corrected results to a separate directory:

```sh
python3 -B tools/verify_dex_timing.py audit \
  --species weavile luxray --jobs 2 --output build/dex-timing-lcd
python3 -B tools/verify_dex_timing.py compare \
  'weavile=/absolute/path/Weavile - Test 1.txt' \
  'luxray=/absolute/path/Luxray - Test 1.txt' \
  --report build/dex-timing-lcd/report.json \
  --baseline build/dex-timing/report.json \
  --rom-sha256 <verified-capture-ROM-hash> --output build/dex-timing-lcd
```

Repeat the `species=path` argument for each capture. `comparison.json` preserves
input hashes, deduplicated observations, component timings, first-miss states,
and the initial timer-phase sweep. `comparison.md` summarizes them. Independent
component phase envelopes sweep three dot positions, both HBlank extremes, and
200 timer phases. They are **not an exhaustive bound or one coherent replay**.
Overlapping all component observations is necessary evidence, not sufficient
calibration. A match must also explain the initial state and service-call history.

The owner-wait revision can be tested independently of the worst-case HBlank
profile. Preserve the earlier reports and generate a normal-layout report:

```sh
python3 -B tools/verify_dex_timing.py audit --species weavile luxray --jobs 2 \
  --profile tools/dex_timing/fixtures/selected_no_input.json \
  --output build/dex-timing-owner-selected
python3 -B tools/verify_dex_timing.py followup \
  '/absolute/path/Weavile Follow-Up Capture.txt' \
  --report build/dex-timing-owner-selected/report.json \
  --rom-sha256 <verified-capture-ROM-hash> \
  --output build/dex-timing-owner-selected
```

`followup` imports the five named stops, checks both timer clocks against the
display counter, recognizes LY zero in mode 1 as physical line 153, and compares
four consecutive intervals. It derives initial audio consumption from the dump,
sweeps the captured timer-phase bound and all eight no-input owner fixtures,
and reports whether **one replay** fits all four intervals. It does not pick
the best matching state separately at each stop and claim a coherent replay.
This focused fixture currently requires the complete dictionary to be loaded
and the next event to be the first miss, as in the Weavile capture.

### Capture-Seeded Linked Owner Replay

`followup` additionally runs `replay.py` against the same five-stop Weavile
capture. This is a deliberately narrow calibration path, not a replacement
for the broad asset/phase model and not another runtime scheduler. It starts
from the first publication's captured RAM, retains that state continuously,
and executes the linked owner, stage constructor, two idle producer calls,
audio refills and interrupt handlers through the first underrun breakpoint.
Later dumps are comparisons only, never inputs that reset the running state.

It includes actual nonzero/full trace counters, normal and interior cache-address
branches, state-dependent VBlank housekeeping, the four footer polls, the
`DelayFrame` return/wait path, and instruction-boundary interrupt delivery.
PC observations precede pending interrupt delivery, matching the captured
producer entry with LCD IF set. Disabled joypad IF is retained as irrelevant
to delivery because IE is `$0f`. Clock-sensitive data reads occur within the
instruction; HALT wakes remain on the CPU's four-T grid.

Both timer readings must agree with **one** initial divider low byte and timer
phase across all five stops. The TIMA overflow/reload delay is included. Merely
fitting four independent elapsed-time ranges does not count as a match.
The report also compares LY/mode, the software display counter, enabled IF bits,
all 27 animation-state bytes, audio counts, and compressed/read/write pointers.

For ROM `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`,
the preserved fixture `tools/dex_timing/fixtures/weavile_owner_followup.txt`
has one matching sampled initial state out of 512 compatible with the first
stop's timer readings. Its consecutive elapsed
times are 37,468 / 30,144 / 6,128 / 105,380 T versus captured timer-derived
nominals of 37,504 / 30,144 / 6,080 / 105,408 T. All differences fit the
observations' +/-63 T uncertainty. This is **CAPTURE_CONSISTENT**, not proof of
cycle-exact emulation, a universal phase guarantee, or sufficient runtime budget.

The original aggregate experiment remains visible in the same report, including
its residual mismatch. Do not mistake its conservative fixture costs for a
precise replay of each actual cache address or trace counter. The original
Weavile case contains no HDMA upload. The extension below covers Luxray's first
upload with the linked scanline, mode and completion polls.
No ROM rebuild, new instrumentation, or resource allocation is involved.

To preserve the preceding results, write the new comparison to
`build/dex-timing-linked-owner` using the existing normal-layout report.

The matching Weavile stage-entry to producer-entry interval decomposes into
19,308 T of mainline instructions (19,180 for stage preparation and 128 for the
caller return), three 1,452-T sample interrupts, and sixty 108-T short LCD
interrupts: exactly 30,144 T. No new dictionary decode, VRAM upload or audio
refill occurs within that leg. This distinguishes CPU stage construction and
interrupt overhead from HDMA waiting, rather than blaming them interchangeably.

### Luxray Continuous Follow-Up

The preserved `tools/dex_timing/fixtures/luxray_owner_followup.txt` adds the same
five stops plus the initial owner/VBlank state. At publication, timer IF is
already set and TIMA is `$38`; the replay must deliver this pending request as
well as schedule subsequent requests, without counting the initial request twice.
The captured text-delay counter is 5, not a choice between the earlier 0/1
fixtures. Known owner fields are used directly; only unknown divider/timer phase
is swept. The replay still seeds memory only once, at publication.

The host now executes the real HDMA helper's launch and completion loops.
It schedules one 16-byte transfer per visible HBlank, updates FF55's remaining
count, and charges 32 T of CPU suspension per block. Transfers and interrupt
requests advance on the same clock; the whole transfer's elapsed wait is not
added a second time to its interrupt cost. This is the bounded transfer model
described by [Pan Docs](https://gbdev.io/pandocs/CGB_Registers.html#transfer-timings),
not SameBoy's full sub-instruction DMA/bus-arbitration implementation. That
distinction remains a limit, especially near a scanline boundary.

The linked replay explicitly keeps the LCD on. This iteration loaded the
already-decoded dictionary from independently validated ROM assets for fully
preloaded cases. The subsequent partial-prefix extension is described below.
It does not claim to reconstruct uncaptured initial tilemaps, pixels, sprite
fetches, or per-line mode lengths. Cancellation, overlapping DMA and non-LDH
HDMA launches fail closed.

For the same ROM hash as above, one compatible initial state uses publication
time 600 T, timer phase 560 T modulo 12,800 T, and DIV low byte `$ec`. The pending
sample request therefore precedes the publication stop by 40 T. All five stops
match LY/mode, display counter, enabled IF, all 27 animation-state bytes, audio
counts, and compressed/read/write pointers. One shared divider phase also
explains every captured DIV/TIMA pair.

| Interval | Captured nominal T | Replay T | Difference T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 37,440 | 37,428 | -12 |
| Stage Entry -> Producer Entry | 25,792 | 25,760 | -32 |
| Producer Entry -> Frame Wait | 5,184 | 5,232 | +48 |
| Frame Wait -> First Miss | 1,936,512 | 1,936,524 | +12 |

These are all within +/-63 T (about 0.015 ms). The first stage leg is 17,220 T
of construction plus 128 T of caller return, two 1,452-T audio interrupts and
51 short 108-T LCD interrupts: 25,760 T. No decompression or VRAM upload occurs
in that leg.

This is not byte-identical trace replay: at the final stop seven trace bytes
differ by one scanline, representing one stage-entry timestamp and the six
timestamps of one idle producer record. No event, quota, progress or schedule
byte differs there. The report lists trace differences separately rather than
hiding them inside a core-state match. Initial publication's dot, fixed HBlank
length, DMA arbitration and intermediate interrupt/poll alignment remain bounded
model assumptions, not measured per-instruction hardware facts.

The matched execution provides a specific failure chain:

1. First frame wait is reached at LY 141 before VBlank, unlike Weavile's initial
   lost interval. The early Luxray path is not stalled there.
2. The schedule deliberately idles for call indices 0..8. Call 9 reaches the
   17-tile transfer helper at LY 126. The helper requires LY below 111 for that
   length, so it waits into interval 10; upload completes after the intended
   interval-10 publication. The model publishes that frame at interval 11.
3. Preparing event 7/frame 2 begins in interval 22. Construction and the caller's
   remaining work cross VBlank before DelayFrame is re-armed. The following
   producer opportunity is then in interval 24 instead of interval 23.
4. At interval 28 the producer consumes schedule action 26, still an idle.
   The two upload actions at indices 27 and 28 have not executed when the
   interval-29 deadline check fires. The stage has 0/21 tiles uploaded even
   though all 134 dictionary tiles are decoded; audio has 87 cached blocks.

The failure is not evidence that those 21 tiles cannot fit anywhere in the
available seven-interval hold. Work release is late and the call-index cursor
stays behind elapsed display time. A runtime redesign still needs to separate
the display clock from completed work, permit early safe preparation, and model
the latest usable upload windows. Simply advancing/discarding schedule actions
would silently discard unfinished work and is not a fix.

Reproduce with `followup --species luxray` and the fixture above, using a fresh
normal-layout audit report under `build/dex-timing-luxray-owner`. Keep the older
Weavile report intact; re-run its fixture into a separate output directory.
No new capture or video is needed for these two first-miss cases. The next
extension adds partially decoded initial state, without yet establishing ongoing
dictionary production in the observed interval.

### Dusknoir And Bastiodon Continuous Follow-Ups

The corresponding `*_owner_followup.txt` fixtures preserve the supplied full
captures. `Frame Miss` is accepted as a label alias only at the linked underrun
PC. Replay seeds only the captured decoded prefix, validating total count,
completed compressed-stream boundary, source bank/address and WRAM destination
against the asset. Unproduced dictionary bytes are not seeded.

Both begin with 145 decoded tiles. Dusknoir still has 102 tiles undecoded and
Bastiodon 68 at the first miss. Neither performs additional dictionary decoding
between publication and this miss; these runs cover heavy construction/uploads
with partial initial state, not concurrent decoder progress.

Reports now use the 139-byte trace as an additional constraint on already
core/timer-compatible initial phases. Dusknoir has three fully trace-compatible
candidates out of 64, and its selected example matches all five stops. A report
with no passing candidate shows the closest timer-compatible state comparison
but keeps `RESIDUAL_MISMATCH`.

That distinction matters for Bastiodon: all four elapsed legs fit within +/-63 T,
but the default publication origin leaves Producer Entry in mode 3 with no LCD
request, versus captured mode 0 and a pending LCD request. All animation/audio
progress agrees. A separately tested eight-T publication-origin adjustment
matches all core/timer/trace state without changing operation costs. The origin
is not directly captured, so the default is unchanged and this is explicitly a
sensitivity test, not a new calibrated per-species offset.

Both cases prepare the second stage across VBlank, then consume idle actions
behind the display clock. The first 20-tile upload reaches its helper too late,
waits into the deadline interval, and leaves 20/32 or 20/37 tiles complete when
the miss is checked. The needed dictionary prefixes, 111 and 121 tiles, are
already available. These failures do not establish inadequate decoding throughput.

Full timing tables, phase counts, construction/interrupt decomposition, remaining
limitations and the unchanged proposed fix are preserved in the
[investigation record](dex_scheduler_investigation.md#dusknoir-and-bastiodon-extension-2026-09-19).
Reproduce with a four-species `audit --species weavile luxray dusknoir bastiodon`
and `followup --species dusknoir` or `--species bastiodon`, using the matching raw
fixture, ROM hash and report. Current generated reports are under
`build/dex-timing-expanded-owner/`, with a subdirectory per species. The separately
named origin-sensitivity unit test preserves the boundary experiment without
altering default comparison verdicts.

### Five Additional Continuous Follow-Ups

Garchomp, Rampardos, Rayquaza, Kyogre, and Metagross now have preserved raw
fixtures and linked replay support. No operation costs or hardware timing rules
were changed for this extension. The five-species executed-output audit passes,
and the host regression suite has 113 tests.

Rayquaza and Kyogre each match all five core/timer observations and all trace
bytes for permitted initial phases. Garchomp retains a Frame Wait scanline/mode
boundary residual; Rampardos and Metagross also retain elapsed/joint-timer
residuals. A comparison with no timer/interval-compatible candidate now shows a
clearly labeled diagnostic candidate rather than an empty example; that is
never counted as a passing replay.

All five reproduce the captured missed event and tile progress, with no new
dictionary decoding before that miss. Kyogre's ten-tile transfer begins legally
and completes before its target VBlank, but subsequent map preparation misses
the queueing opportunity. This explicitly tests the difference between transfer
completion and publication-ready state. The fixed upload cutoff alone does
not budget the whole deadline path.

See the [five-species findings](dex_scheduler_investigation.md#five-additional-species-2026-09-19-results)
for timings, state residuals, scope limits, and unchanged fix direction.
Reports are under `build/dex-timing-five-species/<species>/followup.{json,md}`.
Reproduce using a five-species audit and one `followup` per matching raw fixture.

For the six earlier captures, the `compare` command also accepts
`--hblank-dots 257 369`. It reports both phase sweeps separately. HBlank 369 is
a deliberately pessimistic display configuration, not the expected BG-only
Selected page; it must not silently replace the layout-specific comparison.
An old/new report comparison using different profiles is labeled as such.

Before this becomes the timing authority:

1. Bind new captures to the generated manifest and confirm normal CPU speed.
2. Match decode, gather, map-build, queue and HDMA phase timing; separate actual
   instruction work from interruption/wait time.
3. Explain the first missed event and service-call history for Weavile and Luxray.
4. Measure/bound remaining owner-loop and interrupt paths. If the current trace
   cannot distinguish them, propose focused instrumentation separately.
5. Re-run stress/control paths and expand phase coverage. Keep failures explicit.
6. Only then propose runtime changes and consolidate redundant quota validators.

## Hardware References

The hardware constants and instruction timing conventions are based on
[Pan Docs rendering](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md),
[CGB DMA registers](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md),
[interrupt requests and priority](https://github.com/gbdev/pandocs/blob/master/src/Interrupts.md),
and the [SM83 opcode tables](https://github.com/gbdev/gb-opcodes).
The focused replay's timer phase uses the documented
[overflow/reload delay](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md);
its hardware-read placement follows the
[SameBoy CPU implementation](https://github.com/LIJI32/SameBoy/blob/master/Core/sm83_cpu.c).
The cost of this project's routines is counted from the linked ROM, not inferred
from an unrelated game's implementation.
