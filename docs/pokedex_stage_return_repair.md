# Stage Pokedex Return Reveal Repair

Date: 2026-10-13. The user approved the repaired Stage and requested production
integration. Its source is integrated and fresh full qualification is complete.
This follows the transition/audio review of Production, Reference, Stage
and Hard Cuts. Historical diagnostic results below retain their original scope.

## Result

Stage's entry optimizations and both normal fades are retained. The return
mask now waits for one ordinary display update so the requested white palettes
actually reach hardware before the reload disables the LCD. This adds a
projected **three ROMX bytes**, bringing the Stage source projection from 99
to **102 bytes**, with zero new static WRAM0, WRAMX, ROM0 or HRAM allocation.
The diagnostic's helper grows from six to nine bytes; the source can keep the
sequence inline. The actual source-linked allocation is **96 ROMX bytes**,
six bytes below the diagnostic projection because the cold-layout adapter is
unnecessary in source. No other memory region grows.

Both premature colored frames are gone in the new prototype's checks. No
sound routine, font loader, shared interrupt or normal fade code is changed.
The complete exit effect finishes before the additional display wait.

Review image and matching copied save:
`build/dex-lifecycle-budget-20261013/stage-return-repair/review/pokecrystal-dex-entry-stage-fixed.gbc`.

## Reproduction And Cause

Open Modern or Legacy from the Start menu, then press B to return. Reference
and original Stage show two colored frames before the proper overworld fade.
The first contains mixed Dex/map tiles; the second shows the rebuilt map with
the old Dex palette assignment. The artifact lasts two display intervals,
**33.49 ms / 2 frames**, and appears in all 48 existing lifecycle cases for
each of Reference and Stage. Production does not show those frames.

`ClearPalettes` fills the software palette buffers with white and requests an
upload; it does not immediately write the CGB's physical palette RAM.
`DisableLCD` suppresses VBlank while waiting to turn the display off. The
optimized return goes from the queued white request into that reload without
letting the upload occur. The hardware therefore retains Dex colors while
the LCD is off. The shared reload re-enables it before the map publication
and first proper fade palette have completed.

The palette-write guard correctly avoids rejected writes during the direct
map copier, but it does not establish a white hardware mask. With old hardware
colors still present, partially restored graphics become visible for two
frames. There is no missing asset.

Production's `ClearBGPalettes` includes display waits before the reload, so
white reaches hardware first. Its longer restoration waits also keep the map
hidden. The repair preserves the necessary mask commitment without restoring
all those older waits.

The existing `cold-exit` and `music-best` alternatives also avoid this defect:
they restore maps with the LCD off and force white palettes before enabling
the screen. Their broader entry changes are not required for this repair.

## Exact Change

Original late mask:

```asm
call ClearSprites
jp ClearPalettes
```

Repaired late mask:

```asm
call ClearSprites
call ClearPalettes
jp DelayFrame
```

It runs after `WaitSFX`, before remembered mode bookkeeping and viewport
restoration. The caller does not depend on the temporary register results.
No additional persistent state or clock tracking is introduced. The extra
call can use two additional temporary stack bytes while clearing palettes.

The Stage and fixed diagnostic images differ only in the exit-mask call
target, the new nine-byte helper and cartridge checksum bytes. All entry
code and shared ROM0 code are byte-identical. Both transitions retain the
original four-step fades and their two-frame holds.

## Fresh Paired Timings

These controls were recorded together with the repair, not subtracted from
older runs at a different clock/display phase. Each design has 48 cases:
Modern/Legacy, three sort orders, four requested-input phases and first entry
plus immediate re-entry. One display frame is 16.742706 ms.

| Design | Entry median, ms / frames | Exit median, ms / frames |
| --- | ---: | ---: |
| Production | 777.5 / 46.44 | 860.1 / 51.37 |
| Original Stage | 445.2 / 26.59 | 694.4 / 41.48 |
| Stage with committed white mask | 445.6 / 26.61 | 711.7 / 42.51 |

The paired median exit cost versus original Stage is **18.2 ms / 1.09 frames**;
exit remains **148.2 ms / 8.85 frames faster than production**. Entry's paired
median difference is **0.18 ms / 0.011 frames**. Entry code is unchanged;
immediate re-entry starts at a different display phase after the longer exit.
The largest sampled paired entry difference is 13.82 ms / 0.83 frames. First
entry cases have effectively identical timing.

Fixed entry range: 427.1-479.8 ms / 25.51-28.66 frames.
Fixed exit range: 709.9-725.9 ms / 42.40-43.35 frames.

## Validation

