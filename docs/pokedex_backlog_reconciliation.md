# Pokedex Backlog Reconciliation

Follow-up 2026-10-14: the prioritized
[Info-to-Description investigation](pokedex_info_description_latency_investigation.md)
isolates publication starvation, superseding the initial preparation/admission
hypothesis below. A broader active-paging baseline reaches 4,647.95 ms; three
private fixes reduce the median to 60.45 ms with zero RAM growth. The user chose
the +9 fix, now implemented in production. Fresh active-return, six-model and
full emulator regressions pass with no new failures. Root ROM SHA-256 is
`12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d`;
manual review remains pending. The original reconciliation evidence below
belongs to the frozen pre-fix cleanup baseline, not this new link.

Reconciled 2026-10-14 against the installed cleanup production build. The
accepted implementation is complete, with deferred content/preferences retained.
The one reproduced Selected-tab responsiveness issue is now fixed as noted above.
Five older reports are
historical and not reproduced in current focused tests; they are not claims
that every possible input phase or hardware condition has been ruled out.

The live [backlog](pokedex_selected_bug_backlog.md) retains original causes,
measurements and failed prototypes. Its latest status and reconciliation notes
take precedence over older paragraphs describing an unpromoted prototype.

## Reconciliation Baseline And Evidence

- Production ROM SHA-256:
  `dbef024fdaa1cdceb5a7458e323ac5d0f7e012ddfabb35585e3d806219f3ca7a`.
- Symbols SHA-256:
  `b4a2c6759114db7b36c4e5be19cda0d33182cb8fd8115d359de76c5929b571a1`.
- Map SHA-256:
  `a4ad65064cf74ce82680976841d57c1e68b454f813640225555d6a0dcd156072`.
- Base commit: `81ff02a25`; accepted New Entry/cleanup changes are in the
  current working tree. Reconciliation does not commit or change game code.
- Prior full qualification: `build/dex-cleanup-20261014/`, documented in
  [Cleanup Implementation](pokedex_cleanup_implementation.md).
- Fresh targeted replays: `build/dex-backlog-reconciliation-20261014/`.
  Matching current-link private saves/checkpoints were reused only after
  ROM/symbol provenance checks. Production ROM, symbols, map and the player's
  battery hash remain unchanged.

## Complete And Integrated

| Stories or system | Current disposition and evidence |
| --- | --- |
| `DEX-ANIM-01/02` | Accepted Selected animation scheduling and Seviper correction. Current all-species playback checks pass. |
| `DEX-CRY-01/02/04/05` | Accepted Selected sampled-cry playback, outgoing cancellation, synthesized-cry resumption and header ownership corrections. Other owners are separate. |
| `DEX-INFO-01/05/06` | Accepted retained-panel return, timer-shutdown race correction and bounded/coalesced Info paging. Current Info/content/stress/return checks pass. |
| `DEX-INFO-07` | Ancestors are integrated and manually accepted. Production retains precomputed rendering; the runtime/VRAM alternative is archived. See [ancestors integration](pokedex_ancestors_production_integration.md). |
| `DEX-INFO-03` | +9 ROMX publication fix implemented; fresh 1,492-case, six-model and full emulator regressions pass. No added RAM. Dependency and timing ceiling documented in the linked investigation; manual review pending. |
| `DEX-PAGE-01`, `DEX-DESC-01` | Shared buffered indicators and bounded Description page changes are complete. |
| `DEX-TRANS-01/02/03`, `DEX-NAV-01/02` | Accepted internal handoff, identity/graphics publication, boundary wrapping and fresh-axis input corrections. |
| `DEX-RETURN-01/03`, `DEX-GRID-01/03` | Accepted LCD-on Listing restoration, palette publication and stable presence metadata. |
| `DEX-GRID-05` | Changed-sort cache invalidation is integrated, not awaiting promotion. It was included in the accepted October 11 Moves/Search integration. |
| `DEX-UNOWN-01/02/03/04` | Accepted blank tiles, bounded form counts, red backdrop and black panels. |
| Unown form paging | Static decoding and atomic picture/map publication are integrated. Current CGB E median complete selection remains 49.02 ms. This is distinct from Modes transitions. See [Unown performance](pokedex_unown_performance_prototype.md). |
| `DEX-UI-01/02`, `DEX-AREA-01` | Footprint/category corrections and Area owner/return integration are complete. |
| `DEX-SEARCH-01/02/03/05` | Slowpoke palette/OAM, colored Results, small cursor/caught ball, compact icons, alphabetical controls and ranked type matching are integrated and manually accepted. |
| Moves Dex | Visual layout, scrollbar, discovery persistence/migration, acquisition/learning/battle hooks, initial Struggle discovery, sort remembrance, substring/type Search, themed text entry and standard cursor behavior are complete. Position remembrance is not included. See [production integration](pokedex_moves_search_prototype.md#production-integration). |
| Type Matchups and shared arrow blink | Accepted runtime mode-7 implementation, chart changes, immediate cursor-driven lower panel, layout and shared blinking are integrated. The precomputed alternative is archived. See [integration](pokedex_type_runtime_integration.md). |
| `DEX-PERF-01`, `DEX-EXIT-01` | Repaired Stage opening/closing is accepted and integrated. Current qualification includes 336 lifecycle cases and 88 exit replays, without early colored reveal or shell displacement. |
| `DEX-PERF-03` | Idle animation cache warming is removed from regular Dex modes. |
| `NEWDEX-UI-02` option A | Accepted visual-only Description layout and red footer are in production. Original post-catch A/B flow remains. Option B is not an unfinished part of A. |
| `DEX-CLEAN-01` | Approved cleanup is integrated and accepted: 2,970 decimal ROMX bytes reclaimed from the accepted New Entry build; 2,693 net against prior production. Original graphics remain archived. |
| `NEWDEX-ANIM-01`, `NEWDEX-UI-01`, `QA-CLEANUP-01` | Registration scheduling/text work and temporary encounter/instrumentation cleanup are complete, retaining the accepted Mewtwo presentation caveat. |

The old Search, changed-sort, ancestors, cleanup and exit status lines were
outdated. They do not indicate missing production changes. The retained
precomputed font/heading assets and archived alternative architectures are
intentional choices, not unfinished cleanup.

## Historical Reports Not Reproduced

| ID | Fresh result | Disposition |
| --- | --- | --- |
| `DEX-INFO-04` | 102 caught-species Info-to-Description cancellation cases pass, including Rhyperior at age 0, ages 0-12/16/24/32/settled and five controls. Complete current badge pixels are checked. | Historical, not reproduced. The old fixed `P.` badge implementation has been replaced by shared buffered badges; no new cancellation patch is proposed. |
| `DEX-RETURN-02` | No vertical displacement in 60 direct, internal-page, active-cancel and page-2 returns. Hardware and mirrored scroll are checked on completed display frames. | Historical, not reproduced on this build. |
| `DEX-RETURN-04` | Those returns reveal the correct selection, rendered header and portrait, compared with an independently reached Listing. | Historical, not reproduced on this build. |
| `DEX-GRID-02` | Hardware/target caught-ball palette, actual OAM geometry/attributes and uploaded tile bytes pass across those return frames. | Historical, not reproduced on this build. |
| `DEX-GRID-04` | All 60 returns and their scrolling/wrapping/reentry follow-ups pass the strict rejected-palette-write checks. Dusknoir active-16 is repeated three times with zero rejected writes. | Historical, not reproduced on this build. No speculative palette/interrupt fix or identified single corrective commit is claimed. |

The return replay examines 726 completed outgoing/Listing display frames,
plus each case's navigation traces. This is focused evidence, not a fresh
all-species/all-phase hardware sweep. The eight existing observer negative
controls pass, including wrong hardware colors, wrong marker attributes,
changed header pixels and intermediate cursor detection. The previous broader
return/marker investigations remain linked in the individual stories.

Reopen a historical report with a current-build state/video and its species,
mode/order, tab/page, input timing and playback state if it recurs. Do not
silently delete its earlier reproduction or label it a proven causal fix.

## Still Outstanding

| Story | Current scope |
| --- | --- |
| `DEX-SEARCH-04` | Official National labels remain deferred. Current display can show internal species numbers for added species. |
| `DEX-DATA-01` | Finish placeholder descriptions and height/weight data. |
| `DEX-DATA-02`, alias `DEX-INFO-02` | Complete real gameplay evolution/species records and added branches during the planned species/learnset/stat pass. Ancestor rendering does not supply absent gameplay links. These are one underlying work item, not two fixes. |
| `DEX-DATA-03` | Revalidate family egg-move inheritance after the actual evolution/egg records are updated. Current generated content correctly reflects configured data. |
| `DEX-DATA-04` | Regroup later-generation relatives/babies in the authored Evolves order shared by Modern and Legacy. National/Alphabet remain independent. |
| `DEX-PREF-01` | Durable Pokémon listing position/viewport remembrance. |
| `DEX-PREF-02` | Durable Moves listing position/viewport remembrance, separate from already completed sort remembrance. |
| `DEX-PERF-04` | Optional further Modes-to-Unown and Unown-to-Modes latency reduction. Current cleanup's eight post-Info transition cases complete in about 249.33-249.79 ms entering and 249.59-249.60 ms returning, around 14.9 display frames. Correctness passes; the old 350 ms entry baseline is no longer current. |
| `DEX-PERF-02` | Accepted Selected-tab iteration and the `DEX-INFO-03` publication correction are complete. Keep only broader future performance review as an umbrella; opening/closing, idle warming and Unown form paging are already integrated. |

Future options, not pending approved implementation: New Entry `Desc/Info/Mov/End`
navigation (option B) and the requested future Selected-screen implementation
audit. The user chose the completed visual-only flow for now.

### DEX INFO 03 Historical Pre-Fix Reproduction And Timings

128 normal-input cases cover Modern/Legacy, four physical input phases,
four incoming Pokémon and ages 0/8/32/settled after internal paging. Content,
badge, owner and playback checks pass; that does **not** mean responsiveness
is fixed. Inputs are accepted within 17.054 ms (about 1.02 display frames).
Rendering can be much later.

| Incoming Pokémon | Active-playback completion range | Settled completion range |
| --- | ---: | ---: |
| Dusknoir | 53.15-488.47 ms / 3.17-29.18 display frames | 53.28-65.87 ms / 3.18-3.93 frames |
| Weavile | 57.33-739.62 ms / 3.42-44.18 frames | 53.29-65.85 ms / 3.18-3.93 frames |
| Sceptile | 57.37-2,028.83 ms / 3.43-121.18 frames | 53.32-65.88 ms / 3.18-3.93 frames |
| Meganium | 67.60-1,771.53 ms / 4.04-105.81 frames | 53.31-65.88 ms / 3.18-3.93 frames |

Of 96 active requests, 72 reach complete Description while playback is still
active; 24 finish only after playback. Thus the original report is phase- and
species-dependent, not a universal rule that every tab change waits for the cry.

Concrete replay: open caught Grovyle, settle its playback, select Info, then
page Down to Sceptile. After eight display frames from the incoming owner loop,
select Desc with Left/A. In the Modern q0 replay A is accepted in 3.74 ms,
but complete Description appears in 2,028.83 ms / 121.18 display frames,
after playback ends. The corresponding settled request takes about 65.86 ms.

Relevant owner: `PokedexSelectedMon_ServiceDescriptionText` in
`engine/pokedex/pokedex_description_text.asm`. It gives animation first use
of the interval and defers bounded text slices when a competing publication
is pending or the scanline budget is late during active playback. The initial
trace suggested a preparation/admission delay, not a dropped button.
Which gate dominates each long case requires a separately scoped investigation;
do not relax deadlines or add generic interrupt overhead during reconciliation.

## Adjacent Work Is Separate

`BATTLE-MOVE-02` (Sand Tomb), battle cries, battle UI/animation/capture reports
and overworld turning research retain their existing adjacent-story statuses.
They are not automatically closed by Dex qualification, and were not newly
retested here. `DEX-CRY-03` is complete for standalone double-speed Stats;
its nested normal-speed battle owner is still adjacent deferred work.

The vitamin-prize bug is `BT-REWARD-01` in the dedicated
[Battle Tower backlog](battle_tower_bug_backlog.md). It is deferred, not part
of the remaining Dex implementation. See the independently runnable
[Tower suite](battle_tower_regression_suite.md).

## Reproduce The Focused Audit

The current local source adapter is
`build/dex-cleanup-20261014/runtime/`. Use a fresh output directory for each
attempt; the runner rejects reused completed outputs and mismatched provenance.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.backlog_reconciliation badges --source build/dex-cleanup-20261014/runtime --output build/dex-backlog-reconciliation-20261014/badges --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.backlog_reconciliation tabs --source build/dex-cleanup-20261014/runtime --output build/dex-backlog-reconciliation-20261014/tabs-corrected --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.backlog_reconciliation returns --source build/dex-cleanup-20261014/runtime --output build/dex-backlog-reconciliation-20261014/returns-corrected --jobs 6
PYTHONPATH=tools:. python3 -m unittest tools.test_dex_backlog_revalidation -v
```

Initial `tabs/` has 32 fixture failures because Sneasel is not immediately
before Weavile in the authored order. The corrected run uses Abomasnow and
asserts the actual incoming species; all 128 intended cases complete.
Initial `returns/` failed to compile because the optional observation header
omitted `wPokedexRenderedSelectionKey`. Its declaration was added only to the
host observer; `returns-corrected/` completes all 60 cases. Neither initial
attempt is counted as a game pass or defect. `backlog-before.md` preserves
the prior backlog. No game ROM changed during either correction.
