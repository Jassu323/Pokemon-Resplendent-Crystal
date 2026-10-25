# Registration Local Scheduling Scope

Date: 2026-10-15. Scoping diagnostics only; neither alternative replaces the
reviewed interactive-registration prototype.

## Conclusion

Keep the existing prototype. Reducing registration's bank-call overhead is
cheap in cartridge space, but the two measured adjustments trade scheduling
wins for losses rather than providing a reliable fix. The narrower option
has no median improvement and a very small mean improvement. Neither justifies
promotion solely to address the four historical responsiveness alerts.

This does not prove that every local optimization is unsuitable. It means no
clean fix was found in these two small changes. A further investigation would
need to address safe-window admission deliberately, not assume that fewer CPU
instructions always produce a faster displayed page.

## Protected Baseline

- Frozen source: `build/interactive-registration-dev07-20261015/candidate/`.
- Frozen ROM SHA-256:
  `1abe990d9d96ef34a910e444c6990aa9e745c8827d48946834aa179a29cc8634`.
- Existing review ROM remains identical to that frozen ROM.
- Production ROM remains SHA-256
  `52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
- All diagnostic source copies, ROMs, private saves, traces, patches and media
  are under `build/interactive-registration-local-scope-20261015/`.

Production runtime sources and the player's main save were not edited. The
diagnostic alternatives are not release-qualified ROMs.

## Two Adjustments

### Group The Entire Active View Service

Registration normally makes separate far calls to prepare the portrait,
service its producer, commit its prepared work, and service the lower panel.
Regular Selected already has a block that performs those actions in the same
order, using local calls for the portrait routines.

The first diagnostic replaces registration's whole service block with one
far call to `PokedexSelectedMon_Update.service`. It retains registration's own
input, fixed species, End/B exit and owner-loop pacing. It does not call the
regular Selected input/species-navigation controller.

Linked cost versus the frozen prototype: **45 fewer ROMX bytes**, zero added
ROM0, WRAM0, WRAMX, HRAM or SRAM. Only the private copy of
`engine/pokedex/new_pokedex_entry.asm` changes.

The code change is mechanically simple, but its timing effects are not
uniform. In the controlled continuous-session sweep, Togekiss's third Mov
page changes from **99.59 ms / 5.95 frames** to
**317.06 ms / 18.94 frames**, an added **217.48 ms / 12.99 frames**.
The largest effects are on Mov pages, not the original Info operations.
Reject this option for responsiveness.

### Group Only Info Servicing

The second diagnostic checks the active view first. Only Info uses the shared
service block; Desc and Mov retain registration's separate calls and existing
order. The old, now unreachable Info dispatch is removed from that fallback.

Linked cost versus the frozen prototype: **3 additional ROMX bytes**, zero
added ROM0, WRAM0, WRAMX, HRAM or SRAM. Again, only the private registration
source changes. A named public alias at the existing Selected service boundary
would add no emitted bytes if this were ever promoted; relying on an internal
`.service` label should not become an undocumented integration contract.

The code complexity is low. Timing/verification risk is moderate because
changing one completed page changes when subsequent input and animation work
meet the existing deadlines. Even unchanged Mov service code can receive a
different playback/input phase later in the session.

Examples from the fresh controlled comparison:

| Registration operation | Baseline ms / frames | Info-only ms / frames | Change ms / frames |
| --- | ---: | ---: | ---: |
| Treecko, Desc to Info | 99.02 / 5.91 | 65.53 / 3.91 | -33.49 / -2.00 |
| Moltres, Desc to Info | 99.02 / 5.91 | 81.87 / 4.89 | -17.15 / -1.02 |
| Toxicroak, Desc to Info | 82.28 / 4.91 | 99.15 / 5.92 | +16.88 / +1.01 |
| Delibird, eighth Mov page | 98.60 / 5.89 | 132.08 / 7.89 | +33.49 / +2.00 |

Across 7,069 matched registration operations, the median change is
**0.00 ms / 0.00 frames** and the mean is
**-0.134 ms / -0.008 frames**. There are 101 operations improving by more
than half a frame and 52 worsening by more than half a frame. These are counts
in a fixed scripted sequence, not estimated player-facing probabilities.
The small mean gain is not sufficient grounds to accept new tail delays.

## Historical Outliers And Fresh Controls

The historical Primeape, Tyrogue, Beldum and Toxicroak alerts remain valid
observations in their retained traces. However, the fresh unchanged-baseline
replay itself has different timings on those operations. Comparing an old
baseline trace to a new alternative fixture would wrongly credit all of that
difference to the code adjustment.

This was caught during scoping. Initial apparent two-frame gains on Primeape,
Tyrogue and Beldum are not counted as controlled code benefits here.
The media under `controlled-media/` uses fresh baseline fixtures; the earlier
`media/` captures are exploratory and must not be used for that conclusion.

The old native donor reaches registration at physical T-cycle 134,557,394;
the fresh donor reaches it at 135,119,182. Both report LY 11, but their saved
controller/audio history is not an interchangeable timing control. The source
of that earlier native-history difference was not isolated in this scope.
The baseline ROM hash is unchanged. The three fresh runs have identical
recorded pre-entry donor summaries and use freshly rebuilt, link-specific
fixtures. No checkpoint is transported between ROM links.

In the fresh controlled runs, the first three historical operations display
in approximately 65 ms in all three ROMs. Toxicroak displays in 82.28 ms in the
baseline and grouped version, and 99.15 ms in the Info-only version.
This reinforces that the issue depends on playback/controller history, not a
permanent species-specific cost or duplicate Info preparation.

## Safety And Verification

Both adjustments keep the existing animation/audio priority order, lower-panel
admission checks, VBlank publication code and owner-loop pacing. Neither widens
the READY staging limit (`LY < 84`) or the lower-panel VBlank publication window
(`144 <= LY < 147`). Neither adds interrupt work. The existing
`docs/battle_animation_interrupt_timing_contract.md` remains binding.

Scoping coverage, separate from the full release regression:

- Fresh baseline plus both alternatives: all 373 base species, 7,069 page/tab
  requests per owner per ROM, ordinary Selected and registration controls.
- No semantic, rendered-pixel, authored-playback or cry-content failures in
  those continuous-session sweeps. All 7,069 ordinary Selected operation
  timings are identical between the three fresh ROM runs.
- Eighty detailed timing probes per ROM: five species, two owners, active or
  settled playback, and four input phases. No correctness/playback failures.
- Nine context/bank/memory/interrupt-contract tests per alternative pass.
- No full battle, Tower, all-Unown-form, interrupted-save or comprehensive
  registration-exit regression was rerun for these diagnostics.
- Frame comparisons were inspected; human visual and listening approval are
  not implied. This scope introduces no new audio recording claim.

## Evidence And Reproduction

The diagnostic directory contains `comparison.json`, `scope.py`, and per-option
`change.diff`, `context-contracts.json`, `candidate/` and `catalog/` evidence.
The grouped detailed phase probes are under its earlier `qualification/`
directory. Each input manifest identifies its linked ROM and symbol hashes.

Controlled frame comparison:
`build/interactive-registration-local-scope-20261015/controlled-media/controlled-info-only-timing.png`.
Treecko illustrates a gain; Toxicroak illustrates a loss. Each row shows native
complete rendered displays after the corresponding accepted request, enlarged
with nearest-neighbor scaling. No playback-speed alteration is used.

To repeat a continuous sweep, replace OPTION with `grouped` or `info-only` and
use a fresh output directory:

```sh
python3 -B -m tools.dex_timing.interactive_registration_regression prepare \
  --candidate build/interactive-registration-local-scope-20261015/OPTION/candidate \
  --output build/interactive-registration-local-scope-20261015/OPTION/FRESH \
  --no-forms --jobs 8
python3 -B -m tools.dex_timing.interactive_registration_regression run \
  --output build/interactive-registration-local-scope-20261015/OPTION/FRESH \
  --jobs 8
```

The driver protects existing evidence from overwrite. Never relink a candidate
underneath an existing fixture manifest.
