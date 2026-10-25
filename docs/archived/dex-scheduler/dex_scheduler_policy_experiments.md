# Selected Dex Scheduler Policy Experiments: 2026-09-20

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

## Verdict

The first host-only scheduling experiments support changing work release,
owner wait behavior, and operation order. They do **not** yet establish a
complete, phase-independent runtime solution.

With the existing two VRAM slots, 96-tail-tile startup, 32-block audio prefill,
six-tile compressed streams, and existing decoder/upload routines, a bounded
candidate eliminates unfinished-stage misses in the three actual-initial-state
cases. All three sampled cries complete. However, Luxray and Dusknoir each
retain one late publication. A 16-phase-per-species synthetic timer sweep
additionally finds one unfinished-stage miss in six Dusknoir phases.

No game source, runtime instrumentation, ROM, symbols, assets, audio settings,
CPU speed, save file, or emulator state was changed. No game build or commit
was made. Host tools, tests, documentation, and ignored generated reports are
the only changes in this pass. The game resource cost of this investigation
is zero bytes in ROM0, ROMX, WRAM0, WRAMX, HRAM, and VRAM.

## Evidence Levels

Keep these three levels distinct:

1. **Unchanged linked baseline:** the real ROM instructions execute in the
   calibrated host replay. The independent SameBoy core still agrees at all
   1,515,328 non-HALT instruction starts across Weavile, Luxray, and Dusknoir,
   with every checkpoint register/state/timing comparison exact.
2. **Counterfactual scheduling:** the same starting memory and hardware model
   execute the existing stage/decode/gather/upload/map/audio/interrupt code.
   Host decisions replace the schedule reader and selected call/wait ordering.
   Those decisions carry explicit CPU-time charges, but are not assembled
   runtime code. Their results are conditional, not new emulator observations
   or an instruction-exact prediction of a future implementation.
3. **Synthetic phase controls:** future sample-timer reload phase and the
   corresponding divider phase vary. Initial memory, LCD phase, and already
   latched interrupt requests remain fixed. These are sensitivity experiments,
   not additional user captures or all reachable initial game states.

The first publication is the replay origin. These tests do not measure input
latency, cold/warm selection, internal paging preparation, or cancellation.
Changing operation ordering may affect those contracts in a real implementation.
All runs are normal-speed, normal-pitch, no-input Selected-page continuations.
The main animation, base hold, and idle sequence all execute; stable cleanup
time is not used as a substitute for authored animation duration.

## What Was Tested

All variants retain the existing timeline and deadline-controlled publication.
They leave unfinished-stage failure behavior visible. A lower underflow count
alone is not a pass: late and duplicate publications and wrong uploaded tile
bytes are also recorded.

| Policy | Host change |
|---|---|
| `baseline` | Observe the unchanged linked execution. |
| `wait` | If the Selected owner crossed VBlank while working, retain the normal audio service but omit waiting for another VBlank. |
| `handoff` | Add a pending/published ownership check at actual map submission, preventing resubmission of an already-published stage. |
| `clock` | Add display-released non-idle jobs tagged with event/progress targets, instead of advancing one schedule byte per call. |
| `early` | Replace late release slots with current safe eligibility: upload a ready prefix, otherwise decode toward the retained high-water target. One regular action per display counter. |
| `window` | Add a coarse 48-line pre-launch gathering reserve to `early`. This is a deliberately provisional admission experiment, not a certified bound. |
| `work-first` | Use `early`, but defer the outer frame-wait audio service until after the Selected owner has done its work. Execute the existing refill routine once, not a larger refill. |
| `tail` | Add at most one additional ready suffix of up to eight tiles before commit per owner iteration. No catch-up loop or new VRAM slot. |

All policies after `wait` include the wait and map-submission handoff guards.
`tail` includes `work-first`. Dictionary data and uploaded offsets remain real
progress, not an inferred consequence of elapsed time. A released upload job
is not executed against a different event's stage. Jobs lost because the
existing failure path already published a placeholder are reported as expired;
they are not claimed as completed uploads.

