# Selected Dex Headroom And Synthesized Cry Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Date: 2026-09-20. Follow-up to the
[queue-construction investigation](dex_queue_construction_results.md).

## Scope

The requested work is host-only: increase the previously measured 556-T
finishing margin and test synthesized cries before costing the concrete game
scheduler. No game ASM, cartridge, symbols, emulator state, SRAM, animation
script, preload, cry setting, CPU speed, or runtime allocation was changed.
The game was not rebuilt. Existing dirty game files predate this investigation.

The candidate still uses the previously documented display-clock scheduler,
independent work completion, early preparation under slot ownership, and
deadline-controlled publication. Faster copies alone are not a proposed fix for
the unmodified game's scheduler. These tests include the whole earlier host
candidate, not just a replacement copy routine.

## Additional Headroom

### A Fixed Copy Loop, Not Another Data Format

`Pokedex_GatherReadyAnimationTiles` copies each ready dictionary tile into the
WRAM upload payload with a counted 16-byte loop. The source and destination
increment identically for all 16 bytes. Emit those copy instructions directly
and remove the repeated decrement/branch; retain the per-tile readiness checks,
20-tile cap, source list, upload offset, source-bank selection, and payload.

The original copy body costs 644 T per tile, including its B initialization.
The proposed body costs 392 T and preserves B=0 on exit: **252 T saved per tile**.
Both variants execute actual instructions in the host counter. No cycle
discount or instantaneous host-side memory copy is substituted.

The private probe relocates the full helper to verified empty space at
`$a0:$7800` and keeps a JP at its original entry. That extra **16 T per call is
included** in all reported results, although an eventual in-place replacement
would not need it. Existing operation hooks therefore still observe the entry.
The four queue-copy CALL redirects from the previous experiment remain present.

| Gather/upload prefix | Queue-only candidate | Faster-gather candidate | Saving |
| --- | ---: | ---: | ---: |
| 7 ready tiles | 7,788 T | 6,040 T | 1,748 T |
| 9 ready tiles | 9,660 T | 7,408 T | 2,252 T |
| 10 ready tiles | 10,596 T | 8,092 T | 2,504 T |
| 20 ready tiles | 19,956 T | 14,932 T | 5,024 T |

The last saving is about 1.198 ms of raw normal-speed CPU work. It does not
accelerate HDMA or change how many bytes enter VRAM. Arriving earlier also avoids
some interrupts and launch-window deferrals, so elapsed improvement is not
necessarily equal to the raw instruction saving.

For the ten-tile **complete finishing chain**, including upload, wait allowance,
queue, wrapper and interrupt bounds, the active-audio bound falls from
**41,940 to 36,768 T**. The queue remains 9,380 T. No existing interrupt or
hardware-wait allowance was removed to achieve this result.

### Preserve The Gain As Margin

The faster prefix allows larger finishing jobs to fit. With no explicit reserve,
one newly accepted Rampardos 13-tile finish has only 140 T above its conservative
bound. All 144 coarse sampled-phase runs pass, but taking every newly eligible
job would reproduce the original concern about narrow margins elsewhere.

The host probe therefore also tests a minimum reserve:

```text
available visible time = (143 - sampled LY) * 456 T
admit only if complete-chain bound + minimum reserve <= available visible time
```

The existing launch-line limit, audio-runway check, pending-interrupt drain,
source readiness, slot ownership and publication deadline checks remain.
This discards the rest of the current scanline and does not assume access to a
sub-scanline hardware clock. The reserve is not subtracted from the measured
work, inserted as a delay, or added to an animation hold. It declines optional
early finishing work when the complete chain would leave insufficient slack.

The 2,048-T reserve passes all 144 sampled coarse-phase cases. The 4,096-T
reserve passes the broader matrix below. Its smallest accepted conservative
margin is **4,144 T** (Bastiodon, actual phase, a cost-control case), about
0.988 ms. This is the finishing window's margin, not a claim that every operation
in every display interval has that much spare time.

### Garchomp Comparison

Using the same high-overhead allowances and 64 phase points as before:

| Configuration | Minimum accepted finishing margin |
| --- | ---: |
| Previous queue-copy candidate | 556 T, about 0.133 ms |
| Faster gather, 4,096-T reserve | 12,120 T, about 2.890 ms |
| Faster gather, 8,192-T reserve | 12,120 T, about 2.890 ms |

The 64 phases are 64 through 12,664 T in 200-T increments. The complete authored
110-interval sequence, intermediate maps, tile-slot contents and natural sampled
cry completion all pass. The reserve does not manufacture the larger margin:
Garchomp already gains it from the earlier, less expensive work.

## Synthesized Cry Validation

### Actual Exeggcute State, Not Silent Audio

