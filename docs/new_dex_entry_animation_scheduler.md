# New Dex Entry Animation Scheduler

Living implementation reference, 2026-09-21. This describes the linked game,
not the earlier private preflight prototype. Update it when the owner contract,
resident layout, timeline format, linked costs, or validation results change.

Companions: [test procedure and build identity](dex_new_entry_testing.md),
[Selected Description scheduler](pokedex_animation_scheduler.md),
[sampled cries](sampled_cries.md), [host tools](dex_timing_model.md).

## Scope

This owner runs the post-catch **New Dex Entry** page. It does not migrate the
Stats Screen, battle frontpics, or the Start-menu Selected Description owner.
It reuses the same generated frontpic frame plans and exact animation timelines
as Selected Description, but **keeps the full dictionary resident in VRAM**.
There is no two-slot frame-tile producer, dictionary streaming during playback,
or speculative Listing warming on this screen.

The target is each authored event's hardware display interval. Work completion
does not advance time, and late work does not extend the next authored hold.
Normal-speed CGB is the tested configuration. Passing this owner's tests is not
a claim about every owner, emulator, input phase, or future asset.

No preparation hook was added to ball shakes, the caught jingle, experience,
level-up, or PC-storage logic. Full dictionary loading is still part of the
registration page's setup. The larger, screen-local upload batches reduce that
setup's transfer waits without adding work to the catch animation.

## Source Map

| File | Responsibility |
| --- | --- |
| `engine/pokedex/new_pokedex_entry.asm` | Page lifecycle, text-page input and animation step/cancel calls |
| `engine/pokedex/pokedex.asm`, `_NewPokedexEntry` | Existing registration layout/setup, now calls the local frontpic loader |
| `engine/gfx/new_dex_entry_pics.asm` | Full decompression and resident base/tail layout; registration only |
| `engine/pokedex/new_dex_entry_animation.asm` | Timeline reader, map producer, VBlank publisher, owner cleanup, batch uploader and page-2-only renderer |
| `home/new_dex_entry.asm` | Three fixed-bank bridges: quiet VBlank dispatch, DelayFrame service, tile upload |
| `home/vblank.asm`, `home/delay.asm` | Existing hardware-clock and wait/audio integration points |
| `ram/wram.asm`, `ram/sram.asm` | Aliases over existing animation and graphics scratch, not new allocations |

The owner and uploader are in the existing timeline bank `$a5`; the loader is
in graphics bank `$14`, alongside `_PrepareFrontpic`. Existing timeline and
frame-plan payloads are unchanged. No new ROMX bank or per-species table was
added. Start and cancellation use ordinary foreground `farcall`; they do not
have separate ROM0 wrappers.

## Lifecycle

1. Successful capture proceeds through its normal experience/level-up work.
   The game opens registration only when the species was not previously caught.
2. `_NewPokedexEntry` loads the existing shell and calls
   `NewDexEntry_LoadAnimatedFrontpic`. It fully decompresses the current
   frontpic dictionary and uploads the padded base and animation tail.
3. The existing animation initialization provides the species and clears its
   animation structure. The page's first animation step selects that structure
   in WRAMX 2, obtains the shared frame-plan/timeline pointers, and prepares the
   first complete 7x7 map.
4. `PlayMonCry2` starts the normal synthesized or sampled cry. Sampled startup
   still fills **32 blocks**, not a new screen-specific amount.
5. Only after preparation and cry startup, the owner arms its first deadline
   for `hVBlankCounter + 1`. It saves `hVBlank`/`hOAMUpdate`, selects owner `$88`,
   locks normal OAM copying, and initially disables automatic BG-map updates.
6. VBlank increments the shared display counter. At the deadline it publishes
   the complete prepared map. First/final events also publish frontpic attrs.
7. After VBlank, `DelayFrame` first services sampled audio, then acknowledges
   the published map in the software backing map and prepares the next event.
   This also happens inside nested waits such as description-page refreshes.
   The New Entry-only page-2 renderer also provides three explicit foreground
   map-service boundaries; it does not redraw unchanged page-1/header content.
