# Selected Pokemon Runtime Display Prototype

Review build, 2026-10-12. This prototype replaces generated display graphics
and species display tables on the non-Area Selected Pokemon pages with runtime
work. It reclaims **26,981 bytes of ROMX (26.35 KiB)**, uses **1,643 additional
allocated WRAMX bytes**, and preserves the tested page pixels and content.
Info pages are measurably slower. Production is unchanged; this is not an
approved integration or commit.

The deferred ancestral page is recorded as `DEX-INFO-07` in
[the Selected Dex backlog](pokedex_selected_bug_backlog.md). It is not part of
this implementation.

The subsequent six-way semantic-metadata/restoration/ancestor comparison is
documented in [Selected Display Architecture Comparison](pokedex_selected_architecture_comparison.md).
It supersedes this broad trial for the current architecture decision, without
replacing this historical evidence or integrating either design.

## Review Build And Rollback

- Review ROM: `build/dex-selected-runtime-20261012-v2/pokecrystal-dex-selected-runtime.gbc`
- Copied review battery: the same stem with `.sav`; it is not the player's save.
- Tested source snapshot: `build/dex-selected-runtime-20261012-v2/candidate/`
- Final reproducible source: `build/dex-selected-runtime-20261012-recipe-final/candidate/`
- Candidate SHA-256: `a099ebbf6c649549f4043f5678ba1562a01691d9e86d04831288ac0be7aa6924`
- Baseline commit: `f4182c81fc19a637feffa7b17e8fa01a7d4e77df`
- Baseline SHA-256: `6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac`
- Rollback: `build/dex-selected-runtime-20261012-v2/rollback/` and
  `rollback-source.tar` preserve the original ROM, symbols, allocation map,
  and tracked source.

A clean rebuild from the packaged patch and helpers in
`build/dex-selected-runtime-20261012-recipe-final/` matches the tested ROM, symbols,
and map byte-for-byte. No root gameplay source or production build was replaced.
Unrelated workbook backup changes were left untouched.
The final recipe retains validation-only Selected Moves page/data guards and
corrects the old build-time-composition comment; neither changes the game bytes.

## What Changed

**Info:** stat labels, decimal numbers, bars, names, evolution requirements,
and resident headings are composed from the existing font and source artwork.
There is no linked generated glyph pool, heading bitmap sheet, 256-entry
number/bar table, species display index, forward-evolution display record table,
or precomposed requirement-line table.

Font composition retains the existing sub-tile alignment: normal text uses its
five-pixel phase, stat labels their one-pixel phase, and long requirements use
the existing compact spacing. Native apostrophe ligatures are expanded to retain
the old requirement layout, including `Trade Kings Rock`. Two tiles/glyphs are
processed per admitted job where safe. Headings are composed while the Dex LCD
is off and stored in the same resident font-gap cells.

Forward evolutions are walked from the actual game's evolution records.
A native parent index is built in RAM each time the Dex opens. It replaces the
generated family metadata used to find existing egg-move inheritance. No
evolution links, requirements, or learnsets are changed or invented.

**Selected Moves:** native level-up and egg pointers/counts, actual TM/HM/tutor
compatibility bits, and page counts replace the generated per-species records
and duplicated compatible-machine lists. These small runtime lists are prepared
before the incoming portrait and cry start. The level marker comes from the
existing battle font rather than a separately generated copy.

**Description:** its text already used the native font and authored description
data. There was no duplicate pre-rendered description glyph pool to remove.
Its preparation and return hooks use the new native metadata safely.

**Area:** implementation and map assets are unchanged. Cross-tab, listing,
species, and Area return paths are nevertheless included in qualification.

The inactive atlas may be reused without losing the visible Info page. A
640-byte RAM copy retains atlas B's composed pixels; returning can reconstruct
the needed atlas through the existing upload path, without VRAM readback or a
ROM glyph-source table. Page maps, palette ownership, badge conventions,
queued/canceled input, and portrait/cry scheduling remain in place.

## What Remains

This is not a conversion of the entire Dex animation engine to runtime parsing.
The following are intentionally retained:

- Original source font, type/category icons, minis, palettes, borders, page
  badge art, and the seven actually used source bar tiles. These are source
  artwork, not generated copies of display text.
- A **666-byte move-name pointer index**, shared with the separate Moves Dex
  and Search. There is no second Selected-only copy. Removing that shared
  lookup is a different, broader change.
- Existing portrait animation plans, dictionaries, timelines, and scheduler
  data. Their removal would be an animation-engine project, not removal of
  precomputed Info/Selected Moves display assets.
- Area's generated encounter/map data, explicitly outside this prototype.

Build-time validation still rejects invalid evolution graphs, ambiguous native
parents, unsupported methods, over-limit Info/Selected Moves pages, invalid
move streams, and conflicting egg-family sources. Validation itself does
not consume linked game ROM. Old generated assets are retained in the private
snapshot only as independent regression fixtures; they are not linked into the
review ROM.

