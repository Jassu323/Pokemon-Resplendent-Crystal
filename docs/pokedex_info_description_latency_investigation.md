# Info To Description Latency Investigation

Date: 2026-10-14. Cause isolated; the user selected the **9-byte
pending-map-aware fix**, now implemented in production. Fresh exact-link full
emulator regression passes with no new failures. Manual review and real hardware
testing are not claimed; the completed private comparisons remain below.

## Findings And Reproduction

The long delay is **publication starvation**, not slow text parsing, dropped
input or sampled-cry decoding. This supersedes the initial reconciliation's
preparation/scanline-admission hypothesis.

Use a separate all-seen/all-caught save. Open Grovyle, settle playback, select
Info, internally page Down to Sceptile, then select Desc during the incoming
animation. Some phases respond quickly; the age-8 replay waits about two
seconds. Hitmonlee -> Hitmonchan gives an even longer early-playback case.
Age is measured after reaching the incoming owner loop, before moving the
footer cursor; age 0 does not mean A on its first instruction.

In the Modern Sceptile age-8 q0 trace, A is accepted in 3.74 ms. Text is ready
about 21.20 ms after the request, then waits approximately 1,991 ms for its
VBlank publisher. Complete visible Description arrives at 2,028.83 ms /
121.18 display frames. No additional text buffer or font assets are needed.

The expanded **active internal-paging matrix**, not an average of general Dex
navigation, reaches a median 1,784.97 ms / 106.61 frames and maximum 4,647.95 ms
/ 277.61 frames. The maximum is Hitmonchan, which has a synthesized cry.

## Exact Cause

Owners: `Pokedex_VBlankDispatch`, `Pokedex_VBlankAnimationFrontpicMap` and
`Pokedex_VBlankDescriptionText` in `engine/pokedex/pokedex_3.asm`, and
`PokedexInfo_ReturnDescription` in `engine/pokedex/pokedex_info.asm`.

1. Returning from Info sets `wPokedexInfoRestoreDescription = 1`, requesting
   lower attributes and obsolete Info OAM restoration as well as text.
2. Text rendering finishes and queues `POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT`.
3. The dispatcher gives the portrait publisher first use of the interval.
4. That publisher returns **carry set even when it defers a queued future
   portrait**. Its `.defer` path uses `scf; ret`. Carry is a budget reservation,
   not proof that a transfer happened.
5. On carry set, the dispatcher skips the larger Description restore when
   `wPokedexInfoRestoreDescription` is nonzero. It thus excludes both used
   intervals and otherwise free intervals reserved for a future portrait.
6. The next portrait is often queued throughout its predecessor's authored
   hold. The lower-panel restore can remain excluded until playback ends.

Ordinary Description A-page changes do not need that full attribute/OAM
restore. The analogous Selected Moves -> Description return uses the same
restoration owner and benefits from the same correction.

The +9 fix recognizes an unused reservation by checking the **still-set
`POKEDEX_ANIM_MAP_PENDING_F`**. The current atomic portrait publisher clears
that flag only after a complete transfer. The existing Description helper
still checks LY, DMA locks and active-animation-upload ownership. After an
actual portrait transfer, the larger restore remains excluded.

### Atomic Portrait Contract

The production dispatcher depends on these existing rules of
`Pokedex_VBlankAnimationFrontpicMap`:

- A deferral writes no portrait map/attribute rows and leaves
  `POKEDEX_ANIM_MAP_PENDING_F` set. Carry can still be set: it denotes a
  reservation, not successful publication.
- A complete portrait publication transfers all seven rows in both VRAM banks
  within one VBlank, then clears `POKEDEX_ANIM_MAP_PENDING_F`.
- After carry is returned, a still-set pending flag lets the dispatcher
  **attempt** full Description restoration. The lower helper independently
  rejects active animation uploads, BG/DMA ownership and late LY admission.
  A cleared flag retains the exclusion after a real portrait transfer.

