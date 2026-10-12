; Moves encyclopedia with persistent discoveries and temporary type/name search.
SECTION "Pokedex Moves Mode Prototype", ROMX

DEF wMovesModeSort       EQUS "wPokedexInfoGFX"
DEF wMovesModeCursor     EQUS "wPokedexInfoGFX + 1"
DEF wMovesModeScroll     EQUS "wPokedexInfoGFX + 2"
DEF wMovesModeSelected   EQUS "wPokedexInfoGFX + 4"
DEF wMovesModeRecord     EQUS "wPokedexInfoGFX + 6"
DEF wMovesModeTypeBuffer EQUS "wPokedexInfoGFX + 12"
DEF wMovesModeRow        EQUS "wPokedexInfoGFX + 13"
DEF wMovesModeValue      EQUS "wPokedexInfoGFX + 14"
DEF wMovesModeTextBank   EQUS "wPokedexInfoGFX + 15"
DEF wMovesModeTextRow    EQUS "wPokedexInfoGFX + 16"
DEF wMovesModeTextColumn EQUS "wPokedexInfoGFX + 17"
DEF wMovesModePalettes   EQUS "wPokedexInfoGFX + 18"
DEF wMovesCursorPending EQUS "wPokedexInfoGFX + 34"
DEF wMovesCursorTile    EQUS "wPokedexInfoGFX + 35"
DEF wMovesCursorAddress EQUS "wPokedexInfoGFX + 36"
DEF wMovesModeBorderGFX  EQUS "wPokedexInfoGFX + 3 tiles"
DEF wMovesModeSeenSnapshot EQUS "wPokedexInfoGFX + 36 tiles"
ASSERT wMovesModeBorderGFX + 21 tiles <= wMovesModeSeenSnapshot
ASSERT wMovesModeSeenSnapshot + 64 <= wPokedexInfoGFX + 40 tiles
DEF MOVES_MODE_CATEGORY_TILE EQU $30
DEF MOVES_MODE_CURSOR_TILE EQU $ed
DEF MOVES_MODE_SCROLLBAR_TILE EQU $ba
DEF MOVES_MODE_SCROLL_TRAVEL EQU 65
ASSERT (NUM_ATTACKS - 8) * MOVES_MODE_SCROLL_TRAVEL + (NUM_ATTACKS - 8) / 2 <= $ffff

PokedexMovesMode_Initialize:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    xor a
    ld hl, wPokedexInfoGFX
    ld bc, 48
    call ByteFill
    ldh [hJoypadSum], a
    ld [wPokedexSelectedState], a
    ld [wPokedexOwnerTransition], a
    ld [wPokedexAnimFlags], a
    ld [wPokedexResidentFootprintSpecies], a
    call PokedexMovesMode_RestoreSort
    call PokedexMovesSearch_Reset
    call ClearSprites
    farcall Pokedex_CancelAnimationPrefetch
    call PokedexMovesMode_SnapshotSeen
    call PokedexMovesMode_LoadScrollbarGFX
    call PokedexMovesMode_LoadCategoryGFX
    call PokedexMovesMode_LoadSortBorder
    ld a, BANK(wBGPals1)
    ldh [rSVBK], a
    ld hl, PokedexUIPalette
    ld de, wBGPals1
    ld bc, 1 palettes
    ld a, BANK(PokedexUIPalette)
    call FarCopyBytes
    ld hl, PokedexListScrollThumbPalette
    ld de, wOBPals1 palette 3
    ld bc, 1 palettes
    ld a, BANK(PokedexListScrollThumbPalette)
    call FarCopyBytes
    farcall ApplyPals
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ld a, POKEDEX_SCX
    ldh [hSCX], a
    ld a, $a7
    ldh [hWX], a
    xor a
    ldh [hWY], a
    ldh [hSCY], a
    call PokedexMovesMode_Draw
    farcall PokedexListing_RevealMenu
    ld a, DEXSTATE_MOVES_MODE_UPDATE
    ld [wJumptableIndex], a
    pop af
    ldh [rSVBK], a
    ret

PokedexMovesMode_Update:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    call PokedexMovesMode_ReadInput
    call PokedexMovesMode_BlinkCursor
    ldh a, [hJoyPressed]
    and PAD_SELECT
    jp nz, .leave
    ldh a, [hJoyPressed]
    and PAD_B
    jp nz, .back
    ldh a, [hJoyPressed]
    and PAD_START
    jp nz, .options
    call PokedexMovesSearch_Count
    ld a, h
    or l
    jp z, .done
    ldh a, [hJoyLast]
    and PAD_UP | PAD_DOWN | PAD_LEFT | PAD_RIGHT
    jp z, .done
    bit D_UP_F, a
    jr nz, .up
    bit D_DOWN_F, a
    jr nz, .down
    bit D_LEFT_F, a
    jr nz, .page_left
    call PokedexMovesMode_PageRight
    jp nc, .done
    jp .draw
.page_left
    call PokedexMovesMode_PageLeft
    jp nc, .done
    jp .draw
.up
    ld a, [wMovesModeCursor]
    and a
    jr nz, .cursor_up
    ld hl, wMovesModeScroll
    ld a, [hli]
    or [hl]
    jr z, .wrap_bottom
    dec hl
    ld a, [hl]
    sub 1
    ld [hli], a
    ld a, [hl]
    sbc 0
    ld [hl], a
    jr .draw
.cursor_up
    dec a
    ld [wMovesModeCursor], a
    jr .draw
.wrap_bottom
    call PokedexMovesSearch_MaxScroll
    ld a, l
    ld [wMovesModeScroll], a
    ld a, h
    ld [wMovesModeScroll + 1], a
    call PokedexMovesSearch_Count
    dec hl
    ld a, h
    and a
    ld a, 7
    jr nz, .bottom_cursor
    ld a, l
    cp 8
    jr c, .bottom_cursor
    ld a, 7
.bottom_cursor
    ld [wMovesModeCursor], a
    jr .draw
.down
    call PokedexMovesMode_Ordinal
    push hl
    call PokedexMovesSearch_Count
    dec hl
    ld d, h
    ld e, l
    pop hl
    ld a, h
    cp d
    jr nz, .advance
    ld a, l
    cp e
    jr z, .wrap_top
.advance
    ld a, [wMovesModeCursor]
    cp 7
    jr z, .scroll_down
    inc a
    ld [wMovesModeCursor], a
    jr .draw
.scroll_down
    ld hl, wMovesModeScroll
    inc [hl]
    jr nz, .draw
    inc hl
    inc [hl]
    jr .draw
.wrap_top
    xor a
    ld [wMovesModeCursor], a
    ld [wMovesModeScroll], a
    ld [wMovesModeScroll + 1], a
.draw
    call PokedexMovesMode_Draw
.done
    pop af
    ldh [rSVBK], a
    ret
.options
    ld a, [wMovesSearchActive]
    and a
    jr nz, .done
    xor a
    ld [wDexArrowCursorPosIndex], a
    call PokedexMovesMode_DrawPopupFrame
    call PokedexMovesSearch_DrawOptions
    call PokedexMovesMode_Publish
    ld a, DEXSTATE_MOVES_OPTIONS
    ld [wJumptableIndex], a
    jr .done
.back
    ld a, [wMovesSearchActive]
    and a
    jr z, .leave
    call PokedexMovesSearch_ShowForm
    jr .done
.leave
    farcall PokedexListing_BeginMenuTransition
    ld a, DEXSELECT_STATE_MOVES_RETURN
    ld [wPokedexSelectedState], a
    ld a, DEXSTATE_OPTION_SCR
    ld [wJumptableIndex], a
    jr .done


PokedexMovesMode_SortUpdate:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    call PokedexMovesMode_ReadInput
    call PokedexMovesMode_BlinkCursor
    ldh a, [hJoyPressed]
    and PAD_B | PAD_START
    jr nz, .close
    ldh a, [hJoyPressed]
    and PAD_UP | PAD_DOWN
    jr z, .accept
    ld a, [wDexArrowCursorPosIndex]
    xor 1
    ld [wDexArrowCursorPosIndex], a
    call PokedexMovesMode_DrawSortRows
    call PokedexMovesMode_Publish
    jr .done
.accept
    ldh a, [hJoyPressed]
    and PAD_A
    jr z, .done
    ld a, [wDexArrowCursorPosIndex]
    call PokedexMovesMode_RememberSort
    ld hl, wMovesModeSort
    cp [hl]
    jr z, .close
    ld [hl], a
    xor a
    ld [wMovesModeScroll], a
    ld [wMovesModeScroll + 1], a
    ld [wMovesModeCursor], a
.close
    call PokedexMovesMode_Draw
    ld a, DEXSTATE_MOVES_MODE_UPDATE
    ld [wJumptableIndex], a
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexMovesMode_ReadInput:
    ld a, [wInputType]
    cp AUTO_INPUT
    ret z
    ; Preserve short physical presses across redraws. Synchronize the mirror
    ; while consuming edges so a newly sampled press cannot be accepted twice.
    di
    ldh a, [hJoypadSum]
    ld b, a
    xor a
    ldh [hJoypadSum], a
    ldh a, [hJoypadDown]
    ldh [hJoyDown], a
    ldh a, [hJoyPressed]
    or b
    ldh [hJoyPressed], a
    ld a, b
    and a
    jr z, .done
    ld a, 15
    ld [wTextDelayFrames], a
    ld a, b
    and PAD_CTRL_PAD
    jr z, .done
    ld b, a
    ldh a, [hJoyLast]
    and PAD_BUTTONS
    or b
    ldh [hJoyLast], a
