# Unown Performance Prototype

Review and production integration date: 2026-10-12. The approved v5 prototype
is now integrated into production. The prototype comparisons below refer to
the pre-integration production baseline; see Production Integration for the
current build and fresh promotion checks.

## Review Build

- Candidate: `build/dex-unown-fast-20261012-v5/`.
- Review ROM and matching all-26-forms battery:
  `build/dex-unown-fast-20261012-v5/all-unown-review/pokecrystal-dex-unown-fast.gbc`
  and `.sav`.
- Rollback ROM/symbol/map: candidate `rollback/` directory.
- Rollback source: candidate `rollback-source.tar`.
- Pre-integration production commit: `b4eef5991c8021c877585ef4a28a14cbea4e7573`.
- Pre-integration production ROM SHA-256:
  `469f7db4ed492e3d44fc29cd6bd0dbc51d1f5e5671732861c98a81623a747cac`.
- Candidate ROM SHA-256:
  `6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac`.

The review save is a copied test fixture, not a modification to the player's
save. Select Unown from the Dex mode menu, then hold or tap Left/Right. Return
with A/B and check the original Pokemon listing and selection.

## Old Path And Change

`Pokedex_LoadUnownFrontpicTiles` previously used generic `GetMonFrontpic`,
followed by two explicit redraw delays in
`Pokedex_UnownModeHandleDPadInput`. The generic loader prepares the complete
animation dictionary and uploads via `Request2bpp` in small frame-paced
batches. The Unown page never plays that animation: its native frontpics are
25 tiles, but dictionaries contain 32-46 tiles. Consequently, it pays for
unused animation data and visibly replaces the portrait piecemeal.

The private CGB path instead:

1. Preserves the existing caught-form lookup, permanent/transient species
   conversion, selected-species lock, and original `wUnownLetter` restoration.
2. Selects Unown's base data, decodes only the static base image, and pads it
   into the existing aligned WRAM0 7x7 portrait buffer.
3. Updates the software cursor and Unown word and stages the 20x18 map into
   the existing bank-3 owner tilemap buffer, retaining its 32-tile row stride.
4. Publishes the 784-byte portrait and 576-byte map together with CGB
   general-purpose DMA during one VBlank. The old complete display remains
   visible until the prepared replacement is ready.
5. Returns to the ordinary owner loop without the two redundant redraw delays.

The initial entry uses the same prepared-picture publication before the
existing palette/reveal sequence. The DMG fallback retains the original
loader and delays; this prototype's performance claim is for CGB.

No cache warming, extra animation owner, new OAM, palette changes, or artwork
is introduced. The existing red background and solid black glyph panel remain.

## Placement And Cost

The complete Unown system does **not** need its own reserved ROM bank.
The publisher is in its own linkable section (currently bank `$01`); the
decoder shares the graphics-helper bank (`$14`) so its pointer/padding calls
are ordinary local calls. Existing Unown state handling stays in bank `$10`.

Net linked cost: **247 ROMX bytes**. ROM0, WRAM0, WRAMX, HRAM and SRAM all add
zero bytes; all existing RAM addresses remain unchanged. No new assets.

The original private sources are `tools/dex_timing/probes/unown_fast.asm`,
`unown_decode.asm`, and `unown_fast.diff`. The build recipe copies them into
the candidate's `engine/pokedex/` and patches only candidate `main.asm` and
`engine/pokedex/pokedex.asm`. It rejects tracked game-code modifications and
verifies that production binaries were not changed by the build.

## Timing And Atomic Publication

Native SameBoy measurements use normal button input, 26 forms in both
directions, both Modern/Legacy entry origins, and four within-frame input
phases. Time is emulated physical time from button press, not host CPU time.

| Selection Metric | Pre-Integration Production | Candidate |
| --- | ---: | ---: |
| Complete display, median | 199.38 ms | 49.02 ms |
| Complete display, maximum | 216.14 ms | 65.76 ms |
| Next input loop, median | 198.26 ms | 50.23 ms |
| Held Right for 60 hardware frames | index 6 | index 10 |

Median completion improves approximately **75.4%**, or **4.07x**. A normal
selection completes in about three display frames instead of twelve. Holding
Right is still limited by the existing owner/controller cadence; it is not
one selection per frame.

Fresh ordinary-list comparisons use six starting indices (0/8/24/100/255/371)
and four physical input phases per style, in both production and candidate:
96 rows / 48 pairs. They cover representative selection and scrolling steps;
these are not identical workloads to a one-form Unown step.

| Candidate Listing | Portrait Median | Whole-Display Median | Largest Paired Delta |
| --- | ---: | ---: | ---: |
| Modern | 75.97 ms | 101.11 ms | 0.00 ms |
| Legacy | 75.61 ms | 75.61 ms | 0.00 ms |
| Unown | 49.02 ms | 49.02 ms | intentional improvement |