Do not introduce partial portrait writes that consume the interval while
leaving the pending flag set without revisiting this decision. Likewise,
clearing the flag on cancellation or changing its completion meaning requires
review. A stale set flag after a real transfer could permit two large updates
in one interval. An incorrectly cleared flag on deferral can unnecessarily
delay the lower panel or lose the queued portrait. If this contract changes,
use an explicit transfer outcome or deliberately revise deadline-aware
arbitration, then requalify LY/DMA budgets, authored
portrait deadlines, cry completion, bank/register restoration and tab returns.
The 17-byte experiment is not automatic partial-transfer support.

This is a documented local dependency, not a proposal to add partial transfers.
The atomic renderer prevents piecemeal display updates and remains unchanged.
Here, atomic means **visible portrait map/attribute publication**, not every
graphics upload. The existing hidden/staged graphics upload pipeline can still
work in chunks; its active-upload guard remains in the Description helper.
No generic LCD/VBlank path, battle code, RAM allocation or save format is changed.

The reusable integration runner freezes the actual dirty checkout rather than
Git HEAD, proves its baseline rebuild matches production, verifies the exact
9-byte allocation delta and unchanged RAM labels, and requires the new root ROM
to match the previously tested private candidate. Frozen baseline, source,
matching symbols/maps and fresh full-suite evidence are retained under
`build/dex-description-fix-integration-20261014/`.

## Historical Attribution

The same long case reproduces on current production, pre-cleanup production,
pre-Stage and pre-ancestors builds. The cleanup did not introduce the measured
delay, although settled manual reviews would not expose this active-paging path.

| Frozen link | ROM SHA-256 | Modern Sceptile age-8 q0 |
| --- | --- | ---: |
| Current cleanup | `dbef024fdaa1cdceb5a7458e323ac5d0f7e012ddfabb35585e3d806219f3ca7a` | 2,028.826 ms / 121.177 frames |
| Pre-cleanup / Stage | `e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e` | 2,028.826 ms / 121.177 frames |
| Pre-Stage / ancestors | `357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0` | 2,028.826 ms / 121.177 frames |
| Pre-ancestors / fast Unown | `6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac` | 2,028.826 ms / 121.177 frames |

128 cases per link, 512 total, use each link's own matching checkpoints.
Pre-cleanup paired differences relative to current are -0.0324 to +0.0300 ms
/ -0.00194 to +0.00179 frames, with zero median. Earlier links differ by at
most about 1.243 ms / 0.0742 frames, not seconds. Alignment differences remain
recorded in `comparison.json`.

Source history dates the full-restoration skip to Info-tab commit
`7d82ae0396ae0083cc64fb03f36239c07c75502a`, October 3. This identifies the
policy's origin, not a measured claim about every October 3 input. The oldest
binary replay here is the October 12 pre-ancestors link.

## Options And Costs

Costs are **decimal linked bytes relative to production**. All three add zero
ROM0, WRAM0, WRAMX, HRAM and SRAM, move no RAM labels, change no save format,
and require no artwork or additional generated tables.

| Option | ROMX | Complexity | Risk and tradeoff |
| --- | ---: | --- | --- |
| **Pending-map-aware arbitration, chosen** | **+9** | Low; one local dispatcher decision | Full emulator regression passed. Uses unused intervals while retaining the full-restore/real-portrait separation rule. A future partial visible-map publisher must revisit the pending-flag contract. |
| Deadline-aware lower-panel arbitration | +17 | Low/moderate; extend existing Info scheduling to ready Description work | Low/moderate. Explicitly distinguishes future and due portraits, without interpreting carry as completion. Alters the Info/Description arbitration branch and uses existing deadline/counter-wrap rules. No material timing advantage in this matrix. |
| Allow combined portrait and full Description publication | 0 | Low; replace a conditional call with an unconditional call | Moderate. Existing helper locks and LY checks remain, and focused tests pass, but both larger transfers can now share one VBlank. Requires worst-case combined-budget/timer-latency qualification. Saves nine bytes without a measured frame advantage. |

