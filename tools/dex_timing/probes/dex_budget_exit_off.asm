MACRO FC
IF B_\1 == 0 || B_\1 == PROBE_BANK
    call \1
ELSE
    ld a, B_\1
    ld hl, \1
    rst FarCall
ENDC
ENDM
SECTION "Budget Exit LCD Off", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetExitOff:
    ldh a, [hCGB]
    and a
    jp z, CloseSubmenu
    call ClearPalettes
    call DisableLCD
    call ClearSprites
    FC RefreshSprites
    call LoadStandardFont
    call LoadFontsExtra
    FC UpdateTimeOfDayPal
    call LoadOverworldTilemapAndAttrmapPals
    call LoadTilesetGFX
    ld a, 9
    call SkipMusic
    call UpdateSprites
    call ExitMenu
    ld b, SCGB_MAPPALS
    call GetSGBLayout
    FC LoadOW_BGPal7
    ld de, $9800
    ld a, B_BudgetCopyOff
    ld hl, BudgetCopyOff
    rst FarCall
    call ClearPalettes
    call ForceUpdateCGBPals
    call EnableLCD
    ld a, 1
    ldh [hBGMapMode], a
    FC FadeInFromWhite
    jp EnableSpriteUpdates
BudgetExitOffEnd:
