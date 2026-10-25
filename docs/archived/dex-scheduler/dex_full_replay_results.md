# Selected Dex Full-Sequence Replay: 2026-09-20

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

**Latest additional states:** the
[Garchomp finishing record](dex_garchomp_finishing_results.md#new-actual-starting-states)
calibrates the other six sampled species from the user's new real starting
states, with 4,092,809 further exact instruction comparisons. All nine now have
actual-input continuations (5,608,137 matching instruction starts in total).
Exeggcute is preserved separately pending synth-start support. Historical
partial-input counts below are not changed to imply stronger original evidence.

**Follow-up:** the [actual Weavile/Dusknoir end-to-end results](dex_end_to_end_capture_results.md)
now match all four user-measured checkpoints exactly. Those two actual initial
fixtures replace their synthetic inputs in the ordinary full runner. The new
nine-case total is 5,400,595 matching instruction starts. Dusknoir's measured
cry underrun leaves 333 blocks, not the earlier synthetic prediction of 325.
The earlier pass below is preserved with its original inputs and numbers.

## Earlier Pass: Scope And Verdict

The validated boundary behavior is now in the ordinary linked `OwnerReplay`,
not selected through experimental probe subclasses. Full replay continues from
the first frontpic publication through the main animation, base-picture hold,
idle animation, sampled-cry stop, and the owner's return to its stable frame
wait. No later captured memory is injected.

**All nine full replays agree with the independent SameBoy core at every
executed non-HALT instruction start: 5,326,896 comparisons of elapsed T, ROM
bank, PC, AF, BC, DE, HL, and SP.** All six checkpoint times and animation/audio/
trace-state comparisons also agree. This validates the modeled paths for the
specified inputs; it does not certify all hardware phases or prove a proposed
runtime scheduler can meet its deadlines.

Luxray uses actual initial volatile memory extracted from the user's slot-10
emulator state. Its full continuation was also compared directly with the
independent core loading that original state. The other eight use explicitly
synthetic extensions of the partial captures. Their later results are
core-confirmed predictions, not additional user measurements. In particular,
their missing music state is represented by a silent post-cry control, not an
invented recreation of the user's music channels.

No game ASM, ROM, animation assets, runtime instrumentation, cry settings,
CPU speed, or resource allocations changed. The ROM was not rebuilt. The
emulator state and battery saves were not modified.

## Identity And Reproduction

Pinned inputs:

```text
ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
SYM: 1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
Luxray state: 796c336535dff7525e5e47003832e3c54b21271f060277072d0108e092a02c42
SameBoy core: 213a12ce93d66b105a113debd9396306066a7cfc (clean)
```

The portable `tools/dex_timing/fixtures/luxray_initial_volatile.json` fixture
contains compressed initial WRAM/VRAM/register data, its original stack, and
provenance hashes. It excludes cartridge ROM/SRAM, echo/OAM bus samples, and
emulator PPU/APU internals. It contains no later expected state. The host can
therefore reproduce Luxray without reopening the user's state file. The
reference core's synthetic-PPU control gives the same six checkpoints as its
direct original-state run.

From the repository root, using the local SameBoy source:

```sh
clang -O2 -std=c11 -I../SameBoy \
  -DGB_INTERNAL -DGB_DISABLE_DEBUGGER -DGB_DISABLE_REWIND \
  -DGB_DISABLE_CHEATS -DGB_DISABLE_CHEAT_SEARCH -DGB_DISABLE_TIMEKEEPING \
  '-DGB_VERSION="dex-full-replay"' \
  tools/dex_timing/probes/core_replay.c \
  ../SameBoy/Core/{apu,camera,display,gb,joypad,mbc,memory,printer,random,rumble,save_state,sgb,sm83_cpu,timing,workboy}.c \
  -o /private/tmp/dex_core_full_replay
env PYTHONPATH=tools python3 -B -m dex_timing.full_replay \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --output build/dex-full-replays --jobs 8
python3 -B tools/dex_timing/probes/compare_save_state.py --full \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --state /Applications/SameBoy/Games/pokecrystal.s10 \
  --output build/dex-host-full-luxray.json
python3 -B tools/test_dex_timing.py
```

These commands build a host executable, not the game. They require the pinned
ROM/symbols; the full runner checks identity even for partial-capture-only runs.
The detailed per-species JSON reports include initial-memory/core/host-source
hashes, reference revision, assumptions, instruction comparisons, lifecycle
events, and operation spans. Generated memory exports and instruction traces
stay under `build/`. The raw source state is not included in the repository.

## What Changed In The Model

The earlier source-supported IRQ/HALT/PPU/readback corrections now run by
default in the linked replay. The older `boundary_sensitivity` entry point is a
parameter-sweep wrapper around that implementation, not a second hardware
model. It no longer offers the discarded variant ladder.

Extending beyond the first miss exercised additional boundaries:

1. **Deferred DMA requests:** HBlank requests become pending and execute at
   CPU boundaries. Repeated pending requests coalesce; they are not a queue
   of independent transfers. The CGB-E path's request follows the STAT edge
   by two T, as in SameBoy's `display.c` states 22 and 33. A later Luxray
   upload hit the intervening boundary that the first-miss run had not tested.
2. **Mode-0 launch and wake behavior:** an HDMA armed during an existing
   HBlank can request its first block immediately. SameBoy's IRQ wake path can
   re-arm a block in that HBlank using the latch from the last successful
   HALT (`sm83_cpu.c`, `allow_hdma_on_wake`). Later Rayquaza, Kyogre and
   Garchomp paths exercised these cases. This is shared hardware behavior,
   not a per-species timing adjustment.
3. **GDMA data movement:** publication's immediate DMA now copies the bytes
   as well as charging the transfer time. HDMA and GDMA retain separate
   timing and completion behavior.
4. **Cry shutdown and ordinary music:** model the existing code's TAC disable,
   IF clear, TIMA/TMA/TAC/IE restoration, and subsequent timer period. Preserve
   disabled joypad IF and register read-as-one bits where CPU reads observe
   them. Restore CPU-visible sound control values in the reference fixture;
   this does not reconstruct oscillator/envelope phase or validate the sound
   waveform.
5. **Full completion and accounting:** stop only when animation state is DONE,
   sampled playback is inactive, and the owner returns to `DelayFrame.halt`.
   Record every underflow, publication, dictionary decode, gather/upload,
   cache refill and cry stop. Bounded execution fails rather than fabricating
   completion. Unsupported live TIMA writes and unmodeled starting phases
   also fail explicitly.

No correction alters game execution to make it pass. In particular, the replay
still executes the game's service-call-driven micro-schedule and still exposes
the resulting missed deadlines.

## Full Results

"Misses" counts calls to `Pokedex_CountAnimationUnderflow`. "Late publications"
counts completed map transactions published after their authored display
interval. These are distinct signals, not additive counts of bad pictures.

| Species | Full Selected intervals | Publications | Misses | Late publications | Largest lateness | Cry result | Instruction starts |
|---|---:|---:|---:|---:|---:|---|---:|
| Luxray | 92 | 15 | 4 | 2 | 1 interval | Natural completion | 463,322 |
| Weavile | 78 | 16 | 6 | 3 | 1 interval | Natural completion | 318,239 |
| Dusknoir | 174 | 35 | 24 | 6 | 2 intervals | Underrun, 325 blocks left | 660,068 |
| Bastiodon | 205 | 18 | 10 | 5 | 2 intervals | Natural completion | 736,290 |
| Garchomp | 110 | 14 | 7 | 4 | 2 intervals | Natural completion | 426,741 |
| Rampardos | 139 | 25 | 11 | 4 | 1 interval | Natural completion | 602,234 |
| Rayquaza | 175 | 29 | 16 | 8 | 1 interval | Natural completion | 714,843 |
| Kyogre | 113 | 24 | 12 | 5 | 1 interval | Natural completion | 569,966 |
| Metagross | 228 | 22 | 2 | 2 | 1 interval | Natural completion | 835,193 |

**Full Selected intervals are not just the main animation.** The linked
generator concatenates main animation, 18 base-picture intervals, and idle
animation. Dusknoir remains **107 main intervals + 18 hold + 49 idle = 174**.
In this run its main sequence returns to base at interval 107, idle starts at
125, and the final base publication occurs at 174. Those endpoint matches
coexist with many missed intermediate frames. Hitting total duration alone
is therefore not an adequate acceptance test.

The final cleanup checkpoint occurs after publication/cry cleanup and is not
used as the animation-duration measurement. All nine final publications land
on their final authored interval; this does not cancel their earlier misses.

### Luxray: Actual Initial State

The saved run's captured first miss remains exactly **2,004,944 T** after first
publication, with all endpoint registers and PPU position matching. The full
continuation reaches stable cleanup at 6,477,124 T. The user has not supplied
that later endpoint; it is independently reproduced by the reference core.

The four unfinished-stage events are:

| Event | Frame | Tiles uploaded/required | Dictionary still missing | Audio cache |
|---|---:|---:|---:|---:|
| 7 | 2 | 0/21 | 0 | 87 |
| 8 | 3 | 20/49 | 0 | 83 |
| 10 | 3 | 20/49 | 0 | 85 |
| 12 | 1 | 0/17 | 0 | 85 |

This rules out missing dictionary data or an empty audio cache as the direct
cause of these Luxray animation misses. It supports the earlier diagnosis:
stage preparation/upload and publication are not being completed soon enough
under the current call-driven work schedule. It does not prove that more
prefill, more VRAM, or a particular replacement scheduler is required.

### Weavile: Partial-Capture Continuation

The six missed stages are events 2, 3, 4, 6, 8 and 9. They include both zero
upload progress and stages stuck after the first 20 tiles. All have their
dictionary data already decoded. The old partial capture still has its
producer-entry mode/IF and frame-wait early-LY qualifications; exact agreement
with a reference core given the same synthetic input does not erase them.

### Dusknoir: Decode And Audio Overlap

This longer replay actually executes **17 dictionary decode calls** alongside
the owner, upload, interrupt and refill paths. Thus the model/reference-core
comparison now covers runtime tail decoding, not just already-resident
dictionary cases. A complete real initial-state capture is still needed to
promote this from a core-confirmed prediction to the same evidentiary level
as the saved Luxray run.

The first missed stage needs 32 tiles, has uploaded 20, and still has 102
dictionary tiles outstanding. Later misses also occur after the dictionary
is complete. Decode backlog is therefore not the only failure mechanism.

The cry stops with an empty cache and **325 blocks remaining**, at 2,928,268 T
after the first publication (about 0.698 seconds). This is a genuine modeled
audio underrun, not the normal zero-remaining stop. It must be confirmed on a
complete captured input before being treated as the exact behavior of the
user's current session. Once it stops, later animation work no longer bears
the sampled playback/refill load; do not interpret those later costs as proof
that animation and a healthy full cry can coexist.

## Operation-Cost Evidence

Reports retain individual operation spans rather than one constant tile price.
`instruction_t` excludes interrupt instruction work, `interrupt_t` records
serviced interrupts, and `elapsed_t` includes waits and DMA. Spans are inclusive
and can nest (producer contains gather/upload; next-stage contains build).
**Do not sum different nested categories as if they were exclusive costs.**

Examples from the full runs:

| Run / operation | Calls | Instruction T, total | Elapsed T, total | Largest elapsed call |
|---|---:|---:|---:|---:|
| Luxray stage build | 7 | 144,648 | 221,212 | 50,840 |
| Luxray tile gather | 7 | 91,464 | 135,596 | 29,660 |
| Luxray HDMA helper | 6 | 50,568 | 87,564 | 29,924 |
| Dusknoir dictionary chunk | 17 | 160,100 | 225,920 | 20,336 |
| Dusknoir stage build | 27 | 621,036 | 883,752 | 40,792 |

The HDMA helper's instruction total includes its polling code; it is not the
hardware transfer cost alone. Full elapsed paths include interrupted work and
the phase at which the helper starts. This is why a validator based only on
"six decoded, twenty uploaded per call" cannot establish a display deadline.

These are measured-path costs, not species-independent worst-case guarantees.
For the replacement design, budget the complete dependency chain from work
release through queueing and VBlank publication, retain independent work
completion, and test phase-dependent waits. Avoid fitting a flat per-species
penalty to make the current schedule appear feasible.

## Remaining Limits And Next Evidence

- The old Luxray Pass 4 partial fixture retains its **+8-T** residual. The new
  saved-state run is a different run and is exact; it cannot identify which
  uncaptured initial detail differed in the old one.
- Seven other partial first-miss captures remain consistent with the corrected
  model and their quantized clocks. Weavile retains the boundary qualification
  above. Full core agreement applies to the stated input in each case.
- No on-hardware test, A-button/cancel/input intervention, broad phase sweep,
  other emulator model, double speed, battle, New Dex Entry or party Stats
  Screen validation is claimed. This replay starts at first publication and
  does not measure selection-to-reveal or internal-paging startup latency.
- The earlier aggregate all-species explorer remains **UNCALIBRATED**. Promoting
  the linked replay does not automatically certify that approximation or the
  ROM generator's quota validator.
- The useful next complete inputs are **Dusknoir** (decode/audio overlap) and
  **Weavile** (remaining starting-boundary qualification), saved at the same
  first-publication breakpoint on the unchanged ROM. They are more informative
  than another broad set of partial dumps. A later Luxray miss timestamp can
  independently spot-check the newly modeled continuation if desired.
- No new video or runtime instrumentation is required to finish this host pass.
  Any next capture protocol should preserve one continuous run, reset `ticks`
  only at first publication, and use `ticks keep` at later stops.

The runtime fix direction is still a proposal: shared display-time release and
deadlines, independently tracked completed work, early safe preparation, and
explicit budgeting of assembly/upload/publication plus audio service. This pass
provides a stronger baseline against which to test it; it does not implement it.

## Verification

- 136 host regression tests pass, including portable-fixture identity/sanitizing,
  full Luxray completion, original first-miss preservation, bounded failure,
  cry timer restoration, immediate-mode-0 HDMA and deferred GDMA copying.
- All nine full reference comparisons exit successfully; all checkpoint deltas
  are zero and all 5,326,896 instruction starts match.
- The separate original-state Luxray full comparison also exits successfully,
  including its synthetic-PPU control and both user-measured endpoints.
- The old incomplete Luxray +8-T regression still passes as an explicitly
  expected residual, not an exact-match claim.
- `git diff --check` passes. Repository ROM, SameBoy ROM, symbol and source-state
  SHA-256 hashes remain the pinned values above. Full replay outputs and raw
  generated exports are ignored under their `build/` report paths.
