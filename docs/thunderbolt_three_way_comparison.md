# Thunderbolt Three Way Timing Comparison

Measured on 2026-10-04. This investigation compares freshly built vanilla
Emerald, production Resplendent Crystal, and the accepted whole-game double-speed
prototype. It does not use the rejected phase-pacing prototype. No move script,
animation function, cartridge instruction, or speed policy was changed.

The main result is that there is no universal 30 FPS ceiling in Crystal's battle
animation engine. Thunderbolt's bolt growth is deliberately held across multiple
updates in both games, with different growth increments and hold lengths. The
Emerald aftereffect also uses per-display affine scaling and circling motion
that Crystal's discrete-pose implementation does not reproduce. Double speed
removes late Crystal updates in this test, but does not change its authored bolt
holds.

## Build and Capture Identities

All generated artifacts are under the ignored directory:

`build/thunderbolt-comparison-20261004/`

The user subsequently requested long-term retention. A hash-verified copy of
all captures and videos, exact ROMs and replay metadata is preserved outside
disposable builds under `research_artifacts/thunderbolt-comparison-20261004/`.
See [Preserved Thunderbolt reference](archived/thunderbolt-reference.md) for
contents, cleanup protection and recovery directions.

| Component | Identity |
| --- | --- |
| Emerald source | `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` |
| mGBA source | `c3c8e5e813f245028de118a56734e1dc0f35ce2a` |
| SameBoy source | `213a12ce93d66b105a113debd9396306066a7cfc` |
| Fresh Emerald ROM SHA1 | `f3ae088181bf583e55daf962a92bb46f4f1d07b7` |
| Fresh Emerald ROM SHA256 | `a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af` |
| Production Crystal ROM SHA256 | `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666` |
| Accepted double-speed ROM SHA256 | `5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90` |

Emerald was copied from `~/Documents/GitHub/pokeemerald` into the private build
directory, compiled using agbcc/devkitARM, and passed `make compare` against the
retail checksum. mGBA was built out of tree from `~/Documents/GitHub/mgba` with
its software renderer, debugger API, static library and headless executable.
The replay driver uses mGBA's built-in HLE BIOS and disables idle-loop
optimization. The source checkouts remained clean, and both Crystal ROM hashes
were verified unchanged after testing.

The comparison adds zero ROM0, ROMX, WRAM0, WRAMX, HRAM or VRAM bytes to either
game. The additional code consists of host fixtures, host observers, analysis
and media generation.

## Native Battle Method

Emerald boots the unmodified ROM. The private fixture invokes native new-game
initialization, creates two level-50 Pikachu through the game's own `CreateMon`
and `SetMonMoveSlot` functions, then starts a normal wild battle through
`CB2_InitBattle`. The tested side has Thunderbolt; the other side has Splash.
The fixture is saved at the normal battle action menu. The measured replay
selects Fight and the move using ordinary button inputs; it does not call the
animation directly or patch instructions. Setup calls occur before capture.

Crystal uses the existing separate production/prototype native battle states,
also selecting moves using ordinary inputs. Both attack directions are tested.
Four input offsets are tested per direction and version: full-display offsets
0-3 for Emerald, and quarter-display CPU offsets 0, 17556, 35112 and 52668
normalized T-cycles for Crystal. These are sensitivity samples, not exhaustive
possible hardware phases.

The Crystal fixtures use artificial HP/types to ensure survival and a reliable
hit. Their visible portraits differ between builds: the player is Meganium;
the production foe is Pidgey and the prototype foe is Hoppip. They use the same
Thunderbolt objects, authored coordinates and corresponding attack direction.
Emerald uses Pikachu on both sides. Consequently these are matched animation
tests, not pixel-identical entire battle scenes. The opponent-side Crystal
fixture can display an odd HP denominator because its artificial max HP exceeds
the ordinary three-digit HUD range; that is not a new game regression.

## Measurement Boundaries

Both machines have the same nominal display frequency:

- GBC: 4194304 / 70224 = 59.7275006 Hz.
- GBA: 16777216 / 280896 = 59.7275006 Hz.
- One display interval is 16.7427063 ms.

The primary duration includes Thunderbolt script launch/setup, graphics load,
authored waits, effects and completion. It excludes move announcement time,
later damage processing and the next battle menu.

