# Pokedex Session Position Prototype

Manually accepted and production-integrated 2026-10-15. Modern and Legacy
share a session-only Pokemon bookmark, independent of the Moves bookmark.
The root ROM, symbols and map exactly match the fully qualified review build.
The manifest now records `full_regression_passed: true` and
`production_integrated: true`. The original private qualification and control
hashes below remain historical evidence; player saves were not changed.

## Production Integration

- Production ROM: root `pokecrystal.gbc`, SHA-256
  `52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
  It is byte-for-byte identical to the approved candidate, as are its matching
  symbols and map. The previous full standard/supplementary regression therefore
  qualifies this exact production binary; the full suite was not run again.
- Six assembly owners were integrated without changing the approved code:
  `pokedex.asm`, `pokedex_legacy.asm`, `pokedex_moves_mode.asm`, new
  `pokedex_position.asm`, `intro_menu.asm` and `ram/wram.asm`.
- Freshly compiled production observers pass 16,176 Pokemon and 12,641 Moves
  native cases, six real-input integration contexts and 13 lifecycle cases:
  **28,836 fresh cases, no failures**. Coverage includes Selected/Search
  isolation, independent nonzero bookmarks, exact reopen viewports, normal
  saving, actual soft reset, cold Continue, primary/backup recovery and New Game.
  Saved order/presentation preferences survive while both positions reset.
  All 21 combined Pokemon/Moves host contracts also pass after promotion.
- Combined cost remains **518 decimal ROMX bytes**, eight existing padding
  bytes assigned, four left, no allocation growth and no moved old RAM labels.
- Evidence, pre-integration root binaries/sources, complete patch and reusable
  root-link check driver: `build/dex-position-production-integration-20261015/`.
  `receipt.json` records exact-match/resource assertions and each fresh result.
  No player save or emulator library file was replaced. No commit/push was made.
- Promotion-aware host contracts validate the archived original root hashes
  and the new production artifacts/source against that receipt. Historical
  private-only protection assertions must not treat intentional promotion as
  an unapproved change to the control.
- The stored reconstruction diff was found to contain only the preceding
  Moves/reset portion. Its original copy is retained under integration
  `before/`; both `candidate.diff` and `tools/dex_timing/probes/pokemon_position.diff`
  now contain all six approved owners. A dry run against the frozen production
  source succeeds, and an actual replay reproduces all six source hashes exactly.
  This packaging repair changes no linked game byte.

## Build And Ownership

- Candidate ROM SHA-256:
  `52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
- Production control:
  `942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc`,
  commit `b439cf4e89b39187af6e5937e0f960ab2267a740`.
- Accepted Moves-only base:
  `4143902901b43a33b19dc9a901261ee35f2844e435796473d2fd468333ba5192`.
- Source, matching binaries, allocation map and evidence:
  `build/dex-position-memory-20261014/`.
- Complete production-relative source patch:
  `tools/dex_timing/probes/pokemon_position.diff`, also `candidate.diff` in the
  build directory. This patch includes the preceding Moves session changes.
- Qualified review bundle:
  `build/dex-position-memory-20261014/review/pokecrystal-dex-position-memory.*`.
  The save is a private all-333-moves-seen fixture, not the player's battery.
  A fresh boot of the published files verifies Legacy/Evolves at entry zero,
  Moves Alphabet at entry zero and all 333 move discoveries, without changing
  the input save. See `review-validation/results.json`.
- The prior Moves-only source, review bundle and evidence remain intact.
  New builds and review files stay under `build/`.

## Behavior

Closing/reopening the Dex restores the actually highlighted species and its
exact viewport, without requiring A or opening Options first. Modern restores
its grid cell and aligned three-row viewport; Legacy restores its seven-row
list viewport. Unknown Pokemon remain valid selections without revealing data.

