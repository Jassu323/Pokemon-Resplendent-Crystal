# Pokedex Lifecycle Optimization Within The Space Budget

Date: 2026-10-13. Follow-up to
[the initial lifecycle review](pokedex_lifecycle_performance_review.md), for
`DEX-PERF-01`. These are private diagnostic prototypes, not production changes.

## Manual Review Follow Up

The user rejected original Reference and Stage because of two premature
colored frames on exit, and Hard Cuts because of distorted cues. The final
UI comparisons below did not establish correct mid-transition reveal order.
Frame-by-frame review now confirms the original Reference/Stage defect in all
48 cases each. Preserve these tables as historical timing/resource comparisons,
not as approval of those versions.

The user selected
[Stage with a committed white mask](pokedex_stage_return_repair.md) after
manual review. Source integration uses 96 ROMX bytes (the diagnostic projected
102), no new static RAM, and retains normal fades. Fresh full qualification
is complete with no new issues; the original candidates below remain
historical comparisons.

## Initial Recommendation

Keep the current fades and use the isolated cold-entry, LCD-off restoration,
fused font conversion and local sound-clock accounting implementation
(`music-best`). Its projected additional allocation is **712 ROMX bytes and
5 WRAMX bytes**, with no additional ROM0, HRAM or statically allocated WRAM0.
Median entry is **354.1 ms / 21.15 display frames** and exit is
**669.2 ms / 39.97 frames**, versus production's 778.0 / 46.47 and
860.6 / 51.40 respectively.

Paired median savings versus production are **423.9 ms / 25.32 frames on
entry** and **191.6 ms / 11.44 frames on exit**. Versus the earlier 92-byte
recommendation, the savings are **158.7 ms / 9.48 frames** and
**24.1 ms / 1.44 frames**. This is a meaningful improvement inside all four
requested limits without duplicating fonts or changing shared interrupts.

Two useful alternatives remain:

- Minimal implementation: `stage`, about 99 ROMX bytes and zero new RAM,
  reaches 444.7 ms / 26.56 frames on entry and 693.1 ms / 41.40 on exit.
- Faster presentation: `music-short`, 777 ROMX bytes and 5 WRAMX bytes,
  reaches 287.2 ms / 17.15 frames and 603.4 ms / 36.04. It changes the fade
  cadence, so this is a visual preference, not a free engineering gain.

The 822-byte unrolled option fits too, but its additional 110 bytes buy only
2.9 ms / 0.17 frames on entry and 1.4 ms / 0.08 frames on exit relative to
`music-best`. Keep the compact loops unless that small gain is worth the space.

## Measurement Contract

One display frame is 70,224 emulated T cycles at 4,194,304 Hz:
**16.742706 ms**. Timings measure physical emulated display time, not host
execution speed. Double CPU speed is already the game's normal policy; these
prototypes do not introduce a CPU-speed switch.

Input-to-ready starts at the normal A or B request and ends at the native
Listing or Start-menu input loop. It includes input polling, fades, graphics
work, cleanup and the complete exit sound. It is not merely the time until
the first different pixel. Frames can be fractional because function and
input boundaries can occur partway through a display interval.

Each design has 48 matched cases: Modern and Legacy, all three Pokemon sort
orders, four input phases, and first entry plus immediate re-entry. Medians
are over those cases. Delta medians are calculated from each matched pair;
they need not equal the subtraction of the two absolute medians. Small
phase-dependent changes in a wait are real, even when the code path is equal.

ROM costs below are conservative source projections for additional occupied
ROMX, not the cartridge file size. The prototypes are address-stable binary
overlays, which retain some abandoned diagnostic code and compatibility
trampolines. Final costs must be confirmed from a production source link.
No unreferenced-code reclamation is credited. All costs include the earlier
92-byte entry/exit recommendation where applicable, rather than being on top
of it. The reference's 57-byte close helper is replaced, not counted twice.

