# Automated Cold Listing Acceptance

## Scope

This adds a host-only normal-input suite to the headless SameBoy tooling. It
does not change the cartridge, scheduler, audio player, installed save, or
instrumentation. The existing relocated first-publication replays remain useful
for instruction/cycle analysis, but cannot establish correctness of Listing
selection and startup. This suite covers that missing path.

The user reports a complete New Dex internal-paging pass with no animation or
sampled-cry misses during uninterrupted playback. Unown and the corrected finite
Seviper animation also passed manual cold entry. The one rapid-paging audio miss
remains the separately deferred outgoing-cry issue, not part of settled playback
acceptance.

## Inputs

- ROM SHA-256: `412527bdecc0c55c90a63b1d268ee7f7812788649e6936035dfd86a437e9dff7`
- Symbol SHA-256: `95a72958f693330d4c472a4e2c65196072879f63ee843829510b9c7bdcba905f`
- Battery snapshot SHA-256: `dd139ae92628aad90b33af214cab9e0c0885290640c49b579ae9a5c58ecac5c2`
- SameBoy source commit: `213a12ce93d66b105a113debd9396306066a7cfc`
- Hardware model: CGB-E, normal CPU speed. Host execution is accelerated without
  altering emulated instruction, interrupt, PPU, or DMA timing.

The installed ROM was used as a read-only input because the root ROM had been
moved out of the repository. Its assets were verified against the local linked
symbol file and generated graphics. Both cartridge and battery data were copied
into the local output directory before starting emulation. The runner never
saves battery data back to the source path.

## Method

1. Boot the isolated cartridge/save copy with SameBoy's CGB boot ROM, choose
   Continue, open the start menu, and enter the New Dex with normal key inputs.
   Abort rather than selecting New Game if Continue is unavailable.
2. Navigate the complete three-column Listing with real D-pad input. Save a
   host checkpoint for each resting Listing selection, with input released.
   No owner, species, palette, cache, flag, or dictionary RAM is injected.
3. Restore the appropriate neighboring checkpoint independently for each
   species. Move onto the target and press A at the next input opportunity.
   Horizontal selection and vertical row-scroll entry are both exercised.
4. At the actual A-accept handler, require exactly the native base dictionary
   (`width * width` tiles), no animation dictionary services, no animation
   upload services, and zero upload offset. A warmed case fails qualification;
   it cannot silently count as a cold pass. Warming remains enabled in the ROM.
5. Check the static portrait's tilemap, bank attributes, and 2bpp pixels at
   Selected-page reveal, before the cry/animation starts.
6. Let the complete main/hold/idle sequence and cry finish without input.
   For every publication, compare its event/frame identity, map, attributes,
   and all 49 rendered tiles with the linked source assets. Check deadlines
   against both the byte-sized display counter and independent SameBoy elapsed
   cycles, so a whole counter-wrap stall cannot pass. Require publication during
   VBlank. The final base-restoration event is checked too.
7. Monitor the actual animation-miss routine and the sampled timer's
   cache-empty branch. Natural cry completion is distinguished from exhaustion
   by zero remaining blocks. Require all sound-effect channels to be idle before
   ending the uninterrupted test, including synthesized cries.
8. Press B and record logical return-to-Listing separately. Each next test
   restores its own Listing checkpoint, so a return failure cannot contaminate
   unrelated species. First misses and timeouts save diagnostic emulator states
   and the latest rendered screen to the output directory.

The core driver has no command to write emulated RAM or patch ROM. Checkpoints
and copied battery data are local test artifacts, not replacements for the
user's SameBoy state slots.

## Results

| Check | Result |
| --- | --- |
| New Dex species tested | 373 |
| Confirmed cold at A acceptance | 373 |
| Passed every check, including static reveal | 372 |
| Correct initial static portrait | 372 / 373; Drapion issue below |
| Completed animation and cry | 373 |
| Sampled cries completed naturally | 122 |
| Synthesized-cry controls completed | 251 |
| Animation publications checked | 5,849 |
| Authored display intervals checked | 47,259 |
| Animation misses / sampled cache underruns | 0 / 0 |
| Incorrect animated maps, attributes, or frontpic tile pixels | 0 |
| Late, missing, duplicate, or reordered publications | 0 |
| Logical B-return checks passed | 373 |
| Source cartridge/save changed by this run | No |

Each species' authored main/hold/idle duration matched exactly in display
intervals. This does not require each copy to finish at an identical instruction
or scanline within its legal VBlank publication window.

These results complement the user's complete internal-paging pass. Repeating
every cold entry manually is not required for this instrumented build.

### Manual Presentation Follow-Up

