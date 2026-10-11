; PRIVATE PROTOTYPE. Listing-only overlay of the inactive Battle Tower/Info
; workspace. No new saved state, WRAM allocation, ROM0 or interrupt scratch.
DEF wPopGridGFX EQU $d480
DEF wPopKind EQU $dc00
DEF wPopCursor EQU $dc01
DEF wPopPending EQU $dc02
DEF wPopSorting EQU $dc03
DEF wPopBounds EQU $dc04 ; hardware OAM-space left, right, top, bottom
DEF wPopFallback EQU $dc08
DEF wPopBorderDirty EQU $dc09
DEF wPopShiftPrepared EQU $dc0a
DEF wPopBorderStyle EQU $dc0b
DEF wPopGlyphRows EQU $dc0c
DEF wPopGlyphColumn EQU $dc0d
DEF wPopPreviousGlyph EQU $dc0e
DEF wPopSavedOAM EQU $dc10
DEF wPopBorderGFX EQU $dcb0
DEF wPopRightEdgeGFX EQU $dd30
DEF wPopShiftGFX EQU wPopGridGFX
DEF wPopFont EQU wPopShiftGFX + 31 tiles
DEF wPopBlankGlyph EQU wPopFont + $80 * TILE_1BPP_SIZE
ASSERT wPopGridGFX + 3 * 40 tiles == wPopKind
ASSERT wPopBlankGlyph + TILE_1BPP_SIZE <= wPopKind
ASSERT wPopRightEdgeGFX + 1 tiles <= $de00
DEF wPopOrderBit EQUS "wPokedexNameBuffer"
DEF wPopOrderFlag EQUS "wPokedexNameBuffer + 1"
DEF wPopOrderCount EQUS "wPokedexNameBuffer + 3"
DEF POKEDEX_LAST_SEEN_MASK EQU (1 << ((NUM_POKEMON - 1) % 8 + 1)) - 1

PokedexPopover_Open:
    farcall Pokedex_GetSelectedMon
    ld a, l
    ld [wPrevDexEntry], a
    ld a, h
    ld [wPrevDexEntry + 1], a
    farcall Pokedex_CancelAnimationPrefetch
    xor a
    ldh [hJoypadSum], a
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    xor a
    ld [wPopKind], a
    ld [wPopCursor], a
    ld [wPopPending], a
    ld [wPopSorting], a
    ld [wPopFallback], a
    ld [wPopBorderDirty], a
    ld [wPopShiftPrepared], a
    ld [wPopBorderStyle], a
    ldh [hBGMapMode], a
    ld a, TRUE
    ldh [hOAMUpdate], a
    ld a, DEXSELECT_STATE_MENU_RETURN
    ld [wPokedexSelectedState], a
    ld a, DEXSTATE_POPOVER
    ld [wJumptableIndex], a
    ld hl, wShadowOAM
    ld de, wPopSavedOAM
    ld bc, OAM_COUNT * 4
    call CopyBytes
    ld hl, PokedexPopover_BorderGFX
    ld de, wPopBorderGFX
    ld bc, 8 tiles
    call CopyBytes
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wPopBorderGFX
    ld de, vTiles4 tile $7a
    ld c, 6
    call Pokedex_HDMATransferCacheGFX
    ld hl, wPopBorderGFX + 6 tiles
    ld de, vTiles5 tile $28
    ld c, 2
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    call PokedexPopover_ReadRightEdge
    call PokedexPopover_Draw
    call PokedexPopover_Publish
    pop af
    ldh [rSVBK], a
    ret

PokedexPopover_Update:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
; Preserve physical command edges received during a staged redraw. The normal
; input mirror can miss a release/repress while this local owner is busy.
    di
    ldh a, [hJoypadSum]
    and PAD_A | PAD_B | PAD_START
    ld b, a
    xor a
    ldh [hJoypadSum], a
    ldh a, [hJoyPressed]
    or b
    ei
    bit B_BUTTON_F, a
    jr nz, .back
    bit START_F, a
    jp nz, .close
    bit A_BUTTON_F, a
    jr nz, .choose
    ldh a, [hJoyLast]
    bit D_UP_F, a
    jr nz, .up
    bit D_DOWN_F, a
    jr nz, .down
    jr .done
.up
    ld hl, wPopCursor
    ld a, [hl]
    and a
    jr nz, .decrement
    ld a, [wPopKind]
    add 2
    ld [hl], a
.decrement
    dec [hl]
    jr .cursor_changed
.down
    ld hl, wPopCursor
    inc [hl]
    ld a, [wPopKind]
    add 2
    cp [hl]
    jr nz, .cursor_changed
    xor a
    ld [hl], a
.cursor_changed
    call PokedexPopover_MoveCursor
    call PokedexPopover_Publish
    jr .done
.redraw
    call PokedexPopover_Draw
    call PokedexPopover_Publish
    jr .done
.back
    ld a, [wPopKind]
    and a
    jr z, .close
    xor a
    ld [wPopKind], a
    ld [wPopCursor], a
    jr .redraw
