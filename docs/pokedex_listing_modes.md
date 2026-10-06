# Legacy And Modern Dex Listings

2026-10-05. The Legacy Listing implementation and border corrections have been
visually accepted and committed. The private Modes menu follow-up described
below awaits visual acceptance; its builds leave production ROM outputs and
the installed SameBoy battery unchanged.

## Scope And Controls

- Modern Dex Mode keeps the existing animated three-column grid.
- Legacy Dex Mode uses seven text rows at 16px spacing, no number column,
  a colored static frontpic, Seen/Own totals, dark gray background, green corner
  cursor, colored caught marks and the existing scrollbar.
- The single-tile arrow is the top navigation marker; the bottom uses its Y flip.
- Up/Down selects one entry and wraps from first to last or last to first, like
  Modern. Left/Right keeps the classic bounded seven-row page jumps. Search
  results retain their existing bounded navigation.
- SELECT opens the presentation/mode menu **only from the main Listing**.
  SELECT and START never open it from Description, Info or Moves. Search-result
  Selected pages have the same restriction. Area retains its vanilla controls.
- Modern/Legacy selection preserves the absolute selected entry. Temporary
  New/Old/ABC ordering remains independent of presentation. The Modes menu
  prototype removes these exposed ordering choices while preserving existing
  save/order compatibility. The future Sort interface is separate work.
- START still opens existing Search. The authored footer now correctly pairs
  SELECT with MODE and START with OPTION; the future Sort/Search popup is not
  implemented in this change.
- Both presentations enter exactly the same Selected owner, tabs, internal
  paging, animation timeline, producer and cry code. Visibility remains based
  on Seen/Caught: unseen names are `-----` and cannot be selected; caught-only
  lower panels stay blank for seen-but-uncaught species.

## Presentation And Saved State

`wCurDexMode` remains the ordering enum. `wPokedexListingPresentation` is a
separate session byte: 0 Modern, 1 Legacy. It occupies spare capacity in the
existing WRAM0 union without changing the section's size or existing offsets.

`wLastDexPresentation` replaces one already-saved padding byte immediately after
`wLastDexMode`. Save record sizes, checksums and every following field's offset
are unchanged. Closing the Dex records the preference; a normal game save
persists it. Invalid presentation values fall back to Modern. The supplied
private test battery defaults to Legacy and has all 373 species seen/caught.
It is not a replacement of the user's live save.

The main Listing dispatcher owns mode entry and shared A/B/START checks. Only
its D-pad/render path branches by presentation. Selected has no mode-entry
action. Mode entry cancels idle preparation before borrowing its scratch for
the menu cursor coordinates. Cancellation/reselection then rebuilds preparation
normally, preventing stale warm payload reuse.

Changing to Legacy uses the shared linear-return normalizer. Changing back to
Modern invalidates grid row tags and aligns a viewport around the same entry.
Legacy B-return skips the Modern-only Info panel preservation/grid cache repair;
it retains the shared cry cancellation, footprint restoration and owner reveal.
Every Legacy Listing initialization restores navigation height seven, including
the return from Search's four-row results.

Legacy's local D-pad wrapper first tries the shared bounded controller. Only a
blocked Up/Down at the main Listing boundary wraps. Down clears both scroll and
cursor; Up sets the last visible page and its final valid row. The arithmetic
uses the full 16-bit list length, including the 255/256 boundary. Empty and
one-entry lists stay put. Left/Right and Search are unchanged. Wraps use the
same coherent portrait/map/OAM transaction as ordinary scrolling.

## Rendering And Publication

Implementation lives in `engine/pokedex/pokedex_legacy.asm`, a dedicated bank
`$ba`. Names are read directly from the permanent 16-bit species indices in
`wPokedexOrder`, not from retained transient IDs. Each row is checked against
the current end before reading. The list remains a Window tilemap; the portrait
and counters remain on BG. Neither the font nor the names require new OAM.

Cold initialization and Selected B-return reuse the shared palette staging,
backing-map ownership and Listing reveal transaction. For Legacy scrolling:

1. Cancel idle animation preparation; stage the new frontpic and palette.
2. Freeze automatic shadow-OAM publication and build all seven text rows,
   caught marks, cursor corners and thumb. Convert the Window maps to the
   existing padded owner buffers in WRAM bank 3.
3. Begin the 49-tile portrait upload after its old pixels have passed, in the
   admitted scanline 64-77 range. Commit its palette after that upload.
