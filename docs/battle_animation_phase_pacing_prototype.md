# Battle Animation Phase Pacing Prototype

## Status and Conclusion

Private experiment, 2026-10-04. Production and the accepted whole-game
double-speed ROM remain unchanged. This is a test of phase-local display
pacing, not an approved final timing policy for all battle animations.

The mechanism preserves the animation's logical samples and slows selected
sections without adding a large end-of-animation delay. It restores several
primary durations close to normal-speed production and removes the large
player/opponent timing asymmetry. It does not interpolate motion, remove
Caustic's scanline crowding, or recreate every normal-speed pause.

One common charge target is not a sufficient final policy: Superpower needs
more charge time than this trial supplies, whereas Shock Wave receives too
much. The current records are intentionally retained for visual review rather
than repeatedly tuning targets before the user has assessed the cadence.

## Scope and Isolation

The prototype starts from
`build/global-speed-20261004/final/candidate`, the accepted double-speed
snapshot. The only animation-script changes cover Surf, Water Pulse, Dragon
Dance, Thunderbolt, Caustic and the eight callers of the shared charge
controller: SolarBeam, Dazzling Gleam, Superpower, Shock Wave, Wild Charge,
Volt Tackle, Energy Ball and Shadow Ball.

Petal Dance and Thundershock are unchanged controls. Charge-looking graphics
with a different motion controller are not automatically included. There are
no move-data, motion-function, frameset, sound-program, map-encounter or trainer
changes. The three deferred battle graphical defects remain separate issues.

Build source is generated privately under
`build/battle-pacing-20261004/prototype-v1/candidate`. Do not reuse CPU save
states across differently linked ROMs. Each headless arm booted its own matching
ROM and private battery before native battle fixtures were derived.

## Runtime Method

The normal logical iteration still runs script commands, BG effects, object
motion/framesets/OAM construction, LY overrides and palettes. One shared helper
then gates the next complete logical iteration against the physical VBlank
counter. It never advances motion or framesets independently of their objects.

Each five-byte inline record contains an opcode, extra-hold numerator,
denominator, optional logical-update limit and phase ID. A fractional
accumulator distributes additional display holds through the selected section.
Surf's `2/3` adds two holds per three updates, yielding a repeating physical
gap pattern of 1, 2, 2 intervals. This is temporal resampling by repetition,
not smoother intermediate coordinates.

Deadlines advance from the preceding absolute deadline, not from the producer's
arrival time. Work that already crosses a display boundary consumes its timing
budget; the helper does not automatically add another full delay. It always
performs the existing `BattleAnimDelayFrame` service at least once. Additional
holds use that same service, including its existing audio servicing.

Late work is counted, not concealed by skipped logical states. Subsequent
updates can consume less deliberate waiting to recover. Water Pulse recorded
at most two late checks in one invocation, but no active update gap exceeded
two display intervals and no logical sample was skipped. A late-check count
is not the Dex animation-miss or sampled-cry-underrun signal.

The byte counter wraps normally. Signed comparisons are safe while the pending
deadline is less than 128 intervals away; this trial only requests one- or
two-interval gaps. Unit tests cover wraparound and work already consuming the
budget. The counter previously did not advance in the two cutscene VBlank
handlers, so this private ROM adds an increment to each handler.

| Section | Extra holds / updates | Limit | Observed extra holds |
| --- | ---: | ---: | ---: |
| Surf wave and ending wave section | 2/3 | Explicit end | 126 |
| Water Pulse initial drift | 1/3 | Next section | Included below |
| Water Pulse rings and impact | 6/7 | Explicit end | 88 total |
| Dragon Dance orbital portion | 10/81 | 81 | 10 |
| Thunderbolt initial strikes | 12/77 | 77 | 12 |
| Caustic bubble/pop sequence | 1/15 | Explicit end | 13 |
| Shared charge portion | 34/81 | 81 | 34 |