All designs add zero static WRAM0, ROM0 and HRAM allocations. They call existing
helpers and reuse existing tilemaps, attributes, OAM, scratch and register
mirrors. The clock helper temporarily pushes five register pairs, about
10 stack bytes in the existing stack; this is not a new persistent RAM0 buffer.
Only the four `music-*` designs allocate WRAMX, five bytes each. No SRAM or
save-format changes are involved.

## Complete Timing And Allocation Comparison

`ms / f` means milliseconds / display frames. Lower is better.

| Private design | ROMX bytes | WRAMX bytes | Entry median, ms / f | Exit median, ms / f |
| --- | ---: | ---: | ---: | ---: |
| Current production (`baseline`) | 0 | 0 | 778.0 / 46.47 | 860.6 / 51.40 |
| Earlier recommendation (`reference`) | 92 | 0 | 513.0 / 30.64 | 693.0 / 41.39 |
| Staged layout (`stage`) | 99 | 0 | 444.7 / 26.56 | 693.1 / 41.40 |
| Single cold build (`cold`) | 359 | 0 | 359.4 / 21.46 | 693.1 / 41.40 |
| Cold build and local LCD-off exit (`cold-exit`) | 394 | 0 | 359.8 / 21.49 | 669.4 / 39.98 |
| Runtime fused font (`font-fused`) | 167 | 0 | 505.3 / 30.18 | 693.0 / 41.39 |
| Duplicated preconverted font (`font-prepared`) | 2163 | 0 | 509.0 / 30.40 | 693.0 / 41.39 |
| Cold build and fused font (`cold-font`) | 434 | 0 | 351.7 / 21.01 | 693.1 / 41.40 |
| Cold build, exit and fused font (`cold-exit-font`) | 469 | 0 | 352.2 / 21.04 | 669.4 / 39.98 |
| Short fades without fused font (`short-fades`) | 459 | 0 | 293.0 / 17.50 | 604.0 / 36.07 |
| Hard cuts without fused font (`hard-cuts`) | 437 | 0 | 242.8 / 14.50 | 560.6 / 33.48 |
| Preconverted font and GDMA (`font-gdma`) | 2179 | 0 | 500.2 / 29.88 | 693.0 / 41.39 |
| Cold build with font GDMA (`cold-font-gdma`) | 2446 | 0 | 346.6 / 20.70 | 693.1 / 41.40 |
| LCD-on restoration (`lcd-exit`) | 530 | 0 | 359.8 / 21.49 | 1906.5 / 113.87 |
| LCD-on restoration overlapping sound (`lcd-overlap`) | 527 | 0 | 360.1 / 21.51 | 1621.9 / 96.87 |
| Cold-only font coordinator (`isolated-best`) | 551 | 0 | 352.2 / 21.04 | 669.4 / 39.98 |
| Cold-only coordinator and short fades (`isolated-short`) | 616 | 0 | 285.4 / 17.05 | 604.0 / 36.07 |
| Recommended, with sound clock (`music-best`) | 712 | 5 | 354.1 / 21.15 | 669.2 / 39.97 |
| Sound clock and short fades (`music-short`) | 777 | 5 | 287.2 / 17.15 | 603.4 / 36.04 |
| Sound clock and hard cuts (`music-hard`) | 755 | 5 | 237.1 / 14.16 | 552.5 / 33.00 |
| Sound clock and unrolled loops (`music-unrolled`) | 822 | 5 | 351.2 / 20.98 | 667.8 / 39.88 |

### Paired Timing Deltas

Negative values are faster. Every cell is **ms / display frames**. Values
rounding to zero represent negligible sub-frame differences, not a removed
or inserted full display interval.

