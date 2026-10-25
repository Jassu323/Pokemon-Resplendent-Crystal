# Selected Dex Scheduling Stall Scope

Date: 2026-10-17. Scoping diagnostics only. The reviewed species-information
prototype, production ROM and player's main save are unchanged. Private source
copies, ROMs, batteries, traces and recordings are under
`build/dex-stall-scope-20261017/`.

## Conclusion

There is a worthwhile, very small Mov improvement: recognize the display-clock
wrap during VBlank, and allow up to twelve existing bounded Mov slices instead
of three, rechecking the existing active-playback admission rules before every
slice. The linked cost is **4 additional decimal ROMX bytes**, with **zero
ROM0, WRAM0, WRAMX, HRAM, SRAM or VRAM allocation**. No new artwork, cache or
generated display data is required.

This changes the Selected Pokemon **Mov tab**, including interactive catch
registration, not the standalone Moves Dex. It does not integrate anything into
the reviewed prototype or production.

The Mov-only candidate is the clearest next implementation. The previously
scoped Info READY cutoff adjustment can optionally accompany it without adding
allocated bytes. That combination improves first Info opening while retaining
the Mov gains, but has a greater timing-budget maintenance obligation. Neither
candidate makes every subsequent button press faster.

All numbers below are relative to the **unchanged reviewed species-information
prototype**, not production's earlier placeholder descriptions. One physical
display frame is **16.742706 ms**, or 70,224 ticks at 4,194,304 Hz. Counts and
averages describe the declared scripted workload, not player probabilities.

## What Actually Stalls

`PokedexSelectedMon_Update` and registration service the portrait before the
lower panel. Preserve that order. Mov then has two independent limits:

1. It performs at most three slices per owner-loop iteration.
2. During authored playback it requires the same display-counter epoch and
   `LY < 64`, even when a slice only clears one RAM row or marks a page ready.

The second rule treats late VBlank, such as LY 152, as if there were almost no
time until the next deadline. In fact, the physical scanline counter is about
to wrap to zero, leaving almost a complete frame until the next VBlank. The
owner commonly reaches Mov at this phase after its normal frame pacing.

The first rule can stop a job at LY 10 despite ample time for more small
slices. The next iteration can then hit the late-VBlank rejection. Together,
these rules turn a few milliseconds of preparation into many frame waits.

The detailed Tangrowth second-page control illustrates this directly:

| Measurement | Reviewed prototype | Mov wrap and batching |
| --- | ---: | ---: |
| Request to complete displayed page | 266.858 ms / 15.939 frames | 32.466 ms / 1.939 frames |
| Mov service invocations before publication | 15 | 1 |
| Actual rendering-step calls | 10 | 10 |
| Time inside those steps, including intervening IRQs/waits | 4.209 ms / 0.251 frames | 4.169 ms / 0.249 frames |

Ten baseline admission observations occur at LY 152. Some individual samples
can roll into LY 0 before the following hardware read; the trace must not
classify rejection solely from the earlier snapshot. The overall record still
shows the repeated no-progress service invocations. Rendering the same ten
steps in one admissible visit removes that scheduling wait, rather than moving
eight frames of rendering work elsewhere.

## The Small Mov Change

Only the private copy of `engine/pokedex/pokedex_moves.asm` changes:

```asm
; Existing slice limit changes from 3 to 12; same instruction length.
    ld b, 12

; After the existing playback/loop-tick check:
    ldh a, [rLY]
    cp LY_VBLANK
    jr nc, .admit
    cp 64
    jr nc, .done
```

The comparison and branch add four emitted bytes. The existing limit still
rejects visible scanlines 64-143 during playback. Reaching twelve slices is a
ceiling, not permission to ignore a changed clock or the next slice's gate.
There is no new unbounded catch-up loop. The same RAM work, badge preparation,
page publication request and bank restoration remain in use.

Portrait preparation, decoding, upload and commit still run first. No authored
duration, cry startup, sample refill, owner-loop pacing, interrupt handler or
VBlank publication window is modified. The hidden lower panel still becomes
visible through its existing atomic transaction.

## Measured Alternatives

Five private links were tested across all 373 base species in both ordinary
Selected and registration: 746 continuous sessions and **14,382 page/tab
operations per link**, including 7,422 Mov requests. Each passes semantic,
rendered-pixel, authored-playback and cry-content checks.

All options below add zero bytes in every memory class except the listed ROMX.