Hypothetical schedule dispatch costs 1,024 T in the primary comparison.
Guards cost 64 T each; injected CALL/RET costs are charged separately. These
charges run in interruptible four-T quanta. Existing routines still execute
their real instructions and incur the model's IRQ/DMA/wait costs. A 256, 512,
1,024, and 2,048-T dispatch sweep checks sensitivity to dispatch cost. These
allowances are not a proven runtime WCET, and four-T decision quanta do not
reproduce the interrupt alignment of an as-yet unwritten instruction sequence.

The suffix probe has a bounded call count and size, **not yet a proven elapsed
time admission bound**. It is feasibility evidence for replacing a rigid quota,
not a recommendation to insert an unconditional second upload in the game.

## Actual-Initial-State Results

Each cell is **unfinished-stage misses / late publications**. Counts cover the
entire main/base/idle sequence, not just the first failure.

| Policy | Weavile | Luxray | Dusknoir |
|---|---:|---:|---:|
| Linked baseline | 6 / 4 | 4 / 2 | 24 / 9 |
| Wait only | 6 / 3 | 2 / 14 | 21 / 7 |
| Wait + handoff guard | 6 / 3 | 6 / 2 | 21 / 7 |
| Display-released old work slots | 5 / 3 | 4 / 2 | 19 / 1 |
| Earlier eligible work | 2 / 2 | 1 / 1 | 0 / 1 |
| Coarse upload-window reserve | 4 / 2 | 5 / 1 | 0 / 1 |
| Earlier work + audio after owner | 2 / 0 | 0 / 1 | 0 / 1 |
| Above + bounded small suffix | 0 / 0 | 0 / 1 | 0 / 1 |

The wait-only Luxray result has **one duplicate publication** and shifts its
final publication from interval 92 to 95. This is a regression, despite its
lower underflow count. None of the handoff-guarded variants duplicates a
publication in this matrix. All other final publications remain at their
authored full-sequence interval: Weavile 78, Luxray 92, Dusknoir 174. That does
not excuse late intermediate frames. Dusknoir's 174 includes 107 main-animation
intervals, 18 base-picture hold intervals, and 49 idle intervals; the main
animation target has not changed.

Weavile and Luxray finish their cries in the baseline and all primary variants.
Dusknoir's baseline stops with 333 blocks remaining. It finishes naturally in
every non-baseline primary variant, retaining the original eight-block refill
routine and 32-block prefill. This demonstrates an important scheduling/refill
opportunity component; it is not proof of universal audio safety.

For the bounded suffix candidate, the animation-slot bytes match the asset's
expected tile data at every publication in all three actual-state cases.
This byte check is not a rendered-pixel, tilemap/attribute, or interactive UI
test. Underflow placeholders in failed variants remain separately visible in
the counters and byte mismatches.

The actual-state conclusions for `early` and `tail` remain the same throughout
the 256..2,048-T dispatch sweep. Thus their improvement is not dependent on
giving policy dispatch zero execution cost.

## Findings

### 1. A Shared Clock Is Necessary, Not Sufficient

Tagging the existing late work slots with real display release times improves
some cases, but retains failures. The schedule still releases uploads late,
and stage building, gathering, transfer, queue construction, interrupts, and
the owner shell still consume real time. Clock agreement cannot make those
operations free.

Earlier eligible work is materially more helpful than replaying the old
non-idle slots on the correct clock. These candidates do not require extra
ROMX payload or VRAM to obtain that improvement. They retain the existing
timeline, frame plans, dictionary format and high-water targets. This is not
approval to remove the old schedule or other metadata yet.

### 2. The Wait Contract And Publication Handoff Must Change Together

Skipping an extra frame wait changes when the owner can run. The wait-only
Luxray control exposes a submission race: the queued stage publishes in
VBlank, then mainline submits that same stage again. Finalization later adds
its duration a second time, shifting the rest of the sequence.

An owner-entry check alone is insufficient: VBlank can publish between that
check and the actual map submission. The guarded experiment checks both
pending and published ownership at `Pokedex_CommitAnimationFrontpicMap` entry.
If neither is set, there is no previously queued map for VBlank to publish
during construction. If either is set, mainline must defer to the existing
handoff instead of submitting again. The hypothetical guard preserves the
rest of the linked call path and includes a CPU-time charge.

This is a counterfactual regression exposed by altered ordering, not a new
claim that the supplied unchanged-ROM captures contained this duplicate.

