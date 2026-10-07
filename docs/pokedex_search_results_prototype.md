# Pokedex Search Results Renderer Prototype

2026-10-06. Private prototype, **not promoted to production**. This extends the
ranked Search prototype with colored, base-only Results portraits, the resident
small cursor and colored caught ball, compact Results type badges, an orange gap
below the portrait, and an alphabetical Search selector. The latest revision
also restores the dark inner portrait bottom edge and listing lower-left corner,
cleans the Search header and starts the alphabetical selector on Bug.
No artwork was created or edited. The initial Results build passed 5,363 native
cases, 36 prior-prototype controls and 18 host tests. The latest Search header and
default revision passed 570 focused native cases, 20 host tests and 18 native
screenshot header checks.

## Review Files

Directory: `build/dex-search-results-20261006d/`.

- `pokecrystal-dex-search.gbc`: updated review ROM.
- `pokecrystal-dex-search.sav`: matching all-caught review save.
- `pokecrystal-dex-search.sym/.map`: matching symbols and resource map.
- `candidate/`: isolated build source, including the private Results renderer.
- `visual-search-modern-0/` through `visual-search-modern-2/`: Search entry,
  type-change, Results and Search-return captures under all three orders.
- `visual-search-legacy-0/` through `visual-search-legacy-2/`: equivalent Legacy
  captures under all three orders.
- `search-header-pixel-checks.json`: 18 captured-screen header/default checks.
- The preceding border revision's nine border/gap captures remain in
  `build/dex-search-results-20261006c/`.

ROM SHA256:
`746ab0295430e3a0911b1ff5b13fff9d8a880174771e2ae55a8943b155f3db56`.

Save SHA256:
`7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.

The root production source/output and installed SameBoy ROM/save are not
replaced. The protected root ROM remains
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`.

## Repairs And Ownership

| Request | Old path | Private replacement |
| --- | --- | --- |
| Colored, faster portrait | `Pokedex_PrintListing` tail-called the full `GetMonFrontpic` dictionary loader; Results forced the question-mark/green palette | Accepted base-only staged portrait preparation, normal species colors, and Legacy's coherent portrait/Window transaction |
| Small cursor | Old multi-sprite vanilla outline | Four resident `$40` OAM corner tiles, OBJ0, matching Legacy geometry |
| Caught-ball colors | BG `$4f` glyph inherited the panel palette | Resident `$41` OAM ball, OBJ1, keyed to each row's caught flag |
| Remove dark strip | Generic color2 fill used the new dark-gray UI color | Existing solid color1 `$31` tile for the gap; border tiles retain the standard UI palette |
| Results type badges | Raw Window type strings/slash | Existing compact badges, four sprites each at x80, y112/y120, OBJ2/3 |
| Alphabetical selector | Original gameplay-type-oriented Search enumeration | Search-only conversion and fallback-string tables reordered together |
| Search header | Whole-screen color2 fill became dark gray above and beside the title | Fill the first two rows with existing orange color1 `$31` tiles before drawing the rounded title |
| Starting type | Normal occupied the middle of the alphabetical selector | Type1 starts at Bug, selector value1; Type2 remains None |

No new border tile is required. The existing tile shapes match vanilla after
the project's color-index remapping. The prior outside-border palette covered
rows 8-10, columns 0-8, unintentionally turning the portrait's two-pixel dark bottom
band and four columns inside the listing's lower-left edge orange. That palette
override and its unused palette data are removed. The solid color1 gap already
provides orange outside fill without recoloring any border pixels. White frame
positions and the standard dark-gray outlines and panels are preserved.

The Search header had the same old background-fill assumption: its unused top
row and pixels outside the title inherited color2 instead of orange. Only those
two rows are initialized with the existing orange tile. The title, rounded
caps, menu panel, type icons and Slowpoke keep their established palettes and
artwork. The native captures match vanilla's cap shapes without restoring its
black panel color or uppercase typography.

