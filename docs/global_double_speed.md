# Whole game double speed qualification

Production policy: [double-speed world with normal-speed battles](production_clock_policy.md).
Historical accepted trial: [normal-speed battle envelope](battle_normal_speed_prototype.md).
This report retains the earlier unretimed global-double baseline and its costs;
it is not the current production battle clock policy. References below to
unchanged production describe the historical experiment, not today's link.

2026-10-04. Private prototype based on production `2cec8051763e01b45fc2da51186ef795477fe7d4`
and the manually reviewed round-two Dex performance build. This establishes
double speed as the candidate's ordinary CGB clock policy, retains the Dex
optimizations that demonstrate useful double-speed gains, and qualifies
cross-owner audio, menus and native gameplay. **Production game source, ROM,
symbols, map and live battery saves remain unchanged pending visual review.**

The result is promising: all final automated acceptance cases pass, including
all-species Dex timing, 20-species post-catch input stress, six cry contexts,
custom inventories, 79 moves on both sides and native gameplay round-trips.
One genuine post-catch audio ownership failure was fixed. No animation script,
wait, motion calculation or graphical asset was retimed. The resulting animation
duration differences are explicitly retained for the user's assessment.

## Candidate and provenance

- ROM: `build/global-speed-20261004/final/pokecrystal-global-double-speed.gbc`.
- Matching `.sym` and `.map` are alongside it. The complete private source
  checkout is `final/candidate/`; measurements and regressions are separate.
