# Selected Scheduler Validation And Test Guide

Updated 2026-10-01. This is the current instrumentation-free guide.
See the [implementation reference](pokedex_animation_scheduler.md) for the
runtime contract and the [historical validation record](archived/dex-scheduler/dex_scheduler_validation_history.md)
for earlier ROM hashes, experiments and acceptance stages. Statements about
older temporary encounters or unimplemented candidates belong to that archive.

## Build Identity

Test the normal root `pokecrystal.gbc`, not an earlier A/B cartridge.

```text
ROM SHA-256: cb2eabc2db0df6678c3a3a99fa7b9f19f7044418f30fc1d4237a87493d6d2748
SYM SHA-256: c83daf53a86ead8e6e127f42bcd4290d17f97bc2c349d901e9a928040a293358
MAP SHA-256: 7211eacfbc39b6cdc0161a3deacf640e375e1530a09dad5b7868bb6edd459860
RGBDS: v1.0.1
SameBoy core: 213a12ce93d66b105a113debd9396306066a7cfc
Hardware: CGB-E, normal CPU speed
```

This link includes the later-event full-dictionary targets, restored Route 29/30
encounters, Seviper's finite repeat correction, Description UI/category fixes,
Listing restoration, local cry cancellation, atomic internal reveal and
buffered footprint/type icons with portrait-only masking.
Startup remains 96 animation tail tiles and 32 sampled-cry blocks. Listing
warming remains. Runtime telemetry is removed; the clean-link
[cleanup report](dex_instrumentation_cleanup.md) records the cost remeasurement,
all-species cold/paging passes and New Entry sweeps at that earlier checkpoint.
The [internal handoff acceptance](pokedex_internal_transition_investigation.md#implemented-internal-handoff)
records the earlier final link; [buffered icon acceptance](pokedex_internal_transition_investigation.md#buffered-icons-in-production)
records the current link's regression and remaining limits. The generated
historical outputs were cleaned; their source/parameter recipes remain in
the [build catalog](archived/build-history.md).

Boot through normal Continue using a battery save, not an older emulator state.
Old states can retain incompatible return addresses or prepared work even when
some symbols match. Preserved replay fixtures are separately identified inputs,
not substitutes for fresh live entry tests. No save, ROM or state in a user's
emulator installation is overwritten by the host acceptance runner.

## Acceptance And Limits

| Evidence | Result |
| --- | --- |
| Normal-input cold Listing | All 373 New Dex species qualify as cold and complete animation/cry playback |
| Published animation | 5,849 correct publications; 47,259 exact authored hardware intervals |
| Sampled audio | All 122 sampled cries complete naturally; zero cache-empty hits |
| Synthesized audio | All 251 controls reach sound-channel completion |
| Animation misses | Zero |
| Logical B-return | 373 pass; palette restoration is not audited by this check |
| Initial static portrait | 373 pass; Mew/Drapion category corrections retained |
| Automated settled internal paging | 373 clean handoffs with exact full animation/cry completion |
| Automated active paging/B-return | 1,492 owner handoffs pass with no outgoing cache-empty or retained-cry faults |
| Live internal paging | User tested the entire New Dex with no uninterrupted-playback misses |
| Live presentation controls | Chikorita, Bayleef, Meganium, Dusknoir, Rampardos and Luxray show no visible animation defects |

The current aggregate cold suite passes every static-reveal check, including
Drapion. The [cold Listing results](dex_cold_listing_results.md)
preserve the earlier failing checkpoint and category correction; do not treat
that historical failure as an expected current outcome or suppress its check.
Unown A and
finite Seviper passed both manual cold/internal checks and the automated suite.

Earlier settled-playback evidence comprises 126 compiled-target replays across
18 species, including six synthetic timer-phase controls per species. The 18
nominal independent SameBoy comparisons agreed at 11,514,944 instruction starts.
Minimum observed finishing margin was 12,702 T above the required 8,192-T
reserve; latest publication GDMA ended at 3,382 T of the 4,560-T VBlank.
These are the recorded target-correction build's results, not new runs after
every subsequent source edit. See [compiled integration](archived/dex-scheduler/dex_target_regression_results.md#compiled-integration).

The all-species suite covers real entry and exact full main/hold/idle timelines,
not just the absence of miss breakpoints. Dusknoir's total is 107 main + 18 hold
+ 49 idle = 174 intervals; its main target remains 107. Seviper now has 21 events
totaling 76 + 18 + 28 = 122 intervals. All 399 asset/form timelines terminate
structurally; the normal-input suite tests 373 species, not every Unown form.

Warm entry, every possible rapid-input phase, A-button Description transactions,
Area/Search/alternate-order transitions, subjective waveform quality and other
display owners are not certified by these passes. The reproduced B-return,
category, cry-owner and internal reveal issues now have focused fixes and
regressions; rapid-axis input and active Description-page corruption remain in
the [backlog](pokedex_selected_bug_backlog.md). Manual review of the integrated
reveal and buffered icons passed. New Dex Entry, Party Stats and battles retain
separate scheduling paths.

## Regression Suite After Runtime Changes

No additional playback run is required for documentation-only cleanup.
Use this suite when changing the scheduler, its assets, warming or instrumentation.
Keep ordinary audio enabled at normal emulation speed. Do not press A to change
description text during uninterrupted animation tests.

### Entry Routes And Stress Cases

For Weavile, Luxray, Dusknoir, Garchomp and Groudon, run each route three times:

1. Cold Listing: move from another selection and press A immediately after the
   target appears, without deliberately waiting for warming.
2. Internal paging: enter Selected on another species, then page to the target.

Allow the full main/hold/idle sequence and cry to finish. Look for missing tiles,
font characters, flicker, frozen poses, stretched holds, incomplete final frames,
early cry cutoff and unexpected UI pauses. Warm entry is deliberately outside
the current acceptance; it remains implemented, pending separate removal.

Broader coverage, once per route:

| Cases | Purpose |
| --- | --- |
| Bastiodon, Rampardos, Drapion | Tail requirements beyond the startup lead and multi-batch slot replacement |
| Rayquaza, Kyogre, Metagross | Different upload/decode patterns and longer sampled playback |
| Luxray, Rhyperior | Large changed-cell frames and resident reuse |
| Yanmega | Many events and short holds |
| Milotic | Long animation spanning display-counter wrap |
| Exeggcute, Mewtwo | Active synthesized cries and one-interval events |
| Spheal, Sealeo, Snorlax | Unused dictionary-tail and fully preloaded controls |
| Caterpie, Cyndaquil, Rattata, Bayleef | Earlier stray-pixel and 5x5/6x6 padding regressions |
| Unown A, Seviper | Valid form setup and finite repeat completion |

Hitmonchan is an optional long synthesized control. The all-species cold runner
is the scalable regression route; there is no need to manually repeat all 373
cold selections. Category overflow was separate from animation and is now fixed;
report any new static-reveal defect rather than treating it as expected.

### Ownership And Cancellation

1. B-cancel during early, middle and late playback; move the Listing cursor and
   open another species immediately. Repeat after internal paging.
2. Hold Up/Down through several Selected entries, then stop on a stress case
   and let it complete. Repeat with distinct taps.
3. Move the footer cursor without activating a different page while animation
   plays. Check that cursor work does not disrupt the frontpic.
4. Enter Area, return to Description and let the animation finish; then return
   to Listing. Check the frontpic, shell, viewport and restored Listing icons.
5. Leave the Dex to the overworld, reopen it, scroll both ways and select again.
6. Separately press A to toggle Description text during and after animation.
   The pre-existing corruption is **not claimed fixed**; report new lockups or
   ownership-restoration failures separately from that known issue.

Check Listing minisprites, palette restoration, caught markers and shell
alignment, but distinguish known backlog symptoms from new regressions. A brief
ordinary battle/Party Stats smoke check is useful for the shared VBlank guard;
those owners are not expected to acquire the new Dex timing behavior.

### Recording

Use uninterrupted normal-speed video with the input overlay when comparing
startup, paging or animation durations. Debugger pauses invalidate video timing.
Record any visible defect even when counters remain zero. Identify species,
entry route, held/tapped inputs and whether the screen was visible or in a
transition. Known bugs remain deferred, not implicitly fixed by this suite.

## SameBoy Debugging

Addresses below apply to the `cb2eabc2...` ROM above. Verify the cartridge before
using them. For a fresh link, resolve the labels in `pokecrystal.sym` again.

### Animation Miss

```text
breakpoint $a0:$666a
```

This is `Pokedex_AnimationMiss`, starting with the call to the existing visible
underflow fallback. There is no runtime counter now. It should not fire during
uninterrupted settled playback; the host also checks exact publication timing.

At any hit, capture:

```text
registers
backtrace
ticks keep
lcd
x/27 $0:$c72e
x/3 $0:$c758
x/49 $0:$cb9c
x/49 $0:$cbfe
x/49 $0:$cc60
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff9b]
print/x [$ff9e]
print/x [$ffd8]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
print/x [$ffff]
x/1 $0:$ffc6
```

Record species, route, whether the cursor had warmed it, buttons pressed during
playback, and hit number. Preserve a new-build save state at a reproducible hit.
After continuing to completion, gather the state/audio dumps again.

`$c758-$c75a` are loop tick, last work tick and scheduler control. Control
bit 0 means deferred audio is due; bit 1 means a finish was used this iteration.
The retired `$c73b-$c73c` storage is reserved, not a miss counter. There is no
trace-ring dump. Successful completion is judged by production state and host
publication/audio auditing, not a zero diagnostic count.

### First Publication / New Replay State

Only needed if another full replay is requested:

```text
breakpoint $77:$6093
```

This is `Pokedex_VBlankAnimationFrontpicMap.deadline_reached`. Its first bytes
are `f0 70 f5 f0 4f f5 3e 03`, starting `LDH a, [rSVBK & $ff]`.
Capture registers, backtrace, `ticks`, `lcd`, and a new-build starting save state
before continuing. Do not use older `$77:$5ea5`/`$77:$5edb`/`$77:$6014` addresses for this link.

### Suspected Sampled-Cry Underrun

Prefer the dedicated cache-empty branch for this build:

```text
breakpoint $0:$3cb3
```

The first instruction is `POP af`; expected six bytes are
`f1 e0 70 c3 63 00`. This path runs only when playback blocks remain but the
decoded cache is empty. Normal completion and intentional cancellation do not
pass through it. Outgoing exhaustion during the native Selected owner change
is no longer expected after the local cancellation fix; see `DEX-CRY-04` in
the [bug backlog](pokedex_selected_bug_backlog.md). At a hit,
also capture `x/1 $0:$c727` to distinguish active playback from species staging.

The broader alternative below catches any stop with remaining blocks:

```text
breakpoint $0:$0063 if [$fff2] + [$fff3]
```

Capture registers/backtrace, `x/8 $4:$dff4`, `x/6 $0:$ffee`, `ticks keep`, `lcd`
and the animation state dumps. A deliberate species/page/cancel operation
can also stop a cry early, so that context is essential. Normal sampled
completion has zero remaining blocks. Earlier `$3d1a`/`$3d36` instrumentation
addresses do not apply to this build.

## Reproducing Host Checks

Run these maintained checks from the repository root. Building requires the
normal project toolchain; the host tests use Python 3. Current linked contracts
need the matching root ROM, symbols and generated assets, but no private save
states or ignored integration script.

```sh
make -j8 pokecrystal.gbc
make verify-dex-animations
python3 -B tools/test_dex_scheduler.py
python3 -B tools/test_dex_cold_listing.py
python3 -B tools/test_dex_target_regression.py
PYTHONPATH=tools python3 -B -m dex_timing.finish_bounds \
  --output build/dex-scheduler-integrated/finish-bounds.json
```

At the binary-identical A/B cleanup these three test files passed 11 + 14 + 11
tests (36 total). The finishing checker independently covers 216,000 admission
inequalities. Unit/structural success is not a replacement for timed playback.

For normal-input emulation, use the maintained
[cold Listing procedure](dex_cold_listing_results.md#reproduce). It requires a
local SameBoy checkout, C compiler, boot ROM and suitably prepared battery save.
Those external inputs are explicit prerequisites, not repository fixtures.

Historical capture/model tests require their frozen reference ROM, generated
assets and, for actual-state/core replay, matching local save-state exports.
The old `build/dex-target-integration-20260920/verify_integration.py` is a local
one-off evidence script, not a supported fresh-checkout test command. Its results
remain in the archive; do not commit copied ROMs/saves to make it portable.
See the [host tool guide](dex_timing_model.md) for current versus historical
entry points. Raw reports and traces belong under the ignored root `build/`.

## Cleanup Status

The accepted instrumentation checkpoint has now been cleaned. Runtime logging,
trace buffers and miss/publication counters are removed; production scheduler
state and visible failure paths remain. The [cleanup report](dex_instrumentation_cleanup.md)
contains exact changes, resource totals, tests and current New Entry breakpoints.

Route 29/30 encounters, Joey's party and Master Ball behavior remain ordinary.
The 96-tail startup, 32-block cry prefill and Listing warming remain unchanged.
Root build output stays ignored. Reusable host observers and historical evidence
remain, with frozen-input requirements explicit.

Listing warming removal, other owners and backlog fixes remain separate work.
Staging, committing and pushing remain the user's action.
