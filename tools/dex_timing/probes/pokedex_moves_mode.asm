; Visual-only owner. Discovery and save storage are deliberately deferred.
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
DEF wMovesModeBorderGFX  EQUS "wPokedexInfoGFX + 3 tiles"
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
    call ClearSprites
    farcall Pokedex_CancelAnimationPrefetch
    call PokedexMovesMode_LoadScrollbarGFX
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
    ldh a, [hJoyPressed]
    and PAD_B | PAD_SELECT
    jp nz, .leave
    ldh a, [hJoyPressed]
    and PAD_START
    jp nz, .sort
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
    ld hl, wMovesModeScroll
    ld [hl], LOW(NUM_ATTACKS - 8)
    inc hl
    ld [hl], HIGH(NUM_ATTACKS - 8)
    ld a, 7
    ld [wMovesModeCursor], a
    jr .draw
.down
    call PokedexMovesMode_Ordinal
    ld de, NUM_ATTACKS - 1
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
.sort
    call PokedexMovesMode_DrawSort
    ld a, DEXSTATE_MOVES_MODE_SORT
    ld [wJumptableIndex], a
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
    ld de, NUM_ATTACKS - 8
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
IF DEF(DEX_MOVES_MODE_UNKNOWN)
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
    ld de, PokedexMovesModeSeenFixture
    add hl, de
    ld a, [hl]
    inc b
.rotate
    rrca
    dec b
    jr nz, .rotate
    pop hl
    ret
ELSE
    scf
    ret
ENDC

PokedexMovesMode_Draw:
    ld a, TRUE
    ldh [hOAMUpdate], a
    xor a
    ldh [hBGMapMode], a
    ldh [hCGBPalUpdate], a
    call PokedexMovesMode_DrawShell
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
    ld hl, String_SELECT_MODE
    decoord 1, 17
    ld bc, 18
    ld a, BANK(String_SELECT_MODE)
    call FarCopyBytes
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
    ld bc, (NUM_ATTACKS - 8) / 2
    add hl, bc
    ld de, -(NUM_ATTACKS - 8)
    ld b, -1
.divide
    inc b
    add hl, de
    jr c, .divide
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
    ld e, 10
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
    call PokedexMovesMode_DrawSortRows
    jp PokedexMovesMode_Publish

PokedexMovesMode_DrawSortRows:
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

INCLUDE "build/dex-moves-mode-assets/tables.asm"
IF DEF(DEX_MOVES_MODE_UNKNOWN)
PokedexMovesModeSeenFixture:
INCLUDE "build/dex-moves-mode-assets/seen.asm"
ENDC
