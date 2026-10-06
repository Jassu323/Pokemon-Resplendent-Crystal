# Legacy And Modern Dex Listings

2026-10-05. Private Legacy Listing prototype on top of
`d0d84822e` (Double Speed and Dex Optimizations). Production ROM outputs and the
installed SameBoy battery are unchanged. Manual visual acceptance and production
promotion are still pending.

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
  New/Old/ABC ordering remains independent of presentation, with unlocked Unown
  mode still reachable. Removing those older modes and redesigning this menu
  remain later work.
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

## Exact Linked Cost

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