Modern's whole-display metric includes the mini-icon animation state;
portrait-only latency excludes that ongoing motion and the scrollbar. Unown
is at least comparably responsive in these measurements, with its entire
static selection published together. All 512 ordinary Dex entry pairs also
match production first/complete display timing exactly, across 16 species,
four hover durations and four physical phases per style.

The publisher arms at LY 143 with interrupts enabled until that point, then
disables interrupts briefly and starts DMA at LY 144/145. A missed start
deadline retries on the following frame, retaining the old whole display.
All observed commits start at LY 144, end at LY 150, and take at most
0.688 ms. All six emulated CGB revisions (0/A/B/C/D/E) produce the same
112-case timing ranges. Whole-frame hashes and native screenshot sequences
show only old or new complete selections, never mixed publication frames.

**Ownership contract:** this routine is mainline-only, with the LCD running,
interrupts initially enabled, Window hidden, BG0 owning the screen, BG updates
stopped, and no competing DMA/animation owner active. Existing scratch buffers
must be exclusively owned. It restores incoming VRAM/WRAM bank selectors and
re-enables interrupts before returning. Do not reuse it from an interrupt,
from an animated portrait owner, or from another screen without rechecking
all of these preconditions and the VBlank byte budget.

The ordinary LCD handler, VBlank dispatch, normal VBlank handler, generic
frontpic loader, and `Request2bpp` executed instruction ranges compare
byte-for-byte with production. No new branch or call is added to their shared
executed paths. See the
[Battle Animation Interrupt Timing Contract](battle_animation_interrupt_timing_contract.md).

## Qualification

Focused final-link evidence:

- Six CGB model sweeps, 112 normal-input selection cases per model, four input
  phases, eight return paths per model, and unchanged private/donor batteries.
- Unown visual suite: 136 scenarios, 2,212 form selections, 126 draw-unit cases,
  and the retained negative controls; zero failures.
- Decoder fixtures: 156 cases covering every form after previously viewing
  5-, 6-, and 7-tile Pokemon, original letters 1/26, exact padded bytes,
  species/form identity, and ROM/WRAM/stack/SRAM restoration; zero failures.
- Type Matchups: all six CGB models, every type, chart/raster/palette checks,
  42 owner reentries, 12 close/reopen paths, and 24 subsequent Selected-owner
  playbacks; no new failures or white flashes.
- Pokemon Dex qualification: 4,479 scenarios, zero failures.
- Two host unit tests ensure the Unown return oracle reads its actual centered
  portrait, resident glyph font, and blank tile rather than another owner's
  portrait location.

The final campaign completed with no new regressions:

- Moves search: 1,692 filter contracts, 10 normal-input flows, 1,406 visual
  sweeps, 2,686 navigation cases, 11 transition cases, 1,284 form-polish
  cases, and 3,840 naming-cursor checks.
- Sort memory: 4,096 helper cases, 16 UI cases, and 11 save cases.
- Persistence: 2,380 helper cases, 1,490 cold boots, 152 interrupted writes,
  150 interrupted repairs, four snapshots and five lifecycle cases;
  migration and its separate 150 interrupted-write cases also pass.
- Surrounding gameplay: 10 menu scenarios, 22 gameplay scenarios, two nested
  custom-menu campaigns, and 24 speed/ownership transition scenarios.
- Audio: 960 candidate/baseline cases; sampled-cry segments retain the same
  32 known timing misses with no new identities.
- Standard 100-move battle matrix: 1,600 cases, both sides, four phases, both
  links, with no candidate/baseline differences.
- Selected playback: all 373 species in cold/paging/warm suites in both
  styles, 2,238 cases total; zero failures.
- Ordinary listing idle checks, 1,024 entry timing rows / 512 pairs,
  96 listing-selection timing rows / 48 pairs, and 48 additional Info-owner
  selection measurements; no new functional failures or ordinary-Dex slowdown.

Valid load, legacy load, full legacy migration, and recovery timing match
exactly. Normal save measures 150.4505 ms versus production's 150.4400 ms:
**+0.0105 ms**, without an added display frame. Do not describe every
non-Unown measurement as bit-identical.

The 86-case linked host suite has zero errors and retains one exact baseline
failure: `InfoLinkedTests.test_ready_handoff_obeys_the_active_playback_budget`
at LY 64 (`5 != 0`). This is recorded as an existing failure, not a passing
check or a regression introduced by Unown.

Current evidence is in `build/dex-unown-fast-20261012-v5/` (performance,
decoder tests, CGB models and Type returns) and
`build/dex-unown-fast-regression-20261012-v5/` (campaign statuses and detailed
regression/timing reports). The final `unown-campaign.json` records zero exit
statuses for all scheduled phases. The subsequent 96-row Modern/Legacy
listing comparison replaces the initial Legacy-only timing report.

A clean second build reproduces the candidate ROM, symbols and map exactly.
Completed v4/v5 menu traces were losslessly compressed from 18.10 GB to
0.49 GB; every decompressed stream was SHA-256 verified before replacement.
The compression receipt is `menu-trace-compression.json` in the final campaign.
Review ROMs, saves, sources, rollback, native screenshots and reports remain
available. Compressed trace filenames append `.gz`; their contents are unchanged.