Results retains four rows, the Search Results/Type/Found captions, resident
one-tile arrows, bounded scrolling, the active ranked order and existing
National number labels. Selecting a result opens the shared Selected owner.
Returning reloads the Results-owned portrait, maps, badges and palettes before
reveal. Search and its 207 Slowpoke frame waits are unchanged except for selector
order and initial Type1 choice; Bug now starts Type1 and None starts Type2.
Type2 None or a duplicate of Type1 shows only one Results badge, matching the
previous one-string Results behavior.

The selector sequence is Bug, Dark, Dragon, Electric, Fairy, Fighting, Fire,
Flying, Ghost, Grass, Ground, Ice, Normal, Poison, Psychic, Rock, Steel, Water.
This does not renumber gameplay types, change type matchups, reorder species or
change the ranked both/Type1-only/Type2-only algorithm.

### Portrait Publication

On a Results selection change, base-only decompression and palette preparation
occur while the old portrait remains valid. The old portrait finishes scanning
before its 49 padded tiles and palette are replaced. The new Window names and
small cursor/balls publish together in the following protected VBlank. There is
no visible intermediate monochrome portrait or mismatched name/color frame.

Initial entry and return are hidden owner handoffs: prepare the portrait and
static badges, build both maps and palettes, then reveal. No animation/cry
scheduler policy or playback speed changes are included. Results remains static,
as in vanilla, and does not add a background animation warm-up.

## Resource Cost

Relative to `build/dex-search-ranked-20261006e/`:

| Linked section | Increment |
| --- | ---: |
| Private Search/Results ROMX | 575 bytes |
| Existing Dex bank10 | 57 bytes |
| CGB palette/attribute helper | 55 bytes |
| Legacy row-species bridge | 4 bytes |
| **Total ROMX** | **691 bytes** |
| ROM0, WRAM0, WRAMX, SRAM, HRAM allocations | **0 bytes** |
| New VRAM allocation | **0 tiles** |

The existing bank-3 owner maps occupy `$d000..$d47f`; Search records begin at
`$d480`, so map staging cannot overwrite unconsumed records. The existing scratch
and palette buffers are reused. Badges occupy the first eight tiles of Selected's
existing OBJ reservation, `$28..$2f` in VRAM bank1, only while Results owns it.
The badges are uploaded once per hidden Results entry, not on each scroll.

Results uses BG0 for UI, borders and orange gap, BG1 for the colored portrait;
OBJ0 for cursor, OBJ1 for balls, OBJ2/3 for badges. Maximum visible OAM is
16 sprites: four cursor corners, four row balls, eight badge tiles. The measured
scanline peak is four, below the hardware limit of ten.

The image remains 4 MiB. Linked ROM0 is 15,861 bytes and ROMX is 2,328,901 bytes;
1,849,542 bytes remain unused across the complete cartridge address space,
subject to bank placement. Within the 186 linker-reported ROMX banks, slack is
718,523 bytes. Existing RAM headroom is unchanged: WRAM0 13 bytes, WRAMX 4,728
bytes total, HRAM zero.

The border correction removes 28 ROMX bytes relative to the preceding Results
build and adds no RAM, VRAM or palette allocation.
The subsequent Search header fix adds 11 ROMX bytes; the Bug default costs no
additional space. Neither change allocates new graphics, palettes or RAM.

## Runtime Measurements

These measurements belong to the preceding Results build,
`build/dex-search-results-20261006b/`. The border/header corrections and
starting-type change do not alter scrolling, portrait publication or input
handling; timing was not retaken.

These are actual native display intervals, not loop-count estimates. One
interval is 70,224 base-clock cycles, approximately 16.743 ms. First means the
first completed scanout with changed visible pixels; Complete means the first
scanout matching the settled final picture. A coherent portrait/name/cursor
change deliberately has equal First and Complete values.

The paired control is the preceding ranked/icons prototype, not the older root
production binary. The 36 controls and 36 candidate trials cover Normal/None,
Water/Ice and Grass/None, both Listing presentations and all three orders.
Cursor trials move row0 -> row1 without scrolling; Scroll trials move row3 ->
row4 and shift the visible four-row window.

| Operation | Prior First ms (intervals) | New First ms (intervals) | Prior Complete ms (intervals) | New Complete ms (intervals) |
| --- | --- | --- | --- | --- |
| In-window selection | 47.74-49.04 (2.85-2.93) | 82.46-82.52 (4.93) | 149.47-166.24 (8.93-9.93) | 82.46-82.52 (4.93) |
| Window scroll | 65.76-82.52 (3.93-4.93) | 81.23-82.52 (4.85-4.93) | 199.69-233.20 (11.93-13.93) | 81.23-82.52 (4.85-4.93) |

Completion improves by four to five intervals for in-window selection, and
seven to nine for scrolling. **First feedback is not uniformly faster**: the
old cursor moved before the slow portrait/window refresh. The new coherent
transaction delays that isolated cursor feedback by about two intervals for
in-window selection, and zero to one for scrolling. This is an explicit review
tradeoff, not a hidden claim that every latency metric improved.

Species/ordering affects the old dictionary-load cost. The candidate's sampled
selection and scroll completion is effectively flat at five intervals; the
native all-species checks independently cover larger portraits as well.

The 27 successful/no-match Search trials retain five, 50 and 373 seen fixtures,
all three orders and the same named queries as the preceding report. With all
373 seen, successful Search completion falls from 4,081.58-4,098.32 ms
(243.78-244.78 intervals) to 3,763.47-3,765.52 ms (224.78-224.90): **19-20
intervals sooner**. The Results initializer falls from approximately 25-26
intervals to six. Slowpoke's authored waits are unchanged; filtering and first
Slowpoke motion remain essentially unchanged apart from normal input/scanline
phase differences. The remaining roughly 3.5-second Slowpoke sequence is
intentional, not Results loading work.

Evidence: `results-timing-control/`, `results-timing-new/`, `search-runtime/`.
The A/B directories retain the native PPM frame sequences and exact timing
events rather than only aggregate numbers.

## Qualification

Six native workers maximum; pools run sequentially. The review ROM contains no
new diagnostic code. Native observers read the linked production-style runtime,
RAM, VRAM, hardware palettes/OAM and display cycles without writing game state.

| Suite | Cases | Result |
| --- | ---: | --- |
| All-species Listing, orders, Selected animation/cry, internal paging, Info/Moves and return | 2,238 | Pass |
| Listing/Modes/Unown/Area integration | 66 | Pass |
| Modal controls and transition phases | 144 | Pass |
| Empty/sparse/order/selection edges | 26 | Pass |
| Search controls, 25 Slowpoke poses, transitions and Selected returns | 144 | Pass |
| Every Type1/Type2 pair, duplicate/None, both presentations/all orders | 2,052 | Pass |
| Rapid/held/reversed Search input, field changes and cancel timing | 192 | Pass |
| 0/5/50/373 seen and uncaught Search fixtures | 144 | Pass |
| Search/Selected returns at nonzero/bank-boundary Listing positions | 36 | Pass |
| Results traversal across every type, presentation and order | 108 | Pass |
| Every second-field Results badge, duplicate/None suppression | 114 | Pass |
| Uncaught and mixed-caught Results fixtures | 36 | Pass |
| Candidate Results pixel latency | 36 | Pass |
| Search runtime, five/50/373 seen | 27 | Pass |
| **Candidate native total** | **5,363** | **0 failures** |
| Prior-prototype Results latency controls | 36 | Pass |
| Host sort/index checks plus new Search/Results structural checks | 18 | Pass |

Results traversal visits all **373 species**, with **3,324** independently
checked visits. Across traversal, badge and caught-flag suites, **47,252**
visible scanouts pair the actual resident frontpic bytes and hardware palette
with the name under the visible cursor. Static cursor/ball artwork, OAM
positions/palettes, badge graphics/palettes, row caught flags, orange gap and
safe portrait-transfer start scanlines are checked separately.
All **5,856** observed live portrait uploads start at LY65-73, after the
portrait's visible rows and within the helper's safe transfer budget.

