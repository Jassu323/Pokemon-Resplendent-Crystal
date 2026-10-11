# Pokedex Listing Without Idle Animation Warming

2026-10-11. Private prototype for `DEX-PERF-03`, based on committed production
`7d97fd111ef5c57f05ff90e9e4acce2ab0679be3` (Moves Dex). Native qualification
is complete; manual review and production promotion remain pending.

## Review Files

- ROM: `build/dex-no-warming-20261011/pokecrystal-dex-no-warming.gbc`
- Matching save: `build/dex-no-warming-20261011/pokecrystal-dex-no-warming.sav`
- All-moves-seen pair: `build/dex-no-warming-20261011/all-seen-review/pokecrystal-dex-no-warming.{gbc,sav}`
- Unmodified production comparison: `build/dex-no-warming-20261011/baseline/pokecrystal-dex-no-warming.{gbc,sav}`
- Qualification: `build/dex-no-warming-20261011/no-warming-qualification.json`
- Private source: `build/dex-no-warming-20261011/candidate/`
- Baseline source: `build/dex-no-warming-20261011/baseline/candidate/`

Prototype SHA-256:
`555bd3fbfc396630d8ed88987d705a4fbd153650b5041540b0c8d18128293a1d`.
Production/baseline SHA-256:
`cec8550e793d9c2474982d489baf5460d1f1a301c33e6ca7f520a50683d7eb3c`.
The fresh committed-source baseline rebuild matches production byte-for-byte.

The matching save copies the accepted review battery without changing its
discoveries, party or progression. It has all 373 Pokemon seen/caught, eight
seen moves and the Alphabet Moves preference. The separate all-seen pair has
all 333 moves discovered. These are review fixtures, not player-save updates.

## Scoped Changes

Only four assembly files differ in the private link:

- `engine/pokedex/pokedex.asm`: remove two Listing startup calls and its idle
  producer-service call.
- `engine/pokedex/pokedex_legacy.asm`: remove the equivalent three calls.
- `engine/pokedex/pokedex_animation.asm`: remove two Listing scroll/wrap
  startup calls; retain the shared helpers and Selected scheduler.
- `engine/pokedex/pokedex_popover.asm`: remove one popup-return startup call
  and the bank-switch wrapper that existed solely for that call.

Seven `Pokedex_StartAnimationPrefetch` calls and two
`Pokedex_ServiceAnimationProducer` calls are removed. The helpers are not
globally disabled: Selected initialization still calls them as needed.

The static colored portrait, footprint, visible minisprite grid, icon animation
and on-demand scroll uploads remain. The selected screen's 96-tail-tile startup
runway, complete initial frame, two animation slots, authored timelines,
finishing admission and cry ownership/refill also remain unchanged. The
`pokedex_detail.asm` "warm transition" wording describes retaining an outgoing
screen, not speculative Listing animation work; that path is unchanged.

Preparing the static portrait still arms its deferred-tail bookkeeping. Without
the removed Listing callers, hovering cannot decode/upload that deferred work.
Entering Selected now starts cold regardless of hover duration. No dictionary
storage, shared state or graphics allocation is removed.

The exact resource change is **-58 ROMX bytes**. ROM0, SRAM, WRAM0, WRAMX and
HRAM usage are unchanged; existing RAM symbols retain their addresses. Save
format, gameplay discovery hooks, clock policy and assets are unchanged. Root
production assembly/ROM/symbols/map and retained review batteries are protected.
Only the documentation index and backlog status are intentionally updated.

## Entry Timing

Fresh normal-input SameBoy checkpoints were generated separately for both ROMs
and both Listing presentations. The comparison covers 16 species, four hover
durations and four physical input phases: 512 pairs / 1,024 executions.
Species include heavy dictionaries and sampled cries: Chikorita, Eevee, Ditto,
Unown, Mewtwo, Celebi, Dusknoir, Weavile, Garchomp, Bronzong, Seviper, Spheal,
Groudon, Kyogre, Rayquaza and Metagross.

Times below are median milliseconds from physical A press to the first displayed
complete Selected layout. The final stable UI crop excludes ongoing portrait
animation; authored animation publications and cry timing are audited separately.

| Presentation | Hover Display Frames | Production | No Warming | Median Paired Increase |
| --- | ---: | ---: | ---: | ---: |
| Modern | 0 | 102.96 | 103.36 | 0.45 |
| Modern | 4 | 94.43 | 103.36 | 8.69 |
| Modern | 30 | 77.83 | 103.36 | 17.21 |
| Modern | 120 | 77.83 | 103.36 | 17.21 |
| Legacy | 0 | 101.73 | 102.18 | 0.45 |
| Legacy | 4 | 93.30 | 102.18 | 17.19 |
| Legacy | 30 | 80.74 | 102.18 | 17.20 |
| Legacy | 120 | 76.56 | 102.18 | 17.20 |

The median of paired differences need not equal the difference of aggregate
medians. Immediate-entry changes stay below 0.47 ms. The largest measured
increase is **50.68 ms**, about three display frames, on Spheal. Its largest
absolute candidate entry is **265.82 ms**. Hovering no longer reduces candidate
startup latency. No animation publication or cry deadline regressed.

This is a small absolute startup tradeoff in the measured cases, not a drastic
slowdown. It is also not a claim of zero latency cost or a hardware measurement.
The raw report's `first_visible` lower crop can include continuing Modern
minisprite motion, so that diagnostic is not used as an independent Selected
response-time claim. Timing conclusions use `complete_visible`.

