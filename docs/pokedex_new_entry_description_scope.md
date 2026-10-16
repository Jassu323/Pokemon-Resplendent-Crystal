# New Dex Entry Description Layout Scope

The subsequent [Interactive Registration Prototype](pokedex_interactive_registration_prototype.md)
was accepted and integrated on 2026-10-16: Desc/Info/Mov/End, continuous
Selected-style playback, the synchronized LCD-on capture handoff, Pay Day
preservation and the reviewed evolution graph. The user explicitly retained
all 20 temporary evolution requirements. Its measured costs, media and timings
supersede the estimates below. See
[production integration](pokedex_interactive_registration_integration.md).
The following scope preserves the earlier production baseline and decisions;
its private-only, normal-speed registration and option-B deferral notes are
historical. Normal-speed battle animation ownership remains unchanged.

## Interactive Scope Refreshed 2026 10 15

Current production is commit `3ed28c430b67e8a7c695459a568fc71568cfb7df`
(Dex Location Remembrance), ROM SHA-256
`52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
Visual-only option A, cleanup, ancestors, the Info-to-Description fix and both
session bookmarks are now integrated. The older scoping/build/cleanup status
below is historical. Interactive registration is feasible but not implemented
or approved by this assessment. `DEX-DATA-03/04` remain deferred until the
user completes the species/learnset pass.

The subsequent [Gotcha boundary prototype](#gotcha-boundary-prototype-results)
qualifies a double-speed capture tail with a local fade. It is available for
manual review, but neither that clock policy nor the interactive tabs have
been integrated into production.

### Proposed Behavior

- Open the newly registered species on Desc P.1, with Desc selected.
- Left/right selects Desc, Info, Mov or End using the existing shared blinking
  footer arrow. A activates; moving the arrow alone does not change the panel.
- A on an already open Desc toggles its two pages. Returning from Info/Mov
  starts Desc P.1. Neither A on Desc nor reaching page two exits registration.
- Info cycles Stats, configured Evolutions and Evolves From pages, wrapping
  with the existing content rules. Missing evolution links remain missing;
  this feature does not perform the deferred species-data work.
- Mov cycles the species' existing Level Up/TM-HM/Tutor/Breeding pages, not
  the captured individual's four moves or the searchable standalone Moves Dex.
- B from any panel or A on End cancels pending work and resumes the original
  capture/prize continuation. There is no confirmation screen, Area or species
  navigation, and no change to ordinary Dex preferences/bookmarks.
- Browsing does not discover moves. Existing actual-acquisition hooks remain
  authoritative, including after successful party/PC delivery.

No new visual asset is required: keep the existing four footer columns and
replace Area locally with native-font `End `, leaving ordinary Selected's
Area label/action intact. Reuse current shell, types, footprint, page badges,
Info/ancestor glyphs and Moves metadata rather than duplicating them.

### Architecture And Planning Budget

Both options need a registration-local fixed-species controller. Reuse the
lower-panel producers, but not Selected's whole entry/update/exit flow: those
paths read Listing order/viewport, allow species paging and restore Listing.
Initialize permanent identity, live species ID/lock, caught state, base stats,
page state and valid display-owner dispatch explicitly, without a fake order
table. Reuse existing publication dispatch; add no ordinary VBlank/STAT/timer
overhead, new ROM0 bridge or HRAM flag.

| Dimension | Static portrait handoff | Continuous Selected-style animation |
| --- | --- | --- |
| Extra ROMX planning budget against current production | 1,000-2,500 bytes | 2,000-5,000 bytes |
| Added allocated WRAMX target/contingency | 0 target; up to 64 bytes if preservation cannot fit verified inactive storage | Same |
| Added allocated WRAM0, ROM0 and HRAM | 0, 0 and 0 bytes | 0, 0 and 0 bytes |
| Persistent SRAM / save migration / duplicate species tables | None | None |
| Portrait behavior | Initial resident animation; safely retire it before Info/Mov; portrait then stays static, including on Desc return | Existing streaming producer keeps authored playback across all tabs |
| Complexity / risk | Moderate / moderate | Moderate-high / moderate-high until normal-speed qualification |

These are conservative engineering envelopes, not measured linked deltas or
runtime timings. Do not subtract speculative retirement credits for the old
registration owner. Normal tab preparation may take more physical frames than
in the double-speed Start-menu Dex. Preserve portrait/audio deadlines rather
than promising the same response time. The registration controller's present
ROMX bank has 8,698 free bytes, so an extra bank is not inherently required;
the portrait and Info banks have only 1,435 and 1,747 free bytes respectively.

The fresh all-399-assets audit confirms that **both Info glyph atlases overlap
every resident registration dictionary**. Type badges and Info mini/HP objects
do not overlap. Four species collide with Selected's normal footprint address;
the current registration bank-0 footprint is already safe. Thus merely adding
Info calls to the existing loop would corrupt pictures, even when rendering an
invisible page. Extra CPU speed or a VBlank wait cannot resolve those addresses.

Static handoff must explicitly choose whether the first tab change immediately
cancels the authored motion or waits for it to finish. Restore an atomic static
base before Info preparation, keep the cry serviced until completion/exit, and
do not replay it on tab changes. Continuous playback avoids this behavior
compromise by reusing the existing Selected frame slots and compatible atlas
layout. It is the recommended first prototype for consistency with Selected.

### Capture And Return Risks

The capture caller sets Seen/Caught before registration; captured-mon insertion,
move acquisition hooks and nickname handling happen afterward. Preserve species,
level, moves/PP, DVs, item, capture context and transient locks. B/End must return
exactly once to that continuation, not to Listing, and cannot apply a stale page
publication after exit. Treat synthesized and sampled cry exit ownership
separately from natural playback completion.

The streaming producer uses the 1,300-byte WRAM0 map overlay that aliases the
battle graphics state: its first 32 bytes contain flags, saved palettes and
producer metadata, followed by a 784-byte picture payload. Prove which bytes
are dead, preserve the still-live context and rebuild disposable payload as
needed. Do not add a full 1,300-byte backup or restore a live producer flag
whose payload was overwritten. Bank-3 lower-panel scratch is the Battle Tower
union; registration must remain excluded from active Tower ownership.

Also cover `GameCornerPrizeMonCheckDex`, used by the Celadon and Goldenrod prize
scripts. This non-battle caller enters at ordinary double speed. Preserve the
incoming speed: normal battle registration stays normal, prize registration
stays double, and neither path toggles its caller's clock to simplify rendering.

### Qualification And Cartridge Capacity

Before promotion, test every Info/ancestor and Moves category/page, both Desc
pages, all tab pairs, held/rapid input, animation-start/finish phases, queued
publication and B/End from every state. Require exact content/pixel parity and
uninterrupted timelines for the continuous version, both cry types, all species/
forms, normal captures, full-party PC delivery, nickname yes/no, transformed
captures, contest handling, both prize callers and already-caught/no-Dex bypass.
Verify no extra move discoveries, changed preferences or position bookmarks,
then run the full documented Dex/battle/audio/gameplay/save regression suite.
Measure first reveal, tab/page completion and return in milliseconds and
physical display frames. Twenty current baseline registration host contracts
pass; no interactive candidate has been built or timed.

The current build is up to date. Its linked allocations use 2,359,688 bytes
out of the padded **4,194,304-byte cartridge**, leaving **1,834,616 bytes**
(1.749626 MiB, 43.740654%). There are 83 entirely unused 16,384-byte banks,
totalling 1,359,872 bytes; another 474,744 free bytes are in partially used banks.
The map summary lists only 186 ROMX banks: its 703,641 free ROMX bytes exclude
69 unlisted empty banks (1,130,496 bytes). Add those and ROM0's 479 free bytes
to obtain the full-cartridge remainder. Source-bank placement still matters;
cartridge space does not imply free premium RAM (WRAM0 has 13 free bytes and
HRAM has none). Fresh audit evidence is under
`build/new-entry-interactive-scope-20261015/audit.json`; the ROM is unchanged.

## Selected Streaming Implementation Scope

The user clarified the required playback policy: **match Selected's existing
authored sequence; never interrupt or restart it on a tab change**. Do not add
an indefinite idle loop. A naturally finished sequence remains finished;
B/End is the intentional final owner exit and may cancel remaining playback.

This section originally scoped an incoming-speed-preserving implementation.
The later [double-speed assessment](#double-speed-registration-assessment)
below evaluates an explicit exception to that policy. No such exception has
been integrated into production.

### Entry Without Listing Dependencies

Retain `NewPokedexEntry` as the public call boundary and its caller-specific
continuations. Add a registration-local streaming controller, preferably in
`engine/pokedex/new_entry_streaming.asm` included alongside the existing wrapper
in ROMX bank 62. It has space for the present planning envelope.

1. Capture the caller's context before clearing or borrowing scratch. Explicitly
   normalize species input: battle supplies `wTempSpecies`; the Game Corner
   special supplies `wScriptVar` through `wNamedObjectIndex`. Capture the stable
   species word and live ID, and establish a temporary Dex species lock without
   changing battle/map locks. Preserve the caller's form selection, rather than
   substituting Listing's first-seen Unown form.
2. Hide setup using the existing entry transition. Initialize owner/view/job,
   footer, palette-dirty, upload and page fields explicitly. Set the existing
   Selected display-dispatch state for publication, not a fabricated Listing
   order. Save/restore its previous value. There is no required order-table
   scan, grid construction, Search initialization or neighbor preparation.
3. Reuse the existing font/shell/badge loaders. Draw the upper Description
   content and footer with local `End ` replacement. Seed `wPokedexSelectedSpecies`
   and permanent `wPrevDexEntry` directly; obtain the caught/base-stat/Info/
   ancestor metadata with `PokedexInfo_PrepareSpecies`. It is base-species
   information, not the captured individual's IV-adjusted stats.
4. Call `Pokedex_PrepareFrontpicBase` on that explicit species instead of the
   list-resolving `Pokedex_PrepareSelectedMonTiles`. Commit the bank-0 base and
   compatible footprint before loading type graphics into the temporary payload.
   Initialize the normal icon buffer and load types before priming the first
   animated frame. Type staging uses the same WRAM0 payload; doing it after
   priming can overwrite ready frame data.
5. Reuse `Pokedex_PrimeDescriptionAnimation` to prepare the first complete stage
   and startup runway. `Pokedex_PrepareFrontpicBase` already arms the owner, so
   registration need not call the list-resolving `Pokedex_StartAnimationPrefetch`.
   Keep Info/ancestor staging out of the primed portrait payload, as current
   Selected does with its separate mini staging buffer.
6. Stage the complete maps, attributes, palettes and OAM, reveal once, then
   start the cry and deadline playback once. Expose a narrow prepared-owner
   entry in `Pokedex_BeginDescriptionAnimation` after its Listing-resolution
   prefix. Ordinary Selected can fall through that label with no added branch
   or call. Registration validates its initialized owner before entering it.
   Do not call `LoadMonAnimation` or arm the old resident New Entry owner too.

### Foreground Loop And Tab Transactions

The controller should use the existing owner-loop begin/end services, not the
old A/B wait loop or a second scheduler:

```text
BeginOwnerLoop: sample physical display tick, poll normal input
  update the shared blinking footer; dispatch A or final B/End
  PrepareDescriptionAnimation
  ServiceAnimationProducer
  CommitDescriptionAnimation
  service current lower view: Description text, Info, or Moves