The Search pair/stress/sparse suites check **189,000** visible compact-icon
scanouts. Combined visible coherence checks total **236,252**. No animation
underruns or premature sampled-cry exhaustion occur in the standard suite.
Native screenshots confirm that Selected-return restores the same Results
layout, while B-return restores Slowpoke and the originating Listing.

The table above and its scanout totals are from the initial Results build.
The intermediate border revision, `build/dex-search-results-20261006c/`, passed
504 focused native cases, 19 host tests and nine captured-screen border/gap
checks. The latest Search header/default review ROM has this qualification:

| Suite | Cases | Result |
| --- | ---: | --- |
| Results traversal, all 373 species, both presentations and all orders | 108 | Pass |
| Search controls, Slowpoke poses, transitions and Selected returns | 144 | Pass |
| Rapid/held/reversed type input, field changes and cancel timing | 192 | Pass |
| Default Bug search with only five species seen and no matches | 24 | Pass |
| Search/Selected returns at nonzero/bank-boundary Listing positions | 36 | Pass |
| Listing/Modes/Unown and Search/reopen integration | 66 | Pass |
| **Focused native total** | **570** | **0 failures** |
| Host sort/index and Search/Results checks | 20 | Pass |
| Native screenshot header/default checks | 18 | Pass |

Results traversal still covers 3,324 species visits and checks 31,643 visible
scanouts. The native checks retain the standard UI attributes and hardware
palette on the portrait bottom and listing corner, as well as the existing
`$53/$69/$6a` corner tiles. Search checks require orange tiles outside the title
on the first two rows, the expected cap/text tiles and standard UI attributes.
The stress suite additionally checks 14,856 compact-icon scanouts.

Eighteen captured Search screens verify the orange top strip, clean fill beside
the title and vanilla cap shapes on entry, after changing to Water/Ice and after
returning from Results, across both presentations and all three orders.
Default initialization is Bug/None; the 24 sparse fixtures also verify its
no-match dialog and clean Search return with only five species seen. No
animation underruns or premature sampled-cry exhaustion occur in the
roundtrip/integration checks.

The original full-suite summaries remain in
`build/dex-search-results-20261006b/`: `popover-qualification/` is the all-species
suite; `integration/`, `modal-qualification/`, `edges/` and `edges-legacy/` hold
shared regressions. The focused corrected-ROM summaries are under the current
review directory: `results-traversal/`, `search-qualification/`, `search-stress/`,
`search-default-empty/`, `search-listing-returns/` and `integration/`.

## Scope And Deferred Work

Official National labels remain independently deferred under `DEX-SEARCH-04`.
They still use internal species numbers. The established Search ranking,
species-data completion and Modern warm-up backlog are not changed here.
Qualification targets the current CGB-only game; no DMG compatibility claim is
added.

## Reproduction

Use the matching private review ROM/save. Open either Modern or Legacy Listing,
then START -> Search. Select Water/Ice and Begin Search. Results should show a
colored portrait, the four-corner green cursor, colored caught balls, two compact
badges and an orange gap under the portrait. Scroll past the fourth result and
back, open a result, visit Info/Moves, B-return, then B-return to Search/Listing.
Repeat under Nat'l Dex and Alphabet ordering. Verify left/right or A cycles the
selector alphabetically, with Bug as its initial value. The space above and
beside the rounded Search title should be orange, with no dark strip or stray
rectangular patch.

To rebuild privately:

```sh
PYTHONPATH=tools python3 tools/build_dex_search_prototype.py \
  --source build/dex-search-investigation-20261006/cursor \
  --output build/dex-search-results-review-copy \
  --jobs 8 --results --prepare \
  --battery build/dex-search-ranked-20261006e/pokecrystal-dex-search.sav
```

Use fresh private outputs, six native workers maximum, and matching symbols.
The headless observers read emulated memory/display state; no diagnostic code
or breakpoints are inserted into the review cartridge.
