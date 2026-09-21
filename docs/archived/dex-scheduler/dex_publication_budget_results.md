# Selected Dex Publication Budget Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Date: 2026-09-20. Scope: **host-only counterfactual investigation** at normal
CPU speed. No ROM rebuild, game-source edit, emulator-state write, or runtime
resource allocation was made for this step.

Follow-up: [steady-display publication and recovery](dex_steady_publication_results.md)
addresses the critical-write bound under an explicit viewport/OAM ownership
contract, tests forced late entry, and broadens the species controls. It retains
a new Garchomp work-completion counterexample. Results below remain the record
of this earlier publication-budget step.

## Result

The previous [policy experiments](dex_scheduler_policy_experiments.md) left
two concrete problems: ready maps missing the narrow VBlank publication window,
and Dusknoir phase controls missing subsequent preparation deadlines.

With the previous `tail` policy, holding already-published empty OAM unchanged
and allowing publication when the sampled LY is below 149 produces:

- Zero unfinished-stage misses, late publications, duplicate publications, or
  sampled-cry underruns in all three actual-initial-state continuations.
- The same zero failures in 192 synthetic timer-phase continuations: 64 each
  for Weavile, Luxray, and Dusknoir.
- Correct published slot tile bytes and independently checked hardware
  tilemaps/attribute maps in every publication of those runs.
- All audited critical writes and map transfers finish inside physical VBlank.
  No competing palette, map, requested-tile, or tileset work is present.

This is **conditional feasibility evidence, not a runtime fix or a universal
deadline guarantee**. In particular, a blanket `CP 149` is not yet an acceptable
final implementation: its worst theoretical on-time margin is extremely small,
and its already-late branch can exceed VBlank. See the bound below.

The result weakens the case for immediately adding another producer, more VRAM,
larger startup loading, or more asset metadata. It does not prove that those
options are unnecessary for every species and interactive transition.

## Pinned Inputs And Unchanged Costs

The ROM remains:

```text
ROM  7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
SYM  1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
```

The three initial volatile-memory fixtures are the same actual save-state
exports used in the [end-to-end checks](dex_end_to_end_capture_results.md).
The unchanged linked baseline was previously matched at 1,515,328 non-HALT
instruction starts across those three inputs. The new read-only audit also
retains Luxray's six baseline checkpoint times exactly.

Candidates retain normal speed, two frame slots, 96 tail tiles of startup
lead, six-tile dictionary chunks, up to 20 tiles per ordinary upload, 32 audio
prefill blocks, and the same eight-block audio refill implementation. The
existing `tail` experiment additionally permits one ready suffix of at most
eight tiles per owner iteration. It is not an unlimited catch-up loop.

As before, `tail` includes earlier eligible work, separate clock/progress
tracking, the wait and handoff guards, and moving the outer audio service after
Selected work. These results do **not** mean that suppressing OAM alone fixes
the existing ROM. All linked decode, gather, upload, stage construction, map
queueing, audio, and interrupt instructions still execute. Hypothetical
scheduling decisions use explicit CPU-time charges, not zero-cost decisions.

## What The New Audit Measures

Host tool: `tools/dex_timing/budget_experiment.py`.

1. Map GDMA spans, including both full seven-row transfers and their stalls.
2. Critical native I/O stores at their bus-write M-cycle, after any pending
   HDMA/GDMA stall, not at the earlier outer interpreter boundary.
3. Conservative OAM completion, 648 T after its DMA-register write. This is a
   deadline check only; it is not added again to CPU execution time. The
   existing HRAM busy loop already executes in the replay.
4. Completion within the same **physical** 4,560-T VBlank. LY's early reset on
   line 153 and wrap to the next VBlank cannot masquerade as safe completion.
5. The 49 displayed tile IDs and 49 attributes read from physical VRAM,
   independently reconstructed from the asset plan. Slot pixels are checked
   separately against the decoded dictionary. Failed controls remain failures;
   the audit does not replace bad pixels/maps with expected data.

