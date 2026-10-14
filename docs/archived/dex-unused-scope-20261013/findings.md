# Unused Pokedex Code Removal Scope

Scope date: 2026-10-13. Baseline commit: `81ff02a25` (Pokedex Enter/Exit
Optimization). This is a removal assessment, not a production integration.

The recommended first prototype can recover **1,661 ROMX bytes** without
changing the accepted renderer architecture or adding RAM. Of that total,
**1,624 bytes are unreachable code/data** and **37 bytes are small live-path
simplifications**. A Dex-only graphics trim increases the total to **1,702
ROMX bytes**. All byte quantities below are decimal.

No allocated ROM0, WRAM0, WRAMX, SRAM or HRAM is recovered by these packages.
The cartridge file remains 4,194,304 bytes; cleanup increases free capacity
inside its existing banks rather than shrinking the file or freeing a complete
16,384-byte bank. Savings are spread across several banks.

## Immediate Unreachable Components

These groups have no remaining production entry path after the indicated
replacement. Private pruning builds verify their linked allocation changes.
The risk column includes maintenance and validation risk, not just whether
the linker accepts the removal.

| Component | ROMX bytes | Complexity | Risk | Replacement or reason |
| --- | ---: | --- | --- | --- |
| Old large OAM selection cursors and records | 454 | Low | Low | Current compact cursor owners replace both main-list and results cursors |
| Old mode explanations and Changing Modes wait | 244 | Low | Low | Current mode-selection owner renders its own content; old wait has no caller |
| Old static wild-location scanner | 146 | Moderate | Moderate | Area uses the indexed lookup; retain its dynamic roamer helpers |
| Old main-list printer and caught-symbol helper | 138 | Low | Low | Current Legacy printer and current Results printer own these lists |
| Obsolete wrapped-grid lookahead refill chain | 124 | Low | Low/moderate | Superseded by accepted lazy row preparation; old entry is behind a return |
| Old Options screen shell and strings | 116 | Low | Low | Current Dex mode-selection screen replaces it |
| Old Selected entry next/previous controller | 81 | Low | Low/moderate | Current Selected owner resolves absolute list positions and return state |
| Unused Info page-number graphics | 64 | Low | Low | Four linked tiles have no consumer |
| Old Info tile-copy implementation | 63 | Low | Low | Current wrapper returns through the fast copier before this old implementation |
| Obsolete Description stop/base-map restore chain | 55 | Low | Moderate | Current owner cancellation and restoration replace this chain |
| Old performance batch admission guard | 38 | Low | Low | Current scheduler uses its own admission policy |
| Orphan printer page-pointer helper | 35 | Low | Moderate | Remaining source references are in printer modules not compiled into production |
| Old raw-text Results type renderer | 34 | Low | Low | Results now render compact type icons |
| Unused BG mode 4 wrappers | 22 | Low | Low | No remaining callers; live mode 3 and reset helpers stay |
| Two helper stubs and two unused strings | 10 | Low | Low | Four-byte index helper, one-byte Selected placeholder, two-byte string, three-byte Number label |
| **Total** | **1,624** | | | |

### Removal Boundaries

1. **Large cursor chain:** `engine/pokedex/pokedex.asm:2597`,
   `Pokedex_UpdateCursorOAM` through the code immediately before
   `Pokedex_PutScrollbarOAM`. This includes the old main cursor updater,
   mode-specific sprite records, results cursor and record loader. Keep
   `Pokedex_PutScrollbarOAM`: the current Legacy owner still calls it.

2. **Mode explanation/wait chain:** `pokedex.asm:2397`,
   `Pokedex_DisplayModeDescription` through the code immediately before
   `Pokedex_UpdateSearchMonType`. The explanation routine and its text occupy
   173 bytes; the Changing Modes routine and string occupy 71 bytes. Keep
   `Pokedex_LoadPointer`, shared text helpers and `SFX_CHANGE_DEX_MODE`.
   The Master Ball animation still uses that sound.

3. **Static nest scanner:** `engine/overworld/wildmons.asm:38`, the `FindNest`
   entry, Johto/Kanto table scans and their search helpers before `.AppendNest`.
   `PokedexPerf_FastNests` in `engine/pokedex/performance_indexed.asm` replaces
   this scan but still farcalls `FindNest.RoamMon1` and `.RoamMon2`. Preserve
   those helpers, `.AppendNest` and the actual encounter-loading code.
   The measurement keeps `FindNest` as a zero-byte namespace label only;
   implementation should rename the retained helper namespace and callers
   together so nobody accidentally treats the new label location as the old
   public scanner. Update observers that still name the old scanner.

