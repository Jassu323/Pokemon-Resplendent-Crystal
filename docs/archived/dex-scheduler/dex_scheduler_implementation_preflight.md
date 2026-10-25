# Selected Dex Scheduler Implementation Pre-Flight

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Date: 2026-09-20.

## Status And Scope

Historical pre-flight. The cohesive implementation is now linked; see the
[living scheduler reference](../../pokedex_animation_scheduler.md) and
[validation/test guide](../../dex_scheduler_validation.md) for current behavior and
the final resource bill. Figures below intentionally preserve the draft rather
than retroactively presenting it as the integrated code. The final link saves
4,951 occupied ROM bytes, versus this draft's projected 4,954.

This is the concrete resource/design follow-up to the
[headroom and synthesized-cry investigation](dex_headroom_synth_results.md).
It is not a game implementation or a new test cartridge. Game ASM, ROM, symbols,
save states and SRAM have not been changed by this pre-flight.

A standalone RGBDS draft under `tools/dex_timing/preflight/owner_policy.asm`
provides actual assembled byte counts rather than estimates of how large the
new branches might be. It is deliberately outside `main.asm` and the game
Makefile. The driver is `tools/dex_timing/implementation_preflight.py`.

The bill below is exact for these assembled fragments, the specified removals,
and the six verified tail-call replacements. It is not a final linked-game bill:
integrating those fragments, auditing the new interrupt/ownership boundaries,
and replaying their actual instructions are still required. Any resulting
adjustment must be reflected in the bill and regenerated timing thresholds.

## Recommended Architecture

Keep the tested two-slot streaming model. Do not add another producer thread,
another full-frame buffer, a resident whole-animation dictionary in VRAM, a new
animation asset format, or double CPU speed.

The changes are one scheduler correction with bounded finishing work and two
copy optimizations. The successful host candidate is the basis, not the old
micro-schedule indexed by how often the producer happened to be called.

Retain these current parameters for this iteration:

- Normal CPU speed, 70,224 T-cycles per hardware display interval.
- Startup lead of up to 96 animation-tail tiles, in addition to the base image.
- Existing six-tile compressed dictionary streams.
- Up to 20 tiles in a regular gather/upload operation.
- Two existing 49-tile VRAM slots.
- Global sampled-cry prefill of 32 blocks; existing eight-block refill service.
- Authored main animation, base hold, idle animation and event durations.
- Existing resident-stage fast path and precomputed source/cell frame plans.
- Existing exact timelines and per-event dictionary high-water targets.

The settled-playback host matrix passed for ten species/forms including active
synthesized Exeggcute audio, with no change to their intended publication
intervals. That is not yet a guarantee for cold entry, input handoffs, every
species or the concrete draft below.

## Order Of Operations

### 1. Establish Selected Ownership

The existing entry/paging path stages the base picture, prepares its initial
animation work and reveals the Selected UI. After that reveal has actually
published the empty OAM and the intended viewport, acquire a quiet display
ownership tag before queuing the first animation publication.

`PolicyAcquireQuietOwner` checks that no competing BG, palette, DMA, tile-request,
map-animation or owner-transition work is queued. It also checks all four
viewport shadows against the hardware registers. Its caller must supply the
already-published-empty-OAM guarantee; testing `hOAMUpdate` alone cannot prove
that guarantee.

The proposed tag uses bit 7 of the existing `hVBlank` byte:

- `$80`: quiet Selected ownership, ordinary VBlank handler.
- `$87`: quiet Selected ownership, pending Dex VBlank work.
- Low three bits still select the existing eight handlers. The current entry
  already masks them with 7; no ninth handler/table entry is needed.

`hOAMUpdate = 1` retains already-published empty OAM. A six-byte check in
`VBlank_Normal` skips only the four unchanged scroll/window register copies
while the explicit ownership tag is set. Normal sound, timer, joypad and other
VBlank work still runs. This is not permission to ignore a newly queued request.

Release the tag and OAM suppression before canceling/changing species, leaving
Selected, changing the view, or starting Description text-page work. Cancellation
is the shared release point; the Description-toggle path needs its own release
because it does not currently cancel animation preparation. Reacquire only after
the reveal contract is satisfied again.