This is not a pixel renderer or a complete proof of all display-bus behavior.
The hardware rules remain those of the calibrated CGB-E, normal-speed,
BG-only Selected continuation. The OAM allowance is grounded in the local
SameBoy `Core/memory.c` DMA start/progress paths and this ROM's HRAM DMA loop.

## Why Widening The Window Alone Is Insufficient

In the captured Luxray candidate, the audio timer ISR overlaps VBlank. With
the old guard, the already-ready event 7/frame 2 waits until interval 30 instead
of 29. Raising the guard allows both map banks to complete at VBlank phase
2,626 T. However, `VBlank_Normal` then updates the scroll/window registers,
checks other requests, and performs OAM DMA.

That DMA starts at phase 3,994 T. Its conservative completion is **4,642 T**,
82 T beyond the 4,560-T VBlank. The maps are correct and on time, but the whole
critical hardware path fails the audit. This is not a measured visible glitch
and is not grounds to assert that empty OAM necessarily corrupts line 0; it is
a reason not to declare the widened path safely budgeted.

## OAM Ownership Control

All three actual starting fixtures contain 160 zero shadow-OAM bytes, already
equal to physical OAM. During the tested, no-input Description animation, they
do not change. `PokedexSelectedMon_Update` uses BG tiles for its footer cursor.
Repeating the empty shadow-OAM transfer therefore does no useful display work.

The counterfactual sets the existing `hOAMUpdate` suppression flag to one at
the first masked publication. A 48-T setup charge accounts for preserving AF,
loading/storing the flag, and restoring AF. The ordinary VBlank path then
skips the DMA using its existing branch. No new HRAM/WRAM flag is invented.

The host rejects a nonempty or mismatched initial OAM image, and rechecks shadow
OAM and the suppression flag at each owner-loop boundary during this continuation.
It also logs every competing normal-VBlank transfer request. All successful
matrix runs have zero such requests.

Skipping this branch saves **700 T of linked CPU work per VBlank**. The last
critical hardware action also moves earlier: scroll/window writes no longer
have the later OAM completion deadline attached. This both shortens CPU work
and makes the critical publication window easier to satisfy.

This lifetime must be scoped to the current Selected owner. Listing, initial
clearing/reveal, species changes, Area, return-to-Listing, and future OAM-based
type icons require explicit handoff rules. The host continuation does not test
those operations or authorize suppressing their required OAM updates.

## Actual-State Controls

Numbers are unfinished-stage misses / late publications. Each row executes
the full main animation, base hold, idle sequence, and cry cleanup.

| Policy | Weavile | Luxray | Dusknoir | Critical hardware result |
|---|---:|---:|---:|---|
| Unchanged ROM | 6 / 4 | 4 / 2 | 24 / 9 | All audited writes within VBlank |
| Previous `tail`, original cutoff | 0 / 0 | 0 / 1 | 0 / 1 | Within VBlank |
| `tail`, cutoff 149 only | 0 / 0 | 0 / 0 | 0 / 0 | Luxray OAM exceeds the conservative deadline |
| `tail`, quiet OAM only | 0 / 0 | 0 / 1 | 0 / 1 | Within VBlank |
| `tail`, quiet OAM, cutoff 148 | 0 / 0 | 0 / 0 | 0 / 0 | Within VBlank in these three starts |
| `tail`, quiet OAM, cutoff 149 | 0 / 0 | 0 / 0 | 0 / 0 | Within VBlank in these three starts |

All candidate cries complete naturally. The unchanged-ROM Dusknoir control
retains its captured underrun with 333 blocks left. The baseline also retains
its incorrect published maps/slot contents; these are not removed by the audit.

The cutoff-148 control is not sufficient across phases. Sixteen Dusknoir runs
retain seven late publications and one unfinished-stage miss. In delay 10,464 T,
event 22/frame 1 is ready with all 30/30 tiles and all 247 dictionary tiles
decoded, but LY 148 fails the guard. It publishes at interval 83 instead of 82.
Event 23/frame 7 then misses with 20/31 tiles uploaded, a fully decoded
dictionary, and 90 audio blocks cached. Its slot and map failure remain visible
in the report. This is a concrete late-publication-to-next-stage failure chain,
not evidence that this event needs a faster decompressor or more dictionary
preload. The same phase passes with cutoff 149 and quiet OAM.

