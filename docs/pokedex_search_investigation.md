# Pokedex Search Investigation

2026-10-06. Investigation and isolated repair trial, **not promoted**. The
accepted Modern/Legacy Options prototype and production source/output are
unchanged. Compact Search type icons are scoped below, not implemented.

The subsequent [ranked Search prototype](pokedex_search_ranked_prototype.md)
implements the user's expanded ranking and compact icons, retains these visual
repairs, and qualifies the combined private build. The estimates below remain
the historical investigation; measured final costs/timings are in that report.

## Controls And Method

- Current baseline: `build/dex-options-modern-shift-final-20261006/`, including
  both Listing presentations, three generated orders and the accepted Modern
  Sort popup's 3px shift.
- Repair candidate: `build/dex-search-investigation-20261006/cursor/`.
- Vanilla: the existing fresh local-master build in
  `build/dex-sort-scope-20261005/vanilla/`, from local pokecrystal commit
  `5beda23ffa505f62e1dad7e3d7c214d1737b3358` (2026-09-29). Its Search routines
  were compared directly against `~/Documents/GitHub/pokecrystal`.
- Historical production control: root `pokecrystal.gbc/.sym`. These compiled
  artifacts predate the current Legacy/Modes source changes; they lack the
  presentation symbols. They are not treated as an up-to-date build of HEAD.

Normal button inputs and isolated battery copies drive the SameBoy headless
runner. The host observer reads CPU routine boundaries, actual hardware OAM,
hardware palettes, VRAM, maps, attributes and physical display boundaries;
it does not patch emulator ROM/RAM to manufacture a successful screen.
Checkpoints are recreated for each candidate's matching symbols. Native
screenshots are emulator captures, not newly generated graphical assets.
Parallel native testing is capped at six workers; builds use at most eight
jobs, following the user's 80% headroom request.

## Confirmed Findings

### 1. Slowpoke Inherits The Listing Cursor Palette

Reproduction: open the historical production Dex, press START, and observe
Search. Slowpoke is black. In the current private Options build, open
START -> Search; the separate suspended-OAM fault below hides it completely.
Releasing OAM alone in an isolated control makes the black Slowpoke visible.

`engine/gfx/cgb_layouts.asm:_CGB_PokedexSearchOption` initializes BG0 but does
not initialize OBJ0. Vanilla relies on the preceding Dex owner having installed
the party-menu OBJ palettes. Our Listings instead install their cursor palette.
`Pokedex_ApplyUsualPals` maps OBJ0 through `$e0` (indices 0,0,2,3), turning that
inherited palette into four black colors. Slowpoke's nine sprites all use OBJ0.

The 880 resident Slowpoke graphic bytes match their decompressed ROM source
in every capture. This is palette ownership, not damaged graphics or a failed
VRAM upload. The intended vanilla Search graphic is red with pale edging; it
does not use Slowpoke's pink species-frontpic palette. The project's party
red is slightly different from vanilla's existing red tuning.

Recommended trial: initialize **only OBJ0** from existing `PartyMenuOBPals`
inside the Search/Modes layout, then use the existing palette publication.

| Option | Cost | Complexity / Risk | Tradeoff |
| --- | --- | --- | --- |
| Load the one owned palette | +9 ROMX bytes; 8 palette bytes copied; no new memory | Low | Explicit ownership; leaves the other seven OBJ palettes alone |
| Call `InitPartyMenuOBPals` | +3 ROMX bytes; 64 palette bytes copied; no new memory | Low, wider side effects | Saves six code bytes but resets palettes Search does not own |
| Give Slowpoke a new species palette | New palette/appearance decision | Unnecessary for this defect | Does not restore the established vanilla presentation |

The single-palette repair is recommended and included in the trial. Sharing
this layout with Modes is safe in the tested paths; its text cursor is BG,
not dependent on the former Listing OBJ0 palette.

### 2. Search And Results Never Release Suspended Sprite DMA

Reproduction in either private Listing presentation: START -> Search shows
no Slowpoke. Begin a Normal search; Results lacks the green selection outline.
Open a result, visit Info, then B-return to Results: the outline is still
missing. B-return again to Search leaves its sprites missing too. The last
return defect also reproduces with the historical production control.