### 3. A Fixed One-Action Quota Can Waste A Usable Short Transfer

With earlier work, Weavile still misses events 4 and 8: frame 4 needs 24 changed
tiles and only 20 are uploaded. These events follow a two-interval hold.
Moving audio after owner work removes their late-publication symptom but
still publishes an unfinished frame. The small-suffix probe permits the
remaining ready tiles to complete without a whole additional owner interval.
It eliminates these misses in the actual-state runs and the tested phases.

This is not equivalent to doubling a global tile quota. The prototype allows
only an already-decoded suffix of at most eight tiles, once per owner
iteration, under the existing stage ownership. A real scheduler still needs
an admission test for the complete suffix + map-queue path and audio reserve.

### 4. Ready Frames Can Lose The Publication Window To The Audio ISR

In the best actual-state candidate:

| Case | Event/frame | Authored interval | Actual interval | State at due interval |
|---|---|---:|---:|---|
| Luxray | Event 7 / frame 2 | 29 | 30 | 21/21 tiles uploaded, map pending, no competing map/DMA request |
| Dusknoir | Event 6 / frame 6 | 27 | 28 | 34/34 tiles uploaded, map pending, no competing map/DMA request |

The sampled-cry timer handler is already executing across the VBlank edge.
It is not preempted by VBlank. Its measured path takes **1,452 T**, about 3.18
scanlines. At map-publisher entry:

| Case | Timer starts relative to VBlank | Timer ends | Publisher enters |
|---|---:|---:|---:|
| Luxray | -746 T | +706 T | +1,130 T, LY 146 |
| Dusknoir | -946 T | +506 T | +930 T, LY 146 |

`Pokedex_VBlankAnimationFrontpicMap` rejects LY >= 146. The frame is already
ready, but publication is deferred one display interval. Neither more upfront
dictionary data nor a faster stage builder can resolve that particular check.

Do **not** simply raise the cutoff. The next investigation must account for
the complete critical VRAM transaction and remaining interrupt work, including
hardware access windows. Even existing accepted publication paths have whole
VBlank handlers extending into visible lines; the safe deadline concerns
specific hardware writes, not a blanket assumption that the entire handler
finishes inside VBlank. Post-cry music paths also change interrupt costs.

### 5. Producer Operations Have Substantial Real Costs

Representative maximum elapsed spans in the unchanged three-case baseline:

| Operation | Observed maximum | Display-interval fraction |
|---|---:|---:|
| Luxray stage construction | 50,840 T | 0.72 |
| Ready-tile gathering | 34,040 T | 0.48 |
| HDMA helper, including waits | 29,924 T | 0.43 |
| Map backing/queue construction | 22,228 T | 0.32 |
| One outer audio service | 27,860 T | 0.40 |
| Dictionary chunk service | 20,584 T | 0.29 |

These are observed maxima from different invocations/species, not universal
WCETs or one additive budget. Parent/child spans overlap. They include the
interrupts and waits encountered in their actual execution. They nevertheless
show why a quota-only validator cannot certify six decoded tiles plus twenty
uploaded tiles in every interval alongside all other work.

## Synthetic Phase Sweep

The `tail` policy was replayed with 16 different future sample-timer delays per
species: 64, 864, ... 12,064 T. The divider is shifted consistently; an already
pending timer IF bit is retained, not silently discarded. All use the same LCD
publication phase, initial memory and 1,024-T dispatch charge.

| Species | Runs | Runs with unfinished-stage misses | Late publications per run | Cry underruns |
|---|---:|---:|---:|---:|
| Weavile | 16 | 0 | 0..3 | 0 |
| Luxray | 16 | 0 | 0..2 | 0 |
| Dusknoir | 16 | 6, one miss each | 1..4 | 0 |

This is why the three captured-state successes must not be generalized into a
deadline guarantee. The remaining Dusknoir failures are informative:

- Delays 2,464, 3,264 and 4,064 T: event 6 has 29/34 uploaded, dictionary loaded
  through tile 210 (211 loaded), and 36 tiles undecoded. Its high-water target
  is 216. The remaining five stage tiles are not yet decoded. The naive
  upload-first policy spends services on available prefixes instead of making
  the next six-tile decode at a useful earlier point.
