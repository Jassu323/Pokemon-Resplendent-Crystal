# Pokedex Ranked Search Prototype

2026-10-06. Private prototype, **not promoted to production**. Search now ranks
both-type matches before Type1-only and Type2-only matches, uses existing compact
OBJ type badges, retains Slowpoke's animation, and includes the qualified Search
page repairs. All 5,069 native qualification cases and 12 host tests pass.

The broader ranking adds modest filtering latency. With all 373 species seen,
the measured first Slowpoke motion is one or two display intervals later than
the preceding repair prototype, depending on the query. Successful Results
reveal is two or three intervals later. No animation or sampled-cry scheduler
changes are included.

## Review Files

Directory: `build/dex-search-ranked-20261006e/`.

- `pokecrystal-dex-search.gbc`: updated review ROM.
- `pokecrystal-dex-search.sav`: matching all-caught review save.
- `pokecrystal-dex-search.sym/.map`: matching symbols and resource map.
- `candidate/`: isolated source used for this build.
- `visuals-modern-final/` and `visuals-legacy/`: native Search, animation,
  Results, Selected-return and Listing-return PNG/PPM captures.
- Qualification, timing and hardware-publication evidence resides in the
  subdirectories listed below. Copies of the accepted preceding prototypes
  are retained separately.

ROM SHA256:
`64aa89bf74d96dcfbf954ae9e8d0fc076aa853a275616ca3a101bb197bf7d8e2`.

Save SHA256:
`7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.

Root production source/output and the installed SameBoy ROM/save were not
replaced. The protected root ROM remains
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`.

## Search Behavior

The three groups are:

1. Species containing both selected types, regardless of their natural order.
2. Species containing Type1 but not Type2.
3. Species containing Type2 but not Type1.

The current Evolves, National or Alphabet order is preserved **within each
group**. Each species appears once. Type2 None is a single-type search; selecting
the same type twice also produces that type's species once, not duplicated
groups. Eligibility remains **seen**, not caught. Unseen species never appear.
There are no extra group-heading/separator rows or Results layout changes.

Example with the review save and Evolves order: Fire/Flying returns 73 species.
Charizard, Moltres and Ho-Oh are first (three both-type matches), followed by
25 Fire-only matches beginning with Cyndaquil, then 45 Flying-only matches
beginning with Pidgey. Flying/Fire retains the same first three, but exchanges
the following groups. Fire/None and Fire/Fire each return all 28 Fire species
once.

### Algorithm And Data Ownership

`PokedexSearch_Filter` classifies the active `wPokedexOrder` in one pass, using
seen flags and direct indirect-table BaseData type reads. Each temporary record
contains a word species ID and a one-byte group. Three inexpensive emission
passes rebuild the active order, update the word result count, and fill the
unused tail with `$ffff`. Empty extents are guarded explicitly.

It does not call `GetBaseData`, allocate transient species IDs, scan all types
through separate expensive filters, or introduce another authored species table.
Changes to species types are read from the actual rebuilt BaseData. Species
expansion follows `NUM_POKEMON`, existing order generation and the checked scratch
capacity; there is no new manually updated Search index. The prototype asserts
that its three-byte records cannot reach the icon metadata at `$dc00`.

The records borrow inactive bank-3 Info/Battle Tower workspace. After emission,
`PokedexInfo_Reset` invalidates the overlapping inactive Info state before a
Selected owner can use it. Search can only be opened from a Listing, so Info,
Moves and Area are not simultaneous owners of this workspace.

## Compact Icons And Publication

Existing `gfx/types/compact/` artwork and palettes are reused through Selected's
compact-type tile mapping. No graphical assets were generated or edited.

Each badge is four 8x8 sprites at screen x88, with Type1 at y32 and Type2 at y48.
OBJ0 belongs to Slowpoke, OBJ1 to Type1 and OBJ2 to Type2. Type2 None retains the
existing `----` BG placeholder and has no visible badge sprites. The existing
white arrow buttons remain unchanged. A DMG text fallback is retained, but
qualification here targets the current CGB game.

Both badges stage into the inactive half of Selected's existing bank-1 OBJ
reservation, tiles `$28..$37`. A Search-local VBlank transaction publishes OAM,
the two palettes, and the BG field placeholders together. The old badge remains
valid while uploads complete; None does not leave a stale icon, and a new type
never appears with the preceding type's palette. The interrupt helper resides
in the same ROMX bank as `Pokedex_VBlankDispatch` and does not use interrupt-unsafe
FarCall scratch.

Search departure cancels pending badge publication and uses the existing
full BG/OBJ hidden transition for Search -> Listing, Search -> Results and
Results -> Search. Destination-owned reveal retains the prior visual repairs;
Search sprites do not bleed into the next screen.

### Repairs Retained

