SECTION "Budget Local Fades", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetFadeOut:
    call FillWhiteBGColor
IF FADE_DELAY == 0
    ld c, $12
    call GetTimePalFade
    call DmgToCgbTimePals
    jp DelayFrame
ELSE
    ld c, $9
    call GetTimePalFade
    ld b, 4
.loop
    call DmgToCgbTimePals
    inc hl
    inc hl
    inc hl
    ld c, FADE_DELAY
    call DelayFrames
    dec b
    jr nz, .loop
    ret
ENDC
BudgetFadeIn:
IF FADE_DELAY == 0
    ld c, $9
    call GetTimePalFade
    call DmgToCgbTimePals
    jp DelayFrame
ELSE
    ld c, $12
    call GetTimePalFade
    ld b, 4
.loop
    call DmgToCgbTimePals
    dec hl
    dec hl
    dec hl
    ld c, FADE_DELAY
    call DelayFrames
    dec b
    jr nz, .loop
    ret
ENDC
BudgetFadeEnd:
