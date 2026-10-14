MACRO FC
IF B_\1 == 0 || B_\1 == PROBE_BANK
    call \1
ELSE
    ld a, B_\1
    ld hl, \1
    rst FarCall
ENDC
ENDM

SECTION "Budget Cold Entry", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetColdStart:
IF DEF(MUSIC_SYNC)
    call BudgetMusicBegin
ENDC
    FC ClearSprites
    ld a, [wPokedexListingPresentation]
    and a
    jr nz, .legacy
    FC Pokedex_LoadGridPage
    FC DrawPokedexListWindow
    FC Pokedex_PrintSelectedName
    call .Footer
    ld de, $9c00
    call BudgetCopyOff
IF DEF(MUSIC_SYNC)
    call BudgetMusicCheckpoint
ENDC
    FC Pokedex_DrawMainScreenBG
    jr .common
.legacy
    FC PokedexLegacy_DrawWindow
    ld de, $9c00
    call BudgetCopyOff
IF DEF(MUSIC_SYNC)
    call BudgetMusicCheckpoint
ENDC
    FC PokedexLegacy_DrawSidebar
.common
    ld a, 5
    ldh [hSCX], a
    xor a
    ldh [hWY], a
    FC Pokedex_PrepareAndCommitSelectedMonGFX
IF DEF(MUSIC_SYNC)
    call BudgetMusicCheckpoint
ENDC
    FC CGB_PokedexStageListLayout
    ld de, $9800
    call BudgetCopyOff
    FC Pokedex_RecordRenderedSelectionKey
    ld a, [wPokedexListingPresentation]
    and a
    jr nz, .legacy_oam
    FC Pokedex_UpdateGridOAM
    FC DrawPokedexListWindow
    FC Pokedex_PrintSelectedName
    call .Footer
    jr .reveal
.legacy_oam
    FC PokedexLegacy_UpdateOAM
    FC PokedexLegacy_DrawWindow
.reveal
    xor a
    ldh [hBGMapMode], a
    ldh [hOAMUpdate], a
    ld [wPokedexSelectedState], a
    ldh [$ff42], a
    ldh [$ff4a], a
    ld a, 5
    ldh [$ff43], a
    ld a, $47
    ldh [hWX], a
    ldh [$ff4b], a
    FC ForceUpdateCGBPals
    FC hTransferShadowOAM
    FC Pokedex_IncrementDexPointer
IF DEF(MUSIC_SYNC)
    call BudgetMusicCheckpoint
ENDC
    FC EnableLCD
    ld a, VBLANK_POKEDEX
    ldh [hVBlank], a
    FC DelayFrame
    ret
.Footer
    ld hl, wTilemap + 17 * 20
    ld de, .FooterData
    ld b, 10
.next
    ld a, [de]
    inc de
    ld [hli], a
    dec b
    jr nz, .next
    ret
.FooterData
    db $3c,$3b,$41,$42,$43,$44,$45,$46,$47,$3c

BudgetCopyOff:
    ldh a, [$ff4f]
    push af
    push de
    ld a, 1
    ldh [$ff4f], a
    ld hl, wAttrmap
    call .Rows
    pop de
    xor a
    ldh [$ff4f], a
    ld hl, wTilemap
    call .Rows
    pop af
    ldh [$ff4f], a
    ret
.Rows
    ld b, 18
.row
IF DEF(UNROLL_MAP)
REPT 20
    ld a, [hli]
    ld [de], a
    inc de
ENDR
ELSE
    ld c, 20
.column
    ld a, [hli]
    ld [de], a
    inc de
    dec c
    jr nz, .column
ENDC
    ld a, e
    add 12
    ld e, a
    jr nc, .next_row
    inc d
.next_row
    dec b
    jr nz, .row
IF DEF(UNROLL_MAP)
    ld c, 0
ENDC
    ret
BudgetColdEnd:
