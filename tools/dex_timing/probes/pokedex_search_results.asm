; Private Results owner: share the accepted Legacy portrait transaction.
SECTION FRAGMENT "Pokedex Search Prototype", ROMX

ASSERT wPokedexOwnerAttrmapBuffer + TILEMAP_WIDTH * SCREEN_HEIGHT == wSearchRecords

PokedexResults_Initialize:
    xor a
    ldh [hVBlank], a
    ldh [hBGMapMode], a
    ldh [hCGBPalUpdate], a
    ld a, TRUE
    ldh [hOAMUpdate], a
    farcall Pokedex_CancelAnimationPrefetch
    ld a, 4
    ld [wDexListingHeight], a
    farcall Pokedex_PrepareAndCommitSelectedMonGFX
    farcall CGB_PokedexResultsStagePalettes
    call PokedexResults_LoadTypes
    farcall PokedexResults_DrawBG
    farcall Pokedex_StageOwnerTransitionMaps
    di
.wait_bg
    ldh a, [rLY]
    cp 144
    jr c, .wait_bg
    call PokedexResults_CommitBG
    ei
    call PokedexResults_DrawWindow
    call PokedexResults_UpdateOAM
    farcall Pokedex_StageOwnerTransitionMaps
    di
.wait_window
    ldh a, [rLY]
    cp 144
    jr c, .wait_window
    farcall PokedexLegacy_CommitWindow
    ei
    ld a, POKEDEX_SCX
    ldh [hSCX], a
    ld a, $4a
    ldh [hWX], a
    xor a
    ldh [hWY], a
    farcall ApplyPals
    ld a, TRUE
    ldh [hCGBPalUpdate], a
    farcall PokedexListing_RevealMenu
    farcall Pokedex_RecordRenderedSelectionKey
    ret

PokedexResults_Scroll:
    farcall Pokedex_CancelAnimationPrefetch
    xor a
    ldh [hBGMapMode], a
    farcall Pokedex_PrepareSelectedMonTiles
    farcall CGB_PokedexPrepareFrontpicPalette
    ld a, TRUE
    ldh [hOAMUpdate], a
    call PokedexResults_DrawWindow
    call PokedexResults_UpdateOAM
    farcall Pokedex_StageOwnerTransitionMaps
.wait_portrait
    ldh a, [rLY]
    cp 64
    jr c, .wait_portrait
    cp 78
    jr nc, .wait_portrait
    farcall PokedexLegacy_CommitPortrait
    farcall CGB_PokedexCommitFrontpicPalette
    di
.wait_window
    ldh a, [rLY]
    cp 144
    jr c, .wait_window
    farcall PokedexLegacy_CommitWindow
    call hTransferShadowOAM
    ei
    xor a
    ldh [hOAMUpdate], a
    farcall Pokedex_RecordRenderedSelectionKey
    ret

PokedexResults_CommitBG:
    ldh a, [rSVBK]
    push af
    ldh a, [rVBK]
    push af
    ld a, BANK(wPokedexOwnerTilemapBuffer)
    ldh [rSVBK], a
    ld a, 1
    ldh [rVBK], a
    ld hl, wPokedexOwnerAttrmapBuffer
    call .Transfer
    xor a
    ldh [rVBK], a
    ld hl, wPokedexOwnerTilemapBuffer
    call .Transfer
    pop af
    ldh [rVBK], a
    pop af
    ldh [rSVBK], a
    ret
.Transfer
    ld a, h
    ldh [rVDMA_SRC_HIGH], a
    ld a, l
    ldh [rVDMA_SRC_LOW], a
    ld a, HIGH(vBGMap0) & $1f
    ldh [rVDMA_DEST_HIGH], a
    xor a
    ldh [rVDMA_DEST_LOW], a
    ld a, 2 * SCREEN_HEIGHT - 1
    ldh [rVDMA_LEN], a
    ret

PokedexResults_DrawWindow:
    xor a
    hlcoord 0, 0, wAttrmap
    ld bc, SCREEN_AREA
    call ByteFill
    ld a, $32
    hlcoord 0, 0
    ld bc, SCREEN_AREA
    call ByteFill
    farcall DrawPokedexSearchResultsWindow
    farcall PokedexResults_PrintNames
    ret

