# Battle animation pacing at double speed

2026-10-04. Follow-up to the [whole-game qualification](global_double_speed.md)
and [79-move measurements](global_double_speed_animation_measurements.md).

**Original pass: diagnosis and implementation proposal, not a retiming patch.** The
accepted double-speed prototype remains the next baseline, not production.
Neither its ROM nor the production ROM/game source was changed in this pass.
The only implemented corrections are host-side profiling, the manual review
save builder, and documentation. The three user-reported graphical defects
are logged for later investigation.

The subsequent requested private retiming experiment is documented separately
in [Battle animation phase pacing prototype](battle_animation_phase_pacing_prototype.md).
It does not alter either baseline described by this original investigation.

## Current Direction After Visual Review

The user rejected the shared logical-update pacing trial: Water Pulse's motion
was unacceptable, charge effects stuttered, and Caustic's sound relationship
still differed. The accepted unpaced global double-speed prototype remains the
next baseline. The historical recommendation below is not approval to promote
that rejected trial.

The next proposed investigation is a phase-by-phase production reference for
Water Pulse, Surf, Dragon Dance, Caustic and representative charge effects
(SolarBeam, Dazzling Gleam and Superpower), on both attack sides. Correlate
script commands, motion/frameset progress, BG effects, actual published OAM,
visible onset/phase/end and sound dispatch/completion on the display timeline.
Separate authored holds from incidental CPU/publication delays. Then use those
references to choose deliberate motion/phase targets; do not reproduce every
old missed VBlank or indiscriminately freeze the entire logical update.

Potential implementations should adjust the relevant functions, framesets or
controller progression while keeping display/BG publication and audio service
regular. Whether interpolation or a slower phase accumulator is appropriate
must be decided per effect and visually tested, not assumed to be a universal
solution. Surf retains the user's intermediate target, while Water Pulse and
charge motion need coherent rhythm without inherited opponent-side penalties.
Petal Dance remains unchanged unless separately requested.

The [Thunderbolt three-way reference](thunderbolt_three_way_comparison.md)
clarifies that this is not a global 30 FPS display ceiling: authored pose holds,
spatial increments and different aftereffect implementations can dominate the
apparent cadence even when one logical update meets every display interval.
This section records the next proposed investigation; no new retiming or
reference sweep is implemented by the evidence-preservation step.

That subsequent investigation and private implementation are now recorded in
[Targeted battle motion prototype](battle_animation_targeted_motion_prototype.md).
It retimes seven selected effects locally, not the shared animation loop, and
is automatically qualified for manual review only. Neither baseline is replaced.

## Findings

1. The faster CPU does not double the LCD or APU clock. It eliminates many
   accidental two- or three-display-interval animation updates. Ordinary
   one-interval updates remain one interval.
2. The animation engine advances scripts, motion functions, framesets, BG
   effects and shadow OAM on a logical loop, not a fixed physical-display
   timeline. Waiting for the next VBlank after work finishes does not guarantee
   a fixed interval since the preceding update.
3. Completed logical states match between normal and double speed in all 20
   profiled move/side pairs at phase zero. No evidence here indicates skipped
   script commands or missing logical animation frames.
4. Whole-wrapper duration can conceal a much greater acceleration of the
   visible primary effect. In particular, faster Surf ends its wave early and
   then waits for still-running sound. Padding the end would not fix the wave.
5. OAM construction and its nested object/frameset/motion work are important
   costs. Trigonometry is only part of this. Opponent coordinate transformation
   adds further per-object work, explaining some old side asymmetry.
6. Caustic's completed shadow OAM exceeds ten sprites on a scanline in both
   clocks. Retiming can improve presentation but is not proof that the actual
   overlap/dropout defect has been removed.
7. Polished Crystal supplies no generic normal-speed timing restoration system.
   Its Surf edits are authored script changes; Poison Gas is removed.

## Scope and reproducibility

