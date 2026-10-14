# New Dex Entry Visual Prototype

The accepted red-footer layout is now integrated with the October 14 cleanup.
See [Cleanup Implementation](pokedex_cleanup_implementation.md) for the exact
production link and full regression. The prototype-only status and space
figures below are retained as historical records of the separate builds.

## Red Footer Revision, 2026-10-14

The current review build is `build/dex-new-entry-visual-20261014-red-footer/`,
SHA-256 `a5dd313b939a99d92c2b18169be403f14d6a052877890a382005a420d53793fe`.
It replaces the former dark-gray tab/footer strip with the red Dex background,
including the exposed right-edge column. The cursor cell uses an otherwise
unused BG palette slot copied from the existing UI palette, with its font
background mapped to red. Its hidden phase uses the red fill tile instead of
the font's horizontal-line tile. The shared `BlinkCursor` routine is unchanged.

This revision costs 50 more ROMX bytes than the gray-footer build below:
277 ROMX bytes total over production, with zero added ROM0, WRAM0, WRAMX,
HRAM or SRAM. No new graphics are needed. The two-page A/B flow is unchanged.
Paired entry/publication and page-two timings have zero display-frame difference
from the preceding gray-footer prototype.

The Info host assertion has also been corrected: READY handoff is allowed before
scanline 84, not before the obsolete scanline 64 cutoff. The test now covers all
154 scanlines, and a new method checks frame-counter mismatch, active portrait
upload, insufficient sampled-cry cache and the sufficient-cache boundary.
The runtime Info admission rules are not changed.

Current-build verification passed:

- All 87 existing/updated host tests on production and the candidate, with no
  failures, errors or skips. The former LY-64 exception is now resolved.
- Twenty registration contracts on each build, plus seven footer-palette
  isolation/bank-restoration cases on the candidate.
- Fresh native catches for Caterpie and Dusknoir on both links; 120 paired
  representative animation/page/early-exit cases.
- 8,314 candidate input-offset/stress cases, 746 cases over all 373 selectable
  species, 1,119 hardware-layout snapshots and 60 native screenshot/pixel audits.
- Four party/PC catch-return scenarios with naming declined, plus four with a
  nickname entered and End selected, across both links.

The entire bottom eight-pixel band is checked against the linked UI red, with
only the existing white continuation glyph permitted in its cursor cell. The
palette check also verifies that every other BG palette is left unchanged.
All resident mapping and publication budgets remain unchanged.

This small revision reruns registration and host coverage, not the complete
standard Dex/Moves or full-game campaign. Those broader Dex results below belong
to the preceding gray-footer link and are retained as historical evidence, not
relabeled as results for the new binary. Full-game promotion testing remains
pending.

The installed `pokecrystal-dex-new-entry-visual.gbc/.sym/.map` were updated;
the existing SameBoy prototype battery was deliberately not overwritten.
Production ROM and the player's main save remain unchanged. The original
gray-footer build and its evidence are retained below as the rollback point.

## Decision And Review Build

The remainder of this report records the preceding gray-footer revision.

Implements option A from [the scope](pokedex_new_entry_description_scope.md):
match the Selected Pokemon Description content panels, while retaining the
two-page post-catch flow. Info/Moves/Area navigation and the future Selected
screen audit are not part of this prototype.

Baseline: production commit `81ff02a25`.

| Build | SHA-256 |
| --- | --- |
| Production | `e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e` |
| Final visual prototype | `1f12b8ca062209fc5516cbaa8203b962baa64fa773c18387ff272fd0f1bb42da` |

Review files are in `build/dex-new-entry-visual-20261013-v3/`, with stem
`pokecrystal-dex-new-entry-visual`, and were copied to SameBoy's Games folder.
The `.sav` is a separate Route 30 test copy
with 99 Master Balls and cleared caught flags, so catching an ordinary wild
Pokemon displays registration. It is not the player's main save. Production
code, production ROM and the main battery have not been changed.

Press A or B to advance to page two, then A or B again to leave. The footer
retains the registration continuation indicator rather than displaying
nonfunctional `Desc Info Mov Area` controls. This is the intentional difference
from Selected Description; the content-panel layout is shared exactly.

## What Changed

- `_NewPokedexEntry` uses the existing Description background, divider, page
  badge and exposed right-edge column, with an explicit page-one reset.
- The existing Description printer supplies the same name, number, category,
  height, weight and authored text. National IDs and descriptions are unchanged.
- A registration-specific adapter applies the Description palettes, including
  the dark-gray footprint background and one or two compact type badges.
- Type badges use the same remapping primitive, OBJ colors and coordinates as
  Selected Description. Monotypes clear the unused second four-sprite slot.
- Type upload staging reuses 64 or 128 bytes of the already allocated 512-byte
  `sNewDexEntryUploadBuffer`, not the live battle graphics WRAM0 overlay.
