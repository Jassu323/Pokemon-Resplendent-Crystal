# Selected Dex Garchomp Finishing Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Date: 2026-09-20. Follow-up to
[steady-display publication and recovery](dex_steady_publication_results.md).

Follow-up: the [queue-construction experiment](dex_queue_construction_results.md)
retains the results below as native-helper controls and closes their known
counterexamples in the host candidate with measured copy-loop savings. It does
not change the game ROM or retroactively change the historical results here.

## Verdict

Garchomp's original candidate failure is not missing dictionary decoding. All
140 dictionary tiles are available, but event 5 needs 30 gathered/uploaded tiles
and the first call completes only 20. The previous experimental finishing rule
allows at most eight additional tiles, so it refuses the remaining ten.

A species-independent, complete-chain time budget removes that arbitrary limit.
With early finishing and map submission, all nine actual sampled-species starts
complete at their authored deadlines with correct intermediate maps/slot bytes
and natural cry completion in the nominal host run. Startup lead remains 96 tail
tiles; no additional VRAM, larger audio prefill, or slower animation is used.

**This is promising but not a general signoff.** The candidate passes 143/144
timer-phase runs and 106/108 overhead-cost runs. All remaining failures are
Garchomp conservative-admission rejections, not accepted jobs exceeding their
bound. One phase arrives 180 T short of the conservative time required for the
ten-tile finish. Two high-overhead settings also expose a later post-cry finish.
Those misses and their incorrect fallback maps remain explicitly recorded.

No game code, ROM, sampled-cry setting, runtime instrumentation, allocation, or
emulator save was changed. The candidate remains a costed host counterfactual.

## New Actual Starting States

The user supplied seven more states at `$77:$5ea5`. The importer reads them
without saving over them or touching battery saves. Portable fixtures retain
only initial volatile memory and registers, with ROM/SRAM and echo/OAM bus
samples stripped. No later expected state is injected into the host replay.

| State | Species | Unchanged-ROM instruction starts matched | Misses / late publications |
| --- | --- | ---: | ---: |
| 07 | Garchomp | 451,032 | 7 / 3 |
| 06 | Bastiodon | 793,823 | 10 / 5 |
| 05 | Rampardos | 625,711 | 11 / 4 |
| 04 | Rayquaza | 757,165 | 16 / 8 |
| 03 | Kyogre | 575,982 | 12 / 5 |
| 02 | Metagross | 889,096 | 2 / 2 |
| 01 | Exeggcute | Preserved, not yet host-replayed | Not assessed here |

For the six sampled species, the independently executed SameBoy core and the
host agree at all **4,092,809 non-HALT instruction starts**, including CPU
registers and elapsed T-cycles. Checkpoint timing and captured state also match.
Together with the existing actual Luxray, Weavile, and Dusknoir fixtures, this
provides nine actual-input calibrated continuations totaling **5,608,137**
matching instruction starts. This replaces the earlier six-species partial
initial-memory qualification for these new runs, not retroactively for old runs.

Exeggcute is a synthesized-cry control. Its state and independent core output
are preserved, but the focused host constructor still assumes a sampled-cry
initial timer configuration. It has not been forced through that constructor
or counted as a passing animation test. No replacement capture is needed.

## Candidate Change

`tools/dex_timing/finish_experiment.py` compares four host policies:

| Mode | Purpose |
| --- | --- |
| `eight` | Historical steady-publication candidate, including its <=8-tile finish heuristic |
| `probe` | Unrestricted <=20-tile finishing feasibility control; not a safe recommendation |
| `budget` | Admit a complete ready remainder only when upload plus queue construction fit |
| `early-budget` | Same budget, but finish and submit before noncritical producer bookkeeping |

`eight` is **not the unchanged ROM**. It already includes the prior display-clock
work-release, wait, audio-order, ownership, and steady-publication experiments.
The original-ROM calibration results above are a separate control.

The early boundary is `Pokedex_ServiceAnimationProducer.record_dictionary`.
The host calls the existing linked uploader, then the existing linked
`Pokedex_CommitDescriptionAnimation`, and resumes the original bookkeeping.
It does not omit the dictionary debug update, trace recording, later owner
work, or audio service. The normal later submission is prevented from duplicating
an already pending/published frame by the previous queue-boundary ownership check.

Admission requires:

- A valid unfinished stage in the non-displayed slot, with all remaining source
  tiles decoded and no more than 20 tiles left.
- A visible-line entry with the authored deadline not already behind the next
  publication opportunity. The rest of the current scanline is discarded when
  calculating available time; no exact host-only dot position is used.
- Enough time for gathering, HDMA launch/wait/transfer, upload completion, and
  the complete map/attribute queue, not just the DMA itself.
- The predicted helper launch remains before its native `128 - tile_count`
  cutoff, and the entire chain completes before VBlank starts.
- Adequate audio runway through this work plus two display intervals: one to
  enter the next real service and one to complete its refill. If the entire
  remaining cry is already cached, no nonexistent future refill is required.
