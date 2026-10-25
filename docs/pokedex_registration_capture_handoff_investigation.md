# Interactive Registration: Capture Money And Invisible Speed Handoff

Date: 2026-10-16. Investigation and independent experiments only.

## Decision Summary

The white flash can be removed without sacrificing Selected-style animated
registration, double-speed tabs, or the existing music-reset boundary.

**Recommended candidate:** synchronize the normal-to-double `STOP` to the
beginning of LCD rendering mode 3, leave the LCD enabled, and retain the existing
sound reset after the caught cue has finished. This is a capture-tail-only
helper, not a change to the shared speed-switch routine or interrupt handlers.

The independent compact candidate also includes the separately identified
Pay Day context fix. Compared with the reviewed interactive prototype, the
combined candidate saves **126 decimal ROMX bytes**, allocates no additional
RAM, and uses three more bytes of already borrowed registration scratch.
No new graphics or palette assets are needed.

The existing reviewed ROM, production ROM, and player's main save are unchanged.
Do not interpret this experiment as production integration or full release
regression approval. Human audio/visual approval and real-hardware verification
remain outstanding.

## Protected Baselines And Evidence

- Production ROM SHA-256:
  `52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
- Reviewed interactive ROM SHA-256:
  `1abe990d9d96ef34a910e444c6990aa9e745c8827d48946834aa179a29cc8634`.
- Reviewed source: `build/interactive-registration-dev07-20261015/candidate/`.
- Entire investigation: `build/registration-catch-investigation-20261016/`.
- Machine-readable findings: `options-report.json`, `report.json`,
  `money-context-helper.json`, and `render-compact-source.diff` in that directory.
- Experimental source and link: `render-compact/` in that directory.
- Separately named evaluation ROM, symbols, map and private test save:
  `review/pokecrystal-interactive-registration-invisible-switch.*`.
  ROM SHA-256: `d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.
- Native replay logs and complete scanouts: `runs/` and `qualification/`.
- Four-way, six-second comparison: `review/speed-switch-four-way.mp4`.
  Its audio is the synchronized candidate only, not a mixture of soundtracks.
- Sequential thirty-second audio review: `review/speed-switch-options-with-audio.mp4`.
  Six seconds each: production, current prototype, synchronized candidate,
  hidden/preserve music, hidden/restart music. Every segment has its own audio.
- Frame contact sheet: `review/speed-switch-options-frames.png`.
- False payout capture: `review/caterpie-false-payday.png`.

All timing below uses physical Game Boy display time:
`70224 / 4194304` seconds = **16.742706 ms per display frame**. An LCD-off
SameBoy callback is not necessarily a new physical display frame.

## False Pay Day Payout

### Reproduction

1. Enter a wild battle with an uncaught Pidgey, Caterpie, or Sentret.
2. Do not attack; catch it with one Master Ball.
3. Visit or leave interactive registration, decline naming, and finish the battle.
4. The reviewed interactive prototype displays a Pay Day payout and actually
   increases the player's wallet. Frozen production does not.

Native Caterpie and Sentret replays produced 65,536; the wallet changed from
2,137 to 67,673. An early-exit Pidgey replay also produced 65,536. A settled
Pidgey fixture produced 720,896 instead, because the last portrait tile count
was different. Thus the bug is not intrinsically a fixed 65,536 reward, even
though all three user reproductions showed that amount.

### Cause

`wPayDayMoney` is a three-byte big-endian live battle accumulator at WRAM0
`$c6f0..$c6f2`. The Dex deliberately reuses that memory outside battles:
`wDexTempCounter + 1` aliases its high byte, and the next two bytes overlap
the start of `wPokedexGridOccupied`.

`Pokedex_GatherReadyAnimationTiles.tile_loop` in
`engine/pokedex/pokedex_animation.asm` stores the number of gathered tiles in
`wDexTempCounter + 1`. The observed writer in the reviewed link is bank `$a0`,
PC `$6587`. A final count of one leaves `01 00 00`, or 65,536, in the amount.

Interactive registration preserved 28 scalar fields but not the three Pay Day
bytes. Returning to `ExitBattle.HandleEndOfBattle -> CheckPayDay` therefore
consumed genuine scratch corruption as a legitimate reward. This is a new
interactive-registration ownership bug, not a money formatter or speed-switch
bug. Removing the flash alone does not fix it.