| Private variant | Change | ROMX bytes | Mean Mov improvement | Assessment |
| --- | --- | ---: | ---: | --- |
| `moves-budget` | Mov VBlank wrap only; retain three slices | 4 | 1.034 ms / 0.062 frames | Some large stalls improve, but most ordinary pages retain their old latency. |
| `panel-wrap` | Wrap handling in Mov and Info; retain three Mov slices | 14 | 1.029 ms / 0.061 frames | Reject the Info extension: no first-Info benefit, some additional slower cases. |
| `panel-budget` | Both wrap changes, twelve Mov slices | 14 | 50.738 ms / 3.030 frames | Strong Mov gains, but ten unnecessary bytes compared with Mov-only. |
| **`moves-batch`** | **Mov wrap plus twelve slices; Info unchanged** | **4** | **50.760 ms / 3.032 frames** | **Recommended core improvement.** |
| `moves-ready` | Mov wrap/batching plus Info READY cutoff 84 to 108 | 4 | 50.720 ms / 3.029 frames | Optional first-Info improvement; more budget-maintenance responsibility. |

The earlier hidden-Description printer is not included in these candidates.
Initial wider-visible-cutoff drafts were built before tracing isolated the
wrap/quota problem; they were replaced before native fixture preparation and
are not measured alternatives or evidence for adopting wider cutoffs.

### Mov-Only Distribution

| Request-to-complete-display statistic | Reviewed prototype | `moves-batch` |
| --- | ---: | ---: |
| Median | 98.776 ms / 5.900 frames | 48.546 ms / 2.900 frames |
| 95th percentile | 115.518 ms / 6.900 frames | 65.288 ms / 3.899 frames |
| Maximum | 333.828 ms / 19.939 frames | 81.487 ms / 4.867 frames |

All **7,422 Mov requests improve**, by 16.854-284.452 ms, approximately
1.007-16.989 frames. The median paired improvement is exactly
**50.228 ms / 3 frames**. Category maximums are distribution statistics, not
a claim that their endpoints belong to the same operation.

Matched ordinary Selected examples:

| Operation | Reviewed ms / frames | Mov-only ms / frames | Improvement ms / frames |
| --- | ---: | ---: | ---: |
| Tangrowth, second Mov page | 266.858 / 15.939 | 32.466 / 1.939 | 234.391 / 14.000 |
| Tangrowth, third Mov page | 98.775 / 5.900 | 65.945 / 3.939 | 32.830 / 1.961 |
| Toxicroak, Mov wrap | 267.030 / 15.949 | 32.460 / 1.939 | 234.571 / 14.010 |
| Togekiss, third Mov page | 317.259 / 18.949 | 49.376 / 2.949 | 267.883 / 16.000 |

This is unlike the earlier Tangrowth second/third-page redistribution: both
pages improve here. Every species/owner's complete Mov page-and-wrap sequence
has less total request latency. Mean saving is **405.315 ms / 24.208 frames**;
the smallest saving is **66.644 ms / 3.980 frames**.

As an end-to-end control, all 746 complete scripted page/tab workflows finish
sooner, measured from their first page request to the final complete display.
The Mov-only median saving is **401.825 ms / 24 frames**, with improvements
of **50.228-636.223 ms / 3-38 frames**. These workflows visit every page,
wrap and all six directed tab pairs. They include input/cursor pacing, not
just the sum of measured request latencies. They exclude the test's final
forced wait for authored playback to finish; animation is not accelerated.

An additional **2,984 direct Desc-to-Mov cases** cover all 373 species, both
owners and four input phases without an intervening Info visit. Every case
improves, by **33.485-217.655 ms / 2-13 frames**. Median gain is three frames.
Thus the benefit does not require a different earlier Info history.

## Info And Other Screens

### Info

Info already attempts twelve individually admitted slices. Its preparation
includes separate planning, glyph copy, hardware upload, saved return-panel
recording and READY staging. A page can legitimately span several iterations;
it is not simply using Mov's three-slice rule.

Allowing Info work during late VBlank does not improve first Info in this
catalog and worsens ten original Info sequences by a display-frame-scale
amount. The added admission instructions can themselves change whether a
later stage meets a boundary. Do not generalize the successful Mov change
into a shared replacement scheduler.

There is one measured, narrower Info opportunity: READY only stages already
prepared palettes/OAM. Changing its existing cutoff from LY 84 to 108 costs
zero allocated bytes. With Mov batching also installed:

- 369 of 746 first-Info openings improve; none become slower at that step.
- Maximum first-opening improvement: **33.485 ms / 2 frames**.
- Mean first-opening improvement: **9.494 ms / 0.567 frames**; median zero.
- Across all 3,732 Info requests, mean improvement is
  **3.256 ms / 0.194 frames**; median zero. There are 828 half-frame-scale
  improvements and 179 half-frame-scale slowdowns later in the workflow.
- Across each species/owner's original Info page sequence, mean improvement
  is **15.941 ms / 0.952 frames**, and median improvement is one frame.
  No complete Info sequence worsens by half a frame; the largest small
  increase is **1.702 ms / 0.102 frames**.
