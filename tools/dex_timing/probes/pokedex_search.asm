; Private Search owner. Borrow inactive Info/Battle Tower work, not new RAM.
SECTION FRAGMENT "Pokedex Search Prototype", ROMX

DEF wSearchRecords EQU $d480
DEF wSearchPending EQU $dc00
DEF wSearchStageBuffer EQU $dc01
DEF wSearchIconBuffer EQU $dc02
DEF wSearchStageType1 EQU $dc03
DEF wSearchStageType2 EQU $dc04
DEF wSearchIconType1 EQU $dc05
DEF wSearchIconType2 EQU $dc06
DEF wSearchOAM EQU $dc10
DEF wSearchOutput EQUS "wPokedexNameBuffer"
DEF wSearchGroup EQUS "wPokedexNameBuffer + 2"
DEF wSearchType2 EQUS "wPokedexNameBuffer + 3"
DEF wSearchIconPalettes EQUS "wPokedexWRAM0Scratch + 8 tiles"
ASSERT wSearchRecords + NUM_POKEMON * 3 <= wSearchPending
ASSERT wPokedexWRAM0Scratch + 10 tiles <= wPokedexWRAM0ScratchEnd

PokedexSearch_Initialize:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    xor a
    ld [wSearchPending], a
    ld a, 8
    ld [wSearchIconBuffer], a
    ld a, $ff
    ld [wSearchIconType1], a
    ld [wSearchIconType2], a
    pop af
    ldh [rSVBK], a
    ld a, VBLANK_POKEDEX
    ldh [hVBlank], a
    ret

PokedexSearch_DrawFields:
    xor a
    ldh [hBGMapMode], a
    hlcoord 9, 3
    ld de, SCREEN_WIDTH - 8
    ld b, 4
.row
    ld c, 8
    ld a, ' '
.column
    ld [hli], a
    dec c
    jr nz, .column
    add hl, de
    dec b
    jr nz, .row
    farcall PokedexSearch_DrawFieldText
    ret

PokedexSearch_ConvertType:
    and a
    jr nz, .real
    ld a, $ff
    ret
.real
    ld e, a
    ld d, 0
    ld hl, PokedexTypeSearchConversionTable - 1
    add hl, de
    ld a, BANK(PokedexTypeSearchConversionTable)
    jp GetFarByte

PokedexSearch_UpdateIcons:
    ldh a, [hCGB]
    and a
    ret z
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    ld a, [wSearchIconType1]
    ld b, a
    ld a, [wDexSearchMonType1]
    cp b
    jr nz, .changed
    ld a, [wSearchIconType2]
    ld b, a
    ld a, [wDexSearchMonType2]
    cp b
    jp z, .restore
.changed
    ld a, [wDexSearchMonType1]
    ld [wSearchStageType1], a
    call PokedexSearch_ConvertType
    push af
    ld c, a
    ld de, wPokedexWRAM0Scratch
    farcall PokedexInfo_CopyCompactTypeTilesByC
    pop af
    ld de, wSearchIconPalettes
    call .Palette
    ld a, [wDexSearchMonType2]
    ld [wSearchStageType2], a
    and a
    jr nz, .second
    ld hl, wSearchIconPalettes + 1 palettes
    ld bc, 1 palettes
    call ByteFill
    jr .upload
.second
    call PokedexSearch_ConvertType
    push af
    ld c, a
    ld de, wPokedexWRAM0Scratch + 4 tiles
    farcall PokedexInfo_CopyCompactTypeTilesByC
    pop af
    ld de, wSearchIconPalettes + 1 palettes
    call .Palette
.upload
    ld a, [wSearchIconBuffer]
    xor 8
    ld [wSearchStageBuffer], a
    ld de, vTiles3 tile POKEDEX_TYPE_OBJ_TILE
    and a
    jr z, .destination
    ld de, vTiles3 tile (POKEDEX_TYPE_OBJ_TILE + 8)
.destination
    ld hl, wPokedexWRAM0Scratch
    ld c, 4
    ld a, [wSearchStageType2]
    and a
    jr z, .transfer
    ld c, 8
.transfer
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ld a, [wSearchStageBuffer]
    add POKEDEX_TYPE_OBJ_TILE
    ld b, a
    ld hl, wSearchOAM
    ld c, 4
    ld d, 48 ; Search row 4: screen y=32
    ld e, OAM_BANK1 | 1
    call .OAM
    ld a, [wSearchStageType2]
    and a
    jr z, .none
    ld c, 4
    ld d, 64 ; Search row 6: screen y=48
    ld e, OAM_BANK1 | 2
    call .OAM
    jr .queue
.none
    ld bc, 16
    xor a
    call ByteFill
.queue
    ; Publish palettes and OAM together, even if normal BG work is pending.
    di
    ld a, BANK(wOBPals1)
    ldh [rSVBK], a
    ld hl, wSearchIconPalettes
    ld de, wOBPals1 palette 1
    ld bc, 2 palettes
    call CopyBytes
    ld hl, wSearchIconPalettes
    ld de, wOBPals2 palette 1
    ld bc, 2 palettes
    call CopyBytes
    ld a, 3
    ldh [rSVBK], a
    ld a, 1
    ld [wSearchPending], a
    ei
    ldh a, [hOAMUpdate]
    and a
    jr nz, .restore ; hidden initialization is revealed by the destination
.wait
    call DelayFrame
    ld a, [wSearchPending]
    and a
    jr nz, .wait
.restore
    pop af
    ldh [rSVBK], a
    ret
.Palette
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
.OAM
    push bc
    ld a, d
    ld [hli], a
    pop bc
    ld a, 96 ; centered in the existing field: screen x=88
.sprites
    ld [hli], a
    ld a, b
    ld [hli], a
    ld a, e
    ld [hli], a
    inc b
    dec c
    ret z
    ld a, d
    ld [hli], a
    ; Derive the next x from the current tile's position within this badge.
    push bc
    ld a, b
    and 3
    add a
    add a
    add a
    add 96
    pop bc
    jr .sprites

SECTION FRAGMENT "bank77", ROMX
PokedexSearch_VBlank:
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    ld a, [wSearchPending]
    and a
    jr z, .done
    ld hl, wSearchOAM
    ld de, wShadowOAMSprite09
    ld bc, 8 * SPRITEOAMSTRUCT_LENGTH
    call CopyBytes
    ldh a, [rVBK]
    push af
    xor a
    ldh [rVBK], a
    hlcoord 9, 4
    debgcoord 9, 4
    rept 8
        ld a, [hli]
        ld [de], a
        inc de
    endr
    hlcoord 9, 6
    debgcoord 9, 6
    rept 8
        ld a, [hli]
        ld [de], a
        inc de
    endr
    pop af
    ldh [rVBK], a
    call ForceUpdateCGBPals
    ld a, [wSearchStageBuffer]
    ld [wSearchIconBuffer], a
    ld a, [wSearchStageType1]
    ld [wSearchIconType1], a
    ld a, [wSearchStageType2]
    ld [wSearchIconType2], a
    xor a
    ld [wSearchPending], a
.done
    pop af
    ldh [rSVBK], a
    ret

ASSERT BANK(PokedexSearch_VBlank) == BANK(Pokedex_VBlankDispatch)
SECTION FRAGMENT "Pokedex Search Prototype", ROMX
PokedexSearch_Leave:
    xor a
    ldh [hVBlank], a
    ldh a, [rSVBK]
    push af
    ld a, 3
    ldh [rSVBK], a
    xor a
    ld [wSearchPending], a
    pop af
    ldh [rSVBK], a
    ret

PokedexSearch_Filter:
    ldh a, [rSVBK]
    push af
    ld a, [wDexSearchMonType1]
    call PokedexSearch_ConvertType
    ld [wDexConvertedMonType], a
    ld a, [wDexSearchMonType2]
    call PokedexSearch_ConvertType
    ld [wSearchType2], a
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld hl, wDexListingEnd
    ld a, [hli]
    ld c, a
    ld b, [hl]
    ld a, b
    or c
    jr z, .emit
    ld hl, wPokedexOrder
    ld de, wSearchRecords