.choose
    ld a, [wPopKind]
    and a
    jr nz, .sort
    ld a, [wPopCursor]
    and a
    jr nz, .search
    inc a
    ld [wPopKind], a
    ld a, [wCurDexMode]
    ld [wPopCursor], a
    jr .redraw
.sort
    ld a, [wPopCursor]
    ld hl, wCurDexMode
    cp [hl]
    jr z, .close
    ld [hl], a
    call PokedexPopover_Resort
    jr .done
.search
    call PokedexPopover_ResetWorkspace
    farcall PokedexListing_BeginMenuTransition
    xor a
    ldh [hSCX], a
    ld a, $a7
    ldh [hWX], a
    ld a, DEXSTATE_SEARCH_SCR
    ld [wJumptableIndex], a
    jr .done
.close
    call PokedexPopover_Close
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexPopover_MoveCursor:
; Only the cursor cells change. The complete padded map and masked OAM are
; already staged, so navigation needs no grid/name/frame reconstruction.
    ld a, [wPokedexListingPresentation]
    and a
    jr nz, .ordinary
    ld a, [wPopKind]
    and a
    jp nz, PokedexPopover_MoveShiftedCursor
.ordinary
    ld hl, wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH + 2
    ld a, [wPopKind]
    and a
    jr z, .origin
    ld hl, wPokedexOwnerTilemapBuffer + 7 * TILEMAP_WIDTH + 1
.origin
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .position
    ld de, -TILEMAP_WIDTH
    add hl, de
.position
    push hl
    ld a, [wPopKind]
    add 2
    ld b, a
    ld de, 2 * TILEMAP_WIDTH
.clear
    ld [hl], " "
    add hl, de
    dec b
    jr nz, .clear
    pop hl
    ld a, [wPopCursor]
.row
    and a
    jr z, .place
    add hl, de
    dec a
    jr .row
.place
    ld [hl], "▶"
    ret

PokedexPopover_DrawBase:
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .modern
    farcall PokedexLegacy_DrawWindow
    ret
.modern
    farcall DrawPokedexListWindow
    ld a, BANK(wPokedexSeen)
    ldh [rSVBK], a
    farcall Pokedex_PrintSelectedName
    ld a, 3
    ldh [rSVBK], a
    hlcoord 0, 17
    ld de, .Footer
    ld b, 10
.footer
    ld a, [de]
    inc de
    ld [hli], a
    dec b
    jr nz, .footer
    ret
.Footer:
    db $3c, $3b, $41, $42, $43, $44, $45, $46, $47, $3c

PokedexPopover_Draw:
    ld a, [wPopKind]
    and a
    jr z, .base
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .covered
.base
    call PokedexPopover_DrawBase
.covered
; Modern Sort contains the entire Options rectangle. Its fill replaces all
; outgoing modal cells, so rebuilding the unchanged Listing is unnecessary.
    ld hl, PokedexPopover_BorderGFX
    ld de, wPopBorderGFX
    ld bc, 8 tiles
    call CopyBytes
    ld a, [wPopBorderStyle]
    and a
    jr z, .border_ready
    ld a, 1
    ld [wPopBorderDirty], a
    xor a
    ld [wPopBorderStyle], a
.border_ready
    ld hl, wPopSavedOAM
    ld de, wShadowOAM
    ld bc, OAM_COUNT * 4
    call CopyBytes
    ld a, [wPopKind]
    and a
    jr nz, .sort
    hlcoord 1, 7
    lb bc, 5, 9
    call PokedexPopover_MoveUpForLegacy
    call PokedexPopover_Frame
    hlcoord 3, 8
    call PokedexPopover_MoveUpForLegacy
    ld de, PokedexPopover_Options
    call PlaceString
    hlcoord 2, 8
    call PokedexPopover_MoveUpForLegacy
    ld a, [wPopCursor]
    add a
    ld de, SCREEN_WIDTH
    and a
    jr z, .cursor
    add hl, de
    add hl, de
    jr .cursor
.sort
    ld a, [wPokedexListingPresentation]
    and a
    jp z, PokedexPopover_DrawModernSort
    hlcoord 0, 6
    lb bc, 7, 11
    call PokedexPopover_MoveUpForLegacy
    call PokedexPopover_Frame
    hlcoord 2, 7
    call PokedexPopover_MoveUpForLegacy
    ld de, PokedexPopover_Sort
    call PlaceString
    hlcoord 1, 7
    call PokedexPopover_MoveUpForLegacy
    ld a, [wPopCursor]
    ld de, SCREEN_WIDTH * 2
.cursor_row
    and a
    jr z, .cursor
    add hl, de
    dec a
    jr .cursor_row
.cursor
    ld [hl], "▶"
PokedexPopover_StageDraw:
    call PokedexPopover_MaskSprites
    farcall Pokedex_StageOwnerTransitionMaps
    ret
PokedexPopover_Options:
    db "Sort", $4e, "Search", $50
PokedexPopover_Sort:
    db "Evolves", $4e, "Nat'l Dex", $4e, "Alphabet", $50

