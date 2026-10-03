# Pokedex VRAM and scratch-RAM plan

For the current execution/ownership contract and adaptation to other owners,
see [Selected animation scheduler](pokedex_animation_scheduler.md). The resource
allocation below includes the Description border, buffered OBJ type badges
and Info pages, including the 2026-10-03 heading/entry placement revision; the
animation slots remain unchanged.
See [Description UI](pokedex_description_ui.md) and
[Info pages](pokedex_info.md) for layout, palette ownership and exact budgets.

This document records the current Pokedex graphics ownership and the target
permanent allocation for the listing, description, search, search-results,
options, and Unown screens. The area map loads a temporary graphics overlay;
Info prepares bounded, double-buffered local glyphs and evolution icons on
demand without replacing the resident portrait or shared font.

The allocation deliberately does not cache neighboring frontpics. The
selected known or unseen static frontpic occupies one 49-tile bank-0 region.
Two bank-1 regions stream only the changed tiles required by the selected
known Pokemon's main and idle animation frames.

Each frontpic is stored as a small container. Its first LZ stream contains only
the native 5x5, 6x6, or 7x7 base pose; subsequent streams contain at most six
animation-dictionary tiles apiece. Normal frontpic consumers decode all streams
immediately. A Listing selection decodes only the base stream and pads it
directly into Dex WRAM0, reveals the new selection, and retains the tail address,
destination, and tile count as a cancellable background job. On each
otherwise-idle Listing update, the Dex can decompress one six-tile tail stream
and prepare its initial stage. Settled Selected playback instead chooses one
useful regular decode or upload action per hardware tick, with an optional
budget-admitted complete finishing upload. Input is checked first, so a new
selection cancels this work before another chunk begins.

The build tools generate one Dex-only stage plan for every visual animation
frame. Each record begins with its changed-tile count and dictionary high-water
mark, then directly names each changed 7x7 tilemap position and either its
padded base tile or animation-dictionary source. Base references come first;
dictionary references are ordered by source index so the producer can consume
each newly decompressed prefix immediately. This replaces runtime bitmask
expansion, coordinate reconstruction, a 256-entry lookup-table clear, a scan of
the available dictionary, and changed-tile deduplication and sorting.

A separate generated timeline expands the main and idle scripts into exact
visual durations. The first event's decode target covers the bounded startup
lead and the first three events' dictionary high-water marks. Every later
event targets the full dictionary extent, permitting early bounded decoding
during repeated poses; this is permission to progress, not a synchronous load.
The controller prepares a
hidden slot ahead of time and publishes its tilemap and attributes atomically
on an absolute `hVBlankCounter` deadline. Deadlines accumulate from the prior
deadline instead of the controller's completion time, so ordinary scheduling
jitter cannot stretch the animation. Structural asset validation checks the
timeline and source ranges; linked-code timing replay, not an optimistic
tiles-per-tick simulation, establishes runtime feasibility for tested cases.

Entering Description preserves any Listing prefetch and synchronously fills
only the remaining startup deficit: a complete first visual frame plus a fixed
96-tail-tile WRAM runway, capped by the end of the dictionary. This is not 96
additional resident VRAM tiles. The completed static
base remains visible while `PlayMonCry2` performs its synchronous setup. The
first animated pose is then queued for the next VBlank; that publication
anchors the generated timeline. Internal Description paging follows the same
base-only path and does not fall back to decoding the complete animation
dictionary up front.

## Current VRAM writes

### VRAM bank 0

| Region | Current owner | Tiles | Notes |
| --- | --- | ---: | --- |
| `vTiles0 $00-$36` | `PokedexSlowpokeLZ` | 55 | Shared Dex artwork and OBJ graphics; tile `$0f` is the list scroll thumb. |
| `vTiles0 $40` | List cursor | 1 | Four cursor corners reuse this tile with OBJ flips. |
| `vTiles0 $41` | Caught-ball marker | 1 | One OBJ per caught visible entry. |
| `vTiles0 $78-$7b` | Area-map player icon | 4 | Temporary area-map load. |
| `vTiles0 $7f` | Area-map nest icon | 1 | Temporary area-map load. |
| `vTiles1 $00-$7f` | Inverted font | 128 | Occupies the full signed-font region. |
| `vTiles1 $3a-$3f` | Listing scrollbar | 6 | Replaces signed characters `$ba-$bf`. |
| `vTiles1 $46-$49` | Unseen grid icon | 4 | Replaces signed characters `$c6-$c9`. |
| `vTiles1 $4a-$4f,$57-$5e,$64-$65` | Shifted Info headings | 16 | Otherwise blank font gaps; signed IDs `$ca-$cf,$d7-$de,$e4-$e5`. Both titles share the identical final partial `s` at `$cf`. |
| `vTiles2 $00-$30` | Selected static frontpic or unseen image | 49 | Area-map graphics temporarily overwrite `$00-$2f`. |
| `vTiles2 $31-$70` | Shared Pokedex UI | 64 | Loaded from `pokedex.2bpp`. |
| `vTiles2 $71-$7a` | Description border and page badge | 10 | Loaded once with permanent Dex graphics; the other screens retain their existing shell. |
| `vTiles2 $7b-$7e` | Info P.3/P.4 digits | 4 | Upper/lower tiles from the standalone editable page-number sheet. |
| `vTiles2 $54` and `$5b` | DMG Listing joined border | 2 | CGB uses the resident bank-1 copies instead. |
| `vTiles2 $62-$65` | Standalone-entry/DMG footprint | 4 | The normal CGB Dex uses the resident bank-1 footprint. |
| `vTiles2 $40-$5a` | DMG Unown glyphs and cursor | 27 | CGB uses the resident bank-1 copies instead. |

