# Battle Animation Interrupt Timing Contract

Recorded 2026-10-12 after the Type Matchups prototype's exhaustive animation
regression. This is a permanent guardrail for shared display code, not a fix or
authorization to retime battle animations.

**DO NOT ADD OVERHEAD TO ORDINARY LCD/VBLANK PATHS: EVEN AN INACTIVE FEATURE
CHECK CAN BREAK BATTLE ANIMATION TIMING.** Preserve their critical cycle budgets.
An intended timing change requires explicit assessment and fresh qualification,
not a claim that the feature's main handler is inactive during battle.

## Exact Changes That Caused The Regression

These executable changes exist in the private Type Matchups prototype, not in
production. The production source receives comment-only warnings referencing
this report. The repeatable prototype changes are retained in
`tools/dex_timing/probes/type_matchups_mode.patch`; its current source is
`build/dex-types-cursors-20261011/candidate/`.

### LCD Interrupt: Rejected Type Dispatch Still Costs 20 T-Cycles

File: `home/lcd.asm`, `LCD`, immediately after the existing zero-pointer exit:

```asm
    ldh a, [hLCDCPointer]
    and a
    jr z, .done
    ; Added by Type Matchups:
    cp $ff
    jp z, PokedexTypes_LCD
```

The existing `hLCDCPointer` selects per-line scroll-register overrides. The
prototype reserves `$ff` for Type Matchups' new ROM0 palette handler. The page
sets this sentinel in `engine/pokedex/pokedex_types.asm:PokedexTypes_Initialize`
and clears it in `PokedexTypes_Leave`.

The newly added instructions cost the ordinary nonzero-pointer path:

| Instruction | Battle Outcome | Added T-Cycles |
| --- | --- | ---: |
| `cp $ff` | Existing SCX/SCY pointer is not `$ff` | 8 |
| `jp z, PokedexTypes_LCD` | Branch not taken | 12 |
| Total | Every active ordinary raster interrupt | 20 |

The original zero-pointer exit is unchanged and bypasses this check. The
20-cycle cost therefore applies when a raster effect enables the ordinary
SCX/SCY override path, not to every possible LCD interrupt. A raster animation
can run this handler repeatedly within a single display frame.

`PokedexTypes_LCD` itself was also added in this file. It reads unbanked Dex
scratch and writes the Type badges' changing palette accents. It does not run
during the tested battles: the rejected dispatch check is the extra battle work.

### Normal VBlank: Rejected Type Check Costs 32 T-Cycles

File: `home/vblank.asm`, `VBlank_Normal`, after shadow OAM transfer at
`.done_oam`, before the existing non-graphics work:

```asm
.done_oam
    ; Added by Type Matchups:
    ldh a, [hLCDCPointer]
    cp $ff
    jr nz, .raster_ready
    ei
.raster_ready
```

The intent was to let the Type-only LCD palette handler interrupt the remaining
VBlank work, preventing missed palette updates. The ordinary path is:

| Instruction | Battle Outcome | Added T-Cycles |
| --- | --- | ---: |
| `ldh a, [hLCDCPointer]` | Read ordinary owner pointer | 12 |
| `cp $ff` | Type owner is inactive | 8 |
| `jr nz, .raster_ready` | Branch taken | 12 |
| Total | Every invocation of ordinary `VBlank_Normal` | 32 |

The Type-only `ei` is not executed in these battles. Its rejection still costs
32 cycles. Actual battle-animation script frames use `VBlank_CutsceneCGB`, not
`VBlank_Normal`; the new normal-path check affects surrounding setup/cleanup
and frame alignment, rather than adding 32 cycles to every script frame.

The shared handler entry/dispatch code is part of the same timing contract.
Moving an extra check to a wrapper does not remove its cost from ordinary users.

## How Tiny Costs Become Visible Animation Delays

`engine/battle_anims/anim_commands.asm:BattleAnimDelayFrame` waits for VBlank
after the animation update's work. If that work finishes just beyond a display
deadline, the next wait can hold the current visible state for an extra whole
frame. One physical frame here is approximately 16.743 ms.

The move scripts and logical update counts did not change. In the worst
Waterfall sample, both links perform 243 logical updates. Production has 30
two-frame gaps between completed updates; the prototype has 60. The entire
animation call is about 33 frames longer, including its surrounding work.
Thus a correct counter and successful return can coexist with visibly different
motion cadence. Different start alignment can also make some cases shorter.

The impact is not confined to Water-type moves. Waterfall, Water Pulse,
Whirlpool, Heat Wave, Extrasensory, and the auxiliary InWhirlpool entry use
`BattleBGEffect_Whirlpool` in `engine/battle_anims/bg_effects.asm`, which enables
per-line SCY updates. Other water effects and unrelated animations also depend
on the shared display scheduling.

## Evidence And Controlled Comparison

Production baseline: commit `6d9fba86f6aa67e465721bfd76a53e5662d93ffc`, ROM SHA-256
`591d2075b0c986846b94bc92288d1fa4f9d2918fccc680a83928fd8fdcf59bee`.

Review prototype ROM SHA-256:
`69705d016d2cd9022bdd2fc3ae28d5884b78548012c430ec70cc8f784000803c`.

