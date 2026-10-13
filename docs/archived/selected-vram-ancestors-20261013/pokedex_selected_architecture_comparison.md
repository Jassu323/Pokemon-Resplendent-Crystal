# Selected Pokemon Display Architecture Comparison

Private review prototypes, 2026-10-12. This comparison retains semantic ROM
metadata while generating Selected Pokemon display pixels at runtime. Each
restoration architecture is built both without and with the proposed
"Evolves from" pages. Production has not been integrated, staged, or committed.

## Findings

- Retaining semantic metadata removes the large new parent/evolution/Moves
  caches from the earlier broad runtime prototype. The retained-buffer trial
  needs **640 allocated WRAMX bytes**, not 1,643; both buffer-free trials need
  **zero additional allocated WRAMX bytes**.
- Runtime display composition still costs display frames compared with
  production. Double-speed CPU operation does not double LCD refresh or remove
  the bounded job cadence. Semantic metadata fixes the unnecessary parent
  startup work; it does not eliminate pixel-composition work.
- The new ancestor feature costs **2,108 ROMX bytes** in the RAM and VRAM
  architectures, with **no additional WRAMX allocation**. Its heading needs
  a temporary, reversible 208-byte VRAM reuse, not a new persistent buffer.
- ROM restoration reintroduces generated glyphs and recovery vectors. With
  ancestors, its net ROMX allocation is **12,139 bytes above production**.
  That is not a useful space-saving solution merely because it saves RAM.

The recommended space-conscious architecture is semantic metadata plus VRAM
restoration, subject to manual acceptance of the measured Info page latency.
Retain the 640-byte buffer if its particular return-path timing tradeoff is
preferable. Do not choose ROM restoration solely to improve speed: compare its
actual frame results, not just its cheaper raw memory reads.

## Frozen Builds

All six builds use baseline commit
`f4182c81fc19a637feffa7b17e8fa01a7d4e77df` and copied review batteries, not the
player's active save. Each directory includes the source snapshot, allocation
map, symbols, build log, input manifest, rollback ROM, and source archive.
Review ROM filename: `pokecrystal-dex-selected-runtime.gbc`.

| Architecture | Without ancestors | With ancestors |
| --- | --- | --- |
| RAM buffer | `build/dex-selected-semantic-ram-20261012-v5` | `build/dex-selected-ancestors-ram-20261012-v8` |
| VRAM recovery | `build/dex-selected-semantic-vram-20261012-v1` | `build/dex-selected-ancestors-vram-20261012-v6` |
| ROM recovery | `build/dex-selected-semantic-rom-20261012-v2` | `build/dex-selected-ancestors-rom-20261012-v7` |

Candidate ROM SHA-256 values, in the same table order:

```text
RAM without  5ce9b066b282d053c2a08b3c39e31c7f2f3ce6042c8dc1e4d24055fec5f22e8d
RAM with     5e3e61bb4dfd5fdd5592a01b42f89ef429ec138e88193b964725596b2980a4d6
VRAM without 78268be0c11fb3ea56a6fa085630642feec996f1377a2468150f2f391085010d
VRAM with    07bec143ad5138fed762476fdc8df9bd8f57011e121b6d4b1cbf1d5b4efb23d2
ROM without  e6595fc7a18ecaa5f9ff2e40c8e56db75e39b47fbee9f9049678352bf9520562
ROM with     099009dfab1ef6f28d0b73ac95586e50644f0646e40f8adb0bd3f5e36bbbc504
```

The fresh production timing control is
`build/dex-selected-production-control-20261012-v1`. Its ROM SHA is
`6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac`.
The three without-ancestor recipes also rebuild byte-identical review ROMs in
`build/dex-selected-semantic-{ram,vram,rom}-recipe-20261012`.
Their symbol/map names differ only because the shared heading routine/text
labels were exposed for the new helper; the cartridge bytes and allocation
totals match. All three ancestor recipes in
`build/dex-selected-ancestors-{ram,vram,rom}-recipe-20261012` match the reviewed
ROM, symbols and map byte-for-byte.

## Resource Matrix

Allocation-map bytes, relative to current production. Negative means reclaimed
ROMX; the fixed 4 MiB cartridge image itself does not shrink.

| Architecture | Ancestors | ROMX delta | WRAMX delta | Total allocated ROMX | Total allocated WRAMX |
| --- | --- | ---: | ---: | ---: | ---: |
| RAM buffer | No | -12,304 | +640 | 2,328,166 | 24,650 |
| RAM buffer | Yes | -10,196 | +640 | 2,330,274 | 24,650 |
| VRAM recovery | No | -12,364 | 0 | 2,328,106 | 24,010 |
| VRAM recovery | Yes | -10,256 | 0 | 2,330,214 | 24,010 |
| ROM recovery | No | +3,945 | 0 | 2,344,415 | 24,010 |
| ROM recovery | Yes | +12,139 | 0 | 2,352,609 | 24,010 |

ROM0, WRAM0, SRAM and HRAM allocation is unchanged in all six: 15,905,
4,083, 49,994 and 127 bytes respectively. No save layout or discovery format
changes are needed.

Allocated size is not the same as scratch usage. All six still use another
**217 temporary bytes inside the already allocated bank-3 Battle Tower
overlay**, ending at `$dc40`. The live Search region immediately follows;
there is no unclaimed gap there. Previous live RAM addresses are unchanged.
Only `wPokedexInfoWorkspaceEnd`, an end marker, moves.

Those 217 bytes are a 128-byte composed text line, 32-byte encoded text buffer,
eight native glyph rows, one 16-byte output tile, and 33 bytes of formatting,
hash, traversal and state fields. Another 24 bytes reuse dead mini-picture
scratch, and three old line-state bytes are aliases, not new allocations.
The 1,003 allocated bytes removed from the broad prototype are exactly the
746-byte parent index, 180-byte forward-record cache and 77-byte Moves cache.

The RAM version's bank-5 buffer occupies `$d950-$dbcf`, leaving 1,072 bytes
before `$e000`. Buffer-free versions end at `$d950`, leaving 1,712 bytes.
The earlier broad runtime trial ended at `$dfbb`, with only 69 bytes free.

## What Is Retained And Removed

**Retained Info semantics:** a three-byte header for each of 373 species and
deduplicated five-byte target/method/parameter records: **1,879 bytes** total
without ancestors. These are identifiers and evolution conditions, not font
pixels, shifted names, or prepared text lines. They preserve direct access and
avoid rebuilding forward lists in RAM.

**Retained Selected Moves semantics:** the existing per-species stream
pointers/counts, egg-family mapping, compatible TM/HM/tutor ID lists and page
counts. The semantic portion is **13,404 bytes**. The shared **666-byte** move
name pointer index was already retained in the broad trial and is not a second
Selected-only copy. Keeping these records avoids the 746-byte parent cache,
77-byte temporary Moves lists, and parent-index startup walk.

**Removed display data:** generated Info glyph pool, shifted heading sheet,
number/bar lookup graphics, source-pointer display tables, and precomposed
evolution text lines. All main Info pages compose from the native font, item
names, and original seven used source bar tiles. The separate duplicate level
marker is replaced by the native battle glyph. Description already used native
text; Area data is untouched.

Original type icons, borders, minis, palettes, page badges, source fonts,
portrait dictionaries/timelines and the scheduler remain. Their removal is not
required by glyph removal and is not part of these trials.

## The Three Restoration Paths

### RAM Buffer

Retain the visible atlas-B pixels in a 640-byte bank-5 buffer during page
composition. Modern listing return can reconstruct the scattered atlas-A
layout from that copy. Legacy return does not need the same repair.

This is the simplest recovery source and does not require readable VRAM or a
recovery-only ROM database. Its cost is 640 allocated bytes and extra bounded
copy work during some ordinary page builds. Buffer lifetime must still follow
the actually committed page, not a queued request.

### VRAM Recovery

Remove that buffer and omit the ordinary preservation-copy jobs. On the
specific Modern listing-return repair, read the committed atlas-B pixels from
bank-1 VRAM into the existing Info upload workspace, then use the existing
upload path. The visible page is preserved throughout repair.

Reads are guarded pairs: disable interrupts, wait for STAT mode 0/1, read two
bytes, then re-enable interrupts. The next mode-2 interval supplies sufficient
margin even at normal CPU speed. VBK is restored. Portrait/cry producers are
canceled before return repair. No shared ISR work is added.

Complexity is moderate and local: correctness depends on the visible atlas
remaining resident until capture, valid VRAM-access windows, and cancellation
ordering. A future reassignment of those cells or return sequencing requires
these tests to be rerun. It does not require another system to allocate RAM.

### ROM Recovery

A mutable 640-byte page cannot literally live in ROM. This trial instead
precomputes all possible recovery glyphs and per-page ordered unique-tile
vectors. Main page rendering is still runtime. The committed record stores a
three-byte species/page recipe in existing source-pointer slots; recovery
resolves its sources once into three existing unused fields.

Without ancestors, recovery data costs **16,142 bytes**: 8,096 pixels, 746
species-index bytes, 238 page-list bytes, 4,984 tile-vector bytes, 30 shared
pointers and 2,048 numeric pointers. Net extra code versus VRAM is 167 bytes;
the total architecture difference is **16,309 ROMX bytes**.

With ancestors, recovery data costs **22,228 bytes**: 9,152 pixels, 746 index,
482 lists, 9,770 vectors, 30 shared and 2,048 numeric pointers. Metadata and
glyphs occupy separate ROMX sections to fit their banks. Difference from the
VRAM trial becomes **22,395 bytes**.

This is the most complex option: generated recovery order must exactly match
runtime atlas order, the key must describe the committed page during canceled
requests, and both implementations must track wording/font/layout changes.
It avoids VRAM-read ownership risks, but introduces a second display-data
representation and stronger build/runtime coupling.

## Incremental Ancestor Feature

The actual game graph gives 123 of 373 species ancestors. Earliest ancestor
comes first; each requirement describes its edge toward the next descendant.
Sibling branches are excluded. Forward and ancestor groups start on separate
pages, even when a forward page has an unused second entry. Empty groups are
skipped and the cycle wraps to Stats. Existing caught/uncaught rules remain.

Bayleef: Stats -> Meganium / Level 32 -> Chikorita / Level 16.
Meganium: Stats -> Chikorita / Level 16 and Bayleef / Level 32.
No acquisition, battle-use, SRAM or actual evolution rules are changed.

The semantic header becomes six bytes/species. The Info semantic total rises
from 1,879 to 3,758 bytes: **1,119 extra header bytes plus 760 ancestor-record
bytes**. Additional page selection, heading handling and Unown restoration
code is **229 bytes**, giving the measured **2,108-byte** feature cost.

The ROM architecture also needs **6,086 extra recovery-data bytes**, so its
feature cost is **8,194 bytes**. The original 5-6 KiB estimate was for a
different generated-display design, not this runtime architecture.

The maximum remains four actual Info pages. The busiest ancestor page uses
36 unique tiles and the busiest forward page 39, within the 40-tile atlas.
Future changes are validated against 19 pages and 40 unique tiles per page.

### Heading Ownership

The new heading needs 13 tiles, or 208 bytes. The existing two resident heading
sets have no equally sized spare gap. It temporarily borrows bank-1 cells
`$b5-$c1` at `$8b50-$8c1f`, the first 13 Unown-font cells. Every Selected
species preparation regenerates the heading before the incoming portrait/cry
starts. On Unown entry, exactly those glyphs are restored from the existing
Unown source through 208 bytes of already allocated unbanked menu scratch and
the existing fast graphics upload path. The other 14 Unown cells remain intact.

This avoids another persistent restoration buffer and does not touch either
Info atlas, joined borders, listing artwork or animated sidebar. It adds a
paired Selected/Unown ownership obligation. Future work must preserve it.
Initial trials collided with sidebar/atlas cells; native page and cross-mode
tests caught those errors. A pointer-clobbering bank call in the first restore
attempt was also caught and removed. None of those failed trials is a review
build. The corrected helper uses a local inversion loop and the ROM0 upload
wrapper, preserving the source pointer and bank-return path.

## Alternatives

1. **VRAM recovery plus semantic metadata:** best measured ROM/RAM balance
   among these six, with runtime page latency to review.
2. **Keep the RAM buffer:** trade 640 WRAMX bytes for the simpler committed
   pixel source and its measured return behavior. It is not necessarily faster
   on ordinary Stats rendering because maintaining the copy itself costs jobs.
3. **Keep only selected display acceleration:** a smaller numeric/bar cache
   could recover part of Stats latency without restoring every shifted name.
   This is an unbuilt middle ground; measure its actual linked byte cost and
   bounded jobs rather than assuming a whole generated pool is necessary.
4. **Smaller semantic Moves metadata:** retaining only the lowest-stage family
   mapping while parsing native TM/tutor streams could reclaim some of the
   retained 13,404 bytes without rebuilding the entire parent graph. This is
   also unbuilt; temporary list space and per-species preparation cost need a
   separate comparison. It is not required for removing glyphs.
5. **Lazy ancestor heading:** generate the heading only when first visiting an
   ancestor page, or only for the 123 relevant species. This could move/remove
   preparation cost but needs a tested validity/ownership policy; no such cache
   is assumed in the six measured links.

Adding future species increases semantic index bytes linearly (three or six
per species), plus actual unique evolution lists. RAM/VRAM architectures do
not reserve another per-species parent array. New names/methods add runtime
composition work rather than stored shifted pixels. ROM recovery additionally
grows its unique glyph pool and page vectors. More moves do not directly add
Info glyphs, but the retained Moves indexes/lists still grow with real data.

## Reproduction

`tools/build_selected_semantic_prototype.py` builds an isolated trial from
current production. Always use a fresh output directory:

```sh
python3 tools/build_selected_semantic_prototype.py --output build/selected-semantic-new --restore vram --ancestors --jobs 6
python3 -m tools.dex_timing.selected_architecture prepare --source build/selected-semantic-new --jobs 6
python3 -m tools.dex_timing.selected_architecture units --source build/selected-semantic-new --jobs 6
python3 -m tools.dex_timing.selected_architecture campaign --source build/selected-semantic-new --jobs 6
```

Use `ram`, `vram` or `rom`; omit `--ancestors` for the matching old-page trial.
The source recipe and tests are repository tools, not changes to production
gameplay ASM. See [the regression suite](full_regression_suite.md).

## Runtime Measurements

All comparisons use fresh matching ROM/symbol checkpoints, the same copied
battery, native button input, both styles, active and settled portraits, and
four physical input phases. A display frame is about **16.74 ms**. Timings are
not universal hardware worst-case bounds or estimates for future content.

Main page timing is 1,072 cases per link. The additional page survey uses 12
species and every actual Info page: 672 cases without ancestors and 1,248 with.
Pairs are rejected if the initial or destination page changed semantically.
In particular, old wrap-to-Stats must not be compared with a newly rendered
ancestor page. The all-page comparison excludes 128 such changed transitions.

Median matched deltas versus production, Modern presentation:

| Action | RAM, no/with ancestors | VRAM, no/with ancestors | ROM, no/with ancestors |
| --- | ---: | ---: | ---: |
| Settled Description -> Stats | +50.23 / +50.23 ms | +33.49 / +33.49 ms | +33.49 / +33.49 ms |
| Stats during portrait playback | +66.97 / +66.97 ms | +50.23 / +50.24 ms | +50.23 / +50.24 ms |
| Settled Stats -> first forward page | +83.71 / +83.83 ms | +83.71 / +83.83 ms | +83.71 / +83.83 ms |
| First forward page during playback | +117.20 / +117.15 ms | +117.20 / +117.17 ms | +117.20 / +117.17 ms |
| Settled Info-owned species change | +33.48 / +33.48 ms | +33.48 / +33.48 ms | +33.48 / +33.48 ms |
| Settled Description -> Selected Moves | effectively 0 / 0 | effectively 0 / 0 | effectively 0 / 0 |
| Full Dex reopen | +8.00 / +8.07 ms | +8.00 / +8.07 ms | +8.00 / +8.07 ms |
| Initial Selected entry | effectively 0 / +16.74 ms | effectively 0 / +16.74 ms | effectively 0 / +16.74 ms |

Legacy has the same broad page-rendering pattern. Removing the preservation
copy makes Stats about one frame quicker than the RAM architecture. It does
not materially speed forward-evolution text composition. The largest sampled
forward-page increase versus production is about 133.94 ms, eight frames,
during active playback. Portrait and cry deadlines themselves still pass.

The broad runtime trial had a roughly 97.6 ms Dex-reopen increase, including
89.55 ms of parent-index construction. Semantic metadata reduces that to
about 8 ms; adding ancestors changes reopen by only **0.073 ms**.

Initial Selected entry has a separate 512-case survey per link: 16 species,
hover durations 0/4/30/120 frames, four physical phases, both styles. All three
without-feature links have effectively zero median native static-reveal delta
versus production. Eager ancestor-heading preparation adds **one display
frame** to the median in every style/hover group, corroborated by the native
static portrait reveal and complete-pixel timing. This happens before playback
begins; it does not extend the portrait animation or cry. It affects entry even
for a species without ancestors in the current eager implementation.

### What The New Page Adds At Runtime

In the VRAM trial, sampled ancestor pages complete in a Modern median of
**151.67 ms settled** and **192.93 ms during playback**. Content matters:
Bayleef's one-entry page is **109.81 / 125.14 ms**; Meganium's two-entry page is
**160.05 / 192.94 ms**. Legacy aggregate medians are 151.64 / 192.91 ms.
All three architectures have essentially the same median ancestor-page times.
Sample maxima reach about 279 ms during playback; these are not global bounds.

Adding the feature does not add another frame to the usual Stats/forward-page
medians. Individual active cases can shift one or two frames because the
heading preparation changes the subsequent job/portrait phase. Info-owned
species changes have an effectively zero median feature delta, with individual
cases adding a frame. This is why reporting just a population median would
hide real costs.

**Area -> Info is the clearer added cost.** It must regenerate the heading
after Area replaces resident graphics. Across the common-page 12-species
survey, Modern median feature delta is about **16.74 ms**, one frame, in all
three architectures; not every individual case crosses that boundary. Largest
sampled owner-ready increase is about 17.41 ms. This applies even when returning
to Stats, because the present implementation prepares the heading eagerly.
Lazy/conditional heading preparation is an unbuilt optimization, not a saving
already included in these numbers.

Unown entry/return also restores its glyphs, but the 16 matched transition
scenarios show no additional complete-display frame. Its largest matched
entry difference is below 0.44 ms. The source font and post-Unown Info heading
are checked byte-for-byte, not only by a first-form screenshot.

### Restoration Work Versus Visible Return Timing

VRAM reads have a real local processing cost. In sampled Modern return
traces, median copy spans are about **7.26 ms RAM**, **11.81 ms VRAM**, and
**10.20 ms ROM**. The ROM experiment was built to assess that extra work.
These spans include interrupt/STAT waits and are not pure instruction counts.
The complete repair span remains about **33.05 ms** in all three, and the
matched native listing-ready time has an effectively zero architecture delta,
with sub-millisecond individual differences in the main sample.

The raw final-pixel-hash timing reports some extra frames for VRAM versus RAM:
13 of 80 main Modern returns without ancestors, 29 of 80 with ancestors. ROM
does not improve any of those sampled frame outcomes. They must not be
presented as 13/29 slower usable-screen returns without corroboration: the
listing has a blinking cursor, and its final hash can wait for that phase.

For example, the with/without feature comparison for Blissey, Modern, active,
Stats, input phase 52,668 reports **+66.996 ms** by final hash. The actual
`listing_reveal` event differs by just **104 ticks, 0.025 ms**, and the repair
routine itself is slightly quicker. This is a hash/visual-phase artifact, not
four extra frames of restoration work. Both raw hash and native owner-ready
distributions are retained in the comparison JSON. Do not infer an algorithm
regression from a blinking final-image match alone.

Settled native listing-ready medians are effectively unchanged versus
production. Three of 40 active main returns have about one extra frame in all
architectures, associated with the changed outgoing runtime page timing.
Returning from actual ancestor pages passes the same pixel-preservation and
index rules. ROM recovery supplies no measured frame advantage that justifies
its extra 16.3/22.4 KiB over VRAM.

Machine-readable matched distributions:
`build/dex-selected-architecture-comparison-20261012/summary.json`, generated
by `tools/dex_timing/selected_comparison.py`. The comparison has separate raw
pixel, owner-ready, startup, architecture, and feature-only sections.

## Qualification And Limits

All six reviewed ROMs pass the native standard Dex campaign and additional
Selected/ancestor checks. Each link has:

| Suite | Without ancestors | With ancestors | Result |
| --- | ---: | ---: | --- |
| Standard Dex scenarios | 4,479 | 4,479 | pass |
| All-species Info scenarios | 746 | 746 | pass, every actual page |
| All-species Selected Moves scenarios | 746 | 746 | pass |
| Info rapid/held/canceled input | 400 | 400 | pass |
| Main native timing cases | 1,072 | 1,072 | pass |
| Extra all-page timing | 672 | 1,248 | pass |
| Selected entry timing | 512 | 512 | pass |
| Dex reopen | 8 | 8 | pass |
| Canceled/uncanceled pixel-preserving returns | 105 | 115 | pass |
| Prior-Info Unown/font reuse | 16 | 16 | pass, 96 transitions |

Counts overlap; do not add them as independent tests. Standard Dex coverage
includes both presentations, all three sorts, all 373 listings, popovers,
modal/visual interfaces, edge and navigation cases, Selected pages, Pokemon
Search ranks/empty/defaults/returns, and 192 ordinary mode transitions.

Fifteen runtime unit methods run against each linked trial. Applicable methods
all pass: RAM skips four without/two with ancestors; VRAM and ROM skip three
without/one with ancestors. Checks include all 256 numeric/bar composites,
every native text line, all semantic lists and 373 ancestor chains, exact
titles/attributes, workspace limits, register/bank preservation and the
architecture-specific committed-atlas recovery. Three comparison-method unit
tests also pass.

All six pass the CGB-E Type Matchups visual/raster/return campaign: 18 types,
72 navigation cases, 32 physical phases, 720 held-input frames and 1,800 idle
frames. It checks 790,016 badge pixels, 42 owner reentries, 12 close/reopens,
24 post-return Selected playbacks and 3,406 battle-chart calculations. No
illegal palette writes or register/bank errors occur. These are current native
runs, not copies of an old Type report.

The 86-method existing host suite has **85 passes and one existing failure**
on every candidate. `InfoLinkedTests.test_ready_handoff_obeys_the_active_playback_budget`
at synthetic LY 64 still reports `5 != 0` on unchanged production too. The
matched host result is `no_new_failures: true`; the exception is not silently
called a pass. Native content, publication and portrait/cry deadline checks
pass for the corrected builds.

Source checks verify shared VBlank/LCD/audio, Area, portrait scheduler, Type
Matchups and Unown animation code against the frozen baseline. Only local
Selected preparation/return and Unown-font entry handling differ. The default
production display compiler's four outputs (tile pool, headings, tables and
manifest) also remain byte-identical to HEAD. Production ROM/symbol/map hashes
remain unchanged, and unrelated workbook changes were not modified.

This is a Dex-focused comparison on SameBoy CGB-E, not a new all-move battle
animation, full discovery/persistence, PC/daycare or physical-hardware campaign.
Those systems and shared ISRs are unchanged. Their previously documented
coverage is not falsely re-attributed to these six builds. Manual review is
still required for whether the latency and extra page are desirable.

Example native screenshots from the VRAM ancestor trial:

![Bayleef ancestry](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-ancestors-vram-20261012-v6/focused/info-all-double-speed/bayleef-info-3.png)

![Meganium ancestry](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-ancestors-vram-20261012-v6/focused/info-all-double-speed/meganium-info-2.png)

Review cartridges:

| Recovery | Without ancestor page | With ancestor page |
| --- | --- | --- |
| RAM | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-semantic-ram-20261012-v5/pokecrystal-dex-selected-runtime.gbc) | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-ancestors-ram-20261012-v8/pokecrystal-dex-selected-runtime.gbc) |
| VRAM | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-semantic-vram-20261012-v1/pokecrystal-dex-selected-runtime.gbc) | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-ancestors-vram-20261012-v6/pokecrystal-dex-selected-runtime.gbc) |
| ROM | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-semantic-rom-20261012-v2/pokecrystal-dex-selected-runtime.gbc) | [ROM](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-ancestors-rom-20261012-v7/pokecrystal-dex-selected-runtime.gbc) |

## Configured Sampled Cry Evolution Comparison

2026-10-13: matched timing-only prototypes configure the three Hoenn starter
lines and complete the Magnemite and Swinub lines. The VRAM candidate starts
from the reviewed ancestor-enabled VRAM prototype; the control retains
production's precomputed display architecture and has no ancestor page.
Production gameplay sources, ROM, symbols and map remain unchanged.

The sampled-cry evolution pages are not disproportionately slower in this
sample. Rendering still adds visible frames, but sampled playback remains fed
and its natural duration differs by no more than 0.041 ms. These are native
button/display/cry-state timing captures on SameBoy CGB-E, not a regression
campaign or an audible waveform comparison.

### Configured Lines

| Line | Requirements in both prototypes | Cry implementation |
| --- | --- | --- |
| Treecko -> Grovyle -> Sceptile | Level 16, Level 36 | sampled at every stage |
| Torchic -> Combusken -> Blaziken | Level 16, Level 36 | sampled at every stage |
| Mudkip -> Marshtomp -> Swampert | Level 16, Level 36 | sampled at every stage |
| Magnemite -> Magneton -> Magnezone | existing Level 30, test-only Level 40 | synthesized, synthesized, sampled |
| Swinub -> Piloswine -> Mamoswine | existing Level 33, test-only Level 40 | synthesized, synthesized, sampled |

The Level 40 links are temporary supported triggers for this display test,
not final evolution-method or balance decisions. Learnsets are unchanged.
Both cartridges use byte-identical all-seen/all-caught review batteries, with
both save records checksummed. Separate private three-member batteries permit
direct Up/Down handoffs across each line, including the otherwise distant
Magnezone and Mamoswine listing positions. No live RAM, instructions, cries or
producer states are injected by the observer.

Only the selected Pokemon's cry plays. An evolution mini does not start the
displayed descendant's cry. Thus Magnezone and Mamoswine are measured on their
own Stats/return paths and incoming/outgoing species handoffs. Their ancestor
pages have absolute VRAM timings, not an equivalent production-page delta.

### Capture Coverage

Production has 1,120 timing cases; VRAM has 1,280. There are 1,120 same-action,
same-content pairs plus 160 VRAM-only ancestor-page captures. Both Modern and
Legacy are included, along with settled and early-playback conditions and four
physical input phases. Coverage is all 15 species' Description -> Stats,
every actual forward page, returns from Stats/forward pages, and all 20
adjacent line handoffs in both directions. No capture errors or native
frontpic/audio deadline misses are reported.

Cry state is read at the actual Info/species/leave request, not inferred from
the generic early-playback label. Every early Stats, forward-evolution and
line-handoff pair has matching active cry state in both ROMs. Eight early
Mudkip forward-page returns have a sampled cry still active in the control but
already finished in VRAM; they are retained as raw captures and excluded from
the matched-cry-state summary groups. All other pairs have matching cry state.

### First Forward Page Timings

Modern medians, from A press on Stats with the Info footer already selected
until the complete Evolutions panel appears. Each row has four physical phases
per condition per ROM. All early rows below have the selected Pokemon's cry
actually active when the request is accepted. Deltas are paired increases,
not differences of independently aggregated medians.

| Selected Pokemon | Settled production / VRAM total | Settled extra | Cry active production / VRAM total | Cry active extra |
| --- | ---: | ---: | ---: | ---: |
| Treecko | 93.08 / 160.01 ms | +66.93 ms | 93.50 / 177.26 ms | +83.76 ms |
| Grovyle | 76.35 / 109.83 ms | +33.48 ms | 76.26 / 127.05 ms | +50.79 ms |
| Torchic | 92.56 / 159.53 ms | +66.97 ms | 110.29 / 194.00 ms | +83.71 ms |
| Combusken | 76.33 / 109.80 ms | +33.47 ms | 76.83 / 110.24 ms | +33.41 ms |
| Mudkip | 93.08 / 160.05 ms | +66.97 ms | 93.55 / 194.01 ms | +100.46 ms |
| Marshtomp | 76.35 / 109.83 ms | +33.48 ms | 76.81 / 110.29 ms | +33.49 ms |
| Magnemite | 93.05 / 160.05 ms | +67.00 ms | 92.47 / 192.91 ms | +100.45 ms |
| Magneton | 76.33 / 109.81 ms | +33.48 ms | 75.75 / 125.97 ms | +50.23 ms |
| Swinub | 93.05 / 160.05 ms | +67.00 ms | 92.41 / 191.84 ms | +99.43 ms |
| Piloswine | 75.75 / 109.79 ms | +34.05 ms | 75.72 / 125.94 ms | +50.23 ms |

