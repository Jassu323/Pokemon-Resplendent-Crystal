# Selected Dex Delay Optimization Scope

Date: 2026-10-17. Scoping only. The reviewed species-information prototype,
production ROM and player's main save remain unchanged. All diagnostic ROMs,
private saves, captures and generated reports are under
`build/dex-delay-scope-20261017/`.

## Recommendation

The best small next candidate combines a specialized hidden-page printer with
a corrected foreground READY admission bound: **59 additional ROMX bytes and
zero additional ROM0, WRAM0, WRAMX, HRAM or SRAM bytes**. No interrupt code,
audio guard, portrait priority or VBlank publication window changes.

The direct benefits are genuine, but this is not a promise that every later
button press becomes faster. Earlier completion changes which part of the
authored portrait playback later requests encounter. Some later rapid-sequence
operations become slower even though others become faster. The maximum Info
and Mov latency across the catalog is unchanged. These remain diagnostic
alternatives, not a promoted or full-game-qualified prototype.

All measured deltas below compare against the **reviewed species-information
prototype**, not directly against production with its shorter placeholder text.
One physical display frame is 16.742706 ms, or 70,224 ticks at 4,194,304 Hz.
Means are over the declared scripted cases, not estimates of player frequency.

## Measured Options

| Option | Added ROMX bytes | Added WRAMX bytes | Direct displayed improvement | Complexity and risk |
| --- | ---: | ---: | --- | --- |
| Hidden Description printer | 59 | 0 | Selected opening: 0-16.743 ms / 0-1 frame | Low code complexity; low/moderate compatibility and timing risk |
| Correct READY admission bound | 0 | 0 | First Info: 0-33.485 ms / 0-2 frames | One data-byte change; moderate proof/maintenance responsibility |
| Both | 59 | 0 | Retains the opening gain and first-Info gain | Low/moderate integration complexity; same timing qualifications |

All three add zero ROM0, WRAM0, HRAM and SRAM bytes. RAM symbols retain their
addresses. The combined link's ROM SHA-256 is
`754b60aa90b3fdcb45c598bfe3d3f934ed338c3adf57110e644988101155d237`.

### Hidden Description Printer

Cold/staged Description construction currently uses the general game text
printer. Each ordinary character passes through its command dictionary and
letter-delay checks even though this panel is hidden and is printed instantly.

The diagnostic adds a small printer for the two later-species entry banks.
It handles ordinary encoded glyphs, row changes and terminators. Unexpected
control bytes restart the page through the existing general printer. Original
species retain the general path. This does not change the bounded live
Description-page renderer, animation startup runway or description contents.

In 256 matched openings covering sixteen species, Modern and Legacy, immediate
and long hover, and four fractional-frame input phases:

- 48 openings improve by exactly **16.743 ms / 1 frame**; none become slower.
- The mean gain is **3.139 ms / 0.1875 frames**; the median is zero.
- Gains occur in Weavile, Garchomp, Rayquaza and some Legacy Metagross cases.
- It does not recover a displayed frame in every previously slower case.

One Weavile example changes from **132.642 ms / 7.922 frames** to
**115.900 ms / 6.922 frames**. Reusing existing glyphs and text avoids adding
any pre-rendered page copies, graphics assets or text cache.

### Correct READY Admission Bound

`PokedexPerf_InfoLatestLY` currently requires `LY < 84` for READY. The
diagnostic changes that single table byte to **`LY < 108`**, the existing
RECORD cutoff. Earlier job states retain their existing bounds.

READY does not generate or upload the Stats/evolution glyphs. It stages the
already-prepared palettes and OAM and queues the atomic lower-panel handoff.
The old bound is substantially earlier than this work currently requires.

The isolated full service path, including a healthy sampled-cry cache check,
uses at most **4,188 normal-speed CPU T-cycles** in the tested READY cases.
The existing guard/reserve accounting at LY 108 permits:

`(144 - 108) * 456 - 2048 - 8182 = 6186 T-cycles`.