4. **Old list printer:** `pokedex.asm:2154`, `Pokedex_PrintListing` (123 bytes),
   plus `Pokedex_PlaceCaughtSymbolIfCaught` at 2258 (15 bytes). Keep
   `Pokedex_PrintNumberIfOldMode`, `Pokedex_PlaceDefaultStringIfNotSeen`,
   the shared name buffer and current Legacy/Results printers.

5. **Refill closure:** `engine/pokedex/pokedex_3.asm:807`,
   `PokedexPerf_LegacyFinalizeWrappedGridCache` (48 bytes), and its otherwise
   unused callee `Pokedex_PrepareGridCacheRefill` at 369 (76 bytes).
   The callee cannot be removed while the old caller is still linked.
   Keep `Pokedex_PrepareGridCacheRow`, the five physical row slots, incoming
   row preparation, pending-row uploads and current wrap preparation.

6. **Old Options screen:** `pokedex.asm:1681`, `Pokedex_DrawOptionScreenBG`
   through the code immediately before `Pokedex_DrawSearchScreenBG`. Current
   option-state handlers delegate to `PokedexListing_InitModeScreen` and
   `PokedexListing_UpdateModeScreen`; they do not use this shell.

7. **Old Selected navigation:** `pokedex.asm:1153`,
   `Pokedex_NextOrPreviousDexEntry` through the code immediately before
   `Pokedex_GridHandleDPadInput`. Keep current linear D-pad helpers: Legacy and
   Results still use them. The old backup cursor/page fields are discussed
   separately below.

8. **Page graphics:** `engine/pokedex/pokedex_description.asm:204`,
   `PokedexInfoPageGFX`, a four-tile slice of the page-number sheet. Delete
   only this unused inclusion. Other sheet tiles and the sheet source still
   serve current pages.

9. **Old Info copier:** `engine/pokedex/pokedex_info.asm:921`,
   `PokedexInfo_CopyTiles_Legacy` through the code immediately before
   `PokedexInfo_UploadTiles`. This name means an older implementation, not the
   currently supported Legacy Dex mode. Keep the fast copier and uploads.

10. **Old Description stop:** `engine/pokedex/pokedex_animation.asm:1419`,
    `Pokedex_RestoreBaseFrontpicMap` plus `Pokedex_StopDescriptionAnimation`
    through the code immediately before `Pokedex_GetAnimationStageMap`.
    Current cancellation does not enter either routine. Keep the active miss
    fallback, owner handoff and resident animation machinery.

11. **Batch guard:** `engine/pokedex/performance_idle.asm`,
    `PokedexPerf_CanBatch`. Its entire linked body is unused. The module include
    can also be removed from `main.asm`; deleting the include itself adds no
    further savings beyond the 38-byte body.

12. **Printer helper:** `engine/pokedex/pokedex_2.asm:241`,
    `GetDexEntryPagePointer`. `engine/printer/print_party.asm` contains its two
    remaining source callers, but that printer module is not a production
    include and its calling labels are absent from the linked ROM. A future
    printer restoration must restore/adapt this API. Keep `GetDexEntryPointer`
    and `PokedexDataPointerTable`.

13. **Results type text:** `pokedex.asm:1792`,
    `Pokedex_PlaceSearchResultsTypeStrings`. Keep the Search form's type-string
    helper and table: they still handle blank dashes and compatibility paths.

14. **BG wrappers:** `pokedex.asm:3400`, `Pokedex_SetBGMapMode4` (10 bytes)
    and `Pokedex_SetBGMapMode_3ifDMG_4ifCGB` (12 bytes). Their removal does not
    alter shared VBlank, STAT, mode 7 or any live BG mode implementation.

15. **Small items:** `Pokedex_GetMonAtOrderIndexDE` at `pokedex.asm:2366`
    (4 bytes), `PokedexSelectedMon_Unavailable` at `pokedex_detail.asm:112`
    (1 byte), `POKeString` at `pokedex_2.asm:218` (2 bytes), and the explicitly
    unreferenced `.Number` string in `Pokedex_DrawDexEntryScreenBG` at
    `pokedex.asm:1672` (3 bytes).

## Small Live Path Simplifications

These are not unreachable instructions. They produce no needed work, but
their removal changes the duration of an active transaction. They belong in a
prototype with timing and visual comparisons rather than a blind deletion.

