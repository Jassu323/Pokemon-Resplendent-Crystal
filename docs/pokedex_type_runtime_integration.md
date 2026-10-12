# Type Matchups Runtime Production Integration

Date: 2026-10-12. Runtime is selected for production; precomputed is a retained
fallback. Source integration, production rebuild, fresh post-integration
qualification and generated-build cleanup are complete.

## Production Changes

The integrated ROM is byte-identical to the approved isolated runtime prototype:

```text
469f7db4ed492e3d44fc29cd6bd0dbc51d1f5e5671732861c98a81623a747cac
```

The reviewed source delta includes Type mode/state transitions, the canonical
chart changes, the shared Dex selection-arrow blink routine, the private mode-7
Type owner and its cooperative audio copy. No precomputed records are enabled.
There are no additional save-format or RAM allocations. Ordinary battle LCD,
normal VBlank and audio paths do not gain Type work. Regular Dex mode 7 pays
the previously measured selector check.

The Makefile explicitly defaults to `all`, so the new generated-audio dependency
does not accidentally become the default target. A stale old raster-handler
comment was removed. These build/comment corrections do not change ROM bytes.
Unrelated workbook changes and other user files were not reverted or included
in the gameplay source delta. No commit is created by this integration.

Before integration, production source and ROM/symbol/map were preserved in a
verified local archive. The player's battery was not modified. The selected
runtime and rejected precomputed source/ROM/save/report snapshots are also
retained outside `build/`; see [Precomputed Fallback](pokedex_type_precomputed_fallback.md).
The fallback archive was extracted in scratch and rebuilt to its original
precomputed ROM hash. Its tracked runtime-to-precomputed overlay also passes
`git apply --check` against the integrated source.

## Fresh Qualification

The campaign is `build/dex-types-production-runtime-20261012/`.
`runtime/` holds an immutable integrated-source snapshot and matching ROM,
symbols, map and copied review battery. `runtime-regression/` compares it with
frozen pre-integration production, not a self-comparison with the updated root
ROM. Root ROM/symbol/map hashes remain protected throughout the campaign.

The complete established campaign is rerun: Dex, Moves/search/keyboard, sort
memory, persistence/migration/corruption/interrupted writes, acquisition,
battle discovery, Struggle award, Unown, PC/daycare, custom menus, sampled
cries, surrounding gameplay, speed transitions, Selected playback and entry
timing. Six-model Type visual/navigation/return/restoration qualification and
both all-music/SFX idle and held-input stress are freshly run too.

The animation campaign compares old production and integrated runtime across
3,656 renderer calls each, all 333 moves and 28 auxiliary entries. It separately
runs 666 ordinary battle-input cases per ROM. The 100-move, both-side, four-phase
matrix remains part of the full gameplay campaign. Chart-only ablations are
rerun for the fresh differing cases, using the same display code with only the
production chart restored and its zero-byte end label added.

An initial Dex phase lacked converted Unown visual-test sidecars in the private
source snapshot. Those sidecars are not all normal ROM-build dependencies.
Current converted `gfx/` was copied into the private snapshot, and the complete
Dex phase was successfully rerun: 4,479 cases, zero failures. No game ROM changed
to correct this fixture issue. Initial failure logs and the successful retry
remain identified in the evidence; it is not waived as a game pass.

The private snapshots also initially omitted generated Dex asset tables used by
host tests. Copying the five current `build/dex-*-assets` directories into both
snapshots resolved those fixture errors. Both host phases were rerun. Current
host coverage is 86 cases with the same production Info LY64 assertion failure;
historical host coverage has the same failure/error/skip identities as production.
Original failed attempts and actual successful retries are preserved. The campaign
status writer now merges individual phase retries under a lock, avoiding stale
status overwrites by concurrent wrappers. None of these fixture corrections
changes game ROM bytes.

Final confirmed results: all six Type models pass; both 122-entry
music/SFX stresses pass; all 3,656 renderer comparisons are timing/pixel/logical
matches with zero restoration failures; the normal-input sweep has the same
34 baseline exception identities per ROM. The final full report has
`merge_ready: true`, an empty new-issue list, and the production hash above.
Every final phase status is zero; the original failed wrapper attempts are not
misrepresented as successful runs.

Known baseline exceptions remain explicit, including the separate Sand Tomb
issue, historical host assertions and sampled-cry timing misses. Fresh owner-reveal
measurements cover 256 pairs per style: Modern median delta -0.0067 ms, maximum
+16.7780 ms; Legacy median -0.0017 ms, maximum +16.7446 ms. Occasional roughly
one-frame entry delays occur in both styles, not only the earlier Legacy case.
The exact responsible instruction is not isolated. Median responsiveness is
effectively unchanged, but this is not a claim of zero non-Type timing changes.
The raw first-change-in-lower-crop metric also has Modern outliers up to
+100.4562 ms (Spheal, 30-frame hover); complete stable display in that group
differs by at most +0.0453 ms. That first pixel change is a different observation
from window-owner reveal or complete page presentation and is sensitive to what
changed in the crop. Its outliers are retained, not described as a one-frame
bound on every possible timing metric or attributed to an unproven cause.

Native animation duration changes are start-phase-dependent;
fresh fixture phases need not reproduce the exact affected-move list from the
earlier comparison. They require fresh chart-ablation evidence, not automatic
acceptance by analogy. Ten all-move cases (including two controls) and seventeen
100-move matrix cases (including two controls) were checked against an otherwise
identical diagnostic ROM with the old chart restored: all duration deltas then
became exactly zero. The isolated animation renderer itself has zero duration
or pixel differences. Physical hardware is not tested by this campaign.

## Build Cleanup Policy

`tools/cleanup_dex_builds.py` requires successful integrated full acceptance and
a matching production ROM hash before deletion. It only selects named Dex build
families and excludes normal generated asset directories and unrelated research/
battle-history folders. Every compact archive is content-hash verified before
the first loose family is removed; metadata checks reject concurrent changes.

Preserved historical data includes source, recipes, reports/JSON, ROMs, batteries
and screenshots. Disposable raw instruction/frame traces, captured PCM, temporary
emulator states, compiled observers and intermediate assets are retired.
Required fixture definitions and Unown negative controls remain directly usable
at their original paths, including their converted graphics and executable cores.
Current aggregate reports, review ROM/save and screenshots remain accessible.

Compact archives/manifests and the cleanup receipt are stored in
`research_artifacts/dex-build-history-20261012/`. The precomputed fallback and
production rollback are separately stored in
`research_artifacts/type-matchups-retained-20261012/`.
Both are intentionally outside disposable build directories and ignored by Git.
The source overlay, documentation, generators and test tools remain in the repo.

```sh
python3 tools/cleanup_dex_builds.py --verify
```

The cleanup receipt records actual before/after storage and archive size. It
does not claim raw traces or temporary states can be restored. Retained archives
must be moved separately when migrating machines. Rebuild fresh test fixtures
for future links rather than reusing old CPU checkpoints.

Actual cleanup: 101 generated build families compacted. `build/` decreased from
168,614,535,168 bytes (168.615 GB) to 8,045,068,288 bytes (8.045 GB). Compressed
family archives total 4,161,947,097 bytes (4.162 GB), giving approximately
156.408 GB net reclaimed by the receipt's accounting. Archive manifests add a
small overhead. Unrelated retained battle history and normal build assets were
left alone. The 43,749 required live fixture files remain at their original
paths; verification checks their hashes against the archive manifests, not just
their existence. The separately retained Type fallback/rollback directory is
about 87 MiB. The verified fallback-rebuild scratch directory was removed too.

The six isolated retention safety tests pass, including rejection of a corrupted
restored fixture. Production's final ROM hash still matches the accepted runtime.
Post-cleanup verification read all 101 archives, checked all 43,749 live fixture
hashes and confirmed the unchanged production hash. The normal default build
still resolves to `all` and is up to date after cleanup.

See [Full Regression Suite](full_regression_suite.md) for exact coverage and
commands, and [Type Mode 7 Comparison](pokedex_type_mode7_comparison.md) for the
original implementation/performance analysis.
