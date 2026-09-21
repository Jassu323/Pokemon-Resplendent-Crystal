# Selected Dex End-to-End Captures: 2026-09-20

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

## Verdict

The user's **Weavile slot 9** and **Dusknoir slot 8** captures are complete.
The normal linked host replay matches all four measured checkpoints exactly:
first-publication entry, first animation miss, sampled-cry stop, and stable
owner completion. Elapsed T-cycles, CPU registers, IME, LY/mode, IF/IE,
DIV/TIMA/TMA/TAC, animation state, trace bytes, and audio/cache bytes agree.
The independent SameBoy core also matches the captured PPU sleeping/pixel
position at each checkpoint.

The host and independent core match at every executed non-HALT instruction
start, including elapsed T, ROM bank, PC, AF, BC, DE, HL and SP:

- Weavile: **337,521** instruction starts.
- Dusknoir: **714,485** instruction starts.
- Combined: **1,052,006**, with no differing instruction or timing offset.

No hardware-timing rule or species-specific correction was needed for these
new inputs. The changes in this pass are capture parsing, additional read-only
snapshot fields, portable initial-memory fixtures, regression assertions, and
documentation. No game ASM, ROM, runtime instrumentation, sampled-cry settings,
CPU speed, WRAM/HRAM/VRAM allocation, save file or source emulator state changed.
The game was not rebuilt.

## Measured Checkpoints

All elapsed times below begin at the initial `77:5ea5` breakpoint, where the
debugger's first `ticks` command resets its counter. The large value printed by
that initial command is not elapsed time for this experiment. Later checkpoints
use `ticks keep` without resetting the origin.

| Species | Checkpoint | Captured T | Host T | Difference |
|---|---|---:|---:|---:|
| Weavile | First animation miss | 181,132 | 181,132 | 0 |
| Weavile | Cry stop | 2,572,872 | 2,572,872 | 0 |
| Weavile | Stable completion | 5,493,520 | 5,493,520 | 0 |
| Dusknoir | First animation miss | 508,736 | 508,736 | 0 |
| Dusknoir | Cry stop | 2,816,412 | 2,816,412 | 0 |
| Dusknoir | Stable completion | 12,240,048 | 12,240,048 | 0 |

The stable completion stop is after publication/cry cleanup. It is not the
animation's authored duration or selection-to-reveal latency.

## Weavile

The dictionary is already complete at the initial publication. All six
underflow calls occur with zero dictionary tiles left to decode:

| Event | Frame | Uploaded / required | Audio cache at miss |
|---|---:|---:|---:|
| 2 | 2 | 0 / 18 | 29 |
| 3 | 3 | 20 / 27 | 29 |
| 4 | 4 | 20 / 24 | 25 |
| 6 | 2 | 0 / 18 | 25 |
| 8 | 4 | 0 / 24 | 15 |
| 9 | 5 | 20 / 25 | 17 |

There are four late publications, at events 4, 6, 8 and 10. The largest is two
display intervals late. Underflow calls and late publications are different
signals, not additive counts of corrupted frames. Some calls occur before a
publication can still complete in its due display interval; conversely,
publication can be late without a corresponding new underflow-counter call.

Its cry completes naturally with zero blocks remaining. This rules out missing
dictionary data or an empty audio cache as the direct explanation for these
animation misses. Stage construction, gathering, upload, queue readiness and
publication timing under the current service-call schedule remain the problem.
It does not demonstrate that removing audio work would have no timing benefit.

The previous synthetic continuation had six misses but three late publications
and a maximum lateness of one interval. These are different initial runs, not
a regression in the host model: the new run preserves the actual initial
memory, timer phase and music state, and agrees exactly with the user and core.
The older partial capture's early-LY/mode qualification is retained as history;
it is not retroactively explained by this different, fully specified run.

## Dusknoir

The first miss has **20 of 32 stage tiles uploaded**, with **102 dictionary
tiles still undecoded** and 36 blocks in the audio cache. The complete run
executes 17 dictionary decode calls. There are **24 underflow calls** and
**nine late publications**, with maximum lateness of two display intervals.

The audio stop is a genuine underrun: cache count is zero and **333 blocks
remain unplayed** (`$014d`). This occurs 2,816,412 T after the initial publication,
about 0.672 seconds into this measured segment. The stop interrupts an active
`SampledCry_FillRollingCache` call, so the final refill was underway but had not
delivered data soon enough.

The captured final state has eight cached blocks and 325 compressed blocks
remaining. That is not recovery: the already-running refill finishes its batch
after playback stops. The stop-time dump, not that later cache count, establishes
the underrun. The old synthetic continuation's predicted stop with 325 blocks
left was from a different input and is superseded by **333** for this actual run.