| Defect | Cause | Qualified repair |
| --- | --- | --- |
| Black Slowpoke | OBJ0 inherited the Listing cursor palette | Initialize only its existing party-menu palette |
| Missing Slowpoke/Results outline | Destination retained suspended OAM DMA | Reveal after maps, palettes and OAM are ready |
| Mixed-case heading seams | Window suffixes retained capitals | Matching lowercase Results/Found suffixes |
| Broken Results arrows | Old references point into the Modern two-tile marker | Resident Legacy one-tile arrow, bottom Y-flipped |
| Black cursor cutouts | Old cursor palette assumed a black panel | Results-only existing dark-gray background color |

Detailed original reproductions and alternative repairs remain in
[the investigation](pokedex_search_investigation.md). Green monochrome Results
portraits and white type-arrow boxes are intentional vanilla behavior.
Official National labels remain deferred as `DEX-SEARCH-04`; Regigigas still
prints its internal 373 in National Results rather than official 486.

## Runtime Measurements

Measurements use normal buttons, physical display boundaries and host-only
SameBoy observers. One display interval is 70,224 base-clock ticks, approximately
16.743 ms. Fractional intervals describe the input's position within a physical
frame; they are not CPU-frame counts. The prior control is the private +48-byte
visual repair, not the historically older root production binary.

### Type Field Response

Forty-eight screenshot-based timing cases cover both presentations, all three
orders and four input phases. Measurement is button assertion to the first
changed pixels in the badge/None field, excluding cursor blink.

| Change | First visible ms | Display intervals |
| --- | ---: | ---: |
| Normal -> Fire badge | 13.00-44.47 | 0.78-2.66 |
| Fairy -> None field | 42.30-48.65 | 2.53-2.91 |

These measurements extend the earlier one-to-two-interval estimate: some inputs
become visible in the third display interval. Graphics, palette and OAM still
publish coherently, rather than showing an intermediate badge or blank field.

### Search Button To Results

Representative Evolves-order cases, including the unchanged cosmetic animation:

| Seen / Query | Filter ms (intervals) | First Slowpoke motion ms (intervals) | Complete Results ms (intervals) |
| --- | ---: | ---: | ---: |
| 5 / Grass | 8.31 (0.50) | 165.82 (9.90) | 3,949.67 (235.90) |
| 50 / Grass | 23.71 (1.42) | 182.59 (10.91) | 3,966.44 (236.91) |
| 373 / Grass | 138.37 (8.26) | 299.79 (17.91) | 4,083.64 (243.91) |
| 373 / Water-Flying | 142.42 (8.51) | 299.78 (17.90) | 4,083.63 (243.90) |

| All 373 comparison | Prior control | Ranked/icons prototype | Delta |
| --- | ---: | ---: | ---: |
| Grass filter | 101.11 ms / 6.04 | 138.37 ms / 8.26 | +37.26 ms / +2.23 |
| Grass first motion | 266.35 ms / 15.91 | 299.79 ms / 17.91 | +33.44 ms / +2.00 |
| Grass complete | 4,033.46 ms / 240.91 | 4,083.64 ms / 243.91 | +50.18 ms / +3.00 |
| Water-Flying filter | 122.46 ms / 7.31 | 142.42 ms / 8.51 | +19.96 ms / +1.19 |
| Water-Flying first motion | 283.08 ms / 16.91 | 299.78 ms / 17.90 | +16.70 ms / +1.00 |
| Water-Flying complete | 4,050.19 ms / 241.91 | 4,083.63 ms / 243.90 | +33.44 ms / +2.00 |

Water/Flying now returns 111 species instead of four. Fire/Normal changes from
no results to 82 results, so its no-match-message completion is not comparable
to successful Results completion. The extra successful-handoff interval is
from the full hidden BG/OBJ transition, not an added Slowpoke animation delay.

Across all 27 current timing cases, filtering spans 8.31-142.42 ms, and successful
Results spans 3,949.67-4,098.32 ms. National early-game costs more than Evolves or
Alphabet because its last-seen extent includes unseen gaps: five seen species
scan 156 positions and take about 30.73 ms rather than 8.31 ms. Alphabet compacts
seen entries; all three orders scan 373 positions at full completion.

Slowpoke's 25 seven-frame poses plus 32 resting waits remain **207 frame waits**.
Its 56-byte animation routine is byte-identical to the preceding repair
(SHA256 `7297f2cd64d5cb93b363225e2f8533dca6f3c58acfc4c6517107f6569c8110ba`).
Measured routine spans are 3,451.41-3,460.99 ms because the first wait begins part
way through a physical frame. Every requested pose is independently audited.

## Costs And Risks

Net **+760 ROMX bytes** over the visual-repair prototype, or **+808 ROMX bytes**
over the accepted shifted Options prototype including those +48 repairs.
This is code, not duplicated artwork or another permanent indexed data table.
It fits existing linked banks; no entire ROMX bank is added.