The +9 version introduces no new owner, cache or buffer. Its game-source edit
is limited to the Dex-specific dispatcher. Ordinary `LCD`, `VBlank_Normal`,
`VBlank_Cutscene` and `VBlank_CutsceneCGB` executed byte ranges are identical
across the three candidates. Dex mode 7 gains local work; its interrupt duration
is not claimed unchanged. Follow the
[interrupt timing contract](battle_animation_interrupt_timing_contract.md).

### Rejected Alternatives

Widening text-work admission from LY 96 to 128 costs zero bytes; servicing
bounded text earlier in the Selected loop costs five ROMX bytes. Both private
128-case trials retain the long Sceptile wait. Early service helps some
Meganium age-0 alignments, but leaves multi-second cases. Text is already ready;
relaxing preparation margins or adding a Description cache does not address
the publication block.

## Timing And Qualification

Each full matrix has **1,492 cases**: all 373 incoming species, Modern/Legacy,
ages 0/8 during playback. All candidates pass content, ownership, complete
badge/type/footprint checks, exact authored portrait publication timing and
natural cry completion. This is CGB E evidence, not all hardware revisions.

| Link | Median complete | Maximum complete | Paired median change |
| --- | ---: | ---: | ---: |
| Production | 1,784.97 ms / 106.61 frames | 4,647.95 ms / 277.61 frames | Control |
| Pending-map-aware | 60.45 ms / 3.61 frames | 93.95 ms / 5.61 frames | -1,724.52 ms / -103.00 frames |
| Deadline-aware | 60.45 ms / 3.61 frames | 93.95 ms / 5.61 frames | -1,724.52 ms / -103.00 frames |
| Combined | 60.45 ms / 3.61 frames | 93.95 ms / 5.61 frames | -1,724.52 ms / -103.00 frames |

Targeted four-species/four-age/four-phase timing adds 128 cases per candidate,
including settled controls. The recommended Sceptile replay drops to 53.20 ms
/ 3.18 frames. Combined differs from +9 by at most 0.001431 ms / 0.0000855
frames in the full matrix: no display-frame benefit.

Individual paired display changes range from -4,587.74 to +1.191 ms, roughly
-274.01 to +0.0711 frames. No matched case becomes one display frame slower.
These improvements concern active internal paging, not all general navigation.

All 122 sampled species are covered in 488 sampled-cry cases per link. Each
sample completes with zero compressed blocks remaining; no audio/animation
underrun is recorded. Cry-stop timing **relative to first portrait publication**
is not bit-identical: +9 ranges from -1.381 to +1.239 ms, about -0.0825 to
+0.0740 frames. Other candidates have similarly small changes. This is not
a waveform/perceptual-equivalence claim. Audio code/data and authored portrait
durations are unchanged.

The +9 candidate additionally passes 400 Info rapid-input/cancellation cases,
115 retained-panel/Listing returns, 128 Selected Moves-to-Description returns
and 128 uncaught-owner checks. The latter two are retained separately under
`moves-returns/` and `visibility-corrected/`.
Eleven host controls pass, including incoming-metadata ordering, unique case
coverage, order wrap, and existing marker/header negative controls. Counts
overlap and must not be summed as unique complete scenarios.

The original private comparisons still required full
Pokemon/Moves/Search/Area/Unown/Types/discovery/save,
all battle animations/audio, PC/daycare and surrounding-gameplay regressions;
rapid alternating tabs, both Info atlases, earliest/latest VBlank admissions,
DMA-descriptor and bank/register restoration, all supported CGB models, and
manual display/audio review. The chosen +9 production link's fresh qualification
is recorded next; +17 and combined remain private alternatives, not promoted.

## Production Integration

