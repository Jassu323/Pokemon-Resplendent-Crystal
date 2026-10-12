# Type Matchups Precomputed Fallback

Decision: 2026-10-12. Runtime construction is the selected production approach.
Precomputed construction is retained as a fallback, not enabled in production.
The user preferred saving ROM space over approximately one frame of faster
selection updates. No save-format or additional RAM allocation differs between
these approaches.

## What Is Preserved

The local, ignored retention directory is
`research_artifacts/type-matchups-retained-20261012/`. It is intentionally outside
the disposable `build/` tree. Copy/archive this directory when moving machines;
Git preserves the recipe and documentation, not these local ROM/source archives.

- `precomputed-approved.tar.gz`: full rebuildable source snapshot, the tested
  precomputed ROM/symbol/map/review battery, original production source archive,
  and selected final acceptance reports.
- `runtime-approved.tar.gz`: matching accepted runtime snapshot and artifacts.
- `production-before-integration.tar.gz`: production source and ROM/symbol/map
  before this integration. The player's battery is not included or changed.
- Matching JSON manifests contain every archived member's size/hash and the
  archive hash. Archives are read back and verified before cleanup.
- `integration-plan.json` records the narrowly selected production source delta.
- `fallback-patch.sha256` identifies the retained runtime-to-precomputed patch.

The portable source overlay is tracked at
`tools/dex_timing/probes/type_mode7_precomputed_fallback.patch`. This differs from
the earlier `type_mode7_precomputed.patch`, which starts from the old shared-IRQ
Type prototype. Use the fallback overlay for the accepted runtime implementation.

Frozen tested ROM SHA-256 values:

```text
Runtime:
469f7db4ed492e3d44fc29cd6bd0dbc51d1f5e5671732861c98a81623a747cac
Precomputed:
a5c469fc9cd06a89c10ee14fa3c9fb08dac4326a92cce91abb8abd6755f684c4
Production before integration:
591d2075b0c986846b94bc92288d1fa4f9d2918fccc680a83928fd8fdcf59bee
```

## Shared Behavior And Display Ownership

Both versions use the same exclusive, cooperative Type display owner: existing
VBlank mode 7 tagged with bit 4 (`$17`), no Type checks in ordinary LCD or normal
VBlank, the same palette deadlines, the same Type-only cooperative audio path,
the same double-buffered lower panel, and the same cursor/input/return behavior.
Both automatically update W/R/I when the cursor moves. Steel keeps its compact
combined resistance/immunity list; other relevant types have a separate I row.

Neither version changes battle animation scripts, saves, discovery tracking, or
the normal audio engine. The requested canonical battle-chart changes are shared
by both and still affect battles intentionally.

Precomputation does not replace the shared owner. It is a different producer of
the same lower-panel data. This is why it saves one frame during navigation but
does not remove the screen's raster/audio maintenance contracts.

## Runtime Construction

On entry, runtime caches the canonical chart in existing exclusive Dex scratch.
For each cursor change it scans those chart records for the selected defending
type, builds alphabetized weakness/resistance/immunity lists, chooses the
resistance row, draws the five lower tile/attribute rows, and assembles the
matching per-row palette accents. Cooperative yields occur throughout that work.

The results are staged off-screen and published atomically by the shared owner.
The published cursor, map, attributes and palette page must agree. No new SRAM,
WRAM or HRAM is allocated; ownership and restoration still matter.

The runtime approach keeps less derived data in ROM and adapts directly to the
linked chart. Its additional maintenance is ensuring computation/drawing loops
remain bounded and yield often enough while the raster is active.

## Precomputed Construction

`tools/pokedex_type_panels.py` executes during the ROM build. It reads the same
canonical chart, type/effectiveness constants, alphabetical order, tile-slot
layout, character map and existing palette files. It creates eighteen records
and a pointer index; there is no second manually maintained chart.

Each record is 262 bytes:

| Portion | Bytes | Purpose |
| --- | ---: | --- |
| Metadata | 22 | Counts, resistance row, ordered W/R/I lists and padding |
| Tile map | 100 | Five 20-tile lower rows |
| Attribute map | 100 | Matching banks/palette assignments |
| Palette accents | 40 | Four two-byte accents for each of five rows |

Records total 4,716 bytes plus a 36-byte pointer index: 4,752 bytes of data.
The additional loader code brings the linked difference to **4,889 ROMX bytes**.
No additional RAM or save storage is needed.

On cursor movement, the precomputed loader selects the matching record and copies
its metadata, maps and accents with frequent yields, then uses the identical
staging/publication mechanism. It avoids the on-page chart scan, list building,
badge placement calculations, and lower accent construction.

The Makefile regenerates records after current chart/constants/order/layout/
palette inputs change. New input formats or sources require updating the
generator and its dependency rule. Its syntax/layout assumptions are explicit,
including eighteen types and fixed-size records. Generated records are not to
be edited by hand. Some unused runtime drawing routines remain linked in the
retained prototype; removing them later would require a fresh qualification.