The new read-only suite contains **160 cases**: ten moves, both sides, normal
and double speed, and four starting offsets (0, 17,556, 35,112 and 52,668
normal-speed T-cycles). Twenty phase-zero pairs additionally compare the entire
finished shadow OAM and script address/delay/parameter at every logical update.
Dragon Dance was separately added to the ordinary native suite: **16 cases**.

All 160 profiled durations and invocation start timestamps match their ordinary,
unprofiled replays exactly. Host observation inserts **no emulated cycles**.
All new cases finish with no animation/sample-cache miss or CPU-speed change.
This is timing/control-flow acceptance, not proof of absence of graphical
defects; the reported battle-menu and Glacial Slam bugs remain open.

The previous all-species Dex, post-catch, audio, menu and gameplay qualification
is not relabelled as a fresh rerun. No cartridge change was made that would
require requalifying those paths in this pass. Thirteen existing host tests also
pass. Once pacing is implemented, full regression is required again.

Artifacts, all ignored under `build/`:

- `build/global-animation-timing-20261004/profile.json`: all cases, primary and
  follow-up script spans, physical tick intervals, inclusive costs, OAM states.
- `build/global-animation-timing-20261004/replays/`: per-case results and
  compressed native events; `observers/` contains read-only host builds.
- `build/global-animation-timing-20261004/polished-audit.json`: source blocks,
  source commits and qualifying unlisted vanilla moves.
- `build/global-speed-20261004/moves/*/dragon_dance-*`: ordinary Dragon Dance
  replays, independent of the deeper observer.
- `build/global-speed-20261004/manual-review-v2/`: corrected review package.

Commands:

```sh
python3 -m tools.dex_timing.global_speed --suite moves --variants production final --moves DRAGON_DANCE --jobs 16
python3 -m tools.dex_timing.global_animation_timing --jobs 24
python3 -m tools.dex_timing.global_animation_timing --report-only
python3 -m tools.dex_timing.global_review_save
python3 tools/test_dex_performance.py
```

The observer is guarded by `DEX_BATTLE_TIMING_TRACE` in
`tools/dex_timing/probes/performance.c`. It instruments the host, not ROM0/ROMX.
The normal arm is unchanged production; `final` is the accepted private
whole-game candidate. SameBoy CGB-E and matching linked symbols/states are used.
Do not share CPU states across differently linked ROMs.

## What the loop actually does

Relevant current source:

- `engine/battle_anims/anim_commands.asm:194`, `RunBattleAnimScript`.
- `engine/battle_anims/anim_commands.asm:331`, `BattleAnimDelayFrame`.
- `engine/battle_anims/core.asm:297`, `InitBattleAnimBuffer`.
- `home/audio.asm:280`, `WaitSFX`.

Each logical update runs:

```text
RunBattleAnimCommand
  -> _ExecuteBGEffects
  -> BattleAnim_UpdateOAM_All
       -> motion functions / framesets / object OAM construction
  -> PushLYOverrides
  -> BattleAnimRequestPals
  -> BattleAnimDelayFrame
  -> next logical update, unless the script has stopped
```

`anim_wait` counts logical updates. Object duration/frame counters do too. If
work crosses a display boundary before `BattleAnimDelayFrame` starts waiting,
the next update is pushed out. Normal speed frequently does that; double speed
often finishes before that boundary. Merely doubling `anim_wait` would also
double updates that already take one physical interval and would not coherently
retime the motion/frameset counters.

The selected cutscene VBlank handler differs by clock, so interrupt/transfer
overhead also changes. Inclusive costs include IRQs and waits, not just the
named routine's own instructions. They do not isolate a universal bare CPU cost.

The opponent path in `InitBattleAnimBuffer` mirrors coordinates and checks a
16-bit exception array for Kinesis/Softboiled/Milk Drink on eligible objects.
It does extra work that the player path avoids. This is not evidence that sine
itself necessarily becomes more expensive merely because the actor is the foe.