- 144 fresh lifecycle cases: production, original Stage and fixed Stage,
  48 each. The dedicated reveal check rejects original Stage in all 48
  cases (96 bad frames); production and fixed Stage have zero bad frames.
- 288 fixed-Stage lifecycle cases across CGB models 0/A/B/C/D/E: no premature
  reveal and normal double-speed state retained.
- 88 detailed exits: zero shifted colored frames, rejected palette writes
  or blocked VRAM writes.
- 36 secondary-route cases comparing production with fixed Stage: mode
  cancel, Pokemon Search, Moves Search, Description, Info/ancestors, Selected
  Moves, Area, Unown and Type Matchups return paths pass.
- 36 independent completed-screen capture comparisons: correct static
  destinations, no reversion after completion. Final maps, attributes,
  palettes, OAM and viewport checks also pass.
- 20 host tests, including six new reveal-detector tests. Old Dex colors
  before LCD re-enable are allowed; old colors after re-enable are rejected.

The earlier investigation's final-screen and palette-bus checks missed this
mid-transition defect. Its "zero final UI differences" result was not proof
of correct reveal ordering. The new reveal check must accompany future Dex
lifecycle qualification, including cases whose final screenshots match.

### Audio Checks

Twelve native mixed-PCM comparisons cover entry and exit for Modern/Legacy
and all three sort orders. Click/beep active durations are unchanged between
original Stage and the repair. Representative durations:

| Sound window | Original and fixed duration, ms / frames |
| --- | ---: |
| Modern entry beep | 306.11 / 18.28 |
| Legacy entry beep | 286.28 / 17.10 |
| Exit beep | 283.86 / 16.95 |

Legacy captures are sample-identical during these active windows. Modern
captures have tiny phase/sample differences: the worst relative RMS
difference is 0.65%, and the lowest correlation is 0.99992. These are close
signal comparisons, not a guarantee of audible equivalence across all songs
or emulator audio configurations. The fix occurs after the exit beep ends;
there is no new fast-forwarding or truncation of either cue.

The original 437-byte Hard Cuts remains rejected by the user's beep review.
Its sound issue is not silently treated as fixed by this Stage-only change.
The user approved the repaired Stage after listening and visual review.
Fresh source-linked full qualification is complete; final integration evidence
is recorded separately from these historical diagnostic checks.

## Evidence And Reproduction Tools

Evidence root:
`build/dex-lifecycle-budget-20261013/stage-return-repair/`.

- `reference-stage-premature-reveal.png`: the two bad frames in both originals.
- `stage-fixed-return-frames.png`: original and repaired first reveal sequences.
- `reveal-audit.json`, `model-qualification.json`, `exit-hardware-audit.json`,
  `capture-audit.json`, `routes-summary.json`, `audio-audit.json` and
  `comparison.json`: measured checks and paired timings.
- `audio-review/`: native entry/exit beep WAV excerpts for manual listening.

Fixed ROM SHA-256:
`e970286ce7a9412f50b7b09718cdb2738f79d6ccb55b26d73791dd4e8cbcd425`.