Evidence: `entry-timing/summary.json`, per-case events/logs and four captured
Selected screenshots. `idle-proof/summary.json` independently checks all
373 species in both presentations after 120 display frames of hover: all 746
retain only the static base and perform zero animation decode/upload services.

## Regression Results

All current native suites passed on this ROM with fresh symbol-matched fixtures
and isolated batteries, using at most six workers per suite:

- 4,479 Pokemon Dex fixtures: all species in all three sorts and both Listing
  presentations, cursor reset/cache behavior, navigation/wrapping, popovers,
  visual reveal, sparse/unseen edges, Selected Description/Info/Moves/Area,
  early cancellation/paging, Search/defaults/returns, Modes and Unown.
- 2,238 additional exact playback fixtures: cold entry, internal paging and
  long-hover entry for all 373 species in both presentations. Authored frames,
  timing, full cries and Listing return identities pass.
- Full Moves UI/Search regressions: 1,692 filter cases, ten completion fixtures,
  232 keyboard-direction checks, 1,406 visual checks, 2,686 navigation checks,
  eleven publication transitions, two surrounding Save/Continue roundtrips,
  1,284 form/footer checks and 3,840 naming-animation checks.
- The established 100-move battle campaign: 1,600 runs across both actors,
  four phases and both builds. First requested animation duration matches in
  all 800 pairs.
- 960 sampled-cry captures across 20 species, six contexts, four phases and
  both builds. Sample bytes, playback settings and termination match in all
  480 pairs. The same 32 known warnings occur in each build, with no new ones.
- 1,792 menu input/register contracts and 464 Pack/Apricorn/TM-HM checks.
  Custom-menu pixels, palettes and OAM sets match production.
- 22 paired gameplay scenarios: navigation, purchase, puzzle, fishing, trainer,
  phone, learning, hatching, PC/party catch and Heal/Save. Another 24 transition
  fixtures cover 64 repeat battles, eight learning events and eight whiteouts.
- 21 current host contracts: 15 Selected scheduler checks, including 216,000
  finishing-bound inequalities, plus six no-warming scope/resource/protection
  tests.

There is no unresolved new runtime failure. The older `tools.test_dex_timing`
campaign is not green: its 187 checks produce six failures, sixteen errors and
103 skips on both the fresh production baseline and candidate. Test identities
and messages match exactly. These checks reference retired budget assumptions
and removed trace symbols; they are retained comparison evidence, not current
acceptance. See `historical-host-comparison.json` and the
[host tools guide](dex_timing_model.md).

This scoped trial reruns ordinary Save/Continue and adjacent gameplay checks,
not the previous exhaustive interrupted-save, migration and every-discovery-
source campaign. Those owners are byte-identical. Native emulation is not a
physical-cartridge power-loss test or an exhaustive map-event playthrough.
Manual review remains required before promotion.

## Reproduction

Use a clean committed production checkout, the retained accepted Moves review
fixtures and the existing local SameBoy source/boot dependencies. The builder
requires a fresh private output directory and verifies the rebuilt baseline
against the root ROM; it never relinks production. Generated-artifact naming
aliases let established Moves qualification tools target this ROM.

```sh
PYTHONPATH=tools:. python3 tools/build_dex_no_warming_prototype.py \
  --output build/dex-no-warming-20261011 --jobs 4
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search prepare \
  --output build/dex-no-warming-20261011
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search_dex_regression prepare \
  --output build/dex-no-warming-20261011
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_search_dex_regression prepare \
  --output build/dex-no-warming-20261011/baseline
PYTHONPATH=tools:. python3 -m tools.dex_timing.listing_warming idle \
  --output build/dex-no-warming-20261011 --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.listing_warming timing \
  --output build/dex-no-warming-20261011 --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.listing_warming host \
  --output build/dex-no-warming-20261011
```

Run `moves_search` with `filter`, `ui`, `visual`, `navigation`, `transitions`,
`surrounding`, `polish` and `cursor`. Do not run its historical `qualify` action
against copied fixture manifests: their old protection claims belong to prior
builds. Run `moves_search_dex_regression` with `listings`, `interfaces` and
`selected`; use `search_qualification --source` for normal, `--returns` and
`--defaults` checks. Run `mode_transitions` against `dex-regression/` with
indices `0,8,255,372`, four phases and six workers, then qualify that Dex suite.

Run `performance_regression` separately against fresh Modern and Legacy configs,
with `--suites cold paging warm --expected-double-speed --jobs 6`, writing to
`playback-modern/` and `playback-legacy/`. Run `acquisition_regression` against
the private baseline: `menus` and `audio` first, then `gameplay`, `custom`,
`transitions` and `moves`. Gameplay/transition fixtures depend on the preceding
setup; they cannot be run first. The prior guide's warning about concurrent
tracking/moves battle-fixture recreation still applies.

For the historical host comparison, run `tools.test_dex_timing` against each
private source root using `DEX_TIMING_REFERENCE_ROOT` and retain matching
failure/error/skip identities and messages in `historical-host-comparison.json`.
The dedicated final action, `listing_warming qualify --output ...`, verifies
all expected suite counts, hashes, paired playback/menu/battle evidence, current
host acceptance and the historical comparison. Its report preserves the
intentional index/backlog status-note changes separately from protected inputs.