This avoids reading a reused WRAM union byte as a global ownership flag. The
global handler first sees an explicitly owned HRAM dispatch tag. It introduces
new meaning for one existing HRAM bit, **not another HRAM byte**.

### 2. Track Display Time Separately From Work

Replace the two outer-loop calls in `engine/pokedex/pokedex.asm` with calls to
owner-local begin/end wrappers in the animation bank. Begin records the hardware
display counter before input handling, clears the per-iteration finishing flag,
then executes the existing joypad-delay routine.

The animation deadline remains the authored deadline. The last regular work
tick records when an actual decode/upload action was selected; an idle call does
not consume a work slot or advance an artificial schedule cursor.

The wrapper is owner pacing, not a replacement global `DelayFrame` API. Nested
waits and unrelated owners continue using the existing routine.
Other Dex states pass through to their existing joypad/wait behavior, but pay
the additional far-call/wrapper overhead. Listing responsiveness is therefore
part of the required regression tests, not assumed unchanged instruction-wise.

### 3. Choose Useful Regular Work

Keep `Pokedex_PrepareDescriptionAnimation` and stage construction/finalization.
Replace `Pokedex_GetNextAnimationScheduleAction` and its run cursor with a
readiness decision:

1. If a regular action already started this display tick, do not start another.
2. If the nondisplayed stage has a ready source prefix, upload it first.
3. Otherwise, if the dictionary is below the retained event high-water target,
   decode the next existing stream.
4. Otherwise, return without work. Do not advance a fictitious action clock.

The upload helper retains its existing cap and ownership checks. A high-water
target means "decode at least this many dictionary tiles in total," not "upload
this many tiles now." Decoded dictionary data is retained and reusable across
many animation events.

### 4. Opportunistically Finish One Complete Remainder

Immediately after the ordinary producer action, before its diagnostic
bookkeeping, consider one additional **complete** stage remainder of 1-20 tiles.
Require all of these:

- Steady Selected ownership and active animation playback.
- A valid stage that is not ready, pending, published or ended.
- Stage slot different from the displayed slot.
- Every remaining source tile decoded and available.
- A future/current publication deadline on the shared display clock.
- Normal CPU speed and a measured timer/short-STAT-handler configuration.
- Enough visible time for gather, launch, transfer, bookkeeping and map queue,
  with an additional **8,192-T finishing reserve**.
- Enough cached audio for that chain and the following refill opportunity.

The sorted-source property already enforced by generated frame plans allows a
constant-time last-source readiness check. The pre-flight independently loaded
all 399 linked assets/forms and checked all 1,722 non-base frame plans.

Admit the entire chain or do none of this optional work. On admission, upload the
remainder and immediately queue the completed maps. Do not loop until a stage
finishes, increase authored holds, skip frames or silently suppress underruns.

### 5. Publish At The Authored Deadline

Keep the two-map VBlank transaction in `engine/pokedex/pokedex_3.asm`. Both
attributes and tile IDs complete before the display scans the new picture.

Add the pending/published guard at the actual queue boundary, not merely at
owner entry. A VBlank publication during preceding work must not cause a second
submission of the same event.

For quiet Selected ownership, accept publication only when `144 <= LY < 149`.
Other routes retain the earlier upper cutoff of 146. The lower check rejects
visible-time entry and the LY=0 readback early on physical line 153. Preserve the
ownership tag when setting or clearing the low-bit pending-work handler ID.

Faster queue copies reduce the critical work. The prior candidate's publication
margin and transfer measurements are evidence for the design, not a reason to
skip remeasuring these new concrete branches.

### 6. Refill Audio And Return Without An Unnecessary Extra Wait

The outer loop services deferred sampled audio after the useful owner work.
Compare the current display counter with the counter recorded at loop entry.
If that work already crossed a display interval, return to the next owner
iteration without adding another full-frame wait. Otherwise wait for VBlank.

After that outer wait, mark audio service due for the next owner's end. Nested
`DelayFrame` calls keep their existing refill behavior. This is a sequencing
change specific to Selected, not removal of refill opportunities or a change to
the global cry decoder/refill quota.