`WaitSFX` continues servicing real-time sound after the primary script stops.
The wrapper waits for sound, but that does not keep the primary effect visible.
This accounts for a visual ending before an electric SFX finishes without
implying that the APU clock has been sped up or that the wrapper returned early.

## Measured durations

One physical display interval is **16.742706ms**. These are medians over four
input phases. Each cell is **normal -> double speed**. Primary is the first
`RunBattleAnimScript` invocation; whole is the matching `_PlayBattleAnim` span,
including setup, sound waits, HUD handling and hit/follow-up scripts.

| Move / side | Primary intervals | Primary ms | Whole intervals |
| --- | ---: | ---: | ---: |
| Surf / player | 377.01 -> 193.04 | 6312.2 -> 3232.0 | 446.00 -> 316.46 |
| Surf / foe | 379.03 -> 193.06 | 6345.9 -> 3232.3 | 453.00 -> 322.51 |
| Water Pulse / player | 241.06 -> 159.03 | 4036.0 -> 2662.7 | 315.00 -> 234.00 |
| Water Pulse / foe | 247.93 -> 159.03 | 4151.0 -> 2662.6 | 325.04 -> 238.98 |
| Thundershock / player | 124.02 -> 123.01 | 2076.5 -> 2059.5 | 204.01 -> 193.51 |
| Thundershock / foe | 123.90 -> 123.01 | 2074.5 -> 2059.5 | 200.00 -> 194.01 |
| Thunderbolt / player | 232.03 -> 220.01 | 3884.8 -> 3683.6 | 305.01 -> 290.01 |
| Thunderbolt / foe | 239.91 -> 220.01 | 4016.7 -> 3683.6 | 314.00 -> 290.00 |
| Caustic / player | 216.10 -> 202.02 | 3618.1 -> 3382.4 | 288.00 -> 267.00 |
| Caustic / foe | 230.10 -> 202.02 | 3852.6 -> 3382.4 | 303.00 -> 271.00 |
| Dragon Dance / player | 156.06 -> 146.02 | 2612.9 -> 2444.8 | 195.88 -> 185.95 |
| Dragon Dance / foe | 165.06 -> 146.05 | 2763.5 -> 2445.2 | 203.86 -> 184.95 |
| Petal Dance / player | 299.05 -> 265.02 | 5006.9 -> 4437.2 | 371.01 -> 337.01 |
| Petal Dance / foe | 365.93 -> 265.04 | 6126.6 -> 4437.5 | 443.00 -> 334.50 |
| SolarBeam charge / player | 207.99 -> 173.98 | 3482.4 -> 2913.0 | 240.95 -> 202.48 |
| SolarBeam charge / foe | 215.02 -> 174.01 | 3600.0 -> 2913.4 | 250.96 -> 201.46 |
| Dazzling Gleam / player | 256.06 -> 224.02 | 4287.1 -> 3750.7 | 325.00 -> 290.50 |
| Dazzling Gleam / foe | 269.05 -> 224.02 | 4504.7 -> 3750.7 | 345.01 -> 294.48 |
| Poison Gas / player | 470.90 -> 330.01 | 7884.1 -> 5525.3 | 501.27 -> 357.69 |
| Poison Gas / foe | 496.05 -> 330.01 | 8305.2 -> 5525.3 | 527.24 -> 358.17 |

These do not establish a unique authoritative normal-speed target. Normal
execution depends on arrival phase and work stalls. Use a deliberate approved
presentation target rather than reproducing every accidental missed boundary.
SolarBeam's attack invocation is separately retained in the raw report; it must
not inherit its charge's pacing automatically. Multi-hit/branching moves must
be compared by equivalent invocation, not entire turns with different DIV/RNG
outcomes. Fractional medians are physical measurements, not fractional refresh.

### Logical cadence explains the changes

Phase-zero examples, primary script only:

| Move / player | Logical updates | Normal step intervals | Double-speed step intervals |
| --- | ---: | --- | --- |
| Surf | 190 | 180 two-interval steps, 8 one-interval steps; first load 5 | 188 one-interval steps; first load 3 |
| Water Pulse | 153 | 74 one, 74 two, 3 three; first load 8 | 151 one; first load 6 |
| Thundershock | 118 | 116 one; first load 5 | 116 one; first load 5 |
| Thunderbolt | 206 | 196 one, 8 two; first load 16 | 204 one; first load 14 |
| Caustic | 197 | 182 one, 13 two; first load 5 | 195 one; first load 5 |
| Dragon Dance | 141 | 132 one, 7 two; first load 6 | 139 one; first load 5 |
| Petal Dance | 260 | 222 one, 36 two; first load 6 | 258 one; first load 5 |
| SolarBeam charge | 171 | 137 one, 32 two; first load 4 | 169 one; first load 3 |
| Dazzling Gleam | 219 | 187 one, 30 two; first load 6 | 217 one; first load 5 |
| Poison Gas | 323 | 181 one, 139 two, one four; first load 5 | 320 one, two four |

The first load is a measured step containing script/asset initialization, not
a steady motion cadence. Counts describe gaps between update starts; they
therefore total one less than the logical-update count. Do not charge a long
inter-script `WaitSFX` gap to a single producer/motion update.

### Where execution time goes

Phase-zero player, first requested animation invocation. Values are inclusive
physical intervals, **normal -> double speed**, and rounded. Motion functions
and sine are nested in the OAM pipeline; **do not add them to OAM again**.

| Move | OAM pipeline | BG work | Motion functions | Sine | Graphics requests |
| --- | ---: | ---: | ---: | ---: | ---: |
| Surf | 133.10 -> 34.38 | 73.98 -> 26.63 | 9.89 -> 3.34 | 1.38 -> 0.53 | 1.99 -> 2.00 |
| Water Pulse | 111.66 -> 35.18 | 23.16 -> 8.14 | 19.78 -> 7.18 | 1.94 -> 0.74 | 3.94 -> 4.03 |
| Dragon Dance | 63.11 -> 26.87 | see raw report | 20.16 -> 8.71 | 8.28 -> 3.56 | 3.98 -> 3.99 |
| Dazzling Gleam | 108.83 -> 44.47 | see raw report | 28.26 -> 12.08 | 10.44 -> 4.37 | see raw report |
| SolarBeam charge | 86.86 -> 35.16 | see raw report | 25.15 -> 10.73 | 9.94 -> 4.30 | see raw report |
| Caustic | 101.48 -> 42.41 | see raw report | 17.93 -> 7.76 | 0 -> 0 | see raw report |
| Poison Gas | 227.92 -> 91.34 | see raw report | 57.99 -> 24.95 | 24.40 -> 10.54 | see raw report |

Graphics requests often retain a physical wait even when the surrounding CPU
work gets faster. Copying a large amount of normal-clock arithmetic is not a
useful way to restore a motion duration: it wastes the gained CPU headroom and
reintroduces interrupt/side-dependent stalls.

## Individual assessment

### Surf

The player's full invocation is about 446 normal intervals and 316.46 double.
Using that whole-invocation measurement as the reference, the requested middle
ground is approximately **381-386 intervals / 6.38-6.46s**, 60-65 intervals faster
than production. The wave itself currently takes only
193 intervals rather than 377. At phase zero the fast build subsequently waits
about **55 intervals for SFX**, whereas the normal build waits almost none.
Across the four double-speed phases the sound-wait median is about 57 intervals
(individual values about 55 or 59).

Consequently, adding 65 wave intervals would mostly replace that already-existing
sound wait. A coarse median-based estimate is **122-127 extra primary-effect
intervals**, yielding roughly 315-320 primary intervals. This is an estimate
from these branches/phases, not a tested target implementation. If the user's
60-65 interval reduction refers specifically to the visible wave instead of
the whole wrapper, the corresponding primary target is instead about 312-317
intervals; the two measurement endpoints must not be silently interchanged.
The prototype must
measure both the wave and wrapper after SFX interaction; do not blindly add a
fixed tail or use the old whole-wrapper ratio as a motion multiplier.