| Component | ROMX bytes | Complexity | Risk | Required checks |
| --- | ---: | --- | --- | --- |
| Wrapped-grid farcall to a one-byte return stub | 7 | Low | Low/moderate | Both wrap directions, row ownership, display timing |
| Registration footer immediately overwritten before LCD reveal | 30 | Low | Moderate | New Dex Entry, both description pages, catch-to-naming and audio handoff |
| **Additional total** | **37** | | | |

`Pokedex_FinalizeWrappedGridCache` is now a one-byte return. Its six-byte
farcall in `pokedex_animation.asm:118` can go with it. The caller immediately
resets the scroll direction and returns; it does not consume output registers
or flags from the stub. This is separate from the unreachable 124-byte old
refill chain.

`Pokedex_DrawDexEntryScreenBG` prints a 21-byte footer string using nine bytes
of setup/call instructions. Its sole caller, `_NewPokedexEntry`, then replaces
all 20 footer tiles before `EnableLCD`. Removing that dead store preserves the
resulting tilemap, but still warrants authentic registration tests. It does
not require redesigning the New Dex Entry screen first.

## Optional Additional Removals

| Component | ROMX bytes | Other allocated savings | Complexity | Risk and recommendation |
| --- | ---: | --- | --- | --- |
| Dex-only Slowpoke asset prefix | 41 | 0 | Low/moderate | Low/moderate; reasonable separate graphics trim |
| Unused generic move-list marking wrapper | 14 | 0 | Low | Low; optional acquisition-module cleanup |
| Move-discovery query API used by tests | 29 | 0 | Moderate | Moderate; defer until coverage is retargeted |
| Dex SGB graphics and compatibility routing | 437 | 0 | Moderate | Moderate/high; requires explicit CGB-only compatibility policy |
| Obsolete Dex WRAM0 fields/padding | 0 | 0 | Low edit complexity | Moderate layout risk for no allocated RAM benefit; keep reserved |

### Slowpoke Graphics

The Dex includes a 266-byte compressed copy of the Slowpoke sheet. Its old
large-cursor tiles are unused after cursor replacement. Keeping the first 48
tiles produces a 225-byte compressed copy, a measured 41-byte saving. The
retained 768 raw bytes contain every Slowpoke animation frame and the used
scrollbar tile. Compression/decompression roundtrip was checked.

Do not truncate the shared source asset globally. Separate EZ Chat and Password
copies are linked elsewhere and may still need their original cursor tiles.
Add a reproducible Dex-specific prefix output to the asset pipeline instead.
The existing Slowpoke animation and its accepted duration remain unchanged.

### Move Discovery APIs

`MoveDiscovery_MarkMoveList` in `move_acquisition.asm:18` has no current runtime
caller; source-specific acquisition hooks use the underlying helpers directly.
Its 14-byte wrapper can be removed independently.

`MoveDiscovery_CheckIndex` in `move_discovery.asm:14` occupies 29 bytes and has
no production caller, but `tools/dex_timing/move_persistence.py:83` actively
uses it for bit/index, invalid-index and register/bank tests. Current Moves Dex
seen checks use their own snapshot query. Removing this API requires changing
the tests to cover the actual production query/marking contracts, preserving
all positive, negative and restoration checks. Do not accept skipped tests as
replacement coverage. The combined two-API pruning build reclaims 43 bytes.
Neither change alters the bitmap, save format or source hooks.

### SGB Compatibility

The current cartridge header is CGB-exclusive. Nevertheless, explicit SGB and
non-CGB routes still exist in the source. Removing the Dex SGB compressed asset,
both loaders, `Pokedex_CheckSGB`, its startup selection branch and the non-CGB
Unown return graphics branch reclaims a linked 437 bytes. This drops supported
source behavior; it is not ordinary unreachable-code pruning across every
compatibility branch. Generic SGB dispatch, shared palettes and other game
systems are outside this measurement. Keep this out of the default package.

### WRAM0 Overlay

The old navigation backup cursor/page occupy three bytes, the unused last-seen
fields occupy two bytes, and retired animation-counter padding occupies two
bytes. All seven sit within the Dex branch of a 280-byte shared union. Another
owner determines that union's allocation; shortening this branch does not
reduce linked WRAM0. A private field-removal build confirms zero allocated RAM
savings. It also shifts later Dex fields and observer addresses unnecessarily.
Reserve/reuse the holes instead. The 1,402-byte ROMX change in that RAM trial
comes from also deleting the already audited old consumers, not from RAM
compaction. No unused allocated WRAMX, SRAM, HRAM or ROM0 region was identified
for the recommended cleanup.