## Concrete ROM Bill

### Bank Deltas

These retain the current instrumentation. Savings from removing instrumentation
are not included.

| Bank | Planned change | Byte delta | Free after change |
| --- | --- | ---: | ---: |
| ROM0 `$00` | Quiet-viewport tag check | +6 | 656 total; 580 at Home tail |
| ROMX `$10` | Two outer-loop farcalls, offset by six tail-call substitutions | 0 | 0 |
| ROMX `$34` | Remove schedule pointer lookup and initialization | -58 | 2,548 |
| ROMX `$77` | Queue-copy unroll, queue guard, publication guard/tag handling | +60 | 2,960 |
| ROMX `$a0` | Decision, pacing, lifetime, finishing, tables, hooks, faster gather | +588 | 2,988 |
| ROMX `$a6` | Remove compact micro-schedule data and banked reader | -5,550 | 16,384 |
| **ROMX total** | **Net after specified packing** | **-4,960** | |

Including the six ROM0 bytes, occupied cartridge space falls by **4,954 bytes**.
The 4 MiB ROM file does not become smaller; these bytes become reusable link
space. No new ROMX bank or graphics-bank repacking is required.

Bank `$a6` currently contains 5,550 occupied bytes and 10,834 free bytes. Removing
its contents makes the whole bank reusable, but it would be incorrect to claim
16 KiB of newly recovered occupied data.

### Animation-Bank Detail

| Item in `$a0` | Net bytes |
| --- | ---: |
| 69-byte readiness decision replacing 32-byte schedule reader | +37 |
| 19-byte producer dispatch replacing 28-byte action switch | -9 |
| Begin/end owner pacing wrappers | +60 |
| Quiet ownership acquire/release helpers | +102 |
| Finishing eligibility, timing and audio-runway checks | +264 |
| Species-independent admission tables | +80 |
| Four integration CALL sites | +12 |
| Unroll the fixed 16-byte gather copy | +42 |
| **Total** | **+588** |

The `$77` increase comprises +30 bytes for two unrolled seven-byte copy loops,
+6 for the queue guard, +17 for the route-sensitive publication range check,
+4 for preserving the ownership tag when queuing and +3 when publication ends.

### The Full Main-Dex Bank

Bank `$10` is already full. Replacing `call JoyTextDelay` and the outer
`call DelayFrame` with two six-byte farcalls requires six bytes, not zero.

Six existing terminal `CALL routine / RET` pairs can become `JP routine`.
Each preserves the callee and its caller-visible return while saving one byte,
24 raw T-cycles and one transient return-address stack level at that site.
The exact original byte patterns were checked against the pinned ROM:

- Main Listing background -> selected frontpic corner placement.
- Entry background -> frontpic corner placement.
- Usual palettes -> object palette conversion.
- Legacy question-mark load -> close SRAM.
- Prepared selection -> prepare footprint.
- Prepared question-mark load -> close SRAM.

These are narrow packing changes within the same Dex module, not relocation of
the module or a bank-wide refactor. The real link must still check branch ranges.
No unrelated free ROM0 gap is needed to make the main-Dex bank fit.

## RAM And VRAM Bill

| Resource | Additional allocation | Explanation |
| --- | ---: | --- |
| WRAM0 | 0 bytes | Repurpose three already-allocated schedule-state bytes |
| WRAMX | 0 bytes | Retain dictionary scratch, audio cache and owner maps |
| HRAM | 0 bytes | Reuse `hVBlank` tag bit and existing counters/OAM flag |
| VRAM | 0 tiles | Retain the two 49-tile slots and current Listing cache |
| SRAM | 0 bytes | No save-format/state changes |

Current three-byte reuse at the present link:

| Address | Current purpose | Proposed purpose |
| --- | --- | --- |
| `$c7e0` | Schedule pointer low | Owner-loop starting display tick |
| `$c7e1` | Schedule pointer high | Last regular work-start display tick |
| `$c7e2` | Schedule run/action | Deferred-audio and finish-used bits |