Switching Modern/Legacy retains the selected Pokemon and uses the existing
layout-normalization rules. There are not separate browsing histories for the
two layouts. Changing Evolves/National/Alphabet starts first; confirming the
current sort or canceling retains position. Selected-page species paging is
authoritative after returning to the ordinary listing. Temporary Pokemon
Search Results cannot replace its bookmark. Moves remains independent.

Saving during play does not clear the live bookmarks. Actual soft reset or
shutdown followed by Continue starts both lists at the beginning, while saved
sort/presentation preferences remain valid. New Game clears both bookmarks and
preferences through its existing reset path.
Loading an emulator CPU save state resumes that live session; it is not a
power-on/Continue test and naturally restores its RAM/bookmarks.

## Implementation And Dependencies

`Pokedex_RememberListingPosition` runs only at ordinary Listing's B-exit. It
reads the permanent species word directly from the writable order table;
it does not resolve or lock a transient species ID. Existing live listing state
already survives Modes/Selected/Unown/Moves/Type visits, so no per-navigation or
per-frame capture is needed.

Keep this capture at the ordinary-list boundary, **not** generic `Pokedex.exit`:
temporary owners may have replaced the order table or cursor. A future direct
exit from another owner must recover the ordinary selection before recording.
Do not remove `wPrevDexEntry`; Description, ancestors, Moves, popup and Search
backup paths still use it, even though it no longer restores Legacy position.

`Pokedex_RestoreListingPosition` runs after order and presentation setup but
before grid-cache priming, portrait preparation and reveal. It validates the
tag/order/presentation and cell, then scans only the active listing length.
Missing/invalid records start at zero. Alphabet's seen-only list and the
seen-bounded Evolves/National lists are not treated as unconditional full lists.
Reordered or newly inserted entries retain the permanent identity and nearest
legal vertical position; Modern's column follows its ordinal modulo three.

Both helpers preserve AF/BC/DE/HL and raw incoming WRAM-bank selection. There
are no changes to shared interrupt, timer, VBlank, LCD, palette or audio handling.
Existing registers/stack are used rather than a new display/restoration buffer.

The new fields occupy WRAMX bank 1 padding:

| Field | Address | Bytes |
| --- | --- | ---: |
| Format/presentation/order tag | `$d9e8` | 1 |
| Permanent species identity | `$d9e9-$d9ea` | 2 |
| Modern cell or Legacy row | `$d9eb` | 1 |

Tags are `$c0-$c2` for Modern's three orders and `$c4-$c6` for Legacy's.
Successful Continue clears the contiguous eight bytes from the Moves tag
through the Pokemon cell, after loading/confirmation/RTC acceptance. Compile-time
assertions enforce this layout. **Keep that reset in actual Continue, not generic
loading/validation that can run during play.** Existing save copying may include
the padding, but the next Continue intentionally discards it. There is no new
save version, custom SRAM write, discovery record or migration.

## Exact Decimal Costs

| Change | ROMX bytes |
| --- | ---: |
| New capture/restore/tag/alignment helpers | +397 |
| Two call sites | +6 |
| Extend Continue clear by four stores | +4 |
| Remove inherited Legacy restorer | -126 |
| Remove its old far-call site | -6 |
| Net Pokemon extension over Moves-only prototype | **+275** |
| Combined Pokemon and Moves extension over production | **+518** |

Four more existing padding bytes are assigned, eight total with Moves. Four
remain at `$d9ec-$d9ef`; following scene data remains at `$d9f0`. No old RAM
address moves. Additional allocated WRAMX/SRAM/WRAM0/ROM0/HRAM is **zero bytes**.
No graphics, VRAM/OAM buffer or generated-table additions are needed.

## Focused Qualification

- 16,176 native cases: 11,022 complete legal viewport round trips across both
  presentations and all three orders; 2,064 short/boundary-list cases;
  3,042 malformed restores; 18 rejected captures; 30 changed-order/insertion/
  missing-identity cases. Bank/register restoration, unchanged transient-ID
  tables/discovery, garbage collection, adjacent Moves preference preservation
  and zero helper SRAM writes pass.
