# Pokedex Backlog Reconciliation

Storage follow-up 2026-10-17: the user approved disposing of the completed
egg test prototype and historical run outputs. Component explanations and
measured results remain in `docs/`; strictly required regression inputs now
live in `tools/regression_fixtures/`. The [retirement map](pokedex_build_retirement.md)
supersedes older statements that a review ROM/video or raw run is retained.

Latest follow-up 2026-10-17: `DEX-DATA-01` is manually accepted and integrated,
including later-species footprints, all 122 sourced descriptions, measurement
corrections and direct-offset multipage rendering. The accepted combined
Mov/Info responsiveness iteration under `DEX-PERF-02` is integrated too.
Production ROM/symbols/map exactly match the fully qualified reviewed build,
SHA-256 `302099f5836115c776de6606379820fbc661c82824aee438364afd4e7f7834e9`.
Total growth versus previous production is 13,237 decimal ROMX bytes: 12,767
content, 466 renderer/metadata and four optimization bytes. No allocated RAM,
ROM0, HRAM or SRAM growth; the player's main save is unchanged. The full suite
excluding Battle Tower is retained for this exact link, and the user accepted
the documented phase-sensitive slower requests. See
[production integration](pokedex_responsiveness_prototype.md#production-integration).

Follow-up 2026-10-16: interactive registration (`NEWDEX-UI-02` option B)
is manually accepted and integrated, including the synchronized LCD-on capture
handoff, Pay Day preservation and 67 added evolution links. The user explicitly
retained all 20 reviewed temporary requirements. Root ROM/symbols/map exactly
match the fully qualified review build; fresh root checks pass. Cost is 5332
decimal ROMX bytes, with no allocated RAM/ROM0/HRAM/SRAM growth. Root ROM SHA-256:
`d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.
The player's main save is unchanged. See
[production integration](pokedex_interactive_registration_integration.md).
Earlier build hashes and pending-review notes below are historical.

Follow-up 2026-10-15: `DEX-PREF-01/02` are manually accepted and integrated.
Shared Modern/Legacy and independent Moves bookmarks are session-only; reset
starts first without losing sort/presentation preferences. Root ROM/symbols/map
exactly match the fully qualified prototype, with 28,836 additional fresh
production checks passing. Combined cost is 518 decimal ROMX bytes, eight
existing padding bytes assigned and no allocated RAM growth. Root ROM SHA-256:
`52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
See [production integration](pokedex_session_position_prototype.md#production-integration).

Follow-up 2026-10-14: `DEX-PERF-04` is manually accepted and integrated.
The root ROM matches the fully tested +51-ROMX-byte candidate exactly:
`942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc`.
Fresh root-build transition checks pass; see
[integration evidence](pokedex_unown_transition_regression.md#production-integration).
The hashes and pending-review notes in earlier records below are historical.

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
| `DEX-INFO-03` | +9 ROMX publication fix implemented and subsequently accepted. Fresh 1,492-case, six-model and full emulator regressions pass. No added RAM. Dependency and timing ceiling documented in the linked investigation. |
| `DEX-PAGE-01`, `DEX-DESC-01` | Shared buffered indicators and bounded Description page changes are complete. |
| `DEX-TRANS-01/02/03`, `DEX-NAV-01/02` | Accepted internal handoff, identity/graphics publication, boundary wrapping and fresh-axis input corrections. |
| `DEX-RETURN-01/03`, `DEX-GRID-01/03` | Accepted LCD-on Listing restoration, palette publication and stable presence metadata. |
| `DEX-GRID-05` | Changed-sort cache invalidation is integrated, not awaiting promotion. It was included in the accepted October 11 Moves/Search integration. |
| `DEX-UNOWN-01/02/03/04` | Accepted blank tiles, bounded form counts, red backdrop and black panels. |
| Unown form paging | Static decoding and atomic picture/map publication are integrated. Current CGB E median complete selection remains 49.02 ms. This is distinct from Modes transitions. See [Unown performance](pokedex_unown_performance_prototype.md). |
| `DEX-UI-01/02`, `DEX-AREA-01` | Footprint/category corrections and Area owner/return integration are complete. |
| `DEX-DATA-01` | Complete and production-integrated 2026-10-17. All 122 later-species footprints, descriptions, approved measurements and two-to-four-page rendering are accepted. [Integration and exact-link evidence](pokedex_responsiveness_prototype.md#production-integration). |
| `DEX-SEARCH-01/02/03/05` | Slowpoke palette/OAM, colored Results, small cursor/caught ball, compact icons, alphabetical controls and ranked type matching are integrated and manually accepted. |
| Moves Dex | Visual layout, scrollbar, discovery persistence/migration, acquisition/learning/battle hooks, initial Struggle discovery, sort remembrance, substring/type Search, themed text entry and standard cursor behavior are complete. Session-only position remembrance is also integrated, as noted below. See [original production integration](pokedex_moves_search_prototype.md#production-integration). |
| `DEX-PREF-01/02` | Manually accepted and production-integrated 2026-10-15. One shared Modern/Legacy species/viewport bookmark and an independent Moves bookmark; both reset on game restart. Exact qualified-ROM match and 28,836 fresh production checks pass. +518 decimal ROMX bytes, eight existing padding bytes, no allocation growth. [Integration and retained qualification](pokedex_session_position_prototype.md#production-integration). |
| Type Matchups and shared arrow blink | Accepted runtime mode-7 implementation, chart changes, immediate cursor-driven lower panel, layout and shared blinking are integrated. The precomputed alternative is archived. See [integration](pokedex_type_runtime_integration.md). |
| `DEX-PERF-01`, `DEX-EXIT-01` | Repaired Stage opening/closing is accepted and integrated. Current qualification includes 336 lifecycle cases and 88 exit replays, without early colored reveal or shell displacement. |
| `DEX-PERF-03` | Idle animation cache warming is removed from regular Dex modes. |
| `DEX-PERF-04` | Manually accepted and integrated byte-for-byte after full qualification. +51 ROMX bytes, no added RAM. Post-Info medians: entry 242.27 to 125.07 ms, return 249.55 to 98.86 ms; form paging remains approximately 49.02 ms. [Production verification](pokedex_unown_transition_regression.md#production-integration). |
| `NEWDEX-UI-02` options A/B | Visual-only A was accepted first; interactive B supersedes it in production as of 2026-10-16. Desc/Info/Mov/End, uninterrupted Selected-style playback, synchronized LCD-on capture handoff and Pay Day preservation are accepted and integrated. Full qualified-build identity and fresh root checks pass. [Integration](pokedex_interactive_registration_integration.md). |
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
| `DEX-DATA-02`, alias `DEX-INFO-02` | Final species/learnset/stat and evolution-requirement pass remains deferred. The reviewed 190-link graph is now complete and integrated, but 20 requirements are approved temporary equivalents rather than final mechanics. These are one underlying content item, not two renderer fixes. |
| `DEX-DATA-03` | Revalidate family egg-move inheritance after final evolution/egg/learnset edits. Private two/three-page qualification across 42 families completes 2026-10-17 with no new correctness regressions; the completed prototype was then discarded with approval, not promoted. Reusable long-list controls remain in tools. Final content approval and its page/bank bounds remain deferred. See [Egg Page Qualification](pokedex_egg_placeholder_prototype.md); the separate production TM-inheritance bug is not a renderer failure. |
| `DEX-DATA-04` | Regroup later-generation relatives/babies in the authored Evolves order shared by Modern and Legacy. National/Alphabet remain independent. |
| `DEX-PERF-02` | Optional broader performance review only. The combined Mov/Info scheduling iteration is accepted and integrated 2026-10-17, alongside the earlier Selected, entry/exit, warming-removal and Unown work. Accepted Info/Description timing tails are not functional blockers. |

The requested future Selected-screen implementation/code-space audit remains
optional. Retained precomputed display assets and archived alternative renderers
are intentional choices. Re-audit old registration helpers against the new
streaming owner before proposing further removal; no extra cleanup is approved
by this integration. There is no approved Dex feature awaiting promotion.

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