These fields are already live scheduler allocations in the Dex union, not newly
claimed padding. Keep their extent when removing the diagnostic overlay later.
No change to `wBattleEnd`, the Miscellaneous union, another owner's scratch, or
following WRAM field addresses is required. Existing stack space is still used
for calls and temporary register saves; stack high-water remains an integration
test, not a new persistent allocation hidden by this table.

## Admission Tables And Measured CPU Costs

The 80-byte table is global, not per species:

- 20 exclusive latest-LY thresholds with the timer disabled.
- 20 with the enabled but inactive sampled handler/slow synthesized timer.
- 20 with active normal-pitch sampled playback.
- 20 audio-cache minimums for the active-sampled case.

The host generates these from the measured linked chain, not from a hand-tuned
"tiles per tick" quota. Each count has two limits: finishing before the visible
window ends with 8,192 T reserved, and reaching the existing HDMA launch cutoff.
Take the stricter threshold. Runtime uses table lookups/comparisons instead of
division, ceiling arithmetic or an iterative interrupt-bound calculation.

The draft rejects double speed, an alternate LCD handler, LCD-off use, visible
mode contradictions and unsupported/faster timer configurations. A short
bank-preserving masked snapshot reads audio counters consistently, then reopens
interrupts before the final LY gate. This concrete detail needs timed-IRQ replay;
it is not identical to the host's earlier instantaneous snapshot abstraction.

CPU-only draft checks found:

| Operation | Largest exercised raw cost |
| --- | ---: |
| Readiness decision including RET, excluding caller CALL | 428 T |
| Timing/audio admission helper including RET | 748 T |
| Full finish eligibility/admission through upload-call entry | 1,232 T |
| Audio snapshot interrupt-masked span, including delayed EI boundary | 160 T |
| Quiet viewport check | 32 T tagged; 28 T ordinary |

These are executed instruction costs with frozen hardware registers, **not**
interrupt-inclusive WCET or a new full-sequence timing result. In particular,
the complete finishing guard is larger than the admission helper alone. It must
replace the host allowances explicitly rather than being compared only with a
convenient smaller subset of old costs.

The common VBlank path pays 28 T, about 6.68 microseconds at normal speed, for
the untagged check. It does not change other owners' animation scheduling or
refill quotas. Tagged Selected avoids 96 T of redundant viewport copies.

The two already-tested copy changes remain:

- Queue construction: 12,596 -> 9,380 raw T, a 3,216-T saving, for +30 ROMX bytes.
- Per-tile copy body: 644 -> 392 raw T, a 252-T saving, for +42 ROMX bytes.
- Twenty-tile gather/upload prefix in the host probe: 19,956 -> 14,932 T.
  That probe includes a 16-T relocation trampoline not needed in-place.

HDMA itself is not made faster. The gains are cheaper work before launch,
cheaper queue assembly, and avoiding unnecessary waiting after an interval has
already elapsed.

## What We Can Remove Or Must Keep

### Remove With This Scheduler

- Micro-schedule payload: **4,703 bytes**.
- Its per-species/form pointer tables: **798 bytes**.
- Its fixed-bank reader: **49 bytes**.
- Its metadata pointer lookup: **43 bytes**.
- Its initializer code: **15 bytes**.
- The old 32-byte per-call run reader and obsolete switch arms, replaced and
  already netted into the bill.
- The micro-schedule generator, build dependencies and generated schedule files
  once the runtime no longer consumes them. Source/build cleanup adds no further
  cartridge savings beyond the linked data/code counted above.

Keep the timeline emitter and `set_timeline_targets`, which are separate from
the micro-schedule emitter. Replace/reclassify `validate_timeline_schedule`'s
old six-decodes-plus-twenty-uploads-per-tick feasibility claim: it cannot certify
this scheduler's real deadlines. Retain structural asset validation and use the
linked cost/replay checks for the actual timing contract. Shared parser/source
helpers are not dead merely because their former schedule caller disappears.

The three schedule-state bytes are **reused**, not also claimed as RAM savings.
Keep historical frozen fixtures/model support needed to reproduce the earlier
captures; those host files consume no cartridge ROM.

### Keep In This Iteration

