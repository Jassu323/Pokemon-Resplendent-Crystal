# Info Return And Evolution Investigation

2026-10-03. Investigation only: no production assembly, evolution data or
cartridge bytes were changed. `DEX-INFO-01/02` remain confirmed.
The user subsequently deferred evolution/species content into `DEX-DATA-02`
for the planned learnset/base-stat/species revision. Shared pagination remains
separate renderer work (`DEX-PAGE-01`); its implementation does not require
adding evolution records. `DEX-INFO-03` is outside this investigation.

Subsequent approved private preflight: the user chose relocating the actually
visible Info-B glyphs into unaliased Info-A storage, retaining the full-cache
Listing rule and outgoing pixels. See the [relocation preflight results](pokedex_info_return_preflight.md)
for its passing return checks, 280-byte ROMX cost, additional 50/151ms latency
and one independently reproduced existing badge-cancellation defect. The
candidate estimates and original recommendation below are historical; the
production ROM still has no return fix applied.

## Provenance And Method

```text
ROM SHA-256: 2928c51263a162d573f4ee96204aca768f83ffb9aff1fe418a7af3de0ee76346
SYM SHA-256: 3c1ee132610963d7f37debd1548b979d1c0a02401bb6930084de195f4136af92
```

The headless SameBoy runner replays matching normal-input Listing checkpoints
and private all-caught battery copies. No live save, species ID, producer
counter or emulated instruction is patched. The diagnostic input cartridges
are byte-identical copies in separate ignored output directories:

- `build/dex-info-investigation-returns`: nine return paths, three repeats each.
- `build/dex-info-investigation-internal`: two retained-Info internal-paging
  paths, three repeats each.
- `build/dex-info-investigation-observer`: observer-off/on controls for three
  Description paths, Info Stats and Info Evolutions.
- `build/dex-info-investigation-analysis`: independent linked-data audit,
  outgoing-frame checks, a fresh all-species runtime pass and comparison image.

All five observer controls have identical cycle counts, state, palette/map
data and final pixels. Forty relevant unit/linked tests pass. The diagnostic
ROM is not a proposed-fix ROM; the candidates below have not been implemented
or replayed. Their implementation byte counts are estimates, not linker results.

## Confirmed B-Return Corruption

### Reproduction

1. Select caught Chikorita from a cold New Dex Listing.
2. Open Info once, leaving its Stats page visible; do not press A again.
3. Press B. The old lower panel acquires minisprite-shaped text/bar corruption
   before the complete Listing replaces it.

Settled playback is sufficient. Representative sampled-cry cases also
reproduce, so an active cry or missed audio deadline is not required.

Further controls isolate the buffer dependency:

- Chikorita Stats corrupts; its first Evolutions page does not.
- Tyrogue P.3 corrupts; Eevee P.4 and Skitty P.2 do not.
- Retain Info and page Chikorita -> Bayleef: B-return is clean. Continue to
  Meganium: B-return corrupts again.
- Chansey and Blissey reproduce, including the extreme-HP endpoint cases.

This is not an absolute odd/even page-number rule. Info alternates glyph
buffers whenever it constructs another page, including a Stats-only wrap.
What matters is whether the currently visible page references atlas B.

### Measured Results

Each row ran three times with the same result. Timing begins at the Leave
routine, not at the first physical button edge. One hardware interval is
70,224 normal-speed T cycles, approximately 16.74ms.

| Outgoing panel | Visible atlas-B references | Corrupted display frames | Leave-to-Listing intervals |
| --- | ---: | ---: | ---: |
| Chikorita Stats | 55 | 11 | 13.177 |
| Chikorita Evolutions P.2 | 0 | 0 | 13.157 |
| Tyrogue Evolutions P.3 | 24 | 12 | 14.164 |
| Eevee Evolutions P.4 | 0 | 0 | 14.165 |
| Chansey Stats | 63 | 12 | 14.179 |
| Blissey Stats | 69 | 12 | 14.177 |
| Skitty Evolutions P.2 | 0 | 0 | 14.165 |
| Dusknoir Stats | 67 | 12 | 14.222 |
| Kyogre Stats | 76 | 12 | 14.196 |
| Info retained, Chikorita -> Bayleef | 0 | 0 | 13.178 |
| Info retained, Chikorita -> Bayleef -> Meganium | 67 | 11 | 13.169 |

Twenty-one of 33 returns expose corruption. The affected frames last roughly
184-201ms; the complete return takes about 220-238ms. All 33 final Listings
are correct, with correct cache bytes, presence flags, used palettes and
subsequent scrolling/re-entry. No palette write is rejected, no white frame
occurs, and the LCD is not disabled for cache repair.

