# New Dex Entry Testing

Current next-owner audit, updated 2026-09-21. No New Dex Entry scheduling fix
or new ROM instrumentation is included in this procedure.

## Checkpoint And Setup

The addresses below apply to accepted ROM SHA-256
`412527bdecc0c55c90a63b1d268ee7f7812788649e6936035dfd86a437e9dff7`.
Verify the matching ROM/symbols using the [validation guide](dex_scheduler_validation.md#build-identity);
re-resolve the labels after any relink.

Selected-page playback has passed all-species cold/internal testing, but New
Dex Entry uses a different owner. The temporary Route 29/30 encounters and
dormant A/B branches are removed; existing Selected instrumentation and active
Listing warming remain. Their retained RAM must not be interpreted as this
owner's diagnostics.

Use a backed-up test save and normal Continue. Before any separately approved
save replacement, close the ROM so SameBoy cannot overwrite it from memory.
Do not load an older save state that restores pre-edit flags. The earlier
all-seen/Unown correction, backup identities and completed Seviper investigation
are preserved in the [historical setup record](archived/dex-scheduler/dex_seviper_new_entry_testing.md).
There is no need to repeat those edits for an already valid save.

## What Is And Is Not Shared

`_NewPokedexEntry` loads `GetAnimatedFrontpic` before playback, then initializes
`ANIM_MON_MENU`. `NewPokedexEntry.WaitPressAorB_AnimateFrontpic` advances
`SetUpPokeAnim` and `HDMATransferTilemapToWRAMBank3` in its own foreground loop.
It continues checking text input and can advance description pages before the
animation completes.

It does not use Selected Mon's streaming slots, hardware-deadline publication,
miss counter, quiet owner or telemetry. There is no corresponding legacy
animation-deadline-miss breakpoint. Slow animation can therefore occur without
ever hitting `$a0:$6805`. Its dictionary is preloaded, so an animation issue
here is not automatically a streaming tile underrun.

The sampled cry player and its `$0:$3cb3` empty-cache breakpoint are shared.
The six-byte HRAM/eight-byte WRAMX-4 dumps are valid; the Selected Mon debug
overlay is not. `$04:$dbe0` is audio data, not the old removed audio probe.

Keep the reusable host timing model and its calibration/auditing. Its current
Selected Mon replays do not certify this owner. If deeper timing data is needed,
extend it with this loop and actual legacy publication boundaries; do not
pretend its frames pass through `Pokedex_VBlankAnimationFrontpicMap`.

## Initial Suite

Start with three uninterrupted registrations each for Dusknoir and Metagross,
plus a synthesized control such as Caterpie. Add one each of Luxray, Weavile
and Groudon once those establish the baseline. Test early A-to-description-2
and B/exit separately, with species, timing and audio ownership recorded.
Seviper's Selected script-fix retest has already passed; it is not a prerequisite
for this separate owner timing suite.

Registration requires the species to be **uncaught**, not unseen. A valid all-seen
save is suitable for currently uncaught species. Dusknoir and Luxray remain
caught; a later separately authorized, backed-up test-save edit is needed to
clear those specific caught flags. The current checkpoint has no encounter overrides. This procedure does not
authorize a save edit or restore old testing encounters. Establish an uncaught save/state per
case so three captures test registration three times rather than only battle.

## Boundary Captures Without New ROM Instrumentation

First arm only the owner entry point, so the preceding battle cry cannot be
confused with registration playback:

```text
breakpoint $3e:$57f0
```

At that stop, capture registers/backtrace and the audio dump below. Then remove
that breakpoint and arm the registration wait-loop entry:

```text
breakpoint $3e:$5871
```

At its first hit, run `ticks` to reset the cycle counter, capture the legacy
state below, and remove this breakpoint. This is before the registration's
animation/cry sequence starts, so it includes startup overhead. Set:

```text
breakpoint $0:$3cb3
breakpoint $34:$42c9
breakpoint $34:$4171
```

- `$34:$42c9` marks an animation script reaching `endanim`. For `ANIM_MON_MENU`,
  expect one main-script and then one idle-script stop. The state/pointer dump
  distinguishes them; do not reset `ticks` between these stops.
- `$34:$4171` is the final `PokeAnim_Finish` setup command. Capture its state and
  `ticks keep`. It marks software completion before the caller's final transfer,
  not the exact LCD publication of the final pixels.
- `$0:$3cb3` is a genuine empty-cache hit. Capture immediately, then continue;
  animation may keep running after the cry stops.

Use this at each stop:

```text
registers
backtrace
ticks keep
lcd
x/41 $2:$d168
x/1 $0:$cf64
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff9b]
print/x [$ff4f]
print/x [$ff70]
print/x [$ffff]
```

After the final animation stop, continue without pressing a button until the
cry also finishes, then manually break for a final audio dump. A cry ending
later than the animation is not by itself a failure. Do not use a breakpoint
on the shared stop function, which also catches normal completion.

Record one uninterrupted normal-speed run per baseline species separately
from debugger captures, with the UI/input overlay visible. These software
boundary captures reveal coarse phase costs and audio failure, while video
establishes visible frame durations. Exact per-frame auditing would then add
legacy frame-ID/publication timestamps and cache/service timing with an
owner-safe buffer or host trace. No new ROM telemetry is required for the
initial triage, and none was added in this checkpoint.

## After The Baseline

Compare the legacy script boundaries, shared sampled-cry state and uninterrupted
video before proposing runtime changes. If per-frame timing remains ambiguous,
add an owner-safe host trace or separately approved instrumentation, not reads
of Selected-only counters. Keep the reusable model/auditing sources.

Instrumentation cleanup and Listing warming removal remain separate later
work. Exclude raw captures, saves/states, compiled runners and copied cartridges
from commits; use ignored `build/` for generated output.