The measured path therefore fits even at normal speed, with 1,998 T-cycles
remaining beyond the unchanged guard and finishing reserve. At double speed,
4,188 CPU T-cycles occupy **0.499 ms / 0.02982 display frames**. This is an
isolated CPU bound, not a simulation of arbitrary interrupt service; native
Dex playback checks separately verify the current workloads.

The 32 isolated controls also confirm rejection for low sampled-cry cache,
active portrait upload and the late LY boundary. The loop-tick check, portrait
upload exclusion, audio-cache threshold and actual VBlank publication window
(`144 <= LY < 147`) remain intact. Normal-speed READY admission changes too;
normal speed is covered by the isolated bound, while native Dex owners here
run at the existing production double speed.

**Maintenance dependency:** any future change to READY staging, its palette
copy, OAM copy, banking, admission checks or service overhead must remeasure
the complete path against the 6,186 T-cycle allowance. Preserve the 2,048
guard and 8,182 finishing reserve. Do not reuse the later cutoff for heavier
job states or widen the interrupt publication window on this evidence.
An implementation should put that warning and a permanent cost assertion next
to the table; neither was added to the reviewed prototype during scoping.

Across all 373 species in ordinary Selected and registration, there are 746
first Info openings with matching preceding workflows:

- 369 improve by at least half a frame; none become slower.
- The largest gain is **33.485 ms / 2 frames**.
- Mean gain: **9.494 ms / 0.567 frames**. Median gain: zero.
- The combined printer/bound option improves 368 first openings, with no slower
  first opening and a mean gain of **9.471 ms / 0.566 frames**.

For the recorded Koffing registration example, first Info changes from
**98.596 ms / 5.889 frames** to **65.111 ms / 3.889 frames**.

## Whole Dex Timing Tradeoffs

Each of the four controlled ROM links completes **14,382 page/tab operations**
across 373 ordinary Selected screens and 373 registration screens. All finish
without semantic, pixel-parity or authored-playback failures. Cry-content
signatures match the unchanged control for every one of the 746 species/owner
cases in each diagnostic, including synthesized and sampled cries.

For the table-only option, all 3,732 Info operations together have a mean gain
of **3.546 ms / 0.212 frames**: 805 improve by more than half a frame and 98
worsen by more than half a frame. Median change remains zero. Later Info
requests can worsen by **32.969 ms / 1.969 frames** in the scripted sequence.
Thus the first-Info result must not be generalized to every subsequent page.

Later Mov requests also encounter different playback phases. The table-only
option's largest matched increase is Toxicroak's Selected Mov wrap:
**267.030 -> 333.390 ms**, or **+66.360 ms / +3.963 frames**. Its mean Mov
change is much smaller: **+0.150 ms / +0.009 frames** across 7,422 operations.

The printer alone moves a larger existing wait between Tangrowth's Mov pages:
the second page improves **133.942 ms / 8 frames**, while the third worsens
**134.161 ms / 8.013 frames**. The combined option retains that redistribution.
This is a real per-button timing tradeoff, not a new eight-frame text-rendering
cost or an audio/animation underrun.

Two controls distinguish phase redistribution from new work:

- The table-only ROM differs from the reviewed ROM in exactly its READY table
  byte and a checksum byte; all symbol addresses and executable bytes match.
- Direct Desc-to-Mov tests without prior Info work cover all 373 species, both
  owners and four input phases: **2,984 matched pairs**, all **0 ms / 0 frames**
  different. The later Mov differences require changed preceding history.

Across the entire catalog, the maximum Info latency remains
**116.394 ms / 6.952 frames**, and maximum Mov latency remains
**333.828 ms / 19.939 frames**, for every measured alternative. Unchanged
category maxima do not make individual slower requests disappear.

The targeted diagnostic matrix adds 192 probes per link: twelve Info targets,
two owners, four phases, with active and completed playback. The table-only
option's active matrix has 33 frame-scale improvements and four worsening
cases; the settled matrix has no half-frame differences. Detailed paired
numbers remain in `audit.json` and each option's `comparison.json`.

## Larger Alternatives Not Built Here

The following are engineering estimates, not linked costs or measured gains.
All can remain outside ROM0/interrupt handling.

