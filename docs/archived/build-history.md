# Historical Build Catalog

Archived 2026-10-01 after accepting buffered Description icons.

Generated cartridges, copied saves/states, images, raw traces, compiled runners and large reports
were removed from the ignored `build/` directory. This catalog lists every former top-level
output, including calibration files that were not distinct ROM builds.

## Reproduction

The basic rebuild/restore script is `tools/rebuild_historical.py`. List IDs with `--list`;
inspect or restore one with `--id NAME --output /private/tmp/reproduction`. It copies only
the preserved sources and parameters, never a user save. `--build-reference` recreates the
instrumented reference from Git plus archived source overrides and checks its ROM hash.
`--build-source` recreates the recorded pre-buffering integrated handoff baseline.

Private overlays retain their original assembly, patch sites, fixed addresses and input hashes.
Use `--overlay --base-rom PATH --base-sym PATH` with the matching baseline to reconstruct a
supported overlay. Old fixed-address helpers must not be applied to a new link.

For example, reconstruct the base before its accepted buffered-icon overlay:

```sh
python3 tools/rebuild_historical.py --id dex-internal-transitions-integrated \
  --output /private/tmp/dex-old-base --build-source
python3 tools/rebuild_historical.py --id dex-icon-buffer-return-repair \
  --output /private/tmp/dex-old-icons --overlay \
  --base-rom /private/tmp/dex-old-base/checkout/pokecrystal.gbc \
  --base-sym /private/tmp/dex-old-base/checkout/pokecrystal.sym
```

These two source-derived cartridges and the frozen instrumented reference were
reconstructed and matched their historical ROM hashes before deleting outputs.

Host experiments often were counterfactual policies rather than playable ROMs. Their maintained
module and recorded parameter grid are listed below; use the module help and the linked
investigation for the complete command. Some early scripts contain original absolute paths.
Restore them under their former directory or adjust input paths in an isolated checkout.

Matching battery saves, authentic catch/start states and the licensed CGB boot ROM are external
inputs, not retained here. New fresh checkpoints can test current behavior, but they do not
recreate a historical captured timer/LCD phase. Portable sanitized timing fixtures already
tracked under `tools/dex_timing/fixtures/` remain available. No bit-identical capture replay is
promised without matching inputs. Nothing in this archive is selected by ordinary `make`.

RGBDS: 1.0.1. SameBoy source revision: `213a12ce93d66b105a113debd9396306066a7cfc`.

Machine-readable identities, parameter grids and compact outcomes: 
`tools/dex_timing/historical_builds/manifest.json`. Detailed retained notes are below.

## .DS_Store

Finder folder metadata; not a build or test input.

- Basic recipe: `none`; inspect with
  `python3 tools/rebuild_historical.py --id .DS_Store`.