4. Protect the following VBlank. Publish both padded Window maps with general
   DMA and transfer shadow OAM before the next visible frame. Restore bank
   registers and release interrupts/OAM ownership.
5. Upload the hidden prepared footprint and set its resident tag **before**
   restarting idle preparation. No Selected animation or cry is playing here.

This keeps the old selection intact until one complete new selection appears.
The hidden footprint may finish after the visible change; it is not allowed to
overwrite a warm animation payload on subsequent Selected entry. This ordering
is important because footprint staging and animation work share WRAM0 scratch.

The generic whole-map stack copy remains useful for cold setup. It is not the
scroll reveal mechanism: its two maps can span a display interval, leaving a
new portrait with the old cursor for one frame. The dedicated protected Window
publication avoids that mismatch without allocating another map buffer.

Idle animation cache warming is deliberately retained in both presentations.
Its later removal is tracked as `DEX-PERF-03` in the
[live backlog](pokedex_selected_bug_backlog.md). The removed minisprite scrolling
lookahead is a different feature and is not reintroduced here.

## Assets, VRAM And Palettes

The user-authored `gfx/pokedex/pokedex.png` is now 128x40. Its original 64 cells
are unchanged. The appended row begins with junction, cap, straight divider and
arrow, in that order. `pokedex_core.2bpp` is a generated 64-cell prefix used by
the shared compressed UI load, so expansion cannot overwrite Description/page
graphics. `PokedexLegacyGFX` includes only the four appended cells directly from
the converted shared sheet. No second source image or duplicate compressed
Legacy payload remains; the standalone arrow PNG was removed after confirming
its linked bytes are identical to the consolidated arrow.

The three border cells are loaded once at Dex startup into BG bank 0
`vTiles2 $62-$64`, formerly unused DMG-footprint slots in the normal CGB Dex.
The CGB footprint remains resident in bank 1. The arrow stays at `$7e`, and
`$7f` remains the space tile. Neither page badges nor font/animation cells are
borrowed. Existing portrait, cursor, caught-ball and scrollbar graphics are
reused; no additional sprite graphics are required.

The BG tile at column 8 starts at screen x=59 with SCX=5. Each divider therefore
has white pixels at local columns 1 and 3: portrait edge x=60, shell gap x=61,
Listing edge x=62 and interior x=63. Its junction closes the portrait and
counters separately across lines 66-69, without a vertical connection. The
bottom cap reuses the top cap with BG Y-flip; the attribute is set only for
Legacy at map cell (8,16). The Window still begins at x=64, keeping name
positions unchanged.

Caught-ball OBJ X is 71 (one pixel left). Left cursor OBJ X is 72 (one pixel
right); right cursor X remains 151. Top Y is 24 + 16*row (one pixel down), and
bottom Y remains 39 + 16*row. These are independent corner offsets, not an
overall cursor translation.

| Target | Legacy use |
| --- | --- |
| BG0 palette | Dark gray text/shell, white lines and red border |
| BG1 palette | Selected species' colored frontpic |
| BG2-7 palettes | Not used by Legacy list icons; shared Selected ownership remains unchanged |
| OBJ0 palette | Green corner cursor |
| OBJ1 palette | Caught balls |
| OBJ5 palette | Scrollbar thumb |
| OAM | Four corners, up to seven caught balls, one thumb: at most 12 entries |

The seven rows do not create OAM scanline pressure: caught marks are separated
by 16px and corner sprites occupy the active row's boundaries. Modern's grid
icon VBlank animation is disabled while Legacy owns Listing. Selected restores
its normal type-badge, evolution-mini and tab palette/OAM ownership.

## Modes Menu Prototype

The Modes menu reuses the existing font, arrow cursor, title caps, panel borders
and palette. Five rows occupy tile rows 3, 5, 7, 9 and 11, starting at column 3;
the arrow occupies column 2. Both description lines use 18 cells at column 1,
rows 14 and 16. Tile `$31` fills the surrounding red shell, correcting the
previous controller's inherited gray area above the panel. No artwork changes
are needed.

| Row | Before Unown unlock | After Unown unlock |
| --- | --- | --- |
| 1 | Modern Dex Mode | Modern Dex Mode |
| 2 | Legacy Dex Mode | Legacy Dex Mode |
| 3 | Moves Dex Mode | Unown Dex Mode |
| 4 | Type Matchups | Moves Dex Mode |
| 5 | Blank, not selectable | Type Matchups |