| Design | Entry vs production | Exit vs production | Entry vs earlier recommendation | Exit vs earlier recommendation |
| --- | ---: | ---: | ---: | ---: |
| `reference` | -265.3 / -15.85 | -167.9 / -10.03 | 0.0 / 0.00 | 0.0 / 0.00 |
| `stage` | -333.0 / -19.89 | -167.4 / -10.00 | -67.6 / -4.04 | +0.1 / 0.00 |
| `cold` | -418.4 / -24.99 | -167.8 / -10.02 | -153.2 / -9.15 | 0.0 / 0.00 |
| `cold-exit` | -418.1 / -24.97 | -191.5 / -11.44 | -152.9 / -9.14 | -23.6 / -1.41 |
| `font-fused` | -273.0 / -16.30 | -167.9 / -10.03 | -7.6 / -0.46 | 0.0 / 0.00 |
| `font-prepared` | -269.3 / -16.08 | -167.9 / -10.03 | -3.9 / -0.24 | 0.0 / 0.00 |
| `cold-font` | -426.0 / -25.45 | -167.8 / -10.02 | -160.8 / -9.61 | 0.0 / 0.00 |
| `cold-exit-font` | -425.8 / -25.43 | -191.5 / -11.44 | -160.6 / -9.59 | -23.6 / -1.41 |
| `short-fades` | -485.0 / -28.97 | -257.0 / -15.35 | -219.8 / -13.13 | -89.2 / -5.33 |
| `hard-cuts` | -535.3 / -31.97 | -300.2 / -17.93 | -270.1 / -16.13 | -132.2 / -7.90 |
| `font-gdma` | -278.1 / -16.61 | -167.9 / -10.03 | -12.7 / -0.76 | 0.0 / 0.00 |
| `cold-font-gdma` | -431.1 / -25.75 | -167.8 / -10.02 | -165.9 / -9.91 | 0.0 / 0.00 |
| `lcd-exit` | -418.2 / -24.98 | +1045.9 / +62.47 | -153.0 / -9.14 | +1213.5 / +72.48 |
| `lcd-overlap` | -418.0 / -24.97 | +761.2 / +45.47 | -152.8 / -9.13 | +928.9 / +55.48 |
| `isolated-best` | -425.8 / -25.43 | -191.5 / -11.44 | -160.6 / -9.59 | -23.6 / -1.41 |
| `isolated-short` | -492.7 / -29.43 | -257.0 / -15.35 | -227.5 / -13.59 | -89.2 / -5.33 |
| `music-best` | -423.9 / -25.32 | -191.6 / -11.44 | -158.7 / -9.48 | -24.1 / -1.44 |
| `music-short` | -490.9 / -29.32 | -257.3 / -15.37 | -225.7 / -13.48 | -90.5 / -5.41 |
| `music-hard` | -540.9 / -32.30 | -308.3 / -18.41 | -275.7 / -16.46 | -140.5 / -8.39 |
| `music-unrolled` | -426.8 / -25.49 | -193.0 / -11.52 | -161.6 / -9.65 | -25.5 / -1.52 |

### Ranges For The Final Choices

| Design | Entry min-max, ms / f | Exit min-max, ms / f |
| --- | ---: | ---: |
| `music-best` | 342.6-380.3 / 20.46-22.71 | 668.5-670.0 / 39.93-40.02 |
| `music-short` | 275.0-313.3 / 16.42-18.71 | 601.6-618.8 / 35.93-36.96 |
| `music-hard` | 226.8-263.4 / 13.55-15.73 | 551.2-552.7 / 32.92-33.01 |
| `music-unrolled` | 339.7-377.4 / 20.29-22.54 | 667.1-668.7 / 39.85-39.94 |

The short-fade exit has a phase-sensitive tail about one display interval
above its typical value. It still improves every matched exit versus the
earlier recommendation. Changing fade cadence does not change frame rate.

## What Each Approach Changes

### Staged Layout

Reuse `CGB_PokedexStageListLayout` instead of immediately applying and waiting
for the cold layout. The Listing subsequently publishes the same attributes
anyway. The private 7-byte calling adapter explains the increase from 92 to
99 bytes; a source link may need less. This is low complexity and the best
tiny-space alternative, saving another 67.6 ms / 4.04 frames on entry versus
the earlier recommendation. Preserve the normal update/restoration layouts;
only initial cold setup has this redundant wait.

### Single Cold Build

