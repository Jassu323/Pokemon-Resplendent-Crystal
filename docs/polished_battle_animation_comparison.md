# Polished Crystal battle animation comparison

2026-10-04. Native comparison of Surf, Razor Leaf, Gust, Whirlpool, Rock Slide,
and Earthquake. Production Resplendent Crystal remains unchanged.

**Conclusion:** Polished does not restore normal-speed Crystal's wall-clock
animation rhythm. It generally executes one logical animation update per LCD
interval and consequently also makes CPU-limited animations faster. It retains
the native coupled scripts, object state machines and framesets, rather than
retiming them through independently sampled motion curves. Thus "faster" and
"disconnected effects" are separate problems. These results do not establish
that its presentation would satisfy our acceptance criteria; the videos are
provided for that judgment.

The expanded local-retiming prototype was rejected during manual review. Its
automated timing and safety passes did not detect the Waterfall hit overlap,
leaf motion/impact, vibration and disconnected wind-effect presentation
problems. No additional retiming or production fix is made by this comparison.

## Builds and method

Three arms are shown in the comparison videos:

1. Resplendent production, normal-speed battles.
2. The accepted **unretimed** whole-game double-speed baseline, before either
   the phase gate or the local-motion expansion. This is not the latest rejected
   expanded prototype. Its third-party comparison role is to isolate the speed
   change within our own engine.
3. A fresh unmodified Polished Crystal master build, double speed.

| Build | Identity |
| --- | --- |
| Production ROM SHA-256 | `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666` |
| Unretimed double ROM SHA-256 | `5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90` |
| Polished source commit | `f7745f128030c2ba8b0bd7ec8c3f161b58791d07` |
| Polished ROM SHA-256 | `16a618e65a434cf631d3181c2f2629576f160f3e31ae4d31a041926ffb78591f` |

Polished's clean tracked checkout was copied with `git archive` to the ignored
`build/polished-battle-comparison-20261004/source/` directory and built there
with RGBDS 1.0.1. Neither that external checkout nor either Resplendent ROM was
modified. The fresh Polished build is `polishedcrystal-3.2.3.gbc`.

All six moves were selected through native battle menus, on each combatant,
at four physical starting offsets: 0, 17,556, 35,112 and 52,668 normal-speed
T-cycle equivalents. **144 captures completed**, 48 per arm. There is no broad
Dex/menu/gameplay regression claim for this narrowly scoped comparison.

The host-only SameBoy observer records interpreter entry/return, logical
update readiness, native object states/positions, BG work, shadow/hardware
OAM, every rendered frame and native audio. No emulated instructions, clocks,
LCD flags, speed state or animation-ready state are patched during capture.
Twelve extra Polished controls, with observation disabled, produced **exactly
the same final physical time, PC, bank, stack, speed and menu/battle state**.

Fixtures supply level-50 combatants, coherent battle/party stats, abundant HP
and PP, high accuracy and a harmless Splash move on the other side. The
Polished fixture starts a native wild battle after its normal new-game setup;
its own party initializer and AI select the fixture's moves before observation.
It is not a naturally found grass encounter. The opponent artwork differs
between arms (Pidgey, Hoppip and Hoothoot); positions and orientation are native.
This is not a pixel-equivalence test of Pokemon art, HUDs or palettes.

Polished needs its own species/form fields, Water type value, and ten 24-byte
animation objects. Resplendent has fourteen 20-byte objects. Early adapter
attempts with incorrect fixture fields were discarded and are not measurements
in the final manifest. The shared host observer's object-byte count is now
configurable; its existing Resplendent default is unchanged. Sampled-cry-specific
observer fields do not apply to Polished and are not used in this analysis.

## Primary animation durations

Each cell is **display intervals / milliseconds**, median over four offsets.
One physical LCD interval is 70,224 normal-speed T cycles, approximately
16.742706ms. These are fractional elapsed intervals, not a count rounded to
the nearest displayed image. CPU double speed does not change LCD frequency.

The primary measurement spans the first `RunBattleAnimScript` invocation,
including its native setup work. It excludes subsequent hit/damage scripts,
HUD teardown and the outer sound wait. It is more useful for motion comparison
than a single number covering all of those operations.

