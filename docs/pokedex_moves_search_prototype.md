# Moves Dex Search Prototype

2026-10-11. Private follow-up over the accepted Moves sort-remembrance build,
updated with standard naming controls, screenshot-driven visual fixes, the
follow-up footer/name-spacing polish, naming-screen cursor animation, and the
standard End command-box geometry.
The accepted final build is now integrated into production; see
[Production Integration](#production-integration) for the current build and checks.
The private trial originally left production unchanged. Its ROM, saves, symbols and source under
`build/dex-moves-search-naming-parity-20261010` are the immediate safe rollback point,
pinned by the new build's `rollback.json` and protected-input manifest. The
form-polish, keyboard, original search and sort-remembrance rollback points
remain protected as well.

## Behavior

Start in the ordinary Moves list opens Sort/Search. Sort retains the accepted
Type/Alphabet popup and persistent preference. Search opens a Dex-themed
Slowpoke form with one alphabetical type selector, including blank `----`,
and a twelve-character name field. Bug is the initial type.

- Type alone matches that move type; name alone matches a case-insensitive
  substring anywhere in the displayed name. Both filters together require both
  to match. Both blank return all discovered moves.
- Only seen moves can appear. Searching never discovers a move or allocates a
  transient move ID. Results retain the current Type/Alphabet order.
- The keyboard starts uppercase whenever opened. Select toggles the letter
  keyboard without altering existing text. A adds, B deletes (empty is a no-op),
  Start highlights End, and A on End accepts the text and returns to the form.
  Filling twelve characters also highlights End, without accepting immediately.
  Backspacing to empty retains the selected case; there is no automatic case
  switch after the first letter. These match the current naming screen.
- Space is the blank key after `Z`/`z`; hyphen remains below the letters. End is
  one selectable command at column 15, row 15 (x120, y120), moved eight pixels
  left. Its white 40x9 box spans x112..151, y119..127 and uses the exact ten OAM
  records from the standard naming command box, with eight pixels of padding
  on each side of the label. Letter boxes remain 9x9. The panel is eight pixels
  taller, with its bottom edge in tile row 16.
  Left/right wrap within letter rows; vertical navigation skips blank cells.
  Hyphen and End are directly linked left/right. No draft-cancel button remains.
  Case-insensitive substring matching is unchanged; entered case is preserved.
- Slowpoke's established animation is retained. Results use the existing Moves
  stats, colored type/category icons, descriptions, scrollbar and wrapping.
  Left/right still move an eight-row page. Zero matches show `No matches.`
- B from results returns to the populated form. B/Start or Cancel from the form
  restores the ordinary list's exact cursor, scroll, sort and selected panel.
  Select from results returns to Modes. Query/results are temporary and reset
  when Moves Mode is reentered; position remembrance remains `DEX-PREF-02`.
- Results have the supplied compact Search Results footer instead of normal
  Select/Start tooltips. Start has no action within the results list.
- The ordinary Moves list's Select/Mode footer omits its final blank dark tile,
  moving only its right cap eight pixels left. Start/Option and the Results
  footer remain at their accepted positions. Pokemon-mode footers are unchanged.
- The form cursor uses the exact Pokemon Search blink routine and coordinate
  table: eight updates visible, eight hidden. Row changes restart the visible
  phase, with no new state allocation.
- The keyboard's white letter and End boxes use the actual naming-screen
  framesets and animation engine: four displayed frames visible, four hidden
  (about 67 ms each at normal speed). Movement and case changes preserve the
  current phase; reopening starts visible. The standard naming screen was
  executed independently to confirm both cursor sizes and its two-frame
  animation-update interval.

Both Search forms move their parameter rows eight pixels left. The empty Name
placeholder starts at x80, aligned with the type badge; populated names start at
x56, leaving one blank tile after Name and fitting twelve characters through
column 18 before the right border. Begin Search and Cancel retain their
original positions. The text-entry screen uses the full-width mockup border and
divider. No new artwork was drawn or existing PNG changed by the implementation.
The supplied footer was explicitly remapped from its three actual colors to
`#FFFFFF`, `#AAAAAA` and `#555555`, preserving every pixel position, opacity and
its 64x8 dimensions. The new 8x8 left-divider tile is mirrored on the right;
the other edges, center divider, font and underline reuse existing graphics.
The user's latest footer edit changes 25 pixels within x48..54, y1..6; its size,
opaque greys and margins remain compatible with the retained three-pixel load
shift. The private builder forces both supplied PNGs' packed graphics to rebuild,
even if their file timestamps are older. The linked footer is checked pixel-for-
pixel against the current PNG. Rebuilding the ROM is sufficient; no save
migration or additional asset is needed.

## Screenshot Fixes

All four supplied screenshots were inspected, including vanilla's naming screen.
The seven defects were reproduced against the protected keyboard prototype.

| Issue | Cause and correction |
| --- | --- |
| Popup text visible behind Sort/Search | The middle interior row retained listing tiles. Clear all three interior rows and attributes before drawing either popup. |
| Search field placement | Type/Name labels, cursors, arrows, fields and badge OAM used the old coordinates. Shift parameter rows left eight pixels in both Search owners; center the empty Name placeholder with the badge. |
| Keyboard cursor | The prototype used a BG arrow. Reuse the standard naming screen's letter and command boxes, with a white OBJ0 palette; shift End left one tile to fit its full standard box. |
| Text dashes | Every empty slot used the low underline. Reuse the existing middle-line graphic for unused slots and lower only the current insertion slot. |
| Wrong category icon after Search | Search's double-buffered OBJ tiles `$28..$37` overlap category tiles `$30..$35`. Reload category graphics while hidden before results and ordinary-list restoration. |
| Results footer placement | Shift the existing footer's packed pixels three pixels left at load time. Its four-pixel empty margin prevents clipping; no replacement asset is required. |
| Moves type badge placement | Shift its OAM x-coordinate from 10 to 11, moving the displayed badge from x2 to x3 in both listing and results. |

Frame-by-frame trials also caught an incorrect row stride in the newly shifted
form cursor. The stride is now initialized for all four rows; tests explicitly
check Type, Name, Begin Search and Cancel positions and results-to-form return.

## Implementation And Cost

The existing Moves renderer now accepts a variable-sized results order. Bounds,
page endpoints and scrollbar division handle zero, short and extended lists.
The regular generated orders are unchanged. Filtering walks the selected order,
checks the menu-lifetime seen snapshot, optionally loads the move type, and
copies a bounded name into scratch for substring comparison without switching
ROM banks for every character. No runtime sort or extra order table is added.

Temporary state/query/draft use WRAMX bank 3 at `$dc40..$dc7f`; the 666-byte
permanent-ID result array uses `$dc80..$df19`. These are borrowed from the
inactive Battle Tower workspace, after the existing Info scratch and Search
VBlank mailbox. The naming screen's shared Dex state is not reused. Pokemon's
order, conversion table, discovery bitmap and saved sort preference are not
modified by filtering.

| Resource | Increment over rollback |
| --- | ---: |
| ROMX | 2,953 bytes |
| ROM0 | 0 |
| Allocated WRAM0, WRAMX, SRAM, HRAM | 0 |
| Borrowed bank-3 workspace span | 730 bytes |
| Inactive bank-1 BG cells reused | 14 tiles / 224 bytes |
| Additional existing OBJ cells for naming cursor | 2 tiles / 32 bytes |

The keyboard revision adds 209 ROMX bytes over the original search prototype.
Its case flag borrows the already reserved `$dc4e` byte within the same workspace;
no RAM allocation, artwork, save format or discovery hook changed.
The visual revision adds another 296 ROMX bytes over that keyboard prototype.
The follow-up form/footer revision adds nine ROMX bytes over the accepted visual
review. Its only assembly change is in the Moves owner; it reuses the shared
Pokemon Search cursor state and graphics without changing that owner's code.
The naming-animation follow-up adds 156 ROMX bytes over that accepted form
prototype. Two control bytes borrow `$dc4f` and `$dc6d`; a sixteen-byte local
animation instance reuses the beginning of the inactive result array at `$dc80`.
Filtering reconstructs that array before results are displayed. The shared
sprite-animation workspace is not claimed, and its temporary OAM flags are
restored after each native engine call. The text state bypasses the Pokemon
owner's VBlank work, then uses the normal OAM transfer. Redraws lock OAM while
assembling a new box; the full background commit rechecks LY after disabling
interrupts to prevent a just-serviced interrupt consuming its VBlank window.
The final End-box follow-up adds eight ROMX bytes over the accepted naming-parity
prototype: two additional four-byte OAM records. No new tiles, state or assets
are required. The existing blinking engine and keyboard controls are unchanged.

Linked totals: ROM0 15,861 used / 523 free; ROMX 2,336,950 used / 710,474
free; WRAM0 4,083 used / 13 free; WRAMX 24,010 used / 4,662 free; SRAM 49,994
used / 15,542 free; HRAM 127 used / 0 free. All existing memory addresses,
save checksums/formats, acquisition/battle discovery and clock policy remain
unchanged. Relative to the protected keyboard rollback, visual assembly changes
are limited to the main Dex Search form, its Search graphics owner, and the Moves
owner. The original Search state table/VBlank dispatch changes remain inherited.
Relative to the form-polish rollback, only the private Moves owner and Dex
VBlank dispatcher change. Relative to the immediate naming-parity rollback,
only the private Moves owner changes. Normal naming-screen code and frameset
data remain byte-identical.

## Qualification

Fresh SameBoy runners use this ROM's symbols and isolated cold batteries.
Build concurrency is four workers; Moves navigation uses two workers; the wider
Pokemon Dex, discovery, battle and gameplay regressions use up to six workers
per suite as authorized for this run. Custom-menu comparisons use two workers.

- 1,692 native filter cases: both sorts, all eighteen types plus blank,
  zero/sparse/full seen snapshots, mixed-case substring queries, spaces,
  hyphens, absent queries and every full move name. Includes IDs above 255,
  all eight incoming WRAM-bank selections, result-buffer canaries, unchanged
  Pokemon order/conversion table/preference/discoveries and zero SRAM writes.
- Ten normal-input completion fixtures: 0, 1, 2, 7, 8, 9, 50, 255, 256 and
  333 moves, across both orders. Independent row, selected identity, stats,
  descriptions, icon pixels/palettes and exact wrapping/page/scrollbar audits.
  Name-only, combined-positive and combined-empty results, blank filters,
  mixed-case text and the twelve-character cap pass. All 29 keyboard selections
  are checked in four directions in both cases (232 checks), including End.
  Normal-button tests cover initial uppercase, first-character case retention,
  Select preserving existing input, backspace to empty, empty backspace, space/
  hyphen, Start without acceptance, A on End, empty confirmation, automatic End
  at twelve characters, ignored thirteenth character and uppercase on reopening.
- 1,284 follow-up form/footer checks: 1,024 exact shared-cursor blink calls
  across four rows and all eight incoming WRAM-bank selections, 256 rendered
  frames covering visible/hidden phases on every row, and blank/short/twelve-
  character field and ordinary-footer checks. Entered text begins at column 7;
  blank hyphens remain at column 10. Start/Option stays byte-for-byte aligned.
  The twelve-character query ends at column 18 without clipping the border.
- 3,840 naming-animation checks: 128 live standard-naming reference samples,
  1,856 native engine comparisons and 1,856 displayed frames across all 29
  keyboard positions in both cases. Both phases, preserved movement/redraw
  phase, unchanged shared engine/discoveries, actual white box pixels and the
  newly edited footer's linked bytes are checked. Repeat searches, reentering
  text entry and case changes also pass the normal-button fixtures below.
  End's exact 40x9 visible-pixel bounds and native ten-sprite data are checked,
  not merely its nominal dimensions.
- 2,686 regular Moves navigation/popup/page cases across both sorts pass.
- 1,406 dedicated visual checks cover all nineteen type choices in both Moves
  sorts, every selected result across the filtered lists, actual category tile
  bytes, icon palettes/positions, opaque popup interiors and shifted footer
  pixels. Both Pokemon Search presentations cycle all field choices.
- Eleven frame-by-frame transitions pass without white flashes, mixed owner
  frames or a reveal reverting. The intentional Slowpoke animation rectangle
  alone is excluded from the search-to-results static-pixel comparison.
- Modern and Legacy roundtrips pass through Modes, Selected Description/Info/
  Moves, Pokemon Search and its 83 Water/Ice results, and restored listings.
  Two normal Save/Continue roundtrips retain valid primary/backup discoveries.
- Current-link preference regression: 4,096 bank/value/register checks,
  sixteen menu fixtures, eleven Save/Continue/backup/legacy-value cases and six
  New Game/canceled overwrite/deletion lifecycle cases.
- Current-link tracking regression: 2,380 permanent-ID/bank/register checks,
  four seen-snapshot fixtures, 12,276 packed/live-ID/ownership helper checks,
  transient-ID reuse across all 333 moves, garbage collection, and all 59
  positive/negative acquisition/learning sources. Battle-source fixtures were
  recreated from this ROM, not reused from an earlier build.
- Full Pokemon Dex regression uses fresh checkpoints from this ROM: 2,238
  all-species/sort/presentation cases, 1,178 Selected-page checks, 399 Legacy
  navigation cases, 66 Modes/Unown/Search integration cases, 144 popup transition
  cases, 192 sort-reveal visual cases, 26 sparse/unseen sorting edge cases,
  204 Pokemon Search/default/return cases and 32 Modes/Unown frame-by-frame
  fixtures covering 192 transitions. Total: 4,479 fixtures, zero failures.
- Fresh persistence campaign: 2,380 helper checks, four snapshots, 1,490 cold
  reloads, 152 interrupted-write and 150 interrupted-repair cases within those
  reloads, and five New Game/overwrite/deletion lifecycle cases. Legacy migration
  adds 29 ownership/packed-ID/egg/daycare/current-box cases and 150 interrupted
  full-capacity migrations. Loads do not use save states.
- Fresh battle-use discovery campaign: 4,724 index/actor/bank/register/ID-reuse
  contracts, 400 charge/Focus Punch/called-move/Sketch/failure-context cases,
  and eight supplemental Bide cases. A real battle, flee, ordinary Save,
  cold Continue and known/unseen Moves Dex snapshot pass on this ROM.
- Paired broader campaigns against the accepted naming-parity ROM: all 100
  battle moves across both actors and four phases (1,600 runs), 20 sampled-cry
  species across six contexts and four phases (960 runs), 1,792 menu input
  contracts, 464 Pack/Apricorn/TM-HM selection checks, and 148 popup-readiness
  captures. Twenty-two paired gameplay scenarios cover navigation, purchase,
  puzzle, fishing, trainer, phone, learning, hatch, PC/party catch and Heal/Save.
  Twenty-four transition fixtures cover 64 repeat battles, eight learning
  transitions and eight whiteout returns.
- Sample data, playback settings and termination match in all 480 paired cry
  captures. The same 32 known sampled-cry misses occur in each build; these are
  existing baseline warnings, not new failures. First requested battle animation
  duration has zero difference in all 800 pairs. Custom-menu pixels, palettes
  and OAM sets also match; popup input-readiness has zero timing difference.
- Host suite: 51 pass, three obsolete popup-implementation checks skip.
  All 725 protected production/rollback files retain their hashes. Results are
  indexed in `search-qualification.json`.

Trials corrected a type-conversion call convention, the new state's VBlank
dispatch coverage, an intermediate Sort-label frame when opening Options,
and a one-frame late type badge on form entry/return. Text map/attributes and
cursor edits are staged together. No unresolved game defect was identified.
The animation trial also caught a lost A return value across FarCall, a missing
idle OAM handoff, and a late text-commit race. The final build reads the native
frameset's selected tag after advancing it and retains the guarded normal OAM
path. Transition tests exclude only the flashing box pixels; Start-to-End leaves
the static keyboard unchanged and its new selection is independently checked.

The full campaigns above were rerun on this link with fresh symbol-matched
fixtures and isolated batteries. Pokemon Dex checks include actual frontpic
animation and sampled-cry timing for every species. Discovery and surrounding
gameplay owners remain byte-identical. Interrupted writes simulate exact battery
write boundaries in the emulator, not physical cartridge power loss; the sampled
gameplay scenarios are not an exhaustive playthrough of every map event.

### Timing

Measured filter routine bodies span about 39-239 ms in the checked cases;
the overall median is 126 ms. This includes checks of all 333 identities, even
when no move is seen. The full-discovery median is about 232 ms. The retained
207-display-interval Slowpoke sequence dominates the visible wait: the captured
Bug search reaches results in about 3.68 seconds. These are not runtime sorting
delays. Captured keyboard insert/delete and case changes
complete in about 49 ms; keyboard entry is about 199 ms and accepting text/
returning to the form is about 200 ms. These are representative captures, not a
whole-campaign percentile benchmark.
Against the immediate accepted naming-parity build, normal, legacy, full-capacity
legacy and recovery-load timing is unchanged in four paired samples each. The
median save difference is -0.020 ms, below one hundredth of a displayed frame.
Raw pairs are recorded in `acquisition-performance.json`; comparisons with the
original sort-remembrance build remain in `sort-memory/timing/summary.json`.

## Review Files

Natural review pair, preserving the previous save's eight discoveries and
saved Alphabet preference:

- `build/dex-moves-search-final-review-20261011/pokecrystal-dex-moves-search.gbc`
- `build/dex-moves-search-final-review-20261011/pokecrystal-dex-moves-search.sav`

The same basename ROM/save pair under `all-seen-review/` has all 333 move flags
seeded solely for visual testing. This does not alter the natural save or game
discovery rules. Screenshots under `search-tests/ui/seen-333/` cover the form,
uppercase/lowercase text entry, End selection, populated text, mixed-case
`DoUbLe` results, combined Poison results and zero matches.
The follow-up captures under `search-tests/form-polish/` show the compact footer,
blank/short/twelve-character name fields and both cursor phases on all four rows.
`search-tests/naming-cursor/` contains independently captured visible/hidden
letter and End boxes in both cases, the live standard-naming reference traces,
and the edited footer on the Results screen.

ROM SHA-256:
`cec8550e793d9c2474982d489baf5460d1f1a301c33e6ca7f520a50683d7eb3c`.
Raw tests are under `search-tests/`; the compact index is
`search-qualification.json`. This accepted ROM is now also the production build.

## Production Integration

2026-10-11. The accepted Moves Dex, persistent discovery, acquisition/learning,
battle-use discovery, initial Struggle discovery, scrollbar, remembered sort,
and Search are integrated into the ordinary production source. The inherited
Modern/Legacy popovers, ordering, ranked Pokemon Search and colored Results
renderer are included as well. No behavior was changed during promotion.
Position remembrance and the other deferred backlog stories remain deferred.

`pokecrystal.gbc` and a clean source-only export both match the accepted ROM
byte-for-byte, with SHA-256
`cec8550e793d9c2474982d489baf5460d1f1a301c33e6ca7f520a50683d7eb3c`.
The clean export began without compiled objects, ROMs or generated tables.
New Makefile rules regenerate the Pokemon order/seen records and Moves
Type/Alphabet orders from their current source inputs. An inactive private
unknown-entry fixture include was removed; it emitted no production bytes.
The link's earlier palette-helper placement error was corrected before
qualification. No unresolved integration defect remains.

Fresh production-native checks pass: 1,692 filter cases, ten completion-level
UI fixtures, 3,840 naming cursor checks, and two Modern/Legacy Search,
Selected-page and normal Save/Continue roundtrips. Eight additional production
host checks verify linked orders/records, native End geometry, unchanged save
checksum boundaries, discovery lifecycle hooks and clean-build inputs. The
sampled-cry audit matches all 65,536 lookup combinations and all 122 samples
(37,655 compressed blocks / 602,480 decoded bytes).

The broader completed campaigns in [Qualification](#qualification) apply to
this exact ROM, established by full binary identity. They were not all rerun
during promotion. Their historical protected-production hashes remain intact
as evidence; they intentionally describe the pre-promotion production build.
Do not rewrite those manifests to claim that promotion left production
unchanged. The independent integration report is
`build/moves-dex-production-integration-20261011/production-qualification.json`.

The pre-integration production source and ROM/symbol/map outputs are retained in
`build/moves-dex-production-integration-20261011/rollback/production-before.tar.gz`,
with per-file hashes and the original working-tree status in `rollback/manifest.json`.
The old production ROM hash is
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`.
Existing user saves and unrelated working-tree edits were not overwritten.

Include the eight new `engine/pokedex` owners, the supplied
`pokedex_moves_scroll_bar_and_borders.png`, `pokedex_moves_search_left_border.png`
and `pokedex_search_results_footer.png`, and
`tools/pokedex_moves_mode_assets.py` with the changed production source and
Makefile. Generated `build/` tables are intentionally ignored and need not be
committed. `tools/test_moves_dex_production.py` is the production-only host suite;
the retained private builders and regression tools remain useful evidence.
No commit was made by the integration task.

```sh
make -j4
PYTHONPATH=tools:. python3 -m unittest tools.test_moves_dex_production -v
make verify-sampled-cries
```

## Reproduction

```sh
PYTHONPATH=tools:. python3 tools/build_moves_search_prototype.py \
  --source build/dex-moves-search-naming-parity-20261010 \
  --output build/dex-moves-search-final-review-20261011 --jobs 4
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search prepare \
  --output build/dex-moves-search-final-review-20261011
```

Run the same module with `filter`, `ui`, `visual`, `navigation`, `transitions`,
`surrounding`, `polish`, `cursor`, `tracking` and `qualify` instead of `prepare`. The output directory must be
fresh for reconstruction; `--relink` is for an existing private trial only.
Run `moves_sort_memory` with `prepare`, `helpers`, `ui`, `saves` and `timing` on
the same output. Run `moves_search_dex_regression` with `prepare`, `listings`,
`interfaces`, `selected` and `qualify`; run `search_qualification` against its
`dex-regression/` directory normally, with `--returns`, and with `--defaults`.
Run `mode_transitions` against that directory with indices `0,8,255,372`, four
phases and six workers. All checkpoints are freshly produced for this ROM.
Tracking uses the current native configuration with `move_persistence.helper_tests`
and `snapshot_tests`, then `move_acquisition` normally and with `--sources`.
Create a fresh coherent POUND battle checkpoint with
`animation_reference.prepare('acquisition', ['POUND'], ..., coherent=True)` under
this build's `runtime/animation/` before running the battle acquisition sources.
Run `move_persistence` against the naming-parity baseline, then `move_acquisition`
with `--migration` and `--interruptions`. Run `acquisition_regression` with
`menus` and `audio` first, then `gameplay`, `custom`, `transitions` and `moves`.
The `moves` setup must follow the Search `tracking` action, since both build
coherent battle fixtures. Run `move_battle_use` with `--only contract`, then
`--only semantic`, then `--only semantic --kinds bide`. Its roundtrip uses the
fresh `dex-regression/modern/config.json` when no top-level Modern fixture exists.
Run `acquisition_performance` and `acquisition_report.popup_readiness` against
the same baseline; do not run `review_save`, which would replace the retained
natural review battery. Final qualification requires all these reports and
compares the paired audio/custom-menu pixels and battle timings.
Run the Search module's `host` action before final `qualify` to record host tests.
Host tests use `MOVES_SEARCH_BUILD`, `DEX_MOVES_MODE_BUILD` and
`MOVE_DISCOVERY_BUILD` set to the new build. The existing
`tools.test_moves_sort_memory` module validates the retained rollback's broader
original campaign; current-link preference evidence is additionally asserted by
`tools.test_moves_search` and included in this build's qualification report.
