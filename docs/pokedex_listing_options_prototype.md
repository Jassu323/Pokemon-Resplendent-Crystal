# Listing Options And Sort Prototype

2026-10-06. Private Modern/Legacy prototype for the Listing START popup,
precomputed sort orders and the existing Search entry. Not promoted to
production. The current review build and qualification are in the first section;
older sections preserve the earlier investigations and measurements.
Production ROM/symbol/map hashes and the installed SameBoy save remain unchanged.

## 2026-10-06: Modern Sort Whole-Popup Three-Pixel Shift

Current private build: `build/dex-options-modern-shift-final-20261006/`. The
Modern Sort frame, labels and cursor all move **3px right**, using the user's
new `gfx/pokedex/pokedex_popover_sheet_modern.png` unchanged. Legacy's accepted
placement and Modern Options are unchanged. This is not a production promotion.

### Exact Placement And Rendering

| Presentation/popup | Visible frame origin | Size | Label origin/rows |
| --- | --- | --- | --- |
| Modern Options, unchanged | 72,56 | 72x40 | x88; y64,80 |
| Modern Sort, shifted | 67,48 | 88x56 | x83; y56,72,88 |
| Legacy Options, unchanged | 72,48 | 72x40 | x88; y56,72 |
| Legacy Sort, unchanged | 64,40 | 88x56 | x80; y48,64,80 |

Modern Sort's cursor moves from x72 to x75. Its BG footprint is 12x7 tiles,
screen x64..159; the actual frame occupies x67..154. The left three pixels
remain gray. The right five pixels retain the Listing's existing right-border
strip, read safely from its uniform bank-0 tile before staging. Each right
corner/side tile combines the user's first three columns with those original
five columns. The six new tiles are TL/TR, L/R, BL/BR in row-major order; the
existing top and bottom straight-edge tiles are shared. No artwork is generated
or edited.

Native font rows are shifted at runtime, including spill bits across tile
boundaries. Three nine-cell label rows, one cursor body and three cursor/first-
glyph variants use 31 cells. The existing combined apostrophe/`l` glyph remains
in `Nat'l Dex`. Text is prepared once per popup session; cursor movement only
changes staged maps. Font/text scratch reuses the inactive grid/Info workspace.
The extra saved right-strip cell extends the borrowed workspace by 16 bytes,
within the existing allocation. All aliases are bounded by assembly assertions.

Unused text cells upload in short HBlank bursts after the visible icon rows.
Changed border cells publish with maps and OAM in the final protected VBlank;
returning to Options atomically restores the original border. Modern Sort's
larger footprint fully covers the preceding Options frame, so its path skips a
redundant base-map redraw. Legacy and Options retain that redraw. No frontpic,
animation scheduler, cry playback or global joypad routine is changed.

### Rapid-Input Correction Found During Prototyping

An early trial could miss a second A press received while shifted glyphs were
being prepared. Reproduction: START, A to enter Sort, release for two display
intervals, then press A again. Normal mirrored input could sample A as held on
both sides of the release/repress, leaving Sort open instead of confirming.

The popup now consumes physical A/B/START edges from the existing `hJoypadSum`
accumulator as well as ordinary `hJoyPressed`, clearing the accumulator on open
and atomically after each poll. This is a popup-local latch, not a new input
queue or HRAM allocation. Held keys do not repeat; distinct command types retain
the existing priority. Multiple same-button edges during one busy span coalesce.
The corrected final link is the review ROM, not either discarded early trial.

### Qualification

The exact-translation A/B suite passes **64 paired native cases**: Modern and
Legacy, Chikorita/Weavile/Garchomp/Kyogre, eight physical input offsets. Each
case covers first Sort opening, three cursor changes/wrap, returning to Options,
reopening Sort in the same session, returning again and closing Options. Native
pixels inside the frame match an exact +3px translation for Modern Sort and an
exact unchanged image for Legacy/Options. Independent font, outer-edge, sprite-
mask and atlas checks prevent a self-consistent wrong final image from passing.
Captured intermediate frames contain only coherent outgoing/incoming states.

All **19,669 native cases and 12 focused host tests pass on this exact link**.
No stale sorted content, partial reveal, animation underrun, premature sampled-
cry exhaustion or additional regression was identified. The rapid command miss
described above was corrected before this final qualification.

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Modern cold/warm/internal paging, Info/Moves/Area, rapid input | 6,555 | 0 |
| Legacy cold/warm/internal paging, Info/Moves/Area, rapid input | 6,555 | 0 |
| All 373 starting positions, three sorts, both modes, Selected follow-ups | 2,238 | 0 |
| Modern cross-order sprite-byte cache stress | 1,728 | 0 |
| Legacy cross-order row/OAM stress | 1,728 | 0 |
| Sparse/single/empty/unknown fixtures in both modes | 26 | 0 |
| Popup held/rapid-input, border and masking contracts | 144 | 0 |
| Frame-atomic sort-publication controls | 192 | 0 |
| Modes/Search/close/reopen integration | 66 | 0 |
| Legacy exact layout, all Info pages and Moves B-return | 373 | 0 |
| Exact +3px/unchanged A/B translation and eight transition routes | 64 | 0 |

The full Selected and cross-order matrices retain the scope described in the
historical both-mode section below. All-species post-sort controls additionally
check Selected animation/cry, internal paging against the chosen order,
Info/Moves loading and Listing restoration. The A/B cases add 512 paired
transition sequences, not 512 additional independent cases.

Evidence directories in the current build are `shift-qualification/`,
`popover-qualification/`, `sort-cache-qualification/`,
`sort-cache-qualification-legacy/`, `regression/`, `regression-legacy/`,
`edges/`, `edges-legacy/`, `modal-qualification/`, `visual-qualification/`,
`integration/` and `listing-qualification/`. Native review captures are in
`visuals/`, including `sort-open.png` and its nearest-neighbor `-4x.png` preview.

### Timing And Cost

A/B against the accepted both-mode build, medians across four species and eight
physical input offsets per presentation. Measurements are button press to the
first fully published frame; there is no intermediate visible update to count
separately for these popup-only transitions.

| Modern route | Previous | Shifted | Paired median change |
| --- | ---: | ---: | ---: |
| First Sort opening in a popup session | 58.790ms / 3.511 intervals | 75.533ms / 4.511 intervals | +1 interval / 16.743ms |
| Cursor movement | 41.663ms / 2.488 intervals | 41.662ms / 2.488 intervals | No added frame |
| Sort back to Options | 42.048ms / 2.511 intervals | 42.047ms / 2.511 intervals | No added frame |
| Sort reopening in the same popup session | 58.405ms / 3.488 intervals | 41.662ms / 2.488 intervals | -1 interval / 16.743ms |

First opening pays for native glyph preparation/upload. Subsequent cursor
updates do not. Cached re-entry benefits from skipping the redundant base-map
redraw. Closing the entire popup session discards that text cache, so a later
START -> Sort is a first opening again. No extra display interval is introduced
in the paired Legacy routes, Options cancellation or remaining cursor/back
controls. No species-dependent difference was identified in these four-species
placement controls; glyph work is constant. These are not all-species latency
measurements. Paired deltas are used where input/display phase changes the
absolute distributions.