All eight charge callers use the same first-trial target. The limiter stops
the policy before the rest of the attack and most of the stationary charge
wait. The final deinitialization sample still receives one additional display
hold, documented below. Entry resets dedicated state, including instrumentation
counts; it does not reuse the Surf scratch union. An explicit disabled record
or the limiter returns the rest of the script to unpaced operation.

The shared mechanism also delays other work in that active logical iteration.
For example, Superpower's concurrent charge, rock chips and shake all advance
together. Individual SFX programs and pitch are untouched, but the times at
which script/object code starts subsequent SFX change with the paced updates.

## Primary Animation Measurements

These are medians over four native starting offsets on each side, not nominal
60 Hz conversions. One display interval is 70,224 normal-speed T-cycles,
approximately 16.742706 ms. P/F means player/opponent. The primary script
includes its authored waits and setup/cleanup; it excludes the outer wrapper's
damage flash and remaining sound wait. SolarBeam here means its charge turn;
its later beam attack is not paced.
Normal refers to this project's production ROM, not an unmodified retail game;
many of the moves have custom animations.

| Move | Normal intervals P/F | Unpaced double P/F | Paced double P/F | Paced ms P/F |
| --- | ---: | ---: | ---: | ---: |
| Surf | 377.01 / 379.03 | 193.04 / 193.06 | 319.01 / 319.00 | 5341.2 / 5340.9 |
| Water Pulse | 241.06 / 247.93 | 159.03 / 159.03 | 247.01 / 247.02 | 4135.7 / 4135.8 |
| Dragon Dance | 156.06 / 165.06 | 146.02 / 146.05 | 156.03 / 156.03 | 2612.3 / 2612.3 |
| Thunderbolt | 232.03 / 239.91 | 220.01 / 220.01 | 232.01 / 232.01 | 3884.5 / 3884.5 |
| Caustic | 216.10 / 230.10 | 202.02 / 202.02 | 215.02 / 215.02 | 3600.1 / 3600.1 |
| SolarBeam | 207.99 / 215.02 | 173.98 / 174.01 | 208.03 / 208.01 | 3483.0 / 3482.6 |
| Dazzling Gleam | 256.06 / 269.05 | 224.02 / 224.02 | 258.02 / 258.02 | 4320.0 / 4320.0 |
| Superpower | 317.08 / 323.08 | 244.02 / 244.03 | 278.01 / 278.04 | 4654.6 / 4655.1 |
| Shock Wave | 302.03 / 311.02 | 283.01 / 283.04 | 317.00 / 317.01 | 5307.4 / 5307.6 |
| Wild Charge | 350.03 / 361.90 | 319.01 / 319.03 | 353.01 / 353.01 | 5910.4 / 5910.3 |
| Volt Tackle | 486.03 / 502.90 | 441.01 / 441.05 | 475.00 / 475.08 | 7952.8 / 7954.1 |
| Energy Ball | 174.08 / 185.96 | 142.05 / 142.04 | 176.02 / 176.03 | 2947.1 / 2947.3 |
| Shadow Ball | 193.05 / 204.06 | 158.02 / 158.04 | 192.01 / 192.02 | 3214.8 / 3215.0 |

Surf's visible script is about 58-60 intervals faster than normal, substantially
closer to the requested middle ground. Its complete wrapper is not uniformly
60-65 faster: player median 446.00 -> 396.50 intervals, opponent 453.00 ->
389.50. Remaining sound waits and damage/restoration work make total wrapper
duration a different target from wave-motion duration. No end padding was added
to force either measurement to match.

Water Pulse is about six intervals slower than normal on the player side and
approximately matches the old opponent duration. Dragon Dance and Thunderbolt
approximately match normal player duration on both sides. Caustic approximately
matches normal player duration, not the slower old opponent cadence.

## Charge Target Limitation

The elapsed time between logical samples 0 and 81 isolates the paced prefix
more usefully than whole-move duration. Means over four offsets on the player
side are approximately:

| Caller | Normal prefix intervals | Unpaced double | This trial |
| --- | ---: | ---: | ---: |
| SolarBeam | 112.53 | 80.53 | 114.55 |
| Dazzling Gleam | 110.40 | 80.47 | 114.48 |
| Superpower | 146.20 | 80.55 | 114.54 |
| Shock Wave | 95.10 | 80.52 | 114.50 |
| Wild Charge | 95.91 | 80.58 | 114.50 |
| Volt Tackle | 111.02 | 80.55 | 114.48 |
| Energy Ball | 110.97 | 80.55 | 114.49 |
| Shadow Ball | 111.87 | 80.43 | 114.39 |

Different companion objects and BG work change the cost of an otherwise shared
controller at normal speed. A universal 34-hold setting therefore is a useful
cadence experiment, not a correct reconstruction of every caller. Per-caller
numerators fit the existing record without additional storage or another
scheduler. Superpower's remaining attack also needs a separate target if its
entire primary script is to return to normal duration. Do not infer all phase
targets from the single total-duration difference.

## Rendered Frame Review and Caveats

The observer captures each native 160x144 raster, hardware OAM and complete
shadow OAM, plus script delay/parameter at each logical iteration. There are
78 encoded clips: 13 target moves, both sides, all three arms. Matched-state
contact sheets focus on the moving effects and Caustic's pop/droplet overlap.
Native encounter backgrounds differ between the independently booted arms;
whole-image pixel identity is not an appropriate cross-arm assertion.

All 656 paired battle cases across the 82-move regression have identical
script-delay/parameter and shadow-OAM sequences between unpaced and paced
double speed. The 104 selected-move pairs have no missing/reordered logical
samples. This verifies those signatures, not every byte of internal BG state
or a particular subjective impression of smoothness.

Specific points for manual assessment:

- **Mixed one-/two-interval cadence:** Surf repeats 1,2,2; Water Pulse's ring
  portion is predominantly two intervals with occasional one. Dragon Dance
  adds one extra hold roughly every eight orbital updates. This can produce
  rhythmic unevenness because it repeats samples instead of interpolating
  motion. It does not create a multi-frame scheduler stall. The rendered
  sequence remains spatially coherent, but final judgment of the feel is manual.
- **Dragon Dance's existing stationary tail:** the longest identical rendered
  run is 59 intervals, approximately 988 ms, in normal, unpaced double and paced
  double. The orbs disappear before the script finishes waiting. This can look
  like an animation hang, but it is not introduced or lengthened by this trial.
- **Caustic's small added stationary hold:** the longest identical rendered run
  is 20 -> 22 intervals on the player side, approximately 335 -> 368 ms, and
  14 -> 15 on the opponent side. Uniformly pacing the entire bubble/pop section
  also repeats a few already-stationary samples. This is a real difference,
  not a lock or a lost update; it is left visible for review.
- **Charge center hold:** SolarBeam, Dazzling Gleam, Energy Ball and Shadow Ball
  have a 23 -> 24 interval longest identical run, approximately 385 -> 402 ms.
  The limited phase includes the first deinitialized-particle sample, so its
  last extra hold extends the stationary center by one interval. A tighter
  limiter could exclude that sample without changing the mechanism.
- **Caustic crowding remains:** player OAM still reaches 16 objects on one
  scanline across 26 crowded logical updates; opponent reaches 12 across four.
  All three arms have the same crowded geometry. Raster strips show the same
  dense bubble/pop/droplet overlap. Pacing cannot guarantee that previously
  obscured dropouts become invisible and may make a crowded state more apparent
  by holding it longer. No claim is made that this fixes the dropout report.
  Superpower/player also reaches 11 objects on two logical updates in all three
  arms; that inherited pressure is not a newly introduced pacing defect.
- **Other inherited stationary runs:** Thunderbolt's longest identical run is
  25 intervals in all arms; Superpower's is 32; Shock Wave's is 37. They were
  not created by an end-of-effect padding routine.