`PokedexListing_BeginMenuTransition` deliberately stages hidden content with
`hOAMUpdate = TRUE`, which **suspends** OAM DMA. Modes and Unown release that
state using `PokedexListing_RevealMenu`. `Pokedex_InitSearchScreen` and
`Pokedex_InitSearchResultsScreen` did not. Shadow OAM is correct while hardware
OAM remains empty/stale.

Recommended trial: invoke the existing reveal helper at the end of **each
destination initializer**, after map/attribute/palette preparation. Cost:
two six-byte far calls, **+12 ROMX bytes**, no new storage. Each call waits one
display interval before advancing to input-ready; that wait publishes the
already-prepared OAM rather than extending the Slowpoke animation.

Unfreezing earlier in the departing owner would be a smaller edit but can
expose intermediate sprites/maps. Changing the global DMA policy would have
much greater scope. Destination-owned reveal is low complexity and consistent
with the accepted stage-and-reveal architecture.

### 3. Results Heading Crosses A Mixed-Case BG/Window Seam

Reproduction: Begin a successful search. Current Results reads
`Search REsults` and, for the Normal all-caught fixture, `54 FounD!`.

The BG strings were modernized to mixed case, but
`engine/pokedex/pokedex_3.asm:DrawPokedexSearchResultsWindow` retained the
capitalized Window suffixes `Esults` and `D!`. Vanilla's all-capital headings
hid this split. Changing the two suffixes to `esults` and `d!` fixes the seam.
**Zero byte/runtime/resource delta**, trivial complexity and low risk.

### 4. Results Uses Half Of The Modern Two-Tile Arrow

Reproduction: Begin any successful search and inspect the top/bottom markers
of its four-row list. The old `$3f`/`$40` one-tile references now point into the
Modern two-tile marker, producing incomplete arrow shapes.

Recommended trial: use the already-resident user-authored Legacy one-tile
arrow, BG bank0 tile `$7e`, and Y-flip it for the bottom marker. Draw the Window
before its existing attribute upload so the flip is published to the correct
Window map. No extra transfer is introduced. **+5 ROMX bytes**, no new asset,
VRAM or RAM. Low complexity/risk; both presentations and all sort orders pass.

### 5. Results Cursor's Black Gaps Clash With The Dark Gray Panel

Reproduction: inspect the green outline around a result. Black rectangles
appear at its gaps/caps. They were invisible against vanilla's black panel.

Recommended trial: after loading the existing green cursor palette, replace
only its color3 with existing `PokedexListDarkGray`, and only for Results
initialization/update states. The outline's green and geometry stay unchanged.
**+22 ROMX bytes**, no new palette asset or memory. Low complexity/risk;
the guarded non-Results path retains its original colors. The shared layout
does execute a small additional state check, not a display-frame wait.

### 6. National-Sorted Results Print Internal Species IDs

This is confirmed but **not changed in the repair trial**. On 2026-10-06 the
user deferred official National IDs to a later pass. It is tracked separately
as `DEX-SEARCH-04`, not a prerequisite for the current Search repairs/icons.

Reproduction with the all-caught fixture: choose Nat'l Dex, open Search,
leave Type1 Normal / Type2 None, Begin, and scroll to the last result.
Regigigas prints **373**, not National **486**. Other examples include
Lopunny 345/428, Lickilicky 363/463 and Porygon-Z 372/474.

`Pokedex_PrintNumberIfOldMode` prints the permanent internal species index.
Vanilla could assume that index equaled the National number; appended species
break that assumption. Generated order/content remains correct. Modern and
Legacy main Listings do not display this number column. The Selected page
also uses project numbering, so a decision about that page is separate rather
than silently broadening this repair to every number consumer.

| Direction | Estimated cost | Complexity / Risk | Tradeoff |
| --- | --- | --- | --- |
| Generated appended-species National map | 122 x 2 = 244 data bytes, roughly 20-40 lookup-code bytes in ROMX; no new RAM | Low/moderate; confirm intended numbering | O(1) lookup, derived from existing National constants; no manually maintained second species table |
| Full generated map | 373 x 2 = 746 data bytes plus lookup code | Low | Simpler uniform lookup; greater data cost |
| Remove Results number column | Little/no added code | Low technical risk, visible design change | Omits a vanilla Old-mode element rather than making it accurate |