PokedexPopover_ReadRightEdge:
; This uniform bank-0 strip is partly outside the translated frame. Read each
; byte in a protected VRAM-accessible phase; never sample during mode 3.
    ldh a, [rVBK]
    push af
    xor a
    ldh [rVBK], a
    ld hl, vTiles2 tile $6c
    ld de, wPopRightEdgeGFX
    ld b, TILE_SIZE
.byte
    di
.wait
    ldh a, [rSTAT]
    and 2
    jr nz, .wait
    ld a, [hli]
    ei
    ld [de], a
    inc de
    dec b
    jr nz, .byte
    pop af
    ldh [rVBK], a
    ret

PokedexPopover_DrawModernSort:
    hlcoord 0, 6
    lb bc, 7, 12
    call PokedexPopover_Frame
    call PokedexPopover_PrepareShiftedText
    ld hl, PokedexPopover_ModernBorderGFX
    ld de, wPopBorderGFX
    call .copy
    ld de, wPopBorderGFX + 2 tiles
    call .copy
    ld de, wPopBorderGFX + 3 tiles
    call .copy
    ld de, wPopBorderGFX + 7 tiles
    call .copy
    ld de, wPopBorderGFX + 4 tiles
    call .copy
    ld de, wPopBorderGFX + 6 tiles
    call .copy
    ld hl, wPopBorderGFX + 2 tiles
    call .compose
    ld hl, wPopBorderGFX + 6 tiles
    call .compose
    ld hl, wPopBorderGFX + 7 tiles
    call .compose
    ld a, 1
    ld [wPopBorderStyle], a
    ld [wPopBorderDirty], a
    hlcoord 2, 7
    ld de, PokedexPopover_ShiftCells
    ld b, 3
.row
    ld c, 9
.cell
    ld a, [de]
    inc de
    ld [hli], a
    dec c
    jr nz, .cell
    push de
    ld de, 2 * SCREEN_WIDTH - 9
    add hl, de
    pop de
    dec b
    jr nz, .row
    hlcoord 2, 7, wAttrmap
    ld b, 3
.attr_row
    ld c, 9
.attr_cell
    ld [hl], BG_BANK1
    inc hl
    dec c
    jr nz, .attr_cell
    ld de, 2 * SCREEN_WIDTH - 9
    add hl, de
    dec b
    jr nz, .attr_row
    call PokedexPopover_MaskSprites
    farcall Pokedex_StageOwnerTransitionMaps
    jp PokedexPopover_MoveShiftedCursor
.copy
    ld bc, TILE_SIZE
    jp CopyBytes
.compose
; Only x0..2 belong to the right edge. Retain the Listing's x3..7 pixels.
    ld de, wPopRightEdgeGFX
    ld b, TILE_SIZE
.plane
    ld a, [de]
    and $1f
    ld c, a
    ld a, [hl]
    and $e0
    or c
    ld [hli], a
    inc de
    dec b
    jr nz, .plane
    ret

PokedexPopover_PrepareShiftedText:
; The native font is copied, then shifted in existing inactive scratch. These
; atlas cells are not used by the outgoing Options popup or live grid cache.
    ld a, [wPopShiftPrepared]
    and a
    ret nz
    ld hl, Font
    ld de, wPopFont
    ld bc, $80 * TILE_1BPP_SIZE
    ld a, BANK(Font)
    call FarCopyBytes
    ld hl, wPopBlankGlyph
    ld bc, TILE_1BPP_SIZE
    xor a
    call ByteFill
    ld a, " "
    ld [wPopPreviousGlyph], a
    ld a, 9
    ld [wPopGlyphColumn], a
    ld hl, .Labels
    ld de, wPopShiftGFX
.glyph
    ld a, [hli]
    cp $50
    jr z, .cursor
    ld c, a
    ld a, [wPopPreviousGlyph]
    ld b, a
    ld a, c
    ld [wPopPreviousGlyph], a
    push hl
    call PokedexPopover_ShiftGlyph
    pop hl
    ld a, [wPopGlyphColumn]
    dec a
    ld [wPopGlyphColumn], a
    jr nz, .glyph
    ld a, " "
    ld [wPopPreviousGlyph], a
    ld a, 9
    ld [wPopGlyphColumn], a
    jr .glyph
.cursor
    ld a, "▶"
    ld b, " "
    call PokedexPopover_ShiftGlyph
    ld hl, wPopShiftGFX
    call .cursor_variant
    ld hl, wPopShiftGFX + 9 tiles
    call .cursor_variant
    ld hl, wPopShiftGFX + 18 tiles
    call .cursor_variant
    call PokedexPopover_UploadShiftedText
    ld a, 1
    ld [wPopShiftPrepared], a
    ret
.cursor_variant
    ld bc, TILE_SIZE
    call CopyBytes
    push de
    ld hl, -TILE_SIZE + 1
    add hl, de
    ld d, h
    ld e, l
    ld hl, wPopFont + ("▶" - $80) * TILE_1BPP_SIZE
    ld b, TILE_HEIGHT