PokedexResults_LoadTypes:
    ldh a, [rSVBK]
    push af
    ld a, [wDexSearchMonType1]
    call PokedexSearch_ConvertType
    push af
    ld c, a
    ld de, wPokedexWRAM0Scratch
    farcall PokedexInfo_CopyCompactTypeTilesByC
    pop af
    ld de, wSearchIconPalettes
    call PokedexSearch_UpdateIcons.Palette
    ld a, [wDexSearchMonType2]
    and a
    jr z, .upload
    ld b, a
    ld a, [wDexSearchMonType1]
    cp b
    jr z, .upload
    ld a, b
    call PokedexSearch_ConvertType
    push af
    ld c, a
    ld de, wPokedexWRAM0Scratch + 4 tiles
    farcall PokedexInfo_CopyCompactTypeTilesByC
    pop af
    ld de, wSearchIconPalettes + 1 palettes
    call PokedexSearch_UpdateIcons.Palette
.upload
    ldh a, [rVBK]
    push af
    ld a, 1
    ldh [rVBK], a
    ld hl, wPokedexWRAM0Scratch
    ld de, vTiles3 tile POKEDEX_TYPE_OBJ_TILE
    ld c, 8
    call Pokedex_HDMATransferCacheGFX
    pop af
    ldh [rVBK], a
    ld a, BANK(wOBPals1)
    ldh [rSVBK], a
    ld hl, wSearchIconPalettes
    ld de, wOBPals1 palette 2
    ld bc, 2 palettes
    call CopyBytes
    pop af
    ldh [rSVBK], a
    ret

PokedexResults_UpdateOAM:
    ldh a, [rSVBK]
    push af
    call ClearSprites
    ld de, wShadowOAM
    ld a, [wDexListingCursor]
    swap a
    add 24
    ld b, a
    ld c, 72
    xor a
    call .Corner
    ld c, 151
    ld a, OAM_XFLIP
    call .Corner
    ld a, b
    add 15
    ld b, a
    ld c, 72
    ld a, OAM_YFLIP
    call .Corner
    ld c, 151
    ld a, OAM_XFLIP | OAM_YFLIP
    call .Corner
    xor a
.ball
    push af
    push de
    ld c, a
    farcall PokedexResults_GetRowSpecies
    ld a, d
    or e
    jr z, .absent
    ld a, BANK(wPokedexCaught)
    ldh [rSVBK], a
    call CheckCaughtMonIndex
    jr z, .absent
    pop de
    pop af
    push af
    swap a
    add 32
    ld [de], a
    inc de
    ld a, 71
    ld [de], a
    inc de
    ld a, POKEDEX_CAUGHT_BALL_TILE
    ld [de], a
    inc de
    ld a, 1
    ld [de], a
    inc de
    jr .next
.absent
    pop de
    inc de
    inc de
    inc de
    inc de
.next
    pop af
    inc a
    cp 4
    jr c, .ball
    ld hl, wShadowOAMSprite08
    ld b, POKEDEX_TYPE_OBJ_TILE
    ld d, 128 ; screen y=112
    ld e, OAM_BANK1 | 2
    call .Badge
    ld a, [wDexSearchMonType2]
    and a
    jr z, .done
    ld c, a
    ld a, [wDexSearchMonType1]
    cp c
    jr z, .done
    ld d, 136 ; screen y=120
    ld e, OAM_BANK1 | 3
    call .Badge
.done
    pop af
    ldh [rSVBK], a
    ret
.Corner
    push af
    ld a, b
    ld [de], a
    inc de
    ld a, c
    ld [de], a
    inc de
    ld a, POKEDEX_LIST_CURSOR_TILE
    ld [de], a
    inc de
    pop af
    ld [de], a
    inc de
    ret
.Badge
    ld c, 4
    ld a, 88 ; screen x=80
.sprite
    push af
    ld a, d
    ld [hli], a
    pop af
    ld [hli], a
    add 8
    push af
    ld a, b
    ld [hli], a
    inc b
    ld a, e
    ld [hli], a
    pop af
    dec c
    jr nz, .sprite
    ret
