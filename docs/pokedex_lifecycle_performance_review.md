# Pokedex Opening And Closing Performance Review

Date: 2026-10-13. Diagnostic scope for `DEX-PERF-01`; no lifecycle changes
have been integrated into production. The baseline is the accepted production
build with the new Evolves from pages and the precomputed Selected renderer.

The best low-space candidate removes redundant display waits from entry and
uses a Dex-only closing coordinator. It reduces median input-to-ready entry
from 778 to 513 ms and exit from 861 to 693 ms. The projected source cost is
92 ROMX bytes, with no new RAM allocation. It retains the complete exit sound,
the normal fades, map reconstruction and all existing cleanup. A zero-space
initialization reorder alone saves 132 ms on entry.

## Save Update

The main `/Applications/SameBoy/Games/pokecrystal.sav` was updated only after
the user saved and closed its window. Its eight existing discoveries were
retained; 192 randomly selected unseen moves were added, yielding 200 of 333
moves, or 60.06%. Integer flags cannot represent exactly 60% of 333.

Both primary and backup discovery records have valid CRCs. Only 88 bytes
changed, all inside those two 72-byte extensions. Player identity, core and
conversion-table checksums, all other save data and appended RTC bytes are
unchanged. A private native cold Continue also loaded all 200 flags.

- Original backup: `build/dex-entry-exit-review-20261013/save-backup/pokecrystal-before-60-percent.sav`.
- Receipt, hashes and added move names: adjacent `.json` file.
- Random seed: `20261013`; updates only add bits, including preservation of
  already-set future-index bits outside the current move catalogue.
- Reusable editor: `tools/set_move_discovery_fraction.py`.

## Measurements

Timings use physical emulated LCD time, not host execution time. One display
interval is about 16.74 ms. The current game is already in double CPU speed
both inside and outside the Dex; no speed-switch optimization is involved.

Each design has 48 normal-input lifecycle cases: Modern and Legacy, all three
Pokemon sort orders, four input phases, and initial entry plus immediate
re-entry. Batteries and ROMs are private copies. The host observer reads
function boundaries, display frames, actual viewport registers and sound
channel flags; it adds no cartridge code or interrupt overhead.

| Candidate | Entry median | Exit median | Paired entry saving | Paired exit saving | Projected source ROMX | Diagnostic net code cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current production | 778.0 ms | 860.6 ms | -- | -- | 0 | 0 |
| A: Initialization reorder | 645.9 ms | 861.1 ms | 132.1 ms | Effectively none | 0 | 0 |
| B: A plus direct right-edge setup | 511.6 ms | 861.1 ms | 265.9 ms | Effectively none | +32 B | +32 B |
| C: Guarded local exit, post-sound mask | 777.8 ms | 692.7 ms | Effectively none | 167.9 ms | +60 B | +72 B |
| D: B and C together | 513.0 ms | 693.0 ms | 265.3 ms | 167.9 ms | +92 B | +104 B |

All costs are changes in occupied ROMX, not changes in cartridge file size.
The diagnostic images are address-stable overlays, not relinked production
sources. Source projections eliminate their compatibility trampolines;
the final linked cost must be confirmed during implementation.

Production entry ranges from 759.6 to 813.1 ms; candidate D ranges from 494.1
to 547.8 ms. Production exit ranges from 860.1 to 861.3 ms; D from 692.1 to
693.9 ms. Every paired D entry and exit is faster: entry saves 265.1-266.1 ms,
exit 166.3-168.1 ms. The median improvements are about 34% and 19.5%.

B alone shifts the display phase enough that one exit comparison gains a
16.2 ms wait, despite no extra exit work. Its median exit delta is -0.1 ms.
This phase-dependent tail is absent from the combined D comparison.

### What The Timing Categories Mean

`Input-to-ready` begins with the normal A or B request and ends at the native
Listing or Start-menu input loop. It includes input polling, fades, preparation
and cleanup. This is the main responsiveness number, not a single helper cost.

First changed pixels are also recorded, but grid icons can animate while the
transition is pending. A changed full-screen hash alone therefore does not
prove the transition has started. First all-white captures, native reveal
boundaries and the completed destination are recorded separately.

