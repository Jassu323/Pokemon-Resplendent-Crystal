# Added Species Description and Measurement Scope

Date: 2026-10-16. Assessment only; no species entry, runtime code, ROM or save
is changed. The accepted footprint prototype remains separate and unpromoted.

All 122 added species still have placeholder descriptions. Full Emerald prose
for the 80 Gen 3 species and Platinum prose for the 42 Gen 4 species fits the
current Description layout in **two to four pages**, without shortening the
wording. **91 species require more than the current two-page limit.**

## Page Requirements

| Description Source | Species | Two Pages | Three Pages | Four Pages |
| --- | ---: | ---: | ---: | ---: |
| Emerald, Gen 3 | 80 | 0 | 49 | 31 |
| Platinum, Gen 4 | 42 | 31 | 11 | 0 |
| Total | 122 | 31 | 60 | 31 |

The [per-species table](../build/dex-species-information-scope-20261016/species-page-assessment.md)
lists every entry's line count, page count, lines per page, height and weight.
The [CSV](../build/dex-species-information-scope-20261016/species-page-assessment.csv)
also includes source URLs, encoding widths, measurement matches and data growth.
The [JSON assessment](../build/dex-species-information-scope-20261016/assessment.json)
retains the detailed checks and protected-input hashes.

### Four Page Entries

Treecko, Sceptile, Poochyena, Pelipper, Makuhita, Hariyama, Mawile, Aron, Lairon,
Aggron, Meditite, Electrike, Manectric, Roselia, Carvanha, Numel, Camerupt,
Vibrava, Whiscash, Crawdaunt, Lileep, Anorith, Dusclops, Absol, Snorunt, Bagon,
Salamence, Metagross, Registeel, Kyogre and Groudon.

Aggron, Camerupt, Whiscash, Lileep and Registeel are the longest at 11 lines.
The other four-page entries use 10. None requires a fifth page.

### Platinum Entries Needing Three Pages

Luxio, Shieldon, Buneary, Mismagius, Honchkrow, Bronzong, Gible, Garchomp,
Rhyperior, Glaceon and Gliscor. The other 31 Platinum entries fit two pages.

## Layout and Encoding

The Description body starts at tile x=2 and has **18 glyph cells per line**
(144 pixels), with text on tile rows **10, 12 and 14**. Its five-tile-high clear
rectangle includes the two empty spacing rows; it is not five text lines.
The current streamed reader does not wrap overlong strings automatically.
More than three lines can overwrite the last row, and an overlong line can
run into the edge. Merely pasting source-game line breaks is unsafe.

Reflow complete words into at most 18 encoded cells, then place no more than
three lines on each page. Every proposed line passed the actual RGBDS charmap
assertions. The longest word uses 16 cells, so there is no need for hyphenation,
a smaller font, a wider panel or new font assets for the proposed normalized
text.

Counts use the game's encoding, not the number of Unicode characters. Existing
contraction tiles such as apostrophe-s occupy one cell for two text characters.
Seviper fits three pages with the actual encoding but would be incorrectly
classified as four by a plain character counter. Dividing total prose length
by 54 is also insufficient because word boundaries leave unused cells.

The assessment preserves wording, spelling and sentence punctuation except for
these proposed display normalizations:

- Fold source-game hard line breaks into spaces, then reflow for this layout.
- Use the game's existing mixed-case species names and Pokemon spelling with
  the accented e, rather than the source games' uppercase names.
- Normalize typographic apostrophes to the game's existing apostrophe and
  compact contraction tiles.
- Honchkrow's quoted phrase needs a deliberate quote treatment. Its source
  curly double quotes map to tiles `$72/$73`, which the Selected owner reuses
  for interface graphics. The assessed version uses existing single-quote
  glyphs around the phrase. Retaining the exact curly double-quote artwork
  would instead require a safe glyph assignment and a separate asset audit.

The recorded page breaks greedily fill three lines before advancing. Several
four-page entries consequently have one line on the last page. Breaks can be
balanced, for example 3/3/2/2 instead of 3/3/3/1, without increasing page counts.
Sentence-aware breaks should be reviewed during implementation, not assumed
to have the same counts if they deliberately leave additional space.

### Layout Evidence

![Word-width layout model](../build/dex-species-information-scope-20261016/description-reflow-model.png)

