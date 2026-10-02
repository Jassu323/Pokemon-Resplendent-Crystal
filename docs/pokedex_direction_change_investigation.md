# Pokedex Direction Change Investigation

Investigated 2026-10-01 against committed checkpoint
`fe3571dfe0395cfd72e71b0899771d341e9fccb9` for `DEX-NAV-02`.
The reported Up/Down-to-Left/Right error is reproduced in normal-input headless
SameBoy. It is a held-versus-new direction arbitration problem, not stale
animation work or a queued navigation command.

**Production accepted 2026-10-02:** after the separate diagnostic suite and
the user's manual menu/overworld review passed, the shared-menu filter was
promoted unchanged into `home/joypad.asm:JoyTextDelay`. The root production
ROM, symbols and map are byte-identical to the accepted diagnostic artifacts.
`DEX-NAV-02` is resolved; overworld turning-delay research is separately
deferred as `OW-MOVE-01`. The installed SameBoy ROM and live battery were not
replaced. Initial investigation and diagnostic-only isolation details below
are historical evidence; see [production integration](#production-integration)
for the promotion checks.

## Inputs And Isolation

| Input | Identity |
| --- | --- |
| Accepted ROM | `cb2eabc2db0df6678c3a3a99fa7b9f19f7044418f30fc1d4237a87493d6d2748` |
| Matching symbols | `c83daf53a86ead8e6e127f42bcd4290d17f97bc2c349d901e9a928040a293358` |
| Source battery | `7111db236a12992c9edf31bf2f16c0ca1fce1313c92b3a0816da71c936ece3c7` |
| SameBoy revision | `213a12ce93d66b105a113debd9396306066a7cfc` |

The root ROM was absent, so the runner copied the accepted cartridge and
battery from `/Applications/SameBoy/Games/`. The source battery has all 373
species seen and uses New Dex order. The copied battery was not edited.
All 373 Listing checkpoints were prepared through normal controller input.
Selected starting states were also reached through normal A and footer input,
after playback settled. Source ROM, symbols and battery hashes remain unchanged.

Generated files are isolated under the ignored
`build/dex-direction-change-investigation/` directory. The optional
`DEX_DIRECTION_CHANGE_TRACE` observer is compiled into a separate headless
executable, not the cartridge. It reads physical/mirrored joypad bits, repeat
timers, navigation handlers, selected indices and footer position. It does not
write game memory or change emulated cycles, registers or banks.

Four observer-on/off controls agree on checkpoint cycles, emulated state,
publication/miss events, UI maps/palettes and rendered pixels. State comparison
excludes only the existing host-synchronized RTC wall-clock fields; the RTC
cycle accumulator is still compared.

## Reliable Reproduction

### Listing

1. In New Dex order, move the cursor to Croconaw at index 7.
2. Press and keep holding Up until the cursor reaches Quilava at index 4.
3. While Up is still represented as held at the menu input sample, press Right.
4. The cursor moves Up again to Bayleef at index 1 instead of Right to
   Typhlosion at index 5.

Left reproduces the same second Up; the expected target is Cyndaquil at index 3.
For Down, start at Bayleef, move Down to Quilava, then add Left or Right while
Down remains held. The second move is Down to Croconaw instead of horizontal.

A one-display-interval overlap after the first navigation handler returns is
sufficient in the tested starts. Two- and four-interval overlaps also reproduce.
This is not a universal wall-clock threshold: the relevant condition is that
the combined held mask reaches the menu poll.

### Selected Mon

1. Open Croconaw and let its playback settle.
2. Press and hold Up to page to Totodile at index 6.
3. After that page is ready, press Right without releasing Up.
4. The footer moves from Desc to Stat, then the same update pages Up again
   to Typhlosion at index 5. The new page resets the footer to Desc, hiding the
   intermediate footer movement in the final state.

Left at the Desc boundary cannot move the footer, but still causes the unwanted
second species page. Down-first combinations reproduce the equivalent forward
page. Thus fixing only the Listing would leave a proven second manifestation.

### Release And Reverse Controls

Releasing the vertical key and pressing the horizontal key works, including a
direct switch with no neutral frame and neutral gaps of 1, 2, 4 and 8 display
intervals. The accepted mask then contains only the new horizontal direction.

Rapid horizontal-first combinations work in the tested starts: the Listing's
vertical priority agrees with the new direction, and the Selected footer's
repeat delay suppresses another horizontal move.

There is a related slower Selected case. Start with Stat selected, press and
hold Right to reach Mov, then add Up or Down after the footer delay expires.
The old Right is repeated to Area before species paging. In the tested start,
10/11/12-frame holds do not cause this, while 13/14-frame holds do, for both
vertical directions. The new vertical press is the only new D-pad bit; the old
horizontal movement is not a second physical press.

## Trace Evidence And Cause

Input flows through these existing routines:

1. `UpdateJoypad` samples the controller in VBlank into `hJoypadDown`.
2. `GetJoypad` computes `hJoyPressed`, `hJoyReleased` and `hJoyDown` from the
   current physical sample and the last menu sample.
3. `Pokedex_BeginOwnerLoop` calls `JoyTextDelay` before dispatching the owner.
4. With `hInMenu = 1`, `JoyTextDelay` puts **all held keys** into `hJoyLast`.
   Any new press bypasses repeat suppression and resets `wTextDelayFrames`
   to 15, even if the new key is on a different axis.
5. `Pokedex_GridHandleDPadInput` reads `hJoyLast` and checks Up, Down, Left,
   Right in that order. It does not prioritize the newly pressed direction.

The second Listing Up-to-Right action records:

| Field | Value | Meaning |
| --- | --- | --- |
| `hInMenu` | `$01` | Menu-mode held-mask behavior |
| `hJoyPressed` | `$10` | Right is the only new key |
| `hJoyDown` | `$50` | Up and Right are held |
| `hJoyLast` | `$50` | Both are accepted by `JoyTextDelay` |
| `wTextDelayFrames` | `$0f` | A new press just reset the repeat delay |
| Executed handler | `Pokedex_GridHandleDPadInput.up` | Wrong direction wins |
| Listing index | `4 -> 1` | Quilava to Bayleef, not Typhlosion |

In this trace, the wrong handler executes at T-cycle 469,704. The preceding
Up handler was at 188,808. The repeat counter is freshly reset, not exhausted:
**this is not an ordinary held-key repeat firing too soon.**

The Selected page has two consumers. `Pokedex_MoveArrowCursor` first checks
new eligible Left/Right presses, so it correctly accepts the new Right.
`PokedexSelectedMon_FindNextSeen` subsequently checks Up/Down in `hJoyLast`,
so it also accepts the held Up. The trace records a footer change at 853,148
and another species page at 856,192 with the same `$10/$50/$50` input state.

For the slower reverse case, the footer first finds no new eligible horizontal
press. Once its own 12-turn delay is zero, it falls back to `hJoyLast` and
accepts the held Right. Species paging then accepts the new vertical key.

The code paths are in [home/joypad.asm](../home/joypad.asm),
[pokedex.asm](../engine/pokedex/pokedex.asm),
[pokedex_detail.asm](../engine/pokedex/pokedex_detail.asm) and
[pokedex_animation_policy.asm](../engine/pokedex/pokedex_animation_policy.asm).
No stale command queue or scheduler backlog is needed to explain these traces.

## Test Results

| Controlled sequence | Listing | Selected Mon |
| --- | --- | --- |
| Clean release, eight axis orders and five gaps | 40/40 correct | 40/40 correct |
| Vertical first, four orders and three overlap lengths | 12/12 wrong vertical moves | 12/12 unwanted species pages |
| Rapid horizontal first, four orders and three overlaps | 12/12 correct | 12/12 correct |

Additional controls:

- 64 display-time input sequences change controller pins during preparation,
  at four quarter-frame start phases. All consume the eventual horizontal key
  correctly and have no animation/audio misses. Their one-frame overlap ends
  before the next owner poll, so no combined held mask remains at that poll.
  This distinguishes a real held-mask conflict from replaying a released key.
- Eight single-direction hold tests retain existing repeats: an initial delay
  of 15, subsequent delay resets of 5, and the footer's independent delay.
  Heavy navigation work can space accepted repeats farther apart than the
  counter alone; this investigation does not change that behavior.
- Eight simultaneous-diagonal tests preserve the baseline's existing policy.
  The Listing prefers vertical; Selected can act on both axes. When both keys
  are newly sampled together, the game has no evidence of their physical
  ordering. These are not classified as reusing an old direction.
- Ten delayed horizontal-to-vertical Selected tests reproduce four unwanted
  footer movements after its repeat delay expires, with no animation/audio
  misses.
- Five cold playback/return controls pass for Chikorita, Bayleef, Meganium,
  Dusknoir and Luxray. Exact expected/actual full playback intervals are
  116/116, 81/81, 137/137, 174/174 and 92/92 respectively. Tilemaps, portrait
  pixels, sampled completion and Listing returns pass.

The main diagnostic report contains 218 input conditions plus four
observer-equivalence controls. The focused host test suite passes 63 tests;
two pre-existing linked-test classes skip because the root ROM was moved out
of the checkout. The normal-input SameBoy runs use its hash-matched copy.

## Proposed Fixes

### Listing Consumer Only

Let `Pokedex_GridHandleDPadInput` prefer `hJoyPressed & PAD_CTRL_PAD`, falling
back to `hJoyLast` only when no new D-pad bit exists. Replacing the current
three-byte mask load with an eight-byte resolver is approximately **5 ROMX
bytes**, with no memory allocation.

This is very small and scoped, but incomplete: it leaves the proven Selected
species/footer conflict. Duplicating arbitration in its separate consumers
would require keeping their policies synchronized, including the reverse
footer case. Not recommended as the complete fix.

### Filter Every Dex Owner

After `JoyTextDelay`, prefer fresh D-pad bits in `hJoyLast`; keep its button
bits and keep the original repeat result if no new D-pad press exists.
The isolated assembled specification adds **14 ROMX bytes** and **48/92
T-cycles** for the no-new-direction/new-direction paths. No new RAM is needed.

This fixes the shared input cause with one rule, but also changes Search,
Options and Unown input behavior. Saving fourteen bytes is not a compelling
reason to expand the behavioral scope.

### Scope The Shared Filter To Listing And Selected

**Initial Dex-only recommendation:** keep the same shared rule, but guard it to jumptable states
1, 3 and 4: Listing update, Selected update and its existing reserved alias.
Place it immediately after `JoyTextDelay` in `Pokedex_BeginOwnerLoop`, before
any footer/grid/species consumer runs.

The rule is:

```text
if this is a Listing or Selected update and a new D-pad direction exists:
    hJoyLast = existing button bits | newly pressed D-pad bits
otherwise:
    keep JoyTextDelay's result unchanged
```

Costs from an isolated RGBDS-assembled instruction specification:

| Resource or path | Added cost |
| --- | --- |
| ROMX, existing Dex animation/UI bank `$a0` | 28 bytes |
| ROM0, dedicated WRAM0/WRAMX/HRAM, VRAM | 0 bytes |
| Temporary existing-stack depth during `JoyTextDelay` | 2 bytes |
| Listing, no new direction / new direction | 84 / 128 T-cycles |
| Selected, no new direction / new direction | 100 / 144 T-cycles |
| Reserved Selected alias | 112 / 156 T-cycles |
| Other Dex states, unchanged input result | 84 T-cycles |

Bank `$a0` currently has 2,175 free bytes; no new bank or repacking is needed.
The specification checks 84 input/state fixtures, including suppressed and
due repeats, held A with a new direction, and all fourteen jumptable states.
Pressed bits and repeat timers remain unchanged. It is a host-only cost
exercise, not a playable patch or proof of integrated timing acceptance.

Complexity is low: one guarded filter, existing input bytes, no last-direction
buffer, interrupt hook or cross-owner work queue. It gives both Selected
consumers the same direction decision and leaves A/B/Select/Start bits and
their existing handler priority intact. Normal single-key repeat stays intact.
The temporary stack cost comes from calling `JoyTextDelay` and returning to
the filter rather than tail-jumping to it; no stack allocation is enlarged.

The policy only prioritizes a **new** direction. If multiple new directions
arrive in the same sample, existing priority remains. If a diagonal remains
held after the new edge, repeat still follows the existing held-mask policy.
Tracking the newest direction indefinitely would be a different feature with
additional state and is not needed for this bug.

There are no added display waits or graphics/audio operations. The maximum
156-T increment is under one scanline, but timing still must be validated on
the integrated link; it is not safe to declare every scheduler boundary
unaffected solely from this small CPU cost.

Do not leave `hInMenu` cleared or replace menu input unconditionally with only
pressed keys: that would lose ordinary held-key repeats. The broader shared
correction below keeps repeat handling intact.

## Shared-Menu Follow-Up

The user subsequently reproduced the rapid direction change issue in the Pack.
The initial source review confirmed that Pack calls
the same `JoyTextDelay` with `hInMenu = 1`, then dispatches Left, Right, Up and
Down from `hJoyLast` in `Pack_ShellPocketMenu`. Its horizontal-first priority
differs from the Dex Listing's vertical-first priority, so individual overlapping
axis orders need not fail in the same direction in the two screens.

The recommended direction, given this broader scope, is now to fix **shared
menu direction arbitration** inside `JoyTextDelay`, rather than add duplicate
Dex and Pack filters. This is not a change to physical controller sampling:
`UpdateJoypad`, `GetJoypad`, the raw held/pressed/released mirrors, and overworld
consumers of raw input remain unchanged.

### Shared Policy And Contracts

Only in menu mode, when `hJoyPressed` contains a new D-pad bit, use:

```text
accepted input = currently held A/B/Select/Start | newly pressed D-pad bits
```

Otherwise use the existing routine unchanged, including repeat suppression,
the initial 15-counter delay, and later 5-counter resets. Newly pressed buttons
without a new direction retain their previous behavior. Do not change each
menu's button priority, coordinate rules or simultaneous-new-direction policy.
After a diagonal's new edge has passed, its held repeat still follows the
existing per-menu priority; this is not an indefinitely remembered most-recent
direction feature.

The global candidate must save/restore BC while constructing the mask. Unlike
the scoped Dex caller, a shared routine cannot assume it is safe to clobber B.
The candidate preserves BC/DE/HL, return A/flags, stack balance, all raw input
mirror values and the repeat timer. No new memory or additional display wait is
needed. The two-byte temporary BC save happens after `GetJoypad` returns, so it
does not deepen the existing maximum stack usage of the complete routine.

`GetMenuJoypad` and `JoyTextDelay_ForcehJoyDown` already take directional bits
from `hJoyLast` and button bits from `hJoyPressed`; they do not reintroduce raw
held directions. This covers their shared scrolling/2D-menu clients as well.
Naming/mail entry, Bills PC, TM/HM, Pokegear and other direct callers also use
the shared accepted input. A caller that bypasses this routine and interprets
`hJoyDown` itself is intentionally outside this fix.

### Measured Cost Comparison

The initial host-only specification included a byte-identical copy of the linked
41-byte `JoyTextDelay` and a 55-byte shared candidate, before either candidate
was linked into a diagnostic cartridge. Both execute the real linked `GetJoypad`; all sixteen old and
new D-pad masks, eight held/new/released button patterns, both menu states and
three repeat-counter values produce **12,288 contract fixtures**. All pass.
These are isolated instruction/contract measurements, not integrated SameBoy
gameplay regression results.

| Cost or scope | Shared-menu correction | Scoped Dex filter |
| --- | --- | --- |
| ROM0 | +14 bytes | 0 |
| ROMX | 0 | +28 bytes |
| Dedicated WRAM0/WRAMX/HRAM, VRAM | 0 | 0 |
| Existing-stack temporary save | 2 bytes, no higher complete-routine peak | +2 bytes of nested-call peak |
| New directional input | +72 T-cycles | +128 Listing / +144 Selected |
| Other menu input / no fresh direction | +20 T-cycles | +84 Listing / +100 Selected |
| Non-menu calls | Unchanged, +0 T-cycles | Not affected by Dex filter |
| Behavioral scope | All clients of shared menu-repeat policy | Listing and Selected only |

At normal speed the shared increments are about 17.2 microseconds for a new
direction and 4.8 microseconds otherwise. The linked map has 582 ROM0 bytes
free, including 506 contiguous bytes at its end. A 14-byte addition would leave
568 total bytes free (492 contiguous), assuming no other link changes.
There is no reason to move this very small correction into ROMX and pay a
bank-switching wrapper cost.

### Complexity, Risk And Approval Boundary

Implementation complexity remains low: one menu-only branch and a register
save, with no per-screen patches, new input buffer or interrupt work. Compared
with a Dex-only fix, the broader regression surface is the meaningful cost.
Menus may have come to rely accidentally on the old mixed held/new mask.
The shared change is therefore a moderate validation task, despite being a
small code change. Raw overworld input and non-menu calls are not changed.

Before acceptance, repeat the existing Dex edge/release/hold/diagonal cases,
then exercise Pack and Battle Pack grid movement and pouch changes, TM/HM,
party/battle menus, PC, naming/mail entry, Pokegear, Options/Search/Unown and
menu-based minigames. Include A/B/Select/Start chords, both axis orders, held
repeats, menu boundaries, and automated tutorial input. Run the existing
all-species Dex playback/return audits and transition timing checks against a
freshly linked diagnostic ROM to detect timing or input ownership regressions.

At this original investigation checkpoint no production fix had been made.
The subsequently approved diagnostic implementation and real-input Pack
regressions are recorded below; production promotion followed on 2026-10-02.

## Integrated Diagnostic Results

The approved shared policy was initially implemented only in
`tools/dex_timing/probes/shared_menu_joypad.asm`. The isolated builder
`tools/dex_timing/shared_input.py` exports the committed checkpoint into
`build/shared-menu-input/baseline/`, rebuilds it, and requires its full ROM hash
to match the accepted installed cartridge before making a candidate checkout.
It replaces only that checkout's `JoyTextDelay` and fully relinks the cartridge.
No cross-link execution save states are used.

| Artifact | Identity |
| --- | --- |
| Baseline source checkpoint | `fe3571dfe0395cfd72e71b0899771d341e9fccb9` |
| Baseline cartridge SHA256 | `cb2eabc2db0df6678c3a3a99fa7b9f19f7044418f30fc1d4237a87493d6d2748` |
| Diagnostic cartridge SHA256 | `d3004b30abc41fcf3ce0933736fd697a85de15944da0e680c03ad80e6d1ad6ea` |
| Diagnostic battery input SHA256 | `a2bdef4a621ba92cfc2b549d28cdda980234cd94d648313e3dbe5c447fa57ea7` |
| SameBoy revision | `213a12ce93d66b105a113debd9396306066a7cfc` |

The playable artifact is
`build/shared-menu-input/pokecrystal-shared-input-diagnostic.gbc`, with matching
`.sym`, `.map` and private `.sav` files. The paired save is an unchanged copy of
the source battery for manual testing. `build.json` records input provenance. Generated ROMs,
saves, logs, checkpoints and reports stay under the ignored build directory;
the reusable diagnostic sources remain in the repository.

### Linked Contracts And Costs

The actual baseline and candidate routines pass **393,216 instruction
contracts** covering all 256 previous masks, all 256 current masks, menu and
non-menu operation, and repeat counters 0, 1 and 10. A further **1,536 scripted
auto-input fixtures** cover all input payloads, both menu modes and three
script lengths. This verifies script-pointer bookkeeping, not an in-game
tutorial playthrough.

Only the permitted menu-mode `hJoyLast` change occurs. Return A/flags,
BC/DE/HL, stack balance, ROM bank, raw input mirrors and repeat-counter values
match the baseline. Negative host controls reject unexpected register,
mirror or repeat changes and verify that the auto-input pointer is checked
as a word, not only its low byte. The refreshed source inventory records 69
direct `JoyTextDelay` call sites, including the mobile source directory.

The linked cost is **14 ROM0 bytes**, **zero ROMX or allocated RAM/VRAM**,
**+0 T-cycles outside menu mode**, **+20 T-cycles for other menu polls**, and
**+72 T-cycles when a fresh menu direction exists**. ROM0 free space changes
from 582 to 568 bytes, with its final contiguous gap changing from 506 to 492.
There are no extra display waits and no increased complete-routine peak stack
depth. These measurements agree with the initial specification.

### Native Menu Regression

Fresh checkpoints are prepared through normal controller input in each link.
Private, checksum-verified battery fixtures supply otherwise unavailable
inventory, map placement and unlock flags; they never replace the live save.
The host observer records inputs and registers without patching game RAM or
consuming emulated CPU cycles.

The native matrix covers **57 menu states**, with **912 released/overlapping
axis-change conditions** and **684 ordinary control conditions per build**.
Covered screens are:

- Start; Dex Listing, Selected, Options, Search, Search Results, Unown and Area.
- All five Pack pouches, item actions, toss quantity, sorting, give/sell Pack,
  TM/HM and Apricorn screens and their action menus.
- Party selection, actions, item actions, Stats, Moves, naming and mail entry.
- Pokegear clock, town map, phone, contact actions and radio; Trainer Card;
  Options and the save prompt.
- Pokemon Center PC, Bill's PC main/withdraw/deposit/move/box/action menus,
  player's PC and item withdrawal/deposit.
- Mart main/buy/quantity/sell; battle main/move/Pack/party menus;
  Card Flip play/bet and an Unown puzzle.

The candidate has **zero wrong accepted masks and zero register-contract
failures**. All ordinary button/hold outcomes agree with the baseline in the
active owner's observed state. These comparisons exclude unrelated bytes of
overlapping WRAM unions; they are not whole-RAM identity claims.
The controls cover A/B/Select/Start, each button with Right, and four
single-direction 60-display-interval holds.

The Pack now has a native reproduction, not just a source inference. With
two entries in its Items pouch, press and keep holding Right to reach the
second item, then add Up. The baseline repeats Right and changes pouches;
the candidate accepts only the newly pressed Up and stays in the original
pouch. An expanded three-item fixture similarly exposes an unwanted baseline
second Right. Up-then-Right is already correct in this Pack layout because
its horizontal priority differs from the Dex Listing's priority.

The focused Dex suite also passes its 128 edge/release conditions, 64
quarter-display-phase conditions, eight held-direction controls, eight
simultaneous-new diagonal controls, ten delayed reverse/footer controls and
four observer-equivalence controls. The baseline's 24 vertical-first failures
and four delayed reverse/footer failures are absent in the candidate.
This does not change simultaneous-new diagonal priority or remember the newest
axis indefinitely during a held diagonal.

Forty-four additional menu-return tests per build verify B-return, cleared
menu ownership, resumed walking and reopening Start. The independent Area
entry/B-return check also passes in both builds on this fixture. This does
not resolve the older Area backlog item across every entry condition.

### Animation And Movement Regression

| Paired regression | Result |
| --- | --- |
| All-species cold Listing entry | 373/373 pass per build |
| All-species internal paging | 373/373 pass per build |
| Listing restoration after those entries | 746/746 pass per build |
| New Dex Entry input sweep | 8,568/8,568 pass per build across 20 species |
| New Dex Entry audited display intervals | 1,207,396 per build |
| Walking input sequences | 38/38 matching logical checkpoints and pixels |
| Cycling input sequences | 38/38 matching logical movement checkpoints |
| Current-link host unit tests | 134 pass, none skipped |
| Frozen historical timing-model unit tests | 197 pass, none skipped |

All-species Dex audits retain exact authored animation intervals, correct
published maps/pixels and complete sampled playback without animation or
sampled-cry misses. The paired New Entry sweep includes natural completion,
every display-offset A/B page/exit press, startup input, holds and rapid-input
cases. Its 20 contexts are explicitly generated by the existing registration
fixture factory from a fresh native catch donor for each link; they are not
twenty independently played catches.

Cold startup deltas have median -0.000285 and mean +0.0183 display intervals;
internal paging deltas have median -0.000114 and mean -0.00186. Individual
measurements range roughly one interval earlier or later because the fully
relinked, independently booted runs can land on opposite display boundaries.
There is no consistent added interval, and every measured full animation
duration remains identical. This is not a claim that all startup cycle counts
are byte-for-byte equal.

Walking and cycling controls include short taps, long holds, B chords,
immediate switches, overlaps, diagonals, collisions and map-boundary movement.
Cycling screenshots match completely in 33/38 cases; the remaining five
have localized moving-NPC differences in the independently booted runs,
not changes in the player's measured movement. No overworld input result,
movement checkpoint or register contract differs.

### Limits And Recommendation

No new functional regression was identified in the tested flows. The shared
menu correction remains the recommended candidate: it removes the reproduced
cause once, costs less CPU than the duplicated Dex-local alternative, and
does not alter physical sampling, non-menu input or repeat timing.

This is broad coverage, not an exhaustive playthrough of every call site.
Actual link partners, printer hardware, mobile-service workflows, the unused
Memory Game, debug menus and some story-gated special menus were not played.
Their shared input/register contract is exercised, but those integrations are
not independently signed off. The auto-input fixtures likewise do not replace
a full catch-tutorial playthrough. Battle animation/cry systems outside the
Dex are not changed or newly certified by this menu regression.

The user subsequently approved the diagnostic after manual menu/overworld
testing, and production promotion is recorded below. The separate cartridge
remains reproducible historical evidence. Do not load execution-PC states from
the older baseline into a relinked cartridge; reuse is safe only when the ROM
and symbol identities match exactly.

## Production Integration

On 2026-10-02 the user accepted the diagnostic's menu behavior, confirmed that
the overworld felt unchanged, and approved the production correction.
`home/joypad.asm:JoyTextDelay` now contains the exact candidate instructions,
with one source comment explaining their purpose:

```text
if hInMenu != 0 and (hJoyPressed & PAD_CTRL_PAD) != 0:
    hJoyLast = (hJoyDown & PAD_BUTTONS) | (hJoyPressed & PAD_CTRL_PAD)
else:
    retain the original held/repeat or non-menu behavior
```

The helper preserves BC around its temporary direction mask. Physical sampling,
input mirrors, returned registers/flags, auto-input bookkeeping and repeat
timers are unchanged. There is no new direction memory or queue and no change
to walking/turning speed. The linked cost remains 14 ROM0 bytes with 568 free,
zero additional ROMX/RAM/VRAM, and no additional display waits.

The normal `make -j8` build succeeds. SHA-256 comparisons confirm exact identity
with all three manually accepted diagnostic artifacts:

| Production artifact | SHA-256 |
| --- | --- |
| `pokecrystal.gbc` | `d3004b30abc41fcf3ce0933736fd697a85de15944da0e680c03ad80e6d1ad6ea` |
| `pokecrystal.sym` | `4fa9f046cb9ce4c20dd2955acdfcc5bf36b063c0bb73bbde65be463f32af57a1` |
| `pokecrystal.map` | `fab2c5d95a3e64dba08b067c1760b8f46ce2e6fcf4b1560a5133e9bf44fb8a70` |

This is stronger than comparing only the changed routine: the production game
is the already accepted diagnostic game, with no additional runtime change.
Its prior 57-state menu matrix, 373-species cold/internal playback checks,
20-species New Entry sweep and walking/cycling results above apply unchanged.
Those complete matrices were not all replayed again merely for promotion.

Additional post-promotion checks on the actual root production link:

- 393,216 exhaustive linked input-mask contracts and 1,536 scripted-input
  contracts pass against the original baseline. Measured added costs remain
  0 T outside menus, 20 T for other menu polls, and 72 T for fresh directions.
- A freshly booted 30-state primary menu matrix passes 480 axis cases and
  360 ordinary button/hold controls with zero wrong masks or register failures.
  All 29 tested menu returns clear menu ownership and resume the overworld.
- All 134 current-link host unit tests pass with no skips.
- All 38 walking sequences replayed from the diagnostic's exact matching-link
  start agree at every logical checkpoint, with zero wrong masks or register
  failures. Independent fresh boots can land at different movement phases;
  their unaligned intermediate snapshots are not an equivalence criterion.
- The archived timing model passes its separate 197-test suite with
  `DEX_TIMING_REFERENCE_ROOT=build/shared-menu-input/historical-reference/checkout`.
  This is a historical-model check, not a current-ROM animation replay.

Test-selection note: blanket discovery initially selected the archived model
against the cleaned production link, producing missing-instrumentation and
obsolete-cost expectation failures. An initial historical retry also named the
old, removed output directory. Neither is a game regression. The explicit
current-link suite (134 tests) and the existing matching frozen checkout
(197 tests) both pass; no game or host-model behavior was changed to suppress
these fixture-selection failures.

Generated production checks are under ignored `build/shared-menu-input/`,
including `production-contracts.json` and `production-menus/`. Matching-link
movement replays and the separate frozen-reference model checks are recorded
there as additional controls. Live save data and the installed SameBoy ROM
remain untouched. The turning-delay research spike and its pinned Polished
Crystal references are in the
[live backlog](pokedex_selected_bug_backlog.md#ow-move-01-research-faster-player-turning-without-changing-walking-behavior).

### Reproducing The Diagnostic

Use a fresh ignored output directory; the builder refuses to replace an
existing diagnostic checkout or any protected input file.

```sh
env PYTHONPATH=. python3 -m tools.dex_timing.shared_input \
  --accepted-rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --battery /Applications/SameBoy/Games/pokecrystal.sav \
  --output build/shared-menu-input --jobs 8

env PYTHONPATH=. python3 -m tools.dex_timing.shared_input_contracts \
  --baseline build/shared-menu-input/baseline \
  --candidate build/shared-menu-input/candidate \
  --output build/shared-menu-input/linked-contracts.json --jobs 8
```

`shared_menu_regression.py` provides normal-input menu setup, matrices and
controls. Run both links with their own checkpoints and the same battery copy;
its `--expanded`, `--location`, `--area-state` and `--bicycle` paths extend
coverage without production changes. `shared_menu_fixtures.py` makes only
private, declared-field/checksum edits and retains the source battery hash.
For relocated saves it reconstructs saved player/object coordinates and the
screen-block window as well as map IDs; changing only the map IDs produces an
invalid fixture. Earlier setup failures from inconsistent fixtures are not
candidate regressions and are excluded from acceptance.

The all-species paths use `cold_listing.py --internal-paging` as appropriate.
`shared_new_entry_regression.py` drives paired 20-species input sweeps from
fresh matching-link catch donors. Accepted artifact paths, aggregate results,
costs and source-input hashes are recorded in
`build/shared-menu-input/acceptance.json`; intermediate setup attempts are
not treated as accepted test reports.

## Original Integration Checklist

1. Re-run the 128 release/overlap cases and the ten delayed reverse cases;
   require zero old-axis actions on a new-axis press.
2. Preserve single-key repeat and the explicitly unchanged simultaneous-new
   diagonal policy. Exercise A/B/Select/Start combinations and footer limits.
3. Exercise grid scrolling, top/bottom wraps, partial last rows, sparse seen
   entries, Search Results returns, Options, Area and Unown controls.
4. Run all-species cold and internal paging playback audits, including active
   owner changes and B-return: exact animation timing, pixels/maps, sampled
   completion and no misses. Re-create states from the new link rather than
   loading old execution-PC states into a shifted ROM.

No additional manual state dump or video is needed to establish this cause.
The diagnostic integration passed the regression checks above. The user
accepted its behavior and the shared correction is now promoted to production;
no additional manual capture is required for this reproduced input cause.

## Reproducing The Investigation

Use a matching accepted ROM/symbol pair and an isolated all-seen New Dex
battery copy. Outputs remain ignored; reusable runner/observer source ships
in the repository.

```sh
env PYTHONPATH=. python3 -m tools.dex_timing.cold_listing \
  --rom /Applications/SameBoy/Games/pokecrystal.gbc \
  --sym pokecrystal.sym \
  --battery /Applications/SameBoy/Games/pokecrystal.sav \
  --output build/dex-direction-change-investigation/cold \
  --species chikorita bayleef meganium dusknoir luxray --jobs 8

env PYTHONPATH=. python3 -m tools.dex_timing.direction_changes \
  --checkpoints build/dex-direction-change-investigation/cold \
  --output build/dex-direction-change-investigation/trace
```

`trace/report.json` contains the condition matrix, handler evidence and
observer controls. `trace/cost-specification/report.json` records assembled
sizes and instruction costs. Individual JSONL files retain the complete
physical/mirrored input history.