8. The timeline's final event restores the base map/bank. Foreground cleanup
   restores the previous owner/OAM state and clears `wFrameCounter`, retaining
   the owner briefly if a complete description is still queued for publication.
9. Leaving early calls cancellation in ROMX. It restores the owner and clears
   animation activity before the existing page/battle return path continues.
   It does not invent a new audio-stop policy.

The screen's full menu sequence includes its authored main animation, the
existing 18-interval transition hold, idle animation, and final base restore.
Dusknoir's main portion is 107 intervals; its complete menu sequence is **174**.
Do not compare the full sequence against the main-only number.

## State And Ownership

All state below reuses the legacy animation owner in WRAMX 2. These aliases are
not globally safe while another screen owns the same union.

| Address | Alias / purpose |
| --- | --- |
| `$d000-$d061` | `wNewDexEntryAnimPairs`: up to 49 `(position, source)` pairs in `wTempTilemap` |
| `$d168` | Flags, alias of `wPokeAnimSceneIndex` |
| `$d169-$d16a` | Next timeline pointer |
| `$d16b` | Existing `wPokeAnimSpecies` |
| `$d16e` | Native base-tile count: 25, 36 or 49 |
| `$d17d` | Publication count |
| `$d17e` | Miss count, instrumentation |
| `$d17f-$d180` | Saved VBlank owner and OAM lock |
| `$d181-$d183` | Deadline, prepared frame ID, duration |
| `$d184` | Existing frame-plan bank |
| `$d185` | Miss reason, instrumentation |
| `$d18f-$d190` | Existing frame-plan address |
| `$d191-$d1c1` | Complete 49-cell map, alias of `wPokeAnimFrameTiles` |

Flags: bit 0 `ACTIVE`, 1 `READY`, 2 `FINISH`, 3 `FIRST`, 4 `ACK`,
5 `MISSED` (instrumentation latch, once per missed deadline),
6 `TEXT` (complete description waiting for VRAM publication).

`READY` is written only after all 49 cells are valid. VBlank does not read a
partly built map. `ACK` means the hardware map has been published but foreground
has not yet synchronized its software backing map. The producer must acknowledge
that published map before reusing the buffer for the next event.

### Why The ACK Barrier Matters

A can draw description page 2 while the animation continues. A VBlank may
publish a new frontpic during that text work, before the next `DelayFrame`.
Allowing ordinary `UpdateBGMap` then would copy the **old software frontpic**
over the new hardware frame. That corruption need not cause a deadline miss.

While `ACK` is set, the new VBlank path suppresses the ordinary graphics pass.
Foreground copies all seven backing rows, synchronizes first/final attrs, and
only then clears `ACK`. Partial backing-map copies therefore cannot become
visible. Subsequent description refreshes use the correct published picture.
The deadline still advances at publication, not when this acknowledgement ends.