Each base-stage forward page has two entries; each middle-stage page has one.
The largest sampled-cry forward-page delta is 100.46 ms, about six frames,
across either presentation. The largest synthesized-cry delta is 118.65 ms,
about seven frames, in Legacy Magnemite. Aggregate content-dependent medians
must not be interpreted as sampled audio inherently being faster than
synthesized audio. Cry, portrait, text, and physical input phase all contribute
to these in-game timings; this is not a cry-only CPU experiment.

The earlier six-way report used a different set of names, methods and page
contents. Its +84/+117 ms aggregate evolution medians are not fixed overhead
constants. These new per-stage rows are the appropriate figures for reviewing
the configured lines.

### Stats And Mixed Cry Handoffs

Across all 15 species, Modern Description -> Stats adds about 33.5 ms settled
and 50.2 ms during cry playback. Final stages are included even though they
have no forward-evolution page. Legacy has the same broad pattern; the largest
sampled active Stats delta is 83.70 ms in its sampled cases.

Direct Info-owned Up/Down handoffs reset the destination to Stats. Modern
complete-display medians for the relevant cry boundary crossings:

| Handoff | Outgoing / incoming cry | Extra with outgoing cry active | Extra after outgoing playback finishes |
| --- | --- | ---: | ---: |
| Magneton -> Magnezone | synthesized / sampled | +33.49 ms | +50.23 ms |
| Magnezone -> Magneton | sampled / synthesized | +34.62 ms | +34.00 ms |
| Piloswine -> Mamoswine | synthesized / sampled | +35.05 ms | +33.52 ms |
| Mamoswine -> Piloswine | sampled / synthesized | +34.57 ms | +33.45 ms |

Other adjacent handoffs follow the same roughly two-frame typical increase,
with some three-frame cases. Natural sampled playback durations have a matched
median delta of -0.0033 ms over 744 measurements and an absolute maximum
difference of 0.0401 ms. Synthesized cry-active flag completion over 336
measurements has a zero median delta and differences from -1.0252 to +1.5669 ms.
That second measurement is a flag snapshot boundary, not a waveform-end sample.
Neither indicates a display-frame-scale extension of cry playback. Neither ROM
reports sampled cache-starvation events.

Listing-return native readiness remains effectively unchanged in the settled
medians. Active returns can differ by roughly a frame depending on outgoing
work and physical phase. Raw first/final image hashes can also differ by much
more because the footer/listing cursors blink; as in the original comparison,
those are not valid stand-alone measures of return-algorithm overhead.

The new ancestor pages are measured separately: one-entry Modern median totals
are about 93-126 ms and two-entry totals about 143-211 ms, depending on species
and cry/playback condition. Production has no corresponding page to subtract.

### Review And Reproduction

- [Production architecture with configured lines](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-sampled-production-20261013-v1/pokecrystal-dex-sampled-evolutions-production.gbc)
- [VRAM architecture with configured lines and ancestors](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-selected-sampled-vram-20261013-v2/pokecrystal-dex-sampled-evolutions-vram.gbc)

Matching review saves are beside both ROMs. Configuring the lines adds 392 ROMX
bytes to the production control and 162 to the reviewed VRAM candidate; no RAM
region allocation changes. These are fixture-specific display/semantic costs,
not the cost of adding ancestors directly to production.

Complete per-case, per-line, per-species, per-cry-state, and raw/native-return
distributions: `build/dex-selected-sampled-comparison-20261013/summary.json`.
The builders and captures are reproducible with
`tools/build_selected_sampled_evolution_prototypes.py` and
`tools/dex_timing/selected_sampled_evolutions.py`. Timing oracles use each private
candidate's evolution graph, not the unchanged production graph. The observers
combine ordinary display timing with read-only cry ownership snapshots.

ROM SHA-256 values:

```text
Production 5e7e45642e695ed574c349c0f6d0fb3a7b6b112a07320d2d0baa8c0b8711b652
VRAM       4153aa6d00b2de4ecfd2753f1a3dd1a51a7b462c3830671a8b512346794647e5
```

The regression campaign is explicitly deferred until an integration decision,
as requested. These timing results must not be treated as production-merge
qualification.