### Bugs Caught While Prototyping

An early trial could miss the VBlank start after the ordinary interrupt won
the race, causing inconsistent input latency. The LY-143 arming boundary
eliminates that race without adding work to the interrupt handlers.

A later trial used the previous Pokemon's base-picture dimensions on initial
entry. The generic loader used to refresh `wCurSpecies` and base data itself;
the replacement must do that explicitly **before** reading `wBasePicSize`.
The final decoder does so. The earlier v4 decoder fails the expected 104
larger-picture fixture cases, while final v5 passes all 156, demonstrating
that the added regression detects the defect. Do not distribute earlier trial
ROMs as the review candidate.

The Type return oracle also needed correction: generic `ui.picture` observes
another owner's portrait coordinates. The Unown check now compares its actual
base tiles and resident font/blank bytes, while map, attributes and palettes
remain checked. This is not a blanket exclusion of portrait correctness.

## Production Integration

The approved v5 source was promoted without changes to:

- `engine/pokedex/pokedex_unown_static.asm`: private atomic publication.
- `engine/pokedex/pokedex_unown_decode.asm`: static base-picture decoding.
- `engine/pokedex/pokedex.asm`: initial publication, selection publication,
  and CGB loader call sites; the original DMG fallback remains.
- `main.asm`: the publisher section and graphics-bank decoder include.

The root `pokecrystal.gbc`, `.sym`, and `.map` were rebuilt and each matches
the corresponding approved v5 output byte-for-byte. Current production ROM
SHA-256:
`6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac`.
The linked cost remains 247 ROMX bytes with no new RAM allocation or assets.
No shared interrupt or generic frontpic execution path was changed.

Fresh checks against the actual root production build:

- 112 normal-input Unown selections on CGB E, all 26 forms, both directions,
  Modern/Legacy origins and four input phases; no partial portrait or display
  publication. Median complete display is 49.02 ms, maximum 65.76 ms.
- Eight return paths restore the original listing and form state; held-input
  behavior and private/donor battery checks also pass.
- 156 decoder fixtures pass, including initial entry after 5-, 6-, and
  7-tile Pokemon; zero failures.
- 88 linked host checks, zero errors or skips, and no new failures. The exact
  existing Info LY-64 assertion (`5 != 0`) remains documented above.

The broader final-v5 qualification remains applicable through exact ROM,
symbol, map, and integrated-source identity. The full campaign was completed
before approval; it was not rerun after this byte-identical promotion.

Integration evidence is in `build/dex-unown-production-20261012/`, including
`integration.json`, `host.json`, `performance/summary.json`, and
`decoder-tests/summary.json`. Its `candidate` entry is a symlink to the root
workspace used for the fresh decoder checks, not a frozen source snapshot.
The old production ROM/symbol/map and affected source files are preserved in
its `rollback/` directory, with the pre-integration HEAD archive in
`rollback-source.tar` and initial hashes in `before.json`.

No player save was modified. Unrelated workbook changes were left untouched.
No commit or staging was performed; the production source is ready for the
user's commit.

## Reproduction And Limits

The original private build recipe below must start from the pre-integration
commit listed above in a clean checkout. It applies the old-to-new patch and
must not be applied again to integrated production. Use fresh output
directories and the retained fixtures described in
[Full Regression Suite](full_regression_suite.md):

```sh
export PYTHONPATH=tools:.
python3 tools/build_unown_performance_prototype.py --output build/unown-new-review
python3 -m tools.dex_timing.unown_performance --source build/unown-new-review/candidate --output build/unown-new-review/performance
python3 -m tools.dex_timing.unown_decoder --source build/unown-new-review --output build/unown-new-review/decoder-tests
python3 -m tools.dex_timing.type_full_regression prepare --source build/unown-new-review --output build/unown-new-regression
python3 -m tools.dex_timing.unown_fast_campaign final --output build/unown-new-regression
python3 -m tools.dex_timing.type_matchups --output build/unown-new-review --all-models
python3 -m unittest tools.test_type_matchups_owner_snapshot
```

To repeat the normal-input check against the current production build from
the repository root:

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.unown_performance --source . --rom pokecrystal.gbc --sym pokecrystal.sym --battery build/dex-unown-fast-20261012-v5/all-unown-review/pokecrystal-dex-unown-fast.sav --output build/unown-production-recheck
```

All timing and display evidence is emulator-based, not a physical cartridge
test. This round uses the standard 100-move battle campaign; it does not
repeat the separate exhaustive 333-move animation-renderer campaign.
Static Unown behavior is intentional; adding animated frontpics later would
require revisiting this exclusive buffer ownership and publication design.

Environment: Python 3.13.12, RGBDS 1.0.1, Apple Clang 17.0.0 on arm64 macOS;
SameBoy source revision `98da08c3117a7bf39c7329fc662c0d18cb54707d`.