- Registration keeps its safe bank-0 footprint tiles, recolored to the same
  palette. Moving them to Selected's bank-1 footprint location would conflict
  with several species' resident animation dictionaries.
- Page two atomically publishes both changing badge cells plus its 90 text
  cells. Its publisher is registration-only; no generic interrupt overhead was
  added.

The resident animation/cry owner, authored frame durations, first/final picture
publication, immutable text transaction, final-picture acknowledgement,
normal-speed policy, input edge handling, post-catch delivery and naming flow
are retained. No generated font architecture or data-table redesign is included.

### Linked Space Cost

All figures are decimal bytes relative to current production, without cleanup:

| Resource | Added |
| --- | ---: |
| ROMX | 227 |
| ROM0 | 0 |
| WRAM0 | 0 |
| WRAMX | 0 |
| HRAM | 0 |
| Allocated SRAM | 0 |

There are no new assets, persistent fields or save migrations. All existing
RAM/SRAM/HRAM symbol addresses remain unchanged. Zero added ROM0 does not mean
byte-identical ROM0: the cartridge checksum and two linked banked-address
operands change. Generic VBlank/STAT implementations are not modified.

The old 126-byte registration shell remains linked but is no longer called by
registration. Do not combine its removal with this review: re-audit it and the
other deferred cleanup targets after the visual prototype is accepted. The
existing shared entry printer and footprint helpers remain live.

## Measured Timing

Paired generated-species contexts from fresh native catch checkpoints, using
20 representative species and the exact production/candidate links. One CGB
display interval is 70,224 base-clock ticks, or 16.742706 ms. These are physical
display intervals, not logical DelayFrame counts.

| Metric | Difference From Production |
| --- | --- |
| Registration entry to first portrait publication | Median 7 frames faster: 117.199 ms; range 6-8 frames faster: 100.456-133.942 ms |
| A input to complete visible page two | No display-frame difference; both 3-4 frames, or 50.228-66.971 ms |
| Authored portrait sequence after its first publication | No difference in frame ordering or durations |

The entry result is the median of paired deltas, not a subtraction of the two
independent medians. First publication is an explicit owner milestone, not a
claim that every entry transition or complete capture is 117 ms faster.

The improvement comes from copying the exposed Description edge while the
LCD is already disabled, eliminating the old LCD-on edge setup waits. The new
type-badge work is a one-time upload. Page-two physical timestamps differ by at
most four base-clock ticks (less than 0.001 ms) in the representative comparisons,
without changing the displayed frame count.

The final 92-cell text publisher's last write is at 2,016 T-cycles, with a
2,280-T minimum available window and 264-T write margin. Picture publication
remains at 1,108/1,704/1,708 T for map/first/final commits, with the prior
716/120/116-T margins. The existing admission cutoff was not relaxed.

## Tests And Evidence

Fresh normal-button captures seeded the generated contexts; old CPU states were
not reused after linking. Counts overlap and must not be summed into a single
grand total.

| Check | Final-Build Result |
| --- | --- |
| Fresh native catch setup | Two species per build, four total; pass |
| Paired representative playback/page/early-exit cases | 120 cases; pass |
| Per-display input-offset and held/mashing/quick A/B sweep | 8,314 candidate cases across 20 species; pass |
| All selectable species, natural playback and page/return | 746 cases across 373 species; pass |
| All-species shell, attrs, footprint, type graphics/palettes/OAM checks | 1,119 hardware snapshots; pass |
| Representative captured page-one/page-two/settled screens | 60 snapshots; pass |
| Resident structural mapping | 399 species/form assets, 2,121 pictures; pass |
| Linked registration contracts and auditor negative controls | 20 production and 20 candidate tests; pass |
| Real party/PC catch follow-through with nickname declined | Four paired scenarios; pass |
| Real party/PC catch follow-through with nickname accepted | Four paired scenarios, entered A and selected End; pass |
| Type Matchups native icon pixel spot-check | 16 frames; pass |
| Type Matchups CGB-E navigation/raster/return campaign | 18 selections, 72 navigation cases, 32 input phases, 3,544 legal display frames; pass |
| Type Matchups surrounding return paths | 42 owner reentries, 12 close/reopens, 24 Selected playbacks; pass |
| Existing Selected/Dex host contracts | 86 checks; 85 pass, one unchanged production failure |
| Standard Pokemon Dex campaign | 4,479 cases; pass |
| Extra Unown transitions after Info and Moves | Eight cases each, 96 transitions total; pass |
| Unown content/palette/navigation | 136 scenarios, 2,212 selections and 126 draw-helper cases; pass |
| Moves filtering | 1,692 helper cases; pass |
| Moves Search UI, graphics and navigation | 10 / 1,406 / 2,686 cases; pass |
| Moves mode transitions and surrounding paths | 11 / 2 cases; pass |
| Moves Search form polish and naming-cursor parity | 1,284 / 3,840 checks; pass |
| Moves sort memory | 4,096 helper cases, 16 UI cases, 11 save cases; pass |
| Shared Dex arrow cursors | 1,792 helper cases, 52 locations and 3,328 observed idle frames; pass |

