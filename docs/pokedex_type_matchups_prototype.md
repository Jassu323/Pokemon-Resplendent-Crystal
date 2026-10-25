# Type Matchups Prototype

**Current status, 2026-10-12:** isolated mode-7 runtime is integrated into
production and freshly qualified. Precomputed is preserved as a verified,
rebuildable fallback. See [Runtime Production Integration](pokedex_type_runtime_integration.md)
for current acceptance and timing caveats, [Precomputed Fallback](pokedex_type_precomputed_fallback.md)
for recovery, and [Type Mode 7 Comparison](pokedex_type_mode7_comparison.md)
for the earlier comparison. The shared-interrupt prototype, hold decision and
build paths below are historical; retired loose builds are in the verified
`research_artifacts/dex-build-history-20261012/` family archives.

2026-10-11. Private review build based on production commit
`6d9fba86f6aa67e465721bfd76a53e5662d93ffc`. Production is unchanged.
The gray-panel implementation uses existing compact badges and border assets.

**2026-10-12 status: hold production integration.** The full regression found
six incorrect black pixels in the upper Ice badge and paired
battle-animation duration changes. The exhaustive animation investigation below
confirms the shared interrupt checks as the timing cause. The new native-input
sweep also found a separate Sand Tomb trapping-message hang in production.
Timing acceptance is pending. The fresh failure supersedes the earlier focused visual
acceptance below; the ROM and production were not changed during this run.

## Review Files

- ROM and matching unchanged save: `build/dex-types-cursors-20261011/pokecrystal-dex-types.{gbc,sav}`.
- Private source: `build/dex-types-cursors-20261011/candidate/`.
- Native screenshots and results: `build/dex-types-cursors-20261011/type-tests/` and `arrow-tests/`.
- Rollback source and production outputs: `build/dex-types-cursors-20261011/rollback-source.tar` and `rollback/`.
- Previous review builds remain intact in `build/dex-types-20261011/` and `build/dex-types-immunities-20261011/`.
- Reproducible source changes: `tools/dex_timing/probes/type_matchups_mode.patch`.

Review ROM SHA-256:
`69705d016d2cd9022bdd2fc3ae28d5884b78548012c430ec70cc8f784000803c`.
Unchanged production ROM SHA-256:
`591d2075b0c986846b94bc92288d1fa4f9d2918fccc680a83928fd8fdcf59bee`.

## Behavior and Layout

All 18 types appear alphabetically in a three-column, six-row grid. Moving the
cursor changes the defensive matchup lists immediately; A is not required.
Directions wrap within the grid. B or Select returns to Mode Selection with
Type Matchups highlighted. Canceling that menu returns to the prior listing.

W lists incoming super-effective types, R ordinary resistances, and I
immunities. All lists are alphabetical. Dark, Electric, Fairy, Flying, Ghost,
Ground, and Normal have separate I sections. W/R/I start at y96/y112/y128,
leaving a blank tile row between sections. Ghost and Normal show an empty R
section because they have no ordinary resistances. Types without immunities
omit I. Steel is the exception: its ten combined resistances/immunities stay
under R, including Poison. Grass and Rock have five weaknesses, so their R
sections move down one tile. Battle-only move exceptions and effects such as
Ingrain are not shown.

The upper badges retain the mockup's 14-pixel row spacing without changing SCY.
Existing badge tiles are vertically phased into temporary VRAM slots. Four BG
palettes share white, gray, and black; only their accent colors change between
rows. The frame retains BG palette 0. The single white arrow is the only OBJ.
Lower badges start at x24 to accommodate the existing two-character W:/R:/I: font
labels; four 32-pixel badges still fit per row.

The outer corners reuse the existing text-entry junction tile. During loading,
the five rows outside the panel are filled with the UI's red color, leaving
only the appropriate white corner. This removes the extra ledges and gray
patches at all four corners without changing or adding an asset. The full
top/bottom margins and border strokes are checked against the mockup geometry.

Graphics load behind the standard black transition mask with the LCD kept on.
Cursor updates publish only the five lower rows, the palette-page pointer, and
OAM together during VBlank. A Type-only VBlank condition permits the
bank-independent, register-preserving ROM0 raster handler to interrupt the
remaining non-graphics work, preventing missed color updates.

## Shared Arrow Blinking

All ten arrow-selection locations now use `Pokedex_AdvanceArrowCursorBlink`:
Mode Selection, Pokemon Options, Pokemon Sort, Pokemon Search, the selected
Pokemon footer, Moves listing/results, Moves Options, Moves Sort, Moves Search,
and Type Matchups. The phase is eight owner updates visible and eight hidden,
with a shared visible-on-movement reset. Ordinary BG arrows, the split-tile
Modern Sort arrow, and the Type page's OBJ arrow share the same phase logic.