.cursor_plane
    ld a, [hli]
    REPT 5
        rlca
    ENDR
    and $e0
    cpl
    ld c, a
    ld a, [de]
    and c
    ld [de], a
    inc de
    inc de
    dec b
    jr nz, .cursor_plane
    pop de
    ret
.Labels
    db "Evolves  ", "Nat'l Dex ", "Alphabet ", $50
ASSERT @ - .Labels == 28

PokedexPopover_UploadShiftedText:
; These cells are invisible in Options. Use short full-HBlank transfers after
; the icon rows have scanned, rather than one blocking HDMA wait per span.
.wait
    ldh a, [rLY]
    cp 120
    jr c, .wait
    cp 124
    jr nc, .wait
    di
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wPopShiftGFX
    ld de, vTiles5 tile $2a
    ld b, 8
    call .transfer
    ld hl, wPopShiftGFX + 8 tiles
    ld de, vTiles5 tile $78
    ld b, 8
    call .transfer
    ld hl, wPopShiftGFX + 16 tiles
    ld de, vTiles5 tile $64
    ld b, 8
    call .transfer
    ld hl, wPopShiftGFX + 24 tiles
    ld de, vTiles5 tile $70
    ld b, 7
    call .transfer
    pop af
    ldh [rVBK], a
    ei
    ret
.transfer
    ld a, h
    ldh [rVDMA_SRC_HIGH], a
    ld a, l
    ldh [rVDMA_SRC_LOW], a
    ld a, d
    and $1f
    ldh [rVDMA_DEST_HIGH], a
    ld a, e
    ldh [rVDMA_DEST_LOW], a
.chunk
    ldh a, [rSTAT]
    and 3
    cp 3
    jr nz, .chunk
.hblank
    ldh a, [rSTAT]
    and 3
    jr nz, .hblank
    ld a, b
    cp 4
    jr c, .count
    ld a, 4
.count
    ld c, a
    dec a
    ldh [rVDMA_LEN], a
    ld a, b
    sub c
    ld b, a
    jr nz, .chunk
    ret

PokedexPopover_ShiftGlyph:
; a=current glyph, b=preceding glyph, de=one 2bpp destination tile.
    push bc
    call .pointer
    push hl
    ld a, b
    call .pointer
    ld b, h
    ld c, l
    pop hl
    ld a, TILE_HEIGHT
    ld [wPopGlyphRows], a
.row
    xor a
    ld [de], a
    inc de
    ld a, [bc]
    inc bc
    REPT 5
        rlca
    ENDR
    and $e0
    push bc
    ld b, a
    ld a, [hli]
    REPT 3
        srl a
    ENDR
    or b
    cpl
    pop bc
    ld [de], a
    inc de
    ld a, [wPopGlyphRows]
    dec a
    ld [wPopGlyphRows], a
    jr nz, .row
    pop bc
    ret
.pointer
    cp " "
    ld hl, wPopBlankGlyph
    ret z
    sub $80
    ld l, a
    ld h, 0
    REPT 3
        add hl, hl
    ENDR
    push de
    ld de, wPopFont
    add hl, de
    pop de
    ret

PokedexPopover_MoveShiftedCursor:
    ld hl, wPokedexOwnerTilemapBuffer + 7 * TILEMAP_WIDTH + 1
    ld de, 2 * TILEMAP_WIDTH
    ld bc, .FirstGlyphs
.clear
    ld [hl], " "
    inc hl
    ld a, [bc]
    ld [hld], a
    inc bc
    add hl, de
    ld a, c
    cp LOW(.FirstGlyphs + 3)
    jr nz, .clear
    ld hl, wPokedexOwnerAttrmapBuffer + 7 * TILEMAP_WIDTH + 1
    REPT 3
        ld [hl], 0
        add hl, de
    ENDR
    ld a, [wPopCursor]
    ld b, a
    ld hl, wPokedexOwnerTilemapBuffer + 7 * TILEMAP_WIDTH + 1
.position
    and a
    jr z, .selected
    add hl, de
    dec a
    jr .position
.selected
    ld [hl], $73
    inc hl
    ld a, b
    add $74
    ld [hl], a
    ld hl, wPokedexOwnerAttrmapBuffer + 7 * TILEMAP_WIDTH + 1
    ld a, b
.attr
    and a
    jr z, .attr_selected
    add hl, de
    dec a
    jr .attr
.attr_selected
    ld [hl], BG_BANK1
    ret
.FirstGlyphs
    db $2a, $79, $66

PokedexPopover_ShiftCells:
FOR cell_id, $2a, $32
    db cell_id
ENDR
FOR cell_id, $78, $80
    db cell_id
ENDR
FOR cell_id, $64, $6c
    db cell_id
ENDR
FOR cell_id, $70, $77
    db cell_id
ENDR

PokedexPopover_MoveUpForLegacy:
; Legacy's two rectangles and text rows are one tile above Modern's.
    ld a, [wPokedexListingPresentation]
    and a
    ret z
    ld de, -SCREEN_WIDTH
    add hl, de
    ret