For Crystal the primary boundary is the first `RunBattleAnimScript` invocation
through its return. The separately measured `_PlayBattleAnim` wrapper includes
additional HUD/preparation/sound waits and subsequent hit animation work.
For Emerald the boundary is `DoMoveAnim(THUNDERBOLT)` through the first
`BattleMainCB2` observation after `gAnimScriptActive` clears. Its actual script
end command occurs about 0.033 intervals earlier. Thus these are useful
main-effect comparisons, not claims that the two engines have identical
function boundaries or cleanup semantics.

First-visible times are measured at completed rendered-frame boundaries, not
merely when an object is created in RAM. Onset therefore has display-frame
precision; instruction/function timings have finer emulator-clock precision.

## Main Effect Duration

Representative phase-zero captures:

| Version | Player intervals | Player ms | Opponent intervals | Opponent ms |
| --- | ---: | ---: | ---: | ---: |
| Vanilla Emerald | 235.030 | 3935.0 | 235.029 | 3935.0 |
| Production Crystal | 231.026 | 3868.0 | 240.025 | 4018.7 |
| Double-speed Crystal | 220.012 | 3683.6 | 220.012 | 3683.6 |

Observed ranges across four input offsets:

| Version | Player interval range | Opponent interval range |
| --- | ---: | ---: |
| Vanilla Emerald | 235.029979-235.029979 | 235.029484-235.029513 |
| Production Crystal | 231.026430-232.030303 | 239.905047-240.025063 |
| Double-speed Crystal | 220.008345-220.011506 | 220.007889-220.011705 |

At phase zero, double speed removes approximately 11.015 intervals / 184.4 ms
from the player's Crystal effect and 20.013 intervals / 335.1 ms from the
opponent's. Emerald is not simply faster overall: its complete main effect is
slightly longer than production Crystal's player-side effect. The scripts have
different fades, waits, strike geometry and aftereffects, so total duration is
not a substitute for matching individual phases.

### First Visible Bolt

| Version | Player intervals / ms | Opponent intervals / ms |
| --- | ---: | ---: |
| Vanilla Emerald | 30.935 / 517.9 | 30.935 / 517.9 |
| Production Crystal | 19.839 / 332.2 | 19.836 / 332.1 |
| Double-speed Crystal | 16.929 / 283.4 | 16.927 / 283.4 |

These are from the primary launch marker, not from button press. Emerald
deliberately fades the background and waits before creating its first bolt.

### Crystal Wrapper Only

| Version | Player intervals / ms | Opponent intervals / ms |
| --- | ---: | ---: |
| Production | 303.949 / 5088.9 | 314.999 / 5273.9 |
| Double speed | 289.009 / 4838.8 | 291.981 / 4888.5 |

Do not compare these broader wrapper values directly with Emerald's primary
effect duration above. The supplied individual videos intentionally include
only a short lead-in and tail around the primary effect, not the entire wrapper.

## Published Bolt States

These counts come from hardware OAM at rendered-frame boundaries, associated
with the corresponding animation objects. They are not counts of function
calls or merely proposed shadow OAM. The phase-zero published bolt holds are
the same for both attack directions within each implementation.

### Emerald Bolts

All three Emerald bolts grow through five 16-pixel height increments, then lose
segments. The published composite-state holds are:

```text
Growth 1-4:             2, 2, 2, 2 intervals
Full height:           5 intervals
Retraction 4-1:        2, 2, 2, 2 intervals
Total per bolt:        21 intervals / 351.6 ms
```

The first bolt's visual growth is therefore about 30 changes per second, not
60. A 60 Hz display does not imply a different bolt height every display.

### Crystal Large Bolt

Crystal grows the large bolt through ten 8-pixel increments. Its published
holds are identical in production and the accepted double-speed prototype:

```text
Growth 1-9:            1, 2, 2, 2, 2, 2, 2, 2, 2 intervals
Full height:           10 intervals
Retraction 9-4:        3, 3, 3, 3, 3, 3 intervals
Retraction 3-1:        2, 2, 2 intervals
Total:                 51 intervals / 853.9 ms
```

The main growth cadence is two displays per pose, like Emerald, but the spatial
increment is half as large. The full-height and retraction holds are also
longer. This directly explains a slower-looking bolt independently of missed
CPU deadlines.

### Crystal Small Bolts

The small bolts grow through five 16-pixel increments, but the regular pose
hold is three displays rather than Emerald's two:

```text
First small bolt:      2, 3, 3, 3, 8, 3, 3, 3, 3 = 31 intervals / 519.0 ms
Second small bolt:     3, 3, 3, 3, 8, 3, 3, 3, 3 = 32 intervals / 535.8 ms
```

Both sequences are unchanged by double speed in the representative captures.
The one-display leading-edge differences are publication/creation ordering,
not evidence that the entire frame timer is one interval shorter.

