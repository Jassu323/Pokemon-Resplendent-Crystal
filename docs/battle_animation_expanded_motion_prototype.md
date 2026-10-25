# Expanded private battle motion retiming

2026-10-04. This is a **private review prototype**, not production acceptance.
Production game source and `pokecrystal.gbc` are unchanged. It extends the
[targeted motion trial](battle_animation_targeted_motion_prototype.md), retains
whole-game double speed, and replaces neither baseline.

**Manual review outcome: rejected.** Waterfall's hit overlap, Leaf Blade and
Razor/Magical Leaf motion/impact, target vibration and wind-effect continuity
did not meet acceptance despite automated timing/safety checks. Do not treat
the results below as visual acceptance or promote this build. The next
[native Polished comparison](polished_battle_animation_comparison.md) records
the alternative-direction investigation; no further broad retiming is applied.

## Scope And Method

The complete suite from
[the original measurements](global_double_speed_animation_measurements.md)
contains 79 moves. Dragon Dance is added explicitly: **80 moves**, each used
by both combatants at four starting offsets, through actual battle input.

The reference observer records script commands/waits, object states and
positions, frameset lifetimes, background work, shadow and hardware OAM,
rendered LCD frames, sound dispatch, and actual interpreter returns. It runs
inside SameBoy without adding cartridge instructions or advancing the emulated
clock. Native execution remains the authority, not an estimated host cost model.

Retiming is local, not a global slowdown or display-clock phase gate:

- Restore lost authored holds and spawn spacing at individual script waits.
  The build recipe derives wait adjustments from four production-player
  references; it does not append one arbitrary delay at the end of each move.
- For selected pure motion functions, sample/interpolate production XY paths
  into ROMX curves. Each object still advances every animation update. Both
  orientations retain their own path but use the normal-player lifetime,
  avoiding the old opponent-side trigonometric penalty.
- Keep native state machines where they own impact spawning or sound. Adjust
  fractional displacement/angular increments instead of freezing their updates.
- Adjust held-pose duration in both the ordinary and extended frameset loaders.
  A longer script alone is insufficient when its visible column/impact pose
  still disappears at the old accelerated rate.
- Keep the accepted Water Pulse, Dragon Dance, Caustic, charge and Thunderbolt
  treatment protected from later shared-wait changes. Keep Petal Dance faster.

This deliberately does **not** reproduce every production missed VBlank or
variable CPU stall. Matching the old wrapper duration by delaying a finished
picture would not satisfy the motion/rhythm requirement. Small setup/teardown
gains remain, and several opponent effects intentionally finish much sooner
than their old CPU-limited presentation.

The user's clarified target explicitly excludes flipped-motion CPU stalls.
The old opponent durations are retained as comparison evidence, not slowdown
targets. Preserving an appropriate motion rhythm on both orientations is the
goal; a faster result versus the stalled old opponent is not a timing failure.

## Surf Correction

The final retreat step now branches directly to Surf's existing cleanup when
the new Y reaches `$70`. Previously it tested only the old Y, then advanced
from 111 to 113 on the last script update; there was no future update to clear
`hLCDCPointer = $42`. The LCD interrupt subsequently read unrelated WRAM bank 1
as the bank-5 scroll table, slicing the HUD and pictures.

Cost: **four ROMX bytes**, no RAM/graphics allocation and no extra script wait.
The production-duration wave motion, rise/fall waits, sound sequence and
accepted intro VBlank-window correction remain. The diagnostic now observes
primary-script exit, outer animation ownership, later interrupts and a native
Surf-last turn followed by fleeing, not just total duration.

## Implementation And Refinement

The extension changes 108 wait sites in its initial phase plan. These are
existing command values except when a hold must be split into valid byte-sized
waits. Gust's shared Sonicboom entry is cloned so Sonicboom does not inherit
Gust's retiming.

Pure-motion curves cover Leaf Blade/chips, Recover orbits, Poison Gas, Gust,
Whirlpool, Waterfall bubbles, Seismic Toss debris and Psychic projectiles.
The reader uses the object's existing `VAR1/VAR2` as a 16-bit sample age;
Poison Gas's lifetime cannot fit in the older byte-age reader. It preserves
the caller's object pointer and deinitializes at the curve's actual end.
Native commands still own sounds and unrelated effects.

Razor/Magical Leaf retain native scatter, fall, dash and one-hit state changes.
The angular progression is finer, travel increments are reduced, and impact
poses last longer. Additional charge effects retain the native fractional
accumulator with a move-specific delta. No whole-engine update is held back.

The first expanded trial exposed two worthwhile refinements:

1. Hydro Pump/Waterfall use the extended pose loader. That loader now receives
   the targeted duration treatment while preserving BC, DE, HL, OAM ID and
   flip flags. Ordinary-loader changes alone had left the visible effects fast.
2. A single median gap for an entire burst loses its changing rhythm. The final
   revision unrolls Poison Gas's ten spawns and Whirlpool's nine spawns with
   independently referenced gaps. This avoids an overlong Whirlpool phase and
   brings Poison Gas's poison flash/sound onset back near production.

Encoded burst waits (a wait byte is not itself the complete held interval):

- Poison Gas: `8, 8, 8, 8, 8, 8, 10, 12, 17, 17`.
- Whirlpool: `6, 6, 9, 10, 13, 13, 13, 13, 13`.

The shared Rock Smash debris subroutine also affects Heavy Slam and Rock Smash.
These two extra consumers are explicitly native-regressed on both sides and
four phases, beyond the requested 80. Their native motion functions are not
replaced by Seismic Toss's move-guarded curve. This is a private shared-wait
tradeoff, not an assertion that every move outside the suite is qualified.

## Qualification And Measurements