`PokedexListing_GetModeID` maps visible row positions through separate ROMX
tables to stable IDs: Modern 0, Legacy 1, Unown 2, Moves 3, Types 4. Actions and
description lookup use these IDs, not shifted row positions. The cursor remains
bounded and uses four or five rows according to the existing unlock flag.
The shared 12-byte cursor-coordinate table is copied into the already-owned
WRAM0 scratch; no new scratch allocation is made.

Unown still requires `ENGINE_UNOWN_DEX`, backed by
`wStatusFlags:STATUSFLAGS_UNOWN_DEX_F` and set by the existing Ruins of Alph
Research Center quest script. This change does not modify the quest or Unown
viewer. Moves and Type Matchups can be highlighted and show their descriptions,
but A is deliberately inactive until those screens are implemented. B or SELECT
returns to the same Listing. Modern/Legacy preserve the selected entry and
existing internal ordering; no placeholder action writes an ordering or
presentation field. Entry remains prohibited from Selected pages.

| Mode | First description line | Second description line |
| --- | --- | --- |
| Modern | `Displays <PKMN> in a` | `visual grid.` |
| Legacy | `Displays <PKMN> in the` | `classic text list.` |
| Unown | `Displays all Unown` | `forms caught.` |
| Moves | `Move descriptions` | `and stats.` |
| Types | `<PKMN> Type weaknesses` | `and resistances.` |

The source uses `<PK><MN>` to place the two special glyph cells directly.
Legacy uses all 18 cells on both lines; Types uses all 18 on the first line.
Native map checks include the panel's right border to detect overflow.

The original private build was `build/dex-modes-prototype-final/`, with exported
`pokecrystal-dex-modes.gbc`, matching symbols/map, and all-caught test batteries.
`pokecrystal-dex-modes.sav` unlocks Unown and contains all 26 forms;
`pokecrystal-dex-modes-locked.sav` clears only the unlock flag in the equivalent
test fixture. An identical `pokecrystal-dex-modes-locked.gbc` and matching symbols
are exported beside that battery for automatic filename-based save loading.
These are private copies, not edits of the installed save. Both ROM variants
have SHA-256 `a382fb6ff297a5fc089f7faff05190f0593dff576914fe18a694e53043afd7f8`.

That first Modes link cost **+49 ROMX bytes** over the accepted border build.
Its dedicated bank `$ba` section was 1,656 bytes, leaving 14,728 bytes.
ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM, palettes and OAM counts are unchanged.
Total linked ROM use is 2,335,403 bytes; the 4 MiB cartridge has 1,858,901 bytes
free, including unused banks.

Qualification uses `tools/dex_timing/dex_modes.py` for 54 real-input cases:
every selectable row in both unlock states, both presentations and all three
retained internal orderings. It checks exact labels/descriptions, cursor
placement and boundaries, inactive-A behavior, cancellation, Unown roundtrips,
selection/order preservation and subsequent playback. Screenshots are captured
for every row in both unlock states/presentations.

Its **8,516 matching-link native checks passed**, with zero animation deadline
or uninterrupted sampled-cry completion failures. Those checks validated settled
menu screens, not every display frame during mode transitions; the visual bugs
reported afterward exposed this coverage gap:

- 6,555 Legacy standard playback/tab/stress cases across all 373 species.
- 1,119 Modern all-species cold/warm/internal-paging playback cases.
- 373 Listing/Selected cases, including all 492 Info-page B-returns.
- 399 frame-by-frame navigation cases with zero mixed-selection frames.
- 54 new Modes cases, ten preference/warmed-menu cancellation cases and six
  Search/Unown roundtrips.

The 72 focused host tests pass. Broader historical host-test limitations remain
as documented in the original qualification; this is not an all-host-tests claim
or physical-hardware certification. Matching summaries are under
`regression-{legacy,modern}/`, `listing-qualification/`, `navigation/` and
`modes-qualification/`, plus `mode-tests.json` and `menu-tests.json` in the
private build directory.

The existing private build/prepare/navigation/playback commands below can use
`build/dex-modes-prototype-final` as their output directory. Then run:

```sh
PYTHONPATH=tools python3 -B -m tools.dex_timing.dex_modes --output build/dex-modes-prototype-final --jobs 10
DEX_LEGACY_BUILD=build/dex-modes-prototype-final PYTHONPATH=tools python3 -B -m unittest test_legacy_listing test_dex_cold_listing test_dex_target_regression test_new_dex_entry test_dex_performance test_pokedex_area_assets
```

Manual review remains the acceptance gate for the new menu's appearance. Check
both unlock layouts, all descriptions, Modern/Legacy selection preservation,
Unown entry/return and inactive-A behavior on the two future-mode placeholders.

## Modes Transition Follow-Up

2026-10-05: four user-reported issues were reproduced in the original Modes
prototype, then corrected privately. Production ROM outputs and the installed
SameBoy save remain unchanged. The updated prototype is
`build/dex-modes-transitions-final/pokecrystal-dex-modes.gbc`, SHA-256
`d53736afb6a6098f6c5b0ed228c9e5ba5efbd9d1cb4e28f169c9fed60a55a34b`.
Matching symbols, map, all-caught/unlocked battery and equivalent locked variant
are exported beside it. Visual acceptance is still required before promotion.

### Reproductions And Causes

1. **Listing to Modes:** open either Listing and press SELECT. The original
   frontpic shifts horizontally, grid/cursor colors flash green, and partial
   menu rows appear. `Pokedex_BlackOutBG` zeros only the *source* BG palettes,
   without copying them to the hardware targets or requesting their publication.
   OBJ colors remain live too. SELECT changes SCX from 5 to 0 and hides the
   Listing Window before any completed hide. The menu's four-frame tilemap and
   attrmap uploads consequently replace an exposed screen piecemeal.
2. **Modes to Listing:** select Modern/Legacy with A, or cancel with B/SELECT.
   The ordinary cold Listing initializer calls `ClearPalettes`, producing a
   full white frame. Legacy to Modern may additionally miss its grid row tags
   and enter `Pokedex_PrimeGridCache`, which disables/re-enables the LCD. Neither
   operation is appropriate for an already-open Dex owner transition.
3. **Modes/Unown handoffs:** highlight unlocked Unown and press A; leave its
   viewer with A or B. These routes used the same ineffective blackout. Unown
   also replaced shared portrait tiles while outgoing menu/map palettes were
   visible, and its return exposed the new menu map/attributes in several steps.
   This is publication order, not a shortage of tiles or a new cry failure.
4. **Wrong return row:** after leaving Unown, the Modes initializer always
   chose `wPokedexListingPresentation`, forcing Modern or Legacy. It did not
   distinguish first entry from Unown return.

The baseline frame captures reproduce the artifacts from both presentations.
All 16 baseline input-phase cases fail the new transition audit, including full
white frames on Listing returns and an LCD-off frame on Legacy-to-Modern cache
rebuilding. Evidence is under the original build's `transition-baseline/`.

### Scoped Fix And Ownership

`PokedexListing_BeginMenuTransition` is a Dex-local hide barrier:

1. Stop the grid VBlank owner and automatic BG-map/palette work. Freeze shadow
   OAM publication before clearing it.
2. Preserve `wBGPals1`/`wOBPals1`, but fill all 16 BG/OBJ hardware-target palettes
   in `wBGPals2`/`wOBPals2` with black. Request publication and release the empty
   OAM for that VBlank.
3. Wait for that completed VBlank before resetting SCX/SCY/WY and hiding Window.
   Hold OAM again while building the incoming screen. Shared tiles, maps and
   attributes may now change without displaying any partial work.
4. Modes and Unown finish their existing map/attrmap uploads and final palette
   conversion, then `PokedexListing_RevealMenu` waits for the finished reveal.
   Modes places its initial BG arrow locally before uploading its map; it does
   not dereference a ROMX coordinate table through another bank.

Two new enum values reuse `wPokedexSelectedState`; no byte is allocated:

- `DEXSELECT_STATE_MENU_RETURN` routes both Listing initializers around the
  white cold-start clear. They still rebuild the correct frontpic, Window and
  palette targets, then reuse the staged owner-map/Listing commit. Grid cache
  misses use the existing LCD-on repair path, not cold LCD-off priming.
- `DEXSELECT_STATE_UNOWN_RETURN` is a short-lived return reason. Modes chooses
  row 2, stages its Unown description and arrow, then clears this state. First
  entry still highlights the current Modern/Legacy presentation. Returning
  through Unown does not change that preference or the selected species.

The menu-to-Listing reveal restores *all* BG/OBJ palettes, since all were masked.
It uses the existing bulk `ForceUpdateCGBPals` in the protected early-VBlank
owner commit. An initial trial used the guarded partial palette copier; the
frame audit detected one frame of incomplete top Legacy cursor corners because
OAM transfer started too late. The bulk copy removes that late-OAM reveal.
Ordinary Selected-to-Listing returns retain their existing guarded partial
palette path. Animation scheduling, cry playback, scrolling and Search are not
redesigned by this change.

### Cost And Qualification

The correction adds **161 ROMX bytes** over the first Modes prototype, or
**210 ROMX bytes** over the accepted Legacy border build. Bank `$ba` now uses
1,776 bytes, leaving 14,608. ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM, palettes and
OAM allocations do not grow. Linked totals:

| Resource | Used | Free |
| --- | ---: | ---: |
| ROM0 | 15,861 | 523 |
| ROMX, occupied banks | 2,319,703 | 727,721 |
| WRAM0 | 4,083 | 13 |
| WRAMX | 23,944 | 4,728 |
| HRAM | 127 | 0 |

Total linked cartridge use is 2,335,564 bytes; 1,858,740 bytes remain across
the 4 MiB cartridge, including unused banks.

The new `tools/dex_timing/mode_transitions.py` boots a private battery and uses
only real controls. It records every visible frame for six routes: Listing to
Modes, Modes cancellation, presentation switch, Modes to Unown, Unown to Modes,
and that Modes screen back to Listing. After the roundtrip it verifies the
species' complete animation timeline, actual picture/map bytes and sampled-cry
completion. Eight sub-frame button phases cover both presentations at twelve
species/index positions, including 255/256, the list end, Seviper and the known
heavy frontpics. Only pixels which actually animate/blink on the two settled
owners are excluded from old/new matching. Every other pixel must show the
intact source, full black mask or intact destination, with no reversed reveal,
LCD shutdown or white flash. Temporary raw frames are removed after PNG export.

Rebuild and reproduce on fresh matching states:

```sh
python3 -B -m tools.dex_timing.legacy_listing build --output build/dex-modes-transitions-final --jobs 10
python3 -B -m tools.dex_timing.legacy_listing prepare --output build/dex-modes-transitions-final --jobs 10
PYTHONPATH=tools python3 -B -m tools.dex_timing.dex_modes --output build/dex-modes-transitions-final --jobs 8
PYTHONPATH=tools python3 -B -m tools.dex_timing.mode_transitions --output build/dex-modes-transitions-final --indices 0,255,256,296,315,333,337,339,341,351,360,372 --phases 8 --jobs 8
DEX_LEGACY_BUILD=build/dex-modes-transitions-final PYTHONPATH=tools python3 -B -m unittest test_legacy_listing test_dex_cold_listing test_dex_target_regression test_new_dex_entry test_dex_performance test_pokedex_area_assets
```

The linked host contracts now additionally check that hiding preserves source
palettes, masks all BG/OBJ targets, freezes OAM during preparation, restores
the WRAM bank, and places the first menu arrow before publication.

### Final Results And Timing

All **8,736 matching-link native cases pass**, with zero animation deadline or
uninterrupted sampled-cry completion failures:

- 6,555 Legacy all-species playback/tab/stress cases and 1,119 Modern
  all-species cold/warm/internal-paging cases.
- 373 Listing/Selected cases, including all 492 Info-page B-returns; 399
  frame-by-frame Legacy navigation cases.
- 54 locked/unlocked Modes cases, ten preference/warmed-menu cases and six
  Search/Unown roundtrips.
- 192 new input-phase/species transition cases, twelve A-return/SELECT-cancel
  variants, eight post-Info and eight post-Moves transition histories. These
  cover **1,320 frame-audited transitions**, plus 220 post-menu complete
  animation/cry replays. No mixed frame, white flash or LCD-off frame occurs.

All 74 focused host tests pass. These are SameBoy and linked host results, not
physical-hardware certification. Only the final directory's matching summaries
are acceptance evidence; the intermediate palette/OAM trial and a superseded
Modern test-navigation fixture remain separate historical diagnostics.

The transition timing below is the median of eight sub-frame input phases for
Chikorita, measured from button assertion to the completed display-frame
boundary. First response is the first changed frame (now the black hide), not
the input handler's acceptance; Complete is the first intact destination frame.
Fractions are elapsed physical display intervals, not producer calls. The
existing baseline may respond first with an artifact, so its First value is
not proof of a clean transition.

