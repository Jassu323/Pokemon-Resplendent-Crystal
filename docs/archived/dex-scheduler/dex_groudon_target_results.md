# Groudon Decode-Lookahead Investigation

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Recorded 2026-09-20. This is a diagnostic follow-up to the
[integrated scheduler](../../pokedex_animation_scheduler.md), not an installed fix.
Game source, cartridge, symbols, battery saves and original emulator states
were not changed during this investigation.

## Inputs And Reproducibility

The user supplied two complete, mutually consistent observations:

- `Groudon - Save State - Cold Entry.txt`: the original first miss, with SameBoy
  save slot 1 already stopped at that miss.
- `Groudon - Full Suite.txt`: first-publication start, both animation misses,
  and a later manual completion snapshot. Slot 2 contains its starting state.

The slot-2 capture is sufficient for an uninterrupted full replay. Slot 1 is
an independent confirmation of the first failure under a different phase, not
a second measured startup-to-finish trace. Its unreset absolute tick count
must not be interpreted as selection latency. No additional Groudon capture or
video is needed to establish this failure.

```text
ROM: /Applications/SameBoy/Games/pokecrystal.gbc
ROM SHA-256: 3c7f469cfad2f141b8c8c6523401e6db0c368c70dd76b6619fa6c4c8ff32f09e
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
Original s1 SHA-256: 9d3dcbcf8fe8d69c38f8e4ecdfd908a9aec0b95ab8e15c575e32806267bce28e
Original s2 SHA-256: a6f743c4a565c48f22fee2db02b4be8bc7b048a046b444979fdaaabbcd5f656c
```

Local diagnostic copies are retained under the ignored directory
`build/dex-scheduler-groudon/` as `groudon-cold-miss.s1` and `groudon-start.s2`.
Reports, independent-core instruction trace and volatile-memory export are
under `build/dex-scheduler-groudon/replay/`.

`tools/dex_timing/probes/current_state.py` imports the actual current-link
registers, mainline/interrupt stack, volatile memory, VRAM and timer state.
Unlike the original ten-species integrated suite, this input is not relocated
onto a rebuilt stack. The start is inside a VBlank interrupt that interrupted
sampled-cry decoding; that real return chain is preserved.

The captured display sleep has 244 cycles remaining at LY 145, rather than
the older fixture's 300. The adapter derives the starting phase from that
captured LCD state using the previously calibrated six-T boundary offset;
it does not reuse the older export header's fixed 606-T phase. Groudon's
resulting model phase is 662 T. Unsupported hardware envelopes are rejected.

## Exact Baseline Agreement

The unchanged-ROM host replay matches the independent SameBoy core at all
**861,581 non-HALT instruction starts**, including registers and elapsed
T-cycles, through the complete sequence.

Both supplied miss snapshots also agree exactly with the host: AF/BC/DE/HL,
SP/PC, elapsed T-cycles, LY/mode, 27 animation-state bytes, 139 diagnostic bytes,
six sampled-playback HRAM bytes and eight WRAM4 cache bytes. There is no
remaining timing discrepancy to investigate before diagnosing these misses.

| Event (1-based) | Pose ID | Due interval | Miss elapsed T | Uploaded / needed | Decoded extent / required extent |
| --- | ---: | ---: | ---: | ---: | ---: |
| 13 | 6 | 43 | 2,962,984 | 29 / 31 | 175 / 177 |
| 14 | 7 | 47 | 3,255,372 | 16 / 33 | 187 / 204 |

Intervals are measured from the first animation publication. Dictionary extents
include the 49 base tiles; Groudon has 204 total tiles, or a 155-tile tail.
The first miss lacks sources 175-176. The second lacks sources 187-203.
The original cold-entry slot-1 miss also has 29/31 uploaded and extent 175.

Both incomplete stages are published on their authored intervals. Thus the
full main/hold/idle timeline still lasts **211 intervals**, but two publications
have incorrect slot/map contents. Exact duration alone is not a pass: the
intentional underrun path preserves the timeline instead of concealing missing
work by stretching a hold.

Audio is healthy in this run. Cache depths at the misses are 116 and 125 blocks;
playback completes naturally at 7,296,204 elapsed T with zero blocks remaining.
No audited GDMA or interrupt hardware writes fall outside VBlank. The latest
GDMA completion is 3,182 T into the 4,560-T VBlank. Four optional finishing
uploads are admitted, with a smallest observed finishing margin of 17,538 T.

The final manual debugger break is later than actual completion. It is not
animation duration. Runtime cleanup completes at 14,833,544 elapsed T; the
authored final publication occurs at interval 211.

## Why It Fails

The inherited `set_timeline_targets` generator in `tools/pokemon_animation.c`
looks only at the current event and its next two successors. At runtime,
`Pokedex_AnimationDictionaryBelowTarget` and `Pokedex_ChooseAnimationWork`
stop dictionary decoding once the loaded extent reaches that target.
Operationally the target is a decoding ceiling, not merely a readiness minimum.

Groudon exposes the weakness of counting nearby events instead of considering
the later workload:

1. Startup already has 145 tiles decoded: 49 base plus the unchanged 96-tile
   tail lead. Its early repeated poses 3/4 need no additional decoding.
