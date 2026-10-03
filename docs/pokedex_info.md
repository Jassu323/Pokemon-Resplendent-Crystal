# Selected Pokedex Info Pages

Updated 2026-10-03. This is the Start-menu Dex's lower-panel implementation,
not the party Stats Screen or New Dex Entry. It extends the existing Selected
owner; it does not replace the portrait scheduler, timeline, dictionary plans,
sampled-cry decoder, 32-block prefill, or cry ownership rules.

The committed-page B-return fix is now integrated: the outgoing Info panel
remains intact while Listing repairs its borrowed glyph cells. Its accepted
timing/resource tradeoffs are recorded below and in the
[three-way preflight comparison](pokedex_info_return_records_preflight.md).
Incomplete gameplay evolution records remain deferred. Shared buffered page indicators are proposed for
Info and future Moves but are not implemented; the current four-page guard
still applies. The separate active-animation tab latency report remains open.

## Behavior And Layout

- The footer says `Desc Info Mov Area`. Selecting Info with A opens Stats.
- A on Info advances to future evolutions, two entries per page, then wraps to
  Stats. Every reachable future stage is included, not just direct successors.
- Internal species paging retains Info and its footer cursor, but resets to
  Stats for the incoming species. Returning to Desc resets its text to P.1.
- Seen-but-uncaught species keep the lower content blank on every page. Page
  badges remain visible; stats, evolution names/methods and minis are hidden.
- B discards any unfinished lower-panel job and uses the normal Listing return.
- The shared upper panel, frontpic and cry continue while lower pages prepare.
  Opening/cycling Info does not restart or stretch the portrait animation.

Coordinates are native 160x144 display pixels with the existing `SCX=5`.
Stat labels begin at x=4, numeric values are right-aligned separately, and bars
begin at x=56. Right-aligned numbers do not reverse the bars: bars grow left to
right. Each row is one tile high, y=80,88,96,104,112,120, in the order
HP, Atk, Def, SpA, SpD, Spe. Both titles begin at x=32, y=72, matching the
2026-10-03 edited screenshots; the stat rows, numbers and bars are unchanged.

The width rule is exactly `min(101, 2 * (base_stat // 5))`. For example, base
49 is 18px, 50 is 20px, 250 is 100px, and 255 is capped at 101px. Data comes
from the game's base stats: Chikorita has 45/49/65/49/65/45 in display order,
not the hypothetical 45/50/65/50/65/45 used for mockup placement.

Evolution names occupy y=88/112 (tile rows 11/14), with one requirement line
at y=96/120 (rows 12/15). Minis are at x=8, y=88/112, eight pixels below the
initial Info layout. Each entry has exactly two text lines, keeping the second
entry above the bottom border. Ordinary level methods retain `Level 16` style
wording; Tyrogue combines level and comparison, for example `<LV>20 Atk < Def`
for Hitmonchan and `<LV>20 Atk > Def` for Hitmonlee. `<LV>` is the dedicated
level marker copied from tile 14 of `gfx/font/font_battle_extra.2bpp`, not the
capital-L font glyph. Held-item trades combine into one line (`Trade Metal
Coat`). Long combined requirements use precomposed compact glyph spacing.
Friendship methods display only `friendship`, without day/night qualifiers,
per the user's request. This simplifies display text only; the actual gameplay
level, held-item, comparison and time requirements remain unchanged.
Each entry uses its existing two-frame 16x16 minisprite, animated every eight
hardware intervals. Skitty's actual game data now includes Moon Stone to
Delcatty; both the gameplay evolution and Info link use that same record.

## Build-Time Work

`tools/pokedex_info_assets.py` compiles disposable outputs under
`build/dex-info-assets/`. Make tracks species/item names and constants,
evolution records, base stats, the font and the bar sheet as dependencies.

The compiler walks each species' evolution graph in table order, recursively
including later stages and rejecting cycles. It emits stable species-indexed
lists and deduplicates target/method records and rendered lines. Runtime does
not allocate IDs for every evolution or walk the graph on each tab change.
Only the minisprite loader resolves each displayed target's existing icon.

The labels' half-tile placement is achieved with locally composed BG glyphs,
not a scanline Window split or OAM text. The shifted titles use sixteen
otherwise empty bank-0 font cells (`$ca-$cf,$d7-$de,$e4-$e5`), loaded once at
LCD-off Dex startup. Their final partial `s` tile is identical and shared at
`$cf`. Build guards require these source-font gaps to stay blank and any shared
title cell to have identical pixels. Other font characters are unchanged.
The number
tiles also contain the first three pixels of the bar so the bar begins at x=56
without sacrificing the desired spacing. The remaining bar uses shared full
and endpoint tiles derived from the editable `gfx/pokedex/dex_stat_bar.png`.

Current generated data has 373 species, 123 distinct evolution records and
506 atlas-source glyph tiles (8,096 bytes), plus sixteen title tiles (256
bytes). A Stats page uses 39 of the 40 atlas cells. An evolution page uses at
most 39 distinct tiles; repeated glyph occurrences share atlas entries.

Build-time guards reject more than four Info pages, more than 40 distinct tiles
per page, unsupported evolution methods and a non-HP bar needing an endpoint
past 99px. Eevee currently requires four pages total. The editable page-number
sheet contains more digits, but only P.1-P.4 are resident. Adding another page
requires extending that allocation rather than silently referencing a missing
tile. Adding a new species or evolution regenerates the tables automatically;
its data must still fit these explicit capacities.

## Preparation And Publication

`engine/pokedex/pokedex_info.asm` owns mainline preparation. Its code/tables
occupy bank `$a6`; local glyphs occupy bank `$a7`. The existing `$77` Dex IRQ
dispatcher includes `pokedex_info_publish.asm`, avoiding a new ROM0 bridge or
interrupt FarCall scratch use.

Before portrait/cry playback begins, `PokedexInfo_PrepareSpecies` caches six
base stats, caught visibility and page count. If internal paging retains Info,
`PokedexInfo_PrepareInitial` constructs Stats before the existing atomic species
reveal. That startup work does not run against an already-started incoming cry.

Ordinary tab changes use a cancellable job:

| State | Value | Work |
| --- | ---: | --- |
| IDLE | 0 | No pending lower-panel replacement |
| CLEAR | 1 | Clear one padded row, then install title/badge |
| PLAN | 2 | One Stats row, or bounded evolution text/mini preparation |
| COPY | 3 | Copy up to eight prepared glyph tiles from ROM |
| UPLOAD | 4 | Upload up to eight tiles in a contiguous atlas run |
| READY | 5 | Complete map, attributes, palettes and OAM await publication |
| INITIALIZE | 6 | Select inactive buffers and the requested evolution records |
| MINI_UPLOAD | 7 | Separately upload one prepared eight-tile animated icon |
| RECORD | 8 | Copy the prepared map/source references into its atlas's committed record |

The Selected loop checks input, services the portrait producer and commits its
deadline work first, then calls Info. During active playback Info admits work
only if `hVBlankCounter` still matches the owner loop tick and LY is below 64.
It attempts at most three slices, rechecking admission before each. A late
slice is deferred; it is not allowed to consume the portrait's finishing
reserve. A mini's lookup/copy and its upload are separate states for the same
reason. After playback finishes, lower preparation no longer has that active
portrait deadline, but publication remains hardware-window controlled.

HDMA reads the existing unbanked WRAM0 animation payload, not the bank-3 Info
staging buffer: sampled-cry interrupts temporarily switch SVBK. The payload is
borrowed only after the portrait producer returns and is reconstructed before
its next upload. This adds no WRAM0 allocation.

The old complete lower page stays visible while the inactive atlas and minis
are populated. After uploads, RECORD retains seven padded map rows, forty ROM
glyph pointers and the glyph count in six slices of at most 64 bytes. The same
three-slice/admission policy applies; no bulk interrupt-time record copy is
required. READY stages OAM and raises owner transition 5. A due portrait
publication has priority. Otherwise Info's IRQ publication admits at LY
144-146 inclusive, transfers the lower attribute/tile rows, updates the upper
half of the badge, commits mini palettes, and transfers shadow OAM. The map
work finishes in VBlank; the OAM handoff precedes the first badge scanline.
The prepared panel, endpoint and minis therefore become visible as one page.
Publication selects the atlas and its matching immutable record together,
and marks Info actually visible. Description/Listing publication clears that
visible ownership. Canceling a pending job does not discard the record or
selector of the still-displayed old page.

An OAM-only minisprite phase update is smaller. It is admitted in VBlank or
before LY 52, because type sprites begin at display y=56. It never updates
only half of a visible icon. The eight-interval phase uses the hardware display
counter, not the number of UI service calls.

### Retained Info During B Return

`engine/pokedex/pokedex_info_return.asm` preserves the actual visible page,
not a requested or partially prepared replacement. Leave cancels text/Info
jobs and cry/portrait producers before borrowing their temporary upload
payload. If the Listing cache is clean, Info is not visible, or the visible
atlas is already unaliased A, preservation is skipped.

For visible atlas B, the routine holds hardware OAM and automatic map/palette
work, restores the committed map and ROM glyph pointers into existing scratch,
reconstructs the recorded glyphs from ROM and uploads them to atlas A through
the existing bounded helpers. It remaps only the low atlas-B tile IDs. In
these Info rows, all permanent bank-0 shell/title/page IDs are >= 40; future
lower renderers must preserve that invariant or explicitly change the remapper.

Owner transition 6 is dispatched after the existing early-VBlank admission.
`Pokedex_VBlankInfoReturn` publishes the seven tilemap rows, acknowledges the
handoff and selects atlas A. Attributes, palettes and hardware OAM remain
unchanged. Only after acknowledgement does the ordinary complete-cache
Listing repair upload into the now-unreferenced atlas-B cells. The outgoing
page retains its pixels throughout; there is no lower-panel blank or VRAM
readback. A pending Info/Description job cannot overwrite the committed
record of the old visible page.

### Shared DMA Register Ownership

The portrait HDMA helper can program FF51-FF54 and then wait across a VBlank.
A lower publication during that wait must not replace its DMA registers.
`POKEDEX_ANIM_UPLOAD_ACTIVE_F` claims bit 2 of the existing scheduler control
byte around that helper. Both lower publishers defer while it is set. This is
an ownership guard, not a new animation action, timing model or RAM field.

### Cancellation And Restoration

New A requests cancel the prior unfinished Info job. B, species changes and
Area ownership also cancel it before reusing its buffers. Internal paging
keeps the outgoing OAM and palettes until the incoming owner reveal, masking
only the portrait. It does not briefly erase type badges, evolution minis or
the HP endpoint.

Returning to Desc stages blank lower attributes, clears Info's extra left
gutter cells and last row, then runs the existing bounded description printer.
The publication removes lower OAM and restores the map together. Uncaught
species queue an explicit blank P.1 restoration without rendering hidden text.
A pending Description transaction re-requests the one-shot IRQ each owner loop
until acknowledged: competing portrait publication can otherwise clear that
request. The larger attribute/OAM restoration is not combined with a due
portrait transfer; normal text-only paging can still use its established
combined transaction.

## Palettes

All eight BG palettes are assigned; types therefore use OBJ palettes.

| Palette | Owner | Border RGB5 | Fill RGB5 |
| --- | --- | --- | --- |
| BG 0 | Shell, ordinary text | Existing shell | Existing shell |
| BG 1 | Portrait | Species palette | Species palette |
| BG 2 | HP and footprint | 11,22,2 | 13,27,2 |
| BG 3 | Attack | 25,22,3 | 29,25,3 |
| BG 4 | Defense | 23,10,2 | 28,12,2 |
| BG 5 | Sp. Attack | 2,19,24 | 2,24,29 |
| BG 6 | Sp. Defense | 8,11,22 | 9,13,27 |
| BG 7 | Speed | 20,3,16 | 26,4,21 |
| OBJ 0/1 | First/optional second type | Existing type colors | Existing type colors |
| OBJ 2/3 | First/second evolution mini | Existing minisprite palettes | Existing minisprite palettes |
| OBJ 4 | HP endpoint | Same as BG 2 | Same as BG 2 |