The footprint, joined-border, and Unown writes explain why those screens
currently need mode-specific graphics restoration even though their main UI
comes from the same 64-tile source.

### VRAM bank 1

| Region | Current owner | Tiles | Notes |
| --- | --- | ---: | --- |
| `vTiles3 $00-$27` | Center-column mini-sprites | 40 | Both 2x2 frames for five physical OBJ-icon rows: three visible plus one above and below. |
| `vTiles3 $28-$37` | Selected type badges | 16 | Two buffered sets of first/second type, four tiles each. |
| `vTiles3 $38-$57` | Info evolution mini-sprites | 32 | Two buffered sets of two animated eight-tile icons. |
| `vTiles3 $58-$59` | Info HP endpoint | 2 | One/two visible pixels for 100px/101px bars. |
| `vTiles4 $00-$30` | Animation buffer A | 49 | Streams only changed tiles; tilemap entries use `$80-$b0`. |
| `vTiles4 $31-$34` | Description footprint set A | 4 | Normal Listing resident footprint; signed IDs `$b1-$b4`. |
| `vTiles4 $35-$4f` | Unown glyphs and cursor | 27 | Loaded once when the Dex starts. |
| `vTiles4 $50-$51` | Listing joined border | 2 | Permanent copies outside the shared bank-0 UI range. |
| `vTiles4 $52-$79` | Left/right mini-sprite frame 1 | 40 | Second frame for ten 2x2 BG icons across the five physical cache rows. |
| `vTiles5 $00-$27` | Left/right mini-sprite frame 0; Info atlas B | 40 | Borrowed only while Selected Info owns the display; its writes invalidate the Listing ring before return. |
| `vTiles4 $7a-$7f` and `vTiles5 $28-$31,$64-$6b,$70-$7f` | Info atlas A | 40 | Six signed IDs `$fa-$ff`, plus 34 IDs in `$9000-$97ff`. |
| `vTiles5 $32` | Unown cursor background | 1 | Bank-1 copy of the dark-gray background tile. |
| `vTiles5 $33-$63` | Animation buffer B | 49 | Streams only changed tiles; tilemap entries use `$33-$63`. |
| `vTiles5 $6c-$6f` | Description footprint set B | 4 | Inactive-set preparation during internal paging. |

## Listing Residency And Info Borrowing

The `vTiles4` ranges above are physical offsets within the `$8800-$8fff`
region. With signed BG tile addressing they appear in tilemaps as `$80-$b0`,
`$b1-$b4`, `$b5-$cf`, `$d0-$d1`, and `$d2-$f9`, respectively, with the
VRAM-bank attribute set. Buffer B uses unsigned tile numbers `$33-$63` with
that same attribute.

The Listing uses a five-row ring: the three visible rows plus one fully
prepared row above and below. Each physical row retains both animation frames.
A scroll consumes the already-resident incoming row, reveals the complete
visible state, and then refills only the newly offscreen look-ahead/look-behind
row before accepting more input. Type badges moving to OBJ frees sixteen BG
cells, which join the former 24 free BG cells to make Info atlas A. Atlas B
temporarily borrows all 40 Listing frame-0 side-icon cells. It does not borrow
the other side-icon frames, center-column minis, title/font storage or portrait slots.
There is no unassigned bank-1 signed-BG tile with Info's allocations reserved.
Bank 1 has 38 free OBJ-only tiles (`vTiles3 $5a-$7f`); bank 0 `vTiles2` has one
free BG tile (`$7f`). Future mutually exclusive lower tabs should reuse Info's
atlases rather than budget new permanent BG storage. The CGB
footprint, Unown overlays, joined border, and cursor-background tile are
loaded into their permanent destinations when the Pokedex starts.