| Move | Side | Production normal | Resplendent raw double | Polished native double |
| --- | --- | ---: | ---: | ---: |
| Surf | Player | 377.01 / 6312.23 | 193.04 / 3231.96 | 173.00 / 2896.52 |
| Surf | Opponent | 379.03 / 6345.91 | 193.06 / 3232.35 | 173.02 / 2896.76 |
| Razor Leaf | Player | 222.00 / 3716.86 | 188.01 / 3147.80 | 182.00 / 3047.22 |
| Razor Leaf | Opponent | 319.02 / 5341.32 | 188.00 / 3147.59 | 182.04 / 3047.91 |
| Gust | Player | 115.03 / 1925.85 | 97.01 / 1624.23 | 92.00 / 1540.33 |
| Gust | Opponent | 139.02 / 2327.61 | 97.01 / 1624.20 | 92.00 / 1540.37 |
| Whirlpool | Player | 264.02 / 4420.47 | 153.02 / 2562.00 | 151.01 / 2528.36 |
| Whirlpool | Opponent | 271.02 / 4537.66 | 153.01 / 2561.85 | 151.01 / 2528.37 |
| Rock Slide | Player | 262.06 / 4387.59 | 250.01 / 4185.86 | 247.00 / 4135.46 |
| Rock Slide | Opponent | 262.02 / 4386.99 | 250.00 / 4185.67 | 247.00 / 4135.47 |
| Earthquake | Player | 103.05 / 1725.38 | 102.02 / 1708.10 | 102.01 / 1707.99 |
| Earthquake | Opponent | 103.05 / 1725.33 | 102.01 / 1707.99 | 102.01 / 1707.97 |

Opponent-side production stalls are evidence, **not slowdown targets**. This
comparison does not recommend reproducing them. Starting-offset variation
does not alter the conclusion; full ranges are in `measurements.json`.

### Outer animation durations

`_PlayBattleAnim` includes preparation, the primary and any later animation
scripts, HUD restoration, fixed waits and waiting for outstanding SFX. A
short primary animation does not imply the entire wrapper or sound has ended.
Earthquake particularly demonstrates why the two measures must not be mixed.

| Move | Side | Production normal | Resplendent raw double | Polished native double |
| --- | --- | ---: | ---: | ---: |
| Surf | Player | 446.00 / 7467.19 | 316.46 / 5298.46 | 235.99 / 3951.15 |
| Surf | Opponent | 453.00 / 7584.41 | 322.51 / 5399.76 | 240.99 / 4034.90 |
| Razor Leaf | Player | 296.59 / 4965.64 | 256.97 / 4302.44 | 250.00 / 4185.74 |
| Razor Leaf | Opponent | 394.52 / 6605.39 | 258.04 / 4320.23 | 250.00 / 4185.75 |
| Gust | Player | 182.96 / 3063.19 | 162.50 / 2720.66 | 154.99 / 2595.00 |
| Gust | Opponent | 212.00 / 3549.43 | 166.54 / 2788.37 | 159.99 / 2678.75 |
| Whirlpool | Player | 338.99 / 5675.68 | 222.49 / 3725.07 | 213.99 / 3582.81 |
| Whirlpool | Opponent | 345.97 / 5792.54 | 225.50 / 3775.47 | 218.99 / 3666.50 |
| Rock Slide | Player | 333.00 / 5575.25 | 316.51 / 5299.22 | 309.99 / 5190.11 |
| Rock Slide | Opponent | 337.97 / 5658.57 | 319.50 / 5349.30 | 314.99 / 5273.82 |
| Earthquake | Player | 278.00 / 4654.39 | 277.00 / 4637.73 | 275.05 / 4605.08 |
| Earthquake | Opponent | 283.97 / 4754.47 | 281.50 / 4713.09 | 280.02 / 4688.37 |

## Update cadence and visual interpretation

The following counts are from the player-side phase-zero trace. They describe
rounded physical spacing between interpreter updates, **not** a guarantee
that every object or pixel changes on every update. Initial asset-loading gaps
are included and listed separately where larger than two intervals.

| Move | Logical updates normal / raw double / Polished | Production step spacing | Polished step spacing |
| --- | ---: | --- | --- |
| Surf | 190 / 190 / 171 | 180 two-interval, 8 one-interval, 1 five-interval | 169 one-interval, 1 two-interval |
| Razor Leaf | 181 / 181 / 181 | 146 one-interval, 33 two-interval, 1 eight-interval | 180 one-interval |
| Gust | 90 / 90 / 90 | 69 one-interval, 19 two-interval, 1 seven-interval | 88 one-interval, 1 two-interval |
| Whirlpool | 148 / 148 / 148 | 38 one-interval, 108 two-interval, 1 seven-interval | 146 one-interval, 1 three-interval |
| Rock Slide | 246 / 246 / 246 | 235 one-interval, 9 two-interval, 1 four-interval | 245 one-interval |
| Earthquake | 101 / 101 / 101 | 100 one-interval | 100 one-interval |