Opponent and player waves already nearly match at double speed. Their whole
wrappers still differ because legitimate follow-up/hit presentation differs.
Require matching wave phase, not identical full-turn duration at any cost.

### Water Pulse and Dragon Dance

Restore a coherent primary cadence near the normal **player** presentation:
about 241 intervals for Water Pulse and 156 for Dragon Dance. Use the same motion
phase targets for both sides rather than restoring the older slower opponent.
Dragon Dance's approximately ten-player/nineteen-opponent interval difference
was missing from the original 79-move table; it is now measured independently.

### Thunderbolt and Thundershock

Thunderbolt gains about twelve primary player intervals, not a factor of two.
Thundershock's primary duration is already within about one interval of normal;
its roughly ten-interval wrapper improvement includes other work. The user's
visual/SFX mismatch must be addressed at the visible electric phase and its
termination, not by padding unrelated setup or multiplying all waits.

Candidate fixes within the pacing design are a phase-specific hold/discharge
cadence and an explicit visible-tail lifetime coordinated with the intended SFX
event. Waiting on every SFX indiscriminately can hold an unrelated sound or music
state. Measure the actual primary disappearance and SFX end in a visual/audio
prototype before selecting that tail rule. The current trace establishes loop
pacing and sound wait spans, not an approved new visual-tail design.

### Caustic

At phase zero, the exact completed shadow OAM states match. Both clocks reach
**16 sprites on one scanline / 26 crowded logical updates for the player**, and
**12 / 4 for the opponent**. These counts model PPU selection from shadow Y
coordinates, including horizontally offscreen sprites that can consume the
scanline selection limit. They are not a direct trace of each scanline's actual
DMA/PPU selection or proof that visible dropout pixels match between clocks.

Restore a normal-like primary cadence around 216 intervals for both sides, but
do not close the dropout concern on pacing alone. Separately examine popping
bubbles/droplet overlap, actual scanline-selected OAM, object ordering and
lifetimes. Possible geometric corrections include staggering droplet creation,
reducing simultaneous sprites or replacing crowded particles. Those changes
alter the authored effect and require separate visual approval.

### Petal Dance, powders and charge effects

Keep Petal Dance's improved double-speed presentation. Its old opponent penalty
is much larger than its player penalty. Powder-controller removal remains a
separate future experiment; it was not done or costed as part of this fix.

For SolarBeam's charge and Dazzling Gleam's charging phase, start with roughly
208 and 256 primary intervals respectively, matching the normal player feel on
both sides. Do not globally restore the old opponent delay. Do not retime
SolarBeam's attack branch just because its charge needs a different target.

## Polished Crystal source audit

Local sources inspected without changes:

- Polished Crystal `f7745f128030c2ba8b0bd7ec8c3f161b58791d07`.
- pret/pokecrystal `5beda23ffa505f62e1dad7e3d7c214d1737b3358`.
- Project baseline `2cec8051763e01b45fc2da51186ef795477fe7d4`.

Polished Crystal enables double speed early (`engine/init.asm:27`). Its battle
loop (`engine/battle_anims/anim_commands.asm:98`) still advances script/BG/OAM
work and then waits for a display frame. There is no generic compensator that
replays normal-speed missed VBlanks. Its sine routine (`engine/math/sine.asm:1`)
uses the same shift/add amplitude multiplication family as this project's
`macros/code.asm`; it is not a faster trigonometry architecture we can simply
copy to solve presentation timing.

Surf (`data/moves/animations.asm:945`) uses wait 112, loop count 1, then wait 56.
pret and this project use wait 32, loop count 4, then wait 56. Polished's version
shortens the authored loop and changes repeated SFX behavior. This is not a
normal-speed duration-restoration mechanism; copying it would be a separate
animation redesign, not our requested middle-ground fix.