Keep the LCD off through initial Listing preparation. Prepare the grid or
Legacy list, selected name, sidebar, portrait, tilemaps, attributes, palettes,
physical viewport registers and OAM before enabling it once. Copy the existing
20x18 maps directly while the LCD is off instead of repeatedly waiting for
the live display to accept them. Continue through the native Listing input
loop with the existing Dex VBlank owner, mode 7. The regular return/update
paths are not replaced by this cold-only builder.

This is moderate, local display-owner complexity. The important invariant is
that all maps, palette banks and OAM are physically ready at reveal, not merely
that their software mirrors have been written. Future additions to the cold
Listing must also be included in that preparation. No new font atlas or map
buffer is required, and no shared VBlank/STAT/Timer code changes are needed.

### Local LCD Off Restoration

The Dex-only close coordinator keeps the full `WaitSFX`, late white-mask
request, species-ID cleanup and overworld reconstruction. It reloads fonts,
sprites, time-of-day palettes, metatiles and tileset graphics while the LCD
is off, restores menu state, directly copies the resulting maps, commits
white palettes, then enables the LCD and runs the normal fade.

It saves about 23.6 ms / 1.41 frames over the earlier closing coordinator.
Complexity is moderate because the local sequence must stay in step with
required shared restoration behavior. The cost is ownership duplication,
not a faster but incomplete map reload. Keep non-CGB fallback behavior on
the original shared close path. Other menus continue using shared code.

### Runtime Font Conversion And Isolation

The existing inverted font path first expands 1bpp glyphs and then converts
the resulting planes. The fused runtime loop reads the original 1bpp font
and writes the final `[0, inverted glyph]` bytes directly. It saves about
7.6 ms / 0.46 frames without storing new glyphs. Additional code is 75 bytes
including the private calling adapter.

The early font trials replace the Dex's shared graphics loader. The final
choices instead copy its 82-byte coordinator for cold entry only and restore
the original `Pokedex_LoadGFX` bytes. New Dex Entry and other callers remain on
the original path. This isolation costs code but reduces the behavioral scope
and makes the recommendation a lifecycle-only change.

### Five Byte Sound Clock

Longer LCD-off preparation pauses normal VBlank music updates. The no-clock
trials are useful performance ablations, but do not compensate for that
additional pause. The recommended version uses existing TIMA reads to account
for elapsed preparation and calls the existing `SkipMusic` for whole missed
music updates. It retains the old graphics loader's existing sound catch-up.

The five WRAMX bytes hold the previous TIMA sample, a two-byte fractional
remainder, a whole-update count and a validity flag. They are initialized on
every cold entry; no save persistence, migration or New Game clearing is
needed. The diagnostic uses verified unallocated bank-2 space; production
must declare a normal named RAM section rather than hardcode its address.

Its code/checkpoints cost 161 bytes over `isolated-best`. Entry costs about
1.9 ms / 0.11 frames versus that no-clock ablation. It checks the current
native double-speed, TAC=4, TMA=0 policy and disables extra catch-up when those
assumptions do not hold. That fallback avoids using an invalid calculation;
it does not prove music timing remains correct under a future timer policy.

This is the principal additional maintenance risk. Unsigned TIMA differences
are reliable only when checkpoints are less than one wrap apart. The current
wrap is 31.25 ms / 1.87 display frames. The worst measured checkpoint interval
across all final designs, sort orders and CGB models is 27.09 ms / 1.62 frames.
There is only about 4.16 ms / 0.25 frames of margin. If added species, changed
portrait work or other preparation lengthens that interval, add another local
checkpoint or rework the time source. Retest after timer-policy changes.

The checkpoint preserves AF/BC/DE/HL and restores its selected WRAM bank;
existing far-call machinery restores the ROM bank. It adds no interrupt or
global frame-counter overhead. Qualification verifies the accumulator and
timer assumptions, not waveform identity across all music tracks. Audible
review and broader sound/gameplay regression remain integration requirements.

### Short Fades And Hard Cuts