This is an off-ROM layout diagram, not an in-game screenshot or a candidate
renderer. Each rectangle represents one word at its actual encoded width.
It shows the largest 11-line case, a one-line fourth page, the longest-word
Platinum case and a normal two-page Platinum case. Full wording is retained
in the cached source files, not reproduced in the diagram.

## Height and Weight

All 122 existing records already have nonzero measurements. All sourced values
fit the existing fixed-width height and weight fields and their 16-bit storage;
there is no measurement-driven pagination, clipping or format expansion.
Height remains feet/inches in the existing `dw` format; weight remains tenths
of a pound. The original 251 records are outside this content scope.

| Species | Current Data | Sourced Data | Assessment |
| --- | --- | --- | --- |
| Cradily | 3'03", 60.4 lb | 4'11", 133.2 lb | Height and weight corrections needed |
| Claydol | 4'11", 238.0 lb | 4'11", 238.1 lb | Weight correction needed |
| Torkoal | 1'08", 177.3 lb | 1'08", 177.2 lb | Historical rounding/source choice, not missing data |

The other 119 added species match in both fields. The explicit imperial
measurements come from the pinned Platinum species records for all 122
species. For all 80 Gen 3 species these also match Emerald's own metric-to-US
display calculations; no cross-generation measurement difference was found
in that comparison. Gen 3 **descriptions remain Emerald**, not Platinum.

