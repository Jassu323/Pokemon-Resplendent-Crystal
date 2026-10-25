# Pokedex Cleanup After New Entry Redesign

Historical scope. The approved combined removal is now integrated and
qualified; see [Cleanup Implementation](pokedex_cleanup_implementation.md).
The measurements and pending-status statements below describe the audit
before implementation, not the current checkout.

Assessed 2026-10-14 against the accepted red-footer New Entry prototype,
SHA-256 `a5dd313b939a99d92c2b18169be403f14d6a052877890a382005a420d53793fe`.
Production is still commit `81ff02a25`; the accepted layout is not integrated
there yet. All quantities below are decimal bytes from fresh private links.

The recommended code cleanup recovers **1,754 ROMX bytes**. Keeping only the
used prefix of the Dex's separate Slowpoke asset raises that to **1,795**.
An optional unused acquisition wrapper raises it to **1,809**. None of these
packages recovers allocated ROM0, WRAM0, WRAMX, SRAM or HRAM.

This is the updated scope, not runtime acceptance of the removal builds.
Production and the installed review ROM were not modified.

## Confirmed Removal Components

| Component | ROMX bytes | Complexity | Risk |
| --- | ---: | --- | --- |
| Old large OAM cursors and sprite records | 454 | Low | Low |
| Old mode explanations and Changing Modes wait | 244 | Low | Low |
| Old static Area nest scanner, preserving roamer helpers | 146 | Moderate | Moderate |
| Old main-list printer and caught-symbol helper | 138 | Low | Low |
| Old New Dex Entry screen builder, labels and footer | 126 | Low | Low |
| Obsolete wrapped-grid refill chain | 124 | Low | Low/moderate |
| Old Options screen builder and strings | 116 | Low | Low |
| Old Selected next/previous controller | 81 | Low | Low/moderate |
| Unused Info page-number graphics | 64 | Low | Low |
| Old Info tile copier | 63 | Low | Low |
| Obsolete Description stop/base-map restore chain | 55 | Low | Moderate |
| Unused old performance batch guard | 38 | Low | Low |
| Orphan printer page-pointer helper | 35 | Low | Moderate |
| Old raw-text Search Results type renderer | 34 | Low | Low |
| Unused BG mode 4 wrappers | 22 | Low | Low |
| Two unused helper stubs and the POKe string | 7 | Low | Low |
| **Unreachable code/data total** | **1,747** | | |
| Live wrap call to a return-only stub, plus that stub | 7 | Low | Low/moderate |
| **Recommended code total** | **1,754** | | |
| Dex-only Slowpoke prefix trim | 41 | Low/moderate | Low/moderate |
| **Code and graphics total** | **1,795** | | |

The earlier [removal scope](pokedex_unused_code_scope.md) retains exact source
boundaries and ownership explanations for the unchanged groups. This cleanup
does not remove the supported Legacy Dex mode, current Search/results owners,
current cursor/scrollbar graphics, animation scheduler or current Info renderer.

### Newly Dead Registration Builder

`Pokedex_DrawDexEntryScreenBG`, in `engine/pokedex/pokedex.asm`, has no remaining
compiled caller in the updated New Entry build. Its 126-byte span includes the
old border/divider setup, height/weight labels, unused Number string and old
`Desc Stat Mov Area` footer string. Remove the span up to, but not including,
`Pokedex_DrawOptionScreenBG`; remove that separate Options block as its own
listed component.

The replacement calls `Pokedex_DrawDescriptionScreenBG`,
`Pokedex_CopyDescriptionRightEdge` and `Pokedex_DisplayDescriptionEntry`, then
sets its registration-only red footer. Nothing needs to replace the dead
builder, so its deletion adds no code, graphics or RAM.

### Avoid Double Counting

The former 1,624-byte dead-code package already counted the builder's three-byte
Number string. Removing the whole builder therefore increases that package by
123, giving 1,747, not 1,750.

The former 1,661-byte recommended package also counted 30 bytes for the old
overwritten footer. The newly dead complete builder adds only the remaining
93 to that package: **1,661 + 93 = 1,754**. Likewise,
**1,702 + 93 = 1,795** for the code-and-asset package.

### Implementation Boundaries

The Area deletion must retain `.AppendNest`, `.RoamMon1` and `.RoamMon2`, which
the indexed Area owner still uses. Rename the retained helper namespace and
its two current callers rather than leaving a misleading `FindNest` public
entry pointing at a different operation. Update the native observer's old
`find_nests` symbol target. Renaming labels adds no cartridge bytes.