The service checks ACK again at `.build`, using the **same loaded flags byte**
as its READY test. If publication occurred since the earlier ACK check, it
branches back to `.ack` before reusing the map. If publication interrupts after
this second snapshot, that snapshot still has READY set, so foreground returns
without overwriting the map and acknowledges it on the next service call.
No interrupt masking or additional state is needed. Separate flag reads without
this recheck can lose the published map, even with no deadline miss; see the
[recorded Dusknoir race](new_dex_entry_regression_results.md#ack-check-race).

## Description Paging

`NewPokedexEntry` calls `NewDexEntry_DisplayPage2`, not shared `DisplayDexEntry`,
when A advances the description. The new routine is local to this screen:

1. Service sampled audio once, then acknowledge/prepare the animation map.
2. Disable automatic BG updates while drawing and resolve the existing entry
   pointer. Scan past the category, four dimension bytes, and page-1 text without
   rendering any of them.
3. Service the animation again, preserving the text pointer and bank.
4. Clear the five description rows, write the page-2 number, and render page 2
   with existing `PlaceFarString`.
5. Service the animation again, then set `TEXT` only after every source cell is
   complete. VBlank sees either no request or a complete immutable description.
6. Wait through `DelayFrame` until the publisher clears `TEXT`. These waits
   still service audio and animation. The old fixed four-interval `WaitBGMap`
   call is removed only from this page-2 path; shared `WaitBGMap` is unchanged.
7. Restore ordinary BG updates and return to the page-input loop.

The local animation helper preserves AF/BC/DE/HL and checks the New Entry owner
before touching its state. Inner boundaries do not refill audio; normal
`DelayFrame` refill opportunities remain. The publisher continues on the exact
hardware-clock timeline throughout this work. The ACK barrier ensures ordinary
BG refresh never copies a stale picture over a newer publication.

The unchanged name, number, category, dimensions, divider and frontpic are not
redrawn. Shared `DisplayDexEntry` and Selected Description behavior are unchanged.
This removes the long producer gap caused by drawing page 1 merely to erase it
again. It neither moves initial page setup nor increases dictionary/audio prefill.

The description publisher copies exactly **91 disjoint cells**: columns 2-19
of rows 10-14, plus the page number at (2,9). It does not copy the frontpic,
header, dimensions, border or attributes. Animation publication has first claim
on VBlank; afterward, or on an interval without a due picture, the description
helper rechecks live LY and admits only lines 144-148. All text stores finish
within that VBlank or none occur. `TEXT` clears only after the last store.
An outstanding picture `ACK` does not block this disjoint copy, but ordinary
BG copying remains blocked while ACK or the description copy consumes the pass.

If the final animation map has been published but text is pending, foreground
retains its final ACK/owner until that copy completes. If A is pressed after the
animation has already ended, the renderer borrows owner `$88` with the same
saved-owner/OAM fields, commits text, and restores it without starting another
animation. Cancellation still releases the owner and all flags.

This fixes `NEWDEX-UI-01`: a fixed wait had counted elapsed display intervals
while animation priority deferred ordinary BG thirds. For all eleven formerly
failing Mewtwo timings, the complete description now appears three intervals
after A, versus nine to eleven previously, with no mixed text frames. Host
observations use actual input and displayed pixels, not the later input-wait
entry; extending a wait therefore cannot disguise a slow or partial refresh.

## Frame Construction

The producer reads an exact `(frame, duration)` event from the shared timeline.
It skips that event's high-water byte because all dictionary tiles are already
resident; Selected's streaming owner still needs that metadata.

Each output begins with the padded column-major base map. Precomputed frame
pairs then replace only changed cells. Position bit 7 identifies an already
padded base-tile reference. Other sources map into the resident animation tail:

```text
resident_tile = source_tile - native_base_count + 49
if resident_tile >= $7f: resident_tile += 1
```

Tile `$7f` remains blank. A zero-pair event bypasses `FarCopyBytes`; its zero
count must never reach a copy loop that interprets it as a wraparound length.
No frame-bitmask scanning, animation script interpretation, pixel decompression,
or per-frame tile upload is needed during playback. Only the 49-cell map changes.

## VBlank Publication

`VBlank_Normal` already tests the quiet-owner high bit before writing viewport
registers. That branch now routes through `NewDexEntry_VBlankDispatch`:

- `$88`: switch directly to the resident owner, publish or retain its map, then
  continue at the normal graphics pass or skip to normal VBlank bookkeeping.
- Other quiet owners: continue the existing normal path; they do not touch this
  owner's WRAMX state.
- Non-quiet owners: do not execute the new dispatch helper.

The interrupt bridge uses explicit bank switching, not `FarCall`'s shared
scratch. Outer VBlank preserves CPU registers; the publisher saves/restores
SVBK and VBK. The foreground DelayFrame bridge separately preserves AF/BC/DE/HL
and its caller's ROM bank. Preserving AF matters outside registration too.

The initial integration checked the owner before `UpdateBGMapBuffer` on every
VBlank. Its extra 36 T-cycles made the normal boot 1bpp loader arrive at LY 146
every time and indefinitely defer its request. The corrected quiet-owner branch
adds no cycles to that ordinary pre-graphics path, has the same instruction
footprint, and passes fresh-boot testing. The linked gate contract checks the
original 124 T-cycles through viewport writes (32 T to the taken quiet branch).
Do not restore an unconditional owner
check there without remeasuring the existing 1bpp/2bpp admission windows.

At a deadline the publisher requires `READY` and a safe live LY. It copies the
map in VRAM bank 0; first/final events also copy 49 attrs in bank 1. It then
increments the publication count, clears `READY`, sets `ACK`, and advances
`deadline += duration` **inside the same interrupt**. The eight-bit deadline
comparison is valid for the current events (maximum hold 65, below 128).

Both VRAM helpers are fully unrolled across the seven rows. The map helper uses
`inc e` within each row and immediate low-byte destinations between rows; the
attribute helper uses `LD [HL+], A` and an immediate low byte between rows.
All cells are inside `$9821-$98e7`, protected by a link-time high-byte assertion.
Each helper has one fixed-destination caller. The attribute helper may clobber
HL because the source map has already been copied, and the publisher needs
neither helper's final pointer value. Outer VBlank still restores caller CPU
registers. Backing-map helpers are unchanged and use full `inc de`.

### Admission Bounds

These costs come from the actual linked SM83 instructions, with a frozen-LY
unit fixture. SameBoy replay separately checks real interrupt/PPU timing.
All figures are normal-speed T-cycles, not instruction counts.

| Publication | Admit only at LY | Final VRAM store finishes after LY read | Minimum available | Margin |
| --- | --- | ---: | ---: | ---: |
| Map only | 144-149 | 1,108 T | 1,824 T | 716 T |
| First map + attrs | 144-149 | 1,704 T | 1,824 T | 120 T |
| Final map + attrs | 144-149 | 1,708 T | 1,824 T | 116 T |
| Complete description + page number | 144-148 | 1,984 T | 2,280 T | 296 T |

With no pending description, the map/first/final paths take
1,444/2,004/2,008 T after their LY read, including bookkeeping and return.
Their final VRAM stores and admission bounds are unchanged by the additional
description helper check. When text is pending it has its own later live-LY
check; the two budgets are not assumed to fit together automatically.
The margin above concerns the last VRAM
write, conservatively including its store instruction. It is not the time
available to add unrelated work. VBlank has interrupts disabled; admission
checks the actual line after any interrupt-entry delay. A sampled-cry timer ISR
can already be running when VBlank begins; this delayed entry exposed the old
first-publication gate. Faster copies now admit that measured phase safely.
Do not merely relax a cutoff without remeasuring its linked last-write cost.

The eight-species catch suite completes publication bookkeeping in mode 1 at
LY 152 or earlier. The synthetic phase suite also reaches physical line 153,
where LY can already read zero while mode 1 is still active. The host accepts
that hardware behavior; it does not accept visible-line-zero modes 0/2/3.

A missed deadline is diagnostic, not an invitation to silently stretch the
timeline. Last complete graphics remain visible; recovery can publish a ready
late event, but the miss remains recorded. Break at the miss before interpreting
the later visual recovery as success.

## Resident VRAM And Startup Upload

The existing registration shell/font layout is retained:

- Bank 0 `$9000-$930f`: padded static base (49 tiles), used on final restore.
- Bank 1 `$9000-$930f`: the same padded base for resident animated maps.
- Bank 1 `$9310-$97ef`: first 78 tail tiles.
- Bank 1 `$97f0-$97ff`: reserved blank tile `$7f`.
- Bank 1 `$8800` onward: remaining tail tiles, using signed BG tile addressing.

The current largest mapped tile is `$f7`, leaving bank-1 `$8f80-$8fff` (8 tiles)
outside this dictionary range. A four-tile BG type icon could fit there under
this owner's contract, but this change does not allocate or render one. Shared
font/shell changes and future larger assets still need an ownership audit.

`NewDexEntry_Get2bpp`/`NewDexEntry_UploadTiles` are local to registration. The
generic `GetAnimatedFrontpic`, battle paths and Stats loaders are unchanged.
The uploader queues at most **32 tiles per VBlank GDMA** and waits through the
existing `WaitDMATransfer`/`DelayFrame` path, retaining audio/input service.
It does not transfer the whole large dictionary in one interrupt.

The padded base begins at SRAM `$a001`, which is not DMA-aligned. Each base
batch is copied into aligned `sNewDexEntryUploadBuffer` at `$00:$a320-$a51f`
before queueing. This is a new alias inside existing temporary graphics SRAM,
not persistent save storage or added SRAM size. The WRAM tail is already aligned.
The loader restores VBK/SVBK and closes SRAM before returning.

A single remaining tile falls back to `Get2bpp`: queued DMA's zero length byte
is the engine's idle sentinel. The loader splits around reserved tile `$7f` and
the signed-address wrap explicitly. It does not overwrite the blank tile.

## Sampled Audio

The codec, pair lookup, 32-block synchronous startup, eight-block refill and
timer playback code are unchanged. `DelayFrame` calls the existing audio
service **before** the registration map service. Nested description-page waits
therefore retain both refill and animation production opportunities.
The page-2-only renderer adds one audio service at its entry, but none at its
two inner map-service boundaries. This avoids unnecessary consecutive decoding
work while retaining the measured refill headroom.

The audio miss breakpoint is the timer's cache-empty branch with nonzero
remaining playback, not the common stop function. Natural completion and early
page exit are different events. The capture suite checks natural completion
for all five sampled species in the eight-species set, including after early
exit; this does not establish every rapid-transition audio policy elsewhere.

## Resource Cost

Compared with the accepted capture-fixture link:

| Resource | Added / remaining |
| --- | --- |
| ROM0 | **74 bytes**: 27 VBlank routing, 29 DelayFrame service, 18 uploader bridge |
| ROM0 free | **582 bytes total**, 506 contiguous at the end |
| ROMX | **1,682 bytes net**; 1,547-byte owner/uploader/page renderer + 153-byte local loader, less replaced call-site code |
| New banks / metadata | None; existing `$a5` and `$14` have room |
| WRAM0 / WRAMX / HRAM | **0 additional bytes**; existing legacy animation scratch reused |
| SRAM | **0 additional bytes**; 512-byte staging alias within existing scratch union |

The page-2 correction adds exactly **100 ROMX bytes** relative to the initial
resident implementation: 96 for the redraw/helper and four for the inline ACK
recheck. It adds no ROM0 or RAM allocation and leaves 1,786 trailing free bytes
in bank `$a5` in that historical link. The subsequent publication-copy correction
adds **148 ROMX bytes**, leaving **1,638 bytes** in that historical bank `$a5`.
The replacement helpers add 154 bytes and the common cutoff removes six bytes.
Existing ROM0 address operands relink to shifted ROMX labels; ROM0 code size is
unchanged. Temporary register saves use the existing stack.

The acknowledged description publisher adds another **405 net ROMX bytes**:
408 in bank `$a5`, minus the three-byte page-2 `WaitBGMap` call in bank `$3e`.
Bank `$a5` now has **1,230 trailing bytes free**. It reuses bit 6 of the existing
flags byte; no queue buffer, extra flag byte, ROM0 bridge or graphics allocation
is added. Its unrolled copy trades ROMX for bounded interrupt time.

The two proposed ROM0 start/cancel wrappers are omitted. The implementation
is reusable as a pattern, not a screen-independent API promise. A future Stats
redesign must choose its own tile ownership, resident versus streaming policy,
map location, backing-map/input rules, audio gaps and proven admission budget.
It can reuse metadata and potentially the upload/dispatch primitives once those
contracts are explicit. Stats work is deliberately deferred.

## Validation And Instrumentation

Maintained host code lives in `tools/dex_timing/new_entry.py` and its SameBoy
probes. It validates frozen catch fixture identities, resumes real catch flows,
derives a registration-entry state, and tests uninterrupted playback, A during
playback, and A then B for early exit. Original saves/states remain read-only.

The ordinary replay observes actual linked execution, physical VRAM maps and rendered
frontpic pixels each display frame. It checks exact event intervals, audio
block accounting, software/hardware UI backing consistency and cleanup. It also
checks the old/new description rectangle and rendered text on every display,
with input-anchored latency independent of the page-wait return time.
It does not inject producer state or substitute a later observation to force
the timing to match. Cross-build fixture guards reject incompatible live
addresses, sound pointers, catch code or assets; arbitrary old states are unsafe.

The current eight catches and 24 registration variants pass, with **2,356**
checked display frames. Four catches include level-up/stat prompts; Vibrava and
Mewtwo go to the PC. Structural checks cover **399 assets / 2,121 pictures**.
The original Master Ball opening is restored. Its previously failing Dusknoir
entry now publishes on time and meets the full 174-interval sequence.

`tools/dex_timing/new_entry_sweep.py` and `probes/new_entry_fixture.c` extend the
same observer to a species-by-input-timing matrix. Original checkpoints remain
read-only; twelve additional species use explicitly generated entry fixtures
with real runtime-ID allocation, not fabricated catch-flow outcomes. The current
20-species suite checks **8,570 cases / 1,207,645 displayed frontpics**. All 7,104
sampled-cry runs finish without underrun. All 5,571 complete animation sequences
meet each authored deadline; early cancellation validates the expected prefix
instead. The checked 3,260 returns restore caller/owner state, without locks.
All cases pass, including the eleven formerly failing Mewtwo text timings.
There are 6,492 description advances and 579,345 checked description displays,
with no mixed or reverted text. Shorter acknowledgement waits allow some exit
inputs sooner; that changes completion/return counts, not authored deadlines.
All twenty untouched baselines retain the previous first-publication interval,
publication count and total authored duration.

The user repeated the preceding picture-publication fix's focused manual cases
with varied inputs and reported no New Dex Entry animation or sampled-cry miss
hits. On 2026-09-21, the user also accepted the description publisher, noting a
perceived one- or two-frame text-before-page-number offset. This is an unmeasured
manual observation, not reproduced by the automated fixtures, and is retained
as an accepted presentation caveat rather than a pending change. Ordinary Route
29/30 encounters and the original Master Ball remain restored; battle-cry
investigation remains deferred.

Fifty-six unit/contract tests include a flag-read interruption regression,
description completion/atomicity checks, and the local helper's
register/owner/audio-service contract. The interruption test
injects publication at the two snapshot boundaries; it is a control-flow fixture,
not a hardware-timing substitute. The full-core sweep supplies timing coverage.

`tools/dex_timing/new_entry_phase_sweep.py` separately varies only the initial
TIMA write in the headless core. This is explicitly synthetic instrumentation,
not part of normal playback, and never writes the ROM or original save states.
It leaves TMA and subsequent periods unchanged. With `--all-input-modes`,
**9,600 phase/input cases** for 16 sampled species pass with **1,122,800 display
checks**. The first overflow offset is swept in 64-T steps across one period;
every species completes, advances description and exits early at every offset.
This is not exhaustive coverage of
every CPU-cycle phase or every arbitrary input sequence. A no-op injection is
checked against the unmodified trace, including timestamps.

Display spacing is checked at the exact PPU boundary, subtracting SameBoy's
unconsumed display-batch ticks from its CPU callback time. The read-only field
fixes two Yanmega observer assertions without changing any old execution events
or widening the tolerance. Both the full input and phase suites were rerun with
zero allowed PPU-boundary drift; see the regression report for the control.

See the [measured regression report](new_dex_entry_regression_results.md) for the
original failures, race trace, private trials and final integrated results.
The suite is not all-species New Entry playback or all possible hardware/input
phases. Twelve fixtures are generated entry states, not additional real catches.
The earlier wholly green sweep used the standard-ball opening override; it
remains historical evidence, not a replacement for current-link results. Fresh
boot, nine Selected cold entries, and 27 settled page-2 pixel comparisons were
also recorded on that earlier integration. Passing registration does not close
the separate deferred battle cry issue.

`NewDexEntryAnimationMiss` increments a latched diagnostic count. Reasons:
1 = map not ready at deadline; 2 = deadline already passed; 3 = unsafe live
publication window. The count/reason/latch use existing owner bytes and are
explicitly instrumentation. They can be removed later without allocating or
moving RAM; remeasure code and update breakpoints after removal.

See [the current manual suite](dex_new_entry_testing.md#current-implementation-test)
for exact build-bound breakpoint commands, capture fields and test order.
Generated ROMs, reports, cores, states, images and raw traces stay under ignored
`build/`; the reusable tools and this contract belong in the repository.