| Route | Before First, intervals / ms | After First | Before Complete | After Complete |
| --- | ---: | ---: | ---: | ---: |
| Modern Listing to Modes | 2.52 / 42.3 | 2.53 / 42.4 | 11.52 / 192.9 | 13.53 / 226.6 |
| Legacy Listing to Modes | 2.52 / 42.1 | 2.53 / 42.3 | 11.52 / 192.8 | 13.53 / 226.5 |
| Modes cancel to either Listing | 3.91 / 65.5 | 2.91 / 48.7 | 13.91 / 232.9 | 8.91 / 149.1 |
| Modern to Legacy selection | 3.89 / 65.2 | 2.92 / 48.9 | 13.89 / 232.6 | 8.92 / 149.3 |
| Legacy to Modern selection | 3.92 / 65.7 | 2.92 / 48.9 | 16.15 / 270.4 | 10.92 / 182.9 |
| Modes to Unown, from Modern | 3.92 / 65.7 | 2.92 / 48.9 | 19.92 / 333.6 | 20.92 / 350.3 |
| Unown to Modes, from Modern | 5.91 / 98.9 | 2.91 / 48.7 | 11.91 / 199.4 | 14.91 / 249.6 |
| Unown's Modes to Modern Listing | 3.91 / 65.5 | 2.91 / 48.6 | 13.91 / 232.9 | 8.91 / 149.1 |

The corresponding Legacy-origin Unown entry completes in 20.92 intervals /
350.3ms; return to Modes in 14.87 / 248.9ms; cancel back to Listing in
8.91 / 149.1ms. Species/cache rebuilding can vary Listing completion time;
the twelve-position transition sweep remains clean throughout. Exact per-case
cycles and rendered frames are retained in `mode-transitions/summary.json` and
its PNG subdirectories. `return-button-variants/`, `after-info/` and
`after-moves/` contain the additional histories.

The hide adds about two display intervals to complete Modes entry, one to
Unown entry and three to the Unown-to-Modes rebuild. Listing returns complete
about five intervals earlier, with an earlier first visible response too.
This is the explicit tradeoff for withholding unfinished menu/map work.
Ordinary Selected-to-Listing returns retain their previous reveal policy;
their all-Info-page control-return median is unchanged at 5.994 intervals /
100.37ms from the original Modes prototype.

Manual acceptance should check SELECT entry from both Listings; B/SELECT
cancellation; same-mode A reselection; Modern/Legacy switching; Unown entry
and A/B exit; the restored Unown row/description; and the hidden locked row.
The two supplied private batteries allow both unlock layouts without editing
the installed battery.

## Exact Linked Legacy Cost

Against the unchanged production map:

| Resource | Change | Prototype used / free |
| --- | --- | --- |
| ROM0 | 0 | 15,861 / 523 bytes |
| ROMX | +1,569 bytes net | 2,319,493 / 727,931 bytes within 186 occupied banks |
| WRAM0 | No aggregate growth; one session byte in union capacity | 4,083 / 13 bytes |
| WRAMX | 0; reuse existing owner map overlay | 23,944 / 4,728 bytes |
| SRAM | No size growth; one saved padding byte assigned | 49,994 / 15,542 bytes |
| HRAM | 0 | 127 / 0 bytes |
| VRAM | Three unused cells inside the existing UI load plus the free arrow cell assigned | 64 bytes of resident artwork; no font/animation displacement |

The new bank's section is 1,607 bytes, leaving 14,777 bytes in `$ba`; replacing
the old option controller yields a smaller net ROMX increase. Cartridge size
stays 4 MiB. Total linked ROM use is 2,335,354 bytes (55.7%); 1,858,950 bytes
(about 1.77 MiB, 44.3%) remain across the cartridge, including unused banks.
The map's occupied-bank free count is not the whole cartridge's free space.

## Qualification And Reproduction

### Border And OAM Follow-Up

The current prototype and matching all-caught test save are in
`build/dex-legacy-borders-prototype/`. ROM SHA-256:
`d4a295b26913e26dd67e26351ca5ff22a9cde16a718d48744bfdc6508241b83d`.
The border/OAM correction adds 70 ROMX bytes over the wraparound prototype:
48 bytes of artwork plus 22 net code bytes. ROM0, RAM, save size and OAM count
are unchanged. All four cells are loaded with the LCD off at initial Dex
startup, with no new per-scroll or B-return upload.