<!-- EXPANDED_RESULTS_START -->
Final linked ROM: `be7db3f4b0fcaf729356fe2fc7fa42ce7219daf6c79a9e0fd9c5e6633d2a038e`.
Unchanged production: `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.

| Final-build native checks | Cases/inputs | Result |
| --- | ---: | --- |
| 80 moves x two sides x four phases x two ROMs | 1280 | No replay/playback failures |
| Additional shared-subroutine consumers, final build | 16 | No failures |
| All-species Dex cold/paging/Info/Moves/Area/stress | 6182 | No failures |
| New Dex Entry, 20 species and input sweep | 8194 | No failures; authored durations retained |
| Cries: Stats/catch/faint/send-out/blocking/stereo | 480 | No misses or waveform/pitch/block-count changes |
| Menu/input/overworld/battle/mart/puzzle/Game Corner | 896 | No mask/register regressions |
| Surf/Caustic ownership, both sides/four phases/two ROMs | 32 | Clean teardown; exact observer parity |
| Private review saves | 3 arms, 82 moves each | Boot, linked moves and PC conversion pass |
| Host motion/pacing invariants | 21 | Pass |

The native intro tests also retain smooth two-pixel-per-display sliding on
eight wild species/four phases and the trainer path. Tests overlap; these
counts are not a claim of that many independent gameplay features.

### Linked Cost

| Resource | Added by expansion over Surf-cleanup | Total free in linked final build |
| --- | ---: | ---: |
| ROM0 | 0 bytes | 547 bytes |
| ROMX | 12,260 bytes | 729,466 bytes |
| WRAM0 | 0 bytes | 13 bytes |
| WRAMX | 0 bytes | 4,728 bytes |
| HRAM | 0 bytes | 0 bytes |
| SRAM | 0 bytes | 15,542 bytes |

One new ROMX bank, `$bb`, holds 9,416 curve-data bytes plus the reader/dispatch
and pose rules. No new VRAM/OAM allocation. Existing per-object scratch is
repurposed only within selected functions. The expansion includes the extra
94 bytes for individually timed bursts. Total battle retiming over the
unpaced double-speed baseline is 16,516 ROMX bytes;
its earlier seven-byte ROM0 whole-game speed cost is inherited, not new here.

### Primary Script Timing

Every duration cell is **display intervals / milliseconds**, medians over
four offsets. One interval is 16.742706ms. The first `RunBattleAnimScript`
body is separate from the broader `_PlayBattleAnim` wrapper measured in
the original report. Setup/HUD/cleanup gains therefore are not disguised
as motion changes. Multi-hit and later charge/attack invocations stay in
the raw traces and are not summed into these first-invocation medians.
"Prior" is the corrected Surf/accepted-local-motion build before expansion,
not the rejected shared-phase-gating experiment.
61/80 player primary bodies finish within three display intervals
of production. This is descriptive, not a visual pass/fail threshold.
59/80 foe bodies are within three intervals of the
normal-player reference. Final player/foe body medians differ by at most
1.000 intervals. The old foe stalls are not target holds.

#### Player Primary Body

| Move | Production | Prior local-motion build | Final expanded build | Final - production (intervals) |
| --- | ---: | ---: | ---: | ---: |
| `THUNDERSHOCK` | 124.02 / 2076.49 | 123.00 / 2059.35 | 123.01 / 2059.52 | -1.01 |
| `THUNDERBOLT` | 232.03 / 3884.82 | 220.00 / 3683.41 | 220.01 / 3683.55 | -12.02 |
| `THUNDER` | 205.04 / 3432.97 | 203.04 / 3399.36 | 203.02 / 3399.06 | -2.03 |
| `HYDRO_PUMP` | 240.88 / 4033.04 | 143.05 / 2395.01 | 238.01 / 3984.92 | -2.87 |
| `WATER_PULSE` | 241.06 / 4036.00 | 241.06 / 4035.94 | 241.02 / 4035.36 | -0.04 |
| `WATERFALL` | 282.05 / 4722.31 | 252.02 / 4219.52 | 279.02 / 4671.60 | -3.03 |
| `SLEEP_POWDER` | 196.91 / 3296.85 | 196.02 / 3281.95 | 196.02 / 3281.95 | -0.89 |
| `STUN_SPORE` | 197.06 / 3299.26 | 196.03 / 3282.00 | 196.02 / 3281.91 | -1.04 |
| `POISONPOWDER` | 196.98 / 3297.96 | 196.02 / 3281.94 | 196.02 / 3281.95 | -0.96 |
| `SPORE` | 197.04 / 3299.05 | 196.02 / 3281.95 | 196.02 / 3281.95 | -1.02 |
| `FIRE_BLAST` | 183.08 / 3065.30 | 164.02 / 2746.19 | 182.04 / 3047.76 | -1.05 |
| `ACID` | 110.05 / 1842.53 | 109.06 / 1826.01 | 109.05 / 1825.77 | -1.00 |
| `CAUSTIC` | 216.10 / 3618.06 | 216.01 / 3616.63 | 216.04 / 3617.08 | -0.06 |
| `CORROSION` | 186.05 / 3114.95 | 184.02 / 3081.01 | 185.02 / 3097.80 | -1.02 |
| `WISH` | 119.01 / 1992.58 | 117.01 / 1959.05 | 117.04 / 1959.52 | -1.97 |
| `DISARMING_VOICE` | 84.18 / 1409.34 | 82.00 / 1372.90 | 82.06 / 1373.94 | -2.11 |
| `FAIRY_WIND` | 142.14 / 2379.86 | 140.05 / 2344.86 | 140.02 / 2344.34 | -2.12 |
| `SILVER_WIND` | 133.05 / 2227.69 | 128.02 / 2143.42 | 131.02 / 2193.68 | -2.03 |
| `SLUDGE_WAVE` | 175.04 / 2930.72 | 169.02 / 2829.87 | 173.02 / 2896.87 | -2.02 |
| `SLUDGE_BOMB` | 113.05 / 1892.80 | 110.04 / 1842.44 | 111.98 / 1874.90 | -1.07 |
| `SUPERPOWER` | 317.08 / 5308.75 | 318.03 / 5324.74 | 318.04 / 5324.91 | +0.97 |
| `WILD_CHARGE` | 350.03 / 5860.39 | 318.99 / 5340.73 | 339.01 / 5675.97 | -11.01 |
| `SHOCK_WAVE` | 302.03 / 5056.85 | 282.99 / 4738.02 | 299.04 / 5006.66 | -3.00 |
| `LEAF_BLADE` | 238.03 / 3985.20 | 155.00 / 2595.12 | 239.06 / 4002.50 | +1.03 |
| `FORCE_PALM` | 87.17 / 1459.54 | 81.01 / 1356.30 | 86.01 / 1440.02 | -1.17 |
| `RAZOR_LEAF` | 222.00 / 3716.86 | 188.01 / 3147.78 | 221.01 / 3700.29 | -0.99 |
| `MAGICAL_LEAF` | 226.05 / 3784.73 | 188.00 / 3147.65 | 225.03 / 3767.65 | -1.02 |
| `SEISMIC_TOSS` | 268.03 / 4487.48 | 249.01 / 4169.08 | 267.97 / 4486.55 | -0.06 |
| `AROMATHERAPY` | 138.10 / 2312.21 | 125.01 / 2093.04 | 136.02 / 2277.36 | -2.08 |
| `PETAL_DANCE` | 299.05 / 5006.94 | 265.01 / 4437.01 | 265.02 / 4437.22 | -34.03 |
| `OUTRAGE` | 268.08 / 4488.47 | 258.05 / 4320.38 | 263.04 / 4403.92 | -5.05 |
| `DRAGON_CLAW` | 306.05 / 5124.16 | 297.00 / 4972.60 | 301.03 / 5040.08 | -5.02 |
| `METEOR_DIVE` | 211.04 / 3533.41 | 209.02 / 3499.53 | 210.04 / 3516.58 | -1.00 |
| `AERIAL_CRASH` | 117.03 / 1959.33 | 113.01 / 1892.10 | 115.04 / 1926.00 | -1.99 |
| `PILEDRIVER` | 235.02 / 3934.93 | 233.02 / 3901.35 | 233.03 / 3901.56 | -1.99 |
| `OVERHEAT` | 288.02 / 4822.30 | 274.03 / 4588.03 | 281.01 / 4704.88 | -7.01 |
| `POISON_GAS` | 470.90 / 7884.09 | 330.02 / 5525.36 | 470.01 / 7869.29 | -0.88 |
| `HEAT_WAVE` | 144.04 / 2411.68 | 141.02 / 2361.00 | 141.02 / 2361.02 | -3.03 |
| `WILL_O_WISP` | 172.14 / 2882.14 | 167.01 / 2796.22 | 169.02 / 2829.86 | -3.12 |
| `BRICK_BREAK` | 98.04 / 1641.53 | 97.02 / 1624.30 | 97.02 / 1624.30 | -1.03 |
| `METEOR_MASH` | 122.09 / 2044.07 | 115.01 / 1925.66 | 121.01 / 2026.09 | -1.07 |
| `SIGNAL_BEAM` | 181.18 / 3033.39 | 172.02 / 2880.10 | 172.02 / 2880.11 | -9.15 |
| `SHADOW_PUNCH` | 150.05 / 2512.30 | 147.00 / 2461.23 | 148.02 / 2478.30 | -2.03 |
| `EXTRASENSORY` | 166.09 / 2780.86 | 162.00 / 2712.34 | 164.04 / 2746.39 | -2.06 |
| `BULLET_SEED` | 110.02 / 1842.10 | 100.99 / 1690.82 | 105.04 / 1758.62 | -4.99 |
| `IRON_DEFENSE` | 148.06 / 2478.85 | 146.04 / 2445.14 | 146.02 / 2444.81 | -2.03 |
| `MUD_SHOT` | 98.07 / 1641.88 | 96.07 / 1608.45 | 96.03 / 1607.76 | -2.04 |
| `MOONBLAST` | 152.07 / 2546.05 | 148.02 / 2478.20 | 150.03 / 2511.85 | -2.04 |
| `DAZZLING_GLEAM` | 256.06 / 4287.11 | 256.02 / 4286.43 | 256.04 / 4286.85 | -0.02 |
| `POUND` | 30.02 / 502.66 | 29.05 / 486.39 | 29.03 / 486.02 | -0.99 |
| `KARATE_CHOP` | 58.02 / 971.41 | 57.01 / 954.49 | 57.01 / 954.49 | -1.01 |
| `DOUBLESLAP` | 22.04 / 369.01 | 21.02 / 351.89 | 21.02 / 351.89 | -1.02 |
| `FIRE_PUNCH` | 49.94 / 836.11 | 49.04 / 820.98 | 49.03 / 820.97 | -0.90 |
| `ICE_PUNCH` | 75.03 / 1256.16 | 74.01 / 1239.16 | 74.01 / 1239.08 | -1.02 |
| `THUNDERPUNCH` | 142.88 / 2392.24 | 141.00 / 2360.70 | 141.01 / 2360.88 | -1.87 |
| `BODY_SLAM` | 91.60 / 1533.61 | 88.02 / 1473.63 | 90.01 / 1507.09 | -1.58 |
| `SWORDS_DANCE` | 63.04 / 1055.47 | 61.02 / 1021.58 | 61.02 / 1021.59 | -2.02 |
| `CUT` | 37.06 / 620.44 | 36.02 / 603.15 | 36.03 / 603.18 | -1.03 |
| `GUST` | 115.03 / 1925.85 | 97.01 / 1624.22 | 111.04 / 1859.07 | -3.99 |
| `FLY` | 72.03 / 1205.98 | 69.02 / 1155.61 | 69.02 / 1155.52 | -3.01 |
| `VINE_WHIP` | 90.02 / 1507.23 | 87.01 / 1456.77 | 87.05 / 1457.42 | -2.97 |
| `DOUBLE_KICK` | 21.89 / 366.42 | 21.01 / 351.82 | 21.01 / 351.75 | -0.88 |
| `SURF` | 377.01 / 6312.23 | 377.01 / 6312.18 | 377.00 / 6311.98 | -0.01 |
| `ICE_BEAM` | 173.07 / 2897.66 | 170.02 / 2846.51 | 170.01 / 2846.46 | -3.06 |
| `BLIZZARD` | 213.02 / 3566.51 | 211.01 / 3532.88 | 213.02 / 3566.45 | -0.00 |
| `HYPER_BEAM` | 73.17 / 1225.00 | 68.04 / 1139.18 | 71.10 / 1190.48 | -2.06 |
| `EARTHQUAKE` | 103.05 / 1725.38 | 102.01 / 1707.95 | 102.03 / 1708.18 | -1.03 |
| `DIG` | 193.99 / 3247.96 | 181.01 / 3030.61 | 194.00 / 3248.10 | +0.01 |
| `PSYCHIC_M` | 217.89 / 3648.02 | 179.01 / 2997.12 | 214.01 / 3583.10 | -3.88 |
| `RECOVER` | 117.02 / 1959.24 | 99.05 / 1658.34 | 113.01 / 1892.10 | -4.01 |
| `SELFDESTRUCT` | 87.07 / 1457.73 | 81.01 / 1356.27 | 82.99 / 1389.47 | -4.08 |
| `EXPLOSION` | 87.07 / 1457.79 | 81.03 / 1356.65 | 83.07 / 1390.77 | -4.00 |
| `SWIFT` | 80.89 / 1354.33 | 80.02 / 1339.67 | 80.01 / 1339.65 | -0.88 |
| `SOLARBEAM` | 207.99 / 3482.37 | 208.01 / 3482.66 | 208.00 / 3482.47 | +0.01 |
| `SHADOW_BALL` | 193.05 / 3232.26 | 158.00 / 2645.37 | 191.02 / 3198.27 | -2.03 |
| `ROLLOUT` | 51.22 / 857.50 | 49.09 / 821.97 | 50.09 / 838.69 | -1.12 |
| `RAIN_DANCE` | 152.90 / 2560.01 | 152.04 / 2545.51 | 152.01 / 2545.14 | -0.89 |
| `SUNNY_DAY` | 152.89 / 2559.74 | 152.03 / 2545.40 | 152.01 / 2545.04 | -0.88 |
| `WHIRLPOOL` | 264.02 / 4420.47 | 153.06 / 2562.65 | 261.01 / 4370.05 | -3.01 |
| `DRAGON_DANCE` | 156.06 / 2612.92 | 156.01 / 2612.11 | 156.03 / 2612.31 | -0.04 |

#### Foe Primary Body

| Move | Production | Prior local-motion build | Final expanded build | Final - production (intervals) |
| --- | ---: | ---: | ---: | ---: |
| `THUNDERSHOCK` | 123.90 / 2074.47 | 123.00 / 2059.43 | 123.01 / 2059.54 | -0.89 |
| `THUNDERBOLT` | 239.91 / 4016.66 | 220.01 / 3683.56 | 220.01 / 3683.56 | -19.89 |
| `THUNDER` | 206.04 / 3449.64 | 203.02 / 3399.06 | 203.02 / 3399.05 | -3.02 |
| `HYDRO_PUMP` | 247.08 / 4136.72 | 143.02 / 2394.57 | 238.01 / 3984.94 | -9.07 |
| `WATER_PULSE` | 247.93 / 4151.04 | 241.02 / 4035.36 | 242.02 / 4052.11 | -5.91 |
| `WATERFALL` | 284.05 / 4755.77 | 252.02 / 4219.53 | 279.05 / 4672.06 | -5.00 |
| `SLEEP_POWDER` | 197.05 / 3299.18 | 196.02 / 3281.93 | 196.02 / 3281.94 | -1.03 |
| `STUN_SPORE` | 197.05 / 3299.19 | 196.01 / 3281.78 | 196.02 / 3281.92 | -1.03 |
| `POISONPOWDER` | 197.05 / 3299.19 | 196.02 / 3281.92 | 196.02 / 3281.95 | -1.03 |
| `SPORE` | 197.10 / 3300.02 | 196.02 / 3281.92 | 196.01 / 3281.79 | -1.09 |
| `FIRE_BLAST` | 264.08 / 4421.37 | 164.05 / 2746.71 | 182.04 / 3047.79 | -82.04 |
| `ACID` | 110.05 / 1842.51 | 108.99 / 1824.86 | 109.02 / 1825.32 | -1.03 |
| `CAUSTIC` | 230.10 / 3852.57 | 216.02 / 3616.77 | 216.02 / 3616.82 | -14.08 |
| `CORROSION` | 186.05 / 3114.97 | 184.03 / 3081.22 | 185.04 / 3098.14 | -1.01 |
| `WISH` | 118.99 / 1992.15 | 117.02 / 1959.22 | 117.04 / 1959.57 | -1.95 |
| `DISARMING_VOICE` | 87.05 / 1457.49 | 82.02 / 1373.30 | 82.02 / 1373.27 | -5.03 |
| `FAIRY_WIND` | 142.05 / 2378.33 | 140.02 / 2344.35 | 140.02 / 2344.36 | -2.03 |
| `SILVER_WIND` | 135.05 / 2261.13 | 128.05 / 2143.95 | 131.02 / 2193.71 | -4.03 |
| `SLUDGE_WAVE` | 181.05 / 3031.26 | 169.01 / 2829.77 | 173.02 / 2896.86 | -8.03 |
| `SLUDGE_BOMB` | 113.05 / 1892.78 | 110.02 / 1842.09 | 112.02 / 1875.55 | -1.03 |
| `SUPERPOWER` | 323.08 / 5409.20 | 318.03 / 5324.77 | 318.53 / 5333.12 | -4.54 |
| `WILD_CHARGE` | 361.90 / 6059.19 | 319.01 / 5341.01 | 339.01 / 5675.99 | -22.89 |
| `SHOCK_WAVE` | 311.02 / 5207.39 | 283.01 / 4738.36 | 299.03 / 5006.57 | -11.99 |
| `LEAF_BLADE` | 242.03 / 4052.15 | 155.01 / 2595.30 | 239.01 / 4001.69 | -3.01 |
| `FORCE_PALM` | 90.02 / 1507.19 | 81.01 / 1356.32 | 86.02 / 1440.22 | -4.00 |
| `RAZOR_LEAF` | 319.02 / 5341.32 | 188.02 / 3147.97 | 221.01 / 3700.30 | -98.01 |
| `MAGICAL_LEAF` | 320.94 / 5373.33 | 188.03 / 3148.18 | 225.03 / 3767.67 | -95.90 |
| `SEISMIC_TOSS` | 269.03 / 4504.22 | 249.01 / 4169.09 | 268.01 / 4487.23 | -1.01 |
| `AROMATHERAPY` | 142.05 / 2378.36 | 125.02 / 2093.22 | 136.02 / 2277.40 | -6.03 |
| `PETAL_DANCE` | 365.93 / 6126.64 | 265.03 / 4437.37 | 265.02 / 4437.22 | -100.90 |
| `OUTRAGE` | 270.08 / 4521.86 | 258.07 / 4320.74 | 263.04 / 4403.96 | -7.04 |
| `DRAGON_CLAW` | 320.05 / 5358.53 | 297.02 / 4972.96 | 301.02 / 5039.95 | -19.03 |
| `METEOR_DIVE` | 211.04 / 3533.46 | 209.01 / 3499.34 | 210.02 / 3516.27 | -1.03 |
| `AERIAL_CRASH` | 117.04 / 1959.49 | 113.00 / 1891.96 | 115.01 / 1925.57 | -2.03 |
| `PILEDRIVER` | 236.03 / 3951.70 | 233.01 / 3901.23 | 233.01 / 3901.23 | -3.01 |
| `OVERHEAT` | 300.02 / 5023.22 | 274.01 / 4587.65 | 281.01 / 4704.89 | -19.01 |
| `POISON_GAS` | 496.05 / 8305.16 | 329.99 / 5524.93 | 470.01 / 7869.31 | -26.03 |
| `HEAT_WAVE` | 144.04 / 2411.58 | 141.02 / 2360.98 | 141.02 / 2361.02 | -3.02 |
| `WILL_O_WISP` | 172.10 / 2881.48 | 167.04 / 2796.71 | 169.03 / 2830.08 | -3.07 |
| `BRICK_BREAK` | 99.04 / 1658.17 | 97.06 / 1625.03 | 97.02 / 1624.34 | -2.02 |
| `METEOR_MASH` | 121.96 / 2041.89 | 115.01 / 1925.66 | 121.02 / 2026.12 | -0.94 |
| `SIGNAL_BEAM` | 199.05 / 3332.64 | 172.02 / 2880.14 | 172.02 / 2880.13 | -27.03 |
| `SHADOW_PUNCH` | 149.94 / 2510.38 | 147.02 / 2461.56 | 148.02 / 2478.30 | -1.92 |
| `EXTRASENSORY` | 165.98 / 2778.99 | 162.01 / 2712.55 | 164.03 / 2746.37 | -1.95 |
| `BULLET_SEED` | 117.04 / 1959.50 | 101.01 / 1691.18 | 105.04 / 1758.69 | -11.99 |
| `IRON_DEFENSE` | 148.06 / 2478.90 | 146.02 / 2444.81 | 146.04 / 2445.14 | -2.02 |
| `MUD_SHOT` | 98.06 / 1641.86 | 96.04 / 1607.95 | 96.03 / 1607.80 | -2.03 |
| `MOONBLAST` | 153.07 / 2562.79 | 148.04 / 2478.58 | 150.03 / 2511.86 | -3.04 |
| `DAZZLING_GLEAM` | 269.05 / 4504.65 | 256.05 / 4286.89 | 256.04 / 4286.82 | -13.01 |
| `POUND` | 30.03 / 502.72 | 28.98 / 485.23 | 29.01 / 485.72 | -1.02 |
| `KARATE_CHOP` | 58.02 / 971.40 | 57.01 / 954.51 | 57.01 / 954.53 | -1.01 |
| `DOUBLESLAP` | 22.04 / 368.99 | 21.02 / 351.86 | 21.02 / 351.91 | -1.02 |
| `FIRE_PUNCH` | 50.08 / 838.55 | 49.04 / 820.98 | 49.04 / 821.02 | -1.05 |
| `ICE_PUNCH` | 75.03 / 1256.14 | 74.01 / 1239.13 | 74.01 / 1239.15 | -1.01 |
| `THUNDERPUNCH` | 142.90 / 2392.54 | 141.00 / 2360.75 | 141.01 / 2360.88 | -1.89 |
| `BODY_SLAM` | 91.08 / 1524.95 | 88.04 / 1473.95 | 90.02 / 1507.14 | -1.06 |
| `SWORDS_DANCE` | 63.04 / 1055.44 | 61.02 / 1021.62 | 61.03 / 1021.74 | -2.01 |
| `CUT` | 37.06 / 620.46 | 36.02 / 603.14 | 36.02 / 603.02 | -1.04 |
| `GUST` | 139.02 / 2327.61 | 96.98 / 1623.75 | 111.01 / 1858.60 | -28.01 |
| `FLY` | 71.12 / 1190.66 | 69.03 / 1155.70 | 69.02 / 1155.58 | -2.10 |
| `VINE_WHIP` | 91.11 / 1525.38 | 87.03 / 1457.08 | 87.01 / 1456.78 | -4.10 |
| `DOUBLE_KICK` | 22.03 / 368.77 | 21.01 / 351.76 | 21.01 / 351.78 | -1.01 |
| `SURF` | 379.03 / 6345.91 | 376.98 / 6311.72 | 377.01 / 6312.17 | -2.02 |
| `ICE_BEAM` | 184.03 / 3081.21 | 170.01 / 2846.50 | 170.01 / 2846.51 | -14.02 |
| `BLIZZARD` | 213.03 / 3566.64 | 211.03 / 3533.20 | 213.01 / 3566.40 | -0.01 |
| `HYPER_BEAM` | 73.16 / 1224.95 | 68.06 / 1139.51 | 71.12 / 1190.66 | -2.05 |
| `EARTHQUAKE` | 103.05 / 1725.33 | 102.02 / 1708.12 | 102.02 / 1708.16 | -1.03 |
| `DIG` | 192.03 / 3215.16 | 181.01 / 3030.60 | 194.00 / 3248.12 | +1.97 |
| `PSYCHIC_M` | 220.03 / 3683.84 | 179.01 / 2997.11 | 214.01 / 3583.12 | -6.02 |
| `RECOVER` | 174.02 / 2913.56 | 99.02 / 1657.86 | 113.00 / 1891.99 | -61.02 |
| `SELFDESTRUCT` | 88.95 / 1489.19 | 81.02 / 1356.52 | 83.03 / 1390.12 | -5.92 |
| `EXPLOSION` | 90.07 / 1507.95 | 81.03 / 1356.64 | 83.03 / 1390.11 | -7.04 |
| `SWIFT` | 81.04 / 1356.82 | 80.01 / 1339.63 | 80.01 / 1339.65 | -1.03 |
| `SOLARBEAM` | 215.02 / 3600.04 | 208.01 / 3482.63 | 208.00 / 3482.50 | -7.02 |
| `SHADOW_BALL` | 204.06 / 3416.47 | 158.06 / 2646.31 | 191.02 / 3198.24 | -13.03 |
| `ROLLOUT` | 50.22 / 840.75 | 49.09 / 821.98 | 50.09 / 838.72 | -0.12 |
| `RAIN_DANCE` | 153.04 / 2562.24 | 151.99 / 2544.73 | 152.04 / 2545.48 | -1.00 |
| `SUNNY_DAY` | 153.02 / 2561.98 | 151.98 / 2544.61 | 152.03 / 2545.36 | -0.99 |
| `WHIRLPOOL` | 271.02 / 4537.66 | 153.02 / 2562.05 | 261.01 / 4370.04 | -10.01 |
| `DRAGON_DANCE` | 165.06 / 2763.55 | 156.03 / 2612.31 | 156.03 / 2612.33 | -9.03 |

### Broader First-Invocation Wrapper

| Move | Side | Production intervals / ms | Final intervals / ms |
| --- | --- | ---: | ---: |
| `THUNDERSHOCK` | player | 204.01 / 3415.71 | 194.01 / 3248.22 |
| `THUNDERSHOCK` | foe | 200.00 / 3348.53 | 193.01 / 3231.55 |
| `THUNDERBOLT` | player | 305.01 / 5106.65 | 292.01 / 4888.99 |
| `THUNDERBOLT` | foe | 314.00 / 5257.19 | 289.54 / 4847.62 |
| `THUNDER` | player | 288.01 / 4822.13 | 285.01 / 4771.81 |
| `THUNDER` | foe | 288.00 / 4821.92 | 285.01 / 4771.88 |
| `HYDRO_PUMP` | player | 310.00 / 5190.16 | 303.50 / 5081.42 |
| `HYDRO_PUMP` | foe | 321.01 / 5374.51 | 308.52 / 5165.40 |
| `WATER_PULSE` | player | 315.00 / 5273.93 | 305.01 / 5106.77 |
| `WATER_PULSE` | foe | 325.04 / 5442.05 | 312.00 / 5223.76 |
| `WATERFALL` | player | 358.07 / 5995.00 | 345.00 / 5776.22 |
| `WATERFALL` | foe | 359.97 / 6026.91 | 346.98 / 5809.46 |
| `SLEEP_POWDER` | player | 227.28 / 3805.21 | 223.19 / 3736.74 |
| `SLEEP_POWDER` | foe | 228.24 / 3821.40 | 223.66 / 3744.62 |
| `STUN_SPORE` | player | 224.97 / 3766.68 | 224.50 / 3758.80 |
| `STUN_SPORE` | foe | 227.90 / 3815.69 | 223.99 / 3750.15 |
| `POISONPOWDER` | player | 230.26 / 3855.10 | 222.69 / 3728.46 |
| `POISONPOWDER` | foe | 229.10 / 3835.81 | 223.65 / 3744.50 |
| `SPORE` | player | 226.26 / 3788.25 | 222.68 / 3728.32 |
| `SPORE` | foe | 228.23 / 3821.27 | 222.67 / 3728.07 |
| `FIRE_BLAST` | player | 306.99 / 5139.90 | 302.00 / 5056.33 |
| `FIRE_BLAST` | foe | 362.00 / 6060.87 | 308.00 / 5156.77 |
| `ACID` | player | 179.96 / 3012.95 | 175.00 / 2929.96 |
| `ACID` | foe | 186.01 / 3114.27 | 178.98 / 2996.68 |
| `CAUSTIC` | player | 288.00 / 4821.85 | 279.00 / 4671.23 |
| `CAUSTIC` | foe | 303.00 / 5073.02 | 286.50 / 4796.81 |
| `CORROSION` | player | 254.00 / 4252.61 | 250.49 / 4193.89 |
| `CORROSION` | foe | 262.00 / 4386.62 | 254.48 / 4260.73 |
| `WISH` | player | 148.88 / 2492.58 | 147.45 / 2468.77 |
| `WISH` | foe | 150.87 / 2525.91 | 143.44 / 2401.61 |
| `DISARMING_VOICE` | player | 156.00 / 2611.90 | 145.00 / 2427.67 |
| `DISARMING_VOICE` | foe | 160.04 / 2679.52 | 153.50 / 2570.01 |
| `FAIRY_WIND` | player | 212.00 / 3549.43 | 205.00 / 3432.25 |
| `FAIRY_WIND` | foe | 214.97 / 3599.23 | 210.00 / 3515.97 |
| `SILVER_WIND` | player | 209.03 / 3499.65 | 195.50 / 3273.20 |
| `SILVER_WIND` | foe | 208.00 / 3482.51 | 201.00 / 3365.29 |
| `SLUDGE_WAVE` | player | 253.03 / 4236.35 | 239.50 / 4009.85 |
| `SLUDGE_WAVE` | foe | 255.00 / 4269.43 | 242.50 / 4060.09 |
| `SLUDGE_BOMB` | player | 198.99 / 3331.68 | 181.01 / 3030.54 |
| `SLUDGE_BOMB` | foe | 187.00 / 3130.88 | 183.50 / 3072.29 |
| `SUPERPOWER` | player | 390.00 / 6529.58 | 383.99 / 6429.03 |
| `SUPERPOWER` | foe | 400.98 / 6713.46 | 390.50 / 6538.05 |
| `WILD_CHARGE` | player | 428.01 / 7166.10 | 412.01 / 6898.15 |
| `WILD_CHARGE` | foe | 438.00 / 7333.31 | 411.01 / 6881.45 |
| `SHOCK_WAVE` | player | 378.02 / 6329.07 | 368.01 / 6161.42 |
| `SHOCK_WAVE` | foe | 387.97 / 6495.64 | 370.00 / 6194.73 |
| `LEAF_BLADE` | player | 313.02 / 5240.73 | 313.01 / 5240.61 |
| `LEAF_BLADE` | foe | 321.01 / 5374.51 | 312.52 / 5232.36 |
| `FORCE_PALM` | player | 159.99 / 2678.68 | 152.03 / 2545.35 |
| `FORCE_PALM` | foe | 165.97 / 2778.85 | 159.50 / 2670.45 |
| `RAZOR_LEAF` | player | 296.59 / 4965.64 | 294.01 / 4922.51 |
| `RAZOR_LEAF` | foe | 394.52 / 6605.39 | 291.51 / 4880.72 |
| `MAGICAL_LEAF` | player | 301.01 / 5039.77 | 294.01 / 4922.46 |
| `MAGICAL_LEAF` | foe | 399.00 / 6680.36 | 293.01 / 4905.81 |
| `SEISMIC_TOSS` | player | 337.00 / 5642.25 | 332.54 / 5567.55 |
| `SEISMIC_TOSS` | foe | 341.00 / 5709.29 | 338.50 / 5667.40 |
| `AROMATHERAPY` | player | 167.90 / 2811.02 | 161.96 / 2711.58 |
| `AROMATHERAPY` | foe | 177.89 / 2978.28 | 163.44 / 2736.39 |
| `PETAL_DANCE` | player | 371.01 / 6211.65 | 333.01 / 5575.43 |
| `PETAL_DANCE` | foe | 443.00 / 7417.04 | 335.51 / 5617.37 |
| `OUTRAGE` | player | 342.00 / 5726.01 | 337.00 / 5642.30 |
| `OUTRAGE` | foe | 350.13 / 5862.18 | 342.01 / 5726.15 |
| `DRAGON_CLAW` | player | 377.03 / 6312.55 | 368.50 / 6169.65 |
| `DRAGON_CLAW` | foe | 395.00 / 6613.37 | 374.00 / 6261.78 |
| `METEOR_DIVE` | player | 283.03 / 4738.73 | 279.50 / 4679.55 |
| `METEOR_DIVE` | foe | 292.00 / 4888.90 | 281.00 / 4704.71 |
| `AERIAL_CRASH` | player | 186.93 / 3129.74 | 181.01 / 3030.56 |
| `AERIAL_CRASH` | foe | 196.00 / 3281.51 | 189.49 / 3172.62 |
| `PILEDRIVER` | player | 306.99 / 5139.92 | 298.00 / 4989.31 |
| `PILEDRIVER` | foe | 311.97 / 5223.25 | 304.50 / 5098.18 |
| `OVERHEAT` | player | 359.99 / 6027.26 | 347.00 / 5809.71 |
| `OVERHEAT` | foe | 377.10 / 6313.66 | 354.50 / 5935.29 |
| `POISON_GAS` | player | 501.27 / 8392.64 | 496.69 / 8315.86 |
| `POISON_GAS` | foe | 527.24 / 8827.43 | 495.67 / 8298.86 |
| `HEAT_WAVE` | player | 216.99 / 3632.95 | 206.99 / 3465.58 |
| `HEAT_WAVE` | foe | 224.97 / 3766.65 | 211.48 / 3540.77 |
| `WILL_O_WISP` | player | 201.20 / 3368.65 | 195.18 / 3267.86 |
| `WILL_O_WISP` | foe | 203.03 / 3399.20 | 197.17 / 3301.14 |
| `BRICK_BREAK` | player | 165.67 / 2773.83 | 161.16 / 2698.17 |
| `BRICK_BREAK` | foe | 174.65 / 2924.11 | 166.65 / 2790.24 |
| `METEOR_MASH` | player | 229.00 / 3834.07 | 221.00 / 3700.10 |
| `METEOR_MASH` | foe | 235.00 / 3934.57 | 227.03 / 3801.07 |
| `SIGNAL_BEAM` | player | 254.00 / 4252.72 | 236.50 / 3959.62 |
| `SIGNAL_BEAM` | foe | 272.00 / 4553.95 | 241.50 / 4043.35 |
| `SHADOW_PUNCH` | player | 218.99 / 3666.56 | 214.52 / 3591.69 |
| `SHADOW_PUNCH` | foe | 235.00 / 3934.59 | 219.00 / 3666.66 |
| `EXTRASENSORY` | player | 237.00 / 3968.02 | 228.52 / 3826.07 |
| `EXTRASENSORY` | foe | 241.00 / 4034.99 | 234.00 / 3917.77 |
| `BULLET_SEED` | player | 137.99 / 2310.41 | 132.00 / 2210.01 |
| `BULLET_SEED` | foe | 150.09 / 2512.97 | 133.50 / 2235.16 |
| `IRON_DEFENSE` | player | 263.00 / 4403.34 | 251.00 / 4202.40 |
| `IRON_DEFENSE` | foe | 256.00 / 4286.13 | 250.50 / 4194.05 |
| `MUD_SHOT` | player | 186.00 / 3114.17 | 161.01 / 2695.73 |
| `MUD_SHOT` | foe | 173.11 / 2898.36 | 166.50 / 2787.66 |
| `MOONBLAST` | player | 254.94 / 4268.39 | 252.99 / 4235.74 |
| `MOONBLAST` | foe | 263.01 / 4403.43 | 257.99 / 4319.49 |
| `DAZZLING_GLEAM` | player | 325.00 / 5441.36 | 321.00 / 5374.42 |
| `DAZZLING_GLEAM` | foe | 345.01 / 5776.32 | 324.50 / 5433.03 |
| `POUND` | player | 100.09 / 1675.84 | 94.99 / 1590.37 |
| `POUND` | foe | 103.99 / 1741.09 | 99.00 / 1657.50 |
| `KARATE_CHOP` | player | 130.99 / 2193.15 | 121.50 / 2034.22 |
| `KARATE_CHOP` | foe | 133.00 / 2226.80 | 127.00 / 2126.33 |
| `DOUBLESLAP` | player | 50.99 / 853.79 | 50.00 / 837.13 |
| `DOUBLESLAP` | foe | 55.97 / 937.16 | 49.00 / 820.39 |
| `FIRE_PUNCH` | player | 213.99 / 3582.83 | 212.00 / 3549.46 |
| `FIRE_PUNCH` | foe | 217.00 / 3633.18 | 216.50 / 3624.82 |
| `ICE_PUNCH` | player | 144.99 / 2427.61 | 137.50 / 2302.06 |
| `ICE_PUNCH` | foe | 147.97 / 2477.43 | 145.00 / 2427.73 |
| `THUNDERPUNCH` | player | 214.01 / 3583.16 | 209.51 / 3507.74 |
| `THUNDERPUNCH` | foe | 222.00 / 3716.91 | 210.01 / 3516.12 |
| `BODY_SLAM` | player | 172.54 / 2888.85 | 158.53 / 2654.18 |
| `BODY_SLAM` | foe | 170.00 / 2846.27 | 161.00 / 2695.57 |
| `SWORDS_DANCE` | player | 173.99 / 2913.09 | 163.01 / 2729.23 |
| `SWORDS_DANCE` | foe | 168.00 / 2812.80 | 163.50 / 2737.42 |
| `CUT` | player | 112.00 / 1875.18 | 101.00 / 1691.02 |
| `CUT` | foe | 115.00 / 1925.36 | 105.00 / 1757.98 |
| `GUST` | player | 182.96 / 3063.19 | 175.50 / 2938.34 |
| `GUST` | foe | 212.00 / 3549.43 | 180.48 / 3021.79 |
| `FLY` | player | 105.02 / 1758.34 | 98.48 / 1648.81 |
| `FLY` | foe | 100.96 / 1690.38 | 95.99 / 1607.17 |
| `VINE_WHIP` | player | 169.02 / 2829.81 | 157.01 / 2628.74 |
| `VINE_WHIP` | foe | 171.97 / 2879.28 | 159.99 / 2678.75 |
| `DOUBLE_KICK` | player | 54.99 / 920.76 | 48.00 / 803.65 |
| `DOUBLE_KICK` | foe | 51.00 / 853.87 | 48.50 / 812.02 |
| `SURF` | player | 446.00 / 7467.19 | 443.53 / 7425.82 |
| `SURF` | foe | 453.00 / 7584.41 | 445.99 / 7467.01 |
| `ICE_BEAM` | player | 242.00 / 4051.77 | 238.49 / 3992.95 |
| `ICE_BEAM` | foe | 262.00 / 4386.59 | 239.50 / 4009.86 |
| `BLIZZARD` | player | 286.00 / 4788.42 | 277.99 / 4654.31 |
| `BLIZZARD` | foe | 289.05 / 4839.53 | 282.51 / 4729.98 |
| `HYPER_BEAM` | player | 196.00 / 3281.57 | 195.50 / 3273.19 |
| `HYPER_BEAM` | foe | 201.98 / 3381.66 | 201.00 / 3365.28 |
| `EARTHQUAKE` | player | 278.00 / 4654.39 | 276.00 / 4620.98 |
| `EARTHQUAKE` | foe | 283.97 / 4754.47 | 283.00 / 4738.20 |
| `DIG` | player | 229.95 / 3849.95 | 222.48 / 3724.87 |
| `DIG` | foe | 223.96 / 3749.68 | 221.97 / 3716.44 |
| `PSYCHIC_M` | player | 285.00 / 4771.63 | 279.00 / 4671.21 |
| `PSYCHIC_M` | foe | 297.00 / 4972.58 | 284.01 / 4755.09 |
| `RECOVER` | player | 155.88 / 2609.85 | 140.99 / 2360.63 |
| `RECOVER` | foe | 206.87 / 3463.63 | 141.95 / 2376.57 |
| `SELFDESTRUCT` | player | 122.96 / 2058.74 | 117.99 / 1975.55 |
| `SELFDESTRUCT` | foe | 128.97 / 2159.31 | 119.02 / 1992.70 |
| `EXPLOSION` | player | 125.96 / 2108.97 | 117.99 / 1975.43 |
| `EXPLOSION` | foe | 130.97 / 2192.77 | 119.47 / 2000.24 |
| `SWIFT` | player | 152.00 / 2544.91 | 143.49 / 2402.41 |
| `SWIFT` | foe | 157.99 / 2645.24 | 149.49 / 2502.79 |
| `SOLARBEAM` | player | 240.95 / 4034.13 | 232.98 / 3900.69 |
| `SOLARBEAM` | foe | 250.96 / 4201.76 | 235.97 / 3950.84 |
| `SHADOW_BALL` | player | 261.00 / 4369.80 | 255.04 / 4270.06 |
| `SHADOW_BALL` | foe | 277.04 / 4638.38 | 260.50 / 4361.46 |
| `ROLLOUT` | player | 124.00 / 2076.09 | 120.00 / 2009.12 |
| `ROLLOUT` | foe | 127.00 / 2126.27 | 126.00 / 2109.56 |
| `RAIN_DANCE` | player | 187.93 / 3146.38 | 188.98 / 3164.02 |
| `RAIN_DANCE` | foe | 187.92 / 3146.25 | 186.97 / 3130.32 |
| `SUNNY_DAY` | player | 183.91 / 3079.16 | 178.46 / 2987.90 |
| `SUNNY_DAY` | foe | 184.91 / 3095.84 | 179.96 / 3013.00 |
| `WHIRLPOOL` | player | 338.99 / 5675.68 | 326.99 / 5474.71 |
| `WHIRLPOOL` | foe | 345.97 / 5792.54 | 330.48 / 5533.18 |
| `DRAGON_DANCE` | player | 195.88 / 3279.51 | 194.95 / 3263.96 |
| `DRAGON_DANCE` | foe | 203.86 / 3413.23 | 194.93 / 3263.64 |

### Sound Dispatch

Sound-count and order differences below are observations, not omissions.
All 640 move/side/start-phase pairs are compared. Controller-generated
sounds can interleave differently even when their
counts and script-owned launch order are preserved. Raw captures retain
each dispatch timestamp and individual clips retain native audio.

- Sound-count differences: `[]`.
- Merged-order differences: `[('CAUSTIC', 'foe', 0), ('CAUSTIC', 'foe', 17556), ('CAUSTIC', 'foe', 35112), ('CAUSTIC', 'foe', 52668)]`.
- Caustic foe interleaving matches the accepted prior local-motion build
  at each of those phases; it is not a new change from this expansion.

Caustic at phase zero, times in physical display intervals from primary-script entry:

| Side/component | Production dispatch times | Final dispatch times |
| --- | --- | --- |
| player launch | 6.1, 17.1, 28.1, 39.1, 50.1, 62.1, 74.1, 88.0, 103.0 | 5.1, 17.0, 29.0, 41.0, 53.0, 65.1, 77.0, 89.0, 101.0 |
| player pop | 69.1, 81.1, 96.1, 110.2, 123.1, 135.1, 146.1, 157.0, 168.0 | 69.0, 82.0, 98.0, 105.1, 118.0, 134.0, 141.0, 154.0, 170.0 |
| foe launch | 6.1, 17.2, 28.1, 39.1, 51.1, 63.1, 75.2, 90.0, 109.1 | 5.0, 17.0, 29.0, 41.0, 53.0, 65.0, 77.0, 89.0, 101.0 |
| foe pop | 77.0, 92.1, 111.1, 130.1, 143.2, 155.1, 166.1, 177.0, 188.0 | 69.0, 82.0, 98.1, 105.0, 118.1, 134.0, 141.0, 154.0, 170.0 |
<!-- EXPANDED_RESULTS_END -->

## Findings And Limits

- Automated completion, clean ownership and zero playback misses do not prove
  visual acceptance. Native comparisons/contact sheets are retained for all
  80 moves on both sides: 160 comparisons and 320 individual audio clips.
  Selected contact sheets were inspected, not every video watched in real
  time; the review ROM is for the user's judgment.
- The normal opponent can be markedly slower than the normal player. The new
  orientation curves preserve its geometry, not every old flipped-trig delay.
  Fire Blast is about 182 intervals on either side, versus about 183 for the
  production player and 264 for the production opponent. The latter difference
  is expected and is not work to undo. Differences in actual motion/phase
  rhythm still warrant review; exact old-opponent equality is not a goal.
- Seismic Toss's primary body finishes within about one interval on both sides,
  but its background/palette cycle is not phase-identical to production.
  Inspected native contacts show different palette states at some equal elapsed
  intervals. Duration matching alone does not qualify that visual rhythm.
- Thunderbolt's previously accepted treatment is retained, not changed again
  to match its old aftereffect-controller overhead. Petal Dance remains faster
  deliberately. Small controller/lifetime differences in Silver Wind,
  Aromatherapy, Overheat and other effects remain visible in the detailed data.
- Caustic retains the accepted bubble-launch and bubble-pop sound treatment.
  Both event streams are recorded separately above. The foe-side merged order
  still differs from production, but is unchanged from the accepted prior
  local-motion build at all four offsets. Timing work is not a fix
  for its existing ten-sprites-per-scanline capacity problem.
- The deferred battle-menu glyph/switch flash and Glacial Slam replacement
  issues are not addressed. Existing battle cry ownership risk is not closed
  by these controlled audio cases. No animation-speed change is promoted.
- Timing fixtures deliberately use high HP to avoid KO interruptions. Their
  normal opponent is Pidgey and the current native prototype donor is Hoothoot;
  both are 5x5 frontpics. This is not pixel-identical scene comparison or a
  claim that ROM/DIV-dependent battle RNG is identical. The delivered save has
  normal level-30 Pokemon/stats, not the artificial timing-fixture HP display.

### Host Fixture And Parallelism Corrections

Two earlier expanded sweeps timed out after player Hyper Beam at offsets
35112/52668. The requested animation had returned normally. A native probe
found damage 912 before `_PlayBattleAnim`, versus 900 HP, followed by a genuine
KO. The factory had adjusted battle stats but left the unmodified critical-hit
stat caches inconsistent. The final A/B rerun explicitly uses coherent party,
player and enemy caches in **both** arms. This is a host-only fixture correction,
not a game fix, not a discarded failure, and not a change to damage mechanics.

Simultaneous rendered/extra-consumer jobs also exposed a host executable-path
collision. Rebuilding an observer in place while another worker used it could
terminate that worker or reject commands. Setup paths now include ROM identity,
purpose and requested move-set identity. Affected captures were re-run with
separate observers. Reported results use the clean reruns, not the failed files.

## Manual Review Save

The private save is at Cherrygrove's Pokemon Center. Its six party members hold
the priority effects together; other suite moves are in **Box 14**. All 82 move
indexes/names/PP, Continue loading and PC deposit/withdrawal are checked in
normal, unpaced-double and retimed arms. The extra two are Volt Tackle and
Energy Ball. The user's live save is not edited.

| Party | Moves |
| --- | --- |
| Kyogre / WATER | Surf, Water Pulse, Hydro Pump, Waterfall |
| Meganium / LEAVES | Leaf Blade, Razor Leaf, Magical Leaf, Petal Dance |
| Dusknoir / HAZE | Poison Gas, Caustic, Whirlpool, Gust |
| Garchomp / CHARGE | Dragon Dance, Superpower, SolarBeam, Dazzling Gleam |
| Mewtwo / MIND | Psychic, Recover, Shadow Ball, Seismic Toss |
| Metagross / OTHER | Thunderbolt, Shock Wave, Wild Charge, Fire Blast |

Review Surf through completion and the restored battle menu first. Then review
the water effects, Leaf Blade/Razor Leaf, Poison Gas/Whirlpool/Recover, additional
charges and both Caustic sound components. Check the other Box-14 moves as
desired. A no-miss result alone does not decide whether a motion feels natural.

## Evidence And Reproduction

Root: `build/battle-motion-reference-20261004/` (ignored host output).

- `prototype-surf-cleanup/`: immutable corrected base and private sources.
- `prototype-expanded[-v2]/`: retained earlier expanded stages and build logs.
- `prototype-expanded-v3/`: final private sources, ROM/symbol/map and recipe metadata.
- `regression-coherent/{production,expanded-v3}/`: 1280 native battle results
  and compressed full traces; each move/side/start offset is distinct.
- `expansion/phases-expanded-v3.json`: complete phase, object and sound analysis.
- `expanded-v3-qualification/`: cry, menu, all-species Dex, New Entry, review-save
  and visual results. `visuals/videos.json` indexes individual audio clips and
  labeled silent A/B comparisons. Comparisons align at primary-script entry.
  `SCRIPT END (padded)` freezes that arm's last primary-script display solely
  to align unequal durations; it is not a native animation hang or a claim
  that HUD/outer-wrapper cleanup has finished. Individual audio clips retain
  another 16 native displays after primary-script exit.
- `surf-cleanup-diagnostic-production-expanded-v3/`: cleanup/interrupt observations
  and native battle-exit screenshots.
- `wild-intro/`: wild and trainer pixel-translation cadence comparisons.

Host recipes use the retained matching-link production references; preserving
only the Python script without its reference data is not sufficient to regenerate
the same sampled curves. Keep the ignored evidence tree for future retiming work.

```sh
env PYTHONPATH=.:tools python3 tools/build_battle_motion_expansion.py \
  --output build/battle-motion-reference-20261004/prototype-expanded-v3 \
  --refine-bursts --jobs 24

env PYTHONPATH=.:tools python3 -m tools.dex_timing.animation_reference \
  --variants production expanded-v3 --regression --coherent-fixture --jobs 32

env PYTHONPATH=.:tools python3 -m tools.dex_timing.motion_expansion \
  --candidate expanded-v3 --folder regression-coherent

env PYTHONPATH=.:tools python3 -m tools.dex_timing.motion_expansion_report \
  --candidate expanded-v3
```

Use a distinct output directory for a new revision; do not rebuild a cartridge
or observer beneath running workers. `--refresh` is only for this builder's
generated private checkout, never for the production working tree.
