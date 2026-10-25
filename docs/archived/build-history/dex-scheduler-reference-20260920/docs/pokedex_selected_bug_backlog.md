# Pokedex Selected-Mon Bug Backlog

This file preserves issues discovered while bringing animated frontpics online
for the Selected-Mon section of the Pokedex. Except for `DEX-ANIM-01` and
`DEX-CRY-01`, these are
deliberately deferred until frontpic animation and cry playback pass the full
Selected-Mon stress suite.

Do not fold these items into animation fixes unless an item directly blocks
animation or cry validation. Revisit them in the groups below after the
animation/cry signoff so each underlying transaction can be fixed and tested as
a unit.

## Current: Animation Timing

### DEX-ANIM-01: Work scheduling falls behind authored publication deadlines

Status: Investigating; runtime fix not implemented

The 2026-09-19 host replay matches the Weavile and Luxray five-stop captures'
core state and timer readings within their measurement uncertainty. Their
producer-call-index schedule loses ground when owner work crosses VBlank before
the next wait is armed; Luxray also reaches an HDMA launch window too late.
Both first-miss cases have fully decoded dictionaries but unfinished uploads.
This is not evidence that the hardware cannot meet the authored animation timing.

The proposed direction is display-clock-based work release with independently
tracked completion, early preparation when slot ownership permits it, bounded
upload/wait scheduling, and unchanged deadline-controlled atomic publication.
It must not skip unfinished work or stretch animation holds to hide failure.

Detailed evidence, build/fixture identities, remaining model uncertainty, code
touchpoints, next validation cases, and final-review gates are preserved in
[Selected Dex Scheduler Investigation](dex_scheduler_investigation.md).
The 2026-09-20 [publication-budget follow-up](dex_publication_budget_results.md)
records successful host-only phase/cost controls, the redundant empty-OAM
transfer, a ready-frame deferral that causes a later upload miss, and the
remaining publication safety bound. These experiments do not close this bug
or constitute a game fix.
The subsequent [steady-display recovery tests](dex_steady_publication_results.md)
bound that quiet publication path and pass the three actual-state phase/cost
suites. Broader partial-state controls retain Garchomp's event-5/frame-4 failure
at 20/30 uploaded tiles despite a fully decoded dictionary, in all 17 runs.
Next is a complete-chain work budget in place of the fixed eight-tile suffix
heuristic. No runtime fix or generalized signoff has been made.
The [Garchomp finishing follow-up](dex_garchomp_finishing_results.md) adds six
new actual starting states, all independently core-calibrated, and a complete-chain
admission candidate. All nine actual sampled-species nominal runs now pass without
larger preload; Garchomp still fails one phase control and two overhead settings.
The missing margin, actual post-cry timer cost, and queue/gather optimization
direction are recorded there. This is host-only progress, not closure of the bug.
The subsequent [queue-copy optimization](dex_queue_construction_results.md)
removes 3,216 T of counted copy-loop overhead without changing map ownership.
On top of the host scheduler candidate, 316 phase/cost/combined continuations
now pass, including all known Garchomp counterexamples. No game fix is installed;
the remaining concrete guard-cost, synthesized-cry and input-handoff validation
gates still apply. The bug remains open.
The [headroom/synth investigation](dex_headroom_synth_results.md) then adds a
fixed tile-copy optimization and an 8,192-T finishing reserve. Its 328 final
phase/cost continuations pass, with a minimum accepted finishing margin of
8,232 T (Garchomp: 12,120 T rather than 556 T). Exeggcute's actual active-synth
baseline is independently core-calibrated; candidate runs preserve its sound
updates, hardware-write sequence and completion frames. This removes the known
tiny finishing margin and adds one genuine synth control, not generalized
runtime or all-synth signoff. Implementation costs and input/owner paths remain
gates. No game fix is installed; this bug remains open.
The separate Description-page transaction bug remains `DEX-DESC-01` below.

## Current: Cry Integration

### DEX-CRY-01: Dusknoir's sampled cry underruns on the Selected page

Status: Measuring

Cry playback has been restored. Baseline instrumentation confirmed that
Dusknoir can exhaust its decoded cache while compressed blocks remain during
concurrent frontpic production. The exact-resident animation-stage fast path is
working as intended but is insufficient by itself:

- Cold Listing-to-Selected and internal Mewtwo-to-Dusknoir runs reduced stage
  builds from 33 to 14 and increased audio production from 216 to 240 blocks,
  but both still underrran with 126 of 366 blocks left compressed.
- A warm Listing-to-Selected run reduced stage builds from 32 to 13 and
  increased audio production from 312 to 344 blocks, but still underrran with
  22 of 366 blocks left compressed.
- Reveal and playback timing did not regress, and none of these runs recorded
  an animation underrun.

Metagross is a useful pre-fast-path baseline control: a cold
Listing-to-Selected run completed with no audio or animation underrun, zero
compressed blocks remaining, and a minimum decoded-cache depth of five blocks.
A post-fast-path repeat remained clean, reduced stage builds from 21 to 15,
and increased its minimum decoded-cache depth from five to ten blocks.

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

## Description Paging

### DEX-DESC-01: Toggling description pages can corrupt the upper screen

Status: Open

Pressing A to switch between an entry's two Description pages can corrupt the
frontpic, header, and other portions of the upper seven tile rows. The failure
is distinct from an animation underrun and occurs during the complete backing
tilemap/attrmap copy used by the page toggle.

This is a tilemap transaction race, not an animation underrun. The A path
redraws the complete backing map through [`CopyTilemapAtOnce` (line 57)](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/home/tilemap.asm:57),
while the animation controller can still have a seven-row portrait publish pending.

[`Pokedex_VBlankAnimationFrontpicMap` (line 1306)](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/engine/pokedex/pokedex_3.asm:1306)
rejects scanlines 146 and later, but never verifies that rLY >= 144.
If the full-map copy delays the VBlank interrupt, the pending handler can
consequently run during visible scanlines 127–143 and treat them as VBlank.
That explains Meganium’s corrupted header, portrait, and horizontal screen
sections immediately after toggling descriptions.

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

### BATTLE-MOVE-01: String Shot reports or applies an Attack drop

Status: Deferred investigation

When an opposing Weedle uses String Shot against the player's Dusknoir, the
battle text says `Dusknoir's Attack fell!` instead of reporting a Speed drop.
Determine whether String Shot is actually modifying Attack or whether only the
stat-down message is selecting the wrong stat before implementing a fix.

### BATTLE-CATCH-01: Caught indicator remains during EXP award

Status: Deferred

After a successful capture, the battle HUD's caught-Pokemon indicator remains
visible while experience is awarded.

### QA-CLEANUP-01: Remove temporary encounter edits

Status: Completed

The Route 29/30 stress-test encounters were restored to their normal tables
before committing the Selected-Mon animation/cry work.