Recommend the generated appended-species map if Results should show true
National numbers. No gameplay or deferred evolution/species content needs
editing. Runtime should be negligible relative to existing text printing;
that estimate has not been benchmarked or implemented.

## Intentional Differences From Vanilla

Mixed-case text and dark gray backgrounds are current project styling, not
corruption. The type-field arrow buttons are white boxes with black arrows
in vanilla too. Results' green monochrome frontpic is also explicit vanilla
behavior (`wCurPartySpecies = $ff` before its layout), not another stale
Slowpoke palette. Colored Results portraits would be a separate design change.

## Trial Costs And Qualification

The first five repairs total **48 ROMX bytes** over the accepted private
Options build. No ROM0, WRAM0, WRAMX, HRAM, SRAM or VRAM allocation changes.
No new graphics, animation-script, animation-scheduler or sampled-cry changes.
The first isolated combined trial cost 26 bytes; the final 48-byte candidate
additionally fixes the Results cursor background mismatch.

| Resource | Final candidate used | Free | Repair delta |
| --- | ---: | ---: | ---: |
| ROM0 | 15,861 | 523 | 0 |
| ROMX, 186 linked banks | 2,327,450 | 719,974 | +48 |
| WRAM0 | 4,083 | 13 | 0 |
| WRAMX, seven banks | 23,944 | 4,728 | 0 |
| HRAM | 127 | 0 | 0 |

Final candidate qualification is recorded in its generated summaries. The
Search-specific suite checks all 25 requested Slowpoke poses in hardware OAM,
all 18 Type1 choices, all 19 Type2 choices including None, wraparound,
single/dual/no-match filters against an independent species-type oracle,
Results navigation, Selected/Info roundtrips and Listing restoration. It runs
both presentations, three orders, four input phases and six route variants.
The broad suite checks all 373 species in both presentations and all orders,
plus Modes/Search/preference roundtrips, modal stress and sparse/empty lists.

| Final candidate suite | Cases | Failures |
| --- | ---: | ---: |
| Search ownership/content/poses/returns | 144 | 0 |
| All 373 species x three sorts x two presentations | 2,238 | 0 |
| Modes/Search/reopen integration | 66 | 0 |
| Modal/input stress | 144 | 0 |
| Sparse/empty Listing edges | 26 | 0 |
| **Native total** | **2,618** | **0** |
| Host ordering/prototype tests | 12 | 0 |

No new failures or animation/sample-cache miss events were detected in these
cases. Final evidence is in `search-qualification/summary.json`,
`listing-qualification/summary.json`, `integration/summary.json`,
`modal-qualification/summary.json`, `edges/` and `edges-legacy/` under the
final candidate. These do not claim to sign off the unimplemented icons or
National-number mapping.

A paired entry capture measured first visible response at **47.664ms /
2.8469 display intervals** in the accepted prototype and **47.674ms / 2.8475
intervals** in the final 48-byte repair, effectively unchanged. This is one
matched input phase, not a worst-case latency distribution. The repair adds
one interval before the input-ready boundary, but restores sprites that the
baseline never published. Its last visible update was 215.101ms / 12.8475
intervals versus 231.834ms / 13.8469 in the baseline. That must **not** be
advertised as an apples-to-apples completion speedup: the baseline's final
picture is missing content. Physical intervals are 16.7427ms, approximately
59.7275Hz. Search's existing authored pose sequence and pauses are unchanged;
the fixes restore their publication. Raw measurements are in
`baseline-timing/entry-timing.json` and `final-timing/entry-timing.json` under
the investigation root.

## Compact Search Type Icons

This feature is feasible with **existing** 32x8 compact artwork under
`gfx/types/compact/`, four 2bpp tiles / 64 bytes per type, and existing type
palettes. No new or modified image assets are required. Keep the Type1/Type2
labels, field positions and controls; replace only the selected raw type
names. Type2 None keeps its existing dashed placeholder. Type1 cannot be None.
Search Results' filter labels are not automatically included in this scope.