The short-fade implementation preserves all four palette steps but holds each
for one frame instead of two. Relative to `music-best`, it saves a paired
67.0 ms / 4.00 frames on entry and 65.8 ms / 3.93 frames on exit. Additional
space is 65 bytes. The code change is small and local, but the transition feels
quicker and deserves manual review.

Hard cuts remove the gradual fade and use a one-frame transition. They save
116.4 ms / 6.95 frames on entry and 117.4 ms / 7.01 frames on exit relative to
`music-best`. They preserve the complete exit sound but change presentation
more substantially; they are not the default recommendation.

### Unrolled Loops

The final compact-loop comparison unrolls map columns and processes two font
tiles per iteration. It costs 110 additional bytes for 2.9 ms / 0.17 frames
entry and 1.4 ms / 0.08 frames exit savings. It has low algorithmic risk but
slightly longer code to maintain. It still uses five clock bytes and the
current fades. This is a diminishing-return comparison, not a required step.

## Alternatives Outside The Budget Or Not Worth Pursuing

Preconverting the font stores an extra 2,048-byte glyph set. CPU copying it
costs 2,163 bytes total yet saves only 3.9 ms / 0.24 frames versus the earlier
recommendation, less than the smaller fused runtime loop. An LCD-off GDMA
copy costs 2,179 bytes and saves 12.7 ms / 0.76 frames versus that reference.
Combining it with cold entry costs 2,446 bytes, exceeding the ROMX cap by
1,422 bytes. It beats comparable cold fused conversion by only about
5.1 ms / 0.30 frames on entry. These options allocate no extra WRAMX, but
their duplicated graphics are not a good balance here.

Keeping the LCD on throughout restoration retains normal VBlank sound
service, but native queued font/sprite uploads become much slower. The tested
exit is 1,906.5 ms / 113.87 frames. Overlapping the full sound with that work
reduces it to 1,621.9 ms / 96.87 frames, still 761.2 ms / 45.47 frames slower
than production. Both final trials restore correct graphics, but they are
poor performance options without a much broader upload rewrite. They do not
justify that added complexity for this story.

The full exit effect remains about 283.8-284.0 ms / 16.95-16.96 frames across
the designs' median channel-active measurements. No recommended implementation
truncates it. It is now a substantial intentional part of exit time; further
large exit gains would require a sound/presentation decision or different
overlap, not simply removing another redundant font wait.

## Validation And Limits

- 1,008 lifecycle cases across 21 designs, with zero unexpected final UI
  differences; both entries and exits are measured in each case.
- 252 independent frame-sequence comparisons across the six first-entry
  configurations per design: static final pixels match, with no reversion
  after the destination appears.
- 352 detailed exit cases: 88 each for `music-best`, `music-short`,
  `music-hard` and `music-unrolled`; zero displaced colored frames, rejected
  palette writes or blocked VRAM writes.
- 576 sound-clock qualification cases: all four final choices, all six
  supported CGB models (0/A/B/C/D/E), Modern/Legacy, three sort orders and
  four input phases. Exact clock accumulators, valid timer policy, mode-7
  restoration and Modern icon animation pass.
- 36 focused secondary-route cases, comparing production with `music-best`:
  mode cancel, Pokemon Search/results, Moves Search/results, Description,
  Info/ancestors, Selected Moves, Area, Unown and Type Matchups. Return to
  Listing, menu and overworld/re-entry checks pass.
- 14 host audit tests pass, including negative tests proving the allowed
  water-palette phase cannot hide real palette, geometry or OAM errors.

Final-state comparison permits only known animated grid-icon phases, the
strictly hidden Window regions and the returned map's native water-palette
phase. Water animation can rotate color 0 of BG palette 3 among that palette's
existing three colors; no other palette bytes may change. Pixel comparisons
also ignore only animated icon rectangles, the menu arrow and map cells using
that water palette. Maps, attributes and OAM geometry are independently checked.

Independent first-entry captures measure the completed static Listing, not
input readiness. For the six captured configurations, production reaches it
at median 790.2 ms / 47.20 frames and `music-best` at 380.3 ms / 22.72 frames.
The restored static menu appears at 844.4 ms / 50.44 frames and
653.8 ms / 39.05 frames respectively. These use a smaller first-entry-only
population, unlike the 48-case figures including re-entry, and should not be
mixed into the input-readiness table.