- Details: [index](../index.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 12,292 bytes.

## dex-background-mask-ab

Private A/B palette mask: white portrait with panel-colored icon masks; superseded by retaining the outgoing icons.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-background-mask-ab`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 5 source/recipe files, 0 notes; 150 parameter records. Removed output: 3,531,713,180 bytes.

## dex-boundary-comparison.json

Host timing calibration/boundary evidence: dex-boundary-comparison.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-boundary-comparison.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 6,164 bytes.

## dex-buffered-icons-production

Production integration of the accepted buffered icons; all-species entry, playback, mask, return and buffer-alternation regressions.

- Basic recipe: `production-icons`; inspect with
  `python3 tools/rebuild_historical.py --id dex-buffered-icons-production`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 1,943,620,688 bytes.

## dex-buffered-icons-test

User-facing copy of the accepted return-repair prototype, not a separate implementation.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-buffered-icons-test`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 1 notes; 1 parameter records. Removed output: 6,186,888 bytes.

- [README.md](build-history/dex-buffered-icons-test/README.md).

## dex-category-rendering

Mew embedded terminator/category control-character investigation and corrected Mew/Drapion category-data regressions.

- Basic recipe: `archived-script`; inspect with
  `python3 tools/rebuild_historical.py --id dex-category-rendering`.
- Details: [pokedex_selected_bug_backlog](../pokedex_selected_bug_backlog.md).
- Preserved: 1 source/recipe files, 0 notes; 0 parameter records. Removed output: 7,503,783 bytes.

## dex-category-rendering-fixed

Mew embedded terminator/category control-character investigation and corrected Mew/Drapion category-data regressions.

- Basic recipe: `archived-script`; inspect with
  `python3 tools/rebuild_historical.py --id dex-category-rendering-fixed`.
- Details: [pokedex_selected_bug_backlog](../pokedex_selected_bug_backlog.md).
- Preserved: 1 source/recipe files, 0 notes; 7 parameter records. Removed output: 57,404,523 bytes.

## dex-cold-listing

All-species real-input cold entry and instrumentation-free linked timing/pixel/audio acceptance.

- Basic recipe: `tools.dex_timing.cold_listing`; inspect with
  `python3 tools/rebuild_historical.py --id dex-cold-listing`.
- Details: [dex_instrumentation_cleanup](../dex_instrumentation_cleanup.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 64,860,447 bytes.

## dex-cry-ownership

Early Dex-local cry cancellation and ownership handoff: synth resumption, outgoing exhaustion and active incoming-header overwrite.

- Basic recipe: `tools.dex_timing.cry_ownership`; inspect with
  `python3 tools/rebuild_historical.py --id dex-cry-ownership`.
- Details: [pokedex_cry_ownership_investigation](../pokedex_cry_ownership_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 62,249,366 bytes.

## dex-cry-ownership-cancel

Early Dex-local cry cancellation and ownership handoff: synth resumption, outgoing exhaustion and active incoming-header overwrite.

- Basic recipe: `tools.dex_timing.cry_ownership`; inspect with
  `python3 tools/rebuild_historical.py --id dex-cry-ownership-cancel`.
- Details: [pokedex_cry_ownership_investigation](../pokedex_cry_ownership_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 4 parameter records. Removed output: 22,823,763 bytes.

## dex-cry-ownership-integrated

Early Dex-local cry cancellation and ownership handoff: synth resumption, outgoing exhaustion and active incoming-header overwrite.

- Basic recipe: `tools.dex_timing.cry_ownership`; inspect with
  `python3 tools/rebuild_historical.py --id dex-cry-ownership-integrated`.
- Details: [pokedex_cry_ownership_investigation](../pokedex_cry_ownership_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 857,236,489 bytes.

## dex-description-ui

Description shell/page-badge, footprint background and compact type-badge implementation with all-species UI audits.

- Basic recipe: `tools.dex_timing.description_ui`; inspect with
  `python3 tools/rebuild_historical.py --id dex-description-ui`.
- Details: [pokedex_description_ui](../pokedex_description_ui.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 300,642,723 bytes.

## dex-full-replays

Full main/hold/idle linked replay and independent SameBoy comparison; actual captured inputs distinguished from synthetic continuation.

- Basic recipe: `tools.dex_timing.full_replay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-full-replays`.
- Details: [dex_full_replay_results](../archived/dex-scheduler/dex_full_replay_results.md).
- Preserved: 0 source/recipe files, 0 notes; 9 parameter records. Removed output: 271,536,677 bytes.

## dex-full-replays-end-to-end

Full main/hold/idle linked replay and independent SameBoy comparison; actual captured inputs distinguished from synthetic continuation.

- Basic recipe: `tools.dex_timing.full_replay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-full-replays-end-to-end`.
- Details: [dex_full_replay_results](../archived/dex-scheduler/dex_full_replay_results.md).
- Preserved: 0 source/recipe files, 0 notes; 9 parameter records. Removed output: 277,382,623 bytes.

## dex-full-replays-policy-baseline

Full main/hold/idle linked replay and independent SameBoy comparison; actual captured inputs distinguished from synthetic continuation.

- Basic recipe: `tools.dex_timing.full_replay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-full-replays-policy-baseline`.
- Details: [dex_full_replay_results](../archived/dex-scheduler/dex_full_replay_results.md).
- Preserved: 0 source/recipe files, 0 notes; 3 parameter records. Removed output: 77,930,851 bytes.

## dex-grid-presence

Listing restoration/cache ownership diagnostic: dex-grid-presence; skipped/late palettes, LCD-off flashes and presence flags instead of stale transient IDs.

- Basic recipe: `tools.dex_timing.listing_restoration`; inspect with
  `python3 tools/rebuild_historical.py --id dex-grid-presence`.
- Details: [pokedex_listing_restoration_investigation](../pokedex_listing_restoration_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 795,493,536 bytes.

## dex-host-full-dusknoir-end-to-end.json

Host timing calibration/boundary evidence: dex-host-full-dusknoir-end-to-end.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-dusknoir-end-to-end.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 2,486,434 bytes.

## dex-host-full-dusknoir-end-to-end.memory.bin

Host timing calibration/boundary evidence: dex-host-full-dusknoir-end-to-end.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-dusknoir-end-to-end.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-full-dusknoir-end-to-end.trace.txt

Host timing calibration/boundary evidence: dex-host-full-dusknoir-end-to-end.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-dusknoir-end-to-end.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 34,413,135 bytes.

## dex-host-full-dusknoir-state.memory.bin

Host timing calibration/boundary evidence: dex-host-full-dusknoir-state.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-dusknoir-state.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-full-dusknoir-state.trace.txt

Host timing calibration/boundary evidence: dex-host-full-dusknoir-state.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-dusknoir-state.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 34,413,135 bytes.

## dex-host-full-luxray.json

Host timing calibration/boundary evidence: dex-host-full-luxray.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-luxray.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 1,010,268 bytes.

## dex-host-full-luxray.memory.bin

Host timing calibration/boundary evidence: dex-host-full-luxray.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-luxray.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-full-luxray.trace.txt

Host timing calibration/boundary evidence: dex-host-full-luxray.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-luxray.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 22,221,560 bytes.

## dex-host-full-weavile-end-to-end.json

Host timing calibration/boundary evidence: dex-host-full-weavile-end-to-end.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-weavile-end-to-end.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 1,124,546 bytes.

## dex-host-full-weavile-end-to-end.memory.bin

Host timing calibration/boundary evidence: dex-host-full-weavile-end-to-end.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-weavile-end-to-end.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-full-weavile-end-to-end.trace.txt

Host timing calibration/boundary evidence: dex-host-full-weavile-end-to-end.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-weavile-end-to-end.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 16,167,302 bytes.

## dex-host-full-weavile-state.memory.bin

Host timing calibration/boundary evidence: dex-host-full-weavile-state.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-weavile-state.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-full-weavile-state.trace.txt

Host timing calibration/boundary evidence: dex-host-full-weavile-state.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-full-weavile-state.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 16,167,302 bytes.

## dex-host-promoted-first-miss.json

Host timing calibration/boundary evidence: dex-host-promoted-first-miss.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-promoted-first-miss.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 252,456 bytes.

## dex-host-promoted-first-miss.memory.bin

Host timing calibration/boundary evidence: dex-host-promoted-first-miss.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-promoted-first-miss.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## dex-host-promoted-first-miss.trace.txt

Host timing calibration/boundary evidence: dex-host-promoted-first-miss.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-host-promoted-first-miss.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 7,596,649 bytes.

## dex-icon-buffer-fast-repair

Fast footprint-only reentry repair; still one extra display interval in four of twelve paired returns.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-icon-buffer-fast-repair`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 5 source/recipe files, 0 notes; 45 parameter records. Removed output: 2,883,985,937 bytes.

## dex-icon-buffer-preflight

First alternate footprint/type allocation; normal-entry repair added a display interval in some return tests.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-icon-buffer-preflight`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 5 source/recipe files, 0 notes; 46 parameter records. Removed output: 2,884,161,022 bytes.

## dex-icon-buffer-return-repair

Final prototype: restore footprint set A during B-return, invalidate its old tag when set B is written; accepted by the user.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-icon-buffer-return-repair`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 5 source/recipe files, 0 notes; 45 parameter records. Removed output: 2,885,655,905 bytes.

## dex-instrumentation-cleanup

All-species real-input cold entry and instrumentation-free linked timing/pixel/audio acceptance.

- Basic recipe: `tools.dex_timing.cold_listing`; inspect with
  `python3 tools/rebuild_historical.py --id dex-instrumentation-cleanup`.
- Details: [dex_instrumentation_cleanup](../dex_instrumentation_cleanup.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 388,985,523 bytes.

## dex-internal-transitions-all

Selected-to-Selected handoff investigation: all; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-all`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 799,675,382 bytes.

## dex-internal-transitions-baseline

Selected-to-Selected handoff investigation: baseline; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-baseline`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 21,133,248 bytes.

## dex-internal-transitions-baseline-validated

Selected-to-Selected handoff investigation: baseline-validated; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-baseline-validated`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 800,403,186 bytes.

## dex-internal-transitions-fast-focused

Selected-to-Selected handoff investigation: fast-focused; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-fast-focused`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 1 parameter records. Removed output: 28,323,698 bytes.

## dex-internal-transitions-images

Selected-to-Selected handoff investigation: images; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-images`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 20,749,309 bytes.

## dex-internal-transitions-integrated

Selected-to-Selected handoff investigation: integrated; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-integrated`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 3 source overrides, 0 notes; 150 parameter records. Removed output: 1,782,788,159 bytes.
- Exact pre-buffering source baseline: Git `9855e86b8ff25244ad42a9e45411d33450f5981e`
  plus the three archived Dex ASM overrides. Rebuild with `--build-source`.
  ROM SHA256: `d220a73f6de22561623561911e39fddebe8389a3587af64eeca36b2a0340d7de`.

## dex-internal-transitions-late-active-validated

Selected-to-Selected handoff investigation: late-active-validated; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-late-active-validated`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 1 parameter records. Removed output: 78,115,123 bytes.

## dex-internal-transitions-late-all

Selected-to-Selected handoff investigation: late-all; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-late-all`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 1 parameter records. Removed output: 726,433,620 bytes.

## dex-internal-transitions-late-cold

Selected-to-Selected handoff investigation: late-cold; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-late-cold`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 61,143,674 bytes.

## dex-internal-transitions-late-focused

Selected-to-Selected handoff investigation: late-focused; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-late-focused`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 1 parameter records. Removed output: 91,758,906 bytes.

## dex-internal-transitions-late-returns

Selected-to-Selected handoff investigation: late-returns; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-late-returns`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 338,243,854 bytes.

## dex-internal-transitions-observer-control

Selected-to-Selected handoff investigation: observer-control; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-observer-control`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 16,552,174 bytes.

## dex-internal-transitions-palette-only

Selected-to-Selected handoff investigation: palette-only; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-palette-only`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 1 source/recipe files, 0 notes; 1 parameter records. Removed output: 800,026,529 bytes.

## dex-internal-transitions-sparse

Selected-to-Selected handoff investigation: sparse; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.

- Basic recipe: `tools.dex_timing.internal_transitions`; inspect with
  `python3 tools/rebuild_historical.py --id dex-internal-transitions-sparse`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 189,868,171 bytes.

## dex-listing-restoration

Listing restoration/cache ownership diagnostic: dex-listing-restoration; skipped/late palettes, LCD-off flashes and presence flags instead of stale transient IDs.

- Basic recipe: `tools.dex_timing.listing_restoration`; inspect with
  `python3 tools/rebuild_historical.py --id dex-listing-restoration`.
- Details: [pokedex_listing_restoration_investigation](../pokedex_listing_restoration_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 132,191,995 bytes.

## dex-listing-restoration-cost

Listing restoration/cache ownership diagnostic: dex-listing-restoration-cost; skipped/late palettes, LCD-off flashes and presence flags instead of stale transient IDs.

- Basic recipe: `tools.dex_timing.listing_restoration`; inspect with
  `python3 tools/rebuild_historical.py --id dex-listing-restoration-cost`.
- Details: [pokedex_listing_restoration_investigation](../pokedex_listing_restoration_investigation.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 26,031,984 bytes.

## dex-listing-restoration-fixed

Listing restoration/cache ownership diagnostic: dex-listing-restoration-fixed; skipped/late palettes, LCD-off flashes and presence flags instead of stale transient IDs.

- Basic recipe: `tools.dex_timing.listing_restoration`; inspect with
  `python3 tools/rebuild_historical.py --id dex-listing-restoration-fixed`.
- Details: [pokedex_listing_restoration_investigation](../pokedex_listing_restoration_investigation.md).
- Preserved: 2 source/recipe files, 0 notes; 150 parameter records. Removed output: 2,039,480,422 bytes.

## dex-scheduler-groudon

Compiled scheduler integration/target-regression work: dex-scheduler-groudon; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-scheduler-groudon`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 93,196,297 bytes.

## dex-scheduler-integrated

Compiled scheduler integration/target-regression work: dex-scheduler-integrated; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-scheduler-integrated`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 3 parameter records. Removed output: 705,201,957 bytes.

## dex-scheduler-reference-20260920

Frozen instrumented scheduler reference, before the production scheduler replacement.

- Basic recipe: `reference`; inspect with
  `python3 tools/rebuild_historical.py --id dex-scheduler-reference-20260920`.
- Details: [dex_scheduler_implementation_preflight](../archived/dex-scheduler/dex_scheduler_implementation_preflight.md).
- Preserved: 869 source/recipe files, 33 notes; 13 parameter records. Removed output: 23,901,050 bytes.

- [battle_anim_commands.md](build-history/dex-scheduler-reference-20260920/docs/battle_anim_commands.md).
- [bugs_and_glitches.md](build-history/dex-scheduler-reference-20260920/docs/bugs_and_glitches.md).
- [credits.md](build-history/dex-scheduler-reference-20260920/docs/credits.md).
- [design_flaws.md](build-history/dex-scheduler-reference-20260920/docs/design_flaws.md).
- [dex_end_to_end_capture_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_end_to_end_capture_results.md).
- [dex_full_replay_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_full_replay_results.md).
- [dex_garchomp_finishing_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_garchomp_finishing_results.md).
- [dex_headroom_synth_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_headroom_synth_results.md).
- [dex_publication_budget_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_publication_budget_results.md).
- [dex_queue_construction_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_queue_construction_results.md).
- [dex_scheduler_implementation_preflight.md](build-history/dex-scheduler-reference-20260920/docs/dex_scheduler_implementation_preflight.md).
- [dex_scheduler_investigation.md](build-history/dex-scheduler-reference-20260920/docs/dex_scheduler_investigation.md).
- [dex_scheduler_policy_experiments.md](build-history/dex-scheduler-reference-20260920/docs/dex_scheduler_policy_experiments.md).
- [dex_steady_publication_results.md](build-history/dex-scheduler-reference-20260920/docs/dex_steady_publication_results.md).
- [dex_timing_boundary_investigation.md](build-history/dex-scheduler-reference-20260920/docs/dex_timing_boundary_investigation.md).
- [dex_timing_capture_dusknoir_bastiodon.md](build-history/dex-scheduler-reference-20260920/docs/dex_timing_capture_dusknoir_bastiodon.md).
- [dex_timing_capture_five_species.md](build-history/dex-scheduler-reference-20260920/docs/dex_timing_capture_five_species.md).
- [dex_timing_model.md](build-history/dex-scheduler-reference-20260920/docs/dex_timing_model.md).
- [event_commands.md](build-history/dex-scheduler-reference-20260920/docs/event_commands.md).
- [index.md](build-history/dex-scheduler-reference-20260920/docs/index.md).
- [map_event_scripts.md](build-history/dex-scheduler-reference-20260920/docs/map_event_scripts.md).
- [map_setup_scripts.md](build-history/dex-scheduler-reference-20260920/docs/map_setup_scripts.md).
- [menus.md](build-history/dex-scheduler-reference-20260920/docs/menus.md).
- [move_effect_commands.md](build-history/dex-scheduler-reference-20260920/docs/move_effect_commands.md).
- [movement_commands.md](build-history/dex-scheduler-reference-20260920/docs/movement_commands.md).
- [music_commands.md](build-history/dex-scheduler-reference-20260920/docs/music_commands.md).
- [palette_color_correction.md](build-history/dex-scheduler-reference-20260920/docs/palette_color_correction.md).
- [pic_animations.md](build-history/dex-scheduler-reference-20260920/docs/pic_animations.md).
- [pokedex_selected_bug_backlog.md](build-history/dex-scheduler-reference-20260920/docs/pokedex_selected_bug_backlog.md).
- [pokedex_vram.md](build-history/dex-scheduler-reference-20260920/docs/pokedex_vram.md).
- [sampled_cries.md](build-history/dex-scheduler-reference-20260920/docs/sampled_cries.md).
- [text_commands.md](build-history/dex-scheduler-reference-20260920/docs/text_commands.md).
- [vc_patch.md](build-history/dex-scheduler-reference-20260920/docs/vc_patch.md).

## dex-selective-mask-ab

Private A/B palette mask: whiten the portrait, footprint and badges; rejected presentation.

- Basic recipe: `overlay`; inspect with
  `python3 tools/rebuild_historical.py --id dex-selective-mask-ab`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 5 source/recipe files, 0 notes; 150 parameter records. Removed output: 3,531,789,559 bytes.

## dex-target-integration-20260920

Compiled scheduler integration/target-regression work: dex-target-integration-20260920; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-target-integration-20260920`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 2 source/recipe files, 0 notes; 2 parameter records. Removed output: 302,422,427 bytes.

## dex-target-regression-20260920

Compiled scheduler integration/target-regression work: dex-target-regression-20260920; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-target-regression-20260920`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 572,968,483 bytes.

## dex-target-regression-spheal-20260920

Compiled scheduler integration/target-regression work: dex-target-regression-spheal-20260920; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-target-regression-spheal-20260920`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 95,893,622 bytes.

## dex-timing

Host timing calibration/boundary evidence: dex-timing; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 3 notes; 1 parameter records. Removed output: 60,965,235 bytes.

- [calibration-captures-2026-09-19.md](build-history/dex-timing/calibration-captures-2026-09-19.md).
- [sameboy_capture.md](build-history/dex-timing/sameboy_capture.md).
- [summary.md](build-history/dex-timing/summary.md).

## dex-timing-additional-actual-states

Compiled scheduler integration/target-regression work: dex-timing-additional-actual-states; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.

- Basic recipe: `tools.dex_timing.target_regression`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-additional-actual-states`.
- Details: [dex_target_regression_results](../archived/dex-scheduler/dex_target_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 7 parameter records. Removed output: 209,646,954 bytes.

## dex-timing-budget-admit

Host-only upload/publication admission experiment: admit; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-admit`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 48 parameter records. Removed output: 121,866,441 bytes.

## dex-timing-budget-admit149

Host-only upload/publication admission experiment: admit149; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-admit149`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 48 parameter records. Removed output: 121,824,027 bytes.

## dex-timing-budget-bounds.json

Host-only upload/publication admission experiment: bounds.json; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-bounds.json`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 35,584 bytes.

## dex-timing-budget-final-admission

Host-only upload/publication admission experiment: final-admission; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-admission`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 48 parameter records. Removed output: 122,228,029 bytes.

## dex-timing-budget-final-conservative

Host-only upload/publication admission experiment: final-conservative; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-conservative`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 16 parameter records. Removed output: 62,372,023 bytes.

## dex-timing-budget-final-controls

Host-only upload/publication admission experiment: final-controls; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-controls`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 18 parameter records. Removed output: 45,141,561 bytes.

## dex-timing-budget-final-costs

Host-only upload/publication admission experiment: final-costs; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-costs`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 144 parameter records. Removed output: 366,455,033 bytes.

## dex-timing-budget-final-dense

Host-only upload/publication admission experiment: final-dense; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-dense`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 488,582,474 bytes.

## dex-timing-budget-final-smoke

Host-only upload/publication admission experiment: final-smoke; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-final-smoke`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 1,773,505 bytes.

## dex-timing-budget-quiet

Host-only upload/publication admission experiment: quiet; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-quiet`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 9 parameter records. Removed output: 22,838,614 bytes.

## dex-timing-budget-quiet-dense

Host-only upload/publication admission experiment: quiet-dense; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-quiet-dense`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 150 parameter records. Removed output: 486,966,462 bytes.

## dex-timing-budget-quiet-phases

Host-only upload/publication admission experiment: quiet-phases; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-quiet-phases`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 48 parameter records. Removed output: 121,725,746 bytes.

## dex-timing-budget-windows

Host-only upload/publication admission experiment: windows; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.

- Basic recipe: `tools.dex_timing.budget_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-budget-windows`.
- Details: [dex_publication_budget_results](../archived/dex-scheduler/dex_publication_budget_results.md).
- Preserved: 0 source/recipe files, 0 notes; 12 parameter records. Removed output: 30,566,708 bytes.

## dex-timing-expanded-owner

Host timing calibration/boundary evidence: dex-timing-expanded-owner; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-expanded-owner`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 6 notes; 5 parameter records. Removed output: 7,452,670 bytes.

- [followup.md](build-history/dex-timing-expanded-owner/bastiodon/followup.md).
- [followup.md](build-history/dex-timing-expanded-owner/dusknoir/followup.md).
- [followup.md](build-history/dex-timing-expanded-owner/luxray-regression/followup.md).
- [sameboy_capture.md](build-history/dex-timing-expanded-owner/sameboy_capture.md).
- [summary.md](build-history/dex-timing-expanded-owner/summary.md).
- [followup.md](build-history/dex-timing-expanded-owner/weavile-regression/followup.md).

## dex-timing-finish-actual-final

Finishing-upload experiment: actual-final; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-actual-final`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 74,639,700 bytes.

## dex-timing-finish-actual-initial

Finishing-upload experiment: actual-initial; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-actual-initial`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 74,481,088 bytes.

## dex-timing-finish-actual-phase

Finishing-upload experiment: actual-phase; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-actual-phase`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 397,540,170 bytes.

## dex-timing-finish-controls

Finishing-upload experiment: controls; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-controls`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 297,531,118 bytes.

## dex-timing-finish-costs-validated

Finishing-upload experiment: costs-validated; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-costs-validated`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 298,304,619 bytes.

## dex-timing-finish-drained

Finishing-upload experiment: drained; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-drained`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 24,797,885 bytes.

## dex-timing-finish-early-controls

Finishing-upload experiment: early-controls; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-early-controls`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 22,919,198 bytes.

## dex-timing-finish-final-costs

Finishing-upload experiment: final-costs; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-final-costs`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 297,856,792 bytes.

## dex-timing-finish-initial

Finishing-upload experiment: initial; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-initial`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 5,798,704 bytes.

## dex-timing-finish-phase-validated

Finishing-upload experiment: phase-validated; complete a ready stage only inside the validated timer/publication reserve.

- Basic recipe: `tools.dex_timing.finish_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-finish-phase-validated`.
- Details: [dex_garchomp_finishing_results](../archived/dex-scheduler/dex_garchomp_finishing_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 398,163,206 bytes.

## dex-timing-five-species

Host timing calibration/boundary evidence: dex-timing-five-species; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-five-species`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 7 notes; 6 parameter records. Removed output: 10,472,111 bytes.

- [followup.md](build-history/dex-timing-five-species/garchomp/followup.md).
- [followup.md](build-history/dex-timing-five-species/kyogre/followup.md).
- [followup.md](build-history/dex-timing-five-species/metagross/followup.md).
- [followup.md](build-history/dex-timing-five-species/rampardos/followup.md).
- [followup.md](build-history/dex-timing-five-species/rayquaza/followup.md).
- [sameboy_capture.md](build-history/dex-timing-five-species/sameboy_capture.md).
- [summary.md](build-history/dex-timing-five-species/summary.md).

## dex-timing-gather-costs

Gather/queue optimization and finishing-headroom experiment: dex-timing-gather-costs; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-gather-costs`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 326,554,772 bytes.

## dex-timing-gather-first

Gather/queue optimization and finishing-headroom experiment: dex-timing-gather-first; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-gather-first`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 8,201,219 bytes.

## dex-timing-gather-garchomp-fine

Gather/queue optimization and finishing-headroom experiment: dex-timing-gather-garchomp-fine; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-gather-garchomp-fine`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 124,153,064 bytes.

## dex-timing-gather-phases

Gather/queue optimization and finishing-headroom experiment: dex-timing-gather-phases; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-gather-phases`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 400,279,722 bytes.

## dex-timing-gather-reserve

Gather/queue optimization and finishing-headroom experiment: dex-timing-gather-reserve; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-gather-reserve`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 801,067,898 bytes.

## dex-timing-headroom-final

Gather/queue optimization and finishing-headroom experiment: dex-timing-headroom-final; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-headroom-final`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 493,676,844 bytes.

## dex-timing-headroom-large-reserve

Gather/queue optimization and finishing-headroom experiment: dex-timing-headroom-large-reserve; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-headroom-large-reserve`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 50,081,204 bytes.

## dex-timing-headroom-reserve8k

Gather/queue optimization and finishing-headroom experiment: dex-timing-headroom-reserve8k; ordered source tiles, unrolled map construction and larger reserves.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-headroom-reserve8k`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 855,311,057 bytes.

## dex-timing-implementation-preflight

Assembled cost-only production-policy draft and decision/admission contracts; not an end-to-end game build.

- Basic recipe: `tools.dex_timing.implementation_preflight`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-implementation-preflight`.
- Details: [dex_scheduler_implementation_preflight](../archived/dex-scheduler/dex_scheduler_implementation_preflight.md).
- Preserved: 2 source/recipe files, 0 notes; 1 parameter records. Removed output: 2,658,445 bytes.

## dex-timing-lcd

Host timing calibration/boundary evidence: dex-timing-lcd; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-lcd`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 1 source/recipe files, 5 notes; 2 parameter records. Removed output: 1,432,456 bytes.

- [comparison.md](build-history/dex-timing-lcd/comparison.md).
- [sameboy_capture.md](build-history/dex-timing-lcd/sameboy_capture.md).
- [summary.md](build-history/dex-timing-lcd/summary.md).
- [weavile-followup.md](build-history/dex-timing-lcd/weavile-followup.md).
- [weavile_followup.md](build-history/dex-timing-lcd/weavile_followup.md).

## dex-timing-lcd-all

Host timing calibration/boundary evidence: dex-timing-lcd-all; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-lcd-all`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 2 notes; 1 parameter records. Removed output: 83,012,097 bytes.

- [sameboy_capture.md](build-history/dex-timing-lcd-all/sameboy_capture.md).
- [summary.md](build-history/dex-timing-lcd-all/summary.md).

## dex-timing-linked-owner

Host timing calibration/boundary evidence: dex-timing-linked-owner; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-linked-owner`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 5 notes; 3 parameter records. Removed output: 3,924,924 bytes.

- [comparison.md](build-history/dex-timing-linked-owner/comparison.md).
- [followup.md](build-history/dex-timing-linked-owner/followup.md).
- [luxray_followup.md](build-history/dex-timing-linked-owner/luxray_followup.md).
- [sameboy_capture.md](build-history/dex-timing-linked-owner/sameboy_capture.md).
- [summary.md](build-history/dex-timing-linked-owner/summary.md).

## dex-timing-linked-owner-all

Host timing calibration/boundary evidence: dex-timing-linked-owner-all; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-linked-owner-all`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 2 notes; 1 parameter records. Removed output: 673,315,975 bytes.

- [sameboy_capture.md](build-history/dex-timing-linked-owner-all/sameboy_capture.md).
- [summary.md](build-history/dex-timing-linked-owner-all/summary.md).

## dex-timing-luxray-owner

Host timing calibration/boundary evidence: dex-timing-luxray-owner; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-luxray-owner`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 4 notes; 3 parameter records. Removed output: 2,889,754 bytes.

- [followup.md](build-history/dex-timing-luxray-owner/followup.md).
- [sameboy_capture.md](build-history/dex-timing-luxray-owner/sameboy_capture.md).
- [summary.md](build-history/dex-timing-luxray-owner/summary.md).
- [followup.md](build-history/dex-timing-luxray-owner/weavile-regression/followup.md).

## dex-timing-owner

Host timing calibration/boundary evidence: dex-timing-owner; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-owner`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 2 notes; 1 parameter records. Removed output: 1,819,345 bytes.

- [sameboy_capture.md](build-history/dex-timing-owner/sameboy_capture.md).
- [summary.md](build-history/dex-timing-owner/summary.md).

## dex-timing-owner-all

Host timing calibration/boundary evidence: dex-timing-owner-all; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-owner-all`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 2 notes; 1 parameter records. Removed output: 673,315,769 bytes.

- [sameboy_capture.md](build-history/dex-timing-owner-all/sameboy_capture.md).
- [summary.md](build-history/dex-timing-owner-all/summary.md).

## dex-timing-owner-selected

Host timing calibration/boundary evidence: dex-timing-owner-selected; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-owner-selected`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 4 notes; 3 parameter records. Removed output: 3,694,737 bytes.

- [comparison.md](build-history/dex-timing-owner-selected/comparison.md).
- [followup.md](build-history/dex-timing-owner-selected/followup.md).
- [sameboy_capture.md](build-history/dex-timing-owner-selected/sameboy_capture.md).
- [summary.md](build-history/dex-timing-owner-selected/summary.md).

## dex-timing-policies

Host-only completion-ledger policy experiment: ; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 18 parameter records. Removed output: 38,926,184 bytes.

## dex-timing-policies-cost-sweep

Host-only completion-ledger policy experiment: cost-sweep; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-cost-sweep`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 6 parameter records. Removed output: 57,522,437 bytes.

## dex-timing-policies-final

Host-only completion-ledger policy experiment: final; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-final`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 24 parameter records. Removed output: 55,724,990 bytes.

## dex-timing-policies-initial

Host-only completion-ledger policy experiment: initial; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-initial`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 15 parameter records. Removed output: 30,640,939 bytes.

## dex-timing-policies-order

Host-only completion-ledger policy experiment: order; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-order`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 6 parameter records. Removed output: 13,988,038 bytes.

## dex-timing-policies-phases

Host-only completion-ledger policy experiment: phases; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-phases`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 48 parameter records. Removed output: 121,617,046 bytes.

## dex-timing-policies-sensitivity

Host-only completion-ledger policy experiment: sensitivity; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-sensitivity`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 3 parameter records. Removed output: 19,516,343 bytes.

## dex-timing-policies-tail

Host-only completion-ledger policy experiment: tail; compare producer-clock, readiness, early work and bounded tail work.

- Basic recipe: `tools.dex_timing.scheduler_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-policies-tail`.
- Details: [dex_scheduler_policy_experiments](../archived/dex-scheduler/dex_scheduler_policy_experiments.md).
- Preserved: 0 source/recipe files, 0 notes; 3 parameter records. Removed output: 22,167,543 bytes.

## dex-timing-queue-costs

Exact map-queue assembly cost experiment: costs; native, row-unrolled and tile-unrolled alternatives.

- Basic recipe: `tools.dex_timing.queue_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-queue-costs`.
- Details: [dex_queue_construction_results](../archived/dex-scheduler/dex_queue_construction_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 298,958,686 bytes.

## dex-timing-queue-garchomp-combined

Exact map-queue assembly cost experiment: garchomp-combined; native, row-unrolled and tile-unrolled alternatives.

- Basic recipe: `tools.dex_timing.queue_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-queue-garchomp-combined`.
- Details: [dex_queue_construction_results](../archived/dex-scheduler/dex_queue_construction_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 123,564,065 bytes.

## dex-timing-queue-garchomp-costs

Exact map-queue assembly cost experiment: garchomp-costs; native, row-unrolled and tile-unrolled alternatives.

- Basic recipe: `tools.dex_timing.queue_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-queue-garchomp-costs`.
- Details: [dex_queue_construction_results](../archived/dex-scheduler/dex_queue_construction_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 30,987,892 bytes.

## dex-timing-queue-phase

Exact map-queue assembly cost experiment: phase; native, row-unrolled and tile-unrolled alternatives.

- Basic recipe: `tools.dex_timing.queue_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-queue-phase`.
- Details: [dex_queue_construction_results](../archived/dex-scheduler/dex_queue_construction_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 398,910,631 bytes.

## dex-timing-smoke

Host timing calibration/boundary evidence: dex-timing-smoke; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-smoke`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 1 notes; 1 parameter records. Removed output: 587,865 bytes.

- [summary.md](build-history/dex-timing-smoke/summary.md).

## dex-timing-steady-broad-phases

Steady-state recovery experiment: broad-phases; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-broad-phases`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 302,731,840 bytes.

## dex-timing-steady-broader

Steady-state recovery experiment: broader; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-broader`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 26,332,337 bytes.

## dex-timing-steady-controls

Steady-state recovery experiment: controls; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-controls`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 26,342,764 bytes.

## dex-timing-steady-costs

Steady-state recovery experiment: costs; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-costs`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 353,795,126 bytes.

## dex-timing-steady-dense

Steady-state recovery experiment: dense; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-dense`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 472,117,514 bytes.

## dex-timing-steady-final-dense

Steady-state recovery experiment: final-dense; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-final-dense`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 472,117,514 bytes.

## dex-timing-steady-final-recovery

Steady-state recovery experiment: final-recovery; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-final-recovery`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 36,924,877 bytes.

## dex-timing-steady-recovery

Steady-state recovery experiment: recovery; budgeted publication and return-to-owner wait behavior.

- Basic recipe: `tools.dex_timing.recovery_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-steady-recovery`.
- Details: [dex_steady_publication_results](../archived/dex-scheduler/dex_steady_publication_results.md).
- Preserved: 0 source/recipe files, 0 notes; 2 parameter records. Removed output: 29,555,508 bytes.

## dex-timing-strict

Host timing calibration/boundary evidence: dex-timing-strict; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-strict`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 2 notes; 1 parameter records. Removed output: 67,050 bytes.

- [sameboy_capture.md](build-history/dex-timing-strict/sameboy_capture.md).
- [summary.md](build-history/dex-timing-strict/summary.md).

## dex-timing-synth-baseline

Synthesized-cry controls for the proposed shared-clock producer and finishing reserve.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-synth-baseline`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 20,159,260 bytes.

## dex-timing-synth-phases

Synthesized-cry controls for the proposed shared-clock producer and finishing reserve.

- Basic recipe: `tools.dex_timing.gather_experiment`; inspect with
  `python3 tools/rebuild_historical.py --id dex-timing-synth-phases`.
- Details: [dex_headroom_synth_results](../archived/dex-scheduler/dex_headroom_synth_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 69,783,561 bytes.

## luxray-actual-state-comparison.json

Host timing calibration/boundary evidence: luxray-actual-state-comparison.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-actual-state-comparison.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 252,024 bytes.

## luxray-actual-state-comparison.memory.bin

Host timing calibration/boundary evidence: luxray-actual-state-comparison.memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-actual-state-comparison.memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## luxray-actual-state-comparison.trace.txt

Host timing calibration/boundary evidence: luxray-actual-state-comparison.trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-actual-state-comparison.trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 7,596,649 bytes.

## luxray-core-fixture.bin

Host timing calibration/boundary evidence: luxray-core-fixture.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-core-fixture.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## luxray-core-instruction-comparison.json

Host timing calibration/boundary evidence: luxray-core-instruction-comparison.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-core-instruction-comparison.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 20,318 bytes.

## luxray-core-sweep.json

Host timing calibration/boundary evidence: luxray-core-sweep.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-core-sweep.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 4,508,286 bytes.

## luxray-core-trace.txt

Host timing calibration/boundary evidence: luxray-core-trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-core-trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 7,596,689 bytes.

## luxray-exact-boundary.json

Host timing calibration/boundary evidence: luxray-exact-boundary.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-exact-boundary.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 1,969 bytes.

## luxray-exact-halt-boundary.json

Host timing calibration/boundary evidence: luxray-exact-halt-boundary.json; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-exact-halt-boundary.json`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 1,974 bytes.

## luxray-save-state-core-trace.txt

Host timing calibration/boundary evidence: luxray-save-state-core-trace.txt; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-save-state-core-trace.txt`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 7,596,649 bytes.

## luxray-state-memory.bin

Host timing calibration/boundary evidence: luxray-state-memory.bin; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.

- Basic recipe: `tools/verify_dex_timing.py`; inspect with
  `python3 tools/rebuild_historical.py --id luxray-state-memory.bin`.
- Details: [dex_timing_model](../archived/dex-scheduler/dex_timing_model_history.md).
- Preserved: 0 source/recipe files, 0 notes; 0 parameter records. Removed output: 114,760 bytes.

## new-dex-entry-catches

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-catches; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-catches`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 9 source/recipe files, 0 notes; 2 parameter records. Removed output: 31,165,697 bytes.

## new-dex-entry-commit-cleanup

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-commit-cleanup; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-commit-cleanup`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 2 source/recipe files, 0 notes; 1 parameter records. Removed output: 21,210,138 bytes.

## new-dex-entry-copy-integration

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-copy-integration; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-copy-integration`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 4 parameter records. Removed output: 39,479,611 bytes.

## new-dex-entry-expanded

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-expanded; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-expanded`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 2 source/recipe files, 0 notes; 2 parameter records. Removed output: 34,441,701 bytes.

## new-dex-entry-integration

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-integration; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-integration`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 2 source/recipe files, 0 notes; 11 parameter records. Removed output: 69,067,986 bytes.

## new-dex-entry-master-ball-restored

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-master-ball-restored; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-master-ball-restored`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 2 source/recipe files, 0 notes; 1 parameter records. Removed output: 34,301,696 bytes.

## new-dex-entry-master-ball-restored-expanded

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-master-ball-restored-expanded; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-master-ball-restored-expanded`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 6,010,721 bytes.

## new-dex-entry-page2-integration

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-page2-integration; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-page2-integration`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 12 parameter records. Removed output: 110,287,594 bytes.

## new-dex-entry-sweep

New Dex Entry input-timing/species/phase sweep: new-dex-entry-sweep; uninterrupted, A, B and A+B interruption plus exact publication and cry completion.

- Basic recipe: `tools.dex_timing.new_entry_sweep`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-sweep`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 14,895,956 bytes.

## new-dex-entry-sweep-final

New Dex Entry input-timing/species/phase sweep: new-dex-entry-sweep-final; uninterrupted, A, B and A+B interruption plus exact publication and cry completion.

- Basic recipe: `tools.dex_timing.new_entry_sweep`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-sweep-final`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 15,313,657 bytes.

## new-dex-entry-sweep-smoke

New Dex Entry input-timing/species/phase sweep: new-dex-entry-sweep-smoke; uninterrupted, A, B and A+B interruption plus exact publication and cry completion.

- Basic recipe: `tools.dex_timing.new_entry_sweep`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-sweep-smoke`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 3,121,808 bytes.

## new-dex-entry-sweep-verified

New Dex Entry input-timing/species/phase sweep: new-dex-entry-sweep-verified; uninterrupted, A, B and A+B interruption plus exact publication and cry completion.

- Basic recipe: `tools.dex_timing.new_entry_sweep`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-sweep-verified`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 0 source/recipe files, 0 notes; 1 parameter records. Removed output: 11,807,421 bytes.

## new-dex-entry-text-publication

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-dex-entry-text-publication; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-entry-text-publication`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 8 source/recipe files, 0 notes; 6 parameter records. Removed output: 110,399,706 bytes.

## new-dex-save-setup

Historical backed-up caught-flag test setup; never run the old live-save editing script automatically.

- Basic recipe: `manual-only`; inspect with
  `python3 tools/rebuild_historical.py --id new-dex-save-setup`.
- Details: [dex_new_entry_testing](../dex_new_entry_testing.md).
- Preserved: 1 source/recipe files, 0 notes; 2 parameter records. Removed output: 11,325 bytes.

## new-entry-page-experiment

New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: new-entry-page-experiment; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.

- Basic recipe: `tools.dex_timing.new_entry`; inspect with
  `python3 tools/rebuild_historical.py --id new-entry-page-experiment`.
- Details: [new_dex_entry_regression_results](../new_dex_entry_regression_results.md).
- Preserved: 3 source/recipe files, 0 notes; 8 parameter records. Removed output: 164,819,199 bytes.

## pack-transition-review

Pack between-pouch transition comparison used as a presentation/ownership reference for Dex paging.

- Basic recipe: `archived-script`; inspect with
  `python3 tools/rebuild_historical.py --id pack-transition-review`.
- Details: [pokedex_internal_transition_investigation](../pokedex_internal_transition_investigation.md).
- Preserved: 2 source/recipe files, 0 notes; 1 parameter records. Removed output: 34,774,895 bytes.