- Interruptible entry after enabled pending interrupts have drained, no active
  DMA, the short STAT handler, and a timer no faster than the measured envelope.
- At most one finishing call per owner iteration, not an unbounded catch-up loop.

The entry contract and cost allowances require a concrete runtime implementation
and remeasurement before deployment. Host assertions are not free runtime checks.

## Cost Model

Costs come from linked instructions, with hardware time added separately. Both
slots, upload offsets, ready-lead branches, trace-ring positions, and publication
counter branches are exercised. The helper is skipped only to isolate its
caller's suffix; its elapsed time is not treated as zero.

For a ten-tile finish:

| Component | Cost |
| --- | ---: |
| Upload caller / gather prefix | 10,596 T |
| Upload completion suffix | 552 T |
| Complete native queue path | 12,596 T |
| Helper setup, phase wait, transfer and polling allowance | 5,300 T |
| Calls, queue guard and wrapper allowance | 256 T |
| Raw work allowance | 29,300 T |
| Interrupt-extended bound, sampled audio active | **46,236 T** |

The queue is a substantial part of the remaining work. This is not simply a
ten-tile DMA problem: gathering and building/copying the map/attribute queue
consume more raw CPU time than the hardware-transfer allowance.

For drained entry, the visible-only response bound solves:

```text
R = raw_work + ceil(R / 12800) * timer_IRQ_cost
             + ceil(R / 456) * 108
```

Active sampled playback uses a 1,480-T timer-interrupt envelope. Future interrupt
phase is arbitrary. Since already-pending enabled interrupts have been serviced,
the model does not also add an old pending IRQ on top of the next periodic IRQ.
The older unknown-entry bound remains recorded (48,256 T for ten tiles), but
cannot be silently substituted for this entry contract or vice versa.

Hardware waiting is included as if interruptible CPU work, conservatively
overcounting interrupts that overlap autonomous HDMA. VBlank itself is excluded;
the admission rule must prove completion before it. Faster timer pitches,
masked callers, different STAT paths, other owners, and future linked-code
changes require another bound. This is not universal WCET certification.

### Post-Cry Distinction Exposed By The New State

The actual Garchomp start includes real post-cry music state, unlike its earlier
silent partial-state control. Event 12 then reaches its seven-tile remainder at
LY 65. Charging the active sampled timer handler incorrectly rejects it.

The restored timer is **still enabled**; it is not valid to charge zero timer
interrupt cost. With `hSampledCryTimer = 0`, the linked vector/handler returns in
**104 T including interrupt entry**. Neither finishing nor queue construction
can start another cry. Using that measured branch gives a 33,428-T bound for
the seven-tile chain versus 35,568 T conservatively available. The actual chain
takes 30,660 T and queues at LY 133, before its publication deadline.

The host also supports a genuinely disabled timer as a distinct lower-cost
case. Regression tests prohibit treating active sampled audio as that case.

## Nominal Actual Garchomp Sequence

| Event | Needed / previously uploaded | Extra tiles | Available / bound | Actual chain | Queue ready at LY |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 | 29 / 20 | 9 | 45,144 / 44,412 T | 38,768 T | 129 |
| 3 | 27 / 20 | 7 | 47,880 / 40,764 T | 35,636 T | 117 |
| 5 | 30 / 20 | 10 | 49,248 / 46,236 T | 40,784 T | 124 |
| 12 | 27 / 20 | 7 | 35,568 / 33,428 T | 30,660 T | 133 |

Event 5 starts finishing at LY 35 in interval 28 and queues before its interval-29
publication. It retains 8,678 T (about 2.07 ms) before that VBlank starts in this
run. Its cry cache goes from 72 to 69 blocks; the subsequent real refill starts
2,000 T after queue completion and takes 30,584 T. No audio service is invented
or skipped. The entire authored Garchomp sequence remains **110 intervals**.

## Full-Sequence Controls

The final nominal comparison runs `eight`, `budget`, and `early-budget` on all
nine actual starts. Both budget candidates pass all nine. `eight` retains the
Garchomp event-5 miss; its other eight runs pass.

The following matrices use `early-budget`, unchanged animation deadlines,
32-block cry startup, 96-tail-tile graphics startup, and both original slots:

| Species | Nominal | 16 timer phases | 12 overhead settings |
| --- | --- | --- | --- |
| Weavile | Pass | 16/16 | 12/12 |
| Luxray | Pass | 16/16 | 12/12 |
| Dusknoir | Pass | 16/16 | 12/12 |
| Bastiodon | Pass | 16/16 | 12/12 |
| Garchomp | Pass | **15/16** | **10/12** |
| Rampardos | Pass | 16/16 | 12/12 |
| Rayquaza | Pass | 16/16 | 12/12 |
| Kyogre | Pass | 16/16 | 12/12 |
| Metagross | Pass | 16/16 | 12/12 |