## After A New Dex Entry Redesign

The automatic post-catch registration screen remains a live user of original
Dex presentation code. Keep it intact during the immediate cleanup. The
following quantities are **gross existing code spans**, not guaranteed net
savings after replacement code or graphics are added.

| Component | Current ROMX bytes | Additional retireable bytes after recommended cleanup | Conditions and risk |
| --- | ---: | ---: | --- |
| Old registration screen shell, `Pokedex_DrawDexEntryScreenBG` | 126 | 93 | New layout must replace its border, divider, height/weight labels and frontpic placement; moderate complexity/risk |
| Old registration initializer, `_NewPokedexEntry` | 100 | Up to 100 gross | Replace setup responsibilities; net savings depend on new code; moderate/high ownership and audio risk |
| Shared entry printer, `DisplayDexEntry` | 224 | 0 from registration redesign alone | Selected Description still calls it; potentially retire its 224-byte span only if both owners are adapted |
| Description printer repair wrapper | 42 | 0 from registration redesign alone | Selected Description uses it; possible replacement/simplification if that printer is also modernized |
| Old footprint loader and placement entry | 19 | 0 automatically | Registration uses them, but non-CGB list/description fallbacks also remain; 12-byte loader plus 7-byte placement entry can go only after those callers are adapted |
| Old right-edge publisher | 56 | 0 automatically | Registration and non-CGB Listing initialization use it; removable only after both paths use a replacement |

The 126-byte screen shell includes the three-byte unused Number string already
counted in immediate cleanup and the 30-byte overwritten footer already counted
in the live-path package. Therefore the later incremental shell saving is
**93 bytes**, not another 126. Without the footer simplification it would be
123 bytes after removing only the unused Number string.

The initializer's 100 bytes include three apparently redundant font/LCD calls
totaling nine bytes: its subsequent `Pokedex_LoadGFX` already disables the LCD,
loads the standard font through the inverted-font loader, and loads the extra
font. These are potential redesign simplifications, not nine more bytes to add
on top of the 100-byte span. Their catch/audio timing impact has not been
measured in this scope.

`PokedexSelectedMon_StageDescription` and the non-CGB description-page toggle
still reach `Pokedex_DisplayDescriptionEntry`, which farcalls `DisplayDexEntry`. That
224-byte printer is therefore not just a registration compatibility fallback.
Its 42-byte wrapper repairs the old divider/page badge for the modern
Description shell; a replacement printer could avoid that repair but still
needs to perform its useful work. No net replacement estimate is claimed.

The footprint graphics and index helper remain useful even if the old upload
and placement entry points are retired. The 11-byte `Pokedex_FillColumn2`
helper also has other active callers, so removing the old right-edge publisher
does not make that helper free.

`GetDexEntryPointer` is shared by current description/text producers.
`PokedexDataPointerTable` and its semantic records are additionally used by
Heavy Ball, Heavy Slam and Pokedex Radio. Removing a presentation routine does
not make the descriptions, species category, height/weight fields or pointer
table disposable. Preserve those interfaces or explicitly migrate every user.

A layout redesign alone also does not retire the New Entry animation producer,
ROM0 publication callbacks, sampled-cry ownership, common frontpic functions,
shared fonts, palettes or entire core Dex graphic sheet. Their responsibilities
still exist. Any later consolidation must be measured as its own architectural
change; no speculative ROM0 recovery is included here.

## Items That Must Stay

- Current Legacy Mode, compact cursor/scrollbar assets, current list-order and
  seen/default-name helpers. An old routine's name does not identify its owner.
- Accepted precomputed Selected Info/Moves/ancestor metadata and glyph atlases,
  rendering buffers and restoration machinery. This is not a runtime-renderer
  conversion and does not revisit the approved performance/space decision.
- Current Area index and semantic encounter tables, including live roamer
  helpers. Removing the old scanner must not touch encounter generation.
- Active Description miss fallbacks, cancellation, sampled/synthesized cry
  handling, Type Matchups owner and isolated mode 7 display handling.
- Shared ROM0/interrupt helpers and battle-sensitive dispatch. No ISR overhead,
  ROM0 reservation or HRAM allocation changes are proposed.
- Live fallthrough blocks, including `Pokedex_PlaceFrontpicAtHLWithTile`,
  `Pokedex_AnimationMiss`, `PokedexPopover_StageDraw`,
  `PokedexMovesMode_UploadSortBorder` and New Entry publication/completion labels.
  Deleting an observer label saves zero bytes; deleting its following body can
  break the active path despite there being no direct call to that label.