Applying the sort itself introduces no extra frame. At the beginning of the
all-caught Evolves list, eight-offset medians on this final link are:

| Changed sort | First response | Complete correct Listing |
| --- | ---: | ---: |
| Modern Nat'l Dex | 42.429ms / 2.534 intervals | 176.371ms / 10.534 intervals |
| Modern Alphabet | 42.429ms / 2.534 intervals | 193.114ms / 11.534 intervals |
| Legacy Nat'l Dex | 42.261ms / 2.524 intervals | 159.460ms / 9.524 intervals |
| Legacy Alphabet | 42.261ms / 2.524 intervals | 159.460ms / 9.524 intervals |

The first response is the established hidden-owner mask when portraits change,
not the rebuilt Listing. Across all 192 paired sort-publication controls,
Modern's median first/complete difference is -0.000057 intervals and Legacy's
is zero. Neither introduces a new display interval.

Peak measured popup commit is 3,430 base-clock cycles when replacing borders;
ordinary publication is 2,998. Both stay below the 4,300-cycle admission policy
and the 4,560-cycle hardware VBlank interval.

The shift adds **900 ROMX bytes** over the accepted both-mode prototype,
including 96 bytes of new user-authored border graphics. Total ROMX used is
**2,327,402**, with **720,022 bytes free in 186 linked banks**, in the unchanged
4MiB cartridge. The popup borrows **39 of 40** already-reserved inactive Info
atlas cells: eight borders plus 31 temporary text/cursor cells. This adds 496
bytes of temporary tile use over the preceding eight-cell popup, not a new VRAM
bank/reservation. No new ROM0, WRAM0, WRAMX, HRAM, SRAM, OAM or palette allocation.

### Review Build And Reconstruction

- ROM: `build/dex-options-modern-shift-final-20261006/pokecrystal-dex-options.gbc`.
- Matching symbols, map and all-caught save have the same basename there.
- ROM SHA-256: `376d0cb36db62d2f59ca72ac7d99ba1d4b22101249ba21a8121946163d0df707`.
- Save SHA-256: `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.
- Original user border SHA-256: `c06e77749a5c3fe58c4cfa6a25a9cdc5b811660d6cdee24f20fd7c74b12a3ce1`.
- Modern user border SHA-256: `c237e2bbed1b8bbc04a84aba6c63122d3faddd3df91e30ad2134d388b916c755`.
- The manifest records `modern_sort_shift_px: 3`; production hashes and source/
  complete build log remain alongside the private build.

Use the reconstruction commands in the following historical section with a
fresh private output. In addition, run `PYTHONPATH=tools python3 -m
dex_timing.popover_shift --baseline build/dex-options-both-modes-20261006
--output build/NEW --jobs 8` for the exact native-frame translation A/B suite.
Focused host tests now number 12 and must target the new build via
`DEX_OPTIONS_BUILD`. Earlier unshifted builds remain historical baselines.

## 2026-10-06: Legacy Popups With Shared Sorting

Historical private build: `build/dex-options-both-modes-20261006/`. The user approved
using the existing artwork and tile-aligned layout for manual review. No graphic
was generated or edited. The Modern whole-Sort-popup +3px shift and final Legacy
pixel alignment were deferred until that review. Legacy was subsequently accepted;
the first section above records the requested Modern shift.

### Behavior And Provisional Placement

- START opens Sort/Search from either main Listing presentation. Search opens
  the existing Slowpoke screen and returns through the existing presentation-
  aware path. Selected pages still cannot open either menu.
- Options opens on Sort; entering Sort highlights the current method. Up/Down
  wraps. B returns Sort to Options, then Options to Listing. START closes either
  popup. Choosing the current sort closes without moving the selection.
- A changed sort resets absolute selection, cursor and scroll to the beginning.
  Evolves/Nat'l retain unseen placeholders and the last-seen extent; Alphabet
  contains only seen species. Both modes use the same generated orders/records.
- Modern retains the corrected common cache invalidation before either portrait
  path. Legacy normalizes a seven-row linear list and redraws its text rows,
  caught marks and corner cursor instead of uploading the grid.
- If the new first portrait differs, both use the established hidden full-owner
  handoff. If it matches, Legacy stages maps and OAM together with the portrait
  retained; it does not do grid graphics or palette replacement work.
- Cancellation restores the presentation's own OAM, stages its original Listing
  maps, publishes them together and restarts normal idle preparation. The popup
  scratch aliases remain the same inactive Info/Battle Tower workspace.

Coordinates below are screen pixels, including the existing Listing SCX. Boxes
are larger than the authored mockups; their dimensions are intentionally kept
from the existing Modern prototype pending visual review.

| Presentation/popup | Tile rectangle origin | Size | Label origin/rows |
| --- | --- | --- | --- |
| Modern Options | 72,56 | 72x40 | x88; y64,80 |
| Modern Sort | 64,48 | 88x56 | x80; y56,72,88 |
| Legacy Options | 72,48 | 72x40 | x88; y56,72 |
| Legacy Sort | 64,40 | 88x56 | x80; y48,64,80 |

Legacy's complete rectangle, labels, cursor, attribute map and sprite-mask
bounds move up one tile together. Ordinary 20-cell maps and staged 32-cell maps
use their own row strides. Intersecting caught marks/corner sprites are hidden;
unobscured Listing sprites and the sidebar remain visible. The existing font
apostrophe and `l` spell `Nat'l Dex`; no separate text sheet is used.

Native emulator captures:

- `build/dex-options-both-modes-20261006/legacy-options.png`.
- `build/dex-options-both-modes-20261006/legacy-sort.png`.
- `build/dex-options-both-modes-20261006/legacy-national.png`.
- Each also has a nearest-neighbor `-4x.png` preview; these are screenshots, not
  new game artwork.

### Qualification

All **19,605 native SameBoy cases and ten focused host tests pass** on this
exact link. No animation underruns, premature sampled-cry exhaustion, stale
sorted content, partial reveal or new regression was identified in these checks.

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Modern cold/warm/internal paging, Info/Moves/Area, rapid input | 6,555 | 0 |
| Legacy cold/warm/internal paging, Info/Moves/Area, rapid input | 6,555 | 0 |
| All 373 starting positions, three sorts, both presentations, Selected follow-ups | 2,238 | 0 |
| Modern cross-order cache stress | 1,728 | 0 |
| Legacy cross-order row/OAM stress | 1,728 | 0 |
| Sparse/single/empty/unknown fixtures in both modes | 26 | 0 |
| Popup held-input/border/masking contracts in both modes | 144 | 0 |
| Heavy-species frame-atomic controls in both modes | 192 | 0 |
| Modes/Search/close/reopen | 66 | 0 |
| Legacy exact layout, all Info pages and Moves B-return | 373 | 0 |