PokedexPopover_Frame:
; hl = tilemap origin; b = height, c = width. Each edge borrows BG bank 1;
; the gray interior and normal font remain in bank 0, palette 0.
    push hl
    push bc
    ld a, $32
    call PokedexPopover_FillBox
    pop bc
    pop hl
    push hl
    push bc
    ld a, $fa
    ld [hli], a
    ld d, c
    dec d
    dec d
    ld a, $fb
.top
    ld [hli], a
    dec d
    jr nz, .top
    ld [hl], $fc
    pop bc
    pop hl
    push bc
    ld de, SCREEN_WIDTH
    dec b
    dec b
.sides
    add hl, de
    push hl
    ld [hl], $fd
    ld a, c
    dec a
    add l
    ld l, a
    jr nc, .right
    inc h
.right
    ld [hl], $29
    pop hl
    dec b
    jr nz, .sides
    add hl, de
    ld [hl], $fe
    inc hl
    ld b, c
    dec b
    dec b
.bottom
    ld [hl], $ff
    inc hl
    dec b
    jr nz, .bottom
    ld [hl], $28
    pop bc
; Set attributes from the same rectangle, retaining the underlying outside cells.
    ld a, [wPopKind]
    and a
    hlcoord 1, 7, wAttrmap
    jr z, .attrs
    hlcoord 0, 6, wAttrmap
.attrs
    call PokedexPopover_MoveUpForLegacy
    push hl
    push bc
    xor a
    call PokedexPopover_FillBox
    pop bc
    pop hl
    ld de, SCREEN_WIDTH
    push bc
    push hl
    ld b, c
.top_attrs
    ld [hl], BG_BANK1
    inc hl
    dec b
    jr nz, .top_attrs
    pop hl
    pop bc
    dec b
.side_attrs
    add hl, de
    push hl
    ld [hl], BG_BANK1
    ld a, c
    dec a
    add l
    ld l, a
    jr nc, .right_attr
    inc h
.right_attr
    ld [hl], BG_BANK1
    pop hl
    dec b
    jr nz, .side_attrs
    ld b, c
.bottom_attrs
    ld [hl], BG_BANK1
    inc hl
    dec b
    jr nz, .bottom_attrs
    ret

PokedexPopover_MaskSprites:
; Color-zero border pixels do not cover OBJ. Hide only intersecting 8x8
; sprites, preserving all unobscured grid sprites and the sidebar.
    ld hl, wPopBounds
    ld a, [wPopKind]
    and a
    jr nz, .sort
    ld a, 72 + 8 - 8
    ld [hli], a
    ld a, 144 + 8
    ld [hli], a
    ld a, 56 + 16 - 8
    ld [hli], a
    ld a, 96 + 16
    ld [hl], a
    jr .mask
.sort
    ld a, 64 + 8 - 8
    ld [hli], a
    ld a, 152 + 8
    ld [hli], a
    ld a, 48 + 16 - 8
    ld [hli], a
    ld a, 104 + 16
    ld [hl], a
.mask
    ld a, [wPokedexListingPresentation]
    and a
    jr nz, .legacy_bounds
    ld a, [wPopKind]
    and a
    jr z, .sprites
    ld hl, wPopBounds
    ld a, [hl]
    add 3
    ld [hli], a
    ld a, [hl]
    add 3
    ld [hl], a
    jr .sprites
.legacy_bounds
    ld hl, wPopBounds + 2
    ld a, [hl]
    sub 8
    ld [hli], a
    ld a, [hl]
    sub 8
    ld [hl], a
.sprites
    ld hl, wShadowOAM
    ld b, OAM_COUNT
.loop
    ld c, [hl]
    ld a, [wPopBounds + 2]
    cp c
    jr nc, .next
    ld a, [wPopBounds + 3]
    cp c
    jr c, .next
    jr z, .next
    inc hl
    ld c, [hl]
    dec hl
    ld a, [wPopBounds]
    cp c
    jr nc, .next
    ld a, [wPopBounds + 1]
    cp c
    jr c, .next
    jr z, .next
    ld [hl], 0
.next
    inc hl
    inc hl
    inc hl
    inc hl
    dec b
    jr nz, .loop
    ret

PokedexPopover_FillBox:
    push bc
    push hl
.column
    ld [hli], a
    dec c
    jr nz, .column
    pop hl
    ld bc, SCREEN_WIDTH
    add hl, bc
    pop bc
    dec b
    jr nz, PokedexPopover_FillBox
    ret

PokedexPopover_Publish:
    ld a, 1
    ld [wPopPending], a
    ld a, VBLANK_POKEDEX
    ldh [hVBlank], a
.wait
    call DelayFrame
    ld a, [wPopPending]
    and a
    jr nz, .wait
    ret

PUSHS
SECTION FRAGMENT "bank77", ROMX
PokedexPopover_VBlank:
; Lives with the dispatcher: no interrupt-time FarCall or ROM bank switch.
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    ld a, [wPopPending]
    and a
    jr z, .done
    ldh a, [rLY]
    cp LY_VBLANK
    jr nz, .done
    ldh a, [rVBK]
    push af
    ld a, [wPopBorderDirty]
    and a
    jr z, .border_ready
    ld a, 1
    ldh [rVBK], a
    ld hl, wPopBorderGFX
    ld de, vTiles4 tile $7a
    ld c, 6
    call PokedexPopover_GDMA
    ld hl, wPopBorderGFX + 6 tiles
    ld de, vTiles5 tile $28
    ld c, 2
    call PokedexPopover_GDMA
