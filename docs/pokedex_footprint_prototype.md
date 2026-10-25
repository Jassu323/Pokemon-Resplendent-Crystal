# Pokedex Footprint Prototype

Initial qualification: 2026-10-16. User visual review accepted. The complete
footprint set is production-integrated as of 2026-10-17 with the reviewed
species-information/responsiveness build; see
[production integration](pokedex_responsiveness_prototype.md#production-integration).
The player's main save is unchanged. The footprint-only costs, comparison
hashes and initial private qualification below are retained historical evidence.

## Changes

All 122 later-species Bulbasaur placeholders in `gfx/footprints.asm` are
replaced with species-specific records: 80 Emerald and 42 Platinum originals.
There are 99 visible marks and 23 intentionally blank footprint regions.
The 251 original species, including their 55 blank footprints, are unchanged.
Descriptions, measurements, evolution records and gameplay code are not edited.

Emerald source commit:
`731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`,
[graphics/pokemon](https://github.com/pret/pokeemerald/tree/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/graphics/pokemon).
Platinum source commit:
`1dc13dcea40c04ab53f1f607de46023dc409ef20`,
[res/pokemon](https://github.com/pret/pokeplatinum/tree/1dc13dcea40c04ab53f1f607de46023dc409ef20/res/pokemon).
The verified originals, per-file hashes/URLs and source pack remain under
`build/footprint-source-review-20261016/`.

Platinum's uniform right-hand padding is omitted, not scaled into the mark.
All output images are 16x16 indexed black/white PNGs. Dark source marks become
white, while white source backgrounds become black in the source PNG. The
existing renderer maps that background to the dark-gray Dex panel. Blank
images compile to 32 bytes of `$ff`, matching the game's existing blank records.
There is no new blank-species flag, alternate symbol or special-case renderer.

## Build And Cost

- Review ROM/save: `build/dex-footprints-20261016/pokecrystal-dex-footprints.gbc`
  and its adjacent private `.sav`, with all 373 species seen/caught.
- Candidate source: `build/dex-footprints-20261016/candidate/`.
- ROM SHA-256:
  `6daf293a82d97e13b3fece67d72f6534fe0789081a39f9e56b182f457dc9a04c`.
- Production/rollback ROM SHA-256:
  `d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.
- ROM0, ROMX, WRAM0, WRAMX, HRAM and SRAM allocation changes: zero bytes each.
- All symbols keep their addresses. Only 2,393 ROM bytes differ, confined to
  the 122 replacement footprint records and the global checksum. All executable
  bytes and the original 251 footprint records are identical to production.

## Verification

Fresh matching-link native SameBoy states were reached through ordinary
controls for production and candidate; no checkpoint was moved between ROMs.
Private fixture saves are all-seen/caught. No live RAM or ROM patch supplies
the selected species, image, palette or navigation result.

- All 373 species in both Modern and Legacy: 746 species/presentation cases
  and 5,968 candidate screen checks, plus 5,968 production controls.
- Eight screens per case: Description P.1, P.2, Info Stats, Mov, Description
  return, internally paged neighbor, internally paged return, and B-return/reentry.
- Independent source masks are checked against linked 1bpp bytes, expanded
  hardware VRAM bytes, tile order, bank/palette attributes and every actual
  displayed footprint pixel. Foreground is raw white; background is raw
  `(41,41,41)` with color correction disabled.
- All 5,968 paired full-screen comparisons are identical outside the footprint
  rectangle. No broad portrait/text/cursor exclusion masks are used.
- 2,238 cold/internal-paging authored animation/cry sequences per ROM pass
  the existing exact playback audit, with no animation or sampled-audio misses.
- 87 current host cases pass, without skips, failures or errors. Eight new
  conversion/pixel-oracle controls pass, including wrong colors, nonuniform
  padding, wrong dimensions and a stale mark on a blank footprint.
- Matched observation times differ by 0 ms / 0 physical display frames. This
  measures these scripted observations, not a separate universal latency study.

An initial supporting host attempt used current banked Info data as its
pre-relocation cost reference and reported `0 != 672` on both production and
candidate. It is preserved under `host-banked-reference/`. The corrected adapter
uses the frozen pre-relocation reference from registration qualification; the
same strict +672-cycle and absolute budget assertions pass. No game code or
test assertion was relaxed for that correction.

The six full-screen contact sheets and four enlarged in-game footprint sheets
were visually inspected across all 373 species. No footprint anomaly was found.
The automated checks and agent image review do not replace the user's manual
approval or claim physical-hardware testing. This is a focused Selected/asset
qualification, not a new full battle or Battle Tower campaign.

Results: `build/dex-footprints-20261016/qualification.json`, `build.json`,
`footprint-import.json`, and the per-link/per-presentation `checks/` reports.
Images are under `review/`, including `production-vs-prototype.png`,
`all-selected-1.png` through `all-selected-6.png`, and `all-footprints-1.png`
through `all-footprints-4.png`. Individual full-resolution images for every
tested screen remain under `checks/`.

## Reproduce

Use a fresh output folder under `build/`. The converter needs the verified
download manifest and originals; the archived source pack contains both.
The prototype driver protects production files and saves and rejects reusing
completed output directories.

```sh
PYTHONPATH=tools:. python3 -B -m unittest tools.test_pokedex_footprints -v
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.footprints build --output build/dex-footprints-FRESH --jobs 6
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.footprints prepare --output build/dex-footprints-FRESH
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.footprints host --output build/dex-footprints-FRESH
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.footprints run --output build/dex-footprints-FRESH --jobs 8
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.footprints qualify --output build/dex-footprints-FRESH
```