## Space Comparison

Allocation-map bytes, not compressed files or source sizes:

| Region | Production | Prototype | Change |
| --- | ---: | ---: | ---: |
| ROMX | 2,340,470 | 2,313,489 | **-26,981** |
| ROM0 | 15,905 | 15,905 | 0 |
| WRAMX | 24,010 | 25,653 | **+1,643** |
| WRAM0 | 4,083 | 4,083 | 0 |
| SRAM | 49,994 | 49,994 | 0 |
| HRAM | 127 | 127 | 0 |

The file remains a fixed-size 4 MiB cartridge image. This reclaims usable
allocated ROM space, across the existing banks; it does not create two wholly
empty contiguous banks or shrink the cartridge image.

| Linked ROM section | Production | Prototype | Change |
| --- | ---: | ---: | ---: |
| Pokedex Info, including its former generated tables | 10,680 | 5,276 | -5,404 |
| Pokedex Info Glyphs and existing fast handlers | 8,929 | 582 | -8,347 |
| Pokedex Moves | 1,734 | 1,726 | -8 |
| Pokedex Moves Index | 14,070 | 666 | -13,404 |
| Font/item private helpers and preparation hooks, net | | | +182 |
| **Net ROMX** | | | **-26,981** |

WRAM bank 3 uses another **217 bytes inside the already allocated Battle Tower
overlay**, ending at `$dc40`; that is not an additional allocated region. All
previous live RAM symbols retain their addresses. Only the workspace end marker
moves. Mutually exclusive temporaries reuse existing mini/line scratch space.

The new bank-5 cache occupies `$d950-$dfba` after the existing listing region:
180 bytes of evolution records, 640 bytes of retained visible atlas pixels,
746 bytes of parents, 16 bytes of stream headers, 57 TM/HM entries, three tutor
entries, and one page-count byte. **69 bytes remain to `$e000`.** Ten additional
species would add 20 parent-index bytes, but future growth must recheck the
allocation assertion. Bank 3 has no spare bytes before the adjacent Search
workspace. No SRAM layout, discovery flags, or save format changes are required.

## Runtime Performance

Fresh native button-input comparisons use matching production/candidate links,
Modern and Legacy styles, four input phases, and both active and settled
portraits. A display frame is about 16.74 ms. Double-speed CPU operation does
not double the LCD refresh rate or eliminate the bounded display-job cadence.

Values below are Modern medians from the sampled case set. Delta is the median
of matched-case differences, which need not equal the difference between two
population medians. Legacy results follow the same pattern.

| Action | Production | Prototype | Paired delta |
| --- | ---: | ---: | ---: |
| Settled Description to Stats | 76.05 ms | 126.10 ms | +50.22 ms, about 3 frames |
| Stats while portrait active | 98.73 ms | 161.93 ms | +66.96 ms, about 4 frames |
| Settled Stats to first Evolutions page | 90.99 ms | 176.80 ms | +83.83 ms, about 5 frames |
| First Evolutions page while portrait active | 102.92 ms | 220.13 ms | +117.18 ms, about 7 frames |
| Settled Description to Selected Moves | 105.59 ms | 105.64 ms | effectively 0 |
| Settled Info-owned species change, complete screen | 126.28 ms | 157.96 ms | +33.48 ms, about 2 frames |
| Settled Info to Modern listing, complete screen | 176.51 ms | 193.53 ms | +16.74 ms, about 1 frame |
| Settled Info to Legacy listing, complete screen | 111.58 ms | 111.88 ms | effectively 0 |
| Area back to Info, complete screen | 142.84 ms | 145.17 ms | effectively 0 median; up to about 1 frame in individual cases |

The largest matched increase in the sampled first-evolution transitions is
133.97 ms, about eight frames, during active portrait playback. Stats' largest
sampled increase is about 83.76 ms. These are not universal worst-case bounds
for all future data, all pages, or physical hardware.

The 1,024-case paired Selected-entry test has near-zero median matched complete
screen delay, with individual cases up to one extra frame. Separate population
medians differ by several milliseconds because different cases straddle frame
boundaries. First-changed-pixel timing can differ more and is not the same as
the time to a complete screen. In particular, early listing-return pixels are
later in the runtime build even when final Legacy-listing timing is unchanged.

Opening/reopening the entire Dex from the start menu is **97.60 ms slower** in
all eight matched style/input-phase pairs: Modern median 738.12 to 835.72 ms,
Legacy 720.53 to 818.13 ms. This includes the normal entry/fade sequence. The
isolated parent-index routine costs about 89.55 ms of double-speed CPU time;
headings plus parent-index construction cost about 98.79 ms before interrupt
overhead. This startup work happens on Dex entry, not every page turn.

The added page delays come from composing pixels over bounded admitted jobs,
not stretching the portrait or cry. The initial naive runtime prototype was
one frame slower on settled Stats; co-locating private font/item readers with
their source data and batching safe work reclaimed that frame without adding
shared interrupt overhead. Further optimization should preserve those timing
and ownership boundaries. Runtime composition is feasible, but it is not free.