The rendered border was compared with the mockup across 1,224 pixels, ignoring
palette color correction; all match. Top cursor Y deliberately includes the
user's requested additional one-pixel downward adjustment. Native qualification
now checks the divider maps/attributes, bottom-cap flip and all four resident
tile payloads on scrolling and every Listing return, not only glyph/OAM state.
The 70 focused host tests pass, including bounded 64-cell decompression and
linked append-only assets. All 8,468 native checks pass on this matching link:

- 6,555 Legacy playback/tab cases: all-species cold, warm, internal paging,
  Info, Moves and Area, plus rapid Info/Moves input sweeps.
- 1,119 Modern all-species cold, warm and internal-paging playback cases.
- 373 Legacy Listing/Selected cases, including all 492 Info-page B-returns,
  Moves returns and Selected mode-entry prohibition.
- 399 frame-by-frame navigation checks, including both boundary wraps and
  seven-row page jumps; zero mixed old/new selection frames.
- 16 presentation/ordering/preference cases and six Search/Unown roundtrips.

No animation deadline or uninterrupted sampled-cry completion failure was
recorded. Matching evidence is in `regression-{legacy,modern}/summary.json`,
`listing-qualification/summary.json`, `navigation/summary.json`,
`mode-tests.json` and `menu-tests.json` under the current prototype directory.
These are headless SameBoy results, not physical-hardware qualification.

All 492 Info B-return checks pass. Their median control-return time remains
5.994 display intervals / 100.361ms, identical to the wraparound prototype.
This measures accepted Leave to Listing input loop, not first visible response.

### Wraparound Follow-Up

The previously delivered wraparound ROM and Legacy-default all-caught save are in
`build/dex-legacy-wrap-prototype/`. ROM SHA-256:
`c52e674f7de68d7a7827bf7e395b91d6350ca8a4347aa18cf06517fae47e92cc`.
Wraparound adds 82 ROMX bytes relative to the first qualified prototype, with
no additional RAM, VRAM, palette or OAM allocation.

All 1,540 follow-up native checks pass:

- 399 frame-by-frame navigation cases, now including both top/bottom wraps;
  every displayed frame is exactly the complete old or new selection.
- 746 all-species cold/warm animation and sampled-cry playback cases. The
  first entry is reached through bottom-to-top wrapping and the last through
  top-to-bottom wrapping, then immediately selected or allowed to warm first.
- 373 Listing/Selected qualification cases, including all 492 Info-page
  B-returns, Moves returns, and the prohibition on mode switching in Selected.
- 16 presentation/ordering/preference checks and six Search/Unown roundtrips.

The 68 focused host tests also pass. Two added contracts cover Up/Down wrapping
for lengths 0, 1, 2, 6, 7, 8, 255, 256 and 373, and unchanged bounded Search
navigation. No animation or sampled-cry miss occurred in the native follow-up.
Matching evidence is in `navigation/summary.json`,
`regression-legacy/summary.json`, `listing-qualification/summary.json`,
`mode-tests.json` and `menu-tests.json` under the new prototype directory.

### Original Full Qualification

The first qualified ROM, before the wraparound addition, is
`build/dex-legacy-prototype-final/pokecrystal-dex-legacy.gbc`, SHA-256
`e2104d5d9eb8447cd8d33a9b2ae11265937125f1d3f7965da653c6c6cb19faea`.

| Final suite | Coverage | Result |
| --- | --- | --- |
| Legacy standard regression | 6,555 cases across all 373 species: 373 warm, 1,492 Info, 746 Moves, 373 cold, 373 internal paging, 2,238 Area, 400 Info stress, 560 Moves stress | Zero failures |
| Modern regression | 1,119 all-species cold, internal-paging and warm cases | Zero failures |
| Legacy Listing/Selected qualification | 373 species; exact names, balls, cursor, arrows, thumb; all 492 Info pages with B-return; Moves returns; SELECT/START prohibition | Zero failures |
| Frame-by-frame navigation | 397 transitions: all adjacent Down selections, reverse movements, seven-row page jumps, 255/256 and bottom-boundary cases | Every displayed frame matches the complete old or complete new selection; zero mixed frames |
| Presentation controls | 16 cases: selection preservation, warmed mode-menu cancellation/playback, close/reopen preference, all three retained orderings in both presentations, unseen/uncaught controls | Zero failures |
| Search/Unown | Six cold/warm Search and unlocked-Unown roundtrips across both presentations | Zero failures |
| Focused host contracts | Five new Legacy and 61 audit/generator tests | All 66 pass |

