# Unown Mode Transition Optimization

Investigation date: 2026-10-14. The user selected the 51-byte candidate; its
[full regression qualification](pokedex_unown_transition_regression.md) passes
with no new regressions. After manual acceptance, the exact candidate was
integrated into production on the same date. The player's save is unchanged.

The remaining Unown performance story concerns **Modes to Unown and back**,
not form paging. Form paging already uses the accepted static decoder and atomic
picture/map publisher. The recommended transition candidate reuses an existing
Dex map uploader, costs **51 decimal ROMX bytes**, allocates **zero additional
RAM**, and substantially shortens the hidden upload interval without removing
the existing hide/reveal barriers.

## Baseline And Evidence

- Source commit: `6b5da51953bdb814581707f95ff5be863340adb4`.
- Production ROM SHA-256:
  `12dda67dca5f739492a06d0e94f312907aacb4e16d0daf5d219619f68ad9978d`.
- Private evidence root: `build/dex-unown-transitions-20261014/`.
- Measurements and paired deltas: evidence root `comparison.json`.
- Candidate source, linked ROM/symbol/map, resource accounting, and source diff:
  its `waits/` and `staged/` directories.
- Reusable host observer: `tools/dex_timing/unown_transition_scope.py`.

These are native SameBoy measurements using normal buttons on copied batteries.
The cartridge contains no timing instrumentation. Time is emulated physical
time from button assertion to the first completely rendered destination frame,
not host execution time or the number of calls to `DelayFrame`.

One physical display frame is 70,224 ticks at 4,194,304 ticks/second, or
16.742706 ms. First response is the existing black hide; completion is the new
whole screen. All tables below use that same clock.

## Where The Time Goes

`Pokedex_InitUnownMode` in `engine/pokedex/pokedex.asm` already prepares a
static frontpic and calls `PokedexUnown_Publish`. That publisher commits the
picture and hardware tilemap together. Initialization then nevertheless calls
`WaitBGMap`, which schedules another four-frame tilemap upload. The CGB layout
subsequently calls `ApplyAttrmap`, adding another four-frame upload wait.

Returning calls `PokedexListing_BeginMenuTransition`, sets the Modes return
state, and explicitly calls `DelayFrame`. The ordinary owner loop also waits
before the next initializer. `PokedexListing_InitModeScreen` then uses the same
four-frame tilemap plus four-frame attribute upload sequence.

Representative current-link post-Info spans, Modern origin:

| Work | Entry ms / frames | Return ms / frames |
| --- | ---: | ---: |
| Hidden palette/OAM barrier | 16.22 / 0.97 | 16.82 / 1.00 |
| Restore 13 borrowed Unown font tiles | 6.46 / 0.39 | Not needed |
| Draw software Unown map | 4.35 / 0.26 | Not applicable |
| Prepare static portrait | 13.08 / 0.78 | Not needed |
| Existing atomic picture/map publication | 9.84 / 0.59 | Not applicable |
| `WaitBGMap` | 66.55 / 3.97 | 65.87 / 3.93 |
| `ApplyAttrmap` | 64.02 / 3.82 | 65.42 / 3.91 |
| Final reveal barrier | 14.89 / 0.89 | 14.88 / 0.89 |

Spans are illustrative, not an additive reconstruction of every latency. Input
sampling, owner-loop boundaries and display completion are also involved;
parent routine spans include their children.

The borrowed font restoration must stay: Selected Info headings reuse 13 of
Unown's resident bank-1 font cells. Removing this restoration would reintroduce
wrong glyphs after visiting Info. It is a real dependency, not unused work.

## Measured Options

Primary comparison: Chikorita after visiting and paging Selected Info, both
Modern/Legacy origins, eight within-frame input phases, 16 cases per version.
Times are medians; frame counts are physical display intervals.

| Version | Entry ms / frames | Return ms / frames | ROMX delta |
| --- | ---: | ---: | ---: |
| Current production | 242.27 / 14.47 | 249.55 / 14.90 | 0 |
| Minimal wait removal | 175.30 / 10.47 | 233.18 / 13.93 | -1 byte |
| Reuse fast hidden-map upload | 125.07 / 7.47 | 98.86 / 5.90 | +51 bytes |

Minimal removal saves 66.97 ms / 4.00 frames entering and approximately
16.37 ms / 0.98 frames returning. The fast-upload candidate saves 117.20 ms /
7.00 frames entering and 150.69 ms / 9.00 frames returning in paired cases.
That is approximately 48% and 60% lower median completion latency.