Private original-interrupt diagnostic ROM SHA-256:
`1f900cc948f41164445c0b145b1419732e42283e94349695dca55520970f4c53`.
This link retains the new chart/cursor changes but removes both added shared
interrupt checks. It is an isolation control, not a usable Type-page fix.

The linked SameBoy CGB E campaign covers all 333 move animation entries from
both sides at four starting delays spanning a frame, plus extra parameter
branches and all 28 auxiliary entries. Across the three links, there are
10,968 retained native animation-engine calls with no missing or duplicate
cases. Each call starts at a naturally reached battle caller boundary with
interrupts enabled; the observer does not force PPU timing or CPU speed.

Results:

- 314 of 333 moves have at least one case differing by more than one frame.
- Of 3,384 paired move cases, 1,331 are slower and 996 faster by over one frame.
- Move-duration extrema range from -19.065 to +33.008 frames. The maximum is
  foe-side Waterfall, approximately +553 ms; the earlier normal-input sample
  remains approximately +31 frames/+519 ms.
- Logical script positions, delays, parameters, OAM, animation objects,
  background-effect state, and update counts match production throughout.
- All calls return with the expected stack, ROM/WRAM banks, VBlank owner, and
  CPU-speed restoration.
- Restoring both original interrupt paths makes all 3,656 paired move/auxiliary
  cases exactly match production execution duration as well as logical state.
  Restoring only LCD or only normal VBlank does not fully restore the focused
  control timings. This rules out the retained type-chart/cursor edits as the
  cause of the measured duration regression.

Worst increases across the tested sides, phases, and parameters:

| Animation | Extra Frames | Extra Time |
| --- | ---: | ---: |
| Waterfall | 33.008 | 553 ms |
| Water Pulse | 28.003 | 469 ms |
| Hydro Pump | 24.005 | 402 ms |
| Water Gun | 20.000 | 335 ms |
| Whirlpool | 10.968 | 184 ms |
| Surf | 9.996 | 167 ms |
| Superpower | 17.059 | 286 ms |
| Psychic | 16.010 | 268 ms |

These are observed maxima, not fixed delays to subtract from authored waits.
The small overall median does not make the large individual regressions safe.

Retained tools and evidence:

- `tools/dex_timing/all_battle_animations.py` and its native observer
  `tools/dex_timing/probes/battle_animation_sweep.c`.
- `build/dex-types-all-animations-20261012/report.json`: coverage contracts,
  per-move timings, logical comparisons, and restoration results.
- `build/dex-types-all-animations-20261012/configurations.json`: exact linked
  runners, checkpoints, ROM identities, and declared fixture inputs.
- `build/dex-types-all-animations-20261012/renderer/`: individual retained calls.
- [Type Matchups investigation](pokedex_type_matchups_prototype.md#exhaustive-animation-investigation-2026-10-12):
  full context and earlier standard-regression results.

## Coverage Limits And Independent Issues

A separate 1,332 normal battle-input run campaign attempts every move from both
sides on production and prototype. Of 666 paired cases, 632 complete cleanly,
32 have identical special-condition or battle-ending/menu-fixture limitations,
and two expose the production Sand Tomb trapping-message hang. None has a new
prototype-only failure identity. Direct animation-entry tests cover those
animations, but do not prove every conditional move effect succeeds in gameplay.

The auxiliary capture fixture was corrected to initialize the wobble count and
predetermined capture result as the real capture caller does. Its 96 cases were
rerun; uninitialized scratch results are preserved for audit and excluded from
the final qualification.

These checks are not pixel-by-pixel visual approval of every animation or
physical-hardware qualification. The Type page's Ice tile corruption is a
separate unresolved VRAM-transfer issue. Sand Tomb's missing trapping-message
entry is separately logged as `BATTLE-MOVE-02`; neither explains this timing
regression.

## Required Guardrail For Future Edits

1. Do not add polling, instrumentation, feature checks, calls, or owner dispatch
   to ordinary shared LCD/VBlank paths without preserving their critical cycle
   budgets. A branch around the feature body is not sufficient isolation.
2. Account separately for active per-line LCD work, normal VBlank setup/cleanup,
   cutscene VBlank, and the shared interrupt-entry/wrapper cost. Document taken
   and rejected paths, normal and double CPU speed, and nesting/owner rules.
3. Prefer owner-specific scheduling for new Type work. It must preserve ordinary
   timing and restore ownership on every cancel/exit; relocating the palette
   routine alone does not solve the shared dispatch overhead.
4. Before accepting a changed interrupt path, regenerate symbol-matched native
   fixtures and compare all moves from both sides, multiple display phases,
   charge/release and other relevant parameter branches, and auxiliary effects.
   Check physical durations and update cadence, not just script/counter totals.
5. Also qualify graphics/audio publication, stack/register/bank restoration,
   interrupt enable state, post-animation raster cleanup, battle exits and Dex
   return paths. Rerun the standard gameplay suite and Type-page visual checks
   on all six supported CGB revisions; emulator results do not replace hardware
   validation.
6. Do not compensate globally by subtracting authored waits or retiming hundreds
   of move scripts. The regression is phase-dependent and has both positive
   and negative deltas. Restore scheduling isolation before considering any
   separately approved animation optimization.

Source comments are zero-cost documentation. This report and the warnings do
not change interrupt behavior, repair Sand Tomb, or update either review ROM.