### Isolated Fix And Cost

Append the three accumulator byte addresses to `NewDexRegistration_Fields` in
`engine/pokedex/new_pokedex_entry.asm`; use the existing save/restore loops.
The field count becomes 31 and the saved context becomes 67 rather than 64 bytes.
Do not simply clear the amount: a player may legitimately have used Pay Day
before catching the Pokemon.

- **6 ROMX bytes** for three pointers; zero allocated ROM0/WRAM0/WRAMX/HRAM/SRAM.
- Three extra borrowed bytes in WRAMX bank 2 `wTempTilemap`. The next live
  animation structure starts at offset 360, well beyond context offset 67.
- Each save or restore adds 0.060081 ms / 0.003589 display frames at double
  speed; round trip 0.120163 ms / 0.007177 frames, CPU-only measurement.
- Low complexity and low risk. Continue guarding the scratch ownership boundary
  and preserve all three bytes together.

Fourteen linked-CPU helper controls compare baseline and fix at seeded amounts
0, 1, 12, 65,535, 65,536, 999,999, and 16,777,215. The fix restores all amounts
exactly, preserves bank/stack state, and leaves the tail canary unchanged.
These are seeded helper tests, not native battles actually using Pay Day.
Native capture tests additionally verify the zero-amount path and wallet.

### Why Earlier Qualification Missed It

The capture runner compared party, EXP, moves, discovery, box delivery, speed
ownership, and map return, but did not compare the wallet or Pay Day accumulator.
Automatic text advancement dismissed the unexpected reward message. A completed
return path consequently passed despite real wallet corruption.

`tools/dex_timing/gotcha_boundary.py` now records both three-byte big-endian
values and asserts an unchanged wallet for its no-attack Master Ball fixtures.
The prior clean report must not be treated as coverage of money preservation.
The strengthened oracle passes a native frozen-production control and rejects
the known-bad reviewed prototype with `Unexpected capture payout`.
Before promotion, also exercise native legitimate Pay Day earnings, including
Amulet Coin and the wallet cap, not just seeded context helpers.

## White Flash Cause

The reviewed `BattleSpeed_CaptureHandoff` in `engine/battle/capture_speed.asm`
adds RGB brightness steps 8, 16, 31, disables the LCD, calls
`BattleSpeed_LeaveNormal`, enables the LCD, and reverses the brightness steps.
This deliberately fades the entire battlefield to white and back. It is not a
missing graphic, palette asset, or requirement of interactive registration.

It is called by `Text_GotchaMonWasCaught` in `engine/items/item_effects.asm`
after `WaitSFX` and `MUSIC_NONE`, before `MUSIC_CAPTURE`. This is a useful audio
boundary, but the visible fade is not acceptable. The same helper also runs on
repeat/no-Dex successful captures; it is not limited to new registrations.

## Measured Options

ROM deltas are decimal bytes relative to the reviewed interactive prototype,
not production. Negative numbers are savings. All measured options allocate
zero additional ROM0, WRAM0, WRAMX, HRAM, or SRAM. Except the combined candidate,
the speed-only controls intentionally still contain the known money bug.

| Option | Handoff Duration | Visible Result | ROMX Delta | Assessment |
| --- | --- | --- | ---: | --- |
| Current fade/LCD-off | 158.321 ms / 9.456 frames | Full-white interval 67.225 ms / 4.015 frames | 0 | Reject visible flash |
| Remove fade only; still toggle LCD | 24.641 ms / 1.472 frames | Still blank for 33.743 ms / 2.015 frames | -35 | Reject; not invisible |
| Synchronized LCD-on, compact, money fix included | 18.846 ms / 1.126 frames | No blank/faded scanout observed | -126 | Recommended for review |
| Hidden registration switch, preserve music | 15.703 ms / 0.938 frames, inside registration transition | No extra Gotcha flash | -176 | Fallback; active-audio clock risk |
| Hidden registration switch, reset/restart music | 19.042 ms / 1.137 frames, inside registration transition | No extra Gotcha flash | -187 | Fallback; audibly restarts capture track by design |