| Approach | Estimated additional ROMX bytes | Estimated additional WRAMX bytes | Expected benefit | Complexity and risk |
| --- | ---: | ---: | --- | --- |
| Recognize an already-resident Stats atlas | 200-400 | 2-8 | Roughly 16.743-33.485 ms / 1-2 frames on eligible repeat visits; no first-Info benefit | Moderate; correct invalidation across Mov, Area, species and Listing ownership is essential |
| Prepare first Stats in the background using shared workspace | 350-900 | 2-8 | Potentially 33.485-66.971 ms / 2-4 frames when preparation finishes before A; little/no gain on immediate A | High ownership/cancellation complexity; conflicts with Description work must be explicit |
| Background preparation with a separate lower-panel snapshot | 400-1000 | About 512 | Similar conditional first-Info benefit, with clearer map ownership | Moderate/high; exceeds the earlier 100-byte WRAM target and still needs invalidation/cancellation work |

The approximate 512-byte snapshot covers padded tile/attribute rows, OAM,
palettes and control metadata, not duplicate font graphics. WRAM bank 3 is
already full, so added storage needs another bank or a separately audited
reuse. Small-tag estimates also need placement review.

These caches reduce actual repeated/pre-input work, but they do not guarantee
identical later animation phases. They should not be justified as a small
fix for only the current one/two-frame cases. Background preparation must never
delay reveal, take priority over portrait/audio work, publish speculatively,
or expose unseen species data.

Earlier call-grouping experiments are not attractive alternatives: they changed
which deadlines requests met and introduced larger later-page delays. See
`pokedex_registration_local_scheduling_scope.md`. Increasing general slice
budgets, changing shared IRQ order, weakening audio-cache checks, interrupting
portraits, or allowing late lower-panel VBlank publication is not recommended.

## Qualification Scope and Evidence

The combined diagnostic additionally passes the standard **4,479-case Pokemon
Dex suite**, **136 Unown cases / 2,212 form selections**, and the Moves Dex
filter/UI/visual/navigation/transition/polish/cursor checks. Type Matchups is
checked separately across all six CGB models, including selection and return
paths. Battle helpers are explicitly skipped in that campaign.

The table-only and combined diagnostics each pass eleven context/RAM/strict
interrupt-isolation contracts and 230 native registration B/End exit replays,
including pending and committed pages for four species. Broader battle,
persistence, general gameplay and Battle Tower suites are not run for this
scope. No physical-hardware or human listening approval is implied.

Final controlled fixtures declare power-on RNG seed `0x17102026` and fixed
host time `1792195200`. Each ROM is freshly booted; no save state is moved
between links. Native pre-registration summaries match in all four links.
Both RNG and RTC import need control: fixing RAM randomization alone did not
make native histories identical.

Exploratory output is retained but excluded from controlled timing conclusions.
It includes missing-reference/order setup errors and eight registration visual
flags in a table-only run with a different native donor history, before Info
was requested. No rendering workaround was applied. Those flags do not recur
in the final matching-startup all-species run; their original trigger was not
independently isolated as a gameplay bug or certified fixed. Further startup
variation testing belongs in release qualification, not a claim of universal
correctness from a single controlled seed.

The retained record is `build/dex-delay-scope-20261017/audit.json`, with linked
maps/resource deltas, native traces and per-operation comparisons. The reviewed
ROM stays SHA-256
`905f6eab5bd17eaacf5623200eed20c9dd972efa6a65f1b01efc10cc8ad2ddb4`.

![Reviewed prototype versus table-only diagnostic](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-delay-scope-20261017/media/ready-bound/koffing-info-comparison.mp4)

The real-rate video aligns before the same Info input. Separate full native
recordings are retained for manual listening:

- [Reviewed prototype audio](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-delay-scope-20261017/baseline/qualification-controlled/review-captures/koffing/view1-page0-registration-continuous-q0/audio.wav)
- [Table-only diagnostic audio](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-delay-scope-20261017/ready-bound/qualification-controlled/review-captures/koffing/view1-page0-registration-continuous-q0/audio.wav)

The still `media/ready-bound/earlier-info.png` shows the earlier Stats handoff.
Captures were visually inspected; the faster panel retains the same finished
layout, and the portrait remains on its authored timeline.