Remove the old wrapped-grid caller and its unused refill callee together; do
not delete the callee while leaving a linked caller. Current lazy row slots,
row preparation/upload and wrap state remain live. Remove the batch-guard
module's unused include as source cleanup, without claiming additional bytes
beyond its 38-byte body.

The printer helper's remaining source references are in an uncompiled printer
module. Restoring printer support later requires restoring or adapting this
API. Retain the shared description pointer and semantic records.

For the Slowpoke trim, add a reproducible Dex-specific 48-tile prefix output to
the graphics pipeline. The retained raw 768 bytes preserve the animation and
used scrollbar tile. Their compressed representation is 225 bytes instead of
266, saving 41. Compression/decompression roundtrip was verified. The original
restriction about preserving the mobile copies is superseded by the focused
retirement audit below: they can be removed with their obsolete loads and
retired-entry guards. Do not silently shorten graphics while retaining active
loaders for screens that expect the complete sheet.

## Mobile Slowpoke Follow-Up Audit

Audited 2026-10-14 against the same accepted red-footer base. The user confirms
the game is permanently CGB-only and that EZ Chat/Mobile Password are retired.
This is a private audit, not production integration or full runtime acceptance.

### Exact Data And Surviving References

Both linked copies contain the same 266-byte compressed blob, SHA-256
`caafc3b0193cefe4b5b53afdc152e2af8ac527d0f12367ffcba64b1eb1ec928d`.
The measured data return is therefore exactly **532 ROMX bytes**, independent
of the Dex copy and its separate 41-byte prefix trim.

| Copy | Source | Bytes | Linked loads |
| --- | --- | ---: | --- |
| `EZChatSlowpokeLZ` | `mobile/fixed_words.asm:3235` | 266 | `Function11c1b9.InitKanaMode`, line 318 |
| `PasswordSlowpokeLZ` | `mobile/mobile_5c.asm:776` | 266 | `Function171c87`, line 660; `Function171d2b`, line 732 |

These are not unreferenced data labels. Deleting only the assets was deliberately
tested and rejected: linking fails with exactly three unresolved loads. Do not
claim that the mobile40 stubs have already eliminated these dependencies.

`mobile/mobile_menu.asm` is not in the compiled include closure. Its direct
calls to the EZ Chat entry, Password entry and mobile-center entry therefore
do not establish current reachability. Their remaining linked ownership is:

- `mobile/fixed_words.asm` is included from
  `engine/events/battle_tower/trainer_text.asm:77`. `Function11c1ab` still has
  an entry in `data/events/special_pointers.asm:149`, although no current map
  script invokes that special. It calls `Function11c1b9`, which loads the copy.
- `mobile/mobile_45_stadium.asm` remains included by `main.asm`. The Password
  entry `Function11765d` reaches `Function117699`, which calls `Function171c87`.
  Three calls to that entry survive in the mobile login/error branches of
  `mobile/mobile_46.asm:4333`, `4359` and `4381`.
- `mobile/mobile_5c.asm` remains included because it also contains live Battle
  Tower functionality. The mobile-center entry `Function1719c8` leads through
  `Function1719ed` to `Function171d2b`. Its only direct source caller is in the
  uncompiled mobile menu.

The ordinary Battle Tower receptionist's challenge path uses
`BattleTowerRoomMenu`, `_BattleTowerRoomMenu` and the normal level-menu states
0 through 12. Challenge completion exits at state 3. Cancel confirmation uses
`BattleTowerRoomMenu2` states 15/16, whose Yes/No handlers return rather than
enter the login/Password branch. The surviving Password calls belong to a
different RoomMenu2 login branch, not that supported level/cancel sequence.
This is a source/control-flow audit, not a native menu replay claim.

### Measured Removal Variants

| Variant | Build result | Additional ROMX reclaimed |
| --- | --- | ---: |
| Unchanged control | Pass; byte-identical to accepted base | 0 |
| Delete the two assets alone | Expected failure: three unresolved loads | Not accepted |
| Assets plus three obsolete decompression sequences | Pass | 559 |
| Above plus three retired-entry return guards | Pass | 598 |

The load sequences are each nine bytes: `ld hl`, `ld de`, `call Decompress`.
Removing three returns **27 bytes**, making **532 + 27 = 559**. The guarded
variant replaces each of the 14-byte wrappers `Function11c1ab`,
`Function11765d` and `Function1719c8` with a one-byte `ret`. This returns
another **39 bytes**, making **598**. All three RET opcodes were verified in
the linked ROM. Their public labels, the special-pointer slot and all following
helper labels remain; no special IDs or RAM layouts shift.