The selector's 1-18 enumeration must go through
`PokedexTypeSearchConversionTable`; it is not the actual type constant.
Both fields must render independently even when their selected types match.
The whole Selected-page type routine cannot simply be called because it
fetches species data and suppresses duplicate second types.

### Recommended: Reuse The Existing OBJ Type Buffers

- Reuse Selected's bank1 tile `$28-$37` double buffer: 16 tiles / 256 bytes
  **already allocated**, no new permanent VRAM footprint.
- Two badges require eight OAM entries. With Slowpoke's nine, the screen uses
  **17 of 40**. Badges on y32/y48 do not overlap Slowpoke on y88-111, so this
  layout uses at most **four sprites per scanline**, below the ten limit.
- Reserve OBJ0 for Slowpoke and OBJ1/2 for the two badges: three of eight
  palettes. Preserve badge slots 9-16 when Slowpoke redraws its first nine.
- Extract/reuse the existing compact-tile remapping helper without changing
  global sprite ownership. Prepare inactive tiles, then publish the palette
  and new OAM tile IDs coherently through the existing VBlank ordering.
- Reuse 128 bytes of existing inactive Dex scratch and a few inactive
  Search/popup state bytes, after auditing their owner lifetimes. Target
  **zero net new WRAM0/WRAMX/HRAM**; do not consume the remaining scarce WRAM0
  merely for convenience.
- Estimated code cost **0.4-0.8 KiB ROMX**, no duplicated type graphics and no
  expected ROM0 additions. One field uploads 64 bytes; initial two-field setup
  uploads 128 bytes. Target response **one to two display intervals,
  16.7-33.5ms**, to be measured in an actual icon prototype, not a result of
  this repair trial.

Complexity is moderate, risk low/moderate. Important edge cases are None,
duplicate types, rapid direction changes, all Slowpoke poses, the no-match
dialog and cleanup when entering Results, Listings or Selected. Explicitly
reclaim buffer/palette ownership and clear stale badge OAM on departure. This
reuses a tested icon publication mechanism without scheduling cries/frontpics
on the Search page.

### Alternative: BG Badges

BG also fits: BG0 for the interface plus BG1/2 for the icons, three of eight
palettes and no added OAM. Borrow eight inactive Info tiles / 128 bytes;
double buffering would use 16 tiles / 256 bytes and up to four badge palettes
plus BG0. Estimated **0.5-1 KiB ROMX**, with no net new RAM if scratch is reused.

The extra work is coherent tile/attribute/palette publication. Existing full
attribute uploads can block for four intervals, and palette-first updates can
temporarily recolor an old icon. A small Dex-local publication path or hidden
field update can solve that, but must be measured. Inactive Info-atlas ownership
also needs invalidation on departure. Both approaches are reasonable; OBJ reuse
is recommended because the existing Selected double-buffer mechanism already
solves most of the publication problem and scanline pressure is comfortably low.

Icon qualification should cover every type pair/None, rapid controls at varied
display phases, all 25 Slowpoke poses, no-match and successful searches,
Selected/Info/Listing roundtrips, sparse saves, hardware tile/palette ownership
and visible-response timing. Do not preload all 18 icons or introduce a second
manually maintained type table.

## Search Algorithm And Runtime Follow-Up

Measured 2026-10-06 on the exact 48-byte repair candidate, in double speed.
These are **Begin Search to outcome** measurements, not the earlier popup to
Search-screen entry measurements. No runtime/animation changes were made for
this audit. Read-only host instrumentation was added and retained in
`tools/dex_timing/search_timing.py`.

### Filtering

`Pokedex_SearchForMons` filters the existing active `wPokedexOrder` in place.
It does not alphabetize or run a comparison sort:

1. Translate selector values to actual type constants using the existing
   Search conversion table.
2. If Type2 is non-None, filter by Type2 first; then filter by Type1.
3. Each pass walks `wDexListingEnd` slots, ignoring zero/`$ffff` entries and
   species not marked **seen**. Caught status is not required.
4. Read both types directly through the species' BaseData indirect pointer.
   This avoids `GetBaseData` and its transient species-ID conversion/collection
   work. A match against either natural type slot is sufficient for that pass.
