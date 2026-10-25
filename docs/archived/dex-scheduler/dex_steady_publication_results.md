# Selected Dex Steady-Display Publication And Recovery

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Date: 2026-09-20. Follow-up to
[the publication-budget investigation](dex_publication_budget_results.md).

**Follow-up:** [Garchomp finishing and additional actual starts](dex_garchomp_finishing_results.md)
replaces the fixed eight-tile heuristic with a costed complete-chain experiment.
It clears all nine nominal actual-start sequences, including Garchomp, but retains
Garchomp phase/cost margin counterexamples. The new states also replace the six
partial-input qualifications for those newer runs. The results below retain their
original policies, inputs and evidence limits.

## Result

The host counterfactual now has a bounded publication path for both on-time and
already-late frames, under an explicit steady Selected-display ownership
contract. Its worst-case critical-transfer margin is **853 normal-speed T-cycles**
at the latest admitted scanline, not the previous effectively zero margin.

The three actual-initial-memory continuations (Weavile, Luxray, Dusknoir), 192
timer-phase runs, and 144 dispatch/owner-guard cost runs all complete with correct
intermediate maps and slot bytes, no missed/late frames, and complete sampled
cries. Deliberately late interrupt-entry controls defer safely and retain the
recorded one-interval lateness; they do not erase it or stretch the timeline.

Broader partial-capture continuations pass for Bastiodon, Rampardos, Rayquaza,
Kyogre, and Metagross. **Garchomp still misses event 5, frame 4: 20/30 tiles
uploaded, dictionary completely decoded.** This occurs in the nominal run and
all 16 timer-phase controls. It is a remaining work-completion failure, not an
unsafe publication or an audio failure. The successful three-species candidate
must not be promoted to a general scheduler on this evidence alone.

No game code, ROM, assets, memory allocation, sampled-cry parameters, or save
states were changed. These remain costed host experiments, not a test ROM.

## What Changed In The Host Experiment

The previous candidate already held empty OAM after it had been cleared and
published. The new experiment also holds the existing hardware viewport during
input-free Selected animation playback:

- `SCX = 5`, `SCY = 0`, `WY = 0`, `WX = 167` in these inputs.
- The four software shadows must continue to equal those hardware values.
- The Selected owner must remain active, with no owner transition or competing
  BG, palette, tile-transfer, or tileset-animation requests.
- The already-published OAM must remain empty and OAM suppression must remain
  enabled, as required by the previous experiment.

`RecoveryReplay.check_owner_contract` fails closed if those assumptions change.
They are host assertions, **not free runtime comparisons of all these fields**.
An eventual runtime implementation would explicitly enter a steady Selected
VBlank route and leave it before any operation needing normal display updates.
Transitions, A-button description changes, internal paging, returning to the
Listing, Area, and other future subpages cannot simply inherit this route.

The normal VBlank handler's four redundant viewport copies cost 96 T. The host
skips that exact, byte-checked linked block and charges a hypothetical 64-T owner
route instead. The cost sweep also tests 256 T, which is more expensive than the
original four copies. The benefit is therefore not merely a 32-T speed saving:
those hardware writes no longer have to follow map-publication bookkeeping
before line 0. All bookkeeping, including the first-publication deadline anchor,
still executes. No instrumentation block was silently removed.

Publication now requires a sampled `144 <= LY < 149`. The lower comparison is
charged as `CP 144 / JR C`: 16 T on admission and 20 T on rejection. The existing
upper comparison retains its linked instruction timing with operand 149.
In particular, `LY = 0` on physical line 153 or after VBlank must not pass an
upper-bound-only check.

The prior progress-based `tail` policy is otherwise unchanged: it retains
display-clock deadlines, independent completed work, early eligible production,
the real queue-boundary ownership check, the elapsed-VBlank wait guard, reordered
outer-loop audio service, and at most one additional ready suffix of eight tiles
per owner iteration. That last limit is still a feasibility heuristic, not a
complete-chain admission model.

## Publication Bound

The linked-code enumerator retains 144 combinations of OAM policy, base versus
animated frame, initial/publication counters, on-time/late bookkeeping, byte
carries, and maximum-lateness updates. Both GDMA stalls are included. All other
display requests are idle, as required by the ownership contract.

The costs below start at the original upper-comparison boundary, four T after
the LY sample. New costs include the added lower-bound comparison.

| Quiet-OAM publication | Previous critical completion | Steady viewport critical completion |
| --- | ---: | ---: |
| On time | 2,276 T | 1,408 T |
| Already late | 2,416 T | 1,424 T |