The guarded variant is preferable to leaving obsolete interactive entry points
available without their graphics. It explicitly prevents those three retired
screens from starting. This is an intentional retirement of unsupported screen
behavior, not a promise to preserve the appearance of a forced mobile login.
Internal old UI helpers are left linked in this narrow probe; a larger mobile
dead-code cleanup would need its own audit. Do not remove whole includes merely
because they are named mobile.

Preserved: the Dex Slowpoke blob, animation and timing; live Battle Tower code,
trainer text and level/cancel menus; `GiveOddEgg`; sprite-animation callbacks;
Password fonts/palettes/maps and other unrelated mobile resources. None of
those retained resources is counted as additional savings. The normal Dex
graphics source is unchanged. Every successful variant changes zero allocated
ROM0, WRAM0, WRAMX, SRAM and HRAM bytes.

### Qualification And Reproduction

Four source-boundary tests pass: the rejected data-only edit retains all three
real references; load deletion does not alter font/LCD setup; guard boundaries
preserve public/following labels and live Battle Tower/Odd Egg functions; and
the graphics-owning modules are compiled while the mobile menu is not.
The unchanged control reproduces the accepted ROM exactly. Protected production
and accepted-base ROM/symbol/map hashes remain unchanged.

Evidence is in `build/dex-mobile-slowpoke-audit-20261014/`: original reference
inventory, manifests, four patches/logs and the three successful ROM/symbol/map
sets. Its working source ends on `guarded-retirement`; apply each saved patch
to the recorded base when restoring another variant. Reproduce with:

```sh
export PYTHONPATH=tools:.
python3 -m unittest tools.test_mobile_slowpoke_cleanup
python3 -m tools.dex_timing.mobile_slowpoke_cleanup --output build/dex-mobile-slowpoke-new-audit
```

Recommend the **598-byte guarded retirement** as a separate low/moderate-risk
cleanup component. It requires no replacement asset, added RAM, save migration,
shared interrupt work or supported-gameplay timing change by design. Fresh
full runtime regression has not been run on this audit build. Before promotion,
recreate matching-link fixtures and test ordinary Battle Tower challenge/level
selection, restrictions, cancel Yes/No, battles/rewards/resume, plus Odd Egg,
normal naming and both Pokemon/Moves Search animations. Include the normal
full Dex/gameplay regression because relinking moves downstream code/data.
Do not add this 598-byte component to the published 1,795-byte package as a
combined measured result until the combined candidate is built and qualified.

## Additional Options

These are separate decisions, excluded from the default 1,795-byte package.

| Option | Additional ROMX bytes | Complexity | Risk and condition |
| --- | ---: | --- | --- |
| Unused `MoveDiscovery_MarkMoveList` wrapper | 14 | Low | Low; no runtime or test caller; source-specific hooks remain |
| Duplicate New Entry LCD/font setup calls | 9 | Low | Moderate; active timing changes need native catch/audio comparison |
| Test-used `MoveDiscovery_CheckIndex` API | 29 | Moderate | Moderate; persistence/index/register tests must be retargeted, not skipped |
| Dex SGB asset/loaders and old compatibility routing | 437 | Moderate | Moderate/high; explicit CGB-only policy change |
| Old Listing edge publisher and its compatibility branch | 71 | Low/moderate | Moderate; explicitly abandon non-CGB Listing setup |
| New Entry adapter's non-CGB fallback | 17 | Low | Moderate; explicitly abandon that compatibility route |
| **Combined measured compatibility subset** | **525** | Moderate | Moderate/high; not ordinary dead-code pruning |

The 71-byte edge option comprises the still-live 56-byte
`DrawDexEntryScreenRightEdge` plus 15 bytes of Listing compatibility routing.
Registration no longer calls it, but `Pokedex_InitListingRightEdge` still does
on its non-CGB path. `Pokedex_FillColumn2` remains live in current Listing and
Search Results rendering even if this edge option is adopted.

The nine setup bytes are three calls in the current 107-byte
`_NewPokedexEntry`: `DisableLCD`, `LoadStandardFont` and `LoadFontsExtra`.
`Pokedex_LoadGFX` subsequently disables the LCD, loads the standard font through
the inverted-font loader, and loads the extra font again. The private link
confirms the nine-byte return; behavior/timing equivalence remains to be tested.
The initializer itself is live and is not a 107-byte deletion candidate.