First-response timing is essentially unchanged: entry 41.36 ms / 2.47 frames
and return approximately 48.64 ms / 2.90 frames. The improvement is the shorter
black interval, not revealing an incomplete screen sooner.

Other initial contexts, also 16 cases per version:

| Prior Selected view | Production entry ms / frames | Fast entry ms / frames | Production return ms / frames | Fast return ms / frames |
| --- | ---: | ---: | ---: | ---: |
| None | 242.28 / 14.47 | 108.34 / 6.47 | 249.91 / 14.93 | 107.60 / 6.43 |
| Info | 242.27 / 14.47 | 125.07 / 7.47 | 249.55 / 14.90 | 98.86 / 5.90 |
| Moves | 242.28 / 14.47 | 116.70 / 6.97 | 249.55 / 14.91 | 99.23 / 5.93 |

The fast uploader is phase-sensitive: it waits for sufficient visible scanlines
for its HBlank transfers. Entry completion spans 101.01-132.39 ms / 6.03-7.91
frames across these contexts, and return 98.47-115.97 ms / 5.88-6.93 frames.
These bounds do not imply a new random workload or cache miss.

The older reconciliation's approximately 249 ms entry number used a narrower
input-phase sample. The fresh eight-phase production median is approximately
242 ms; this difference is not an optimization applied to production.

### Minimal Wait Removal

Only `engine/pokedex/pokedex.asm` changes. CGB entry skips `WaitBGMap` after
the map has already been published; the ordinary attribute/layout/reveal path
remains. Return drops the extra `DelayFrame`, retaining the owner-loop wait.

Complexity and risk are low. The principal dependency is that the CGB publisher
must continue uploading the complete map before entry skips its generic wait.
It is the smallest option, but leaves most return latency intact.

### Fast Hidden Map Upload

The candidate changes three assembly owners:

- `engine/pokedex/pokedex.asm`: after the unchanged atomic portrait/map commit,
  prepare Unown attributes and palette sources without generic publication;
  upload prepared maps through the existing fast helper, then request final
  palettes and retain the normal reveal barrier. Drop the extra return wait.
- `engine/pokedex/pokedex_legacy.asm`: only a return tagged
  `DEXSELECT_STATE_UNOWN_RETURN` takes the fast Modes map upload. Other Modes
  entry sources retain the ordinary path. The return tag is cleared after the
  publication choice, rather than before it.
- `engine/gfx/cgb_layouts.asm`: separate software layout preparation from
  ordinary attribute/palette publication. Existing ordinary layout entry
  points still prepare, upload and apply palettes as before.

`PokedexPerf_FastTownMap` already stages 20x18 software tile and attribute maps
into the two existing bank-3 owner buffers with 32-byte hardware row stride.
With DE set to `vBGMap0`, it transfers both maps through the existing exact
HBlank-DMA helper. It preserves WRAM/VRAM bank selection and keeps interrupts
enabled. The prepared final palettes are not requested until uploads finish.

The maps need not publish atomically while all hardware palettes remain black.
The first visible frame still requires both maps and final palettes to be
complete. Form paging retains its different, already-atomic publisher because
its previous screen remains visible during preparation.

No whole-screen cache is retained. Unown's existing static portrait scratch,
resident glyphs and owner buffers are reused; new ownership does not extend
beyond this hidden transition. Ordinary Modes arrow/description updates retain
automatic BG-map publication after returning.

Complexity is low to moderate. It is a bounded mainline handoff, not a new
interrupt owner or scheduler. Important failure modes for future changes are:

- Exposing final palettes before both maps finish, reproducing transition
  flashes or mismatched tile/attribute frames.
- Reusing owner buffers while another Dex owner, DMA job or cry owns them.
- Losing the return tag too early, selecting the wrong menu row, or failing to
  re-enable ordinary menu map updates.
- Removing the font restoration, or changing a shared helper's bank/destination
  contract without updating this caller.

Do not add work to normal VBlank or LCD handlers for this feature. None changes
here. See the [battle interrupt timing contract](battle_animation_interrupt_timing_contract.md).

### Alternatives Not Worth Adding Now

A retained full menu tilemap/attrmap pair would need 1,152 bytes if newly
allocated in WRAM, before tags or cache-validity state. It is unnecessary when
existing buffers and fast upload already solve the dominant delay.

A new combined entry publisher could transfer portrait, map and attributes in
one protected VBlank. It could avoid duplicated map transfer and a phase wait,
but requires a new entry-only transfer contract and scanline-budget testing.
This option is not built or timed here; no speed or byte-cost claim is made.
The 51-byte reuse version is a better first step than expanding the already
correct form-paging publisher.

## Resources And Qualification

All costs are decimal linked bytes relative to current production, not source
file sizes or the fixed cartridge file size.

| Pool | Minimal candidate | Fast candidate |
| --- | ---: | ---: |
| ROMX | -1 | +51 |
| ROM0 | 0 | 0 |
| WRAM0 | 0 | 0 |
| WRAMX | 0 | 0 |
| HRAM | 0 | 0 |
| SRAM | 0 | 0 |

All existing RAM label addresses remain unchanged. No additional graphics,
VRAM reservations, palettes, OAM entries, save format fields or persistent
state are needed.

Fresh focused checks passed:

- Production and fast candidate: 48 profiling cases each across no prior view,
  Info and Moves, both origins and eight input phases. The minimal candidate
  has 32 cases across no prior view and Info.
- CGB models 0/A/B/C/D: eight post-Info profiling cases per model per ROM;
  CGB E is covered by the eight-phase runs above. No transition failures.
- Fast candidate: 124 caught-form/order layouts, including all singleton forms,
  reversed/rotated/shuffled lists and sparse lists; 1,880 rendered selections
  pass portrait, word, glyph, palette/background, bounds and return checks.
- All 54 locked/unlocked Modes row/presentation/order combinations pass,
  including navigation and subsequent Selected playback.
- Fast candidate: 32 post-Info cases at indices 0/8/255/372 exercise six routes
  each, 192 captured transitions. They also verify subsequent exact Selected
  animation/cry completion and Info pages, including ancestors.
- A fresh matching 32-case production run also passes. Listing-to-Modes,
  cancellation and presentation-switch completion medians differ by 0.00 ms /
  0.00 frames. The final Modes-to-Listing return after Unown differs by
  +0.016 ms / 0.001 frames median, +0.170 ms / 0.010 frames maximum.
- 96 paired settled-screen comparisons match production pixels. Entry compares
  every pixel; return excludes only the 8x8 blinking menu-arrow cell.
- 112 form-paging measurements per ROM: current median 49.0179 ms versus fast
  49.0193 ms, both 2.93 frames. Largest paired increase is 1.41 ms / 0.084
  frames; largest decrease is 2.09 ms / 0.125 frames. Holding Right for 60
  display frames reaches index 10 in every tested phase/origin in both ROMs.

Captured transitions contain only the old whole frame, the black mask and the
new whole frame: no mixed frame, white flash, premature reveal or LCD-off
transition was found. The subsequent full-game/battle campaign passes on this
exact candidate; see the linked qualification report. Physical hardware/manual
audio acceptance is not certified by the automated campaign.

## Recommendation And Review Builds

Proceed with the fast hidden-map upload candidate. Its 51 ROMX bytes are well
inside the earlier 1 KiB ROMX / 100-byte WRAMX optimization budget, with no
premium-memory additions. The smaller option is valid but gives up most of
the return-path improvement for only 52 bytes of linked ROMX savings.

- Recommended ROM: `build/dex-unown-transitions-20261014/staged/pokecrystal-dex-unown-staged.gbc`.
- Its matching `.sav` is a copied all-caught, all-26-Unown fixture, not the
  player's save. Matching `.sym` and `.map` are beside it.
- Minimal alternative: `build/dex-unown-transitions-20261014/waits/pokecrystal-dex-unown-waits.gbc`
  with matching private save/symbols/map.
- Recommended ROM SHA-256:
  `942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc`.
- Minimal ROM SHA-256:
  `fcfc4ff742a9bec76afdf56aeed9eac1e6190d4f4a3693f643bc40ab0147ee74`.

Reproduction uses `PYTHONPATH=tools python3 -B -m
tools.dex_timing.unown_transition_scope`. `setup current` builds the read-only
observer; `test current --prior info --phases 8 --jobs 8` profiles the baseline.
`freeze <label>` creates an isolated source tree; apply its retained
`candidate.diff`, then use `build <label>`, `setup <label>` and `test <label>`.
`neighbors <label>` runs form/menu/adjacent-owner qualification; `models <label>`
checks the other CGB revisions. Fresh output directories are required.

The full regression gate and manual acceptance are complete. The root production
ROM now matches the qualified candidate byte-for-byte. See
[Production Integration](pokedex_unown_transition_regression.md#production-integration)
for the source owners, resource delta and post-integration verification.