The user-supplied slot-01 starting state already contains Exeggcute's active
synthesized cry. It was preserved during the previous import but excluded from
the sampled-timer-only constructor. This investigation now supports its actual
timer registers: TMA=0, TAC low bits=4, a 262,144-T timer period, and the captured
DIV/TIMA phase. It does not pretend a sampled cry is running or switch off the
timer to make the case cheaper.

The host initially matched all instruction start times but differed in several
sound-register readback values. Inspection of SameBoy's `Core/apu.c` confirmed:

- Unused/read-only bits return their hardware masks, not the last written byte.
- NR52 channel-status bits are read-only; writing a masked NR52 value does not
  itself turn those channels off.
- DAC disabling and trigger writes determine channel-active status in this path.

`sound_registers.py` models only those CPU-visible controls. It rejects frequency
sweep, enabled length clocks, power transitions and active wave-RAM reads rather
than guessing at unmodeled APU phase. No waveform, envelope or analogue sound
simulation is claimed. This is enough for the captured Exeggcute path and was
checked against the real core, rather than justified solely from expected output.

The unchanged-ROM full continuation now matches independent SameBoy at
**385,586/385,586 non-HALT instruction starts**, including elapsed T, ROM bank,
PC, AF, BC, DE, HL and SP. All checkpoint timing and state comparisons also match.
Only initial volatile memory is supplied to the host; later states are not fed
back into it. Actual-state baseline coverage now totals **5,993,723** matching
instruction starts across the nine sampled species and Exeggcute.

### What The Candidate Preserves

For the core-validated baseline and the candidate controls:

- Full authored Selected timeline: **113 intervals**, including base hold/idle.
- Sound engine: **114 updates**, exactly one per display interval from the
  initial publication through the final publication; no skipped update interval.
- All **949 sound-register writes** occur in the same ordered address/value
  sequence, including background music work.
- Cry channels 6, 5 and 8 finish in intervals **47, 54 and 55**, respectively,
  exactly as in the baseline. The active flags are cleared by the sound engine.
- No animation miss, late publication, wrong map, wrong tile slot, unsafe
  transfer or duplicate publication occurs.

The sound engine is real work here: the baseline's longest observed VBlank
handler is 22,856 T including sound work after its critical display writes.
Treating synth playback as an idle/silent path would be inappropriate. The full
linked replay executes that work and its consequences for the owner's return.
This handler duration is not the critical VRAM transaction duration; the latter
is audited separately.

The 4,096-T reserve controls cover 16 phases across Exeggcute's actual slow timer
period, both the earlier queue-only and new gather variants, and 12 independent
dispatch/viewport/finishing-guard cost combinations for the new variant. All
**44 synth controls** preserve the properties above. This demonstrates the active
synth path for Exeggcute, not all synthesized cries or rendered audio fidelity.

## Completed 4,096-T Matrix

The final, current-source reports are:

| Matrix | Runs | Result |
| --- | ---: | --- |
| Nine sampled species: 16 phases each, Garchomp expanded to 64 | 192 | Pass |
| Ten species, including Exeggcute: 12 overhead combinations each | 120 | Pass |
| Exeggcute: 16 slow-timer phases, two copy variants | 32 | Pass |
| **Total** | **344** | **No failures** |

The total includes 16 queue-only synth controls; 328 runs use the new gather.
These are counterfactual continuations, not 344 independent live captures.
The phase matrix uses dispatch=2,048 T, viewport guard=256 T and finishing
admission=1,024 T. The cost matrix varies those over 256/1,024/2,048,
64/256, and 256/1,024 T, respectively. These remain allowances, not yet exact
instruction costs for an implemented scheduler.

All runs check every authored publication, source tile payload, published
map/attributes, completion, sampled-cry stop reason, duplicate publication,
finishing bound, audio-runway assumption, and physical transfer window. The
latest critical GDMA completion in this matrix is 3,362 T into the 4,560-T
VBlank. The previously established 853-T worst-case publication-bound margin is
unchanged and separate from the finishing margins discussed above.

Dusknoir's main sequence still has its **107-interval** target. The model's
174-interval full continuation also includes the 18-interval base hold and
49-interval idle sequence; it is not a changed main-animation target.

## Completed 8,192-T Matrix And Recommendation

The larger reserve also passes the full phase/cost follow-up:

| Matrix | Runs | Result |
| --- | ---: | --- |
| Nine sampled species: 16 phases each, Garchomp expanded to 64 | 192 | Pass |
| Ten species, including Exeggcute: 12 overhead combinations each | 120 | Pass |
| Exeggcute: 16 slow-timer phases, faster-gather variant | 16 | Pass |
| **Total** | **328** | **No failures** |

All use the faster-gather candidate. The phase and overhead values are the same
as the 4,096-T matrix. The smallest accepted conservative finishing margin is
**8,232 T**, about **1.963 ms**: Rayquaza event 26, 11 remaining tiles, sampled
LY=53, in two actual-phase cost controls. Garchomp's 64-phase high-overhead
minimum remains **12,120 T**, at event 2 with a 12,064-T initial timer delay.
The latest critical GDMA end remains 3,362 T into VBlank. The separate 853-T
conservative publication-bound margin is not enlarged by this work.