- Archived runtime/VRAM recovery and precomputed Type fallback handoffs. They
  are not production includes. Removing archives, unlinked printer source or
  ignored build outputs yields zero cartridge-space savings.

## Measurement And Qualification

The private control build is byte-identical to production. Production ROM
SHA-256 before/after the scope:

```text
e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e
```

Production allocation: ROM0 15,905; ROMX 2,345,898; WRAM0 4,083; WRAMX 24,010;
SRAM 49,994; HRAM 127 bytes. Root production and the installed SameBoy ROM
remain identical. No player battery was changed.

| Private package | Reclaimed ROMX | Remaining allocated ROMX | ROM0 / WRAM0 / WRAMX / SRAM / HRAM reclaimed |
| --- | ---: | ---: | --- |
| Unchanged control | 0 | 2,345,898 | 0 / 0 / 0 / 0 / 0 |
| Unreachable components | 1,624 | 2,344,274 | 0 / 0 / 0 / 0 / 0 |
| Recommended code cleanup | 1,661 | 2,344,237 | 0 / 0 / 0 / 0 / 0 |
| Recommended plus Dex asset trim | 1,702 | 2,344,196 | 0 / 0 / 0 / 0 / 0 |

The 14-byte acquisition wrapper, 29-byte test query API and 437-byte SGB policy
option are excluded from these combined packages. Their per-component sizes
are available above; adding them requires the corresponding scope/coverage
decision rather than silently treating them as part of the default cleanup.

Evidence lives in `build/dex-unused-scope-20261013/`: `inventory.json`,
`trials/results.json`, `trials/extras.json`, per-variant build logs, ROMs,
symbols and maps. `tools/dex_timing/dex_unused_scope.py` inventories actual
production includes and reproduces explicit private pruning builds. It never
edits production game source. Run from the repository root:

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_unused_scope inventory
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_unused_scope trials
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_unused_scope extras
```

The inventory is a static aid, not a reachability proof: strings, macro aliases,
conditional code, indirect tables, include boundaries and fallthrough need
manual inspection. The removed groups were checked against production callers,
dispatch/predef data, active replacement paths and linked symbols. Initial
rapid-build measurements that reused stale objects were rejected; final probes
delete private generated objects before each link. The unchanged control
matches production byte for byte. Removing only the refill callee correctly
failed while its old caller remained; the successful 124-byte probe removes
the dependency closure together.

**Qualification so far is source/reference inspection, private build/link
checks, exact allocation comparisons and the asset roundtrip. No cleanup
candidate has received the full runtime regression suite or manual acceptance.**
Link success alone does not prove visual, audio or timing equivalence.

## Suggested Implementation Order

1. Prototype the 1,624-byte unreachable-code package. Keep the seven overlay
   holes and all compatibility policy unchanged. Rename the retained nest
   helper namespace and adapt any observer/host assertions that intentionally
   reference removed APIs; do not weaken behavioral coverage.
2. Include the seven-byte wrap no-op and 30-byte footer dead store if their
   focused wrap and authentic-catch comparisons preserve behavior. This is the
   1,661-byte recommended code package.
3. Add the 41-byte Dex-specific asset prefix as a separate reproducible change
   and verify every Search animation frame, compact cursor and scrollbar.
4. Run [Full Regression Suite](full_regression_suite.md) against fresh matching
   baseline/candidate ROMs, symbols and source. Recreate checkpoints after each
   link; old saved CPU states are not safe after address relocation.
5. Cover Modern/Legacy list movement and wraps, Search/results, all Selected
   tabs and ancestors, Unown, Moves/search/text entry, Type Matchups and return
   restoration. Include Area/roamer contexts, all-species New Entry/catch/naming,
   sampled cries/audio, discovery/persistence, all moves from both battle sides,
   custom menus, PC/daycare and surrounding gameplay. Compare entry/exit,
   paging, cry and battle timings against the committed baseline.
6. Obtain manual acceptance before production integration. Queue further
   registration-only removals behind the New Dex Entry redesign rather than
   removing a live shared printer now.

Most deletion work is low complexity; helper ownership, renamed observer
interfaces and complete qualification dominate the cost. The recommended
package introduces no new subsystem, save migration, buffer or graphics
architecture. Its main risks are cutting a retained shared dependency or
mistaking an observer/fallthrough label for a dead entry point.
