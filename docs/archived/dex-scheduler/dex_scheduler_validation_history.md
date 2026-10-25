# Selected Scheduler Validation And Test Guide

> Historical pre-consolidation record, preserved 2026-09-21.
> Build identities and dated measurements below remain evidence; old "current"
> statements and commands are not current checkout instructions. See the
> [archive index](README.md) and [maintained guide](../../dex_scheduler_validation.md).

Updated 2026-09-21. Implementation: [Selected scheduler](../../pokedex_animation_scheduler.md).

## Build Identity

Test the normal root `pokecrystal.gbc`, not an earlier A/B cartridge.

### Latest Acceptance: All-Species Cold Entry

The current ROM, including encounter cleanup and Seviper's finite repeat fix,
has SHA-256 `412527bdecc0c55c90a63b1d268ee7f7812788649e6936035dfd86a437e9dff7`.
Its symbol hash is `95a72958f693330d4c472a4e2c65196072879f63ee843829510b9c7bdcba905f`.
The user's complete internal-paging pass and explicit Unown/Seviper cold-entry
retests pass. The new normal-input headless suite passes animation/audio playback
for all 373 New Dex species from confirmed-cold Listing selection, including 122 natural sampled-cry
completions, 5,849 correct publications and 47,259 exact authored intervals.
There were no animation/audio misses or logical B-return failures. The additional
static-reveal check passes 372 species and catches Drapion's category overflow
writing `n` into its portrait before animation (`DEX-UI-02`). The aggregate suite
therefore intentionally reports one failure; no game fix was made.

See [cold Listing methodology, artifacts and limitations](../../dex_cold_listing_results.md).
No game or save changes were made for that suite. The older build identities
below are retained to identify the earlier replay evidence. Both general miss
breakpoints remain unchanged in this latest ROM.

### Earlier Target-Correction Build

```text
ROM SHA-256: e3846b92741e15056e5886dd3d4dfd39782dcfda10cfac21e0edfc02c33901ee
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
```

The generator now leaves event 1 unchanged and sets every later event's target
to the species' full dictionary extent. Relative to the `22e039...` capture
build below, exactly 2,954 existing target bytes across 387 of 399 assets change,
plus the cartridge global checksum. The complete symbol and map files are
byte-identical. There is no additional ROM0/ROMX, WRAM0/WRAMX, HRAM or VRAM
allocation, and startup remains 96 tail tiles with a 32-block sampled prefill.
The encounter test blocks are unchanged. The emulator's installed ROM and saves
were not replaced automatically.

Both miss breakpoints below remain valid, with their instruction bytes verified
against this rebuilt ROM. Current acceptance is **cold entry and internal
paging only**; warm entry is omitted at the user's request. Warming has not yet
been removed from the game.

### Earlier Build Identities

The scheduler baseline used for the automated results below is:

```text
ROM SHA-256: 55490ff6e8c09a27955a1aa92c35ccbb4993851d4baea6ef1620632f0a58cba6
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
RGBDS:       v1.0.1
SameBoy core: 213a12ce93d66b105a113debd9396306066a7cfc
```

The previous temporary Route 30 encounter-test build, used by the 15-species
target regression, is:

```text
ROM SHA-256: 3c7f469cfad2f141b8c8c6523401e6db0c368c70dd76b6619fa6c4c8ff32f09e
```

Its symbols and executable code are unchanged from the scheduler baseline;
only 59 ROM bytes differ, confined to Route 30 encounters and the cartridge
checksum. The animation-miss (`$a0:$6805`) and sampled-cache-empty
(`$00:$3cb3`) breakpoints therefore remain valid. Route 30 has Groudon,
Drapion, Yanmega, Rhyperior and Milotic at 20% each, levels 3-4, in every time
slot. The normal 10% grass encounter frequency is unchanged. These encounter
edits are explicitly marked **temporary: revert before commit**.