Each full Selected run includes 373 cold, 373 warm, 373 internal-paging, 1,492
Info, 746 Moves, 2,238 Area, 400 Info-stress and 560 Moves-stress cases. The
cross-order matrix covers all three initial orders, ordinals 0-9/150/372, all
three targets including no-op, eight physical input offsets and cold/120-interval
warmed preparation. Modern independently verifies both actual icon frames
against each linked species source; Legacy verifies names, caught marks, cursor,
scrollbar and border placement against the current sorted order. Both check
immediate content, animation follow-ups, scrolling/wrapping and repeated sorts.

Evidence summaries are under `popover-qualification/`,
`sort-cache-qualification/`, `sort-cache-qualification-legacy/`, `regression/`,
`regression-legacy/`, `edges/`, `edges-legacy/`, `modal-qualification/`,
`visual-qualification/`, `integration/` and `listing-qualification/` in the current
build. The ten host tests use the same build through `DEX_OPTIONS_BUILD`.

### Timing And Cost

Beginning of all-caught Evolves Listing, medians of eight physical input offsets.
Times are button press to rendered response, not host execution duration.

| Presentation/changed sort | First response | Complete correct Listing |
| --- | ---: | ---: |
| Modern Nat'l Dex | 42.432ms / 2.534 intervals | 176.374ms / 10.534 intervals |
| Modern Alphabet | 42.432ms / 2.534 intervals | 193.117ms / 11.534 intervals |
| Legacy Nat'l Dex | 42.261ms / 2.524 intervals | 159.460ms / 9.524 intervals |
| Legacy Alphabet | 42.261ms / 2.524 intervals | 159.460ms / 9.524 intervals |

First response here is the intentional hidden-owner mask for the new portrait,
not the rebuilt Listing. The 192-case visual suite also covers retained-portrait
and same-sort controls, four starting species, both modes, all three methods and
eight input offsets. These starting-list medians are not an all-species latency
range. The earlier nine-completion-level records benchmarks remain applicable to
the unchanged shared ordering routine; they were not repeated for this extension.

Against the preceding corrected Modern-only prototype, all 96 paired Modern
visual cases have zero median first/complete change. Maximum paired increase is
0.000285 display intervals, about 0.0048ms; no extra display frame is introduced.

The Legacy extension adds **101 ROMX bytes** over the corrected Modern-only link.
Total ROMX used is **2,326,502**, leaving **720,922 bytes** in 186 linked banks.
No new ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM or OAM allocation. The sort data,
eight border tiles and modal scratch are shared, not duplicated for Legacy.

### Current Review And Reconstruction

- ROM: `build/dex-options-both-modes-20261006/pokecrystal-dex-options.gbc`.
- Matching symbols, map and all-caught save have the same basename there.
- ROM SHA-256: `ad5f742a20d736b5b5cf2f35b091c80eb27fcc36fb59f3ff5fa74e5064301b06`.
- Save SHA-256: `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.
- User border SHA-256: `c06e77749a5c3fe58c4cfa6a25a9cdc5b811660d6cdee24f20fd7c74b12a3ce1`.
- `sort-manifest.json` identifies both presentations and the retained records.
- `production-hashes.json` records the unchanged root `.gbc`, `.sym` and `.map`.
- The candidate source and complete build log remain in this private directory.

Rebuild into a fresh private output with `python3
tools/build_dex_options_prototype.py --output build/NEW`. Prepare exact-link
normal-input checkpoints with `PYTHONPATH=tools python3 -m
dex_timing.listing_options prepare --output build/NEW --battery PATH_TO_COPY`.
The prepare step creates both presentation fixtures and the all-caught review
save without changing the supplied battery or the installed SameBoy save. The
review save starts in Modern/Evolves; use SELECT -> Legacy Dex Mode to review
the new popups there.

Run `qualify`, `edges`, `integration`, `modal` and `visuals` actions of
`dex_timing.listing_options` with `--output build/NEW`. Run
`dex_timing.sort_cache --output build/NEW --presentation modern` and again with
`--presentation legacy`. Run `dex_timing.performance_regression` separately with
`build/NEW/modern/config.json` and `build/NEW/legacy/config.json`, each with suites
`cold warm paging info moves area info-stress moves-stress` and
`--expected-double-speed`. Use `--jobs` to bound parallel workers. The existing
`dex_timing.legacy_listing qualify` supplies the additional 373-species layout
and all-Info-page return audit. Focused host tests use `DEX_OPTIONS_BUILD=build/NEW
PYTHONPATH=tools python3 -m unittest tools/test_pokedex_sort.py`.

## 2026-10-06: Changed-Sort Grid Cache Correction

This section supersedes the earlier October 6 visual acceptance and full-reveal
timings. The user found stale minisprites in the cursor-reset prototype. The
records are retained as requested. Production is still untouched; the corrected
private build awaits manual review. Popup layout and user artwork are unchanged.

### Reproduction And Cause

Open Modern Listing in Evolves, stay on the first grid, then START -> Sort ->
Nat'l Dex. The name/portrait become Bulbasaur and the palettes follow the new
order, but the grid's silhouettes remain the Chikorita family. Alphabet also
reproduces it. Scrolling or wrapping eventually replaces the stale row payloads.

The cache tags contain absolute row offsets, not sort identity. Both orderings
use rows 0, 3 and 6 at their beginning. `PokedexPopover_Resort` invalidated these
tags only on its retained-portrait branch. Its changed-portrait branch performed
the hidden Main-screen handoff with the old tags intact; `Pokedex_EnsureGridCache`
therefore accepted old icon bytes at matching offsets. Later viewports work
when their cached tags do not overlap the destination's first rows. This explains
the user's beginning-of-list observation without tying the defect to Bulbasaur.

The fix calls the existing `Pokedex_InitGridCacheState` after resetting the
cursor/viewport, **before either portrait branch**. It clears all row tags and
pending ownership metadata. Both paths rebuild the new order's visible icons
before their existing reveal. Same-method selection remains a no-op. The
retained-portrait branch's redundant manual tag clear is removed.

### Stronger Qualification

The previous tests checked order, eligibility, header identity, cursor reset,
publication and playback, but not sorted-grid sprite identity. Their final-frame
self-reference admitted a stable wrong grid. That was a real test gap, not
evidence that the user's save or graphics were wrong.

`grid_audit` now independently resolves each seen visible species through the
linked `MonMenuIcons` ROM table and compares both actual VRAM icon frames, all
three columns and normal palette IDs. Matching cache tags are required but are
not sufficient. Unknown/empty cells use shared placeholder graphics and do not
display those cache slots, so their unused bytes are not an icon-identity test.
The new audit runs after sort, after Selected B-return, in sparse fixtures,
frame-atomic qualification and Search integration.

The original records ROM fails all 16 beginning-of-list Nat'l/Alphabet physical
input-phase controls with `Stale grid graphics`; its initial Evolves grid first
passes the same oracle. A host test also demonstrates that valid row tags and
palettes cannot conceal a modified sprite byte.

All **12,005 native cases pass on the corrected records ROM**, plus ten focused
host tests. No animation misses, premature sampled-cry exhaustion, partial
reveals or new regressions were identified in these suites:

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Cross-order cache stress | 1,728 | 0 |
| Sort from all 373 family positions, three targets, Selected follow-ups | 1,119 | 0 |
| Nine completion levels, two distributions, six directions, eight phases | 864 | 0 |
| Modern cold/warm/internal paging | 1,119 | 0 |
| Info four-phase playback | 1,492 | 0 |
| Moves active/settled | 746 | 0 |
| Area three-tab active/settled | 2,238 | 0 |
| Info/Moves rapid-input stress | 960 | 0 |
| Legacy cold/warm/internal paging | 1,119 | 0 |
| Legacy layout and Info/Moves B-return | 373 | 0 |
| Modes/Search/close/reopen | 66 | 0 |
| Sparse/single/empty/unknown | 13 | 0 |
| Popup held-input/border contracts | 72 | 0 |
| Heavy-species frame-atomic controls | 96 | 0 |

The 1,728 cache cases start in each of the three orders, at each ordinal 0-9,
150 and 372, choose each target including same-sort controls, cover eight
physical input offsets and cold/120-interval warmed preparation. Each checks
icon bytes immediately, after icon animation, after scrolling/wrapping/refilling,
and through three additional changed-sort selections. Matching checkpoints are
created exclusively by normal inputs on the exact tested link.

### Corrected Timing And Cost

At the beginning of the all-caught Evolves grid, eight input-phase captures give
these median button-to-rendered-frame times:

| Destination | First response | Complete correct grid |
| --- | ---: | ---: |
| Nat'l Dex | 42.43ms / 2.534 intervals | 176.37ms / 10.534 intervals |
| Alphabet | 42.43ms / 2.534 intervals | 193.11ms / 11.534 intervals |

First response is the existing intentional hidden-owner mask, not the new grid.
The previous incorrect grid appeared around two intervals earlier in these
controls; that was missing sprite work, not a usable performance advantage.
The initial response remains effectively the same. Normal-input checkpoints
and execution alignment differ slightly between the old and corrected links.

The re-run records-only completion sweep uses the same matrix as the earlier
A/B (starting after four downward moves). Medians are ms / display intervals:

| Seen | First response | Correct completion |
| ---: | ---: | ---: |
| 5 | 58.46 / 3.492 | 188.22 / 11.242 |
| 50 | 58.64 / 3.502 | 193.54 / 11.559 |
| 100 | 58.84 / 3.514 | 192.78 / 11.514 |
| 150 | 58.42 / 3.490 | 192.37 / 11.490 |
| 200 | 58.43 / 3.490 | 192.37 / 11.490 |
| 250 | 58.42 / 3.489 | 194.08 / 11.592 |
| 300 | 71.30 / 4.259 | 208.15 / 12.432 |
| 350 | 75.37 / 4.502 | 210.98 / 12.601 |
| 373 | 42.12 / 2.516 | 180.25 / 10.766 |

Across 864 cases: first 34.57-83.47ms / 2.065-4.985 intervals; completion
167.81-233.84ms / 10.023-13.967 intervals. Relative to the buggy records arm,
paired completion increases about 1-3 intervals (typically two); first response
has no consistent extra interval. Earlier **order-construction CPU costs** remain
valid because this correction is after that routine. Earlier button-to-reveal
figures and compact-arm visual acceptance are historical, not current sign-off.

The code replacement saves **5 ROMX bytes** versus the previous records link.
Total ROMX used is 2,326,401, leaving 721,023 bytes in 186 banks. No additional
ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM or OAM is allocated.

### Current Review And Evidence

- ROM: `build/dex-sort-cache-fix-20261006/pokecrystal-dex-options.gbc`.
- Matching symbols, map and all-caught save have the same basename there.
- ROM SHA-256: `b15033503479705e6af1a3aeae8f0f98e440d862be27a288856a2991f2e8b3c0`.
- Save SHA-256: `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.
- Corrected screenshot: `build/dex-sort-cache-fix-20261006/national-fixed.png`.
- Qualification summaries are in that build's `sort-cache-qualification/`,
  `popover-qualification/`, `regression/`, `regression-legacy/`,
  `listing-qualification/`, `integration/`, `edges/`, `modal-qualification/`
  and `visual-qualification/` directories.
