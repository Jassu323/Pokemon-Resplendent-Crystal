MACRO FC
IF B_\1 == 0 || B_\1 == PROBE_BANK
    call \1
ELSE
    ld a, B_\1
    ld hl, \1
    rst FarCall
ENDC
ENDM
SECTION "Budget Exit LCD On", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetExitLCD:
    ldh a, [hCGB]
    and a
    jp z, CloseSubmenu
    call ClearPalettes
    call DelayFrame
    ld a, 1
    ldh [hOAMUpdate], a
    call ClearSprites
    FC RefreshSprites
    FC BudgetFontLCD
    call LoadFontsExtra
    FC UpdateTimeOfDayPal
    call LoadOverworldTilemapAndAttrmapPals
    call .Tileset
    call UpdateSprites
    call ExitMenu
    ld b, SCGB_MAPPALS
    call GetSGBLayout
    FC LoadOW_BGPal7
    ldh a, [hCGBPalUpdate]
    push af
    xor a
    ldh [hCGBPalUpdate], a
    call CGBOnly_CopyTilemapAtOnce
    call DelayFrame
    pop af
    ldh [hCGBPalUpdate], a
    xor a
    ldh [hOAMUpdate], a
    ld a, 1
    ldh [hBGMapMode], a
    FC FadeInFromWhite
    jp EnableSpriteUpdates
.Tileset
    ld hl, wTilesetAddress
    ld a, [hli]
    ld h, [hl]
    ld l, a
    ld a, [wTilesetBank]
    ld e, a
    ldh a, [$ff70]
    push af
    ld a, B_wDecompressScratch
    ldh [$ff70], a
    ld a, e
    ld de, wDecompressScratch
    call FarDecompress
    ld de, wDecompressScratch
    ld hl, $9000
    ld b, PROBE_BANK
    ld c, 96
    call Get2bppViaHDMA
    ld de, wDecompressScratch + $600
    ld hl, $9000
    ld b, PROBE_BANK
    ld c, 96
    call Get2bppViaHDMAToVRAMBank1
    pop af
    ldh [$ff70], a
    ld a, [wMapTileset]
    cp TILESET_JOHTO
    jr z, .roof
    cp TILESET_JOHTO_MODERN
    jr z, .roof
    cp TILESET_BATTLE_TOWER_OUTSIDE
    jr nz, .done
.roof
    FC LoadMapGroupRoof
.done
    xor a
    ldh [hTileAnimFrame], a
    ret
BudgetExitLCDEnd:
