# Pokedex Area Integration

2026-10-03. Integration of the existing full-screen vanilla nest map with the
current Selected-Mon owners. The accepted implementation restores the outgoing
tab/page with a static portrait. The user accepted the separate prototype and
authorized production promotion; the six runtime changes are now integrated.
No installed-ROM replacement or live save edit was performed.

## Production Promotion

A full clean production rebuild matches the accepted static-return prototype
byte-for-byte across the ROM, symbols and map. The production ROM SHA-256 is
`7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.
Runtime source changes are limited to the six files described below. The host
observer remains read-only; no new runtime instrumentation or testing encounters
are included. Original prototypes and their pinned reproduction recipe are
retained as historical evidence, not active build variants.

The final production-path repeat passes all 15,130 Area cases in the matrix
below, with zero failures and all four actual time-palette values represented.
All 536 matched entry/return timings are exactly equal to the accepted
prototype (zero minimum, median and maximum delta).

The standard production repeat also passes 373 cold entries and returns,
1,492 Description cases, 746 Info cases, 373 caught and 373 uncaught Moves
cases, 1,323 Moves stress cases, 40 cry-ownership cases, 16 navigation controls,
1,492 species handoffs, 96 Listing restoration cases, and all 122 sampled cries.
The New Dex Entry sweep passes 8,568 cases across 20 generated species contexts;
the focused 93 host checks and full 406-test host suite pass. Twelve recorded
roundtrips have zero blocked palette writes, white frames or LCD toggles.

Some initial host checks lacked the raw stat-bar reference removed by the clean
build; those results are excluded. Regenerating the reference and repeating
all affected suites in fresh outputs produces the successful results above
without changing the ROM. Two focused matrices were also repeated with the
prototype's exact species/button inputs for like-for-like coverage.
The consolidated production evidence is
`build/dex-area-production/reports/summary.json`; accepted reruns are under
`reports-rerun/`. The ROM, symbols, map, source fixture and live SameBoy battery
are unchanged throughout testing. Generated evidence remains ignored.

`DEX-AREA-01` is marked solved following the user's manual acceptance and this
production repeat. Changes are ready for final review and a single Area
integration commit; no commit or push has been performed by the agent.

## Scope And Retained Behavior

The footer's Area action opens the existing Johto/Kanto map, not a new lower
panel. Graphics, map layouts, encounter lookup, marker placement and controls
retain their current vanilla implementations:

- Start in Johto. Left selects Johto; Right selects Kanto only after the
  existing Hall of Fame flag is set.
- Blink nest markers at the existing 16-display-interval boundaries. Hold
  Select to show the player, only in the displayed region; retain the male,
  female and Fast Ship icons.
- A or B restores the outgoing Description, Info or Moves tab and its exact
  page, with the footer cursor on that tab. Reload the base portrait without
  restarting its frontpic animation or cry. Evolution minis remain animated.
- Area remains available for seen-but-uncaught species. Description, Info and
  Moves still have their existing caught-only visibility.
- Read current grass encounters across all three times of day, water encounters
  and the two tracked Johto roamers. Fishing, headbutt and scripted/event-only
  locations are not added. Species with no matching records have no markers.

No animation scheduler, cry codec/prefill, encounter data, catch animation or
move/evolution data is changed. This is an owner handoff correction, not another
rendering or hardware timing model.

## Reproduction And Causes

Baseline commit: `96e5a8c1708896972fdf27922aa077b904fc59a4`.
Open Dusknoir in New Dex, move the footer cursor right three times and press A.
Normal-input replay on the frozen production ROM fails to reach
`Pokedex_GetArea.loop` within 60 display intervals. The screen remains hidden;
the first one-tile nest-icon `Request2bpp` is pending and B cannot be serviced.

Area inherits Selected's specialized VBlank dispatcher. Its ordinary tile
service arrives too late for `Serve2bppRequest`'s LY 144-145 admission window,
so this pending request does not complete. The older cry/text investigations
already recorded this independently of their changes.

The remaining integration hazards are distinct from that stall:

1. Selected's hidden-transition OAM hold would suppress Area's vanilla player
   and nest sprites unless explicitly released after preparation.
2. Selected's OBJ type badges replace the original red/blue palette slots.
   Area's player/markers need the ordinary time-selected map object palettes.
3. The map and attribute setup overwrites Selected's backing. A normal partial
   map-copy/reveal is not a sufficient return transaction; maps, palettes and
   OAM must belong to the restored Selected owner before it is revealed.

## Runtime Implementation

Only six game-source files differ from the pre-Area production baseline:

| File and boundary | Change | ROMX delta |
| --- | --- | ---: |
| `pokedex_detail.asm`, `PokedexSelectedMon_Area` / `StageDescription` | Select ordinary VBlank; normalize viewport; save/restore the outgoing view; cancel the base loader's producer instead of priming or starting playback on Area return | +19 bytes, bank `$a0` |
| `pokedex_3.asm`, lower-owner publication / `.TransferMap` | Route Area return through atomic internal publication, but restore all 18 map rows even for Info | +11 bytes, bank `$77` |
| `pokegear.asm`, `Pokedex_GetArea` | Finish both maps and initial nests before applying visible palettes, release OAM hold, wait one display interval | +12 bytes, bank `$24` |
| `color.asm`, `PokedexArea_LoadObjectPals` | Copy the first two current `MapObjectPals` palettes into existing `wOBPals1` | +25 bytes, bank `$21` |
| `pokedex_info.asm`, `PokedexInfo_PrepareInitial` | Preserve the current page during Area return; retain ordinary page reset on species entry | +7 bytes |
| `pokedex_moves.asm`, `PokedexMoves_PrepareInitial` | Same Area-only page preservation | +7 bytes |

Entry first cancels Description/Info/Moves preparation and outgoing playback
using the existing Dex-local cleanup. The ordinary VBlank owner services Area's
ordinary graphics requests while the transition remains hidden. Both region
maps and initial marker records finish before palette reveal and OAM release.
The vanilla input loop then owns region changes, player display and blinking.

On entry, the outgoing view is saved in AF on the existing stack. Existing
Description/Info/Moves page fields remain intact while their jobs are canceled.
On exit, the vanilla routine restores its two saved town-map landmark bytes,
then the caller pops AF and restores the view before rebuilding the page.
Info/Moves initial preparation retains that page only in `AREA_ACTIVE` state.

The Selected path hides the outgoing Area owner, restages its existing assets,
then atomically publishes its full maps, palettes and OAM. The base loader
normally arms an animation producer even before playback starts, so Area
return explicitly cancels that producer. It skips dictionary-tail startup,
first-frame priming and animation/cry start. Normal cold entry and species
paging still follow their existing playback paths.

Screenshot review found an Info-specific regression during development:
internal Info publication normally skips rows 0, 16 and 17 because Selected's
shell and footer already exist. That is invalid after Area overwrites them;
the retained Area title/footer appeared in the returned screen even though
the lower content and page audits passed. `AREA_ACTIVE` now requests all 18
rows in both tile and attribute maps. Normal internal Info publication retains
its existing reduced map range. The return audit now independently checks the
omitted shell rows against the staged owner backing, allowing only ordinary
footer-arrow blinking.

`PokedexSelectedMon_Area.map_returned` is a zero-instruction host stop label.
It permits checking the handoff before Selected's base-data union
legitimately overwrites the town-map scratch aliases. There are no runtime
instrumentation counters, trace buffers or additional diagnostic instructions.

## Resource Costs

Total cartridge cost is **81 ROMX bytes**, in existing banks: 48 for the first
Area integration plus 33 for static return, page retention and full Info map
restoration. No new bank, graphics asset, palette table or indexed data is
required.

| Resource | Baseline used/free | Integrated used/free | Allocation delta |
| --- | ---: | ---: | ---: |
| ROM0 | 15,830 / 554 bytes | Same | 0 |
| Occupied ROMX banks | 2,313,941 / 700,715 bytes | 2,314,022 / 700,634 bytes | +81 bytes |
| WRAM0 | 4,083 / 13 bytes | Same | 0 |
| WRAMX | 23,944 / 4,728 bytes | Same | 0 |
| HRAM | 127 / 0 bytes | Same | 0 |
| SRAM | 49,994 / 15,542 bytes | Same | 0 |

The 4 MiB cartridge has 2,329,852 occupied bytes, about 55.55%, leaving
1,864,452 bytes including completely unassigned banks. The palette code bank
`$21` has 252 free bytes after this helper; no relocation is currently needed.

Area temporarily uses the existing vanilla VRAM footprint:

- 48 BG tiles at bank 0 `$9000-$92ff`, signed tile IDs `$00-$2f`.
- Four player OBJ tiles at bank 0 `$8780-$87bf`, plus one nest tile at
  `$87f0-$87ff`.
- Both existing BG/window maps and their attribute maps.
- Existing shadow OAM and tilemap scratch; one OBJ per nest or four for the
  player. No hardware OAM or VRAM allocation is added.

These are exclusive Area-owned overlays, not additional permanently resident
Selected assets. Selected restaging on exit is still required. The routine
copies 16 existing palette bytes and adds one final display wait; the expensive
part remains vanilla map/graphics preparation, not this small helper.
There is no persistent RAM allocation for remembering the view: the Area call
uses two additional temporary stack bytes and pops them before restoration.

## Original Prototype Timing (Historical)

70224 normal-speed T-cycles per display interval; one interval is 16.7427 ms.
The all-species caught Johto matrix measures these logical readiness endpoints:

| Endpoint | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Accepted Area action to first Area input loop | 34.530 intervals / 578.132 ms | 34.974 / 585.567 ms | 38.986 / 652.732 ms |
| A/B press to restored Selected input loop | 10.355 intervals / 173.379 ms | 12.444 / 208.345 ms | 17.310 / 289.817 ms |

These are instruction-boundary timings, not a claim that a fully scanned
visible frame completes at that exact instant. First complete scanout can add
approximately one display interval. There is no meaningful finite entry-speed
comparison against the reproduced baseline, because that baseline stalls.

The roughly 0.6-second opening is the main presentation tradeoff. Vanilla
prepares both regions upfront, including three attribute waits and the existing
tile-map waits for each region. This prototype deliberately retains that model.
Loading one region on demand or adding a dedicated batch uploader would be
broader optimization work under `DEX-PERF-02`, not necessary for correctness.

## Automated Acceptance

Headless SameBoy runs use normal game inputs and private battery copies. The
read-only observer inspects physical ROM/VRAM/OAM/palette memory without adding
cartridge writes or bus reads that advance the PPU. Area expectations are built
independently from linked maps, graphics, landmark coordinates and encounter
records, rather than trusting the renderer's output as its own oracle.

After a clean build, host content checks additionally require the raw generated
bar reference (`make gfx/pokedex/dex_stat_bar.2bpp`). A cached compiled Info
atlas can leave this host-only reference absent even when the cartridge builds
correctly. Regenerating it does not alter the reviewed ROM.

### Static-Return Acceptance (Current)

All results below use the final static-return ROM identified under Prototype
And Reproduction, including the full-map Info restoration correction.

| Area matrix | Cases | Failures |
| --- | ---: | ---: |
| All 373 caught species; three tabs; active/settled; A/B return | 4,476 | 0 |
| All 373 seen-only species; same input matrix | 4,476 | 0 |
| Every available Description, Info and Moves page; all 373 species | 3,814 | 0 |
| Updated half of the matched original/updated timing comparison | 536 | 0 |
| Six entry phases; later pages; repeat Area and internal species paging | 648 | 0 |
| Eight gender/location/clock variants | 672 | 0 |
| Recorded frame/palette controls | 12 | 0 |
| Independent shell-row, repeat-Area and internal-paging audit | 60 | 0 |
| Immediate B-return to Listing from all available pages of 15 species | 520 | 0 |
| **Total** | **15,130** | **0** |

The initial caught matrix includes 876 Area entries while a lower-panel job is
still pending. The location/clock variants verify male/female, Johto/Kanto and
Fast Ship player icons, region locking, and all four actual palette values
0-3. Four observer-on/off controls are byte-for-byte equal; read-only auditing
does not change the replay. Twelve recorded roundtrips contain no blocked
palette writes, white frames or LCD toggles. The independent shell audit checks
rows 0, 16 and 17 as well as the viewport, rather than just lower-page content.

For each restored owner, the audit checks the exact tab/page/cursor, base
frontpic pixels, a canceled producer, no animation or cry restart, and 120
further display intervals without spurious publication. Evolution minis have
two independently verified hardware-tile animation phases; static frontpic
return does not disable those minis. Immediate Listing return and subsequent
normal species paging retain their existing map/OAM/palette and playback
behavior.

The 536 original-prototype comparison cases also pass their original forced
Description/replay contract. They are not counted again in the updated total.
Matched physical A/B press to restored Selected input-loop medians are:

| Outgoing/restored tab | Original prototype | Static-return prototype |
| --- | ---: | ---: |
| Description | 13.409 intervals / 224.502 ms | 11.065 / 185.256 ms |
| Info | 11.486 intervals / 192.313 ms | 14.922 / 249.834 ms |
| Moves | 12.409 intervals / 207.758 ms | 11.922 / 199.601 ms |

The original always restored Description, including after Info/Moves. Info's
roughly 58 ms difference between medians therefore includes rebuilding the
requested Info page, not a slower implementation of the same return behavior.
The median of per-case paired deltas is +42.080 ms for Info, -26.726 ms for
Description and -8.149 ms for Moves; this statistic is distinct from subtracting
the two column medians. Dusknoir Description returns improve from a median
16.313 intervals to 10.924, approximately 90 ms faster without animation-tail
startup.

Opening Area has no median change in matched cases; individual paired changes
range from -2.225 to +2.321 ms. Across all caught species, current opening
readiness is 578.132-653.481 ms, median 585.567 ms. Current return medians across
that larger matrix are Description 182.912 ms, Info 249.836 ms and Moves
199.610 ms. These instruction-boundary endpoints precede a complete scanned
visible frame, which can add approximately one display interval.

| Standard regression on the final ROM | Result |
| --- | --- |
| All-species cold Listing playback and return | 373/373, including 373 returns |
| Description UI | 1,492/1,492 |
| Info UI | 746/746 |
| Caught/uncaught Moves | 373/373 each |
| Moves input/tab/cancellation stress | 1,323/1,323 |
| Cry ownership, navigation and all-species handoffs | 40 + 16 + 1,492, all pass |
| Listing restoration/navigation | 96/96; zero metadata warnings |
| New Dex Entry phase/input regression | 8,568/8,568; 20 species, 1,207,436 observed displays |
| Sampled decoder | 122 cries, 37,655 blocks and 602,480 output bytes match; 65,536 lookup combinations pass |
| Focused host/linked checks | 93/93 |
| Full host suite, including historical golden reference | 406/406 |

The New Entry contexts use normal entry setup and a private native-Master-Ball
donor, not 20 separate manual catches. No tested animation miss, active sampled
cache-empty event or new restoration failure remains. This does not close
unrelated Listing-navigation or battle-cry backlog reports.

Earlier pre-shell-fix outputs are retained separately under ignored
`reports-before-shell-fix/`, not accepted as final evidence. An initial shell
audit also misidentified the ordinary footer arrow tile; its 60 cases were
rerun successfully with the linked tile expectation. Final consolidated
evidence is `build/dex-area-static-return/reports/summary.json`.

### First Integration Regression (Historical)

The following results belong to the earlier prototype that forced a
Description return and replayed the animation/cry, not the static-return build.

| Area matrix | Cases | Failures |
| --- | ---: | ---: |
| All 373 caught species; Description/Info/Moves; active and settled; B return | 2,238 | 0 |
| All 373 seen-but-uncaught species; three tabs; active/settled; A/B return | 4,476 | 0 |
| Additional Description page 2/evolution-page and A/B controls | 96 | 0 |
| All 373 caught species with Kanto unlocked; three tabs; active/settled | 2,238 | 0 |
| Focused unlocked seen-but-uncaught A/B controls | 72 | 0 |
| Six 96-case gender/location/time variants | 576 | 0 |
| Recorded frame/palette-write controls, including unlocked Kanto | 9 | 0 |
| **Total** | **9,705** | **0** |

The variants cover male/female, Johto/Kanto player location, Fast Ship,
Hall of Fame lock/unlock and all four actual `wTimeOfDayPal` values 0-3.
Every case checks nest records/blinking, Select behavior, region controls,
restored Description state, replayed portrait pixels/timeline/cry completion,
subsequent Info/Moves activation and Selected-to-Listing return.
The later map-oracle passes also compare full headings, map/attribute rows,
decompressed town tiles, player/nest graphics and hardware palettes.
The nine recorded controls have zero blocked palette writes, white frames or
LCD enable/disable writes across their observed roundtrips.

| Standard regression | Result |
| --- | --- |
| All-species cold Listing playback and return | 373/373 |
| Description UI | 1,492/1,492 |
| Info UI | 746/746 |
| Caught/uncaught Moves | 373/373 each |
| Moves input/tab/cancellation stress | 1,323/1,323 |
| Cry ownership, navigation and all-species handoffs | 40 + 16 + 1,492, all pass |
| Listing restoration and subsequent navigation | 96/96; no metadata warnings in this run |
| New Dex Entry phase/input regression | 8,596/8,596; 20 species, 1,212,499 observed displays |
| Sampled decoder | All 122 cries and 37,655 compressed blocks match byte-for-byte |
| Focused host/linked checks | 93/93, plus 35 host-only checks |
| Full host suite, including restored historical golden reference | 406/406 |

The New Entry regression generates its 20 species contexts through the game's
existing entry setup, using a normally obtained private native-Master-Ball
donor. It is not a claim of 20 separate manually played catches. The golden
reference was rebuilt to its exact historical hash before the full host-suite
rerun; a missing reference is not treated as passing current acceptance.

Early harness-only failures were corrected and rerun: the Select key mapping
was absent, fixed-time region audits sometimes ran before `FindNest` finished,
and cry navigation sent a short B tap before Area reached its real input loop.
The accepted results wait at linked owner boundaries and verify actual unlock
flags. Those earlier failures are not accepted cartridge evidence.

No tested animation deadline miss, active sampled-cache-empty event, palette
write loss or new restoration failure remains in the accepted matrices.
Existing unrelated backlog items, including `DEX-GRID-04` and the battle cry
report, are not closed by these tests.

## Historical Prototype And Reproduction

Retained manual build: `build/dex-area-static-return/pokecrystal-dex-area-prototype.gbc`, with
matching `.sym`/`.map`. An optional same-basename private `.sav` has all species
caught and Kanto unlocked for broad review; it is not the live SameBoy save.

ROM SHA-256:
`7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.
Symbols SHA-256:
`5b63e314adb0606d09f130e1ee18c3ffd3fc7d3feb58e33b04bfb471bd3867ee`.

The retained `tools/build_dex_area_prototype.py` recipe reconstructs the pinned
Git baseline and applies `tools/dex_timing/probes/area_integration.patch`, then
`area_static_return.patch`, to a fresh private checkout. It refuses an existing output folder and verifies the
reviewed ROM hash. An independent clean reconstruction also matches its symbols
and map hashes. Example:

```sh
python3 -B tools/build_dex_area_prototype.py --output build/dex-area-rebuild --jobs 12
```

Use `--variant original` to reproduce the retained first prototype, whose ROM
hash is `43bba18a8541e9d0931dc488ae0561ceb32162da120a9b7f0436bdb820029239`.
An independent clean static-return reconstruction in
`build/dex-area-static-return-full-map-recipe-check/` matches the reviewed ROM,
symbols and map byte-for-byte.

`tools/dex_timing/area_ui.py` owns the reusable normal-input Area checks. Supply
this prototype's ROM/symbols and a source battery; only private copies are
modified. Outputs, cores, checkpoints, reports and images remain ignored.

```sh
PYTHONPATH=tools python3 -B -m dex_timing.area_ui \
  --rom build/dex-area-static-return/pokecrystal-dex-area-prototype.gbc \
  --sym build/dex-area-static-return/pokecrystal-dex-area-prototype.sym \
  --battery build/dex-area-static-return/pokecrystal-dex-area-prototype.sav \
  --output build/dex-area-rerun --exit-keys a b --jobs 12
```

