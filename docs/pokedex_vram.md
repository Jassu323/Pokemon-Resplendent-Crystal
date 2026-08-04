# Pokedex VRAM and scratch-RAM plan

This document records the current Pokedex graphics ownership and the target
permanent allocation for the listing, description, search, search-results,
options, and Unown screens. The area map is the only normal Pokedex screen
allowed to load graphics on demand.

The allocation deliberately does not cache neighboring frontpics. The
selected known or unseen static frontpic occupies one 49-tile bank-0 region.
Two bank-1 regions stream only the changed tiles required by the selected
known Pokemon's main and idle animation frames.

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
| `vTiles2 $00-$30` | Selected static frontpic or unseen image | 49 | Area-map graphics temporarily overwrite `$00-$2f`. |
| `vTiles2 $31-$70` | Shared Pokedex UI | 64 | Loaded from `pokedex.2bpp`. |
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
| `vTiles4 $00-$30` | Animation buffer A | 49 | Streams only changed tiles; tilemap entries use `$80-$b0`. |
| `vTiles4 $31-$34` | Selected footprint | 4 | Prepared alongside the current known selection. |
| `vTiles4 $35-$4f` | Unown glyphs and cursor | 27 | Loaded once when the Dex starts. |
| `vTiles4 $50-$51` | Listing joined border | 2 | Permanent copies outside the shared bank-0 UI range. |
| `vTiles4 $52-$79` | Left/right mini-sprite frame 1 | 40 | Second frame for ten 2x2 BG icons across the five physical cache rows. |
| `vTiles5 $00-$27` | Left/right mini-sprite frame 0 | 40 | First frame for ten 2x2 BG icons across the five physical cache rows. |
| `vTiles5 $32` | Unown cursor background | 1 | Bank-1 copy of the dark-gray background tile. |
| `vTiles5 $33-$63` | Animation buffer B | 49 | Streams only changed tiles; tilemap entries use `$33-$63`. |

## Target permanent allocation

The ranges below reserve all known listing, description, search, and Unown
requirements without assigning VRAM for neighboring known frontpics.

| Region | Target owner | Tiles |
| --- | --- | ---: |
| `vTiles0 $00-$36` | Shared Dex artwork and OBJ graphics | 55 |
| `vTiles0 $40-$41` | Listing cursor and caught ball | 2 |
| `vTiles1 $00-$7f` | Inverted font plus the existing scrollbar/grid-icon substitutions | 128 |
| `vTiles2 $00-$30` | Current known frontpic or unseen image | 49 |
| `vTiles2 $31-$70` | Shared Pokedex UI | 64 |
| `vTiles3 $00-$27` | Both frames for five cached center-column mini-sprite rows | 40 |
| `vTiles4 $00-$30` | Animation buffer A | 49 |
| `vTiles4 $31-$34` | Preloaded selected footprint | 4 |
| `vTiles4 $35-$4f` | Permanent Unown glyphs and cursor | 27 |
| `vTiles4 $50-$51` | Permanent Listing joined border | 2 |
| `vTiles4 $52-$79` | Frame 1 for five cached left/right mini-sprite rows | 40 |
| `vTiles5 $00-$27` | Frame 0 for five cached left/right mini-sprite rows | 40 |
| `vTiles5 $32` | Unown cursor background | 1 |
| `vTiles5 $33-$63` | Animation buffer B | 49 |

The `vTiles4` ranges above are physical offsets within the `$8800-$8fff`
region. With signed BG tile addressing they appear in tilemaps as `$80-$b0`,
`$b1-$b4`, `$b5-$cf`, `$d0-$d1`, and `$d2-$f9`, respectively, with the
VRAM-bank attribute set. Buffer B uses unsigned tile numbers `$33-$63` with
that same attribute.

The Listing uses a five-row ring: the three visible rows plus one fully
prepared row above and below. Each physical row retains both animation frames.
A scroll consumes the already-resident incoming row, reveals the complete
visible state, and then refills only the newly offscreen look-ahead/look-behind
row before accepting more input. This leaves 132 tiles free in VRAM bank 1:
88 in `vTiles3`, 6 in `vTiles4`, and 38 in `vTiles5`. The CGB
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
does not load species graphics.

The area map remains an explicit temporary overlay. It loads 48 town-map
tiles to `vTiles2 $00-$2f` and five OBJ tiles to `vTiles0 $78-$7b/$7f`.
Returning from the area map must restore the current static frontpic when one
is required. The shared UI remains outside the overwritten range.

## WRAM0 workspace

`wPokedexWRAM0Scratch` overlays the 1,300-byte `wOverworldMapBlocks` union.
It is valid only during the Start-menu Pokedex session. `StartMenu_Pokedex`
calls `ReturnToMapFromSubmenu` before `CloseSubmenu`, rebuilding both map and
connection block data before the overworld is drawn again.

The animated-frontpic path uses these fixed overlapping views:

| Workspace view | Offset | Bytes |
| --- | ---: | ---: |
| Changed-tile payload | `$000` | 784 |
| Logical 7x7 map with 20-byte rows | `$310` | 140 |
| Buffer A tilemap and attributes | `$39c` | 98 |
| Buffer B tilemap and attributes | `$3fe` | 98 |
| Changed source-tile indexes | `$460` | 49 |
| Unused tail | `$491` | 131 |

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

The producer batches a frame's source indexes in a separate 49-byte buffer in
WRAMX bank 2, then switches to WRAMX bank 6 once to gather every changed tile.
The two animation tilemaps and payload stay in WRAM0, avoiding per-tile WRAM
bank changes. Twenty-one bytes in `wPokedexData` hold producer, consumer,
timing, slot, and underrun-diagnostic state. The Listing cache adds 14 bytes:
five 16-bit row-ownership tags, a 16-bit pending row, its physical-row index,
and the last rendered owned-icon animation frame. It remains inside the existing
280-byte Pokedex union by consuming one byte of its reserved padding.