All 28 Exeggcute cases here (16 phases plus 12 cost controls) preserve its
113-interval timeline, 114 consecutive sound updates, 949-write sequence, and
channel-completion intervals. Combined with the prior matrix, that is **672
successful final continuations**, including **72 synth controls**. Each report's
host-source hashes match the current implementation.

An additional nominal comparison at **16,384 T** fails Garchomp with one
recorded miss, despite the faster copies; the other eight sampled nominal starts
pass. Rejecting too much useful early work can lose a deadline. That negative
control is retained rather than suggesting that an arbitrarily large reserve
is necessarily safer.

**Recommended next pre-flight candidate:** retain the preceding queue-copy and
display-clock policy, add the fixed 16-byte gather-copy optimization, and require
an 8,192-T minimum finishing reserve. This gains meaningful margin without
changing startup lead, audio refill settings, authored holds, or VRAM allocation.
It remains a tested host policy with explicit scheduler-cost allowances, not a
proof for every possible timer phase, synth species, input state, or future
instruction implementation.

## Implementation Costing Is Still Deferred

This investigation supports retaining the current two-slot/WRAM dictionary
model and making bounded work cheaper. It does not require another animation
metadata format, more startup tiles, additional VRAM slots, a larger audio
prefill, or double CPU speed to pass these cases.

The private helper manifests retain exact bytes and counts for reproducibility,
but the complete game implementation's ROM0/ROMX/WRAM/HRAM bill remains a
separate next step, as requested. In particular, the dispatch, ownership and
admission logic still needs real code, counted branch paths and a real link.

Remaining gates: normal runtime verification of the concrete candidate;
A/B/input cancellation, Description paging, internal species paging and listing
handoffs; other synth cries whose APU access patterns differ; cold-start behavior
before this first-publication fixture; any other playback owner or cry pitch.
These results cover settled, no-input Selected playback at normal CPU speed.
No new user capture is needed to cost this candidate, but broader synth/owner
signoff must not be inferred from Exeggcute alone.

## Artifacts And Reproduction

```text
ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
Symbols: 1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
Private queue+gather image: 4d614f96645d12efe4f2857ee87f5a92021a4024107c6921ead856ce3357780a
Reference core: f4724e266a7165d683ef643828333eb5136048e161bf08484f176832700c27f6
SameBoy source: 213a12ce93d66b105a113debd9396306066a7cfc
```

Generated, ignored outputs:

- `build/dex-timing-synth-baseline`: actual-state/core full calibration.
- `build/dex-timing-headroom-final`: 192 final sampled-phase continuations.
- `build/dex-timing-gather-costs`: 120 overhead continuations.
- `build/dex-timing-synth-phases`: 32 synth-phase controls.
- `build/dex-timing-gather-phases`, `-gather-reserve`, `-gather-garchomp-fine`:
  earlier zero-reserve, 2,048/4,096-reserve and Garchomp exploratory runs.
- `build/dex-timing-headroom-large-reserve`: the 8,192/16,384 nominal comparison,
  including the deliberately retained failure.
- `build/dex-timing-headroom-reserve8k`: 328 final phase/cost continuations with
  the recommended 8,192-T finishing reserve.

Example reproduction from the repository root:

```sh
PYTHONPATH=tools python3 -B -m dex_timing.probes.import_starting_states \
  --states /Applications/SameBoy/Games --core /private/tmp/dex_core_full_replay \
  --sameboy-source /Users/jakeadams/Documents/GitHub/SameBoy \
  --output build/dex-timing-synth-baseline --fixtures tools/dex_timing/fixtures \
  --species exeggcute --jobs 1
PYTHONPATH=tools python3 -B -m dex_timing.queue_experiment \
  --mode tile-unrolled --dispatch-t 2048 --viewport-guard-t 256 \
  --finish-guard-t 1024 --finish-margin-t 8192 --jobs 8 \
  --timer-delay-t 64 864 1664 2464 3264 4064 4864 5664 6464 7264 8064 8864 9664 10464 11264 12064 \
  --output build/dex-timing-headroom-coarse-recheck
PYTHONPATH=tools python3 -B -m unittest tools.test_dex_timing
```

Verification: **197 regression tests pass**. The new gather equivalence
tests cover 1,283 paired prefix/offset/readiness/early-return fixtures, preserving
payload bytes, write order, registers, flags, banks and memory. Other tests pin
the private image boundary, counted chain costs, reserve rejection, Exeggcute's
core instruction fingerprint, fail-closed sound controls, and candidate sound
update/write sequences. All 672 final 4,096/8,192-T reports match the current
host-source hashes. Repository and emulator ROM hashes and the symbol hash
remain unchanged.