The independent pixel audit covers six first-entry configurations per design.
It masks only the nine animated Modern grid icons or the returned menu's
8x8 blinking arrow. All other final pixels match the paired baseline, and the
static destination never reverts after appearing. Median first complete static
Listing is 790.2 ms in the six baseline captures versus 524.8 ms in D; the
restored static menu is 844.4 versus 676.4 ms. These six-case figures are not
the 48-case input-loop medians above.

The raw `complete_screen_ms` field uses a settled full-frame hash. It can wait
for a matching icon or arrow phase; use `capture-audit.json` for the independently
masked static-screen comparison, not that raw field as an exact reveal metric.

## Where The Time Goes

The costs below are a representative Modern first entry and direct exit on
the copied main save's map. Nested function spans overlap and must not be added
as if independent.

| Entry work | Approximate duration | Interpretation |
| --- | ---: | --- |
| Fade to menu | 132 ms | Mostly the intentional fade, retained |
| `ClearBGPalettes` | 67 ms | Includes a four-frame map wait |
| `ClearTilemap` | 66 ms | Another four-frame map wait with LCD still on |
| `Pokedex_LoadGFX` | 82 ms | Includes LCD synchronization and real font/graphics preparation |
| `DrawDexEntryScreenRightEdge` | 134 ms | Mostly an eight-frame `WaitBGMap2` |
| Ordering | 4 ms | Not a major bottleneck |
| Initial visible grid cache | 20 ms | Needed visible content, not removed cache warming |
| Main-screen initialization | 184 ms | Includes portrait/window preparation and existing reveal sequencing |

| Exit work | Approximate duration | Interpretation |
| --- | ---: | --- |
| Exit `WaitSFX` | 284 ms | Deliberately waits for the full sound |
| Overworld block reconstruction | 7 ms | Required because Dex scratch aliases map-block storage |
| `ClearBGPalettes` | 59 ms | Fixed wait, slightly phase dependent |
| Tileset and palette reload | 143 ms | Includes real font, metatile and tileset work; retained |
| Final `WaitBGMap2` | 128 ms | Fixed streaming wait, replaced locally |
| Fade in | 134 ms | Intentional fade, retained |

The expensive obsolete behavior is chiefly fixed display waits around work
that is already hidden or can be published directly. It is not a reason to
restore cache warming or add large caches, precomputed graphics or SRAM fields.

## Implementation Options

### A Initialization Reorder

In `engine/pokedex/pokedex.asm:InitPokedex`, use `ClearPalettes` instead of
`ClearBGPalettes`, and call `Pokedex_LoadGFX` before `ClearTilemap`.
`Pokedex_LoadGFX` already disables the LCD. Clearing the tilemap afterward no
longer takes an LCD-on four-frame wait. The four calls keep the same code size.

Complexity is low: one local ordering change, no new state. The risk is revealing
old data before the new owner is ready, so retain the existing hidden preparation
and complete-screen reveal. The diagnostic final graphics and captured static
handoff checks pass. Non-CGB entry sequencing still needs explicit qualification
before promoting a source patch.

### B Direct Right Edge Setup

Keep the LCD off through the remaining initialization and replace only Init's
call to `DrawDexEntryScreenRightEdge` with a local helper. Reuse the existing
`Pokedex_CopyDescriptionRightEdge`, which copies the actual exposed BG column
20 and its attributes. Correct row 8 to Listing tile `$67`; Selected uses `$76`
there. Preserve `rVBK`, then enable the LCD. No new tile or graphical asset is
needed. The compatibility branch keeps the ordinary non-CGB path.

The helper is 35 bytes; deleting the earlier three-byte `EnableLCD` call gives
a net +32 ROMX bytes. It reuses existing code and the existing edge table.
`DrawDexEntryScreenRightEdge` itself remains because New Dex Entry still uses
it. Neither New Entry nor the Selected right-edge layout should be changed.

Complexity is low to moderate. The main risks are a wrong exposed edge cell,
attributes, a premature LCD enable or accidentally changing a shared caller.
The prototype verifies both Listing styles and the secondary routes.

### C Dex Only Closing Coordinator

Keep `Pokedex.exit` cleanup, `WaitSFX`, locked-ID release, remembered preferences
and saved viewport restoration. Request white palettes after the sound and
sprite cleanup but before restoring the saved viewport. Do not wait on that
request or remove the necessary `ReturnToMapFromSubmenu` reconstruction.