The successful full timeline endpoints are Weavile 78, Luxray 92, and Dusknoir
174 display intervals. Dusknoir's 174 comprises its 107-interval main animation,
18-interval base hold, and 49-interval idle sequence. Every intermediate event
is checked, not just the final endpoint or later mainline cleanup time.

## Phase And Dispatch-Cost Sensitivity

The dense sweep uses future timer delays 64, 264, ... 12,664 T. Only the timer
phase/divider is perturbed; LCD origin and all initial memory remain fixed.
Already-pending IF bits are retained. These are **synthetic controls**, not 192
new user captures or an exhaustive scan of all possible starting states.

| Species | Runs | Animation misses / late maps | Cry underruns | Latest critical-write end | VBlank margin |
|---|---:|---:|---:|---:|---:|
| Weavile | 64 | 0 / 0 | 0 | 4,150 T | 410 T |
| Luxray | 64 | 0 / 0 | 0 | 4,178 T | 382 T |
| Dusknoir | 64 | 0 / 0 | 0 | 4,182 T | 378 T |

These are observed margins, not universal bounds. All map transfers also finish
within VBlank, with maximum end phases 3,322 / 3,350 / 3,354 T respectively.

An additional 144 runs use 256-, 512-, and 2,048-T scheduling-dispatch charges,
16 timer phases, and all three species. They also have zero failures. The main
dense sweep uses 1,024 T. This is implementation-cost sensitivity, not a promise
that an as-yet-unwritten runtime dispatcher has any particular cost.

## Publication Bound And Remaining Safety Work

The host enumerates 144 linked branch/counter-carry combinations, from the LY
comparison through the last critical write/OAM completion. Other palette,
background, requested-tile, and tileset requests must be idle.

| OAM behavior | On-time publication maximum | Already-late publication maximum |
|---|---:|---:|
| Ordinary OAM DMA | 3,464 T | 3,604 T |
| Quiet OAM | 2,276 T | 2,416 T |

Both GDMA stalls are included. The additional 140 T on the late branch comes
from its deadline/trace bookkeeping path. The whole VBlank handler may run
longer because joypad, sound, and game-time work follows the critical writes;
those instructions are not incorrectly required to finish within VBlank.

An LY=148 sample can occur near that line's end. Account for up to four T from
the read to the comparison: the latest conservative comparison phase is
`5 * 456 - 1 + 4 = 2,283 T`. Adding the on-time maximum yields **4,559 T**, only
one T before the physical boundary. Adding the late maximum yields **4,699 T**,
which fails. The actual dense sweep reaches the comparison much earlier,
at most phase 1,962 T, explaining its larger observed margin.

Therefore:

- Do not promote `CP 149` unconditionally merely because the replays pass.
- A runtime design must either establish a tighter reachable-entry bound,
  distinguish a later on-time admission from an earlier late/recovery admission,
  or shorten/reorder the critical bookkeeping path to retain a real margin.
- A new admission decision must itself be timed before its LY check. Choosing
  a threshold for free in the host and ignoring its runtime cost is not valid.
- The bounds here do not apply when another owner requests palettes, BG maps,
  tile copies, changed OAM, or a different display configuration.

This is the next publication investigation, not a recommendation to apply a
one-byte guard change to the game.

## Decode Versus Upload Preference

The second experiment estimates the linked CPU work before the HDMA helper,
including gathering into scratch, for one to 20 ready tiles. It enumerates both
slots and both short-prefix exits, and adds a 128-T caller/trace allowance.

| Ready tiles | CPU prefix bound | Interrupt-expanded prefix/launch allowance |
|---|---:|---:|
| 4 | 5,188 T | 11,772 T |
| 8 | 8,932 T | 18,616 T |
| 13 | 13,612 T | 24,808 T |
| 20 | 20,116 T | 35,276 T |

