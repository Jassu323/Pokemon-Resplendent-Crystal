# Selected Dex Scheduler Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Current implementation: [living scheduler reference](../../pokedex_animation_scheduler.md)
and [linked validation/emulator test guide](../../dex_scheduler_validation.md).
This record preserves the earlier diagnostic stages and their original ROM identities.

## Latest Status: 2026-09-20

The cohesive scheduler is now implemented and the original ten-species linked
suite and 60 phase controls pass. The expanded live suite exposes a separate
Groudon decoding-horizon failure: its inherited three-event targets hold back
early work during repeated poses. [Groudon's current-link full replay](dex_groudon_target_results.md)
matches the independent core at 861,581 instruction starts and both real misses
exactly. A private later-target control clears them without increasing startup
or work quotas.
The [15-species regression](dex_target_regression_results.md) initially extended
that result to 105 earlier-decoding cases, with all 30 nominal baseline/candidate
runs matching the independent core and the four new states passing both
policies.
The subsequent Spheal/Sealeo/Snorlax unused-tail check passes all 42 additional
baseline/candidate runs. Spheal's extra eight decoding calls leave every
publication and cry-completion timestamp unchanged; Sealeo and Snorlax add no
decoding. Combined candidate coverage is now 126 runs across 18 species, with
36 nominal exact-core matches.

The approved correction is now implemented in `tools/pokemon_animation.c`:
event 1 retains the old startup target; every later event targets the full
dictionary. Rebuilding changes only 2,954 existing target bytes and the global
checksum. Executable code, symbols/map, storage and work limits are unchanged.
The compiled ROM passes the 126-case replay matrix and 18 independent-core
comparisons (11,514,944 instruction starts); the nominal traces exactly match
the private prototypes. See [compiled integration](dex_target_regression_results.md#compiled-integration).
The user subsequently reports passing cold entry/internal paging across the
sampled stress suite and thirteen named synthesized controls, with neither
animation nor audio miss breakpoint firing. Warm-entry testing is deliberately
excluded; its implementation is not removed here. A fresh asset audit found one
distinct untested loop path, Seviper, whose unchanged source resets its repeat
counter indefinitely. That separate source issue and the commit-readiness plan
are recorded in the backlog and validation guide. No runtime cleanup has yet
been performed after this live acceptance.

### Previous Implementation Pre-Flight

The [concrete implementation pre-flight](dex_scheduler_implementation_preflight.md)
now has an isolated assembled cost draft. The specified replacement would add
6 ROM0 bytes and recover 4,960 ROMX bytes net, without adding WRAM, HRAM or VRAM.
It reuses the three schedule-state bytes and removes the obsolete compact
micro-schedule rather than adding another per-species metadata layer. Six checked
tail-call substitutions make room for the outer-loop calls in the full Dex bank.
These are draft byte counts and CPU-only contract checks, not a new integrated
game build or a full timing signoff. The ROM and emulator files remain unchanged.

### Previous Headroom And Synthesized-Cry Step

The [headroom and synthesized-cry follow-up](dex_headroom_synth_results.md)
removes 252 T per gathered tile by unrolling its fixed 16-byte copy, while
retaining all readiness, payload, banking and ownership behavior. Combined with
the existing queue/policy candidate and an 8,192-T minimum finishing reserve,
all 328 final phase/cost continuations pass. Garchomp's 64-phase minimum
finishing margin rises from 556 to 12,120 T; the smallest margin across this
larger matrix is 8,232 T. A 16,384-T nominal negative control fails Garchomp,
showing that rejecting too much early work can itself lose a deadline.

Exeggcute's actual active-synth starting state now matches SameBoy at all 385,586
instruction starts, raising actual-state calibration to 5,993,723 matches.
The candidate preserves its authored 113-interval full timeline, all 114
consecutive sound-engine updates, the 949-write hardware sequence and cry-channel
completion intervals. This is CPU-visible synth-path validation, not a full APU
or all-species audio signoff. Both final 4,096/8,192-T matrices pass (672 runs),
including 72 synth controls; 197 regression tests pass.

Next is the concrete implementation/resource pre-flight, not another runtime
change in this investigation. Actual scheduler guard costs, cold startup and
input/ownership handoffs still need validation; the separate 853-T publication
margin is unchanged. Game ASM, cartridge, symbols, emulator states and SRAM
were not changed. No further user capture is needed before costing this candidate.

### Previous Queue-Copy Step

The [queue-construction follow-up](dex_queue_construction_results.md) measures a
3,216-T saving by unrolling two fixed seven-byte row loops while retaining all
four map copies and their ownership contracts. Queue cost falls 25.5%, from
12,596 to 9,380 T, for a prospective 30-byte ROMX increase and no extra RAM.
The host executes real replacement instructions in a private in-memory image;
the cartridge and game ASM are unchanged.

With this optimization added to the existing candidate, the nine-species phase
and cost matrices pass 144/144 and 108/108, including all previously failing
Garchomp settings. A further high-overhead Garchomp sweep passes all 64 phases.
All 316 candidate runs retain correct intermediate maps/slots, authored timing,
natural cries and safe transfers. The tightest combined admission margin is
556 T, so this is not a universal signoff. Concrete scheduler guard costs,
synthesized-cry coverage and input/ownership handoffs remain gates before a
runtime build. No additional Garchomp capture is currently needed.

### Previous Garchomp Finishing Step

The [Garchomp finishing follow-up](dex_garchomp_finishing_results.md) now uses
the user's additional starting states. Six more actual-input full continuations
match SameBoy at 4,092,809 instruction starts, bringing actual sampled-species
coverage to nine. Exeggcute's synth-start fixture is preserved but not yet replayed
by the sampled-timer-specific constructor.

A costed complete-chain finishing rule replaces the arbitrary eight-tile cap in
the host candidate. All nine nominal starts now complete with correct maps/slots,
authored timing, and natural cries. A stopped cry's still-enabled timer is charged
its measured 104-T short handler, not active playback or zero interrupt cost.
The original Garchomp ten-tile failure and a later real post-cry seven-tile finish
both pass nominally without increasing preload or changing VRAM allocation.

Garchomp still exposes tight admission margins: one of 16 timer-phase controls
and two of 12 overhead-cost settings fail conservatively. The other eight
species pass every setting. These counterexamples remain recorded, not hidden by
timeline stretching or relaxed bounds. Next: gain measured queue/gather or
scheduling headroom, cost the eventual runtime guards, and validate synth/input
handoffs. No runtime fix, ROM rebuild, or resource allocation was made.

### Previous Steady-Publication Step

The [steady-display admission/recovery follow-up](dex_steady_publication_results.md)
now bounds the quiet publication transaction with 853 T of worst-case margin,
including its already-late branch. It holds unchanged viewport registers under
an explicit Selected ownership contract, retains all bookkeeping, and rejects
both late scanlines and LY=0. The three actual-start candidates, 192 phase runs,
and 144 cost runs pass. Fifteen forced-entry controls preserve correct maps and
audio; the twelve deferred cases remain visibly recorded as one interval late.

Broader qualified partial-capture continuations pass for five more species, but
Garchomp retains one failure in its nominal run and every one of 16 phase controls:
event 5/frame 4 has 20/30 tiles uploaded with its dictionary completely decoded.
The inherited extra-eight-tile rule declines the ten-tile remainder. This is the
next complete-chain work-budget case, not grounds to increase preload or claim
the scheduler solved. Initial graphics missing from those partial captures are
explicit canonical-resident assumptions, not newly captured state. No game fix
is implemented or signed off; no new capture is currently needed for this step.

### Previous Publication-Budget Step

The [publication-budget follow-up](dex_publication_budget_results.md) extends
the earlier [host-only policy experiments](dex_scheduler_policy_experiments.md).
Holding already-published empty OAM and expanding the publication window clears
all measured animation/audio failures in the three actual-start candidates and
192 synthetic phase continuations, with correct slot bytes and hardware maps.
The wider window alone overruns the conservative OAM deadline. A 144-case
branch/carry bound also rejects treating the successful cutoff as a universal
rule: its already-late path can exceed VBlank, and its theoretical on-time
margin is too small. These qualifications are preserved alongside successful
phase/cost controls. Next: safely budget admission/recovery and complete-chain
work, then broaden species/ownership coverage before runtime implementation.
No game fix is implemented or signed off; no new capture is currently needed.

The [full-sequence replay record](dex_full_replay_results.md) supersedes the
historical default-model status below. Source-supported boundary corrections
are now in the ordinary linked replay. The subsequent
[Weavile/Dusknoir end-to-end record](dex_end_to_end_capture_results.md) matches all
four user-measured stops exactly. Actual initial fixtures now cover Luxray,
Weavile and Dusknoir. All nine complete animation/cry runs match an independent
SameBoy core at 5,400,595 instruction starts; the other six inputs remain
explicitly qualified partial-capture continuations.

All nine still exhibit animation misses. Dusknoir's actual-state continuation
reproduces the captured sampled-cry underrun with **333 blocks left**; 325 was
the earlier synthetic prediction. Weavile has six animation misses with the
dictionary already decoded and a naturally completing cry. Correct final duration
does not imply correct intermediate frames. The record includes every species'
miss/late-publication totals, operation costs, starting-state limitations, and
the next focused capture direction. No runtime change or resource allocation
was made. Older dated results below remain evidence history, not current
hardware-model defaults.

## Review Record: 2026-09-19

Status: **Weavile, Luxray, Dusknoir, Rayquaza, and Kyogre first-miss replays are
capture-consistent, subject to the trace qualifications below. Bastiodon,
Garchomp, Rampardos, and Metagross retain small timing/PPU-boundary residuals.
The runtime fix remains proposed, not implemented or validated.**

This is the durable findings and decision record for the final scheduler review.
The [host-model guide](../../dex_timing_model.md) documents implementation and usage;
the [bug backlog](../../pokedex_selected_bug_backlog.md) tracks this as `DEX-ANIM-01`.
Generated reports under `build/` are ignored by Git, so the essential evidence,
limitations, and proposed fix are also recorded here. Preserve this dated result
when adding subsequent cases; do not overwrite a historical result with a newer
model's output without recording what changed.

Scope is the Selected-Mon Dex page at normal CPU speed. Battle, New Dex Entry,
party Stats Screen redesign, and the separate A-button Description transaction
bug are outside this investigation's runtime-fix scope.

Priorities remain: no animation/audio underruns and authored animation timing;
responsive selection and paging; minimal ROM0/WRAM0/HRAM usage; then reduced
complexity and fragility. A slower animation or larger unconditional startup
pause is not an acceptable substitute for meeting the schedule.

## Build And Evidence

The tested configuration has 96 tail tiles of startup lead, plus the
dimension-dependent base picture, capped by dictionary length and raised if the
initial stage requires more. It retains two VRAM frame slots, six-tile independent
compressed streams, up to 20 gathered tiles per upload, and the compact ROMX
micro-schedule. Sampled cries use the pair-lookup decoder, 32-block startup fill,
and up to eight blocks per active refill.

Identity of the measured build:

```text
pokecrystal.gbc
7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
pokecrystal.sym
1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
```

The repository ROM and SameBoy copy were verified equal during the investigation.
No ROM rebuild, runtime change, new instrumentation, or resource allocation was
made to obtain the final host comparisons below.

Repository copies of the complete five-stop follow-ups:

- `tools/dex_timing/fixtures/weavile_owner_followup.txt`, SHA-256
  `c19ecf5c208849ec3a5cca4e0395aafcf3d45690564c3c53507afee2ffe52887`.
- `tools/dex_timing/fixtures/luxray_owner_followup.txt`, SHA-256
  `5ab0396a98ae095c9d233ba8f27889c2af5e8124ff5327d703da3229c6096e7a`.

Each follow-up covers first publication, next stage entry, producer entry,
return to the frame wait, and the first underrun check. The raw captures remain
the observations; events between those stops are model predictions.

Generated evidence for this review:

- `build/dex-timing-luxray-owner/manifest.json`: ROM, symbols, assets, runtime
  source, and host-tool identities.
- `build/dex-timing-luxray-owner/report.json`: focused asset/cost audit.
- `build/dex-timing-luxray-owner/followup.{md,json}`: Luxray linked replay.
- `build/dex-timing-luxray-owner/weavile-regression/followup.{md,json}`:
  Weavile regression comparison, including the older aggregate model's mismatch.

Hashes of the generated review artifacts, before any later rerun:

```text
manifest.json
97dab18b267fcb44af98cd562e39a1a2ce41341d81257bfcd5de8ef2b58ef4c8
Luxray followup.json
ba8925a2cbe91cf5dc264f1746d944fad6351798efded4b753e9982e87ca8d9b
Weavile followup.json
00253d536ff191b810235e06cc2d39b84c131600b9d8b17c661acb21b3a672cb
```

## What Was Corrected In The Host Model

The original quota model is insufficient as a timing authority. A producer call
is not guaranteed to occur once per hardware display interval, and the quoted
tile quotas do not account for the surrounding owner, interrupt, and wait work.
The host investigation added or corrected these operations, without changing
their behavior in the game:

1. Execute the actual linked owner/stage/producer/refill/interrupt instructions
   for a continuous first-publication-to-first-miss replay. Seed memory once;
   compare later stops without resetting state to the supplied dumps.
2. Include enabled LCD STAT interrupts even when `hLCDCPointer = 0`. Captured
   `IE = $0f` and mode-0 STAT enable mean the short 108-T handler still consumes
   time. Deliver pending requests with real priority and coalescing behavior.
3. Include footer STAT polls, owner return, deadline check, and `DelayFrame`'s
   wait-flag store/HALT/refill/return. A VBlank occurring before the new wait is
   armed does not satisfy that new wait.
4. Preserve Luxray's already-pending sample timer request at publication without
   delivering it twice. Use captured owner fields, including text-delay state.
5. Execute the upload helper's actual scanline, mode, and completion polls. Model
   one 16-byte HDMA block per eligible visible HBlank, its 32-T CPU stall, and
   continuing interrupt requests on the same elapsed-time clock. Do not add
   interrupt time to a transfer wait a second time.
6. Distinguish physical line 153 reporting LY zero from visible line zero. HDMA
   can be armed in that portion of VBlank but blocks wait for visible HBlank.
7. Compare both timer readings, display counter, LY/mode, enabled pending IF,
   animation state, and audio counts/pointers across all five stops. Report
   trace-timestamp residuals separately instead of hiding them in a pass flag.

## Timing Results

T means a normal-speed CPU clock. Each captured interval has +/-63 T observation
uncertainty, about +/-0.015 ms. These are elapsed times including interruptions
and waits, not pure mainline instruction costs.

| Species | Interval | Captured nominal T | Replay T | Difference T |
|---|---|---:|---:|---:|
| Weavile | Publication -> Stage Entry | 37,504 | 37,468 | -36 |
| Weavile | Stage Entry -> Producer Entry | 30,144 | 30,144 | 0 |
| Weavile | Producer Entry -> Frame Wait | 6,080 | 6,128 | +48 |
| Weavile | Frame Wait -> First Miss | 105,408 | 105,380 | -28 |
| Luxray | Publication -> Stage Entry | 37,440 | 37,428 | -12 |
| Luxray | Stage Entry -> Producer Entry | 25,792 | 25,760 | -32 |
| Luxray | Producer Entry -> Frame Wait | 5,184 | 5,232 | +48 |
| Luxray | Frame Wait -> First Miss | 1,936,512 | 1,936,524 | +12 |

One sampled initial state matches all five stops jointly for each species:
1/512 compatible sampled states for Weavile and 1/60 for Luxray. These counts
are finite searches of unknown initial phase/state, not probabilities, universal
phase coverage, or evidence of a unique physical state. Later observations do
not drive the replay. The nominal interval differences above and both timer
register sequences must agree under the same initial phase.

Both match all 27 animation-state bytes, upload progress, display counter,
LY/mode, enabled IF bits, audio cache/remaining counts, and audio source/read/write
pointers at all five stops. Weavile also matches all 139 trace bytes at those
stops. Luxray has seven differing trace bytes at its final stop:

- `$c783`: captured `$49`, modeled `$4a`, one stage-entry LY timestamp.
- `$c7af/$c7b1/$c7b3/$c7b5/$c7b7/$c7b9`: captured `$42`, modeled `$43`,
  six timestamps from one idle producer record.

These are one-scanline timestamp differences, not different event IDs, actions,
quotas, schedule positions, or completed-work values. The reason for the exact
residuals has not been independently isolated. Do not label this byte-identical
or exact-cycle hardware emulation.

The first stage-construction leg separates as follows in the matching replay:

| Species | Stage construction | Caller return | Sample IRQs | Short LCD IRQs | Total T |
|---|---:|---:|---:|---:|---:|
| Weavile | 19,180 | 128 | 3 x 1,452 | 60 x 108 | 30,144 |
| Luxray | 17,220 | 128 | 2 x 1,452 | 51 x 108 | 25,760 |

There is no new dictionary decoding, VRAM upload, or cache refill in those two
specific stage legs. They demonstrate meaningful map-construction and interrupt
cost, rather than proving every expensive call is an HDMA or decoder problem.
These are measured paths, not worst-case limits for every species or phase.

## Failure Chains

All interval numbers below use the first publication's VBlank as interval zero.
Queueing a map and publishing it to the display are distinct operations.
`Pokedex_AnimationDeadlineDue` checks the *next* display counter, so a breakpoint
in interval 28 can diagnose a missing interval-29 frame before visible corruption.

### Weavile

The next stage requires 18 uploaded tiles. Construction and the remaining owner
work cross VBlank before `DelayFrame` re-arms its wait. The resulting wait skips
a producer opportunity. The call-index schedule remains behind elapsed display
time, and the first deadline check finds 0/18 uploaded tiles. The dictionary is
already decoded; no HDMA transfer runs in this captured replay segment.

This case isolates owner-loop/wait sequencing and work-release drift without
requiring an explanation based on upload-transfer duration.

### Luxray

The matching replay gives the following more extensive chain. Intermediate
scanlines and calls are predictions constrained by the five captured stops.

1. The initial frame wait is reached at LY 141, before VBlank. Luxray does not
   suffer Weavile's initial missed wait opportunity.
2. Schedule actions 0 through 8 are idle. Action 9 reaches the 17-tile upload
   helper in interval 9 at LY 126. The helper requires `LY < 128 - 17`, or
   `LY < 111`; it therefore waits into interval 10.
3. The transfer is armed while physical line 153 reports LY zero, completes
   after the intended interval-10 publication, and queues the map in interval
   10. Actual publication occurs in interval 11. This late publication is not
   itself the later unfinished-stage breakpoint.
4. Subsequent resident/base events publish at intervals 13, 16, 19, and 22.
   Event 7/frame 2 preparation starts in interval 22. Construction plus the
   caller's remaining work crosses VBlank before the next wait is armed, moving
   the next producer opportunity to interval 24 instead of interval 23.
5. At interval 28 the producer still consumes idle action 26. The intended
   upload actions at indices 27 and 28 have not run when the interval-29
   deadline is checked. The stage has 0/21 tiles uploaded despite all 134
   dictionary tiles being decoded. The cry cache contains 87 blocks.

The initial upload wait and the later owner/wait crossing both contribute to
schedule drift. The seven-interval hold does not mean seven producer calls with
20 usable uploads each. Conversely, this failure is not proof that the 21 tiles
cannot be uploaded somewhere within that hold: work was not released in time.

## Conclusions And Confidence

**Supported by code and capture-consistent replay:** publication deadlines and
producer progress use different time bases; owner/wait sequencing can lose
service opportunities; an upload can enter its helper too late for the intended
publication window; the current idle-run schedule does not recover from that
drift. Both cases fail despite an already-decoded dictionary.

**Not established:** that the normal-speed GBC lacks enough total capacity;
that all remaining species fail for exactly these reasons; that removing the
drift alone will guarantee every deadline; or that audio can be deprioritized
without creating a separate failure. Luxray's healthy cache at this stop is not
a full-suite audio guarantee.

The broad audit and the focused replay have different maturity. The older
aggregate model still has residual timing discrepancies. Overall follow-up
reports remain `PARTIAL_NOT_CALIBRATED`; the linked cases are only
`CAPTURE_CONSISTENT`. The broad validator must not be promoted to a universal
deadline authority merely because these two cases agree.

Remaining limitations include fixed HBlank timing, an assumed initial publication
dot, simplified sub-instruction DMA/bus arbitration, unknown divider phase,
uncaptured initial pixels/maps, and finite phase sampling. The linked CPU and
IRQ paths share the instruction counter, so unit tests are not an independent
emulator. The initial two-case replay rejected partially decoded dictionaries;
the extension below now supports verified decoded prefixes. Neither iteration
covers complete animations or arbitrary input.

## Dusknoir And Bastiodon Extension: 2026-09-19

Both supplied five-stop captures are complete. Their final section is named
`Frame Miss`; the parser accepts this as `First Miss` only when its PC is the
linked `Pokedex_CountAnimationUnderflow` address. The original label is retained.
Raw, byte-identical repository copies and SHA-256 identities:

- `tools/dex_timing/fixtures/dusknoir_owner_followup.txt`:
  `88a9d0c9dc401998317bdaa43e347677c8011902aa3b25bf20567828e9c49aed`.
- `tools/dex_timing/fixtures/bastiodon_owner_followup.txt`:
  `98c057bd44fa1bef056b34220e9085c14eba1525ac819da57c96d93c41ae1426`.

The ROM, symbols, and SameBoy ROM copy still match the build identities above.
No runtime instructions, asset layout, or game resources changed for this review.

### Coverage Correction

These are **partially decoded initial dictionaries**, but they are **not tests
of ongoing dictionary decoding after publication**. Both remain at 145 decoded
tiles through the first miss. All tiles needed for the failed second frame are
already in the decoded prefix. The new host support restores only that prefix,
checks its compressed-source and WRAM destination pointers against the linked
stream boundaries, and leaves the future tail unseeded. It does not make the
remaining dictionary available early to obtain a match.

| Observed or asset-verified property | Dusknoir | Bastiodon |
|---|---:|---:|
| Total dictionary tiles | 247 | 213 |
| Decoded tiles at publication and miss | 145 | 145 |
| Tiles still undecoded at miss | 102 | 68 |
| Second frame's required dictionary prefix | 111 | 121 |
| Second stage's upload requirement | 32 | 37 |
| Completed uploads at first miss | 20 | 20 |
| Authored first hold / second-frame deadline, display intervals | 7 | 5 |
| Sampled-cry cache at miss, blocks | 37 | 31 |

The prefix high-water numbers and required upload counts come from the linked
frame plans, checked against the capture's stage state. The healthy audio-cache
counts establish only that the cry is not empty at these stops, not full-playback
audio safety.

### Five-Stop Comparison

Generated artifacts are under `build/dex-timing-expanded-owner/`: the four-species
audit/manifest, `dusknoir/followup.{json,md}`, `bastiodon/followup.{json,md}`, and
separate Weavile/Luxray regression reports. The default publication origin remains
600 T and HBlank starts at dot 257. No species-specific operation cost was added.

| Species | Interval | Captured nominal T | Default-origin replay T | Difference T |
|---|---|---:|---:|---:|
| Dusknoir | Publication -> Stage Entry | 37,184 | 37,208 | +24 |
| Dusknoir | Stage Entry -> Producer Entry | 43,968 | 43,968 | 0 |
| Dusknoir | Producer Entry -> Frame Wait | 3,712 | 3,696 | -16 |
| Dusknoir | Frame Wait -> First Miss | 423,872 | 423,848 | -24 |
| Bastiodon | Publication -> Stage Entry | 37,440 | 37,444 | +4 |
| Bastiodon | Stage Entry -> Producer Entry | 47,488 | 47,480 | -8 |
| Bastiodon | Producer Entry -> Frame Wait | 3,776 | 3,788 | +12 |
| Bastiodon | Frame Wait -> First Miss | 279,552 | 279,548 | -4 |

All elapsed differences are inside +/-63 T capture precision. State comparison
remains stricter than the elapsed-time comparison:

- **Dusknoir: `CAPTURE_CONSISTENT`.** Nine of 64 sampled initial phases match
  the core state and clocks; three also match every byte in each of the five
  139-byte trace dumps. The displayed example uses timer phase 10,180 T and DIV
  low byte 152. All 27 animation-state bytes, LY/mode, display counter, enabled
  IF, audio counts/pointers, DIV/TIMA, and all trace bytes agree. Trace equality
  constrains an already compatible unknown initial phase; it does not alter
  operation costs or reseed later observations.
- **Bastiodon: `RESIDUAL_MISMATCH` at the default origin.** None of 64 candidates
  matches core state and timers together; 13 match the timer sequence. The
  closest timer-compatible example uses phase 340 T and DIV low byte 200. All
  animation bytes, audio counts/pointers, LY and display counters agree at all
  five stops. Only Producer Entry's mode and pending LCD request disagree:
  captured mode 0 / enabled IF `$02`, modeled mode 3 / enabled IF `$00`.
  The modeled PC is at LY 23, dot 252, five T before the assumed HBlank edge.
  Five trace-byte observations also differ, all copies of one stage-entry LY
  timestamp: captured 74, modeled 73. The report shows these rather than
  promoting a close timing match to a pass.

**Separate sensitivity check, not a calibration change:** publication at 608 T
instead of 600 T, phase 340 T, and DIV low byte 208 produces a Bastiodon replay
matching all core state, both timers, and every captured trace byte. Its elapsed
legs are `[37444, 47480, 3788, 279540]` T. The changed publication dot is not
directly measured by these captures. This shows that eight T (about 1.9 us) of
initial timing adjustment is sufficient; it does **not** prove that the initial
origin is the actual source of the residual. It remains possible that local
poll/interrupt/PPU alignment contributes. Do not change operation prices, add a
per-species offset, or call the unadjusted Bastiodon replay identical.

The host regression
`test_bastiodon_origin_sensitivity_is_not_an_operation_cost_change` preserves the
608-T experiment separately from the default-origin residual test. The bounded
exploration of origins 592, 596, 600, 604, 608, 612, and 616 T yielded respectively
1, 2, 0, 0, 4, 4, and 4 all-core/timer/trace matches among 64 candidates per origin.
This is sensitivity analysis, not a probability or a proof of the correct origin.

### What The Added Cases Establish

Stage Entry -> Producer Entry breaks down as follows. These linked-instruction
decompositions explain elapsed cost; only their totals were directly timed in
SameBoy.

| Species | Mainline stage plus caller return | Sample IRQs | LCD IRQs | VBlank IRQ | Total T |
|---|---:|---:|---:|---:|---:|
| Dusknoir | 28,192 | 4,356 | 8,640 | 2,780 | 43,968 |
| Bastiodon | 29,604 | 5,808 | 9,288 | 2,780 | 47,480 |

No dictionary decode, upload, or audio refill occurs in these two stage legs.
Unlike the earlier two-species table, both legs include a VBlank interrupt:
construction starts late enough to cross the display boundary. The first producer
therefore runs in interval 1, already one interval behind its idle-action cursor.

The linked schedules begin with five idle actions for Dusknoir and three for
Bastiodon. Their first two upload actions are at indices 5/6 and 3/4 respectively.
The subsequent sequence is constrained by captures but intermediate locations
remain model predictions:

1. The already-decoded second stage is prepared; the call-index schedule still
   consumes its idle actions despite the display clock having advanced.
2. Dusknoir reaches the 20-tile helper in interval 6 at LY 135; Bastiodon reaches
   it in interval 4 at LY 137. Both are after the helper's `LY < 108` launch cutoff.
3. The helper waits into interval 7 or 5, respectively. Only the first 20-tile
   transfer completes before the owner checks the already-due second-frame
   deadline. The remaining 12 or 17 tiles have not been uploaded.

Both the default Bastiodon replay and the 608-T sensitivity replay give this same
work/deadline outcome. That finding does not depend on choosing the phase that
makes the small HBlank-state residual disappear.

These cases strengthen the existing fix direction: release ready work early
under slot ownership, account for construction and legal upload windows, and
keep display-time progress distinct from completed work. **More initial dictionary
decoding cannot fix these particular misses by supplying missing source tiles:**
those source tiles are already ready. A different preload can change timing, but
that is not proof that dictionary availability was the underlying cause.

No repeat capture or video is needed to diagnose these two first misses. A later
interval with actual dictionary decoding is still a separate coverage gap; do
not mark concurrent decode/upload/audio scheduling or entire animations validated
on the strength of this extension.

## Five Additional Species: 2026-09-19 Results

All five supplied files contain the five consecutive stops, common dumps, and
first-publication extras requested in the capture sheet. The shorter Rayquaza
file is not missing required data. The static first publications for Rayquaza,
Kyogre, and Metagross are correct. Every capture reports normal CPU speed,
`IE = $0f`, the expected Selected display configuration, and the linked stop PCs.

Exact repository copies, verified against the originals in Downloads:

| Fixture under `tools/dex_timing/fixtures/` | SHA-256 |
|---|---|
| `garchomp_owner_followup.txt` | `d53bfdb4626ff3ee540936361632b9d6f8f936fc05a94961f503276b4febb068` |
| `rampardos_owner_followup.txt` | `d335d0e97d94ba11e49fd77da8526688719f3e399fb4636918e296fa836574d5` |
| `rayquaza_owner_followup.txt` | `222ac1eac90023eef2785008299a8174fe626d272da262287a60e801093dff97` |
| `kyogre_owner_followup.txt` | `423efee27313f11e37527d9f54fcc52e22fba2cd0ce39d00643da506277f6247` |
| `metagross_owner_followup.txt` | `833620ee4f1fc45742d9ebbe4eebbc6866e84929ab3ee59399130247d8f95bf4` |

### Directly Captured Outcomes

Events are one-based timeline occurrences, not distinct sprite-frame IDs.
Hardware interval zero is the first publication VBlank. The miss check tests
the upcoming display deadline, so a miss may be detected one interval before
the due interval or before visible corruption appears.

| Species | Decoded / total dictionary | Failed event | Sprite frame ID | Uploaded / required | Due interval | Miss-check interval | Audio blocks cached |
|---|---:|---:|---:|---:|---:|---:|---:|
| Garchomp | 140 / 140 | 2 | 2 | 20 / 29 | 5 | 5 | 31 |
| Rampardos | 145 / 155 | 2 | 2 | 20 / 38 | 4 | 4 | 28 |
| Rayquaza | 115 / 115 | 3 | 2 | 0 / 20 | 11 | 10 | 42 |
| Kyogre | 124 / 124 | 3 | 6 | 0 / 10 | 9 | 8 | 45 |
| Metagross | 97 / 97 | 11 | 4 | 0 / 17 | 44 | 43 | 133 |

No additional dictionary decoding occurs between first publication and first
miss in any of these five runs. Rampardos retains ten undecoded tiles, but its
second stage needs only the first 118, already inside its available 145-tile
prefix. The other four dictionaries are complete from the start. These are
not failures to supply missing dictionary source bytes at the captured miss.

Rayquaza, Kyogre, and Metagross each already record one publication one display
interval late before reaching this unfinished-stage breakpoint. Garchomp and
Rampardos do not yet record a late publication. The two diagnostics therefore
need to remain distinct: an unfinished stage can miss, and a fully uploaded
stage can also reach publication too late.

Every audio cache is nonempty at its animation miss. This does not certify
whole-cry completion or remove audio's CPU/interrupt cost; it only rules out
an already-empty sampled-cry cache at these particular stops.

### Continuous Host Comparison

The extension adds these five supported capture fixtures to the existing linked
replay. It does not change operation costs, interrupt rules, default publication
origin (600 T), or HBlank assumption (dot 257). One initial memory state runs
through all five stops. Later dumps are comparisons, never state resets.

Each 64-candidate search varies the permitted initial timer/divider phase;
these counts are not probabilities. All cases remain within the host's overall
`PARTIAL_NOT_CALIBRATED` scope even where the sampled capture is consistent.

| Species | Core state plus joint timers | Also all trace bytes | Result |
|---|---:|---:|---|
| Garchomp | 0 / 64 | 0 / 64 | Frame Wait scanline/mode residual |
| Rampardos | 0 / 64 | 0 / 64 | Two mode differences and elapsed/timer residuals |
| Rayquaza | 2 / 64 | 2 / 64 | All five stops capture-consistent |
| Kyogre | 12 / 64 | 8 / 64 | All five stops capture-consistent |
| Metagross | 0 / 64 | 0 / 64 | Early one-scanline and joint-timer residuals |

Selected comparison elapsed times, T-cycles:

| Species | Publication -> stage | Stage -> producer | Producer -> wait | Wait -> first miss |
|---|---:|---:|---:|---:|
| Garchomp captured | 37,440 | 43,520 | 3,648 | 283,648 |
| Garchomp replay | 37,444 | 43,524 | 3,680 | 283,624 |
| Rampardos captured | 37,440 | 48,576 | 5,120 | 208,448 |
| Rampardos replay | 37,444 | 48,708 | 5,132 | 208,204 |
| Rayquaza captured | 36,992 | 24,960 | 5,376 | 673,600 |
| Rayquaza replay | 36,976 | 25,012 | 5,348 | 673,580 |
| Kyogre captured | 37,440 | 20,992 | 3,648 | 538,816 |
| Kyogre replay | 37,428 | 21,008 | 3,672 | 538,804 |
| Metagross captured | 36,928 | 15,808 | 3,712 | 3,002,304 |
| Metagross replay | 37,428 | 15,824 | 3,672 | 3,001,832 |

Each captured elapsed value has +/-63 T observation uncertainty. A whole
scanline is 456 T and a display interval is 70,224 T at normal speed.
Rayquaza and Kyogre agree within the bounds on every leg and match the core,
audio, hardware, joint timer readings, and all 139 trace bytes at every stop.

Garchomp fits all four elapsed bounds and a single timer phase, but the host
reaches Frame Wait at LY 22/dot 432/mode 0 versus captured LY 23/mode 2.
All animation/audio state matches. Six trace-byte observations differ by one
scanline. This boundary mismatch is retained as a failure of exact agreement.

Rampardos differs by +132 T during stage construction and -244 T in the last
leg, beyond the observation bounds. It has Producer Entry mode 3 versus captured
mode 2 and First Miss mode 2 versus captured mode 3. All animation/audio fields
and scanline numbers agree. Forty-six trace-byte observations differ by one
scanline, including repeated observations of the same stored timestamps.

Metagross differs by +500 T before stage entry and -472 T in the last leg.
The stage/producer/wait stops are each one scanline later in the host; other
core fields agree. Thirty-three early trace-byte observations differ by one
scanline. The final miss's entire core state and trace match, but no single
initial timer phase accounts for all five stops. Matching the final dump alone
is not sufficient to call the continuous replay calibrated.

The diagnostic report now displays the nearest elapsed-time candidate even
when no timer/interval-compatible candidate exists. It explicitly labels that
candidate **not a passing replay**, lists the residuals, and never promotes it
to `CAPTURE_CONSISTENT`. Previously such a failure could leave the report with
no illustrative sequence. This reporting change does not alter runtime costs.

A separate sensitivity check varied the initial publication origin from 584
through 616 T in four-T steps, keeping one selected phase per species. It can
remove some Garchomp or Metagross state/trace discrepancies, but no tested
combination simultaneously matched all core/timer observations. Rampardos'
construction residual remained. This was not a full alternate-origin phase
sweep, and it does not establish the residuals' cause. No per-species origin
or timing adjustment was adopted.

### What The Replays Add

The following intervening operations are model predictions, not additional
captured breakpoints. Rayquaza and Kyogre's predictions have full five-stop
agreement; the other three retain the timing qualifications above.

- **Garchomp:** building event 2 crosses VBlank. The 20-tile helper is reached
  in interval 4 at LY 138, after its `LY < 108` launch limit. Upload waits into
  interval 5; only 20 of 29 tiles are complete at the miss.
- **Rampardos:** the corresponding 20-tile helper is reached in interval 3
  at LY 135. It waits into interval 4 and leaves 20 of 38 tiles complete.
- **Rayquaza:** event 2's 15-tile helper is reached in interval 5 at LY 116,
  after its `LY < 113` limit. Queueing occurs in interval 6, and publication
  occurs in interval 7 instead of 6. Event 3 then misses with 0/20 uploaded.
- **Metagross:** its initial three-tile transfers and resident frame alternation
  reach the expected publication intervals through event 9. Event 10's 17-tile
  helper is reached in interval 36 at LY 126, after its `LY < 111` limit.
  It waits into interval 37 and publishes in 38 rather than 37. Event 11 then
  misses with 0/17 uploaded. This is not a failure of the initial small transfers.

**Kyogre provides an additional, distinct deadline-budget failure.** Its event 2
needs only ten tiles. The helper is reached in interval 5 at LY 103, before the
`LY < 118` launch limit, and arms HDMA at LY 104. The transfer completes at
407,497 T, before the interval-6 VBlank at 421,344 T. Nevertheless, the map-queued
trace occurs at 430,884 T (interval 6, LY 10), and actual publication is in
interval 7 rather than the authored interval 6.

The remaining path includes stage completion, bookkeeping, instrumentation,
and map preparation. `Pokedex_CommitAnimationFrontpicMap` first copies the
packed 7x7 tilemap and attributes into the backing maps; then
`Pokedex_StageCurrentFrontpicOwnerMaps` copies them into the persistent owner
buffers before setting the pending-publication flag. Interrupt work continues
around this mainline work. An upload-only scanline cutoff is therefore not a
publication deadline budget. The second frame is fully uploaded but not queued
for the needed VBlank; the subsequent ten-tile stage then misses with 0/10 done.

This strengthens, rather than replaces, the proposed fix direction: budget the
**whole path through publication-ready state**, prepare work early when slot
ownership permits, and keep elapsed display time separate from completed work.
Simply finding an earlier legal HDMA start or adding more startup dictionary
tiles is not demonstrated to solve every case. Do not delete either map-copy
pass without first auditing the ownership/atomic-publication contract.

### Remaining Evidence Needs

No missing dump, repeat run, or video is needed from the user for this pass.
The current captures are sufficient to investigate the remaining small host
timing differences. Request a targeted additional stop only if that work exposes
an ambiguity that these observations cannot resolve.

The broader coverage gap remains: none of these first-miss runs actually
executes more dictionary decoding during the measured interval. These results
do not validate concurrent late-dictionary production, complete animations,
all possible interrupt phases, or whole sampled-cry playback. Those stay on the
final review checklist. Nor do the reproduced missed events prove that normal
speed cannot meet the authored timing with a corrected scheduler.

## Boundary Investigation Follow-Up: 2026-09-19

The [detailed boundary investigation](dex_timing_boundary_investigation.md)
records the next host-only pass and its reproducible probes. SameBoy source and
a synthetic CGB-E core probe identified missing interrupt-acknowledgment timing,
HALT wake timing, DMA setup/tail cost, DMA request-versus-execution timing, and
separate LY/STAT/interrupt transitions.

A combined probe at a common 606-T publication origin fully matches Garchomp,
Rampardos, and Metagross across all five stops, joint DIV/TIMA observations,
elapsed bounds, and every trace byte. It also fully matches Dusknoir, Bastiodon,
Rayquaza, and Kyogre. These matches do not require species-specific operation
costs. They do still assume an initial publication phase rather than measuring it.

Cross-checking earlier cases prevents declaring the model finished: Weavile is
one T from the line-153 early-LY boundary at that origin, and Luxray does not yet
match the combined setup. Nearby-origin experiments can match Weavile but do
not resolve Luxray. The default model and game remain unchanged; the experimental
probe is separate and explicitly marked as sensitivity work. The 113 existing
host tests still pass.

The targeted request was **one Luxray five-stop capture**, adding
SameBoy's `ticks`/`ticks keep`, `lcd`, and a few initial housekeeping fields.
The [full directions](dex_timing_boundary_investigation.md#focused-next-capture-luxray-historical)
require no new ROM, instrumentation, video, or rerun of the five new species.
This directly measures elapsed cycles and narrows the initial PPU phase instead
of adjusting costs to make separate cases fit.

**Exact-cycle follow-up received:** `Luxray - Pass 4.txt` supplies those counters
and LCD states (but not the extra housekeeping dumps). The unchanged combined
probe now matches all core state and trace bytes, with elapsed differences
`[0, 0, 0, +8]` T. The LCD state independently supports the 606-T origin for
this run. The eight-T final residual is about 1.91 microseconds and remains
explicitly uncalibrated; the default replay is not replaced. See the
[complete exact-cycle result](dex_timing_boundary_investigation.md#luxray-exact-cycle-follow-up)
for the measurements, reproduction, limitations, and rejected HALT-edge
hypothesis. No additional capture or subsequent-miss suite is requested now.

**Independent-core continuation:** using the user's refreshed SameBoy source
at `213a12c`, all 159,711 executed non-HALT instruction starts match the corrected
host probe in bank, PC, and elapsed cycles. The independent synthetic core
reproduces the same `[0, 0, 0, +8]` interval residual against Pass 4. A 256-state
DIV/subcycle sweep does not remove it. This rules out a missing instruction or
wait cost for that constructed state, but does not certify its uncaptured
starting memory/PPU state. The [detailed core comparison](dex_timing_boundary_investigation.md#independent-sameboy-core-replay)
records the corrected scroll-shadow fixture, exact timings, limits, and the
next focused evidence: a complete emulator state at first publication and the
first-miss clock from the same run, not another full capture suite. All 124 host
tests pass; no runtime, default-model, or ROM changes were made.

**Actual save-state continuation (2026-09-20):** slot 10 supplies the complete
initial state for a new Luxray run. The [read-only state comparison](dex_timing_boundary_investigation.md#actual-save-state-calibration-2026-09-20)
now matches the user's **2,004,944 T** interval exactly, including initial/final
registers and final line 76/OAM 31/40. All 159,713 non-HALT instruction starts
match the independent SameBoy core in timing, bank, PC, and general-purpose
registers; the 27 animation and 139 trace bytes match at all five comparison
stops. The source-supported HALT-pending-during-instruction variant is required
for the interior trace, not merely endpoint agreement. The old partial Pass 4
eight-T regression is preserved and not misrepresented as the same run.
No further Luxray capture is needed for this first-miss calibration. All 129 host
tests pass; the game/default model remain unchanged. Broader phase coverage,
Weavile's older boundary qualification, and actual late-dictionary execution
remain separate gates.

The observed game failure chain and proposed runtime fix direction below are
unchanged. The new work concerns the precision of the host used to evaluate
that future fix, not an additional game patch.

## Proposed Fix Direction

This is a design direction for review, **not a finalized implementation or an
approved memory/bank allocation**. Keep the exact timeline and deadline-controlled
atomic publication. Change how preparation is released and completed.

1. **Use the hardware display clock for release/deadline decisions.** Keep an
   animation epoch and authored event deadlines. Track decoded dictionary extent,
   stage construction, uploaded extent, residency, and publication independently.
   A missed call must not move the authored timeline or erase unfinished work.
2. **Treat schedule entries as work/dependencies, not a clock that advances once
   per invocation.** Retain pending operations until complete. Do not replay
   elapsed idle slots or skip unexecuted uploads to catch up. Coalescing overdue
   work must still respect a bounded per-service time budget.
3. **Prepare early when ownership allows it.** Decode needed dictionary data,
   build maps, and upload into an actually free off-screen slot before the last
   legal interval. Preserve the displayed slot and every queued map/source.
   Two in-flight jobs would be cooperative work on one CPU, not extra capacity;
   a second producer, extra VRAM slots, or precomputed stage tables are options
   to evaluate, not requirements established by these captures.
4. **Budget upload windows before entering a blocking helper.** Include stage
   construction, gathering, bank changes, interrupt pressure, helper launch
   cutoff, transfer, map queueing, and the next publication. Arriving at LY 126
   with 17 tiles is already too late under the current helper. Moving work
   earlier or selecting a smaller legal chunk are candidate solutions; changing
   a universal quota alone is not a demonstrated solution. Kyogre additionally
   proves that a legal transfer start and pre-VBlank transfer completion can
   still leave too little time for the remaining publication preparation.
5. **Audit the owner's return/wait contract.** Crossing VBlank during work must
   not silently lose the next useful service opportunity. Any elapsed-frame-aware
   wait or additional bounded service point should be scoped to the Selected
   owner first, without an unreviewed global `DelayFrame` change, busy catch-up
   loop, duplicate per-frame service, input starvation, or audio starvation.
6. **Make generator, runtime, and validator describe the same work semantics.**
   Validate execution costs and legal release windows, not just six decode tiles
   and twenty uploads per nominal tick. Keep dependencies and completed work
   explicit. Retain exact timelines, frame-plan data, and high-water safety
   checks until a replacement proves that any removed metadata is redundant.
7. **Keep failures visible.** Do not stretch authored holds, silently drop frames,
   or stop counting misses to make a test pass. Track unfinished-stage misses
   separately from maps that were complete but published late.

Code touchpoints for the eventual reviewed implementation (symbol names are the
stable references; addresses/line numbers change when the ROM is rebuilt):

| Responsibility | Current code |
|---|---|
| Selected owner ordering | `engine/pokedex/pokedex_detail.asm`: `PokedexSelectedMon_Update` |
| Main loop and frame wait | `engine/pokedex/pokedex.asm`: `Pokedex.main`; `home/delay.asm`: `DelayFrame` |
| Action consumption | `engine/pokedex/pokedex_animation.asm`: `Pokedex_ServiceAnimationProducer`, `Pokedex_GetNextAnimationScheduleAction` |
| Stage turnover/construction | Same file: `Pokedex_PrepareDescriptionAnimation`, `Pokedex_FinalizePublishedAnimationStage`, `Pokedex_PrepareNextAnimationStage`, `Pokedex_BuildAnimationStage` |
| Upload and progress | Same file: `Pokedex_GatherReadyAnimationTiles`, `Pokedex_ServiceAnimationUploadChunk`, `Pokedex_FinishAnimationStage` |
| Upload launch/completion waits | `home/gfx.asm`: `Pokedex_HDMATransferAnimationGFX`; `engine/gfx/dma_transfer.asm`: `HDMATransfer_Exact_NoDI_Arbitrary` |
| Deadline and queue | `engine/pokedex/pokedex_animation.asm`: `Pokedex_AnimationDeadlineDue`, `Pokedex_CommitDescriptionAnimation`, `Pokedex_QueueReadyAnimationStage` |
| Atomic publication | `engine/pokedex/pokedex_3.asm`: `Pokedex_CommitAnimationFrontpicMap`, `Pokedex_VBlankAnimationFrontpicMap` |
| ROMX schedule/timeline readers | `engine/pokedex/pokedex_animation_schedule.asm`, `engine/pokedex/pokedex_animation_timeline.asm` |
| Generated plans and validation | `tools/pokemon_animation.c`; `tools/dex_timing/` |

This investigation has spent **zero additional ROM0, ROMX, WRAM0, WRAMX, HRAM,
or VRAM bytes in the game**. Exact runtime-fix costs are not yet estimated.
Preflight those costs, union lifetimes, bank headroom, and required metadata
before implementation; do not interpret host-only work as approval for new
premium memory reservations or a higher startup preload.

## Next Evidence And Final Review Gates

- [x] Preserve raw five-stop Weavile/Luxray captures and measured build identity.
- [x] Obtain one continuous core-state/timer match per case, without later reseeding.
- [x] Re-run Weavile after adding Luxray HDMA support; retain the timestamp residuals.
- [x] Pass all 95 host tests and the focused two-species asset audit.
- [x] Add Dusknoir/Bastiodon partial-prefix captures and heavy upload comparisons;
      preserve Bastiodon's boundary residual rather than hiding it.
- [x] Pass 106 host tests and the four-species asset audit for this extension.
- [x] Preserve and compare all five additional species; retain three timing
      residuals and record Kyogre's post-upload publication-preparation failure.
- [x] Pass 113 host tests and the five-species executed-output asset audit.
- [x] Reproduce a full-state Luxray first-miss run with exact endpoint timing and
      instruction-by-instruction reference-core agreement; pass 129 host tests.
- [x] Promote validated boundary behavior into the normal linked replay and
      compare complete animation/cry continuations for all nine species.
- [x] Exercise runtime dictionary decode in the full host/reference-core
      Dusknoir continuation, retaining its partial-capture qualification.
- [x] Capture and compare actual-state dictionary decoding alongside owner,
      upload and audio work: Dusknoir slot 8 and its full continuation close
      this gate; see the end-to-end record.
- [x] Run host-only wait/clock/early-work/order/suffix controls from all three
      actual starts; preserve duplicate-publication and phase-sensitive failures.
- [ ] Broaden phase coverage and bound or explain the remaining timestamp residuals
      wherever they could change a scheduling decision.
      The first 48 synthetic timer-phase policy runs are recorded, not a full
      phase/owner-state certification.
- [ ] Agree on a concrete Selected-only runtime design and resource-cost preflight.
- [ ] Make the generator, model, and runtime share the new work-release/completion
      contract; reject unsupported or insufficient schedules explicitly.
- [ ] Show authored publication intervals and total animation duration on the
      new build, with neither unfinished-stage underruns nor late publications.
- [ ] Verify sampled-cry completion and adequate refill opportunity alongside
      the animation, not just a healthy cache at one breakpoint.
- [ ] Compare cold/warm selection and internal paging latency; include rapid
      cancel/re-entry and repeated frame/resident-slot cases without hiding misses.
- [ ] Re-run broader assets, controls, and counter-wrap cases before signoff.
- [ ] Reconcile superseded schedule metadata/validators and remove temporary
      instrumentation only after the final review; document retained ROMX cost.

No repeat capture or video is required for the four first-miss cases at this
point. New species/intervals need new captured state and any required host support;
do not silently reuse a fully decoded dictionary fixture for partially loaded cases.
The build-bound [Dusknoir/Bastiodon capture instructions](dex_timing_capture_dusknoir_bastiodon.md)
preserve the five-stop procedure and initial owner-state supplement used above.
No runtime fix or universal timing guarantee is signed off by this record.

### Requested Five-Species Expansion

The user supplied all five requested cold runs for Garchomp, Rampardos,
Rayquaza, Kyogre, and Metagross. The
[additional-species capture sheet](dex_timing_capture_five_species.md) preserves
the unchanged-ROM procedure. Results and qualifications are recorded under
[Five Additional Species](#five-additional-species-2026-09-19-results); these are
no longer pending captures, but three retain host-timing residuals.

The linked startup rule fully decodes Garchomp (140 tiles), Rayquaza (115),
Kyogre (124), and Metagross (97) before playback. Rampardos starts with 145/155
tiles decoded; its second stage requires only the first 118. Thus this suite
adds meaningful map/upload/residency and cry-overlap variety, but may still stop
before any ongoing dictionary decode. Do not mark that separate coverage gate
complete merely because Rampardos has a partially decoded initial dictionary.

Rayquaza, Kyogre, and Metagross start with timed frame 0. Their first publication
is deliberately captured while the picture still looks static; skipping it
would select a different event/epoch and invalidate the initial-state assumption.
No extra ROM instrumentation, runtime edits, or resource allocation is requested
for these captures. Repeat runs and video remain contingent on a concrete gap.

## Reproduction

Using the measured ROM/symbols and corresponding assets, run from the repository
root. These commands do not rebuild the game. Preserve older reports by choosing
a separate output directory for a different host revision or ROM.

```sh
python3 -B -m unittest discover -s tools -p test_dex_timing.py
python3 -B tools/verify_dex_timing.py audit --species weavile luxray --jobs 2 \
  --profile tools/dex_timing/fixtures/selected_no_input.json \
  --output build/dex-timing-luxray-owner
python3 -B tools/verify_dex_timing.py followup \
  tools/dex_timing/fixtures/luxray_owner_followup.txt --species luxray \
  --report build/dex-timing-luxray-owner/report.json \
  --rom-sha256 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f \
  --output build/dex-timing-luxray-owner
python3 -B tools/verify_dex_timing.py followup \
  tools/dex_timing/fixtures/weavile_owner_followup.txt --species weavile \
  --report build/dex-timing-luxray-owner/report.json \
  --rom-sha256 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f \
  --output build/dex-timing-luxray-owner/weavile-regression
```

The 2026-09-19 verification completed with 95 tests passing, both linked cases
`CAPTURE_CONSISTENT`, and `git diff --check` clean. This record and its backlinks
are documentation-only additions; committing them remains a separate user step.

The subsequent Dusknoir/Bastiodon extension completed with **106 tests passing**,
the four-species executed-output audit passing, and `git diff --check` clean.
Weavile's regression still has 1/512 core/timer/trace matches; Luxray still has
1/60 core/timer matches with the same seven one-scanline trace residuals. No
previous operation costs or matching example timings changed.

Final extension artifact hashes under `build/dex-timing-expanded-owner/`:

```text
manifest.json
8f979eca04d458499f9bd9a857c6b5928702931c818d14fdfb89abdfe845898b
dusknoir/followup.json
00ce9f3ad3248847e36f82b90bd5fba6a0e15a3879d43b4e9e82575f6261acdc
bastiodon/followup.json
b5e9948f16cde1b6ce80d16268ada3e6d2ca2825d060dc2f9dc6adda3c41bfee
weavile-regression/followup.json
730d2488cee94931de4f000494e6f3f1651766faabd4c8e273d3c7afeee1ce77
luxray-regression/followup.json
47d65e86ba39e4f549c75f053c49f8c1abda536cec17f8d08f150d242066ff11
```

The five-additional-species extension completed with **113 tests passing**, all
five linked asset sets' executed decode/build/gather outputs validated, and
`git diff --check` clean. ROM and symbols retain the hashes above; the SameBoy
ROM still matches. Changes are limited to host fixtures/support/reporting/tests
and documentation, with no game rebuild or runtime edits.

```sh
python3 -B tools/verify_dex_timing.py audit \
  --species garchomp rampardos rayquaza kyogre metagross --jobs 5 \
  --profile tools/dex_timing/fixtures/selected_no_input.json \
  --output build/dex-timing-five-species
python3 -B tools/verify_dex_timing.py followup \
  tools/dex_timing/fixtures/kyogre_owner_followup.txt --species kyogre \
  --report build/dex-timing-five-species/report.json \
  --rom-sha256 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f \
  --output build/dex-timing-five-species/kyogre
```

Repeat the `followup` command with each other species name. Final artifacts
under `build/dex-timing-five-species/`:

```text
manifest.json
a75579600e3ea944e7b61069c00c39cd0ea3bc79d834d893abb36da8de8bb919
garchomp/followup.json
92dfc1a9cafb032a19a0c8274f080c2c11cdf2b413fa6cb78b2a857745a04616
rampardos/followup.json
003a8a05fe83a7477e55b91da29167fe4adc6f49de7b2da507f13e9aab6e4bf1
rayquaza/followup.json
bf58539a17dd3ed334d81406c848ac66d8d730d536b80d246e62e1970b3d8f73
kyogre/followup.json
2b4f9a11c2ed02e75de493d4e797b8fe26e1d143781fcb73b3be051f97c09e38
metagross/followup.json
4b5da17fc5cb97169b6ea66954dab90d9637bd4b643677b9a66f04390136e813
```