- **Partial timing restoration:** Superpower remains appreciably faster overall;
  Shock Wave becomes slower than normal. These are target-selection limitations
  rather than evidence of lost motion states. Listen for sound/effect coordination
  as well as watching overall duration.

No new long frozen state, lock, graphical corruption or playback miss was found
in this suite. The caveats above prevent calling this production-ready solely
on the basis of its total durations.

## Regression Coverage

- 360 selected/control comparisons: 15 moves, two sides, four starting offsets,
  normal production, accepted unpaced double speed and paced double speed.
- Full 82-move pass on both double-speed arms: 656 cases per arm. Together with
  normal comparisons, 1,432 distinct native battle cases pass. Repeated-hit and
  charge/attack paths are exercised through ordinary battle inputs.
- 6,182 Dex cases: all 373 species, cold entry, internal paging, Info, Moves,
  Area and rapid-input stress on the established intensive subset. No playback
  misses or expected-speed failures.
- 480 audio-owner cases: 20 species, four offsets, Stats, catch/New Dex Entry,
  fainting, player send-out, blocking and stereo cry. No sampled misses; wave
  block counts/content, timer settings and frequencies match the accepted
  double-speed reference in every case.
- 896 menu-input permutations across standard menus, battle, mart, Ruins puzzle
  and Game Corner; Pack, TM/HM Case and Apricorn Box included. No wrong input
  masks or register-clobber failures. Native return, movement and bicycle checks
  also pass.
- All 82 review-save moves verified through loaded dynamic IDs, linked name
  bytes and PP in each of three ROMs, plus native PC deposit/withdraw.
- 23 host unit tests, including clock wrap, late work, fractional distribution,
  bounded phases and private source-patch scope.

The unselected primary scripts differ by less than one interval in paired
median duration. Only Vine Whip/player exceeds 0.1 interval: approximately
0.464 interval faster. Its logical signature is unchanged; this is a small
display-boundary/starting-phase difference, not a newly assigned pacing target.
Whole battle wrappers can differ with damage/RNG and sound waits and are not
used as the assertion for unselected animation timing.

An initial runner assumption expected Volt Tackle always to return to the turn
menu. Recoil can end that turn/battle. The harness now recognizes native
animation completion for it, like Wild Charge, and the affected comparisons
were rerun. This required no cartridge gameplay fix.

## Exact Cartridge Costs

These are linked deltas against the accepted double-speed baseline, including
the temporary hold/late counters:

| Resource | Added | Remaining |
| --- | ---: | ---: |
| ROM0 | 8 bytes | 539 bytes |
| ROMX | 230 bytes | 712,984 bytes across 185 mapped banks |
| WRAM0 | 0 | 13 bytes |
| WRAMX | 10 bytes in bank 5 | 4,718 bytes across seven banks |
| HRAM | 0 | 0 |
| VRAM / OAM slots | 0 | Unchanged |

ROMX is 137 helper bytes, a three-byte reset call and 90 bytes of inline
records. The existing delay call and dummy opcode-table entry are replaced
without growing. No new ROMX bank is needed. Bank 5 uses five functional pacing
bytes, a one-byte instrumentation phase tag and four instrumentation counter
bytes. Its new
range is `$d4c2-$d4cb`, leaving 52 bytes before the fixed `$d500` section.

The two counter increments add 24 CPU T-cycles to each affected VBlank handler,
12 normal-speed-equivalent T-cycles while the CPU is doubled. Exact native
timing measurements include this overhead. Other users of `hVBlankCounter`
were audited; the broader menu/puzzle/Dex/cry tests guard its shared usage.

Complexity is modest: one shared gate, one inline command and bounded records,
with no new tile staging or second engine. Principal risks are motion cadence,
incorrect phase boundaries, a clock missing increments and audio starting at
undesirable points relative to the resampled motion. Counter instrumentation
and paired native state/clip tests make those risks observable. Caustic's
geometry problem remains independent.

