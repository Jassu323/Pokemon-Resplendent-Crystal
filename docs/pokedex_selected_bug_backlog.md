# Pokedex Selected-Mon Bug Backlog

Updated 2026-09-21. This is the live issue/status list, not the chronological
scheduler investigation. Settled Selected animation/audio acceptance has passed;
the separate UI, input, transition and adjacent-owner items below remain deferred.

Keep each transaction fix independently scoped and tested. A passing animation
counter does not close a palette, text, input or cancellation bug. Earlier
measurements and superseded diagnoses are retained in the
[backlog investigation history](archived/dex-scheduler/dex_backlog_investigation_history.md)
and [scheduler archive](archived/dex-scheduler/README.md).

## Current: Animation Timing

### DEX-ANIM-01: Work scheduling falls behind authored publication deadlines

Status: Settled cold-entry/internal-paging acceptance passed; cleanup regression pending

The current scheduler uses the hardware display clock with independent work
completion, bounded finishing, quiet publication ownership and owner-local
audio/wait sequencing. Later timeline events permit bounded decoding to the
dictionary's end, correcting the Groudon lookahead misses without increasing
startup or allocating more RAM/VRAM.

The recorded target-correction matrix passes 126 replays across 18 species.
The subsequent normal-input cold suite checks all 373 New Dex species, every
published portrait and exact full authored timing with no animation/audio misses.
The user's complete internal-paging pass and representative visual controls also
pass. Drapion's initial static portrait remains the separate text overflow
`DEX-UI-02`, not an animated-frame failure.

Warm entry, rapid cancellation, Description text toggles and all owner/exit
transactions are not signed off. Revalidate after removing instrumentation or
warming; their timing is part of this accepted checkpoint. See the
[implementation](pokedex_animation_scheduler.md), [acceptance/test guide](dex_scheduler_validation.md)
and [cold results](dex_cold_listing_results.md). Historical failures, hypotheses
and progression remain in the archive rather than being repeated as current
open scheduler diagnoses.

### DEX-ANIM-02: Seviper's authored main animation repeats indefinitely

Status: Script corrected; manual cold/internal and automated cold retests passed

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

Status: Uninterrupted cold-entry/internal-paging acceptance passed

The integrated scheduler retains the 32-block prefill and eight-block refill.
The target-correction matrix records 112 natural sampled completions across
16 species and seven timer phases. The normal-input cold suite subsequently
completed all 122 sampled cries naturally with zero cache-empty hits; the full
manual internal-paging pass also had no uninterrupted-playback misses.