At the Dex caller in `engine/menus/start_menu.asm:StartMenu_Pokedex`, use a
Dex-specific CGB closing helper rather than changing shared `CloseSubmenu`.
It keeps tileset reload, sprite reconstruction, menu-stack restoration, map
palette setup, overworld palette 7, normal fade and sprite-update re-enablement.
The initial white request uses `ClearPalettes`; the final eight-frame streamed
map wait becomes the existing direct tilemap/attribute copier.

The direct copier requires a local palette guard, described below. The guarded
helper is 57 bytes. Putting it in the caller's bank avoids the diagnostic's
nine-byte farcall trampoline. A source-level post-sound `call ClearPalettes`
adds three bytes: projected +60 ROMX total. Current bank 4 has 1,975 free bytes
and bank 16 has 182, sufficient for those placements at this checkpoint.

Complexity is moderate, but confined to Dex lifecycle coordination. Shared
VBlank, STAT, battle code, `CloseSubmenu`, map copying and fades stay unchanged.
It uses existing copy scratch and a temporary two-byte stack save, not a new
WRAM allocation. Later changes to generic close sequencing must be reflected
in this local coordinator; keep its restoration checklist alongside it.

### D Combine B And C

This is the preferred balance: about 433 ms saved over an open/close pair,
projected +92 ROMX bytes, no new ROM0, WRAM0, WRAMX, HRAM, SRAM or VRAM allocation.
It introduces no new asset set or persistence format. Its source placement
removes 12 bytes of diagnostic-only mask/trampoline overhead.

A is a very small implementation. B is another small, isolated entry helper.
C needs a careful local sequencing change and hardware-write checks; testing
and review are the larger portion of its cost. D combines those tasks rather
than introducing another architecture. Expect a small code patch followed by
the full existing regression campaign, not a cache or display-engine rewrite.

## Important Timing Guard

The first unguarded local exit looked correct at its final endpoint, but all
88 detailed cases had rejected palette writes: 4,136 in total. The existing
`CopyTilemapAtOnce` temporarily disables interrupts, copies both maps, and
re-enables interrupts at line 127 or later. A VBlank request accumulated during
that copy can then execute on a visible scanline. With map palettes queued,
`ForceUpdateCGBPals` attempted writes on lines 128-130; the PPU rejected them.

This is a property of calling the existing helper under these conditions,
not added overhead in a shared ISR and not a production regression. Those
unguarded ROMs are discarded candidates despite their correct final screenshots.

The corrected local helper preserves `hCGBPalUpdate`, temporarily clears it,
calls the existing copier, waits for a fresh frame with `DelayFrame`, then
restores the queued palette request before the normal fade. This adds 12 code
bytes and uses the existing stack. It does not modify the shared copier or
interrupt routine. In the measured matrix its alignment is absorbed by the
subsequent fade: the entry/exit medians remain unchanged.

Both corrected mask timings have zero rejected palette or VRAM writes in
their qualified detailed checks. Removing the guard because the screenshot
looks correct would reintroduce the hidden failure.

## Mask And Sound Choices

An early mask at `Pokedex_Exit` makes the screen fully white roughly 66 ms after
the request, while the exit sound is still playing. It does not itself shorten
the exit. With the faster coordinator, it gives a median 21 all-white captures.

The post-sound version keeps the outgoing Dex during its sound, then masks
before viewport restoration. In the faster prototype the first completed
all-white capture is about 493 ms and there is one all-white capture before
the fade. LCD-off reload intervals also exist and are not equivalent to a
completed LCD-on white frame. This version is preferred for manual review:
it has the same approximately 693 ms input readiness without the long early
white dwell. Both variants remain available for comparison.

An independent trial removed the exit `WaitSFX`. It brought exit readiness to
577 ms, saving 284 ms, with net +6 diagnostic ROMX bytes. The sound continued
during restoration, but its measured active duration shortened from 283.9 to
276.5 ms. Reload's existing `SkipMusic` advances audio while the LCD is off.
That is a behavior change, not a free removal of unused code. It requires
listening and an explicit choice about sound overlap; it is not included in D.

Shorter local fades could save additional frames without adding RAM, but would
change the transition's appearance. That option is not prototyped or costed
here. Retaining decompressed fonts/tilesets or map blocks would trade substantial
RAM/VRAM space for smaller remaining gains and complicate ownership. Removing
the map rebuild would be incorrect, since the Dex overwrites its union.

## Validation And Remaining Qualification