Poison Gas is commented out/removed (`data/moves/animations.asm:6456`), so it
offers no implemented timing solution to borrow.

### Other qualifying vanilla moves

Among the **previously measured 79 moves**, the following moves outside the
user's custom-animation list are at least 10% faster in one or both sides.
Percentages compare median first-invocation wrapper durations; paired per-case
differences remain in the original report. This is not an exhaustive runtime
sweep of every vanilla move.

| Move | Qualifying side / reduction | Polished animation source line | Useful result |
| --- | --- | ---: | --- |
| DoubleSlap | foe 16.9% | 512 | Same alternating wait-6/wait-8 hit pattern; no compensator |
| Cut | player 10.3% | 1470 | Same wait-32 shape; no compensator |
| Gust | player 11.2%, foe 21.4% | 1173 | Same wait-6 loop, then 8/16; no compensator |
| Double Kick | player 12.7% | 548 | Same alternating hit waits; no compensator |
| Surf | player 29.0%, foe 28.8% | 945 | Shorter authored script, not original timing restoration |
| Psychic | player 14.6%, foe 16.3% | 3398 | Similar wait-8 loop and 96/4 tail; no compensator |
| Recover | player 18.2%, foe 38.9% | 1543 | Similar branch/wait-32 plus glimmer helper; no compensator |
| Whirlpool | player 34.4%, foe 34.8% | 5719 | Same wait-16, wait-6 loop and 64/1 tail; no compensator |

These scripts can differ in coordinates, palettes or helpers; similar waits do
not prove identical rendered animations or runtime cost. Polished's live ROM
was not used as another measured runtime arm. Source comparison is sufficient
to rule out a general pacing system at these call sites, not to assert its
actual durations. DoubleSlap hit counts and Whirlpool's later binding invocation
must be kept separate from their first matching invocation.

## Implementation options

Costs below are design estimates, **not linked implementation measurements**.
They are incremental to the accepted double-speed candidate.

| Option | Estimated added resources | Complexity / risk | Assessment |
| --- | --- | --- | --- |
| Edit individual script waits | Roughly 10-200 ROMX bytes; usually no new RAM | Low mechanical complexity; medium/high presentation risk | Cannot coherently slow object/frameset counters; selected simple tails only |
| Per-move motion/controller changes | Roughly 50-150 ROMX bytes per affected function plus scripts; state depends on safe object fields | Medium individually, high cumulative maintenance | Fine for a unique visual redesign, poor general restoration policy |
| Shared battle-local cadence plus compact phase targets | Initially about 1-2KiB ROMX, 8 ROM0 bytes, 8-12 WRAMX bytes; no new WRAM0/HRAM/VRAM | Moderate; central clock, audio and publication regression required | **Recommended**; coordinated pacing, default unchanged, sides can share approved targets |
| Dense captured cadence table | Current first-invocation 79-move tick counts imply about 27,486 bytes for one byte/update/both sides, before headers/code | Medium/high; branch validation and regeneration essential | Handles irregularity but overfits captured normal stalls and costs two data banks |
| Switch CPU speed around animations | Hardware switch and timer/audio ownership changes | High integration risk and visible-switch concern | Rejected: contradicts whole-game double-speed policy |
| CPU busy-wait padding | Small code, large wasted CPU time | Phase/IRQ-dependent and side-dependent | Rejected: recreates the inefficiency we are removing |

The dense estimate is for the current measured first invocations, not every
move branch or every move in the game. Bit-packing one/two-interval holds could
reduce those decisions to about 3,436 bytes, but long holds, headers, initialization,
variable hits and branches need additional records; the estimate is not a ready
ROM payload. A compact first set of roughly 50 phase spans at 6-8 bytes each,
move/branch headers and a 400-900 byte helper gives the recommended 1-2KiB range.
Scaling compact coverage to roughly 79 moves with six eight-byte spans each
would require about 3.8KiB of span data before headers/helper, still within a bank.