5. Write surviving permanent species indices back from the start of the same
   buffer, count matches, and fill the unused tail with `$ffff`.

Two selectors are an **intersection**: a Water/Flying search requires both
types, in either natural order. Selecting the same type twice still works,
but performs two passes. Original Evolves/National/Alphabet order is preserved.
The second pass still loops over the original listing extent, although the
first pass's discarded entries are now cheap sentinel skips. Filtering is
linear in that extent (up to two passes), with no separately allocated result
list. The selected generated order is restored when leaving Results or after
an unsuccessful search.

Evolves/National retain unseen gaps through the last seen position; Alphabet
already compacts to seen entries. Thus identical completion percentages can
have different scanned extents. For this fixture's first five Evolves entries,
National scans 156 slots, not five; expensive BaseData reads still apply only
to the seen surviving candidates.

### Deliberate Delay And Results Preparation

Filtering completes **before** `AnimateDexSearchSlowpoke` begins. The animation
is cosmetic, not background filtering or a progress indicator. Its script
requests 25 poses held for seven frames each, followed by a 32-frame resting
pose: **207 frame waits**, about **3,466ms**. Actual measured function spans
were 3,459-3,465ms, depending on entry/display phase; the first wait can finish
within an already-started physical interval.

The initial animation pose matches the existing idle pose, so it does not
provide immediate changed pixels. Filtering, input acceptance and that first
hold contribute to the measured first-motion latency.

Successful Results setup then builds the four-row BG/Window maps, frontpic,
type/count labels, palettes and selection OAM. The initializer takes about
**418-436ms / 25-26 intervals** in these samples. From animation return until
the final visible Results picture, including state dispatch and publication,
the total is **451-467ms / 27-28 intervals**.

### Measured Latencies

Each cell below is **milliseconds / physical display intervals**. Inputs are
ordinary A presses on Begin Search; completion means the final stable Results
picture, not merely that the routine computed the match count.

| Seen | Sort | Query / matches | Filter only | First Slowpoke movement | Final visible Results |
| ---: | --- | --- | ---: | ---: | ---: |
| 5 | Evolves | Grass / 3 | 2.91 / 0.17 | 165.88 / 9.91 | 3,932.99 / 234.91 |
| 5 | National | Grass / 3 | 13.49 / 0.81 | 163.83 / 9.79 | 3,930.94 / 234.79 |
| 5 | Alphabet | Grass / 3 | 2.91 / 0.17 | 165.89 / 9.91 | 3,933.00 / 234.91 |
| 50 | Evolves | Grass / 3 | 13.44 / 0.80 | 165.90 / 9.91 | 3,933.00 / 234.91 |
| 50 | National | Grass / 3 | 23.59 / 1.41 | 180.58 / 10.79 | 3,947.69 / 235.79 |
| 50 | Alphabet | Grass / 3 | 13.42 / 0.80 | 163.83 / 9.79 | 3,930.94 / 234.79 |
| 373 | Evolves | Grass / 37 | 101.11 / 6.04 | 266.35 / 15.91 | 4,033.46 / 240.91 |
| 373 | National | Grass / 37 | 101.11 / 6.04 | 266.35 / 15.91 | 4,033.46 / 240.91 |
| 373 | Alphabet | Grass / 37 | 101.11 / 6.04 | 264.29 / 15.79 | 4,048.14 / 241.79 |
| 373 | Evolves | Water/Flying / 4 | 122.46 / 7.31 | 283.08 / 16.91 | 4,050.19 / 241.91 |
| 373 | National | Water/Flying / 4 | 122.46 / 7.31 | 283.08 / 16.91 | 4,050.19 / 241.91 |
| 373 | Alphabet | Water/Flying / 4 | 122.42 / 7.31 | 281.03 / 16.79 | 4,048.14 / 241.79 |

No-match queries still play the entire animation. All-seen Fire/Normal takes
about **122.56ms / 7.32 intervals** to reject all candidates, but the visible
failure message arrives only at **3,663-3,665ms / 218.8-218.9 intervals**.
The message function then intentionally waits 128 frames (about 2,143ms)
before restoring Search. That additional message timeout is an authored
wait, not included in the visible-failure numbers.