| Retained metadata | Payload | Pointers | Total |
| --- | ---: | ---: | ---: |
| Frame plans/source ordering | 47,186 | 1,197 | **48,383 bytes** |
| Exact timelines, including high-water targets | 12,699 | 798 | **13,497 bytes** |
| New global finishing tables | 80 | 0 | **80 bytes** |
| **Total metadata after removal** | | | **61,960 bytes** |

The timelines contain 5,787 high-water bytes, one per serialized event. That is
a subset of their payload above, not another addition. Removing those targets
now would change the tested decode policy and require a replacement predictor
or runtime lookahead. It is not part of the current evidence-backed cleanup.

Frame plans eliminate the parsing/scanning work that previously made production
too expensive. The resident-stage fast path also remains useful. The original
animation scripts still serve other owners and asset generation, so the Dex's
exact timeline does not make them globally obsolete.

Keep both VRAM slots, both packed map/attribute pairs, owner backing buffers and
WRAM dictionary. Their ownership boundaries are used by the tested candidate.
Removing a copy/buffer or borrowing the Listing's 80 tiles would be a separate
architectural experiment, not a free consequence of this scheduler change.

An exact-byte inventory found no duplicate whole frame-plan or timeline payload
stored at distinct linked locations among these 399 assets. There is no further
whole-payload aliasing saving to claim. More aggressive compression, partial
sharing or high-water repacking would require a different reader/cost analysis.

Keep the global sampled-cry pair lookup (4,409 linked bytes in `$a4`, including
its associated linked content). It benefits the cry decoder independently of
the obsolete animation micro-schedule. The earlier uncompressed-dictionary
storage prototype is already absent; it cannot be counted as a new saving.

The `DEX_AB_*` alternative source branches are assembly-time options. Removing
their inactive alternatives is useful source cleanup but does not reclaim bytes
from the pinned normal build. Do not remove active Listing warming or alter the
96-tile startup lead in the name of cleanup.

## Validation And Next Implementation Gate

Completed in this pre-flight:

- RGBDS assembled the isolated draft successfully.
- 1,024 executed work-decision fixtures agree with the readiness policy.
- 600 executed timing/audio-admission fixtures pass.
- 20 full finishing-prefix fixtures reach upload with the one-shot flag set.
- 216,000 table cases match the host admission inequalities exactly.
- All 399 linked assets/forms and 1,722 non-base frame plans pass source checks.
- The six bank-packing byte patterns match the current linked code.
- The existing host regression suite passes all 197 tests.

Before treating the concrete implementation as validated:

1. Integrate the replacement in one scoped scheduler change, retaining the old
   cartridge and fixtures as rollback/reference inputs. Remove its unused
   micro-schedule dependencies at the same time; do not leave two active policy
   paths to fall back between silently.
2. Link normally, regenerate admission thresholds from those exact instructions
   and audit branch reach, bank headroom, register preservation and stack depth.
3. Replace the host's policy-cost allowances with the actual owner/guard code.
   Replay the 8,192-T phase/cost suite, including synthesized Exeggcute. Inspect
   the new atomic audio snapshot, both tagged VBlank paths and IRQ phase after
   the four replaced viewport writes.
4. Require correct maps/slots, exact authored intervals, no miss, no sampled
   underrun and safe VRAM/critical hardware writes. A changed route must not
   inherit the old 853-T publication margin without recomputation.
5. Then test cold/warm Listing entry, internal species paging, rapid input,
   B-cancel, footer/view changes and returning to the Listing. Existing separate
   Description-toggle corruption and synth-cry ownership bugs remain explicitly
   tracked; this pre-flight does not silently mark them fixed.

No additional user capture is needed to make this implementation attempt.
The candidate and costs are confined to the Dex. Party Stats, New Dex Entry,
battle animation owners and their independent outstanding cry/timing issues
are not included in the proposed runtime change.

## Reproduction And Identity

```sh
PYTHONPATH=tools python3 -B -m dex_timing.implementation_preflight
```

Output: `build/dex-timing-implementation-preflight/report.json`, with the
standalone assembly object, map and symbols. `cost-only.bin` is a fragment image,
not a playable ROM; do not install it in an emulator.

```text
Game ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
Symbols:  1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
RGBDS:    rgbasm v1.0.1
```
