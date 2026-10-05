# Double-speed game, normal-speed battles

2026-10-05. Private trial requested after the expanded move-retiming prototype
was rejected. Artifact directories retain their `20261004` investigation date.
**Production source, ROM and live saves are unchanged.**

Historical report: the accepted final cartridge was promoted byte-for-byte
on 2026-10-05. See [production clock policy and fresh qualification](production_clock_policy.md).
The unchanged-production statements below describe this trial before promotion.

Manual review accepted this private baseline on 2026-10-05. The user noted a
possible slightly weaker Superpower target shake in the comparison video, but
found it acceptable in-game. This is recorded as `BATTLE-ANIM-03`, not silently
corrected or treated as a confirmed amplitude regression. Production promotion
remains a separate step.

The prototype retains the accepted unretimed double-speed/Dex performance
baseline, but executes battle-owned gameplay at normal speed. No move script,
frameset, object function, vibration amplitude, BG-effect function or sound
schedule is retimed. The rejected pacing gates and motion tables are absent.

## Result

The final automated qualification passes its defined acceptance checks, with
the existing production wild-appearance cry failures explicitly excluded from
any claim of universally successful battle audio. All 100 moves execute on both
sides. Their logical motion, object-state, BG-effect-state and sound sequences
match production. Physical holds are close, not cycle-identical: the largest
paired primary-effect difference is 9.99 display-equivalent intervals, and no
move/side median differs by 10% or more.

There are no new final-build sampled playback failures in the tested contexts.
A genuine first-revision Vibrava regression was isolated and corrected before
the complete final-link rerun. Manual acceptance of motion and the hidden
battle-music handoff is still required; these are not hardware certification or
an exhaustive playthrough of every event in the game.

## Build identity and review files

| Item | Identity |
| --- | --- |
| Production source baseline | `2cec8051763e01b45fc2da51186ef795477fe7d4` |
| Production ROM SHA-256 | `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666` |
| Accepted unretimed global-double ROM | `5c18007b0ac98c7cf6b97952ed656a2cefd230638fa36825cc851e3b10fe5e90` |
| Final normal-battle prototype ROM | `94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec` |
| SameBoy source | `213a12ce93d66b105a113debd9396306066a7cfc`, CGB-E |

Main ROM, symbols, map, provenance and private source are under
`build/battle-normal-speed-20261004/prototype/`. The complete test records,
native inputs, compressed observations and frame archives are under the parent
directory. `initial-revision/` and `timer-controls/` retain the rejected timer
overhead and its controls, not the final acceptance results.

The 2026-10-05 disk cleanup moves bulky loose historical/case files into verified
lossless archives under `build/retained-history-20261005/`. Original relative
paths, per-file hashes and recovery instructions are recorded there. Current
source snapshots, ROM/save review pairs, aggregate results and comparison videos
remain at their original paths. Recover archived checkpoints/traces into a
scratch directory before rerunning historical replay commands. The retained
Thunderbolt evidence under `research_artifacts/` is not part of this cleanup.