2. Early lookahead targets remain only 115. Multiple owner iterations choose
   no dictionary work despite unused future decoding opportunities.
3. The first post-publication dictionary chunk does not execute until interval
   30, when preparing event 10 raises the target to 146.
4. Preparing event 11 raises the target to 177 at interval 33; event 12 raises
   it to 204 at interval 37. Heavy new poses are due at intervals 43 and 47.
5. Stage construction, gathering, upload waits and audio now share that short
   window with the deferred decoding. The dictionary finishes only at interval
   53, after both first-use deadlines.

For example, event 13's stage construction spans interval 40, LY 15-98, and
takes 37,792 T including interruptions. Its 20-tile upload crosses into interval
41; the following nine-tile prefix upload crosses into interval 42. The last
two needed source tiles still await a six-tile dictionary chunk. Merely finding
space for another upload cannot help when its source bytes do not exist yet.

The upload-ready-first policy and the finishing gate are behaving as written.
The finishing gate requires the entire remaining source range to be decoded;
it correctly refuses a partial-source finish. The failure is not evidence of
insufficient VRAM, a broken display clock, unsafe bank selection, or a fundamental
hardware inability to perform Groudon's total workload.

## Host-Only Earlier-Decoding Control

A separate counterfactual retains the captured RAM and first-event target, but
raises subsequent Groudon targets to its full required extent, 204. This changes
17 existing target bytes in the host's private ROM image. It emits no modified
cartridge and does not change any CPU instructions or payload lengths.

Unchanged: 96-tail startup lead, first stage, six-tile decode quota, 20-tile
upload quota, two VRAM slots, all stage/gather/queue costs, 32-block audio prefill,
runtime audio service, 8,192-T finishing reserve and authored deadlines.

| Measurement | Current targets | Earlier-decoding control |
| --- | ---: | ---: |
| Startup decoded extent | 145 | 145 |
| Post-start dictionary chunks | 10 | 10 |
| Decoder instruction cost, excluding interrupts | 74,348 T | 74,348 T |
| Dictionary fully decoded by interval | 53 | 14 |
| Animation misses | 2 | 0 |
| Incorrect slot/map publications | 2 / 2 | 0 / 0 |
| Full authored duration | 211 intervals | 211 intervals |
| Sampled cry stop | Natural | Natural |
| Latest GDMA end within VBlank | 3,182 T | 3,182 T |
| Minimum observed finishing margin | 17,538 T | 17,538 T |

This demonstrates usable earlier production opportunities with the existing
architecture. It does not make decompression free, increase per-call quotas,
or preload the full dictionary before reveal. The same ten chunks run earlier
while their stage-upload work is not competing for the regular work choice.

The exact comparison covers the unchanged baseline. The counterfactual is a
host-only feasibility test of this one captured starting phase, not independent
core or live-game signoff for a modified build, and not an all-species guarantee.

The subsequent [15-species target regression](dex_target_regression_results.md)
extends this initial result: both policies now match the independent core at
their nominal starts, and all 105 earlier-decoding nominal/phase runs pass.
It includes the user's new Milotic, Drapion, Rhyperior and Yanmega starting
states. This strengthens the evidence without installing a game correction.

## Fix Direction And Remaining Gates

Improve the decoding horizon while retaining the current scheduler and finishing
guards. Candidate directions include later-future high-water requirements or
bounded opportunistic decoding when current stage work is already satisfied.
Avoid an arbitrary species exception or another blanket startup increase.

Separate startup's latency bound from the later steady-state horizon. In
particular, changing the first timeline target to the entire dictionary can
accidentally turn runtime lookahead into extra synchronous startup work. The
successful control deliberately leaves that first target and captured startup
alone. It requires no new VRAM and adds no metadata records or runtime memory.

Before installing a general correction:

1. Choose a generator/runtime rule that expresses the larger useful horizon,
   including loop successors and the initial warm/cold preparation contract.
2. Replay Groudon across phases and rerun the original sampled/synthesized set
   with that exact rule. More early decoding can still change audio and owner
   timing, so one successful counterfactual is not sufficient signoff.
3. Continue the remaining live expansion cases: Drapion, Yanmega, Rhyperior and
   Milotic. Capture a full sequence/start state only if another failure occurs.
4. Recheck cold/warm entry, internal paging and cancellation after a new build.

No further Groudon capture is requested for the current diagnosis. Keep the
game unchanged until the target-policy correction has been reviewed.

## Reproduction

The independent core helper is the previously built diagnostic executable.
Run from the repository root, with the unchanged current ROM and symbols:

```sh
PYTHONPATH=tools python3 -B -m dex_timing.probes.current_state \
  --rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --state build/dex-scheduler-groudon/groudon-start.s2 \
  --species groudon \
  --core build/dex-scheduler-integrated/final-core-check/sameboy-linked-replay \
  --output build/dex-scheduler-groudon/replay \
  --eager-tail-control
```

The probe hashes its inputs, refuses the control if the baseline instruction
comparison is not exact, and verifies that those inputs remain unchanged.
Its reports retain the per-operation work ledger, every publication/slot/map
audit, hardware-write audit, cry stop, and private target-byte changes.

The existing reference-ROM host regression suite also passes: **197 tests**
in 201.096 seconds. This is separate from the new exact current-link Groudon
replay and the host-only counterfactual above.