- 576 lifecycle observations across 12 designs, including the rejected
  unguarded trials; all measured final static fields match after explicit
  animation/off-screen normalization.
- 144 captured entry/exit comparisons: identical static destination pixels and
  no reversion after the completed static destination.
- Recommended D: 48 lifecycle cases; 88 detailed exit cases with no displaced
  colored frames, rejected palette writes or rejected VRAM writes.
- 36 normal-input secondary-route cases compare baseline with D in both styles:
  mode cancellation, Pokemon Search/results, Description, Bayleef Info including
  forward and ancestor pages, Selected Moves, Area, Unown, Type Matchups and
  Moves Search/text/results. All return through the Start menu and back to
  overworld movement; zero failures. The Area route correctly uses a separate
  B to return to Selected and then another to leave Selected.
- 13 host tests pass: five save-editor cases and eight strict visual-audit
  controls. Real palette, map, portrait, sprite position and viewport changes
  cannot be normalized away as icon phases.
- Native cold Continue validates the modified discovery save. Production
  ROM/symbol hashes remain identical to the diagnostic baseline.

Raw differences are retained rather than called byte-identical: Modern icon
frames use the established tile pairs, the unused far-right window column
differs in the direct edge trial, and the returned menu hides its window at
`WY=144`. Visible text, geometry, hardware palettes, portrait and viewport match.

The historical October 2 exit shift does not reproduce in the current baseline's
48 lifecycle or fresh 88 detailed cases. Current block reconstruction is about
7 ms, below one display interval. Older tests had a longer rebuild and a
different clock/save context. This is not proof that every map is immune;
masking before viewport restoration protects the ordering without deleting the
rebuild. Keep the original evidence as historical, not a current 88/88 failure.

These diagnostics use SameBoy CGB E, not physical hardware. Before production
integration, run the full documented suite, supported CGB-model checks, sparse
and all-caught listings, larger/connected maps, rapid input, map music/exit audio,
save/reload and preference retention. Include New Entry, sampled cries and all
battle animations to establish no changes outside lifecycle. This report does
not claim that those full integration regressions have already run on D.

## Artifacts And Reproduction

All private outputs are under `build/dex-entry-exit-review-20261013/`.

- Baseline ROM: `baseline/pokecrystal.gbc`.
- Preferred diagnostic: `local-late-guarded/pokecrystal-diagnostic.gbc`.
- Alternative early mask: `local-guarded/pokecrystal-diagnostic.gbc`.
- An adjacent copied `.sav` accompanies the baseline and preferred ROM. These
  do not share the installed main ROM's battery path.
- `comparison.json`: paired timings, raw UI differences and their strict audits.
- `capture-audit.json`, `routes-summary.json`, `late-guarded-bus-audit.json`:
  pixel, secondary-route and hardware-write checks.
- `exit-matrix/*/results/report.json`: detailed 88-case matrices, including the
  discarded unguarded trial. The recommended late-guarded bus totals are zero.
- `v2`, `v3`, `v4`: retained timing campaigns and compressed observer events.

Baseline ROM SHA-256:
`357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0`.
Preferred diagnostic SHA-256:
`41050dd2467e5442ee91bd2d1e5eafebb425afe2aefefa6aef63c918767daa8f`.

The reusable runner is `tools/dex_timing/dex_lifecycle_review.py`; the three
small assembly probes and read-only observer live under `tools/dex_timing/probes/`.
It verifies linked call bytes and free space before applying any private overlay.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_review report
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_review capture-audit
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_review routes \
  --variants baseline local-late-guarded --jobs 6
PYTHONPATH=tools:. python3 -m tools.dex_timing.dex_lifecycle_review exit-matrix \
  --variants baseline local-late-guarded
PYTHONPATH=tools:. python3 -m unittest \
  tools.test_move_discovery_fraction tools.test_dex_lifecycle_review
```

For a new link, prepare a fresh base with a closed/copy-only donor battery,
build fresh matching Listing checkpoints, and update the detailed-matrix fixture
path. Do not reuse old checkpoints or symbols across relinked source changes.
Full regression instructions remain in `docs/full_regression_suite.md`.

Manual comparison: Continue each private ROM, open the Start menu, select Dex,
then B back to the menu. Repeat immediately and in Legacy. Inspect the portrait,
window edge and blank/fade timing as well as how quickly input becomes usable.
The preferred ROM changes lifecycle only; it is not the production replacement.
