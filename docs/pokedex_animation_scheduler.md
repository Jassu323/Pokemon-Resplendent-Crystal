# Selected Pokedex Animation Scheduler

Living implementation reference, updated 2026-10-05.

The production Dex now inherits the double-speed world clock. Physical event
deadlines, the two-slot producer and 32-block prefill are unchanged. Bounded
active Info admission, quiet batching and Area/cache optimizations are detailed
in the [production clock policy](production_clock_policy.md); costs and test
results from older revisions below remain historical measurements.

This describes the **linked game implementation**, not an experimental host
policy. It supersedes the runtime direction in the earlier micro-schedule
investigations. Preserve those investigations as evidence; update this document
whenever the runtime, asset format, ownership contract or measured costs change.

Companion documents:

- [Instrumentation cleanup and current results](dex_instrumentation_cleanup.md)
- [Validation and emulator test procedure](dex_scheduler_validation.md)
- [All-species normal-input cold Listing results](dex_cold_listing_results.md)
- [VRAM and scratch allocation](pokedex_vram.md)
- [New Dex Entry resident scheduler](new_dex_entry_animation_scheduler.md)
- [Selected-to-Listing restoration contract and results](pokedex_listing_restoration_investigation.md)
- [Description text transaction and regression results](pokedex_description_paging_investigation.md#implemented-transaction)
- [Outstanding bugs](pokedex_selected_bug_backlog.md)
- [Historical implementation pre-flight](archived/dex-scheduler/dex_scheduler_implementation_preflight.md)
- [Investigation record](archived/dex-scheduler/dex_scheduler_investigation.md)

## Scope And Guarantees

The owner is the Start-menu Pokedex's Selected Description screen on CGB. This
change does not migrate Party Stats or battle animation owners. New Dex Entry
now has a separate resident scheduler (linked above), not this two-slot owner.
They share frontpic metadata, exact timelines and audio code, not VRAM ownership.

Goals, in order:

1. Publish every authored animation event at its intended hardware interval.
2. Keep audio supplied without lengthening authored holds or masking underruns.
3. Keep selection and paging responsive; retain useful Listing warming.
4. Avoid additional ROM0, WRAM and HRAM allocations where practical.
5. Use an explicit, auditable owner contract instead of implicit bank state.

The linked replay suite meets the exact timelines for its tested species.
That is evidence for this implementation, not proof that every species, future
asset, user-input sequence or display owner is schedulable. New assets still
require structural validation and representative timed replay. The current
integration starts at a relocated first-publication state. The separate
normal-input cold Listing suite now covers real selection/startup and complete
playback for all 373 New Dex species, with exact timelines and no misses. It
originally exposed a separate Drapion static-reveal text overflow (`DEX-UI-02`,
since corrected). It
boots a copied save and never injects producer state. This complements the
user's all-species internal-paging pass; it does not cover every input or owner
handoff. See the cold Listing results for the precise checks and limitations.

The expanded live suite exposed two Groudon misses in the inherited
three-event decode-lookahead policy. An exact actual-stack replay and a
successful earlier-decoding control are documented in
[Groudon results](archived/dex-scheduler/dex_groudon_target_results.md). The target correction is now
implemented in the asset generator: startup is unchanged, but every later
event permits decoding through the dictionary's end. No runtime instructions,
work quotas, publication deadlines or memory allocations changed.
The broader [target-policy regression](archived/dex-scheduler/dex_target_regression_results.md) now
passes all 18 captured species at their initial phase and six additional timer
phases, including active synthesized audio. It supports an earlier post-start
decoding horizon while leaving the first-event/startup target unchanged.
The Spheal/Sealeo/Snorlax follow-up also checks unused dictionary tails: Spheal
does eight extra bounded decode calls but retains exact publication and cry
timing; the two fully preloaded controls add no decoding.
The user reports that the rebuilt ROM passes cold Listing entry and internal
paging on the sampled stress suite and thirteen synthesized controls, without
either miss breakpoint firing. Warm-entry testing is deliberately deferred;
Listing warming remains implemented, pending a separate removal. Seviper's
script-only repeat fix and Unown's test-save display-form correction passed
manual cold/internal entry and the automated cold suite. Commit cleanup and
other owner/transaction checks remain in the validation guide.

### Retained Parameters

| Parameter | Value |
| --- | --- |
| CPU | Normal speed; 4,194,304 T-cycles/second |
| Hardware display interval | 70,224 T; 154 lines of 456 T |
| VBlank | 10 lines, 4,560 T |
| Startup dictionary lead | Up to 96 tail tiles, plus the native base image |
| Dictionary stream | At most 6 decompressed tiles |
| Regular upload | At most 20 ready tiles |
| Optional finishing upload | One complete remainder of 1-20 ready tiles |
| VRAM slots | Two existing 49-tile regions |
| Sampled cry | Existing 32-block prefill and at-most-8-block refill |
| Optional finishing reserve | 8,192 T beyond the bounded work chain |

**96 startup tiles means decoded dictionary tiles in WRAM, not 96 additional
resident VRAM tiles.** Startup also finishes the first visual stage. Only that
stage's needed changed cells are uploaded to its slot. The fixed lead is capped
by the dictionary's end; a larger first-frame requirement must still be met.

## Components And Ownership

| Source | Responsibility |
| --- | --- |
| `engine/pokedex/pokedex.asm` | Dex outer loop, shared constants, Listing owner |
| `engine/pokedex/pokedex_detail.asm` | Selected entry, input, species/view changes, exit |
| `engine/pokedex/pokedex_description_text.asm` | Bounded lower-text staging with animation-first admission and cancellation |
| `engine/pokedex/pokedex_animation.asm` | Dictionary cursor, stage maps, gather/upload, deadlines |
| `engine/pokedex/pokedex_animation_policy.asm` | Display-clock work choice, pacing, quiet ownership, finishing admission |
| `engine/pokedex/pokedex_animation_timeline.asm` | Fixed-bank exact-event reader |
| `engine/pokedex/pokedex_3.asm` | Queue backing maps and atomically publish both maps in VBlank |
| `engine/gfx/load_pics.asm` | Base-only preparation and retained tail cursor |
| `engine/gfx/pic_animation.asm` | Frame-plan/timeline pointer access shared with asset setup |
| `home/vblank.asm` | Existing dispatcher and explicit quiet-viewport tag check |
| `tools/pokemon_animation.c` | Frame plans, timelines, high-water targets, structural checks |
| `tools/dex_timing/finish_bounds.py` | Recompute finishing thresholds from linked code |
| `tools/dex_timing/integrated_replay.py` | Execute the linked owner, optionally compare to SameBoy |
| `tools/dex_timing/cold_listing.py` | Boot an isolated save and audit real-input cold entry for every New Dex species |

There is one mainline producer, not two concurrent CPU workers. The two VRAM
slots separate the currently visible frame from work being prepared. VBlank
publishes a completed or deliberately incomplete stage; the sampled timer
consumes audio independently. Mainline owns decoding, staging and audio refill.

### Three Separate Things To Track

- **Time:** `hVBlankCounter` and the absolute `wPokedexAnimDeadline`.
- **Completed work:** decoded dictionary cursor, stage tile count/upload offset,
  valid/ready flags and resident-frame identities.
- **Published display:** pending/published map flags and displayed-slot identity.

Elapsed time does not mean work completed. A missed producer opportunity does
not consume a work-queue entry. Conversely, preparing a stage early does not
permit revealing it early.

## Data Formats

### Dictionary

Frontpic containers start with a native base-pose LZ stream, followed by
independently decodable tail streams of at most six tiles. The tail's ROM bank,
source pointer, WRAM destination and remaining count persist across services.
WRAMX bank 6 holds the decoded dictionary. Already decoded tiles are reusable
by any later animation frame; decoding them again is unnecessary.

The static base is padded directly into a 7x7 image. Padding must not corrupt
the native dictionary: the earlier stray-line bug is why these views must not
be treated as interchangeable in-place buffers.

### Per-Frame Plan

The generated record supplies a changed-cell count and dictionary high-water
mark, followed by direct position/source pairs. Base-tile references precede
tail references; tail sources are nondecreasing. This removes runtime bitmask
expansion, coordinate reconstruction, a large lookup-table clear, dictionary
scanning, deduplication and sorting.

Each changed tail cell gets its own slot tile. Identical sources may therefore
appear more than once. That modest duplication is intentional: it avoids a
costly runtime remapping structure. The current 1,722 non-base plans contain
only 37 such extra copies among 20,149 changed cells.

Sorted sources have two important uses:

1. A newly decoded prefix immediately exposes a contiguous uploadable prefix.
2. The final source ID proves whether **every** remaining source is available.

Do not change source ordering without updating both producer and admission
checks. The host loader validates it for all 399 current assets/forms.

### Timeline And High-Water Target

The timeline expands the authored main script, base hold and idle script into
visual events. It is not a schedule of CPU calls. Each ordinary event stores a
frame ID, duration and dictionary target. Short durations share a packed byte
with the frame ID; longer durations use an extension byte. Finish/loop markers
are handled by the fixed-bank reader. Durations are constrained to 1-127.

The target is a permitted decoded-dictionary extent, **not** a number of tiles
to upload now. Its generation has two deliberately different rules:

1. Event 1 retains the original startup target: the larger of the capped
   native-base-plus-96-tile lead and the current/next-two-event high-water marks,
   including relevant loop successors. It does not preload the full dictionary.
2. Every subsequent event targets the full dictionary extent. Once that event
   is prepared, otherwise available regular-work opportunities can decode
   future six-tile streams without waiting for their poses to enter a short
   lookahead window. Ready uploads still take priority.

The decoder still stops at its target/end and performs at most one regular
action per display counter. This is early release of bounded work, not an
unbounded decoder loop or an additional upload. Decoded tiles stay in WRAMX 6;
the two existing VRAM slots and their publication rules are unchanged.

Groudon demonstrated why the old current-plus-two-event horizon was insufficient:
repeated early poses withheld useful decoding until later deadlines were too
close. The new rule removes that restriction without increasing entry work.
It may decode unused tail tiles: Spheal adds eight bounded calls for 45 tiles
in the regression suite, with unchanged publication and cry-completion timing.
No new target table or expanded record is needed; the existing target byte is
reused. Future species still require timing validation, not just valid bounds.

The generator now verifies structure and source bounds. It no longer claims
that six decoded tiles plus twenty uploaded tiles can always fit into every
display interval. Only a timing analysis of the linked paths can establish
that sort of feasibility.

The compact micro-schedule, its pointer reader, run cursor and build generator
have been removed. Historical host fixtures retain support for reading old
ROMs solely to reproduce the investigation.

## Entry And Startup

1. Listing movement prepares the new static base and footprint. Existing idle
   Listing prefetch may decode tail streams and prepare the first stage.
2. Selecting the entry retains valid work for that same species. A cold entry
   or internal species change prepares the base and primes only its startup
   deficit: the 96-tail-tile lead and complete first stage.
3. The Selected reveal installs the UI, palette, viewport and empty OAM through
   the existing owner transition. There is no new neighboring-species cache.
   Internal paging keeps the outgoing page frozen during RAM preparation, hides
   before shared VRAM uploads, then publishes the maps and used BG palettes in
   one VBlank. See [internal handoff](#internal-description-handoff).
4. `Pokedex_BeginDescriptionAnimation` starts the cry using the existing audio
   setup, then attempts to acquire quiet ownership.
5. It queues the first visual event for the next hardware interval. That first
   publication anchors the timeline. Later deadlines accumulate from the prior
   deadline, never from how late mainline happened to finish.

The outer loop's starting tick is preserved across species cancellation and
base preparation. Clearing it during a transition would make the end-of-loop
wait compare against an unrelated zero, including a false equality at wrap.

## One Settled Selected Iteration

```text
BeginOwnerLoop
  remember display counter; permit one finishing attempt; process normal input delay
Selected Update
  footer/input first; cancel or hand off if requested
  retire published stage; advance authored event/deadline; prepare hidden stage
  choose at most one regular useful action for this display-counter value
    ready upload prefix -> gather and upload
    otherwise dictionary below permitted target -> decode one stream
    otherwise -> no regular work
  optionally finish one complete ready remainder, if all admission gates pass
  queue a ready or genuinely due incomplete stage, without duplicate submissions
EndOwnerLoop
  service deferred sampled audio when due
  if this iteration already crossed VBlank: return without another forced wait
  otherwise: wait for VBlank
  mark audio service due for the next owner's end
```

Interrupts remain enabled in ordinary production. The timer consumes cached
audio while work proceeds. HBlank DMA uploads the graphics during safe transfer
windows; it may wait if mainline reaches its launch cutoff too late. VBlank
publishes the maps independently when their authored deadline arrives.

Mainline computation is **not restricted to HBlank/VBlank**. Decompression,
gathering and WRAM staging run during visible scanlines too. The restrictions
apply to particular hardware writes and transfers, not all CPU work.

### Regular Work Policy

`Pokedex_ChooseAnimationWork` returns decode, upload or idle. It records
`wPokedexAnimWorkTick` only for actual selected work. Upload is preferred when a
valid unready stage has a ready source prefix. Otherwise decoding can advance
toward the permitted dictionary target. The helper still enforces source availability,
hidden-slot ownership, transfer size and upload-offset bounds.

At most one regular action starts per hardware counter value. An action can
span an interval; this does not falsely record completion. The next call reads
the current display clock and the actual updated cursors.

### Resident Fast Path

Each slot retains the identity of its last fully uploaded visual frame. If the
next stage exactly matches that resident frame, its graphics already exist:
construct/queue the maps without another tile upload. Incomplete uploads must
not receive a completed resident identity. The displayed slot cannot be reused
for a different frame while still visible.

### Optional Finishing Work

`Pokedex_TryFinishAnimationStage` follows the regular action. It is a bounded
additional operation, not a loop that catches up arbitrarily. It requires:

- Quiet Selected ownership and active playback.
- No earlier admitted finish in this owner iteration.
- Valid stage, but not ready, pending, published or ended.
- A nondisplayed destination slot.
- A complete remaining upload of 1-20 tiles, all decoded.
- A deadline not already past under the modulo display-clock comparison.
- Supported hardware/timer state and adequate time/audio reserve.

On admission it marks the one-shot flag, uploads the entire remainder and
immediately attempts the map queue. The actual queue boundary rejects a pending
or already-published stage, including a publication that interrupted earlier
mainline work. This closes the duplicate-publication race at the mutation site.

## Finishing Cost Model

The game uses 80 global bytes, not per-species estimates: three rows of twenty
exclusive LY limits plus twenty minimum-audio counts. The host derives them
from executed linked instructions for each remainder size.

For a remainder of `n` tiles, let `C` be the conservative complete-chain bound
and `L` the conservative launch-prefix bound, including measured interrupt
interference. The exclusive scanline limit is the stricter of:

```text
144 - ceil((C + 8192) / 456)
127 - n - ceil(L / 456)
```

This reserves time through gather, upload launch, transfer, bookkeeping and map
queue. It also accounts for the existing HDMA helper's size-dependent launch
cutoff. Missing that cutoff can otherwise move completion into another frame.
No instruction makes HDMA intrinsically faster.

The active sampled-audio reserve is:

```text
1 + ceil((C + 2 * 70224) / 12800)
```

Require at least the smaller of that count and all remaining playback blocks.
Current thresholds require 14-17 cached blocks. The extra horizon covers the
chain and the subsequent refill opportunity; the 8,192-T finishing reserve is
additional time margin, not a persistent allocation or an injected delay.

Admission accepts the short LCD handler and measured timer classes only.
Normal-speed active playback uses the 200-count block period (`TAC=6`,
`TMA=56`); the production double-speed path checks KEY1 and its matching
ordinary timer (`TAC=7`, `TMA=156`). The physical block period and conservative
finishing reserve remain the same. Unsupported pitch/timer settings,
LCD-off use and another LCD handler reject the optional finish. Regular work
continues, and misses remain observable. Do not copy these constants to another
owner or a fainted-cry path without measuring its timer configuration.

The shared remaining/cache counters are sampled in a short interrupt-masked
section with WRAMX bank 4 selected. It restores the caller's WRAM bank and
reopens interrupts before the final LY gate. The measured longest masked span
is 160 raw T, including the delayed-EI boundary. Callers must enter with IME
enabled; this helper is not an interrupt-safe API for arbitrary callers.

After instrumentation removal, the linked twenty-tile prefix is 14,740 raw T
before the interrupt envelope; the conservative active-audio complete chain
reaches 53,516 T. Queue construction is 8,100 raw T, including ownership guards.
These raw counts and response bounds are different quantities.

The two fixed-size copy optimizations save CPU work:

- Unroll the sixteen-byte tile copy: 644 -> 392 raw T per copy body.
- Unroll seven-byte map rows while retaining all four required copies.

Regenerate/check thresholds whenever those paths, wrappers, audio ISR, LCD ISR,
queue code or instrumentation change. A passing conservative-table check proves
the compiled inequalities, not complete animation feasibility by itself.
`finish_bounds` reports recomputed and shipped rows, failing if shipped gates
are more permissive than their bounds. Diagnostic removal retains the older,
more conservative gates. The tool never silently edits the ASM. Update the constants, rebuild and rerun both
the bounds check and complete linked replays before accepting a changed table.

## Atomic Publication And Quiet Ownership

Stage construction first patches the normal 20-wide tilemap/attribute backing
maps, then copies the relevant rows into persistent 32-wide owner buffers.
VBlank transfers seven full 32-byte rows from each owner buffer with GDMA:
224 attribute bytes plus 224 tile-ID bytes. Both transfers finish before the
next visible frame. The map transfer is distinct from the changed-tile HBlank
upload into the hidden animation slot.

The queue sets `MAP_PENDING`; successful publication clears it, sets
`MAP_PUBLISHED`, records the displayed slot and updates diagnostic timing.
Mainline subsequently retires that event. Incomplete stages deliberately remain
visible on a real deadline miss; the scheduler does not stretch or hide it.

The existing `hVBlank` dispatch byte carries an explicit ownership bit:

| Value | Meaning |
| --- | --- |
| `$80` | Quiet Selected ownership; ordinary low-bit handler |
| `$87` | Quiet Selected ownership; Dex publication work queued |
| bit 7 clear | Existing ordinary ownership rules |

The dispatcher already masks the low three bits; no ninth handler is added.
Queuing and completing publication preserve bit 7. Under this tag,
`hOAMUpdate=1` retains the **already-published empty OAM**, and `VBlank_Normal`
skips four unchanged scroll/window copies. Sound, timer, joypad and other normal
VBlank processing are not disabled.

Acquisition requires no queued BG/palette/DMA/tile/map-animation/owner-transition
work and matching shadow/hardware viewport registers. The caller separately
guarantees that empty OAM was actually published. A flag alone cannot prove it.
The ordinary handler or an idle Dex handler may be selected at acquisition.
Canceling an early queued animation can leave the low handler ID at 7; that is
not a competing owner once its pending/published map flags have been cleared.
Acquisition explicitly rejects live pending/published maps before accepting it.

Quiet publication accepts `144 <= LY < 149`. Untagged publication retains
`144 <= LY < 146`. The lower bound rejects visible-time entry and physical line
153's early LY=0 readback. The linked quiet transaction has a conservative
1,436-T critical transfer bound from its LY check and at least 845 T remaining
at the latest accepted coarse entry. This is conditional on the quiet-owner
contract, not a general allowance for arbitrary VBlank transfers.

### Required Release Points

`Pokedex_CancelAnimationPrefetch` releases quiet ownership before clearing
producer state. Selected species changes, B-return and Area handoff use it.
These owner changes also cancel pending Description text before reusing the
backing buffers.

Description A-button text paging no longer releases quiet ownership. Its
bounded local job services text after animation prepare/produce/commit, then
publishes only padded lower tile-ID rows 8-14 in one admitted VBlank transfer.
The due portrait has priority; text cannot acknowledge an animation event or
rewrite portrait attributes. Both publications may occur in the same VBlank
only if their individual admission gates allow it. This specifically measured
contract replaces the old synchronous whole-screen copy and avoids stopping
the producer or permanently losing quiet mode on A. The 81-phase matched
controls retain identical animation publication signatures, with all-species
content/playback tests also clean. See the
[text ownership contract and latency measurements](pokedex_description_paging_investigation.md#implemented-transaction).

Future palette updates, scroll changes, OAM type icons or any other new display
work must release/reestablish ownership or provide a newly measured contract.

### Listing Return Is A Separate Publication Profile

The 2026-10-01 restoration correction does not alter the quiet-animation gates
or work scheduler. A Selected B-return cancels production/releases quiet
ownership, repairs only missing icon-cache rows with the LCD on, stages the
Listing and explicitly requests its BG slots 2-7 and OBJ slots 0-5.

`Pokedex_VBlankOwnerTransition` accepts only `144 <= LY < 145`. Its two complete
maps finish in VBlank. For the **Listing owner only**, palette stores use
STAT-protected Mode 0/1 windows; OAM DMA follows and finishes before the first
cursor pixels at line 34. BG slots 0/1 remain untouched and the first dependent
side-icon BG pixels are at line 40. This owner transaction can finish on visible
line 24: it is not the animation publisher and is not claimed to fit wholly
inside VBlank. Cold Description retains its unrolled dirty-palette path;
internal Description uses the separate profile below.

The late-admission stress suite retains at least 1,148 T of map headroom,
4,688 T for OBJ palettes and 3,904 T for OAM before their first-use boundaries.
These guarantees depend on the Listing layout and interrupt-disabled
transaction. Moving dependent graphics earlier requires remeasurement; do not
reuse this profile as a generic visible-time upload allowance. The correction
adds 166 ROMX bytes in bank `$77` and no RAM, ROM0 or VRAM allocations. See the
[full restoration record](pokedex_listing_restoration_investigation.md#implemented-restoration)
for baseline comparisons, cache ownership and all-species regression limits.
The current optimization cannot suppress a transfer that has become necessary.

### Internal Description Handoff

This 2026-10-01 cleanup changes initial species publication, not animation work
selection, finish admission, deadlines, startup lead or sampled-cry refill.
After canceling the outgoing owner, native internal paging retains the old
display through RAM-only text/base/footprint preparation, then masks the shared
portrait white before replacing its graphics. Alternating footprint/type tile
sets retain the outgoing icons until the new maps and palettes are published.
Selected palette staging never requests a premature generic hardware update.

The new internal owner-request value reuses the existing request byte and two
576-byte buffers. The VBlank owner dispatcher admits at `144 <= LY < 145`, then
publishes both maps and only BG palettes 0/1/2/6/7 (40 bytes). No Selected OBJ
content is visible, so this profile skips OBJ palettes/OAM DMA. Bank restore,
request/dirty clearing and success carry precede incoming playback. Mainline
honors that carry and omits the old general copier/separate reveal wait.

The linked owner body takes 3,924 T to its success marker and returns with
252 T before physical line 0 in the tested settled/active traces. That is not
a whole-interrupt completion guarantee. Map/palette publication itself is
entirely in VBlank; Listing's distinct visible-time profile is unchanged.
The original handoff added 176 ROMX bytes and no other resource allocations.
The accepted buffered-icon follow-up adds another 228 ROMX bytes and 12 BG tiles,
reusing one existing scratch byte without allocating RAM or HRAM. Neither change
borrows an animation slot. Exact timing comparisons, all-species regressions,
icon lifetimes and visibility limits are in the
[handoff implementation record](pokedex_internal_transition_investigation.md#buffered-icons-in-production).

## Pacing And Audio

`Pokedex_BeginOwnerLoop` records the hardware counter before input and clears the
per-iteration finishing flag. `Pokedex_EndOwnerLoop` moves the outer sampled-cry
service behind useful animation work while retaining its deferred obligation.
If work already crossed VBlank, it does not blindly add a second display wait.
Otherwise it performs the normal HALT-until-VBlank pattern.

The wait flag is armed before the loop-end clock comparison, so a VBlank that
interrupts that comparison cannot have its acknowledgment overwritten by a
subsequent wait-arm store. It still uses the existing interrupt-driven HALT
pattern rather than spinning until the next frame.

Nested `DelayFrame` calls retain their existing audio service. Nonquiet Dex
states fall through to the original delay behavior. Other owners do not use
this pacing policy. This is not a new global audio-prefetch system and does not
change the decoder, 32-block prefill or eight-block refill quota.

Accepted species-change, B-return and Area-entry boundaries now call the
Dex-local `PokedexSelectedMon_CancelCry` before synchronous staging or incoming
cry lookup. It stops an active sampled timer first, then clears only active
synthesized-cry channels and restores their volume/priority bookkeeping. This
closes outgoing cache exhaustion, synth resumption and the incoming-header race
without changing scheduling, prefill or refill. A-description text toggles keep
the same audio owner and do not call the helper. It adds 127 bytes in the
existing Dex ROMX bank, with no dedicated memory or ROM0 allocation. See the
[ownership contract and regression results](pokedex_cry_ownership_investigation.md)
for interrupt requirements, all-species coverage and timing comparisons.

## Memory And Bank Contracts

### Persistent State

The existing 26-byte block beginning at `wPokedexAnimOwner` retains owner,
flags, slot identities, deadline, counters and dictionary/timeline pointers.
The retired two-byte miss count remains reserved to preserve the pointer
layout. Three production bytes follow the name buffer, outside the cleared
owner extent:

| Current address | Field | Lifetime |
| --- | --- | --- |
| `$c758` | `wPokedexAnimLoopTick` | Beginning to end of one outer iteration; preserve during cancellation |
| `$c759` | `wPokedexAnimWorkTick` | Last regular work-start counter; initialized before playback |
| `$c75a` | `wPokedexAnimSchedulerControl` | Deferred audio bit 0; finish-used bit 1 |

These production bytes remain after removal of the diagnostic block. Bit 7 of
`wPokedexAnimFlags` now marks the first publication: queueing sets it, actual
publication anchors the first deadline and clears it. No later event is
re-anchored. The diagnostic publication count is no longer consulted. No new
WRAM0/WRAMX/HRAM/VRAM/SRAM is allocated; `wBattleEnd` and other union ownership
boundaries are unchanged. `hVBlank` uses one existing bit, not HRAM padding.

### Workspace

`wPokedexWRAM0Scratch` is the existing 1,300-byte overworld-map union at `$c800`.
It is safe only for this Start-menu owner; returning to the map reconstructs
the overlapped overworld data. Key offsets:

| Offset | Use | Bytes |
| --- | --- | ---: |
| `$000` | One upload payload | 320 maximum |
| `$310` | Copied frame-plan pairs | 98 maximum |
| `$39c` | Slot A packed tilemap and attributes | 98 |
| `$3fe` | Slot B packed tilemap and attributes | 98 |
| `$460` | Ordered source IDs for current stage | 49 |
| `$4d0` | Active-order seen bitset | 47 currently |

Selection base/footprint staging and Listing row staging overlap these views.
They must cancel/release the producer before overwriting them. The seen mask is
outside those transient regions. Bank 6 contains the decoded dictionary; bank 3
contains persistent owner maps at `$d000` and `$d240`; bank 4 owns sampled audio.

VRAM bank 0 keeps the 49-tile static base at `$9000`. Bank 1 keeps slot A at
`$8800-$8b0f` and slot B at `$9330-$963f`. They map to signed tile IDs
`$80-$b0` and `$33-$63` with the bank attribute set. Neither the font nor the
Listing's 80 side-icon tiles is borrowed by this implementation.

### Calling Discipline

- `farcall` installs its target in HL. Never pass an input pointer in HL across
  it unless using the specifically supported wrapper/return convention.
- Preserve caller-selected `rSVBK`/`rVBK` around service-local bank changes.
  The timed replay compares register/bank behavior against SameBoy.
- WRAM union bytes are not globally trustworthy ownership flags. The VBlank
  fast path first checks the explicit dispatch tag instead.
- The sampled audio snapshot is mainline-only with IME enabled.
- Generated data readers execute in their required ROM banks. Retain their
  bank/address contracts when moving metadata.
- Pending owner buffers must stay stable until VBlank acknowledges publication.
- Slot residency is valid only after its entire upload completes.
- The eight-bit deadline comparison assumes each hold is below 128 intervals;
  it is not a general long-duration clock or recovery mechanism for 256-frame stalls.

## Final Linked Resource Bill

The scheduler-integration delta below compares the 2026-09-20 integration with
its frozen pre-change ROM, with instrumentation retained. It is a dated change
bill, not an automatic measurement of every later checkout. The subsequent
Seviper script correction adds 13 timeline bytes in bank `$a5`; the current
metadata table below includes that increase. Encounter cleanup changes contents,
not allocation, and removal of dormant A/B branches is binary-identical.

| Bank/resource | Occupied-byte change | Free after change |
| --- | ---: | ---: |
| ROM0 `$00` | +6 | 656 total; 580 at Home tail |
| ROMX `$10` | 0 | 0 |
| ROMX `$14` | -3 | 1,648 |
| ROMX `$34` | -58 | 2,548 |
| ROMX `$77` | +57 | 2,963 |
| ROMX `$a0` | +597 | 2,979 |
| ROMX `$a6` | -5,550 | 16,384 |
| **ROMX total** | **-4,957** | |
| **All ROM combined** | **-4,951** | |

The 4 MiB file stays 4 MiB. Occupied space decreases; no new ROMX bank is needed.
Bank `$10` fits through six equivalent terminal CALL/RET-to-JP substitutions,
offsetting the outer wrappers' farcall bytes. `$a6` is now wholly reusable, but
only its formerly occupied 5,550 bytes count as newly recovered data/code.

Retained optimization metadata in the accepted 2026-09-21 ROM:

| Data | Bytes including pointers |
| --- | ---: |
| Frame plans | 48,383 |
| Exact timelines and high-water hints | 13,510 |
| Global finishing tables | 80 |
| **Total** | **61,973** |

These are metadata totals, not all animation code or graphics. The global
sampled-cry pair lookup remains useful independently. Original animation scripts
remain necessary for other owners and generation. Dormant A/B source branches
have been removed; host-analysis files do not consume cartridge space. The
97-byte timeline reader shares bank `$a5`, which now has 2,777 bytes free.

The normal global VBlank path gains a 28-T tag check (about 6.68 microseconds).
Quiet Selected takes 32 T there and avoids 96 T of unchanged viewport stores,
plus its redundant OAM transfer. It would be inaccurate to call the global
change instruction-for-instruction free for the Listing or other owners.

## Adapting The Design To Another Owner

Do not start by copying the Dex loop and its LY table. Start with the owner's
real display/interrupt workload and memory lifetime.

1. Specify which tiles, OAM, palettes, maps and viewport registers that owner
   needs throughout playback, and which can remain unchanged.
2. Choose resident dictionary or streaming slots based on that owner's VRAM
   allocation. The Dex's slot geometry is not a prerequisite for timelines.
3. Assign persistent state and scratch whose lifetime is actually valid there.
   Party Stats cannot assume it owns the Dex's overworld union or bank-3 maps.
4. Reuse frame-plan/timeline generation where its formats fit. Keep authored
   deadlines on the hardware clock and progress on independent cursors.
5. Define a prepare/queue/publish acknowledgment protocol. Never overwrite the
   displayed slot or an interrupt-owned pending buffer.
6. Measure that owner's useful-work path, interrupt interference, transfer
   launch limits and publication window. Regenerate its admission constants.
7. Position audio service where it supplies sufficient runway without delaying
   time-critical launches. Keep visible misses and diagnostic counters during testing.
8. Test actual linked execution, sampled and synth audio, cold entry, repeat
   frames, short deadlines, cancellation, paging, and exit restoration.

Stats may need a different publication window, visible OAM or per-page palette
updates. That can justify a bespoke owner wrapper while retaining the same
principles, metadata and host tooling. There is no requirement to create one
universal interrupt path or to make every owner use the Dex's buffers.

## Maintenance Checklist

- Change one documented ownership/cost assumption at a time and keep a replayable
  reference ROM/symbol pair.
- Build assets and check all structural invariants.
- Recompute the 80-byte finishing table from the new link; fail on a mismatch.
- Run linked contracts, full replay, audio-phase controls and independent core comparison.
- Recheck both map contents and interval timing, not only the absence of an underrun count.
- Recheck input/exit paths in the emulator; relocated replay is not startup proof.
- Update this document, validation identities/results and the outstanding bug list.
- When removing instrumentation, retain production state and regenerate costs
  before claiming the new link inherits these timing results.