Representative native timing is Caterpie with matching-link generated encounter
contexts. Timings are helper spans, not total capture-to-overworld times.
The compact speed helper alone saves 132 bytes; the money fix spends six of
those. Hidden options would each spend six additional ROMX bytes if combined
with the money fix. The earlier untrimmed LCD-on diagnostic retained dead fade
code and cost +19 bytes; that is not the compact candidate's final cost.

### Recommended: Synchronized LCD-On

Keep the same successful-capture callback and silent sound-reset boundary.
Preserve BC/DE/HL and the interrupt mask, disable interrupts, stop any sampled
owner defensively, disable the sound hardware, deselect joypad lines, and arm
the normal-to-double switch. Wait for the next LCD mode 2, then its transition
to mode 3; execute `STOP` immediately there. Reset sound, restore the interrupt
mask, and return to the existing capture-music start.

No LCD disable/enable and no additive palette fade occur on the battlefield.
CPU work still pauses, but the already drawn battle remains on screen.
EXP, learning, naming, registration and post-battle evolution retain the
reviewed prototype's speed policy. The registration remains double speed
before any streaming preparation, and its existing animated tab owner is intact.

[Pan Docs' KEY1 description](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md#ff4d--key1spd-cgb-mode-only-prepare-speed-switch)
explains that mode 0/1 can yield black pixels, mode 2 can omit sprites, while
mode 3 permits the PPU's correct memory access during the pause. Therefore
"switch during VBlank" is not the appropriate live-LCD shortcut here.

Complexity is low/moderate and local: roughly one short helper replaces the
fade implementation. The important dependency is **normal-to-double only,
successful-capture tail, sound inactive, no concurrent display producer**.
Do not turn this into a generic battle speed-switch routine or add shared
interrupt work. Preserve the phase check immediately before `STOP`.

Risk is moderate until hardware approval. SameBoy is only one emulator engine;
six modeled revisions are not six independent implementations or physical
consoles. Its CPU source also labels some switch timing as unverified. Pan Docs
describes a shorter pause than this SameBoy build measures. The timings above
are measurements of this emulator, not a claim of exact physical-hardware STOP
latency. Another accurate core and a real CGB/compatible target should qualify
the mode-3 dependency before a hardware-wide release claim.

### Hidden Registration Switch, Preserve Music

Remove the Gotcha handoff. EXP/learning remain normal speed, as in production.
In `NewDexRegistration_Prepare`, disable the LCD just before the existing
graphics reload, then switch to double speed **without** clearing `rNR52` or
calling `InitSound`. Existing capture music continues logically. Repeat/no-Dex
captures use the original map-return switch instead of switching early.

The native helper preserved the entire logical audio-state hash and the same
three active hardware channels across STOP. That proves no software track
restart, not imperceptible sound: the divider/CPU pause can still affect sound
sequencing or stretch a note. This option trades the live-display dependency
for an active-audio dependency and changes the capture-tail speed policy.

Registration prepare-to-reveal was 160.945 ms / 9.613 frames, versus 152.513 ms /
9.109 frames in the current prototype: +8.432 ms / +0.504 frames. The switch
overlaps some work previously hidden by the LCD transition. Its streaming tabs
still run at double speed. Complexity is moderate; audio risk is higher than
the recommended silent-boundary switch. Only focused visual/audio experiments,
not the full capture-tail matrix, were run on this fallback.

### Hidden Registration Switch, Restart Music

Use the same later LCD-off boundary but retain `BattleSpeed_LeaveNormal`'s
sound reset and restart `MUSIC_CAPTURE`. This avoids active-APU switching,
but replays the beginning of the looping capture tune when registration opens.
The restart is an intentional behavior difference, not an audio underrun.

Prepare-to-reveal was 167.963 ms / 10.032 frames: +15.450 ms / +0.923 frames over
the current prototype. Complexity is low/moderate and visual risk low, but
music continuity is sacrificed. A fully seamless sound-state recovery would
need additional sound-engine ownership work; it is not equivalent to simply
resuming a saved software pointer. Not recommended while the silent-boundary
mode-3 option remains viable. Only focused experiments were run on this option.

## Other Approaches Reviewed, Not Implemented

| Approach | Why It Is Not Preferred | Cost / Complexity / Risk |
| --- | --- | --- |
| LCD-on with no phase synchronization, or at HBlank/VBlank | Known PPU access-lock problem in the hardware documentation | Small code; low complexity but high visual risk |
| Shorter/smaller fade or matching the blank palette | Still changes the visible battlefield; does not meet invisible-switch goal | Small code; low complexity; rejected presentation |
| Switch during the ball animation's existing flash | Moves the boundary into active battle/SFX animation rather than a finished capture tail | Unmeasured; medium/high complexity and regression risk; no saving justified |
| Hold LCD off from Gotcha until registration | EXP and learning must still render, and repeat/no-Dex captures might never enter registration | Requires flow/presentation redesign; high behavioral risk |
| Reset APU later and reconstruct the active track | Software note pointers do not restore hardware envelope, wave, noise or oscillator phase | Unmeasured sound-state machinery; moderate/high complexity and audio risk |
| Remain normal speed and optimize the entire registration owner | Avoids this switch but gives up the requested double-speed streaming headroom | Broad separate optimization; high engineering cost, no comparable performance claim |
| Make battles globally double speed | Changes the ownership/timing policy of ordinary move animations | Broad and high risk; outside this local fix |

These are code/hardware scoping conclusions, not measured experimental results.
No speculative byte estimate is presented as a linked cost.

## Focused Qualification

The recommended combined candidate passed **32 capture-tail cases** and **eight
follow-up battle cases**, using native control flow on matching ROM checkpoints.
RAM fixtures declare party/species/EXP conditions before enemy initialization;
they do not repair the clock, sound, PPU, or speed state during the replay.

- Caterpie and sampled-cry Dusknoir: party/PC delivery, both naming paths,
  repeat catches, no Dex, empty-slot learning, replacement, declined learning,
  EXP Share, multiple levels, successful evolution and canceled evolution.
- Four input-phase variants on ordinary party captures for both species.
- Map resume and a following native encounter, followed by running, fighting,
  or another catch; battle animations remain normal speed.
- No unexpected wallet increase in those no-attack capture fixtures. The eight
  explicit follow-up cases also check the wallet after the second battle.
- Separate native Pidgey/Caterpie/Sentret captures, including Info and Mov
  visits, restore the Pay Day accumulator before battle settlement.
- CGB 0/A/B/C/D/E booted independently in SameBoy. All six rendered the
  synchronized capture handoff without an observed blank frame, and entered
  STOP in mode 3 with sound inactive. This is not physical-hardware testing.
- Dusknoir's wild cry (512 blocks at normal speed) and registration cry (557
  blocks at double speed) match the reviewed prototype's waveform-block hash,
  timer configuration and median 12,800-T block interval exactly. The interval
  is 3.052 ms / 0.182 display frames. No observed audio/animation miss events
  occur during registration, and no native warnings were emitted. The initial
  wild appearance still has the existing 512/557-block cutoff with 45 blocks
  remaining, identical to both frozen production and the reviewed prototype
  before Gotcha. It is an unchanged baseline exception, not a complete wild cry
  or a newly successful audio test. There are no new miss identities.
- ROM0 code is byte-identical except cartridge checksum bytes; the dedicated
  Dex display-dispatch bank is byte-identical; allocated RAM addresses do not move.

An initially added high-EXP Dusknoir case exhausted 160 input-attempt pairs
while progressing through several move-learning prompts. Raising its allowance
to 600 passed on the unchanged ROM. Both initial failures (including an initial
retry that had changed the wrong call site in the private driver) are retained
in their original evidence directories; neither is silently counted as a ROM
fix. This case was an expansion beyond the prior multi-level Caterpie fixture.

This is focused investigation, not a rerun of every Dex/species/battle-animation
or Battle Tower test. Failed captures and the tutorial exclusion were inspected
in code, not requalified as new native cases here. Before replacing the reviewed
prototype, run the full regression with the stronger wallet oracle, the native
legitimate Pay Day cases, all-species registration qualification as needed,
and obtain human video/audio approval. The independent candidate is provided
for evaluation only.

The twelve host registration-harness tests also pass. They check harness
timing/coverage logic, not human perception or physical-hardware behavior.
