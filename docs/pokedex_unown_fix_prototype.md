# Unown Mode Correctness Prototype

2026-10-11. Private repair of `DEX-UNOWN-01/02`, based on the current
no-warming prototype. Automated qualification passed; manual acceptance and
production promotion remain pending.

The [black-panel revision](#black-panel-revision) below is the latest review
build. The red-backdrop revision is preserved as its rollback.

## Review Files

- ROM/save: `build/dex-unown-fix-20261011/pokecrystal-dex-unown-fix.{gbc,sav}`.
- All-26-Unown review pair: `build/dex-unown-fix-20261011/all-unown-review/pokecrystal-dex-unown-fix.{gbc,sav}`.
- All-333-moves review pair: `build/dex-unown-fix-20261011/all-seen-review/pokecrystal-dex-unown-fix.{gbc,sav}`.
- Qualification: `build/dex-unown-fix-20261011/unown-qualification.json`.
- Private source: `build/dex-unown-fix-20261011/candidate/`.
- Unchanged rollback: `build/dex-no-warming-20261011/`.

New ROM SHA-256:
`4103150a13c4198fc46d31ecdb208dc7c57e843912845a7e9d76bcbbd509be3d`.
Rollback ROM SHA-256:
`555bd3fbfc396630d8ed88987d705a4fbd153650b5041540b0c8d18128293a1d`.
A second independent private rebuild produces the same new ROM bytes.

The ordinary review save is an unchanged copy of the previous prototype's
save. The separate all-Unown battery unlocks the mode and declares A-Z caught
in both checksummed records, while retaining the ordinary save's progression
and move discoveries. Its exact published bytes are confirmed through native
normal-input entry/navigation. Neither a player save nor production is updated.

## Repair

Only `Pokedex_DrawUnownModeBG` in `engine/pokedex/pokedex.asm` changes relative
to the rollback. Before placing caught letters, its CGB path initializes all
52 letter/cursor coordinates with existing resident bank-1 dark-gray tile
`$32`. This matches the overlay's existing bank attributes, instead of leaving
bank-0 `$7f` references under bank-1 attributes. It does not rewrite the shared
bank-1 `$7f` graphics, borrow new tiles or alter the coordinates.

The form conversion preserves BC around its use of C as a temporary form ID.
The loop therefore retains its 26-form bound, stops at the first unused entry,
and correctly counts all caught forms in encounter order. Both CGB and DMG
code paths retain their intended tile conversion.

Cost is **23 additional ROMX bytes** versus the no-warming rollback, or
**35 fewer ROMX bytes** than committed production when combined with the
retained warming removal. ROM0, SRAM, WRAM0, WRAMX and HRAM usage and addresses
are unchanged. No artwork, save migration, animation policy or latency
optimization is included. Production remains at the previous Moves Dex commit.

## Qualification

All fresh checks on the new link passed:

- 136 normal-input Unown fixtures, covering every individual form, sparse
  collections, A first/middle/last, no A, ascending/reversed/rotated/shuffled
  catch orders, all 26 forms, both Listing origins and input phases.
- 2,212 forward/backward form selections; count/index/order, every frontpic,
  footer word, cursor placement and 141,568 overlay-cell tile/bank/pixel checks.
  Bounds, return-menu selection and subsequent Selected animation/cry playback
  also pass. Content checks include prior Info and Moves visits.
- 126 isolated native drawing calls exercise both code branches, empty through
  full-capacity arrays, a poisoned following byte, stack/bank/SRAM restoration
  and unchanged caught data. These test the DMG branch on the CGB native core;
  they are not a complete DMG-hardware visual campaign.
- Two negative controls confirm the same content/pixel oracle rejects both
  existing defects in the unchanged rollback.
- 4,479 established Pokemon Dex fixtures, including all 373 species in three
  orders/both presentations, navigation, popovers, Selected subpages and Search.
  Sixteen extra prior-Info/Moves fixtures check another 96 coherent transitions.
- Complete Moves list/search UI suites: 1,692 filter cases, ten completion
  fixtures/232 keyboard navigation checks, 1,406 visuals, 2,686 navigation checks,
  eleven transitions, two Save/Continue roundtrips, 1,284 form/footer checks and
  3,840 naming-cursor checks. No new functional or visual failures.
- All graphics bytes match the rollback; 7,096 protected production inputs,
  production outputs and rollback ROM/save remain unchanged.

The dedicated Unown content/pixel checks close the coverage gap described in
the [investigation](pokedex_unown_investigation.md). This narrow repair reruns
the Dex and ordinary save/load suites, not the previous full battle, sampled-
cry, interrupted-save or migration campaigns. Their owners remain unchanged.
Native emulator validation does not replace manual review or real-hardware
testing. Deferred Unown entry/return performance work remains separate.

Screenshots: `unown-tests/single-01-p0-q0/form-00.png`,
`unown-tests/ascending-26-p0-q0/form-00.png` and `form-25.png` under the new
build directory. These are unmodified native captures, not new artwork.

## Reproduction

```sh
PYTHONPATH=tools:. python3 tools/build_dex_unown_prototype.py \
  --base build/dex-no-warming-20261011 --output build/dex-unown-fix-20261011
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search_dex_regression prepare \
  --output build/dex-unown-fix-20261011
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search prepare \
  --output build/dex-unown-fix-20261011
PYTHONPATH=tools:. python3 -m tools.dex_timing.unown_regression \
  --output build/dex-unown-fix-20261011 --jobs 6
```

Run `moves_search_dex_regression` with `listings` and `interfaces`, then
`unown_qualification` with `dex`, `moves` and `qualify`, each using the same
`--output`. The builder requires a fresh private directory and the retained
rollback source/fixtures; the supplied `.diff` applies only to its private copy.

## Red Backdrop Revision

2026-10-11. `DEX-UNOWN-03` corrects a further user-identified mismatch: the
outer canvas was dark gray except for red pixels supplied by the border tiles.
The original content oracle covered letter/cursor/word cells but omitted the
outer backdrop. The initial repair's qualification did not establish that
the entire Unown screen matched vanilla's intended presentation.

Status: full native qualification passed; manual review/promotion pending.

Red-backdrop review files are under `build/dex-unown-background-20261011/`:

- `pokecrystal-dex-unown-fix.{gbc,sav}`: ordinary review pair.
- `all-unown-review/pokecrystal-dex-unown-fix.{gbc,sav}`: all 26 forms caught.
- `all-seen-review/pokecrystal-dex-unown-fix.{gbc,sav}`: all 333 moves seen.
- `unown-qualification.json`: final acceptance checks.
- `unown-backdrop-comparison.json`: six direct native pixel comparisons.
- `unown-tests/`: expanded content, navigation and screenshots.

New ROM SHA-256:
`80737cf94facc4da8be0313d48edac0e11d290ceb5049b1046729d5ad74f23eb`.
The unchanged rollback is `build/dex-unown-fix-20261011/`, SHA-256
`4103150a13c4198fc46d31ecdb208dc7c57e843912845a7e9d76bcbbd509be3d`.
A second private rebuild produces identical ROM bytes.

Only Unown's drawing routine changes again. Its initial CGB full-screen fill
now selects existing bank-0 red tile `$31`, before drawing the framed panels.
The DMG branch retains its former `$32` fill. Panel interiors and resident
bank-1 font/cursor blank cells remain dark gray. No shared fill routine,
palette, graphics, save data or animation policy changes.

This revision costs **15 ROMX bytes** versus the first repair. The combined
repair adds 38 bytes versus no-warming alone, leaving 20 fewer ROMX bytes than
committed production. All other memory usage and addresses remain unchanged.

Expanded checks on this ROM:

- 136 native Unown fixtures and 2,212 forward/backward selections still pass,
  including all forms, sparse collections, catch orders, both Listing origins
  and prior Info/Moves visits. All 141,568 existing overlay-cell checks pass.
- Every selection checks all 135 outer tiles and their displayed pixels:
  **298,620 outer tile/bank/pixel checks**. The expected red is native upstream
  RGB `(214,82,49)`, also the project's `RGB 26,10,6` palette entry.
- Six independent screenshots cover one/full collections, A/Z selection and
  both origins. Each has all 8,640 outer pixels exactly matching the vanilla
  reference, and all 14,400 framed-panel pixels identical to the first repair.
- 126 native drawing calls still pass. They additionally verify the CGB red
  outer fill and retained DMG fill, without changing the existing branch limits.
- Three negative controls detect the original two defects and independently
  reject the first repair's outer-gray backdrop. The latter has no unrelated
  content failures, confirming this is a distinct presentation issue.
- All 4,479 Pokemon Dex fixtures pass again, along with sixteen additional
  prior-Info/Moves transition fixtures and the full Moves UI/Search suites
  enumerated above. Ordinary Save/Continue roundtrips also pass. No new
  functional, visual or coherent-transition failures are present.
- The final qualifier preserves all 7,096 protected production inputs, all
  graphics bytes and the previous prototype's ROM/save. The published all-26
  review battery is also confirmed through normal-input native navigation.

Screenshots use the same relative paths as the first repair, under the latest
directory. They are native captures; no new artwork is generated. As before,
manual review remains required, and production is not promoted by this work.

To build this revision, use a fresh directory and the retained first-repair base:

```sh
PYTHONPATH=tools:. python3 tools/build_dex_unown_prototype.py \
  --base build/dex-unown-fix-20261011 \
  --output build/dex-unown-background-20261011 --red-background
```

Repeat the same preparation and native suites described above, using the new
output directory. The final qualifier checks the full Pokemon/Moves reports,
backdrop comparisons, immutable production/rollback inputs and published review
save through normal-input navigation.

## Black Panel Revision

2026-10-11. `DEX-UNOWN-04` addresses the remaining user-identified contrast:
inverted Unown letters have black tile backgrounds, while the panel fill and
unused overlays were dark gray. The portrait palette also covered `(7,5)` to
`(13,11)`, one tile right of the actual picture at `(6,5)` to `(12,11)`; its
second gray could therefore color the empty strip alongside the portrait.

Status: full native qualification passed; manual acceptance/promotion pending.

Latest review files are under `build/dex-unown-black-20261011/`. The ROM stem
remains `pokecrystal-dex-unown-fix`; the ordinary save is unchanged from the
red-backdrop revision. The final qualifier publishes and verifies the separate
`all-unown-review/` ROM/save pair with all 26 forms caught.

ROM SHA-256:
`591d2075b0c986846b94bc92288d1fa4f9d2918fccc680a83928fd8fdcf59bee`.
Rollback: `build/dex-unown-background-20261011/`, SHA-256
`80737cf94facc4da8be0313d48edac0e11d290ceb5049b1046729d5ad74f23eb`.
An independent private rebuild produces the same ROM bytes.

Only `_CGB_PokedexUnownMode` and its local palette in
`engine/gfx/cgb_layouts.asm` change relative to that rollback. The standard
bank-preserving palette loader loads a dedicated white/red/black/black palette
for this screen. The shared `PokedexUIPalette` and resident graphics are
unchanged. Both framed panels now use solid black, while the outer canvas
remains red and the frontpic retains its own palette and white field. The
portrait attribute rectangle now matches its actual seven-by-seven tile map.
No other Dex palette is changed.

Cost: **8 ROMX bytes** versus the red-backdrop revision, 46 bytes versus the
no-warming prototype, or 12 fewer ROMX bytes than committed production. All
other resource usage and memory addresses remain unchanged. No new assets,
save changes, animation changes or production integration are included.

The expanded oracle independently requires the exact white/red/black/black
palette, solid-black blank-cell pixels, portrait palette ownership over exactly
49 cells and native portrait pixels matching the existing asset and mon palette.
It retains the original form/count/bank/navigation and red-canvas checks. A
new negative control must reject the preceding revision's gray panels and
misaligned portrait attributes, separately from the older faults. Screenshot
comparisons allow only the intended gray-to-black conversion outside the
portrait; white/red/black border and glyph pixels must remain unchanged.

All fresh qualification checks passed on this ROM:

- 136 normal-input Unown fixtures and 2,212 forward/backward selections:
  141,568 overlay cells, 298,620 red-canvas cells, **151,734 solid-black panel
  cells** and **108,388 portrait cells**, with native displayed-pixel checks.
  All forms, sparse/full collections, encounter orders, both Listing origins,
  prior Info/Moves visits, selection bounds and subsequent playback pass.
- 126 isolated draw calls retain the original CGB/DMG branch, count, guard,
  bank/register/stack and SRAM-restoration checks. Four negative controls
  separately detect the original content faults, gray canvas and gray-panel/
  portrait-boundary faults in preserved earlier builds.
- Six independent screenshot comparisons preserve all 8,640 outer red pixels
  per capture and validate the intended panel conversion over 11,264 UI pixels.
  Actual portrait pixels are independently verified against the existing
  graphics and portrait palette across all tested selections.
- All 4,479 Pokemon Dex cases pass, plus sixteen additional prior-Info/Moves
  return fixtures with 96 transitions. The complete Moves UI/Search suites
  enumerated above pass again, including ordinary Save/Continue roundtrips.
- The final qualifier confirms all 7,096 protected production inputs, all
  graphics bytes, unchanged RAM addresses and the preserved rollback ROM/save.
  The exact published all-26 review battery passes native normal-input entry
  and all 51 forward/backward selections. The independent rebuild is identical.

Final report: `unown-qualification.json`; six screenshot comparisons:
`unown-backdrop-comparison.json`. Native captures are
`unown-tests/single-01-p0-q0/form-00.png` and
`unown-tests/ascending-26-p0-q0/form-00.png` / `form-25.png`, under the latest
build directory. They are unmodified emulator captures, not generated artwork.

The first bank-write trial failed the new palette/pixel oracle and was rejected;
its partial suites were canceled. Only the dedicated-palette build above is
the current review candidate. No rejected trial was promoted to production.

Build using a fresh directory and the retained red-backdrop base:

```sh
PYTHONPATH=tools:. python3 tools/build_dex_unown_prototype.py \
  --base build/dex-unown-background-20261011 \
  --output build/dex-unown-black-20261011 --black-panels
```

Repeat the same preparation and Unown/Pokemon/Moves suites described above.
The original testing limits still apply: this is native emulator visual and
Dex regression coverage, not a new full battle, sampled-cry or interrupted-save
campaign. Manual review and production promotion remain separate.