The old critical endpoint was a later viewport register store. The new endpoint
is completion of the second map GDMA. CPU bookkeeping may continue afterward;
that is not itself a VRAM-access violation. Sound execution is still timed and
sampled-cry completion remains an independent pass condition.

Using the conservative last possible LY=148 sample, including its four-T age:

```text
latest comparison entry = 5 * 456 - 1 + 4 = 2,283 T into VBlank
latest critical finish  = 2,283 + 1,424   = 3,707 T
remaining margin        = 4,560 - 3,707   =   853 T
```

That is about 0.203 ms or 1.87 scanlines at normal speed. This is a bound for the
specified quiet transaction, not a universal budget for arbitrary VBlank work.
Adding another transfer, changing the viewport contract, retaining OAM DMA, or
changing the linked map transaction requires a new bound. Normal animation
timing success also does not establish correct input/transition handoff.

## Actual-State And Phase Results

All three nominal inputs are the existing hash-bound initial volatile-memory
fixtures. Later expected state is never injected. Synthetic phase controls alter
the initial sample timer phase and retain independently latched interrupt flags.

| Species | Nominal misses / late / cry underruns | 64 phase runs | 48 cost runs |
| --- | --- | --- | --- |
| Weavile | 0 / 0 / 0 | All pass | All pass |
| Luxray | 0 / 0 / 0 | All pass | All pass |
| Dusknoir | 0 / 0 / 0 | All pass | All pass |

All these runs also have zero duplicate publications, incorrect slot bytes,
incorrect tilemap/attrmap cells, competing transfers, and out-of-VBlank critical
hardware operations. The full authored sequence boundaries remain 78, 92, and
174 intervals respectively. Dusknoir's 174 includes its 107-interval main
sequence, 18-interval base hold, and 49-interval idle sequence.

The phase sweep uses 64..12,664 T in 200-T increments. The cost sweep uses
256/1,024/2,048-T dispatch costs, 64/256-T viewport guards, and eight phases
64..11,264 T in 1,600-T increments. These are 336 executions, with some overlapping
parameter settings, not 336 newly captured live sessions.

Worst observed map-GDMA completion in the 192 phase runs was 3,370 T into VBlank,
leaving 1,190 T. The analytical bound above is stricter than the observed maximum.

## Deliberate Late-Entry Recovery

Fifteen additional runs inject a single masked delay immediately before a later
due publication's LY read, once per species and test phase. They test admission
and recovery, not the probability of such an interrupt delay in ordinary play.
They retain both interrupt requests and elapsed display time.

| Forced pre-read phase in VBlank coordinates | Result in each species |
| --- | --- |
| 2,260 T | Admitted; correct on-time map; transfer ends at 3,682 T |
| 2,276 T | Rejected; correct map published one interval late |
| 2,284 T | Rejected; correct map published one interval late |
| 4,108 T | Physical line 153 reports LY=0; rejected; one interval late |
| 4,564 T | Visible line 0; rejected; one interval late |

The timing includes the actual LY-read bus cycle after the injected boundary,
so 2,276 T does not mean the comparison samples LY=148. In the 12 deferred cases,
the next VBlank publishes the prepared map once. None causes a later unfinished
frame, duplicate publication, incorrect intermediate map, unsafe GDMA, or cry
underrun. The delayed event remains marked late. Total timeline holds are not
silently extended to make the recovery look on time.

## Broader Species And Initial-State Qualifications

The other six species still lack complete starting-memory captures. Their prior
text captures omit physical VRAM, slot-map buffers, and the queued owner maps.
Using zeros for those bytes produces false initial rendering failures, including
a reused Bastiodon frame. Such failures are not newly produced bad uploads.

For this explicitly synthetic control, the constructor now supplies canonical
asset bytes only for frames that the captured resident IDs already claim exist,
their cached maps, and the already-queued initial seven-row map. It checks every
resident source against the captured decoded-prefix length. It does **not**
advance dictionary decoding, fill a future slot, change scheduler flags/counts,
or modify later checkpoints. Initial viewport values match the earlier reference
core's explicit setup. Post-cry music is silent, as in the previous partial
continuations. These are stronger functional controls, not equivalent to actual
complete user-state evidence.