.done
    ei
    ret

PokedexMovesMode_Ordinal:
    ld a, [wMovesModeScroll]
    ld l, a
    ld a, [wMovesModeScroll + 1]
    ld h, a
    ld a, [wMovesModeCursor]
    ld e, a
    ld d, 0
    add hl, de
    ret

PokedexMovesMode_PageLeft:
    ld a, [wMovesModeScroll]
    ld l, a
    ld a, [wMovesModeScroll + 1]
    ld h, a
    or l
    ret z
    ld de, -8
    add hl, de
    jr c, PokedexMovesMode_StorePage
    ld hl, 0
    jr PokedexMovesMode_StorePage

PokedexMovesMode_PageRight:
    ld a, [wMovesModeScroll]
    ld l, a
    ld a, [wMovesModeScroll + 1]
    ld h, a
    push hl
    call PokedexMovesSearch_MaxScroll
    ld d, h
    ld e, l
    pop hl
    ld a, h
    cp d
    jr nz, .advance
    ld a, l
    cp e
    ret z
.advance
    ld bc, 8
    add hl, bc
    ld a, h
    cp d
    jr c, PokedexMovesMode_StorePage
    jr nz, .last_page
    ld a, l
    cp e
    jr c, PokedexMovesMode_StorePage
.last_page
    ld h, d
    ld l, e
PokedexMovesMode_StorePage:
    ld a, l
    ld [wMovesModeScroll], a
    ld a, h
    ld [wMovesModeScroll + 1], a
    scf
    ret

PokedexMovesMode_LoadSortBorder:
    ; Reuse the existing popup art and its inactive Info atlas cells.
    ld hl, PokedexPopover_BorderGFX
    ld de, wMovesModeBorderGFX
    ld bc, 8 tiles
    ld a, BANK(PokedexPopover_BorderGFX)
    call FarCopyBytes
PokedexMovesMode_UploadSortBorder:
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wMovesModeBorderGFX
    ld de, vTiles4 tile $7a
    ld c, 6
    call Pokedex_HDMATransferCacheGFX
    ld hl, wMovesModeBorderGFX + 6 tiles
    ld de, vTiles5 tile $28
    ld c, 2
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ret

PokedexMovesMode_GetMove:
    ld a, [wMovesSearchActive]
    and a
    jr z, .regular
    add hl, hl
    ld de, wMovesSearchResults
    add hl, de
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ret
.regular
    add hl, hl
    ld de, PokedexMovesModeTypeOrder
    ld a, [wMovesModeSort]
    and a
    jr z, .order
    ld de, PokedexMovesModeNameOrder
.order
    add hl, de
    ld a, BANK(PokedexMovesModeTypeOrder)
    call GetFarWord
    ret

PokedexMovesMode_IsSeen:
    push hl
    dec hl
    ld a, l
    and 7
    ld b, a
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld de, wMovesModeSeenSnapshot
    add hl, de
    ld a, [hl]
    inc b
.rotate
    rrca
    dec b
    jr nz, .rotate
    pop hl
    ret

PokedexMovesMode_SnapshotSeen:
    ; Gameplay is paused while this owner is active. Refresh on every entry.
    ld hl, wMoveDiscoverySeen
    ld de, wMovesModeSeenSnapshot
    ld b, 64
.copy
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld a, [hli]
    ld c, a
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ld a, c
    ld [de], a
    inc de
    dec b
    jr nz, .copy
    ret

PokedexMovesMode_Draw:
    farcall Pokedex_ResetArrowCursorBlink
    ld a, TRUE
    ldh [hOAMUpdate], a
    xor a
    ldh [hBGMapMode], a
    ldh [hCGBPalUpdate], a
    call PokedexMovesMode_DrawShell
    call ClearSprites
    xor a
    ld [wMovesModeRow], a
.row
    ld a, [wMovesModeScroll]
    ld l, a
    ld a, [wMovesModeScroll + 1]
    ld h, a
    ld a, [wMovesModeRow]
    ld e, a
    ld d, 0
    add hl, de
    push hl
    call PokedexMovesSearch_Count
    ld d, h
    ld e, l
    pop hl
    ld a, h
    cp d
    jr c, .valid
    jr nz, .rows_done
    ld a, l
    cp e
    jr nc, .rows_done
.valid
    call PokedexMovesMode_GetMove
    push hl
    call PokedexMovesMode_IsSeen
    jr nc, .unknown
    add hl, hl
    ld de, PokedexMovesNamePointers - 2
    add hl, de
    ld a, BANK(PokedexMovesNamePointers)
    call GetFarWord
    ld d, h
    ld e, l
    push de
    call PokedexMovesMode_RowAddress
    pop de
    ld a, BANK(MoveNames)
    call FarPlaceString
    jr .next
.unknown
    call PokedexMovesMode_RowAddress
    ld de, .Unknown
    call PlaceString
.next
    pop hl
    ld a, [wMovesModeCursor]
    ld b, a
    ld a, [wMovesModeRow]
    cp b
    jr nz, .advance
    ld a, l
    ld [wMovesModeSelected], a
    ld a, h
    ld [wMovesModeSelected + 1], a
    push hl
    call PokedexMovesMode_RowAddress
    dec hl
    ld [hl], MOVES_MODE_CURSOR_TILE
    pop hl
    call PokedexMovesMode_DrawPanel
.advance
    ld hl, wMovesModeRow
    inc [hl]
    ld a, [hl]
    cp 8
    jr nz, .row
.rows_done
    call PokedexMovesMode_DrawScrollbar
    jp PokedexMovesMode_Publish
.Unknown
    db "-----@"

PokedexMovesMode_RowAddress:
    hlcoord 7, 1
    ld a, [wMovesModeRow]
    ld de, SCREEN_WIDTH
    and a
    ret z
.row
    add hl, de
    dec a
    jr nz, .row
    ret

PokedexMovesMode_BlinkCursor:
    ld a, VBLANK_POKEDEX
    ldh [hVBlank], a
    farcall Pokedex_AdvanceArrowCursorBlink
    ld c, MOVES_MODE_CURSOR_TILE
    jr z, .position
    ld c, $32
.position
    ld a, [wJumptableIndex]
    cp DEXSTATE_MOVES_MODE_UPDATE
    jr nz, .popup
    ld a, [wMovesModeSelected]
    ld b, a
    ld a, [wMovesModeSelected + 1]
    or b
    ret z
    hlcoord 6, 1
    debgcoord 6, 1
    ld a, [wMovesModeCursor]
    ld b, a
.row
    ld a, b
    and a
    jr z, .tile
    push bc
    ld bc, SCREEN_WIDTH
    add hl, bc
    ld a, e
    add TILEMAP_WIDTH
    ld e, a
    jr nc, .next
    inc d
.next
    pop bc
    dec b
    jr .row
.popup
    hlcoord 7, 3
    debgcoord 7, 3
    ld a, [wDexArrowCursorPosIndex]
    and a
    jr z, .tile
    hlcoord 7, 5
    debgcoord 7, 5
.tile
    ld a, c
    cp [hl]
    ret z
    di
    ld [hl], a
    ld [wMovesCursorTile], a
    ld a, e
    ld [wMovesCursorAddress], a
    ld a, d
    ld [wMovesCursorAddress + 1], a
    ld a, 1
    ld [wMovesCursorPending], a
    ei
    ret

PokedexMovesMode_DrawShell:
    ld a, $32
    hlcoord 0, 0
    ld bc, SCREEN_AREA
    call ByteFill
    xor a
    hlcoord 0, 0, wAttrmap
    ld bc, SCREEN_AREA
    call ByteFill
    hlcoord 0, 0
    ld [hl], $33
    inc hl
    ld a, $34
    ld bc, 19
    call ByteFill
    hlcoord 5, 0
    ld [hl], POKEDEX_LEGACY_CAP_TILE
    hlcoord 0, 1
    ld b, 8
    ld a, $36
    call PokedexMovesMode_FillColumn
    hlcoord 5, 1
    ld b, 8
    ld a, POKEDEX_LEGACY_DIVIDER_TILE
    call PokedexMovesMode_FillColumn
    hlcoord 0, 9
    ld [hl], $71
    inc hl
    ld a, $74
    ld bc, 19
    call ByteFill
    hlcoord 5, 9
    ld [hl], $75
    hlcoord 0, 10
    ld b, 6
    ld a, $36
    call PokedexMovesMode_FillColumn
    hlcoord 0, 16
    ld [hl], $38
    inc hl
    ld a, $39
    ld bc, 19
    call ByteFill
    hlcoord 0, 17
    ld a, $31
    ld bc, 20
    call ByteFill
    ld a, [wMovesSearchActive]
    and a
    jr z, .regular_footer
    call PokedexMovesSearch_DrawFooter
    jr .footer_done
