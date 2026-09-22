# Pokemon Resplendent Crystal Documentation

Start here for this fork's maintained systems, validation procedures and open
issues. Historical experiments are retained separately so their old build
addresses and proposed fixes are not mistaken for current instructions.

## Current Systems

- [Selected Pokedex animation scheduler](pokedex_animation_scheduler.md): runtime architecture, timing/admission contract, resource costs and adaptation to other owners.
- [New Dex Entry animation scheduler](new_dex_entry_animation_scheduler.md): resident dictionary, exact publication timing, local batch uploader and reusable owner contracts.
- [Pokedex VRAM and scratch ownership](pokedex_vram.md): graphics allocation and memory lifetimes.
- [Sampled cries](sampled_cries.md): codec, asset pipeline, playback/refill behavior and owner-specific limits.
- [Palette color correction](palette_color_correction.md): palette authoring/calibration reference.

## Testing And Open Work

- [Selected scheduler validation](dex_scheduler_validation.md): accepted ROM identity, miss breakpoints, regression suite and deferred cleanup.
- [All-species cold Listing acceptance](dex_cold_listing_results.md): normal-input SameBoy methodology, reproducible setup, results and the known Drapion failure.
- [Host timing tools](dex_timing_model.md): current checks versus historical models, fixtures and limits.
- [New Dex Entry testing](dex_new_entry_testing.md): current miss breakpoints, focused manual checks, eight catch fixtures and headless validation.
- [New Dex Entry input-timing regression](new_dex_entry_regression_results.md): 20-species acceptance, timer-phase stress, the acknowledged Mewtwo text-refresh fix and historical failure evidence.
- [Live Dex and adjacent bug backlog](pokedex_selected_bug_backlog.md): current status, reproductions and deferred investigations.

## Historical Evidence

- [Dex scheduler investigation archive](archived/dex-scheduler/README.md): measurements, failed controls, implementation preflight and older test-build records.
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