These are the supplied mockup colors quantized to the GBC's 5-bit channels,
not an alternative approximate palette. Local bar colors are white=0,
border=1, fill=2, gray=3, with gray `RGB 5,5,5`. The footprint contains only
colors 0/3, so sharing HP's palette does not recolor it. OBJ color 0 is
transparent. Types preserve their white lettering and colored fill; the
background/corners become transparent over the existing dark-gray BG.

## VRAM And OAM

The static 49-tile portrait and both 49-tile streaming slots are unchanged.
The bank-0 font gains only the title tiles in its otherwise blank gaps.
BG storage is addressed with the normal signed
tile scheme; OBJ allocations below are physical offsets in `vTiles3`.

| Bank/range | Use | Tiles |
| --- | --- | ---: |
| Bank 0 signed `$ca-$cf,$d7-$de,$e4-$e5` | Shifted Info headings in reserved font gaps | 16 |
| Bank 0 `vTiles2 $7b-$7e` | P.3/P.4 upper/lower digit tiles | 4 |
| Bank 1 `vTiles3 $00-$27` | Existing Listing center minis | 40 |
| Bank 1 `vTiles3 $28-$37` | Two sets of two type badges | 16 |
| Bank 1 `vTiles3 $38-$57` | Two sets of two animated evolution minis | 32 |
| Bank 1 `vTiles3 $58-$59` | 100px/101px HP endpoint variants | 2 |
| Bank 1 signed `$fa-$ff,$28-$31,$78-$7f,$64-$6b,$70-$77` | Inactive/active atlas A | 40 |
| Bank 1 signed `$00-$27` | Atlas B, borrowing Listing side-icon frame 0 | 40 |

Atlas A uses 24 formerly unused BG cells and 16 freed BG type-icon cells.
Atlas B borrows exactly the Listing's 40 frame-0 BG cells while Selected owns
the display. Its uploads invalidate the Listing ring before B-return; the
normal cache repair restores it without reusing stale ownership tags. It does
not overwrite visible Info references: B-return first relocates them to atlas A
using the committed page record, closing `DEX-INFO-01`. The
other Listing frames and center minis are not overwritten.

Only types, evolution minis and the two extreme-HP endpoint cases use OAM.
HP 100px needs one endpoint pixel and HP 101px needs two, at x=155. This avoids
borrowing a BG border tile; x=157 remains dark gray before the x=158 border.
Chansey uses the 100px version and Blissey the capped 101px version.

Types use shadow entries 0-7; Info minis or endpoint use entries 8-15. A
dual-type species needs eight same-scanline OBJs, below the hardware limit of
ten. Minis have at most two OBJs on either of their own scanlines; the endpoint
does not coexist with evolution entries. No text or numeric OAM is required.

After these reservations, bank 0 has one unused BG cell (`$7f`), and bank 1
has 38 unused OBJ-only cells (`vTiles3 $5a-$7f`). There is no spare bank-1
BG-addressable cell while both Info atlases are reserved. The next lower tabs
can reuse Info's mutually exclusive atlases/workspace, not assume a new
independent allocation. See [the complete ownership map](pokedex_vram.md).

## RAM And ROM Budget

The new workspace extends the existing Dex overlay in the bank-3 Battle Tower
union. It is not a new WRAMX section or a live Battle Tower allocation.

| Field | Address | Bytes |
| --- | --- | ---: |
| Alignment after description chunk | `$d4a2-$d4af` | 14 |
| Glyph staging | `$d4b0-$d72f` | 640 |
| Mini staging | `$d730-$d82f` | 256 |
| Lower OAM staging | `$d830-$d84f` | 32 |
| Glyph source pointers | `$d850-$d89f` | 80 |
| State, stats, palette targets, cursors | `$d8a0-$d8d4` | 53 |
| Committed atlas-A page record | `$d8d5-$da05` | 305 |
| Committed atlas-B page record | `$da06-$db36` | 305 |
| Actually-visible Info flag | `$db37` | 1 |
| Total overlay extension | | 1,686 |

The workspace ends at `$db38`; the conservative `$dc00` assertion leaves
200 bytes before that boundary. The physical bank has more space after it,
but that is not a promise that all other union lifetimes permit using it.
Move/Area should reuse this mutually exclusive lower-panel workspace.

