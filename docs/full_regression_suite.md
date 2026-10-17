# Full Regression Suite

Maintained reference: 2026-10-17. This documents the campaigns actually run for
the Dex branch, including the isolated Type Matchups prototypes. It is a
reusable test specification and local execution runbook, not a claim that
every possible game state has been exhaustively tested.

The [species-information prototype](pokedex_species_information_prototype.md)
adds a Dex-only multipage addendum. Description readers and registration
catalogs must enumerate actual counts, not assume two pages. Its independent
source/offset controls, all-page captures, P.3/P.4 Area returns and rapid-Desc
tests are required for future Description changes. Keep the accepted text
sources and the independent expectations in `tools/regression_fixtures/`;
restore the small assessment input under `build/` for a run. A matching runtime/oracle alone
does not prove that an entry's final page exists. The initial October 16 result
was Dex-only. Its subsequent [full follow-up](pokedex_species_information_prototype.md#full-regression-follow-up)
reruns the broader standard and supplementary campaigns, **excluding Battle
Tower**, on the exact reviewed link. It keeps the baseline-matching rapid-input
exception and real phase-sensitive timing changes explicit rather than claiming
every raw test is clean.

The October 17 [combined responsiveness qualification](pokedex_responsiveness_prototype.md)
repeats the full suite excluding Battle Tower on the final accepted link,
including the full Description/registration coverage above. Mov uses twelve
bounded slices and wrap-aware admission; Info READY uses cutoff 108. Keep the
linked cutoff guard, independent 36-state staging budget and exact interrupt
body comparisons: do not change a hard-coded test expectation without measuring
the new work. The reviewed build is now production-integrated byte-for-byte;
its promotion receipt distinguishes fresh root checks from the retained full
qualification and the user's manual timing acceptance.

The registration coverage plan must sum each catalog row's real
`description_pages` for both page coverage and unique committed B/End exits.
Retain the two-page default only for older catalogs without that field. The
two coverage-plan unit controls distinguish three/four-page rows from that
legacy default; the native exit sweep must still visit the actual later pages.

The final October 17 [build retirement](pokedex_build_retirement.md) supersedes
the earlier conservative cleanup. The completed egg prototype, historical
source copies, review cartridges/saves, audio/video/images, reports and run
outputs are discarded with approval. Only the strictly required fixture inputs
are preserved in the compact portable bundle under `tools/regression_fixtures/`.
The component guides and measured qualifications remain in `docs/`; old build
links are provenance, not retained downloads. Production and the main battery
are unchanged. Generate fresh matching-link evidence for future campaigns.

Battle Tower coverage is a separate, independently runnable addendum:
[Battle Tower Regression Suite](battle_tower_regression_suite.md). Its
[findings](battle_tower_testing_findings.md) include existing prize-pocket
failures. Do not fold those into a claim that the Tower is clean merely because
the standard Dex campaign passes.

The October 14 cleanup run is summarized in
[Cleanup Implementation](pokedex_cleanup_implementation.md). It removes the
test-only `MoveDiscovery_CheckIndex` API; current exhaustive persistence checks
use retained `MoveDiscovery_MarkIndex`, `MoveDiscovery_BitAddress`, and the
production Moves UI seen-query path instead. No index/bank/register coverage
is skipped. Slowpoke checks compare the linked 48-tile prefix with the exact
archived original in `gfx/archived/pokedex/`; do not expect retired trailing
cursor tiles to remain in VRAM. Shared-arrow results fixtures must explicitly
seed seen moves and assert a nonzero result count. Type fixtures must explicitly
unlock Unown when testing that return menu. These are declared fixture changes,
not altered game completion flags.

The subsequent [Backlog Reconciliation](pokedex_backlog_reconciliation.md)
documents focused current-link replays for badge cancellation, tab latency,
Listing return frames, caught markers and rejected palette writes. That audit
does not replace this full suite or turn latency findings into correctness passes.

The nine-byte [Info-to-Description correction](pokedex_info_description_latency_investigation.md)
also needs an active internal-paging test. Settled tab navigation alone does
not expose its former starvation. Preserve the atomic portrait pending-flag
contract documented beside both dispatcher and publisher; source checks are
additional controls, not substitutes for native timing/visual tests.
Its fresh October 14 full campaign is retained at
`build/dex-description-fix-integration-20261014/`, including all standard phases,
all-move renderer/native comparisons, six-model display/return checks and the
supplementary Selected/New Entry/lifecycle/audio qualifications. The exact
production ROM hash, costs, results and preserved harness corrections are in
the linked investigation's Production Integration section.

For the final Type prototype results and ROM hashes, see
[Type Mode 7 Comparison](pokedex_type_mode7_comparison.md). For the critical
interrupt rule, see [Battle Animation Interrupt Timing Contract](battle_animation_interrupt_timing_contract.md).

## 1. Testing Principles

The later October 14 [Unown transition qualification](pokedex_unown_transition_regression.md)
reuses this full suite for the private 51-byte fast-map candidate. Its dedicated
`unown_transition_campaign` driver freezes both links, requires exact rebuilds,
runs standard/supplementary phases, and gates finalization on matching binary
identities, case counts, negative controls and unchanged artwork/RAM. The
report records the corrected artifact-audit sidecar filter and unchanged
production exceptions. The qualification phase left production unchanged;
after manual acceptance, a separate production rebuild matched the qualified
ROM byte-for-byte. Its fresh root-link smoke checks and receipt are documented
in [Production Integration](pokedex_unown_transition_regression.md#production-integration).

1. Freeze a production baseline and a candidate. Compare fresh evidence for
   those exact binaries, with matching symbols, maps, and source trees.
2. Do not modify the player's battery or production ROM. All fixtures, saves,
   compiled observers, and generated reports live in private test directories.
3. Separate normal-button integration tests from synthetic fixtures, direct
   helper calls, and direct animation-renderer calls. Each answers a different
   question; one cannot replace the others.
4. Test actual displayed frames and physical time. An animation can return and
   perform the same logical updates while taking much longer on screen.
5. Preserve failures, timeouts, skipped cases, baseline exceptions, and retries.
   A missing report or incomplete case set is not a pass.
6. Use independent expectations where possible: canonical order/data,
   separately transcribed chart values, known graphics, and a frozen baseline.
   Generating both implementation and oracle from the same erroneous result
   would make the test circular.
7. Rebuild/recreate fixtures after a new link. Saved CPU state contains PCs,
   banked addresses, and caller state and cannot safely be reused across ROMs.
8. Include relevant recordings and captures with scoping/prototype assessments
   for manual verification: labeled production/candidate audio A/B, screenshots
   or short videos. Keep real-time playback separate from slowed diagnostics;
   passing register/content checks is not listening or visual approval.

The focused successful-capture clock qualification is documented in
[Gotcha Boundary Prototype Results](pokedex_new_entry_description_scope.md#gotcha-boundary-prototype-results).
It independently exercises catch EXP, learning, naming, post-battle evolution,
overworld return and following-battle ownership, with RGB/publication controls
and paired recordings. It supplements, rather than replaces, the global suite.

Counts below describe the October 12 catalog: **373 species, 333 moves,
18 types, and 122 music entries including silence**. Several counts overlap,
and some are pairs or nested assertions rather than complete scenarios. Do not
add them into a misleading grand total.

## 2. Environment And Required Inputs

Commands are run from the repository root. The local native tools require:

- Python 3, Pillow, and the repository's Python modules.
- RGBDS and the normal Makefile toolchain for fresh private ROM builds.
- Clang with C11 support.
- SameBoy source at `~/Documents/GitHub/SameBoy`; runners compile its native
  core together with read-only observers or explicit fixture helpers.
- CGB boot ROM at `/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin`.
- Sufficient disk space for two source/build trees, copied batteries, native
  checkpoints, screenshots, and compressed event traces.

Record Python/RGBDS/Clang versions and the SameBoy revision with the campaign.
Changing emulator/toolchain versions deserves a new baseline comparison rather
than mixing old and new observer results.

```sh
export PYTHONPATH=tools:.
python3 --version
rgbasm --version
clang --version
git -C ~/Documents/GitHub/SameBoy rev-parse HEAD
```

### Frozen Game Inputs

The established `type_full_regression` adapter expects a source directory with:

```text
candidate/                         matching source and linked build
pokecrystal-dex-types.gbc           immutable candidate ROM
pokecrystal-dex-types.sym           matching symbols
pokecrystal-dex-types.map           matching allocation map
pokecrystal-dex-types.sav           copied review battery
rollback-source.tar                source archive matching production
```

Conventional production `pokecrystal.gbc/.sym/.map` must also be present at the
repository root. Preparation copies these frozen baseline files into the
baseline source directory as well as the expected test aliases. This matters
for linked host tests: without those conventional filenames, a baseline may
skip tests or produce file-not-found errors while the candidate runs them.

The preparation manifest records SHA-256 values and protects production files.
Never pair an old `.sym` with a newly linked ROM. Never treat an old JSON report
as acceptance for a new ROM simply because the filename is unchanged.

### Retained Fixture Dependencies

The current local adapter uses a source-controlled compact fixture bundle,
not loose historical build trees. Before a campaign, restore and verify it:

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures verify
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures restore --compile-controls
```

It recreates only these historical-path fixture definitions under `build/`:

- `build/dex-moves-search-final-review-20261011/`: `all-seen-tests.sav`,
  `legacy-input.sav`, `sort-manifest.json`, and `moves-mode-manifest.json`.
- The sort-memory source referenced by that Moves manifest, including its
  `battle-review/` donor battery and matching manifest.
- `build/dex-unown-black-20261011/unown-manifest.json` and the old ROM/symbol/save
  paths referenced for the Unown negative controls.
- The one known-bad Moves keyboard control, pre-relocation numeric-cost
  reference and independent description/footprint expectations.

Fixture manifests provide data/setup definitions, **not historical pass
evidence**. The current campaign recreates cores, checkpoints, and assertions
against the new link. Observers are rebuilt from current tools, not retained
machine executables. The bundle remaps checkout paths and refuses conflicting
existing files. Its isolated safety controls are in
`tools/test_regression_fixtures.py` (five controls, including concurrent restore).

The October 12 integration uses `--baseline-source` on `prepare` to select frozen
pre-integration ROM/symbol/map files while protecting the newly integrated root
ROM. The source archive must still match that selected baseline. Private source
snapshots also need converted graphics sidecars for native visual checks; the
integration snapshot copies current `gfx/`, including all Unown forms. A normal
ROM build alone does not necessarily generate every visual-test sidecar.
Host snapshots also require the generated `dex-area-assets`, `dex-info-assets`,
`dex-moves-assets`, `dex-moves-mode-assets` and `dex-sort-assets` directories under
their own `build/`. Missing fixture tables are setup errors, not game regressions;
correct the snapshot and rerun the affected phases before acceptance.
Keep each snapshot's matching generated tables. A pre-ancestor baseline uses
three-byte Info headers while the integrated ancestor build uses six-byte
headers; copying candidate tables over the baseline invalidates that comparison.

Bind the restored Moves visual/donor controls into each new campaign before
`moves`:

```sh
python3 -m tools.dex_timing.unown_fast_campaign restore-negative --output build/regression-new-review
```

Despite its historical module name, this helper now uses the tools fixture
bundle for the Moves keyboard cartridge and Struggle-grant batteries. It no
longer requires the large ignored Dex build-history archives. It changes only
private test setup. Preserve failed setup logs before retrying.

The old family archives and loose source snapshots are retired. The previous
`tools/cleanup_dex_builds.py --verify` command describes the superseded archive
layout, not the current retention boundary. Use the bundle verification instead:

```sh
PYTHONPATH=tools:. python3 -m unittest tools.test_regression_fixtures
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures verify
```

For durable reuse on another machine, retain `tools/regression_fixtures/` with
the source checkout and install the external toolchain/boot ROM listed above.
Freeze fresh baseline/candidate sources rather than recovering an obsolete
whole-game candidate. Experimental builders for old architectures may require
their documented baselines to be reconstructed; their historical outputs are
not current-suite prerequisites. The two deliberately retained fallback
implementations have separate documented restoration archives.
An all-moves-seen fixture is for UI coverage; it does not replace empty/mixed
discovery fixtures or prove that gameplay discovery hooks work.

## 3. Full Campaign Execution

Use a fresh output under `build/`. Preparation rejects an existing output.
For current changes, use the generic fresh-link preparation first. The private
`build/new-candidate-source` placeholder below must already contain the candidate
source and its matching built ROM/symbols/map. The baseline defaults to the
current production checkout, not a retired October 14 candidate:

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures restore --compile-controls
PYTHONPATH=tools:. python3 -m tools.dex_timing.interactive_full_regression prepare --base build/regression-new-review --baseline-source . --candidate-source build/new-candidate-source --battery build/dex-moves-search-final-review-20261011/legacy-input.sav --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.unown_fast_campaign restore-negative --output build/regression-new-review/runtime-regression
```

Preparation freezes fresh baseline/candidate snapshots and creates the common
aliases. The standard phases below then target
`build/regression-new-review/runtime-regression`, not the parent directory.
Keep the supplementary registration, multipage, bookmark, capture and all-move
coverage described later; the standard phase list alone is not the full suite.

The lower-level examples below document the original Type adapter. Substitute
your fresh `BASE/runtime` and `BASE/runtime-regression` for the retired source
and output paths. Do not attempt to retrieve the removed historical directory:

```sh
python3 -m tools.dex_timing.type_full_regression prepare --source build/dex-types-mode7-audio-20261012/runtime --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression setup --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression dex --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression moves --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression persistence --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression discovery --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression gameplay --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression battle-discovery --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression timing --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression readiness --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression host --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression historical-host --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression gift --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression chart --output build/regression-new-review
python3 -m tools.dex_timing.type_full_regression diagnose-types --output build/regression-new-review
```

Run `discovery` before `gameplay` recreates the 100-move battle fixtures.
`readiness` depends on custom-menu fixture setup from `gameplay`. The focused
arrow/Type tests and exhaustive animations below must finish before `report`:

```sh
python3 -m tools.dex_timing.dex_arrow_cursors --output build/dex-types-mode7-audio-20261012/runtime
python3 -m tools.dex_timing.type_matchups --output build/dex-types-mode7-audio-20261012/runtime --all-models
python3 -m tools.dex_timing.type_full_regression report --output build/regression-new-review
```

For the two-variant layout, first prepare `BASE/runtime-regression` and
`BASE/precomputed-regression` using their respective source directories. Then
the campaign wrapper executes the ordered phases and stores statuses/logs:

```sh
python3 -m tools.dex_timing.type_mode7_campaign --base build/dex-types-mode7-audio-20261012 --variant runtime
python3 -m tools.dex_timing.type_mode7_campaign --base build/dex-types-mode7-audio-20261012 --variant precomputed
```

Do not rerun the full wrapper into a completed campaign merely to retry one
phase. Its optional phase selection retains previous attempt statuses/logs:

```sh
python3 -m tools.dex_timing.type_mode7_campaign --base build/dex-types-mode7-audio-20261012 --variant runtime --phases host historical-host report
```

Most established modules cap workers at six. Exhaustive renderer runs use eight
by default. Separate variants can run concurrently, but never run two writers
against the same fixture/core/report directory. Avoid editing a candidate
while its tests are running. If CPU headroom is needed, reduce workers in the
phase command definitions or run phases serially; do not silently reduce case
coverage. Child processes can keep running after a parent is interrupted.

## 4. Pokemon Dex Coverage

### Active Description Return Publication

`tools.dex_timing.description_latency_integration` freezes the actual checkout
(including accepted uncommitted work), requires an exact baseline ROM rebuild,
and verifies the production link's nine-byte ROMX increase with no added/moved
RAM. Its standard/extra phases reuse the full campaign described above, rather
than treating the focused improvement matrix as full acceptance.

After `selected` has created fresh matching Modern/Legacy checkpoints, run
`focused`: 128 four-age/four-phase Info returns, 128 Selected Moves returns,
128 uncaught returns, all 373 incoming species at ages 0/8 in both styles
(1,492 scenarios), and 256 Info/Moves return cases on each CGB 0/A/B/C/D/E.
Every model boots and builds its own checkpoints. Check actual complete lower
pixels, badge/type/footprint and ownership, exact authored portrait publication,
natural cry completion, and no upload/audio misses. Compare timings to the
frozen pre-fix matrix, in milliseconds and physical display frames.
`audit-latency` requires complete visible publication within eight display
frames (133.94 ms) for the 1,492 caught active-return cases, with margin above
the qualified maximum of 5.62 frames. The pre-fix matrix must fail this control.
This is a scoped regression ceiling, not a promised budget for every Dex action.

```sh
PYTHONPATH=tools:. python3 -m unittest tools.test_dex_description_latency tools.test_dex_backlog_revalidation -v
python3 -m tools.dex_timing.description_latency_integration selected --base build/description-review-new
python3 -m tools.dex_timing.description_latency_integration focused --base build/description-review-new --jobs 6
python3 -m tools.dex_timing.description_latency_integration audit-latency --base build/description-review-new
```

The integration runner's `freeze`/`prepare` actions are for this specific
promotion and require its retained cleanup assets and private nine-byte control.
For later source changes, adapt the baseline/candidate preparation and expected
resource delta explicitly; do not silently reuse October 14 checkpoints or
relax hash checks. The `models` action can resume a completed per-model native
report after a reporting-only interruption; its existing immutable inputs,
case count and success guards are verified first. Preserve the failed attempt.

Primary tools: `moves_search_dex_regression`, `listing_options`,
`search_qualification`, `mode_transitions`, `unown_regression`,
`performance_regression`, and `dex_arrow_cursors` in `tools/dex_timing/`.

The main Dex qualification has 4,479 scenarios:

| Suite | Cases | Coverage |
| --- | ---: | --- |
| Listing/sort popovers | 2,238 | All 373 species, three orderings, Modern and Legacy |
| Integration | 66 | List/detail and surrounding owner handoffs |
| Modal qualification | 144 | Popover input, publication, return ownership |
| Visual qualification | 192 | Layout, graphics, palette and cursor states |
| Edge cases | 13 per style | Empty/sparse/full seen sets, sort reset/no-op, gaps |
| Navigation | 399 | Directions, paging, wrapping, controller states |
| Selected owner | 1,178 | Frontpics, animation, cry, detail paging and returns |
| Pokemon search | 144 | Type filtering/order and displayed results |
| Search/list returns | 36 | Returning to the correct species/order/style |
| Search defaults/empty | 24 | Default Bug, blank secondary type, empty results |
| Mode transitions | 32 | 192 transitions across representative indices/phases |

Additional mode-transition runs enter Unown after prior Info and Moves views.
Locked/unlocked modes and closing/reopening must remain coherent.

Important invariants:

- New/evolution, National, and alphabetical vectors match canonical data;
  "National" currently means the game's existing sequence, not promised
  official National IDs. Species ID changes need separate oracle updates.
- Selecting a different sort starts at the list beginning. A same-sort no-op
  retains selection. Minisprites, names, frontpic, caught marker, and palette
  must agree immediately, including when already at the top before re-sorting.
- Modern/Legacy paths use their intended new colored frontpic/cursor rendering,
  without stale mini tiles, category/type palettes, or missing borders.
- Search ranks unordered dual-type matches first, then Type 1-only, then
  Type 2-only results. Assert against an independent expected sequence, not
  only a result count. Empty and duplicate/identical criteria are exercised.
- Search forms, Slowpoke animation, compact badges, blinking row cursor,
  result footer, palette restoration, and all return paths remain correct.

### Unown

The current campaign has 136 scenarios, 2,212 form selections, and 126 direct
draw units. It covers empty sets, all individual letters, varying set sizes,
ascending/reversed/rotated/shuffled order, sparse sets without A, and A in the
middle. It checks letter indexing, title/footer overlays, portrait palette
bounds, solid red outside background, solid black panels, and return ownership.
Direct draw cases include the tested monochrome/color flag variants; this is
not a full physical DMG gameplay campaign.

Negative controls must detect the earlier indexing, background, and panel
defects. A checker that passes both good and intentionally bad ROMs is not a
useful acceptance oracle.

The static Unown performance prototype adds native button-to-display sweeps:
112 cases on each of CGB 0/A/B/C/D/E, both listing origins and four input
phases. Every displayed frame must be an old or new whole selection; assert
that picture/map DMA stays within VBlank, the original form/banks are restored,
and returning preserves the originating selection. Compare ordinary Modern
and Legacy selection/entry timing against the frozen production link.

Its direct decoder fixture has 156 cases: all 26 forms after prior 5-, 6-,
and 7-tile species, with original form values 1/26. Check the independent
padded base image and stack/ROM/WRAM/SRAM restoration. The intentionally stale
dimension decoder must fail the expected 104 cases. Type return checks must
inspect Unown's actual centered portrait tiles and resident font/blank bytes,
not the generic top-left portrait oracle. See
[Unown Performance Prototype](pokedex_unown_performance_prototype.md) for the
recipe, evidence, ownership contract, and this run's explicit coverage limits.

### Selected Playback And Entry Timing

For each style, exercise all 373 species in cold, paging, and warm suites:
2,238 playback cases per candidate. Check actual picture frames, timelines,
resident tiles, upload/decode services, queue ownership, and cry completion.
Idle listing checks verify 120 hover frames do not resume cache warming.

### Long Breeding Lists

`tools/test_pokedex_egg_pages.py` creates disposable source fixtures under
`build/`; it does not require retaining artificial lists in production. Run:

```sh
PYTHONPATH=tools:. python3 -m unittest tools.test_pokedex_egg_pages -v
```

The four tests cover 6/10/11/15 moves (two/three pages, partial/full final
pages), move indices 1/255/256/333, family inheritance, unchanged non-Breeding
streams and unrelated species, the 19-page aggregate Mov limit, rejection at
20 pages, invalid moves and conflicting descendant lists. Check real linked
bank capacity too: successful host generation does not prove that the data
will fit beside its current neighboring sections.

For a private native qualification, add clearly labeled lists only to suitable
empty families, preserve existing lists and empty controls, and freeze both
links before testing. Enumerate each species' actual page counts for Selected,
registration, committed/pending B/End exits and rapid/held/canceled input.
Verify row contents, category transitions, partial-page clearing, badges,
page wrap, portraits, cries, caller banks/registers and complete displayed
pixels. Include Legacy presentation and input-phase controls; a Modern-only
contact sheet is not whole-Dex acceptance. Record new-page timings separately
from matched production pages, which may not exist in the empty baseline.

The retained October 17 fixture and native helper recipe are documented in
[Egg Page Qualification Prototype](pokedex_egg_placeholder_prototype.md).
Its direct `GetEggMove`/`InitEggMoves` calls exercise real linked routines on
cold-booted cores, not a complete naturally generated egg/hatch session.
`BREED-MOVE-01` in the separate [Breeding Bug Backlog](breeding_bug_backlog.md)
is a baseline TM-fallback failure, not an explicit egg-list or Dex-renderer
failure. Keep its strict raw reproduction and baseline comparison visible;
do not treat a scoped egg-list pass as a clean bill of health for breeding.

### Selected Runtime Display Qualification

The October 12 private runtime-display trial additionally removes Info glyph,
heading, number/bar and species-display tables, plus Selected Moves metadata.
It does not remove Area data or portrait scheduler plans. See
[Selected Pokemon Runtime Display Prototype](pokedex_selected_runtime_prototype.md)
for the frozen inputs, allocation delta, retained data, timing tradeoffs, and
existing host exception.

`tools/test_selected_runtime_display.py` compares linked runtime bytes against
the original display compiler and native source data: headings/stat glyphs,
all 256 numeric/bar values, all evolution text/requirements, every species'
native graph and move streams, decimal formatting, RAM boundaries, and bank
restoration. Select the candidate explicitly:

```sh
DEX_RUNTIME_SOURCE=build/selected-runtime-new/candidate python3 -m unittest tools.test_selected_runtime_display -v
```

Prepare normal-input Modern checkpoints with `performance --prepare` under
the source's `focused/modern/`; use matching ROM, symbols, and a copied battery.
The `selected_runtime` wrapper runs 746 Info scenarios, 746 Selected Moves
scenarios, and 400 rapid/held/canceled Info scenarios. Its audit explicitly
expects the integrated double-speed policy. A legacy normal-speed harness
report is not acceptance evidence for the current game.

```sh
python3 -m tools.dex_timing.selected_runtime info --source build/selected-runtime-new --jobs 6
python3 -m tools.dex_timing.selected_runtime moves --source build/selected-runtime-new --jobs 6
python3 -m tools.dex_timing.selected_runtime stress --source build/selected-runtime-new --jobs 6
python3 -m tools.dex_timing.selected_runtime inventory --source build/selected-runtime-new
```

After `type_full_regression prepare/setup`, paired timing phases use fresh
candidate/baseline Modern and Legacy checkpoints. `compare` has 1,600 page,
species, listing, and Area-return cases; `extra-timing` has 544 evolution/Moves
cases; `startup` has 16 normal-input Dex-reopen cases. The latter explicitly
selects Legacy before closing, rather than assuming a Legacy checkpoint's
battery already stores that presentation.

```sh
python3 -m tools.dex_timing.selected_runtime compare --source build/selected-runtime-new --campaign build/runtime-review-new --jobs 6
python3 -m tools.dex_timing.selected_runtime extra-timing --source build/selected-runtime-new --campaign build/runtime-review-new --jobs 6
python3 -m tools.dex_timing.selected_runtime startup --source build/selected-runtime-new --campaign build/runtime-review-new --jobs 6
python3 -m tools.dex_timing.listing_warming timing --output build/runtime-review-new --jobs 6
```

Report median matched-case differences, distributions and individual maxima,
not only differences between population medians. Separate input acceptance,
first changed pixel, complete screen, and animation/cry deadlines. At double
speed, safe preparation still proceeds at the display-frame cadence, so a ROM
saving can add page latency without changing the portrait timeline. Run the
standard Dex, Moves Search, Unown, Type return, host and full-species playback
phases on the same frozen link before accepting a runtime-rendering change.

### Precomputed Production Ancestors

The October 13 production build retains generated display pixels and adds
ancestor groups after forward Evolutions. It uses six-byte Info headers and
pooled precomputed display records. Qualify actual graph direction/order,
native requirements, empty/odd groups, caught visibility, page capacity,
caller banks and unchanged live RAM addresses:

```sh
PYTHONPATH=tools:. python3 -m unittest tools.test_pokedex_ancestors -v
python3 -m tools.dex_timing.selected_architecture prepare --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture info --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture moves --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture stress --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture feature --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture returns --source build/ancestor-review-new --jobs 6
python3 -m tools.dex_timing.selected_architecture modes --source build/ancestor-review-new --jobs 6
```

The frozen source needs the wrapper's `pokecrystal-dex-selected-runtime` aliases,
matching symbols and copied battery; the alias does not imply runtime rendering.
The 13 precomputed heading tiles borrow bank-1 Unown font cells `$b5-$c1`.
After Info, verify every actual Unown font byte, centered portrait, blank tile
and letter overlay; returning to Selected must restore the heading. Cover both
Pokemon listing origins and all six CGB models. Existing Area data and shared
ISR/battle/audio code remain unchanged, but the complete full regression and
all-move timing/pixel comparisons are still required.

The accepted native catalog's focused matrix has 746 Info, 746 Selected Moves,
400 stress, 1,056 all-page feature timings, 115 panel returns and 96 font-reuse
transitions. Actual counts vary with evolution data; inspect current summaries
rather than treating the earlier scoped 1,248 estimate as observed evidence.
See [production ancestor integration](pokedex_ancestors_production_integration.md)
for the exact build and [archived fallback](archived/selected-vram-ancestors-20261013/README.md)
for the separately restorable runtime/VRAM alternative.

### Semantic Metadata And Ancestor Architecture Trials

The six private October 12 links retain semantic Info/Selected Moves records
but remove main-rendering display glyphs. Compare RAM preservation, guarded
VRAM readback and immutable ROM recovery, each with and without ancestor
pages. See [the architecture report](pokedex_selected_architecture_comparison.md)
for exact hashes, allocations, implementation and matched measurements.

```sh
python3 tools/build_selected_semantic_prototype.py --output build/selected-semantic-new --restore vram --ancestors --jobs 6
python3 -m tools.dex_timing.selected_architecture prepare --source build/selected-semantic-new --jobs 6
python3 -m tools.dex_timing.selected_architecture units --source build/selected-semantic-new --jobs 6
python3 -m tools.dex_timing.selected_architecture campaign --source build/selected-semantic-new --jobs 6
```

Omit `--ancestors` for the paired old-page link. Always use a fresh private
directory; never run the patched recipe against production source or the
player's battery. `control` freezes production and prepares matching fixtures
for timing instead of borrowing an older save's discovery expectations.

The campaign records 746 Info, 746 Selected Moves, 400 input-stress, 1,072
main timing, eight reopen, 512 entry-timing, 4,479 standard Dex and host
scenarios. The separate all-page timing survey has 672 old-page or 1,248
ancestor-page cases, with 105 or 115 cancellation/pixel return cases. Counts
overlap and are not an additive independent-test total. Check actual summary
counts and hashes before claiming acceptance.

Runtime unit tests now cover all old glyph/heading/number pixels, native
requirements, semantic lists, all 373 ancestor chains, group page boundaries,
page selectors, headings/attributes, RAM limits and bank restoration. The
VRAM branch also checks exact committed-atlas reads at all 1-40 tile counts
and both prior VBK values. The ROM branch checks every species/page's ordered
recovery atlas and committed keys surviving a subsequently requested page.
Branches skip genuinely inapplicable tests; skips are not passes.

The new heading temporarily owns the first 13 bank-1 Unown-font tiles. Run
`modes` after Selected/Info ownership, not just on a clean Dex menu: 16 phase,
index and presentation scenarios, 96 transitions. Read all 27 resident Unown
glyphs from VRAM and compare to the linked source; then revisit every actual
Info page and audit heading pixels/attributes. A correct first Unown portrait
alone cannot detect a damaged alphabet. Page and intraspecies sweeps must also
catch heading collisions with the scattered Info atlas and animated sidebar.

`types` runs all 18 selections, 72 navigation and 32 input-phase cases,
720 held-input frames, 1,800 idle frames, raster/palette/bank checks, 42 owner
reentries, 12 close/reopens and 24 post-return Selected playbacks. It also
checks the linked battle chart's 648 single/2,754 dual calculations. This is
not a substitute for the separate all-move animation campaign.

`selected_comparison` emits matched distributions for the six frozen links.
Three comparison unit tests prevent pairing an old wrap/no-op with a newly
rendered ancestor page. Existing Area, Moves and species-transition audits
detect the ancestor-enabled symbol and use its actual page count.

Keep native owner-ready/reveal timing alongside final-pixel-hash timing.
A blinking cursor can delay matching the final hash by multiple frames even
when the native reveal time is unchanged. Investigate the raw trace before
calling that an algorithm slowdown. Conversely, do not discard a real
Area-to-Info regeneration delay because a population median is small.
Historical campaigns through October 13 retain the synthetic LY-64 host failure
as recorded evidence. On October 14, the stale READY-handoff assertion was
corrected to the current 83/84 admission boundary, expanded to all 154 scanlines,
and supplemented with portrait/frame/sample-cache guard checks. The current
87-test host group passes on production and the New Entry visual prototype.
Do not carry the old LY-64 assertion forward as an allowed failure in new runs;
investigate future failures against the current timing contract.

Entry timing uses sixteen representative species, four hover durations
(0, 4, 30, 120 frames), four physical phases, both styles, and both links:
1,024 rows / 512 pairs. Retain first/complete display metrics and actual owner
reveal. Animated/blinking frame hashes can make a generic "first change"
misleading; corroborate with owner/window publication events.

Shared arrow checks exercise 1,792 counter/bank/reset cases, 52 locations, and
3,328 idle frames. Only the arrow should change between blink phases; text,
borders, and backgrounds remain static. The naming-screen box is a distinct
cursor convention and must not become an arrow.

## 5. Moves Dex, Search, And Sort Memory

Primary tools: `moves_mode`, `moves_search`, `moves_sort_memory`.

| Suite | Current Cases |
| --- | ---: |
| Native filter contracts | 1,692 |
| Normal-button control flows | 10 |
| Visual sweeps | 1,406 |
| Navigation/paging | 2,686 |
| Mode/search transitions | 11 |
| Surrounding/save flows | 2 |
| Search form polish | 1,284 |
| Naming selection cursor | 3,840 |
| Sort preference helpers | 4,096 |
| Sort preference UI | 16 |
| Sort preference save cases | 11 |

Filter contracts cover empty/mixed/all-seen sets, both sort orders, all eighteen
types plus blank, nine representative name queries, and all 333 complete move
names. Queries include case differences, substrings such as `double`, internal
matches, punctuation/space, and no-hit text. When both criteria are present,
type and case-insensitive substring matching are ANDed. Unseen moves are never
search hits. Blank criteria yield the seen subset in the selected sort order.
Check result buffers and adjacent sentinels, count/index width, bank restoration,
sort memory, the main Pokemon order, and transient move tables for corruption.

Visual/navigation tests cover both orders, seen/unseen names, stats, type and
category icons, descriptions, scrollbar, full-page left/right jumps, held keys,
wraparound, popover priority, margins, search/result footers, and returning from
results to the full list. No stale search icon may replace the category icon.
Changing sort resets position; sort preference survives the intended save/load
paths. Position remembrance is a separate feature, not implied by sort memory.

Text-entry assertions cover default uppercase, Select casing changes, A insert,
B backspace including empty/boundary cases, Start moving to End, and A confirming
End. Exercise every directional neighbor and the maximum query length derived
from `MOVE_NAME_LENGTH - 1`, including automatic End positioning at capacity.
Verify white blinking letter/command boxes against the normal naming-screen
geometry, End placement, elevated unused dashes/lowered current position,
background isolation, and restoration of menu fonts/palettes/OAM on exit.
Do not assume that changing the query's case should change matching results.

Sort helpers test all byte values across all WRAM bank selections for read/write
normalization and restoration. UI/save tests include invalid legacy values,
defaults, opposite/current selection, cold reload, and unaffected discovery bits.

### Shared Moves Bookmark Qualification

The combined implementation was production-integrated on 2026-10-15 with exact
ROM/symbol/map equality to the fully qualified candidate. Fresh root-link
observers reran 16,176 Pokemon helpers, 12,641 Moves helpers, six integration
contexts and 13 lifecycle cases. The original full campaign was reused by exact
binary identity, not presented as a second full run. The reusable promotion
driver and receipt are under `build/dex-position-production-integration-20261015/`;
see [production integration](pokedex_session_position_prototype.md#production-integration).
Promotion-aware host contracts compare original protected root artifacts to
their archived copies and new production artifacts to the integration receipt.

The later [combined Pokemon/Moves prototype](pokedex_session_position_prototype.md)
adds `pokemon_position`, `dex_position_campaign` and `test_dex_position`. Its
16,176 native cases include every legal Modern/Legacy viewport across the three
Pokemon sorts, malformed/sparse/changed orders and identity preservation.
Require all 48 real-input cell/row contexts, Search/Selected isolation,
independent Moves bookmarks, normal Save, actual soft reset/cold Continue,
primary/backup recovery and the normal title-menu New Game path. Do not invoke
the broad New Game RAM reset as a suspended overworld helper call.

Capture Pokemon state only at ordinary Listing exit; restore before grid-cache
priming. Invalid or reset bookmarks start first, including Legacy, which no
longer consults the inherited temporary-species restorer. Modern/Legacy share
selection; layout switching retains the current existing conversion behavior.
The combined eight-byte padding layout requires an eight-byte successful-Continue
clear while leaving sort/presentation preferences alone. Emulator state resume
does not substitute for a reset/cold-boot test.

Modern checkpoint preparation must explicitly seed Modern/Evolves in a private
fixture rather than trust its donor save. Run discovery before gameplay,
gameplay menu setup before battle discovery, and persistence/migration setup
before timing. Chart helpers create their own output directory. Compare sound
register values **and relative physical write timing**; same-case fade/init cost
deltas explain entry busy-flag timing, not a pooled opening median. Preserve
the original failed expectation and the stronger hardware proof. The combined
campaign also samples 144 first/middle/last reopen workflows; record the actual
selected identity on both links, because production need not render the same
selection or viewport as a candidate that remembers position.

The private [Moves position prototype](pokedex_moves_position_prototype.md)
adds `moves_position` and `test_moves_position` without replacing the existing
sort/Search tests. Its tag/ID/row fields consume four saved-padding bytes;
position is not a new discovery flag or a transient-ID reference. Do not keep
an unconditional reset-to-first expectation for same-session reentry when
these linked helpers exist. The 2026-10-14 session revision explicitly clears
position on successful Continue after either cold power-on or real soft reset,
while retaining the separately saved sort preference. Saving during play must
not clear the live bookmark. New Game also starts at the beginning. The earlier
persistent prototype and its full campaign are historical evidence only; its
cold-Continue restored-position expectations do not apply to this revision.
Changed sort must still reset; same-sort/cancel must preserve; Search form,
keyboard and Results must not overwrite the ordinary-list bookmark.

At 333 moves and eight rows, exercise all 5,216 legal cursor/viewport pairs
across both sorts. Include all raw WRAM banks, preserved registers/adjacent
saved bytes/discovery, malformed or absent tags/IDs/rows, sort mismatch and
boundary clamping after reordered data. Native menu checks must cover all rows,
both Pokemon-mode origins, full Dex reopen, shared Info/Moves/Unown/Type owners,
unseen rendering, zero results and direct Results exit. Test normal Save/cold
Continue, primary/backup precedence/corruption, the actual bookmark/checksum
write-prefix interruptions, canceled Save/New Game, overwrite and deletion.
For the session revision, any recovered copy must retain its sort but start
at the first move; do not assert that its saved bookmark is restored.
Measure entry at beginning/middle/end of both orders against a frozen baseline
in milliseconds and physical display frames; assert actual restored identity,
not just that entry completed.

For large campaigns, `DEX_COMPRESS_TRACE_ROOT` may name the fresh evidence root.
Only consumed JSONL traces inside that root are replaced by lossless gzip
siblings; `direction_changes.load_trace` replays either form. Other files and
old campaigns remain untouched. Record this retention option with the evidence
and retain the compression round-trip/outside-root negative controls. It is
not permission to omit traces, skip cases or erase failed attempts.

## 6. Persistence And Legacy Migration

Primary tools: `move_persistence`, `move_acquisition` migration/interruption
actions, `move_persistence_report`, and `acquisition_performance`.

Current coverage per candidate:

- 2,380 bit/index helper cases and four payload snapshots.
- 1,490 cold-boot cases, including five save patterns reloaded through both
  copies; these counts include interrupted/corrupted input families.
- 152 interrupted-save-write cases and 150 interrupted-repair cases.
- Five lifecycle cases: New Game, subsequent save/reload, canceled overwrite,
  old-save preservation, and deletion/reset behavior.
- 29 acquisition-aware migration cases, with up to 288 owned Pokemon / 1,152
  move slots, plus 150 interrupted-migration cases.

Check every valid permanent move index, boundary/high-byte indexes, invalid
zero/out-of-range indexes, duplicate marks, unused bitmap bits, and incoming
bank/register preservation. Use empty, singleton, mixed boundary, alternating,
and all-seen patterns.

Cold boot must execute the actual loader rather than loading an emulator state
that already contains the expected flags. Test valid primary/backup copies,
checksum/signature/version corruption, mismatched copies, absent legacy records,
and recovery policy. Interrupt each relevant byte write/repair boundary, restart
from that battery, and require a valid recoverable result. Preserve unrelated
core-save bytes/checksums, other banks, RTC data, and buffer sentinels.

Legacy migration scans owned party, current/inactive PC boxes, and valid daycare
ownership, correctly handling packed permanent IDs, eggs, invalid counts/indexes,
and mixed saves. Its initial read-only reconstruction must not perform premature
SRAM writes; normal save/repair must produce both complete valid records.
Canceled New Game overwrite must not destroy the previous persisted discoveries.

## 7. Acquisition And Learning Discovery

`move_acquisition` has 12,276 native helper cases plus 59 positive/negative
source scenarios. The helpers test valid/invalid permanent IDs, repeated marking,
transient-ID reuse, garbage collection, party move inspection, and caller
bank/register state.

The current source inventory is defined explicitly in
`move_acquisition.qualify(..., sources=True)` and includes:

- Learning into an empty slot or replacing a move; declining; battle learning;
  transformed/other-Pokemon contexts; level and evolution learning/declining.
- TM, HM, and tutor success, already-known, incompatible, and declined cases.
- Failed ball, trainer battle, full storage, tutorial capture, party/PC success
  through surrounding capture scenarios, and enemy generation without receipt.
- Party/PC gifts, full storage failure, pre-Dex gifts, extended-ID gifts,
  normal/special/skipped Dratini gifts, and successful/declined/wrong trades.
- Egg receipt/full storage/not-ready negatives and actual hatch positives.
- Daycare man/lady retrieval and full-party negatives; service success,
  decline, insufficient-money, and full-party paths for each provider.
- Contest party/PC receipt, no catch, full storage, and pending contest catch.

Assert that a positive scenario really acquired/learned the intended move, not
merely that a helper set a bit. Negative scenarios must neither set discovery
bits nor alter an unrelated Pokemon. Recording uses permanent indexes, never
temporary IDs whose meaning can change after collection/reuse.

Policy contracts: eggs record on hatch, daycare records at retrieval without
retroactively tracking overwritten moves, and contest catches record only when
finally received. Special gifts are covered through their actual move-writing/
receipt path, including scripts bypassing ordinary LearnMove.

## 8. Battle-Use Discovery And Struggle

Primary tools: `move_battle_use`, `battle_use_campaign`, `pokedex_gift`.

The current full phase runs 4,724 native wrapper/index contracts, 400 semantic
cases (50 kinds, both actors, four phases), and eight supplemental Bide cases.
The separate Struggle award tests have sixteen initial plus sixteen repeated
awards, cold save/reload, and an assertion that awarding alone does not write SRAM.

Semantic inventory includes ordinary use, miss, immunity, failed effect,
selected-but-not-used, sleep/freeze/flinch/recharge/disable/paralysis/confusion,
switch actions, canceled selection, inability to move, Focus Punch tightening/
disruption/switching, Metronome and rejected selections, Sleep Talk success/
awake/self-only/disabled/charge-only pools, Mirror Move success/charge/failure,
Sketch use versus copy-only mutation, Mimic, Transform, borrowed moves,
Struggle, trainer/Tower/tutorial/scripted/pre-Dex contexts, scene-off behavior,
disobedience/substitution, sun SolarBeam, and each declared charge move.

Rules to assert:

- A charge move is seen on its first use, even if release never happens.
- Focus Punch is seen when focus tightens, even if disrupted.
- Called moves and their caller are both recorded when actually presented.
- Selecting an action without reaching use does not discover it.
- Sketch itself is recorded on use; converting it into another move is not
  independently treated as that copied move being used.
- Struggle is marked when the player receives the Dex, idempotently.

The battle roundtrip fixture saves actual new discoveries, cold reloads, checks
the seen bitmap, and verifies the Moves Dex display. Keep this integration step
even when direct wrapper/semantic units pass.

## 9. All Battle Animations

Primary runner: `tools/dex_timing/all_battle_animations.py`.
Native observer: `tools/dex_timing/probes/battle_animation_sweep.c`.

Supply a JSON array of configurations. Each contains `variant`, `root`, `rom`,
`sym`, `battery`, `expected_double_speed`, `expected_battle_speed`, and
`fresh_battle_fixture`. One variant must be named `production`. For the current
three-build comparison the builder supplies this file after full preparation:

```sh
python3 tools/build_dex_types_mode7.py animation-configs --output build/dex-types-mode7-audio-20261012
python3 -m tools.dex_timing.all_battle_animations prepare --output build/dex-types-mode7-audio-20261012/all-animations --configurations build/dex-types-mode7-audio-20261012/animation-inputs.json
python3 -m tools.dex_timing.all_battle_animations renderer --output build/dex-types-mode7-audio-20261012/all-animations --configurations build/dex-types-mode7-audio-20261012/animation-inputs.json --jobs 8
python3 -m tools.dex_timing.all_battle_animations native --output build/dex-types-mode7-audio-20261012/all-animations --configurations build/dex-types-mode7-audio-20261012/animation-inputs.json --jobs 6
python3 -m tools.dex_timing.all_battle_animations report --output build/dex-types-mode7-audio-20261012/all-animations --configurations build/dex-types-mode7-audio-20261012/animation-inputs.json
```

Use the same custom configuration path for every action. Default paths describe
an older investigation and are not a generic current baseline. `smoke` is useful
for debugging but is not full acceptance. `compile` refreshes observers after
observer code changes; it does not recreate linked-ROM-dependent checkpoints.

### Direct Renderer Matrix

The catalog is derived from move constants and animation pointers. Current
coverage is all 333 move entries plus 28 auxiliary entries. Each runs on both
sides and at four physical phases (0, 17,556, 35,112, 52,668 ticks). Scripts with
`anim_if_param` also run parameters 1, 2, and 3 in addition to 0: currently thirty
moves and two auxiliary entries.

This produces 3,384 move calls plus 272 auxiliary calls = **3,656 per build**,
or 10,968 across production and both candidates. Cover charge/release, Substitute,
send-out/shiny, capture/wobble context, and other auxiliary branch variants.

The fixture explicitly supplies animation ID, side, parameter, and coherent
battle/capture context, then executes the real animation routine. It does not
patch PPU state, IME, or speed to manufacture equal timing. This isolates the
renderer; it does not prove every move's damage/effect/discovery behavior.

Required comparisons:

- Returned successfully; ROM bank, WRAM bank, speed, and VBlank owner restored.
- Exact physical elapsed time for unchanged animation behavior.
- Same logical state, object/OAM/background effects, update counts, and cadence.
- Same rendered full-frame pixel hash sequence and frame count.
- No missing, unexpected, or duplicate catalog/side/parameter/phase cases.

The observer hashes actual rendered pixels. The first partial frame after a
loaded CPU checkpoint is excluded because the emulator's external pixel buffer
is not part of that checkpoint. All subsequent complete frames are included.
The renderer uses a 32-bit FNV sequence hash, not stored images of every frame;
hashes are practical regression evidence, not a mathematical no-collision proof.
Keep screenshots/traces for failing cases and representative manual review.

Native time fields use 4,194,304 physical ticks per second and 70,224 per frame
(about 16.743 ms). At double CPU speed, CPU instruction T-cycles are not the same
units as these physical ticks. Do not accidentally double/halve measured time.

### Normal Battle Input Matrix

All 333 moves also run through ordinary battle inputs on both actors at phase
zero: 666 cases per build. The established 100-move matrix adds both sides and
four phases, yielding 1,600 rows / 800 baseline-candidate pairs per full campaign.
Check actual requested-animation start/return, completed gameplay ownership,
CPU speed, menu return, discovery state, and move effects appropriate to the
fixture. Direct renderer coverage cannot substitute for these integration runs.

Current known all-move exceptions: nineteen condition-specific fixtures do not
activate the requested animation; thirteen knockout/ending/switch paths do not
return to the generic turn menu; two Sand Tomb cases hang after the animation
returns. These identities must match production. New identities are failures,
even if the total exception count stays 34. `edges` extracts invocation/return
evidence for exception diagnosis.

When a duration differs, inspect actual start alignment. The current requested
chart changes alter pre-animation scanning and therefore a few start phases.
`type_chart_phase_check` documents a chart-only ablation: keep display code,
restore only the frozen production chart plus its zero-byte end label, rebuild,
create fresh checkpoints, and rerun differing cases plus controls. Never assume
that a similar-looking delta has the same cause. An incremental build that did
not rebuild changed data is not a valid ablation.

## 10. Menus, Gameplay, Audio, And Speed

Primary orchestrator: `acquisition_regression`. Its current paired campaigns:

| Campaign | Coverage |
| --- | --- |
| Menus | Ten context reports, 1,792 input/register contracts |
| Custom menus | 464 internal cases across two links; actual pixel/timing comparison |
| Popup readiness | 148 selections, including Pack, Apricorn, TM/HM entries |
| Surrounding gameplay | 22 scenarios, eleven kinds on baseline and candidate |
| Sampled cries | 960 rows / 480 pairs |
| Battle speed transitions | 24 runs, repeated battles/learning/loss at four phases |

Menu contexts are standard, battle, mart, puzzle, and game corner. Verify allowed
button masks, new/held/repeat/overlap/release handling, rejected controls, register
preservation, menu ownership, and CPU speed. Custom inventories also compare
selected contents, frame/palette/OAM hashes, and first/complete display timing.

Gameplay scenarios cover movement/navigation, purchase, puzzle, fishing,
trainer battle, phone, level-up learning, egg hatch, PC capture, party capture,
and heal/save. Acquisition tests add actual daycare, gifts, contest, and trade
paths. This is a surrounding-gameplay sample, not every map/script/quest.

Sampled cries cover twenty species across stats, catch, faint, player send-out,
blocking playback, and stereo playback, with four phases on two links. Compare
sample blocks, waveform hashes, timer configuration, frequency, expected speed,
exhaustion/completion, and shutdown. Keep known baseline timing misses explicit;
equal misses are not newly passing cases. Listen manually to representative
samples because register/hash tests do not replace auditory review.

Normal battles must use the intended normal clock while world/menus use the
intended double clock. Repeat eight battles, return through menus, learn a move,
and exercise loss/blackout. Check clock restoration after animations, cries,
Dex views, and gameplay return rather than checking only the initial setting.

`acquisition_performance` measures valid load, small/full legacy migration,
recovery, and normal save against the baseline. Retain physical times and
protected save bytes. A CPU-host wall-clock slowdown is not a game slowdown.

## 11. Type Matchups Add-On Qualification

These checks are mandatory when Type Matchups exists in the candidate; for a
branch without that feature, record the explicit scope exclusion instead of
pretending the Type-specific adapter ran successfully.

```sh
python3 -m tools.dex_timing.type_matchups --output build/dex-types-mode7-audio-20261012/runtime --all-models
python3 -m tools.dex_timing.type_mode7_comparison measure --base build/dex-types-mode7-audio-20261012 --variant runtime
python3 -m tools.dex_timing.type_mode7_comparison audio --base build/dex-types-mode7-audio-20261012 --variant runtime
python3 -m tools.dex_timing.type_mode7_comparison audio_navigation --base build/dex-types-mode7-audio-20261012 --variant runtime
```

Repeat for `precomputed` when comparing both implementations. The ordinary full
campaign is primarily CGB E; focused Type tests additionally use revisions
0, A, B, C, and D. This does not certify all gameplay on every revision or on
physical hardware.

Type checks include eighteen selections, 72 directions, 32 starting-phase
cases, 720 held-input frames, 790,016 badge pixels per revision, and 13,164
legal full frames per variant across the six revisions. Verify 88 accent bytes
per frame, no mode-3 writes, correct palette indexes, atomic lower-panel/cursor
publication, and exactly-once frame work. Check AF/BC/DE/HL/SP, ROM/WRAM banks,
input, sound, game clock, interrupts, OAM locks, and scratch ownership.

Entry/exit checks cover eight phases each and no white flashes. Return coverage
includes 42 owner reentries, twelve closes/reopens, both styles, all Pokemon
sorts, locked/unlocked Unown, and 24 Selected picture/cry playbacks after leaving.

The independent workbook snapshot validates 324 attack/defense cells and current
128 records. Battle-routine calls cover 648 singles, 2,754 unique dual-type
combinations, and four identified/Foresight cases. Validate alphabetical badges,
Electric self-immunity, separate I rows, Steel's combined R, overflow placement,
empty rows, and exact existing art/colors/corners/borders.

Music stress uses all 122 entries, including silence, for 1,800 idle frames each,
then `SFX_MENU`, `SFX_READ_TEXT_2`, and `SFX_CHANGE_DEX_MODE` for 90 frames each.
The navigation variant uses 360 idle frames and immediate SFX with 90 held-down
frames plus release, auditing legal atomic selection frames. These use real
PlayMusic/PlaySFX calls from an explicit synthetic caller at the natural live
Type-owner boundary; they do not claim naturally traversing all music maps or
exhaustively covering arbitrarily long future command streams. No PPU/IME patch.

Measure eight entry phases and 576 direction changes per variant. Report input
acceptance, map publication, and first complete displayed change separately.
Then compare all eighteen actual screenshots between variants, normalizing only
the expected arrow blink rectangle, not arbitrary mismatched pixels.

## 12. Host Tests And Acceptance Reports

The linked host group contains the repository's Moves production, Dex scheduler,
Info, Moves, Area assets, description paging, sampled-cry shutdown, and battle
motion tests. The historical group runs `tools.test_dex_timing` against the two
matching source roots. Do not substitute only static text assertions for native
integration tests or change goldens merely to make a new feature pass.

Required acceptance for a current full run:

- Every planned phase completes, with matching ROM hashes and expected cases.
- No new native functional/visual/bank/save corruption failures.
- Complete animation catalog and native input coverage, exact phase-matched
  renderer timing/logical/pixel sequence, and unchanged baseline exception IDs.
- Unchanged normal menu/save/audio behavior; quantified latency deltas outside
  the requested feature. Investigate unexplained multi-frame changes.
- If Type exists: six-model evidence, both music stress reports, independent
  chart calls, and complete Type entry/navigation/return checks.
- Protected production ROM/symbol/map and review battery hashes unchanged.
- All retained baseline failures/skips explained, with actual baseline reruns.

The current report gates return nonzero on failed/missing acceptance, rather
than printing a false `merge_ready` value while exiting successfully. Inspect
`full-regression.json`, `phase-results.json`, and the underlying reports anyway.
The two-variant aggregator is:

```sh
python3 -m tools.dex_timing.type_mode7_report --base build/dex-types-mode7-audio-20261012
```

It additionally requires identical ordinary source paths, final ROM hashes,
complete rendered-frame evidence, both independent campaigns, six Type models,
both audio stresses, visual equivalence, and the retained chart-start-phase
investigation. This aggregator is specific to the two Type variants, not a
universal gate for an arbitrary unrelated branch.

### Historical Type Comparison Limitations

These counts belong to the original Type comparison reference, not an automatic
allowlist for the latest production link. In particular, the current linked
host group no longer permits the old LY64 failure. Use the fresh paired reports
and exact exception identities for each run; the interactive qualification
report records its current results separately.

- Linked host: 85/86 pass; Info ready-handoff at LY64 fails equally on both.
- Historical host: six failures, sixteen errors, 103 skips among 187 checks,
  with the same identities on production/candidate. Detail differences are kept.
- All-move normal input: nineteen missing condition-specific setups, thirteen
  ending/menu ownership expectations, two pre-existing Sand Tomb hangs.
- Sampled cries: the same 32 known timing misses per paired link.
- Type comparison: requested chart changes explain small whole-battle duration
  differences; phase-matched rendering is exact. Long-hover Legacy Dusknoir
  Selected entry is one frame later despite unchanged median Legacy latency.
- No physical Game Boy validation, exhaustive long-duration music proof,
  hardware battery/power measurements, or every-map/every-event playthrough.

Do not grandfather a future new failure simply because its category resembles
one of these. When fixing a baseline defect, update/remove its recorded exception
only after new positive and negative evidence demonstrates the fix.

## 13. Failure Investigation And Retesting

For each failure retain the ROM hash, baseline hash, exact case parameters,
emulator model, fixture battery/checkpoint, expected and actual result, event
trace, screenshots, and first failing frame/call. Reproduce with the same
link before changing anything.

Determine whether the failure is gameplay, rendering, timing, fixture setup,
stale symbols/checkpoint, incomplete build dependency, or an outdated oracle.
Compare production in the same environment. For timing, separate pre-call start
phase, logical update count, physical gaps, and displayed pixels. Use a scoped
ablation only as diagnostic evidence, not as the review ROM.

After a game fix, rebuild and regenerate affected fixtures, then rerun the
affected suite and surrounding/full suites according to its blast radius.
After a harness-only fix, preserve the initial evidence and rerun both baseline
and candidate assertions. Do not overwrite a failed phase with a manual "pass"
without an actual successful rerun.

## 14. Reuse And Catalog Growth

For another gameplay change, freeze that branch's baseline/candidate source and
binary inputs, regenerate coherent snapshots, update adapter filenames/manifests,
and run the applicable unchanged campaigns. The current adapter carries Type
aliases and old fixture paths; it needs a thin configuration adjustment where
those do not exist. Do not alter game logic or expected outcomes merely to fit
an old adapter. Keep feature exclusions explicit in the report.

Before adding approximately eighty moves or ten species:

- Audit hardcoded 333/334 and 373/374 ranges in persistence, acquisition,
  battle-use, search, gift, navigation, and fixture generation. Update to catalog
  constants where appropriate, with an independent expected-count check.
- The 64-byte move bitmap nominally holds 512 indexes, but that alone does not
  prove every bound/buffer/layout supports a larger catalog. Search result
  buffers, sort records, permanent/transient tables, and unused-bit tests need
  explicit review. Current filter sentinels assume 666 result bytes.
- The exhaustive animation catalog derives current pointers/constants. Assert
  new expected coverage, include each new conditional parameter path, and add
  normal battle fixtures for special semantics. Keep the 100-move historical
  sample as continuity coverage rather than replacing exhaustive coverage.
- When baseline and candidate catalogs differ, compare shared entries by stable
  identity using each ROM's own ID mapping and symbols. Test newly added entries
  separately as candidate-only coverage. The current animation runner reads
  the working catalog; it must be adapted before comparing an expanded candidate
  against an older production ROM. Never call a new candidate ID in a baseline
  that lacks that entry or count such a run as a valid paired comparison. Apply
  the same shared/new partition to expanded species coverage and fixtures.
- Refresh species orders, pictures, descriptions, cries, seen/caught fixtures,
  extended-ID boundaries, Unown placement, and representative new entries.
- Regenerate Type panels and the independent expected chart when effectiveness
  intentionally changes; do not leave a stale workbook oracle in place.
- Update music-entry expectations (currently 122) if the table changes. Rerun
  worst-case command/SFX/deadline tests after audio changes. Audio bank `$3a`
  currently has only 26 free bytes in the Type prototypes; bank-local pressure
  matters even with substantial aggregate ROM space.
- Refresh legacy migration/corruption fixtures after save-format changes and
  test compatibility with genuine prior-save layouts, not only newly generated
  saves using the new layout.

## 15. Manual Release Review

Automated qualification is followed by manual review of both UI styles, all Dex
modes, Type movements/immunities/Steel overflow, search text controls, scrollbar/
popover placement, menu returns, selected animation/cry, real saves/reloads,
party/PC/daycare/egg/contest interactions, and representative battles on both
sides. Include long animations, water screen effects, charging/called moves,
and rapid mode switching. Listen to music/SFX/cries and review the reported
latency outliers. Physical CGB testing is a separate desirable release step.

Do not promote production automatically because the machine report says
`merge_ready`: that means the defined automated acceptance has cleared, not
that manual review, known separate backlog work, or user approval is complete.

## 16. Evidence Record Template

Record the following with each campaign:

```text
Date, branch/commit and dirty-source snapshot:
Baseline ROM/source/symbol/map hashes:
Candidate ROM/source/symbol/map hashes:
Fixture manifest/battery/boot-ROM hashes:
Python/RGBDS/Clang/SameBoy versions:
Emulator model(s), clock expectations and worker counts:
Exact preparation and phase commands:
Expected/actual cases and coverage per suite:
New failures, baseline exceptions, skipped/excluded scope:
Latency comparisons and critical-path instruction changes:
Failed attempts, diagnosis, correction and successful retries:
Report/trace/checkpoint/screenshot locations:
Production-input protection checks:
Manual/hardware review status and integration decision:
```

The October 12 final evidence is retained in
`build/dex-types-mode7-audio-20261012/`. Its comparison document records the
frozen outputs, full campaign results, the corrected host-baseline setup,
audio-stress fix, chart ablations, narrow Legacy latency difference, and memory
costs. Future runs should create their own dated evidence instead of silently
reusing or overwriting that reference.

## 17. Dex Entry And Exit Reveal

The Stage integration adds a mid-transition requirement: a correct completed
overworld does not excuse corrupt frames before it. `ClearPalettes` queues
white; it is not a synchronous hardware update. Preserve the display wait
before the map reload suppresses VBlank. Also preserve the local close guard
around map publication, and the complete exit `WaitSFX` before masking.
See [Stage Return Repair](pokedex_stage_return_repair.md) for the two-frame
negative control and source ownership.

Use a new source-linked core and new checkpoints for each cartridge. Compare
both listing styles and all three orders, cold entry and immediate reentry,
at four physical input phases. Qualify CGB 0/A/B/C/D/E, validate double-speed
restoration, and compare completed maps, attrs, OAM, palettes and viewports.
Audit every native exit frame from LCD re-enable to fade-in: it must remain
white, not merely avoid the old Dex palette signature. Original Reference
and Stage are retained negative controls, not passing alternatives.

The October 13 source adapter freezes original production before game edits
and protects the integrated root ROM during testing:

```sh
python3 -m tools.dex_timing.stage_integration freeze
# Apply the approved Stage source changes, then build the production ROM.
make -s -j6 pokecrystal.gbc
python3 -m tools.dex_timing.stage_integration prepare
python3 -m tools.dex_timing.stage_integration resources
python3 -m tools.dex_timing.stage_integration lifecycle
python3 -m tools.dex_timing.stage_integration lifecycle-audit
python3 -m tools.dex_timing.stage_integration routes
python3 -m tools.dex_timing.stage_integration selected
python3 -m tools.dex_timing.stage_integration exit-matrix
python3 -m tools.dex_timing.stage_integration audio-reference
python3 -m unittest tools.test_pokedex_lifecycle_stage tools.test_dex_return_reveal
```

This dated adapter is specific to the approved four-file source integration;
update its source list and baseline configuration for another change. It adds
336 paired/model lifecycle cases, 36 secondary routes, 88 viewport/hardware
exits and twelve fresh cue comparisons against the approved Stage cartridge.
Secondary routes cover mode cancellation, Pokemon Search, Description,
ancestor Info, Selected Moves, Area, Unown, Type Matchups and Moves Search,
followed by actual overworld movement. Cue parity with the approved Stage is
separate from original-production parity: faster cold preparation changes
entry sound servicing, as retained explicitly in the audio comparison.

Run the full suite from earlier sections as well. The `animations`, `displays`
and `selected` adapter actions rebuild exhaustive battle, six-model Type/Unown,
both 122-song owner stresses and focused Selected acceptance. Final reports
must all carry the integrated ROM hash. The `precomputed` campaign alias names
the retained Selected renderer; Type Matchups still uses its chosen runtime
owner, not the archived precomputed Type implementation.

## 18. Interactive Registration Qualification

The [interactive prototype report](pokedex_interactive_registration_prototype.md)
records the current private link, implementation, approved temporary evolution
data, results and media. A fixed-species registration owner is not equivalent
to a regular Listing entry, and the retained resident New Entry helper matrix
does not qualify its streaming behavior.

Use `tools.dex_timing.interactive_full_regression` to freeze matching baseline
and candidate source, rebuild each to its exact input hash, protect production
and main saves, and execute the standard campaign plus supplementary animation,
display/model, Selected, description, lifecycle, routes, audio, catch-tail and
independent Tower campaigns. It has a locked action ledger; do not run multiple
writers in the same campaign. Original failed logs and retry records must remain
available. Review `orchestration/inventory.json` for the expanded commands and
fixture requirements before starting.

```sh
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_full_regression inventory \
  --base build/interactive-full-FRESH
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_full_regression prepare \
  --base build/interactive-full-FRESH \
  --baseline-source build/dex-position-memory-20261014/candidate \
  --candidate-source build/interactive-registration-dev07-20261015/candidate
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_full_regression run \
  --base build/interactive-full-FRESH --jobs 6
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_full_regression audit \
  --base build/interactive-full-FRESH
```

Its audit intentionally calls this `support_campaign_complete`, not full
qualification. The separately owned all-species registration suite and evolution
audit must also pass. Existing Tower failures must match the frozen baseline;
complete Tower coverage is not synonymous with a clean Tower.

Run the native all-species suite into another fresh directory. Each ROM creates
its own checkpoints. The generated species/form contexts derive from a native
successful-capture donor; they are declared fixtures, not 373 normal wild catches.
Regular Selected controls enter through normal Dex inputs. Initial all-species
content checks, every internal page, all six directed tab pairs, B/End from each
committed page, pending exit attempts, four-phase input stresses and recorded
animation/cry deadlines are separate required dimensions.
The `all` action also replays queued-page checkpoints with physical one-frame
footer taps and combined Right+A, observing actual pending work at the leave
boundary. Pre-input queued state is not interchangeable with dispatch-time
cancellation proof; keep unobserved Description/Info-End cases explicit.

```sh
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_registration_regression all \
  --candidate build/interactive-registration-dev07-20261015/candidate \
  --output build/interactive-tabs-FRESH --jobs 6 --final-link --record
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_registration_regression latency-probes \
  --output build/interactive-tabs-FRESH --jobs 6 --detailed
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.interactive_registration_regression finalize \
  --output build/interactive-tabs-FRESH
```

Require the exact 373-species/398-species-and-form coverage plan, complete
committed exits, 12,736 stress cases, no missing completions, and successful
negative controls. Report latency warnings separately from correctness and
playback failures; do not widen a tolerance to hide a phase-dependent delay.
Compare the 20 declared representative species with identical data on regular
Selected. Report both publication and first subsequent complete displayed
frame, in milliseconds and physical display frames. An earlier identical page
cannot count as a new completion. Checkpoint-replay exit records use independent
time epochs and are not a continuous-session latency dataset.

Special-return integration is separately runnable through
`tools.dex_timing.interactive_registration_returns`; use its CLI help for current
source/output parameters. Cover actual Transform behavior and both Game Corner
scripts, as well as declared contest/Celebi battle types and a separate forced
ID-GC case. Do not describe a declared battle type as full event-script coverage
or a direct collector call as normal-input gameplay.

For contest inventory, `PokeBallEffect.return_from_capture` is the start of
continuation, before `.used_park_ball` decrements the counter. Record the value
there, but require the exact initial ball count minus observed native throws
only after the normal overworld return. Checking consumption at that earlier
label produces the same false failure on the accepted baseline. The October 16
full follow-up preserves both failed runs and the corrected B/End replays;
registration restoration and cancellation assertions remain unchanged.

Every source-aware test must use that link's matching `Repository` and generated
Info/Mov metadata. New evolution rows change page counts. A root-checkout
`Compiler` paired with a private-ROM `Repository` is an invalid mixed oracle and
can crash on otherwise valid pages. Correct both source and expectations without
skipping the new pages; retain and replay the failed native cases.

Run `tools/test_interactive_registration.py` against the frozen candidate, the
linked numeric planner cases through the support runner's `numbers` action,
and `tools/audit_evolution_data.py` against the pinned reference cache. Verify
the context alias boundary, permanent-ID lock restoration, live/dead producer
state, direct-call bank correctness, animation WAITING guard, numeric glyph
parity/budget, shared ISR byte identity, all direct/forward/ancestor/family data,
learnset preservation, ordered-method reachability and audit negative controls.

The review publisher copies only private artifacts, constructs/checks a private
Continue save, and packages silent videos plus unretimed A/B audio. Publishing
does not itself confer a qualification pass. Keep automated checks, human visual
review and human listening approval explicitly distinct.

For no-Dex catches derive `STATUSFLAGS_POKEDEX_F` from the matching source,
inspect the actual `CheckReceivedDex` zero result and require zero registration
entries. Bit 1 is Unown Dex, not Pokedex. The older fixture used the wrong
literal mask and held A could silently dismiss resident registration, producing
a false-positive bypass. Preserve that correction and negative evidence.
Following-catch drivers must also handle a genuinely unseen second encounter
opening registration; do not assume every later catch uses `skip_pokedex` or
pre-mark the species caught to bypass the feature being tested.

### Capture Wallet And Visible Handoff Addendum (2026-10-16)

See [the capture handoff investigation](pokedex_registration_capture_handoff_investigation.md)
for the false Pay Day reproduction, memory alias and independent options.
Capture qualification must snapshot the three-byte big-endian `wMoney` and
`wPayDayMoney`, not just party/EXP/delivery. In no-attack Master Ball fixtures,
require an unchanged wallet after both the first capture and following battle.
The stronger native oracle must pass production and reject the known-bad
interactive prototype; automatically dismissing text is not a money check.

Also seed the context helper with legitimate nonzero amounts and test actual
Pay Day earnings natively, with/without Amulet Coin and at the wallet cap.
Clearing the accumulator to hide the symptom is not an acceptable fix.

Keep capture-tail speed ownership explicit in the candidate contract. The
independent mode-3 experiment intentionally permits an LCD-on switch only at
the verified capture helper return PC, normal-to-double with sound inactive.
Do not globally relax the existing LCD-off/audio-off switch assertions. Preserve
the normal-speed battle animation owner, hidden follow-up battle/map switches,
and the ROM0/shared-interrupt byte-identity controls. The combined prototype's
general runner now permits that narrow exception only when its linked symbols
identify the synchronized helper, its STOP opcode/layout match, and a recorded
mode-3 STOP proves normal speed with sound and interrupts inactive. Old ROMs
without that helper retain the original LCD-off contract. Tutorial and
already-double-speed guard paths must preserve registers and stack state.

Measure completed scanouts and physical time around Gotcha and registration
entry. Capture labeled current/candidate video and separate native soundtracks.
Use independent model boots; emulated CGB revisions do not replace another
core or real-hardware checks. Retain the known Dusknoir introduction cutoff as
a baseline exception, not as a passing complete sample. Human listening and
visual approval remain distinct from automatic block/hash checks.

The repeatable legitimate-earnings supplement is:

```sh
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.registration_payday \
  --baseline build/interactive-registration-fixed-full-20261016/baseline-source \
  --candidate build/interactive-registration-fixed-full-20261016/candidate \
  --output build/registration-payday-FRESH --jobs 6
```

It allocates the real Pay Day move ID in a declared pre-enemy fixture, gives a
level-6 party a level-10 opponent, then uses Pay Day through normal battle input
before catching. Check the actual command, accumulator, registration return,
payout, Amulet Coin multiplier and 999,999 wallet cap in both ROMs. An earlier
fixture accidentally retained the level-32 seed party and knocked out the
opponent; that timeout is not evidence of a capture or speed-switch failure.
`tools/test_capture_handoff.py` independently rejects a wrong LCD phase, active
audio/interrupts, missing STOP evidence, a wrong return PC, and a live reverse
switch. Keep those negative controls when changing the handoff.

For paired capture delivery, independently booted ROMs can generate different
wild DVs before Gotcha. Never silently discard all DV/stat differences. Replay
each matching-ROM `fixture.s0` to the Gotcha callback before the handoff, record
the native enemy DVs/stats, and prove that delivery and map return preserve
those values. Only after that proof may the pair comparator exclude the newly
caught individual's initial DVs/stats (boxed storage has DVs but not party
stats). Keep the existing party and every other delivered field strict. Preserve
the original raw comparison. `gotcha_boundary_review delivery` performs this
104-case proof before `analyze`; the review publisher gates on both reports.
Negative controls must reject changed received DVs/stats and still detect
changes to existing party members, caught moves and pre-delivery snapshots.

The standard current-host comparison reruns only candidate failures against
production; an empty baseline-failure log is not a full baseline run. The
interactive support campaign's `baseline-host` action independently executes
the complete 87-test host group on the frozen production source and records
its real count before final coverage aggregation.

For production promotion, keep the pre-integration source/ROM/symbols frozen.
Pass that source explicitly as `tools/test_interactive_registration.py
--baseline PATH` when checking actual root production with `--root .`.
Do not use the newly promoted root as its own before-baseline: identity and
numeric-copy cost checks would compare the candidate to itself. Retain the
positive-overhead and bounded CPU-cost assertions. The integration driver in
`tools/dex_timing/registration_integration.py` records exact reviewed build
identity, protected-save hashes and fresh root checks. Its first failed
mutable-baseline attempt is preserved separately from the corrected passing
run; the test correction does not change or requalify different ROM bytes.

The all-species registration timing diagnostics must derive their targets from
the current build's actual timing alerts, not a fixed list from an earlier
build. Retain historical alert species as additional controls, match the exact
operation, and decode the linked admission cutoffs. Preserve both the original
continuous-scan deltas and the diagnostic replays: delayed publication during
active playback is a responsiveness warning, not a content or audio failure.

### Selected Footprint Asset Addendum (2026-10-16)

The independently runnable `tools.dex_timing.footprints` suite builds a private
asset-only candidate and boots fresh matching-link Modern/Legacy states. Its
`build`, `prepare`, `host`, `run`, and `qualify` actions cover all 373 species,
both Description pages, Info/Mov, internal paging in both directions and
B-return/reentry. See [the footprint qualification](pokedex_footprint_prototype.md)
for exact commands, source archive and retained native screenshots.

Do not use the converted PNG or linked ROM as the only oracle for new imports:
derive expected mark masks independently from the verified original artwork.
Check source/linked data, uploaded VRAM, actual tile order/bank/palette and all
256 completed-screen pixels, including blank images. Preserve wrong-polarity,
padding, orientation and stale-blank negative controls. Compare the paired
complete screen outside only the actual footprint rectangle; no broad text,
portrait or cursor mask should conceal unrelated differences. Retain the
existing exact authored playback audit while reaching each species.

The supporting banked-Stats cost test needs its frozen unbanked reference;
current production already includes the relocation and cannot measure that
historical +672-cycle delta against itself. Keep that reference distinct from
the fresh production ROM used for native screenshot/playback comparisons.

The registration bank guard still compares ROM0 interrupt/delay bodies and the
whole Dex-dispatch bank. A content/rendering change may relocate normal callee
addresses without adding interrupt instructions: the October 16 follow-up has
five changed immediate bytes in named mainline farcalls before dispatch. Only
those exact caller/callee instruction patterns are normalized against symbols;
all opcodes, handler bytes, other bank bytes and caller positions remain strict.
Wrong call targets and changed interrupt opcodes must fail the two new negative
controls. Never replace this with a broad relocation mask or infer that an
unchanged source filename alone proves unchanged linked interrupt work.

### Selected Scheduling Addendum (2026-10-17)

The Selected Mov wrap-aware admission and twelve-slice prototype is documented
in [the scheduling scope](pokedex_selected_stall_optimization_scope.md).
Preserve the per-slice clock/playback checks, portrait-first service order and
atomic lower-panel publication. Test later pages and wrap, not only first Mov
opening. Tangrowth's second/third pages, Toxicroak's wrap and Togekiss's third
page expose the former scheduling stalls. Include ordinary Selected and the
fixed-species registration owner, active and finished playback, and four input
phases. Compare complete workflows as well as individual buttons: removing an
earlier wait changes the portrait phase at later requests.

The optional Info READY cutoff is 108 instead of 84. Its unchanged guard and
finishing reserve leave 6,186 normal-speed CPU T-cycles at that cutoff.
`test_info_ready_staging_fits_its_declared_budget` runs the complete READY
service for two pages with a healthy sampled-cry cache, checks the staging
transition, and checks stack/WRAM bank restoration. This is a bounded staging
test, not permission to relax heavy Info states or interrupt publication gates.
Re-measure after changes to palette/OAM staging, bank calls or service overhead;
retain native animation/sample deadline audits in addition to the CPU test.
The current matrix has 36 combinations: Stats/evolution pages, zero/two active
miniatures, inactive/exact-threshold/healthy sampled caches, and caller WRAM
banks 1/3/5. Preserve per-case CPU costs; its maximum is 4,216 T-cycles against
the 6,186-T budget at cutoff 108.
The all-scanline Info host test must derive the supported READY cutoff from the
linked table (84 or 108) instead of rejecting every line at or beyond 84. Test
the audio/portrait/clock guards at the last admitted line of that same policy;
neither arbitrary cutoff values nor a failed staging-cost bound are accepted.

The dispatch-bank relocation guard now also recognizes the exact mainline
`PokedexBadge_Prepare` farcall inside the Description-badge window. Its target
can move with other ROMX code; no handler instruction is masked. A separate
wrong-badge-target negative control must fail, alongside the existing wrong
call-target and interrupt-opcode controls. The current context suite has
fourteen tests; preserve and investigate older failed receipts rather than
overwriting them after a harness correction.