- Completion sweep: `build/dex-sort-cache-fix-benchmark-20261006b/summary.json`.
- Original-ROM negative controls and stale screenshot:
  `build/dex-sort-cache-control-20261006/`.
- Miss breakpoints remain `$a0:$6671` (animation) and `$00:$3cdc` (sample cache
  empty branch). They are existing observation sites, not new instrumentation.

Rebuild with `python3 tools/build_dex_options_prototype.py --output build/NEW`
and prepare matching checkpoints with `PYTHONPATH=tools python3 -m
dex_timing.listing_options prepare --output build/NEW --battery PATH_TO_COPY`.
Then run `PYTHONPATH=tools python3 -m dex_timing.sort_cache --output build/NEW
--jobs 10` plus the existing Listing/Selected regression commands. Records are
the default; do not select `--without-records` for the accepted direction.

Production `.gbc`, `.sym` and `.map` still match `production-hashes.json`.
No production runtime source or user graphics was edited. No installed save
was replaced. The whole-popup +3px alignment remains deferred as requested.

## 2026-10-06: Cursor Reset And Records-Free A/B

Both private candidates now reset **changed** sorts to absolute entry zero,
cursor zero and scroll zero. Choosing the already-active order still closes
without rebuilding or moving the selection. Evolves/National start at the first
authored entry, even if unseen; Alphabet starts at its first seen entry. There
is no previously-selected-species search. A matching first-species portrait
uses the existing staged grid path; a different first species uses the existing
hidden complete-owner handoff, including a blank portrait for an unseen entry.
That portrait/name refresh is necessary to implement the requested reset policy.
It is common to both arms, not a penalty of removing records.

Popup position, borders, text and cursor graphics are unchanged. No artwork was
created or edited. Production source/output and the installed save are untouched.

### Candidates And Costs