Popover phase changes queue the normal VBlank map publication without adding
a blocking frame. Moves arrows queue only one tile for a bank-local VBlank
handler. A direct visible-line tile write was rejected after native frame
checks caught a partially drawn arrow. Full redraws cancel stale cursor work.
Type Matchups changes only the existing OBJ arrow's visibility at idle; it
does not redraw badges or alter palette timing.

Corner-outline Pokemon cursors, Unown's diamond, scroll indicators, and the
nickname-style keyboard box retain their existing behavior. No assets changed.

## Workbook Chart

The canonical battle table implements all 324 cells of the
[Type Matchups sheet](https://docs.google.com/spreadsheets/d/1cz3nOxlh5xGCpVy3m70Iwk3fbntOwrbPGgxxlzeKBg4/edit#gid=2077216416),
including the intentionally added Electric self-immunity. The captured matrix,
color legend, and 18 changed interactions are retained in
`tools/dex_timing/probes/type_matchups_workbook.json`.

Both battles and this page use `data/types/type_matchups.asm`. The original
Foresight divider remains in place for Normal/Fighting versus Ghost. The new
Ground versus Ghost immunity remains independent of that exception.

## Focused Qualification (2026-10-11)

Native SameBoy checks passed on all six CGB revisions, 0 through E:

- All 18 selections, 72 directional moves, 32 input phases, and held directions per revision.
- 4,740,096 badge pixels compared to the original artwork and palettes.
- Full lower-panel comparisons, including W/R/I labels, empty sections, spacing, and clearing stale icons.
- All seven separate immunity lists and Steel's combined ten-icon R list.
- Clean corners, red outer margins, and continuous white top/bottom borders.
- 13,188 complete display frames matched valid layouts, with no mixed-color frames.
- No Mode 3 palette writes, unintended palette indexes, or IRQ register/bank restoration failures.
- Eight entry and eight exit phases without white flashes.
- 42 mode reentries across Modern, Legacy, Moves, and unlocked Unown.
- Locked/unlocked menus, both listing presentations, and all three Pokemon sort orders.
- 12 complete closes to the overworld and subsequent Dex reopenings.
- 24 post-return Selected Mon animations, cries, and description-page checks.
- 648 single-type battle calculations, 2,754 dual-type calculations, and four Foresight boundary cases.

Additional shared-arrow qualification on CGB E passed:

- 1,792 native phase/reset cases: all 256 counter values across seven WRAM banks, including wrap and BC/DE/bank preservation.
- 52 on/off and moved-cursor cases across Modern and Legacy, covering every Search row and all four selected-Pokemon footer positions.
- 3,328 observed idle frames; only the existing arrow glyph changes between phases, including both halves of shifted text.
- Moves search results, list navigation, Options/Sort navigation, and the unchanged text-entry keyboard box.

These are focused new-feature and return-path checks, not the full gameplay,
save/migration, 100-move battle, or full sampled-cry regression campaigns.
Manual review and real-hardware validation remain separate.

## Full Regression (2026-10-12)

Fresh batteries, symbol-matched native runners, and normal-input checkpoints
were generated for this exact ROM. Production commit `6d9fba86` and its ROM
were the paired baseline. Results are retained in
`build/dex-types-full-regression-20261012/full-regression.json`; the historical
Moves manifests supply fixture definitions only, not old protection claims.

Passed campaigns:

- Pokemon Dex: 4,479 cases across Modern/Legacy listings, all three sorts,
  modals, Search, detail pages, transitions, and return paths.
- Pokemon playback: 2,238 cold, paging, and warm cases covering all 373 species
  in each listing presentation. No animation or cry misses introduced.
- Unown: 136 scenarios, 2,212 form selections, and 126 draw units, including
  original-defect negative controls, red backdrop, and black panels.
- Moves Search: all 1,692 filters and the complete UI, keyboard, navigation,
  category-icon, footer, and surrounding-menu campaigns.
- Moves sort memory: exhaustive helper checks, menu/reentry checks, and normal
  Save/cold-reload checks, including legacy preference values and New Game.
- Persistence: 2,380 bit/index/register cases, four snapshots, 1,490 cold
  boots, 152 interrupted writes, 150 interrupted repairs, and five lifecycle
  cases. Separate legacy migration and 150 interrupted-migration cases pass.
- Acquisition: 12,276 helper contracts and all 59 positive/negative discovery
  sources, including declined learning, unsuccessful acquisitions, PC/daycare,
  contest receipt, special gifts, trades, and egg hatch.
- Battle discovery: 4,724 contracts, 400 semantic cases, eight supplemental
  Bide cases, and actual battle-input/normal-Save/cold-reload/Dex roundtrip.
- Struggle grant: 16 actual Dex-award script cases, 16 repeated awards, no
  immediate SRAM writes, and cold save/reload.
- Established battle animation correctness campaign: 100 moves, both sides,
  four phases, both links, for 1,600 cases. Duration comparison is not cleared
  (see below). Paired sampled cries: 960 cases; the same 32 known timing misses
  appear in both links, with no new playback differences.
- Surrounding gameplay: 22 scenarios; custom menus, menu input contracts, and
  24 repeat-battle/learning/loss transitions passed against production.
- Workbook battle chart: 648 single-type calls, 2,754 dual-type calls, and four
  identified-target/Foresight exceptions, rerun independently of visual tests.
- Shared blinking arrows: 1,792 native counter/reset cases, 52 visual and
  movement cases, and 3,328 idle frames passed again.

Normal save time changed by -0.019 ms; valid load by +0.042 ms; full-capacity
legacy migration by +0.140 ms. Among 256 paired Modern owner-reveal cases,
median entry delta was -0.022 ms and the largest increase was +0.783 ms.
Legacy complete-display maximum increase was +0.111 ms. The old
first-change metric can detect the listing highlight's blink before the page
appears; hardware window reveal was separately compared to avoid interpreting
that as a 100 ms page-entry regression. Full Selected display completion and
animation/cry correctness still passed. Listing idle work remained absent.

### Remaining Visual Defect

The Type page's Ice badge has black pixels at x114 through x119, y56 instead
of its existing cyan accent. This reproduced on repeated fresh entry, and
persisted across all 16 frames in an independent runner without Type raster
tracing. Evidence:

- `type-diagnostic/frame-00.png`: native screenshot.
- `type-diagnostic/summary.json`: exact pixel differences and ROM identity.
- `type-diagnostic/ice-tile.json`: VRAM bank 1, tile $02. Its first low-plane
  byte is $3f instead of $00, producing the six black pixels.
- `type-diagnostic/state.s0`: matching native failure checkpoint.

The linked original icon is correct. This is a code/runtime tile-data issue,
not missing artwork; the user does not need to create an asset. No game-source
fix was made as part of this regression-only request. The fresh six-model Type
visual campaign stops at this mismatch, so its prior focused pass must not be
used as fresh merge acceptance. Resolve this defect, then rerun that campaign.

### Battle Duration Concern

All 1,600 battle-animation cases completed without their functional assertions
failing. However, the separate elapsed-duration comparison is not unchanged:
581 of 800 paired cases differ by more than one frame. Median delta is +0.004
frames, but extrema span -16.140 to +31.000 frames. The largest increase is
Waterfall on the foe side at phase zero, approximately +519 ms. Water Pulse
also shows increases. These measurements describe animation execution duration,
not Dex entry time or input responsiveness.

The subsequent exhaustive investigation confirms the added shared LCD/VBlank
dispatch checks as the cause, rather than the type-chart changes or move scripts.
No fix has been applied to the user review ROM or production. Private diagnostic
links are only counterfactual controls and are not usable Type-page replacements.

### Exhaustive Animation Investigation (2026-10-12)

The retained campaign is `tools/dex_timing/all_battle_animations.py` with its
native observer in `tools/dex_timing/probes/battle_animation_sweep.c`. Complete
results, per-move comparisons, coverage assertions, and ROM identities are in
`build/dex-types-all-animations-20261012/report.json` and `configurations.json`.

Coverage:

- All 333 moves, from both sides, at four input delays spanning a display frame.
  Scripts with parameter branches additionally receive parameters 1, 2, and 3.
- All 28 auxiliary animation entries, including send-out, status, and capture.
- Production, the current prototype, and a private prototype retaining every
  other change but restoring both original shared interrupt paths.
- 10,968 retained native renderer calls, with no missing, duplicate, or unexpected
  cases. These execute the linked cartridge's real animation engine; they are
  not a simulation of the scripts or patched animation counters.
- A separate 1,332 normal battle-input runs: all 333 moves, both sides, on both
  production and prototype. Those runs use a harmless Splash opponent/control.

Each direct call starts at a naturally reached battle caller boundary with
interrupts enabled. If a delayed entry lands in an interrupt, the observer lets
that interrupt finish before making the call; it does not force IME, PPU state,
CPU speed, or display timing. Logical comparisons normalize script addresses and
hash every completed update's script position, delay, parameter, shadow OAM,
active objects, and background-effect state. Stack return, WRAM bank, ROM caller
bank, VBlank owner, and CPU-speed restoration are checked separately.

Results:

- All calls returned, with no restoration failures.
- Every move and auxiliary entry retained the same logical update count and
  state sequence as production. No new animation-engine failure was detected.
- 314 of 333 moves had at least one side/phase/parameter case differing by more
  than one physical frame. Across move cases, 1,331 were slower and 996 faster.
  This is a scheduling regression, not uniformly longer scripted waits.
- Extremes were -19.065 to +33.008 frames. The maximum is foe-side Waterfall,
  approximately +553 ms. The small median (+0.004 frames for move cases) does
  not negate the large individual regressions.
- Restoring both original interrupt paths made all 3,656 paired renderer cases
  exactly match production timing, as well as logical state and update counts.
  Restoring only LCD or only VBlank did not fully restore the focused controls.
  The diagnostic link still has the prototype's new type chart and cursor code.

Largest measured increases among selected water/raster effects, across both
sides and all tested phases (not a universal extra delay for every use):

| Move | Extra Frames | Extra Time |
| --- | ---: | ---: |
| Waterfall | 33.008 | 553 ms |
| Water Pulse | 28.003 | 469 ms |
| Hydro Pump | 24.005 | 402 ms |
| Water Gun | 20.000 | 335 ms |
| Whirlpool | 10.968 | 184 ms |
| Surf | 9.996 | 167 ms |
| Bubble | 4.006 | 67 ms |
| BubbleBeam | 3.003 | 50 ms |
| Heat Wave | 4.000 | 67 ms |
| Extrasensory | 3.994 | 67 ms |

Waterfall, Water Pulse, Whirlpool, Heat Wave, Extrasensory, and the auxiliary
InWhirlpool animation share `BattleBGEffect_Whirlpool`. It enables line-by-line
SCY updates. Hydro Pump, Water Gun, and BubbleBeam use the separate water-screen
effects; Surf uses its own screen effect. Non-water moves also differ, including
Superpower (up to +286 ms) and Psychic (up to +268 ms). The affected scope is
shared display scheduling, not the move's elemental type.

#### Confirmed Timing Mechanism

The permanent source warning and detailed guardrail are maintained in
[Shared Interrupt Timing Contract](battle_animation_interrupt_timing_contract.md).

The prototype adds `cp $ff / jp z, PokedexTypes_LCD` to `home/lcd.asm` after the
existing zero-pointer exit. An ordinary battle raster interrupt now spends an
extra 20 T-cycles rejecting the Type-page sentinel. The Type palette renderer
itself is not running during battle. Raster animations invoke this path many
times per display frame, so the check's cost is repeated.

`home/vblank.asm` also adds `ldh a, [hLCDCPointer] / cp $ff / jr nz` to
`VBlank_Normal`, costing 32 T-cycles on the ordinary path. Battle scripts use
`VBlank_CutsceneCGB`; the normal-path addition changes surrounding setup/cleanup
and starting alignment, rather than adding 32 cycles to every script frame.
The Type-only `ei` is not executed during these battles.

`BattleAnimDelayFrame` waits for the next VBlank after the update's work. Small
extra costs can push an update beyond that boundary, making the displayed state
persist for another whole frame. In the worst Waterfall sample both links
perform 243 logical updates, but production has 30 two-frame gaps between
updates and the prototype has 60. Thus the sequence is intact while its cadence
is visibly slower. Other starting alignments can make some cases shorter.

To reproduce without a diagnostic link, use Waterfall in a normal battle on
either side in the review prototype and production, with animations enabled.
Compare the full animation duration, not damage or the post-move text. Exact
delta depends on the starting phase. The retained native-input foe-side sample
reproduces the earlier approximately +31-frame/+519-ms result.

#### Native-Input Exceptions and Sand Tomb

The normal-input sweep has 632 completely clean paired cases out of 666. Every
exception identity is the same on both links; none is prototype-only:

- 19 paired cases do not activate the requested animation in this generic
  fixture: Counter, Mirror Coat, Mirror Move, Dream Eater, Nightmare, Snore,
  Sleep Talk, Attract, Sucker Punch, and foe Baton Pass. These need condition-
  specific damage, sleep, gender, calling, or switching setups. Their actual
  animation engines were exercised by the direct-call sweep on both sides.
- 13 paired cases play and return from the animation but do not return to the
  turn menu expected by the old runner: Guillotine/Horn Drill/Fissure knockouts,
  Roar/Whirlwind/Teleport battle endings, and player Baton Pass's switch menu.
- Two paired cases, player and foe Sand Tomb, expose an existing gameplay hang
  after the requested animation has returned. The observed PC is
  `BattleCommand_TrapTarget.next_trap_text` on both links. The `.Traps` table in
  `engine/battle/effect_commands.asm` has Bind, Wrap, Fire Spin, Clamp, and
  Whirlpool, but no Sand Tomb and no not-found terminator. Its unbounded scan
  consequently searches beyond the table for Sand Tomb's index.

Sand Tomb reproduction: in a wild battle, successfully hit a non-immune target
without a Substitute using Sand Tomb, applying the initial trapping effect.
The animation completes, then processing gets stuck before the trapping message
and next turn. Both sides reproduced against the actual linked production ROM.
This is not caused by the Type page, its chart, or the new interrupt checks.

The minimal Sand Tomb fix would add a four-byte move/text-pointer record using
the existing generic "was trapped!" text. Complexity is low; no artwork, SRAM,
or WRAM is needed. Test every trapping move from both sides and the existing
trap/Substitute/failure paths. A separately bounded table lookup would make
future missing entries safer, at a modest additional implementation/test cost.
Neither change was made during this investigation.
The user queued this as `BATTLE-MOVE-02` in the Dex backlog for a separate fix
in this branch, outside the current interrupt/palette work.

#### Fixture and Acceptance Limits

The auxiliary capture fixture was corrected to initialize the wobble count and
predetermined catch result, as the real capture caller does. Leaving the count
as unrelated move-menu scratch produced misleading duration/state differences.
All 96 capture cases were rerun; the original invalid records are retained in
`capture-uninitialized-fixture.json` for audit, not included in qualification.

This is exhaustive animation-entry and logical-state coverage on SameBoy CGB E,
not an assertion that every special move effect succeeds in a real battle, nor
pixel-by-pixel visual acceptance for every animation. Condition-specific native
fixtures and physical hardware remain separate coverage. The existing 100-move
native campaign also continues to pass its functional checks. The earlier Ice
badge defect remains unresolved and independent of these results.

#### Fix Direction and Cost

The detailed, assessment-only scope below supersedes the preliminary estimate.
Recommended: a Type-only frame owner, a dedicated branch inside the existing
Dex VBlank mode, and precomputed lower panels. Ordinary LCD and VBlank_Normal
instruction paths must revert to production without replacement owner checks.

No production promotion or user review-ROM replacement occurred. The private
original-interrupt diagnostic cannot display the Type page correctly and must
not be used as a proposed fix.

### Isolated Type Display Scope (2026-10-12)

Status: scoped, not implemented or qualified. The user approves considering
precomputed lower panels and wants to preserve room for approximately 80 future
moves, their animations/assets, and another 10 species. No new artwork is needed
for this design. Generated layout records would be build data derived from the
existing chart and tiles, not new graphical assets.

#### VBlank Mode 7 Is Available For Extension, Not Reassignment

The user's recollection is correct historically: slot 7 formerly pointed to
`VBlank_Normal` with an `unused` comment. Commit `bc899701fb` assigned it to
`VBlank_Pokedex` on 2026-08-04. Both current production and the Type prototype
use it as `VBLANK_POKEDEX`; removing cache warming did not free this slot.

Current live uses include:

- `engine/pokedex/pokedex.asm` and `pokedex_legacy.asm`: list/owner updates.
- `pokedex_3.asm:Pokedex_VBlankDispatch`: staged owner transitions, frontpic
  maps, Info/Description publication, and resident mini-sprite animation.
- `pokedex_search.asm` and the Moves Search state: Search publication.
- `pokedex_popover.asm`: popover publication.
- `pokedex_moves.asm`: Moves display synchronization through the same owner.

The existing handler saves the caller's bank, switches to the Dex dispatcher,
restores the bank, then enters `VBlank_Normal`. A Type-only branch inside
`VBlank_Pokedex` can instead call a dedicated bank-local Type service and return
without entering `VBlank_Normal`. The outer `VBlank` wrapper would still run
`GameTimer` once, preserve registers, and return normally. The ordinary Dex
branch must retain its existing jobs; it cannot be replaced wholesale.

The selector belongs *inside* mode 7, not before the shared dispatch table or
inside `VBlank_Normal`. A state check using `DEXSTATE_TYPES_UPDATE` is sufficient
in principle and avoids adding another owner tag. A straightforward version
adds about 32 T-cycles to other mode-7 frames only, around 0.004 ms in CGB double
speed. This is an estimate, not permission to assume other Dex modes are safe:
their publication deadlines and entry times must be compared during acceptance.
Ordinary/battle modes would not execute that selector at all.

Do not simply add a ninth handler. The current eight-entry table masks the low
three bits of `hVBlank`. `VBLANK_NEW_DEX_ENTRY` is $88: its bit 3 is an ownership
tag, not handler index 8. Widening the mask for a ninth entry would route that
existing owner incorrectly unless its encoding and every consumer were also
redesigned. Extending mode 7 avoids this unnecessary global change.

Mode 7 addresses VBlank ownership only. It does not by itself isolate the
mid-screen palette changes, which currently pass through the fixed LCD vector.

#### Recommended Display Design

1. Remove the prototype's Type gate and palette routine from `home/lcd.asm`,
   and its Type gate from `VBlank_Normal`. Preserve the timing-contract comments.
   Keep the shared vectors, ordinary instructions, and normal dispatch mask
   unchanged.
2. While Types is visible, use a dedicated ROMX frame loop that observes `rLY`
   and `rSTAT` and performs the existing accent writes in the required HBlank
   windows. Disable LCD STAT interrupts for this owner instead of invoking an
   inactive shared handler on every line. The badges, palettes, phased tile art,
   14-pixel row spacing, corners, W/R/I rules, and shared blinking arrow remain.
3. Use mode 7's Type service for atomic lower-map/palette-page/OAM publication
   and the necessary once-per-frame housekeeping. It must supply the frame
   counter, delay counters, input accumulation, RNG bookkeeping, sound update,
   and completion signal that this owner needs without serving unrelated map,
   tile, palette, or animation jobs. `GameTimer` remains in the unchanged outer
   wrapper; do not call it a second time. Use explicit bank preservation rather
   than the shared FarCall scratch inside an interrupt.
4. Preload the first top-row accents during VBlank, before its badge pixels at
   line 8. This removes the need for a separate line-7 palette event and gives
   sound/bookkeeping until the next event at line 21. All VRAM, palette, and OAM
   writes must still occur in their legal windows; only non-display bookkeeping
   may extend into the early visible lines.
5. Prepare the next lower panel in bounded work units between palette deadlines.
   Publish its maps, accent page, and corresponding cursor together on a later
   VBlank. Until then, retain the complete previous selection. A one-to-two-frame
   response, roughly 17-33 ms, is a design target, not a measured result.
6. Preserve `JoyTextDelay`/`GetJoypad`, accumulated press edges, held-direction
   repeat, wraparound, and the shared arrow's owner-update cadence. The ordinary
   Dex main loop must not call a blocking `DelayFrame` while the Type display
   still depends on main-thread palette polling. Return to it only after Types
   has relinquished the display.
7. Save/restore IE, STAT/LYC state, LCD owner, VBlank owner, map/OAM locks, pending
   jobs, and caller banks on every B/Select/transition path. Discard only this
   owner's stale STAT request, not unrelated pending interrupts. Mask the Type
   view before stopping its palette loop; clear pending work before handing its
   exclusive scratch to another Dex screen.

This is a medium-high-complexity display scheduling change with substantial
qualification cost. It is not just assigning a new VBlank number. Its advantage
is that the continuing timing obligations are localized to one menu instead of
the battle engine or every LCD interrupt.

#### Why Precompute The Lower Panel

The read-only native observer is `tools/dex_timing/type_isolation_scope.py`.
Measurements are retained in `build/dex-types-isolation-scope-20261012/costs.json`,
with the raw event stream and run log in that directory. It used real button
input on the unchanged review ROM, SHA-256
`69705d016d2cd9022bdd2fc3ae28d5884b78548012c430ec70cc8f784000803c`.

| Operation | Samples | Median | Maximum |
| --- | ---: | ---: | ---: |
| Build defensive matchup lists | 48 | 5.342 ms | 5.538 ms |
| Stage accent colors | 48 | 2.141 ms | 2.172 ms |
| Complete selection draw, including the two operations above | 48 | 10.824 ms | 13.263 ms |
| Stage the full visible maps, separate from drawing | 48 | 7.711 ms | 9.216 ms |
| Commit the lower maps | 48 | 0.209 ms | 0.209 ms |
| Update sound | 392 | 0.675 ms | 2.533 ms |
| Update joypad | 392 | 0.049 ms | 0.049 ms |
| Game timer | 392 | 0.032 ms | 0.061 ms |

These are wall-clock spans including interrupts, not isolated CPU instruction
budgets. Nested draw/build/color figures must not be added together. Cost
collection makes no pixel assertions and does not fix the known Ice defect or
prove visual correctness. Its sound samples cover the review context, not every music/SFX
path. Current drawing and map staging each exceed several palette intervals, so
moving those operations unchanged into a palette-polling loop is not viable.

Precompute 18 defensive lower layouts from the canonical
`data/types/type_matchups.asm`, including base immunities after the Foresight
divider. Reuse the existing tile identifiers and accent colors. Keep alphabetic
listing, overflow to another row, separate I where applicable, and Steel's
combined R exactly as in the accepted prototype. Add a build dependency so chart
edits regenerate records; never maintain a second hand-written chart.

Two simple storage formats:

| Format | Per Type | All 18 Types | Tradeoff |
| --- | ---: | ---: | --- |
| Packed visible rows: 20 x 5 tiles, matching attributes, five rows of four two-byte accents | 240 bytes | 4,320 bytes | Smaller; bounded copies must expand map rows to the 32-tile hardware stride |
| Hardware-stride rows: 32 x 5 tiles, attributes, the same accents | 360 bytes | 6,480 bytes | About 2.1 KB more; simpler contiguous map copies |

A small index adds roughly 36-54 bytes depending on bank placement. Prefer the
packed form if bounded-copy timing qualifies; use the padded form if it makes
the schedule materially more reliable. Do not introduce complicated compression
solely to save this small difference. If tighter storage becomes necessary,
redundant fixed border/blank cells could later be omitted without changing art.

#### Space And Engineering Cost

| Resource | Scoped Cost |
| --- | --- |
| ROMX layout data | 4,320-6,480 bytes, plus a small index |
| ROMX display/copy code | Allow approximately 0.5-1.2 KB before removing superseded runtime routines |
| Overall added ROMX planning allowance | Approximately 4-8 KB; final linked delta must be measured |
| ROM0 | Removing the current shared Type hooks recovers exactly 70 bytes; allow roughly 20-40 bytes for a mode-7-only selector/bridge, for an estimated net recovery of 30-50 bytes |
| Working state | Approximately 8-24 bytes within existing Type-exclusive scratch; no new permanent allocation expected |
| SRAM / save layout | No changes |
| HRAM / new artwork | No allocation or assets required |

The current linked map reports 707,914 free ROMX bytes across its 186 mapped
banks, about 691 KiB. The 4-8 KB allowance consumes roughly 0.6-1.2% of that
reported free space and does not require enlarging the 4 MiB ROM. This is not a
budget for the future 80 moves/10 species: their actual compressed animation,
graphics, audio, and code sizes still need separate measurement.

Bank placement matters more than that aggregate figure: the current Type code
is in bank 1, which has only 122 bytes left after its other allocations. Put the
new records and scheduling helpers in appropriately sized ROMX sections, moving
the Type section if necessary; do not force them into bank 1 or ROM0. Retain
bank-local palette writers and explicitly budget any cross-bank bounded copies.

Implementation should proceed in three reviewable stages: prove the isolated
palette/audio schedule, add generated panels and complete owner/input handling,
then run qualification. The testing stage is substantial because the defect
changes physical battle timing without changing animation state counts.

#### Feasibility Gate And Risks

The proposed safe bookkeeping window runs approximately from line 144 through
the following frame's line 21, about 3.37 ms. The measured 2.533 ms sound maximum
plus the 0.209 ms map commit and other short jobs makes this worth prototyping,
but margins are not established by those samples. The fixed outer VBlank wrapper,
bank switches, OAM transfer, RNG/delay handling, palette preload, and worst-case
music/SFX decoding must all fit before the next palette deadline. Sound must
still run exactly once per physical frame. Do not solve a miss by skipping sound
or input frames. All music reachable when opening the Dex, long decoding paths,
and repeated menu sounds require targeted profiling before accepting this route.

Other risks are illegal/missed HBlank writes, torn lower maps, palette/cursor
page disagreement, lost input while preparing records, blink/repeat cadence
changes, stale pending interrupts, and incomplete restoration on owner changes
or software reset. All six supported CGB models and CPU-speed assumptions need
qualification. The existing Ice upload defect remains a separate code fix and
must be resolved before visual acceptance; this scheduling proposal does not
claim to fix it automatically. Sand Tomb remains the separately queued story.

#### Alternatives

- A full ordinary LCD handler resident in unbanked RAM could preserve its exact
  instruction timing and substitute a Type-only entry while this menu is active.
  The ordinary body is 22 bytes, however, with only 13 free WRAM0 bytes and no
  free HRAM. It requires reclaiming permanent storage, ROM-to-RAM initialization,
  and auditing every clearing/reset path. The 24-byte "Unused Map Buffer" is
  actually the live player/enemy Wish-name storage, not free memory. Relocating
  it introduces battle and map-memory risks unrelated to this UI. This is a
  higher-blast-radius fallback if the private polling/audio schedule cannot be
  bounded, not the first recommendation.
- A RAM trampoline alone does not help: an additional ordinary `jp` still adds
  16 T-cycles to each active interrupt. Likewise, merely moving the current
  Type routine to another file or mode while retaining a shared LCD owner check
  does not remove the diagnosed regression.
- A cycle-neutral shared-handler redesign may be possible, but tightly couples
  this menu to all raster effects and must preserve every ordinary path, not just
  the common case. It is more brittle than keeping the Type work private.
- Static-palette/extra-OAM designs would require revisiting the accepted gray
  background, palette allocation, and lower-row sprite limits. They are a visual
  redesign, not an equivalent isolated implementation using the current layout.
- Do not compensate by adjusting individual battle waits. The regression is
  phase-dependent and changes hundreds of moves in both directions.

#### Acceptance Before Promotion

1. Compare ordinary LCD, VBlank_Normal, and common vector/table instructions and
   cycle paths against production. Confirm the new selector runs only in mode 7.
2. Assert generated panels against all 324 attack/defense cells of the canonical
   chart, including Foresight-separated base immunities, Electric self-immunity,
   Steel's combined R, overflow placement, alphabetic order, and empty sections.
3. For all 18 selections on all six CGB models, verify palette-write windows,
   linked tile data, corners, badges, labels, cursor phases, map atomicity, and
   repeated/held/rapid direction changes. Capture screenshots and deadline traces.
4. Exercise B/Select/re-entry, every Dex return path, pending-publication exits,
   software reset, and repeated cross-mode transitions. Check bank/register,
   interrupt owner/mask, lock, scratch, frame-counter, input, and sound restoration.
5. Qualify the worst-case reachable music and menu SFX, with no missed accent
   windows or duplicate/skipped once-per-frame work. Measure Type response times
   and other Dex modes' entry/publication times against the unchanged prototype
   and production.
6. Rerun the exhaustive 333-move/two-side/phase/parameter and 28-auxiliary-entry
   animation oracle against production. Require physical timing agreement as
   well as the existing logical-state/restoration checks. Retain known fixture
   limitations and the separately queued Sand Tomb failure explicitly.
7. Run the full Dex, Moves/search/persistence/discovery, PC/daycare, custom-menu,
   sampled-cry, surrounding-gameplay, and existing battle regression campaigns.

No game behavior, type-chart value, artwork, save, or review ROM was changed by
this assessment. Only the native cost observer and this scope documentation were
added. The linked delta, deadline bounds, and private owner behavior remain to be
established by the next implementation prototype.

### Test Caveats

The current linked host suite passed 85 of 86 checks. Its existing Info handoff
LY64 assertion fails identically on production and the prototype. The older
`tools.test_dex_timing` suite has the same six failure, sixteen error, and 103
skip identities among 187 checks on both links. Two failure messages have
expected cycle-count differences from shared cursor calls and VBlank dispatch;
current scheduler/bounds and native playback campaigns pass. These retained
tests are not represented as green or skipped silently.

Two test expectations were updated: blinking Moves Sort arrows may be visible
or hidden, and Type Matchups is now entered/exited rather than treated as a
placeholder. Both updated campaigns passed. A popup-readiness setup dependency
was rerun after its custom-menu fixtures existed. Production ROM/symbol/map,
the tested ROM, and its natural review save retain their original hashes.
Physical Game Boy hardware validation remains outstanding.

The retained `type_full_regression` module runs preparation and each campaign
phase independently. Use a fresh private output for `prepare`, then `setup`,
`dex`, `moves`, `persistence`, `discovery`, `gameplay`, `battle-discovery`,
`timing`, `readiness`, `host`, `historical-host`, `gift`, `chart`, and `report`.
Run `discovery` before `gameplay` recreates the 100-move battle fixtures;
`readiness` follows the custom-menu setup. Run the focused Type/arrow modules
separately against the source prototype. `diagnose-types` retains independent
failure evidence without modifying the ROM.

ROM usage increases by 2,642 bytes, including 70 bytes in ROM0. The shared-arrow
revision adds 295 bytes over the immunity/corner review ROM. There are no
new WRAM, HRAM, SRAM allocations or save-format changes. Temporary data reuses
the Dex's existing exclusive scratch areas; resident Unown/font/border tiles
are preserved. Production source graphics are unchanged.

## Reproduction

Use a fresh private output directory based on the same production commit:

```sh
python3 tools/build_dex_types_prototype.py prepare --output build/dex-types-cursors-review
python3 tools/build_dex_types_prototype.py build --output build/dex-types-cursors-review
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_arrow_cursors --output build/dex-types-cursors-review
PYTHONPATH=tools:. python3 -m tools.dex_timing.type_matchups --output build/dex-types-cursors-review --all-models
```

The builder requires the retained all-Unown rollback review save. Tests use
the local SameBoy source and boot ROM. UI checks use ordinary inputs on copied
batteries; the separate battle units explicitly set only their isolated test
fixtures before executing the actual ROM routine.