.regular_footer
    call PokedexMovesSearch_DrawCompactFooter
.footer_done
    hlcoord 19, 0
    ld [hl], MOVES_MODE_SCROLLBAR_TILE
    hlcoord 19, 1
    ld b, 8
    ld a, MOVES_MODE_SCROLLBAR_TILE + 2
    call PokedexMovesMode_FillColumn
    ld [hl], MOVES_MODE_SCROLLBAR_TILE + 4
    hlcoord 19, 0, wAttrmap
    ld b, 10
    ld a, BG_BANK1
    jp PokedexMovesMode_FillColumn

PokedexMovesMode_LoadCategoryGFX:
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld de, TMHMCaseCategoryIconGFX
    ld hl, vTiles3 tile MOVES_MODE_CATEGORY_TILE
    lb bc, BANK(TMHMCaseCategoryIconGFX), 6
    call Get2bpp
    pop af
    ldh [rVBK], a
    ret

PokedexMovesMode_LoadScrollbarGFX:
    ld hl, PokedexMovesModeScrollbarGFX
    ld de, wMovesModeBorderGFX
    ld bc, 6 tiles
    ld a, BANK(PokedexMovesModeScrollbarGFX)
    call FarCopyBytes
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wMovesModeBorderGFX
    ld de, vTiles4 tile (MOVES_MODE_SCROLLBAR_TILE - $80)
    ld c, 6
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ret

PokedexMovesMode_DrawScrollbar:
    ; Round the 16-bit viewport offset over the thumb's 65-pixel travel.
    ld a, [wMovesModeScroll]
    ld l, a
    ld a, [wMovesModeScroll + 1]
    ld h, a
    ld b, h
    ld c, l
    REPT 6
        add hl, hl
    ENDR
    add hl, bc
    push hl
    call PokedexMovesSearch_MaxScroll
    ld a, h
    or l
    jr nz, .nonzero
    pop hl
    ld b, 0
    jr .position
.nonzero
    ld b, h
    ld c, l
    srl b
    rr c
    xor a
    sub l
    ld e, a
    ld a, 0
    sbc h
    ld d, a
    pop hl
    add hl, bc
    ld b, -1
.divide
    inc b
    add hl, de
    jr c, .divide
.position
    ld a, b
    add 20
    ld hl, wShadowOAMSprite06
    ld [hli], a
    ld a, 160
    ld [hli], a
    ld a, POKEDEX_SCROLL_THUMB_TILE
    ld [hli], a
    ld [hl], 3
    ret

PokedexMovesMode_DrawPanel:
    push hl
    call ClearSprites
    pop hl
    call PokedexMovesMode_IsSeen
    ret nc
    ld b, h
    ld c, l
    ld hl, Moves
    ld a, BANK(Moves)
    call LoadIndirectPointer
    ld de, wMovesModeRecord
    ld bc, MOVE_LENGTH - 1
    call FarCopyBytes
    hlcoord 1, 3
    ld de, .Power
    call PlaceString
    ld a, [wMovesModeRecord + MOVE_POWER - 1]
    hlcoord 1, 4
    cp 2
    jr c, .power_none
    call .Number
    jr .accuracy
.power_none
    call .None
.accuracy
    hlcoord 1, 5
    ld de, .Accuracy
    call PlaceString
    hlcoord 1, 6
    ld a, [wMovesModeRecord + MOVE_EFFECT - 1]
    cp EFFECT_ALWAYS_HIT
    jr z, .accuracy_none
    ld a, [wMovesModeRecord + MOVE_ACC - 1]
    call PokedexMovesMode_Percentage
    call .Number
    jr .chance
.accuracy_none
    call .None
.chance
    hlcoord 1, 7
    ld de, .Effect
    call PlaceString
    hlcoord 1, 8
    ld a, [wMovesModeRecord + MOVE_CHANCE - 1]
    and a
    jr z, .chance_none
    call PokedexMovesMode_Percentage
    call .Number
    jr .icons
.chance_none
    call .None
.icons
    call PokedexMovesMode_PrepareIcons
    ld a, [wMovesModeSelected]
    ld c, a
    ld a, [wMovesModeSelected + 1]
    ld b, a
    ld a, BANK(MoveDescriptions)
    ld hl, MoveDescriptions
    call LoadDoubleIndirectPointer
    ret z
    ld [wMovesModeTextBank], a
    jp PokedexMovesMode_DrawDescription
.Number
    ld [wMovesModeValue], a
    ld de, wMovesModeValue
    lb bc, PRINTNUM_LEFTALIGN | 1, 3
    jp PrintNum
.None
    ld de, .Dashes
    jp PlaceString
.Power
    db "Pow@"
.Accuracy
    db "Acc@"
.Effect
    db "Eff@"
.Dashes
    db "---@"

PokedexMovesMode_AlignedIcons:
PokedexMovesMode_PrepareIcons:
    ld a, [wMovesModeTypeBuffer]
    xor 4
    ld [wMovesModeTypeBuffer], a
    ld a, [wMovesModeRecord + MOVE_TYPE - 1]
    push af
    ld c, a
    ld de, wPokedexWRAM0Scratch
    farcall PokedexInfo_CopyCompactTypeTilesByC
    pop af
    ld de, wMovesModePalettes
    call PokedexMovesMode_TypePalette
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld a, [wMovesModeTypeBuffer]
    add POKEDEX_TYPE_OBJ_TILE
    ld e, a
    ld d, 0
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    ld hl, vTiles3
    add hl, de
    ld d, h
    ld e, l
    ld hl, wPokedexWRAM0Scratch
    ld c, 4
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ld hl, wShadowOAM
    ld a, [wMovesModeTypeBuffer]
    add POKEDEX_TYPE_OBJ_TILE
    ld b, a
    ld c, 4
    ld d, 24
    ld e, 11
    ld a, OAM_BANK1 | 1
    call .Row
    ld a, [wMovesModeRecord + MOVE_POWER - 1]
    cp 2
    ld a, MOVE_CATEGORY_STATUS
    jr c, .category
    ld a, [wMovesModeRecord + MOVE_TYPE - 1]
    cp SPECIAL
    ld a, MOVE_CATEGORY_PHYSICAL
    jr c, .category
    ld a, MOVE_CATEGORY_SPECIAL
.category
    push af
    add a
    ld e, a
    ld d, 0
    ld hl, .CategoryPalettes
    add hl, de
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld de, wMovesModePalettes + 1 palettes
    ld bc, 1 palettes
    ld a, BANK(TMHMCasePhysicalCategoryIconPalette)
    call FarCopyBytes
    pop af
    add a
    add MOVES_MODE_CATEGORY_TILE
    ld b, a
    ld c, 2
    ld d, 32
    ld e, 18
    ld hl, wShadowOAMSprite04
    ld a, OAM_BANK1 | 2
.Row
    push af
.sprite
    ld a, d
    ld [hli], a
    ld a, e
    ld [hli], a
    ld a, b
    ld [hli], a
    pop af
    ld [hli], a
    inc b
    dec c
    ret z
    push af
    ld a, e
    add 8
    ld e, a
    jr .sprite
.CategoryPalettes
    dw TMHMCasePhysicalCategoryIconPalette
    dw TMHMCaseSpecialCategoryIconPalette
    dw TMHMCaseStatusCategoryIconPalette

PokedexMovesMode_FillColumn:
    ld de, SCREEN_WIDTH
.row
    ld [hl], a
    add hl, de
    dec b
    jr nz, .row
    ret

PokedexMovesMode_TypePalette:
    push de
    ld e, a
    ld d, 0
    ld hl, TypeIconPalettePointers
    add hl, de
    add hl, de
    ld a, BANK(TypeIconPalettePointers)
    call GetFarWord
    pop de
    push de
    ld bc, 1 palettes
    ld a, BANK(TypeIconPalettes)
    call FarCopyBytes
    pop hl
    ld a, [hli]
    ld b, [hl]
    inc hl
    ld [hli], a
    ld [hl], b
    ret

PokedexMovesMode_Percentage:
; Same rounding as the battle/TMHM panels, without their owner or farcall ABI.
    push hl
    ldh [hMultiplicand + 2], a
    xor a
    ldh [hMultiplicand + 1], a
    ldh [hMultiplicand], a
    ld a, 100
    ldh [hMultiplier], a
    call Multiply
    ldh a, [hProduct + 2]
    and a
    jr z, .done
    inc a
.done
    pop hl
    ret

PokedexMovesMode_DrawDescription:
    xor a
    ld [wMovesModeTextRow], a
    ld [wMovesModeTextColumn], a
    decoord 1, 10
.character
    ld a, [wMovesModeTextBank]
    call GetFarByte
    inc hl
    cp '@'
    ret z
    cp '<LINE>'
    jr z, .newline
    cp '<NEXT>'
    jr z, .newline
    cp '<LF>'
    jr z, .newline
    ld b, a
    ld a, [wMovesModeTextColumn]
    cp 19
    ret nc
    inc a
    ld [wMovesModeTextColumn], a
    ld a, b
    ld [de], a
    inc de
    jr .character