- All 7,422 Mov requests still improve. All 746 complete scripted sessions
  finish sooner, with median improvement **418.568 ms / 25 frames** and
  minimum improvement **66.971 ms / 4 frames**.

The existing proof is in `pokedex_description_delay_optimization_scope.md`:
at LY 108, the unchanged 2,048-T guard and 8,182-T finishing reserve leave
6,186 normal-speed CPU T-cycles. The full measured READY path takes at most
4,188 T-cycles. This cutoff must be remeasured if its staging, bank calls,
palette/OAM copies or overhead change. It is not permission to widen heavier
Info states or the actual VBlank publication window.

The combined READY link has a fresh full-catalog sweep, 128 targeted timing
probes and eleven context/isolation contracts. The additional broad Dex,
rapid-input, exit and direct-Mov campaigns in this scope target `moves-batch`,
not this optional combination. Neither is full-game release-qualified.

### Description

Live Description staging already recognizes `LY >= 144` as useful time and
has its own bounded slices. It also uses the reviewed direct page offsets,
so later text pages do not repeatedly scan every preceding page. There is no
corresponding three-slice/VBlank-wrap omission to remove here.

The earlier pending-portrait publication starvation fix remains intact. Do
not remove its real-transfer-versus-deferral distinction or enlarge the
interrupt publication window to pursue a small remaining frame difference.

### Area, Listing, Unown, Search And Type Matchups

They do not use this Selected Mov admission gate. There is no justified
generalization of the four-byte fix into those owners. They retain their
existing preparation and publication policies; this scope changes neither
their assets nor their shared IRQ execution. Their return paths are covered
by the additional Dex campaign described below.

## Residual Timing Tradeoffs

The Mov-only variant leaves all first Info openings and all original
Description/Info page sequences before Mov **exactly unchanged**. After Mov
finishes sooner, later tab returns can meet a different portrait phase:

| Later request category | Mean delta | Largest slower request | Half-frame faster / slower |
| --- | ---: | ---: | ---: |
| Description, 3,228 requests | +0.055 ms / +0.003 frames | +32.942 ms / +1.968 frames | 8 / 17 |
| Info, 3,732 requests | +0.370 ms / +0.022 frames | +34.580 ms / +2.065 frames | 72 / 151 |

For example, later Toxicroak Desc-to-Info changes from
**65.071 ms / 3.887 frames** to **99.651 ms / 5.952 frames**. No extra Info
work is added; that later request now arrives while playback is less advanced.
This remains a real per-button tradeoff and is not waived by correctness tests.

With the optional READY adjustment, later Description maximum slowdown is
**17.682 ms / 1.056 frames**, and Info maximum slowdown is
**34.290 ms / 2.048 frames**. Their respective mean changes are +0.077 ms /
+0.005 frames and -3.256 ms / -0.194 frames. The overall and Mov gains do
not make those individual slower requests disappear.

The present result is nevertheless a substantial net improvement, not the
earlier nearly zero-sum redistribution. Eliminating every phase-sensitive
later wait would require a larger Info/Description scheduling or preparation
redesign, not another blanket quota increase.

## Cost, Complexity And Risk

The Mov-only change is low implementation complexity. Its validation risk is
low/moderate because doing more useful foreground work can change audio-refill,
timer and publication timing even without modifying their routines.

Fresh instruction-counter coverage includes **10,368 page/caught/badge-buffer
cases** across all species. Maximum per-step CPU costs are 3,356 T for
initialization, 7,376 T for clearing/badge preparation and 6,592 T for drawing.
The largest twelve-step payload is 50,628 CPU T, or **6.035 ms / 0.360 frames**
at double speed. This isolated counter fixes STAT to an accessible mode and
does not simulate interrupts, VRAM waits or DMA; it is not a hardware deadline
proof. The targeted native probes, including actual IRQs and VRAM waits, have
a maximum observed whole Mov service duration of **7.196 ms / 0.430 frames**.

There are also **168 isolated admission/bank/stack controls**, spanning LY
0/63/64/143/144/152/153, matched/mismatched loop epochs, display-counter values
0/255, active/quiet playback and three caller-selected WRAM banks. These are
logic controls, not normal-speed native playback qualification.

Dependencies to preserve if implementing:

- Keep animation service first and the existing loop-epoch rejection during
  playback. Do not use a stale epoch as permission for catch-up work.
- Keep the visible-period cutoff and recheck before every slice. Late VBlank
  is a wrap case, not permission to perform work arbitrarily late in visible
  scanout.
- Keep page buffers inactive until the existing atomic publisher accepts
  them. No partial visible page, early OAM reveal or widened IRQ window.