## Measured Differences

The final comparison used eight entry phases and 576 navigation cases per
implementation. Median complete Type entry is the same, 175.32 ms.

| Navigation Measurement | Runtime | Precomputed |
| --- | ---: | ---: |
| Direction accepted | 10.50 ms | 10.50 ms |
| Lower panel published | 58.72 ms | 41.98 ms |
| First complete changed display | 75.39 ms | 58.66 ms |

Precomputation gains approximately **16.74 ms**, one display frame. Current linked
ROMX growth over the retained pre-mode-7 Type prototype is 713 bytes for runtime
and 5,602 bytes for precomputed. Both use 15,905 ROM0 bytes with 479 free. The
audio/song bank `$3a` has only 26 free bytes in both; precomputation does not
solve that bank-local constraint.

## Problems This Fallback Can Address

These are potential future reasons to switch, not unresolved current failures:

- Runtime panel updates become too slow after chart or presentation changes.
  Finished records avoid repeating the added computation during navigation.
- A runtime list/drawing loop becomes too expensive between raster yields.
  Replacing that producer with short copy loops can remove that specific deadline
  violation. The shared owner and copies still require correct yields.
- Runtime chart-cache interpretation, temporary-bank usage, or calculation code
  gains a defect. A validated build-time generator can avoid that runtime path.
  It cannot correct an erroneous canonical chart or an equally erroneous oracle.
- New layout rules make assembly list/placement code difficult to maintain.
  The same work may be simpler to calculate and inspect in generated records,
  subject to keeping generator, format, loader and dependencies synchronized.

Ordinarily adding moves or species does not increase these eighteen Type records
or the runtime chart work. Changes to types, matchups or display layout are more
relevant. Additional music/SFX can exercise shared audio independently.

## Problems This Fallback Does Not Address

- Shared palette-owner timing, wrong scanline positions, palette writes in
  forbidden windows, atomic publication errors or cursor/input ownership bugs.
- Slow/new shared audio decoder helpers or new command semantics that prevent
  the Type-only cooperative parser from meeting its deadlines. Both use it.
- Incorrect bank/register/interrupt restoration or scratch-buffer ownership.
- Common interrupt, CPU speed, clock, bank-switching or audio defects elsewhere.
- The intentional type-chart-induced battle start-phase differences, occasional
  Modern/Legacy Selected-entry delays, or production's separate Sand Tomb hang.
- Bank-local capacity issues such as the nearly full audio bank.

If those occur, investigate and repair the shared cause rather than assuming
precomputation is a universal fix. It adds build-time failure risks: stale records
if dependencies are incomplete, generator/loader format disagreement, and
assumptions that need revision for future types or layout changes.

## Recover Or Trial The Fallback

Inspect and extract archives into a fresh scratch directory, never over a newer
checkout or the player's battery:

```sh
tar -tzf research_artifacts/type-matchups-retained-20261012/precomputed-approved.tar.gz
mkdir -p /private/tmp/type-precomputed-recovery
tar -xzf research_artifacts/type-matchups-retained-20261012/precomputed-approved.tar.gz -C /private/tmp/type-precomputed-recovery
make -C /private/tmp/type-precomputed-recovery/candidate -j6 pokecrystal.gbc
make -C /private/tmp/type-precomputed-recovery/candidate -j6 gfx/pokemon/unown_{a..z}/front.dexanim
```

The second build command prepares Unown visual-test sidecars that are not all
dependencies of the normal ROM target. The archived source was extracted into
scratch and rebuilt successfully to the frozen precomputed ROM hash before
cleanup; its rebuildability is checked, not just assumed.

That preserves the historical implementation. On a future branch, use a private
source copy/worktree and review the runtime-to-precomputed overlay instead of
replacing the branch with this old source snapshot. First run `git apply --check`
against the fallback patch. If it no longer applies, port its three logical
changes: enable `TYPE_PANEL_PRECOMPUTED`, add the panel-generation dependencies,
and generate records from the future branch's current canonical data.

The production integration also makes `all` the explicit default Make target and
removes a stale comment, neither affecting ROM bytes. An old overlay may need
minor context adjustment around that Makefile change. Never restore an old
chart, shared owner, artwork, audio engine or save layout just to apply it.

After a fresh link, regenerate fixtures and run the full suite, all eighteen
Type selections, six CGB revisions, all music/SFX and held-input stress, atomic
publication and return/restoration tests. Compare frame timing/pixels for all
battle animations and surrounding gameplay. Preserve new hashes and assess
storage costs; the historical green result is not acceptance for a future ROM.

See [Type Mode 7 Comparison](pokedex_type_mode7_comparison.md),
[Runtime Production Integration](pokedex_type_runtime_integration.md),
[Full Regression Suite](full_regression_suite.md), and the
[Interrupt Timing Contract](battle_animation_interrupt_timing_contract.md).