The earlier partial improvements and failed cache measurements are preserved
in the [historical entry](archived/dex-scheduler/dex_backlog_investigation_history.md#dex-cry-01-dusknoirs-sampled-cry-underruns-on-the-selected-page).
They describe older builds, not remaining settled-playback failures in this
checkpoint. This acceptance does not close `DEX-CRY-02`, `DEX-CRY-03` or
transition-only `DEX-CRY-04`. Warm entry remains untested, and instrumentation
removal requires a fresh timed regression.

### DEX-CRY-02: A synthesized cry resumes after sampled playback ends

Status: Current

When internally paging from Mewtwo to Dusknoir, Mewtwo's synthesized cry is
paused rather than canceled when Dusknoir's sampled cry takes ownership. After
Dusknoir underruns and sampled playback shuts down, the normal sound engine
resumes and plays the remaining tail of Mewtwo's cry while Dusknoir is still
selected. The Selected-Mon owner change must terminate the outgoing cry state,
not merely start the incoming cry.

### DEX-CRY-03: Dusknoir also underruns on the party Stats Screen

Status: Confirmed adjacent issue

After Dusknoir's Stats Screen cry stopped, `hSampledCryTimer` and the decoded
cache count were both zero while 78 compressed blocks remained. This proves
that the failure is not exclusive to the new Pokedex animation producer. The
Dex still has its own concurrent-workload pressure, but any eventual audio
solution should account for this shared failure mode rather than assuming the
Selected-Mon controller is its sole cause.

### DEX-CRY-04: Outgoing sampled cry can exhaust during species preparation

Status: Confirmed transition-only issue; deferred, low observed impact

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

The species-change path cancels animation production but does not explicitly
cancel outgoing audio before synchronous preparation. The timer can continue
consuming Garchomp's cache while Bastiodon's startup work runs. This is a real
cache-empty stop, not the normal cancellation branch, but it is not an underrun
of Bastiodon's subsequently started cry or of settled playback.

Fix direction, not implemented: stop the outgoing cry at the accepted species
handoff before preparing the next entry. Coordinate sampled and synthesized
cry ownership with `DEX-CRY-02`; do not infer that one implementation necessarily
fixes both without auditing the sound-engine cleanup. No increase to startup
prefill or change to the settled animation scheduler is indicated by this capture.

## Description Paging

### DEX-DESC-01: Toggling description pages can corrupt the upper screen

Status: Open; historical diagnosis superseded, current-link retest required

Pressing A to switch an entry's Description text pages was observed corrupting
the frontpic, header and other upper tile rows. This is a separate transaction
from uninterrupted animation playback, which does not exercise A-page toggles.

The old explanation relied on the portrait publisher lacking an `rLY >= 144`
check. That explanation is no longer valid: the current
`Pokedex_VBlankAnimationFrontpicMap` in [pokedex_3.asm](../engine/pokedex/pokedex_3.asm)
checks `LY_VBLANK` as a lower bound before applying its upper cutoff. The
[superseded diagnostic](archived/dex-scheduler/dex_backlog_investigation_history.md#dex-desc-01-toggling-description-pages-can-corrupt-the-upper-screen)
is retained only as historical evidence.

Retest A during and after animation on the current link before choosing a fix.
Audit the full backing-map transfer through
`CopyTilemapAtOnce` in [tilemap.asm](../home/tilemap.asm), pending portrait
publication, quiet-owner release/reacquisition and text redraw as one
transaction. A race remains an investigation direction, not a proven current
cause. Do not mark this fixed solely because the lower-bound check now exists.

## Selected-Mon Internal Paging

### DEX-TRANS-01: Internal paging has a long black staging interval

Status: Open

Paging between Selected-Mon entries shows a fully black screen for roughly
8-16 frames. This occurred on every internal paging operation in the
`pokecrystal-260902-084326.mkv` review.

### DEX-TRANS-02: Species identity is not published atomically

Status: Open

During internal paging, the frontpic and textual identity can belong to
different Pokemon. Confirmed examples include Mewtwo with Exeggcute data,
Rayquaza with Kyogre data, and Meganium with Bayleef data.

### DEX-TRANS-03: Graphics and palettes can mix before playback begins

Status: Open

Internal paging can expose a staged frontpic with the prior Pokemon's palette
or stale tiles. Confirmed examples include Dusknoir with Metagross's blue
palette and a following mixed Metagross frame containing stale graphics and an
incorrect Pokedex number.

These three items should be addressed together as one Selected-Mon paging
transaction: hide, stage one complete species state, and reveal it atomically.

### DEX-NAV-01: Internal paging does not wrap at list boundaries

Status: Open

Selected-Mon internal paging stops at the beginning and end of the Pokedex
instead of wrapping between Chikorita and the final available entry in the
opposite direction. This should match the full-list wrap behavior already used
by the Listing page.

### DEX-NAV-02: A rapid axis change repeats the previous vertical input

Status: Reported; deferred investigation

2026-09-21: During Dex testing, quickly pressing Up followed by Left or Right
is processed as two Up inputs. Quickly pressing Down followed by Left or Right
is likewise processed as two Down inputs. The reverse order, Left or Right
followed by Up or Down, processes both directions correctly.

Expected behavior: each accepted press uses its actual direction, without
replaying the preceding vertical direction. Record the exact Listing/Selected
owner, whether the first key was released, and the interval between presses
when reproducing; those details have not yet been captured. Inspect newly
pressed, held and auto-repeat input state together with any queued navigation
direction. Do not assume a scheduler or input-buffer cause until that state is
observed. No fix has been attempted.

## Return To Listing

### DEX-RETURN-01: Some returns show a white blank screen

Status: Open

Selected-Mon to Listing sometimes displays a white screen for roughly 4-5
frames before the Listing appears.

### DEX-RETURN-02: The Selected page can reappear vertically displaced

Status: Open

After the white blank interval, the Selected page can reappear eight pixels too
low and move upward one pixel per frame before the Listing takes ownership.

### DEX-RETURN-03: Listing BG minisprite columns can contain stale graphics

Status: Open

Some returns reveal the Listing immediately, but the left and right BG
minisprite columns contain footprint or frontpic-era tiles. The middle OAM
column remains correct. This points to an incomplete BG cache restoration or
publication transaction.

### DEX-RETURN-04: Listing can briefly expose placeholder selection state

Status: Open

Some returns briefly show the unseen portrait, `-----`, or an intermediate
cursor position before restoring the real Listing selection.

The return issues should be handled as one Selected-Mon-to-Listing ownership
handoff, including tile data, tilemap, attrmap, palettes, OAM, scroll position,
and selection metadata.

## Listing Follow-Ups

### DEX-GRID-01: Intermittent minisprite palette errors

Status: Open

Listing minisprites can receive the wrong palette, especially after ownership
transitions. This may share its root cause with `DEX-RETURN-03`.

2026-09-21: The user reconfirms intermittent palette errors when B-returning
from Selected to Listing. The automated logical-return checks do not validate
palette restoration and do not close this issue.

### DEX-GRID-02: Caught Poke Ball can receive the wrong OBJ palette

Status: Open

The caught indicator has occasionally appeared with the wrong palette. The
issue is difficult to reproduce and should be tested alongside Listing palette
restoration.

## Secondary Pokedex Screens And Presentation

### DEX-UI-01: Footprint background uses pure black

Status: Deferred

Footprint graphics use a pure-black background instead of the Pokedex dark
grey.

### DEX-UI-02: Pokemon category text is cut off for some species

Status: Deferred; Drapion overflow confirmed by cold-entry audit, Mew unresolved

The user reports truncated category text in the Dex for Drapion and Mew.
Drapion exceeds the available character width. Mew's category is expected to
fit, so do not assume both cases are explained by string length or share the
same cause.

The all-species cold Listing automation confirms a related Drapion portrait
artifact before animation. `DisplayDexEntry` in `engine/pokedex/pokedex_2.asm`
prints its 13-character `Ogre Scorpion` at `(9,4)` without a field-width limit.
The last `o` and `n` overflow the 20-column WRAM row to `(0,5)` and `(1,5)`.
At initial Selected-page reveal, portrait cell 28 contains font tile `$ad`
(`n`) instead of base tile `$04`, with the correct bank attribute. This matches
VRAM map cell `$00:$98a1`. Every subsequent animation publication has the
correct map and tile pixels; the first publication repairs the visible portrait.
There are no animation or cry misses. This is page text construction, not the
streaming scheduler. The runner deliberately reports `static_reveal_tiles`
instead of treating the known issue as a passing case. See
[cold Listing evidence](dex_cold_listing_results.md).

2026-09-21: The user visually confirms Drapion's overflow in the current build.
It remains deferred; the animation publications themselves still look correct.

Expected behavior: the complete category is readable for each species.
During investigation, compare source strings with the rendered text, check
field bounds and string termination, and determine whether later drawing
overwrites any characters. Record the missing text and entry path for each
case before choosing a fix. No runtime changes have been made for this report.

### DEX-AREA-01: Area transitions expose temporary corruption

Status: Deferred

Description-to-Area and Area-to-Description transitions can reveal temporary
tilemap corruption.

### DEX-SEARCH-01: Search-page Slowpoke has an all-black palette

Status: Deferred

The Search page currently displays Slowpoke with an incorrect all-black
palette.

### DEX-EXIT-01: Dex-to-menu shell shift needs revalidation

Status: Needs revalidation

A shell/layout shift was previously reported while leaving the Pokedex for the
main menu. Recent full-screen fades appeared normal, but the original issue has
not been explicitly closed.

### DEX-DATA-01: Custom entries contain placeholder data

Status: Content backlog

Some custom Pokemon entries still have blank or placeholder descriptions and
unknown height/weight values.

## Adjacent Deferred Work

### NEWDEX-ANIM-01: Restored Master Ball opening exposes a late first publication

Status: Fixed; automated animation/audio regression and manual confirmation passed

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

Status: Closed with accepted presentation caveat; automated regression passes

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

### QA-CLEANUP-01: Remove temporary encounter edits

Status: Complete for Selected and New Entry; instrumentation intentionally retained

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
superseded host-only page-2 patch prototype was removed. Current instrumentation,
auditing and reusable regression runners are intentionally retained for later
cleanup. Generated outputs remain under ignored `build/`.