- ROM SHA-256: `5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90`.
- Unchanged production SHA-256:
  `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.
- SameBoy source: `213a12ce93d66b105a113debd9396306066a7cfc`; CGB-E model,
  existing CGB boot ROM and MBC30 cartridge handling.
- Use matching native states for each ROM link. Do not load a production CPU
  save state into this differently linked ROM. A copied battery save is suitable.

The earlier `full/` build predates the final post-catch cancellation correction.
Its failures are retained as historical evidence, not current acceptance results.
Only `final/entry-accepted/` is the accepted final post-catch sweep. Intermediate
auditor failures from not recognizing a conditional cancellation call are test
tool errors, not additional game misses.

## Clock policy and implementation

The CGB enters double speed once during initialization, after stack/hardware
flags are valid while the LCD and interrupts are disabled, before ordinary game
audio and display setup. The helper checks KEY1's current-speed bit, so a soft
reset already in double speed does not execute another hardware STOP/switch.
Dex entry/exit inherits that policy: it no longer saves KEY1 on the stack or
switches back to normal when returning to gameplay. Defensive legacy mobile
cleanup calls request double speed rather than undoing the policy. Multiplayer
entry paths remain outside project scope and are not enabled by this work.

This avoids repeated visible speed-switch freezes and double-to-normal APU
mode transitions. SameBoy's warning is specifically guarded by an enabled APU
and a switch *from* double speed in `Core/sm83_cpu.c`. It was not observed in the
qualified final startup, Dex visits, save/reboot or native soft-reset paths.
Absence of that warning is not independent physical-CGB sound qualification.

The physical display clock remains 70,224 normal-speed T-cycles / 4,194,304Hz,
**16.742706ms per interval**. CPU time available in that interval doubles; LCD,
HDMA/PPU and APU clocks do not. Read-only observers convert SameBoy's absolute
ticks to physical time. Fractional intervals describe input/return points within
an interval, not a changed refresh rate. Inclusive routine spans include waits
and interrupts and must not be added to nested spans.

### Sampled cry cadence

The startup timer helper is ROMX, behind the existing ROM0 entry. Normal-speed
fallback is retained. The timer interrupt never makes a far call.

| Cry | Normal timer | Double-speed timer | Physical block period |
| --- | --- | --- | ---: |
| Ordinary | TAC 6, TMA 56, 200 clocks | TAC 7, TMA 156, 100 clocks | 12,800 normal T |
| Fainted | TAC 6, TMA 43, 213 clocks | TAC 7, alternating TMA 150/149, 106/107 clocks | 13,632 normal T average |

TAC 7's nominal 16,384Hz selection becomes 32,768Hz at double CPU speed. Odd
periods alternate floor/ceil rather than rounding every period up. First TIMA
uses the floor count; TMA initially selects the ceil count. At interrupt entry,
TIMA has already reloaded the old TMA, so the ISR selects the *next* reload and
negates a one-byte step. Ordinary even periods use a short zero-step path.
The odd pair is exactly 27,264 normal T, equal to two original fainted periods;
individual timer-overflow phases differ by at most 64 normal T from equal
spacing. IRQ-entry timestamps additionally include interrupt-service jitter.

The byte reuses bank-4 padding at `$dffc`; no aggregate RAM section grows.
CH3 frequency, decoded samples, codec, cache layout and 32-block prefill remain
unchanged. The Dex's existing double-speed finishing/admission path recognizes
the tested ordinary timer configuration. Faster CPU operation is not permission
to remove the scheduler's physical-clock deadlines or bounded work admission.

### New Dex Entry handoff correction

The initial faster build had nine real post-catch failures in the input sweep:
seven Metagross input/phase combinations and two Milotic combinations. The page
could return while its nonblocking sampled cry still had hundreds of blocks
remaining. Later naming/post-catch waits did not service that outgoing cry, so
the cache eventually emptied **after registration had returned**, not during
the owned animation.

At final page exit, immediately after `NewDexEntry_CancelAnimation`, the candidate
disables interrupts, checks `hSampledCryTimer`, conditionally calls the existing
`StopSampledCryAsync_NoInterruptControl`, then enables interrupts. This is eight
ROMX bytes; it introduces no wrapper or RAM. The page-1 to page-2 transaction
does not execute it. Synthesized cries are unchanged. Intentional owner exit
cancels remaining sampled audio instead of letting it leak into unrelated waits.

The host audit observes the exact conditional call site. It accepts nonzero
remaining blocks only when that owner cancellation was actually observed, and
still checks produced/consumed/cache accounting. Natural completion requires
zero remaining blocks and full sample production. This is not a relaxed rule
that silently treats every stop as success.

## Double speed optimization decisions

Each retained option has a qualifying double-speed path that saves approximately
one physical interval or more. This is a path-specific criterion, not a claim
that every request improves by an interval. Independent ablations kept the
other options and clock policy fixed; 816 matched cases per variant passed.

| Retained option | Double-speed evidence when removed | Qualification |
| --- | --- | --- |
| Bounded active Info admission | Active Info about 8.8-10.3 intervals slower; settled about 3 slower | Retain; active normal-speed version remains rejected |
| Fast Town Map graphics/palette/map transfer | Area about 27.6 instead of 9.5 intervals | Retain; largest non-clock Area gain |
| Indexed static nests with live roamer merge | Area completion about 2 intervals slower | Retain; species/location data regenerated at build time |
| Finish/coalesce pending Info pages | Rapid-input first response about 5.25 active / 3 settled intervals later | Retain; responsiveness during continued input matters |
| Committed Info retained across Area | Paired median 1 interval; 88/96 pairs save over 0.8 | Retain; benefit exists at double speed, not only normal speed |
| No eager offscreen Listing lookahead | Paired Info-return median 1 interval; 67/96 pairs save over 0.8 | Retain; physical five-slot ring remains, visible rows prepared before reveal |
| Fast glyph transfers | Ordinary Info often unchanged; several Stats loads and 19/96 Info returns save about 1 or more, max 5 | Retain for qualifying paths; not a uniform one-interval gain |

No new OAM conversion or permanent Stats VRAM allocation was implemented. No
physical reduction of the Listing ring was needed. Committed Info is retained
only when its owner/job is idle and valid; cancellation/incomplete preparation
uses the ordinary reconstruction fallback. Resource ownership and the earlier
rejected return-repair experiment are described in the
[round-two report](pokedex_selected_performance_round2.md).

## Performance measurements

The final check repeats 816 actions across Chikorita, Eevee, Tyrogue, Dusknoir,
Weavile and Garchomp, active/settled playback, relevant Info pages and four input
offsets. The previous 27-species production/benchmark matrix remains the baseline;
it was not rerun or silently replaced. Independent boot/normal-input states have
different initial phases, so small shifts in medians are not perfectly frozen
CPU/PPU comparisons. Full-screen First may include footer/portrait motion;
lower-panel replacement uses a quiet crop and is independently content-audited.

Each cell below is **physical intervals / ms**, rounded; First and Complete are
separate. These are final-build medians, not worst-case guarantees.

| Action | First | Complete |
| --- | ---: | ---: |
| Description -> Stats, active | 6.22 / 104.1 | same |
| Moves -> Stats, active | 5.65 / 94.6 | same |
| Description/Moves -> Stats, settled | 4.56 / 76.3 | same |
| Info cycling, active | 5.78 / 96.7 | same |
| Info cycling, settled | 4.93 / 82.6 | same |
| Description -> Area, active | 2.22 / 37.1 | 9.56 / 160.1 |
| Description/Moves -> Area, settled | 2.56 / 42.8 | 9.56 / 160.0 |
| Info -> Area, settled | 2.43 / 40.7 | 9.56 / 160.0 |
| Area -> Info, settled | 2.54 / 42.6 | 8.54 / 143.1 |
| Info -> Listing, active | 1.90 / 31.8 | 9.72 / 162.7 |
| Info -> Listing, settled | 1.68 / 28.2 | 10.43 / 174.7 |
| Fresh Description -> Listing, active | 1.53 / 25.6 | 6.69 / 111.9 |
| Fresh Description -> Listing, settled | 4.06 / 67.9 | 8.06 / 134.9 |
| Fresh Moves -> Listing, active | 6.19 / 103.6 | 6.94 / 116.1 |
| Fresh Moves -> Listing, settled | 1.81 / 30.3 | 6.56 / 109.8 |

Rapid Info: fifteen A presses, two intervals held/two released. First is 6.28 /
105.1 active and 5.56 / 93.1 settled; completion from the *first* press is 61.15 /
1023.9 and 59.81 / 1001.3. Most completion time is continued player input, not
an idle stall. Pages are published while input continues. Repeated requests no
longer perpetually abandon unfinished preparation.

Listing history still matters. Retaining the outgoing panel can make initial
full-screen feedback later even while correct Listing completion improves.
For example fresh active Moves First remains about 103ms, unlike production's
earlier roughly 31ms natural screen change. This was already present in the
manually reviewed whole-Dex prototype and is not concealed by faster Complete.
This pass does not claim to solve deferred opening/closing presentation work.

### Custom inventory responsiveness

Paired no-input replays exclude autonomous icon/disc motion from First. Native
CPU/PPU checkpoints are preserved; the host framebuffer is separately restored
because SameBoy does not serialize its already-rendered output pixels. The
following values aggregate measured actions that actually changed pixels, not
no-op controls. They use one native checkpoint per selection, not a four-phase
latency sweep or a universal worst-case promise.

| UI | Production First; Complete in intervals / ms | Final First; Complete in intervals / ms |
| --- | --- | --- |
| Pack | 2.12 / 35.5; 8.12 / 136.0 | 2.54 / 42.5; 5.54 / 92.7 |
| TM/HM Case | 2.61 / 43.6; 6.61 / 110.6 | 2.37 / 39.7; 5.37 / 90.0 |
| Apricorn Box | 2.20 / 36.8; 4.20 / 70.3 | 2.37 / 39.7; 3.37 / 56.4 |

Pack First is about 0.42 interval / 7ms later in these boot phases; Apricorn
First about 0.17 / 2.8ms later. One Items-pocket A action completes 1.42 / 23.7ms
later; other measured Pack completions are unchanged or faster. No functional
failure accompanies it. TM/HM completion has individual phase tails up to
0.77 interval later even though its median is faster. These small tradeoffs
remain observations for manual review, not animation-speed adjustments.

All 57 TM/HM selections, including the two-slot TM49-50 page and seven-slot HM
page, retain correct data and palette presentation. Right/Select disc-animation
state sets match. The settled default disc cycle is four states with four
displayed intervals per state in both ROMs. Opening the action menu freezes a
different valid disc/side-mini phase in 37 selections because earlier work
finishes at a different phase; this is not corrupted data or a new animation
asset. Five Pack B-return raw palette arrays differ in unused slots although
the visible returned screen matches. Whole-array/pixel identity is therefore
not claimed indiscriminately.

## Animation differences retained for review

The [full move measurement tables](global_double_speed_animation_measurements.md)
give all 79 moves on both sides, four input phases, paired difference ranges,
and subsequent multi-stage/hit invocations. Raw per-case durations are retained.
First requested invocation examples, medians in intervals / ms:

| Move and side | Production | Double speed |
| --- | ---: | ---: |
| Surf, player | 446.00 / 7467.2 | 316.46 / 5298.3 |
| Surf, opponent | 453.00 / 7584.4 | 322.51 / 5399.7 |
| Poison Gas, player | 501.27 / 8392.7 | 357.69 / 5988.7 |
| Poison Gas, opponent | 527.24 / 8827.3 | 358.17 / 5996.8 |
| Water Pulse, player | 315.00 / 5273.9 | 234.00 / 3917.8 |
| Thunderbolt, player | 305.01 / 5106.7 | 290.01 / 4855.5 |

Rain Dance is essentially unchanged at the median; two opponent phase samples
are about 1.05 intervals / 17.6ms longer. The complete table includes these
positive differences too. Differences are not uniformly 2x. Script-command
dispatch counts for the first invocation match in **all 158 move/side pairs**
at phase zero. Authored scripts, waits, motion code and assets are byte-identical
to production. The runtime can perform the same logical work using fewer
physical display intervals, particularly CPU-heavy motion, transfer and palette
work. This evidence supports CPU stalls as a contributor; it is not a per-function
proof that every saved interval was specifically trigonometry.

The native full-party Master Ball catch also records its entire throw/catch
animation invocation: **678.003 / 11351.6ms normal -> 584.002 / 9777.7ms double**,
about 94 intervals faster. Player send-out in that one scenario is 53.868 ->
52.999 intervals. These are single scenario measurements, not four-phase medians.
Other native animation routine spans in the same single-scenario replays:

| Animation routine | Production intervals / ms | Double-speed intervals / ms | Difference |
| --- | ---: | ---: | ---: |
| Egg hatch sequence | 761.797 / 12754.55 | 746.401 / 12496.77 | -15.397 / -257.78ms |
| Caterpie -> Metapod evolution | 655.798 / 10979.83 | 631.919 / 10580.04 | -23.878 / -399.79ms |
| Pokecenter healing animation | 201.781 / 3378.37 | 201.787 / 3378.47 | +0.006 / +0.10ms |

These are inclusive `EggHatch_AnimationSequence`, `EvolutionAnimation` and
`HealMachineAnim` spans, not complete interactions including text or player
input. They include authored waits and interrupt work. No delays were inserted
to make any of these take their old CPU-limited duration.

DIV-dependent RNG intentionally does not reproduce the same random stream at a
different CPU speed. Multi-hit count, encounter choices, contact choice and
battle follow-through can therefore differ. Compare equivalent animation
invocations, not entire battles with different outcomes.

## Automated qualification

All runs use isolated saves/states. Host observers do not repair timer settings,
force ready flags, reset the APU after Dex visits, skip waits, rewrite speed or
inject instruction costs. Fixtures declare only intended gameplay inputs/data:
species allocation, moves, party/encounter stats, owned items, location/events,
caught flags and expiring phone/egg counters. Actual menus, attacks, catches,
evolution, hatch scripts, warp routines and save logic execute in the ROM.

| Final suite | Coverage | Result |
| --- | --- | --- |
| Dex regressions | 6,182 cases: 373 species, cold/paging, Info, Moves, Area, active and rapid stress | zero failures; exact authored timeline and audio checks |
| Dex latency matrix | 816 requests, six representative species, four input phases | zero correctness/playback failures |
| New Dex Entry | 8,254 cases: 80 quiet baselines plus 8,174 phase/input patterns across 20 species | zero misses/accounting errors |
| Audio outside/through Dex | 960 cases, 20 species, Stats, wild catch, fainting, player send-out, blocking and stereo wrappers, four phases, zero/one prior Dex visit | zero misses; 1,024 complete sampled segments |
| Menu axis switches | 896 cases across 45 standard, battle, Mart, Ruins and Game Corner states | zero wrong masks or register-contract failures |
| Other menu controls | 672 held/key/button checks, 44 B-return/reopen round-trips | zero mask/register/return failures |
| Overworld movement | 38 walking and 38 cycling sequences | native positions/directions/menus qualified |
| Custom inventories | 232 final cases: 40 Pack actions, 21 Apricorn actions, 171 TM/HM actions | no selection/speed failures; presentation qualifications above |
| Move animations | 632 final cases: 79 moves x both sides x four phases | zero misses/locks; production and earlier private variant separately pass 632 each |
| Native gameplay | ten scenarios in production and final | zero final scenario failures |

Native gameplay covers connected-map crossing; entering/exiting buildings;
purchase, quantity/confirmation and reopening Pack; Old Rod dispatch;
Joey trainer battle through victory; actual Rare Candy level-up and
Caterpie -> Metapod evolution; egg hatching through overworld steps; incoming
random phone script after expiry (not a forced caller/script); full-party
Dusknoir Master Ball catch through New Dex Entry and PC handoff; Pokecenter
healing, in-game save, battery reboot and native A+B+Select+Start soft reset;
and all sixteen Ruins puzzle pieces through solved completion. Standard menus
also include PC storage/box actions, mail, naming, radio, phone, map, options,
party actions, Pack sort/quantity and battle-use inventory controls.

Audio comparison checks every final decoded block and CH3 frequency against
production; for production's premature misses it compares the complete common
prefix, not an impossible full digest. All **1,024** final sampled segments
complete. Production reproduces **52** known miss-containing cases in the same
matrix: 20 Stats, 16 catch/encounter and 16 foe-faint cases. Double-speed replay
eliminates those observed failures; this does not automatically close the old
normal-speed adjacent-owner bug reports or prove untested simultaneous workloads.
An ordinary final block period is 12,800 normal T; a Dusknoir fainting run has
13,632.011 normal T average measured IRQ spacing, including ISR jitter. No
pitch/sample data difference or speed restoration to normal was detected.

This is broad finite regression evidence, **not a complete playthrough of every
map, event, move or side activity**. No multiplayer/IR/mobile acceptance is
attempted. Long real-time RTC/day transitions, every fishing outcome, full
contest/Tower/credits story flows, hardware battery/power behavior, independent
emulator and physical-CGB audio remain outside this automated acceptance.
Native fixture/harness failures (wrong route through a wall, an incorrect TM
page assumption, insufficient input release, or a menu expectation after
Rollout won the battle) were corrected and rerun; they were not patched in the
game or misreported as speed regressions.

## Resources and risk

Exact linked cost versus unchanged production: **+7 ROM0 bytes, +3,804 ROMX
bytes**, one additional mapped bank `$b9`. Versus the reviewed whole-Dex
prototype: +21 ROM0, -17 ROMX. The ROM0 increment is an 18-byte odd-period
reload helper plus its three-byte IRQ call; startup relocation already saved
14 bytes versus production. Final-page cry cancellation is eight ROMX bytes.
No ROM0/WRAM0/HRAM expansion is concealed in a general aggregate.

| Region | Production used / free | Final used / free |
| --- | ---: | ---: |
| ROM0 | 15,830 / 554 | 15,837 / 547 |
| Mapped ROMX | 2,314,022 / 700,634 in 184 banks | 2,317,826 / 713,214 in 185 banks |
| SRAM | 49,994 / 15,542 | unchanged |
| WRAM0 | 4,083 / 13 | unchanged |
| WRAMX | 23,944 / 4,728 across seven banks | unchanged aggregate |
| HRAM | 127 / 0 | unchanged |

Two Info flags use existing bank-3 overlay slack; one timer-step byte uses
existing bank-4 tail padding. No VRAM/OAM allocation grows. About **1.77MiB**
of the 4MiB cartridge remains outside linked payload, including mapped holes
and unmapped banks. Free space is not all interchangeable across banks.

Implementation complexity is moderate rather than a Dex rewrite. The important
global risk is clock assumptions in future software timers and cycle-counted
effects. Future code must distinguish CPU cycles from physical display/APU
time; do not copy a normal-speed timer divisor into new audio code. DIV/RNG
behavior changes, while RTC and authored display-count waits are independent.
Do not reintroduce `NormalSpeed` calls into gameplay without a deliberately
owned transition and fresh audio/display qualification. Existing normal helper
definitions are retained but there are no ordinary gameplay call sites in the
candidate. Unused legacy Info glyph-copy code could reclaim about 63 ROMX bytes
on promotion; it is not necessary to change it for this qualification.

## Reproduction and artifact policy

All generated output is ignored under `build/`. Reusable tools are in
`tools/dex_timing/`; no runtime instrumentation was added to the production ROM.
The builder currently consumes the preserved accepted round-two candidate
snapshot. Keep that source snapshot or reconstruct it with the documented
round-two build recipe before reproducing these commands.

```sh
python3 tools/build_global_speed_prototype.py --output build/global-speed-20261004/rebuilt --jobs 24
python3 -m tools.dex_timing.global_speed --suite menus --variants production final
python3 -m tools.dex_timing.global_custom_menus
python3 -m tools.dex_timing.global_speed --suite moves --variants production final --jobs 24
python3 -m tools.dex_timing.global_speed --suite audio --variants final --jobs 24
python3 -m tools.dex_timing.global_gameplay --variants production final
python3 -m tools.dex_timing.global_review_save
python3 -m tools.dex_timing.performance_entry --audio build/global-speed-20261004/audio --audio-report report-final.json --output build/global-speed-20261004/final/entry-accepted --input-variant final --jobs 24
python3 -m tools.dex_timing.global_speed_report
```

The existing performance regression/measurement driver also generated
`final/regression/summary.json` and `final/measurements/performance.json`.
`global_speed_ablation.py` preserves one-option-disabled comparisons. Town
transfer's corrected ablation is `ablations-v2/town/`; earlier wrong-anchor
experiments are not the accepted result. `qualification/` consolidates current
per-case move/audio/gameplay reports without counting superseded harness errors.
Large WAV/log/JSONL files may be losslessly gzipped after writers finish;
representative listening WAVs, ROMs, states and reports are preserved. Gzip
integrity and original content SHA-256 are checked before removing the plain copy.
The completed qualification archive reclaimed 12.82GiB; twelve representative
normal/final Dusknoir and Mewtwo WAVs remain directly playable in `listening/`.

## Manual review

Use the final ROM with a copied battery save, starting from boot. Review Pack
switching/use/B-return, TM/HM selected-disc motion and all pages, Apricorn colors,
active and settled Info, Area round-trips and outgoing Listing presentation.
Listen to ordinary and fainted Dusknoir/Metagross cries in Stats, battle and
post-catch registration; exit New Dex Entry while a cry is active, then continue
through naming/PC prompts. Compare CPU-heavy Surf, Poison Gas, Water Pulse,
leaf/spinning effects and the Master Ball animation against the unmodified ROM.
The duration differences are intentionally not corrected.

For this final link, Selected animation-miss is `$a0:$6671`; sampled cache-empty
is `$00:$3cc1`. The latter branch should not occur for an uninterrupted owned
cry with blocks remaining; explicit final-page cancellation uses a different
path. New Entry clean-link misses are host-observed deadline/window branches,
not unconditional user breakpoints that only fire on failure. Capture a state,
registers/backtrace, `ticks keep`, `lcd`, `x/27 $0:$c72e`,
`x/8 $4:$dff4`, `x/6 $0:$ffee`, and `print/x [$ff4d]` if either miss reproduces.
Use matching symbols; all addresses are build-specific.

### Prepared animation comparison saves

**Superseded review save:** the original `manual-review/` package had an
off-by-one move-index error: its parser included `NO_MOVE` but added one to every
position. Its original self-check repeated that error. Do not use that package
to identify the intended assigned moves. The native automated move fixtures
use zero-based positions with `NO_MOVE` included and are unaffected; the linked
animation indexes and all new read-only timing replays confirm that separately.

`build/global-speed-20261004/manual-review-v2/` contains standalone `normal/` and
`double/` ROM copies with matching symbols and **byte-identical starting battery
saves**. Normal is unchanged production; double is the final qualified candidate.
Boot and Continue rather than sharing CPU states between differently linked ROMs.
The source fixture and the user's live save remain unchanged.

The save starts at Cherrygrove Pokecenter with six level-30 party Pokemon:
Kyogre (four largest player timing differences), Garchomp (Hydro Pump, Superpower,
Fire Blast and Water Pulse), Luxray (Thunderbolt, Thundershock, Caustic and Dragon
Dance), Rayquaza (charge effects/Overheat/Petal Dance), Meganium (leaf effects)
and Dusknoir (additional effects). Fourteen more review Pokemon in **Box 14,
ANIMS**, supply the remaining moves. All 79 original tested moves plus Dragon
Dance are included; move legality is intentionally not a
fixture requirement. Deposit a party member before withdrawing a boxed tester.
The package's `README.md` lists every nickname and move assignment.

The reusable `global_review_save.py` builder respects both save records,
conversion-table checksums, dynamic party IDs, wide stored-box move indexes,
box species indexes and the RTC trailer. Its corrected native verification checks
all 80 loaded move indexes, independently matches their linked name strings to
the requested names, checks usable PP and exercises a real PC deposit/withdraw
round-trip in both ROMs. Both ROMs are byte-identical to their previous arms;
no animation retiming is applied in this package.

See the [animation pacing investigation](global_double_speed_animation_pacing.md)
for the updated diagnosis, Polished Crystal comparison and proposed follow-up.