The final authored publication still occurs at interval 174: 107 main-animation
intervals, 18 base-picture hold intervals, and 49 idle intervals. Intermediate
misses remain despite the correct final duration. Later misses also occur after
the dictionary is complete, so decode backlog alone cannot explain the failure.
Once the cry has stopped, subsequent work no longer bears a healthy sampled
cry's continued load; those later timings cannot prove simultaneous feasibility.

Representative costs from this actual-state replay:

| Operation | Calls | Instruction T | Elapsed T | Largest elapsed call |
|---|---:|---:|---:|---:|
| Dictionary chunk | 17 | 160,100 | 225,828 | 20,336 |
| Stage build | 27 | 621,036 | 877,460 | 40,812 |
| Tile gather | 21 | 206,592 | 311,092 | 34,040 |
| HDMA helper | 15 | 68,456 | 115,356 | 17,640 |
| Audio refill | 25 | 426,956 | 631,684 | 25,616 |

Elapsed costs include interruptions/waits; instruction costs exclude interrupt
instructions. Operation spans may nest, so categories must not be summed as an
exclusive CPU budget. The HDMA helper's instruction cost includes polling and
setup, not just the hardware transfer itself. These are measured path costs,
not universal worst-case guarantees.

## Reproducibility And Limits

Raw states are read-only inputs and are not checked into the repository.
Portable `weavile_initial_volatile.json` and `dusknoir_initial_volatile.json`
retain their initial physical WRAM/VRAM, CPU/IO values and call stacks. They
exclude cartridge ROM/SRAM, emulator PPU/APU internals and later state. The text
captures are separate expected-output fixtures, never injected during replay.

An additional independent-core control reconstructed the supported PPU phase
using only the initial-memory export. It matched all four checkpoints and PPU
positions from the raw-state runs. Thus the host does not need to reload the
user's raw state or borrow later core results to reproduce these failures.

Pinned identities:

```text
ROM: 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
SYM: 1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
Weavile s9: a4ff2cb8b3ab736802a109830277a3cf62e10cda7d1a3f729d5706eae04574fd
Dusknoir s8: e8dd78db216ca76c9233ac75bd9800c5bfe0b4b432b20538b6c6920338094397
SameBoy source: 213a12ce93d66b105a113debd9396306066a7cfc
```

After building the host core as described in
[the full-replay guide](dex_full_replay_results.md#identity-and-reproduction):

```sh
env PYTHONPATH=tools python3 -B -m dex_timing.end_to_end \
  --species weavile --capture tools/dex_timing/fixtures/weavile_end_to_end.txt \
  --state /Applications/SameBoy/Games/pokecrystal.s9 \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --output build/dex-host-full-weavile-end-to-end.json
env PYTHONPATH=tools python3 -B -m dex_timing.end_to_end \
  --species dusknoir --capture tools/dex_timing/fixtures/dusknoir_end_to_end.txt \
  --state /Applications/SameBoy/Games/pokecrystal.s8 \
  --core /private/tmp/dex_core_full_replay --sameboy-source ../SameBoy \
  --output build/dex-host-full-dusknoir-end-to-end.json
```

The ordinary full runner now uses actual initial fixtures for Luxray, Weavile
and Dusknoir. All nine cases were rerun: **5,400,595 matching instruction starts**,
with all six internal checkpoints matching the reference core. The other six
species remain explicitly synthetic extensions of partial captures. The 141
host tests pass, including direct four-stop comparisons from the portable
Weavile/Dusknoir fixtures without opening the emulator or raw states.

Validation is specific to the captured normal-speed CGB-E, no-input Selected
path and pinned build. It is not a general hardware certification, visual/audio
waveform comparison, phase sweep, or validation of the aggregate quota model.
No A-button/cancel intervention, startup latency, party Stats Screen, New Dex
Entry, or battle behavior is covered.

## Next Decision

No additional capture or video is needed to close this calibration step. The
model now reproduces the observed failures with actual state for three useful
cases: Luxray's large stages, Weavile's short deadlines without decode work,
and Dusknoir's concurrent tail decoding/audio starvation.

Use this unchanged baseline to evaluate the proposed shared-display-clock
scheduler and independently tracked completed work. Budget the full dependency
chain, including safe early stage preparation, gathering, phase-sensitive
upload/queue/publication, and audio service. Compare every publication and
audio-cache deadline, not merely the final duration. Then broaden initial-phase
coverage before claiming a guaranteed work budget or changing game code.

This evidence does not yet prove a particular replacement meets every deadline
at normal speed, nor that extra VRAM/ROM or a larger startup lead is necessary.
The runtime fix still requires a separate reviewed implementation.