Info-specific ROMX banks use 10,322 bytes in `$a6` (code/tables) and 8,352 in
`$a7` (glyphs/titles), with 6,062 and 8,032 bytes free respectively. Small integration
and IRQ code is also in the existing Dex banks. The overall addition is about
18KiB. A few existing Listing graphics moved from the tight shared Dex bank to
`$77`; their callers already use the graphics' BANK labels. No ROM0 bridge,
WRAM0 byte, HRAM byte, SRAM field or runtime instrumentation was added.

Current linked cart: 2,313,880 used bytes out of 4,194,304 (55.17% used),
1,880,424 bytes free (44.83%, about 1.79MiB). Eighty-seven ROMX banks remain
completely unused (including fourteen empty banks listed in the linker map,
not just the seventy-three beyond its last mapped bank). Premium free totals are ROM0 568 bytes, WRAM0 13 bytes,
HRAM 0 bytes; the union-wide WRAMX map reports 4,728 free bytes. Unused ROM0
fragments are not necessarily one contiguous block.

## Validation And Manual Checks

Use a fresh ROM boot or a freshly captured same-link state. All normal-input
Info fixtures edit only private battery copies under ignored `build/`.
Observers are host-side; the production cartridge contains no telemetry.

```sh
make -j8
make verify-dex-animations verify-sampled-cries
PYTHONPATH=tools python3 -B -m unittest tools.test_pokedex_info
PYTHONPATH=tools python3 -B -m dex_timing.info_ui --battery /path/to/copied.sav --output build/dex-info-check --jobs 8
```

The maintained Info audit covers all 373 species at four opening phases,
Stats, every evolution page, wrap, animated minis, exact glyph/palette/tile
data, HP endpoints, retained Info during internal paging, footer action after
the reveal, complete Desc restoration, and B-return. It checks every portrait
publication against authored intervals and pixels, and every sampled cry's
complete block accounting. `--uncaught` verifies hidden content. `--stress`
adds rapid/held A and cancellation by Desc, B and another species.

For visual review, check Chikorita's layout, Oddish/Poliwag/Eevee multi-page
branches, Tyrogue's conditions, Skitty/Delcatty's link, Chansey/Blissey's long
HP bars, and a final-stage species' Stats-only wrap. Switch to Info immediately
on Dusknoir, Luxray, Kyogre, Garchomp and Groudon; change pages or species while
the animation/cry is still playing. Check outgoing and incoming types,
endpoint removal/creation, mini motion, and repeated B-return/reentry. Check
an uncaught species too. No type/endpoint blank frame is expected on paging.

Current-link SameBoy miss breakpoints:

```text
breakpoint $a0:$6677
breakpoint $0:$3cc1
```

The first is `Pokedex_AnimationMiss`. The second is the validated cache-empty
branch, six bytes before `SampledCry_AsyncTimerTick.has_decoded_block`; unlike
the generic stop routine it does not trigger on an intentional cry cancel.
Neither should hit during Selected Info/Desc playback or ordinary paging.
Other screens' known sampled-cry issues are separate from this acceptance.

If one hits, capture registers/backtrace and the following before continuing:

```text
x/26 $0:$c72e
x/3 $0:$c758
x/53 $3:$d8a0
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
print/x [$ff9b]
```

Record species, page, input, cold/internal path and whether the miss was in
Selected or another screen. A screenshot/video is useful for a visual fault
without a miss; a fresh state at the miss preserves its exact phase. Re-resolve
all addresses from the matching symbol file after subsequent code changes.

### Timing Tradeoffs

Current accepted B-return preservation adds roughly 50ms/three display
intervals on common atlas-B paths (two intervals for smaller glyph sets),
and effectively no return delay on atlas-A pages. Preparing committed records
adds approximately 33.49ms/two intervals to settled Stats activation, now
about thirteen intervals. Internal Info reveal remains phase-dependent; the
preflight paired cases have near-zero median added delay and a maximum of
about 1.94 intervals. These costs are accepted for correctness and deferred
to `DEX-PERF-02` after the remaining tabs/modes exist.

The following ranges describe the earlier placement link before record
preparation was added, not a promise of current whole-tab latency:

The ready-state audit measures A-to-published-Stats latency, including its
confirmation display, at 11-34 hardware intervals (median 15) across the four
phases. Settled Stats preparation is about 11 intervals. Dusknoir's busiest
opening phase can take about 32; the old page remains complete and its portrait
keeps exact timing while lower work waits for available budget. This is deferred
page preparation, not slowed portrait frames. Internal Info preparation adds
1.99-5.00 display intervals compared with ordinary Desc internal paging
(median 3.08, roughly 34-84ms). The captured ranges are 7.18-14.18 intervals
for Desc and 10.17-17.18 for Info. The incoming type icons and HP endpoint
are present on the first incoming display, with no extra blank icon frame.

The separately logged `DEX-AREA-01` return stall is not fixed or hidden by
this work; Area implementation remains deferred.

### Initial Info Acceptance (Before Placement Revision)

All tests below used private battery copies and the initial Info link, with no
live-save changes or game-side instrumentation. Its accepted identity was:

```text
ROM SHA-256: 4cb2e89b62bb9856c0c963d282f4587a3486f38fc619406e1f3f0ece0775b182
SYM SHA-256: 00dd7e53314bc936487d071e51d04d3e5d34ff738cbbb906fcf2954ad4c6cdc5
```

A full clean rebuild, followed by both asset verification targets, reproduced
these ROM and symbol-file hashes exactly.

| Suite | Passed | Evidence under ignored `build/` |
| --- | ---: | --- |
| Info, all species at phases 0/8/32/settled | 1,492/1,492 | `dex-info-final` |
| Rapid/held A and unfinished-job cancellation, 13 species | 260/260 | `dex-info-stress-latest` |
| Seen but uncaught, eight species at four phases | 32/32 | `dex-info-uncaught-final` |
| Cold Description opens plus Listing returns | 373/373 + 373/373 | `dex-info-cold-final` |
| Description shell/pages/types/internal targets | 1,492/1,492 observations | `dex-info-description-final` |
| Fully captured Desc internal transitions | 373/373 | `dex-info-transition-final` |
| Fully captured Info Stats internal transitions | 373/373 | `dex-info-info-transition-final` |
| Focused outgoing Info page/active-phase transitions | 24/24 | `dex-info-evo-transition-final` |
| Listing restoration and subsequent navigation/reentry | 30/30 | `dex-info-listing-final` |
| Focused cry cancellation and all-species active handoffs | 40/40 + 1,492/1,492 | `dex-info-cry-final` |
| New Dex Entry, 20 species with the full input-timing sweep | 8,570/8,570 | `dex-info-new-entry` |
| Maintained unit/linked contracts | 178/178 | Test command below |

The New Dex Entry sweep starts from a native current-link Master Ball catch
donor and explicitly generated species contexts. It is not presented as
twenty independent authentic wild catches. Twenty uninterrupted baselines and
8,550 A/B/held/rapid-input cases retain exact timing, pixels, cry accounting,
text publication and return ownership. Listing and cry observer-on/off controls
also match cycle/state/palette/map/pixel results.

Every Info playback audit retains the authored portrait intervals and correct
tile pixels, with complete sampled block accounting. All 770 captured internal
transitions show the outgoing non-portrait pixels unchanged during masking and
the correct incoming icons/endpoints on the first incoming display. There are
no full-screen black/white flashes, blocked palette writes or extra blank
type/HP frames. The blink oracle exempts only the four footer cursor cells;
footer labels, border pixels and logical cursor ownership remain checked.

Listing's unused OBJ palettes 6/7 can differ from the target array because its
bounded restoration publishes only used slots 0-5. No visible object uses the
unrestored slots; the visible-palette and cache/navigation audits pass.

The automated suite caught and corrected DMA-register contention during a
portrait wait, a too-tight lower publication gate, lost one-shot restoration
requests, uncleared shifted-label gutter cells, incorrect Info cursor reset
on internal paging, and cancellation of a just-queued uncaught blank Desc
page. Each correction retains the existing portrait/audio design; linked
contracts and normal-input regressions cover their behavior.

The maintained contract command is:

```sh
PYTHONPATH=tools python3 -B -m unittest tools.test_pokedex_info tools.test_dex_description_ui tools.test_dex_scheduler tools.test_cry_ownership tools.test_internal_transitions tools.test_listing_restoration tools.test_direction_changes tools.test_description_paging tools.test_shared_input tools.test_dex_cold_listing tools.test_new_dex_entry tools.test_dex_target_regression tools.test_dex_backlog_revalidation
```

Asset checks verify 399 timeline structures, all 65,536 sampled-lookup header/
selector combinations, and all 122 sampled cries (37,655 compressed blocks,
602,480 decoded bytes) byte-for-byte. The older historical timing-discovery
suite still expects removed instrumentation and earlier capture addresses;
it is not the acceptance suite for this clean implementation.

### Placement And Requirement Follow-Up (2026-10-03)

The production layout revision shifts the headings 13px right and evolution
entries 8px down. Stat rows and bar scaling are unchanged. It combines
requirements into one line, uses the existing `<LV>` glyph for Tyrogue, and
simplifies friendship display wording without altering gameplay requirements.
Compared with the initial Info link it costs 728 additional ROMX bytes, no
additional ROM0/WRAM0/WRAMX/HRAM bytes, and sixteen previously blank cells
within the already-reserved bank-0 font region. No new animation slots or
OAM entries are allocated.

```text
ROM SHA-256: 2928c51263a162d573f4ee96204aca768f83ffb9aff1fe418a7af3de0ee76346
SYM SHA-256: 3c1ee132610963d7f37debd1548b979d1c0a02401bb6930084de195f4136af92
```

| Revision suite | Passed | Evidence under ignored `build/` |
| --- | ---: | --- |
| Info, all 373 species at phases 0/8/32/settled | 1,492/1,492 | `dex-info-placement` |
| Rapid/held A, Desc/B/species cancellation, 13 species at four phases | 260/260 | `dex-info-placement-stress` |
| Seen but uncaught, eight species at four phases | 32/32 | `dex-info-placement-uncaught` |
| Description pages/types/internal targets | 1,492/1,492 observations | `dex-info-placement-description` |
| Maintained unit/linked contracts | 180/180 | Maintained command above |

The audit now checks heading tile pixels and attributes, exact evolution text
rows and mini OAM positions. The dedicated level marker is checked against
the battle font and explicitly distinguished from ordinary `L`. Chikorita's
white title and lower-body text pixels match both supplied edited screenshots
exactly (zero differing ink pixels); title bounds begin at x=32, y=72. The
minis' hardware positions put their display origins at y=88/112. Native and
4x screenshots of Chikorita and Tyrogue are retained in the placement output.
Info opening latency remains 11-34 intervals (median 15), with settled Stats
preparation about 11 intervals. All measured portrait timelines and sampled
block accounting remain exact, with zero animation/cache-empty misses.

The first stress invocation exposed a host-only assumption that the `settled`
phase was an integer delay. The runner now explicitly settles playback for
that phase, and the entire 260-case suite passes on rerun. An initial
Description invocation lacked that runner's private `input-copy` ROM/save
filenames; after supplying exact matching copies, its full suite also passes.
Neither invocation failure was a cartridge failure or required a gameplay fix.

These placement regressions did **not** close the three subsequent user reports
`DEX-INFO-01/02/03` in the [live backlog](pokedex_selected_bug_backlog.md#info-pages).
In particular, rendering the generated evolution records is not an independent
proof that every reported added evolution branch is present. Missing added
branches, session-dependent Listing corruption and tab responsiveness during
playback need their own reproduction and diagnosis. They were logged, not
silently folded into this placement change.

### Committed Page Return Acceptance (2026-10-03)

`DEX-INFO-01` is now solved by the retained-page transaction described above.
The user accepted its measured return/preparation costs and deferred further
optimization. Production reproduces the tested prototype ROM/SYM/MAP exactly;
the [production acceptance](pokedex_info_return_records_preflight.md#production-integration)
records the identities, 373-species playback pass, 96 focused B-returns,
250 cancellation cases, full 7,460-case rapid-input sweep and resource bill.
The only stress failure remains the independently logged `DEX-INFO-04`
Rhyperior Description badge loss. No new game-side instrumentation was added.