EndOwnerLoop: normal audio refill and display-frame pacing
```

The fixed-species controller must omit `FindNextSeen`, `ChangeSpecies`, Area,
Listing restoration, bookmark capture and Start-menu fades. Reuse existing
footer cursor read/commit primitives; the fourth command dispatches End only
in this controller. Up/down cannot page species. On an Info/Mov/Desc request,
cancel obsolete lower-panel work but retain portrait flags, dictionary cursor,
slot identities, timeline pointer, absolute deadline and cry. Never call
`Pokedex_CancelAnimationPrefetch`, reset the whole Info workspace, reload the
base picture or invoke cry startup as part of a tab change.

Reuse `PokedexInfo_Activate/Service`, `PokedexMoves_Activate/Service`, and the
bounded Description text transaction. Their inputs are the fixed species/view
state and current permanent word, not a new copy of their semantic data.
Preserve coalesced rapid-A Info requests and committed-page publication.
Only the relevant inactive lower atlas/OAM is prepared. Existing VBlank
dispatch publishes the completed lower transaction without altering upper
portrait ownership, including the current Info-to-Description atomic-map fix.
No new check belongs in ordinary VBlank, STAT, timer or shared DelayFrame.

Battle registration remains normal speed; Game Corner registration retains
double speed. Existing Info admission already uses normal-speed conservative
bounds. Use that budget first; if a combined normal-speed trace misses a
portrait/audio deadline, reduce registration-local lower work or increase
pre-playback preparation, not shared ISR overhead or authored frame durations.

### Optional Full Dictionary Preparation

A registration-only startup loop can finish decoding the current species into
the **existing WRAMX bank-6 dictionary**, before its cry and animated timeline
start. VRAM still uses the two Selected frame slots; this is not restoration of
the colliding resident VRAM dictionary, a new cache, or extra species warming.
It needs no new graphics table or RAM buffer. It removes later dictionary
decoding from competition with tab work, but not frame uploads/publication.

The current linked assets show 393/399 already decode completely during normal
Selected startup. The six remaining cases have these additional existing
decoder-body costs at normal speed:

| Asset | Extra tiles | CPU-only ms | Display-frame equivalent |
| --- | ---: | ---: | ---: |
| Bastiodon | 68 | 24.554 | 1.467 |
| Drapion | 5 | 1.490 | 0.089 |
| Dusknoir | 102 | 38.738 | 2.314 |
| Groudon | 59 | 18.060 | 1.079 |
| Rampardos | 10 | 4.476 | 0.267 |
| Spheal | 45 | 18.314 | 1.094 |

These execute the current decoder and check every output byte, but exclude
the new loop's overhead, interrupts, audio, DMA and waits. They are **not**
end-to-end entry deltas versus production's already fully resident loader.
One display frame is 70,224 / 4,194,304 seconds. Use full preparation as a
low-memory normal-speed stability option in the prototype, and measure its
actual reveal cost against bounded preparation and current registration.

### Concrete Memory And Return Plan

Propose a 64-byte context alias at bank 2 `$d000-$d03f`, the beginning of existing
`wTempTilemap`. The old resident owner already borrows its first 98 bytes; the
Selected frame producer uses `wPokeAnimStruct` at `$d168` and its own WRAM0 plan
buffer instead. Do not place context inside `wPokeAnimStruct`: producer setup
clears that entire struct. Do not use SRAM scratch for context: base preparation
also writes there. Compile-time bounds and runtime write-watch tests must prove
that the proposed bank-2 bytes survive the complete new call graph.

| Context allocation inside that existing region | Bytes |
| --- | ---: |
| Battle graphics flags, saved palettes and producer metadata prefix | 32 |
| Saved hardware mirrors, input/display/species/form/volume fields | 25 |
| Previous permanent Dex species word | 2 |
| Previous Dex lock's permanent species word, zero if empty | 2 |
| Spare context bytes | 3 |
| Total assigned existing temporary bytes | 64 |
| Additional allocated WRAMX / WRAM0 | 0 / 0 |

The evidence JSON lists all 25 proposed byte fields. Save the previous lock by
**permanent identity**, not a raw temporary ID that garbage collection could
reuse while the screen is open. Recover/relock that identity on exit. Current
battle and script map species locks stay protected throughout.

Do not back up the full 1,300-byte WRAM0 union or its 784-byte battle picture
payload. At entry require the old battle producer and DMA transaction to be
inactive; finish/cancel it under the existing loader contract if necessary,
before starting any registration owner. Restore semantic prefix state at exit
but invalidate graphics-clean claims whose VRAM was replaced. Never restore
an active producer referring to an overwritten payload.

B/End must first cancel lower jobs/requests, stop page-owned cry safely, cancel
streaming, release quiet ownership and clear OAM before restoring the caller's
dispatcher/viewport/bank fields. Reuse the existing post-catch font/palette/DV
and nickname continuation, with captured species/level/moves/PP/item/DVs intact.
Do not change the capture delivery/discovery hooks or write persistent fields.

For Game Corner, add `ReturnToMapFromSubmenu` after the interactive call and
before `ExitAllMenus`. Its `MAPSETUP_SUBMENU` script rebuilds block and connection
block data only. Existing `ExitAllMenus` reloads graphics/palettes but does not
rebuild the overwritten blocks. Normalize the prize species explicitly before
entry, preserve the active script/menu stack and `wScriptVar`, and resume the
existing `givepoke`/coin deduction flow exactly once. No new shared map-return
or battle-speed behavior is required.

### Expected Source Boundaries And Costs

| Owner | Required change |
| --- | --- |
| New `new_entry_streaming.asm` | Fixed-species setup, preparation/loop, local footer actions, context and exit orchestration |
| `new_pokedex_entry.asm`, its include in `main.asm` | Route registration to streaming instead of its two A/B resident waits; retain the public caller boundary |
| `pokedex_animation.asm` | Expose a prepared-owner animation-start label; registration-only full-decode entry if chosen |
| `_NewPokedexEntry` / `new_entry_visual.asm` | Adapt or bypass resident-only setup; use streaming-compatible footprint/types/footer, no resident animation call |
| `ram/wram.asm` | Name and assert the 64-byte alias without moving existing labels or growing a section |
| `engine/events/specials.asm` | Explicit prize-species input and map-block reconstruction on prize return |
| Tests / documentation | New input/service/return observers, normal/double-speed fixtures, publication/write-watch and audio assertions |

`load_pics.asm`, Info/Moves/ancestors, Description text, frame plans/timelines,
normal Selected controller and interrupt publication should be reused without
new per-frame branches. Their existing behavior is the regression reference;
do not make them registration-aware by adding a generic owner flag everywhere.

Budget remains **2,000-5,000 extra ROMX bytes** before measured cleanup credits;
the concrete context plan targets **zero allocation growth** in all RAM classes
and no added ROM0/HRAM. New assets, species tables and save format changes are
unnecessary. Old resident code/home bridges can be assessed for retirement only
after every caller, type upload and DelayFrame/audio dependency is accounted
for. Do not combine global DelayFrame timing changes with this prototype or
count an unimplemented deletion as a space saving.

Complexity is moderate-high integration, concentrated in initialization,
scratch ownership, scheduling and return, not a new graphics/animation engine.
The 64-byte lifetime proof and normal-speed combined workload are prototype
acceptance gates, not guaranteed by this source-only assessment.

### Prototype And Qualification Gates

1. Freeze the current ROM/save/source rollback; build only under `build/`.
   Implement fixed-species streaming startup/exit first, checking correct
   Unown form, first complete reveal and exact normal/double-speed playback.
2. Add the four footer actions and existing lower services. Check every Info/
   ancestor/Mov page, all tab pairs and input phases during active playback.
   Require unchanged event order/holds, no missed/incomplete frames or cry
   starvation, no restart on tabs, and correct natural finish.
3. Write-watch context and live capture/script data. Force transient-ID garbage
   collection, save/restore bank/register/stack ownership, and exercise B/End
   from every queued/uploading/published state. Verify correct party/PC/nickname,
   transformed catch, contest and both Game Corner prize returns, then walking
   and continuing menus. Require untouched discovery except genuine acquisition
   and unchanged Dex sort/presentation/session bookmarks.
4. Run the full documented regression, including all other Dex owners, normal
   saving/loading, all move animations from both sides, cries, menus, PC/daycare
   and the independent Tower suite for the reused union. Use fresh matching-link
   fixtures, not relocated CPU states. Compare authentic entry/tab/page/exit
   timings in ms and physical frames; distinguish requested exit cancellation
   from natural cry completion. Manual review precedes production integration.

Fresh read-only evidence: `build/new-entry-interactive-scope-20261015/streaming-preflight.json`.
The decoder/preparation and proposed context checks do not constitute a running
interactive prototype or full native qualification. Production is unchanged.

## Double Speed Registration Assessment

Scoped and diagnostically tested on 2026-10-15 against the current production
hash above. The user additionally authorized an audio experiment at the proposed
"Gotcha!" handoff. The private diagnostic exists under
`build/new-entry-clock-scope-20261015/gotcha/`; it retains today's visual-only
two-page registration. **It is not an interactive registration implementation,
an approved clock policy, or a production-ready transition.** Production ROM,
symbols, map and the source battery were hash-verified unchanged.

### Finding And Capture Timeline

Double-speed registration is feasible; the speed change does not require
catching one precise frame of the ball animation. Establish a quiet, hidden
handoff, then perform the existing guarded hardware switch. The difficult
choices are the scope of the new clock ownership and the audio/display
presentation at its boundary, not a hardware prohibition on switching here.

The current successful-capture sequence in `engine/items/item_effects.asm` is:

1. Finish the ball animation and restore the caught species, moves/PP and other
   capture state. The tutorial branches to its own finish path.
2. Print `Gotcha! <nickname> was caught!` and play `SFX_CAUGHT_MON`.
3. Its text-ASM callback, `Text_GotchaMonWasCaught`, already calls `WaitSFX`,
   plays `MUSIC_NONE`, waits a display frame and starts `MUSIC_CAPTURE`.
4. Award EXP through `ApplyExperienceAfterEnemyCaught`. This can include
   level-up and move-learning screens. Restore captured species/level afterward.
5. Check prior caught/Dex ownership, set seen/caught and, only when appropriate,
   print the new-data message and call `NewPokedexEntry`.
6. After registration, perform contest/party/PC delivery, actual move-discovery
   hooks, happiness/caught-data work and optional naming/PC messages.
7. Exit battle, including `EvolveAfterBattle`, clear `wBattleMode`, then reload
   the map. The hidden map setup currently performs the normal-to-double switch.

Thus the user's proposed location contains a real audio-reset opportunity:
**after the existing caught fanfare finishes and `MUSIC_NONE` runs, before the
capture tune starts**. Do not switch at the instant the message starts, during
the fanfare, or in the ball animation. This candidate also changes the clock of
EXP/learning and every subsequent capture-owned screen; it is not Dex-only.

`GameCornerPrizeMonCheckDex` already enters at double speed, so it must not
perform another switch. Already-caught/no-Dex successful catches should share
whatever successful-capture tail policy is adopted. Avoid making the tail's
clock depend on whether registration happened to appear.

### Hardware And Audio Contract

`home/double_speed.asm` provides the guarded `DoubleSpeed`/`NormalSpeed` entries
and the shared `SwitchSpeed` body. The latter clears IF/IE and prepares JOYP
before STOP, but does not restore interrupts, protect graphics/audio, or restore
music by itself. Do not call it raw from visible text or an active sample.

The conservative boundary is:

1. Finish short SFX at their current speed. If a sample can be present, use a
   service-aware wait such as `WaitCrySFX`, or cancel only its legitimate owner.
   Do not busy-wait on a sample without refilling it.
2. Hide the transition; finish/cancel graphics producers and transfers. Disable
   the LCD through its existing safe wait before masking all interrupts.
3. Save IE, disable interrupts, retire sampled ownership, disable NR52, invoke
   the guarded speed helper, and reinitialize sound. Restore IE/interrupts.
4. Complete the display/owner setup before revealing. Start the intended music
   and new registration cry only after the final speed is established.

`BattleSpeed_LeaveNormal` supplies most of the existing normal-to-double
primitive and leaves the LCD off. `BattleSpeed_EnterNormal` is **not** a generic
reverse primitive: it reenables LCD and jumps to `PlayBattleMusic`, deliberately
restarting the battle track. A registration-only island needs a local reverse
helper without that behavior, not a new generic ISR path.

The audio reset matters: `_InitSound` clears **447 bytes** from `wAudio` through
`wAudioEnd`, in addition to resetting sound registers. `wMusicID` is also used
by SFX/cries; saving its value alone is not even a reliable song identity, much
less preservation of channel positions. Restarting a known song, choosing
silence, and continuing the exact musical position are different policies.
The capture tune loops, so waiting for it to finish is not a general solution.

An exact continuation scheme would have to preserve/reconstruct audio software
and hardware state. Backing up the entire software region alone requires 447
temporary bytes, before register/phase handling. Power-cycling the APU also
loses hardware phase, so that backup is not proof of click-free continuation.
This is unnecessary at the tested Gotcha reset gap and is not included in any
low-memory estimate below. Leaving live audio running across STOP remains an
unqualified research option, not a recommended shortcut.

[Pan Docs' KEY1 guidance](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md#ff4d--key1spd-cgb-mode-only-prepare-speed-switch)
documents the guarded STOP procedure, doubled CPU/timer clocks, unchanged
display/APU rates, and display/audio hazards during STOP. Those properties do
not imply a real-time event or cry should play twice as fast. Existing
double-speed sampled playback uses a different timer configuration to retain
the same physical sample period.

### Measured Gotcha Diagnostic

The candidate changes only `Text_GotchaMonWasCaught` in its private source copy:
after `MUSIC_NONE`, skip the experiment for the tutorial, otherwise disable LCD,
far-call `BattleSpeed_LeaveNormal`, reenable LCD, then follow the original
`DelayFrame` and `MUSIC_CAPTURE` sequence. **Linked delta: +19 ROMX bytes;
0 ROM0, WRAM0, WRAMX, HRAM or SRAM bytes.** No new graphics, table or per-frame
branch is involved. It deliberately stays double speed through the capture tail;
the map helper's existing KEY1 guard then avoids a second return switch.

Fresh matching-link encounter checkpoints were generated for each ROM. Normal
inputs select the ball, dismiss text, visit both existing registration pages,
decline naming and return to the map. Species changes are explicit generated
encounter fixtures, not alterations to the player's save. Four input schedules
per species include fast dismissal and a 180-frame Gotcha pause: eight paired
comparisons / **16 final executions**, plus two sampled-content executions.
The initial quarter-frame offsets sometimes reconverge at existing frame waits;
this is not an exhaustive sweep of all hardware STOP phases.

| Observation | Production vs diagnostic |
| --- | --- |
| Final control-flow/clock assertions | All 18 focused executions pass; map returns at double speed and party count agrees |
| Switches from the post-battle-entry encounter checkpoint to the map | One in each: production switches at map reload, candidate switches at Gotcha |
| Hardware when KEY1 is armed | LCD off, APU off, IME off, no active sample and no HDMA; no SameBoy odd-mode warnings |
| Caught fanfare / preceding sound-register command stream | Identical in all eight pairs |
| Capture tune starts / later map music | Same song sequence, one capture start, no added mid-song restart |
| First 120 display-equivalent intervals of uninterrupted capture music | Same 34 channel/frequency triggers in all four paused pairs; maximum onset-relative timing shift 3.980 ms / 0.238 frames |
| Dusknoir registration sample content | 557/557 blocks, identical block hash and CH3 frequency 1848 at both speeds |
| Dusknoir registration sample rate | Identical median block spacing, 3.051758 ms / 0.182274 frames (12,800 reference T-cycles); normal TAC/TMA 6/56 changes correctly to double 7/156 |
| Dusknoir initial battle-appearance sample | Existing 512/557-block cutoff, 45 blocks remaining, unchanged before the switch in both ROMs; not fixed or counted as a successful complete cry |

Automated register/content checks do not replace listening or real hardware
qualification. The recorded comparison WAVs contain production first, 0.7 s of
silence, then the diagnostic, starting just before the caught fanfare:

- `build/new-entry-clock-scope-20261015/gotcha/review/caterpie-production-then-gotcha.wav`
- `build/new-entry-clock-scope-20261015/gotcha/review/dusknoir-production-then-gotcha.wav`

A uniquely named review ROM, `pokecrystal-registration-clock-test.gbc`, and its
matching symbols/map/private save are in that same review directory. Continue
places the test player on Route 30 with Master Balls and cleared caught flags;
encounter a wild Pokemon and catch it to exercise the handoff. This is a test
save, not the player's main save. The ROM changes only clock placement and still
has the old two-page registration, not Desc/Info/Mov/End. Do not promote it.

| Timed span | Milliseconds | Display-frame equivalents |
| --- | ---: | ---: |
| Existing normal-to-double `SwitchSpeed` body | 15.645 | 0.934 |
| Existing leave-normal wrapper including observer far-call unwind | 18.009 | 1.076 |
| Existing double-to-normal `SwitchSpeed` body | 31.263 | 1.867 |
| Diagnostic LCD-disabled interval at Gotcha | 18.040 | 1.077 |
| Added Gotcha-callback-to-capture-music delay vs paired production | 32.899-32.909 | 1.965-1.966 |

These spans overlap and must not be added together. The later map transition's
switch moves earlier rather than being newly added; the cue-onset delta is not
a measured increase in total catch duration. The reverse wrapper also starts
battle music, so its measured 56.542-56.544 ms / 3.377 frames is not the cost of
a future minimal registration-exit helper.

Measurements use the local SameBoy CGB E core and physical elapsed time, with
one display frame = 70,224 / 4,194,304 s. LCD-off intervals are time equivalents,
not displayed pictures. SameBoy's STOP implementation explicitly notes incomplete
speed-switch timing tests and uses a pause model different from Pan Docs' stated
pause. These values are emulator measurements, not certified hardware latency.

The diagnostic intentionally does **not** polish the visible handoff: disabling
and reenabling LCD on the caught-text screen introduces a brief display
interruption. Its complete cue-onset shift is roughly two frames, with LCD off
for about one. Test a fade/hidden handoff and capture it frame by frame before
treating the +19-byte experiment as a shippable solution. The experiment is
evidence against a timing/audio impossibility, not proof of visual acceptability.

### Alternatives And Production Budget

The numbers below are planning envelopes for the additional clock integration
only, except for the linked +19-byte diagnostic. The existing interactive
streaming feature remains separately budgeted at 2,000-5,000 extra ROMX bytes.
No implementation retirement credits are assumed.

| Boundary / ownership | Added ROMX clock budget | New RAM target | Complexity / principal risk |
| --- | ---: | --- | --- |
| Gotcha's existing sound-reset gap; stay double through successful-capture tail | 19 measured diagnostic; 128-384 planning allowance for production guards/presentation | 0 allocated bytes | Small clock change, moderate integration/qualification; visible handoff and XP/learning/naming/evolution now double |
| Hidden registration setup; stay double afterward | 96-256 estimated | 0 allocated bytes | Moderate; leaves XP untouched but interrupts an active capture track and can make first-catch vs repeat/no-Dex tail clocks inconsistent unless broadened |
| Registration-only double-speed island, restore incoming speed on B/End | 192-512 estimated | 0 allocated target; one flag in the proposed existing context | Moderate-high; two extra switches on new-entry catches, two audio boundaries, new reverse helper and hidden exit |

For the first candidate, a combined conservative planning allowance is therefore
**2,128-5,384 ROMX bytes** for interactive streaming plus clock adaptation,
not 19 bytes for the whole feature. Actual visual-transition choices can change
that allowance and require a fresh link. The 64-byte scratch-lifetime proof
from the streaming scope still applies. The Gotcha approach needs no music-state
snapshot; it knows the next track and switches before that track begins.

All approaches target zero new ROM0/HRAM/WRAM0 and no allocated WRAMX growth.
They must not add checks to shared VBlank/STAT/timer/DelayFrame hot paths.
Do not clear `wBattleMode` early to trick map setup; capture delivery and battle
cleanup still own that semantic state even when their CPU clock becomes double.
The next battle must use the existing guarded entry and return to normal speed.

**Recommendation after the diagnostic:** investigate a polished Gotcha reset-gap
handoff as the lowest-state, lowest-switch-count option if changing the whole
successful-capture tail is acceptable. The native audio evidence is favorable;
the remaining blockers are display review and broader timing qualification.
If strict isolation from EXP/naming/evolution is required, use the registration
island instead and budget for explicit music policy plus the extra reverse
switch. Switching later solely to avoid the Gotcha display transition trades
that concern for a harder ongoing-music handoff, not a free simplification.

### Required Qualification Before Interactive Promotion

- First catch, repeat catch, no-Dex catch, failed ball, tutorial, debug, contest,
  Celebi, transformed catch, full-party PC send, nickname yes/no and cancellation.
- EXP Share/multiple recipients, level-up stats, accepted/declined learning,
  post-battle evolution yes/no, evolution cry/graphics, and subsequent walking,
  menus, saving/loading and next-battle entry. A double-speed tail must not
  accidentally execute another actual battle action at double speed.
- Game Corner prizes at already-double speed, including both prize callers,
  exact script/coin/givepoke continuation and map-block reconstruction.
- Fast/held input around both cues and every tab/exit, short UI SFX, synthesized
  and even/odd-period sampled cries, natural completion vs intentional exit
  cancellation, no extra move discovery, and unchanged captured data/locks.
- Record every actual switch's LCD/APU/sample/DMA/IME/IE conditions, verify KEY1
  after it, restore banks/registers/stack, and test soft reset from every owner.
- Frame-by-frame presentation and listening A/B; do not infer absence of a click
  from note-frequency parity. Real CGB/GBA or another independent accurate core
  should qualify the new STOP placement before hardware-safe claims.
- Then the full documented Dex, all-move/both-sides, audio, menus, PC/daycare,
  save and independent Battle Tower suites. No full regression was run for this
  diagnostic-only scope; interactive tab timing/continuity has not been tested.

Evidence: `switch-diagnostic.json` (existing helper spans and STOP snapshots),
`gotcha/manifest.json` (linked cost and protected hashes), `gotcha/report.json`
(16 final native runs), `gotcha/sample-content-report.json` (two content runs),
`gotcha/audio-analysis.json` (paired command/timing comparisons), and
`gotcha/gotcha.diff`, all below `build/new-entry-clock-scope-20261015/`.
Private experiment/analysis scripts are retained there for reproduction.
Initial rejected harness attempts are retained separately: the first tried to
break on text-script data instead of its ASM callback; the next counted the
earlier battle-entry switch even though its checkpoint was captured afterward.
Corrected final runs use the verified executable callback and expect one
remaining switch. Neither required a game-runtime fix.

## Gotcha Boundary Prototype Results

Later [interactive qualification](pokedex_interactive_registration_prototype.md#broad-regression-and-retained-exceptions)
found that this campaign's original no-Dex fixture cleared the Unown-Dex bit,
so those earlier bypass results were false positives. The later corrected
baseline/candidate replays clear the actual Dex flag, inspect its native query
and require zero registration entries. The earlier no-Dex rows below are
historical evidence, not valid bypass qualification. Production game code was
unaffected by this test-fixture mistake.

Built and qualified 2026-10-15 at
`build/gotcha-boundary-final-20261015/`. The review ROM is
`review/pokecrystal-gotcha-boundary.gbc`, SHA-256
`27b2ebfc3d40740d0e98b58f3e41a8dea661ce0b0dc13d7e9b0fe18e4c502b3e`.
Production remains the unchanged `52ba945b...` baseline above. This is a
**clock-boundary prototype with the current two-page registration**, not
Desc/Info/Mov/End and not a production integration.

### Implementation And Cost

`Text_GotchaMonWasCaught` calls a new ROMX-local
`BattleSpeed_CaptureHandoff` after the existing `WaitSFX` and `MUSIC_NONE`, before
`MUSIC_CAPTURE`. The helper keeps the tutorial unchanged and returns immediately
when already double speed. It fades the actual RGB palette components toward
white, disables LCD, reuses `BattleSpeed_LeaveNormal`, reenables LCD and fades
back. The battle remains semantically active: do not clear `wBattleMode` early.
EXP, learning, registration, delivery, naming and evolution now execute at
double speed after a successful ordinary catch. A subsequent battle still
enters normal speed; the existing map guard skips a redundant return switch.

The helper is included with `start_battle.asm` in bank 11. Its only caller is
the successful-capture text callback in `engine/items/item_effects.asm`.
The private source diff is `candidate.diff`; reusable source and the builder
are `tools/dex_timing/probes/gotcha_boundary.asm` and
`tools/build_gotcha_boundary_prototype.py`.

| Linked resource delta vs production | Decimal bytes |
| --- | ---: |
| ROMX | +219 |
| ROM0, WRAM0, WRAMX, HRAM, SRAM | 0 each |
| New graphics, species metadata or persistent save fields | 0 |

The fade borrows existing `wBGPals2`/`wOBPals2` and `hCGBPalUpdate`, with bounded
stack/register saves. Original source palettes and BGP/OBP mappings are unchanged.
There is no new shared VBlank, STAT, timer or DelayFrame work. **Queue palette
publication only after the whole RGB step is prepared**: use `CopyPals`, not
the wrappers that queue an upload midway through the producer. Preserve the
brightness input across `DelayFrame`, which clobbers A. Both dependencies have
independent tests, including rejection of the earlier broken linked helper.

### Focused Qualification

| Fresh final-link coverage | Result |
| --- | --- |
| 13 gameplay scenarios, four input offsets, two ROMs: 104 executions / 52 paired data comparisons | All pass; exact party/box species, EXP, level, stats, DVs, PP, moves, nicknames and discovery flags at the tested boundaries |
| Subsequent battle victory and subsequent capture after party/PC naming routes: eight additional executions | All pass, including box nickname/storage assertions and normal-speed real battle attacks |
| Total observed clock transitions in those 112 executions | All 336 have LCD/APU off and no active sample; no odd-mode warnings or leaked post-catch speed into battle actions |
| Twenty species/form registration contexts, six playback/input schedules, both ROMs: 240 executions | All pass authored publication, pixels, sample completion/cancellation and return contracts |
| Current New Entry host contracts | 20 per ROM, 40 pass; zero skips |
| RGB blend oracle | All 32,768 colors at strengths 0/8/16/31: 131,072 checks pass |
| Full fade-step mapping/publication contracts | 112 combinations of brightness, incoming WRAM bank and BGP/OBP mappings pass; palette dirty flag is queued only after completed preparation |
| Tutorial/already-double guard controls | Six register/stack/no-publication checks pass |
| Native frame capture | Both representative routes show two distinct intermediate gray levels, full white and the reverse restoration sequence |

The gameplay scenarios explicitly cover first catch, repeat catch, no-Dex catch,
party/PC delivery, nickname accepted/declined, an empty move slot, move replacement,
declined learning, EXP Share and multiple recipients, multiple gained levels,
and accepted/canceled post-battle evolution. Bulbasaur learns Leech Seed at
level 7; declined learning neither changes its moves nor discovers Leech Seed.
The multiple-level fixture advances from 6 to 10 and learns Vine Whip too.
EXP Share advances both Bulbasaur and Caterpie to 7. Caterpie evolves to Metapod
and learns Harden when accepted, or remains Caterpie when canceled.

Each main scenario then walks into another real encounter, checks normal speed,
escapes, returns to the double-speed overworld and opens/closes the Start menu.
The supplemental routes also actually defeat the next opponent or catch another
Pokemon. Capture-tail data comparisons ignore expected clock/input/temporary
workspace differences, not party or box semantic differences.

Fixtures boot each link from private batteries. Declared species, party, EXP,
held-item and flag data are changed before the native enemy initializer; CPU,
PPU, APU and speed are not fabricated. Quarter-frame requests can reconverge at
existing waits, so these are four input schedules, not every possible STOP phase.
The registration expansion uses explicitly generated species contexts from
fresh matching-link native catches, not twenty claims of naturally encountered
wild species. Source batteries and the player's main save remain untouched.

The existing Dusknoir initial battle-appearance cutoff still leaves 45 of 557
blocks in both links, before the new boundary. It is not a new failure or a
complete cry. Its subsequent registration playback completes 557/557 blocks
with identical content and physical sample spacing at normal and double speed.
No new audio starvation was observed. The 240-case suite additionally checks
even/odd-period sampled species, heavy pictures and natural versus canceled
playback; it does not make a real-hardware certification claim.

### Timing And Manual Review

| Measured SameBoy CGB E span | Milliseconds | Display-frame equivalents |
| --- | ---: | ---: |
| Local fade and speed handoff, minimum / median / maximum | 158.264 / 158.340 / 158.361 | 9.453 / 9.457 / 9.459 |
| Capture music starts later than paired production, minimum / median / maximum | +166.753 / +166.776 / +166.788 | +9.960 / +9.961 / +9.962 |
| Maximum complete palette preparation before the speed switch | 13.940 | 0.833 |
| Maximum complete palette preparation after the speed switch | 5.934 | 0.354 |
| Minimum observed preparation margin to next VBlank | 1.281 | 0.076 |

The deliberate fade is the main presentation cost relative to the earlier
19-byte bare-switch diagnostic. These spans overlap; do not add them together
or claim that music-onset delay equals total catch-duration change. The palette
producer currently completes before the next VBlank, and its publication gate
also prevents an incomplete palette upload if future preparation work grows.
One frame is 70,224 / 4,194,304 s; LCD-off time is a physical-time equivalent.
SameBoy STOP timing is model-specific, as noted in the earlier assessment.

The review directory contains:

- `pokecrystal-gotcha-boundary.gbc`, matching `.sym`/`.map` and a separate `.sav`.
- `capture-audio-production-then-prototype.wav`: production, 0.7 s silence,
  prototype; actual captured audio without pitch or timing adjustment.
- `party-name-production-vs-prototype.mp4`: synchronized Gotcha origin through
  sampled registration and naming, production left / prototype right, silent.
- `evolve-production-vs-prototype.mp4`: the same comparison through evolution.
- `gotcha-fade-first-12-frames.png`: frame-by-frame transition contact sheet.

Continue the review save on Route 30. It has four Pokemon, Master Balls,
Bulbasaur one EXP below level 7 and Caterpie one EXP below level 7 holding EXP
Share. The first successful catch exercises learning before registration and
evolution afterward; accept/decline those prompts normally. Names and move
choices are editable, and B still cancels evolution. This is not the main save.
A fresh Continue check verified its party, EXP, held item and double-speed map.

The user requested recordings/captures for future scoping; that standing
preference is now in root `AGENTS.md` and the regression testing principles.

### Reproduction And Remaining Gates

Use a fresh `build/` output and pass the same output to each command. The builder
uses the retained matching production template
`build/dex-position-memory-20261014/candidate`; the runtime seed is the retained
private `legacy-input.sav` described by the main regression runbook.

```sh
export PYTHONPATH=tools:.
python3 -B tools/build_gotcha_boundary_prototype.py --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary setup --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary campaign --output build/gotcha-review-new --jobs 8
python3 -B -m tools.dex_timing.gotcha_boundary supplement --output build/gotcha-review-new --jobs 4
python3 -B -m tools.dex_timing.gotcha_boundary registration --output build/gotcha-review-new --jobs 8
python3 -B -m tools.dex_timing.gotcha_boundary contracts --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary_palette --root build/gotcha-review-new/candidate --report build/gotcha-review-new/palette-oracle.json
python3 -B -m tools.dex_timing.gotcha_boundary_review analyze --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary_review visuals --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary_review visual_audit --output build/gotcha-review-new
python3 -B -m tools.dex_timing.gotcha_boundary_review publish --output build/gotcha-review-new
```

Run `tools.test_new_dex_entry` against each matching source/link before publish;
the final `contracts.json` records those two 20-test results. The helper's
brightness negative control is retained as
`brightness-negative-control.json`, with its rejected source/link in
`build/gotcha-boundary-rejected-argument-loss-20261015/`. Initial harness retries
also remain labeled: an invalid net-coordinate assertion and a follow-up fight
driver repeatedly choosing newly learned Leech Seed instead of Thunderbolt.
Neither was a production game defect. The 93-byte palette-index fade and the
intermediate RGB attempts are rejected visual/control-flow experiments, not
qualified alternatives or promotion candidates.

Final evidence lives in `manifest.json`, `report.json`, `comparison.json`,
`supplement.json`, `registration.json`, `palette-oracle.json`, `contracts.json`,
`visual-audit.json`, the negative control, `candidate.diff`, and `review/`.
The ordinary global all-move/Dex/menu/save/Tower campaign was not rerun for this
clock-only prototype. Special contest/Celebi/debug/tutorial event continuations
and real CGB/GBA playback are not newly claimed as native coverage here; the
tutorial bypass is directly tested. Manual presentation approval and the wider
promotion regression remain gates, followed by the separately scoped interactive
streaming implementation. Do not integrate merely because this focused suite
passes.

## Historical Scope From 2026 10 13

Scoped 2026-10-13 against production commit `81ff02a25`. Both requested options
are feasible. The user subsequently selected visual-only option A; its private
implementation and measured results are in [the prototype report](pokedex_new_entry_visual_prototype.md).
Option B remains scoped only. Production ROM and the player battery remain unchanged.

The cleanup findings and exact builds were archived first in
[Deferred Dex Cleanup Archive](archived/dex-unused-scope-20261013/README.md).
Both archived source/patch packages were restored and rebuilt; each produced
its original ROM byte-for-byte. Cleanup remains deferred until registration
is finalized.

## Options

| Dimension | A Visual Only | B Desc Info Mov End |
| --- | --- | --- |
| Description content | Same panels, borders, page badge, text, colored frontpic, footprint and type badges as Selected Description | Same, with the interactive footer |
| Controls | Current two-page A/B flow retained | Left/right footer selection; A activates; B or A on End leaves |
| Info and Moves | Not available | Reuse existing species Info and Moves pages |
| Species selection | Captured species only | Captured species only; no up/down species paging |
| Portrait architecture | Keep current resident New Entry owner | Must choose a static handoff or Selected streaming owner |
| New graphics or semantic tables | None expected | None expected; End uses the existing font |
| Complexity | Low/moderate | Moderate with static portrait handoff; moderate/high for uninterrupted portrait animation |
| Principal risk | Text/badge publication and post-catch restoration | The same risks plus RAM/VRAM ownership and normal-speed lower-panel servicing |

### Planning Costs

These are the original **engineering planning envelopes, not linked measurements**.
Option A's subsequent measured cost is 227 ROMX bytes, with no added RAM; see
the prototype report above. B has not been implemented. Estimates exclude
unrelated cleanup and do not duplicate the existing
Info/Moves/ancestor tables or glyph atlases.

| Resource | A Visual Only | B Static Handoff | B Continuous Animation |
| --- | --- | --- | --- |
| Additional ROMX budget, net of replacing the old registration shell | Approximately 300-800 bytes | Approximately 1,000-2,500 bytes | Approximately 2,000-5,000 bytes |
| Added allocated WRAMX target | 0 bytes | 0-64 bytes for context/owner bookkeeping | 0-64 bytes for context/owner bookkeeping |
| Added allocated WRAM0 target | 0 bytes | 0 bytes | 0 bytes |
| Added ROM0 / HRAM target | 0 / 0 bytes | 0 / 0 bytes | 0 / 0 bytes |
| Persistent SRAM or save migration | None | None | None |
| Implementation effort before full qualification | Small | Several times A | Larger owner integration and timing audit |

The WRAMX allowance is a conservative contingency, not a request to allocate
it immediately. Prefer existing verified-dead owner scratch, stack-held small
context and existing temporary SRAM staging. Do not allocate a full battle
scratch backup or another page buffer merely because it simplifies integration.
The actual source/alias audit must decide which state can safely be reused.

The source banks containing the existing registration, Description and Info
code have available space, but final placement must be checked after linking.
No new ROM bank is inherently required for either option.

## Shared Visual Work

The reference is the actual current Selected Description owner, not a new
approximation of its mockup. Reuse `PokedexDescriptionTilemap`,
`PokedexDescriptionGFX` and `PokedexDescriptionRightEdge` in
`engine/pokedex/pokedex_description.asm`.

At native 160 by 144 pixels and the existing five-pixel horizontal offset,
the portrait outline is x=1..60, y=5..66; the data outline is x=62..158,
y=5..66; the lower outline is x=1..158, y=69..130. The extra right-edge column
is necessary because the horizontal offset exposes five pixels beyond the
ordinary 20-column backing map. It must have the Description join/divider
tiles and palette-0 attributes through every reveal and text-page change.

Name, number, category, height, weight and text positions already largely
match. The substantive differences are the shell/divider/page badge, footprint
background, compact type badges and footer handling. Keep the existing
species data and authored descriptions; this does not change National IDs,
evolutions, learnsets or wording.

`Pokedex_LoadGFX` already calls `Pokedex_LoadPermanentCGBGFX`, which loads the
Description border/page graphics and permanent badge/Info assets. A must not
add another copy of their ROM data or eagerly reload them just to change the
registration tilemap. The shared shell data comprises a 360-byte backing map,
18-byte edge column and 160-byte border/badge graphics, all already linked.

Use a registration-specific palette/setup adapter. Do not call Selected's
full entry procedure or fake its species-list context simply to satisfy a
layout check. Its entry/exit/controller assumes a Listing, saved viewport,
species navigation, Area and Start-menu return ownership that registration
does not have.

## A Visual Only

Keep `NewPokedexEntry` in `engine/pokedex/new_pokedex_entry.asm` as the lifecycle
and `new_dex_entry_animation.asm` as the resident animation owner. Preserve:

- A or B advances page 1 to page 2; A or B then returns from registration.
- The initial authored main/hold/idle animation and cry begin once.
- Description paging does not restart or interrupt portrait/cry playback.
- Final exit cancels the page-owned sampled cry and restores the original
  catch/naming context and normal-speed clock policy.

Replace `_NewPokedexEntry`'s old background/edge setup with the common
Description shell and explicit registration attributes/palettes. Reuse the
entry printer through the Description divider/page-badge repair instead of
leaving its old divider on screen. Initialize the description-page state
explicitly, rather than relying on a previous Dex session's value.

### Type Badges And Footprint

The compact type OBJ destinations are already safe with the resident loader.
Use the same tile graphics, palette colors and screen positions as Selected:
one 32 by 8 badge at x=67, y=56 and an optional second at x=107, y=56. Monotypes
must clear the second four-sprite slot. Eight sprites on the badge scanline
remain below the ten-sprite limit.

However, `PokedexInfo_LoadTypeSprites` is not safe to call unchanged from
battle registration: its staging buffer is `wPokedexWRAM0Scratch`, which
aliases battle graphics state. Reuse its compact-type copy/remap primitive,
but stage registration's small upload in its existing temporary upload
workspace rather than overwriting live battle state. Select and restore the
SRAM/WRAM/VRAM banks explicitly, and publish the initial OAM before the
resident animation owner locks ordinary OAM updates.

Keep registration's existing four footprint tiles in VRAM bank 0. Apply the
same white/dark-gray footprint palette as Selected while leaving their bank
attribute at zero. This is pixel-equivalent without moving the footprint to
Selected's conflicting bank-1 address. It also keeps the current animation
dictionary capacity available for future species.

### Description Page Two

Keep the existing disjoint, immutable text transaction. The current New Entry
publisher copies 90 text cells plus one old page-number cell. The modern page
badge has two changing cells, at backing coordinates (2,8) and (2,9), so page 2
must commit **92 cells**, not merely replace the old lower digit.

That additional cell requires remeasuring the New Entry-only publication
routine's live-LY admission margin. The present 91-cell normal-speed contract
has 296 T-cycles of store margin; adding a literal load/store pair would consume
32 T-cycles, but the complete linked path must confirm its actual cost. Do not
relax the cutoff or add any check to ordinary VBlank/STAT dispatch.
The frame-map ACK barrier, text READY discipline and final-owner retention
must remain intact.

### Footer

For A, retain the registration continuation indicator in the same footer
geometry. The content panels should match Selected exactly; showing inactive
Info/Mov/Area commands would imply navigation that A does not implement.
This footer content is the intentional visual difference, not a new layout.

### Runtime Expectation

No new per-frame graphics composition, extra dictionary loading or cry startup
is needed. The shell is already resident. Badge staging adds a small one-time
copy/upload to entry, and the page-2 publisher adds one cell. These are expected
to be small costs, but no millisecond or display-frame delta is claimed without
a prototype. Measure setup-to-first-complete-reveal and input-to-complete-page
separately; keeping the same animation timeline does not prove unchanged entry
latency.

## B Desc Info Mov End

Give registration its own fixed-species controller and return path. Reuse
lower-panel renderers, not `PokedexSelectedMon_Update` or
`PokedexSelectedMon_Leave` wholesale.

Proposed behavior:

- Open on Description P.1 with Desc selected.
- Left/right moves the shared blinking footer arrow between Desc, Info, Mov,
  End. Up/down does not change species.
- A on Desc from another tab returns to Description P.1; subsequent A presses
  on Desc toggle P.1/P.2. Description does not automatically exit on A.
- A on Info opens Stats, then cycles the existing Evolutions and Evolves From
  pages in their current order and wraps. A on Mov opens/cycles the existing
  species learnset pages.
- A on End, or B from any tab, cancels pending work and returns to the original
  capture sequence. Area is not available.

Mov means the Selected screen's species learnsets, not the newly captured
Pokemon's four current moves and not the standalone searchable Moves Dex.
Viewing those records must not mark the entire learnset as seen.

The capture code in `engine/items/item_effects.asm` sets Seen/Caught before
opening registration, but party/box insertion and nickname handling happen
after it returns. The interactive screen must remain read-only and preserve
the enemy/captured-mon records required by those later operations. Do not
treat viewing Info as completion of acquisition or move-discovery hooks.

### Why The Resident Owner Cannot Simply Keep Running

The read-only audit covered all **399 linked species/form animation assets**.
Maximum dictionary size is 247 tiles, with a maximum 198-tile tail. Existing
bank-1 overlap counts are:

| Region | Assets with a resident-dictionary overlap |
| --- | ---: |
| Description type OBJ sets | 0 |
| Info mini and HP endpoint OBJ regions | 0 |
| Selected normal footprint | 4 |
| Selected alternate footprint | 22 |
| Info glyph atlas A | 399 |
| Info glyph atlas B | 399 |

The four normal-footprint conflicts are Bastiodon, Dusknoir, Groudon and
Spheal. The atlas conflicts are structural, not an exceptional big species:
one atlas includes base-frame cells and the other is entirely inside the
resident base. Preparing an invisible Info page can already corrupt the
animation. Ancestor-title preparation also writes bank-1 glyph cells, so it
must not be eagerly run against an active resident dictionary.

These are physical VRAM collisions; extra ROM tables, CPU speed or an extra
VBlank wait cannot fix them.

### B Static Handoff

Keep A's resident animation on the initial Description page. Before entering
Info/Mov, acknowledge/cancel or finish that animation, atomically restore its
bank-0 static base, then relinquish the resident dictionary and give the normal
lower renderer its bank-1 workspace. Delay graphics-writing Info preparation
until that handoff is complete.

The portrait would remain static after the first tab handoff, including when
returning to Desc; it would not replay its cry. Audio still needs foreground
service until completion or final exit. Waiting for an authored animation to
finish would delay the requested tab; canceling immediately changes that
animation's behavior. Either policy needs explicit acceptance before building
this variant.

Reuse current lower-panel formatting, page data, bounded upload and atomic
publication helpers under a registration-local adapter. Ensure a New Entry
owner cannot be silently converted into a different owner by existing Info
request/cleanup code. Normal-speed work must keep audio runway and service
limits intact. Avoid copying the whole Selected service controller merely to
obtain lower-panel updates.

This is the smaller interactive implementation, but it is not full animation
parity with Selected. It avoids new frame streaming while making the lifecycle
handoff and static-base restoration explicit.

### B Continuous Animation

Use the existing Selected streaming frontpic producer for this registration
profile instead of keeping the full New Entry dictionary resident. Its two
frame slots, footprint/type buffers and lower glyph atlases are already designed
to coexist. Reuse the accepted precomputed renderer and metadata; do not add
new per-species tables or redo glyph architecture.

This is the better fit if opening Info/Mov must leave the frontpic and cry
running like Selected. It requires adapting the entry/reveal lifecycle to the
captured species, seeding stable species metadata, initializing the correct
owner fields, and validating the Selected producer plus lower-panel work at
the post-catch **normal CPU speed**. Do not switch the whole catch/naming path
to double speed just to make this integration easier.

The fixed-species controller must not require a fabricated list order or
viewport. Existing getters/footer handlers with those assumptions need narrow
shared primitives or registration-specific wrappers. B/End must not restore a
Listing, update its last position, enter Area or execute Start-menu fades.

Keep ordinary VBlank/STAT instruction budgets unchanged. Reuse existing
owner dispatch/publication interfaces rather than adding a new generic-owner
test. Any necessary changes to owner-local publication still require physical
timing verification from both battle sides and all existing Dex paths.

This path has greater integration/testing cost, but preserves the strongest
behavioral parity with Selected and avoids a new special-purpose lower renderer.
Potential retirement of the old registration animation code is a later audit,
not an assumed ROM0/ROMX refund in these planning estimates.

## RAM And Return Ownership

`wPokedexWRAM0Scratch` is a 1,300-byte overlay of overworld map blocks and the
battle menu/frontpic staging region. Its first 32 bytes include battle graphics
flags, saved palettes and producer metadata; the next 784 bytes are the staged
frontpic. Registration occurs inside battle, so the Start-menu assumption that
these bytes are disposable does not apply automatically.

A should avoid that overlap. B must preserve the still-live prefix/context and
prove whether the producer payload is already dead or must be reconstructed.
Do not restore an active flag referring to overwritten payload. Prefer keeping
small verified context in existing temporary owner storage and reconstructing
only genuinely disposable graphics over adding a 1,300-byte RAM backup.

The lower renderer's WRAMX bank-3 workspace overlays Battle Tower state.
Ordinary successful wild captures do not run inside an active Battle Tower
session, but that lifetime assumption must remain an explicit contract. New
Entry's bank-2 animation workspace and conversion/contest/discovery regions
also have separate owners; do not treat the whole bank as free scratch.

Preserve the captured stable species index and transient ID lock, current
party species/level, enemy moves/PP/DVs and the caller's menu/viewport/bank
state. Save/restore rather than persistently change the ordinary Dex's view,
selection or remembrance settings. Cancel queued lower jobs before return,
release any sprite locks, clear the type/mini OAM and restore fonts/palettes,
volume, clock and the original catch continuation exactly once.

Neither option requires save-format changes, additional seen flags or a
migration. The battle scratch issue is a runtime lifetime contract, not a
persistent storage requirement.

## Files And Cleanup Dependencies

| File | Expected responsibility |
| --- | --- |
| `engine/pokedex/new_pokedex_entry.asm` | Registration input/lifecycle and catch return; B adds its own fixed-species footer loop |
| `engine/pokedex/pokedex.asm` | Replace `_NewPokedexEntry` setup and retire its old shell only when the new path is complete |
| `engine/pokedex/pokedex_description.asm` | Reuse common shell/edge; narrow footer or explicit palette adapter if needed |
| `engine/pokedex/new_dex_entry_animation.asm` | A's two-cell modern page badge and bounded publication; B's chosen owner handoff |
| `engine/gfx/new_dex_entry_pics.asm` | Preserve resident loader for A/static B; continuous B uses the Selected preparation path |
| `engine/pokedex/pokedex_info.asm`, `pokedex_moves.asm`, `pokedex_ancestors.asm` | B lower-panel services and their existing metadata, without list/Area assumptions |
| `engine/pokedex/pokedex_detail.asm`, animation/policy/publication modules | B shares narrow primitives; no wholesale Selected entry/leave reuse |
| `engine/gfx/cgb_layouts.asm` | Explicit registration palette/attribute setup where reuse needs an adapter |
| `ram/wram.asm`, `ram/sram.asm` | Ownership/alias guards and only necessary context storage |
| Current New Entry/Dex tests and `docs/full_regression_suite.md` | Independent pixel, input, audio, timing and restoration expectations |

The old 126-byte `Pokedex_DrawDexEntryScreenBG` becomes unneeded once
registration uses the shared shell. Current production has not received the
archived cleanup, so 126 is the gross old shell span here. The archived
1,661-byte cleanup already includes three bytes of its unused Number string
and its 30-byte overwritten footer; do not count those 33 bytes twice when
rebasing cleanup after this feature.

`DisplayDexEntry` remains shared by Selected Description and can also remain
the common header/content producer for A/B. Its 224 bytes are not automatically
freed. A deliberately keeps the existing bank-0 footprint loader, so the old
19-byte footprint entry points are not newly dead simply because the screen
looks modern. The old right-edge routine also retains non-CGB callers unless
those compatibility paths are explicitly adapted.

Update the cleanup inventory after implementing the selected option. Do not
apply either archived pruning patch blindly to the resulting production.

## Qualification Before Promotion

No New Entry layout candidate exists yet. This scope ran the read-only linked
asset/VRAM audit and the current baseline's 20 New Entry contract tests, all
passing. Those checks do not qualify a future A/B implementation.

For either option, compare complete native displayed pixels with Selected
Description, including right-edge exposure, monotype clearing, both type
palettes, footprint background, category/name dimensions, P.1/P.2 and every
border join. Use independently captured reference expectations, not an oracle
generated by the proposed registration builder itself.

Re-run all-species/form resident or streaming frame mapping, all-species New
Entry normal-input/phase sweeps, authored animation timing and sampled/synth
cry checks. Include the existing short-hold Mewtwo and ACK-race Dusknoir controls,
and Bastiodon/Groudon/Spheal footprint collisions. Test before/after the final
animation event and while text or a lower page is queued.

B additionally needs every Info/evolution/ancestor and Moves category/page for
the fixed captured species, rapid repeated requests, all tab return pairs,
both portrait policies as applicable, and B/End from each pending/committed
state. Verify that no keypress navigates to another species and no lower
renderer marks moves seen or changes saved Dex preferences.

Use authentic captures with party space and full-party PC delivery, nickname
yes/no, already-caught/no-Dex bypass, contest and special supported catches.
Check captured species, level, moves/PP/DVs, caught data and acquisition hooks
after delivery. Continue through battle exit and normal overworld input/audio.

Run the complete [Full Regression Suite](full_regression_suite.md), including
all other Dex modes, all move animations from both sides, cries, persistence,
custom menus, PC/daycare and normal saving/loading. Recreate matching native
checkpoints after each link. Report timings in both milliseconds and display
frames for first complete registration reveal, description paging, B tab
changes and End/B return to naming/catch continuation. No generic ISR overhead
or outside-registration timing changes should be accepted without investigation.

## Recommendation

A is the lowest-cost foundation and keeps the already qualified resident
animation flow. If the interactive footer is preferred, choose its portrait
policy explicitly: static handoff is smaller but changes animation behavior;
continuous animation should use the existing streaming Selected architecture
and receive the broader normal-speed ownership qualification. Neither needs
new artwork or duplicate Info/Moves/ancestor metadata.