The later user-approved compaction moves retained historical members into
`build/retained-history-20261005/compact/`. Reports/reference JSON, exact ROMs,
saves/starting states, source and review media survive; superseded per-test
JSONL/frame/audio bulk is intentionally retired. Current production-run
qualification is separately retained losslessly. The original catalogs are
audit records, not recoverable copies of retired content; see
[current archive policy](archived/README.md#approved-follow-up-compaction).

The isolated manual-review pair is:

- `manual-review/battle-normal/pokecrystal-animation-battle-normal.gbc`
- `manual-review/battle-normal/pokecrystal-animation-battle-normal.sav`
- `manual-review/normal/pokecrystal-animation-normal.gbc` and matching `.sav`
  provide the production comparison.

These are battery saves, not CPU states, and both are verified through native
party/PC deposit and withdrawal. Start each ROM from boot; never transfer a CPU
save state between differently linked ROMs. No live SameBoy save was edited.

All 100 moves are available. The six level-30 party members are:

| Pokemon / nickname | Moves |
| --- | --- |
| Kyogre / BIGDIFF | Poison Gas, Surf, Whirlpool, Leaf Blade |
| Garchomp / HEAVY | Hydro Pump, Superpower, Fire Blast, Water Pulse |
| Luxray / RESTORE | Thunderbolt, Thundershock, Caustic, Dragon Dance |
| Rayquaza / CHARGE | SolarBeam, Dazzling Gleam, Overheat, Petal Dance |
| Meganium / LEAVES | Razor Leaf, Magical Leaf, Seismic Toss, Earthquake |
| Dusknoir / MORE | Sludge Wave, Sludge Bomb, Meteor Dive, Aerial Crash |

The remaining 76 moves are on 19 Pokemon in **Box 14, ANIMS**. The full
move-to-party/box mapping is `manual-review/animation-review.json`.

## Clock ownership

1. Ordinary CGB initialization, overworld and menus retain global double speed.
2. The existing battle wipe still runs at double speed. Immediately after
   `DoBattleTransition`, while the BG is black and its scanline work has ended,
   `BattleSpeed_EnterNormal` waits for SFX, disables LCD/interrupts, stops any
   owned sample defensively, disables the APU, requests normal speed and
   reinitializes sound. It restores IE, enables LCD and restarts battle music.
3. Battle intro, menus, moves, nested Pack/Party/Stats, catching, New Dex Entry
   and post-battle evolution inherit normal speed. These nested owners do not
   independently toggle clocks. Normal-speed CPU bottlenecks remain; avoiding
   them is future targeted work, not the goal of this trial.
4. Battle cleanup clears `wBattleMode`. The existing map-setup DisableLCD
   command invokes `BattleSpeed_MapDisableLCD` at its unchanged command ID.
   Only when battle ownership has ended does it call `BattleSpeed_LeaveNormal`.
   LCD/APU are off during the switch. Sound is reinitialized and LCD remains
   off for the original map graphics reload and map-music restoration.
5. Ordinary map reloads already at double speed take the fast return. Native
   whiteout warps also pass through this map-setup boundary. The policy does
   not equate clearing the battle flag with an already restored overworld.

All 140 actual switches in the dedicated final stress suite occur with LCD,
APU and sampled playback disabled. There are no SameBoy odd-mode warnings.
Multiplayer/mobile/infrared entry paths remain disabled and outside scope.

The catch tutorial's `StartBattle` and script reload, and Battle Tower's
`StartBattle` -> `FadeOutToWhite` -> `reloadmap` paths were source-audited for
the same boundary. A full tutorial playback and seven-trainer Tower challenge
were **not** executed in this pass. They remain useful manual/specialized
coverage before promotion if those areas are part of the release acceptance.

### Handoff delay and audio tradeoff

The quarter-zero continuous trace measures about **4.283 display-equivalent
intervals / 71.71ms** inside the entry wrapper, and **1.072 / 17.94ms** inside
the return-speed wrapper. The entry/return `SwitchSpeed` spans themselves are
approximately **1.867 / 31.26ms** and **0.934 / 15.64ms**, respectively, in this
SameBoy model. The return map-disable wrapper including its native LCD wait
takes about **1.972 / 33.01ms**. These nested costs must not be added twice.

LCD-off time is measured as elapsed physical time expressed in equivalent LCD
intervals, not as newly displayed pictures. This is a small additional black
handoff, not a zero-cost switch. It is intentionally outside visible motion.
Battle music begins before the original wipe and is restarted after the sound
reset. Listen for that restart/gap during manual review. Preserving an active
APU across the double-to-normal switch was deliberately not used.

## Sampled timer correction

The inherited global-speed implementation called
`SampledCry_AlternateBlockTimer` for every decoded block, even when normal-speed
playback did not need alternating reloads. Its zero-step call costs **64 normal
T cycles**: CALL 24, absolute LD 16, AND 4, taken conditional RET 20.

That extra IRQ work makes Vibrava's native appearance cry stop at 200 of 217
blocks in the initial prototype. Production completes 217. A control removing
the call completes 217; a conditional-call control still misses; the final
dispatch control completes 217. All controls retain their reports. The final
four-offset/six-context rerun completes every Vibrava segment.

The final handler uses the existing `hSampledCryTimer` byte as:

- 0: inactive.
- 1: normal-speed or even-period playback, original active-IRQ budget.
- 2: double-speed odd-period playback requiring floor/ceil reload alternation.

Normal active dispatch changes AND/JR NZ to DEC/JR Z, with the same instruction
time. Its block handler is the original production body. Only value 2 enters
the extra bank-preserving timer helper. All other readers already test zero
versus nonzero, and cancellation still clears the byte. No HRAM is added.
The inactive return is 16 T cycles longer; the shared odd-period path has extra
bank-save/dispatch work. Both are covered separately rather than charging that
work to every ordinary sampled block.

Odd-period compatibility was explicitly checked at double speed with period
213 on all 16 sampled species, four offsets, against the accepted global-double
ROM: **128 executions, 64 pairs, no misses or waveform/timer/frequency/content
differences**. These are ABI-based shared-routine fixtures from native menu
states, not a claim that actual fainting takes place in an overworld menu.

## Regression results

All final cases use newly generated matching-link checkpoints. Species/move/
party/XP fixtures change only declared data; native game code performs the
effects, catches, menus and clock switches. Host observation does not patch
timing, speed, hardware or scheduler-ready state. Native tests run in parallel.

| Suite | Final coverage | Result |
| --- | --- | --- |
| Move execution | 100 moves x 2 sides x 4 offsets x 2 ROMs = 1,600 | No execution/clock/setup failures |
| Primary move motion audit | 800 paired effects | Identical logical shadow OAM, native object/BG state and SFX sequences |
| Selected Dex | 6,182 cases, all 373 species | No content, animation, sample, input or ownership failures |
| New Dex Entry | 8,572 cases, 20 species; 1,208,058 displayed frames checked | No misses, exact authored timelines, clean complete/early-exit ownership |
| Cross-owner cry/audio | 960 cases, 20 species x 6 contexts x 4 offsets x 2 ROMs | No new final-build misses; inherited appearance failures below |
| Odd-period audio | 128 explicit shared-routine cases | No misses or playback-setting/content differences |
| Menu inputs/registers | 896 cases across standard, battle, mart, puzzle and Game Corner | No wrong masks/register failures |
| Custom inventory | 232 actions; 5 Pack pockets, 57 TM/HM selections, 7 Apricorn colors | No selection/clock failures; presentation qualifications below |
| Continuous switch stress | 4 streams x 16 consecutive native wild battles, no state reload between battles | 128 safe switches, no playback misses; battle and post-return sampled Stats exercised |
| Whiteout | 4 native defeats/warp returns | Normal battle to double-speed overworld, no misses |
| Post-battle evolution | 4 native wins/XP level-ups, Caterpie -> Metapod and learn-move prompt | Evolution remains normal, map return double; no misses |
| Wild/trainer slide | 64 wild and 8 trainer captures including production comparisons | No irregular pixel translations |
| Native gameplay | 10 scenarios | No failures |
| Review save | 100 distinct moves, party and PC conversion in both ROMs | Both saves verified |
| Host unit checks | 13 tests | Pass |

Selected Dex includes 1,492 Info cases, 746 Moves, 373 cold entries, 373 internal
pages, 2,238 Area transitions, 400 Info stress and 560 Moves stress cases.
New Entry baseline durations equal the scripts, including Dusknoir's 107
intervals. Its startup is normal-speed again, not the faster global-double
registration startup. That and battle-nested menus are expected tradeoffs.

Gameplay exercises connected maps and buildings, item purchase/quantity/Pack
reopen, the Alph sliding-puzzle solution, fishing, a native Joey trainer win,
incoming phone dispatch, Rare Candy/evolution, an egg hatch, a full-party catch
sent to the PC, healing, saving/reboot and soft reset. Walk/bicycle/menu returns
are also covered by the menu suite. This remains bounded automated coverage.

Custom inventory First/Complete timings differ from the accepted double-speed
baseline by less than 0.001 interval at the family medians. TM/HM disc-motion
state sets match that baseline. The older production/double comparison retains
its valid different action-menu frozen phases, not new motion changes here.
Raw OBJ palette hashes differ in transparent or unused slots. Additional
matched native replays of Apricorn/TM/Pack and all five Pack returns produce
identical final pixels and no differing visible nontransparent OBJ colors.
The historical Pack-return screenshots used different day/night world palettes;
fresh returns reach the same night state and are pixel-identical. Those old
screenshots must not be called a new palette regression.

The initial stress-harness retries are also retained: selecting no damaging
move, trying to forget an HM with A-only input, failing to confirm Stats, or
not releasing B before a second B press can legitimately prevent the scripted
test from progressing. These were corrected in the host fixture/driver, not
by changing game behavior. The final 12-case transition report is clean.

## Timing and visual comparisons

Each table cell is median **physical display intervals**, over four offsets,
for the first native `RunBattleAnimScript` span including its preparation.
It excludes later hit/damage scripts, teardown and the outer SFX wait. Multiply
by 16.742706ms for milliseconds; full precision, both sides and all 100 moves
are in `move-timings.csv` and `comparison.json`. This is not a per-move retiming
table shipped in the cartridge.

| Move | Player production / trial | Opponent production / trial |
| --- | ---: | ---: |
| Surf | 377.01 / 377.02 | 379.03 / 378.03 |
| Water Pulse | 241.06 / 246.05 | 247.93 / 243.97 |
| Thunderbolt | 232.03 / 231.02 | 239.91 / 241.03 |
| Caustic | 216.10 / 216.14 | 230.10 / 231.05 |
| Dragon Dance | 156.06 / 155.06 | 165.06 / 167.07 |
| Waterfall | 282.05 / 280.05 | 284.05 / 282.05 |
| Leaf Blade | 238.03 / 239.02 | 242.03 / 240.94 |
| Razor Leaf | 222.00 / 217.03 | 319.02 / 322.03 |
| Magical Leaf | 226.05 / 220.89 | 320.94 / 322.94 |
| Gust | 115.03 / 114.02 | 139.02 / 139.02 |
| Whirlpool | 264.02 / 262.02 | 271.02 / 271.03 |
| Petal Dance | 299.05 / 294.05 | 365.93 / 367.06 |
| Superpower | 317.08 / 315.08 | 323.08 / 324.16 |
| DragonBreath | 232.08 / 222.08 | 328.96 / 328.00 |

No move/side median differs by >=10%. The largest individual paired primary
delta is DragonBreath player, 9.99 intervals / about 167.3ms faster (4.3%).
Logical updates are identical, but some native work crosses a VBlank differently
after the changed entry/music/layout/interrupt phase. The present audit does
not isolate each hold difference's exact contributing instruction. It does
not claim pixel-time identity or introduce compensating stalls to erase them.

The full suite is the original 79 moves plus Dragon Dance, Rock Slide, Volt
Tackle, Energy Ball, Glacial Slam, Icicle Crash, Fire Spin, Flame Wheel, Lava
Plume, Dragon Rage, DragonBreath, Night Slash, X-Scissor, Giga Drain, Sacred
Fire, Hyper Fang, Blaze Kick, Heavy Slam, Rock Blast, Poison Jab and Iron Tail.
The machine-readable report lists all 100 by move constant.

`visuals/` contains 64 individual native-audio clips, 32 synchronized silent
two-column comparisons and player/opponent comparison reels. Sixteen priority
moves are recorded on both sides: Surf, Water Pulse, Dragon Dance, Thunderbolt,
Caustic, SolarBeam, Dazzling Gleam, Superpower, Waterfall, Leaf Blade, Razor Leaf,
Magical Leaf, Gust, Whirlpool, Piledriver and Petal Dance. There is no interpolation
or playback-speed change. Captures use different native foe artwork between
ROMs, with coherent fixture stats/types, so Pokemon/HUD pixel identity is not
an assertion. Raw native frames are losslessly archived and verified before
removal of loose PPMs; final encoding reclaimed about 4.56GiB.

## Known remaining defects

The prototype retains the production wild-appearance cry exhaustion for
Dusknoir (45 blocks remaining), Groudon (198), Kyogre (226) and Yanmega (405).
These are the **first encounter segment** in the catch/faint test scenarios,
not their later New Entry or fainting cries. Production and prototype agree
in those 32 paired cases. Player send-out, the later fainting/New Entry segment
and blocking/stereo playback complete in the tested contexts. This is the
deferred `BATTLE-CRY-01` investigation, not a speed-switch cancellation.

The 20 other cross-owner comparison differences are improvements: six-context
sampling at four offsets shows previously truncated production **outside-battle
Stats** cries for Dusknoir, Vibrava, Groudon, Kyogre and Yanmega complete at double
speed. Do not generalize that improvement to their normal-speed battle appearance.

Production battle-menu glyph corruption/brief switching flash and Glacial Slam
sprite slicing remain open. Normal speed is not presented as a fix for those
existing defects. The future optimization story is
[BATTLE-PERF-01](pokedex_selected_bug_backlog.md#battle-perf-01-targeted-move-animation-performance-and-display-cadence),
including the retained Emerald Thunderbolt cadence evidence.

The accepted review also records the unconfirmed Superpower shake difference
under `BATTLE-ANIM-03`. Its videos remain directly available during build cleanup.

## Incremental cost and risk

Compared with the accepted unretimed global-double baseline:

| Resource | Added |
| --- | ---: |
| ROM0 Home | 24 bytes, timer dispatch compatibility correction |
| ROMX bank B | 80 bytes, entry/return clock and sound ownership |
| ROMX bank 5 | 15 bytes, existing map-disable command wrapper |
| ROMX Dex Performance Index | 3 bytes, odd-period active marker |
| Total | 122 bytes |
| WRAM0 / WRAMX / HRAM / VRAM / OAM | No additional allocation |

The existing global timer-step byte in bank-4 padding and active HRAM byte are
reused. Current linked budget: ROM0 15,861 used / 523 free; mapped ROMX 2,317,924
used / 713,116 free in 185 banks; WRAM0 4,083 / 13 free; WRAMX 23,944 / 4,728 free;
HRAM 127 / 0 free. Free memory is fragmented, not interchangeable across owners.
The padded ROM is 4MiB; allocated ROM sections total 2,333,785 bytes, leaving
about 1.77MiB across mapped gaps and otherwise unallocated cartridge banks.

Implementation complexity is low relative to broad animation reconstruction,
but the hardware/audio boundary is sensitive. Risks are an unsafe APU switch,
restoring double speed before battle-owned work ends, missing a special battle
return, and losing the normal sampled-IRQ budget. The guarded black/LCD-off
handoffs, source audit, native repeated returns, normal IRQ dispatch and full
final-link regressions address those tested risks. Release hardware/other
emulators and remaining special battle paths are not certified by this result.

## Reproduction and manual acceptance

`tools/build_battle_normal_speed_prototype.py` builds only in ignored `build/`
from the accepted global-double source snapshot. Use a fresh `--output` directory;
`--relink` is only for an existing private candidate. It verifies that production
is unchanged. The associated retained host tools are:

```text
tools.dex_timing.battle_normal_speed: moves, audio, odd-timer, registration,
                                    dex-prepare, custom, manual
tools.dex_timing.performance_regression: full Selected regression
tools.dex_timing.new_entry_sweep: full post-catch input sweep
tools.dex_timing.global_speed --suite menus --variants battle-normal
tools.dex_timing.global_gameplay --variants battle-normal
tools.dex_timing.battle_speed_transitions: continuous, whiteout, evolution
tools.dex_timing.battle_intro_reference --variants production battle-normal
tools.dex_timing.battle_normal_speed_report: paired timing/content/resource audit
tools.dex_timing.battle_normal_speed_visuals: native clips and verified archives
tools.dex_timing.battle_speed_menu_comparison: active palette/time-of-day audit
```

For manual review, compare the isolated saves from boot and check the previously
rejected water/leaf/wind/vibration relationships, both Caustic sound phases,
charge motion and battle intro. Enter battle Pack and Party -> Stats, return,
then flee/win/catch and verify outside menus still feel fast. Listen for music
at the wipe and after return. Known encounter-cry misses must be distinguished
from New Entry or speed-switch misses.

Optional final-link breakpoints: Selected animation miss
`$a0:$6671` (`Pokedex_AnimationMiss`) and sampled premature exhaustion
`$00:$3cdc`, the `POP AF` immediately before the cache-exhaustion return sequence
(`f1 e0 70 c3 9e 00` at that address in this ROM). The common
`StopSampledCryAsync_FromTimer` stop also occurs at natural completion and is
not by itself an underrun oracle. Host tests check remaining blocks at the
actual cache-empty path rather than treating every stop as a failure.