.newline
    ld a, [wMovesModeTextRow]
    inc a
    cp 6
    ret nc
    ld [wMovesModeTextRow], a
    push hl
    hlcoord 1, 10
    ld de, SCREEN_WIDTH
.advance
    add hl, de
    dec a
    jr nz, .advance
    ld d, h
    ld e, l
    pop hl
    xor a
    ld [wMovesModeTextColumn], a
    jr .character

PokedexMovesMode_StageRightEdge:
    ld hl, wPokedexOwnerTilemapBuffer + 20
    ld de, TILEMAP_WIDTH
    ld [hl], MOVES_MODE_SCROLLBAR_TILE + 1
    add hl, de
    ld b, 8
.top
    ld [hl], MOVES_MODE_SCROLLBAR_TILE + 3
    add hl, de
    dec b
    jr nz, .top
    ld [hl], MOVES_MODE_SCROLLBAR_TILE + 5
    add hl, de
    ld b, 6
.bottom
    ld [hl], $67
    add hl, de
    dec b
    jr nz, .bottom
    ld [hl], $68
    add hl, de
    ld [hl], $31
    ld hl, wPokedexOwnerAttrmapBuffer + 20
    ld b, 10
    ld a, BG_BANK1
.attrs
    ld [hl], a
    add hl, de
    dec b
    jr nz, .attrs
    ret

PokedexMovesMode_DrawSort:
    ld a, [wMovesModeSort]
    ld [wDexArrowCursorPosIndex], a
    call PokedexMovesMode_DrawPopupFrame
    call PokedexMovesMode_DrawSortRows
    jp PokedexMovesMode_Publish

PokedexMovesMode_DrawPopupFrame:
    hlcoord 7, 3
    lb bc, 3, 11
    ld a, $32
    call FillBoxWithByte
    hlcoord 7, 3, wAttrmap
    lb bc, 3, 11
    xor a
    call FillBoxWithByte
    hlcoord 6, 2
    ld [hl], $fa
    inc hl
    ld a, $fb
    ld bc, 11
    call ByteFill
    ld [hl], $fc
    hlcoord 6, 3
    ld b, 3
    ld a, $fd
    call PokedexMovesMode_FillColumn
    hlcoord 18, 3
    ld b, 3
    ld a, $29
    call PokedexMovesMode_FillColumn
    hlcoord 6, 6
    ld [hl], $fe
    inc hl
    ld a, $ff
    ld bc, 11
    call ByteFill
    ld [hl], $28
    hlcoord 6, 2, wAttrmap
    ld a, BG_BANK1
    ld bc, 13
    call ByteFill
    hlcoord 6, 6, wAttrmap
    ld bc, 13
    call ByteFill
    hlcoord 6, 2, wAttrmap
    ld b, 5
    ld a, BG_BANK1
    call PokedexMovesMode_FillColumn
    hlcoord 18, 3, wAttrmap
    ld b, 3
    ld a, BG_BANK1
    call PokedexMovesMode_FillColumn
    ret

PokedexMovesMode_DrawSortRows:
    farcall Pokedex_ResetArrowCursorBlink
    hlcoord 7, 4
    ld a, $32
    ld bc, 11
    call ByteFill
    hlcoord 7, 3
    ld bc, 11
    call ByteFill
    hlcoord 7, 5
    ld bc, 11
    call ByteFill
    ld de, .Type
    hlcoord 8, 3
    call PlaceString
    ld de, .Alphabet
    hlcoord 8, 5
    call PlaceString
    hlcoord 7, 3
    ld a, [wDexArrowCursorPosIndex]
    and a
    jr z, .cursor
    hlcoord 7, 5
.cursor
    ld [hl], MOVES_MODE_CURSOR_TILE
    ret
.Type
    db "Type@"
.Alphabet
    db "Alphabet@"

PokedexMovesMode_Publish:
    xor a
    ld [wMovesCursorPending], a
    farcall Pokedex_StageOwnerTransitionMaps
    call PokedexMovesMode_StageRightEdge
    ld hl, wMovesModePalettes
    ld de, wPokedexWRAM0Scratch
    ld bc, 2 palettes
    call CopyBytes
    ld a, BANK(wOBPals1)
    ldh [rSVBK], a
    ld hl, wPokedexWRAM0Scratch
    ld de, wOBPals1 palette 1
    ld bc, 2 palettes
    call CopyBytes
    ld hl, wPokedexWRAM0Scratch
    ld de, wOBPals2 palette 1
    ld bc, 2 palettes
    call CopyBytes
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ; Hold interrupts only around the upload, not throughout a display frame.
.near_vblank
    ldh a, [rLY]
    cp 140
    jr c, .near_vblank
    cp 144
    jr nc, .near_vblank
    di
.vblank
    ldh a, [rLY]
    cp 144
    jr c, .vblank
    farcall PokedexResults_CommitBG
    ; Reveal BG and OBJ together; neither may precede the other on entry.
    ld a, BANK(wBGPals1)
    ldh [rSVBK], a
    ld a, $80
    ldh [rBCPS], a
    ld hl, wBGPals1
    ld b, 1 palettes
.background_palette
    ld a, [hli]
    ldh [rBCPD], a
    dec b
    jr nz, .background_palette
    ld a, BANK(wOBPals1)
    ldh [rSVBK], a
    ld a, $80 | 1 palettes
    ldh [rOCPS], a
    ld hl, wOBPals1 palette 1
    ld b, 3 palettes
.palette
    ld a, [hli]
    ldh [rOCPD], a
    dec b
    jr nz, .palette
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    call hTransferShadowOAM
    xor a
    ldh [hOAMUpdate], a
    ei
    ret

PokedexMovesModeScrollbarGFX:
INCBIN "gfx/pokedex/pokedex_moves_scroll_bar_and_borders.2bpp"
ASSERT @ - PokedexMovesModeScrollbarGFX == 6 tiles

PUSHS
SECTION FRAGMENT "bank77", ROMX
PokedexMovesCursor_VBlank:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ld a, [wMovesCursorPending]
    and a
    jr z, .done
    ldh a, [rVBK]
    push af
    xor a
    ldh [rVBK], a
    ld a, [wMovesCursorAddress]
    ld l, a
    ld a, [wMovesCursorAddress + 1]
    ld h, a
    ld a, [wMovesCursorTile]
    ld [hl], a
    xor a
    ld [wMovesCursorPending], a
    pop af
    ldh [rVBK], a
.done
    pop af
    ldh [rSVBK], a
    ret
POPS

INCLUDE "build/dex-moves-mode-assets/tables.asm"

DEF MOVES_SORT_MEMORY_TAG EQU $a0

; All registers and bank ownership survive. Unknown/legacy values mean Type.
PokedexMovesMode_RestoreSort::
    push af
    push bc
    ldh a, [rSVBK]
    push af
    ld a, BANK(wLastMovesDexSort)
    ldh [rSVBK], a
    ld a, [wLastMovesDexSort]
    cp MOVES_SORT_MEMORY_TAG + 1
    ld b, 0
    jr nz, .decoded
    inc b
.decoded
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ld a, b
    ld [wMovesModeSort], a
    pop af
    ldh [rSVBK], a
    pop bc
    pop af
    ret

; A is the confirmed Type/Alphabet choice. Never write SRAM from the menu.
PokedexMovesMode_RememberSort::
    push af
    cp 2
    jr nc, .done
    push bc
    ld b, a
    ldh a, [rSVBK]
    push af
    ld a, BANK(wLastMovesDexSort)
    ldh [rSVBK], a
    ld a, b
    or MOVES_SORT_MEMORY_TAG
    ld [wLastMovesDexSort], a
    pop af
    ldh [rSVBK], a
    pop bc
.done
    pop af
    ret


; Reuse the inactive Battle Tower workspace, away from Search's VBlank mailbox.
DEF wMovesSearchActive EQU $dc40
DEF wMovesSearchCount EQU $dc41
DEF wMovesSearchBackupCursor EQU $dc43
DEF wMovesSearchBackupScroll EQU $dc44
DEF wMovesSearchType EQU $dc46
DEF wMovesSearchRow EQU $dc47
DEF wMovesSearchOrdinal EQU $dc48
DEF wMovesSearchOutput EQU $dc4a
DEF wMovesSearchKeyboard EQU $dc4c
DEF wMovesSearchLength EQU $dc4d
DEF wMovesSearchLetterCase EQU $dc4e
DEF wMovesSearchTextDelay EQU $dc4f
DEF wMovesSearchQuery EQU $dc50
DEF wMovesSearchDraft EQU $dc60
DEF wMovesSearchTextFrame EQU $dc6d
DEF wMovesSearchResults EQU $dc80
DEF wMovesSearchTextAnim EQU wMovesSearchResults
ASSERT wMovesSearchDraft + MOVE_NAME_LENGTH <= wMovesSearchTextFrame
ASSERT wMovesSearchTextAnim + SPRITEANIMSTRUCT_LENGTH <= wMovesSearchResults + NUM_ATTACKS * 2
ASSERT wPokedexInfoWorkspaceEnd <= wMovesSearchActive
ASSERT wSearchOAM + 8 * SPRITEOAMSTRUCT_LENGTH <= wMovesSearchActive
ASSERT wMovesSearchResults + NUM_ATTACKS * 2 <= $e000
DEF MOVES_SEARCH_LEFT_TILE EQU $70
DEF MOVES_SEARCH_CORNER_TILE EQU $71
DEF MOVES_SEARCH_SIDE_TILE EQU $72
DEF MOVES_SEARCH_MIDDLE_TILE EQU $73
DEF MOVES_SEARCH_UNDERLINE_TILE EQU $74
DEF MOVES_SEARCH_MIDDLELINE_TILE EQU $75
DEF MOVES_SEARCH_CURSOR_TILE EQU $76
DEF MOVES_SEARCH_FOOTER_TILE EQU $78
DEF MOVES_SEARCH_END_KEY EQU 28