Host runner: `tools/dex_timing/dex_lifecycle_return_repair.py`.
Local assembly helper: `tools/dex_timing/probes/dex_budget_mask_commit.asm`.
Negative host tests: `tools/test_dex_return_reveal.py`.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair prepare
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair profile --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair audit
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair models --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair audio-audit
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair exit-matrix
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair routes --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair capture-audit
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_return_repair report
```

These commands depend on the immutable earlier baseline/fixtures. Re-review
offsets and ownership if production changes; do not blindly replay the overlay.

## Production Integration

Production ROM: `pokecrystal.gbc`, SHA-256
`e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e`.
Baseline commit: `79f78ba6b`; baseline ROM:
`357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0`.
Fresh evidence: `build/dex-stage-production-integration-20261013/`.
The tested cartridge is also copied to
`/Applications/SameBoy/Games/pokecrystal.gbc`, with the same SHA-256.
The existing production save is unchanged; its before/after SHA-256 is
`bb38df0979599e89ce60fc09675732f23fb351ab6bd56c3f10f29e343fd5d5c6`.
No commit or push is made by this integration.

The game edits are limited to four files:

- `engine/pokedex/pokedex.asm`: clear the map after the existing graphics
  loader disables LCD, stage cold CGB listing palettes, and commit white after
  the complete exit cue but before viewport restoration.
- `engine/pokedex/pokedex_description.asm`: publish the exposed right edge
  directly while LCD is off, then enable LCD. The shared automatic-entry edge
  routine remains unchanged, with an explicit non-CGB fallback.
- `engine/pokedex/pokedex_legacy.asm`: use the existing staged listing layout
  on cold entry, just as on return entry.
- `engine/menus/start_menu.asm`: only Dex uses the guarded local close.
  Preserve map block rebuilding, normal fade-in and the non-CGB shared-close
  fallback. Other submenus still use the original shared close routine.

The actual linked cost is +32 bytes for the edge helper/net entry change,
+1 for direct cold-layout staging, +6 for the inline exit mask/wait, and
+57 for the close coordinator: **96 ROMX bytes total**. ROM0, WRAM0, WRAMX,
SRAM and HRAM allocation are unchanged, as are existing RAM symbol addresses.
The palette guard temporarily holds two AF bytes on the existing stack,
not a newly allocated buffer. Cartridge size is unchanged. Relinking updates
six ROM0 operand bytes referencing moved ROMX labels and the checksum;
the fixed-bank instruction sequence and all shared interrupt work are unchanged.
`integration.json` verifies every one of those relocations rather than
treating arbitrary fixed-bank changes as acceptable.

| Native median | Baseline ms / frames | Integrated ms / frames | Paired improvement ms / frames |
| --- | ---: | ---: | ---: |
| Dex entry | 777.49 / 46.44 | 445.56 / 26.61 | 332.10 / 19.84 |
| Dex exit | 860.11 / 51.37 | 711.65 / 42.51 | 148.18 / 8.85 |

Paired improvement is the median of matching case differences, not the
difference of independent medians. A display interval is 70224 cycles at
4194304 Hz, approximately 16.74 ms. These are emulated physical durations,
not host recording or wall-clock processing times.

Fresh source-linked focused checks pass:

- 336 lifecycle cases: 48 baseline, 288 integrated across CGB 0/A/B/C/D/E.
  No premature reveal, nonwhite pre-fade frames, completed-screen differences
  or clock-policy errors.
- 88 viewport/hardware exit cases and 36 secondary routes, no failures.
- Twelve freshly recaptured cue comparisons against the approved repaired
  ROM, no duration mismatch at 0.001 ms tolerance. Original production entry
  holds sound-active flags 35-58 ms longer because cold preparation services
  sound differently; this difference already existed in the approved Stage.
  Mixed music/PCM identity with original production is not asserted.
- 746 Info and 746 Selected Moves cases, 400 stress cases, 1056 feature
  timings, 115 panel returns and 96 font-reuse transitions, no failures.
- Twenty visual/reveal audit tests and five linked Stage safeguards pass.

The full campaign completed all 16 phases successfully, including its final
report. `precomputed-regression/full-regression.json` records `merge_ready: true`
and `issues: []` for the integrated hash. The final root rebuild has that same
hash. Fresh full qualification includes:

- 4479 main Dex cases, plus full Pokemon Search, all sort/mode transitions,
  Moves Search/text/cursor/sort memory and Unown content checks, no failures.
- 2238 cold/paging/warm playback cases, no failures.
- Persistence: 2380 native helper cases, 1490 cold boots, 152 interrupted
  writes, 150 interrupted repairs and five save lifecycle cases, no issues.
  Acquisition/learning, migration, discovery and battle-use contracts and
  semantics, including Bide, also pass.
- 960 paired cry/audio cases, surrounding gameplay, normal/custom menus
  and speed/learning/loss transitions, no issues.
- 7312 exhaustive battle renderer calls / 3656 pairs: exact timing, logical
  sequence, pixels and restoration. 1332 normal battle cases / 666 pairs
  retain exactly the same 34 exception identities as baseline, including the
  separately backlogged Sand Tomb hang. No new gameplay exceptions.
- Historical 100-move campaign: 1600 cases / 800 pairs, no failures or
  over-one-frame timing differences.
- Six-model Type visual checks; both 122-song Type audio/SFX stresses,
  including held navigation; six-model Unown selection and 156 decoder checks,
  all pass against this exact ROM.
- Shared arrows at 52 locations / 3328 idle frames, no new issues.
- Current host group: 86 tests, no new failures. The existing LY=64 synthetic
  Info handoff assertion fails identically on baseline/candidate (`5 != 0`).
- Historical host group: 187 cases per build, identical messages and
  outcomes: six failures, 16 errors and 103 skips. These are retained baseline
  limitations, not silently reported as clean passes.

No physical hardware testing was performed. Original Hard Cuts' audio issue
and unrelated baseline exceptions are not fixed or promoted by this change.
The production save was not edited. The workbook backup changes already in
the worktree were left untouched. Environment versions and exact relocation
proof are in `integration.json`; command logs, checkpoints and reports remain
under the fresh evidence directory.

See [Full Regression Suite](full_regression_suite.md#17-dex-entry-and-exit-reveal)
for the source-linked adapter, required return audit and rerun commands.