The cold-open prime fills all five physical icon rows while the LCD is off,
before their ownership tags can be reused by the Listing. Owned icons alternate
between their two frames every eight hardware frames; seen-but-uncaught icons
remain on frame 0. While the Listing is active, its dedicated VBlank handler
rewrites only the 24 resident side-column BG tile IDs and 12 center-column shadow
OAM tile IDs. This keeps the visible grid animating while synchronous frontpic
preparation runs. A render-changing selection locks OAM only for its final
reveal, synchronizes both columns to the hardware phase, installs the side-column
IDs after scanline 119, and releases the center-column OAM with the frontpic
palette. Scrolls claim the same ownership before changing grid metadata, consume
an already-resident row, and stage the complete frontpic, icon palette, grid map,
and OAM state while the old frame remains visible. The name is replaced after
scanline 15, the frontpic after scanline 63, and the nine 2x2 grid cells plus
their dependent palettes after scanline 119. The offscreen row is refilled only
after that complete new frame is visible.

Search, search results, and options currently load no unique tile graphics;
they use the shared font and Pokedex UI. The normal description path also
reuses the listing frontpic. Its four-tile footprint is prepared and loaded
while that known species is selected, so entering Description from Listing
does not reload the base portrait or footprint. Description additionally copies
one or two compact type badges into bank-1 OBJ storage using the existing
WRAM0 payload workspace, before animation production starts.

Internal paging alternates footprint/type sets A and B. Only the shared
portrait palette is masked to white; the outgoing icons and their hardware
palettes stay visible while the incoming icon graphics upload offscreen.
The existing owner publication switches tile IDs, attributes and palettes
together. Set A's cache tag is invalidated when preparing B, because it must
not falsely describe the incoming footprint. B-return repairs A under the
normal hidden Listing handoff; fresh Description entry resets to A. Type and
footprint buffering itself borrows no minisprite or animation-buffer tile.
Info additionally borrows the Listing's bank-1 BG frame-0 cells for its second
glyph atlas. It invalidates those cache-row tags before the normal hidden
Listing repair. The 2026-10-03 [Info return investigation](pokedex_info_return_evolution_investigation.md)
confirms that hiding the Listing Window does not hide the outgoing Info BG:
visible atlas-B references must be removed before those cache uploads. That
correction is proposed, not implemented. The owner reveal transfers incoming type/lower OAM and their
palettes together; outgoing types, minis and HP endpoints remain intact until
that handoff.

The area map remains an explicit temporary overlay. It loads 48 town-map
tiles to `vTiles2 $00-$2f` and five OBJ tiles to `vTiles0 $78-$7b/$7f`.
Returning from the area map must restore the current static frontpic when one
is required. The shared UI remains outside the overwritten range.

## WRAM0 workspace

`wPokedexWRAM0Scratch` overlays the 1,300-byte `wOverworldMapBlocks` union.
It is valid only during the Start-menu Pokedex session. `StartMenu_Pokedex`
calls `ReturnToMapFromSubmenu` before `CloseSubmenu`, rebuilding both map and
connection block data before the overworld is drawn again.

The Dex uses these fixed overlapping views:

| Workspace view | Offset | Bytes |
| --- | ---: | ---: |
| Changed-tile upload payload | `$000` | 320 maximum |
| Compact generated stage-plan record | `$310` | 98 maximum |
| Buffer A tilemap and attributes | `$39c` | 98 |
| Buffer B tilemap and attributes | `$3fe` | 98 |
| Changed source-tile indexes | `$460` | 49 |
| Active-order seen mask | `$4d0` | 47 currently |
| Persistent unused tail | `$4ff` | 20 currently |
| Description icon-buffer selector | `$513` | 1 existing union byte |

The first 848 bytes still overlap the selection-change staging layout: 784
bytes for the static frontpic and 64 bytes for its footprint. That is
intentional: both are committed before a new animation producer is marked
pending.

Listing scrolls temporarily use the animation-map portion of this workspace
while that producer is cancelled. The next offscreen center icon row occupies
128 bytes at `$350`, its side-icon frame 0 occupies 128 bytes at `$3d0`, and
its side-icon frame 1 occupies 128 bytes at `$450`. The Listing keeps the
Pack's cache ownership and post-reveal refill model, but uses a Dex-specific
visible commit: only 72 tilemap/attribute bytes, BG palettes 1-7, and OBJ
palettes 2-4 are changed. Three exact-length eight-tile HBlank DMA transfers
then refill the newly vacated physical cache row. The completed graphics remain
resident in the five-row VRAM ring; the WRAM staging bytes are immediately
reusable by animation.