PokedexMovesSearch_Reset:
    xor a
    ld hl, wMovesSearchActive
    ld bc, $40
    call ByteFill
    ld a, 1
    ld [wMovesSearchType], a
    ld a, '@'
    ld [wMovesSearchQuery], a
    ret

PokedexMovesSearch_Count:
    ld hl, NUM_ATTACKS
    ld a, [wMovesSearchActive]
    and a
    ret z
    ld a, [wMovesSearchCount]
    ld l, a
    ld a, [wMovesSearchCount + 1]
    ld h, a
    ret

PokedexMovesSearch_MaxScroll:
    call PokedexMovesSearch_Count
    ld a, l
    sub 8
    ld l, a
    ld a, h
    sbc 0
    ld h, a
    ret nc
    ld hl, 0
    ret

PokedexMovesSearch_DrawOptions:
    farcall Pokedex_ResetArrowCursorBlink
    hlcoord 7, 4
    ld a, $32
    ld bc, 11
    call ByteFill
    hlcoord 7, 3
    ld a, $32
    ld bc, 11
    call ByteFill
    hlcoord 7, 5
    ld bc, 11
    call ByteFill
    hlcoord 8, 3
    ld de, .Sort
    call PlaceString
    hlcoord 8, 5
    ld de, .Search
    call PlaceString
    hlcoord 7, 3
    ld a, [wDexArrowCursorPosIndex]
    and a
    jr z, .cursor
    hlcoord 7, 5
.cursor
    ld [hl], MOVES_MODE_CURSOR_TILE
    ret
.Sort
    db "Sort@"
.Search
    db "Search@"

PokedexMovesSearch_OptionsUpdate:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    call PokedexMovesMode_ReadInput
    call PokedexMovesMode_BlinkCursor
    ldh a, [hJoyPressed]
    and PAD_B | PAD_START
    jr nz, .close
    ldh a, [hJoyPressed]
    and PAD_UP | PAD_DOWN
    jr z, .accept
    ld a, [wDexArrowCursorPosIndex]
    xor 1
    ld [wDexArrowCursorPosIndex], a
    call PokedexMovesSearch_DrawOptions
    call PokedexMovesMode_Publish
    jr .done
.accept
    ldh a, [hJoyPressed]
    and PAD_A
    jr z, .done
    ld a, [wDexArrowCursorPosIndex]
    and a
    jr nz, .search
    call PokedexMovesMode_DrawSort
    ld a, DEXSTATE_MOVES_MODE_SORT
    ld [wJumptableIndex], a
    jr .done
.search
    ld a, [wMovesModeCursor]
    ld [wMovesSearchBackupCursor], a
    ld a, [wMovesModeScroll]
    ld [wMovesSearchBackupScroll], a
    ld a, [wMovesModeScroll + 1]
    ld [wMovesSearchBackupScroll + 1], a
    xor a
    ld [wMovesSearchRow], a
    call PokedexMovesSearch_ShowForm
    jr .done
.close
    call PokedexMovesMode_Draw
    ld a, DEXSTATE_MOVES_MODE_UPDATE
    ld [wJumptableIndex], a
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexMovesSearch_ShowForm:
    farcall PokedexSearch_Leave
    farcall PokedexListing_BeginMenuTransition
    xor a
    ld [wMovesSearchActive], a
    call PokedexMovesSearch_DrawForm
    ld a, DEXSTATE_MOVES_SEARCH
    ld [wJumptableIndex], a
    ret

PokedexMovesSearch_DrawForm:
    farcall PokedexSearch_Initialize
    farcall Pokedex_DrawSearchScreenBG
    hlcoord 2, 4
    ld de, .Type
    call PlaceString
    hlcoord 2, 6
    ld de, .Name
    call PlaceString
    ; Only the Type row has arrows; the Name field is a twelve-character input.
    hlcoord 6, 6
    ld a, $32
    ld bc, 13
    call ByteFill
    hlcoord 7, 6
    ld de, wMovesSearchQuery
    ld a, [de]
    cp '@'
    jr nz, .name
    hlcoord 10, 6
    ld de, .Empty
.name
    call PlaceString
    ld a, [wMovesSearchType]
    ld [wDexSearchMonType1], a
    xor a
    ld [wDexSearchMonType2], a
    ld [wDexSearchSlowpokeFrame], a
    farcall DoDexSearchSlowpokeFrame
    call PokedexMovesSearch_DrawCursor
    call PokedexMovesSearch_DrawType
    call WaitBGMap
    call PokedexMovesSearch_UpdateTypeIcon
    ld b, SCGB_POKEDEX_SEARCH_OPTION
    call GetSGBLayout
    farcall Pokedex_ApplyUsualPals
    xor a
    ldh [hCGBPalUpdate], a
    call PokedexMovesSearch_RevealForm
    farcall PokedexListing_RevealMenu
    ret
.Type
    db "Type @"
.Name
    db "Name @"
.Empty
    db "----@"

PokedexMovesSearch_RevealForm:
.near_vblank
    ldh a, [rLY]
    cp 140
    jr c, .near_vblank
    cp 144
    jr nc, .near_vblank
    di
.vblank
    ldh a, [rLY]
    cp 144
    jr c, .vblank
    farcall PokedexSearch_VBlank
    call hTransferShadowOAM
    xor a
    ldh [hOAMUpdate], a
    ei
    ret

PokedexMovesSearch_DrawType:
    hlcoord 8, 4
    ld a, $32
    ld bc, 8
    call ByteFill
    ld a, [wMovesSearchType]
    and a
    ret nz
    hlcoord 10, 4
    ld de, .Empty
    jp PlaceString
.Empty
    db "----@"

PokedexMovesSearch_UpdateTypeIcon:
    ld a, [wMovesSearchType]
    and a
    jr z, .blank
    farcall PokedexSearch_UpdateIcons
    ret
.blank
    ld hl, wSearchOAM
    ld bc, 8 * SPRITEOAMSTRUCT_LENGTH
    call ByteFill
    ld [wSearchStageType1], a
    ld [wSearchStageType2], a
    ld a, [wSearchIconBuffer]
    ld [wSearchStageBuffer], a
    ld a, 1
    ld [wSearchPending], a
    ldh a, [hOAMUpdate]
    and a
    ret nz
.wait
    call DelayFrame
    ld a, [wSearchPending]
    and a
    jr nz, .wait
    ret

PokedexMovesSearch_DrawCursor:
    hlcoord 1, 4
    ld [hl], $32
    hlcoord 1, 6
    ld [hl], $32
    hlcoord 2, 13
    ld [hl], $32
    hlcoord 2, 15
    ld [hl], $32
    farcall Pokedex_ResetArrowCursorBlink
    ld a, [wMovesSearchRow]
    ld [wDexArrowCursorPosIndex], a
PokedexMovesSearch_BlinkCursor:
    ld de, Pokedex_UpdateSearchScreen.ArrowCursorData + 2
    farcall Pokedex_BlinkArrowCursor
    ret

PokedexMovesSearch_Update:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    call PokedexMovesMode_ReadInput
    call PokedexMovesSearch_BlinkCursor
    ldh a, [hJoyPressed]
    and PAD_B | PAD_START
    jp nz, .cancel
    ldh a, [hJoyLast]
    bit D_UP_F, a
    jr nz, .up
    bit D_DOWN_F, a
    jr nz, .down
    ld a, [wMovesSearchRow]
    and a
    jr nz, .accept
    ldh a, [hJoyLast]
    and PAD_LEFT | PAD_RIGHT
    jr z, .accept
    bit D_LEFT_F, a
    jr nz, .previous_type
.next_type
    ld a, [wMovesSearchType]
    inc a
    cp NUM_TYPES + 1
    jr c, .type
    xor a
    jr .type
.previous_type
    ld a, [wMovesSearchType]
    sub 1
    jr nc, .type
    ld a, NUM_TYPES
.type
    ld [wMovesSearchType], a
    ld [wDexSearchMonType1], a
    call PokedexMovesSearch_DrawType
    call WaitBGMap
    call PokedexMovesSearch_UpdateTypeIcon
    jp .done
.up
    ld a, [wMovesSearchRow]
    dec a
    and 3
    jr .cursor