- 48 real-input contexts cover every grid cell and Legacy row in every order,
  full Dex close/reopen, same/changed sort and repeated layout conversions.
- Six integration contexts cover ordinary Selected paging, Search Results and
  Selected-from-Results isolation, independent nonzero Moves/Pokemon bookmarks,
  normal Save, same-session reuse, real A+B+Select+Start and cold Continue.
- Six sparse/unknown contexts preserve hidden entries and seen-only Alphabet.
  Thirteen lifecycle cases cover primary/backup corruption and actual New Game.
- Moves is requalified with 12,641 native helper cases, 32 UI contexts,
  16 shared-owner restores, four Search edges and four session-reset contexts.
- Eleven additional current-link host/resource/ownership contracts pass.

Evidence is under `pokemon-position-tests/`, `position-tests/`,
`moves-session-validation.json` and `bookmark-contracts.json` in the build root.

## Timing And Audio

Physical display frames use `70224 / 4194304` seconds, not emulator speed.
The native restore helper's measured median is **2.224 ms / 0.133 frames**;
maximum **6.409 ms / 0.383 frames** across the legal-view matrix. Capture runs
only on exit, and restore only on reopen; navigation has no new work.

The 336-case lifecycle matrix's paired median opening difference is
**+0.063181 ms / +0.003774 frames**; closing is
**+0.000477 ms / +0.0000285 frames**. No completed-screen corruption or early
colored reveal is detected; the 88-case hardware exit audit passes.

An additional 144-case real-button matrix samples first/middle/last positions,
all orders/presentations and four input phases on both links. These are
**workflow comparisons**, not equal rendering workloads: production uses its
old reopen policy; the candidate restores the requested selection/viewport.
Do not attribute all differences to the lookup alone.

| Reopened position | Modern complete-display median delta | Legacy complete-display median delta |
| --- | ---: | ---: |
| First, ordinal 0 | +0.332 ms / +0.01985 frames | +0.072 ms / +0.00430 frames |
| Middle, ordinal 186 | -2.108 ms / -0.12588 frames | +1.672 ms / +0.09985 frames |
| Last, ordinal 372 | -2.051 ms / -0.12252 frames | **+20.016 ms / +1.19552 frames** |

The last Legacy workflow is the main performance point for manual review.
It includes different portrait/list work and frame alignment versus the original
return-to-start screen. The recorded CPU-ready median across both layouts at
the bottom is +14.205 ms / +0.84844 frames; this is not the complete-display
metric above. Exit differences remain effectively zero.

Normal save-body median differs by -0.029802 ms / -0.001780 frames in the
four-sample fixture. Valid loading, legacy/full migration and backup recovery
procedure timings match exactly. These procedure-body measurements are not
complete Save dialogue durations or a claim of a new saving optimization.

All twelve button-cue comparisons have **identical sound-register values and
relative physical hardware-write timing**. The old generic audio audit rejected
six entry flag durations because it assumed every scenario's duration delta
equaled one global opening median. The stronger same-case proof shows onset
and post-hardware busy-flag deltas exactly equal the nonoverlapping fade/init
procedure deltas. The hardware cue is unchanged; only flag-clear bookkeeping
varies by roughly -0.00334 to +0.05484 ms. Exits match exactly. See
`lifecycle/audio-hardware-proof.json`; the rejected original expectation remains
in `audio-global-assumption-rejection.json`.

## Full Regression

All sixteen standard phases pass after the retained fixture-order retries.
`runtime-regression/full-regression.json` reports `merge_ready: true` and no new
issues for the exact candidate/control hashes above. This report flag does not
authorize production integration. Finalization separately requires the new
bookmark cases and supplementary reports, exact ROM/RAM identities, retained
New Entry boundary coverage and unchanged protected files.

