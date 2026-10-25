# Host Boundary Timing Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Current status: the [end-to-end capture results](dex_end_to_end_capture_results.md)
validate the ordinary linked model against actual Weavile/Dusknoir initial
states through completion, without species-specific timing adjustments. All
four measured checkpoints match exactly. The dated stages below preserve the
earlier boundary investigation and its partial-state qualifications.

2026-09-19. Host-only diagnostic work; no game code, ROM, scheduler, memory
allocation, or captured dump was changed. The default replay is deliberately
unchanged pending the cross-capture check described below.

Latest update: the [independent SameBoy-core replay](#independent-sameboy-core-replay)
matches all 159,711 executed non-HALT instruction starts in the corrected host
probe. Both retain the exact-cycle Luxray capture's eight-T final residual.
This is a synthetic-state cross-check, not a captured save-state replay.

## Scope And Reference

This investigates the remaining Garchomp, Rampardos, and Metagross residuals
from [the five-species comparison](dex_scheduler_investigation.md#five-additional-species-2026-09-19-results).
The experiment executes the same linked instructions and capture-seeded state
as the existing replay. It changes hardware-boundary assumptions, not per-species
instruction costs or authored deadlines.

The installed SameBoy app identifies itself as 1.0.3. The local reference source
is `SameBoy` commit `eb4c47ebf58cf93261620bfe138b650979f94049`, described as
`v1.0.3-2-geb4c47e`. Its two post-release commits concern save-state masking.
This is a source reference, not proof of the exact internals/configuration of
the installed executable. The synthetic reference probe explicitly uses CGB-E,
normal speed, SCX 5, WX 167, WY 0, LCDC `$e3`, and mode-0 STAT interrupts.

Build identities remain:

```text
ROM  7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
SYM  1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
```

The ROM in `/Applications/SameBoy/Games` still matches the repository ROM.

## Concrete Model Omissions

The reference is local source, primarily `Core/sm83_cpu.c:1629`,
`Core/memory.c:1907`, and `Core/display.c:2107`.

1. **Interrupt acknowledgment:** the old replay removes IF at the start of
   interrupt entry. SameBoy re-evaluates priority during entry, then clears the
   selected IF bit near its end. The probe selects at 16 T, clears at 18 T,
   and reaches the vector at 20 T. A new request for an already-pending source
   can coalesce before acknowledgment; it must not automatically become a
   second handler call. One extra short LCD handler costs 108 T here.
2. **HALT wake:** the CGB halted CPU samples requests and advances a four-T
   halted step before entering a selected interrupt. The previous replay
   advanced to the request boundary but omitted this final wake step.
3. **DMA overhead:** a reference-core probe measured 36 T for one 16-byte
   burst and 452 T for a continuous 14-block transfer. The old replay charges
   32 and 448 T respectively. SameBoy's transfer routine has two T before the
   bytes and two T after, in addition to 32 T per block at normal speed.
4. **DMA execution boundary:** an HBlank request is not an instantaneous
   mid-instruction transfer. In this reference implementation, the transfer
   is serviced around opcode fetch; interrupt entry can precede it. The final
   probe separates the scheduled request from executing the DMA burst.
5. **PPU register boundaries:** LY changes, STAT mode changes, and the STAT
   request are not one simultaneous event. The BG-only reference probe finds
   mode 0 one T before its interrupt, with the HDMA request another T later.
   The early LY-zero transition on physical line 153 needs separate treatment.

These small differences can change how many polling-loop iterations execute,
which interrupts coalesce, or which VRAM-access window is reached. Consequently,
a few T of missing overhead can produce a whole-scanline difference downstream.
This is not evidence that a species' assembly operation itself has acquired a
different instruction cost.

## Controlled Experiments

The progression matters. PPU/HALT corrections alone did not resolve all three
residuals. Interrupt acknowledgment plus HALT could match Rampardos, but adding
the DMA overhead changed that result again. The combined request/execution DMA
model then matched all three new cases. An isolated match is not sufficient.

The combined experiment uses the same 606-T publication origin for every
species, with compatible timer phases on the corresponding two-mod-four grid.
That is a sensitivity setting informed by the boundary investigation, **not a
newly captured IRQ-entry timestamp**. The previous model's origin was 600 T.
Do not treat either as an exact measurement or fit a separate operation cost
for each species.

The five-stop replay starts from the first dump only; later dumps are never
re-seeded. A full match requires all core animation/audio state, LY/STAT/IF,
one jointly consistent DIV/TIMA phase, every elapsed-time bound, and all 139
trace bytes at every stop. Captured elapsed values still have +/-63 T uncertainty.

| Species | Full matches at common origin 606 T | Result |
|---|---:|---|
| Garchomp | 1 | All five stops and traces match |
| Rampardos | 3 | All five stops and traces match |
| Metagross | 1 | All five stops and traces match |
| Dusknoir | 4 | All five stops and traces match |
| Bastiodon | 9 | All five stops and traces match |
| Rayquaza | 8 | All five stops and traces match |
| Kyogre | 4 | All five stops and traces match |
| Weavile | 0 | One LY boundary remains at Frame Wait |
| Luxray | 0 | Early elapsed-time/hardware-state residuals remain |

Counts describe compatible candidates, not pass probabilities or independent
test repetitions. All candidates for a species use the same captured initial
memory state, apart from the already documented missing owner-state fixture
choices in the oldest Weavile capture.

| Species | Publication -> stage | Stage -> producer | Producer -> wait | Wait -> first miss |
|---|---:|---:|---:|---:|
| Garchomp captured | 37,440 | 43,520 | 3,648 | 283,648 |
| Garchomp probe | 37,464 | 43,524 | 3,680 | 283,604 |
| Rampardos captured | 37,440 | 48,576 | 5,120 | 208,448 |
| Rampardos probe | 37,464 | 48,600 | 5,132 | 208,416 |
| Metagross captured | 36,928 | 15,808 | 3,712 | 3,002,304 |
| Metagross probe | 36,964 | 15,824 | 3,672 | 3,002,296 |

The three previously failing cases now fit every observed interval. This does
not establish cycle-exact hardware validation: the timer observations are
quantized, and the initial IRQ/PPU phase is not yet measured directly.

### Cross-Capture Limits

At origin 606 T, Weavile's Frame Wait falls at modeled physical line 153,
dot 2, just one T before this reference's early LY-zero transition. The capture
reads LY zero. All trace bytes, elapsed bounds, and joint timers otherwise match.
Nearby-origin experiments (including 604 and 608 T) can fully match it. That
shows sensitivity, not authorization to assign a different origin to Weavile.

Luxray is the stronger remaining counterexample. The combined probe's selected
606-T diagnostic has elapsed legs `[36964, 25868, 5232, 1936880]` versus captured
`[37440, 25792, 5184, 1936512]`. Stage entry is one line early. Sweeping the
origin from 600 through 616 T in two-T increments did not produce a full match.
Do not promote the combined probe to the default model or call all nine cases
calibrated while this remains unresolved. Nor should the older Luxray model's
partial agreement be used to justify dropping source-supported boundary costs.

A read-before-write audit also identified uncaptured housekeeping state:
game-time counters/cap, overworld delay, input-disable state, and display shadow
registers. Controlled single-candidate variations changed some timing, but did
not establish any of these as the actual cause. For example, the linked
`GameTimer` costs 272 T normally and 328 T on a seconds rollover. No guessed
housekeeping value has been installed in the default replay.

All AF/BC/DE/HL values at the four post-publication stops matched the original
replay for the three new residual cases. Together with the matching dictionary,
stage, and audio state, that supports a timing-boundary investigation rather
than a new register-corruption diagnosis.

## Reproduction

The exploratory probe is preserved separately from the default model:

```sh
python3 -B tools/dex_timing/probes/boundary_sensitivity.py \
  --species weavile luxray dusknoir bastiodon garchomp rampardos rayquaza kyogre metagross \
  --origins 606 --variants deferred --jobs 9 \
  --output build/dex-boundary-comparison.json
```

`base`, `ppu`, `halt`, `ack`, `ack-halt`, `ack-ppu-halt`,
`ack-ppu-halt-gdma`, and `ack-ppu-halt-gdma-burst` retain the intermediate
sensitivity experiments. Only `deferred` contains the complete combination
described above. These are investigation variants, not competing game schedulers.

`tools/dex_timing/probes/sameboy_boundaries.c` is the independent PPU/DMA
reference probe. It initializes a synthetic CGB-E core and never loads a ROM,
save, or save state. It can be compiled with the local SameBoy Core sources
(excluding debugger, symbol/disassembler, rewind, and cheat source files) and
the corresponding `GB_DISABLE_*` definitions. It prints DMA duration and
LY/STAT/IF transitions against a steady-state VBlank reference.

The existing 113 host tests passed unchanged. No runtime build was performed.

## Effect On The Scheduler Diagnosis

The concrete game failures remain the same: late service/launch opportunities,
unfinished VRAM uploads, and post-upload map preparation missing publication.
The tested corrections do not supply missing dictionary tiles, remove the
observed misses, or show that normal-speed hardware is incapable of meeting
the authored timings with a different scheduling policy.

The [recorded fix direction](dex_scheduler_investigation.md#proposed-fix-direction)
still stands. The immediate task is to finish calibrating the host's boundary
behavior before relying on it to certify that replacement scheduler.

## Luxray Exact-Cycle Follow-Up

The user supplied `Luxray - Pass 4.txt`, preserved verbatim as
`tools/dex_timing/fixtures/luxray_exact_followup.txt`:

```text
SHA-256 86979830ef8702f48fc762c11a6d03ebcdf8eb29e8f389081889efe4cebf3d0d
```

This is one continuous cold-entry five-stop run on the unchanged build. It
includes the requested debugger cycle counters and full `lcd` output at every
stop. The separate extra initial housekeeping dumps were not included. Do not
claim those fields were captured, or replace unknown values with invented data.
No further user capture is requested for this pass.

The first `ticks` reports then resets 71,629,084 T; that value is not elapsed
animation time. The subsequent `ticks keep` counts are cumulative from that
reset: 36,964, 62,940, 68,280, and 2,004,924 T. Every Absolute 8MHz count is
exactly twice the corresponding T count, consistent with the captured normal
CPU speed. The exact intervals also agree with the independently inferred
DIV/TIMA bounds.

### Starting Phase Is Now Constrained

The first LCD dump reports physical line 145, VBlank, and `Sleeping (300 cycles
to next event)`. The synthetic reference-core probe, with the same CGB-E,
normal-speed, SCX/WX/LCDC assumptions, produces that state at **606 T after the
VBlank request**. The previously selected 606-T origin is therefore independently
supported for this capture, not selected to make its elapsed intervals fit.
This does not retroactively measure the origin of older captures.

`sameboy_boundaries.c` now prints this specific reference state as well as its
previous boundary/DMA observations. The installed emulator's exact model/build
and uncaptured PPU state remain limits of this source-reference comparison.

### Replay Result

The existing combined `deferred` probe, without changing its operation costs,
produces this comparison at origin 606, timer phase 658, DIV low byte 16, and
owner variant 0:

| Interval | Exact captured T | Probe T | Difference |
|---|---:|---:|---:|
| Publication -> Stage Entry | 36,964 | 36,964 | 0 |
| Stage Entry -> Producer Entry | 25,976 | 25,976 | 0 |
| Producer Entry -> Frame Wait | 5,340 | 5,340 | 0 |
| Frame Wait -> First Miss | 1,936,644 | 1,936,652 | +8 |

All captured animation/audio state, enabled IF bits, LY/mode, display counters,
joint DIV/TIMA readings, and every 139-byte trace match at all five stops. Later
capture dumps are comparisons only, never re-seeded into the replay. The search
checks 64 initial timer/DIV candidates compatible with the first capture;
**none matches all four exact intervals**, so the verdict remains
`RESIDUAL_MISMATCH`, not a timing pass.

The remaining eight T equal about 1.91 microseconds or 0.018 scanlines. This is
far smaller than the earlier whole-scanline disagreement. It is still a real
model discrepancy now that exact counters are available, not something to hide
under the old +/-63-T observation tolerance. An explicit regression test retains
the `[0, 0, 0, +8]` result.

A separate `deferred-halt` experiment checks SameBoy's behavior when an interrupt
request arrives during the HALT instruction itself: that case re-fetches HALT
after the interrupt instead of taking the usual halted wake step. Its results
are unchanged for this capture. This edge case does **not** explain the remaining
eight T, and is not installed in the default model.

Reproduce the two diagnostic variants with:

```sh
python3 -B tools/dex_timing/probes/boundary_sensitivity.py \
  --species luxray \
  --capture tools/dex_timing/fixtures/luxray_exact_followup.txt \
  --origins 606 --variants deferred deferred-halt --jobs 2 \
  --output build/luxray-exact-boundary-comparison.json
```

The host parser now recognizes an initial `ticks` reset followed by four
`ticks keep` observations. It validates the paired clocks and timer bounds,
then requires exact intervals rather than +/-63 T. Old captures without clock
outputs retain their original bounds. Partial/mis-reset or inconsistent exact
clock sequences are rejected.

### Effect On Diagnosis And Next Work

At the same first underrun check, event 7 requires frame 2, containing 21 upload
tiles, and the upload offset remains zero. All 134 dictionary tiles are decoded,
and the sampled-cry cache contains 87 blocks. This is still the same work-release
and upload scheduling failure, not missing dictionary bytes or an empty audio
cache. Fixing a few host cycles would not provide the missing upload work.

No subsequent-miss capture or video is currently needed. The new data are enough
to retain the eight-T residual explicitly and audit the remaining host
interrupt/wait/polling boundaries before promoting the probe. The missing
housekeeping fields must remain an initial-state uncertainty if they become
relevant. This result does not establish why every older Luxray run differed,
close Weavile's separate LY-boundary residual, or certify complete animations,
concurrent late-dictionary decoding, and other entry paths.

No runtime ASM, ROM, default hardware replay, or memory allocation changed.
All 120 host tests pass, including the new exact-clock parser checks and the
explicit eight-T residual regression. The archived capture and supplied file
have identical hashes; the repository and installed game ROMs still match.

## Independent SameBoy-Core Replay

The user refreshed the local SameBoy master checkout during this investigation.
This pass uses clean commit `213a12ce93d66b105a113debd9396306066a7cfc`.
Compared with the earlier `eb4c47e` reference, the changes are in Cocoa document
atomic execution/battery handling and Workboy weekday reporting. The CPU,
display, memory/DMA, and timer source used for this comparison is unchanged.
The installed app still identifies itself as 1.0.3; a source reference does not
prove its exact build configuration.

### Method

Three explicitly host-only probe files support the check:

- `probes/export_core_fixture.py` exports the host's constructed initial CPU,
  RAM/HRAM, bank selection, verified dictionary prefix, and reconstructed stack.
- `probes/core_replay.c` loads the pinned ROM read-only into the local SameBoy
  core, warms a CGB-E PPU to the initial captured LCD phase, injects that synthetic
  memory state once, and executes the actual ROM through all five stops.
- `probes/compare_core.py` compares the snapshots and optionally every executed
  non-HALT instruction's time, ROM bank, and PC. HALT waiting is reflected in
  elapsed time; repeated idle CPU polls are not counted as instructions.

This is **not** a game boot, a complete captured emulator state, or pixel-output
validation. It never reads a user battery save, changes the ROM, or re-seeds a
later observation. Uncaptured OAM/pixel buffers remain zeroed. The caller stack
is constructed by executing the linked owner path, not copied from the user's
stack dump. Normal speed, LCDC `$e3`, SCX 5, WX 167, WY 0, and short mode-0 STAT
interrupts remain explicit assumptions supported by the capture/code.

An initial probe-fixture mistake was found and corrected before accepting the
comparison: zeroed `hSCX`/`hWX` shadows were copied into the hardware by VBlank.
The exporter now retains the captured screen configuration in those shadows
without mutating the host replay. This corrects the reference's rendering
positions from pixels 81/65 to the captured 82/66. It does **not** remove the
eight-T residual. A `--zero-scroll-shadows` negative control preserves that
earlier fixture for comparison. These are host-fixture edits, not game HRAM edits.

### Result

At origin 606, timer phase 658, DIV low byte 16:

| Interval | User capture T | Corrected host probe T | Independent core T |
|---|---:|---:|---:|
| Publication -> Stage Entry | 36,964 | 36,964 | 36,964 |
| Stage Entry -> Producer Entry | 25,976 | 25,976 | 25,976 |
| Producer Entry -> Frame Wait | 5,340 | 5,340 | 5,340 |
| Frame Wait -> First Miss | 1,936,644 | 1,936,652 | 1,936,652 |

**All 159,711 executed non-HALT instruction starts match between the host probe
and the independent core, including their elapsed T, ROM bank, and PC.** This
includes the linked owner, preparation/gather/upload paths, cry servicing,
interrupt handlers, and waits, rather than only comparing the five endpoints.
It is not a claim that every CPU register or pixel matches between implementations.

The independent core also matches all captured animation-state bytes, all 139
trace bytes at each stop, audio counts/pointers, display counters, LY/mode,
enabled IF bits, and DIV-high/TIMA. PPU detail provides another check: the first
two rendering stops are pixels 82 and 66, and Frame Wait is OAM entry 15/40,
exactly as captured. At the final stop the synthetic core is at OAM entry 25/40
instead of the capture's 21/40, consistent with being eight T later. Therefore
the discrepancy is not merely a rounded or misinterpreted debugger counter.

A separate search runs all 64 initially compatible DIV/timer combinations
with each of four divider subphases, totaling 256 independent-core runs:

| Cumulative timing differences across the five stops, T | Runs |
|---|---:|
| `[0, -12, -12, -12, +480]` | 64 |
| `[0, 0, 0, 0, +8]` | 144 |
| `[0, +440, +440, +440, -432]` | 48 |

None matches all four exact intervals. These counts describe synthetic initial
states, not probabilities. Do not choose a different operation cost, subtract
eight T, or widen the exact comparison to manufacture a passing verdict.

### Assessment And Remaining Gap

For this constructed state, the corrected host operation/boundary execution now
has an independent implementation cross-check. There is no evidence here of an
omitted large stage, upload, decode, interrupt, or wait cost. The remaining
capture discrepancy points toward incomplete starting state or reference/app
configuration, but no particular byte or setting has been proven responsible.
Matching a synthetic run is not proof that the starting state matches the user.

The existing runtime diagnosis remains unchanged: at Luxray's event-7 miss,
frame 2 needs 21 upload tiles, its uploaded offset is zero, all 134 dictionary
tiles are decoded, and the cry cache contains 87 blocks. Eight T cannot account
for that unperformed upload. The proposed hardware-clock/dependency/early-work
fix direction in the main investigation record remains applicable; no runtime
change has been made or authorized by this host result.

To close the final discrepancy, the next useful evidence is **one complete
SameBoy emulator save state at the first publication**, plus the first-miss
exact clock result from that same run. More repeated partial byte dumps or
another video would leave the same initial-state uncertainty. A battery `.sav`
is not sufficient. Keep the same ROM. Stop at `$77:$5ea5`, reset `ticks`, save
an emulator state while stopped, and then collect `ticks keep`/`lcd` at the
first `$a0:$67fc`. Use an unused state slot so an existing state is not replaced.
No intermediate three-stop dumps, new instrumentation, or full species suite
are needed for that focused check.

The default replay remains unchanged. The old Weavile early-LY residual and
older Luxray capture qualifications remain open; this focused Luxray result
does not silently mark them resolved. Full-animation, late-dictionary decode,
and other entry-path coverage also remain separate acceptance gates.

### Reproduction And Verification

From the repository root, using the local SameBoy source (no game rebuild):

```sh
clang -O2 -std=c11 -I../SameBoy \
  -DGB_INTERNAL -DGB_DISABLE_DEBUGGER -DGB_DISABLE_REWIND \
  -DGB_DISABLE_CHEATS -DGB_DISABLE_CHEAT_SEARCH -DGB_DISABLE_TIMEKEEPING \
  '-DGB_VERSION="boundary-probe"' \
  tools/dex_timing/probes/core_replay.c \
  ../SameBoy/Core/{apu,camera,display,gb,joypad,mbc,memory,printer,random,rumble,save_state,sgb,sm83_cpu,timing,workboy}.c \
  -o /private/tmp/dex_core_replay
python3 -B tools/dex_timing/probes/compare_core.py \
  --core /private/tmp/dex_core_replay --trace --sameboy-source ../SameBoy \
  --output build/luxray-core-instruction-comparison.json
python3 -B tools/dex_timing/probes/compare_core.py \
  --core /private/tmp/dex_core_replay --sweep --sameboy-source ../SameBoy \
  --output build/luxray-core-sweep.json
python3 -B -m unittest discover -s tools -p test_dex_timing.py
```

Reports record ROM/capture/core-binary hashes, the reference revision and dirty
status, and the synthetic-state assumptions. All **124 host tests pass**,
including fixture-format/scroll-shadow preservation and strict snapshot parsing.
The exact eight-T regression is retained rather than changed to a pass.

## Actual Save-State Calibration: 2026-09-20

The user supplied the requested first-publication emulator state in SameBoy
slot 10 and the exact first-miss measurement from that same run. This is a
new run, not the earlier Pass 4: its measured interval is **2,004,944 T**, whereas
Pass 4 measured 2,004,924 T. Do not subtract or combine timestamps across them.

### Evidence And Read-Only Method

The source state is `/Applications/SameBoy/Games/pokecrystal.s10`, SHA-256
`796c336535dff7525e5e47003832e3c54b21271f060277072d0108e092a02c42`.
The repository and installed game ROM both retain the pinned
`7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f` hash.
The symbol hash remains
`1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5`.

`probes/core_replay.c --state` uses SameBoy's own `GB_load_state` against the
unchanged ROM. It does not warm/reset the captured PPU, synthesize the stack,
replace memory, or save anything back to the emulator. The source state loads
as normal-speed CGB-E, matching the 1:2 T-cycle/8-MHz counter ratio. The local
SameBoy core is still the clean `213a12ce93d66b105a113debd9396306066a7cfc` revision.

The host receives a one-time physical RAM/HRAM/VRAM/register export. Initial
DIV is `$c8c0`, TIMA `$39`, divider subphase -3, with a timer interrupt already
pending. Those values determine timer phase 546; no phase search, new fitted
cost, or later-state injection is used. The original caller stack is preserved
at SP `$c0af`, rather than reconstructed at the fixture's default address.
The host still uses the source-supported 606-T publication origin and the
existing boundary probe, not a pixel renderer or an imported PPU implementation.

The user's two endpoint observations are preserved separately in
`tools/dex_timing/fixtures/luxray_save_state_capture.json`. The three intermediate
stops below are **independent-core predictions**, not user-supplied observations.
The raw emulator state and generated memory exports are not added to the fixture
directory; reports/exports stay under `build/` and the original state is read-only.

### Exact Result

| Stop | User elapsed T | Independent core T | Host probe T |
|---|---:|---:|---:|
| First publication | 0 | 0 | 0 |
| Next stage entry | Not captured | 36,964 | 36,964 |
| Next producer entry | Not captured | 62,724 | 62,724 |
| Next frame wait | Not captured | 67,956 | 67,956 |
| First miss | 2,004,944 | 2,004,944 | 2,004,944 |

Both measured endpoints match their captured PC/bank, AF/BC/DE/HL/SP, IME,
LY, and STAT mode. The first publication retains 300 cycles to the next PPU
event; the final core position is exactly **line 76, OAM 31/40**. There is no
remaining endpoint clock or PPU-position discrepancy for this run.

**All 159,713 executed non-HALT instruction starts match between host and
independent core in elapsed T, ROM bank, PC, AF, BC, DE, HL, and SP.** All 27
animation-state bytes, 139 instrumentation bytes, display counters, and audio
counts/pointers match at each of the five comparisons. This is stricter than
the earlier synthetic comparison, which compared instruction timing/bank/PC
but did not require general-purpose register equality.

Two host-probe details matter to this stronger comparison:

- `rSVBK`/`rVBK` retain their hardware read-as-one bits; no-input `rJOYP` retains
  its selected-row and upper bits. Omitting them changes temporary registers
  even where subsequent masks leave game behavior and timing unchanged.
- The existing `PendingHaltReplay` variant handles an interrupt becoming pending
  during the HALT instruction itself. SameBoy then refetches HALT after the IRQ,
  without the ordinary halted-wake penalty. The simpler wake variant diverged
  at elapsed 127,960/127,964 T and executed four extra non-HALT instructions over
  the interval, even though its five endpoint times happened to match. Selecting
  the source-supported variant removes that interior discrepancy. This is not
  evidence that the same HALT edge caused the old Pass 4 eight-T residual; that
  variant had already been tested there without changing the residual.

A separate control replays the actual initial memory through the older
synthetic-PPU initialization. It also matches all five elapsed times, registers,
LY/mode, DIV/TIMA, and animation/trace arrays. Thus the newly successful match
does not require a special hidden PPU phase adjustment or a species-specific
operation cost.

### Meaning And Remaining Limits

For this captured initial state, the corrected host has now reproduced the
real application's first-miss interval exactly and has an instruction-by-
instruction cross-check against SameBoy's independent core. **No further Luxray
dump, repeat run, or video is needed to close this focused calibration check.**

The earlier partial Pass 4 fixture still reproduces its recorded +8-T residual.
Keep that regression and its qualification: no complete state exists for that
old run, so this new state cannot prove which omitted byte/configuration caused
its discrepancy. The old Weavile early-LY boundary qualification is likewise
not silently closed by a Luxray result. This pass does not replace the default
model or claim full-animation/all-phase/late-dictionary calibration.

At the reproduced game miss, Luxray's event 7/frame 2 requires a 21-tile upload
whose completed offset is zero. All 134 dictionary tiles are already decoded,
and the sampled-cry cache has 87 blocks. The runtime diagnosis and proposed
fix direction are unchanged: preparation is arriving too late under the current
service-call schedule, and the complete path through publication needs budgeting.
Neither an empty cry cache nor an uncertain few-cycle operation cost explains
this unperformed upload. The result does not prove normal speed is incapable
of meeting the authored timeline with a corrected scheduler.

### Reproduction And Verification

Recompile the standalone core with the command in the preceding section, then:

```sh
python3 -B tools/dex_timing/probes/compare_save_state.py \
  --core /private/tmp/dex_core_replay \
  --state /Applications/SameBoy/Games/pokecrystal.s10 \
  --sameboy-source ../SameBoy \
  --output build/luxray-actual-state-comparison.json
python3 -B -m unittest discover -s tools -p test_dex_timing.py
```

The comparison verifies state/ROM/symbol/capture identities, rejects unsupported
starting phases, checks source-state immutability, and exits nonzero for a timing,
state, instruction, or observed-endpoint mismatch. It also preserves the
actual-memory/synthetic-PPU control. All **129 host tests pass**, including export
bounds, hardware readback, endpoint provenance, real-stack restoration, fail-
closed phase checks, and the two different HALT boundary paths. The older
synthetic instruction comparison was re-run and retains its original +8-T result.

No game ASM, ROM, sampled-cry settings, runtime instrumentation, or emulated
resource allocations changed; the ROM and source state hashes are unchanged.

## Full-Sequence Consolidation: 2026-09-20

The approved next steps are implemented in the ordinary linked replay. See
[the full results and reproduction record](dex_full_replay_results.md) for all
nine species, the preserved actual initial-memory fixture, later misses and
publication lateness, operation spans, and cry completion/underrun results.
All 5,326,896 executed non-HALT instruction starts match the independent core
in elapsed T and general-purpose registers. The source-state Luxray run also
matches through full cleanup, not just the previously captured first miss.

Full runs exposed additional DMA launch/wake/coalescing and cry timer-restoration
paths. In particular, the CGB-E HDMA request is two T after the STAT edge, not
the earlier probe's one-T offset. A later Luxray transfer exercised the exact
intervening boundary; first-miss tests alone had not distinguished them.
These source-supported corrections are now shared defaults, not experimental
per-species overrides. Earlier variant-sweep commands and results above remain
historical; `boundary_sensitivity` now wraps the consolidated model.

The incomplete older Luxray +8-T capture and Weavile boundary qualification
remain explicit. Other species' full continuations are independent-core
predictions from partial initial inputs, not user-supplied full-state runs.
Neither the game nor the measured ROM has changed. The useful next complete
captures are Dusknoir and Weavile; no repeat Luxray startup capture is needed.

## Focused Next Capture: Luxray (Historical)

Historical directions: `Luxray - Pass 4.txt` has now supplied the exact-clock
and LCD portions. Do not rerun them or gather later misses unless requested.

One cold Listing-to-Luxray run is enough. No other species, repeat suite, video,
ROM rebuild, or new instrumentation is requested. Use the same unchanged build
and the five stops/Common Dump/Publication Extras in
[the existing capture sheet](dex_timing_capture_five_species.md#start-each-run):

1. First publication: `breakpoint $77:$5ea5`
2. Next stage entry: `breakpoint $a0:$6483`
3. Next producer entry: `breakpoint $a0:$6282`
4. Next frame wait: `breakpoint $0:$047e`
5. First miss after that: `breakpoint $a0:$67fc`

Keep one breakpoint active at a time, using `delete` before setting the next.
Do not advance to a later publication or mix separate runs. At the first
publication, while paused, add:

```text
ticks
lcd
x/2 $0:$cfb1
x/3 $0:$cfbc
x/10 $0:$c2c7
x/6 $1:$d4c5
x/32 $0:$ffcf
```

Save the complete output. Bare `ticks` reports then resets only the debugger's
tick counters; it does not reset DIV/TIMA or modify game memory. Its initial
reported count is not part of the measured interval. The extra memory covers
overworld/text delay, cursor/game-time and input gates, game-time counters,
and shadow display/transfer flags omitted from the original fixture.

At **each of stops 2-5**, add these to the normal Common Dump:

```text
ticks keep
lcd
```

Use `ticks keep`, not bare `ticks`, at these later stops so all counts stay
relative to the same initial publication. The command spelling and reset
behavior were checked in SameBoy's `Core/debugger.c`. Include both its T-cycle
and Absolute 8MHz-tick lines, plus the full `lcd` output. This replaces inferred
elapsed bounds with exact emulator cycle counts and exposes more of the PPU
phase; no additional in-game counter is needed.