All 8,466 native cases pass. The playback audits check exact authored display
intervals, published maps/pixels and natural sampled-cry completion, not merely
whether a breakpoint was reached. No animation or sampled-cry miss was recorded
in the final native suite. These are SameBoy tests, not physical-hardware proof.

The 492 Info B-returns take 5.857-6.995 display intervals from accepted Leave
entry to the Listing input loop, median 5.994: 98.070-117.117ms, median 100.361ms.
This is a control-return measurement, not first-visible input latency. Navigation
frames are inspected individually rather than inferring coherence from that
control-return time.

Evidence is under `regression-{legacy,modern}/summary.json`,
`listing-qualification/summary.json`, `navigation/summary.json`,
`mode-tests.json` and `menu-tests.json` in the delivered private directory.
Earlier private full Modern/Legacy repeats also passed, but only the matching
final-link results above are the acceptance totals.

Broad historical host-test discovery is **not green**: its ten failures and
16 errors reproduce identically against the committed parent. They include
removed instrumentation symbols, frozen normal-speed cost expectations and
older owner/workspace contracts. The parent/current comparison is retained in
`host-unit-baseline.json`; it confirms no new failing legacy test IDs. Updating
those old tests is separate maintenance, not concealed by the native pass count.

The observer is host-only: it reads linked symbols, memory and rendered frames;
it does not add cartridge instrumentation, patch live CPU state or change the
user's battery. Starting checkpoints are produced through normal inputs.

The private build/export and complete reproduction entry point is
`tools/dex_timing/legacy_listing.py`. Use a fresh ignored `build/` directory:

```sh
python3 -m tools.dex_timing.legacy_listing build --output build/dex-legacy-borders-prototype --jobs 8
python3 -m tools.dex_timing.legacy_listing prepare --output build/dex-legacy-borders-prototype
python3 -m tools.dex_timing.legacy_listing modes --output build/dex-legacy-borders-prototype
python3 -m tools.dex_timing.legacy_listing menus --output build/dex-legacy-borders-prototype
python3 -m tools.dex_timing.legacy_listing navigation --output build/dex-legacy-borders-prototype --jobs 4
python3 -m tools.dex_timing.legacy_listing qualify --output build/dex-legacy-borders-prototype --jobs 4
python3 -m tools.dex_timing.performance_regression --config build/dex-legacy-borders-prototype/legacy/config.json --output build/dex-legacy-borders-prototype/regression-legacy --suites warm info moves cold paging area info-stress moves-stress --expected-double-speed --jobs 10
python3 -m tools.dex_timing.performance_regression --config build/dex-legacy-borders-prototype/modern/config.json --output build/dex-legacy-borders-prototype/regression-modern --suites cold paging warm --expected-double-speed --jobs 4
DEX_LEGACY_BUILD=build/dex-legacy-borders-prototype PYTHONPATH=tools python3 -B -m unittest test_legacy_listing
```

Preparation defaults to the retained, all-caught integration seed. Pass
`--battery /absolute/path/to/a/copied/save.sav` when using a different source.
The tools isolate and checksum the fixture copies. `modes` exports the matching
Legacy-default `pokecrystal-dex-legacy.sav`; ROM, symbols and map share that stem.
Original production output hashes are saved and verified by every private build.

Manual review should cover Listing scroll/page movement, SELECT roundtrips,
Selected tab/Area returns, and the largest sampled-cry species. Prototype miss
breakpoints are `$a0:$6671` (animation) and `$00:$3cdc` (sample cache empty).
Rapid intentional cry cancellation remains distinguishable from uninterrupted
playback failure; capture the backtrace/state if either path is unexpected.

## Corrected Prototype Findings

- A foreground OAM transfer initially lacked interrupt protection. A short
  protected transaction prevents dispatch into inaccessible ROM during DMA.
- The generic Window copy could reveal a new portrait one frame before the
  cursor. The padded-map/OAM publication above removes that mixed frame.
- Retaining a hidden footprint's transient species tag could select stale
  graphics after that ID was reused. Uploading the incoming footprint fixes it.
- Deferring that footprint until Selected entry corrupted some already-warm
  first-frame payloads. It now finishes before warming restarts.
- Search's four-row navigation height could survive a Legacy return. Main
  Listing initialization now restores seven rows unconditionally.

These are corrected implementation findings, not deferred production bugs.
Earlier private builds/results are superseded and are not the delivered ROM.