- Records: `build/dex-sort-records-20261006/pokecrystal-dex-options.gbc`.
- Compact: `build/dex-sort-compact-20261006/pokecrystal-dex-options.gbc`.
- Each directory includes matching `.sym`, `.map` and all-caught `.sav` files.
- Records ROM SHA-256: `7d37f16fe382c21ce1ffec31db7741baa9d2fd870393434f672d8ec0e1381d80`.
- Compact ROM SHA-256: `58a08ea19063e0fdb4d2248ceba7d2e218f7124f9d4b4374fc03103fabc0ab1a`.
- Both saves SHA-256: `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.

The compact arm retains all three 746-byte word arrays and removes all three
1,492-byte record arrays: 4,476 bytes of data removed. Its local 16-bit bit-address
calculation, eight-byte mask lookup and longer loop jump add 28 code/data bytes,
for **4,448 bytes net ROMX recovered**. It snapshots seen flags once and never
uses general flag helpers or per-entry WRAM switches. Both builds retain the
identical all-seen direct-copy path. The generated indices remain automatic.

| Resource | Records | Compact |
| --- | ---: | ---: |
| Total ROMX used | 2,326,406 | 2,321,958 |
| Net ROMX above fresh current-source control | +6,703 | +2,255 |
| ROMX free in 186 linked banks | 721,018 | 725,466 |
| New ROM0 / WRAM0 / WRAMX / HRAM / SRAM allocation | 0 | 0 |

### Method

The native headless SameBoy runner uses copied battery saves and ordinary
buttons, with read-only execution/display instrumentation. There are 1,728 A/B
cases: nine seen counts, two distributions, six changed-sort directions, eight
physical input offsets and two arms. The distributions are nested first-N
authored-family entries and deterministic scattered sets (seed 20261006), not
claims about a particular player's progression. Remaining seen species are
also caught in these fixtures; unseen species are neither seen nor caught.
The duplicate all-373 distributions deliberately use identical flags.

The runner checks the complete order, eligibility mask and last-seen extent
after boot and after changing sort; cursor/viewport reset; final header/species;
old-popup/hidden-mask/new-page publication; and playback misses. It also profiles
the order routine at boot and inside the live modal. Every observed order span
runs at double speed. Display intervals are 70,224 base-clock cycles, about
16.7427ms. CPU spans include actual interrupt costs, not host execution time.

Raw spans, display-state classifications, per-method aggregates and paired
differences are in `build/dex-sort-benchmark-20261006/summary.json`.

### Order Construction

Median boot spans, milliseconds / display intervals. Evolves and National have
identical costs; Alphabet does less bookkeeping for unseen entries. Medians
combine both flag distributions and repeated input-offset fixtures.

| Seen | Evolves/National records | Evolves/National compact | Alphabet records | Alphabet compact |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 16.732 / 0.999 | 23.312 / 1.392 | 13.045 / 0.779 | 19.625 / 1.172 |
| 50 | 17.461 / 1.043 | 24.042 / 1.436 | 14.226 / 0.850 | 20.807 / 1.243 |
| 100 | 18.272 / 1.091 | 24.852 / 1.484 | 15.537 / 0.928 | 22.117 / 1.321 |
| 150 | 19.083 / 1.140 | 25.663 / 1.533 | 16.847 / 1.006 | 23.427 / 1.399 |
| 200 | 19.893 / 1.188 | 26.474 / 1.581 | 18.161 / 1.085 | 24.742 / 1.478 |
| 250 | 20.770 / 1.241 | 27.351 / 1.634 | 19.538 / 1.167 | 26.119 / 1.560 |
| 300 | 21.598 / 1.290 | 28.178 / 1.683 | 20.868 / 1.246 | 27.448 / 1.639 |
| 350 | 22.422 / 1.339 | 29.002 / 1.732 | 22.191 / 1.325 | 28.771 / 1.718 |
| 373 | 4.200 / 0.251 | 4.200 / 0.251 | 4.200 / 0.251 | 4.200 / 0.251 |

Every partial-seen boot span adds exactly 27,600 cycles: **6.580ms / 0.393
intervals**. Inside the live popup, additional interrupt/phase costs make the
median per-method penalty approximately 7.45-8.75ms. The observed maximum
order span is 27.029ms with records versus 35.492ms compact. All-seen live-modal
medians are identical at 4.766ms / 0.285 intervals.

### Button-To-Display

Each cell is milliseconds / display intervals. These are medians across 96
changed-sort cases per arm per seen count, combining methods, distributions and
input offsets; they are not an all-species latency distribution. First means
the first changed rendered frame, generally the intentional black owner mask.
Complete means the fully revealed destination Listing, not background prefetch
completion. Rendered frames are classified directly; ongoing icon motion is
accepted using the destination's normal animation phases.

| Seen | Records first | Compact first | Records complete | Compact complete |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 58.46 / 3.49 | 71.02 / 4.24 | 160.45 / 9.58 | 174.19 / 10.40 |
| 50 | 58.63 / 3.50 | 71.19 / 4.25 | 159.09 / 9.50 | 171.65 / 10.25 |
| 100 | 58.63 / 3.50 | 75.38 / 4.50 | 159.09 / 9.50 | 175.83 / 10.50 |
| 150 | 58.42 / 3.49 | 75.17 / 4.49 | 158.88 / 9.49 | 175.62 / 10.49 |
| 200 | 58.99 / 3.52 | 75.17 / 4.49 | 159.45 / 9.52 | 175.62 / 10.49 |
| 250 | 58.41 / 3.49 | 75.15 / 4.49 | 160.54 / 9.59 | 177.27 / 10.59 |
| 300 | 71.18 / 4.25 | 75.48 / 4.51 | 174.96 / 10.45 | 177.29 / 10.59 |
| 350 | 75.32 / 4.50 | 75.32 / 4.50 | 177.47 / 10.60 | 177.47 / 10.60 |
| 373 | 42.09 / 2.51 | 42.09 / 2.51 | 154.26 / 9.21 | 154.26 / 9.21 |

Paired compact cases add approximately one visible interval to first response
in 542/768 partial-seen pairs (70.6%) and to completion in 535/768 (69.7%). The
extra completion interval occurs in 64/96 at 5 seen, 64/96 at 50, 96/96 at 100,
96/96 at 150, 94/96 at 200, 96/96 at 250, 25/96 at 300, and 0/96 at 350.
The remaining extra CPU work fits inside existing publication waits. At 373,
every paired first/complete measurement is exactly identical. Medians of
whole distributions are not the same calculation as medians of paired deltas.

The changed-sort path now often replaces the portrait, so its full reveal is
longer than October 5's retained-species grid-only route. Across this sweep the
records arm first response is 34.52-83.47ms / 2.06-4.99 intervals; complete is
134.97-200.31ms / 8.06-11.96. Compact first has the same overall range and
complete reaches 200.35ms / 11.97; overlapping ranges conceal the paired delay.
There were no partial-page reveals in the A/B captures.

**Recommendation:** retain the records for this performance-focused UI. Compact
is correct and saves 4.34KiB net, but commonly delays response and reveal by a
display interval. The cursor-reset policy remains implemented in both review
copies. Further portrait/cache-transition optimization is distinct from the
order-record decision. Production integration and the requested three-pixel
popup shift remain pending user review.

### Reproduce The Follow-Up

```sh
python3 tools/build_dex_options_prototype.py --output build/dex-sort-records-review --jobs 10
python3 tools/build_dex_options_prototype.py --output build/dex-sort-compact-review --jobs 10 --without-records
PYTHONPATH=tools python3 -m dex_timing.sort_benchmark --records build/dex-sort-records-review --compact build/dex-sort-compact-review --output build/dex-sort-benchmark-review --battery build/dex-options-prototype-20261005c/pokecrystal-dex-options.sav --jobs 16
```

Use `--quick` for the 48-case five/all-seen smoke test. Both candidates' current
miss breakpoints are `$a0:$6671` (animation) and `$0:$3cdc` (sampled cache empty).
Resolve those addresses again after any new link.

### Follow-Up Qualification

All **11,141 native cases** pass, plus the 48-case smoke test and nine host tests
on each arm (18 host executions). The compact arm received the full broader
Dex suite; both arms received the completion-level A/B and linked-data checks.
No new bugs, animation misses, sampled-cache exhaustions, order/visibility
errors, partial reveals or physical RAM growth were identified.

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Completion-level A/B, both arms | 1,728 | 0 |
| Modern cold/warm/internal paging | 1,119 | 0 |
| Modern Info, four playback phases | 1,492 | 0 |
| Modern Moves, active/settled | 746 | 0 |
| Modern Area, three tabs and active/settled | 2,238 | 0 |
| Modern Info/Moves rapid-input stress | 960 | 0 |
| Legacy cold/warm/internal paging | 1,119 | 0 |
| Legacy layout and Info/Moves B-returns | 373 | 0 |
| Sort selection from every species position, all three targets | 1,119 | 0 |
| Modes/Search/close/reopen integration | 66 | 0 |
| Sparse/single/empty/unknown controls | 13 | 0 |
| Popup cursor/held-input/border contracts | 72 | 0 |
| Heavy-species frame-atomic controls | 96 | 0 |

Sort selection tests require zero cursor/viewport on a changed method and
unchanged selection on a same-method no-op. Subsequent playback, sorted internal
paging and Info/Moves returns are checked after each selection. The broader
suite still visits every species, including all known heavy animation/cry cases.
Frame tests allow the deliberate fully hidden portrait-replacement handoff but
reject mixed pages. They retain the stronger unchanged-portrait/graphics checks
when the portrait is not being replaced.

Evidence is under `build/dex-sort-compact-20261006/` in `regression/`,
`regression-legacy/`, `listing-qualification/`, `popover-qualification/`,
`integration/`, `edges/`, `modal-qualification/`, and `visual-qualification/`.
Production `.gbc`, `.sym` and `.map` hashes match both builds' recorded before
hashes. User border artwork still matches SHA-256
`c06e77749a5c3fe58c4cfa6a25a9cdc5b811660d6cdee24f20fd7c74b12a3ce1`.

## Initial Layout And Controls (October 5)

The user-authored `gfx/pokedex/pokedex_popover_sheet.png` is used unchanged.
Its eight tiles provide all corners and edges. There is no new font artwork:
the existing `$d1` combined `'l` glyph makes `Nat'l Dex` eight text cells.
Missing or revised artwork must be requested from the user, not generated.

The tile-aligned first prototype follows the scope's accepted direction rather
than attempting transparent, off-tile composition:

| Popup | Screen rectangle | Text origins | Cursor origins |
| --- | --- | --- | --- |
| Options | x72/y56, 72x40px | x88, y64/y80 | x80, y64/y80 |
| Sort | x64/y48, 88x56px | x80, y56/y72/y88 | x72, y56/y72/y88 |

All edges have the sheet's two-pixel white border. Fill and text use existing
UI palette 0; the background is existing RGB(5,5,5). The colored portrait,
name, Seen/Own totals, footer and uncovered grid remain visible. Grid animation
and navigation freeze while either popup is open. Only intersecting sprites
are masked, including caught balls and green cursor corners.

- START in Modern Listing opens `Sort` / `Search`.
- A on Sort opens `Evolves`, `Nat'l Dex`, `Alphabet`, highlighting the current
  order. Up/Down wraps either popup's rows.