`b-return-comparison.png` in the analysis directory shows Chikorita's intact
Stats page, captured display frame 4 with visible tile replacement, and the
correct final Listing. Image and write-trace evidence agree.

### Cause And Ordering

The 40-cell Info atlas B is exactly the Listing side-icon frame-0 region,
bank 1 `vTiles5 $00-$27` (physical `$9000-$927f`). Its uploads mark the
Listing cache dirty. Atlas A does not overlap that cache region.

The current order is:

1. `PokedexSelectedMon_Leave` cancels Info, records LEAVING, invalidates the
   Listing row tags, cancels cry/prefetch ownership and normalizes the Listing.
2. `Pokedex_InitMainScreen` holds OAM updates and calls
   `Pokedex_EnsureGridCache` before staging the incoming Listing maps.
3. `Pokedex_RepairGridCache` prepares the missing physical rows.
   `Pokedex_UploadPendingGridCacheRow` uploads their side-icon frame 0 first,
   then center OBJ and side-icon frame 1; it publishes each row tag afterward.
4. The complete Listing map, attributes, used palettes, OAM and viewport
   finally publish through the existing owner handoff.

During step 3, the old Info BG map is still visible and still references
atlas B. Hiding the Listing Window at WX=167 does not hide this BG panel.
Cache uploads therefore replace live glyph/bar pixels with minisprite pixels.
The Stats heading survives because it uses separate resident bank-0 cells.

Thus the issue is graphics ownership/publication order, **not** exceeding a
palette-write VBlank budget. Faster uploads alone would shorten, not remove,
the invalid ownership interval.

### Fix Candidates And Recommendation

| Candidate | Expected resources | Complexity / risk | Presentation tradeoff |
| --- | --- | --- | --- |
| Publish a neutral lower-panel mask before borrowing ends | Approximately 150-350 ROMX code bytes; reuse owner-map/attribute and OAM staging; no new ROM0, WRAM0, WRAMX, HRAM or VRAM expected | Low/moderate; preserve banks, borders and upper OAM, cancel unfinished jobs, admit publication safely and wait for completion before cache uploads | Lower body is dark gray during repair; normally zero/one additional display interval is the target, not yet measured |
| Retain Info until an early Listing reveal, defer frame-0 restoration | Several hundred ROMX bytes provisionally; partial-cache validity/phase state may need a WRAMX byte | Moderate/high; scrolling, sparse-seen entries, incomplete rows and canceled returns need new ownership rules | Preserves outgoing content, but initial Listing icon phase/animation must wait for frame-0 restoration |
| Give Info a permanently unaliased second atlas | 40 BG tiles, 640 VRAM bytes, plus allocation/loader changes | High relative to this defect; there is no spare 40-cell BG region | Avoids the repair alias, but displaces other graphics or requires a broader redesign |

Recommend the **Info-local neutral lower-panel mask**. Stop the outgoing cry
and portrait producer first, remove all visible references to the borrowed
atlas and any lower minis/HP endpoint, then acknowledge that publication
before the existing cache repair begins. Keep the portrait/header/type icons
and permanent shell intact; do not add a full-screen white/black flash.

The mask must use known resident background graphics with correct bank and
palette attributes. It must be staged deliberately: an unfinished Info job
may already have changed the owner buffers, so treating those buffers as an
unchanged copy of the visible page is unsafe. Place the operation before
`ClearSprites` erases the upper shadow OAM if the existing type icons are to
remain visible. Avoid redundant masking when the visible page is unaliased.

The mask is a correctness transaction, not a performance optimization of the
13-14-interval repair. Further reducing that repair belongs to `DEX-PERF-02`.
The exact code size and any added latency need an approved private preflight;
these estimates do not establish that the patch has already passed.

### Regression Gap Corrected

The return probe had an extra A after choosing the requested Info page, so
some cases labeled Stats had actually returned from Evolutions. The host
probe now asserts its actual view/page/state before B. Original Description
page-two controls retain their separate A press.

The old acceptance checked the correctly restored final Listing and follow-up
navigation, not every outgoing display frame. The new evidence check compares
the canceled Info body across those frames and independently detects tile
replacement under unchanged atlas-B map references. Both checks are needed;
the passing final Listing never disproved the user's transient corruption.

## Confirmed Missing Evolution Content

### Reproduction And Data Audit

Open caught Treecko, Shinx or Duskull, select Info and press A after Stats
is ready. It wraps to Stats rather than showing an evolution page. Eevee
cycles four total pages containing its five vanilla targets, not Leafeon or
Glaceon. Chikorita and the approved Skitty -> Delcatty link are working
controls.

An independent reader decoded the linked gameplay evolution pointer tables
and all method/target bytes, then followed every linked Info future-stage
list. Across **373 species**, source and linked gameplay tables agree, and
every linked Info list exactly matches its gameplay graph. There are **123
direct evolution records**, all vanilla records plus the approved Skitty link.
Skitty is the **only one of the 122 added species with a nonempty evolution
record**. Many added species are legitimately final/standalone; this does not
mean every empty record needs an evolution.

Representative results from a fresh 373-species, settled-phase headless pass:

| Species | Future targets in the actual game data | Runtime Info pages |
| --- | --- | ---: |
| Chikorita | Bayleef, Meganium | 2 |
| Eevee | Jolteon, Vaporeon, Flareon, Espeon, Umbreon | 4 |
| Treecko / Shinx / Duskull | None | 1 each |
| Rhyhorn | Rhydon, but no Rhyperior | 2 |
| Skitty | Delcatty | 2 |
| Delcatty | None | 1 |

All 373 runtime cases preserve current generated content, mini animation,
type/footprint pixels, exact portrait timelines and sampled block accounting.
They also exercise settled internal Info paging and Description restoration.
This is **implementation-versus-current-data** acceptance, not a statement
that the current data contains every intended family. A shared expected graph
cannot serve as a completeness oracle when its input records are missing.

The separate `FirstEvoStages` family table identifies **67 members unreachable
from their declared lowest stage**. It includes the added starter families,
Shinx/Luxio/Luxray, Duskull/Dusclops/Dusknoir, Trapinch/Vibrava/Flygon and the
new branches on vanilla roots. The complete list is in the generated report.
This table corroborates missing relationships but does not specify their
direct parent, evolution level, item or other requirement.

There is also a related data inconsistency: Delcatty still names itself as
its lowest stage despite Skitty's approved Moon Stone link. This is not the
Info failure's cause, since Info walks actual evolution records, but the
family table should be normalized during the gameplay-data correction.

### Cause

`data/pokemon/evos_attacks_custom.asm` predominantly contains placeholder
`db 0 ; no more evolutions` blocks. Eevee's Kanto block stops after Umbreon;
Leafeon/Glaceon records are absent. Other added branches are similarly absent.

The compiler correctly emits no future targets for those roots, and
`PokedexInfo_PrepareSpecies` computes `1 + ceil(target_count / 2)`. With no
targets the only page is Stats, so A wraps to that page. Caught visibility,
canonical 16-bit species indexing, pointer resolution and rendering are not
the cause of the missing families.

### Fix Choices

| Candidate | Cost / complexity | Risk / recommendation |
| --- | --- | --- |
| Populate real evolution data, regenerate Info | Four ROMX bytes per ordinary direct gameplay edge, five for a stat-comparison edge; eight bytes per unique Info target/method record, two per root-list reference, plus deduplicated rendered names/requirements | Recommended single source of truth. Low renderer risk; medium gameplay-content risk because these changes make the evolutions actually occur |
| Maintain a Dex-only override graph | Similar display ROMX costs plus another content map, generator rules and tests | Does not repair gameplay; could promise an impossible evolution or diverge later. Not recommended merely to hide incomplete data |
| Infer edges from the first-stage table at runtime | Graph work/state and missing requirement information | Cannot determine direct parents or conditions reliably. Not a valid fix |

The straightforward level/item/trade/friendship links using **existing**
methods/items are data edits. The engine currently supports LEVEL, ITEM,
TRADE, HAPPINESS and STAT, not arbitrary location/move/special-method rules.
Several later-generation items are also absent. The intended requirements
therefore need approval; do not silently invent a level, substitute an item
or add a new global evolution method in this UI fix.

For scale, 67 ordinary new edges would be 268 gameplay ROMX bytes and up to
536 distinct Info-record bytes, before root references and rendered glyphs.
That is an illustration, not an exact approved edge count or a full cost.
Glyph growth will likely be the larger component. Existing Info code/tables
have 6,335 free bytes in bank A6 and glyphs/titles have 8,032 in A7. Recompile
and report exact totals once requirements are settled; no ROM0, WRAM0 or
HRAM growth is expected for data-only additions. New global evolution methods
would be a separate, explicitly costed engine change.

### Shared Page Indicator, Including Future Moves

