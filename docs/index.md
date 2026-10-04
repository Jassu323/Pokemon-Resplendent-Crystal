# Pokemon Resplendent Crystal Documentation

Start here for this fork's maintained systems, validation procedures and open
issues. Historical experiments are retained separately so their old build
addresses and proposed fixes are not mistaken for current instructions.

## Current Systems

- [Selected Pokedex animation scheduler](pokedex_animation_scheduler.md): runtime architecture, timing/admission contract, resource costs and adaptation to other owners.
- [Selected Pokedex Info pages](pokedex_info.md): stats/evolution pages, build-time glyphs, bounded preparation, OBJ types, palettes, memory budgets and regression/manual checks.
- [New Dex Entry animation scheduler](new_dex_entry_animation_scheduler.md): resident dictionary, exact publication timing, local batch uploader and reusable owner contracts.
- [Pokedex VRAM and scratch ownership](pokedex_vram.md): graphics allocation and memory lifetimes.
- [Sampled cries](sampled_cries.md): codec, asset pipeline, playback/refill behavior and owner-specific limits.
- [Palette color correction](palette_color_correction.md): palette authoring/calibration reference.

## Testing And Open Work

- [Dex instrumentation cleanup](dex_instrumentation_cleanup.md): runtime removal, host-only observers, clean-link regression results and current breakpoints.
- [Selected scheduler validation](dex_scheduler_validation.md): accepted ROM identity, miss breakpoints, regression suite and deferred cleanup.
- [All-species cold Listing acceptance](dex_cold_listing_results.md): normal-input SameBoy methodology, reproducible setup, historical results and category-data regression follow-up.
- [Host timing tools](dex_timing_model.md): current checks versus historical models, fixtures and limits.
- [New Dex Entry testing](dex_new_entry_testing.md): current miss breakpoints, focused manual checks, eight catch fixtures and headless validation.
- [New Dex Entry input-timing regression](new_dex_entry_regression_results.md): 20-species acceptance, timer-phase stress, the acknowledged Mewtwo text-refresh fix and historical failure evidence.
- [Live Dex and adjacent bug backlog](pokedex_selected_bug_backlog.md): current status, reproductions and deferred investigations.
- [Info return and evolution investigation](pokedex_info_return_evolution_investigation.md): transient glyph/cache aliasing, independently verified missing gameplay records, shared buffered pagination for future Moves, fix estimates and regression requirements.
- [Info return relocation preflight](pokedex_info_return_preflight.md): separate test ROM, unchanged outgoing pixels, linked resource costs, paired return latency and full input/playback regressions.
- [Info return committed records acceptance](pokedex_info_return_records_preflight.md): integrated retained-page fix, reused Tower WRAMX, three-way timing comparisons, production regressions and accepted preparation tradeoff.
- [Area integration](pokedex_area.md): accepted vanilla full-screen nest map, exact tab/page return without frontpic/cry replay, owner/palette handoffs, costs, timings, headless regressions and historical build recipe.
- [Listing restoration investigation](pokedex_listing_restoration_investigation.md): normal-input reproductions, skipped/late palette commits, LCD-off cache flashes and scoped fix directions.
- [Historical return and exit revalidation](pokedex_backlog_revalidation.md): current-link results for the four older Listing/exit reports, confirmed viewport/white-mask ordering defect and measured private fix costs.
- [Dex opening and closing optimization story](pokedex_selected_bug_backlog.md#dex-perf-01-optimize-pokedex-opening-and-closing): deferred lifecycle work including the merged `DEX-EXIT-01` shift, timing measurements and regression requirements.
- [Whole-Dex performance optimization story](pokedex_selected_bug_backlog.md#dex-perf-02-profile-and-optimize-the-completed-dex): deferred until Moves, Area and other Dex modes are implemented; profile tab/paging/cache work while preserving exact playback and presentation.
- [Cry ownership investigation](pokedex_cry_ownership_investigation.md): Dex-local cancellation, synth resumption/outgoing exhaustion/header-race fixes, exact resource costs and all-species transition regressions.
- [Internal transition investigation and fix](pokedex_internal_transition_investigation.md): delayed blackout, atomic internal reveal, final-link costs/timing/regressions and historical prototype evidence.
- [Direction change investigation](pokedex_direction_change_investigation.md): held/new-axis conflicts, accepted shared-menu correction, exact costs, 57-state menu regressions and animation/overworld acceptance.
- [Description page transaction](pokedex_description_paging_investigation.md): original A-page corruption diagnosis, accepted bounded lower-text publication, resource costs and automated/manual acceptance.
- [Overworld turning-delay research spike](pokedex_selected_bug_backlog.md#ow-move-01-research-faster-player-turning-without-changing-walking-behavior): Polished Crystal references, timing differences, proposed measurements and scope limits; no overworld change implemented.

## Historical Evidence

- [Dex scheduler investigation archive](archived/dex-scheduler/README.md): measurements, failed controls, implementation preflight and older test-build records.
- [Historical build catalog](archived/build-history.md): each former build/output, preserved recipes, parameter grids, source overrides and safe reconstruction script.
- [Other archived material](archived/README.md): legacy references and artifact policy.

Keep curated findings and reusable tools in the repository. Generated reports,
copied cartridges/saves, emulator states, screenshots, compiled runners and raw
traces belong under the ignored root `build/` directory. A report's local
artifact path is provenance, not a promise that the file ships with the repo.

## Upstream Reference

These guides originated with the [pokecrystal disassembly](https://github.com/pret/pokecrystal).
They document general engine concepts or upstream behavior and may not describe
every customization in this fork. In particular, the upstream bug/design lists
below are not the live fork backlog.

### Scripts

- [Map event scripts](map_event_scripts.md)
- [Event commands](event_commands.md)
- [Movement commands](movement_commands.md)
- [Text commands](text_commands.md)
- [Map setup scripts](map_setup_scripts.md)
- [Battle animation commands](battle_anim_commands.md)
- [Move effect commands](move_effect_commands.md)
- [Music commands](music_commands.md)

### Other References

- [Picture animations](pic_animations.md)
- [Menus](menus.md)
- [Upstream bugs and glitches](bugs_and_glitches.md)
- [Upstream design flaws](design_flaws.md)
- [Credits](credits.md)
- [Legacy Virtual Console patch notes](archived/legacy/vc_patch.md), not a supported fork target.