### Recommended code direction

1. Add a physical-display cadence source for battle cutscenes. The existing
   `hVBlankCounter` increments in ordinary handlers, but not `VBlank_Cutscene`
   or `VBlank_CutsceneCGB`. Incrementing it with `ld hl, hVBlankCounter` and
   `inc [hl]` costs **four ROM0 bytes per handler, eight total**. It costs 24
   CPU T-cycles per interrupt, or 12 normal-speed-equivalent cycles in double
   speed. No new HRAM is required. Only the double-speed handler would cost
   four bytes, but covering both makes the control implementation consistent.
2. Audit existing counter readers before changing those handlers. A serviced
   VBlank counter is only a reliable display clock when no long interrupt-disabled
   window loses a whole interrupt; validate that assumption and bounded waits.
   Counter wrapping is harmless for one/two-interval comparisons below half
   the byte range. Explicitly rebase after long asset/sound/owner transitions.
3. Initialize battle-local pacing state **after** `ClearBattleAnims`; that routine
   clears the animation workspace. Select data by the resolved 16-bit animation
   index, charge/attack parameter and phase, not dynamic one-byte move IDs.
4. Gate the **entire logical update** together: script delay, BG effects, motion,
   frameset and OAM construction. Additional hold intervals keep the previous
   prepared state and service normal display/audio work. Do not advance only
   a motion timer while script lifetime/framesets continue at a different rate.
5. Use compact phase spans and a fractional/integer cadence accumulator to
   distribute deliberate extra display holds. Schedule from display deadlines,
   not from producer-call count. Separate initialization/loading and after-hit
   work from the phase whose motion is being retimed.
6. Preserve the existing transfer/publication safety checks. Do not eagerly
   mutate a visible state before its allowed display interval. Missed work is
   diagnosed and the previous state held; do not catch up by skipping visual
   steps or executing multiple logical updates merely because a deadline passed.
   Faster computation and deliberate holds leave spare CPU capacity available.
7. Let audio progress on its existing physical timer/VBlank cadence. Extra holds
   must keep any owned sampled-cry refill/frontpic service live. Do not call
   `NormalSpeed`, change the sample divisor, globally delay sound, or stretch the
   Dex/New Entry timeline as a side effect of battle-motion pacing.
8. Default unlisted/approved moves to existing double-speed behavior. Keep Petal
   Dance fast. Preserve Rollout's intentional no-delay path. Use explicit reset
   points for repeated hits, charge/attack branches, status effects and catch
   animations; do not accidentally inherit one move's phase into another owner.

RAM allocation estimate: bank-5 animation storage currently ends at `$d4c1`,
with **62 bytes free** before the next fixed section at `$d500`. A dedicated
8-12 byte cadence record can fit without moving that section or allocating a
new RAM bank; used WRAMX increases by those 8-12 bytes within existing free
space. The scratch union overlaps the Surf wave buffer and is not safe
to reuse blindly for state that must persist across updates. No new WRAM0,
HRAM, SRAM, VRAM or OAM allocation is proposed. Existing HRAM is already full.

The current loop's ROMX bank `$33` has **1,118 free bytes**. A 400-900 byte core
helper can remain there; the entire upper estimate of code plus phase data
cannot. Start with a small table that fits or put phase data in another ROMX
bank, load/cache the current span through existing far-read machinery, and keep
the per-update clock check local. Larger coverage can use a dedicated data bank.
This avoids requiring a new ROM0 bank-switch wrapper, but data fetching and RAM
records must be included in the actual implementation link/timing audit.
ROM0 currently has 547 free bytes in the candidate;
an eight-byte interrupt change fits, subject to a real link and handler audit.
No allocation in this proposal has been spent yet.

### Target selection and next prototype tests

