# Pokedex Selected-Mon Bug Backlog

This file preserves issues discovered while bringing animated frontpics online
for the Selected-Mon section of the Pokedex. Except for `DEX-CRY-01`, these are
deliberately deferred until frontpic animation and cry playback pass the full
Selected-Mon stress suite.

Do not fold these items into animation fixes unless an item directly blocks
animation or cry validation. Revisit them in the groups below after the
animation/cry signoff so each underlying transaction can be fixed and tested as
a unit.

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

### BATTLE-CATCH-01: Caught indicator remains during EXP award

Status: Deferred

After a successful capture, the battle HUD's caught-Pokemon indicator remains
visible while experience is awarded.

### QA-CLEANUP-01: Remove temporary encounter edits

Status: Completed

The Route 29/30 stress-test encounters were restored to their normal tables
before committing the Selected-Mon animation/cry work.