2026-09-21: The user reports no visible animation issues in Chikorita, Bayleef,
Meganium, Dusknoir, Rampardos or Luxray. This covers both synthesized and sampled
cry species visually; it is not a separate waveform audit. The user also
confirms Drapion's overflow and recurring B-return palette errors, both of
which remain in the backlog. A newly reported rapid vertical-to-horizontal
input error is recorded as `DEX-NAV-02`; the normal-input cold suite does not
cover that rapid direction sequence.

### Static Reveal Finding: Drapion

The additional static-reveal audit catches the already logged category-text
problem affecting the portrait too. Before animation, portrait cell 28 (row 4,
column 0 within the 7x7 picture) contains tile `$ad` instead of base tile `$04`.
Its attribute is correct. All 25 subsequent publications are correct, and the
175-interval animation and sampled cry finish with no miss.

`DisplayDexEntry` places the category at screen `(9,4)` through `PlaceFarString`
without a field-width limit. Drapion's `Ogre Scorpion` is 13 characters. In the
20-column WRAM map, its last `o` and `n` land at `(0,5)` and `(1,5)`; the latter
is this portrait cell. `$ad` is precisely the lowercase `n` font tile. The VRAM
tilemap evidence at `$00:$98a1` matches that mechanism. This is text overflow
during page construction, not an animation producer/deadline failure. The first
animation publication restores the correct portrait map.

The result is intentionally retained as a failing `static_reveal_tiles` check;
the suite exits nonzero rather than hiding a known bug. Details were added to
`DEX-UI-02` in the backlog. No game fix was attempted. Mew's separately reported
category truncation still needs its own diagnosis.

An initial version of the extra reveal probe counted a few pending instructions
twice when an interrupt was dispatched before they executed. The final driver
uses SameBoy's executed-instruction callback instead of a pre-dispatch PC poll.
The entire suite was rerun after that host-only correction; Drapion is the only
remaining failure.

## Reproduce

From the repository root:

```sh
python3 -m tools.dex_timing.cold_listing \
  --rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --battery /Applications/SameBoy/Games/pokecrystal.sav \
  --output build/dex-cold-listing \
  --jobs 8
```

`--rom` defaults to the root `pokecrystal.gbc`. `--sameboy-source` defaults to
`~/Documents/GitHub/SameBoy`; `--boot` defaults to the installed SameBoy app's CGB
boot image. A local C compiler is required. The battery input must have all New
Dex entries seen, New Dex mode selected, and a valid first-seen Unown form A.
The tool does not unlock species or correct saves itself.

Use `--species chikorita dusknoir weavile luxray unown_a seviper` for a focused
run. `--reuse-listing-states` avoids repeating normal-input checkpoint discovery
only when ROM, symbols, save, boot ROM, core source, and driver provenance match.
Do not reuse these states after rebuilding or cleaning up instrumentation.

Outputs under `build/dex-cold-listing/`:

Commit-review follow-up (2026-09-21): the entire root `build/` directory is now
ignored, including these outputs. Keep the runner, audit tests and this results
document, not generated states, images, binaries, copied game inputs or per-run
logs. No build files were tracked, and the files remain available locally.

- `provenance.json`: input and host-source hashes, including the SameBoy commit.
- `summary.json`, `totals.json`: aggregate results and independent return status.
- `NNN-species.json`: cold-entry state, reveal/publication evidence, final state,
  precise event timing, and any failure details.
- `listing-states/`: actual normal-input predecessor states.
- Failure-only `.s0` and `.ppm` files: first miss, entry/finish timeout, or return
  failure evidence. The screen image is the last rendered image, not a claim
  that the paused instruction has already become visible.

Host audit tests:

```sh
python3 tools/test_dex_cold_listing.py
python3 tools/test_dex_target_regression.py
```

The new audit has negative controls for false-cold qualification, wrong tiles
and maps, static-reveal corruption, late/duplicate/missing publications, counter
wrap aliases, unsupported CPU speed, incomplete cries, and both miss types.
All 14 new audit tests and 11 existing target-regression tests pass.

## Limits And Next Gates

- This is one verified-cold normal-input route per species, not exhaustive
  phase, direction, repeated-input, or save-state exploration. Earlier focused
  timer-phase regression remains separate evidence.
- Unown A is tested here, not all 26 forms; Egg is not a New Dex entry. The
  broader 399-asset structural checks are a different suite.
- B-return success means the input loop and expected selection were restored.
  It does not certify minisprite palettes, text, layout, or every transition
  frame. The deferred Listing/Description bugs remain open.
- Frontpic 2bpp content and bank attributes are checked, not displayed RGB
  palette correctness or subjective audio quality. No waveform listening test
  was performed by this harness.
- Warm entry, rapid cancellation, A-button description paging, New Dex Entry,
  Stats, and battle are not covered. No conclusions about those owners follow
  from this pass.
- Repeat this suite after removing instrumentation or warming. Those changes
  can alter timing even if they are intended as cleanup.
