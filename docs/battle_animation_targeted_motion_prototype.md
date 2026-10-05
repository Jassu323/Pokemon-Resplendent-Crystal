# Targeted battle motion at double speed

2026-10-04. Private follow-up to the rejected
[shared phase-pacing trial](battle_animation_phase_pacing_prototype.md) and the
[production timing investigation](global_double_speed_animation_pacing.md).

**Status: historical private trial. Its Surf cleanup regression is corrected in
the [expanded follow-up](battle_animation_expanded_motion_prototype.md).
Neither trial is production or a universal patch.**
The accepted unpaced whole-game double-speed ROM remains the baseline. Neither
it nor the production game source/cartridge was altered. There is no new shared
animation gate, global wait, timer adjustment or CPU-speed switch.

Follow-up: the user accepted all effects except Surf. The original measurements
below describe the retained intermediate-Surf trial, not the latest ROM.
The [Surf and battle intro revision](#surf-and-battle-intro-revision) restores
Surf's production-duration target and corrects a separately reproduced slide
publication defect. The user has accepted its motion timing and intro, but
identified a persistent sliced battle scene after Surf. The
[Surf teardown diagnosis](#surf-teardown-diagnosis) below records the confirmed
cause and proposed correction as recorded at that stage. The same-update
correction is now applied and native-regressed in the expanded private build;
the original measurements below remain unchanged historical evidence.

## Findings and recommendation

The useful direction is to author the timing of individual effects while
keeping the animation engine, backgrounds and audio serviced normally. Matching
an entire cutscene's duration does not ensure that its moving objects, pose
changes, launches and impacts have the right rhythm. The rejected trial proved
that holding the shared update can make a correct total look wrong.

This candidate separates those components:

- Water Pulse: slower continuous ring/bubble travel, appropriately extended
  pose lifetimes, and separately retimed launch and impact-phase spacing.
- Charge effects: smaller fractional radial increments, coordinated frameset
  lifetimes, and appropriate script phase lengths. Their movement is not frozen
  on alternating display intervals.
- Caustic: separate launch spacing and per-bubble flight-to-pop progression;
  the existing sound/pop/droplet callback stays attached to the actual impact.
- Dragon Dance: continuous angle/radius samples instead of holding the shared
  loop; preserve its six initial phases and native trigonometric rendering.
- Surf: deliberately intermediate wave ascent/retreat timing, not the full
  normal-speed duration and not the unpaced double-speed duration.

The candidate matches the production **player-side primary duration** to within
about one display interval for the six normal-target moves. Surf is about 62
intervals faster than production, in the requested 60-65 interval range. Both
sides now follow approximately the same primary timing; the old opponent-side
CPU penalty is not an intended target.

Recommend manual comparison of this local-motion candidate before extending
the approach to other moves. Duration and control-flow checks passed, but there
are known presentation differences below. Do not promote it solely because the
total duration matches.

## Reference method

SameBoy CGB-E runs three real, separately linked ROMs:

1. Current production, normal speed.
2. Accepted unpaced whole-game double-speed prototype, called `final` in data.
3. This targeted-motion prototype, called `targeted` in data.

The observer is host-only. It records primary/follow-up script spans, script
counters, every active object structure, BG-effect structures, inclusive
routine costs, shadow and hardware OAM, sound dispatches, real rendered frames
and recorded stereo audio. It does not insert cartridge instructions, emulate
additional waits or force a frame to be ready. Physical time is normalized to
the LCD clock, not CPU instruction count.

The focused matrix is 15 moves x 2 sides x 4 starting offsets x 3 ROMs =
**360 cases**. Offsets are 0, 17,556, 35,112 and 52,668 normal-speed T-cycles.
Seven moves are retimed; eight others check shared function isolation:
Thunderbolt, Petal Dance, Thundershock, Shock Wave, Wild Charge, Volt Tackle,
Energy Ball and Shadow Ball. They are **not retimed** in this candidate.

Each ROM gets a native matching-link battle checkpoint, then controlled move
allocation and side selection. Natural donor encounters differ between arms
(Pidgey, Hoppip and Poliwag in the displayed examples). Consequently these are
not pixel-identical combatant comparisons. Source object trajectories, counts,
four-phase medians and identical completed states on unchanged moves provide
the stronger controls. This is not exhaustive coverage of all battle/RNG/
weather/branch combinations or physical hardware qualification.

One display interval is 70,224 normal-speed T-cycles, **16.742706 ms**, about
59.7275 Hz. Fractional measurements locate code entry/return within an interval;
the panel still displays whole physical refreshes.

## Measured primary durations

Median first `RunBattleAnimScript` span across four offsets. Each timing cell
is **display intervals / milliseconds**. This is the primary animation, not
button-to-next-menu latency. Setup, HUD restoration, follow-up hit scripts and
`WaitSFX` are reported separately afterward.

| Move / side | Production | Unpaced double | Targeted double |
| --- | ---: | ---: | ---: |
| Surf / player | 377.01 / 6312.2 | 193.04 / 3232.0 | 315.03 / 5274.5 |
| Surf / foe | 379.03 / 6345.9 | 193.06 / 3232.3 | 315.01 / 5274.2 |
| Water Pulse / player | 241.06 / 4036.0 | 159.03 / 2662.7 | 241.02 / 4035.4 |
| Water Pulse / foe | 247.93 / 4151.0 | 159.03 / 2662.6 | 241.02 / 4035.4 |
| Dragon Dance / player | 156.06 / 2612.9 | 146.02 / 2444.8 | 156.03 / 2612.3 |
| Dragon Dance / foe | 165.06 / 2763.5 | 146.05 / 2445.2 | 156.03 / 2612.3 |
| Caustic / player | 216.10 / 3618.1 | 202.02 / 3382.4 | 216.04 / 3617.2 |
| Caustic / foe | 230.10 / 3852.6 | 202.02 / 3382.4 | 216.02 / 3616.8 |
| SolarBeam charge / player | 207.99 / 3482.4 | 173.98 / 2913.0 | 208.01 / 3482.7 |
| SolarBeam charge / foe | 215.02 / 3600.0 | 174.01 / 2913.4 | 207.99 / 3482.3 |
| Dazzling Gleam / player | 256.06 / 4287.1 | 224.02 / 3750.7 | 256.02 / 4286.5 |
| Dazzling Gleam / foe | 269.05 / 4504.7 | 224.02 / 3750.7 | 256.02 / 4286.5 |
| Superpower / player | 317.08 / 5308.8 | 244.02 / 4085.5 | 318.04 / 5324.9 |
| Superpower / foe | 323.08 / 5409.2 | 244.03 / 4085.8 | 318.03 / 5324.8 |

Whole `_PlayBattleAnim` wrappers, including native setup/restoration/audio
waits and follow-ups, in intervals:

| Move / side | Production | Unpaced double | Targeted double |
| --- | ---: | ---: | ---: |
| Surf / player | 446.00 | 316.46 | 384.00 |
| Surf / foe | 453.00 | 322.51 | 385.00 |
| Water Pulse / player | 315.00 | 234.00 | 306.50 |
| Water Pulse / foe | 325.04 | 238.98 | 313.00 |
| Dragon Dance / player | 195.88 | 185.95 | 194.45 |
| Dragon Dance / foe | 203.86 | 184.95 | 195.94 |
| Caustic / player | 288.00 | 267.00 | 280.50 |
| Caustic / foe | 303.00 | 271.00 | 284.00 |
| SolarBeam charge / player | 240.95 | 202.48 | 235.98 |
| SolarBeam charge / foe | 250.96 | 201.46 | 234.98 |
| Dazzling Gleam / player | 325.00 | 290.50 | 320.50 |
| Dazzling Gleam / foe | 345.01 | 294.48 | 324.98 |
| Superpower / player | 390.00 | 311.01 | 389.00 |
| Superpower / foe | 400.98 | 315.51 | 389.50 |

A faster wrapper with a matching primary is expected when incidental setup,
hit/HUD work and publication stalls remain faster. It is not automatically a
missing visible animation phase. SolarBeam's firing turn remains separate; its
phase-zero completed firing states match the unpaced double-speed reference
on both sides.

## Why the phases need separate treatment

Illustrative phase-zero **player-side** object lifetimes, in physical intervals:

| Component | Production | Unpaced double | Targeted double |
| --- | ---: | ---: | ---: |
| Water Pulse rings | 60.1-70.1 | 33.9-34.2 | 63.9-64.5 |
| Water Pulse scatter/path bubbles | 37.3-71.8 | 18.7-48.7 | 37.8-72.7 |
| Water Pulse target bubbles | 42.8-59.4 | 32.6-32.8 | 47.7-59.5 |
| Dragon Dance orbit objects | 87.0 | 79.7 | 91.6 |
| SolarBeam inward orbs | 111.1 | 78.7 | 109.6 |
| Dazzling Gleam inward orbs | 108.3 | 78.6 | 106.7 |
| Superpower inward orbs | 146.1 | 78.8 | 144.7 |
| Superpower chips | 109.0-162.2 | 82.6-107.8 | 108.7-161.6 |

The same native charge function experiences different production workloads
depending on the surrounding effect. One global multiplier would be wrong for
these three moves. Lifetimes include observed creation/deletion and script
clears; they are not independent authoritative design specifications.

Inclusive routine measurements further identify the incidental stalls. These
are fractions of a display interval, not isolated bare instruction costs:

| Player-side routine | Production median / max | Unpaced double median / max | Targeted median / max |
| --- | ---: | ---: | ---: |
| Surf BG effects | .389 / 1.666 | .141 / .461 | .138 / .461 |
| Surf OAM construction | .652 / .985 | .171 / .179 | .173 / .185 |
| Water Pulse OAM construction | .596 / 1.761 | .213 / .424 | .218 / .532 |
| Caustic OAM construction | .474 / 1.336 | .205 / .378 | .208 / .439 |
| Superpower OAM construction | .508 / 1.294 | .215 / .471 | .254 / .587 |

OAM costs contain object updates, framesets and nested trig calls; do not add
those nested measurements again. BG/graphics initialization can include LCD
transfer waits. This is why restoring every old missed boundary would recreate
unwanted work stalls, not just desired motion rhythm.

## Private implementation

The build uses existing object-owned `VAR1`/`VAR2` bytes for ages, fractional
progress or initial position. Thirty compact ROMX tables contain two-byte
samples with a one-byte length header, totaling 4,114 payload bytes. A 32-byte
reader looks up one sample per object update. Bank switches use existing far
calls; no new generic scheduler or memory owner is introduced.

Production reference positions are interpolated over chosen physical-length
targets. Signed offsets are interpolated as signed values; absolute X remains
unsigned. Angles are unwrapped before interpolation and wrapped only on output.
These safeguards prevent a signed coordinate or angle crossing from becoming
an unintended traverse across the screen. The tables contain motion, not whole
OAM frames or screenshots. Runtime still constructs OAM, performs native side
transforms and publishes palettes/backgrounds normally.

These ages still count completed native updates; this is **not** a new
hardware-clock deadline/catch-up scheduler. The current double-speed captures
verify one update per display interval during the retimed motion. Adding other
heavy runtime work later requires requalification; the table reader cannot
recover a missed refresh automatically. Its purpose here is explicit local
motion authoring without deliberately skipping otherwise available updates.

Selected local changes:

- **Surf:** five-of-eight vertical progress, with ascent/hold/recede script
  phases lengthened. Horizontal wave oscillation and BG tile rotation still use
  the faster normal double-speed update cadence. Manual review must assess that
  separately from the overall 315-interval target.
- **Water Pulse:** five scatter curves, eight supported drift directions,
  64-interval ring travel and four target-bubble curves. Ring launches have
  their own shorter spacing, separate from the later path-bubble phase. Ring,
  path and target frameset durations are coordinated with these lifetimes.
  The Whirlpool background continues regularly, without reproducing the old
  CPU-limited distortion cadence. This visual difference is deliberate, not
  evidence of pixel-identical production playback.
- **Dragon Dance:** a 92-sample angle/radius curve retains six phase offsets;
  native sine/cosine render each update. Orb pose durations and the later script
  hold change locally. The initial electricity subscript remains faster, so its
  first warp sound is still around interval 61 versus 70 in player production
  (81 on the foe). The second is around 102 versus 101 player production. This
  trial does **not** claim exact restoration of every Dragon Dance phase.
- **Caustic:** uniform 12-interval launches and three flight lengths of
  63/64/68 intervals, with side-specific geometry but no inherited foe delay.
  Native pop frameset, `SFX_TOXIC` dispatch and droplet callback remain local to
  the actual bubble state transition. Droplet motion itself is not retimed.
- **SolarBeam / Dazzling Gleam / Superpower:** radial increments become
  91/256, 94/256 and 69/256 pixels per update rather than the common 128/256.
  Charge-orb and center framesets receive move-specific lifetimes. Script holds
  become 138/176/the separately phased Superpower charge. Superpower chips and
  its local impact helper are retimed too; the shared hit helper is untouched.

The ordinary frameset namespace is nearly full, so this trial avoids allocating
new frameset IDs. A small hook selects changed durations only when loading a
new regular pose and only for selected move/frameset combinations. Extended
framesets and unrelated moves retain native duration values. This adds some
routine overhead even to rejected matches; the regression measures its effect.

Old selected function bodies are replaced rather than retained beside unused
copies. The private source differs from the accepted baseline in nine ASM
files, including three new motion files and their include; no production ASM
file is changed in the working tree.

## Caustic: both launch and pop sounds

Both components were explicitly captured, not just the impact callback.
Every focused replay has nine bubbles, **nine launch SFX** and **nine pop SFX**.
The target launch events are approximately 5,17,29,41,53,65,77,89,101 intervals
from primary-script entry. Sounds accompany each actual spawn, not a separate
hard-coded audio timeline.

Representative player-side sound dispatch positions, rounded to intervals:

| Sequence | Production | Targeted double |
| --- | --- | --- |
| Launches | 6,17,28,39,50,62,74,88,103 | 5,17,29,41,53,65,77,89,101 |
| Pops | 69,81,96,110,123,135,146,157,168 | 69,82,98,105,118,134,141,154,170 |

The target is a coherent uniform launch rhythm and lane-specific travel, not an
exact copy of the late-sequence workload stalls. This explains the remaining
differences between individual pop positions even though total duration matches.
The target foe sequence is now essentially the same timing as the player.

The callback occurs before OAM construction/publication. At phase zero target
pop sounds precede their completed shadow state by up to .40 interval. Matching
whole hardware-OAM states are normally observed around 1.81-1.91 intervals
after pop dispatch. Launch states similarly pass through the native publication
pipeline (about 1.88-1.90 for subsequent launches; the startup is different).
These are **dispatch-to-completed-frame observations**, not precise audible
sample-onset measurements or the first pixel on a scanline. Native sound service
also occurs after dispatch. Do not call the sound and visible pop simultaneous
merely because the callback is shared. Recorded sound clips preserve that
relationship for the requested manual review.

No new audio delay/padding gate is introduced. Launch/pop sounds may preempt
each other on their native SFX channels, as before. Consequently there is no
claim that Caustic's resulting PCM is byte-identical to production.

**Crowding is still present.** Phase-zero peak OAM candidates per scanline:
production player 16, unpaced double player 16, targeted player 14; foe 12 in
all three. Target crowded completed updates fall from 26 to 21 on the player
and from 4 to 2 on the foe. The hardware limit is ten. Retiming can obscure
dropouts or reduce overlap but is not a hardware-limit fix. Inspect the pop and
droplet overlap visually; leave geometry/particle-count redesign separate if
the dropout is unacceptable.

## Cadence and visual qualifications

In the focused target captures, consecutive completed animation updates are one
display interval apart for all selected moves except the existing 17-interval
Superpower graphics/actor-picture handoff. The same handoff exists in both
baselines; a roughly 16-interval command span accounts for it. It is not a new
shared pacing hold. This report does not promise that every authored pose changes
every refresh: integer pixel quantization, long center poses, flashes and native
blink frames still repeat pictures intentionally.

Seven physical-time contact sheets were inspected. They show continuous
phase progress and no early center deletion in the final candidate. An earlier
private trial extended orb travel without extending center lifetime, exposing a
gap; it was corrected before this final ROM and all final qualification runs.
Blink/size-pose boundaries can still differ by a few intervals from production.
Contact sheets and state traces are not substitutes for viewing the motion and
hearing its rhythm. In particular, assess Water Pulse, charge smoothness,
Dragon Dance's early first warp, Surf's retained faster oscillation and both
Caustic sound phases before accepting this direction.

Thunderbolt remains the **unpaced double-speed** version (about 220 primary
intervals), not the 232-interval gated version from the rejected trial. Petal
Dance retains its accepted faster motion. Other charge users are regression
controls, not silently changed to the three selected charge rates.

## Linked costs

Measured relative to the accepted unpaced double-speed ROM:

| Allocation | Net change |
| --- | ---: |
| New ROMX bank `$ba`, motion tables + reader | +4,146 bytes |
| Existing Battle Animation Function Bank | +60 bytes |
| Move Animations frameset hook | +10 bytes |
| Battle Animation Scripts | +25 bytes |
| **Total ROMX payload** | **+4,241 bytes, about 4.14 KiB** |
| ROM0 code | **0** |
| WRAM0 / WRAMX / HRAM | **0 / 0 / 0** |
| VRAM / additional OAM slots | **0 / 0** |

One 16 KiB ROMX bank is assigned, leaving 12,238 bytes for later use in it.
The ROM0 binary differs only at its two cartridge-global checksum bytes; all
ROM0 instructions are identical to the accepted double-speed baseline.

The targeted linked totals are 15,837 ROM0 bytes (547 free), 2,322,067 ROMX
bytes across 186 occupied banks, 4,083 WRAM0 bytes (13 free), 23,944 WRAMX bytes
(4,728 free across seven banks), and 127 HRAM bytes (none free). These are linker
totals, including unrelated existing systems; free space can be fragmented.

Complexity is moderate: localized motion readers and frameset/script changes,
plus production-reference generation. Main risks are signed coordinates,
side transforms, reused object workspace, shared-frame duration isolation and
maintaining data when an animation is later rewritten. Regenerate/reference
review is required for edited motions; these tables are not a permanent automatic
retiming system for arbitrary future scripts. Relative to a broad shared gate,
the behavior is more explicit but requires per-effect authoring and review.

## Final regression results

All results below are fresh runs of the final targeted ROM, not borrowed from
earlier qualification:

- **360 focused move/side/phase/ROM cases:** no execution/playback miss.
- **640 broad native battle cases:** 80 moves, both sides, four offsets; no
  animation/sample-cache miss, wrong-speed state or failure to finish.
- **584 unchanged-move cases:** every completed delay/parameter/shadow-OAM state
  matches the unpaced double-speed reference, ignoring relocated script PCs.
  Vine Whip varies by about one physical interval in four cases despite identical
  logical states; the observed range is -1.002 to +1.023 intervals. The other
  unchanged cases do not show a comparable primary change. Do not claim exact
  physical timing invariance from logical equality alone.
- **480 audio cases:** 20 species x six contexts x four offsets, covering Party
  Stats, catch/New Entry, faint, player send-out, blocking and stereo cries.
  Sample counts, wave-block content hashes, CH3 frequency and timer configuration
  match the unpaced double-speed baseline; no cache misses. A comparison bug
  initially treated live tuple timer records as unequal to JSON list records;
  canonicalizing the comparison removed the false flags without changing game
  code. This does not assert identical IRQ-entry timestamps or full PCM.
- **6,182 Dex cases:** all 373 species cold/paging; Info 1,492, Moves 746,
  cold 373, paging 373, Area 2,238, Info stress 400 and Moves stress 560. No
  failures, with exact animation publication targets checked by the existing
  scheduler audit.
- **8,254 New Entry cases:** 80 full completions plus 8,174 input/phase cases
  over 20 species, including cancellation combinations; no failures.
- **896 menu inputs** over five locations (standard, battle, mart, puzzle,
  Game Corner): no wrong masks or register failures.
- **Three manual-review save arms:** boot/Continue verified, 82 real moves with
  linked names/PP checked, and native PC deposit/withdraw verified.
- **Seven host unit tests:** signed/mixed coordinates, unwrapped angles,
  curve bounds/payload, no new clock/workspace and audio JSON roundtrip pass.
  The ten existing phase-pacing tests and thirteen performance tests also pass
  (30 host tests total).

These tests do not resolve the already logged battle-menu glyph corruption,
switch-menu flash or Glacial Slam sprite slicing. Nor do they replace the user's
manual aesthetic acceptance or a physical-console test. There was no reason to
alter animation speed elsewhere or re-label the previous entire-game audit as a
new exhaustive run.

## Manual review package

All generated files are under the ignored
`build/battle-motion-reference-20261004/` directory:

```text
manual-review/targeted/pokecrystal-animation-targeted.gbc
manual-review/targeted/pokecrystal-animation-targeted.sav
manual-review/normal/pokecrystal-animation-normal.gbc
manual-review/normal/pokecrystal-animation-normal.sav
manual-review/double/pokecrystal-animation-double.gbc
manual-review/double/pokecrystal-animation-double.sav
visuals/<move>-<player|foe>-comparison.mp4
visuals/<move>-<player|foe>-<production|final|targeted>.mp4
visuals/<move>-contact.png
```

Use the paired ROM/save in its own folder and Continue. These are copies for
review; the live `/Applications/SameBoy/Games/pokecrystal.sav` is untouched.
Start in Cherrygrove's Pokemon Center. The first two party members contain every
retimed move so there is no PC hunt:

| Pokemon / nickname | Moves |
| --- | --- |
| Kyogre / WATER | Surf, Water Pulse, Caustic, Thunderbolt |
| Garchomp / PACE | Dragon Dance, Superpower, SolarBeam, Dazzling Gleam |
| Rayquaza / CHARGE | Shock Wave, Wild Charge, Volt Tackle, Energy Ball |
| Dusknoir / CONTROL | Shadow Ball, Petal Dance, Thundershock, Fire Blast |
| Meganium / LEAVES | Razor Leaf, Magical Leaf, Seismic Toss, Earthquake |
| Metagross / HEAVY | Hydro Pump, Overheat, Meteor Dive, Aerial Crash |

Other previously requested moves remain in Box 14, `ANIMS`. In particular Hydro
Pump, Superpower and Fire Blast are verified real moves, not invalid dynamic IDs.

Prioritize:

1. Water Pulse's launch spacing, travel smoothness and transition into its
   target bubbles, with the background distortion running independently.
2. Charge-orb travel and center growth on SolarBeam, Dazzling Gleam and
   Superpower. Look for stutter, a lingering unmoving orb or an unexplained gap.
3. Caustic **launch sounds as well as every impact/pop sound**, watching the
   later overlap with droplets. The sounds are not expected to reproduce every
   production stall, but should fit the deliberately retimed motion.
4. Surf's intermediate overall pace and separate wave oscillation; Dragon
   Dance's visible orbit and the two warp sounds.
5. Petal Dance and other controls should retain their faster baseline behavior.

The 14 three-column comparisons are silent, aligned to primary script start;
finished arms are explicitly padded/labeled. They are not input-latency videos.
The **42 individual clips have sound** and include a short pre/post roll.
Use those for Caustic sound review rather than the silent composites.

## Evidence and reproduction

Generated evidence:

- `reference.json`: full per-object reference and all focused timing rows.
- `phase-audit.json`: object counts/lifetimes, scanline crowding, sound vectors,
  ready/hardware publication correspondence and active update gaps.
- `work-audit.json`: inclusive command/BG/OAM/trig/GFX/wait costs.
- `regression/comparison.json`, `audio/comparison.json`,
  `dex-regression/summary.json`, `new-entry-regression/report.json`,
  `menus/report.json`, `manual-review/verification.json`: final checks.
- `replays/`: raw native events, audio, frames and matching checkpoints.
- `prototype/provenance.json`, `costs.json`: unchanged baseline hashes and costs.

Builder `tools/build_battle_motion_prototype.py` works only in its private
checkout; patch templates are under `tools/dex_timing/probes/battle_motion_*.asm`.
Reference data is required to generate the tables. Regenerating from different
animation source is a new trial, not an identical build.

```sh
python3 -m tools.dex_timing.animation_reference --variants production final --jobs 24
PYTHONPATH=.:tools python3 tools/build_battle_motion_prototype.py --jobs 24
python3 -m tools.dex_timing.animation_reference --variants targeted --jobs 24
python3 -m tools.dex_timing.animation_reference --variants targeted --regression --jobs 24
python3 -m tools.dex_timing.battle_motion_qualification audio --jobs 24
python3 -m tools.dex_timing.battle_motion_qualification menus --jobs 24
python3 -m tools.dex_timing.battle_motion_qualification dex-prepare --jobs 24
python3 -m tools.dex_timing.performance_regression --config build/battle-motion-reference-20261004/dex-setup/config.json --output build/battle-motion-reference-20261004/dex-regression --expected-double-speed --jobs 32
python3 -m tools.dex_timing.performance_entry --audio build/battle-motion-reference-20261004/audio --output build/battle-motion-reference-20261004/new-entry-regression --input-variant targeted --jobs 24
python3 -m tools.dex_timing.animation_reference_audit
python3 -m tools.dex_timing.battle_motion_qualification manual
python3 -m tools.dex_timing.animation_reference_visuals
python3 tools/test_battle_motion.py
```

Existing private checkouts require `--relink`; the builder deliberately refuses
to overwrite one. Raw loose frames/audio can be losslessly archived after video
generation with `animation_reference_visuals --archive-frames`; it verifies
SHA-256 equality before removing loose copies. To re-encode afterward, unpack
each `rendered-frames.tar.gz` and `audio.raw.gz` into its original replay folder.
Videos, events, results and reference tables remain intact.
The final preservation pass verified those archives and reclaimed about
3.35 GiB of redundant loose frames/audio.

Baseline identities:

```text
production 7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666
double     5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90
targeted   0a27acec515b38494c33171c06f61ffb169e5d09286b7cd33d11157c1050a2e6
```

## Surf and battle intro revision

2026-10-04, following manual review. Water Pulse, Dragon Dance, Thunderbolt,
Caustic and the charge effects passed the user's review. Surf's intermediate
target did not: its rise/return balance was objectionable. Restore the
production target instead of preserving the former 60-65-interval saving.
The user also reported a stuttering wild-battle slide at double speed.

This revision is **a separate private ROM**, `surf-intro` in saved data.
Production, the accepted unpaced global-speed baseline and the original
targeted-motion review package remain untouched. The six previously approved
retimed effects have no source changes.

### Surf correction

The local step accumulator changes from 5/8 to 1/2. A rise step is one pixel;
a retreat step is two pixels, matching the native function. Surf's local
angle/X-offset advancement and BG wave rotation also advance once every two
completed updates, reproducing their production cadence. This does **not**
skip the shared animation loop, other objects, frameset processing, palette
service or sound updates.

The four sound/script phases use `anim_wait 66`, and the final wait is 104.
These are measured physical-duration targets, not blindly doubled byte values:
the native command includes a yield, and production's final section is not
uniformly CPU-bound. The longer object progression and script envelope must
be changed together.

Median primary-script measurements over four starting offsets:

| Side | Production | Previous intermediate trial | Revised |
| --- | ---: | ---: | ---: |
| Player | 377.014 / 6312.230 ms | 315.032 / 5274.487 ms | 376.990 / 6311.827 ms |
| Opponent | 379.026 / 6345.913 ms | 315.015 / 5274.204 ms | 377.039 / 6312.658 ms |

Cells are display intervals / milliseconds. The revised sides are intentionally
consistent; the production opponent's extra CPU delay is not reinstated.
The rise's first-to-last observed phase span is 193.579 intervals versus
193.693 in production, player-side. The retreat is 104.792 versus 101.422.
The crest hold is 71.996 versus 65.878; initialization is quicker in the
prototype. Thus **this is not an instruction-by-instruction or pixel-phase
replica** despite matching the primary total. It restores production motion
rates and approximately the envelope without imposing a whole-engine stall.
Manual review remains necessary. Full phase endpoints, samples and sound
spacings are in `surf-intro-qualification/motion-audit.json`.

### Slide diagnosis and correction

Reproduction: start a grass encounter at double speed and watch the static foe
picture slide in. The foe occasionally repeats a position, then advances four
pixels. The trainer OAM's two-pixel progression is already regular. Joey's
trainer portrait has the same BG-side defect.

`BattleIntroSlidingPics.loop2` previously admitted **every LY >= 96**, including
VBlank (144-153). At normal speed, producer work generally carries execution
past that window into the next visible frame, and the code waits to line 96.
At double speed, earlier completion sometimes admits a scroll-table update in
VBlank instead. The next live scanline table and the already committed OAM do
not then have the intended publication relationship. Variable entry phase
produces apparent holds/jumps, even though total duration remains about 74
intervals and the logical slide increments are still two pixels.

In the uncorrected double-speed Dusknoir q0 replay, 29 of 73 scroll-step entries
occur on line 152; another reaches the step body at line zero after crossing
the frame boundary. Production has 72 entries on 96 and one on 110. With the
correction, all 73 are on 96. This is a missing upper bound, not a decision to
slow an animation, add a phase target or change the producer architecture.

The private patch is:

```asm
.loop2
    ldh a, [rLY]
    cp LY_VBLANK
    jr nc, .loop2
    cp $60
    jr c, .loop2
```

The remaining scroll writes, OAM step, producer servicing, transfer ownership,
`DelayFrame`, iteration count and final setup are unchanged. Staging occurs
after the foe's upper visible rows have already been scanned and before the
next VBlank commits OAM. No new timer, interrupt or buffer is introduced.

### Intro A/B qualification

Three linked arms: production, Surf-corrected double speed **without** the
intro guard (`surf-production`), and the delivered `surf-intro` guard.
Eight species x four input-start offsets x three arms = **96 wild intros**:
Caterpie, Mewtwo, Dusknoir, Metagross, Luxray, Garchomp, Bastiodon and Weavile.
Native overworld walking and encounter initialization precede the captured
intro. Species allocation happens before `LoadEnemyMon`, not by injecting a
ready picture or changing PPU state. Four pre-encounter starting offsets are
not a claim of four independently chosen LY values at slide entry.
The final runs use alternating A presses/releases to dismiss the later text
and require reaching the actual `LoadBattleMenuGraphic.loop` checkpoint;
exhausting a frame budget while holding A is not accepted as menu completion.

Every rendered interval is captured. Above the trainer's sprites, the static
foe picture must translate two pixels right each interval. The comparison
excludes incoming edge pixels and the intro's first three setup displays.
Blank/cropped frames that match several translations are not classified as
stutters. The final transition away from the sliding layout is excluded.

| Arm | Wild pixel-cadence violations | Joey trainer violations |
| --- | ---: | ---: |
| Production | 0 | 0 |
| Double speed, guard absent | 648 | 30 |
| Double speed, guard present | 0 | 0 |

Joey adds three native trainer-intro runs, one per arm. The foe and player
pictures, producer completion and subsequent native battle menu are exercised.
Wild median slide duration is 73.976-73.979 intervals in production and
73.956-73.976 with the correction, approximately **1238-1239 ms**. Joey is
72.962 versus 72.977 intervals, approximately **1222 ms**. There is no meaningful
total-duration increase. This is specifically sliding-intro timing, not
overworld-button-to-complete-battle-menu latency.

### Costs and regression scope

Relative to the earlier targeted trial:

- Surf: +9 bytes in `bank32` for the local BG rotation divider, -2 bytes in the
  function bank for the local motion guards: **+7 ROMX bytes** net.
- Intro: **+4 ROMX bytes** in `bank13_2`.
- Total: **+11 ROMX bytes**, bringing the targeted changes to **4252 bytes**
  relative to the unpaced double-speed baseline. Existing 4114-byte curve
  payload and bank `$ba` are unchanged.
- **No ROM0 code, WRAM0, WRAMX, HRAM, VRAM or OAM allocation increase.** Existing
  Surf object/BG scratch fields are used, not new workspace.

The guard is low complexity and removes a timing assumption rather than adding
a new scheduler. Its main risk is an unexpected caller/producer phase forcing
an extra wait, so both producer-heavy wild intros and the trainer path are
tested. No extra interval is observed. It still relies on the existing LCD-on,
interrupt-enabled battle intro contract and does not redesign that contract.

Fresh delivered-build qualification, not inherited trial results:

- 120 focused animation cases, 15 moves x both sides x four offsets: no runner
  failures. The native rendered/audio Surf captures are retained.
- 640 broad battle cases, 80 moves x both sides x four offsets: no failures;
  **all 632 non-Surf cases have identical completed delay/parameter/shadow-OAM
  sequences to the earlier accepted local-motion trial**, ignoring relocated
  script PCs. Physical fractional timing can still move slightly with phase.
- 480 audio cases, 20 species x six owners x four offsets: no failures and no
  sample-content/timer/frequency changes against the unpaced double-speed arm.
- 896 menu-input cases across standard/battle/Mart/puzzle/Game Corner: zero
  wrong masks or register failures; overworld and bicycle checks also pass.
- Three private review-save arms boot/Continue successfully, verify all 82
  moves and PP and pass native PC deposit/withdraw.
- 30 existing motion/pacing/performance host tests pass.

The earlier exhaustive Dex/New Entry suites remain the previous revision's
evidence, not fresh runs here. This revision does not alter their scheduler or
type-icon/page code. It does not fix the separate deferred battle sampled-cry
owner issue, Caustic's known scanline capacity or the three production battle
visual bugs. Those remain logged independently.

### Review package and evidence

Updated ROM and matching save:

```text
build/battle-motion-reference-20261004/surf-intro-qualification/manual-review/surf-intro/pokecrystal-animation-surf-intro.gbc
build/battle-motion-reference-20261004/surf-intro-qualification/manual-review/surf-intro/pokecrystal-animation-surf-intro.sav
```

Kyogre (`WATER`) retains Surf/Water Pulse/Caustic/Thunderbolt. Garchomp (`PACE`)
retains Dragon Dance/Superpower/SolarBeam/Dazzling Gleam. The review box and
other party members are unchanged. Please review Surf's rise, crest and return
on both sides, and several wild slides; optionally check Joey's trainer slide.
The existing accepted effects should continue to look the same. No live user
save is changed.

Evidence below `build/battle-motion-reference-20261004/`:

- `wild-intro/report-production-surf-production-surf-intro.json` and individual
  event/rendered-frame captures; `wild-intro/trainer-*.json` for Joey.
- `surf-intro-qualification/motion-audit.json`, `audio/comparison.json`,
  `menus/report.json` and `manual-review/verification.json`.
- `surf-intro-qualification/visuals/`: separate player/foe Surf three-way clips,
  wild Dusknoir and Joey intro three-way clips. They are silent comparisons;
  completion padding is labeled, not counted as animation time.
- `visuals/surf-player-surf-intro.mp4` and `surf-foe-surf-intro.mp4`: updated
  single-arm Surf recordings with captured sound.

After creating the videos, the new native PPM/audio captures were losslessly
archived and SHA-256-verified before removing redundant loose copies, reclaiming
about **7.66 GiB**. Per-case `rendered-frames.tar.gz`, `audio.raw.gz`, structured
events, measurements and videos remain. The comparison generator reads archived
frames directly; individual sound-video re-encoding requires unpacking its
original frames/audio first.
Use `battle_motion_revision_visuals --comparisons-only` to regenerate the
archived-frame comparisons without unpacking the sound recordings.
The final press/release-to-menu rerun was also archived after re-encoding its
comparisons, reclaiming another 2.71 GiB of redundant loose intro frames.

Build/replay commands (repository root):

```sh
PYTHONPATH=.:tools python3 tools/build_battle_motion_prototype.py --surf-production --intro-visible --output build/battle-motion-reference-20261004/prototype-surf-intro --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.animation_reference --variants surf-intro --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.animation_reference --variants surf-intro --regression --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_intro_reference --variants production surf-production surf-intro --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_intro_reference --variants production surf-production surf-intro --trainer --jobs 3
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_motion_revision_audit
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_motion_qualification audio --variant surf-intro --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_motion_qualification menus --variant surf-intro --jobs 24
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_motion_qualification manual --variant surf-intro
PYTHONPATH=.:tools python3 -m tools.dex_timing.battle_motion_revision_visuals
```

Build `prototype-surf-production` with `--surf-production` but without
`--intro-visible` to reproduce the separate uncorrected-intro control. The
builder's default retains the original intermediate recipe for historical
reproduction. It refuses to overwrite an existing checkout; `--relink` only
rebuilds that checkout, and does not change its recipe.

Delivered ROM SHA-256:

```text
409521772354de086a5b6fd974ca0ae27f70209fa47a27fcb62fff148f88b57d
```

## Surf teardown diagnosis

Historical diagnosis of the broken `surf-intro` trial. The four-byte terminal
step correction is implemented in `surf-cleanup` and the later expanded private
builds. See [expanded retiming and acceptance](battle_animation_expanded_motion_prototype.md)
for current results; the "not yet implemented" wording below records the
original investigation, not the latest build's status.

2026-10-04, following manual review of `pokecrystal-animation-surf-intro.gbc`.
The revised Surf motion visually matches production and the battle slide is
accepted. The post-Surf battle scene, however, is horizontally sliced and
wrapped until another path resets the scanline handler. This is a regression
in the private production-duration Surf retargeting, not an instruction to
change production or abandon double speed.

### Reproduction and native results

Use Surf in the delivered private ROM, allow it to finish, and inspect the HUD,
sprites and battle menu after the wave retreats. Both attack directions
reproduce the dangling handler. A subsequent move with its own scroll cleanup
can mask it: an otherwise harmless opponent Splash sometimes resets the
handler, so a sequence ending with Surf is a stronger persistence control.
Caustic from a clean entry does not reproduce the defect.

The read-only headless diagnostic runs three unchanged ROMs, Surf/Caustic,
both sides and four starting offsets: **48 cases**. It extends menu observation
by 60 display intervals and observes the actual interrupt and WRAM ownership,
not merely the animation's duration or a final screenshot.

| ROM | Surf cleanup violations | Caustic cleanup violations |
| --- | ---: | ---: |
| Normal-speed production | 0/8 | 0/8 |
| Earlier intermediate-Surf targeted trial | 0/8 | 0/8 |
| Latest production-duration Surf/intro trial | 8/8 | 0/8 |

The new observer produces exactly the existing animation invocation timestamps
and durations in all **48/48** replays. Its assertions therefore do not cause
the failure. Seventeen targeted-motion/pacing host tests also pass. These
checks do not constitute qualification of a fix: no fix has been built.

One native persistence/recovery control executes Surf last in the turn,
waits at the battle menu and uses ordinary direction/A input to run away.
`hLCDCPointer` is `$42` before fleeing and zero on return to the overworld;
the rendered scene is restored. The overworld's
`ReanchorBGMap_NoOAMUpdate.ReanchorBGMap` explicitly clears that pointer.
This explains the user's observation that leaving battle repairs the scene.

### Exact cause

1. Surf uses the LCD interrupt to write `rSCY` (vertical BG scroll) separately
   on each scanline. `hLCDCPointer = $42` selects that register. Its intended
   per-line values live in `wLYOverrides`, WRAM bank 5.
2. `BattleAnimFunc_Surf.three` tests the Y coordinate **before** taking the
   next retreat step. At `Y >= $70` it clears the pointer and bounds and
   deinitializes the Surf object; otherwise `.move_down` advances Y.
3. The revised one-in-two divider plus `anim_wait 104` leaves the final update
   advancing Y from `$6f` (111) to `$71` (113). That update passed the old-Y
   threshold test, so it does not perform cleanup. There is no later object
   update before the script stops.
4. At the first player's primary script return in the diagnostic, the Surf
   object is still active in state 3, Y = `$71`, divider = zero. The cleanup
   entry was never reached. HRAM still contains pointer `$42`, start `$61`
   and end `$5e`. Production and the earlier trial reach cleanup once.
5. The animation interpreter does not promise another object update after
   the stop flag. Later `ClearBattleAnims` can clear the remaining object and
   WRAM animation buffers, but it does **not** clear this HRAM pointer.
6. HUD restoration and the outer `PlayBattleAnim` handoff select WRAM bank 1.
   The LCD handler explicitly assumes the active bank is `BANK(wLYOverrides)`;
   it neither switches nor validates that bank. With `$42` still enabled, it
   reads ordinary bank-1 game data as per-scanline vertical scroll offsets.

The first player's outer return retains `$42` with bank 1 selected. Actual
interrupt observations include line 10 reading value 36 from bank 1 where the
intended bank-5 value is zero. Thousands of these wrong-bank accesses continue
in the post-animation captures. The opponent-side post-menu screenshot
reproduces the sliced HUD/sprites, matching the reported failure class.

This is incorrect display-state ownership/teardown, not a wave that needs a
slower motion curve, a VRAM-capacity problem or insufficient double-speed CPU
time. Resetting `hSCY` alone is insufficient: the interrupt overwrites `rSCY`
again on subsequent scanlines while the pointer remains enabled.

### Recommended correction, not yet implemented

Finish Surf **on the same update that reaches the terminal retreat Y**.
Give the existing cleanup block a local label; immediately after storing the
new retreat Y, compare it with `$70` and branch to that block when finished.
Retain the existing pre-step threshold check as well.

Projected cost: `cp $70` plus `jr nc, .finish` is **four ROMX bytes** in the
Surf function's current bank. The label and reused cleanup add no payload.
No ROM0 code, WRAM0, WRAMX, HRAM, VRAM, OAM or motion-table allocation changes.
The script waits, one-in-two motion divider, wave rotation, SFX schedule,
accepted intro fix and all other moves remain unchanged. The last off-screen
wave update is removed as part of proper finalization; rendered cadence and
display-interval timing still need to be requalified in the corrected build.

Alternatives:

- Increase the final wait from 104 to 105. No additional ROM payload and about
  one extra display interval, but teardown still depends on a spare future
  update and a hand-maintained script/motion relationship. Less robust.
- Reset every animation's scanline ownership globally at interpreter exit.
  Broader protection, but affects other BG effects and their intended lifetime.
  This would need a separate ownership audit; it is unnecessary for this
  Surf-local boundary error.

The same-update local finalization is recommended. Test primary-script and
outer-owner cleanup, post-menu pixels, both directions/starting offsets and
Surf followed by other moves. Also preserve the existing timing/SFX/OAM
regressions. Do not use an opponent's later scroll cleanup as proof that Surf
cleaned up correctly.

### Validation gap and retained evidence

The previous zero-failure totals were runner/control-flow assertions, with
non-Surf completed-state parity checks. They did not assert Surf's HRAM cleanup
or the LCD handler's WRAM ownership after the changed terminal step. Total
duration can be correct despite this error. That missing lifecycle assertion
is now explicit in the diagnostic, and correctly reports all eight failures;
the earlier qualification must not be read as approving this ROM for promotion.

Host instrumentation is behind `DEX_SURF_CLEANUP_TRACE`, with no cartridge
instructions, memory writes or timing changes. The runner's optional
`post_menu_frames` is zero by default; only this diagnostic enables it.
No runtime source, prototype cartridge or production cartridge was changed.
The production and delivered-ROM hashes remain those recorded above.

Evidence directory:
`build/battle-motion-reference-20261004/surf-cleanup-diagnostic/`

- `report.json`: 48 comparisons, timestamp parity and native battle exit.
- `observers/<variant>/`: reproducible read-only observer configuration.
- `replays/<variant>/<move>-<side>-q<offset>/`: full compressed events,
  derived cleanup assertions and post-menu screenshots.
- `battle-exit/`: interrupted ownership observations and native before/after
  battle screenshots, plus event capture and final recovery result.

Reproduce without editing a ROM:

```sh
PYTHONPATH=.:tools python3 -m tools.dex_timing.surf_cleanup_diagnostic
```