.classify
    push bc
    ld a, [hli]
    ld c, a
    ld a, [hli]
    ld b, a
    push hl
    call .Classify
    push af
    ld a, 3
    ldh [rSVBK], a
    ld a, c
    ld [de], a
    inc de
    ld a, b
    ld [de], a
    inc de
    pop af
    ld [de], a
    inc de
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    pop hl
    pop bc
    dec bc
    ld a, b
    or c
    jr nz, .classify
.emit
    xor a
    ld [wDexSearchResultCount], a
    ld [wDexSearchResultCount + 1], a
    ld hl, wPokedexOrder
    ld a, l
    ld [wSearchOutput], a
    ld a, h
    ld [wSearchOutput + 1], a
    ld a, 1
    ld [wSearchGroup], a
.group
    ld a, 3
    ldh [rSVBK], a
    ld hl, wDexListingEnd
    ld a, [hli]
    ld c, a
    ld b, [hl]
    ld a, b
    or c
    jr z, .clear
    ld hl, wSearchRecords
.record
    ld e, [hl]
    inc hl
    ld d, [hl]
    inc hl
    ld a, [wSearchGroup]
    cp [hl]
    inc hl
    jr nz, .next
    push hl
    push bc
    ld hl, wSearchOutput
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld [hl], e
    inc hl
    ld [hl], d
    inc hl
    ld a, l
    ld [wSearchOutput], a
    ld a, h
    ld [wSearchOutput + 1], a
    ld a, 3
    ldh [rSVBK], a
    ld hl, wDexSearchResultCount
    inc [hl]
    jr nz, .counted
    inc hl
    inc [hl]
.counted
    pop bc
    pop hl
.next
    dec bc
    ld a, b
    or c
    jr nz, .record
    ld hl, wSearchGroup
    inc [hl]
    ld a, [hl]
    cp 4
    jr nz, .group
.clear
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    ld hl, wDexSearchResultCount
    ld e, [hl]
    inc hl
    ld d, [hl]
    ld hl, NUM_POKEMON + 1
    ld a, l
    sub e
    ld c, a
    ld a, h
    sbc d
    ld b, a
    ld hl, wSearchOutput
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, $ff
.tail
    ld [hli], a
    ld [hli], a
    dec bc
    push af
    ld a, b
    or c
    jr z, .clean
    pop af
    jr .tail
.clean
    pop af
    farcall PokedexInfo_Reset ; classified records overlap inactive Info work
    pop af
    ldh [rSVBK], a
    ret
.Classify
    push de
    ld a, b
    or c
    jr z, .zero
    ld a, b
    and c
    inc a
    jr z, .zero
    push bc
    ld d, b
    ld e, c
    ld a, BANK(wPokedexSeen)
    ldh [rSVBK], a
    call CheckSeenMonIndex
    push af
    ld a, BANK(wPokedexOrder)
    ldh [rSVBK], a
    pop af
    pop bc
    jr z, .zero
    push bc
    ld a, BANK(BaseData)
    ld hl, BaseData
    call LoadIndirectPointer
    jr z, .null
    ld bc, BASE_TYPES
    add hl, bc
    call GetFarWord
    ld c, 0
    ld a, [wDexConvertedMonType]
    cp h
    jr z, .one
    cp l
    jr nz, .two
.one
    set 0, c
.two
    ld a, [wSearchType2]
    cp $ff
    jr z, .single
    cp h
    jr z, .both
    cp l
    jr nz, .rank
.both
    set 1, c
.rank
    ld a, c
    and a
    jr z, .null
    cp 3
    ld a, 1
    jr z, .return
    ld a, c
    inc a ; Type1-only=2, Type2-only=3
    jr .return
.single
    ld a, c
    jr .return
.null
    xor a
.return
    pop bc
    pop de
    ret
.zero
    xor a
    pop de
    ret
