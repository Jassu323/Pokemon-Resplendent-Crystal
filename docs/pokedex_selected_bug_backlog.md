# Pokedex Selected-Mon Bug Backlog

Updated 2026-10-03. This is the live issue/status list, not the chronological
scheduler investigation. Settled Selected animation/audio and New Dex Entry
acceptance have passed, including instrumentation cleanup. Description UI,
footprint styling and New Dex boundary wrapping are also accepted. The separate
Listing return palette/cache fixes now pass their reproduction and regression
suites, and grid metadata now uses presence flags instead of retained transient
IDs. Mew's incomplete category and Drapion's category overflow are also corrected
with focused headless regressions passed. The remaining historical UI,
secondary-screen and adjacent-owner items below remain deferred. Internal paging's delayed
portrait masking, buffered icons and atomic reveal are implemented, with
automated regression and the user's manual visual review passed.
The shared-menu fresh-direction correction is now accepted for production;
overworld turning-delay changes remain a separate research spike.
The bounded A-button Description transaction is also manually accepted and
committed as `9f89227efd33a56e064fc010a9ebb4c7d0666d7f` (Description Paging Bug
Fix). Its automated timing/content regressions remain the recorded evidence;
the user's confirmation closes `DEX-DESC-01` without closing Area or older
Listing/exit presentation reports.

Remaining Dex review queue:

- `DEX-INFO-01` is solved by the integrated
  [committed-record return fix](pokedex_info_return_records_preflight.md).
  It preserves outgoing pixels with about 50ms common return overhead and
  two extra intervals of Info preparation, accepted for now and retained as
  measured baselines for `DEX-PERF-02`. `DEX-INFO-04` is a separately confirmed early-cancellation
  Description badge defect; revalidate it after the shared-indicator promotion
  before closing its historical report. Missing evolution
  data (`DEX-INFO-02`) is deferred into the broader `DEX-DATA-02` species pass.
  Shared pagination is integrated under `DEX-PAGE-01`. `DEX-INFO-03`,
  delayed tab changes during frontpic playback, remains uninvestigated.
- `DEX-INFO-05` records a phase-dependent physical display-interval loss during
  Info-owned Dusclops-to-Dusknoir paging. Its timer-shutdown interrupt race is
  corrected in production with the accepted Moves implementation. The exact
  failing phase and all 746 Info cases pass physical-clock audits; the user
  also reports no visual/audio/data errors or miss breakpoints in manual review.
- `DEX-PERF-01` is a deferred optimization story for opening and closing the
  Dex. It includes the confirmed `DEX-EXIT-01` shell shift, now merged into
  that broader lifecycle work rather than scheduled as a standalone fix.
- `DEX-PERF-02` defers broader Dex profiling/optimization until Moves, Area
  and the remaining Dex modes have been implemented.
- Historical reports `DEX-RETURN-02` (vertical displacement), `DEX-RETURN-04`
  (placeholder Listing state) and `DEX-GRID-02` (caught-ball OBJ palette) do not
  reproduce in the current 448-return/746-viewport revalidation. Keep their
  individual historical reports pending manual revalidation rather than
  inventing another fix. See the [full revalidation](pokedex_backlog_revalidation.md).
- `DEX-GRID-04` records a separate blocked BG palette write during Listing
  follow-up navigation in both matched pre/post-egg prototypes. Visible content
  remains correct in those sampled checks; investigate without conflating it
  with return restoration or the timer-shutdown correction.
- Keep `DEX-AREA-01` separate: its Area setup stall is reproduced, while the
  older transition-corruption report still needs presentation revalidation.
- `DEX-SEARCH-01` remains a deferred Search palette report; recheck it before
  changing that screen. `DEX-DATA-01` is content completion, not scheduling.

Keep each transaction fix independently scoped and tested. A passing animation
counter does not close a palette, text, input or cancellation bug. Earlier
measurements and superseded diagnoses are retained in the
[backlog investigation history](archived/dex-scheduler/dex_backlog_investigation_history.md)
and [scheduler archive](archived/dex-scheduler/README.md).

## Current: Animation Timing

### DEX-ANIM-01: Work scheduling falls behind authored publication deadlines

Status: Solved for uninterrupted cold entry and settled internal paging; cleanup/UI regressions passed

The current scheduler uses the hardware display clock with independent work
completion, bounded finishing, quiet publication ownership and owner-local
audio/wait sequencing. Later timeline events permit bounded decoding to the
dictionary's end, correcting the Groudon lookahead misses without increasing
startup or allocating more RAM/VRAM.

The recorded target-correction matrix passes 126 replays across 18 species.
The subsequent normal-input cold suite checks all 373 New Dex species, every
published portrait and exact full authored timing with no animation/audio misses.
The user's complete internal-paging pass and representative visual controls also
pass. Drapion's initial static portrait defect was the separate text overflow
`DEX-UI-02`, not an animated-frame failure; its category-data correction below
now passes the initial reveal check too.