The all-species checks validate independent linked base-stat types, canonical
type graphics and palettes, footprint source bytes, fixed shell/edge cells,
mono-type OAM clearing, actual portrait pixels, authored sequence deadlines,
owner release, caller restoration and atomic page-two pixel/map presentation.
The offset sweep is not an exhaustive Cartesian product of arbitrary inputs.

### Findings Preserved

The initial pixel audit caught a prototype-only footprint palette error: a
`farcall` overwrites input A/HL, so it cannot pass that attribute fill's inputs.
The final build uses direct local attribute stores. The independent audit then
passed every species. The non-CGB fallback was also corrected to pass the
layout selector through B to the original ROM0 dispatcher; this CGB-only review
does not claim a separate DMG/SGB qualification.

The pre-existing Info LY-64 host assertion returns `5 != 0` in both production
and candidate. It is not counted as a pass or repaired as part of this visual
change. It was previously recorded in
[the Unown performance report](pokedex_unown_performance_prototype.md).

The first additional Type Matchups campaign stopped on its return-menu check
because its borrowed all-seen fixture had Unown locked (`wStatusFlags=$91`),
while that particular test assumes five unlocked menu rows. The failed fixture
and raster evidence are retained in `type-fixture-locked-original.sav` and
`type-tests-locked-fixture/`. The private fixture was regenerated with the
existing locked/unlocked fixture helper, then the complete CGB-E campaign
passed, including Type-to-menu-to-list return and surrounding owner reentries.
No game code or assertion was changed to resolve that setup error.

The broader native catch-return runner also records the same encounter-phase
audio-empty event in both builds, at tick 17,506,036 with 45 blocks remaining,
well before registration starts at tick 137,096,328. Registration's focused
animation/cry audits have no misses; the pre-existing encounter observation is
retained and is not hidden by the return-path pass.

This is a registration/standard Dex qualification, not a rerun of every battle
animation, save-corruption/interruption scenario or all surrounding gameplay.
The [full regression suite](full_regression_suite.md) remains the promotion
checklist. Manual review and production integration are still pending.

## Reproduction And Source

Manual game edits are retained as a private patch and new module:

- `tools/dex_timing/probes/new_entry_visual.diff`
- `tools/dex_timing/probes/new_entry_visual.asm`
- `tools/build_new_entry_visual_prototype.py`

The candidate snapshot contains the applied production assembly. Host-only
observer changes distinguish the old 91-cell badge from this 92-cell layout;
they do not add game code or loosen the old audit.

```sh
export PYTHONPATH=tools:.
python3 tools/build_new_entry_visual_prototype.py --output build/new-entry-visual-review --jobs 10
python3 -m tools.dex_timing.new_entry_visual prepare --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual smoke --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual visual --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual sweep --output build/new-entry-visual-review --jobs 10
python3 -m tools.dex_timing.new_entry_visual all-species --output build/new-entry-visual-review --jobs 10
python3 -m tools.dex_timing.new_entry_visual contracts --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual returns --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual nicknames --output build/new-entry-visual-review
python3 -m tools.dex_timing.new_entry_visual dex-prepare --output build/new-entry-visual-review
python3 -m tools.dex_timing.type_full_regression setup --output build/new-entry-visual-review/dex-campaign
python3 -m tools.dex_timing.type_full_regression dex --output build/new-entry-visual-review/dex-campaign
python3 -m tools.dex_timing.type_full_regression moves --output build/new-entry-visual-review/dex-campaign
python3 -m tools.dex_timing.type_full_regression host --output build/new-entry-visual-review/dex-campaign
python3 -m tools.dex_timing.type_full_regression diagnose-types --output build/new-entry-visual-review/dex-campaign
python3 -m tools.dex_timing.dex_arrow_cursors --output build/new-entry-visual-review
python3 -m tools.dex_timing.type_matchups --output build/new-entry-visual-review
```

The builder starts from the current HEAD; use the recorded baseline if restoring
this exact comparison later. A rebuild on a different production revision needs
new hashes, fixtures and evidence. The earlier verified source/build archive
is [here](archived/dex-unused-scope-20261013/README.md).

Final evidence: `visual-manifest.json`, `smoke-summary.json`, `sweep/summary.json`,
`all-species/summary.json`, `visual/summary.json`, `contracts-summary.json`,
`returns-summary.json`, `nicknames-summary.json`, and `dex-campaign/` under the
final private build directory; `arrow-tests/summary.json` and
`type-tests/summary.json` hold the additional cross-mode checks. PNGs are lossless conversions of native PPM
captures; they have not been recolored or repainted.

Environment: Python 3.13.12, RGBDS 1.0.1, SameBoy core
`c4cf7abab79a4e22dc17e0704995976cb2751b2d`.
