# Pokemon Resplendent Crystal Documentation

Start here for this fork's maintained systems, validation procedures and open
issues. Historical experiments are retained separately so their old build
addresses and proposed fixes are not mistaken for current instructions.

## Current Systems

- [Production CPU clock and Dex performance](production_clock_policy.md): double-speed world, normal-speed battle envelope, retained Dex optimizations, generated Area index, audio timer contract, current resource budget and fresh qualification.
- [Selected Pokedex animation scheduler](pokedex_animation_scheduler.md): runtime architecture, timing/admission contract, resource costs and adaptation to other owners.
- [Selected Pokedex Info pages](pokedex_info.md): stats/evolution pages, build-time glyphs, bounded preparation, OBJ types, palettes, memory budgets and regression/manual checks.
- [New Dex Entry animation scheduler](new_dex_entry_animation_scheduler.md): resident dictionary, exact publication timing, local batch uploader and reusable owner contracts.
- [Pokedex VRAM and scratch ownership](pokedex_vram.md): graphics allocation and memory lifetimes.
- [Sampled cries](sampled_cries.md): codec, asset pipeline, playback/refill behavior and owner-specific limits.
- [Palette color correction](palette_color_correction.md): palette authoring/calibration reference.

## Testing And Open Work

- [Normal-speed battle prototype](battle_normal_speed_prototype.md): historical manually accepted trial now promoted byte-for-byte; 100-move comparisons, all-species/UI/gameplay/switch regressions, timer-overhead correction, costs and retained ROM/save/videos.
- [Polished battle animation comparison](polished_battle_animation_comparison.md): fresh upstream native six-move/both-side timing and motion against production and unretimed double speed, retained comparison/audio videos, implementation differences and next-trial recommendation.
- [Expanded private battle retiming](battle_animation_expanded_motion_prototype.md): Surf teardown correction, full 80-move phase/motion review, costs, native regressions, retained comparisons and review-save guide. Not promoted to production.
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
- [Selected-tab performance investigation](pokedex_selected_performance.md): historical current/vanilla timings, separate first-response/completion measurements, Area/Info/Listing candidates, exact costs, rapid-input correction and all-species regressions. Only the later accepted components are promoted; the component-repair return was rejected.
- [Selected performance round two](pokedex_selected_performance_round2.md): whole-Dex double speed, retained Info, bounded active preparation, no eager lookahead, return-history measurements, expanded post-switch audio/New Entry regressions, upstream speed-use audit and hardware qualifications. Private prototype only.
- [Whole game double speed qualification](global_double_speed.md): private global clock policy, double-speed ablations, exact costs, broad menu/gameplay/audio acceptance and the post-catch cancellation correction.
- [Double speed animation measurements](global_double_speed_animation_measurements.md): observed durations for 79 moves on both sides, paired physical-frame/ms differences and multi-stage qualifications. No animation retiming applied.
- [Double speed animation pacing investigation](global_double_speed_animation_pacing.md): primary-effect versus wrapper timing, Dragon Dance, read-only tick/OAM/cost traces, Polished Crystal audit, corrected review saves and proposed pacing options. No production retiming applied.
- [Battle animation phase pacing prototype](battle_animation_phase_pacing_prototype.md): private selected-move gate, exact costs, paired timings, rendered-state caveats, common-charge target limitations, full regressions and three-arm manual review files. Production remains unchanged.
- [Targeted battle motion prototype](battle_animation_targeted_motion_prototype.md): production per-object/phase references, continuous local motion and charge rates instead of a shared gate, both Caustic sound sequences, exact costs, final regressions, known presentation differences and a separate manual-review ROM/save.
- [Thunderbolt three-way comparison](thunderbolt_three_way_comparison.md): retail-matching Emerald/headless mGBA versus production and accepted double-speed Crystal; native both-side captures, exact script/visible-pose timings, OAM/affine traces, observer parity and synchronized review videos. No animation retiming applied.
- [Whole-Dex performance optimization story](pokedex_selected_bug_backlog.md#dex-perf-02-profile-and-optimize-the-completed-dex): accepted Selected-tab performance is integrated and freshly qualified; additional modes and entry/exit work remain deferred. Preserve exact playback and presentation while optimizing tab/paging/cache work.
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