.border_ready
    ld a, [wPopSorting]
    and a
    jr z, .maps
    ld a, BANK(wBGPals2)
    ldh [rSVBK], a
    call ForceUpdateCGBPals
    ld a, 3
    ldh [rSVBK], a
.maps
    ld a, 1
    ldh [rVBK], a
    ld hl, wPokedexOwnerAttrmapBuffer
    ld de, vBGMap1
    ld c, 2 * SCREEN_HEIGHT
    call PokedexPopover_GDMA
    xor a
    ldh [rVBK], a
    ld hl, wPokedexOwnerTilemapBuffer
    ld de, vBGMap1
    ld c, 2 * SCREEN_HEIGHT
    call PokedexPopover_GDMA
    call hTransferShadowOAM
.committed
    xor a
    ld [wPopPending], a
    ld [wPopSorting], a
    ld [wPopBorderDirty], a
    pop af
    ldh [rVBK], a
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexPopover_GDMA:
    ld a, h
    ldh [rVDMA_SRC_HIGH], a
    ld a, l
    ldh [rVDMA_SRC_LOW], a
    ld a, d
    and $1f
    ldh [rVDMA_DEST_HIGH], a
    ld a, e
    ldh [rVDMA_DEST_LOW], a
    ld a, c
    dec a
    ldh [rVDMA_LEN], a
    ret
POPS

PokedexPopover_StageCacheRow:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    ld a, [wPopSorting]
    and a
    jr z, .ordinary
    ld a, [wPokedexGridPendingPhysicalRow]
    ld l, a
    ld h, 0
    REPT 7
        add hl, hl
    ENDR
    ld de, wPopGridGFX
    add hl, de
    ld d, h
    ld e, l
    ld hl, POKEDEX_GRID_SIDE_FRAME0_GFX
    ld bc, 8 tiles
    call CopyBytes
    ld hl, 40 tiles - 8 tiles
    add hl, de
    ld d, h
    ld e, l
    ld hl, POKEDEX_GRID_CENTER_GFX
    ld bc, 8 tiles
    call CopyBytes
    ld hl, 40 tiles - 8 tiles
    add hl, de
    ld d, h
    ld e, l
    ld hl, POKEDEX_GRID_SIDE_FRAME1_GFX
    ld bc, 8 tiles
    call CopyBytes
    ld a, [wPokedexGridPendingPhysicalRow]
    add a
    ld e, a
    ld d, 0
    ld hl, wPokedexGridCacheRowOffsets
    add hl, de
    ld a, [wPokedexGridPendingRowOffset]
    ld [hli], a
    ld a, [wPokedexGridPendingRowOffset + 1]
    ld [hl], a
    pop af
    ldh [rSVBK], a
    scf
    ret
.ordinary
    pop af
    ldh [rSVBK], a
    and a
    ret

PokedexPopover_Resort:
    call PokedexPopover_OrderMons
; Changed sorts always start at entry zero. Keep the staged-grid path only
; when the first species is already the displayed portrait.
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld hl, wPokedexOrder
    ld a, [hli]
    ld e, a
    ld a, [hl]
    ld d, a
    ld a, BANK(wPrevDexEntry)
    ldh [rSVBK], a
    ld hl, wPrevDexEntry
    ld a, [hli]
    cp e
    jr nz, .replacement
    ld a, [hl]
    cp d
    jr nz, .replacement
    xor a
    jr .position
.replacement
    ld a, 1
.position
    ld e, a
    ld a, 3
    ldh [rSVBK], a
    ld a, e
    ld [wPopFallback], a
    xor a
    ld [wPokedexSelectedIndex], a
    ld [wPokedexSelectedIndex + 1], a
    ld [wPokedexListingSavedScrollOffset], a
    ld [wPokedexListingSavedScrollOffset + 1], a
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .modern_position
    farcall PokedexSelectedMon_NormalizeLinearReturn
    jr .invalidate
.modern_position
    farcall Pokedex_NormalizeListingAfterSelectedMon
.invalidate
; Row tags identify positions, not sort order. Neither portrait path may
; reuse the previous order's icon tiles at those same positions.
    farcall Pokedex_InitGridCacheState
    ld a, 3
    ldh [rSVBK], a
    ld a, [wPopFallback]
    and a
    jr z, .retained_portrait
; A different first species needs the established hidden complete-owner
; handoff, including an unseen/blank portrait in National or Evolves.
    call PokedexPopover_ResetWorkspace
    farcall PokedexListing_BeginMenuTransition
    ld a, DEXSELECT_STATE_MENU_RETURN
    ld [wPokedexSelectedState], a
    ld a, DEXSTATE_MAIN_SCR
    ld [wJumptableIndex], a
    ret