### Logical Holds Versus Published Holds

Crystal stores the supplied `oamframe` duration and then decrements it on later
updates before advancing. A duration of 1 usually occupies two logical
updates, 2 occupies three, and 9 occupies ten. Its large-bolt frameset thus
occupies 52 logical updates, while this captured hardware-publication sequence
occupies 51 displays. Emerald's raw sprite/task state likewise reports a
22-update bolt sequence versus 21 actually published displays.

The CSV files distinguish these quantities rather than silently treating a
script operand, RAM pose and visible pose as the same timing.

## Aftereffect and Update Cadence

Emerald's orb is sampled for 44 consecutive displays; its hardware affine
scale changes on all 43 transitions. The circling spark positions also change
on consecutive displays, while the orb's blink independently alternates
four-display visible/hidden runs. A sprite graphic can therefore remain the
same while its scale or position changes every display.

Crystal instead uses small/medium/large orb graphics, blank holds and a local
aftereffect controller. Its thirteen logical orb states have counts
`4,4,4,4,7,4,4,4,4,7,4,4,4`; production stretches several of those states with
late updates, especially on the opponent side. The per-object ready-time CSV
records the resulting wall-clock durations. This is not the same continuous
affine/position system as Emerald, and multiplying CPU speed cannot create
missing intermediate visual states.

| Version and side | Primary logical updates | Gaps between updates |
| --- | ---: | --- |
| Emerald, either side | 235 | 234 one-display gaps |
| Production Crystal, player | 206 | Initial 16-display graphics-load gap; 196 one-display and 8 two-display gaps |
| Production Crystal, opponent | 206 | Initial 16-display gap; 188 one-display, 15 two-display and 1 three-display gap |
| Double-speed Crystal, either side | 206 | Initial 14-display graphics-load gap; 204 one-display gaps |

After initial setup the double-speed captures execute one primary logical
update per physical display. Production does not always meet that cadence,
but it is not intrinsically restricted to alternating displays. The missed
updates in this case are concentrated in the later effect rather than the
measured bolt pose holds.

Median observed tick-to-ready work is 0.323 / 0.344 display intervals in
production for player/opponent and 0.140 / 0.148 at double speed. The largest
tick measurement includes blocking upfront graphics load; it must not be
reported as the cost of every steady-state update.

Sound-command timestamps are preserved as well. Emerald creates separate bolt
sound cues around intervals 28.005, 37.064 and 46.064, an orb cue around
105.466 and later electrical cues around 172.004 and 191.202. Crystal's primary
bolt sound is around 17.126 at normal speed and 14.052 at double speed; its
aftereffect cue is around 94.113 and 91.050 respectively on the player side.
The two implementations do not have identical sound scripts. These timestamps
measure command dispatch, not the end of each sound's audible envelope.

## Code Explaining the Results

- `data/moves/animations.asm`, `BattleAnim_Thunderbolt`: two small strikes,
  one large strike, explicit waits, custom aftereffect and electricity subroutine.
- `engine/battle_anims/extension_frame_oam.asm`,
  `.Frameset_ThunderboltStrike`, `.Frameset_ThundershockStrike`, and
  `.Frameset_ThunderboltAftereffect`: spatial stages and authored holds.
- `engine/battle_anims/helpers.asm`, `GetBattleAnimFrame`, and
  `BattleAnimExt_LoadFrame`: duration storage/decrement and extended poses.
- `engine/battle_anims/anim_commands.asm`: script, object, BG and publication
  preparation in the primary loop; no universal every-other-display limiter.
- `engine/battle_anims/extension_functions.asm`: Crystal's local aftereffect
  controller rather than GBA affine objects.
- Emerald `data/battle_anim_scripts.s`, `Move_THUNDERBOLT`: fades, waits,
  three bolt tasks, orb plus eight circling sparks and final electrical effects.
- Emerald `src/battle_anim_electric.c`, `AnimTask_ElectricBolt_Step`: five
  segments introduced at counters 0, 2, 4, 6 and 8; each segment adds 16 pixels.
- Emerald `AnimSparkElectricityFlashing_Step`: per-update sine/cosine positions;
  `src/sprite.c` supplies affine animation updates.
- Emerald `src/battle_main.c`, `BattleMainCB2` and VBlank callback: ordinary
  per-display sprite/task work and hardware OAM publication.

## Capture Validation

24 traced cases completed: three versions, two attack directions and four
input offsets. No Crystal animation/sampled-cry miss was reported by the
existing host observers during these specific move captures; this is not a
replacement for the broader game regression suite.