| Partial-capture continuation | Nominal result | 16 phase controls |
| --- | --- | --- |
| Bastiodon | Pass | All pass |
| Garchomp | One unfinished frame; incorrect fallback map | Same failure in all 16 |
| Rampardos | Pass | All pass |
| Rayquaza | Pass | All pass |
| Kyogre | Pass | All pass |
| Metagross | Pass | All pass |

All 102 broader executions (six nominal plus 96 phase controls) have natural cry
completion, no late map publication, and no critical transfer outside VBlank.
Garchomp illustrates why on-time publication alone is not success: its deliberate
underflow map is published on time, but it is the wrong animation image.

### Garchomp's Remaining Failure

In the nominal continuation, event 5 needs animation frame 4 at interval 29:

- All 140 dictionary tiles are decoded. No decode is outstanding.
- Stage preparation takes 37,136 T, ending in interval 27 at about LY 92.
- The first upload call takes 41,684 T including gather, interrupts, and HDMA.
  It crosses into interval 28 and returns at about LY 35 with 20/30 tiles ready.
- Ten tiles remain. The inherited suffix heuristic permits only eight, so it
  declines additional work. The normal commit path then judges the upcoming
  deadline and constructs the visible underflow map.
- The cry cache still contains about 80 blocks. Neither an empty audio cache nor
  a missing dictionary source explains this miss.

This does not prove that an unbounded second upload is safe, or even that any
ten-tile upload always fits. It identifies precisely where a species-independent
complete-chain budget is needed. The workload includes gathering the remainder,
HDMA launch/waits, upload completion, queue construction, and enough audio-service
reserve. Merely changing eight to ten would replace one empirical cutoff with
another and would not establish the required guarantee.

## Next Investigation And Runtime Gate

1. Keep this publication/ownership contract as a candidate, not an implemented
   fix. Any runtime design must explicitly restore normal display ownership for
   A/B input, paging, exit, and other subpages. Do not globally disable viewport
   writes or OAM updates.
2. Replace the fixed extra-eight-tile feasibility rule in a separate host
   experiment with a remaining-work admission test. Garchomp event 5 is the first
   concrete acceptance case, alongside all prior successful cases.
3. Charge the complete operation chain and audio reserve. If that cannot fit,
   test earlier stage construction or a smaller regular upload before changing
   preload or adding another cache. Keep failures visible and independently
   validate every map and slot.
4. Once the candidate survives broader cost/phase controls, implement a narrow
   runtime trial and repeat real captures. Actual complete initial states for the
   six partial species would strengthen final signoff, but no additional user
   capture is needed to investigate the current host counterexample.

This turn consumed zero cartridge ROM0/ROMX, WRAM0/WRAMX, HRAM, or VRAM bytes.
It retained 96 startup tail tiles, both existing frame slots, six-tile decode
chunks, the normal 20-tile upload cap, 32 audio-prefill blocks, eight-block active
refills, and normal CPU speed.

## Reproduction And Verification

New runner: `tools/dex_timing/recovery_experiment.py`. The branch-cost enumerator
in `budget_experiment.py` accepts `hold_viewport=True`; its original default
behavior and the calibrated baseline tests are unchanged.

```sh
python3 -B -m tools.dex_timing.recovery_experiment \
  --output build/dex-timing-steady-broader --jobs 8
python3 -B -m tools.dex_timing.recovery_experiment \
  --output build/dex-timing-steady-final-recovery \
  --species weavile luxray dusknoir \
  --forced-entry-phase 2260 2276 2284 4108 4564 --jobs 8
python3 -B tools/test_dex_timing.py
```

Final generated reports are under these ignored directories:

- `build/dex-timing-steady-broader`: nine nominal runs and branch bounds.
- `build/dex-timing-steady-final-dense`: 192 actual-input timer-phase controls.
- `build/dex-timing-steady-costs`: 144 actual-input cost controls.
- `build/dex-timing-steady-broad-phases`: 96 qualified partial-input controls.
- `build/dex-timing-steady-final-recovery`: 15 deliberately delayed-entry controls.

Earlier `steady-controls`, `steady-dense`, and `steady-recovery` reports are
development runs, not the final report set. In particular, the first partial
controls lacked canonical initial graphics and retain their failures for context.

All reports bind their inputs, ROM/symbols, and host sources by SHA-256. Tests:
**173 passing**, including unchanged exact baseline checkpoints, ownership
contract rejection, line-153 rejection, worst-branch margin, correct recovery,
partial-resident assumptions, and preservation of Garchomp's unresolved failure.

Repository and SameBoy ROM both remain:
`7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`.
Symbols remain:
`1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5`.