User decision: implement the +9 fix and document its dependency. Production
source and root ROM are updated; the fresh full campaign passes with no new
failures. All 16 ordered standard phases, including the consolidated report,
return zero. Required supplementary display/audio/playback checks also pass.
No commit/push or player battery modification is performed by this integration.

Frozen pre-fix source rebuilt to the exact production baseline ROM
`dbef024fdaa1cdceb5a7458e323ac5d0f7e012ddfabb35585e3d806219f3ca7a`.
The updated root ROM matches the previously tested private +9 candidate exactly:
`12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d`.
Actual linked cost is **9 decimal ROMX bytes**, zero in every RAM class/ROM0,
and no moved RAM symbols. The only game-source edit is the dispatcher decision
and dependency comments in `engine/pokedex/pokedex_3.asm`.

Completed fresh checks on this exact production link:

| Coverage | Cases | Result |
| --- | ---: | --- |
| Info active/settled four-age/four-phase returns, Modern/Legacy | 128 | Pass |
| Selected Moves-to-Description returns | 128 | Pass |
| Uncaught Info-to-Description returns | 128 | Pass |
| All 373 incoming species, ages 0/8, Modern/Legacy | 1,492 | Pass; 60.45 ms / 3.61-frame median, 93.95 ms / 5.61-frame maximum |
| Six CGB models, Info/Moves, both layouts and four input phases | 256 per model, 1,536 total | Pass; maximum 82.50 ms / 4.93 frames in this targeted matrix |
| Complete Info / Selected Moves / rapid-cancel matrices | 746 / 746 / 400 | Pass |
| Ancestor/all-page feature timings / retained-panel returns / font-reuse transitions | 1,056 / 115 / 96 transitions | Pass |
| Exhaustive battle renderer, both links | 7,312 calls | Exact timing/logical/rendered-frame parity; restoration passes |
| Normal battle-input all-move catalog | 666 per link | Matching 34 known exception identities; no new native failures |
| Entry/exit lifecycle / secondary routes / exit hardware publication | 336 / 36 / 88 | Pass |
| Dependency, latency-gate and existing visual negative controls | 14 | Pass |
| Standard Pokemon Dex / Unown | 4,479 / 136 | Pass; 2,212 Unown selections and 126 direct draw units |
| Ordinary selected playback, cold/paging/warm, both layouts | 2,238 | Pass; exact authored playback checks |
| Standard 100-move battle comparison | 800 matched pairs / 1,600 rows | Zero duration differences, 0 ms / 0 frames |
| Sampled cries / surrounding gameplay / battle clock transitions | 960 / 22 / 24 | Pass |
| Current linked host tests / historical host comparison | 87 / matching failure-error-skip identities | No new failures or errors |

Moves Search/type/substring filtering, keyboard/cursor, sorting/remembrance,
exhaustive discovery index/bank/register/GC tests, save/reload/corruption/repair,
legacy migration, interrupted writes, acquisition/learning/battle hooks,
PC/daycare, custom menus and popup readiness pass. Type Matchups has fresh
six-model visual checks and both 122-song audio/held-navigation stress runs.
Unown additionally passes 112 paging cases on each model and 156 decoder cases.
The separate Battle Tower addendum was not rerun: this is the standard campaign,
and its already logged reward bug remains separate.

Counts overlap and are not a unique scenario total. Ordinary LCD and the
normal/cutscene VBlank executed byte ranges are identical to the frozen baseline.
Entry paired median delta is 0 ms / 0 frames; exit is +0.000477 ms /
+0.0000285 frames. Button sound-register sequences match; duration deltas are
zero or -0.000477 ms, within the existing four-tick comparison tolerance.

The scoped regression ceiling is **eight physical display frames / 133.94 ms**
for the 1,492 caught active Info returns. All pass; the pre-fix control rejects
1,440 cases. This gate catches starvation even if content eventually becomes
correct. It is not a universal budget for every Dex operation.

