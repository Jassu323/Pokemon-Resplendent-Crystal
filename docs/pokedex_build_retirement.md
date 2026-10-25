# Dex Build Retirement And Recovery

Date: 2026-10-17. The egg-placeholder prototype has completed its purpose and
is disposed of with the user's approval, without promotion. Its measured
results remain in [Egg Page Qualification](pokedex_egg_placeholder_prototype.md).
`DEX-DATA-03` still needs final legitimate species content; `BREED-MOVE-01`
remains separately logged and unfixed.

## Authoritative Component Guides

Production implementation lives in the normal source tree, not a historical
candidate copy. These guides explain ownership, rendering, data and validation:

| Component | Maintained Documentation |
| --- | --- |
| Modern/Legacy listings, modes and grid publication | [Listing modes](pokedex_listing_modes.md), [VRAM ownership](pokedex_vram.md) |
| Options, ordering, Search and results | [Listing options](pokedex_listing_options_prototype.md), [ranked Search](pokedex_search_ranked_prototype.md), [results renderer](pokedex_search_results_prototype.md) |
| Portrait animation, cry playback and bounded publication | [Selected scheduler](pokedex_animation_scheduler.md), [sampled cries](sampled_cries.md), [interrupt timing contract](battle_animation_interrupt_timing_contract.md) |
| Description layout, metadata, direct page offsets and footprints | [Description UI](pokedex_description_ui.md), [multipage renderer](pokedex_description_multipage_scope.md), [species information](pokedex_species_information_prototype.md), [footprints](pokedex_footprint_prototype.md) |
| Info: Stats, evolutions, ancestors and retained returns | [Info pages](pokedex_info.md), [ancestors integration](pokedex_ancestors_production_integration.md), [atomic portrait dependency](pokedex_info_description_latency_investigation.md) |
| Selected Mov: level, TM/HM, tutor, breeding and shared badges | [Selected Moves](pokedex_moves.md), [long-list qualification](pokedex_egg_placeholder_prototype.md) |
| Area owner and exact tab/page restoration | [Area integration](pokedex_area.md) |
| Moves encyclopedia, scrollbar, sort, substring/type Search and text entry | [Moves integration](pokedex_moves_search_prototype.md), [scrollbar](pokedex_moves_scrollbar_prototype.md) |
| Permanent-index seen flags, SRAM CRC/recovery/migration and gameplay hooks | [Discovery design](pokedex_move_discovery_scope.md), [persistence](pokedex_move_persistence_prototype.md), [acquisition](pokedex_move_acquisition_prototype.md), [battle use](pokedex_move_battle_use_prototype.md) |
| Session-only position and saved sort preference | [Position integration](pokedex_session_position_prototype.md), [sort memory](pokedex_moves_sort_memory_prototype.md) |
| Unown artwork, atomic form updates and transitions | [Correctness](pokedex_unown_fix_prototype.md), [form performance](pokedex_unown_performance_prototype.md), [transition optimization](pokedex_unown_transition_optimization.md) |
| Type Matchups palettes, isolated mode 7 and runtime panel construction | [Runtime integration](pokedex_type_runtime_integration.md), [mode 7 comparison](pokedex_type_mode7_comparison.md) |
| Dex opening/closing and whole-game CPU clock boundaries | [Stage return](pokedex_stage_return_repair.md), [clock policy](production_clock_policy.md) |
| Interactive post-catch registration, LCD-on switch and Pay Day preservation | [Registration integration](pokedex_interactive_registration_integration.md), [capture fixes](pokedex_registration_capture_fixes_review.md) |
| Accepted Info/Mov scheduling changes and measured tradeoffs | [Responsiveness](pokedex_responsiveness_prototype.md) |
| Remaining work and adjacent defects | [Live backlog](pokedex_selected_bug_backlog.md), [reconciliation](pokedex_backlog_reconciliation.md), [breeding issue](breeding_bug_backlog.md) |

Older wording such as "retained ROM", "review video" or an ignored `build/`
link is historical provenance, not a promise that the payload still exists.
This retirement notice supersedes those storage promises, not their measured
results, qualifications or explicitly recorded coverage limits.

## Retention Boundary

The cleanup removes the completed egg prototype and historical Crystal test
builds, copied sources, reports, audio/video/screenshots, ROMs, saves, compiled
observers and temporary states. It also retires the redundant ignored Dex
build-history archives after the essential fixtures have been independently
preserved. It does not change the production ROM/map/symbols, main battery,
game source, artwork or unrelated HeartGold/species/workbook work.

The tiny Makefile-generated `build/dex-*-assets` directories remain: they are
current build inputs, not historical tests. Regenerate them with the normal
Makefile rules when needed. Do not remove authored cry/music files in `audio/`
or graphics in `gfx/` when discarding captured recordings.

The two explicitly requested fallback implementations remain outside `build/`:
[precomputed Type panels](pokedex_type_precomputed_fallback.md) and
[Selected runtime/VRAM recovery](archived/selected-vram-ancestors-20261013/README.md).
They are small, deliberate restoration archives, not another loose run history.

## Minimal Regression Inputs

The portable bundle is [tools/regression_fixtures](../tools/regression_fixtures/README.md).
Its compressed input payload is 1,906,308 decimal bytes (1.82 MiB), containing
644 declared files / 32,737,000 uncompressed bytes. Nothing from the discarded
egg prototype is required. Specifically retained are:

- Legacy/all-moves and natural/battle-discovered seed batteries and fixture definitions.
- Three known-bad Unown cartridges, symbols, private batteries and only the
  animation sidecars actually read by their frozen content oracle.
- One known-bad Moves Search cartridge/symbol pair and its all-seen seed.
- The frozen pre-relocation ROM/symbol pair for the Info numeric-copy timing
  comparison. It is not a current production baseline or a full source snapshot.
- Independent source-pinned description page/measurement/hash expectations
  and the 122 original footprint masks/provenance records.

No source snapshots, recorded audio, prior pass reports, emulator checkpoints
or compiled host executables are retained in this bundle. Every member has a
purpose and hash in its manifest. Known-bad cartridges are necessary negative
controls, not historical review builds kept just in case.

The first post-cleanup host run exposed one extra dependency: the experimental
battle-motion table-bound unit test read `battle-motion-reference-20261004/reference.json`.
That old capture is retired, not silently replaced with fabricated measurements.
The unit test now injects explicitly synthetic poses from `tools/test_battle_motion.py`,
checks exact generated size for those inputs and rejects one/256-frame chip
ages. Its purpose is table construction/bounds, not historical motion timing.
The private builder still requires real measurements when no test reference is
injected. Current all-move native timing/audio/pixel campaign requirements are
unchanged; this unit fixture does not stand in for those measurements.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures verify
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures restore --compile-controls
PYTHONPATH=tools:. python3 -m unittest tools.test_regression_fixtures
```

Restoration expands only the declared test inputs below `build/`, remaps local
paths, refuses changed existing files and rebuilds native observers from the
current harness. Generated observers/captures remain disposable. The compact
archive, manifest and reusable Python/C harnesses stay in `tools/`.

For the next campaign, freeze fresh current-production and candidate source,
ROM/symbol/map sets, use copied fixture batteries and generate new native
checkpoints. Follow [Full Regression Suite](full_regression_suite.md), its
registration/multipage addenda and the independently runnable
[Battle Tower suite](battle_tower_regression_suite.md). Never restore an old
whole-game ROM as the baseline for a new change. Historical model/experimental
builders may need their documented baseline recreated; those are not part of
the current acceptance campaign.

## Cleanup Verification

- `build/` shrinks from approximately 146 GiB to 1.07 GiB, with the redundant
  ignored Dex archive also removed; approximately 151 GiB of volume space is
  recovered. The remaining bulk is unrelated HeartGold/Sacred Gold and
  species/workbook work, plus the current generated build assets.
- The bundle passes archive/member hashes, private-path round-trip restoration
  and fresh native observer compilation. All five native negative controls
  detect their intended original defects using only the minimal restored inputs.
- Current campaign fixture binding succeeds without the retired archives.
- All 87 current host checks and 31 extra controls pass, with zero failures,
  errors or skips. Extra controls cover long egg lists, description offsets,
  footprint polarity, restore safety/concurrency and the earlier retention tool.
- Production ROM/symbol/map, main save, generated build inputs and the two
  deliberate fallback archives retain their hashes. The normal production
  build remains up to date; it is not rebuilt or promoted.
- The first missing-dependency host attempt is recorded separately from the
  successful replay. No full native gameplay campaign is claimed for this
  storage-only change; current game code/data/cartridge bytes are unchanged.

Only small cleanup/verification receipts remain under
`build/cleanup-dex-final-20261017/`. Expanded fixture copies, compiled observers,
temporary verification media and source wrappers are removed again after the
checks; a future campaign restores its inputs from `tools/` as needed.