## Manual Review Package

`build/battle-pacing-20261004/manual-review/` contains normal, accepted unpaced
double and paced ROMs with byte-identical starting battery files and matching
symbols. Boot and Continue; do not load an old CPU state. The user's live save
has not been edited. Start in Cherrygrove Pokecenter with six level-30 Pokemon:

| Party | Nickname | Species | Moves |
| --- | --- | --- | --- |
| 1 | WATER | Kyogre | Surf, Water Pulse, Caustic, Thunderbolt |
| 2 | PACE | Garchomp | Dragon Dance, Superpower, SolarBeam, Dazzling Gleam |
| 3 | CHARGE | Rayquaza | Shock Wave, Wild Charge, Volt Tackle, Energy Ball |
| 4 | CONTROL | Dusknoir | Shadow Ball, Petal Dance, Thundershock, Fire Blast |
| 5 | LEAVES | Meganium | Razor Leaf, Magical Leaf, Seismic Toss, Earthquake |
| 6 | HEAVY | Metagross | Hydro Pump, Overheat, Meteor Dive, Aerial Crash |

The remaining review moves are on 15 Pokemon in Box 14, ANIMS. The generated
`animation-review.json` lists every assignment. Deposit a party Pokemon before
withdrawing a boxed one. PP is usable; these are test movesets, not legal
learnsets. Review all four WATER moves, then all PACE/CHARGE moves and Shadow
Ball. Compare Petal Dance as an intentionally unchanged control. Watch orbit
cadence, ring travel, bubble-pop overlaps, stationary tails and SFX endings.

## Evidence and Reproduction

Private evidence lives in `build/battle-pacing-20261004/`: `timing.json`,
`state-comparison.json`, `regression.json` (initial paced full pass; subsequent
runs use `regression-paced.json`),
`regression-final.json`, Dex regression summary, audio reports, menu reports,
review-save verification and `visuals/analysis.json`. The clips and matched-state
PNGs are in `visuals/`. Large generated raster frames, audio and logs are
losslessly archived with digest verification; they are not deleted without a
verified retained copy. Build output remains ignored.

Build and primary testing recipes:

```sh
python3 tools/build_battle_pacing_prototype.py --output build/battle-pacing-20261004/prototype-v1
python3 -m tools.dex_timing.battle_pacing --jobs 24
python3 -m tools.dex_timing.battle_pacing --regression --variants paced --jobs 24
python3 -m tools.dex_timing.battle_pacing --regression --variants final --jobs 24
python3 -m tools.dex_timing.battle_pacing_visuals
python3 -m tools.dex_timing.battle_pacing --audio-regression --jobs 24
python3 -m tools.dex_timing.battle_pacing --menu-regression --jobs 24
python3 -m tools.dex_timing.battle_pacing --manual-review
python3 -m unittest tools.test_battle_pacing tools.test_dex_performance
```

The builder refuses to patch an existing candidate unless explicitly relinking;
use a fresh output when recreating sources. The runner's private variant path
must point at that output. Dex fixtures were prepared with
`performance.prepare` using this private ROM/symbol pair and the existing
private test battery, then the complete `performance_regression` suite was run
with `--expected-double-speed --jobs 24`.

ROM SHA-256 values:

- Normal production: `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.
- Accepted unpaced double: `5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90`.
- Paced prototype: `565e9c6be0ece9479eaa9e2dff9e1bb66f2a24bae55c6bc10f724c8261b4dc95`.

## Recommended Next Decision

First judge this prototype's cadence visually. A close total duration is not
enough to accept it. If sample repetition feels acceptable, use per-caller
charge targets and narrower motion/idle boundaries; those fit the same small
record format. If orbit/ring motion visibly pulses, consider controller-level
fixed-point step scaling for those specific effects while retaining shared
pacing only where repeating samples looks natural. Investigate Caustic's OAM
population/priority separately rather than expecting timing alone to remove it.

No production promotion is recommended before that review.
