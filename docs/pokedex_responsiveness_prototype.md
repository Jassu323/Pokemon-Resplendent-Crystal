# Selected Dex Responsiveness Prototype

Date: 2026-10-17. Implementation and the full regression **excluding
Battle Tower** are complete, manually accepted and production-integrated.
The final prototype audit identifies **zero new correctness failures** relative
to the previous reviewed prototype. This is not an all-raw-tests-clean claim:
known battle/audio fixtures and historical host-test exceptions remain identical.
Production ROM/symbols/map now match the reviewed build exactly. The player's
main save is unchanged. See [Production Integration](#production-integration)
for promotion evidence; earlier protected production hashes belong to the
pre-promotion qualification.

## Review Files

- Main ROM: `build/dex-responsive-prototype-20261017/pokecrystal-dex-responsive.gbc`.
- Matching private save: `build/dex-responsive-prototype-20261017/pokecrystal-dex-responsive.sav`.
- Optional catch-test pair: `pokecrystal-dex-responsive-capture.gbc` and `.sav`
  in the same directory. This is the same ROM, paired with a different battery.
- Full source: `build/dex-responsive-prototype-20261017/candidate/`.
- Frozen previous source: `build/dex-species-information-20261016/candidate/`;
  a separate `rollback-source.tar` is retained under the new build directory.

The main review save has all 373 species seen/caught and all 26 Unown forms
unlocked. It contains 99 Master Balls in the Balls pocket. Other progression,
party data and existing move-discovery flags are retained from the private
review battery; this is not a modification of the player's main save.

The optional catch save instead leaves Caterpie, Pidgey and Sentret seen but
uncaught. Their next capture triggers interactive registration. It also has
99 Master Balls. Both standard save records/checksums and the private move-save
binding were updated. The main pair was booted from its actual delivered
battery and navigated normally through seven species without checkpoint loads
or runtime memory injection; every page, playback and B-return check passed.

## Implementation

This adds the two approved local adjustments to the reviewed
species-information prototype, retaining its footprints, full descriptions,
measurements and direct Description page offsets:

1. `PokedexMoves_Service` recognizes late VBlank as useful preparation time
   before the scanline clock wraps. It attempts up to twelve existing bounded
   slices instead of three, rechecking its clock/playback admission before each
   slice. Visible scanlines 64-143 remain excluded during active playback.
2. Info's READY staging cutoff changes from LY 84 to 108. No other Info-state
   cutoff, VBlank publication window or portrait/audio deadline is widened.

Only `engine/pokedex/pokedex_moves.asm` and
`engine/pokedex/performance_admission.asm` change in the private game source.
Portrait servicing stays first. Panel publication remains atomic. There is no
new artwork, generated display table, cache, buffer, speed switch or save format.
This changes the Selected Pokemon Mov tab and interactive registration, not
the separate Moves Dex mode.

| Memory Class | Decimal Byte Change Versus Previous Prototype |
| --- | ---: |
| ROMX | +4 |
| ROM0 | 0 |
| WRAM0 | 0 |
| WRAMX | 0 |
| HRAM | 0 |
| SRAM | 0 |

Existing RAM symbols retain their addresses. The ROM remains 4 MiB.

The READY dependency is documented beside its table: at LY 108, the unchanged
2,048-T guard and 8,182-T finishing reserve leave 6,186 normal-speed CPU
T-cycles. The expanded 36-state test observes at most 4,216 T-cycles, leaving
1,970 T-cycles beyond the existing guard/reserve (the original narrower scope
observed 4,188). Re-measure
after changing palette/OAM staging, bank calls, copying or service overhead;
this is not permission to widen heavy producer states or interrupt gates.

## Timings

All before/after figures here compare the **previous reviewed prototype** with
the updated prototype, not production's older description content. One physical
display frame is 16.742706 ms. Latency is accepted request to the first complete
displayed panel, not merely time spent executing its renderer.

The controlled all-373-species comparison from the immediately preceding scope
contains 746 owner sessions and 14,382 operations. The new build is byte-identical
to that scope's combined `moves-ready` link. Those controlled comparisons are
retained evidence, not described as a second fresh benchmark. This turn adds
fresh full-catalog correctness/registration runs, focused timing replays and
native recordings on the final packaged link.
The ordinary Selected timing inventory uses Modern presentation. Legacy
correctness and entry timing are tested separately; this is not a claim to have
measured every possible Legacy tab/input history against the same numbers.

| Controlled Measurement | Previous | Updated |
| --- | ---: | ---: |
| Median of 7,422 Mov requests | 98.776 ms / 5.900 frames | 48.547 ms / 2.900 frames |
| Maximum Mov request | 333.828 ms / 19.939 frames | 81.487 ms / 4.867 frames |
| Median paired Mov improvement | | 50.228 ms / 3 frames |
| Median complete page/tab workflow improvement | | 418.568 ms / 25 frames |

The median/maximum columns summarize each distribution; their endpoints need
not be the same request. The later example table contains matched requests.

All 7,422 Mov requests and all 746 complete scripted workflows finish sooner.
These workflows advance input when pages are ready and do not accelerate
authored portrait playback. First Info improves for 369/746 owner sessions,
by up to 33.485 ms / 2 frames, with no first-Info slowdown; the other 377 are
unchanged. Mean first-Info saving is 9.494 ms / 0.567 frames.

Fresh focused replays cover active/settled playback and four input phases:
128 cases on each link, with no content, pixel or playback failure. Illustrative
continuous-active cases are below; they include the changed preceding workflow,
so they are not isolated fixed-portrait-phase CPU benchmarks.

| Request | Previous ms / Frames | Updated ms / Frames |
| --- | ---: | ---: |
| Tangrowth, Selected Mov P.2 | 266.858 / 15.939 | 32.640 / 1.949 |
| Tangrowth, Selected Mov P.3 | 98.775 / 5.900 | 49.376 / 2.949 |
| Tangrowth, registration Mov P.2 | 82.543 / 4.930 | 32.489 / 1.940 |
| Tangrowth, registration Mov P.3 | 116.328 / 6.948 | 49.185 / 2.938 |
| Toxicroak, Selected Mov wrap | 267.030 / 15.949 | 48.763 / 2.912 |
| Togekiss, Selected Mov P.3 | 317.259 / 18.949 | 65.824 / 3.932 |
| Koffing, registration first Info | 98.596 / 5.889 | 65.111 / 3.889 |
| Eevee, Selected next Info page | 98.122 / 5.861 | 114.867 / 6.861 |

### Remaining Timing Tradeoffs

Not every later button press improves. Earlier completion changes the portrait
phase at subsequent requests. Across the controlled combined workload, the
largest later Description slowdown is 17.682 ms / 1.056 frames and the largest
Info slowdown is 34.290 ms / 2.048 frames. Eevee's one-frame example above is
one such real tradeoff, not additional rendering work. These do not cancel the
complete-workflow gains, but remain manual responsiveness decisions.

The complete inventory is
`build/dex-responsive-prototype-20261017/timing/page-slowdowns.md`.
It lists every one of the 203 measured slowdowns of at least half a display
frame, across 117 species, with owner, one-based page, request context, old/new
latency and delta. Another 1,065 positive changes are smaller than half a frame;
their maximum is 2.282143 ms / 0.136307 frames. All 1,268 positive changes,
including the tiny ones, are retained at full precision in
`timing/all-page-slowdowns.csv`. `timing/all-page-timings.csv` also includes all
3,790 unchanged and 9,324 faster requests. No Mov request is slower, and no
first Info opening is slower in this comparison.

The ten largest delays all affect later Desc-to-Info returns to **Info P.1
(Stats)**, after the initial complete page cycles:

| Pokemon | Owner | Previous ms / Frames | Updated ms / Frames | Added ms / Frames |
| --- | --- | ---: | ---: | ---: |
| Toxicroak | Selected | 65.071 / 3.887 | 99.361 / 5.935 | 34.290 / 2.048 |
| Milotic | Selected | 65.992 / 3.942 | 99.651 / 5.952 | 33.659 / 2.010 |
| Teddiursa | Selected | 65.288 / 3.899 | 98.846 / 5.904 | 33.558 / 2.004 |
| Armaldo | Registration | 65.533 / 3.914 | 99.018 / 5.914 | 33.485 / 2.000 |
| Umbreon | Registration | 65.670 / 3.922 | 98.611 / 5.890 | 32.941 / 1.968 |
| Ekans | Registration | 65.670 / 3.922 | 98.069 / 5.857 | 32.398 / 1.935 |
| Arbok | Selected | 65.361 / 3.904 | 97.663 / 5.833 | 32.302 / 1.929 |
| Armaldo | Selected | 65.400 / 3.906 | 97.578 / 5.828 | 32.177 / 1.922 |
| Geodude | Registration | 65.670 / 3.922 | 97.823 / 5.843 | 32.153 / 1.920 |
| Umbreon | Selected | 65.480 / 3.911 | 97.472 / 5.822 | 31.992 / 1.911 |

The complete inventory also identifies every slower initial Info P.2/P.3 or
wrap request, and every slower Description P.1 return. Those should not be
mistaken for uniformly faster page sequences. The timing values depend on the
declared continuous input history and active portrait phase, not species alone.

The fresh registration-versus-ordinary-Selected table also flags five
phase-sensitive requests: Armaldo's later Desc-to-Info, Blissey's first Info,
Cyndaquil's next Info page, Stantler's first Info and Togekiss's Info wrap.
These are comparisons between two owners of the updated build, not five new
before/after regressions. Their detailed active/settled, four-phase replay
campaign has 160 cases and no correctness failure. The final report retains
the original scan deltas separately from these diagnostic replays.

## Tradeoff Attribution And Production Comparison

Follow-up analysis on 2026-10-17 does not change either prototype or production.
The seven highlighted focused timing cases were not the complete set of
affected species. The complete previous-versus-current inventory covers 117
species with at least one slower request of more than half a display frame.
This is a union across the tested Modern Selected and registration owners,
not a claim that each request for those species is always slower.

### Which Change Causes Which Wait

The retained four-way controls compare the previous prototype, Mov-only,
Info READY-only, and both changes. All 2,240 initial Info requests occur before
the first Mov visit. Mov-only is exactly identical in measured latency
to the previous prototype for these requests; the combined build matches
Info READY-only. Consequently, slower initial Info P.2/P.3/wrap requests are
attributable to READY's changed completion/input phase, not Mov batching.

After visiting Mov, either optimization can change the active portrait phase
at subsequent requests, including interactions between them. Description's
renderer itself is unchanged by these two optimizations. Keeping Mov-only
does not preserve later Info/Description timing: Toxicroak's later Selected
Desc-to-Info return is 34.580 ms / 2.065 frames slower with Mov-only, versus
34.290 ms / 2.048 frames slower with both. Conversely, Eevee's next Selected
Info page is unchanged with Mov-only but 16.746 ms / 1.000 frames slower with
both. Tangrowth's later registration Desc-to-Info return is 0.626 ms / 0.037
frames faster with Mov-only but 16.743 ms / 1.000 frames slower with both.

These are phase-sensitive admission waits, not added Description rendering
work or longer authored portrait playback. Earlier completion shifts when
the next ready-paced input reaches the unchanged portrait-priority rules.
They are real request-latency tradeoffs, even when the total visit is faster.

| Versus Previous Reviewed Prototype | Mov Only | Mov And Info READY |
| --- | ---: | ---: |
| Species with any frame-scale slower request | 106 / 373 | 117 / 373 |
| Slower requests | 168 / 14,382 | 203 / 14,382 |
| Species with slower Description requests | 12 | 13 |
| Species with slower Info requests | 98 | 106 |
| Species with slower Mov requests | 0 | 0 |
| Species with a slower initial Info page | 0 | 46 |
| Species with faster first Info | 0 | 220 |
| Largest slower request | 34.580 ms / 2.065 frames | 34.290 ms / 2.048 frames |
| Median full-workflow saving | 401.825 ms / 24 frames | 418.568 ms / 25 frames |

All 7,422 Mov requests and all 746 complete workflows are faster with either
variant. READY makes 369 first-Info owner requests faster, with none slower.
Although 75 later initial-Info requests across 46 species are slower, the
elapsed initial Info sequence is faster in 450 owner sessions and unchanged
in 296: no whole initial Info sequence is slower. Its median saving is
16.743 ms / 1 frame and its maximum saving is 66.971 ms / 4 frames.

Adding READY to Mov-only makes 493 complete workflows faster and leaves 253
unchanged; none is slower. The median additional saving is 16.743 ms / 1 frame.
The slower-species sets are not nested: 47 species with a Mov-only slowdown
have none with both, while 58 become newly affected. Choosing Mov-only avoids
some highlighted waits, but is not a no-tradeoff alternative.

### Fresh Production Sweep

A fresh timing-only sweep uses the exact protected production ROM, not the
artwork-only footprint baseline. It covers all 373 species in both owners:
746 sessions / 14,138 requests, with zero semantic, portrait-playback or
owner-parity failures. Each ROM has independently generated checkpoints.
Startup RNG seed `0x17102026` and fixed host time `1792195200` match the retained
prototype controls. All 746 cry-content signatures match each prototype.

The newer descriptions add 244 P.3/P.4 requests across the two owners; those
requests have no production counterpart and are excluded from the shared-page
table. Each build still uses its own real description content and advances
when ready. Thus later input histories differ in page count and portrait
phase. This measures actual complete browsing, not isolated same-phase CPU
cost or every possible input timing. It does not retest Selected entry latency.

| Species With At Least One Slower Shared Request Versus Production | Previous | Mov Only | Both |
| --- | ---: | ---: | ---: |
| Any page, union of owners | 75 | 135 | 139 |
| Description | 22 | 32 | 34 |
| Info | 58 | 124 | 120 |
| Mov | 37 | 0 | 0 |
| First Info | 18 | 18 | 9 |
| Slower shared requests | 230 / 14,138 | 289 / 14,138 | 283 / 14,138 |

The current build therefore broadens the set with an individual slower
Info/Description request; it does not reduce that set to seven species.
Nevertheless, every shared Mov request is faster than production, and the
sum of shared-request latency is lower for all 373 species in both owners.
Its paired median saving is 570.968 ms / 34.102 frames; this sum is not the
elapsed time of an entire visit because it excludes inputs and setup waits.

For the actual full visit-every-page workflow, 93 species have a longer visit
in the previous prototype than production, versus 47 with Mov-only and 34
with both. The remaining 34 all have extra Description pages absent from
production, so this is not an equal-content comparison. The current median
full-workflow saving versus production is 418.568 ms / 25 frames; the longest
remaining positive delta is 133.942 ms / 8 frames. Every current full workflow
is faster than the previous prototype with the same content.

The nine remaining first-Info species slower than production in this
continuous history are Marshtomp, Breloom, Numel, Seviper, Solrock, Walrein,
Salamence, Bronzong and Garchomp. Owner details are in the CSV. Their largest
penalty is Garchomp's 33.617 ms / 2.008 frames, already present in the previous
prototype. Prior entry-timing evidence is separate: the four highlighted
one-frame Selected-opening penalties in the 64-species phased entry sample
remain unchanged by these optimizations; that is not an all-373 entry count.

Reproducible evidence is under `build/dex-responsive-tradeoffs-20261017/`:
`compare.py`, `summary.json`, the fresh `production/` catalog and observer,
`four-way-attribution.csv`, `species-tradeoffs.csv`, and the per-comparison
request/workflow CSVs. A slower count here means more than 0.5 frames
(8.371353 ms), separating frame-scale waits from small timing shifts. ROM,
save and production hashes remain protected; no additional full regression
or game-source change is part of this analysis.

## Manual Review

1. **Tangrowth:** open Mov during its animated/sampled introduction, cycle
   P.1 -> P.2 -> P.3 -> P.1, then return through Info and Desc. Both later Mov
   pages should be faster, without corrupt text, an interrupted portrait or
   audible sample discontinuity. Footprint artwork is unchanged from the
   reviewed prototype.
   In registration, its **later Desc -> Info P.1 (Stats)** return is one frame
   slower: 65.533 ms / 3.914 frames -> 82.275 ms / 4.914 frames, a difference
   of 16.743 ms / 1 frame. That is separate from the faster Mov P.2/P.3 requests.
2. **Toxicroak and Togekiss:** check Mov wrap and P.3 respectively while the
   portrait is still playing. Also try their later Info returns; these exercise
   phase differences after faster preparation.
3. **Koffing, Eevee and Dusknoir:** compare first Info, Eevee's complete five-page
   Info/evolution sequence, and Dusknoir's sampled introduction and ancestor page. A
   single later Eevee page can take one extra frame even though the full
   sequence is faster overall.
4. **Clefairy or Mew:** page through the long Mov lists, including two-digit
   page badges and wrap. They have 13 and 15 Mov pages respectively.
5. **Treecko and Metagross:** cycle all four Description pages, return from Area
   on a later page, then move through Info/Mov and back to Desc. Existing page
   preservation/reset conventions should remain unchanged.
6. Use the optional catch pair to catch Caterpie, Pidgey or Sentret. Review
   registration tabs, B/End exit, naming and overworld/battle return. The save
   has enough Master Balls to repeat without changing the main save.

Automated semantic/pixel/playback checks do not constitute human listening or
responsiveness approval. No real Game Boy hardware was tested.

## Recordings

Both videos use unretimed native frames at the physical display rate. Inputs
advance independently after each page is ready, rather than forcing identical
wall-clock times after the workflows have diverged. The first-Info video is
aligned to its matched final input. Videos are silent; native WAV files are
separate so neither side is mixed over the other.

- Tangrowth Mov comparison:
  `build/dex-responsive-prototype-20261017/timing/media/moves-ready/tangrowth-mov-comparison.mp4`.
- First Info comparison:
  `build/dex-responsive-prototype-20261017/timing/info-comparison/koffing-info-comparison.mp4`.
- Previous/updated Tangrowth native audio: the `audio.wav` files under
  `timing/baseline/review-captures/tangrowth/view2-page2-selected-continuous-q0/`
  and `timing/moves-ready/review-captures/tangrowth/view2-page2-selected-continuous-q0/`.
- Previous/updated Koffing audio: `audio.wav` under the corresponding
  `timing/info-comparison/{baseline,moves-ready}/koffing/view1-page0-registration-continuous-q0/`.
- Manifests, complete scanout frames and native traces are retained beside them.

## Full Regression

Fresh evidence lives under `build/dex-responsive-prototype-20261017/full-regression/`.
`qualification.json` verifies completion and acceptance of all 37 orchestrated
actions, the separately owned exhaustive registration and extended Description
campaigns, exact ROM identities, deliverable hashes and protected inputs.
`runtime-regression/full-regression.json` also reports `merge_ready: true` with
no issues. That is an automated qualification, not production promotion or
human responsiveness approval. Battle Tower is explicitly excluded; no Tower
campaign directory was created.

Some inherited campaign filenames use the labels `production`/`integrated` or
`baseline`/`acquisition`. In this run they mean the frozen reviewed
species-information prototype and the updated candidate, identified by the
hashes below. Root production is separately protected, not silently substituted
for the comparison baseline.

Counts overlap and must not be summed into one end-to-end total.

| Coverage | Result |
| --- | --- |
| Standard Pokemon Dex | 4,479 cases pass |
| Moves Dex/search/sort | All 11 UI/helper/save phases pass |
| Unown | 136 cases, 2,212 form selections and six-model performance/return checks pass |
| Type Matchups | All selections/navigation, six display models, return paths and 122-song idle/held-navigation audio stresses pass |
| Shared arrow cursors | 52 locations, 3,328 idle frames and 1,792 helper/bank contracts pass |
| Selected Info and Mov | 746 cases each, plus 400 input-stress cases pass |
| Full authored Selected playback | 2,238 Modern/Legacy cases pass |
| Description pages | 746 species/presentation cases, 2,482 captured screens pass |
| Later Description/Area return | 732 P.3/P.4 cases pass |
| Active Description return | 1,492 cases pass |
| Six-model Description display | 1,536 cases pass |
| Interactive tabs | 373 Selected + 398 species/form registration runs; 14,682 operations pass |
| Registration stress | All 12,736 cases pass; zero raw failures |
| Registration exits | 17,218 replays; 8,614 unique committed B/End exits; no restoration failures |
| Capture/caller continuation | 104 capture cases, 8 follow-up battle/catch cases, 104 delivered-DV/stat checks pass |
| Pay Day and special rewards | All positive/negative Pay Day, contest and special-gift return cases pass |
| All battle animations | 7,312 renderer calls; exact timing, logical and rendered sequences |
| All moves through normal battle input | 1,332 rows / 666 pairs; same 34 baseline exception identities |
| Historical 100-move matrix | 1,600 rows; no issues or animation-duration changes |
| Sampled audio | 960 rows / 480 pairs; all waveform signatures match; same 32 known timing misses per link |
| Menus and custom inventories | 1,792 input/register contracts, 464 custom cases and 148 popup selections pass |
| Persistence | 2,380 helper, 1,490 cold-boot, 152 interrupted-write and 150 interrupted-repair cases pass |
| Acquisition/learning/battle discovery | Positive/negative sources, failed attempts, migration, called/charge/semantic and Struggle checks pass |
| Bookmarks | Pokemon and Moves helper/UI/owner/sparse/session-reset campaigns pass |
| Lifecycle | 336 main cases, 36 routes and 88 exit-matrix cases pass |
| Linked numeric planning | 3,072 cases pass |
| Standard host | 87 cases on each link, plus eight multipage controls, with no failures/errors/skips |
| Context/isolation | Fourteen cases on each link; expanded READY matrix has 36 combinations per link |
| Actual delivered main save | Fresh Continue, normal navigation and full pages/returns for seven review species pass |

The all-animation timing delta is exactly **0 ms / 0 display frames**. All
1,024 ordinary Selected-entry timing cases also have exactly **0 ms / 0 frames**
delta, including the complete visible panel in both presentations. This local
optimization does not remove the previously discussed entry difference relative
to older production content; its comparison is the previous reviewed prototype.

Normal valid loading, legacy migration, full legacy migration and backup
recovery controls are unchanged at **0 ms / 0 frames**. The save-helper timing
changes from 150.769711 ms / 9.005098 frames to 150.686741 ms / 9.000142 frames:
**-0.082970 ms / -0.004956 frames**, not a display-frame-scale saving. Accepted
and canceled normal-save menu paths both cold-reload successfully. Detailed
menus, custom inventory, PC/daycare, egg, learning, post-battle evolution,
fishing, trainer/phone, purchase and overworld-resume evidence is retained with
the standard gameplay and capture caller campaigns.

### Retained Exceptions And Limits

- The 34 all-move native exception identities are unchanged across all 666
  pairs. The exhaustive renderer still covers every declared animation, both
  sides and phases; native conditional invocation/return limitations are not
  relabeled as clean battle runs.
- Sampled-audio traces retain exactly 32 known timing-miss events per link,
  with matching identities/content. They are not new Selected-tab underruns.
  `sampled-audio-comparison.json` checks all 480 waveform/miss pairs explicitly.
- The historical host group remains 187 cases per link: six failures,
  sixteen errors and 103 skips, with exactly matching identities. These old
  expectations are separate from the current 87-case passing host suite.
- The earlier Houndoom one-frame rapid-Info failure did **not reproduce** in
  the new 12,736-case registration run. This is not a claimed general fix for
  arbitrarily short physical input pulses.
- Supplemental exits prove 107 Info-B cancellations while work is still live
  at leave dispatch. No live Desc/Mov B/End or Info-End cancellation was
  observed there: those jobs can finish before dispatch or during footer
  travel. A pending state before a button signal is not counted as proof of
  pending work at the actual exit boundary. Committed exits, early exits,
  context cleanup and complete returns still pass.
- The user accepted the supplied responsiveness cases and slower timing tails
  on 2026-10-17, including Toxicroak, before requesting promotion. A separate
  per-recording listening sign-off is not recorded; retain the automated audio
  evidence without calling it a listening test. Real-hardware validation is
  not claimed.

One expected host-test mismatch was found and corrected: the all-scanline Info
READY assertion still hard-coded 84 and rejected all 24 newly permitted lines
84-107. The updated test decodes only the supported measured policies (84/108),
checks every scanline, tests clock/portrait/audio guards at the last admitted
line, and retains the independent complete-staging CPU-cost bound. Both links
pass all 87 standard host cases after that test-only correction. The original
failed receipt remains under `host-original-cutoff/`; no ROM changed.

An initial delivered-save review attempt also used the wrong host navigation
assumption for the Modern three-column grid. Its failed log is retained; the
corrected fresh run uses ordinary grid movement and neutral releases. All
seven species pass without altering the ROM or delivered battery.

The context/isolation suite now has fourteen cases, including the actual READY
budget and a negative control for the relocated mainline badge farcall. The
dispatch bank's interrupt opcodes and handler bytes remain strictly compared;
only verified normal-call operands may relocate. Both links pass these tests.

## Build Identity

| Artifact | SHA-256 |
| --- | --- |
| Reviewed prototype and current production | `302099f5836115c776de6606379820fbc661c82824aee438364afd4e7f7834e9` |
| Previous reviewed prototype | `905f6eab5bd17eaacf5623200eed20c9dd972efa6a65f1b01efc10cc8ad2ddb4` |
| Pre-integration production | `d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0` |

The reproducible runner is `build/dex-responsive-prototype-20261017/run.py`.
Its input manifest guards production, the player's main save, both prototype
links and the frozen regression battery after every campaign action.

## Production Integration

The user accepted the reviewed cases and requested promotion on 2026-10-17.
Production source now includes all reviewed footprints, descriptions,
measurements, direct-page offsets and combined scheduling changes. A normal
repository-root build reproduces the qualified ROM, symbols and memory map
byte-for-byte. The current root ROM is `pokecrystal.gbc`, SHA-256
`302099f5836115c776de6606379820fbc661c82824aee438364afd4e7f7834e9`.
No commit or push was made.

The production rollback, complete 256-file promotion manifest and receipts are
under `build/dex-responsive-production-20261017/`. Existing sources and the old
ROM/symbol/map are retained in `rollback/`; files newly added by promotion have
an explicit absent-original marker. Saves at the repository root and the
player's `/Applications/SameBoy/Games/pokecrystal.sav` are hash-verified unchanged.
Unrelated workbook edits were not overwritten or staged.

| Allocation Versus Pre-Integration Production | Decimal Bytes |
| --- | ---: |
| Full description content | +12,767 ROMX |
| Multipage renderer and direct-offset metadata | +466 ROMX |
| Mov/Info scheduling optimization | +4 ROMX |
| Footprint replacement | 0 allocation growth |
| Total | +13,237 ROMX |
| ROM0, WRAM0, WRAMX, HRAM, SRAM | 0 each |

Every existing RAM symbol retains its address. The ROM remains 4 MiB. The
four-byte optimization cost is not the cost of the separately approved full
description content.

Fresh checks against the root build pass:

- 87 standard linked host tests, without failures, errors or skips.
- Eight multipage and eight footprint-conversion/oracle tests, without skips.
- 14 interactive context/isolation tests, including all 36 READY staging
  combinations. The maximum remains 4,216 T-cycles inside its 6,186-T budget.
- All 373 species in ordinary Modern Selected and fixed-species registration:
  746 native sessions / 14,382 tab/page operations. Semantic content, completed
  physical panels, exact owner parity, uninterrupted authored portraits and
  natural cry completion pass. These are fresh matching-link fixtures, not
  checkpoints transported from the private ROM.
- Rebuilt ROM/symbol/map identity, unchanged saves and all existing RAM symbol
  addresses, plus a clean `git diff --check`.

The retained exact-link full regression excludes Battle Tower. Promotion does
not claim a second fresh full battle/gameplay campaign: those qualified bytes
are identical to the reviewed candidate. The root checks above supplement
that complete qualification. Historical battle/audio/host exceptions retain
their documented identities and are not silently marked fixed.

Only source formatting differs from the reviewed source: one terminating
blank line was removed from each of the 122 imported description files. Both
root builds still match the reviewed ROM/symbol/map exactly. The original
native run completed every case successfully, but its already-running final
artifact guard retained the pre-formatting source expectation and rejected
that whitespace cleanup. The failed post-guard log is preserved. A separate
formatting-aware audit revalidates every case/fixture, exact reviewed binaries,
unchanged saves, and only the explicitly recorded one-line source differences;
no game assertion was relaxed and the native cases were not claimed as rerun.

Receipts: `inputs.json`, `verification.json`, `source-formatting.json`,
`root-host.json`, `root-native.json` and `root-native-audit.json`. The local
promotion driver is `integrate.py`. `DEX-DATA-01` is now closed; only deferred
data/order stories, optional profiling/audits and separately tracked adjacent
battle work remain.
