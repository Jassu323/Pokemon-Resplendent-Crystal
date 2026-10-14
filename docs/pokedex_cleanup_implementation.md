# Pokedex Cleanup Implementation

Implemented 2026-10-14 on commit `81ff02a25`, including the accepted visual-only
New Dex Entry Description layout and red footer. No commit/push was made.
Historical component audits are in
[Post-New-Entry Cleanup Scope](pokedex_post_new_entry_cleanup_scope.md).

## Space And Boundaries

All quantities are decimal linked bytes, not compressed archive/file sizes.

| Approved component | ROMX reclaimed from accepted New Entry layout |
| --- | ---: |
| Replaced/unreachable Dex code, graphics label and wrap no-op | 1,754 |
| Dex Slowpoke 48-tile prefix | 41 |
| Unused acquisition-list wrapper | 14 |
| Duplicate New Entry LCD/font setup calls | 9 |
| Test-only move discovery query API | 29 |
| Approved CGB-only compatibility subset | 525 |
| Two mobile Slowpoke blobs, three loads and three retired-entry guards | 598 |
| **Cleanup total** | **2,970** |
| Accepted New Entry layout cost relative to prior production | **277** |
| **Net reclaimed from prior production** | **2,693** |

Final allocation: ROM0 15,905; ROMX 2,343,205; WRAM0 4,083; WRAMX 24,010;
allocated SRAM 49,994; HRAM 127. ROM0, all allocated RAM, SRAM and HRAM are
unchanged. Existing RAM addresses remain unchanged. The 4,194,304-byte ROM
file stays the same size; these are additional free bytes in existing banks,
not a newly freed complete bank.

Removed: old OAM records/controllers, old mode descriptions/waits and options
shell, replaced listing/Selected/search renderers, obsolete static Area scan
and wrapped-grid refill, old registration shell, unused Info tile/page graphics,
unused Description restore/stop chain, orphan printer helper, old batch guard,
and the approved non-CGB Dex fallbacks. `performance_idle.asm` and its include
are removed. Retained roamer helpers are named `PokedexArea_RoamerNests` and
their current indexed-Area callers are updated without adding code bytes.

This is not a game-wide non-CGB/mobile purge. Current Legacy mode, both Search
owners, live font/palette/graphics helpers, animation/cry owners, semantic data,
precomputed Selected Info/Moves/ancestor assets, `GiveOddEgg`, ordinary Battle
Tower and its shared callbacks remain. Generic VBlank/STAT and battle logic
were not changed. ROM0 operands/checksum may relink despite zero allocation
change; zero bytes added does not mean byte-identical ROM0.

The three retired screen wrappers retain public labels and special IDs but
now return immediately. Their internal font/palette/helper modules are not
globally deleted. Removing whole `mobile/*` includes remains out of scope.

## Preserved Artwork

`gfx/archived/pokedex/` retains the original Slowpoke and SGB PNGs, raw tiles,
compressed outputs, the unused four Info-number tiles, and the shared original
number-sheet PNG for context. No original pixels were edited.

The active Slowpoke output is generated reproducibly from the archived raw
sheet's first 48 tiles. The Makefile retains the original conversion option
when regeneration is needed. Its 768 raw bytes include all five animation poses
and scrollbar tile 15; only seven obsolete large-cursor tiles are excluded.
Compression changes from 266 to 225 linked bytes, giving the 41-byte saving.
The remaining live shared page-number sheet stays in `gfx/pokedex`.
Narrow ignore exceptions keep the archival converted files commit-visible.

## Binaries And Promotion

| Binary | SHA-256 |
| --- | --- |
| Prior production | `e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e` |
| Accepted red-footer New Entry base | `a5dd313b939a99d92c2b18169be403f14d6a052877890a382005a420d53793fe` |
| Tested cleanup and rebuilt production | `dbef024fdaa1cdceb5a7458e323ac5d0f7e012ddfabb35585e3d806219f3ca7a` |
| Final symbols | `b4a2c6759114db7b36c4e5be19cda0d33182cb8fd8115d359de76c5929b571a1` |
| Final map | `a4ad65064cf74ce82680976841d57c1e68b454f813640225555d6a0dcd156072` |

The private candidate was qualified before promotion. The production ROM,
symbols and map rebuilt **byte-for-byte identically** afterward. Promotion
checked baseline game-source hashes and retained a source rollback before
copying only the changed game files and moving the exact archived artwork.
Unrelated tools/docs were not replaced by the candidate snapshot.

Build/evidence: `build/dex-cleanup-20261014/`. It contains the immutable
candidate, frozen pre-cleanup rollback, source archive, component/promotion
manifests, patch, build logs and all current campaign results. The historical
`production_unchanged` field in the full-regression report describes testing
before authorized promotion; the promotion manifest and final hashes describe
the subsequent checkout state. Player/installed-emulator batteries were not
edited or overwritten.

## Standard And Supplementary Qualification

The complete standard campaign passes with no new issues:
`runtime-regression/full-regression.json`, `merge_ready: true`.
All evidence is for the final cleanup SHA above, not relabeled old prototypes.