Adding Eevee's two missing branches means seven targets, four evolution
pages and **five total Info pages**. The current generator rejects more than
four pages, and the renderer has only resident P.1-P.4. Extending data alone
would therefore fail the build guard; bypassing it would reference invalid
digit graphics. P.5's upper/lower tiles are distinct from the resident digits.

The user confirms that future Moves learnsets will need more than four pages.
Recommend a **shared buffered page-indicator transaction**, not permanently
allocating two more BG cells for every additional digit:

- Keep the existing fixed P.1/P.2 digits and the editable standalone sheet.
- Repurpose current P.3/P.4 cells `$7b-$7e` as two two-tile buffers.
- Load the next digit into the unreferenced pair using bounded preparation.
- Publish both badge cells with the corresponding complete lower page; never
  overwrite the visible pair before changing its references.
- Integrate that preparation with Info now and expose the same ownership
  contract to future Moves/Area/mode renderers. Page count remains a property
  of each tab, not a hardcoded renderer limit of four.

Estimated shared-helper/integration code: **150-300 ROMX bytes**, plus **160
net ROMX graphics bytes** to extend the existing P.3/P.4 payload through P.9.
Each preparation copies/uploads 32 bytes, with no additional VRAM allocation
or need for OAM text. Existing lower-panel tile scratch is reusable once its
glyph uploads finish. Info can derive its badge-buffer choice from existing
double-buffer ownership; a reusable independent selector may need **one
WRAMX byte**, to be resolved in implementation preflight. No new ROM0, WRAM0
or HRAM should be necessary. These are unassembled estimates.

Complexity/risk is low/moderate: include rapid A, canceled jobs, internal
species paging and Info-to-Desc restoration so a stale digit cannot publish
with a new page. Digit upload must obey the existing portrait/audio admission
and DMA ownership contract. The sheet currently provides single digits only;
pages 10+ still require a wider badge/layout and asset decision, not just a
larger counter. Do not silently wrap a tenth page to a misleading digit.

## Regression Requirements For An Approved Fix

- Re-run all 33 returns, actual requested-page checks, outgoing pixels,
  borrowed-cell write checks, final Listing cache/palettes and scrolling/reentry.
- Add A-to-B cancellation during every Info preparation state, Stats-only
  wraps and different atlas parities, plus visible HP endpoints/evolution minis.
- Verify that a mask never removes upper type icons or corrupts their palettes,
  and separately measure Leave-to-mask and Leave-to-complete-Listing latency.
- Audit intended family completeness independently of the generated Info graph;
  preserve all vanilla conditions and normalize corresponding family metadata.
- Test every evolution page, including Eevee P.5, page wrap and rapid/canceled
  badge jobs. Include uncaught blank pages and current P.1/P.2 Description.
- Re-run all-species cold/internal portrait timing and sampled-cry accounting
  with active lower-page changes. Do not claim a settled test closes INFO-03.
- Check actual gameplay evolution requirements when adding records; a correct
  display of an incorrect game requirement is still a content regression.

## Reproduction Commands

```sh
PYTHONPATH=tools python3 -B -m dex_timing.listing_restoration \
  --checkpoints build/dex-info-placement \
  --output build/dex-info-investigation-returns \
  --case chikorita-info1 --case chikorita-info2 \
  --case tyrogue-info3 --case eevee-info4 \
  --case chansey-info1 --case blissey-info1 \
  --case skitty-info2 --case dusknoir-info1 --case kyogre-info1 \
  --repeat 3 --follow-up

PYTHONPATH=tools python3 -B -m dex_timing.listing_restoration \
  --checkpoints build/dex-info-placement \
  --output build/dex-info-investigation-internal \
  --case chikorita-info-down1 --case chikorita-info-down2 \
  --repeat 3 --follow-up

PYTHONPATH=tools python3 -B -m dex_timing.listing_restoration \
  --checkpoints build/dex-info-placement \
  --output build/dex-info-investigation-observer \
  --case chikorita-info1 --verify-observer

PYTHONPATH=tools python3 -B -m dex_timing.info_investigation \
  --returns build/dex-info-investigation-returns \
  --returns build/dex-info-investigation-internal \
  --runtime build/dex-info-placement \
  --output build/dex-info-investigation-analysis --jobs 8

PYTHONPATH=tools python3 -B -m unittest \
  tools/test_listing_restoration.py tools/test_dex_info_investigation.py \
  tools/test_pokedex_info.py
```

The runtime runner uses matching checkpoints; regenerate them with `info_ui`
after a production ROM/symbol change. The reports intentionally retain the
known baseline return failures; they are evidence, not a green fix acceptance.