The cartridge header is CGB-exclusive, but removing compatibility branches
changes the source's supported fallback behavior and its synthetic test cases.
The 525-byte option is a specific measured subset, not an estimate for removing
every non-CGB branch throughout the game. Generic ROM0/SGB dispatch and other
systems are outside its scope.

## Components That Stay

| Component | Current ROMX bytes | Why it stays |
| --- | ---: | --- |
| `_NewPokedexEntry` | 107 | Current registration initialization, graphics and animation setup |
| `DisplayDexEntry` | 224 | Shared modern Description printer, reached through its wrapper |
| `Pokedex_DisplayDescriptionEntry` | 42 | Used by registration, Selected preparation and description-page switching |
| Old footprint upload/placement entries | 19 | Registration still uses bank-0 footprint tiles; compatibility callers also remain |
| `DrawDexEntryScreenRightEdge` | 56 | Non-CGB Listing caller remains unless compatibility policy changes |
| `Pokedex_FillColumn2` | 11 | Current Listing and Results still call it |

Keep the chosen precomputed Selected Info/Moves/ancestor tables and glyphs.
They remain live and were explicitly retained for responsiveness. Removing
them would reopen the separate renderer architecture decision, not clean up
unused code. Keep semantic species descriptions, categories, height/weight
records and pointers used by Heavy Ball, Heavy Slam and Pokedex Radio.

There is no newly dead complete font, palette, core Dex graphics sheet,
resident animation module, sampled-cry owner or shared interrupt implementation
to remove. Any additional core-sheet tile trim requires a separate per-tile
consumer audit; no speculative saving is included here. Observer-only labels
and live fallthrough bodies are not removable code just because their names
have no textual callers.

Seven obsolete Dex overlay bytes still produce zero allocated WRAM0 savings:
another owner determines the union size. Keep those holes reserved/reusable
rather than shifting live fields and observer addresses for no RAM return.

## Space Accounting

The accepted New Entry layout currently adds 277 ROMX bytes over production.
To compare the combined result against the existing production ROM, subtract
that cost from the cleanup return:

| Package | Reclaimed from accepted New Entry build | Net reclaimed from current production after adding New Entry | Remaining ROMX allocation |
| --- | ---: | ---: | ---: |
| Dead code/data only | 1,747 | 1,470 | 2,344,428 |
| Recommended code | 1,754 | 1,477 | 2,344,421 |
| Code and Slowpoke trim | 1,795 | 1,518 | 2,344,380 |
| Above plus unused acquisition wrapper | 1,809 | 1,532 | 2,344,366 |

Every linked option measured zero change to allocated ROM0, WRAM0, WRAMX,
SRAM and HRAM. The 4,194,304-byte cartridge file does not shrink; existing ROM
banks gain free space. These savings do not free a complete 16,384-byte bank.

## Evidence And Next Step

Thirteen fresh private variants built successfully. The unchanged control
reproduces the accepted New Entry ROM byte-for-byte. The fresh include/reference
inventory excludes patch backup files and inactive printer source from the
compiled closure. Source-boundary regression checks pass in three unit tests.

Results, maps, ROMs, patches and logs are in
`build/dex-unused-post-entry-20261014/`; reproduce with:

```sh
export PYTHONPATH=tools:.
python3 -m tools.dex_timing.dex_post_entry_cleanup --output build/dex-cleanup-new-measurement
python3 -m unittest tools.test_dex_post_entry_cleanup
```

Each patch applies to the recorded red-footer New Entry source. The asset
variant also requires the prefix blob from the trial working tree's `build/`.
The single working tree ends on the last variant; do not pair that source with
another variant's ROM/symbols without restoring its own patch to the base.

Two initial probe attempts are retained. The first stopped on deletion ordering
before producing a combined result. In the second, two compatibility probes
were rejected because a source selector matched the branch operand instead of
the `.cgb` label. Corrected source boundaries and targeted regression tests
produce the final 17/525-byte policy results. Only `trials/results.json` is the
accepted measurement set.

Recommended implementation: the 1,754-byte code package, optionally the 41-byte
Dex-only asset trim and 14-byte unused acquisition wrapper. Defer the test-used
query API and compatibility policy. Measure the nine-byte active setup trim
separately. Before promotion, recreate matching-link fixtures and run the
full documented Dex, New Entry, battle-animation/audio, persistence and
surrounding-gameplay suite, including raw timing comparisons and both catch
delivery/naming paths. Build/link success is not a substitute for that suite.