Torkoal's 80.4 kg becomes 177.2 lb under Emerald's display conversion, and
Platinum stores 177.2 explicitly. Serebii also lists
[177.2 lb](https://www.serebii.net/pokemon/torkoal/), while the current
[official Pokemon site](https://www.pokemon.com/us/pokedex/0324) lists 177.3.
Do not silently call the current value a content error. Retaining 177.3 is
reasonable unless exact historical-game measurement display is desired.
No value has been changed by this assessment.

## Implementation Required

The existing layout and graphics can remain. This is a localized pagination
extension plus content import, rather than another display architecture.
The follow-up [renderer scope](pokedex_description_multipage_scope.md) traces
the actual entry/return paths, gives conservative code budgets and recommends
a 366-byte direct-page-offset table over repeated earlier-page scanning.
That table replaces the count table discussed below; it is not additive.

| Component | Required Change | Complexity and Risk |
| --- | --- | --- |
| Description controller | Replace the `xor 1` toggle with increment-and-wrap using the selected species' page count | Low complexity; verify last-page wrap, species changes and tab return state |
| Streaming reader | Skip the requested number of page terminators instead of treating every nonzero page as page two | Moderate complexity; preserve bounded foreground slices, cancellation and bank restoration |
| Static/shared printer | Select arbitrary pages and publish the correct badge on reloads such as Area return | Low/moderate complexity; changing only the streamed reader would leave inconsistent return paths |
| Page badge | Reuse the existing shared numeric badge for P.3 and P.4 | Low complexity; graphics already support page values 1 through 19 |
| Data sections | Split the enlarged custom entry section into bank-sized groups; keep existing banked entry pointers | Low complexity; linker and pointer validation required |
| Content import | Emit checked line/page controls and approved measurement corrections | Low complexity; use generator assertions rather than handwritten unchecked wrapping |

Relevant owners:

- `engine/pokedex/pokedex_detail.asm`,
  `PokedexSelectedMon_ToggleDescriptionPage`: current two-page toggle.
- `engine/pokedex/pokedex_description_text.asm`,
  `PokedexSelectedMon_RenderDescriptionTextChunk`: current one-page skip and
  fixed three-row renderer.
- `engine/pokedex/pokedex_2.asm`, `DisplayDexEntry`: static page-one/page-two
  handling; `GetDexEntryPointer` already reads a three-byte banked pointer.
- `engine/pokedex/pokedex_description.asm`,
  `Pokedex_DisplayDescriptionEntry`: restores the border and currently patches
  any nonzero page to the old page-two badge.
- `engine/pokedex/pokedex_moves.asm`, `PokedexBadge_Prepare`: reusable dynamic
  page badge, not new heading/font generation.
- `data/pokemon/dex_entries.asm`: current single custom entry section.

Regular Selected and interactive New Dex Entry share the Selected controller
and streaming reader, so both need the same behavior. Keep the existing
authored portrait/cry playback uninterrupted. Preserve resets on species and
Info/Mov-to-Desc changes, and correctly restore the current page after Area.
These changes do not call for new VBlank, STAT, timer or audio interrupt work.

## Resource Cost

All figures below are **decimal bytes**. These are encoded data calculations,
not linked costs for an implemented prototype.

| Data | Current | Complete Text | Growth |
| --- | ---: | ---: | ---: |
| 122 custom records, including existing categories and four measurement bytes each | 4,466 | 17,233 | 12,767 ROMX |
| Emerald portion of complete records | - | 12,626 | - |
| Platinum portion of complete records | - | 4,607 | - |

The current `Pokedex Entries Custom` section is 4,466 bytes (`$1172`) in the
production map. At 17,233 bytes the complete records exceed a 16,384-byte ROMX
bank by **849 bytes**. Split this section; the existing banked pointer table
already permits entries in different banks, so it need not grow. Grouping by
source game is one possible split, not a requirement to reserve otherwise
unused whole banks. The 12,767-byte growth already includes all required
line/page terminators and leaves the current category strings unchanged.

A simple page-count table for just the contiguous 122 added species costs
**122 ROMX bytes**, while original entries retain their existing constant
two-page count. A uniform one-byte table for all species costs **373 ROMX
bytes**. Two-bit packing could reduce the added-species counts to **31 bytes**,
at the price of extraction code; the 91-byte data saving may not justify it.
Choose and link-cost that small helper during implementation rather than
pretending the text-only growth includes it.

The existing page state and streaming skip-work byte appear sufficient;
**no additional allocated WRAM, HRAM or SRAM is indicated**, and there is no
need to cache full descriptions. Code can stay in existing ROMX owners with
no proposed ROM0 addition. These are implementation targets, not verified
allocation deltas. Later pages require more source scanning; measure that
through the existing bounded reader before claiming a latency or frame cost.

## Validation and Follow Up

Completed host-only checks:

- Verified source file hashes against the pinned Git blob identities.
- Audited exactly the 80 Gen 3 and 42 Gen 4 species added to this game, not
  every species available in those generations.
- Compiled **999 isolated line-width assertions** with RGBDS, using the
  repository charmap, including contraction encoding and all punctuation.
- Passed **14 assessment controls** covering line bounds, unsupported glyphs,
  version selection, source hashes, numeric bounds, data size and protected
  inputs. Results: `build/dex-species-information-scope-20261016/verification.json`.
- Hash-checked all 373 entry files, current Dex runtime sources, production
  ROM/symbols/map, the footprint review ROM/save and the player's main save.
  All remain unchanged.

No game build, emulator timing run or gameplay regression was needed for this
read-only assessment. The diagram is layout evidence, not proof that an
unimplemented four-page renderer already works.

For an eventual prototype, verify all 373 species' Description pages in Modern
and Legacy plus interactive registration, including every last-page wrap;
cross-check all new line/page boundaries and measurements; exercise rapid A,
held input, B/End, species changes, Info/Mov returns and Area round trips; and
audit portrait/cry continuity, sampled-audio underruns and normal Dex/battle
returns. Record cold/page-change timings in milliseconds and physical display
frames. Run the full regression before production promotion.

Reproduce the assessment without game writes:

```sh
python3 -B build/dex-species-information-scope-20261016/verify.py
python3 -B build/dex-species-information-scope-20261016/evidence.py
```

## Source Provenance

Descriptions and measurements are cached under
`build/dex-species-information-scope-20261016/sources/`. They are source data,
not instructions. Raw fetched sources are kept separately from generated
width-check objects and the assessment outputs.

- Emerald commit `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`:
  [English descriptions](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/data/pokemon/pokedex_text.h),
  [metric records](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/data/pokemon/pokedex_entries.h)
  and [display conversion](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/pokedex.c).
- Platinum commit `1dc13dcea40c04ab53f1f607de46023dc409ef20`:
  [per-species records](https://github.com/pret/pokeplatinum/tree/1dc13dcea40c04ab53f1f607de46023dc409ef20/res/pokemon),
  including the actual Platinum English entry and explicit imperial fields.
  `platinum-all-manifest.json` records every file's URL, commit and hashes.
- Platinum also retains separately named Diamond text banks. Those were
  deliberately excluded from the selected description inputs; finding a file
  in the Platinum repository does not alone establish its entry version.