.retained_portrait
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .grid
; Same first portrait: only Legacy's names, cursor and marks change. Publish
; those maps/OAM together without a grid upload or palette replacement.
    call PokedexPopover_DrawBase
    farcall PokedexLegacy_UpdateOAM
    farcall Pokedex_StageOwnerTransitionMaps
    call PokedexPopover_Publish
    jp PokedexPopover_Finish
.grid
    ld a, 1
    ld [wPopSorting], a
    ld hl, wPopGridGFX
    ld bc, 3 * 40 tiles
    xor a
    call ByteFill
    farcall Pokedex_EnsureGridCache
    farcall Pokedex_LoadGridPage
    farcall Pokedex_SyncGridIconAnimationFrame
    farcall Pokedex_UpdateGridOAM
    farcall CGB_PokedexLoadListIconPalettes
    call PokedexPopover_DrawBase
    farcall Pokedex_StageOwnerTransitionMaps
    farcall ApplyPals
    xor a
    ldh [hCGBPalUpdate], a
    call PokedexPopover_UploadGrid
    ld a, 1
    ld [wPopPending], a
    ei
.wait
    call DelayFrame
    ld a, [wPopPending]
    and a
    jr nz, .wait
    call PokedexPopover_Finish
    ret

PokedexPopover_UploadGrid:
; Visible icons finish by line 120. Upload the three visible physical rows
; after that scan, leaving the next VBlank exclusively for maps/palettes/OAM.
; Four-tile GDMA bursts fit in a full HBlank. A longer active-display GDMA
; can corrupt both VRAM banks, even when the outgoing grid has finished.
; The invalid look-behind/look-ahead tags are repaired by ordinary scrolling.
.wait
    ldh a, [rLY]
    cp 120
    jr c, .wait
    cp 124
    jr nc, .wait
    di
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wPopGridGFX + 8 tiles
    ld de, vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 8)
    call .Transfer
    ld hl, wPopGridGFX + 48 tiles
    ld de, vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 8)
    call .Transfer
    ld hl, wPopGridGFX + 88 tiles
    ld de, vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 8)
    call .Transfer
    pop af
    ldh [rVBK], a
    ret
.Transfer:
    ld a, h
    ldh [rVDMA_SRC_HIGH], a
    ld a, l
    ldh [rVDMA_SRC_LOW], a
    ld a, d
    and $1f
    ldh [rVDMA_DEST_HIGH], a
    ld a, e
    ldh [rVDMA_DEST_LOW], a
    ld c, 6
.chunk
    ldh a, [rSTAT]
    and 3
    cp 3
    jr nz, .chunk
.hblank
    ldh a, [rSTAT]
    and 3
    jr nz, .hblank
    ld a, 4 - 1
    ldh [rVDMA_LEN], a
    dec c
    jr nz, .chunk
    ret

PokedexPopover_Close:
    ld a, [wPokedexListingPresentation]
    and a
    jr z, .modern
    farcall PokedexLegacy_UpdateOAM
    jr .maps
.modern
    farcall Pokedex_SyncGridIconAnimationFrame
    farcall Pokedex_UpdateGridOAM
.maps
    call PokedexPopover_DrawBase
    farcall Pokedex_StageOwnerTransitionMaps
    call PokedexPopover_Publish
    ; fallthrough
PokedexPopover_Finish:
    call PokedexPopover_ResetWorkspace
    xor a
    ld [wPokedexSelectedState], a
    ldh [hOAMUpdate], a
    ld a, DEXSTATE_UPDATE_MAIN_SCR
    ld [wJumptableIndex], a
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexSeen)
    ldh [rSVBK], a
    farcall Pokedex_StartAnimationPrefetch
    pop af
    ldh [rSVBK], a
    ret

PokedexPopover_ResetWorkspace:
; Staging overwrites inactive Info state too. Clear it before normal dispatch
; resumes, otherwise random glyph bytes can resemble a pending Info producer.
    ld hl, wPokedexDescriptionTextState
    ld bc, wPokedexInfoWorkspaceEnd - wPokedexDescriptionTextState
    xor a
    call ByteFill
    ret

PokedexPopover_OrderMons:
; Both builds snapshot seen flags once. The compact candidate computes its
; bit address locally; it does not call FlagAction or change banks per entry.
; The active order remains writable for the existing type Search compactor.
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexSeen)
    ldh [rSVBK], a
    ld hl, wPokedexSeen
    ld de, POKEDEX_GRID_CENTER_GFX
    ld bc, POKEDEX_ORDER_SEEN_BYTES
    call CopyBytes
    call .AllSeen
    jp c, .all_seen
    ld hl, POKEDEX_ORDER_SEEN_FLAGS
    ld bc, POKEDEX_ORDER_SEEN_BYTES
    xor a
    call ByteFill
    ld [wDexListingEnd], a
    ld [wDexListingEnd + 1], a
    ld [wPopOrderCount], a
    ld [wPopOrderCount + 1], a
    ld a, 1
    ld [wPopOrderBit], a
    ld a, LOW(POKEDEX_ORDER_SEEN_FLAGS)
    ld [wPopOrderFlag], a
    ld a, HIGH(POKEDEX_ORDER_SEEN_FLAGS)
    ld [wPopOrderFlag + 1], a
    ld a, LOW(-NUM_POKEMON)
    ld [wDexTempCounter], a
    ld a, HIGH(-NUM_POKEMON)
    ld [wDexTempCounter + 1], a
    ld a, [wCurDexMode]
    add a
    ld c, a
    ld b, 0
