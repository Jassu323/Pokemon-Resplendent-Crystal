# Unown Transition Full Regression

Completed 2026-10-14. The selected **51-byte ROMX** candidate passes the full
standard campaign and supplementary qualification with **no new regressions**.
The user subsequently tested and accepted it, then authorized production
integration. The rebuilt root production ROM matches this exact qualified
candidate; see [Production Integration](#production-integration).

## Frozen Inputs

| Input | SHA-256 |
| --- | --- |
| Production | `12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d` |
| Qualified candidate | `942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc` |

Source baseline: `6b5da51953bdb814581707f95ff5be863340adb4`. Both snapshots
rebuild their respective ROMs exactly. The candidate is byte-identical to the
approved investigation build, not a later modified implementation.

Evidence: `build/dex-unown-transition-regression-20261014/`. Its final
`qualification.json` verifies all required phase statuses, controls, binary
identity, unchanged production files, unchanged RAM addresses and artwork.
`runtime-regression/full-regression.json` has `merge_ready: true` and no new
issues. This existing adapter flag means qualification, not an actual merge.

The delta remains +51 ROMX bytes and zero ROM0, WRAM0, WRAMX, HRAM or SRAM
bytes. Only `pokedex.asm`, `pokedex_legacy.asm` and `cgb_layouts.asm` differ
among assembly owners. All 11,349 retained `gfx` files, including source and
converted assets, match. No new graphics, VRAM reservations or OAM entries.

## Standard Campaign

All sixteen phases succeed: setup, Dex, Moves, persistence, discovery, gameplay,
battle discovery, timing, readiness, current host tests, historical host
comparison, Dex gift, chart, Type diagnostics, shared arrows and final report.

| Coverage | Result |
| --- | --- |
| Pokemon Dex, layouts, sorting, Search and owner returns | 4,479 scenarios, no failures |
| Unown correctness | 136 scenarios, 2,212 form selections and 126 direct draw cases pass; retained negative controls detect their defects |
| Moves Search/UI/sort memory | Filter, visual, navigation, text-entry, cursor, footer, save and preference checks pass |
| Persistence | 2,380 helpers, 1,490 cold boots, 152 interrupted writes, 150 interrupted repairs and five lifecycle cases pass |
| Acquisition/learning | 12,276 contracts, 59 positive/negative sources and migration/interruption checks pass |
| Battle discovery | 4,724 contracts, 400 semantic cases and eight supplemental Bide cases pass |
| Struggle grant | Initial/repeated awards, cold reload and no-premature-SRAM-write checks pass |
| Shared/custom menus | 1,792 input contracts, 464 custom-menu cases and popup-readiness comparisons pass |
| Gameplay/clock restoration | 22 paired scenarios and 24 battle-transition runs pass |
| Sampled audio | 960 rows / 480 pairs accepted; existing baseline misses remain identical |
| Selected playback | 373 cold, 373 paging and 373 warm cases pass in each presentation, 2,238 total |
| Current host tests | All 87 pass; zero skips |

Counts overlap and are not an additive independent-test total. The
[full specification](full_regression_suite.md) defines fixture/native-call
distinctions and acceptance limits.

## Battle Animation Comparisons

All 333 move animations and 28 auxiliary entries run from both sides and at
four physical phases, including declared parameter branches:

- 7,312 renderer calls / 3,656 matched pairs, with no missing, unexpected or
  duplicate cases.
- Every elapsed duration, logical update sequence and full-frame pixel-hash
  sequence matches production exactly. Bank, speed and VBlank restoration pass.
- 1,332 ordinary battle-input rows / 666 pairs have identical issue identities.
- The separate 100-move matrix has 1,600 rows / 800 pairs, each with
  **0 ms / 0 display-frame animation-duration difference**.

The 666 native pairs include 632 clean pairs and the same 34 production
exceptions: nineteen condition-dependent fixtures do not execute the requested
animation, thirteen ending/knockout/switch paths do not return to the generic
turn menu, and two Sand Tomb cases retain the known post-animation hang.
These are not newly passing scenarios or new defects. Sand Tomb remains a
separate deferred issue.

Evidence: `all-animations/report.json` and
`runtime-regression/acquisition-moves-regression.json`.

## Supplementary Checks

All supplementary checks pass on the same candidate:

- 746 Selected Info, 746 Selected Moves, 400 input-stress, 1,056 feature cases,
  115 panel returns and 96 post-Info/font-reuse transitions.
- 1,492 all-species active Info-to-Description returns. Maximum complete
  display is 5.612 frames, below the scoped eight-frame / 133.94 ms ceiling.
  Additional 128-case matrices cover active Info, Moves and uncaught returns.
- 256 active Info/Moves returns on each CGB 0/A/B/C/D/E, 1,536 total.
- Six-model Type layout/raster/return qualification and both 122-music-entry
  stress runs, with three menu SFX per entry and held-navigation coverage.
- 112 Unown paging cases on each CGB revision, 672 total: atomic whole-frame
  publication, caught-order bounds, held input and return ownership pass.
- 156 Unown decoder cases after prior 5-, 6- and 7-tile species pass. A separate
  deliberately stale decoder rejects exactly the expected 104 six-/seven-tile
  cases while preserving banks, stack, SRAM state and letter.
- New Dex Entry: 746 generated-species cases, 60 visual snapshots, 8,272 input
  sweep cases, four normal return flows and four nickname flows pass.
- 336 Dex lifecycle cases, 36 secondary routes and 88 hardware exit-publication
  cases pass, without premature reveal or palette-write rejection.
- Twelve button-cue register sequences match production; twelve cue duration
  comparisons remain within the existing physical-tick contract.
- Twenty-two additional Description/ancestor/runner contracts pass on each
  frozen link without skips.

## Performance

All times use physical display intervals: 70,224 ticks at 4,194,304 Hz, about
16.743 ms per frame regardless of CPU double speed. The original matched
post-Info measurements describe this exact qualified ROM:

| Route | Production ms / frames | Candidate ms / frames |
| --- | ---: | ---: |
| Modes to Unown | 242.27 / 14.47 | 125.07 / 7.47 |
| Unown to Modes | 249.55 / 14.90 | 98.86 / 5.90 |

Fresh full-regression comparisons outside these intended changes:

| Measurement | Matched difference |
| --- | ---: |
| Selected entry, 512 pairs across styles/phases/hover ages | 0 ms / 0 frames for first/complete display and owner reveal |
| All renderer and 100-move animation pairs | 0 ms / 0 frames |
| Normal Dex opening, median | 0 ms / 0 frames |
| Normal Dex closing, median | -0.000477 ms / -0.0000285 frames |
| Valid load, small/full migration and recovery | 0 ms / 0 frames |
| Normal saving, fixture median | +0.042677 ms / +0.002549 frames |

No material responsiveness regression is observed. Form paging remains about
49.02 ms / 2.93 frames. The [investigation](pokedex_unown_transition_optimization.md)
retains matched form-paging and transition distributions.

## Exceptions And Audit Correction

The historical host model runs 187 tests per link with the same six failures,
sixteen errors and 103 skips. Both identities and detailed reports match.
These older assertions do not replace native acceptance; the current 87-test
host group and supplementary contracts pass normally.

The sampled-cry comparison retains 32 known misses per link with identical
identities. Capture-return fixtures also retain the same early startup audio
event on both links. These are recorded, not erased or called newly clean
playback. See `paired_campaigns` in the standard report and
`unchanged_preexisting_capture_startup_audio_events` in `qualification.json`.

The first artifact-only finalization mistakenly treated `gfx/tilesets.o` as
artwork. Its relocation/debug metadata is not graphic data. The checker now
excludes `.o`/`.d` sidecars while still comparing every source/converted asset.
The rerun passes. No cartridge fix, fixture relaxation or ROM rebuild was
needed; `finalize-initial-failure.json` preserves the initial diagnostic.

Physical hardware and manual auditory acceptance are not certified. The
independent Battle Tower addendum was not rerun and its existing deferred
bug is not resolved by this standard campaign.

## Reproduction

Driver: `tools/dex_timing/unown_transition_campaign.py`. Its constants pin this
pair. Future links require a fresh output and deliberate updates to expected
hashes, paths and catalog counts, not reused CPU checkpoints or relaxed gates.

From the repository root with `PYTHONPATH=tools:.`, invoke:

```sh
python3 -B -m tools.dex_timing.unown_transition_campaign prepare --jobs 8
python3 -B -m tools.dex_timing.unown_transition_campaign standard
python3 -B -m tools.dex_timing.unown_transition_campaign report
python3 -B -m tools.dex_timing.unown_transition_campaign finalize
```

Before `report`, run the separate supplementary actions: `animations`,
`selected`, `description`, `models`, `displays`, `registration`, `lifecycle`,
`lifecycle_audit`, `routes`, `exit_matrix`, `audio_registers`, `audio`, and
`contracts`. Description/exit checks need Selected fixtures; lifecycle audit,
routes and audio need lifecycle evidence. Independent groups may run in
parallel, but never two writers against the same target.

For the decoder control, copy the frozen candidate into
`stale-decoder-control/candidate`, remove only `call GetBaseData` in its
`pokedex_unown_decode.asm`, and rebuild privately. Export matching
`pokecrystal-dex-unown-fast.gbc/.sym/.map` beside that source and copy the
private test battery. Before finalization, run:

```sh
python3 -B -m tools.dex_timing.unown_decoder --source build/dex-unown-transition-regression-20261014/stale-decoder-control --output build/dex-unown-transition-regression-20261014/stale-decoder-control/decoder --negative
```

Pre-integration qualification state: `full_regression_passed: true`,
`production_integrated: false`. This historical record is retained unchanged.
Review ROM: `build/dex-unown-transition-regression-20261014/pokecrystal-dex-unown-transitions.gbc`.
Matching symbols/map and a private battery with all Pokemon seen/caught and
all 26 Unown forms are adjacent. This is not the player's save.

## Production Integration

On 2026-10-14, after the user confirmed manual testing and requested integration,
the exact approved changes were applied to these three production owners:

- `engine/pokedex/pokedex.asm`: prepare and upload the hidden Unown layout using
  the existing fast-map helper; remove the redundant return delay.
- `engine/pokedex/pokedex_legacy.asm`: use that hidden upload only for the tagged
  Unown return, preserving ordinary Modes publication for other callers.
- `engine/gfx/cgb_layouts.asm`: separate software layout preparation from the
  existing public palette/attribute publication wrappers.

The root `pokecrystal.gbc`, `pokecrystal.sym` and `pokecrystal.map` were rebuilt.
The ROM SHA-256 is
`942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc`,
identical to the manually accepted, fully regression-tested candidate. The
three source owners also match the frozen candidate exactly. The linked delta
is **+51 decimal ROMX bytes** and zero ROM0, WRAM0, WRAMX, HRAM or SRAM bytes;
all existing RAM symbol addresses remain unchanged.

Fresh root-build checks cover Modern and Legacy entry/return after both Info
and Moves, four input phases each: **16 cases / 32 transitions**, no failures.
They check resident Unown font restoration, hide/reveal correctness, return
menu state and original listing selection. Full-suite results above apply by
exact binary identity; the entire campaign was not rerun after this rebuild.

Integration receipt and fresh evidence:
`build/dex-unown-production-integration-20261014/`. The original full-suite
`qualification.json` remains an immutable pre-integration record. No player
save or emulator-library file was changed; no commit or push was performed.