.down
    ld a, [wMovesSearchRow]
    inc a
    and 3
.cursor
    ld [wMovesSearchRow], a
    call PokedexMovesSearch_DrawCursor
    call WaitBGMap
    jp .done
.accept
    ldh a, [hJoyPressed]
    and PAD_A
    jp z, .done
    ld a, [wMovesSearchRow]
    and a
    jp z, .next_type
    cp 1
    jr z, .text
    cp 3
    jr z, .cancel
    call PokedexMovesSearch_Filter
    farcall AnimateDexSearchSlowpoke
    farcall PokedexSearch_Leave
    farcall PokedexListing_BeginMenuTransition
    ld a, 1
    ld [wMovesSearchActive], a
    xor a
    ld [wMovesModeCursor], a
    ld [wMovesModeScroll], a
    ld [wMovesModeScroll + 1], a
    ld a, POKEDEX_SCX
    ldh [hSCX], a
    call PokedexMovesSearch_LoadFooter
    call PokedexMovesMode_LoadCategoryGFX
    call PokedexMovesMode_Draw
    farcall PokedexListing_RevealMenu
    ld a, DEXSTATE_MOVES_MODE_UPDATE
    ld [wJumptableIndex], a
    jr .done
.text
    call PokedexMovesSearch_OpenText
    jr .done
.cancel
    farcall PokedexSearch_Leave
    farcall PokedexListing_BeginMenuTransition
    xor a
    ld [wMovesSearchActive], a
    ld a, [wMovesSearchBackupCursor]
    ld [wMovesModeCursor], a
    ld a, [wMovesSearchBackupScroll]
    ld [wMovesModeScroll], a
    ld a, [wMovesSearchBackupScroll + 1]
    ld [wMovesModeScroll + 1], a
    ld a, POKEDEX_SCX
    ldh [hSCX], a
    call PokedexMovesMode_LoadCategoryGFX
    call PokedexMovesMode_Draw
    farcall PokedexListing_RevealMenu
    ld a, DEXSTATE_MOVES_MODE_UPDATE
    ld [wJumptableIndex], a
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexMovesSearch_Filter:
    ; Permanent IDs only; no transient conversion, sorting or discovery writes.
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    xor a
    ld [wMovesSearchActive], a
    ld [wMovesSearchCount], a
    ld [wMovesSearchCount + 1], a
    ld [wMovesSearchOrdinal], a
    ld [wMovesSearchOrdinal + 1], a
    ld hl, wMovesSearchResults
    ld a, l
    ld [wMovesSearchOutput], a
    ld a, h
    ld [wMovesSearchOutput + 1], a
.move
    ld a, [wMovesSearchOrdinal]
    ld l, a
    ld a, [wMovesSearchOrdinal + 1]
    ld h, a
    call PokedexMovesMode_GetMove
    push hl
    call PokedexMovesMode_IsSeen
    jr nc, .next
    ld a, [wMovesSearchType]
    and a
    jr z, .name
    push hl
    call PokedexMovesSearch_ConvertType
    push af
    ld hl, sp + 2
    ld c, [hl]
    inc hl
    ld b, [hl]
    ld a, BANK(Moves)
    ld hl, Moves
    call LoadIndirectPointer
    push af
    ld bc, MOVE_TYPE - 1
    add hl, bc
    pop af
    call GetFarByte
    ld b, a
    pop af
    cp b
    pop hl
    jr nz, .next
.name
    ld a, [wMovesSearchQuery]
    cp '@'
    jr z, .emit
    add hl, hl
    ld de, PokedexMovesNamePointers - 2
    add hl, de
    ld a, BANK(PokedexMovesNamePointers)
    call GetFarWord
    call PokedexMovesSearch_Matches
    jr nc, .next
.emit
    pop de
    ld a, [wMovesSearchOutput]
    ld l, a
    ld a, [wMovesSearchOutput + 1]
    ld h, a
    ld a, e
    ld [hli], a
    ld a, d
    ld [hli], a
    ld a, l
    ld [wMovesSearchOutput], a
    ld a, h
    ld [wMovesSearchOutput + 1], a
    ld hl, wMovesSearchCount
    inc [hl]
    jr nz, .advance
    inc hl
    inc [hl]
    jr .advance
.next
    pop hl
.advance
    ld hl, wMovesSearchOrdinal
    inc [hl]
    jr nz, .count
    inc hl
    inc [hl]
.count
    ld a, [wMovesSearchOrdinal + 1]
    cp HIGH(NUM_ATTACKS)
    jp nz, .move
    ld a, [wMovesSearchOrdinal]
    cp LOW(NUM_ATTACKS)
    jp nz, .move
    pop af
    ldh [rSVBK], a
    ret

PokedexMovesSearch_Matches:
    ; Copy once, then match in scratch without a bank switch per character.
    ld a, [wMovesSearchQuery]
    cp '@'
    jr z, .yes
    ld de, wPokedexWRAM0Scratch
    ld bc, MOVE_NAME_LENGTH
    ld a, BANK(MoveNames)
    call FarCopyBytes
    ld hl, wPokedexWRAM0Scratch
.start
    push hl
    ld de, wMovesSearchQuery
.character
    ld a, [de]
    cp '@'
    jr z, .found
    call PokedexMovesSearch_Fold
    ld b, a
    ld a, [hl]
    cp '@'
    jr z, .ended
    call PokedexMovesSearch_Fold
    cp b
    jr nz, .mismatch
    inc hl
    inc de
    jr .character
.mismatch
    pop hl
    inc hl
    jr .start
.ended
    pop hl
    and a
    ret

.found
    pop hl
.yes
    scf
    ret

PokedexMovesSearch_ConvertType:
    dec a
    ld e, a
    ld d, 0
    ld hl, PokedexTypeSearchConversionTable
    add hl, de
    ld a, BANK(PokedexTypeSearchConversionTable)
    jp GetFarByte

PokedexMovesSearch_Fold:
    cp 'A'
    ret c
    cp 'Z' + 1
    ret nc
    add 'a' - 'A'
    ret

PokedexMovesSearch_DrawCompactFooter:
    ld hl, String_SELECT_MODE
    decoord 1, 17
    ld bc, 7
    ld a, BANK(String_SELECT_MODE)
    call FarCopyBytes
    ld a, $3c
    ld [de], a
    ld hl, String_START_OPTION + 1
    decoord 10, 17
    ld bc, 9
    ld a, BANK(String_START_OPTION)
    jp FarCopyBytes

PokedexMovesSearch_LoadFooter:
    ld hl, PokedexMovesSearchFooterGFX
    ld de, wPokedexWRAM0Scratch
    ld bc, 8 tiles
    ld a, BANK(PokedexMovesSearchFooterGFX)
    call FarCopyBytes
    call PokedexMovesSearch_ShiftFooter
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wPokedexWRAM0Scratch
    ld de, vTiles5 tile MOVES_SEARCH_FOOTER_TILE
    ld c, 8
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ret

PokedexMovesSearch_ShiftFooter:
    ; The supplied badge has four empty pixels on its left; retain all artwork.
    ld hl, wPokedexWRAM0Scratch
    ld b, 8 tiles
.byte
    ld a, [hl]
    add a
    add a
    add a
    ld c, a
    ld a, b
    cp 1 tiles + 1
    jr c, .background
    push hl
    ld de, 1 tiles
    add hl, de
    ld a, [hl]
    pop hl
    jr .next
.background
    ld a, b
    and 1
    ld a, 0
    jr nz, .next
    dec a
.next
    rlca
    rlca
    rlca
    and 7
    or c
    ld [hli], a
    dec b
    jr nz, .byte
    ret

PokedexMovesSearch_DrawFooter:
    hlcoord 7, 17
    ld a, MOVES_SEARCH_FOOTER_TILE
    ld b, 8
.tile
    ld [hli], a
    inc a
    dec b
    jr nz, .tile
    hlcoord 7, 17, wAttrmap
    ld a, BG_BANK1
    ld bc, 8
    call ByteFill
    ld a, [wMovesSearchCount]
    ld b, a
    ld a, [wMovesSearchCount + 1]
    or b
    ret nz
    hlcoord 7, 1
    ld de, .None
    jp PlaceString
.None
    db "No matches.@"

PokedexMovesSearch_OpenText:
    farcall PokedexSearch_Leave
    ld b, SCGB_POKEDEX_SEARCH_OPTION
    call GetSGBLayout
    farcall Pokedex_ApplyUsualPals
    farcall PokedexListing_BeginMenuTransition
    ld hl, wMovesSearchQuery
    ld de, wMovesSearchDraft
    ld bc, MOVE_NAME_LENGTH
    call CopyBytes
    xor a
    ld [wMovesSearchKeyboard], a
    ld [wMovesSearchLetterCase], a
    ld hl, wMovesSearchDraft
    ld b, 0
.length
    ld a, [hli]
    cp '@'
    jr z, .end
    inc b
    jr .length
.end
    ld a, b
    ld [wMovesSearchLength], a
    call PokedexMovesSearch_LoadTextBorder
    call PokedexMovesSearch_InitTextCursor
    call PokedexMovesSearch_DrawText
    ld a, DEXSTATE_MOVES_TEXT_ENTRY
    ld [wJumptableIndex], a
    ret

