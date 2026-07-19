# Pokedex VRAM and scratch-RAM plan

This document records the current Pokedex graphics ownership and the target
permanent allocation for the listing, description, search, search-results,
options, and Unown screens. The area map is the only normal Pokedex screen
allowed to load graphics on demand.

The target allocation deliberately does not cache neighboring known
frontpics. The selected known frontpic keeps one 49-tile destination, while
the common unseen frontpic remains resident in VRAM bank 1.

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
| `vTiles2 $00-$30` | Selected known frontpic | 49 | Area-map graphics temporarily overwrite `$00-$2f`. |
| `vTiles2 $31-$70` | Shared Pokedex UI | 64 | Loaded from `pokedex.2bpp`. |
| `vTiles2 $54` and `$5b` | Listing joined border | 2 | Listing-specific overlays inside the shared UI range. |
| `vTiles2 $62-$65` | Selected footprint | 4 | Description-specific overlay inside the shared UI range. |
| `vTiles2 $40-$5a` | Unown glyphs and cursor | 27 | Unown-mode overlay inside the shared UI range. |

The footprint, joined-border, and Unown writes explain why those screens
currently need mode-specific graphics restoration even though their main UI
comes from the same 64-tile source.

### VRAM bank 1

| Region | Current owner | Tiles | Notes |
| --- | --- | ---: | --- |
| `vTiles3 $00-$0b` | Center-column mini-sprites | 12 | Three 2x2 OBJ icons. |
| `vTiles4` | Unused by the normal Pokedex | 128 | Available for permanent cross-screen assets. |
| `vTiles5 $00-$17` | Left/right mini-sprites | 24 | Six 2x2 BG icons. |

## Target permanent allocation

The ranges below reserve all known listing, description, search, and Unown
requirements without assigning VRAM for neighboring known frontpics.

| Region | Target owner | Tiles |
| --- | --- | ---: |
| `vTiles0 $00-$36` | Shared Dex artwork and OBJ graphics | 55 |
| `vTiles0 $40-$41` | Listing cursor and caught ball | 2 |
| `vTiles1 $00-$7f` | Inverted font plus the existing scrollbar/grid-icon substitutions | 128 |
| `vTiles2 $00-$30` | Current known frontpic | 49 |
| `vTiles2 $31-$70` | Shared Pokedex UI | 64 |
| `vTiles3 $00-$13` | Five center-column mini-sprite rows | 20 |
| `vTiles4 $00-$30` | Resident unseen 7x7 frontpic | 49 |
| `vTiles4 $31-$34` | Preloaded selected footprint | 4 |
| `vTiles4 $35-$4f` | Permanent Unown glyphs and cursor | 27 |
| `vTiles5 $00-$27` | Five left/right mini-sprite rows | 40 |

The `vTiles4` ranges above are physical offsets within the `$8800-$8fff`
region. With signed BG tile addressing they appear in tilemaps as `$80-$b0`,
`$b1-$b4`, and `$b5-$cf`, respectively, with the VRAM-bank attribute set.

This leaves 244 tiles free in VRAM bank 1: 108 in `vTiles3`, 48 in
`vTiles4`, and 88 in `vTiles5`. The footprint and Unown overlays must move
to their bank-1 destinations in later residency phases. The listing-specific
joined-border tiles can remain in bank 0 if the final cross-screen tilemap
audit confirms that no other Pokedex screen needs the original tiles.

Search, search results, and options currently load no unique tile graphics;
they use the shared font and Pokedex UI. The normal description path also
reuses the listing frontpic. Its only species-specific VRAM load is the
four-tile footprint, which will be prepared while that species is selected.

The area map remains an explicit temporary overlay. It loads 48 town-map
tiles to `vTiles2 $00-$2f` and five OBJ tiles to `vTiles0 $78-$7b/$7f`.
Returning from the area map must restore the current known frontpic when one
is required; the permanent unseen frontpic and shared UI are not in the
overwritten range.

## WRAM0 workspace

`wPokedexWRAM0Scratch` overlays the 1,300-byte `wOverworldMapBlocks` union.
It is valid only during the Start-menu Pokedex session. `StartMenu_Pokedex`
calls `ReturnToMapFromSubmenu` before `CloseSubmenu`, rebuilding both map and
connection block data before the overworld is drawn again.

Future phases may define overlapping views within this workspace. Useful
maximum sizes include:

| Workspace view | Bytes |
| --- | ---: |
| Padded 7x7 frontpic | 784 |
| Frontpic plus four 2bpp footprint tiles | 848 |
| Native 20x18 tilemap and attrmap | 720 |
| HDMA-padded 32x18 tilemap and attrmap | 1152 |
| Nine 2x2 mini-sprites | 576 |
| Five rows of three 2x2 mini-sprites | 960 |

The global `wScratchTilemap` is `TILEMAP_AREA`, or 32x32 = 1,024 bytes. It
can already stage a complete 784-byte frontpic for `Get2bppViaHDMA`. The
WRAM0 workspace is therefore optional for that transfer, but can remove an
extra staging copy or preserve Dex-specific prepared data while the global
scratch union is reused.
