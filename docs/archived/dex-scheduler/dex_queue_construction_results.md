# Selected Dex Queue Construction Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Follow-up: [headroom and synthesized-cry results](dex_headroom_synth_results.md)
retain this queue optimization, improve the 556-T finishing margin, and add
actual-state synthesized-cry validation. The results below remain the historical
queue-only step.

Date: 2026-09-20. Follow-up to the
[Garchomp complete-chain finishing investigation](dex_garchomp_finishing_results.md).

## Scope And Result

The requested sequence was followed: first measure and reduce queue-construction
cost, then rerun full animation/cry continuations and the known failing controls.
All work is host-only. No game ASM, cartridge file, allocation, emulator state,
SRAM, startup lead, audio setting, or animation script was changed or rebuilt.

The measured improvement is a small instruction-level optimization, not another
ownership or buffering redesign. Unrolling the fixed seven-byte inner loops in
the two map-copy helpers removes **3,216 T per queue**, reducing its worst measured
raw CPU cost from **12,596 to 9,380 T (25.5%)**. Both backing maps, both owner
buffers, their copy order, bank restoration, pending handoff, and all temporary
instrumentation remain intact.

On top of the existing host scheduler candidate, this closes the three known
Garchomp failing configurations. The nine-species matrices now pass **144/144
phase runs and 108/108 overhead-cost runs**, versus 143/144 and 106/108 previously.
Correct intermediate graphics and cry completion are checked, not just final
animation duration. This is host feasibility evidence, not a runtime signoff.

## Step 1: Where The Queue Time Goes

The existing queue performs four 49-byte copies:

1. Packed stage tilemap to the 20-column normal backing tilemap.
2. Packed stage attributes to the 20-column normal backing attrmap.
3. Backing tiles to the 32-column persistent VBlank owner buffer.
4. Backing attributes to the second 32-column owner buffer.

The first pair is `Pokedex_CopyPackedFrontpicMapToBacking`; the second pair is
`Pokedex_StageCurrentFrontpicOwnerMaps.CopyMap`. These copies preserve two
different representations that existing transitions and publication use.
The experiment deliberately keeps both; it does not invalidate the backing
maps or introduce a special return path.

| Queue component | Native T | Unrolled T | Saving |
| --- | ---: | ---: | ---: |
| Two packed-to-backing copies | 4,632 | 3,024 | 1,608 |
| Two backing-to-owner copies | 5,304 | 3,696 | 1,608 |
| Remaining queue work, including diagnostics | 2,660 | 2,660 | 0 |
| **Total** | **12,596** | **9,380** | **3,216** |

Each helper originally loads C=7 for every row, then decrements/tests C after
every byte. The prototype emits the seven `LD A,[HLI] / LD [DE],A / INC DE`
triples directly. The outer seven-row loop and all stride/carry handling remain.
C is set to zero once so the original return-register contract is preserved.
Each call saves exactly 804 T, independently of the data and page carries.

At normal speed, 3,216 T is about **0.767 ms of raw CPU work**. Elapsed savings
can be greater because the shorter path also avoids interrupt service that would
otherwise fall inside it. This does not change the DMA engine's speed or the
quantity of VRAM data transferred. It also does not remove stage construction,
dictionary decoding, gathering, or any audio refill.

### Executable Prototype And Resource Cost

`tools/dex_timing/queue_experiment.py` emits the two proposed helper bodies into
a private in-memory copy of the pinned ROM and redirects exactly four existing
CALL operands. The instruction replay executes those actual bytes. There is no
magic map copy, arbitrary cycle discount, alternate ROM file, or game rebuild.
The fixture identity is checked before changing even this private image.

| Resource | Increment for replacing the two helper bodies |
| --- | ---: |
| ROMX | **30 bytes**: 21 -> 36 and 27 -> 42 |
| ROM0 | 0 |
| WRAM0 / WRAMX | 0 / 0 |
| HRAM / VRAM | 0 / 0 |
| Generated animation metadata | 0 |

The host relocation uses 78 bytes of verified zero-filled padding at
`$77:$7c00` and retains the old, now-uncalled helper bodies. That is a probe
layout, not the proposed production layout. A later implementation would replace
the bodies and relink. Bank $77 currently has 3,020 free bytes; no new ROMX bank
is expected for this optimization. The final link and branch ranges still need
checking at implementation time. These costs apply to this copy optimization,
not to the complete scheduler implementation, whose guards remain costed models.