## Qualification Results

Fresh evidence for the review SHA is under
`build/dex-selected-runtime-regression-20261012-v2/` and the prototype's
`focused/`, `paired-timing/`, `extra-timing/`, `startup-timing/`, and `type-tests/`.
Overlapping case counts below are not a single additive total.

- **11 runtime unit tests pass**, including every old heading,
  shared stat tile, 256 numeric/bar composites, every evolution text line,
  native traversal/requirements and move streams for all 373 species,
  decimal 0-255, removed-table assertions, RAM bounds, title bank restoration,
  and source validation without emitted display tables.
- **746 all-species Info scenarios pass**, with every actual Info page checked
  at active and settled portrait phases.
- **746 all-species Selected Moves scenarios pass**, with native content/page
  counts, wrap, and return checks.
- **400 Info rapid-input, hold, cancellation, cross-tab, listing, and species
  change cases pass.**
- **4,479 standard Dex scenarios pass**, covering Modern/Legacy sorts,
  popovers, visual interfaces, Selected pages, search ranks/defaults/empty
  results, and mode transitions. Additional prior-Info/prior-Moves Unown
  transitions pass.
- **136 Unown scenarios, 2,212 form selections, and 126 draw units pass.**
- **2,238 portrait playback cases pass**, all 373 species in cold/paging/warm
  paths in both listing styles, with no animation or cry deadline misses.
- **1,600 main paired page/return cases, 544 additional evolution/Moves timing
  cases, 1,024 paired Selected-entry cases, and 16 Dex-reopen cases pass.**
- Separate Moves Dex Search/filter/navigation/visual/cursor/sort-memory/save
  phases pass, including 1,856 naming-cursor rendered cases and negative
  controls that detect the old defects.
- Type Matchups passes on CGB revisions 0/A/B/C/D/E, including all 18 choices,
  palette/raster checks, continuous input, and return ownership. The E run
  includes 42 owner reentries, 12 close/reopens, 24 Selected playbacks, and
  the existing 648 single-type/2,754 dual-type battle-chart checks.
- The 86-test established host suite has **no new failures or errors**. Its
  one `InfoLinkedTests.test_ready_handoff_obeys_the_active_playback_budget`
  failure at synthetic LY 64 (`5 != 0`) is identical on production. It is
  retained as an existing test-contract exception, not silently counted as a pass.
- Shared VBlank, LCD, audio, Type Matchups, and the separate Area source files
  are identical to the baseline archive. The clean recipe rebuild matches.
- The surrounding campaign passes **10 menu, 960 sampled-cry, 22 gameplay,
  two custom-menu, 24 battle-clock transition, and 1,600 battle cases**. The
  latter covers the established 100 moves, both sides, four input phases, and
  both links. All 784 pairs with complete numeric animation-duration records
  match production exactly; the other 16 pairs have identical partial-event
  records but do not provide a complete duration measurement.

Representative native screenshots in the prototype's `review-images/` cover
Stats, ordinary level evolution, trade/item requirements, stat comparisons,
and Selected Moves. Pixel/data oracles compare the runtime output with the
original compiler and authoritative game data, not a second copy of runtime
output. No new graphical assets are needed.

These are emulator and linked-code checks, not a physical cartridge/LCD test.
This trial does not rerun every move-discovery/save-corruption case or the
333-move exhaustive animation campaign; no persistence or shared interrupt
implementation changed. The surrounding gameplay campaign is recorded in
`campaign-logs/gameplay.json` and `acquisition-*-regression.json`.

## Reproduction

The recipe requires the retained fixture batteries/manifests and converted
graphics described in [Full Regression Suite](full_regression_suite.md).
Use fresh output paths; never reuse native CPU checkpoints across links.

```sh
export PYTHONPATH=tools:.
python3 tools/build_selected_runtime_prototype.py --output build/selected-runtime-new --jobs 6
DEX_RUNTIME_SOURCE=build/selected-runtime-new/candidate python3 -m unittest tools.test_selected_runtime_display -v
python3 -m tools.dex_timing.selected_runtime inventory --source build/selected-runtime-new
```

Before the native panel sweeps, prepare matching Modern checkpoints with
`tools.dex_timing.performance --prepare`, targeting
`build/selected-runtime-new/focused/modern/`. Prepare the full-campaign
candidate and baseline separately with `type_full_regression prepare/setup`.
Then use the runtime phases and the standard campaigns listed in the regression
runbook. The old panel audit expects normal speed unless explicitly adapted;
`selected_runtime` supplies the current double-speed policy.

## Review Decision

The ROM saving is real and larger than the originally discussed font-only
estimate because the Selected Moves species/machine tables were also removed.
Manual review should concentrate on Dex entry, Info page turns while the
portrait is playing, long/branching evolution pages, and B-return to the Modern
listing. Production remains the rollback point until those delays and the RAM
tradeoff are accepted.
