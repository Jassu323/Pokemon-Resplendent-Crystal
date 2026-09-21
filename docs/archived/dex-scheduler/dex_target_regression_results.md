# Earlier-Decoding Target Regression

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Recorded 2026-09-20. Follow-up to the
[Groudon decoding-horizon diagnosis](dex_groudon_target_results.md).
The initial sections preserve the host/core experiments. The approved generator
change and rebuilt-ROM validation are recorded under [Compiled Integration](#compiled-integration).

## Exact Policy Tested

For each species, leave the first timeline event and every captured startup byte
unchanged. Change the dictionary target in every subsequent event to that
species' complete dictionary extent. No duration, frame ID, loop marker,
instruction, work quota, buffer, or audio parameter changes.

This is the same full-tail control that fixed Groudon, applied consistently to
the other cases. It does not mean synchronously loading the full dictionary
before reveal. Runtime continues to select one regular useful operation per
display counter: an uploadable prefix first, otherwise a bounded dictionary
chunk if below target. Existing finishing admission remains unchanged.

The experiment intentionally uses full dictionary extent, including any unused
tail entries, rather than silently substituting a future-referenced-extent
optimization. That distinction matters when choosing the final generator rule.

The normal game ROM, symbols, original emulator save states, SRAM and game ASM
are untouched. Private diagnostic ROM images containing only the target edits
are retained under the ignored results directory for independent-core replay.
They were not installed in SameBoy or made into a user test build.

## Coverage And Identity

All 15 available replay species are included: the original ten cases, Groudon,
and the four new starting states. This is full runtime coverage of the current
captured suite, **not** runtime certification of all 399 assets/forms.

| New starting input | Source | SHA-256 |
| --- | --- | --- |
| Milotic | SameBoy slot 3 | `739aaafd291f974f79939214b648f3a37958eabda1e26d2e40aa72c1567a057f` |
| Drapion | SameBoy slot 4 | `4ef3e47fe699334099af171053007f16bac743f376e48c3b771eb446c995f84f` |
| Rhyperior | SameBoy slot 5 | `4595dcfbd9d415de26b12e8bdfb3c58cfb9a157fde47b1c58a79b4746c2cfe56` |
| Yanmega | SameBoy slot 6 | `ba059ea41dcaae527b0ad72e5d60c6b98b6075cc34a799c3b0bceef1a1dbd83e` |

Groudon uses the previously preserved slot-2 starting state, hash
`a6f743c4a565c48f22fee2db02b4be8bc7b048a046b444979fdaaabbcd5f656c`.
These five cases import the complete actual current-link initial stack and
volatile state. The original ten use the previously calibrated captured inputs,
relocated onto the current link as described in the
[integrated validation guide](../../dex_scheduler_validation.md).

```text
ROM SHA-256: 3c7f469cfad2f141b8c8c6523401e6db0c368c70dd76b6619fa6c4c8ff32f09e
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
Core executable SHA-256: ab710f3e9d6ebb822198c5724cc7e5cd27b772390ad4b5ee00661ef0db6d70fc
```

The runner copies the new states into its ignored input directory before testing
and verifies all source hashes on exit. It also records model source hashes in
the manifest. No later captured state is injected into a replay.

## Results

The suite comprises **210 complete animation/cry runs**:

- 15 baseline and 15 earlier-decoding runs at their initial captured phases.
  Every one matches the independent SameBoy core instruction-for-instruction,
  including registers and elapsed T-cycles: **19,788,568 instruction starts**.
- Six additional timer phases per species, for both policies: 180 host runs.
  The initial delays are 64, 2,048, 4,096, 6,400, 9,600 and 12,800 T. These
  deliberately perturbed phases are controls, not new user captures.

All **105 earlier-decoding runs pass**. Groudon is the only baseline failure,
with the same two misses in each of its seven baseline runs. Every other
baseline case also passes, so the correction introduces no regression in this
matrix.

| Species | Full authored intervals | Baseline misses at captured phase | Earlier-decoding cases passed |
| --- | ---: | ---: | ---: |
| Weavile | 78 | 0 | 7 / 7 |
| Luxray | 92 | 0 | 7 / 7 |
| Dusknoir | 174 | 0 | 7 / 7 |
| Garchomp | 110 | 0 | 7 / 7 |
| Bastiodon | 205 | 0 | 7 / 7 |
| Rampardos | 139 | 0 | 7 / 7 |
| Rayquaza | 175 | 0 | 7 / 7 |
| Kyogre | 113 | 0 | 7 / 7 |
| Metagross | 228 | 0 | 7 / 7 |
| Exeggcute, active synthesized cry | 113 | 0 | 7 / 7 |
| Groudon | 211 | 2 | 7 / 7 |
| Milotic | 275 | 0 | 7 / 7 |
| Drapion | 175 | 0 | 7 / 7 |
| Rhyperior | 155 | 0 | 7 / 7 |
| Yanmega | 169 | 0 | 7 / 7 |

Full duration includes main animation, authored base hold and idle sequence.
The correction does not stretch holds, skip poses, or publish frames early.
Milotic explicitly exercises a full sequence longer than the 256-interval
display-counter range.

The new inputs have the expected bounded startup prefixes: Groudon 145/204
tiles, Drapion 145/150, Milotic 105/105, Rhyperior 133/133 and Yanmega 87/87.
Thus Drapion still exercises post-start decoding; the other three new cases
exercise stage/upload/timeline work with dictionaries that already fit within
the existing startup lead. No extra warmed prefix was injected to obtain passes.

Across all 105 candidate runs:

- Zero animation misses, late/early publications, duplicate publications,
  incorrect resident-slot tile bytes or incorrect published map cells.
- All 98 sampled-cry runs complete naturally, with zero remaining playback
  blocks and no cache exhaustion.
- All seven Exeggcute runs retain completed synthesized cries. Their complete
  audited sound records equal the corresponding baseline: 114 sound-engine
  updates and 949 hardware writes per run, including timestamps and channel
  completion changes. This does not model the full acoustic APU waveform.
- No audited GDMA or interrupt hardware writes occur outside VBlank.
- Smallest observed finishing margin: **12,702 T**, Bastiodon at phase 4,096,
  still above the unchanged 8,192-T finishing reserve.
- Latest GDMA completion: **3,382 T** into the 4,560-T VBlank, leaving 1,178 T.

The existing reference-model suite passes **197 tests** in 210.522 seconds.
Eight focused tests additionally cover private target edits, preservation of
first-event/duration/loop data, rejection of malformed control data, and the
diagnostic reader's clean-completion-without-a-miss format.

## All-Asset Structural Check

All **399 linked assets/forms** pass independent dictionary/plan/timeline
validation. The private target transformation is checked for every one, proving
that only later target bytes change, the first target stays intact, durations
and frame IDs remain identical, and loop destinations and payload lengths are
preserved. This check is structural, not cycle-accurate replay of all species.

## Assessment And Remaining Gates

The broader results support fixing the post-start decoding horizon without
changing the scheduler, increasing startup lead, adding another producer,
relaxing deadlines, or allocating more VRAM. Groudon's failure remains an
avoidable delay in releasing useful work, not a demonstrated lack of hardware
capacity. No earlier success in the captured suite is lost.

The concrete tested rule reuses existing target bytes and adds no payload
length or runtime memory. A production implementation must preserve the first
event's startup contract. Using only the maximum future referenced extent
could avoid decoding unused dictionary suffixes, but would be a different
general rule and should not be treated as already tested by this full-tail
experiment.

These runs start at first publication. They do not measure input-to-reveal
latency, simulate rapid paging/cancellation, or sign off the known Description
A-button transaction issue. Live cold/warm/paging checks are still appropriate
after an approved generator/runtime change. The separate Stats/New Dex Entry/
battle owners are not changed or certified here. No additional capture is
needed to proceed with the target-policy decision for the current Selected
owner.

## Reproduction And Artifacts

The entry point is `tools/dex_timing/target_regression.py`. It runs eight worker
processes by default and calibrates both nominal policies against the independent
core before allowing the phase sweep. Reports and copied inputs are under
`build/dex-target-regression-20260920/`:

- `manifest.json`: source identities, policy, coverage and model source hashes.
- `asset-validation.json`: all 399 structural checks.
- `summary.json`: all 210 results, including the failing baseline controls.
- `<species>/captured/`: actual or relocated input, baseline/candidate reports,
  independent-core output and compressed instruction traces.
- `<species>/phase-<T>/`: full baseline/candidate replay and hardware audits.

```sh
PYTHONPATH=tools python3 -B -m dex_timing.target_regression \
  --rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --reference build/dex-scheduler-reference-20260920 \
  --core build/dex-scheduler-integrated/final-core-check/sameboy-linked-replay \
  --state-directory /Applications/SameBoy/Games \
  --groudon-state build/dex-scheduler-groudon/groudon-start.s2 \
  --species weavile luxray dusknoir garchomp bastiodon rampardos rayquaza \
    kyogre metagross exeggcute groudon milotic drapion rhyperior yanmega \
  --output build/dex-target-regression-20260920 \
  --jobs 8
```

Slots 3-6 must still contain the identified states to repeat this command.
The preserved copies in `inputs/` remain the authoritative inputs for this run
if the user later reuses those slots.

## Unused-Dictionary-Tail Follow-Up

Also recorded 2026-09-20. The user supplied first-publication states for Spheal
(slot 7), Sealeo (slot 8), and Snorlax (slot 9), with registers, backtraces and
LCD snapshots in `Spheal, Sealeo, and Snorlax.txt`. All three snapshots agree
with their states at `$77:$5edb`, before the first publication transaction.
The LCD is on line 145, with 244 T until the next display event for Spheal and
240 T for each control. No additional user capture is needed for this check.

These inputs use the encounter-only Route 29/30 build:

```text
ROM SHA-256: 22e039075004ee7444c9b948b9ae502374c2c38dbd196bed4120867207006c83
SYM SHA-256: 08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
```

Executable code and animation assets are unchanged from the preceding
15-species regression. Original ROM, symbols, states and attached capture text
were not modified; copied inputs and the new manifest preserve their identity.

| Species | Slot | State SHA-256 |
| --- | ---: | --- |
| Spheal | 7 | `cc0eb1c8880960dc3e3ce9accb4e2f052c57354f86956b30d6cc76e4f8af1cf7` |
| Sealeo | 8 | `b9945aafc8ffa2343201f272c918a3b6a5aa4d2870fee7546618a546cbd27622` |
| Snorlax | 9 | `1677bc22bc18b86e7f48ecc5ef9547007025712103cb0c523cf3c0042a7d3dfa` |

### Coverage And Results

Both target policies were replayed through the full animation and cry for all
three species: the captured phase plus the same six timer-phase controls gives
**42 runs, all passing**. All six nominal runs match the independent SameBoy
core instruction-for-instruction, including registers and T-cycles:
**3,247,893 instruction starts**. Phase controls are host runs, not additional
user captures or independent-core comparisons.

| Species | Full authored intervals | Decoded tiles at start / total | Post-start decoder calls, baseline / proposed | Proposed cases passed |
| --- | ---: | ---: | ---: | ---: |
| Spheal | 166 | 121 / 166 | 0 / 8 | 7 / 7 |
| Sealeo | 166 | 126 / 126 | 0 / 0 | 7 / 7 |
| Snorlax | 174 | 76 / 76 | 0 / 0 | 7 / 7 |

Every proposed run retains the baseline's exact publication timestamps, not
just the same final duration. No animation miss, late/early or duplicate
publication, wrong tile/map cell, sampled-cry underrun, or audited out-of-VBlank
GDMA/interrupt hardware write occurs. The smallest finishing margin is 14,990 T
(Sealeo), above the unchanged 8,192-T reserve. Latest GDMA completion is 2,662 T
into VBlank, leaving 1,898 T before its end.

Spheal and Sealeo sampled cries finish naturally in all 14 candidate runs,
with the same completion timestamps as the corresponding baselines. Snorlax's
synthesized cry starts active and completes in all seven candidate runs. Its
CPU-visible sound audit is identical to baseline, including timestamps: 175
sound updates and 951 hardware writes in the nominal run. Acoustic APU waveform
equivalence is not claimed by this CPU/register audit.

### Exact Spheal Cost

Spheal's current timeline references only the first 68 dictionary tiles, but
startup has already decoded 121. The full-dictionary control decodes the
remaining **45 unused tiles** in eight bounded calls. At the captured phase:

- Decoder instructions cost **75,696 T**, about **18.05 ms total CPU work**.
- Including interrupts during those calls gives 113,172 T elapsed inside the
  decoder spans, about 26.98 ms. That is not all extra CPU work: those interrupts
  also run in the baseline.
- Work is distributed across display intervals 2-9, not one added startup pause.
  Individual decoder instruction costs range from 4,880 to 12,600 T.
- Frame-publication and cry-completion timestamps remain exactly unchanged.
  No extra uploads are needed for the unused tiles.

This removes the observed regression concern for the simple full-dictionary
rule. It does not make the extra work useful. Avoiding that work by using a
future-referenced extent is still a separate optimization, not the rule tested
here. No species-specific exception is required by these results.

### Host Importer Adjustment

The first attempted run correctly rejected Snorlax under the importer's earlier
sampled-timer-only guard. Its saved timer is the ordinary `(TMA=$00, TAC=$04)`
configuration with sampled playback inactive, not `(TMA=$38, TAC=$06)`.
The underlying timer model already supports both periods. The importer now
also accepts the normal timer for a synthesized species with inactive sampled
playback, without substituting timer registers or changing emulation timing.
Three focused tests cover acceptance and rejection; all 11 target/importer
tests pass. Snorlax's exact independent-core match validates this input path.
The existing reference-model suite also passes all 197 tests in 198.541 seconds.

### Assessment And Reproduction

Combined with the earlier matrix, the same candidate policy now passes **126
runs across 18 species**. All 36 nominal baseline/candidate replays match the
independent core, totaling 23,036,461 instruction starts. This is coverage of
the captured suite, not runtime certification of all 399 assets or all possible
timer phases. The all-asset structural check was repeated and still passes.
Cold input-to-reveal latency, rapid paging/cancellation, and other display
owners remain outside these first-publication replays.

At this stage the game still used its original targets. These results supported proceeding
with the already described generator correction while preserving startup,
work quotas, reserves, memory allocation and authored durations. A rebuilt
production ROM still needed linked regression and live entry/paging checks.

The runner now accepts `--species` to select a subset. Results, copied states,
the attached capture text, private diagnostic ROMs, and compressed core traces
are under `build/dex-target-regression-spheal-20260920/`:

```sh
PYTHONPATH=tools python3 -B -m dex_timing.target_regression \
  --rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --reference build/dex-scheduler-reference-20260920 \
  --core build/dex-scheduler-integrated/final-core-check/sameboy-linked-replay \
  --state-directory /Applications/SameBoy/Games \
  --groudon-state build/dex-scheduler-groudon/groudon-start.s2 \
  --species spheal sealeo snorlax \
  --output build/dex-target-regression-spheal-20260920 \
  --jobs 3
```

Slots 7-9 must still contain the identified states to repeat this command.
The copied inputs remain authoritative after the live slots are reused.

## Compiled Integration

Implemented on 2026-09-20 after approval of the unused-tail follow-up. The
production generator now receives the dictionary extent when assigning targets:
event 1 keeps its previous target calculation, and every later event uses the
complete extent. Runtime assembly is unchanged. The first-event startup floor,
six-tile decode streams, twenty-tile uploads, finishing reserve, two VRAM slots,
32-block audio prefill and authored durations are all retained.

### Binary And Resource Verification

```text
Before ROM: 22e039075004ee7444c9b948b9ae502374c2c38dbd196bed4120867207006c83
After ROM:  e3846b92741e15056e5886dd3d4dfd39782dcfda10cfac21e0edfc02c33901ee
SYM:        08e0b973240d3e3adf6446f5fcb4ea72e59dc8b8b5a76755f6ec2c1034472d9c
```

An independent byte comparison reconstructed the expected ROM by applying the
already tested target-only control to the old cartridge and updating its global
checksum. The result matches the rebuilt ROM exactly:

- 2,954 existing target bytes change across 387 of 399 assets/forms.
- Every first-event target, duration, frame ID, loop and asset size is unchanged.
- All other bytes, including executable code and encounters, are unchanged
  apart from the cartridge global checksum.
- The complete map and symbol files are byte-identical; the ROM stays 4 MiB.
- Added allocation is **zero** in ROM0, ROMX, WRAM0, WRAMX, HRAM and VRAM.

The previous ROM, map, symbols and generator source are preserved in
`build/dex-target-integration-20260920/baseline/`. The installed SameBoy ROM,
original saved states and SRAM were not edited.

### Rebuilt-ROM Replay Results

All **126 runs pass**, covering the same 18 species and seven initial timer
phases per species as the earlier candidate matrix. There are no animation
misses, late/duplicate publications, incorrect maps or tiles, sampled-cry
underruns, or unsafe publication transfers/writes. Every expected complete
main/hold/idle duration is met. All 112 sampled cases finish naturally; active
synthesized Exeggcute and Snorlax remain included in the other fourteen cases.

The 18 nominal runs match the independent SameBoy core at **11,514,944
instruction starts**, including registers and elapsed T-cycles. Their entire
core traces are byte-identical to the corresponding private-prototype traces.
All six extra timer-phase outcomes per species also match the previous
prototype outcomes. Minimum finishing margin remains **12,702 T** against the
unchanged **8,192-T** reserve; latest publication GDMA ends at **3,382 T** within
the **4,560-T** VBlank.

The integration imports archived current-link inputs: ten previously relocated
starts plus eight actual-stack states. No host timing/model changes or later
state injection were needed. The imported-state replay class records fewer
optional operation spans than the older relocated-start class; comparisons
therefore check the identical outcome fields and common operation spans, with
full nominal trace equality independently proving identical CPU execution.

`make verify-dex-animations` validates all 399 generated structures. Eleven
linked scheduler tests and eleven target/importer tests pass. The added linked
contract test checks all species' preserved startup rule and complete later
targets, so the generator policy is protected against regression.
The historical reference-model suite also passes all 197 tests in 204.622 seconds.

Local artifacts are under `build/dex-target-integration-20260920/`:
`binary-verification.json`, `manifest.json`, `summary.json`, and per-case linked
reports, exported memory and compressed core traces. Its local verification
driver reuses the archived inputs and prior results, runs the actual compiled
ROM without private target overrides, and checks input hashes before/after.
This directory is explicitly ignored so memory dumps and diagnostics do not
become production assets.

### Live Acceptance And Remaining Scope

The user reports passing **cold Listing entry and internal paging** across all
previously tested sampled species and Mewtwo, Snorlax, Exeggcute, Hoppip, Ledyba,
Caterpie, Sentret, Rattata, Pidgey, Cyndaquil, Meganium, Bayleef and Chikorita.
Neither miss breakpoint fired. Warm entry is deliberately omitted, while its
existing implementation is retained for a separate future removal. The installed
SameBoy ROM hash was checked against the rebuilt artifact. This is a user-reported
breakpoint result, not a new frame-by-frame duration measurement for every species.

The ordinary finite workload coverage is sufficient to proceed toward cleanup;
Seviper's distinct persistent-loop path is the one additional recommended check.
Its unchanged authored script jumps onto its own repeat reset; that issue is
logged separately rather than silently changing its timeline during cleanup.

Breakpoints remain `$a0:$6805` for animation misses and `$00:$3cb3` for sampled
cache exhaustion with blocks remaining. Both instruction sequences were read
back from the rebuilt ROM. See the [test guide](../../dex_scheduler_validation.md)
for capture commands and the distinction between uninterrupted playback and
the already deferred outgoing-cry exhaustion during rapid black-screen paging.
These no-input replay results do not certify startup latency, every species,
interactive handoffs, or the separate Stats/New Dex Entry/battle owners.