| Resource | Current used | Free in linked space | Net allocation delta |
| --- | ---: | ---: | ---: |
| ROM0 | 15,861 | 523 | 0 |
| ROMX, 186 linked banks | 2,328,210 | 719,214 | +760 versus repair |
| WRAM0 | 4,083 | 13 | 0 |
| WRAMX, seven banks | 23,944 | 4,728 | 0 |
| HRAM | 127 | 0 | 0 |
| SRAM | 49,994 | 15,542 | 0 |

Temporary use: 1,119 bank-3 record bytes plus 39 icon state/OAM bytes in the
48-byte `$dc00..$dc2f` span; 144 bytes of existing WRAM0 graphics/palette scratch
and four existing name-buffer bytes. No new WRAM0, WRAMX or HRAM declaration.

VRAM reuses 16 existing OBJ tiles (256 bytes), with 64 or 128 bytes uploaded per
changed field pair. Slowpoke plus one badge uses 13/40 OAM entries; two badges
uses 17/40, with at most four sprites on any scanline. No BG type-palette slots
are consumed and no scanline-limit overflow was observed.

Complexity is moderate and Dex-local: stable classification is straightforward;
the important engineering constraint is atomic BG/OBJ/palette publication and
explicit ownership of reused scratch. Future Info/workspace expansion must
preserve these lifetimes or move the metadata; Search must not become a
concurrent Selected-page overlay without revisiting ownership. Direct species
type lookup avoids another data synchronization obligation.

## Qualification

Build jobs were capped at eight and native pools at six, with pools run
sequentially to preserve the requested CPU headroom. No cartridge instrumentation,
animation retiming, runtime test RAM patches or asset changes were used.

| Suite / Evidence directory | Cases | Failures |
| --- | ---: | ---: |
| All 342 type pairs x 3 orders x 2 presentations / `ranked-pairs` | 2,052 | 0 |
| Rapid A, held/reversed directions, cursor changes, None wrap, immediate B, pixel timing / `selector-stress-final` | 192 | 0 |
| 0/5/50/373 seen, all uncaught, six queries, all orders/presentations / `sparse-pairs-final` | 144 | 0 |
| Slowpoke poses, fields, dialogs, Results/Selected/Info/Modes/Listing / `search-qualification` | 144 | 0 |
| Search returns at positions 8/9/254/255/256/372 / `search-listing-returns` | 36 | 0 |
| All 373 species x 3 orders x 2 presentations / `popover-qualification` | 2,238 | 0 |
| Modes/Unown/Search/close/reopen integration / `integration` | 66 | 0 |
| Modal input/owner stress / `modal-qualification` | 144 | 0 |
| Sparse/empty Listing/order edges / `edges`, `edges-legacy` | 26 | 0 |
| Search filter/motion/completion timing / `search-runtime` | 27 | 0 |
| Host order/data/cache contracts | 12 | 0 |

The three icon-trace suites audit **185,544 visible scanouts** against actual
VRAM tile bytes, hardware palette bytes, complete OAM rows and BG placeholders.
Ranked results are checked against an independent source-type oracle, including
group ordering, unseen exclusion, duplicate suppression and the final terminator.
All-species qualification verifies frontpic publication, sampled cries,
Description/Info/Moves transitions, internal paging, Listing returns and both
resident mini frames against ROM source data. No animation underrun, premature
sampled-cry cache exhaustion, stale icon graphics or new page corruption was found.

Manual review remains the promotion gate. Native screenshot review shows the
compact badges, restored Slowpoke, correct Results seams/arrows/cursor background,
and normal return screens in both presentations.

## Reproduction And Reconstruction

For manual review, open either Listing, START -> Search, set Fire/Flying and
Begin Search. Inspect the first three entries and the group boundaries after
entries 3 and 28. Repeat Flying/Fire, Fire/None and Fire/Fire. Open a result,
visit Info/Moves, then B through Results and Search back to the originating
Listing position. Repeat from the last Listing entry and with rapid field input.

Build the candidate in a fresh output directory:

```sh
env PYTHONPATH=tools python3 tools/build_dex_search_prototype.py \
  --source build/dex-search-investigation-20261006/cursor \
  --output build/dex-search-ranked-rebuild \
  --jobs 8 --prepare \
  --battery build/dex-search-investigation-20261006/cursor/pokecrystal-dex-search.sav
```

The builder copies that isolated source and installs
`tools/dex_timing/probes/pokedex_search.asm`, with anchored Search dispatch/owner
changes and a four-byte register-safe compact-tile helper. It verifies that root
production ROM/symbol/map hashes remain unchanged.

Run `dex_timing.search_ranked` with fresh `--output` directories for the default
exhaustive pairs, `--stress` and `--sparse` modes; run
`dex_timing.search_qualification` normally and with `--returns`. Standard
`dex_timing.listing_options` actions are `qualify`, `integration`, `modal` and
`edges`, all with `--jobs 6`. Use `dex_timing.search_timing` for the 27 timing cases
and `tools/test_pokedex_sort.py` with `DEX_OPTIONS_BUILD` pointing to the rebuilt
candidate. Keep generated evidence under ignored `build/`.