IF DEF(DEX_SORT_WITHOUT_RECORDS)
    ld hl, .Words
ELSE
    ld hl, .Records
ENDC
    add hl, bc
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld de, wPokedexOrder
.loop
    ld a, [hli]
    ld [de], a
    inc de
IF DEF(DEX_SORT_WITHOUT_RECORDS)
    ld c, a
ENDC
    ld a, [hli]
    ld [de], a
    inc de
IF DEF(DEX_SORT_WITHOUT_RECORDS)
    ld b, a
    dec bc
    push hl
    push de
    ld a, c
    and 7
    ld e, a
    ld d, 0
    ld hl, .Masks
    add hl, de
    ld a, [hl]
    push af
    REPT 3
        srl b
        rr c
    ENDR
    ld hl, POKEDEX_GRID_CENTER_GFX
    add hl, bc
    ld c, [hl]
    pop af
    pop de
    pop hl
ELSE
    ld a, [hli]
    ld c, a
    ld b, 0
    push hl
    ld hl, POKEDEX_GRID_CENTER_GFX
    add hl, bc
    ld c, [hl]
    pop hl
    ld a, [hli]
ENDC
    and c
    jr nz, .seen
    ld a, [wCurDexMode]
    cp DEXMODE_ABC
    jr nz, .advance
    dec de
    dec de
    jr .remaining
.seen
    push hl
    ld hl, wPopOrderFlag
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, [wPopOrderBit]
    or [hl]
    ld [hl], a
    ld hl, wPopOrderCount
    ld a, [hli]
    add 1
    ld [wDexListingEnd], a
    ld a, [hl]
    adc 0
    ld [wDexListingEnd + 1], a
    pop hl
.advance
    push hl
    ld hl, wPopOrderCount
    inc [hl]
    jr nz, .counted
    inc hl
    inc [hl]
.counted
    ld hl, wPopOrderBit
    rlc [hl]
    jr nc, .bit_ready
    ld hl, wPopOrderFlag
    inc [hl]
    jr nz, .bit_ready
    inc hl
    inc [hl]
.bit_ready
    pop hl
.remaining
    push hl
    ld hl, wDexTempCounter
    inc [hl]
    jr nz, .more
    inc hl
    inc [hl]
    jr nz, .more
    pop hl
    ld a, -1
    ld [de], a
    inc de
    ld [de], a
    pop af
    ldh [rSVBK], a
    ret
.more
    pop hl
IF DEF(DEX_SORT_WITHOUT_RECORDS)
    jp .loop
ELSE
    jr .loop
ENDC
IF DEF(DEX_SORT_WITHOUT_RECORDS)
.Masks:
    db $01, $02, $04, $08, $10, $20, $40, $80
ELSE
.Records:
    dw NewPokedexOrderRecords, NationalPokedexOrderRecords, AlphabeticalPokedexOrderRecords
ENDC
.AllSeen:
    ld hl, POKEDEX_GRID_CENTER_GFX
    ld b, POKEDEX_ORDER_SEEN_BYTES - 1
.full_bytes
    ld a, [hli]
    inc a
    jr nz, .not_all
    dec b
    jr nz, .full_bytes
    ld a, [hl]
    and POKEDEX_LAST_SEEN_MASK
    cp POKEDEX_LAST_SEEN_MASK
    jr nz, .not_all
    scf
    ret
.not_all
    and a
    ret
.all_seen
    ld a, [wCurDexMode]
    add a
    ld c, a
    ld b, 0
    ld hl, .Words
    add hl, bc
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld de, wPokedexOrder
    ld bc, NUM_POKEMON * 2
    call CopyBytes
    ld a, -1
    ld [de], a
    inc de
    ld [de], a
    ld hl, POKEDEX_ORDER_SEEN_FLAGS
    ld bc, POKEDEX_ORDER_SEEN_BYTES
    call ByteFill
    ld a, LOW(NUM_POKEMON)
    ld [wDexListingEnd], a
    ld a, HIGH(NUM_POKEMON)
    ld [wDexListingEnd + 1], a
    pop af
    ldh [rSVBK], a
    ret
.Words:
    dw NewPokedexOrder, NationalPokedexOrder, AlphabeticalPokedexOrder

PokedexPopover_BorderGFX:
INCBIN "gfx/pokedex/pokedex_popover_sheet.2bpp"
.end
ASSERT .end - PokedexPopover_BorderGFX == 8 tiles
PokedexPopover_ModernBorderGFX:
INCBIN "gfx/pokedex/pokedex_popover_sheet_modern.2bpp"
.end
ASSERT .end - PokedexPopover_ModernBorderGFX == 6 tiles
INCLUDE "build/dex-sort-assets/tables.asm"