Instrumentation cleanup and the 2026-09-30 Description UI change each retained
exact authored timing with no animation/audio misses across all 373 species on
both cold entry and settled internal paging. See the
[cleanup results](dex_instrumentation_cleanup.md) and
[UI results](pokedex_description_ui.md#current-results).

Warm entry, rapid cancellation, active-animation Description text toggles and
all owner/exit transactions are not signed off by these settled-playback tests
alone. The separate `DEX-DESC-01` active-input regression and manual acceptance
now sign off the bounded text transaction; older Listing/exit reports retain
their individual status below.
Revalidate if warming is removed or production timing changes. See the
[implementation](pokedex_animation_scheduler.md), [acceptance/test guide](dex_scheduler_validation.md)
and [cold results](dex_cold_listing_results.md). Historical failures, hypotheses
and progression remain in the archive rather than being repeated as current
open scheduler diagnoses.

### DEX-ANIM-02: Seviper's authored main animation repeats indefinitely

Status: Solved; manual cold/internal and automated cold retests passed

The 2026-09-20 all-asset audit found Seviper is the only generated timeline with
a persistent loop marker. In `gfx/pokemon/seviper/anim.asm`, `dorepeat 6` jumps
to zero-based command 6, `setrepeat 2`, resetting the repeat counter on every
trip. The original animation interpreter uses that same command-index meaning.

The original generator output contained 49 introductory intervals followed by a
13-interval frame-4/frame-5 loop. Main `endanim`, base hold and idle script were
unreachable with that script. This is a separate authored-script issue, not
evidence that the new scheduler missed a deadline.

The user confirmed the Selected Mon animation continued for over a minute
without stopping. The approved correction changes only `dorepeat 6` to
`dorepeat 7`, targeting `frame 4` instead of the counter reset. The existing
two-pass limit now applies, making the main end, base hold and idle script
reachable. The rebuilt timeline contains 21 events totaling 122 display
intervals and ends without a loop. All 399 linked timelines pass structural
validation and all 11 scheduler contract tests pass; no scheduler, cry or
memory-allocation change was needed. The user confirms both cold entry and
internal paging now finish. The normal-input core suite also verifies all 122
intervals and the final base restoration without animation or audio misses.
See the [completed Seviper investigation](archived/dex-scheduler/dex_seviper_new_entry_testing.md#seviper-verify-the-repeat-target-fix)
and [current acceptance](dex_scheduler_validation.md#acceptance-and-limits).

## Current: Cry Integration

### DEX-CRY-01: Dusknoir's sampled cry underruns on the Selected page

Status: Solved for uninterrupted cold entry and settled internal paging

The integrated scheduler retains the 32-block prefill and eight-block refill.
The target-correction matrix records 112 natural sampled completions across
16 species and seven timer phases. The normal-input cold suite subsequently
completed all 122 sampled cries naturally with zero cache-empty hits; the full
manual internal-paging pass also had no uninterrupted-playback misses.

The earlier partial improvements and failed cache measurements are preserved
in the [historical entry](archived/dex-scheduler/dex_backlog_investigation_history.md#dex-cry-01-dusknoirs-sampled-cry-underruns-on-the-selected-page).
They describe older builds, not remaining settled-playback failures in this
checkpoint. This acceptance does not close `DEX-CRY-02`, `DEX-CRY-03` or
transition-only `DEX-CRY-04`. Post-instrumentation-cleanup and Description UI
regressions pass for all 122 sampled cries on both settled entry paths. Warm
entry and rapid cancellation remain separate, unaccepted cases.

### DEX-CRY-02: A synthesized cry resumes after sampled playback ends

Status: Solved 2026-10-01 for Selected Mon owner changes

In the baseline, when internally paging from Mewtwo to Dusknoir, Mewtwo's
synthesized cry was paused rather than canceled when Dusknoir's sampled cry
took ownership. The
2026-10-01 headless traces reproduce resumption even after Dusknoir finishes
naturally: an underrun is not required. Channels 5/6/8 retain active cry flags
and frozen script state, then resume when sampled playback releases the sound
engine. Early B-return can also leave the outgoing synth playing on the Listing.
All-seen Celebi-to-Treecko controls reproduce the same failure without modifying
the visible paging neighbors.

Implemented `PokedexSelectedMon_CancelCry` at accepted species-change,
B-return and Area-entry boundaries, before staging or incoming lookup. It
clears only active cry channels and restores their volume/priority bookkeeping;
music and the decoder are unchanged. The integrated helper passes 78 focused
cases and 1,492 active all-species handoffs, plus full 373-species cold/paging
animation/audio regressions. This also closes `DEX-CRY-04` and the related
metadata race `DEX-CRY-05` for this owner. See the
[cry ownership investigation](pokedex_cry_ownership_investigation.md).

### DEX-CRY-03: Dusknoir also underruns on the party Stats Screen

Status: Confirmed adjacent issue

After Dusknoir's Stats Screen cry stopped, `hSampledCryTimer` and the decoded
cache count were both zero while 78 compressed blocks remained. This proves
that the failure is not exclusive to the new Pokedex animation producer. The
Dex still has its own concurrent-workload pressure, but any eventual audio
solution should account for this shared failure mode rather than assuming the
Selected-Mon controller is its sole cause.

### DEX-CRY-04: Outgoing sampled cry can exhaust during species preparation

Status: Solved 2026-10-01 for Selected Mon owner changes

Reproduction on the 2026-09-20 scheduler build: start on Weavile, let playback
finish, then hold Up. Garchomp becomes visible and starts its animation/cry.
Continuing to hold Up selects Bastiodon; `$00:$3cb3` triggers during the black
transition, before Bastiodon's reveal. After continuing and releasing the pad,
Bastiodon's cry finishes normally without another hit. The user reports no
noticeable unwanted outgoing audio during the transition.

The captured state establishes which cry and path are involved:

- `hSampledCryBank=$9f` and compressed cursor `$478a` identify Garchomp's sample
  (`$9f:$4622-$50e3`); Bastiodon's sample is in bank `$92`.
- `wSampledCryCacheCount=0`, while both remaining playback and compressed counts
  are `$010a` (266 blocks). `hSampledCryTimer=1` is still active at the breakpoint.
- `wPokedexSelectedState=$02` is `DEXSELECT_STATE_SWITCHING_SPECIES`, and
  `wPokedexAnimPlaybackState=0`; the incoming animation has not begun playback.
- The interrupted mainline is `PokedexSelectedMon_ChangeSpecies` ->
  `PokedexSelectedMon_StageDescription` -> `Pokedex_PrimeDescriptionAnimation` ->
  `Pokedex_ServiceAnimationProducer` -> dictionary chunk -> `FarDecompress`.

The baseline species-change path canceled animation production but did not
explicitly cancel outgoing audio before synchronous preparation. The timer
could continue consuming Garchomp's cache while Bastiodon's startup work ran.
This is a real
cache-empty stop, not the normal cancellation branch, but it is not an underrun
of Bastiodon's subsequently started cry or of settled playback.

Implemented: stop outgoing sampled and synthesized cries together at the
accepted owner boundary before preparing the next entry or restoring the
Listing. The integrated all-species active handoff and B-return regressions
have no empty-cache hits. Startup prefill, refill quota and the settled
animation scheduler are unchanged.

2026-10-01 Listing-restoration investigation: four normal-input early B-cancel
cases (Dusknoir/Weavile at offsets 0/4) also exhaust the outgoing sampled cache
while the Listing is prepared. This extended the same cancellation
scope to B-return. It does not invalidate settled Selected playback or establish
an incoming cry failure. See the
[restoration investigation](pokedex_listing_restoration_investigation.md#unreproduced-and-adjacent-findings).

The dedicated 2026-10-01 ownership investigation reproduces ten outgoing
cache-empty cases in a 40-case baseline, including both species preparation
and B-return. The incoming sampled cries finish naturally except for the
separate header race below. Stopping the outgoing cry before synchronous work
eliminates these cases in the integrated Dex-local helper without changing
prefill, refill or animation timing. See the
[current cause and fix costs](pokedex_cry_ownership_investigation.md).

### DEX-CRY-05: Replacing an active sample can corrupt the incoming header

Status: Solved 2026-10-01 for Selected Mon owner changes

Active Metagross-to-Luxray paging can overwrite shared
`hSampledCryBank/address` with Luxray metadata before the old Metagross timer
stops. The timer then advances Luxray's header pointer from `$53a0` to `$53b0`.
Startup captures that wrong pointer before its existing cancellation runs,
reading 53,662 blocks from audio payload instead of Luxray's correct 508. The
bounded headless test does not finish. This is a metadata ownership race, not
insufficient decode throughput.

The same early owner cancellation implemented for `DEX-CRY-02/04` prevents this
race in the Dex and passes focused and all-species header/block-count audits.
A future shared-loader
audit should make its no-active-sample requirement explicit; this investigation
does not establish that other screens reproduce the race. See the
[instruction-level trace](pokedex_cry_ownership_investigation.md#incoming-header-race).

## Info Pages

### DEX-INFO-01: B-return from Stats corrupts the lower Listing graphics

Status: Solved 2026-10-03; committed-record return preservation accepted and integrated

Reproduction: cold-select caught Chikorita, open Info once and press B without
another A. The lower labels/bars acquire minisprite pixels before the correct
Listing appears. Settled playback is enough. Chikorita P.2 is a clean control;
Tyrogue P.3 and Stats after Chikorita -> Bayleef -> Meganium also reproduce.

Cause: atlas B borrows bank-1 Listing frame-0 cells. Cache repair uploads into
them before removing the outgoing Info BG references. Hiding the Window does
not hide this BG panel. This is not a rejected palette-write deadline.
Twenty-one of 33 focused returns corrupt for 11-12 display frames; all 33 final
Listings, used palettes, cache bytes, scrolling and re-entry checks pass.

The user selected preserving the outgoing panel by relocating its actual
Info-B tiles to unaliased Info-A storage, then acknowledging an identical-pixel
map publication before the unchanged full-cache Listing repair. A separate
private ROM passes 96 paired returns and 150 pending-job cancellation pairs,
with no exposed tile replacement or lower-panel blanking. Linked cost is
280 ROMX bytes, no new ROM0/RAM/VRAM. It adds approximately 50ms on unaliased
Info returns and 151ms when relocation is required; production is untouched
pending review. The user rejected this readback latency. Its
[committed-record successor](pokedex_info_return_records_preflight.md) passes
the same suites plus 100 additional cancellation cases. Common atlas-B
returns add about 50ms/three intervals; atlas-A returns are effectively
unchanged. Cost is 364 ROMX bytes and 611 reused Tower-overlay bytes, with
zero physical WRAM growth or premium/VRAM additions. Info preparation itself
adds about two intervals. The user accepted these costs and requested
production integration, deferring further performance work until the other
Dex components are situated. The production ROM, SYM and MAP reproduce the
accepted prototype byte-for-byte. The retained-screen transaction remains
separate from `DEX-INFO-04`; acceptance does not close that badge defect.
See [historical readback results](pokedex_info_return_preflight.md).
The test probe's extra A was corrected, and the oracle checks outgoing display
frames rather than just the final Listing.
See [full reproduction, trace, alternatives and costs](pokedex_info_return_evolution_investigation.md#confirmed-b-return-corruption).

### DEX-INFO-04: Early Info cancellation can erase Description's P. badge

Status: Confirmed in production and private return preflight 2026-10-03; not fixed

Reproduction: cold-select caught Rhyperior, immediately select Info with
Right/A, then Left/A back to Description before Info finishes preparation.
The phase-0 automated replay reproduces; phases 8, 32 and settled do not.
The lower `P.` badge remains blank while the description and digit display
correctly. Playback completes without animation/audio misses. This is not a
Listing return defect and occurs before the new return helper executes.

Cause: Info's incremental row clear replaces row 9 column 1 with blank `$32`;
its badge renderer restores `$77` only after all rows are cleared. The caught
Description-restoration path and text initializer assume this cell survives,
updating the page digit but not explicitly restoring `P.`. The failure differs
from the expected Description map at that one cell only.

Recommended direction: stage the complete Description badge on restoration,
then sweep cancellation before/during every Info preparation phase. A small
ROMX-only change is expected, but not yet implemented or linked-costed. No new
ROM0, WRAM0 or HRAM is expected. Include caught/uncaught, both atlas buffers,
active playback and internally paged owners. Retain the current failing test;
do not suppress its badge check. See [preflight evidence](pokedex_info_return_preflight.md#existing-badge-failure).

### DEX-INFO-02: Added-species evolution pages and added branches are missing

Status: Confirmed; deferred 2026-10-03 into DEX-DATA-02, not solved

The user will address evolution/family records while revising species learnsets,
base stats and other species data. Do not add gameplay evolution links or
Dex-only substitutes as part of the current return/pagination work. Retain the
existing approved Skitty link. See [DEX-DATA-02](#dex-data-02-complete-species-data-during-the-planned-species-revision).

Reproduction: on caught post-Gen-2 species with future evolutions, open Info's
Stats page and press A again. The user reports that it never advances to the
evolution pages, while vanilla evolution families generally work. This also
affects vanilla roots with added evolutions: Eevee is missing Leafeon and
Glaceon. Include Skitty/Delcatty and representative added multi-stage families,
and regression-test every existing vanilla family as well.

Independent linked-data decoding across all 373 species finds no generator,
indexing or visibility mismatch. Current Info lists correctly match the
gameplay graph, which has only 123 direct edges. Skitty is the only added
species with an evolution record; Eevee stops after its five vanilla targets.
The separate first-stage family table names 67 members unreachable from their
root, including Leafeon/Glaceon. Delcatty's lowest-stage entry also still needs
normalizing to match the approved Skitty link. A fresh 373-species headless
pass preserves current content and exact playback; this does not certify
family completeness against missing input data.

Recommend filling the real gameplay evolution tables and regenerating Info,
not a Dex-only override. Ordinary records are four ROMX bytes each (five for
stat comparisons), plus generated display records/glyphs; no premium RAM
growth is expected for data-only changes. Approve requirements for absent
items or unsupported special methods before adding them to the game.

Eevee's seven intended targets will require five Info pages once its data is
completed. Pagination is independent renderer work under `DEX-PAGE-01`, not
deferred with these source records. See [full data audit and fix choices](pokedex_info_return_evolution_investigation.md#confirmed-missing-evolution-content).

### DEX-INFO-03: Switching lower tabs waits for frontpic animation completion

Status: User-reported 2026-10-03; investigation pending

Reproduction: leave Info's Stats page selected, internally page to another
Pokemon, then select Desc while that incoming frontpic is still animating.
The user observes that the lower tab does not change until the animation ends.

Investigate when the input request is accepted, when Description preparation
receives budget, and when its completed panel publishes. Separate dropped
input from an accepted but starved job. Compare both tab directions, active
and settled playback, and sampled/synthesized cries. Any fix must keep exact
portrait deadlines and avoid sampled-cache exhaustion while making progress
on the requested tab; the cause and acceptable latency are not yet measured.

### DEX-INFO-05: Info-Owned Paging Can Lose One Physical Animation Interval

Status: Solved and integrated 2026-10-03; private automated and manual review
passed, followed by production regression

The egg-inheritance regression passes 745 of 746 Info cases. The remaining
case is settled Dusclops followed by an internal Down page to Dusknoir with
Info owning the lower panel. All portrait maps/pixels and all 35 publications
are correct, and the sampled cry finishes all 557 blocks naturally. Neither
animation-miss nor sampled-cache-empty breakpoints fires. However, the host's
physical-cycle audit finds an extra display interval from publication 29 onward.

The authored sequence is 174 intervals; the game clock also reports 174.
Physical elapsed time instead rounds to 175. Publication 1 is at tick 184,
publication 29 is at tick 31 (103 elapsed byte-counter intervals) but 104
physical intervals, and the final publication is at tick 102, about 175
physical intervals after the first. This is distinct from incomplete work
detected by an animation miss. The confirmed cause is a shared audio interrupt
race, not insufficient decoder or transfer budget.

Automated reproduction: use all-caught New Dex Listing checkpoints, cold-enter
Dusclops, settle its animation/cry, select Info, cycle its one-page Stats panel
and settle, then page Down to Dusknoir while retaining Info. The failing
starting phase is preserved in the private prototype's
`candidate/build/info-egg-regression/listing-states/` checkpoints and its
`dusclops-settled.json` trace. An ordinary fresh-checkpoint control on the
earlier cartridge passes, so reproducing the starting hardware/input phase
matters; a single manual attempt is not sufficient to dismiss this report.

The matched egg-inheritance before/after control loads the exact same Listing
checkpoint into both private cartridges. Their code, symbols and memory layout are identical;
the only ROM differences are the 112 family egg descriptors and checksum.
Both produce the same seven `hardware_interval_event_29` through `_35`
findings, identical readiness and identical playback measurements. Thus the
egg-index change does not introduce this issue. Evidence is under ignored
`build/dex-moves-prototype/candidate/build/info-egg-matched-before/` and
`info-egg-matched-after/`; preserve the checkpoint phase during investigation.

Instruction-level SameBoy observation identifies the lost request at natural
sample completion. `SampledCry_ClearTimerFlag` begins its IF read at T=18,224,236;
LY becomes 144 and VBlank raises IF from $f2 to $f3 before the routine writes
its stale $f2 back at T=18,224,268. The timer ISR returns normally, but the
VBlank handler never runs for that interval. Its byte counter is therefore one
interval behind physical time. No amount of extra portrait work can recover
an interrupt request which was erased.

The integrated correction routes both timer-ISR shutdown branches
(natural completion and actual cache exhaustion) to
`StopSampledCryAsync_FromTimer`. That path disables sampled playback/timer,
then joins the existing saved timer/audio restoration without touching IF.
The IRQ already acknowledged its timer request; a second clear is redundant.
Manual cancellation retains the existing flag-clear path. This does not
redesign the scheduler, change authored durations, or weaken either miss or
physical-clock auditing. It also does not claim to make every other IF
read/modify/write elsewhere in the game atomic.

Cost: 14 additional ROM0 bytes in the existing $0063 gap, leaving 554 ROM0
bytes free overall; zero additional ROMX, WRAM0, WRAMX, HRAM, SRAM or VRAM.
The timer shutdown path is 56 T-cycles shorter. No extra transition wait is
introduced. Two explicit entry paths avoid a new flags/register protocol or
stored mode byte. Both paths share restoration, so restored audio/timer
state remains identical.

The same failing checkpoint now publishes all 35 Dusknoir frames in exactly
174 physical intervals and naturally consumes all 557 blocks. All 746 fresh
Info cases pass, including early/settled playback and retained-Info internal
paging; all 2,576 Moves pages and 1,323 rapid-input/tab-cancellation cases also
pass. Four linked shutdown tests cover all pending-interrupt bit combinations,
unchanged manual clearing, identical saved-state restoration, and both IRQ
branch targets. Host observers recognize both shutdown entry points.
The same-phase Moves comparison also replays all 373 species on both timer
implementations: first-page readiness is identical to the T-cycle, so the
correction does not add a page-opening wait. Description passes all 1,492
cases; cry ownership passes 40 targeted cases, 14 navigation controls and
1,492 all-species handoffs. The generated-context New Dex Entry sweep passes
8,594 input-timing cases across 20 species. Sample lookup equivalence remains
byte-exact across all 122 assets. Listing restoration passes all 96 cases;
its separate three follow-up legality warnings remain under `DEX-GRID-04`.
The user manually tested every prototype review entry and found no visual,
audio or data errors and neither miss breakpoint fired. The clean production
build is byte-identical to that accepted ROM and its symbols. Production
regression repeats the all-species/tab/cancellation/entry suites, with the same
known Listing follow-up and legacy-model warnings, not new failures.
See [the production implementation and validation](pokedex_moves.md); private
matched-phase evidence is retained in its historical prototype directory.
The live save remains unchanged.

### DEX-PAGE-01: Shared Buffered Page Indicators For Lower Tabs

Status: Implemented and manually accepted 2026-10-03; integrated with Moves

Description, Info and Moves share bounded inactive-buffer preparation and
deadline-controlled lower-panel publication. Digit pairs are `$73/$78` and
`$79/$7a`; `$7b/$7c` is the permanent double-digit closing pair, `$7d` the
battle-level glyph. Both editable source sheets remain authoritative. Pages
1-19 are supported; over-limit data stops the build rather than wrapping or
truncating. The Info compiler's four-page guard is replaced by the 19-page guard.

Linked tests check every page and both buffer parities. All-species Moves,
Info and Description sweeps cover real content, page 9/10 transitions, wrap,
canceled preparations, cross-tab/species paging and B-return. No evolution
records were invented to create test pages. The user's manual review passes.
This closes renderer pagination only, not the deferred species-content pass
or the separate historical early-cancellation badge revalidation.
See [shared page indicators and resource accounting](pokedex_moves.md#shared-page-indicators).

## Description Paging

### DEX-DESC-01: Toggling description pages can corrupt the upper screen

Status: Solved 2026-10-02; automated regression and manual confirmation passed

Pressing A to switch an entry's Description text pages was observed corrupting
the frontpic, header and other upper tile rows. This is a separate transaction
from uninterrupted animation playback, which does not exercise A-page toggles.

The old explanation relied on the portrait publisher lacking an `rLY >= 144`
check. That explanation is no longer valid: the current
`Pokedex_VBlankAnimationFrontpicMap` in [pokedex_3.asm](../engine/pokedex/pokedex_3.asm)
checks `LY_VBLANK` as a lower bound before applying its upper cutoff. The
[superseded diagnostic](archived/dex-scheduler/dex_backlog_investigation_history.md#dex-desc-01-toggling-description-pages-can-corrupt-the-upper-screen)
is retained only as historical evidence.

The 2026-10-02 headless investigation reproduces animation misses in 24 of 81
A-page phase tests; 18 matched uninterrupted controls are clean. The old toggle
permanently released the quiet animation owner, synchronously redrew unchanged
header fields and both text pages for a page-2 request, then copies the whole
backing map/attributes through `CopyTilemapAtOnce`. That copy bypasses portrait
publication ownership and exposes transient mixed portraits. Interrupted
production and the slower later owner loop also cause delayed animation-miss
fallback corruption.

No current header/type/footprint pixel corruption was reproduced in the
detailed replays, so that part of the historical report remains unconfirmed.
The same full copy masks timer service for long enough to interrupt sampled
block timing, despite no cache-empty hits. Retaining quiet ownership alone is
insufficient; retaining it and omitting the copy still leaves two of sixteen
cases failing from synchronous redraw work.

The implemented Selected-local text job preserves the animation owner,
prepares only the requested text page in bounded slices, and atomically
publishes the lower text/badge/divider tile IDs. It does not rewrite portrait,
upper data, icons, attributes or palettes. Repeated A coalesces the desired
page; B/species/Area changes cancel the job before changing owners.

The rebuilt production ROM passes 153 unit/contract checks, the 81-case phase
sweep, 746 all-species active/completed A cases, 1,492 UI checks and both
373-species cold/internal playback suites. Matched uninterrupted controls
have identical portrait publication signatures. Neither animation nor active
sampled-cache-empty misses occur. All 90 non-Area repeated-input/handoff cases
pass; existing Area setup stalls remain separately deferred under
`DEX-AREA-01`. Text-only publication sometimes waits behind animation work:
median about 2.6 display intervals and worst observed about 8 (132 ms).
See the [implemented contract, costs and results](pokedex_description_paging_investigation.md#implemented-transaction).
The user confirms the fix checks out and has committed/pushed it as
`9f89227efd33a56e064fc010a9ebb4c7d0666d7f`. No new Description behavior concern
was reported in that manual acceptance.

## Selected-Mon Internal Paging

### DEX-TRANS-01: Internal paging has a long black staging interval

Status: Solved 2026-10-01 for internal Description paging; automated and manual acceptance passed

Paging between Selected-Mon entries shows a fully black screen for roughly
8-16 frames. This occurred on every internal paging operation in the
`pokecrystal-260902-084326.mkv` review.

2026-10-01: All-species normal-input paging on the accepted cry-ownership build
measures 8.831-14.962 intervals from accepted change to the revealed codepoint.
Blackout precedes RAM preparation, then internal paging stages owner buffers
but still uses the general map copier and a separate reveal wait. A private
atomic-publication/late-hide prototype established the fix direction. The
integrated handoff now reduces mean navigation time by 2.316 intervals and
mean completed black frames from 9.936 to 4.670 across all 373 transitions.
Necessary shared-VRAM staging still produces 3-9 black frames; this is not a
blackout-free architecture. See the
[implemented transition](pokedex_internal_transition_investigation.md#implemented-internal-handoff).

That paragraph records the first integration, not the current presentation.
The accepted follow-up masks only the portrait to white while preserving the
outgoing shell, footprint and type badges. Incoming icons upload into an
inactive set and reveal with the new maps/palettes. The final production link
has zero fully black/white display frames across all 373 settled transitions;
the portrait still needs a bounded masked staging period. Manual review passed.

### DEX-TRANS-02: Species identity is not published atomically

Status: Solved 2026-10-01 for the reproduced internal handoff; automated and manual acceptance passed

During internal paging, the frontpic and textual identity can belong to
different Pokemon. Confirmed examples include Mewtwo with Exeggcute data,
Rayquaza with Kyogre data, and Meganium with Bayleef data.

2026-10-01: Current normal-input reproductions are Heracross -> Koffing,
Doduo -> Dodrio, Crawdaunt -> Baltoy, Baltoy -> Claydol, and Croagunk -> Toxicroak.
They expose the incoming portrait with outgoing identity for 2-3 completed
frames. `Pokedex_ApplyUsualPals` temporarily requests palette publication before
new maps are ready. A request-free local staging helper removes all reproduced
mixing in the private sweep. Production now uses request-free staging and an
atomic owner publication, with all 373 settled handoffs and 36 focused active
traces clean. The historical pairs above were not re-established on the baseline
link; the actual five current reproductions pass on the integrated build.
The accepted buffered-icon follow-up also passes all 373 current-link pixel,
type/footprint and publication checks, plus focused active transitions.

### DEX-TRANS-03: Graphics and palettes can mix before playback begins

Status: Solved 2026-10-01 for the demonstrated shared handoff; automated and manual acceptance passed

Internal paging can expose a staged frontpic with the prior Pokemon's palette
or stale tiles. Confirmed examples include Dusknoir with Metagross's blue
palette and a following mixed Metagross frame containing stale graphics and an
incorrect Pokedex number.

2026-10-01: The current premature palette reveal also exposes stale outgoing
second type badges during Heracross -> Koffing and Crawdaunt -> Baltoy. The
historical blue Dusknoir palette itself was not reproduced. No blocked palette
writes or animation/audio misses accompany the five current raced transitions.
All reproduced staging artifacts disappear on the integrated build, with no
blocked palette writes, exposed staging or playback misses. The historical blue
Dusknoir example remains un-reproduced on the baseline; this result establishes
the correction of the demonstrated shared handoff, not an independent diagnosis
of every historical screenshot.
Manual review of the resulting presentation, including retained outgoing icons,
passed. No historical un-reproduced screenshot is claimed independently diagnosed.

These three items are addressed together as one Selected-Mon paging
transaction: retain the old page through RAM preparation, hide for shared-VRAM
portrait replacement while retaining buffered icons, then reveal one complete
species state atomically.
The [current investigation](pokedex_internal_transition_investigation.md) records
reproduction steps, trace evidence, final-link regression, resource costs and
remaining limits. All-species cold/paging playback, 1,492 active owner handoffs,
and Listing return/cache regression pass; animation/audio production quotas
are unchanged. Icon buffering adds twelve VRAM tiles and reuses one existing
scratch-union byte; it does not allocate more WRAM or change the animation slots.

### DEX-NAV-01: Internal paging does not wrap at list boundaries

Status: Solved for New Dex internal paging; normal-input boundary regression passed

The earlier Selected-Mon implementation stopped at the beginning and end of
the Pokedex rather than wrapping. The current
`PokedexSelectedMon_FindNextSeen` already wraps forward to index zero and
backward to `wDexListingEnd - 1`, skipping unseen entries and stopping if it
returns to the current selection.

2026-09-30: A normal-input headless SameBoy check on the accepted Description UI
build verifies Up from Chikorita (index 0) reaches Regigigas (index 372), then
Down from Regigigas returns to Chikorita. Both entries finish without animation
or sampled-cry misses. The all-seen New Dex save and the hash-matched UI ROM
copy were used; no game RAM, ROM instructions or cartridge flags were patched.
Evidence: `build/dex-description-ui/cold-final/boundary-wrap-report.json`.
Sparse seen sets and Search Results were not part of this focused boundary test.

### DEX-NAV-02: A rapid axis change repeats the previous vertical input

Status: Solved 2026-10-02; shared-menu production fix accepted after automated and manual testing

2026-09-21: During Dex testing, quickly pressing Up followed by Left or Right
is processed as two Up inputs. Quickly pressing Down followed by Left or Right
is likewise processed as two Down inputs. The reverse order, Left or Right
followed by Up or Down, processes both directions correctly.

Expected behavior: a newly pressed D-pad direction takes priority over a held
direction, while ordinary held-key repeats remain available.

2026-10-01: normal-input headless SameBoy reproduces all 24 vertical-first
overlap cases across Listing and Selected. All 80 clean-release conditions
work. `JoyTextDelay` accepts the whole held mask on any new press while
`hInMenu` is set; the Listing then prioritizes Up/Down in `hJoyLast`. A new
Right therefore has `hJoyPressed = $10` but `hJoyLast = $50`, and another Up
wins. This is not a stale navigation queue or ordinary timer-driven repeat.

Selected has the same cause: its footer accepts new Left/Right, then species
paging also accepts the old Up/Down from `hJoyLast`. When the footer repeat
delay expires, the reverse combination can likewise repeat an old horizontal
move before new vertical paging. Simultaneously new diagonal inputs remain
a separate existing priority policy, not a replayed old key.

Follow-up: the user also reproduces the issue in the Pack. The approved
diagnostic implements the fresh-direction rule inside `JoyTextDelay`'s shared
menu branch, preserving button bits, registers and no-new-direction repeats.
Native Pack input now reproduces the baseline's old-axis pouch change and
confirms its removal in the candidate. The separate cartridge passes 393,216
linked contracts, 1,536 scripted-input fixtures, a 57-state menu matrix,
all-species cold/internal Dex audits and the 20-species New Entry input sweep.
Walking and cycling movement checkpoints match the baseline. Cost is 14
ROM0 bytes, no allocated memory or added display waits, and zero extra CPU
cycles outside menu mode. The original Dex-only alternative costs 28 ROMX
bytes and affects only Listing/Selected.

2026-10-02: the user confirms improved menu input and unchanged overworld
movement, and approves promotion. The exact diagnostic correction is now in
production `home/joypad.asm:JoyTextDelay`. Fresh menu directions exclude old
held D-pad bits while retaining held A/B/Select/Start. Non-menu input,
ordinary repeat timing and simultaneous-new diagonal priority are unchanged.
This resolves the demonstrated menu issue, not rapid-tap buffering or turning
delays in the overworld. See the
[direction change investigation](pokedex_direction_change_investigation.md)
for reliable steps, trace evidence, coverage limits, results and measured costs.

## Return To Listing

### DEX-RETURN-01: Some returns show a white blank screen

Status: Solved; LCD-on cache repair and all-seen/sparse return regressions passed

Selected-Mon to Listing sometimes displays a white screen for roughly 4-5
frames before the Listing appears.

2026-10-01: open Chikorita, internally page nine times to Pidgey, then B after
playback settles. A missing five-row cache tag invokes `Pokedex_PrimeGridCache`,
which disables the LCD, rebuilds all rows, and re-enables it before the Listing
is ready. Five white presented frames are followed by seven outgoing Description
frames. Sparse seen rosters reproduce the same path with six white frames.
Fix direction: retain matching rows and refill missing rows with the existing
LCD-on uploader while keeping the outgoing owner visible until a complete
Listing handoff.

Implemented 2026-10-01: `Pokedex_RepairGridCache` retains matching rows and
uses the existing LCD-on three-transfer uploader for missing rows. The nine-page
Pidgey path repairs one row, not five; sparse far jumps repair all five safely.
All 25 all-seen/sparse/bottom-boundary return conditions and nine repeats have
zero white frames and no LCDC toggles. Scrolling/wrapping and re-entry also pass.
See the
[current investigation](pokedex_listing_restoration_investigation.md#cause-3-lcd-off-cache-rebuild-exposes-the-wrong-owner).

### DEX-RETURN-02: The Selected page can reappear vertically displaced

Status: LCD-off page reappearance resolved; historical displacement not reproduced in current-link revalidation

After the white blank interval, the Selected page can reappear eight pixels too
low and move upward one pixel per frame before the Listing takes ownership.

2026-10-01: the outgoing page does reappear after LCD re-enable on cache rebuilds,
but the eight-pixel displacement/upward movement is not reproduced in the
current all-seen or sparse tests. Hardware and mirrored SCY remain zero.
Do not close the displacement report solely by fixing the proven LCD-off path.

The cache-repair correction removes the LCD-off/white interval and its later
page reappearance. The outgoing page now remains visible continuously until
the complete Listing is ready. No eight-pixel displacement is reproduced by
the fixed return suite; the historical displacement report remains open.

2026-10-02: 448 targeted/all-species B-returns, including sparse-seen,
active-cancel, text-page-2 and internally paged paths, expose no displacement
across 7,211 completed display frames. Hardware and mirrored SCY remain zero.
Keep the older report as unreproduced pending manual confirmation; no scroll
patch is proposed. See the [revalidation evidence](pokedex_backlog_revalidation.md).

### DEX-RETURN-03: Listing BG minisprite columns can contain stale graphics

Status: Solved for the confirmed palette cause; restoration and cache-byte checks passed

Some returns reveal the Listing immediately, but the left and right BG
minisprite columns contain footprint or frontpic-era tiles. The middle OAM
column remains correct. The appearance initially suggested incomplete BG cache
restoration or publication.

2026-10-01: direct Chikorita -> Description -> B reliably reproduces the side
columns' incorrect appearance. All 120 cached icon tiles remain byte-identical;
the side maps still select those icons. `CGB_PokedexStageListLayout` prepares
correct targets but leaves the palette dirty flags zero, so the owner publisher
skips the restore and retains Description BG slots 2-7 (38 differing bytes).
The middle OAM palettes remain correct. Six direct species, active B-cancels
and text-page-2 returns reproduce this. This is palette state, not overwritten
icon graphics, in these cases. Restore requests and the unsafe publication below
must be addressed together.

Implemented 2026-10-01: every Selected B-return explicitly requests BG slots
2-7 and OBJ slots 0-5, then uses the Listing-only safe publisher. All 96 bytes
are committed legally and match the independent Listing targets. The tested
direct, internally paged, active-cancel and page-2 return paths have no visible
palette mismatch. Cached graphics also match independently reached viewports.
See the
[palette diagnosis](pokedex_listing_restoration_investigation.md#cause-1-listing-palettes-are-prepared-but-not-requested).

### DEX-RETURN-04: Listing can briefly expose placeholder selection state

Status: Historical report not reproduced in current-link revalidation; manual revalidation pending

Some returns briefly show the unseen portrait, `-----`, or an intermediate
cursor position before restoring the real Listing selection.

2026-10-01: the original 24 restoration conditions and fixed 25-condition suite
did not expose these placeholder
states. Keep this report open pending a matching current-link reproduction;
palette/cached-row findings alone do not prove its cause.

2026-10-02: the 448-return revalidation compares the rendered selection header,
static portrait, actual absolute selection and hardware cursor against an
independently reached Listing. No unseen portrait, `-----` or intermediate
cursor appears on first reveal or subsequent observed frames. The existing
atomic handoff passes; no additional repair is justified without a matching
reproduction. See the [revalidation evidence](pokedex_backlog_revalidation.md).

The return issues should be handled as one Selected-Mon-to-Listing ownership
handoff, including tile data, tilemap, attrmap, palettes, OAM, scroll position,
and selection metadata.

## Listing Follow-Ups

### DEX-GRID-01: Intermittent minisprite palette errors

Status: Solved for both confirmed Selected-to-Listing palette-handoff causes

Listing minisprites can receive the wrong palette, especially after ownership
transitions. This may share its root cause with `DEX-RETURN-03`.

2026-09-21: The user reconfirms intermittent palette errors when B-returning
from Selected to Listing. The automated logical-return checks do not validate
palette restoration and do not close this issue.

2026-10-01: direct returns skip BG restoration (`DEX-RETURN-03`). After internal
paging, dirty flags instead remain `$fc/$3f`; the owner attempts maps plus both
palette ranges in one VBlank. Its 5,540-T-cycle commit reaches visible LY 0,
where eleven OBJ writes (byte indexes 22-32) are rejected in mode 3. It still
acknowledges success and clears the flags. OBJ palette 3 keeps two wrong bytes
in several cases; other cases mask the failure because old/new values happen
to match. Fix the explicit restore request and actual write-window admission
as one Listing publication change. See the
[timing diagnosis](pokedex_listing_restoration_investigation.md#cause-2-the-owner-commit-runs-into-mode-3).

Implemented 2026-10-01: map transfers remain in VBlank, and Listing-only palette
writes wait for legal STAT windows. OAM completes before its first dependent
line. The direct restore request and guarded publication are tested together;
zero writes are rejected in the normal return suite or 43 late-entry stress
cases. No wrong visible BG/OBJ palettes remain in these reproductions. This
does not claim to close unrelated Search/Options/Area palette bugs or the
separate caught-ball report below. See the
[implementation and regression](pokedex_listing_restoration_investigation.md#implemented-restoration).

### DEX-GRID-02: Caught Poke Ball can receive the wrong OBJ palette

Status: Historical report not reproduced in current-link revalidation; manual revalidation pending

The caught indicator has occasionally appeared with the wrong palette. The
issue is difficult to reproduce and should be tested alongside Listing palette
restoration.

2026-10-01: caught-ball OBJ slot 1 is correct in the tested returns and lies
outside the confirmed rejected-write range. Keep this issue separate/open;
do not assume the palette-3 corruption explains the earlier caught-ball report.

2026-10-02: actual hardware OBJ palette 1, marker OAM attributes/tile/bank and
uploaded tile pixels pass all 746 mixed/all-caught Listing viewports (3,382
visible markers), plus the transient return-frame checks. Target buffers alone
are not used as proof. This does not establish the original report's cause;
retain it as unreproduced and do not add a marker-specific patch. See the
[revalidation evidence](pokedex_backlog_revalidation.md).

### DEX-GRID-03: Retained grid IDs are not garbage-collection roots

Status: Solved; presence flags replace retained grid IDs; reproduction and regressions passed

2026-10-01: cold-open Luxray, settle, B, then Up, Down four times, Up three
times, Left, Right, releasing the pad between presses. At Listing scroll 336,
the middle row (Rampardos, Shieldon, Bastiodon) retains temporary species IDs
`$52/$53/$54`, but their conversion-table entries are zero. Graphics, flags,
palette metadata and hardware colors remain byte-correct. A full re-entry/
return reconstructs the IDs. The exact unchanged baseline reproduces this too;
it is not a regression from the Listing-restoration correction.

`PokemonTableGarbageCollection` marks other retained species owners but not
`wPokedexGridSpecies`; allocating the entering row can collect IDs still stored
in shifted rows. Selected identity is independently resolved from the absolute
16-bit order entry and locked, so no wrong name, selection or frontpic is seen
in this test. Keep this as a metadata warning, not an invented visual defect.

The approved correction reuses the same nine bytes as `wPokedexGridOccupied`:
`1` for any valid order entry (seen or unseen), `0` for an empty cell. Palette
construction receives a fresh ID explicitly; grid drawing and cursor validation
retain only occupancy. Selected identity and the five-row VRAM cache continue
using stable order positions. No global GC changes, additional locks, or RAM/
VRAM allocations are needed; the linked code saves three ROMX bytes net.

The original Luxray sequence now retains Boolean flags with byte-correct visible
graphics/palettes and no warnings. All 25 normal return conditions, 281 follow-up
checks and 43 admission stress cases pass, along with 72 focused unit tests.
All 373 species retain exact animation timing and uninterrupted sampled-cry
completion on cold entry and internal paging. That build's separate Drapion
text overflow was subsequently corrected under `DEX-UI-02`. See the
[implementation and evidence](pokedex_listing_restoration_investigation.md#presence-flag-correction).

### DEX-GRID-04: Listing Navigation Can Attempt A Blocked BG Palette Write

Status: Host-observed legality warning 2026-10-03; cause investigation deferred

The private Moves regression's Selected-to-Listing restoration itself passes
all 96 repeated cases. Three repetitions of the subsequent navigation sequence
after a Dusknoir active-16 return each attempt one BG palette-data write in
mode 3. The follow-up's strict legality audit therefore passes 93/96, not 96/96.
All sampled cache, OAM, palette and visible-content comparisons remain correct;
this report does not assert visible corruption that was not observed.

Reproduction uses all-caught cold Listing checkpoints: enter Dusknoir, return
with B after 16 display intervals, then Up, Down four times, Up three times,
Right, with released inputs between navigation requests; re-enter and return
as in the Listing follow-up harness. Preserve the saved phase for investigation.
The rejected write is $35 to $ff69 at bank $21 PC $4f81, LY 129/mode 3,
T=4,871,548 in the original traced follow-up.

Matched before/after cartridges loaded from the same Listing checkpoint show
identical return timing (9.254784689 intervals) and identical follow-up findings.
The egg-index inheritance change therefore did not introduce it. Evidence:
`build/dex-moves-prototype/candidate/build/listing-egg-matched-before/`,
`listing-egg-matched-after/` and `listing-egg-regression/`.
The cause and fix cost are not yet established. Trace the palette writer and
any intervening interrupt before choosing an atomic write/admission correction;
do not hide the warning by weakening the mode-3 audit.

## Secondary Pokedex Screens And Presentation

### DEX-UI-01: Footprint background uses pure black

Status: Solved for Selected Description; automated UI audit and manual confirmation passed

The Selected Description footprint's formerly pure-black background now uses
the Dex dark grey (`RGB 5,5,5`) in BG palette 2, retaining its white footprint
pixels. The 2026-09-30 UI audit verifies the footprint palette and attributes
across all 373 species, and the user accepts the new Description layout.
This does not change the New Dex Entry layout. See
[Description UI implementation](pokedex_description_ui.md#type-badges-and-palettes).

### DEX-UI-02: Pokemon category text is cut off for some species

Status: Solved; category-data corrections and focused headless regressions passed

The two reports had different data causes. Drapion exceeded the available
character width. Mew was not being clipped: its source category was already
abbreviated to `New Specie@`, without the final `s` in `New Species`. The approved
2026-10-01 data correction uses `New Species@` for Mew and `Scorpion@` for
Drapion, matching Skorupi's existing category. No renderer or scheduler changed.

Historical baseline evidence: the all-species cold Listing automation confirmed
a related Drapion portrait artifact before animation. `DisplayDexEntry` in
`engine/pokedex/pokedex_2.asm` printed its 13-character `Ogre Scorpion` at `(9,4)`
without a field-width limit.
The last `o` and `n` overflow the 20-column WRAM row to `(0,5)` and `(1,5)`.
At initial Selected-page reveal, portrait cell 28 contains font tile `$ad`
(`n`) instead of base tile `$04`, with the correct bank attribute. This matches
VRAM map cell `$00:$98a1`. Every subsequent animation publication has the
correct map and tile pixels; the first publication repairs the visible portrait.
There are no animation or cry misses. This is page text construction, not the
streaming scheduler. The runner deliberately reports `static_reveal_tiles`
instead of treating the known issue as a passing case. See
[cold Listing evidence](dex_cold_listing_results.md).

2026-09-21 cleanup regression: both all-species cold entry and settled internal
paging still report only Drapion's static-reveal defect. A pre-cleanup control
produces byte-identical static tilemap and tile pixels. Animation timing and cry
completion pass in both links; the failure is deliberately not suppressed.

2026-09-21: The user visually confirmed Drapion's overflow in that build.
It was deferred at the time; the animation publications themselves looked correct.

2026-10-01 Mew investigation, before the correction:

- `data/pokemon/dex_entries/mew.asm:1` stores `New Specie@`. The linked
  `MewPokedexEntry` at `$73:$4915` contains
  `8d a4 b6 7f 92 af a4 a2 a8 a4 50`: all ten characters followed immediately
  by the `$50` string terminator, not the `$b2` tile for lowercase `s`.
- The linked pointer for stable species 151 is `73 15 49`, confirming the
  intended bank and entry. `DisplayDexEntry` obtains that pointer and prints
  the category at `(9,4)` through `PlaceFarString`/`PlaceString`. The printer
  stops at `@`; it does not impose a ten-character category limit.
- The ten source characters occupy BG cells `(9,4)` through `(18,4)`.
  Cell `(19,4)` remains the Description blank tile `$32`, with correct
  attributes. No later drawing or animation publication removes a character.
- Repository history already contains `NEW SPECIE@` before the title-case
  conversion in commit `9d98748a6`. This is not a new animation/UI regression.
- Reproduce in New Dex order by selecting Mew from Listing, paging Down from
  Mewtwo, or paging Up from Celebi. The result is always `New Specie`, including
  after settled A-button description-page toggles. Missing caught status only
  suppresses later height/weight/description data, not the category printer.

The read-only headless SameBoy test covers 15 Mew conditions: immediate new
selection, short hover, fully warmed hover, Mewtwo-to-Mew, and Celebi-to-Mew,
each with three input-delay variations. Six Natu/Bronzong control conditions
verify that their existing eleven-character `Little Bird` and `Bronze Bell`
categories fit, including the last character at `(19,4)`. Across all 21
conditions, 63 settled description-page checks and 4,419 Selected-update-loop
row observations match the linked category strings and expected attributes.
There are no animation/audio miss stops or shell/type-badge audit failures.
These are read-only observation points, not a claim of sampling every physical
display frame. Mew was tested seen-but-not-caught; caught-category behavior is
supported by the shared printer's unconditional placement before `CheckCaughtMon`.

The diagnostic ROM is a byte-identical copy of the committed restoration/grid
build, SHA-256 `3cafe3699e1a33d50865ea8ed82896bfc36be0fffc6b6e6d2cf27cdf8abd95da`,
with matching symbols SHA-256
`8ea6a02d3f6d7eab981cbe2dac7e3b0c0652406689f4c4974a8ed7323ed91a01`.
The separate runner, read-only investigation script, raw report and screenshots
are under ignored `build/dex-category-rendering/`. The initial investigation
changed no game source, live battery save, production build artifact or runtime
instrumentation.

Implemented correction and validation:

- Mew's category is now `New Species@`. It is eleven characters and fits
  `(9,4)` through `(19,4)` without touching the right border at column 20.
  Drapion's eight-character `Scorpion@` also fits without overflowing the map;
  Skorupi already had that value and needs no edit.
- The two data changes save four ROMX bytes net: one added for Mew and five
  removed from Drapion. There is no new ROM0 code, WRAM/HRAM state, font tile or
  VRAM allocation. Variable-length category parsing continues to locate the
  numeric and description data through the terminator.
- The fresh normal-input cold suite passes all six species: Mew, Skorupi,
  Drapion, Chikorita, Natu and Bronzong. All qualify as cold at A acceptance and
  pass static reveal, authored animation timing, cry completion and logical
  B-return. Drapion's initial portrait is now byte-correct before animation.
- The read-only UI suite passes 33 cold, hovered and internal-paging conditions,
  99 settled description-page checks and 6,291 Selected-update-loop category-row
  observations. Mew, Skorupi and Drapion display complete categories; shell,
  type badges and category attributes remain correct. No animation/audio miss
  stops occur. This is focused runtime coverage, not a fresh all-species replay.
- A linked-data audit verifies all 373 entry pointers, category strings and
  terminators, and height/weight values against their sources after relocation.
  All 373 categories fit the eleven-character field. The audit does not add a
  permanent build-time width guard or runtime clipping.

Current test ROM SHA-256:
`c94a70ad545580a580b55ba24133e222f032f3afb4c8c6f3102101796a763470`.
Matching symbols SHA-256:
`bb1222d0ad898826b9a1fa5b033aed98422c31dbfcf6d1aa8bcab867b061590e`.
Reports and visually checked screenshots are under ignored
`build/dex-category-rendering-fixed/`. Tests leave the production ROM and source
battery unchanged; the live SameBoy save was not edited.

### DEX-AREA-01: Area transitions expose temporary corruption

Status: Deferred

2026-10-01 buffered-icon integration: twelve focused Area roundtrips (six on
icon set A and six on set B) retain correct returning footprint/type graphics.
These controls do not independently close the older Area presentation report.

Description-to-Area and Area-to-Description transitions can reveal temporary
tilemap corruption.

2026-10-01 cry-ownership regression also reproduces an Area setup stall in
both the unchanged category-fix baseline and the integrated cry fix. Open
Dusknoir, move the footer cursor Right three times, and press A. The first
nest-icon `Request2bpp` remains pending (one tile at `$87f0`), and the Area
input loop is never reached, so B cannot return. In both builds, all six
observed `Serve2bppRequest` calls arrive at LY 146 and reject the request:
that service accepts only LY 144-145. The existing Dex VBlank fallback is too
late for this request; this is not introduced by cry cancellation.

Potential directions for a separate Area pass: select an appropriate ordinary
VBlank handler before Area requests, or provide measured Area-local tile
service, with entry/return graphics ownership audited. Area-entry cry cleanup
passes, but Area navigation/rendering is not signed off. See the
[deferred Area diagnostic](pokedex_cry_ownership_investigation.md#deferred-area-stall).

2026-10-02 Description-text regression: twelve of fifteen pending-text Area
entries stall during setup; three roundtrips pass. A separate no-A replay on
the unchanged pre-text-fix ROM stalls in thirteen of fifteen entries. Both
tests enter the Area owner and wait before its input loop, confirming that
this existing setup failure is independent of Description text publication.
The new text job is canceled at Area handoff; this pass does not fix or sign
off Area rendering/navigation.

### DEX-SEARCH-01: Search-page Slowpoke has an all-black palette

Status: Deferred

The Search page currently displays Slowpoke with an incorrect all-black
palette.

### DEX-EXIT-01: Saved menu viewport is restored before the Dex is hidden

Status: Merged into DEX-PERF-01 on 2026-10-02; confirmed defect remains unfixed

The user deferred the standalone fix so entry/exit timing and presentation can
be addressed together. See
[DEX-PERF-01](#dex-perf-01-optimize-pokedex-opening-and-closing) for scope,
acceptance criteria and retained diagnostic evidence. This ID remains as a
cross-reference, not a separate active work item or a solved bug.

### DEX-DATA-01: Custom entries contain placeholder data

Status: Content backlog

Some custom Pokemon entries still have blank or placeholder descriptions and
unknown height/weight values.

### DEX-DATA-02: Complete Species Data During The Planned Species Revision

Status: Deferred by the user 2026-10-03; includes confirmed DEX-INFO-02

The user will review species learnsets, updated base stats and related species
data in a later content pass. Complete actual gameplay evolution links and
their requirements during that work, then regenerate Dex Info. Missing
evolution pages remain an expected consequence of incomplete source records,
not a reason to invent a separate Dex-only evolution graph.

Retain the [independent source/linked audit](pokedex_info_return_evolution_investigation.md#confirmed-missing-evolution-content):
all 373 Info lists match gameplay, but only Skitty has a nonempty added-species
evolution block; the existing first-stage table identifies 67 family members
unreachable from their root. Check added branches on vanilla roots as well as
new families, and normalize Delcatty's lowest-stage metadata to match the
approved Skitty link. Preserve current evolution records until changes are
explicitly chosen; approve absent items or unsupported methods separately.

Acceptance: independently verify intended family completeness and requirements,
regenerate Info and confirm all future stages/conditions/pages, then test actual
gameplay evolution behavior and relevant species/learnset/stat consumers.
`DEX-DATA-01` remains the separate placeholder Dex prose/height/weight backlog;
coordinate that content where appropriate without silently closing it.
Shared pagination (`DEX-PAGE-01`) is renderer work and may proceed before this
species pass without changing the data. No content implementation is approved
by this deferral, and no completion date is assigned.

### DEX-DATA-03: Revalidate Dex Moves Egg Inheritance During Species Updates

Status: Deferred by the user 2026-10-03; coordinate with DEX-DATA-02

The integrated Moves renderer shares each configured evolution family's existing
egg-move list across all of its members. It uses actual gameplay evolution
links, including branches and baby species, and does not infer missing links
or change breeding behavior. Consequently, deferred families and newer branches
such as Sneasel/Weavile and Eevee/Leafeon/Glaceon still need their real species
data completed before they inherit the expected Breeding pages.

During the species pass, complete evolution links and egg lists, rebuild, then
verify every member's Breeding content, category-separated page count and wrap.
The generator rejects different nonempty egg lists within one family rather
than silently choosing or merging them; explicitly resolve any such content
conflict. Retain the 19-page limit and review its build errors after learnset
expansion. Do not close this story merely because existing configured families
pass the renderer's regression suite.

The Moves index is automatically regenerated from species constants, evolution/
level-up pointer tables, egg pointers/lists and base-stat compatibility. Adding
a fully configured species requires no manual Dex Moves index entry or family
override. A new species and subsequent family-link edit are covered by an
automated generator test. Normal game-wide species registration, source-table
order/completeness and resource limits still apply. Each new species adds a
17-byte Moves descriptor plus its generated TM/HM/tutor eligibility bytes;
review bank capacity when expanding the roster. A new source-file partition,
nonstandard species filename or future tutor schema needs generator review,
not hand editing of its generated index.

## Dex Performance Optimization

### DEX-PERF-01: Optimize Pokedex opening and closing

Status: Deferred story; includes DEX-EXIT-01, no production implementation approved

2026-10-02: optimize the full Start-menu-to-Dex entry and Dex-to-menu exit
procedures together rather than adding a standalone mask fix. The objective
is faster, responsive opening/closing with clean graphics ownership throughout
the transition, not simply replacing visible waiting with a longer blank mask.
Selected-Mon internal paging and New Dex Entry are separate transactions.

Investigation scope:

- Measure accepted input to first visible transition, complete incoming screen
  and renewed input readiness separately on both entry and exit.
- Profile menu fades, Dex graphics/cache initialization, waits, exit sound,
  cleanup and overworld map reconstruction. Identify redundant work or waits
  and useful opportunities to prepare work without exposing partial screens.
- Design viewport, tilemap/attributes, palette and OAM handoffs together;
  resolve the merged exit shift as part of that sequencing.
- Preserve the overworld-union reconstruction required by Dex scratch use,
  species-ID cleanup, menu/viewport restoration and audio ownership. Do not
  remove necessary rebuilds or waits solely to improve a timing number.
- Cost any proposed implementation before approval, explicitly flagging ROM0,
  WRAM0 or HRAM changes. The broader optimization has not yet been costed.

Merged defect and evidence from DEX-EXIT-01:

A shell/layout shift was previously reported while leaving the Pokedex for the
main menu. The user reconfirms it in the latest build. Headless normal-input
revalidation reproduces one colored outgoing Dex frame displaced five pixels
right, with the right-hand window content missing, in all 88 exit cases.

`Pokedex.exit` restores saved `hSCX/hWX/hWY` before returning. The Start-menu
caller then rebuilds overworld map blocks before `CloseSubmenu` requests white
palettes. That rebuild takes 76,660-84,004 T cycles, crossing VBlank while old
Dex colors/maps remain visible under the restored viewport. No palette write
is rejected; this is owner/cleanup ordering, not animation or audio starvation.

A private Dex-local early white-mask request removes the displaced frame in
all 88 matched cases without adding a display interval. Final menu VRAM,
palettes, OAM and viewport state match; first white occurs 19 intervals earlier,
replacing the previous static-Dex dwell. Proposed net cost is nine ROMX bytes,
with no new ROM0, WRAM0, WRAMX, HRAM or VRAM allocation. The earlier white
appearance is the visual tradeoff. The late-hide-and-wait alternative may add
an interval and is not yet tested. No production assembly or ROM changed.
These remain comparison candidates, not the prescribed optimization design;
the user deferred promotion of the narrow early-mask fix.
See [reproduction, trace, alternatives and costs](pokedex_backlog_revalidation.md#confirmed-exit-shift).

Acceptance and regression requirements:

- Report before/after entry and exit timings, with any added blank duration or
  latency tradeoff made explicit; retain a matching baseline/private test ROM.
- Eliminate the displaced colored Dex frame and avoid mixed-owner palettes,
  missing window content, placeholder selection or partially restored maps.
- Re-run the existing 88-case exit matrix and Listing restoration/cache tests;
  broaden entry/exit controls to supported Dex modes and secondary-owner
  routes affected by the implementation, plus rapid open/close and re-entry.
- Verify returned Start-menu graphics, OAM, palettes, selection/input state and
  viewport, then normal overworld rendering, movement and audio after closing.
- Preserve accepted Description animation/cry timing and input behavior in
  focused and all-species regressions. Obtain manual presentation approval.

### DEX-PERF-02: Profile And Optimize The Completed Dex

Status: Deferred story; start after Moves, Area and other Dex modes are implemented

Requested 2026-10-03 after the Info return/evolution investigation. Optimize
the completed Dex as a whole using measured headless normal-input traces,
not assumptions about heavy operations or isolated synthetic throughput.
Coordinate entry/exit work with `DEX-PERF-01`; retain that story's merged
`DEX-EXIT-01` acceptance requirements rather than duplicating or closing them.

Scope:

- Profile accepted input to first visible response, complete publication and
  renewed input readiness for Listing selection, internal species paging,
  B-return, lower-tab/page changes, searches, supported modes and entry/exit.
- Separate CPU copy/decode work, VRAM/DMA and palette/OAM publication, boundary
  waits, input-repeat timing and necessary cache restoration. Record cold,
  settled and canceled/rapid-input cases, including sampled/synthesized cries.
- Investigate restoring only invalid Listing components, retaining unaffected
  cache rows/frames, deduplicating repeated preparation and performing safe
  early work. Info currently invalidates complete row tags when only its
  borrowed frame-0 glyph atlas changed; evaluate component ownership before
  weakening those tags, especially after internal paging changes the viewport.
- Assess bounded lower-job scheduling and shared buffered pagination after all
  tabs exist. Do not trade exact portrait timing/audio reliability for an
  apparently faster tab, remove input checks or expose partial graphics.
- Revisit the accepted committed-record B-return costs: common atlas-B
  returns add about 50ms/three intervals (smaller glyph sets about two),
  atlas-A returns are effectively unchanged, and settled Info Stats activation
  adds about 33.49ms/two intervals. Preserve the outgoing panel and immutable
  visible-page ownership when optimizing either preparation or Listing repair.
  The records reuse 611 overlay bytes, leaving 200 bytes before `$dc00`;
  future mutually exclusive lower tabs should share the workspace. See the
  [measured comparison and production acceptance](pokedex_info_return_records_preflight.md).
- Cost each candidate and explicitly flag ROM0, WRAM0, WRAMX, HRAM and VRAM
  additions. Prefer existing owner scratch and ROMX trades where justified.

Acceptance:

- Matching baseline/prototype ROM identities and repeatable before/after timing
  distributions, including added mask/blank duration and timer/display phases.
- Measurable responsiveness improvement without visual corruption, icon lag,
  stale page digits, palette rejection, incorrect input or ownership leakage.
- Full all-species cold/internal playback accounting, tab/paging/cancellation,
  Listing-cache/navigation, supported-mode and menu/overworld exit regressions.
- Manual presentation confirmation before promotion. Preserve separately
  logged correctness fixes; this story is not permission to defer INFO-01/02.

## Adjacent Deferred Work

### NEWDEX-ANIM-01: Restored Master Ball opening exposes a late first publication

Status: Solved; automated animation/audio regression and manual confirmation passed

After restoring the original Master Ball animation on 2026-09-21, Dusknoir's
authentic catch replay reaches New Dex Entry but misses its first animation
publication. Reason 3 fires at LY 149 after the cutoff reads LY 148; first map
plus attrs requires LY < 148.
The ready map publishes one interval late, shortening its first hold by one
interval. Its sampled cry finishes normally. Seven other catch fixtures pass.
This is separate from `BATTLE-CRY-01`, not a New Entry cry underrun. The earlier
8,570-case acceptance used entry states derived with the standard-ball override.
See the [restoration evidence](new_dex_entry_regression_results.md#master-ball-restoration-follow-up).
Only the ball-animation override was removed; no scheduler fix was attempted.

The user then tested all four Route 30 targets with no New Dex Entry misses;
only Dusknoir's battle cry hit a breakpoint. The installed ROM matches the
restored build hash. A repeat replay of the saved Dusknoir registration state
still reproduces the same first-publication miss, so the manual passes do not
close this timing case. Instruction-level replay confirms the sampled-cry timer
ISR overlaps VBlank and delays the cutoff from the passing fixture's LY 145 to
LY 148. The map was ready; no decoding/refilling takes place in the blocking ISR.

The fixed-rectangle copy optimization is now integrated. It reduces first/final
last-write cost by 732 T, permits a cost-checked LY < 150 gate, and adds **148
ROMX bytes**, with no RAM/ROM0 allocation. Dusknoir now meets its first deadline
and completes the exact 174-interval sequence. All 8,570 input cases pass
animation/picture/audio checks, and all 3,600 synthetic timer-phase cases pass.
That historical run retained eleven text-refresh failures; the later acknowledged
description publisher resolves them. See [current results](new_dex_entry_regression_results.md#acknowledged-description-publication).

After that correction, the user repeated the focused targets several times with
varied input permutations and reported no New Dex Entry animation or sampled-cry
misses. Manual confirmation is complete. Encounter cleanup changes no executable
code or breakpoint addresses; it does not affect this acceptance result.

### NEWDEX-UI-01: Mewtwo page-2 text refresh lags during short animation holds

Status: Solved with accepted presentation caveat; automated regression passes

The restored-Master-Ball input sweep finds this on Mewtwo when A is pressed at
offsets 32-41 or 43 from first publication. Fourteen UI cells, including the page
number and upper text, still differ from the software backing map at the page-2
snapshot. The page number is `$57` in VRAM and `$58` in backing memory. The
remaining cells refresh one to three intervals after that snapshot. The picture
and exact 111-interval animation timeline are correct throughout; no audio miss
or lock occurs.

All eleven cases were replayed on the previous restored-Master-Ball ROM with
its matching entry state. The failing displays and mismatch counts are identical,
so this is **not introduced by the faster copies**. The earlier wholly passing
input sweep used entry phases derived with the standard-ball opening override.

`WaitBGMap` waits four intervals without checking completed map thirds. Due
animation publications and the ACK barrier legitimately defer ordinary BG
updates; Mewtwo's short 1/2-interval holds can delay the middle-third text update
after the lower text has changed. This was not fixed by the picture-copy change.

The subsequent targeted correction queues the complete five-row description
and page number, publishes all 91 cells in one admitted VBlank, and acknowledges
the actual final store. Animation keeps priority and its exact deadlines;
ordinary BG thirds no longer determine description completion. No new RAM or
ROM0 allocation is needed. The eleven paired cases improve from 9-11 intervals
after A to 3, with no mixed old/new text frames. The full 8,570-case input matrix
passes. Per-display pixel/map checks and input-anchored latency ensure this is
not a later snapshot hiding the previous failure.

Manual acceptance (2026-09-21): the user perceives the description text updating
slightly before the page number, approximately one or two frames, and accepts
the result. That offset is unmeasured and was not reproduced by the automated
fixtures. Preserve it as an accepted caveat; no further fix is requested here.
The battle cry issue is separate and remains open.

Evidence: [comparison and traces](new_dex_entry_regression_results.md#remaining-mewtwo-text-refresh),
`build/new-dex-entry-copy-integration/mewtwo-ui-comparison/report.json`.
Fix and paired before/after evidence:
[acknowledged description publication](new_dex_entry_regression_results.md#acknowledged-description-publication),
`build/new-dex-entry-text-publication/mewtwo-comparison/report.json`.

### BATTLE-CRY-01: Dusknoir's sampled cry underruns in battle

Status: User-reported regression; investigation and fix explicitly deferred

Reported 2026-09-21 during New Dex Entry testing: Dusknoir's sampled cry
underruns **in battle, not on the New Dex Entry page**. The user reports that
earlier battle playback worked. The introducing change and underlying cause
have not been established; do not attribute this to the page-2/ACK correction
without a matching-build comparison.

The user reported another battle-cry breakpoint hit on Dusknoir while testing
Route 30 after restoring the Master Ball opening. No New Dex Entry miss was
reported in that manual pass. This battle issue remains explicitly deferred.

When revisited, record the ROM/symbol identity and whether the failure occurs
on wild encounter, trainer/player send-out, or fainting, then capture the
battle stack and sampled cache/remaining-block state at the underrun. The
specific battle trigger has not yet been recorded. Keep this separate from
the Stats Screen issue (`DEX-CRY-03`) and Selected paging cancellation
(`DEX-CRY-04`); passing New Dex Entry tests does not close it.

### BATTLE-MOVE-01: String Shot reports or applies an Attack drop

Status: Deferred investigation

When an opposing Weedle uses String Shot against the player's Dusknoir, the
battle text says `Dusknoir's Attack fell!` instead of reporting a Speed drop.
Determine whether String Shot is actually modifying Attack or whether only the
stat-down message is selecting the wrong stat before implementing a fix.

### BATTLE-CATCH-01: Capture ball disappears during EXP award

Status: Deferred presentation request; original report clarified

After a successful capture, the capture-ball graphic disappears while
experience is awarded. The user requested reviewing that presentation even
though it was not a regression. This is about the capture animation's ball,
not the small HUD caught indicator or trainer party-ball palette; the earlier
backlog wording incorrectly described a caught indicator remaining visible.

### OW-MOVE-01: Research faster player turning without changing walking behavior

Status: Research spike; deferred, no implementation approved

2026-10-02: following acceptance of the shared-menu direction fix, the user
reports that overworld movement feels unchanged and requests retaining
Polished Crystal's turning-delay approach for future consideration. This is a
responsiveness option, not a confirmed new regression or part of `DEX-NAV-02`.

Reference reviewed: local `~/Documents/GitHub/polishedcrystal`, master snapshot
`f7745f128030c2ba8b0bd7ec8c3f161b58791d07`. Relevant code at that snapshot:

- [StepFunction_Turn and .GetTurningSpeed](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/overworld/map_objects.asm#L1626):
  both turn phases load their duration through the helper. `TURNING_SPEED`
  clear returns four updates (Slow); set returns two (Fast). Initialization
  falls through into decrementing each phase, so counter totals alone are not
  an exact input-to-step display-duration measurement.
- [Options_TurningSpeed](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/menus/options_menu.asm#L482)
  toggles the bit in `wOptions1` and displays Slow/Fast. The
  [default options](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/data/options/default_options.asm#L8)
  leave the bit clear: Slow is the default.
- [CheckTurning](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/overworld/player_movement.asm#L187)
  still turns before stepping, permitting a tap to change facing without moving.
  [GetAction](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/overworld/player_movement.asm#L650)
  uses held directions with Down/Up/Left/Right priority, not a queue of taps or
  a newest-direction-wins rule.
- Timing context: Polished's
  [overworld loop](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/overworld/events.asm#L114)
  targets one display interval per update (approximately 60 Hz), and CGB
  [initialization enables double CPU speed](https://github.com/Rangi42/polishedcrystal/blob/f7745f128030c2ba8b0bd7ec8c3f161b58791d07/engine/init.asm#L27).
  Normal walking uses one pixel over 16 updates; this fork uses two pixels
  over eight updates at approximately 30 Hz. The walking pace is broadly the
  same, but the animation resolution differs. Do not copy the turn counters
  without accounting for the different update cadence.

Current fork touch points: `engine/overworld/map_objects.asm:StepFunction_Turn`
uses fixed two-update counters for both phases;
`engine/overworld/player_movement.asm:DoPlayerMovement.CheckTurning` selects the
turn; `engine/overworld/events.asm:MaxOverworldDelay/NextOverworldFrame` governs
the nominal two-display-interval update cadence. Physical input sampling and
menu repeat handling should remain outside this spike.

Research deliverables before proposing a patch:

1. Measure input-to-facing and input-to-first-step timing in headless SameBoy
   for taps, held turns, reversals and overlapping directions at several
   display phases. Separate ordinary tile-step completion from turn holds.
2. Compare a player-only shorter turn hold with a configurable hold, preserving
   the ability to face an NPC without taking a step. Measure costs rather than
   assuming the Polished counters imply the same wall-clock delay here.
3. Check walking, cycling, surfing, collisions, ice/forced movement, scripts
   and NPC turns. The existing turn-step handler is shared with other objects;
   an unguarded change could shorten scripted or NPC turns unintentionally.
4. Return a scoped recommendation and ROM/RAM costs. A 60 Hz overworld port,
   CPU-speed change and D-pad tap queue are separate, unapproved projects.

### QA-CLEANUP-01: Remove temporary encounter edits

Status: Complete; encounter/ball overrides restored and runtime instrumentation removed

Earlier Route 29/30 stress-test encounters were restored before the previous
Selected-Mon animation/cry commit. The Selected scheduler investigation's
temporary overrides were Spheal/Sealeo/Snorlax on Route 29, and
Groudon/Drapion/Yanmega/Rhyperior/Milotic on Route 30. Both blocks were restored
to the branch baseline before that commit, along with trainer/encounter-table
testing edits. Scheduler instrumentation was deliberately retained.

The subsequent New Entry investigation added a new marked test set: Mewtwo,
Vibrava, Exeggcute and Garchomp on Route 29, and Dusknoir, Metagross, Luxray and
Caterpie on Route 30. Following automated and manual New Entry acceptance, both
blocks have now been restored exactly to the committed branch baseline. Trainer
parties and the original Master Ball animation also match that baseline. The
superseded host-only page-2 patch prototype was removed. At that checkpoint,
runtime instrumentation, auditing and reusable regression runners were retained
for the subsequent cleanup.

Runtime instrumentation has since been removed from Selected Description and
New Dex Entry. Production readiness/deadline/cancellation checks and zero-byte
observation labels remain, as do the reusable host-side regression runners.
Post-cleanup automated acceptance and representative manual observations passed;
the later Description UI regressions also pass. No temporary encounter or
Master Ball override remains. See the
[completed cleanup](dex_instrumentation_cleanup.md). Generated outputs remain
under ignored `build/`.