PokedexMovesSearch_LoadTextBorder:
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld de, PokedexMovesSearchLeftGFX
    ld hl, vTiles5 tile MOVES_SEARCH_LEFT_TILE
    lb bc, BANK(PokedexMovesSearchLeftGFX), 1
    call Get2bpp
    ld de, PokedexMovesSearchExistingBorderGFX
    ld hl, vTiles5 tile MOVES_SEARCH_CORNER_TILE
    lb bc, BANK(PokedexMovesSearchExistingBorderGFX), 2
    call Get2bpp
    ld de, PokedexListJoinedMiddleGFX
    ld hl, vTiles5 tile MOVES_SEARCH_MIDDLE_TILE
    lb bc, BANK(PokedexListJoinedMiddleGFX), 1
    call Get2bpp
    ld hl, NamingScreenGFX_UnderLine
    call .Line
    ld de, vTiles5 tile MOVES_SEARCH_UNDERLINE_TILE
    call .UploadLine
    ld hl, NamingScreenGFX_MiddleLine
    call .Line
    ld de, vTiles5 tile MOVES_SEARCH_MIDDLELINE_TILE
    call .UploadLine
    ld de, NamingScreenGFX_Cursor
    ld hl, vTiles3 tile MOVES_SEARCH_CURSOR_TILE
    lb bc, BANK(NamingScreenGFX_Cursor), 2
    call Get2bpp
    pop af
    ldh [rVBK], a
    ld a, BANK(wOBPals1)
    ldh [rSVBK], a
    ld hl, .CursorPalette
    ld de, wOBPals1
    ld bc, 1 palettes
    ld a, BANK(.CursorPalette)
    call FarCopyBytes
    ld hl, .CursorPalette
    ld de, wOBPals2
    ld bc, 1 palettes
    ld a, BANK(.CursorPalette)
    call FarCopyBytes
    ld a, 3
    ldh [rSVBK], a
    ret
.Line
    ld de, wPokedexWRAM0Scratch
    ld c, 8
.underline
    ld a, BANK(NamingScreenGFX_UnderLine)
    call GetFarByte
    inc hl
    ld b, a
    xor a
    ld [de], a
    inc de
    ld a, b
    cpl
    ld [de], a
    inc de
    dec c
    jr nz, .underline
    ret
.UploadLine
    ld hl, wPokedexWRAM0Scratch
    ld c, 1
    jp Pokedex_HDMATransferCacheGFX
.CursorPalette
    dw 0, $7fff, $7fff, $7fff
ASSERT BANK(NamingScreenGFX_MiddleLine) == BANK(NamingScreenGFX_UnderLine)

PokedexMovesSearch_InitTextCursor:
    xor a
    ld hl, wMovesSearchTextAnim
    ld bc, SPRITEANIMSTRUCT_LENGTH
    call ByteFill
    ld a, SPRITE_ANIM_FRAMESET_TEXT_ENTRY_CURSOR
    ld [wMovesSearchTextAnim + SPRITEANIMSTRUCT_FRAMESET_ID], a
    ld a, -1
    ld [wMovesSearchTextAnim + SPRITEANIMSTRUCT_FRAME], a
    ld a, 2
    ld [wMovesSearchTextDelay], a
    jp PokedexMovesSearch_NextTextCursorFrame

PokedexMovesSearch_NextTextCursorFrame:
    ld a, [wCurSpriteOAMFlags]
    push af
    ld bc, wMovesSearchTextAnim
    farcall GetSpriteAnimFrame
    ; FarCall preserves flags but not A; read the selected shared frame tag.
    ld a, [wMovesSearchTextAnim + SPRITEANIMSTRUCT_FRAMESET_ID]
    ld e, a
    ld d, 0
    ld hl, SpriteAnimFrameData
    add hl, de
    add hl, de
    ld a, BANK(SpriteAnimFrameData)
    call GetFarWord
    ld a, [wMovesSearchTextAnim + SPRITEANIMSTRUCT_FRAME]
    add a
    ld e, a
    add hl, de
    ld a, BANK(SpriteAnimFrameData)
    call GetFarByte
    ld [wMovesSearchTextFrame], a
    pop af
    ld [wCurSpriteOAMFlags], a
    ret

PokedexMovesSearch_AnimateTextCursor:
    ; NamingScreen advances this frameset between two DelayFrame calls.
    ld hl, wMovesSearchTextDelay
    dec [hl]
    ret nz
    ld [hl], 2
    call PokedexMovesSearch_NextTextCursorFrame
    jp PokedexMovesSearch_DrawTextCursor

PokedexMovesSearch_DrawText:
    ld a, TRUE
    ldh [hOAMUpdate], a
    call ClearSprites
    ld a, $31
    hlcoord 0, 0
    ld bc, SCREEN_AREA
    call ByteFill
    xor a
    hlcoord 0, 0, wAttrmap
    ld bc, SCREEN_AREA
    call ByteFill
    ld a, $32
    hlcoord 1, 1
    lb bc, 15, 18
    call ClearBox
    ; The original corner/side face right; flip only the left-hand cells.
    hlcoord 0, 0
    ld [hl], MOVES_SEARCH_CORNER_TILE
    hlcoord 19, 0
    ld [hl], MOVES_SEARCH_CORNER_TILE
    hlcoord 0, 0, wAttrmap
    ld [hl], BG_BANK1 | BG_XFLIP
    hlcoord 19, 0, wAttrmap
    ld [hl], BG_BANK1
    hlcoord 1, 0
    ld a, $34
    ld bc, 18
    call ByteFill
    hlcoord 0, 1
    ld a, MOVES_SEARCH_SIDE_TILE
    ld b, 15
    call PokedexMovesMode_FillColumn
    hlcoord 19, 1
    ld b, 15
    call PokedexMovesMode_FillColumn
    hlcoord 0, 1, wAttrmap
    ld a, BG_BANK1 | BG_XFLIP
    ld b, 15
    call PokedexMovesMode_FillColumn
    hlcoord 19, 1, wAttrmap
    ld a, BG_BANK1
    ld b, 15
    call PokedexMovesMode_FillColumn
    hlcoord 0, 16
    ld [hl], MOVES_SEARCH_CORNER_TILE
    hlcoord 19, 16
    ld [hl], MOVES_SEARCH_CORNER_TILE
    hlcoord 0, 16, wAttrmap
    ld [hl], BG_BANK1 | BG_XFLIP | BG_YFLIP
    hlcoord 19, 16, wAttrmap
    ld [hl], BG_BANK1 | BG_YFLIP
    hlcoord 1, 16
    ld a, $39
    ld bc, 18
    call ByteFill
    hlcoord 0, 7
    ld [hl], MOVES_SEARCH_LEFT_TILE
    hlcoord 19, 7
    ld [hl], MOVES_SEARCH_LEFT_TILE
    hlcoord 0, 7, wAttrmap
    ld [hl], BG_BANK1
    hlcoord 19, 7, wAttrmap
    ld [hl], BG_BANK1 | BG_XFLIP
    hlcoord 1, 7
    ld a, MOVES_SEARCH_MIDDLE_TILE
    ld bc, 18
    call ByteFill
    hlcoord 1, 7, wAttrmap
    ld a, BG_BANK1
    ld bc, 18
    call ByteFill
    hlcoord 3, 2
    ld de, .Prompt
    call PlaceString
    hlcoord 3, 6
    ld a, MOVES_SEARCH_MIDDLELINE_TILE
    ld bc, 12
    call ByteFill
    hlcoord 3, 6, wAttrmap
    ld a, BG_BANK1
    ld bc, 12
    call ByteFill
    ld a, [wMovesSearchLength]
    cp MOVE_NAME_LENGTH - 1
    jr nc, .text
    ld e, a
    ld d, 0
    hlcoord 3, 6
    add hl, de
    ld [hl], MOVES_SEARCH_UNDERLINE_TILE
.text
    hlcoord 3, 6
    ld de, wMovesSearchDraft
    call PlaceString
    ld a, [wMovesSearchLength]
    ld b, a
    and a
    jr z, .keyboard
    hlcoord 3, 6, wAttrmap
    xor a
.letter_attribute
    ld [hli], a
    dec b
    jr nz, .letter_attribute
.keyboard
    hlcoord 2, 8
    ld de, .UpperKeyboard
    ld a, [wMovesSearchLetterCase]
    and a
    jr z, .case_ready
    ld de, .LowerKeyboard
.case_ready
    ld b, 4
.row
    push hl
    ld c, 9
.key
    ld a, [de]
    inc de
    ld [hli], a
    inc hl
    dec c
    jr nz, .key
    pop hl
    push de
    ld de, 2 * SCREEN_WIDTH
    add hl, de
    pop de
    dec b
    jr nz, .row
    hlcoord 15, 15
    ld de, .End
    call PlaceString
    call PokedexMovesSearch_DrawTextCursor
    call PokedexMovesSearch_PublishText
    farcall PokedexListing_RevealMenu
    ret