`--uncaught` tests seen-only visibility, `--lock-kanto`/`--unlock-kanto` control
the original restriction, `--player-map`, `--female` and `--hour-offset` create
declared private variants. `--checkpoints` requires matching ROM, symbols and
battery hashes. The consolidated local evidence is
`build/dex-area-static-return/reports/summary.json`; generated artifacts do not ship
with repository documentation.
`--all-pages` adds every available Info/Moves page and both Description pages;
`--repeat-area` checks reopening from the static returned owner; `--follow-up`
checks normal internally paged animation/cry completion; `--direct-listing`
audits the borrowed-panel/palette/map/OAM transaction on immediate B-return.

## Manual Review

1. Use Rattata/Magikarp for visible nests and Dusknoir/Mewtwo for a no-static-nest
   control. Open Area from Description, Info and Moves, both during animation
   and after completion. Also try Description page 2 and an evolution page.
2. Check the vanilla full-screen map/title, blinking markers and Select player
   icon. Try Left/Right, including a pre-Hall-of-Fame save where Right is locked.
3. Return with A and B. Check the restored shell, types, footprint, exact tab,
   page and footer cursor. The frontpic and cry must not restart; evolution
   minis must still animate. Reopen Area, cycle the retained tab's pages, and
   try both direct B-return to Listing and an internal species change. Only
   the species change should start a new frontpic animation/cry.

For the integrated production link and its identical accepted prototype:

```text
breakpoint $a0:$6677
breakpoint $0:$3cc1
```

The first is `Pokedex_AnimationMiss`; the second is the timer's cache-empty
branch after confirming remaining sampled blocks are nonzero, not natural
completion. Neither should trigger on the uninterrupted cases above.
If one triggers or a visible restoration defect appears, retain a screenshot
and save state with `registers`, `backtrace`, `ticks keep` and `lcd`. Include
whether entry was active/settled, the outgoing tab/page, region and exit key.
Do not reuse these addresses for another link; matching symbols remain the
authority. Additional diagnostics are not required unless manual review finds
a problem.

## Assessment

Accepted by the user and integrated as the scoped functional Area implementation.
Complexity is low: reuse the
existing map renderer and existing atomic Selected publisher, with explicit
owner setup/cleanup instead of a new rendering system. Main risks are inherited
palette/scratch ownership and later modifications to shared map routines; the
linked-data and owner-handoff regressions should be retained for those changes.
The root production ROM, symbols and map match the accepted static-return
prototype byte-for-byte. Area's approximately 0.6-second vanilla preparation
remains a measured optimization candidate under `DEX-PERF-02`; acceptance does
not imply that the broader performance story is complete.