Retained evidence: `build/dex-description-fix-integration-20261014/`, including
`integration.json`, `description-response-budget.json`,
`runtime/all-species-integrated/summary.json`, `description-models/summary.json`,
`all-animations/report.json` and `dependency-host-final.log`. The full standard
report is `runtime-regression/full-regression.json`, with `merge_ready: true`,
an empty new-issue list, and the expected real-hardware/historical-host scope
limitations. The 34 native battle exception identities, including the separately
deferred Sand Tomb issue, match baseline; they are not newly passing move tests.
Both listing styles' 256 paired owner-reveal timings are exactly unchanged.

Preserved harness issues: the first model sweep passed all CGB 0 cases but
stopped on a reporting-only `rom` versus `rom_sha256` key typo. The corrected
`models` action validates/reuses that successful report and completes the other
five fresh model matrices; retry output is `description-models-retry.log`.
The original post-publication screenshot could still show the previous scanout.
The observer now captures after two actual display frames; new separate
`review-native/` Sceptile/Hitmonchan replays pass. No cartridge code was changed
for either harness correction, and timing measurements are unchanged.

## Artifacts And Reproduction

Root: `build/dex-description-latency-20261014/`. `comparison.json` contains
paired results, resource/RAM-label checks, ordinary interrupt-code identity,
and cry-stop differences. `history-retry/history/` is canonical attribution;
`current/trace/` diagnoses the original block. The canonical broad baseline is
`current/all-species-audio/`. Candidate directories retain source, manifests,
ROM/symbol/map, fresh matching checkpoints and all reports. Canonical paired
matrices are `all-species-audio/` for +9/+17, `all-species/` for combined.
`cutoff128/` and `early-text/` retain rejected alternatives.

The recommended review pair is
`pending-aware/review/pokecrystal-dex-description-fix.gbc` and its matching
`.sav`, a separate all-species-caught fixture. Matching symbols/map are beside
it. Do not replace the player's battery with this fixture. Comment-only
documentation added to the private dispatcher rebuilds to the same tested ROM.

| Candidate | SHA-256 |
| --- | --- |
| Pending-map-aware | `12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d` |
| Deadline-aware | `869294b6a54ee2f9ca3190fdcf9ce2cc2134dca5952c4e68e806f3b7f1d272a5` |
| Combined | `9c4e5cb38ec4a23e915f84f23948862532de84cca05819d067d11d69ef71234a` |

Reusable runners: `tools/dex_timing/description_latency.py`,
`backlog_reconciliation.py` and host-only `probes/description_latency.c`.
There are no cartridge instrumentation writes, waits or allocations. Use fresh
output tags; example paths below already hold completed evidence.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.description_latency test --variant pending-aware --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.description_latency all-species --variant pending-aware --tag audio --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.description_latency trace --variant pending-aware --jobs 3
PYTHONPATH=tools:. python3 -m tools.dex_timing.description_latency report
PYTHONPATH=tools:. python3 -m unittest tools.test_dex_description_latency tools.test_dex_backlog_revalidation -v
```

Preserved attempts: initial `history/` passed its 512 game cases but returned
failure because its guard also watched the live SameBoy battery, which changed
externally. Initial cutoff preparation stopped for the same reason. ROM/symbol/
map did not change. The final guard protects game artifacts and actual frozen
private inputs, not a live file unused by the tests. The canonical rerun passes.
The player battery is never a native test argument or write destination.

Initial `current/all-species/` has 1,492 harness errors from recording incoming
metadata before assigning it. A host test now covers that ordering; the complete
canonical rerun passes. Initial visibility preparation assumed its Legacy
battery selected Legacy, but the older adapter actually changes presentation
in gameplay. It was stopped; corrected preparation explicitly selects/verifies
the layout and bounds navigation. None is counted as a game defect or waived
acceptance. No production ROM changed.