| Coverage | Current result |
| --- | --- |
| Pokemon Dex lists/options/Selected/Search/returns | 4,479 cases, zero failures |
| Moves Dex filtering/forms/keyboard/results/sort/navigation | All current phases pass |
| Move persistence and migration | Exhaustive bit/index/bank tests, normal saves, corruption/interruption, New Game and cancellation pass |
| Acquisition/learning and battle discovery | Positive/negative hook tests and surrounding gameplay pass |
| Shared gameplay | Existing 100-move battle suite, cries, custom menus, PC/daycare and returns pass |
| Host contracts | 87 current tests on each link; no failures/skips |
| Selected pages | Info and Moves 746 each, 400 stress, 1,056 feature, 115 return and 96 presentation cases pass |
| Shared arrow blinking | All current locations in both presentations, with populated Moves results, pass |
| Type/Unown | Six CGB revisions each; Type music/navigation stress over 122 entries; Unown decoder and negative controls pass |
| Registration | 20 contracts per link plus seven palette/bank checks; 120 smoke, 746 species, 8,270 offset/stress and 60 visual cases pass; party/PC and naming returns pass |
| Dex lifecycle | 336 comparisons, 36 routes and 88 exit scenarios; no early colored reveal/restoration issue |

All-move coverage: 333 moves, 361 catalog entries, **7,312 renderer calls /
3,656 paired comparisons**. Logical/visual sequences, restoration and durations
match production exactly: **0 ms / 0 display frames** for every measured pair.
The native battle side matrix has 666 pairs: 632 clean and 34 matching baseline
exceptions, including conditional/ending moves and the separately logged Sand
Tomb issue. Zero differing issue identities. Those exceptions are not newly
fixed or silently counted as clean native executions.

### Timing And Button Audio

One CGB display frame is 16.742706 ms.

| Median paired change vs prior production | ms | Display frames |
| --- | ---: | ---: |
| Dex entry | -1.197338 | -0.071514 |
| Dex exit | -0.000477 | -0.000028 |
| Move animation renderer duration | 0 | 0 |

The shorter Slowpoke decode also shortens the observed entry button-cue active
flag by 1.197338 ms (0.071514 frames) in all six style/order pairs. Exit flag
differences are 0 or +0.014305 ms (+0.000854 frames). The initial strict
four-T-cycle duration comparison is preserved as `lifecycle/audio-initial-exact.json`.
It is not reported as exact parity.

Follow-up read-only APU tracing verifies identical pitch/envelope/control
register-change sequences for all twelve entry/exit pairs. The qualified
audio report requires that parity, entry shortening matching the independently
measured entry gain, and exit within 64 physical T cycles. No sound-engine or
interrupt fix was applied. This is a bounded duration difference, not a claim
that captured PCM files are byte-identical.

### Harness Changes, Not Game Workarounds

The removed `MoveDiscovery_CheckIndex` tests now exercise retained MarkIndex,
BitAddress and the production Moves UI seen-query path. All index/bank/register
coverage remains. Slowpoke tests validate the retained prefix against the
independent archived original rather than expecting removed trailing tiles.
Arrow fixtures explicitly mark all moves seen and validate nonempty results;
Type fixtures explicitly unlock Unown instead of assuming donor save state.
The old `FindNest` observer resolves the retained roamer namespace.

Initial failed setup/assertion attempts remain recorded in phase logs. No
acceptance assertion was skipped to compensate for removed code. The separate
Tower suite has its own declared synthetic fixtures and explicit limitations.

## Independent Battle Tower Addendum

See [Battle Tower Regression Suite](battle_tower_regression_suite.md) for
commands, exact coverage, fixture/state contracts, PR 16 audit, negative
controls, artifacts and the required additional/manual matrix. See
[Tower Findings](battle_tower_testing_findings.md) for the existing prize bug
and fix choices. This addendum remains separate from the ordinary campaign.

The Tower is **not certified entirely clean**. The normal-button streak, loss
and ordinary menus are covered, but the independent suite detects existing
prize-routing/failed-receipt behavior on both ROMs. The direct battle matrix
completes 140 native battles per ROM with zero battle/restoration failures.
One production defensive-Tyranitar case completed at 90,063 total frames after
the single bounded continuation; its initial timeout remains preserved. This
uses extreme synthetic HP/stats, not an ordinary-player performance benchmark.
Final `report.json` records implemented coverage complete, protected inputs
unchanged, and no new candidate failures. Its only correctness failures are
the matched ten routing assertions and one normal-button prize-loss assertion.
`clean` therefore remains false. Resume/interruption and manual gaps are
listed explicitly in the runbook. No unrelated Tower fix is included here.

## Reuse

The historical build recipe is `tools/build_dex_cleanup_prototype.py`; it
requires the retained accepted New Entry source and a fresh output directory.
Do not apply that removal recipe to an already-cleaned source. Campaign phases
are in `tools/dex_timing/dex_cleanup_campaign.py`, with separate `standard`,
`registration`, `selected`, `animations`, `displays`, lifecycle and audio
actions. Registration preparation now accepts an explicit frozen
`--baseline-source`, preventing a later promoted root from replacing the old
control. Future changes require fresh matching-link campaigns, not reuse of
these JSON pass results.