The earlier temporary Route 29/30 capture build was:

```text
ROM SHA-256: 22e039075004ee7444c9b948b9ae502374c2c38dbd196bed4120867207006c83
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
```

Relative to the previous Route 30 build, exactly 67 ROM bytes differ, confined
to Route 29 encounter slots and the cartridge checksum. All executable code,
timelines, symbols, and Route 30 encounters remain identical. The proposed
earlier-decoding target correction is **not installed** in this capture build.

Route 29 now has Spheal (34%), Sealeo (33%), and Snorlax (33%) at levels 2-3
in every time slot, with the normal 10% encounter frequency and seven slots.
This is a second explicitly marked **temporary: revert before commit** block.
These are the three assets whose complete dictionaries extend beyond the
tiles referenced by their Selected timelines. Spheal can expose 45 additional
post-start decoded tiles under the proposed policy; Sealeo and Snorlax already
fit completely within startup and serve as controls.

For the additional host regression, capture one cold-entry starting save state
per species at the first `$77:$5edb` hit, with `registers`, `backtrace`, `ticks`,
and `lcd`, and record the save-slot mapping. Preserve the state before
continuing. No video or full sequence capture is needed initially. All debug
addresses below also remain valid for the current target-only rebuild.
These inputs have now been received in slots 7 (Spheal), 8 (Sealeo), and 9
(Snorlax), and their complete baseline/candidate replays pass; see the
[unused-tail follow-up](dex_target_regression_results.md#unused-dictionary-tail-follow-up).

The implementation retains current instrumentation and Listing warming, uses
the global 96-tail-tile startup target, and keeps sampled-cry prefill at 32.
No emulator cartridge, battery save or save state was overwritten automatically.

The complete pre-change ROM, symbols, map and source archive are preserved
locally under `build/dex-scheduler-reference-20260920/`. This is an ignored
reference artifact, not a commit. Its ROM hash is
`7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`.

**Boot the new ROM using a battery save, not an old emulator save state.** Old
states can contain return addresses from an older link or pending work prepared
under older targets. Even when addresses are unchanged, use a fresh entry for
live acceptance; the calibrated archived starts are a separate replay fixture.

## Automated Results

### Compiled Target Correction

The current `e3846b...` ROM passes **126 full replays across 18 species**:
one preserved start and six timer-phase controls each. All have zero animation
misses, late/duplicate publications, incorrect tiles/maps, sampled underruns,
or unsafe VBlank writes/transfers. All authored main/hold/idle durations are
preserved. The 18 nominal independent SameBoy comparisons agree at
**11,514,944 instruction starts**; their traces are also byte-identical to the
previous private target-policy prototype traces. Every phase-control timing
outcome matches its previous prototype result.

All 399 generated structures and the 11 linked scheduler contract tests pass,
including a new all-assets check that preserves the first target and requires
the full extent on later events. The 11 target-regression unit tests pass.
The 197-test historical reference-model suite also passes unchanged.
Minimum observed finishing margin remains 12,702 T, above the 8,192-T reserve;
latest publication GDMA ends at 3,382 T within the 4,560-T VBlank.

This is settled playback validation from preserved starts, not an automated
measurement of cold startup, interactive paging, or every species. The live
results below supplement it without proving every owner/input path. Detailed results and local replay artifacts are
recorded in [target correction integration](dex_target_regression_results.md#compiled-integration).

### Original Cohesive Scheduler Baseline

The final game links successfully. All 399 timeline structures and all 1,722
non-base plans pass asset validation. Comparing the reference and current links
finds no moved existing RAM symbols. All frame plans, timelines and dictionary
bytes used by the relocated test inputs are unchanged.

Ten linked contract tests cover 1,024 work-choice combinations, 600 finishing
LY/audio boundaries, counter wrap, unsupported hardware, short audio tails,
complete ready finishing remainders, ownership acquisition/release, cancellation, outer-loop waiting, duplicate queue
rejection and publication timing. The table checker additionally compares
216,000 combinations against the conservative admission inequalities.

### Full Linked Replays

These runs execute the new game instructions. No hypothetical producer policy,
free queue operation or guessed guard cost replaces runtime work. Independent
SameBoy comparison agrees at **6,017,550 non-HALT instruction starts**, including
registers and elapsed timing, across the ten baseline inputs.

| Pokemon | Expected full intervals | Linked result | Optional finishes | Smallest observed finish margin (T) |
| --- | ---: | ---: | ---: | ---: |
| Weavile | 78 | 78 | 5 | 26,718 |
| Luxray | 92 | 92 | 1 | 36,686 |
| Dusknoir | 174 | 174 | 7 | 14,978 |
| Garchomp | 110 | 110 | 4 | 17,278 |
| Bastiodon | 205 | 205 | 7 | 12,718 |
| Rampardos | 139 | 139 | 3 | 13,174 |
| Rayquaza | 175 | 175 | 13 | 18,766 |
| Kyogre | 113 | 113 | 7 | 13,186 |
| Metagross | 228 | 228 | 0 | Not needed |
| Exeggcute, active synthesized cry | 113 | 113 | 2 | 19,978 |

Full means main animation, authored base hold and idle sequence. For Dusknoir,
this is **107 main + 18 hold + 49 idle = 174** intervals. Its 107-interval main
target is not being replaced by a 174-interval main animation.

All ten have zero missed/late/duplicate publications, incorrect slot tiles,
incorrect map cells, sampled underruns or publication transfers outside VBlank.

An additional six initial timer-phase controls per species, at 64, 2,048, 4,096,
6,400, 9,600 and 12,800 T until the next timer event, give **60 further passing
host replays**. These are synthetic phase variations, not additional captures.
Their smallest observed finish margin is 12,702 T; latest GDMA completion is
3,382 T into the 4,560-T VBlank. The baseline independent-core matrix is separate
from this 60-run host-only matrix.

A conservative linked quiet-publication calculation bounds the critical
transaction at 1,436 T after the LY check. At the latest accepted coarse entry,
at least 845 T remain before VBlank ends. This is different from the larger
observed finishing margins, which measure mainline work before publication.

### What This Does Not Prove

- Replay starts at a **relocated settled first-publication input**. Captured
  assets/audio/viewport data are retained, while the new link builds its own
  call/interrupt stack. This is not a new SameBoy capture of cold startup.
- It does not measure A-button-to-reveal or internal-paging latency.
- No-input full animation replay does not exercise every input or exit path.
- Ten species plus phase controls do not certify all future species or all
  possible hardware phases/owner workloads.
- The lowest replay SP is `$c0b6` relative to a rebuilt fixture stack at `$c0f0`.
  That is not the deepest possible live game stack including all submenu parents.
- Party Stats, New Dex Entry and battles retain their current schedulers and
  outstanding cry/timing issues.
- The known A-button Description-page corruption and synth-to-sampled cry
  cancellation issue remain separate backlog items.

## Emulator Test Suite

### Live Follow-Up Results

The user tested cold Listing entry and internal paging across the
Weavile-to-Exeggcute range, covering the replay cases plus Mewtwo. The animation
miss breakpoint did not fire. Warm Listing entry was deliberately omitted.
The dedicated sampled-cache-empty breakpoint, `$00:$3cb3` in this build, did
not fire during uninterrupted playback; it did fire while rapidly paging.

One captured Weavile -> Garchomp -> Bastiodon held-Up sequence confirms the
rapid-paging hit belongs to Garchomp's outgoing cry during Bastiodon's hidden
startup decompression. Garchomp's cache is empty with 266 blocks remaining,
the owner is switching species, and incoming animation playback is inactive.
Bastiodon's cry subsequently completes normally. This is recorded as deferred
`DEX-CRY-04` in the [bug backlog](../../pokedex_selected_bug_backlog.md), separate from
the passing uninterrupted-playback results. These observations do not sign off
the untested warm-entry or remaining exit/ownership cases below.

The expanded live suite then found **two Groudon animation misses**. Its actual
current-link starting state reproduces exactly in the independent core and host
at 861,581 instruction starts. Groudon exposes the short decoding-lookahead
horizon: repeated early poses prevent useful future decoding until too late.
A host-only later-target control clears both misses with unchanged startup,
quotas, VRAM and audio parameters. At that stage no game correction was installed. See
[Groudon results and fix direction](dex_groudon_target_results.md); the original
ten-species results above remain valid but do not close animation validation.

The subsequent [target-policy regression](dex_target_regression_results.md)
initially included 15 replay species and six extra timer phases per species.
All 105 earlier-decoding candidates pass, with unchanged startup and quotas.
Both nominal policies match the independent core at 19,788,568 instruction
starts. The unchanged build fails only Groudon; the new Milotic, Drapion,
Rhyperior and Yanmega inputs pass both policies. All 399 assets also pass the
separate structural check. These are host/core tests, not a new installed ROM.
The Spheal/Sealeo/Snorlax follow-up adds 42 successful baseline/candidate runs,
including six further nominal exact-core comparisons. Spheal's eight extra
decode calls change neither publication nor cry-completion timestamps.
Combined candidate coverage is 126 cases across 18 species; the other limits
and live acceptance requirements remain unchanged.
The correction is now compiled into the current build, and the 126-case linked
rerun passes as described above.

### Latest Live Acceptance: Target Correction

The user reports that neither the animation-miss nor sampled-cache-empty
breakpoint fired when testing **cold Listing entry and internal paging** on all
previously tested sampled-cry species, plus Mewtwo, Snorlax, Exeggcute, Hoppip,
Ledyba, Caterpie, Sentret, Rattata, Pidgey, Cyndaquil, Meganium, Bayleef and
Chikorita. Warm entry was deliberately not tested because its removal is
planned. No repeat count or new frame-by-frame timing capture was supplied.
The installed SameBoy ROM was independently checked and matches `e3846b...`.

This signs off the reported uninterrupted-playback suite for the two requested
entry paths. It does not imply warm-entry, rapid cancellation, A-button
Description transactions or adjacent-owner fixes. Exact authored timing remains
backed by the 18-species linked replay matrix, not inferred solely from the
absence of breakpoint hits across the additional species.

A fresh read-only scan of all 399 linked assets confirms the selected suite
covers all five timelines needing more than the 96-tile tail lead (Dusknoir,
Bastiodon, Groudon, Rampardos and Drapion), the largest changed-cell frame
(Luxray, 49), the most events (Yanmega, 48), one-interval events (Exeggcute and
Mewtwo), all native dimensions (5/6/7), counter wrap (Milotic), and the unused-tail
controls (Spheal/Sealeo/Snorlax). More ordinary finite species are not a required
gate for this change. Hitmonchan remains an optional long synthesized-cry check.

The audit also found **Seviper was the only generated timeline with a persistent
loop marker**: `dorepeat 6` jumped to `setrepeat 2`, resetting the counter on
every trip. Its 49 introductory intervals led to an endless 13-interval
frame-4/frame-5 loop, never reaching main `endanim` or the idle sequence. The
user subsequently confirmed more than a minute of uninterrupted looping.

With separate user approval, `DEX-ANIM-02` is now corrected by targeting command
7 (`frame 4`) instead. Rebuilding produces a finite 21-event timeline: 76 main
intervals, 18 base-hold intervals and 28 idle intervals, totaling 122 intervals.
All 399 linked timelines now terminate structurally and all 11 scheduler
contract tests pass. This script-only correction does not alter scheduler or
cry-runtime behavior and is not a new cycle-accurate replay acceptance result.

The user has since confirmed Seviper cold entry and internal paging terminate
correctly. Its 122-interval timeline and final base restoration also pass the
automated cold suite. See the [Seviper setup record](dex_seviper_new_entry_testing.md)
for that build's timeline completion breakpoint. No encounter changes were needed.

Start with no breakpoints for the visual tests. Leave normal audio enabled and
use normal emulation speed. The on-screen input overlay is useful for recording
startup/paging responsiveness; do not use debugger pauses in the timing video.

### 1. Focused Timing Cases

Use **Weavile, Luxray, Dusknoir and Garchomp**. For each, test these routes three
times, allowing the full main/hold/idle animation and cry to finish:

1. Cold Listing: move from another selection and press A immediately after the
   target appears. Do not deliberately wait to warm its animation dictionary.
2. Internal paging: enter Selected on a different species, then page to it.

For this target correction, also run **Groudon three times on each route**;
its two original misses are the primary reproduction. Warm-entry testing is
deliberately omitted at the user's request, not claimed to have passed.

Do not press A again during this group; that exercises the deferred Description
text-page bug rather than isolated animation playback. Look for missing pieces,
font tiles, flicker, an incomplete final frame, frozen poses, stretched holds,
early cry cutoff, and unexpected pauses in input or screen changes.

### 2. Broader Animation And Audio Cases

Run both routes once each for **Bastiodon, Rampardos, Rayquaza, Kyogre,
Metagross and Exeggcute**. Metagross covers a longer sampled cry; Exeggcute
covers active synthesized sound. Add available small controls such as
Chikorita/Bayleef, Meganium, Cyndaquil, Caterpie and Rattata for one clean pass.

#### Targeted Expansion After The Initial Live Pass

A read-only scan of all 399 linked assets/forms identified the following next
cases. This is structural coverage selection, not an additional cycle-accurate
replay or proof that these species pass. Counts include the complete generated
main/hold/idle timeline unless stated otherwise.

| Pokemon | Reason to add it |
| --- | --- |
| Groudon | 155 tail tiles actually referenced, above the 96-tile startup lead; several 3-interval holds and a 574-block sampled cry. |
| Drapion | 101 referenced tail tiles; repeated three-frame cycles with 27-32 changed tail cells exercise replacement beyond two resident slots. |
| Yanmega | 48 timeline events, the most in the current asset set; frequent 2-interval holds and base/resident-frame alternation with sampled audio. |
| Rhyperior | 35-38 changed tail cells in large poses, including transitions after 3-interval holds; multi-batch uploads and resident-frame reuse. |
| Milotic | 275 total intervals and a 609-block sampled cry; the sequence necessarily crosses the 8-bit display counter's wrap. |

Groudon and Drapion are the only untested members of the five-species set whose
current timelines require more than 96 tail tiles; Bastiodon, Dusknoir and
Rampardos are already covered. Do not rank this by unused dictionary entries:
Spheal has a 141-tile asset tail but its current timeline requires only the
first 43 of those tiles.

Start with one cold-entry and one internal-paging pass per new species, allowing
the entire main/hold/idle sequence and cry to complete without input. Keep both
animation-miss and sampled-cache-empty breakpoints enabled for diagnostic runs;
no complete capture suite is needed unless a miss or visual defect occurs.

Separately, a quick Caterpie/Cyndaquil/Rattata regression pass checks the earlier
stray-pixel cases; Bayleef adds a 6x6-native padding control. Hitmonchan is an
optional 279-interval synthesized-cry counterpart to Milotic. Include Spheal,
Sealeo and Snorlax once per route to check the unused-tail/control cases.
Warming remains implemented but is outside this live acceptance pass. Do not
treat its future removal as tested by the present build.

### 3. Ownership And Cancellation

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

### 4. What To Record

A single clean video covering the first four stress cases and representative
cold/paging/B-return routes is sufficient initially. Include the input
overlay if comparing responsiveness. Add a video of any visual defect even if
the miss counter stays zero: correct deadline counts alone do not prove correct
graphics. No need to repeat all historical suites before this first review.

## SameBoy Debugging

Addresses below apply to the current `e3846b...` ROM above. Verify the cartridge before
using them. For a fresh link, resolve the labels in `pokecrystal.sym` again.

### Animation Miss

```text
breakpoint $a0:$6805
```

This is `Pokedex_CountAnimationUnderflow`. Expected bytes:

```text
x/8 $a0:$6805
21 3b c7 34 c0 23 34 c9
```

The first instruction is `LD hl, $c73b`; the underflow count has not yet been
incremented at this breakpoint. It should not fire during uninterrupted settled
playback in the target cases. Do not infer that it proves visual corruption has
already appeared on the current scanline.

At any hit, capture:

```text
registers
backtrace
ticks keep
lcd
x/27 $0:$c72e
x/139 $0:$c758
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
After continuing to completion, gather the state/debug/audio dumps again.

`x/139 $0:$c758` still spans the existing diagnostic region plus the three
production scheduler bytes. **The final three bytes no longer represent a
compact-schedule pointer/run:** they are loop tick, last work tick and control.
Read them separately with `x/3 $0:$c7e0` when useful. Control bit 0 means deferred
audio is due; bit 1 means an optional finish was used in the current iteration.

Successful uninterrupted playback should leave `x/2 $0:$c73b` as `00 00`.
For a representative successful case, break manually after animation and cry
completion and capture the first two dumps plus audio state; no full backtrace
is needed unless something looks wrong.

### First Publication / New Replay State

Only needed if another full replay is requested:

```text
breakpoint $77:$5edb
```

This is `Pokedex_VBlankAnimationFrontpicMap.deadline_reached`. Its first bytes
are `f0 70 f5 f0 4f f5 3e 03`, starting `LDH a, [rSVBK & $ff]`.
Capture registers, backtrace, `ticks`, `lcd`, and a new-build starting save state
before continuing. Do not use the old `$77:$5ea5` address for this link.

### Suspected Sampled-Cry Underrun

Prefer the dedicated cache-empty branch for this build:

```text
breakpoint $0:$3cb3
```

The first instruction is `POP af`; expected six bytes are
`f1 e0 70 c3 63 00`. This path runs only when playback blocks remain but the
decoded cache is empty. Normal completion and intentional cancellation do not
pass through it. A hit during a hidden species transition can still be the
outgoing cry exhausting; see the live follow-up and `DEX-CRY-04` above. At a hit,
also capture `x/1 $0:$c727` to distinguish active playback from species staging.

The broader alternative below catches any stop with remaining blocks:

```text
breakpoint $0:$0063 if [$fff2] + [$fff3]
```

Capture registers/backtrace, `x/8 $4:$dff4`, `x/6 $0:$ffee`, `ticks keep`, `lcd`
and the animation state/debug dumps. A deliberate species/page/cancel operation
can also stop a cry early, so that context is essential. Normal sampled
completion has zero remaining blocks. Earlier `$3d1a`/`$3d36` instrumentation
addresses do not apply to this build.

## Reproducing Host Checks

Run from the repository root:

```sh
make -j8
make verify-dex-animations
python3 -B tools/test_dex_scheduler.py
python3 -B tools/test_dex_target_regression.py
PYTHONPATH=tools python3 -B -m dex_timing.finish_bounds \
  --output build/dex-scheduler-integrated/finish-bounds.json
```

The local integration rerun additionally uses the archived current-link starts,
prototype reports, and independent core retained under `build/`:

```sh
PYTHONPATH=tools python3 -B build/dex-target-integration-20260920/verify_integration.py
```

Its diagnostic script and artifacts are intentionally ignored, not portable
source fixtures. The earlier `integrated_replay --reference` procedure is for
the unchanged-target baseline: its cross-link asset equality guard correctly
rejects the new targets. The integration run imports the already-relocated
current-link inputs and actual save states instead; it does not weaken that
guard or alter the model to make the new ROM pass.

## Commit Preparation

### Current Checkpoint Decision

The user has chosen to commit the instrumented scheduler checkpoint first and
defer instrumentation cleanup until after the New Dex Entry audit. This
supersedes the earlier recommendation to strip telemetry before this commit.
Route 29/30 encounter overrides have been restored exactly to the branch
baseline and the normal ROM rebuilt; no scheduler, audio or instrumentation
instructions were changed. The rebuilt ROM differs from the accepted test
build only in encounter bytes and the ROM checksum; breakpoint addresses are
unchanged. Do not claim instrumentation removal or cleaned-build signoff.

The SameBoy save was backed up and both saved seen bitsets now cover all 373
species; caught flags and RTC data were preserved. No save is a source-tree
build input. The [Seviper and New Dex Entry procedure](dex_seviper_new_entry_testing.md)
records the next diagnostics, the rebuilt-ROM identity and owner-specific
limits of the current instrumentation. Warm caching remains unchanged.

### Checkpoint Audit: 2026-09-21

The user's final visual check reports no animation issues in Chikorita,
Bayleef, Meganium, Dusknoir, Rampardos or Luxray. Together with the full manual
internal-paging pass and automated cold suite, this is sufficient settled
Selected-page evidence for the instrumented checkpoint. It does not close
the B-return palette, Drapion overflow, rapid-input or outgoing-cry bugs.
The new vertical-to-horizontal input report is logged as `DEX-NAV-02`.

The working-tree review found these remaining test-specific cleanup items:

- `build/dex-cold-listing/` is not covered by the existing output ignore rules.
  It occupies about 68 MiB and exposes 1,162 untracked generated files, including
  emulator states, screenshots, reports, logs and the compiled runner. ROM/save
  copies are already ignored by extension, but the whole output directory
  should be excluded from the commit and given a dedicated ignore rule.
- The inactive `DEX_AB_DISABLE_LIST_WARMING` branch in `pokedex.asm` and
  `DEX_AB_FULL_DICTIONARY` call/helper in `pokedex_animation.asm` remain from
  the older A/B tests. Neither is enabled by the normal build; the full-tail
  helper is absent from the current linked symbols. Removing these branches
  while preserving their normal-build behavior is a suitable nonfunctional
  cleanup, separate from the retained instrumentation. Also distinguish the
  harmless obsolete `*.dexschedule` ignore/clean rules from actual live data;
  the generator and ROM no longer emit or consume a compact micro-schedule.

Route 29/30 have normal 10-percent encounter rates and their baseline species
tables. Joey's first party is one level-4 Rattata. Encounters, trainer parties,
wild-selection logic, sampled-cry constants and the sampled player have no
uncommitted test overrides. The 96-tail-tile animation startup and 32-block cry
prefill are intentional production settings, not remaining A/B overrides.
Active Listing warming, telemetry, miss diagnostics, host models, tests and
documented historical fixtures remain intentionally retained. Save unlocks and
Unown's form correction are external test-save changes, not game-source edits.

The initial audit changed documentation only. The subsequent approved cleanup
removes both dormant A/B branches while preserving the normal Listing producer
call and startup path. It also replaces the selective output ignore rules with
one root `/build/` rule. No files under `build/` were tracked, and all local
artifacts are retained. Instrumentation, active warming, host tools and the
production preload settings are unchanged. No staging, commit or save
replacement is part of this cleanup.

Validation: the normal ROM rebuilt successfully and is byte-for-byte identical
to the installed, accepted `412527bd...` ROM above. Symbol and map hashes are
also unchanged, so breakpoint addresses and prior playback evidence still
apply. All 11 linked scheduler contract tests, 14 cold-listing audit tests and
11 target-regression tests pass (36 total); `git diff --check` is clean. No
new full emulator sweep was needed for this binary-identical cleanup. Git now
reports no tracked or unignored files beneath `build/`.

### Deferred Release Cleanup

The following is a cleanup plan, not work already performed. Keep the cohesive
scheduler/generator change together; removal of active Listing warming and
unrelated backlog fixes are separate behavior changes.

- [x] Record the passing compiled-ROM replay matrix and reported live cold/paging suite.
- [x] Check Seviper's corrected finite loop path: manual cold/internal checks and the automated cold suite pass; optional Hitmonchan is not a gate.
- [ ] Preserve the accepted instrumented ROM, symbols, map and matching sources as a local reference before relinking.
- [x] Restore only the temporary Route 29/30 encounter blocks in `data/wild/johto_grass.asm` to the branch baseline. `parties.asm` and `engine/overworld/wildmons.asm` also have no uncommitted changes.
- [ ] Remove temporary trace/telemetry calls, counters, buffers and constants; retain visible underrun behavior and named miss paths for debugging.
- [ ] Preserve production logic currently mixed into diagnostics: the first-publication anchor uses `wPokedexAnimDebugMapPublishes` and `wPokedexAnimDebugLastPublishTick`. Replace that dependence with explicit production state rather than deleting it. Keep `wPokedexAnimLoopTick`, `wPokedexAnimWorkTick` and `wPokedexAnimSchedulerControl` independently of the removed debug reservation.
- [x] Remove inactive A/B branches (`DEX_AB_FULL_DICTIONARY`, `DEX_AB_DISABLE_LIST_WARMING`), preserving active warming and the cold/paging startup helpers. Historical host experiments and harmless obsolete `.dexschedule` ignore/clean rules remain separate from live runtime data.
- [ ] Retain reusable host-model code, regression tests and the living scheduler reference. Distinguish current-link tests from historical probes requiring a frozen reference ROM; make advertised test commands clear about those prerequisites.
- [x] Exclude local reports, volatile memory exports and traces from staging. The entire root `build/` directory is now ignored; no local reports or captures were deleted and no tracked build files needed removal.
- [ ] Rebuild from source, rerun asset checks and linked contracts, regenerate/check admission bounds, and replay the cleaned link. Removing instrumentation changes instruction timing and interrupt phase; it is not automatically covered by the instrumented-ROM results.
- [ ] Refresh breakpoint addresses and do a short cleaned-build live regression: Groudon, Dusknoir, Luxray, Spheal, a synthesized control, cold entry/internal paging, B-return and leaving/reopening the Dex. Preserve known transition/cancellation bugs as deferred, not implicitly fixed.
- [ ] Review the final staged diff, resource usage and backlog status before committing. Keep raw captures, emulator saves, binaries and experimental results out of the production commit.

Listing warming is still in the current implementation and is not signed off by
these cold/paging results. The preferred isolation is to commit the cleaned
scheduler first, then remove warming as a separately reviewed change with fresh
entry/scroll/paging checks. No instrumentation cleanup, warming removal,
staging or commit has been performed. The temporary encounters and dormant A/B
source branches have been removed under the checkpoint decisions above.

The historical 197-test model/capture regression suite deliberately uses the
frozen reference link, not current addresses. All 197 tests pass after the
host-model integration changes:

```sh
PYTHONPATH=tools DEX_TIMING_REFERENCE_ROOT=build/dex-scheduler-reference-20260920 \
  python3 -B tools/test_dex_timing.py
```

Reports and independent-core traces stay in ignored build directories. The
replay input identifies both ROMs and rejects moved RAM or asset pointers that
would require an explicit migration. It does not silently substitute an old
ROM when the new link differs. Current tests use the concrete linked routines;
historical experiments remain host-only and are not alternate runtime policies.
