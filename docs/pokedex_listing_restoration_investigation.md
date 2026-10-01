# Pokedex Listing Restoration Investigation

Investigated 2026-10-01. Diagnostic only: no game fix is implemented by this
investigation. The accepted Description UI and animation scheduler are unchanged.

## Result

Three current failures are reproducible through normal controller input:

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

## Build And Observation

The runner uses the accepted 2026-09-30 UI ROM copy and matching linked symbols:

- ROM: `build/dex-description-ui/cold-final/input-copy.gbc`
- ROM SHA-256: `070f2c8b13155486cffa1abc36c4f4db39a11d8fe6d00842e4c3308e6cd33599`
- Symbol SHA-256: `dc18c7ab57654bc611cfeddecd92d7fd39427d7dd909188984c2878bfc438084`
- Diagnostic copy: `build/dex-listing-restoration/diagnostic-input.gbc`
- Full 20-condition report: `build/dex-listing-restoration/matrix-report.json`
- Sparse-seen report: `build/dex-listing-restoration/sparse/report.json`
- Repeated paths: `build/dex-listing-restoration/repeated/report.json`
- Observation control: `build/dex-listing-restoration/observer-control.json`

The diagnostic ROM is byte-identical to the accepted copy. Root
`pokecrystal.gbc` is not built or replaced. Instrumentation is entirely in the
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
and begins OBJ palette work at LY 0 of the next visible frame.

| Palette branches | Entry-to-success cost | LY at success |
| --- | ---: | ---: |
| Both skipped | 3,916 normal-speed T-cycles | 0 |
| BG and OBJ copied | 5,540 normal-speed T-cycles | 2 |

The ten-line VBlank is only 4,560 T-cycles, and the publisher already starts
partway into it. The extra two palette branches add 1,624 T-cycles. Even the
palette-skipping return completes cleanup/OAM after the frame wraps, although
its maps are ready before scanning begins.

OBJ byte indexes 22-32 are attempted with `STAT=$8f`, LY 0 and SameBoy's CGB
palette-access block active. SameBoy's memory implementation rejects the data
while still auto-incrementing the palette index. The publisher acknowledges
success and clears both dirty flags without detecting or retrying these writes.
Indexes 28/29 survive as incorrect OBJ palette-3 color data on the Bayleef,
Feraligatr/Pidgey and sparse-roster examples. Other rejected bytes can match by
coincidence, concealing the defect visually.

This is a hardware access-window failure, not a slow icon decoder. Caught-ball
OBJ slot 1 is outside the rejected index range and is correct in this suite.

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

## Fix Direction, Not Yet Implemented

Treat this as a complete Listing handoff, with a separate cache-preparation
step. Preserve the existing animation scheduler and graphics allocations.

### Palette Ownership And Safe Publication

Explicitly request the Listing-owned palette restore when staging its layout,
rather than inheriting whatever dirty flags the previous transition left.
Then make the Listing publication honor actual legal write windows before
acknowledging completion. A dirty-flag-only change is insufficient.

The preferred first preflight is a Listing-specific commit profile: retain the
VBlank map transfers, use STAT-protected palette writes if the palette work
extends into visible lines, and complete palette/OAM preparation before the
Listing's first dependent pixels are scanned. On the measured layout, the
first cursor OBJ is at line 34 and side BG icons first use slots 2-7 at line
40. BG slots 0/1 are already correct and must remain untouched by that delayed
range. This provides a much less restrictive legal completion boundary than
pretending the entire operation fits in VBlank.

This is a proposal, not a proven fix or a reason to merely relax the existing
gate. Preflight the protected loop and OAM DMA against late admitted entry,
all viewport positions and relevant interrupt phases. Reject/defer a
transaction that cannot meet its first-use boundary. Preserve the existing
Description publication behavior with a Listing-only branch.

An alternative is to prepare Listing-only palettes after their final outgoing
Description use, then publish the completed maps/OAM in the following VBlank.
That requires an explicit last-use/admission contract and guaranteed timely
handoff to avoid showing the old Description with new colors. An opaque
multi-VBlank transition is a simpler fallback but introduces a visible staging
frame. Reordering the same oversized unguarded writes merely moves the risk.

### Cache Repair Without LCD-Off

Reuse matching cache rows and refill only missing row tags while the outgoing
Description remains visible and animation production is canceled. The
existing `Pokedex_PrepareGridCacheRow` and
`Pokedex_UploadPendingGridCacheRow` already provide staged ownership and an
LCD-on uploader: three exact eight-tile HBlank DMA transfers per physical row,
then tag publication. A far jump may need all rows, but it should not require
disabling the LCD or exposing half-built Listing state.

Keep the window hidden and OAM locked until cache, maps, palette targets and
selection metadata are complete. This should remove the white/old-page flash;
latency improvements from reusing rows still need measurement. Do not promise
a faster far-jump refill merely from switching to LCD-on transfers.

No extra animation slots, resident dictionary, timeline data or VRAM allocation
is indicated. Existing pending-row buffers, owner request and palette flags
appear sufficient; an exact ROMX code cost belongs to implementation preflight.
No additional ROM0, WRAM0 or HRAM reservation is currently justified.

## Unreproduced And Adjacent Findings

- The outgoing Description does reappear after LCD re-enable, but the older
  eight-pixel downward displacement/upward scroll was not reproduced. Hardware
  and mirrored SCY remain zero throughout these traces.
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

No further manual SameBoy capture is needed to establish the three confirmed
causes. Additional reproduction evidence is still needed for the unresolved
displacement, placeholder and caught-ball symptoms if they survive the
complete Listing handoff correction.

## Reproduction Tool

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
```

The first command emits `report.json`; this investigation's complete aggregate
is also saved as `matrix-report.json` because later focused control reruns used
the same output directory. Each case retains its own report, write/frame trace,
before/after images and pre-B save state. The source checkpoint suite and
matching symbols are required; the tool does not silently accept a different
ROM link. After a game fix, regenerate matching normal-input checkpoints and
rerun this matrix, then check Selected entry/animation and ordinary Listing
scrolling for shared-publisher regressions.