### Correctness Checks Before Timing Replays

- 3,072 paired helper fixtures cover both routines, every destination low byte,
  three source alignments including page crossings, and two initial flag states.
  Both versions produce the same 49 writes in the same order, final registers,
  flags, stack pointer, bank, and memory. Every case saves 804 T.
- 60 paired whole-queue fixtures cover both slots, base and animated maps,
  three incoming WRAM banks, and all five trace-ring positions. Backing/owner
  bytes, restored banks, registers, and memory agree. Pending is published only
  after both owner maps are complete. Each queue saves 3,216 T.
- The private-image test permits only the two new bodies and four CALL operand
  changes. Original game-file hashes remain unchanged.
- Full replays compare published map/attribute cells and slot tile data against
  canonical animation assets, rather than merely comparing two queue routines.

## Step 2: Garchomp And Full-Sequence Replays

All candidate runs retain the prior early-budget policy: shared display clock,
independent work completion, early eligible production, one bounded finishing
call, unchanged atomic deadline-controlled publication, the settled owner route,
and the complete audio/diagnostic paths. Only the queue helpers and their measured
contribution to admission change.

The ten-tile finishing envelope changes as follows:

| Component | Before | After |
| --- | ---: | ---: |
| Gather/upload caller prefix | 10,596 T | 10,596 T |
| Upload suffix | 552 T | 552 T |
| Queue | 12,596 T | 9,380 T |
| Hardware-helper allowance | 5,300 T | 5,300 T |
| Wrapper allowance | 256 T | 256 T |
| Raw complete-chain work | 29,300 T | 26,084 T |
| Interrupt-extended active-audio bound | **46,236 T** | **41,940 T** |

For the seven-tile post-cry finish, the still-enabled timer's measured 104-T
short handler remains charged. Its bound falls from 33,428 to **29,132 T**.
The full-chain checks still discard the remainder of the current scanline,
include interrupt costs, reject late DMA launch, and reserve subsequent audio
service time. They were not relaxed to obtain a passing result.

### Known Negative Controls

| Previously failing configuration | Old result | Unrolled queue |
| --- | --- | --- |
| Garchomp, timer phase 3,264 T | Event 5 rejected by 180 T | Pass; same LY 42 entry, **4,116-T admission margin** |
| Dispatch 2,048 / viewport 64 / finish guard 1,024 T | Event 12 rejected by 596 T | Full sequence passes |
| Dispatch 2,048 / viewport 256 / finish guard 1,024 T | Events 5 and 12 rejected | Full sequence passes |

Fresh native-helper controls reproduce the two high-cost failures, including
their incorrect fallback maps. The existing phase-failure regression continues
to retain the original 180-T rejection. Failures are not hidden by stretching
holds or suppressing the underrun counter.

Nominal actual Garchomp finishing spans:

| Event | Remaining tiles | Old elapsed | New elapsed | Old / new queue-ready LY |
| --- | ---: | ---: | ---: | ---: |
| 2 | 9 | 38,768 T | 33,000 T | 129 / 117 |
| 3 | 7 | 35,636 T | 29,780 T | 117 / 104 |
| 5 | 10 | 40,784 T | 34,928 T | 124 / 112 |
| 12 | 7 | 30,660 T | 26,472 T | 133 / 123 |

Garchomp still uses its **110 authored display intervals**. The new earlier
readiness is preparation lead, not early publication or faster playback.
Its nominal sampled cry stops naturally at the same elapsed time as the native
queue control. Startup remains 96 tail tiles, with the same two VRAM slots,
six-tile compressed chunks, 20-tile normal uploads and 32-block audio prefill.

### Nine-Species Controls

| Species | 16 timer phases | 12 overhead settings |
| --- | ---: | ---: |
| Luxray | 16/16 | 12/12 |
| Weavile | 16/16 | 12/12 |
| Dusknoir | 16/16 | 12/12 |
| Bastiodon | 16/16 | 12/12 |
| Garchomp | 16/16 | 12/12 |
| Rampardos | 16/16 | 12/12 |
| Rayquaza | 16/16 | 12/12 |
| Kyogre | 16/16 | 12/12 |
| Metagross | 16/16 | 12/12 |

These 252 runs contain no animation misses, late/duplicate publications, wrong
maps or slot tiles, sampled-cry underruns, finishing-bound overruns, finishing
chains crossing VBlank, audio-reserve violations, or unsafe display writes.
Latest map-GDMA completion is 3,338 T into VBlank, within the unchanged previously
derived publication contract. No successful fallback map is counted as a pass.