The fixed-point response calculation includes helper setup/poll slack, a
potentially pending plus periodic 1,480-T timer handler and 108-T short STAT
handler. It makes a fit claim only when the whole prefix stays in visible
lines without crossing VBlank. It is not a bound for arbitrary pitches,
interrupt configurations, or another owner's display mode.

When that estimate will miss the helper's visible launch window, the candidate
decodes a useful chunk instead, if the retained high-water target still needs
one. When there is no useful decode alternative, it retains the upload; it
does not insert an unconditional idle wait.

Across 48 cutoff-149/quiet-OAM runs, this changes 159 upload choices into decode
choices. All 48 pass. However, the same 48 timer phases already pass without
this preference after the publication/OAM adjustment. It is not established
as necessary, and should not automatically become another runtime subsystem.

Despite the `--admission` experimental option name, this is only a **prefix
ordering preference**. It does not yet certify the complete gather + transfer
+ map queue + audio reserve path. The existing bounded suffix also still needs
a complete-chain admission rule for a production implementation. The data do
not justify pretending that six decodes and twenty uploads always fit per tick.

## Recommended Next Step

Stay host-side for one more safety/preflight pass:

1. Resolve the on-time versus late-publication bound above with charged decision
   costs. Preserve deliberate failing controls instead of widening windows until
   failures disappear. Keep initial reveal and later interactive owner handoffs
   outside the quiet-OAM shortcut unless their contracts are explicitly checked.
2. Re-run the three actual starts and phase/cost controls with that final rule.
   Extend to the other six species as qualified partial-capture controls; obtain
   a fresh complete start only if an ambiguity requires it.
3. Make a complete-chain budget for the small suffix and any decode/upload
   preference retained in the final design. Do not add complexity merely because
   the experiment can express it.
4. Preflight the assembled Selected-only implementation, metadata retirement,
   memory ownership, and interactive paths before modifying game code. Validate
   new ROM behavior with fresh SameBoy captures afterward.

No further user capture, save state, or video is needed for the next host-side
step. Selection/paging latency before first publication is not measured by
these continuations; no startup-performance improvement is claimed.

## Artifacts And Regression Coverage

Generated reports are ignored by Git; this document preserves essential results.

- `build/dex-timing-budget-final-controls/`: 18 actual-start control runs.
- `build/dex-timing-budget-final-dense/`: 192 phase continuations.
- `build/dex-timing-budget-final-costs/`: 144 dispatch-cost controls.
- `build/dex-timing-budget-final-admission/`: 48 prefix-preference controls.
- `build/dex-timing-budget-final-conservative/`: 16 cutoff-148 Dusknoir controls,
  including the deliberately retained downstream failure.
- `build/dex-timing-budget-bounds.json`: linked publication/prefix bounds.

Each continuation includes ROM/symbol/fixture/host-source hashes, the original
operation ledger, decisions, interrupts, slot/map checks, and critical writes.
Earlier exploratory `dex-timing-budget-*` folders are not the final matrix.

Example reproduction:

```sh
python3 -B -m tools.dex_timing.budget_experiment \
  --output build/dex-timing-budget-example --cutoff 149 --quiet-oam --jobs 8 \
  --timer-delay-t 64 864 1664 2464 3264 4064 4864 5664 \
    6464 7264 8064 8864 9664 10464 11264 12064

# Add --admission for the prefix-preference control, or use
# --dispatch-t 256 512 2048 for the dispatch-cost sensitivity matrix.

python3 -B tools/test_dex_timing.py
```

Validation: **166 host tests pass**. Coverage includes unchanged baseline
timing, physical-frame wrap, conservative OAM completion, the unsafe widened
Luxray control, OAM lifetime rejection, asset-derived map verification, the
three successful actual starts, prior failing Dusknoir phases, branch/carry
bounds, linked upload-prefix costs, and the safe-but-too-early publication
control that produces a downstream miss despite a completely decoded dictionary.