The phase sweep uses 64..12,064 T in 800-T steps, with 1,024-T dispatch,
64-T viewport routing and 256-T finishing-admission allowances. The cost sweep
uses 256/1,024/2,048-T dispatch, 64/256-T viewport routing and 256/1,024-T finishing
allowances at the original phase. These are synthetic controls from actual
initial states, not 252 additional user-recorded sessions or an exhaustive sweep.

All 252 runs retain natural cry completion, no duplicate or late publication,
no finishing-bound overruns, no finishing chain crossing VBlank, no audio-runway
violations, and no unsafe hardware transfers. The failed runs still publish
incorrect underflow maps on time; they therefore **do not count as success**.
The maximum observed map-GDMA completion is 3,338 T into VBlank, within the prior
steady-publication bound. The hardware publication contract is unchanged.

### Remaining Counterexamples

- Timer phase 3,264 T: event 5 reaches admission at LY 42, with 46,056 T available
  against its 46,236-T bound. It rejects by 180 T and preserves the 20/30 miss.
- Dispatch 2,048 T, viewport 64 T, finishing guard 1,024 T: event 12 reaches LY 71
  with 32,832 T available against 33,428 T. It rejects by 596 T.
- Dispatch 2,048 T, viewport 256 T, finishing guard 1,024 T: event 5 rejects by
  180 T and event 12 at LY 74 rejects by 1,964 T. Both misses remain visible.

These are conservative-admission deficits, not measurements proving the actual
work would overrun by those amounts. Do not relax the bound just to make them
pass. Nominal success plus these tight margins is evidence to seek more real
headroom before runtime implementation.

## Fix Direction And Remaining Gates

Keep the shared display clock, independently tracked work, early eligible
preparation, and deadline-controlled atomic publication. Replace the arbitrary
eight-tile finish rule with a complete-chain budget; retain early submission
ahead of noncritical bookkeeping. This does not require another dictionary
format, new full-frame ROM assets, extra preload, or another VRAM slot.

The next targeted host step should examine the native queue path and redundant
work before admission. Its 12,596-T raw queue cost is material, and queue-only
or gather improvements would benefit all species. Cost a concrete cheaper path
or move genuinely noncritical work afterward, then rerun the known negative
controls. Merely changing a maximum tile count or deleting diagnostic work from
the model would not establish a reliable runtime scheduler.

Before a runtime test build, also cost the actual dispatch/guard implementation,
close the remaining phase/cost misses with margin, add the synthesized-cry
control, and validate ownership exit/re-entry for A, B, internal paging and other
UI work. These steady no-input continuations do not establish responsive input
handling or safe viewport/OAM handoff. Battle, New Dex Entry and party Stats
remain outside this runtime-fix scope.

## Reproduction And Artifacts

Pinned ROM and symbols are unchanged:

```text
ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
SYM: 1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
SameBoy revision: 213a12ce93d66b105a113debd9396306066a7cfc
Core executable: f4724e266a7165d683ef643828333eb5136048e161bf08484f176832700c27f6
```

Import/calibrate, using the existing read-only core runner:

```sh
python3 -B -m tools.dex_timing.probes.import_starting_states \
  --states /Applications/SameBoy/Games \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --output build/dex-timing-additional-actual-states \
  --fixtures tools/dex_timing/fixtures --jobs 4
python3 -B -m tools.dex_timing.finish_experiment --actual-states \
  --mode eight budget early-budget --jobs 8 \
  --output build/dex-timing-finish-actual-final
python3 -B -m tools.dex_timing.finish_experiment --actual-states \
  --mode early-budget --jobs 8 \
  --timer-delay-t 64 864 1664 2464 3264 4064 4864 5664 6464 7264 8064 8864 9664 10464 11264 12064 \
  --output build/dex-timing-finish-phase-validated
python3 -B -m tools.dex_timing.finish_experiment --actual-states \
  --mode early-budget --jobs 8 --dispatch-t 256 1024 2048 \
  --viewport-guard-t 64 256 --finish-guard-t 256 1024 \
  --output build/dex-timing-finish-costs-validated
python3 -B tools/test_dex_timing.py
```

Each run includes input/source hashes, full publications and misses, per-attempt
cost/admission reasons, observed finishing spans, audio-reserve checks, and
hardware/map audits. Omitting `--actual-states` deliberately retains historical
partial-state controls for the six newly supplied sampled species. Earlier
`finish-initial`, `finish-drained`, `finish-controls`, `finish-early-controls`,
`finish-actual-initial`, `finish-actual-phase`, and `finish-final-costs` directories
are development history, not the final matrices above.

Regression tests retain both passing actual-start runs and failing controls;
they also cover sanitized fixture identity, queue-inclusive costs, stopped versus
disabled timers, low audio runway, unsupported pitch, and admission rejection.
Verification completed: the 181-test full suite and the subsequently added
actual-Garchomp phase-failure regression both pass. All 279 final comparison
reports match the current host-source hashes. Repository/SameBoy ROM hashes
remain identical to the pinned value above; `git diff --check` passes.