The phase sweep uses 64..12,064 T in 800-T steps with default dispatch/viewport/
finish costs 1,024/64/256 T. The cost sweep uses dispatch 256/1,024/2,048 T,
viewport 64/256 T and finishing admission 256/1,024 T at each actual initial
phase. These are synthetic variations of actual initial fixtures, not additional
live captures or an exhaustive proof over every possible entry state.

### Combined Garchomp Stress

A further **64/64** full Garchomp continuations pass with the highest tested
dispatch/viewport/finishing costs (2,048/256/1,024 T) combined with timer phases
64..12,664 T in 200-T steps. All correctness, audio, admission-bound, and hardware
checks remain clean. The latest map-GDMA completion is 3,362 T into VBlank.

The smallest accepted conservative margin is **556 T**, at event 2 with timer
phase 7,464 T and admission at LY 58. The minimum observed time remaining within
the conservatively truncated window after actual finishing is 5,076 T, in a
different run. Do not substitute the observed margin for the conservative one.
The 556-T result is useful evidence but still tight; these 64 phases are not an
exhaustive proof of every timing alignment or arbitrary additional work.

Together, the two nine-species matrices and this combined sweep total **316/316
passing candidate continuations**. The separate 16-run native/unrolled Garchomp
comparison retains the failing native controls instead of counting them as passes.

## Assessment And Remaining Gates

The queue had enough avoidable CPU overhead to explain the remaining tested
Garchomp margin failures. It is not necessary, on this evidence, to add VRAM,
increase startup lead, generate another animation-data format, or remove the
normal backing maps to close those particular cases.

This improvement belongs with the existing scheduler corrections, not instead
of them. Applying just the two faster copies to the current game is **not** what
these passing candidate runs tested. The unchanged-ROM defects and earlier
host-policy changes remain separately documented.

Before approving a runtime build, the next gates are a concrete instruction-costed
implementation of the scheduler decisions, synthesized-cry coverage using the
already supplied Exeggcute state, and ownership/input tests for A, B, internal
paging, transitions and cancellation. The present scope is settled, no-input
Selected playback at normal speed and normal sampled pitch. No new Garchomp
capture is needed to continue those host-side steps. Battle, New Dex Entry,
party Stats and Description paging remain outside this runtime-fix scope.

## Reproduction And Identity

Reports include original ROM/symbol and host-source hashes, the private image's
exact patch manifest, per-operation costs, each finish admission and observed
span, hardware/asset checks and full completion records. Generated reports live
in ignored `build/dex-timing-*` directories; this document preserves the findings.

```text
Original ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
Symbols: 1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
Private instruction image: 8cb1e2162d96b6cbe61a1bd5292614f94662bcb03563bb1e09b30c287937bfe4
```

```sh
python3 -B -m tools.dex_timing.queue_experiment --species garchomp \
  --mode native row-unrolled --dispatch-t 1024 2048 \
  --viewport-guard-t 64 256 --finish-guard-t 256 1024 --jobs 8 \
  --output build/dex-timing-queue-garchomp-costs
python3 -B -m tools.dex_timing.queue_experiment --jobs 8 \
  --timer-delay-t 64 864 1664 2464 3264 4064 4864 5664 6464 7264 8064 8864 9664 10464 11264 12064 \
  --output build/dex-timing-queue-phase
python3 -B -m tools.dex_timing.queue_experiment --jobs 8 \
  --dispatch-t 256 1024 2048 --viewport-guard-t 64 256 --finish-guard-t 256 1024 \
  --output build/dex-timing-queue-costs
python3 -B -m tools.dex_timing.queue_experiment --species garchomp --jobs 8 \
  --dispatch-t 2048 --viewport-guard-t 256 --finish-guard-t 1024 \
  --timer-delay-t $(seq 64 200 12664) \
  --output build/dex-timing-queue-garchomp-combined
python3 -B tools/test_dex_timing.py
```

Verification completed: **187 regression tests pass**, including the new helper
equivalence, whole-queue handoff, private-image boundary, measured-cost and known
Garchomp counterexample tests. All **332** reports across the four directories
above match the current host-source hashes. The 316-run candidate sweeps have no
failures; the separate comparison deliberately retains its native failures.
Repository and SameBoy cartridge hashes and the symbol hash are unchanged, and
`git diff --check` passes. No user saves or states were written.