| Coverage | Completed result |
| --- | --- |
| Pokemon orders, layouts, navigation, Search and returns | 4,479 cases pass |
| Existing Moves/Search/sort remembrance | All filtering, UI, visuals, navigation, cursors, save and preference tests pass |
| Discovery persistence/migration and acquisition/learning | Standard bit/index/bank, cold-boot, corruption, interrupted-write, lifecycle, hook and source matrices pass |
| Battle-use discovery | Contract, semantic and Bide matrices pass |
| Separate 100-move suite | 1,600 rows / 800 pairs; exact durations |
| Selected Info/Moves | 746 Info, 746 Moves, 400 stress, 1,056 feature and 115 return cases pass |
| Selected playback | 2,238 cold/paging/warm cases pass across both layouts |
| Active Description returns | 1,492 species/age cases pass; maximum 5.612 frames under the eight-frame limit |
| Six-model Description returns | 1,536 cases pass |
| Type/Unown and music | All six CGB revisions pass; both 122-song stress matrices pass, including held navigation |
| Unown paging/decoder | 112 cases on each model; 156 decoder cases and negative controls pass |
| New Entry | 746 species, 60 visual and 8,270 generated input cases pass; four fresh boundary replays preserve the prior input union |
| Catch and nickname returns | Four cases each pass |
| Dex lifecycle/publication/audio | 336 lifecycle, 36 secondary routes, 88 exit cases and twelve hardware cue proofs pass |
| Host contracts | 87 current tests with zero skips; 44 additional Description/ancestor tests plus eleven new bookmark contracts pass |

The all-animation renderer completes 7,312 calls / 3,656 pairs with exact
timing, logical sequence and rendered pixels. The ordinary-input matrix has
1,332 rows / 666 pairs: 632 clean pairs and 34 unchanged exceptions per link.
Those include existing conditional-move fixtures, ending/KO/switch returns and
Sand Tomb. Existing sampled-audio and historical host exceptions are not
relabeled as clean passes. The independent Battle Tower addendum and physical
hardware/manual audio acceptance are outside this standard campaign.

## Harness Corrections And Reproduction

No cartridge correction has been needed after the first successful 518-byte
link. Retained setup corrections are separate from game regressions:

- Legacy navigation tests now wait for an owner-loop update/release rather than
  send a second two-frame input during a portrait update. Initial UI/integration
  attempts remain; successful reports point to fresh attempt directories.
- New Game must run through the title menu's normal caller. Directly calling
  its broad RAM reset from a suspended overworld helper destroys that helper's
  context; the rejected direct-call attempt remains as a harness failure.
- Modern checkpoint setup now explicitly seeds Modern/Evolves in a private
  copy, instead of assuming the donor battery's remembered presentation.
  The failed checkpoint folder and reconstructed error receipt remain. The old
  wrapper reused that first log filename; future retry logs get unique names.
- Gameplay waits for discovery fixtures; battle-discovery waits for menu/battle
  fixtures; timing waits for persistence/migration fixtures. Premature attempts
  are retained in phase history and must be replaced by completed runs, not
  counted as passes. Chart unit setup now creates its own output directory.
- Resume checks compare six-model fixtures with the selected candidate hash,
  not the production root hash. Optional trace compression remains lossless
  and limited to consumed traces inside this fresh evidence root.

The complete patch applies to the frozen production source, not on top of the
Moves-only patch a second time. For a new build, use a fresh `--output` under
`build` with `tools/build_dex_position_prototype.py prepare`, then `build`.
Prepare the normal campaign through `dex_cleanup_campaign prepare --base ...`
and run setup first. Run `pokemon_position` prepare/helpers/ui/integration/
lifecycle/sparse/warm_timing and `dex_position_campaign` standard/supplementary
actions. Respect the fixture dependencies above. Finalize only after every
required report passes, then publish. No old CPU checkpoints may be reused
across different ROM links.