- A applies the chosen order and closes. Applying the already-active order
  just closes; it does not reconstruct the order or decompress icons.
- B in Sort returns to Options. B or START in Options closes. START in Sort
  also closes to Listing.
- A on Search uses the existing full-screen Slowpoke/type Search owner and
  its accepted hidden stage-and-reveal transition.
- SELECT still opens Modes from Listing only. START/SELECT remain ignored
  on Selected Description, Info and Moves, including during playback.
- Legacy START retains its existing direct Search action. No unreviewed Legacy
  popup layout was introduced. The new ordering data serves both listings.

Changing order retains the selected permanent 16-bit species identity and
normalizes its new cursor/viewport position. It does not preserve an old
ordinal or transient allocated species ID. Alphabet retains vanilla's seen-only
behavior. If it excludes an unseen selected species, the first seen result is
chosen through the established hidden full-owner reconstruction; that exceptional
route also replaces the portrait. An empty Dex remains empty and prohibits
menus as before.

The sort enum remains distinct from Modern/Legacy presentation. The existing
last-order preference is saved on Dex exit and restored on reopening; no save
layout or migration is needed.

## Ordering And Future Species

`tools/pokedex_sort_assets.py` produces three validated orders on every private
build/relink. There is no runtime comparison sort and no Changing Modes message
or 128-frame deliberate wait.

- Evolves uses `data/pokemon/dex_order_new.asm`, preserving the currently
  authored family backbone. It does not infer missing gameplay evolution links.
- National uses the original first 251 constants' sequential national numbers
  and explicit `NatDex` metadata on subsequent species constants. The prior
  1..N internal-index path was not National order for several additions.
- Alphabet is generated from displayed names, ignoring punctuation and using
  deterministic gender/national-number tie breaks. This also fixes existing
  authored inversions such as Absol/Abra and Buneary/Banette.

Each order has a 373-word array and 373 four-byte records containing the
permanent species word, seen-byte offset and bit mask. The word array provides
a fast direct copy when every species is seen. Otherwise a bounded O(N) pass
builds the active writable order and position-keyed eligibility mask. National
and Evolves preserve unknown holes through the last seen entry; Alphabet
compacts them. Search can still compact the same active buffer in place.

The seen bitmap is snapshotted once into existing WRAM0 grid scratch. This
avoids per-species division, general flag helpers and repeated bank changes.
The four-byte records intentionally duplicate species words to keep the
partial-seen loop simple, while retaining the all-seen direct-copy path.

Renaming a species automatically changes its generated Alphabet position.
Changing its explicit National number automatically changes National position.
Adding a species requires its normal game data/name, a National number and one
authored family placement; there is no manual generated-index edit. The compiler
rejects duplicate numbers, inconsistent names and incomplete family coverage.
These behaviors are tested with a synthetic 374th species and a renamed entry.

Family corrections remain deferred. Editing gameplay evolution records alone
does not reorder Evolves; update the authored family list when that data work
is done. The current 67-byte eligibility-mask allocation supports at most 536
species; increasing beyond that requires revisiting scratch, not just rebuilding
the tables. The prototype compiler is called by the private build tool; a future
production integration must add the equivalent generated-file dependencies.

## Stage And Reveal

The popup is a separate Listing state. Entry cancels idle animation warming
before borrowing inactive Info/Description workspace. It saves the 160-byte
shadow OAM and uploads eight border tiles into unused BG-bank-1 Info-atlas cells
`$fa..$ff` and `$28..$29`. Existing font cells remain in BG bank 0.

Maps are staged in the existing padded 32-column owner buffers. A same-bank
VBlank helper publishes the complete attribute map, tilemap and masked OAM.
Cursor-only navigation edits its two or three padded cursor cells without
rebuilding names, borders or grid data. Closing reconstructs the resident
Listing map/OAM without reloading the portrait or decompressing the grid.