.Prompt
    db "Enter text to"
    next "search for."
    db "@"
.End
    db "End@"
.UpperKeyboard
    db "ABCDEFGHI"
    db "JKLMNOPQR"
    db "STUVWXYZ "
    db "-        "
.LowerKeyboard
    db "abcdefghi"
    db "jklmnopqr"
    db "stuvwxyz "
    db "-        "
; Match NamingScreen's letter and five-tile command boxes exactly.
.LetterCursor
    db -1, -1, 0, 0
    db -1,  0, 0, OAM_XFLIP
    db  0, -1, 0, OAM_YFLIP
    db  0,  0, 0, OAM_XFLIP | OAM_YFLIP
.CommandCursor
    db -1,  0, 0, 0
    db -1,  8, 1, 0
    db -1, 16, 1, 0
    db -1, 24, 1, 0
    db -1, 32, 0, OAM_XFLIP
    db  0,  0, 0, OAM_YFLIP
    db  0,  8, 1, OAM_YFLIP
    db  0, 16, 1, OAM_YFLIP
    db  0, 24, 1, OAM_YFLIP
    db  0, 32, 0, OAM_XFLIP | OAM_YFLIP

PokedexMovesSearch_StandardEndCursor:
PokedexMovesSearch_DrawTextCursor:
    ldh a, [hOAMUpdate]
    push af
    ld a, TRUE
    ldh [hOAMUpdate], a
    call ClearSprites
    ld a, [wMovesSearchKeyboard]
    cp MOVES_SEARCH_END_KEY
    ld a, SPRITE_ANIM_FRAMESET_TEXT_ENTRY_CURSOR
    jr nz, .frameset
    inc a
.frameset
    ld [wMovesSearchTextAnim + SPRITEANIMSTRUCT_FRAMESET_ID], a
    ld a, [wMovesSearchTextFrame]
    cp oamwait_command
    jr z, .done
    ld a, [wMovesSearchKeyboard]
    cp MOVES_SEARCH_END_KEY
    jr nz, .letter_cursor
    ld b, 136
    ld c, 120
    ld de, PokedexMovesSearch_DrawText.CommandCursor
    ld a, 10
    jr .cursor
.letter_cursor
    ld b, 0
.divide
    cp 9
    jr c, .column
    sub 9
    inc b
    jr .divide
.column
    add a
    add a
    add a
    add a
    add 24
    ld c, a
    ld a, b
    swap a
    add 80
    ld b, a
    ld de, PokedexMovesSearch_DrawText.LetterCursor
    ld a, 4
.cursor
    ld hl, wShadowOAM
.sprite
    push af
    ld a, [de]
    inc de
    add b
    ld [hli], a
    ld a, [de]
    inc de
    add c
    ld [hli], a
    ld a, [de]
    inc de
    add MOVES_SEARCH_CURSOR_TILE
    ld [hli], a
    ld a, [de]
    inc de
    or OAM_BANK1
    ld [hli], a
    pop af
    dec a
    jr nz, .sprite
.done
    pop af
    ldh [hOAMUpdate], a
    ret

PokedexMovesSearch_PublishText:
    ld a, TRUE
    ldh [hOAMUpdate], a
    xor a
    ldh [hBGMapMode], a
    ldh [hCGBPalUpdate], a
    farcall Pokedex_StageOwnerTransitionMaps
.near_vblank
    ldh a, [rLY]
    cp 140
    jr c, .near_vblank
    cp 144
    jr nc, .near_vblank
    di
    ; A VBlank interrupt between the LY check and DI can consume the window.
    ldh a, [rLY]
    cp 144
    jr c, .vblank
    ei
    jr .near_vblank
.vblank
    ldh a, [rLY]
    cp 144
    jr c, .vblank
    farcall PokedexResults_CommitBG
    ld a, BANK(wBGPals1)
    ldh [rSVBK], a
    ld a, $80
    ldh [rBCPS], a
    ld hl, wBGPals1
    ld b, 1 palettes
.palette
    ld a, [hli]
    ldh [rBCPD], a
    dec b
    jr nz, .palette
    ld a, $80
    ldh [rOCPS], a
    ld hl, wOBPals1
    ld b, 1 palettes
.cursor_palette
    ld a, [hli]
    ldh [rOCPD], a
    dec b
    jr nz, .cursor_palette
    ld a, 3
    ldh [rSVBK], a
    call hTransferShadowOAM
    xor a
    ldh [hOAMUpdate], a
    ei
    ret

PokedexMovesSearch_TextUpdate:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    call PokedexMovesMode_ReadInput
    ldh a, [hJoyPressed]
    bit A_BUTTON_F, a
    jp nz, .insert
    bit B_BUTTON_F, a
    jp nz, .delete
    bit START_F, a
    jr nz, .start
    bit SELECT_F, a
    jr nz, .toggle_case
    ldh a, [hJoyLast]
    bit D_LEFT_F, a
    jr nz, .left
    bit D_RIGHT_F, a
    jr nz, .right
    bit D_UP_F, a
    jr nz, .up
    bit D_DOWN_F, a
    jr nz, .down
    jp .done
.left
    ld hl, .Left
    jr .move
.right
    ld hl, .Right
    jr .move
.up
    ld hl, .Up
    jr .move
.down
    ld hl, .Down
.move
    ld a, [wMovesSearchKeyboard]
    ld e, a
    ld d, 0
    add hl, de
    ld a, [hl]
    jr .position
.start
    ld a, MOVES_SEARCH_END_KEY
.position
    ld [wMovesSearchKeyboard], a
    jr .draw
.toggle_case
    ld a, [wMovesSearchLetterCase]
    xor 1
    ld [wMovesSearchLetterCase], a
    jr .draw
.delete
    ld a, [wMovesSearchLength]
    and a
    jp z, .done
    dec a
    ld [wMovesSearchLength], a
    ld e, a
    ld d, 0
    ld hl, wMovesSearchDraft
    add hl, de
    ld [hl], '@'
    jr .draw
.insert
    ld a, [wMovesSearchKeyboard]
    cp MOVES_SEARCH_END_KEY
    jr z, .confirm
    ld a, [wMovesSearchLength]
    cp MOVE_NAME_LENGTH - 1
    jr nc, .done
    ld e, a
    ld d, 0
    ld hl, wMovesSearchDraft
    add hl, de
    push hl
    ld a, [wMovesSearchKeyboard]
    ld e, a
    ld hl, .UpperCharacters
    ld a, [wMovesSearchLetterCase]
    and a
    jr z, .character_case_ready
    ld hl, .Characters
.character_case_ready
    add hl, de
    ld a, [hl]
    pop hl
    ld [hli], a
    ld [hl], '@'
    ld hl, wMovesSearchLength
    inc [hl]
    ld a, [hl]
    cp MOVE_NAME_LENGTH - 1
    jr z, .start
.draw
    call PokedexMovesSearch_DrawText
    jr .done
.confirm
    ld hl, wMovesSearchDraft
    ld de, wMovesSearchQuery
    ld bc, MOVE_NAME_LENGTH
    call CopyBytes
    call PokedexMovesSearch_ShowForm
.done
    ld a, [wJumptableIndex]
    cp DEXSTATE_MOVES_TEXT_ENTRY
    call z, PokedexMovesSearch_AnimateTextCursor
    pop af
    ldh [rSVBK], a
    ret
.Characters
    db "abcdefghijklmnopqrstuvwxyz -"
.UpperCharacters
    db "ABCDEFGHIJKLMNOPQRSTUVWXYZ -"
; END is one command, not three character keys. Skip the blank lower cells.
.Left
    db 8, 0, 1, 2, 3, 4, 5, 6, 7
    db 17, 9, 10, 11, 12, 13, 14, 15, 16
    db 26, 18, 19, 20, 21, 22, 23, 24, 25
    db 28, 27
.Right
    db 1, 2, 3, 4, 5, 6, 7, 8, 0
    db 10, 11, 12, 13, 14, 15, 16, 17, 9
    db 19, 20, 21, 22, 23, 24, 25, 26, 18
    db 28, 27
.Up
    db 27, 27, 27, 27, 27, 28, 28, 28, 28
    db 0, 1, 2, 3, 4, 5, 6, 7, 8
    db 9, 10, 11, 12, 13, 14, 15, 16, 17
    db 18, 25
.Down
    db 9, 10, 11, 12, 13, 14, 15, 16, 17
    db 18, 19, 20, 21, 22, 23, 24, 25, 26
    db 27, 27, 27, 27, 27, 28, 28, 28, 28
    db 28, 7

PokedexMovesSearchLeftGFX:
    INCBIN "gfx/pokedex/pokedex_moves_search_left_border.2bpp"
ASSERT @ - PokedexMovesSearchLeftGFX == 1 tiles
PokedexMovesSearchExistingBorderGFX:
    INCBIN "gfx/pokedex/pokedex.2bpp", 58 tiles, 2 tiles
PokedexMovesSearchFooterGFX:
    INCBIN "gfx/pokedex/pokedex_search_results_footer.2bpp"
ASSERT @ - PokedexMovesSearchFooterGFX == 8 tiles