Eight additional Emerald replays omit function breakpoints. Across 9692 paired
rendered frames, traced and untraced runs match every pixel hash, animation
pointer/active flag, sprite/task RAM, shadow OAM, hardware OAM and palette dump.
There are zero frame/state differences. The host's final batched-versus-stepped
stop can differ by two GBA cycles; that command-boundary detail is not an
observed display difference. The sixteen Crystal primary/wrapper timing
records also match the corresponding earlier baseline capture records exactly.

Three analysis-contract tests pass, including disambiguation of Emerald's
private `Cmd_end` symbol and preservation of separate holds when a display
sample is absent. Whole-shadow-OAM association may fail during complex partial
publication; the Crystal published-state CSV does not fill such gaps or claim
unobserved poses. The direct bolt holds above have complete associated runs.
Detailed aftereffect data include raw per-update state and hardware dumps so
missing associations remain auditable.

All ten videos were decoded/probed successfully. Their video rate is the
native `262144/4389` rational rate, with no internal frame interpolation,
speed conversion or time stretching. Representative bolt and later-aftereffect
frames were visually checked. This confirms usable captures, not physical
GBA/GBC hardware equivalence or subjective acceptance of the animation.

## Videos and Detailed Outputs

The `videos/` subdirectory contains:

- `comparison-player-script.mp4` and `comparison-foe-script.mp4`: align primary
  script launch to expose startup and phase timing differences.
- `comparison-player-first-bolt.mp4` and
  `comparison-foe-first-bolt.mp4`: align the first published bolt to compare
  motion/hold rhythm without the different startup fades.
- `emerald-player.mp4`, `emerald-foe.mp4`, `production-player.mp4`,
  `production-foe.mp4`, `final-player.mp4`, `final-foe.mp4`: individual native
  recordings with sound.

Comparison panels are left Emerald, middle production Crystal, right accepted
double-speed Crystal. They are silent to avoid mixing three soundtracks.
Nearest-neighbor integer scaling preserves pixel art. Only exterior lead-in
or completed-page padding is held to synchronize panels; the animation itself
retains every rendered frame at its original rate.

Emerald's native stream is 65536 Hz, measured from mGBA's audio API. The export
uses that rate and AAC resamples it to supported 64000 Hz; it is not incorrectly
interpreted as 44100 Hz. Crystal's captured audio is 44100 Hz. The standalone
clips include four preceding and about 24 following display intervals, so their
container duration is intentionally longer than the main-effect table.

`measurements.json` contains all timing records and observer parity. Each
Crystal capture has `object-state-holds.csv`, `published-state-per-frame.csv`
and `published-state-holds.csv`. Each Emerald capture has
`sprite-state-per-frame.csv`, `individual-sprite-holds.csv`,
`component-state-holds.csv`, `published-state-holds.csv` and
`orb-affine-per-frame.csv`. Function/cycle events and raw OAM/palette data are
retained beside them. Phase-zero raw videos/images and private states remain
in the ignored build directory, not in repository documentation.

## Reproduction

From the project root, with the existing agbcc/devkitARM, CMake, FFmpeg and
Python/Pillow dependencies installed:

```sh
python3 -m tools.gba_timing.build --jobs 24
python3 -m tools.gba_timing.thunderbolt fixture
python3 -m tools.gba_timing.thunderbolt emerald
python3 -m tools.gba_timing.thunderbolt crystal
python3 -m tools.gba_timing.analyze
python3 -m unittest tools.gba_timing.test_analysis
```

The Crystal command currently consumes the accepted prototype and existing
private battle fixture locations from the whole-game speed investigation. A
fresh machine must first reproduce those fixtures; the generated save states
are not version-controlled source assets. Emerald setup is self-contained
once its source/compiler and mGBA source are available.

## Assessment and Next Decision

There is no need to increase LCD refresh frequency. The accepted double-speed
build already meets one primary update per display after setup for this move.
To obtain more frequent visible motion, the relevant authored functions and
framesets need more frequent pose advancement or additional intermediate
positions, with sound/BG phase alignment considered separately.

For Thunderbolt specifically, the evidence points first to its 8-pixel large
bolt progression and longer holds, then to the discrete orb/spark implementation.
A targeted frameset/controller experiment could change those without globally
pacing unrelated move functions. That is a proposed next experiment, not an
implemented fix or a claim that literal Emerald timing is the desired target.
The three-way videos are the basis for the user's visual review before making
that design decision.