A changed sort keeps the outgoing popup and grid visible during preparation.
It rebuilds order-dependent tags, stages the three visible grid rows in reused
WRAMX, and prepares maps, palettes, cursor, caught marks and scrollbar. The same
known selected species keeps its portrait graphics and palette.

The staged icons are uploaded after scanline 120, once all visible grid icons
have been scanned. Each four-tile GDMA burst starts in a full HBlank; 18 bursts
finish before VBlank. The following VBlank commits maps, palette targets and
OAM together. Offscreen cache tags stay invalid and ordinary scrolling repairs
them when needed. No whole-screen LCD-off clear is used for ordinary sorting.

The measured changed-sort publication costs 4,184 reference cycles, below the
4,560-cycle physical VBlank budget. Popup-only publication costs 2,974. The
entire bank-0 tile-graphics range remains byte-identical across all focused
sort captures. Frame audits allow only the old complete popup/grid or new
complete grid, never a partially assembled combination. The scrollbar may
correctly relocate because the selected species has a different ordinal.

Before normal dispatch resumes, inactive Description/Info state overwritten
by staging is cleared. Idle warming then restarts with the correct seen-bitmap
WRAM bank. Warming itself is retained; removing it remains `DEX-PERF-03`.
No portrait scheduler, sampled-cry timer or playback pacing changes are made.

## Timing

Physical display intervals use 70,224 reference cycles at 59.7275Hz, about
16.743ms each. Button assertion, native routine spans and completed display
boundaries are observed externally in SameBoy; the ROM has no added diagnostic
counters. Host parallelism changes test throughput, not emulated timing.

First response below means the requested UI response, not an independent
minisprite animation that happens while the key is being sampled. Publication
is atomic, so first requested response and complete destination share a frame.

| Route, Chikorita single input phase | First ms / display intervals | Complete ms / display intervals |
| --- | ---: | ---: |
| START to Options | 64.42 / 3.85 | 64.42 / 3.85 |
| Options to Sort | 64.42 / 3.85 | 64.42 / 3.85 |
| Sort cursor Down | 47.67 / 2.85 | 47.67 / 2.85 |
| Apply National from Evolves | 97.90 / 5.85 | 97.90 / 5.85 |
| Sort B to Options | 47.67 / 2.85 | 47.67 / 2.85 |
| Options B cancellation | 47.67 / 2.85 | 47.67 / 2.85 |
| Apply already-active sort | 47.67 / 2.85 | 47.67 / 2.85 |
| Options START cancellation | 47.67 / 2.85 | 47.67 / 2.85 |

Across Chikorita, Unown, Kyogre and Regigigas, three sort targets and eight
physical input phases, there are 96 focused captures:

| Action | Cases | First and complete range, ms / intervals | Median, ms / intervals |
| --- | ---: | ---: | ---: |
| Same Evolves no-op | 32 | 34.59-49.77 / 2.07-2.97 | 42.18 / 2.52 |
| Changed National or Alphabet | 64 | 84.92-116.66 / 5.07-6.97 | 100.78 / 6.02 |

The changed-sort variation includes selected-position lookup, incoming icon
preparation and physical input phase, not frontpic animation complexity. This
is not an all-species latency distribution. The exceptional unseen-to-Alphabet
portrait-replacement path uses the full hidden reconstruction and is not
represented by the ordinary retained-portrait timing range.

Observed order-construction spans at Dex boot, including ordinary interrupt
costs in that route:

| Seen population | Evolves ms / intervals | National ms / intervals | Alphabet ms / intervals |
| --- | ---: | ---: | ---: |
| All 373 | 4.20 / 0.25 | 4.20 / 0.25 | 4.20 / 0.25 |
| 364, nine holes | 22.62 / 1.35 | 22.62 / 1.35 | 22.53 / 1.35 |
| One | 16.67 / 1.00 | 16.67 / 1.00 | 12.94 / 0.77 |
| None | 16.65 / 0.99 | 16.65 / 0.99 | 12.92 / 0.77 |

All-seen changed-sort spans under the active modal are 4.754-4.768ms because
their interrupted execution phase differs from boot. The prior measured
all-seen double-speed paths were 39.32ms Evolves, 4.82ms internal-index numerical
and 24.89ms Alphabet. The numerical comparison is not identical semantics:
the new table provides genuine National ordering for additions.

The initial one-to-two-interval popup-publication target is not met: this first
prototype takes roughly three-to-four intervals including polling and safe
uploads. The several-second vanilla delay is removed. The scope's vanilla
button-to-Listing-ready route measured 2,879-2,997ms, primarily its explicit
message waits and full Listing reconstruction. That control-loop metric is not
an exact pixel-latency A/B for these differently designed screens.

## Resource Cost

Linked against a freshly rebuilt, unmodified current-source control rather
than the older root output map:

| Resource | Net cost |
| --- | ---: |
| ROMX | +6,730 bytes, about 6.57 KiB |
| Generated orders/records | +5,222 bytes after replacing old two tables |
| Controller, publication, wrappers and replaced order code | +1,380 bytes |
| User border graphics | +128 bytes |
| New physical ROM0 / WRAM0 / WRAMX / HRAM / SRAM allocation | Zero |
| Borrowed VRAM | Eight BG-bank-1 tiles, 128 bytes |
| New BG/OBJ palettes or OAM entries | Zero |

The existing BA Legacy/Modes section grows by 8,358 bytes; new code there,
elsewhere and removed old ordering code yield the smaller net delta above.
BA still has 6,250 free bytes, and the linked ROMX bank count stays at 186.

The reused bank-3 overlay is `$d480..$dd2f`, a 2,224-byte span including padding:
1,920 bytes for physical-row staging, nine control bytes, 160 saved OAM bytes
and 128 border bytes. The existing 1,152-byte padded map/attribute buffers at
`$d000..$d47f` remain their normal allocation. This is more scratch reuse than
the initial 0.5-KiB estimate because changed sorts stage incoming icons too;
it adds no physical allocation and never overlaps an active Selected producer.

The private link uses 15,861 ROM0 and 2,326,433 ROMX bytes. ROM0 has 523 free,
WRAM0 13, WRAMX 4,728 across seven banks, and HRAM zero. The cartridge remains
4 MiB; code/data occupies 2,342,294 bytes, leaving 1,852,010 bytes overall
(about 1.77 MiB). Of that, 720,991 bytes are holes in already-linked ROMX banks;
the remainder includes unlinked banks and ROM0 free space.

Complexity is moderate: orders are straightforward, but a live grid with mixed
BG/OAM palettes requires explicit publication ownership. Main risks are cache
tags following old ordinals, interrupt-time bank changes, OAM leakage and
scratch lifetimes. The stage-and-reveal/frame/byte audits exercise those risks;
SameBoy results do not replace physical-hardware qualification or manual review.

## Qualification