Initial test targets: Surf middle ground; Water Pulse/Dragon Dance normal-player
feel on both sides; Thunderbolt/Thundershock visible/SFX coordination; Caustic
normal-like cadence with separate crowding investigation; charge effects matched
between sides; Petal Dance unchanged. Poison Gas and the qualifying vanilla
moves can share the mechanism, with individually reviewed target decisions.

Test at least the same four input offsets on both sides, measure first visible
motion, primary disappearance, SFX completion and whole-wrapper return. Compare
motion/OAM logical state order as well as duration; a correct total duration
does not establish perceptible orbit speed. Expand phase-offset coverage around
near-boundary publications and inspect rendered Caustic scanlines.

Then rerun the complete existing 79-plus-Dragon move suite, repeated hits,
charge/attack turns, status animations, Master Ball catch, frontpic/sample audio,
Dex/New Entry/Stats ownership and ordinary battle turn/UI restoration. The
three already-reported graphical bugs must remain separately labelled, not
misclassified as failures introduced by pacing. Provide another private ROM for
visual approval before any production promotion.

## Private Phase Pacing Trial

The requested selected-move experiment is implemented in a separate ROM. See
[Battle animation phase pacing prototype](battle_animation_phase_pacing_prototype.md)
for exact linked costs, paired timings, native frame/OAM review, remaining
charge-target limitations, inherited stationary tails and manual review files.
Production and the accepted unpaced double-speed baseline remain unchanged.

## Corrected manual review package

The old save builder erroneously included `NO_MOVE` and then added one to each
position; its self-check repeated that same error. This explains the missing
Hydro Pump/Superpower/Fire Blast in the user's review package. The native
automated move fixtures used the correct zero-based index and are unaffected.

The corrected builder reads `const_def`/`const` values, verifies all 80 requested
indexes and independently compares the game's loaded name bytes with each
requested canonical name. It checks usable PP and exercises actual PC
deposit/withdraw in both ROMs. All checks pass. New review battery files are
byte-identical between the normal and double arms; no live save was edited.

- Party 1 Kyogre `BIGDIFF`: Poison Gas, Surf, Whirlpool, Leaf Blade, the four
  largest player-side differences in the original measurements.
- Party 2 Garchomp `HEAVY`: Hydro Pump, Superpower, Fire Blast, Water Pulse.
- Party 3 Luxray `RESTORE`: Thunderbolt, Thundershock, Caustic, Dragon Dance.
- Party 4 Rayquaza `CHARGE`: SolarBeam, Dazzling Gleam, Overheat, Petal Dance.
- Party 5 Meganium `LEAVES`: Razor Leaf, Magical Leaf, Seismic Toss, Earthquake.
- Party 6 Dusknoir `MORE`: Sludge Wave, Sludge Bomb, Meteor Dive, Aerial Crash.

Fourteen more Pokemon in Box 14 `ANIMS` hold the remainder. The package README
lists all assignments. Saves start in Cherrygrove Pokecenter; boot/Continue,
do not share CPU states between links. Files are in
`build/global-speed-20261004/manual-review-v2/{normal,double}/`.

New save SHA-256:
`7be522ecc9ef6ff5e2576efbf8fbba1e02c948add7931fab93ec94406f82cc18`.
Double ROM SHA-256 remains
`5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90`.
Normal ROM SHA-256 remains
`7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.

## Deferred graphical defects

See `BATTLE-UI-01`, `BATTLE-UI-02` and `BATTLE-ANIM-01` in the
[bug backlog](pokedex_selected_bug_backlog.md). They are user-reported in both
production and the double-speed prototype, and not fixed here:

- Persistent battle-menu glyph corruption after party Stats -> Switch.
- Transient font glyph flash when selecting a switch-in Pokemon.
- Glacial Slam slicing the opposing sprite.

The suspected VRAM/OAM explanations remain hypotheses until those dedicated
investigations. This pass does not claim they are caused by double speed.