The active-order seen mask starts after that final icon-row staging buffer, so
it remains valid across Listing movement and Selected-page animation. It uses
one bit per position in the current Dex ordering and is rebuilt whenever that
ordering changes. Its maximum 64-byte size under the current 512-species flag
capacity also fits in the 68-byte persistent tail.
The icon selector uses the last byte of the 1,300-byte union, outside even
the maximum 64-byte seen mask and all temporary grid staging. Assembly
assertions enforce those boundaries. Zero selects A; one selects B. This
is an alias within existing storage, not a new WRAM0 allocation or padding byte.

Other useful maximum sizes include:

| Workspace view | Bytes |
| --- | ---: |
| Padded 7x7 frontpic | 784 |
| Frontpic plus four 2bpp footprint tiles | 848 |
| Frontpic, footprint, and packed 7x7 tile/attribute maps | 946 |
| Native 20x18 tilemap and attrmap | 720 |
| HDMA-padded 32x18 tilemap and attrmap | 1152 |
| Nine 2x2 mini-sprites | 576 |
| Three rows of three 2x2 mini-sprites | 576 |

The producer seeds a slot with the base 7x7 map, copies at most 98 bytes of plan
data into WRAM0, and applies those direct position/source pairs. Animation
sources are already ordered by dictionary index, so no runtime lookup table,
deduplication, or sort is needed. Duplicate source references deliberately keep
separate slot tiles; across all 1,722 current frames this adds only 37 tile
copies among 20,149 changed cells and avoids rebuilding a mapping structure
every frame. Services select WRAMX bank 6 for dictionary reads/decompression,
decode at most one six-tile stream per regular decode action, and gather a
ready source prefix for each upload. The two animation tilemaps and bounded upload
payload stay in WRAM0, avoiding per-tile WRAM bank changes. VRAM uploads resume
from a saved offset in chunks of at most 20 tiles. A separately admitted
finishing action may complete one ready remainder in that owner iteration. Each
physical animation slot retains its completed frame ID after release, allowing
an exact later match to become tilemap-only. An underrun deliberately installs
its incomplete slot and increments its reserved diagnostic counter instead of
concealing the missed deadline behind the previous complete frame. The two
diagnostic counter bytes remain unlabeled padding after instrumentation
cleanup; current miss detection is a host observer/breakpoint at
`Pokedex_AnimationMiss`.

Twenty-six bytes in `wPokedexData` hold timeline, playback, deadline, slot,
residency, reserved diagnostic padding, and background-dictionary state. This is one
byte smaller than the prior controller and returns that byte to the union's
reserved padding; no new WRAM, SRAM, or HRAM is allocated. The temporary
136-byte scheduler trace and its runtime writes have been removed. Three
production scheduler bytes at `$c758-$c75a` remain for loop tick, last-work
tick and control flags. Their existing control bit 2 now guards portrait DMA
register ownership against lower-page publication. The Listing cache remains
in the same union, and subsequent RAM symbols retain their addresses. Current
telemetry runs in the host-side SameBoy observer, not in cartridge RAM.

Info extends the mutually exclusive bank-3 Battle Tower/Dex overlay by 1,686
bytes, including alignment and the committed-page B-return records. It ends
at `$db38`, leaving 200 bytes before the asserted `$dc00`
boundary. Its 640-byte glyph buffer, 256-byte mini buffer, 32-byte OAM buffer,
80-byte glyph pointers, 53-byte state and 611-byte records/visible flag do not enlarge the overall union or
use new WRAM0/HRAM. See [Info's exact workspace and budget](pokedex_info.md#ram-and-rom-budget).

The frame-plan ROM cost is 47,186 bytes of generated payload plus a 1,197-byte
far-pointer table. The payload remains isolated in banks `$a1`-`$a3` (decimal
161-163), leaving 654, 656, and 656 bytes free. The generated timelines occupy
their own bank `$a5` (decimal 165): 12,712 bytes of events plus 798 bytes of
two-byte pointers, with the 97-byte fixed-bank reader also resident there and
2,777 bytes free. These are the accepted 2026-09-21 link's totals, including
the 13-byte increase from Seviper's finite repeat correction. Bank `$a0`
(decimal 160), which owns the runtime, frame-plan pointer table and 80 global
finishing-bound bytes, retains 2,979 free bytes in that link. The
obsolete compact micro-schedule and its reader are removed. The formerly empty
`$a6` bank now holds Info code/tables (9,951 bytes), and `$a7` holds its local
glyphs (7,728 bytes). The totals above describe the historical scheduler
checkpoint, not current whole-cart use; see Info's resource table for the
current link and the scheduler document for its historical resource bill.