- Keep per-step work bounded, including move-name length and badge preparation.
  Requalify after changing their workload, increasing twelve again, changing
  cry refill, moving the owner loop or altering its CPU-speed contract.
- Current native Selected and registration owners use double speed. This scope
  does not certify a hypothetical future normal-speed streaming owner.

The optional Info READY adjustment is similarly tiny in code/data size but
moderate in maintenance responsibility because it carries an explicit cycle
budget. The ten-byte Info wrap extension is not recommended.

Larger alternatives remain possible, but are not needed for the measured Mov
win: prepare a future page in the background, retain an already-resident Info
atlas, or add a separate panel cache. Earlier estimates are approximately
200-1,000 ROMX bytes and 2-8 WRAMX tag bytes for carefully shared storage, or
about 512 WRAMX bytes for an isolated panel snapshot. Those estimates are not
new linked measurements or promised gains. They introduce cancellation,
invalidation and workspace-ownership work and are not recommended as the first
implementation. WRAM bank 3 is already full.

## Evidence And Reproduction

Protected reviewed ROM SHA-256:
`905f6eab5bd17eaacf5623200eed20c9dd972efa6a65f1b01efc10cc8ad2ddb4`.
Production and the player's battery are also hash-checked unchanged.

All timing comparisons use the retained controlled baseline and fresh
ROM-specific candidate boots/checkpoints, power-on RNG seed `0x17102026`, and
host time `1792195200`. Native donor summaries match exactly. No save state is
transferred between ROM links. Timing includes a fresh publication followed by
a matching complete displayed scanout, not merely a RAM ready flag.

Retained `scope.py` implements the builds, matched native suites, detailed
read-only profiling, CPU controls, media and comparisons. Each variant has a
resource report, protected hashes, full-catalog results and per-request pairs.
The instruction counter is not presented as an emulator. Native sweeps use
CGB E; Type Matchups compatibility checks separately cover all six CGB models.

The initial strict isolation test flags one additional mainline FarCall operand
because `PokedexBadge_Prepare` moves by four bytes. The private contract adapter
verifies that exact target and normalizes only that non-interrupt operand,
alongside the test's pre-existing mainline relocation allowances. All interrupt
bytes remain protected, and its handler-opcode/wrong-target negative controls
still pass. The original unadapted failure logs are retained; no production
test is silently weakened.

The additional Mov-only campaigns include 128 active/settled timing probes,
2,984 direct entry probes, 256 rapid-input/finish/cancel stress cases, 240
registration B/End exit replays, and eleven context/isolation contracts. The
full catalog checks all 122 sampled and 251 synthesized cry species, with
identical cry-content signatures relative to the control and no recorded
audio/portrait underruns or authored animation deadline failures. Counts
overlap and must not be added as unique complete scenarios.

The wider Dex-only campaign and consolidated machine audit are recorded under
the same build directory. Completed Mov-only checks additionally include:

| Dex campaign | Coverage | Result |
| --- | ---: | --- |
| Standard Pokemon Dex, both layouts, search, selected pages, popovers and returns | 4,479 cases | Pass |
| Unown | 136 cases / 2,212 form selections | Pass |
| Standalone Moves Dex filtering, UI, visuals, navigation, transitions, polish and cursor | Seven phases | Pass |
| Type Matchups, selection and return paths | All 18 types on six CGB models | Pass |

The retained `build/dex-stall-scope-20261017/audit.json` validates those reports,
protected artifacts, resource deltas, matched donors, cross-link stable pixel
hashes and cry signatures. All stable pixel hashes match the control for all
five diagnostic links. There are no new automated correctness failures.

The campaigns do not include battle animations, Battle Tower, save/persistence
or general surrounding gameplay. No full-game release
qualification, physical-hardware approval or human listening approval is
claimed. A composite frame was visually inspected; that is not user approval
of every rendered frame or of the native audio.

![Tangrowth Mov timing comparison](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-stall-scope-20261017/media/moves-batch/tangrowth-mov-comparison.mp4)

The silent video is real-rate, aligned before the first Mov request. Each side
requests the next page after its current page completes, making the saved
waiting time visible. Separate unmodified full native WAVs are retained at:

- [Reviewed prototype recording](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-stall-scope-20261017/baseline/review-captures/tangrowth/view2-page2-selected-continuous-q0/audio.wav)
- [Mov diagnostic recording](/Users/jakeadams/Documents/GitHub/Pokemon-Resplendent-Crystal/build/dex-stall-scope-20261017/moves-batch/review-captures/tangrowth/view2-page2-selected-continuous-q0/audio.wav)

The current prototype remains the review/rollback point. Any implementation
requires explicit promotion and a fresh release regression on the final link.