The follow-up ran **27 cases, zero failures**: 5/50/373 seen, all three sorts,
and Grass, Water/Flying and Fire/Normal queries. Saves clear later seen/caught
flags in authored Evolves order; these are controlled fixtures, not a claim
that every natural five-species save has the same extent or timings. These
are representative phases/queries, not exhaustive worst-case bounds. Six
native workers were used; production and candidate ROM bytes are unchanged.

The main opportunity for reducing the multi-second wait is shortening the
cosmetic Slowpoke sequence. Filter optimization can still recover several
intervals and improve initial responsiveness in a complete Dex, but it alone
cannot remove the roughly 3.47-second authored delay. Results preparation is
a second, separately measurable component; none of these changes is being
implemented automatically by this timing follow-up.

Full routine spans, display hashes and input/outcome timestamps are retained
in `build/dex-search-investigation-20261006/search-runtime/summary.json` and
the individual case JSON/log files. Reproduce with a fresh output:

```sh
PYTHONPATH=tools python3 -m dex_timing.search_timing \
  --source build/dex-search-investigation-20261006/cursor \
  --output build/dex-search-runtime-new --jobs 6
```

## Review Files And Retained Evidence

- ROM: `build/dex-search-investigation-20261006/cursor/pokecrystal-dex-search.gbc`.
- Matching private all-caught save:
  `build/dex-search-investigation-20261006/cursor/pokecrystal-dex-search.sav`.
- Search/Results native captures: `cursor-captures/` under the investigation
  root; vanilla equivalents in `vanilla/`. `production-return/`, `modern/`
  and `reveal-captures/` preserve the independent black-palette/DMA controls.
- Numbering evidence: `national-captures/results-last-4x.png` and
  `national-captures/captures.json` (window text, selected index and count).
- Hardware palettes, OAM, maps, attributes and graphic comparison are retained
  in each capture directory's JSON files. These are observations, not repaired
  emulator state.

Final ROM SHA256:
`7517f316670e7edeb5fbd70c40fce87a2af8291357b55da399e8d5caa7009df4`.
Review save SHA256:
`7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce`.
Accepted baseline ROM remains
`376d0cb36db62d2f59ca72ac7d99ba1d4b22101249ba21a8121946163d0df707`.
Root production ROM remains
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`;
its `.sym/.map` also remain unchanged. Installed SameBoy ROMs/saves were not
replaced. The review ROM has the first five fixes, **not** compact type icons
or the National-number mapping.

## Reconstruction

Use a fresh private output name, not an existing capture directory:

```sh
PYTHONPATH=tools python3 tools/build_dex_search_probe.py \
  --source build/dex-options-modern-shift-final-20261006 \
  --output build/dex-search-review-new --variant cursor --jobs 8 --prepare \
  --battery build/dex-options-modern-shift-final-20261006/pokecrystal-dex-options.sav
PYTHONPATH=tools python3 -m dex_timing.search_qualification \
  --source build/dex-search-review-new --jobs 6
PYTHONPATH=tools python3 -m dex_timing.listing_options qualify \
  --output build/dex-search-review-new --jobs 6
PYTHONPATH=tools python3 -m dex_timing.listing_options integration \
  --output build/dex-search-review-new --jobs 6
PYTHONPATH=tools python3 -m dex_timing.listing_options modal \
  --output build/dex-search-review-new --jobs 6
PYTHONPATH=tools python3 -m dex_timing.listing_options edges \
  --output build/dex-search-review-new
DEX_OPTIONS_BUILD=build/dex-search-review-new PYTHONPATH=tools \
  python3 -m unittest discover -s tools -p test_pokedex_sort.py
PYTHONPATH=tools python3 -m dex_timing.search_palette \
  --source build/dex-search-review-new \
  --output build/dex-search-review-captures --measure
```

Run native pools sequentially, not concurrently, to retain six-worker headroom.
The builder applies the repairs only inside the copied candidate and verifies
root production outputs. A fresh `reconstruction-final/` build reproduced the
final candidate's ROM hash byte-for-byte. All generated orders still come
from the accepted Options build's existing generated manifest; no gameplay
data is changed.