All rows below refer to the final native-font ROM, not superseded private links.

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Modern cold / warm / internal paging | 1,119 | 0 |
| Modern Info at four input timings | 1,492 | 0 |
| Modern Moves at two input timings | 746 | 0 |
| Modern Area across three tabs, active/settled | 2,238 | 0 |
| Modern Info / Moves rapid-input stress | 960 | 0 |
| Legacy cold / warm / internal paging | 1,119 | 0 |
| Legacy layout and all Info-page/Moves B-returns | 373 | 0 |
| Every species, all three orders, post-sort playback/paging/returns | 1,119 | 0 |
| Locked/unlocked Modes, Search and close/reopen preference | 66 | 0 |
| Sparse / single / empty seen lists and unseen-selection fallback | 13 | 0 |
| Atomic visual reveal, four species / eight phases / three targets | 96 | 0 |
| Nine cursor positions / eight phases, border/OAM/held/rapid input | 72 | 0 |
| Native total | 9,413 | 0 |
| Focused table/art/font/memory host contracts | 8 | 0 |

The sort-specific species suite verifies full permutations, masks, last-seen
extent, permanent selected identity, internal paging by the new order and
Info/Moves returns. Playback checks audit authored map/pixel publication and
natural sampled-cry completion, not only whether a miss breakpoint is reached.
No animation or sampled-cry miss is recorded. Legacy qualification exercises
492 individual Info-page B-returns in its 373 species cases.

Additional independent checks verify ROM/symbol/map production hashes, unchanged
user sheet pixels, native `$d1` label encoding, valid VBlank cost, no bank-0 tile
graphics changes and no partially revealed frame. Held A/B/START do not repeat
across modal owners; rapid A eventually enters ordinary Selected and B returns
with the original selection/order. Both popup grids mask exactly the intersecting
saved sprites and retain the others.

Corrected private implementation findings:

- An early helper switched ROM banks while executing ROMX code. Publication now
  lives alongside the dispatcher and uses a direct same-bank call; no interrupt
  FarCall scratch is borrowed.
- A long active-display GDMA corrupted both VRAM banks. The final bounded
  full-HBlank bursts and frame/byte audits replace that unsafe transfer.
- Overlay glyph bytes could masquerade as pending Info state. Inactive state
  is cleared before resuming ordinary dispatch.
- Seen/name/warming helpers need their expected WRAM bank; all relevant boundaries
  now select and restore it explicitly.
- Empty Alphabet could feed the `$ffff` terminator into the transient ID allocator.
  A valid unseen placeholder is resolved instead; an empty list is still empty.

These are resolved prototype findings, not outstanding regressions or claims
that the separate deferred production bugs are fixed.

## Reproduction And Manual Review

Private output directory: `build/dex-options-prototype-20261005c/`.

- ROM: `pokecrystal-dex-options.gbc`
- Matching all-caught private save: `pokecrystal-dex-options.sav`
- Symbols/map share the ROM stem.
- Screenshots: `visuals/options.png`, `visuals/sort.png`, plus 4x versions.
- Timing captures: `visuals/measurements.json`, `visual-qualification/summary.json`,
  and `edges/order-costs.json`.
- Matching native summaries: `regression-modern-final/summary.json`,
  `regression-legacy-final/summary.json`, `popover-qualification/summary.json`,
  `listing-qualification/summary.json`, `integration/summary.json`,
  `edges/summary.json`, `modal-qualification/summary.json`.
- `production-hashes.json` records unchanged root output identities.

ROM SHA-256:
`75b6fa142a8e6c2284fb8ccff388ecd97242e074e48929c22663d11539512a30`.
Fresh unchanged current-source control SHA-256:
`d53736afb6a6098f6c5b0ed228c9e5ba5efbd9d1cb4e28f169c9fed60a55a34b`.
User border sheet SHA-256:
`c06e77749a5c3fe58c4cfa6a25a9cdc5b811660d6cdee24f20fd7c74b12a3ce1`.

Build a fresh private directory; a relink of the same candidate needs
`--relink`. Always prepare new matching states after changing the ROM:

```sh
python3 tools/build_dex_options_prototype.py --output build/dex-options-review --jobs 10
PYTHONPATH=tools python3 -m dex_timing.listing_options prepare --output build/dex-options-review --battery build/dex-options-prototype-20261005c/pokecrystal-dex-options.sav
PYTHONPATH=tools python3 -m dex_timing.listing_options qualify --output build/dex-options-review --jobs 6
PYTHONPATH=tools python3 -m dex_timing.listing_options edges --output build/dex-options-review
PYTHONPATH=tools python3 -m dex_timing.listing_options integration --output build/dex-options-review --jobs 4
PYTHONPATH=tools python3 -m dex_timing.listing_options visuals --output build/dex-options-review --jobs 4
PYTHONPATH=tools python3 -m dex_timing.listing_options modal --output build/dex-options-review --jobs 4
PYTHONPATH=tools python3 -m dex_timing.listing_options measure --output build/dex-options-review
PYTHONPATH=tools python3 -m dex_timing.legacy_listing qualify --output build/dex-options-review --jobs 4
PYTHONPATH=tools python3 -m dex_timing.performance_regression --config build/dex-options-review/modern/config.json --output build/dex-options-review/regression-modern --suites cold warm paging info moves area info-stress moves-stress --expected-double-speed --jobs 10
PYTHONPATH=tools python3 -m dex_timing.performance_regression --config build/dex-options-review/legacy/config.json --output build/dex-options-review/regression-legacy --suites cold warm paging --expected-double-speed --jobs 4
DEX_OPTIONS_BUILD=build/dex-options-review PYTHONPATH=tools python3 -m unittest tools/test_pokedex_sort.py
```

The private build copies tracked/local assets without editing them, applies
the isolated feature patches and compiles generated ordering data. The headless
observer reads execution, pixels, VRAM and existing ownership fields; it never
patches live runtime RAM to force a successful route.

Preparation's `--battery` accepts an existing compatible save as a read-only
seed, including the delivered review save. It normalizes order/presentation
only in a new private copy before adding all-caught flags and checksums. This
avoids depending on the older default seed directory after artifact cleanup.

Initial October 5 manual review: check both popup sizes/placement, native `Nat'l Dex` spacing,
white border and green-corner masking; change all three orders at early/late
entries and confirm the highlighted species remains selected. This historical
selection-preservation instruction is superseded by the October 6 cursor-reset
policy above; current build recipes produce that newer policy. Exercise B/START
cancellation, Search/Selected returns and Modes/Unown roundtrips. Check known
heavy animation/cry species after menu use. Family-order omissions are still
deferred data, not a sorting-controller defect.

Miss breakpoints for this exact ROM:

```text
breakpoint $a0:$6671
breakpoint $0:$3cdc
```

At an unexpected hit record species, input sequence, backtrace/registers,
`ticks keep`, `lcd`, `x/27 $0:$c72e`, `x/3 $0:$c758`, `x/8 $4:$dff4`,
`x/6 $0:$ffee`, and a failure state/video. The first breakpoint is Selected
animation failure; the second is sampled-cache empty with work remaining.
Addresses must be resolved again after a later link.