The raw-double arm has essentially one interval per steady logical update too.
That is why it is close to Polished after accounting for script/setup changes.

Frame inspection and native state traces support these distinctions:

- **Surf:** Polished's wave rises and retreats at its native per-update rates,
  so the motion is much faster than production. Its script is also shorter:
  `wait 112` once, versus our `wait 32` looped four times. Polished is not an
  example of retaining production's slower wave rhythm at double speed.
- **Razor Leaf:** both use the same main wait/release ordering, but Polished
  retains the simpler original leaf behavior. Our leaf function additionally
  spawns per-leaf impacts and enters an extra state. Polished therefore cannot
  prove that our customized impact timing is correct. Its scatter/fall/release
  remain native while production's overloaded sections take longer.
- **Gust:** the native vortex object state machine and its framesets remain
  together. Polished's nine objects spawn roughly seven display intervals
  apart (a `wait 6` plus command/update progression), like raw double, rather
  than receiving independent interpolated trajectories. The vortex and impacts
  finish earlier; there is no inserted phase wait or motion-table catch-up.
- **Whirlpool:** background distortion, nine vortex spawns and native angular
  progression remain coupled to the same interpreter updates. Production
  spawn spacing grows from approximately 7 to 14 intervals as work increases;
  Polished remains around 7. This is faster coherent native execution, not a
  restoration of those CPU-limited holds.
- **Rock Slide:** the script's four repeated rock bursts and final wait are
  essentially the same. Most of the normal-speed animation already runs at
  one update per interval, so the speed difference is modest.
- **Earthquake:** its script and shake progression are essentially the same,
  and production already updates every interval. Its primary duration differs
  by only about one interval. This is a useful control against assuming that
  double speed automatically halves every animation.

The recordings show no capture crashes or obvious persistent post-effect
corruption. This is not a visual acceptance declaration. In particular,
Polished's faster movement may still be undesirable for our animations.

## Relevant Polished implementation differences

There is **no general normal-speed timing compensation** in the reviewed path:

- `engine/init.asm:27` enables double speed early with the LCD disabled.
- `engine/battle_anims/anim_commands.asm:16` selects its cutscene VBlank handler
  according to current speed, but does not switch battle execution to normal.
- `RunBattleAnimScript`, at line 101, performs command, BG-effect, object/OAM,
  scanline-table and palette work, then calls `DelayFrame`. Steady updates
  return at the next VBlank when the work fits. No per-move production-duration
  table or fixed every-other-display-frame gate is present in this path.
- `home/delay.asm:32` uses a halting VBlank wait. Our battle wait also services
  the sampled-cry cache. Removing that servicing is not a safe optimization.
- `home/battle.asm:908` uses a **dedicated scanline-override transfer request**.
  `home/video.asm:299` copies it via `LYOverrideStackCopy`, called by cutscene
  VBlank at `home/vblank.asm:301`. Our scanline table uses the normal 2bpp
  request fields. This is a useful architectural reference for efficient and
  explicit BG-effect publication, not a normal-speed rhythm mechanism.
- Polished's `VBlank1` always reaches `PushOAM`, even when a palette update
  skips BG/tile work. Our cutscene handler's palette early-exit skips the OAM
  transfer as well. This is worth a separate publication audit; these captures
  do not attribute every duration or visual difference to that branch.
- Polished updates each active object's function and OAM consecutively, up to
  ten objects. Our fourteen-object engine updates functions first and performs
  its separate OAM pass, with sampled-cry servicing. Blindly importing that
  loop would change ownership and runtime contracts, not just optimize a call.
- Its sine calculation uses shift/add multiplication. Our `calc_sine_wave`
  already uses that method, so this is **not** a missing trig optimization we
  can copy to solve the problem.

Relevant native functions are `BattleAnimFunction_RazorLeaf` at
`engine/battle_anims/functions.asm:837`, Surf at 1165, and Gust at 1649.
Native water BG effects are at `engine/battle_anims/bg_effects.asm:859` and 920.
The six scripts are at `data/moves/animations.asm:945`, 986, 1173, 1239, 1755
and 5719 in the retained Polished source snapshot. Line references apply to
the recorded commit, not a future upstream checkout.

