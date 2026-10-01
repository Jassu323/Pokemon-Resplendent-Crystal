# Pokedex Listing Restoration Investigation

Updated 2026-10-01. The three diagnosed Listing-restoration fixes are now
implemented and verified. The Description animation scheduler and graphics
allocations are unchanged. Baseline findings are retained below so that the
before/after evidence remains auditable. The adjacent grid-ID lifetime weakness
is also resolved with presence flags; see the [correction](#presence-flag-correction).

## Result

Three baseline failures were reproduced through normal controller input:

1. Returning without internal species paging skips the Listing BG palette
   restore. Correct icon tiles are displayed with Description palettes.
2. Returning after internal species paging attempts the palette restore, but
   the combined owner publication extends beyond VBlank. Eleven OBJ palette
   writes are rejected during pixel transfer, and the request is still cleared.
3. Returning outside the existing five-row icon cache disables the LCD to
   rebuild the cache. The LCD is re-enabled before the Listing is constructed,
   exposing white frames followed by the outgoing Description again.

These are Listing ownership/publication failures, not animation dictionary
underruns or evidence that the Selected scheduler needs another redesign.
The first two must be fixed together: setting the missing dirty flags alone
would turn a skipped restore into the already-reproduced late-write failure.

The implemented handoff explicitly restores Listing palettes, protects their
writes against Mode 3, and repairs only missing cache rows without disabling
the LCD. The original 24 conditions, a bottom-boundary return, nine repeat
runs, 281 post-return navigation/cache checks and 43 late-admission stress
cases pass. No new functional regression was found. All 373 species retain
exact animation timing and uninterrupted cry completion on both cold entry
and settled internal paging. Drapion's known static text overflow is still
reported, not suppressed. See [implementation and results](#implemented-restoration).

## Baseline Build And Observation

The runner uses the accepted 2026-09-30 UI ROM copy and matching linked symbols:

- ROM: `build/dex-description-ui/cold-final/input-copy.gbc`
- ROM SHA-256: `070f2c8b13155486cffa1abc36c4f4db39a11d8fe6d00842e4c3308e6cd33599`
- Symbol SHA-256: `dc18c7ab57654bc611cfeddecd92d7fd39427d7dd909188984c2878bfc438084`
- Diagnostic copy: `build/dex-listing-restoration/diagnostic-input.gbc`
- Full 20-condition report: `build/dex-listing-restoration/matrix-report.json`
- Sparse-seen report: `build/dex-listing-restoration/sparse/report.json`
- Repeated paths: `build/dex-listing-restoration/repeated/report.json`
- Observation control: `build/dex-listing-restoration/observer-control.json`
- Physical-clock cost follow-up: `build/dex-listing-restoration-cost/report.json`
- Follow-up observation control: `build/dex-listing-restoration-cost/observer-control.json`

The original diagnostic ROM is byte-identical to the accepted copy. The initial
investigation did not rebuild root `pokecrystal.gbc`; the implementation phase
does rebuild it. Instrumentation is entirely in the
headless SameBoy runner, enabled only by `DEX_LISTING_RESTORE_TRACE`; it neither
patches game instructions nor writes game memory. The normal runner does not
install these callbacks. Generated artifacts remain under ignored `build/`.

The observer records presented pixels, all VRAM, hardware and target palettes,
OAM, cache tags, scroll/window registers, palette dirty flags and owner phases.
It records each palette write's index, LY, STAT and SameBoy access-blocking
state. The observer-enabled and uninstrumented cores reproduce identical
cycles, state snapshots, maps, palettes and final pixels for direct return,
one internal page and nine internal pages. Host logging changes wall-clock
execution time, not emulated time.

There are 24 distinct conditions: 20 all-seen paths and four sparse-seen paths.
The three principal all-seen reproductions were also run three times apiece
(nine repeat runs). Six additional control replays compare observer on/off.
This is a restoration-focused sample, not an exhaustive all-species/phase
acceptance matrix. The existing 14 cold-runner unit tests pass.

## Reliable Reproductions

Use New Dex ordering. Release the pad between actions and allow animation and
cry completion unless testing active cancellation.

| Path | Steps | Current result |
| --- | --- | --- |
| Direct return | Open Chikorita from Listing, settle, press B without paging | Side BG icons have incorrect colors; center OAM icons remain correct. |
| Internal return, same viewport | Open Chikorita, settle, press Down once to Bayleef, settle, press B | BG palettes restore, but center-row OBJ palette 3 retains two incorrect bytes. No LCD-off flash. |
| Internal return, outside cached viewport | Open Chikorita, settle, page Down nine times to Pidgey, settling each time, then B | Five white presented frames, then the outgoing Description for seven frames, then Listing. The OBJ write failure also occurs. |

The direct failure also occurs with Meganium, Togetic, Dusknoir, Luxray and
Weavile, after a text-page-2 toggle, and when canceling active Dusknoir/Weavile
animations. All 16 direct-return conditions have 38 incorrect bytes among BG
palette slots 2-7. Hardware OBJ slots 0-5 are correct on these direct returns;
unused OBJ slots 6-7 are excluded from the visible-failure count.

Internal Down 1, 8, 9 and 12 paths each reject the same eleven OBJ writes. The
Down 12 result happens to have no surviving visible palette mismatch: rejected
bytes already equal their intended values. This explains an apparently
intermittent visual symptom despite a deterministic publication defect.

The sparse fixture preserves caught flags, RTC and unrelated save data, clears
other seen flags, and keeps the last New Dex entry seen. Both save checksums
are verified/recomputed. It is a separate copied battery; the user's live save
is untouched. Chikorita direct return and one internal page reproduce the same
palette failures; paging across unseen gaps to Mewtwo/Dusknoir reproduces the
LCD-off rebuild and palette rejection. Those far returns contain six white
presented frames. The invisible/unseen holes do not explain the palette bug.

## Cause 1: Listing Palettes Are Prepared But Not Requested

Relevant paths:

- [Selected Leave](../engine/pokedex/pokedex_detail.asm):
  `PokedexSelectedMon_Leave` cancels animation and normalizes the Listing view.
- [Listing initialization](../engine/pokedex/pokedex.asm):
  `Pokedex_InitMainScreen` stages the window, Listing layout, maps and OAM.
- [Palette preparation](../engine/gfx/cgb_layouts.asm):
  `CGB_PokedexStageListLayout` calls `ResetBGPals`, builds the correct Listing
  targets and copies them through `ApplyPals`. It does not request their commit.
- [Owner publisher](../engine/pokedex/pokedex_3.asm):
  `Pokedex_VBlankOwnerTransition.CommitDirtyBGPals` returns immediately when
  `wPokedexSelectedBGPaletteDirty` is zero.

After direct Description entry, the completed owner transition clears both
dirty flags. They remain zero through Leave, Listing layout staging and the
Listing owner queue. The hardware thus retains Description BG palettes in
slots 2-7 instead of receiving the already-correct Listing targets.

The new Description footprint uses BG slot 2 and its type badges use slots
6/7. Its dirty mask is nonzero, causing the existing publisher to copy the
entire six-slot BG range, including otherwise-unused Description slots 3-5.
The older appearance resembling footprint/font debris is therefore not proof
that those graphics were loaded into the icon cache.

In both cache-preserving principal tests, all 120 cached icon tiles are
byte-identical before and after Description: 40 center OBJ tiles and 80 side
BG tiles. The direct-return side maps/attributes still select the cached icon
graphics. Caught-icon frame changes are the normal synchronized two-frame
phase, not corruption. Hardware palette data, rather than overwritten tiles,
accounts for the incorrect appearance in these reproductions.

## Cause 2: The Owner Commit Runs Into Mode 3

An internal species change calls `Pokedex_BlackOutSelectedMonBG`, which marks
BG slots 2-7 (`$fc`) and OBJ slots 0-5 (`$3f`) dirty. The hidden reveal uses the
general palette path but leaves those flags set. A subsequent Listing return
therefore takes the full palette branches, unlike direct return.

The current owner publisher performs:

1. Window/scroll ownership selection.
2. A 576-byte attrmap GDMA transfer (36 blocks).
3. A 576-byte tilemap GDMA transfer (36 blocks).
4. Forty-eight BG palette bytes.
5. Forty-eight OBJ palette bytes.
6. Shadow OAM DMA and request/dirty-flag clearing.

It admits the transaction when LY is below 145, but that does not establish
that the complete transaction fits in the remaining VBlank. The trace enters
the owner at LY 144, changes WX at LY 145, begins BG palette work at LY 151
and begins OBJ palette work on physical line 153. At that point LY already
reads zero, but STAT still identifies VBlank. The subsequent eleven rejected
writes occur on actual visible line 0, in Mode 3.

| Palette branches | Entry to success marker | Entry through function return | Physical line at return |
| --- | ---: | ---: | ---: |
| Both skipped | 3,916 T-cycles | 3,936 T-cycles | 153, still VBlank |
| BG and OBJ copied | 5,540 T-cycles | 5,560 T-cycles | 2, visible frame |

The ten-line VBlank is only 4,560 T-cycles, and the publisher already starts
partway into it. The extra two palette branches add 1,624 T-cycles. The initial
trace marked success immediately before `SCF; RET`; the follow-up measures the
additional 20 cycles through return to the dispatcher. This corrects the
measurement boundary, not the code or its behavior. The earlier interpretation
that the palette-skipping path also finished in the visible frame was wrong:
LY zero alone does not distinguish physical line 153 from visible line 0.

OBJ byte indexes 22-32 are attempted with `STAT=$8f`, LY 0 and SameBoy's CGB
palette-access block active. SameBoy's memory implementation rejects the data
while still auto-incrementing the palette index. The publisher acknowledges
success and clears both dirty flags without detecting or retrying these writes.
Indexes 28/29 survive as incorrect OBJ palette-3 color data on the Bayleef,
Feraligatr/Pidgey and sparse-roster examples. Other rejected bytes can match by
coincidence, concealing the defect visually.

This is a hardware access-window failure, not a slow icon decoder. Caught-ball
OBJ slot 1 is outside the rejected index range and is correct in this suite.

### Measured Cost And Optimization Headroom

The 2026-10-01 cost follow-up adds host-only physical-line callbacks, the actual
caller-return marker, and OAM call/return markers. It repeats direct return,
one internal page and nine internal pages without changing the ROM. All three
observer-enabled/disabled comparisons retain identical emulated cycles, state,
maps, palettes and pixels. Physical line callbacks account for SameBoy's CPU
batch overshoot using the display coroutine's remaining 8MHz ticks; each
complete measured line-144-to-line-0 interval is exactly 4,560 T-cycles. An
LCD-disable/re-enable interval is not treated as a complete VBlank.

In all three final owner publications, entry is 364 cycles after the physical
VBlank boundary, leaving **4,196 cycles**, not the full 4,560. The full commit
misses that boundary by **1,364 cycles**. The palette-skipping path finishes
260 cycles before it. Neither observation is a worst-phase admission guarantee;
a new implementation must also validate the latest entry its gate permits.

The full-copy trace has the following contiguous, non-overlapping intervals:

| Interval | Normal-speed T-cycles |
| --- | ---: |
| Entry/admission, window ownership, bank setup, first DMA call | 332 |
| Attrmap transfer helper and setup for next map | 1,332 |
| Tilemap transfer helper and setup for palette copy | 1,324 |
| BG palette helper and call to OBJ helper | 876 |
| OBJ palette helper and bank restoration | 900 |
| OAM call and HRAM DMA helper | 704 |
| Final flags, success and return | 92 |
| Total | **5,560** |

The minimum time for this same payload is already 4,480 cycles: 2,304 cycles
of map DMA stalls, 1,536 cycles for 96 unrolled palette-byte copies, and 640
cycles of OAM DMA. That excludes all admission, register setup, calls, bank
restoration and bookkeeping. It leaves just 80 cycles even in a completely
unused VBlank, and already exceeds the measured 4,196-cycle remaining budget.
Instruction trimming alone cannot make this full payload fit reliably.

The BG/OBJ inner copies are already unrolled `LD A,[HLI]; LDH [C],A`, costing
16 cycles per byte. The OAM wait is required for the DMA hardware, not a
removable busy-wait. These are not the main inefficiencies.

There are larger, Listing-specific opportunities that remain unused alternatives:

- **Avoid the full attrmap transfer.** Across the 20 all-seen return traces,
  the only changed visible BG0 attributes lie in the 7x7 portrait and seven
  joined-border cells at row 8. Settled returns change only the seven border
  cells; active cancellation also needs the portrait's VRAM bank reset.
  A conservative uniform restore of all 56 cells would replace the 576-byte
  transfer. A straight-line seven-row fill is roughly 560 cycles versus the
  current 1,280-cycle transfer helper, saving about 720 before added profile
  dispatch and seen/unseen checks. This is an instruction-count estimate, not
  an implemented or phase-validated complete commit. The hidden BG0 columns
  would no longer mirror the full backing map, so subsequent owners must
  rebuild them and the Listing window must remain enabled.
- **Preserve unused OBJ palette ownership through Description.** Direct
  Description entry already preserves Listing OBJ slots 0-5. Internal paging
  loads party-menu OBJ palettes through `InitPartyMenuOBPals` and the general
  hidden palette reveal even though Description does not display those OAMs.
  Avoiding that overwrite could remove redundant restoration for unchanged
  viewports. It is not safe to simply skip the existing OBJ copy: the observed
  internal-page hardware colors really do differ from the Listing targets,
  and a new viewport may need new center-icon palettes. Fully skipping a
  palette helper would save 812 cycles, but that is not a universal return-path
  saving and is insufficient on its own.
- **Do not treat map padding as a free contiguous-transfer reduction.** The
  32-column VRAM stride differs from the 20-column backing map. Eighteen short
  row transfers need separate register setup; the apparent padding savings
  are not all recoverable just by lowering the DMA length.

These opportunities can reduce real work, but do not yet prove an all-phase
single-VBlank commit. The safe-publication preflight below remains preferable
to depending on a narrow margin won by several special-case omissions.

## Cause 3: LCD-Off Cache Rebuild Exposes The Wrong Owner

`Pokedex_EnsureGridCache` validates the five physical row tags. Any missing tag
calls `Pokedex_PrimeGridCache`, which turns the LCD off, reloads all five rows
and immediately turns it back on. Only then does `Pokedex_InitMainScreen`
finish the window, metadata, layout, maps and eventual owner publication.

For Chikorita -> Pidgey, the original row offsets are `-1,0,3,6,9`; the new
viewport requires `0,3,6,9,12`. One missing look-ahead row causes all five rows
to be rebuilt. The LCDC writes bracket 267,832 T-cycles of LCD-off work, about
3.81 normal display intervals. Frame callbacks show five white presented
frames, including the LCD re-enable boundary, followed by seven Description
frames before the completed Listing takes ownership.

| Settled path | Accepted Leave to Listing-ready intervals | Approximate time |
| --- | ---: | ---: |
| Chikorita direct | 8.851 | 148 ms |
| Chikorita -> Bayleef | 9.026 | 151 ms |
| Chikorita -> Pidgey | 14.024 | 235 ms |

These timings start at the accepted B handler, not the physical button edge.
Presented white-frame counts include SameBoy LCD-off/artificial callbacks and
must not be substituted for the exact LCD-off cycle duration.

## Implemented Restoration

Only [pokedex_3.asm](../engine/pokedex/pokedex_3.asm) changes executable game
behavior. The host observer, test assertions and documentation are separate
from the production ROM.

### Palette Ownership And Safe Publication

`Pokedex_RevealOrCommitListing` sets the existing BG dirty mask to `$fc` and
OBJ mask to `$3f` on a Selected Leave, immediately before queueing the Listing
owner. Both direct and internally paged returns therefore request the same
complete Listing-owned palette ranges, independent of inherited flags.

`Pokedex_VBlankOwnerTransition` admits only `144 <= LY < 145`. The added lower
bound also rejects visible LY zero and physical line 153's early LY-zero
readback. A late request remains queued for the next VBlank; it is not
acknowledged or partially committed. Both complete 576-byte map transfers
remain inside VBlank.

The Listing-only branch then copies BG slots 2-7 and OBJ slots 0-5 with a
STAT-protected byte loop. Each write waits for Mode 0 or 1; the following
Mode 2 supplies a reserve if a read/write pair begins just before an HBlank
ends. Interrupts remain disabled, so that pair cannot be preempted into
Mode 3. BG slots 0/1 are preserved. Shadow OAM DMA follows, then the pending
owner and dirty flags are acknowledged. Description retains the existing
unrolled palette helpers and its quiet-animation publication path.

**The whole Listing transaction does not fit in one VBlank.** This correction
does not claim otherwise. The maps finish before visible line zero, while the
protected palette work and OAM complete before their first dependent Listing
pixels. The upper portrait/shell uses the already-correct BG slots 0/1. The
earliest cursor OAM is at line 34; side icons first need BG slots 2-7 at line
40. Normal owner return is on physical line 24, after 15,592 T-cycles including
safe-window waits. The extra wait time is not busy work that can simply be
removed without reopening the access-window defect.

| Required boundary | Ordinary replay headroom | Minimum in late-admission stress |
| --- | ---: | ---: |
| Both maps before visible line 0 | 1,156 T | 1,148 T |
| BG palettes before side icons at line 40 | 14,204 T | 14,164 T |
| OBJ palettes before cursor at line 34 | 4,984 T | 4,688 T |
| OAM DMA complete before cursor at line 34 | 4,200 T | 3,904 T |

The 43-case admission sweep injects a separate, explicitly synthetic CPU stall
at the first Listing owner dispatch: 0-160 T in four-cycle increments, plus
256 and 456 T. It advances real SameBoy devices without changing ROM, RAM or
registers. Delays 0/4/8 admit entries 364/368/372 T into VBlank. At 12 T and
later, the gate defers to the following VBlank. Every case retains legal writes
and positive first-use margins. Ordinary input replays use no injected stall.

This is a **Listing-layout-specific contract**, not a general license to
publish arbitrary palettes/OAM during visible scanning. Revalidate if the
palette ownership, map payload, CPU speed, cursor/side-icon Y positions or
interrupt behavior changes. In particular, moving dependent OAM above line 34
could consume the measured reserve. Search/Area and unrelated owners are not
covered by this acceptance.

### Cache Repair Without LCD-Off

`Pokedex_EnsureGridCache` first preserves an existing matching top-row ring
alignment. If no top tag matches, it uses canonical physical row 1. For a
Selected Leave, a missing tag enters `Pokedex_RepairGridCache`; other owners
retain the existing cold-prime fallback.

Repair checks the previous row and four forward rows. Matching rows are kept;
only mismatches use `Pokedex_PrepareGridCacheRow` and
`Pokedex_UploadPendingGridCacheRow`. Each row uses the existing three eight-tile
HBlank DMA transfers, publishing its absolute tag only after upload completion.
The loop saves BC/DE around the existing clobbering helpers. End-of-list blank
rows and the unused `-1` look-behind tag keep their established meanings.

The outgoing Description remains visible while animation production is
canceled, the Listing Window stays off-screen and OAM is locked. The existing
handoff then publishes completed metadata, maps, palettes and OAM. No LCDC
toggle or partially rebuilt Listing is exposed. Pidgey's nine-page return
repairs one row instead of rebuilding five; the twelve-page return repairs two.
Sparse far jumps still need all five rows, but now do so with the LCD running.
The cache regions do not overlap the Description frontpic, footprint or type
badge graphics.

### Measured Return Latency

These start at accepted B/Leave and end when Listing initialization is ready,
not at the physical input edge. Values are CPU completion fractions of a
70,224-T hardware display interval, not counts of independently visible frames.

| Settled path | Baseline intervals | Fixed intervals | Approximate change |
| --- | ---: | ---: | ---: |
| Chikorita direct | 8.851 | 9.171 | +5.36 ms |
| Chikorita -> Bayleef | 9.026 | 9.164 | +2.31 ms |
| Chikorita -> Pidgey, nine pages | 14.024 | 10.164 | -64.63 ms |
| Chikorita, twelve pages | 13.897 | 12.204 | -28.36 ms |

Direct/same-cache returns pay a small safe-publication cost; row reuse makes
cache-miss returns faster. All measured return sequences have zero white
presented frames and no LCD disable/re-enable writes.

### Resources

The executable change adds exactly **166 ROMX bytes in bank `$77`**. The
Pokedex 3 section grows from `$1831` to `$18d7` bytes. No ROM0, WRAM0, WRAMX,
HRAM, VRAM or SRAM allocation is added. Existing row staging, palette flags,
owner queue and persistent map buffers are reused. `.committed` is a host
observation label with no emitted instruction cost. No animation metadata,
prefill/quota, encounter, save or Master Ball changes are included.

### Regression Results

Evidence is under ignored `build/dex-listing-restoration-fixed/`:

- `matrix/report.json`: all original 20 all-seen conditions pass. No rejected
  palette writes, visible palette mismatches, white frames or LCD toggles;
  each owner copies all 96 required palette bytes. Unused OBJ slots 6/7 are
  deliberately not treated as Listing-visible failures.
- `follow-up-verified/report.json`: 21 paths, including the last-entry return,
  pass 235 post-return checks of row tags, all 24 tiles per row,
  metadata, target/hardware palettes, ordinary scrolling, wrap and re-entry.
  The independent reference viewports are reached through normal input.
- `sparse-verified/report.json`: four sparse-roster paths pass another 46
  checks, including five-row repair and A correctly doing nothing on unseen
  entries. Only a copied battery is edited; caught/RTC/unrelated state and the
  live save are preserved.
- `repeated/report.json`: the three principal paths repeated three times
  each pass with identical results.
- `admission/report.json`: all 43 separately identified late-entry stress
  cases meet the publication boundaries above.
- `final-controls/observer-control.json`: three observer-on/off pairs have
  identical emulated cycles, state, maps, palettes and pixels.
- `cold/` and `paging/`: 373 species each, 746 complete playback cases. Every
  species meets its exact authored animation duration; all 122 sampled cries
  finish naturally on each path. All 746 returns finish. Each suite reports
  372 full visual passes and the same pre-existing Drapion static text overflow.
- `ui/report.json`: 1,492 Description-page/neighbor checks; only the four
  already-known Drapion shell-overflow observations fail.
- Fourteen Listing observer unit tests pass. The focused current cold,
  scheduler, Description UI, New Dex Entry and Listing suites pass together:
  68 tests, no failures.

The broad historical `test_dex_timing` suite is not all green: it still expects
removed instrumentation symbols and superseded cycle counts. An exact baseline
ROM was rebuilt in a separate shadow source tree and matches the accepted
SHA-256 above byte-for-byte. Its historical test results match the fixed link:
187 tests, 103 skipped, six failures and sixteen errors, with **zero new failing
test IDs**. See `legacy-test-comparison.json`. These are retained limitations
of the historical suite, not silently counted as passing runtime regressions.

During the additional cache checks, initial host assertions incorrectly
required unused end-of-list/look-behind graphics to be blank and expected A
on an unseen entry to open Description. Those test assumptions were corrected;
the `*-verified` reports are the final acceptance reports. No game workaround
was added for those false positives.

## Existing Metadata Lifetime Weakness

The following observation reproduced in the **byte-identical baseline** and
the palette/cache-restoration build. It was not caused by the new row repair or
safe palette writes. The separately approved presence-flag correction below
now removes this unnecessary retained-ID lifetime.

Reproduction: cold-open Luxray, settle, B, then Up, Down four times, Up three
times, Left, Right, releasing the pad between actions. At the last Up,
Listing scroll is 336 and the middle absolute row is 339 (Rampardos, Shieldon,
Bastiodon). The shifted `wPokedexGridSpecies` still contains temporary IDs
`$52/$53/$54`, but their bank-2 conversion-table entries have been collected.
The translated indices read zero instead of 340/341/342. The same warning
persists through Left/Right; a full re-entry/return reconstructs the metadata.

Cause: `PokemonTableGarbageCollection` in
[table_functions.asm](../engine/16/table_functions.asm) marks party, buffered,
locked and recent-conversion roots but not the nine retained grid IDs. Loading
a new row can therefore collect IDs still stored in shifted Listing metadata.

The actual cached tile bytes, flags, palette metadata and hardware palettes
remain correct. Selection independently resolves the absolute 16-bit
`wPokedexOrder` entry and locks that selected ID. Current grid consumers tested
here use the stale IDs as nonzero occupancy, not as species identity; no wrong
name, frontpic, selection or visible corruption is reproduced. The runner keeps
this as a separate metadata warning, not a false graphics-acceptance failure.

### Presence Flag Correction

The same nine bytes at `$c6f1` are now named `wPokedexGridOccupied`. Each valid
order entry stores `1`, including an unseen Pokemon; out-of-range entries and
`$ffff` sentinels remain `0`. Cursor validation and grid drawing read these
flags, and the existing row shifts copy them with the separate seen/caught
flags and cached icon palettes. No transient species ID remains in this array.

`Pokedex_CacheGridPosition` still resolves a fresh temporary ID for construction,
but passes it explicitly in `c` to `Pokedex_CacheGridIconPalette`. That helper
caches the resulting palette without storing or later resolving the ID. The
five-row VRAM icon cache remains keyed by absolute Listing offsets. Selected
identity still resolves the 16-bit `wPokedexOrder` entry and locks its fresh ID.
There is no additional selection lookup, global GC root, lock slot, or cache
rebuild policy change.

Relative to the preceding restoration build, bank `$10` grows by two bytes
(`$2873` to `$2875`), and bank `$77` shrinks by five (`$18d7` to `$18d2`):
**three ROMX bytes saved net**. ROM0, WRAM0, WRAMX, HRAM, SRAM and VRAM allocations
are unchanged. The original restoration resource estimate above describes its
pre-presence build, not this additional correction.

The host observer recognizes both linked contracts. Old-ROM comparisons still
translate retained IDs and report identity warnings. Current-ROM checks instead
require exactly nine Boolean presence values matching the actual Listing
bounds, independently of seen/caught status. They never translate a presence
byte through the species conversion table. Unit cases reject non-Boolean IDs,
missing unseen occupancy, populated out-of-range cells and truncated arrays.

Acceptance artifacts are under ignored `build/dex-grid-presence/`:

- `baseline-luxray/report.json`: the original normal-input reproduction still
  produces three stale-ID warnings before the change.
- `restoration/report.json`: all 21 normal return conditions and 235 subsequent
  cache/navigation/re-entry checks pass with zero metadata warnings. At the
  original failing row, `$52/$53/$54` are replaced by `1/1/1`; seen/caught flags,
  icon palettes and all Listing-used hardware palette bytes match the baseline.
  The settled Luxray return screenshot is byte-identical to the pre-change one.
- `sparse/report.json`: four sparse-seen returns and 46 subsequent checks pass,
  including occupied unseen entries, partial end rows, wrapping and ignored A
  selection on unseen entries. Only an isolated battery fixture is edited.
- `admission/report.json`: all 43 synthetic late-publication admission cases
  retain safe map, palette and OAM publication with no white flash.
- `restoration/observer-control.json`: all three observer-on/off replay pairs
  remain identical in emulated cycles, state, maps, palettes and final pixels.
- `cold/` and `paging/`: all 373 authored animation durations match exactly on
  each path; all 122 sampled species naturally complete on each path, without
  animation or sampled-cry misses. All 746 returns reach Listing. The only
  whole-case failure on either path is the unchanged Drapion static text overflow.
- `ui/report.json`: 1,492 Description UI checks have only the same four known
  Drapion `shell_0_5` failures; no new layout, type, palette or paging failure.

All 72 focused unit tests pass, including the four new presence-contract cases.
The root ROM is rebuilt. No new functional regression was found; `DEX-GRID-03`
is closed. The unrelated text/input/transition/canceled-cry backlog stays open.

## Unreproduced And Adjacent Findings

- The baseline outgoing Description reappears after LCD re-enable. The fixed
  return keeps it visible continuously until handoff instead. The older
  eight-pixel downward displacement/upward scroll was not reproduced in either
  link; hardware and mirrored SCY remain zero throughout these traces.
- No temporary unseen portrait, `-----`, or intermediate cursor was reproduced,
  including sparse seen flags. Keep `DEX-RETURN-04` open.
- Caught-ball palette corruption was not reproduced. The confirmed OBJ write
  failure does not overwrite caught-ball slot 1; keep `DEX-GRID-02` open.
- Four early B-cancel cases (Dusknoir/Weavile at offsets 0/4) exhaust the
  outgoing sampled cache during Listing preparation. This extends the already
  deferred outgoing-audio ownership issue `DEX-CRY-04`; it is not an incoming
  Listing animation failure or an uninterrupted Selected cry regression.
- Search Results, Area returns, Options/search transitions, rapid-axis input
  and active A-description corruption are outside this suite.

No further manual SameBoy capture is needed for the three implemented fixes.
Additional matching-link reproduction evidence is still needed for the
unresolved displacement, placeholder and caught-ball reports. The fixed
all-seen/sparse suites do not reproduce those independent symptoms.

## Reproduction Tool

Generate new normal-input checkpoints whenever game bytes or linked symbols
change. The fixed suite uses `build/dex-listing-restoration-fixed/cold`; ROM
and symbol hashes are checked before any saved state is reused. Current
restoration acceptance commands are:

```sh
python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-listing-restoration-fixed/cold \
  --output build/dex-listing-restoration-fixed/follow-up-verified \
  --expect-fixed --follow-up

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-listing-restoration-fixed/cold \
  --output build/dex-listing-restoration-fixed/sparse-verified \
  --expect-fixed --sparse --follow-up

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-listing-restoration-fixed/cold \
  --output build/dex-listing-restoration-fixed/admission \
  --expect-fixed --admission-sweep

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-listing-restoration-fixed/cold \
  --output build/dex-listing-restoration-fixed/final-controls \
  --case chikorita --case chikorita-down1 --case chikorita-down9 \
  --expect-fixed --verify-observer
```

For comparison, the original baseline diagnostic commands were:

```sh
python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-description-ui/cold-final \
  --output build/dex-listing-restoration \
  --verify-observer

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-description-ui/cold-final \
  --output build/dex-listing-restoration/sparse --sparse

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-description-ui/cold-final \
  --output build/dex-listing-restoration/repeated \
  --case chikorita --case chikorita-down1 --case chikorita-down9 --repeat 3

python3 -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-description-ui/cold-final \
  --output build/dex-listing-restoration-cost \
  --case chikorita --case chikorita-down1 --case chikorita-down9 \
  --verify-observer
```

The original first command emits `report.json`; that baseline's complete aggregate
is also saved as `matrix-report.json` because later focused control reruns used
the same output directory. Each case retains its own report, write/frame trace,
before/after images and pre-B save state. The source checkpoint suite and
matching symbols are required; the tool does not silently accept a different
ROM link. To replay an old comparison, also pass `--sym` with that ROM's exact
symbol file. Use a new output directory when retaining before/after evidence.
The fixed follow-up compares ring rows by absolute tag rather than physical
slot, and compares against independently reached normal-input viewports.
Normal scrolling needs only its three visible rows; a completed Description
return must have all five cache tags valid. Separate metadata-lifetime warnings
do not replace the graphics/palette checks. All generated cores, copied saves,
states, images and logs stay under ignored `build/`; host tracing is not part
of `pokecrystal.gbc`.