- At delay 2,464 T, upload service decisions occur at LY 112/130 for event 5
  and LY 111/131 for event 6. The blocking helper/gather paths consume later
  intervals. Decoding a needed chunk instead of entering an already-poor upload window is a
  concrete ordering alternative to test.
- Delay 7,264 T: event 5 publishes a tick late, and event 6 reaches its due
  check at 20/34 despite sufficient dictionary data.
- Delays 9,664 and 10,464 T: event 22 publishes a tick late; event 23 then
  reaches its deadline with 20/31 uploaded and the dictionary fully decoded.

Thus a bad publication window can shorten the next stage's usable preparation
time even though authored deadlines correctly remain fixed. Separately,
upload-prefix availability is not enough information for a good decode/upload
priority decision. The coarse upload-window-only control in the primary matrix
also worsens some results: blindly waiting is not a solution.

## Next Investigation

Follow-up: [publication-window and complete-critical-path results](dex_publication_budget_results.md)
now investigate items 1 and 2 below. Preserve this section as the earlier
decision record; use the follow-up for the latest successes, failed controls,
and remaining safety/admission work.

Continue host-side before implementing the game change:

1. Bound the actual publication transaction against the latest timer-ISR
   completion phase. Evaluate safe admission or interrupt/dispatch ordering;
   do not suppress the phase-dependent deferrals in the model.
2. Replace the naive upload-first rule with cost-aware decode/upload admission.
   Include gathering, helper cutoff, transfer, map queueing and audio reserve.
   Use the remaining Dusknoir phase controls and Weavile's short holds as
   explicit regression cases.
3. Re-run the captured states and phase controls, then broader species and
   owner/timer phases. The six older partial-capture inputs can be useful
   qualified controls, but are not equivalent to complete actual starts.
4. Only after this succeeds, preflight the Selected-only runtime change,
   memory lifetimes, ROM bank costs, metadata retention, and input/wait contract.
   Then validate the resulting assembled implementation and new captures.

No additional user save state, breakpoint capture, or video is needed for the
next two investigations. New capture will matter when validating the actual
runtime implementation and interactive paths. Nothing here proves a need for
extra VRAM or larger startup loading, nor rules out those options if more
complete budgeting later establishes a genuine capacity problem.

## Artifacts And Reproduction

Host implementation: `tools/dex_timing/scheduler_experiment.py`.
The calibrated `OwnerReplay` is unchanged. Its initial-state factory accepts an
optional replay class; the default remains the exact linked baseline.

Generated outputs (ignored by Git):

- `build/dex-full-replays-policy-baseline/`: renewed independent-core checks.
- `build/dex-timing-policies-final/`: eight primary policies, three species.
- `build/dex-timing-policies-cost-sweep/`: early/suffix dispatch-cost sensitivity.
- `build/dex-timing-policies-phases/`: 48 synthetic timer-phase continuations.

Reports contain ROM/symbol/fixture/host-source hashes, full operation ledgers,
policy decisions and their charged costs, publication data checks, map entry
states, timer/VBlank interrupt spans, misses, duplicates, and cry-stop reason.
Intermediate exploratory directories are not the final evidence matrix.

```sh
python3 -B -m tools.dex_timing.scheduler_experiment \
  --output build/dex-timing-policies-final --jobs 6

python3 -B -m tools.dex_timing.scheduler_experiment \
  --output build/dex-timing-policies-cost-sweep --policies early tail \
  --dispatch-t 256 512 1024 2048 --jobs 8

python3 -B -m tools.dex_timing.scheduler_experiment \
  --output build/dex-timing-policies-phases --policies tail --jobs 8 \
  --timer-delay-t 64 864 1664 2464 3264 4064 4864 5664 \
    6464 7264 8064 8864 9664 10464 11264 12064

python3 -B tools/test_dex_timing.py
```

Validation: **154 host tests pass**. New coverage includes unchanged-baseline
observation, wait-caller matching, ownership and completed-progress gating,
clock wrap, retained jobs, bounded suffixes, natural cry completion, preserved
late publications, timer-phase consistency, and a deliberately failing
Dusknoir phase that must continue to be reported.