## Direction recommended for the next trial

Polished is not a ready-made replacement for the rejected retiming approach.
Its native faster presentation can be assessed from the videos, but it does
not supply our desired production-like rhythm for Surf/Whirlpool or our
customized moves.

If those faster native presentations are unacceptable, the next bounded trial
should be a **normal-speed battle ownership envelope**, while retaining double
speed outside battles. Prototype the switch on existing hidden/blank lifecycle
boundaries, not mid-effect on a visible battlefield. Validate input, the intro,
sampled cries/timer configuration, catch/New Entry and exit before broadening.
This is a recommendation only; no speed-policy change is made here.

That has a small likely code/data footprint and moderate integration risk,
versus high per-effect complexity for reconstructing every native relationship
through ROMX curves. Exact byte costs need a scoped preflight. Its deliberate
tradeoff is retaining normal-speed battle CPU stalls and preparation costs.
If retaining smooth fast opponent behavior is mandatory too, native local
state-machine/rate work remains necessary; normal speed alone cannot provide
both benefits.

Do not reinstate a broad phase gate or hold completed pictures merely to match
total duration. Neither protects impact overlap, sound cadence, native shake
amplitude or coordinated multi-object motion. The manual failure of the
expanded prototype is decisive despite its near-matching total durations.

## Retained artifacts and reproduction

Artifacts are under the ignored
`build/polished-battle-comparison-20261004/` directory:

- `source/`: unmodified source and freshly linked Polished ROM/symbols/map.
- `setup/`: private battle checkpoint, bootstrap fixture and compiled observer.
- `replays/polished/`: 48 results with compressed event captures; twelve include
  losslessly retained rendered frames and audio.
- `measurements.json`: per-case durations, costs, cadence, object histories and
  sound dispatch; summary over all four offsets.
- `observer-parity.json`: twelve observation-disabled native controls.
- `visuals/`: twelve three-column comparisons, two compiled comparison reels,
  six moves x two sides x three arms individual clips with **full wrapper audio**,
  and per-move contact sheets. `videos.json` is the complete media manifest;
  `README.md` links every clip. All **50 videos** were verified for playable
  streams and native frame rate; all 36 individual clips include audio.

Comparisons are synchronized at the first primary-script display and play at
native LCD cadence. They are silent to avoid mixing three soundtracks.
After a script ends, its final primary frame is explicitly labeled
`SCRIPT END (padded)`. That is comparison padding, **not** a real held pose.
Individual clips cover the native wrapper with lead-in and tail, including
sound waits; they are the audio references. Art/color/HUD differences are native.

The complete player and opponent reels are `visuals/player-all-moves-comparison.mp4`
and `visuals/foe-all-moves-comparison.mp4`. Each move also has
`<move>-<side>-comparison.mp4` and three corresponding individual files.

Reproduce using the retained fresh source build and the original private
Resplendent battle fixtures:

```sh
make -C build/polished-battle-comparison-20261004/source -j24
env PYTHONPATH=.:tools python3 -m tools.dex_timing.animation_reference --variants production final --moves SURF RAZOR_LEAF GUST WHIRLPOOL ROCK_SLIDE EARTHQUAKE --coherent-fixture --capture-all --phases 0 17556 35112 52668 --jobs 16
env PYTHONPATH=.:tools python3 -m tools.dex_timing.polished_battle_reference --jobs 16
env PYTHONPATH=.:tools python3 -m tools.dex_timing.polished_battle_reference --parity-only --jobs 12
env PYTHONPATH=.:tools python3 -m tools.dex_timing.polished_battle_visuals
env PYTHONPATH=.:tools python3 -m tools.dex_timing.polished_battle_visuals --verify-only
env PYTHONPATH=.:tools python3 -m tools.dex_timing.polished_battle_visuals --archive-frames
```

The observer, renderer and documentation add **zero runtime ROM0, ROMX, WRAM0,
WRAMX, HRAM, VRAM or OAM cost** to either cartridge. All testing is host-side.
Generated frames/audio can be losslessly archived and verified before loose
copies are reclaimed; linked ROMs, checkpoints, measurements and videos remain.
Verified archival reclaimed approximately **2.58 GiB** of loose generated
frames/audio across the three comparison arms without discarding that evidence.