This is focused diagnostic qualification, not the complete production
regression suite. All-move battle animation timing, all-species cries, normal
saving/loading, broad maps/time-of-day and all secondary-owner details must
be rerun after source integration. Shared fixed-bank code is byte-identical
in all diagnostic ROMs except the cartridge checksum header. Production ROM,
symbols and map remain unchanged.

## Video And Review ROMs

The side-by-side recording compares production with `music-best`, using the
same copied save, sort order and requested input time. It contains Modern and
Legacy entry and exit at real speed, followed by a clearly labeled half-speed
Modern replay. On-screen times are native input-to-ready measurements for
those individual recordings, not the pooled medians above. Game pixels are
unfiltered integer nearest-neighbor enlargement. The video is silent.

Measured individual video runs; each timing is **ms / display frames**:

| Recording | Production | Balanced prototype | Saving |
| --- | ---: | ---: | ---: |
| Modern entry | 793.5 / 47.39 | 370.1 / 22.10 | 423.5 / 25.29 |
| Modern exit | 860.2 / 51.38 | 669.5 / 39.99 | 190.7 / 11.39 |
| Legacy entry | 773.2 / 46.18 | 357.3 / 21.34 | 415.9 / 24.84 |
| Legacy exit | 860.7 / 51.41 | 670.1 / 40.03 | 190.6 / 11.38 |

The video is 17.80 seconds, 1,063 frames at the native 59.7275 Hz cadence,
1080x720 H.264. Captures continue for 120 native frames after readiness,
preserving the live icon/menu animation while the slower side catches up.

Video: `build/dex-lifecycle-budget-20261013/video/production-vs-balanced-prototype.mp4`.
Recording timings, ROM hashes and alignment are in adjacent `recordings.json`
and `video-receipt.json`. No fade or blank duration is edited out.

Review ROMs and matching private copied saves:

- Current fades: `build/dex-lifecycle-budget-20261013/music-best/pokecrystal-diagnostic.gbc`.
- Short fades: `build/dex-lifecycle-budget-20261013/music-short/pokecrystal-diagnostic.gbc`.
- Unrolled loops: `build/dex-lifecycle-budget-20261013/music-unrolled/pokecrystal-diagnostic.gbc`.

Do not point these diagnostic ROMs at the live main save. Their adjacent
`.sav` files are copies; the live save has not been edited during this follow-up.

## Evidence And Reproduction

Baseline production ROM SHA-256:
`357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0`.
Recommended ROM SHA-256:
`74a9bf44536bbb5b03673b510a0c0e82bc6e982d351a305511b2703e31ca1795`.

Evidence root: `build/dex-lifecycle-budget-20261013/`. `comparison.json` includes
all medians, ranges and paired deltas in both units, allocation checks and
production identity. `capture-audit.json`, `exit-hardware-audit.json`,
`clock-qualification.json` and `routes-summary.json` record the focused checks.
`config.json` records helper locations, five-byte allocation and image hashes.

The reusable diagnostic builder is `tools/dex_timing/dex_lifecycle_budget.py`;
its assembly helpers live under `tools/dex_timing/probes/dex_budget_*.asm`.
The recorder/compositor is `tools/dex_timing/dex_lifecycle_video.py`. These are
host test tools; no production assembly is altered. They depend on the
immutable baseline and earlier lifecycle fixtures, so a different production
revision requires fresh preparation and review, not blindly replaying offsets.

Representative commands, from the repository root:

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget prepare
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget extend
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget profile --variants baseline reference music-best --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget report
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget qualify --variants music-best --models 0 A B C D E
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget exit-matrix --variants music-best
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget exit-audit --variants music-best
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_budget routes --variants baseline music-best --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_video record
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_video render
```

Use disjoint profile groups when collecting all designs; the report reads
every `profile-*.json` file, so overlapping group files would duplicate cases.
