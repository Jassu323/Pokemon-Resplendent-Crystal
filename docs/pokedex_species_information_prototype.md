# Species Information Prototype

Initial qualification: 2026-10-16. The full regression follow-up, **excluding Battle Tower**, is
complete on the exact reviewed link. No new correctness failure was identified
relative to the accepted baseline. This is not an all-raw-tests-clean claim:
one rapid-input stress failure matches a fresh baseline replay, and measured
responsiveness changes were retained for manual review. The user subsequently
accepted the combined responsiveness prototype and requested production
integration on 2026-10-17. All content and renderer changes below are now
integrated with those four optimization bytes; see
[production integration](pokedex_responsiveness_prototype.md#production-integration).
The player's main save is unchanged. Earlier hashes and pending-review notes
refer to the initial private qualification, not a remaining promotion task.

## Review Build

- ROM: `build/dex-species-information-20261016/pokecrystal-dex-species-information.gbc`.
- Adjacent `.sav`: private all-373-seen/caught review battery, not the main save.
- Complete candidate source: `build/dex-species-information-20261016/candidate/`.
- SHA-256: `905f6eab5bd17eaacf5623200eed20c9dd972efa6a65f1b01efc10cc8ad2ddb4`.
- Safe base: accepted footprint prototype, SHA-256
  `6daf293a82d97e13b3fece67d72f6534fe0789081a39f9e56b182f457dc9a04c`.
- Protected production SHA-256:
  `d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.

The footprint artwork from that accepted prototype is retained byte-for-byte.
No artwork additions are needed for the descriptions or page-number extension.

## Content

All 122 later-species placeholders are replaced with full sourced prose:
80 Gen 3 entries use Emerald, and 42 Gen 4 entries use Platinum. Names and
apostrophes follow the assessed mixed-case/font normalization. Honchkrow uses
existing single quotes instead of curly double-quote tiles that the UI reuses.
Wording is not shortened; page/line breaks follow the checked whole-word reflow.

| Pages | Added Species |
| --- | ---: |
| 2 | 31 |
| 3 | 60 |
| 4 | 31 |

All 122 measurements were checked against the sourced imperial values.
Cradily is corrected from 3'03", 60.4 lb to **4'11", 133.2 lb**.
Claydol is corrected from 238.0 lb to **238.1 lb**. Torkoal remains **177.3 lb**:
the 177.2 historical value was a source/rounding choice rather than confirmed
missing data. Other matching measurements and existing category names remain
unchanged. The original 251 complete entry records are byte-identical to the
accepted base.

Source URLs, pinned commits/hashes, normalization and the per-species breakdown
are in the [content scope](pokedex_species_information_scope.md). The
[renderer scope](pokedex_description_multipage_scope.md) records the design
comparison preceding implementation.

## Renderer

The 366-byte semantic table stores P.2/P.3/P.4 offsets relative to P.1 for each
added species. Zero marks an absent page, so the same table supplies page counts
without another count array. Exported page labels let RGBDS resolve and range
check the offsets across the separate entry-data object. The source files also
assert every encoded line's size, including its control/terminator bytes.

The shared lookup resolves the stable 16-bit species index from the transient
ID. The A-on-Desc controller increments and wraps at the real count. The bounded
reader seeks directly to the requested later-species page after its normal
category/measurement skip. Original entries keep their existing P.2 scan.

Cold/staged construction and Area return use the same direct offset helper,
printing only the requested page. The old duplicate P.1-then-P.2 printing and
fixed P.2 badge patch are removed. The existing staged badge preparer chooses
the actual digit before reveal. Info/Mov returns still reset to P.1; Area
returns retain the selected Description page.

The existing 24-byte chunk, three-slice limit, LY admission, animation-first
service and atomic lower-panel publication are unchanged. No new cache, buffer,
interrupt handler work, speed switch or save format is introduced. All shared
`home/` sources and the Dex interrupt/dispatcher source
`engine/pokedex/pokedex_3.asm` are identical to the accepted base.

## Linked Cost

All figures are decimal bytes relative to the accepted footprint prototype.

| Component | ROMX Growth |
| --- | ---: |
| Description data | 12,767 |
| Direct page offsets | 366 |
| Net renderer code, after deleting duplicate printing | 100 |
| Total | **13,233** |

ROM0, WRAM0, WRAMX, HRAM and SRAM growth is **zero**. Existing RAM labels retain
their addresses. The ROM remains 4 MiB. The enlarged custom records use two
available text banks, `$bb/$bc`; bank `$74` retains the original final entries
and Dex order. Splitting placement does not count unused bank capacity as
occupied data. Renderer growth of **466 bytes including metadata** is below
the scoped 768-byte allowance.

## Initial Dex Qualification

Counts overlap; they should not be added into a single total.

- **4,479 standard Pokemon Dex cases**, including every species/sort/presentation,
  menus, visual layouts, edges, Selected tabs, search and mode transitions.
- Moves Dex filter, keyboard, cursor, visual, navigation, result/owner transitions,
  surrounding Dex restoration and sort remembrance phases all pass. No move-use
  battle or acquisition campaign is included in that statement.
- **136 Unown cases**, including 2,212 form selections, pass its graphic/return
  checks. Additional prior-Info/prior-Moves menu-return sweeps pass.
- Type Matchups passes all 18 selections, 72 navigation cases, 790,016 icon-pixel
  checks, raster/idle guards and owner-return paths. Its direct chart-helper
  checks are not a full battle-animation regression.
- Shared arrows pass 52 locations and 3,328 idle frames; 1,792 counter/bank cases
  retain the blink/register contract. The keyboard box is unchanged.
- **868 unique caught Description pages per presentation**, plus wraps: 746
  species/presentation cases and **2,482 captured screens** across Modern/Legacy.
  Footprint pixels, type sprites, borders, badges, text and cold playback pass.
- **732 P.3/P.4 Area cases** cover both presentations, A/B exits, active and
  settled requests, repeated Area entry and exact retained page restoration.
- All **373 species** in ordinary Selected and fixed-species registration:
  **746 cases / 14,382 tab/page operations**, with exact rendered-panel parity,
  complete authored portrait playback and natural cry completion.
- **224** normal stress cases plus **488** rapid-Description cases. The latter
  exercise every added species at four input phases and check the final page
  against accepted requests, including queued-job replacement/wrap.
- **87 standard host controls plus 6 new multipage controls**, with no failures,
  errors or skips. New controls cover source-text hashes, all offsets/counts,
  every static seek, measurement words, ID reuse, index boundaries and invalid
  offset requests. Every imported full text matches its normalized pinned source.
- A fresh 20-species baseline gives **40** Selected/registration comparisons;
  all 40 cry-content signatures match the accepted footprint base.

No game fault requiring a runtime correction was found in these campaigns.
`qualification.json` records the exact link, counts, excluded campaigns and
protected-input checks.

### Timing

These are request acceptance to the first complete displayed panel, not just
time spent executing the helper. Frames are physical display equivalents.

| Screen | P.3 Median | P.3 Maximum | P.4 Median | P.4 Maximum |
| --- | --- | --- | --- | --- |
| Selected | 49.46 ms / 2.95 frames | 66.21 ms / 3.95 frames | 49.46 ms / 2.95 frames | 66.20 ms / 3.95 frames |
| Registration | 49.40 ms / 2.95 frames | 66.18 ms / 3.95 frames | 49.27 ms / 2.94 frames | 66.01 ms / 3.94 frames |

The matched baseline comparison uses the **first P.2 request**, not wraps after
different amounts of P.3/P.4 navigation. Ordinary Selected is exactly **0 ms /
0 frames different** for all 20 sampled species. Registration changes range
from **-0.844 to +0.279 ms / -0.0504 to +0.0167 frames**. Full new text replaces
placeholders in ten of those species, so those pairs are not a pure code-only
benchmark. These measurements show no display-frame-scale regression in this
sample, not a universal latency guarantee for every input phase.

The largest isolated slice remains **5,464 CPU T-cycles**, below the existing
6,144-cycle limit. No larger time slice or relaxed deadline was needed.
The source-bank seek changes the work, not the visible-transfer size.

Detailed timings: `description-timings.json` and
`baseline-description-comparison.json` under the prototype directory.

## Full Regression Follow-Up

Fresh evidence is in `build/dex-species-information-20261016/full-regression/`.
Its `qualification.json` checks completion of all 37 orchestrated actions,
preserved failures and corrected test-only controls, matching ROM hashes and
protected inputs. The accepted footprint prototype is the comparison baseline;
`baseline-production-equivalence.json` verifies that all executable bytes and
symbol addresses match production. Their only 2,393 differing bytes are later
footprints and the cartridge checksum. No cross-ROM CPU checkpoint was reused.

The standard campaign acceptance report is
`runtime-regression/full-regression.json`; the broader final audit additionally
retains the registration stress exception. Its raw registration summary still
says `automated_suite_pass: false`. Neither that result nor the original failed
contract/contest logs was overwritten with a clean pass. Battle Tower was
explicitly excluded, and no Tower campaign directory was created.

Counts overlap and must not be summed into one end-to-end total.

| Coverage | Result |
| --- | --- |
| Standard Pokemon Dex | 4,479 cases; no failures |
| Moves Dex/search/sort | All 11 UI/helper/save phases pass |
| Additional Selected Info/Mov | 746 cases each; 400 stress cases pass |
| Full authored Selected playback | 2,238 cases pass |
| All battle animations | 7,312 renderer calls; exact timing, logic and rendered sequences |
| All moves through normal battle input | 1,332 rows / 666 pairs; same 34 baseline exception identities |
| Historical 100-move battle matrix | 1,600 rows / 800 pairs; no issues or duration changes |
| Sampled audio | 960 rows / 480 pairs; same content and same 32 known timing misses per link |
| Menus/custom inventories | 1,792 input/register contracts, 464 custom cases, 148 popup selections pass |
| Persistence | 2,380 helper, 1,490 cold-boot, 152 interrupted-write and 150 interrupted-repair cases pass |
| Acquisition, learning, battle discovery | Positive/negative, migration, called/charge/semantic and Struggle checks pass |
| Interactive registration | 373 Selected + 398 species/form registration runs; 14,682 continuous operations pass |
| Registration exits | 33,966 replays; 8,614 unique committed B/End exits; no restoration failure |
| Registration input stress | 12,735 pass; one raw failure matches the accepted baseline, discussed below |
| Active Description return | 1,492 cases pass; six-model Description matrix adds 1,536 passing cases |
| Numeric planner | 3,072 linked row/value cases pass |
| Lifecycle | 336 entry/exit, 36 route and 88 expanded exit cases pass |
| Type/Unown/model/music | All six emulated CGB revisions pass; both 122-entry music/SFX sweeps pass |

The current standard host group passes all 87 tests on each link, with no skips
or errors. Additional controls pass: eight multipage, eight footprint, thirteen
capture-handoff, and twelve registration-context tests. The broader context
groups also pass 22 and 20 tests per link. The twelve context tests include two
new negative controls for the bank guard described below. Do not confuse these
with the separate historical 187-test compatibility group: its six failures,
sixteen errors and 103 skips have identical baseline/candidate identities.

Native catch-tail tests cover 104 principal and eight follow-up-capture cases,
including EXP, accepted/declined learning, naming, evolution/cancellation,
party/PC delivery, repeat/no-Dex branches, and subsequent battle/overworld return.
The independent 104-case delivery proof preserves each native encounter's DVs
and stats. Eight actual Pay Day controls preserve real earnings, Amulet Coin
and the wallet cap. No false capture payout recurred. Special callers cover
both Game Corners, Transform and declared contest/Celebi contexts; these are
not claims of running every contest/event script. All-species registration
uses declared species contexts derived from native capture, not 373 wild catches.

### Measured Changes

Frame units are physical 70,224-tick displays at 4,194,304 Hz. Deltas below are
prototype minus accepted baseline, except the explicitly separate within-ROM
comparison afterward. Loading/saving numbers are native game time, not host
test duration.

| Measurement | Paired Delta |
| --- | --- |
| Every direct battle-animation call | **0 ms / 0 frames** |
| Dex entry median | **0 ms / 0 frames**; both 444.695 ms / 26.561 frames |
| Dex exit median | **0 ms / 0 frames**; both 711.637 ms / 42.504 frames |
| Valid load, small/full legacy migration, recovery | **0 ms / 0 frames** |
| Normal save | -0.0296 ms / -0.00177 frames |
| Selected opening, 512 matched pairs | Median 0 ms / 0 frames; maximum **+16.743 ms / 1 frame** |
| Active Info diagnostic, 96 matched probes | Median 0; range -17.990 to +33.485 ms / -1.074 to +2 frames |
| Settled Info diagnostic, 96 matched probes | Median 0; maximum +0.3233 ms / +0.01931 frames |

The one-frame Selected opening cost occurs in some Weavile, Garchomp, Rayquaza
and Metagross cases after replacing their short placeholder descriptions. There
are 116 complete-visible penalties of at least half a frame among the 512 pairs,
all in these four species. No missing displayed completion or playback deadline
failure accompanied the delay. These are full-content workflow comparisons,
not a text-identical isolated code benchmark.

Within the prototype, seven catalog operations exceed the unchanged two-frame
registration-versus-Selected warning threshold: Diglett, Igglybuff, Koffing,
Kyogre, Mareep, Metang and Parasect. Their displayed deltas are 33.618-34.597 ms /
2.008-2.066 frames. The twenty representative species have a much smaller
median difference of 0.1607 ms / 0.00960 frames across 354 operations.

192 fresh diagnostic cases per link replay those identities plus historical
controls at four input phases, with active and finished playback. Actual slower
baseline comparisons include Igglybuff's first Info (+33.485 ms / 2 frames),
Kyogre's Desc-to-Info (up to +33.368 ms / 1.993 frames), and Metang/Dusknoir
Info requests (+16.743 ms / 1 frame). Other phases improve, including Beldum and
ordinary Selected Kyogre/Metang. With playback finished, the largest increase
is only 0.3233 ms / 0.01931 frames.

The traces identify late foreground admission followed by late VBlank
publication admission, not repeated content generation or audio starvation.
For example, Igglybuff still plans six Stats rows with the same 21,084 physical
ticks of observed planner work; the active producer needs five service visits
instead of three because admission waits consume two display boundaries.
New description work/page counts change preceding request phase. Named-workflow
comparisons do not imply identical absolute animation/key schedules.
These real responsiveness changes are **not fixed or automatically approved**.

![Accepted baseline versus reviewed prototype](../build/dex-species-information-20261016/full-regression/timing-review/igglybuff-info-baseline-v-prototype.mp4)

This two-second real-rate video aligns near the Info signal. Its labels measure
accepted request to complete displayed panel, not physical button signal to
display. It is silent; separate unmodified native WAVs and full frame captures
are retained under `full-regression/timing-review/`. Screenshots were inspected;
human listening and responsiveness approval are separate from automated checks.

### Raw Input Exception

The only raw registration-stress failure is Houndoom, `rapid-info`, phase
52,668 ticks. After selecting Info, sixteen A pulses alternate one physical
frame down and one up: 16.743 ms / 1 frame each, approximately thirty taps per
second. The raw hardware polls never observe A, so no Info request is accepted;
the screen correctly remains on Description while the old test awaits Info.
Portrait playback finishes without an underrun or corrupt page.

A fresh accepted-baseline replay with the ordinary observer has the identical
failure. An additional 16-case two-link probe matrix shows matching failed
identities at this phase and a nearby -512-tick offset, while surrounding offsets
capture the short pulses. Both links capture all sixteen two-frame-on/two-frame-off
presses. A separate in-session replay reproduces the missed train, then opens
Info with a two-frame press and returns with B, preserving context and playback.
This is a newly exposed **baseline polling limitation**, not a new page-job hang.
It remains a raw failure, not a rewritten passing test or an increased tolerance.
Evidence: `input-probes/`, `input-recovery/`, and
`input-baseline-original-observer/` under the full campaign.

Other baseline exceptions remain unchanged: the 34 native move pairs comprise
nineteen condition-specific non-invocations, thirteen ending/switch/menu paths,
and two Sand Tomb hangs after animation return. Sand Tomb remains logged as
`BATTLE-MOVE-02`; it was not fixed here. Known sampled-cry timing misses and the
historical host compatibility failures were not reclassified as clean passes.

### Test Corrections

Three test-only assumptions were corrected without changing the reviewed ROM:

- Coverage/committed-exit totals now sum actual Description page counts. New
  three/four-page and legacy-default controls prevent a two-page tally returning.
- The contest test checked Park Ball consumption at the start of continuation,
  before the decrement. Baseline and candidate both failed there. The corrected
  check requires exact consumption after native overworld return; both B/End
  paths pass, including a same-fixture candidate replay. Original logs remain.
- A whole-bank interrupt guard saw five relocated farcall operands in normal
  Dex setup functions. The guard now validates precisely those five named
  mainline caller/callee instructions, then compares the entire remaining bank.
  ROM0 interrupt/delay spans and actual handlers remain byte-identical. The new
  controls reject both a modified interrupt opcode and a wrong call operand.
  This is not permission to add interrupt work or broadly ignore relocated bytes.

Receipts are in `orchestration/contest-test-repair.json` and
`orchestration/interrupt-bank-test-repair.json`; original failed reports and
original harness files are retained. The final harness snapshot is
`orchestration/harness-final/manifest.json`. The full private orchestration
script is `build/dex-species-information-20261016/full_regression.py`.

No runtime fix, prototype rebuild, production promotion or main-save edit was
performed in this follow-up. The earlier Dex-only `qualification.json` remains
its original scoped record; the separate full-campaign qualification is the new
result. No physical hardware or Battle Tower validation is claimed. Pending
Desc B/End and Info-End cancellation could complete before the observed leave
boundary; the reports keep those unobserved live-work combinations explicit.

## Review Evidence

![Accepted base and candidate](../build/dex-species-information-20261016/review/before-after.png)

[All representative Description pages](../build/dex-species-information-20261016/review/description-pages.png)
shows Treecko, Aggron, Mismagius, Honchkrow, Cradily and Claydol. Every tested
Modern/Legacy page also has its native image under `multipage/`.

Short real-time recordings with audio:

- `review/treecko-selected.mp4`: ordinary Selected, including the four-page loop.
- `review/aggron-registration.mp4`: registration Desc/Info/Mov navigation.
- Lossless WAVs and frame captures for six species in both screens remain under
  `review/captures/runs/`. The two review videos omit the first two post-load
  frames, which can contain host framebuffer state not restored by checkpoints.

Screenshots were visually inspected. Pixel/content, playback-deadline and
cry-signature checks are automated; user listening approval and real-hardware
testing are not claimed.

## Harness and Retention

The Description oracle and registration catalog now enumerate actual pages,
and badge-buffer test selection is independent of page ordinal. Independent
source/count/offset checks prevent the runtime and oracle from silently agreeing
on a missing P.3/P.4. Runtime budgets and playback assertions are unchanged;
the full follow-up's narrowly scoped harness corrections are documented above.
The standard numeric-copy host adapter uses the same frozen pre-relocation
reference as footprint qualification, preserving the +672-cycle check.

Initial development links required moving the text sections out of the old
pinned bank and exporting page labels. These were resolved before native
qualification. An orchestration indentation error caused a post-test NameError
after complete successful screen/Area runs; the corrected driver rechecked
the same exact-link reports and returned zero. No game assertion was weakened
and no native failure was reclassified as a pass. Details are retained in
`development-notes.json`.

`source-overlay.tar.gz` contains the changed game-source files relative to the
accepted footprint candidate, not relative to current production. Preserve that
base or use the complete candidate directory. This is not an instruction to
apply the overlay or promote any source now.

Reusable entry points:

```sh
python3 -B -m tools.dex_timing.species_information prepare --output build/FRESH
# Apply the reviewed renderer/layout source overlay to that private candidate.
python3 -B -m tools.dex_timing.species_information build --output build/FRESH
python3 -B -m tools.dex_timing.species_information regression-prepare --output build/FRESH
python3 -B -m tools.dex_timing.type_full_regression setup --output build/FRESH/regression
python3 -B -m tools.dex_timing.type_full_regression dex --output build/FRESH/regression
python3 -B -m tools.dex_timing.type_full_regression moves --output build/FRESH/regression
python3 -B -m tools.dex_timing.species_information pages --output build/FRESH
python3 -B -m tools.dex_timing.species_information host --output build/FRESH
```

The initial prepare uses the pinned assessment/source cache and accepted
footprint base, so retain those dependencies. Registration, stress, media and
baseline commands/configs are separate artifacts in this run; the final
qualifier requires their complete results. Do not call it against only the
eight commands above or describe those commands as a full-game campaign.
